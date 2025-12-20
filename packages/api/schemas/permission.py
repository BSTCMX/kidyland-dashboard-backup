"""
Permission Pydantic schemas.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime


class UserPermissionBase(BaseModel):
    """Base permission schema."""
    permission_type: str = Field(..., description="Type: 'dashboard_access', 'module_access', 'action_access'")
    resource: str = Field(..., description="Resource: 'kidibar', 'recepcion', 'admin', etc.")
    action: str = Field(..., description="Action: 'view', 'edit', 'create', 'delete', 'export'")
    granted: bool = Field(default=True, description="Whether permission is granted")


class UserPermissionCreate(UserPermissionBase):
    """Schema for creating a permission."""
    user_id: UUID


class UserPermissionRead(UserPermissionBase):
    """Schema for reading a permission."""
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PermissionTemplateRead(BaseModel):
    """Schema for reading a permission template."""
    id: UUID
    name: str
    description: Optional[str]
    permissions: List[dict]
    
    class Config:
        from_attributes = True


class ApplyTemplateRequest(BaseModel):
    """Schema for applying a template."""
    template_name: str


class SetPermissionsRequest(BaseModel):
    """Schema for setting multiple permissions."""
    permissions: List[UserPermissionBase]


class CheckPermissionRequest(BaseModel):
    """Schema for checking a permission."""
    resource: str
    action: str
    permission_type: str = "module_access"


class CheckPermissionResponse(BaseModel):
    """Response for permission check."""
    granted: bool
    resource: str
    action: str
























