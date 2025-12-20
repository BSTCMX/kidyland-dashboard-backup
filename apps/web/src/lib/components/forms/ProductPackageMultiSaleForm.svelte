<script lang="ts">
  /**
   * ProductPackageMultiSaleForm component - Multi-package sale form for KidiBar.
   * 
   * Handles complete product package sale creation flow with multiple packages:
   * 1. Package selection (multi-select)
   * 2. Payer information
   * 3. Payment details
   * 4. Confirmation
   * 
   * Based on ProductSaleForm.svelte, adapted for multiple package sales.
   */
  import { onMount } from "svelte";
  import { user } from "@kidyland/utils";
  import type { Package } from "@kidyland/shared/types";
  import { fetchAllPackages, packagesAdminStore } from "$lib/stores/packages-admin";
  import { fetchProducts, productsStore } from "$lib/stores/products";
  import { createPackageSale, salesStore } from "$lib/stores/sales";
  import { filterActiveProductPackages } from "$lib/utils/package-filters";
  import PackageMultiSelector from "$lib/components/selectors/PackageMultiSelector.svelte";
  import PaymentForm from "./PaymentForm.svelte";
  import { printTicket } from "$lib/stores/sales-history";

  // Form state
  let currentStep = 1;
  const totalSteps = 3;

  // Package selection (cart)
  let selectedItems: Array<{ package: Package; quantity: number }> = [];
  let packages: Package[] = [];
  let products: any[] = [];

  // Payer info
  let payerName = "";
  let payerPhone = "";

  // Payment
  let paymentMethod: "cash" | "card" | "transfer" = "cash";
  let cashReceivedCents: number | undefined = undefined;
  let cardAuthCode = "";
  let transferReference = "";
  let discountCents = 0;

  // State
  let loading = false;
  let printing = false;
  let error: string | null = null;
  let saleResponse: any = null;

  // Calculate totals
  $: subtotalCents = selectedItems.reduce(
    (total, item) => total + item.package.price_cents * item.quantity,
    0
  );
  $: totalCents = subtotalCents - discountCents;

  $: canProceedStep1 = selectedItems.length > 0;
  $: canProceedStep2 = true; // Payer name is optional for quick sales
  $: canProceedStep3 =
    paymentMethod === "cash"
      ? cashReceivedCents !== undefined && cashReceivedCents >= totalCents
      : paymentMethod === "card"
        ? cardAuthCode.trim() !== ""
        : paymentMethod === "transfer"
          ? transferReference.trim() !== ""
          : false;

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
      
      packages = filterActiveProductPackages($packagesAdminStore.list);
      products = $productsStore.list;
    } catch (e: any) {
      error = e.message || "Error loading data";
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
    if (!currentUser?.sucursal_id || selectedItems.length === 0) {
      error = "Missing required information";
      return;
    }

    loading = true;
    error = null;

    try {
      // Create multiple package sales - one sale per package
      // This maintains backward compatibility with the backend
      const salePromises = selectedItems.map((item) => {
        const formData = {
          packageId: item.package.id,
          quantity: item.quantity,
          payerName: payerName.trim() || undefined,
          payerPhone: payerPhone.trim() || undefined,
          paymentMethod,
          cashReceivedCents,
          cardAuthCode: cardAuthCode.trim() || undefined,
          transferReference: transferReference.trim() || undefined,
          discountCents: 0, // Discount is per package, not per sale
        };

        return createPackageSale(
          formData,
          currentUser.sucursal_id,
          currentUser.id,
          item.package.price_cents
        );
      });

      // Wait for all sales to complete
      const responses = await Promise.all(salePromises);
      
      // Use the first response for confirmation (all should have same structure)
      saleResponse = responses[0];
      if (responses.length > 1) {
        saleResponse.multiple_sales = true;
        saleResponse.total_sales = responses.length;
      }

      // Move to confirmation step
      currentStep = 4;
    } catch (e: any) {
      error = e.message || "Error creating sale";
    } finally {
      loading = false;
    }
  }

  function resetForm() {
    currentStep = 1;
    selectedItems = [];
    payerName = "";
    payerPhone = "";
    paymentMethod = "cash";
    cashReceivedCents = undefined;
    cardAuthCode = "";
    transferReference = "";
    discountCents = 0;
    error = null;
    saleResponse = null;
  }

  function formatPrice(cents: number): string {
    return `$${(cents / 100).toFixed(2)}`;
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
</script>

<div class="sale-form-container">
  <div class="form-header">
    <h2 class="form-title">Nueva Venta - Paquetes</h2>
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

  {#if currentStep === 1}
    <!-- Step 1: Package Selection -->
    <div class="form-step">
      <h3 class="step-title">1. Seleccionar Paquetes</h3>
      {#if loading}
        <div class="loading-state">Cargando paquetes...</div>
      {:else}
        <PackageMultiSelector
          {packages}
          {products}
          bind:selectedItems
          {error}
        />
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
            Nombre del Cliente
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
        <div class="summary-box">
          <div class="summary-row">
            <span class="summary-label">Subtotal:</span>
            <span class="summary-value">{formatPrice(subtotalCents)}</span>
          </div>
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
          {#if saleResponse.multiple_sales}
            <div class="detail-row">
              <span class="detail-label">Ventas creadas:</span>
              <span class="detail-value">{saleResponse.total_sales}</span>
            </div>
          {/if}
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

  .form-title {
    font-family: var(--font-primary);
    font-size: var(--text-2xl);
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: var(--spacing-lg);
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
  }

  .step-dot.active {
    background: var(--accent-success);
    color: var(--text-inverse);
    border-color: var(--accent-success);
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
  }

  .error-banner {
    padding: var(--spacing-md);
    background: rgba(211, 5, 84, 0.1);
    border: 1px solid var(--accent-danger);
    border-radius: var(--radius-md);
    color: var(--accent-danger);
    margin-bottom: var(--spacing-lg);
  }

  .loading-state {
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

  .form-fields {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-lg);
  }

  .input-wrapper {
    position: relative;
    width: 100%;
    margin-bottom: 16px;
  }

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

  .step-actions {
    display: flex;
    gap: 12px;
    justify-content: flex-end;
    margin-top: 32px;
    padding-top: 0;
    border-top: none;
  }

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

  .confirmation {
    text-align: center;
    align-items: center;
  }

  .success-icon {
    font-size: 64px;
    margin-bottom: var(--spacing-md);
  }

  .confirmation-details {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-md);
    padding: var(--spacing-lg);
    background: var(--theme-bg-secondary);
    border-radius: var(--radius-md);
    text-align: left;
  }

  .detail-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .detail-label {
    font-weight: 600;
    color: var(--text-secondary);
  }

  .detail-value {
    font-family: var(--font-mono);
    color: var(--text-primary);
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
      min-height: 44px;
    }
  }

  @media (hover: none) and (pointer: coarse) {
    .btn-primary:hover:not(:disabled),
    .btn-secondary:hover:not(:disabled) {
      /* Maintain gradient but remove any transform effects */
    }
  }
</style>

