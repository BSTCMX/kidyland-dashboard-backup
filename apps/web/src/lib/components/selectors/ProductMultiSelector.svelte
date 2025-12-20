<script lang="ts">
  /**
   * ProductMultiSelector component - Multi-select products with quantity.
   * 
   * Displays products in a grid with checkboxes and conditional quantity inputs.
   * Based on ItemSelector pattern, adapted for product sales with quantities.
   */
  import { tick } from "svelte";
  import { fade } from "svelte/transition";
  import { Button } from "@kidyland/ui";
  import { ShoppingBag, CheckSquare, Square } from "lucide-svelte";
  import type { Product } from "@kidyland/shared/types";

  export let products: Product[] = [];
  export let selectedItems: Array<{ product: Product; quantity: number }> = [];
  export let error: string | null = null;

  // Internal state: Map of productId -> quantity
  // This allows O(1) lookup for checking if a product is selected
  $: selectedMap = new Map(
    selectedItems.map((item) => [item.product.id, item.quantity])
  );

  // Computed: selected product IDs
  $: selectedProductIds = Array.from(selectedMap.keys());

  // Computed: selected count
  $: selectedCount = selectedProductIds.length;

  // Computed: total count
  $: totalCount = products.length;

  // Computed: cart total
  $: cartTotal = selectedItems.reduce(
    (total, item) => total + item.product.price_cents * item.quantity,
    0
  );

  function formatPrice(cents: number): string {
    return `$${(cents / 100).toFixed(2)}`;
  }

  function toggleProduct(productId: string) {
    const product = products.find((p) => p.id === productId);
    if (!product) return;

    const isSelected = selectedMap.has(productId);

    if (isSelected) {
      // Remove from selection
      selectedItems = selectedItems.filter((item) => item.product.id !== productId);
    } else {
      // Add to selection with default quantity of 1
      if (product.stock_qty > 0) {
        selectedItems = [...selectedItems, { product, quantity: 1 }];
      }
    }
  }

  function updateQuantity(productId: string, newQuantity: number) {
    const product = products.find((p) => p.id === productId);
    if (!product) return;

    // Clamp quantity to valid range
    const clampedQuantity = Math.max(1, Math.min(newQuantity, product.stock_qty));

    const existingIndex = selectedItems.findIndex(
      (item) => item.product.id === productId
    );

    if (existingIndex >= 0) {
      // Update quantity
      selectedItems[existingIndex].quantity = clampedQuantity;
      selectedItems = [...selectedItems]; // Trigger reactivity
    }
  }

  function removeFromCart(productId: string) {
    selectedItems = selectedItems.filter((item) => item.product.id !== productId);
  }

  async function selectAll() {
    const availableProducts = products.filter((p) => p.stock_qty > 0);
    const newItems = availableProducts.map((product) => ({
      product,
      quantity: 1,
    }));
    selectedItems = [...newItems];
    await tick();
  }

  async function deselectAll() {
    selectedItems = [];
    await tick();
  }

  function getQuantity(productId: string): number {
    return selectedMap.get(productId) || 1;
  }

  function isSelected(productId: string): boolean {
    return selectedMap.has(productId);
  }

  function hasStock(product: Product): boolean {
    return product.stock_qty > 0;
  }

  function getStockStatus(product: Product): string {
    if (product.stock_qty === 0) return "Sin stock";
    if (product.stock_qty <= 5) return `Stock bajo (${product.stock_qty})`;
    return `Stock: ${product.stock_qty}`;
  }

  function handleQuantityInput(productId: string, event: Event) {
    const target = event.target as HTMLInputElement;
    const value = parseInt(target.value) || 1;
    updateQuantity(productId, value);
  }

  function handleCartQuantityInput(productId: string, event: Event) {
    const target = event.target as HTMLInputElement;
    const value = parseInt(target.value) || 1;
    updateQuantity(productId, value);
  }
</script>

