/**
 * Metrics store for dashboard analytics.
 * 
 * Manages state for sales, stock, and services reports.
 * Provides reactive updates for dashboard components.
 */
import { writable, derived, get } from "svelte/store";
import type { Writable } from "svelte/store";

// Types for metrics reports
export interface SalesReport {
  total_revenue_cents: number;
  average_transaction_value_cents: number;
  sales_count: number;
  revenue_by_type: Record<string, number>;
  revenue_by_sucursal: Record<string, number>;
  revenue_by_payment_method: Record<string, number>;
  period: {
    start_date: string;
    end_date: string;
  };
}

export interface StockReport {
  low_stock_alerts: Array<{
    product_id: string;
    product_name: string;
    stock_qty: number;
    threshold_alert_qty: number;
    sucursal_id: string;
  }>;
  total_products: number;
  total_stock_value_cents: number;
  alerts_count: number;
}

export interface ServicesReport {
  active_timers_count: number;
  total_services: number;
  services_by_sucursal: Record<string, number>;
}

export interface SalesPrediction {
  forecast: Array<{
    date: string;
    predicted_revenue_cents: number;
    predicted_count: number;
  }>;
  confidence: "high" | "medium" | "low";
  method: string;
  historical_avg_revenue_cents?: number;
  historical_avg_count?: number;
  trend_factor?: number;
}

export interface CapacityPrediction {
  forecast: Array<{
    date: string;
    predicted_active_timers: number;
    utilization_rate: number;
  }>;
  confidence: "high" | "medium" | "low";
  method: string;
  historical_avg_timers?: number;
  total_capacity?: number;
}

export interface StockPrediction {
  reorder_suggestions: Array<{
    product_id: string;
    product_name: string;
    current_stock: number;
    predicted_daily_usage: number;
    days_until_out_of_stock: number;
    recommended_reorder_qty: number;
    threshold_alert_qty: number;
  }>;
  confidence: "high" | "medium" | "low";
  method: string;
}

export interface PredictionsState {
  sales: SalesPrediction | null;
  capacity: CapacityPrediction | null;
  stock: StockPrediction | null;
  generatedAt: number | null;
  forecastDays: number;
  predictionInProgress: boolean;
  error: string | null;
}

export interface MetricsState {
  sales: SalesReport | null;
  stock: StockReport | null;
  services: ServicesReport | null;
  lastRefresh: number | null;
  refreshInProgress: boolean;
  refreshCount: number;
  error: string | null;
  predictions: PredictionsState;
}

const initialPredictionsState: PredictionsState = {
  sales: null,
  capacity: null,
  stock: null,
  generatedAt: null,
  forecastDays: 7,
  predictionInProgress: false,
  error: null,
};

const initialState: MetricsState = {
  sales: null,
  stock: null,
  services: null,
  lastRefresh: null,
  refreshInProgress: false,
  refreshCount: 0,
  error: null,
  predictions: initialPredictionsState,
};

// Main metrics store
export const metricsStore: Writable<MetricsState> = writable(initialState);

/**
 * Update sales report in store.
 */
export function updateSales(sales: SalesReport): void {
  metricsStore.update((state) => ({
    ...state,
    sales,
    lastRefresh: Date.now(),
    error: null,
  }));
}

/**
 * Update stock report in store.
 */
export function updateStock(stock: StockReport): void {
  metricsStore.update((state) => ({
    ...state,
    stock,
    error: null,
  }));
}

/**
 * Update services report in store.
 */
export function updateServices(services: ServicesReport): void {
  metricsStore.update((state) => ({
    ...state,
    services,
    error: null,
  }));
}

/**
 * Update all metrics at once (from refresh endpoint).
 */
export function updateAllMetrics(
  sales: SalesReport,
  stock: StockReport,
  services: ServicesReport
): void {
  metricsStore.update((state) => ({
    ...state,
    sales,
    stock,
    services,
    lastRefresh: Date.now(),
    refreshInProgress: false,
    refreshCount: state.refreshCount + 1,
    error: null,
  }));
}

/**
 * Set refresh in progress state.
 */
export function setRefreshInProgress(inProgress: boolean): void {
  metricsStore.update((state) => ({
    ...state,
    refreshInProgress: inProgress,
  }));
}

/**
 * Set error state.
 */
export function setError(error: string | null): void {
  metricsStore.update((state) => ({
    ...state,
    error,
    refreshInProgress: false,
  }));
}

/**
 * Reset refresh count (useful for new sessions).
 */
export function resetRefreshCount(): void {
  metricsStore.update((state) => ({
    ...state,
    refreshCount: 0,
  }));
}

/**
 * Get current metrics state.
 */
export function getMetricsState(): MetricsState {
  return get(metricsStore);
}

/**
 * Update predictions in store.
 */
export function updatePredictions(
  predictions: {
    sales?: SalesPrediction;
    capacity?: CapacityPrediction;
    stock?: StockPrediction;
  },
  forecastDays: number
): void {
  metricsStore.update((state) => ({
    ...state,
    predictions: {
      ...state.predictions,
      ...predictions,
      generatedAt: Date.now(),
      forecastDays,
      predictionInProgress: false,
      error: null,
    },
  }));
}

/**
 * Set prediction in progress state.
 */
export function setPredictionInProgress(inProgress: boolean): void {
  metricsStore.update((state) => ({
    ...state,
    predictions: {
      ...state.predictions,
      predictionInProgress: inProgress,
    },
  }));
}

/**
 * Set prediction error state.
 */
export function setPredictionError(error: string | null): void {
  metricsStore.update((state) => ({
    ...state,
    predictions: {
      ...state.predictions,
      error,
      predictionInProgress: false,
    },
  }));
}

/**
 * Derived store for formatted revenue.
 */
export const formattedRevenue = derived(metricsStore, ($metrics) => {
  if (!$metrics.sales) return "$0.00";
  return `$${($metrics.sales.total_revenue_cents / 100).toFixed(2)}`;
});

/**
 * Derived store for formatted ATV (Average Transaction Value).
 */
export const formattedATV = derived(metricsStore, ($metrics) => {
  if (!$metrics.sales) return "$0.00";
  return `$${($metrics.sales.average_transaction_value_cents / 100).toFixed(2)}`;
});

/**
 * Derived store for time since last refresh.
 */
export const timeSinceLastRefresh = derived(metricsStore, ($metrics) => {
  if (!$metrics.lastRefresh) return null;
  const seconds = Math.floor((Date.now() - $metrics.lastRefresh) / 1000);
  if (seconds < 60) return `${seconds}s ago`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  return `${hours}h ago`;
});

