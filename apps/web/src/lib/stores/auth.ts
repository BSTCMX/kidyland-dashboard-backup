/**
 * Authentication store wrapper for web app.
 * 
 * Re-exports auth utilities from @kidyland/utils and adds app-specific functionality
 * (role-based routing, redirects, etc.) while using the single source of truth store.
 */
import { browser } from "$app/environment";
import { goto } from "$app/navigation";
import { ROLE_ROUTES } from "../types";

// Re-export stores and functions from @kidyland/utils (single source of truth)
export {
  user,
  token,
  getToken,
  getUser,
  hasRole,
  hasAnyRole,
  getUsernameFromToken,
  isTokenStoreConsistent,
  hasAccess,
  canEdit,
  hasAccessSecure,
  canEditSecure,
  DEFAULT_ROUTE_PERMISSIONS,
  DEFAULT_EDIT_PERMISSIONS,
  type RoutePermissions,
  type EditPermissions,
} from "@kidyland/utils";

// Re-export permission utilities from local permissions module
export {
  getModulePermissions,
  canCreateSales,
  canExecuteDayOperations,
  clearPermissionCache,
  type ModulePermissions,
} from "../utils/permissions";

// Import login and logout to wrap them
import { login as baseLogin, logout as baseLogout } from "@kidyland/utils";

/**
 * Login with username and password (app-specific version with redirects).
 * 
 * @param username - User username
 * @param password - User password
 * @throws Error if login fails
 */
export async function login(username: string, password: string): Promise<void> {
  await baseLogin(username, password, async (userData) => {
    // Redirect based on role after successful login
    if (browser && userData?.role) {
      const targetRoute = ROLE_ROUTES[userData.role as keyof typeof ROLE_ROUTES];
      if (targetRoute) {
        goto(targetRoute);
      }
    }
  });
}

/**
 * Logout and clear all auth state (app-specific version with redirect).
 */
export function logout(): void {
  baseLogout(() => {
    // Redirect to login page after logout
    if (browser) {
      goto("/");
    }
  });
}

// Import getUser directly
import { getUser as getSharedUser } from "@kidyland/utils";

/**
 * Get route for user's role.
 * 
 * @returns Route path for current user's role or null
 */
export function getRoleRoute(): string | null {
  const currentUser = getSharedUser();
  if (!currentUser?.role) return null;
  return ROLE_ROUTES[currentUser.role as keyof typeof ROLE_ROUTES] || null;
}