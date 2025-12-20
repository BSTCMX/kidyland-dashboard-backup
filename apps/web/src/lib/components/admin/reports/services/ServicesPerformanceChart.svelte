<script lang="ts">
  /**
   * ServicesPerformanceChart - Revenue and popularity analysis by service.
   */
  import { onMount } from 'svelte';
  import { fetchServicesPerformance, formatPrice, type ServicesPerformanceReport } from '$lib/stores/reports';
  import LoadingSpinner from '$lib/components/admin/LoadingSpinner.svelte';
  import ErrorBanner from '$lib/components/admin/ErrorBanner.svelte';
  import { BarChart3, TrendingUp } from 'lucide-svelte';

  export let sucursalId: string | null = null;
  export let startDate: string;
  export let endDate: string;

  let performanceData: ServicesPerformanceReport | null = null;
  let loading = false;
  let error: string | null = null;

  let previousSucursalId: string | null = null;
  let previousStartDate: string | null = null;
  let previousEndDate: string | null = null;

  async function loadPerformanceData() {
    loading = true;
    error = null;

    try {
      const report = await fetchServicesPerformance(sucursalId, startDate, endDate);
      performanceData = report;
    } catch (err: any) {
      console.error('Error loading performance data:', err);
      error = err.message || 'Error al cargar datos de performance';
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
      loadPerformanceData();
    }
  }

  onMount(() => {
    loadPerformanceData();
  });
</script>

<div class="services-performance">
  {#if loading}
    <LoadingSpinner />
  {:else if error}
    <ErrorBanner {error} />
  {:else if performanceData}
    <div class="performance-container">
      <h3 class="section-title">Performance por Servicio</h3>
      
      <!-- Summary -->
      <div class="summary-grid">
        <div class="summary-card">
          <h4 class="summary-title">Total Servicios</h4>
          <div class="summary-value">{performanceData.summary.total_services}</div>
        </div>
        <div class="summary-card">
          <h4 class="summary-title">Total Ventas</h4>
          <div class="summary-value">{performanceData.summary.total_sales}</div>
        </div>
        <div class="summary-card">
          <h4 class="summary-title">Revenue Total</h4>
          <div class="summary-value">{formatPrice(performanceData.summary.total_revenue_cents)}</div>
        </div>
      </div>

      <!-- Top Services -->
      {#if performanceData.services && performanceData.services.length > 0}
        <div class="services-list">
          <h4 class="list-title">
            <BarChart3 size={20} />
            Servicios por Performance
          </h4>
          <div class="services-grid">
            {#each performanceData.services.slice(0, 10) as service (service.service_id)}
              <div class="service-card">
                <div class="service-header">
                  <h5 class="service-name">{service.service_name}</h5>
                  <span class="popularity-rank">#{service.popularity_rank}</span>
                </div>
                <div class="service-metrics">
                  <div class="metric-item">
                    <span class="metric-label">Ventas:</span>
                    <span class="metric-value">{service.sales_count}</span>
                  </div>
                  <div class="metric-item">
                    <span class="metric-label">Revenue:</span>
                    <span class="metric-value revenue">{formatPrice(service.revenue_cents)}</span>
                  </div>
                </div>
              </div>
            {/each}
          </div>
        </div>
      {/if}
    </div>
  {:else}
    <div class="placeholder-content">
      <p>No hay datos de performance disponibles.</p>
    </div>
  {/if}
</div>

<style>
  .services-performance {
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
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
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

  .services-list {
    margin-top: var(--spacing-lg, 1.5rem);
  }

  .list-title {
    font-size: var(--text-lg, 1.125rem);
    font-weight: 600;
    color: var(--text-primary);
    margin: 0 0 var(--spacing-md, 1rem) 0;
    display: flex;
    align-items: center;
    gap: var(--spacing-xs, 0.5rem);
  }

  .services-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
    gap: var(--spacing-md, 1rem);
  }

  .service-card {
    background: var(--theme-bg-secondary);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md, 8px);
    padding: var(--spacing-md, 1rem);
  }

  .service-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--spacing-sm, 0.75rem);
  }

  .service-name {
    font-size: var(--text-base, 1rem);
    font-weight: 600;
    color: var(--text-primary);
    margin: 0;
  }

  .popularity-rank {
    font-size: var(--text-sm, 0.875rem);
    color: var(--text-secondary);
    font-weight: 500;
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

  .metric-value.revenue {
    color: var(--accent-primary, #0093F7);
    font-weight: 600;
  }

  .placeholder-content {
    text-align: center;
    padding: var(--spacing-xl, 2rem);
    color: var(--text-secondary);
    font-style: italic;
  }

  @media (max-width: 768px) {
    .summary-grid {
      grid-template-columns: 1fr;
    }
    .services-grid {
      grid-template-columns: 1fr;
    }
  }
</style>



