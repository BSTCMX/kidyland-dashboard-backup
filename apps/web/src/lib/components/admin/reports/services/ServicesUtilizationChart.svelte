<script lang="ts">
  /**
   * ServicesUtilizationChart - Utilization analysis for services.
   * 
   * Displays utilization rate, active timers, and capacity metrics per service.
   */
  import { onMount } from 'svelte';
  import { fetchServicesUtilization, formatPrice, type ServicesUtilizationReport, type ServicesUtilizationService } from '$lib/stores/reports';
  import LoadingSpinner from '$lib/components/admin/LoadingSpinner.svelte';
  import ErrorBanner from '$lib/components/admin/ErrorBanner.svelte';
  import { Activity, TrendingUp, TrendingDown } from 'lucide-svelte';

  export let sucursalId: string | null = null;
  export let startDate: string;
  export let endDate: string;

  let utilizationData: ServicesUtilizationReport | null = null;
  let loading = false;
  let error: string | null = null;

  let previousSucursalId: string | null = null;
  let previousStartDate: string | null = null;
  let previousEndDate: string | null = null;

  async function loadUtilizationData() {
    loading = true;
    error = null;

    try {
      const report = await fetchServicesUtilization(sucursalId, startDate, endDate);
      utilizationData = report;
    } catch (err: any) {
      console.error('Error loading utilization data:', err);
      error = err.message || 'Error al cargar análisis de utilización';
    } finally {
      loading = false;
    }
  }

  $: {
    const paramsChanged = 
      sucursalId !== previousSucursalId ||
      startDate !== previousStartDate ||
      endDate !== previousEndDate;

    if (paramsChanged) {
      previousSucursalId = sucursalId;
      previousStartDate = startDate;
      previousEndDate = endDate;
      loadUtilizationData();
    }
  }

  onMount(() => {
    loadUtilizationData();
  });

  function getUtilizationColor(rate: number): string {
    if (rate > 80) return "var(--accent-error, #EF4444)";
    if (rate > 50) return "var(--accent-warning, #F59E0B)";
    if (rate > 20) return "var(--accent-success, #10B981)";
    return "var(--text-secondary)";
  }

  function getUtilizationLabel(rate: number): string {
    if (rate > 80) return "Alta";
    if (rate > 50) return "Media";
    if (rate > 20) return "Normal";
    return "Baja";
  }
</script>

