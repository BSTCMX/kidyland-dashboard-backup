<script lang="ts">
  /**
   * Estadísticas page for reception.
   * 
   * Shows detailed statistics for recepcion module.
   */
  import { onMount } from "svelte";
  import { goto } from "$app/navigation";
  import { page } from "$app/stores";
  import { user, hasAccessSecure } from "$lib/stores/auth";
  import { fetchRecepcionStats, recepcionStatsStore } from "$lib/stores/recepcion-stats";
  import { 
    BarChart3,
    TrendingUp,
    RefreshCw
  } from "lucide-svelte";
  import { Button } from "@kidyland/ui";

  // Get effective sucursal_id: prioritize user's sucursal_id, fallback to query param
  // This allows super_admin to access panels with a specific sucursal via query params
  $: effectiveSucursalId = $user?.sucursal_id || $page.url.searchParams.get('sucursal_id') || null;
  $: hasValidSucursal = effectiveSucursalId !== null;
  $: shouldShowSucursalError = !hasValidSucursal && $user && $user.role !== "super_admin";
  $: displayBackendError = $recepcionStatsStore.error && 
    !($user?.role === "super_admin" && 
      $recepcionStatsStore.error.includes("Sucursal ID is required"));

  async function loadStats() {
    if (effectiveSucursalId) {
      try {
        await fetchRecepcionStats(effectiveSucursalId);
      } catch (error) {
        // Error handled by store
      }
    }
  }

  onMount(() => {
    // Verify user has access to recepcion
    if (!$user || !hasAccessSecure("/recepcion")) {
      goto("/recepcion");
      return;
    }

    // Load stats
    if (effectiveSucursalId) {
      loadStats();
    }
  });

  function formatPrice(cents: number): string {
    return `$${(cents / 100).toFixed(2)}`;
  }
</script>

<div class="estadisticas-page">
  <div class="page-container">
    <div class="page-header">
      <div>
        <h1 class="page-title">Estadísticas</h1>
        <p class="page-description">
          Estadísticas detalladas de recepción.
        </p>
      </div>
      <div class="header-actions">
        <Button 
          variant="brutalist" 
          size="small" 
          on:click={loadStats} 
          disabled={$recepcionStatsStore.loading}
        >
          <RefreshCw size={16} strokeWidth={1.5} />
          {#if $recepcionStatsStore.loading}
            Actualizando...
          {:else}
            Actualizar
          {/if}
        </Button>
      </div>
    </div>

    {#if shouldShowSucursalError}
      <div class="error-banner">
        No hay sucursal asignada. Por favor, selecciona una sucursal desde el panel de acceso.
      </div>
    {/if}

    {#if displayBackendError}
      <div class="error-banner">{$recepcionStatsStore.error}</div>
    {/if}

    <!-- Statistics Section -->
    {#if $recepcionStatsStore.loading && !$recepcionStatsStore.stats}
      <div class="loading-state">Cargando estadísticas...</div>
    {:else if $recepcionStatsStore.stats}
      {@const stats = $recepcionStatsStore.stats}
      <div class="stats-grid">
        <!-- Sales Card -->
        <div class="stat-card">
          <div class="stat-header">
            <BarChart3 size={24} strokeWidth={1.5} />
            <h3>Ventas del Día</h3>
          </div>
          <div class="stat-value">{formatPrice(stats.sales?.total_revenue_cents || 0)}</div>
          <div class="stat-details">
            <div class="detail-item">
              <span class="detail-label">Total:</span>
              <span class="detail-value">{stats.sales?.total_count || 0}</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">Servicios:</span>
              <span class="detail-value">{stats.sales?.service_count || 0}</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">Paquetes:</span>
              <span class="detail-value">{stats.sales?.package_count || 0}</span>
            </div>
          </div>
        </div>

        <!-- Timers Card -->
        <div class="stat-card">
          <div class="stat-header">
            <TrendingUp size={24} strokeWidth={1.5} />
            <h3>Timers Activos</h3>
          </div>
          <div class="stat-value">{stats.active_timers}</div>
          <p class="stat-description">Timers activos en este momento</p>
        </div>

        <!-- Tickets Card -->
        <div class="stat-card">
          <div class="stat-header">
            <BarChart3 size={24} strokeWidth={1.5} />
            <h3>Tickets Generados</h3>
          </div>
          <div class="stat-value">{stats.tickets.generated_today}</div>
          <p class="stat-description">Tickets generados hoy</p>
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
                  <span class="sales-count">{peak.sales_count} ventas</span>
                </div>
              {/each}
            </div>
          </div>
        {/if}
      </div>
    {/if}
  </div>
</div>

<style>
  .estadisticas-page {
    width: 100%;
  }

  .page-container {
    max-width: 1400px;
    margin: 0 auto;
  }

  .page-header {
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
    margin: 0 0 var(--spacing-md) 0;
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
    border: 1px solid var(--border-secondary);
  }

  .hour-label {
    color: var(--text-primary);
    font-weight: 600;
    font-size: var(--text-base);
  }

  .sales-count {
    color: var(--text-secondary);
    font-size: var(--text-sm);
  }

  @media (max-width: 768px) {
    .page-header {
      flex-direction: column;
    }
  }
</style>
