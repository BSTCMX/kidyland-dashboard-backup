<script lang="ts">
  /**
   * ExportSectionSelector component - Step 1 of export wizard.
   * 
   * Allows users to select which sections to include in the export.
   * Supports master checkboxes for categories and individual section selection.
   */
  import { createEventDispatcher } from "svelte";
  import { onMount } from "svelte";
  import { Check, Square, ChevronDown } from "lucide-svelte";
  import type {
    ExportReportType,
    ExportSection,
    ExportSectionInfo
  } from "$lib/utils/export-helpers";
  import { getAvailableSections } from "$lib/utils/export-helpers";
  // Import stores to make availableSections reactive to their changes
  import { metricsStore } from "$lib/stores/metrics";
  import { forecastingStore } from "$lib/stores/reports";

  const dispatch = createEventDispatcher<{
    change: { sections: ExportSection[] };
    predictionsChange: { include: boolean };
  }>();

  export let reportType: ExportReportType;
  export let selectedSections: ExportSection[] = [];
  export let includePredictions: boolean = false;

  // Automatically sync includePredictions with selectedSections
  // When "predictions" section is selected/deselected, update includePredictions
  // This reactive statement only dispatches events, doesn't modify props directly
  $: {
    const hasPredictionsSection = selectedSections.includes("predictions");
    if (hasPredictionsSection !== includePredictions) {
      // Dispatch event to parent to update includePredictions
      dispatch("predictionsChange", { include: hasPredictionsSection });
    }
  }

  // Track expanded state for each category (accordion functionality)
  let expandedCategories: Record<string, boolean> = {};
  let windowWidth = 1024;
  // Track previous categoryKeys to detect changes (Pattern: ServiceForm/ProductForm)
  let prevCategoryKeys: string[] = [];

  // Initialize window width and handle resize
  onMount(() => {
    if (typeof window !== 'undefined') {
      windowWidth = window.innerWidth;
      const handleResize = () => {
        windowWidth = window.innerWidth;
      };
      window.addEventListener('resize', handleResize);
      return () => window.removeEventListener('resize', handleResize);
    }
    return undefined;
  });

  // Get available sections for this report type
  // Make it reactive to changes in metricsStore and forecastingStore
  // This ensures that when predictions are generated, the sections list updates automatically
  // Access stores to establish reactivity dependency - when they change, this will re-run
  // getAvailableSections() will call checkPredictionsAvailable() which reads from the stores
  $: availableSections = (() => {
    // Access stores to establish reactivity dependency
    // When metricsStore.predictions or forecastingStore changes, this will re-run
    $metricsStore; // Establish dependency on metricsStore
    $forecastingStore; // Establish dependency on forecastingStore
    
    // Re-execute getAvailableSections when stores or reportType change
    return getAvailableSections(reportType);
  })();
  
  // Group sections by category
  $: sectionsByCategory = availableSections.reduce((acc, section) => {
    const category = section.category || "other";
    if (!acc[category]) {
      acc[category] = [];
    }
    acc[category].push(section);
    return acc;
  }, {} as Record<string, ExportSectionInfo[]>);

  $: categoryKeys = Object.keys(sectionsByCategory);

  // Responsive: Desktop (min-width: 769px) = all expanded, Mobile (max-width: 768px) = all collapsed
  $: isMobile = windowWidth <= 768;
  
  // Initialize expanded state reactively when categoryKeys change (Pattern: ServiceForm/ProductForm)
  // Desktop: all categories expanded by default
  // Mobile: all categories collapsed by default
  // This pattern ensures initialization happens when:
  // 1. categoryKeys changes (e.g., when predictions become available)
  // 2. New categories are added that aren't in expandedCategories
  $: {
    if (categoryKeys.length > 0) {
      // Check if categoryKeys actually changed (compare sorted arrays)
      const keysChanged = JSON.stringify(categoryKeys.sort()) !== JSON.stringify(prevCategoryKeys.sort());
      
      // Check if any category is missing from expandedCategories
      const hasMissingCategories = categoryKeys.some(cat => !(cat in expandedCategories));
      
      // Only update if keys changed or there are missing categories
      if (keysChanged || hasMissingCategories) {
        const shouldExpandAll = !isMobile; // Desktop: true, Mobile: false
        const updated = { ...expandedCategories };
        
        // Initialize all categories: new ones get default, existing ones keep their state
        categoryKeys.forEach((category) => {
          if (!(category in updated)) {
            // New category: initialize with default based on screen size
            updated[category] = shouldExpandAll;
          }
          // Existing categories: keep their current state (preserve user's manual toggles)
        });
        
        expandedCategories = updated;
        prevCategoryKeys = [...categoryKeys];
      }
    }
  }

  // Track master checkbox states for each category
  $: categoryStates = categoryKeys.reduce((acc, category) => {
    const categorySections = sectionsByCategory[category];
    const allSelected = categorySections.every(s => selectedSections.includes(s.id));
    const someSelected = categorySections.some(s => selectedSections.includes(s.id));
    
    acc[category] = {
      all: allSelected,
      some: someSelected && !allSelected
    };
    return acc;
  }, {} as Record<string, { all: boolean; some: boolean }>);

  function toggleSection(sectionId: ExportSection) {
    if (selectedSections.includes(sectionId)) {
      selectedSections = selectedSections.filter(id => id !== sectionId);
    } else {
      selectedSections = [...selectedSections, sectionId];
    }
    dispatch("change", { sections: selectedSections });
    // includePredictions will be updated automatically via reactive statement
  }

  // Toggle category selection (select/deselect all sections in category)
  function toggleCategorySelection(category: string, event?: MouseEvent) {
    if (event) {
      event.stopPropagation(); // Prevent expansion toggle
    }
    const categorySections = sectionsByCategory[category];
    const allSelected = categorySections.every(s => selectedSections.includes(s.id));
    
    if (allSelected) {
      // Deselect all in category
      selectedSections = selectedSections.filter(
        id => !categorySections.some(s => s.id === id)
      );
    } else {
      // Select all in category
      const newSections = categorySections
        .filter(s => s.available && !selectedSections.includes(s.id))
        .map(s => s.id);
      selectedSections = [...selectedSections, ...newSections];
    }
    dispatch("change", { sections: selectedSections });
    // includePredictions will be updated automatically via reactive statement
  }

  // Toggle category expansion/collapse (accordion functionality)
  function toggleCategoryExpansion(category: string) {
    expandedCategories[category] = !expandedCategories[category];
    // Trigger reactivity
    expandedCategories = { ...expandedCategories };
  }

  // Helper: Check if category is expanded
  // Removed fallback: always trust expandedCategories state
  // If category doesn't exist in expandedCategories, return false (collapsed)
  // The reactive initialization above will set it properly
  function isCategoryExpanded(category: string): boolean {
    // Explicitly check if category exists in expandedCategories
    // No fallback: let the reactive initialization handle defaults
    if (category in expandedCategories) {
      return expandedCategories[category];
    }
    // If not initialized yet, return false (collapsed by default)
    // This will be corrected by the reactive initialization above
    return false;
  }


  function getCategoryLabel(category: string): string {
    const labels: Record<string, string> = {
      dashboard: "Dashboard",
      reports: "Reportes Avanzados",
      predictions: "Predicciones"
    };
    return labels[category] || category;
  }
