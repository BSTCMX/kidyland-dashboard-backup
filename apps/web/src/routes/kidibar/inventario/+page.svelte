

<script lang="ts">
  /**
   * Inventario page - Stock alerts for kidibar.
   * 
   * Shows stock alerts with real-time WebSocket updates.
   */
  import { onMount, onDestroy } from "svelte";
  import { goto } from "$app/navigation";
  import { user, hasAccessSecure, token, getToken } from "$lib/stores/auth";
  import { get } from "@kidyland/utils";
  import type { Product } from "@kidyland/shared/types";
  import { createTimerWebSocket } from "@kidyland/utils";
  import { Button } from "@kidyland/ui";

  let stockAlerts: Product[] = [];
  let ws: any = null; // WebSocketClient will be implemented later
  let loading = false;
  let error: string | null = null;

  onMount(() => {
    // Verify user has access to kidibar
    if (!$user || !hasAccessSecure("/kidibar")) {
      goto("/kidibar");
      return;
    }

    loadStockAlerts();
    connectWebSocket();
  });

  onDestroy(() => {
    if (ws) {
      ws.disconnect();
    }
  });

  async function loadStockAlerts() {
    try {
      loading = true;
      const currentUser = $user;
      if (!currentUser?.sucursal_id) {
        error = "No sucursal assigned";
        return;
      }

      stockAlerts = await get<Product[]>(
        `/stock/alerts?sucursal_id=${currentUser.sucursal_id}`
      );
    } catch (e: any) {
      error = e.message || "Error loading stock alerts";
      console.error("Error loading stock alerts:", e);
    } finally {
      loading = false;
    }
  }

  function connectWebSocket() {
    const currentUser = $user;
    const currentToken = getToken();
    if (!currentUser?.sucursal_id || !currentToken) {
      console.warn("Cannot connect WebSocket: missing user or token");
      return;
    }

    // TODO: Implement WebSocket connection when WebSocket utilities are available
    console.log("WebSocket connection not yet implemented for stock alerts");
    error = "WebSocket connection not yet implemented";
  }
</script>

<div class="inventario-page">
  <div class="page-header">
    <button class="back-button" on:click={() => goto("/kidibar")}>← Volver</button>
    <h1 class="page-title">Inventario - Alertas de Stock</h1>
  </div>

  {#if error}
    <div class="error-banner">{error}</div>
  {/if}

  {#if loading}
    <p>Cargando alertas...</p>
  {:else if stockAlerts.length === 0}
    <div class="success-message">
      ✅ Todo el stock está en orden
    </div>
  {:else}
    <div class="alert-banner">
      ⚠️ {stockAlerts.length} producto(s) con stock bajo
    </div>

    <div class="products-grid">
      {#each stockAlerts as product}
        <div class="product-card">
          <h3 class="product-name">{product.name}</h3>
          <p class="product-stock">
            Stock: <span class="stock-value">{product.stock_qty}</span>
          </p>
          <p class="product-threshold">
            Umbral: {product.threshold_alert_qty}
          </p>
        </div>
      {/each}
    </div>
  {/if}

  <div class="actions">
    <Button on:click={loadStockAlerts}>Actualizar</Button>
    <p class="ws-status">
      WebSocket: 🔴 No implementado aún
    </p>
  </div>
</div>

<style>
  .inventario-page {
    min-height: 100vh;
    background: var(--theme-bg-primary);
    padding: var(--spacing-lg);
  }

  .page-header {
    display: flex;
    align-items: center;
    gap: var(--spacing-md);
    margin-bottom: var(--spacing-xl);
  }

  .back-button {
    min-width: 48px;
    min-height: 48px;
    padding: var(--spacing-sm) var(--spacing-md);
    background: var(--theme-bg-elevated);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
    color: var(--text-primary);
    cursor: pointer;
    font-size: var(--text-base);
    transition: all 0.2s ease;
  }

  .back-button:hover {
    background: var(--theme-bg-secondary);
    transform: translateY(-1px);
  }

  .page-title {
    font-family: var(--font-primary);
    font-size: var(--text-3xl);
    font-weight: 700;
    color: var(--text-primary);
  }

  .error-banner {
    padding: var(--spacing-md);
    background: rgba(211, 5, 84, 0.1);
    border: 1px solid var(--accent-danger);
    border-radius: var(--radius-md);
    color: var(--accent-danger);
    margin-bottom: var(--spacing-lg);
  }

  .success-message {
    padding: var(--spacing-lg);
    background: rgba(61, 173, 9, 0.1);
    border: 1px solid var(--accent-success);
    border-radius: var(--radius-md);
    color: var(--accent-success);
    font-weight: 600;
    text-align: center;
    margin-bottom: var(--spacing-xl);
  }

  .alert-banner {
    padding: var(--spacing-md) var(--spacing-lg);
    background: rgba(255, 206, 0, 0.1);
    border: 1px solid var(--accent-warning);
    border-radius: var(--radius-md);
    color: var(--accent-warning);
    font-weight: 600;
    margin-bottom: var(--spacing-xl);
  }

  .products-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: var(--spacing-lg);
    margin-bottom: var(--spacing-xl);
  }

  .product-card {
    padding: var(--spacing-xl);
    background: var(--theme-bg-elevated);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-sm);
  }

  .product-name {
    font-size: var(--text-xl);
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: var(--spacing-md);
  }

  .product-stock {
    font-size: var(--text-base);
    color: var(--text-secondary);
    margin-bottom: var(--spacing-sm);
  }

  .stock-value {
    font-weight: 700;
    color: var(--accent-danger);
    font-size: var(--text-lg);
  }

  .product-threshold {
    font-size: var(--text-sm);
    color: var(--text-muted);
  }

  .actions {
    display: flex;
    align-items: center;
    gap: var(--spacing-lg);
    margin-top: var(--spacing-xl);
  }

  .ws-status {
    font-size: var(--text-sm);
    color: var(--text-secondary);
    margin: 0;
  }

  @media (max-width: 768px) {
    .inventario-page {
      padding: var(--spacing-md);
    }

    .products-grid {
      grid-template-columns: 1fr;
    }
  }
</style>

