/**
 * useBreakpoint - Reactive breakpoint detection utility.
 * 
 * Provides reactive breakpoint detection using window.matchMedia.
 * Compatible with SSR (SvelteKit) - returns default value on server.
 * 
 * Usage:
 *   const isMobile = useBreakpoint('(max-width: 640px)');
 *   const isTablet = useBreakpoint('(min-width: 641px) and (max-width: 1024px)');
 *   const isDesktop = useBreakpoint('(min-width: 1025px)');
 */
import { readable, type Readable } from 'svelte/store';
import { browser } from '$app/environment';

/**
 * Create a readable store that tracks a media query match.
 * 
 * @param query - Media query string (e.g., '(max-width: 640px)')
 * @param defaultValue - Default value for SSR (default: false)
 * @returns Readable store that updates when media query matches/unmatches
 */
export function useBreakpoint(
  query: string,
  defaultValue: boolean = false
): Readable<boolean> {
  if (!browser) {
    // SSR: return store with default value
    return readable(defaultValue);
  }

  // Browser: create reactive store with matchMedia
  return readable(defaultValue, (set) => {
    const mediaQuery = window.matchMedia(query);
    
    // Set initial value
    set(mediaQuery.matches);
    
    // Create handler function
    const handler = (event: MediaQueryListEvent | MediaQueryList) => {
      set(event.matches);
    };
    
    // Add listener (using modern API if available, fallback to addListener)
    if (mediaQuery.addEventListener) {
      mediaQuery.addEventListener('change', handler);
    } else {
      // Fallback for older browsers
      mediaQuery.addListener(handler);
    }
    
    // Cleanup function
    return () => {
      if (mediaQuery.removeEventListener) {
        mediaQuery.removeEventListener('change', handler);
      } else {
        // Fallback for older browsers
        mediaQuery.removeListener(handler);
      }
    };
  });
}

/**
 * Predefined breakpoint stores for common screen sizes.
 * Follows the project's breakpoint system.
 * 
 * Export individual stores for direct import (recommended pattern).
 * Also export as object for convenience when multiple stores are needed.
 */

/** Mobile: max-width 640px */
export const isMobile = useBreakpoint('(max-width: 640px)');

/** Tablet: 641px - 1024px */
export const isTablet = useBreakpoint('(min-width: 641px) and (max-width: 1024px)');

/** Desktop: min-width 1025px */
export const isDesktop = useBreakpoint('(min-width: 1025px)');

/** Mobile or Tablet: max-width 1024px */
export const isMobileOrTablet = useBreakpoint('(max-width: 1024px)');

/**
 * Breakpoints object for convenience when multiple stores are needed.
 * Note: Use individual exports (isMobile, isTablet, etc.) for direct $ syntax.
 */
export const breakpoints = {
  isMobile,
  isTablet,
  isDesktop,
  isMobileOrTablet,
};

