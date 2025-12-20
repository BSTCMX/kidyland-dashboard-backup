/**
 * Promise guard utility for preventing duplicate concurrent requests.
 * 
 * Ensures only one request is in-flight at a time, reusing the same promise
 * for concurrent calls. Handles rejected promises correctly to prevent
 * reusing already-rejected promises.
 * 
 * Usage:
 * ```typescript
 * const guard = createPromiseGuard<string>();
 * 
 * async function fetchData() {
 *   return guard.execute(async () => {
 *     const response = await fetch('/api/data');
 *     return response.json();
 *   });
 * }
 * ```
 */
export interface PromiseGuard<T> {
  /**
   * Execute a function, reusing the promise if already in progress.
   * 
   * @param fn - Function to execute
   * @returns Promise that resolves/rejects based on function result
   */
  execute(fn: () => Promise<T>): Promise<T>;
  
  /**
   * Check if a request is currently in progress.
   */
  isInProgress(): boolean;
  
  /**
   * Reset the guard (useful for error recovery).
   */
  reset(): void;
}

/**
 * Create a promise guard instance.
 * 
 * @returns PromiseGuard instance
 */
export function createPromiseGuard<T>(): PromiseGuard<T> {
  let currentPromise: Promise<T> | null = null;
  let inProgress = false;

  return {
    execute(fn: () => Promise<T>): Promise<T> {
      // If already in progress, return existing promise
      if (inProgress && currentPromise) {
        // Validate that promise is still pending (not rejected/resolved)
        // We can't check promise state directly, but we can check if it's the same reference
        // The promise will be cleared in finally block after completion
        return currentPromise;
      }

      inProgress = true;
      
      const promise = (async () => {
        try {
          const result = await fn();
          return result;
        } catch (error) {
          // Cleanup immediately on rejection to prevent reusing rejected promise
          inProgress = false;
          currentPromise = null;
          throw error;
        } finally {
          // Cleanup on resolution (or if somehow we get here)
          inProgress = false;
          currentPromise = null;
        }
      })();

      currentPromise = promise;
      return promise;
    },

    isInProgress(): boolean {
      return inProgress;
    },

    reset(): void {
      inProgress = false;
      currentPromise = null;
    },
  };
}