</script>

<div class="section-selector">
  <div class="selector-header">
    <p class="helper-text">
      Selecciona las secciones que deseas incluir en el reporte. Puedes usar las casillas maestras para seleccionar todas las secciones de una categoría.
    </p>
  </div>

  <div class="sections-list">
    {#each categoryKeys as category}
      {@const categorySections = sectionsByCategory[category]}
      {@const categoryState = categoryStates[category]}
      
      {@const isExpanded = isCategoryExpanded(category)}
      
      <div class="category-group">
        <button
          type="button"
          class="category-header"
          on:click={() => toggleCategoryExpansion(category)}
          title={isExpanded ? "Colapsar categoría" : "Expandir categoría"}
        >
          <div 
            class="checkbox-wrapper"
            on:click|stopPropagation={(e) => toggleCategorySelection(category, e)}
            title={categoryState.all ? "Deseleccionar todo" : "Seleccionar todo"}
            role="button"
            tabindex="0"
            on:keydown|stopPropagation={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                toggleCategorySelection(category);
              }
            }}
          >
            {#if categoryState.all}
              <Check size={18} class="check-icon" />
            {:else if categoryState.some}
              <div class="indeterminate-indicator"></div>
            {:else}
              <Square size={18} class="square-icon" />
            {/if}
          </div>
          <span class="category-label">{getCategoryLabel(category)}</span>
          <span class="category-count">
            ({categorySections.filter(s => selectedSections.includes(s.id)).length} / {categorySections.length})
          </span>
          <span class="chevron-icon" class:rotated={isExpanded}>
            <ChevronDown size={18} />
          </span>
        </button>

        <div class="category-sections" class:expanded={isExpanded}>
          {#each categorySections as section}
            <label class="section-item" class:disabled={!section.available}>
              <input
                type="checkbox"
                checked={selectedSections.includes(section.id)}
                disabled={!section.available}
                on:change={() => toggleSection(section.id)}
              />
              <div class="section-info">
                <span class="section-label">{section.label}</span>
                {#if section.description}
                  <span class="section-description">{section.description}</span>
                {/if}
              </div>
            </label>
          {/each}
        </div>
      </div>
    {/each}
  </div>
</div>

<style>
  .section-selector {
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
    color: var(--text-secondary);
    line-height: 1.5;
  }

  .sections-list {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-md);
    /* Removed max-height and overflow-y: let modal handle scroll */
    /* Modal's .modal-content already has overflow-y: auto */
  }

  .category-group {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-sm);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
    overflow: hidden;
  }

  .category-header {
    display: flex;
    align-items: center;
    gap: var(--spacing-md);
    padding: var(--spacing-md);
    background: var(--theme-bg-secondary);
    border: none;
    cursor: pointer;
    transition: all 0.2s;
    text-align: left;
  }

  .category-header:hover {
    background: var(--theme-bg-elevated);
  }

  .checkbox-wrapper {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 24px;
    height: 24px;
    border: 2px solid var(--border-primary);
    border-radius: var(--radius-sm);
    background: var(--theme-bg-primary);
    flex-shrink: 0;
    cursor: pointer;
    transition: all 0.2s;
  }

  .checkbox-wrapper:hover {
    background: var(--theme-bg-secondary);
    border-color: var(--accent-primary);
  }

  .check-icon {
    color: var(--accent-primary);
    stroke-width: 3;
  }

  .square-icon {
    color: var(--text-secondary);
    stroke-width: 1.5;
  }

  .indeterminate-indicator {
    width: 12px;
    height: 3px;
    background: var(--accent-primary);
    border-radius: 2px;
  }

  .category-label {
    font-weight: 600;
    font-size: var(--text-base);
    color: var(--text-primary);
    flex: 1;
  }

  .category-count {
    font-size: var(--text-sm);
    color: var(--text-secondary);
    font-weight: 500;
  }

  .chevron-icon {
    flex-shrink: 0;
    color: var(--text-secondary);
    transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }

  .chevron-icon.rotated {
    transform: rotate(180deg);
  }

  .category-sections {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xs);
    padding: var(--spacing-sm) var(--spacing-md);
    background: var(--theme-bg-primary);
    /* Accordion: Always visible on desktop, collapsible on mobile */
    max-height: 2000px; /* Large enough for all content */
    overflow: hidden;
    transition: max-height 0.3s cubic-bezier(0.4, 0, 0.2, 1), 
                padding 0.3s cubic-bezier(0.4, 0, 0.2, 1),
                opacity 0.2s ease;
    opacity: 1;
  }

  /* Collapsed state (mobile default) */
  .category-sections:not(.expanded) {
    max-height: 0;
    padding-top: 0;
    padding-bottom: 0;
    opacity: 0;
  }

  .section-item {
    display: flex;
    align-items: flex-start;
    gap: var(--spacing-md);
    padding: var(--spacing-sm);
    border-radius: var(--radius-sm);
    cursor: pointer;
    transition: all 0.2s;
  }

  .section-item:hover:not(.disabled) {
    background: var(--theme-bg-secondary);
  }

  .section-item.disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .section-item input[type="checkbox"] {
    margin-top: 2px;
    width: 20px;
    height: 20px;
    cursor: pointer;
    flex-shrink: 0;
    accent-color: var(--accent-primary, #0093f7);
  }

  .section-info {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xs);
    flex: 1;
  }

  .section-label {
    font-weight: 500;
    font-size: var(--text-base);
    color: var(--text-primary);
  }

  .section-description {
    font-size: var(--text-sm);
    color: var(--text-secondary, #808097);
    line-height: 1.4;
  }

  /* Removed custom scrollbar - using modal's scroll now */

  /* Responsive - Mobile */
  @media (max-width: 768px) {
    .category-header {
      padding: var(--spacing-sm) var(--spacing-md);
      /* Ensure touch target is large enough */
      min-height: 48px;
    }

    .category-sections {
      /* Accordion: collapsed by default on mobile */
      /* Default state (collapsed) handled by :not(.expanded) */
    }

    .category-sections.expanded {
      /* Expanded state on mobile */
      padding: var(--spacing-xs) var(--spacing-sm);
    }

    .checkbox-wrapper {
      /* Larger touch target on mobile */
      width: 28px;
      height: 28px;
      min-width: 28px;
      min-height: 28px;
    }

    .chevron-icon {
      /* Slightly larger on mobile for better visibility */
      width: 20px;
      height: 20px;
    }
  }

  /* Desktop: categories always expanded (no accordion behavior) */
  @media (min-width: 769px) {
    .category-sections {
      /* Force visible on desktop regardless of expanded state */
      max-height: 2000px !important;
      padding: var(--spacing-sm) var(--spacing-md) !important;
      opacity: 1 !important;
    }
  }
</style>

