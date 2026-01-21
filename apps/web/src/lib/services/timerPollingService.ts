/**
 * Timer Polling Service - Adaptive polling with ETag caching
 * 
 * Implements Hybrid Intelligent Polling pattern:
 * - Adaptive interval (5s-30s) based on data freshness
 * - ETag caching for bandwidth optimization
 * - Visibility-aware pausing
 * - Exponential backoff on errors
 * - Jitter to prevent thundering herd
 */

interface PollingConfig {
  minInterval: number;
  maxInterval: number;
  initialInterval: number;
  backoffMultiplier: number;
  jitterRange: number;
}

interface PollingState {
  isPolling: boolean;
  isPaused: boolean;
  currentInterval: number;
  lastETag: string | null;
  consecutiveUnchanged: number;
  errorCount: number;
  consecutiveFailures: number;  // Track consecutive failures for degradation detection
  degradedAt: number | null;    // Timestamp when system became degraded (for debug)
  timeoutId: number | null;
}

type TimerData = any; // Replace with actual timer type

export class TimerPollingService {
  private config: PollingConfig;
  private state: PollingState;
  private onUpdate: ((timers: TimerData[]) => void) | null = null;
  private onError: ((error: Error) => void) | null = null;
  private apiBaseUrl: string;
  private sucursalId: string | null = null;
  private lastSuccessfulData: TimerData[] | null = null;  // Fallback data for graceful degradation

  constructor(config?: Partial<PollingConfig>) {
    this.config = {
      minInterval: 5000,        // 5 seconds minimum
      maxInterval: 30000,       // 30 seconds maximum
      initialInterval: 5000,    // Start at 5 seconds
      backoffMultiplier: 1.5,   // Increase by 50% when no changes
      jitterRange: 1000,        // ±1 second random jitter
      ...config
    };

    this.state = {
      isPolling: false,
      isPaused: false,
      currentInterval: this.config.initialInterval,
      lastETag: null,
      consecutiveUnchanged: 0,
      errorCount: 0,
      consecutiveFailures: 0,
      degradedAt: null,
      timeoutId: null
    };

    // Get API base URL from environment
    this.apiBaseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
  }

