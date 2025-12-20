"""
Report Service - Business logic for analytics and metrics reports.

Integrates with AnalyticsCache for efficient metric retrieval.
All methods support optional caching to reduce database load.
"""
import logging
import asyncio
from datetime import datetime, date, timedelta
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, case, Integer
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import literal_column

from models.sale import Sale
from models.sale_item import SaleItem
from models.product import Product
from models.service import Service
from models.timer import Timer
from models.package import Package
from models.sucursal import Sucursal
from services.analytics_cache import get_cache
from utils.package_helpers import get_service_package_ids, get_product_package_ids
from utils.datetime_helpers import get_business_date_in_timezone
from sqlalchemy import text
from uuid import UUID
from datetime import timezone as dt_timezone

logger = logging.getLogger(__name__)


class ReportService:
    """Service for generating analytics reports with optional caching."""
    
    def __init__(self):
        """Initialize ReportService with cache."""
        self.cache = get_cache()
        # Cache for sucursal timezones to avoid repeated DB queries
        self._timezone_cache: Dict[str, str] = {}
    
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
            sucursal_uuid = UUID(sucursal_id)
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
        # Only allow alphanumeric, underscore, slash, and hyphen
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
        
        return func.extract('dow', timezone_expr)
    
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
    
    async def get_sales_report(
        self,
        db: AsyncSession,
        sucursal_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Get sales report with aggregations.
        
        Args:
            db: Database session
            sucursal_id: Optional sucursal ID to filter by
            start_date: Optional start date (defaults to today)
            end_date: Optional end date (defaults to today)
            use_cache: Whether to use cache (default: True)
            
        Returns:
            Dictionary with sales metrics:
            {
                "total_revenue_cents": int,
                "average_transaction_value_cents": int,
                "sales_count": int,
                "unique_customers": int,
                "revenue_by_type": dict,
                "revenue_by_sucursal": dict,
                "revenue_by_payment_method": dict,
                "period": {
                    "start_date": str,
                    "end_date": str
                }
            }
        """
        # Generate cache key
        cache_key = self.cache._generate_key(
            "sales",
            sucursal_id,
            start_date.isoformat() if start_date else None,
            end_date.isoformat() if end_date else None
        )
        
        # Check cache
        if use_cache:
            cached = await self.cache.get(cache_key)
            if cached:
                logger.debug(f"Cache HIT for sales report: {cache_key}")
                return cached
        
        # Default to today if no dates provided
        if not start_date:
            start_date = date.today()
        if not end_date:
            end_date = date.today()
        
        # Build query
        query = select(
            func.sum(Sale.total_cents).label("total_revenue"),
            func.count(Sale.id).label("sales_count"),
            func.avg(Sale.total_cents).label("avg_transaction_value"),
            Sale.tipo,
            Sale.sucursal_id,
            Sale.payment_method
        ).where(
            and_(
                Sale.created_at >= datetime.combine(start_date, datetime.min.time()),
                Sale.created_at <= datetime.combine(end_date, datetime.max.time())
            )
        )
        
        if sucursal_id:
            query = query.where(Sale.sucursal_id == sucursal_id)
        
        query = query.group_by(Sale.tipo, Sale.sucursal_id, Sale.payment_method)
        
        result = await db.execute(query)
        rows = result.all()
        
        # Aggregate results
        total_revenue_cents = 0
        total_sales_count = 0
        revenue_by_type: Dict[str, int] = {}
        revenue_by_sucursal: Dict[str, int] = {}
        revenue_by_payment_method: Dict[str, int] = {}
        
        for row in rows:
            revenue = int(row.total_revenue or 0)
            count = int(row.sales_count or 0)
            
            total_revenue_cents += revenue
            total_sales_count += count
            
            # Revenue by type
            tipo = row.tipo or "unknown"
            revenue_by_type[tipo] = revenue_by_type.get(tipo, 0) + revenue
            
            # Revenue by sucursal
            suc_id = str(row.sucursal_id) if row.sucursal_id else "unknown"
            revenue_by_sucursal[suc_id] = revenue_by_sucursal.get(suc_id, 0) + revenue
            
            # Revenue by payment method
            payment = row.payment_method or "unknown"
            revenue_by_payment_method[payment] = revenue_by_payment_method.get(payment, 0) + revenue
        
        # Calculate ATV
        avg_transaction_value_cents = (
            int(total_revenue_cents / total_sales_count)
            if total_sales_count > 0
            else 0
        )
        
        # Calculate unique customers (separate query following project pattern)
        unique_customers_query = select(
            func.count(func.distinct(Sale.payer_name)).label("unique_customers")
        ).where(
            and_(
                Sale.payer_name.isnot(None),
                Sale.payer_name != '',
                Sale.created_at >= datetime.combine(start_date, datetime.min.time()),
                Sale.created_at <= datetime.combine(end_date, datetime.max.time())
            )
        )
        
        if sucursal_id:
            unique_customers_query = unique_customers_query.where(Sale.sucursal_id == sucursal_id)
        
        unique_customers_result = await db.execute(unique_customers_query)
        unique_customers = unique_customers_result.scalar() or 0
        
        report = {
            "total_revenue_cents": total_revenue_cents,
            "average_transaction_value_cents": avg_transaction_value_cents,
            "sales_count": total_sales_count,
            "unique_customers": unique_customers,
            "revenue_by_type": revenue_by_type,
            "revenue_by_sucursal": revenue_by_sucursal,
            "revenue_by_payment_method": revenue_by_payment_method,
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            }
        }
        
        # Cache result
        if use_cache:
            await self.cache.set(cache_key, report, ttl=300)  # 5 minutes
        
        logger.info(
            f"Sales report generated: {total_sales_count} sales, "
            f"${total_revenue_cents/100:.2f} revenue, "
            f"{unique_customers} unique customers"
        )
        
        return report
    
    async def get_sales_timeseries(
        self,
        db: AsyncSession,
        sucursal_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Get sales time series data aggregated by day.
        
        Args:
            db: Database session
            sucursal_id: Optional sucursal ID to filter by
            start_date: Optional start date (defaults to 30 days ago)
            end_date: Optional end date (defaults to today)
            use_cache: Whether to use cache (default: True)
            
        Returns:
            Dictionary with time series data:
            {
                "timeseries": [
                    {
                        "date": "YYYY-MM-DD",
                        "revenue_cents": int,
                        "sales_count": int,
                        "atv_cents": int
                    },
                    ...
                ],
                "period": {
                    "start_date": str,
                    "end_date": str
                }
            }
        """
        # Generate cache key
        cache_key = self.cache._generate_key(
            "sales_timeseries",
            sucursal_id,
            start_date.isoformat() if start_date else None,
            end_date.isoformat() if end_date else None
        )
        
        # Check cache
        if use_cache:
            cached = await self.cache.get(cache_key)
            if cached:
                logger.debug(f"Cache HIT for sales timeseries: {cache_key}")
                return cached
        
        # Default to last 30 days if no dates provided
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        # Build query to aggregate by day
        query = select(
            func.date(Sale.created_at).label("sale_date"),
            func.sum(Sale.total_cents).label("total_revenue"),
            func.count(Sale.id).label("sales_count"),
            func.avg(Sale.total_cents).label("avg_transaction_value")
        ).where(
            and_(
                func.date(Sale.created_at) >= start_date,
                func.date(Sale.created_at) <= end_date
            )
        )
        
        if sucursal_id:
            query = query.where(Sale.sucursal_id == sucursal_id)
        
        query = query.group_by(func.date(Sale.created_at)).order_by(func.date(Sale.created_at))
        
        result = await db.execute(query)
        rows = result.all()
        
        # Transform to time series format
        timeseries = []
        for row in rows:
            sale_date = row.sale_date
            revenue_cents = int(row.total_revenue or 0)
            sales_count = int(row.sales_count or 0)
            atv_cents = int(row.avg_transaction_value or 0)
            
            timeseries.append({
                "date": sale_date.isoformat() if isinstance(sale_date, date) else sale_date,
                "revenue_cents": revenue_cents,
                "sales_count": sales_count,
                "atv_cents": atv_cents
            })
        
        # Fill in missing dates with zeros
        current_date = start_date
        filled_timeseries = []
        timeseries_dict = {item["date"]: item for item in timeseries}
        
        while current_date <= end_date:
            date_str = current_date.isoformat()
            if date_str in timeseries_dict:
                filled_timeseries.append(timeseries_dict[date_str])
            else:
                filled_timeseries.append({
                    "date": date_str,
                    "revenue_cents": 0,
                    "sales_count": 0,
                    "atv_cents": 0
                })
            current_date += timedelta(days=1)
        
        report = {
            "timeseries": filled_timeseries,
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            }
        }
        
        # Cache result
        if use_cache:
            await self.cache.set(cache_key, report, ttl=300)  # 5 minutes
        
        logger.info(
            f"Sales timeseries generated: {len(filled_timeseries)} days, "
            f"from {start_date.isoformat()} to {end_date.isoformat()}"
        )
        
        return report
    
    async def get_day_totals_for_arqueo(
        self,
        db: AsyncSession,
        sucursal_id: str,
        start_datetime: datetime,
        end_datetime: datetime
    ) -> Dict[str, Any]:
        """
        Get day totals optimized for arqueo (cash reconciliation) calculation.
        
        This method is specifically designed for day close operations and only
        returns the data necessary for arqueo calculations, avoiding unnecessary
        data like average_transaction_value or revenue_by_sucursal.
        
        Args:
            db: Database session
            sucursal_id: Sucursal ID (required, as UUID string)
            start_datetime: Start datetime (timezone-aware)
            end_datetime: End datetime (timezone-aware)
            
        Returns:
            Dictionary with day totals:
            {
                "total_revenue_cents": int,
                "total_sales_count": int,
                "revenue_by_payment_method": {
                    "cash": int,
                    "card": int,
                    "transfer": int
                },
                "revenue_by_type": {
                    "service": int,
                    "product": int,
                    "package": int
                },
                "cash_received_total_cents": int  # SUM of cash_received_cents for cash payments
            }
        """
        from uuid import UUID
        
        # Convert sucursal_id to UUID
        try:
            sucursal_uuid = UUID(sucursal_id)
        except (ValueError, TypeError):
            logger.error(f"Invalid sucursal_id format: {sucursal_id}")
            raise ValueError(f"Invalid sucursal_id format: {sucursal_id}")
        
        # Build optimized query for arqueo - only select what we need
        query = select(
            func.sum(Sale.total_cents).label("total_revenue"),
            func.count(Sale.id).label("sales_count"),
            func.sum(
                case(
                    (Sale.payment_method == "cash", Sale.cash_received_cents),
                    else_=0
                )
            ).label("cash_received_total"),
            Sale.payment_method,
            Sale.tipo
        ).where(
            and_(
                Sale.sucursal_id == sucursal_uuid,
                Sale.created_at >= start_datetime,
                Sale.created_at <= end_datetime
            )
        ).group_by(Sale.payment_method, Sale.tipo)
        
        result = await db.execute(query)
        rows = result.all()
        
        # Initialize aggregations
        total_revenue_cents = 0
        total_sales_count = 0
        revenue_by_payment_method: Dict[str, int] = {
            "cash": 0,
            "card": 0,
            "transfer": 0
        }
        revenue_by_type: Dict[str, int] = {}
        cash_received_total_cents = 0
        
        # Aggregate results
        for row in rows:
            revenue = int(row.total_revenue or 0)
            count = int(row.sales_count or 0)
            cash_received = int(row.cash_received_total or 0)
            
            total_revenue_cents += revenue
            total_sales_count += count
            cash_received_total_cents += cash_received
            
            # Revenue by payment method
            payment = row.payment_method or "unknown"
            if payment in revenue_by_payment_method:
                revenue_by_payment_method[payment] += revenue
            else:
                revenue_by_payment_method[payment] = revenue
            
            # Revenue by type
            tipo = row.tipo or "unknown"
            revenue_by_type[tipo] = revenue_by_type.get(tipo, 0) + revenue
        
        # Handle edge case: if cash_received_total is 0 but we have cash sales,
        # use total_cents as fallback (for legacy data or missing cash_received_cents)
        if cash_received_total_cents == 0 and revenue_by_payment_method.get("cash", 0) > 0:
            logger.warning(
                f"cash_received_total_cents is 0 but cash sales exist. "
                f"Using revenue_by_payment_method['cash'] as fallback. "
                f"Sucursal: {sucursal_id}"
            )
            cash_received_total_cents = revenue_by_payment_method["cash"]
        
        return {
            "total_revenue_cents": total_revenue_cents,
            "total_sales_count": total_sales_count,
            "revenue_by_payment_method": revenue_by_payment_method,
            "revenue_by_type": revenue_by_type,
            "cash_received_total_cents": cash_received_total_cents
        }
    
    async def get_day_totals_for_arqueo_kidibar(
        self,
        db: AsyncSession,
        sucursal_id: str,
        start_datetime: datetime,
        end_datetime: datetime
    ) -> Dict[str, Any]:
        """
        Get day totals for KidiBar arqueo (cash reconciliation) calculation.
        
        This method filters ONLY:
        - Direct product sales (tipo="product")
        - Product package sales (packages containing only products)
        
        Excludes:
        - Service sales
        - Service packages
        - Mixed packages (products + services)
        
        Args:
            db: Database session
            sucursal_id: Sucursal ID (required, as UUID string)
            start_datetime: Start datetime (timezone-aware)
            end_datetime: End datetime (timezone-aware)
            
        Returns:
            Dictionary with day totals (same format as get_day_totals_for_arqueo):
            {
                "total_revenue_cents": int,
                "total_sales_count": int,
                "revenue_by_payment_method": {
                    "cash": int,
                    "card": int,
                    "transfer": int
                },
                "revenue_by_type": {
                    "product": int,
                    "package": int  # Only product packages
                },
                "cash_received_total_cents": int
            }
        """
        from uuid import UUID
        
        # Convert sucursal_id to UUID
        try:
            sucursal_uuid = UUID(sucursal_id)
        except (ValueError, TypeError):
            logger.error(f"Invalid sucursal_id format: {sucursal_id}")
            raise ValueError(f"Invalid sucursal_id format: {sucursal_id}")
        
        # ===== STEP 1: Query direct product sales =====
        product_sales_query = select(
            func.sum(Sale.total_cents).label("total_revenue"),
            func.count(Sale.id).label("sales_count"),
            func.sum(
                case(
                    (Sale.payment_method == "cash", Sale.cash_received_cents),
                    else_=0
                )
            ).label("cash_received_total"),
            Sale.payment_method
        ).where(
            and_(
                Sale.tipo == "product",
                Sale.sucursal_id == sucursal_uuid,
                Sale.created_at >= start_datetime,
                Sale.created_at <= end_datetime
            )
        ).group_by(Sale.payment_method)
        
        product_sales_result = await db.execute(product_sales_query)
        product_sales_rows = product_sales_result.all()
        
        # ===== STEP 2: Query package sales and filter product packages =====
        # First, get all package sales for the date/sucursal
        package_sales_query = select(
            SaleItem.ref_id.label("package_id"),
            Sale.id.label("sale_id"),
            Sale.total_cents.label("total_cents"),
            case(
                (Sale.payment_method == "cash", Sale.cash_received_cents),
                else_=0
            ).label("cash_received_cents"),
            Sale.payment_method
        ).join(
            Sale, SaleItem.sale_id == Sale.id
        ).where(
            and_(
                SaleItem.type == "package",
                Sale.tipo == "package",
                Sale.sucursal_id == sucursal_uuid,
                Sale.created_at >= start_datetime,
                Sale.created_at <= end_datetime
            )
        ).distinct()
        
        package_sales_result = await db.execute(package_sales_query)
        package_sales_rows = package_sales_result.all()
        
        # Extract unique package IDs (for filtering) and unique sale IDs (to avoid double counting)
        package_ids = list(set(row.package_id for row in package_sales_rows))
        sale_ids_seen = set()  # Track sales we've already counted
        
        # Initialize aggregations
        total_revenue_cents = 0
        total_sales_count = 0
        revenue_by_payment_method: Dict[str, int] = {
            "cash": 0,
            "card": 0,
            "transfer": 0
        }
        revenue_by_type: Dict[str, int] = {
            "product": 0,
            "package": 0
        }
        cash_received_total_cents = 0
        product_package_ids = []
        
        # Aggregate product sales
        for row in product_sales_rows:
            revenue = int(row.total_revenue or 0)
            count = int(row.sales_count or 0)
            cash_received = int(row.cash_received_total or 0)
            
            total_revenue_cents += revenue
            total_sales_count += count
            cash_received_total_cents += cash_received
            revenue_by_type["product"] += revenue
            
            # Revenue by payment method
            payment = row.payment_method or "unknown"
            if payment in revenue_by_payment_method:
                revenue_by_payment_method[payment] += revenue
        
        # Filter product packages if we have package sales
        if package_ids:
            packages_query = select(Package).where(Package.id.in_(package_ids))
            packages_result = await db.execute(packages_query)
            packages = packages_result.scalars().all()
            
            # Get product package IDs using helper
            product_package_ids = get_product_package_ids(list(packages))
            product_package_ids_set = set(product_package_ids)
            
            # Aggregate revenue and count for product packages only
            # Use sale_id to avoid double counting if a sale has multiple package items
            for row in package_sales_rows:
                if row.package_id in product_package_ids_set:
                    sale_id = row.sale_id
                    # Skip if we've already counted this sale
                    if sale_id in sale_ids_seen:
                        continue
                    sale_ids_seen.add(sale_id)
                    
                    revenue = int(row.total_cents or 0)
                    cash_received = int(row.cash_received_cents or 0)
                    
                    total_revenue_cents += revenue
                    total_sales_count += 1
                    cash_received_total_cents += cash_received
                    revenue_by_type["package"] += revenue
                    
                    # Revenue by payment method
                    payment = row.payment_method or "unknown"
                    if payment in revenue_by_payment_method:
                        revenue_by_payment_method[payment] += revenue
        
        # Handle edge case: if cash_received_total is 0 but we have cash sales,
        # use total_cents as fallback (for legacy data or missing cash_received_cents)
        if cash_received_total_cents == 0 and revenue_by_payment_method.get("cash", 0) > 0:
            logger.warning(
                f"cash_received_total_cents is 0 but cash sales exist for KidiBar. "
                f"Using revenue_by_payment_method['cash'] as fallback. "
                f"Sucursal: {sucursal_id}"
            )
            cash_received_total_cents = revenue_by_payment_method["cash"]
        
        logger.debug(
            f"KidiBar arqueo totals for sucursal {sucursal_id}: "
            f"{total_sales_count} sales, ${total_revenue_cents/100:.2f} revenue"
        )
        
        return {
            "total_revenue_cents": total_revenue_cents,
            "total_sales_count": total_sales_count,
            "revenue_by_payment_method": revenue_by_payment_method,
            "revenue_by_type": revenue_by_type,
            "cash_received_total_cents": cash_received_total_cents
        }
    
    async def get_stock_report(
        self,
        db: AsyncSession,
        sucursal_id: Optional[str] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Get stock report with alerts and turnover metrics.
        
        Args:
            db: Database session
            sucursal_id: Optional sucursal ID to filter by
            use_cache: Whether to use cache (default: True)
            
        Returns:
            Dictionary with stock metrics:
            {
                "low_stock_alerts": list,
                "total_products": int,
                "total_stock_value_cents": int,
                "products_by_category": dict
            }
        """
        # Generate cache key
        cache_key = self.cache._generate_key("stock", sucursal_id)
        
        # Check cache
        if use_cache:
            cached = await self.cache.get(cache_key)
            if cached:
                logger.debug(f"Cache HIT for stock report: {cache_key}")
                return cached
        
        # Build query
        query = select(Product).where(Product.active == True)
        
        if sucursal_id:
            query = query.where(Product.sucursal_id == sucursal_id)
        
        result = await db.execute(query)
        products = result.scalars().all()
        
        # Process products
        low_stock_alerts: List[Dict[str, Any]] = []
        total_stock_value_cents = 0
        products_by_category: Dict[str, int] = {}
        
        for product in products:
            stock_value = product.stock_qty * product.price_cents
            total_stock_value_cents += stock_value
            
            # Check for low stock
            if product.stock_qty <= product.threshold_alert_qty:
                low_stock_alerts.append({
                    "product_id": str(product.id),
                    "product_name": product.name,
                    "stock_qty": product.stock_qty,
                    "threshold_alert_qty": product.threshold_alert_qty,
                    "sucursal_id": str(product.sucursal_id)
                })
        
        # Sort alerts by stock quantity (lowest first)
        low_stock_alerts.sort(key=lambda x: x["stock_qty"])
        
        report = {
            "low_stock_alerts": low_stock_alerts,
            "total_products": len(products),
            "total_stock_value_cents": total_stock_value_cents,
            "alerts_count": len(low_stock_alerts)
        }
        
        # Cache result
        if use_cache:
            await self.cache.set(cache_key, report, ttl=300)  # 5 minutes
        
        logger.info(
            f"Stock report generated: {len(products)} products, "
            f"{len(low_stock_alerts)} low stock alerts"
        )
        
        return report
    
    async def get_services_report(
        self,
        db: AsyncSession,
        sucursal_id: Optional[str] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Get services report with active timers, sales metrics, peak hours, and tickets.
        
        Args:
            db: Database session
            sucursal_id: Optional sucursal ID to filter by
            use_cache: Whether to use cache (default: True)
            
        Returns:
            Dictionary with services metrics:
            {
                "active_timers_count": int,  # For backward compatibility
                "active_timers": int,  # Alias for active_timers_count
                "total_services": int,
                "services_by_sucursal": dict,
                "tickets_generated": int,  # Service sales count for today
                "peak_hours": List[{"hour": int, "sales_count": int}],
                "total_revenue_cents": int,  # Service sales revenue for today
                "sales": {
                    "service_count": int,
                    "package_count": int,
                    "total_count": int
                }
            }
        """
        from uuid import UUID
        from models.sale_item import SaleItem
        from models.package import Package
        # get_service_package_ids already imported at top of file from utils.package_helpers
        
        # Get business date for cache key (considering timezone)
        business_date = await self._get_business_date(db, sucursal_id)
        # Generate cache key
        cache_key = self.cache._generate_key("services_report", sucursal_id, business_date.isoformat())
        
        # Check cache
        if use_cache:
            cached = await self.cache.get(cache_key)
            if cached:
                logger.debug(f"Cache HIT for services report: {cache_key}")
                return cached
        
        # Get active timers
        # Count timers that are truly active (status IN ('active', 'scheduled', 'extended') AND end_at > now)
        # This includes:
        # - 'active': timers that are currently running
        # - 'scheduled': timers waiting for delay period to pass (but already created)
        # - 'extended': timers that have been extended but still running
        # This excludes timers that have expired but still have status='active'
        # This is consistent with TimerService.get_active_timers() logic
        from models.sale import Sale
        now_utc = datetime.now(dt_timezone.utc)
        timer_query = select(Timer).where(
            and_(
                Timer.status.in_(["active", "scheduled", "extended"]),  # Include all active timer states
                Timer.end_at > now_utc  # Only include timers that haven't expired
            )
        )
        sucursal_uuid = None
        
        if sucursal_id:
            try:
                sucursal_uuid = UUID(sucursal_id)
                # Join with Sale to filter by sucursal
                timer_query = timer_query.join(
                    Sale, Timer.sale_id == Sale.id
                ).where(
                    Sale.sucursal_id == sucursal_uuid
                )
            except (ValueError, TypeError):
                logger.warning(f"Invalid sucursal_id format: {sucursal_id}")
                sucursal_uuid = None
        
        timer_result = await db.execute(timer_query)
        active_timers = timer_result.scalars().all()
        active_timers_count = len(active_timers)
        
        # Get total services
        service_query = select(Service).where(Service.active == True)
        
        if sucursal_uuid:
            service_query = service_query.where(Service.sucursal_id == sucursal_uuid)
        
        service_result = await db.execute(service_query)
        services = service_result.scalars().all()
        
        # Count services by sucursal
        services_by_sucursal: Dict[str, int] = {}
        for service in services:
            suc_id = str(service.sucursal_id)
            services_by_sucursal[suc_id] = services_by_sucursal.get(suc_id, 0) + 1
        
        # Get today's service sales metrics (if sucursal_id provided)
        # Use business date considering sucursal timezone
        today = await self._get_business_date(db, sucursal_id)
        start_datetime = datetime.combine(today, datetime.min.time())
        end_datetime = datetime.combine(today, datetime.max.time())
        
        # Get sucursal timezone for hour extraction
        timezone_str = await self._get_sucursal_timezone(db, sucursal_id)
        
        logger.debug(
            f"Services report query: date={today.isoformat()}, "
            f"sucursal_id={sucursal_id}, timezone={timezone_str}, "
            f"range=[{start_datetime.isoformat()}, {end_datetime.isoformat()}]"
        )
        
        service_count = 0
        package_count = 0
        total_revenue_cents = 0
        peak_hours: List[Dict[str, Any]] = []
        
        if sucursal_uuid:
            logger.debug(f"Querying service sales for sucursal_id={sucursal_id}")
            # Query direct service sales for today
            service_sales_query = select(
                func.sum(Sale.total_cents).label("total_revenue"),
                func.count(Sale.id).label("sales_count")
            ).where(
                and_(
                    Sale.tipo == "service",
                    Sale.sucursal_id == sucursal_uuid,
                    Sale.created_at >= start_datetime,
                    Sale.created_at <= end_datetime
                )
            )
            
            service_sales_result = await db.execute(service_sales_query)
            service_sales_row = service_sales_result.one()
            service_revenue_cents = int(service_sales_row.total_revenue or 0)
            service_count = int(service_sales_row.sales_count or 0)
            
            logger.debug(
                f"Service sales query result: count={service_count}, "
                f"revenue_cents={service_revenue_cents}"
            )
            
            # Query service package sales for today
            package_sales_query = select(
                SaleItem.ref_id.label("package_id"),
                Sale.total_cents.label("total_cents")
            ).join(
                Sale, SaleItem.sale_id == Sale.id
            ).where(
                and_(
                    SaleItem.type == "package",
                    Sale.tipo == "package",
                    Sale.sucursal_id == sucursal_uuid,
                    Sale.created_at >= start_datetime,
                    Sale.created_at <= end_datetime
                )
            )
            
            package_sales_result = await db.execute(package_sales_query)
            package_sales_rows = package_sales_result.all()
            
            logger.debug(f"Package sales query returned {len(package_sales_rows)} rows")
            
            package_ids = list(set(row.package_id for row in package_sales_rows))
            package_revenue_cents = 0
            package_count = 0
            
            if package_ids:
                logger.debug(f"Found {len(package_ids)} unique package IDs, checking for service packages")
                packages_query = select(Package).where(Package.id.in_(package_ids))
                packages_result = await db.execute(packages_query)
                packages = packages_result.scalars().all()
                
                service_package_ids = get_service_package_ids(list(packages))
                service_package_ids_set = set(service_package_ids)
                
                for row in package_sales_rows:
                    if row.package_id in service_package_ids_set:
                        package_revenue_cents += int(row.total_cents or 0)
                        package_count += 1
                
                logger.debug(
                    f"Service packages: count={package_count}, "
                    f"revenue_cents={package_revenue_cents}, "
                    f"total_packages_checked={len(package_sales_rows)}"
                )
            
            total_revenue_cents = service_revenue_cents + package_revenue_cents
            tickets_generated = service_count + package_count
            
            logger.debug(
                f"Total service metrics: service_count={service_count}, "
                f"package_count={package_count}, tickets_generated={tickets_generated}, "
                f"total_revenue_cents={total_revenue_cents}"
            )
            
            # Get peak hours for today (extract hour in sucursal timezone)
            service_hour_expr = self._extract_hour_in_timezone(Sale.created_at, timezone_str)
            service_peak_query = select(
                service_hour_expr.label('hour'),
                func.count(Sale.id).label('sales_count')
            ).where(
                and_(
                    Sale.tipo == "service",
                    Sale.sucursal_id == sucursal_uuid,
                    Sale.created_at >= start_datetime,
                    Sale.created_at <= end_datetime
                )
            ).group_by(
                service_hour_expr
            )
            
            service_peak_result = await db.execute(service_peak_query)
            service_peak_rows = service_peak_result.all()
            
            # Package sales by hour (only service packages)
            package_peak_hours: Dict[int, int] = {}
            if package_ids and service_package_ids:
                # Extract hour in sucursal timezone for package sales
                package_hour_expr = self._extract_hour_in_timezone(Sale.created_at, timezone_str)
                package_peak_query = select(
                    package_hour_expr.label('hour'),
                    SaleItem.ref_id.label("package_id")
                ).join(
                    Sale, SaleItem.sale_id == Sale.id
                ).where(
                    and_(
                        SaleItem.type == "package",
                        Sale.tipo == "package",
                        Sale.sucursal_id == sucursal_uuid,
                        Sale.created_at >= start_datetime,
                        Sale.created_at <= end_datetime,
                        SaleItem.ref_id.in_(service_package_ids)
                    )
                )
                
                package_peak_result = await db.execute(package_peak_query)
                package_peak_rows = package_peak_result.all()
                
                for row in package_peak_rows:
                    hour = int(row.hour)
                    package_peak_hours[hour] = package_peak_hours.get(hour, 0) + 1
            
            # Combine peak hours
            peak_hours_dict: Dict[int, int] = {}
            for row in service_peak_rows:
                hour = int(row.hour)
                peak_hours_dict[hour] = peak_hours_dict.get(hour, 0) + int(row.sales_count or 0)
            
            for hour, count in package_peak_hours.items():
                peak_hours_dict[hour] = peak_hours_dict.get(hour, 0) + count
            
            # Convert to list and sort by sales_count descending
            peak_hours = [
                {"hour": hour, "sales_count": count}
                for hour, count in peak_hours_dict.items()
            ]
            peak_hours = sorted(peak_hours, key=lambda x: x["sales_count"], reverse=True)[:5]
            
            logger.debug(
                f"Peak hours calculated: {len(peak_hours)} hours, "
                f"top_hour={peak_hours[0]['hour'] if peak_hours else 'N/A'}"
            )
        else:
            tickets_generated = 0
            logger.debug("No sucursal_id provided, skipping service sales metrics")
        
        report = {
            # Backward compatibility
            "active_timers_count": active_timers_count,
            "active_timers": active_timers_count,  # Alias for frontend
            "total_services": len(services),
            "services_by_sucursal": services_by_sucursal,
            # Additional metrics (only when sucursal_id provided)
            "tickets_generated": tickets_generated,
            "peak_hours": peak_hours,
            "total_revenue_cents": total_revenue_cents,
            "sales": {
                "service_count": service_count,
                "package_count": package_count,
                "total_count": service_count + package_count
            }
        }
        
        # Cache result
        if use_cache:
            await self.cache.set(cache_key, report, ttl=60)  # 1 minute (more dynamic)
        
        logger.info(
            f"Services report generated: sucursal_id={sucursal_id}, "
            f"active_timers={active_timers_count}, "
            f"total_services={len(services)}, "
            f"tickets_generated={tickets_generated}, "
            f"total_revenue_cents={total_revenue_cents}, "
            f"service_count={service_count}, "
            f"package_count={package_count}, "
            f"peak_hours_count={len(peak_hours)}"
        )
        
        if tickets_generated == 0 and sucursal_uuid:
            logger.warning(
                f"No service tickets found for sucursal_id={sucursal_id} "
                f"on date={today.isoformat()}. "
                f"Check if there are sales with tipo='service' or service packages."
            )
        
        return report
    
    async def get_dashboard_summary(
        self,
        db: AsyncSession,
        sucursal_id: Optional[str] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Get complete dashboard summary with all key metrics.
        
        This method loads all reports in parallel for efficiency.
        
        Args:
            db: Database session
            sucursal_id: Optional sucursal ID to filter by
            use_cache: Whether to use cache (default: True)
            
        Returns:
            Dictionary with all metrics combined
        """
        # Load all reports in parallel
        sales_task = self.get_sales_report(
            db=db,
            sucursal_id=sucursal_id,
            use_cache=use_cache
        )
        
        stock_task = self.get_stock_report(
            db=db,
            sucursal_id=sucursal_id,
            use_cache=use_cache
        )
        
        services_task = self.get_services_report(
            db=db,
            sucursal_id=sucursal_id,
            use_cache=use_cache
        )
        
        # Execute in parallel
        sales_report, stock_report, services_report = await asyncio.gather(
            sales_task,
            stock_task,
            services_task
        )
        
        summary = {
            "sales": sales_report,
            "stock": stock_report,
            "services": services_report,
            "generated_at": datetime.utcnow().isoformat()
        }
        
        logger.info("Dashboard summary generated successfully")
        
        return summary
    
    async def get_peak_hours_report(
        self,
        db: AsyncSession,
        sucursal_id: Optional[str] = None,
        target_date: Optional[date] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        days: Optional[int] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Get peak hours report showing busiest hours across a date range.
        
        Args:
            db: Database session
            sucursal_id: Optional sucursal ID to filter by
            target_date: Target date to analyze (defaults to today) - DEPRECATED, use start_date/end_date
            start_date: Optional start date for range analysis
            end_date: Optional end date for range analysis
            days: Optional number of days to look back (overrides start_date/end_date)
            use_cache: Whether to use cache (default: True)
            
        Returns:
            Dictionary with peak hours metrics:
            {
                "date": str (end date or target_date),
                "start_date": str (if range provided),
                "end_date": str (if range provided),
                "sucursal_id": str | None,
                "peak_hours": [
                    {
                        "hour": int,
                        "sales_count": int,
                        "revenue_cents": int
                    }
                ],
                "busiest_hour": {
                    "hour": int,
                    "sales_count": int,
                    "revenue_cents": int
                }
            }
        """
        # Calculate date range if days is provided
        if days is not None:
            from datetime import timedelta
            end_date = date.today()
            start_date = end_date - timedelta(days=days - 1)  # -1 to include today
            target_date = None  # Clear target_date when using range
        
        # Use start_date/end_date if provided, otherwise fall back to target_date
        if start_date and end_date:
            analysis_start = start_date
            analysis_end = end_date
            date_label = f"{start_date.isoformat()} to {end_date.isoformat()}"
        elif target_date:
            analysis_start = target_date
            analysis_end = target_date
            date_label = target_date.isoformat()
        else:
            # Default to today
            analysis_start = date.today()
            analysis_end = date.today()
            date_label = date.today().isoformat()
        
        # Generate cache key
        cache_key = self.cache._generate_key(
            "peak_hours",
            sucursal_id,
            date_label
        )
        
        # Check cache
        if use_cache:
            cached = await self.cache.get(cache_key)
            if cached:
                logger.debug(f"Cache HIT for peak hours report: {cache_key}")
                return cached
        
        # Get sucursal timezone for hour extraction
        timezone_str = await self._get_sucursal_timezone(db, sucursal_id)
        
        # Build query to get sales by hour across the date range
        # Note: We still filter by UTC datetime range, but extract hour in local timezone
        start_datetime = datetime.combine(analysis_start, datetime.min.time())
        end_datetime = datetime.combine(analysis_end, datetime.max.time())
        
        logger.debug(
            f"Querying peak hours for date range: start={analysis_start.isoformat()}, end={analysis_end.isoformat()}, "
            f"sucursal_id={sucursal_id}, timezone={timezone_str}, "
            f"range=[{start_datetime.isoformat()}, {end_datetime.isoformat()}]"
        )
        
        # Extract hour in sucursal timezone
        hour_expr = self._extract_hour_in_timezone(Sale.created_at, timezone_str)
        
        query = select(
            hour_expr.label('hour'),
            func.count(Sale.id).label('sales_count'),
            func.sum(Sale.total_cents).label('revenue_cents')
        ).where(
            and_(
                Sale.created_at >= start_datetime,
                Sale.created_at <= end_datetime
            )
        )
        
        if sucursal_id:
            query = query.where(Sale.sucursal_id == sucursal_id)
        
        query = query.group_by(hour_expr)
        query = query.order_by(func.count(Sale.id).desc())
        
        result = await db.execute(query)
        rows = result.all()
        
        logger.debug(f"Peak hours query returned {len(rows)} hour groups")
        
        # Process results
        peak_hours: List[Dict[str, Any]] = []
        for row in rows:
            peak_hours.append({
                "hour": int(row.hour),
                "sales_count": int(row.sales_count or 0),
                "revenue_cents": int(row.revenue_cents or 0)
            })
        
        # Get busiest hour (first one, already sorted by sales_count desc)
        # Always return a consistent structure, even with empty data
        if not peak_hours:
            busiest_hour = {
                "hour": 0,
                "sales_count": 0,
                "revenue_cents": 0
            }
            top_peak_hours = []
        else:
            busiest_hour = {
                "hour": peak_hours[0]["hour"],
                "sales_count": peak_hours[0]["sales_count"],
                "revenue_cents": peak_hours[0]["revenue_cents"]
            }
            # Take top 5
            top_peak_hours = peak_hours[:5]
        
        # Always return a consistent structure, even with empty data
        report = {
            "date": analysis_end.isoformat(),  # For backward compatibility
            "sucursal_id": sucursal_id,
            "peak_hours": top_peak_hours,
            "busiest_hour": busiest_hour
        }
        
        # Add range info if using date range
        if start_date and end_date and start_date != end_date:
            report["start_date"] = analysis_start.isoformat()
            report["end_date"] = analysis_end.isoformat()
        
        # Cache result
        if use_cache:
            await self.cache.set(cache_key, report, ttl=300)  # 5 minutes
        
        logger.info(
            f"Peak hours report generated: date={analysis_end.isoformat()}, "
            f"start_date={analysis_start.isoformat() if start_date and end_date and start_date != end_date else 'N/A'}, "
            f"sucursal_id={sucursal_id}, "
            f"total_hours={len(peak_hours)}, "
            f"busiest_hour={busiest_hour['hour']}:00 "
            f"with {busiest_hour['sales_count']} sales"
        )
        
        if len(peak_hours) == 0:
            logger.warning(
                f"No peak hours data found for date={target_date.isoformat()}, "
                f"sucursal_id={sucursal_id}. "
                f"Returning empty report structure."
            )
        
        return report
    
    async def get_top_products_report(
        self,
        db: AsyncSession,
        sucursal_id: Optional[str] = None,
        days: int = 7,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Get top products report showing most sold products.
        
        Args:
            db: Database session
            sucursal_id: Optional sucursal ID to filter by
            days: Number of days to look back (default: 7)
            use_cache: Whether to use cache (default: True)
            
        Returns:
            Dictionary with top products metrics:
            {
                "period_days": int,
                "sucursal_id": str | None,
                "top_products": [
                    {
                        "product_id": str,
                        "product_name": str,
                        "quantity_sold": int,
                        "revenue_cents": int
                    }
                ]
            }
        """
        # Generate cache key
        cache_key = self.cache._generate_key(
            "top_products",
            sucursal_id,
            str(days)
        )
        
        # Check cache
        if use_cache:
            cached = await self.cache.get(cache_key)
            if cached:
                logger.debug(f"Cache HIT for top products report: {cache_key}")
                return cached
        
        # Calculate date range using business date (today in sucursal timezone)
        end_date = await self._get_business_date(db, sucursal_id)
        start_date = end_date - timedelta(days=days)
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())
        
        # Build query to get top products from sale_items
        query = select(
            SaleItem.ref_id.label('product_id'),
            Product.name.label('product_name'),
            func.sum(SaleItem.quantity).label('quantity_sold'),
            func.sum(SaleItem.subtotal_cents).label('revenue_cents')
        ).join(
            Sale, SaleItem.sale_id == Sale.id
        ).join(
            Product, SaleItem.ref_id == Product.id
        ).where(
            and_(
                SaleItem.type == 'product',
                Sale.created_at >= start_datetime,
                Sale.created_at <= end_datetime
            )
        )
        
        if sucursal_id:
            query = query.where(Sale.sucursal_id == sucursal_id)
        
        query = query.group_by(SaleItem.ref_id, Product.name)
        query = query.order_by(func.sum(SaleItem.quantity).desc())
        query = query.limit(5)
        
        result = await db.execute(query)
        rows = result.all()
        
        # Process results
        top_products: List[Dict[str, Any]] = []
        for row in rows:
            top_products.append({
                "product_id": str(row.product_id),
                "product_name": row.product_name or "Unknown",
                "quantity_sold": int(row.quantity_sold or 0),
                "revenue_cents": int(row.revenue_cents or 0)
            })
        
        report = {
            "period_days": days,
            "sucursal_id": sucursal_id,
            "top_products": top_products
        }
        
        # Cache result
        if use_cache:
            await self.cache.set(cache_key, report, ttl=300)  # 5 minutes
        
        logger.info(
            f"Top products report generated: {len(top_products)} products "
            f"over {days} days"
        )
        
        return report
    
    async def get_top_services_report(
        self,
        db: AsyncSession,
        sucursal_id: Optional[str] = None,
        days: int = 7,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Get top services report showing most used services.
        
        Args:
            db: Database session
            sucursal_id: Optional sucursal ID to filter by
            days: Number of days to look back (default: 7)
            use_cache: Whether to use cache (default: True)
            
        Returns:
            Dictionary with top services metrics:
            {
                "period_days": int,
                "sucursal_id": str | None,
                "top_services": [
                    {
                        "service_id": str,
                        "service_name": str,
                        "usage_count": int,
                        "avg_duration_minutes": float
                    }
                ]
            }
        """
        # Generate cache key
        cache_key = self.cache._generate_key(
            "top_services",
            sucursal_id,
            str(days)
        )
        
        # Check cache
        if use_cache:
            cached = await self.cache.get(cache_key)
            if cached:
                logger.debug(f"Cache HIT for top services report: {cache_key}")
                return cached
        
        # Calculate date range using business date (today in sucursal timezone)
        end_date = await self._get_business_date(db, sucursal_id)
        start_date = end_date - timedelta(days=days)
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())
        
        # Build query to get top services from sale_items
        query = select(
            SaleItem.ref_id.label('service_id'),
            Service.name.label('service_name'),
            func.count(SaleItem.id).label('usage_count')
        ).join(
            Sale, SaleItem.sale_id == Sale.id
        ).join(
            Service, SaleItem.ref_id == Service.id
        ).where(
            and_(
                SaleItem.type == 'service',
                Sale.created_at >= start_datetime,
                Sale.created_at <= end_datetime
            )
        )
        
        if sucursal_id:
            query = query.where(Sale.sucursal_id == sucursal_id)
        
        query = query.group_by(SaleItem.ref_id, Service.name)
        query = query.order_by(func.count(SaleItem.id).desc())
        query = query.limit(5)
        
        result = await db.execute(query)
        rows = result.all()
        
        # Process results
        top_services: List[Dict[str, Any]] = []
        for row in rows:
            top_services.append({
                "service_id": str(row.service_id),
                "service_name": row.service_name or "Unknown",
                "usage_count": int(row.usage_count or 0),
                "avg_duration_minutes": 0.0  # Placeholder, can be enhanced later
            })
        
        report = {
            "period_days": days,
            "sucursal_id": sucursal_id,
            "top_services": top_services
        }
        
        # Cache result
        if use_cache:
            await self.cache.set(cache_key, report, ttl=300)  # 5 minutes
        
        logger.info(
            f"Top services report generated: {len(top_services)} services "
            f"over {days} days"
        )
        
        return report
    
    async def get_top_customers_report(
        self,
        db: AsyncSession,
        sucursal_id: Optional[str] = None,
        days: int = 7,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Get top customers report showing most frequent child customers.
        
        This report is based on service tickets (timers) where child data is registered.
        
        Args:
            db: Database session
            sucursal_id: Optional sucursal ID to filter by
            days: Number of days to look back (default: 7)
            use_cache: Whether to use cache (default: True)
            
        Returns:
            Dictionary with top customers metrics:
            {
                "period_days": int,
                "sucursal_id": str | None,
                "top_customers": [
                    {
                        "child_name": str,
                        "child_age": int | None,
                        "visit_count": int,
                        "total_revenue_cents": int
                    }
                ]
            }
        """
        # Generate cache key
        cache_key = self.cache._generate_key(
            "top_customers",
            sucursal_id,
            str(days)
        )
        
        # Check cache
        if use_cache:
            cached = await self.cache.get(cache_key)
            if cached:
                logger.debug(f"Cache HIT for top customers report: {cache_key}")
                return cached
        
        # Calculate date range using business date (today in sucursal timezone)
        end_date = await self._get_business_date(db, sucursal_id)
        start_date = end_date - timedelta(days=days)
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())
        
        # Build query to get top customers from timers
        # Group by child_name and child_age to handle same name with different ages
        query = select(
            Timer.child_name,
            Timer.child_age,
            func.count(Timer.id).label('visit_count'),
            func.sum(Sale.total_cents).label('total_revenue_cents')
        ).join(
            Sale, Timer.sale_id == Sale.id
        ).where(
            and_(
                Timer.child_name.isnot(None),
                Timer.child_name != '',
                Sale.created_at >= start_datetime,
                Sale.created_at <= end_datetime
            )
        )
        
        if sucursal_id:
            query = query.where(Sale.sucursal_id == sucursal_id)
        
        query = query.group_by(Timer.child_name, Timer.child_age)
        query = query.order_by(func.count(Timer.id).desc())
        query = query.limit(5)
        
        result = await db.execute(query)
        rows = result.all()
        
        # Process results
        top_customers: List[Dict[str, Any]] = []
        for row in rows:
            top_customers.append({
                "child_name": row.child_name or "Unknown",
                "child_age": int(row.child_age) if row.child_age else None,
                "visit_count": int(row.visit_count or 0),
                "total_revenue_cents": int(row.total_revenue_cents or 0)
            })
        
        report = {
            "period_days": days,
            "sucursal_id": sucursal_id,
            "top_customers": top_customers
        }
        
        # Cache result
        if use_cache:
            await self.cache.set(cache_key, report, ttl=300)  # 5 minutes
        
        logger.info(
            f"Top customers report generated: {len(top_customers)} customers "
            f"over {days} days"
        )
        
        return report

    async def get_top_customers_by_module_report(
        self,
        db: AsyncSession,
        sucursal_id: Optional[str] = None,
        days: int = 7,
        module: Optional[str] = None,  # "recepcion", "kidibar", or None for all
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Get top customers report segmented by module (Recepción vs KidiBar).
        
        Recepción customers: Based on Timer.child_name (service customers)
        KidiBar customers: Based on Sale.payer_name (product customers)
        
        Args:
            db: Database session
            sucursal_id: Optional sucursal ID to filter by
            days: Number of days to look back (default: 7)
            module: Module filter ("recepcion", "kidibar", or None for all)
            use_cache: Whether to use cache (default: True)
            
        Returns:
            Dictionary with top customers by module:
            {
                "period_days": int,
                "sucursal_id": str | None,
                "module": str | None,
                "recepcion": {
                    "top_customers": [
                        {
                            "customer_name": str,
                            "child_age": int | None,
                            "visit_count": int,
                            "total_revenue_cents": int
                        }
                    ]
                },
                "kidibar": {
                    "top_customers": [
                        {
                            "customer_name": str,
                            "visit_count": int,
                            "total_revenue_cents": int
                        }
                    ]
                }
            }
        """
        from uuid import UUID
        
        # Generate cache key
        cache_key = self.cache._generate_key(
            "top_customers_by_module",
            sucursal_id,
            str(days),
            module or "all"
        )
        
        # Check cache
        if use_cache:
            cached = await self.cache.get(cache_key)
            if cached:
                logger.debug(f"Cache HIT for top customers by module report: {cache_key}")
                return cached
        
        # Calculate date range using business date (today in sucursal timezone)
        end_date = await self._get_business_date(db, sucursal_id)
        start_date = end_date - timedelta(days=days)
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())
        
        sucursal_uuid = None
        if sucursal_id:
            try:
                sucursal_uuid = UUID(sucursal_id)
            except (ValueError, TypeError):
                logger.warning(f"Invalid sucursal_id format: {sucursal_id}")
        
        # Get Recepción customers (from Timer)
        recepcion_customers: List[Dict[str, Any]] = []
        if not module or module == "recepcion":
            recepcion_query = select(
                Timer.child_name,
                Timer.child_age,
                func.count(Timer.id).label('visit_count'),
                func.sum(Sale.total_cents).label('total_revenue_cents')
            ).join(
                Sale, Timer.sale_id == Sale.id
            ).where(
                and_(
                    Timer.child_name.isnot(None),
                    Timer.child_name != '',
                    Sale.created_at >= start_datetime,
                    Sale.created_at <= end_datetime
                )
            )
            
            if sucursal_uuid:
                recepcion_query = recepcion_query.where(Sale.sucursal_id == sucursal_uuid)
            
            recepcion_query = recepcion_query.group_by(Timer.child_name, Timer.child_age)
            recepcion_query = recepcion_query.order_by(func.count(Timer.id).desc())
            recepcion_query = recepcion_query.limit(10)
            
            recepcion_result = await db.execute(recepcion_query)
            recepcion_rows = recepcion_result.all()
            
            for row in recepcion_rows:
                recepcion_customers.append({
                    "customer_name": row.child_name or "Unknown",
                    "child_age": int(row.child_age) if row.child_age else None,
                    "visit_count": int(row.visit_count or 0),
                    "total_revenue_cents": int(row.total_revenue_cents or 0)
                })
        
        # Get KidiBar customers (from Sale.payer_name for product sales)
        kidibar_customers: List[Dict[str, Any]] = []
        if not module or module == "kidibar":
            # Query product sales with payer_name
            kidibar_query = select(
                Sale.payer_name,
                func.count(Sale.id).label('visit_count'),
                func.sum(Sale.total_cents).label('total_revenue_cents')
            ).where(
                and_(
                    Sale.tipo == "product",
                    Sale.payer_name.isnot(None),
                    Sale.payer_name != '',
                    Sale.created_at >= start_datetime,
                    Sale.created_at <= end_datetime
                )
            )
            
            if sucursal_uuid:
                kidibar_query = kidibar_query.where(Sale.sucursal_id == sucursal_uuid)
            
            kidibar_query = kidibar_query.group_by(Sale.payer_name)
            kidibar_query = kidibar_query.order_by(func.count(Sale.id).desc())
            kidibar_query = kidibar_query.limit(10)
            
            kidibar_result = await db.execute(kidibar_query)
            kidibar_rows = kidibar_result.all()
            
            for row in kidibar_rows:
                kidibar_customers.append({
                    "customer_name": row.payer_name or "Unknown",
                    "visit_count": int(row.visit_count or 0),
                    "total_revenue_cents": int(row.total_revenue_cents or 0)
                })
            
            # Also include product package sales
            package_query = select(
                SaleItem.ref_id.label("package_id"),
                Sale.payer_name,
                Sale.total_cents.label("total_cents")
            ).join(
                Sale, SaleItem.sale_id == Sale.id
            ).where(
                and_(
                    SaleItem.type == "package",
                    Sale.tipo == "package",
                    Sale.payer_name.isnot(None),
                    Sale.payer_name != '',
                    Sale.created_at >= start_datetime,
                    Sale.created_at <= end_datetime
                )
            )
            
            if sucursal_uuid:
                package_query = package_query.where(Sale.sucursal_id == sucursal_uuid)
            
            package_result = await db.execute(package_query)
            package_rows = package_result.all()
            
            if package_rows:
                package_ids = list(set(row.package_id for row in package_rows))
                packages_query = select(Package).where(Package.id.in_(package_ids))
                packages_result = await db.execute(packages_query)
                packages = packages_result.scalars().all()
                
                product_package_ids = set(get_product_package_ids(list(packages)))
                
                # Aggregate by payer_name for product packages
                package_customers: Dict[str, Dict[str, Any]] = {}
                for row in package_rows:
                    if row.package_id in product_package_ids:
                        payer_name = row.payer_name or "Unknown"
                        if payer_name not in package_customers:
                            package_customers[payer_name] = {
                                "customer_name": payer_name,
                                "visit_count": 0,
                                "total_revenue_cents": 0
                            }
                        package_customers[payer_name]["visit_count"] += 1
                        package_customers[payer_name]["total_revenue_cents"] += int(row.total_cents or 0)
                
                # Merge with existing kidibar customers
                for payer_name, data in package_customers.items():
                    existing = next((c for c in kidibar_customers if c["customer_name"] == payer_name), None)
                    if existing:
                        existing["visit_count"] += data["visit_count"]
                        existing["total_revenue_cents"] += data["total_revenue_cents"]
                    else:
                        kidibar_customers.append(data)
                
                # Re-sort by visit_count
                kidibar_customers.sort(key=lambda x: x["visit_count"], reverse=True)
                kidibar_customers = kidibar_customers[:10]
        
        report = {
            "period_days": days,
            "sucursal_id": sucursal_id,
            "module": module,
            "recepcion": {
                "top_customers": recepcion_customers
            },
            "kidibar": {
                "top_customers": kidibar_customers
            }
        }
        
        # Cache result
        if use_cache:
            await self.cache.set(cache_key, report, ttl=300)  # 5 minutes
        
        logger.info(
            f"Top customers by module report generated: "
            f"{len(recepcion_customers)} recepcion, {len(kidibar_customers)} kidibar "
            f"over {days} days"
        )
        
        return report
    
    async def get_customers_list_paginated(
        self,
        db: AsyncSession,
        sucursal_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        module: Optional[str] = None,  # "recepcion", "kidibar", or None for all
        skip: int = 0,
        limit: int = 25,
        sort_by: str = "revenue",  # "revenue", "visits", "recency"
        order: str = "desc",
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Get paginated list of customers with sorting and filtering.
        
        Args:
            db: Database session
            sucursal_id: Optional sucursal ID to filter by
            start_date: Optional start date
            end_date: Optional end date
            module: Module filter ("recepcion", "kidibar", or None for all)
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            sort_by: Field to sort by ("revenue", "visits", "recency")
            order: Sort order ("asc" or "desc")
            use_cache: Whether to use cache (default: True)
            
        Returns:
            Dictionary with paginated customers list:
            {
                "customers": [
                    {
                        "customer_name": str,
                        "module": str,  # "recepcion" or "kidibar"
                        "child_age": int | None,  # Only for recepcion
                        "visit_count": int,
                        "total_revenue_cents": int,
                        "last_visit_date": str | None,
                        "first_visit_date": str | None
                    }
                ],
                "pagination": {
                    "skip": int,
                    "limit": int,
                    "total": int,
                    "has_more": bool
                }
            }
        """
        from uuid import UUID
        
        # Generate cache key
        cache_key = self.cache._generate_key(
            "customers_list_paginated",
            sucursal_id,
            start_date.isoformat() if start_date else None,
            end_date.isoformat() if end_date else None,
            module or "all",
            str(skip),
            str(limit),
            sort_by,
            order
        )
        
        # Check cache
        if use_cache:
            cached = await self.cache.get(cache_key)
            if cached:
                logger.debug(f"Cache HIT for customers list paginated: {cache_key}")
                return cached
        
        # Default date range: last 30 days if not provided
        if not end_date:
            end_date = await self._get_business_date(db, sucursal_id)
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())
        
        sucursal_uuid = None
        if sucursal_id:
            try:
                sucursal_uuid = UUID(sucursal_id)
            except (ValueError, TypeError):
                logger.warning(f"Invalid sucursal_id format: {sucursal_id}")
        
        all_customers: List[Dict[str, Any]] = []
        
        # Get Recepción customers (from Timer)
        if not module or module == "recepcion":
            recepcion_query = select(
                Timer.child_name,
                Timer.child_age,
                func.count(Timer.id).label('visit_count'),
                func.sum(Sale.total_cents).label('total_revenue_cents'),
                func.max(Sale.created_at).label('last_visit_date'),
                func.min(Sale.created_at).label('first_visit_date')
            ).join(
                Sale, Timer.sale_id == Sale.id
            ).where(
                and_(
                    Timer.child_name.isnot(None),
                    Timer.child_name != '',
                    Sale.created_at >= start_datetime,
                    Sale.created_at <= end_datetime
                )
            )
            
            if sucursal_uuid:
                recepcion_query = recepcion_query.where(Sale.sucursal_id == sucursal_uuid)
            
            recepcion_query = recepcion_query.group_by(Timer.child_name, Timer.child_age)
            
            # Apply sorting
            if sort_by == "revenue":
                order_by_col = func.sum(Sale.total_cents)
            elif sort_by == "visits":
                order_by_col = func.count(Timer.id)
            elif sort_by == "recency":
                order_by_col = func.max(Sale.created_at)
            else:
                order_by_col = func.sum(Sale.total_cents)
            
            if order == "desc":
                recepcion_query = recepcion_query.order_by(order_by_col.desc())
            else:
                recepcion_query = recepcion_query.order_by(order_by_col.asc())
            
            recepcion_result = await db.execute(recepcion_query)
            recepcion_rows = recepcion_result.all()
            
            for row in recepcion_rows:
                all_customers.append({
                    "customer_name": row.child_name or "Unknown",
                    "module": "recepcion",
                    "child_age": int(row.child_age) if row.child_age else None,
                    "visit_count": int(row.visit_count or 0),
                    "total_revenue_cents": int(row.total_revenue_cents or 0),
                    "last_visit_date": row.last_visit_date.isoformat() if row.last_visit_date else None,
                    "first_visit_date": row.first_visit_date.isoformat() if row.first_visit_date else None
                })
        
        # Get KidiBar customers (from Sale.payer_name for product sales)
        if not module or module == "kidibar":
            kidibar_query = select(
                Sale.payer_name,
                func.count(Sale.id).label('visit_count'),
                func.sum(Sale.total_cents).label('total_revenue_cents'),
                func.max(Sale.created_at).label('last_visit_date'),
                func.min(Sale.created_at).label('first_visit_date')
            ).where(
                and_(
                    Sale.tipo == "product",
                    Sale.payer_name.isnot(None),
                    Sale.payer_name != '',
                    Sale.created_at >= start_datetime,
                    Sale.created_at <= end_datetime
                )
            )
            
            if sucursal_uuid:
                kidibar_query = kidibar_query.where(Sale.sucursal_id == sucursal_uuid)
            
            kidibar_query = kidibar_query.group_by(Sale.payer_name)
            
            # Apply sorting
            if sort_by == "revenue":
                order_by_col = func.sum(Sale.total_cents)
            elif sort_by == "visits":
                order_by_col = func.count(Sale.id)
            elif sort_by == "recency":
                order_by_col = func.max(Sale.created_at)
            else:
                order_by_col = func.sum(Sale.total_cents)
            
            if order == "desc":
                kidibar_query = kidibar_query.order_by(order_by_col.desc())
            else:
                kidibar_query = kidibar_query.order_by(order_by_col.asc())
            
            kidibar_result = await db.execute(kidibar_query)
            kidibar_rows = kidibar_result.all()
            
            for row in kidibar_rows:
                all_customers.append({
                    "customer_name": row.payer_name or "Unknown",
                    "module": "kidibar",
                    "child_age": None,
                    "visit_count": int(row.visit_count or 0),
                    "total_revenue_cents": int(row.total_revenue_cents or 0),
                    "last_visit_date": row.last_visit_date.isoformat() if row.last_visit_date else None,
                    "first_visit_date": row.first_visit_date.isoformat() if row.first_visit_date else None
                })
            
            # Also include product package sales
            package_query = select(
                SaleItem.ref_id.label("package_id"),
                Sale.payer_name,
                Sale.total_cents.label("total_cents"),
                Sale.created_at
            ).join(
                Sale, SaleItem.sale_id == Sale.id
            ).where(
                and_(
                    SaleItem.type == "package",
                    Sale.tipo == "package",
                    Sale.payer_name.isnot(None),
                    Sale.payer_name != '',
                    Sale.created_at >= start_datetime,
                    Sale.created_at <= end_datetime
                )
            )
            
            if sucursal_uuid:
                package_query = package_query.where(Sale.sucursal_id == sucursal_uuid)
            
            package_result = await db.execute(package_query)
            package_rows = package_result.all()
            
            if package_rows:
                package_ids = list(set(row.package_id for row in package_rows))
                packages_query = select(Package).where(Package.id.in_(package_ids))
                packages_result = await db.execute(packages_query)
                packages = packages_result.scalars().all()
                
                product_package_ids = set(get_product_package_ids(list(packages)))
                
                # Aggregate by payer_name for product packages
                package_customers: Dict[str, Dict[str, Any]] = {}
                for row in package_rows:
                    if row.package_id in product_package_ids:
                        payer_name = row.payer_name or "Unknown"
                        if payer_name not in package_customers:
                            package_customers[payer_name] = {
                                "customer_name": payer_name,
                                "module": "kidibar",
                                "visit_count": 0,
                                "total_revenue_cents": 0,
                                "last_visit_date": None,
                                "first_visit_date": None,
                                "dates": []
                            }
                        package_customers[payer_name]["visit_count"] += 1
                        package_customers[payer_name]["total_revenue_cents"] += int(row.total_cents or 0)
                        if row.created_at:
                            package_customers[payer_name]["dates"].append(row.created_at)
                
                # Merge with existing kidibar customers
                for payer_name, data in package_customers.items():
                    existing = next((c for c in all_customers if c["customer_name"] == payer_name and c["module"] == "kidibar"), None)
                    if existing:
                        existing["visit_count"] += data["visit_count"]
                        existing["total_revenue_cents"] += data["total_revenue_cents"]
                        if data["dates"]:
                            max_date = max(data["dates"])
                            min_date = min(data["dates"])
                            if not existing["last_visit_date"] or max_date.isoformat() > existing["last_visit_date"]:
                                existing["last_visit_date"] = max_date.isoformat()
                            if not existing["first_visit_date"] or min_date.isoformat() < existing["first_visit_date"]:
                                existing["first_visit_date"] = min_date.isoformat()
                    else:
                        max_date = max(data["dates"]) if data["dates"] else None
                        min_date = min(data["dates"]) if data["dates"] else None
                        all_customers.append({
                            "customer_name": payer_name,
                            "module": "kidibar",
                            "child_age": None,
                            "visit_count": data["visit_count"],
                            "total_revenue_cents": data["total_revenue_cents"],
                            "last_visit_date": max_date.isoformat() if max_date else None,
                            "first_visit_date": min_date.isoformat() if min_date else None
                        })
        
        # Re-sort combined list if needed (since we merged data)
        if sort_by == "revenue":
            all_customers.sort(key=lambda x: x["total_revenue_cents"], reverse=(order == "desc"))
        elif sort_by == "visits":
            all_customers.sort(key=lambda x: x["visit_count"], reverse=(order == "desc"))
        elif sort_by == "recency":
            all_customers.sort(key=lambda x: x["last_visit_date"] or "", reverse=(order == "desc"))
        
        # Apply pagination
        total = len(all_customers)
        has_more = (skip + limit) < total
        paginated_customers = all_customers[skip:skip + limit]
        
        report = {
            "customers": paginated_customers,
            "pagination": {
                "skip": skip,
                "limit": limit,
                "total": total,
                "has_more": has_more
            }
        }
        
        # Cache result
        if use_cache:
            await self.cache.set(cache_key, report, ttl=300)  # 5 minutes
        
        logger.info(
            f"Customers list paginated: {len(paginated_customers)} customers "
            f"(skip={skip}, limit={limit}, total={total})"
        )
        
        return report
    
    async def get_customers_summary(
        self,
        db: AsyncSession,
        sucursal_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Get customers summary with aggregated metrics.
        
        Args:
            db: Database session
            sucursal_id: Optional sucursal ID to filter by
            start_date: Optional start date
            end_date: Optional end date
            use_cache: Whether to use cache (default: True)
            
        Returns:
            Dictionary with customers summary metrics
        """
        from uuid import UUID
        
        # Generate cache key
        cache_key = self.cache._generate_key(
            "customers_summary",
            sucursal_id,
            start_date.isoformat() if start_date else None,
            end_date.isoformat() if end_date else None
        )
        
        # Check cache
        if use_cache:
            cached = await self.cache.get(cache_key)
            if cached:
                logger.debug(f"Cache HIT for customers summary: {cache_key}")
                return cached
        
        # Default date range: last 30 days if not provided
        if not end_date:
            end_date = await self._get_business_date(db, sucursal_id)
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())
        
        sucursal_uuid = None
        if sucursal_id:
            try:
                sucursal_uuid = UUID(sucursal_id)
            except (ValueError, TypeError):
                logger.warning(f"Invalid sucursal_id format: {sucursal_id}")
        
        # Get unique customers count
        recepcion_customers_query = select(
            func.count(func.distinct(Timer.child_name)).label('unique_customers')
        ).join(
            Sale, Timer.sale_id == Sale.id
        ).where(
            and_(
                Timer.child_name.isnot(None),
                Timer.child_name != '',
                Sale.created_at >= start_datetime,
                Sale.created_at <= end_datetime
            )
        )
        
        if sucursal_uuid:
            recepcion_customers_query = recepcion_customers_query.where(Sale.sucursal_id == sucursal_uuid)
        
        recepcion_result = await db.execute(recepcion_customers_query)
        recepcion_unique = recepcion_result.scalar() or 0
        
        kidibar_customers_query = select(
            func.count(func.distinct(Sale.payer_name)).label('unique_customers')
        ).where(
            and_(
                Sale.tipo == "product",
                Sale.payer_name.isnot(None),
                Sale.payer_name != '',
                Sale.created_at >= start_datetime,
                Sale.created_at <= end_datetime
            )
        )
        
        if sucursal_uuid:
            kidibar_customers_query = kidibar_customers_query.where(Sale.sucursal_id == sucursal_uuid)
        
        kidibar_result = await db.execute(kidibar_customers_query)
        kidibar_unique = kidibar_result.scalar() or 0
        
        # Note: Some customers might be in both modules, so total might be less than sum
        # For now, we'll use the sum as an approximation
        total_unique_customers = recepcion_unique + kidibar_unique
        
        # Get new customers (simplified: customers with first visit in period)
        # This is an approximation - for exact calculation, would need to check if customer existed before period
        # For now, we'll use a simpler approach: count distinct customers in period
        # A more accurate implementation would require checking min(created_at) per customer
        recepcion_new = 0  # Placeholder - would require complex subquery to check first visit date
        kidibar_new = 0  # Placeholder - would require complex subquery to check first visit date
        total_new_customers = recepcion_new + kidibar_new
        
        # Get total revenue from customers
        recepcion_revenue_query = select(
            func.sum(Sale.total_cents).label('total_revenue')
        ).join(
            Timer, Timer.sale_id == Sale.id
        ).where(
            and_(
                Timer.child_name.isnot(None),
                Timer.child_name != '',
                Sale.created_at >= start_datetime,
                Sale.created_at <= end_datetime
            )
        )
        
        if sucursal_uuid:
            recepcion_revenue_query = recepcion_revenue_query.where(Sale.sucursal_id == sucursal_uuid)
        
        recepcion_revenue_result = await db.execute(recepcion_revenue_query)
        recepcion_revenue = int(recepcion_revenue_result.scalar() or 0)
        
        kidibar_revenue_query = select(
            func.sum(Sale.total_cents).label('total_revenue')
        ).where(
            and_(
                Sale.tipo == "product",
                Sale.payer_name.isnot(None),
                Sale.payer_name != '',
                Sale.created_at >= start_datetime,
                Sale.created_at <= end_datetime
            )
        )
        
        if sucursal_uuid:
            kidibar_revenue_query = kidibar_revenue_query.where(Sale.sucursal_id == sucursal_uuid)
        
        kidibar_revenue_result = await db.execute(kidibar_revenue_query)
        kidibar_revenue = int(kidibar_revenue_result.scalar() or 0)
        
        total_revenue = recepcion_revenue + kidibar_revenue
        
        # Calculate average revenue per customer
        avg_revenue_per_customer = (
            int(total_revenue / total_unique_customers)
            if total_unique_customers > 0
            else 0
        )
        
        summary = {
            "total_unique_customers": total_unique_customers,
            "recepcion_unique": recepcion_unique,
            "kidibar_unique": kidibar_unique,
            "new_customers": total_new_customers,
            "recepcion_new": recepcion_new,
            "kidibar_new": kidibar_new,
            "total_revenue_cents": total_revenue,
            "recepcion_revenue_cents": recepcion_revenue,
            "kidibar_revenue_cents": kidibar_revenue,
            "avg_revenue_per_customer_cents": avg_revenue_per_customer,
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            }
        }
        
        # Cache result
        if use_cache:
            await self.cache.set(cache_key, summary, ttl=300)  # 5 minutes
        
        logger.info(
            f"Customers summary generated: {total_unique_customers} unique customers, "
            f"{total_new_customers} new customers"
        )
        
        return summary

    async def get_arqueos_report(
        self,
        db: AsyncSession,
        sucursal_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        module: Optional[str] = None,  # "recepcion", "kidibar", or None for all
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Get arqueos (day close) report with metrics and analysis.
        
        Args:
            db: Database session
            sucursal_id: Optional sucursal ID to filter by
            start_date: Optional start date
            end_date: Optional end date
            module: Optional module filter ("recepcion", "kidibar", or None for all)
            use_cache: Whether to use cache (default: True)
            
        Returns:
            Dictionary with arqueos metrics:
            {
                "period": {
                    "start_date": str,
                    "end_date": str
                },
                "total_arqueos": int,
                "total_system_cents": int,
                "total_physical_cents": int,
                "total_difference_cents": int,
                "average_difference_cents": float,
                "perfect_matches": int,
                "discrepancies": int,
                "discrepancy_rate": float,
                "by_sucursal": dict,
                "recent_arqueos": [
                    {
                        "id": str,
                        "date": str,
                        "system_total_cents": int,
                        "physical_count_cents": int,
                        "difference_cents": int,
                        "sucursal_id": str
                    }
                ]
            }
        """
        from uuid import UUID
        from models.day_close import DayClose
        from models.user import User
        
        # Generate cache key (include module in cache key)
        cache_key = self.cache._generate_key(
            "arqueos_report",
            sucursal_id,
            start_date.isoformat() if start_date else None,
            end_date.isoformat() if end_date else None,
            module
        )
        
        # Check cache
        if use_cache:
            cached = await self.cache.get(cache_key)
            if cached:
                logger.debug(f"Cache HIT for arqueos report: {cache_key}")
                return cached
        
        # Default to last 30 days if no dates provided (using business date)
        if not end_date:
            end_date = await self._get_business_date(db, sucursal_id)
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())
        
        # Build query
        query = select(DayClose).where(
            and_(
                DayClose.date >= start_date,
                DayClose.date <= end_date
            )
        )
        
        sucursal_uuid = None
        if sucursal_id:
            try:
                sucursal_uuid = UUID(sucursal_id)
                query = query.where(DayClose.sucursal_id == sucursal_uuid)
            except (ValueError, TypeError):
                logger.warning(f"Invalid sucursal_id format: {sucursal_id}")
        
        # Filter by module if provided
        # Module is determined by the user role who closed the day
        # KidiBar users only close days with product sales
        if module:
            if module == "kidibar":
                # Join with User to filter by role
                query = query.join(User, DayClose.usuario_id == User.id).where(
                    User.role == "kidibar"
                )
            elif module == "recepcion":
                # Recepcion includes all non-kidibar roles
                query = query.join(User, DayClose.usuario_id == User.id).where(
                    User.role != "kidibar"
                )
            else:
                logger.warning(f"Invalid module filter: {module}. Ignoring filter.")
        
        query = query.order_by(DayClose.date.desc())
        
        logger.debug(
            f"Arqueos report query: sucursal_id={sucursal_id}, "
            f"module={module}, "
            f"date_range=[{start_date.isoformat()}, {end_date.isoformat()}]"
        )
        
        result = await db.execute(query)
        arqueos = result.scalars().all()
        
        # Calculate metrics
        total_arqueos = len(arqueos)
        total_system_cents = sum(arqueo.system_total_cents or 0 for arqueo in arqueos)
        total_physical_cents = sum(arqueo.physical_count_cents or 0 for arqueo in arqueos)
        total_difference_cents = sum(arqueo.difference_cents or 0 for arqueo in arqueos)
        
        average_difference_cents = total_difference_cents / total_arqueos if total_arqueos > 0 else 0.0
        
        perfect_matches = sum(1 for arqueo in arqueos if (arqueo.difference_cents or 0) == 0)
        discrepancies = total_arqueos - perfect_matches
        discrepancy_rate = (discrepancies / total_arqueos * 100) if total_arqueos > 0 else 0.0
        
        # Group by sucursal
        by_sucursal: Dict[str, Dict[str, Any]] = {}
        for arqueo in arqueos:
            sucursal_id_str = str(arqueo.sucursal_id)
            if sucursal_id_str not in by_sucursal:
                by_sucursal[sucursal_id_str] = {
                    "count": 0,
                    "total_system_cents": 0,
                    "total_physical_cents": 0,
                    "total_difference_cents": 0,
                    "perfect_matches": 0
                }
            
            by_sucursal[sucursal_id_str]["count"] += 1
            by_sucursal[sucursal_id_str]["total_system_cents"] += arqueo.system_total_cents or 0
            by_sucursal[sucursal_id_str]["total_physical_cents"] += arqueo.physical_count_cents or 0
            by_sucursal[sucursal_id_str]["total_difference_cents"] += arqueo.difference_cents or 0
            if (arqueo.difference_cents or 0) == 0:
                by_sucursal[sucursal_id_str]["perfect_matches"] += 1
        
        # Get recent arqueos (last 10)
        recent_arqueos = []
        for arqueo in arqueos[:10]:
            recent_arqueos.append({
                "id": str(arqueo.id),
                "date": arqueo.date.isoformat(),
                "system_total_cents": arqueo.system_total_cents or 0,
                "physical_count_cents": arqueo.physical_count_cents or 0,
                "difference_cents": arqueo.difference_cents or 0,
                "sucursal_id": str(arqueo.sucursal_id),
                "created_at": arqueo.created_at.isoformat() if arqueo.created_at else None
            })
        
        report = {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "total_arqueos": total_arqueos,
            "total_system_cents": total_system_cents,
            "total_physical_cents": total_physical_cents,
            "total_difference_cents": total_difference_cents,
            "average_difference_cents": round(average_difference_cents, 2),
            "perfect_matches": perfect_matches,
            "discrepancies": discrepancies,
            "discrepancy_rate": round(discrepancy_rate, 2),
            "by_sucursal": by_sucursal,
            "recent_arqueos": recent_arqueos
        }
        
        # Cache result
        if use_cache:
            await self.cache.set(cache_key, report, ttl=300)  # 5 minutes
        
        logger.info(
            f"Arqueos report generated: sucursal_id={sucursal_id}, "
            f"module={module}, "
            f"total_arqueos={total_arqueos}, "
            f"{perfect_matches} perfect matches, {discrepancy_rate:.1f}% discrepancy rate"
        )
        
        return report
    
    async def get_arqueos_timeseries(
        self,
        db: AsyncSession,
        sucursal_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        module: Optional[str] = None,  # "recepcion", "kidibar", or None for all
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Get arqueos time series data aggregated by day.
        
        Args:
            db: Database session
            sucursal_id: Optional sucursal ID to filter by
            start_date: Optional start date (defaults to 30 days ago)
            end_date: Optional end date (defaults to today)
            module: Optional module filter ("recepcion", "kidibar", or None for all)
            use_cache: Whether to use cache (default: True)
            
        Returns:
            Dictionary with time series data:
            {
                "timeseries": [
                    {
                        "date": "YYYY-MM-DD",
                        "system_total_cents": int,
                        "physical_count_cents": int,
                        "difference_cents": int,
                        "arqueos_count": int,
                        "perfect_matches": int,
                        "discrepancies": int
                    },
                    ...
                ],
                "period": {
                    "start_date": str,
                    "end_date": str
                }
            }
        """
        from uuid import UUID
        from models.day_close import DayClose
        from models.user import User
        
        # Generate cache key (include module in cache key)
        cache_key = self.cache._generate_key(
            "arqueos_timeseries",
            sucursal_id,
            start_date.isoformat() if start_date else None,
            end_date.isoformat() if end_date else None,
            module
        )
        
        # Check cache
        if use_cache:
            cached = await self.cache.get(cache_key)
            if cached:
                logger.debug(f"Cache HIT for arqueos timeseries: {cache_key}")
                return cached
        
        # Default to last 30 days if no dates provided
        if not end_date:
            end_date = await self._get_business_date(db, sucursal_id)
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        # Build query to aggregate by day
        query = select(
            DayClose.date.label("arqueo_date"),
            func.sum(DayClose.system_total_cents).label("total_system_cents"),
            func.sum(DayClose.physical_count_cents).label("total_physical_cents"),
            func.sum(DayClose.difference_cents).label("total_difference_cents"),
            func.count(DayClose.id).label("arqueos_count"),
            func.sum(
                case((DayClose.difference_cents == 0, 1), else_=0).cast(Integer)
            ).label("perfect_matches"),
            func.sum(
                case((DayClose.difference_cents != 0, 1), else_=0).cast(Integer)
            ).label("discrepancies")
        ).where(
            and_(
                DayClose.date >= start_date,
                DayClose.date <= end_date
            )
        )
        
        # Filter by sucursal
        sucursal_uuid = None
        if sucursal_id:
            try:
                sucursal_uuid = UUID(sucursal_id)
                query = query.where(DayClose.sucursal_id == sucursal_uuid)
            except (ValueError, TypeError):
                logger.warning(f"Invalid sucursal_id format: {sucursal_id}")
        
        # Filter by module if provided
        if module:
            if module == "kidibar":
                query = query.join(User, DayClose.usuario_id == User.id).where(
                    User.role == "kidibar"
                )
            elif module == "recepcion":
                query = query.join(User, DayClose.usuario_id == User.id).where(
                    User.role != "kidibar"
                )
            else:
                logger.warning(f"Invalid module filter: {module}. Ignoring filter.")
        
        query = query.group_by(DayClose.date).order_by(DayClose.date)
        
        result = await db.execute(query)
        rows = result.all()
        
        # Transform to time series format
        timeseries = []
        for row in rows:
            arqueo_date = row.arqueo_date
            system_total_cents = int(row.total_system_cents or 0)
            physical_count_cents = int(row.total_physical_cents or 0)
            difference_cents = int(row.total_difference_cents or 0)
            arqueos_count = int(row.arqueos_count or 0)
            perfect_matches = int(row.perfect_matches or 0)
            discrepancies = int(row.discrepancies or 0)
            
            timeseries.append({
                "date": arqueo_date.isoformat() if isinstance(arqueo_date, date) else arqueo_date,
                "system_total_cents": system_total_cents,
                "physical_count_cents": physical_count_cents,
                "difference_cents": difference_cents,
                "arqueos_count": arqueos_count,
                "perfect_matches": perfect_matches,
                "discrepancies": discrepancies
            })
        
        # Fill in missing dates with zeros
        current_date = start_date
        filled_timeseries = []
        timeseries_dict = {item["date"]: item for item in timeseries}
        
        while current_date <= end_date:
            date_str = current_date.isoformat()
            if date_str in timeseries_dict:
                filled_timeseries.append(timeseries_dict[date_str])
            else:
                filled_timeseries.append({
                    "date": date_str,
                    "system_total_cents": 0,
                    "physical_count_cents": 0,
                    "difference_cents": 0,
                    "arqueos_count": 0,
                    "perfect_matches": 0,
                    "discrepancies": 0
                })
            current_date += timedelta(days=1)
        
        report = {
            "timeseries": filled_timeseries,
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            }
        }
        
        # Cache result
        if use_cache:
            await self.cache.set(cache_key, report, ttl=300)  # 5 minutes
        
        logger.info(
            f"Arqueos timeseries generated: {len(filled_timeseries)} days, "
            f"module={module}, "
            f"from {start_date.isoformat()} to {end_date.isoformat()}"
        )
        
        return report
    
    async def get_arqueos_heatmap(
        self,
        db: AsyncSession,
        sucursal_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        module: Optional[str] = None,  # "recepcion", "kidibar", or None for all
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Get arqueos heatmap data for calendar visualization.
        
        Returns data organized by date with intensity levels for discrepancies.
        
        Args:
            db: Database session
            sucursal_id: Optional sucursal ID to filter by
            start_date: Optional start date (defaults to 30 days ago)
            end_date: Optional end date (defaults to today)
            module: Optional module filter ("recepcion", "kidibar", or None for all)
            use_cache: Whether to use cache (default: True)
            
        Returns:
            Dictionary with heatmap data:
            {
                "heatmap": [
                    {
                        "date": "YYYY-MM-DD",
                        "difference_cents": int,
                        "discrepancy_rate": float,
                        "intensity": int,  # 0-4: 0=perfect, 1=low, 2=medium, 3=high, 4=critical
                        "arqueos_count": int
                    },
                    ...
                ],
                "period": {
                    "start_date": str,
                    "end_date": str
                },
                "intensity_scale": {
                    "perfect": int,  # difference == 0
                    "low": int,      # 0 < abs(difference) <= threshold1
                    "medium": int,   # threshold1 < abs(difference) <= threshold2
                    "high": int,      # threshold2 < abs(difference) <= threshold3
                    "critical": int   # abs(difference) > threshold3
                }
            }
        """
        from uuid import UUID
        from models.day_close import DayClose
        from models.user import User
        
        # Generate cache key
        cache_key = self.cache._generate_key(
            "arqueos_heatmap",
            sucursal_id,
            start_date.isoformat() if start_date else None,
            end_date.isoformat() if end_date else None,
            module
        )
        
        # Check cache
        if use_cache:
            cached = await self.cache.get(cache_key)
            if cached:
                logger.debug(f"Cache HIT for arqueos heatmap: {cache_key}")
                return cached
        
        # Default to last 90 days for heatmap (better calendar view)
        if not end_date:
            end_date = await self._get_business_date(db, sucursal_id)
        if not start_date:
            start_date = end_date - timedelta(days=90)
        
        # Build query
        query = select(
            DayClose.date.label("arqueo_date"),
            func.sum(DayClose.difference_cents).label("total_difference"),
            func.count(DayClose.id).label("arqueos_count"),
            func.sum(
                case((DayClose.difference_cents == 0, 1), else_=0).cast(Integer)
            ).label("perfect_matches"),
            func.sum(
                case((DayClose.difference_cents != 0, 1), else_=0).cast(Integer)
            ).label("discrepancies")
        ).where(
            and_(
                DayClose.date >= start_date,
                DayClose.date <= end_date
            )
        )
        
        # Filter by sucursal
        if sucursal_id:
            try:
                sucursal_uuid = UUID(sucursal_id)
                query = query.where(DayClose.sucursal_id == sucursal_uuid)
            except (ValueError, TypeError):
                logger.warning(f"Invalid sucursal_id format: {sucursal_id}")
        
        # Filter by module if provided
        if module:
            if module == "kidibar":
                query = query.join(User, DayClose.usuario_id == User.id).where(
                    User.role == "kidibar"
                )
            elif module == "recepcion":
                query = query.join(User, DayClose.usuario_id == User.id).where(
                    User.role != "kidibar"
                )
        
        query = query.group_by(DayClose.date).order_by(DayClose.date)
        
        result = await db.execute(query)
        rows = result.all()
        
        # Calculate thresholds based on data distribution
        differences = [abs(int(row.total_difference or 0)) for row in rows if row.total_difference]
        if differences:
            sorted_diffs = sorted(differences)
            p25 = sorted_diffs[len(sorted_diffs) // 4] if len(sorted_diffs) > 0 else 0
            p50 = sorted_diffs[len(sorted_diffs) // 2] if len(sorted_diffs) > 0 else 0
            p75 = sorted_diffs[3 * len(sorted_diffs) // 4] if len(sorted_diffs) > 0 else 0
            max_diff = max(differences) if differences else 0
            
            threshold_low = max(100, p25)  # At least $1.00
            threshold_medium = max(500, p50)  # At least $5.00
            threshold_high = max(2000, p75)  # At least $20.00
            threshold_critical = max(5000, max_diff * 0.8)  # At least $50.00 or 80% of max
        else:
            threshold_low = 100
            threshold_medium = 500
            threshold_high = 2000
            threshold_critical = 5000
        
        # Transform to heatmap format
        heatmap = []
        intensity_counts = {"perfect": 0, "low": 0, "medium": 0, "high": 0, "critical": 0}
        
        for row in rows:
            arqueo_date = row.arqueo_date
            difference_cents = int(row.total_difference or 0)
            arqueos_count = int(row.arqueos_count or 0)
            discrepancies = int(row.discrepancies or 0)
            
            abs_difference = abs(difference_cents)
            discrepancy_rate = (discrepancies / arqueos_count * 100) if arqueos_count > 0 else 0.0
            
            # Determine intensity level
            if difference_cents == 0:
                intensity = 0  # Perfect
                intensity_counts["perfect"] += 1
            elif abs_difference <= threshold_low:
                intensity = 1  # Low
                intensity_counts["low"] += 1
            elif abs_difference <= threshold_medium:
                intensity = 2  # Medium
                intensity_counts["medium"] += 1
            elif abs_difference <= threshold_high:
                intensity = 3  # High
                intensity_counts["high"] += 1
            else:
                intensity = 4  # Critical
                intensity_counts["critical"] += 1
            
            heatmap.append({
                "date": arqueo_date.isoformat() if isinstance(arqueo_date, date) else arqueo_date,
                "difference_cents": difference_cents,
                "discrepancy_rate": round(discrepancy_rate, 2),
                "intensity": intensity,
                "arqueos_count": arqueos_count
            })
        
        # Fill in missing dates with zero intensity
        current_date = start_date
        filled_heatmap = []
        heatmap_dict = {item["date"]: item for item in heatmap}
        
        while current_date <= end_date:
            date_str = current_date.isoformat()
            if date_str in heatmap_dict:
                filled_heatmap.append(heatmap_dict[date_str])
            else:
                filled_heatmap.append({
                    "date": date_str,
                    "difference_cents": 0,
                    "discrepancy_rate": 0.0,
                    "intensity": 0,
                    "arqueos_count": 0
                })
            current_date += timedelta(days=1)
        
        report = {
            "heatmap": filled_heatmap,
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "intensity_scale": intensity_counts,
            "thresholds": {
                "low": threshold_low,
                "medium": threshold_medium,
                "high": threshold_high,
                "critical": threshold_critical
            }
        }
        
        # Cache result
        if use_cache:
            await self.cache.set(cache_key, report, ttl=300)  # 5 minutes
        
        logger.info(
            f"Arqueos heatmap generated: {len(filled_heatmap)} days, "
            f"module={module}, "
            f"from {start_date.isoformat()} to {end_date.isoformat()}"
        )
        
        return report
    
    async def get_arqueos_variance_analysis(
        self,
        db: AsyncSession,
        sucursal_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        module: Optional[str] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Get variance analysis for arqueos differences.
        
        Returns statistical distribution data for histogram and box plot visualization.
        
        Args:
            db: Database session
            sucursal_id: Optional sucursal ID to filter by
            start_date: Optional start date
            end_date: Optional end date
            module: Optional module filter
            use_cache: Whether to use cache
            
        Returns:
            Dictionary with variance analysis:
            {
                "differences": [int, ...],  # All difference values
                "statistics": {
                    "mean": float,
                    "median": float,
                    "std_dev": float,
                    "min": int,
                    "max": int,
                    "q1": float,  # First quartile
                    "q3": float,  # Third quartile
                    "iqr": float  # Interquartile range
                },
                "distribution": {
                    "perfect": int,  # difference == 0
                    "ranges": [
                        {"min": int, "max": int, "count": int},
                        ...
                    ]
                },
                "period": {
                    "start_date": str,
                    "end_date": str
                }
            }
        """
        from uuid import UUID
        from models.day_close import DayClose
        from models.user import User
        import statistics
        
        # Generate cache key
        cache_key = self.cache._generate_key(
            "arqueos_variance",
            sucursal_id,
            start_date.isoformat() if start_date else None,
            end_date.isoformat() if end_date else None,
            module
        )
        
        # Check cache
        if use_cache:
            cached = await self.cache.get(cache_key)
            if cached:
                logger.debug(f"Cache HIT for arqueos variance: {cache_key}")
                return cached
        
        # Default to last 30 days
        if not end_date:
            end_date = await self._get_business_date(db, sucursal_id)
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        # Build query
        query = select(DayClose.difference_cents).where(
            and_(
                DayClose.date >= start_date,
                DayClose.date <= end_date
            )
        )
        
        # Filter by sucursal
        if sucursal_id:
            try:
                sucursal_uuid = UUID(sucursal_id)
                query = query.where(DayClose.sucursal_id == sucursal_uuid)
            except (ValueError, TypeError):
                logger.warning(f"Invalid sucursal_id format: {sucursal_id}")
        
        # Filter by module if provided
        if module:
            if module == "kidibar":
                query = query.join(User, DayClose.usuario_id == User.id).where(
                    User.role == "kidibar"
                )
            elif module == "recepcion":
                query = query.join(User, DayClose.usuario_id == User.id).where(
                    User.role != "kidibar"
                )
        
        result = await db.execute(query)
        rows = result.all()
        
        # Extract differences
        differences = [int(row.difference_cents or 0) for row in rows]
        
        if not differences:
            return {
                "differences": [],
                "statistics": {
                    "mean": 0.0,
                    "median": 0.0,
                    "std_dev": 0.0,
                    "min": 0,
                    "max": 0,
                    "q1": 0.0,
                    "q3": 0.0,
                    "iqr": 0.0
                },
                "distribution": {
                    "perfect": 0,
                    "ranges": []
                },
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                }
            }
        
        # Calculate statistics
        sorted_diffs = sorted(differences)
        n = len(sorted_diffs)
        
        mean = statistics.mean(differences) if differences else 0.0
        median = statistics.median(differences) if differences else 0.0
        std_dev = statistics.stdev(differences) if len(differences) > 1 else 0.0
        min_val = min(differences)
        max_val = max(differences)
        
        # Calculate quartiles
        q1_idx = n // 4
        q3_idx = 3 * n // 4
        q1 = sorted_diffs[q1_idx] if q1_idx < n else 0.0
        q3 = sorted_diffs[q3_idx] if q3_idx < n else 0.0
        iqr = q3 - q1
        
        # Count perfect matches
        perfect_count = sum(1 for d in differences if d == 0)
        
        # Create distribution ranges for histogram
        abs_differences = [abs(d) for d in differences if d != 0]
        if abs_differences:
            max_abs = max(abs_differences)
            # Create 10 bins
            bin_size = max(100, max_abs // 10)  # At least $1.00 per bin
            ranges = []
            for i in range(10):
                min_range = i * bin_size
                max_range = (i + 1) * bin_size if i < 9 else max_abs + 1
                count = sum(1 for d in abs_differences if min_range <= d < max_range)
                ranges.append({
                    "min": min_range,
                    "max": max_range,
                    "count": count
                })
        else:
            ranges = []
        
        report = {
            "differences": differences,
            "statistics": {
                "mean": round(mean, 2),
                "median": round(median, 2),
                "std_dev": round(std_dev, 2),
                "min": min_val,
                "max": max_val,
                "q1": round(q1, 2),
                "q3": round(q3, 2),
                "iqr": round(iqr, 2)
            },
            "distribution": {
                "perfect": perfect_count,
                "ranges": ranges
            },
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            }
        }
        
        # Cache result
        if use_cache:
            await self.cache.set(cache_key, report, ttl=300)
        
        logger.info(
            f"Arqueos variance analysis generated: {len(differences)} arqueos, "
            f"module={module}, mean={mean:.2f}, std_dev={std_dev:.2f}"
        )
        
        return report
    
    async def get_arqueos_anomalies(
        self,
        db: AsyncSession,
        sucursal_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        module: Optional[str] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Detect anomalies in arqueos differences using IQR method.
        
        Args:
            db: Database session
            sucursal_id: Optional sucursal ID
            start_date: Optional start date
            end_date: Optional end date
            module: Optional module filter
            use_cache: Whether to use cache
            
        Returns:
            Dictionary with anomalies:
            {
                "anomalies": [
                    {
                        "date": str,
                        "difference_cents": int,
                        "system_total_cents": int,
                        "physical_count_cents": int,
                        "severity": str,  # "moderate" or "severe"
                        "z_score": float
                    }
                ],
                "thresholds": {
                    "lower_bound": float,
                    "upper_bound": float,
                    "iqr": float
                },
                "statistics": {
                    "q1": float,
                    "q3": float,
                    "median": float
                },
                "period": {
                    "start_date": str,
                    "end_date": str
                }
            }
        """
        from uuid import UUID
        from models.day_close import DayClose
        from models.user import User
        
        # Get variance analysis first
        variance_data = await self.get_arqueos_variance_analysis(
            db, sucursal_id, start_date, end_date, module, use_cache
        )
        
        if not variance_data or not variance_data["differences"]:
            return {
                "anomalies": [],
                "thresholds": {"lower_bound": 0.0, "upper_bound": 0.0, "iqr": 0.0},
                "statistics": {"q1": 0.0, "q3": 0.0, "median": 0.0},
                "period": variance_data["period"] if variance_data else {"start_date": "", "end_date": ""}
            }
        
        stats = variance_data["statistics"]
        q1 = stats["q1"]
        q3 = stats["q3"]
        iqr = stats["iqr"]
        median = stats["median"]
        std_dev = stats["std_dev"]
        
        # Calculate bounds using IQR method (1.5 * IQR for moderate, 3 * IQR for severe)
        moderate_multiplier = 1.5
        severe_multiplier = 3.0
        
        lower_bound_moderate = q1 - (moderate_multiplier * iqr)
        upper_bound_moderate = q3 + (moderate_multiplier * iqr)
        lower_bound_severe = q1 - (severe_multiplier * iqr)
        upper_bound_severe = q3 + (severe_multiplier * iqr)
        
        # Build query to get full arqueo data
        query = select(
            DayClose.date,
            DayClose.difference_cents,
            DayClose.system_total_cents,
            DayClose.physical_count_cents
        ).where(
            and_(
                DayClose.date >= start_date,
                DayClose.date <= end_date
            )
        )
        
        if sucursal_id:
            try:
                sucursal_uuid = UUID(sucursal_id)
                query = query.where(DayClose.sucursal_id == sucursal_uuid)
            except (ValueError, TypeError):
                pass
        
        if module:
            if module == "kidibar":
                query = query.join(User, DayClose.usuario_id == User.id).where(
                    User.role == "kidibar"
                )
            elif module == "recepcion":
                query = query.join(User, DayClose.usuario_id == User.id).where(
                    User.role != "kidibar"
                )
        
        result = await db.execute(query)
        rows = result.all()
        
        anomalies = []
        for row in rows:
            diff = int(row.difference_cents or 0)
            
            # Calculate z-score
            z_score = (diff - median) / std_dev if std_dev > 0 else 0.0
            
            # Determine if anomaly
            is_severe = diff < lower_bound_severe or diff > upper_bound_severe
            is_moderate = (diff < lower_bound_moderate or diff > upper_bound_moderate) and not is_severe
            
            if is_severe or is_moderate:
                anomalies.append({
                    "date": row.date.isoformat() if isinstance(row.date, date) else row.date,
                    "difference_cents": diff,
                    "system_total_cents": int(row.system_total_cents or 0),
                    "physical_count_cents": int(row.physical_count_cents or 0),
                    "severity": "severe" if is_severe else "moderate",
                    "z_score": round(z_score, 2)
                })
        
        # Sort by absolute difference (most severe first)
        anomalies.sort(key=lambda x: abs(x["difference_cents"]), reverse=True)
        
        return {
            "anomalies": anomalies,
            "thresholds": {
                "lower_bound": round(lower_bound_moderate, 2),
                "upper_bound": round(upper_bound_moderate, 2),
                "iqr": round(iqr, 2)
            },
            "statistics": {
                "q1": q1,
                "q3": q3,
                "median": median
            },
            "period": variance_data["period"]
        }
    
    async def get_arqueos_trends(
        self,
        db: AsyncSession,
        sucursal_id: Optional[str] = None,
        end_date: Optional[date] = None,
        module: Optional[str] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Get temporal trends (MoM, WoW, YoY) for arqueos.
        
        Returns comparison metrics for month-over-month, week-over-week, year-over-year.
        """
        from uuid import UUID
        from models.day_close import DayClose
        from models.user import User
        
        if not end_date:
            end_date = await self._get_business_date(db, sucursal_id)
        
        # Current period (last 30 days)
        current_start = end_date - timedelta(days=30)
        current_data = await self.get_arqueos_report(
            db, sucursal_id, current_start, end_date, module, use_cache
        )
        
        # Previous month (30 days before current)
        prev_start = current_start - timedelta(days=30)
        prev_month_data = await self.get_arqueos_report(
            db, sucursal_id, prev_start, current_start, module, use_cache
        )
        
        # Previous week (7 days before current)
        prev_week_start = end_date - timedelta(days=37)
        prev_week_end = end_date - timedelta(days=7)
        prev_week_data = await self.get_arqueos_report(
            db, sucursal_id, prev_week_start, prev_week_end, module, use_cache
        )
        
        # Previous year (same period last year)
        prev_year_start = current_start - timedelta(days=365)
        prev_year_end = end_date - timedelta(days=365)
        prev_year_data = await self.get_arqueos_report(
            db, sucursal_id, prev_year_start, prev_year_end, module, use_cache
        )
        
        def calculate_change(current: float, previous: float) -> Dict[str, Any]:
            if previous == 0:
                return {"change": 0.0, "percent_change": 0.0, "trend": "stable"}
            change = current - previous
            percent_change = (change / previous) * 100
            if percent_change > 5:
                trend = "improving"
            elif percent_change < -5:
                trend = "worsening"
            else:
                trend = "stable"
            return {
                "change": round(change, 2),
                "percent_change": round(percent_change, 2),
                "trend": trend
            }
        
        current_rate = current_data.get("discrepancy_rate", 0.0) if current_data else 0.0
        prev_month_rate = prev_month_data.get("discrepancy_rate", 0.0) if prev_month_data else 0.0
        prev_week_rate = prev_week_data.get("discrepancy_rate", 0.0) if prev_week_data else 0.0
        prev_year_rate = prev_year_data.get("discrepancy_rate", 0.0) if prev_year_data else 0.0
        
        return {
            "current": {
                "discrepancy_rate": current_rate,
                "perfect_matches": current_data.get("perfect_matches", 0) if current_data else 0,
                "discrepancies": current_data.get("discrepancies", 0) if current_data else 0
            },
            "month_over_month": calculate_change(current_rate, prev_month_rate),
            "week_over_week": calculate_change(current_rate, prev_week_rate),
            "year_over_year": calculate_change(current_rate, prev_year_rate),
            "period": {
                "current_start": current_start.isoformat(),
                "current_end": end_date.isoformat()
            }
        }
    
    async def get_arqueos_by_user(
        self,
        db: AsyncSession,
        sucursal_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        module: Optional[str] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Get arqueos analysis by user (who closes with most discrepancies).
        """
        from uuid import UUID
        from models.day_close import DayClose
        from models.user import User
        
        if not end_date:
            end_date = await self._get_business_date(db, sucursal_id)
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        query = select(
            User.id,
            User.name,
            User.role,
            func.count(DayClose.id).label("arqueos_count"),
            func.sum(
                case((DayClose.difference_cents == 0, 1), else_=0).cast(Integer)
            ).label("perfect_matches"),
            func.sum(
                case((DayClose.difference_cents != 0, 1), else_=0).cast(Integer)
            ).label("discrepancies"),
            func.avg(DayClose.difference_cents).label("avg_difference"),
            func.sum(func.abs(DayClose.difference_cents)).label("total_abs_difference")
        ).join(
            User, DayClose.usuario_id == User.id
        ).where(
            and_(
                DayClose.date >= start_date,
                DayClose.date <= end_date
            )
        )
        
        if sucursal_id:
            try:
                sucursal_uuid = UUID(sucursal_id)
                query = query.where(DayClose.sucursal_id == sucursal_uuid)
            except (ValueError, TypeError):
                pass
        
        if module:
            if module == "kidibar":
                query = query.where(User.role == "kidibar")
            elif module == "recepcion":
                query = query.where(User.role != "kidibar")
        
        query = query.group_by(User.id, User.name, User.role).order_by(
            func.sum(func.abs(DayClose.difference_cents)).desc()
        )
        
        result = await db.execute(query)
        rows = result.all()
        
        users = []
        for row in rows:
            arqueos_count = int(row.arqueos_count or 0)
            perfect_matches = int(row.perfect_matches or 0)
            discrepancies = int(row.discrepancies or 0)
            discrepancy_rate = (discrepancies / arqueos_count * 100) if arqueos_count > 0 else 0.0
            
            users.append({
                "user_id": str(row.id),
                "user_name": row.name or "Unknown",
                "user_role": row.role or "unknown",
                "arqueos_count": arqueos_count,
                "perfect_matches": perfect_matches,
                "discrepancies": discrepancies,
                "discrepancy_rate": round(discrepancy_rate, 2),
                "avg_difference_cents": int(row.avg_difference or 0),
                "total_abs_difference_cents": int(row.total_abs_difference or 0)
            })
        
        return {
            "users": users,
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            }
        }
    
    async def get_arqueos_predictions(
        self,
        db: AsyncSession,
        sucursal_id: Optional[str] = None,
        forecast_days: int = 7,
        module: Optional[str] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Predict future discrepancies based on historical patterns.
        
        Uses moving average and trend analysis similar to sales predictions.
        """
        from uuid import UUID
        from models.day_close import DayClose
        from models.user import User
        
        end_date = await self._get_business_date(db, sucursal_id)
        start_date = end_date - timedelta(days=60)  # Use 60 days for better prediction
        
        # Get historical data
        query = select(
            DayClose.date,
            DayClose.difference_cents,
            func.count(DayClose.id).label("arqueos_count")
        ).where(
            and_(
                DayClose.date >= start_date,
                DayClose.date <= end_date
            )
        )
        
        if sucursal_id:
            try:
                sucursal_uuid = UUID(sucursal_id)
                query = query.where(DayClose.sucursal_id == sucursal_uuid)
            except (ValueError, TypeError):
                pass
        
        if module:
            if module == "kidibar":
                query = query.join(User, DayClose.usuario_id == User.id).where(
                    User.role == "kidibar"
                )
            elif module == "recepcion":
                query = query.join(User, DayClose.usuario_id == User.id).where(
                    User.role != "kidibar"
                )
        
        query = query.group_by(DayClose.date, DayClose.difference_cents).order_by(DayClose.date)
        result = await db.execute(query)
        rows = result.all()
        
        if len(rows) < 7:
            return {
                "forecast": [],
                "confidence": "low",
                "method": "insufficient_data",
                "message": "Se requieren al menos 7 días de datos históricos"
            }
        
        # Calculate average absolute difference
        historical_diffs = [abs(int(row.difference_cents or 0)) for row in rows]
        avg_abs_diff = sum(historical_diffs) / len(historical_diffs) if historical_diffs else 0
        
        # Calculate trend (simple linear regression)
        recent_diffs = historical_diffs[-7:]  # Last 7 days
        older_diffs = historical_diffs[-14:-7] if len(historical_diffs) >= 14 else historical_diffs[:-7]
        
        recent_avg = sum(recent_diffs) / len(recent_diffs) if recent_diffs else avg_abs_diff
        older_avg = sum(older_diffs) / len(older_diffs) if older_diffs else avg_abs_diff
        
        trend_factor = (recent_avg - older_avg) / older_avg if older_avg > 0 else 0
        
        # Generate forecast
        forecast = []
        current_date = end_date + timedelta(days=1)
        
        for i in range(forecast_days):
            # Apply trend with decay (trend becomes less significant over time)
            decay = 1.0 - (i * 0.1)  # Decay 10% per day
            predicted_diff = avg_abs_diff * (1 + trend_factor * decay)
            
            forecast.append({
                "date": current_date.isoformat(),
                "predicted_difference_cents": int(predicted_diff),
                "confidence": "medium" if i < 3 else "low"
            })
            current_date += timedelta(days=1)
        
        confidence = "high" if len(rows) >= 30 else "medium" if len(rows) >= 14 else "low"
        
        return {
            "forecast": forecast,
            "confidence": confidence,
            "method": "moving_average_with_trend",
            "historical_avg": int(avg_abs_diff),
            "trend_factor": round(trend_factor * 100, 2)
        }
    
    async def get_arqueos_alerts(
        self,
        db: AsyncSession,
        sucursal_id: Optional[str] = None,
        module: Optional[str] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Generate intelligent alerts based on dynamic thresholds.
        
        Analyzes recent patterns and sets adaptive thresholds.
        """
        end_date = await self._get_business_date(db, sucursal_id)
        start_date = end_date - timedelta(days=30)
        
        # Get recent arqueos
        recent_data = await self.get_arqueos_report(
            db, sucursal_id, start_date, end_date, module, use_cache
        )
        
        if not recent_data or recent_data.get("total_arqueos", 0) == 0:
            return {
                "alerts": [],
                "thresholds": {},
                "status": "no_data"
            }
        
        # Calculate dynamic thresholds
        discrepancy_rate = recent_data.get("discrepancy_rate", 0.0)
        total_arqueos = recent_data.get("total_arqueos", 0)
        avg_difference = abs(recent_data.get("total_difference_cents", 0) / total_arqueos) if total_arqueos > 0 else 0
        
        # Get variance for threshold calculation
        variance_data = await self.get_arqueos_variance_analysis(
            db, sucursal_id, start_date, end_date, module, use_cache
        )
        
        alerts = []
        
        # Alert 1: High discrepancy rate
        if discrepancy_rate > 20.0:  # More than 20% discrepancies
            alerts.append({
                "type": "high_discrepancy_rate",
                "severity": "high",
                "message": f"Tasa de discrepancias alta: {discrepancy_rate:.1f}%",
                "recommendation": "Revisar procesos de conteo y cierre de caja",
                "value": discrepancy_rate,
                "threshold": 20.0
            })
        elif discrepancy_rate > 10.0:
            alerts.append({
                "type": "moderate_discrepancy_rate",
                "severity": "medium",
                "message": f"Tasa de discrepancias moderada: {discrepancy_rate:.1f}%",
                "recommendation": "Monitorear de cerca los próximos arqueos",
                "value": discrepancy_rate,
                "threshold": 10.0
            })
        
        # Alert 2: Large average difference
        if variance_data and variance_data.get("statistics"):
            std_dev = variance_data["statistics"].get("std_dev", 0)
            mean = abs(variance_data["statistics"].get("mean", 0))
            
            if avg_difference > mean + (2 * std_dev):
                alerts.append({
                    "type": "large_average_difference",
                    "severity": "high",
                    "message": f"Diferencia promedio alta: {avg_difference / 100:.2f}",
                    "recommendation": "Verificar procedimientos de conteo físico",
                    "value": avg_difference,
                    "threshold": mean + (2 * std_dev)
                })
        
        # Alert 3: Declining perfect match rate
        perfect_matches = recent_data.get("perfect_matches", 0)
        perfect_rate = (perfect_matches / total_arqueos * 100) if total_arqueos > 0 else 0
        
        if perfect_rate < 50.0:  # Less than 50% perfect matches
            alerts.append({
                "type": "low_perfect_match_rate",
                "severity": "medium",
                "message": f"Tasa de coincidencias perfectas baja: {perfect_rate:.1f}%",
                "recommendation": "Capacitar al personal en procedimientos de cierre",
                "value": perfect_rate,
                "threshold": 50.0
            })
        
        return {
            "alerts": alerts,
            "thresholds": {
                "discrepancy_rate_warning": 10.0,
                "discrepancy_rate_critical": 20.0,
                "perfect_match_minimum": 50.0
            },
            "status": "active" if alerts else "normal"
        }
    
    async def get_arqueos_recommendations(
        self,
        db: AsyncSession,
        sucursal_id: Optional[str] = None,
        module: Optional[str] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Generate actionable recommendations based on analysis.
        """
        end_date = await self._get_business_date(db, sucursal_id)
        start_date = end_date - timedelta(days=30)
        
        # Get all relevant data
        arqueos_data = await self.get_arqueos_report(db, sucursal_id, start_date, end_date, module, use_cache)
        variance_data = await self.get_arqueos_variance_analysis(db, sucursal_id, start_date, end_date, module, use_cache)
        user_data = await self.get_arqueos_by_user(db, sucursal_id, start_date, end_date, module, use_cache)
        trends_data = await self.get_arqueos_trends(db, sucursal_id, end_date, module, use_cache)
        
        recommendations = []
        
        if not arqueos_data:
            return {
                "recommendations": [{
                    "priority": "info",
                    "title": "Datos insuficientes",
                    "description": "Se requieren más datos para generar recomendaciones",
                    "action": "Continuar monitoreando"
                }],
                "summary": "No hay suficientes datos para análisis"
            }
        
        discrepancy_rate = arqueos_data.get("discrepancy_rate", 0.0)
        perfect_matches = arqueos_data.get("perfect_matches", 0)
        total_arqueos = arqueos_data.get("total_arqueos", 0)
        perfect_rate = (perfect_matches / total_arqueos * 100) if total_arqueos > 0 else 0
        
        # Recommendation 1: Based on discrepancy rate
        if discrepancy_rate > 15.0:
            recommendations.append({
                "priority": "high",
                "title": "Revisar procesos de conteo",
                "description": f"La tasa de discrepancias ({discrepancy_rate:.1f}%) está por encima del umbral recomendado.",
                "action": "Implementar doble conteo y verificación cruzada",
                "impact": "Alto - Mejorará la precisión de los arqueos"
            })
        elif discrepancy_rate > 5.0:
            recommendations.append({
                "priority": "medium",
                "title": "Mejorar precisión de conteo",
                "description": f"La tasa de discrepancias ({discrepancy_rate:.1f}%) puede mejorarse.",
                "action": "Capacitar al personal en técnicas de conteo preciso",
                "impact": "Medio - Reducirá discrepancias menores"
            })
        
        # Recommendation 2: Based on perfect match rate
        if perfect_rate < 60.0:
            recommendations.append({
                "priority": "medium",
                "title": "Aumentar coincidencias perfectas",
                "description": f"Solo {perfect_rate:.1f}% de los arqueos tienen coincidencia perfecta.",
                "action": "Establecer estándares más estrictos y revisión de procedimientos",
                "impact": "Medio - Mejorará la confiabilidad"
            })
        
        # Recommendation 3: Based on user analysis
        if user_data and user_data.get("users"):
            worst_user = user_data["users"][0]  # Already sorted by total_abs_difference
            if worst_user.get("discrepancy_rate", 0) > 20.0:
                recommendations.append({
                    "priority": "high",
                    "title": f"Capacitación para {worst_user.get('user_name', 'usuario')}",
                    "description": f"Este usuario tiene una tasa de discrepancias del {worst_user.get('discrepancy_rate', 0):.1f}%.",
                    "action": "Proporcionar capacitación adicional y supervisión",
                    "impact": "Alto - Mejorará el desempeño individual"
                })
        
        # Recommendation 4: Based on trends
        if trends_data:
            mom_trend = trends_data.get("month_over_month", {})
            if mom_trend.get("trend") == "worsening":
                recommendations.append({
                    "priority": "high",
                    "title": "Tendencia negativa detectada",
                    "description": f"Las discrepancias han aumentado {abs(mom_trend.get('percent_change', 0)):.1f}% respecto al mes anterior.",
                    "action": "Investigar causas raíz y tomar medidas correctivas inmediatas",
                    "impact": "Alto - Revertirá la tendencia negativa"
                })
            elif mom_trend.get("trend") == "improving":
                recommendations.append({
                    "priority": "low",
                    "title": "Mantener buenas prácticas",
                    "description": f"Las discrepancias han mejorado {mom_trend.get('percent_change', 0):.1f}% respecto al mes anterior.",
                    "action": "Continuar con los procedimientos actuales y documentar mejores prácticas",
                    "impact": "Bajo - Mantendrá la mejora continua"
                })
        
        # Recommendation 5: Based on variance
        if variance_data and variance_data.get("statistics"):
            std_dev = variance_data["statistics"].get("std_dev", 0)
            if std_dev > 5000:  # High variance (> $50)
                recommendations.append({
                    "priority": "medium",
                    "title": "Reducir variabilidad",
                    "description": "Hay alta variabilidad en las diferencias, indicando inconsistencia en los procesos.",
                    "action": "Estandarizar procedimientos de conteo y cierre",
                    "impact": "Medio - Aumentará la consistencia"
                })
        
        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2, "info": 3}
        recommendations.sort(key=lambda x: priority_order.get(x.get("priority", "info"), 3))
        
        return {
            "recommendations": recommendations,
            "summary": f"{len([r for r in recommendations if r.get('priority') == 'high'])} recomendaciones de alta prioridad, {len([r for r in recommendations if r.get('priority') == 'medium'])} de prioridad media"
        }
    
    async def get_recepcion_stats(
        self,
        db: AsyncSession,
        sucursal_id: str,
        target_date: Optional[date] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Get reception statistics - ONLY services and service packages.
        
        Reception panel statistics include:
        - Sales of services (direct service sales)
        - Sales of service packages (packages containing only services)
        - Active timers for the sucursal
        - Peak hours for service sales
        - Tickets generated (service sales count)
        
        Excludes:
        - Product sales
        - Product packages
        - Mixed packages (products + services)
        - Inventory information
        
        Args:
            db: Database session
            sucursal_id: Sucursal ID (required)
            target_date: Target date (defaults to today)
            use_cache: Whether to use cache (default: True)
            
        Returns:
            Dictionary with reception statistics:
            {
                "date": str,
                "sucursal_id": str,
                "sales": {
                    "total_revenue_cents": int,
                    "total_count": int,
                    "service_count": int,
                    "package_count": int
                },
                "tickets": {
                    "generated_today": int
                },
                "peak_hours": List[{"hour": int, "sales_count": int}],
                "active_timers": int,
                "generated_at": str
            }
        """
        # Generate cache key
        cache_key = self.cache._generate_key(
            "recepcion_stats",
            sucursal_id,
            target_date.isoformat() if target_date else None
        )
        
        # Check cache
        if use_cache:
            cached = await self.cache.get(cache_key)
            if cached:
                logger.debug(f"Cache HIT for recepcion stats: {cache_key}")
                return cached
        
        # Default to business date (today in sucursal timezone) if no date provided
        if not target_date:
            target_date = await self._get_business_date(db, sucursal_id)
        
        # Get sucursal timezone for hour extraction
        timezone_str = await self._get_sucursal_timezone(db, sucursal_id)
        
        # Convert sucursal_id to UUID
        from uuid import UUID
        try:
            sucursal_uuid = UUID(sucursal_id)
        except (ValueError, TypeError):
            logger.error(f"Invalid sucursal_id format: {sucursal_id}")
            raise ValueError(f"Invalid sucursal_id format: {sucursal_id}")
        
        # Setup date range for the target date
        start_datetime = datetime.combine(target_date, datetime.min.time())
        end_datetime = datetime.combine(target_date, datetime.max.time())
        
        # ===== STEP 1: Query direct service sales =====
        service_sales_query = select(
            func.sum(Sale.total_cents).label("total_revenue"),
            func.count(Sale.id).label("sales_count")
        ).where(
            and_(
                Sale.tipo == "service",
                Sale.sucursal_id == sucursal_uuid,
                Sale.created_at >= start_datetime,
                Sale.created_at <= end_datetime
            )
        )
        
        service_sales_result = await db.execute(service_sales_query)
        service_sales_row = service_sales_result.one()
        service_revenue_cents = int(service_sales_row.total_revenue or 0)
        service_count = int(service_sales_row.sales_count or 0)
        
        # ===== STEP 2: Query package sales and filter service packages =====
        # First, get all package sales for the date/sucursal
        package_sales_query = select(
            SaleItem.ref_id.label("package_id"),
            Sale.total_cents.label("total_cents")
        ).join(
            Sale, SaleItem.sale_id == Sale.id
        ).where(
            and_(
                SaleItem.type == "package",
                Sale.tipo == "package",
                Sale.sucursal_id == sucursal_uuid,
                Sale.created_at >= start_datetime,
                Sale.created_at <= end_datetime
            )
        )
        
        package_sales_result = await db.execute(package_sales_query)
        package_sales_rows = package_sales_result.all()
        
        # Extract unique package IDs
        package_ids = list(set(row.package_id for row in package_sales_rows))
        
        # Load packages from database
        package_revenue_cents = 0
        package_count = 0
        
        if package_ids:
            packages_query = select(Package).where(Package.id.in_(package_ids))
            packages_result = await db.execute(packages_query)
            packages = packages_result.scalars().all()
            
            # Get service package IDs using helper
            service_package_ids = get_service_package_ids(list(packages))
            service_package_ids_set = set(service_package_ids)
            
            # Aggregate revenue and count for service packages only
            for row in package_sales_rows:
                if row.package_id in service_package_ids_set:
                    package_revenue_cents += int(row.total_cents or 0)
                    package_count += 1
        
        # ===== STEP 3: Query active timers =====
        # Count timers that are truly active (status IN ('active', 'scheduled', 'extended') AND end_at > now)
        # This includes:
        # - 'active': timers that are currently running
        # - 'scheduled': timers waiting for delay period to pass (but already created)
        # - 'extended': timers that have been extended but still running
        # This excludes timers that have expired but still have status='active'
        # This is consistent with TimerService.get_active_timers() logic
        now_utc = datetime.now(dt_timezone.utc)
        timer_query = select(func.count(Timer.id)).join(
            Sale, Timer.sale_id == Sale.id
        ).where(
            and_(
                Timer.status.in_(["active", "scheduled", "extended"]),  # Include all active timer states
                Sale.sucursal_id == sucursal_uuid,
                Timer.end_at > now_utc  # Only include timers that haven't expired
            )
        )
        
        timer_result = await db.execute(timer_query)
        active_timers_count = int(timer_result.scalar() or 0)
        
        # ===== STEP 4: Query peak hours for service sales =====
        # Get service sales + service package sales by hour
        # We need to aggregate both service sales and service package sales
        
        # Get sucursal timezone for hour extraction (if not already obtained)
        if 'timezone_str' not in locals():
            timezone_str = await self._get_sucursal_timezone(db, sucursal_id)
        
        # Service sales by hour (extract hour in sucursal timezone)
        service_hour_expr = self._extract_hour_in_timezone(Sale.created_at, timezone_str)
        service_peak_query = select(
            service_hour_expr.label('hour'),
            func.count(Sale.id).label('sales_count')
        ).where(
            and_(
                Sale.tipo == "service",
                Sale.sucursal_id == sucursal_uuid,
                Sale.created_at >= start_datetime,
                Sale.created_at <= end_datetime
            )
        ).group_by(
            service_hour_expr
        )
        
        service_peak_result = await db.execute(service_peak_query)
        service_peak_rows = service_peak_result.all()
        
        # Package sales by hour (only service packages)
        package_peak_hours: Dict[int, int] = {}
        if package_ids and service_package_ids:
            # Get package sales by hour for service packages only (extract hour in sucursal timezone)
            package_peak_hour_expr = self._extract_hour_in_timezone(Sale.created_at, timezone_str)
            package_peak_query = select(
                package_peak_hour_expr.label('hour'),
                SaleItem.ref_id.label("package_id")
            ).join(
                Sale, SaleItem.sale_id == Sale.id
            ).where(
                and_(
                    SaleItem.type == "package",
                    Sale.tipo == "package",
                    Sale.sucursal_id == sucursal_uuid,
                    Sale.created_at >= start_datetime,
                    Sale.created_at <= end_datetime,
                    SaleItem.ref_id.in_(service_package_ids)
                )
            )
            
            package_peak_result = await db.execute(package_peak_query)
            package_peak_rows = package_peak_result.all()
            
            # Count by hour
            for row in package_peak_rows:
                hour = int(row.hour)
                package_peak_hours[hour] = package_peak_hours.get(hour, 0) + 1
        
        # Combine peak hours
        peak_hours_dict: Dict[int, int] = {}
        for row in service_peak_rows:
            hour = int(row.hour)
            peak_hours_dict[hour] = peak_hours_dict.get(hour, 0) + int(row.sales_count or 0)
        
        for hour, count in package_peak_hours.items():
            peak_hours_dict[hour] = peak_hours_dict.get(hour, 0) + count
        
        # Convert to list and sort by hour
        peak_hours = [
            {"hour": hour, "sales_count": count}
            for hour, count in sorted(peak_hours_dict.items())
        ]
        
        # Take top 5 busiest hours
        top_peak_hours = sorted(peak_hours, key=lambda x: x["sales_count"], reverse=True)[:5]
        
        # ===== STEP 5: Combine results =====
        total_revenue_cents = service_revenue_cents + package_revenue_cents
        total_count = service_count + package_count
        
        report = {
            "date": target_date.isoformat(),
            "sucursal_id": sucursal_id,
            "sales": {
                "total_revenue_cents": total_revenue_cents,
                "total_count": total_count,
                "service_count": service_count,
                "package_count": package_count
            },
            "tickets": {
                "generated_today": total_count  # Tickets = service sales + service package sales
            },
            "peak_hours": top_peak_hours,
            "active_timers": active_timers_count,
            "generated_at": datetime.utcnow().isoformat()
        }
        
        # Cache result (60 seconds TTL - dynamic data)
        if use_cache:
            await self.cache.set(cache_key, report, ttl=60)
        
        logger.info(
            f"Reception stats generated for sucursal {sucursal_id}: "
            f"{total_count} sales (${total_revenue_cents/100:.2f}), "
            f"{active_timers_count} active timers"
        )
        
        return report
    
    async def get_kidibar_stats(
        self,
        db: AsyncSession,
        sucursal_id: str,
        target_date: Optional[date] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Get KidiBar statistics - ONLY products and product packages.
        
        KidiBar panel statistics include:
        - Sales of products (direct product sales)
        - Sales of product packages (packages containing only products)
        - Low stock alerts count
        - Peak hours for product sales
        
        Excludes:
        - Service sales
        - Service packages
        - Mixed packages (products + services)
        - Timer information
        
        Args:
            db: Database session
            sucursal_id: Sucursal ID (required)
            target_date: Target date (defaults to today)
            use_cache: Whether to use cache (default: True)
            
        Returns:
            Dictionary with KidiBar statistics:
            {
                "date": str,
                "sucursal_id": str,
                "sales": {
                    "total_revenue_cents": int,
                    "total_count": int,
                    "product_count": int,
                    "package_count": int
                },
                "stock_alerts": {
                    "low_stock_count": int,
                    "low_stock_products": List[Dict[str, Any]]  # List of products with low stock
                },
                "peak_hours": List[{"hour": int, "sales_count": int}],
                "generated_at": str
            }
        """
        # Generate cache key
        cache_key = self.cache._generate_key(
            "kidibar_stats",
            sucursal_id,
            target_date.isoformat() if target_date else None
        )
        
        # Check cache
        if use_cache:
            cached = await self.cache.get(cache_key)
            if cached:
                logger.debug(f"Cache HIT for kidibar stats: {cache_key}")
                return cached
        
        # Default to business date (today in sucursal timezone) if no date provided
        if not target_date:
            target_date = await self._get_business_date(db, sucursal_id)
        
        # Get sucursal timezone for hour extraction
        timezone_str = await self._get_sucursal_timezone(db, sucursal_id)
        
        # Convert sucursal_id to UUID
        from uuid import UUID
        try:
            sucursal_uuid = UUID(sucursal_id)
        except (ValueError, TypeError):
            logger.error(f"Invalid sucursal_id format: {sucursal_id}")
            raise ValueError(f"Invalid sucursal_id format: {sucursal_id}")
        
        # Setup date range for the target date
        start_datetime = datetime.combine(target_date, datetime.min.time())
        end_datetime = datetime.combine(target_date, datetime.max.time())
        
        # ===== STEP 1: Query direct product sales =====
        product_sales_query = select(
            func.sum(Sale.total_cents).label("total_revenue"),
            func.count(Sale.id).label("sales_count")
        ).where(
            and_(
                Sale.tipo == "product",
                Sale.sucursal_id == sucursal_uuid,
                Sale.created_at >= start_datetime,
                Sale.created_at <= end_datetime
            )
        )
        
        product_sales_result = await db.execute(product_sales_query)
        product_sales_row = product_sales_result.one()
        product_revenue_cents = int(product_sales_row.total_revenue or 0)
        product_count = int(product_sales_row.sales_count or 0)
        
        # ===== STEP 2: Query package sales and filter product packages =====
        # First, get all package sales for the date/sucursal
        package_sales_query = select(
            SaleItem.ref_id.label("package_id"),
            Sale.total_cents.label("total_cents")
        ).join(
            Sale, SaleItem.sale_id == Sale.id
        ).where(
            and_(
                SaleItem.type == "package",
                Sale.tipo == "package",
                Sale.sucursal_id == sucursal_uuid,
                Sale.created_at >= start_datetime,
                Sale.created_at <= end_datetime
            )
        )
        
        package_sales_result = await db.execute(package_sales_query)
        package_sales_rows = package_sales_result.all()
        
        # Extract unique package IDs
        package_ids = list(set(row.package_id for row in package_sales_rows))
        
        # Load packages from database
        package_revenue_cents = 0
        package_count = 0
        product_package_ids = []
        
        if package_ids:
            packages_query = select(Package).where(Package.id.in_(package_ids))
            packages_result = await db.execute(packages_query)
            packages = packages_result.scalars().all()
            
            # Get product package IDs using helper
            product_package_ids = get_product_package_ids(list(packages))
            product_package_ids_set = set(product_package_ids)
            
            # Aggregate revenue and count for product packages only
            for row in package_sales_rows:
                if row.package_id in product_package_ids_set:
                    package_revenue_cents += int(row.total_cents or 0)
                    package_count += 1
        
        # ===== STEP 3: Query low stock alerts =====
        # Get both count and list of products with low stock
        low_stock_query = select(Product).where(
            and_(
                Product.sucursal_id == sucursal_uuid,
                Product.active == True,
                Product.stock_qty <= Product.threshold_alert_qty
            )
        ).order_by(Product.stock_qty.asc())  # Order by stock (lowest first)
        
        low_stock_result = await db.execute(low_stock_query)
        low_stock_products = low_stock_result.scalars().all()
        low_stock_count = len(low_stock_products)
        
        # Build list of low stock products
        low_stock_list = [
            {
                "product_id": str(product.id),
                "product_name": product.name,
                "stock_qty": product.stock_qty,
                "threshold_alert_qty": product.threshold_alert_qty,
                "price_cents": product.price_cents
            }
            for product in low_stock_products
        ]
        
        # ===== STEP 4: Query peak hours for product sales =====
        # Get product sales + product package sales by hour
        
        # Get sucursal timezone for hour extraction (if not already obtained)
        if 'timezone_str' not in locals():
            timezone_str = await self._get_sucursal_timezone(db, sucursal_id)
        
        # Product sales by hour (extract hour in sucursal timezone)
        product_hour_expr = self._extract_hour_in_timezone(Sale.created_at, timezone_str)
        product_peak_query = select(
            product_hour_expr.label('hour'),
            func.count(Sale.id).label('sales_count')
        ).where(
            and_(
                Sale.tipo == "product",
                Sale.sucursal_id == sucursal_uuid,
                Sale.created_at >= start_datetime,
                Sale.created_at <= end_datetime
            )
        ).group_by(
            product_hour_expr
        )
        
        product_peak_result = await db.execute(product_peak_query)
        product_peak_rows = product_peak_result.all()
        
        # Package sales by hour (only product packages)
        package_peak_hours: Dict[int, int] = {}
        if package_ids and product_package_ids:
            # Get package sales by hour for product packages only (extract hour in sucursal timezone)
            package_peak_hour_expr = self._extract_hour_in_timezone(Sale.created_at, timezone_str)
            package_peak_query = select(
                package_peak_hour_expr.label('hour'),
                SaleItem.ref_id.label("package_id")
            ).join(
                Sale, SaleItem.sale_id == Sale.id
            ).where(
                and_(
                    SaleItem.type == "package",
                    Sale.tipo == "package",
                    Sale.sucursal_id == sucursal_uuid,
                    Sale.created_at >= start_datetime,
                    Sale.created_at <= end_datetime,
                    SaleItem.ref_id.in_(product_package_ids)
                )
            )
            
            package_peak_result = await db.execute(package_peak_query)
            package_peak_rows = package_peak_result.all()
            
            # Count by hour
            for row in package_peak_rows:
                hour = int(row.hour)
                package_peak_hours[hour] = package_peak_hours.get(hour, 0) + 1
        
        # Combine peak hours
        peak_hours_dict: Dict[int, int] = {}
        for row in product_peak_rows:
            hour = int(row.hour)
            peak_hours_dict[hour] = peak_hours_dict.get(hour, 0) + int(row.sales_count or 0)
        
        for hour, count in package_peak_hours.items():
            peak_hours_dict[hour] = peak_hours_dict.get(hour, 0) + count
        
        # Convert to list and sort by hour
        peak_hours = [
            {"hour": hour, "sales_count": count}
            for hour, count in sorted(peak_hours_dict.items())
        ]
        
        # Take top 5 busiest hours
        top_peak_hours = sorted(peak_hours, key=lambda x: x["sales_count"], reverse=True)[:5]
        
        # ===== STEP 5: Combine results =====
        total_revenue_cents = product_revenue_cents + package_revenue_cents
        total_count = product_count + package_count
        
        report = {
            "date": target_date.isoformat(),
            "sucursal_id": sucursal_id,
            "sales": {
                "total_revenue_cents": total_revenue_cents,
                "total_count": total_count,
                "product_count": product_count,
                "package_count": package_count
            },
            "stock_alerts": {
                "low_stock_count": low_stock_count,
                "low_stock_products": low_stock_list
            },
            "peak_hours": top_peak_hours,
            "generated_at": datetime.utcnow().isoformat()
        }
        
        # Cache result (60 seconds TTL - dynamic data)
        if use_cache:
            await self.cache.set(cache_key, report, ttl=60)
        
        logger.info(
            f"KidiBar stats generated for sucursal {sucursal_id}: "
            f"{total_count} sales (${total_revenue_cents/100:.2f}), "
            f"{low_stock_count} low stock alerts"
        )
        
        return report

    async def get_sales_comparison_report(
        self,
        db: AsyncSession,
        sucursal_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        comparison_type: str = "previous_period",  # "previous_period", "month_over_month", "year_over_year"
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Get sales report with comparison to previous period.
        
        Args:
            db: Database session
            sucursal_id: Optional sucursal ID to filter by
            start_date: Start date of current period
            end_date: End date of current period
            comparison_type: Type of comparison ("previous_period", "month_over_month", "year_over_year")
            use_cache: Whether to use cache (default: True)
            
        Returns:
            Dictionary with current and previous period metrics and comparison:
            {
                "current": {
                    "total_revenue_cents": int,
                    "sales_count": int,
                    "average_transaction_value_cents": int
                },
                "previous": {
                    "total_revenue_cents": int,
                    "sales_count": int,
                    "average_transaction_value_cents": int
                },
                "comparison": {
                    "revenue": {
                        "current": int,
                        "previous": int,
                        "change_percent": float,
                        "change_absolute": int,
                        "trend": "up" | "down" | "stable"
                    },
                    "sales_count": {...},
                    "atv": {...}
                }
            }
        """
        # Get current period report
        current_report = await self.get_sales_report(
            db=db,
            sucursal_id=sucursal_id,
            start_date=start_date,
            end_date=end_date,
            use_cache=use_cache
        )
        
        # Calculate previous period dates (using business date)
        if not start_date or not end_date:
            # Default to last 30 days
            end_date = await self._get_business_date(db, sucursal_id)
            start_date = end_date - timedelta(days=30)
        
        period_days = (end_date - start_date).days + 1
        
        if comparison_type == "month_over_month":
            # Previous month (same day range)
            prev_end = start_date - timedelta(days=1)
            prev_start = prev_end - timedelta(days=period_days - 1)
        elif comparison_type == "year_over_year":
            # Same period last year
            prev_start = start_date.replace(year=start_date.year - 1)
            prev_end = end_date.replace(year=end_date.year - 1)
        else:  # previous_period (default)
            # Previous period (same length, immediately before)
            prev_end = start_date - timedelta(days=1)
            prev_start = prev_end - timedelta(days=period_days - 1)
        
        # Get previous period report
        previous_report = await self.get_sales_report(
            db=db,
            sucursal_id=sucursal_id,
            start_date=prev_start,
            end_date=prev_end,
            use_cache=use_cache
        )
        
        # Calculate comparisons
        def calculate_comparison(current_val: int, previous_val: int) -> Dict[str, Any]:
            change_absolute = current_val - previous_val
            change_percent = (change_absolute / previous_val * 100) if previous_val != 0 else 0.0
            
            if abs(change_percent) < 1.0:
                trend = "stable"
            elif change_percent > 0:
                trend = "up"
            else:
                trend = "down"
            
            return {
                "current": current_val,
                "previous": previous_val,
                "change_percent": round(change_percent, 2),
                "change_absolute": change_absolute,
                "trend": trend
            }
        
        current_revenue = current_report.get("total_revenue_cents", 0)
        previous_revenue = previous_report.get("total_revenue_cents", 0)
        current_count = current_report.get("sales_count", 0)
        previous_count = previous_report.get("sales_count", 0)
        current_atv = current_report.get("average_transaction_value_cents", 0)
        previous_atv = previous_report.get("average_transaction_value_cents", 0)
        
        return {
            "current": {
                "total_revenue_cents": current_revenue,
                "sales_count": current_count,
                "average_transaction_value_cents": current_atv
            },
            "previous": {
                "total_revenue_cents": previous_revenue,
                "sales_count": previous_count,
                "average_transaction_value_cents": previous_atv
            },
            "comparison": {
                "revenue": calculate_comparison(current_revenue, previous_revenue),
                "sales_count": calculate_comparison(current_count, previous_count),
                "atv": calculate_comparison(current_atv, previous_atv)
            },
            "comparison_type": comparison_type,
            "periods": {
                "current": {
                    "start_date": start_date.isoformat() if start_date else None,
                    "end_date": end_date.isoformat() if end_date else None
                },
                "previous": {
                    "start_date": prev_start.isoformat(),
                    "end_date": prev_end.isoformat()
                }
            }
        }

    async def get_module_comparison_report(
        self,
        db: AsyncSession,
        sucursal_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Get comparison report between Recepción and KidiBar modules.
        
        Args:
            db: Database session
            sucursal_id: Optional sucursal ID to filter by
            start_date: Optional start date
            end_date: Optional end date
            use_cache: Whether to use cache (default: True)
            
        Returns:
            Dictionary with module comparison:
            {
                "recepcion": {
                    "revenue_cents": int,
                    "sales_count": int,
                    "atv_cents": int
                },
                "kidibar": {
                    "revenue_cents": int,
                    "sales_count": int,
                    "atv_cents": int
                },
                "total": {
                    "revenue_cents": int,
                    "sales_count": int,
                    "atv_cents": int
                },
                "participation": {
                    "recepcion_percent": float,
                    "kidibar_percent": float
                }
            }
        """
        # Default to business date (today in sucursal timezone) if no dates provided
        if not start_date:
            start_date = await self._get_business_date(db, sucursal_id)
        if not end_date:
            end_date = await self._get_business_date(db, sucursal_id)
        
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())
        
        # Convert sucursal_id to UUID if provided
        from uuid import UUID
        sucursal_uuid = None
        if sucursal_id:
            try:
                sucursal_uuid = UUID(sucursal_id)
            except (ValueError, TypeError):
                logger.error(f"Invalid sucursal_id format: {sucursal_id}")
                raise ValueError(f"Invalid sucursal_id format: {sucursal_id}")
        
        # Determine if we need period-based stats (when dates differ or when we want range)
        # Always use period-based methods when we have a date range (even if single day, for consistency)
        use_period_methods = start_date != end_date or True  # Always use period for consistency
        
        # Get Recepción stats (services + service packages)
        if use_period_methods:
            recepcion_stats = await self._get_recepcion_stats_for_period(
                db=db,
                sucursal_id=sucursal_id,
                start_datetime=start_datetime,
                end_datetime=end_datetime
            )
        else:
            # Fallback to single-day method (only if dates are same and we want single day)
            recepcion_stats = await self.get_recepcion_stats(
                db=db,
                sucursal_id=sucursal_id or "",
                target_date=end_date,
                use_cache=use_cache
            )
        
        # Get KidiBar stats (products + product packages)
        if use_period_methods:
            kidibar_stats = await self._get_kidibar_stats_for_period(
                db=db,
                sucursal_id=sucursal_id,
                start_datetime=start_datetime,
                end_datetime=end_datetime
            )
        else:
            # Fallback to single-day method (only if dates are same and we want single day)
            kidibar_stats = await self.get_kidibar_stats(
                db=db,
                sucursal_id=sucursal_id or "",
                target_date=end_date,
                use_cache=use_cache
            )
        
        recepcion_revenue = recepcion_stats.get("sales", {}).get("total_revenue_cents", 0)
        recepcion_count = recepcion_stats.get("sales", {}).get("total_count", 0)
        recepcion_atv = int(recepcion_revenue / recepcion_count) if recepcion_count > 0 else 0
        
        kidibar_revenue = kidibar_stats.get("sales", {}).get("total_revenue_cents", 0)
        kidibar_count = kidibar_stats.get("sales", {}).get("total_count", 0)
        kidibar_atv = int(kidibar_revenue / kidibar_count) if kidibar_count > 0 else 0
        
        total_revenue = recepcion_revenue + kidibar_revenue
        total_count = recepcion_count + kidibar_count
        total_atv = int(total_revenue / total_count) if total_count > 0 else 0
        
        recepcion_percent = (recepcion_revenue / total_revenue * 100) if total_revenue > 0 else 0.0
        kidibar_percent = (kidibar_revenue / total_revenue * 100) if total_revenue > 0 else 0.0
        
        return {
            "recepcion": {
                "revenue_cents": recepcion_revenue,
                "sales_count": recepcion_count,
                "atv_cents": recepcion_atv
            },
            "kidibar": {
                "revenue_cents": kidibar_revenue,
                "sales_count": kidibar_count,
                "atv_cents": kidibar_atv
            },
            "total": {
                "revenue_cents": total_revenue,
                "sales_count": total_count,
                "atv_cents": total_atv
            },
            "participation": {
                "recepcion_percent": round(recepcion_percent, 2),
                "kidibar_percent": round(kidibar_percent, 2)
            }
        }

    async def _get_recepcion_stats_for_period(
        self,
        db: AsyncSession,
        sucursal_id: Optional[str],
        start_datetime: datetime,
        end_datetime: datetime
    ) -> Dict[str, Any]:
        """Helper method to get Recepción stats for a date range (not just a single day)."""
        from uuid import UUID
        sucursal_uuid = None
        if sucursal_id:
            try:
                sucursal_uuid = UUID(sucursal_id)
            except (ValueError, TypeError):
                raise ValueError(f"Invalid sucursal_id format: {sucursal_id}")
        
        # Query service sales
        service_query = select(
            func.sum(Sale.total_cents).label("total_revenue"),
            func.count(Sale.id).label("sales_count")
        ).where(
            and_(
                Sale.tipo == "service",
                Sale.created_at >= start_datetime,
                Sale.created_at <= end_datetime
            )
        )
        
        if sucursal_uuid:
            service_query = service_query.where(Sale.sucursal_id == sucursal_uuid)
        
        service_result = await db.execute(service_query)
        service_row = service_result.one()
        service_revenue = int(service_row.total_revenue or 0)
        service_count = int(service_row.sales_count or 0)
        
        # Query service package sales
        package_query = select(
            SaleItem.ref_id.label("package_id"),
            Sale.total_cents.label("total_cents")
        ).join(
            Sale, SaleItem.sale_id == Sale.id
        ).where(
            and_(
                SaleItem.type == "package",
                Sale.tipo == "package",
                Sale.created_at >= start_datetime,
                Sale.created_at <= end_datetime
            )
        )
        
        if sucursal_uuid:
            package_query = package_query.where(Sale.sucursal_id == sucursal_uuid)
        
        package_result = await db.execute(package_query)
        package_rows = package_result.all()
        
        package_ids = list(set(row.package_id for row in package_rows))
        package_revenue = 0
        package_count = 0
        
        if package_ids:
            packages_query = select(Package).where(Package.id.in_(package_ids))
            packages_result = await db.execute(packages_query)
            packages = packages_result.scalars().all()
            
            service_package_ids = get_service_package_ids(list(packages))
            service_package_ids_set = set(service_package_ids)
            
            for row in package_rows:
                if row.package_id in service_package_ids_set:
                    package_revenue += int(row.total_cents or 0)
                    package_count += 1
        
        return {
            "sales": {
                "total_revenue_cents": service_revenue + package_revenue,
                "total_count": service_count + package_count,
                "service_count": service_count,
                "package_count": package_count
            }
        }

    async def _get_kidibar_stats_for_period(
        self,
        db: AsyncSession,
        sucursal_id: Optional[str],
        start_datetime: datetime,
        end_datetime: datetime
    ) -> Dict[str, Any]:
        """Helper method to get KidiBar stats for a date range (not just a single day)."""
        from uuid import UUID
        sucursal_uuid = None
        if sucursal_id:
            try:
                sucursal_uuid = UUID(sucursal_id)
            except (ValueError, TypeError):
                raise ValueError(f"Invalid sucursal_id format: {sucursal_id}")
        
        # Query product sales
        product_query = select(
            func.sum(Sale.total_cents).label("total_revenue"),
            func.count(Sale.id).label("sales_count")
        ).where(
            and_(
                Sale.tipo == "product",
                Sale.created_at >= start_datetime,
                Sale.created_at <= end_datetime
            )
        )
        
        if sucursal_uuid:
            product_query = product_query.where(Sale.sucursal_id == sucursal_uuid)
        
        product_result = await db.execute(product_query)
        product_row = product_result.one()
        product_revenue = int(product_row.total_revenue or 0)
        product_count = int(product_row.sales_count or 0)
        
        # Query product package sales
        package_query = select(
            SaleItem.ref_id.label("package_id"),
            Sale.total_cents.label("total_cents")
        ).join(
            Sale, SaleItem.sale_id == Sale.id
        ).where(
            and_(
                SaleItem.type == "package",
                Sale.tipo == "package",
                Sale.created_at >= start_datetime,
                Sale.created_at <= end_datetime
            )
        )
        
        if sucursal_uuid:
            package_query = package_query.where(Sale.sucursal_id == sucursal_uuid)
        
        package_result = await db.execute(package_query)
        package_rows = package_result.all()
        
        package_ids = list(set(row.package_id for row in package_rows))
        package_revenue = 0
        package_count = 0
        
        if package_ids:
            packages_query = select(Package).where(Package.id.in_(package_ids))
            packages_result = await db.execute(packages_query)
            packages = packages_result.scalars().all()
            
            product_package_ids = get_product_package_ids(list(packages))
            product_package_ids_set = set(product_package_ids)
            
            for row in package_rows:
                if row.package_id in product_package_ids_set:
                    package_revenue += int(row.total_cents or 0)
                    package_count += 1
        
        return {
            "sales": {
                "total_revenue_cents": product_revenue + package_revenue,
                "total_count": product_count + package_count,
                "product_count": product_count,
                "package_count": package_count
            }
        }

    async def get_customers_rfm_analysis(
        self,
        db: AsyncSession,
        sucursal_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Get RFM (Recency, Frequency, Monetary) analysis for customers.
        
        RFM Segmentation:
        - Recency: Days since last visit (R)
        - Frequency: Number of visits (F)
        - Monetary: Total revenue (M)
        
        Each metric is scored 1-5, then combined into segments.
        
        Args:
            db: Database session
            sucursal_id: Optional sucursal ID to filter by
            start_date: Optional start date
            end_date: Optional end date
            use_cache: Whether to use cache (default: True)
            
        Returns:
            Dictionary with RFM analysis
        """
        from uuid import UUID
        
        # Generate cache key
        cache_key = self.cache._generate_key(
            "customers_rfm",
            sucursal_id,
            start_date.isoformat() if start_date else None,
            end_date.isoformat() if end_date else None
        )
        
        # Check cache
        if use_cache:
            cached = await self.cache.get(cache_key)
            if cached:
                logger.debug(f"Cache HIT for customers RFM: {cache_key}")
                return cached
        
        # Default date range: last 90 days if not provided
        if not end_date:
            end_date = await self._get_business_date(db, sucursal_id)
        if not start_date:
            start_date = end_date - timedelta(days=90)
        
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())
        # Use UTC for consistent timezone-aware datetime
        today = datetime.now(dt_timezone.utc)
        
        sucursal_uuid = None
        if sucursal_id:
            try:
                sucursal_uuid = UUID(sucursal_id)
            except (ValueError, TypeError):
                logger.warning(f"Invalid sucursal_id format: {sucursal_id}")
        
        # Get all customers with RFM metrics
        customers_rfm: List[Dict[str, Any]] = []
        
        # Recepción customers
        recepcion_query = select(
            Timer.child_name,
            func.count(Timer.id).label('frequency'),
            func.sum(Sale.total_cents).label('monetary'),
            func.max(Sale.created_at).label('last_visit')
        ).join(
            Sale, Timer.sale_id == Sale.id
        ).where(
            and_(
                Timer.child_name.isnot(None),
                Timer.child_name != '',
                Sale.created_at >= start_datetime,
                Sale.created_at <= end_datetime
            )
        )
        
        if sucursal_uuid:
            recepcion_query = recepcion_query.where(Sale.sucursal_id == sucursal_uuid)
        
        recepcion_query = recepcion_query.group_by(Timer.child_name)
        recepcion_result = await db.execute(recepcion_query)
        
        for row in recepcion_result.all():
            last_visit = row.last_visit
            # Normalize last_visit to UTC if it's timezone-aware, otherwise assume UTC
            if last_visit:
                if last_visit.tzinfo is None:
                    # If naive, assume UTC (defensive programming)
                    last_visit_utc = last_visit.replace(tzinfo=dt_timezone.utc)
                else:
                    # If aware, normalize to UTC
                    last_visit_utc = last_visit.astimezone(dt_timezone.utc)
                recency_days = (today - last_visit_utc).days
            else:
                recency_days = 999
            
            frequency = int(row.frequency or 0)
            monetary = int(row.monetary or 0)
            
            customers_rfm.append({
                "customer_name": row.child_name or "Unknown",
                "module": "recepcion",
                "recency_days": recency_days,
                "frequency": frequency,
                "monetary_cents": monetary
            })
        
        # KidiBar customers
        kidibar_query = select(
            Sale.payer_name,
            func.count(Sale.id).label('frequency'),
            func.sum(Sale.total_cents).label('monetary'),
            func.max(Sale.created_at).label('last_visit')
        ).where(
            and_(
                Sale.tipo == "product",
                Sale.payer_name.isnot(None),
                Sale.payer_name != '',
                Sale.created_at >= start_datetime,
                Sale.created_at <= end_datetime
            )
        )
        
        if sucursal_uuid:
            kidibar_query = kidibar_query.where(Sale.sucursal_id == sucursal_uuid)
        
        kidibar_query = kidibar_query.group_by(Sale.payer_name)
        kidibar_result = await db.execute(kidibar_query)
        
        for row in kidibar_result.all():
            last_visit = row.last_visit
            # Normalize last_visit to UTC if it's timezone-aware, otherwise assume UTC
            if last_visit:
                if last_visit.tzinfo is None:
                    # If naive, assume UTC (defensive programming)
                    last_visit_utc = last_visit.replace(tzinfo=dt_timezone.utc)
                else:
                    # If aware, normalize to UTC
                    last_visit_utc = last_visit.astimezone(dt_timezone.utc)
                recency_days = (today - last_visit_utc).days
            else:
                recency_days = 999
            
            frequency = int(row.frequency or 0)
            monetary = int(row.monetary or 0)
            
            customers_rfm.append({
                "customer_name": row.payer_name or "Unknown",
                "module": "kidibar",
                "recency_days": recency_days,
                "frequency": frequency,
                "monetary_cents": monetary
            })
        
        if not customers_rfm:
            return {
                "segments": {},
                "summary": {
                    "total_customers": 0,
                    "segment_counts": {}
                }
            }
        
        try:
            # Calculate RFM scores (1-5 scale)
            recency_values = [c["recency_days"] for c in customers_rfm]
            frequency_values = [c["frequency"] for c in customers_rfm]
            monetary_values = [c["monetary_cents"] for c in customers_rfm]
            
            # Validate that we have valid values
            if not recency_values or not frequency_values or not monetary_values:
                logger.warning("Empty RFM values, returning empty report")
                return {
                    "segments": {},
                    "summary": {
                        "total_customers": len(customers_rfm),
                        "segment_counts": {}
                    }
                }
            
            recency_quintiles = self._calculate_quintiles(recency_values, reverse=True)  # Lower is better
            frequency_quintiles = self._calculate_quintiles(frequency_values, reverse=False)  # Higher is better
            monetary_quintiles = self._calculate_quintiles(monetary_values, reverse=False)  # Higher is better
            
            # Validate quintiles length matches customers length
            if len(recency_quintiles) != len(customers_rfm) or \
               len(frequency_quintiles) != len(customers_rfm) or \
               len(monetary_quintiles) != len(customers_rfm):
                logger.error(f"Quintiles length mismatch: recency={len(recency_quintiles)}, "
                           f"frequency={len(frequency_quintiles)}, monetary={len(monetary_quintiles)}, "
                           f"customers={len(customers_rfm)}")
                raise ValueError("Quintiles calculation failed: length mismatch")
        except Exception as e:
            logger.error(f"Error calculating RFM quintiles: {e}", exc_info=True)
            # Return empty segments but preserve customer count
            return {
                "segments": {},
                "summary": {
                    "total_customers": len(customers_rfm),
                    "segment_counts": {},
                    "error": str(e)
                }
            }
        
        # Assign scores and segments
        segments: Dict[str, List[Dict[str, Any]]] = {
            "champions": [],
            "loyal_customers": [],
            "potential_loyalists": [],
            "new_customers": [],
            "promising": [],
            "need_attention": [],
            "about_to_sleep": [],
            "at_risk": [],
            "cannot_lose": [],
            "hibernating": [],
            "lost": []
        }
        
        for i, customer in enumerate(customers_rfm):
            r_score = recency_quintiles[i]
            f_score = frequency_quintiles[i]
            m_score = monetary_quintiles[i]
            
            customer["r_score"] = r_score
            customer["f_score"] = f_score
            customer["m_score"] = m_score
            customer["rfm_score"] = f"{r_score}{f_score}{m_score}"
            
            # Segment assignment
            if r_score == 5 and f_score == 5 and m_score == 5:
                segments["champions"].append(customer)
            elif r_score >= 4 and f_score >= 4 and m_score >= 3:
                segments["loyal_customers"].append(customer)
            elif r_score >= 3 and f_score >= 3 and m_score <= 3:
                segments["potential_loyalists"].append(customer)
            elif r_score == 5 and f_score <= 2 and m_score <= 2:
                segments["new_customers"].append(customer)
            elif r_score >= 3 and r_score <= 4 and f_score <= 2 and m_score <= 2:
                segments["promising"].append(customer)
            elif r_score >= 3 and r_score <= 4 and f_score >= 3 and f_score <= 4 and m_score >= 2 and m_score <= 3:
                segments["need_attention"].append(customer)
            elif r_score >= 2 and r_score <= 3 and f_score >= 2 and f_score <= 3 and m_score >= 2 and m_score <= 3:
                segments["about_to_sleep"].append(customer)
            elif r_score <= 2 and f_score >= 3 and m_score >= 3:
                if f_score >= 4 and m_score >= 4:
                    segments["cannot_lose"].append(customer)
                else:
                    segments["at_risk"].append(customer)
            elif r_score <= 2 and f_score <= 2 and m_score <= 2:
                segments["hibernating"].append(customer)
            else:
                segments["lost"].append(customer)
        
        segment_counts = {segment: len(customers) for segment, customers in segments.items()}
        
        report = {
            "segments": segments,
            "summary": {
                "total_customers": len(customers_rfm),
                "segment_counts": segment_counts
            }
        }
        
        # Cache result
        if use_cache:
            await self.cache.set(cache_key, report, ttl=600)  # 10 minutes
        
        logger.info(f"RFM analysis generated: {len(customers_rfm)} customers segmented")
        
        return report
    
    def _calculate_quintiles(self, values: List[float], reverse: bool = False) -> List[int]:
        """Calculate quintile scores (1-5) for a list of values."""
        if not values:
            return []
        
        sorted_values = sorted(values, reverse=reverse)
        n = len(sorted_values)
        
        if n == 0:
            return []
        
        # Define quintile thresholds
        quintile_size = n / 5
        thresholds = []
        for i in range(1, 6):
            idx = int(quintile_size * i)
            if idx >= n:
                thresholds.append(sorted_values[-1])
            else:
                thresholds.append(sorted_values[idx])
        
        # Assign scores
        scores = []
        for value in values:
            if reverse:
                # For recency: lower is better
                if value <= thresholds[0]:
                    scores.append(5)
                elif value <= thresholds[1]:
                    scores.append(4)
                elif value <= thresholds[2]:
                    scores.append(3)
                elif value <= thresholds[3]:
                    scores.append(2)
                else:
                    scores.append(1)
            else:
                # For frequency/monetary: higher is better
                if value >= thresholds[4]:
                    scores.append(5)
                elif value >= thresholds[3]:
                    scores.append(4)
                elif value >= thresholds[2]:
                    scores.append(3)
                elif value >= thresholds[1]:
                    scores.append(2)
                else:
                    scores.append(1)
        
        return scores
    
    async def get_customers_cohort_analysis(
        self,
        db: AsyncSession,
        sucursal_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        cohort_type: str = "monthly",
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Get cohort analysis for customers.
        
        Groups customers by their first visit (cohort) and tracks retention over time.
        
        Args:
            db: Database session
            sucursal_id: Optional sucursal ID to filter by
            start_date: Optional start date
            end_date: Optional end date
            cohort_type: Type of cohort grouping ("monthly", "weekly", "daily")
            use_cache: Whether to use cache (default: True)
            
        Returns:
            Dictionary with cohort analysis
        """
        from uuid import UUID
        
        # Generate cache key
        cache_key = self.cache._generate_key(
            "customers_cohort",
            sucursal_id,
            start_date.isoformat() if start_date else None,
            end_date.isoformat() if end_date else None,
            cohort_type
        )
        
        # Check cache
        if use_cache:
            cached = await self.cache.get(cache_key)
            if cached:
                logger.debug(f"Cache HIT for customers cohort: {cache_key}")
                return cached
        
        # Default date range based on cohort type
        if not end_date:
            end_date = await self._get_business_date(db, sucursal_id)
        if not start_date:
            if cohort_type == "monthly":
                start_date = end_date - timedelta(days=365)
            elif cohort_type == "weekly":
                start_date = end_date - timedelta(days=90)
            else:
                start_date = end_date - timedelta(days=30)
        
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())
        
        sucursal_uuid = None
        if sucursal_id:
            try:
                sucursal_uuid = UUID(sucursal_id)
            except (ValueError, TypeError):
                logger.warning(f"Invalid sucursal_id format: {sucursal_id}")
        
        # Get first visit dates for all customers
        customers_first_visit: Dict[str, datetime] = {}
        
        # Recepción customers
        recepcion_query = select(
            Timer.child_name,
            func.min(Sale.created_at).label('first_visit')
        ).join(
            Sale, Timer.sale_id == Sale.id
        ).where(
            and_(
                Timer.child_name.isnot(None),
                Timer.child_name != '',
                Sale.created_at >= start_datetime,
                Sale.created_at <= end_datetime
            )
        )
        
        if sucursal_uuid:
            recepcion_query = recepcion_query.where(Sale.sucursal_id == sucursal_uuid)
        
        recepcion_query = recepcion_query.group_by(Timer.child_name)
        recepcion_result = await db.execute(recepcion_query)
        
        for row in recepcion_result.all():
            customer_key = f"recepcion_{row.child_name}"
            if row.first_visit:
                customers_first_visit[customer_key] = row.first_visit
        
        # KidiBar customers
        kidibar_query = select(
            Sale.payer_name,
            func.min(Sale.created_at).label('first_visit')
        ).where(
            and_(
                Sale.tipo == "product",
                Sale.payer_name.isnot(None),
                Sale.payer_name != '',
                Sale.created_at >= start_datetime,
                Sale.created_at <= end_datetime
            )
        )
        
        if sucursal_uuid:
            kidibar_query = kidibar_query.where(Sale.sucursal_id == sucursal_uuid)
        
        kidibar_query = kidibar_query.group_by(Sale.payer_name)
        kidibar_result = await db.execute(kidibar_query)
        
        for row in kidibar_result.all():
            customer_key = f"kidibar_{row.payer_name}"
            if row.first_visit:
                customers_first_visit[customer_key] = row.first_visit
        
        if not customers_first_visit:
            return {
                "cohorts": [],
                "summary": {
                    "total_cohorts": 0,
                    "average_retention": 0.0
                }
            }
        
        # Group customers by cohort period
        cohort_groups: Dict[str, List[str]] = {}
        
        for customer_key, first_visit in customers_first_visit.items():
            if cohort_type == "monthly":
                cohort_period = first_visit.strftime("%Y-%m")
            elif cohort_type == "weekly":
                week_start = first_visit - timedelta(days=first_visit.weekday())
                cohort_period = week_start.strftime("%Y-W%U")
            else:  # daily
                cohort_period = first_visit.strftime("%Y-%m-%d")
            
            if cohort_period not in cohort_groups:
                cohort_groups[cohort_period] = []
            cohort_groups[cohort_period].append(customer_key)
        
        # Build cohort analysis (simplified - tracks cohort size over time)
        cohorts = []
        
        for cohort_period in sorted(cohort_groups.keys()):
            cohort_customers = cohort_groups[cohort_period]
            cohort_size = len(cohort_customers)
            
            cohorts.append({
                "cohort_period": cohort_period,
                "cohort_size": cohort_size,
                "periods": []  # Simplified - would need additional queries for full retention tracking
            })
        
        report = {
            "cohorts": cohorts,
            "summary": {
                "total_cohorts": len(cohorts),
                "average_retention": 0.0  # Would calculate from periods data
            }
        }
        
        # Cache result
        if use_cache:
            await self.cache.set(cache_key, report, ttl=600)  # 10 minutes
        
        logger.info(f"Cohort analysis generated: {len(cohorts)} cohorts")
        
        return report
    
    async def get_customers_trends_analysis(
        self,
        db: AsyncSession,
        sucursal_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Get comprehensive trends analysis combining RFM, Cohort, and behavioral metrics.
        
        This method provides advanced insights including:
        - Retention trends over time
        - Churn prediction indicators
        - Segment behavior analysis
        - Advanced temporal comparisons
        
        Args:
            db: Database session
            sucursal_id: Optional sucursal ID to filter by
            start_date: Optional start date
            end_date: Optional end date
            use_cache: Whether to use cache (default: True)
            
        Returns:
            Dictionary with trends analysis:
            {
                "retention_trends": {
                    "periods": [...],
                    "retention_rates": [...],
                    "trend": "increasing" | "decreasing" | "stable"
                },
                "churn_indicators": {
                    "at_risk_count": int,
                    "hibernating_count": int,
                    "lost_count": int,
                    "churn_probability": float
                },
                "segment_behavior": {
                    "segment": {
                        "trend": str,
                        "growth_rate": float,
                        "customer_count": int
                    }
                },
                "temporal_comparisons": {
                    "current_period": {...},
                    "previous_period": {...},
                    "changes": {...}
                }
            }
        """
        from uuid import UUID
        
        # Generate cache key
        cache_key = self.cache._generate_key(
            "customers_trends",
            sucursal_id,
            start_date.isoformat() if start_date else None,
            end_date.isoformat() if end_date else None
        )
        
        # Check cache
        if use_cache:
            cached = await self.cache.get(cache_key)
            if cached:
                logger.debug(f"Cache HIT for customers trends: {cache_key}")
                return cached
        
        # Default date range: last 90 days if not provided
        if not end_date:
            end_date = await self._get_business_date(db, sucursal_id)
        if not start_date:
            start_date = end_date - timedelta(days=90)
        
        # Get RFM analysis for current period
        rfm_analysis = await self.get_customers_rfm_analysis(
            db=db,
            sucursal_id=sucursal_id,
            start_date=start_date,
            end_date=end_date,
            use_cache=use_cache
        )
        
        # Get cohort analysis
        cohort_analysis = await self.get_customers_cohort_analysis(
            db=db,
            sucursal_id=sucursal_id,
            start_date=start_date,
            end_date=end_date,
            cohort_type="monthly",
            use_cache=use_cache
        )
        
        # Get customers summary for additional metrics
        customers_summary = await self.get_customers_summary(
            db=db,
            sucursal_id=sucursal_id,
            start_date=start_date,
            end_date=end_date,
            use_cache=use_cache
        )
        
        # Calculate churn indicators from RFM
        churn_indicators = {
            "at_risk_count": len(rfm_analysis.get("segments", {}).get("at_risk", [])),
            "hibernating_count": len(rfm_analysis.get("segments", {}).get("hibernating", [])),
            "lost_count": len(rfm_analysis.get("segments", {}).get("lost", [])),
            "cannot_lose_count": len(rfm_analysis.get("segments", {}).get("cannot_lose", []))
        }
        
        total_customers = rfm_analysis.get("summary", {}).get("total_customers", 0)
        churn_risk_total = (
            churn_indicators["at_risk_count"] +
            churn_indicators["hibernating_count"] +
            churn_indicators["lost_count"]
        )
        churn_probability = (
            (churn_risk_total / total_customers * 100) if total_customers > 0 else 0.0
        )
        churn_indicators["churn_probability"] = round(churn_probability, 2)
        
        # Calculate segment behavior trends
        segment_behavior = {}
        segment_counts = rfm_analysis.get("summary", {}).get("segment_counts", {})
        
        for segment, count in segment_counts.items():
            if count > 0:
                # Calculate growth rate (simplified - would need historical data for real trend)
                segment_behavior[segment] = {
                    "customer_count": count,
                    "percentage": round((count / total_customers * 100) if total_customers > 0 else 0.0, 2),
                    "trend": "stable",  # Would calculate from historical data
                    "growth_rate": 0.0  # Would calculate from historical data
                }
        
        # Calculate retention trends (simplified - would need time series data)
        retention_trends = {
            "periods": [],
            "retention_rates": [],
            "trend": "stable",
            "average_retention": cohort_analysis.get("summary", {}).get("average_retention", 0.0)
        }
        
        # Temporal comparisons (current vs previous period)
        previous_start = start_date - timedelta(days=(end_date - start_date).days)
        previous_end = start_date - timedelta(days=1)
        
        try:
            previous_rfm = await self.get_customers_rfm_analysis(
                db=db,
                sucursal_id=sucursal_id,
                start_date=previous_start,
                end_date=previous_end,
                use_cache=use_cache
            )
            
            current_total = rfm_analysis.get("summary", {}).get("total_customers", 0)
            previous_total = previous_rfm.get("summary", {}).get("total_customers", 0)
            
            customer_growth = current_total - previous_total
            customer_growth_rate = (
                ((current_total - previous_total) / previous_total * 100)
                if previous_total > 0 else 0.0
            )
            
            temporal_comparisons = {
                "current_period": {
                    "total_customers": current_total,
                    "champions": len(rfm_analysis.get("segments", {}).get("champions", [])),
                    "at_risk": churn_indicators["at_risk_count"]
                },
                "previous_period": {
                    "total_customers": previous_total,
                    "champions": len(previous_rfm.get("segments", {}).get("champions", [])),
                    "at_risk": len(previous_rfm.get("segments", {}).get("at_risk", []))
                },
                "changes": {
                    "customer_growth": customer_growth,
                    "customer_growth_rate": round(customer_growth_rate, 2),
                    "champions_change": (
                        len(rfm_analysis.get("segments", {}).get("champions", [])) -
                        len(previous_rfm.get("segments", {}).get("champions", []))
                    ),
                    "at_risk_change": (
                        churn_indicators["at_risk_count"] -
                        len(previous_rfm.get("segments", {}).get("at_risk", []))
                    )
                }
            }
        except Exception as e:
            logger.warning(f"Error calculating temporal comparisons: {e}")
            temporal_comparisons = {
                "current_period": {
                    "total_customers": total_customers,
                    "champions": len(rfm_analysis.get("segments", {}).get("champions", [])),
                    "at_risk": churn_indicators["at_risk_count"]
                },
                "previous_period": None,
                "changes": None,
                "error": "Could not calculate previous period comparison"
            }
        
        report = {
            "retention_trends": retention_trends,
            "churn_indicators": churn_indicators,
            "segment_behavior": segment_behavior,
            "temporal_comparisons": temporal_comparisons,
            "summary": {
                "total_customers": total_customers,
                "new_customers": customers_summary.get("new_customers", 0),
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                }
            }
        }
        
        # Cache result
        if use_cache:
            await self.cache.set(cache_key, report, ttl=600)  # 10 minutes
        
        logger.info(f"Trends analysis generated: {total_customers} customers analyzed")
        
        return report

    # ============================================================================
    # INVENTORY REPORTS - Phase 1: Time Series and Turnover
    # ============================================================================

    async def get_inventory_timeseries(
        self,
        db: AsyncSession,
        sucursal_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        product_id: Optional[str] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Get inventory time series data aggregated by day.
        
        Tracks stock quantity changes over time by analyzing sale_items.
        
        Args:
            db: Database session
            sucursal_id: Optional sucursal ID to filter by
            start_date: Start date for analysis
            end_date: End date for analysis
            product_id: Optional product ID to filter by specific product
            use_cache: Whether to use cache (default: True)
            
        Returns:
            Dictionary with time series data:
            {
                "timeseries": [
                    {
                        "date": "YYYY-MM-DD",
                        "stock_qty": int,
                        "products_count": int,
                        "low_stock_count": int,
                        "total_value_cents": int
                    }
                ],
                "period": {
                    "start_date": "YYYY-MM-DD",
                    "end_date": "YYYY-MM-DD"
                }
            }
        """
        from uuid import UUID
        
        # Generate cache key
        cache_key = self.cache._generate_key(
            "inventory_timeseries",
            sucursal_id,
            start_date.isoformat() if start_date else None,
            end_date.isoformat() if end_date else None,
            product_id
        )
        
        # Check cache
        if use_cache:
            cached = await self.cache.get(cache_key)
            if cached:
                logger.debug(f"Cache HIT for inventory timeseries: {cache_key}")
                return cached
        
        # Default to last 30 days if no dates provided
        if not end_date:
            end_date = await self._get_business_date(db, sucursal_id)
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        # Build query to get daily stock snapshots
        # We'll calculate stock by: initial_stock - sales + (if we had purchase records)
        # For now, we track current stock and sales to estimate historical stock
        
        # Get current products
        product_query = select(Product).where(Product.active == True)
        
        sucursal_uuid = None
        if sucursal_id:
            try:
                sucursal_uuid = UUID(sucursal_id)
                product_query = product_query.where(Product.sucursal_id == sucursal_uuid)
            except (ValueError, TypeError):
                logger.warning(f"Invalid sucursal_id format: {sucursal_id}")
        
        if product_id:
            try:
                product_uuid = UUID(product_id)
                product_query = product_query.where(Product.id == product_uuid)
            except (ValueError, TypeError):
                logger.warning(f"Invalid product_id format: {product_id}")
        
        product_result = await db.execute(product_query)
        products = product_result.scalars().all()
        
        # Get sales data for the period to calculate stock changes
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())
        
        # Query sales of products in the period
        sales_query = select(
            func.date(Sale.created_at).label("sale_date"),
            SaleItem.ref_id.label("product_id"),
            func.sum(SaleItem.quantity).label("quantity_sold")
        ).join(
            SaleItem, Sale.id == SaleItem.sale_id
        ).where(
            and_(
                SaleItem.type == "product",
                Sale.created_at >= start_datetime,
                Sale.created_at <= end_datetime
            )
        )
        
        if sucursal_uuid:
            sales_query = sales_query.where(Sale.sucursal_id == sucursal_uuid)
        
        if product_id:
            try:
                product_uuid = UUID(product_id)
                sales_query = sales_query.where(SaleItem.ref_id == product_uuid)
            except (ValueError, TypeError):
                pass
        
        sales_query = sales_query.group_by(
            func.date(Sale.created_at),
            SaleItem.ref_id
        )
        
        sales_result = await db.execute(sales_query)
        sales_data = sales_result.all()
        
        # Create a map of product_id -> current_stock
        product_stock_map = {str(p.id): p.stock_qty for p in products}
        product_price_map = {str(p.id): p.price_cents for p in products}
        product_threshold_map = {str(p.id): p.threshold_alert_qty for p in products}
        
        # Create a map of date -> product_id -> quantity_sold
        sales_by_date: Dict[str, Dict[str, int]] = {}
        for row in sales_data:
            date_str = row.sale_date.isoformat() if isinstance(row.sale_date, date) else str(row.sale_date)
            prod_id = str(row.product_id)
            qty = int(row.quantity_sold or 0)
            
            if date_str not in sales_by_date:
                sales_by_date[date_str] = {}
            sales_by_date[date_str][prod_id] = sales_by_date[date_str].get(prod_id, 0) + qty
        
        # Generate time series by working backwards from end_date
        # We'll estimate historical stock by adding sales back to current stock
        timeseries = []
        current_date = start_date
        cumulative_sales: Dict[str, int] = {}  # product_id -> total_sold_since_start
        
        while current_date <= end_date:
            date_str = current_date.isoformat()
            
            # Add sales for this date to cumulative
            if date_str in sales_by_date:
                for prod_id, qty in sales_by_date[date_str].items():
                    cumulative_sales[prod_id] = cumulative_sales.get(prod_id, 0) + qty
            
            # Calculate estimated stock for this date (current + cumulative sales)
            total_stock_qty = 0
            total_value_cents = 0
            low_stock_count = 0
            products_count = 0
            
            for prod_id, current_stock in product_stock_map.items():
                estimated_stock = current_stock + cumulative_sales.get(prod_id, 0)
                total_stock_qty += estimated_stock
                total_value_cents += estimated_stock * product_price_map.get(prod_id, 0)
                
                threshold = product_threshold_map.get(prod_id, 0)
                if estimated_stock <= threshold:
                    low_stock_count += 1
                
                products_count += 1
            
            timeseries.append({
                "date": date_str,
                "stock_qty": total_stock_qty,
                "products_count": products_count,
                "low_stock_count": low_stock_count,
                "total_value_cents": total_value_cents
            })
            
            current_date += timedelta(days=1)
        
        report = {
            "timeseries": timeseries,
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            }
        }
        
        # Cache result
        if use_cache:
            await self.cache.set(cache_key, report, ttl=300)  # 5 minutes
        
        logger.info(
            f"Inventory timeseries generated: {len(timeseries)} days, "
            f"from {start_date.isoformat()} to {end_date.isoformat()}"
        )
        
        return report

    async def get_inventory_turnover(
        self,
        db: AsyncSession,
        sucursal_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Get inventory turnover analysis.
        
        Calculates stock turnover rate and days on hand for each product.
        
        Args:
            db: Database session
            sucursal_id: Optional sucursal ID to filter by
            start_date: Start date for analysis (default: 30 days ago)
            end_date: End date for analysis (default: today)
            use_cache: Whether to use cache (default: True)
            
        Returns:
            Dictionary with turnover metrics:
            {
                "products": [
                    {
                        "product_id": str,
                        "product_name": str,
                        "current_stock": int,
                        "quantity_sold": int,
                        "turnover_rate": float,
                        "days_on_hand": float,
                        "category": str (fast/slow/normal)
                    }
                ],
                "summary": {
                    "total_products": int,
                    "fast_movers": int,
                    "slow_movers": int,
                    "average_turnover": float
                },
                "period": {
                    "start_date": "YYYY-MM-DD",
                    "end_date": "YYYY-MM-DD"
                }
            }
        """
        from uuid import UUID
        
        # Generate cache key
        cache_key = self.cache._generate_key(
            "inventory_turnover",
            sucursal_id,
            start_date.isoformat() if start_date else None,
            end_date.isoformat() if end_date else None
        )
        
        # Check cache
        if use_cache:
            cached = await self.cache.get(cache_key)
            if cached:
                logger.debug(f"Cache HIT for inventory turnover: {cache_key}")
                return cached
        
        # Default to last 30 days if no dates provided
        if not end_date:
            end_date = await self._get_business_date(db, sucursal_id)
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        days_in_period = (end_date - start_date).days + 1
        
        # Get products
        product_query = select(Product).where(Product.active == True)
        
        sucursal_uuid = None
        if sucursal_id:
            try:
                sucursal_uuid = UUID(sucursal_id)
                product_query = product_query.where(Product.sucursal_id == sucursal_uuid)
            except (ValueError, TypeError):
                logger.warning(f"Invalid sucursal_id format: {sucursal_id}")
        
        product_result = await db.execute(product_query)
        products = product_result.scalars().all()
        
        # Get sales data for products in the period
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())
        
        sales_query = select(
            SaleItem.ref_id.label("product_id"),
            func.sum(SaleItem.quantity).label("quantity_sold")
        ).join(
            Sale, SaleItem.sale_id == Sale.id
        ).where(
            and_(
                SaleItem.type == "product",
                Sale.created_at >= start_datetime,
                Sale.created_at <= end_datetime
            )
        )
        
        if sucursal_uuid:
            sales_query = sales_query.where(Sale.sucursal_id == sucursal_uuid)
        
        sales_query = sales_query.group_by(SaleItem.ref_id)
        
        sales_result = await db.execute(sales_query)
        sales_data = {str(row.product_id): int(row.quantity_sold or 0) for row in sales_result.all()}
        
        # Calculate turnover for each product
        products_turnover = []
        total_turnover = 0.0
        fast_movers = 0
        slow_movers = 0
        
        for product in products:
            product_id = str(product.id)
            current_stock = product.stock_qty
            quantity_sold = sales_data.get(product_id, 0)
            
            # Calculate average stock (simplified: use current stock as average)
            # In a real scenario, we'd calculate average stock over the period
            average_stock = max(current_stock, 1)  # Avoid division by zero
            
            # Turnover rate = quantity_sold / average_stock
            turnover_rate = quantity_sold / average_stock if average_stock > 0 else 0.0
            
            # Days on hand = (average_stock / (quantity_sold / days_in_period))
            # If no sales, days on hand is infinite, so we cap it
            if quantity_sold > 0:
                daily_sales_rate = quantity_sold / days_in_period
                days_on_hand = average_stock / daily_sales_rate if daily_sales_rate > 0 else 999
            else:
                days_on_hand = 999  # No sales, infinite days on hand
            
            # Categorize: fast (>2x), slow (<0.5x), normal (0.5x-2x)
            # Using average turnover as baseline
            category = "normal"
            if turnover_rate > 2.0:
                category = "fast"
                fast_movers += 1
            elif turnover_rate < 0.5:
                category = "slow"
                slow_movers += 1
            
            products_turnover.append({
                "product_id": product_id,
                "product_name": product.name,
                "current_stock": current_stock,
                "quantity_sold": quantity_sold,
                "turnover_rate": round(turnover_rate, 2),
                "days_on_hand": round(days_on_hand, 1),
                "category": category
            })
            
            total_turnover += turnover_rate
        
        # Sort by turnover rate (descending)
        products_turnover.sort(key=lambda x: x["turnover_rate"], reverse=True)
        
        average_turnover = total_turnover / len(products_turnover) if products_turnover else 0.0
        
        report = {
            "products": products_turnover,
            "summary": {
                "total_products": len(products_turnover),
                "fast_movers": fast_movers,
                "slow_movers": slow_movers,
                "normal_movers": len(products_turnover) - fast_movers - slow_movers,
                "average_turnover": round(average_turnover, 2)
            },
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days_in_period
            }
        }
        
        # Cache result
        if use_cache:
            await self.cache.set(cache_key, report, ttl=300)  # 5 minutes
        
        logger.info(
            f"Inventory turnover generated: {len(products_turnover)} products, "
            f"from {start_date.isoformat()} to {end_date.isoformat()}"
        )
        
        return report

    # ============================================================================
    # SERVICES REPORTS - Phase 1: Time Series and Utilization
    # ============================================================================

    async def get_services_timeseries(
        self,
        db: AsyncSession,
        sucursal_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        service_id: Optional[str] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Get services time series data aggregated by day.
        
        Tracks service sales, active timers, and revenue over time.
        
        Args:
            db: Database session
            sucursal_id: Optional sucursal ID to filter by
            start_date: Start date for analysis
            end_date: End date for analysis
            service_id: Optional service ID to filter by specific service
            use_cache: Whether to use cache (default: True)
            
        Returns:
            Dictionary with time series data:
            {
                "timeseries": [
                    {
                        "date": "YYYY-MM-DD",
                        "service_sales_count": int,
                        "package_sales_count": int,
                        "total_sales_count": int,
                        "revenue_cents": int,
                        "active_timers_count": int
                    }
                ],
                "period": {
                    "start_date": "YYYY-MM-DD",
                    "end_date": "YYYY-MM-DD"
                }
            }
        """
        from uuid import UUID
        
        # Generate cache key
        cache_key = self.cache._generate_key(
            "services_timeseries",
            sucursal_id,
            start_date.isoformat() if start_date else None,
            end_date.isoformat() if end_date else None,
            service_id
        )
        
        # Check cache
        if use_cache:
            cached = await self.cache.get(cache_key)
            if cached:
                logger.debug(f"Cache HIT for services timeseries: {cache_key}")
                return cached
        
        # Default to last 30 days if no dates provided
        if not end_date:
            end_date = await self._get_business_date(db, sucursal_id)
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())
        
        sucursal_uuid = None
        if sucursal_id:
            try:
                sucursal_uuid = UUID(sucursal_id)
            except (ValueError, TypeError):
                logger.warning(f"Invalid sucursal_id format: {sucursal_id}")
        
        # Query service sales (direct service sales)
        service_sales_query = select(
            func.date(Sale.created_at).label("sale_date"),
            func.count(Sale.id).label("sales_count"),
            func.sum(Sale.total_cents).label("revenue_cents")
        ).where(
            and_(
                Sale.tipo == "service",
                Sale.created_at >= start_datetime,
                Sale.created_at <= end_datetime
            )
        )
        
        if sucursal_uuid:
            service_sales_query = service_sales_query.where(Sale.sucursal_id == sucursal_uuid)
        
        if service_id:
            try:
                service_uuid = UUID(service_id)
                # Join with SaleItem to filter by service
                service_sales_query = service_sales_query.join(
                    SaleItem, Sale.id == SaleItem.sale_id
                ).where(
                    and_(
                        SaleItem.type == "service",
                        SaleItem.ref_id == service_uuid
                    )
                )
            except (ValueError, TypeError):
                logger.warning(f"Invalid service_id format: {service_id}")
        
        service_sales_query = service_sales_query.group_by(func.date(Sale.created_at))
        
        service_sales_result = await db.execute(service_sales_query)
        service_sales_data = {
            row.sale_date.isoformat() if isinstance(row.sale_date, date) else str(row.sale_date): {
                "count": int(row.sales_count or 0),
                "revenue": int(row.revenue_cents or 0)
            }
            for row in service_sales_result.all()
        }
        
        # Query package sales (service packages)
        # First, get all package sales for the period
        package_sales_query = select(
            func.date(Sale.created_at).label("sale_date"),
            SaleItem.ref_id.label("package_id"),
            Sale.total_cents.label("total_cents")
        ).join(
            SaleItem, Sale.id == SaleItem.sale_id
        ).where(
            and_(
                SaleItem.type == "package",
                Sale.tipo == "package",
                Sale.created_at >= start_datetime,
                Sale.created_at <= end_datetime
            )
        )
        
        if sucursal_uuid:
            package_sales_query = package_sales_query.where(Sale.sucursal_id == sucursal_uuid)
        
        package_sales_result = await db.execute(package_sales_query)
        package_sales_rows = package_sales_result.all()
        
        # Extract unique package IDs
        package_ids = list(set(row.package_id for row in package_sales_rows))
        
        # Load packages from database and filter service packages
        package_sales_data = {}
        if package_ids:
            packages_query = select(Package).where(Package.id.in_(package_ids))
            packages_result = await db.execute(packages_query)
            packages = packages_result.scalars().all()
            
            # Get service package IDs using helper
            service_package_ids = get_service_package_ids(list(packages))
            service_package_ids_set = set(service_package_ids)
            
            # If service_id is provided, we need to filter packages that contain that specific service
            if service_id:
                try:
                    service_uuid = UUID(service_id)
                    # Filter packages that contain the specific service
                    filtered_service_package_ids = []
                    for pkg in packages:
                        if pkg.id in service_package_ids_set:
                            # Check if package contains the specific service
                            items = pkg.included_items or []
                            for item in items:
                                item_service_id = item.get("service_id")
                                if item_service_id:
                                    # Normalize to UUID for comparison (handle both string and UUID)
                                    if isinstance(item_service_id, str):
                                        try:
                                            item_service_uuid = UUID(item_service_id)
                                        except (ValueError, TypeError):
                                            continue
                                    else:
                                        item_service_uuid = item_service_id
                                    
                                    if item_service_uuid == service_uuid:
                                        filtered_service_package_ids.append(pkg.id)
                                        break  # Found the service, no need to check other items
                    service_package_ids_set = set(filtered_service_package_ids)
                except (ValueError, TypeError) as e:
                    logger.warning(f"Invalid service_id format: {service_id}, error: {e}")
                    service_package_ids_set = set()  # Empty set if invalid service_id
            
            # Aggregate package sales by date, only for service packages
            for row in package_sales_rows:
                if row.package_id in service_package_ids_set:
                    date_str = row.sale_date.isoformat() if isinstance(row.sale_date, date) else str(row.sale_date)
                    if date_str not in package_sales_data:
                        package_sales_data[date_str] = {"count": 0, "revenue": 0}
                    package_sales_data[date_str]["count"] += 1
                    package_sales_data[date_str]["revenue"] += int(row.total_cents or 0)
        
        # Query active timers count by date
        # Count timers that were active on each day
        timer_query = select(
            func.date(Timer.created_at).label("timer_date"),
            func.count(Timer.id).label("timers_count")
        ).where(
            and_(
                Timer.status.in_(["active", "scheduled", "extended"]),
                Timer.created_at >= start_datetime,
                Timer.created_at <= end_datetime
            )
        )
        
        if sucursal_uuid:
            timer_query = timer_query.join(Sale, Timer.sale_id == Sale.id).where(
                Sale.sucursal_id == sucursal_uuid
            )
        
        if service_id:
            try:
                service_uuid = UUID(service_id)
                timer_query = timer_query.where(Timer.service_id == service_uuid)
            except (ValueError, TypeError):
                pass
        
        timer_query = timer_query.group_by(func.date(Timer.created_at))
        
        timer_result = await db.execute(timer_query)
        timer_data = {
            row.timer_date.isoformat() if isinstance(row.timer_date, date) else str(row.timer_date): int(row.timers_count or 0)
            for row in timer_result.all()
        }
        
        # Generate time series
        timeseries = []
        current_date = start_date
        
        while current_date <= end_date:
            date_str = current_date.isoformat()
            
            service_sales = service_sales_data.get(date_str, {"count": 0, "revenue": 0})
            package_sales = package_sales_data.get(date_str, {"count": 0, "revenue": 0})
            
            timeseries.append({
                "date": date_str,
                "service_sales_count": service_sales["count"],
                "package_sales_count": package_sales["count"],
                "total_sales_count": service_sales["count"] + package_sales["count"],
                "revenue_cents": service_sales["revenue"] + package_sales["revenue"],
                "active_timers_count": timer_data.get(date_str, 0)
            })
            
            current_date += timedelta(days=1)
        
        report = {
            "timeseries": timeseries,
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            }
        }
        
        # Cache result
        if use_cache:
            await self.cache.set(cache_key, report, ttl=300)  # 5 minutes
        
        logger.info(
            f"Services timeseries generated: {len(timeseries)} days, "
            f"from {start_date.isoformat()} to {end_date.isoformat()}"
        )
        
        return report

    async def get_services_utilization(
        self,
        db: AsyncSession,
        sucursal_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Get services utilization analysis.
        
        Calculates utilization rate based on active timers vs capacity.
        If max_capacity is not set in Service model, uses estimated capacity.
        
        Args:
            db: Database session
            sucursal_id: Optional sucursal ID to filter by
            start_date: Start date for analysis (default: 30 days ago)
            end_date: End date for analysis (default: today)
            use_cache: Whether to use cache (default: True)
            
        Returns:
            Dictionary with utilization metrics:
            {
                "services": [
                    {
                        "service_id": str,
                        "service_name": str,
                        "active_timers": int,
                        "max_capacity": int (or estimated),
                        "utilization_rate": float,
                        "total_sales": int,
                        "revenue_cents": int
                    }
                ],
                "summary": {
                    "total_services": int,
                    "average_utilization": float,
                    "high_utilization_count": int,
                    "low_utilization_count": int
                },
                "period": {
                    "start_date": "YYYY-MM-DD",
                    "end_date": "YYYY-MM-DD"
                }
            }
        """
        from uuid import UUID
        
        # Generate cache key
        cache_key = self.cache._generate_key(
            "services_utilization",
            sucursal_id,
            start_date.isoformat() if start_date else None,
            end_date.isoformat() if end_date else None
        )
        
        # Check cache
        if use_cache:
            cached = await self.cache.get(cache_key)
            if cached:
                logger.debug(f"Cache HIT for services utilization: {cache_key}")
                return cached
        
        # Default to last 30 days if no dates provided
        if not end_date:
            end_date = await self._get_business_date(db, sucursal_id)
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())
        
        # Get services
        service_query = select(Service).where(Service.active == True)
        
        sucursal_uuid = None
        if sucursal_id:
            try:
                sucursal_uuid = UUID(sucursal_id)
                service_query = service_query.where(Service.sucursal_id == sucursal_uuid)
            except (ValueError, TypeError):
                logger.warning(f"Invalid sucursal_id format: {sucursal_id}")
        
        service_result = await db.execute(service_query)
        services = service_result.scalars().all()
        
        # Get active timers count per service
        timer_query = select(
            Timer.service_id,
            func.count(Timer.id).label("timers_count")
        ).where(
            and_(
                Timer.status.in_(["active", "scheduled", "extended"]),
                Timer.created_at >= start_datetime,
                Timer.created_at <= end_datetime
            )
        )
        
        if sucursal_uuid:
            timer_query = timer_query.join(Sale, Timer.sale_id == Sale.id).where(
                Sale.sucursal_id == sucursal_uuid
            )
        
        timer_query = timer_query.group_by(Timer.service_id)
        
        timer_result = await db.execute(timer_query)
        timer_data = {str(row.service_id): int(row.timers_count or 0) for row in timer_result.all()}
        
        # Get sales data per service
        sales_query = select(
            SaleItem.ref_id.label("service_id"),
            func.count(Sale.id).label("sales_count"),
            func.sum(Sale.total_cents).label("revenue_cents")
        ).join(
            Sale, SaleItem.sale_id == Sale.id
        ).where(
            and_(
                SaleItem.type == "service",
                Sale.created_at >= start_datetime,
                Sale.created_at <= end_datetime
            )
        )
        
        if sucursal_uuid:
            sales_query = sales_query.where(Sale.sucursal_id == sucursal_uuid)
        
        sales_query = sales_query.group_by(SaleItem.ref_id)
        
        sales_result = await db.execute(sales_query)
        sales_data = {
            str(row.service_id): {
                "count": int(row.sales_count or 0),
                "revenue": int(row.revenue_cents or 0)
            }
            for row in sales_result.all()
        }
        
        # Calculate utilization for each service
        services_utilization = []
        total_utilization = 0.0
        high_utilization_count = 0
        low_utilization_count = 0
        
        for service in services:
            service_id = str(service.id)
            active_timers = timer_data.get(service_id, 0)
            
            # Estimate max_capacity if not available
            # Use a default based on typical service capacity
            # In future, this could come from Service.max_capacity field
            max_capacity = 10  # Default estimated capacity
            # TODO: Add max_capacity to Service model when available
            
            utilization_rate = (active_timers / max_capacity * 100) if max_capacity > 0 else 0.0
            utilization_rate = min(utilization_rate, 100.0)  # Cap at 100%
            
            sales_info = sales_data.get(service_id, {"count": 0, "revenue": 0})
            
            # Categorize: high (>80%), low (<20%), normal (20%-80%)
            if utilization_rate > 80.0:
                high_utilization_count += 1
            elif utilization_rate < 20.0:
                low_utilization_count += 1
            
            services_utilization.append({
                "service_id": service_id,
                "service_name": service.name,
                "active_timers": active_timers,
                "max_capacity": max_capacity,
                "utilization_rate": round(utilization_rate, 1),
                "total_sales": sales_info["count"],
                "revenue_cents": sales_info["revenue"]
            })
            
            total_utilization += utilization_rate
        
        # Sort by utilization rate (descending)
        services_utilization.sort(key=lambda x: x["utilization_rate"], reverse=True)
        
        average_utilization = total_utilization / len(services_utilization) if services_utilization else 0.0
        
        report = {
            "services": services_utilization,
            "summary": {
                "total_services": len(services_utilization),
                "average_utilization": round(average_utilization, 1),
                "high_utilization_count": high_utilization_count,
                "low_utilization_count": low_utilization_count,
                "normal_utilization_count": len(services_utilization) - high_utilization_count - low_utilization_count
            },
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            }
        }
        
        # Cache result
        if use_cache:
            await self.cache.set(cache_key, report, ttl=300)  # 5 minutes
        
        logger.info(
            f"Services utilization generated: {len(services_utilization)} services, "
            f"from {start_date.isoformat()} to {end_date.isoformat()}"
        )
        
        return report

    # ============================================================================
    # INVENTORY REPORTS - Phase 2: Heatmap and Movement Analysis
    # ============================================================================

    async def get_inventory_heatmap(
        self,
        db: AsyncSession,
        sucursal_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Get inventory heatmap data for calendar visualization.
        
        Shows stock levels and alerts intensity by day.
        """
        from uuid import UUID
        
        cache_key = self.cache._generate_key(
            "inventory_heatmap",
            sucursal_id,
            start_date.isoformat() if start_date else None,
            end_date.isoformat() if end_date else None
        )
        
        if use_cache:
            cached = await self.cache.get(cache_key)
            if cached:
                logger.debug(f"Cache HIT for inventory heatmap: {cache_key}")
                return cached
        
        if not end_date:
            end_date = await self._get_business_date(db, sucursal_id)
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        # Get time series data
        timeseries_data = await self.get_inventory_timeseries(
            db, sucursal_id, start_date, end_date, None, False
        )
        
        heatmap = []
        for point in timeseries_data.get("timeseries", []):
            # Calculate intensity based on low_stock_count
            low_stock = point.get("low_stock_count", 0)
            total_products = point.get("products_count", 1)
            intensity = min(4, int((low_stock / total_products) * 4)) if total_products > 0 else 0
            
            heatmap.append({
                "date": point["date"],
                "stock_qty": point.get("stock_qty", 0),
                "low_stock_count": low_stock,
                "intensity": intensity
            })
        
        report = {"heatmap": heatmap, "period": timeseries_data.get("period", {})}
        
        if use_cache:
            await self.cache.set(cache_key, report, ttl=300)
        
        logger.info(f"Inventory heatmap generated: {len(heatmap)} days")
        return report

    async def get_inventory_movement(
        self,
        db: AsyncSession,
        sucursal_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Get fast/slow movers analysis.
        
        Identifies products with high/low movement rates.
        """
        # Reuse turnover data but format differently
        turnover_data = await self.get_inventory_turnover(
            db, sucursal_id, start_date, end_date, use_cache
        )
        
        fast_movers = [p for p in turnover_data["products"] if p["category"] == "fast"]
        slow_movers = [p for p in turnover_data["products"] if p["category"] == "slow"]
        normal_movers = [p for p in turnover_data["products"] if p["category"] == "normal"]
        
        return {
            "fast_movers": fast_movers[:20],  # Top 20
            "slow_movers": slow_movers[:20],
            "normal_movers": normal_movers[:20],
            "summary": turnover_data["summary"],
            "period": turnover_data["period"]
        }

    # ============================================================================
    # INVENTORY REPORTS - Phase 3: Reorder Points and Alerts
    # ============================================================================

    async def get_inventory_reorder_points(
        self,
        db: AsyncSession,
        sucursal_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Calculate reorder points for products.
        
        ROP = (average_daily_sales * lead_time_days) + safety_stock
        """
        from uuid import UUID
        
        cache_key = self.cache._generate_key(
            "inventory_reorder_points",
            sucursal_id,
            start_date.isoformat() if start_date else None,
            end_date.isoformat() if end_date else None
        )
        
        if use_cache:
            cached = await self.cache.get(cache_key)
            if cached:
                logger.debug(f"Cache HIT for reorder points: {cache_key}")
                return cached
        
        if not end_date:
            end_date = await self._get_business_date(db, sucursal_id)
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        days_in_period = (end_date - start_date).days + 1
        
        # Get turnover data
        turnover_data = await self.get_inventory_turnover(
            db, sucursal_id, start_date, end_date, False
        )
        
        # Default lead time (in days) - can be configured per product in future
        default_lead_time = 7
        safety_stock_factor = 1.5  # 50% extra as safety stock
        
        reorder_points = []
        for product in turnover_data["products"]:
            quantity_sold = product["quantity_sold"]
            daily_sales = quantity_sold / days_in_period if days_in_period > 0 else 0
            
            # Calculate reorder point
            lead_time_days = default_lead_time
            reorder_point = int((daily_sales * lead_time_days) * safety_stock_factor)
            
            # Current stock status
            current_stock = product["current_stock"]
            needs_reorder = current_stock <= reorder_point
            
            reorder_points.append({
                "product_id": product["product_id"],
                "product_name": product["product_name"],
                "current_stock": current_stock,
                "daily_sales_avg": round(daily_sales, 2),
                "lead_time_days": lead_time_days,
                "reorder_point": reorder_point,
                "safety_stock": int(reorder_point * 0.33),  # 33% of ROP
                "needs_reorder": needs_reorder,
                "days_until_stockout": int(current_stock / daily_sales) if daily_sales > 0 else 999
            })
        
        # Sort by needs_reorder and days_until_stockout
        reorder_points.sort(key=lambda x: (not x["needs_reorder"], x["days_until_stockout"]))
        
        report = {
            "reorder_points": reorder_points,
            "summary": {
                "total_products": len(reorder_points),
                "needs_reorder_count": sum(1 for p in reorder_points if p["needs_reorder"]),
                "default_lead_time_days": default_lead_time
            },
            "period": turnover_data["period"]
        }
        
        if use_cache:
            await self.cache.set(cache_key, report, ttl=300)
        
        logger.info(f"Reorder points calculated: {len(reorder_points)} products")
        return report

    async def get_inventory_alerts(
        self,
        db: AsyncSession,
        sucursal_id: Optional[str] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Get intelligent inventory alerts with context.
        
        Combines low stock alerts with turnover and reorder point data.
        """
        end_date = await self._get_business_date(db, sucursal_id)
        start_date = end_date - timedelta(days=30)
        
        # Get all relevant data
        stock_data = await self.get_stock_report(db, sucursal_id, use_cache)
        turnover_data = await self.get_inventory_turnover(db, sucursal_id, start_date, end_date, use_cache)
        reorder_data = await self.get_inventory_reorder_points(db, sucursal_id, start_date, end_date, use_cache)
        
        alerts = []
        
        # Low stock alerts
        for alert in stock_data.get("low_stock_alerts", []):
            product_id = alert.get("product_id")
            
            # Find turnover and reorder info
            turnover_info = next((p for p in turnover_data["products"] if p["product_id"] == product_id), None)
            reorder_info = next((p for p in reorder_data["reorder_points"] if p["product_id"] == product_id), None)
            
            alert_level = "high"
            if reorder_info and reorder_info["days_until_stockout"] > 7:
                alert_level = "medium"
            elif reorder_info and reorder_info["days_until_stockout"] > 14:
                alert_level = "low"
            
            alerts.append({
                "type": "low_stock",
                "level": alert_level,
                "product_id": product_id,
                "product_name": alert.get("product_name"),
                "current_stock": alert.get("stock_qty", 0),
                "threshold": alert.get("threshold_alert_qty", 0),
                "days_until_stockout": reorder_info["days_until_stockout"] if reorder_info else None,
                "recommended_reorder_qty": reorder_info["reorder_point"] if reorder_info else None,
                "turnover_rate": turnover_info["turnover_rate"] if turnover_info else None
            })
        
        # Reorder needed alerts
        for reorder in reorder_data["reorder_points"]:
            if reorder["needs_reorder"] and not any(a["product_id"] == reorder["product_id"] for a in alerts):
                alerts.append({
                    "type": "reorder_needed",
                    "level": "high" if reorder["days_until_stockout"] < 7 else "medium",
                    "product_id": reorder["product_id"],
                    "product_name": reorder["product_name"],
                    "current_stock": reorder["current_stock"],
                    "reorder_point": reorder["reorder_point"],
                    "days_until_stockout": reorder["days_until_stockout"],
                    "recommended_reorder_qty": reorder["reorder_point"]
                })
        
        # Sort by level (high first)
        alerts.sort(key=lambda x: {"high": 0, "medium": 1, "low": 2}.get(x["level"], 3))
        
        return {
            "alerts": alerts,
            "summary": {
                "total_alerts": len(alerts),
                "high_priority": sum(1 for a in alerts if a["level"] == "high"),
                "medium_priority": sum(1 for a in alerts if a["level"] == "medium"),
                "low_priority": sum(1 for a in alerts if a["level"] == "low")
            }
        }

    # ============================================================================
    # INVENTORY REPORTS - Phase 4: Forecasting and Recommendations
    # ============================================================================

    async def get_inventory_forecast(
        self,
        db: AsyncSession,
        sucursal_id: Optional[str] = None,
        forecast_days: int = 7,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Forecast inventory demand for next N days.
        
        Uses simple moving average based on recent sales.
        """
        end_date = await self._get_business_date(db, sucursal_id)
        start_date = end_date - timedelta(days=30)
        
        # Get turnover data for recent sales
        turnover_data = await self.get_inventory_turnover(db, sucursal_id, start_date, end_date, use_cache)
        
        forecasts = []
        for product in turnover_data["products"]:
            quantity_sold = product["quantity_sold"]
            days_in_period = turnover_data["period"]["days"]
            daily_avg = quantity_sold / days_in_period if days_in_period > 0 else 0
            
            # Simple forecast: daily_avg * forecast_days
            forecasted_demand = int(daily_avg * forecast_days)
            current_stock = product["current_stock"]
            projected_stock = current_stock - forecasted_demand
            
            forecasts.append({
                "product_id": product["product_id"],
                "product_name": product["product_name"],
                "current_stock": current_stock,
                "daily_avg_sales": round(daily_avg, 2),
                "forecasted_demand": forecasted_demand,
                "projected_stock": projected_stock,
                "will_run_out": projected_stock < 0,
                "days_until_out": int(current_stock / daily_avg) if daily_avg > 0 else 999
            })
        
        forecasts.sort(key=lambda x: (not x["will_run_out"], x["days_until_out"]))
        
        return {
            "forecasts": forecasts,
            "summary": {
                "forecast_days": forecast_days,
                "total_products": len(forecasts),
                "will_run_out_count": sum(1 for f in forecasts if f["will_run_out"])
            },
            "period": {
                "start_date": end_date.isoformat(),
                "end_date": (end_date + timedelta(days=forecast_days)).isoformat()
            }
        }

    async def get_inventory_recommendations(
        self,
        db: AsyncSession,
        sucursal_id: Optional[str] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Generate actionable recommendations for inventory management.
        """
        end_date = await self._get_business_date(db, sucursal_id)
        start_date = end_date - timedelta(days=30)
        
        # Get all relevant data
        stock_data = await self.get_stock_report(db, sucursal_id, use_cache)
        turnover_data = await self.get_inventory_turnover(db, sucursal_id, start_date, end_date, use_cache)
        reorder_data = await self.get_inventory_reorder_points(db, sucursal_id, start_date, end_date, use_cache)
        forecast_data = await self.get_inventory_forecast(db, sucursal_id, 7, use_cache)
        
        recommendations = []
        
        # Check for slow movers
        slow_movers_count = turnover_data["summary"]["slow_movers"]
        if slow_movers_count > 0:
            recommendations.append({
                "priority": "medium",
                "title": f"Revisar {slow_movers_count} productos de movimiento lento",
                "description": "Algunos productos tienen baja rotación. Considera promociones o ajustes de stock.",
                "action": "Revisar estrategia de pricing o marketing para estos productos"
            })
        
        # Check for products that will run out
        will_run_out = forecast_data["summary"]["will_run_out_count"]
        if will_run_out > 0:
            recommendations.append({
                "priority": "high",
                "title": f"{will_run_out} productos se quedarán sin stock",
                "description": "Según el pronóstico, algunos productos se agotarán en los próximos 7 días.",
                "action": "Realizar pedidos urgentes para estos productos"
            })
        
        # Check reorder needs
        needs_reorder = reorder_data["summary"]["needs_reorder_count"]
        if needs_reorder > 0:
            recommendations.append({
                "priority": "high",
                "title": f"{needs_reorder} productos requieren reorden",
                "description": "El stock actual está por debajo del punto de reorden recomendado.",
                "action": "Proceder con pedidos de reposición"
            })
        
        if not recommendations:
            recommendations.append({
                "priority": "info",
                "title": "Inventario en buen estado",
                "description": "No se detectaron problemas críticos en el inventario.",
                "action": "Continuar monitoreando"
            })
        
        return {
            "recommendations": recommendations,
            "summary": f"{len(recommendations)} recomendaciones generadas"
        }

    # ============================================================================
    # SERVICES REPORTS - Phase 2: Performance and Duration Analysis
    # ============================================================================

    async def get_services_performance(
        self,
        db: AsyncSession,
        sucursal_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Get service performance metrics (revenue, popularity, efficiency).
        """
        from uuid import UUID
        
        cache_key = self.cache._generate_key(
            "services_performance",
            sucursal_id,
            start_date.isoformat() if start_date else None,
            end_date.isoformat() if end_date else None
        )
        
        if use_cache:
            cached = await self.cache.get(cache_key)
            if cached:
                logger.debug(f"Cache HIT for services performance: {cache_key}")
                return cached
        
        if not end_date:
            end_date = await self._get_business_date(db, sucursal_id)
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())
        
        sucursal_uuid = None
        if sucursal_id:
            try:
                sucursal_uuid = UUID(sucursal_id)
            except (ValueError, TypeError):
                logger.warning(f"Invalid sucursal_id format: {sucursal_id}")
        
        # Get service sales data
        sales_query = select(
            SaleItem.ref_id.label("service_id"),
            func.count(Sale.id).label("sales_count"),
            func.sum(Sale.total_cents).label("revenue_cents")
        ).join(
            Sale, SaleItem.sale_id == Sale.id
        ).where(
            and_(
                SaleItem.type == "service",
                Sale.created_at >= start_datetime,
                Sale.created_at <= end_datetime
            )
        )
        
        if sucursal_uuid:
            sales_query = sales_query.where(Sale.sucursal_id == sucursal_uuid)
        
        sales_query = sales_query.group_by(SaleItem.ref_id)
        
        sales_result = await db.execute(sales_query)
        sales_data = {
            str(row.service_id): {
                "count": int(row.sales_count or 0),
                "revenue": int(row.revenue_cents or 0)
            }
            for row in sales_result.all()
        }
        
        # Get services
        service_query = select(Service).where(Service.active == True)
        if sucursal_uuid:
            service_query = service_query.where(Service.sucursal_id == sucursal_uuid)
        
        service_result = await db.execute(service_query)
        services = service_result.scalars().all()
        
        performance = []
        for service in services:
            service_id = str(service.id)
            sales_info = sales_data.get(service_id, {"count": 0, "revenue": 0})
            
            performance.append({
                "service_id": service_id,
                "service_name": service.name,
                "sales_count": sales_info["count"],
                "revenue_cents": sales_info["revenue"],
                "popularity_rank": 0  # Will be set after sorting
            })
        
        # Sort by revenue and assign ranks
        performance.sort(key=lambda x: x["revenue_cents"], reverse=True)
        for i, p in enumerate(performance):
            p["popularity_rank"] = i + 1
        
        report = {
            "services": performance,
            "summary": {
                "total_services": len(performance),
                "total_revenue_cents": sum(p["revenue_cents"] for p in performance),
                "total_sales": sum(p["sales_count"] for p in performance)
            },
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            }
        }
        
        if use_cache:
            await self.cache.set(cache_key, report, ttl=300)
        
        logger.info(f"Services performance generated: {len(performance)} services")
        return report

    async def get_services_duration(
        self,
        db: AsyncSession,
        sucursal_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Analyze average service duration and usage patterns.
        """
        from uuid import UUID
        
        cache_key = self.cache._generate_key(
            "services_duration",
            sucursal_id,
            start_date.isoformat() if start_date else None,
            end_date.isoformat() if end_date else None
        )
        
        if use_cache:
            cached = await self.cache.get(cache_key)
            if cached:
                logger.debug(f"Cache HIT for services duration: {cache_key}")
                return cached
        
        if not end_date:
            end_date = await self._get_business_date(db, sucursal_id)
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())
        
        sucursal_uuid = None
        if sucursal_id:
            try:
                sucursal_uuid = UUID(sucursal_id)
            except (ValueError, TypeError):
                logger.warning(f"Invalid sucursal_id format: {sucursal_id}")
        
        # Query timer durations
        timer_query = select(
            Timer.service_id,
            func.avg(
                func.extract('epoch', Timer.end_at - Timer.start_at) / 60
            ).label("avg_duration_minutes"),
            func.count(Timer.id).label("timer_count")
        ).where(
            and_(
                Timer.status == "completed",
                Timer.start_at >= start_datetime,
                Timer.end_at <= end_datetime
            )
        )
        
        if sucursal_uuid:
            timer_query = timer_query.join(Sale, Timer.sale_id == Sale.id).where(
                Sale.sucursal_id == sucursal_uuid
            )
        
        timer_query = timer_query.group_by(Timer.service_id)
        
        timer_result = await db.execute(timer_query)
        duration_data = {
            str(row.service_id): {
                "avg_duration_minutes": float(row.avg_duration_minutes or 0),
                "timer_count": int(row.timer_count or 0)
            }
            for row in timer_result.all()
        }
        
        # Get services
        service_query = select(Service).where(Service.active == True)
        if sucursal_uuid:
            service_query = service_query.where(Service.sucursal_id == sucursal_uuid)
        
        service_result = await db.execute(service_query)
        services = service_result.scalars().all()
        
        durations = []
        for service in services:
            service_id = str(service.id)
            duration_info = duration_data.get(service_id, {"avg_duration_minutes": 0, "timer_count": 0})
            
            # Get allowed durations from service
            allowed_durations = service.durations_allowed or []
            min_duration = min(allowed_durations) if allowed_durations else 0
            max_duration = max(allowed_durations) if allowed_durations else 0
            
            durations.append({
                "service_id": service_id,
                "service_name": service.name,
                "avg_duration_minutes": round(duration_info["avg_duration_minutes"], 1),
                "timer_count": duration_info["timer_count"],
                "min_allowed_duration": min_duration,
                "max_allowed_duration": max_duration,
                "usage_efficiency": round((duration_info["avg_duration_minutes"] / max_duration * 100) if max_duration > 0 else 0, 1)
            })
        
        durations.sort(key=lambda x: x["timer_count"], reverse=True)
        
        report = {
            "services": durations,
            "summary": {
                "total_services": len(durations),
                "total_timers": sum(d["timer_count"] for d in durations),
                "avg_duration_all": round(sum(d["avg_duration_minutes"] for d in durations) / len(durations) if durations else 0, 1)
            },
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            }
        }
        
        if use_cache:
            await self.cache.set(cache_key, report, ttl=300)
        
        logger.info(f"Services duration generated: {len(durations)} services")
        return report

    # ============================================================================
    # SERVICES REPORTS - Phase 3: Capacity and Peak Hours Analysis
    # ============================================================================

    async def get_services_capacity(
        self,
        db: AsyncSession,
        sucursal_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Get capacity utilization heatmap by hour/day.
        """
        from uuid import UUID
        
        cache_key = self.cache._generate_key(
            "services_capacity",
            sucursal_id,
            start_date.isoformat() if start_date else None,
            end_date.isoformat() if end_date else None
        )
        
        if use_cache:
            cached = await self.cache.get(cache_key)
            if cached:
                logger.debug(f"Cache HIT for services capacity: {cache_key}")
                return cached
        
        if not end_date:
            end_date = await self._get_business_date(db, sucursal_id)
        if not start_date:
            start_date = end_date - timedelta(days=7)  # Last week for capacity analysis
        
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())
        
        sucursal_uuid = None
        if sucursal_id:
            try:
                sucursal_uuid = UUID(sucursal_id)
            except (ValueError, TypeError):
                logger.warning(f"Invalid sucursal_id format: {sucursal_id}")
        
        timezone_str = await self._get_sucursal_timezone(db, sucursal_id)
        
        # Query active timers by hour and day
        timer_query = select(
            func.date(Timer.created_at).label("timer_date"),
            self._extract_hour_in_timezone(Timer.created_at, timezone_str).label("timer_hour"),
            func.count(Timer.id).label("active_count")
        ).where(
            and_(
                Timer.status.in_(["active", "scheduled", "extended"]),
                Timer.created_at >= start_datetime,
                Timer.created_at <= end_datetime
            )
        )
        
        if sucursal_uuid:
            timer_query = timer_query.join(Sale, Timer.sale_id == Sale.id).where(
                Sale.sucursal_id == sucursal_uuid
            )
        
        timer_query = timer_query.group_by(
            func.date(Timer.created_at),
            self._extract_hour_in_timezone(Timer.created_at, timezone_str)
        )
        
        timer_result = await db.execute(timer_query)
        capacity_data = {}
        
        for row in timer_result.all():
            date_str = row.timer_date.isoformat() if isinstance(row.timer_date, date) else str(row.timer_date)
            hour = int(row.timer_hour)
            count = int(row.active_count or 0)
            
            if date_str not in capacity_data:
                capacity_data[date_str] = {}
            capacity_data[date_str][hour] = count
        
        # Generate heatmap data
        heatmap = []
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.isoformat()
            for hour in range(24):
                count = capacity_data.get(date_str, {}).get(hour, 0)
                intensity = min(4, int((count / 10) * 4))  # Normalize to 0-4
                heatmap.append({
                    "date": date_str,
                    "hour": hour,
                    "active_count": count,
                    "intensity": intensity
                })
            current_date += timedelta(days=1)
        
        report = {
            "heatmap": heatmap,
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            }
        }
        
        if use_cache:
            await self.cache.set(cache_key, report, ttl=300)
        
        logger.info(f"Services capacity heatmap generated: {len(heatmap)} data points")
        return report

    async def get_services_peak_hours(
        self,
        db: AsyncSession,
        sucursal_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Advanced peak hours analysis with patterns and recommendations.
        """
        from uuid import UUID
        
        cache_key = self.cache._generate_key(
            "services_peak_hours",
            sucursal_id,
            start_date.isoformat() if start_date else None,
            end_date.isoformat() if end_date else None
        )
        
        if use_cache:
            cached = await self.cache.get(cache_key)
            if cached:
                logger.debug(f"Cache HIT for services peak hours: {cache_key}")
                return cached
        
        if not end_date:
            end_date = await self._get_business_date(db, sucursal_id)
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())
        
        sucursal_uuid = None
        if sucursal_id:
            try:
                sucursal_uuid = UUID(sucursal_id)
            except (ValueError, TypeError):
                logger.warning(f"Invalid sucursal_id format: {sucursal_id}")
        
        timezone_str = await self._get_sucursal_timezone(db, sucursal_id)
        
        # Query sales by hour
        sales_query = select(
            self._extract_hour_in_timezone(Sale.created_at, timezone_str).label("sale_hour"),
            func.count(Sale.id).label("sales_count"),
            func.sum(Sale.total_cents).label("revenue_cents")
        ).where(
            and_(
                Sale.tipo == "service",
                Sale.created_at >= start_datetime,
                Sale.created_at <= end_datetime
            )
        )
        
        if sucursal_uuid:
            sales_query = sales_query.where(Sale.sucursal_id == sucursal_uuid)
        
        sales_query = sales_query.group_by(
            self._extract_hour_in_timezone(Sale.created_at, timezone_str)
        )
        
        sales_result = await db.execute(sales_query)
        hourly_data = {
            int(row.sale_hour): {
                "sales_count": int(row.sales_count or 0),
                "revenue_cents": int(row.revenue_cents or 0)
            }
            for row in sales_result.all()
        }
        
        # Generate hourly stats
        peak_hours = []
        for hour in range(24):
            data = hourly_data.get(hour, {"sales_count": 0, "revenue_cents": 0})
            peak_hours.append({
                "hour": hour,
                "sales_count": data["sales_count"],
                "revenue_cents": data["revenue_cents"]
            })
        
        # Sort by sales count
        peak_hours.sort(key=lambda x: x["sales_count"], reverse=True)
        
        # Identify peak periods
        max_sales = max(h["sales_count"] for h in peak_hours) if peak_hours else 0
        peak_threshold = max_sales * 0.7  # 70% of max is considered peak
        
        peak_periods = [h for h in peak_hours if h["sales_count"] >= peak_threshold]
        off_peak_periods = [h for h in peak_hours if h["sales_count"] < max_sales * 0.3]
        
        return {
            "hourly_stats": peak_hours,
            "peak_periods": peak_periods[:5],  # Top 5
            "off_peak_periods": off_peak_periods[:5],
            "summary": {
                "peak_hour": peak_hours[0]["hour"] if peak_hours else None,
                "peak_sales_count": peak_hours[0]["sales_count"] if peak_hours else 0,
                "total_hours_analyzed": 24
            },
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            }
        }

    # ============================================================================
    # SERVICES REPORTS - Phase 4: Patterns and Recommendations
    # ============================================================================

    async def get_services_patterns(
        self,
        db: AsyncSession,
        sucursal_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Analyze demand patterns (day of week, seasonal, etc.).
        """
        from uuid import UUID
        
        cache_key = self.cache._generate_key(
            "services_patterns",
            sucursal_id,
            start_date.isoformat() if start_date else None,
            end_date.isoformat() if end_date else None
        )
        
        if use_cache:
            cached = await self.cache.get(cache_key)
            if cached:
                logger.debug(f"Cache HIT for services patterns: {cache_key}")
                return cached
        
        if not end_date:
            end_date = await self._get_business_date(db, sucursal_id)
        if not start_date:
            start_date = end_date - timedelta(days=90)  # 3 months for patterns
        
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())
        
        sucursal_uuid = None
        if sucursal_id:
            try:
                sucursal_uuid = UUID(sucursal_id)
            except (ValueError, TypeError):
                logger.warning(f"Invalid sucursal_id format: {sucursal_id}")
        
        # Query by day of week
        sales_query = select(
            func.extract('dow', Sale.created_at).label("day_of_week"),
            func.count(Sale.id).label("sales_count"),
            func.sum(Sale.total_cents).label("revenue_cents")
        ).where(
            and_(
                Sale.tipo == "service",
                Sale.created_at >= start_datetime,
                Sale.created_at <= end_datetime
            )
        )
        
        if sucursal_uuid:
            sales_query = sales_query.where(Sale.sucursal_id == sucursal_uuid)
        
        sales_query = sales_query.group_by(func.extract('dow', Sale.created_at))
        
        sales_result = await db.execute(sales_query)
        
        day_names = ["Domingo", "Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"]
        day_patterns = []
        
        for row in sales_result.all():
            dow = int(row.day_of_week)
            day_patterns.append({
                "day_of_week": dow,
                "day_name": day_names[dow],
                "sales_count": int(row.sales_count or 0),
                "revenue_cents": int(row.revenue_cents or 0)
            })
        
        # Fill missing days
        for dow in range(7):
            if not any(p["day_of_week"] == dow for p in day_patterns):
                day_patterns.append({
                    "day_of_week": dow,
                    "day_name": day_names[dow],
                    "sales_count": 0,
                    "revenue_cents": 0
                })
        
        day_patterns.sort(key=lambda x: x["day_of_week"])
        
        return {
            "day_of_week_patterns": day_patterns,
            "summary": {
                "busiest_day": max(day_patterns, key=lambda x: x["sales_count"])["day_name"] if day_patterns else None,
                "quietest_day": min(day_patterns, key=lambda x: x["sales_count"])["day_name"] if day_patterns else None
            },
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            }
        }

    async def get_services_recommendations(
        self,
        db: AsyncSession,
        sucursal_id: Optional[str] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Generate actionable recommendations for services management.
        """
        end_date = await self._get_business_date(db, sucursal_id)
        start_date = end_date - timedelta(days=30)
        
        # Get all relevant data
        utilization_data = await self.get_services_utilization(db, sucursal_id, start_date, end_date, use_cache)
        performance_data = await self.get_services_performance(db, sucursal_id, start_date, end_date, use_cache)
        peak_hours_data = await self.get_services_peak_hours(db, sucursal_id, start_date, end_date, use_cache)
        
        recommendations = []
        
        # High utilization services
        high_util = utilization_data["summary"]["high_utilization_count"]
        if high_util > 0:
            recommendations.append({
                "priority": "high",
                "title": f"{high_util} servicios con alta utilización",
                "description": "Algunos servicios están cerca de su capacidad máxima. Considera aumentar capacidad o ajustar horarios.",
                "action": "Revisar capacidad y horarios de operación"
            })
        
        # Low utilization services
        low_util = utilization_data["summary"]["low_utilization_count"]
        if low_util > 0:
            recommendations.append({
                "priority": "medium",
                "title": f"{low_util} servicios con baja utilización",
                "description": "Algunos servicios tienen poca demanda. Considera promociones o ajustes de marketing.",
                "action": "Desarrollar estrategias de marketing para estos servicios"
            })
        
        # Peak hours recommendations
        if peak_hours_data and peak_hours_data.get("peak_periods"):
            peak_hour = peak_hours_data["summary"]["peak_hour"]
            if peak_hour is not None:
                recommendations.append({
                    "priority": "medium",
                    "title": f"Hora pico identificada: {peak_hour}:00",
                    "description": f"La hora {peak_hour}:00 tiene la mayor demanda. Asegúrate de tener suficiente personal.",
                    "action": "Optimizar asignación de personal para horas pico"
                })
        
        if not recommendations:
            recommendations.append({
                "priority": "info",
                "title": "Servicios en buen estado",
                "description": "No se detectaron problemas críticos en los servicios.",
                "action": "Continuar monitoreando"
            })
        
        return {
            "recommendations": recommendations,
            "summary": f"{len(recommendations)} recomendaciones generadas"
        }


