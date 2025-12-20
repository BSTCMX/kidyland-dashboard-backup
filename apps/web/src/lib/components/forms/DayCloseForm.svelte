<script lang="ts">
  /**
   * DayCloseForm component - Form to close a day with cash reconciliation.
   * 
   * Handles day close with physical cash count and shows differences.
   */
  import { onMount } from "svelte";
  import { user } from "$lib/stores/auth";
  import { closeDay, fetchDayStatus, dayOperationsStore, previewDayClose, type DayClosePreview } from "$lib/stores/day-operations";
  import { createEventDispatcher } from "svelte";
  import CashReconciliation from "../shared/CashReconciliation.svelte";
  import { get } from "@kidyland/utils/api";
  import type { Sucursal } from "@kidyland/shared/types";
  import { RefreshCw } from "lucide-svelte";

  export let sucursalId: string = "";

  const dispatch = createEventDispatcher();

  let physicalCashInput = "";
  let notesInput = "";
  let loading = false;
  let loadingPreview = false;
  let error: string | null = null;
  let successMessage: string | null = null;
  let dayCloseResult: any = null;
  let businessDate: string = "";
  let preview: DayClosePreview | null = null;
  let justClosedDay = false; // Track if we just closed a day to show success message

  $: physicalCashCents = physicalCashInput ? Math.round(parseFloat(physicalCashInput) * 100) : 0;
  $: expectedTotalCents = preview?.expected_total_cents || 0;
  $: differenceCents = physicalCashCents - expectedTotalCents;
  $: canSubmit = physicalCashInput !== "" && parseFloat(physicalCashInput) >= 0;

  function formatPrice(cents: number): string {
    return `$${(cents / 100).toFixed(2)}`;
  }

  /**
   * Format datetime string defensively with null/undefined checks.
   * Returns formatted date in Spanish locale or fallback string.
   */
  function formatDateTime(dateTimeString: string | undefined | null): string {
    if (!dateTimeString) {
      return "ahora";
    }
    
    try {
      const date = new Date(dateTimeString);
      
      // Check if date is valid
      if (isNaN(date.getTime())) {
        return "ahora";
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
      return "ahora";
    }
  }

  async function loadPreview(sucursalId: string) {
    if (!sucursalId) return;
    loadingPreview = true;
    error = null;
    try {
      preview = await previewDayClose(sucursalId);
    } catch (e: any) {
      error = e.message || "Error al cargar el preview del cierre";
    } finally {
      loadingPreview = false;
    }
  }
  
  /**
   * Calculate business date using sucursal timezone.
   * Falls back to current date if timezone cannot be fetched.
   * The backend will validate and use its own calculated date (backend authority).
   */
  async function calculateBusinessDate(sucursalId: string): Promise<string> {
    try {
      // Try to get sucursal timezone
      const sucursal = await get<Sucursal>(`/sucursales/${sucursalId}`);
      const timezone = sucursal?.timezone || "America/Mexico_City";
      
      // Calculate today's date in the sucursal's timezone
      const dateFormatter = new Intl.DateTimeFormat("en-CA", {
        timeZone: timezone,
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
      });
      
      return dateFormatter.format(new Date()); // YYYY-MM-DD format
    } catch (e) {
      // Fallback to current date if timezone fetch fails
      console.warn("Could not fetch sucursal timezone, using current date:", e);
      return new Date().toISOString().split("T")[0];
    }
  }

  onMount(async () => {
    // Fetch current day status and get business date
    const currentUser = $user;
    const targetSucursalId = sucursalId || currentUser?.sucursal_id || "";
    if (targetSucursalId) {
      try {
        await fetchDayStatus(targetSucursalId);
        // Use business date from backend if available, otherwise calculate it
        // The backend is the source of truth, but we calculate it here as fallback
        const backendBusinessDate = $dayOperationsStore.dayStatus?.currentBusinessDate;
        if (backendBusinessDate) {
          businessDate = backendBusinessDate;
        } else {
          // Fallback: calculate business date using sucursal timezone
          businessDate = await calculateBusinessDate(targetSucursalId);
        }
        // Load preview if day is open
        if ($dayOperationsStore.dayStatus?.isOpen) {
          await loadPreview(targetSucursalId);
        }
      } catch (e: any) {
        error = e.message || "Error loading day status";
        // Fallback to current date
        businessDate = new Date().toISOString().split("T")[0];
      }
    } else {
      // Fallback to current date if no sucursal ID
      businessDate = new Date().toISOString().split("T")[0];
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
      error = "Please enter a valid physical cash amount";
      return;
    }

    // Refresh day status before checking to ensure we have the latest state
    await fetchDayStatus(targetSucursalId);
    
    if (!$dayOperationsStore.dayStatus?.isOpen) {
      error = "No hay un día activo para cerrar";
      return;
    }

    loading = true;
    error = null;

    try {
      // Use calculated business date (backend will validate and use its own calculated date)
      const dateToSend = businessDate || new Date().toISOString().split("T")[0];
      
      const result = await closeDay({
        sucursal_id: targetSucursalId,
        date: dateToSend,
        physical_count_cents: physicalCashCents,
        notes: notesInput.trim() || undefined,
      });
      
      // Refresh day status after closing to update the store
      await fetchDayStatus(targetSucursalId);
      
      // Show success message with close date/time
      const closeDateTime = result.created_at 
        ? formatDateTime(result.created_at)
        : "ahora";
      successMessage = `✅ Día cerrado exitosamente el ${closeDateTime}`;
      justClosedDay = true;
      
      // Wait 1.5s to show the success message, then set dayCloseResult and dispatch
      setTimeout(() => {
        justClosedDay = false;
        dayCloseResult = result;
        dispatch("success", { dayClose: result });
      }, 1500);
    } catch (e: any) {
      // Handle error properly - e might be an object or string
      if (typeof e === 'string') {
        error = e;
      } else if (e?.message) {
        error = e.message;
      } else if (e?.detail) {
        error = e.detail;
      } else {
        error = "Error closing day";
      }
      console.error("Error closing day:", e);
    } finally {
      loading = false;
    }
  }

  function resetForm() {
    physicalCashInput = "";
    notesInput = "";
    dayCloseResult = null;
    error = null;
    successMessage = null;
    preview = null;
    justClosedDay = false;
  }
</script>

<div class="day-close-form-container">
  <div class="form-header">
    <h2 class="form-title">Cerrar Día</h2>
  </div>

  {#if !$dayOperationsStore.dayStatus?.isOpen}
    <div class="info-banner">
      {#if justClosedDay && successMessage}
        <div class="success-banner">{successMessage}</div>
      {:else}
        <p>⚠️ No hay un día activo para cerrar</p>
        <p class="info-text">Debe iniciar un día antes de poder cerrarlo.</p>
      {/if}
    </div>
  {:else if dayCloseResult}
    <!-- Show reconciliation after closing -->
    <CashReconciliation dayClose={dayCloseResult} />
    <div class="step-actions">
      <button 
        type="button"
        class="btn btn-primary" 
        on:click={resetForm}
      >
        Cerrar
      </button>
    </div>
  {:else}
    <div class="form-step">
      <div class="form-fields">
        <div class="input-wrapper">
          <label for="date" class="label">
            Fecha <span class="required">*</span>
          </label>
          <input
            id="date"
            type="date"
            class="input"
            value={businessDate || new Date().toISOString().split("T")[0]}
            disabled
          />
        </div>

        {#if loadingPreview}
          <div class="loading-preview">
            <p>Cargando cálculo automático...</p>
          </div>
        {:else if preview}
          <div class="preview-section">
            <div class="section-header">
              <h3 class="section-title">Cálculo Automático</h3>
              <div class="header-actions">
                <button
                  type="button"
                  class="btn btn-secondary btn-small refresh-button"
                  on:click={() => {
                    const targetSucursalId = sucursalId || $user?.sucursal_id || "";
                    if (targetSucursalId) {
                      loadPreview(targetSucursalId);
                    }
                  }}
                  disabled={loadingPreview}
                >
                  <RefreshCw size={16} strokeWidth={1.5} />
                  {#if loadingPreview}
                    Actualizando...
                  {:else}
                    Actualizar
                  {/if}
                </button>
              </div>
            </div>
            
            <div class="preview-grid">
              <div class="preview-item">
                <span class="preview-label">Efectivo Inicial:</span>
                <span class="preview-value">{formatPrice(preview.initial_cash_cents)}</span>
              </div>
              <div class="preview-item">
                <span class="preview-label">Efectivo Recibido:</span>
                <span class="preview-value">{formatPrice(preview.cash_received_total_cents)}</span>
              </div>
              <div class="preview-item expected-total">
                <span class="preview-label">Total Esperado:</span>
                <span class="preview-value expected">{formatPrice(preview.expected_total_cents)}</span>
              </div>
            </div>
          </div>
        {/if}

        <div class="input-wrapper">
          <label for="physical-cash" class="label">
            Dinero Contado Físicamente (en pesos) <span class="required">*</span>
          </label>
          <input
            id="physical-cash"
            type="number"
            step="0.01"
            min="0"
            class="input"
            bind:value={physicalCashInput}
            placeholder="0.00"
            required
          />
        </div>

        {#if preview && physicalCashInput && parseFloat(physicalCashInput) >= 0}
          <div class="difference-section" class:positive={differenceCents > 0} class:negative={differenceCents < 0} class:zero={differenceCents === 0}>
            <div class="difference-label">Diferencia:</div>
            <div class="difference-value">
              {differenceCents > 0 ? "+" : ""}{formatPrice(differenceCents)}
            </div>
            <div class="difference-help">
              {#if differenceCents > 0}
                Hay más dinero del esperado
              {:else if differenceCents < 0}
                Falta dinero del esperado
              {:else}
                El conteo coincide con el esperado
              {/if}
            </div>
          </div>
        {/if}

        <div class="input-wrapper">
          <label for="notes" class="label">
            Notas Adicionales (opcional)
          </label>
          <textarea
            id="notes"
            class="input textarea"
            bind:value={notesInput}
            placeholder="Observaciones, notas o comentarios sobre el cierre de día..."
            rows="4"
          ></textarea>
        </div>

        {#if successMessage && !dayCloseResult}
          <div class="success-banner">{successMessage}</div>
        {/if}

        {#if error}
          <div class="error-banner">{error}</div>
        {/if}

        <div class="step-actions">
          <button 
            type="button"
            class="btn btn-primary" 
            on:click={handleSubmit}
            disabled={!canSubmit || loading}
          >
            {loading ? "Cerrando..." : "Cerrar Día"}
          </button>
        </div>
      </div>
    </div>
  {/if}
</div>

<style>
  .day-close-form-container {
    max-width: 600px;
    margin: 0 auto;
    padding: var(--spacing-xl);
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

  .input.textarea {
    height: auto;
    min-height: 100px;
    padding: 16px 20px;
    resize: vertical;
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

  .btn-small {
    min-width: auto;
    height: 40px;
    font-size: 14px;
    padding: 0 16px;
  }

  .loading-preview {
    padding: var(--spacing-md);
    text-align: center;
    color: var(--text-secondary);
  }

  .preview-section {
    padding: var(--spacing-lg);
    background: rgba(74, 119, 212, 0.05);
    border: 1px solid rgba(74, 119, 212, 0.2);
    border-radius: var(--radius-md);
    margin-bottom: var(--spacing-lg);
  }

  .section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--spacing-md);
    gap: var(--spacing-md);
    flex-wrap: wrap;
  }

  .header-actions {
    display: flex;
    gap: var(--spacing-sm);
    align-items: center;
  }

  .refresh-button {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
  }

  .section-title {
    font-family: var(--font-primary);
    font-size: var(--text-xl);
    font-weight: 700;
    color: var(--text-primary);
    margin: 0;
  }

  .preview-grid {
    display: grid;
    grid-template-columns: 1fr;
    gap: var(--spacing-sm);
  }

  .preview-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: var(--spacing-sm);
    background: var(--theme-bg-elevated);
    border-radius: var(--radius-sm);
  }

  .preview-item.expected-total {
    background: rgba(34, 197, 94, 0.1);
    border: 1px solid rgba(34, 197, 94, 0.3);
    font-weight: 600;
  }

  .preview-label {
    font-size: var(--text-sm);
    color: var(--text-secondary);
  }

  .preview-value {
    font-size: var(--text-base);
    font-weight: 600;
    color: var(--text-primary);
  }

  .preview-value.expected {
    color: #22c55e;
  }

  .difference-section {
    padding: var(--spacing-md);
    border-radius: var(--radius-md);
    border: 2px solid;
    background: var(--theme-bg-secondary);
  }

  .difference-section.positive {
    border-color: #22c55e;
    background: rgba(34, 197, 94, 0.1);
  }

  .difference-section.negative {
    border-color: var(--accent-danger);
    background: rgba(211, 5, 84, 0.1);
  }

  .difference-section.zero {
    border-color: var(--accent-warning);
    background: rgba(255, 206, 0, 0.1);
  }

  .difference-label {
    font-size: var(--text-sm);
    font-weight: 600;
    color: var(--text-secondary);
    margin-bottom: var(--spacing-xs);
  }

  .difference-value {
    font-size: var(--text-2xl);
    font-weight: 700;
    margin-bottom: var(--spacing-xs);
  }

  .difference-section.positive .difference-value {
    color: #22c55e;
  }

  .difference-section.negative .difference-value {
    color: var(--accent-danger);
  }

  .difference-section.zero .difference-value {
    color: var(--accent-warning);
  }

  .difference-help {
    font-size: var(--text-sm);
    color: var(--text-secondary);
  }

  @media (max-width: 768px) {
    .day-close-form-container {
      padding: var(--spacing-md);
    }

    .section-header {
      flex-direction: column;
      align-items: stretch;
      gap: var(--spacing-sm);
    }

    .header-actions {
      width: 100%;
      flex-direction: column;
      gap: var(--spacing-sm);
      align-items: stretch;
    }

    .refresh-button {
      width: 100%;
      min-height: 44px; /* Minimum touch target size for accessibility */
      justify-content: center;
    }

    .preview-grid {
      grid-template-columns: 1fr;
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
    .refresh-button:hover,
    .step-actions .btn-primary:hover:not(:disabled),
    .step-actions .btn-secondary:hover:not(:disabled) {
      transform: none;
    }
  }
</style>
























