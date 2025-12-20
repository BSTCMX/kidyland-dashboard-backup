<script lang="ts">
  /**
   * ProductPackageSaleForm component - Package sale form for KidiBar (product packages only).
   * 
   * Handles complete product package sale creation flow:
   * 1. Package selection (pre-selected if packageId is provided)
   * 2. Payer information
   * 3. Payment details
   * 4. Confirmation
   * 
   * Based on PackageSaleForm.svelte, adapted for product packages only.
   */
  import { onMount } from "svelte";
  import { user } from "@kidyland/utils";
  import type { Package } from "@kidyland/shared/types";
  import { fetchAllPackages, packagesAdminStore } from "$lib/stores/packages-admin";
  import { fetchProducts, productsStore } from "$lib/stores/products";
  import { createPackageSale, salesStore } from "$lib/stores/sales";
  import { filterActiveProductPackages } from "$lib/utils/package-filters";
  import PaymentForm from "./PaymentForm.svelte";
  import { printTicket } from "$lib/stores/sales-history";

  export let packageId: string | null = null; // Optional: pre-select a package
  export let onClose: (() => void) | null = null;

  // Form state
  let currentStep = 1;
  const totalSteps = 3;

  // Package selection
  let selectedPackageId = packageId || "";
  let quantity = 1;

  // Payer info
  let payerName = "";
  let payerPhone = "";

  // Payment
  let paymentMethod: "cash" | "card" | "transfer" = "cash";
  let cashReceivedCents: number | undefined = undefined;
  let cardAuthCode = "";
  let transferReference = "";

  // State
  let loading = false;
  let printing = false;
  let error: string | null = null;
  let saleResponse: any = null;
  let availablePackages: Package[] = [];

  // Product name mapping for displaying included items
  $: productMap = new Map($productsStore.list.map((p: { id: string; name: string }) => [p.id, p.name]));

  // Use reactive store directly for automatic synchronization
  $: selectedPackage = availablePackages.find((p: Package) => p.id === selectedPackageId);
  $: totalCents =
    selectedPackage
      ? selectedPackage.price_cents * quantity
      : 0;

  // Helper function to get product name by ID
  function getProductName(productId: string | undefined): string {
    if (!productId) return "Producto desconocido";
    const productName = productMap.get(productId);
    return productName || `Producto ID: ${productId.slice(0, 8)}...`;
  }

  $: canProceedStep1 = selectedPackageId && quantity > 0;
  $: canProceedStep2 = true; // Name is now optional - always allow proceeding
  $: canProceedStep3 =
    paymentMethod === "cash"
      ? cashReceivedCents !== undefined && cashReceivedCents >= totalCents
      : paymentMethod === "card"
        ? cardAuthCode.trim() !== ""
        : paymentMethod === "transfer"
          ? transferReference.trim() !== ""
          : false;

  // Load packages and products on mount
  onMount(async () => {
    const currentUser = $user;
    if (!currentUser?.sucursal_id) {
      error = "No sucursal assigned";
      return;
    }

    loading = true;
    try {
      // Load packages and products in parallel
      await Promise.all([
        fetchAllPackages(currentUser.sucursal_id),
        fetchProducts(currentUser.sucursal_id)
      ]);
      
      // Filter to show only active product packages (KidiBar only sells product packages)
      availablePackages = filterActiveProductPackages($packagesAdminStore.list);
      
      // If packageId is provided, ensure it's selected
      if (packageId && !selectedPackageId) {
        selectedPackageId = packageId;
      }
    } catch (e: any) {
      error = e.message || "Error loading packages";
    } finally {
      loading = false;
    }
  });

  function nextStep() {
    if (currentStep < totalSteps) {
      currentStep++;
      error = null;
    }
  }

  function previousStep() {
    if (currentStep > 1) {
      currentStep--;
      error = null;
    }
  }

  async function submitSale() {
    const currentUser = $user;
    if (!currentUser?.sucursal_id || !selectedPackage) {
      error = "Missing required information";
      return;
    }

    loading = true;
    error = null;

    try {
      const formData = {
        packageId: selectedPackageId,
        quantity,
        payerName: payerName.trim() || undefined, // Optional now
        payerPhone: payerPhone.trim() || undefined,
        paymentMethod,
        cashReceivedCents,
        cardAuthCode: cardAuthCode.trim() || undefined,
        transferReference: transferReference.trim() || undefined,
      };

      saleResponse = await createPackageSale(
        formData,
        currentUser.sucursal_id,
        currentUser.id,
        selectedPackage.price_cents
      );

      // Move to confirmation step
      currentStep = 4;
    } catch (e: any) {
      error = e.message || "Error creating sale";
    } finally {
      loading = false;
    }
  }

  async function handlePrintTicket() {
    if (!saleResponse?.sale_id) {
      error = "No hay información de venta para imprimir";
      return;
    }

    printing = true;
    error = null;

    try {
      await printTicket(saleResponse.sale_id);
    } catch (e: any) {
      error = e.message || "Error al imprimir ticket";
    } finally {
      printing = false;
    }
  }

  function resetForm() {
    currentStep = 1;
    selectedPackageId = packageId || "";
    quantity = 1;
    payerName = "";
    payerPhone = "";
    paymentMethod = "cash";
    cashReceivedCents = undefined;
    cardAuthCode = "";
    transferReference = "";
    error = null;
    saleResponse = null;
    printing = false;
  }

  function handleClose() {
    if (onClose) {
      onClose();
    }
  }

  function formatPrice(cents: number): string {
    return `$${(cents / 100).toFixed(2)}`;
  }
