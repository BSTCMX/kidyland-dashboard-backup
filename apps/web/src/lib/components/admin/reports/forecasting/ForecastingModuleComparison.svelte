<script lang="ts">
  /**
   * ForecastingModuleComparison - Side-by-side comparison view for multiple modules.
   * 
   * Displays:
   * - KPIs for each module (Recepción, KidiBar, Total)
   * - Comparison chart showing all modules
   * - Responsive layout (stacks on mobile)
   */
  import ForecastingKPIs from './ForecastingKPIs.svelte';
  import ForecastingTimeSeriesChart from './ForecastingTimeSeriesChart.svelte';
  import ForecastingCalendarHeatmap from './ForecastingCalendarHeatmap.svelte';
  import ForecastingDayOfWeekDistribution from './ForecastingDayOfWeekDistribution.svelte';
  import ForecastingPeakHoursHeatmap from './ForecastingPeakHoursHeatmap.svelte';
  import type { SegmentedPredictionsResponse } from '$lib/stores/reports';
  import type { TimeSeriesDataPoint } from '$lib/utils/charts/chartHelpers';

  export let predictionsData: SegmentedPredictionsResponse | null = null;
  export let historicalData: TimeSeriesDataPoint[] = [];
  export let forecastDays: number = 7;

  // Check if all required predictions are available
  $: hasAllData = predictionsData && 
    predictionsData.predictions.recepcion && 
    predictionsData.predictions.kidibar && 
    predictionsData.predictions.total;
</script>

