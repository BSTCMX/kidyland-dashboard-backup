"""
Product Pydantic schemas.
"""
from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


class ProductBase(BaseModel):
    """Base product schema with common fields."""
    name: str
    price_cents: int
    stock_qty: int = 0
    threshold_alert_qty: int = 0
    enabled_for_package: bool = False
    package_deduction_qty: int = 0
    active: bool = True
    sucursal_id: Optional[UUID] = None  # Kept for backward compatibility
    sucursales_ids: Optional[list[str]] = []  # New: support for multiple sucursales

    class Config:
        from_attributes = True


class ProductCreate(ProductBase):
    """Schema for creating a new product."""
    sucursales_ids: list[str]  # Required: at least one sucursal
    sucursal_id: Optional[UUID] = None  # Optional: will be derived from sucursales_ids if not provided


class ProductUpdate(BaseModel):
    """Schema for updating product (all fields optional)."""
    name: Optional[str] = None
    price_cents: Optional[int] = None
    stock_qty: Optional[int] = None
    threshold_alert_qty: Optional[int] = None
    enabled_for_package: Optional[bool] = None
    package_deduction_qty: Optional[int] = None
    active: Optional[bool] = None
    sucursales_ids: Optional[list[str]] = None
    sucursal_id: Optional[UUID] = None  # Optional: for backward compatibility

    class Config:
        from_attributes = True


class ProductRead(ProductBase):
    """Schema for reading product data."""
    id: UUID
    sucursal_id: UUID  # Kept for backward compatibility
    sucursales_ids: Optional[list[str]] = []  # New: support for multiple sucursales
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True














