"""
Reports endpoints for analytics and metrics.

Security Rules:
- GET /reports/*: super_admin and admin_viewer can view
- POST /reports/refresh: super_admin and admin_viewer can refresh
"""
import time
import logging
from datetime import date
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from database import get_db
from models.user import User
from services.report_service import ReportService
from services.prediction_service import PredictionService
from services.analytics_cache import get_cache
from utils.auth import get_current_user, require_role

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reports", tags=["reports"])

# In-memory storage for refresh state (per user)
# In production, consider using Redis or database for multi-instance deployments
_refresh_state: Dict[str, Dict[str, Any]] = {}
_prediction_state: Dict[str, Dict[str, Any]] = {}


class RefreshResponse(BaseModel):
    """Response model for refresh endpoint."""
    success: bool
    message: str
    metrics: Dict[str, Any]
    elapsed_seconds: float
    refresh_count: int
    cache_invalidated: bool


class PredictionResponse(BaseModel):
    """Response model for predictions endpoint."""
    success: bool
    message: str
    predictions: Dict[str, Any]
    elapsed_seconds: float
    confidence: str
    forecast_days: int


@router.post("/refresh", response_model=RefreshResponse, dependencies=[Depends(require_role(["super_admin", "admin_viewer"]))])
async def refresh_metrics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    sucursal_id: Optional[str] = Query(None, description="Optional: Filter by sucursal ID"),
    force: bool = Query(False, description="Force refresh and invalidate cache"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)")
) -> RefreshResponse:
    """
    Refresh metrics manually (Master Button functionality).
    
    Similar to Databoard's refresh button:
    - Validates time limits (minimum 2 seconds between refreshes)
    - Validates count limits (maximum 30 refreshes per session)
    - Loads metrics in parallel for efficiency
    - Optionally invalidates cache if force=True
    
    Security: Only super_admin and admin_viewer can refresh metrics.
    
    Args:
        db: Database session
        current_user: Current authenticated user
        sucursal_id: Optional sucursal ID to filter by
        force: Force refresh and invalidate cache
        start_date: Optional start date for sales report
        end_date: Optional end date for sales report
        
    Returns:
        RefreshResponse with updated metrics and status
    """
    user_id = str(current_user.id)
    current_time = time.time()
    
    # Initialize user state if not exists
    if user_id not in _refresh_state:
        _refresh_state[user_id] = {
            "refresh_in_progress": False,
            "last_refresh": 0,
            "refresh_count": 0
        }
    
    user_state = _refresh_state[user_id]
    
    # Validation 1: Check if refresh is already in progress
    if user_state.get("refresh_in_progress", False):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Refresh already in progress. Please wait."
        )
    
    # Validation 2: Check minimum time between refreshes (2 seconds)
    last_refresh = user_state.get("last_refresh", 0)
    time_since_last = current_time - last_refresh
    
    if time_since_last < 2:
        remaining = 2 - time_since_last
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Please wait {remaining:.1f} seconds before refreshing again."
        )
    
    # Validation 3: Check maximum refresh count (30 per session)
    refresh_count = user_state.get("refresh_count", 0)
    if refresh_count >= 30:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Maximum refresh limit reached (30). Please wait before refreshing again."
        )
    
    # Update state
    user_state["refresh_in_progress"] = True
    user_state["last_refresh"] = current_time
    user_state["refresh_count"] = refresh_count + 1
    
    start_time = time.time()
    cache_invalidated = False
    
    try:
        # Invalidate cache if force=True
        if force:
            cache = get_cache()
            if sucursal_id:
                await cache.invalidate(f"sales:{sucursal_id}:*")
                await cache.invalidate(f"stock:{sucursal_id}")
                await cache.invalidate(f"services:{sucursal_id}")
            else:
                await cache.invalidate("sales:*")
                await cache.invalidate("stock:*")
                await cache.invalidate("services:*")
            cache_invalidated = True
            logger.info(f"Cache invalidated for user {user_id} (force=True)")
        
        # Parse dates if provided
        parsed_start_date = None
        parsed_end_date = None
        
        if start_date:
            try:
                parsed_start_date = date.fromisoformat(start_date)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid start_date format. Use YYYY-MM-DD."
                )
        
        if end_date:
            try:
                parsed_end_date = date.fromisoformat(end_date)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid end_date format. Use YYYY-MM-DD."
                )
        
        # Initialize service
        report_service = ReportService()
        
        # Load metrics in parallel (similar to Databoard's load_dashboard_data)
        use_cache = not force
        
        # Create tasks for parallel execution
        sales_task = report_service.get_sales_report(
            db=db,
            sucursal_id=sucursal_id,
            start_date=parsed_start_date,
            end_date=parsed_end_date,
            use_cache=use_cache
        )
        
        stock_task = report_service.get_stock_report(
            db=db,
            sucursal_id=sucursal_id,
            use_cache=use_cache
        )
        
        services_task = report_service.get_services_report(
            db=db,
            sucursal_id=sucursal_id,
            use_cache=use_cache
        )
        
        # Execute in parallel using asyncio.gather (like Databoard)
        import asyncio
        sales_report, stock_report, services_report = await asyncio.gather(
            sales_task,
            stock_task,
            services_task
        )
        
        # Combine metrics
        metrics = {
            "sales": sales_report,
            "stock": stock_report,
            "services": services_report,
            "generated_at": time.time()
        }
        
        elapsed = time.time() - start_time
        
        logger.info(
            f"Metrics refreshed for user {user_id} in {elapsed:.2f}s "
            f"(refresh #{user_state['refresh_count']})"
        )
        
        return RefreshResponse(
            success=True,
            message=f"Metrics refreshed successfully in {elapsed:.2f}s",
            metrics=metrics,
            elapsed_seconds=round(elapsed, 2),
            refresh_count=user_state["refresh_count"],
            cache_invalidated=cache_invalidated
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error refreshing metrics for user {user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error refreshing metrics. Please try again."
        )
    finally:
        # Always reset refresh_in_progress
        user_state["refresh_in_progress"] = False


@router.get("/sales", dependencies=[Depends(require_role(["super_admin", "admin_viewer"]))])
async def get_sales_report(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    sucursal_id: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    use_cache: bool = Query(True, description="Use cache if available")
):
    """
    Get sales report.
    
    Security: super_admin and admin_viewer can view.
    """
    report_service = ReportService()
    
    parsed_start_date = None
    parsed_end_date = None
    
    if start_date:
        parsed_start_date = date.fromisoformat(start_date)
    if end_date:
        parsed_end_date = date.fromisoformat(end_date)
    
    return await report_service.get_sales_report(
        db=db,
        sucursal_id=sucursal_id,
        start_date=parsed_start_date,
        end_date=parsed_end_date,
        use_cache=use_cache
    )


@router.get("/stock", dependencies=[Depends(require_role(["super_admin", "admin_viewer"]))])
async def get_stock_report(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    sucursal_id: Optional[str] = Query(None),
    use_cache: bool = Query(True, description="Use cache if available")
):
    """
    Get stock report.
    
    Security: super_admin and admin_viewer can view.
    """
    report_service = ReportService()
    return await report_service.get_stock_report(
        db=db,
        sucursal_id=sucursal_id,
        use_cache=use_cache
    )


@router.get("/services", dependencies=[Depends(require_role(["super_admin", "admin_viewer"]))])
async def get_services_report(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    sucursal_id: Optional[str] = Query(None),
    use_cache: bool = Query(True, description="Use cache if available")
):
    """
    Get services report.
    
    Security: super_admin and admin_viewer can view.
    """
    report_service = ReportService()
    return await report_service.get_services_report(
        db=db,
        sucursal_id=sucursal_id,
        use_cache=use_cache
    )


@router.get("/dashboard", dependencies=[Depends(require_role(["super_admin", "admin_viewer"]))])
async def get_dashboard_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    sucursal_id: Optional[str] = Query(None),
    use_cache: bool = Query(True, description="Use cache if available")
):
    """
    Get complete dashboard summary with all metrics.
    
    Security: super_admin and admin_viewer can view.
    """
    report_service = ReportService()
    return await report_service.get_dashboard_summary(
        db=db,
        sucursal_id=sucursal_id,
        use_cache=use_cache
    )