</script>

<div class="sale-form-container">
  <div class="form-header">
    <div class="header-top">
      <h2 class="form-title">Nueva Venta - Paquete</h2>
      {#if onClose}
        <button class="close-button" on:click={handleClose} aria-label="Cerrar">
          ✕
        </button>
      {/if}
    </div>
    <div class="step-indicator">
      {#each Array(totalSteps) as _, i}
        <div
          class="step-dot"
          class:active={currentStep > i + 1}
          class:current={currentStep === i + 1}
        >
          {i + 1}
        </div>
        {#if i < totalSteps - 1}
          <div class="step-line" class:active={currentStep > i + 1}></div>
        {/if}
      {/each}
    </div>
  </div>

  {#if error}
    <div class="error-banner">{error}</div>
  {/if}

  {#if loading && currentStep === 1}
    <div class="loading-state">Cargando paquetes...</div>
  {:else if currentStep === 1}
    <!-- Step 1: Package Selection -->
    <div class="form-step">
      <h3 class="step-title">1. Seleccionar Paquete</h3>
      
      {#if availablePackages.length === 0}
        <div class="empty-state">
          <p>No hay paquetes de productos disponibles.</p>
        </div>
      {:else}
        <div class="package-selector">
          {#each availablePackages as pkg}
            <button
              class="package-option"
              class:selected={selectedPackageId === pkg.id}
              on:click={() => {
                selectedPackageId = pkg.id;
                error = null;
              }}
            >
              <div class="package-info">
                <h4 class="package-name">{pkg.name}</h4>
                {#if pkg.description}
                  <p class="package-description">{pkg.description}</p>
                {/if}
                <div class="package-price">{formatPrice(pkg.price_cents)}</div>
              </div>
              {#if selectedPackageId === pkg.id}
                <div class="selected-indicator">✓</div>
              {/if}
            </button>
          {/each}
        </div>

        {#if selectedPackage}
          <div class="quantity-selector">
            <label for="quantity" class="label">Cantidad</label>
            <div class="quantity-controls">
              <button
                class="quantity-button"
                on:click={() => {
                  if (quantity > 1) quantity--;
                }}
                disabled={quantity <= 1}
              >
                −
              </button>
              <input
                id="quantity"
                type="number"
                min="1"
                class="quantity-input"
                bind:value={quantity}
              />
              <button
                class="quantity-button"
                on:click={() => quantity++}
              >
                +
              </button>
            </div>
            <div class="subtotal-preview">
              Subtotal: {formatPrice(selectedPackage.price_cents * quantity)}
            </div>
          </div>
        {/if}
      {/if}

      <div class="step-actions">
        <button 
          type="button"
          class="btn btn-primary" 
          on:click={nextStep} 
          disabled={!canProceedStep1}
        >
          Siguiente →
        </button>
      </div>
    </div>
  {:else if currentStep === 2}
    <!-- Step 2: Payer Info -->
    <div class="form-step">
      <h3 class="step-title">2. Información del Cliente</h3>
      <div class="form-fields">
        <div class="input-wrapper">
          <label for="payer-name" class="label">
            Nombre del Cliente (opcional)
          </label>
          <input
            id="payer-name"
            type="text"
            class="input"
            bind:value={payerName}
            placeholder="Nombre completo (opcional)"
          />
        </div>
        <div class="input-wrapper">
          <label for="payer-phone" class="label">Teléfono (opcional)</label>
          <input
            id="payer-phone"
            type="tel"
            class="input"
            bind:value={payerPhone}
            placeholder="Teléfono de contacto"
          />
        </div>
        {#if selectedPackage && selectedPackage.included_items && selectedPackage.included_items.length > 0}
          <div class="package-items-preview">
            <p class="items-label">Productos incluidos:</p>
            <ul class="items-list">
              {#each selectedPackage.included_items.filter((item) => item.product_id) as item}
                <li class="item-entry">
                  {getProductName(item.product_id)}
                  {#if item.quantity && item.quantity > 1}
                    <span class="item-quantity">(x{item.quantity})</span>
                  {/if}
                </li>
              {/each}
            </ul>
          </div>
        {/if}
        <div class="summary-box">
          <div class="summary-row total">
            <span class="summary-label">Total:</span>
            <span class="summary-value">{formatPrice(totalCents)}</span>
          </div>
        </div>
      </div>
      <div class="step-actions">
        <button 
          type="button"
          class="btn btn-secondary" 
          on:click={previousStep}
        >
          ← Anterior
        </button>
        <button 
          type="button"
          class="btn btn-primary" 
          on:click={nextStep} 
          disabled={!canProceedStep2}
        >
          Siguiente →
        </button>
      </div>
    </div>
  {:else if currentStep === 3}
    <!-- Step 3: Payment -->
    <div class="form-step">
      <h3 class="step-title">3. Método de Pago</h3>
      <PaymentForm
        bind:paymentMethod
        bind:cashReceivedCents
        bind:cardAuthCode
        bind:transferReference
        {totalCents}
        {error}
      />
      <div class="step-actions">
        <button 
          type="button"
          class="btn btn-secondary" 
          on:click={previousStep}
        >
          ← Anterior
        </button>
        <button
          type="button"
          class="btn btn-primary"
          on:click={submitSale}
          disabled={!canProceedStep3 || loading}
        >
          {loading ? "Procesando..." : "Confirmar Venta"}
        </button>
      </div>
    </div>
  {:else if currentStep === 4}
    <!-- Step 4: Confirmation -->
    <div class="form-step confirmation">
      <div class="success-icon">✅</div>
      <h3 class="step-title">¡Venta Registrada Exitosamente!</h3>
      {#if saleResponse}
        <div class="confirmation-details">
          <div class="detail-row">
            <span class="detail-label">ID de Venta:</span>
            <span class="detail-value">{saleResponse.sale_id}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">Total:</span>
            <span class="detail-value">{formatPrice(totalCents)}</span>
          </div>
        </div>
      {/if}
      <div class="step-actions">
        {#if saleResponse?.sale_id}
          <button 
            type="button"
            class="btn btn-secondary" 
            on:click={handlePrintTicket}
            disabled={printing}
          >
            {printing ? "Imprimiendo..." : "Ver/Imprimir Ticket"}
          </button>
        {/if}
        <button 
          type="button"
          class="btn btn-primary" 
          on:click={resetForm}
        >
          Nueva Venta
        </button>
        {#if onClose}
          <button 
            type="button"
            class="btn btn-secondary" 
            on:click={handleClose}
          >
            Cerrar
          </button>
        {/if}
      </div>
    </div>
  {/if}
</div>

<style>
  .sale-form-container {
    max-width: 600px;
    margin: 0 auto;
    padding: var(--spacing-xl);
    background: var(--theme-bg-elevated);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-md);
  }

  .form-header {
    margin-bottom: var(--spacing-xl);
  }

  .header-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--spacing-lg);
  }

  .form-title {
    font-family: var(--font-primary);
    font-size: var(--text-2xl);
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: var(--spacing-lg);
  }

  .close-button {
    background: var(--theme-bg-secondary);
    border: 2px solid var(--border-primary);
    border-radius: var(--radius-md);
    font-size: 24px;
    color: var(--text-primary);
    cursor: pointer;
    padding: var(--spacing-xs);
    line-height: 1;
    min-width: 40px;
    min-height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }

  .close-button:hover {
    background: var(--accent-danger);
    border-color: var(--accent-danger);
    color: #ffffff;
    box-shadow: 0 0 20px rgba(211, 5, 84, 0.3);
    transform: translateY(-2px);
  }

  .close-button:active {
    transform: translateY(0);
  }

  .step-indicator {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: var(--spacing-sm);
  }

  .step-dot {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 600;
    background: var(--theme-bg-secondary);
    color: var(--text-muted);
    border: 2px solid var(--border-primary);
    transition: all 0.2s ease;
  }

  .step-dot.current {
    background: var(--accent-primary);
    color: var(--text-inverse);
    border-color: var(--accent-primary);
    box-shadow: 0 0 15px var(--glow-primary);
  }

  .step-dot.active {
    background: var(--accent-success);
    color: var(--text-inverse);
    border-color: var(--accent-success);
    box-shadow: 0 0 15px rgba(34, 197, 94, 0.4);
  }

  .step-line {
    flex: 1;
    height: 2px;
    background: var(--border-primary);
    max-width: 60px;
    transition: background 0.2s ease;
  }

  .step-line.active {
    background: var(--accent-success);
    box-shadow: 0 0 10px rgba(34, 197, 94, 0.3);
  }

  .error-banner {
    padding: var(--spacing-md);
    background: rgba(211, 5, 84, 0.1);
    border: 1px solid var(--accent-danger);
    border-radius: var(--radius-md);
    color: var(--accent-danger);
    margin-bottom: var(--spacing-lg);
    text-align: center;
    font-weight: 500;
    box-shadow: 0 0 20px rgba(211, 5, 84, 0.2);
  }

  .loading-state,
  .empty-state {
    padding: var(--spacing-xl);
    text-align: center;
    color: var(--text-secondary);
  }

  .form-step {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xl);
  }

  .step-title {
    font-family: var(--font-primary);
    font-size: var(--text-xl);
    font-weight: 700;
    color: var(--text-primary);
  }

  .package-selector {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-md);
  }

  .package-option {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: var(--spacing-lg);
    background: var(--theme-bg-secondary);
    backdrop-filter: blur(8px) saturate(150%);
    -webkit-backdrop-filter: blur(8px) saturate(150%);
    border: 2px solid var(--border-primary);
    border-radius: var(--radius-md);
    cursor: pointer;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    text-align: left;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }

  .package-option:hover {
    border-color: var(--accent-primary);
    background: var(--theme-bg-elevated);
    box-shadow: 0 4px 12px rgba(0, 147, 247, 0.2), 0 0 15px var(--glow-primary);
    transform: translateY(-2px);
  }

  .package-option.selected {
    border-color: var(--accent-primary);
    background: rgba(0, 147, 247, 0.1);
    box-shadow: 0 0 20px var(--glow-primary);
  }

  .package-info {
    flex: 1;
  }

  .package-name {
    font-size: var(--text-lg);
    font-weight: 600;
    color: var(--text-primary);
    margin: 0 0 var(--spacing-xs) 0;
  }

  .package-description {
    font-size: var(--text-sm);
    color: var(--text-secondary);
    margin: 0 0 var(--spacing-sm) 0;
  }

  .package-price {
    font-size: var(--text-xl);
    font-weight: 700;
    color: var(--accent-primary);
  }

  .selected-indicator {
    font-size: 24px;
    color: var(--accent-success);
    margin-left: var(--spacing-md);
  }

  .quantity-selector {
    padding: var(--spacing-lg);
    background: rgba(74, 119, 212, 0.05);
    backdrop-filter: blur(8px) saturate(150%);
    -webkit-backdrop-filter: blur(8px) saturate(150%);
    border: 1px solid rgba(74, 119, 212, 0.2);
    border-radius: var(--radius-md);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }

  .quantity-controls {
    display: flex;
    align-items: center;
    gap: var(--spacing-md);
    margin: var(--spacing-md) 0;
  }

  .quantity-button {
    width: 48px;
    height: 48px;
    border-radius: 12px;
    border: 2px solid var(--border-primary);
    background: var(--theme-bg-elevated);
    color: var(--text-primary);
    font-size: var(--text-xl);
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  }

  .quantity-button:hover:not(:disabled) {
    background: var(--accent-primary);
    color: var(--text-inverse);
    border-color: var(--accent-primary);
    box-shadow: 0 4px 8px rgba(0, 147, 247, 0.3), 0 0 15px var(--glow-primary);
    transform: translateY(-2px);
  }

  .quantity-button:active:not(:disabled) {
    transform: translateY(0);
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1), inset 0 2px 4px rgba(0, 0, 0, 0.1);
  }

  .quantity-button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .quantity-input {
    width: 80px;
    padding: var(--spacing-sm);
    text-align: center;
    border: 1px solid var(--border-primary);
    border-radius: 12px;
    background: var(--input-bg);
    color: var(--text-primary);
    font-size: 18px;
    font-weight: 600;
    height: 50px;
    transition: all 0.2s ease;
  }

  .quantity-input:focus {
    background-color: var(--input-bg-focus);
    border-color: var(--accent-primary);
    box-shadow: 0 0 15px rgba(0, 147, 247, 0.2);
    outline: 0;
  }

  .subtotal-preview {
    font-size: var(--text-lg);
    font-weight: 600;
    color: var(--text-primary);
    text-align: center;
  }

  .form-fields {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-lg);
  }

  /* Input Wrapper - Estilo Admin Forms */
  .input-wrapper {
    position: relative;
    width: 100%;
    margin-bottom: 16px;
  }

  /* Inputs simplificados - estilo moderno pero simple */
  .input {
    width: 100%;
    margin-bottom: 0;
    background-color: var(--input-bg);
    border-radius: 12px;
    border: 1px solid var(--border-primary);
    box-sizing: border-box;
    color: var(--text-primary);
    font-size: 18px;
    height: 50px;
    outline: 0;
    padding: 0 20px;
    font-family: var(--font-body, sans-serif);
    transition: all 0.2s ease;
  }

  .input:focus {
    background-color: var(--input-bg-focus);
    border-color: var(--accent-primary);
  }

  .input:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .input::placeholder {
    color: var(--text-muted);
    opacity: 1;
  }

  .label {
    font-weight: 600;
    font-size: var(--text-base);
    color: var(--text-primary);
    margin-bottom: 8px;
    display: block;
  }

  .summary-box {
    padding: var(--spacing-lg);
    background: var(--theme-bg-secondary);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
    margin-top: var(--spacing-md);
  }

  .summary-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--spacing-sm);
  }

  .summary-row.total {
    margin-top: var(--spacing-md);
    padding-top: var(--spacing-md);
    border-top: 2px solid var(--border-primary);
    font-weight: 700;
    font-size: var(--text-lg);
  }

  .summary-label {
    color: var(--text-secondary);
  }

  .summary-value {
    color: var(--text-primary);
    font-weight: 600;
  }

  .summary-row.total .summary-value {
    color: var(--accent-primary);
    font-size: var(--text-xl);
  }

  .package-items-preview {
    padding: var(--spacing-md);
    background: var(--theme-bg-secondary);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
    margin-top: var(--spacing-md);
  }

  .package-items-preview .items-label {
    font-size: var(--text-sm);
    font-weight: 600;
    color: var(--text-secondary);
    margin: 0 0 var(--spacing-sm) 0;
  }

  .package-items-preview .items-list {
    list-style: none;
    padding: 0;
    margin: 0;
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xs);
  }

  .package-items-preview .item-entry {
    font-size: var(--text-sm);
    color: var(--text-primary);
    padding: var(--spacing-xs) var(--spacing-sm);
    background: var(--theme-bg-elevated);
    border-radius: var(--radius-sm);
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .package-items-preview .item-quantity {
    font-size: var(--text-xs);
    color: var(--text-secondary);
    margin-left: var(--spacing-xs);
  }

  .step-actions {
    display: flex;
    gap: 12px;
    justify-content: flex-end;
    margin-top: 32px;
    padding-top: 0;
    border-top: none;
  }

  /* Botones con estilo Admin Forms */
  .btn {
    background-color: var(--accent-primary, #08d);
    border-radius: 12px;
    border: 0;
    box-sizing: border-box;
    color: #eee;
    cursor: pointer;
    font-size: 18px;
    height: 50px;
    text-align: center;
    width: auto;
    min-width: 120px;
    padding: 0 24px;
    font-family: sans-serif;
    font-weight: 600;
    transition: background-color 0.2s ease;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
  }

  .btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .btn-primary {
    background: linear-gradient(to bottom, #6eb6de, #4a77d4);
    background-color: #4a77d4;
    border-color: #3762bc;
    color: #ffffff;
    text-shadow: 0 -1px 0 rgba(0, 0, 0, 0.25);
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.2), 0 1px 2px rgba(0, 0, 0, 0.2);
  }

  .btn-primary:hover:not(:disabled) {
    background: linear-gradient(to bottom, #7fc3e5, #5a87e4);
    background-color: #5a87e4;
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.2), 0 2px 4px rgba(0, 0, 0, 0.3);
  }

  .btn-primary:active:not(:disabled) {
    background: linear-gradient(to bottom, #4a77d4, #3762bc);
    background-color: #3762bc;
    box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.2);
  }

  .btn-secondary {
    background: linear-gradient(to bottom, #f5f5f5, #e6e6e6);
    background-color: #e6e6e6;
    border-color: #d4d4d4;
    color: #333333;
    text-shadow: 0 1px 1px rgba(255, 255, 255, 0.75);
  }

  .btn-secondary:hover:not(:disabled) {
    background: linear-gradient(to bottom, #ffffff, #f5f5f5);
    background-color: #f5f5f5;
    border-color: #d4d4d4;
  }

  .btn-secondary:active:not(:disabled) {
    background: linear-gradient(to bottom, #e6e6e6, #d4d4d4);
    background-color: #d4d4d4;
    box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.1);
  }

  .confirmation {
    text-align: center;
  }

  .success-icon {
    font-size: 64px;
    margin-bottom: var(--spacing-lg);
  }

  .confirmation-details {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-md);
    padding: var(--spacing-lg);
    background: var(--theme-bg-secondary);
    border-radius: var(--radius-md);
    margin: var(--spacing-lg) 0;
  }

  .detail-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .detail-label {
    color: var(--text-secondary);
    font-weight: 600;
  }

  .detail-value {
    color: var(--text-primary);
    font-weight: 700;
  }

  @media (max-width: 768px) {
    .sale-form-container {
      padding: var(--spacing-md);
    }

    .step-actions {
      flex-direction: column;
    }

    .step-actions .btn {
      width: 100%;
      min-height: 44px; /* Minimum touch target size for accessibility */
    }

    .quantity-controls {
      flex-wrap: wrap;
      justify-content: center;
    }

    .quantity-button {
      min-width: 48px;
      min-height: 48px;
    }

    .package-option {
      padding: var(--spacing-md);
    }
  }

  /* Prevent hover transform issues on touch devices */
  @media (hover: none) and (pointer: coarse) {
    .package-option:hover {
      transform: none;
    }

    .quantity-button:hover:not(:disabled) {
      transform: none;
    }

    .close-button:hover {
      transform: none;
    }

    .btn-primary:hover:not(:disabled),
    .btn-secondary:hover:not(:disabled) {
      /* Maintain gradient but remove any transform effects */
      transform: none;
    }
  }
</style>

