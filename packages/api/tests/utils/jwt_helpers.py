"""
JWT token helpers for testing authentication.

Provides utilities to create JWT tokens for different roles.
"""
from datetime import datetime, timedelta
from typing import Optional

from jose import jwt
from datetime import datetime, timedelta

from models.user import User, UserRole

# Use test secret key (same as in conftest.py)
TEST_SECRET_KEY = "test-secret-key-for-testing-only"
TEST_ALGORITHM = "HS256"


def create_jwt_token(
    user_id: str,
    username: str,
    role: UserRole,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a JWT token for testing.

    Args:
        user_id: User ID
        username: Username
        role: User role
        expires_delta: Optional expiration delta (default: 30 minutes)

    Returns:
        JWT token string
    """
    if expires_delta is None:
        expires_delta = timedelta(minutes=30)

    expire = datetime.utcnow() + expires_delta

    to_encode = {
        "sub": str(user_id),
        "username": username,
        "role": role.value,
        "exp": expire,
    }

    encoded_jwt = jwt.encode(
        to_encode,
        TEST_SECRET_KEY,
        algorithm=TEST_ALGORITHM,
    )

    return encoded_jwt


def create_expired_jwt_token(
    user_id: str,
    username: str,
    role: UserRole,
) -> str:
    """Create an expired JWT token for testing expiration handling."""
    return create_jwt_token(
        user_id=user_id,
        username=username,
        role=role,
        expires_delta=timedelta(minutes=-1),  # Expired 1 minute ago
    )


def create_super_admin_token(user_id: str, username: str = "superadmin") -> str:
    """Create a JWT token for super admin."""
    return create_jwt_token(user_id, username, UserRole.SUPER_ADMIN)


def create_admin_viewer_token(user_id: str, username: str = "adminviewer") -> str:
    """Create a JWT token for admin viewer."""
    return create_jwt_token(user_id, username, UserRole.ADMIN_VIEWER)


def create_recepcion_token(user_id: str, username: str = "recepcion") -> str:
    """Create a JWT token for recepcion."""
    return create_jwt_token(user_id, username, UserRole.RECEPCION)


def create_kidibar_token(user_id: str, username: str = "kidibar") -> str:
    """Create a JWT token for kidibar."""
    return create_jwt_token(user_id, username, UserRole.KIDIBAR)


def create_monitor_token(user_id: str, username: str = "monitor") -> str:
    """Create a JWT token for monitor."""
    return create_jwt_token(user_id, username, UserRole.MONITOR)


def get_auth_headers(token: str) -> dict:
    """
    Get authorization headers for API requests.

    Args:
        token: JWT token

    Returns:
        Headers dict with Authorization header
    """
    return {"Authorization": f"Bearer {token}"}

