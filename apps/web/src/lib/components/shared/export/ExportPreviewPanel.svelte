<script lang="ts">
  /**
   * ExportPreviewPanel component - Step 2 of export wizard.
   * 
   * Displays a preview of the export configuration.
   */
  import type { ExportConfiguration, ExportSection } from "$lib/utils/export-helpers";
  import { getAvailableSections } from "$lib/utils/export-helpers";
  import { FileText, Download, Calendar, Building2, Filter } from "lucide-svelte";

  export let config: ExportConfiguration;

  $: availableSections = getAvailableSections(config.reportType);
  $: selectedSectionsInfo = availableSections.filter(s => config.sections.includes(s.id));

  function formatDate(dateStr: string | undefined): string {
    if (!dateStr) return "No especificada";
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString("es-ES", {
        year: "numeric",
        month: "long",
        day: "numeric"
      });
    } catch {
      return dateStr;
    }
  }

  function getSectionLabel(sectionId: ExportSection): string {
    const section = availableSections.find(s => s.id === sectionId);
    return section?.label || sectionId;
  }
</script>

<div class="preview-panel">
  <div class="preview-header">
    <h3>Vista Previa de la Configuración</h3>
    <p class="preview-description">
      Revisa la configuración antes de continuar. Puedes volver atrás para hacer cambios.
    </p>
  </div>

  <div class="preview-content">
    <div class="preview-section">
      <div class="section-header">
        <FileText size={20} />
        <span>Información General</span>
      </div>
      <div class="section-body">
        <div class="info-row">
          <span class="info-label">Tipo de Reporte:</span>
          <span class="info-value">{config.reportType}</span>
        </div>
        <div class="info-row">
          <span class="info-label">Formato:</span>
          <span class="info-value">{config.format.toUpperCase()}</span>
        </div>
        {#if config.module}
          <div class="info-row">
            <span class="info-label">Módulo:</span>
            <span class="info-value">{config.module}</span>
          </div>
        {/if}
      </div>
    </div>

    <div class="preview-section">
      <div class="section-header">
        <Download size={20} />
        <span>Secciones Seleccionadas ({config.sections.length})</span>
      </div>
      <div class="section-body">
        {#if config.sections.length === 0}
          <p class="empty-state">No hay secciones seleccionadas</p>
        {:else}
          <div class="sections-grid">
            {#each selectedSectionsInfo as section}
              <div class="section-badge">
                {section.label}
              </div>
            {/each}
          </div>
        {/if}
        {#if config.includePredictions}
          <div class="predictions-badge">
            <span>✓ Predicciones y Análisis incluidos</span>
          </div>
        {/if}
      </div>
    </div>

    {#if config.sucursalId || config.startDate || config.endDate}
      <div class="preview-section">
        <div class="section-header">
          <Filter size={20} />
          <span>Filtros</span>
        </div>
        <div class="section-body">
          {#if config.sucursalId}
            <div class="info-row">
              <span class="info-label">
                <Building2 size={16} />
                Sucursal:
              </span>
              <span class="info-value">{config.sucursalId}</span>
            </div>
          {/if}
          {#if config.startDate}
            <div class="info-row">
              <span class="info-label">
                <Calendar size={16} />
                Fecha Inicio:
              </span>
              <span class="info-value">{formatDate(config.startDate)}</span>
            </div>
          {/if}
          {#if config.endDate}
            <div class="info-row">
              <span class="info-label">
                <Calendar size={16} />
                Fecha Fin:
              </span>
              <span class="info-value">{formatDate(config.endDate)}</span>
            </div>
          {/if}
        </div>
      </div>
    {/if}
  </div>
</div>

<style>
  .preview-panel {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-lg);
  }

  .preview-header {
    padding: var(--spacing-md);
    background: rgba(0, 147, 247, 0.05);
    border-radius: var(--radius-md);
    border: 1px solid rgba(0, 147, 247, 0.2);
  }

  .preview-header h3 {
    margin: 0 0 var(--spacing-xs) 0;
    font-size: var(--text-xl);
    font-weight: 700;
    color: var(--text-primary);
  }

  .preview-description {
    margin: 0;
    font-size: var(--text-sm);
    color: var(--text-secondary);
    line-height: 1.5;
  }

  .preview-content {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-md);
  }

  .preview-section {
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
    overflow: hidden;
  }

  .section-header {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    padding: var(--spacing-md);
    background: var(--theme-bg-secondary);
    border-bottom: 1px solid var(--border-primary);
    font-weight: 600;
    font-size: var(--text-base);
    color: var(--text-primary);
  }

  .section-body {
    padding: var(--spacing-md);
    display: flex;
    flex-direction: column;
    gap: var(--spacing-sm);
  }

  .info-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: var(--spacing-md);
    padding: var(--spacing-sm) 0;
  }

  .info-label {
    display: flex;
    align-items: center;
    gap: var(--spacing-xs);
    font-size: var(--text-sm);
    color: var(--text-secondary);
    font-weight: 500;
  }

  .info-value {
    font-size: var(--text-base);
    color: var(--text-primary);
    font-weight: 600;
    text-align: right;
  }

  .sections-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
    gap: var(--spacing-sm);
  }

  .section-badge {
    padding: var(--spacing-sm) var(--spacing-md);
    background: rgba(0, 147, 247, 0.1);
    border: 1px solid rgba(0, 147, 247, 0.3);
    border-radius: var(--radius-sm);
    font-size: var(--text-sm);
    font-weight: 500;
    color: var(--accent-primary);
    text-align: center;
  }

  .predictions-badge {
    margin-top: var(--spacing-xs);
    padding: var(--spacing-sm) var(--spacing-md);
    background: rgba(34, 197, 94, 0.1);
    border: 1px solid rgba(34, 197, 94, 0.3);
    border-radius: var(--radius-sm);
    font-size: var(--text-sm);
    font-weight: 500;
    color: var(--accent-success);
  }

  .empty-state {
    margin: 0;
    padding: var(--spacing-md);
    text-align: center;
    color: var(--text-secondary);
    font-size: var(--text-sm);
    font-style: italic;
  }

  /* Responsive */
  @media (max-width: 768px) {
    .info-row {
      flex-direction: column;
      align-items: flex-start;
      gap: var(--spacing-xs);
    }

    .info-value {
      text-align: left;
    }

    .sections-grid {
      grid-template-columns: 1fr;
    }
  }
</style>

