"""
Operations endpoints - Day start/close operations.

Handles business day operations:
- Start day: Initialize a new business day
- Close day: Close the current business day with cash reconciliation
- Get day status: Check if a day is currently active
"""
import logging
from datetime import datetime, timezone, date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from models.user import User
from schemas.day_start import DayStartCreate, DayStartRead, DayStatusRead
from schemas.day_close import DayCloseCreate, DayCloseRead, PreviewDayCloseRead
from services.day_start_service import DayStartService
from services.day_close_service import DayCloseService
from utils.auth import get_current_user, require_role
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/operations", tags=["operations"])


@router.post("/day/start", response_model=Dict[str, Any], dependencies=[Depends(require_role(["kidibar", "recepcion", "super_admin"]))])
async def start_day(
    start_data: DayStartCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Start a new business day for a sucursal.
    
    Security: Only kidibar, recepcion, and super_admin roles can start days.
    Other roles (admin_viewer, monitor) can view but not execute.
    
    Validates that no other day is currently active for the sucursal.
    Creates a new DayStart record with is_active=True.
    
    Args:
        start_data: Day start data (sucursal_id, initial_cash_cents)
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Dictionary with day_start object and success message
        
    Raises:
        HTTPException: If a day is already active (400) or other error (500)
    """
    try:
        # Validate that user has access to the sucursal
        if current_user.sucursal_id and str(current_user.sucursal_id) != str(start_data.sucursal_id):
            # Allow if user is super_admin or admin_viewer
            user_role_value = current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role)
            if user_role_value not in ["super_admin", "admin_viewer"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No tienes permisos para iniciar el día en esta sucursal."
                )
        
        # Start the day using the service
        day_start = await DayStartService.start_day(
            db=db,
            start_data=start_data,
            user_id=str(current_user.id)
        )
        
        # Debug logging after day start
        logger.info(
            f"[DEBUG start_day endpoint] Day started successfully: "
            f"id={day_start.id}, started_at={day_start.started_at}, "
            f"started_at_type={type(day_start.started_at)}, "
            f"started_at_repr={repr(day_start.started_at)}, "
            f"is_active={day_start.is_active}"
        )
        
        # Serialize the day start for response
        started_at_iso = day_start.started_at.isoformat()
        logger.info(
            f"[DEBUG start_day endpoint] Serialized started_at to ISO: {started_at_iso}"
        )
        
        day_start_dict = {
            "id": str(day_start.id),
            "sucursal_id": str(day_start.sucursal_id),
            "usuario_id": str(day_start.usuario_id),
            "started_at": started_at_iso,
            "initial_cash_cents": day_start.initial_cash_cents,
            "is_active": day_start.is_active,
            "created_at": day_start.created_at.isoformat(),
            "updated_at": day_start.updated_at.isoformat(),
        }
        
        logger.info(
            f"Day started successfully for sucursal {start_data.sucursal_id} "
            f"by user {current_user.id}"
        )
        
        return {
            "success": True,
            "message": "Día iniciado exitosamente",
            "day_start": day_start_dict
        }
        
    except ValueError as e:
        logger.warning(f"Validation error starting day: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting day: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al iniciar el día"
        )


@router.post("/day/close", response_model=Dict[str, Any], dependencies=[Depends(require_role(["kidibar", "recepcion", "super_admin"]))])
async def close_day(
    close_data: DayCloseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Close the current business day for a sucursal.
    
    Security: Only kidibar, recepcion, and super_admin roles can close days.
    Other roles (admin_viewer, monitor) can view but not execute.
    
    Validates that a day is currently active for the sucursal.
    Creates a DayClose record and sets the active DayStart to is_active=False.
    
    Args:
        close_data: Day close data (sucursal_id, date, system_total_cents, physical_count_cents, etc.)
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Dictionary with day_close object and success message
        
    Raises:
        HTTPException: If no day is active (400) or other error (500)
    """
    try:
        # Validate that user has access to the sucursal
        if current_user.sucursal_id and str(current_user.sucursal_id) != str(close_data.sucursal_id):
            # Allow if user is super_admin or admin_viewer
            user_role_value = current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role)
            if user_role_value not in ["super_admin", "admin_viewer"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No tienes permisos para cerrar el día en esta sucursal."
                )
        
        # Set usuario_id from current_user if not provided
        if close_data.usuario_id is None:
            close_data.usuario_id = current_user.id
        
        # Close the day using the service
        # Pass user role to filter arqueo calculation for KidiBar
        user_role_value = current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role)
        day_close = await DayCloseService.close_day(
            db=db,
            close_data=close_data,
            user_id=str(current_user.id),
            user_role=user_role_value
        )
        
        # Serialize the day close for response
        day_close_dict = {
            "id": str(day_close.id),
            "sucursal_id": str(day_close.sucursal_id),
            "usuario_id": str(day_close.usuario_id),
            "date": day_close.date.isoformat(),
            "system_total_cents": day_close.system_total_cents,
            "physical_count_cents": day_close.physical_count_cents,
            "difference_cents": day_close.difference_cents,
            "totals": day_close.totals,
            "notes": day_close.notes,
            "created_at": day_close.created_at.isoformat(),
            "updated_at": day_close.updated_at.isoformat(),
        }
        
        logger.info(
            f"Day closed successfully for sucursal {close_data.sucursal_id} "
            f"by user {current_user.id}"
        )
        
        return {
            "success": True,
            "message": "Día cerrado exitosamente",
            "day_close": day_close_dict
        }
        
    except ValueError as e:
        logger.warning(f"Validation error closing day: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error closing day: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al cerrar el día"
        )


