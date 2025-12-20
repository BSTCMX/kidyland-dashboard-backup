"""
Factory functions for creating test data.

Provides consistent, reusable factories for all test models.
"""
import uuid
from datetime import datetime, timedelta, date
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User, UserRole
from models.sucursal import Sucursal
from models.service import Service
from models.product import Product
from models.package import Package
from models.sale import Sale
from models.timer import Timer
from models.day_start import DayStart
from models.day_close import DayClose
from core.security import get_password_hash


# ============================================================================
# USER FACTORIES
# ============================================================================

async def create_test_user(
    db: AsyncSession,
    username: str = "testuser",
    name: str = "Test User",
    role: UserRole = UserRole.RECEPCION,
    password: str = "TestPass123",
    is_active: bool = True,
    sucursal_id: Optional[uuid.UUID] = None,
) -> User:
    """Create a test user with specified role."""
    user = User(
        id=uuid.uuid4(),
        username=username,
        name=name,
        role=role,
        password_hash=get_password_hash(password),
        is_active=is_active,
        sucursal_id=sucursal_id,
    )
    db.add(user)
    await db.flush()  # Flush to get ID, but don't commit - let tests control transactions
    await db.refresh(user)
    return user


async def create_super_admin(
    db: AsyncSession,
    username: str = "superadmin",
    password: str = "AdminPass123",
    sucursal_id: Optional[uuid.UUID] = None,
) -> User:
    """Create a super admin user."""
    return await create_test_user(
        db=db,
        username=username,
        name="Super Admin",
        role=UserRole.SUPER_ADMIN,
        password=password,
        sucursal_id=sucursal_id,
    )


async def create_admin_viewer(
    db: AsyncSession,
    username: str = "adminviewer",
    password: str = "ViewerPass123",
    sucursal_id: Optional[uuid.UUID] = None,
) -> User:
    """Create an admin viewer user."""
    return await create_test_user(
        db=db,
        username=username,
        name="Admin Viewer",
        role=UserRole.ADMIN_VIEWER,
        password=password,
        sucursal_id=sucursal_id,
    )


async def create_recepcion_user(
    db: AsyncSession,
    username: str = "recepcion",
    password: str = "RecepcionPass123",
    sucursal_id: Optional[uuid.UUID] = None,
) -> User:
    """Create a recepcion user."""
    return await create_test_user(
        db=db,
        username=username,
        name="Recepcion User",
        role=UserRole.RECEPCION,
        password=password,
        sucursal_id=sucursal_id,
    )


async def create_kidibar_user(
    db: AsyncSession,
    username: str = "kidibar",
    password: str = "KidibarPass123",
    sucursal_id: Optional[uuid.UUID] = None,
) -> User:
    """Create a kidibar user."""
    return await create_test_user(
        db=db,
        username=username,
        name="Kidibar User",
        role=UserRole.KIDIBAR,
        password=password,
        sucursal_id=sucursal_id,
    )


async def create_monitor_user(
    db: AsyncSession,
    username: str = "monitor",
    password: str = "MonitorPass123",
    sucursal_id: Optional[uuid.UUID] = None,
) -> User:
    """Create a monitor user."""
    return await create_test_user(
        db=db,
        username=username,
        name="Monitor User",
        role=UserRole.MONITOR,
        password=password,
        sucursal_id=sucursal_id,
    )


# ============================================================================
# SUCURSAL FACTORIES
# ============================================================================

async def create_test_sucursal(
    db: AsyncSession,
    name: str = "Test Sucursal",
    address: Optional[str] = "Test Address 123",
    timezone: str = "America/Mexico_City",
    active: bool = True,
    identifier: Optional[str] = None,
) -> Sucursal:
    """Create a test sucursal."""
    # Generate a unique identifier if not provided
    if identifier is None:
        identifier = f"test-{uuid.uuid4().hex[:8]}"
    
    sucursal = Sucursal(
        id=uuid.uuid4(),
        identifier=identifier,
        name=name,
        address=address,
        timezone=timezone,
        active=active,
    )
    db.add(sucursal)
    await db.flush()  # Flush to get ID, but don't commit - let tests control transactions
    await db.refresh(sucursal)
    return sucursal


# ============================================================================
# SERVICE FACTORIES
# ============================================================================

async def create_test_service(
    db: AsyncSession,
    sucursal_id: uuid.UUID,
    name: str = "Test Service",
    durations_allowed: list[int] = None,
    duration_prices: dict[int, int] = None,  # {duration_minutes: price_cents}
    alerts_config: list[dict] = None,
    active: bool = True,
) -> Service:
    """Create a test service."""
    if durations_allowed is None:
        durations_allowed = [30, 60, 90]
    if duration_prices is None:
        # Default: 1000 cents (10.00) for each duration
        duration_prices = {duration: 1000 for duration in durations_allowed}
    if alerts_config is None:
        alerts_config = [
            {"minutes_before": 15},
            {"minutes_before": 10},
            {"minutes_before": 5},
        ]

    service = Service(
        id=uuid.uuid4(),
        sucursal_id=sucursal_id,
        name=name,
        durations_allowed=durations_allowed,
        duration_prices=duration_prices,
        alerts_config=alerts_config,
        active=active,
    )
    db.add(service)
    await db.flush()  # Flush to get ID, but don't commit - let tests control transactions
    await db.refresh(service)
    return service


# ============================================================================
# PRODUCT FACTORIES
# ============================================================================

