<script lang="ts">
  /**
   * TabsMobile - Mobile dropdown tabs navigation component.
   * 
   * Renders a dropdown menu for mobile viewports.
   * Similar to PeriodSelector pattern but for tabs navigation.
   */
  import { onMount } from 'svelte';
  import { ChevronDown } from 'lucide-svelte';
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

  let isOpen = false;
  let dropdownRef: HTMLDivElement;

  // Get active tab info
  $: activeTabInfo = tabs.find((tab) => tab.id === activeTab) || tabs[0];

  function toggleDropdown() {
    isOpen = !isOpen;
  }

  function handleTabSelect(tabId: string) {
    onTabChange(tabId);
    isOpen = false; // Close dropdown after selection
  }

  // Close dropdown when clicking outside
  function handleClickOutside(event: MouseEvent) {
    if (dropdownRef && !dropdownRef.contains(event.target as Node)) {
      isOpen = false;
    }
  }

  // Handle keyboard navigation
  function handleKeydown(event: KeyboardEvent) {
    if (event.key === 'Escape') {
      isOpen = false;
    }
  }

  onMount(() => {
    document.addEventListener('click', handleClickOutside);
    document.addEventListener('keydown', handleKeydown);
    
    return () => {
      document.removeEventListener('click', handleClickOutside);
      document.removeEventListener('keydown', handleKeydown);
    };
  });
</script>

<div class="tabs-mobile-wrapper" bind:this={dropdownRef}>
  <button
    class="tabs-mobile-trigger"
    class:open={isOpen}
    on:click={toggleDropdown}
    aria-expanded={isOpen}
    aria-haspopup="listbox"
    aria-label="Seleccionar sección de reporte"
  >
      <div class="trigger-content">
        {#if activeTabInfo}
          <svelte:component this={activeTabInfo.icon} size={18} strokeWidth={1.5} />
          <span class="trigger-label">{activeTabInfo.label}</span>
        {/if}
      </div>
      <span class="chevron" class:rotated={isOpen}>
        <ChevronDown size={18} strokeWidth={1.5} />
      </span>
  </button>

  {#if isOpen}
    <div class="tabs-mobile-dropdown" role="listbox">
      {#each tabs as tab}
        <button
          class="tabs-mobile-option"
          class:active={activeTab === tab.id}
          on:click={() => handleTabSelect(tab.id)}
          role="option"
          aria-selected={activeTab === tab.id}
        >
          <svelte:component this={tab.icon} size={18} strokeWidth={1.5} />
          <span class="option-label">{tab.label}</span>
          {#if activeTab === tab.id}
            <span class="check-indicator" aria-hidden="true">✓</span>
          {/if}
        </button>
      {/each}
    </div>
  {/if}
</div>

<style>
  .tabs-mobile-wrapper {
    position: relative;
    width: 100%;
  }

  .tabs-mobile-trigger {
    display: flex;
    align-items: center;
    justify-content: space-between;
    width: 100%;
    padding: var(--spacing-md);
    background: var(--theme-bg-elevated);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
    color: var(--text-primary);
    font-size: var(--text-base);
    font-weight: 500;
    cursor: pointer;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    min-height: 48px; /* Touch target size */
  }

  .tabs-mobile-trigger:hover {
    background: var(--theme-bg-secondary);
    border-color: var(--accent-primary);
  }

  .tabs-mobile-trigger.open {
    border-color: var(--accent-primary);
    box-shadow: 0 0 0 3px rgba(0, 147, 247, 0.1);
  }

  .tabs-mobile-trigger:focus-visible {
    outline: 2px solid var(--accent-primary);
    outline-offset: 2px;
  }

  .trigger-content {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    flex: 1;
  }

  .trigger-label {
    font-weight: 500;
  }

  .chevron {
    transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    flex-shrink: 0;
  }

  .chevron.rotated {
    transform: rotate(180deg);
  }

  .tabs-mobile-dropdown {
    position: absolute;
    top: calc(100% + var(--spacing-xs));
    left: 0;
    right: 0;
    background: var(--theme-bg-card);
    backdrop-filter: blur(16px) saturate(150%);
    -webkit-backdrop-filter: blur(16px) saturate(150%);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
    box-shadow: 
      0 8px 24px rgba(0, 0, 0, 0.15),
      0 0 20px var(--glow-primary);
    z-index: 1000;
    max-height: 400px;
    overflow-y: auto;
    margin-top: var(--spacing-xs);
  }

  .tabs-mobile-dropdown::-webkit-scrollbar {
    width: 6px;
  }

  .tabs-mobile-dropdown::-webkit-scrollbar-track {
    background: transparent;
  }

  .tabs-mobile-dropdown::-webkit-scrollbar-thumb {
    background: var(--border-primary);
    border-radius: 3px;
  }

  .tabs-mobile-option {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    width: 100%;
    padding: var(--spacing-md);
    background: transparent;
    border: none;
    border-bottom: 1px solid var(--border-primary);
    color: var(--text-primary);
    font-size: var(--text-base);
    font-weight: 500;
    text-align: left;
    cursor: pointer;
    transition: all 0.2s ease;
    min-height: 48px; /* Touch target size */
  }

  .tabs-mobile-option:last-child {
    border-bottom: none;
  }

  .tabs-mobile-option:hover {
    background: var(--theme-bg-secondary);
  }

  .tabs-mobile-option.active {
    background: rgba(0, 147, 247, 0.1);
    color: var(--accent-primary);
    font-weight: 600;
  }

  .tabs-mobile-option:focus-visible {
    outline: 2px solid var(--accent-primary);
    outline-offset: -2px;
  }

  .option-label {
    flex: 1;
  }

  .check-indicator {
    color: var(--accent-primary);
    font-weight: 700;
    font-size: var(--text-lg);
  }
</style>

