"""
DayClose model.
"""
import uuid
import json
from datetime import datetime, date, timezone
from sqlalchemy import Column, String, Integer, Date, JSON, ForeignKey, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from database import Base


class DayClose(Base):
    __tablename__ = "day_closes"

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
    date = Column(Date, nullable=False, index=True)
    system_total_cents = Column(Integer, nullable=False)
    physical_count_cents = Column(Integer, nullable=False)
    difference_cents = Column(Integer, nullable=False)
    totals = Column(JSON, nullable=True)  # Additional totals JSON
    notes = Column(Text, nullable=True)  # Optional notes/observations for the day close
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
