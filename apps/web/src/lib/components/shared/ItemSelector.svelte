<script lang="ts">
  /**
   * ItemSelector component - Multi-select for services, products, and packages.
   * 
   * Allows users to select which items to include in the video export.
   */
  import { onMount } from "svelte";
  import { tick } from "svelte";
  import { createEventDispatcher } from "svelte";
  import { user } from "$lib/stores/auth";
  import { fetchServices, activeServices } from "$lib/stores/services";
  import { fetchProducts, availableProducts } from "$lib/stores/products";
  import { fetchAllPackages, packagesAdminStore } from "$lib/stores/packages-admin";
  import { Button } from "@kidyland/ui";
  import { 
    Gamepad2, 
    ShoppingBag, 
    Package as PackageIcon, 
    CheckSquare, 
    Square 
  } from "lucide-svelte";
  import type { Service } from "@kidyland/shared/types";
  import type { Product } from "@kidyland/shared/types";
  import type { Package } from "@kidyland/shared/types";

  export let selectedServices: string[] = [];
  export let selectedProducts: string[] = [];
  export let selectedPackages: string[] = [];
  /** Optional sucursal ID. If not provided, uses current user's sucursal_id */
  export let sucursalId: string | null = null;
  /** Show grouping mode selector */
  export let showGroupingMode: boolean = false;

  const dispatch = createEventDispatcher<{
    change: { services: string[]; products: string[]; packages: string[] };
    groupingChange?: { mode: "all" | "services-with-packages" | "products-with-packages" };
  }>();

  let services: Service[] = [];
  let products: Product[] = [];
  let packages: Package[] = [];
  let loading = false;
  let error: string | null = null;

  // Reload items when sucursalId changes
  $: if (sucursalId || $user?.sucursal_id) {
    loadItems();
  }

  onMount(async () => {
    await loadItems();
    
    // Initialize selection if empty - select all by default
    // Wait for reactivity to ensure items are loaded
    await tick();
    
    let hasChanges = false;
    
    if (services.length > 0 && selectedServices.length === 0) {
      selectedServices = [...services.map((s) => s.id)];
      hasChanges = true;
    }
    if (products.length > 0 && selectedProducts.length === 0) {
      selectedProducts = [...products.map((p) => p.id)];
      hasChanges = true;
    }
    if (packages.length > 0 && selectedPackages.length === 0) {
      selectedPackages = [...packages.map((p) => p.id)];
      hasChanges = true;
    }
    
    // Wait again after state updates
    await tick();
    
    // Dispatch initial state if there were changes
    if (hasChanges) {
      dispatch("change", { 
        services: selectedServices, 
        products: selectedProducts, 
        packages: selectedPackages 
      });
    }
  });

  async function loadItems() {
    // Use provided sucursalId or fall back to current user's sucursal_id
    const targetSucursalId = sucursalId || $user?.sucursal_id;
    
    if (!targetSucursalId) {
      error = "No hay sucursal seleccionada";
      loading = false;
      return;
    }

    loading = true;
    error = null;

    try {
      await Promise.all([
        fetchServices(targetSucursalId),
        fetchProducts(targetSucursalId),
        fetchAllPackages(targetSucursalId),
      ]);

      services = $activeServices;
      products = $availableProducts;
      packages = $packagesAdminStore.list.filter((pkg) => pkg.active !== false);
    } catch (e: any) {
      error = e.message || "Error loading items";
      console.error("Error loading items:", e);
    } finally {
      loading = false;
    }
  }

  function toggleService(id: string) {
    selectedServices = selectedServices.includes(id)
      ? selectedServices.filter((s) => s !== id)
      : [...selectedServices, id];
    dispatch("change", { 
      services: selectedServices, 
      products: selectedProducts, 
      packages: selectedPackages 
    });
  }

  function toggleProduct(id: string) {
    selectedProducts = selectedProducts.includes(id)
      ? selectedProducts.filter((p) => p !== id)
      : [...selectedProducts, id];
    dispatch("change", { 
      services: selectedServices, 
      products: selectedProducts, 
      packages: selectedPackages 
    });
  }

  function togglePackage(id: string) {
    selectedPackages = selectedPackages.includes(id)
      ? selectedPackages.filter((p) => p !== id)
      : [...selectedPackages, id];
    dispatch("change", { 
      services: selectedServices, 
      products: selectedProducts, 
      packages: selectedPackages 
    });
  }

  async function selectAll(type: "services" | "products" | "packages") {
    if (type === "services" && services.length > 0) {
      // Create new array to trigger reactivity
      selectedServices = [...services.map((s) => s.id)];
    } else if (type === "products" && products.length > 0) {
      selectedProducts = [...products.map((p) => p.id)];
    } else if (type === "packages" && packages.length > 0) {
      selectedPackages = [...packages.map((p) => p.id)];
    }
    
    // Wait for reactivity to propagate
    await tick();
    
    // Dispatch change event
    dispatch("change", { 
      services: selectedServices, 
      products: selectedProducts, 
      packages: selectedPackages 
    });
  }

  async function deselectAll(type: "services" | "products" | "packages") {
    if (type === "services") {
      selectedServices = [];
    } else if (type === "products") {
      selectedProducts = [];
    } else if (type === "packages") {
      selectedPackages = [];
    }
    
    // Wait for reactivity to propagate
    await tick();
    
    // Dispatch change event
    dispatch("change", { 
      services: selectedServices, 
      products: selectedProducts, 
      packages: selectedPackages 
    });
  }