<div class="product-multi-selector">
  <!-- Header with actions -->
  <div class="selector-header">
    <div class="header-title">
      <ShoppingBag size={20} strokeWidth={1.5} />
      <h3 class="section-title">
        Productos ({selectedCount}/{totalCount})
      </h3>
    </div>
    <div class="header-actions">
      <Button
        variant="brutalist"
        size="sm"
        on:click={selectAll}
        disabled={selectedCount === totalCount || products.filter((p) => p.stock_qty > 0).length === 0}
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

  <!-- Products Grid -->
  {#if products.length === 0}
    <div class="empty-state">
      <p>No hay productos disponibles</p>
    </div>
  {:else}
    <div class="products-grid">
      {#each products as product (product.id)}
        {@const isSelected = isSelected(product.id)}
        {@const quantity = getQuantity(product.id)}
        {@const hasAvailableStock = hasStock(product)}
        <label
          class="product-checkbox"
          class:selected={isSelected}
          class:no-stock={!hasAvailableStock}
        >
          <div class="checkbox-wrapper">
            <input
              type="checkbox"
              checked={isSelected}
              disabled={!hasAvailableStock}
              on:change={() => toggleProduct(product.id)}
            />
          </div>
          <div class="product-info">
            <div class="product-name">{product.name}</div>
            <div class="product-details">
              <span class="product-price">{formatPrice(product.price_cents)}</span>
              <span
                class="stock-badge"
                class:low-stock={product.stock_qty > 0 && product.stock_qty <= 5}
                class:no-stock={product.stock_qty === 0}
              >
                {getStockStatus(product)}
              </span>
            </div>
          </div>
          {#if isSelected}
            <div class="quantity-wrapper" transition:fade={{ duration: 200 }}>
              <label class="quantity-label" for="qty-{product.id}">Cantidad:</label>
              <input
                id="qty-{product.id}"
                type="number"
                min="1"
                max={product.stock_qty}
                value={quantity}
                class="quantity-input"
                on:input={(e) => handleQuantityInput(product.id, e)}
              />
              {#if quantity > product.stock_qty}
                <span class="quantity-error">
                  Máximo: {product.stock_qty}
                </span>
              {/if}
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
        {#each selectedItems as item (item.product.id)}
          <div class="cart-item">
            <div class="cart-item-info">
              <span class="cart-item-name">{item.product.name}</span>
              <span class="cart-item-details">
                {formatPrice(item.product.price_cents)} × {item.quantity}
              </span>
            </div>
            <div class="cart-item-actions">
              <input
                type="number"
                min="1"
                max={item.product.stock_qty}
                value={item.quantity}
                class="cart-quantity-input"
                on:input={(e) => handleCartQuantityInput(item.product.id, e)}
              />
              <Button
                variant="danger"
                size="sm"
                on:click={() => removeFromCart(item.product.id)}
              >
                🗑️
              </Button>
            </div>
            <div class="cart-item-total">
              {formatPrice(item.product.price_cents * item.quantity)}
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
  .product-multi-selector {
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

  .products-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: var(--spacing-md);
  }

  .product-checkbox {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-sm);
    padding: var(--spacing-md);
    border: 2px solid var(--border-primary);
    border-radius: var(--radius-md);
    cursor: pointer;
    transition: all 0.2s ease;
    background: var(--theme-bg-primary);
    min-height: 80px;
  }

  .product-checkbox:hover:not(.no-stock) {
    background: var(--theme-bg-secondary);
    border-color: var(--accent-primary);
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
  }

  .product-checkbox.selected {
    border-color: var(--accent-primary);
    background: var(--theme-bg-secondary);
    box-shadow: 0 0 0 3px rgba(0, 147, 247, 0.1);
  }

  .product-checkbox.no-stock {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .product-checkbox:active:not(.no-stock) {
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

  .product-info {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xs);
  }

  .product-name {
    font-weight: 600;
    font-size: var(--text-base);
    color: var(--text-primary);
  }

  .product-details {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: var(--spacing-sm);
    flex-wrap: wrap;
  }

  .product-price {
    font-size: var(--text-lg);
    font-weight: 700;
    color: var(--accent-success);
  }

  .stock-badge {
    font-size: var(--text-xs);
    padding: 2px 8px;
    border-radius: var(--radius-sm);
    background: var(--theme-bg-elevated);
    color: var(--text-secondary);
    border: 1px solid var(--border-primary);
  }

  .stock-badge.low-stock {
    background: rgba(255, 193, 7, 0.1);
    color: #ffc107;
    border-color: #ffc107;
  }

  .stock-badge.no-stock {
    background: rgba(211, 5, 84, 0.1);
    color: var(--accent-danger);
    border-color: var(--accent-danger);
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

  .quantity-error {
    font-size: var(--text-xs);
    color: var(--accent-danger);
    font-weight: 600;
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
    .products-grid {
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
    .products-grid {
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

    .product-checkbox {
      min-height: auto;
      padding: var(--spacing-sm) var(--spacing-md);
    }

    .product-details {
      flex-direction: column;
      align-items: flex-start;
    }
  }

  /* Prevent hover transform issues on touch devices */
  @media (hover: none) and (pointer: coarse) {
    .product-checkbox:hover:not(.no-stock) {
      transform: none;
      box-shadow: 0 0 0 3px rgba(0, 147, 247, 0.1);
    }
  }
</style>

