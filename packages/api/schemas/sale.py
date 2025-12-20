"""
Sale Pydantic schemas.
"""
from pydantic import BaseModel, model_validator
from typing import Optional, List
from uuid import UUID
from datetime import datetime, date


class SaleBase(BaseModel):
    """Base sale schema with common fields."""
    sucursal_id: UUID
    usuario_id: UUID
    tipo: str  # "product", "service", "package"
    subtotal_cents: int
    discount_cents: Optional[int] = 0
    total_cents: int
    payment_method: str  # "cash", "card", "transfer"
    payer_name: Optional[str] = None
    payer_phone: Optional[str] = None
    payer_signature: Optional[str] = None
    cash_received_cents: Optional[int] = None
    card_auth_code: Optional[str] = None
    transfer_reference: Optional[str] = None

    class Config:
        from_attributes = True


class ChildInfo(BaseModel):
    """Schema for child information in multi-child sales."""
    name: str
    age: Optional[int] = None


class SaleCreate(SaleBase):
    """Schema for creating a new sale."""
    items: Optional[List[dict]] = None  # Sale items will be created separately
    child_age: Optional[int] = None  # Child age for service sales (stored in timer) - DEPRECATED: use children array
    child_name: Optional[str] = None  # Child name for service sales (stored in timer) - DEPRECATED: use children array
    children: Optional[List[ChildInfo]] = None  # List of children for multi-child sales
    scheduled_date: Optional[date] = None  # Scheduled date for package sales (when package is scheduled for a future date)
    
    @model_validator(mode='after')
    def validate_children_for_service(self):
        """
        Validate children information for service sales.
        
        Business rules:
        - For service sales, either child_name (legacy) or children array must be provided
        - If children array is provided, quantity in items must match len(children)
        - For backward compatibility, child_name is still accepted but children array is preferred
        """
        if self.tipo == "service":
            # Check if using new multi-child format
            if self.children is not None and len(self.children) > 0:
                # Validate children array
                for child in self.children:
                    if not child.name or not child.name.strip():
                        raise ValueError(
                            "Each child in children array must have a non-empty name."
                        )
                
                # Validate quantity matches children count
                if self.items:
                    service_item = next(
                        (item for item in self.items if item.get("type") == "service"),
                        None
                    )
                    if service_item:
                        quantity = service_item.get("quantity", 1)
                        if quantity != len(self.children):
                            raise ValueError(
                                f"Quantity ({quantity}) must match number of children ({len(self.children)}). "
                                f"Please ensure quantity in sale item matches the number of children."
                            )
            else:
                # Legacy single-child format: validate child_name
                if not self.child_name or not self.child_name.strip():
                    raise ValueError(
                        "For service sales, either child_name (legacy) or children array must be provided. "
                        "Please provide at least one child's name."
                    )
        return self


class SaleUpdate(BaseModel):
    """Schema for updating a sale."""
    payment_method: Optional[str] = None
    payer_name: Optional[str] = None
    payer_phone: Optional[str] = None
    payer_signature: Optional[str] = None
    cash_received_cents: Optional[int] = None
    card_auth_code: Optional[str] = None
    transfer_reference: Optional[str] = None

    class Config:
        from_attributes = True


class SaleRead(SaleBase):
    """Schema for reading a sale."""
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TimerExtensionRequest(BaseModel):
    """Schema for extending a timer with a new sale."""
    duration_minutes: int  # Duration to extend (must be in service.durations_allowed)
    payment_method: str  # "cash", "card", "transfer"
    payer_name: Optional[str] = None  # Optional, defaults to original sale payer_name
    payer_phone: Optional[str] = None  # Optional, defaults to original sale payer_phone
    payer_signature: Optional[str] = None  # Optional, defaults to original sale payer_signature
    cash_received_cents: Optional[int] = None  # Required if payment_method is "cash"
    card_auth_code: Optional[str] = None  # Required if payment_method is "card"
    transfer_reference: Optional[str] = None  # Required if payment_method is "transfer"
    
    @model_validator(mode='after')
    def validate_payment_fields(self):
        """Validate payment method specific fields."""
        if self.payment_method == "cash":
            if self.cash_received_cents is None:
                raise ValueError("cash_received_cents is required for cash payment")
        elif self.payment_method == "card":
            if not self.card_auth_code or not self.card_auth_code.strip():
                raise ValueError("card_auth_code is required for card payment")
        elif self.payment_method == "transfer":
            if not self.transfer_reference or not self.transfer_reference.strip():
                raise ValueError("transfer_reference is required for transfer payment")
        else:
            raise ValueError(f"Invalid payment_method: {self.payment_method}. Must be one of: cash, card, transfer")
        return self
