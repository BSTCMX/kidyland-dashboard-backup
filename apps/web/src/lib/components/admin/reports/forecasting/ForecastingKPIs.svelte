<script lang="ts">
  /**
   * ForecastingKPIs - Displays key prediction metrics.
   * 
   * Shows KPIs for sales predictions (revenue, count, ATV, etc.)
   * Responsive grid layout - single column on mobile, multiple on desktop.
   */
  import type { SegmentedPredictionsResponse } from '$lib/stores/reports';
  import { formatPrice } from '$lib/stores/reports';
  import { TrendingUp, TrendingDown, Minus } from 'lucide-svelte';

  export let predictionsData: SegmentedPredictionsResponse | null = null;
  export let moduleKey: "recepcion" | "kidibar" | "total" | null = null;

  // Calculate KPIs from prediction data
  $: kpis = calculateKPIs(predictionsData, moduleKey);

  function calculateKPIs(
    data: SegmentedPredictionsResponse | null,
    key: string | null
  ): {
    totalRevenue: number;
    totalCount: number;
    avgRevenue: number;
    avgCount: number;
    confidence: "high" | "medium" | "low";
  } | null {
    if (!data || !key || !data.predictions[key]?.sales) {
      return null;
    }

    const salesPred = data.predictions[key].sales;
    if (!salesPred || !salesPred.forecast || !Array.isArray(salesPred.forecast)) {
      return null;
    }

    const forecast = salesPred.forecast;
    const totalRevenue = forecast.reduce((sum: number, day: any) => sum + (day.predicted_revenue_cents || 0), 0);
    const totalCount = forecast.reduce((sum: number, day: any) => sum + (day.predicted_count || 0), 0);
    const days = forecast.length;

    return {
      totalRevenue,
      totalCount,
      avgRevenue: days > 0 ? totalRevenue / days : 0,
      avgCount: days > 0 ? totalCount / days : 0,
      confidence: salesPred.confidence || data.overall_confidence,
    };
  }

  function getModuleLabel(key: string | null): string {
    switch (key) {
      case "recepcion":
        return "Recepción";
      case "kidibar":
        return "KidiBar";
      case "total":
        return "Total";
      default:
        return "Predicción";
    }
  }

  function getConfidenceColor(confidence: "high" | "medium" | "low"): string {
    switch (confidence) {
      case "high":
        return "#10b981";
      case "medium":
        return "#f59e0b";
      case "low":
        return "#ef4444";
      default:
        return "#6b7280";
    }
  }
</script>

{#if kpis}
  <div class="kpis-container">
    <h4 class="kpis-title">{getModuleLabel(moduleKey)}</h4>
    <div class="kpis-grid">
      <div class="kpi-card">
        <div class="kpi-label">Revenue Total</div>
        <div class="kpi-value">{formatPrice(kpis.totalRevenue)}</div>
        <div class="kpi-subtitle">En {predictionsData?.forecast_days || 0} días</div>
      </div>

      <div class="kpi-card">
        <div class="kpi-label">Ventas Totales</div>
        <div class="kpi-value">{kpis.totalCount.toLocaleString()}</div>
        <div class="kpi-subtitle">Transacciones previstas</div>
      </div>

      <div class="kpi-card">
        <div class="kpi-label">Revenue Promedio/Día</div>
        <div class="kpi-value">{formatPrice(kpis.avgRevenue)}</div>
        <div class="kpi-subtitle">Promedio diario</div>
      </div>

      <div class="kpi-card">
        <div class="kpi-label">Ventas Promedio/Día</div>
        <div class="kpi-value">{kpis.avgCount.toFixed(1)}</div>
        <div class="kpi-subtitle">Transacciones diarias</div>
      </div>

      <div class="kpi-card">
        <div class="kpi-label">Confianza</div>
        <div class="kpi-value" style="color: {getConfidenceColor(kpis.confidence)};">
          {kpis.confidence.toUpperCase()}
        </div>
        <div class="kpi-subtitle">Nivel de confianza</div>
      </div>
    </div>
  </div>
{/if}

<style>
  .kpis-container {
    width: 100%;
    margin-bottom: var(--spacing-lg);
  }

  .kpis-title {
    font-size: var(--text-lg);
    font-weight: 700;
    color: var(--text-primary);
    margin: 0 0 var(--spacing-md) 0;
  }

  .kpis-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(min(200px, 100%), 1fr));
    gap: var(--spacing-md);
  }

  .kpi-card {
    background: var(--theme-bg-elevated);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
    padding: var(--spacing-md);
    transition: all 0.2s;
  }

  .kpi-card:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-md);
    border-color: var(--accent-primary);
  }

  .kpi-label {
    font-size: var(--text-xs);
    color: var(--text-secondary);
    font-weight: 500;
    margin-bottom: var(--spacing-xs);
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .kpi-value {
    font-size: var(--text-xl);
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: var(--spacing-xs);
    line-height: 1.2;
  }

  .kpi-subtitle {
    font-size: var(--text-xs);
    color: var(--text-secondary);
    font-style: italic;
  }

  /* Responsive adjustments */
  @media (max-width: 640px) {
    .kpis-grid {
      grid-template-columns: 1fr;
    }

    .kpi-value {
      font-size: var(--text-lg);
    }
  }

  @media (min-width: 641px) and (max-width: 1024px) {
    .kpis-grid {
      grid-template-columns: repeat(2, 1fr);
    }
  }
</style>



