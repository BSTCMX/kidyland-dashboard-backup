"""
User Pydantic schemas with validations.
"""
from pydantic import BaseModel, constr, field_validator
from typing import Optional
from uuid import UUID
from datetime import datetime
from enum import Enum
import re


class RoleEnum(str, Enum):
    """Valid user roles."""
    super_admin = "super_admin"
    admin_viewer = "admin_viewer"
    recepcion = "recepcion"
    kidibar = "kidibar"
    monitor = "monitor"


# Valid roles list for backward compatibility
VALID_ROLES = [role.value for role in RoleEnum]


def validate_password(password: str) -> str:
    """
    Validate password: minimum 8 chars, at least 1 uppercase and 1 number.
    
    Args:
        password: Password to validate
        
    Returns:
        Password if valid
        
    Raises:
        ValueError: If password doesn't meet requirements
    """
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long")
    if not re.search(r'[A-Z]', password):
        raise ValueError("Password must contain at least one uppercase letter")
    if not re.search(r'[0-9]', password):
        raise ValueError("Password must contain at least one number")
    return password


class UserBase(BaseModel):
    """Base user schema with common fields."""
    username: constr(min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
    name: str
    role: RoleEnum
    sucursal_id: Optional[UUID] = None

    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        """
        Validate username: 3-50 chars, alphanumeric + underscore.
        
        Regex pattern: ^[a-zA-Z0-9_]+$ (already enforced by constr, but explicit validation)
        """
        if not re.match(r"^[a-zA-Z0-9_]{3,50}$", v):
            raise ValueError("Username must be 3-50 chars, alphanumeric + underscore")
        return v

    class Config:
        from_attributes = True


class UserCreate(UserBase):
    """Schema for creating a new user."""
    password: str

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """
        Validate password: minimum 8 chars, at least 1 uppercase and 1 number.
        
        Requirements:
        - Minimum 8 characters
        - At least 1 uppercase letter (A-Z)
        - At least 1 number (0-9)
        """
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not re.search(r'[A-Z]', v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r'[0-9]', v):
            raise ValueError("Password must contain at least one number")
        return v


class UserUpdate(BaseModel):
    """Schema for updating user (all fields optional)."""
    name: Optional[str] = None
    username: Optional[constr(min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")] = None
    role: Optional[RoleEnum] = None
    sucursal_id: Optional[UUID] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None

    @field_validator('username')
    @classmethod
    def validate_username(cls, v: Optional[str]) -> Optional[str]:
        """Validate username if provided."""
        if v is not None:
            if not re.match(r"^[a-zA-Z0-9_]{3,50}$", v):
                raise ValueError("Username must be 3-50 chars, alphanumeric + underscore")
        return v

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: Optional[str]) -> Optional[str]:
        """Validate password if provided."""
        if v is not None:
            if len(v) < 8:
                raise ValueError("Password must be at least 8 characters long")
            if not re.search(r'[A-Z]', v):
                raise ValueError("Password must contain at least one uppercase letter")
            if not re.search(r'[0-9]', v):
                raise ValueError("Password must contain at least one number")
        return v

    class Config:
        from_attributes = True


class UserRead(UserBase):
    """Schema for reading user data (includes all fields)."""
    id: UUID
    is_active: bool
    created_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class ChangePasswordRequest(BaseModel):
    """Schema for changing user password."""
    current_password: str
    new_password: str

    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        """Validate new password meets requirements."""
        return validate_password(v)


class ChangePasswordByAdminRequest(BaseModel):
    """Schema for admin changing user password (no current password required)."""
    new_password: str

    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        """Validate new password meets requirements."""
        return validate_password(v)

