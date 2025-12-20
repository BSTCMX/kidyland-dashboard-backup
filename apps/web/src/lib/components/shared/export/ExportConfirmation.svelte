<script lang="ts">
  /**
   * ExportConfirmation component - Step 4 of export wizard.
   * 
   * Final confirmation step before export.
   */
  import { Button } from "@kidyland/ui";
  import { createEventDispatcher } from "svelte";
  import { Download, X, CheckCircle } from "lucide-svelte";
  import type { ExportConfiguration } from "$lib/utils/export-helpers";
  import { generateExportFilename } from "$lib/utils/export-helpers";

  const dispatch = createEventDispatcher<{
    confirm: null;
    cancel: null;
  }>();

  export let config: ExportConfiguration;

  $: filename = generateExportFilename(config);

  function handleConfirm() {
    dispatch("confirm");
  }

  function handleCancel() {
    dispatch("cancel");
  }
</script>

<div class="confirmation-panel">
  <div class="confirmation-header">
    <div class="success-icon">
      <CheckCircle size={48} />
    </div>
    <h3>¿Confirmar Exportación?</h3>
    <p class="confirmation-description">
      El reporte se generará con la siguiente configuración y se descargará automáticamente.
    </p>
  </div>

  <div class="confirmation-summary">
    <div class="summary-item">
      <span class="summary-label">Nombre del archivo:</span>
      <span class="summary-value">{filename}</span>
    </div>
    <div class="summary-item">
      <span class="summary-label">Formato:</span>
      <span class="summary-value">{config.format.toUpperCase()}</span>
    </div>
    <div class="summary-item">
      <span class="summary-label">Secciones:</span>
      <span class="summary-value">{config.sections.length} sección(es) seleccionada(s)</span>
    </div>
    {#if config.includePredictions}
      <div class="summary-item">
        <span class="summary-label">Predicciones:</span>
        <span class="summary-value">Incluidas</span>
      </div>
    {/if}
  </div>

  <div class="confirmation-actions">
    <Button
      variant="secondary"
      size="large"
      on:click={handleCancel}
    >
      <X size={18} strokeWidth={2} />
      Cancelar
    </Button>

    <Button
      variant="primary"
      size="large"
      on:click={handleConfirm}
    >
      <Download size={18} strokeWidth={2} />
      Generar y Descargar
    </Button>
  </div>
</div>

<style>
  .confirmation-panel {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xl);
    align-items: center;
    text-align: center;
    padding: var(--spacing-lg) 0;
  }

  .confirmation-header {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: var(--spacing-md);
  }

  .success-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 80px;
    height: 80px;
    border-radius: 50%;
    background: rgba(34, 197, 94, 0.1);
    color: var(--accent-success);
    margin-bottom: var(--spacing-sm);
  }

  .confirmation-header h3 {
    margin: 0;
    font-size: var(--text-2xl);
    font-weight: 700;
    color: var(--text-primary);
  }

  .confirmation-description {
    margin: 0;
    font-size: var(--text-base);
    color: var(--text-secondary, #808097);
    line-height: 1.6;
    max-width: 500px;
  }

  .confirmation-summary {
    width: 100%;
    max-width: 500px;
    display: flex;
    flex-direction: column;
    gap: var(--spacing-md);
    padding: var(--spacing-lg);
    background: var(--theme-bg-secondary);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
  }

  .summary-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: var(--spacing-md);
    padding: var(--spacing-sm) 0;
    border-bottom: 1px solid var(--border-primary);
  }

  .summary-item:last-child {
    border-bottom: none;
  }

  .summary-label {
    font-size: var(--text-sm);
    color: var(--text-secondary, #808097);
    font-weight: 500;
  }

  .summary-value {
    font-size: var(--text-base);
    color: var(--text-primary);
    font-weight: 600;
    text-align: right;
  }

  .confirmation-actions {
    display: flex;
    gap: var(--spacing-md);
    width: 100%;
    max-width: 500px;
  }

  /* Responsive */
  @media (max-width: 768px) {
    .confirmation-summary {
      padding: var(--spacing-md);
    }

    .summary-item {
      flex-direction: column;
      align-items: flex-start;
      gap: var(--spacing-xs);
    }

    .summary-value {
      text-align: left;
    }

    .confirmation-actions {
      flex-direction: column;
    }

    .confirmation-actions :global(button) {
      width: 100%;
    }
  }
</style>

