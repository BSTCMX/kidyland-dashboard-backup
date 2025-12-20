"""
DayClose Pydantic schemas.
"""
from pydantic import BaseModel
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime, date


class DayCloseBase(BaseModel):
    """Base day close schema with common fields."""
    date: date
    system_total_cents: Optional[int] = None  # Optional: calculated automatically if not provided
    physical_count_cents: int
    difference_cents: Optional[int] = None  # Optional: calculated automatically
    totals: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None  # Optional notes/observations

    class Config:
        from_attributes = True


class DayCloseCreate(DayCloseBase):
    """Schema for creating a new day close."""
    sucursal_id: UUID
    usuario_id: Optional[UUID] = None  # Optional: will be set from current_user in the endpoint


class DayCloseUpdate(BaseModel):
    """Schema for updating day close (all fields optional)."""
    date: Optional[date] = None
    system_total_cents: Optional[int] = None
    physical_count_cents: Optional[int] = None
    difference_cents: Optional[int] = None
    totals: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class DayCloseRead(DayCloseBase):
    """Schema for reading day close data."""
    id: UUID
    sucursal_id: UUID
    usuario_id: UUID
    notes: Optional[str] = None  # Ensure notes is included in read schema
    created_at: datetime
    updated_at: datetime
    started_at: Optional[str] = None  # ISO format datetime string from totals JSON (hybrid pattern)
    closed_at: Optional[datetime] = None  # Alias for created_at (when day was closed)

    class Config:
        from_attributes = True


class PreviewDayCloseRead(BaseModel):
    """Schema for day close preview (calculated values before closing)."""
    expected_total_cents: int
    initial_cash_cents: int
    cash_received_total_cents: int
    breakdown: Dict[str, Any]
    business_date: str  # YYYY-MM-DD format
    timezone: str
    period: Dict[str, str]  # start_datetime, end_datetime in ISO format

    class Config:
        from_attributes = True




























