/**
 * Server-side hooks for role-based routing and authentication.
 */
import { redirect } from "@sveltejs/kit";
import type { Handle } from "@sveltejs/kit";

export const handle: Handle = async ({ event, resolve }) => {
  const token = event.cookies.get("auth_token");
  const userRole = event.cookies.get("user_role");

  // Allow access to login page without auth
  if (event.url.pathname === "/login") {
    return resolve(event);
  }

  // Require authentication for all other routes
  if (!token) {
    throw redirect(302, "/login");
  }

  // Role-based routing (if needed in the future)
  // For now, reception app is accessible to all authenticated users
  // You can add specific role checks here if needed

  return resolve(event);
};
































