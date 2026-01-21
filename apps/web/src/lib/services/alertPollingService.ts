/**
 * Alert Polling Service - Polls for pending timer alerts
 * 
 * Implements alert recovery mechanism:
 * - Regular polling for pending alerts (every 10s)
 * - Tracks shown alerts to prevent duplicates
 * - Visibility-aware pausing
 * - Automatic recovery on reconnection
 */

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
  consecutiveFailures: number;  // Track consecutive failures for degradation detection
  degradedAt: number | null;    // Timestamp when system became degraded (for debug)
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
  private lastSuccessfulData: AlertData[] | null = null;  // Fallback data for graceful degradation

  constructor(config?: Partial<AlertPollingConfig>) {
    this.config = {
      interval: 10000,      // 10 seconds
      jitterRange: 1000,    // ±1 second random jitter
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

    // Get API base URL from environment
    this.apiBaseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
  }

  /**
   * Start polling for pending alerts
   */
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

    // Start first poll immediately
    this.poll();

    // Setup visibility change listener
    this.setupVisibilityListener();
  }

  /**
   * Stop polling
   */
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

  /**
   * Pause polling (e.g., when tab is hidden)
   */
  pause(): void {
    if (!this.state.isPolling) return;

    this.state.isPaused = true;
    if (this.state.timeoutId !== null) {
      clearTimeout(this.state.timeoutId);
      this.state.timeoutId = null;
    }

    console.log('[AlertPolling] Paused alert polling');
  }

  /**
   * Resume polling (e.g., when tab becomes visible)
   */
  resume(): void {
    if (!this.state.isPolling || !this.state.isPaused) return;

    this.state.isPaused = false;
    console.log('[AlertPolling] Resumed alert polling');

    // Poll immediately on resume to get fresh alerts
    this.poll();
  }

  /**
   * Acknowledge an alert
   */
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

  /**
   * Perform a single poll request for pending alerts
   */
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
        
        // Reset error counters on success
        this.state.errorCount = 0;
        this.state.consecutiveFailures = 0;
        
        // Clear degraded state if recovered
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

    // Schedule next poll
    this.scheduleNextPoll();
  }

  /**
   * Handle received alerts
   */
  private handleAlerts(alerts: AlertData[]): void {
    // Store successful data for fallback
    this.lastSuccessfulData = alerts;

    if (alerts.length === 0) {
      return;
    }

    console.log('[AlertPolling] Received alerts', { count: alerts.length });

    // Process each alert
    for (const alert of alerts) {
      const alertKey = `${alert.timer_id}-${alert.alert_minutes}`;

      // Skip if already shown
      if (this.state.shownAlerts.has(alertKey)) {
        continue;
      }

      // Mark as shown
      this.state.shownAlerts.add(alertKey);

      // Notify callback
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

  /**
   * Handle polling error
   */
  private handleError(error: Error): void {
    this.state.errorCount++;
    this.state.consecutiveFailures++;

    const FAILURE_THRESHOLD = 2;

    // Log diferenciado: debug para transient, warn para persistent
    if (this.state.consecutiveFailures === 1) {
      console.debug('[AlertPolling] Transient failure', {
        error: error.message,
        errorCount: this.state.errorCount
      });
    } else if (this.state.consecutiveFailures >= FAILURE_THRESHOLD) {
      // Mark system as degraded
      if (this.state.degradedAt === null) {
        this.state.degradedAt = Date.now();
      }
      
      console.warn('[AlertPolling] Persistent failure - system degraded', {
        error: error.message,
        consecutiveFailures: this.state.consecutiveFailures,
        errorCount: this.state.errorCount,
        degradedForSeconds: Math.round((Date.now() - this.state.degradedAt) / 1000)
      });

      // Graceful degradation: use last successful data if available
      if (this.lastSuccessfulData && this.lastSuccessfulData.length > 0) {
        console.log('[AlertPolling] Using fallback data (last successful response)');
        this.handleAlerts(this.lastSuccessfulData);
      }
    }

    // Notify error callback
    if (this.onError) {
      this.onError(error);
    }

    // Stop polling after too many errors
    if (this.state.errorCount >= 10) {
      console.error('[AlertPolling] Too many errors, stopping alert polling');
      this.stop();
    }
  }

  /**
   * Schedule next poll with jitter
   */
  private scheduleNextPoll(): void {
    if (!this.state.isPolling || this.state.isPaused) {
      return;
    }

    // Add random jitter to prevent thundering herd
    const jitter = (Math.random() - 0.5) * this.config.jitterRange;
    const delay = Math.max(0, this.config.interval + jitter);

    this.state.timeoutId = window.setTimeout(() => {
      this.poll();
    }, delay);
  }

  /**
   * Setup visibility change listener for pause/resume
   */
  private setupVisibilityListener(): void {
    const handleVisibilityChange = () => {
      if (document.hidden) {
        this.pause();
      } else {
        this.resume();
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);

    // Cleanup on stop
    const originalStop = this.stop.bind(this);
    this.stop = () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      originalStop();
    };
  }

  /**
   * Get authentication token from localStorage
   */
  private getToken(): string | null {
    try {
      return localStorage.getItem('auth_token');
    } catch (error) {
      console.error('[AlertPolling] Error getting token', error);
      return null;
    }
  }

  /**
   * Get current polling state (for debugging)
   */
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

// Export singleton instance
export const alertPollingService = new AlertPollingService();