<div class="services-utilization">
  {#if loading}
    <LoadingSpinner />
  {:else if error}
    <ErrorBanner {error} />
  {:else if utilizationData}
    <div class="utilization-container">
      <h3 class="section-title">Análisis de Utilización de Servicios</h3>
      
      <!-- Summary Cards -->
      <div class="summary-grid">
        <div class="summary-card">
          <h4 class="summary-title">Total Servicios</h4>
          <div class="summary-value">{utilizationData.summary.total_services}</div>
        </div>
        <div class="summary-card">
          <h4 class="summary-title">Utilización Promedio</h4>
          <div class="summary-value">{utilizationData.summary.average_utilization.toFixed(1)}%</div>
        </div>
        <div class="summary-card high">
          <h4 class="summary-title">Alta Utilización</h4>
          <div class="summary-value">{utilizationData.summary.high_utilization_count}</div>
        </div>
        <div class="summary-card low">
          <h4 class="summary-title">Baja Utilización</h4>
          <div class="summary-value">{utilizationData.summary.low_utilization_count}</div>
        </div>
        <div class="summary-card">
          <h4 class="summary-title">Utilización Normal</h4>
          <div class="summary-value">{utilizationData.summary.normal_utilization_count}</div>
        </div>
      </div>

      <!-- Services List -->
      <div class="services-list-section">
        <h4 class="list-title">Servicios por Utilización</h4>
        <div class="services-grid">
          {#each utilizationData.services as service (service.service_id)}
            {@const utilizationColor = getUtilizationColor(service.utilization_rate)}
            {@const utilizationLabel = getUtilizationLabel(service.utilization_rate)}
            <div class="service-card">
              <div class="service-header">
                <h5 class="service-name">{service.service_name}</h5>
                <span class="utilization-badge" style="color: {utilizationColor}">
                  {utilizationLabel}
                </span>
              </div>
              <div class="service-metrics">
                <div class="metric-item">
                  <span class="metric-label">Utilización:</span>
                  <span class="metric-value" style="color: {utilizationColor}">
                    {service.utilization_rate.toFixed(1)}%
                  </span>
                </div>
                <div class="metric-item">
                  <span class="metric-label">Timers Activos:</span>
                  <span class="metric-value">{service.active_timers} / {service.max_capacity}</span>
                </div>
                <div class="metric-item">
                  <span class="metric-label">Ventas:</span>
                  <span class="metric-value">{service.total_sales}</span>
                </div>
                <div class="metric-item">
                  <span class="metric-label">Revenue:</span>
                  <span class="metric-value">{formatPrice(service.revenue_cents)}</span>
                </div>
              </div>
              <div class="utilization-bar">
                <div 
                  class="utilization-fill" 
                  style="width: {Math.min(service.utilization_rate, 100)}%; background-color: {utilizationColor};"
                ></div>
              </div>
            </div>
          {/each}
        </div>
      </div>
    </div>
  {:else}
    <div class="placeholder-content">
      <p>No hay datos de utilización disponibles.</p>
    </div>
  {/if}
</div>

<style>
  .services-utilization {
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
    margin: 0 0 var(--spacing-lg, 1.5rem) 0;
  }

  .summary-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: var(--spacing-md, 1rem);
    margin-bottom: var(--spacing-lg, 1.5rem);
  }

  .summary-card {
    background: var(--theme-bg-secondary);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md, 8px);
    padding: var(--spacing-md, 1rem);
    text-align: center;
  }

  .summary-card.high {
    border-left: 4px solid var(--accent-error, #EF4444);
  }

  .summary-card.low {
    border-left: 4px solid var(--accent-success, #10B981);
  }

  .summary-title {
    font-size: var(--text-sm, 0.875rem);
    color: var(--text-secondary);
    margin: 0 0 var(--spacing-xs, 0.5rem) 0;
  }

  .summary-value {
    font-size: var(--text-2xl, 1.5rem);
    font-weight: 700;
    color: var(--text-primary);
  }

  .services-list-section {
    margin-top: var(--spacing-lg, 1.5rem);
  }

  .list-title {
    font-size: var(--text-lg, 1.125rem);
    font-weight: 600;
    color: var(--text-primary);
    margin: 0 0 var(--spacing-md, 1rem) 0;
  }

  .services-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: var(--spacing-md, 1rem);
  }

  .service-card {
    background: var(--theme-bg-secondary);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md, 8px);
    padding: var(--spacing-md, 1rem);
    display: flex;
    flex-direction: column;
    gap: var(--spacing-sm, 0.75rem);
  }

  .service-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--spacing-xs, 0.5rem);
  }

  .service-name {
    font-size: var(--text-base, 1rem);
    font-weight: 600;
    color: var(--text-primary);
    margin: 0;
  }

  .utilization-badge {
    font-size: var(--text-xs, 0.75rem);
    font-weight: 600;
    padding: var(--spacing-xs, 0.5rem) var(--spacing-sm, 0.75rem);
    border-radius: var(--radius-sm, 4px);
    background: var(--theme-bg-primary);
  }

  .service-metrics {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xs, 0.5rem);
  }

  .metric-item {
    display: flex;
    justify-content: space-between;
    font-size: var(--text-sm, 0.875rem);
  }

  .metric-label {
    color: var(--text-secondary);
  }

  .metric-value {
    font-weight: 500;
    color: var(--text-primary);
  }

  .utilization-bar {
    width: 100%;
    height: 8px;
    background: var(--theme-bg-primary);
    border-radius: var(--radius-sm, 4px);
    overflow: hidden;
    margin-top: var(--spacing-xs, 0.5rem);
  }

  .utilization-fill {
    height: 100%;
    transition: width 0.3s ease;
  }

  .placeholder-content {
    text-align: center;
    padding: var(--spacing-xl, 2rem);
    color: var(--text-secondary);
    font-style: italic;
  }

  @media (max-width: 768px) {
    .summary-grid {
      grid-template-columns: repeat(2, 1fr);
    }

    .services-grid {
      grid-template-columns: 1fr;
    }
  }
</style>

