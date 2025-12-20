"""
Unit tests for UserService.

Tests cover:
- User creation with validations
- User updates
- Password management
- User activation/deactivation
- Edge cases and error handling
"""
import pytest
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from services.user_service import UserService
from schemas.user import UserCreate, UserUpdate, ChangePasswordByAdminRequest
from models.user import User, UserRole
from core.security import verify_password


@pytest.mark.asyncio
@pytest.mark.unit
async def test_create_user_success(
    test_db: AsyncSession,
    test_superadmin: User
):
    """Test successful user creation with valid username and password."""
    user_data = UserCreate(
        username="newuser",
        name="New User",
        role="recepcion",
        password="NewPass123"
    )
    
    user = await UserService.create_user(
        db=test_db,
        user_data=user_data,
        created_by_id=str(test_superadmin.id)
    )
    
    assert user is not None
    assert user.username == "newuser"
    assert user.role == UserRole.RECEPCION
    assert user.is_active is True
    assert user.created_by == test_superadmin.id
    assert user.password_hash != "NewPass123"  # Should be hashed
    # Verify password works
    assert verify_password("NewPass123", user.password_hash)


@pytest.mark.asyncio
@pytest.mark.unit
async def test_create_user_duplicate_username(
    test_db: AsyncSession,
    test_superadmin: User,
    test_user: User
):
    """Test that creating user with duplicate username fails."""
    user_data = UserCreate(
        username="testuser",  # Already exists
        name="Duplicate User",
        role="recepcion",
        password="NewPass123"
    )
    
    with pytest.raises(ValueError, match="Username 'testuser' already exists"):
        await UserService.create_user(
            db=test_db,
            user_data=user_data,
            created_by_id=str(test_superadmin.id)
        )


@pytest.mark.asyncio
@pytest.mark.unit
async def test_create_user_invalid_username_too_short(
    test_db: AsyncSession,
    test_superadmin: User
):
    """Test that username validation fails for too short username."""
    # This will be caught by Pydantic schema validation
    with pytest.raises(ValueError):
        user_data = UserCreate(
            username="ab",  # Too short (min 3 chars)
            name="New User",
            role="recepcion",
            password="NewPass123"
        )


@pytest.mark.asyncio
@pytest.mark.unit
async def test_create_user_invalid_username_too_long(
    test_db: AsyncSession,
    test_superadmin: User
):
    """Test that username validation fails for too long username."""
    # This will be caught by Pydantic schema validation
    with pytest.raises(ValueError):
        user_data = UserCreate(
            username="a" * 51,  # Too long (max 50 chars)
            name="New User",
            role="recepcion",
            password="NewPass123"
        )


@pytest.mark.asyncio
@pytest.mark.unit
async def test_create_user_invalid_username_special_chars(
    test_db: AsyncSession,
    test_superadmin: User
):
    """Test that username validation fails for special characters."""
    # This will be caught by Pydantic schema validation
    with pytest.raises(ValueError):
        user_data = UserCreate(
            username="user@name",  # Invalid: contains @
            name="New User",
            role="recepcion",
            password="NewPass123"
        )


@pytest.mark.asyncio
@pytest.mark.unit
async def test_create_user_invalid_password_too_short(
    test_db: AsyncSession,
    test_superadmin: User
):
    """Test that password validation fails for too short password."""
    from pydantic import ValidationError
    
    # Pydantic validation should catch this
    with pytest.raises(ValidationError) as exc_info:
        UserCreate(
            username="newuser",
            name="New User",
            role="recepcion",
            password="Short1"  # Only 7 chars, needs 8+
        )
    
    errors = exc_info.value.errors()
    assert any("Password must be at least 8 characters" in str(e) for e in errors)


@pytest.mark.asyncio
@pytest.mark.unit
async def test_create_user_invalid_password_no_uppercase(
    test_db: AsyncSession,
    test_superadmin: User
):
    """Test that password validation fails for password without uppercase."""
    from pydantic import ValidationError
    
    # Pydantic validation should catch this
    with pytest.raises(ValidationError) as exc_info:
        UserCreate(
            username="newuser",
            name="New User",
            role="recepcion",
            password="password123"  # No uppercase
        )
    
    errors = exc_info.value.errors()
    assert any("uppercase letter" in str(e).lower() for e in errors)


