<script lang="ts">
  /**
   * CashReconciliation component - Display cash reconciliation after day close.
   * 
   * Shows system totals vs physical count and highlights differences.
   */
  // DayClose type - compatible with both day-operations and day-close-history stores
  export let dayClose: {
    system_total_cents: number;
    physical_count_cents: number;
    difference_cents: number;
    totals: Record<string, any> | null;
    notes?: string | null; // Optional notes/observations for the day close
    created_at?: string; // Optional: date/time when day was closed
  };

  function formatPrice(cents: number): string {
    return `$${(cents / 100).toFixed(2)}`;
  }

  /**
   * Format datetime string defensively with null/undefined checks.
   * Returns formatted date in Spanish locale or fallback string.
   */
  function formatDateTime(dateTimeString: string | undefined | null): string {
    if (!dateTimeString) {
      return "N/A";
    }
    
    try {
      const date = new Date(dateTimeString);
      
      // Check if date is valid
      if (isNaN(date.getTime())) {
        return "N/A";
      }
      
      // Format date in Spanish locale
      return date.toLocaleString("es-ES", {
        year: "numeric",
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit"
      });
    } catch (error) {
      console.warn("Error formatting datetime:", dateTimeString, error);
      return "N/A";
    }
  }

  $: hasDifference = dayClose.difference_cents !== 0;
  $: isPositive = dayClose.difference_cents > 0;
  $: isNegative = dayClose.difference_cents < 0;
</script>

