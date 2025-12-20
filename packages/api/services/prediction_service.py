"""
Prediction Service - Business logic for generating predictions and forecasts.

Currently uses simple algorithms (moving averages, trends).
Designed to be easily extended with AI/ML models in the future.
"""
import logging
import random
import statistics
from datetime import datetime, date, timedelta
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, extract
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import literal_column

from models.sale import Sale
from models.sale_item import SaleItem
from models.timer import Timer
from models.product import Product
from models.service import Service
from models.package import Package
from models.sucursal import Sucursal
from services.report_service import ReportService
from utils.package_helpers import get_service_package_ids, get_product_package_ids
from utils.datetime_helpers import get_business_date_in_timezone
from sqlalchemy import text
from uuid import UUID as UUIDType
from datetime import timezone as dt_timezone

logger = logging.getLogger(__name__)


class PredictionService:
    """Service for generating predictions and forecasts."""
    
    def __init__(self):
        # Cache for sucursal timezones to avoid repeated DB queries
        self._timezone_cache: Dict[str, str] = {}
        # Initialize ReportService for accessing report methods
        self.report_service = ReportService()
    
    async def _get_sucursal_timezone(
        self,
        db: AsyncSession,
        sucursal_id: Optional[str]
    ) -> str:
        """
        Get timezone for a sucursal with caching.
        
        Args:
            db: Database session
            sucursal_id: Optional sucursal ID
            
        Returns:
            IANA timezone string (e.g., "America/Mexico_City")
        """
        if not sucursal_id:
            return "America/Mexico_City"  # Default timezone
        
        # Check cache first
        if sucursal_id in self._timezone_cache:
            return self._timezone_cache[sucursal_id]
        
        try:
            sucursal_uuid = UUIDType(sucursal_id)
            result = await db.execute(
                select(Sucursal).where(Sucursal.id == sucursal_uuid)
            )
            sucursal = result.scalar_one_or_none()
            
            if sucursal and sucursal.timezone:
                timezone_str = sucursal.timezone
            else:
                timezone_str = "America/Mexico_City"  # Default
            
            # Cache the result
            self._timezone_cache[sucursal_id] = timezone_str
            return timezone_str
        except (ValueError, TypeError):
            logger.warning(f"Invalid sucursal_id format: {sucursal_id}, using default timezone")
            return "America/Mexico_City"
    
    def _extract_hour_in_timezone(
        self,
        column,
        timezone_str: str
    ):
        """
        Extract hour from a datetime column in a specific timezone.
        
        Uses PostgreSQL AT TIME ZONE for efficient timezone conversion.
        
        For TIMESTAMP WITH TIME ZONE columns (which our columns are), the correct syntax is:
        column AT TIME ZONE 'timezone' - this converts the timestamp to the specified timezone.
        
        Args:
            column: SQLAlchemy column (e.g., Sale.created_at)
            timezone_str: IANA timezone string (validated)
            
        Returns:
            SQLAlchemy expression for extracting hour in timezone
        """
        # Validate timezone string to prevent SQL injection
        import re
        if not re.match(r'^[A-Za-z0-9_/]+$', timezone_str):
            raise ValueError(f"Invalid timezone string: {timezone_str}")
        
        # PostgreSQL: For TIMESTAMP WITH TIME ZONE, use: column AT TIME ZONE 'timezone'
        # This converts the timestamp (stored in UTC) to the specified timezone
        # Use the column object directly with op() to create the AT TIME ZONE expression
        # This ensures SQLAlchemy can properly resolve the column reference in the query context
        column_name = column.name if hasattr(column, 'name') else str(column)
        
        logger.debug(f"Extracting hour in timezone: column={column_name}, timezone={timezone_str}")
        
        # Build the AT TIME ZONE expression using the column's op() method
        # This creates: column AT TIME ZONE 'timezone'
        timezone_expr = column.op('AT TIME ZONE')(literal_column(f"'{timezone_str}'"))
        
        return func.extract('hour', timezone_expr)
    
    def _extract_dow_in_timezone(
        self,
        column,
        timezone_str: str
    ):
        """
        Extract day of week (0=Sunday, 6=Saturday) from a datetime column in a specific timezone.
        
        For TIMESTAMP WITH TIME ZONE columns, use: column AT TIME ZONE 'timezone'
        
        Args:
            column: SQLAlchemy column (e.g., Sale.created_at)
            timezone_str: IANA timezone string (validated)
            
        Returns:
            SQLAlchemy expression for extracting day of week in timezone
        """
        # Validate timezone string
        import re
        if not re.match(r'^[A-Za-z0-9_/]+$', timezone_str):
            raise ValueError(f"Invalid timezone string: {timezone_str}")
        
        # Use the column object directly with op() to create the AT TIME ZONE expression
        column_name = column.name if hasattr(column, 'name') else str(column)
        
        logger.debug(f"Extracting day of week in timezone: column={column_name}, timezone={timezone_str}")
        
        # Build the AT TIME ZONE expression using the column's op() method
        timezone_expr = column.op('AT TIME ZONE')(literal_column(f"'{timezone_str}'"))
        
        return extract('dow', timezone_expr)
    
    def _extract_date_in_timezone(
        self,
        column,
        timezone_str: str
    ):
        """
        Extract date from a datetime column in a specific timezone.
        
        For TIMESTAMP WITH TIME ZONE columns, use: column AT TIME ZONE 'timezone'
        
        Args:
            column: SQLAlchemy column (e.g., Sale.created_at)
            timezone_str: IANA timezone string (validated)
            
        Returns:
            SQLAlchemy expression for extracting date in timezone
        """
        # Validate timezone string
        import re
        if not re.match(r'^[A-Za-z0-9_/]+$', timezone_str):
            raise ValueError(f"Invalid timezone string: {timezone_str}")
        
        # Use the column object directly with op() to create the AT TIME ZONE expression
        column_name = column.name if hasattr(column, 'name') else str(column)
        
        logger.debug(f"Extracting date in timezone: column={column_name}, timezone={timezone_str}")
        
        # Build the AT TIME ZONE expression using the column's op() method
        timezone_expr = column.op('AT TIME ZONE')(literal_column(f"'{timezone_str}'"))
        
        return func.date(timezone_expr)
    
    async def _get_business_date(
        self,
        db: AsyncSession,
        sucursal_id: Optional[str],
        target_date: Optional[date] = None
    ) -> date:
        """
        Get business date for a sucursal considering its timezone.
        
        Args:
            db: Database session
            sucursal_id: Optional sucursal ID
            target_date: Optional target date (defaults to today in sucursal timezone)
            
        Returns:
            Date object in sucursal timezone
        """
        if target_date:
            return target_date
        
        timezone_str = await self._get_sucursal_timezone(db, sucursal_id)
        now_utc = datetime.now(dt_timezone.utc)
        return get_business_date_in_timezone(now_utc, timezone_str)
    
    # ============================================================================
    # Helper Functions for Predictions (Reusable, Modular)
    # ============================================================================
    
    @staticmethod
    def _get_day_of_week_factor(forecast_date: date, weekly_pattern: Optional[Dict[int, float]] = None) -> float:
        """
        Get day-of-week adjustment factor for predictions.
        
        Args:
            forecast_date: Date to get factor for
            weekly_pattern: Optional dict with day-of-week factors {0: sunday_factor, ..., 6: saturday_factor}
                           If None, uses default factors based on typical retail patterns
        
        Returns:
            Float factor to multiply base prediction (1.0 = no adjustment)
        """
        day_of_week = forecast_date.weekday()  # 0=Monday, 6=Sunday
        
        if weekly_pattern:
            # Use calculated pattern from historical data
            # Convert to isoweekday format (1=Monday, 7=Sunday) for consistency
            isoweekday = forecast_date.isoweekday()  # 1=Monday, 7=Sunday
            # Map to 0-6 format (0=Monday, 6=Sunday) for pattern dict
            pattern_key = (isoweekday - 1) % 7  # Convert 1-7 to 0-6
            return weekly_pattern.get(pattern_key, 1.0)
        
        # Default factors based on typical retail patterns
        # These can be overridden with calculated patterns from historical data
        default_factors = {
            0: 1.0,   # Monday - base
            1: 1.0,   # Tuesday - base
            2: 1.0,   # Wednesday - base
            3: 1.0,   # Thursday - base
            4: 1.15,  # Friday - slightly higher
            5: 1.25,  # Saturday - highest
            6: 1.20   # Sunday - high
        }
        
        return default_factors.get(day_of_week, 1.0)
    
    @staticmethod
    def _calculate_weekly_pattern(historical_data: List) -> Optional[Dict[int, float]]:
        """
        Calculate day-of-week factors from historical data.
        
        Args:
            historical_data: List of rows with 'daily_revenue' and 'day_of_week' attributes
        
        Returns:
            Dict with day-of-week factors {0: factor, ..., 6: factor} or None if insufficient data
        """
        if not historical_data or len(historical_data) < 14:
            # Need at least 2 weeks of data to calculate reliable patterns
            return None
        
        # Group by day of week
        day_revenues: Dict[int, List[float]] = {}
        for row in historical_data:
            dow = int(row.day_of_week) if hasattr(row, 'day_of_week') else None
            revenue = float(row.daily_revenue or 0) if hasattr(row, 'daily_revenue') else 0
            
            if dow is not None:
                if dow not in day_revenues:
                    day_revenues[dow] = []
                day_revenues[dow].append(revenue)
        
        if len(day_revenues) < 5:
            # Need data for at least 5 different days of week
            return None
        
        # Calculate average revenue per day of week
        day_averages: Dict[int, float] = {}
        for dow, revenues in day_revenues.items():
            if revenues:
                day_averages[dow] = sum(revenues) / len(revenues)
        
        if not day_averages:
            return None
        
        # Calculate overall average
        overall_avg = sum(day_averages.values()) / len(day_averages)
        
        if overall_avg == 0:
            return None
        
        # Calculate factors (relative to overall average)
        weekly_pattern: Dict[int, float] = {}
        for dow in range(7):  # 0-6 (Monday-Sunday)
            avg_for_day = day_averages.get(dow, overall_avg)
            weekly_pattern[dow] = avg_for_day / overall_avg if overall_avg > 0 else 1.0
        
        return weekly_pattern
    
    @staticmethod
    def _apply_natural_variation(base_value: float, coefficient_of_variation: float = 0.1) -> float:
        """
        Apply natural variation to prediction to simulate real-world variability.
        
        Uses normal distribution with mean=base_value and std=base_value * CV.
        This creates realistic variation without being too extreme.
        
        Args:
            base_value: Base prediction value
            coefficient_of_variation: CV (std/mean) - default 0.1 (10% variation)
        
        Returns:
            Adjusted value with natural variation
        """
        import random
        
        if base_value <= 0:
            return base_value
        
        # Calculate standard deviation
        std_dev = base_value * coefficient_of_variation
        
        # Generate random variation using normal distribution
        # random is imported at module level
        variation = random.gauss(0, std_dev)
        
        # Apply variation (ensure non-negative)
        adjusted_value = base_value + variation
        
        # Ensure result is non-negative (realistic constraint)
        return max(0, adjusted_value)
    
    @staticmethod
    def _calculate_coefficient_of_variation(values: List[float]) -> float:
        """
        Calculate coefficient of variation (CV) from historical values.
        
        CV = std_dev / mean
        Used to determine natural variation for predictions.
        
        Args:
            values: List of historical values
        
        Returns:
            Coefficient of variation (0.0 if insufficient data or zero mean)
        """
        if not values or len(values) < 3:
            return 0.1  # Default 10% variation
        
        # statistics is imported at module level
        try:
            mean = statistics.mean(values)
            if mean == 0:
                return 0.1  # Default if mean is zero
            
            std_dev = statistics.stdev(values) if len(values) > 1 else 0
            cv = std_dev / mean
            
            # Cap CV at reasonable limits (0.05 to 0.3)
            return max(0.05, min(0.3, cv))
        except (statistics.StatisticsError, ZeroDivisionError):
            return 0.1  # Default fallback
    
    @staticmethod
    def _calculate_trend_factor(historical_data: List, recent_days: int = 7) -> float:
        """
        Calculate trend factor from historical data.
        
        Compares recent period vs previous period to detect trends.
        
        Args:
            historical_data: List of rows with revenue/count data
            recent_days: Number of recent days to compare (default: 7)
        
        Returns:
            Trend factor (1.0 = no trend, >1.0 = increasing, <1.0 = decreasing)
        """
        if not historical_data or len(historical_data) < recent_days * 2:
            return 1.0  # No trend if insufficient data
        
        # Get revenue values (handle different data structures)
        revenues = []
        for row in historical_data:
            if hasattr(row, 'daily_revenue'):
                revenue = float(row.daily_revenue or 0)
            elif hasattr(row, 'daily_revenue_cents'):
                revenue = float(row.daily_revenue_cents or 0)
            else:
                continue
            revenues.append(revenue)
        
        if len(revenues) < recent_days * 2:
            return 1.0
        
        # Calculate recent average (last N days)
        recent_revenue = sum(revenues[-recent_days:]) / recent_days
        
        # Calculate previous average (N days before recent)
        previous_revenue = sum(revenues[-recent_days*2:-recent_days]) / recent_days
        
        # Calculate trend factor
        if previous_revenue > 0:
            trend_factor = recent_revenue / previous_revenue
            # Cap extreme trends (0.5 to 2.0)
            return max(0.5, min(2.0, trend_factor))
        
        return 1.0
    
    async def predict_sales(
        self,
        db: AsyncSession,
        sucursal_id: Optional[str] = None,
        forecast_days: int = 7
    ) -> Dict[str, Any]:
        """
        Predict future sales based on historical data.
        
        Uses simple moving average and trend analysis.
        Now considers: Peak Hours, Top Products, Top Services, Top Customers.
        
        Args:
            db: Database session
            sucursal_id: Optional sucursal ID to filter by
            forecast_days: Number of days to forecast (default: 7)
            
        Returns:
            Dictionary with sales predictions:
            {
                "forecast": [
                    {"date": "YYYY-MM-DD", "predicted_revenue_cents": int, "predicted_count": int},
                    ...
                ],
                "confidence": "high" | "medium" | "low",
                "method": "moving_average",
                "historical_avg_revenue": int,
                "historical_avg_count": int
            }
        """
        # Get sucursal timezone for date extraction
        timezone_str = await self._get_sucursal_timezone(db, sucursal_id)
        
        # Get historical data (last 30 days)
        # Use business date (today in sucursal timezone) instead of server date
        end_date = await self._get_business_date(db, sucursal_id)
        start_date = end_date - timedelta(days=30)
        
        # Extract date in sucursal timezone
        date_expr = self._extract_date_in_timezone(Sale.created_at, timezone_str)
        
        # Build query for historical sales
        query = select(
            date_expr.label("sale_date"),
            func.sum(Sale.total_cents).label("daily_revenue"),
            func.count(Sale.id).label("daily_count")
        ).where(
            and_(
                Sale.created_at >= datetime.combine(start_date, datetime.min.time()),
                Sale.created_at <= datetime.combine(end_date, datetime.max.time())
            )
        )
        
        if sucursal_id:
            query = query.where(Sale.sucursal_id == sucursal_id)
        
        query = query.group_by(date_expr)
        query = query.order_by(date_expr)
        
        result = await db.execute(query)
        historical_data = result.all()
        
        if not historical_data or len(historical_data) < 3:
            # Not enough data for prediction
            return {
                "forecast": [],
                "confidence": "low",
                "method": "insufficient_data",
                "message": "Not enough historical data for prediction (need at least 3 days)"
            }
        
        # Get additional metrics to improve predictions
        peak_hours_report = await self.report_service.get_peak_hours_report(
            db=db,
            sucursal_id=sucursal_id,
            target_date=end_date,
            use_cache=True
        )
        
        top_products_report = await self.report_service.get_top_products_report(
            db=db,
            sucursal_id=sucursal_id,
            days=7,
            use_cache=True
        )
        
        top_customers_report = await self.report_service.get_top_customers_report(
            db=db,
            sucursal_id=sucursal_id,
            days=7,
            use_cache=True
        )
        
        # Calculate averages
        total_revenue = sum(row.daily_revenue or 0 for row in historical_data)
        total_count = sum(row.daily_count or 0 for row in historical_data)
        days_count = len(historical_data)
        
        avg_revenue = int(total_revenue / days_count) if days_count > 0 else 0
        avg_count = int(total_count / days_count) if days_count > 0 else 0
        
        # Calculate trend factor using helper function
        trend_factor = self._calculate_trend_factor(historical_data, recent_days=7)
        
        # Apply adjustments based on metrics
        # 1. Peak hours adjustment: higher activity during peak hours
        peak_hours_factor = 1.0
        if peak_hours_report and peak_hours_report.get("busiest_hour"):
            busiest_hour = peak_hours_report["busiest_hour"].get("hour", 14)  # Default 2 PM
            # Adjust based on time of day (simplified: assume peak hours increase sales by 15%)
            peak_hours_factor = 1.15
        
        # 2. Top customers adjustment: frequent customers increase repeat business
        customer_loyalty_factor = 1.0
        if top_customers_report and top_customers_report.get("top_customers"):
            top_customers = top_customers_report["top_customers"]
            if len(top_customers) > 0:
                # If we have frequent customers, increase confidence and adjust prediction
                avg_visits = sum(c.get("visit_count", 0) for c in top_customers) / len(top_customers)
                if avg_visits >= 3:  # Frequent customers (3+ visits)
                    customer_loyalty_factor = 1.10  # 10% increase due to loyalty
        
        # 3. Top products adjustment: popular products drive sales
        product_demand_factor = 1.0
        if top_products_report and top_products_report.get("top_products"):
            top_products = top_products_report["top_products"]
            if len(top_products) > 0:
                # If we have strong product sales, maintain or increase prediction
                total_products_sold = sum(p.get("quantity_sold", 0) for p in top_products)
                if total_products_sold > 50:  # Strong product demand
                    product_demand_factor = 1.05  # 5% increase
        
        # Combine all factors
        combined_factor = peak_hours_factor * customer_loyalty_factor * product_demand_factor
        
        # Calculate weekly pattern from historical data if available
        weekly_pattern = self._calculate_weekly_pattern(historical_data)
        
        # Calculate coefficient of variation for natural variation
        historical_revenues = [float(row.daily_revenue or 0) for row in historical_data]
        cv = self._calculate_coefficient_of_variation(historical_revenues)
        
        # Generate forecast
        forecast = []
        for i in range(1, forecast_days + 1):
            forecast_date = end_date + timedelta(days=i)
            
            # Get day-of-week factor
            day_factor = self._get_day_of_week_factor(forecast_date, weekly_pattern)
            
            # Apply trend factor with decay (trend weakens over time)
            # Only apply decay if there's an actual trend (not 1.0)
            if abs(trend_factor - 1.0) > 0.05:  # Significant trend
                decay_factor = 1.0 - (i * 0.05)  # 5% decay per day
                adjusted_trend = 1.0 + ((trend_factor - 1.0) * decay_factor)
            else:
                adjusted_trend = 1.0  # No trend, no decay
            
            # Apply combined factors
            base_factor = adjusted_trend * combined_factor * day_factor
            
            # Calculate base prediction
            base_revenue = avg_revenue * base_factor
            base_count = avg_count * base_factor
            
            # Apply natural variation for realism
            predicted_revenue = int(self._apply_natural_variation(base_revenue, cv))
            predicted_count = int(self._apply_natural_variation(base_count, cv * 0.8))  # Slightly less variation for count
            
            forecast.append({
                "date": forecast_date.isoformat(),
                "predicted_revenue_cents": max(0, predicted_revenue),
                "predicted_count": max(0, predicted_count)
            })
        
        # Determine confidence (improved with metrics)
        base_confidence = "low"
        if days_count >= 14 and abs(trend_factor - 1.0) < 0.2:
            base_confidence = "high"
        elif days_count >= 7:
            base_confidence = "medium"
        
        # Increase confidence if we have good metrics data
        if top_customers_report and top_products_report and peak_hours_report:
            if base_confidence == "medium":
                confidence = "high"
            elif base_confidence == "low":
                confidence = "medium"
            else:
                confidence = base_confidence
        else:
            confidence = base_confidence
        
        return {
            "forecast": forecast,
            "confidence": confidence,
            "method": "moving_average_with_trend_and_metrics",
            "historical_avg_revenue_cents": avg_revenue,
            "historical_avg_count": avg_count,
            "trend_factor": round(trend_factor, 2),
            "historical_days": days_count,
            "metrics_used": {
                "peak_hours": peak_hours_report is not None,
                "top_products": top_products_report is not None,
                "top_customers": top_customers_report is not None,
                "adjustment_factors": {
                    "peak_hours": round(peak_hours_factor, 2),
                    "customer_loyalty": round(customer_loyalty_factor, 2),
                    "product_demand": round(product_demand_factor, 2),
                    "combined": round(combined_factor, 2)
                }
            }
        }
    
    async def predict_capacity(
        self,
        db: AsyncSession,
        sucursal_id: Optional[str] = None,
        forecast_days: int = 7
    ) -> Dict[str, Any]:
        """
        Predict capacity usage based on timer history.
        
        Args:
            db: Database session
            sucursal_id: Optional sucursal ID to filter by
            forecast_days: Number of days to forecast
            
        Returns:
            Dictionary with capacity predictions:
            {
                "forecast": [
                    {"date": "YYYY-MM-DD", "predicted_active_timers": int, "utilization_rate": float},
                    ...
                ],
                "confidence": "high" | "medium" | "low",
                "method": "timer_history_analysis"
            }
        """
        # Get sucursal timezone for date/day-of-week extraction
        timezone_str = await self._get_sucursal_timezone(db, sucursal_id)
        
        # Get historical timer data (last 30 days)
        # Use business date (today in sucursal timezone) instead of server date
        end_date = await self._get_business_date(db, sucursal_id)
        start_date = end_date - timedelta(days=30)
        
        # Extract date and day of week in sucursal timezone
        timer_date_expr = self._extract_date_in_timezone(Timer.start_at, timezone_str)
        timer_dow_expr = self._extract_dow_in_timezone(Timer.start_at, timezone_str)
        
        # Query for active timers per day with day of week
        query = select(
            timer_date_expr.label("timer_date"),
            func.count(Timer.id).label("daily_timers"),
            timer_dow_expr.label("day_of_week")  # 0=Sunday, 6=Saturday
        ).where(
            and_(
                Timer.start_at >= datetime.combine(start_date, datetime.min.time()),
                Timer.start_at <= datetime.combine(end_date, datetime.max.time())
            )
        )
        
        if sucursal_id:
            # Join with Sale to filter by sucursal
            # Use explicit join condition: Timer.sale_id == Sale.id
            # Convert sucursal_id to UUID for comparison with Sale.sucursal_id
            try:
                sucursal_uuid = UUIDType(sucursal_id)
                query = query.join(Sale, Timer.sale_id == Sale.id).where(
                    Sale.sucursal_id == sucursal_uuid
                )
            except (ValueError, TypeError):
                logger.warning(f"Invalid sucursal_id format: {sucursal_id}")
                # If invalid, don't filter by sucursal (return all timers)
        
        query = query.group_by(timer_date_expr, timer_dow_expr)
        query = query.order_by(timer_date_expr)
        
        result = await db.execute(query)
        historical_data = result.all()
        
        if not historical_data or len(historical_data) < 3:
            return {
                "forecast": [],
                "confidence": "low",
                "method": "insufficient_data",
                "message": "Not enough historical timer data for prediction"
            }
        
        # Calculate average active timers
        total_timers = sum(row.daily_timers or 0 for row in historical_data)
        days_count = len(historical_data)
        avg_timers = int(total_timers / days_count) if days_count > 0 else 0
        
        # Calculate weekly pattern from historical data if available
        weekly_pattern = self._calculate_weekly_pattern(historical_data)
        
        # Calculate coefficient of variation for natural variation
        historical_timers = [float(row.daily_timers or 0) for row in historical_data]
        cv = self._calculate_coefficient_of_variation(historical_timers)
        
        # Get total services capacity
        service_query = select(Service).where(Service.active == True)
        if sucursal_id:
            try:
                sucursal_uuid = UUIDType(sucursal_id)
                service_query = service_query.where(Service.sucursal_id == sucursal_uuid)
            except (ValueError, TypeError):
                logger.warning(f"Invalid sucursal_id format for Service query: {sucursal_id}")
                # If invalid, don't filter by sucursal (return all services)
        
        service_result = await db.execute(service_query)
        services = service_result.scalars().all()
        total_capacity = len(services)  # Simplified: one timer per service capacity
        
        # Generate forecast with day-of-week and natural variation
        forecast = []
        for i in range(1, forecast_days + 1):
            forecast_date = end_date + timedelta(days=i)
            
            # Get day-of-week factor
            day_factor = self._get_day_of_week_factor(forecast_date, weekly_pattern)
            
            # Calculate base prediction with day factor
            base_timers = avg_timers * day_factor
            
            # Apply natural variation for realism
            predicted_timers = int(self._apply_natural_variation(base_timers, cv))
            
            utilization_rate = (predicted_timers / total_capacity) if total_capacity > 0 else 0
            
            forecast.append({
                "date": forecast_date.isoformat(),
                "predicted_active_timers": max(0, predicted_timers),
                "utilization_rate": round(min(1.0, utilization_rate), 2)
            })
        
        confidence = "high" if days_count >= 14 else "medium" if days_count >= 7 else "low"
        
        return {
            "forecast": forecast,
            "confidence": confidence,
            "method": "timer_history_analysis",
            "historical_avg_timers": avg_timers,
            "total_capacity": total_capacity,
            "historical_days": days_count
        }
    
    async def predict_stock_needs(
        self,
        db: AsyncSession,
        sucursal_id: Optional[str] = None,
        forecast_days: int = 7
    ) -> Dict[str, Any]:
        """
        Predict stock reorder needs based on sales history.
        
        Args:
            db: Database session
            sucursal_id: Optional sucursal ID to filter by
            forecast_days: Number of days to forecast
            
        Returns:
            Dictionary with stock predictions:
            {
                "reorder_suggestions": [
                    {
                        "product_id": str,
                        "product_name": str,
                        "current_stock": int,
                        "predicted_daily_usage": float,
                        "days_until_out_of_stock": int,
                        "recommended_reorder_qty": int
                    },
                    ...
                ],
                "confidence": "high" | "medium" | "low"
            }
        """
        # Get products
        product_query = select(Product).where(Product.active == True)
        if sucursal_id:
            product_query = product_query.where(Product.sucursal_id == sucursal_id)
        
        product_result = await db.execute(product_query)
        products = product_result.scalars().all()
        
        if not products:
            return {
                "reorder_suggestions": [],
                "confidence": "low",
                "message": "No products found"
            }
        
        # Get sucursal timezone for date extraction
        timezone_str = await self._get_sucursal_timezone(db, sucursal_id)
        
        # Get sales history for products (last 30 days)
        # Use business date (today in sucursal timezone) instead of server date
        end_date = await self._get_business_date(db, sucursal_id)
        start_date = end_date - timedelta(days=30)
        
        # Extract date in sucursal timezone
        sale_date_expr = self._extract_date_in_timezone(Sale.created_at, timezone_str)
        
        # Validate we have enough historical data before processing
        # Check if there are any product sales in the date range
        validation_query = select(
            func.count(func.distinct(sale_date_expr)).label("days_with_sales")
        ).join(
            SaleItem, SaleItem.sale_id == Sale.id
        ).where(
            and_(
                SaleItem.type == 'product',
                Sale.created_at >= datetime.combine(start_date, datetime.min.time()),
                Sale.created_at <= datetime.combine(end_date, datetime.max.time())
            )
        )
        
        if sucursal_id:
            validation_query = validation_query.where(Sale.sucursal_id == sucursal_id)
        
        validation_result = await db.execute(validation_query)
        days_with_sales = validation_result.scalar() or 0
        
        # Validate minimum data requirement (at least 3 days)
        if days_with_sales < 3:
            return {
                "reorder_suggestions": [],
                "confidence": "low",
                "method": "insufficient_data",
                "message": f"Not enough historical sales data for stock predictions (need at least 3 days, found {days_with_sales})",
                "forecast_days": forecast_days
            }
        
        reorder_suggestions = []
        
        for product in products:
            # Query sales of this product using type and ref_id pattern
            # Following the pattern from report_service.py (line 1140)
            sales_query = select(
                func.sum(SaleItem.quantity).label("total_sold")
            ).join(
                Sale, SaleItem.sale_id == Sale.id
            ).where(
                and_(
                    SaleItem.type == 'product',
                    SaleItem.ref_id == product.id,
                    Sale.created_at >= datetime.combine(start_date, datetime.min.time()),
                    Sale.created_at <= datetime.combine(end_date, datetime.max.time())
                )
            )
            
            if sucursal_id:
                sales_query = sales_query.where(Sale.sucursal_id == sucursal_id)
            
            sales_result = await db.execute(sales_query)
            total_sold = sales_result.scalar() or 0
            
            # Calculate daily usage
            days_count = 30
            daily_usage = total_sold / days_count if days_count > 0 else 0
            
            # Predict days until out of stock
            if daily_usage > 0:
                days_until_out = int(product.stock_qty / daily_usage)
            else:
                days_until_out = 999  # No usage, won't run out
            
            # Recommend reorder if stock will run out within forecast period
            if days_until_out <= forecast_days:
                # Recommend enough stock for forecast_days + buffer
                recommended_reorder = int(daily_usage * (forecast_days + 7))  # 7 day buffer
                
                reorder_suggestions.append({
                    "product_id": str(product.id),
                    "product_name": product.name,
                    "current_stock": product.stock_qty,
                    "predicted_daily_usage": round(daily_usage, 2),
                    "days_until_out_of_stock": days_until_out,
                    "recommended_reorder_qty": recommended_reorder,
                    "threshold_alert_qty": product.threshold_alert_qty
                })
        
        # Sort by days until out of stock (most urgent first)
        reorder_suggestions.sort(key=lambda x: x["days_until_out_of_stock"])
        
        # Determine confidence based on data quality and quantity
        # Similar to predict_sales pattern (line 324)
        if days_with_sales >= 14:
            confidence = "high"
        elif days_with_sales >= 7:
            confidence = "medium"
        else:
            confidence = "low"
        
        # If no reorder suggestions, confidence is still low
        if len(reorder_suggestions) == 0:
            confidence = "low"
        
        return {
            "reorder_suggestions": reorder_suggestions,
            "confidence": confidence,
            "method": "sales_history_analysis",
            "forecast_days": forecast_days,
            "data_quality": {
                "days_with_sales": days_with_sales,
                "analysis_period_days": 30
            }
        }
    
    async def predict_sales_by_type(
        self,
        db: AsyncSession,
        sucursal_id: Optional[str] = None,
        forecast_days: int = 7
    ) -> Dict[str, Any]:
        """
        Predict sales segmented by type (products, services, packages).
        
        Args:
            db: Database session
            sucursal_id: Optional sucursal ID to filter by
            forecast_days: Number of days to forecast
        
        Returns:
            Dictionary with predictions by type:
            {
                "forecast": {
                    "products": [{"date": "YYYY-MM-DD", "predicted_revenue_cents": int, "predicted_count": int}, ...],
                    "services": [{"date": "YYYY-MM-DD", "predicted_revenue_cents": int, "predicted_count": int}, ...],
                    "packages": [{"date": "YYYY-MM-DD", "predicted_revenue_cents": int, "predicted_count": int}, ...]
                },
                "confidence": "high" | "medium" | "low"
            }
        """
        from uuid import UUID
        
        # Get sucursal timezone for date/day-of-week extraction
        timezone_str = await self._get_sucursal_timezone(db, sucursal_id)
        
        # Use business date (today in sucursal timezone) instead of server date
        end_date = await self._get_business_date(db, sucursal_id)
        start_date = end_date - timedelta(days=30)
        
        # Extract date and day of week in sucursal timezone
        sale_date_expr = self._extract_date_in_timezone(Sale.created_at, timezone_str)
        sale_dow_expr = self._extract_dow_in_timezone(Sale.created_at, timezone_str)
        
        # Query for sales by type
        query = select(
            sale_date_expr.label("sale_date"),
            Sale.tipo.label("sale_type"),
            func.sum(Sale.total_cents).label("daily_revenue"),
            func.count(Sale.id).label("daily_count"),
            sale_dow_expr.label("day_of_week")
        ).where(
            and_(
                Sale.created_at >= datetime.combine(start_date, datetime.min.time()),
                Sale.created_at <= datetime.combine(end_date, datetime.max.time())
            )
        )
        
        if sucursal_id:
            try:
                sucursal_uuid = UUID(sucursal_id)
                query = query.where(Sale.sucursal_id == sucursal_uuid)
            except (ValueError, TypeError):
                logger.warning(f"Invalid sucursal_id format: {sucursal_id}")
        
        query = query.group_by(
            sale_date_expr,
            Sale.tipo,
            sale_dow_expr
        )
        query = query.order_by(sale_date_expr)
        
        result = await db.execute(query)
        historical_data = result.all()
        
        if not historical_data:
            return {
                "forecast": {
                    "products": [],
                    "services": [],
                    "packages": []
                },
                "confidence": "low",
                "message": "No historical sales data available"
            }
        
        # Group by type
        type_data: Dict[str, List] = {"product": [], "service": [], "package": []}
        for row in historical_data:
            sale_type = row.sale_type or "product"
            if sale_type in type_data:
                type_data[sale_type].append(row)
        
        # Generate predictions for each type
        forecast_by_type: Dict[str, List] = {
            "products": [],
            "services": [],
            "packages": []
        }
        
        type_mapping = {
            "product": "products",
            "service": "services",
            "package": "packages"
        }
        
        min_confidence = "high"
        
        for sale_type, data_rows in type_data.items():
            if not data_rows:
                continue
            
            # Calculate averages
            total_revenue = sum(row.daily_revenue or 0 for row in data_rows)
            total_count = sum(row.daily_count or 0 for row in data_rows)
            days_count = len(data_rows)
            
            avg_revenue = int(total_revenue / days_count) if days_count > 0 else 0
            avg_count = int(total_count / days_count) if days_count > 0 else 0
            
            # Calculate weekly pattern
            weekly_pattern = self._calculate_weekly_pattern(data_rows)
            
            # Calculate coefficient of variation
            historical_revenues = [float(row.daily_revenue or 0) for row in data_rows]
            cv = self._calculate_coefficient_of_variation(historical_revenues)
            
            # Calculate trend
            trend_factor = self._calculate_trend_factor(data_rows, recent_days=7)
            
            # Generate forecast
            type_forecast = []
            for i in range(1, forecast_days + 1):
                forecast_date = end_date + timedelta(days=i)
                
                # Get day-of-week factor
                day_factor = self._get_day_of_week_factor(forecast_date, weekly_pattern)
                
                # Apply trend with decay
                if abs(trend_factor - 1.0) > 0.05:
                    decay_factor = 1.0 - (i * 0.05)
                    adjusted_trend = 1.0 + ((trend_factor - 1.0) * decay_factor)
                else:
                    adjusted_trend = 1.0
                
                # Calculate base prediction
                base_factor = adjusted_trend * day_factor
                base_revenue = avg_revenue * base_factor
                base_count = avg_count * base_factor
                
                # Apply natural variation
                predicted_revenue = int(self._apply_natural_variation(base_revenue, cv))
                predicted_count = int(self._apply_natural_variation(base_count, cv * 0.8))
                
                type_forecast.append({
                    "date": forecast_date.isoformat(),
                    "predicted_revenue_cents": max(0, predicted_revenue),
                    "predicted_count": max(0, predicted_count)
                })
            
            forecast_by_type[type_mapping[sale_type]] = type_forecast
            
            # Determine confidence for this type
            if days_count < 7:
                type_confidence = "low"
            elif days_count < 14:
                type_confidence = "medium"
            else:
                type_confidence = "high"
            
            # Track minimum confidence
            if type_confidence == "low" or (type_confidence == "medium" and min_confidence == "high"):
                min_confidence = type_confidence
            elif type_confidence == "medium":
                min_confidence = "medium"
        
        return {
            "forecast": forecast_by_type,
            "confidence": min_confidence,
            "method": "type_segmented_moving_average"
        }
    
    async def predict_peak_hours(
        self,
        db: AsyncSession,
        sucursal_id: Optional[str] = None,
        forecast_days: int = 7
    ) -> Dict[str, Any]:
        """
        Predict peak hours for future days based on historical patterns.
        
        Args:
            db: Database session
            sucursal_id: Optional sucursal ID to filter by
            forecast_days: Number of days to forecast
        
        Returns:
            Dictionary with peak hour predictions:
            {
                "forecast": [
                    {
                        "date": "YYYY-MM-DD",
                        "predicted_peak_hours": [{"hour": int, "expected_activity": float}, ...],
                        "busiest_hour": {"hour": int, "expected_activity": float}
                    },
                    ...
                ],
                "confidence": "high" | "medium" | "low"
            }
        """
        from uuid import UUID
        
        # Get sucursal timezone for date/hour extraction
        timezone_str = await self._get_sucursal_timezone(db, sucursal_id)
        
        # Use business date (today in sucursal timezone) instead of server date
        end_date = await self._get_business_date(db, sucursal_id)
        start_date = end_date - timedelta(days=30)
        
        # Extract date, hour, and day of week in sucursal timezone
        date_expr = self._extract_date_in_timezone(Sale.created_at, timezone_str)
        hour_expr = self._extract_hour_in_timezone(Sale.created_at, timezone_str)
        dow_expr = self._extract_dow_in_timezone(Sale.created_at, timezone_str)
        
        # Query for sales by hour
        query = select(
            date_expr.label("sale_date"),
            hour_expr.label("hour"),
            func.count(Sale.id).label("hourly_count"),
            dow_expr.label("day_of_week")
        ).where(
            and_(
                Sale.created_at >= datetime.combine(start_date, datetime.min.time()),
                Sale.created_at <= datetime.combine(end_date, datetime.max.time())
            )
        )
        
        if sucursal_id:
            try:
                sucursal_uuid = UUID(sucursal_id)
                query = query.where(Sale.sucursal_id == sucursal_uuid)
            except (ValueError, TypeError):
                logger.warning(f"Invalid sucursal_id format: {sucursal_id}")
        
        query = query.group_by(
            date_expr,
            hour_expr,
            dow_expr
        )
        query = query.order_by(date_expr, hour_expr)
        
        result = await db.execute(query)
        historical_data = result.all()
        
        if not historical_data:
            return {
                "forecast": [],
                "confidence": "low",
                "message": "No historical sales data available for peak hours analysis"
            }
        
        # Group by day of week and hour
        hourly_patterns: Dict[int, Dict[int, List[int]]] = {}  # {day_of_week: {hour: [counts]}}
        
        for row in historical_data:
            dow = int(row.day_of_week) if row.day_of_week is not None else 0
            hour = int(row.hour) if row.hour is not None else 12
            count = int(row.hourly_count or 0)
            
            if dow not in hourly_patterns:
                hourly_patterns[dow] = {}
            if hour not in hourly_patterns[dow]:
                hourly_patterns[dow][hour] = []
            hourly_patterns[dow][hour].append(count)
        
        # Calculate average activity per hour for each day of week
        avg_hourly_activity: Dict[int, Dict[int, float]] = {}  # {day_of_week: {hour: avg_activity}}
        
        for dow, hours in hourly_patterns.items():
            avg_hourly_activity[dow] = {}
            for hour, counts in hours.items():
                avg_hourly_activity[dow][hour] = sum(counts) / len(counts) if counts else 0
        
        # Generate forecast
        forecast = []
        for i in range(1, forecast_days + 1):
            forecast_date = end_date + timedelta(days=i)
            dow = forecast_date.weekday()  # 0=Monday, 6=Sunday
            
            # Get hourly pattern for this day of week
            day_pattern = avg_hourly_activity.get(dow, {})
            
            if not day_pattern:
                # Fallback: use overall average if no pattern for this day
                all_hours = {}
                for pattern in avg_hourly_activity.values():
                    for hour, activity in pattern.items():
                        if hour not in all_hours:
                            all_hours[hour] = []
                        all_hours[hour].append(activity)
                
                day_pattern = {
                    hour: sum(activities) / len(activities) if activities else 0
                    for hour, activities in all_hours.items()
                }
            
            # Create peak hours list (top 3 hours)
            peak_hours_list = sorted(
                [(hour, activity) for hour, activity in day_pattern.items() if activity > 0],
                key=lambda x: x[1],
                reverse=True
            )[:3]
            
            predicted_peak_hours = [
                {"hour": hour, "expected_activity": round(activity, 2)}
                for hour, activity in peak_hours_list
            ]
            
            busiest_hour = None
            if peak_hours_list:
                busiest_hour = {
                    "hour": peak_hours_list[0][0],
                    "expected_activity": round(peak_hours_list[0][1], 2)
                }
            
            forecast.append({
                "date": forecast_date.isoformat(),
                "predicted_peak_hours": predicted_peak_hours,
                "busiest_hour": busiest_hour
            })
        
        # Determine confidence
        total_data_points = sum(len(hours) for hours in hourly_patterns.values())
        if total_data_points < 20:
            confidence = "low"
        elif total_data_points < 50:
            confidence = "medium"
        else:
            confidence = "high"
        
        return {
            "forecast": forecast,
            "confidence": confidence,
            "method": "hourly_pattern_analysis"
        }
    
    async def predict_busiest_days(
        self,
        db: AsyncSession,
        sucursal_id: Optional[str] = None,
        forecast_days: int = 7
    ) -> Dict[str, Any]:
        """
        Predict which days will be busiest in the forecast period.
        
        Args:
            db: Database session
            sucursal_id: Optional sucursal ID to filter by
            forecast_days: Number of days to forecast
        
        Returns:
            Dictionary with busiest days predictions:
            {
                "forecast": [
                    {"date": "YYYY-MM-DD", "day_of_week": str, "predicted_activity": float, "rank": int},
                    ...
                ],
                "confidence": "high" | "medium" | "low"
            }
        """
        from uuid import UUID
        
        # Get sucursal timezone for date/day-of-week extraction
        timezone_str = await self._get_sucursal_timezone(db, sucursal_id)
        
        # Use business date (today in sucursal timezone) instead of server date
        end_date = await self._get_business_date(db, sucursal_id)
        start_date = end_date - timedelta(days=30)
        
        # Extract date and day of week in sucursal timezone
        sale_date_expr = self._extract_date_in_timezone(Sale.created_at, timezone_str)
        sale_dow_expr = self._extract_dow_in_timezone(Sale.created_at, timezone_str)
        
        # Query for daily sales
        query = select(
            sale_date_expr.label("sale_date"),
            func.sum(Sale.total_cents).label("daily_revenue"),
            func.count(Sale.id).label("daily_count"),
            sale_dow_expr.label("day_of_week")
        ).where(
            and_(
                Sale.created_at >= datetime.combine(start_date, datetime.min.time()),
                Sale.created_at <= datetime.combine(end_date, datetime.max.time())
            )
        )
        
        if sucursal_id:
            try:
                sucursal_uuid = UUID(sucursal_id)
                query = query.where(Sale.sucursal_id == sucursal_uuid)
            except (ValueError, TypeError):
                logger.warning(f"Invalid sucursal_id format: {sucursal_id}")
        
        query = query.group_by(sale_date_expr, sale_dow_expr)
        query = query.order_by(sale_date_expr)
        
        result = await db.execute(query)
        historical_data = result.all()
        
        if not historical_data:
            return {
                "forecast": [],
                "confidence": "low",
                "message": "No historical sales data available"
            }
        
        # Calculate weekly pattern
        weekly_pattern = self._calculate_weekly_pattern(historical_data)
        
        # Calculate average daily activity
        total_revenue = sum(row.daily_revenue or 0 for row in historical_data)
        days_count = len(historical_data)
        avg_revenue = total_revenue / days_count if days_count > 0 else 0
        
        # Generate forecast
        forecast = []
        for i in range(1, forecast_days + 1):
            forecast_date = end_date + timedelta(days=i)
            dow = forecast_date.weekday()  # 0=Monday, 6=Sunday
            
            # Get day-of-week factor
            day_factor = self._get_day_of_week_factor(forecast_date, weekly_pattern)
            
            # Calculate predicted activity
            predicted_activity = avg_revenue * day_factor
            
            # Apply natural variation
            historical_revenues = [float(row.daily_revenue or 0) for row in historical_data]
            cv = self._calculate_coefficient_of_variation(historical_revenues)
            predicted_activity = self._apply_natural_variation(predicted_activity, cv)
            
            # Day name
            day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            day_name = day_names[dow]
            
            forecast.append({
                "date": forecast_date.isoformat(),
                "day_of_week": day_name,
                "predicted_activity": round(predicted_activity, 2),
                "rank": 0  # Will be set after sorting
            })
        
        # Sort by predicted activity and assign ranks
        forecast.sort(key=lambda x: x["predicted_activity"], reverse=True)
        for idx, day in enumerate(forecast, start=1):
            day["rank"] = idx
        
        # Determine confidence
        if days_count < 14:
            confidence = "low"
        elif days_count < 30:
            confidence = "medium"
        else:
            confidence = "high"
        
        return {
            "forecast": forecast,
            "confidence": confidence,
            "method": "weekly_pattern_analysis"
        }
    
    async def generate_all_predictions(
        self,
        db: AsyncSession,
        sucursal_id: Optional[str] = None,
        forecast_days: int = 7
    ) -> Dict[str, Any]:
        """
        Generate all types of predictions in parallel using separate database sessions.
        
        Each prediction task uses its own database session to allow true parallelism
        without SQLAlchemy async session conflicts.
        
        Args:
            db: Database session (not used directly, but kept for API compatibility)
            sucursal_id: Optional sucursal ID to filter by
            forecast_days: Number of days to forecast
            
        Returns:
            Dictionary with all predictions combined
        """
        import asyncio
        from database import AsyncSessionLocal
        
        # Wrapper functions that create their own sessions for parallel execution
        # This allows true parallelism without SQLAlchemy async session conflicts
        async def _predict_sales():
            async with AsyncSessionLocal() as session:
                return await self.predict_sales(session, sucursal_id, forecast_days)
        
        async def _predict_capacity():
            async with AsyncSessionLocal() as session:
                return await self.predict_capacity(session, sucursal_id, forecast_days)
        
        async def _predict_stock():
            async with AsyncSessionLocal() as session:
                return await self.predict_stock_needs(session, sucursal_id, forecast_days)
        
        async def _predict_sales_by_type():
            async with AsyncSessionLocal() as session:
                return await self.predict_sales_by_type(session, sucursal_id, forecast_days)
        
        async def _predict_peak_hours():
            async with AsyncSessionLocal() as session:
                return await self.predict_peak_hours(session, sucursal_id, forecast_days)
        
        async def _predict_busiest_days():
            async with AsyncSessionLocal() as session:
                return await self.predict_busiest_days(session, sucursal_id, forecast_days)
        
        # Execute all predictions in parallel with separate sessions
        # Each session is automatically closed when the context manager exits
        sales_pred, capacity_pred, stock_pred, sales_by_type_pred, peak_hours_pred, busiest_days_pred = await asyncio.gather(
            _predict_sales(),
            _predict_capacity(),
            _predict_stock(),
            _predict_sales_by_type(),
            _predict_peak_hours(),
            _predict_busiest_days()
        )
        
        return {
            "sales": sales_pred,
            "capacity": capacity_pred,
            "stock": stock_pred,
            "sales_by_type": sales_by_type_pred,
            "peak_hours": peak_hours_pred,
            "busiest_days": busiest_days_pred,
            "generated_at": datetime.utcnow().isoformat(),
            "forecast_days": forecast_days
        }

    async def predict_sales_enhanced(
        self,
        db: AsyncSession,
        sucursal_id: Optional[str] = None,
        forecast_days: int = 7,
        module: Optional[str] = None  # "recepcion", "kidibar", or None for all
    ) -> Dict[str, Any]:
        """
        Enhanced sales prediction with module segmentation, day-of-week adjustment, and outlier validation.
        
        Improvements over predict_sales:
        1. Module segmentation: Separate predictions for Recepción vs KidiBar
        2. Day-of-week adjustment: Accounts for weekly patterns (weekends, weekdays)
        3. Outlier validation: Filters out anomalous data points
        
        Args:
            db: Database session
            sucursal_id: Optional sucursal ID to filter by
            forecast_days: Number of days to forecast (default: 7)
            module: Optional module filter ("recepcion", "kidibar", or None for all)
            
        Returns:
            Dictionary with enhanced sales predictions:
            {
                "forecast": [
                    {"date": "YYYY-MM-DD", "predicted_revenue_cents": int, "predicted_count": int, "day_of_week": str},
                    ...
                ],
                "confidence": "high" | "medium" | "low",
                "method": "enhanced_moving_average",
                "module": str | None,
                "day_of_week_adjustments": dict,
                "outliers_removed": int
            }
        """
        from uuid import UUID
        
        # Get sucursal timezone for date/day-of-week extraction
        timezone_str = await self._get_sucursal_timezone(db, sucursal_id)
        
        # Get historical data (last 30 days, extended to 60 for better day-of-week analysis)
        # Use business date (today in sucursal timezone) instead of server date
        end_date = await self._get_business_date(db, sucursal_id)
        start_date = end_date - timedelta(days=60)
        
        # Extract date and day of week in sucursal timezone
        date_expr = self._extract_date_in_timezone(Sale.created_at, timezone_str)
        dow_expr = self._extract_dow_in_timezone(Sale.created_at, timezone_str)
        
        # Build base query
        query = select(
            date_expr.label("sale_date"),
            func.sum(Sale.total_cents).label("daily_revenue"),
            func.count(Sale.id).label("daily_count"),
            dow_expr.label("day_of_week")  # 0=Sunday, 6=Saturday
        ).where(
            and_(
                Sale.created_at >= datetime.combine(start_date, datetime.min.time()),
                Sale.created_at <= datetime.combine(end_date, datetime.max.time())
            )
        )
        
        # Apply module filter
        if module == "recepcion":
            # Recepción: services + service packages
            query = query.where(Sale.tipo.in_(["service", "package"]))
            # We'll filter packages later
        elif module == "kidibar":
            # KidiBar: products + product packages
            query = query.where(Sale.tipo.in_(["product", "package"]))
            # We'll filter packages later
        
        if sucursal_id:
            try:
                sucursal_uuid = UUID(sucursal_id)
                query = query.where(Sale.sucursal_id == sucursal_uuid)
            except (ValueError, TypeError):
                logger.warning(f"Invalid sucursal_id format: {sucursal_id}")
        
        query = query.group_by(date_expr, dow_expr)
        query = query.order_by(date_expr)
        
        result = await db.execute(query)
        historical_data = result.all()
        
        # Filter package sales by module if needed
        if module and historical_data:
            # Get package IDs from sales
            package_sale_dates = {}
            for row in historical_data:
                if row.sale_date not in package_sale_dates:
                    package_sale_dates[row.sale_date] = []
            
            # Query package sales for these dates
            package_query = select(
                date_expr.label("sale_date"),
                SaleItem.ref_id.label("package_id"),
                Sale.total_cents.label("total_cents")
            ).join(
                Sale, SaleItem.sale_id == Sale.id
            ).where(
                and_(
                    SaleItem.type == "package",
                    Sale.tipo == "package",
                    date_expr.in_(list(package_sale_dates.keys()))
                )
            )
            
            if sucursal_id:
                try:
                    sucursal_uuid = UUID(sucursal_id)
                    package_query = package_query.where(Sale.sucursal_id == sucursal_uuid)
                except (ValueError, TypeError):
                    pass
            
            package_result = await db.execute(package_query)
            package_rows = package_result.all()
            
            if package_rows:
                package_ids = list(set(row.package_id for row in package_rows))
                packages_query = select(Package).where(Package.id.in_(package_ids))
                packages_result = await db.execute(packages_query)
                packages = packages_result.scalars().all()
                
                if module == "recepcion":
                    valid_package_ids = set(get_service_package_ids(list(packages)))
                else:  # kidibar
                    valid_package_ids = set(get_product_package_ids(list(packages)))
                
                # Filter historical data: remove package sales that don't match module
                filtered_data = []
                for row in historical_data:
                    # If it's a package sale date, check if package is valid
                    if row.sale_date in package_sale_dates:
                        # This is a simplified check - in reality we'd need to match by date
                        # For now, we'll keep all data and adjust later
                        filtered_data.append(row)
                    else:
                        filtered_data.append(row)
                
                historical_data = filtered_data
        
        if not historical_data or len(historical_data) < 3:
            return {
                "forecast": [],
                "confidence": "low",
                "method": "insufficient_data",
                "message": "Not enough historical data for prediction (need at least 3 days)",
                "module": module
            }
        
        # Outlier validation: Remove days that are >3 standard deviations from mean
        revenues = [row.daily_revenue or 0 for row in historical_data]
        if len(revenues) > 0:
            import statistics
            mean_revenue = statistics.mean(revenues)
            if len(revenues) > 1:
                std_revenue = statistics.stdev(revenues)
                threshold = mean_revenue + (3 * std_revenue)
                
                filtered_data = []
                outliers_removed = 0
                for row in historical_data:
                    if (row.daily_revenue or 0) <= threshold:
                        filtered_data.append(row)
                    else:
                        outliers_removed += 1
                        logger.debug(f"Removed outlier: date={row.sale_date}, revenue={row.daily_revenue}")
                
                historical_data = filtered_data
            else:
                outliers_removed = 0
        else:
            outliers_removed = 0
        
        if len(historical_data) < 3:
            return {
                "forecast": [],
                "confidence": "low",
                "method": "insufficient_data_after_outlier_removal",
                "message": "Not enough data after outlier removal",
                "module": module,
                "outliers_removed": outliers_removed
            }
        
        # Calculate day-of-week averages
        day_of_week_data: Dict[int, List[float]] = {i: [] for i in range(7)}  # 0=Sunday, 6=Saturday
        for row in historical_data:
            dow = int(row.day_of_week or 0)
            day_of_week_data[dow].append(row.daily_revenue or 0)
        
        day_of_week_avg: Dict[int, float] = {}
        for dow, revenues in day_of_week_data.items():
            if revenues:
                day_of_week_avg[dow] = sum(revenues) / len(revenues)
            else:
                day_of_week_avg[dow] = 0.0
        
        # Calculate overall average
        total_revenue = sum(row.daily_revenue or 0 for row in historical_data)
        total_count = sum(row.daily_count or 0 for row in historical_data)
        days_count = len(historical_data)
        
        avg_revenue = total_revenue / days_count if days_count > 0 else 0
        avg_count = total_count / days_count if days_count > 0 else 0
        
        # Calculate day-of-week adjustment factors (relative to overall average)
        day_of_week_factors: Dict[int, float] = {}
        for dow, avg in day_of_week_avg.items():
            if avg_revenue > 0:
                day_of_week_factors[dow] = avg / avg_revenue
            else:
                day_of_week_factors[dow] = 1.0
        
        # Calculate trend (last 7 days vs previous 7 days)
        recent_days = min(7, len(historical_data))
        recent_revenue = sum(
            row.daily_revenue or 0 
            for row in historical_data[-recent_days:]
        ) / recent_days
        
        previous_revenue = 0
        if len(historical_data) >= 14:
            previous_revenue = sum(
                row.daily_revenue or 0 
                for row in historical_data[-14:-recent_days]
            ) / recent_days
        
        trend_factor = 1.0
        if previous_revenue > 0:
            trend_factor = recent_revenue / previous_revenue
        
        # Generate forecast with day-of-week adjustments
        forecast = []
        day_names = ["Domingo", "Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"]
        
        for i in range(1, forecast_days + 1):
            forecast_date = end_date + timedelta(days=i)
            day_of_week = forecast_date.weekday()  # 0=Monday, 6=Sunday (Python's weekday)
            # Convert to Sunday=0 format
            dow_index = (day_of_week + 1) % 7
            
            # Get day-of-week adjustment factor
            dow_factor = day_of_week_factors.get(dow_index, 1.0)
            
            # Apply trend with decay
            decay_factor = 1.0 - (i * 0.05)
            adjusted_trend = 1.0 + ((trend_factor - 1.0) * decay_factor)
            
            # Combine factors
            final_factor = adjusted_trend * dow_factor
            
            predicted_revenue = int(avg_revenue * final_factor)
            predicted_count = int(avg_count * final_factor)
            
            forecast.append({
                "date": forecast_date.isoformat(),
                "predicted_revenue_cents": max(0, predicted_revenue),
                "predicted_count": max(0, predicted_count),
                "day_of_week": day_names[dow_index],
                "day_of_week_factor": round(dow_factor, 2)
            })
        
        # Determine confidence
        confidence = "low"
        if days_count >= 14 and abs(trend_factor - 1.0) < 0.2:
            confidence = "high"
        elif days_count >= 7:
            confidence = "medium"
        
        # Reduce confidence if many outliers were removed
        if outliers_removed > len(historical_data) * 0.1:  # More than 10% outliers
            if confidence == "high":
                confidence = "medium"
            elif confidence == "medium":
                confidence = "low"
        
        return {
            "forecast": forecast,
            "confidence": confidence,
            "method": "enhanced_moving_average",
            "module": module,
            "historical_avg_revenue_cents": int(avg_revenue),
            "historical_avg_count": int(avg_count),
            "trend_factor": round(trend_factor, 2),
            "historical_days": days_count,
            "day_of_week_adjustments": {
                day_names[i]: round(day_of_week_factors.get(i, 1.0), 2)
                for i in range(7)
            },
            "outliers_removed": outliers_removed
        }