  /**
   * Start polling for timer updates
   */
  start(sucursalId: string, onUpdate: (timers: TimerData[]) => void, onError?: (error: Error) => void): void {
    if (this.state.isPolling) {
      console.warn('[TimerPolling] Already polling, stopping previous instance');
      this.stop();
    }

    this.sucursalId = sucursalId;
    this.onUpdate = onUpdate;
    this.onError = onError || null;
    this.state.isPolling = true;
    this.state.isPaused = false;
    this.state.currentInterval = this.config.initialInterval;
    this.state.consecutiveUnchanged = 0;
    this.state.errorCount = 0;
    this.state.consecutiveFailures = 0;
    this.state.degradedAt = null;

    console.log('[TimerPolling] Starting adaptive polling', {
      sucursalId,
      initialInterval: this.state.currentInterval
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
    this.onUpdate = null;
    this.onError = null;

    console.log('[TimerPolling] Stopped polling');
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

    console.log('[TimerPolling] Paused polling');
  }

  /**
   * Resume polling (e.g., when tab becomes visible)
   */
  resume(): void {
    if (!this.state.isPolling || !this.state.isPaused) return;

    this.state.isPaused = false;
    console.log('[TimerPolling] Resumed polling');

    // Poll immediately on resume to get fresh data
    this.poll();
  }

  /**
   * Force an immediate poll (e.g., after user action)
   */
  async forcePoll(): Promise<void> {
    if (!this.state.isPolling) return;

    // Cancel scheduled poll
    if (this.state.timeoutId !== null) {
      clearTimeout(this.state.timeoutId);
      this.state.timeoutId = null;
    }

    // Reset interval to minimum for responsive updates
    this.state.currentInterval = this.config.minInterval;
    this.state.consecutiveUnchanged = 0;

    // Poll immediately
    await this.poll();
  }

  /**
   * Perform a single poll request
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

      const url = new URL(`${this.apiBaseUrl}/timers/active`);
      if (this.sucursalId) {
        url.searchParams.set('sucursal_id', this.sucursalId);
      }

      const headers: Record<string, string> = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      };

      // Add ETag header if we have one
      if (this.state.lastETag) {
        headers['If-None-Match'] = this.state.lastETag;
      }

      const response = await fetch(url.toString(), {
        method: 'GET',
        headers
      });

      if (response.status === 304) {
        // Not Modified - data hasn't changed
        this.handleUnchangedData();
      } else if (response.ok) {
        // Data changed - update ETag and process
        const newETag = response.headers.get('ETag');
        if (newETag) {
          this.state.lastETag = newETag;
        }

        const timers = await response.json();
        this.handleChangedData(timers);
      } else if (response.status === 401) {
        throw new Error('Authentication failed');
      } else {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      // Reset error counters on success
      this.state.errorCount = 0;
      this.state.consecutiveFailures = 0;
      
      // Clear degraded state if recovered
      if (this.state.degradedAt !== null) {
        const recoveryTime = Date.now() - this.state.degradedAt;
        console.log(`[TimerPolling] System recovered after ${Math.round(recoveryTime / 1000)}s`);
        this.state.degradedAt = null;
      }

    } catch (error) {
      this.handleError(error as Error);
    }

    // Schedule next poll
    this.scheduleNextPoll();
  }

  /**
   * Handle unchanged data (304 response)
   */
  private handleUnchangedData(): void {
    this.state.consecutiveUnchanged++;

    // Adaptive interval: increase when data is stable
    if (this.state.consecutiveUnchanged >= 2) {
      this.state.currentInterval = Math.min(
        this.state.currentInterval * this.config.backoffMultiplier,
        this.config.maxInterval
      );
    }

    console.log('[TimerPolling] Data unchanged (304)', {
      consecutiveUnchanged: this.state.consecutiveUnchanged,
      nextInterval: this.state.currentInterval
    });
  }

  /**
   * Handle changed data (200 response)
   */
  private handleChangedData(timers: TimerData[]): void {
    // Reset interval to minimum when changes detected
    this.state.currentInterval = this.config.minInterval;
    this.state.consecutiveUnchanged = 0;

    // Store successful data for fallback
    this.lastSuccessfulData = timers;

    console.log('[TimerPolling] Data changed (200)', {
      timersCount: timers.length,
      nextInterval: this.state.currentInterval
    });

    // Notify callback
    if (this.onUpdate) {
      this.onUpdate(timers);
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
      console.debug('[TimerPolling] Transient failure', {
        error: error.message,
        errorCount: this.state.errorCount
      });
    } else if (this.state.consecutiveFailures >= FAILURE_THRESHOLD) {
      // Mark system as degraded
      if (this.state.degradedAt === null) {
        this.state.degradedAt = Date.now();
      }
      
      console.warn('[TimerPolling] Persistent failure - system degraded', {
        error: error.message,
        consecutiveFailures: this.state.consecutiveFailures,
        errorCount: this.state.errorCount,
        degradedForSeconds: Math.round((Date.now() - this.state.degradedAt) / 1000)
      });

      // Graceful degradation: use last successful data if available
      if (this.lastSuccessfulData && this.onUpdate) {
        console.log('[TimerPolling] Using fallback data (last successful response)');
        this.onUpdate(this.lastSuccessfulData);
      }
    }

    // Exponential backoff on errors
    this.state.currentInterval = Math.min(
      this.config.initialInterval * Math.pow(2, this.state.errorCount - 1),
      this.config.maxInterval
    );

    // Notify error callback
    if (this.onError) {
      this.onError(error);
    }

    // Stop polling after too many errors
    if (this.state.errorCount >= 10) {
      console.error('[TimerPolling] Too many errors, stopping polling');
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
    const delay = Math.max(0, this.state.currentInterval + jitter);

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
      console.error('[TimerPolling] Error getting token', error);
      return null;
    }
  }

  /**
   * Get current polling state (for debugging)
   */
  getState(): Readonly<PollingState> {
    return { ...this.state };
  }
}

// Export singleton instance
export const timerPollingService = new TimerPollingService();
