<script lang="ts">
  /**
   * DayStartForm component - Form to start a new day.
   * 
   * Handles day start with initial cash amount.
   */
  import { onMount } from "svelte";
  import { user } from "$lib/stores/auth";
  import { startDay, fetchDayStatus, dayOperationsStore } from "$lib/stores/day-operations";
  import { createEventDispatcher } from "svelte";

  export let sucursalId: string = "";

  const dispatch = createEventDispatcher();

  let initialCashInput = "";
  let loading = false;
  let error: string | null = null;
  let successMessage: string | null = null;
  let justStartedDay = false; // Track if we just started a day to show success message

  $: initialCashCents = initialCashInput ? Math.round(parseFloat(initialCashInput) * 100) : 0;
  $: canSubmit = initialCashInput !== "" && parseFloat(initialCashInput) >= 0;

  onMount(async () => {
    // Fetch current day status
    const currentUser = $user;
    const targetSucursalId = sucursalId || currentUser?.sucursal_id || "";
    if (targetSucursalId) {
      try {
        await fetchDayStatus(targetSucursalId);
      } catch (e: any) {
        error = e.message || "Error loading day status";
      }
    }
  });

  async function handleSubmit() {
    const currentUser = $user;
    const targetSucursalId = sucursalId || currentUser?.sucursal_id || "";
    
    if (!targetSucursalId) {
      error = "Sucursal ID is required";
      return;
    }

    if (!canSubmit) {
      error = "Please enter a valid initial cash amount";
      return;
    }

    loading = true;
    error = null;

    try {
      const success = await startDay({
        sucursal_id: targetSucursalId,
        initial_cash_cents: initialCashCents,
      });
      
      if (success) {
        // Refresh day status to update the store
        await fetchDayStatus(targetSucursalId);
        
        // Show success message with start date/time
        const startDateTime = $dayOperationsStore.dayStatus?.dayStart?.started_at
          ? formatStartedAt($dayOperationsStore.dayStatus.dayStart.started_at)
          : "ahora";
        successMessage = `✅ Día iniciado exitosamente el ${startDateTime}`;
        justStartedDay = true;
        initialCashInput = "";
        
        // Clear the flag after showing the message for 1.5s
        setTimeout(() => {
          justStartedDay = false;
          dispatch("success");
        }, 1500);
      } else {
        error = "No se pudo iniciar el día";
      }
    } catch (e: any) {
      error = e.message || "Error starting day";
    } finally {
      loading = false;
    }
  }

  function formatPrice(cents: number): string {
    return `$${(cents / 100).toFixed(2)}`;
  }

  /**
   * Format started_at date defensively with null/undefined checks.
   * Returns "N/A" if date is invalid or cannot be parsed.
   */
  function formatStartedAt(startedAt: string | undefined | null): string {
    if (!startedAt) {
      return "N/A";
    }
    
    try {
      // Handle ISO format strings (with or without timezone)
      const date = new Date(startedAt);
      
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
      console.warn("Error formatting started_at date:", startedAt, error);
      return "N/A";
    }
  }
</script>

<div class="day-start-form-container">
  {#if $dayOperationsStore.dayStatus?.isOpen}
    <div class="info-banner">
      {#if justStartedDay && successMessage}
        <div class="success-banner">{successMessage}</div>
      {/if}
      <p>⚠️ Ya hay un día activo iniciado el {
        formatStartedAt($dayOperationsStore.dayStatus?.dayStart?.started_at)
      }</p>
      <p class="info-text">Debe cerrar el día actual antes de iniciar uno nuevo.</p>
    </div>
  {:else}
    <div class="form-step">
      <div class="form-fields">
        <div class="input-wrapper">
          <label for="initial-cash" class="label">
            Dinero Inicial (en pesos) <span class="required">*</span>
          </label>
          <input
            id="initial-cash"
            type="number"
            step="0.01"
            min="0"
            class="input"
            bind:value={initialCashInput}
            placeholder="0.00"
            required
          />
        </div>

        {#if successMessage}
          <div class="success-banner">{successMessage}</div>
        {/if}

        {#if error}
          <div class="error-banner">{error}</div>
        {/if}

        <div class="form-actions">
          <button
            type="button"
            class="btn btn-primary"
            on:click={handleSubmit}
            disabled={!canSubmit || loading}
          >
            {loading ? "Iniciando..." : "Iniciar Día"}
          </button>
        </div>
      </div>
    </div>
  {/if}
</div>

<style>
  .day-start-form-container {
    max-width: 500px;
    margin: 0 auto;
    padding: var(--spacing-xl);
    background: var(--theme-bg-elevated);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-md);
  }

  .form-step {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xl);
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

  .error-banner {
    padding: var(--spacing-md);
    background: rgba(211, 5, 84, 0.1);
    border: 1px solid var(--accent-danger);
    border-radius: var(--radius-md);
    color: var(--accent-danger);
    margin-bottom: var(--spacing-lg);
  }

  .success-banner {
    padding: var(--spacing-md);
    background: rgba(34, 197, 94, 0.1);
    border: 1px solid #22c55e;
    border-radius: var(--radius-md);
    color: #22c55e;
    font-weight: 600;
    margin-bottom: var(--spacing-lg);
  }

  .info-banner {
    padding: var(--spacing-md);
    background: rgba(255, 206, 0, 0.1);
    border: 1px solid var(--accent-warning);
    border-radius: var(--radius-md);
    color: var(--accent-warning);
  }

  .info-text {
    margin-top: var(--spacing-sm);
    font-size: var(--text-sm);
  }

  .form-actions {
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

  @media (max-width: 768px) {
    .day-start-form-container {
      padding: var(--spacing-md);
    }

    .form-actions {
      flex-direction: column;
      align-items: stretch;
    }

    .form-actions .btn {
      width: 100%;
      min-height: 44px;
    }
  }

  /* Prevent hover transform issues on touch devices */
  @media (hover: none) and (pointer: coarse) {
    .form-actions .btn-primary:hover:not(:disabled) {
      transform: none;
    }
  }
</style>
























