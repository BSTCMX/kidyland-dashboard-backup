

/**
 * Tests for metrics store.
 * 
 * Covers dashboard data, refresh, and predictions.
 */
import { describe, it, expect, beforeEach, vi } from "vitest";
import { get } from "svelte/store";
import {
  metricsStore,
  updateSales,
  updateStock,
  updateServices,
  updateAllMetrics,
  setRefreshInProgress,
  setError,
  resetRefreshCount,
  getMetricsState,
  updatePredictions,
  setPredictionInProgress,
  setPredictionError,
  formattedRevenue,
  formattedATV,
  timeSinceLastRefresh,
  type SalesReport,
  type StockReport,
  type ServicesReport,
} from "../metrics";

describe("metrics store", () => {
  beforeEach(() => {
    metricsStore.set({
      sales: null,
      stock: null,
      services: null,
      lastRefresh: null,
      refreshInProgress: false,
      refreshCount: 0,
      error: null,
      predictions: {
        sales: null,
        capacity: null,
        stock: null,
        generatedAt: null,
        forecastDays: 7,
        predictionInProgress: false,
        error: null,
      },
    });
  });

  describe("initial state", () => {
    it("should have initial state with null metrics", () => {
      const state = get(metricsStore);
      expect(state.sales).toBeNull();
      expect(state.stock).toBeNull();
      expect(state.services).toBeNull();
      expect(state.lastRefresh).toBeNull();
      expect(state.refreshInProgress).toBe(false);
      expect(state.refreshCount).toBe(0);
      expect(state.error).toBeNull();
    });
  });

  describe("updateSales", () => {
    it("should update sales report and lastRefresh", () => {
      const salesReport: SalesReport = {
        total_revenue_cents: 100000,
        average_transaction_value_cents: 5000,
        sales_count: 20,
        revenue_by_type: { service: 60000, product: 40000 },
        revenue_by_sucursal: { "suc-1": 100000 },
        revenue_by_payment_method: { cash: 80000, card: 20000 },
        period: {
          start_date: "2024-01-01",
          end_date: "2024-01-31",
        },
      };

      updateSales(salesReport);

      const state = get(metricsStore);
      expect(state.sales).toEqual(salesReport);
      expect(state.lastRefresh).toBeGreaterThan(0);
      expect(state.error).toBeNull();
    });
  });

  describe("updateStock", () => {
    it("should update stock report", () => {
      const stockReport: StockReport = {
        low_stock_alerts: [
          {
            product_id: "prod-1",
            product_name: "Test Product",
            stock_qty: 5,
            threshold_alert_qty: 10,
            sucursal_id: "suc-1",
          },
        ],
        total_products: 50,
        total_stock_value_cents: 500000,
        alerts_count: 1,
      };

      updateStock(stockReport);

      const state = get(metricsStore);
      expect(state.stock).toEqual(stockReport);
      expect(state.error).toBeNull();
    });
  });

  describe("updateServices", () => {
    it("should update services report", () => {
      const servicesReport: ServicesReport = {
        active_timers_count: 5,
        total_services: 10,
        services_by_sucursal: { "suc-1": 10 },
      };

      updateServices(servicesReport);

      const state = get(metricsStore);
      expect(state.services).toEqual(servicesReport);
      expect(state.error).toBeNull();
    });
  });

  describe("updateAllMetrics", () => {
    it("should update all metrics at once", () => {
      const salesReport: SalesReport = {
        total_revenue_cents: 100000,
        average_transaction_value_cents: 5000,
        sales_count: 20,
        revenue_by_type: {},
        revenue_by_sucursal: {},
        revenue_by_payment_method: {},
        period: { start_date: "2024-01-01", end_date: "2024-01-31" },
      };

      const stockReport: StockReport = {
        low_stock_alerts: [],
        total_products: 50,
        total_stock_value_cents: 500000,
        alerts_count: 0,
      };

      const servicesReport: ServicesReport = {
        active_timers_count: 5,
        total_services: 10,
        services_by_sucursal: {},
      };

      updateAllMetrics(salesReport, stockReport, servicesReport);

      const state = get(metricsStore);
      expect(state.sales).toEqual(salesReport);
      expect(state.stock).toEqual(stockReport);
      expect(state.services).toEqual(servicesReport);
      expect(state.lastRefresh).toBeGreaterThan(0);
      expect(state.refreshInProgress).toBe(false);
      expect(state.refreshCount).toBe(1);
      expect(state.error).toBeNull();
    });

    it("should increment refreshCount", () => {
      const emptyReport = {
        total_revenue_cents: 0,
        average_transaction_value_cents: 0,
        sales_count: 0,
        revenue_by_type: {},
        revenue_by_sucursal: {},
        revenue_by_payment_method: {},
        period: { start_date: "", end_date: "" },
      };

      updateAllMetrics(emptyReport, { low_stock_alerts: [], total_products: 0, total_stock_value_cents: 0, alerts_count: 0 }, { active_timers_count: 0, total_services: 0, services_by_sucursal: {} });

      expect(get(metricsStore).refreshCount).toBe(1);

      updateAllMetrics(emptyReport, { low_stock_alerts: [], total_products: 0, total_stock_value_cents: 0, alerts_count: 0 }, { active_timers_count: 0, total_services: 0, services_by_sucursal: {} });

      expect(get(metricsStore).refreshCount).toBe(2);
    });
  });

  describe("setRefreshInProgress", () => {
    it("should set refreshInProgress state", () => {
      setRefreshInProgress(true);
      expect(get(metricsStore).refreshInProgress).toBe(true);

      setRefreshInProgress(false);
      expect(get(metricsStore).refreshInProgress).toBe(false);
    });
  });

  describe("setError", () => {
    it("should set error and clear refreshInProgress", () => {
      setRefreshInProgress(true);
      setError("Test error");

      const state = get(metricsStore);
      expect(state.error).toBe("Test error");
      expect(state.refreshInProgress).toBe(false);
    });

    it("should clear error when set to null", () => {
      setError("Test error");
      setError(null);

      expect(get(metricsStore).error).toBeNull();
    });
  });

  describe("resetRefreshCount", () => {
    it("should reset refreshCount to 0", () => {
      const emptyReport = {
        total_revenue_cents: 0,
        average_transaction_value_cents: 0,
        sales_count: 0,
        revenue_by_type: {},
        revenue_by_sucursal: {},
        revenue_by_payment_method: {},
        period: { start_date: "", end_date: "" },
      };

      updateAllMetrics(emptyReport, { low_stock_alerts: [], total_products: 0, total_stock_value_cents: 0, alerts_count: 0 }, { active_timers_count: 0, total_services: 0, services_by_sucursal: {} });
      expect(get(metricsStore).refreshCount).toBe(1);

      resetRefreshCount();
      expect(get(metricsStore).refreshCount).toBe(0);
    });
  });

  describe("getMetricsState", () => {
    it("should return current metrics state", () => {
      const state = getMetricsState();
      expect(state).toEqual(get(metricsStore));
    });
  });

  describe("updatePredictions", () => {
    it("should update predictions", () => {
      const salesPrediction = {
        forecast: [
          { date: "2024-02-01", predicted_revenue_cents: 10000, predicted_count: 5 },
        ],
        confidence: "high" as const,
        method: "moving_average",
      };

      updatePredictions({ sales: salesPrediction }, 7);

      const state = get(metricsStore);
      expect(state.predictions.sales).toEqual(salesPrediction);
      expect(state.predictions.generatedAt).toBeGreaterThan(0);
      expect(state.predictions.forecastDays).toBe(7);
      expect(state.predictions.predictionInProgress).toBe(false);
      expect(state.predictions.error).toBeNull();
    });

    it("should update multiple predictions at once", () => {
      const salesPrediction = {
        forecast: [],
        confidence: "high" as const,
        method: "test",
      };

      const capacityPrediction = {
        forecast: [],
        confidence: "medium" as const,
        method: "test",
        utilization_rate: 0.5,
      };

      updatePredictions(
        {
          sales: salesPrediction,
          capacity: capacityPrediction,
        },
        14
      );

      const state = get(metricsStore);
      expect(state.predictions.sales).toEqual(salesPrediction);
      expect(state.predictions.capacity).toEqual(capacityPrediction);
      expect(state.predictions.forecastDays).toBe(14);
    });
  });

  describe("setPredictionInProgress", () => {
    it("should set predictionInProgress state", () => {
      setPredictionInProgress(true);
      expect(get(metricsStore).predictions.predictionInProgress).toBe(true);

      setPredictionInProgress(false);
      expect(get(metricsStore).predictions.predictionInProgress).toBe(false);
    });
  });

  describe("setPredictionError", () => {
    it("should set prediction error and clear predictionInProgress", () => {
      setPredictionInProgress(true);
      setPredictionError("Prediction error");

      const state = get(metricsStore);
      expect(state.predictions.error).toBe("Prediction error");
      expect(state.predictions.predictionInProgress).toBe(false);
    });
  });

  describe("derived stores", () => {
    describe("formattedRevenue", () => {
      it("should format revenue in dollars", () => {
        updateSales({
          total_revenue_cents: 123450,
          average_transaction_value_cents: 0,
          sales_count: 0,
          revenue_by_type: {},
          revenue_by_sucursal: {},
          revenue_by_payment_method: {},
          period: { start_date: "", end_date: "" },
        });

        expect(get(formattedRevenue)).toBe("$1234.50");
      });

      it("should return $0.00 when no sales", () => {
        expect(get(formattedRevenue)).toBe("$0.00");
      });
    });

    describe("formattedATV", () => {
      it("should format average transaction value in dollars", () => {
        updateSales({
          total_revenue_cents: 0,
          average_transaction_value_cents: 5678,
          sales_count: 0,
          revenue_by_type: {},
          revenue_by_sucursal: {},
          revenue_by_payment_method: {},
          period: { start_date: "", end_date: "" },
        });

        expect(get(formattedATV)).toBe("$56.78");
      });

      it("should return $0.00 when no sales", () => {
        expect(get(formattedATV)).toBe("$0.00");
      });
    });

    describe("timeSinceLastRefresh", () => {
      it("should return seconds ago for recent refresh", () => {
        updateSales({
          total_revenue_cents: 0,
          average_transaction_value_cents: 0,
          sales_count: 0,
          revenue_by_type: {},
          revenue_by_sucursal: {},
          revenue_by_payment_method: {},
          period: { start_date: "", end_date: "" },
        });

        const timeStr = get(timeSinceLastRefresh);
        expect(timeStr).toMatch(/\d+s ago/);
      });

      it("should return minutes ago for older refresh", () => {
        // Set lastRefresh to 2 minutes ago
        const twoMinutesAgo = Date.now() - 2 * 60 * 1000;
        metricsStore.update((state) => ({
          ...state,
          lastRefresh: twoMinutesAgo,
        }));

        const timeStr = get(timeSinceLastRefresh);
        expect(timeStr).toMatch(/\d+m ago/);
      });

      it("should return null when no refresh", () => {
        metricsStore.update((state) => ({
          ...state,
          lastRefresh: null,
        }));

        expect(get(timeSinceLastRefresh)).toBeNull();
      });
    });
  });
});

