<script lang="ts">
  import { onMount, onDestroy } from "svelte";
  import { timersStore, startTimerPolling, stopTimerPolling } from "$lib/stores/timers";
  import type { PageData } from "./$types";

  export let data: PageData;

  const DISPLAY_THRESHOLD_MINUTES = 5; // Only show timers ≤5 minutes
  const FINISHED_MESSAGE_DURATION = 120000; // 2 minutes in milliseconds

  // Track finished timers with timestamp
  let finishedTimers = new Map<string, { timer: any; finishedAt: number }>();
  let cleanupInterval: number;
  let allDisplayItems: Array<{ type: string; timer: any }> = []; // Initialize for SSR

  // Filter timers for display (≤5 minutes)
  $: displayTimers = $timersStore.list.filter((timer) => {
    const minutes = Math.ceil((timer.time_left_seconds || 0) / 60);
    return minutes > 0 && minutes <= DISPLAY_THRESHOLD_MINUTES;
  });

  // Detect newly finished timers
  $: {
    $timersStore.list.forEach((timer) => {
      if (timer.time_left_seconds <= 0 && !finishedTimers.has(timer.id)) {
        finishedTimers.set(timer.id, {
          timer,
          finishedAt: Date.now(),
        });
        finishedTimers = finishedTimers; // Trigger reactivity
      }
    });
  }

  // Combined list: active timers + finished timers (within message duration)
  // Prevent duplicates: exclude finished timers that are now active (e.g., after extension)
  $: {
    const activeIds = new Set(displayTimers.map(t => t.id));
    
    allDisplayItems = [
      ...displayTimers.map((t) => ({ type: "active", timer: t })),
      ...Array.from(finishedTimers.values())
        .filter((item) => 
          Date.now() - item.finishedAt < FINISHED_MESSAGE_DURATION &&
          !activeIds.has(item.timer.id)  // Exclude if timer is now active
        )
        .map((item) => ({ type: "finished", timer: item.timer })),
    ];
  }

  function formatTimeLeft(seconds: number): string {
    if (seconds <= 0) return "00:00";
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
  }

  function getUrgencyClass(seconds: number): string {
    const minutes = Math.ceil(seconds / 60);
    if (minutes <= 1) return "critical";
    if (minutes <= 2) return "high";
    if (minutes <= 3) return "medium";
    return "low";
  }

  function formatChildrenNames(timer: any): string {
    // Check if timer has children array (multi-child sale)
    if (timer.children && Array.isArray(timer.children) && timer.children.length > 0) {
      return timer.children.map((child: any) => child.name).join(", ");
    }
    // Fallback to child_name (single child)
    return timer.child_name || "Niño sin nombre";
  }

  onMount(() => {
    if (data.sucursalId) {
      startTimerPolling(data.sucursalId);
    }

    // Cleanup finished timers every 10 seconds
    cleanupInterval = window.setInterval(() => {
      const now = Date.now();
      let hasChanges = false;

      finishedTimers.forEach((item, id) => {
        if (now - item.finishedAt > FINISHED_MESSAGE_DURATION) {
          finishedTimers.delete(id);
          hasChanges = true;
        }
      });

      if (hasChanges) {
        finishedTimers = finishedTimers; // Trigger reactivity
      }
    }, 10000);
  });

  onDestroy(() => {
    stopTimerPolling();
    if (cleanupInterval) {
      clearInterval(cleanupInterval);
    }
  });
</script>

