<script lang="ts">
  /**
   * ServicesDurationAnalysis - Average service duration analysis.
   * 
   * Displays average duration, efficiency, and duration patterns by service.
   */
  import { onMount } from 'svelte';
  import { fetchServicesDuration, type ServicesDurationReport, type ServicesDurationService } from '$lib/stores/reports';
  import LoadingSpinner from '$lib/components/admin/LoadingSpinner.svelte';
  import ErrorBanner from '$lib/components/admin/ErrorBanner.svelte';
  import { Clock, TrendingUp, TrendingDown } from 'lucide-svelte';

  export let sucursalId: string | null = null;
  export let startDate: string;
  export let endDate: string;

  let durationData: ServicesDurationReport | null = null;
  let loading = false;
  let error: string | null = null;

  let previousSucursalId: string | null = null;
  let previousStartDate: string | null = null;
  let previousEndDate: string | null = null;

  async function loadDurationData() {
    loading = true;
    error = null;

    try {
      const report = await fetchServicesDuration(sucursalId, startDate, endDate);
      durationData = report;
    } catch (err: any) {
      console.error('Error loading duration data:', err);
      error = err.message || 'Error al cargar análisis de duración';
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
      loadDurationData();
    }
  }

  onMount(() => {
    loadDurationData();
  });

  function formatDuration(minutes: number): string {
    if (minutes < 60) {
      return `${Math.round(minutes)} min`;
    }
    const hours = Math.floor(minutes / 60);
    const mins = Math.round(minutes % 60);
    if (mins === 0) {
      return `${hours} ${hours === 1 ? 'hora' : 'horas'}`;
    }
    return `${hours}h ${mins}min`;
  }

  function getEfficiencyColor(efficiency: number): string {
    if (efficiency >= 80) return 'var(--accent-success, #10B981)';
    if (efficiency >= 60) return 'var(--accent-warning, #F59E0B)';
    return 'var(--accent-error, #EF4444)';
  }
</script>

<div class="services-duration">
  {#if loading}
    <LoadingSpinner />
  {:else if error}
    <ErrorBanner {error} />
  {:else if durationData}
    <div class="duration-container">
      <h3 class="section-title">Análisis de Duración de Servicios</h3>
      
      <!-- Summary -->
      <div class="summary-grid">
        <div class="summary-card">
          <h4 class="summary-title">Total Servicios</h4>
          <div class="summary-value">{durationData.summary.total_services}</div>
        </div>
        <div class="summary-card">
          <h4 class="summary-title">Total Timers</h4>
          <div class="summary-value">{durationData.summary.total_timers}</div>
        </div>
        <div class="summary-card">
          <h4 class="summary-title">Duración Promedio</h4>
          <div class="summary-value">{formatDuration(durationData.summary.avg_duration_all)}</div>
        </div>
      </div>

      <!-- Services List -->
      {#if durationData.services && durationData.services.length > 0}
        <div class="services-list">
          <h4 class="list-title">
            <Clock size={20} />
            Duración por Servicio
          </h4>
          <div class="services-grid">
            {#each durationData.services as service (service.service_id)}
              {@const efficiencyColor = getEfficiencyColor(service.usage_efficiency)}
              <div class="service-card">
                <div class="service-header">
                  <h5 class="service-name">{service.service_name}</h5>
                  <span class="efficiency-badge" style="color: {efficiencyColor}">
                    {service.usage_efficiency.toFixed(0)}% eficiencia
                  </span>
                </div>
                <div class="service-metrics">
                  <div class="metric-item">
                    <span class="metric-label">Duración Promedio:</span>
                    <span class="metric-value">{formatDuration(service.avg_duration_minutes)}</span>
                  </div>
                  <div class="metric-item">
                    <span class="metric-label">Timers:</span>
                    <span class="metric-value">{service.timer_count}</span>
                  </div>
                  <div class="metric-item">
                    <span class="metric-label">Rango Permitido:</span>
                    <span class="metric-value">
                      {formatDuration(service.min_allowed_duration)} - {formatDuration(service.max_allowed_duration)}
                    </span>
                  </div>
                </div>
                <div class="efficiency-bar">
                  <div 
                    class="efficiency-fill" 
                    style="width: {Math.min(service.usage_efficiency, 100)}%; background-color: {efficiencyColor};"
                  ></div>
                </div>
              </div>
            {/each}
          </div>
        </div>
      {/if}
    </div>
  {:else}
    <div class="placeholder-content">
      <p>No hay datos de duración disponibles.</p>
    </div>
  {/if}
</div>

<style>
  .services-duration {
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
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
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

  .efficiency-badge {
    font-size: var(--text-xs, 0.75rem);
    font-weight: 600;
  }

  .service-metrics {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xs, 0.5rem);
    margin-bottom: var(--spacing-sm, 0.75rem);
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

  .efficiency-bar {
    width: 100%;
    height: 6px;
    background: var(--theme-bg-primary);
    border-radius: var(--radius-sm, 4px);
    overflow: hidden;
  }

  .efficiency-fill {
    height: 100%;
    transition: width 0.3s ease-in-out;
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



