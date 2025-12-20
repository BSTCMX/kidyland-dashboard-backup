/**
 * WebSocket utilities for the web app.
 * 
 * Note: Main WebSocket functionality is in @kidyland/utils/websocket.
 * This file provides app-specific WebSocket utilities if needed.
 */

// Re-export from @kidyland/utils for convenience
export {
  createTimerWebSocket,
  type TimerWebSocketOptions,
  type TimerWebSocketConnection,
} from "@kidyland/utils";
