"""
Permission Service - Business logic for user permissions.

Features:
- Check user permissions
- Grant/revoke permissions
- Apply permission templates
- Get user permissions
"""
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload
import json

from models.user_permission import UserPermission, PermissionTemplate
from models.user import User

logger = logging.getLogger(__name__)


class PermissionService:
    """Service for managing user permissions."""
    
    async def check_permission(
        self,
        db: AsyncSession,
        user_id: str,
        resource: str,
        action: str,
        permission_type: str = "module_access"
    ) -> bool:
        """
        Check if user has a specific permission.
        
        Args:
            db: Database session
            user_id: User ID to check
            resource: Resource name (e.g., 'kidibar', 'recepcion')
            action: Action name (e.g., 'view', 'edit')
            permission_type: Type of permission (default: 'module_access')
            
        Returns:
            True if permission is granted, False otherwise
        """
        try:
            query = select(UserPermission).where(
                and_(
                    UserPermission.user_id == user_id,
                    UserPermission.permission_type == permission_type,
                    UserPermission.resource == resource,
                    UserPermission.action == action,
                    UserPermission.granted == True
                )
            )
            result = await db.execute(query)
            permission = result.scalar_one_or_none()
            
            return permission is not None
        except Exception as e:
            logger.error(f"Error checking permission: {e}", exc_info=True)
            return False
    
    async def grant_permission(
        self,
        db: AsyncSession,
        user_id: str,
        resource: str,
        action: str,
        permission_type: str = "module_access"
    ) -> UserPermission:
        """
        Grant a permission to a user.
        
        Args:
            db: Database session
            user_id: User ID
            resource: Resource name
            action: Action name
            permission_type: Type of permission
            
        Returns:
            Created or updated UserPermission
        """
        # Check if permission already exists
        query = select(UserPermission).where(
            and_(
                UserPermission.user_id == user_id,
                UserPermission.permission_type == permission_type,
                UserPermission.resource == resource,
                UserPermission.action == action
            )
        )
        result = await db.execute(query)
        existing = result.scalar_one_or_none()
        
        if existing:
            existing.granted = True
            await db.commit()
            await db.refresh(existing)
            return existing
        else:
            permission = UserPermission(
                user_id=user_id,
                permission_type=permission_type,
                resource=resource,
                action=action,
                granted=True
            )
            db.add(permission)
            await db.commit()
            await db.refresh(permission)
            return permission
    
    async def revoke_permission(
        self,
        db: AsyncSession,
        user_id: str,
        resource: str,
        action: str,
        permission_type: str = "module_access"
    ) -> Optional[UserPermission]:
        """
        Revoke a permission from a user.
        
        Args:
            db: Database session
            user_id: User ID
            resource: Resource name
            action: Action name
            permission_type: Type of permission
            
        Returns:
            Updated UserPermission if found, None otherwise
        """
        query = select(UserPermission).where(
            and_(
                UserPermission.user_id == user_id,
                UserPermission.permission_type == permission_type,
                UserPermission.resource == resource,
                UserPermission.action == action
            )
        )
        result = await db.execute(query)
        permission = result.scalar_one_or_none()
        
        if permission:
            permission.granted = False
            await db.commit()
            await db.refresh(permission)
            return permission
        
        return None
    
    async def get_user_permissions(
        self,
        db: AsyncSession,
        user_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get all permissions for a user.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            List of permission dictionaries
        """
        query = select(UserPermission).where(
            and_(
                UserPermission.user_id == user_id,
                UserPermission.granted == True
            )
        )
        result = await db.execute(query)
        permissions = result.scalars().all()
        
        return [
            {
                "id": str(perm.id),
                "permission_type": perm.permission_type,
                "resource": perm.resource,
                "action": perm.action,
                "granted": perm.granted
            }
            for perm in permissions
        ]
    
    async def apply_template(
        self,
        db: AsyncSession,
        user_id: str,
        template_name: str
    ) -> List[UserPermission]:
        """
        Apply a permission template to a user.
        
        Args:
            db: Database session
            user_id: User ID
            template_name: Name of the template to apply
            
        Returns:
            List of created/updated permissions
        """
        # Get template
        query = select(PermissionTemplate).where(
            PermissionTemplate.name == template_name
        )
        result = await db.execute(query)
        template = result.scalar_one_or_none()
        
        if not template:
            raise ValueError(f"Template '{template_name}' not found")
        
        # Parse permissions JSON
        try:
            permissions_data = json.loads(template.permissions_json)
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON in template '{template_name}'")
        
        # Apply each permission
        applied_permissions = []
        for perm_data in permissions_data:
            permission = await self.grant_permission(
                db=db,
                user_id=user_id,
                resource=perm_data["resource"],
                action=perm_data["action"],
                permission_type=perm_data.get("permission_type", "module_access")
            )
            applied_permissions.append(permission)
        
        return applied_permissions
    
    async def get_templates(
        self,
        db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """
        Get all permission templates.
        
        Args:
            db: Database session
            
        Returns:
            List of template dictionaries
        """
        query = select(PermissionTemplate)
        result = await db.execute(query)
        templates = result.scalars().all()
        
        return [
            {
                "id": str(template.id),
                "name": template.name,
                "description": template.description,
                "permissions": json.loads(template.permissions_json) if template.permissions_json else []
            }
            for template in templates
        ]
    
    async def set_user_permissions(
        self,
        db: AsyncSession,
        user_id: str,
        permissions: List[Dict[str, str]]
    ) -> List[UserPermission]:
        """
        Set multiple permissions for a user (replaces existing).
        
        Args:
            db: Database session
            user_id: User ID
            permissions: List of permission dictionaries with keys:
                - permission_type
                - resource
                - action
                - granted (optional, defaults to True)
                
        Returns:
            List of created/updated permissions
        """
        # First, revoke all existing permissions for this user
        query = select(UserPermission).where(
            UserPermission.user_id == user_id
        )
        result = await db.execute(query)
        existing_permissions = result.scalars().all()
        
        for perm in existing_permissions:
            perm.granted = False
        
        # Then, grant new permissions
        created_permissions = []
        for perm_data in permissions:
            permission = await self.grant_permission(
                db=db,
                user_id=user_id,
                resource=perm_data["resource"],
                action=perm_data["action"],
                permission_type=perm_data.get("permission_type", "module_access")
            )
            created_permissions.append(permission)
        
        await db.commit()
        return created_permissions
























