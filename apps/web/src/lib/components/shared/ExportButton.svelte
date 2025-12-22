<script lang="ts">
  /**
   * ExportButton component - Reusable button for exporting reports.
   * 
   * Supports Excel and PDF exports with progress indicators.
   * Can use simple export (legacy) or advanced wizard for granular control.
   * Integrates with backend export endpoints.
   */
  import { Button } from "@kidyland/ui";
  import { token } from "$lib/stores/auth";
  import { downloadFromApi, supportsAutoDownload } from "$lib/utils/download";
  import { getApiUrl } from "$lib/utils/api-config";
  import { createEventDispatcher } from "svelte";
  import ExportWizardModal from "./export/ExportWizardModal.svelte";
  import type {
    ExportReportType,
    ExportConfiguration
  } from "$lib/utils/export-helpers";
  import { buildExportUrl, generateExportFilename } from "$lib/utils/export-helpers";

  export let exportType: "excel" | "pdf" = "excel";
  export let reportType: string = "dashboard";
  export let sucursalId: string | undefined = undefined;
  export let startDate: string | undefined = undefined;
  export let endDate: string | undefined = undefined;
  export let label: string | undefined = undefined;
  export let variant: "primary" | "secondary" | "danger" | "brutalist" | "brutalist-danger" = "primary";
  export let size: "small" | "medium" | "large" = "medium";
  
  // Advanced wizard mode
  export let useWizard: boolean = false;
  export let activeTab: string | undefined = undefined;
  export let activeSubTab: string | undefined = undefined;
  export let module: "recepcion" | "kidibar" | "all" | undefined = undefined;

  const dispatch = createEventDispatcher<{
    start: null;
    success: null;
    error: { error: string };
    export: { config: ExportConfiguration };
  }>();

  let loading = false;
  let error: string | null = null;
  let showWizard = false;

  // Reactive type conversion: convert string to ExportReportType for wizard
  // This ensures type safety while maintaining backward compatibility
  // Declare variable first, then assign reactively to avoid scope issues
  let validReportType: ExportReportType = "dashboard";
  $: validReportType = reportType as ExportReportType;

  // Pre-select format based on exportType when using wizard
  $: preSelectedFormatForWizard = useWizard ? exportType : undefined;

  $: displayLabel = label || (exportType === "excel" ? "Exportar Excel" : "Exportar PDF");
  $: fileExtension = exportType === "excel" ? "xlsx" : "pdf";

  async function handleExport() {
    // If wizard mode is enabled, show wizard instead
    if (useWizard) {
      showWizard = true;
      return;
    }

    // Legacy simple export (backward compatible)
    loading = true;
    error = null;
    dispatch("start");

    try {
      // Build URL with query params
      const params = new URLSearchParams();
      params.append("report_type", reportType);
      
      if (sucursalId) {
        params.append("sucursal_id", sucursalId);
      }
      if (startDate) {
        params.append("start_date", startDate);
      }
      if (endDate) {
        params.append("end_date", endDate);
      }

      // Build absolute URL using API base URL
      const apiUrl = getApiUrl();
      const url = `${apiUrl}/exports/${exportType}?${params.toString()}`;
      
      // Generate filename
      const dateStr = new Date().toISOString().split("T")[0].replace(/-/g, "");
      const filename = `kidyland_${reportType}_${dateStr}.${fileExtension}`;

      // Download file
      await downloadFromApi(url, filename, $token);

      dispatch("success");
    } catch (e: any) {
      error = e.message || `Error al exportar ${exportType.toUpperCase()}`;
      dispatch("error", { error });
      
      // Show error to user
      if (!supportsAutoDownload()) {
        error = "Tu navegador puede requerir que permitas descargas. Por favor, intenta de nuevo.";
      }
    } finally {
      loading = false;
    }
  }

  async function handleWizardExport(event: CustomEvent<{ config: ExportConfiguration }>) {
    const config = event.detail.config;
    loading = true;
    error = null;
    dispatch("start");
    dispatch("export", { config });

    try {
      // Build export URL using helper
      const apiUrl = getApiUrl();
      const url = buildExportUrl(config, apiUrl);
      
      // Generate filename using helper
      const filename = generateExportFilename(config);

      // Download file
      await downloadFromApi(url, filename, $token);

      dispatch("success");
      showWizard = false;
    } catch (e: any) {
      error = e.message || `Error al exportar ${config.format.toUpperCase()}`;
      dispatch("error", { error });
      
      // Show error to user
      if (!supportsAutoDownload()) {
        error = "Tu navegador puede requerir que permitas descargas. Por favor, intenta de nuevo.";
      }
    } finally {
      loading = false;
    }
  }

  function handleWizardCancel() {
    showWizard = false;
  }

  function handleWizardClose() {
    showWizard = false;
  }
</script>

<div class="export-button-container">
  <Button
    variant={variant}
    size={size}
    on:click={handleExport}
    disabled={loading}
  >
    {#if loading}
      <span class="loading-spinner">⏳</span> Generando...
    {:else if $$slots.default}
      <slot />
    {:else}
      {displayLabel}
    {/if}
  </Button>

  {#if error}
    <div class="error-message" role="alert">
      {error}
    </div>
  {/if}
</div>

{#if useWizard}
  <ExportWizardModal
    open={showWizard}
    reportType={validReportType}
    {activeTab}
    {activeSubTab}
    {sucursalId}
    {startDate}
    {endDate}
    preSelectedFormat={preSelectedFormatForWizard}
    on:export={handleWizardExport}
    on:cancel={handleWizardCancel}
    on:close={handleWizardClose}
  />
{/if}

<style>
  .export-button-container {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xs);
    align-items: flex-start;
  }

  .loading-spinner {
    display: inline-block;
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    from {
      transform: rotate(0deg);
    }
    to {
      transform: rotate(360deg);
    }
  }

  .error-message {
    font-size: var(--text-sm);
    color: var(--accent-danger);
    padding: var(--spacing-xs) var(--spacing-sm);
    background: rgba(211, 5, 84, 0.1);
    border-radius: var(--radius-sm);
    border: 1px solid var(--accent-danger);
    max-width: 300px;
  }

  @media (max-width: 768px) {
    .export-button-container {
      width: 100%;
    }

    .export-button-container :global(button) {
      width: 100%;
    }
  }
</style>

