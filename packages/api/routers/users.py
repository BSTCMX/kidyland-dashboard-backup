"""
User management endpoints.

Security Rules:
- Only super_admin can CREATE, UPDATE, or DELETE users
- super_admin and admin_viewer can VIEW users (list and get)
- Other roles cannot access user management endpoints
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from database import get_db
from schemas.user import (
    UserCreate, UserUpdate, UserRead,
    ChangePasswordRequest, ChangePasswordByAdminRequest
)
from models.user import User
from services.user_service import UserService
from utils.auth import require_role, get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserRead, dependencies=[Depends(require_role("super_admin"))])
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new user.
    
    Security: Only super_admin can create users.
    Super Admin defines username, password, and role for each user.
    
    Validations:
    - Username: 3-50 chars, alphanumeric + underscore, unique
    - Password: Minimum 8 chars, at least 1 uppercase and 1 number
    - Role: One of the 5 valid roles
    """
    try:
        user = await UserService.create_user(
            db=db,
            user_data=user_data,
            created_by_id=str(current_user.id)
        )
        return UserRead.model_validate(user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating user: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating user"
        )


@router.get("", response_model=List[UserRead], dependencies=[Depends(require_role(["super_admin", "admin_viewer"]))])
async def list_users(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    active_only: bool = Query(False, description="Only return active users")
):
    """
    List all users with pagination.
    
    Security: super_admin and admin_viewer can list users.
    """
    try:
        users = await UserService.list_users(
            db=db,
            skip=skip,
            limit=limit,
            active_only=active_only
        )
        return [UserRead.model_validate(user) for user in users]
    except Exception as e:
        logger.error(f"Error listing users: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error listing users"
        )


@router.get("/{user_id}", response_model=UserRead, dependencies=[Depends(require_role(["super_admin", "admin_viewer"]))])
async def get_user(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific user by ID.
    
    Security: super_admin and admin_viewer can view user details.
    """
    try:
        user = await UserService.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found"
            )
        return UserRead.model_validate(user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting user"
        )


@router.put("/{user_id}", response_model=UserRead, dependencies=[Depends(require_role("super_admin"))])
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update a user.
    
    Security: Only super_admin can update users.
    Super Admin can change username, password, role, and other fields.
    
    Validations:
    - Username: 3-50 chars, alphanumeric + underscore, unique (if changing)
    - Password: Minimum 8 chars, at least 1 uppercase and 1 number (if changing)
    - Role: One of the 5 valid roles (if changing)
    """
    try:
        user = await UserService.update_user(
            db=db,
            user_id=user_id,
            user_data=user_data
        )
        return UserRead.model_validate(user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating user: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating user"
        )


@router.delete("/{user_id}", dependencies=[Depends(require_role("super_admin"))])
async def delete_user(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a user (soft delete).
    
    Security: Only super_admin can delete users.
    
    Prevents deletion of the last active super_admin.
    
    This performs a soft delete by marking the user with deleted_at timestamp.
    The user will be permanently deleted after 30 days by an automatic cleanup task.
    """
    try:
        await UserService.delete_user(db, user_id)
        return {"message": "User deleted successfully. It will be permanently removed after 30 days."}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error deleting user: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting user"
        )


@router.post("/{user_id}/change-password", dependencies=[Depends(require_role("super_admin"))])
async def change_password_by_admin(
    user_id: str,
    password_data: ChangePasswordByAdminRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Change user password by admin (no current password required).
    
    Security: Only super_admin can change passwords.
    """
    try:
        await UserService.change_password_by_admin(
            db=db,
            user_id=user_id,
            new_password=password_data.new_password
        )
        return {"message": "Password changed successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error changing password: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error changing password"
        )


@router.post("/{user_id}/deactivate", response_model=UserRead, dependencies=[Depends(require_role("super_admin"))])
async def deactivate_user(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Deactivate a user (soft delete).
    
    Security: Only super_admin can deactivate users.
    
    Prevents deactivation of the last active super_admin.
    """
    try:
        user = await UserService.deactivate_user(db, user_id)
        return UserRead.model_validate(user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error deactivating user: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deactivating user"
        )


@router.post("/{user_id}/activate", response_model=UserRead, dependencies=[Depends(require_role("super_admin"))])
async def activate_user(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Activate a user.
    
    Security: Only super_admin can activate users.
    """
    try:
        user = await UserService.activate_user(db, user_id)
        return UserRead.model_validate(user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error activating user: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error activating user"
        )


@router.get("/me", response_model=UserRead)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Get current authenticated user's profile.
    
    Security: Any authenticated user can view their own profile.
    """
    return UserRead.model_validate(current_user)

