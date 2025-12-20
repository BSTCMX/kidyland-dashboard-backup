<script lang="ts">
  /**
   * Reception page - Sales and timer management with real-time WebSocket updates.
   */
  import { onMount, onDestroy } from "svelte";
  import { user, token } from "@kidyland/utils";
  import { createTimerWebSocket } from "@kidyland/utils";
  import { get, post } from "@kidyland/utils";
  import type { Timer } from "@kidyland/shared/types";
  import { Button, Input } from "@kidyland/ui";
  import { goto } from "$app/navigation";

  let timers: Timer[] = [];
  let ws: ReturnType<typeof createTimerWebSocket> | null = null;
  let loading = false;
  let error: string | null = null;

  // Load active timers on mount
  onMount(async () => {
    await loadTimers();
    connectWebSocket();
  });

  onDestroy(() => {
    if (ws) {
      ws.disconnect();
    }
  });

  async function loadTimers() {
    try {
      loading = true;
      const currentUser = $user;
      if (!currentUser?.sucursal_id) {
        error = "No sucursal assigned";
        return;
      }

      const data = await get<{ timer_id: string; time_left: number }[]>(
        `/timers/active?sucursal_id=${currentUser.sucursal_id}`
      );
      
      // Transform to Timer format if needed
      timers = data as any;
    } catch (e: any) {
      error = e.message || "Error loading timers";
      console.error("Error loading timers:", e);
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

    try {
      ws = createTimerWebSocket(currentUser.sucursal_id, {
        onMessage: (data) => {
          if (data.type === "timers_update") {
            timers = data.timers || [];
          } else if (data.type === "timer_alert") {
            // Show alert notification
            alert(`Timer alert: ${data.message || "Some timers are ending soon"}`);
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

  function formatTimeLeft(seconds: number): string {
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${minutes}:${secs.toString().padStart(2, "0")}`;
  }
</script>

<div class="container mx-auto p-4">
  <div class="page-header">
    <h1 class="text-2xl font-bold">Recepción - Timers Activos</h1>
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
    <p>Cargando timers...</p>
  {:else if timers.length === 0}
    <p>No hay timers activos</p>
  {:else}
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {#each timers as timer}
        <div class="bg-white border rounded-lg p-4 shadow">
          <h3 class="font-semibold">{timer.child_name || "Sin nombre"}</h3>
          <p class="text-sm text-gray-600">Tiempo restante: {formatTimeLeft(timer.time_left_seconds || 0)}</p>
          <p class="text-xs text-gray-500">Estado: {timer.status}</p>
        </div>
      {/each}
    </div>
  {/if}

  <div class="mt-4">
    <p class="text-sm text-gray-500">
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




