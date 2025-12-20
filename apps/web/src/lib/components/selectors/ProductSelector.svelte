<script lang="ts">
  /**
   * ProductSelector component - Select products and quantities.
   * 
   * Displays available products and allows adding to cart.
   * Based on ServiceSelector.svelte pattern, adapted for products.
   */
  import type { Product } from "@kidyland/shared/types";
  import { Button } from "@kidyland/ui";

  export let products: Product[] = [];
  export let selectedItems: Array<{ product: Product; quantity: number }> = [];
  export let error: string | null = null;

  let selectedProductId = "";
  let quantity = 1;

  $: selectedProduct = products.find((p) => p.id === selectedProductId);

  function handleProductChange(event: Event) {
    const target = event.target as HTMLSelectElement;
    selectedProductId = target.value;
    quantity = 1; // Reset quantity when product changes
  }

  function addToCart() {
    if (!selectedProduct) return;

    // Check if product already in cart
    const existingIndex = selectedItems.findIndex(
      (item) => item.product.id === selectedProduct.id
    );

    if (existingIndex >= 0) {
      // Update quantity if already in cart
      selectedItems[existingIndex].quantity += quantity;
    } else {
      // Add new item to cart
      selectedItems = [...selectedItems, { product: selectedProduct, quantity }];
    }

    // Reset selection
    selectedProductId = "";
    quantity = 1;
  }

  function removeFromCart(index: number) {
    selectedItems = selectedItems.filter((_, i) => i !== index);
  }

  function updateQuantity(index: number, newQuantity: number) {
    if (newQuantity <= 0) {
      removeFromCart(index);
      return;
    }
    selectedItems[index].quantity = newQuantity;
    selectedItems = [...selectedItems]; // Trigger reactivity
  }

  function formatPrice(cents: number): string {
    return `$${(cents / 100).toFixed(2)}`;
  }

  $: cartTotal = selectedItems.reduce(
    (total, item) => total + item.product.price_cents * item.quantity,
    0
  );
</script>

<div class="product-selector">
  <div class="form-group">
    <label for="product-select" class="label">
      Producto <span class="required">*</span>
    </label>
    <select
      id="product-select"
      class="select"
      value={selectedProductId}
      on:change={handleProductChange}
      disabled={products.length === 0}
    >
      <option value="">Seleccione un producto</option>
      {#each products as product}
        <option value={product.id} disabled={product.stock_qty === 0}>
          {product.name} - {formatPrice(product.price_cents)}
          {product.stock_qty === 0 ? " (Sin stock)" : ` (Stock: ${product.stock_qty})`}
        </option>
      {/each}
    </select>
    {#if products.length === 0}
      <p class="help-text">Cargando productos...</p>
    {/if}
  </div>

  {#if selectedProduct}
    <div class="form-group">
      <label for="quantity-input" class="label">
        Cantidad <span class="required">*</span>
      </label>
      <div class="quantity-controls">
        <input
          id="quantity-input"
          type="number"
          min="1"
          max={selectedProduct.stock_qty}
          class="input"
          bind:value={quantity}
        />
        <span class="stock-info">
          Stock disponible: {selectedProduct.stock_qty}
        </span>
      </div>
      {#if quantity > selectedProduct.stock_qty}
        <p class="error-text">
          Cantidad excede stock disponible
        </p>
      {/if}
    </div>

    <div class="add-to-cart">
      <Button
        variant="primary"
        on:click={addToCart}
        disabled={quantity <= 0 || quantity > selectedProduct.stock_qty}
      >
        ➕ Agregar al Carrito
      </Button>
    </div>
  {/if}

  {#if selectedItems.length > 0}
    <div class="cart-section">
      <h3 class="cart-title">Carrito de Compras</h3>
      <div class="cart-items">
        {#each selectedItems as item, index}
          <div class="cart-item">
            <div class="cart-item-info">
              <span class="cart-item-name">{item.product.name}</span>
              <span class="cart-item-price">
                {formatPrice(item.product.price_cents)} c/u
              </span>
            </div>
            <div class="cart-item-controls">
              <input
                type="number"
                min="1"
                max={item.product.stock_qty}
                class="quantity-input-small"
                value={item.quantity}
                on:input={(e) =>
                  updateQuantity(index, parseInt(e.target.value) || 1)}
              />
              <Button
                variant="danger"
                on:click={() => removeFromCart(index)}
              >
                🗑️
              </Button>
            </div>
            <div class="cart-item-total">
              Total: {formatPrice(item.product.price_cents * item.quantity)}
            </div>
          </div>
        {/each}
      </div>
      <div class="cart-total">
        <span class="total-label">Total del Carrito:</span>
        <span class="total-value">{formatPrice(cartTotal)}</span>
      </div>
    </div>
  {/if}

  {#if error}
    <div class="error-message">{error}</div>
  {/if}
</div>

<style>
  .product-selector {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-lg);
  }

  .form-group {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-sm);
  }

  .label {
    font-weight: 600;
    font-size: var(--text-base);
    color: var(--text-primary);
  }

  .required {
    color: var(--accent-danger);
  }

  .select,
  .input {
    width: 100%;
    min-height: 48px;
    padding: var(--spacing-sm) var(--spacing-md);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
    font-size: var(--text-base);
    background: var(--theme-bg-elevated);
    color: var(--text-primary);
    transition: border-color 0.2s ease;
  }

  .select:focus,
  .input:focus {
    outline: none;
    border-color: var(--accent-primary);
    box-shadow: 0 0 0 3px rgba(0, 147, 247, 0.1);
  }

  .select:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .help-text {
    font-size: var(--text-sm);
    color: var(--text-muted);
  }

  .quantity-controls {
    display: flex;
    align-items: center;
    gap: var(--spacing-md);
  }

  .stock-info {
    font-size: var(--text-sm);
    color: var(--text-secondary);
  }

  .error-text {
    color: var(--accent-danger);
    font-size: var(--text-sm);
    font-weight: 600;
  }

  .add-to-cart {
    margin-top: var(--spacing-md);
  }

  .cart-section {
    margin-top: var(--spacing-xl);
    padding: var(--spacing-lg);
    background: var(--theme-bg-secondary);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-lg);
  }

  .cart-title {
    font-family: var(--font-primary);
    font-size: var(--text-xl);
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: var(--spacing-lg);
  }

  .cart-items {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-md);
    margin-bottom: var(--spacing-lg);
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
    margin-bottom: var(--spacing-sm);
  }

  .cart-item-name {
    font-weight: 600;
    color: var(--text-primary);
  }

  .cart-item-price {
    font-size: var(--text-sm);
    color: var(--text-secondary);
  }

  .cart-item-controls {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    margin-bottom: var(--spacing-sm);
  }

  .quantity-input-small {
    width: 80px;
    min-height: 40px;
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

  .error-message {
    padding: var(--spacing-sm) var(--spacing-md);
    background: rgba(211, 5, 84, 0.1);
    border: 1px solid var(--accent-danger);
    border-radius: var(--radius-md);
    color: var(--accent-danger);
    font-size: var(--text-sm);
  }
</style>

