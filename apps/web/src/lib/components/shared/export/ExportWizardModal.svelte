<script lang="ts">
  /**
   * ExportWizardModal component - Main wizard modal for advanced export functionality.
   * 
   * Implements multi-step export flow:
   * Step 1: Section Selection
   * Step 2: Preview
   * Step 3: Format Selection
   * Step 4: Confirmation
   */
  import { Modal } from "@kidyland/ui";
  import WizardStep from "../WizardStep.svelte";
  import ExportSectionSelector from "./ExportSectionSelector.svelte";
  import ExportPreviewPanel from "./ExportPreviewPanel.svelte";
  import ExportFormatSelector from "./ExportFormatSelector.svelte";
  import ExportConfirmation from "./ExportConfirmation.svelte";
  import type {
    ExportReportType,
    ExportSection,
    ExportFormat,
    ExportConfiguration
  } from "$lib/utils/export-helpers";
  import { generateSmartDefaults } from "$lib/utils/export-helpers";
  import { createEventDispatcher } from "svelte";

  const dispatch = createEventDispatcher<{
    export: { config: ExportConfiguration };
    cancel: null;
    close: null;
  }>();

  export let open: boolean = false;
  export let reportType: ExportReportType = "dashboard";
  export let activeTab: string | undefined = undefined;
  export let activeSubTab: string | undefined = undefined;
  export let sucursalId: string | undefined = undefined;
  export let startDate: string | undefined = undefined;
  export let endDate: string | undefined = undefined;
  export let preSelectedFormat: ExportFormat | undefined = undefined;

  type WizardStepType = "sections" | "preview" | "format" | "confirmation";

  const steps: Array<{ id: WizardStepType; title: string; description?: string }> = [
    { 
      id: "sections", 
      title: "Seleccionar Secciones", 
      description: "Elige qué secciones incluir en el reporte" 
    },
    { 
      id: "preview", 
      title: "Vista Previa", 
      description: "Revisa la configuración del reporte" 
    },
    { 
      id: "format", 
      title: "Formato", 
      description: "Selecciona el formato de exportación" 
    },
    { 
      id: "confirmation", 
      title: "Confirmar Exportación", 
      description: "Confirma y genera el reporte" 
    }
  ];

  // Export configuration state
  let config: ExportConfiguration = generateSmartDefaults(reportType, activeTab, activeSubTab, preSelectedFormat);

  // Current step
  let currentStep: WizardStepType = "sections";

  // Initialize config when modal opens
  $: if (open) {
    config = generateSmartDefaults(reportType, activeTab, activeSubTab, preSelectedFormat);
    if (sucursalId) config.sucursalId = sucursalId;
    if (startDate) config.startDate = startDate;
    if (endDate) config.endDate = endDate;
    currentStep = "sections";
  }

  // Get effective steps (exclude format step if format is pre-selected)
  $: effectiveSteps = preSelectedFormat 
    ? steps.filter(s => s.id !== "format")
    : steps;

  // Reactive: Update index and data when currentStep changes
  // Use effectiveSteps for step number calculation
  $: currentStepIndex = effectiveSteps.findIndex((s) => s.id === currentStep);
  $: currentStepData = currentStepIndex >= 0 ? effectiveSteps[currentStepIndex] : effectiveSteps[0];

  // Reactive: Compute canGoNext based on current step
  $: canGoNext = (() => {
    switch (currentStep) {
      case "sections":
        return config.sections.length > 0;
      case "preview":
        return true;
      case "format":
        // If format is pre-selected, it's always valid
        return config.format !== undefined || !!preSelectedFormat;
      case "confirmation":
        return false; // Can't go forward from confirmation
      default:
        return false;
    }
  })();

  function handleNext() {
    const nextIndex = currentStepIndex + 1;
    if (nextIndex < effectiveSteps.length) {
      // Use effectiveSteps to ensure correct navigation
      currentStep = effectiveSteps[nextIndex].id;
      
      // If format is pre-selected, ensure it's set in config
      if (preSelectedFormat && currentStep !== "format") {
        config.format = preSelectedFormat;
      }
    }
  }

  function handleBack() {
    const prevIndex = currentStepIndex - 1;
    if (prevIndex >= 0) {
      // Use effectiveSteps to ensure correct navigation
      currentStep = effectiveSteps[prevIndex].id;
    }
  }

  function handleSectionsChange(event: CustomEvent<{ sections: ExportSection[] }>) {
    config.sections = event.detail.sections;
  }

  function handleFormatChange(event: CustomEvent<{ format: ExportFormat }>) {
    config.format = event.detail.format;
  }

  function handleConfirm() {
    dispatch("export", { config });
    open = false;
  }

  function handleCancel() {
    dispatch("cancel");
    open = false;
  }

  function handleClose() {
    dispatch("close");
    open = false;
  }
</script>

<Modal {open} title="Exportar Reporte" size="lg" on:close={handleClose}>
  <div class="export-wizard">
    {#if currentStep === "sections"}
      <WizardStep
        stepNumber={currentStepIndex + 1}
        totalSteps={effectiveSteps.length}
        title={currentStepData.title}
        description={currentStepData.description}
        canGoNext={canGoNext}
        canGoBack={false}
        on:next={handleNext}
        on:back={handleBack}
      >
        <ExportSectionSelector
          reportType={reportType}
          selectedSections={config.sections}
          includePredictions={config.includePredictions}
          on:change={handleSectionsChange}
          on:predictionsChange={(e) => {
            config.includePredictions = e.detail.include;
          }}
        />
      </WizardStep>

    {:else if currentStep === "preview"}
      <WizardStep
        stepNumber={currentStepIndex + 1}
        totalSteps={effectiveSteps.length}
        title={currentStepData.title}
        description={currentStepData.description}
        canGoNext={canGoNext}
        on:next={handleNext}
        on:back={handleBack}
      >
        <ExportPreviewPanel {config} />
      </WizardStep>

    {:else if currentStep === "format"}
      <WizardStep
        stepNumber={currentStepIndex + 1}
        totalSteps={effectiveSteps.length}
        title={currentStepData.title}
        description={preSelectedFormat ? 
          `Formato pre-seleccionado: ${preSelectedFormat.toUpperCase()}. Puedes cambiarlo si lo deseas.` : 
          currentStepData.description}
        canGoNext={canGoNext}
        on:next={handleNext}
        on:back={handleBack}
      >
        <ExportFormatSelector
          selectedFormat={config.format}
          on:change={handleFormatChange}
        />
      </WizardStep>

    {:else if currentStep === "confirmation"}
      <WizardStep
        stepNumber={currentStepIndex + 1}
        totalSteps={effectiveSteps.length}
        title={currentStepData.title}
        description={currentStepData.description}
        canGoNext={false}
        showNavigation={false}
      >
        <ExportConfirmation
          {config}
          on:confirm={handleConfirm}
          on:cancel={handleCancel}
        />
      </WizardStep>
    {/if}
  </div>
</Modal>

<style>
  .export-wizard {
    width: 100%;
    display: flex;
    flex-direction: column;
    min-height: 0; /* Critical: allows flex children to scroll */
    height: 100%; /* Take full modal content height */
  }
</style>