@pytest.mark.asyncio
@pytest.mark.unit
async def test_create_user_invalid_password_no_number(
    test_db: AsyncSession,
    test_superadmin: User
):
    """Test that password validation fails for password without number."""
    from pydantic import ValidationError
    
    # Pydantic validation should catch this
    with pytest.raises(ValidationError) as exc_info:
        UserCreate(
            username="newuser",
            name="New User",
            role="recepcion",
            password="Password"  # No number
        )
    
    errors = exc_info.value.errors()
    assert any("number" in str(e).lower() for e in errors)


@pytest.mark.asyncio
@pytest.mark.unit
async def test_list_users(
    test_db: AsyncSession,
    test_user: User,
    test_superadmin: User
):
    """Test listing users."""
    users = await UserService.list_users(
        db=test_db,
        skip=0,
        limit=100
    )
    
    assert len(users) >= 2
    usernames = [u.username for u in users]
    assert "testuser" in usernames
    assert "superadmin" in usernames


@pytest.mark.asyncio
@pytest.mark.unit
async def test_list_users_active_only(
    test_db: AsyncSession,
    test_user: User
):
    """Test listing only active users."""
    # Deactivate a user first
    test_user.is_active = False
    await test_db.commit()
    
    active_users = await UserService.list_users(
        db=test_db,
        active_only=True
    )
    
    # All returned users should be active
    assert all(user.is_active for user in active_users)
    
    # Reactivate for cleanup
    test_user.is_active = True
    await test_db.commit()


@pytest.mark.asyncio
@pytest.mark.unit
async def test_get_user_by_id(
    test_db: AsyncSession,
    test_user: User
):
    """Test getting user by ID."""
    user = await UserService.get_user_by_id(
        db=test_db,
        user_id=str(test_user.id)
    )
    
    assert user is not None
    assert user.id == test_user.id
    assert user.username == "testuser"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_get_user_by_id_not_found(
    test_db: AsyncSession
):
    """Test getting non-existent user returns None."""
    fake_id = str(uuid.uuid4())
    user = await UserService.get_user_by_id(
        db=test_db,
        user_id=fake_id
    )
    
    assert user is None


@pytest.mark.asyncio
@pytest.mark.unit
async def test_get_user_by_username(
    test_db: AsyncSession,
    test_user: User
):
    """Test getting user by username."""
    user = await UserService.get_user_by_username(
        db=test_db,
        username="testuser"
    )
    
    assert user is not None
    assert user.username == "testuser"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_update_user_partial(
    test_db: AsyncSession,
    test_user: User
):
    """Test updating user with partial data."""
    update_data = UserUpdate(
        name="Updated Name"
    )
    
    updated_user = await UserService.update_user(
        db=test_db,
        user_id=str(test_user.id),
        user_data=update_data
    )
    
    assert updated_user.name == "Updated Name"
    assert updated_user.username == test_user.username  # Unchanged


@pytest.mark.asyncio
@pytest.mark.unit
async def test_update_user_username(
    test_db: AsyncSession,
    test_user: User
):
    """Test updating username."""
    update_data = UserUpdate(
        username="updateduser"
    )
    
    updated_user = await UserService.update_user(
        db=test_db,
        user_id=str(test_user.id),
        user_data=update_data
    )
    
    assert updated_user.username == "updateduser"
    
    # Cleanup: restore original username
    restore_data = UserUpdate(username="testuser")
    await UserService.update_user(
        db=test_db,
        user_id=str(test_user.id),
        user_data=restore_data
    )


@pytest.mark.asyncio
@pytest.mark.unit
async def test_update_user_duplicate_username(
    test_db: AsyncSession,
    test_user: User,
    test_superadmin: User
):
    """Test that updating to duplicate username fails."""
    update_data = UserUpdate(
        username="superadmin"  # Already exists
    )
    
    with pytest.raises(ValueError, match="Username 'superadmin' already exists"):
        await UserService.update_user(
            db=test_db,
            user_id=str(test_user.id),
            user_data=update_data
        )


