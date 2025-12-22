"""
Package model.
"""
import uuid
import json
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Text, JSON, ForeignKey, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database import Base


class Package(Base):
    __tablename__ = "packages"

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
    description = Column(Text, nullable=True)
    price_cents = Column(Integer, nullable=False)
    included_items = Column(JSON, nullable=False, default=list)  # List of PackageItem objects
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
    # sucursal = relationship("Sucursal", back_populates="packages")
