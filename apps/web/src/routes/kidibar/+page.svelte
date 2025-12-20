<script lang="ts">
  /**
   * Kidibar dashboard page.
   * 
   * Main dashboard for kidibar role.
   */
  import { onMount, onDestroy } from "svelte";
  import { goto } from "$app/navigation";
  import { page } from "$app/stores";
  import { user, hasAccessSecure, canEditSecure, hasRole } from "$lib/stores/auth";
  import { fetchKidibarStats, kidibarStatsStore } from "$lib/stores/kidibar-stats";
  import { 
    Eye,
    BarChart3,
    TrendingUp,
    AlertTriangle,
    RefreshCw
  } from "lucide-svelte";
  import { Button } from "@kidyland/ui";

  let refreshInterval: ReturnType<typeof setInterval> | null = null;

  // Get effective sucursal_id: prioritize user's sucursal_id, fallback to query param
  // This allows super_admin to access panels with a specific sucursal via query params
  $: effectiveSucursalId = $user?.sucursal_id || $page.url.searchParams.get('sucursal_id') || null;
  $: hasValidSucursal = effectiveSucursalId !== null;
  // Show error banner only if no valid sucursal AND user exists AND user is NOT super_admin
  // Using $user directly ensures reactivity in Svelte
  $: shouldShowSucursalError = !hasValidSucursal && $user && $user.role !== "super_admin";
  // Filter backend errors: hide "Sucursal ID is required" for super_admin
  // This allows super_admin to access all panel functionalities even without stats
  $: displayBackendError = $kidibarStatsStore.error && 
    !($user?.role === "super_admin" && 
      $kidibarStatsStore.error.includes("Sucursal ID is required"));

  async function loadStats() {
    if (effectiveSucursalId) {
      try {
        await fetchKidibarStats(effectiveSucursalId);
      } catch (error) {
        // Error handled by store
      }
    }
  }

  onMount(() => {
    // Early return: verify user has access BEFORE executing any logic
    // Uses secure checks that verify token-store consistency
    // This prevents race conditions where fetchKidibarStats() executes with stale token
    if (!$user || !hasAccessSecure("/kidibar")) {
      goto("/");
      return;
    }

    // Only execute if user has access AND token-store are consistent
    // Load stats if we have a valid sucursal_id (from user or query params)
    if (effectiveSucursalId) {
      loadStats();
      
      // Auto-refresh every 30 seconds
      refreshInterval = setInterval(() => {
        if (effectiveSucursalId) {
          loadStats();
        }
      }, 30000);
    }
  });

  onDestroy(() => {
    if (refreshInterval) {
      clearInterval(refreshInterval);
    }
  });

  function formatPrice(cents: number): string {
    return `$${(cents / 100).toFixed(2)}`;
  }

  $: readonly = !canEditSecure("kidibar");
</script>

