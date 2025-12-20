"""
TimerHistory Pydantic schemas.
"""
from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


class TimerHistoryBase(BaseModel):
    """Base timer history schema with common fields."""
    event_type: str  # "start", "extend", "end"
    minutes_added: Optional[int] = None

    class Config:
        from_attributes = True


class TimerHistoryCreate(TimerHistoryBase):
    """Schema for creating a new timer history entry."""
    timer_id: UUID


class TimerHistoryRead(TimerHistoryBase):
    """Schema for reading timer history data."""
    id: UUID
    timer_id: UUID
    timestamp: datetime

    class Config:
        from_attributes = True
































