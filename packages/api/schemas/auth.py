"""
Authentication Pydantic schemas.
"""
from pydantic import BaseModel
from schemas.user import UserRead


class LoginRequest(BaseModel):
    """Schema for login request."""
    username: str
    password: str


class LoginResponse(BaseModel):
    """Schema for login response."""
    access_token: str
    token_type: str = "bearer"
    user: UserRead

