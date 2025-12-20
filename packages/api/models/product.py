"""
Product model.
"""
import uuid
import json
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Boolean, JSON, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database import Base
from models.mixins import SoftDeleteMixin


class Product(Base, SoftDeleteMixin):
    __tablename__ = "products"

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
    sucursales_ids = Column(
        JSON,
        nullable=True,
        default=list
    )  # List of UUIDs for multiple sucursales support
    name = Column(String(100), nullable=False)
    price_cents = Column(Integer, nullable=False)
    stock_qty = Column(Integer, nullable=False, default=0)
    threshold_alert_qty = Column(Integer, nullable=False, default=0)
    enabled_for_package = Column(Boolean, nullable=False, default=False)
    package_deduction_qty = Column(Integer, nullable=False, default=0)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    # sucursal = relationship("Sucursal", back_populates="products")
