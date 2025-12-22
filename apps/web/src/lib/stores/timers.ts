/**
 * Timers store - Real-time timer management with WebSocket support.
 * 
 * Handles fetching active timers and WebSocket connections for real-time updates.
 */
import { writable, get } from "svelte/store";
import { get as apiGet, createTimerWebSocket, post } from "@kidyland/utils";
import type { Timer, ServiceAlert } from "@kidyland/shared/types";
import { addNotification, removeNotification } from "./notifications";

export interface TimersState {
  list: Timer[];
  loading: boolean;
  error: string | null;
  wsConnected: boolean;
}

export const timersStore = writable<TimersState>({
  list: [],
  loading: false,
  error: null,
  wsConnected: false,
});

let wsConnection: ReturnType<typeof createTimerWebSocket> | null = null;

/**
 * Singleton WebSocket connection state object.
 * 
 * Encapsulates all WebSocket connection state in a single object to:
 * - Prevent duplicate declarations
 * - Improve code organization
 * - Make state management more maintainable
 * - Enable easy extension of state in the future
 */
const wsState = {
  currentSucursalId: null as string | null,
  connectionAttemptInProgress: false,
};

// Audio elements for alert sounds (one per alert type to support multiple simultaneous alerts)
const alertAudioElements: Map<number, HTMLAudioElement> = new Map();

// Track active alerts to prevent duplicate notifications
// Key format: "timerId:alertMinutes"
const activeAlertKeys = new Set<string>();

// Track timestamps of local updates to prevent WebSocket from overwriting recent local changes
// Key: timerId, Value: timestamp (Date.now()) when timer was last updated locally
const lastLocalUpdate = new Map<string, number>();

// Track server timestamps (updated_at) for each timer to enable server-side conflict resolution
// Key: timerId, Value: ISO timestamp string from server (updated_at field)
const lastServerUpdate = new Map<string, string>();

/**
 * Generate a unique key for an alert.
 */
function getAlertKey(timerId: string, alertMinutes: number): string {
  return `${timerId}:${alertMinutes}`;
}

/**
 * Compare two ISO timestamp strings to determine which is more recent.
 * 
 * @param timestamp1 - ISO timestamp string (e.g., "2024-01-01T12:00:00Z")
 * @param timestamp2 - ISO timestamp string (e.g., "2024-01-01T12:00:00Z")
 * @returns positive number if timestamp1 > timestamp2, negative if timestamp1 < timestamp2, 0 if equal
 */
function compareTimestamps(timestamp1: string | null | undefined, timestamp2: string | null | undefined): number {
  if (!timestamp1 || !timestamp2) {
    return 0; // If either is missing, cannot compare
  }
  
  try {
    const date1 = new Date(timestamp1).getTime();
    const date2 = new Date(timestamp2).getTime();
    return date1 - date2;
  } catch (error) {
    console.warn("[TimerStore] Error comparing timestamps:", error);
    return 0;
  }
}

/**
 * Determine if a WebSocket update should be accepted for a specific timer.
 * 
 * Uses hybrid approach:
 * 1. Phase 1 (fallback): Local timestamp tracking (if server timestamp not available)
 * 2. Phase 2 (preferred): Server timestamp comparison (if server provides updated_at)
 * 
 * This prevents WebSocket from overwriting recent local optimistic updates or more recent server updates.
 * 
 * @param timerId - Timer ID to check
 * @param wsTimeLeftSeconds - Time left from WebSocket update
 * @param currentTimeLeftSeconds - Current time left in store
 * @param wsUpdatedAt - Server timestamp (updated_at) from WebSocket update (optional, Phase 2)
 * @param cooldownMs - Cooldown period in milliseconds for local updates (default: 10000 = 10 seconds)
 * @returns true if WebSocket update should be accepted, false if it should be ignored
 */