@router.post("/predictions/generate", response_model=PredictionResponse, dependencies=[Depends(require_role(["super_admin", "admin_viewer"]))])
async def generate_predictions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    sucursal_id: Optional[str] = Query(None, description="Optional: Filter by sucursal ID"),
    forecast_days: int = Query(7, ge=1, le=30, description="Number of days to forecast (1-30)"),
    prediction_type: str = Query("all", description="Type of prediction: 'all', 'sales', 'capacity', 'stock'")
) -> PredictionResponse:
    """
    Generate predictions under demand (similar to Databoard's prediction button).
    
    Only executes when user explicitly requests it (not automatic).
    - Validates time limits (minimum 5 seconds between predictions)
    - Validates count limits (maximum 10 predictions per session)
    - Generates predictions based on historical data
    - Uses simple algorithms (moving averages, trends)
    
    Security: Only super_admin and admin_viewer can generate predictions.
    
    Args:
        db: Database session
        current_user: Current authenticated user
        sucursal_id: Optional sucursal ID to filter by
        forecast_days: Number of days to forecast (1-30, default: 7)
        prediction_type: Type of prediction ('all', 'sales', 'capacity', 'stock')
        
    Returns:
        PredictionResponse with generated predictions and confidence level
    """
    user_id = str(current_user.id)
    current_time = time.time()
    
    # Initialize user state if not exists
    if user_id not in _prediction_state:
        _prediction_state[user_id] = {
            "prediction_in_progress": False,
            "last_prediction": 0,
            "prediction_count": 0
        }
    
    user_state = _prediction_state[user_id]
    
    # Validation 1: Check if prediction is already in progress
    if user_state.get("prediction_in_progress", False):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Prediction already in progress. Please wait."
        )
    
    # Validation 2: Check minimum time between predictions (5 seconds - predictions are heavier)
    last_prediction = user_state.get("last_prediction", 0)
    time_since_last = current_time - last_prediction
    
    if time_since_last < 5:
        remaining = 5 - time_since_last
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Please wait {remaining:.1f} seconds before generating predictions again."
        )
    
    # Validation 3: Check maximum prediction count (10 per session - predictions are expensive)
    prediction_count = user_state.get("prediction_count", 0)
    if prediction_count >= 10:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Maximum prediction limit reached (10). Please wait before generating predictions again."
        )
    
    # Validate prediction_type
    valid_types = ["all", "sales", "capacity", "stock"]
    if prediction_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid prediction_type. Must be one of: {', '.join(valid_types)}"
        )
    
    # Update state
    user_state["prediction_in_progress"] = True
    user_state["last_prediction"] = current_time
    user_state["prediction_count"] = prediction_count + 1
    
    start_time = time.time()
    
    try:
        # Initialize service
        prediction_service = PredictionService()
        
        # Generate predictions based on type
        if prediction_type == "all":
            predictions = await prediction_service.generate_all_predictions(
                db=db,
                sucursal_id=sucursal_id,
                forecast_days=forecast_days
            )
            # Determine overall confidence (lowest of all)
            confidences = []
            if "sales" in predictions and "confidence" in predictions["sales"]:
                confidences.append(predictions["sales"]["confidence"])
            if "capacity" in predictions and "confidence" in predictions["capacity"]:
                confidences.append(predictions["capacity"]["confidence"])
            if "stock" in predictions and "confidence" in predictions["stock"]:
                confidences.append(predictions["stock"]["confidence"])
            
            overall_confidence = "low"
            if all(c == "high" for c in confidences):
                overall_confidence = "high"
            elif any(c == "high" for c in confidences) or all(c == "medium" for c in confidences):
                overall_confidence = "medium"
        elif prediction_type == "sales":
            predictions = {
                "sales": await prediction_service.predict_sales(
                    db=db,
                    sucursal_id=sucursal_id,
                    forecast_days=forecast_days
                )
            }
            overall_confidence = predictions["sales"].get("confidence", "low")
        elif prediction_type == "capacity":
            predictions = {
                "capacity": await prediction_service.predict_capacity(
                    db=db,
                    sucursal_id=sucursal_id,
                    forecast_days=forecast_days
                )
            }
            overall_confidence = predictions["capacity"].get("confidence", "low")
        elif prediction_type == "stock":
            predictions = {
                "stock": await prediction_service.predict_stock_needs(
                    db=db,
                    sucursal_id=sucursal_id,
                    forecast_days=forecast_days
                )
            }
            overall_confidence = predictions["stock"].get("confidence", "low")
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid prediction_type: {prediction_type}"
            )
        
        elapsed = time.time() - start_time
        
        logger.info(
            f"Predictions generated for user {user_id} in {elapsed:.2f}s "
            f"(type: {prediction_type}, forecast_days: {forecast_days}, "
            f"prediction #{user_state['prediction_count']})"
        )
        
        return PredictionResponse(
            success=True,
            message=f"Predictions generated successfully in {elapsed:.2f}s",
            predictions=predictions,
            elapsed_seconds=round(elapsed, 2),
            confidence=overall_confidence,
            forecast_days=forecast_days
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating predictions for user {user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error generating predictions. Please try again."
        )
    finally:
        # Always reset prediction_in_progress
        user_state["prediction_in_progress"] = False

