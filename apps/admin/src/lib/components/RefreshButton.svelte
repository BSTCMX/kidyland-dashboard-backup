<script lang="ts">
  /**
   * RefreshButton component - Master button for refreshing metrics.
   * 
   * Features:
   * - Validates time limits (minimum 2 seconds between refreshes)
   * - Validates count limits (maximum 30 refreshes per session)
   * - Calls POST /reports/refresh endpoint
   * - Updates metrics store with results
   * - Visual feedback for user
   */
  import { post } from "@kidyland/utils";
  import {
    metricsStore,
    updateAllMetrics,
    setRefreshInProgress,
    setError,
    type SalesReport,
    type StockReport,
    type ServicesReport,
  } from "$lib/stores/metrics";

  // Component state
  let disabled = false;
  let buttonText = "🔄 Actualizar";
  let statusMessage = "";
  let lastRefreshTime = 0;
  let refreshCount = 0;

  // Subscribe to store for reactive updates
  $: {
    disabled = $metricsStore.refreshInProgress;
    refreshCount = $metricsStore.refreshCount;
    
    if ($metricsStore.lastRefresh) {
      lastRefreshTime = $metricsStore.lastRefresh;
    }
    
    // Update button text based on state
    if ($metricsStore.refreshInProgress) {
      buttonText = "🔄 Actualizando...";
      statusMessage = "Actualizando métricas...";
    } else {
      buttonText = "🔄 Actualizar";
      if ($metricsStore.lastRefresh) {
        const seconds = Math.floor((Date.now() - $metricsStore.lastRefresh) / 1000);
        if (seconds < 60) {
          statusMessage = `Actualizado hace ${seconds}s`;
        } else {
          const minutes = Math.floor(seconds / 60);
          statusMessage = `Actualizado hace ${minutes}m`;
        }
      } else {
        statusMessage = "Presiona Actualizar para cargar métricas";
      }
    }
    
    // Show error if exists
    if ($metricsStore.error) {
      statusMessage = `❌ ${$metricsStore.error}`;
    }
  }

  /**
   * Handle refresh button click.
   */
  async function handleRefresh() {
    const currentState = $metricsStore;
    const currentTime = Date.now();

    // Validation 1: Check if refresh is already in progress
    if (currentState.refreshInProgress) {
      return;
    }

    // Validation 2: Check minimum time between refreshes (2 seconds)
    if (currentState.lastRefresh) {
      const timeSinceLastRefresh = currentTime - currentState.lastRefresh;
      if (timeSinceLastRefresh < 2000) {
        const remaining = ((2000 - timeSinceLastRefresh) / 1000).toFixed(1);
        setError(`Espera ${remaining}s antes de actualizar nuevamente`);
        return;
      }
    }

    // Validation 3: Check maximum refresh count (30 per session)
    if (currentState.refreshCount >= 30) {
      setError("Límite de actualizaciones alcanzado (30). Por favor espera.");
      return;
    }

    // Set refresh in progress
    setRefreshInProgress(true);
    setError(null);

    try {
      // Call refresh endpoint
      const response = await post<{
        success: boolean;
        message: string;
        metrics: {
          sales: SalesReport;
          stock: StockReport;
          services: ServicesReport;
        };
        elapsed_seconds: number;
        refresh_count: number;
        cache_invalidated: boolean;
      }>("/reports/refresh");

      if (response.success && response.metrics) {
        // Update store with new metrics
        updateAllMetrics(
          response.metrics.sales,
          response.metrics.stock,
          response.metrics.services
        );

        // Update status message
        statusMessage = `✅ Actualizado en ${response.elapsed_seconds}s`;
      } else {
        throw new Error(response.message || "Error al actualizar métricas");
      }
    } catch (error: any) {
      console.error("Error refreshing metrics:", error);
      
      // Handle specific error cases
      if (error.message?.includes("429")) {
        setError("Demasiadas solicitudes. Por favor espera.");
      } else if (error.message?.includes("401")) {
        setError("Sesión expirada. Por favor inicia sesión nuevamente.");
      } else {
        setError(error.message || "Error al actualizar métricas");
      }
    } finally {
      // Reset refresh in progress (already handled by updateAllMetrics or setError)
      // But ensure it's reset in case of unexpected errors
      setTimeout(() => {
        setRefreshInProgress(false);
      }, 100);
    }
  }
</script>

<div class="refresh-button-container">
  <button
    on:click={handleRefresh}
    disabled={disabled}
    class="refresh-button"
    class:disabled
    class:loading={$metricsStore.refreshInProgress}
  >
    {buttonText}
  </button>
  
  {#if statusMessage}
    <div class="status-message" class:error={$metricsStore.error}>
      {statusMessage}
    </div>
  {/if}
  
  {#if $metricsStore.refreshCount > 0}
    <div class="refresh-count">
      Actualizaciones: {$metricsStore.refreshCount}/30
    </div>
  {/if}
</div>

<style>
  .refresh-button-container {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 0.5rem;
    margin-bottom: 1rem;
  }

  .refresh-button {
    background: linear-gradient(135deg, #7c3aed 0%, #d946ef 50%, #ec4899 100%);
    color: white;
    font-weight: 600;
    padding: 0.75rem 1.5rem;
    border-radius: 0.5rem;
    border: none;
    cursor: pointer;
    transition: all 0.2s ease;
    font-size: 1rem;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  }

  .refresh-button:hover:not(.disabled) {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
  }

  .refresh-button:active:not(.disabled) {
    transform: translateY(0);
  }

  .refresh-button.disabled,
  .refresh-button.loading {
    opacity: 0.6;
    cursor: not-allowed;
    background: #6b7280;
  }

  .refresh-button.loading {
    animation: pulse 1.5s ease-in-out infinite;
  }

  @keyframes pulse {
    0%, 100% {
      opacity: 0.6;
    }
    50% {
      opacity: 0.8;
    }
  }

  .status-message {
    font-size: 0.875rem;
    color: #6b7280;
    text-align: right;
  }

  .status-message.error {
    color: #ef4444;
    font-weight: 500;
  }

  .refresh-count {
    font-size: 0.75rem;
    color: #9ca3af;
    text-align: right;
  }
</style>


