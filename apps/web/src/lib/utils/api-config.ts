/**
 * API configuration utilities.
 * 
 * Clean Architecture: Dynamic configuration, no hardcoding.
 * Provides functions to get API URL dynamically based on environment.
 * 
 * Priority:
 * 1. VITE_API_URL env variable (explicit override)
 * 2. Runtime detection: window.location.hostname === 'localhost' → development
 * 3. window.location.origin (in browser - always use same origin in production)
 * 4. Empty string (relative path for SSR/production builds without window)
 * 5. http://localhost:8000 (development fallback only when not in browser)
 * 
 * Important: Uses runtime detection (hostname) instead of build-time env vars
 * to ensure correct behavior in production builds. In production browser,
 * always uses same origin (no CORS needed). Never uses localhost in production browser context.
 */

/**
 * Get API base URL.
 * 
 * Uses runtime detection for environment to work correctly in production builds.
 * 
 * @returns API base URL string
 */
export function getApiUrl(): string {
  const apiUrl = import.meta.env.VITE_API_URL;

  // 1. Explicit override via env variable (highest priority)
  if (apiUrl) {
    return apiUrl;
  }

  // 2. Runtime detection in browser context
  if (typeof window !== 'undefined' && window.location) {
    // Runtime detection: check hostname instead of build-time env vars
    // This ensures correct behavior in production builds
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
      // In development (localhost): use backend port 8000
      return "http://localhost:8000";
    }
    // In production browser: use same origin (no CORS needed)
    return window.location.origin;
  }

  // 3. SSR or production build without window: use relative paths
  // Fallback to build-time detection for SSR context
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
