"""
Timer Alert Model.

Persistent storage for timer alerts with delivery tracking.
Supports reliable alert delivery and recovery mechanisms.
"""
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    Integer,
    DateTime,
    ForeignKey,
    CheckConstraint,
    UniqueConstraint,
    Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from database import Base


class TimerAlert(Base):
    """
    Timer Alert model for persistent alert tracking.
    
    Stores alerts with status tracking to ensure reliable delivery
    even across server restarts or client disconnections.
    """
    __tablename__ = "timer_alerts"
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False
    )
    timer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("timers.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    alert_minutes = Column(
        Integer,
        nullable=False,
        comment="Minutes before timer end when alert should trigger (e.g., 1, 5, 10, 15)"
    )
    triggered_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )
    delivered_at = Column(
        DateTime(timezone=True),
        nullable=True
    )
    acknowledged_at = Column(
        DateTime(timezone=True),
        nullable=True
    )
    status = Column(
        String(20),
        default="pending",
        nullable=False,
        comment="Alert status: pending, delivered, acknowledged, failed"
    )
    retry_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Number of delivery retry attempts"
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
    timer = relationship("Timer", back_populates="alerts")
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'delivered', 'acknowledged', 'failed')",
            name="timer_alerts_status_check"
        ),
        CheckConstraint(
            "alert_minutes > 0",
            name="timer_alerts_alert_minutes_check"
        ),
        UniqueConstraint(
            "timer_id",
            "alert_minutes",
            name="timer_alerts_unique_alert"
        ),
        Index(
            "idx_timer_alerts_status",
            "status",
            postgresql_where=Column("status") == "pending"
        ),
        Index(
            "idx_timer_alerts_status_triggered",
            "status",
            "triggered_at",
            postgresql_where=Column("status") == "pending"
        ),
    )
    
    def __repr__(self):
        return (
            f"<TimerAlert(id={self.id}, timer_id={self.timer_id}, "
            f"alert_minutes={self.alert_minutes}, status={self.status})>"
        )
    
    def to_dict(self):
        """Convert alert to dictionary representation."""
        return {
            "id": str(self.id),
            "timer_id": str(self.timer_id),
            "alert_minutes": self.alert_minutes,
            "triggered_at": self.triggered_at.isoformat() if self.triggered_at else None,
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "status": self.status,
            "retry_count": self.retry_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
