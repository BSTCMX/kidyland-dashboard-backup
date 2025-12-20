/**
 * KidiBar stats store - Statistics for KidiBar module.
 * 
 * Used by KidiBar module.
 * Loads KidiBar-specific statistics from backend.
 */
import { writable } from "svelte/store";
import type { Writable } from "svelte/store";
import { get, createPromiseGuard, REQUEST_TIMEOUTS } from "@kidyland/utils";

export interface KidibarStats {
  date: string;
  sucursal_id: string;
  sales: {
    total_revenue_cents: number;
    total_count: number;
    product_count: number;
    package_count: number;
  };
  stock_alerts: {
    low_stock_count: number;
    low_stock_products: Array<{
      product_id: string;
      product_name: string;
      stock_qty: number;
      threshold_alert_qty: number;
      price_cents: number;
    }>;
  };
  peak_hours: Array<{
    hour: number;
    sales_count: number;
  }>;
  generated_at: string;
}

export interface KidibarStatsState {
  stats: KidibarStats | null;
  loading: boolean;
  error: string | null;
}

const initialState: KidibarStatsState = {
  stats: null,
  loading: false,
  error: null,
};

export const kidibarStatsStore: Writable<KidibarStatsState> = writable(initialState);

// Promise guard to prevent concurrent fetch operations
const fetchGuard = createPromiseGuard<KidibarStats>();

/**
 * Fetch KidiBar statistics for a sucursal.
 * 
 * Prevents concurrent fetch operations to avoid race conditions.
 * If a fetch is already in progress, returns the existing promise.
 * Uses configurable timeout from REQUEST_TIMEOUTS.STATS.
 */
export async function fetchKidibarStats(
  sucursalId: string,
  targetDate?: string
): Promise<KidibarStats> {
  return fetchGuard.execute(async () => {
    kidibarStatsStore.update((state) => ({ ...state, loading: true, error: null }));

    try {
      let url = `/reports/kidibar?sucursal_id=${sucursalId}`;
      if (targetDate) {
        url += `&date=${targetDate}`;
      }
      
      // Use configurable timeout from constants
      const stats = await get<KidibarStats>(url, {
        timeout: REQUEST_TIMEOUTS.STATS,
      });
      
      kidibarStatsStore.update((state) => ({
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
        : error.message || "Error loading KidiBar statistics";
      
      kidibarStatsStore.update((state) => ({
        ...state,
        error: errorMessage,
        loading: false,
      }));
      
      throw error;
    }
  });
}



