<script lang="ts">
  /**
   * ServicesPeakHoursAnalysis - Advanced peak hours analysis.
   */
  import { onMount } from 'svelte';
  import { fetchServicesPeakHours, formatPrice, type ServicesPeakHoursReport } from '$lib/stores/reports';
  import LoadingSpinner from '$lib/components/admin/LoadingSpinner.svelte';
  import ErrorBanner from '$lib/components/admin/ErrorBanner.svelte';
  import { Clock, TrendingUp, TrendingDown } from 'lucide-svelte';

  export let sucursalId: string | null = null;
  export let startDate: string;
  export let endDate: string;

  let peakHoursData: ServicesPeakHoursReport | null = null;
  let loading = false;
  let error: string | null = null;

  let previousSucursalId: string | null = null;
  let previousStartDate: string | null = null;
  let previousEndDate: string | null = null;

  async function loadPeakHoursData() {
    loading = true;
    error = null;

    try {
      const report = await fetchServicesPeakHours(sucursalId, startDate, endDate);
      peakHoursData = report;
    } catch (err: any) {
      console.error('Error loading peak hours data:', err);
      error = err.message || 'Error al cargar análisis de horas pico';
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
      loadPeakHoursData();
    }
  }

  onMount(() => {
    loadPeakHoursData();
  });
</script>

<div class="services-peak-hours">
  {#if loading}
    <LoadingSpinner />
  {:else if error}
    <ErrorBanner {error} />
  {:else if peakHoursData}
    <div class="peak-hours-container">
      <h3 class="section-title">Análisis de Horas Pico</h3>
      
      <!-- Summary -->
      {#if peakHoursData.summary.peak_hour !== null}
        <div class="summary-card highlight">
          <div class="summary-icon">
            <Clock size={24} />
          </div>
          <div class="summary-content">
            <h4 class="summary-title">Hora Pico</h4>
            <div class="summary-value">{peakHoursData.summary.peak_hour}:00</div>
            <div class="summary-subtitle">{peakHoursData.summary.peak_sales_count} ventas</div>
          </div>
        </div>
      {/if}

      <!-- Peak Periods -->
      {#if peakHoursData.peak_periods && peakHoursData.peak_periods.length > 0}
        <div class="periods-section">
          <h4 class="section-subtitle">
            <TrendingUp size={18} />
            Horas de Alta Demanda
          </h4>
          <div class="periods-grid">
            {#each peakHoursData.peak_periods as period (period.hour)}
              <div class="period-card peak">
                <div class="period-hour">{period.hour}:00</div>
                <div class="period-stats">
                  <span class="period-stat">{period.sales_count} ventas</span>
                  <span class="period-stat revenue">{formatPrice(period.revenue_cents)}</span>
                </div>
              </div>
            {/each}
          </div>
        </div>
      {/if}

      <!-- Off-Peak Periods -->
      {#if peakHoursData.off_peak_periods && peakHoursData.off_peak_periods.length > 0}
        <div class="periods-section">
          <h4 class="section-subtitle">
            <TrendingDown size={18} />
            Horas de Baja Demanda
          </h4>
          <div class="periods-grid">
            {#each peakHoursData.off_peak_periods as period (period.hour)}
              <div class="period-card off-peak">
                <div class="period-hour">{period.hour}:00</div>
                <div class="period-stats">
                  <span class="period-stat">{period.sales_count} ventas</span>
                  <span class="period-stat revenue">{formatPrice(period.revenue_cents)}</span>
                </div>
              </div>
            {/each}
          </div>
        </div>
      {/if}
    </div>
  {:else}
    <div class="placeholder-content">
      <p>No hay datos de horas pico disponibles.</p>
    </div>
  {/if}
</div>

<style>
  .services-peak-hours {
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

  .summary-card {
    background: var(--theme-bg-secondary);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md, 8px);
    padding: var(--spacing-md, 1rem);
    margin-bottom: var(--spacing-lg, 1.5rem);
    display: flex;
    align-items: center;
    gap: var(--spacing-md, 1rem);
  }

  .summary-card.highlight {
    border-left: 4px solid var(--accent-primary, #0093F7);
  }

  .summary-icon {
    color: var(--accent-primary, #0093F7);
  }

  .summary-content {
    flex: 1;
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

  .summary-subtitle {
    font-size: var(--text-sm, 0.875rem);
    color: var(--text-secondary);
    margin-top: var(--spacing-xs, 0.5rem);
  }

  .periods-section {
    margin-top: var(--spacing-lg, 1.5rem);
  }

  .section-subtitle {
    font-size: var(--text-lg, 1.125rem);
    font-weight: 600;
    color: var(--text-primary);
    margin: 0 0 var(--spacing-md, 1rem) 0;
    display: flex;
    align-items: center;
    gap: var(--spacing-xs, 0.5rem);
  }

  .periods-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
    gap: var(--spacing-sm, 0.75rem);
  }

  .period-card {
    background: var(--theme-bg-secondary);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md, 8px);
    padding: var(--spacing-sm, 0.75rem);
    text-align: center;
  }

  .period-card.peak {
    border-left: 4px solid var(--accent-success, #10B981);
  }

  .period-card.off-peak {
    border-left: 4px solid var(--accent-warning, #F59E0B);
  }

  .period-hour {
    font-size: var(--text-lg, 1.125rem);
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: var(--spacing-xs, 0.5rem);
  }

  .period-stats {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xs, 0.5rem);
    font-size: var(--text-sm, 0.875rem);
  }

  .period-stat {
    color: var(--text-secondary);
  }

  .period-stat.revenue {
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
    .periods-grid {
      grid-template-columns: repeat(2, 1fr);
    }
  }
</style>