<div class="cash-reconciliation">
  <h3 class="reconciliation-title">Arqueo de Caja</h3>
  
  {#if dayClose.created_at}
    <div class="close-datetime">
      <span class="close-datetime-label">Cerrado el:</span>
      <span class="close-datetime-value">{formatDateTime(dayClose.created_at)}</span>
    </div>
  {/if}

  <div class="reconciliation-details">
    <div class="detail-row">
      <span class="detail-label">Total Sistema:</span>
      <span class="detail-value">{formatPrice(dayClose.system_total_cents)}</span>
    </div>

    <div class="detail-row">
      <span class="detail-label">Dinero Contado:</span>
      <span class="detail-value">{formatPrice(dayClose.physical_count_cents)}</span>
    </div>

    <div class="detail-row difference" class:positive={isPositive} class:negative={isNegative}>
      <span class="detail-label">Diferencia:</span>
      <span class="detail-value">
        {isPositive ? "+" : ""}{formatPrice(dayClose.difference_cents)}
      </span>
    </div>

    {#if dayClose.totals}
      <div class="totals-section">
        <h4 class="section-title">Detalles Adicionales</h4>
        {#if dayClose.totals.cash_received_total_cents !== undefined}
          <div class="detail-row">
            <span class="detail-label">Efectivo Recibido:</span>
            <span class="detail-value">{formatPrice(dayClose.totals.cash_received_total_cents)}</span>
          </div>
        {/if}
        {#if dayClose.totals.initial_cash_cents !== undefined}
          <div class="detail-row">
            <span class="detail-label">Efectivo Inicial:</span>
            <span class="detail-value">{formatPrice(dayClose.totals.initial_cash_cents)}</span>
          </div>
        {/if}
        {#if dayClose.totals.total_sales_count !== undefined}
          <div class="detail-row">
            <span class="detail-label">Número de Ventas:</span>
            <span class="detail-value">{dayClose.totals.total_sales_count}</span>
          </div>
        {/if}
        {#if dayClose.totals.total_revenue_cents !== undefined}
          <div class="detail-row">
            <span class="detail-label">Ingresos Totales:</span>
            <span class="detail-value">{formatPrice(dayClose.totals.total_revenue_cents)}</span>
          </div>
        {/if}
        {#if dayClose.totals.revenue_by_payment_method}
          <div class="payment-methods">
            <h5 class="subsection-title">Por Método de Pago:</h5>
            {#if dayClose.totals.revenue_by_payment_method.cash !== undefined}
              <div class="detail-row">
                <span class="detail-label">Efectivo:</span>
                <span class="detail-value">{formatPrice(dayClose.totals.revenue_by_payment_method.cash)}</span>
              </div>
            {/if}
            {#if dayClose.totals.revenue_by_payment_method.card !== undefined}
              <div class="detail-row">
                <span class="detail-label">Tarjeta:</span>
                <span class="detail-value">{formatPrice(dayClose.totals.revenue_by_payment_method.card)}</span>
              </div>
            {/if}
            {#if dayClose.totals.revenue_by_payment_method.transfer !== undefined}
              <div class="detail-row">
                <span class="detail-label">Transferencia:</span>
                <span class="detail-value">{formatPrice(dayClose.totals.revenue_by_payment_method.transfer)}</span>
              </div>
            {/if}
          </div>
        {/if}
      </div>
    {/if}
  </div>

  {#if dayClose.notes && dayClose.notes.trim()}
    <div class="notes-section">
      <h4 class="section-title">Notas Adicionales</h4>
      <div class="notes-content">{dayClose.notes}</div>
    </div>
  {/if}

  {#if hasDifference}
    <div class="alert-banner" class:positive={isPositive} class:negative={isNegative}>
      {#if isPositive}
        <p>⚠️ Hay un excedente de {formatPrice(dayClose.difference_cents)}</p>
      {:else}
        <p>⚠️ Hay una falta de {formatPrice(Math.abs(dayClose.difference_cents))}</p>
      {/if}
    </div>
  {:else}
    <div class="success-banner">
      <p>✅ El arqueo coincide perfectamente</p>
    </div>
  {/if}
</div>

<style>
  .cash-reconciliation {
    padding: var(--spacing-lg);
    background: var(--theme-bg-secondary);
    border-radius: var(--radius-md);
    border: 1px solid var(--border-primary);
  }

  .reconciliation-title {
    font-family: var(--font-primary);
    font-size: var(--text-xl);
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: var(--spacing-md);
  }

  .close-datetime {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    margin-bottom: var(--spacing-lg);
    padding: var(--spacing-sm) var(--spacing-md);
    background: var(--theme-bg-secondary);
    border-radius: var(--radius-md);
    border: 1px solid var(--border-primary);
  }

  .close-datetime-label {
    font-size: var(--text-sm);
    font-weight: 600;
    color: var(--text-secondary);
  }

  .close-datetime-value {
    font-size: var(--text-sm);
    font-weight: 600;
    color: var(--text-primary);
    font-family: var(--font-mono);
  }

  .reconciliation-details {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-md);
    margin-bottom: var(--spacing-lg);
  }

  .detail-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: var(--spacing-sm) 0;
    border-bottom: 1px solid var(--border-primary);
  }

  .detail-row:last-child {
    border-bottom: none;
  }

  .detail-row.difference {
    font-weight: 700;
    font-size: var(--text-lg);
    padding: var(--spacing-md) 0;
    border-top: 2px solid var(--border-primary);
    border-bottom: 2px solid var(--border-primary);
  }

  .detail-label {
    font-weight: 600;
    color: var(--text-secondary);
  }

  .detail-value {
    font-family: var(--font-mono);
    color: var(--text-primary);
    font-weight: 600;
  }

  .detail-row.difference.positive .detail-value {
    color: var(--accent-success);
  }

  .detail-row.difference.negative .detail-value {
    color: var(--accent-danger);
  }

  .totals-section {
    margin-top: var(--spacing-md);
    padding-top: var(--spacing-md);
    border-top: 1px solid var(--border-primary);
  }

  .section-title {
    font-size: var(--text-base);
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: var(--spacing-sm);
  }

  .subsection-title {
    font-size: var(--text-sm);
    font-weight: 600;
    color: var(--text-secondary);
    margin-top: var(--spacing-sm);
    margin-bottom: var(--spacing-xs);
  }

  .payment-methods {
    margin-top: var(--spacing-sm);
    padding-top: var(--spacing-sm);
    border-top: 1px dashed var(--border-primary);
  }

  .notes-section {
    margin-top: var(--spacing-md);
    padding-top: var(--spacing-md);
    border-top: 1px solid var(--border-primary);
  }

  .notes-content {
    padding: var(--spacing-md);
    background: var(--theme-bg-secondary);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
    color: var(--text-primary);
    white-space: pre-wrap; /* Preserve line breaks and whitespace */
    word-wrap: break-word; /* Break long words if needed */
    line-height: 1.6;
    font-size: var(--text-base);
  }

  .alert-banner {
    padding: var(--spacing-md);
    border-radius: var(--radius-md);
    font-weight: 600;
  }

  .alert-banner.positive {
    background: rgba(0, 200, 83, 0.1);
    border: 1px solid var(--accent-success);
    color: var(--accent-success);
  }

  .alert-banner.negative {
    background: rgba(211, 5, 84, 0.1);
    border: 1px solid var(--accent-danger);
    color: var(--accent-danger);
  }

  .success-banner {
    padding: var(--spacing-md);
    background: rgba(0, 200, 83, 0.1);
    border: 1px solid var(--accent-success);
    border-radius: var(--radius-md);
    color: var(--accent-success);
    font-weight: 600;
    text-align: center;
  }
</style>

























