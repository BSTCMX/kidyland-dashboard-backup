"""
Unit tests for SaleService.
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from services.sale_service import SaleService
from schemas.sale import SaleCreate
from models.user import User
from models.sucursal import Sucursal
from models.service import Service


@pytest.mark.asyncio
@pytest.mark.unit
async def test_create_sale_with_product(
    test_db: AsyncSession,
    test_user: User,
    test_sucursal: Sucursal,
    test_product,
):
    """Test creating a sale with a product item."""
    sale_data = SaleCreate(
        sucursal_id=test_sucursal.id,
        usuario_id=test_user.id,
        tipo="product",
        subtotal_cents=500,
        discount_cents=0,
        total_cents=500,
        payment_method="cash",
        items=[
            {
                "type": "product",
                "ref_id": str(test_product.id),
                "quantity": 1,
                "unit_price_cents": 500,
                "subtotal_cents": 500,
            }
        ],
    )

    sale_response = await SaleService.create_sale(
        db=test_db,
        sale_data=sale_data,
        current_user=test_user,
    )

    sale_id = sale_response["sale_id"]
    assert sale_response["timer_id"] is None  # No timer for product sales
    
    # Fetch sale to verify
    from models.sale import Sale
    sale = await test_db.get(Sale, sale_id)
    assert sale is not None
    assert sale.tipo == "product"
    assert sale.total_cents == 500


@pytest.mark.asyncio
@pytest.mark.unit
async def test_create_sale_with_service_creates_timer(
    test_db: AsyncSession,
    test_user: User,
    test_sucursal: Sucursal,
    test_service: Service,
):
    """Test creating a sale with a service item automatically creates a timer."""
    sale_data = SaleCreate(
        sucursal_id=test_sucursal.id,
        usuario_id=test_user.id,
        tipo="service",
        subtotal_cents=1000,
        discount_cents=0,
        total_cents=1000,
        payment_method="cash",
        child_name="Test Child",  # Required for service sales
        items=[
            {
                "type": "service",
                "ref_id": str(test_service.id),
                "quantity": 1,
                "unit_price_cents": 1000,
                "subtotal_cents": 1000,
                "duration_minutes": 60,
            }
        ],
    )

    sale_response = await SaleService.create_sale(
        db=test_db,
        sale_data=sale_data,
        current_user=test_user,
    )

    sale_id = sale_response["sale_id"]
    timer_id = sale_response["timer_id"]
    
    assert sale_id is not None
    assert timer_id is not None
    
    # Fetch sale and timer to verify
    from models.sale import Sale
    from models.timer import Timer
    sale = await test_db.get(Sale, sale_id)
    timer = await test_db.get(Timer, timer_id)
    
    assert sale is not None
    assert sale.tipo == "service"
    assert timer is not None
    assert timer.sale_id == sale.id
    assert timer.service_id == test_service.id
    assert timer.status == "active"
    assert timer.child_name == "Test Child"
    
    # Verify timer duration (now using timezone-aware datetime)
    from datetime import timezone
    expected_end = datetime.now(timezone.utc) + timedelta(minutes=60)
    assert abs((timer.end_at - expected_end).total_seconds()) < 5  # 5 second tolerance


@pytest.mark.asyncio
@pytest.mark.unit
async def test_create_sale_invalid_service_id(
    test_db: AsyncSession,
    test_user: User,
    test_sucursal: Sucursal,
):
    """Test creating a sale with invalid service ID raises error."""
    import uuid

    sale_data = SaleCreate(
        sucursal_id=test_sucursal.id,
        usuario_id=test_user.id,
        tipo="service",
        subtotal_cents=1000,
        discount_cents=0,
        total_cents=1000,
        payment_method="cash",
        child_name="Test Child",  # Required for service sales
        items=[
            {
                "type": "service",
                "ref_id": str(uuid.uuid4()),  # Non-existent service
                "quantity": 1,
                "unit_price_cents": 1000,
                "subtotal_cents": 1000,
                "duration_minutes": 60,
            }
        ],
    )

    with pytest.raises(ValueError, match="Service.*not found"):
        await SaleService.create_sale(
            db=test_db,
            sale_data=sale_data,
            current_user=test_user,
        )


@pytest.mark.asyncio
@pytest.mark.unit
async def test_create_sale_transaction_rollback_on_error(
    test_db: AsyncSession,
    test_user: User,
    test_sucursal: Sucursal,
):
    """Test that transaction rolls back on error."""
    from sqlalchemy import select
    from models.sale import Sale

    sale_data = SaleCreate(
        sucursal_id=test_sucursal.id,
        usuario_id=test_user.id,
        tipo="product",
        subtotal_cents=500,
        discount_cents=0,
        total_cents=500,
        payment_method="cash",
        items=[
            {
                "type": "product",
                "ref_id": "invalid-uuid",  # This will cause an error
                "quantity": 1,
                "unit_price_cents": 500,
                "subtotal_cents": 500,
            }
        ],
    )

    # Count sales before
    result = await test_db.execute(select(Sale))
    count_before = len(result.scalars().all())

    # Attempt to create sale (should fail)
    try:
        await SaleService.create_sale(
            db=test_db,
            sale_data=sale_data,
            user_id=str(test_user.id),
        )
    except Exception:
        pass  # Expected to fail

    # Count sales after (should be same)
    result = await test_db.execute(select(Sale))
    count_after = len(result.scalars().all())

    assert count_before == count_after, "Transaction should have rolled back"























