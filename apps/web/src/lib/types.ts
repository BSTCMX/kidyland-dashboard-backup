/**
 * Type definitions for the web app.
 * 
 * Re-exports types from shared packages and defines app-specific types.
 */

// Re-export all types from shared package for convenience
export type {
  User,
  Sucursal,
  Product,
  Service,
  Package,
  PackageItem,
  Sale,
  Timer,
  ServiceAlert,
} from "@kidyland/shared/types";

// App-specific types
export type UserRole = "super_admin" | "admin_viewer" | "recepcion" | "kidibar" | "monitor";

/**
 * Route mappings for each user role.
 * Used for automatic redirects based on user role.
 */
export const ROLE_ROUTES: Record<UserRole, string> = {
  super_admin: "/admin",
  admin_viewer: "/admin-viewer",
  recepcion: "/recepcion",
  kidibar: "/kidibar",
  monitor: "/monitor",
};