function shouldAcceptWebSocketUpdate(
  timerId: string,
  wsTimeLeftSeconds: number,
  currentTimeLeftSeconds: number,
  wsUpdatedAt?: string | null,
  cooldownMs: number = 10000
): boolean {
  // Phase 2: Server timestamp comparison (preferred if available)
  if (wsUpdatedAt) {
    const lastServerTimestamp = lastServerUpdate.get(timerId);
    
    // If we have a previous server timestamp, compare them
    if (lastServerTimestamp) {
      const comparison = compareTimestamps(wsUpdatedAt, lastServerTimestamp);
      
      // If WebSocket timestamp is older (negative comparison), reject the update (stale data)
      if (comparison < 0) {
        console.warn(
          `[TimerWebSocket] Ignoring stale update (server timestamp) for timer ${timerId}: ` +
          `WebSocket updated_at=${wsUpdatedAt} is older than current updated_at=${lastServerTimestamp}`
        );
        return false;
      }
      
      // If WebSocket timestamp is newer or equal, accept it
      // (We'll update lastServerUpdate after accepting)
      return true;
    } else {
      // First time seeing this timer from server, accept and track
      return true;
    }
  }
  
  // Phase 1: Fallback to local timestamp tracking (if server timestamp not available)
  const localUpdateTime = lastLocalUpdate.get(timerId);
  
  // If no local update recorded, always accept WebSocket update
  if (!localUpdateTime) {
    return true;
  }
  
  const now = Date.now();
  const timeSinceLocalUpdate = now - localUpdateTime;
  
  // If within cooldown period, be more conservative about accepting WebSocket updates
  if (timeSinceLocalUpdate < cooldownMs) {
    // During cooldown, only accept if WebSocket shows MORE time (extension succeeded) or same time
    // Reject if WebSocket shows significantly LESS time (likely stale data)
    const difference = wsTimeLeftSeconds - currentTimeLeftSeconds;
    const differenceMinutes = Math.abs(difference / 60);
    
    // Accept if WebSocket shows same or more time (extension is reflected)
    if (difference >= -30) { // Allow 30 seconds tolerance for timing differences
      return true;
    }
    
    // Reject if WebSocket shows significantly less time (stale data)
    if (differenceMinutes > 1) {
      console.warn(
        `[TimerWebSocket] Ignoring stale update during cooldown for timer ${timerId}: ` +
        `${Math.floor(currentTimeLeftSeconds / 60)} min (local) vs ${Math.floor(wsTimeLeftSeconds / 60)} min (WebSocket). ` +
        `Local update was ${Math.floor(timeSinceLocalUpdate / 1000)}s ago.`
      );
      return false;
    }
  }
  
  // After cooldown period, accept WebSocket updates normally
  // But still reject if there's a significant decrease (more than 2 minutes)
  const significantDecrease = currentTimeLeftSeconds > 0 && 
                              wsTimeLeftSeconds < currentTimeLeftSeconds && 
                              (currentTimeLeftSeconds - wsTimeLeftSeconds) > 120; // 2 minutes
  
  if (significantDecrease) {
    console.warn(
      `[TimerWebSocket] Ignoring significant decrease for timer ${timerId}: ` +
      `${Math.floor(currentTimeLeftSeconds / 60)} min (current) -> ${Math.floor(wsTimeLeftSeconds / 60)} min (WebSocket)`
    );
    return false;
  }
  
  return true;
}

/**
 * Fetch active timers for a sucursal.
 * 
 * @param sucursalId - Sucursal ID to fetch timers for
 */
export async function fetchActiveTimers(sucursalId: string): Promise<void> {
  timersStore.update((state) => ({ ...state, loading: true, error: null }));

  try {
    const response = await apiGet<any[]>(`/timers/active?sucursal_id=${sucursalId}`);
    
    // Transform API response to Timer format
    // Backend returns: {id, sale_id, service_id, child_name, child_age, status, start_at, end_at, time_left_minutes}
    // Filter out timers with time_left <= 0 (expired/finished timers)
    const timers: Timer[] = response
      .map((item, index) => {
        // Ensure id is always defined (use item.id, fallback to sale_id, then generate unique)
        const timerId = item.id || item.sale_id || `temp-${Date.now()}-${index}`;
        
        return {
          id: timerId,
          sale_id: item.sale_id || "",
          service_id: item.service_id || "", // Include service_id for extension functionality
          child_name: item.child_name || "",
          child_age: item.child_age || 0,
          time_left_seconds: (item.time_left_minutes || 0) * 60, // Convert minutes to seconds
          status: item.status || "active",
          start_at: item.start_at || "",
          end_at: item.end_at || "",
          history: [], // History not provided by API currently
        };
      })
      .filter((timer) => timer.time_left_seconds > 0); // Only include timers with time left

    timersStore.update((state) => ({
      ...state,
      list: timers,
      loading: false,
      error: null,
    }));
  } catch (error: any) {
    timersStore.update((state) => ({
      ...state,
      loading: false,
      error: error.message || "Error al cargar timers",
    }));
  }
}

