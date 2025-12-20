<script lang="ts">
  /**
   * ArqueosAnomalies - Anomaly detection component.
   */
  import { onMount } from 'svelte';
  import { fetchArqueosAnomalies, formatPrice, type ArqueosAnomaliesReport } from '$lib/stores/reports';
  import LoadingSpinner from '$lib/components/admin/LoadingSpinner.svelte';
  import ErrorBanner from '$lib/components/admin/ErrorBanner.svelte';
  import { AlertTriangle } from 'lucide-svelte';

  export let sucursalId: string | null = null;
  export let startDate: string;
  export let endDate: string;
  export let selectedModule: "all" | "recepcion" | "kidibar" = "all";

  let anomaliesData: ArqueosAnomaliesReport | null = null;
  let loading = false;
  let error: string | null = null;

  let previousSucursalId: string | null = null;
  let previousStartDate: string | null = null;
  let previousEndDate: string | null = null;
  let previousModule: "all" | "recepcion" | "kidibar" = "all";

  async function loadAnomaliesData() {
    loading = true;
    error = null;

    try {
      const report = await fetchArqueosAnomalies(sucursalId, startDate, endDate, selectedModule);
      anomaliesData = report;
    } catch (err: any) {
      console.error('Error loading anomalies data:', err);
      error = err.message || 'Error al cargar anomalías';
    } finally {
      loading = false;
    }
  }

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
      loadAnomaliesData();
    }
  }

  onMount(() => {
    loadAnomaliesData();
  });
</script>

<div class="arqueos-anomalies">
  {#if loading}
    <LoadingSpinner />
  {:else if error}
    <ErrorBanner {error} />
  {:else if anomaliesData}
    <div class="anomalies-container">
      <h3 class="section-title">Detección de Anomalías</h3>
      
      {#if anomaliesData.anomalies.length === 0}
        <div class="no-anomalies">
          <p>No se detectaron anomalías en el período seleccionado.</p>
        </div>
      {:else}
        <div class="anomalies-summary">
          <div class="summary-item">
            <span class="summary-label">Anomalías detectadas:</span>
            <span class="summary-value">{anomaliesData.anomalies.length}</span>
          </div>
          <div class="summary-item">
            <span class="summary-label">Severas:</span>
            <span class="summary-value severe">
              {anomaliesData.anomalies.filter(a => a.severity === "severe").length}
            </span>
          </div>
          <div class="summary-item">
            <span class="summary-label">Moderadas:</span>
            <span class="summary-value moderate">
              {anomaliesData.anomalies.filter(a => a.severity === "moderate").length}
            </span>
          </div>
        </div>

        <div class="anomalies-list">
          {#each anomaliesData.anomalies as anomaly (anomaly.date)}
            <div class="anomaly-item" class:severe={anomaly.severity === "severe"}>
              <div class="anomaly-header">
                <div class="anomaly-date">
                  <AlertTriangle size={20} style="color: {anomaly.severity === 'severe' ? 'var(--accent-error, #EF4444)' : 'var(--accent-warning, #F59E0B)'}" />
                  <span>{new Date(anomaly.date).toLocaleDateString('es-ES', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}</span>
                </div>
                <span class="anomaly-severity" class:severe={anomaly.severity === "severe"}>
                  {anomaly.severity === "severe" ? "Severa" : "Moderada"}
                </span>
              </div>
              <div class="anomaly-details">
                <div class="anomaly-detail">
                  <span class="detail-label">Diferencia:</span>
                  <span class="detail-value" class:positive={anomaly.difference_cents > 0} class:negative={anomaly.difference_cents < 0}>
                    {formatPrice(anomaly.difference_cents)}
                  </span>
                </div>
                <div class="anomaly-detail">
                  <span class="detail-label">Sistema:</span>
                  <span class="detail-value">{formatPrice(anomaly.system_total_cents)}</span>
                </div>
                <div class="anomaly-detail">
                  <span class="detail-label">Físico:</span>
                  <span class="detail-value">{formatPrice(anomaly.physical_count_cents)}</span>
                </div>
                <div class="anomaly-detail">
                  <span class="detail-label">Z-Score:</span>
                  <span class="detail-value">{anomaly.z_score.toFixed(2)}</span>
                </div>
              </div>
            </div>
          {/each}
        </div>
      {/if}
    </div>
  {:else}
    <div class="placeholder-content">
      <p>No hay datos de anomalías disponibles.</p>
    </div>
  {/if}
</div>

<style>
  .arqueos-anomalies {
    width: 100%;
  }

  .anomalies-container {
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
    margin: 0 0 var(--spacing-lg, 1.25rem) 0;
  }

  .anomalies-summary {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: var(--spacing-md, 1rem);
    margin-bottom: var(--spacing-lg, 1.25rem);
    padding: var(--spacing-md, 1rem);
    background: var(--theme-bg-secondary);
    border-radius: var(--radius-md, 8px);
  }

  .summary-item {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xs, 0.5rem);
  }

  .summary-label {
    font-size: var(--text-sm, 0.875rem);
    color: var(--text-secondary);
  }

  .summary-value {
    font-size: var(--text-lg, 1.125rem);
    font-weight: 700;
    color: var(--text-primary);
  }

  .summary-value.severe {
    color: var(--accent-error, #EF4444);
  }

  .summary-value.moderate {
    color: var(--accent-warning, #F59E0B);
  }

  .no-anomalies {
    padding: var(--spacing-xl, 1.5rem);
    text-align: center;
    color: var(--text-secondary);
  }

  .anomalies-list {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-md, 1rem);
  }

  .anomaly-item {
    padding: var(--spacing-md, 1rem);
    background: var(--theme-bg-secondary);
    border: 1px solid var(--border-primary);
    border-left-width: 4px;
    border-left-color: var(--accent-warning, #F59E0B);
    border-radius: var(--radius-md, 8px);
  }

  .anomaly-item.severe {
    border-left-color: var(--accent-error, #EF4444);
    background: var(--theme-bg-card);
  }

  .anomaly-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--spacing-sm, 0.75rem);
  }

  .anomaly-date {
    display: flex;
    align-items: center;
    gap: var(--spacing-xs, 0.5rem);
    font-weight: 600;
    color: var(--text-primary);
    text-transform: capitalize;
  }

  .anomaly-severity {
    font-size: var(--text-xs, 0.75rem);
    font-weight: 600;
    padding: var(--spacing-xs, 0.5rem) var(--spacing-sm, 0.75rem);
    background: var(--accent-warning, #F59E0B)20;
    color: var(--accent-warning, #F59E0B);
    border-radius: var(--radius-sm, 4px);
    text-transform: uppercase;
  }

  .anomaly-severity.severe {
    background: var(--accent-error, #EF4444)20;
    color: var(--accent-error, #EF4444);
  }

  .anomaly-details {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: var(--spacing-sm, 0.75rem);
  }

  .anomaly-detail {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xs, 0.5rem);
  }

  .detail-label {
    font-size: var(--text-xs, 0.75rem);
    color: var(--text-secondary);
  }

  .detail-value {
    font-size: var(--text-sm, 0.875rem);
    font-weight: 600;
    color: var(--text-primary);
  }

  .detail-value.positive {
    color: var(--accent-success, #10B981);
  }

  .detail-value.negative {
    color: var(--accent-error, #EF4444);
  }

  .placeholder-content {
    padding: var(--spacing-2xl, 3rem);
    text-align: center;
    color: var(--text-secondary);
    font-style: italic;
  }
</style>



