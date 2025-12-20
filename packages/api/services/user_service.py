"""
User Service - Business logic for user management operations.

Handles all user-related business logic including:
- User creation with validations
- User updates
- User deletion with safety checks
- Password management
- User activation/deactivation
"""
import logging
import uuid
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError

from models.user import User, UserRole
from models.sucursal import Sucursal
from schemas.user import UserCreate, UserUpdate
from core.security import get_password_hash, verify_password

logger = logging.getLogger(__name__)


def _convert_role_enum_to_user_role(role: any) -> UserRole:
    """
    Helper function to convert RoleEnum (from schema) to UserRole (from model).
    
    Args:
        role: RoleEnum instance or string value
        
    Returns:
        UserRole enum instance
    """
    if isinstance(role, UserRole):
        return role
    role_value = role.value if hasattr(role, 'value') else str(role)
    return UserRole(role_value)


class UserService:
    """Service for handling user management operations."""
    
    @staticmethod
    async def create_user(
        db: AsyncSession,
        user_data: UserCreate,
        created_by_id: str
    ) -> User:
        """
        Create a new user with validations.
        
        Args:
            db: Database session
            user_data: User creation data
            created_by_id: ID of the user creating this user (super_admin)
            
        Returns:
            Created User object
            
        Raises:
            ValueError: If username already exists
            ValueError: If sucursal_id is provided but doesn't exist
            ValueError: If role is invalid
        """
        # Check if username already exists (excluding soft-deleted users)
        username_check = await db.execute(
            select(User).where(
                User.username == user_data.username,
                User.deleted_at.is_(None)  # Exclude soft-deleted users
            )
        )
        if username_check.scalar_one_or_none():
            raise ValueError(f"Username '{user_data.username}' already exists")
        
        # Validate sucursal_id if provided
        if user_data.sucursal_id:
            sucursal_check = await db.execute(
                select(Sucursal).where(Sucursal.id == user_data.sucursal_id)
            )
            if not sucursal_check.scalar_one_or_none():
                raise ValueError(f"Sucursal with ID {user_data.sucursal_id} not found")
        
        # Hash password
        password_hash = get_password_hash(user_data.password)
        
        # Create user
        user = User(
            id=uuid.uuid4(),
            username=user_data.username,
            name=user_data.name,
            password_hash=password_hash,
            role=_convert_role_enum_to_user_role(user_data.role),
            is_active=True,
            sucursal_id=user_data.sucursal_id,
            created_by=uuid.UUID(created_by_id) if created_by_id else None
        )
        
        db.add(user)
        try:
            await db.commit()
            await db.refresh(user)
            logger.info(f"User created: {user.username} (ID: {user.id}) by {created_by_id}")
            return user
        except IntegrityError as e:
            await db.rollback()
            logger.error(f"Error creating user: {e}")
            raise ValueError("User creation failed due to database constraint")
    
    @staticmethod
    async def list_users(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = False
    ) -> List[User]:
        """
        List all users with optional filtering.
        
        Excludes soft-deleted users by default (deleted_at IS NULL).
        
        Args:
            db: Database session
            skip: Number of records to skip (pagination)
            limit: Maximum number of records to return
            active_only: If True, only return active users (is_active=True)
            
        Returns:
            List of User objects (non-deleted only)
        """
        query = select(User).where(User.deleted_at.is_(None))  # Exclude soft-deleted users
        
        if active_only:
            query = query.where(User.is_active == True)
        
        query = query.offset(skip).limit(limit).order_by(User.created_at.desc())
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def get_user_by_id(
        db: AsyncSession,
        user_id: str,
        include_deleted: bool = False
    ) -> Optional[User]:
        """
        Get a user by ID.
        
        Excludes soft-deleted users by default (deleted_at IS NULL).
        
        Args:
            db: Database session
            user_id: User ID (UUID string)
            include_deleted: If True, include soft-deleted users (default: False)
            
        Returns:
            User object or None if not found or deleted (unless include_deleted=True)
        """
        try:
            user_uuid = uuid.UUID(user_id)
        except ValueError:
            return None
        
        query = select(User).where(User.id == user_uuid)
        if not include_deleted:
            query = query.where(User.deleted_at.is_(None))  # Exclude soft-deleted users
        
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_user_by_username(
        db: AsyncSession,
        username: str
    ) -> Optional[User]:
        """
        Get a user by username.
        
        Excludes soft-deleted users (deleted_at IS NULL).
        This is critical for authentication - deleted users cannot log in.
        
        Args:
            db: Database session
            username: Username
            
        Returns:
            User object or None if not found or deleted
        """
        result = await db.execute(
            select(User).where(
                User.username == username,
                User.deleted_at.is_(None)  # Exclude soft-deleted users
            )
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def update_user(
        db: AsyncSession,
        user_id: str,
        user_data: UserUpdate
    ) -> User:
        """
        Update a user.
        
        Args:
            db: Database session
            user_id: User ID to update
            user_data: Update data (all fields optional)
            
        Returns:
            Updated User object
            
        Raises:
            ValueError: If user not found
            ValueError: If username already exists
            ValueError: If sucursal_id is provided but doesn't exist
        """
        user = await UserService.get_user_by_id(db, user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
        
        # Check username uniqueness if changing (excluding soft-deleted users)
        if user_data.username and user_data.username != user.username:
            username_check = await db.execute(
                select(User).where(
                    User.username == user_data.username,
                    User.deleted_at.is_(None)  # Exclude soft-deleted users
                )
            )
            if username_check.scalar_one_or_none():
                raise ValueError(f"Username '{user_data.username}' already exists")
            user.username = user_data.username
        
        # Get fields that were explicitly set (to distinguish None from not-provided)
        user_data_dict = user_data.model_dump(exclude_unset=True)
        
        # Handle sucursal_id: allow setting to None explicitly
        if 'sucursal_id' in user_data_dict:
            if user_data.sucursal_id is not None:
                # Validate sucursal exists if a value is provided
                sucursal_check = await db.execute(
                    select(Sucursal).where(Sucursal.id == user_data.sucursal_id)
                )
                if not sucursal_check.scalar_one_or_none():
                    raise ValueError(f"Sucursal with ID {user_data.sucursal_id} not found")
                user.sucursal_id = user_data.sucursal_id
            else:
                # Explicitly set to None to unassign sucursal
                user.sucursal_id = None
        
        # Update other fields
        if user_data.name is not None:
            user.name = user_data.name
        if user_data.role is not None:
            user.role = _convert_role_enum_to_user_role(user_data.role)
        if user_data.is_active is not None:
            user.is_active = user_data.is_active
        if user_data.password is not None:
            user.password_hash = get_password_hash(user_data.password)
        
        try:
            await db.commit()
            await db.refresh(user)
            logger.info(f"User updated: {user.username} (ID: {user.id})")
            return user
        except IntegrityError as e:
            await db.rollback()
            logger.error(f"Error updating user: {e}")
            raise ValueError("User update failed due to database constraint")
    
    @staticmethod
    async def delete_user(
        db: AsyncSession,
        user_id: str
    ) -> bool:
        """
        Delete a user (soft delete).
        
        Prevents deletion of the last active super_admin.
        Performs soft delete by marking the user with deleted_at timestamp.
        The user will be permanently deleted after 30 days by an automatic cleanup task.
        
        Args:
            db: Database session
            user_id: User ID to delete
            
        Returns:
            True if deleted successfully
            
        Raises:
            ValueError: If user not found or already deleted
            ValueError: If trying to delete last active super_admin
        """
        # Get user including soft-deleted ones to check if already deleted
        user = await UserService.get_user_by_id(db, user_id, include_deleted=True)
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
        
        # Check if already soft-deleted
        if user.deleted_at is not None:
            raise ValueError(f"User {user_id} is already deleted")
        
        # Prevent deletion of last active super_admin
        if user.role == UserRole.SUPER_ADMIN:
            # Count active super_admins (not soft-deleted)
            count_result = await db.execute(
                select(func.count(User.id)).where(
                    User.role == UserRole.SUPER_ADMIN,
                    User.deleted_at.is_(None)  # Only count non-deleted users
                )
            )
            active_super_admin_count = count_result.scalar_one()
            
            if active_super_admin_count <= 1:
                raise ValueError("Cannot delete the last active super_admin")
        
        # Soft delete: mark with deleted_at timestamp (also sets is_active=False via mixin)
        user.soft_delete()
        await db.commit()
        logger.info(f"User soft-deleted: {user.username} (ID: {user.id})")
        return True
    
    @staticmethod
    async def change_password(
        db: AsyncSession,
        user_id: str,
        current_password: str,
        new_password: str
    ) -> bool:
        """
        Change user password (requires current password).
        
        Args:
            db: Database session
            user_id: User ID
            current_password: Current password for verification
            new_password: New password
            
        Returns:
            True if password changed successfully
            
        Raises:
            ValueError: If user not found
            ValueError: If current password is incorrect
        """
        user = await UserService.get_user_by_id(db, user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
        
        # Verify current password
        if not verify_password(current_password, user.password_hash):
            raise ValueError("Current password is incorrect")
        
        # Update password
        user.password_hash = get_password_hash(new_password)
        await db.commit()
        logger.info(f"Password changed for user: {user.username} (ID: {user.id})")
        return True
    
    @staticmethod
    async def change_password_by_admin(
        db: AsyncSession,
        user_id: str,
        new_password: str
    ) -> bool:
        """
        Change user password by admin (no current password required).
        
        Args:
            db: Database session
            user_id: User ID
            new_password: New password
            
        Returns:
            True if password changed successfully
            
        Raises:
            ValueError: If user not found
        """
        user = await UserService.get_user_by_id(db, user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
        
        # Update password
        user.password_hash = get_password_hash(new_password)
        await db.commit()
        logger.info(f"Password changed by admin for user: {user.username} (ID: {user.id})")
        return True
    
    @staticmethod
    async def deactivate_user(
        db: AsyncSession,
        user_id: str
    ) -> User:
        """
        Deactivate a user (soft delete).
        
        Args:
            db: Database session
            user_id: User ID to deactivate
            
        Returns:
            Updated User object (is_active=False)
            
        Raises:
            ValueError: If user not found
            ValueError: If trying to deactivate last super_admin
        """
        user = await UserService.get_user_by_id(db, user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
        
        # Prevent deactivation of last super_admin (exclude soft-deleted)
        if user.role == UserRole.SUPER_ADMIN:
            count_result = await db.execute(
                select(func.count(User.id)).where(
                    User.role == UserRole.SUPER_ADMIN,
                    User.is_active == True,
                    User.deleted_at.is_(None)  # Exclude soft-deleted users
                )
            )
            active_super_admin_count = count_result.scalar_one()
            
            if active_super_admin_count <= 1:
                raise ValueError("Cannot deactivate the last active super_admin")
        
        user.is_active = False
        await db.commit()
        await db.refresh(user)
        logger.info(f"User deactivated: {user.username} (ID: {user.id})")
        return user
    
    @staticmethod
    async def activate_user(
        db: AsyncSession,
        user_id: str
    ) -> User:
        """
        Activate a user.
        
        Args:
            db: Database session
            user_id: User ID to activate
            
        Returns:
            Updated User object (is_active=True)
            
        Raises:
            ValueError: If user not found
        """
        user = await UserService.get_user_by_id(db, user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
        
        user.is_active = True
        await db.commit()
        await db.refresh(user)
        logger.info(f"User activated: {user.username} (ID: {user.id})")
        return user

