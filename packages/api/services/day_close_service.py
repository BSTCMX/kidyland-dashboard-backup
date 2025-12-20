"""
Day close service - Business logic for day close operations.
"""
import logging
from datetime import datetime, timezone, date
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from models.day_close import DayClose
from models.day_start import DayStart
from models.sucursal import Sucursal
from schemas.day_close import DayCloseCreate
from services.day_start_service import DayStartService
from services.report_service import ReportService
from utils.datetime_helpers import get_business_date_in_timezone

logger = logging.getLogger(__name__)


class DayCloseService:
    """Service for handling day close operations."""
    
    @staticmethod
    async def close_day(
        db: AsyncSession,
        close_data: DayCloseCreate,
        user_id: str,
        user_role: Optional[str] = None
    ) -> DayClose:
        """
        Close the active day for a sucursal.
        
        Validates that a day is currently active for the sucursal.
        Creates a DayClose record and marks the active DayStart as inactive.
        
        For KidiBar users, only product and product package sales are included in the arqueo.
        For other roles (recepcion, etc.), all sales are included.
        
        Args:
            db: Database session
            close_data: Day close creation data
            user_id: ID of the user closing the day
            user_role: Optional role of the user (e.g., "kidibar", "recepcion")
            
        Returns:
            Created DayClose object
            
        Raises:
            ValueError: If no day is active for the sucursal
        """
        try:
            # Check if there's an active day for this sucursal
            active_day = await DayStartService.get_active_day(
                db=db,
                sucursal_id=str(close_data.sucursal_id)
            )
            
            if not active_day:
                raise ValueError(
                    f"No hay un día activo para cerrar para la sucursal {close_data.sucursal_id}. "
                    f"Debe iniciar un día antes de poder cerrarlo."
                )
            
            # Get sucursal timezone
            sucursal_result = await db.execute(
                select(Sucursal).where(Sucursal.id == close_data.sucursal_id)
            )
            sucursal = sucursal_result.scalar_one_or_none()
            if not sucursal:
                raise ValueError(f"Sucursal {close_data.sucursal_id} not found")
            
            timezone_str = sucursal.timezone or "America/Mexico_City"
            
            # Calculate business date from active_day.started_at using sucursal timezone
            # This ensures the date is always correct regardless of when/where the close happens
            business_date = get_business_date_in_timezone(active_day.started_at, timezone_str)
            
            # Validate that provided date matches calculated business date (if provided)
            # If dates don't match, log a warning but use the calculated date (backend authority)
            if close_data.date != business_date:
                logger.warning(
                    f"Date mismatch for day close: provided={close_data.date}, "
                    f"calculated={business_date} (using calculated date). "
                    f"Sucursal: {close_data.sucursal_id}, Timezone: {timezone_str}"
                )
            
            # Calculate day totals automatically from sales
            # Use timezone-aware datetimes for accurate date range calculation
            from zoneinfo import ZoneInfo
            from datetime import time as dt_time
            
            # Get start of business day in sucursal timezone
            start_date_local = get_business_date_in_timezone(active_day.started_at, timezone_str)
            start_datetime_local = datetime.combine(start_date_local, dt_time.min)
            tz = ZoneInfo(timezone_str)
            start_datetime_utc = start_datetime_local.replace(tzinfo=tz).astimezone(timezone.utc)
            
            # Get end of business day (current time) in UTC
            # Use current time as end_datetime to include all sales up to the moment of closing
            end_datetime_utc = datetime.now(timezone.utc)
            
            # Get day totals using ReportService
            # For KidiBar, use filtered method that only includes products and product packages
            # For other roles, use general method that includes all sales
            report_service = ReportService()
            if user_role == "kidibar":
                day_totals = await report_service.get_day_totals_for_arqueo_kidibar(
                    db=db,
                    sucursal_id=str(close_data.sucursal_id),
                    start_datetime=start_datetime_utc,
                    end_datetime=end_datetime_utc
                )
            else:
                day_totals = await report_service.get_day_totals_for_arqueo(
                    db=db,
                    sucursal_id=str(close_data.sucursal_id),
                    start_datetime=start_datetime_utc,
                    end_datetime=end_datetime_utc
                )
            
            # Calculate system_total_cents automatically
            # system_total = initial_cash + cash_received_during_day
            initial_cash_cents = active_day.initial_cash_cents
            cash_received_total_cents = day_totals["cash_received_total_cents"]
            calculated_system_total_cents = initial_cash_cents + cash_received_total_cents
            
            # Use provided system_total_cents if available, otherwise use calculated
            # If provided, validate it matches calculated (with tolerance for rounding)
            system_total_cents = close_data.system_total_cents
            if system_total_cents is None or system_total_cents == 0:
                system_total_cents = calculated_system_total_cents
                logger.info(
                    f"Using calculated system_total_cents: {system_total_cents} "
                    f"(initial: {initial_cash_cents} + cash_received: {cash_received_total_cents})"
                )
            else:
                # Validate provided value matches calculated (allow 1 cent difference for rounding)
                difference = abs(system_total_cents - calculated_system_total_cents)
                if difference > 1:
                    logger.warning(
                        f"System total mismatch: provided={system_total_cents}, "
                        f"calculated={calculated_system_total_cents} (difference: {difference}). "
                        f"Using provided value. Sucursal: {close_data.sucursal_id}"
                    )
                else:
                    logger.info(
                        f"Provided system_total_cents matches calculated value: {system_total_cents}"
                    )
            
            # Calculate difference
            difference_cents = close_data.physical_count_cents - system_total_cents
            
            # Build totals JSON with complete breakdown
            # Include started_at for easy access in frontend (hybrid pattern)
            totals: Dict[str, Any] = {
                "total_revenue_cents": day_totals["total_revenue_cents"],
                "total_sales_count": day_totals["total_sales_count"],
                "revenue_by_payment_method": day_totals["revenue_by_payment_method"],
                "revenue_by_type": day_totals["revenue_by_type"],
                "cash_received_total_cents": cash_received_total_cents,
                "initial_cash_cents": initial_cash_cents,
                "calculated_system_total_cents": calculated_system_total_cents,
                "started_at": active_day.started_at.isoformat(),  # Store started_at for easy access
                "period": {
                    "start_datetime": start_datetime_utc.isoformat(),
                    "end_datetime": end_datetime_utc.isoformat(),
                    "timezone": timezone_str
                }
            }
            
            # Merge with provided totals if any (allows additional custom data)
            if close_data.totals:
                totals.update(close_data.totals)
            
            # Create new DayClose record
            import uuid
            if isinstance(user_id, str):
                user_uuid = uuid.UUID(user_id)
            else:
                user_uuid = user_id
            
            day_close = DayClose(
                sucursal_id=close_data.sucursal_id,
                usuario_id=user_uuid,
                date=business_date,  # Use calculated date (backend authority)
                system_total_cents=system_total_cents,  # Use calculated or validated provided value
                physical_count_cents=close_data.physical_count_cents,
                difference_cents=difference_cents,
                totals=totals,  # Use calculated totals with complete breakdown
                notes=close_data.notes,  # Optional notes/observations
            )
            db.add(day_close)
            await db.flush()  # Flush to get day_close.id
            
            # Mark the active day as closed
            active_day.is_active = False
            active_day.updated_at = datetime.now(timezone.utc)
            await db.flush()  # Flush to ensure active_day changes are saved
            
            await db.commit()
            
            await db.refresh(day_close)
            await db.refresh(active_day)
            
            logger.info(
                f"Day closed for sucursal {close_data.sucursal_id} "
                f"by user {user_id}. System total: {system_total_cents} cents "
                f"(initial: {initial_cash_cents} + cash_received: {cash_received_total_cents}), "
                f"Physical count: {close_data.physical_count_cents} cents, "
                f"Difference: {difference_cents} cents, "
                f"Total sales: {day_totals['total_sales_count']}, "
                f"Total revenue: {day_totals['total_revenue_cents']} cents"
            )
            return day_close
                
        except ValueError:
            await db.rollback()
            raise
        except Exception as e:
            logger.error(f"Error closing day: {e}", exc_info=True)
            await db.rollback()
            raise
    
    @staticmethod
    async def list_day_closes(
        db: AsyncSession,
        sucursal_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[DayClose]:
        """
        List day closes with optional filtering and pagination.
        
        Uses hybrid pattern: includes started_at from totals JSON if available,
        otherwise attempts to find corresponding DayStart via query.
        
        Args:
            db: Database session
            sucursal_id: Optional sucursal ID to filter by (UUID string)
            start_date: Optional start date to filter by (inclusive)
            end_date: Optional end date to filter by (inclusive)
            skip: Number of records to skip (pagination)
            limit: Maximum number of records to return
            
        Returns:
            List of DayClose objects ordered by date descending (newest first)
            Note: started_at is available in totals JSON for new records,
            or can be retrieved via DayStart query for historical records.
        """
        from uuid import UUID
        
        query = select(DayClose)
        
        # Filter by sucursal_id if provided
        if sucursal_id:
            try:
                sucursal_uuid = UUID(sucursal_id)
                query = query.where(DayClose.sucursal_id == sucursal_uuid)
            except ValueError:
                logger.warning(f"Invalid sucursal_id format: {sucursal_id}")
                return []
        
        # Filter by date range if provided
        if start_date:
            query = query.where(DayClose.date >= start_date)
        
        if end_date:
            query = query.where(DayClose.date <= end_date)
        
        # Order by date descending (newest first), then by created_at descending
        query = query.order_by(DayClose.date.desc(), DayClose.created_at.desc())
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        result = await db.execute(query)
        day_closes = result.scalars().all()
        
        # Hybrid pattern: For day closes without started_at in totals,
        # try to find corresponding DayStart and add it to totals
        # This handles historical records created before we started storing started_at
        if day_closes and sucursal_id:
            try:
                sucursal_uuid = UUID(sucursal_id)
                # Get sucursal timezone for date calculations
                sucursal_result = await db.execute(
                    select(Sucursal).where(Sucursal.id == sucursal_uuid)
                )
                sucursal = sucursal_result.scalar_one_or_none()
                timezone_str = sucursal.timezone if sucursal else "America/Mexico_City"
                
                # For each day_close without started_at in totals, try to find DayStart
                for day_close in day_closes:
                    if not day_close.totals or "started_at" not in day_close.totals:
                        # Try to find corresponding DayStart
                        # Match by: same sucursal, is_active=False, and business date matches
                        day_starts_query = select(DayStart).where(
                            and_(
                                DayStart.sucursal_id == day_close.sucursal_id,
                                DayStart.is_active == False
                            )
                        ).order_by(DayStart.started_at.desc())
                        
                        day_starts_result = await db.execute(day_starts_query)
                        day_starts = day_starts_result.scalars().all()
                        
                        # Find DayStart whose business date matches day_close.date
                        for day_start in day_starts:
                            business_date = get_business_date_in_timezone(
                                day_start.started_at, timezone_str
                            )
                            if business_date == day_close.date:
                                # Found matching DayStart, add started_at to totals
                                if day_close.totals is None:
                                    day_close.totals = {}
                                day_close.totals["started_at"] = day_start.started_at.isoformat()
                                logger.debug(
                                    f"Found matching DayStart for DayClose {day_close.id}, "
                                    f"added started_at to totals"
                                )
                                break
            except Exception as e:
                logger.warning(
                    f"Error trying to enrich day closes with started_at: {e}. "
                    f"Continuing without enrichment."
                )
        
        logger.debug(
            f"Retrieved {len(day_closes)} day closes (skip={skip}, limit={limit}, "
            f"sucursal_id={sucursal_id}, start_date={start_date}, end_date={end_date})"
        )
        
        return list(day_closes)
    
    @staticmethod
    async def preview_day_close(
        db: AsyncSession,
        sucursal_id: str,
        user_role: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Preview day close calculations without actually closing the day.
        
        This method calculates what the system_total_cents would be if the day
        were closed right now, without creating a DayClose record.
        
        For KidiBar users, only product and product package sales are included in the preview.
        For other roles (recepcion, etc.), all sales are included.
        
        Args:
            db: Database session
            sucursal_id: Sucursal ID (UUID string)
            user_role: Optional role of the user (e.g., "kidibar", "recepcion")
            
        Returns:
            Dictionary with preview data:
            {
                "expected_total_cents": int,  # initial_cash + cash_received
                "initial_cash_cents": int,
                "cash_received_total_cents": int,
                "breakdown": {
                    "total_revenue_cents": int,
                    "total_sales_count": int,
                    "revenue_by_payment_method": dict,
                    "revenue_by_type": dict,
                },
                "business_date": str,  # YYYY-MM-DD
                "timezone": str
            }
            
        Raises:
            ValueError: If no day is active for the sucursal
        """
        # Check if there's an active day for this sucursal
        active_day = await DayStartService.get_active_day(
            db=db,
            sucursal_id=sucursal_id
        )
        
        if not active_day:
            raise ValueError(
                f"No hay un día activo para la sucursal {sucursal_id}. "
                f"Debe iniciar un día antes de poder ver el preview del cierre."
            )
        
        # Get sucursal timezone
        sucursal_result = await db.execute(
            select(Sucursal).where(Sucursal.id == active_day.sucursal_id)
        )
        sucursal = sucursal_result.scalar_one_or_none()
        if not sucursal:
            raise ValueError(f"Sucursal {sucursal_id} not found")
        
        timezone_str = sucursal.timezone or "America/Mexico_City"
        
        # Calculate business date from active_day.started_at using sucursal timezone
        business_date = get_business_date_in_timezone(active_day.started_at, timezone_str)
        
        # Calculate day totals automatically from sales
        from zoneinfo import ZoneInfo
        from datetime import time as dt_time
        
        # Get start of business day in sucursal timezone
        start_date_local = get_business_date_in_timezone(active_day.started_at, timezone_str)
        start_datetime_local = datetime.combine(start_date_local, dt_time.min)
        tz = ZoneInfo(timezone_str)
        start_datetime_utc = start_datetime_local.replace(tzinfo=tz).astimezone(timezone.utc)
        
        # Get end of business day (current time) in UTC
        end_datetime_utc = datetime.now(timezone.utc)
        
        # Get day totals using ReportService
        # For KidiBar, use filtered method that only includes products and product packages
        # For other roles, use general method that includes all sales
        report_service = ReportService()
        if user_role == "kidibar":
            day_totals = await report_service.get_day_totals_for_arqueo_kidibar(
                db=db,
                sucursal_id=sucursal_id,
                start_datetime=start_datetime_utc,
                end_datetime=end_datetime_utc
            )
        else:
            day_totals = await report_service.get_day_totals_for_arqueo(
                db=db,
                sucursal_id=sucursal_id,
                start_datetime=start_datetime_utc,
                end_datetime=end_datetime_utc
            )
        
        # Calculate expected system_total_cents
        initial_cash_cents = active_day.initial_cash_cents
        cash_received_total_cents = day_totals["cash_received_total_cents"]
        expected_total_cents = initial_cash_cents + cash_received_total_cents
        
        return {
            "expected_total_cents": expected_total_cents,
            "initial_cash_cents": initial_cash_cents,
            "cash_received_total_cents": cash_received_total_cents,
            "breakdown": {
                "total_revenue_cents": day_totals["total_revenue_cents"],
                "total_sales_count": day_totals["total_sales_count"],
                "revenue_by_payment_method": day_totals["revenue_by_payment_method"],
                "revenue_by_type": day_totals["revenue_by_type"],
            },
            "business_date": business_date.isoformat(),
            "timezone": timezone_str,
            "period": {
                "start_datetime": start_datetime_utc.isoformat(),
                "end_datetime": end_datetime_utc.isoformat(),
            }
        }
