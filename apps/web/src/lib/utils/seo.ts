/**
 * SEO utility functions for dynamic page titles and meta descriptions.
 * 
 * Clean Architecture: Reusable utility for SEO management.
 * Provides helper functions to generate SEO-friendly titles and descriptions
 * that can be used with svelte:head in layouts and pages.
 * 
 * Usage:
 * ```svelte
 * <svelte:head>
 *   {@html getPageTitle("Dashboard Admin")}
 *   {@html getPageDescription("Panel de administración del sistema Kidyland")}
 * </svelte:head>
 * ```
 */

/**
 * Generate page title with site name suffix.
 * 
 * Clean Architecture: Reusable function, no hardcoding.
 * 
 * @param pageTitle - Page-specific title (e.g., "Dashboard Admin")
 * @param siteName - Site name (default: "Kidyland")
 * @returns HTML string with <title> tag
 * 
 * @example
 * getPageTitle("Dashboard Admin") 
 * // Returns: '<title>Dashboard Admin - Kidyland</title>'
 */
export function getPageTitle(pageTitle: string, siteName: string = "Kidyland"): string {
  const fullTitle = `${pageTitle} - ${siteName}`;
  return `<title>${escapeHtml(fullTitle)}</title>`;
}

/**
 * Generate meta description tag.
 * 
 * Clean Architecture: Reusable function, no hardcoding.
 * 
 * @param description - Page description (150-160 characters recommended)
 * @returns HTML string with meta description tag
 * 
 * @example
 * getPageDescription("Panel de administración del sistema Kidyland")
 * // Returns: '<meta name="description" content="Panel de administración del sistema Kidyland">'
 */
export function getPageDescription(description: string): string {
  return `<meta name="description" content="${escapeHtml(description)}">`;
}

/**
 * Generate complete SEO tags (title + description).
 * 
 * Clean Architecture: Convenience function combining title and description.
 * 
 * @param pageTitle - Page-specific title
 * @param description - Page description
 * @param siteName - Site name (default: "Kidyland")
 * @returns HTML string with both title and meta description tags
 */
export function getPageSEOTags(
  pageTitle: string,
  description: string,
  siteName: string = "Kidyland"
): string {
  return `${getPageTitle(pageTitle, siteName)}\n${getPageDescription(description)}`;
}

/**
 * Escape HTML special characters to prevent XSS.
 * 
 * Clean Architecture: Security utility, reusable.
 * Works in both SSR and client contexts.
 * 
 * @param text - Text to escape
 * @returns Escaped text safe for HTML
 */
function escapeHtml(text: string): string {
  // Use string replacement for SSR compatibility (no DOM required)
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

