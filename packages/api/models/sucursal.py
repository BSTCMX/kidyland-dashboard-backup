"""
Sucursal model.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database import Base


class Sucursal(Base):
    __tablename__ = "sucursales"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    identifier = Column(String(20), nullable=False, unique=True, index=True)  # e.g., "suc01"
    name = Column(String(100), nullable=False)
    address = Column(String(255), nullable=True)
    timezone = Column(String(50), nullable=False, default="America/Mexico_City")
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
    # users = relationship("User", back_populates="sucursal")
    # products = relationship("Product", back_populates="sucursal")
    # services = relationship("Service", back_populates="sucursal")
    # sales = relationship("Sale", back_populates="sucursal")