/**
 * Connect to timer WebSocket for real-time updates.
 * 
 * Implements singleton pattern to prevent multiple connections:
 * - Only one connection per sucursalId at a time
 * - Automatically disconnects previous connection if sucursalId changes
 * - Prevents duplicate connection attempts
 * 
 * @param sucursalId - Sucursal ID to subscribe to
 * @param token - Authentication token (deprecated, token is obtained internally via getToken())
 */
export function connectTimerWebSocket(sucursalId: string, token?: string): void {
  // Validate sucursalId
  if (!sucursalId || sucursalId.trim() === "") {
    console.error("[TimerStore] Cannot connect: invalid sucursalId");
    return;
  }

  // If already connected to the same sucursal, do nothing
  if (wsConnection && wsState.currentSucursalId === sucursalId && wsState.connectionAttemptInProgress === false) {
    console.debug("[TimerStore] WebSocket already connected to sucursal:", sucursalId);
    return;
  }

  // If connection attempt is in progress for same sucursal, wait
  if (wsState.connectionAttemptInProgress && wsState.currentSucursalId === sucursalId) {
    console.debug("[TimerStore] Connection attempt already in progress for sucursal:", sucursalId);
    return;
  }

  // Disconnect existing connection if sucursal changed or connection exists
  if (wsConnection) {
    console.debug(
      "[TimerStore] Disconnecting existing connection",
      wsState.currentSucursalId !== sucursalId ? `(sucursal changed: ${wsState.currentSucursalId} -> ${sucursalId})` : ""
    );
    try {
      // Disconnect will handle different connection states gracefully
      wsConnection.disconnect();
    } catch (error) {
      // Ignore errors during cleanup (connection may already be closing)
      console.debug("[TimerStore] Error during WebSocket cleanup (ignored):", error);
    }
    wsConnection = null;
    wsState.currentSucursalId = null;
  }

  // Set connection attempt flag
  wsState.connectionAttemptInProgress = true;
  wsState.currentSucursalId = sucursalId;

  // createTimerWebSocket obtains token internally via getToken() from auth store
  // Token parameter is kept for backward compatibility but not used
  wsConnection = createTimerWebSocket(sucursalId, {
    onOpen: () => {
      wsState.connectionAttemptInProgress = false;
      timersStore.update((state) => ({ ...state, wsConnected: true }));
      console.debug("[TimerStore] WebSocket connected successfully to sucursal:", sucursalId);
    },
    onMessage: (data: any) => {
      if (data.type === "timers_update") {
        // Get current timers from store
        const currentTimers = get(timersStore).list;
        const currentTimersMap = new Map<string, Timer>();
        currentTimers.forEach((t) => {
          if (t.id) {
            currentTimersMap.set(t.id, t);
          }
        });

        // Build a map of WebSocket timers by ID for efficient lookup
        const wsTimersMap = new Map<string, any>();
        (data.timers || []).forEach((item: any, index: number) => {
          const timerId = item.id || item.sale_id || `temp-${Date.now()}-${index}`;
          wsTimersMap.set(timerId, item);
        });

        // Intelligent merge: Update only timers that changed, preserve local updates
        const updatedTimersMap = new Map<string, Timer>(currentTimersMap);
        let hasChanges = false;

        // Process each timer from WebSocket
        wsTimersMap.forEach((wsItem: any, timerId: string) => {
          const currentTimer = currentTimersMap.get(timerId);
          const wsTimeLeftSeconds = (wsItem.time_left_minutes || 0) * 60;
          const currentTimeLeftSeconds = currentTimer?.time_left_seconds || 0;
          const wsUpdatedAt = wsItem.updated_at || null; // Server timestamp (Phase 2)

          // Check if we should accept this WebSocket update (using server timestamp if available)
          if (!shouldAcceptWebSocketUpdate(timerId, wsTimeLeftSeconds, currentTimeLeftSeconds, wsUpdatedAt)) {
            // Keep current timer, skip WebSocket update
            return;
          }

          // Track server timestamp if provided (Phase 2)
          if (wsUpdatedAt) {
            lastServerUpdate.set(timerId, wsUpdatedAt);
          }

          // Use WebSocket update
          const finalTimeLeftSeconds = wsTimeLeftSeconds;
          const oldTimeLeftSeconds = currentTimeLeftSeconds;

          // Filter out timers with time_left <= 0 (expired/finished timers)
          // Only process and include timers that still have time remaining
          if (finalTimeLeftSeconds <= 0) {
            // Timer has expired - remove it from the map if it exists
            if (updatedTimersMap.has(timerId)) {
              updatedTimersMap.delete(timerId);
              hasChanges = true;
            }
            return; // Skip processing expired timers
          }

          // Check if timer was extended (time_left increased significantly)
          if (oldTimeLeftSeconds > 0 && finalTimeLeftSeconds > oldTimeLeftSeconds) {
            // Timer was extended - cancel all active alerts for thresholds below new time_left
            const newTimeLeftMinutes = Math.ceil(finalTimeLeftSeconds / 60);
            const oldTimeLeftMinutes = Math.ceil(oldTimeLeftSeconds / 60);

            // Cancel alerts for thresholds that are now below the new time_left
            for (let alertMinutes = 1; alertMinutes <= oldTimeLeftMinutes; alertMinutes++) {
              if (alertMinutes < newTimeLeftMinutes) {
                const alertKey = getAlertKey(timerId, alertMinutes);
                if (activeAlertKeys.has(alertKey)) {
                  stopAlertSound(alertMinutes);
                  activeAlertKeys.delete(alertKey);
                }
              }
            }

            console.log(
              `[TimerExtended] Timer ${timerId} extended via WebSocket: ${oldTimeLeftMinutes} -> ${newTimeLeftMinutes} minutes. ` +
              `Cancelled obsolete alerts for thresholds < ${newTimeLeftMinutes}`
            );
          }

          // Create/update timer entry
          const updatedTimer: Timer = {
            id: timerId,
            sale_id: wsItem.sale_id || currentTimer?.sale_id || "",
            service_id: wsItem.service_id || currentTimer?.service_id || "",
            child_name: wsItem.child_name || currentTimer?.child_name || "",
            child_age: wsItem.child_age || currentTimer?.child_age || 0,
            time_left_seconds: finalTimeLeftSeconds,
            status: wsItem.status || currentTimer?.status || "active",
            start_at: wsItem.start_at || currentTimer?.start_at || "",
            end_at: wsItem.end_at || currentTimer?.end_at || "",
            history: currentTimer?.history || [], // Preserve existing history
          };

          updatedTimersMap.set(timerId, updatedTimer);
          hasChanges = true;
        });

        // Remove timers that are no longer in WebSocket update (they were deactivated/removed)
        // But only if they weren't recently updated locally (to avoid removing during cooldown)
        const now = Date.now();
        const cooldownMs = 10000; // 10 seconds
        currentTimersMap.forEach((currentTimer, timerId) => {
          if (!wsTimersMap.has(timerId)) {
            const localUpdateTime = lastLocalUpdate.get(timerId);
            // Only remove if not recently updated locally
            if (!localUpdateTime || (now - localUpdateTime) >= cooldownMs) {
              updatedTimersMap.delete(timerId);
              hasChanges = true;
            }
          }
        });

        // Clean up old local update timestamps periodically (every WebSocket update)
        cleanupOldLocalUpdates();

        // Only update store if there were actual changes
        if (hasChanges) {
          timersStore.update((state) => ({
            ...state,
            list: Array.from(updatedTimersMap.values()),
            wsConnected: true,
          }));
        } else {
          // Still update wsConnected status even if no changes
          timersStore.update((state) => ({
            ...state,
            wsConnected: true,
          }));
        }
      } else if (data.type === "timer_alert") {
        // Show notification for timer alerts
        const timer = data.timer;
        const timerId = timer?.id || data.timer?.timer_id || "";
        const timeLeftMinutes = timer?.time_left_minutes || Math.ceil((timer?.time_left || 0) / 60);
        const alertMinutes = data.alert_minutes || timeLeftMinutes; // Backend sends which alert triggered (5, 10, 15)
        const alertsConfig = data.alerts_config || []; // Backend sends service alerts_config
        
        // Generate alert key to prevent duplicates
        const alertKey = getAlertKey(timerId, alertMinutes);
        
        // Skip if this alert is already active (prevent duplicate notifications)
        if (activeAlertKeys.has(alertKey)) {
          return;
        }
        
        // Mark as active
        activeAlertKeys.add(alertKey);
        
        // Show persistent notification with dismiss button
        const notificationId = addNotification({
          type: "warning",
          title: `⚠️ Alerta: ${timer?.child_name || "Timer"} tiene ${Math.ceil(timeLeftMinutes)} minutos restantes`,
          duration: 0, // No auto-dismiss (persistent)
          persistent: true,
          action: {
            label: "Cerrar Alerta",
            handler: () => {
              dismissTimerAlert(timerId, alertMinutes, notificationId);
            }
          }
        });

        // Play sound if configured
        if (alertsConfig && alertsConfig.length > 0) {
          const alertConfig = alertsConfig.find((a: ServiceAlert) => a.minutes_before === alertMinutes);
          if (alertConfig?.sound_enabled) {
            playAlertSound(alertConfig, alertMinutes);
          }
        }
      }
    },
    onError: (error: Event) => {
      wsState.connectionAttemptInProgress = false;
      const errorMessage = error instanceof Error ? error.message : "Error en WebSocket";
      console.error("[TimerStore] WebSocket error:", errorMessage);
      timersStore.update((state) => ({
        ...state,
        error: errorMessage,
        wsConnected: false,
      }));
    },
    onClose: () => {
      wsState.connectionAttemptInProgress = false;
      console.debug("[TimerStore] WebSocket disconnected");
      timersStore.update((state) => ({ ...state, wsConnected: false }));
    },
  });

  // Connect the WebSocket
  wsConnection.connect();
}

