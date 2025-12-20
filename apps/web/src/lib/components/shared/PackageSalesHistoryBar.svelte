<script lang="ts">
  /**
   * PackageSalesHistoryBar component - Collapsible sales history bar for packages.
   * 
   * Displays a horizontal, collapsible bar at the top of the packages page
   * showing package sales history without interfering with package layout.
   */
  import { ChevronDown, ChevronUp } from "lucide-svelte";
  import SalesHistory from "./SalesHistory.svelte";

  let collapsed = true;

  function toggleCollapse() {
    collapsed = !collapsed;
  }
</script>

<div class="package-history-bar">
  <button class="history-bar-header" on:click={toggleCollapse} aria-label={collapsed ? "Expandir historial" : "Colapsar historial"}>
    <div class="header-content">
      <h2 class="bar-title">Historial de Ventas - Paquetes</h2>
      <div class="toggle-icon">
        {#if collapsed}
          <ChevronDown size={20} strokeWidth={2} />
        {:else}
          <ChevronUp size={20} strokeWidth={2} />
        {/if}
      </div>
    </div>
  </button>

  {#if !collapsed}
    <div class="history-bar-content">
      <SalesHistory saleType="package" packageType="service" />
    </div>
  {/if}
</div>

<style>
  .package-history-bar {
    position: sticky;
    top: 0;
    z-index: 50;
    background: var(--theme-bg-elevated);
    backdrop-filter: blur(16px) saturate(150%);
    -webkit-backdrop-filter: blur(16px) saturate(150%);
    border-bottom: 2px solid var(--border-primary);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1), 0 0 20px rgba(0, 147, 247, 0.1);
    margin-bottom: var(--spacing-lg);
  }

  .history-bar-header {
    width: 100%;
    padding: var(--spacing-md) var(--spacing-lg);
    background: transparent;
    border: none;
    cursor: pointer;
    transition: background-color 0.2s ease;
  }

  .history-bar-header:hover {
    background: rgba(0, 147, 247, 0.05);
  }

  .history-bar-header:active {
    background: rgba(0, 147, 247, 0.1);
  }

  .header-content {
    display: flex;
    justify-content: space-between;
    align-items: center;
    width: 100%;
  }

  .bar-title {
    font-family: var(--font-primary);
    font-size: var(--text-lg);
    font-weight: 700;
    color: var(--text-primary);
    margin: 0;
    text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.1);
  }

  .toggle-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--accent-primary);
    transition: transform 0.2s ease;
  }

  .history-bar-content {
    max-height: 60vh;
    overflow-y: auto;
    padding: var(--spacing-md);
    background: var(--theme-bg-card);
    border-top: 1px solid var(--border-primary);
  }

  /* Scrollbar styling */
  .history-bar-content::-webkit-scrollbar {
    width: 8px;
  }

  .history-bar-content::-webkit-scrollbar-track {
    background: var(--theme-bg-secondary);
    border-radius: 4px;
  }

  .history-bar-content::-webkit-scrollbar-thumb {
    background: var(--accent-primary);
    border-radius: 4px;
  }

  .history-bar-content::-webkit-scrollbar-thumb:hover {
    background: var(--accent-primary-hover);
  }

  /* Responsive adjustments */
  @media (max-width: 768px) {
    .history-bar-header {
      padding: var(--spacing-sm) var(--spacing-md);
    }

    .bar-title {
      font-size: var(--text-base);
    }

    .history-bar-content {
      max-height: 50vh;
      padding: var(--spacing-sm);
    }
  }

  @media (max-width: 480px) {
    .bar-title {
      font-size: var(--text-sm);
    }

    .history-bar-content {
      max-height: 40vh;
    }
  }
</style>


