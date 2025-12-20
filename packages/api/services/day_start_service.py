"""
Day start service - Business logic for day start operations.
"""
import logging
from datetime import datetime, timezone, date
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from models.day_start import DayStart
from models.sucursal import Sucursal
from schemas.day_start import DayStartCreate
from utils.datetime_helpers import get_business_date_in_timezone

logger = logging.getLogger(__name__)


class DayStartService:
    """Service for handling day start operations."""
    
    @staticmethod
    async def start_day(
        db: AsyncSession,
        start_data: DayStartCreate,
        user_id: str
    ) -> DayStart:
        """
        Start day for a sucursal.
        
        Validates that no other day is currently active for the sucursal.
        
        Args:
            db: Database session
            start_data: Day start creation data
            user_id: ID of the user starting the day
            
        Returns:
            Created DayStart object
            
        Raises:
            ValueError: If a day is already active for the sucursal
        """
        try:
            # Check if there's an active day for this sucursal
            active_day = await DayStartService.get_active_day(
                db=db,
                sucursal_id=start_data.sucursal_id
            )
            
            if active_day:
                raise ValueError(
                    f"Day is already active for sucursal {start_data.sucursal_id}. "
                    f"Please close the current day before starting a new one."
                )
            
            # Get sucursal timezone
            sucursal_result = await db.execute(
                select(Sucursal).where(Sucursal.id == start_data.sucursal_id)
            )
            sucursal = sucursal_result.scalar_one_or_none()
            if not sucursal:
                raise ValueError(f"Sucursal {start_data.sucursal_id} not found")
            
            timezone_str = sucursal.timezone or "America/Mexico_City"
            
            # Get current UTC datetime
            now_utc = datetime.now(timezone.utc)
            
            # Create new DayStart record
            # Convert user_id to UUID if it's a string
            import uuid
            if isinstance(user_id, str):
                user_uuid = uuid.UUID(user_id)
            else:
                user_uuid = user_id
            
            day_start = DayStart(
                sucursal_id=start_data.sucursal_id,
                usuario_id=user_uuid,
                started_at=now_utc,
                initial_cash_cents=start_data.initial_cash_cents,
                is_active=True
            )
            db.add(day_start)
            await db.flush()  # Flush to get day_start.id
            
            await db.commit()
            
            await db.refresh(day_start)
            
            logger.info(
                f"Day started for sucursal {start_data.sucursal_id} "
                f"by user {user_id} with initial cash: {start_data.initial_cash_cents} cents"
            )
            return day_start
                
        except ValueError:
            await db.rollback()
            raise
        except Exception as e:
            logger.error(f"Error starting day: {e}", exc_info=True)
            await db.rollback()
            raise
    
    @staticmethod
    async def get_active_day(
        db: AsyncSession,
        sucursal_id: str
    ) -> Optional[DayStart]:
        """
        Get the active day start for a sucursal.
        
        Args:
            db: Database session
            sucursal_id: Sucursal ID (string, will be converted to UUID)
            
        Returns:
            Active DayStart object or None if no active day
        """
        import uuid
        # Convert string to UUID (handle both string and UUID inputs)
        try:
            if isinstance(sucursal_id, uuid.UUID):
                sucursal_uuid = sucursal_id
            else:
                sucursal_uuid = uuid.UUID(str(sucursal_id))
        except (ValueError, AttributeError):
            logger.error(f"Invalid sucursal_id format: {sucursal_id}")
            return None
        
        result = await db.execute(
            select(DayStart).where(
                and_(
                    DayStart.sucursal_id == sucursal_uuid,
                    DayStart.is_active == True
                )
            ).order_by(DayStart.started_at.desc())
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_day_status(
        db: AsyncSession,
        sucursal_id: str
    ) -> dict:
        """
        Get day status (open/closed) for a sucursal.
        
        Args:
            db: Database session
            sucursal_id: Sucursal ID
            
        Returns:
            Dict with is_open, day_start (if open), current_date (in UTC), 
            and current_business_date (in sucursal timezone)
        """
        import uuid
        try:
            if isinstance(sucursal_id, uuid.UUID):
                sucursal_uuid = sucursal_id
            else:
                sucursal_uuid = uuid.UUID(str(sucursal_id))
        except (ValueError, AttributeError):
            logger.error(f"Invalid sucursal_id format: {sucursal_id}")
            sucursal_uuid = None
        
        # Get sucursal timezone
        timezone_str = "America/Mexico_City"  # Default
        if sucursal_uuid:
            sucursal_result = await db.execute(
                select(Sucursal).where(Sucursal.id == sucursal_uuid)
            )
            sucursal = sucursal_result.scalar_one_or_none()
            if sucursal:
                timezone_str = sucursal.timezone or "America/Mexico_City"
        
        active_day = await DayStartService.get_active_day(
            db=db,
            sucursal_id=sucursal_id
        )
        
        # Debug logging
        if active_day:
            logger.info(
                f"[DEBUG get_day_status] Active day found for sucursal {sucursal_id}: "
                f"id={active_day.id}, started_at={active_day.started_at}, "
                f"started_at_type={type(active_day.started_at)}, "
                f"is_active={active_day.is_active}"
            )
        else:
            logger.info(
                f"[DEBUG get_day_status] No active day found for sucursal {sucursal_id}"
            )
        
        now_utc = datetime.now(timezone.utc)
        current_business_date = get_business_date_in_timezone(now_utc, timezone_str)
        
        status_dict = {
            "is_open": active_day is not None,
            "day_start": active_day,
            "current_date": now_utc,
            "current_business_date": current_business_date.isoformat()  # YYYY-MM-DD format
        }
        
        # Debug: Log what we're returning
        logger.info(
            f"[DEBUG get_day_status] Returning status_dict: "
            f"is_open={status_dict['is_open']}, "
            f"day_start={'present' if status_dict['day_start'] else 'None'}, "
            f"day_start_type={type(status_dict['day_start']) if status_dict['day_start'] else 'None'}"
        )
        
        return status_dict
    
    @staticmethod
    async def close_active_day(
        db: AsyncSession,
        sucursal_id: str
    ) -> Optional[DayStart]:
        """
        Mark the active day as closed (is_active = False).
        
        This is called when a day is closed via DayCloseService.
        
        Args:
            db: Database session
            sucursal_id: Sucursal ID (string, will be converted to UUID)
            
        Returns:
            Updated DayStart object or None if no active day
        """
        active_day = await DayStartService.get_active_day(
            db=db,
            sucursal_id=sucursal_id
        )
        
        if active_day:
            active_day.is_active = False
            active_day.updated_at = datetime.now(timezone.utc)
            await db.flush()
            await db.commit()
            await db.refresh(active_day)
            
            logger.info(
                f"Active day closed for sucursal {sucursal_id}"
            )
            return active_day
        
        return None

