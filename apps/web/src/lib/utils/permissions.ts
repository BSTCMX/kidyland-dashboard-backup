/**
 * Permissions utility - Centralized permission matrix.
 * 
 * Single source of truth for all module permissions.
 * Type-safe and easily extensible.
 */
import type { UserRole } from "../types";

export interface ModulePermissions {
  canAccess: boolean;
  canEdit: boolean;
  canCreate: boolean;
  canDelete: boolean;
}

type Module = "admin" | "recepcion" | "kidibar" | "monitor";

// Permission cache for performance
const permissionCache = new Map<string, ModulePermissions>();

/**
 * Get permissions for a user role and module.
 * 
 * @param userRole - User's role
 * @param module - Module to check permissions for
 * @returns ModulePermissions object
 */
export function getModulePermissions(
  userRole: UserRole,
  module: Module
): ModulePermissions {
  const cacheKey = `${userRole}:${module}`;
  
  // Check cache first
  if (permissionCache.has(cacheKey)) {
    return permissionCache.get(cacheKey)!;
  }

  // Permission matrix - Single source of truth
  const permissions: Record<UserRole, Record<Module, ModulePermissions>> = {
    super_admin: {
      admin: { canAccess: true, canEdit: true, canCreate: true, canDelete: true },
      recepcion: { canAccess: true, canEdit: true, canCreate: true, canDelete: true },
      kidibar: { canAccess: true, canEdit: true, canCreate: true, canDelete: true },
      monitor: { canAccess: true, canEdit: true, canCreate: true, canDelete: true },
    },
    admin_viewer: {
      admin: { canAccess: true, canEdit: false, canCreate: false, canDelete: false },
      recepcion: { canAccess: true, canEdit: false, canCreate: false, canDelete: false },
      kidibar: { canAccess: true, canEdit: false, canCreate: false, canDelete: false },
      monitor: { canAccess: true, canEdit: false, canCreate: false, canDelete: false },
    },
    recepcion: {
      admin: { canAccess: false, canEdit: false, canCreate: false, canDelete: false },
      recepcion: { canAccess: true, canEdit: true, canCreate: true, canDelete: true },
      kidibar: { canAccess: true, canEdit: false, canCreate: false, canDelete: false }, // READ+ supervision
      monitor: { canAccess: false, canEdit: false, canCreate: false, canDelete: false },
    },
    kidibar: {
      admin: { canAccess: false, canEdit: false, canCreate: false, canDelete: false },
      recepcion: { canAccess: false, canEdit: false, canCreate: false, canDelete: false },
      kidibar: { canAccess: true, canEdit: true, canCreate: true, canDelete: true },
      monitor: { canAccess: false, canEdit: false, canCreate: false, canDelete: false },
    },
    monitor: {
      admin: { canAccess: false, canEdit: false, canCreate: false, canDelete: false },
      recepcion: { canAccess: true, canEdit: false, canCreate: false, canDelete: false },
      kidibar: { canAccess: true, canEdit: false, canCreate: false, canDelete: false },
      monitor: { canAccess: true, canEdit: true, canCreate: true, canDelete: true },
    },
  };

  const result = permissions[userRole]?.[module] || {
    canAccess: false,
    canEdit: false,
    canCreate: false,
    canDelete: false,
  };

  // Cache result
  permissionCache.set(cacheKey, result);
  
  return result;
}

/**
 * Clear permission cache (useful for testing or role changes).
 */
export function clearPermissionCache(): void {
  permissionCache.clear();
}

/**
 * Check if user can execute day operations (start/close day).
 * 
 * Only kidibar, recepcion, and super_admin can execute day operations.
 * Other roles (admin_viewer, monitor) can view but not execute.
 * 
 * @param userRole - User's role
 * @returns True if user can execute day operations
 */
export function canExecuteDayOperations(userRole: UserRole | undefined): boolean {
  if (!userRole) return false;
  return userRole === "kidibar" || userRole === "recepcion" || userRole === "super_admin";
}





























