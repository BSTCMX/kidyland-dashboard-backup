"""
User Permission model for granular RBAC.

Separate from base roles, allows fine-grained control over user permissions.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database import Base


class UserPermission(Base):
    """User permission model for granular access control."""
    
    __tablename__ = "user_permissions"
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    permission_type = Column(
        String(50),
        nullable=False,
        comment="Type of permission: 'dashboard_access', 'module_access', 'action_access'"
    )
    resource = Column(
        String(50),
        nullable=False,
        index=True,
        comment="Resource: 'kidibar', 'recepcion', 'admin', 'monitor', 'users', 'products', etc."
    )
    action = Column(
        String(50),
        nullable=False,
        comment="Action: 'view', 'edit', 'create', 'delete', 'export'"
    )
    granted = Column(
        Boolean,
        nullable=False,
        default=True,
        comment="Whether permission is granted (true) or denied (false)"
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
    user = relationship("User", backref="permissions")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('user_id', 'permission_type', 'resource', 'action', name='uq_user_permission'),
        Index('idx_user_permissions_type_resource', 'permission_type', 'resource'),
    )
    
    def __repr__(self):
        return f"<UserPermission(user_id={self.user_id}, resource={self.resource}, action={self.action}, granted={self.granted})>"


class PermissionTemplate(Base):
    """Permission template for predefined permission sets."""
    
    __tablename__ = "permission_templates"
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    name = Column(
        String(100),
        nullable=False,
        unique=True,
        index=True
    )
    description = Column(
        String,
        nullable=True
    )
    permissions_json = Column(
        String,  # JSONB in PostgreSQL, stored as String in SQLAlchemy
        nullable=False,
        comment="JSON array of permission objects"
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
    
    def __repr__(self):
        return f"<PermissionTemplate(name={self.name})>"















