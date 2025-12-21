/**
 * API client for authenticated HTTP requests.
 * 
 * Provides functions for making API requests with automatic token injection
 * and error handling.
 */
import { getToken, logout } from "./auth";
import { fetchWithTimeout, FetchWithTimeoutOptions } from "./utils/fetch-with-timeout";

/**
 * Get API URL from environment or use current origin in browser.
 * 
 * Clean Architecture: Dynamic configuration, no hardcoding.
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
function getApiUrl(): string {
  const env = typeof import.meta !== 'undefined' && (import.meta as any).env;
  
  // 1. Explicit override via env variable (highest priority)
  if (env?.VITE_API_URL) {
    return env.VITE_API_URL;
  }

  // 2. In browser context
  if (typeof window !== 'undefined' && window.location) {
    // In development mode: use backend port 8000
    if (env?.MODE === 'development' || env?.DEV) {
      return "http://localhost:8000";
    }
    // In production: use same origin (no CORS needed)
    return window.location.origin;
  }

  // 3. SSR or production build without window: use relative paths
  if (env?.MODE === 'production' || env?.PROD) {
    return "";
  }

  // 4. Development fallback (only when not in browser, e.g., Node.js scripts)
  return "http://localhost:8000";
}

/**
 * Make an authenticated API request.
 * 
 * @param endpoint - API endpoint (e.g., "/users")
 * @param options - Fetch options including timeout
 * @returns Promise that resolves to response data
 * @throws Error if request fails or returns non-ok status
 */
export async function apiRequest(
  endpoint: string,
  options: FetchWithTimeoutOptions = {}
): Promise<any> {
  const token = getToken();
  const { timeout, ...fetchOptions } = options;
  
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(fetchOptions.headers as Record<string, string> || {}),
  };
  
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  
  const url = `${getApiUrl()}${endpoint}`;
  
  const res = timeout !== undefined
    ? await fetchWithTimeout(url, {
        ...fetchOptions,
        headers,
        timeout,
      })
    : await fetch(url, {
        ...fetchOptions,
        headers,
      });
  
  // Handle 401 (unauthorized) - token expired or invalid
  if (res.status === 401) {
    logout();
    if (typeof window !== "undefined") {
      // Try to redirect to login if in browser
      try {
        const { goto } = await import("$app/navigation");
        goto("/login");
      } catch {
        // Navigation not available, just logout
      }
    }
    throw new Error("Authentication required");
  }
  
  if (!res.ok) {
    let errorData;
    try {
      errorData = await res.json();
    } catch {
      errorData = { detail: `Request failed: ${res.statusText}` };
    }
    const error = new Error(errorData.detail || `Request failed: ${res.statusText}`);
    (error as any).response = { data: errorData, status: res.status };
    throw error;
  }
  
  const contentType = res.headers.get("content-type");
  if (contentType && contentType.includes("application/json")) {
    return await res.json();
  }
  
  return {};
}

/**
 * Make a GET request.
 * 
 * @param endpoint - API endpoint
 * @param options - Optional fetch options
 * @returns Promise that resolves to response data
 */
export async function get(endpoint: string, options: FetchWithTimeoutOptions = {}): Promise<any> {
  return apiRequest(endpoint, { ...options, method: "GET" });
}

/**
 * Make a POST request.
 * 
 * @param endpoint - API endpoint
 * @param data - Request body data
 * @param options - Optional fetch options
 * @returns Promise that resolves to response data
 */
export async function post(
  endpoint: string,
  data?: any,
  options: FetchWithTimeoutOptions = {}
): Promise<any> {
  return apiRequest(endpoint, {
    ...options,
    method: "POST",
    body: data ? JSON.stringify(data) : undefined,
  });
}

/**
 * Make a PUT request.
 * 
 * @param endpoint - API endpoint
 * @param data - Request body data
 * @param options - Optional fetch options
 * @returns Promise that resolves to response data
 */
export async function put(
  endpoint: string,
  data?: any,
  options: FetchWithTimeoutOptions = {}
): Promise<any> {
  return apiRequest(endpoint, {
    ...options,
    method: "PUT",
    body: data ? JSON.stringify(data) : undefined,
  });
}

/**
 * Make a DELETE request.
 * 
 * @param endpoint - API endpoint
 * @param options - Optional fetch options
 * @returns Promise that resolves to response data
 */
export async function del(endpoint: string, options: FetchWithTimeoutOptions = {}): Promise<any> {
  return apiRequest(endpoint, { ...options, method: "DELETE" });
}
