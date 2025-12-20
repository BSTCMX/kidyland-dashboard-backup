"""
Permission management endpoints.

Security Rules:
- Only super_admin can manage permissions
- Users can check their own permissions
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID
from database import get_db
from schemas.permission import (
    UserPermissionRead,
    PermissionTemplateRead,
    ApplyTemplateRequest,
    SetPermissionsRequest,
    CheckPermissionRequest,
    CheckPermissionResponse
)
from models.user import User
from services.permission_service import PermissionService
from utils.auth import require_role, get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/permissions", tags=["permissions"])
permission_service = PermissionService()


@router.get("/users/{user_id}", response_model=List[UserPermissionRead], dependencies=[Depends(require_role("super_admin"))])
async def get_user_permissions(
    user_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all permissions for a user.
    
    Security: Only super_admin can view user permissions.
    """
    try:
        permissions = await permission_service.get_user_permissions(db, str(user_id))
        return permissions
    except Exception as e:
        logger.error(f"Error getting user permissions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting user permissions"
        )


@router.post("/users/{user_id}/apply-template", dependencies=[Depends(require_role("super_admin"))])
async def apply_permission_template(
    user_id: UUID,
    request: ApplyTemplateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Apply a permission template to a user.
    
    Security: Only super_admin can apply templates.
    """
    try:
        permissions = await permission_service.apply_template(
            db=db,
            user_id=str(user_id),
            template_name=request.template_name
        )
        return {
            "message": f"Template '{request.template_name}' applied successfully",
            "permissions_count": len(permissions)
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error applying template: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error applying template"
        )


@router.post("/users/{user_id}/set", dependencies=[Depends(require_role("super_admin"))])
async def set_user_permissions(
    user_id: UUID,
    request: SetPermissionsRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Set multiple permissions for a user (replaces existing).
    
    Security: Only super_admin can set permissions.
    """
    try:
        permissions_data = [
            {
                "permission_type": p.permission_type,
                "resource": p.resource,
                "action": p.action,
                "granted": p.granted
            }
            for p in request.permissions
        ]
        permissions = await permission_service.set_user_permissions(
            db=db,
            user_id=str(user_id),
            permissions=permissions_data
        )
        return {
            "message": "Permissions set successfully",
            "permissions_count": len(permissions)
        }
    except Exception as e:
        logger.error(f"Error setting permissions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error setting permissions"
        )


@router.get("/templates", response_model=List[PermissionTemplateRead], dependencies=[Depends(require_role("super_admin"))])
async def get_permission_templates(
    db: AsyncSession = Depends(get_db)
):
    """
    Get all permission templates.
    
    Security: Only super_admin can view templates.
    """
    try:
        templates = await permission_service.get_templates(db)
        return templates
    except Exception as e:
        logger.error(f"Error getting templates: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting templates"
        )


@router.post("/check", response_model=CheckPermissionResponse)
async def check_permission(
    request: CheckPermissionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Check if current user has a specific permission.
    
    Security: Any authenticated user can check their own permissions.
    """
    try:
        granted = await permission_service.check_permission(
            db=db,
            user_id=str(current_user.id),
            resource=request.resource,
            action=request.action,
            permission_type=request.permission_type
        )
        return CheckPermissionResponse(
            granted=granted,
            resource=request.resource,
            action=request.action
        )
    except Exception as e:
        logger.error(f"Error checking permission: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error checking permission"
        )
























