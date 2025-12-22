/**
 * Debounce utility for reactive statements and function calls.
 * 
 * Clean Architecture: Reusable debouncing utility for preventing excessive executions.
 * Useful for reactive statements in Svelte that trigger API calls or expensive operations.
 * 
 * Usage in reactive statements:
 * ```typescript
 * import { createDebouncedReactive } from "$lib/utils/debounce";
 * 
 * const debouncedLoad = createDebouncedReactive(loadTimeSeriesData, 500);
 * 
 * $: if (startDate && endDate) {
 *   debouncedLoad();
 * }
 * ```
 * 
 * Usage for regular functions:
 * ```typescript
 * import { debounce } from "$lib/utils/debounce";
 * 
 * const debouncedSearch = debounce((query: string) => {
 *   performSearch(query);
 * }, 300);
 * 
 * input.addEventListener('input', (e) => {
 *   debouncedSearch(e.target.value);
 * });
 * ```

/**
 * Creates a debounced function that delays execution until after wait time has passed.
 * 
 * @param fn - Function to debounce
 * @param delay - Delay in milliseconds (default: 300)
 * @returns Debounced function
 */
export function debounce<T extends (...args: any[]) => any>(
  fn: T,
  delay: number = 300
): (...args: Parameters<T>) => void {
  let timeoutId: ReturnType<typeof setTimeout> | null = null;

  return function debounced(...args: Parameters<T>) {
    if (timeoutId) {
      clearTimeout(timeoutId);
    }

    timeoutId = setTimeout(() => {
      fn(...args);
      timeoutId = null;
    }, delay);
  };
}

/**
 * Creates a debounced reactive handler for use in Svelte reactive statements.
 * 
 * Clean Architecture: Reusable pattern for debouncing reactive statements that trigger
 * expensive operations (API calls, calculations, etc.).
 * 
 * This function returns a debounced version of the provided function that can be safely
 * called multiple times in reactive statements without causing excessive executions.
 * 
 * @param fn - Function to debounce (can be async)
 * @param delay - Delay in milliseconds (default: 500)
 * @returns Debounced function that can be called in reactive statements
 * 
 * @example
 * ```typescript
 * const debouncedLoad = createDebouncedReactive(loadTimeSeriesData, 500);
 * 
 * $: if (startDate && endDate) {
 *   debouncedLoad();
 * }
 * ```
 */
export function createDebouncedReactive<T extends (...args: any[]) => any>(
  fn: T,
  delay: number = 500
): (...args: Parameters<T>) => void {
  let timeoutId: ReturnType<typeof setTimeout> | null = null;

  return function debounced(...args: Parameters<T>) {
    if (timeoutId) {
      clearTimeout(timeoutId);
    }

    timeoutId = setTimeout(() => {
      fn(...args);
      timeoutId = null;
    }, delay);
  };
}

/**
 * Creates a debounced reactive handler with cleanup support.
 * 
 * Useful when you need to clean up timeouts (e.g., in onDestroy).
 * 
 * @param fn - Function to debounce
 * @param delay - Delay in milliseconds (default: 500)
 * @returns Object with debounced function and cleanup method
 * 
 * @example
 * ```typescript
 * import { onDestroy } from "svelte";
 * 
 * const { debounced, cleanup } = createDebouncedReactiveWithCleanup(loadData, 500);
 * 
 * $: if (condition) {
 *   debounced();
 * }
 * 
 * onDestroy(() => {
 *   cleanup();
 * });
 * ```
 */
export function createDebouncedReactiveWithCleanup<T extends (...args: any[]) => any>(
  fn: T,
  delay: number = 500
): {
  debounced: (...args: Parameters<T>) => void;
  cleanup: () => void;
} {
  let timeoutId: ReturnType<typeof setTimeout> | null = null;

  const debounced = function (...args: Parameters<T>) {
    if (timeoutId) {
      clearTimeout(timeoutId);
    }

    timeoutId = setTimeout(() => {
      fn(...args);
      timeoutId = null;
    }, delay);
  };

  const cleanup = () => {
    if (timeoutId) {
      clearTimeout(timeoutId);
      timeoutId = null;
    }
  };

  return { debounced, cleanup };
}

