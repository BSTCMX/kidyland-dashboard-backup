"""
Authentication middleware for role-based access control.
"""
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer

security = HTTPBearer()


async def get_current_user(
    # TODO: Implement JWT token validation
    credentials = Depends(security)
):
    """
    Validate JWT token and return current user.
    """
    # TODO: Implement authentication logic
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Authentication not implemented"
    )


def require_role(allowed_roles: list[str]):
    """
    Dependency factory for role-based access control.
    """
    async def role_checker(current_user = Depends(get_current_user)):
        # TODO: Check if user role is in allowed_roles
        return current_user
    return role_checker
