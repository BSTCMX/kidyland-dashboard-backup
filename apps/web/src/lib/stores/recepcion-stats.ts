/**
 * Reception stats store - Statistics for recepcion module.
 * 
 * Used by recepcion module.
 * Loads reception-specific statistics from backend.
 */
import { writable } from "svelte/store";
import type { Writable } from "svelte/store";
import { get, createPromiseGuard, REQUEST_TIMEOUTS } from "@kidyland/utils";

export interface RecepcionStats {
  date: string;
  sucursal_id: string;
  sales: {
    total_revenue_cents: number;
    total_count: number;
    service_count: number;
    package_count: number;
  };
  tickets: {
    generated_today: number;
  };
  peak_hours: Array<{
    hour: number;
    sales_count: number;
  }>;
  active_timers: number;
  generated_at: string;
}

export interface RecepcionStatsState {
  stats: RecepcionStats | null;
  loading: boolean;
  error: string | null;
}

const initialState: RecepcionStatsState = {
  stats: null,
  loading: false,
  error: null,
};

export const recepcionStatsStore: Writable<RecepcionStatsState> = writable(initialState);

// Promise guard to prevent concurrent fetch operations
const fetchGuard = createPromiseGuard<RecepcionStats>();

/**
 * Fetch reception statistics for a sucursal.
 * 
 * Prevents concurrent fetch operations to avoid race conditions.
 * If a fetch is already in progress, returns the existing promise.
 * Uses configurable timeout from REQUEST_TIMEOUTS.STATS.
 */
export async function fetchRecepcionStats(
  sucursalId: string,
  targetDate?: string
): Promise<RecepcionStats> {
  return fetchGuard.execute(async () => {
    recepcionStatsStore.update((state) => ({ ...state, loading: true, error: null }));

    try {
      let url = `/reports/recepcion?sucursal_id=${sucursalId}`;
      if (targetDate) {
        url += `&date=${targetDate}`;
      }
      
      // Use configurable timeout from constants
      const stats = await get<RecepcionStats>(url, {
        timeout: REQUEST_TIMEOUTS.STATS,
      });
      
      recepcionStatsStore.update((state) => ({
        ...state,
        stats,
        loading: false,
        error: null,
      }));
      
      return stats;
    } catch (error: any) {
      // Handle timeout errors with user-friendly message
      const errorMessage = error.isTimeout
        ? "Request timeout - please check your connection and try again"
        : error.message || "Error loading reception statistics";
      
      recepcionStatsStore.update((state) => ({
        ...state,
        error: errorMessage,
        loading: false,
      }));
      
      throw error;
    }
  });
}

