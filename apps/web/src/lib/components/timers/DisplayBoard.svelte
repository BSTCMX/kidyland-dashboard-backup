<script lang="ts">
  /**
   * DisplayBoard - Fullscreen timer display component
   * 
   * Reusable component for displaying timers in a large, readable format.
   * Can be used in fullscreen mode or as part of a page.
   * 
   * Features:
   * - Grid layout of active timers
   * - Large, readable countdown from distance
   * - Color-coded by urgency (green/yellow/red)
   * - Responsive design
   */
  import type { Timer } from '@kidyland/shared/types';
  
  export let timers: Timer[] = [];
  export let loading: boolean = false;
  
  // Format seconds to MM:SS
  function formatTime(seconds: number): string {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  }
  
  // Get color class based on time remaining
  function getUrgencyClass(seconds: number): string {
    const minutes = seconds / 60;
    if (minutes > 10) return 'safe';
    if (minutes > 5) return 'warning';
    return 'urgent';
  }
</script>

<div class="display-board">
  <header class="board-header">
    <h1 class="board-title">Timers Activos</h1>
    <div class="timer-count">
      {timers.length} {timers.length === 1 ? 'Timer' : 'Timers'}
    </div>
  </header>

  <div class="timers-grid">
    {#if loading && timers.length === 0}
      <div class="loading-state">
        <div class="spinner"></div>
        <p>Cargando timers...</p>
      </div>
    {:else if timers.length === 0}
      <div class="empty-state">
        <div class="empty-icon">⏱️</div>
        <p class="empty-message">No hay timers activos</p>
      </div>
    {:else}
      {#each timers as timer (timer.id)}
        <div class="timer-card {getUrgencyClass(timer.time_left_seconds)}">
          <div class="timer-name">{timer.child_name}</div>
          <div class="timer-countdown">{formatTime(timer.time_left_seconds)}</div>
          <div class="timer-age">{timer.child_age} años</div>
          {#if timer.status === 'scheduled'}
            <div class="timer-status">Programado</div>
          {/if}
        </div>
      {/each}
    {/if}
  </div>
</div>

<style>
  .display-board {
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
    padding: 2rem;
    box-sizing: border-box;
    background: var(--color-background-dark, #1a1a1a);
    color: var(--color-text-light, #ffffff);
  }

  .board-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 2rem;
    padding-bottom: 1rem;
    border-bottom: 2px solid rgba(255, 255, 255, 0.1);
  }

  .board-title {
    font-size: 2.5rem;
    font-weight: 700;
    margin: 0;
    color: #ffffff;
  }

  .timer-count {
    font-size: 1.5rem;
    color: rgba(255, 255, 255, 0.7);
    font-weight: 500;
  }

  .timers-grid {
    flex: 1;
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 2rem;
    overflow-y: auto;
    padding-right: 0.5rem;
  }

  /* Scrollbar styling */
  .timers-grid::-webkit-scrollbar {
    width: 8px;
  }

  .timers-grid::-webkit-scrollbar-track {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 4px;
  }

  .timers-grid::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.2);
    border-radius: 4px;
  }

  .timers-grid::-webkit-scrollbar-thumb:hover {
    background: rgba(255, 255, 255, 0.3);
  }

  .timer-card {
    background: linear-gradient(135deg, #2d3748 0%, #1a202c 100%);
    border-radius: 1rem;
    padding: 2rem;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    transition: all 0.3s ease;
    border: 3px solid transparent;
    min-height: 200px;
    position: relative;
  }

  .timer-card.safe {
    border-color: #48bb78;
    background: linear-gradient(135deg, #2f855a 0%, #276749 100%);
  }

  .timer-card.warning {
    border-color: #ecc94b;
    background: linear-gradient(135deg, #d69e2e 0%, #b7791f 100%);
  }

  .timer-card.urgent {
    border-color: #f56565;
    background: linear-gradient(135deg, #e53e3e 0%, #c53030 100%);
    animation: pulse 2s ease-in-out infinite;
  }

  @keyframes pulse {
    0%, 100% {
      box-shadow: 0 0 20px rgba(245, 101, 101, 0.5);
    }
    50% {
      box-shadow: 0 0 40px rgba(245, 101, 101, 0.8);
    }
  }

  .timer-name {
    font-size: 2rem;
    font-weight: 700;
    margin-bottom: 1rem;
    color: #ffffff;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .timer-countdown {
    font-size: 4rem;
    font-weight: 900;
    font-family: 'Courier New', monospace;
    color: #ffffff;
    margin-bottom: 0.5rem;
    line-height: 1;
  }

  .timer-age {
    font-size: 1.2rem;
    color: rgba(255, 255, 255, 0.7);
    font-weight: 500;
  }

  .timer-status {
    position: absolute;
    top: 1rem;
    right: 1rem;
    background: rgba(147, 51, 234, 0.3);
    color: #9333ea;
    padding: 0.25rem 0.75rem;
    border-radius: 0.5rem;
    font-size: 0.875rem;
    font-weight: 600;
    border: 1px solid #9333ea;
  }

  .loading-state,
  .empty-state {
    grid-column: 1 / -1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    color: rgba(255, 255, 255, 0.5);
  }

  .spinner {
    width: 60px;
    height: 60px;
    border: 4px solid rgba(255, 255, 255, 0.1);
    border-top-color: #ffffff;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin-bottom: 1rem;
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
  }

  .loading-state p,
  .empty-message {
    font-size: 1.5rem;
    margin: 0;
  }

  .empty-icon {
    font-size: 5rem;
    margin-bottom: 1rem;
    opacity: 0.3;
  }

  /* Responsive adjustments */
  @media (min-width: 1200px) {
    .timers-grid {
      grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
    }
  }

  @media (min-width: 1600px) {
    .timers-grid {
      grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
    }

    .board-title {
      font-size: 3rem;
    }

    .timer-countdown {
      font-size: 5rem;
    }
  }

  @media (max-width: 768px) {
    .display-board {
      padding: 1rem;
    }

    .board-title {
      font-size: 1.8rem;
    }

    .timer-count {
      font-size: 1.2rem;
    }

    .timers-grid {
      grid-template-columns: 1fr;
      gap: 1rem;
    }

    .timer-card {
      min-height: 150px;
      padding: 1.5rem;
    }

    .timer-name {
      font-size: 1.5rem;
    }

    .timer-countdown {
      font-size: 3rem;
    }
  }
</style>