async def create_test_product(
    db: AsyncSession,
    sucursal_id: uuid.UUID,
    name: str = "Test Product",
    price_cents: int = 500,  # 5.00
    stock_qty: int = 10,
    threshold_alert_qty: int = 5,
    enabled_for_package: bool = False,
    package_deduction_qty: int = 0,
    active: bool = True,
) -> Product:
    """Create a test product."""
    product = Product(
        id=uuid.uuid4(),
        sucursal_id=sucursal_id,
        name=name,
        price_cents=price_cents,
        stock_qty=stock_qty,
        threshold_alert_qty=threshold_alert_qty,
        enabled_for_package=enabled_for_package,
        package_deduction_qty=package_deduction_qty,
        active=active,
    )
    db.add(product)
    await db.flush()  # Flush to get ID, but don't commit - let tests control transactions
    await db.refresh(product)
    return product


# ============================================================================
# PACKAGE FACTORIES
# ============================================================================

async def create_test_package(
    db: AsyncSession,
    sucursal_id: uuid.UUID,
    name: str = "Test Package",
    description: Optional[str] = "Test package description",
    price_cents: int = 2000,  # 20.00
    included_items: list[dict] = None,
    active: bool = True,
) -> Package:
    """Create a test package."""
    if included_items is None:
        included_items = []

    package = Package(
        id=uuid.uuid4(),
        sucursal_id=sucursal_id,
        name=name,
        description=description,
        price_cents=price_cents,
        included_items=included_items,
        active=active,
    )
    db.add(package)
    await db.flush()  # Flush to get ID, but don't commit - let tests control transactions
    await db.refresh(package)
    return package


# ============================================================================
# SALE FACTORIES
# ============================================================================

async def create_test_sale(
    db: AsyncSession,
    sucursal_id: uuid.UUID,
    user_id: uuid.UUID,
    tipo: str = "service",
    total_cents: int = 1000,
    payment_method: str = "cash",
    payer_name: Optional[str] = "Test Payer",
    payer_phone: Optional[str] = None,
    payer_signature: Optional[str] = None,
    subtotal_cents: Optional[int] = None,
    discount_cents: int = 0,
) -> Sale:
    """Create a test sale."""
    if subtotal_cents is None:
        subtotal_cents = total_cents
    
    sale = Sale(
        id=uuid.uuid4(),
        sucursal_id=sucursal_id,
        usuario_id=user_id,
        tipo=tipo,
        subtotal_cents=subtotal_cents,
        discount_cents=discount_cents,
        total_cents=total_cents,
        payment_method=payment_method,
        payer_name=payer_name,
        payer_phone=payer_phone,
        payer_signature=payer_signature,
    )
    db.add(sale)
    await db.flush()  # Flush to get ID, but don't commit - let tests control transactions
    await db.refresh(sale)
    return sale


# ============================================================================
# TIMER FACTORIES
# ============================================================================

async def create_test_timer(
    db: AsyncSession,
    sale_id: uuid.UUID,
    service_id: uuid.UUID,
    duration_minutes: int = 60,
    start_delay_minutes: int = 0,
    child_name: Optional[str] = "Test Child",
    child_age: Optional[int] = 5,
    status: str = "active",
    start_at: Optional[datetime] = None,
    end_at: Optional[datetime] = None,
) -> Timer:
    """Create a test timer."""
    now = datetime.utcnow()
    if start_at is None:
        start_at = now + timedelta(minutes=start_delay_minutes)
    if end_at is None:
        end_at = start_at + timedelta(minutes=duration_minutes)

    timer = Timer(
        id=uuid.uuid4(),
        sale_id=sale_id,
        service_id=service_id,
        start_delay_minutes=start_delay_minutes,
        child_name=child_name,
        child_age=child_age,
        status=status,
        start_at=start_at,
        end_at=end_at,
    )
    db.add(timer)
    await db.flush()  # Flush to get ID, but don't commit - let tests control transactions
    await db.refresh(timer)
    return timer


# ============================================================================
# DAY START FACTORIES
# ============================================================================

async def create_test_day_start(
    db: AsyncSession,
    sucursal_id: uuid.UUID,
    user_id: uuid.UUID,
    initial_cash_cents: int = 10000,  # 100.00
    is_active: bool = True,
    started_at: Optional[datetime] = None,
) -> DayStart:
    """Create a test day start."""
    if started_at is None:
        started_at = datetime.utcnow()

    day_start = DayStart(
        id=uuid.uuid4(),
        sucursal_id=sucursal_id,
        usuario_id=user_id,
        initial_cash_cents=initial_cash_cents,
        is_active=is_active,
        started_at=started_at,
    )
    db.add(day_start)
    await db.flush()  # Flush to get ID, but don't commit - let tests control transactions
    await db.refresh(day_start)
    return day_start


# ============================================================================
# DAY CLOSE FACTORIES
# ============================================================================

async def create_test_day_close(
    db: AsyncSession,
    sucursal_id: uuid.UUID,
    user_id: uuid.UUID,
    close_date: Optional[date] = None,
    system_total_cents: int = 0,
    physical_count_cents: int = 10000,  # 100.00
    difference_cents: Optional[int] = None,
    totals: Optional[dict] = None,
) -> DayClose:
    """Create a test day close."""
    if close_date is None:
        close_date = date.today()
    if difference_cents is None:
        difference_cents = physical_count_cents - system_total_cents
    if totals is None:
        totals = {}

    day_close = DayClose(
        id=uuid.uuid4(),
        sucursal_id=sucursal_id,
        usuario_id=user_id,
        date=close_date,
        system_total_cents=system_total_cents,
        physical_count_cents=physical_count_cents,
        difference_cents=difference_cents,
        totals=totals,
    )
    db.add(day_close)
    await db.flush()  # Flush to get ID, but don't commit - let tests control transactions
    await db.refresh(day_close)
    return day_close

