<script lang="ts">
  /**
   * ArqueosModuleComparison - Comparison component for arqueos by module.
   * 
   * Displays side-by-side comparison of Recepción vs KidiBar arqueos.
   * Only shown when selectedModule === "all".
   * 
   * Note: This component will fetch separate data for each module
   * to provide accurate comparison.
   */
  import { onMount } from 'svelte';
  import { fetchArqueosReport, formatPrice, type ArqueosReport } from '$lib/stores/reports';
  import LoadingSpinner from '$lib/components/admin/LoadingSpinner.svelte';
  import ErrorBanner from '$lib/components/admin/ErrorBanner.svelte';

  export let sucursalId: string | null = null;
  export let startDate: string;
  export let endDate: string;

  let recepcionData: ArqueosReport | null = null;
  let kidibarData: ArqueosReport | null = null;
  let loading = false;
  let error: string | null = null;

  async function fetchComparisonData() {
    loading = true;
    error = null;

    try {
      const [recepcion, kidibar] = await Promise.all([
        fetchArqueosReport(sucursalId, startDate, endDate, 'recepcion'),
        fetchArqueosReport(sucursalId, startDate, endDate, 'kidibar')
      ]);

      recepcionData = recepcion;
      kidibarData = kidibar;
    } catch (err: any) {
      console.error('Error fetching module comparison:', err);
      error = err.message || 'Error al cargar comparación por módulos';
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
      fetchComparisonData();
    }
  }

  onMount(() => {
    fetchComparisonData();
  });

  // Calculate discrepancy rates
  $: recepcionDiscrepancyRate = recepcionData && recepcionData.total_arqueos > 0
    ? (recepcionData.discrepancies / recepcionData.total_arqueos * 100).toFixed(1)
    : '0.0';

  $: kidibarDiscrepancyRate = kidibarData && kidibarData.total_arqueos > 0
    ? (kidibarData.discrepancies / kidibarData.total_arqueos * 100).toFixed(1)
    : '0.0';

  $: recepcionPerfectRate = recepcionData && recepcionData.total_arqueos > 0
    ? (recepcionData.perfect_matches / recepcionData.total_arqueos * 100).toFixed(1)
    : '0.0';

  $: kidibarPerfectRate = kidibarData && kidibarData.total_arqueos > 0
    ? (kidibarData.perfect_matches / kidibarData.total_arqueos * 100).toFixed(1)
    : '0.0';
</script>

