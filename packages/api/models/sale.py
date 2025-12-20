"""
Sale model.
"""
import uuid
import json
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from database import Base


class Sale(Base):
    __tablename__ = "sales"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    sucursal_id = Column(
        UUID(as_uuid=True),
        ForeignKey("sucursales.id"),
        nullable=False,
        index=True
    )
    usuario_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )
    tipo = Column(String(20), nullable=False)  # "service", "day", "package", "product"
    
    # Pricing information
    subtotal_cents = Column(Integer, nullable=False)
    discount_cents = Column(Integer, nullable=False, default=0)
    total_cents = Column(Integer, nullable=False)
    
    # Payer information
    payer_name = Column(String(100), nullable=True)
    payer_phone = Column(String(20), nullable=True)
    payer_signature = Column(String, nullable=True)  # Base64 encoded signature image
    
    # Payment information
    payment_method = Column(String(20), nullable=False)  # "cash", "card", "transfer"
    cash_received_cents = Column(Integer, nullable=True)
    card_auth_code = Column(String(50), nullable=True)
    transfer_reference = Column(String(100), nullable=True)  # Transfer reference number/folio
    
    # Children information (for multi-child sales)
    # JSONB format: [{"name": "Juan", "age": 5}, {"name": "María", "age": 7}]
    # Using JSONB for better indexing and query performance
    children = Column(JSONB, nullable=True)
    
    # Scheduled date for package sales (when package is scheduled for a future date)
    scheduled_date = Column(DateTime(timezone=False), nullable=True, index=True)
    
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    # sucursal = relationship("Sucursal", back_populates="sales")
    # usuario = relationship("User", back_populates="sales")
    items = relationship("SaleItem", backref="sale", cascade="all, delete-orphan")
