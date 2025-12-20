<script lang="ts">
  /**
   * TemplateSelector component - Select template for menu board.
   * 
   * Displays available templates in a grid with preview images.
   */
  import { onMount } from "svelte";
  import { createEventDispatcher } from "svelte";
  import { templatesStore, selectedTemplate } from "$lib/stores/templates";
  import type { Template } from "$lib/schemas/template-schema";
  import { Image, Check } from "lucide-svelte";

  const dispatch = createEventDispatcher();

  let templates: Template[] = [];
  let selectedTemplateId: string | null = null;
  let loading = false;
  let error: string | null = null;

  onMount(async () => {
    loading = true;
    await templatesStore.loadTemplates();
    templates = $templatesStore.templates;
    selectedTemplateId = $templatesStore.selectedTemplateId;
    loading = false;

    // Dispatch initial selection
    if (selectedTemplateId) {
      dispatch("select", { templateId: selectedTemplateId });
    }
  });

  // React to store changes
  $: if ($templatesStore.templates.length > 0) {
    templates = $templatesStore.templates;
  }

  $: if ($templatesStore.selectedTemplateId) {
    selectedTemplateId = $templatesStore.selectedTemplateId;
  }

  $: error = $templatesStore.error;
  $: loading = $templatesStore.loading;

  function selectTemplate(templateId: string) {
    templatesStore.selectTemplate(templateId);
    dispatch("select", { templateId });
  }
</script>

<div class="template-selector">
  {#if loading}
    <div class="loading-state">
      <p>Cargando templates...</p>
    </div>
  {:else if error}
    <div class="error-state">
      <p>{error}</p>
    </div>
  {:else if templates.length === 0}
    <div class="empty-state">
      <Image size={48} strokeWidth={1.5} />
      <p>No hay templates disponibles</p>
      <p class="empty-hint">
        Coloca las imágenes de templates en <code>/static/templates/</code>
      </p>
    </div>
  {:else}
    <div class="templates-grid">
      {#each templates as template (template.id)}
        <button
          type="button"
          class="template-card"
          class:selected={selectedTemplateId === template.id}
          on:click={() => selectTemplate(template.id)}
        >
          <div class="template-image-wrapper">
            <img
              src={template.image}
              alt={template.name}
              class="template-image"
              loading="lazy"
              on:error={(e) => {
                // Fallback if image doesn't exist yet
                e.currentTarget.style.display = "none";
              }}
            />
            <div class="template-overlay">
              {#if selectedTemplateId === template.id}
                <div class="selected-badge">
                  <Check size={24} strokeWidth={2.5} />
                </div>
              {/if}
            </div>
          </div>
          <div class="template-info">
            <h3 class="template-name">{template.name}</h3>
            {#if template.description}
              <p class="template-description">{template.description}</p>
            {/if}
            <div class="template-meta">
              <span class="template-columns">
                {template.layout.grid.columns} columnas
              </span>
              {#if template.resolution}
                <span class="template-resolution">
                  {template.resolution.width}x{template.resolution.height}
                </span>
              {/if}
            </div>
          </div>
        </button>
      {/each}
    </div>
  {/if}
</div>

<style>
  .template-selector {
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

  .empty-hint {
    font-size: var(--text-sm);
    opacity: 0.7;
  }

  .empty-hint code {
    background: var(--theme-bg-secondary);
    padding: 2px 6px;
    border-radius: var(--radius-sm);
    font-family: monospace;
    font-size: var(--text-xs);
  }

  .templates-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: var(--spacing-lg);
    padding: var(--spacing-md) 0;
  }

  .template-card {
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

  .template-card:hover {
    border-color: var(--accent-primary);
    transform: translateY(-4px);
    box-shadow: 0 8px 16px rgba(0, 0, 0, 0.15);
  }

  .template-card.selected {
    border-color: var(--accent-primary);
    border-width: 3px;
    box-shadow: 0 0 0 3px rgba(0, 147, 247, 0.2);
  }

  .template-image-wrapper {
    position: relative;
    width: 100%;
    aspect-ratio: 16 / 9;
    background: var(--theme-bg-secondary);
    overflow: hidden;
  }

  .template-image {
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
  }

  .template-overlay {
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

  .template-card:hover .template-overlay,
  .template-card.selected .template-overlay {
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

  .template-info {
    padding: var(--spacing-md);
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xs);
  }

  .template-name {
    font-size: var(--text-lg);
    font-weight: 700;
    color: var(--text-primary);
    margin: 0;
  }

  .template-description {
    font-size: var(--text-sm);
    color: var(--text-secondary);
    margin: 0;
  }

  .template-meta {
    display: flex;
    gap: var(--spacing-md);
    margin-top: var(--spacing-xs);
    font-size: var(--text-xs);
    color: var(--text-secondary);
    opacity: 0.8;
  }

  .template-columns,
  .template-resolution {
    padding: 2px 8px;
    background: var(--theme-bg-secondary);
    border-radius: var(--radius-sm);
  }

  /* Responsive */
  @media (max-width: 768px) {
    .templates-grid {
      grid-template-columns: 1fr;
      gap: var(--spacing-md);
    }

    .template-card:hover {
      transform: none;
    }
  }

  /* Prevent hover transform on touch devices */
  @media (hover: none) and (pointer: coarse) {
    .template-card:hover {
      transform: none;
      box-shadow: 0 8px 16px rgba(0, 0, 0, 0.15);
    }
  }
</style>
