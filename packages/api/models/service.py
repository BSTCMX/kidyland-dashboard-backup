"""
Service model.
"""
import uuid
import json
from datetime import datetime, timezone
from typing import Dict, Any
from sqlalchemy import Column, String, Integer, Boolean, JSON, ForeignKey, DateTime
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database import Base
from models.mixins import SoftDeleteMixin
from utils.json_normalizers import normalize_json_int_keys


class Service(Base, SoftDeleteMixin):
    __tablename__ = "services"

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
    durations_allowed = Column(JSON, nullable=False, default=list)  # List of minutes
    duration_prices = Column(JSON, nullable=False, default=dict)  # Required: {duration_minutes: price_cents} for flexible pricing
    alerts_config = Column(JSON, nullable=False, default=list)  # List of ServiceAlert objects
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
    # sucursal = relationship("Sucursal", back_populates="services")
    
    @hybrid_property
    def duration_prices_normalized(self) -> Dict[int, int]:
        """
        Get duration_prices with all keys normalized to integers.
        
        This property normalizes string keys (e.g., "30") to integers (e.g., 30)
        to handle cases where PostgreSQL JSON columns store numeric keys as strings.
        
        This is a defensive property that ensures consistent access regardless of
        how the data was stored in the database.
        
        Returns:
            Dictionary with integer keys mapping duration_minutes to price_cents.
            Returns empty dict if duration_prices is None or invalid.
        """
        return normalize_json_int_keys(self.duration_prices)
