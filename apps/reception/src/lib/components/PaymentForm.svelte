<script lang="ts">
  /**
   * PaymentForm component - Payment method and details.
   * 
   * Handles payment method selection and payment details input.
   */
  export let paymentMethod: "cash" | "card" | "mixed" = "cash";
  export let cashReceivedCents: number | undefined = undefined;
  export let cardAuthCode: string = "";
  export let totalCents: number = 0;
  export let error: string | null = null;

  function formatPrice(cents: number): string {
    return `$${(cents / 100).toFixed(2)}`;
  }

  function handlePaymentMethodChange(event: Event) {
    const target = event.target as HTMLSelectElement;
    paymentMethod = target.value as "cash" | "card" | "mixed";
    // Reset payment details when method changes
    if (paymentMethod === "cash") {
      cardAuthCode = "";
    } else if (paymentMethod === "card") {
      cashReceivedCents = undefined;
    }
  }

  function handleCashReceivedChange(event: Event) {
    const target = event.target as HTMLInputElement;
    const value = parseFloat(target.value) || 0;
    cashReceivedCents = Math.round(value * 100);
  }

  $: changeCents =
    paymentMethod === "cash" && cashReceivedCents
      ? cashReceivedCents - totalCents
      : 0;
</script>

<div class="payment-form">
  <div class="form-group">
    <label for="payment-method" class="label">
      Método de Pago <span class="required">*</span>
    </label>
    <select
      id="payment-method"
      class="select"
      value={paymentMethod}
      on:change={handlePaymentMethodChange}
    >
      <option value="cash">Efectivo</option>
      <option value="card">Tarjeta</option>
      <option value="mixed">Mixto</option>
    </select>
  </div>

  <div class="total-display">
    <div class="total-label">Total a Pagar:</div>
    <div class="total-value">{formatPrice(totalCents)}</div>
  </div>

  {#if paymentMethod === "cash" || paymentMethod === "mixed"}
    <div class="form-group">
      <label for="cash-received" class="label">
        Efectivo Recibido {paymentMethod === "mixed" ? "(parcial)" : ""}
      </label>
      <input
        id="cash-received"
        type="number"
        step="0.01"
        min="0"
        class="input"
        placeholder="0.00"
        value={cashReceivedCents ? cashReceivedCents / 100 : ""}
        on:input={handleCashReceivedChange}
      />
      {#if paymentMethod === "cash" && cashReceivedCents && changeCents >= 0}
        <div class="change-display">
          Cambio: {formatPrice(changeCents)}
        </div>
      {:else if paymentMethod === "cash" && cashReceivedCents && changeCents < 0}
        <div class="error-text">
          Faltan {formatPrice(Math.abs(changeCents))}
        </div>
      {/if}
    </div>
  {/if}

  {#if paymentMethod === "card" || paymentMethod === "mixed"}
    <div class="form-group">
      <label for="card-auth" class="label">
        Código de Autorización {paymentMethod === "mixed" ? "(opcional)" : ""}
      </label>
      <input
        id="card-auth"
        type="text"
        class="input"
        placeholder="Código de autorización"
        bind:value={cardAuthCode}
      />
    </div>
  {/if}

  {#if error}
    <div class="error-message">{error}</div>
  {/if}
</div>

<style>
  .payment-form {
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

  .total-display {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: var(--spacing-lg);
    background: var(--theme-bg-secondary);
    border: 2px solid var(--accent-primary);
    border-radius: var(--radius-lg);
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

  .change-display {
    padding: var(--spacing-sm);
    background: rgba(61, 173, 9, 0.1);
    border: 1px solid var(--accent-success);
    border-radius: var(--radius-sm);
    color: var(--accent-success);
    font-weight: 600;
    font-size: var(--text-sm);
  }

  .error-text {
    padding: var(--spacing-sm);
    color: var(--accent-danger);
    font-size: var(--text-sm);
    font-weight: 600;
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





























