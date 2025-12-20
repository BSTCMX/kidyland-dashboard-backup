"""
Unit tests for TimerService.
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from services.timer_service import TimerService
from models.timer import Timer
from models.sale import Sale
from models.service import Service
from models.user import User
from models.sucursal import Sucursal


@pytest.mark.asyncio
@pytest.mark.unit
async def test_extend_timer(
    test_db: AsyncSession,
    test_user: User,
    test_sucursal: Sucursal,
    test_service: Service,
):
    """Test extending an active timer."""
    import uuid
    # Create a sale first
    sale = Sale(
        id=uuid.uuid4(),
        sucursal_id=test_sucursal.id,
        usuario_id=test_user.id,
        tipo="service",
        subtotal_cents=1000,
        discount_cents=0,
        total_cents=1000,
        payment_method="cash",
    )
    test_db.add(sale)
    await test_db.flush()

    # Create an active timer
    start_at = datetime.utcnow()
    end_at = start_at + timedelta(minutes=60)
    timer = Timer(
        id=uuid.uuid4(),
        sale_id=sale.id,
        service_id=test_service.id,
        start_at=start_at,
        end_at=end_at,
        status="active",
    )
    test_db.add(timer)
    await test_db.commit()
    await test_db.refresh(timer)

    original_end_at = timer.end_at

    # Extend timer by 30 minutes
    extended_timer = await TimerService.extend_timer(
        db=test_db,
        timer_id=str(timer.id),
        minutes_to_add=30,
    )

    assert extended_timer.end_at == original_end_at + timedelta(minutes=30)
    assert extended_timer.status == "extended"

    # Verify timer history was created
    from sqlalchemy import select
    from models.timer_history import TimerHistory

    result = await test_db.execute(
        select(TimerHistory).where(TimerHistory.timer_id == timer.id)
    )
    history = result.scalars().all()
    assert len(history) > 0
    assert any(h.event_type == "extend" for h in history)


@pytest.mark.asyncio
@pytest.mark.unit
async def test_extend_timer_not_active_raises_error(
    test_db: AsyncSession,
    test_user: User,
    test_sucursal: Sucursal,
    test_service: Service,
):
    """Test that extending a non-active timer raises error."""
    import uuid
    # Create a sale
    sale = Sale(
        id=uuid.uuid4(),
        sucursal_id=test_sucursal.id,
        usuario_id=test_user.id,
        tipo="service",
        subtotal_cents=1000,
        discount_cents=0,
        total_cents=1000,
        payment_method="cash",
    )
    test_db.add(sale)
    await test_db.flush()

    # Create an ended timer
    start_at = datetime.utcnow() - timedelta(hours=2)
    end_at = start_at + timedelta(minutes=60)
    timer = Timer(
        id=uuid.uuid4(),
        sale_id=sale.id,
        service_id=test_service.id,
        start_at=start_at,
        end_at=end_at,
        status="ended",
    )
    test_db.add(timer)
    await test_db.commit()

    with pytest.raises(ValueError, match="not active"):
        await TimerService.extend_timer(
            db=test_db,
            timer_id=str(timer.id),
            minutes_to_add=30,
        )


@pytest.mark.asyncio
@pytest.mark.unit
async def test_get_active_timers(
    test_db: AsyncSession,
    test_user: User,
    test_sucursal: Sucursal,
    test_service: Service,
):
    """Test getting active timers."""
    import uuid
    # Create a sale
    sale = Sale(
        id=uuid.uuid4(),
        sucursal_id=test_sucursal.id,
        usuario_id=test_user.id,
        tipo="service",
        subtotal_cents=1000,
        discount_cents=0,
        total_cents=1000,
        payment_method="cash",
    )
    test_db.add(sale)
    await test_db.flush()

    # Create active timer
    start_at = datetime.utcnow()
    end_at = start_at + timedelta(minutes=60)
    active_timer = Timer(
        id=uuid.uuid4(),
        sale_id=sale.id,
        service_id=test_service.id,
        start_at=start_at,
        end_at=end_at,
        status="active",
    )
    test_db.add(active_timer)

    # Create ended timer
    old_start = datetime.utcnow() - timedelta(hours=2)
    old_end = old_start + timedelta(minutes=60)
    ended_timer = Timer(
        id=uuid.uuid4(),
        sale_id=sale.id,
        service_id=test_service.id,
        start_at=old_start,
        end_at=old_end,
        status="ended",
    )
    test_db.add(ended_timer)
    await test_db.commit()

    # Get active timers
    active_timers = await TimerService.get_active_timers(db=test_db)

    assert len(active_timers) == 1
    assert active_timers[0].id == active_timer.id
    assert active_timers[0].status == "active"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_get_timers_with_time_left(
    test_db: AsyncSession,
    test_user: User,
    test_sucursal: Sucursal,
    test_service: Service,
):
    """Test getting timers with calculated time_left."""
    import uuid
    # Create a sale
    sale = Sale(
        id=uuid.uuid4(),
        sucursal_id=test_sucursal.id,
        usuario_id=test_user.id,
        tipo="service",
        subtotal_cents=1000,
        discount_cents=0,
        total_cents=1000,
        payment_method="cash",
    )
    test_db.add(sale)
    await test_db.flush()

    # Create active timer with 30 minutes remaining
    start_at = datetime.utcnow()
    end_at = start_at + timedelta(minutes=30)
    timer = Timer(
        id=uuid.uuid4(),
        sale_id=sale.id,
        service_id=test_service.id,
        start_at=start_at,
        end_at=end_at,
        status="active",
    )
    test_db.add(timer)
    await test_db.commit()

    # Get timers with time_left
    timer_data = await TimerService.get_timers_with_time_left(db=test_db)

    assert len(timer_data) == 1
    assert timer_data[0]["id"] == str(timer.id)
    # Allow 1 minute tolerance for timing differences between creation and query
    assert 29 <= timer_data[0]["time_left_minutes"] <= 30
    assert timer_data[0]["status"] == "active"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_get_timers_nearing_end(
    test_db: AsyncSession,
    test_user: User,
    test_sucursal: Sucursal,
    test_service: Service,
):
    """Test getting timers that are ending soon."""
    import uuid
    # Create a sale
    sale = Sale(
        id=uuid.uuid4(),
        sucursal_id=test_sucursal.id,
        usuario_id=test_user.id,
        tipo="service",
        subtotal_cents=1000,
        discount_cents=0,
        total_cents=1000,
        payment_method="cash",
    )
    test_db.add(sale)
    await test_db.flush()

    # Create timer ending in 3 minutes (within 5 minute threshold)
    start_at = datetime.utcnow()
    end_at = start_at + timedelta(minutes=3)
    near_end_timer = Timer(
        id=uuid.uuid4(),
        sale_id=sale.id,
        service_id=test_service.id,
        start_at=start_at,
        end_at=end_at,
        status="active",
    )
    test_db.add(near_end_timer)

    # Create timer ending in 10 minutes (outside threshold)
    end_at_far = start_at + timedelta(minutes=10)
    far_timer = Timer(
        id=uuid.uuid4(),
        sale_id=sale.id,
        service_id=test_service.id,
        start_at=start_at,
        end_at=end_at_far,
        status="active",
    )
    test_db.add(far_timer)
    await test_db.commit()

    # Get timers nearing end (5 minute threshold)
    alert_timers = await TimerService.get_timers_nearing_end(
        db=test_db,
        minutes_before=5,
    )

    assert len(alert_timers) == 1
    assert alert_timers[0]["id"] == str(near_end_timer.id)

