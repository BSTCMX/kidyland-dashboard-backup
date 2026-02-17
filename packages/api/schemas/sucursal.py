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


# ---------- Display settings (Vista Display: zero_alert only) ----------


class ZeroAlertConfig(BaseModel):
    """Config for alert when timer reaches 0 (Vista Display only)."""
    sound_enabled: bool = False
    sound_loop: bool = False


class DisplaySettingsRead(BaseModel):
    """Display settings for a sucursal (read)."""
    zero_alert: ZeroAlertConfig = ZeroAlertConfig()

    class Config:
        from_attributes = True


class DisplaySettingsUpdate(BaseModel):
    """Display settings update (partial)."""
    zero_alert: Optional[ZeroAlertConfig] = None

    class Config:
        from_attributes = True









