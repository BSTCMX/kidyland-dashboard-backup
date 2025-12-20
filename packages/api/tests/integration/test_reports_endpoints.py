"""
Integration tests for reports endpoints.
"""
import pytest
import time
import uuid
from httpx import AsyncClient
from main import app
from models.user import User
from models.sucursal import Sucursal
from models.sale import Sale
from models.product import Product
from models.service import Service
from models.timer import Timer
from datetime import datetime, timedelta
from core.security import create_access_token


@pytest.mark.asyncio
@pytest.mark.integration
async def test_refresh_metrics_success(
    test_db,
    test_superadmin: User,
    test_sucursal: Sucursal,
):
    """Test successful metrics refresh."""
    from fastapi import Depends
    from database import get_db
    
    async def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    # Create token
    token = create_access_token(data={"sub": test_superadmin.username})
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/reports/refresh",
            headers={"Authorization": f"Bearer {token}"},
            params={"sucursal_id": str(test_sucursal.id)},
        )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "metrics" in data
    assert "sales" in data["metrics"]
    assert "stock" in data["metrics"]
    assert "services" in data["metrics"]
    assert data["elapsed_seconds"] >= 0
    assert data["refresh_count"] == 1
    
    app.dependency_overrides.clear()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_refresh_metrics_rate_limit(
    test_db,
    test_superadmin: User,
    test_sucursal: Sucursal,
):
    """Test refresh rate limit (2 seconds minimum)."""
    from fastapi import Depends
    from database import get_db
    
    async def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    token = create_access_token(data={"sub": test_superadmin.username})
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        # First refresh
        response1 = await client.post(
            "/reports/refresh",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response1.status_code == 200
        
        # Immediate second refresh (should fail)
        response2 = await client.post(
            "/reports/refresh",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response2.status_code == 429
        assert "wait" in response2.json()["detail"].lower()
    
    app.dependency_overrides.clear()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_refresh_metrics_max_limit(
    test_db,
    test_superadmin: User,
):
    """Test refresh maximum limit (30 refreshes)."""
    from fastapi import Depends
    from database import get_db
    from routers.reports import _refresh_state
    
    async def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    token = create_access_token(data={"sub": test_superadmin.username})
    user_id = str(test_superadmin.id)
    
    # Set refresh count to 30
    _refresh_state[user_id] = {
        "refresh_in_progress": False,
        "last_refresh": time.time() - 3,  # 3 seconds ago
        "refresh_count": 30
    }
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/reports/refresh",
            headers={"Authorization": f"Bearer {token}"},
        )
        
        assert response.status_code == 429
        assert "limit" in response.json()["detail"].lower()
    
    # Cleanup
    if user_id in _refresh_state:
        del _refresh_state[user_id]
    
    app.dependency_overrides.clear()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_refresh_metrics_force_invalidate_cache(
    test_db,
    test_superadmin: User,
    test_sucursal: Sucursal,
):
    """Test that force=True invalidates cache."""
    from fastapi import Depends
    from database import get_db
    from services.analytics_cache import get_cache
    
    async def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    # Set some cache
    cache = get_cache()
    await cache.set("sales:test", {"value": 123})
    
    token = create_access_token(data={"sub": test_superadmin.username})
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/reports/refresh",
            headers={"Authorization": f"Bearer {token}"},
            params={"force": True, "sucursal_id": str(test_sucursal.id)},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["cache_invalidated"] is True
    
    app.dependency_overrides.clear()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_sales_report(
    test_db,
    test_superadmin: User,
    test_sucursal: Sucursal,
):
    """Test GET /reports/sales endpoint."""
    from fastapi import Depends
    from database import get_db
    
    async def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    token = create_access_token(data={"sub": test_superadmin.username})
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/reports/sales",
            headers={"Authorization": f"Bearer {token}"},
            params={"sucursal_id": str(test_sucursal.id)},
        )
    
    assert response.status_code == 200
    data = response.json()
    assert "total_revenue_cents" in data
    assert "average_transaction_value_cents" in data
    assert "sales_count" in data
    
    app.dependency_overrides.clear()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_generate_predictions_success(
    test_db,
    test_superadmin: User,
    test_sucursal: Sucursal,
):
    """Test successful predictions generation."""
    from fastapi import Depends
    from database import get_db
    
    async def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    token = create_access_token(data={"sub": test_superadmin.username})
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/reports/predictions/generate",
            headers={"Authorization": f"Bearer {token}"},
            params={
                "sucursal_id": str(test_sucursal.id),
                "forecast_days": 7,
                "prediction_type": "all",
            },
        )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "predictions" in data
    assert "confidence" in data
    assert data["forecast_days"] == 7
    assert data["elapsed_seconds"] >= 0
    
    app.dependency_overrides.clear()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_generate_predictions_rate_limit(
    test_db,
    test_superadmin: User,
):
    """Test predictions rate limit (5 seconds minimum)."""
    from fastapi import Depends
    from database import get_db
    
    async def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    token = create_access_token(data={"sub": test_superadmin.username})
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        # First prediction
        response1 = await client.post(
            "/reports/predictions/generate",
            headers={"Authorization": f"Bearer {token}"},
            params={"forecast_days": 7},
        )
        assert response1.status_code == 200
        
        # Immediate second prediction (should fail)
        response2 = await client.post(
            "/reports/predictions/generate",
            headers={"Authorization": f"Bearer {token}"},
            params={"forecast_days": 7},
        )
        assert response2.status_code == 429
        assert "wait" in response2.json()["detail"].lower()
    
    app.dependency_overrides.clear()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_generate_predictions_invalid_type(
    test_db,
    test_superadmin: User,
):
    """Test predictions with invalid prediction_type."""
    from fastapi import Depends
    from database import get_db
    
    async def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    token = create_access_token(data={"sub": test_superadmin.username})
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/reports/predictions/generate",
            headers={"Authorization": f"Bearer {token}"},
            params={"prediction_type": "invalid_type"},
        )
        
        assert response.status_code == 400
        assert "invalid" in response.json()["detail"].lower()
    
    app.dependency_overrides.clear()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_generate_predictions_forecast_days_validation(
    test_db,
    test_superadmin: User,
):
    """Test predictions forecast_days validation (1-30)."""
    from fastapi import Depends
    from database import get_db
    
    async def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    token = create_access_token(data={"sub": test_superadmin.username})
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Test with forecast_days=0 (should fail)
        response1 = await client.post(
            "/reports/predictions/generate",
            headers={"Authorization": f"Bearer {token}"},
            params={"forecast_days": 0},
        )
        assert response1.status_code == 422  # Validation error
        
        # Test with forecast_days=31 (should fail)
        response2 = await client.post(
            "/reports/predictions/generate",
            headers={"Authorization": f"Bearer {token}"},
            params={"forecast_days": 31},
        )
        assert response2.status_code == 422
        
        # Test with forecast_days=15 (should succeed)
        response3 = await client.post(
            "/reports/predictions/generate",
            headers={"Authorization": f"Bearer {token}"},
            params={"forecast_days": 15},
        )
        assert response3.status_code == 200
    
    app.dependency_overrides.clear()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_reports_endpoints_require_auth(test_db):
    """Test that reports endpoints require authentication."""
    from fastapi import Depends
    from database import get_db
    
    async def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Test refresh without auth
        response1 = await client.post("/reports/refresh")
        assert response1.status_code == 401
        
        # Test predictions without auth
        response2 = await client.post("/reports/predictions/generate")
        assert response2.status_code == 401
        
        # Test GET endpoints without auth
        response3 = await client.get("/reports/sales")
        assert response3.status_code == 401
    
    app.dependency_overrides.clear()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_reports_endpoints_require_role(
    test_db,
    test_user: User,  # recepcion role (not allowed)
):
    """Test that reports endpoints require super_admin or admin_viewer role."""
    from fastapi import Depends
    from database import get_db
    
    async def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    token = create_access_token(data={"sub": test_user.username})
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Test refresh with recepcion role (should fail)
        response1 = await client.post(
            "/reports/refresh",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response1.status_code == 403
        
        # Test predictions with recepcion role (should fail)
        response2 = await client.post(
            "/reports/predictions/generate",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response2.status_code == 403
    
    app.dependency_overrides.clear()


