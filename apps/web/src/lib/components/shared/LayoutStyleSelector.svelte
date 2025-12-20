<script lang="ts">
  /**
   * LayoutStyleSelector component - Select layout style for menu board.
   * 
   * Displays available layout styles with runtime-generated previews showing grid structure.
   * Based on TemplateSelector pattern but uses canvas-generated previews instead of images.
   */
  import { onMount } from "svelte";
  import { createEventDispatcher } from "svelte";
  import { layoutsStore, selectedLayoutStyle } from "$lib/stores/layouts";
  import type { LayoutStyle } from "$lib/schemas/layout-style-schema";
  import { generateLayoutPreview } from "$lib/utils/layout-preview";
  import { Layers, Check } from "lucide-svelte";

  const dispatch = createEventDispatcher<{
    select: { layoutId: string };
  }>();

  let layouts: LayoutStyle[] = [];
  let selectedLayoutId: string | null = null;
  let loading = false;
  let error: string | null = null;
  let previewCache: Map<string, string> = new Map();

  onMount(async () => {
    loading = true;
    await layoutsStore.loadLayouts();
    layouts = $layoutsStore.layouts;
    selectedLayoutId = $layoutsStore.selectedLayoutId;
    
    // Generate previews for all layouts
    layouts.forEach((layout) => {
      const preview = generateLayoutPreview(layout);
      if (preview) {
        previewCache.set(layout.id, preview);
      }
    });
    
    loading = false;

    // Dispatch initial selection
    if (selectedLayoutId) {
      dispatch("select", { layoutId: selectedLayoutId });
    }
  });

  // React to store changes
  $: if ($layoutsStore.layouts.length > 0) {
    layouts = $layoutsStore.layouts;
    // Generate previews if not cached
    layouts.forEach((layout) => {
      if (!previewCache.has(layout.id)) {
        const preview = generateLayoutPreview(layout);
        if (preview) {
          previewCache.set(layout.id, preview);
        }
      }
    });
  }

  $: if ($layoutsStore.selectedLayoutId) {
    selectedLayoutId = $layoutsStore.selectedLayoutId;
  }

  $: error = $layoutsStore.error;
  $: loading = $layoutsStore.loading;

  function selectLayout(layoutId: string) {
    layoutsStore.selectLayout(layoutId);
    dispatch("select", { layoutId });
  }

  function getPreview(layoutId: string): string | null {
    return previewCache.get(layoutId) || null;
  }
</script>

<div class="layout-style-selector">
  {#if loading}
    <div class="loading-state">
      <p>Cargando estilos de layout...</p>
    </div>
  {:else if error}
    <div class="error-state">
      <p>{error}</p>
    </div>
  {:else if layouts.length === 0}
    <div class="empty-state">
      <Layers size={48} strokeWidth={1.5} />
      <p>No hay estilos de layout disponibles</p>
    </div>
  {:else}
    <div class="layouts-grid">
      {#each layouts as layout (layout.id)}
        {@const preview = getPreview(layout.id)}
        <button
          type="button"
          class="layout-card"
          class:selected={selectedLayoutId === layout.id}
          on:click={() => selectLayout(layout.id)}
        >
          <div class="layout-preview-wrapper">
            {#if preview}
              <img
                src={preview}
                alt="Preview de {layout.name}"
                class="layout-preview-image"
              />
            {:else}
              <div class="layout-preview-placeholder">
                <Layers size={32} strokeWidth={1.5} />
                <span>Generando preview...</span>
              </div>
            {/if}
            <div class="layout-overlay">
              {#if selectedLayoutId === layout.id}
                <div class="selected-badge">
                  <Check size={24} strokeWidth={2.5} />
                </div>
              {/if}
            </div>
          </div>
          <div class="layout-info">
            <h3 class="layout-name">{layout.name}</h3>
            {#if layout.description}
              <p class="layout-description">{layout.description}</p>
            {/if}
            <div class="layout-meta">
              <span class="layout-columns">
                {layout.layout.grid.columns} columnas
              </span>
              <span class="layout-gap">
                Gap: {layout.layout.grid.gap}px
              </span>
            </div>
          </div>
        </button>
      {/each}
    </div>
  {/if}
</div>

<style>
  .layout-style-selector {
    width: 100%;
  }

  .loading-state,
  .error-state,
  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: var(--spacing-xl);
    text-align: center;
    min-height: 200px;
    gap: var(--spacing-md);
  }

  .error-state {
    color: var(--accent-danger);
  }

  .empty-state {
    color: var(--text-secondary);
  }

  .layouts-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: var(--spacing-lg);
    padding: var(--spacing-md) 0;
  }

  .layout-card {
    display: flex;
    flex-direction: column;
    border: 2px solid var(--border-primary);
    border-radius: var(--radius-lg);
    background: var(--theme-bg-primary);
    cursor: pointer;
    transition: all 0.2s;
    overflow: hidden;
    text-align: left;
    padding: 0;
  }

  .layout-card:hover {
    border-color: var(--accent-primary);
    transform: translateY(-4px);
    box-shadow: 0 8px 16px rgba(0, 0, 0, 0.15);
  }

  .layout-card.selected {
    border-color: var(--accent-primary);
    border-width: 3px;
    box-shadow: 0 0 0 3px rgba(0, 147, 247, 0.2);
  }

  .layout-preview-wrapper {
    position: relative;
    width: 100%;
    aspect-ratio: 16 / 9;
    background: var(--theme-bg-secondary);
    overflow: hidden;
  }

  .layout-preview-image {
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
  }

  .layout-preview-placeholder {
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: var(--spacing-sm);
    color: var(--text-secondary);
    font-size: var(--text-sm);
  }

  .layout-overlay {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(0, 0, 0, 0.3);
    opacity: 0;
    transition: opacity 0.2s;
  }

  .layout-card:hover .layout-overlay,
  .layout-card.selected .layout-overlay {
    opacity: 1;
  }

  .selected-badge {
    background: var(--accent-primary);
    color: white;
    border-radius: 50%;
    width: 48px;
    height: 48px;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 4px 12px rgba(0, 147, 247, 0.4);
  }

  .layout-info {
    padding: var(--spacing-md);
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xs);
  }

  .layout-name {
    font-size: var(--text-lg);
    font-weight: 700;
    color: var(--text-primary);
    margin: 0;
    
    /* Brutalist 3D text shadow */
    text-shadow: 
      0 0.05em 0 rgba(0, 0, 0, 0.1),
      0 0.1em 0 rgba(0, 0, 0, 0.1),
      0 0.15em 0 rgba(0, 0, 0, 0.1),
      0 0.2em 0 rgba(0, 0, 0, 0.1);
  }

  .layout-description {
    font-size: var(--text-sm);
    color: var(--text-secondary);
    margin: 0;
  }

  .layout-meta {
    display: flex;
    gap: var(--spacing-md);
    margin-top: var(--spacing-xs);
    font-size: var(--text-xs);
    color: var(--text-secondary);
    opacity: 0.8;
  }

  .layout-columns,
  .layout-gap {
    padding: 2px 8px;
    background: var(--theme-bg-secondary);
    border-radius: var(--radius-sm);
  }

  /* Responsive */
  @media (max-width: 768px) {
    .layouts-grid {
      grid-template-columns: 1fr;
      gap: var(--spacing-md);
    }

    .layout-card:hover {
      transform: none;
    }
  }

  /* Prevent hover transform on touch devices */
  @media (hover: none) and (pointer: coarse) {
    .layout-card:hover {
      transform: none;
      box-shadow: 0 8px 16px rgba(0, 0, 0, 0.15);
    }
  }
</style>














