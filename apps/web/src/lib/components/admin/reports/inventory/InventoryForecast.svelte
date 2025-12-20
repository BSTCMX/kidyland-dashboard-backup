<script lang="ts">
  /**
   * InventoryForecast - Demand forecasting and stock projection.
   * 
   * Displays projected stock levels based on historical sales patterns.
   */
  import { onMount } from 'svelte';
  import { fetchInventoryForecast, type InventoryForecastReport, type InventoryForecastProduct } from '$lib/stores/reports';
  import LoadingSpinner from '$lib/components/admin/LoadingSpinner.svelte';
  import ErrorBanner from '$lib/components/admin/ErrorBanner.svelte';
  import { TrendingDown, AlertTriangle } from 'lucide-svelte';

  export let sucursalId: string | null = null;
  export let forecastDays: number = 7;

  let forecastData: InventoryForecastReport | null = null;
  let loading = false;
  let error: string | null = null;

  let previousSucursalId: string | null = null;
  let previousForecastDays: number = 7;

  async function loadForecastData() {
    loading = true;
    error = null;

    try {
      const report = await fetchInventoryForecast(sucursalId, forecastDays);
      forecastData = report;
    } catch (err: any) {
      console.error('Error loading forecast data:', err);
      error = err.message || 'Error al cargar pronóstico';
    } finally {
      loading = false;
    }
  }

  $: {
    const paramsChanged = 
      sucursalId !== previousSucursalId ||
      forecastDays !== previousForecastDays;

    if (paramsChanged) {
      previousSucursalId = sucursalId;
      previousForecastDays = forecastDays;
      loadForecastData();
    }
  }

  onMount(() => {
    loadForecastData();
  });
</script>

<div class="inventory-forecast">
  {#if loading}
    <LoadingSpinner />
  {:else if error}
    <ErrorBanner {error} />
  {:else if forecastData}
    <div class="forecast-container">
      <h3 class="section-title">Pronóstico de Demanda</h3>
      <p class="section-description">
        Proyección de {forecastData.summary.forecast_days} días basada en ventas históricas.
      </p>
      
      <!-- Summary -->
      <div class="summary-grid">
        <div class="summary-card">
          <h4 class="summary-title">Total Productos</h4>
          <div class="summary-value">{forecastData.summary.total_products}</div>
        </div>
        <div class="summary-card urgent">
          <h4 class="summary-title">Se Agotarán</h4>
          <div class="summary-value">{forecastData.summary.will_run_out_count}</div>
        </div>
      </div>

      <!-- Products at Risk -->
      {#if forecastData.forecasts && forecastData.forecasts.length > 0}
        <div class="forecasts-list">
          <h4 class="list-title">Productos en Riesgo</h4>
          {#each forecastData.forecasts.filter(p => p.will_run_out) as product (product.product_id)}
            <div class="forecast-item urgent">
              <div class="forecast-header">
                <h5 class="forecast-product-name">{product.product_name}</h5>
                <span class="forecast-badge urgent">
                  <AlertTriangle size={16} />
                  <span>Se Agotará</span>
                </span>
              </div>
              <div class="forecast-metrics">
                <div class="forecast-metric">
                  <span class="metric-label">Stock Actual:</span>
                  <span class="metric-value">{product.current_stock}</span>
                </div>
                <div class="forecast-metric">
                  <span class="metric-label">Ventas Diarias Promedio:</span>
                  <span class="metric-value">{product.daily_avg_sales.toFixed(2)}</span>
                </div>
                <div class="forecast-metric">
                  <span class="metric-label">Demanda Pronosticada:</span>
                  <span class="metric-value">{product.forecasted_demand.toFixed(0)}</span>
                </div>
                <div class="forecast-metric">
                  <span class="metric-label">Stock Proyectado:</span>
                  <span class="metric-value">{product.projected_stock.toFixed(0)}</span>
                </div>
                <div class="forecast-metric urgent">
                  <span class="metric-label">Días hasta Agotarse:</span>
                  <span class="metric-value">{product.days_until_out}</span>
                </div>
              </div>
            </div>
          {/each}
        </div>
      {/if}
    </div>
  {:else}
    <div class="placeholder-content">
      <p>No hay datos de pronóstico disponibles.</p>
    </div>
  {/if}
</div>

<style>
  .inventory-forecast {
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
    margin: 0 0 var(--spacing-xs, 0.5rem) 0;
  }

  .section-description {
    font-size: var(--text-base, 1rem);
    color: var(--text-secondary);
    margin-bottom: var(--spacing-lg, 1.5rem);
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

  .summary-card.urgent {
    border-left: 4px solid var(--accent-error, #EF4444);
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

  .forecasts-list {
    margin-top: var(--spacing-lg, 1.5rem);
  }

  .list-title {
    font-size: var(--text-lg, 1.125rem);
    font-weight: 600;
    color: var(--text-primary);
    margin: 0 0 var(--spacing-md, 1rem) 0;
  }

  .forecast-item {
    background: var(--theme-bg-secondary);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md, 8px);
    padding: var(--spacing-md, 1rem);
    margin-bottom: var(--spacing-md, 1rem);
  }

  .forecast-item.urgent {
    border-left: 4px solid var(--accent-error, #EF4444);
  }

  .forecast-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--spacing-sm, 0.75rem);
  }

  .forecast-product-name {
    font-size: var(--text-base, 1rem);
    font-weight: 600;
    color: var(--text-primary);
    margin: 0;
  }

  .forecast-badge {
    display: inline-flex;
    align-items: center;
    gap: var(--spacing-xs, 0.5rem);
    padding: var(--spacing-xs, 0.5rem) var(--spacing-sm, 0.75rem);
    border-radius: var(--radius-sm, 4px);
    font-size: var(--text-xs, 0.75rem);
    font-weight: 600;
  }

  .forecast-badge.urgent {
    background: rgba(239, 68, 68, 0.1);
    color: var(--accent-error, #EF4444);
  }

  .forecast-metrics {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: var(--spacing-sm, 0.75rem);
  }

  .forecast-metric {
    display: flex;
    justify-content: space-between;
    font-size: var(--text-sm, 0.875rem);
  }

  .forecast-metric.urgent {
    color: var(--accent-error, #EF4444);
    font-weight: 600;
  }

  .metric-label {
    color: var(--text-secondary);
  }

  .metric-value {
    font-weight: 500;
    color: var(--text-primary);
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
    .forecast-metrics {
      grid-template-columns: 1fr;
    }
  }
</style>



