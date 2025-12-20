"""
Integration tests for user management endpoints.

Tests cover:
- POST /users - Create user
- GET /users - List users
- GET /users/{id} - Get user
- PUT /users/{id} - Update user
- DELETE /users/{id} - Delete user
- POST /users/{id}/change-password - Change password
- POST /users/{id}/deactivate - Deactivate user
- POST /users/{id}/activate - Activate user
- GET /users/me - Get current user profile

Security and authorization tests included.
"""
import pytest
import uuid
from httpx import AsyncClient
from main import app
from models.user import User, UserRole
from core.security import create_access_token


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_user_success(
    test_db,
    test_superadmin: User
):
    """Test successful user creation via endpoint."""
    from fastapi import Depends
    from database import get_db
    
    async def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    token = create_access_token(data={"sub": test_superadmin.username})
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/users",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "username": "newuser",
                "name": "New User",
                "role": "recepcion",
                "password": "NewPass123"
            }
        )
    
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "newuser"
    assert data["role"] == "recepcion"
    assert "id" in data
    assert "password" not in data  # Password should not be in response
    
    app.dependency_overrides.clear()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_user_duplicate_username(
    test_db,
    test_superadmin: User,
    test_user: User
):
    """Test that creating user with duplicate username returns 400."""
    from fastapi import Depends
    from database import get_db
    
    async def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    token = create_access_token(data={"sub": test_superadmin.username})
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/users",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "username": "testuser",  # Already exists
                "name": "Duplicate",
                "role": "recepcion",
                "password": "NewPass123"
            }
        )
    
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"].lower()
    
    app.dependency_overrides.clear()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_user_invalid_password(
    test_db,
    test_superadmin: User
):
    """Test that invalid password returns validation error."""
    from fastapi import Depends
    from database import get_db
    
    async def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    token = create_access_token(data={"sub": test_superadmin.username})
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/users",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "username": "newuser",
                "name": "New User",
                "role": "recepcion",
                "password": "short"  # Invalid: too short, no uppercase, no number
            }
        )
    
    assert response.status_code == 422  # Validation error
    detail = str(response.json())
    assert "password" in detail.lower() or "validation" in detail.lower()
    
    app.dependency_overrides.clear()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_user_invalid_username_too_short(
    test_db,
    test_superadmin: User
):
    """Test that username too short returns validation error."""
    from fastapi import Depends
    from database import get_db
    
    async def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    token = create_access_token(data={"sub": test_superadmin.username})
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/users",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "username": "ab",  # Too short (min 3 chars)
                "name": "New User",
                "role": "recepcion",
                "password": "NewPass123"
            }
        )
    
    assert response.status_code == 422  # Validation error
    detail = str(response.json())
    assert "username" in detail.lower() or "validation" in detail.lower()
    
    app.dependency_overrides.clear()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_user_invalid_username_special_chars(
    test_db,
    test_superadmin: User
):
    """Test that username with special characters returns validation error."""
    from fastapi import Depends
    from database import get_db
    
    async def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    token = create_access_token(data={"sub": test_superadmin.username})
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/users",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "username": "user@name",  # Invalid: contains @
                "name": "New User",
                "role": "recepcion",
                "password": "NewPass123"
            }
        )
    
    assert response.status_code == 422  # Validation error
    detail = str(response.json())
    assert "username" in detail.lower() or "validation" in detail.lower()
    
    app.dependency_overrides.clear()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_user_invalid_role(
    test_db,
    test_superadmin: User
):
    """Test that invalid role returns validation error."""
    from fastapi import Depends
    from database import get_db
    
    async def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    token = create_access_token(data={"sub": test_superadmin.username})
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/users",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "username": "newuser",
                "name": "New User",
                "role": "invalid_role",  # Invalid role
                "password": "NewPass123"
            }
        )
    
    assert response.status_code == 422  # Validation error
    detail = str(response.json())
    assert "role" in detail.lower() or "validation" in detail.lower()
    
    app.dependency_overrides.clear()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_user_requires_super_admin(
    test_db,
    test_user: User  # recepcion role
):
    """Test that non-super_admin cannot create users."""
    from fastapi import Depends
    from database import get_db
    
    async def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    token = create_access_token(data={"sub": test_user.username})
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/users",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "username": "newuser",
                "name": "New User",
                "role": "recepcion",
                "password": "NewPass123"
            }
        )
    
    assert response.status_code == 403  # Forbidden
    
    app.dependency_overrides.clear()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_users_success(
    test_db,
    test_superadmin: User,
    test_user: User
):
    """Test listing users."""
    from fastapi import Depends
    from database import get_db
    
    async def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    token = create_access_token(data={"sub": test_superadmin.username})
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/users",
            headers={"Authorization": f"Bearer {token}"}
        )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2
    usernames = [u["username"] for u in data]
    assert "testuser" in usernames
    assert "superadmin" in usernames
    
    app.dependency_overrides.clear()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_users_admin_viewer_can_access(
    test_db,
    test_admin_viewer: User
):
    """Test that admin_viewer can list users."""
    from fastapi import Depends
    from database import get_db
    
    async def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    token = create_access_token(data={"sub": test_admin_viewer.username})
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/users",
            headers={"Authorization": f"Bearer {token}"}
        )
    
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    
    app.dependency_overrides.clear()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_user_by_id_success(
    test_db,
    test_superadmin: User,
    test_user: User
):
    """Test getting user by ID."""
    from fastapi import Depends
    from database import get_db
    
    async def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    token = create_access_token(data={"sub": test_superadmin.username})
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            f"/users/{test_user.id}",
            headers={"Authorization": f"Bearer {token}"}
        )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(test_user.id)
    assert data["username"] == "testuser"
    
    app.dependency_overrides.clear()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_user_by_id_not_found(
    test_db,
    test_superadmin: User
):
    """Test getting non-existent user returns 404."""
    from fastapi import Depends
    from database import get_db
    
    async def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    token = create_access_token(data={"sub": test_superadmin.username})
    fake_id = str(uuid.uuid4())
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            f"/users/{fake_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
    
    assert response.status_code == 404
    
    app.dependency_overrides.clear()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_update_user_partial(
    test_db,
    test_superadmin: User,
    test_user: User
):
    """Test updating user with partial data."""
    from fastapi import Depends
    from database import get_db
    
    async def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    token = create_access_token(data={"sub": test_superadmin.username})
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.put(
            f"/users/{test_user.id}",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "Updated Name"
            }
        )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["username"] == "testuser"  # Unchanged
    
    # Cleanup: restore original name
    await client.put(
        f"/users/{test_user.id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Test User"}
    )
    
    app.dependency_overrides.clear()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_update_user_password(
    test_db,
    test_superadmin: User,
    test_user: User
):
    """Test updating user password."""
    from fastapi import Depends
    from database import get_db
    
    async def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    token = create_access_token(data={"sub": test_superadmin.username})
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.put(
            f"/users/{test_user.id}",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "password": "UpdatedPass123"
            }
        )
    
    assert response.status_code == 200
    
    # Verify password was changed by trying to login
    from core.security import verify_password
    from sqlalchemy import select
    result = await test_db.execute(
        select(User).where(User.id == test_user.id)
    )
    updated_user = result.scalar_one()
    assert verify_password("UpdatedPass123", updated_user.password_hash)
    
    app.dependency_overrides.clear()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_update_user_requires_super_admin(
    test_db,
    test_user: User
):
    """Test that non-super_admin cannot update users."""
    from fastapi import Depends
    from database import get_db
    
    async def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    token = create_access_token(data={"sub": test_user.username})
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.put(
            f"/users/{test_user.id}",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "Updated Name"
            }
        )
    
    assert response.status_code == 403  # Forbidden
    
    app.dependency_overrides.clear()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_delete_user_success(
    test_db,
    test_superadmin: User
):
    """Test deleting a user."""
    from fastapi import Depends
    from database import get_db
    from services.user_service import UserService
    from schemas.user import UserCreate
    
    async def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    # Create a temporary user to delete
    temp_user_data = UserCreate(
        username="todelete",
        name="To Delete",
        role="monitor",
        password="DeletePass123"
    )
    temp_user = await UserService.create_user(
        db=test_db,
        user_data=temp_user_data,
        created_by_id=str(test_superadmin.id)
    )
    
    token = create_access_token(data={"sub": test_superadmin.username})
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.delete(
            f"/users/{temp_user.id}",
            headers={"Authorization": f"Bearer {token}"}
        )
    
    assert response.status_code == 200
    assert "deleted successfully" in response.json()["message"].lower()
    
    app.dependency_overrides.clear()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_delete_user_last_super_admin_fails(
    test_db,
    test_superadmin: User
):
    """Test that deleting last super_admin returns 400."""
    from fastapi import Depends
    from database import get_db
    
    async def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    token = create_access_token(data={"sub": test_superadmin.username})
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.delete(
            f"/users/{test_superadmin.id}",
            headers={"Authorization": f"Bearer {token}"}
        )
    
    assert response.status_code == 400
    assert "last super_admin" in response.json()["detail"].lower()
    
    app.dependency_overrides.clear()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_change_password_by_admin_success(
    test_db,
    test_superadmin: User,
    test_user: User
):
    """Test changing password by admin."""
    from fastapi import Depends
    from database import get_db
    
    async def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    token = create_access_token(data={"sub": test_superadmin.username})
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            f"/users/{test_user.id}/change-password",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "new_password": "NewAdminPass123"
            }
        )
    
    assert response.status_code == 200
    assert "changed successfully" in response.json()["message"].lower()
    
    # Verify password was changed
    from core.security import verify_password
    from sqlalchemy import select
    result = await test_db.execute(
        select(User).where(User.id == test_user.id)
    )
    updated_user = result.scalar_one()
    assert verify_password("NewAdminPass123", updated_user.password_hash)
    
    app.dependency_overrides.clear()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_change_password_invalid_password(
    test_db,
    test_superadmin: User,
    test_user: User
):
    """Test that invalid password returns validation error."""
    from fastapi import Depends
    from database import get_db
    
    async def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    token = create_access_token(data={"sub": test_superadmin.username})
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            f"/users/{test_user.id}/change-password",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "new_password": "short"  # Invalid
            }
        )
    
    assert response.status_code == 422  # Validation error
    
    app.dependency_overrides.clear()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_deactivate_user_success(
    test_db,
    test_superadmin: User,
    test_user: User
):
    """Test deactivating a user."""
    from fastapi import Depends
    from database import get_db
    
    async def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    token = create_access_token(data={"sub": test_superadmin.username})
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            f"/users/{test_user.id}/deactivate",
            headers={"Authorization": f"Bearer {token}"}
        )
    
    assert response.status_code == 200
    data = response.json()
    assert data["is_active"] is False
    
    # Cleanup: reactivate
    await client.post(
        f"/users/{test_user.id}/activate",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    app.dependency_overrides.clear()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_deactivate_user_last_super_admin_fails(
    test_db,
    test_superadmin: User
):
    """Test that deactivating last super_admin returns 400."""
    from fastapi import Depends
    from database import get_db
    
    async def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    token = create_access_token(data={"sub": test_superadmin.username})
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            f"/users/{test_superadmin.id}/deactivate",
            headers={"Authorization": f"Bearer {token}"}
        )
    
    assert response.status_code == 400
    assert "last active super_admin" in response.json()["detail"].lower()
    
    app.dependency_overrides.clear()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_activate_user_success(
    test_db,
    test_superadmin: User,
    test_user: User
):
    """Test activating a user."""
    from fastapi import Depends
    from database import get_db
    from services.user_service import UserService
    
    async def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    # First deactivate
    await UserService.deactivate_user(
        db=test_db,
        user_id=str(test_user.id)
    )
    
    token = create_access_token(data={"sub": test_superadmin.username})
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            f"/users/{test_user.id}/activate",
            headers={"Authorization": f"Bearer {token}"}
        )
    
    assert response.status_code == 200
    data = response.json()
    assert data["is_active"] is True
    
    app.dependency_overrides.clear()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_current_user_profile(
    test_db,
    test_user: User
):
    """Test getting current user profile."""
    from fastapi import Depends
    from database import get_db
    
    async def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    token = create_access_token(data={"sub": test_user.username})
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {token}"}
        )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(test_user.id)
    assert data["username"] == "testuser"
    assert "password" not in data
    
    app.dependency_overrides.clear()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_current_user_profile_requires_auth(test_db):
    """Test that /users/me requires authentication."""
    from fastapi import Depends
    from database import get_db
    
    async def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/users/me")
    
    assert response.status_code == 403  # Forbidden (no token)
    
    app.dependency_overrides.clear()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_user_with_sucursal(
    test_db,
    test_superadmin: User,
    test_sucursal
):
    """Test creating user with valid sucursal_id."""
    from fastapi import Depends
    from database import get_db
    
    async def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    token = create_access_token(data={"sub": test_superadmin.username})
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/users",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "username": "userwithsucursal",
                "name": "User With Sucursal",
                "role": "recepcion",
                "password": "SucursalPass123",
                "sucursal_id": str(test_sucursal.id)
            }
        )
    
    assert response.status_code == 200
    data = response.json()
    assert data["sucursal_id"] == str(test_sucursal.id)
    
    app.dependency_overrides.clear()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_user_invalid_sucursal(
    test_db,
    test_superadmin: User
):
    """Test that creating user with invalid sucursal_id returns 400."""
    from fastapi import Depends
    from database import get_db
    
    async def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    token = create_access_token(data={"sub": test_superadmin.username})
    invalid_id = str(uuid.uuid4())
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/users",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "username": "user_invalid",
                "name": "User Invalid",
                "role": "recepcion",
                "password": "Password123",
                "sucursal_id": invalid_id
            }
        )
    
    assert response.status_code == 400
    assert f"Sucursal with ID {invalid_id} not found" in response.json()["detail"]
    
    app.dependency_overrides.clear()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_update_user_invalid_sucursal(
    test_db,
    test_superadmin: User,
    test_user: User
):
    """Test that updating user with invalid sucursal_id returns 400."""
    from fastapi import Depends
    from database import get_db
    
    async def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    token = create_access_token(data={"sub": test_superadmin.username})
    invalid_id = str(uuid.uuid4())
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.put(
            f"/users/{test_user.id}",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "sucursal_id": invalid_id
            }
        )
    
    assert response.status_code == 400
    assert f"Sucursal with ID {invalid_id} not found" in response.json()["detail"]
    
    app.dependency_overrides.clear()

