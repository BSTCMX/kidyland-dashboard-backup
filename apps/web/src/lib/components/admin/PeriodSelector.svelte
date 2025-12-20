<script lang="ts">
  /**
   * Period Selector Component
   * 
   * Reusable component for selecting time period (7, 15, 30, etc. days).
   * Follows Clean Architecture and Design System patterns.
   * 
   * Features:
   * - Responsive design (mobile, tablet, desktop)
   * - Accessible dropdown/button group
   * - Consistent styling with architecture
   * - Lucide icons support
   */
  import { onMount } from "svelte";
  import { Calendar, ChevronDown } from "lucide-svelte";
  import { periodStore, setPeriod, type PeriodOption, PERIOD_OPTIONS } from "$lib/stores/period";
  
  export let selectedDays: number = 30;
  export let options: readonly number[] = PERIOD_OPTIONS;
  export let variant: "dropdown" | "button-group" = "dropdown";
  export let size: "small" | "medium" | "large" = "medium";
  export let showLabel: boolean = true;
  export let label: string = "Período:";
  
  let isOpen = false;
  let dropdownRef: HTMLDivElement;
  
  // Sync with store
  $: {
    if ($periodStore.selectedDays !== selectedDays) {
      selectedDays = $periodStore.selectedDays;
    }
  }
  
  function handleSelect(days: number): void {
    selectedDays = days;
    setPeriod(days);
    isOpen = false;
    dispatch("change", { days });
  }
  
  function handleClickOutside(event: MouseEvent): void {
    if (dropdownRef && !dropdownRef.contains(event.target as Node)) {
      isOpen = false;
    }
  }
  
  onMount(() => {
    // Initialize with current store value
    selectedDays = $periodStore.selectedDays;
    
    // Handle click outside
    if (variant === "dropdown") {
      document.addEventListener("click", handleClickOutside);
      return () => {
        document.removeEventListener("click", handleClickOutside);
      };
    }
  });
  
  // Dispatch custom event
  import { createEventDispatcher } from "svelte";
  const dispatch = createEventDispatcher<{ change: { days: number } }>();
</script>