<div class="dashboard-page">
  <div class="dashboard-container">
    <div class="dashboard-header">
      <div>
        <h1 class="page-title">Dashboard</h1>
        <p class="page-description">
          Estadísticas de KidiBar y control de inventario.
        </p>
      </div>
      <div class="header-actions">
        <Button 
          variant="brutalist" 
          size="small" 
          on:click={loadStats} 
          disabled={$kidibarStatsStore.loading}
        >
          <RefreshCw size={16} strokeWidth={1.5} />
          {#if $kidibarStatsStore.loading}
            Actualizando...
          {:else}
            Actualizar
          {/if}
        </Button>
      </div>
    </div>

    {#if readonly}
      <div class="readonly-banner">
        <Eye size={20} strokeWidth={1.5} />
        <span class="readonly-text">Modo de Solo Lectura - No puedes editar ni crear</span>
      </div>
    {/if}

    {#if shouldShowSucursalError}
      <div class="error-banner">
        No hay sucursal asignada. Por favor, selecciona una sucursal desde el panel de acceso.
      </div>
    {/if}

    {#if displayBackendError}
      <div class="error-banner">{$kidibarStatsStore.error}</div>
    {/if}

    <!-- Statistics Section -->
    {#if $kidibarStatsStore.loading && !$kidibarStatsStore.stats}
      <div class="loading-state">Cargando estadísticas...</div>
    {:else if $kidibarStatsStore.stats}
      {@const stats = $kidibarStatsStore.stats}
      {@const sales = stats?.sales}
      {#if sales}
        <div class="stats-grid">
          <!-- Sales Card -->
          <div class="stat-card">
            <div class="stat-header">
              <BarChart3 size={24} strokeWidth={1.5} />
              <h3>Ventas del Día</h3>
            </div>
            <div class="stat-value">{formatPrice(sales.total_revenue_cents || 0)}</div>
            <div class="stat-details">
              <div class="detail-item">
                <span class="detail-label">Total:</span>
                <span class="detail-value">{sales.total_count || 0}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">Productos:</span>
                <span class="detail-value">{sales.product_count || 0}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">Paquetes:</span>
                <span class="detail-value">{sales.package_count || 0}</span>
              </div>
            </div>
          </div>

          <!-- Stock Alerts Card -->
          <div class="stat-card">
            <div class="stat-header">
              <AlertTriangle size={24} strokeWidth={1.5} />
              <h3>Alertas de Stock</h3>
            </div>
            <div class="stat-value">{stats.stock_alerts?.low_stock_count || 0}</div>
            <p class="stat-description">Productos con stock bajo</p>
            {#if stats.stock_alerts?.low_stock_products && stats.stock_alerts.low_stock_products.length > 0}
              <div class="low-stock-list">
                {#each stats.stock_alerts.low_stock_products as product}
                  <div class="low-stock-item">
                    <span class="product-name">{product.product_name}</span>
                    <span class="stock-info">
                      Stock: <strong>{product.stock_qty || 0}</strong> / Alerta: {product.threshold_alert_qty || 0}
                    </span>
                  </div>
                {/each}
              </div>
            {/if}
          </div>

          <!-- Peak Hours Card -->
          {#if stats.peak_hours && stats.peak_hours.length > 0}
            <div class="stat-card">
              <div class="stat-header">
                <TrendingUp size={24} strokeWidth={1.5} />
                <h3>Horas Pico</h3>
              </div>
              <div class="peak-hours-list">
                {#each stats.peak_hours.slice(0, 3) as peak}
                  <div class="peak-hour-item">
                    <span class="hour-label">{peak.hour}:00</span>
                    <span class="sales-count">{peak.sales_count || 0} ventas</span>
                  </div>
                {/each}
              </div>
            </div>
          {/if}
        </div>
      {:else}
        <div class="error-banner">Error: Datos de ventas no disponibles</div>
      {/if}
    {/if}
  </div>
</div>

<style>
  .dashboard-page {
    width: 100%;
  }

  .dashboard-container {
    max-width: 1400px;
    margin: 0 auto;
  }

  .dashboard-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: var(--spacing-xl);
    gap: var(--spacing-lg);
  }

  .header-actions {
    display: flex;
    gap: var(--spacing-md);
    align-items: center;
  }

  .page-title {
    font-family: var(--font-primary);
    font-size: var(--text-3xl);
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: var(--spacing-md);
  }

  .page-description {
    font-size: var(--text-lg);
    color: var(--text-secondary);
    margin: 0;
  }

  .error-banner {
    padding: var(--spacing-md);
    background: rgba(211, 5, 84, 0.1);
    border: 1px solid rgba(211, 5, 84, 0.3);
    border-radius: var(--radius-md);
    color: #d30554;
    margin-bottom: var(--spacing-xl);
  }

  .loading-state {
    padding: var(--spacing-xl);
    text-align: center;
    color: var(--text-secondary);
    font-size: var(--text-lg);
  }

  .stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: var(--spacing-xl);
    margin-bottom: var(--spacing-xl);
  }

  .stat-card {
    padding: var(--spacing-xl);
    background: var(--theme-bg-card);
    backdrop-filter: blur(16px) saturate(150%);
    -webkit-backdrop-filter: blur(16px) saturate(150%);
    border: 1px solid var(--border-primary);
    border-radius: 16px;
    box-shadow: 
      0 8px 24px rgba(0, 0, 0, 0.15),
      0 0 20px var(--glow-primary),
      inset 0 1px 0 rgba(255, 255, 255, 0.05);
  }

  .stat-header {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    margin-bottom: var(--spacing-md);
    color: var(--text-secondary);
  }

  .stat-header h3 {
    font-size: var(--text-lg);
    font-weight: 600;
    margin: 0;
    color: var(--text-primary);
  }

  .stat-value {
    font-size: var(--text-3xl);
    font-weight: 700;
    color: var(--accent-primary);
    margin-bottom: var(--spacing-md);
  }

  .stat-description {
    color: var(--text-secondary);
    font-size: var(--text-sm);
    margin: 0;
  }

  .stat-details {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-sm);
  }

  .detail-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .detail-label {
    color: var(--text-secondary);
    font-size: var(--text-sm);
  }

  .detail-value {
    color: var(--text-primary);
    font-weight: 600;
    font-size: var(--text-sm);
  }

  .peak-hours-list {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-sm);
  }

  .peak-hour-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: var(--spacing-sm);
    background: var(--theme-bg-secondary);
    border-radius: var(--radius-sm);
  }

  .hour-label {
    color: var(--text-secondary);
    font-size: var(--text-sm);
    font-weight: 500;
  }

  .sales-count {
    color: var(--text-primary);
    font-size: var(--text-sm);
    font-weight: 600;
  }

  .low-stock-list {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-sm);
    margin-top: var(--spacing-md);
    padding-top: var(--spacing-md);
    border-top: 1px solid var(--border-primary);
  }

  .low-stock-item {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xs);
    padding: var(--spacing-sm);
    background: rgba(211, 5, 84, 0.05);
    border: 1px solid rgba(211, 5, 84, 0.2);
    border-radius: var(--radius-sm);
  }

  .low-stock-item .product-name {
    color: var(--text-primary);
    font-size: var(--text-sm);
    font-weight: 600;
  }

  .low-stock-item .stock-info {
    color: var(--text-secondary);
    font-size: var(--text-xs);
  }

  .low-stock-item .stock-info strong {
    color: var(--accent-error);
    font-weight: 700;
  }

  .readonly-banner {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: var(--spacing-sm);
    padding: var(--spacing-md) var(--spacing-lg);
    background: rgba(255, 206, 0, 0.1);
    border: 1px solid var(--accent-warning);
    border-radius: var(--radius-md);
    margin-bottom: var(--spacing-xl);
    color: var(--accent-warning);
    font-weight: 600;
  }

  .readonly-text {
    font-size: var(--text-sm);
  }

  @media (max-width: 768px) {
    .dashboard-header {
      flex-direction: column;
      align-items: stretch;
      gap: var(--spacing-md);
    }

    .header-actions {
      width: 100%;
      flex-direction: column;
      gap: var(--spacing-sm);
      align-items: stretch;
    }

    .header-actions :global(.btn-brutalist) {
      width: 100%;
      min-height: 44px; /* Minimum touch target size for accessibility */
      justify-content: center;
    }

    .stats-grid {
      grid-template-columns: 1fr;
    }
  }

  /* Prevent hover transform issues on touch devices */
  @media (hover: none) and (pointer: coarse) {
    .header-actions :global(.btn-brutalist:hover) {
      transform: none;
      box-shadow: 3px 3px 0px 0px var(--accent-primary);
      border-width: 2px;
    }
  }
</style>

