"""
Timer Pydantic schemas.
"""
from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


class TimerBase(BaseModel):
    """Base timer schema with common fields."""
    sale_id: UUID
    service_id: UUID
    start_delay_minutes: int = 0
    child_name: Optional[str] = None
    child_age: Optional[int] = None
    status: str = "active"  # "active", "completed", "cancelled"
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    entry_time: Optional[datetime] = None
    exit_time: Optional[datetime] = None

    class Config:
        from_attributes = True


class TimerCreate(TimerBase):
    """Schema for creating a new timer."""
    pass


class TimerUpdate(BaseModel):
    """Schema for updating a timer."""
    status: Optional[str] = None
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    entry_time: Optional[datetime] = None
    exit_time: Optional[datetime] = None
    child_name: Optional[str] = None
    child_age: Optional[int] = None

    class Config:
        from_attributes = True


class TimerRead(TimerBase):
    """Schema for reading a timer."""
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
