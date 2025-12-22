/**
 * Navigation utilities for preserving query parameters across route navigation.
 * 
 * This module provides helpers to maintain URL state (like sucursal_id filter)
 * when navigating between routes, ensuring consistent filtering for superadmin users.
 */

import { goto } from "$app/navigation";
import type { Page } from "@sveltejs/kit";

/**
 * Preserves sucursal_id query parameter from current URL when constructing new URLs.
 * 
 * This is primarily used for superadmin navigation to maintain the selected
 * sucursal filter across different pages (ventas, arqueos, etc.).
 * 
 * For regular users, this function is transparent - if there's no sucursal_id
 * in the current URL, it returns the baseUrl unchanged, allowing the normal
 * flow (using $user?.sucursal_id) to work as expected.
 * 
 * Handles edge cases:
 * - URLs that already have query params
 * - Prevents duplicate sucursal_id params
 * - Preserves existing query params in baseUrl
 * 
 * @param baseUrl - The target URL path (e.g., "/recepcion/ventas" or "/recepcion/ventas?page=1")
 * @param currentUrl - The current page URL object from $page.url
 * @returns The baseUrl with sucursal_id query param appended if it exists in currentUrl
 * 
 * @example
 * ```typescript
 * // Superadmin on /recepcion?sucursal_id=123
 * preserveQueryParams("/recepcion/ventas", $page.url)
 * // Returns: "/recepcion/ventas?sucursal_id=123"
 * 
 * // With existing query params
 * preserveQueryParams("/recepcion/ventas?page=1", $page.url)
 * // Returns: "/recepcion/ventas?page=1&sucursal_id=123"
 * 
 * // Regular user on /recepcion (no query params)
 * preserveQueryParams("/recepcion/ventas", $page.url)
 * // Returns: "/recepcion/ventas" (unchanged)
 * ```
 */
export function preserveQueryParams(baseUrl: string, currentUrl: Page['url']): string {
  const sucursalId = currentUrl.searchParams.get('sucursal_id');
  
  if (!sucursalId) {
    return baseUrl;
  }
  
  // Parse baseUrl to check for existing query params
  try {
    const url = new URL(baseUrl, 'http://localhost'); // Use dummy base for relative URLs
    const hasExistingParams = url.search.length > 0;
    
    // Check if sucursal_id already exists in baseUrl
    if (url.searchParams.has('sucursal_id')) {
      // Update existing sucursal_id param
      url.searchParams.set('sucursal_id', sucursalId);
      // Return pathname + search (without protocol/host)
      return url.pathname + url.search;
    }
    
    // Add sucursal_id to existing params or create new query string
    url.searchParams.set('sucursal_id', sucursalId);
    return url.pathname + url.search;
  } catch {
    // Fallback for malformed URLs: simple string concatenation
    // Check if baseUrl already has query params
    const separator = baseUrl.includes('?') ? '&' : '?';
    // Check if sucursal_id already exists (simple check)
    if (baseUrl.includes('sucursal_id=')) {
      // Replace existing sucursal_id
      return baseUrl.replace(/sucursal_id=[^&]*/, `sucursal_id=${sucursalId}`);
    }
    return `${baseUrl}${separator}sucursal_id=${sucursalId}`;
  }
}

/**
 * Navigates to a URL while preserving sucursal_id query parameter from current URL.
 * 
 * This is a convenience wrapper around SvelteKit's goto() that automatically
 * preserves the sucursal_id filter for superadmin users.
 * 
 * @param url - The target URL path (e.g., "/recepcion/ventas")
 * @param currentUrl - The current page URL object from $page.url
 * @param options - Optional goto options (keepFocus, invalidateAll, etc.)
 * 
 * @example
 * ```typescript
 * // In a Svelte component
 * import { page } from "$app/stores";
 * import { gotoWithQueryParams } from "$lib/utils/navigation";
 * 
 * function handleNavigate() {
 *   gotoWithQueryParams("/recepcion/ventas", $page.url);
 * }
 * ```
 */
/**
 * Navigates to a URL while preserving sucursal_id query parameter from current URL.
 * 
 * This is a convenience wrapper around SvelteKit's goto() that automatically
 * preserves the sucursal_id filter for superadmin users.
 * 
 * @param url - The target URL path (e.g., "/recepcion/ventas")
 * @param currentUrl - The current page URL object from $page.url
 * @param options - Optional goto options (keepFocus, invalidateAll, etc.)
 * 
 * @example
 * ```typescript
 * // In a Svelte component
 * import { page } from "$app/stores";
 * import { gotoWithQueryParams } from "$lib/utils/navigation";
 * 
 * function handleNavigate() {
 *   gotoWithQueryParams("/recepcion/ventas", $page.url);
 * }
 * ```
 */
export function gotoWithQueryParams(
  url: string,
  currentUrl: Page['url'],
  options?: { keepFocus?: boolean; invalidateAll?: boolean; noScroll?: boolean }
): void {
  const preservedUrl = preserveQueryParams(url, currentUrl);
  goto(preservedUrl, options);
}

/**
 * Gets a navigation link URL with preserved query parameters.
 * 
 * This helper is designed for use in sidebar navigation and other static links
 * that need to preserve query params (like sucursal_id) when navigating.
 * 
 * The returned URL is reactive to changes in currentUrl, making it suitable
 * for use in Svelte templates with reactive statements.
 * 
 * @param route - The target route path (e.g., "/recepcion/servicios")
 * @param currentUrl - The current page URL object from $page.url
 * @returns The route with sucursal_id query param appended if it exists in currentUrl
 * 
 * @example
 * ```svelte
 * <script>
 *   import { page } from "$app/stores";
 *   import { getNavLink } from "$lib/utils/navigation";
 * </script>
 * 
 * <a href={getNavLink("/recepcion/servicios", $page.url)}>Servicios</a>
 * ```
 */
export function getNavLink(route: string, currentUrl: Page['url']): string {
  return preserveQueryParams(route, currentUrl);
}