@pytest.mark.asyncio
@pytest.mark.unit
async def test_update_user_password(
    test_db: AsyncSession,
    test_user: User
):
    """Test updating user password."""
    new_password = "NewPass456"
    update_data = UserUpdate(
        password=new_password
    )
    
    updated_user = await UserService.update_user(
        db=test_db,
        user_id=str(test_user.id),
        user_data=update_data
    )
    
    # Verify password was hashed
    assert updated_user.password_hash != new_password
    # Verify password works
    from core.security import verify_password
    assert verify_password(new_password, updated_user.password_hash)


@pytest.mark.asyncio
@pytest.mark.unit
async def test_update_user_role(
    test_db: AsyncSession,
    test_user: User
):
    """Test updating user role."""
    update_data = UserUpdate(
        role="kidibar"
    )
    
    updated_user = await UserService.update_user(
        db=test_db,
        user_id=str(test_user.id),
        user_data=update_data
    )
    
    assert updated_user.role == UserRole.KIDIBAR
    
    # Cleanup: restore original role
    restore_data = UserUpdate(role="recepcion")
    await UserService.update_user(
        db=test_db,
        user_id=str(test_user.id),
        user_data=restore_data
    )


@pytest.mark.asyncio
@pytest.mark.unit
async def test_update_user_not_found(
    test_db: AsyncSession
):
    """Test updating non-existent user fails."""
    fake_id = str(uuid.uuid4())
    update_data = UserUpdate(name="New Name")
    
    with pytest.raises(ValueError, match=f"User with ID {fake_id} not found"):
        await UserService.update_user(
            db=test_db,
            user_id=fake_id,
            user_data=update_data
        )


@pytest.mark.asyncio
@pytest.mark.unit
async def test_delete_user_success(
    test_db: AsyncSession,
    test_user: User
):
    """Test deleting a user."""
    # Create a temporary user to delete
    from schemas.user import UserCreate
    temp_user_data = UserCreate(
        username="todelete",
        name="To Delete",
        role="monitor",
        password="DeletePass123"
    )
    temp_user = await UserService.create_user(
        db=test_db,
        user_data=temp_user_data,
        created_by_id=str(test_user.id)
    )
    
    # Delete the user
    result = await UserService.delete_user(
        db=test_db,
        user_id=str(temp_user.id)
    )
    
    assert result is True
    
    # Verify user is deleted
    deleted_user = await UserService.get_user_by_id(
        db=test_db,
        user_id=str(temp_user.id)
    )
    assert deleted_user is None


@pytest.mark.asyncio
@pytest.mark.unit
async def test_delete_user_last_super_admin_fails(
    test_db: AsyncSession,
    test_superadmin: User
):
    """Test that deleting the last super_admin fails."""
    # Ensure test_superadmin is the only super_admin
    # (This should be the case in a fresh test DB)
    
    with pytest.raises(ValueError, match="Cannot delete the last super_admin"):
        await UserService.delete_user(
            db=test_db,
            user_id=str(test_superadmin.id)
        )


@pytest.mark.asyncio
@pytest.mark.unit
async def test_delete_user_not_found(
    test_db: AsyncSession
):
    """Test deleting non-existent user fails."""
    fake_id = str(uuid.uuid4())
    
    with pytest.raises(ValueError, match=f"User with ID {fake_id} not found"):
        await UserService.delete_user(
            db=test_db,
            user_id=fake_id
        )


@pytest.mark.asyncio
@pytest.mark.unit
async def test_change_password_by_admin_success(
    test_db: AsyncSession,
    test_user: User
):
    """Test changing password by admin."""
    new_password = "NewAdminPass123"
    
    result = await UserService.change_password_by_admin(
        db=test_db,
        user_id=str(test_user.id),
        new_password=new_password
    )
    
    assert result is True
    
    # Verify password was changed
    updated_user = await UserService.get_user_by_id(
        db=test_db,
        user_id=str(test_user.id)
    )
    assert verify_password(new_password, updated_user.password_hash)


