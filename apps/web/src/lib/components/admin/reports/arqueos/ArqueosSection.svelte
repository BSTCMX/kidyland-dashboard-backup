<script lang="ts">
  /**
   * ArqueosSection - Orchestrator component for Arqueos reports.
   * 
   * Manages sub-components and respects global module filter.
   * Similar to CustomersSection pattern.
   */
  import { onMount } from 'svelte';
  import LoadingSpinner from '$lib/components/admin/LoadingSpinner.svelte';
  import ErrorBanner from '$lib/components/admin/ErrorBanner.svelte';
  import ArqueosTimeSeriesChart from './ArqueosTimeSeriesChart.svelte';
  import ArqueosModuleComparison from './ArqueosModuleComparison.svelte';
  import ArqueosHeatmap from './ArqueosHeatmap.svelte';
  import ArqueosTrends from './ArqueosTrends.svelte';
  import ArqueosAlerts from './ArqueosAlerts.svelte';
  import ArqueosRecommendations from './ArqueosRecommendations.svelte';
  import ArqueosAnomalies from './ArqueosAnomalies.svelte';
  import ArqueosByUser from './ArqueosByUser.svelte';
  import { reportsStore, fetchArqueosTimeSeries, type ArqueosTimeSeriesDataPoint } from '$lib/stores/reports';
  import type { ArqueosReport } from '$lib/stores/reports';

  export let sucursalId: string | null = null;
  export let startDate: string;
  export let endDate: string;
  export let selectedModule: "all" | "recepcion" | "kidibar" = "all";

  // Local state for arqueos data
  let arqueosData: ArqueosReport | null = null;
  let loading = false;
  let error: string | null = null;

  // Time series data
  let timeSeriesData: ArqueosTimeSeriesDataPoint[] = [];
  let timeSeriesLoading = false;
  let timeSeriesError: string | null = null;

  // Reactive statement to update when store changes
  $: {
    if ($reportsStore.arqueos) {
      arqueosData = $reportsStore.arqueos;
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
      const timeSeriesReport = await fetchArqueosTimeSeries(
        sucursalId,
        startDate,
        endDate,
        selectedModule
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
  let previousModule: "all" | "recepcion" | "kidibar" = "all";

  // Fetch when params change
  $: {
    const paramsChanged = 
      sucursalId !== previousSucursalId ||
      startDate !== previousStartDate ||
      endDate !== previousEndDate ||
      selectedModule !== previousModule;

    if (paramsChanged) {
      previousSucursalId = sucursalId;
      previousStartDate = startDate;
      previousEndDate = endDate;
      previousModule = selectedModule;
      loadTimeSeriesData();
    }
  }

  onMount(() => {
    loadTimeSeriesData();
  });
</script>

<div class="arqueos-section">
  {#if loading}
    <LoadingSpinner />
  {:else if error}
    <ErrorBanner {error} />
  {:else if arqueosData}
    <!-- Time Series Chart -->
    <div class="time-series-section">
      <h3 class="section-title">Tendencia de Discrepancias</h3>
      <ArqueosTimeSeriesChart
        data={timeSeriesData}
        metric="difference"
        height="400px"
        loading={timeSeriesLoading}
        error={timeSeriesError}
      />
    </div>

    <!-- Heatmap -->
    <ArqueosHeatmap
      {sucursalId}
      {startDate}
      {endDate}
      {selectedModule}
    />

    <!-- Module Comparison (only when selectedModule === "all") -->
    {#if selectedModule === "all"}
      <ArqueosModuleComparison
        {sucursalId}
        {startDate}
        {endDate}
      />
    {/if}

    <!-- Phase 3: Trends, Anomalies, By User -->
    <ArqueosTrends
      {sucursalId}
      endDate={endDate}
      {selectedModule}
    />

    <ArqueosAnomalies
      {sucursalId}
      {startDate}
      {endDate}
      {selectedModule}
    />

    <ArqueosByUser
      {sucursalId}
      {startDate}
      {endDate}
      {selectedModule}
    />

    <!-- Phase 4: Alerts and Recommendations -->
    <ArqueosAlerts
      {sucursalId}
      {selectedModule}
    />

    <ArqueosRecommendations
      {sucursalId}
      {selectedModule}
    />
  {:else}
    <div class="placeholder-content">
      <p>No hay datos de arqueos disponibles. Ajusta los filtros y vuelve a intentar.</p>
    </div>
  {/if}
</div>

<style>
  .arqueos-section {
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

