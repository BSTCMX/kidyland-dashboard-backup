"""
Authentication and authorization utilities.

Role Hierarchy:
- super_admin: Full control, only one who can create users
- admin_viewer: Read-only access to everything
- recepcion: Daily operations (sales, timers, day close), cannot create users
- kidibar: Only products and product sales
- monitor: Only view active timers, zero input
"""
import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Union, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models.user import User
from core.security import verify_token

logger = logging.getLogger(__name__)
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Validate JWT token and return current user.
    
    Args:
        credentials: HTTP Bearer token from Authorization header
        db: Async database session
        
    Returns:
        User object from database
        
    Raises:
        HTTPException: 401 if token is invalid or user not found
    """
    token = credentials.credentials
    
    # Verify and decode token
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract username from token (sub field)
    username: str = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Find user in database (exclude soft-deleted users)
    result = await db.execute(
        select(User).where(
            User.username == username,
            User.deleted_at.is_(None)  # Exclude soft-deleted users
        )
    )
    user = result.scalar_one_or_none()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


def require_role(required_roles: Union[str, List[str]]):
    """
    Dependency factory for role-based access control.
    
    Args:
        required_roles: Single role string or list of allowed roles
                       (e.g., "super_admin" or ["super_admin", "admin_viewer"])
    
    Returns:
        Dependency function that verifies the user has one of the required roles
    
    Examples:
        @router.post("/users", dependencies=[Depends(require_role("super_admin"))])
        @router.get("/reports", dependencies=[Depends(require_role(["super_admin", "admin_viewer"]))])
        @router.post("/sales", dependencies=[Depends(require_role("recepcion"))])
    """
    # Normalize to list
    if isinstance(required_roles, str):
        allowed_roles = [required_roles]
    else:
        allowed_roles = required_roles
    
    async def role_checker(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
    ):
        """
        Verify that the current user has one of the required roles.
        
        Raises:
            HTTPException: 403 if user doesn't have any of the required roles
        """
        # Refresh user from database to get latest role (async query)
        result = await db.execute(
            select(User).where(User.id == current_user.id)
        )
        db_user = result.scalar_one_or_none()
        
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Normalize role comparison: use .value for enum to string conversion
        user_role_value = db_user.role.value if hasattr(db_user.role, 'value') else str(db_user.role)
        
        # Super admin bypass: full system access regardless of required roles
        # This maintains security by still validating the user exists and is active
        if user_role_value == "super_admin":
            logger.debug(
                f"Super admin bypass: user_id={db_user.id}, username={db_user.username}, "
                f"required_roles={allowed_roles}"
            )
            return db_user
        
        if user_role_value not in allowed_roles:
            roles_str = ", ".join(allowed_roles)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role(s): {roles_str}. Your role: {user_role_value}"
            )
        
        # Log successful role check for debugging (temporary)
        logger.debug(
            f"Role check passed: user_id={db_user.id}, username={db_user.username}, "
            f"role={user_role_value}, allowed_roles={allowed_roles}"
        )
        
        return db_user
    
    return role_checker


def require_superadmin():
    """
    Convenience function to require super_admin role.
    Only super_admin can create, update, or delete users.
    
    Returns:
        Dependency that verifies the user is a super_admin
    """
    return require_role("super_admin")