/**
 * Clean up old local update timestamps and server timestamps to prevent memory leaks.
 * Removes timestamps older than the cooldown period (10 seconds by default).
 */
function cleanupOldLocalUpdates(cooldownMs: number = 10000): void {
  const now = Date.now();
  const expiredTimerIds: string[] = [];
  
  // Clean up local update timestamps
  lastLocalUpdate.forEach((timestamp, timerId) => {
    if (now - timestamp > cooldownMs * 2) { // Clean up after 2x cooldown (20 seconds)
      expiredTimerIds.push(timerId);
    }
  });
  
  expiredTimerIds.forEach((timerId) => {
    lastLocalUpdate.delete(timerId);
    // Also clean up server timestamp for removed timers (they're no longer active)
    lastServerUpdate.delete(timerId);
  });
  
  if (expiredTimerIds.length > 0) {
    console.debug(`[TimerStore] Cleaned up ${expiredTimerIds.length} old update timestamps (local and server)`);
  }
}

/**
 * Disconnect from timer WebSocket.
 * 
 * Implements proper cleanup:
 * - Disconnects WebSocket connection
 * - Resets singleton state
 * - Cleans up resources (sounds, timestamps)
 */
export function disconnectTimerWebSocket(): void {
  if (wsConnection) {
    console.debug("[TimerStore] Disconnecting WebSocket");
    try {
      // Disconnect will handle state transitions properly via state machine
      wsConnection.disconnect();
    } catch (error) {
      // Ignore errors during disconnect (connection may already be closed)
      console.debug("[TimerStore] Error disconnecting WebSocket (ignored):", error);
    }
    wsConnection = null;
  }
  
  // Reset singleton state
  wsState.currentSucursalId = null;
  wsState.connectionAttemptInProgress = false;
  
  // Stop all alert sounds
  stopAllAlertSounds();
  // Clean up old local update timestamps
  cleanupOldLocalUpdates();
  timersStore.update((state) => ({ ...state, wsConnected: false }));
}

