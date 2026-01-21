/**
 * Timer Polling Service - Adaptive polling with ETag caching
 * 
 * Implements Hybrid Intelligent Polling pattern:
 * - Adaptive interval (5s-30s) based on data freshness
 * - ETag caching for bandwidth optimization
 * - Visibility-aware pausing
 * - Exponential backoff on errors
 * - Jitter to prevent thundering herd
 * 
 * Clean Architecture: Uses getApiUrl() for dynamic API URL resolution.
 */

import { getApiUrl } from '$lib/utils/api-config';

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
  consecutiveFailures: number;
  degradedAt: number | null;
  timeoutId: number | null;
}

type TimerData = any;

export class TimerPollingService {
  private config: PollingConfig;
  private state: PollingState;
  private onUpdate: ((timers: TimerData[]) => void) | null = null;
  private onError: ((error: Error) => void) | null = null;
  private apiBaseUrl: string;
  private sucursalId: string | null = null;
  private lastSuccessfulData: TimerData[] | null = null;

  constructor(config?: Partial<PollingConfig>) {
    this.config = {
      minInterval: 5000,
      maxInterval: 30000,
      initialInterval: 5000,
      backoffMultiplier: 1.5,
      jitterRange: 1000,
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

    // Get API base URL using dynamic configuration (Clean Architecture)
    // This handles development (localhost) and production (same-origin) correctly
    this.apiBaseUrl = getApiUrl();
  }

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
    this.onUpdate = null;
    this.onError = null;

    console.log('[TimerPolling] Stopped polling');
  }

  pause(): void {
    if (!this.state.isPolling) return;

    this.state.isPaused = true;
    if (this.state.timeoutId !== null) {
      clearTimeout(this.state.timeoutId);
      this.state.timeoutId = null;
    }

    console.log('[TimerPolling] Paused polling');
  }

  resume(): void {
    if (!this.state.isPolling || !this.state.isPaused) return;

    this.state.isPaused = false;
    console.log('[TimerPolling] Resumed polling');
    this.poll();
  }

  async forcePoll(): Promise<void> {
    if (!this.state.isPolling) return;

    if (this.state.timeoutId !== null) {
      clearTimeout(this.state.timeoutId);
      this.state.timeoutId = null;
    }

    this.state.currentInterval = this.config.minInterval;
    this.state.consecutiveUnchanged = 0;

    await this.poll();
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

      const url = new URL(`${this.apiBaseUrl}/timers/active`);
      if (this.sucursalId) {
        url.searchParams.set('sucursal_id', this.sucursalId);
      }

      const headers: Record<string, string> = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      };

      if (this.state.lastETag) {
        headers['If-None-Match'] = this.state.lastETag;
      }

      const response = await fetch(url.toString(), {
        method: 'GET',
        headers
      });

      if (response.status === 304) {
        this.handleUnchangedData();
      } else if (response.ok) {
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

      this.state.errorCount = 0;
      this.state.consecutiveFailures = 0;
      
      if (this.state.degradedAt !== null) {
        const recoveryTime = Date.now() - this.state.degradedAt;
        console.log(`[TimerPolling] System recovered after ${Math.round(recoveryTime / 1000)}s`);
        this.state.degradedAt = null;
      }

    } catch (error) {
      this.handleError(error as Error);
    }

    this.scheduleNextPoll();
  }

  private handleUnchangedData(): void {
    this.state.consecutiveUnchanged++;

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

  private handleChangedData(timers: TimerData[]): void {
    this.state.currentInterval = this.config.minInterval;
    this.state.consecutiveUnchanged = 0;
    this.lastSuccessfulData = timers;

    console.log('[TimerPolling] Data changed (200)', {
      timersCount: timers.length,
      nextInterval: this.state.currentInterval
    });

    if (this.onUpdate) {
      this.onUpdate(timers);
    }
  }

  private handleError(error: Error): void {
    this.state.errorCount++;
    this.state.consecutiveFailures++;

    const FAILURE_THRESHOLD = 2;

    if (this.state.consecutiveFailures === 1) {
      console.debug('[TimerPolling] Transient failure', {
        error: error.message,
        errorCount: this.state.errorCount
      });
    } else if (this.state.consecutiveFailures >= FAILURE_THRESHOLD) {
      if (this.state.degradedAt === null) {
        this.state.degradedAt = Date.now();
      }
      
      console.warn('[TimerPolling] Persistent failure - system degraded', {
        error: error.message,
        consecutiveFailures: this.state.consecutiveFailures,
        errorCount: this.state.errorCount,
        degradedForSeconds: Math.round((Date.now() - this.state.degradedAt) / 1000)
      });

      if (this.lastSuccessfulData && this.onUpdate) {
        console.log('[TimerPolling] Using fallback data (last successful response)');
        this.onUpdate(this.lastSuccessfulData);
      }
    }

    this.state.currentInterval = Math.min(
      this.config.initialInterval * Math.pow(2, this.state.errorCount - 1),
      this.config.maxInterval
    );

    if (this.onError) {
      this.onError(error);
    }

    if (this.state.errorCount >= 10) {
      console.error('[TimerPolling] Too many errors, stopping polling');
      this.stop();
    }
  }

  private scheduleNextPoll(): void {
    if (!this.state.isPolling || this.state.isPaused) {
      return;
    }

    const jitter = (Math.random() - 0.5) * this.config.jitterRange;
    const delay = Math.max(0, this.state.currentInterval + jitter);

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
      console.error('[TimerPolling] Error getting token', error);
      return null;
    }
  }

  getState(): Readonly<PollingState> {
    return { ...this.state };
  }
}

export const timerPollingService = new TimerPollingService();
