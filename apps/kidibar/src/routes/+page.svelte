<script lang="ts">
  /**
   * Kidibar page - Product sales and stock alerts with real-time WebSocket updates.
   */
  import { onMount, onDestroy } from "svelte";
  import { user, token } from "@kidyland/utils";
  import { get } from "@kidyland/utils";
  import { WebSocketClient } from "@kidyland/utils";
  import type { Product } from "@kidyland/shared/types";
  import { Button } from "@kidyland/ui";

  let products: Product[] = [];
  let stockAlerts: Product[] = [];
  let ws: WebSocketClient | null = null;
  let loading = false;
  let error: string | null = null;

  onMount(async () => {
    await loadStockAlerts();
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
    const currentToken = $token;

    if (!currentUser?.sucursal_id || !currentToken) {
      console.warn("Cannot connect WebSocket: missing user or token");
      return;
    }

    const wsUrl = import.meta.env.VITE_WS_URL || "ws://localhost:8000";
    
    try {
      ws = new WebSocketClient({
        url: `${wsUrl}/ws/stock-alerts`,
        params: {
          token: currentToken,
          sucursal_id: currentUser.sucursal_id,
        },
        onMessage: (data) => {
          if (data.type === "stock_alert") {
            // Update stock alerts
            stockAlerts = data.alerts || [];
            // Show notification
            if (data.alerts && data.alerts.length > 0) {
              alert(`Stock alert: ${data.alerts.length} productos con stock bajo`);
            }
          }
        },
        onError: (err) => {
          console.error("WebSocket error:", err);
          error = "WebSocket connection error";
        },
        onClose: () => {
          console.log("WebSocket disconnected");
        },
      });

      ws.connect();
    } catch (e: any) {
      console.error("Error creating WebSocket:", e);
      error = e.message || "Error connecting to WebSocket";
    }
  }
</script>

<script lang="ts">
  import { goto } from "$app/navigation";
</script>

<div class="container mx-auto p-4">
  <div class="page-header">
    <h1 class="text-2xl font-bold">KidiBar - Alertas de Stock</h1>
    <button
      class="new-sale-button"
      on:click={() => goto("/venta")}
    >
      ➕ Nueva Venta
    </button>
  </div>

  {#if error}
    <div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
      {error}
    </div>
  {/if}

  {#if loading}
    <p>Cargando alertas...</p>
  {:else if stockAlerts.length === 0}
    <p class="text-green-600">✅ Todo el stock está en orden</p>
  {:else}
    <div class="bg-yellow-100 border border-yellow-400 text-yellow-800 px-4 py-3 rounded mb-4">
      ⚠️ {stockAlerts.length} producto(s) con stock bajo
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {#each stockAlerts as product}
        <div class="bg-white border rounded-lg p-4 shadow">
          <h3 class="font-semibold">{product.name}</h3>
          <p class="text-sm text-gray-600">
            Stock: <span class="font-bold text-red-600">{product.stock_qty}</span>
          </p>
          <p class="text-xs text-gray-500">
            Umbral: {product.threshold_alert_qty}
          </p>
        </div>
      {/each}
    </div>
  {/if}

  <div class="mt-4">
    <Button on:click={loadStockAlerts}>Actualizar</Button>
    <p class="text-sm text-gray-500 mt-2">
      WebSocket: {ws?.isConnected() ? "🟢 Conectado" : "🔴 Desconectado"}
    </p>
  </div>
</div>

<style>
  .container {
    max-width: 1200px;
  }

  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--spacing-lg);
    flex-wrap: wrap;
    gap: var(--spacing-md);
  }

  .new-sale-button {
    min-width: 160px;
    min-height: 48px;
    padding: var(--spacing-md) var(--spacing-lg);
    background: var(--accent-primary);
    color: var(--text-inverse);
    border: none;
    border-radius: var(--radius-md);
    font-weight: 600;
    font-size: var(--text-base);
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .new-sale-button:hover {
    background: var(--accent-primary-hover);
    transform: translateY(-1px);
    box-shadow: var(--shadow-md);
  }

  @media (max-width: 768px) {
    .page-header {
      flex-direction: column;
      align-items: stretch;
    }

    .new-sale-button {
      width: 100%;
    }
  }
</style>




