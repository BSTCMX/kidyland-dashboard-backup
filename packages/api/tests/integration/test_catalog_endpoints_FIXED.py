"""
Integration tests for Catalog endpoints - FIXED VERSION.

This is a corrected version that properly uses create_access_token
and includes all necessary user fixtures.
"""
import pytest
import uuid
from httpx import AsyncClient, ASGITransport
from main import app
from models.user import User
from models.sucursal import Sucursal
from models.product import Product
from models.service import Service
from models.package import Package
from database import get_db
from core.security import create_access_token


# ============================================================================
# HELPER FIXTURES
# ============================================================================

@pytest.fixture
def override_get_db(test_db):
    """Override get_db dependency for testing."""
    async def _get_db():
        yield test_db
    return _get_db


@pytest.fixture(autouse=True)
async def setup_dependencies(override_get_db):
    """Setup dependency overrides before each test."""
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()


# ============================================================================
# TEST SUCURSALES ENDPOINTS
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.integration
class TestSucursalesEndpoints:
    """Tests for Sucursales CRUD endpoints."""

    async def test_get_sucursales_super_admin(
        self,
        test_db,
        test_superadmin: User,
        test_sucursal: Sucursal,
    ):
        """Test GET /sucursales with super_admin role."""
        token = create_access_token(data={"sub": test_superadmin.username})
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                "/sucursales",
                headers={"Authorization": f"Bearer {token}"}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(s["id"] == str(test_sucursal.id) for s in data)

    async def test_get_sucursales_admin_viewer(
        self,
        test_db,
        test_admin_viewer: User,
        test_sucursal: Sucursal,
    ):
        """Test GET /sucursales with admin_viewer role."""
        token = create_access_token(data={"sub": test_admin_viewer.username})
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                "/sucursales",
                headers={"Authorization": f"Bearer {token}"}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_get_sucursales_forbidden_recepcion(
        self,
        test_db,
        test_user: User,
    ):
        """Test GET /sucursales denied for recepcion role."""
        token = create_access_token(data={"sub": test_user.username})
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                "/sucursales",
                headers={"Authorization": f"Bearer {token}"}
            )
        
        assert response.status_code == 403
        data = response.json()
        assert "detail" in data
        assert "Access denied" in data["detail"]

    async def test_get_sucursales_forbidden_kidibar(
        self,
        test_db,
        test_kidibar: User,
    ):
        """Test GET /sucursales denied for kidibar role."""
        token = create_access_token(data={"sub": test_kidibar.username})
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                "/sucursales",
                headers={"Authorization": f"Bearer {token}"}
            )
        
        assert response.status_code == 403

    async def test_get_sucursales_empty_list(
        self,
        test_db,
        test_superadmin: User,
    ):
        """Test GET /sucursales returns empty list when no sucursales exist."""
        from sqlalchemy import select
        result = await test_db.execute(select(Sucursal))
        existing = result.scalars().all()
        for s in existing:
            await test_db.delete(s)
        await test_db.commit()

        token = create_access_token(data={"sub": test_superadmin.username})
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                "/sucursales",
                headers={"Authorization": f"Bearer {token}"}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data == []

    async def test_create_sucursal_super_admin(
        self,
        test_db,
        test_superadmin: User,
    ):
        """Test POST /sucursales with super_admin role."""
        token = create_access_token(data={"sub": test_superadmin.username})
        sucursal_data = {
            "name": "New Sucursal",
            "address": "123 Test Street",
            "timezone": "America/Mexico_City",
            "active": True,
        }
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/sucursales",
                headers={"Authorization": f"Bearer {token}"},
                json=sucursal_data,
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == sucursal_data["name"]
        assert data["address"] == sucursal_data["address"]
        assert "id" in data
        assert data["active"] is True

    async def test_create_sucursal_forbidden_admin_viewer(
        self,
        test_db,
        test_admin_viewer: User,
    ):
        """Test POST /sucursales denied for admin_viewer role."""
        token = create_access_token(data={"sub": test_admin_viewer.username})
        sucursal_data = {
            "name": "New Sucursal",
            "address": "123 Test Street",
        }
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/sucursales",
                headers={"Authorization": f"Bearer {token}"},
                json=sucursal_data,
            )
        
        assert response.status_code == 403

    async def test_create_sucursal_validation_required_fields(
        self,
        test_db,
        test_superadmin: User,
    ):
        """Test POST /sucursales validation for required fields."""
        token = create_access_token(data={"sub": test_superadmin.username})
        # Missing required 'name' field
        invalid_data = {
            "address": "123 Test Street",
        }
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/sucursales",
                headers={"Authorization": f"Bearer {token}"},
                json=invalid_data,
            )
        
        assert response.status_code == 422  # Validation error

    async def test_update_sucursal_super_admin(
        self,
        test_db,
        test_superadmin: User,
        test_sucursal: Sucursal,
    ):
        """Test PUT /sucursales/{id} with super_admin role."""
        token = create_access_token(data={"sub": test_superadmin.username})
        update_data = {
            "name": "Updated Sucursal Name",
            "address": "Updated Address",
        }
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.put(
                f"/sucursales/{test_sucursal.id}",
                headers={"Authorization": f"Bearer {token}"},
                json=update_data,
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["address"] == update_data["address"]
        assert data["id"] == str(test_sucursal.id)

    async def test_update_sucursal_not_found(
        self,
        test_db,
        test_superadmin: User,
    ):
        """Test PUT /sucursales/{id} returns 404 for non-existent sucursal."""
        token = create_access_token(data={"sub": test_superadmin.username})
        non_existent_id = str(uuid.uuid4())
        update_data = {"name": "Updated Name"}
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.put(
                f"/sucursales/{non_existent_id}",
                headers={"Authorization": f"Bearer {token}"},
                json=update_data,
            )
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    async def test_update_sucursal_partial_update(
        self,
        test_db,
        test_superadmin: User,
        test_sucursal: Sucursal,
    ):
        """Test PUT /sucursales/{id} with partial update (only name)."""
        token = create_access_token(data={"sub": test_superadmin.username})
        original_address = test_sucursal.address
        update_data = {"name": "Only Name Updated"}
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.put(
                f"/sucursales/{test_sucursal.id}",
                headers={"Authorization": f"Bearer {token}"},
                json=update_data,
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == update_data["name"]
        # Address should remain unchanged
        assert data["address"] == original_address

    async def test_delete_sucursal_super_admin(
        self,
        test_db,
        test_superadmin: User,
        test_sucursal: Sucursal,
    ):
        """Test DELETE /sucursales/{id} performs soft delete."""
        token = create_access_token(data={"sub": test_superadmin.username})
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.delete(
                f"/sucursales/{test_sucursal.id}",
                headers={"Authorization": f"Bearer {token}"},
            )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        
        # Verify soft delete (active=False)
        await test_db.refresh(test_sucursal)
        assert test_sucursal.active is False

    async def test_delete_sucursal_not_found(
        self,
        test_db,
        test_superadmin: User,
    ):
        """Test DELETE /sucursales/{id} returns 404 for non-existent sucursal."""
        token = create_access_token(data={"sub": test_superadmin.username})
        non_existent_id = str(uuid.uuid4())
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.delete(
                f"/sucursales/{non_existent_id}",
                headers={"Authorization": f"Bearer {token}"},
            )
        
        assert response.status_code == 404

    async def test_delete_sucursal_forbidden_admin_viewer(
        self,
        test_db,
        test_admin_viewer: User,
        test_sucursal: Sucursal,
    ):
        """Test DELETE /sucursales/{id} denied for admin_viewer role."""
        token = create_access_token(data={"sub": test_admin_viewer.username})
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.delete(
                f"/sucursales/{test_sucursal.id}",
                headers={"Authorization": f"Bearer {token}"},
            )
        
        assert response.status_code == 403





























