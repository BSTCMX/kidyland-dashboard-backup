"""
Unit tests for DayCloseService.
"""
import pytest
import uuid
from datetime import date, datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from services.day_close_service import DayCloseService
from schemas.day_close import DayCloseCreate
from models.user import User
from models.sucursal import Sucursal
from models.sale import Sale


@pytest.mark.asyncio
@pytest.mark.unit
async def test_close_day_calculates_totals(
    test_db: AsyncSession,
    test_user: User,
    test_sucursal: Sucursal,
):
    """Test that day close calculates system totals from sales."""
    # Create sales for today
    today = date.today()
    start_of_day = datetime.combine(today, datetime.min.time())
    end_of_day = datetime.combine(today, datetime.max.time())

    # Create sale 1
    sale1 = Sale(
        id=uuid.uuid4(),
        sucursal_id=test_sucursal.id,
        usuario_id=test_user.id,
        tipo="product",
        subtotal_cents=1000,
        discount_cents=0,
        total_cents=1000,
        payment_method="cash",
        cash_received_cents=1000,
        created_at=start_of_day + timedelta(hours=10),
    )
    test_db.add(sale1)

    # Create sale 2
    sale2 = Sale(
        id=uuid.uuid4(),
        sucursal_id=test_sucursal.id,
        usuario_id=test_user.id,
        tipo="service",
        subtotal_cents=2000,
        discount_cents=100,
        total_cents=1900,
        payment_method="card",
        created_at=start_of_day + timedelta(hours=14),
    )
    test_db.add(sale2)
    await test_db.commit()

    # Close day
    close_data = DayCloseCreate(
        sucursal_id=test_sucursal.id,
        usuario_id=test_user.id,
        date=today,
        system_total_cents=0,  # Will be calculated
        physical_count_cents=3000,
        difference_cents=0,  # Will be calculated
    )

    day_close = await DayCloseService.close_day(
        db=test_db,
        close_data=close_data,
        user_id=str(test_user.id),
    )

    # Verify calculations
    assert day_close.system_total_cents == 2900  # 1000 + 1900
    assert day_close.physical_count_cents == 3000
    assert day_close.difference_cents == 100  # 3000 - 2900
    assert day_close.totals is not None
    assert day_close.totals["sale_count"] == 2


@pytest.mark.asyncio
@pytest.mark.unit
async def test_close_day_with_no_sales(
    test_db: AsyncSession,
    test_user: User,
    test_sucursal: Sucursal,
):
    """Test closing day with no sales."""
    today = date.today()

    close_data = DayCloseCreate(
        sucursal_id=test_sucursal.id,
        usuario_id=test_user.id,
        date=today,
        system_total_cents=0,
        physical_count_cents=0,
        difference_cents=0,
    )

    day_close = await DayCloseService.close_day(
        db=test_db,
        close_data=close_data,
        user_id=str(test_user.id),
    )

    assert day_close.system_total_cents == 0
    assert day_close.physical_count_cents == 0
    assert day_close.difference_cents == 0
    assert day_close.totals["sale_count"] == 0

