<script lang="ts">
  /**
   * CustomersSummary - Executive summary of customer metrics.
   */
  import { onMount } from 'svelte';
  import { get } from '@kidyland/utils/api';
  import { formatPrice } from '$lib/stores/reports';
  import LoadingSpinner from '$lib/components/admin/LoadingSpinner.svelte';
  import ErrorBanner from '$lib/components/admin/ErrorBanner.svelte';

  export let sucursalId: string | null = null;
  export let startDate: string | null = null;
  export let endDate: string | null = null;

  interface CustomersSummary {
    total_unique_customers: number;
    recepcion_unique: number;
    kidibar_unique: number;
    new_customers: number;
    recepcion_new: number;
    kidibar_new: number;
    total_revenue_cents: number;
    recepcion_revenue_cents: number;
    kidibar_revenue_cents: number;
    avg_revenue_per_customer_cents: number;
    period: {
      start_date: string;
      end_date: string;
    };
  }

  let loading = true;
  let error: string | null = null;
  let summary: CustomersSummary | null = null;

  async function fetchSummary() {
    loading = true;
    error = null;

    try {
      const params = new URLSearchParams();
      if (sucursalId) params.append('sucursal_id', sucursalId);
      if (startDate) params.append('start_date', startDate);
      if (endDate) params.append('end_date', endDate);

      summary = await get<CustomersSummary>(`/reports/customers/summary?${params.toString()}`);
    } catch (err: any) {
      error = err.message || 'Error al cargar resumen de clientes';
    } finally {
      loading = false;
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
      fetchSummary();
    }
  }

  onMount(() => {
    fetchSummary();
  });
</script>

<div class="customers-summary-container">
  {#if loading}
    <LoadingSpinner />
  {:else if error}
    <ErrorBanner {error} />
  {:else if summary}
    <div class="summary-grid">
      <!-- Total Unique Customers -->
      <div class="metric-card">
        <h3 class="metric-title">Clientes Únicos</h3>
        <div class="metric-value">{summary.total_unique_customers}</div>
        <div class="metric-breakdown">
          <div class="breakdown-item">
            <span class="breakdown-label">Recepción:</span>
            <span class="breakdown-value">{summary.recepcion_unique}</span>
          </div>
          <div class="breakdown-item">
            <span class="breakdown-label">KidiBar:</span>
            <span class="breakdown-value">{summary.kidibar_unique}</span>
          </div>
        </div>
      </div>

      <!-- New Customers -->
      <div class="metric-card">
        <h3 class="metric-title">Clientes Nuevos</h3>
        <div class="metric-value">{summary.new_customers}</div>
        <div class="metric-breakdown">
          <div class="breakdown-item">
            <span class="breakdown-label">Recepción:</span>
            <span class="breakdown-value">{summary.recepcion_new}</span>
          </div>
          <div class="breakdown-item">
            <span class="breakdown-label">KidiBar:</span>
            <span class="breakdown-value">{summary.kidibar_new}</span>
          </div>
        </div>
      </div>

      <!-- Total Revenue -->
      <div class="metric-card">
        <h3 class="metric-title">Revenue Total</h3>
        <div class="metric-value">{formatPrice(summary.total_revenue_cents)}</div>
        <div class="metric-breakdown">
          <div class="breakdown-item">
            <span class="breakdown-label">Recepción:</span>
            <span class="breakdown-value">{formatPrice(summary.recepcion_revenue_cents)}</span>
          </div>
          <div class="breakdown-item">
            <span class="breakdown-label">KidiBar:</span>
            <span class="breakdown-value">{formatPrice(summary.kidibar_revenue_cents)}</span>
          </div>
        </div>
      </div>

      <!-- Average Revenue per Customer -->
      <div class="metric-card">
        <h3 class="metric-title">Revenue Promedio por Cliente</h3>
        <div class="metric-value">{formatPrice(summary.avg_revenue_per_customer_cents)}</div>
        <div class="metric-subtitle">
          {summary.total_unique_customers > 0 
            ? `Basado en ${summary.total_unique_customers} clientes únicos`
            : 'Sin datos disponibles'}
        </div>
      </div>
    </div>
  {:else}
    <div class="empty-state">
      <p>No hay datos disponibles para el período seleccionado.</p>
    </div>
  {/if}
</div>

<style>
  .customers-summary-container {
    width: 100%;
  }

  .summary-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: var(--spacing-lg);
  }

  .metric-card {
    padding: var(--spacing-lg);
    background: var(--theme-bg-card);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
    box-shadow: var(--shadow-md);
    transition: all 0.2s ease;
  }

  .metric-card:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-lg);
    border-color: var(--accent-primary);
  }

  .metric-title {
    font-size: var(--text-sm);
    font-weight: 500;
    color: var(--text-secondary);
    margin-bottom: var(--spacing-sm);
  }

  .metric-value {
    font-size: var(--text-2xl);
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: var(--spacing-md);
  }

  .metric-breakdown {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xs);
    padding-top: var(--spacing-sm);
    border-top: 1px solid var(--border-primary);
  }

  .breakdown-item {
    display: flex;
    justify-content: space-between;
    font-size: var(--text-sm);
  }

  .breakdown-label {
    color: var(--text-secondary);
  }

  .breakdown-value {
    font-weight: 500;
    color: var(--text-primary);
  }

  .metric-subtitle {
    font-size: var(--text-xs);
    color: var(--text-secondary);
    margin-top: var(--spacing-xs);
  }

  .empty-state {
    text-align: center;
    padding: var(--spacing-xl);
    color: var(--text-secondary);
  }

  @media (max-width: 768px) {
    .summary-grid {
      grid-template-columns: 1fr;
    }
  }
</style>

