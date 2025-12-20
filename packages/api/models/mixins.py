"""
SQLAlchemy mixins for reusable model functionality.

This module provides mixins that can be used across multiple models
to add common functionality like soft delete.
"""
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime
from sqlalchemy.ext.declarative import declared_attr


class SoftDeleteMixin:
    """
    Mixin for soft delete functionality.
    
    Adds deleted_at timestamp field and provides methods for soft delete.
    Models using this mixin can be soft-deleted (marked with deleted_at)
    instead of being permanently removed from the database.
    
    Usage:
        class Service(Base, SoftDeleteMixin):
            __tablename__ = "services"
            # ... other fields
    """
    
    @declared_attr
    def deleted_at(cls):
        """Timestamp when the record was soft-deleted (None if not deleted)."""
        return Column(
            DateTime(timezone=True),
            nullable=True,
            default=None,
            index=True
        )
    
    def soft_delete(self):
        """
        Mark this record as soft-deleted by setting deleted_at timestamp.
        
        Also sets active=False for backward compatibility.
        """
        self.deleted_at = datetime.now(timezone.utc)
        if hasattr(self, 'active'):
            self.active = False
    
    def restore(self):
        """
        Restore a soft-deleted record by clearing deleted_at.
        
        Also sets active=True if the model has an active field.
        """
        self.deleted_at = None
        if hasattr(self, 'active'):
            self.active = True
    
    @property
    def is_deleted(self) -> bool:
        """Check if this record is soft-deleted."""
        return self.deleted_at is not None









