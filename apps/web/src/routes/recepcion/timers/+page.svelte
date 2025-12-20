<script lang="ts">
  /**
   * Timers page - Active timers list for reception.
   * 
   * Shows active timers with real-time WebSocket updates.
   */
  import { onMount, onDestroy } from "svelte";
  import { goto } from "$app/navigation";
  import { user, token, hasAccessSecure, canEditSecure } from "$lib/stores/auth";
  import {
    timersStore,
    fetchActiveTimers,
    connectTimerWebSocket,
    disconnectTimerWebSocket,
  } from "$lib/stores/timers";
  import { Button } from "@kidyland/ui";
  import ExtendTimerModal from "$lib/components/shared/ExtendTimerModal.svelte";
  import type { Timer, Sale } from "@kidyland/shared/types";
  import { Clock, Clock3 } from "lucide-svelte";
  import { fetchSaleById } from "$lib/stores/sales-history";

  onMount(() => {
    // Verify user has access to recepcion
    if (!$user || !hasAccessSecure("/recepcion")) {
      goto("/recepcion");
      return;
    }

    sucursalId = $user?.sucursal_id || "";

    // Load timers
    if (sucursalId) {
      fetchActiveTimers(sucursalId);
    }

    // Connect WebSocket
    if (sucursalId && $token) {
      connectTimerWebSocket(sucursalId, $token);
    }
  });

  onDestroy(() => {
    disconnectTimerWebSocket();
  });

  let selectedTimer: Timer | null = null;
  let showExtendModal = false;
  let sucursalId = "";
  
  // Store sales data for each timer (for multi-child display)
  let timerSales: Map<string, Sale> = new Map();

  function formatTimeLeft(seconds: number): string {
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${minutes}:${secs.toString().padStart(2, "0")}`;
  }

  // Load sale data for a timer (for multi-child support)
  async function loadTimerSale(timer: Timer) {
    if (!timer.sale_id || timerSales.has(timer.sale_id)) {
      return; // Already loaded or no sale_id
    }
    
    try {
      const sale = await fetchSaleById(timer.sale_id);
      if (sale) {
        timerSales.set(timer.sale_id, sale);
        timerSales = timerSales; // Trigger reactivity
      }
    } catch (e) {
      // Silently fail - backward compatibility (timer.child_name will be used)
      console.warn(`Could not load sale ${timer.sale_id} for timer:`, e);
    }
  }

  // Format children names for display
  function formatChildrenNames(children: { name: string; age?: number }[]): string {
    if (!children || children.length === 0) return "";
    return children
      .map((child) => `${child.name}${child.age ? ` (${child.age})` : ""}`)
      .join(", ");
  }
</script>

<div class="timers-page">
  <div class="page-header">
    <button class="back-button" on:click={() => goto("/recepcion")}>← Volver</button>
    <h1 class="page-title">Timers Activos</h1>
  </div>

  {#if $timersStore.error}
    <div class="error-banner">{$timersStore.error}</div>
  {/if}

  {#if $timersStore.loading}
    <div class="loading-state">
      <div class="loading-spinner"></div>
      <p>Cargando timers...</p>
    </div>
  {:else if $timersStore.list.length === 0}
    <div class="empty-state">
      <div class="empty-icon">⏱️</div>
      <h3 class="empty-title">No hay timers activos</h3>
      <p class="empty-description">Los timers aparecerán aquí cuando se creen nuevas ventas de servicios.</p>
    </div>
  {:else}
    <div class="timers-grid">
{#each $timersStore.list.filter(timer => (timer.time_left_seconds || 0) > 0) as timer (timer.id)}
        {@const sale = timerSales.get(timer.sale_id || "")}
        {@const children = sale?.children}
        <div class="timer-card" class:alert={timer.status === 'alert'} class:ended={timer.status === 'ended'}>
          <div class="timer-header">
            {#if children && children.length > 0}
              <!-- Multi-child sale: show count and list -->
              <div class="timer-children-info">
                <h3 class="timer-child-name">{children.length} {children.length === 1 ? 'Niño' : 'Niños'}</h3>
                <p class="timer-children-list">{formatChildrenNames(children)}</p>
              </div>
            {:else}
              <!-- Single child or legacy format -->
              <h3 class="timer-child-name">{timer.child_name || "Niño sin nombre"}</h3>
            {/if}
            <span class="timer-status-badge" class:status-active={timer.status === 'active'} class:status-extended={timer.status === 'extended'} class:status-alert={timer.status === 'alert'} class:status-scheduled={timer.status === 'scheduled'} class:status-ended={timer.status === 'ended'}>
              {timer.status === 'active' ? 'Activo' : timer.status === 'extended' ? 'Extendido' : timer.status === 'alert' ? 'Alerta' : timer.status === 'scheduled' ? 'Programado' : 'Finalizado'}
            </span>
          </div>
          
          <div class="timer-time-container">
            <div class="timer-time-left">
              {formatTimeLeft(timer.time_left_seconds || 0)}
            </div>
            <div class="timer-time-label">
              {timer.status === 'scheduled' ? 'Duración Total' : 'Tiempo Restante'}
            </div>
          </div>

          {#if timer.status === 'scheduled'}
            <div class="scheduled-badge">
              <Clock3 size={18} strokeWidth={2} class="scheduled-icon" />
              <span class="scheduled-text">Programado - Iniciará en breve</span>
            </div>
          {/if}

          {#if timer.status === 'alert'}
            <div class="alert-badge">
              <span class="alert-icon">⚠️</span>
              <span class="alert-text">Alerta: {Math.ceil((timer.time_left_seconds || 0) / 60)} min restantes</span>
            </div>
          {/if}

          {#if canEditSecure("recepcion") && (timer.status === 'active' || timer.status === 'extended')}
            <div class="timer-actions">
              <Button
                variant="brutalist"
                size="small"
                on:click={async () => {
                  // Load sale data if not already loaded
                  await loadTimerSale(timer);
                  selectedTimer = timer;
                  showExtendModal = true;
                }}
                class="extend-button"
              >
                <Clock size={18} strokeWidth={2} />
                <span>Extender</span>
              </Button>
            </div>
          {/if}
        </div>
      {/each}
    </div>
  {/if}

  <!-- WebSocket status hidden - functionality works in background -->
  <!-- Uncomment below for debugging if needed -->
  <!--
  <div class="websocket-status" class:connected={$timersStore.wsConnected} class:disconnected={!$timersStore.wsConnected}>
    <span class="ws-indicator"></span>
    <span class="ws-text">WebSocket: {$timersStore.wsConnected ? "Conectado" : "Desconectado"}</span>
  </div>
  -->
</div>

<!-- Extend Timer Modal -->
{#if showExtendModal && selectedTimer}
  <ExtendTimerModal
    open={showExtendModal}
    timer={selectedTimer}
    saleId={selectedTimer.sale_id}
    on:close={() => {
      showExtendModal = false;
      selectedTimer = null;
    }}
    on:success={() => {
      // Timer is already updated immediately via updateTimerFromExtension()
      // WebSocket will sync the update across all clients within 5 seconds
      // No need to refetch, which could cause a brief flash of old data
    }}
  />
{/if}

<style>
  .timers-page {
    min-height: 100vh;
    background: var(--theme-bg-primary);
    padding: var(--spacing-xl);
  }

  .page-header {
    display: flex;
    align-items: center;
    gap: var(--spacing-md);
    margin-bottom: var(--spacing-xl);
    flex-wrap: wrap;
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
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }

  .back-button:hover {
    background: var(--theme-bg-secondary);
    transform: translateY(-2px);
    border-color: rgba(0, 147, 247, 0.5);
    box-shadow: 0 4px 12px rgba(0, 147, 247, 0.2);
  }

  .page-title {
    font-family: var(--font-primary);
    font-size: var(--text-3xl);
    font-weight: 700;
    color: var(--text-primary);
    margin: 0;
    
    /* Efecto 3D - solo sombreado, sin animaciones */
    text-shadow: 
      0 0.05em 0 rgba(0, 0, 0, 0.1),
      0 0.1em 0 rgba(0, 0, 0, 0.1),
      0 0.15em 0 rgba(0, 0, 0, 0.1),
      0 0.2em 0 rgba(0, 0, 0, 0.1),
      0 0.25em 0 rgba(0, 0, 0, 0.1),
      0 0.25em 0.02em rgba(0, 0, 0, 0.15),
      0 0.28em 0.2em rgba(0, 0, 0, 0.25);
  }

  .error-banner {
    padding: var(--spacing-md);
    background: rgba(211, 5, 84, 0.1);
    border: 1px solid var(--accent-danger);
    border-radius: var(--radius-md);
    color: var(--accent-danger);
    margin-bottom: var(--spacing-lg);
    text-align: center;
    font-weight: 500;
    box-shadow: 0 0 20px rgba(211, 5, 84, 0.2);
  }

  .loading-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: var(--spacing-2xl);
    gap: var(--spacing-md);
  }

  .loading-spinner {
    width: 48px;
    height: 48px;
    border: 4px solid var(--border-primary);
    border-top-color: var(--accent-primary);
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
  }

  .loading-state p {
    color: var(--text-secondary);
    font-size: var(--text-lg);
    margin: 0;
  }

  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: var(--spacing-2xl);
    text-align: center;
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

  .empty-icon {
    font-size: 64px;
    margin-bottom: var(--spacing-md);
    opacity: 0.6;
  }

  .empty-title {
    font-family: var(--font-primary);
    font-size: var(--text-2xl);
    font-weight: 700;
    color: var(--text-primary);
    margin: 0 0 var(--spacing-sm) 0;
  }

  .empty-description {
    color: var(--text-secondary);
    font-size: var(--text-base);
    margin: 0;
    max-width: 400px;
  }

  .timers-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: var(--spacing-xl);
    margin-bottom: var(--spacing-xl);
  }

  .timer-card {
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
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    display: flex;
    flex-direction: column;
    gap: var(--spacing-md);
  }

  .timer-card:hover {
    transform: translateY(-4px);
    border-color: rgba(0, 147, 247, 0.5);
    box-shadow: 
      0 12px 32px rgba(0, 0, 0, 0.2),
      0 0 30px var(--glow-primary),
      0 0 40px var(--glow-secondary),
      inset 0 1px 0 rgba(255, 255, 255, 0.1);
  }

  .timer-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: var(--spacing-sm);
    margin-bottom: var(--spacing-xs);
  }

  .timer-child-name {
    font-size: var(--text-xl);
    font-weight: 700;
    color: var(--text-primary);
    margin: 0;
    flex: 1;
    line-height: 1.3;
  }

  .timer-status-badge {
    padding: var(--spacing-xs) var(--spacing-sm);
    border-radius: var(--radius-sm);
    font-size: var(--text-xs);
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    white-space: nowrap;
    flex-shrink: 0;
  }

  .timer-status-badge.status-active {
    background: rgba(61, 173, 9, 0.2);
    color: var(--accent-success);
    border: 1px solid var(--accent-success);
  }

  .timer-status-badge.status-extended {
    background: rgba(0, 147, 247, 0.2);
    color: var(--accent-primary);
    border: 1px solid var(--accent-primary);
  }

  .timer-status-badge.status-alert {
    background: rgba(255, 206, 0, 0.2);
    color: var(--accent-warning);
    border: 1px solid var(--accent-warning);
  }

  .timer-status-badge.status-scheduled {
    background: rgba(147, 51, 234, 0.2);
    color: #9333ea;
    border: 1px solid #9333ea;
  }

  .timer-status-badge.status-ended {
    background: rgba(211, 5, 84, 0.2);
    color: var(--accent-danger);
    border: 1px solid var(--accent-danger);
  }

  .timer-time-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: var(--spacing-xs);
    padding: var(--spacing-lg);
    background: rgba(0, 147, 247, 0.05);
    border-radius: var(--radius-lg);
    border: 1px solid rgba(0, 147, 247, 0.2);
    margin: var(--spacing-sm) 0;
  }

  .timer-time-left {
    font-size: var(--text-4xl);
    font-weight: 700;
    font-family: var(--font-mono);
    color: var(--accent-primary);
    line-height: 1;
    text-shadow: 0 0 20px var(--glow-primary);
  }

  .timer-time-label {
    font-size: var(--text-sm);
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    font-weight: 500;
  }

  .alert-badge {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    padding: var(--spacing-sm) var(--spacing-md);
    background: rgba(255, 206, 0, 0.15);
    border: 1px solid var(--accent-warning);
    border-radius: var(--radius-md);
    font-size: var(--text-sm);
    font-weight: 600;
    color: var(--accent-warning);
    box-shadow: 0 0 20px rgba(255, 206, 0, 0.3);
  }

  .alert-icon {
    font-size: var(--text-lg);
  }

  .alert-text {
    flex: 1;
  }

  .scheduled-badge {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    padding: var(--spacing-sm) var(--spacing-md);
    background: rgba(147, 51, 234, 0.15);
    border: 1px solid #9333ea;
    border-radius: var(--radius-md);
    font-size: var(--text-sm);
    font-weight: 600;
    color: #9333ea;
    box-shadow: 0 0 20px rgba(147, 51, 234, 0.3);
    margin-top: var(--spacing-sm);
  }

  .scheduled-icon {
    flex-shrink: 0;
    color: #9333ea;
  }

  .scheduled-text {
    flex: 1;
  }

  .timer-card.alert {
    border-color: var(--accent-warning);
    animation: pulse-alert 2s ease-in-out infinite;
  }

  @keyframes pulse-alert {
    0%, 100% {
      box-shadow: 
        0 8px 24px rgba(0, 0, 0, 0.15),
        0 0 20px var(--glow-primary),
        0 0 0 0 rgba(255, 206, 0, 0.4);
    }
    50% {
      box-shadow: 
        0 12px 32px rgba(0, 0, 0, 0.2),
        0 0 30px var(--glow-primary),
        0 0 40px rgba(255, 206, 0, 0.4),
        0 0 0 8px rgba(255, 206, 0, 0);
    }
  }

  .timer-card.ended {
    border-color: var(--accent-danger);
    background: rgba(211, 5, 84, 0.05);
    opacity: 0.7;
  }

  .timer-actions {
    margin-top: var(--spacing-sm);
    display: flex;
    justify-content: flex-end;
  }

  .extend-button {
    min-width: 120px;
    display: inline-flex !important;
    align-items: center;
    gap: var(--spacing-xs);
    justify-content: center;
    padding: var(--spacing-sm) var(--spacing-md);
  }

  .extend-button :global(svg) {
    flex-shrink: 0;
  }

  .extend-button :global(span) {
    display: inline-block;
    white-space: nowrap;
  }

  .websocket-status {
    position: fixed;
    bottom: var(--spacing-md);
    right: var(--spacing-md);
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    padding: var(--spacing-sm) var(--spacing-md);
    background: var(--theme-bg-card);
    backdrop-filter: blur(16px) saturate(150%);
    -webkit-backdrop-filter: blur(16px) saturate(150%);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
    font-size: var(--text-sm);
    color: var(--text-secondary);
    box-shadow: 
      0 4px 12px rgba(0, 0, 0, 0.15),
      0 0 10px var(--glow-primary);
    z-index: 50;
  }

  .ws-indicator {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    flex-shrink: 0;
    transition: all 0.3s ease;
  }

  .websocket-status.connected .ws-indicator {
    background: var(--accent-success);
    box-shadow: 0 0 8px var(--accent-success);
  }

  .websocket-status.disconnected .ws-indicator {
    background: var(--accent-danger);
    box-shadow: 0 0 8px var(--accent-danger);
  }

  .ws-text {
    font-weight: 500;
  }

  @media (max-width: 768px) {
    .timers-page {
      padding: var(--spacing-md);
    }

    .page-header {
      flex-direction: column;
      align-items: stretch;
      gap: var(--spacing-sm);
    }

    .page-title {
      font-size: var(--text-2xl);
      text-align: center;
    }

    .back-button {
      width: 100%;
      justify-content: center;
    }

    .timers-grid {
      grid-template-columns: 1fr;
      gap: var(--spacing-lg);
    }

    .timer-card {
      padding: var(--spacing-lg);
    }

    .timer-time-left {
      font-size: var(--text-3xl);
    }

    .timer-actions {
      width: 100%;
      flex-direction: column;
      align-items: stretch;
      gap: var(--spacing-sm);
    }

    .timer-actions :global(.btn-brutalist) {
      width: 100%;
      min-height: 48px; /* Minimum touch target size for accessibility */
      justify-content: center;
      display: flex !important;
      align-items: center;
      gap: var(--spacing-xs);
    }

    .websocket-status {
      position: relative;
      bottom: auto;
      right: auto;
      margin-top: var(--spacing-xl);
      width: 100%;
      justify-content: center;
    }
  }

  /* Tablet adjustments */
  @media (min-width: 769px) and (max-width: 1024px) {
    .timer-actions {
      width: 100%;
      flex-direction: column;
      align-items: stretch;
    }

    .timer-actions :global(.btn-brutalist) {
      width: 100%;
      min-height: 44px;
      justify-content: center;
      display: flex !important;
      align-items: center;
      gap: var(--spacing-xs);
    }
  }

  /* Prevent hover transform issues on touch devices */
  @media (hover: none) and (pointer: coarse) {
    .timer-card:hover {
      transform: none;
      box-shadow: 
        0 8px 24px rgba(0, 0, 0, 0.15),
        0 0 20px var(--glow-primary),
        inset 0 1px 0 rgba(255, 255, 255, 0.05);
    }

    .back-button:hover {
      transform: none;
    }

    .timer-actions :global(.btn-brutalist:hover) {
      transform: none;
      box-shadow: 3px 3px 0px 0px var(--accent-primary);
      border-width: 2px;
    }
  }
</style>