/**
 * Update a timer in the store with new data from extension response.
 * This allows immediate UI update without waiting for WebSocket broadcast.
 * 
 * @param timerId - Timer ID to update
 * @param timerData - Timer data from extension API response (includes time_left_minutes)
 */
export function updateTimerFromExtension(timerId: string, timerData: any): void {
  timersStore.update((state) => {
    const timerIndex = state.list.findIndex((t) => t.id === timerId);
    
    if (timerIndex === -1) {
      // Timer not found, log warning but don't throw error
      console.warn(`[TimerExtension] Timer ${timerId} not found in store for immediate update`);
      return state;
    }
    
    // Get current timer
    const currentTimer = state.list[timerIndex];
    
    // Transform API response timer data to Timer format
    // Backend returns: {id, sale_id, service_id, child_name, child_age, status, start_at, end_at, time_left_minutes, ...}
    const updatedTimer: Timer = {
      id: timerData.id || timerId,
      sale_id: timerData.sale_id || currentTimer.sale_id,
      service_id: timerData.service_id || currentTimer.service_id,
      child_name: timerData.child_name || currentTimer.child_name,
      child_age: timerData.child_age || currentTimer.child_age,
      time_left_seconds: (timerData.time_left_minutes || 0) * 60, // Convert minutes to seconds
      status: timerData.status || currentTimer.status,
      start_at: timerData.start_at || currentTimer.start_at,
      end_at: timerData.end_at || currentTimer.end_at,
      history: currentTimer.history, // Preserve existing history
    };
    
    // Create new list with updated timer
    const newList = [...state.list];
    newList[timerIndex] = updatedTimer;
    
    // Register local update timestamp to prevent WebSocket from overwriting this update (Phase 1 fallback)
    lastLocalUpdate.set(timerId, Date.now());
    
    // Also track server timestamp if provided in response (Phase 2 preferred)
    if (timerData.updated_at) {
      lastServerUpdate.set(timerId, timerData.updated_at);
    }
    
    console.log(
      `[TimerExtension] Timer ${timerId} updated immediately: ${Math.floor(currentTimer.time_left_seconds / 60)} -> ${timerData.time_left_minutes} minutes. ` +
      `Protected from WebSocket overwrite using ${timerData.updated_at ? 'server timestamp' : 'local timestamp (10s cooldown)'}.`
    );
    
    return {
      ...state,
      list: newList,
    };
  });
}

