<script lang="ts">
  /**
   * SaleForm component - Main sale form with step-by-step flow.
   * 
   * Handles complete sale creation flow:
   * 1. Service selection
   * 2. Child and payer information
   * 3. Payment details
   * 4. Confirmation
   */
  import { onMount } from "svelte";
  import { user } from "@kidyland/utils";
  import type { Service } from "@kidyland/shared/types";
  import { fetchServices, activeServices } from "$lib/stores/services";
  import { createServiceSale, calculateServicePrice, salesStore } from "$lib/stores/sales";
  import { printTicket } from "$lib/stores/sales-history";
  import ServiceSelector from "$lib/components/selectors/ServiceSelector.svelte";
  import PaymentForm from "./PaymentForm.svelte";

  // Form state
  let currentStep = 1;
  const totalSteps = 3;

  // Service selection
  let selectedServiceId = "";
  let selectedDuration = 0;

  // Children info (multi-child support)
  interface ChildInfo {
    name: string;
    age?: number;
  }
  let children: ChildInfo[] = [{ name: "", age: undefined }];
  let payerName = "";

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

  // Use reactive store directly for automatic synchronization
  $: selectedService = $activeServices.find((s) => s.id === selectedServiceId);
  $: unitPriceCents = selectedService && selectedDuration
    ? calculateServicePrice(selectedService, selectedDuration)
    : 0;
  $: totalCents = unitPriceCents * children.length; // Price per slot * number of children

  $: canProceedStep1 = selectedServiceId && selectedDuration > 0;
  $: canProceedStep2 = children.length > 0 
    && children.every(child => child.name.trim() && (!child.age || child.age > 0))
    && payerName.trim();
  $: canProceedStep3 =
    paymentMethod === "cash"
      ? cashReceivedCents !== undefined && cashReceivedCents >= totalCents
      : paymentMethod === "card"
        ? cardAuthCode.trim() !== ""
        : paymentMethod === "transfer"
          ? transferReference.trim() !== ""
          : false;

  // Load services on mount, but use reactive store for automatic updates
  onMount(async () => {
    const currentUser = $user;
    if (!currentUser?.sucursal_id) {
      error = "No sucursal assigned";
      return;
    }

    loading = true;
    try {
      await fetchServices(currentUser.sucursal_id);
      // Services are now automatically synced via $activeServices reactive store
    } catch (e: any) {
      error = e.message || "Error loading services";
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
    if (!currentUser?.sucursal_id || !selectedService) {
      error = "Missing required information";
      return;
    }

    loading = true;
    error = null;

    try {
      // Filter out empty children and prepare children array
      const validChildren = children
        .filter(child => child.name.trim())
        .map(child => ({
          name: child.name.trim(),
          age: child.age && child.age > 0 ? child.age : undefined,
        }));

      if (validChildren.length === 0) {
        error = "Debe agregar al menos un niño";
        return;
      }

      const formData = {
        serviceId: selectedServiceId,
        durationMinutes: selectedDuration,
        children: validChildren,
        payerName: payerName.trim(),
        paymentMethod,
        cashReceivedCents,
        cardAuthCode: cardAuthCode.trim() || undefined,
        transferReference: transferReference.trim() || undefined,
      };

      saleResponse = await createServiceSale(
        formData,
        currentUser.sucursal_id,
        currentUser.id,
        selectedService
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

  function addChild() {
    children = [...children, { name: "", age: undefined }];
  }

  function removeChild(index: number) {
    if (children.length > 1) {
      children = children.filter((_, i) => i !== index);
    }
  }

  function resetForm() {
    currentStep = 1;
    selectedServiceId = "";
    selectedDuration = 0;
    children = [{ name: "", age: undefined }];
    payerName = "";
    paymentMethod = "cash";
    cashReceivedCents = undefined;
    cardAuthCode = "";
    transferReference = "";
    error = null;
    saleResponse = null;
    printing = false;
  }
</script>

<div class="sale-form-container">
  <div class="form-header">
    <h2 class="form-title">Nueva Venta - Servicio</h2>
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
    <!-- Step 1: Service Selection -->
    <div class="form-step">
      <h3 class="step-title">1. Seleccionar Servicio</h3>
      <ServiceSelector
        bind:selectedServiceId
        bind:selectedDuration
        services={$activeServices}
        {error}
      />
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
    <!-- Step 2: Children and Payer Info -->
    <div class="form-step">
      <h3 class="step-title">2. Información del Cliente</h3>
      <div class="form-fields">
        <div class="children-section">
          <div class="section-header">
            <label class="label">
              Niños <span class="required">*</span>
            </label>
            <button
              type="button"
              class="btn btn-secondary btn-small"
              on:click={addChild}
            >
              + Agregar Niño
            </button>
          </div>
          {#each children as child, index}
            <div class="child-row">
              <div class="input-wrapper">
                <input
                  type="text"
                  class="input"
                  placeholder="Nombre del niño"
                  bind:value={child.name}
                  required
                />
              </div>
              <div class="input-wrapper">
                <input
                  type="number"
                  class="input"
                  min="1"
                  max="18"
                  step="1"
                  placeholder="Edad (opcional)"
                  value={child.age || ""}
                  on:input={(e) => {
                    const value = parseInt(e.target.value, 10);
                    child.age = isNaN(value) ? undefined : value;
                  }}
                />
              </div>
              {#if children.length > 1}
                <button
                  type="button"
                  class="btn btn-danger btn-small"
                  on:click={() => removeChild(index)}
                  aria-label="Eliminar niño"
                >
                  ×
                </button>
              {/if}
            </div>
          {/each}
          <div class="price-preview">
            <span class="price-label">Precio por niño:</span>
            <span class="price-value">${(unitPriceCents / 100).toFixed(2)}</span>
          </div>
          <div class="total-preview">
            <span class="total-label">Total ({children.length} {children.length === 1 ? 'niño' : 'niños'}):</span>
            <span class="total-value">${(totalCents / 100).toFixed(2)}</span>
          </div>
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
          {#if saleResponse.timer_id}
            <div class="detail-row">
              <span class="detail-label">Timer Creado:</span>
              <span class="detail-value">{saleResponse.timer_id}</span>
            </div>
          {/if}
          <div class="detail-row">
            <span class="detail-label">Total:</span>
            <span class="detail-value">${(totalCents / 100).toFixed(2)}</span>
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

  .input.error {
    border: 2px solid var(--accent-danger, #dc2f55);
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

  .required {
    color: var(--accent-danger);
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

  .children-section {
    background: rgba(74, 119, 212, 0.05);
    border: 1px solid rgba(74, 119, 212, 0.2);
    border-radius: var(--radius-md);
    padding: var(--spacing-lg);
    margin-bottom: var(--spacing-lg);
  }

  .section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--spacing-md);
  }

  .child-row {
    display: flex;
    gap: var(--spacing-md);
    align-items: flex-start;
    margin-bottom: var(--spacing-md);
  }

  .child-row .input-wrapper {
    flex: 1;
    margin-bottom: 0;
  }

  .btn-small {
    min-width: auto;
    height: 40px;
    font-size: 14px;
    padding: 0 16px;
  }

  .btn-danger {
    background: linear-gradient(to bottom, #dc2f55, #c01e3f);
    color: #ffffff;
  }

  .btn-danger:hover:not(:disabled) {
    background: linear-gradient(to bottom, #e8456a, #d32a4f);
  }

  .price-preview {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: var(--spacing-sm) 0;
    border-top: 1px dashed rgba(74, 119, 212, 0.3);
    margin-top: var(--spacing-md);
  }

  .price-label {
    font-size: var(--text-sm);
    color: var(--text-muted);
  }

  .price-value {
    font-size: var(--text-base);
    font-weight: 600;
    color: var(--text-primary);
  }

  .total-preview {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: var(--spacing-md) 0;
    border-top: 2px solid rgba(74, 119, 212, 0.3);
    margin-top: var(--spacing-sm);
  }

  .total-label {
    font-size: var(--text-base);
    font-weight: 600;
    color: var(--text-primary);
  }

  .total-value {
    font-size: var(--text-lg);
    font-weight: 700;
    color: var(--accent-primary);
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

  /* Responsive: Mobile */
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
  }

  /* Prevent hover transform issues on touch devices */
  @media (hover: none) and (pointer: coarse) {
    .step-actions .btn-primary:hover:not(:disabled),
    .step-actions .btn-secondary:hover:not(:disabled) {
      /* Maintain gradient but remove any transform effects */
    }
  }
</style>