@pytest.mark.asyncio
@pytest.mark.unit
async def test_change_password_by_admin_not_found(
    test_db: AsyncSession
):
    """Test changing password for non-existent user fails."""
    fake_id = str(uuid.uuid4())
    
    with pytest.raises(ValueError, match=f"User with ID {fake_id} not found"):
        await UserService.change_password_by_admin(
            db=test_db,
            user_id=fake_id,
            new_password="NewPass123"
        )


@pytest.mark.asyncio
@pytest.mark.unit
async def test_deactivate_user_success(
    test_db: AsyncSession,
    test_user: User
):
    """Test deactivating a user."""
    deactivated_user = await UserService.deactivate_user(
        db=test_db,
        user_id=str(test_user.id)
    )
    
    assert deactivated_user.is_active is False
    
    # Cleanup: reactivate
    await UserService.activate_user(
        db=test_db,
        user_id=str(test_user.id)
    )


@pytest.mark.asyncio
@pytest.mark.unit
async def test_deactivate_user_last_super_admin_fails(
    test_db: AsyncSession,
    test_superadmin: User
):
    """Test that deactivating the last active super_admin fails."""
    with pytest.raises(ValueError, match="Cannot deactivate the last active super_admin"):
        await UserService.deactivate_user(
            db=test_db,
            user_id=str(test_superadmin.id)
        )


@pytest.mark.asyncio
@pytest.mark.unit
async def test_activate_user_success(
    test_db: AsyncSession,
    test_user: User
):
    """Test activating a user."""
    # First deactivate
    await UserService.deactivate_user(
        db=test_db,
        user_id=str(test_user.id)
    )
    
    # Then activate
    activated_user = await UserService.activate_user(
        db=test_db,
        user_id=str(test_user.id)
    )
    
    assert activated_user.is_active is True


@pytest.mark.asyncio
@pytest.mark.unit
async def test_activate_user_not_found(
    test_db: AsyncSession
):
    """Test activating non-existent user fails."""
    fake_id = str(uuid.uuid4())
    
    with pytest.raises(ValueError, match=f"User with ID {fake_id} not found"):
        await UserService.activate_user(
            db=test_db,
            user_id=fake_id
        )


@pytest.mark.asyncio
@pytest.mark.unit
async def test_create_user_with_sucursal(
    test_db: AsyncSession,
    test_superadmin: User,
    test_sucursal
):
    """Test creating user with sucursal_id."""
    user_data = UserCreate(
        username="userwithsucursal",
        name="User With Sucursal",
        role="recepcion",
        password="SucursalPass123",
        sucursal_id=test_sucursal.id
    )
    
    user = await UserService.create_user(
        db=test_db,
        user_data=user_data,
        created_by_id=str(test_superadmin.id)
    )
    
    assert user.sucursal_id == test_sucursal.id


@pytest.mark.asyncio
@pytest.mark.unit
async def test_create_user_invalid_sucursal(
    test_db: AsyncSession,
    test_superadmin: User
):
    """Test that creating user with invalid sucursal_id fails."""
    invalid_id = uuid.uuid4()
    user_data = UserCreate(
        username="user_invalid",
        name="User Invalid",
        role="recepcion",
        password="Password123",
        sucursal_id=invalid_id
    )
    
    with pytest.raises(ValueError, match=f"Sucursal with ID {invalid_id} not found"):
        await UserService.create_user(
            db=test_db,
            user_data=user_data,
            created_by_id=str(test_superadmin.id)
        )


@pytest.mark.asyncio
@pytest.mark.unit
async def test_update_user_invalid_sucursal(
    test_db: AsyncSession,
    test_user: User
):
    """Test that updating user with invalid sucursal_id fails."""
    invalid_id = uuid.uuid4()
    user_update = UserUpdate(sucursal_id=invalid_id)
    
    with pytest.raises(ValueError, match=f"Sucursal with ID {invalid_id} not found"):
        await UserService.update_user(
            db=test_db,
            user_id=str(test_user.id),
            user_data=user_update
        )

