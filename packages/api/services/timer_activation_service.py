"""
Timer Activation Service - Background task for activating scheduled timers.

Clean Architecture:
- Separates timer activation logic from timer service
- Uses existing TimerService and database models
- Handles periodic polling and batch activation of scheduled timers
"""
import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from models.timer import Timer
from models.timer_history import TimerHistory
from database import AsyncSessionLocal

logger = logging.getLogger(__name__)


class TimerActivationService:
    """Service for activating scheduled timers after their delay period."""
    
    @staticmethod
    async def activate_scheduled_timers(db: AsyncSession) -> int:
        """
        Activate scheduled timers that have passed their start_delay_minutes period.
        
        Logic:
        - Finds timers with status='scheduled'
        - Checks if created_at + start_delay_minutes <= now
        - Updates status to 'active' in batch
        - Creates history entries for activated timers
        
        Args:
            db: Database session
            
        Returns:
            Number of timers activated
        """
        try:
            now = datetime.now(timezone.utc)
            
            # Query scheduled timers that should be activated
            # We need to check: created_at + INTERVAL '1 minute' * start_delay_minutes <= now
            # For PostgreSQL, we use SQL expression: created_at + (start_delay_minutes || ' minutes')::interval
            # However, SQLAlchemy async doesn't easily support interval arithmetic with columns
            # So we'll use a hybrid approach: filter by status first, then check in Python
            # This is efficient because:
            # 1. Most queries will have few scheduled timers (status='scheduled' is temporary)
            # 2. The status column should be indexed for fast filtering
            # 3. The Python calculation is trivial (datetime arithmetic)
            query = select(Timer).where(Timer.status == "scheduled")
            result = await db.execute(query)
            scheduled_timers = result.scalars().all()
            
            if not scheduled_timers:
                return 0
            
            # Filter timers that should be activated
            # Calculate activation time: created_at + start_delay_minutes
            timers_to_activate: List[Timer] = []
            for timer in scheduled_timers:
                activation_time = timer.created_at + timedelta(minutes=timer.start_delay_minutes)
                
                # Check if activation time has passed
                if activation_time <= now:
                    timers_to_activate.append(timer)
            
            if not timers_to_activate:
                return 0
            
            # Batch update: activate all eligible timers
            timer_ids = [timer.id for timer in timers_to_activate]
            
            # Update status to 'active' in batch
            update_stmt = (
                update(Timer)
                .where(Timer.id.in_(timer_ids))
                .values(status="active", updated_at=now)
            )
            await db.execute(update_stmt)
            
            # Create history entries for activated timers (optional, for audit trail)
            for timer in timers_to_activate:
                history = TimerHistory(
                    timer_id=timer.id,
                    event_type="start",  # Timer started after delay
                    minutes_added=None,
                    timestamp=now
                )
                db.add(history)
            
            await db.commit()
            
            # Structured logging with context
            logger.info(
                f"Activated {len(timers_to_activate)} scheduled timers",
                extra={
                    "activated_count": len(timers_to_activate),
                    "timer_ids": [str(tid) for tid in timer_ids],
                    "activation_time": now.isoformat(),
                }
            )
            
            return len(timers_to_activate)
            
        except Exception as e:
            logger.error(f"Error activating scheduled timers: {e}", exc_info=True)
            await db.rollback()
            raise


async def periodic_timer_activation_task(
    interval_seconds: int = 60,
    business_hours_start: int = 13,
    business_hours_end: int = 22,
    timezone_str: str = "America/Mexico_City"
):
    """
    Background task optimizado para activación de timers programados.
    
    Optimizaciones:
    - Intervalo aumentado a 60s (alineado con granularidad de minutos)
    - Solo ejecuta en horario laboral (configurable)
    - Timezone-aware (horarios en CDMX)
    
    Args:
        interval_seconds: Segundos entre checks (default: 60)
        business_hours_start: Hora inicio horario laboral en CDMX (default: 1 PM)
        business_hours_end: Hora fin horario laboral en CDMX (default: 10 PM)
        timezone_str: Timezone para horario laboral (default: America/Mexico_City)
    """
    import os
    from zoneinfo import ZoneInfo
    
    # Obtener configuración de env vars (sin hardcodeo)
    interval_seconds = int(os.getenv("TIMER_ACTIVATION_INTERVAL", str(interval_seconds)))
    business_hours_start = int(os.getenv("BUSINESS_HOURS_START", str(business_hours_start)))
    business_hours_end = int(os.getenv("BUSINESS_HOURS_END", str(business_hours_end)))
    timezone_str = os.getenv("BUSINESS_TIMEZONE", timezone_str)
    
    logger.info(
        f"Starting periodic timer activation task: "
        f"interval={interval_seconds}s, "
        f"business_hours={business_hours_start}-{business_hours_end} {timezone_str}"
    )
    
    while True:
        try:
            await asyncio.sleep(interval_seconds)
            
            # OPTIMIZACIÓN: Verificar horario laboral en CDMX
            now_utc = datetime.now(timezone.utc)
            now_local = now_utc.astimezone(ZoneInfo(timezone_str))
            current_hour = now_local.hour
            
            if current_hour < business_hours_start or current_hour >= business_hours_end:
                # Fuera de horario laboral, skip iteration
                logger.debug(
                    f"Outside business hours ({current_hour}:00), skipping activation",
                    extra={
                        "current_hour": current_hour,
                        "business_hours": f"{business_hours_start}-{business_hours_end}"
                    }
                )
                continue
            
            # Process scheduled timers
            async with AsyncSessionLocal() as db:
                try:
                    activated_count = await TimerActivationService.activate_scheduled_timers(db)
                    
                    # Log even when no timers activated (lower level, but still visible for diagnostics)
                    if activated_count > 0:
                        logger.info(
                            f"Timer activation check completed: {activated_count} timers activated",
                            extra={"activated_count": activated_count}
                        )
                    else:
                        logger.debug(
                            "Timer activation check completed: no timers to activate",
                            extra={"activated_count": 0}
                        )
                    
                finally:
                    # Ensure session is closed
                    await db.close()
                    
        except asyncio.CancelledError:
            logger.info("Periodic timer activation task cancelled")
            break
        except Exception as e:
            logger.error(
                f"Error in periodic timer activation task: {e}",
                exc_info=True
            )
            # Continue running even if one iteration fails
            # Wait a bit before retrying to avoid tight loop on persistent errors
            await asyncio.sleep(10)

