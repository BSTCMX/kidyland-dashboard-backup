<script lang="ts">
  /**
   * LayoutEditor component - Manual layout configuration editor.
   * 
   * Allows users to manually adjust layout parameters (columns, padding, gap, fontSize)
   * with the option to reset to auto-calculation.
   */
  import { layoutEditorStore } from "$lib/stores/layout-editor";
  import { Button } from "@kidyland/ui";
  import { RotateCcw, Settings } from "lucide-svelte";

  let columnsValue = 3;
  let paddingValue = 40;
  let gapValue = 30;
  let fontSizeValue = 48;

  // Sync values with store
  $: {
    const store = $layoutEditorStore;
    if (store.mode === "manual") {
      if (store.manualConfig.columns !== null) columnsValue = store.manualConfig.columns;
      if (store.manualConfig.padding !== null) paddingValue = store.manualConfig.padding;
      if (store.manualConfig.gap !== null) gapValue = store.manualConfig.gap;
      if (store.manualConfig.fontSize !== null) fontSizeValue = store.manualConfig.fontSize;
    }
  }

  function handleModeToggle() {
    if ($layoutEditorStore.mode === "auto") {
      // Switch to manual mode with current values
      layoutEditorStore.setManualConfig({
        columns: columnsValue,
        padding: paddingValue,
        gap: gapValue,
        fontSize: fontSizeValue,
      });
    } else {
      // Switch to auto mode
      layoutEditorStore.resetToAuto();
    }
  }

  function handleReset() {
    layoutEditorStore.resetToAuto();
    // Reset to default values
    columnsValue = 3;
    paddingValue = 40;
    gapValue = 30;
    fontSizeValue = 48;
  }

  function handleColumnsChange(event: Event) {
    const value = parseInt((event.target as HTMLInputElement).value, 10);
    columnsValue = value;
    if ($layoutEditorStore.mode === "manual") {
      layoutEditorStore.setManualConfig({ columns: value });
    }
  }

  function handlePaddingChange(event: Event) {
    const value = parseInt((event.target as HTMLInputElement).value, 10);
    paddingValue = value;
    if ($layoutEditorStore.mode === "manual") {
      layoutEditorStore.setManualConfig({ padding: value });
    }
  }

  function handleGapChange(event: Event) {
    const value = parseInt((event.target as HTMLInputElement).value, 10);
    gapValue = value;
    if ($layoutEditorStore.mode === "manual") {
      layoutEditorStore.setManualConfig({ gap: value });
    }
  }

  function handleFontSizeChange(event: Event) {
    const value = parseInt((event.target as HTMLInputElement).value, 10);
    fontSizeValue = value;
    if ($layoutEditorStore.mode === "manual") {
      layoutEditorStore.setManualConfig({ fontSize: value });
    }
  }
</script>

