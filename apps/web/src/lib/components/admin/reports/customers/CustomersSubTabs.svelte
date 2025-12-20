<script lang="ts">
  /**
   * CustomersSubTabs - Submenu tabs for Customers section.
   * 
   * Provides navigation between different customer analysis views:
   * - Summary (Resumen)
   * - List (Lista Completa)
   * - RFM (Segmentación RFM)
   * - Cohorts (Análisis de Cohortes)
   * - Trends (Tendencias)
   */
  import { isMobileOrTablet } from '$lib/utils/useBreakpoint';
  import { 
    BarChart3, 
    List, 
    Users, 
    TrendingUp, 
    Activity 
  } from 'lucide-svelte';
  import type { ComponentType } from 'svelte';
  import type { SvelteComponent } from 'svelte';

  export interface SubTab {
    id: string;
    label: string;
    icon: ComponentType<SvelteComponent>;
  }

  export let activeSubTab: string = 'summary';
  export let onSubTabChange: (tabId: string) => void = () => {};

  const subTabs: SubTab[] = [
    { id: 'summary', label: 'Resumen', icon: BarChart3 },
    { id: 'list', label: 'Lista Completa', icon: List },
    { id: 'rfm', label: 'Segmentación RFM', icon: Users },
    { id: 'cohorts', label: 'Cohortes', icon: TrendingUp },
    { id: 'trends', label: 'Tendencias', icon: Activity },
  ];

  $: useMobile = $isMobileOrTablet;

  function handleSelectChange(event: Event) {
    const target = event.target as HTMLSelectElement;
    if (target) {
      onSubTabChange(target.value);
    }
  }
</script>

<div class="customers-sub-tabs-container">
  {#if useMobile}
    <!-- Mobile: Dropdown -->
    <div class="sub-tabs-mobile">
      <select 
        class="sub-tabs-select"
        value={activeSubTab}
        on:change={handleSelectChange}
        aria-label="Seleccionar vista de clientes"
      >
        {#each subTabs as tab}
          <option value={tab.id}>{tab.label}</option>
        {/each}
      </select>
    </div>
  {:else}
    <!-- Desktop: Horizontal tabs -->
    <div class="sub-tabs-desktop">
      {#each subTabs as tab}
        <button
          class="sub-tab-button"
          class:active={activeSubTab === tab.id}
          on:click={() => onSubTabChange(tab.id)}
          aria-label={tab.label}
          aria-pressed={activeSubTab === tab.id}
        >
          <svelte:component this={tab.icon} size={18} strokeWidth={1.5} />
          <span class="sub-tab-label">{tab.label}</span>
        </button>
      {/each}
    </div>
  {/if}
</div>

<style>
  .customers-sub-tabs-container {
    width: 100%;
    margin-bottom: var(--spacing-md);
    border-bottom: 1px solid var(--border-primary);
  }

  /* Desktop: Horizontal tabs */
  .sub-tabs-desktop {
    display: flex;
    gap: var(--spacing-xs);
    overflow-x: auto;
    scrollbar-width: thin;
  }

  .sub-tab-button {
    display: flex;
    align-items: center;
    gap: var(--spacing-xs);
    padding: var(--spacing-sm) var(--spacing-md);
    background: transparent;
    border: none;
    border-bottom: 2px solid transparent;
    color: var(--text-secondary);
    font-size: var(--text-sm);
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
    white-space: nowrap;
  }

  .sub-tab-button:hover {
    color: var(--text-primary);
    background: var(--theme-bg-elevated);
  }

  .sub-tab-button.active {
    color: var(--accent-primary);
    border-bottom-color: var(--accent-primary);
    background: var(--theme-bg-elevated);
  }

  .sub-tab-label {
    font-size: inherit;
  }

  /* Mobile: Dropdown */
  .sub-tabs-mobile {
    width: 100%;
  }

  .sub-tabs-select {
    width: 100%;
    padding: var(--spacing-sm);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
    background: var(--theme-bg-elevated);
    color: var(--text-primary);
    font-size: var(--text-base);
    cursor: pointer;
    appearance: none;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%236b7280' d='M6 9L1 4h10z'/%3E%3C/svg%3E");
    background-repeat: no-repeat;
    background-position: right var(--spacing-sm) center;
    padding-right: calc(var(--spacing-md) + 1rem);
    transition: all 0.2s ease;
  }

  .sub-tabs-select:hover {
    border-color: var(--accent-primary);
  }

  .sub-tabs-select:focus {
    outline: none;
    border-color: var(--accent-primary);
    box-shadow: 0 0 0 3px rgba(0, 147, 247, 0.1);
  }

  /* Responsive adjustments */
  @media (max-width: 640px) {
    .sub-tab-button {
      padding: var(--spacing-xs) var(--spacing-sm);
      font-size: var(--text-xs);
    }

    .sub-tab-label {
      display: none;
    }
  }
</style>