<div class="display-container">
  <!-- Header - Clean design for fullscreen display -->
  <div class="display-header">
    <h1 class="display-title">Timers Activos</h1>
  </div>

  <!-- Content -->
  {#if $timersStore.loading && allDisplayItems.length === 0}
    <div class="display-loading">
      <div class="loading-spinner"></div>
      <p>Cargando timers...</p>
    </div>
  {:else if allDisplayItems.length === 0}
    <div class="display-empty">
      <div class="empty-icon">⏱️</div>
      <h2>No hay timers próximos a finalizar</h2>
      <p>Los timers aparecerán aquí cuando falten 5 minutos o menos</p>
    </div>
  {:else}
    <div class="display-grid">
      {#each allDisplayItems as item (item.timer.id)}
        {#if item.type === "active"}
          <div class="timer-card {getUrgencyClass(item.timer.time_left_seconds)}">
            <div class="timer-child-name">{formatChildrenNames(item.timer)}</div>
            <div class="timer-countdown">{formatTimeLeft(item.timer.time_left_seconds)}</div>
            <div class="timer-label">Tiempo Restante</div>
          </div>
        {:else}
          <div class="timer-card finished">
            <div class="timer-child-name">{formatChildrenNames(item.timer)}</div>
            <div class="finished-message">¡Tu tiempo terminó!</div>
            <div class="finished-icon">
              <img src="/favicon.svg" alt="Kidyland" />
            </div>
          </div>
        {/if}
      {/each}
    </div>
  {/if}

  <!-- Kidyland Logo Watermark - Branding -->
  <div class="logo-watermark">
    <img src="/logo.svg" alt="Kidyland" />
  </div>
</div>

<style>
  .display-container {
    width: 100%;
    height: 100%;
    padding: clamp(1rem, 3vw, 3rem);
    display: flex;
    flex-direction: column;
    gap: clamp(1rem, 2vw, 2rem);
    position: relative;
  }

  /* Header - Clean design for fullscreen */
  .display-header {
    display: flex;
    justify-content: center;
    align-items: center;
    margin-bottom: clamp(1rem, 2vw, 2rem);
  }

  .display-title {
    font-size: clamp(1.5rem, 3vw, 2.5rem);
    font-weight: 600;
    color: rgba(255, 255, 255, 0.9);
    margin: 0;
    text-align: center;
    letter-spacing: 0.05em;
  }

  /* Loading state */
  .display-loading {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 1rem;
  }

  .loading-spinner {
    width: 48px;
    height: 48px;
    border: 4px solid rgba(255, 255, 255, 0.1);
    border-top-color: white;
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
  }

  .display-loading p {
    font-size: var(--text-lg);
    color: rgba(255, 255, 255, 0.7);
  }

  /* Empty state */
  .display-empty {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 1rem;
    text-align: center;
  }

  .empty-icon {
    font-size: clamp(3rem, 8vw, 6rem);
  }

  .display-empty h2 {
    font-size: clamp(1.25rem, 3vw, 2rem);
    font-weight: 600;
    color: white;
    margin: 0;
  }

  .display-empty p {
    font-size: clamp(1rem, 2vw, 1.25rem);
    color: rgba(255, 255, 255, 0.7);
    max-width: 600px;
  }

  /* Grid - responsive */
  .display-grid {
    flex: 1;
    display: grid;
    grid-template-columns: 1fr;
    gap: clamp(1rem, 2vw, 2rem);
    overflow-y: auto;
    padding-bottom: 1rem;
  }

  /* Tablet: 2 columns */
  @media (min-width: 768px) {
    .display-grid {
      grid-template-columns: repeat(2, 1fr);
    }
  }

  /* Desktop: auto-fit 3-4 columns */
  @media (min-width: 1024px) {
    .display-grid {
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    }
  }

  /* Tablet portrait: 1 large column */
  @media (orientation: portrait) and (min-width: 768px) {
    .display-grid {
      grid-template-columns: 1fr;
    }
  }

  /* Timer cards */
  .timer-card {
    background: rgba(255, 255, 255, 0.05);
    border: 2px solid rgba(255, 255, 255, 0.1);
    border-radius: var(--radius-lg);
    padding: clamp(1.5rem, 3vw, 3rem);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: clamp(0.75rem, 1.5vw, 1.5rem);
    transition: all 0.3s ease;
    min-height: 200px;
  }

  .timer-child-name {
    font-size: clamp(1.25rem, 3vw, 2rem);
    font-weight: 700;
    color: white;
    text-align: center;
    word-break: break-word;
  }

  .timer-countdown {
    font-size: clamp(3rem, 8vw, 6rem);
    font-weight: 700;
    font-variant-numeric: tabular-nums;
    line-height: 1;
    color: white;
  }

  .timer-label {
    font-size: clamp(0.875rem, 1.5vw, 1.125rem);
    color: rgba(255, 255, 255, 0.7);
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  /* Urgency colors */
  .timer-card.critical {
    background: rgba(239, 68, 68, 0.2);
    border-color: #ef4444;
    animation: pulse-border 1s ease-in-out infinite;
  }

  .timer-card.high {
    background: rgba(249, 115, 22, 0.2);
    border-color: #f97316;
  }

  .timer-card.medium {
    background: rgba(234, 179, 8, 0.2);
    border-color: #eab308;
  }

  .timer-card.low {
    background: rgba(34, 197, 94, 0.2);
    border-color: #22c55e;
  }

  @keyframes pulse-border {
    0%, 100% { border-color: #ef4444; }
    50% { border-color: #dc2626; }
  }

  /* Finished timer */
  .timer-card.finished {
    background: rgba(168, 85, 247, 0.2);
    border-color: #a855f7;
  }

  .finished-message {
    font-size: clamp(1.5rem, 4vw, 3rem);
    font-weight: 700;
    color: #a855f7;
    text-align: center;
  }

  .finished-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: clamp(3rem, 8vw, 6rem);
    height: clamp(3rem, 8vw, 6rem);
  }

  .finished-icon img {
    width: 100%;
    height: 100%;
    object-fit: contain;
    filter: drop-shadow(0 2px 8px rgba(168, 85, 247, 0.4));
  }

  /* Scrollbar styling */
  .display-grid::-webkit-scrollbar {
    width: 8px;
  }

  .display-grid::-webkit-scrollbar-track {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 4px;
  }

  .display-grid::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.2);
    border-radius: 4px;
  }

  .display-grid::-webkit-scrollbar-thumb:hover {
    background: rgba(255, 255, 255, 0.3);
  }

  /* Logo Watermark - Branding */
  .logo-watermark {
    position: fixed;
    bottom: 1.5rem;
    left: 1.5rem;
    z-index: 10;
    opacity: 0.7;
    transition: opacity 0.3s ease;
  }

  .logo-watermark:hover {
    opacity: 1;
  }

  .logo-watermark img {
    width: clamp(80px, 10vw, 120px);
    height: auto;
    filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.3));
  }

  /* Responsive: Hide logo on very small screens */
  @media (max-width: 480px) {
    .logo-watermark {
      width: 60px;
    }
  }
</style>
