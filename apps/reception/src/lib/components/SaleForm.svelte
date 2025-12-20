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
  import { fetchServices, activeServices } from "../stores/services";
  import { createSale, calculateServicePrice, salesStore } from "../stores/sales";
  import ServiceSelector from "./ServiceSelector.svelte";
  import PaymentForm from "./PaymentForm.svelte";
  import { Button, Input } from "@kidyland/ui";

  // Form state
  let currentStep = 1;
  const totalSteps = 3;

  // Service selection
  let selectedServiceId = "";
  let selectedDuration = 0;
  let services: Service[] = [];

  // Child and payer info
  let childName = "";
  let payerName = "";
  let payerPhone = "";

  // Payment
  let paymentMethod: "cash" | "card" | "mixed" = "cash";
  let cashReceivedCents: number | undefined = undefined;
  let cardAuthCode = "";
  let discountCents = 0;

  // State
  let loading = false;
  let error: string | null = null;
  let saleResponse: any = null;

  $: selectedService = services.find((s) => s.id === selectedServiceId);
  $: totalCents =
    selectedService && selectedDuration
      ? calculateServicePrice(selectedService, selectedDuration) - discountCents
      : 0;

  $: canProceedStep1 = selectedServiceId && selectedDuration > 0;
  $: canProceedStep2 = childName.trim() && payerName.trim();
  $: canProceedStep3 =
    paymentMethod === "cash"
      ? cashReceivedCents !== undefined && cashReceivedCents >= totalCents
      : paymentMethod === "card"
        ? cardAuthCode.trim() !== ""
        : true; // Mixed can proceed if at least one payment method is filled

  onMount(async () => {
    const currentUser = $user;
    if (!currentUser?.sucursal_id) {
      error = "No sucursal assigned";
      return;
    }

    loading = true;
    try {
      await fetchServices(currentUser.sucursal_id);
      services = $activeServices;
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
      const formData = {
        serviceId: selectedServiceId,
        durationMinutes: selectedDuration,
        childName: childName.trim(),
        payerName: payerName.trim(),
        payerPhone: payerPhone.trim() || undefined,
        paymentMethod,
        cashReceivedCents,
        cardAuthCode: cardAuthCode.trim() || undefined,
        discountCents,
      };

      saleResponse = await createSale(
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

  function resetForm() {
    currentStep = 1;
    selectedServiceId = "";
    selectedDuration = 0;
    childName = "";
    payerName = "";
    payerPhone = "";
    paymentMethod = "cash";
    cashReceivedCents = undefined;
    cardAuthCode = "";
    discountCents = 0;
    error = null;
    saleResponse = null;
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
        {services}
        {error}
      />
      <div class="step-actions">
        <Button variant="primary" on:click={nextStep} disabled={!canProceedStep1}>
          Siguiente →
        </Button>
      </div>
    </div>
  {:else if currentStep === 2}
    <!-- Step 2: Child and Payer Info -->
    <div class="form-step">
      <h3 class="step-title">2. Información del Cliente</h3>
      <div class="form-fields">
        <div class="form-group">
          <label for="child-name" class="label">
            Nombre del Niño <span class="required">*</span>
          </label>
          <Input
            id="child-name"
            type="text"
            bind:value={childName}
            placeholder="Nombre del niño"
            required
          />
        </div>
        <div class="form-group">
          <label for="payer-name" class="label">
            Nombre del Pagador <span class="required">*</span>
          </label>
          <Input
            id="payer-name"
            type="text"
            bind:value={payerName}
            placeholder="Nombre completo"
            required
          />
        </div>
        <div class="form-group">
          <label for="payer-phone" class="label">Teléfono (opcional)</label>
          <Input
            id="payer-phone"
            type="tel"
            bind:value={payerPhone}
            placeholder="Teléfono de contacto"
          />
        </div>
        {#if totalCents > 0}
          <div class="form-group">
            <label for="discount" class="label">Descuento (opcional)</label>
            <Input
              id="discount"
              type="number"
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
      </div>
      <div class="step-actions">
        <Button variant="secondary" on:click={previousStep}>← Anterior</Button>
        <Button variant="primary" on:click={nextStep} disabled={!canProceedStep2}>
          Siguiente →
        </Button>
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
        {totalCents}
        {error}
      />
      <div class="step-actions">
        <Button variant="secondary" on:click={previousStep}>← Anterior</Button>
        <Button
          variant="primary"
          on:click={submitSale}
          disabled={!canProceedStep3 || loading}
        >
          {loading ? "Procesando..." : "Confirmar Venta"}
        </Button>
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
        <Button variant="primary" on:click={resetForm}>Nueva Venta</Button>
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

  .step-actions {
    display: flex;
    gap: var(--spacing-md);
    justify-content: flex-end;
    margin-top: var(--spacing-lg);
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

    .step-actions :global(button) {
      width: 100%;
    }
  }
</style>





























