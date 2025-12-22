/**
 * WebSocket client for real-time timer updates.
 * 
 * Provides WebSocket connection with automatic reconnection and error handling.
 */
import { getToken } from "./auth";

/**
 * Get WebSocket URL with robust validation.
 * 
 * Priority:
 * 1. VITE_WS_URL env variable (if explicitly set)
 * 2. Derive from VITE_API_URL (convert http:// to ws://, https:// to wss://)
 * 3. ws://localhost:8000 (development fallback)
 * 
 * This ensures WebSocket connects to the backend server (port 8000) rather than
 * the Vite dev server (port 5179) when VITE_API_URL is not set.
 * 
 * @returns WebSocket URL string
 * @throws Error if URL is invalid or points to Vite dev server
 */
function getWebSocketUrl(): string {
  const env = typeof import.meta !== 'undefined' && (import.meta as any).env;
  let wsUrl: string;
  
  // Priority 1: Use VITE_WS_URL if explicitly set
  if (env?.VITE_WS_URL) {
    wsUrl = env.VITE_WS_URL;
    console.debug("[WebSocket] Using VITE_WS_URL:", wsUrl);
  }
  // Priority 2: Derive from VITE_API_URL
  else if (env?.VITE_API_URL) {
    const apiUrl = env.VITE_API_URL;
    // Convert protocol: http:// -> ws://, https:// -> wss://
    wsUrl = apiUrl.replace(/^http:/, "ws:").replace(/^https:/, "wss:");
    console.debug("[WebSocket] Derived from VITE_API_URL:", apiUrl, "->", wsUrl);
  }
  // Priority 3: Development fallback - use backend port (8000), not Vite port (5179)
  else {
    // Determine protocol based on current page (if in browser) or default to ws
    const protocol = typeof window !== 'undefined' && window.location.protocol === "https:" ? "wss:" : "ws:";
    wsUrl = `${protocol}//localhost:8000`;
    console.debug("[WebSocket] Using development fallback:", wsUrl);
  }
  
  // Validate URL: ensure it doesn't point to Vite dev server
  if (typeof window !== 'undefined') {
    const vitePort = window.location.port || '5179';
    const viteHost = window.location.hostname;
    
    // Check if URL contains Vite's port or host
    if (wsUrl.includes(`:${vitePort}`) || wsUrl.includes(`${viteHost}:${vitePort}`)) {
      console.error("[WebSocket] ERROR: URL points to Vite dev server! Fixing to backend port 8000");
      // Fix: replace with backend port
      wsUrl = wsUrl.replace(/:5179/g, ':8000').replace(/:5173/g, ':8000');
      console.debug("[WebSocket] Fixed URL:", wsUrl);
    }
  }
  
  // Final validation: ensure URL is valid WebSocket URL
  if (!wsUrl.match(/^wss?:\/\/.+/)) {
    console.error("[WebSocket] ERROR: Invalid WebSocket URL:", wsUrl);
    // Fallback to safe default
    const protocol = typeof window !== 'undefined' && window.location.protocol === "https:" ? "wss:" : "ws:";
    wsUrl = `${protocol}//localhost:8000`;
    console.debug("[WebSocket] Using safe fallback:", wsUrl);
  }
  
  return wsUrl;
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
 * WebSocket connection states.
 */
enum WebSocketState {
  DISCONNECTED = "DISCONNECTED",
  CONNECTING = "CONNECTING",
  CONNECTED = "CONNECTED",
  CLOSING = "CLOSING",
  RECONNECTING = "RECONNECTING",
}

/**
 * Calculate exponential backoff delay with jitter.
 * 
 * Formula: baseDelay * 2^attempts + random(0, jitter)
 * 
 * @param attempts - Number of reconnection attempts
 * @param baseDelay - Base delay in milliseconds (default: 1000)
 * @param maxDelay - Maximum delay in milliseconds (default: 30000)
 * @param jitter - Random jitter in milliseconds (default: 500)
 * @returns Delay in milliseconds
 */
function calculateBackoffDelay(
  attempts: number,
  baseDelay: number = 1000,
  maxDelay: number = 30000,
  jitter: number = 500
): number {
  const exponentialDelay = baseDelay * Math.pow(2, attempts);
  const jitterAmount = Math.random() * jitter;
  const totalDelay = Math.min(exponentialDelay + jitterAmount, maxDelay);
  return Math.floor(totalDelay);
}

/**
 * Create a WebSocket connection for timer updates with robust error handling.
 * 
 * Features:
 * - State machine for connection lifecycle
 * - Exponential backoff with jitter for reconnection
 * - Debounce for rapid reconnection attempts
 * - Proper cleanup on disconnect
 * - Hot reload detection and cleanup
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
  let state: WebSocketState = WebSocketState.DISCONNECTED;
  let reconnectAttempts = 0;
  const maxReconnectAttempts = 10; // Increased for better resilience
  const baseDelay = 1000; // 1 second
  const maxDelay = 30000; // 30 seconds max
  const jitter = 500; // 500ms jitter
  const debounceDelay = 100; // 100ms debounce for rapid reconnection attempts
  let reconnectTimeoutId: ReturnType<typeof setTimeout> | null = null;
  let debounceTimeoutId: ReturnType<typeof setTimeout> | null = null;
  let isIntentionallyDisconnected = false;
  let lastReconnectTime = 0;

  /**
   * Clean up WebSocket connection and reset state.
   */
  function cleanup(): void {
    if (reconnectTimeoutId) {
      clearTimeout(reconnectTimeoutId);
      reconnectTimeoutId = null;
    }
    
    if (debounceTimeoutId) {
      clearTimeout(debounceTimeoutId);
      debounceTimeoutId = null;
    }

    if (ws) {
      // Check current state before closing
      const currentState = ws.readyState;
      
      // Only close if not already closed or closing
      if (currentState === WebSocket.OPEN || currentState === WebSocket.CONNECTING) {
        try {
          // Remove all event listeners to prevent memory leaks
          ws.onopen = null;
          ws.onmessage = null;
          ws.onerror = null;
          ws.onclose = null;
          ws.close();
        } catch (error) {
          console.debug("[WebSocket] Error during cleanup (ignored):", error);
        }
      }
      
      ws = null;
    }
    
    state = WebSocketState.DISCONNECTED;
  }

  /**
   * Check if WebSocket is in a valid state for connection.
   */
  function canConnect(): boolean {
    if (isIntentionallyDisconnected) {
      return false;
    }

    if (!ws) {
      return true;
    }

    const readyState = ws.readyState;
    
    // Can connect if disconnected or closed
    if (readyState === WebSocket.CLOSED) {
      return true;
    }
    
    // Cannot connect if already connected or connecting
    if (readyState === WebSocket.OPEN || readyState === WebSocket.CONNECTING) {
      return false;
    }
    
    // If closing, wait for it to close first
    if (readyState === WebSocket.CLOSING) {
      console.debug("[WebSocket] Connection is closing, waiting...");
      return false;
    }
    
    return true;
  }

  function connect(): void {
    // Debounce rapid reconnection attempts
    const now = Date.now();
    if (now - lastReconnectTime < debounceDelay) {
      console.debug("[WebSocket] Debouncing rapid reconnection attempt");
      if (debounceTimeoutId) {
        clearTimeout(debounceTimeoutId);
      }
      debounceTimeoutId = setTimeout(() => {
        connect();
      }, debounceDelay);
      return;
    }
    lastReconnectTime = now;

    // Check if we can connect
    if (!canConnect()) {
      console.debug("[WebSocket] Cannot connect: connection already exists or is in invalid state");
      return;
    }

    // Clean up any existing connection before creating new one
    if (ws && (ws.readyState === WebSocket.CLOSING || ws.readyState === WebSocket.CLOSED)) {
      cleanup();
    }

    isIntentionallyDisconnected = false;
    state = WebSocketState.CONNECTING;

    const token = getToken();
    if (!token) {
      console.error("[WebSocket] Cannot connect: no token available");
      state = WebSocketState.DISCONNECTED;
      if (onError) {
        onError(new Event("no_token"));
      }
      return;
    }

    const baseUrl = getWebSocketUrl();
    const url = `${baseUrl}/ws/timers?token=${encodeURIComponent(token)}&sucursal_id=${encodeURIComponent(sucursalId)}`;

    console.debug("[WebSocket] Attempting to connect:", url.replace(/token=[^&]+/, "token=***"));

    try {
      ws = new WebSocket(url);

      ws.onopen = () => {
        console.debug("[WebSocket] Connection opened");
        state = WebSocketState.CONNECTED;
        reconnectAttempts = 0; // Reset on successful connection
        
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
        state = WebSocketState.DISCONNECTED;
        
        if (onError) {
          onError(error);
        }
      };

      ws.onclose = (event) => {
        console.debug("[WebSocket] Connection closed", {
          code: event.code,
          reason: event.reason,
          wasClean: event.wasClean,
          state: state,
        });
        
        state = WebSocketState.DISCONNECTED;
        
        if (onClose) {
          onClose();
        }

        // Attempt to reconnect if not intentionally disconnected
        if (!isIntentionallyDisconnected && reconnectAttempts < maxReconnectAttempts) {
          state = WebSocketState.RECONNECTING;
          const delay = calculateBackoffDelay(reconnectAttempts, baseDelay, maxDelay, jitter);
          reconnectAttempts++;
          
          console.log(
            `[WebSocket] Reconnecting in ${Math.floor(delay)}ms ` +
            `(attempt ${reconnectAttempts}/${maxReconnectAttempts})...`
          );
          
          reconnectTimeoutId = setTimeout(() => {
            connect();
          }, delay);
        } else if (reconnectAttempts >= maxReconnectAttempts) {
          console.error("[WebSocket] Max reconnection attempts reached. Stopping reconnection.");
          state = WebSocketState.DISCONNECTED;
        }
      };
    } catch (error) {
      console.error("[WebSocket] Error creating connection:", error);
      state = WebSocketState.DISCONNECTED;
      
      if (onError) {
        onError(error as Event);
      }
    }
  }

  function disconnect(): void {
    console.debug("[WebSocket] Disconnecting intentionally");
    isIntentionallyDisconnected = true;
    state = WebSocketState.CLOSING;
    
    cleanup();
    
    state = WebSocketState.DISCONNECTED;
  }

  // Cleanup on hot reload (Vite HMR)
  if (typeof import.meta !== 'undefined' && (import.meta as any).hot) {
    (import.meta as any).hot.dispose(() => {
      console.debug("[WebSocket] Hot reload detected, cleaning up connection");
      cleanup();
    });
  }

  // Cleanup on page unload
  if (typeof window !== 'undefined') {
    window.addEventListener('beforeunload', () => {
      cleanup();
    });
  }

  return {
    connect,
    disconnect,
  };
}
