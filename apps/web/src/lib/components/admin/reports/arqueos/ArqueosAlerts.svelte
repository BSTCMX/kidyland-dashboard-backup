<script lang="ts">
  /**
   * ArqueosAlerts - Intelligent alerts component.
   */
  import { onMount } from 'svelte';
  import { fetchArqueosAlerts, type ArqueosAlertsReport } from '$lib/stores/reports';
  import LoadingSpinner from '$lib/components/admin/LoadingSpinner.svelte';
  import ErrorBanner from '$lib/components/admin/ErrorBanner.svelte';
  import { AlertTriangle, AlertCircle, Info } from 'lucide-svelte';

  export let sucursalId: string | null = null;
  export let selectedModule: "all" | "recepcion" | "kidibar" = "all";

  let alertsData: ArqueosAlertsReport | null = null;
  let loading = false;
  let error: string | null = null;

  let previousSucursalId: string | null = null;
  let previousModule: "all" | "recepcion" | "kidibar" = "all";

  async function loadAlertsData() {
    loading = true;
    error = null;

    try {
      const report = await fetchArqueosAlerts(sucursalId, selectedModule);
      alertsData = report;
    } catch (err: any) {
      console.error('Error loading alerts data:', err);
      error = err.message || 'Error al cargar alertas';
    } finally {
      loading = false;
    }
  }

  $: {
    const paramsChanged = 
      sucursalId !== previousSucursalId ||
      selectedModule !== previousModule;

    if (paramsChanged) {
      previousSucursalId = sucursalId;
      previousModule = selectedModule;
      loadAlertsData();
    }
  }

  onMount(() => {
    loadAlertsData();
  });

  function getAlertIcon(severity: string) {
    if (severity === "high") return AlertTriangle;
    if (severity === "medium") return AlertCircle;
    return Info;
  }

  function getAlertColor(severity: string): string {
    if (severity === "high") return "var(--accent-error, #EF4444)";
    if (severity === "medium") return "var(--accent-warning, #F59E0B)";
    return "var(--accent-primary, #0093F7)";
  }
</script>

<div class="arqueos-alerts">
  {#if loading}
    <LoadingSpinner />
  {:else if error}
    <ErrorBanner {error} />
  {:else if alertsData}
    <div class="alerts-container">
      <h3 class="section-title">Alertas Inteligentes</h3>
      
      {#if alertsData.status === "no_data"}
        <div class="no-data-message">
          <p>No hay suficientes datos para generar alertas.</p>
        </div>
      {:else if alertsData.alerts.length === 0}
        <div class="no-alerts-message">
          <Info size={24} style="color: var(--accent-success, #10B981)" />
          <p>No hay alertas activas. Todo está funcionando correctamente.</p>
        </div>
      {:else}
        <div class="alerts-list">
          {#each alertsData.alerts as alert (alert.type)}
            {@const AlertIcon = getAlertIcon(alert.severity)}
            <div class="alert-item" style="border-left-color: {getAlertColor(alert.severity)}">
              <div class="alert-icon">
                <AlertIcon size={24} style="color: {getAlertColor(alert.severity)}" />
              </div>
              <div class="alert-content">
                <div class="alert-header">
                  <h4 class="alert-title">{alert.message}</h4>
                  <span class="alert-severity" style="background: {getAlertColor(alert.severity)}20; color: {getAlertColor(alert.severity)}">
                    {alert.severity === "high" ? "Alta" : alert.severity === "medium" ? "Media" : "Baja"}
                  </span>
                </div>
                <p class="alert-recommendation">{alert.recommendation}</p>
                <div class="alert-details">
                  <span class="alert-detail">Valor: {alert.value.toFixed(2)}</span>
                  <span class="alert-detail">Umbral: {alert.threshold.toFixed(2)}</span>
                </div>
              </div>
            </div>
          {/each}
        </div>
      {/if}
    </div>
  {:else}
    <div class="placeholder-content">
      <p>No hay datos de alertas disponibles.</p>
    </div>
  {/if}
</div>

<style>
  .arqueos-alerts {
    width: 100%;
  }

  .alerts-container {
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

  .no-data-message,
  .no-alerts-message {
    padding: var(--spacing-xl, 1.5rem);
    text-align: center;
    color: var(--text-secondary);
  }

  .no-alerts-message {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: var(--spacing-md, 1rem);
  }

  .alerts-list {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-md, 1rem);
  }

  .alert-item {
    display: flex;
    gap: var(--spacing-md, 1rem);
    padding: var(--spacing-md, 1rem);
    background: var(--theme-bg-secondary);
    border: 1px solid var(--border-primary);
    border-left-width: 4px;
    border-radius: var(--radius-md, 8px);
  }

  .alert-icon {
    flex-shrink: 0;
  }

  .alert-content {
    flex: 1;
  }

  .alert-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--spacing-xs, 0.5rem);
    gap: var(--spacing-sm, 0.75rem);
  }

  .alert-title {
    font-size: var(--text-base, 1rem);
    font-weight: 600;
    color: var(--text-primary);
    margin: 0;
    flex: 1;
  }

  .alert-severity {
    font-size: var(--text-xs, 0.75rem);
    font-weight: 600;
    padding: var(--spacing-xs, 0.5rem) var(--spacing-sm, 0.75rem);
    border-radius: var(--radius-sm, 4px);
    text-transform: uppercase;
  }

  .alert-recommendation {
    font-size: var(--text-sm, 0.875rem);
    color: var(--text-secondary);
    margin: var(--spacing-xs, 0.5rem) 0;
  }

  .alert-details {
    display: flex;
    gap: var(--spacing-md, 1rem);
    margin-top: var(--spacing-xs, 0.5rem);
  }

  .alert-detail {
    font-size: var(--text-xs, 0.75rem);
    color: var(--text-secondary);
  }

  .placeholder-content {
    padding: var(--spacing-2xl, 3rem);
    text-align: center;
    color: var(--text-secondary);
    font-style: italic;
  }
</style>



