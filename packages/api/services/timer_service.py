"""
Timer Service - Business logic for timer operations.

Clean Architecture:
- Separates business logic from API layer
- Uses async database operations
- Handles timer lifecycle (extend, get active, alerts)
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from uuid import UUID

from models.timer import Timer
from models.timer_history import TimerHistory
from models.sale import Sale

logger = logging.getLogger(__name__)


class TimerService:
    """Service for managing timers with business logic."""
    
    @staticmethod
    async def extend_timer(
        db: AsyncSession,
        timer_id: str,
        minutes_to_add: int
    ) -> Timer:
        """
        Extend an active timer by adding minutes.
        
        Args:
            db: Database session
            timer_id: UUID of timer to extend
            minutes_to_add: Minutes to add to timer
            
        Returns:
            Extended Timer object
            
        Raises:
            ValueError: If timer is not active or not found
        """
        # Get timer
        result = await db.execute(
            select(Timer).where(Timer.id == UUID(timer_id))
        )
        timer = result.scalar_one_or_none()
        
        if not timer:
            raise ValueError(f"Timer {timer_id} not found")
        
        if timer.status not in ["active", "extended"]:
            raise ValueError(f"Timer {timer_id} is not active or extended (status: {timer.status})")
        
        # Extend end_at time (sum time to existing end_at, don't reset)
        if timer.end_at:
            timer.end_at = timer.end_at + timedelta(minutes=minutes_to_add)
        else:
            # If no end_at, set it based on current time
            timer.end_at = datetime.now(timezone.utc) + timedelta(minutes=minutes_to_add)
        
        # Also extend exit_time to keep it synchronized with end_at
        # exit_time is used for ticket display and must match end_at
        if timer.exit_time:
            timer.exit_time = timer.exit_time + timedelta(minutes=minutes_to_add)
        else:
            # If no exit_time, set it to match end_at
            timer.exit_time = timer.end_at
        
        timer.status = "extended"
        timer.updated_at = datetime.now(timezone.utc)
        
        # Create history entry
        history = TimerHistory(
            timer_id=timer.id,
            event_type="extend",
            minutes_added=minutes_to_add,
            timestamp=datetime.now(timezone.utc)
        )
        db.add(history)
        
        await db.commit()
        await db.refresh(timer)
        
        logger.info(f"Timer {timer_id} extended by {minutes_to_add} minutes")
        return timer
    
    @staticmethod
    async def get_active_timers(
        db: AsyncSession,
        sucursal_id: Optional[str] = None
    ) -> List[Timer]:
        """
        Get all active, scheduled, and extended timers.
        
        This includes:
        - Timers with status='active' (already running)
        - Timers with status='scheduled' (waiting for delay period to pass)
        - Timers with status='extended' (have been extended but still running)
        
        Args:
            db: Database session
            sucursal_id: Optional sucursal ID to filter by
            
        Returns:
            List of Timer objects that are active, scheduled, or extended
        """
        from sqlalchemy import or_
        
        # Include 'active', 'scheduled', and 'extended' timers
        # Scheduled timers should be visible in the frontend immediately,
        # even though they haven't started counting down yet
        # Extended timers should remain visible after being extended
        query = select(Timer).where(
            or_(
                Timer.status == "active",
                Timer.status == "scheduled",
                Timer.status == "extended"
            )
        )
        
        if sucursal_id:
            # Join with Sale to filter by sucursal
            query = query.join(Sale, Timer.sale_id == Sale.id).where(
                Sale.sucursal_id == UUID(sucursal_id)
            )
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def get_timers_with_time_left(
        db: AsyncSession,
        sucursal_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get active timers with calculated time_left in minutes.
        
        Args:
            db: Database session
            sucursal_id: Optional sucursal ID to filter by
            
        Returns:
            List of timer dictionaries with time_left calculated
        """
        timers = await TimerService.get_active_timers(db, sucursal_id)
        now = datetime.now(timezone.utc)
        
        result = []
        for timer in timers:
            time_left_minutes = 0
            
            # For scheduled timers, show the total duration (end_at - start_at)
            # For active/extended timers, show remaining time (end_at - now)
            if timer.status == "scheduled":
                # Scheduled timer: show total duration that will be available when it starts
                if timer.start_at and timer.end_at:
                    # Normalize both datetimes to UTC
                    start_at = timer.start_at
                    if start_at.tzinfo is None:
                        start_at = start_at.replace(tzinfo=timezone.utc)
                    else:
                        start_at = start_at.astimezone(timezone.utc)
                    
                    end_at = timer.end_at
                    if end_at.tzinfo is None:
                        end_at = end_at.replace(tzinfo=timezone.utc)
                    else:
                        end_at = end_at.astimezone(timezone.utc)
                    
                    # Calculate total duration: end_at - start_at
                    delta = end_at - start_at
                    time_left_minutes = max(0, int(delta.total_seconds() / 60))
            elif timer.end_at:
                # Active/extended timer: show remaining time (end_at - now)
                # Normalize timer.end_at to UTC if it's naive or timezone-aware
                # This handles both cases: datetimes from DB (should be aware with UTC connection config)
                # and datetimes created in tests (may be naive)
                end_at = timer.end_at
                if end_at.tzinfo is None:
                    # If naive, assume UTC (defensive programming for tests)
                    end_at = end_at.replace(tzinfo=timezone.utc)
                else:
                    # If aware, normalize to UTC
                    end_at = end_at.astimezone(timezone.utc)
                
                delta = end_at - now
                time_left_minutes = max(0, int(delta.total_seconds() / 60))
            
            # Only include timers with time_left > 0 (exclude expired/finished timers)
            # This ensures that only truly active timers are returned
            if time_left_minutes > 0:
                result.append({
                    "id": str(timer.id),
                    "sale_id": str(timer.sale_id),
                    "service_id": str(timer.service_id),
                    "child_name": timer.child_name,
                    "child_age": timer.child_age,
                    "status": timer.status,
                    "start_at": timer.start_at.isoformat() if timer.start_at else None,
                    "end_at": timer.end_at.isoformat() if timer.end_at else None,
                    "time_left_minutes": time_left_minutes,
                    "updated_at": timer.updated_at.isoformat() if timer.updated_at else None,  # Server timestamp for conflict resolution
                })
        
        return result
    
    @staticmethod
    async def get_timers_nearing_end(
        db: AsyncSession,
        minutes_before: int = 5,
        sucursal_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get timers that are nearing their end time.
        
        Args:
            db: Database session
            minutes_before: Alert when timer has this many minutes left
            sucursal_id: Optional sucursal ID to filter by
            
        Returns:
            List of timer dictionaries that are nearing end
        """
        timers = await TimerService.get_timers_with_time_left(db, sucursal_id)
        
        result = []
        for timer_data in timers:
            time_left = timer_data.get("time_left_minutes", 0)
            if 0 < time_left <= minutes_before:
                result.append(timer_data)
        
        return result
