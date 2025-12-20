<script lang="ts">
  /**
   * TabsDesktop - Desktop tabs navigation component.
   * 
   * Renders horizontal tabs for desktop viewports.
   * Maintains accessibility with ARIA attributes.
   */
  import type { ComponentType } from 'svelte';
  import type { SvelteComponent } from 'svelte';

  export interface Tab {
    id: string;
    label: string;
    icon: ComponentType<SvelteComponent>;
  }

  export let tabs: Tab[] = [];
  export let activeTab: string = '';
  export let onTabChange: (tabId: string) => void = () => {};
</script>

<div class="tabs-nav" role="tablist">
  {#each tabs as tab}
    <button
      class="tab-button"
      class:active={activeTab === tab.id}
      on:click={() => onTabChange(tab.id)}
      role="tab"
      aria-selected={activeTab === tab.id}
      aria-controls={`tabpanel-${tab.id}`}
    >
      <svelte:component this={tab.icon} size={18} strokeWidth={1.5} />
      <span class="tab-label">{tab.label}</span>
    </button>
  {/each}
</div>

<style>
  .tabs-nav {
    display: flex;
    gap: var(--spacing-xs);
    padding: var(--spacing-sm);
    background: var(--theme-bg-elevated);
    border-bottom: 1px solid var(--border-primary);
    overflow-x: auto;
    scrollbar-width: thin;
    scrollbar-color: var(--border-primary) transparent;
    -webkit-overflow-scrolling: touch;
  }

  .tabs-nav::-webkit-scrollbar {
    height: 4px;
  }

  .tabs-nav::-webkit-scrollbar-track {
    background: transparent;
  }

  .tabs-nav::-webkit-scrollbar-thumb {
    background: var(--border-primary);
    border-radius: 2px;
  }

  .tab-button {
    display: flex;
    align-items: center;
    gap: var(--spacing-xs);
    padding: var(--spacing-sm) var(--spacing-md);
    background: transparent;
    border: none;
    border-radius: var(--radius-md);
    color: var(--text-secondary);
    font-size: clamp(var(--text-xs), 2.5vw, var(--text-sm));
    font-weight: 500;
    cursor: pointer;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    white-space: nowrap;
    flex-shrink: 0;
    min-width: fit-content;
  }

  .tab-label {
    display: inline;
  }

  .tab-button:hover {
    background: var(--theme-bg-secondary);
    color: var(--text-primary);
  }

  .tab-button.active {
    background: var(--accent-primary);
    color: white;
    box-shadow: 0 4px 12px rgba(0, 147, 247, 0.3);
  }

  .tab-button:focus-visible {
    outline: 2px solid var(--accent-primary);
    outline-offset: 2px;
  }
</style>



