/**
 * WebSocket client for real-time timer updates.
 * 
 * Provides WebSocket connection with automatic reconnection and error handling.
 */
import { getToken } from "./auth";

/**
 * Get WebSocket URL.
 * 
 * Uses same logic as API URL resolution:
 * 1. VITE_API_URL env variable
 * 2. window.location.origin (in browser, for production)
 * 3. ws://localhost:8000 (development fallback)
 */
function getWebSocketUrl(): string {
  const protocol = typeof window !== 'undefined' && window.location.protocol === "https:" ? "wss:" : "ws:";
  const env = typeof import.meta !== 'undefined' && (import.meta as any).env;
  const apiUrl = env?.VITE_API_URL || (typeof window !== 'undefined' ? window.location.origin : "http://localhost:8000");
  const host = apiUrl.replace(/^https?:\/\//, "").replace(/^wss?:\/\//, "");
  
  return `${protocol}//${host}`;
}

/**
 * WebSocket connection options.
 */
export interface TimerWebSocketOptions {
  onOpen?: () => void;
  onMessage?: (data: any) => void;
  onError?: (error: Event) => void;
  onClose?: () => void;
}

/**
 * Timer WebSocket connection interface.
 */
export interface TimerWebSocketConnection {
  connect: () => void;
  disconnect: () => void;
}

/**
 * Create a WebSocket connection for timer updates.
 * 
 * @param sucursalId - Sucursal ID to subscribe to
 * @param options - Connection callbacks
 * @returns WebSocket connection object with connect/disconnect methods
 */
export function createTimerWebSocket(
  sucursalId: string,
  options: TimerWebSocketOptions = {}
): TimerWebSocketConnection {
  const { onOpen, onMessage, onError, onClose } = options;
  let ws: WebSocket | null = null;
  let reconnectAttempts = 0;
  const maxReconnectAttempts = 5;
  const baseDelay = 1000; // 1 second
  let reconnectTimeoutId: ReturnType<typeof setTimeout> | null = null;
  let isIntentionallyDisconnected = false;

  function connect(): void {
    if (ws?.readyState === WebSocket.OPEN || ws?.readyState === WebSocket.CONNECTING) {
      return; // Already connected or connecting
    }

    isIntentionallyDisconnected = false;

    const token = getToken();
    if (!token) {
      console.error("[WebSocket] Cannot connect: no token available");
      if (onError) {
        onError(new Event("no_token"));
      }
      return;
    }

    const baseUrl = getWebSocketUrl();
    const url = `${baseUrl}/ws/timers?token=${encodeURIComponent(token)}&sucursal_id=${encodeURIComponent(sucursalId)}`;

    try {
      ws = new WebSocket(url);

      ws.onopen = () => {
        reconnectAttempts = 0;
        if (onOpen) {
          onOpen();
        }
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (onMessage) {
            onMessage(data);
          }
        } catch (error) {
          console.error("[WebSocket] Error parsing message:", error);
        }
      };

      ws.onerror = (error) => {
        console.error("[WebSocket] Connection error:", error);
        if (onError) {
          onError(error);
        }
      };

      ws.onclose = () => {
        if (onClose) {
          onClose();
        }

        // Attempt to reconnect if not intentionally disconnected
        if (!isIntentionallyDisconnected && reconnectAttempts < maxReconnectAttempts) {
          const delay = baseDelay * Math.pow(2, reconnectAttempts); // Exponential backoff
          reconnectAttempts++;
          
          console.log(`[WebSocket] Reconnecting in ${delay}ms (attempt ${reconnectAttempts}/${maxReconnectAttempts})...`);
          
          reconnectTimeoutId = setTimeout(() => {
            connect();
          }, delay);
        } else if (reconnectAttempts >= maxReconnectAttempts) {
          console.error("[WebSocket] Max reconnection attempts reached");
        }
      };
    } catch (error) {
      console.error("[WebSocket] Error creating connection:", error);
      if (onError) {
        onError(error as Event);
      }
    }
  }

  function disconnect(): void {
    isIntentionallyDisconnected = true;
    
    if (reconnectTimeoutId) {
      clearTimeout(reconnectTimeoutId);
      reconnectTimeoutId = null;
    }

    if (ws) {
      try {
        ws.close();
      } catch (error) {
        console.debug("[WebSocket] Error during disconnect:", error);
      }
      ws = null;
    }
  }

  return {
    connect,
    disconnect,
  };
}
