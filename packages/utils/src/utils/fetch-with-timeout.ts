/**
 * Fetch with timeout utility.
 * 
 * Wraps fetch requests with AbortController-based timeout handling.
 * Prevents race conditions by checking if response already received before aborting.
 * 
 * Usage:
 * ```typescript
 * const data = await fetchWithTimeout('/api/data', { timeout: 30000 });
 * ```
 */
import { getRequestTimeout } from '../constants/request-timeouts';

export interface FetchWithTimeoutOptions extends RequestInit {
  /** Timeout in milliseconds (defaults to REQUEST_TIMEOUTS.DEFAULT) */
  timeout?: number;
  /** Whether to check for response before aborting (prevents race conditions) */
  checkResponseBeforeAbort?: boolean;
}

/**
 * Fetch with timeout support.
 * 
 * @param url - Request URL
 * @param options - Fetch options including timeout
 * @returns Promise that resolves to Response
 * @throws Error with isTimeout flag if request times out
 */
export async function fetchWithTimeout(
  url: string | URL,
  options: FetchWithTimeoutOptions = {}
): Promise<Response> {
  const {
    timeout = getRequestTimeout('DEFAULT'),
    checkResponseBeforeAbort = true,
    signal: existingSignal,
    ...fetchOptions
  } = options;

  const controller = new AbortController();
  let responseReceived = false;
  let timeoutId: ReturnType<typeof setTimeout> | null = null;

  // Combine signals if existing signal provided
  if (existingSignal) {
    existingSignal.addEventListener('abort', () => {
      controller.abort();
    });
  }

  // Set timeout
  timeoutId = setTimeout(() => {
    // Only abort if response hasn't been received (prevents race condition)
    if (!responseReceived) {
      controller.abort();
    }
  }, timeout);

  try {
    const response = await fetch(url, {
      ...fetchOptions,
      signal: controller.signal,
    });

    // Mark response as received before clearing timeout
    responseReceived = true;
    
    if (timeoutId) {
      clearTimeout(timeoutId);
      timeoutId = null;
    }

    return response;
  } catch (error: any) {
    // Clear timeout on error
    if (timeoutId) {
      clearTimeout(timeoutId);
      timeoutId = null;
    }

    // Check if error is due to timeout/abort
    if (error.name === 'AbortError' || error.name === 'TimeoutError') {
      const timeoutError = new Error(
        responseReceived
          ? 'Request timeout (response received but incomplete)'
          : 'Request timeout - please check your connection and try again'
      );
      (timeoutError as any).isTimeout = true;
      (timeoutError as any).name = 'TimeoutError';
      throw timeoutError;
    }

    // Re-throw other errors
    throw error;
  }
}








