/**
 * Authentication store and utilities.
 * 
 * Handles JWT token management, user state, and API authentication.
 * Includes robust error handling for token expiration and invalid credentials.
 */
import { writable, get } from "svelte/store";
import { browser } from "$app/environment";
import { goto } from "$app/navigation";
import type { User } from "@kidyland/shared/types";

export const user = writable<User | null>(null);
export const token = writable<string | null>(null);

// Load from localStorage on init
if (browser) {
  const storedToken = localStorage.getItem("auth_token");
  const storedUser = localStorage.getItem("auth_user");
  
  if (storedToken) {
    token.set(storedToken);
  }
  
  if (storedUser) {
    try {
      user.set(JSON.parse(storedUser));
    } catch (e) {
      console.error("Error parsing stored user:", e);
      localStorage.removeItem("auth_user");
    }
  }
}

// Sync to localStorage
token.subscribe((value) => {
  if (browser) {
    if (value) {
      localStorage.setItem("auth_token", value);
    } else {
      localStorage.removeItem("auth_token");
    }
  }
});

user.subscribe((value) => {
  if (browser) {
    if (value) {
      localStorage.setItem("auth_user", JSON.stringify(value));
    } else {
      localStorage.removeItem("auth_user");
    }
  }
});

/**
 * Login with username and password.
 * 
 * @param username - User username
 * @param password - User password
 * @param onSuccess - Optional callback after successful login
 * @throws Error if login fails
 */
