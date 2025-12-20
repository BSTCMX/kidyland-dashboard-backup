"""
Sucursal Pydantic schemas.
"""
from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


class SucursalBase(BaseModel):
    """Base sucursal schema with common fields."""
    identifier: str  # e.g., "suc01"
    name: str
    address: Optional[str] = None
    timezone: str = "America/Mexico_City"
    active: bool = True

    class Config:
        from_attributes = True


class SucursalCreate(SucursalBase):
    """Schema for creating a new sucursal."""
    pass


class SucursalUpdate(BaseModel):
    """Schema for updating sucursal (all fields optional)."""
    identifier: Optional[str] = None
    name: Optional[str] = None
    address: Optional[str] = None
    timezone: Optional[str] = None
    active: Optional[bool] = None

    class Config:
        from_attributes = True


class SucursalRead(SucursalBase):
    """Schema for reading sucursal data."""
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True









