/**
 * Alert Polling Service - Polls for pending timer alerts
 * 
 * Implements alert recovery mechanism:
 * - Regular polling for pending alerts (every 10s)
 * - Tracks shown alerts to prevent duplicates
 * - Visibility-aware pausing
 * - Automatic recovery on reconnection
 * 
 * Clean Architecture: Uses getApiUrl() for dynamic API URL resolution.
 */

import { getApiUrl } from '$lib/utils/api-config';

interface AlertPollingConfig {
  interval: number;
  jitterRange: number;
}

interface AlertPollingState {
  isPolling: boolean;
  isPaused: boolean;
  timeoutId: number | null;
  shownAlerts: Set<string>;
  errorCount: number;
  consecutiveFailures: number;
  degradedAt: number | null;
}

type AlertData = {
  id: string;
  timer_id: string;
  alert_minutes: number;
  triggered_at: string;
  status: string;
  timer: {
    id: string;
    sale_id: string;
    service_id: string;
    child_name: string;
    child_age: number;
    status: string;
  };
};

export class AlertPollingService {
  private config: AlertPollingConfig;
  private state: AlertPollingState;
  private onAlert: ((alert: AlertData) => void) | null = null;
  private onError: ((error: Error) => void) | null = null;
  private apiBaseUrl: string;
  private sucursalId: string | null = null;
  private lastSuccessfulData: AlertData[] | null = null;

  constructor(config?: Partial<AlertPollingConfig>) {
    this.config = {
      interval: 10000,
      jitterRange: 1000,
      ...config
    };

    this.state = {
      isPolling: false,
      isPaused: false,
      timeoutId: null,
      shownAlerts: new Set<string>(),
      errorCount: 0,
      consecutiveFailures: 0,
      degradedAt: null
    };

    // Get API base URL using dynamic configuration (Clean Architecture)
    // This handles development (localhost) and production (same-origin) correctly
    this.apiBaseUrl = getApiUrl();
  }

  start(sucursalId: string, onAlert: (alert: AlertData) => void, onError?: (error: Error) => void): void {
    if (this.state.isPolling) {
      console.warn('[AlertPolling] Already polling, stopping previous instance');
      this.stop();
    }

    this.sucursalId = sucursalId;
    this.onAlert = onAlert;
    this.onError = onError || null;
    this.state.isPolling = true;
    this.state.isPaused = false;
    this.state.errorCount = 0;

    console.log('[AlertPolling] Starting alert polling', {
      sucursalId,
      interval: this.config.interval
    });

    this.poll();
    this.setupVisibilityListener();
  }

  stop(): void {
    if (this.state.timeoutId !== null) {
      clearTimeout(this.state.timeoutId);
      this.state.timeoutId = null;
    }

    this.state.isPolling = false;
    this.state.isPaused = false;
    this.onAlert = null;
    this.onError = null;
    this.state.shownAlerts.clear();

    console.log('[AlertPolling] Stopped alert polling');
  }

  pause(): void {
    if (!this.state.isPolling) return;

    this.state.isPaused = true;
    if (this.state.timeoutId !== null) {
      clearTimeout(this.state.timeoutId);
      this.state.timeoutId = null;
    }

    console.log('[AlertPolling] Paused alert polling');
  }

  resume(): void {
    if (!this.state.isPolling || !this.state.isPaused) return;

    this.state.isPaused = false;
    console.log('[AlertPolling] Resumed alert polling');
    this.poll();
  }

