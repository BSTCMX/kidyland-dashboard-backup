<script lang="ts">
  /**
   * ExtendTimerModal component - Modal for extending a timer with service extension sale.
   * 
   * Allows selecting extension duration from service slots and payment method.
   */
  import { Modal, Button } from "@kidyland/ui";
  import { post } from "@kidyland/utils";
  import { createEventDispatcher, onMount } from "svelte";
  import type { Timer, Service, Sale, ChildInfo } from "@kidyland/shared/types";
  import { activeServices, fetchServices } from "$lib/stores/services";
  import { user } from "@kidyland/utils";
  import PaymentForm from "$lib/components/forms/PaymentForm.svelte";
  import { printTicket, fetchSaleById } from "$lib/stores/sales-history";
  import { updateTimerFromExtension } from "$lib/stores/timers";

  export let open = false;
  export let timer: Timer | null = null;
  export let saleId: string = "";

  const dispatch = createEventDispatcher();

  // Service and duration selection
  let selectedDuration: number = 0;
  let selectedService: Service | null = null;

  // Original sale data (for multi-child support)
  let originalSale: Sale | null = null;
  let loadingSale = false;

  // Payment form state
  let paymentMethod: "cash" | "card" | "transfer" = "cash";
  let cashReceivedCents: number | undefined = undefined;
  let cardAuthCode: string = "";
  let transferReference: string = "";

  let loading = false;
  let error: string | null = null;

  // Load services and original sale on mount if not already loaded
  onMount(async () => {
    const currentUser = $user;
    if (currentUser?.sucursal_id && $activeServices.length === 0) {
      await fetchServices(currentUser.sucursal_id);
    }
    
    // Load original sale to get children information (for multi-child support)
    if (saleId) {
      loadingSale = true;
      try {
        originalSale = await fetchSaleById(saleId);
      } catch (e: any) {
        console.warn("Could not fetch original sale for children info:", e);
        // Continue without children info (backward compatibility)
      } finally {
        loadingSale = false;
      }
    }
  });

  // Reload original sale when saleId changes
  $: if (saleId && open) {
    (async () => {
      loadingSale = true;
      try {
        originalSale = await fetchSaleById(saleId);
      } catch (e: any) {
        console.warn("Could not fetch original sale for children info:", e);
        originalSale = null;
      } finally {
        loadingSale = false;
      }
    })();
  }

  // Find service from timer.service_id
  $: if (timer?.service_id && $activeServices.length > 0) {
    selectedService = $activeServices.find((s) => s.id === timer.service_id) || null;
  } else {
    selectedService = null;
  }

  // Available durations from service
  $: availableDurations = selectedService?.durations_allowed || [];

  // Calculate quantity from original sale's children (for multi-child support)
  $: childrenQuantity = originalSale?.children && originalSale.children.length > 0
    ? originalSale.children.length
    : 1; // Default to 1 for backward compatibility

  // Calculate unit price from duration_prices
  $: unitPrice = selectedService && selectedDuration && selectedService.duration_prices
    ? (selectedService.duration_prices[selectedDuration] || 
       selectedService.duration_prices[Math.min(...selectedService.durations_allowed)] || 
       0)
    : 0;

  // Calculate total price: unit price × quantity (for multi-child extensions)
  $: calculatedPrice = unitPrice * childrenQuantity;

  // Reset form when modal closes
  $: if (!open) {
    selectedDuration = 0;
    paymentMethod = "cash";
    cashReceivedCents = undefined;
    cardAuthCode = "";
    transferReference = "";
    error = null;
  }

  function handleDurationChange(event: Event) {
    const target = event.target as HTMLSelectElement;
    selectedDuration = parseInt(target.value, 10);
    // Reset payment when duration changes
    cashReceivedCents = undefined;
  }

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

  function formatPrice(cents: number): string {
    return `$${(cents / 100).toFixed(2)}`;
  }

  async function handleExtend() {
    // Validation
    if (!selectedDuration || selectedDuration <= 0) {
      error = "Debe seleccionar una duración válida";
      return;
    }

    if (!selectedService) {
      error = "No se encontró el servicio del timer";
      return;
    }

    if (calculatedPrice <= 0) {
      error = "No se pudo calcular el precio para la duración seleccionada";
      return;
    }

    // Validate payment method specific fields
    if (paymentMethod === "cash") {
      if (!cashReceivedCents || cashReceivedCents < calculatedPrice) {
        error = `El efectivo recibido debe ser al menos ${formatPrice(calculatedPrice)}`;
        return;
      }
    } else if (paymentMethod === "card") {
      if (!cardAuthCode || !cardAuthCode.trim()) {
        error = "Debe ingresar el código de autorización";
        return;
      }
    } else if (paymentMethod === "transfer") {
      if (!transferReference || !transferReference.trim()) {
        error = "Debe ingresar la referencia de transferencia";
        return;
      }
    }

    loading = true;
    error = null;

    try {
      // Prepare request body
      const extensionData: any = {
        duration_minutes: selectedDuration,
        payment_method: paymentMethod,
      };

      if (paymentMethod === "cash") {
        extensionData.cash_received_cents = cashReceivedCents;
      } else if (paymentMethod === "card") {
        extensionData.card_auth_code = cardAuthCode;
      } else if (paymentMethod === "transfer") {
        extensionData.transfer_reference = transferReference;
      }

      // Call extend endpoint
      const result = await post(`/sales/${saleId}/extend`, extensionData);
      
      // Immediately update the timer in the store with the response data
      // This eliminates the perceived delay until WebSocket update (every 5 seconds)
      // Backend now returns timer object with time_left_minutes for immediate UI update
      if (result.timer && timer?.id) {
        updateTimerFromExtension(timer.id, result.timer);
      }
      
      // If ticket HTML is returned, print it
      if (result.ticket_html) {
        // Open print window with ticket HTML
        const printWindow = window.open("", "_blank");
        if (printWindow) {
          printWindow.document.write(result.ticket_html);
          printWindow.document.close();
          printWindow.focus();
          setTimeout(() => {
            printWindow.print();
          }, 250);
        }
      } else if (result.sale_id) {
        // Fallback: use printTicket function if ticket_html not in response
        await printTicket(result.sale_id);
      }

      dispatch("success");
      open = false;
    } catch (e: any) {
      error = e.message || "Error al extender el timer";
    } finally {
      loading = false;
    }
  }
