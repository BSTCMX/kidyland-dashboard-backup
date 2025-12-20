<script context="module" lang="ts">
  /**
   * MultiSelectDropdown - Reusable dropdown component with checkboxes.
   * 
   * Styled to match the project's design system.
   */
  export interface Option {
    value: string | number;
    label: string;
    disabled?: boolean; // Individual option disabled state
    metadata?: Record<string, any>; // Additional metadata (e.g., stock info)
  }
</script>

<script lang="ts">
  import { createEventDispatcher } from "svelte";
  import { ChevronDown } from "lucide-svelte";

  export let options: Option[] = [];
  export let selectedValues: (string | number)[] = [];
  export let placeholder: string = "Seleccionar...";
  export let label: string = "";
  export let disabled: boolean = false;
  export let error: boolean = false;
  export let required: boolean = false;
  export let ariaDescribedBy: string | undefined = undefined;
  export let showMetadata: boolean = false; // Show metadata in label (e.g., stock info)
  // Callback function for individual item selection
  export let onItemSelect: ((value: string | number, checked: boolean) => void) | undefined = undefined;

  const dispatch = createEventDispatcher<{
    change: (string | number)[];
    itemSelect: { value: string | number; checked: boolean };
  }>();

  let isOpen = false;
  let dropdownRef: HTMLDivElement;
  let internalSelectedValues: (string | number)[] = [];
  let listId = `multi-select-list-${Math.random().toString(36).substr(2, 9)}`;

  // Sync internal state with prop when it changes
  $: {
    if (selectedValues) {
      if (options.length > 0) {
        // Filter to only include valid options
        internalSelectedValues = selectedValues.filter((val) =>
          options.some((opt) => opt.value === val)
        );
      } else {
        internalSelectedValues = [...selectedValues];
      }
    } else {
      internalSelectedValues = [];
    }
  }

  function toggleDropdown() {
    if (disabled) return;
    isOpen = !isOpen;
  }

  function handleCheckboxChange(value: string | number, checked: boolean) {
    // Check if option is disabled
    const option = options.find((opt) => opt.value === value);
    if (option?.disabled) {
      return; // Don't allow selection of disabled options
    }

    if (checked) {
      internalSelectedValues = [...internalSelectedValues, value];
    } else {
      internalSelectedValues = internalSelectedValues.filter((v) => v !== value);
    }
    
    // Dispatch both events for backward compatibility and new functionality
    dispatch("change", internalSelectedValues);
    dispatch("itemSelect", { value, checked });
    
    // Call custom callback if provided (using optional chaining for safety)
    onItemSelect?.(value, checked);
  }

  function getDisplayText(): string {
    if (internalSelectedValues.length === 0) {
      return placeholder;
    }
    if (internalSelectedValues.length === 1) {
      const option = options.find((opt) => opt.value === internalSelectedValues[0]);
      return option?.label || placeholder;
    }
    return `${internalSelectedValues.length} seleccionados`;
  }

  // Close dropdown when clicking outside
  function handleClickOutside(event: MouseEvent) {
    if (dropdownRef && !dropdownRef.contains(event.target as Node)) {
      isOpen = false;
    }
  }

</script>

<svelte:window on:click={handleClickOutside} />

