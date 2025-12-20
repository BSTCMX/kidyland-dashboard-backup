<script lang="ts">
  /**
   * InventorySection - Orchestrator component for Inventory reports.
   * 
   * Manages sub-components and respects global filters.
   * Similar to ArqueosSection pattern.
   */
  import { onMount } from 'svelte';
  import LoadingSpinner from '$lib/components/admin/LoadingSpinner.svelte';
  import ErrorBanner from '$lib/components/admin/ErrorBanner.svelte';
  import InventoryTimeSeriesChart from './InventoryTimeSeriesChart.svelte';
  import InventoryTurnoverAnalysis from './InventoryTurnoverAnalysis.svelte';
  import InventoryHeatmap from './InventoryHeatmap.svelte';
  import InventoryMovementAnalysis from './InventoryMovementAnalysis.svelte';
  import InventoryReorderPoints from './InventoryReorderPoints.svelte';
  import InventoryAlerts from './InventoryAlerts.svelte';
  import InventoryForecast from './InventoryForecast.svelte';
  import InventoryRecommendations from './InventoryRecommendations.svelte';
  import { 
    reportsStore, 
    fetchInventoryTimeSeries, 
    type InventoryTimeSeriesDataPoint 
  } from '$lib/stores/reports';
  import type { StockReport } from '$lib/stores/reports';

  export let sucursalId: string | null = null;
  export let startDate: string;
  export let endDate: string;

  // Local state for stock data
  let stockData: StockReport | null = null;
  let loading = false;
  let error: string | null = null;

  // Time series data
  let timeSeriesData: InventoryTimeSeriesDataPoint[] = [];
  let timeSeriesLoading = false;
  let timeSeriesError: string | null = null;

  // Reactive statement to update when store changes
  $: {
    if ($reportsStore.stock) {
      stockData = $reportsStore.stock;
      loading = false;
      error = null;
    } else if ($reportsStore.loading) {
      loading = true;
      error = null;
    } else if ($reportsStore.error) {
      error = $reportsStore.error;
      loading = false;
    }
  }

  // Load time series data
  async function loadTimeSeriesData() {
    timeSeriesLoading = true;
    timeSeriesError = null;

    try {
      const timeSeriesReport = await fetchInventoryTimeSeries(
        sucursalId,
        startDate,
        endDate
      );

      if (timeSeriesReport) {
        timeSeriesData = timeSeriesReport.timeseries || [];
      }
    } catch (err: any) {
      console.error('Error loading time series data:', err);
      timeSeriesError = err.message || 'Error al cargar datos temporales';
    } finally {
      timeSeriesLoading = false;
    }
  }

  // Track previous params to detect changes
  let previousSucursalId: string | null = null;
  let previousStartDate: string | null = null;
  let previousEndDate: string | null = null;

  // Fetch when params change
  $: {
    const paramsChanged = 
      sucursalId !== previousSucursalId ||
      startDate !== previousStartDate ||
      endDate !== previousEndDate;

    if (paramsChanged) {
      previousSucursalId = sucursalId;
      previousStartDate = startDate;
      previousEndDate = endDate;
      loadTimeSeriesData();
    }
  }

  onMount(() => {
    loadTimeSeriesData();
  });
</script>

<div class="inventory-section">
  {#if loading}
    <LoadingSpinner />
  {:else if error}
    <ErrorBanner {error} />
  {:else if stockData}
    <!-- Time Series Chart -->
    <div class="time-series-section">
      <h3 class="section-title">Evolución de Stock</h3>
      <InventoryTimeSeriesChart
        data={timeSeriesData}
        metric="stock_qty"
        height="400px"
        loading={timeSeriesLoading}
        error={timeSeriesError}
      />
    </div>

    <!-- Turnover Analysis -->
    <InventoryTurnoverAnalysis
      {sucursalId}
      {startDate}
      {endDate}
    />

    <!-- Phase 2: Heatmap and Movement -->
    <InventoryHeatmap
      {sucursalId}
      {startDate}
      {endDate}
    />

    <InventoryMovementAnalysis
      {sucursalId}
      {startDate}
      {endDate}
    />

    <!-- Phase 3: Reorder Points and Alerts -->
    <InventoryReorderPoints
      {sucursalId}
      {startDate}
      {endDate}
    />

    <InventoryAlerts
      {sucursalId}
    />

    <!-- Phase 4: Forecast and Recommendations -->
    <InventoryForecast
      {sucursalId}
      forecastDays={7}
    />

    <InventoryRecommendations
      {sucursalId}
    />
  {:else}
    <div class="placeholder-content">
      <p>No hay datos de inventario disponibles. Ajusta los filtros y vuelve a intentar.</p>
    </div>
  {/if}
</div>

<style>
  .inventory-section {
    width: 100%;
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xl, 1.5rem);
  }

  .time-series-section {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-md, 1rem);
  }

  .section-title {
    font-size: var(--text-xl, 1.25rem);
    font-weight: 700;
    color: var(--text-primary);
    margin: 0;
  }

  .placeholder-content {
    padding: var(--spacing-2xl, 3rem);
    text-align: center;
    color: var(--text-secondary);
    font-style: italic;
  }
</style>

