/**
 * Metrics store for dashboard analytics.
 * 
 * Manages state for sales, stock, and services reports.
 * Provides reactive updates for dashboard components.
 */
import { writable, derived, get as getStore } from "svelte/store";
import type { Writable } from "svelte/store";
import { get } from "@kidyland/utils/api";
import { getProductsBroadcastChannel } from "$lib/utils/broadcast-channel";
import type { Product } from "$lib/types";

// Types for metrics reports
export interface SalesReport {
  total_revenue_cents: number;
  average_transaction_value_cents: number;
  sales_count: number;
  unique_customers?: number; // Optional for backward compatibility
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
  active_timers?: number;  // Alias for active_timers_count
  total_services: number;
  services_by_sucursal: Record<string, number>;
  tickets_generated?: number;
  peak_hours?: Array<{
    hour: number;
    sales_count: number;
  }>;
  total_revenue_cents?: number;
  sales?: {
    service_count: number;
    package_count: number;
    total_count: number;
  };
}

export interface PeakHourData {
  hour: number;
  sales_count: number;
  revenue_cents: number;
}

export interface TopProductData {
  product_id: string;
  product_name: string;
  quantity_sold: number;
  revenue_cents: number;
}

export interface TopServiceData {
  service_id: string;
  service_name: string;
  usage_count: number;
  avg_duration_minutes: number;
}

export interface PeakHoursReport {
  date: string;
  sucursal_id?: string;
  peak_hours: PeakHourData[];
  busiest_hour: {
    hour: number;
    sales_count: number;
  };
}

export interface TopProductsReport {
  period_days: number;
  sucursal_id?: string;
  top_products: TopProductData[];
}

export interface TopServicesReport {
  period_days: number;
  sucursal_id?: string;
  top_services: TopServiceData[];
}

export interface TopCustomerData {
  child_name: string;
  child_age: number | null;
  visit_count: number;
  total_revenue_cents: number;
}