<div class="arqueos-module-comparison">
  {#if loading}
    <LoadingSpinner />
  {:else if error}
    <ErrorBanner {error} />
  {:else if recepcionData && kidibarData}
    <div class="comparison-section">
      <h3 class="section-title">Comparación por Módulo</h3>
      <div class="module-comparison-grid">
        <!-- Recepción Card -->
        <div class="module-card recepcion">
          <h4 class="module-title">Recepción</h4>
          <div class="module-metrics">
            <div class="module-metric">
              <span class="metric-label">Total Arqueos:</span>
              <span class="metric-value">{recepcionData.total_arqueos}</span>
            </div>
            <div class="module-metric">
              <span class="metric-label">Coincidencias Perfectas:</span>
              <span class="metric-value">{recepcionData.perfect_matches}</span>
              <span class="metric-percentage">({recepcionPerfectRate}%)</span>
            </div>
            <div class="module-metric">
              <span class="metric-label">Discrepancias:</span>
              <span class="metric-value">{recepcionData.discrepancies}</span>
              <span class="metric-percentage">({recepcionDiscrepancyRate}%)</span>
            </div>
            <div class="module-metric">
              <span class="metric-label">Diferencia Total:</span>
              <span class="metric-value" class:positive={recepcionData.total_difference_cents > 0} class:negative={recepcionData.total_difference_cents < 0}>
                {formatPrice(recepcionData.total_difference_cents || 0)}
              </span>
            </div>
            <div class="module-metric">
              <span class="metric-label">Sistema Total:</span>
              <span class="metric-value">{formatPrice(recepcionData.total_system_cents || 0)}</span>
            </div>
            <div class="module-metric">
              <span class="metric-label">Físico Total:</span>
              <span class="metric-value">{formatPrice(recepcionData.total_physical_cents || 0)}</span>
            </div>
          </div>
        </div>

        <!-- KidiBar Card -->
        <div class="module-card kidibar">
          <h4 class="module-title">KidiBar</h4>
          <div class="module-metrics">
            <div class="module-metric">
              <span class="metric-label">Total Arqueos:</span>
              <span class="metric-value">{kidibarData.total_arqueos}</span>
            </div>
            <div class="module-metric">
              <span class="metric-label">Coincidencias Perfectas:</span>
              <span class="metric-value">{kidibarData.perfect_matches}</span>
              <span class="metric-percentage">({kidibarPerfectRate}%)</span>
            </div>
            <div class="module-metric">
              <span class="metric-label">Discrepancias:</span>
              <span class="metric-value">{kidibarData.discrepancies}</span>
              <span class="metric-percentage">({kidibarDiscrepancyRate}%)</span>
            </div>
            <div class="module-metric">
              <span class="metric-label">Diferencia Total:</span>
              <span class="metric-value" class:positive={kidibarData.total_difference_cents > 0} class:negative={kidibarData.total_difference_cents < 0}>
                {formatPrice(kidibarData.total_difference_cents || 0)}
              </span>
            </div>
            <div class="module-metric">
              <span class="metric-label">Sistema Total:</span>
              <span class="metric-value">{formatPrice(kidibarData.total_system_cents || 0)}</span>
            </div>
            <div class="module-metric">
              <span class="metric-label">Físico Total:</span>
              <span class="metric-value">{formatPrice(kidibarData.total_physical_cents || 0)}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  {:else}
    <div class="placeholder-content">
      <p>No hay datos disponibles para comparar módulos.</p>
    </div>
  {/if}
</div>

<style>
  .arqueos-module-comparison {
    width: 100%;
  }

  .comparison-section {
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

  .module-comparison-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(min(300px, 100%), 1fr));
    gap: var(--spacing-lg, 1.5rem);
  }

  .module-card {
    background: var(--theme-bg-card);
    backdrop-filter: blur(16px) saturate(150%);
    -webkit-backdrop-filter: blur(16px) saturate(150%);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-lg, 12px);
    padding: var(--spacing-lg, 1.5rem);
    box-shadow: 
      0 8px 24px rgba(0, 0, 0, 0.15),
      0 0 20px var(--glow-primary, rgba(0, 147, 247, 0.1)),
      inset 0 1px 0 rgba(255, 255, 255, 0.05);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }

  .module-card:hover {
    transform: translateY(-4px);
    border-color: rgba(0, 147, 247, 0.5);
    box-shadow: 
      0 12px 32px rgba(0, 0, 0, 0.2),
      0 0 30px var(--glow-primary, rgba(0, 147, 247, 0.2));
  }

  .module-card.recepcion {
    border-left: 4px solid var(--accent-primary, #0093F7);
  }

  .module-card.kidibar {
    border-left: 4px solid var(--accent-success, #10B981);
  }

  .module-title {
    font-size: var(--text-lg, 1.125rem);
    font-weight: 700;
    color: var(--text-primary);
    margin: 0 0 var(--spacing-md, 1rem) 0;
  }

  .module-metrics {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-sm, 0.75rem);
  }

  .module-metric {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: var(--spacing-sm, 0.75rem) 0;
    border-top: 1px solid var(--border-primary);
  }

  .module-metric:first-child {
    border-top: none;
  }

  .module-metric .metric-label {
    font-size: var(--text-sm, 0.875rem);
    color: var(--text-secondary);
    flex: 1;
  }

  .module-metric .metric-value {
    font-size: var(--text-base, 1rem);
    font-weight: 600;
    color: var(--text-primary);
    text-align: right;
  }

  .module-metric .metric-value.positive {
    color: var(--accent-success, #10B981);
  }

  .module-metric .metric-value.negative {
    color: var(--accent-error, #EF4444);
  }

  .metric-percentage {
    font-size: var(--text-sm, 0.875rem);
    color: var(--text-secondary);
    margin-left: var(--spacing-xs, 0.5rem);
  }

  .placeholder-content {
    padding: var(--spacing-2xl, 3rem);
    text-align: center;
    color: var(--text-secondary);
    font-style: italic;
  }

  @media (max-width: 768px) {
    .module-comparison-grid {
      grid-template-columns: 1fr;
    }
  }
</style>