<div class="multi-select-wrapper" bind:this={dropdownRef}>
  {#if label}
    <label class="multi-select-label">
      {label}
      {#if required}
        <span class="required">*</span>
      {/if}
    </label>
  {/if}

  <div
    class="multi-select-dropdown"
    class:open={isOpen}
    class:error={error}
    class:disabled={disabled}
    role="combobox"
    aria-expanded={isOpen}
    aria-describedby={ariaDescribedBy}
    aria-haspopup="listbox"
    aria-controls={listId}
  >
    <button
      type="button"
      class="multi-select-trigger"
      on:click={toggleDropdown}
      disabled={disabled}
      aria-label={getDisplayText()}
    >
      <span class="multi-select-display" class:placeholder={internalSelectedValues.length === 0}>
        {getDisplayText()}
      </span>
      <span class="chevron" class:rotated={isOpen}>
        <ChevronDown size={16} />
      </span>
    </button>

    {#if isOpen}
      <div class="multi-select-dropdown-content">
        <ul id={listId} class="multi-select-list" role="listbox">
          {#each options as option (option.value)}
            {@const isDisabled = disabled || option.disabled}
            {@const isSelected = internalSelectedValues.includes(option.value)}
            <li 
              class="multi-select-item" 
              class:disabled={isDisabled}
              role="option" 
              aria-selected={isSelected}
              aria-disabled={isDisabled}
            >
              <label class="multi-select-checkbox-label" class:disabled={isDisabled}>
                <input
                  type="checkbox"
                  class="multi-select-checkbox"
                  checked={isSelected}
                  on:change={(e) =>
                    handleCheckboxChange(option.value, e.currentTarget.checked)}
                  disabled={isDisabled}
                />
                <span class="multi-select-checkbox-text">
                  {option.label}
                  {#if showMetadata && option.metadata}
                    <span class="metadata-info">
                      {#if option.metadata.stock_qty !== undefined}
                        {option.metadata.stock_qty === 0 
                          ? " (Sin stock)" 
                          : ` (Stock: ${option.metadata.stock_qty})`}
                      {/if}
                    </span>
                  {/if}
                </span>
              </label>
            </li>
          {/each}
        </ul>
      </div>
    {/if}
  </div>
</div>

<style>
  .multi-select-wrapper {
    position: relative;
    width: 100%;
  }

  .multi-select-label {
    display: block;
    font-size: 0.875rem;
    font-weight: 500;
    color: var(--text-primary, #e2e8f0);
    margin-bottom: 0.5rem;
  }

  .required {
    color: var(--error, #ef4444);
    margin-left: 0.25rem;
  }

  .multi-select-dropdown {
    position: relative;
    width: 100%;
  }

  .multi-select-trigger {
    width: 100%;
    padding: 0.875rem 1rem;
    font-size: 1rem;
    background: var(--theme-bg-secondary, rgba(15, 23, 42, 0.6));
    border: 2px solid var(--border-primary, rgba(148, 163, 184, 0.2));
    border-radius: 10px;
    color: var(--text-primary, #e2e8f0);
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.5rem;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    text-align: left;
  }

  .multi-select-trigger:hover:not(:disabled) {
    border-color: rgba(0, 147, 247, 0.5);
    background: var(--theme-bg-secondary, rgba(15, 23, 42, 0.8));
  }

  .multi-select-trigger:focus {
    outline: none;
    border-color: #0093f7;
    box-shadow:
      0 0 0 3px rgba(0, 147, 247, 0.1),
      0 0 20px var(--glow-primary, rgba(0, 147, 247, 0.3));
  }

  .multi-select-trigger:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .multi-select-dropdown.error .multi-select-trigger {
    border-color: var(--error, #ef4444);
  }

  .multi-select-dropdown.open .multi-select-trigger {
    border-color: #0093f7;
    box-shadow:
      0 0 0 3px rgba(0, 147, 247, 0.1),
      0 0 20px var(--glow-primary, rgba(0, 147, 247, 0.3));
  }

  .multi-select-display {
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .multi-select-display.placeholder {
    color: var(--text-secondary, rgba(148, 163, 184, 0.6));
  }

  .chevron {
    display: inline-flex;
    align-items: center;
    flex-shrink: 0;
    transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    color: var(--text-secondary, rgba(148, 163, 184, 0.6));
  }

  .chevron.rotated {
    transform: rotate(180deg);
  }

  .multi-select-dropdown-content {
    position: absolute;
    top: calc(100% + 0.5rem);
    left: 0;
    right: 0;
    z-index: 3000; /* Higher than modal (2000) and overlay (1000) */
    background: var(--theme-bg-card, rgba(15, 23, 42, 0.95));
    backdrop-filter: blur(16px) saturate(150%);
    -webkit-backdrop-filter: blur(16px) saturate(150%);
    border: 2px solid var(--border-primary, rgba(148, 163, 184, 0.2));
    border-radius: 10px;
    box-shadow:
      0 8px 24px rgba(0, 0, 0, 0.3),
      0 0 20px var(--glow-primary, rgba(0, 147, 247, 0.2));
    max-height: 300px;
    overflow-y: auto;
    animation: fadeIn 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  }

  @keyframes fadeIn {
    from {
      opacity: 0;
      transform: translateY(-10px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  .multi-select-list {
    list-style: none;
    margin: 0;
    padding: 0.5rem;
  }

  .multi-select-item {
    margin: 0;
    padding: 0;
  }

  .multi-select-checkbox-label {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.75rem 1rem;
    cursor: pointer;
    border-radius: 6px;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    user-select: none;
  }

  .multi-select-checkbox-label:hover {
    background: var(--theme-bg-secondary, rgba(15, 23, 42, 0.6));
  }

  .multi-select-checkbox {
    width: 18px;
    height: 18px;
    cursor: pointer;
    accent-color: #0093f7;
    flex-shrink: 0;
  }

  .multi-select-checkbox:disabled {
    cursor: not-allowed;
    opacity: 0.6;
  }

  .multi-select-checkbox-text {
    flex: 1;
    color: var(--text-primary, #e2e8f0);
    font-size: 0.9375rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .metadata-info {
    color: var(--text-secondary, rgba(148, 163, 184, 0.7));
    font-size: 0.875rem;
    font-weight: normal;
  }

  .multi-select-item.disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .multi-select-checkbox-label.disabled {
    cursor: not-allowed;
  }

  .multi-select-checkbox-label.disabled:hover {
    background: transparent;
  }

  /* Scrollbar styling */
  .multi-select-dropdown-content::-webkit-scrollbar {
    width: 8px;
  }

  .multi-select-dropdown-content::-webkit-scrollbar-track {
    background: var(--theme-bg-secondary, rgba(15, 23, 42, 0.3));
    border-radius: 4px;
  }

  .multi-select-dropdown-content::-webkit-scrollbar-thumb {
    background: var(--border-primary, rgba(148, 163, 184, 0.4));
    border-radius: 4px;
  }

  .multi-select-dropdown-content::-webkit-scrollbar-thumb:hover {
    background: rgba(148, 163, 184, 0.6);
  }

  /* Responsive */
  @media (max-width: 640px) {
    .multi-select-trigger {
      padding: 0.75rem 0.875rem;
      font-size: 0.9375rem;
    }

    .multi-select-checkbox-label {
      padding: 0.625rem 0.875rem;
    }
  }
</style>