<div class="layout-editor">
  <div class="editor-header">
    <h3 class="editor-title">
      <Settings size={20} strokeWidth={1.5} style="display: inline-block; vertical-align: middle; margin-right: 8px;" />
      Editor de Layout
    </h3>
    <div class="mode-toggle">
      <button
        class="toggle-button"
        class:active={$layoutEditorStore.mode === "manual"}
        on:click={handleModeToggle}
        type="button"
      >
        <span class="toggle-label">{$layoutEditorStore.mode === "auto" ? "Automático" : "Manual"}</span>
      </button>
    </div>
  </div>

  <div class="editor-controls">
    <!-- Columns Slider -->
    <div class="control-group">
      <label for="columns-slider" class="control-label">
        Columnas: <span class="value-display">{columnsValue}</span>
      </label>
      <input
        id="columns-slider"
        type="range"
        min="1"
        max="6"
        step="1"
        value={columnsValue}
        on:input={handleColumnsChange}
        disabled={$layoutEditorStore.mode === "auto"}
        class="slider"
      />
      <div class="slider-labels">
        <span>1</span>
        <span>6</span>
      </div>
    </div>

    <!-- Padding Slider -->
    <div class="control-group">
      <label for="padding-slider" class="control-label">
        Padding: <span class="value-display">{paddingValue}px</span>
      </label>
      <input
        id="padding-slider"
        type="range"
        min="10"
        max="100"
        step="5"
        value={paddingValue}
        on:input={handlePaddingChange}
        disabled={$layoutEditorStore.mode === "auto"}
        class="slider"
      />
      <div class="slider-labels">
        <span>10px</span>
        <span>100px</span>
      </div>
    </div>

    <!-- Gap Slider -->
    <div class="control-group">
      <label for="gap-slider" class="control-label">
        Espaciado: <span class="value-display">{gapValue}px</span>
      </label>
      <input
        id="gap-slider"
        type="range"
        min="5"
        max="50"
        step="5"
        value={gapValue}
        on:input={handleGapChange}
        disabled={$layoutEditorStore.mode === "auto"}
        class="slider"
      />
      <div class="slider-labels">
        <span>5px</span>
        <span>50px</span>
      </div>
    </div>

    <!-- Font Size Input -->
    <div class="control-group">
      <label for="fontsize-input" class="control-label">
        Tamaño de Fuente: <span class="value-display">{fontSizeValue}px</span>
      </label>
      <input
        id="fontsize-input"
        type="number"
        min="24"
        max="72"
        step="2"
        value={fontSizeValue}
        on:input={handleFontSizeChange}
        disabled={$layoutEditorStore.mode === "auto"}
        class="number-input"
      />
    </div>
  </div>

  {#if $layoutEditorStore.mode === "manual"}
    <div class="editor-actions">
      <Button
        variant="brutalist"
        size="medium"
        on:click={handleReset}
      >
        <RotateCcw size={16} strokeWidth={1.5} />
        Resetear a Automático
      </Button>
    </div>
  {/if}
</div>

<style>
  .layout-editor {
    background: var(--theme-bg-secondary);
    border: 2px solid var(--border-primary);
    border-radius: var(--radius-md);
    padding: var(--spacing-lg);
    display: flex;
    flex-direction: column;
    gap: var(--spacing-lg);
  }

  .editor-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-bottom: var(--spacing-md);
    border-bottom: 2px solid var(--border-primary);
  }

  .editor-title {
    font-size: var(--text-xl);
    font-weight: 700;
    color: var(--text-primary);
    margin: 0;
    display: flex;
    align-items: center;
    text-shadow: 2px 2px 0 var(--border-primary);
  }

  .mode-toggle {
    display: flex;
    align-items: center;
  }

  .toggle-button {
    padding: var(--spacing-sm) var(--spacing-md);
    border: 2px solid var(--border-primary);
    background: var(--theme-bg-primary);
    color: var(--text-primary);
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
    border-radius: var(--radius-sm);
    box-shadow: 3px 3px 0 var(--border-primary);
  }

  .toggle-button:hover {
    transform: translate(2px, 2px);
    box-shadow: 1px 1px 0 var(--border-primary);
  }

  .toggle-button.active {
    background: var(--accent-primary);
    color: white;
    border-color: var(--accent-primary);
  }

  .editor-controls {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-lg);
  }

  .control-group {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-sm);
  }

  .control-label {
    font-size: var(--text-base);
    font-weight: 600;
    color: var(--text-primary);
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .value-display {
    font-weight: 700;
    color: var(--accent-primary);
    font-family: monospace;
  }

  .slider {
    width: 100%;
    height: 8px;
    border-radius: 4px;
    background: var(--theme-bg-primary);
    border: 2px solid var(--border-primary);
    outline: none;
    -webkit-appearance: none;
    appearance: none;
    cursor: pointer;
  }

  .slider::-webkit-slider-thumb {
    -webkit-appearance: none;
    appearance: none;
    width: 24px;
    height: 24px;
    border-radius: 50%;
    background: var(--accent-primary);
    border: 3px solid var(--border-primary);
    cursor: pointer;
    box-shadow: 2px 2px 0 var(--border-primary);
    transition: all 0.2s;
  }

  .slider::-webkit-slider-thumb:hover {
    transform: scale(1.1);
  }

  .slider::-moz-range-thumb {
    width: 24px;
    height: 24px;
    border-radius: 50%;
    background: var(--accent-primary);
    border: 3px solid var(--border-primary);
    cursor: pointer;
    box-shadow: 2px 2px 0 var(--border-primary);
    transition: all 0.2s;
  }

  .slider::-moz-range-thumb:hover {
    transform: scale(1.1);
  }

  .slider:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .slider-labels {
    display: flex;
    justify-content: space-between;
    font-size: var(--text-sm);
    color: var(--text-secondary);
  }

  .number-input {
    width: 100%;
    padding: var(--spacing-sm) var(--spacing-md);
    border: 2px solid var(--border-primary);
    background: var(--theme-bg-primary);
    color: var(--text-primary);
    font-size: var(--text-base);
    font-weight: 600;
    border-radius: var(--radius-sm);
    box-shadow: 3px 3px 0 var(--border-primary);
    transition: all 0.2s;
  }

  .number-input:focus {
    outline: none;
    transform: translate(2px, 2px);
    box-shadow: 1px 1px 0 var(--border-primary);
  }

  .number-input:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .editor-actions {
    display: flex;
    justify-content: center;
    padding-top: var(--spacing-md);
    border-top: 2px solid var(--border-primary);
  }

  /* Responsive */
  @media (max-width: 768px) {
    .layout-editor {
      padding: var(--spacing-md);
    }

    .editor-header {
      flex-direction: column;
      align-items: flex-start;
      gap: var(--spacing-md);
    }

    .toggle-button {
      width: 100%;
      text-align: center;
    }

    .editor-actions :global(button) {
      width: 100%;
    }
  }

  /* Prevent hover transform on touch devices */
  @media (hover: none) and (pointer: coarse) {
    .toggle-button:hover {
      transform: none;
      box-shadow: 3px 3px 0 var(--border-primary);
    }

    .slider::-webkit-slider-thumb:hover {
      transform: none;
    }

    .slider::-moz-range-thumb:hover {
      transform: none;
    }
  }
</style>














