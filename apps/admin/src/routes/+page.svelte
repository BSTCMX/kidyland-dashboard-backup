<script lang="ts">
  /**
   * Admin Dashboard - Main page with metrics and refresh button.
   * 
   * Features:
   * - Master refresh button
   * - Display of sales, stock, and services metrics
   * - Reactive updates from metrics store
   */
  import { onMount } from "svelte";
  import RefreshButton from "$lib/components/RefreshButton.svelte";
  import PredictionsPanel from "$lib/components/PredictionsPanel.svelte";
  import { metricsStore, formattedRevenue, formattedATV, timeSinceLastRefresh } from "$lib/stores/metrics";

  // Load initial metrics on mount (optional - can be done via button)
  onMount(() => {
    // Metrics will be loaded when user clicks refresh button
    // Or can be loaded automatically here if desired
  });
</script>

<div class="dashboard-container">
  <div class="dashboard-header">
    <h1 class="dashboard-title">📊 Dashboard Admin</h1>
    <RefreshButton />
  </div>

  {#if $metricsStore.error}
    <div class="error-banner">
      {$metricsStore.error}
    </div>
  {/if}

  <div class="metrics-grid">
    <!-- Sales Metrics -->
    <div class="metric-card">
      <h2 class="metric-title">💰 Ventas</h2>
      {#if $metricsStore.sales}
        <div class="metric-content">
          <div class="metric-value">{$formattedRevenue}</div>
          <div class="metric-label">Total Revenue</div>
          
          <div class="metric-row">
            <span class="metric-label">Ticket Promedio:</span>
            <span class="metric-value-small">{$formattedATV}</span>
          </div>
          
          <div class="metric-row">
            <span class="metric-label">Total Ventas:</span>
            <span class="metric-value-small">{$metricsStore.sales.sales_count}</span>
          </div>
          
          <div class="metric-row">
            <span class="metric-label">Por Tipo:</span>
            <div class="metric-detail">
              {#each Object.entries($metricsStore.sales.revenue_by_type) as [type, revenue]}
                <div class="metric-item">
                  {type}: ${(revenue / 100).toFixed(2)}
                </div>
              {/each}
            </div>
          </div>
        </div>
      {:else}
        <div class="metric-empty">
          Presiona "Actualizar" para cargar métricas de ventas
        </div>
      {/if}
    </div>

    <!-- Stock Metrics -->
    <div class="metric-card">
      <h2 class="metric-title">📦 Inventario</h2>
      {#if $metricsStore.stock}
        <div class="metric-content">
          <div class="metric-value">{$metricsStore.stock.total_products}</div>
          <div class="metric-label">Total Productos</div>
          
          <div class="metric-row">
            <span class="metric-label">Valor Total:</span>
            <span class="metric-value-small">
              ${($metricsStore.stock.total_stock_value_cents / 100).toFixed(2)}
            </span>
          </div>
          
          {#if $metricsStore.stock.alerts_count > 0}
            <div class="alert-badge">
              ⚠️ {$metricsStore.stock.alerts_count} alertas de stock bajo
            </div>
            
            <div class="alerts-list">
              {#each $metricsStore.stock.low_stock_alerts.slice(0, 5) as alert}
                <div class="alert-item">
                  {alert.product_name}: {alert.stock_qty} unidades
                </div>
              {/each}
            </div>
          {:else}
            <div class="metric-success">✅ Sin alertas de stock</div>
          {/if}
        </div>
      {:else}
        <div class="metric-empty">
          Presiona "Actualizar" para cargar métricas de inventario
        </div>
      {/if}
    </div>

    <!-- Services Metrics -->
    <div class="metric-card">
      <h2 class="metric-title">⏱️ Servicios</h2>
      {#if $metricsStore.services}
        <div class="metric-content">
          <div class="metric-value">{$metricsStore.services.active_timers_count}</div>
          <div class="metric-label">Timers Activos</div>
          
          <div class="metric-row">
            <span class="metric-label">Total Servicios:</span>
            <span class="metric-value-small">{$metricsStore.services.total_services}</span>
          </div>
          
          <div class="metric-row">
            <span class="metric-label">Por Sucursal:</span>
            <div class="metric-detail">
              {#each Object.entries($metricsStore.services.services_by_sucursal) as [sucursal, count]}
                <div class="metric-item">
                  Sucursal {sucursal.slice(0, 8)}: {count}
                </div>
              {/each}
            </div>
          </div>
        </div>
      {:else}
        <div class="metric-empty">
          Presiona "Actualizar" para cargar métricas de servicios
        </div>
      {/if}
    </div>
  </div>

  {#if $metricsStore.lastRefresh && $timeSinceLastRefresh}
    <div class="last-refresh">
      Última actualización: {$timeSinceLastRefresh}
    </div>
  {/if}

  <!-- Predictions Panel (Bajo Demanda) -->
  <PredictionsPanel />
</div>

<style>
  .dashboard-container {
    min-height: 100vh;
    background: linear-gradient(135deg, #0f0a1f 0%, #1a0f2e 100%);
    padding: 2rem;
    color: white;
  }

  .dashboard-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 2rem;
  }

  .dashboard-title {
    font-size: 2rem;
    font-weight: 800;
    background: linear-gradient(135deg, #ffffff 0%, #f0e7ff 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0;
  }

  .error-banner {
    background: #ef4444;
    color: white;
    padding: 1rem;
    border-radius: 0.5rem;
    margin-bottom: 1rem;
    text-align: center;
    font-weight: 500;
  }

  .metrics-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 1.5rem;
    margin-bottom: 2rem;
  }

  .metric-card {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 1rem;
    padding: 1.5rem;
    backdrop-filter: blur(10px);
  }

  .metric-title {
    font-size: 1.25rem;
    font-weight: 700;
    margin: 0 0 1rem 0;
    color: #f0e7ff;
  }

  .metric-content {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .metric-value {
    font-size: 2rem;
    font-weight: 800;
    color: #d946ef;
  }

  .metric-label {
    font-size: 0.875rem;
    color: #9ca3af;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .metric-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.5rem 0;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
  }

  .metric-value-small {
    font-weight: 600;
    color: #f0e7ff;
  }

  .metric-detail {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
    margin-top: 0.5rem;
  }

  .metric-item {
    font-size: 0.875rem;
    color: #d1d5db;
  }

  .metric-empty {
    color: #6b7280;
    font-style: italic;
    text-align: center;
    padding: 2rem;
  }

  .alert-badge {
    background: #fef3c7;
    color: #92400e;
    padding: 0.5rem 1rem;
    border-radius: 0.5rem;
    font-weight: 600;
    margin-top: 0.5rem;
  }

  .alerts-list {
    margin-top: 0.5rem;
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  .alert-item {
    font-size: 0.875rem;
    color: #fca5a5;
    padding: 0.25rem 0;
  }

  .metric-success {
    color: #10b981;
    font-weight: 500;
    margin-top: 0.5rem;
  }

  .last-refresh {
    text-align: center;
    color: #6b7280;
    font-size: 0.875rem;
    margin-top: 2rem;
  }
</style>

