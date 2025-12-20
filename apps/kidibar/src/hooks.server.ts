/**
 * Server-side hooks for kidibar app.
 */
import { redirect } from "@sveltejs/kit";
import type { Handle } from "@sveltejs/kit";

export const handle: Handle = async ({ event, resolve }) => {
  const token = event.cookies.get("auth_token");

  // Allow access to login page without auth
  if (event.url.pathname === "/login") {
    return resolve(event);
  }

  // Require authentication for all other routes
  if (!token) {
    throw redirect(302, "/login");
  }

  return resolve(event);
};
































