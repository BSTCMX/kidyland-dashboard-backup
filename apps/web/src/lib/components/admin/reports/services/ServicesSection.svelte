<script lang="ts">
  /**
   * ServicesSection - Orchestrator component for Services reports.
   * 
   * Manages sub-components and respects global filters.
   * Similar to ArqueosSection pattern.
   */
  import { onMount } from 'svelte';
  import LoadingSpinner from '$lib/components/admin/LoadingSpinner.svelte';
  import ErrorBanner from '$lib/components/admin/ErrorBanner.svelte';
  import ServicesTimeSeriesChart from './ServicesTimeSeriesChart.svelte';
  import ServicesUtilizationChart from './ServicesUtilizationChart.svelte';
  import ServicesPerformanceChart from './ServicesPerformanceChart.svelte';
  import ServicesDurationAnalysis from './ServicesDurationAnalysis.svelte';
  import ServicesCapacityHeatmap from './ServicesCapacityHeatmap.svelte';
  import ServicesPeakHoursAnalysis from './ServicesPeakHoursAnalysis.svelte';
  import ServicesRecommendations from './ServicesRecommendations.svelte';
  import { 
    reportsStore, 
    fetchServicesTimeSeries, 
    type ServicesTimeSeriesDataPoint 
  } from '$lib/stores/reports';
  import type { ServicesReport } from '$lib/stores/reports';

  export let sucursalId: string | null = null;
  export let startDate: string;
  export let endDate: string;

  // Local state for services data
  let servicesData: ServicesReport | null = null;
  let loading = false;
  let error: string | null = null;

  // Time series data
  let timeSeriesData: ServicesTimeSeriesDataPoint[] = [];
  let timeSeriesLoading = false;
  let timeSeriesError: string | null = null;

  // Reactive statement to update when store changes
  $: {
    if ($reportsStore.services) {
      servicesData = $reportsStore.services;
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
      const timeSeriesReport = await fetchServicesTimeSeries(
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

<div class="services-section">
  {#if loading}
    <LoadingSpinner />
  {:else if error}
    <ErrorBanner {error} />
  {:else if servicesData}
    <!-- Time Series Chart -->
    <div class="time-series-section">
      <h3 class="section-title">Evolución de Servicios</h3>
      <ServicesTimeSeriesChart
        data={timeSeriesData}
        metric="revenue"
        height="400px"
        loading={timeSeriesLoading}
        error={timeSeriesError}
      />
    </div>

    <!-- Utilization Analysis -->
    <ServicesUtilizationChart
      {sucursalId}
      {startDate}
      {endDate}
    />

    <!-- Phase 2: Performance and Duration -->
    <ServicesPerformanceChart
      {sucursalId}
      {startDate}
      {endDate}
    />

    <ServicesDurationAnalysis
      {sucursalId}
      {startDate}
      {endDate}
    />

    <!-- Phase 3: Capacity and Peak Hours -->
    <ServicesCapacityHeatmap
      {sucursalId}
      {startDate}
      {endDate}
    />

    <ServicesPeakHoursAnalysis
      {sucursalId}
      {startDate}
      {endDate}
    />

    <!-- Phase 4: Recommendations -->
    <ServicesRecommendations
      {sucursalId}
    />
  {:else}
    <div class="placeholder-content">
      <p>No hay datos de servicios disponibles. Ajusta los filtros y vuelve a intentar.</p>
    </div>
  {/if}
</div>

<style>
  .services-section {
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