{#if variant === "dropdown"}
  <div class="period-selector dropdown" class:size-small={size === "small"} class:size-medium={size === "medium"} class:size-large={size === "large"} bind:this={dropdownRef}>
    {#if showLabel}
      <div class="period-label">
        <Calendar size={16} strokeWidth={1.5} />
        <span>{label}</span>
      </div>
    {/if}
    <div class="dropdown-container">
      <button
        class="dropdown-trigger"
        class:open={isOpen}
        on:click|stopPropagation={() => isOpen = !isOpen}
        aria-expanded={isOpen}
        aria-haspopup="listbox"
      >
        <span class="selected-value">{selectedDays} días</span>
        <span class="chevron-icon" class:rotated={isOpen}>
          <ChevronDown size={16} strokeWidth={2} />
        </span>
      </button>
      
      {#if isOpen}
        <div class="dropdown-menu" role="listbox">
          {#each options as option}
            <button
              class="dropdown-option"
              class:selected={selectedDays === option}
              on:click|stopPropagation={() => handleSelect(option)}
              role="option"
              aria-selected={selectedDays === option}
            >
              {option} días
            </button>
          {/each}
        </div>
      {/if}
    </div>
  </div>
  {:else}
  <div class="period-selector button-group" class:size-small={size === "small"} class:size-medium={size === "medium"} class:size-large={size === "large"}>
    {#if showLabel}
      <div class="period-label">
        <Calendar size={16} strokeWidth={1.5} />
        <span>{label}</span>
      </div>
    {/if}
    <div class="button-group-container">
      {#each options as option}
        <button
          class="period-button"
          class:active={selectedDays === option}
          on:click={() => handleSelect(option)}
          aria-pressed={selectedDays === option}
        >
          {option}d
        </button>
      {/each}
    </div>
  </div>
{/if}

<style>
  .period-selector {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xs, 0.5rem);
  }
  
  .period-label {
    display: flex;
    align-items: center;
    gap: var(--spacing-xs, 0.5rem);
    font-size: var(--text-sm, 0.875rem);
    font-weight: 600;
    color: var(--text-secondary, #6b7280);
    margin: 0;
  }
  
  /* Dropdown Variant */
  .dropdown-container {
    position: relative;
    display: inline-block;
  }
  
  .dropdown-trigger {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: var(--spacing-sm, 0.75rem);
    padding: var(--spacing-sm, 0.75rem) var(--spacing-md, 1rem);
    background: var(--theme-bg-elevated, #1f2937);
    border: 1px solid var(--border-primary, #374151);
    border-radius: var(--radius-md, 0.5rem);
    color: var(--text-primary, #f9fafb);
    font-size: var(--text-sm, 0.875rem);
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
    min-width: 120px;
  }
  
  .dropdown-trigger:hover {
    border-color: var(--accent-primary, #0093f7);
    background: var(--theme-bg-card, #111827);
  }
  
  .dropdown-trigger.open {
    border-color: var(--accent-primary, #0093f7);
    box-shadow: 0 0 0 3px rgba(0, 147, 247, 0.1);
  }
  
  .selected-value {
    flex: 1;
    text-align: left;
  }
  
  .chevron-icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    transition: transform 0.2s ease;
  }
  
  .chevron-icon.rotated {
    transform: rotate(180deg);
  }
  
  .chevron-icon :global(svg) {
    display: block;
  }
  
  .dropdown-menu {
    position: absolute;
    top: calc(100% + 4px);
    left: 0;
    right: 0;
    background: var(--theme-bg-elevated, #1f2937);
    border: 1px solid var(--border-primary, #374151);
    border-radius: var(--radius-md, 0.5rem);
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    z-index: 1000;
    overflow: hidden;
    margin-top: var(--spacing-xs, 0.5rem);
  }
  
  .dropdown-option {
    display: block;
    width: 100%;
    padding: var(--spacing-sm, 0.75rem) var(--spacing-md, 1rem);
    background: transparent;
    border: none;
    color: var(--text-primary, #f9fafb);
    font-size: var(--text-sm, 0.875rem);
    text-align: left;
    cursor: pointer;
    transition: background-color 0.15s ease;
  }
  
  .dropdown-option:hover {
    background: var(--theme-bg-card, #111827);
  }
  
  .dropdown-option.selected {
    background: var(--accent-primary, #0093f7);
    color: white;
    font-weight: 600;
  }
  
  /* Button Group Variant */
  .button-group-container {
    display: flex;
    gap: var(--spacing-xs, 0.5rem);
    flex-wrap: wrap;
  }
  
  .period-button {
    padding: var(--spacing-xs, 0.5rem) var(--spacing-sm, 0.75rem);
    background: var(--theme-bg-elevated, #1f2937);
    border: 1px solid var(--border-primary, #374151);
    border-radius: var(--radius-md, 0.5rem);
    color: var(--text-primary, #f9fafb);
    font-size: var(--text-sm, 0.875rem);
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
    min-width: 50px;
  }
  
  .period-button:hover {
    border-color: var(--accent-primary, #0093f7);
    background: var(--theme-bg-card, #111827);
  }
  
  .period-button.active {
    background: var(--accent-primary, #0093f7);
    border-color: var(--accent-primary, #0093f7);
    color: white;
    font-weight: 600;
  }
  
  /* Size Variants */
  .size-small .dropdown-trigger,
  .size-small .period-button {
    padding: var(--spacing-xs, 0.5rem) var(--spacing-sm, 0.75rem);
    font-size: var(--text-xs, 0.75rem);
    min-width: 100px;
  }
  
  .size-large .dropdown-trigger,
  .size-large .period-button {
    padding: var(--spacing-md, 1rem) var(--spacing-lg, 1.25rem);
    font-size: var(--text-base, 1rem);
    min-width: 140px;
  }
  
  /* Responsive Design */
  @media (max-width: 640px) {
    .period-selector {
      width: 100%;
    }
    
    .dropdown-container {
      width: 100%;
    }
    
    .dropdown-trigger {
      width: 100%;
    }
    
    .button-group-container {
      width: 100%;
    }
    
    .period-button {
      flex: 1;
      min-width: 0;
    }
  }
  
  @media (min-width: 641px) and (max-width: 1024px) {
    .button-group-container {
      gap: var(--spacing-sm, 0.75rem);
    }
  }
</style>

