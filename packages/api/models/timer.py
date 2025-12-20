"""
Timer model.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database import Base


class Timer(Base):
    __tablename__ = "timers"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    sale_id = Column(
        UUID(as_uuid=True),
        ForeignKey("sales.id"),
        nullable=False,
        index=True
    )
    service_id = Column(
        UUID(as_uuid=True),
        ForeignKey("services.id"),
        nullable=False,
        index=True
    )
    start_delay_minutes = Column(Integer, default=0, nullable=False)
    child_name = Column(String(255), nullable=True)
    child_age = Column(Integer, nullable=True)
    status = Column(String(20), default="active", nullable=False)  # "active", "completed", "cancelled"
    start_at = Column(
        DateTime(timezone=True),
        nullable=True
    )
    end_at = Column(
        DateTime(timezone=True),
        nullable=True
    )
    entry_time = Column(
        DateTime(timezone=True),
        nullable=True
    )
    exit_time = Column(
        DateTime(timezone=True),
        nullable=True
    )
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
    # sale = relationship("Sale", back_populates="timers")
    # service = relationship("Service", back_populates="timers")
    # history = relationship("TimerHistory", back_populates="timer")
