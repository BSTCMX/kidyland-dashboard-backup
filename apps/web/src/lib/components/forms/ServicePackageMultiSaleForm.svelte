<script lang="ts">
  /**
   * ServicePackageMultiSaleForm component - Multi-package sale form for Recepcion.
   * 
   * Handles complete service package sale creation flow with multiple packages:
   * 1. Package selection (multi-select)
   * 2. Child and payer information (with scheduled date)
   * 3. Payment details
   * 4. Confirmation
   * 
   * Based on PackageSaleForm.svelte, adapted for multiple package sales.
   * Maintains all fields from PackageSaleForm: scheduledDate, childName, childAge, discountCents.
   */
  import { onMount } from "svelte";
  import { user } from "@kidyland/utils";
  import type { Package } from "@kidyland/shared/types";
  import { fetchAllPackages, packagesAdminStore } from "$lib/stores/packages-admin";
  import { fetchAllServices, servicesAdminStore } from "$lib/stores/services-admin";
  import { createPackageSale, salesStore } from "$lib/stores/sales";
  import { filterActiveServicePackages } from "$lib/utils/package-filters";
  import PackageMultiSelector from "$lib/components/selectors/PackageMultiSelector.svelte";
  import PaymentForm from "./PaymentForm.svelte";
  import { printTicket } from "$lib/stores/sales-history";

  // Form state
  let currentStep = 1;
  const totalSteps = 4; // Added step for child info and scheduled date

  // Package selection (cart)
  let selectedItems: Array<{ package: Package; quantity: number }> = [];
  let packages: Package[] = [];
  let services: any[] = [];

  // Date selection for package scheduling (shared for all packages in the sale)
  let selectedDate = "";

  // Child and payer info
  let childName = "";
  let childAge: number | undefined = undefined;
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

  // Get today's date in YYYY-MM-DD format for min date (using local timezone)
  // Use local date methods to avoid timezone issues
  function getTodayLocalDate(): string {
    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const day = String(now.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  }
  
  const today = getTodayLocalDate();
  // Max date: 1 year from today
  const maxDate = new Date();
  maxDate.setFullYear(maxDate.getFullYear() + 1);
  const maxDateStr = `${maxDate.getFullYear()}-${String(maxDate.getMonth() + 1).padStart(2, '0')}-${String(maxDate.getDate()).padStart(2, '0')}`;
  
  // Calculate totals
  $: subtotalCents = selectedItems.reduce(
    (total, item) => total + item.package.price_cents * item.quantity,
    0
  );
  $: totalCents = subtotalCents - discountCents;

  $: canProceedStep1 = selectedItems.length > 0 && selectedDate.trim() !== "";
  $: canProceedStep2 = childName.trim() && payerName.trim();
  $: canProceedStep3 =
    paymentMethod === "cash"
      ? cashReceivedCents !== undefined && cashReceivedCents >= totalCents
      : paymentMethod === "card"
        ? cardAuthCode.trim() !== ""
        : paymentMethod === "transfer"
          ? transferReference.trim() !== ""
          : false;

  onMount(async () => {
    // Initialize selectedDate to today (only if not already set)
    // Use local date to avoid timezone issues
    if (!selectedDate) {
      selectedDate = today;
    }

    const currentUser = $user;
    if (!currentUser?.sucursal_id) {
      error = "No sucursal assigned";
      return;
    }

    loading = true;
    try {
      // Load packages and services in parallel
      // For services: super_admin and admin_viewer load all services (no filter)
      // to ensure all service names are available for package items
      const isSuperAdminOrAdminViewer = currentUser.role === "super_admin" || currentUser.role === "admin_viewer";
      const servicesPromise = isSuperAdminOrAdminViewer 
        ? fetchAllServices(undefined) // Load all services for super_admin/admin_viewer
        : fetchAllServices(currentUser.sucursal_id); // Filter by sucursal_id for other roles
      
      await Promise.all([
        fetchAllPackages(currentUser.sucursal_id),
        servicesPromise
      ]);
      
      packages = filterActiveServicePackages($packagesAdminStore.list);
      services = $servicesAdminStore.list;
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
      // Each sale includes: scheduledDate, childName, childAge, discountCents (per package)
      const salePromises = selectedItems.map((item) => {
        // Calculate discount per package (proportional to package price)
        const packageSubtotal = item.package.price_cents * item.quantity;
        const packageDiscount = discountCents > 0 
          ? Math.round((packageSubtotal / subtotalCents) * discountCents)
          : 0;

        const formData = {
          packageId: item.package.id,
          quantity: item.quantity,
          scheduledDate: selectedDate || undefined, // Shared scheduled date for all packages
          childName: childName.trim(),
          childAge,
          payerName: payerName.trim(),
          payerPhone: payerPhone.trim() || undefined,
          paymentMethod,
          cashReceivedCents,
          cardAuthCode: cardAuthCode.trim() || undefined,
          transferReference: transferReference.trim() || undefined,
          discountCents: packageDiscount, // Proportional discount per package
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
    selectedDate = today;
    childName = "";
    childAge = undefined;
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
    <h2 class="form-title">Nueva Venta - Paquetes de Servicios</h2>
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
          products={services}
          bind:selectedItems
          {error}
        />
        
        {#if selectedItems.length > 0}
          <div class="date-selector">
            <label for="package-date" class="label">
              Fecha del Paquete <span class="required">*</span>
            </label>
            <input
              id="package-date"
              type="date"
              class="input"
              bind:value={selectedDate}
              min={today}
              max={maxDateStr}
              required
            />
            <p class="help-text">Seleccione la fecha para la cual se programan los paquetes</p>
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
    <!-- Step 2: Child and Payer Info -->
    <div class="form-step">
      <h3 class="step-title">2. Información del Cliente</h3>
      <div class="form-fields">
        <div class="input-wrapper">
          <label for="child-name" class="label">
            Nombre del Niño <span class="required">*</span>
          </label>
          <input
            id="child-name"
            type="text"
            class="input"
            bind:value={childName}
            placeholder="Nombre del niño"
            required
          />
        </div>
        <div class="input-wrapper">
          <label for="child-age" class="label">Edad (opcional)</label>
          <input
            id="child-age"
            type="number"
            class="input"
            min="0"
            max="18"
            step="1"
            placeholder="Edad (opcional)"
            value={childAge || ""}
            on:input={(e) => {
              const value = parseInt(e.target.value, 10);
              childAge = isNaN(value) ? undefined : value;
            }}
          />
        </div>
        <div class="input-wrapper">
          <label for="payer-name" class="label">
            Nombre del Adulto Responsable <span class="required">*</span>
          </label>
          <input
            id="payer-name"
            type="text"
            class="input"
            bind:value={payerName}
            placeholder="Nombre completo"
            required
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
        {#if totalCents > 0}
          <div class="input-wrapper">
            <label for="discount" class="label">Descuento (opcional)</label>
            <input
              id="discount"
              type="number"
              class="input"
              step="0.01"
              min="0"
              placeholder="0.00"
              value={discountCents ? discountCents / 100 : ""}
              on:input={(e) => {
                const value = parseFloat(e.target.value) || 0;
                discountCents = Math.round(value * 100);
              }}
            />
          </div>
        {/if}
        <div class="summary-box">
          <div class="summary-row">
            <span class="summary-label">Subtotal:</span>
            <span class="summary-value">{formatPrice(subtotalCents)}</span>
          </div>
          {#if discountCents > 0}
            <div class="summary-row">
              <span class="summary-label">Descuento:</span>
              <span class="summary-value">-{formatPrice(discountCents)}</span>
            </div>
          {/if}
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
          {#if saleResponse.multiple_sales}
            <div class="detail-row">
              <span class="detail-label">Total de Ventas:</span>
              <span class="detail-value">{saleResponse.total_sales}</span>
            </div>
          {/if}
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
    max-width: 800px;
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

  .date-selector {
    margin-top: var(--spacing-lg);
    margin-bottom: var(--spacing-lg);
    position: relative;
  }

  .date-selector .input {
    width: 100%;
    height: 50px;
    font-size: 18px;
    border-radius: 12px;
    padding: 0 20px;
    padding-right: 50px;
    background-color: var(--theme-bg-elevated);
    border: 2px solid var(--border-primary);
    color: var(--text-primary);
    transition: all 0.2s ease;
    cursor: pointer;
    font-weight: 500;
  }

  .date-selector .input:focus {
    outline: none;
    background-color: var(--theme-bg-card);
    border-color: var(--accent-primary);
    box-shadow: 0 0 0 3px rgba(0, 147, 247, 0.1), 0 0 15px var(--glow-primary);
  }

  .help-text {
    font-size: var(--text-sm);
    color: var(--text-secondary);
    margin-top: var(--spacing-xs);
    font-style: italic;
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

  .required {
    color: var(--accent-danger);
  }

  .summary-box {
    padding: var(--spacing-lg);
    background: rgba(74, 119, 212, 0.05);
    backdrop-filter: blur(8px) saturate(150%);
    -webkit-backdrop-filter: blur(8px) saturate(150%);
    border: 1px solid rgba(74, 119, 212, 0.2);
    border-radius: var(--radius-md);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    margin-top: var(--spacing-md);
  }

  .summary-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: var(--spacing-sm) 0;
  }

  .summary-row.total {
    border-top: 2px solid var(--border-primary);
    margin-top: var(--spacing-sm);
    padding-top: var(--spacing-md);
    font-weight: 700;
    font-size: var(--text-lg);
  }

  .summary-label {
    color: var(--text-secondary);
    font-weight: 600;
  }

  .summary-value {
    color: var(--text-primary);
    font-weight: 700;
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

  .step-actions :global(button) {
    border-radius: 12px !important;
    border: 0 !important;
    box-sizing: border-box !important;
    cursor: pointer !important;
    font-size: 18px !important;
    height: 50px !important;
    text-align: center !important;
    width: auto !important;
    min-width: 120px !important;
    padding: 0 24px !important;
    font-family: sans-serif !important;
    font-weight: 600 !important;
    transition: background-color 0.2s ease !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    gap: 8px !important;
  }

  .step-actions :global(button):disabled {
    opacity: 0.6 !important;
    cursor: not-allowed !important;
  }

  .step-actions :global(button.bg-blue-600),
  .step-actions :global(button[class*="bg-blue"]) {
    background: linear-gradient(to bottom, #6eb6de, #4a77d4) !important;
    background-color: #4a77d4 !important;
    border-color: #3762bc !important;
    color: #ffffff !important;
    text-shadow: 0 -1px 0 rgba(0, 0, 0, 0.25) !important;
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.2), 0 1px 2px rgba(0, 0, 0, 0.2) !important;
  }

  .step-actions :global(button.bg-blue-600:hover:not(:disabled)),
  .step-actions :global(button[class*="bg-blue"]:hover:not(:disabled)) {
    background: linear-gradient(to bottom, #7fc3e5, #5a87e4) !important;
    background-color: #5a87e4 !important;
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.2), 0 2px 4px rgba(0, 0, 0, 0.3) !important;
  }

  .step-actions :global(button.bg-gray-200),
  .step-actions :global(button[class*="bg-gray"]) {
    background: linear-gradient(to bottom, #f5f5f5, #e6e6e6) !important;
    background-color: #e6e6e6 !important;
    border-color: #d4d4d4 !important;
    color: #333333 !important;
    text-shadow: 0 1px 1px rgba(255, 255, 255, 0.75) !important;
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

    .step-actions :global(button) {
      width: 100% !important;
      min-height: 44px !important;
    }
  }
</style>

