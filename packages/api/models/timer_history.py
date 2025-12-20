"""
TimerHistory model.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from database import Base


class TimerHistory(Base):
    __tablename__ = "timer_history"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    timer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("timers.id"),
        nullable=False,
        index=True
    )
    event_type = Column(String(20), nullable=False)  # "start", "extend", "end"
    minutes_added = Column(Integer, nullable=True)  # Only for "extend" events
    timestamp = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )























