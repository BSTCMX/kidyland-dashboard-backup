/**
 * Timers store - Real-time timer management with Hybrid Intelligent Polling.
 * 
 * Handles fetching active timers and polling for real-time updates with:
 * - Adaptive polling (5-30s) with ETag caching
 * - Alert polling (10s) with recovery mechanism
 * - Visibility-aware pausing
 * - Client-side countdown for zero-latency UI
 */
import { writable, get } from "svelte/store";
import { get as apiGet, post } from "@kidyland/utils";
import type { Timer, ServiceAlert } from "@kidyland/shared/types";
import { addNotification, removeNotification } from "./notifications";
import { timerPollingService } from "$lib/services/timerPollingService";
import { alertPollingService } from "$lib/services/alertPollingService";

export interface TimersState {
  list: Timer[];
  loading: boolean;
  error: string | null;
  wsConnected: boolean; // Kept for backward compatibility, represents polling active
}

export const timersStore = writable<TimersState>({
  list: [],
  loading: false,
  error: null,
  wsConnected: false,
});

/**
 * Polling state object.
 */
const pollingState = {
  currentSucursalId: null as string | null,
  isActive: false,
  countdownInterval: null as number | null,
};

// Audio elements for alert sounds
const alertAudioElements: Map<number, HTMLAudioElement> = new Map();

// Track active alerts to prevent duplicates
const activeAlertKeys = new Set<string>();

// Track local updates for optimistic UI
const lastLocalUpdate = new Map<string, number>();

/**
 * Generate unique key for an alert.
 */
function getAlertKey(timerId: string, alertMinutes: number): string {
  return `${timerId}:${alertMinutes}`;
}

/**
 * Acknowledge alert in backend to prevent re-showing.
 */
async function acknowledgeAlert(timerId: string, alertMinutes: number): Promise<void> {
  try {
    await post(`/timers/${timerId}/alerts/acknowledge?alert_minutes=${alertMinutes}`, {});
    console.log("[TimerStore] Alert acknowledged:", { timerId, alertMinutes });
  } catch (error: any) {
    console.error("[TimerStore] Failed to acknowledge alert:", error);
    throw error;
  }
}

/**
 * Fetch active timers for a sucursal.
 */
export async function fetchActiveTimers(sucursalId: string): Promise<void> {
  timersStore.update((state) => ({ ...state, loading: true, error: null }));

  try {
    const response = await apiGet<any[]>(`/timers/active?sucursal_id=${sucursalId}`);
    
    const timers: Timer[] = response
      .map((item) => {
        const timerId = item.id || `timer-${Date.now()}-${Math.random()}`;
        
        return {
          id: timerId,
          sale_id: item.sale_id || "",
          service_id: item.service_id || "",
          child_name: item.child_name || "",
          child_age: item.child_age || 0,
          children: item.children || null,  // Include children array from backend
          time_left_seconds: item.time_left_seconds || 0,
          status: item.status || "active",
          start_at: item.start_at || "",
          end_at: item.end_at || "",
          history: [],
        };
      })
      .filter((timer) => 
        timer.time_left_seconds > 0 && 
        ["active", "scheduled", "extended"].includes(timer.status)
      );

    timersStore.update((state) => ({
      ...state,
      list: timers,
      loading: false,
      error: null,
    }));
  } catch (error: any) {
    console.error("[TimerStore] Error fetching timers:", error);
    timersStore.update((state) => ({
      ...state,
      loading: false,
      error: error.message || "Error fetching timers",
    }));
  }
}

/**
 * Start polling for timer updates and alerts.
 */
export function startTimerPolling(sucursalId: string): void {
  if (pollingState.isActive && pollingState.currentSucursalId === sucursalId) {
    console.log("[TimerStore] Polling already active for this sucursal");
    return;
  }

  // Stop existing polling if any
  stopTimerPolling();

  pollingState.currentSucursalId = sucursalId;
  pollingState.isActive = true;

  console.log("[TimerStore] Starting polling for sucursal:", sucursalId);

  // Fetch initial data
  fetchActiveTimers(sucursalId);

  // Start timer polling service
  timerPollingService.start(
    sucursalId,
    (timers) => handleTimerUpdate(timers),
    (error) => handlePollingError(error)
  );

  // Start alert polling service
  alertPollingService.start(
    sucursalId,
    (alert) => handleAlertReceived(alert),
    (error) => console.error("[TimerStore] Alert polling error:", error)
  );

  // Start client-side countdown
  startCountdown();

  // Update store status
  timersStore.update((state) => ({ ...state, wsConnected: true, error: null }));
}

/**
 * Stop polling for timer updates and alerts.
 */
export function stopTimerPolling(): void {
  if (!pollingState.isActive) {
    return;
  }

  console.log("[TimerStore] Stopping polling");

  // Stop polling services
  timerPollingService.stop();
  alertPollingService.stop();

  // Stop countdown
  if (pollingState.countdownInterval !== null) {
    clearInterval(pollingState.countdownInterval);
    pollingState.countdownInterval = null;
  }

  // Stop all alert sounds
  stopAllAlertSounds();

  // Reset state
  pollingState.isActive = false;
  pollingState.currentSucursalId = null;
  activeAlertKeys.clear();
  lastLocalUpdate.clear();

  // Update store
  timersStore.update((state) => ({ ...state, wsConnected: false }));
}

/**
 * Validate if a timer extension is legitimate.
 * 
 * @param serverSeconds - Time left from server
 * @param localSeconds - Time left from local countdown
 * @returns true if extension is legitimate (difference > 60s)
 */
function isLegitimateExtension(
  serverSeconds: number,
  localSeconds: number
): boolean {
  const EXTENSION_THRESHOLD = 60; // 1 minute minimum
  return serverSeconds > localSeconds + EXTENSION_THRESHOLD;
}

/**
 * Handle timer update from polling service.
 */
function handleTimerUpdate(timersData: any[]): void {
  const state = get(timersStore);
  const currentTimersMap = new Map(state.list.map((t) => [t.id, t]));
  const updatedTimersMap = new Map<string, Timer>();

  // Process each timer from server
  timersData.forEach((item) => {
    const timerId = item.id;
    const currentTimer = currentTimersMap.get(timerId);
    const timeLeftSeconds = item.time_left_seconds || 0;
    const newStatus = item.status;
    const oldStatus = currentTimer?.status;

    // Detect status transitions
    if (currentTimer && oldStatus !== newStatus) {
      console.log(
        `[TimerTransition] Timer ${timerId} (${item.child_name || 'unknown'}): ${oldStatus} → ${newStatus}`
      );
    }

    // Check if timer was extended (legitimate extension only)
    if (currentTimer && currentTimer.time_left_seconds > 0 && isLegitimateExtension(timeLeftSeconds, currentTimer.time_left_seconds)) {
      const newTimeLeftMinutes = Math.ceil(timeLeftSeconds / 60);
      const oldTimeLeftMinutes = Math.ceil(currentTimer.time_left_seconds / 60);

      // Cancel obsolete alerts
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
        `[TimerExtended] Timer ${timerId} (${item.child_name || 'unknown'}) extended: ${oldTimeLeftMinutes} -> ${newTimeLeftMinutes} minutes`
      );
    }

    // Create/update timer
    const updatedTimer: Timer = {
      id: timerId,
      sale_id: item.sale_id || currentTimer?.sale_id || "",
      service_id: item.service_id || currentTimer?.service_id || "",
      child_name: item.child_name || currentTimer?.child_name || "",
      child_age: item.child_age || currentTimer?.child_age || 0,
      children: item.children || currentTimer?.children || null,
      time_left_seconds: timeLeftSeconds,
      status: item.status || currentTimer?.status || "active",
      start_at: item.start_at || currentTimer?.start_at || "",
      end_at: item.end_at || currentTimer?.end_at || "",
      history: currentTimer?.history || [],
    };

    if (updatedTimer.time_left_seconds > 0 && ["active", "scheduled", "extended"].includes(updatedTimer.status)) {
      updatedTimersMap.set(timerId, updatedTimer);
    }
  });

  // Update store
  timersStore.update((state) => ({
    ...state,
    list: Array.from(updatedTimersMap.values()),
  }));
}

/**
 * Handle alert received from alert polling service.
 */
function handleAlertReceived(alert: any): void {
  const timerId = alert.timer_id;
  const alertMinutes = alert.alert_minutes;
  const alertKey = getAlertKey(timerId, alertMinutes);

  // Skip if already shown
  if (activeAlertKeys.has(alertKey)) {
    return;
  }

  // Mark as active
  activeAlertKeys.add(alertKey);

  // Skip notifications in Display mode (public screen)
  const isDisplayRoute = typeof window !== 'undefined' && window.location.pathname.startsWith('/display');
  if (isDisplayRoute) {
    console.log("[TimerStore] Alert notification skipped in Display mode:", { timerId, alertMinutes });
    // Still acknowledge alert in backend to prevent re-showing
    acknowledgeAlert(timerId, alertMinutes).catch((error) => {
      console.error("[TimerStore] Failed to acknowledge alert:", error);
    });
    return;
  }

  // Get timer info
  const state = get(timersStore);
  const timer = state.list.find((t) => t.id === timerId);
  const childName = timer?.child_name || alert.timer?.child_name || "Timer";
  const timeLeftMinutes = Math.ceil((timer?.time_left_seconds || 0) / 60);

  // Get alert configuration to determine auto-dismiss behavior
  const alertsConfig = alert.alerts_config || [];
  const alertConfig = alertsConfig.find((a: any) => a.minutes_before === alertMinutes);
  const shouldLoop = alertConfig?.sound_loop || false;

  // Show notification (only in /recepcion/timers)
  // Auto-dismiss if sound doesn't loop, manual dismiss if sound loops
  const notificationId = addNotification({
    type: "warning",
    title: `Alerta: ${childName} tiene ${timeLeftMinutes} minutos restantes`,
    duration: shouldLoop ? 0 : 10000,  // Auto-dismiss in 10s if not looping
    persistent: shouldLoop,             // Persistent only if looping
    action: {
      label: "Cerrar Alerta",
      handler: () => {
        dismissTimerAlert(timerId, alertMinutes, notificationId);
      },
    },
  });

  // Play sound based on service configuration (from backend)
  // Skip sound if we're on Display route (public screen - already checked above)
  // Reuse alertConfig from notification setup above
  if (alertConfig?.sound_enabled && !isDisplayRoute) {
    playAlertSound(alertConfig, alertMinutes);
    console.log("[TimerStore] Alert sound playing:", { timerId, alertMinutes, childName, soundLoop: alertConfig.sound_loop });
  } else if (alertConfig) {
    const reason = isDisplayRoute ? "display route" : "sound disabled";
    console.log(`[TimerStore] Alert shown (sound skipped - ${reason}):`, { timerId, alertMinutes, childName });
  } else {
    console.log("[TimerStore] Alert shown (no config):", { timerId, alertMinutes, childName });
  }

  // Acknowledge alert in backend to prevent re-showing
  acknowledgeAlert(timerId, alertMinutes).catch((error) => {
    console.error("[TimerStore] Failed to acknowledge alert:", error);
  });
}

/**
 * Handle polling error.
 */
function handlePollingError(error: Error): void {
  console.error("[TimerStore] Polling error:", error);
  timersStore.update((state) => ({
    ...state,
    error: error.message || "Polling error",
  }));
}

/**
 * Start client-side countdown (updates every second).
 * 
 * Uses End-Time Based Countdown pattern:
 * - time_left_seconds is DERIVED from end_at (never mutated)
 * - Auto-corrects for drift, latency, and clock skew
 * - Survives page refresh
 * - Synchronized across clients
 */
function startCountdown(): void {
  if (pollingState.countdownInterval !== null) {
    clearInterval(pollingState.countdownInterval);
  }

  pollingState.countdownInterval = window.setInterval(() => {
    const state = get(timersStore);
    let hasChanges = false;

    const updatedList = state.list.map((timer) => {
      // time_left_seconds is DERIVED from end_at (source of truth)
      if (!timer.end_at) {
        return timer; // No end_at, keep current value
      }
      
      const endTime = new Date(timer.end_at).getTime();
      const now = Date.now();
      
      // Math.round for better UX (prevents "losing" 1 second visually)
      const time_left_seconds = Math.max(0, Math.round((endTime - now) / 1000));
      
      // Only update if changed
      if (time_left_seconds !== timer.time_left_seconds) {
        hasChanges = true;
        return {
          ...timer,
          time_left_seconds, // Derived, not mutated
        };
      }
      
      return timer;
    });

    if (hasChanges) {
      timersStore.update((state) => ({ ...state, list: updatedList }));
    }
  }, 1000);
}

