<script lang="ts">
  /**
   * Monitor timers page - Real-time timer display.
   * 
   * Pure client-side real-time timer display for monitor role.
   */
  import { onMount, onDestroy } from "svelte";
  import { goto } from "$app/navigation";
  import { user, hasAccessSecure, getToken } from "$lib/stores/auth";
  import {
    timersStore,
    fetchActiveTimers,
    connectTimerWebSocket,
    disconnectTimerWebSocket,
  } from "$lib/stores/timers";

  let sucursalId = "";

  onMount(() => {
    // Verify user has access to monitor
    if (!$user || !hasAccessSecure("/monitor")) {
      goto("/monitor");
      return;
    }

    // Get sucursal_id from user or URL params
    const params = new URLSearchParams(window.location.search);
    sucursalId = $user?.sucursal_id || params.get("sucursal_id") || import.meta.env.VITE_SUCURSAL_ID || "";

    if (sucursalId) {
      fetchActiveTimers(sucursalId);
      const currentToken = getToken();
      if (currentToken) {
        connectTimerWebSocket(sucursalId, currentToken);
      }
    }
  });

  onDestroy(() => {
    disconnectTimerWebSocket();
  });

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

<div class="monitor-timers-page">
  <h1 class="page-title">Monitoreo de Timers - Tiempo Real</h1>

  {#if $timersStore.error}
    <div class="error-banner">{$timersStore.error}</div>
  {/if}

  <div class="timers-grid">
    {#each $timersStore.list as timer}
      <div class="timer-card {getStatusColor(timer.status)}" class:alert-status={timer.status === 'alert'}>
        <h2 class="timer-name">{timer.child_name || "Sin nombre"}</h2>
        <div class="timer-time">
          {formatTimeLeft(timer.time_left_seconds || 0)}
        </div>
        {#if timer.status === 'alert'}
          <div class="alert-badge">
            ⚠️ {Math.ceil((timer.time_left_seconds || 0) / 60)} min
          </div>
        {/if}
        <p class="timer-status">Estado: {timer.status}</p>
      </div>
    {/each}
  </div>

  {#if $timersStore.list.length === 0 && !$timersStore.error}
    <div class="empty-state">
      <p>No hay timers activos</p>
    </div>
  {/if}

  <div class="ws-status">
    {$timersStore.wsConnected ? "🟢 Conectado" : "🔴 Desconectado"}
  </div>
</div>

<style>
  .monitor-timers-page {
    min-height: 100vh;
    background: var(--theme-bg-primary);
    padding: var(--spacing-xl);
  }

  .page-title {
    font-family: var(--font-primary);
    font-size: var(--text-4xl);
    font-weight: 700;
    color: var(--text-primary);
    text-align: center;
    margin-bottom: var(--spacing-2xl);
  }

  .error-banner {
    padding: var(--spacing-md);
    background: rgba(211, 5, 84, 0.1);
    border: 1px solid var(--accent-danger);
    border-radius: var(--radius-md);
    color: var(--accent-danger);
    text-align: center;
    margin-bottom: var(--spacing-xl);
  }

  .timers-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: var(--spacing-xl);
    margin-bottom: var(--spacing-xl);
  }

  .timer-card {
    padding: var(--spacing-2xl);
    background: var(--theme-bg-elevated);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-lg);
    border: 3px solid;
    text-align: center;
  }

  .timer-card.bg-green-500 {
    border-color: var(--accent-success);
  }

  .timer-card.bg-yellow-500 {
    border-color: var(--accent-warning);
  }

  .timer-card.alert-status {
    animation: pulse-alert 2s ease-in-out infinite;
  }

  @keyframes pulse-alert {
    0%, 100% {
      box-shadow: 0 0 0 0 rgba(255, 206, 0, 0.4);
    }
    50% {
      box-shadow: 0 0 0 12px rgba(255, 206, 0, 0);
    }
  }

  .alert-badge {
    display: inline-flex;
    align-items: center;
    gap: var(--spacing-xs);
    padding: var(--spacing-xs) var(--spacing-sm);
    background: var(--accent-warning);
    color: var(--text-primary);
    border-radius: var(--radius-sm);
    font-size: var(--text-sm);
    font-weight: 600;
    margin-bottom: var(--spacing-sm);
  }

  .timer-card.bg-gray-500 {
    border-color: var(--text-muted);
  }

  .timer-card.bg-blue-500 {
    border-color: var(--accent-primary);
  }

  .timer-name {
    font-size: var(--text-2xl);
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: var(--spacing-lg);
  }

  .timer-time {
    font-size: var(--text-4xl);
    font-weight: 700;
    font-family: var(--font-mono);
    color: var(--accent-primary);
    margin-bottom: var(--spacing-md);
  }

  .timer-status {
    font-size: var(--text-sm);
    color: var(--text-secondary);
    text-transform: uppercase;
    font-weight: 600;
  }

  .empty-state {
    text-align: center;
    padding: var(--spacing-2xl);
    color: var(--text-muted);
    font-size: var(--text-lg);
  }

  .ws-status {
    position: fixed;
    bottom: var(--spacing-md);
    right: var(--spacing-md);
    padding: var(--spacing-sm) var(--spacing-md);
    background: var(--theme-bg-elevated);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
    font-size: var(--text-sm);
    color: var(--text-secondary);
  }

  @media (max-width: 768px) {
    .monitor-timers-page {
      padding: var(--spacing-md);
    }

    .timers-grid {
      grid-template-columns: 1fr;
    }

    .page-title {
      font-size: var(--text-2xl);
    }
  }
</style>

