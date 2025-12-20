/**
 * Service filtering utilities.
 * 
 * Provides reusable functions for determining filter parameters
 * based on user role and permissions.
 * 
 * Pattern:
 * - super_admin and admin_viewer: See all services (no filter)
 * - recepcion and other roles: See services filtered by sucursal_id
 */

import type { User } from "@kidyland/shared/types";
import { hasRole } from "$lib/stores/auth";

/**
 * Determine the sucursal_id filter parameter based on user role.
 * 
 * Logic:
 * - super_admin: Returns undefined (no filter, see all services)
 * - admin_viewer: Returns undefined (no filter, see all services - read-only)
 * - recepcion and other roles: Returns user's sucursal_id (filtered view)
 * 
 * @param user - Current user object (can be null/undefined)
 * @returns sucursal_id string if user should be filtered, undefined if user should see all
 */
export function getServiceFilterSucursalId(user: User | null | undefined): string | undefined {
  if (!user) {
    return undefined;
  }

  // Super admin and admin_viewer see all services (no filter)
  if (hasRole("super_admin") || hasRole("admin_viewer")) {
    return undefined;
  }

  // Other roles (recepcion, etc.) see only their sucursal's services
  return user.sucursal_id || undefined;
}

/**
 * Check if current user should see all services (no filtering).
 * 
 * @param user - Current user object (can be null/undefined)
 * @returns true if user should see all services, false if filtered
 */
export function shouldShowAllServices(user: User | null | undefined): boolean {
  if (!user) {
    return false;
  }
  return hasRole("super_admin") || hasRole("admin_viewer");
}