@router.get("/day/close/preview", response_model=PreviewDayCloseRead, dependencies=[Depends(require_role(["recepcion", "kidibar", "super_admin", "admin_viewer", "monitor"]))])
async def preview_day_close(
    sucursal_id: str = Query(..., description="Sucursal ID to preview day close for"),
    module: Optional[str] = Query(None, description="Module context: 'kidibar' to filter only product sales, 'recepcion' for all sales. If not provided, uses user role as fallback."),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> PreviewDayCloseRead:
    """
    Preview day close calculations without actually closing the day.
    
    Returns the expected system total and breakdown that would be calculated
    if the day were closed right now.
    
    Security: Only recepcion, kidibar, super_admin, admin_viewer, and monitor roles can preview day close.
    Users with sucursal_id are automatically filtered to their sucursal.
    
    The 'module' parameter determines which sales to include:
    - 'kidibar': Only product and product package sales (for Kidibar context)
    - 'recepcion' or None: All sales (default behavior)
    If 'module' is not provided, the user's role is used as fallback.
    """
    try:
        # Validate that user has access to the sucursal
        if current_user.sucursal_id and str(current_user.sucursal_id) != sucursal_id:
            user_role_value = current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role)
            if user_role_value not in ["super_admin", "admin_viewer"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No tienes permisos para ver el preview del cierre de día de esta sucursal."
                )
        
        # Determine which role/context to use for filtering:
        # 1. If module parameter is provided, use it (kidibar context)
        # 2. Otherwise, use user role as fallback
        if module == "kidibar":
            # When accessing from Kidibar context, always filter to kidibar sales
            filter_role = "kidibar"
        else:
            # Use user role as fallback (existing behavior)
            filter_role = current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role)
        
        preview_data = await DayCloseService.preview_day_close(
            db=db,
            sucursal_id=sucursal_id,
            user_role=filter_role
        )
        return PreviewDayCloseRead.model_validate(preview_data)
    except ValueError as e:
        logger.warning(f"Validation error previewing day close: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error previewing day close: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener el preview del cierre de día"
        )


@router.get("/day/status", response_model=DayStatusRead)
async def get_day_status(
    sucursal_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> DayStatusRead:
    """
    Get the current day status for a sucursal.
    
    Returns whether a day is currently active and the active day_start if available.
    
    Args:
        sucursal_id: Sucursal ID to check status for
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        DayStatusRead with is_open, day_start (if open), and current_date
        
    Raises:
        HTTPException: If user doesn't have access to the sucursal (403)
    """
    try:
        # Validate that user has access to the sucursal
        if current_user.sucursal_id and str(current_user.sucursal_id) != sucursal_id:
            # Allow if user is super_admin or admin_viewer
            user_role_value = current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role)
            if user_role_value not in ["super_admin", "admin_viewer"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No tienes permisos para consultar el estado del día de esta sucursal."
                )
        
        # Get day status using the service
        status_dict = await DayStartService.get_day_status(
            db=db,
            sucursal_id=sucursal_id
        )
        
        # Serialize day_start if it exists
        day_start_read = None
        logger.info(f"[DEBUG get_day_status endpoint] status_dict keys: {list(status_dict.keys())}")
        logger.info(f"[DEBUG get_day_status endpoint] is_open={status_dict.get('is_open')}, day_start present={status_dict.get('day_start') is not None}")
        
        if status_dict.get("day_start"):
            day_start = status_dict["day_start"]
            
            # Debug logging before serialization
            logger.info(
                f"[DEBUG get_day_status endpoint] Serializing day_start: "
                f"id={day_start.id}, started_at={day_start.started_at}, "
                f"started_at_type={type(day_start.started_at)}, "
                f"started_at_repr={repr(day_start.started_at)}"
            )
            
            try:
                day_start_read = DayStartRead(
                    id=day_start.id,
                    sucursal_id=day_start.sucursal_id,
                    usuario_id=day_start.usuario_id,
                    started_at=day_start.started_at,
                    initial_cash_cents=day_start.initial_cash_cents,
                    is_active=day_start.is_active,
                    created_at=day_start.created_at,
                    updated_at=day_start.updated_at,
                )
                
                # Debug logging after Pydantic serialization
                logger.info(
                    f"[DEBUG get_day_status endpoint] After Pydantic serialization: "
                    f"day_start_read.started_at={day_start_read.started_at}, "
                    f"started_at_type={type(day_start_read.started_at)}, "
                    f"started_at_repr={repr(day_start_read.started_at)}"
                )
            except Exception as e:
                logger.error(f"[DEBUG get_day_status endpoint] Error serializing day_start: {e}", exc_info=True)
                raise
        else:
            logger.info(
                f"[DEBUG get_day_status endpoint] No day_start in status_dict, "
                f"is_open={status_dict.get('is_open')}"
            )
        
        response = DayStatusRead(
            is_open=status_dict["is_open"],
            day_start=day_start_read,
            current_date=status_dict["current_date"],
            current_business_date=status_dict.get("current_business_date")
        )
        
        # Debug: Log final response structure
        logger.info(
            f"[DEBUG get_day_status endpoint] Final response: "
            f"is_open={response.is_open}, "
            f"day_start={'present' if response.day_start else 'None'}, "
            f"day_start.started_at={response.day_start.started_at if response.day_start else 'N/A'}"
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting day status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener el estado del día"
        )


