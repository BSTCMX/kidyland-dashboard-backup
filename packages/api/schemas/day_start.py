"""
DayStart Pydantic schemas.
"""
from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


class DayStartBase(BaseModel):
    """Base day start schema with common fields."""
    started_at: datetime
    initial_cash_cents: int
    is_active: bool = True

    class Config:
        from_attributes = True


class DayStartCreate(BaseModel):
    """Schema for creating a new day start."""
    sucursal_id: UUID
    initial_cash_cents: int = 0

    class Config:
        from_attributes = True


class DayStartUpdate(BaseModel):
    """Schema for updating day start (all fields optional)."""
    initial_cash_cents: Optional[int] = None
    is_active: Optional[bool] = None

    class Config:
        from_attributes = True


class DayStartRead(DayStartBase):
    """Schema for reading day start data."""
    id: UUID
    sucursal_id: UUID
    usuario_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DayStatusRead(BaseModel):
    """Schema for day status (open/closed)."""
    is_open: bool
    day_start: Optional[DayStartRead] = None
    current_date: datetime
    current_business_date: Optional[str] = None  # YYYY-MM-DD format in sucursal timezone

    class Config:
        from_attributes = True

