export async function login(
  username: string,
  password: string,
  onSuccess?: (user: User | null) => void | Promise<void>
): Promise<void> {
  // Clean Architecture: Use runtime detection for environment
  // Same pattern as api-config.ts for consistency
  let apiUrl: string;
  
  try {
    // 1. Explicit override via env variable (highest priority)
    if (import.meta.env.VITE_API_URL) {
      apiUrl = import.meta.env.VITE_API_URL;
    } else if (typeof window !== 'undefined' && window.location) {
      // 2. Runtime detection: check hostname instead of build-time env vars
      // This ensures correct behavior in production builds
      if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        // In development (localhost): use backend port 8000
        apiUrl = "http://localhost:8000";
      } else {
        // In production: use same origin
        apiUrl = window.location.origin;
      }
    } else {
      // 3. Fallback for SSR or non-browser contexts
      // Use build-time detection for SSR context
      if (import.meta.env.MODE === 'production' || import.meta.env.PROD) {
        apiUrl = "";
      } else {
        apiUrl = "http://localhost:8000";
      }
    }
    
    // Validate apiUrl before making request
    if (!apiUrl || typeof apiUrl !== 'string') {
      const error = new Error("Invalid API URL configuration");
      if (import.meta.env.DEV) {
        console.error("[Login] Invalid API URL:", { apiUrl, env: import.meta.env });
      }
      throw error;
    }
    
    // Log in development for debugging
    if (import.meta.env.DEV) {
      console.debug("[Login] Attempting login:", { 
        username, 
        apiUrl: `${apiUrl}/auth/login`,
        mode: import.meta.env.MODE 
      });
      console.log("[Login] Full URL:", `${apiUrl}/auth/login`);
    }
    
    const res = await fetch(`${apiUrl}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password })
    });
  
    // Handle 401 (unauthorized) - token expired or invalid
    if (res.status === 401) {
      if (import.meta.env.DEV) {
        console.error("[Login] 401 Unauthorized - Invalid credentials");
      }
      logout();
      if (browser) {
        goto("/login");
      }
      throw new Error("Invalid credentials");
    }
    
    if (!res.ok) {
      const data = await res.json().catch(() => ({ detail: "Login failed" }));
      const errorMessage = data.detail || `Login failed with status ${res.status}`;
      if (import.meta.env.DEV) {
        console.error("[Login] Request failed:", { status: res.status, detail: data.detail });
      }
      throw new Error(errorMessage);
    }
    
    const data = await res.json();
    
    // Validate response data
    if (!data.access_token || !data.user) {
      const error = new Error("Invalid login response - missing token or user data");
      if (import.meta.env.DEV) {
        console.error("[Login] Invalid response:", data);
      }
      throw error;
    }
    
    // Set token and user
    token.set(data.access_token);
    user.set(data.user);
    
    if (import.meta.env.DEV) {
      console.debug("[Login] Success:", { username: data.user.username, role: data.user.role });
    }
    
    // Call onSuccess callback if provided
    if (onSuccess) {
      await onSuccess(data.user);
    }
  } catch (error: any) {
    // Re-throw with better error message if it's a network error
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
      const networkError = new Error("Network error - unable to reach server. Please check your connection.");
      if (import.meta.env.DEV) {
        console.error("[Login] Network error:", error);
      }
      throw networkError;
    }
    // Re-throw other errors as-is
    throw error;
  }
}

/**
 * Logout and clear all auth state.
 * 
 * @param onLogout - Optional callback after logout
 */
export function logout(onLogout?: () => void | Promise<void>): void {
  token.set(null);
  user.set(null);
  
  if (browser) {
    localStorage.removeItem("auth_token");
    localStorage.removeItem("auth_user");
  }
  
  // Call onLogout callback if provided
  if (onLogout) {
    Promise.resolve(onLogout()).catch(console.error);
  }
}

/**
 * Get current auth token.
 * 
 * @returns Current token or null
 */
export function getToken(): string | null {
  return get(token);
}

/**
 * Get current user.
 * 
 * @returns Current user or null
 */
export function getUser(): User | null {
  return get(user);
}

/**
 * Check if user has a specific role.
 * 
 * @param role - Role to check
 * @returns True if user has the role
 */
export function hasRole(role: User["role"]): boolean {
  const currentUser = get(user);
  return currentUser?.role === role;
}

/**
 * Check if user has any of the specified roles.
 * 
 * @param roles - Roles to check
 * @returns True if user has any of the roles
 */
export function hasAnyRole(roles: User["role"][]): boolean {
  const currentUser = get(user);
  if (!currentUser) return false;
  return roles.includes(currentUser.role);
}

// Permission types
export type UserRole = User["role"];
export type RoutePermissions = Record<string, UserRole[]>;
export type EditPermissions = Record<string, UserRole[]>;

// Default route permissions
export const DEFAULT_ROUTE_PERMISSIONS: RoutePermissions = {
  "/admin": ["super_admin"],
  "/admin-viewer": ["admin_viewer", "super_admin"],
  "/recepcion": ["super_admin", "admin_viewer", "recepcion", "monitor"],
  "/kidibar": ["super_admin", "admin_viewer", "recepcion", "kidibar", "monitor"],
  "/monitor": ["super_admin", "admin_viewer", "monitor"]
};

// Default edit permissions
export const DEFAULT_EDIT_PERMISSIONS: EditPermissions = {
  admin: ["super_admin"],
  recepcion: ["super_admin", "recepcion"],
  kidibar: ["super_admin", "kidibar", "recepcion"],
  monitor: ["super_admin"]
};

/**
 * Check if user has access to a route.
 * 
 * @param route - Route to check
 * @param permissions - Optional custom permissions (defaults to DEFAULT_ROUTE_PERMISSIONS)
 * @returns True if user has access
 */
export function hasAccess(
  route: string,
  permissions: RoutePermissions = DEFAULT_ROUTE_PERMISSIONS
): boolean {
  const currentUser = get(user);
  if (!currentUser) return false;
  
  // Check exact match first
  if (permissions[route]) {
    return permissions[route].includes(currentUser.role);
  }
  
  // Check route prefixes (e.g., /recepcion/ventas matches /recepcion)
  for (const [allowedRoute, allowedRoles] of Object.entries(permissions)) {
    if (route.startsWith(allowedRoute) && allowedRoles.includes(currentUser.role)) {
      return true;
    }
  }
  
  return false;
}

/**
 * Check if user can edit a module.
 * 
 * @param module - Module to check
 * @param permissions - Optional custom permissions (defaults to DEFAULT_EDIT_PERMISSIONS)
 * @returns True if user can edit
 */
export function canEdit(
  module: string,
  permissions: EditPermissions = DEFAULT_EDIT_PERMISSIONS
): boolean {
  const currentUser = get(user);
  if (!currentUser) return false;
  
  const allowedRoles = permissions[module] || [];
  return allowedRoles.includes(currentUser.role);
}

/**
 * Check if user has access to a route (secure version - throws error if no user).
 * 
 * @param route - Route to check
 * @param permissions - Optional custom permissions
 * @returns True if user has access
 * @throws Error if no user is logged in
 */
export function hasAccessSecure(
  route: string,
  permissions: RoutePermissions = DEFAULT_ROUTE_PERMISSIONS
): boolean {
  const currentUser = get(user);
  if (!currentUser) {
    throw new Error("User not authenticated");
  }
  return hasAccess(route, permissions);
}

/**
 * Check if user can edit a module (secure version - throws error if no user).
 * 
 * @param module - Module to check
 * @param permissions - Optional custom permissions
 * @returns True if user can edit
 * @throws Error if no user is logged in
 */
export function canEditSecure(
  module: string,
  permissions: EditPermissions = DEFAULT_EDIT_PERMISSIONS
): boolean {
  const currentUser = get(user);
  if (!currentUser) {
    throw new Error("User not authenticated");
  }
  return canEdit(module, permissions);
}

// Token utilities
/**
 * Get username from JWT token.
 * 
 * @returns Username or null
 */
export function getUsernameFromToken(): string | null {
  const currentToken = get(token);
  if (!currentToken) return null;
  
  try {
    const parts = currentToken.split(".");
    if (parts.length !== 3) return null;
    
    const encodedPayload = parts[1];
    if (!encodedPayload) return null;
    
    const payload = JSON.parse(atob(encodedPayload));
    return payload.sub || null;
  } catch {
    return null;
  }
}

/**
 * Check if token and user store are consistent.
 * 
 * @returns True if token username matches user username
 */
export function isTokenStoreConsistent(): boolean {
  const tokenUsername = getUsernameFromToken();
  const currentUser = get(user);
  
  if (!tokenUsername || !currentUser) return false;
  return tokenUsername === currentUser.username;
}

















