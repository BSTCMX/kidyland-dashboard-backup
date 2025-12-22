/**
 * Export Helpers - Utility functions for export functionality.
 * 
 * Provides helper functions for determining available sections,
 * generating export configurations, and managing export state.
 */

import type { SegmentedPredictionsResponse, ForecastingState } from "$lib/stores/reports";
import { forecastingStore, hasForecastingPredictions } from "$lib/stores/reports";
import { metricsStore } from "$lib/stores/metrics";
import { get } from "svelte/store";

// ========== TYPES ==========

export type ExportReportType = 
  | "dashboard" 
  | "reports" 
  | "sales" 
  | "stock" 
  | "inventory"
  | "services" 
  | "summary" 
  | "arqueos" 
  | "customers" 
  | "forecasting";

export type ExportSection = 
  | "sales"
  | "stock"
  | "inventory"
  | "services"
  | "peak_hours"
  | "top_products"
  | "top_services"
  | "top_customers"
  | "summary"
  | "arqueos"
  | "customers"
  | "forecasting"
  | "predictions";

export type ExportFormat = "excel" | "pdf";

export interface ExportSectionInfo {
  id: ExportSection;
  label: string;
  description: string;
  available: boolean;
  category?: "dashboard" | "reports";
  parentSection?: ExportSection; // For sub-sections (e.g., customer sub-menus)
}

export interface ExportConfiguration {
  reportType: ExportReportType;
  format: ExportFormat;
  sections: ExportSection[];
  includePredictions: boolean;
  module?: "recepcion" | "kidibar" | "all";
  sucursalId?: string;
  startDate?: string;
  endDate?: string;
}

// ========== SECTION DEFINITIONS ==========

/**
 * Get all available sections for a given report type.
 */
export function getAvailableSections(reportType: ExportReportType): ExportSectionInfo[] {
  const baseSections: ExportSectionInfo[] = [
    {
      id: "sales",
      label: "Ventas",
      description: "Reporte de ventas y transacciones",
      available: true,
      category: "dashboard"
    },
    {
      id: "stock",
      label: "Inventario",
      description: "Estado actual del inventario",
      available: true,
      category: "dashboard"
    },
    {
      id: "services",
      label: "Servicios",
      description: "Reporte de servicios",
      available: true,
      category: "dashboard"
    },
    {
      id: "peak_hours",
      label: "Horas Pico",
      description: "Análisis de horas de mayor actividad",
      available: true,
      category: "dashboard"
    },
    {
      id: "top_products",
      label: "Productos Top",
      description: "Productos más vendidos",
      available: true,
      category: "dashboard"
    },
    {
      id: "top_services",
      label: "Servicios Top",
      description: "Servicios más utilizados",
      available: true,
      category: "dashboard"
    },
    {
      id: "top_customers",
      label: "Clientes Top",
      description: "Clientes más activos",
      available: true,
      category: "dashboard"
    }
  ];

  const reportSections: ExportSectionInfo[] = [
    {
      id: "summary",
      label: "Resumen Ejecutivo",
      description: "Resumen ejecutivo con métricas clave",
      available: true,
      category: "reports"
    },
    {
      id: "sales",
      label: "Ventas",
      description: "Reporte avanzado de ventas y transacciones",
      available: true,
      category: "reports"
    },
    {
      id: "inventory",
      label: "Inventario (Avanzado)",
      description: "Reporte avanzado de inventario",
      available: true,
      category: "reports"
    },
    {
      id: "arqueos",
      label: "Arqueos",
      description: "Reporte de arqueos y cierres de caja",
      available: true,
      category: "reports"
    },
    {
      id: "customers",
      label: "Clientes",
      description: "Análisis avanzado de clientes",
      available: true,
      category: "reports"
    },
    {
      id: "forecasting",
      label: "Forecasting",
      description: "Predicciones y análisis de pronósticos",
      available: true,
      category: "reports"
    }
  ];

  // Check if predictions are available (only check once)
  const predictionsAvailable = checkPredictionsAvailable();
  
  // Predictions section - conditionally added to appropriate category
  const predictionsSection: ExportSectionInfo = {
    id: "predictions",
    label: "Predicciones y Análisis",
    description: "Predicciones del dashboard y pronósticos avanzados",
    available: predictionsAvailable,
    // Category matches the report type: dashboard predictions go in dashboard, reports predictions go in reports
    category: reportType === "dashboard" ? "dashboard" : "reports"
  };

  // Determine which sections to return based on report type
  if (reportType === "dashboard") {
    // For dashboard: base sections + predictions (if available)
    const sections = [...baseSections];
    if (predictionsAvailable) {
      sections.push(predictionsSection);
    }
    return sections;
  } else if (reportType === "reports") {
    // For reports: report sections + predictions (if available)
    const sections = [...reportSections];
    if (predictionsAvailable) {
      sections.push(predictionsSection);
    }
    return sections;
  } else if (reportType === "sales") {
    return baseSections.filter(s => s.id === "sales");
  } else if (reportType === "stock" || reportType === "inventory") {
    return baseSections.filter(s => s.id === "stock" || s.id === "inventory");
  } else if (reportType === "services") {
    return baseSections.filter(s => s.id === "services");
  } else if (reportType === "summary") {
    return reportSections.filter(s => s.id === "summary");
  } else if (reportType === "arqueos") {
    return reportSections.filter(s => s.id === "arqueos");
  } else if (reportType === "customers") {
    return reportSections.filter(s => s.id === "customers");
  } else if (reportType === "forecasting") {
    return reportSections.filter(s => s.id === "forecasting");
  }

  return [];
}

