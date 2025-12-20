/**
 * Reports store for advanced analytics and reporting.
 * 
 * Manages state for comprehensive reports with filters and comparisons.
 */
import { writable, derived } from "svelte/store";
import type { Writable } from "svelte/store";
import { get } from "@kidyland/utils/api";
import type { SalesReport, StockReport, ServicesReport } from "./metrics";

// Types for comparison reports
export interface ComparisonData {
  current: number;
  previous: number;
  change_percent: number;
  change_absolute: number;
  trend: "up" | "down" | "stable";
}

export interface ModuleComparison {
  recepcion: {
    revenue_cents: number;
    sales_count: number;
    atv_cents: number;
  };
  kidibar: {
    revenue_cents: number;
    sales_count: number;
    atv_cents: number;
  };
  total: {
    revenue_cents: number;
    sales_count: number;
    atv_cents: number;
  };
  participation: {
    recepcion_percent: number;
    kidibar_percent: number;
  };
}

export interface ArqueosReport {
  period: {
    start_date: string;
    end_date: string;
  };
  total_arqueos: number;
  total_system_cents: number;
  total_physical_cents: number;
  total_difference_cents: number;
  average_difference_cents: number;
  perfect_matches: number;
  discrepancies: number;
  discrepancy_rate: number;
  by_sucursal: Record<string, any>;
  recent_arqueos: Array<{
    id: string;
    date: string;
    system_total_cents: number;
    physical_count_cents: number;
    difference_cents: number;
    sucursal_id: string;
    created_at?: string | null;
  }>;
}

export interface CustomersByModuleReport {
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

export interface ForecastReport {
  forecast: Array<{
    date: string;
    predicted_revenue_cents: number;
    predicted_count: number;
    day_of_week?: string;
    day_of_week_factor?: number;
  }>;
  confidence: "high" | "medium" | "low";
  method: string;
  module?: string | null;
  historical_avg_revenue_cents?: number;
  historical_avg_count?: number;
  trend_factor?: number;
  historical_days?: number;
  day_of_week_adjustments?: Record<string, number>;
  outliers_removed?: number;
}

// Segmented predictions types (for Forecasting section)
export interface SegmentedPredictionsResponse {
  success: boolean;
  message: string;
  predictions: {
    recepcion?: {
      sales?: any;
      capacity?: any;
      stock?: any;
    };
    kidibar?: {
      sales?: any;
      capacity?: any;
      stock?: any;
    };
    total?: {
      sales?: any;
      capacity?: any;
      stock?: any;
    };
  };
  elapsed_seconds: number;
  overall_confidence: "high" | "medium" | "low";
  forecast_days: number;
  modules: string[];
}

// Executive Summary Types
export type InsightType = "opportunity" | "risk" | "trend" | "alert";
export type InsightPriority = "high" | "medium" | "low";
export type InsightCategory = "sales" | "inventory" | "services" | "arqueos" | "customers" | "forecasting";
export type HealthStatus = "excellent" | "good" | "warning" | "critical";
export type HealthTrend = "improving" | "stable" | "declining";

export interface Insight {
  type: InsightType;
  priority: InsightPriority;
  category: InsightCategory;
  title: string;
  description: string;
  impact: string;
  actionable: boolean;
  linkToSection?: string;
}

export interface ModuleKPIs {
  revenue: number;
  salesCount: number;
  atv: number;
  uniqueCustomers?: number;
  servicesActive?: number;
  stockAlerts?: number;
}

export interface FinancialKPIs {
  totalRevenue: number;
  revenueTrend: ComparisonData | null;
  projectedRevenue?: number;
  revenueByModule: {
    recepcion: number;
    kidibar: number;
    total: number;
  };
  atv: number;
  revenueGrowth?: number;
}

export interface OperationalKPIs {
  activeServices: number;
  utilizationRate: number;
  stockHealth: number; // % products not low stock
  arqueosAccuracy: number; // % perfect matches
  discrepancyRate: number;
}

export interface CustomerKPIs {
  uniqueCustomers: number;
  newCustomers: number;
  avgRevenuePerCustomer: number;
  customerGrowth: ComparisonData | null;
  topCustomersCount: number;
}

export interface ForecastProjection {
  next7Days: {
    projectedRevenue: number;
    projectedCount: number;
    confidence: "high" | "medium" | "low";
  };
  next30Days: {
    projectedRevenue: number;
    projectedCount: number;
    confidence: "high" | "medium" | "low";
  };
  overallConfidence: "high" | "medium" | "low";
}

export interface OverallHealth {
  score: number; // 0-100
  status: HealthStatus;
  trend: HealthTrend;
  breakdown: {
    financial: number;
    operational: number;
    inventory: number;
    cash: number;
    customer: number;
  };
}

export interface ExecutiveSummary {
  overallHealth: OverallHealth;
  financialKPIs: FinancialKPIs;
  operationalKPIs: OperationalKPIs;
  customerKPIs: CustomerKPIs;
  topInsights: Insight[];
  moduleBreakdown?: {
    recepcion: ModuleKPIs;
    kidibar: ModuleKPIs;
    comparison?: ModuleComparison;
  };
  forecastProjections?: ForecastProjection;
}

export interface ReportsState {
  // Current period reports
  sales: SalesReport | null;
  stock: StockReport | null;
  services: ServicesReport | null;
  
  // Comparison data
  salesComparison: ComparisonData | null;
  moduleComparison: ModuleComparison | null;
  
  // Additional reports
  arqueos: ArqueosReport | null;
  customers: CustomersByModuleReport | null;
  customersSummary: CustomersSummaryReport | null;
  forecast: ForecastReport | null;
  
  // Loading and error states
  loading: boolean;
  error: string | null;
  
