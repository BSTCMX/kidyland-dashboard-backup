"""
SaleItem model.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from database import Base


class SaleItem(Base):
    __tablename__ = "sale_items"

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
    type = Column(String(20), nullable=False)  # "product", "service", "package"
    ref_id = Column(
        UUID(as_uuid=True),
        nullable=False
    )  # ID of product/service/package
    quantity = Column(Integer, nullable=False, default=1)
    unit_price_cents = Column(Integer, nullable=False)
    subtotal_cents = Column(Integer, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )























