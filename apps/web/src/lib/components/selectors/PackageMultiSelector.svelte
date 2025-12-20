<script lang="ts">
  /**
   * PackageMultiSelector component - Multi-select packages with quantity.
   * 
   * Displays packages in a grid with checkboxes and conditional quantity inputs.
   * Based on ProductMultiSelector pattern, adapted for package sales with quantities.
   */
  import { tick } from "svelte";
  import { fade } from "svelte/transition";
  import { Button } from "@kidyland/ui";
  import { Package, CheckSquare, Square } from "lucide-svelte";
  import type { Package as PackageType } from "@kidyland/shared/types";
  import type { Product } from "@kidyland/shared/types";

  export let packages: PackageType[] = [];
  export let products: Product[] = []; // For displaying product names in included_items
  export let selectedItems: Array<{ package: PackageType; quantity: number }> = [];
  export let error: string | null = null;

  // Product name mapping for displaying included items
  $: productMap = new Map(
    products.map((p: { id: string; name: string }) => [p.id, p.name])
  );

  // Internal state: Map of packageId -> quantity
  // This allows O(1) lookup for checking if a package is selected
  $: selectedMap = new Map(
    selectedItems.map((item) => [item.package.id, item.quantity])
  );

  // Computed: selected package IDs
  $: selectedPackageIds = Array.from(selectedMap.keys());

  // Computed: selected count
  $: selectedCount = selectedPackageIds.length;

  // Computed: total count
  $: totalCount = packages.length;

  // Computed: cart total
  $: cartTotal = selectedItems.reduce(
    (total, item) => total + item.package.price_cents * item.quantity,
    0
  );

  function formatPrice(cents: number): string {
    return `$${(cents / 100).toFixed(2)}`;
  }

  function togglePackage(packageId: string) {
    const pkg = packages.find((p) => p.id === packageId);
    if (!pkg) return;

    const isSelected = selectedMap.has(packageId);

    if (isSelected) {
      // Remove from selection
      selectedItems = selectedItems.filter((item) => item.package.id !== packageId);
    } else {
      // Add to selection with default quantity of 1
      selectedItems = [...selectedItems, { package: pkg, quantity: 1 }];
    }
  }

  function updateQuantity(packageId: string, newQuantity: number) {
    const pkg = packages.find((p) => p.id === packageId);
    if (!pkg) return;

    // Clamp quantity to valid range (minimum 1, no maximum for packages)
    const clampedQuantity = Math.max(1, newQuantity);

    const existingIndex = selectedItems.findIndex(
      (item) => item.package.id === packageId
    );

    if (existingIndex >= 0) {
      // Update quantity
      selectedItems[existingIndex].quantity = clampedQuantity;
      selectedItems = [...selectedItems]; // Trigger reactivity
    }
  }

  function removeFromCart(packageId: string) {
    selectedItems = selectedItems.filter((item) => item.package.id !== packageId);
  }

  async function selectAll() {
    const newItems = packages.map((pkg) => ({
      package: pkg,
      quantity: 1,
    }));
    selectedItems = [...newItems];
    await tick();
  }

  async function deselectAll() {
    selectedItems = [];
    await tick();
  }

  function getQuantity(packageId: string): number {
    return selectedMap.get(packageId) || 1;
  }

  function isSelected(packageId: string): boolean {
    return selectedMap.has(packageId);
  }

  function getProductName(productId: string | undefined): string {
    if (!productId) return "Producto desconocido";
    const productName = productMap.get(productId);
    return productName || `Producto ID: ${productId.slice(0, 8)}...`;
  }

  function handleQuantityInput(packageId: string, event: Event) {
    const target = event.target as HTMLInputElement;
    const value = parseInt(target.value) || 1;
    updateQuantity(packageId, value);
  }

  function handleCartQuantityInput(packageId: string, event: Event) {
    const target = event.target as HTMLInputElement;
    const value = parseInt(target.value) || 1;
    updateQuantity(packageId, value);
  }
</script>

<div class="package-multi-selector">
  <!-- Header with actions -->
  <div class="selector-header">
    <div class="header-title">
      <Package size={20} strokeWidth={1.5} />
      <h3 class="section-title">
        Paquetes ({selectedCount}/{totalCount})
      </h3>
    </div>
    <div class="header-actions">
      <Button
        variant="brutalist"
        size="sm"
        on:click={selectAll}
        disabled={selectedCount === totalCount || packages.length === 0}
      >
        <CheckSquare size={16} strokeWidth={1.5} />
        Seleccionar todos
      </Button>
      <Button
        variant="brutalist"
        size="sm"
        on:click={deselectAll}
        disabled={selectedCount === 0}
      >
        <Square size={16} strokeWidth={1.5} />
        Deseleccionar todos
      </Button>
    </div>
  </div>

  <!-- Packages Grid -->
  {#if packages.length === 0}
    <div class="empty-state">
      <p>No hay paquetes disponibles</p>
    </div>
  {:else}
    <div class="packages-grid">
      {#each packages as pkg (pkg.id)}
        {@const isSelected = isSelected(pkg.id)}
        {@const quantity = getQuantity(pkg.id)}
        <label
          class="package-checkbox"
          class:selected={isSelected}
        >
          <div class="checkbox-wrapper">
            <input
              type="checkbox"
              checked={isSelected}
              on:change={() => togglePackage(pkg.id)}
            />
          </div>
          <div class="package-info">
            <div class="package-name">{pkg.name}</div>
            {#if pkg.description}
              <div class="package-description">{pkg.description}</div>
            {/if}
            <div class="package-details">
              <span class="package-price">{formatPrice(pkg.price_cents)}</span>
            </div>
            {#if pkg.included_items && pkg.included_items.length > 0}
              <div class="package-items-preview">
                <span class="items-label">Productos incluidos:</span>
                <ul class="items-list">
                  {#each pkg.included_items.filter((item) => item.product_id) as item}
                    <li class="item-entry">
                      <span class="item-name">{getProductName(item.product_id)}</span>
                      {#if item.quantity && item.quantity > 1}
                        <span class="item-quantity">(x{item.quantity})</span>
                      {/if}
                    </li>
                  {/each}
                </ul>
              </div>
            {/if}
          </div>
          {#if isSelected}
            <div class="quantity-wrapper" transition:fade={{ duration: 200 }}>
              <label class="quantity-label" for="qty-{pkg.id}">Cantidad:</label>
              <input
                id="qty-{pkg.id}"
                type="number"
                min="1"
                value={quantity}
                class="quantity-input"
                on:input={(e) => handleQuantityInput(pkg.id, e)}
              />
            </div>
          {/if}
        </label>
      {/each}
    </div>
  {/if}

  <!-- Cart Summary -->
  {#if selectedItems.length > 0}
    <div class="cart-summary">
      <h4 class="cart-title">Resumen del Carrito</h4>
      <div class="cart-items">
        {#each selectedItems as item (item.package.id)}
          <div class="cart-item">
            <div class="cart-item-info">
              <span class="cart-item-name">{item.package.name}</span>
              <span class="cart-item-details">
                {formatPrice(item.package.price_cents)} × {item.quantity}
              </span>
            </div>
            <div class="cart-item-actions">
              <input
                type="number"
                min="1"
                value={item.quantity}
                class="cart-quantity-input"
                on:input={(e) => handleCartQuantityInput(item.package.id, e)}
              />
              <Button
                variant="danger"
                size="sm"
                on:click={() => removeFromCart(item.package.id)}
              >
                🗑️
              </Button>
            </div>
            <div class="cart-item-total">
              {formatPrice(item.package.price_cents * item.quantity)}
            </div>
          </div>
        {/each}
      </div>
      <div class="cart-total">
        <span class="total-label">Total:</span>
        <span class="total-value">{formatPrice(cartTotal)}</span>
      </div>
    </div>
  {/if}

  {#if error}
    <div class="error-message">{error}</div>
  {/if}
</div>

<style>
  .package-multi-selector {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-lg);
  }

  .selector-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: var(--spacing-md);
    padding-bottom: var(--spacing-md);
    border-bottom: 2px solid var(--border-primary);
  }

  .header-title {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
  }

  .section-title {
    font-family: var(--font-primary);
    font-size: var(--text-xl);
    font-weight: 700;
    color: var(--text-primary);
    margin: 0;
  }

  .header-actions {
    display: flex;
    gap: var(--spacing-sm);
    flex-wrap: wrap;
  }

  .packages-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: var(--spacing-md);
  }

  .package-checkbox {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-sm);
    padding: var(--spacing-md);
    border: 2px solid var(--border-primary);
    border-radius: var(--radius-md);
    cursor: pointer;
    transition: all 0.2s ease;
    background: var(--theme-bg-primary);
    min-height: 120px;
  }

  .package-checkbox:hover {
    background: var(--theme-bg-secondary);
    border-color: var(--accent-primary);
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
  }

  .package-checkbox.selected {
    border-color: var(--accent-primary);
    background: var(--theme-bg-secondary);
    box-shadow: 0 0 0 3px rgba(0, 147, 247, 0.1);
  }

  .package-checkbox:active {
    transform: translateY(0);
  }

  .checkbox-wrapper {
    display: flex;
    align-items: center;
  }

  .checkbox-wrapper input[type="checkbox"] {
    cursor: pointer;
    width: 20px;
    height: 20px;
    accent-color: var(--accent-primary);
    flex-shrink: 0;
  }

  .package-info {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xs);
  }

  .package-name {
    font-weight: 600;
    font-size: var(--text-base);
    color: var(--text-primary);
  }

  .package-description {
    font-size: var(--text-xs);
    color: var(--text-secondary);
    line-height: 1.4;
  }

  .package-details {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: var(--spacing-sm);
    flex-wrap: wrap;
  }

  .package-price {
    font-size: var(--text-lg);
    font-weight: 700;
    color: var(--accent-success);
  }

  .package-items-preview {
    margin-top: var(--spacing-xs);
    padding-top: var(--spacing-xs);
    border-top: 1px solid var(--border-primary);
  }

  .items-label {
    font-size: var(--text-xs);
    font-weight: 600;
    color: var(--text-secondary);
    display: block;
    margin-bottom: var(--spacing-xs);
  }

  .items-list {
    list-style: none;
    padding: 0;
    margin: 0;
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .item-entry {
    font-size: var(--text-xs);
    color: var(--text-primary);
    display: flex;
    align-items: center;
    gap: var(--spacing-xs);
  }

  .item-name {
    flex: 1;
  }

  .item-quantity {
    font-size: var(--text-xs);
    color: var(--text-secondary);
    font-weight: 600;
  }

  .quantity-wrapper {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xs);
    margin-top: var(--spacing-xs);
    padding-top: var(--spacing-sm);
    border-top: 1px solid var(--border-primary);
  }

  .quantity-label {
    font-size: var(--text-xs);
    font-weight: 600;
    color: var(--text-secondary);
  }

  .quantity-input {
    width: 100%;
    min-height: 40px;
    padding: var(--spacing-xs) var(--spacing-sm);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-sm);
    font-size: var(--text-base);
    background: var(--theme-bg-elevated);
    color: var(--text-primary);
    transition: border-color 0.2s ease;
  }

  .quantity-input:focus {
    outline: none;
    border-color: var(--accent-primary);
    box-shadow: 0 0 0 3px rgba(0, 147, 247, 0.1);
  }

  .cart-summary {
    margin-top: var(--spacing-lg);
    padding: var(--spacing-lg);
    background: var(--theme-bg-secondary);
    border: 2px solid var(--border-primary);
    border-radius: var(--radius-lg);
  }

  .cart-title {
    font-family: var(--font-primary);
    font-size: var(--text-lg);
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: var(--spacing-md);
  }

  .cart-items {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-sm);
    margin-bottom: var(--spacing-md);
  }

  .cart-item {
    padding: var(--spacing-md);
    background: var(--theme-bg-elevated);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
  }

  .cart-item-info {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--spacing-xs);
    flex-wrap: wrap;
    gap: var(--spacing-xs);
  }

  .cart-item-name {
    font-weight: 600;
    color: var(--text-primary);
    flex: 1;
  }

  .cart-item-details {
    font-size: var(--text-sm);
    color: var(--text-secondary);
  }

  .cart-item-actions {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    margin-bottom: var(--spacing-xs);
  }

  .cart-quantity-input {
    width: 80px;
    min-height: 36px;
    padding: var(--spacing-xs) var(--spacing-sm);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-sm);
    font-size: var(--text-sm);
    background: var(--theme-bg-elevated);
    color: var(--text-primary);
  }

  .cart-item-total {
    font-weight: 600;
    color: var(--accent-primary);
    font-size: var(--text-sm);
    text-align: right;
  }

  .cart-total {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: var(--spacing-md);
    background: var(--theme-bg-elevated);
    border: 2px solid var(--accent-primary);
    border-radius: var(--radius-md);
  }

  .total-label {
    font-weight: 600;
    font-size: var(--text-lg);
    color: var(--text-primary);
  }

  .total-value {
    font-size: var(--text-2xl);
    font-weight: 700;
    color: var(--accent-primary);
    font-family: var(--font-secondary);
  }

  .empty-state {
    padding: var(--spacing-xl);
    text-align: center;
    color: var(--text-muted);
  }

  .error-message {
    padding: var(--spacing-md);
    background: rgba(211, 5, 84, 0.1);
    border: 1px solid var(--accent-danger);
    border-radius: var(--radius-md);
    color: var(--accent-danger);
    font-size: var(--text-sm);
  }

  /* Tablet */
  @media (min-width: 769px) and (max-width: 1024px) {
    .packages-grid {
      grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
    }

    .selector-header {
      flex-direction: column;
      align-items: stretch;
    }

    .header-actions {
      width: 100%;
      justify-content: flex-end;
    }
  }

  /* Mobile */
  @media (max-width: 768px) {
    .packages-grid {
      grid-template-columns: 1fr;
      gap: var(--spacing-sm);
    }

    .selector-header {
      flex-direction: column;
      align-items: stretch;
      gap: var(--spacing-sm);
    }

    .header-actions {
      width: 100%;
      flex-direction: column;
    }

    .header-actions :global(button) {
      width: 100%;
      min-height: 44px;
      justify-content: center;
    }

    .package-checkbox {
      min-height: auto;
      padding: var(--spacing-sm) var(--spacing-md);
    }

    .package-details {
      flex-direction: column;
      align-items: flex-start;
    }
  }

  /* Prevent hover transform issues on touch devices */
  @media (hover: none) and (pointer: coarse) {
    .package-checkbox:hover {
      transform: none;
      box-shadow: 0 0 0 3px rgba(0, 147, 247, 0.1);
    }
  }
</style>





