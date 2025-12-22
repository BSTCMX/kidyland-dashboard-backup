"""
Package Pydantic schemas.
"""
from pydantic import BaseModel, model_validator
from typing import Optional, List
from uuid import UUID
from datetime import datetime


class PackageItem(BaseModel):
    """
    Package item schema with automatic validation.
    
    Rules (enforced automatically):
    - Must have exactly one of: product_id OR service_id (not both, not neither)
    - If product_id: must have quantity, cannot have duration_minutes
    - If service_id: duration_minutes is optional, cannot have quantity
    """
    product_id: Optional[UUID] = None
    service_id: Optional[UUID] = None
    quantity: Optional[int] = None  # For products
    duration_minutes: Optional[int] = None  # For services

    @model_validator(mode='after')
    def validate_item_type(self):
        """
        Automatically validate PackageItem structure.
        
        This ensures:
        1. Exactly one of product_id or service_id is provided
        2. Products require quantity, cannot have duration_minutes
        3. Services: duration_minutes is optional (if provided, must be > 0), cannot have quantity
        
        No manual validation needed elsewhere - this is automatic.
        """
        has_product = self.product_id is not None
        has_service = self.service_id is not None
        
        # Rule 1: Must have exactly one type
        if has_product and has_service:
            raise ValueError(
                "PackageItem cannot have both product_id and service_id. "
                "Choose either a product or a service, not both."
            )
        if not has_product and not has_service:
            raise ValueError(
                "PackageItem must have either product_id or service_id. "
                "At least one item type is required."
            )
        
        # Rule 2: Products require quantity, cannot have duration_minutes
        if has_product:
            if self.quantity is None:
                raise ValueError(
                    "PackageItem with product_id must have quantity. "
                    "Products require a quantity value."
                )
            if self.quantity <= 0:
                raise ValueError(
                    f"PackageItem quantity must be greater than 0, got {self.quantity}"
                )
            if self.duration_minutes is not None:
                raise ValueError(
                    "PackageItem with product_id cannot have duration_minutes. "
                    "Duration is only for services (rental by day/duration)."
                )
        
        # Rule 3: Services cannot have quantity, duration_minutes is optional
        if has_service:
            # duration_minutes is optional for services in packages
            # If provided, it must be > 0
            if self.duration_minutes is not None and self.duration_minutes <= 0:
                raise ValueError(
                    f"PackageItem duration_minutes must be greater than 0, got {self.duration_minutes}"
                )
            if self.quantity is not None:
                raise ValueError(
                    "PackageItem with service_id cannot have quantity. "
                    "Services use duration_minutes for rental period, not quantity."
                )
        
        return self


class PackageBase(BaseModel):
    """Base package schema with common fields."""
    name: str
    description: Optional[str] = None
    price_cents: int
    included_items: List[PackageItem] = []
    active: bool = True
    sucursal_id: Optional[UUID] = None  # Kept for backward compatibility
    sucursales_ids: Optional[list[str]] = []  # New: support for multiple sucursales

    class Config:
        from_attributes = True


class PackageCreate(PackageBase):
    """Schema for creating a new package."""
    sucursales_ids: list[str]  # Required: at least one sucursal
    sucursal_id: Optional[UUID] = None  # Optional: will be derived from sucursales_ids if not provided


class PackageUpdate(BaseModel):
    """Schema for updating package (all fields optional)."""
    name: Optional[str] = None
    description: Optional[str] = None
    price_cents: Optional[int] = None
    included_items: Optional[List[PackageItem]] = None
    active: Optional[bool] = None
    sucursales_ids: Optional[list[str]] = None
    sucursal_id: Optional[UUID] = None  # Optional: for backward compatibility

    class Config:
        from_attributes = True


class PackageRead(PackageBase):
    """Schema for reading package data."""
    id: UUID
    sucursal_id: UUID  # Kept for backward compatibility
    sucursales_ids: Optional[list[str]] = []  # New: support for multiple sucursales
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True















