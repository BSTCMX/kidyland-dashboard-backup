"""
Service Pydantic schemas.
"""
from pydantic import BaseModel
from typing import Optional, List, Dict
from uuid import UUID
from datetime import datetime


class ServiceAlert(BaseModel):
    """Service alert configuration."""
    minutes_before: int
    sound: Optional[str] = None  # Kept for backward compatibility
    sound_enabled: Optional[bool] = False  # New: enable/disable sound for this alert
    sound_loop: Optional[bool] = False  # New: loop sound continuously until stopped


class ServiceBase(BaseModel):
    """Base service schema with common fields."""
    name: str
    durations_allowed: List[int]
    duration_prices: Dict[int, int]  # Required: {duration_minutes: price_cents} for flexible pricing
    alerts_config: List[ServiceAlert] = []
    active: bool = True

    class Config:
        from_attributes = True


class ServiceCreate(ServiceBase):
    """Schema for creating a new service."""
    sucursal_id: Optional[UUID] = None  # Optional: can be derived from sucursales_ids
    sucursales_ids: Optional[List[UUID]] = None  # New: support for multiple sucursales


class ServiceUpdate(BaseModel):
    """Schema for updating service (all fields optional)."""
    name: Optional[str] = None
    durations_allowed: Optional[List[int]] = None
    duration_prices: Optional[Dict[int, int]] = None  # Optional: {duration_minutes: price_cents} for flexible pricing
    alerts_config: Optional[List[ServiceAlert]] = None
    active: Optional[bool] = None
    sucursal_id: Optional[UUID] = None  # Kept for backward compatibility
    sucursales_ids: Optional[List[UUID]] = None  # New: support for multiple sucursales

    class Config:
        from_attributes = True


class ServiceRead(ServiceBase):
    """Schema for reading service data."""
    id: UUID
    sucursal_id: UUID  # Kept for backward compatibility
    sucursales_ids: Optional[List[UUID]] = None  # New: support for multiple sucursales
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True










