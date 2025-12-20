"""
Timer endpoints.

Security Rules:
- GET /timers/active: All authenticated users can view active timers
- POST /timers/{timer_id}/alerts/acknowledge: All authenticated users can acknowledge alerts
"""
import logging
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from uuid import UUID
from database import get_db
from services.timer_service import TimerService
from services.timer_alert_service import TimerAlertService
from utils.auth import get_current_user
from models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/timers", tags=["timers"])


@router.get("/active", response_model=List[dict])
async def get_active_timers(
    sucursal_id: Optional[str] = Query(None, description="Optional: Filter by sucursal ID"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get active timers with time_left calculated.
    
    Security: All authenticated users can view active timers.
    
    Returns:
        List of timer objects with time_left in minutes
    """
    timers = await TimerService.get_timers_with_time_left(
        db=db,
        sucursal_id=sucursal_id
    )
    return timers


@router.post("/{timer_id}/alerts/acknowledge", response_model=Dict[str, Any])
async def acknowledge_timer_alert(
    timer_id: UUID,
    alert_minutes: int = Query(..., ge=1, le=60, description="Alert threshold in minutes that was acknowledged"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Acknowledge a timer alert to stop it from being broadcasted.
    
    When a user acknowledges an alert, it will no longer be sent via WebSocket
    to any clients for that timer and alert threshold combination.
    
    Security: Any authenticated user can acknowledge alerts.
    
    Args:
        timer_id: Timer ID
        alert_minutes: Alert threshold in minutes (e.g., 5, 10, 15)
    
    Returns:
        Success message with acknowledgment confirmation
    """
    try:
        # Validate that timer exists and is active
        timers = await TimerService.get_timers_with_time_left(
            db=db,
            sucursal_id=None  # Check across all sucursales
        )
        
        timer_exists = any(str(timer.get("id")) == str(timer_id) for timer in timers)
        
        if not timer_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Timer {timer_id} not found or not active"
            )
        
        # Acknowledge the alert
        TimerAlertService.acknowledge_alert(str(timer_id), alert_minutes)
        
        logger.info(
            f"Alert acknowledged by user {current_user.id}: timer_id={timer_id}, alert_minutes={alert_minutes}",
            extra={
                "timer_id": str(timer_id),
                "alert_minutes": alert_minutes,
                "user_id": str(current_user.id)
            }
        )
        
        return {
            "success": True,
            "message": "Alert acknowledged successfully",
            "timer_id": str(timer_id),
            "alert_minutes": alert_minutes
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error acknowledging alert for timer {timer_id}: {e}",
            exc_info=True,
            extra={"timer_id": str(timer_id), "alert_minutes": alert_minutes}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error acknowledging alert"
        )

