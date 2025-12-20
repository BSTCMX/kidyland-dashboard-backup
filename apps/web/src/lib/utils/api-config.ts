/**
 * API configuration utilities.
 * 
 * Clean Architecture: Dynamic configuration, no hardcoding.
 * Provides functions to get API URL dynamically based on environment.
 * 
 * Priority:
 * 1. VITE_API_URL env variable (explicit override)
 * 2. window.location.origin (in browser - always use same origin in production)
 * 3. Empty string (relative path for SSR/production builds without window)
 * 4. http://localhost:8000 (development fallback only when not in browser)
 * 
 * Important: In production browser, always uses same origin (no CORS needed).
 * Never uses localhost in production browser context.
 */

/**
 * Get API base URL.
 * 
 * @returns API base URL string
 */
export function getApiUrl(): string {
  const apiUrl = import.meta.env.VITE_API_URL;

  // 1. Explicit override via env variable (highest priority)
  if (apiUrl) {
    return apiUrl;
  }

  // 2. In browser context: always use same origin (production or development)
  // This ensures same-origin requests in production, avoiding CORS issues
  if (typeof window !== 'undefined' && window.location) {
    return window.location.origin;
  }

  // 3. SSR or production build without window: use relative paths
  if (import.meta.env.MODE === 'production' || import.meta.env.PROD) {
    return "";
  }

  // 4. Development fallback (only when not in browser, e.g., Node.js scripts)
  return "http://localhost:8000";
}

/**
 * Get API URL with path appended.
 * 
 * @param path - API endpoint path (e.g., "/sales/123")
 * @returns Full API URL with path
 */
export function getApiUrlWithPath(path: string): string {
  const baseUrl = getApiUrl();
  // Ensure path starts with /
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${baseUrl}${normalizedPath}`;
}
