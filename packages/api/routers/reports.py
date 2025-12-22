"""
Reports endpoints for analytics and metrics.

Security Rules:
- GET /reports/*: super_admin and admin_viewer can view
- POST /reports/refresh: super_admin and admin_viewer can refresh
"""
import time
import logging
from datetime import date
from typing import Optional, Dict, Any, List
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


class SegmentedPredictionsRequest(BaseModel):
    """Request model for segmented predictions endpoint."""
    sucursal_id: Optional[str] = None
    forecast_days: int = 7
    modules: Optional[List[str]] = None  # ["recepcion", "kidibar", "total"]
    prediction_types: Optional[List[str]] = None  # ["sales", "capacity", "stock"]


class SegmentedPredictionsResponse(BaseModel):
    """Response model for segmented predictions endpoint."""
    success: bool
    message: str
    predictions: Dict[str, Dict[str, Any]]  # {module: {type: prediction_data}}
    elapsed_seconds: float
    overall_confidence: str
    forecast_days: int
    modules: List[str]


@router.post("/refresh", response_model=RefreshResponse, dependencies=[Depends(require_role(["super_admin", "admin_viewer"]))])
async def refresh_metrics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    sucursal_id: Optional[str] = Query(None, description="Optional: Filter by sucursal ID"),
    force: bool = Query(False, description="Force refresh and invalidate cache"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    days: int = Query(30, ge=1, le=365, description="Number of days for historical metrics (peak_hours, top_products, top_services). Default: 30")
) -> RefreshResponse:
    """
    Refresh metrics manually (Master Button functionality).
    
    Similar to Databoard's refresh button:
    - Validates time limits (minimum 2 seconds between refreshes)
    - Validates count limits (maximum 30 refreshes per session)
    - Loads metrics in parallel for efficiency
    - Optionally invalidates cache if force=True
    - Includes historical metrics: peak_hours, top_products, top_services
    
    Security: Only super_admin and admin_viewer can refresh metrics.
    
    Args:
        db: Database session
        current_user: Current authenticated user
        sucursal_id: Optional sucursal ID to filter by
        force: Force refresh and invalidate cache
        start_date: Optional start date for sales report
        end_date: Optional end date for sales report
        days: Number of days for historical metrics (peak_hours, top_products, top_services). Default: 30
        
    Returns:
        RefreshResponse with updated metrics and status, including:
        - sales: Sales report
        - stock: Stock report
        - services: Services report
        - peak_hours: Peak hours analysis (optional)
        - top_products: Top products report (optional)
        - top_services: Top services report (optional)
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
                await cache.invalidate(f"peak_hours:{sucursal_id}:*")
                await cache.invalidate(f"top_products:{sucursal_id}:*")
                await cache.invalidate(f"top_services:{sucursal_id}:*")
            else:
                await cache.invalidate("sales:*")
                await cache.invalidate("stock:*")
                await cache.invalidate("services:*")
                await cache.invalidate("peak_hours:*")
                await cache.invalidate("top_products:*")
                await cache.invalidate("top_services:*")
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
        # Core metrics (always loaded)
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
        
        # Historical metrics (for dashboard analytics)
        peak_hours_task = report_service.get_peak_hours_report(
            db=db,
            sucursal_id=sucursal_id,
            days=days,
            use_cache=use_cache
        )
        
        top_products_task = report_service.get_top_products_report(
            db=db,
            sucursal_id=sucursal_id,
            days=days,
            use_cache=use_cache
        )
        
        top_services_task = report_service.get_top_services_report(
            db=db,
            sucursal_id=sucursal_id,
            days=days,
            use_cache=use_cache
        )
        
        # Execute in parallel using asyncio.gather (like Databoard)
        import asyncio
        sales_report, stock_report, services_report, peak_hours_report, top_products_report, top_services_report = await asyncio.gather(
            sales_task,
            stock_task,
            services_task,
            peak_hours_task,
            top_products_task,
            top_services_task,
            return_exceptions=True  # Allow individual failures without breaking the entire refresh
        )
        
        # Handle exceptions in individual reports (log but don't fail the entire refresh)
        if isinstance(peak_hours_report, Exception):
            logger.warning(f"Error loading peak_hours report: {peak_hours_report}")
            peak_hours_report = None
        if isinstance(top_products_report, Exception):
            logger.warning(f"Error loading top_products report: {top_products_report}")
            top_products_report = None
        if isinstance(top_services_report, Exception):
            logger.warning(f"Error loading top_services report: {top_services_report}")
            top_services_report = None
        
        # Combine metrics
        metrics = {
            "sales": sales_report,
            "stock": stock_report,
            "services": services_report,
            "generated_at": time.time()
        }
        
        # Add historical metrics if available (optional fields)
        if peak_hours_report is not None:
            metrics["peak_hours"] = peak_hours_report
        if top_products_report is not None:
            metrics["top_products"] = top_products_report
        if top_services_report is not None:
            metrics["top_services"] = top_services_report
        
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
    module: Optional[str] = Query(None, description="Module filter: 'recepcion', 'kidibar', or None for all"),
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
    
    # Validate module parameter
    if module and module not in ["recepcion", "kidibar", "all"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid module. Must be 'recepcion', 'kidibar', or 'all' (or omit for all)"
        )
    
    # Normalize "all" to None
    module_filter = None if module == "all" else module
    
    return await report_service.get_sales_report(
        db=db,
        sucursal_id=sucursal_id,
        start_date=parsed_start_date,
        end_date=parsed_end_date,
        module=module_filter,
        use_cache=use_cache
    )


@router.get("/sales/timeseries", dependencies=[Depends(require_role(["super_admin", "admin_viewer"]))])
async def get_sales_timeseries(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    sucursal_id: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    module: Optional[str] = Query(None, description="Module filter: 'recepcion', 'kidibar', or None for all"),
    use_cache: bool = Query(True, description="Use cache if available")
):
    """
    Get sales time series data aggregated by day.
    
    Security: super_admin and admin_viewer can view.
    """
    report_service = ReportService()
    
    parsed_start_date = None
    parsed_end_date = None
    
    if start_date:
        try:
            parsed_start_date = date.fromisoformat(start_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid start_date format. Use YYYY-MM-DD."
            )
    if end_date:
        try:
            parsed_end_date = date.fromisoformat(end_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid end_date format. Use YYYY-MM-DD."
            )
    
    # Validate module parameter
    if module and module not in ["recepcion", "kidibar", "all"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid module. Must be 'recepcion', 'kidibar', or 'all' (or omit for all)"
        )
    
    # Normalize "all" to None
    module_filter = None if module == "all" else module
    
    return await report_service.get_sales_timeseries(
        db=db,
        sucursal_id=sucursal_id,
        start_date=parsed_start_date,
        end_date=parsed_end_date,
        module=module_filter,
        use_cache=use_cache
    )


@router.get("/sales/comparison", dependencies=[Depends(require_role(["super_admin", "admin_viewer"]))])
async def get_sales_comparison(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    sucursal_id: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    comparison_type: str = Query("previous_period", description="Comparison type: 'previous_period', 'month_over_month', 'year_over_year'"),
    module: Optional[str] = Query(None, description="Module filter: 'recepcion', 'kidibar', or None for all"),
    use_cache: bool = Query(True, description="Use cache if available")
):
    """
    Get sales report with comparison to previous period.
    
    Security: super_admin and admin_viewer can view.
    """
    report_service = ReportService()
    
    parsed_start_date = None
    parsed_end_date = None
    
    if start_date:
        try:
            parsed_start_date = date.fromisoformat(start_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid start_date format. Use YYYY-MM-DD."
            )
    if end_date:
        try:
            parsed_end_date = date.fromisoformat(end_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid end_date format. Use YYYY-MM-DD."
            )
    
    # Validate comparison_type
    valid_comparison_types = ["previous_period", "month_over_month", "year_over_year"]
    if comparison_type not in valid_comparison_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid comparison_type. Must be one of: {', '.join(valid_comparison_types)}"
        )
    
    # Validate module parameter
    if module and module not in ["recepcion", "kidibar", "all"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid module. Must be 'recepcion', 'kidibar', or 'all' (or omit for all)"
        )
    
    # Normalize "all" to None
    module_filter = None if module == "all" else module
    
    return await report_service.get_sales_comparison_report(
        db=db,
        sucursal_id=sucursal_id,
        start_date=parsed_start_date,
        end_date=parsed_end_date,
        comparison_type=comparison_type,
        module=module_filter,
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


@router.get("/services/timeseries", dependencies=[Depends(require_role(["super_admin", "admin_viewer"]))])
async def get_services_timeseries(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    sucursal_id: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    service_id: Optional[str] = Query(None, description="Optional service ID to filter by specific service"),
    use_cache: bool = Query(True, description="Use cache if available")
):
    """
    Get services time series data aggregated by day.
    
    Security: super_admin and admin_viewer can view.
    """
    report_service = ReportService()
    
    parsed_start_date = None
    parsed_end_date = None
    
    if start_date:
        try:
            parsed_start_date = date.fromisoformat(start_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid start_date format. Use YYYY-MM-DD."
            )
    if end_date:
        try:
            parsed_end_date = date.fromisoformat(end_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid end_date format. Use YYYY-MM-DD."
            )
    
    return await report_service.get_services_timeseries(
        db=db,
        sucursal_id=sucursal_id,
        start_date=parsed_start_date,
        end_date=parsed_end_date,
        service_id=service_id,
        use_cache=use_cache
    )


@router.get("/services/utilization", dependencies=[Depends(require_role(["super_admin", "admin_viewer"]))])
async def get_services_utilization(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    sucursal_id: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    use_cache: bool = Query(True, description="Use cache if available")
):
    """
    Get services utilization analysis.
    
    Security: super_admin and admin_viewer can view.
    """
    report_service = ReportService()
    
    parsed_start_date = None
    parsed_end_date = None
    
    if start_date:
        try:
            parsed_start_date = date.fromisoformat(start_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid start_date format. Use YYYY-MM-DD."
            )
    if end_date:
        try:
            parsed_end_date = date.fromisoformat(end_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid end_date format. Use YYYY-MM-DD."
            )
    
    return await report_service.get_services_utilization(
        db=db,
        sucursal_id=sucursal_id,
        start_date=parsed_start_date,
        end_date=parsed_end_date,
        use_cache=use_cache
    )


@router.get("/services/performance", dependencies=[Depends(require_role(["super_admin", "admin_viewer"]))])
async def get_services_performance(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    sucursal_id: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    use_cache: bool = Query(True, description="Use cache if available")
):
    """
    Get service performance metrics (revenue, popularity, efficiency).
    
    Security: super_admin and admin_viewer can view.
    """
    report_service = ReportService()
    
    parsed_start_date = None
    parsed_end_date = None
    
    if start_date:
        try:
            parsed_start_date = date.fromisoformat(start_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid start_date format. Use YYYY-MM-DD."
            )
    if end_date:
        try:
            parsed_end_date = date.fromisoformat(end_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid end_date format. Use YYYY-MM-DD."
            )
    
    return await report_service.get_services_performance(
        db=db,
        sucursal_id=sucursal_id,
        start_date=parsed_start_date,
        end_date=parsed_end_date,
        use_cache=use_cache
    )


@router.get("/services/duration", dependencies=[Depends(require_role(["super_admin", "admin_viewer"]))])
async def get_services_duration(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    sucursal_id: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    use_cache: bool = Query(True, description="Use cache if available")
):
    """
    Analyze average service duration and usage patterns.
    
    Security: super_admin and admin_viewer can view.
    """
    report_service = ReportService()
    
    parsed_start_date = None
    parsed_end_date = None
    
    if start_date:
        try:
            parsed_start_date = date.fromisoformat(start_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid start_date format. Use YYYY-MM-DD."
            )
    if end_date:
        try:
            parsed_end_date = date.fromisoformat(end_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid end_date format. Use YYYY-MM-DD."
            )
    
    return await report_service.get_services_duration(
        db=db,
        sucursal_id=sucursal_id,
        start_date=parsed_start_date,
        end_date=parsed_end_date,
        use_cache=use_cache
    )


@router.get("/services/capacity", dependencies=[Depends(require_role(["super_admin", "admin_viewer"]))])
async def get_services_capacity(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    sucursal_id: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    use_cache: bool = Query(True, description="Use cache if available")
):
    """
    Get services capacity analysis and heatmap data.
    
    Security: super_admin and admin_viewer can view.
    """
    report_service = ReportService()
    
    parsed_start_date = None
    parsed_end_date = None
    
    if start_date:
        try:
            parsed_start_date = date.fromisoformat(start_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid start_date format. Use YYYY-MM-DD."
            )
    if end_date:
        try:
            parsed_end_date = date.fromisoformat(end_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid end_date format. Use YYYY-MM-DD."
            )
    
    return await report_service.get_services_capacity(
        db=db,
        sucursal_id=sucursal_id,
        start_date=parsed_start_date,
        end_date=parsed_end_date,
        use_cache=use_cache
    )


@router.get("/services/peak-hours", dependencies=[Depends(require_role(["super_admin", "admin_viewer"]))])
async def get_services_peak_hours(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    sucursal_id: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    use_cache: bool = Query(True, description="Use cache if available")
):
    """
    Advanced peak hours analysis with patterns and recommendations.
    
    Security: super_admin and admin_viewer can view.
    """
    report_service = ReportService()
    
    parsed_start_date = None
    parsed_end_date = None
    
    if start_date:
        try:
            parsed_start_date = date.fromisoformat(start_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid start_date format. Use YYYY-MM-DD."
            )
    if end_date:
        try:
            parsed_end_date = date.fromisoformat(end_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid end_date format. Use YYYY-MM-DD."
            )
    
    return await report_service.get_services_peak_hours(
        db=db,
        sucursal_id=sucursal_id,
        start_date=parsed_start_date,
        end_date=parsed_end_date,
        use_cache=use_cache
    )


@router.get("/services/recommendations", dependencies=[Depends(require_role(["super_admin", "admin_viewer"]))])
async def get_services_recommendations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    sucursal_id: Optional[str] = Query(None),
    use_cache: bool = Query(True, description="Use cache if available")
):
    """
    Generate actionable recommendations for services management.
    
    Security: super_admin and admin_viewer can view.
    """
    report_service = ReportService()
    
    return await report_service.get_services_recommendations(
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


@router.post("/predictions/generate/segmented", response_model=SegmentedPredictionsResponse, dependencies=[Depends(require_role(["super_admin", "admin_viewer"]))])
async def generate_segmented_predictions(
    request: SegmentedPredictionsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> SegmentedPredictionsResponse:
    """
    Generate segmented predictions by module and prediction type.
    
    Allows generating predictions for specific modules (recepcion, kidibar, total)
    and specific prediction types (sales, capacity, stock).
    
    Security: Only super_admin and admin_viewer can generate predictions.
    
    Args:
        request: SegmentedPredictionsRequest with modules, prediction_types, etc.
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        SegmentedPredictionsResponse with predictions organized by module and type
    """
    user_id = str(current_user.id)
    start_time = time.time()
    
    # Validate forecast_days
    if request.forecast_days < 1 or request.forecast_days > 30:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="forecast_days must be between 1 and 30"
        )
    
    # Default modules if not provided
    modules_to_forecast = request.modules or ["recepcion", "kidibar", "total"]
    
    # Normalize "all" to "total" for compatibility with frontend
    modules_to_forecast = ["total" if m == "all" else m for m in modules_to_forecast]
    
    # Validate modules
    valid_modules = ["recepcion", "kidibar", "total"]
    for mod in modules_to_forecast:
        if mod not in valid_modules:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid module: {mod}. Must be one of: {', '.join(valid_modules)}"
            )
    
    # Default prediction_types if not provided
    prediction_types = request.prediction_types or ["sales", "capacity", "stock"]
    
    # Validate prediction_types
    valid_types = ["sales", "capacity", "stock"]
    for pred_type in prediction_types:
        if pred_type not in valid_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid prediction_type: {pred_type}. Must be one of: {', '.join(valid_types)}"
            )
    
    try:
        prediction_service = PredictionService()
        segmented_predictions: Dict[str, Dict[str, Any]] = {}
        
        # Generate predictions for each module
        for mod in modules_to_forecast:
            module_predictions: Dict[str, Any] = {}
            
            # Generate sales predictions for each module
            if "sales" in prediction_types:
                try:
                    sales_pred = await prediction_service.predict_sales_enhanced(
                        db=db,
                        sucursal_id=request.sucursal_id,
                        forecast_days=request.forecast_days,
                        module=mod if mod != "total" else None  # "total" means all modules aggregated (None)
                    )
                    module_predictions["sales"] = sales_pred
                except Exception as e:
                    logger.warning(f"Could not generate sales predictions for {mod}: {e}", exc_info=True)
                    module_predictions["sales"] = {
                        "error": "generation_failed",
                        "message": f"No se pudieron generar predicciones de ventas para {mod}",
                        "forecast": [],
                        "confidence": "low"
                    }
            
            # Generate capacity predictions (only for recepcion or total)
            if "capacity" in prediction_types and mod in ["recepcion", "total"]:
                try:
                    capacity_pred = await prediction_service.predict_capacity(
                        db=db,
                        sucursal_id=request.sucursal_id,
                        forecast_days=request.forecast_days
                    )
                    module_predictions["capacity"] = capacity_pred
                except Exception as e:
                    logger.warning(f"Could not generate capacity predictions for {mod}: {e}", exc_info=True)
                    module_predictions["capacity"] = {
                        "error": "generation_failed",
                        "message": f"No se pudieron generar predicciones de capacidad para {mod}",
                        "forecast": [],
                        "confidence": "low"
                    }
            
            # Generate stock predictions (only for kidibar or total)
            if "stock" in prediction_types and mod in ["kidibar", "total"]:
                try:
                    stock_pred = await prediction_service.predict_stock_needs(
                        db=db,
                        sucursal_id=request.sucursal_id,
                        forecast_days=request.forecast_days
                    )
                    module_predictions["stock"] = stock_pred
                except Exception as e:
                    logger.warning(f"Could not generate stock predictions for {mod}: {e}", exc_info=True)
                    module_predictions["stock"] = {
                        "error": "generation_failed",
                        "message": f"No se pudieron generar predicciones de inventario para {mod}",
                        "forecast": [],
                        "confidence": "low"
                    }
            
            if module_predictions:
                segmented_predictions[mod] = module_predictions
        
        # Calculate overall confidence (lowest of all)
        confidences = []
        for mod_data in segmented_predictions.values():
            for pred_data in mod_data.values():
                if isinstance(pred_data, dict) and "confidence" in pred_data:
                    conf = pred_data["confidence"]
                    if conf in ["high", "medium", "low"]:
                        confidences.append(conf)
        
        overall_confidence = "low"
        if all(c == "high" for c in confidences):
            overall_confidence = "high"
        elif any(c == "high" for c in confidences) or all(c == "medium" for c in confidences):
            overall_confidence = "medium"
        
        elapsed = time.time() - start_time
        
        logger.info(
            f"Segmented predictions generated for user {user_id} in {elapsed:.2f}s "
            f"(modules: {modules_to_forecast}, types: {prediction_types}, forecast_days: {request.forecast_days})"
        )
        
        return SegmentedPredictionsResponse(
            success=True,
            message=f"Segmented predictions generated successfully in {elapsed:.2f}s",
            predictions=segmented_predictions,
            elapsed_seconds=round(elapsed, 2),
            overall_confidence=overall_confidence,
            forecast_days=request.forecast_days,
            modules=modules_to_forecast
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating segmented predictions for user {user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error generating segmented predictions. Please try again."
        )


@router.get("/arqueos", dependencies=[Depends(require_role(["super_admin", "admin_viewer"]))])
async def get_arqueos_report(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    sucursal_id: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    module: Optional[str] = Query(None, description="Module filter: 'recepcion', 'kidibar', or None for all"),
    use_cache: bool = Query(True, description="Use cache if available")
):
    """
    Get arqueos (day close) report with metrics and analysis.
    
    Security: super_admin and admin_viewer can view.
    """
    report_service = ReportService()
    
    parsed_start_date = None
    parsed_end_date = None
    
    if start_date:
        try:
            parsed_start_date = date.fromisoformat(start_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid start_date format. Use YYYY-MM-DD."
            )
    if end_date:
        try:
            parsed_end_date = date.fromisoformat(end_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid end_date format. Use YYYY-MM-DD."
            )
    
    # Validate module parameter
    if module and module not in ["recepcion", "kidibar", "all"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid module. Must be 'recepcion', 'kidibar', or 'all' (or omit for all)"
        )
    
    # Normalize "all" to None
    module_filter = None if module == "all" else module
    
    return await report_service.get_arqueos_report(
        db=db,
        sucursal_id=sucursal_id,
        start_date=parsed_start_date,
        end_date=parsed_end_date,
        module=module_filter,
        use_cache=use_cache
    )


@router.get("/arqueos/timeseries", dependencies=[Depends(require_role(["super_admin", "admin_viewer"]))])
async def get_arqueos_timeseries(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    sucursal_id: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    module: Optional[str] = Query(None, description="Module filter: 'recepcion', 'kidibar', or None for all"),
    use_cache: bool = Query(True, description="Use cache if available")
):
    """
    Get arqueos time series data aggregated by day.
    
    Security: super_admin and admin_viewer can view.
    """
    report_service = ReportService()
    
    parsed_start_date = None
    parsed_end_date = None
    
    if start_date:
        try:
            parsed_start_date = date.fromisoformat(start_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid start_date format. Use YYYY-MM-DD."
            )
    if end_date:
        try:
            parsed_end_date = date.fromisoformat(end_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid end_date format. Use YYYY-MM-DD."
            )
    
    # Validate module parameter
    if module and module not in ["recepcion", "kidibar", "all"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid module. Must be 'recepcion', 'kidibar', or 'all' (or omit for all)"
        )
    
    # Normalize "all" to None
    module_filter = None if module == "all" else module
    
    return await report_service.get_arqueos_timeseries(
        db=db,
        sucursal_id=sucursal_id,
        start_date=parsed_start_date,
        end_date=parsed_end_date,
        module=module_filter,
        use_cache=use_cache
    )


@router.get("/arqueos/heatmap", dependencies=[Depends(require_role(["super_admin", "admin_viewer"]))])
async def get_arqueos_heatmap(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    sucursal_id: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    module: Optional[str] = Query(None, description="Module filter: 'recepcion', 'kidibar', or None for all"),
    use_cache: bool = Query(True, description="Use cache if available")
):
    """
    Get arqueos heatmap data for calendar visualization.
    
    Security: super_admin and admin_viewer can view.
    """
    report_service = ReportService()
    
    parsed_start_date = None
    parsed_end_date = None
    
    if start_date:
        try:
            parsed_start_date = date.fromisoformat(start_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid start_date format. Use YYYY-MM-DD."
            )
    if end_date:
        try:
            parsed_end_date = date.fromisoformat(end_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid end_date format. Use YYYY-MM-DD."
            )
    
    # Validate module parameter
    if module and module not in ["recepcion", "kidibar", "all"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid module. Must be 'recepcion', 'kidibar', or 'all' (or omit for all)"
        )
    
    # Normalize "all" to None
    module_filter = None if module == "all" else module
    
    return await report_service.get_arqueos_heatmap(
        db=db,
        sucursal_id=sucursal_id,
        start_date=parsed_start_date,
        end_date=parsed_end_date,
        module=module_filter,
        use_cache=use_cache
    )


@router.get("/arqueos/trends", dependencies=[Depends(require_role(["super_admin", "admin_viewer"]))])
async def get_arqueos_trends(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    sucursal_id: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    module: Optional[str] = Query(None, description="Module filter: 'recepcion', 'kidibar', or None for all"),
    use_cache: bool = Query(True, description="Use cache if available")
):
    """
    Get temporal trends (MoM, WoW, YoY) for arqueos.
    
    Security: super_admin and admin_viewer can view.
    """
    report_service = ReportService()
    
    parsed_end_date = None
    
    if end_date:
        try:
            parsed_end_date = date.fromisoformat(end_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid end_date format. Use YYYY-MM-DD."
            )
    
    # Validate module parameter
    if module and module not in ["recepcion", "kidibar", "all"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid module. Must be 'recepcion', 'kidibar', or 'all' (or omit for all)"
        )
    
    # Normalize "all" to None
    module_filter = None if module == "all" else module
    
    return await report_service.get_arqueos_trends(
        db=db,
        sucursal_id=sucursal_id,
        end_date=parsed_end_date,
        module=module_filter,
        use_cache=use_cache
    )


@router.get("/arqueos/anomalies", dependencies=[Depends(require_role(["super_admin", "admin_viewer"]))])
async def get_arqueos_anomalies(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    sucursal_id: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    module: Optional[str] = Query(None, description="Module filter: 'recepcion', 'kidibar', or None for all"),
    use_cache: bool = Query(True, description="Use cache if available")
):
    """
    Detect anomalies in arqueos differences using IQR method.
    
    Security: super_admin and admin_viewer can view.
    """
    report_service = ReportService()
    
    parsed_start_date = None
    parsed_end_date = None
    
    if start_date:
        try:
            parsed_start_date = date.fromisoformat(start_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid start_date format. Use YYYY-MM-DD."
            )
    if end_date:
        try:
            parsed_end_date = date.fromisoformat(end_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid end_date format. Use YYYY-MM-DD."
            )
    
    # Validate module parameter
    if module and module not in ["recepcion", "kidibar", "all"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid module. Must be 'recepcion', 'kidibar', or 'all' (or omit for all)"
        )
    
    # Normalize "all" to None
    module_filter = None if module == "all" else module
    
    return await report_service.get_arqueos_anomalies(
        db=db,
        sucursal_id=sucursal_id,
        start_date=parsed_start_date,
        end_date=parsed_end_date,
        module=module_filter,
        use_cache=use_cache
    )


@router.get("/arqueos/by-user", dependencies=[Depends(require_role(["super_admin", "admin_viewer"]))])
async def get_arqueos_by_user(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    sucursal_id: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    module: Optional[str] = Query(None, description="Module filter: 'recepcion', 'kidibar', or None for all"),
    use_cache: bool = Query(True, description="Use cache if available")
):
    """
    Get arqueos analysis by user (who closes with most discrepancies).
    
    Security: super_admin and admin_viewer can view.
    """
    report_service = ReportService()
    
    parsed_start_date = None
    parsed_end_date = None
    
    if start_date:
        try:
            parsed_start_date = date.fromisoformat(start_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid start_date format. Use YYYY-MM-DD."
            )
    if end_date:
        try:
            parsed_end_date = date.fromisoformat(end_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid end_date format. Use YYYY-MM-DD."
            )
    
    # Validate module parameter
    if module and module not in ["recepcion", "kidibar", "all"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid module. Must be 'recepcion', 'kidibar', or 'all' (or omit for all)"
        )
    
    # Normalize "all" to None
    module_filter = None if module == "all" else module
    
    return await report_service.get_arqueos_by_user(
        db=db,
        sucursal_id=sucursal_id,
        start_date=parsed_start_date,
        end_date=parsed_end_date,
        module=module_filter,
        use_cache=use_cache
    )


@router.get("/arqueos/alerts", dependencies=[Depends(require_role(["super_admin", "admin_viewer"]))])
async def get_arqueos_alerts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    sucursal_id: Optional[str] = Query(None),
    module: Optional[str] = Query(None, description="Module filter: 'recepcion', 'kidibar', or None for all"),
    use_cache: bool = Query(True, description="Use cache if available")
):
    """
    Get arqueos alerts based on thresholds and patterns.
    
    Security: super_admin and admin_viewer can view.
    """
    report_service = ReportService()
    
    # Validate module parameter
    if module and module not in ["recepcion", "kidibar", "all"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid module. Must be 'recepcion', 'kidibar', or 'all' (or omit for all)"
        )
    
    # Normalize "all" to None
    module_filter = None if module == "all" else module
    
    return await report_service.get_arqueos_alerts(
        db=db,
        sucursal_id=sucursal_id,
        module=module_filter,
        use_cache=use_cache
    )


@router.get("/arqueos/recommendations", dependencies=[Depends(require_role(["super_admin", "admin_viewer"]))])
async def get_arqueos_recommendations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    sucursal_id: Optional[str] = Query(None),
    module: Optional[str] = Query(None, description="Module filter: 'recepcion', 'kidibar', or None for all"),
    use_cache: bool = Query(True, description="Use cache if available")
):
    """
    Generate actionable recommendations based on arqueos analysis.
    
    Security: super_admin and admin_viewer can view.
    """
    report_service = ReportService()
    
    # Validate module parameter
    if module and module not in ["recepcion", "kidibar", "all"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid module. Must be 'recepcion', 'kidibar', or 'all' (or omit for all)"
        )
    
    # Normalize "all" to None
    module_filter = None if module == "all" else module
    
    return await report_service.get_arqueos_recommendations(
        db=db,
        sucursal_id=sucursal_id,
        module=module_filter,
        use_cache=use_cache
    )


@router.get("/customers/summary", dependencies=[Depends(require_role(["super_admin", "admin_viewer"]))])
async def get_customers_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    sucursal_id: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    module: Optional[str] = Query(None, description="Module filter: 'recepcion', 'kidibar', or None for all"),
    use_cache: bool = Query(True, description="Use cache if available")
):
    """
    Get customers summary with aggregated metrics.
    
    Security: super_admin and admin_viewer can view.
    """
    report_service = ReportService()
    
    parsed_start_date = None
    parsed_end_date = None
    
    if start_date:
        try:
            parsed_start_date = date.fromisoformat(start_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid start_date format. Use YYYY-MM-DD."
            )
    if end_date:
        try:
            parsed_end_date = date.fromisoformat(end_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid end_date format. Use YYYY-MM-DD."
            )
    
    # Validate module parameter
    if module and module not in ["recepcion", "kidibar", "all"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid module. Must be 'recepcion', 'kidibar', or 'all' (or omit for all)"
        )
    
    # Normalize "all" to None
    module_filter = None if module == "all" else module
    
    return await report_service.get_customers_summary(
        db=db,
        sucursal_id=sucursal_id,
        start_date=parsed_start_date,
        end_date=parsed_end_date,
        module=module_filter,
        use_cache=use_cache
    )


@router.get("/customers/by-module", dependencies=[Depends(require_role(["super_admin", "admin_viewer"]))])
async def get_customers_by_module(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    sucursal_id: Optional[str] = Query(None),
    days: int = Query(30, ge=1, le=365, description="Number of days to look back (1-365)"),
    module: Optional[str] = Query(None, description="Module filter: 'recepcion', 'kidibar', or None for all"),
    use_cache: bool = Query(True, description="Use cache if available")
):
    """
    Get top customers report segmented by module (Recepción vs KidiBar).
    
    Security: super_admin and admin_viewer can view.
    """
    report_service = ReportService()
    
    # Validate module parameter
    if module and module not in ["recepcion", "kidibar", "all"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid module. Must be 'recepcion', 'kidibar', or 'all' (or omit for all)"
        )
    
    # Normalize "all" to None
    module_filter = None if module == "all" else module
    
    return await report_service.get_top_customers_by_module_report(
        db=db,
        sucursal_id=sucursal_id,
        days=days,
        module=module_filter,
        use_cache=use_cache
    )


@router.get("/modules/comparison", dependencies=[Depends(require_role(["super_admin", "admin_viewer"]))])
async def get_module_comparison(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    sucursal_id: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    use_cache: bool = Query(True, description="Use cache if available")
):
    """
    Get comparison report between Recepción and KidiBar modules.
    
    Security: super_admin and admin_viewer can view.
    """
    report_service = ReportService()
    
    parsed_start_date = None
    parsed_end_date = None
    
    if start_date:
        try:
            parsed_start_date = date.fromisoformat(start_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid start_date format. Use YYYY-MM-DD."
            )
    if end_date:
        try:
            parsed_end_date = date.fromisoformat(end_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid end_date format. Use YYYY-MM-DD."
            )
    
    return await report_service.get_module_comparison_report(
        db=db,
        sucursal_id=sucursal_id,
        start_date=parsed_start_date,
        end_date=parsed_end_date,
        use_cache=use_cache
    )


# ============================================================================
# INVENTORY REPORTS ENDPOINTS
# ============================================================================

@router.get("/inventory/timeseries", dependencies=[Depends(require_role(["super_admin", "admin_viewer"]))])
async def get_inventory_timeseries(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    sucursal_id: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    product_id: Optional[str] = Query(None, description="Optional product ID to filter by"),
    use_cache: bool = Query(True, description="Use cache if available")
):
    """
    Get inventory time series data aggregated by day.
    
    Tracks stock quantity changes over time by analyzing sale_items.
    
    Security: super_admin and admin_viewer can view.
    """
    report_service = ReportService()
    
    parsed_start_date = None
    parsed_end_date = None
    
    if start_date:
        try:
            parsed_start_date = date.fromisoformat(start_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid start_date format. Use YYYY-MM-DD."
            )
    if end_date:
        try:
            parsed_end_date = date.fromisoformat(end_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid end_date format. Use YYYY-MM-DD."
            )
    
    return await report_service.get_inventory_timeseries(
        db=db,
        sucursal_id=sucursal_id,
        start_date=parsed_start_date,
        end_date=parsed_end_date,
        product_id=product_id,
        use_cache=use_cache
    )


@router.get("/inventory/turnover", dependencies=[Depends(require_role(["super_admin", "admin_viewer"]))])
async def get_inventory_turnover(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    sucursal_id: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    use_cache: bool = Query(True, description="Use cache if available")
):
    """
    Get inventory turnover analysis.
    
    Calculates stock turnover rate and days on hand for each product.
    
    Security: super_admin and admin_viewer can view.
    """
    report_service = ReportService()
    
    parsed_start_date = None
    parsed_end_date = None
    
    if start_date:
        try:
            parsed_start_date = date.fromisoformat(start_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid start_date format. Use YYYY-MM-DD."
            )
    if end_date:
        try:
            parsed_end_date = date.fromisoformat(end_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid end_date format. Use YYYY-MM-DD."
            )
    
    return await report_service.get_inventory_turnover(
        db=db,
        sucursal_id=sucursal_id,
        start_date=parsed_start_date,
        end_date=parsed_end_date,
        use_cache=use_cache
    )


@router.get("/inventory/heatmap", dependencies=[Depends(require_role(["super_admin", "admin_viewer"]))])
async def get_inventory_heatmap(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    sucursal_id: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    use_cache: bool = Query(True, description="Use cache if available")
):
    """
    Get inventory heatmap data for calendar visualization.
    
    Shows stock levels and alerts intensity by day.
    
    Security: super_admin and admin_viewer can view.
    """
    report_service = ReportService()
    
    parsed_start_date = None
    parsed_end_date = None
    
    if start_date:
        try:
            parsed_start_date = date.fromisoformat(start_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid start_date format. Use YYYY-MM-DD."
            )
    if end_date:
        try:
            parsed_end_date = date.fromisoformat(end_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid end_date format. Use YYYY-MM-DD."
            )
    
    return await report_service.get_inventory_heatmap(
        db=db,
        sucursal_id=sucursal_id,
        start_date=parsed_start_date,
        end_date=parsed_end_date,
        use_cache=use_cache
    )


@router.get("/inventory/movement", dependencies=[Depends(require_role(["super_admin", "admin_viewer"]))])
async def get_inventory_movement(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    sucursal_id: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    use_cache: bool = Query(True, description="Use cache if available")
):
    """
    Get fast/slow movers analysis.
    
    Identifies products with high/low movement rates.
    
    Security: super_admin and admin_viewer can view.
    """
    report_service = ReportService()
    
    parsed_start_date = None
    parsed_end_date = None
    
    if start_date:
        try:
            parsed_start_date = date.fromisoformat(start_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid start_date format. Use YYYY-MM-DD."
            )
    if end_date:
        try:
            parsed_end_date = date.fromisoformat(end_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid end_date format. Use YYYY-MM-DD."
            )
    
    return await report_service.get_inventory_movement(
        db=db,
        sucursal_id=sucursal_id,
        start_date=parsed_start_date,
        end_date=parsed_end_date,
        use_cache=use_cache
    )


@router.get("/inventory/forecast", dependencies=[Depends(require_role(["super_admin", "admin_viewer"]))])
async def get_inventory_forecast(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    sucursal_id: Optional[str] = Query(None),
    forecast_days: int = Query(7, ge=1, le=30, description="Number of days to forecast (1-30)"),
    use_cache: bool = Query(True, description="Use cache if available")
):
    """
    Forecast inventory demand for next N days.
    
    Uses simple moving average based on recent sales.
    
    Security: super_admin and admin_viewer can view.
    """
    report_service = ReportService()
    
    return await report_service.get_inventory_forecast(
        db=db,
        sucursal_id=sucursal_id,
        forecast_days=forecast_days,
        use_cache=use_cache
    )


@router.get("/inventory/reorder-points", dependencies=[Depends(require_role(["super_admin", "admin_viewer"]))])
async def get_inventory_reorder_points(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    sucursal_id: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    use_cache: bool = Query(True, description="Use cache if available")
):
    """
    Calculate reorder points for products.
    
    ROP = (average_daily_sales * lead_time_days) + safety_stock
    
    Security: super_admin and admin_viewer can view.
    """
    report_service = ReportService()
    
    parsed_start_date = None
    parsed_end_date = None
    
    if start_date:
        try:
            parsed_start_date = date.fromisoformat(start_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid start_date format. Use YYYY-MM-DD."
            )
    if end_date:
        try:
            parsed_end_date = date.fromisoformat(end_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid end_date format. Use YYYY-MM-DD."
            )
    
    return await report_service.get_inventory_reorder_points(
        db=db,
        sucursal_id=sucursal_id,
        start_date=parsed_start_date,
        end_date=parsed_end_date,
        use_cache=use_cache
    )


@router.get("/inventory/alerts", dependencies=[Depends(require_role(["super_admin", "admin_viewer"]))])
async def get_inventory_alerts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    sucursal_id: Optional[str] = Query(None),
    use_cache: bool = Query(True, description="Use cache if available")
):
    """
    Get intelligent inventory alerts with context.
    
    Combines low stock alerts with turnover and reorder point data.
    
    Security: super_admin and admin_viewer can view.
    """
    report_service = ReportService()
    
    return await report_service.get_inventory_alerts(
        db=db,
        sucursal_id=sucursal_id,
        use_cache=use_cache
    )


@router.get("/inventory/recommendations", dependencies=[Depends(require_role(["super_admin", "admin_viewer"]))])
async def get_inventory_recommendations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    sucursal_id: Optional[str] = Query(None),
    use_cache: bool = Query(True, description="Use cache if available")
):
    """
    Generate actionable recommendations for inventory management.
    
    Security: super_admin and admin_viewer can view.
    """
    report_service = ReportService()
    
    return await report_service.get_inventory_recommendations(
        db=db,
        sucursal_id=sucursal_id,
        use_cache=use_cache
    )


# ============================================================================
# CUSTOMERS REPORTS ENDPOINTS
# ============================================================================

@router.get("/customers/list", dependencies=[Depends(require_role(["super_admin", "admin_viewer"]))])
async def get_customers_list(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    sucursal_id: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    module: Optional[str] = Query(None, description="Module filter: 'recepcion', 'kidibar', or None for all"),
    skip: int = Query(0, ge=0, description="Number of records to skip (for pagination)"),
    limit: int = Query(25, ge=1, le=100, description="Maximum number of records to return (1-100)"),
    sort_by: str = Query("revenue", description="Field to sort by: 'revenue', 'visits', 'recency'"),
    order: str = Query("desc", description="Sort order: 'asc' or 'desc'"),
    use_cache: bool = Query(True, description="Use cache if available")
):
    """
    Get paginated list of customers with sorting and filtering.
    
    Security: super_admin and admin_viewer can view.
    """
    report_service = ReportService()
    
    parsed_start_date = None
    parsed_end_date = None
    
    if start_date:
        try:
            parsed_start_date = date.fromisoformat(start_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid start_date format. Use YYYY-MM-DD."
            )
    if end_date:
        try:
            parsed_end_date = date.fromisoformat(end_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid end_date format. Use YYYY-MM-DD."
            )
    
    # Validate module parameter
    if module and module not in ["recepcion", "kidibar", "all"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid module. Must be 'recepcion', 'kidibar', or 'all' (or omit for all)"
        )
    
    # Normalize "all" to None
    module_filter = None if module == "all" else module
    
    # Validate sort_by
    valid_sort_fields = ["revenue", "visits", "recency"]
    if sort_by not in valid_sort_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid sort_by. Must be one of: {', '.join(valid_sort_fields)}"
        )
    
    # Validate order
    if order not in ["asc", "desc"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid order. Must be 'asc' or 'desc'"
        )
    
    return await report_service.get_customers_list_paginated(
        db=db,
        sucursal_id=sucursal_id,
        start_date=parsed_start_date,
        end_date=parsed_end_date,
        module=module_filter,
        skip=skip,
        limit=limit,
        sort_by=sort_by,
        order=order,
        use_cache=use_cache
    )


@router.get("/customers/rfm", dependencies=[Depends(require_role(["super_admin", "admin_viewer"]))])
async def get_customers_rfm(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    sucursal_id: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    use_cache: bool = Query(True, description="Use cache if available")
):
    """
    Get RFM (Recency, Frequency, Monetary) analysis for customers.
    
    RFM Segmentation:
    - Recency: Days since last visit (R)
    - Frequency: Number of visits (F)
    - Monetary: Total revenue (M)
    
    Each metric is scored 1-5, then combined into segments.
    
    Security: super_admin and admin_viewer can view.
    """
    report_service = ReportService()
    
    parsed_start_date = None
    parsed_end_date = None
    
    if start_date:
        try:
            parsed_start_date = date.fromisoformat(start_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid start_date format. Use YYYY-MM-DD."
            )
    if end_date:
        try:
            parsed_end_date = date.fromisoformat(end_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid end_date format. Use YYYY-MM-DD."
            )
    
    return await report_service.get_customers_rfm_analysis(
        db=db,
        sucursal_id=sucursal_id,
        start_date=parsed_start_date,
        end_date=parsed_end_date,
        use_cache=use_cache
    )


@router.get("/customers/cohorts", dependencies=[Depends(require_role(["super_admin", "admin_viewer"]))])
async def get_customers_cohorts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    sucursal_id: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    cohort_type: str = Query("monthly", description="Type of cohort grouping: 'monthly', 'weekly', 'daily'"),
    use_cache: bool = Query(True, description="Use cache if available")
):
    """
    Get cohort analysis for customers.
    
    Groups customers by their first visit (cohort) and tracks retention over time.
    
    Security: super_admin and admin_viewer can view.
    """
    report_service = ReportService()
    
    parsed_start_date = None
    parsed_end_date = None
    
    if start_date:
        try:
            parsed_start_date = date.fromisoformat(start_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid start_date format. Use YYYY-MM-DD."
            )
    if end_date:
        try:
            parsed_end_date = date.fromisoformat(end_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid end_date format. Use YYYY-MM-DD."
            )
    
    # Validate cohort_type
    valid_cohort_types = ["monthly", "weekly", "daily"]
    if cohort_type not in valid_cohort_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid cohort_type. Must be one of: {', '.join(valid_cohort_types)}"
        )
    
    return await report_service.get_customers_cohort_analysis(
        db=db,
        sucursal_id=sucursal_id,
        start_date=parsed_start_date,
        end_date=parsed_end_date,
        cohort_type=cohort_type,
        use_cache=use_cache
    )


@router.get("/customers/trends", dependencies=[Depends(require_role(["super_admin", "admin_viewer"]))])
async def get_customers_trends(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    sucursal_id: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    use_cache: bool = Query(True, description="Use cache if available")
):
    """
    Get comprehensive trends analysis combining RFM, Cohort, and behavioral metrics.
    
    This method provides advanced insights including:
    - Retention trends over time
    - Churn prediction indicators
    - Segment behavior analysis
    - Advanced temporal comparisons
    
    Security: super_admin and admin_viewer can view.
    """
    report_service = ReportService()
    
    parsed_start_date = None
    parsed_end_date = None
    
    if start_date:
        try:
            parsed_start_date = date.fromisoformat(start_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid start_date format. Use YYYY-MM-DD."
            )
    if end_date:
        try:
            parsed_end_date = date.fromisoformat(end_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid end_date format. Use YYYY-MM-DD."
            )
    
    return await report_service.get_customers_trends_analysis(
        db=db,
        sucursal_id=sucursal_id,
        start_date=parsed_start_date,
        end_date=parsed_end_date,
        use_cache=use_cache
    )


# ============================================================================
# MODULE-SPECIFIC STATS ENDPOINTS (for kidibar and recepcion panels)
# ============================================================================

@router.get("/kidibar", dependencies=[Depends(require_role(["kidibar", "recepcion", "super_admin", "admin_viewer", "monitor"]))])
async def get_kidibar_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    sucursal_id: str = Query(..., description="Sucursal ID (required)"),
    date: Optional[str] = Query(None, description="Target date (YYYY-MM-DD), defaults to today"),
    use_cache: bool = Query(True, description="Use cache if available")
):
    """
    Get KidiBar statistics for a sucursal.
    
    Returns statistics specific to the KidiBar module:
    - Sales of products (direct product sales)
    - Sales of product packages (packages containing only products)
    - Low stock alerts count
    - Peak hours for product sales
    
    Security: kidibar, recepcion, super_admin, and admin_viewer can view.
    Users with sucursal_id are automatically filtered to their sucursal.
    """
    report_service = ReportService()
    
    # Validate that user has access to the sucursal
    if current_user.sucursal_id and str(current_user.sucursal_id) != sucursal_id:
        # Allow if user is super_admin or admin_viewer
        user_role_str = current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role)
        if user_role_str not in ["super_admin", "admin_viewer"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para ver estadísticas de esta sucursal."
            )
    
    # Parse date if provided (avoid shadowing datetime.date by using date_str variable)
    parsed_date = None
    if date:
        try:
            # date parameter shadows datetime.date, so we reference the class directly
            # Import date class at function level to avoid shadowing
            from datetime import date as date_class
            parsed_date = date_class.fromisoformat(date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Use YYYY-MM-DD."
            )
    
    return await report_service.get_kidibar_stats(
        db=db,
        sucursal_id=sucursal_id,
        target_date=parsed_date,
        use_cache=use_cache
    )


@router.get("/recepcion", dependencies=[Depends(require_role(["recepcion", "super_admin", "admin_viewer", "monitor"]))])
async def get_recepcion_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    sucursal_id: str = Query(..., description="Sucursal ID (required)"),
    date: Optional[str] = Query(None, description="Target date (YYYY-MM-DD), defaults to today"),
    use_cache: bool = Query(True, description="Use cache if available")
):
    """
    Get reception statistics for a sucursal.
    
    Returns statistics specific to the recepcion module:
    - Sales of services (direct service sales)
    - Sales of service packages (packages containing only services)
    - Active timers for the sucursal
    - Peak hours for service sales
    - Tickets generated (service sales count)
    
    Security: recepcion, super_admin, and admin_viewer can view.
    Users with sucursal_id are automatically filtered to their sucursal.
    """
    report_service = ReportService()
    
    # Validate that user has access to the sucursal
    if current_user.sucursal_id and str(current_user.sucursal_id) != sucursal_id:
        # Allow if user is super_admin or admin_viewer
        user_role_str = current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role)
        if user_role_str not in ["super_admin", "admin_viewer"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para ver estadísticas de esta sucursal."
            )
    
    # Parse date if provided (avoid shadowing datetime.date by using date_str variable)
    parsed_date = None
    if date:
        try:
            # date parameter shadows datetime.date, so we reference the class directly
            # Import date class at function level to avoid shadowing
            from datetime import date as date_class
            parsed_date = date_class.fromisoformat(date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Use YYYY-MM-DD."
            )
    
    return await report_service.get_recepcion_stats(
        db=db,
        sucursal_id=sucursal_id,
        target_date=parsed_date,
        use_cache=use_cache
    )

