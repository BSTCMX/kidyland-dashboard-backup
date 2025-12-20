<script lang="ts">
  /**
   * ArqueosTrends - Temporal trends component (MoM, WoW, YoY).
   */
  import { onMount } from 'svelte';
  import { fetchArqueosTrends, formatPrice, type ArqueosTrendsReport } from '$lib/stores/reports';
  import LoadingSpinner from '$lib/components/admin/LoadingSpinner.svelte';
  import ErrorBanner from '$lib/components/admin/ErrorBanner.svelte';
  import { TrendingUp, TrendingDown, Minus } from 'lucide-svelte';

  export let sucursalId: string | null = null;
  export let endDate: string;
  export let selectedModule: "all" | "recepcion" | "kidibar" = "all";

  let trendsData: ArqueosTrendsReport | null = null;
  let loading = false;
  let error: string | null = null;

  let previousSucursalId: string | null = null;
  let previousEndDate: string | null = null;
  let previousModule: "all" | "recepcion" | "kidibar" = "all";

  async function loadTrendsData() {
    loading = true;
    error = null;

    try {
      const report = await fetchArqueosTrends(sucursalId, endDate, selectedModule);
      trendsData = report;
    } catch (err: any) {
      console.error('Error loading trends data:', err);
      error = err.message || 'Error al cargar tendencias';
    } finally {
      loading = false;
    }
  }

  $: {
    const paramsChanged = 
      sucursalId !== previousSucursalId ||
      endDate !== previousEndDate ||
      selectedModule !== previousModule;

    if (paramsChanged) {
      previousSucursalId = sucursalId;
      previousEndDate = endDate;
      previousModule = selectedModule;
      loadTrendsData();
    }
  }

  onMount(() => {
    loadTrendsData();
  });

  function getTrendIcon(trend: string) {
    if (trend === "improving") return TrendingDown; // Lower discrepancy is better
    if (trend === "worsening") return TrendingUp;
    return Minus;
  }

  function getTrendColor(trend: string): string {
    if (trend === "improving") return "var(--accent-success, #10B981)";
    if (trend === "worsening") return "var(--accent-error, #EF4444)";
    return "var(--text-secondary)";
  }

  // Reactive variables for trend icons and colors
  $: momTrendIcon = trendsData ? getTrendIcon(trendsData.month_over_month.trend) : Minus;
  $: momTrendColor = trendsData ? getTrendColor(trendsData.month_over_month.trend) : "var(--text-secondary)";
  $: wowTrendIcon = trendsData ? getTrendIcon(trendsData.week_over_week.trend) : Minus;
  $: wowTrendColor = trendsData ? getTrendColor(trendsData.week_over_week.trend) : "var(--text-secondary)";
  $: yoyTrendIcon = trendsData ? getTrendIcon(trendsData.year_over_year.trend) : Minus;
  $: yoyTrendColor = trendsData ? getTrendColor(trendsData.year_over_year.trend) : "var(--text-secondary)";
</script>