@router.get("/day/closes", response_model=List[DayCloseRead], dependencies=[Depends(require_role(["recepcion", "kidibar", "super_admin", "admin_viewer", "monitor"]))])
async def list_day_closes(
    sucursal_id: Optional[str] = Query(None, description="Filter by sucursal ID"),
    start_date: Optional[str] = Query(None, description="Filter by start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Filter by end date (YYYY-MM-DD)"),
    skip: int = Query(0, ge=0, description="Number of records to skip (for pagination)"),
    limit: int = Query(25, ge=1, le=500, description="Maximum number of records to return (1-500, default: 25)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[DayCloseRead]:
    """
    Get paginated list of day closes with optional filters.
    
    Security: Only recepcion, kidibar, super_admin, admin_viewer, and monitor roles can view day closes.
    Users with sucursal_id are automatically filtered to their sucursal if no sucursal_id is provided.
    
    Args:
        sucursal_id: Optional sucursal ID to filter by
        start_date: Optional start date (YYYY-MM-DD format)
        end_date: Optional end date (YYYY-MM-DD format)
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List of DayCloseRead objects (paginated, ordered by date descending)
        
    Raises:
        HTTPException: If date format is invalid (400) or other error (500)
    """
    try:
        # Auto-filter by user's sucursal if they have one and no sucursal_id provided
        target_sucursal_id = sucursal_id
        if not target_sucursal_id and current_user.sucursal_id:
            target_sucursal_id = str(current_user.sucursal_id)
        
        # Validate that user has access to the requested sucursal
        if target_sucursal_id and current_user.sucursal_id:
            if str(current_user.sucursal_id) != target_sucursal_id:
                # Allow if user is super_admin or admin_viewer
                user_role_value = current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role)
                if user_role_value not in ["super_admin", "admin_viewer"]:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="No tienes permisos para ver arqueos de esta sucursal."
                    )
        
        # Parse date filters
        parsed_start_date = None
        parsed_end_date = None
        
        if start_date:
            try:
                parsed_start_date = date.fromisoformat(start_date)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid start_date format. Use YYYY-MM-DD format."
                )
        
        if end_date:
            try:
                parsed_end_date = date.fromisoformat(end_date)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid end_date format. Use YYYY-MM-DD format."
                )
        
        # Get day closes using the service
        day_closes = await DayCloseService.list_day_closes(
            db=db,
            sucursal_id=target_sucursal_id,
            start_date=parsed_start_date,
            end_date=parsed_end_date,
            skip=skip,
            limit=limit
        )
        
        # Serialize to DayCloseRead schema
        # Extract started_at from totals JSON (hybrid pattern)
        day_closes_read = []
        for dc in day_closes:
            started_at_iso = None
            if dc.totals and isinstance(dc.totals, dict) and "started_at" in dc.totals:
                started_at_iso = dc.totals["started_at"]
            
            day_close_read = DayCloseRead(
                id=dc.id,
                sucursal_id=dc.sucursal_id,
                usuario_id=dc.usuario_id,
                date=dc.date,
                system_total_cents=dc.system_total_cents,
                physical_count_cents=dc.physical_count_cents,
                difference_cents=dc.difference_cents,
                totals=dc.totals,
                notes=dc.notes,
                created_at=dc.created_at,
                updated_at=dc.updated_at,
                started_at=started_at_iso,  # Extracted from totals JSON
                closed_at=dc.created_at,  # Alias for created_at (when day was closed)
            )
            day_closes_read.append(day_close_read)
        
        logger.info(
            f"Retrieved {len(day_closes_read)} day closes for user {current_user.id} "
            f"(sucursal_id={target_sucursal_id}, skip={skip}, limit={limit})"
        )
        
        return day_closes_read
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing day closes: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener el historial de arqueos"
        )
