"""
Integration tests for timers endpoints.
"""
import pytest
import uuid
from httpx import AsyncClient
from main import app
from models.user import User
from models.sucursal import Sucursal
from models.service import Service
from models.sale import Sale
from models.timer import Timer
from datetime import datetime, timedelta
from core.security import create_access_token


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_active_timers(
    test_db,
    test_user: User,
    test_sucursal: Sucursal,
    test_service: Service,
):
    """Test getting active timers with time_left calculated."""
    from fastapi import Depends
    from database import get_db
    
    async def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    # Create sale and active timer
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
    
    timer = Timer(
        id=uuid.uuid4(),
        sale_id=sale.id,
        service_id=test_service.id,
        start_at=datetime.utcnow(),
        end_at=datetime.utcnow() + timedelta(minutes=30),
        status="active",
        child_name="Test Child",
    )
    test_db.add(timer)
    await test_db.commit()
    
    # Create token
    token = create_access_token(data={"sub": test_user.username})
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/timers/active",
            headers={"Authorization": f"Bearer {token}"},
        )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "timer_id" in data[0]
    assert "time_left" in data[0]
    assert "time_left_seconds" in data[0]
    assert data[0]["status"] == "active"
    
    app.dependency_overrides.clear()

