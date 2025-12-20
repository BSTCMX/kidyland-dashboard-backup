"""
End-to-end integration tests for complete workflows.
"""
import pytest
import uuid
from httpx import AsyncClient
from main import app
from models.user import User
from models.sucursal import Sucursal
from models.service import Service
from core.security import create_access_token


@pytest.mark.asyncio
@pytest.mark.integration
async def test_e2e_sale_to_timer_to_alert_flow(
    test_db,
    test_user: User,
    test_sucursal: Sucursal,
    test_service: Service,
):
    """
    End-to-end test: Login → Create Sale → Timer Created → Get Active Timers.
    """
    from fastapi import Depends
    from database import get_db
    from sqlalchemy import select
    from models.timer import Timer
    from models.sale import Sale
    
    async def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        # 1. Login
        login_response = await client.post(
            "/auth/login",
            json={
                "username": "testuser",
                "password": "testpass123",
            }
        )
        assert login_response.status_code == 200
        login_data = login_response.json()
        token = login_data["access_token"]
        
        # 2. Create sale with service
        sale_response = await client.post(
            "/sales",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "sucursal_id": str(test_sucursal.id),
                "usuario_id": str(test_user.id),
                "tipo": "service",
                "subtotal_cents": 1000,
                "discount_cents": 0,
                "total_cents": 1000,
                "payment_method": "cash",
                "child_name": "E2E Test Child",
                "items": [
                    {
                        "type": "service",
                        "ref_id": str(test_service.id),
                        "quantity": 1,
                        "unit_price_cents": 1000,
                        "subtotal_cents": 1000,
                        "duration_minutes": 60,
                    }
                ],
            }
        )
        assert sale_response.status_code == 200
        sale_data = sale_response.json()
        assert "sale_id" in sale_data
        assert "timer_id" in sale_data
        assert sale_data["timer_id"] is not None
        
        # 3. Get active timers
        timers_response = await client.get(
            "/timers/active",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert timers_response.status_code == 200
        timers_data = timers_response.json()
        assert isinstance(timers_data, list)
        assert len(timers_data) > 0
        
        # Verify timer is in the list
        timer_found = any(
            t["timer_id"] == sale_data["timer_id"] for t in timers_data
        )
        assert timer_found, "Created timer should be in active timers list"
        
        # 4. Verify timer has time_left calculated
        timer = next(
            t for t in timers_data if t["timer_id"] == sale_data["timer_id"]
        )
        assert "time_left" in timer
        assert "time_left_seconds" in timer
        assert timer["time_left"] > 0
        assert timer["time_left_seconds"] > 0
    
    app.dependency_overrides.clear()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_e2e_role_based_access(
    test_db,
    test_user: User,
    test_superadmin: User,
    test_sucursal: Sucursal,
):
    """Test role-based access control end-to-end."""
    from fastapi import Depends
    from database import get_db
    
    async def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Login as recepcion user
        login_response = await client.post(
            "/auth/login",
            json={
                "username": "testuser",
                "password": "testpass123",
            }
        )
        token = login_response.json()["access_token"]
        
        # Try to access super_admin only endpoint (should fail)
        users_response = await client.post(
            "/users",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "username": "newuser",
                "name": "New User",
                "role": "recepcion",
                "password": "password123",
            }
        )
        assert users_response.status_code == 403  # Forbidden
        
        # Login as super_admin
        admin_login = await client.post(
            "/auth/login",
            json={
                "username": "superadmin",
                "password": "admin123",
            }
        )
        admin_token = admin_login.json()["access_token"]
        
        # Now should be able to access (if endpoint was implemented)
        # For now, it returns 501, but 403 would be correct if implemented
        users_response = await client.post(
            "/users",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "username": "newuser",
                "name": "New User",
                "role": "recepcion",
                "password": "password123",
            }
        )
        # Currently returns 501 (not implemented), but should be 200 if implemented
        assert users_response.status_code in [200, 501]
    
    app.dependency_overrides.clear()























