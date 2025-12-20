<script lang="ts">
  /**
   * PackageItemConfig - Inline configuration component for package items.
   * 
   * Handles configuration for products (quantity) and services (duration).
   */
  import { AlertCircle } from "lucide-svelte";
  import type { Product, Service } from "@kidyland/shared/types";

  export let itemType: "product" | "service";
  export let product: Product | undefined = undefined;
  export let service: Service | undefined = undefined;
  export let quantity: number = 1;
  export let durationMinutes: number | undefined = undefined;
  export let onQuantityChange: ((quantity: number) => void) | undefined = undefined;
  export let onDurationChange: ((durationMinutes: number) => void) | undefined = undefined;
  export let error: string | undefined = undefined;
  export let disabled: boolean = false;

  // Format duration for display
  function formatDuration(minutes: number): string {
    if (minutes < 60) {
      return `${minutes} min`;
    }
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    if (mins === 0) {
      return `${hours} ${hours === 1 ? "hora" : "horas"}`;
    }
    return `${hours}h ${mins}min`;
  }

  function handleQuantityInput(e: Event) {
    const target = e.currentTarget as HTMLInputElement;
    const newQuantity = parseInt(target.value, 10) || 0;
    if (onQuantityChange) {
      onQuantityChange(newQuantity);
    }
  }

  function handleDurationSelect(e: Event) {
    const target = e.currentTarget as HTMLSelectElement;
    const newDuration = parseInt(target.value, 10) || 0;
    if (onDurationChange && newDuration > 0) {
      onDurationChange(newDuration);
    }
  }

  // Validate stock for products
  $: stockError = itemType === "product" && product
    ? quantity > product.stock_qty
      ? `Stock insuficiente. Disponible: ${product.stock_qty}`
      : undefined
    : undefined;

  $: hasError = !!error || !!stockError;
</script>

<div class="item-config">
  {#if itemType === "product" && product}
    <!-- Product Quantity Configuration -->
    <div class="config-field">
      <label for="item-quantity" class="config-label">
        Cantidad <span class="required">*</span>
      </label>
      <div class="input-wrapper">
        <input
          id="item-quantity"
          type="number"
          min="1"
          max={product.stock_qty}
          value={quantity}
          on:input={handleQuantityInput}
          disabled={disabled}
          class="input"
          class:error={hasError}
          aria-describedby="help-item-quantity"
        />
      </div>
      <p id="help-item-quantity" class="help-text">
        Cantidad de este producto que se incluirá en el paquete
        {#if product.stock_qty !== undefined}
          <span class="stock-info">(Stock disponible: {product.stock_qty})</span>
        {/if}
      </p>
      {#if stockError}
        <p class="error-text">
          <AlertCircle size={14} />
          {stockError}
        </p>
      {/if}
      {#if error}
        <p class="error-text">
          <AlertCircle size={14} />
          {error}
        </p>
      {/if}
    </div>
  {:else if itemType === "service" && service}
    <!-- Service Duration Configuration -->
    <div class="config-field">
      <label for="item-duration" class="config-label">
        Duración <span class="required">*</span>
      </label>
      <div class="input-wrapper">
        <select
          id="item-duration"
          value={durationMinutes || ""}
          on:change={handleDurationSelect}
          disabled={disabled}
          class="input select"
          class:error={hasError}
          aria-describedby="help-item-duration"
        >
          <option value="">Seleccione duración</option>
          {#each service.durations_allowed || [] as duration}
            <option value={duration}>
              {formatDuration(duration)}
              {#if service.duration_prices && service.duration_prices[duration]}
                - ${((service.duration_prices[duration] || 0) / 100).toFixed(2)}
              {/if}
            </option>
          {/each}
        </select>
      </div>
      <p id="help-item-duration" class="help-text">
        Duración de la renta (sin timer). Se pueden vender múltiples veces el mismo día.
      </p>
      {#if error}
        <p class="error-text">
          <AlertCircle size={14} />
          {error}
        </p>
      {/if}
    </div>
  {/if}
</div>

<style>
  .item-config {
    margin-top: 12px;
    padding: 12px;
    background: var(--theme-bg-secondary, rgba(15, 23, 42, 0.4));
    border-radius: 8px;
    border: 1px solid var(--border-primary, rgba(148, 163, 184, 0.2));
  }

  .config-field {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .config-label {
    font-size: 0.875rem;
    font-weight: 500;
    color: var(--text-primary, #e2e8f0);
    margin-bottom: 4px;
  }

  .required {
    color: var(--error, #ef4444);
    margin-left: 0.25rem;
  }

  .input-wrapper {
    position: relative;
    width: 100%;
  }

  .input {
    width: 100%;
    background-color: var(--input-bg, #303245);
    border-radius: 12px;
    border: 1px solid var(--border-primary, #444);
    box-sizing: border-box;
    color: var(--text-primary, #eee);
    font-size: 16px;
    height: 44px;
    outline: 0;
    padding: 0 16px;
    font-family: var(--font-body, sans-serif);
    transition: all 0.2s ease;
  }

  .input:focus {
    background-color: var(--input-bg-focus, #3a3d52);
    border-color: var(--accent-primary, #0093f7);
  }

  .input.error {
    border: 2px solid var(--accent-danger, #dc2f55);
  }

  .input:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .input.select {
    cursor: pointer;
    appearance: none;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%2365657b' d='M6 9L1 4h10z'/%3E%3C/svg%3E");
    background-repeat: no-repeat;
    background-position: right 16px center;
    padding-right: 40px;
  }

  .help-text {
    font-size: 12px;
    color: #808097;
    margin-top: 4px;
    margin-bottom: 0;
    padding-left: 4px;
  }

  .stock-info {
    color: var(--text-secondary, rgba(148, 163, 184, 0.7));
    font-weight: normal;
  }

  .error-text {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-top: 4px;
    margin-bottom: 0;
    font-size: 12px;
    color: #dc2f55;
    padding-left: 4px;
  }
</style>


















