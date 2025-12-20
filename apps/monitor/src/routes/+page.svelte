<script lang="ts">
  /**
   * Monitor page - Pure client-side real-time timer display.
   * No authentication required (public display).
   */
  import { onMount, onDestroy } from "svelte";
  import { createTimerWebSocket } from "@kidyland/utils";
  import type { Timer } from "@kidyland/shared/types";

  let timers: Timer[] = [];
  let ws: ReturnType<typeof createTimerWebSocket> | null = null;
  let error: string | null = null;
  let sucursalId = ""; // Can be set via query param or env

  onMount(() => {
    // Get sucursal_id from URL params or env
    const params = new URLSearchParams(window.location.search);
    sucursalId = params.get("sucursal_id") || import.meta.env.VITE_SUCURSAL_ID || "";

    if (sucursalId) {
      connectWebSocket();
    } else {
      error = "Sucursal ID required";
    }
  });

  onDestroy(() => {
    if (ws) {
      ws.disconnect();
    }
  });

  function connectWebSocket() {
    try {
      // For monitor, we might need a public token or different auth
      // For now, using the same WebSocket endpoint
      // Note: Monitor might need special auth or public endpoint
      const wsUrl = import.meta.env.VITE_WS_URL || "ws://localhost:8000";
      
      // Import WebSocketClient dynamically
      import("@kidyland/utils").then(({ WebSocketClient }) => {
        ws = new WebSocketClient({
        url: `${wsUrl}/ws/timers`,
        params: {
          token,
          sucursal_id: sucursalId,
        },
        onMessage: (data) => {
          if (data.type === "timers_update") {
            timers = data.timers || [];
          }
        },
        onError: (err) => {
          console.error("WebSocket error:", err);
          error = "Connection error";
        },
        onClose: () => {
          console.log("WebSocket disconnected");
        },
      });

        ws.connect();
      }).catch((e: any) => {
        console.error("Error creating WebSocket:", e);
        error = e.message || "Error connecting";
      });
    } catch (e: any) {
      console.error("Error importing WebSocket:", e);
      error = e.message || "Error connecting";
    }
  }

  function formatTimeLeft(seconds: number): string {
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${minutes}:${secs.toString().padStart(2, "0")}`;
  }

  function getStatusColor(status: string): string {
    switch (status) {
      case "active":
        return "bg-green-500";
      case "alert":
        return "bg-yellow-500";
      case "ended":
        return "bg-gray-500";
      default:
        return "bg-blue-500";
    }
  }
</script>

<div class="min-h-screen bg-gray-900 text-white p-8">
  <h1 class="text-4xl font-bold mb-8 text-center">Monitoreo de Timers</h1>

  {#if error}
    <div class="bg-red-600 text-white px-4 py-3 rounded mb-4 text-center">
      {error}
    </div>
  {/if}

  <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
    {#each timers as timer}
      <div class="bg-gray-800 rounded-lg p-6 shadow-lg border-2 {getStatusColor(timer.status)}">
        <h2 class="text-2xl font-bold mb-2">{timer.child_name || "Sin nombre"}</h2>
        <div class="text-4xl font-mono font-bold mb-2">
          {formatTimeLeft(timer.time_left_seconds || 0)}
        </div>
        <p class="text-sm opacity-75">Estado: {timer.status}</p>
      </div>
    {/each}
  </div>

  {#if timers.length === 0 && !error}
    <div class="text-center text-gray-400 mt-8">
      <p>No hay timers activos</p>
    </div>
  {/if}

  <div class="fixed bottom-4 right-4 text-sm text-gray-400">
    {ws?.isConnected() ? "🟢 Conectado" : "🔴 Desconectado"}
  </div>
</div>

<style>
  :global(body) {
    margin: 0;
    font-family: system-ui, -apple-system, sans-serif;
  }
</style>