{#if hasAllData && predictionsData}
  <div class="comparison-container">
    <h3 class="comparison-title">Comparación de Módulos</h3>
    
    <!-- KPIs Comparison Grid -->
    <div class="comparison-kpis">
      <div class="kpi-module">
        <ForecastingKPIs {predictionsData} moduleKey="recepcion" />
      </div>
      <div class="kpi-module">
        <ForecastingKPIs {predictionsData} moduleKey="kidibar" />
      </div>
      <div class="kpi-module">
        <ForecastingKPIs {predictionsData} moduleKey="total" />
      </div>
    </div>

    <!-- Comparison Chart Section -->
    <div class="comparison-chart-section">
      <h4 class="chart-section-title">Comparación de Revenue (Histórico vs Predicción)</h4>
      <div class="chart-container">
        <!-- Note: We'll show individual charts for now, could be enhanced to show combined chart -->
        <div class="chart-module">
          <h5 class="chart-module-title">Recepción</h5>
          <ForecastingTimeSeriesChart 
            {predictionsData} 
            moduleKey="recepcion" 
            {historicalData}
            height="300px"
          />
        </div>
        <div class="chart-module">
          <h5 class="chart-module-title">KidiBar</h5>
          <ForecastingTimeSeriesChart 
            {predictionsData} 
            moduleKey="kidibar" 
            {historicalData}
            height="300px"
          />
        </div>
        <div class="chart-module">
          <h5 class="chart-module-title">Total</h5>
          <ForecastingTimeSeriesChart 
            {predictionsData} 
            moduleKey="total" 
            {historicalData}
            height="300px"
          />
        </div>
      </div>
    </div>

    <!-- Calendar Heatmaps Comparison -->
    <div class="comparison-section">
      <h4 class="chart-section-title">Calendarios de Predicciones</h4>
      <div class="chart-container">
        <div class="chart-module">
          <h5 class="chart-module-title">Recepción</h5>
          <ForecastingCalendarHeatmap {predictionsData} moduleKey="recepcion" />
        </div>
        <div class="chart-module">
          <h5 class="chart-module-title">KidiBar</h5>
          <ForecastingCalendarHeatmap {predictionsData} moduleKey="kidibar" />
        </div>
        <div class="chart-module">
          <h5 class="chart-module-title">Total</h5>
          <ForecastingCalendarHeatmap {predictionsData} moduleKey="total" />
        </div>
      </div>
    </div>

    <!-- Day of Week Distribution Comparison -->
    <div class="comparison-section">
      <h4 class="chart-section-title">Distribución por Día de la Semana</h4>
      <div class="chart-container">
        <div class="chart-module">
          <h5 class="chart-module-title">Recepción</h5>
          <ForecastingDayOfWeekDistribution {predictionsData} moduleKey="recepcion" />
        </div>
        <div class="chart-module">
          <h5 class="chart-module-title">KidiBar</h5>
          <ForecastingDayOfWeekDistribution {predictionsData} moduleKey="kidibar" />
        </div>
        <div class="chart-module">
          <h5 class="chart-module-title">Total</h5>
          <ForecastingDayOfWeekDistribution {predictionsData} moduleKey="total" />
        </div>
      </div>
    </div>

    <!-- Peak Hours Heatmaps Comparison -->
    <div class="comparison-section comparison-peak-hours">
      <h4 class="chart-section-title">Horas Pico Previstas</h4>
      <div class="chart-container">
        <div class="chart-module">
          <h5 class="chart-module-title">Recepción</h5>
          <ForecastingPeakHoursHeatmap {predictionsData} moduleKey="recepcion" {forecastDays} />
        </div>
        <div class="chart-module">
          <h5 class="chart-module-title">KidiBar</h5>
          <ForecastingPeakHoursHeatmap {predictionsData} moduleKey="kidibar" {forecastDays} />
        </div>
        <div class="chart-module">
          <h5 class="chart-module-title">Total</h5>
          <ForecastingPeakHoursHeatmap {predictionsData} moduleKey="total" {forecastDays} />
        </div>
      </div>
    </div>
  </div>
{:else}
  <div class="no-comparison-data">
    <p>No hay suficientes datos para mostrar la comparación. Se requieren predicciones para Recepción, KidiBar y Total.</p>
  </div>
{/if}

<style>
  .comparison-container {
    width: 100%;
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xl);
  }

  .comparison-title {
    font-size: var(--text-xl);
    font-weight: 700;
    color: var(--text-primary);
    margin: 0;
  }

  .comparison-kpis {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(min(300px, 100%), 1fr));
    gap: var(--spacing-lg);
  }

  .kpi-module {
    width: 100%;
  }

  .comparison-chart-section {
    width: 100%;
  }

  .chart-section-title {
    font-size: var(--text-lg);
    font-weight: 600;
    color: var(--text-primary);
    margin: 0 0 var(--spacing-md) 0;
  }

  .chart-container {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(min(350px, 100%), 1fr));
    gap: var(--spacing-lg);
  }

  .chart-module {
    background: var(--theme-bg-elevated);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
    padding: var(--spacing-md);
    min-width: 0; /* Critical: allows grid items to shrink and enable horizontal scrolling for nested content */
  }

  .chart-module-title {
    font-size: var(--text-base);
    font-weight: 600;
    color: var(--text-primary);
    margin: 0 0 var(--spacing-sm) 0;
  }

  .no-comparison-data {
    text-align: center;
    padding: var(--spacing-xl);
    color: var(--text-secondary);
    font-style: italic;
  }

  /* Responsive adjustments */
  @media (max-width: 640px) {
    .comparison-kpis {
      grid-template-columns: 1fr;
    }

    .chart-container {
      grid-template-columns: 1fr;
    }

    /* Peak Hours Heatmaps: Stack vertically (full-width) in mobile too */
    .comparison-peak-hours .chart-container {
      grid-template-columns: 1fr; /* Single column, each heatmap takes full width */
    }

    /* For heatmaps - remove side padding from chart-module to allow edge-to-edge scroll */
    .chart-module {
      padding-left: 0;
      padding-right: 0;
      padding-top: var(--spacing-md);
      padding-bottom: var(--spacing-md);
    }

    /* Keep padding for titles */
    .chart-module-title {
      padding-left: var(--spacing-md);
      padding-right: var(--spacing-md);
      margin-bottom: var(--spacing-md);
    }

    /* Override calendar-grid-wrapper negative margins when inside chart-module */
    .chart-module :global(.calendar-grid-wrapper) {
      margin-left: 0;
      margin-right: 0;
      padding-left: var(--spacing-md);
      padding-right: var(--spacing-md);
    }

    /* Ensure peak hours heatmap container can scroll horizontally */
    .chart-module :global(.heatmap-table-container) {
      width: 100%;
      overflow-x: auto;
      overflow-y: visible;
      padding-left: var(--spacing-md);
      padding-right: var(--spacing-md);
    }
  }

  @media (min-width: 641px) and (max-width: 1024px) {
    .comparison-kpis {
      grid-template-columns: repeat(2, 1fr);
    }

    .chart-container {
      grid-template-columns: repeat(2, 1fr);
    }

    /* Peak Hours Heatmaps: Stack vertically (full-width) in tablet too, override default 2-column */
    .comparison-peak-hours .chart-container {
      grid-template-columns: 1fr; /* Single column, each heatmap takes full width */
    }
  }

  /* Desktop: Optimize peak hours heatmaps in comparison view - allow natural fitting without scroll */
  @media (min-width: 1025px) {
    .comparison-peak-hours .chart-module :global(.heatmap-table-container) {
      overflow-x: visible; /* Allow natural table fitting, consistent with individual module views */
    }
  }

  /* Peak Hours Heatmaps: Stack vertically (full-width) instead of horizontal grid */
  .comparison-peak-hours .chart-container {
    grid-template-columns: 1fr; /* Single column, each heatmap takes full width */
  }
</style>
