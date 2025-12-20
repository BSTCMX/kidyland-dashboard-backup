/**
 * Request timeout constants.
 * 
 * Centralized configuration for request timeouts across the application.
 * Allows easy adjustment of timeout values without hardcoding.
 */
export const REQUEST_TIMEOUTS = {
  /** Default timeout for standard API requests (30s) */
  DEFAULT: 30000,
  
  /** Timeout for complex/stats requests that may take longer (30s) */
  STATS: 30000,
  
  /** Timeout for simple/quick requests (10s) */
  SIMPLE: 10000,
  
  /** Timeout for WebSocket connection attempts (30s) */
  WEBSOCKET_CONNECTION: 30000,
  
  /** Timeout for WebSocket heartbeat pong response (15s) */
  WEBSOCKET_HEARTBEAT: 15000,
} as const;

/**
 * Get timeout value for a specific request type.
 * 
 * @param type - Request type
 * @returns Timeout in milliseconds
 */
export function getRequestTimeout(type: keyof typeof REQUEST_TIMEOUTS = 'DEFAULT'): number {
  return REQUEST_TIMEOUTS[type];
}