<div class="arqueos-trends">
  {#if loading}
    <LoadingSpinner />
  {:else if error}
    <ErrorBanner {error} />
  {:else if trendsData}
    <div class="trends-container">
      <h3 class="section-title">Tendencias Temporales</h3>
      
      <div class="trends-grid">
        <!-- Month over Month -->
        <div class="trend-card">
          <div class="trend-header">
            <h4 class="trend-title">Mes a Mes (MoM)</h4>
            <svelte:component this={momTrendIcon} size={20} style="color: {momTrendColor}" />
          </div>
          <div class="trend-value" style="color: {momTrendColor}">
            {trendsData.month_over_month.percent_change > 0 ? '+' : ''}{trendsData.month_over_month.percent_change.toFixed(1)}%
          </div>
          <div class="trend-label">{trendsData.month_over_month.trend === "improving" ? "Mejorando" : trendsData.month_over_month.trend === "worsening" ? "Empeorando" : "Estable"}</div>
        </div>

        <!-- Week over Week -->
        <div class="trend-card">
          <div class="trend-header">
            <h4 class="trend-title">Semana a Semana (WoW)</h4>
            <svelte:component this={wowTrendIcon} size={20} style="color: {wowTrendColor}" />
          </div>
          <div class="trend-value" style="color: {wowTrendColor}">
            {trendsData.week_over_week.percent_change > 0 ? '+' : ''}{trendsData.week_over_week.percent_change.toFixed(1)}%
          </div>
          <div class="trend-label">{trendsData.week_over_week.trend === "improving" ? "Mejorando" : trendsData.week_over_week.trend === "worsening" ? "Empeorando" : "Estable"}</div>
        </div>

        <!-- Year over Year -->
        <div class="trend-card">
          <div class="trend-header">
            <h4 class="trend-title">Año a Año (YoY)</h4>
            <svelte:component this={yoyTrendIcon} size={20} style="color: {yoyTrendColor}" />
          </div>
          <div class="trend-value" style="color: {yoyTrendColor}">
            {trendsData.year_over_year.percent_change > 0 ? '+' : ''}{trendsData.year_over_year.percent_change.toFixed(1)}%
          </div>
          <div class="trend-label">{trendsData.year_over_year.trend === "improving" ? "Mejorando" : trendsData.year_over_year.trend === "worsening" ? "Empeorando" : "Estable"}</div>
        </div>
      </div>

      <div class="current-metrics">
        <h4 class="metrics-title">Métricas Actuales</h4>
        <div class="metrics-grid">
          <div class="metric-item">
            <span class="metric-label">Tasa de Discrepancias:</span>
            <span class="metric-value">{trendsData.current.discrepancy_rate.toFixed(1)}%</span>
          </div>
          <div class="metric-item">
            <span class="metric-label">Coincidencias Perfectas:</span>
            <span class="metric-value">{trendsData.current.perfect_matches}</span>
          </div>
          <div class="metric-item">
            <span class="metric-label">Discrepancias:</span>
            <span class="metric-value">{trendsData.current.discrepancies}</span>
          </div>
        </div>
      </div>
    </div>
  {:else}
    <div class="placeholder-content">
      <p>No hay datos de tendencias disponibles.</p>
    </div>
  {/if}
</div>

<style>
  .arqueos-trends {
    width: 100%;
  }

  .trends-container {
    background: var(--theme-bg-card);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-lg, 12px);
    padding: var(--spacing-lg, 1.5rem);
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  }

  .section-title {
    font-size: var(--text-xl, 1.25rem);
    font-weight: 700;
    color: var(--text-primary);
    margin: 0 0 var(--spacing-lg, 1.25rem) 0;
  }

  .trends-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(min(250px, 100%), 1fr));
    gap: var(--spacing-md, 1rem);
    margin-bottom: var(--spacing-lg, 1.25rem);
  }

  .trend-card {
    background: var(--theme-bg-secondary);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md, 8px);
    padding: var(--spacing-md, 1rem);
    text-align: center;
  }

  .trend-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--spacing-sm, 0.75rem);
  }

  .trend-title {
    font-size: var(--text-sm, 0.875rem);
    font-weight: 600;
    color: var(--text-secondary);
    margin: 0;
  }

  .trend-value {
    font-size: var(--text-2xl, 1.5rem);
    font-weight: 700;
    margin-bottom: var(--spacing-xs, 0.5rem);
  }

  .trend-label {
    font-size: var(--text-xs, 0.75rem);
    color: var(--text-secondary);
    text-transform: capitalize;
  }

  .current-metrics {
    padding-top: var(--spacing-lg, 1.25rem);
    border-top: 1px solid var(--border-primary);
  }

  .metrics-title {
    font-size: var(--text-lg, 1.125rem);
    font-weight: 600;
    color: var(--text-primary);
    margin: 0 0 var(--spacing-md, 1rem) 0;
  }

  .metrics-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: var(--spacing-md, 1rem);
  }

  .metric-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: var(--spacing-sm, 0.75rem);
    background: var(--theme-bg-secondary);
    border-radius: var(--radius-sm, 4px);
  }

  .metric-label {
    font-size: var(--text-sm, 0.875rem);
    color: var(--text-secondary);
  }

  .metric-value {
    font-size: var(--text-base, 1rem);
    font-weight: 600;
    color: var(--text-primary);
  }

  .placeholder-content {
    padding: var(--spacing-2xl, 3rem);
    text-align: center;
    color: var(--text-secondary);
    font-style: italic;
  }
</style>

