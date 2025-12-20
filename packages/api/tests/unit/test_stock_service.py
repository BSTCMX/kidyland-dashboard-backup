"""
Unit tests for StockService.
"""
import pytest
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from services.stock_service import StockService
from models.sucursal import Sucursal
from models.product import Product


@pytest.mark.asyncio
@pytest.mark.unit
async def test_get_stock_alerts(
    test_db: AsyncSession,
    test_sucursal: Sucursal,
):
    """Test getting products with stock at or below threshold."""
    # Create product with low stock (below threshold)
    low_stock_product = Product(
        id=uuid.uuid4(),
        sucursal_id=test_sucursal.id,
        name="Low Stock Product",
        price_cents=500,
        stock_qty=3,  # Below threshold
        threshold_alert_qty=5,
        enabled_for_package=False,
        package_deduction_qty=0,
        active=True,
    )
    test_db.add(low_stock_product)

    # Create product with adequate stock
    adequate_product = Product(
        id=uuid.uuid4(),
        sucursal_id=test_sucursal.id,
        name="Adequate Stock Product",
        price_cents=1000,
        stock_qty=10,  # Above threshold
        threshold_alert_qty=5,
        enabled_for_package=False,
        package_deduction_qty=0,
        active=True,
    )
    test_db.add(adequate_product)

    # Create product at threshold
    at_threshold_product = Product(
        id=uuid.uuid4(),
        sucursal_id=test_sucursal.id,
        name="At Threshold Product",
        price_cents=750,
        stock_qty=5,  # At threshold
        threshold_alert_qty=5,
        enabled_for_package=False,
        package_deduction_qty=0,
        active=True,
    )
    test_db.add(at_threshold_product)
    await test_db.commit()

    # Get stock alerts
    alerts = await StockService.get_stock_alerts(
        db=test_db,
        sucursal_id=str(test_sucursal.id),
    )

    # Should return products at or below threshold, ordered by stock ASC
    assert len(alerts) == 2
    assert alerts[0].name == "Low Stock Product"  # Lowest stock first
    assert alerts[0].stock_qty == 3
    assert alerts[1].name == "At Threshold Product"
    assert alerts[1].stock_qty == 5


@pytest.mark.asyncio
@pytest.mark.unit
async def test_get_stock_alerts_excludes_inactive(
    test_db: AsyncSession,
    test_sucursal: Sucursal,
):
    """Test that inactive products are excluded from alerts."""
    # Create inactive product with low stock
    inactive_product = Product(
        id=uuid.uuid4(),
        sucursal_id=test_sucursal.id,
        name="Inactive Product",
        price_cents=500,
        stock_qty=2,
        threshold_alert_qty=5,
        enabled_for_package=False,
        package_deduction_qty=0,
        active=False,  # Inactive
    )
    test_db.add(inactive_product)
    await test_db.commit()

    alerts = await StockService.get_stock_alerts(
        db=test_db,
        sucursal_id=str(test_sucursal.id),
    )

    # Should not include inactive product
    assert len(alerts) == 0