  // Filters
  filters: {
    sucursalId: string | null;
    module: "all" | "recepcion" | "kidibar";
    startDate: string;
    endDate: string;
  };
}

const initialState: ReportsState = {
  sales: null,
  stock: null,
  services: null,
  salesComparison: null,
  moduleComparison: null,
  arqueos: null,
  customers: null,
  customersSummary: null,
  forecast: null,
  loading: false,
  error: null,
  filters: {
    sucursalId: null,
    module: "all",
    startDate: new Date(new Date().setDate(new Date().getDate() - 30)).toISOString().split("T")[0],
    endDate: new Date().toISOString().split("T")[0],
  },
};

export const reportsStore: Writable<ReportsState> = writable(initialState);

/**
 * Calculate comparison data between current and previous period.
 */
function calculateComparison(current: number, previous: number): ComparisonData {
  const change_absolute = current - previous;
  const change_percent = previous !== 0 ? (change_absolute / previous) * 100 : 0;
  
  let trend: "up" | "down" | "stable";
  if (Math.abs(change_percent) < 1) {
    trend = "stable";
  } else if (change_percent > 0) {
    trend = "up";
  } else {
    trend = "down";
  }
  
  return {
    current,
    previous,
    change_percent,
    change_absolute,
    trend,
  };
}

/**
 * Time series data point interface.
 */
export interface TimeSeriesDataPoint {
  date: string;
  revenue_cents: number;
  sales_count: number;
  atv_cents: number;
}

/**
 * Time series report interface.
 */
export interface TimeSeriesReport {
  timeseries: TimeSeriesDataPoint[];
  period: {
    start_date: string;
    end_date: string;
  };
}

/**
 * Fetch sales report with optional filters.
 */
export async function fetchSalesReport(
  sucursalId?: string | null,
  startDate?: string,
  endDate?: string,
  module?: "all" | "recepcion" | "kidibar"
): Promise<SalesReport | null> {
  try {
    const params = new URLSearchParams();
    if (sucursalId) params.append("sucursal_id", sucursalId);
    if (startDate) params.append("start_date", startDate);
    if (endDate) params.append("end_date", endDate);
    if (module && module !== "all") params.append("module", module);
    
    const report = await get<SalesReport>(`/reports/sales?${params.toString()}`);
    return report;
  } catch (error: any) {
    console.error("Error fetching sales report:", error);
    throw error;
  }
}

/**
 * Fetch sales time series data.
 */
export async function fetchSalesTimeSeries(
  sucursalId?: string | null,
  startDate?: string,
  endDate?: string,
  module?: "all" | "recepcion" | "kidibar"
): Promise<TimeSeriesReport | null> {
  try {
    const params = new URLSearchParams();
    if (sucursalId) params.append("sucursal_id", sucursalId);
    if (startDate) params.append("start_date", startDate);
    if (endDate) params.append("end_date", endDate);
    if (module && module !== "all") params.append("module", module);
    
    const report = await get<TimeSeriesReport>(`/reports/sales/timeseries?${params.toString()}`);
    return report;
  } catch (error: any) {
    console.error("Error fetching sales time series:", error);
    throw error;
  }
}

/**
 * Fetch stock report.
 */
export async function fetchStockReport(
  sucursalId?: string | null
): Promise<StockReport | null> {
  try {
    const params = new URLSearchParams();
    if (sucursalId) params.append("sucursal_id", sucursalId);
    
    const report = await get<StockReport>(`/reports/stock?${params.toString()}`);
    return report;
  } catch (error: any) {
    console.error("Error fetching stock report:", error);
    throw error;
  }
}

/**
 * Fetch services report.
 */
export async function fetchServicesReport(
  sucursalId?: string | null
): Promise<ServicesReport | null> {
  try {
    const params = new URLSearchParams();
    if (sucursalId) params.append("sucursal_id", sucursalId);
    
    const report = await get<ServicesReport>(`/reports/services?${params.toString()}`);
    return report;
  } catch (error: any) {
    console.error("Error fetching services report:", error);
    throw error;
  }
}

/**
 * Fetch all reports and update store.
 */
export async function fetchAllReports(
  sucursalId?: string | null,
  startDate?: string,
  endDate?: string,
  module?: "all" | "recepcion" | "kidibar"
): Promise<void> {
  reportsStore.update((state) => ({ ...state, loading: true, error: null }));
  
  try {
    // Fetch current period reports
    const [sales, stock, services] = await Promise.all([
      fetchSalesReport(sucursalId, startDate, endDate, module),
      fetchStockReport(sucursalId),
      fetchServicesReport(sucursalId),
    ]);
    
    // Calculate previous period for comparison
    let salesComparison: ComparisonData | null = null;
    if (sales && startDate && endDate) {
      try {
        const comparisonParams = new URLSearchParams();
        if (sucursalId) comparisonParams.append("sucursal_id", sucursalId);
        comparisonParams.append("start_date", startDate);
        comparisonParams.append("end_date", endDate);
        comparisonParams.append("comparison_type", "previous_period");
        
        const comparisonData = await get<{
          comparison: {
            revenue: ComparisonData;
          };
        }>(`/reports/sales/comparison?${comparisonParams.toString()}`);
        
        if (comparisonData?.comparison?.revenue) {
          salesComparison = comparisonData.comparison.revenue;
        }
      } catch (error) {
        console.warn("Could not fetch sales comparison:", error);
      }
    }
    
    // Calculate module comparison (Recepción vs KidiBar)
    let moduleComparison: ModuleComparison | null = null;
    try {
      const moduleParams = new URLSearchParams();
      if (sucursalId) moduleParams.append("sucursal_id", sucursalId);
      if (startDate) moduleParams.append("start_date", startDate);
      if (endDate) moduleParams.append("end_date", endDate);
      
      const moduleData = await get<ModuleComparison>(`/reports/modules/comparison?${moduleParams.toString()}`);
      moduleComparison = moduleData;
    } catch (error) {
      console.warn("Could not fetch module comparison:", error);
    }
    
    // Fetch additional reports
    let arqueos: ArqueosReport | null = null;
    let customers: CustomersByModuleReport | null = null;
    
    try {
      arqueos = await fetchArqueosReport(sucursalId, startDate, endDate, module);
    } catch (error) {
      console.warn("Could not fetch arqueos report:", error);
    }
    
    try {
      const customersParams = new URLSearchParams();
      if (sucursalId) customersParams.append("sucursal_id", sucursalId);
      customersParams.append("days", "30");
      if (module && module !== "all") customersParams.append("module", module);
      
      customers = await get<CustomersByModuleReport>(`/reports/customers/by-module?${customersParams.toString()}`);
    } catch (error) {
      console.warn("Could not fetch customers report:", error);
    }

    // Fetch customers summary for executive summary
    let customersSummary: CustomersSummaryReport | null = null;
    try {
      customersSummary = await fetchCustomersSummary(sucursalId, startDate, endDate);
    } catch (error) {
      console.warn("Could not fetch customers summary:", error);
    }
    
    reportsStore.update((state) => ({
      ...state,
      sales,
      stock,
      services,
      salesComparison,
      moduleComparison,
      arqueos,
      customers,
      customersSummary,
      loading: false,
      filters: {
        sucursalId: sucursalId || null,
        module: module || "all",
        startDate: startDate || state.filters.startDate,
        endDate: endDate || state.filters.endDate,
      },
      error: null,
    }));
  } catch (error: any) {
    reportsStore.update((state) => ({
      ...state,
      error: error.message || "Error loading reports",
      loading: false,
    }));
  }
}

/**
 * Format price from cents.
 */
export function formatPrice(cents: number): string {
  return `$${(cents / 100).toFixed(2)}`;
}

/**
 * Format percentage change.
 */
export function formatPercentChange(percent: number): string {
  const sign = percent >= 0 ? "+" : "";
  return `${sign}${percent.toFixed(1)}%`;
}

/**
 * Fetch arqueos report.
 */
export async function fetchArqueosReport(
  sucursalId?: string | null,
  startDate?: string,
  endDate?: string,
  module?: "all" | "recepcion" | "kidibar"
): Promise<ArqueosReport | null> {
  try {
    const params = new URLSearchParams();
    if (sucursalId) params.append("sucursal_id", sucursalId);
    if (startDate) params.append("start_date", startDate);
    if (endDate) params.append("end_date", endDate);
    if (module && module !== "all") params.append("module", module);
    
    const report = await get<ArqueosReport>(`/reports/arqueos?${params.toString()}`);
    return report;
  } catch (error: any) {
    console.error("Error fetching arqueos report:", error);
    throw error;
  }
}

/**
 * Time series data point for arqueos.
 */
export interface ArqueosTimeSeriesDataPoint {
  date: string;
  system_total_cents: number;
  physical_count_cents: number;
  difference_cents: number;
  arqueos_count: number;
  perfect_matches: number;
  discrepancies: number;
}

/**
 * Time series report for arqueos.
 */
export interface ArqueosTimeSeriesReport {
  timeseries: ArqueosTimeSeriesDataPoint[];
  period: {
    start_date: string;
    end_date: string;
  };
}

/**
 * Fetch arqueos time series data.
 */
export async function fetchArqueosTimeSeries(
  sucursalId?: string | null,
  startDate?: string,
  endDate?: string,
  module?: "all" | "recepcion" | "kidibar"
): Promise<ArqueosTimeSeriesReport | null> {
  try {
    const params = new URLSearchParams();
    if (sucursalId) params.append("sucursal_id", sucursalId);
    if (startDate) params.append("start_date", startDate);
    if (endDate) params.append("end_date", endDate);
    if (module && module !== "all") params.append("module", module);
    
    const report = await get<ArqueosTimeSeriesReport>(`/reports/arqueos/timeseries?${params.toString()}`);
    return report;
  } catch (error: any) {
    console.error("Error fetching arqueos time series:", error);
    throw error;
  }
}

/**
 * Heatmap data point for arqueos.
 */
export interface ArqueosHeatmapDataPoint {
  date: string;
  difference_cents: number;
  discrepancy_rate: number;
  intensity: number; // 0-4: 0=perfect, 1=low, 2=medium, 3=high, 4=critical
  arqueos_count: number;
}

/**
 * Heatmap report for arqueos.
 */
export interface ArqueosHeatmapReport {
  heatmap: ArqueosHeatmapDataPoint[];
  period: {
    start_date: string;
    end_date: string;
  };
  intensity_scale: {
    perfect: number;
    low: number;
    medium: number;
    high: number;
    critical: number;
  };
  thresholds: {
    low: number;
    medium: number;
    high: number;
    critical: number;
  };
}

/**
 * Fetch arqueos heatmap data.
 */
export async function fetchArqueosHeatmap(
  sucursalId?: string | null,
  startDate?: string,
  endDate?: string,
  module?: "all" | "recepcion" | "kidibar"
): Promise<ArqueosHeatmapReport | null> {
  try {
    const params = new URLSearchParams();
    if (sucursalId) params.append("sucursal_id", sucursalId);
    if (startDate) params.append("start_date", startDate);
    if (endDate) params.append("end_date", endDate);
    if (module && module !== "all") params.append("module", module);
    
    const report = await get<ArqueosHeatmapReport>(`/reports/arqueos/heatmap?${params.toString()}`);
    return report;
  } catch (error: any) {
    console.error("Error fetching arqueos heatmap:", error);
    throw error;
  }
}

/**
 * Variance analysis report for arqueos.
 */
export interface ArqueosVarianceReport {
  differences: number[];
  statistics: {
    mean: number;
    median: number;
    std_dev: number;
    min: number;
    max: number;
    q1: number;
    q3: number;
    iqr: number;
  };
  distribution: {
    perfect: number;
    ranges: Array<{
      min: number;
      max: number;
      count: number;
    }>;
  };
  period: {
    start_date: string;
    end_date: string;
  };
}

/**
 * Fetch arqueos variance analysis.
 */
export async function fetchArqueosVariance(
  sucursalId?: string | null,
  startDate?: string,
  endDate?: string,
  module?: "all" | "recepcion" | "kidibar"
): Promise<ArqueosVarianceReport | null> {
  try {
    const params = new URLSearchParams();
    if (sucursalId) params.append("sucursal_id", sucursalId);
    if (startDate) params.append("start_date", startDate);
    if (endDate) params.append("end_date", endDate);
    if (module && module !== "all") params.append("module", module);
    
    const report = await get<ArqueosVarianceReport>(`/reports/arqueos/variance?${params.toString()}`);
    return report;
  } catch (error: any) {
    console.error("Error fetching arqueos variance:", error);
    throw error;
  }
}

/**
 * Anomaly data point.
 */
export interface ArqueosAnomaly {
  date: string;
  difference_cents: number;
  system_total_cents: number;
  physical_count_cents: number;
  severity: "moderate" | "severe";
  z_score: number;
}

/**
 * Anomalies report.
 */
export interface ArqueosAnomaliesReport {
  anomalies: ArqueosAnomaly[];
  thresholds: {
    lower_bound: number;
    upper_bound: number;
    iqr: number;
  };
  statistics: {
    q1: number;
    q3: number;
    median: number;
  };
  period: {
    start_date: string;
    end_date: string;
  };
}

/**
 * Fetch arqueos anomalies.
 */
export async function fetchArqueosAnomalies(
  sucursalId?: string | null,
  startDate?: string,
  endDate?: string,
  module?: "all" | "recepcion" | "kidibar"
): Promise<ArqueosAnomaliesReport | null> {
  try {
    const params = new URLSearchParams();
    if (sucursalId) params.append("sucursal_id", sucursalId);
    if (startDate) params.append("start_date", startDate);
    if (endDate) params.append("end_date", endDate);
    if (module && module !== "all") params.append("module", module);
    
    const report = await get<ArqueosAnomaliesReport>(`/reports/arqueos/anomalies?${params.toString()}`);
    return report;
  } catch (error: any) {
    console.error("Error fetching arqueos anomalies:", error);
    throw error;
  }
}

/**
 * Trends report.
 */
export interface ArqueosTrendsReport {
  current: {
    discrepancy_rate: number;
    perfect_matches: number;
    discrepancies: number;
  };
  month_over_month: {
    change: number;
    percent_change: number;
    trend: "improving" | "worsening" | "stable";
  };
  week_over_week: {
    change: number;
    percent_change: number;
    trend: "improving" | "worsening" | "stable";
  };
  year_over_year: {
    change: number;
    percent_change: number;
    trend: "improving" | "worsening" | "stable";
  };
  period: {
    current_start: string;
    current_end: string;
  };
}

/**
 * Fetch arqueos trends.
 */
export async function fetchArqueosTrends(
  sucursalId?: string | null,
  endDate?: string,
  module?: "all" | "recepcion" | "kidibar"
): Promise<ArqueosTrendsReport | null> {
  try {
    const params = new URLSearchParams();
    if (sucursalId) params.append("sucursal_id", sucursalId);
    if (endDate) params.append("end_date", endDate);
    if (module && module !== "all") params.append("module", module);
    
    const report = await get<ArqueosTrendsReport>(`/reports/arqueos/trends?${params.toString()}`);
    return report;
  } catch (error: any) {
    console.error("Error fetching arqueos trends:", error);
    throw error;
  }
}

/**
 * User analysis data.
 */
export interface ArqueosUserAnalysis {
  user_id: string;
  user_name: string;
  user_role: string;
  arqueos_count: number;
  perfect_matches: number;
  discrepancies: number;
  discrepancy_rate: number;
  avg_difference_cents: number;
  total_abs_difference_cents: number;
}

/**
 * By user report.
 */
export interface ArqueosByUserReport {
  users: ArqueosUserAnalysis[];
  period: {
    start_date: string;
    end_date: string;
  };
}

/**
 * Fetch arqueos by user.
 */
export async function fetchArqueosByUser(
  sucursalId?: string | null,
  startDate?: string,
  endDate?: string,
  module?: "all" | "recepcion" | "kidibar"
): Promise<ArqueosByUserReport | null> {
  try {
    const params = new URLSearchParams();
    if (sucursalId) params.append("sucursal_id", sucursalId);
    if (startDate) params.append("start_date", startDate);
    if (endDate) params.append("end_date", endDate);
    if (module && module !== "all") params.append("module", module);
    
    const report = await get<ArqueosByUserReport>(`/reports/arqueos/by-user?${params.toString()}`);
    return report;
  } catch (error: any) {
    console.error("Error fetching arqueos by user:", error);
    throw error;
  }
}

/**
 * Prediction data point.
 */
export interface ArqueosPrediction {
  date: string;
  predicted_difference_cents: number;
  confidence: "high" | "medium" | "low";
}

/**
 * Predictions report.
 */
export interface ArqueosPredictionsReport {
  forecast: ArqueosPrediction[];
  confidence: "high" | "medium" | "low";
  method: string;
  historical_avg?: number;
  trend_factor?: number;
  message?: string;
}

/**
 * Fetch arqueos predictions.
 */
export async function fetchArqueosPredictions(
  sucursalId?: string | null,
  forecastDays: number = 7,
  module?: "all" | "recepcion" | "kidibar"
): Promise<ArqueosPredictionsReport | null> {
  try {
    const params = new URLSearchParams();
    if (sucursalId) params.append("sucursal_id", sucursalId);
    params.append("forecast_days", forecastDays.toString());
    if (module && module !== "all") params.append("module", module);
    
    const report = await get<ArqueosPredictionsReport>(`/reports/arqueos/predictions?${params.toString()}`);
    return report;
  } catch (error: any) {
    console.error("Error fetching arqueos predictions:", error);
    throw error;
  }
}

/**
 * Alert data.
 */
export interface ArqueosAlert {
  type: string;
  severity: "high" | "medium" | "low";
  message: string;
  recommendation: string;
  value: number;
  threshold: number;
}

/**
 * Alerts report.
 */
export interface ArqueosAlertsReport {
  alerts: ArqueosAlert[];
  thresholds: {
    [key: string]: number;
  };
  status: "active" | "normal" | "no_data";
}

/**
 * Fetch arqueos alerts.
 */
export async function fetchArqueosAlerts(
  sucursalId?: string | null,
  module?: "all" | "recepcion" | "kidibar"
): Promise<ArqueosAlertsReport | null> {
  try {
    const params = new URLSearchParams();
    if (sucursalId) params.append("sucursal_id", sucursalId);
    if (module && module !== "all") params.append("module", module);
    
    const report = await get<ArqueosAlertsReport>(`/reports/arqueos/alerts?${params.toString()}`);
    return report;
  } catch (error: any) {
    console.error("Error fetching arqueos alerts:", error);
    throw error;
  }
}

/**
 * Recommendation data.
 */
export interface ArqueosRecommendation {
  priority: "high" | "medium" | "low" | "info";
  title: string;
  description: string;
  action: string;
  impact: string;
}

/**
 * Recommendations report.
 */
export interface ArqueosRecommendationsReport {
  recommendations: ArqueosRecommendation[];
  summary: string;
}

/**
 * Fetch arqueos recommendations.
 */
export async function fetchArqueosRecommendations(
  sucursalId?: string | null,
  module?: "all" | "recepcion" | "kidibar"
): Promise<ArqueosRecommendationsReport | null> {
  try {
    const params = new URLSearchParams();
    if (sucursalId) params.append("sucursal_id", sucursalId);
    if (module && module !== "all") params.append("module", module);
    
    const report = await get<ArqueosRecommendationsReport>(`/reports/arqueos/recommendations?${params.toString()}`);
    return report;
  } catch (error: any) {
    console.error("Error fetching arqueos recommendations:", error);
    throw error;
  }
}

/**
 * Customers summary interface.
 */
export interface CustomersSummaryReport {
  total_unique_customers: number;
  recepcion_unique: number;
  kidibar_unique: number;
  new_customers: number;
  recepcion_new: number;
  kidibar_new: number;
  total_revenue_cents: number;
  recepcion_revenue_cents: number;
  kidibar_revenue_cents: number;
  avg_revenue_per_customer_cents: number;
  period: {
    start_date: string;
    end_date: string;
  };
}

/**
 * Fetch customers summary.
 */
export async function fetchCustomersSummary(
  sucursalId?: string | null,
  startDate?: string,
  endDate?: string
): Promise<CustomersSummaryReport | null> {
  try {
    const params = new URLSearchParams();
    if (sucursalId) params.append("sucursal_id", sucursalId);
    if (startDate) params.append("start_date", startDate);
    if (endDate) params.append("end_date", endDate);
    
    const report = await get<CustomersSummaryReport>(`/reports/customers/summary?${params.toString()}`);
    return report;
  } catch (error: any) {
    console.error("Error fetching customers summary:", error);
    return null;
  }
}

/**
 * Fetch customers by module report.
 */
export async function fetchCustomersByModuleReport(
  sucursalId?: string | null,
  days: number = 30,
  module?: "all" | "recepcion" | "kidibar"
): Promise<CustomersByModuleReport | null> {
  try {
    const params = new URLSearchParams();
    if (sucursalId) params.append("sucursal_id", sucursalId);
    params.append("days", days.toString());
    if (module && module !== "all") params.append("module", module);
    
    const report = await get<CustomersByModuleReport>(`/reports/customers/by-module?${params.toString()}`);
    return report;
  } catch (error: any) {
    console.error("Error fetching customers report:", error);
    throw error;
  }
}

/**
 * Generate enhanced forecast.
 */
export async function generateEnhancedForecast(
  sucursalId?: string | null,
  forecastDays: number = 7,
  module?: "recepcion" | "kidibar" | null
): Promise<ForecastReport | null> {
  try {
    const params = new URLSearchParams();
    if (sucursalId) params.append("sucursal_id", sucursalId);
    params.append("forecast_days", forecastDays.toString());
    if (module) params.append("module", module);
    
    const response = await fetch(`/api/reports/predictions/generate/enhanced?${params.toString()}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    return data.predictions?.sales || null;
  } catch (error: any) {
    console.error("Error generating enhanced forecast:", error);
    throw error;
  }
}

/**
 * Generate segmented predictions for multiple modules.
 */
export async function generateSegmentedPredictions(
  sucursalId?: string | null,
  forecastDays: number = 7,
  modules: string[] = ["all"],
  predictionTypes: string[] = ["sales"]
): Promise<SegmentedPredictionsResponse | null> {
  try {
    const { post } = await import("@kidyland/utils");
    
    const response = await post<SegmentedPredictionsResponse>(
      "/reports/predictions/generate/segmented",
      {
        sucursal_id: sucursalId || null,
        forecast_days: forecastDays,
        modules: modules,
        prediction_types: predictionTypes,
      }
    );
    
    return response;
  } catch (error: any) {
    console.error("Error generating segmented predictions:", error);
    throw error;
  }
}

/**
 * Reset prediction limit for current user (development helper).
 * Resets the prediction count allowing unlimited predictions again.
 */
export async function resetPredictionLimit(): Promise<{ success: boolean; message: string; reset_count: number } | null> {
  try {
    const { post } = await import("@kidyland/utils");
    
    const response = await post<{ success: boolean; message: string; reset_count: number }>(
      "/reports/predictions/reset",
      {}
    );
    
    return response;
  } catch (error: any) {
    console.error("Error resetting prediction limit:", error);
    return null;
  }
}

// ============================================================================
// INVENTORY REPORTS - Phase 1: Time Series and Turnover
// ============================================================================

// ============================================================================
// INVENTORY REPORTS - Phase 1: Time Series and Turnover
// ============================================================================

// ============================================================================
// INVENTORY REPORTS - Phase 1: Time Series and Turnover
// ============================================================================

export interface InventoryTimeSeriesDataPoint {
  date: string;
  stock_qty: number;
  products_count: number;
  low_stock_count: number;
  total_value_cents: number;
}

export interface InventoryTimeSeriesReport {
  timeseries: InventoryTimeSeriesDataPoint[];
  period: {
    start_date: string;
    end_date: string;
  };
}

export interface InventoryTurnoverProduct {
  product_id: string;
  product_name: string;
  current_stock: number;
  quantity_sold: number;
  turnover_rate: number;
  days_on_hand: number;
  category: "fast" | "slow" | "normal";
}

export interface InventoryTurnoverReport {
  products: InventoryTurnoverProduct[];
  summary: {
    total_products: number;
    fast_movers: number;
    slow_movers: number;
    normal_movers: number;
    average_turnover: number;
  };
  period: {
    start_date: string;
    end_date: string;
    days: number;
  };
}

/**
 * Fetch inventory time series data.
 */
export async function fetchInventoryTimeSeries(
  sucursalId?: string | null,
  startDate?: string,
  endDate?: string,
  productId?: string | null
): Promise<InventoryTimeSeriesReport | null> {
  try {
    const params = new URLSearchParams();
    if (sucursalId) params.append("sucursal_id", sucursalId);
    if (startDate) params.append("start_date", startDate);
    if (endDate) params.append("end_date", endDate);
    if (productId) params.append("product_id", productId);
    
    const report = await get<InventoryTimeSeriesReport>(`/reports/inventory/timeseries?${params.toString()}`);
    return report;
  } catch (error: any) {
    console.error("Error fetching inventory time series:", error);
    throw error;
  }
}

/**
 * Fetch inventory turnover analysis.
 */
export async function fetchInventoryTurnover(
  sucursalId?: string | null,
  startDate?: string,
  endDate?: string
): Promise<InventoryTurnoverReport | null> {
  try {
    const params = new URLSearchParams();
    if (sucursalId) params.append("sucursal_id", sucursalId);
    if (startDate) params.append("start_date", startDate);
    if (endDate) params.append("end_date", endDate);
    
    const report = await get<InventoryTurnoverReport>(`/reports/inventory/turnover?${params.toString()}`);
    return report;
  } catch (error: any) {
    console.error("Error fetching inventory turnover:", error);
    throw error;
  }
}

// ============================================================================
// SERVICES REPORTS - Phase 1: Time Series and Utilization
// ============================================================================

export interface ServicesTimeSeriesDataPoint {
  date: string;
  service_sales_count: number;
  package_sales_count: number;
  total_sales_count: number;
  revenue_cents: number;
  active_timers_count: number;
}

export interface ServicesTimeSeriesReport {
  timeseries: ServicesTimeSeriesDataPoint[];
  period: {
    start_date: string;
    end_date: string;
  };
}

export interface ServicesUtilizationService {
  service_id: string;
  service_name: string;
  active_timers: number;
  max_capacity: number;
  utilization_rate: number;
  total_sales: number;
  revenue_cents: number;
}

export interface ServicesUtilizationReport {
  services: ServicesUtilizationService[];
  summary: {
    total_services: number;
    average_utilization: number;
    high_utilization_count: number;
    low_utilization_count: number;
    normal_utilization_count: number;
  };
  period: {
    start_date: string;
    end_date: string;
  };
}

/**
 * Fetch services time series data.
 */
export async function fetchServicesTimeSeries(
  sucursalId?: string | null,
  startDate?: string,
  endDate?: string,
  serviceId?: string | null
): Promise<ServicesTimeSeriesReport | null> {
  try {
    const params = new URLSearchParams();
    if (sucursalId) params.append("sucursal_id", sucursalId);
    if (startDate) params.append("start_date", startDate);
    if (endDate) params.append("end_date", endDate);
    if (serviceId) params.append("service_id", serviceId);
    
    const report = await get<ServicesTimeSeriesReport>(`/reports/services/timeseries?${params.toString()}`);
    return report;
  } catch (error: any) {
    console.error("Error fetching services time series:", error);
    throw error;
  }
}

/**
 * Fetch services utilization analysis.
 */
export async function fetchServicesUtilization(
  sucursalId?: string | null,
  startDate?: string,
  endDate?: string
): Promise<ServicesUtilizationReport | null> {
  try {
    const params = new URLSearchParams();
    if (sucursalId) params.append("sucursal_id", sucursalId);
    if (startDate) params.append("start_date", startDate);
    if (endDate) params.append("end_date", endDate);
    
    const report = await get<ServicesUtilizationReport>(`/reports/services/utilization?${params.toString()}`);
    return report;
  } catch (error: any) {
    console.error("Error fetching services utilization:", error);
    throw error;
  }
}

// ============================================================================
// INVENTORY REPORTS - Phase 2-4: Heatmap, Movement, Reorder, Forecast, Recommendations
// ============================================================================

export interface InventoryHeatmapDataPoint {
  date: string;
  stock_qty: number;
  low_stock_count: number;
  intensity: number;
}

export interface InventoryHeatmapReport {
  heatmap: InventoryHeatmapDataPoint[];
  period: {
    start_date: string;
    end_date: string;
  };
}

export interface InventoryMovementReport {
  fast_movers: InventoryTurnoverProduct[];
  slow_movers: InventoryTurnoverProduct[];
  normal_movers: InventoryTurnoverProduct[];
  summary: InventoryTurnoverReport["summary"];
  period: InventoryTurnoverReport["period"];
}

export interface InventoryReorderPoint {
  product_id: string;
  product_name: string;
  current_stock: number;
  daily_sales_avg: number;
  lead_time_days: number;
  reorder_point: number;
  safety_stock: number;
  needs_reorder: boolean;
  days_until_stockout: number;
}

export interface InventoryReorderPointsReport {
  reorder_points: InventoryReorderPoint[];
  summary: {
    total_products: number;
    needs_reorder_count: number;
    default_lead_time_days: number;
  };
  period: {
    start_date: string;
    end_date: string;
  };
}

export interface InventoryAlert {
  type: string;
  level: "high" | "medium" | "low";
  product_id: string;
  product_name: string;
  current_stock: number;
  threshold?: number;
  days_until_stockout: number | null;
  recommended_reorder_qty: number | null;
  turnover_rate: number | null;
}

export interface InventoryAlertsReport {
  alerts: InventoryAlert[];
  summary: {
    total_alerts: number;
    high_priority: number;
    medium_priority: number;
    low_priority: number;
  };
}

export interface InventoryForecastProduct {
  product_id: string;
  product_name: string;
  current_stock: number;
  daily_avg_sales: number;
  forecasted_demand: number;
  projected_stock: number;
  will_run_out: boolean;
  days_until_out: number;
}

export interface InventoryForecastReport {
  forecasts: InventoryForecastProduct[];
  summary: {
    forecast_days: number;
    total_products: number;
    will_run_out_count: number;
  };
  period: {
    start_date: string;
    end_date: string;
  };
}

export interface InventoryRecommendation {
  priority: "high" | "medium" | "low" | "info";
  title: string;
  description: string;
  action: string;
}

export interface InventoryRecommendationsReport {
  recommendations: InventoryRecommendation[];
  summary: string;
}

/**
 * Fetch inventory heatmap data.
 */
export async function fetchInventoryHeatmap(
  sucursalId?: string | null,
  startDate?: string,
  endDate?: string
): Promise<InventoryHeatmapReport | null> {
  try {
    const params = new URLSearchParams();
    if (sucursalId) params.append("sucursal_id", sucursalId);
    if (startDate) params.append("start_date", startDate);
    if (endDate) params.append("end_date", endDate);
    
    const report = await get<InventoryHeatmapReport>(`/reports/inventory/heatmap?${params.toString()}`);
    return report;
  } catch (error: any) {
    console.error("Error fetching inventory heatmap:", error);
    throw error;
  }
}

/**
 * Fetch inventory movement analysis (fast/slow movers).
 */
export async function fetchInventoryMovement(
  sucursalId?: string | null,
  startDate?: string,
  endDate?: string
): Promise<InventoryMovementReport | null> {
  try {
    const params = new URLSearchParams();
    if (sucursalId) params.append("sucursal_id", sucursalId);
    if (startDate) params.append("start_date", startDate);
    if (endDate) params.append("end_date", endDate);
    
    const report = await get<InventoryMovementReport>(`/reports/inventory/movement?${params.toString()}`);
    return report;
  } catch (error: any) {
    console.error("Error fetching inventory movement:", error);
    throw error;
  }
}

/**
 * Fetch inventory reorder points.
 */
export async function fetchInventoryReorderPoints(
  sucursalId?: string | null,
  startDate?: string,
  endDate?: string
): Promise<InventoryReorderPointsReport | null> {
  try {
    const params = new URLSearchParams();
    if (sucursalId) params.append("sucursal_id", sucursalId);
    if (startDate) params.append("start_date", startDate);
    if (endDate) params.append("end_date", endDate);
    
    const report = await get<InventoryReorderPointsReport>(`/reports/inventory/reorder-points?${params.toString()}`);
    return report;
  } catch (error: any) {
    console.error("Error fetching inventory reorder points:", error);
    throw error;
  }
}

/**
 * Fetch inventory alerts.
 */
export async function fetchInventoryAlerts(
  sucursalId?: string | null
): Promise<InventoryAlertsReport | null> {
  try {
    const params = new URLSearchParams();
    if (sucursalId) params.append("sucursal_id", sucursalId);
    
    const report = await get<InventoryAlertsReport>(`/reports/inventory/alerts?${params.toString()}`);
    return report;
  } catch (error: any) {
    console.error("Error fetching inventory alerts:", error);
    throw error;
  }
}

/**
 * Fetch inventory forecast.
 */
export async function fetchInventoryForecast(
  sucursalId?: string | null,
  forecastDays: number = 7
): Promise<InventoryForecastReport | null> {
  try {
    const params = new URLSearchParams();
    if (sucursalId) params.append("sucursal_id", sucursalId);
    params.append("forecast_days", forecastDays.toString());
    
    const report = await get<InventoryForecastReport>(`/reports/inventory/forecast?${params.toString()}`);
    return report;
  } catch (error: any) {
    console.error("Error fetching inventory forecast:", error);
    throw error;
  }
}

/**
 * Fetch inventory recommendations.
 */
export async function fetchInventoryRecommendations(
  sucursalId?: string | null
): Promise<InventoryRecommendationsReport | null> {
  try {
    const params = new URLSearchParams();
    if (sucursalId) params.append("sucursal_id", sucursalId);
    
    const report = await get<InventoryRecommendationsReport>(`/reports/inventory/recommendations?${params.toString()}`);
    return report;
  } catch (error: any) {
    console.error("Error fetching inventory recommendations:", error);
    throw error;
  }
}

// ============================================================================
// SERVICES REPORTS - Phase 2-4: Performance, Duration, Capacity, Patterns, Recommendations
// ============================================================================

export interface ServicesPerformanceService {
  service_id: string;
  service_name: string;
  sales_count: number;
  revenue_cents: number;
  popularity_rank: number;
}

export interface ServicesPerformanceReport {
  services: ServicesPerformanceService[];
  summary: {
    total_services: number;
    total_revenue_cents: number;
    total_sales: number;
  };
  period: {
    start_date: string;
    end_date: string;
  };
}

export interface ServicesDurationService {
  service_id: string;
  service_name: string;
  avg_duration_minutes: number;
  timer_count: number;
  min_allowed_duration: number;
  max_allowed_duration: number;
  usage_efficiency: number;
}

export interface ServicesDurationReport {
  services: ServicesDurationService[];
  summary: {
    total_services: number;
    total_timers: number;
    avg_duration_all: number;
  };
  period: {
    start_date: string;
    end_date: string;
  };
}

export interface ServicesCapacityDataPoint {
  date: string;
  hour: number;
  active_count: number;
  intensity: number;
}

export interface ServicesCapacityReport {
  heatmap: ServicesCapacityDataPoint[];
  period: {
    start_date: string;
    end_date: string;
  };
}

export interface ServicesPeakHoursReport {
  hourly_stats: Array<{
    hour: number;
    sales_count: number;
    revenue_cents: number;
  }>;
  peak_periods: Array<{
    hour: number;
    sales_count: number;
    revenue_cents: number;
  }>;
  off_peak_periods: Array<{
    hour: number;
    sales_count: number;
    revenue_cents: number;
  }>;
  summary: {
    peak_hour: number | null;
    peak_sales_count: number;
    total_hours_analyzed: number;
  };
  period: {
    start_date: string;
    end_date: string;
  };
}

export interface ServicesPatternDay {
  day_of_week: number;
  day_name: string;
  sales_count: number;
  revenue_cents: number;
}

export interface ServicesPatternsReport {
  day_of_week_patterns: ServicesPatternDay[];
  summary: {
    busiest_day: string | null;
    quietest_day: string | null;
  };
  period: {
    start_date: string;
    end_date: string;
  };
}

export interface ServicesRecommendation {
  priority: "high" | "medium" | "low" | "info";
  title: string;
  description: string;
  action: string;
}

export interface ServicesRecommendationsReport {
  recommendations: ServicesRecommendation[];
  summary: string;
}

/**
 * Fetch services performance metrics.
 */
export async function fetchServicesPerformance(
  sucursalId?: string | null,
  startDate?: string,
  endDate?: string
): Promise<ServicesPerformanceReport | null> {
  try {
    const params = new URLSearchParams();
    if (sucursalId) params.append("sucursal_id", sucursalId);
    if (startDate) params.append("start_date", startDate);
    if (endDate) params.append("end_date", endDate);
    
    const report = await get<ServicesPerformanceReport>(`/reports/services/performance?${params.toString()}`);
    return report;
  } catch (error: any) {
    console.error("Error fetching services performance:", error);
    throw error;
  }
}

/**
 * Fetch services duration analysis.
 */
export async function fetchServicesDuration(
  sucursalId?: string | null,
  startDate?: string,
  endDate?: string
): Promise<ServicesDurationReport | null> {
  try {
    const params = new URLSearchParams();
    if (sucursalId) params.append("sucursal_id", sucursalId);
    if (startDate) params.append("start_date", startDate);
    if (endDate) params.append("end_date", endDate);
    
    const report = await get<ServicesDurationReport>(`/reports/services/duration?${params.toString()}`);
    return report;
  } catch (error: any) {
    console.error("Error fetching services duration:", error);
    throw error;
  }
}

/**
 * Fetch services capacity heatmap.
 */
export async function fetchServicesCapacity(
  sucursalId?: string | null,
  startDate?: string,
  endDate?: string
): Promise<ServicesCapacityReport | null> {
  try {
    const params = new URLSearchParams();
    if (sucursalId) params.append("sucursal_id", sucursalId);
    if (startDate) params.append("start_date", startDate);
    if (endDate) params.append("end_date", endDate);
    
    const report = await get<ServicesCapacityReport>(`/reports/services/capacity?${params.toString()}`);
    return report;
  } catch (error: any) {
    console.error("Error fetching services capacity:", error);
    throw error;
  }
}

/**
 * Fetch services peak hours analysis.
 */
export async function fetchServicesPeakHours(
  sucursalId?: string | null,
  startDate?: string,
  endDate?: string
): Promise<ServicesPeakHoursReport | null> {
  try {
    const params = new URLSearchParams();
    if (sucursalId) params.append("sucursal_id", sucursalId);
    if (startDate) params.append("start_date", startDate);
    if (endDate) params.append("end_date", endDate);
    
    const report = await get<ServicesPeakHoursReport>(`/reports/services/peak-hours?${params.toString()}`);
    return report;
  } catch (error: any) {
    console.error("Error fetching services peak hours:", error);
    throw error;
  }
}

/**
 * Fetch services demand patterns.
 */
export async function fetchServicesPatterns(
  sucursalId?: string | null,
  startDate?: string,
  endDate?: string
): Promise<ServicesPatternsReport | null> {
  try {
    const params = new URLSearchParams();
    if (sucursalId) params.append("sucursal_id", sucursalId);
    if (startDate) params.append("start_date", startDate);
    if (endDate) params.append("end_date", endDate);
    
    const report = await get<ServicesPatternsReport>(`/reports/services/patterns?${params.toString()}`);
    return report;
  } catch (error: any) {
    console.error("Error fetching services patterns:", error);
    throw error;
  }
}

/**
 * Fetch services recommendations.
 */
export async function fetchServicesRecommendations(
  sucursalId?: string | null
): Promise<ServicesRecommendationsReport | null> {
  try {
    const params = new URLSearchParams();
    if (sucursalId) params.append("sucursal_id", sucursalId);
    
    const report = await get<ServicesRecommendationsReport>(`/reports/services/recommendations?${params.toString()}`);
    return report;
  } catch (error: any) {
    console.error("Error fetching services recommendations:", error);
    throw error;
  }
}

/**
 * Executive Summary - Aggregation and calculation functions
 */

/**
 * Calculate health score breakdown from reports data.
 */
function calculateHealthBreakdown(
  sales: SalesReport | null,
  stock: StockReport | null,
  services: ServicesReport | null,
  arqueos: ArqueosReport | null,
  customers: CustomersSummaryReport | null
): OverallHealth["breakdown"] {
  // Financial health (0-100): Based on revenue trends
  let financial = 50; // Default neutral
  if (sales) {
    // Positive revenue = good financial health
    if (sales.total_revenue_cents > 0) {
      financial = Math.min(100, 50 + Math.min(50, (sales.total_revenue_cents / 1000000) * 2)); // Scale based on revenue
    } else {
      financial = 25; // Low if no revenue
    }
  }

  // Operational health (0-100): Based on services utilization
  let operational = 50;
  if (services) {
    const utilizationRate = services.active_timers_count > 0 ? 
      (services.active_timers_count / Math.max(services.total_services || 1, 1)) * 100 : 0;
    operational = Math.min(100, utilizationRate);
  }

  // Inventory health (0-100): Based on stock alerts
  let inventory = 100;
  if (stock) {
    const totalProducts = stock.total_products || 1;
    const lowStockCount = stock.low_stock_alerts?.length || 0;
    const healthPercentage = ((totalProducts - lowStockCount) / totalProducts) * 100;
    inventory = Math.max(0, healthPercentage);
  }

  // Cash accuracy (0-100): Based on arqueos perfect matches
  let cash = 100;
  if (arqueos && arqueos.total_arqueos > 0) {
    const perfectRate = (arqueos.perfect_matches / arqueos.total_arqueos) * 100;
    cash = Math.max(0, perfectRate);
  }

  // Customer health (0-100): Based on customer metrics
  let customer = 50;
  if (customers) {
    if (customers.total_unique_customers > 0) {
      customer = Math.min(100, 50 + Math.min(50, (customers.total_unique_customers / 100) * 10)); // Scale based on customer count
    }
  }

  return { financial, operational, inventory, cash, customer };
}

/**
 * Calculate overall health score and status.
 */
function calculateOverallHealth(breakdown: OverallHealth["breakdown"]): OverallHealth {
  // Weighted average
  const weights = {
    financial: 0.30,
    operational: 0.25,
    inventory: 0.20,
    cash: 0.15,
    customer: 0.10
  };

  const score = Math.round(
    breakdown.financial * weights.financial +
    breakdown.operational * weights.operational +
    breakdown.inventory * weights.inventory +
    breakdown.cash * weights.cash +
    breakdown.customer * weights.customer
  );

  let status: HealthStatus;
  if (score >= 80) status = "excellent";
  else if (score >= 60) status = "good";
  else if (score >= 40) status = "warning";
  else status = "critical";

  // Determine trend (simplified - would need historical data for accurate trend)
  let trend: HealthTrend = "stable";
  if (score >= 75) trend = "improving";
  else if (score < 50) trend = "declining";

  return { score, status, trend, breakdown };
}

/**
 * Generate insights from all report sections.
 */
function generateInsights(
  sales: SalesReport | null,
  stock: StockReport | null,
  services: ServicesReport | null,
  arqueos: ArqueosReport | null,
  customers: CustomersSummaryReport | null,
  salesComparison: ComparisonData | null,
  forecast: ForecastReport | null,
  module: "all" | "recepcion" | "kidibar"
): Insight[] {
  const insights: Insight[] = [];

  // Sales insights
  if (sales && salesComparison) {
    if (salesComparison.trend === "up" && salesComparison.change_percent > 10) {
      insights.push({
        type: "opportunity",
        priority: "high",
        category: "sales",
        title: "Crecimiento de Ventas",
        description: `Las ventas han aumentado un ${salesComparison.change_percent.toFixed(1)}% comparado con el período anterior.`,
        impact: "Positivo",
        actionable: true,
        linkToSection: "sales"
      });
    } else if (salesComparison.trend === "down" && salesComparison.change_percent < -10) {
      insights.push({
        type: "risk",
        priority: "high",
        category: "sales",
        title: "Declive en Ventas",
        description: `Las ventas han disminuido un ${Math.abs(salesComparison.change_percent).toFixed(1)}% comparado con el período anterior.`,
        impact: "Requiere atención",
        actionable: true,
        linkToSection: "sales"
      });
    }
  }

  // Inventory insights
  if (stock && stock.low_stock_alerts && stock.low_stock_alerts.length > 0) {
    const criticalAlerts = stock.low_stock_alerts.filter((p: any) => 
      p.current_stock <= (p.threshold_alert_qty || 0)
    );
    if (criticalAlerts.length > 0) {
      insights.push({
        type: "risk",
        priority: criticalAlerts.length > 5 ? "high" : "medium",
        category: "inventory",
        title: "Alertas de Stock Bajo",
        description: `${criticalAlerts.length} producto(s) con stock crítico requieren reabastecimiento urgente.`,
        impact: "Alto - Puede afectar ventas",
        actionable: true,
        linkToSection: "inventory"
      });
    }
  }

  // Services insights
  if (services) {
    const utilizationRate = services.total_services > 0 ?
      (services.active_timers_count / services.total_services) * 100 : 0;
    if (utilizationRate < 30) {
      insights.push({
        type: "opportunity",
        priority: "medium",
        category: "services",
        title: "Baja Utilización de Servicios",
        description: `La utilización de servicios está en ${utilizationRate.toFixed(1)}%. Hay capacidad disponible para aumentar ingresos.`,
        impact: "Oportunidad de crecimiento",
        actionable: true,
        linkToSection: "services"
      });
    }
  }

  // Arqueos insights
  if (arqueos && arqueos.total_arqueos > 0) {
    const discrepancyRate = arqueos.discrepancy_rate || 0;
    if (discrepancyRate > 10) {
      insights.push({
        type: "risk",
        priority: discrepancyRate > 20 ? "high" : "medium",
        category: "arqueos",
        title: "Alta Tasa de Discrepancias",
        description: `La tasa de discrepancias en arqueos es del ${discrepancyRate.toFixed(1)}%. Requiere revisión de procedimientos.`,
        impact: "Afecta precisión financiera",
        actionable: true,
        linkToSection: "arqueos"
      });
    } else if (arqueos.perfect_matches / arqueos.total_arqueos > 0.9) {
      insights.push({
        type: "trend",
        priority: "low",
        category: "arqueos",
        title: "Excelente Precisión en Arqueos",
        description: `${((arqueos.perfect_matches / arqueos.total_arqueos) * 100).toFixed(1)}% de los arqueos son coincidencias perfectas.`,
        impact: "Excelente control operacional",
        actionable: false,
        linkToSection: "arqueos"
      });
    }
  }

  // Customer insights
  if (customers) {
    if (customers.new_customers > 0 && customers.new_customers / customers.total_unique_customers > 0.3) {
      insights.push({
        type: "opportunity",
        priority: "high",
        category: "customers",
        title: "Crecimiento en Clientes Nuevos",
        description: `${customers.new_customers} clientes nuevos (${((customers.new_customers / customers.total_unique_customers) * 100).toFixed(1)}% del total).`,
        impact: "Positivo para crecimiento",
        actionable: true,
        linkToSection: "customers"
      });
    }
  }

  // Forecasting insights
  if (forecast && forecast.forecast.length > 0) {
    const avgPredicted = forecast.forecast.reduce((sum, f) => sum + f.predicted_revenue_cents, 0) / forecast.forecast.length;
    if (sales && avgPredicted > sales.total_revenue_cents * 1.1) {
      insights.push({
        type: "trend",
        priority: "medium",
        category: "forecasting",
        title: "Proyección Optimista",
        description: `Las predicciones sugieren un crecimiento del ${(((avgPredicted - sales.total_revenue_cents) / sales.total_revenue_cents) * 100).toFixed(1)}% en los próximos días.`,
        impact: "Prepararse para mayor demanda",
        actionable: true,
        linkToSection: "forecasting"
      });
    }
  }

  // Sort by priority (high first, then medium, then low)
  const priorityOrder = { high: 0, medium: 1, low: 2 };
  insights.sort((a, b) => priorityOrder[a.priority] - priorityOrder[b.priority]);

  return insights.slice(0, 10); // Return top 10 insights
}

/**
 * Aggregate financial KPIs from reports.
 */
function aggregateFinancialKPIs(
  sales: SalesReport | null,
  salesComparison: ComparisonData | null,
  moduleComparison: ModuleComparison | null,
  forecast: ForecastReport | null
): FinancialKPIs {
  const totalRevenue = sales?.total_revenue_cents || 0;
  const atv = sales?.average_transaction_value_cents || 0;

  // Calculate revenue by module
  let revenueByModule = {
    recepcion: 0,
    kidibar: 0,
    total: totalRevenue
  };

  if (moduleComparison) {
    revenueByModule = {
      recepcion: moduleComparison.recepcion?.revenue_cents || 0,
      kidibar: moduleComparison.kidibar?.revenue_cents || 0,
      total: moduleComparison.total?.revenue_cents || 0
    };
  }

  // Calculate projected revenue from forecast (next 7 days)
  let projectedRevenue: number | undefined;
  if (forecast && forecast.forecast.length > 0) {
    projectedRevenue = forecast.forecast
      .slice(0, 7)
      .reduce((sum, f) => sum + f.predicted_revenue_cents, 0);
  }

  // Calculate revenue growth from comparison
  const revenueGrowth = salesComparison?.change_percent;

  return {
    totalRevenue,
    revenueTrend: salesComparison,
    projectedRevenue,
    revenueByModule,
    atv,
    revenueGrowth
  };
}

/**
 * Aggregate operational KPIs from reports.
 */
function aggregateOperationalKPIs(
  services: ServicesReport | null,
  stock: StockReport | null,
  arqueos: ArqueosReport | null
): OperationalKPIs {
  const activeServices = services?.active_timers_count || 0;
  
  // Calculate utilization rate
  const utilizationRate = services && services.total_services > 0 ?
    (activeServices / services.total_services) * 100 : 0;

  // Calculate stock health (% products not low stock)
  let stockHealth = 100;
  if (stock && stock.total_products > 0) {
    const lowStockCount = stock.low_stock_alerts?.length || 0;
    stockHealth = ((stock.total_products - lowStockCount) / stock.total_products) * 100;
  }

  // Calculate arqueos accuracy (% perfect matches)
  let arqueosAccuracy = 100;
  let discrepancyRate = 0;
  if (arqueos && arqueos.total_arqueos > 0) {
    arqueosAccuracy = (arqueos.perfect_matches / arqueos.total_arqueos) * 100;
    discrepancyRate = arqueos.discrepancy_rate || 0;
  }

  return {
    activeServices,
    utilizationRate,
    stockHealth,
    arqueosAccuracy,
    discrepancyRate
  };
}

/**
 * Aggregate customer KPIs from reports.
 */
function aggregateCustomerKPIs(
  customers: CustomersSummaryReport | null,
  sales: SalesReport | null,
  salesComparison: ComparisonData | null
): CustomerKPIs {
  const uniqueCustomers = customers?.total_unique_customers || 0;
  const newCustomers = customers?.new_customers || 0;
  const avgRevenuePerCustomer = customers?.avg_revenue_per_customer_cents || 0;

  // Calculate customer growth (approximate from unique customers)
  let customerGrowth: ComparisonData | null = null;
  if (salesComparison && customers) {
    // Approximate customer growth from revenue growth
    customerGrowth = {
      current: uniqueCustomers,
      previous: uniqueCustomers - newCustomers, // Approximation
      change_percent: newCustomers > 0 ? (newCustomers / uniqueCustomers) * 100 : 0,
      change_absolute: newCustomers,
      trend: newCustomers > uniqueCustomers * 0.1 ? "up" : "stable"
    };
  }

  // Count top customers (from sales unique customers if available)
  const topCustomersCount = sales?.unique_customers || uniqueCustomers;

  return {
    uniqueCustomers,
    newCustomers,
    avgRevenuePerCustomer,
    customerGrowth,
    topCustomersCount
  };
}

/**
 * Aggregate module breakdown from reports.
 */
function aggregateModuleBreakdown(
  moduleComparison: ModuleComparison | null,
  customers: CustomersSummaryReport | null,
  services: ServicesReport | null,
  stock: StockReport | null
): ExecutiveSummary["moduleBreakdown"] {
  if (!moduleComparison) return undefined;

  const recepcion: ModuleKPIs = {
    revenue: moduleComparison.recepcion.revenue_cents,
    salesCount: moduleComparison.recepcion.sales_count,
    atv: moduleComparison.recepcion.atv_cents,
    uniqueCustomers: customers?.recepcion_unique,
    servicesActive: undefined, // Would need module-specific services data
    stockAlerts: undefined // Would need module-specific stock data
  };

  const kidibar: ModuleKPIs = {
    revenue: moduleComparison.kidibar.revenue_cents,
    salesCount: moduleComparison.kidibar.sales_count,
    atv: moduleComparison.kidibar.atv_cents,
    uniqueCustomers: customers?.kidibar_unique,
    servicesActive: undefined,
    stockAlerts: undefined
  };

  return {
    recepcion,
    kidibar,
    comparison: moduleComparison
  };
}

/**
 * Calculate forecast projections from forecast report.
 */
function calculateForecastProjections(
  forecast: ForecastReport | null
): ForecastProjection | undefined {
  if (!forecast || !forecast.forecast || forecast.forecast.length === 0) {
    return undefined;
  }

  const forecastArray = forecast.forecast;
  
  // Next 7 days
  const next7Days = forecastArray.slice(0, 7);
  const projectedRevenue7 = next7Days.reduce((sum, f) => sum + f.predicted_revenue_cents, 0);
  const projectedCount7 = next7Days.reduce((sum, f) => sum + f.predicted_count, 0);

  // Next 30 days (or available days)
  const next30Days = forecastArray.slice(0, Math.min(30, forecastArray.length));
  const projectedRevenue30 = next30Days.reduce((sum, f) => sum + f.predicted_revenue_cents, 0);
  const projectedCount30 = next30Days.reduce((sum, f) => sum + f.predicted_count, 0);

  return {
    next7Days: {
      projectedRevenue: projectedRevenue7,
      projectedCount: projectedCount7,
      confidence: forecast.confidence
    },
    next30Days: {
      projectedRevenue: projectedRevenue30,
      projectedCount: projectedCount30,
      confidence: forecast.confidence
    },
    overallConfidence: forecast.confidence
  };
}

/**
 * Generate executive summary from reports state.
 */
export function generateExecutiveSummary(
  state: ReportsState,
  customersSummary?: CustomersSummaryReport | null
): ExecutiveSummary | null {
  // Check if we have at least sales data
  if (!state.sales) {
    return null;
  }

  // Calculate health breakdown
  const breakdown = calculateHealthBreakdown(
    state.sales,
    state.stock,
    state.services,
    state.arqueos,
    customersSummary || null
  );

  // Calculate overall health
  const overallHealth = calculateOverallHealth(breakdown);

  // Aggregate KPIs
  const financialKPIs = aggregateFinancialKPIs(
    state.sales,
    state.salesComparison,
    state.moduleComparison,
    state.forecast
  );

  const operationalKPIs = aggregateOperationalKPIs(
    state.services,
    state.stock,
    state.arqueos
  );

  const customerKPIs = aggregateCustomerKPIs(
    customersSummary || null,
    state.sales,
    state.salesComparison
  );

  // Generate insights
  const topInsights = generateInsights(
    state.sales,
    state.stock,
    state.services,
    state.arqueos,
    customersSummary || null,
    state.salesComparison,
    state.forecast,
    state.filters.module
  );

  // Module breakdown (only if module comparison available)
  const moduleBreakdown = state.filters.module === "all" 
    ? aggregateModuleBreakdown(state.moduleComparison, customersSummary || null, state.services, state.stock)
    : undefined;

  // Forecast projections
  const forecastProjections = calculateForecastProjections(state.forecast);

  return {
    overallHealth,
    financialKPIs,
    operationalKPIs,
    customerKPIs,
    topInsights,
    moduleBreakdown,
    forecastProjections
  };
}

/**
 * Derived store for Executive Summary.
 * Automatically calculates executive summary from reports state.
 */
export const executiveSummaryStore = derived(
  reportsStore,
  ($reportsStore) => {
    return generateExecutiveSummary($reportsStore, $reportsStore.customersSummary);
  }
);

// ========== FORECASTING STORE ==========
/**
 * Forecasting State - Global store for forecasting predictions.
 * 
 * This store maintains forecasting predictions state across the application,
 * allowing components to access forecasting data without prop drilling.
 * Used for export functionality and cross-component data sharing.
 */
export interface ForecastingState {
  predictionsData: SegmentedPredictionsResponse | null;
  generatedAt: number | null;
  forecastDays: number | null;
  module: "all" | "recepcion" | "kidibar" | null;
  predictionType: "sales" | "capacity" | "stock" | "all" | null;
  sucursalId: string | null;
  startDate: string | null;
  endDate: string | null;
}

const initialForecastingState: ForecastingState = {
  predictionsData: null,
  generatedAt: null,
  forecastDays: null,
  module: null,
  predictionType: null,
  sucursalId: null,
  startDate: null,
  endDate: null,
};

export const forecastingStore = writable<ForecastingState>(initialForecastingState);

/**
 * Update forecasting predictions in global store.
 * 
 * @param data - Segmented predictions response data
 * @param module - Module filter used for predictions
 * @param predictionType - Type of prediction generated
 * @param forecastDays - Number of days forecasted
 * @param sucursalId - Sucursal ID used for filtering
 * @param startDate - Start date used for historical data
 * @param endDate - End date used for historical data
 */
export function updateForecastingPredictions(
  data: SegmentedPredictionsResponse,
  module: "all" | "recepcion" | "kidibar",
  predictionType: "sales" | "capacity" | "stock" | "all",
  forecastDays: number,
  sucursalId: string | null = null,
  startDate: string | null = null,
  endDate: string | null = null
): void {
  forecastingStore.update((state) => ({
    ...state,
    predictionsData: data,
    generatedAt: Date.now(),
    module,
    predictionType,
    forecastDays,
    sucursalId,
    startDate,
    endDate,
  }));
}

/**
 * Clear forecasting predictions from global store.
 */
export function clearForecastingPredictions(): void {
  forecastingStore.set(initialForecastingState);
}

/**
 * Check if forecasting predictions exist and are valid.
 */
export function hasForecastingPredictions(state: ForecastingState): boolean {
  return (
    state.predictionsData !== null &&
    state.generatedAt !== null &&
    state.predictionsData.success === true
  );
}

