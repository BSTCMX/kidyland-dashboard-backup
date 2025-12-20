<script lang="ts">
  /**
   * ExportFormatSelector component - Step 3 of export wizard.
   * 
   * Allows users to select the export format (Excel or PDF).
   */
  import { createEventDispatcher } from "svelte";
  import { FileSpreadsheet, FileText } from "lucide-svelte";
  import type { ExportFormat } from "$lib/utils/export-helpers";

  const dispatch = createEventDispatcher<{
    change: { format: ExportFormat };
  }>();

  export let selectedFormat: ExportFormat = "excel";

  function selectFormat(format: ExportFormat) {
    selectedFormat = format;
    dispatch("change", { format });
  }
</script>

<div class="format-selector">
  <div class="selector-header">
    <p class="helper-text">
      Selecciona el formato en el que deseas exportar el reporte.
    </p>
  </div>

  <div class="format-options">
    <button
      type="button"
      class="format-option"
      class:selected={selectedFormat === "excel"}
      on:click={() => selectFormat("excel")}
    >
      <div class="format-icon">
        <FileSpreadsheet size={48} strokeWidth={1.5} />
      </div>
      <h3 class="format-title">Excel (.xlsx)</h3>
      <p class="format-description">
        Formato ideal para análisis y manipulación de datos. Incluye múltiples hojas organizadas por sección.
      </p>
      <ul class="format-features">
        <li>Múltiples hojas de cálculo</li>
        <li>Fácil de editar y filtrar</li>
        <li>Compatible con Excel y Google Sheets</li>
      </ul>
    </button>

    <button
      type="button"
      class="format-option"
      class:selected={selectedFormat === "pdf"}
      on:click={() => selectFormat("pdf")}
    >
      <div class="format-icon">
        <FileText size={48} strokeWidth={1.5} />
      </div>
      <h3 class="format-title">PDF (.pdf)</h3>
      <p class="format-description">
        Formato ideal para presentaciones y compartir. Diseño optimizado para lectura e impresión.
      </p>
      <ul class="format-features">
        <li>Formato de documento profesional</li>
        <li>Listo para imprimir o compartir</li>
        <li>Diseño visual optimizado</li>
      </ul>
    </button>
  </div>
</div>

<style>
  .format-selector {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-lg);
  }

  .selector-header {
    padding: var(--spacing-md);
    background: rgba(0, 147, 247, 0.05);
    border-radius: var(--radius-md);
    border: 1px solid rgba(0, 147, 247, 0.2);
  }

  .helper-text {
    margin: 0;
    font-size: var(--text-sm);
    color: var(--text-secondary, #808097);
    line-height: 1.5;
  }

  .format-options {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: var(--spacing-lg);
  }

  .format-option {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: var(--spacing-md);
    padding: var(--spacing-xl);
    border: 3px solid var(--border-primary);
    border-radius: var(--radius-lg);
    background: var(--theme-bg-primary);
    cursor: pointer;
    transition: all 0.2s;
    text-align: left;
    min-height: 300px;
  }

  .format-option:hover {
    border-color: var(--accent-primary);
    transform: translateY(-4px);
    box-shadow: 0 8px 16px rgba(0, 0, 0, 0.15);
  }

  .format-option.selected {
    border-color: var(--accent-primary);
    border-width: 4px;
    background: rgba(0, 147, 247, 0.1);
    box-shadow: 0 0 0 4px rgba(0, 147, 247, 0.2);
  }

  .format-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 64px;
    height: 64px;
    border-radius: var(--radius-md);
    background: rgba(0, 147, 247, 0.1);
    color: var(--accent-primary);
  }

  .format-option.selected .format-icon {
    background: rgba(0, 147, 247, 0.2);
  }

  .format-title {
    font-size: var(--text-xl);
    font-weight: 700;
    color: var(--text-primary);
    margin: 0;
  }

  .format-description {
    font-size: var(--text-base);
    color: var(--text-secondary);
    margin: 0;
    line-height: 1.6;
  }

  .format-features {
    list-style: none;
    padding: 0;
    margin: 0;
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xs);
    width: 100%;
  }

  .format-features li {
    font-size: var(--text-sm);
    color: var(--text-secondary, #808097);
    padding-left: var(--spacing-md);
    position: relative;
  }

  .format-features li::before {
    content: "✓";
    position: absolute;
    left: 0;
    color: var(--accent-success);
    font-weight: 700;
  }

  /* Responsive */
  @media (max-width: 768px) {
    .format-options {
      grid-template-columns: 1fr;
      gap: var(--spacing-md);
    }

    .format-option {
      min-height: auto;
      padding: var(--spacing-lg);
    }
  }

  /* Prevent hover transform on touch devices */
  @media (hover: none) and (pointer: coarse) {
    .format-option:hover {
      transform: none;
      box-shadow: 0 8px 16px rgba(0, 0, 0, 0.15);
    }
  }
</style>

