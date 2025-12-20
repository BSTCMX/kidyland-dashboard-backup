<script lang="ts">
  /**
   * InventoryAlerts - Intelligent inventory alerts with context.
   * 
   * Displays alerts with priority levels and actionable recommendations.
   */
  import { onMount } from 'svelte';
  import { fetchInventoryAlerts, formatPrice, type InventoryAlertsReport, type InventoryAlert } from '$lib/stores/reports';
  import LoadingSpinner from '$lib/components/admin/LoadingSpinner.svelte';
  import ErrorBanner from '$lib/components/admin/ErrorBanner.svelte';
  import { AlertTriangle, AlertCircle, Info, CheckCircle } from 'lucide-svelte';

  export let sucursalId: string | null = null;

  let alertsData: InventoryAlertsReport | null = null;
  let loading = false;
  let error: string | null = null;

  let previousSucursalId: string | null = null;

  async function loadAlertsData() {
    loading = true;
    error = null;

    try {
      const report = await fetchInventoryAlerts(sucursalId);
      alertsData = report;
    } catch (err: any) {
      console.error('Error loading alerts data:', err);
      error = err.message || 'Error al cargar alertas';
    } finally {
      loading = false;
    }
  }

  $: {
    if (sucursalId !== previousSucursalId) {
      previousSucursalId = sucursalId;
      loadAlertsData();
    }
  }

  onMount(() => {
    loadAlertsData();
  });

  function getAlertIcon(level: string) {
    if (level === "high") return AlertTriangle;
    if (level === "medium") return AlertCircle;
    return Info;
  }

  function getAlertColor(level: string): string {
    if (level === "high") return "var(--accent-error, #EF4444)";
    if (level === "medium") return "var(--accent-warning, #F59E0B)";
    return "var(--text-secondary)";
  }
</script>

<div class="inventory-alerts">
  {#if loading}
    <LoadingSpinner />
  {:else if error}
    <ErrorBanner {error} />
  {:else if alertsData}
    <div class="alerts-container">
      <h3 class="section-title">Alertas de Inventario</h3>
      
      <!-- Summary -->
      <div class="summary-grid">
        <div class="summary-card">
          <h4 class="summary-title">Total Alertas</h4>
          <div class="summary-value">{alertsData.summary.total_alerts}</div>
        </div>
        <div class="summary-card high">
          <h4 class="summary-title">Alta Prioridad</h4>
          <div class="summary-value">{alertsData.summary.high_priority}</div>
        </div>
        <div class="summary-card medium">
          <h4 class="summary-title">Media Prioridad</h4>
          <div class="summary-value">{alertsData.summary.medium_priority}</div>
        </div>
        <div class="summary-card low">
          <h4 class="summary-title">Baja Prioridad</h4>
          <div class="summary-value">{alertsData.summary.low_priority}</div>
        </div>
      </div>

      <!-- Alerts List -->
      {#if alertsData.alerts && alertsData.alerts.length > 0}
        <div class="alerts-list">
          {#each alertsData.alerts as alert (alert.product_id + alert.type)}
            {@const AlertIcon = getAlertIcon(alert.level)}
            {@const alertColor = getAlertColor(alert.level)}
            <div class="alert-card" style="border-left-color: {alertColor};">
              <div class="alert-header">
                <div class="alert-icon-wrapper" style="color: {alertColor};">
                  <svelte:component this={AlertIcon} size={20} />
                </div>
                <div class="alert-title-section">
                  <h4 class="alert-title">{alert.product_name}</h4>
                  <span class="alert-type">{alert.type === "low_stock" ? "Stock Bajo" : "Reorden Necesario"}</span>
                </div>
                <span class="alert-level-badge" style="background-color: {alertColor};">
                  {alert.level === "high" ? "Alta" : alert.level === "medium" ? "Media" : "Baja"}
                </span>
              </div>
              <div class="alert-details">
                <div class="alert-detail-item">
                  <span class="detail-label">Stock Actual:</span>
                  <span class="detail-value">{alert.current_stock}</span>
                </div>
                {#if alert.threshold !== undefined}
                  <div class="alert-detail-item">
                    <span class="detail-label">Umbral:</span>
                    <span class="detail-value">{alert.threshold}</span>
                  </div>
                {/if}
                {#if alert.days_until_stockout !== null}
                  <div class="alert-detail-item">
                    <span class="detail-label">Días hasta Agotarse:</span>
                    <span class="detail-value" class:urgent={alert.days_until_stockout < 7}>
                      {alert.days_until_stockout}
                    </span>
                  </div>
                {/if}
                {#if alert.recommended_reorder_qty !== null}
                  <div class="alert-detail-item">
                    <span class="detail-label">Cantidad Recomendada:</span>
                    <span class="detail-value">{alert.recommended_reorder_qty}</span>
                  </div>
                {/if}
                {#if alert.turnover_rate !== null}
                  <div class="alert-detail-item">
                    <span class="detail-label">Tasa de Rotación:</span>
                    <span class="detail-value">{alert.turnover_rate.toFixed(2)}x</span>
                  </div>
                {/if}
              </div>
            </div>
          {/each}
        </div>
      {:else}
        <div class="no-alerts">
          <CheckCircle size={48} style="color: var(--accent-success, #10B981);" />
          <p>No hay alertas de inventario en este momento.</p>
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
  .inventory-alerts {
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

  .summary-card.medium {
    border-left: 4px solid var(--accent-warning, #F59E0B);
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

  .alerts-list {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-md, 1rem);
  }

  .alert-card {
    background: var(--theme-bg-secondary);
    border: 1px solid var(--border-primary);
    border-left-width: 4px;
    border-radius: var(--radius-md, 8px);
    padding: var(--spacing-md, 1rem);
  }

  .alert-header {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm, 0.75rem);
    margin-bottom: var(--spacing-sm, 0.75rem);
  }

  .alert-icon-wrapper {
    flex-shrink: 0;
  }

  .alert-title-section {
    flex: 1;
  }

  .alert-title {
    font-size: var(--text-base, 1rem);
    font-weight: 600;
    color: var(--text-primary);
    margin: 0 0 var(--spacing-xs, 0.5rem) 0;
  }

  .alert-type {
    font-size: var(--text-xs, 0.75rem);
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .alert-level-badge {
    padding: var(--spacing-xs, 0.5rem) var(--spacing-sm, 0.75rem);
    border-radius: var(--radius-sm, 4px);
    font-size: var(--text-xs, 0.75rem);
    font-weight: 600;
    color: white;
  }

  .alert-details {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: var(--spacing-sm, 0.75rem);
    margin-top: var(--spacing-sm, 0.75rem);
  }

  .alert-detail-item {
    display: flex;
    justify-content: space-between;
    font-size: var(--text-sm, 0.875rem);
  }

  .detail-label {
    color: var(--text-secondary);
  }

  .detail-value {
    font-weight: 500;
    color: var(--text-primary);
  }

  .detail-value.urgent {
    color: var(--accent-error, #EF4444);
    font-weight: 600;
  }

  .no-alerts {
    text-align: center;
    padding: var(--spacing-xl, 2rem);
    color: var(--text-secondary);
  }

  .no-alerts p {
    margin-top: var(--spacing-md, 1rem);
    font-size: var(--text-base, 1rem);
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
    .alert-details {
      grid-template-columns: 1fr;
    }
  }
</style>