  async acknowledgeAlert(timerId: string, alertMinutes: number): Promise<void> {
    try {
      const token = this.getToken();
      if (!token) {
        throw new Error('No authentication token available');
      }

      const url = new URL(`${this.apiBaseUrl}/timers/${timerId}/alerts/acknowledge`);
      url.searchParams.set('alert_minutes', alertMinutes.toString());

      const response = await fetch(url.toString(), {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      console.log('[AlertPolling] Alert acknowledged', { timerId, alertMinutes });

    } catch (error) {
      console.error('[AlertPolling] Error acknowledging alert', error);
      throw error;
    }
  }

  private async poll(): Promise<void> {
    if (!this.state.isPolling || this.state.isPaused) {
      return;
    }

    try {
      const token = this.getToken();
      if (!token) {
        throw new Error('No authentication token available');
      }

      const url = new URL(`${this.apiBaseUrl}/timers/alerts/pending`);
      if (this.sucursalId) {
        url.searchParams.set('sucursal_id', this.sucursalId);
      }

      const response = await fetch(url.toString(), {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const alerts: AlertData[] = await response.json();
        this.handleAlerts(alerts);
        
        this.state.errorCount = 0;
        this.state.consecutiveFailures = 0;
        
        if (this.state.degradedAt !== null) {
          const recoveryTime = Date.now() - this.state.degradedAt;
          console.log(`[AlertPolling] System recovered after ${Math.round(recoveryTime / 1000)}s`);
          this.state.degradedAt = null;
        }
      } else if (response.status === 401) {
        throw new Error('Authentication failed');
      } else {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

    } catch (error) {
      this.handleError(error as Error);
    }

    this.scheduleNextPoll();
  }

  private handleAlerts(alerts: AlertData[]): void {
    this.lastSuccessfulData = alerts;

    if (alerts.length === 0) {
      return;
    }

    console.log('[AlertPolling] Received alerts', { count: alerts.length });

    for (const alert of alerts) {
      const alertKey = `${alert.timer_id}-${alert.alert_minutes}`;

      if (this.state.shownAlerts.has(alertKey)) {
        continue;
      }

      this.state.shownAlerts.add(alertKey);

      if (this.onAlert) {
        this.onAlert(alert);
      }

      console.log('[AlertPolling] New alert shown', {
        timerId: alert.timer_id,
        alertMinutes: alert.alert_minutes,
        childName: alert.timer.child_name
      });
    }
  }

  private handleError(error: Error): void {
    this.state.errorCount++;
    this.state.consecutiveFailures++;

    const FAILURE_THRESHOLD = 2;

    if (this.state.consecutiveFailures === 1) {
      console.debug('[AlertPolling] Transient failure', {
        error: error.message,
        errorCount: this.state.errorCount
      });
    } else if (this.state.consecutiveFailures >= FAILURE_THRESHOLD) {
      if (this.state.degradedAt === null) {
        this.state.degradedAt = Date.now();
      }
      
      console.warn('[AlertPolling] Persistent failure - system degraded', {
        error: error.message,
        consecutiveFailures: this.state.consecutiveFailures,
        errorCount: this.state.errorCount,
        degradedForSeconds: Math.round((Date.now() - this.state.degradedAt) / 1000)
      });

      if (this.lastSuccessfulData && this.lastSuccessfulData.length > 0) {
        console.log('[AlertPolling] Using fallback data (last successful response)');
        this.handleAlerts(this.lastSuccessfulData);
      }
    }

    if (this.onError) {
      this.onError(error);
    }

    if (this.state.errorCount >= 10) {
      console.error('[AlertPolling] Too many errors, stopping alert polling');
      this.stop();
    }
  }

  private scheduleNextPoll(): void {
    if (!this.state.isPolling || this.state.isPaused) {
      return;
    }

    const jitter = (Math.random() - 0.5) * this.config.jitterRange;
    const delay = Math.max(0, this.config.interval + jitter);

    this.state.timeoutId = window.setTimeout(() => {
      this.poll();
    }, delay);
  }

  private setupVisibilityListener(): void {
    const handleVisibilityChange = () => {
      if (document.hidden) {
        this.pause();
      } else {
        this.resume();
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);

    const originalStop = this.stop.bind(this);
    this.stop = () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      originalStop();
    };
  }

  private getToken(): string | null {
    try {
      return localStorage.getItem('auth_token');
    } catch (error) {
      console.error('[AlertPolling] Error getting token', error);
      return null;
    }
  }

  getState(): Readonly<Omit<AlertPollingState, 'shownAlerts'> & { shownAlertsCount: number }> {
    return {
      isPolling: this.state.isPolling,
      isPaused: this.state.isPaused,
      timeoutId: this.state.timeoutId,
      shownAlertsCount: this.state.shownAlerts.size,
      errorCount: this.state.errorCount
    };
  }
}

export const alertPollingService = new AlertPollingService();
