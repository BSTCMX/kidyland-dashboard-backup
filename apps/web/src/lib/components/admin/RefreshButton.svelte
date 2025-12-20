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
  import {
    metricsStore,
    refreshMetrics,
  } from "$lib/stores/metrics";
  import { selectedDays } from "$lib/stores/period";
  import { user } from "$lib/stores/auth";
  import { RefreshCw } from "lucide-svelte";

  // Component state
  let disabled = false;
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
    
    // Update status message based on state
    if ($metricsStore.refreshInProgress) {
      statusMessage = "Actualizando métricas...";
    } else {
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
   * Uses refreshMetrics from store as single source of truth.
   */
  async function handleRefresh() {
    // Get sucursal ID from user store or use null for all
    const sucursalId = $user?.sucursal_id || null;
    
    try {
      // Call refreshMetrics from store - it handles all validation and state management
      await refreshMetrics(sucursalId, $selectedDays);
    } catch (error: any) {
      // Errors are already handled by refreshMetrics and stored in metricsStore.error
      // Just log for debugging
      console.error("Error in RefreshButton:", error);
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
    <RefreshCw size={18} strokeWidth={1.5} class={$metricsStore.refreshInProgress ? 'spinning' : ''} style="display: inline-block; vertical-align: middle; margin-right: 6px;" />
    {$metricsStore.refreshInProgress ? "Actualizando..." : "Actualizar"}
  </button>
  
  {#if statusMessage}
    <div class="status-message" class:error={$metricsStore.error}>
      {statusMessage}
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
    border: 2px solid var(--accent-primary);
    box-shadow: 3px 3px 0px 0px var(--accent-primary);
    background-color: var(--theme-bg-elevated);
    color: var(--accent-primary);
    font-weight: 600;
    padding: 0.75rem 1.5rem;
    border-radius: var(--radius-md);
    cursor: pointer;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    font-size: 1rem;
  }

  .refresh-button:hover:not(.disabled) {
    box-shadow: none;
    border-width: 3px;
    transform: translate(3px, 3px);
    background-color: var(--accent-primary);
    color: var(--text-inverse);
  }

  .refresh-button:active:not(.disabled) {
    transform: translate(2px, 2px);
    transition-duration: 0.1s;
  }

  .refresh-button.disabled,
  .refresh-button.loading {
    opacity: 0.5;
    cursor: not-allowed;
    box-shadow: 1px 1px 0px 0px var(--accent-primary);
    background-color: var(--theme-bg-elevated);
    color: var(--accent-primary);
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
  
  :global(.spinning) {
    animation: spin 1s linear infinite;
  }
  
  @keyframes spin {
    from {
      transform: rotate(0deg);
    }
    to {
      transform: rotate(360deg);
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

  /* Mobile: Optimize for touch devices */
  @media (max-width: 768px) {
    .refresh-button-container {
      width: 100%;
      align-items: stretch;
    }

    .refresh-button {
      width: 100%;
      min-height: 44px; /* Minimum touch target size for accessibility */
      justify-content: center;
    }

    .status-message {
      text-align: center;
    }
  }

  /* Prevent hover transform issues on touch devices */
  @media (hover: none) and (pointer: coarse) {
    .refresh-button:hover:not(.disabled) {
      transform: none;
      box-shadow: 3px 3px 0px 0px var(--accent-primary);
      border-width: 2px;
    }
  }
</style>


