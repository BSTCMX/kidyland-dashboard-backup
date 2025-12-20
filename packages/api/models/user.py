"""
User model.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database import Base
from models.mixins import SoftDeleteMixin
import enum


class UserRole(str, enum.Enum):
    """Valid user roles."""
    SUPER_ADMIN = "super_admin"
    ADMIN_VIEWER = "admin_viewer"
    RECEPCION = "recepcion"
    KIDIBAR = "kidibar"
    MONITOR = "monitor"


class User(Base, SoftDeleteMixin):
    __tablename__ = "users"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    username = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(
        SQLEnum(UserRole),
        nullable=False,
        default=UserRole.MONITOR
    )
    # Valid roles: super_admin, admin_viewer, recepcion, kidibar, monitor
    # Only super_admin can create/update/delete users
    is_active = Column(Boolean, default=True, nullable=False)
    sucursal_id = Column(
        UUID(as_uuid=True),
        ForeignKey("sucursales.id"),
        nullable=True
    )
    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
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
    last_login = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    # sucursal = relationship("Sucursal", back_populates="users")
    # creator = relationship("User", remote_side=[id], backref="created_users")