/**
 * Dismiss a timer alert.
 */
export async function dismissTimerAlert(timerId: string, alertMinutes: number, notificationId?: string): Promise<void> {
  try {
    // Acknowledge alert on server
    await alertPollingService.acknowledgeAlert(timerId, alertMinutes);

    // Remove from active alerts
    const alertKey = getAlertKey(timerId, alertMinutes);
    activeAlertKeys.delete(alertKey);

    // Stop sound
    stopAlertSound(alertMinutes);

    // Remove notification
    if (notificationId) {
      removeNotification(notificationId);
    }

    console.log("[TimerStore] Alert dismissed:", { timerId, alertMinutes });
  } catch (error) {
    console.error("[TimerStore] Error dismissing alert:", error);
  }
}

/**
 * Play alert sound.
 */
function playAlertSound(alertConfig: ServiceAlert, alertMinutes: number): void {
  if (!alertConfig.sound_enabled) {
    return;
  }

  let audio = alertAudioElements.get(alertMinutes);
  if (!audio) {
    audio = new Audio("/sounds/alert.mp3");
    alertAudioElements.set(alertMinutes, audio);

    audio.addEventListener("ended", () => {
      if (alertConfig.sound_loop) {
        audio?.play().catch((err) => {
          console.error(`Error looping alert sound for ${alertMinutes}min:`, err);
        });
      }
    });
  }

  audio.loop = alertConfig.sound_loop || false;
  audio.currentTime = 0;
  audio.play().catch((err) => {
    console.error(`Error playing alert sound for ${alertMinutes}min:`, err);
  });
}

/**
 * Stop alert sound for specific alert type.
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
 * Update timer from extension (backward compatibility).
 * Used by ExtendTimerModal to update timer immediately after extension.
 */
export function updateTimerFromExtension(timerId: string, timerData: any): void {
  const state = get(timersStore);
  const timerIndex = state.list.findIndex((t) => t.id === timerId);

  if (timerIndex === -1) {
    console.warn(`[TimerStore] Timer ${timerId} not found for update`);
    return;
  }

  // Update timer with new data from backend
  const currentTimer = state.list[timerIndex];
  const updatedTimer: Timer = {
    ...currentTimer,
    time_left_seconds: timerData.time_left_seconds || 0,
    status: timerData.status || currentTimer.status,
    end_at: timerData.end_at || currentTimer.end_at,
  };

  timersStore.update((state) => {
    const newList = [...state.list];
    newList[timerIndex] = updatedTimer;
    return { ...state, list: newList };
  });

  console.log(`[TimerStore] Timer ${timerId} updated from extension`);
}

/**
 * Extend timer (optimistic UI update).
 */
export async function extendTimer(timerId: string, minutesToAdd: number): Promise<void> {
  const state = get(timersStore);
  const timerIndex = state.list.findIndex((t) => t.id === timerId);

  if (timerIndex === -1) {
    throw new Error(`Timer ${timerId} not found`);
  }

  // Record local update timestamp
  lastLocalUpdate.set(timerId, Date.now());

  // Optimistic UI update
  const currentTimer = state.list[timerIndex];
  const optimisticTimer: Timer = {
    ...currentTimer,
    time_left_seconds: currentTimer.time_left_seconds + minutesToAdd * 60,
  };

  timersStore.update((state) => {
    const newList = [...state.list];
    newList[timerIndex] = optimisticTimer;
    return { ...state, list: newList };
  });

  try {
    // Send to server
    await post(`/sales/${currentTimer.sale_id}/extend`, {
      timer_id: timerId,
      minutes_to_add: minutesToAdd,
    });

    // Force immediate poll to get confirmed data
    await timerPollingService.forcePoll();

    console.log("[TimerStore] Timer extended successfully:", { timerId, minutesToAdd });
  } catch (error: any) {
    console.error("[TimerStore] Error extending timer:", error);

    // Revert optimistic update on error
    timersStore.update((state) => {
      const newList = [...state.list];
      newList[timerIndex] = currentTimer;
      return { ...state, list: newList };
    });

    throw error;
  }
}

// Backward compatibility exports
export const connectTimerWebSocket = startTimerPolling;
export const disconnectTimerWebSocket = stopTimerPolling;