/**
 * Play alert sound based on configuration.
 * 
 * @param alertConfig - Service alert configuration
 * @param alertMinutes - Minutes before timer ends (5, 10, or 15)
 */
function playAlertSound(alertConfig: ServiceAlert, alertMinutes: number): void {
  // Get or create audio element for this alert type
  let audio = alertAudioElements.get(alertMinutes);
  if (!audio) {
    audio = new Audio("/sounds/alert.mp3");
    alertAudioElements.set(alertMinutes, audio);
    
    // Handle audio end event
    audio.addEventListener("ended", () => {
      if (alertConfig.sound_loop) {
        // If loop is enabled, restart the sound
        audio?.play().catch((err) => {
          console.error(`Error looping alert sound for ${alertMinutes}min:`, err);
        });
      }
    });
  }

  // Configure audio based on alert config
  audio.loop = alertConfig.sound_loop || false;
  
  // Reset to beginning and play
  audio.currentTime = 0;
  audio.play().catch((err) => {
    console.error(`Error playing alert sound for ${alertMinutes}min:`, err);
  });
}

/**
 * Stop alert sound for a specific alert type.
 * 
 * @param alertMinutes - Minutes before timer ends (5, 10, or 15)
 */
export function stopAlertSound(alertMinutes: number): void {
  const audio = alertAudioElements.get(alertMinutes);
  if (audio) {
    audio.pause();
    audio.currentTime = 0;
  }
}

/**
 * Stop all alert sounds.
 */
export function stopAllAlertSounds(): void {
  alertAudioElements.forEach((audio) => {
    audio.pause();
    audio.currentTime = 0;
  });
}

/**
 * Dismiss a timer alert.
 * Stops the sound, removes the alert from active tracking, removes notification, and acknowledges it on the backend.
 * 
 * @param timerId - Timer ID
 * @param alertMinutes - Alert threshold in minutes
 * @param notificationId - Optional notification ID to remove
 */
export async function dismissTimerAlert(timerId: string, alertMinutes: number, notificationId?: string): Promise<void> {
  const alertKey = getAlertKey(timerId, alertMinutes);
  
  // Stop sound for this alert
  stopAlertSound(alertMinutes);
  
  // Remove notification if ID provided
  if (notificationId) {
    removeNotification(notificationId);
  }
  
  // Remove from active alerts (allows re-triggering if timer is extended)
  activeAlertKeys.delete(alertKey);
  
  // Acknowledge on backend for synchronization across all clients
  try {
    await post(`/timers/${timerId}/alerts/acknowledge?alert_minutes=${alertMinutes}`);
  } catch (error) {
    console.error("Error acknowledging alert on backend:", error);
    // Continue even if API call fails (local dismiss still works)
  }
}
