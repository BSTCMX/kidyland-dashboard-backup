/**
 * SvelteKit type stubs for shared package.
 * 
 * Clean Architecture: Type declarations for SvelteKit modules used conditionally.
 * 
 * These types allow packages/utils to import SvelteKit modules without errors
 * during type checking, while the actual imports are handled dynamically at runtime
 * (see auth.ts and api.ts for conditional imports).
 * 
 * Note: These are type-only declarations. The actual modules are provided by
 * SvelteKit at runtime in apps that use this package.
 */

declare module "$app/navigation" {
  /**
   * Navigate to a route programmatically.
   * 
   * @param url - URL to navigate to
   * @param options - Navigation options
   */
  export function goto(
    url: string,
    options?: {
      replaceState?: boolean;
      noScroll?: boolean;
      keepFocus?: boolean;
      invalidateAll?: boolean;
      state?: any;
    }
  ): Promise<void>;

  /**
   * Invalidate all data.
   */
  export function invalidate(): Promise<void>;

  /**
   * Preload data for a route.
   */
  export function preloadData(href: string): Promise<void>;

  /**
   * Preload code for a route.
   */
  export function preloadCode(href: string): Promise<void>;
}

declare module "$app/environment" {
  /**
   * Whether the code is running in the browser.
   */
  export const browser: boolean;

  /**
   * Whether the code is running in development mode.
   */
  export const dev: boolean;

  /**
   * Whether the code is being built.
   */
  export const building: boolean;

  /**
   * SvelteKit version.
   */
  export const version: string;
}