</script>

<Modal open={open} on:close={() => dispatch("close")}>
  <div class="extend-timer-modal">
    <h2 class="modal-title">Extender Timer</h2>
    
    {#if timer}
      <div class="timer-info">
        {#if originalSale?.children && originalSale.children.length > 0}
          <!-- Multi-child sale: show all children -->
          <p><strong>Niños ({originalSale.children.length}):</strong></p>
          <ul class="children-list">
            {#each originalSale.children as child}
              <li>{child.name}{child.age ? ` (${child.age})` : ""}</li>
            {/each}
          </ul>
        {:else}
          <!-- Single child or legacy format: show timer.child_name -->
          <p><strong>Niño:</strong> {timer.child_name || "N/A"}</p>
        {/if}
        <p><strong>Estado:</strong> {timer.status}</p>
        {#if selectedService}
          <p><strong>Servicio:</strong> {selectedService.name}</p>
        {/if}
      </div>
    {/if}

    {#if !selectedService}
      <div class="loading-info">
        <p>Cargando información del servicio...</p>
      </div>
    {:else if availableDurations.length === 0}
      <div class="error-banner">
        El servicio no tiene duraciones disponibles
      </div>
    {:else}
      <!-- Duration Selection -->
      <div class="form-group">
        <div class="input-wrapper">
          <label for="duration-select" class="label">
            Duración de Extensión <span class="required">*</span>
          </label>
          <select
            id="duration-select"
            class="select"
            value={selectedDuration}
            on:change={handleDurationChange}
            disabled={loading}
          >
            <option value="0">Seleccione duración</option>
            {#each availableDurations as duration}
              <option value={duration}>
                {formatDuration(duration)}
                {#if selectedService.duration_prices && selectedService.duration_prices[duration]}
                  - {formatPrice(selectedService.duration_prices[duration])}
                {/if}
              </option>
            {/each}
          </select>
          <p class="help-text">Seleccione la duración que desea agregar al timer</p>
        </div>
      </div>

      {#if selectedDuration > 0 && calculatedPrice > 0}
        <!-- Price Preview with quantity info -->
        <div class="price-preview">
          <div class="price-breakdown">
            <p class="price-label">Precio unitario:</p>
            <p class="price-value">${(unitPrice / 100).toFixed(2)}</p>
          </div>
          {#if childrenQuantity > 1}
            <div class="price-breakdown">
              <p class="price-label">Cantidad de niños:</p>
              <p class="price-value">{childrenQuantity}</p>
            </div>
          {/if}
          <div class="price-breakdown total-price">
            <p class="price-label">Total a pagar:</p>
            <p class="price-value">${(calculatedPrice / 100).toFixed(2)}</p>
          </div>
        </div>

        <!-- Payment Form -->
        <PaymentForm
          bind:paymentMethod
          bind:cashReceivedCents
          bind:cardAuthCode
          bind:transferReference
          totalCents={calculatedPrice}
          {error}
        />
      {/if}
    {/if}

    {#if error}
      <div class="error-banner">{error}</div>
    {/if}

    <div class="modal-actions">
      <button 
        type="button"
        class="btn btn-secondary" 
        on:click={() => dispatch("close")} 
        disabled={loading}
      >
        Cancelar
      </button>
      <button 
        type="button"
        class="btn btn-primary" 
        on:click={handleExtend} 
        disabled={loading || !selectedDuration || !selectedService || calculatedPrice <= 0}
      >
        {loading ? "Extendiendo..." : "Extender Timer"}
      </button>
    </div>
  </div>
</Modal>

<style>
  .extend-timer-modal {
    padding: var(--spacing-xl);
    max-width: 500px;
    width: 100%;
  }

  .modal-title {
    font-family: var(--font-primary);
    font-size: var(--text-2xl);
    font-weight: 700;
    color: var(--text-primary);
    margin: 0 0 var(--spacing-lg) 0;
    
    /* Efecto 3D - solo sombreado, sin animaciones */
    text-shadow: 
      0 0.05em 0 rgba(0, 0, 0, 0.1),
      0 0.1em 0 rgba(0, 0, 0, 0.1),
      0 0.15em 0 rgba(0, 0, 0, 0.1),
      0 0.2em 0 rgba(0, 0, 0, 0.1),
      0 0.25em 0 rgba(0, 0, 0, 0.1),
      0 0.25em 0.02em rgba(0, 0, 0, 0.15),
      0 0.28em 0.2em rgba(0, 0, 0, 0.25);
  }

  .timer-info {
    padding: var(--spacing-lg);
    background: var(--theme-bg-card);
    backdrop-filter: blur(16px) saturate(150%);
    -webkit-backdrop-filter: blur(16px) saturate(150%);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-lg);
    margin-bottom: var(--spacing-lg);
    box-shadow: 
      0 4px 12px rgba(0, 0, 0, 0.15),
      0 0 10px var(--glow-primary);
  }

  .timer-info p {
    margin: var(--spacing-xs) 0;
    color: var(--text-primary);
    font-size: var(--text-base);
    line-height: 1.6;
  }

  .timer-info strong {
    color: var(--text-primary);
    font-weight: 600;
  }

  .loading-info {
    padding: var(--spacing-lg);
    text-align: center;
    color: var(--text-secondary);
    margin-bottom: var(--spacing-lg);
    font-size: var(--text-base);
  }

  .form-group {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-sm);
    margin-bottom: var(--spacing-lg);
  }

  /* Input Wrapper - Estilo consistente con ServiceSaleForm */
  .input-wrapper {
    position: relative;
    width: 100%;
    margin-bottom: 16px;
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

  .select {
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
    cursor: pointer;
  }

  .select:focus {
    background-color: var(--input-bg-focus);
    border-color: var(--accent-primary);
    box-shadow: 
      0 0 0 3px rgba(0, 147, 247, 0.1),
      0 0 20px var(--glow-primary);
  }

  .select:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .help-text {
    font-size: var(--text-sm);
    color: var(--text-secondary);
    margin-top: var(--spacing-xs);
    padding-left: 4px;
  }

  .price-preview {
    padding: var(--spacing-md);
    background: var(--theme-bg-card);
    backdrop-filter: blur(16px) saturate(150%);
    -webkit-backdrop-filter: blur(16px) saturate(150%);
    border: 2px solid var(--accent-primary);
    border-radius: var(--radius-lg);
    margin-bottom: var(--spacing-lg);
    box-shadow: 
      0 4px 12px rgba(0, 0, 0, 0.15),
      0 0 20px var(--glow-primary);
  }

  .price-breakdown {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: var(--spacing-xs) 0;
    border-bottom: 1px solid rgba(0, 147, 247, 0.2);
  }

  .price-breakdown:last-child {
    border-bottom: none;
  }

  .price-breakdown.total-price {
    margin-top: var(--spacing-sm);
    padding-top: var(--spacing-sm);
    border-top: 2px solid var(--accent-primary);
    border-bottom: none;
  }

  .price-label {
    font-weight: 600;
    font-size: var(--text-base);
    color: var(--text-primary);
    margin: 0;
  }

  .price-value {
    font-weight: 700;
    font-size: var(--text-lg);
    color: var(--accent-primary);
    font-family: var(--font-secondary);
    text-shadow: 0 0 10px var(--glow-primary);
    margin: 0;
  }

  .price-breakdown.total-price .price-value {
    font-size: var(--text-2xl);
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

  .modal-actions {
    display: flex;
    gap: 12px;
    justify-content: flex-end;
    margin-top: 32px;
    padding-top: 0;
    border-top: none;
  }

  /* Botones con estilo consistente con ServiceSaleForm */
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

  /* Responsive: Mobile */
  @media (max-width: 768px) {
    .extend-timer-modal {
      padding: var(--spacing-md);
    }

    .modal-actions {
      flex-direction: column;
    }

    .modal-actions .btn {
      width: 100%;
      min-height: 48px; /* Minimum touch target size for accessibility */
    }
  }

  /* Prevent hover transform issues on touch devices */
  @media (hover: none) and (pointer: coarse) {
    .modal-actions .btn-primary:hover:not(:disabled),
    .modal-actions .btn-secondary:hover:not(:disabled) {
      /* Maintain gradient but remove any transform effects */
    }
  }
</style>
