<script lang="ts">
  /**
   * ItemsArrangement component - Item selection with grouping options.
   * 
   * Combines ItemSelector with grouping mode selection.
   */
  import { onMount } from "svelte";
  import { createEventDispatcher } from "svelte";
  import { user } from "$lib/stores/auth";
  import { fetchAllPackages, packagesAdminStore } from "$lib/stores/packages-admin";
  import ItemSelector from "./ItemSelector.svelte";
  import { 
    groupItems, 
    getGroupingModeLabel, 
    type GroupingMode 
  } from "$lib/utils/package-grouping";
  import { Layers } from "lucide-svelte";

  const dispatch = createEventDispatcher();

  export let sucursalId: string | null = null;
  export let selectedServices: string[] = [];
  export let selectedProducts: string[] = [];
  export let selectedPackages: string[] = [];

  let groupingMode: GroupingMode = "all";
  let allPackages: any[] = [];

  onMount(async () => {
    const currentUser = $user;
    const targetSucursalId = sucursalId || currentUser?.sucursal_id;
    
    if (targetSucursalId) {
      await fetchAllPackages(targetSucursalId);
      allPackages = $packagesAdminStore.list.filter((p) => p.active !== false);
    }
  });

  function handleItemChange(event: CustomEvent<{ services: string[]; products: string[]; packages: string[] }>) {
    selectedServices = event.detail.services;
    selectedProducts = event.detail.products;
    selectedPackages = event.detail.packages;
    
    // Re-apply grouping when items change
    applyGrouping();
  }

  function handleGroupingChange(mode: GroupingMode) {
    groupingMode = mode;
    applyGrouping();
  }

  function applyGrouping() {
    // Get actual service/product items from stores (simplified - in real implementation,
    // we'd need to fetch these based on selected IDs)
    // For now, dispatch with current selection and grouping mode
    dispatch("change", {
      services: selectedServices,
      products: selectedProducts,
      packages: selectedPackages,
      groupingMode,
    });
  }

  const groupingOptions: Array<{ value: GroupingMode; label: string }> = [
    { value: "all", label: getGroupingModeLabel("all") },
    { value: "services-with-packages", label: getGroupingModeLabel("services-with-packages") },
    { value: "products-with-packages", label: getGroupingModeLabel("products-with-packages") },
  ];
</script>

<div class="items-arrangement">
  <div class="grouping-section">
    <div class="section-header">
      <Layers size={20} strokeWidth={1.5} />
      <h3 class="section-title">Modo de Agrupación</h3>
    </div>
    <div class="grouping-options">
      {#each groupingOptions as option}
        <label class="radio-option">
          <input
            type="radio"
            name="grouping-mode"
            value={option.value}
            checked={groupingMode === option.value}
            on:change={() => handleGroupingChange(option.value)}
          />
          <span class="radio-label">{option.label}</span>
        </label>
      {/each}
    </div>
  </div>

  <div class="selector-section">
    <ItemSelector
      bind:selectedServices
      bind:selectedProducts
      bind:selectedPackages
      {sucursalId}
      on:change={handleItemChange}
    />
  </div>
</div>

<style>
  .items-arrangement {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-lg);
  }

  .grouping-section {
    padding: var(--spacing-md);
    background: var(--theme-bg-secondary);
    border-radius: var(--radius-md);
    border: 1px solid var(--border-primary);
  }

  .section-header {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    margin-bottom: var(--spacing-md);
  }

  .section-title {
    font-size: var(--text-lg);
    font-weight: 700;
    color: var(--text-primary);
    margin: 0;
  }

  .grouping-options {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-sm);
  }

  .radio-option {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    padding: var(--spacing-sm) var(--spacing-md);
    border: 2px solid var(--border-primary);
    border-radius: var(--radius-sm);
    cursor: pointer;
    transition: all 0.2s;
    background: var(--theme-bg-primary);
    min-height: 44px;
  }

  .radio-option:hover {
    border-color: var(--accent-primary);
    background: var(--theme-bg-elevated);
  }

  .radio-option input[type="radio"] {
    cursor: pointer;
    width: 20px;
    height: 20px;
    accent-color: var(--accent-primary);
    flex-shrink: 0;
  }

  .radio-option input[type="radio"]:checked + .radio-label {
    font-weight: 600;
    color: var(--accent-primary);
  }

  .radio-label {
    flex: 1;
    font-size: var(--text-base);
    color: var(--text-primary);
  }

  .selector-section {
    flex: 1;
  }

  /* Responsive */
  @media (max-width: 768px) {
    .grouping-options {
      gap: var(--spacing-xs);
    }

    .radio-option {
      min-height: 52px;
    }
  }

  /* Prevent hover effects on touch devices */
  @media (hover: none) and (pointer: coarse) {
    .radio-option:hover {
      background: var(--theme-bg-primary);
      border-color: var(--border-primary);
    }
  }
</style>