export interface TopCustomersReport {
  period_days: number;
  sucursal_id?: string;
  top_customers: TopCustomerData[];
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

export interface SalesByTypePrediction {
  forecast: {
    products: Array<{
      date: string;
      predicted_revenue_cents: number;
      predicted_count: number;
    }>;
    services: Array<{
      date: string;
      predicted_revenue_cents: number;
      predicted_count: number;
    }>;
    packages: Array<{
      date: string;
      predicted_revenue_cents: number;
      predicted_count: number;
    }>;
  };
  confidence: "high" | "medium" | "low";
  method?: string;
}

export interface PeakHoursPrediction {
  forecast: Array<{
    date: string;
    predicted_peak_hours: Array<{
      hour: number;
      expected_activity: number;
    }>;
    busiest_hour: {
      hour: number;
      expected_activity: number;
    } | null;
  }>;
  confidence: "high" | "medium" | "low";
  method?: string;
}

export interface BusiestDaysPrediction {
  forecast: Array<{
    date: string;
    day_of_week: string;
    predicted_activity: number;
    rank: number;
  }>;
  confidence: "high" | "medium" | "low";
  method?: string;
}

export interface PredictionsState {
  sales: SalesPrediction | null;
  capacity: CapacityPrediction | null;
  stock: StockPrediction | null;
  sales_by_type: SalesByTypePrediction | null;
  peak_hours: PeakHoursPrediction | null;
  busiest_days: BusiestDaysPrediction | null;
  generatedAt: number | null;
  forecastDays: number;
  predictionInProgress: boolean;
  error: string | null;
}

export interface TopCustomersByModule {
  period_days: number;
  sucursal_id: string | null;
  module: string | null;
  recepcion: {
    top_customers: Array<{
      customer_name: string;
      child_age?: number | null;
      visit_count: number;
      total_revenue_cents: number;
    }>;
  };
  kidibar: {
    top_customers: Array<{
      customer_name: string;
      visit_count: number;
      total_revenue_cents: number;
    }>;
  };
}

export interface MetricsState {
  sales: SalesReport | null;
  stock: StockReport | null;
  services: ServicesReport | null;
  peak_hours: PeakHoursReport | null;
  top_products: TopProductsReport | null;
  top_services: TopServicesReport | null;
  top_customers: TopCustomersReport | null;
  top_customers_by_module: TopCustomersByModule | null;
  lastRefresh: number | null;
  refreshInProgress: boolean;
  refreshCount: number;
  error: string | null;
  predictions: PredictionsState;
  hasInitialData: boolean; // Flag to track if data has been loaded at least once
}

const initialPredictionsState: PredictionsState = {
  sales: null,
  capacity: null,
  stock: null,
  sales_by_type: null,
  peak_hours: null,
  busiest_days: null,
  generatedAt: null,
  forecastDays: 7,
  predictionInProgress: false,
  error: null,
};

const initialState: MetricsState = {
  sales: null,
  stock: null,
  services: null,
  peak_hours: null,
  top_products: null,
  top_services: null,
  top_customers: null,
  top_customers_by_module: null,
  lastRefresh: null,
  refreshInProgress: false,
  refreshCount: 0,
  error: null,
  predictions: {
    ...initialPredictionsState,
    sales_by_type: null,
    peak_hours: null,
    busiest_days: null,
  },
  hasInitialData: false, // No data loaded initially - user must click RefreshButton
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
/**
 * Update all metrics at once (from refresh endpoint).
 * 
 * Uses explicit undefined checks to preserve state only when new data is not provided,
 * following the "Explicit Update with Null Safety" pattern.
 */
export function updateAllMetrics(
  sales: SalesReport,
  stock: StockReport,
  services: ServicesReport,
  peak_hours?: PeakHoursReport,
  top_products?: TopProductsReport,
  top_services?: TopServicesReport,
  top_customers?: TopCustomersReport
): void {
  metricsStore.update((state) => ({
    ...state,
    sales,
    stock,
    services,
    // Explicit undefined check: only update if new value is provided
    // This preserves previous state when backend doesn't return the field
    peak_hours: peak_hours !== undefined ? peak_hours : state.peak_hours,
    top_products: top_products !== undefined ? top_products : state.top_products,
    top_services: top_services !== undefined ? top_services : state.top_services,
    top_customers: top_customers !== undefined ? top_customers : state.top_customers,
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
  return getStore(metricsStore);
}

/**
 * Fetch top customers by module (segmented).
 * 
 * This function loads customers segmented by module (reception vs kidibar)
 * for the Admin Dashboard, providing a more comprehensive view than
 * the single top_customers_report which only shows reception customers.
 * 
 * @param sucursalId - Optional sucursal ID to filter by
 * @param days - Number of days to look back (default: 30)
 * @returns Promise that resolves when customers are loaded
 */
export async function fetchTopCustomersByModule(
  sucursalId?: string | null,
  days: number = 30
): Promise<void> {
  try {
    const params = new URLSearchParams();
    if (sucursalId) {
      params.append("sucursal_id", sucursalId);
    }
    params.append("days", days.toString());
    
    const response = await get<{
      period_days: number;
      sucursal_id: string | null;
      module: string | null;
      recepcion: {
        top_customers: Array<{
          customer_name: string;
          child_age?: number | null;
          visit_count: number;
          total_revenue_cents: number;
        }>;
      };
      kidibar: {
        top_customers: Array<{
          customer_name: string;
          visit_count: number;
          total_revenue_cents: number;
        }>;
      };
    }>(`/reports/customers/by-module?${params.toString()}`);
    
    // Store segmented customers data in a separate field for Admin Dashboard
    // We keep top_customers for backward compatibility
    metricsStore.update((state) => ({
      ...state,
      top_customers_by_module: response,
      error: null,
    }));
  } catch (error: any) {
    console.error("Error fetching top customers by module:", error);
    setError(error.message || "Error al cargar clientes segmentados");
  }
}

/**
 * Update predictions in store.
 */
export function updatePredictions(
  predictions: {
    sales?: SalesPrediction;
    capacity?: CapacityPrediction;
    stock?: StockPrediction;
    sales_by_type?: SalesByTypePrediction;
    peak_hours?: PeakHoursPrediction;
    busiest_days?: BusiestDaysPrediction;
  },
  forecastDays: number
): void {
  console.log("updatePredictions called with:", {
    has_sales: !!predictions.sales,
    has_capacity: !!predictions.capacity,
    has_stock: !!predictions.stock,
    has_sales_by_type: !!predictions.sales_by_type,
    has_peak_hours: !!predictions.peak_hours,
    has_busiest_days: !!predictions.busiest_days,
    forecastDays
  });
  
  metricsStore.update((state) => {
    const newState = {
      ...state,
      predictions: {
        ...state.predictions,
        ...predictions,
        generatedAt: Date.now(),
        forecastDays,
        predictionInProgress: false,
        error: null,
      },
    };
    
    // Log after update to verify
    console.log("Predictions after update:", {
      has_sales: !!newState.predictions.sales,
      has_capacity: !!newState.predictions.capacity,
      has_stock: !!newState.predictions.stock,
      has_sales_by_type: !!newState.predictions.sales_by_type,
      has_peak_hours: !!newState.predictions.peak_hours,
      has_busiest_days: !!newState.predictions.busiest_days,
    });
    
    return newState;
  });
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
 * 
 * Clean Architecture: Defensive programming with null checks.
 * Handles cases where sales or total_revenue_cents might be undefined.
 */
export const formattedRevenue = derived(metricsStore, ($metrics) => {
  if (!$metrics.sales) return "$0.00";
  const revenue = $metrics.sales.total_revenue_cents;
  if (revenue === undefined || revenue === null) return "$0.00";
  return `$${(revenue / 100).toFixed(2)}`;
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

// Throttle state for refreshMetrics
let lastRefreshTime = 0;
let isInitialLoad = true; // Flag to skip throttle on first load
const REFRESH_THROTTLE_MS = 2000; // Minimum 2 seconds between refreshes

/**
 * Refresh metrics from API (optional helper function).
 * 
 * Note: RefreshButton component handles refresh internally.
 * This function is provided for programmatic refresh if needed.
 * 
 * Includes throttling to prevent 429 errors from too many requests.
 * Skips throttle on initial load to allow immediate data fetching.
 */
/**
 * Refresh all metrics from the backend.
 * 
 * For daily metrics (sales, stock, services): uses today's date
 * For historical metrics (peak_hours, top_products, top_services): uses selected period
 * 
 * @param sucursalId - Optional sucursal ID to filter by
 * @param days - Optional number of days for historical metrics (default: 30)
 * @param skipThrottle - Optional flag to skip throttle (for initial load)
 */
export async function refreshMetrics(sucursalId?: string | null, days?: number, skipThrottle: boolean = false): Promise<void> {
  const { post } = await import("@kidyland/utils");
  
  // Get current state to check if refresh is in progress
  const currentState = getStore(metricsStore);
  
  // Prevent concurrent refreshes
  if (currentState.refreshInProgress) {
    throw new Error("Refresh already in progress. Please wait.");
  }

  // Throttle: prevent too frequent refreshes (min 2 seconds between)
  // Skip throttle on initial load or if explicitly requested
  const shouldSkipThrottle = skipThrottle || isInitialLoad;
  const now = Date.now();
  const timeSinceLastRefresh = now - lastRefreshTime;
  
  if (!shouldSkipThrottle && timeSinceLastRefresh < REFRESH_THROTTLE_MS) {
    const remainingMs = REFRESH_THROTTLE_MS - timeSinceLastRefresh;
    throw new Error(`Please wait ${Math.ceil(remainingMs / 1000)} second(s) before refreshing again.`);
  }
  
  setRefreshInProgress(true);
  setError(null);
  lastRefreshTime = now;
  
  try {
    const params = new URLSearchParams();
    if (sucursalId) {
      params.append("sucursal_id", sucursalId);
    }
    // Add days parameter for historical metrics if provided
    if (days !== undefined) {
      params.append("days", days.toString());
    }
    
    const response = await post<{
      success: boolean;
      message: string;
      metrics: {
        sales: SalesReport;
        stock: StockReport;
        services: ServicesReport;
        peak_hours?: PeakHoursReport;
        top_products?: TopProductsReport;
        top_services?: TopServicesReport;
      };
      elapsed_seconds: number;
      refresh_count: number;
      cache_invalidated: boolean;
    }>(`/reports/refresh${params.toString() ? `?${params.toString()}` : ""}`);
    
      if (response.success && response.metrics) {
        // Debug logging for peak_hours
        if (response.metrics.peak_hours) {
          console.debug("Peak hours received:", {
            date: response.metrics.peak_hours.date,
            sucursal_id: response.metrics.peak_hours.sucursal_id,
            peak_hours_count: response.metrics.peak_hours.peak_hours?.length || 0,
            busiest_hour: response.metrics.peak_hours.busiest_hour
          });
        } else {
          console.warn("Peak hours not in response:", Object.keys(response.metrics));
        }
        
        updateAllMetrics(
          response.metrics.sales,
          response.metrics.stock,
          response.metrics.services,
          response.metrics.peak_hours,
          response.metrics.top_products,
          response.metrics.top_services
        );
        
        // Also fetch segmented customers by module (non-blocking)
        fetchTopCustomersByModule(sucursalId, days).catch((error) => {
          console.error("Error fetching customers by module:", error);
          // Don't throw - this is supplementary data
        });
        
        // Mark that initial data has been loaded
        metricsStore.update((state) => ({
          ...state,
          hasInitialData: true,
        }));
        
        // Reset initial load flag after first successful refresh
        if (isInitialLoad) {
          isInitialLoad = false;
        }
    } else {
      throw new Error(response.message || "Error al actualizar métricas");
    }
  } catch (error: any) {
    console.error("Error refreshing metrics:", error);
    setError(error.message || "Error al actualizar métricas");
    // Reset initial load flag even on error to prevent infinite retries
    if (isInitialLoad) {
      isInitialLoad = false;
    }
  } finally {
    setRefreshInProgress(false);
  }
}

/**
 * Initialize BroadcastChannel listeners for real-time stock alerts updates.
 * Listens for product updates and refreshes stock metrics when products reach threshold.
 */
function initializeStockAlertsListeners() {
  // Only initialize in browser environment
  if (typeof window === 'undefined') {
    return;
  }

  const broadcastChannel = getProductsBroadcastChannel();
  
  // Listen for product updates - if a product reaches threshold, refresh stock metrics
  broadcastChannel.on('product-updated', async (product: Product) => {
    // Check if product has reached threshold (stock <= threshold_alert_qty)
    if (product.stock_qty !== undefined && 
        product.threshold_alert_qty !== undefined &&
        product.stock_qty <= product.threshold_alert_qty) {
      
      // Product reached threshold - refresh stock metrics
      // Use skipThrottle to allow immediate refresh for critical alerts
      try {
        const currentState = getStore(metricsStore);
        const sucursalId = currentState.stock?.low_stock_alerts?.[0]?.sucursal_id || undefined;
        
        // Refresh stock metrics (non-blocking)
        refreshMetrics(sucursalId, undefined, true).catch((error) => {
          console.warn('[StockAlerts] Error refreshing metrics after product threshold reached:', error);
          // Don't throw - this is a background update
        });
      } catch (error) {
        console.warn('[StockAlerts] Error checking stock metrics after product update:', error);
      }
    }
  });
  
  // Listen for explicit stock alerts updates
  broadcastChannel.on('stock-alerts-updated', async (data: { sucursal_id?: string }) => {
    try {
      const sucursalId = data?.sucursal_id;
      // Refresh stock metrics when explicitly notified
      refreshMetrics(sucursalId, undefined, true).catch((error) => {
        console.warn('[StockAlerts] Error refreshing metrics after stock-alerts-updated event:', error);
      });
    } catch (error) {
      console.warn('[StockAlerts] Error handling stock-alerts-updated event:', error);
    }
  });
}

// Initialize listeners on module load (browser only)
if (typeof window !== 'undefined') {
  initializeStockAlertsListeners();
}