/**
 * Check if predictions are available (either from dashboard or forecasting reports).
 * 
 * Verifies all types of dashboard predictions:
 * - sales: checks forecast array length
 * - capacity: checks forecast array length
 * - stock: checks reorder_suggestions array length
 * - sales_by_type: checks forecast object existence
 * - peak_hours: checks forecast array length
 * - busiest_days: checks forecast array length
 * 
 * Also checks forecasting predictions from reports section.
 * 
 * @returns true if at least one type of prediction has valid data
 */
export function checkPredictionsAvailable(): boolean {
  // Get metrics store
  const metrics = get(metricsStore);
  const predictions = metrics?.predictions;
  
  // If no predictions object exists, return false
  if (!predictions) {
    return false;
  }
  
  // Check each prediction type according to its structure
  // Using optional chaining for safe property access
  const hasSales = (predictions.sales?.forecast?.length ?? 0) > 0;
  const hasCapacity = (predictions.capacity?.forecast?.length ?? 0) > 0;
  const hasStock = (predictions.stock?.reorder_suggestions?.length ?? 0) > 0;
  const hasSalesByType = !!predictions.sales_by_type?.forecast;
  const hasPeakHours = (predictions.peak_hours?.forecast?.length ?? 0) > 0;
  const hasBusiestDays = (predictions.busiest_days?.forecast?.length ?? 0) > 0;
  
  // Check if any dashboard prediction has valid data
  const hasDashboardPredictions = 
    hasSales || 
    hasCapacity || 
    hasStock || 
    hasSalesByType || 
    hasPeakHours || 
    hasBusiestDays;
  
  // Check forecasting predictions from reports section
  const forecasting = get(forecastingStore);
  const hasForecastingPredictions_ = hasForecastingPredictions(forecasting);
  
  // Return true if either dashboard or forecasting predictions are available
  return hasDashboardPredictions || hasForecastingPredictions_;
}

/**
 * Get default sections for a report type.
 */
export function getDefaultSections(
  reportType: ExportReportType,
  includePredictions: boolean = false
): ExportSection[] {
  const availableSections = getAvailableSections(reportType);
  
  // Filter out predictions if not requested
  let sections = availableSections
    .filter(s => includePredictions || s.id !== "predictions")
    .map(s => s.id);

  return sections;
}

/**
 * Generate smart defaults based on current context.
 */
export function generateSmartDefaults(
  reportType: ExportReportType,
  activeTab?: string,
  activeSubTab?: string,
  preSelectedFormat?: ExportFormat
): ExportConfiguration {
  // Check if predictions are available
  const predictionsAvailable = checkPredictionsAvailable();

  // Determine sections based on context
  let sections: ExportSection[] = [];
  
  if (reportType === "dashboard") {
    sections = getDefaultSections(reportType, predictionsAvailable);
  } else if (reportType === "reports") {
    // If in a specific tab/subtab, include that section
    if (activeTab) {
      const tabToSectionMap: Record<string, ExportSection> = {
        "summary": "summary",
        "ventas": "sales",
        "inventario": "inventory",
        "servicios": "services",
        "arqueos": "arqueos",
        "clientes": "customers",
        "forecasting": "forecasting"
      };
      
      const primarySection = tabToSectionMap[activeTab];
      if (primarySection) {
        sections = [primarySection];
      } else {
        sections = getDefaultSections(reportType, predictionsAvailable);
      }
    } else {
      sections = getDefaultSections(reportType, predictionsAvailable);
    }
  } else {
    sections = getDefaultSections(reportType, predictionsAvailable);
  }

  // Synchronize includePredictions with sections: if "predictions" is in sections, includePredictions should be true
  const includePredictionsAuto = sections.includes("predictions");

  return {
    reportType,
    format: preSelectedFormat || "excel", // Use pre-selected format or default to excel
    sections,
    includePredictions: includePredictionsAuto,
    module: undefined,
    sucursalId: undefined,
    startDate: undefined,
    endDate: undefined
  };
}

/**
 * Build export URL with configuration.
 */
export function buildExportUrl(
  config: ExportConfiguration,
  baseUrl: string
): string {
  const params = new URLSearchParams();
  
  params.append("report_type", config.reportType);
  
  if (config.sections.length > 0) {
    params.append("sections", config.sections.join(","));
  }
  
  if (config.includePredictions) {
    params.append("include_predictions", "true");
  }
  
  if (config.module) {
    params.append("module", config.module);
  }
  
  if (config.sucursalId) {
    params.append("sucursal_id", config.sucursalId);
  }
  
  if (config.startDate) {
    params.append("start_date", config.startDate);
  }
  
  if (config.endDate) {
    params.append("end_date", config.endDate);
  }

  return `${baseUrl}/exports/${config.format}?${params.toString()}`;
}

/**
 * Generate filename for export.
 */
export function generateExportFilename(
  config: ExportConfiguration
): string {
  const dateStr = new Date().toISOString().split("T")[0].replace(/-/g, "");
  const sectionsStr = config.sections.length > 0 
    ? `_${config.sections.join("-")}` 
    : "";
  const extension = config.format === "excel" ? "xlsx" : "pdf";
  
  return `kidyland_${config.reportType}${sectionsStr}_${dateStr}.${extension}`;
}

/**
 * Check if a section is available for export.
 */
export function isSectionAvailable(
  sectionId: ExportSection,
  reportType: ExportReportType
): boolean {
  const availableSections = getAvailableSections(reportType);
  const section = availableSections.find(s => s.id === sectionId);
  return section?.available ?? false;
}