</script>

{#if loading}
  <div class="loading">Cargando items...</div>
{:else if error}
  <div class="error">{error}</div>
{:else}
  <div class="item-selector">
    <!-- Services Section -->
    {#if services.length > 0}
      <div class="section">
        <div class="section-header">
          <h3 class="section-title">
            <Gamepad2 size={24} strokeWidth={1.5} style="display: inline-block; vertical-align: middle; margin-right: 8px;" />
            Servicios ({selectedServices.length}/{services.length})
          </h3>
          <div class="section-actions">
            <Button 
              variant="brutalist" 
              size="small"
              on:click={() => selectAll("services")}
            >
              <CheckSquare size={18} strokeWidth={1.5} style="display: inline-block; vertical-align: middle; margin-right: 6px;" />
              Seleccionar todos
            </Button>
            <Button 
              variant="brutalist" 
              size="small"
              on:click={() => deselectAll("services")}
            >
              <Square size={18} strokeWidth={1.5} style="display: inline-block; vertical-align: middle; margin-right: 6px;" />
              Deseleccionar todos
            </Button>
          </div>
        </div>
        <div class="items-grid">
          {#each services as service}
            <label class="item-checkbox">
              <input
                type="checkbox"
                checked={selectedServices.includes(service.id)}
                on:change={() => toggleService(service.id)}
              />
              <span class="item-name">{service.name}</span>
              <span class="item-price">
                ${service.duration_prices && Object.keys(service.duration_prices).length > 0
                  ? (Math.min(...Object.values(service.duration_prices)) / 100).toFixed(2)
                  : "0.00"}
              </span>
            </label>
          {/each}
        </div>
      </div>
    {/if}

    <!-- Products Section -->
    {#if products.length > 0}
      <div class="section">
        <div class="section-header">
          <h3 class="section-title">
            <ShoppingBag size={24} strokeWidth={1.5} style="display: inline-block; vertical-align: middle; margin-right: 8px;" />
            Productos ({selectedProducts.length}/{products.length})
          </h3>
          <div class="section-actions">
            <Button 
              variant="brutalist" 
              size="small"
              on:click={() => selectAll("products")}
            >
              <CheckSquare size={18} strokeWidth={1.5} style="display: inline-block; vertical-align: middle; margin-right: 6px;" />
              Seleccionar todos
            </Button>
            <Button 
              variant="brutalist" 
              size="small"
              on:click={() => deselectAll("products")}
            >
              <Square size={18} strokeWidth={1.5} style="display: inline-block; vertical-align: middle; margin-right: 6px;" />
              Deseleccionar todos
            </Button>
          </div>
        </div>
        <div class="items-grid">
          {#each products as product}
            <label class="item-checkbox">
              <input
                type="checkbox"
                checked={selectedProducts.includes(product.id)}
                on:change={() => toggleProduct(product.id)}
              />
              <span class="item-name">{product.name}</span>
              <span class="item-price">${(product.price_cents / 100).toFixed(2)}</span>
            </label>
          {/each}
        </div>
      </div>
    {/if}

    <!-- Packages Section -->
    {#if packages.length > 0}
      <div class="section">
        <div class="section-header">
          <h3 class="section-title">
            <PackageIcon size={24} strokeWidth={1.5} style="display: inline-block; vertical-align: middle; margin-right: 8px;" />
            Paquetes ({selectedPackages.length}/{packages.length})
          </h3>
          <div class="section-actions">
            <Button 
              variant="brutalist" 
              size="small"
              on:click={() => selectAll("packages")}
            >
              <CheckSquare size={18} strokeWidth={1.5} style="display: inline-block; vertical-align: middle; margin-right: 6px;" />
              Seleccionar todos
            </Button>
            <Button 
              variant="brutalist" 
              size="small"
              on:click={() => deselectAll("packages")}
            >
              <Square size={18} strokeWidth={1.5} style="display: inline-block; vertical-align: middle; margin-right: 6px;" />
              Deseleccionar todos
            </Button>
          </div>
        </div>
        <div class="items-grid">
          {#each packages as pkg}
            <label class="item-checkbox">
              <input
                type="checkbox"
                checked={selectedPackages.includes(pkg.id)}
                on:change={() => togglePackage(pkg.id)}
              />
              <span class="item-name">{pkg.name}</span>
              <span class="item-price">${(pkg.price_cents / 100).toFixed(2)}</span>
            </label>
          {/each}
        </div>
      </div>
    {/if}
  </div>
{/if}

<style>
  .item-selector {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-lg);
    padding: var(--spacing-md);
    background: var(--theme-bg-elevated);
    border-radius: var(--radius-lg);
    border: 1px solid var(--border-primary);
    max-height: 600px;
    overflow-y: auto;
  }

  .section {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-md);
  }

  .section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: var(--spacing-sm);
  }

  .section-title {
    font-size: var(--text-lg);
    font-weight: 700;
    color: var(--text-primary);
    margin: 0;
    display: flex;
    align-items: center;
    
    /* Brutalist 3D text shadow effect */
    text-shadow: 
      0 0.05em 0 rgba(0, 0, 0, 0.1),
      0 0.1em 0 rgba(0, 0, 0, 0.1),
      0 0.15em 0 rgba(0, 0, 0, 0.1),
      0 0.2em 0 rgba(0, 0, 0, 0.1),
      0 0.25em 0 rgba(0, 0, 0, 0.1),
      0 0.25em 0.02em rgba(0, 0, 0, 0.15),
      0 0.28em 0.2em rgba(0, 0, 0, 0.25);
  }

  .section-actions {
    display: flex;
    gap: var(--spacing-sm);
  }

  .items-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
    gap: var(--spacing-sm);
  }

  .item-checkbox {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    padding: var(--spacing-md);
    border: 2px solid var(--border-primary);
    border-radius: var(--radius-sm);
    cursor: pointer;
    transition: all 0.2s;
    background: var(--theme-bg-primary);
    min-height: 48px;
  }

  .item-checkbox:hover {
    background: var(--theme-bg-secondary);
    border-color: var(--accent-primary);
    transform: translateY(-1px);
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  }

  .item-checkbox:active {
    transform: translateY(0);
  }

  .item-checkbox input[type="checkbox"] {
    cursor: pointer;
    width: 20px;
    height: 20px;
    accent-color: var(--accent-primary);
    flex-shrink: 0;
  }

  .item-name {
    flex: 1;
    font-size: var(--text-sm);
    color: var(--text-primary);
  }

  .item-price {
    font-size: var(--text-sm);
    font-weight: 600;
    color: var(--accent-success);
  }

  .loading,
  .error {
    padding: var(--spacing-md);
    text-align: center;
    border-radius: var(--radius-md);
  }

  .loading {
    background: var(--theme-bg-secondary);
    color: var(--text-secondary);
  }

  .error {
    background: rgba(211, 5, 84, 0.1);
    border: 1px solid var(--accent-danger);
    color: var(--accent-danger);
  }

  /* Tablet */
  @media (min-width: 769px) and (max-width: 1024px) {
    .items-grid {
      grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    }

    .section-header {
      flex-wrap: wrap;
    }

    .section-actions {
      flex: 1;
      justify-content: flex-end;
    }
  }

  /* Mobile */
  @media (max-width: 768px) {
    .item-selector {
      max-height: 500px;
      padding: var(--spacing-sm);
      gap: var(--spacing-md);
    }

    .section {
      gap: var(--spacing-sm);
    }

    .section-header {
      flex-direction: column;
      align-items: stretch;
      gap: var(--spacing-sm);
    }

    .section-title {
      font-size: var(--text-base);
      text-align: center;
    }

    .section-actions {
      width: 100%;
      flex-direction: column;
      gap: var(--spacing-xs);
    }

    .section-actions :global(button) {
      width: 100%;
      min-height: 44px; /* Minimum touch target size for accessibility */
      justify-content: center;
    }

    .items-grid {
      grid-template-columns: 1fr;
      gap: var(--spacing-xs);
    }

    .item-checkbox {
      min-height: 52px; /* Larger touch target on mobile */
      padding: var(--spacing-sm) var(--spacing-md);
    }

    .item-name {
      font-size: var(--text-sm);
    }

    .item-price {
      font-size: var(--text-sm);
    }
  }

  /* Prevent hover transform issues on touch devices */
  @media (hover: none) and (pointer: coarse) {
    .section-actions :global(.btn-brutalist:hover),
    .item-checkbox:hover {
      transform: none;
    }

    .section-actions :global(.btn-brutalist:hover) {
      box-shadow: 3px 3px 0px 0px var(--accent-primary);
      border-width: 2px;
    }

    .item-checkbox:hover {
      border-color: var(--accent-primary);
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
  }
</style>

