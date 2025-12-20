"""
SaleItem Pydantic schemas.
"""
from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


class SaleItemBase(BaseModel):
    """Base sale item schema with common fields."""
    type: str  # "product", "service", "package"
    ref_id: UUID
    quantity: int = 1
    unit_price_cents: int
    subtotal_cents: int

    class Config:
        from_attributes = True


class SaleItemCreate(SaleItemBase):
    """Schema for creating a new sale item."""
    pass


class SaleItemRead(SaleItemBase):
    """Schema for reading sale item data."""
    id: UUID
    sale_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True
































