<script lang="ts">
  /**
   * BackgroundImageSelector component - Select background image for menu board.
   * 
   * Displays available background images in a grid with preview images.
   * Based on TemplateSelector pattern but simplified for background images only.
   */
  import { onMount } from "svelte";
  import { createEventDispatcher } from "svelte";
  import { backgroundImagesStore, selectedBackgroundImage } from "$lib/stores/background-images";
  import type { BackgroundImage } from "$lib/schemas/background-image-schema";
  import { Image, Check } from "lucide-svelte";

  const dispatch = createEventDispatcher<{
    select: { imageId: string };
  }>();

  let images: BackgroundImage[] = [];
  let selectedImageId: string | null = null;
  let loading = false;
  let error: string | null = null;

  onMount(async () => {
    loading = true;
    await backgroundImagesStore.loadImages();
    images = $backgroundImagesStore.images;
    selectedImageId = $backgroundImagesStore.selectedImageId;
    loading = false;

    // Dispatch initial selection
    if (selectedImageId) {
      dispatch("select", { imageId: selectedImageId });
    }
  });

  // React to store changes
  $: if ($backgroundImagesStore.images.length > 0) {
    images = $backgroundImagesStore.images;
  }

  $: if ($backgroundImagesStore.selectedImageId) {
    selectedImageId = $backgroundImagesStore.selectedImageId;
  }

  $: error = $backgroundImagesStore.error;
  $: loading = $backgroundImagesStore.loading;

  function selectImage(imageId: string) {
    backgroundImagesStore.selectImage(imageId);
    dispatch("select", { imageId });
  }
</script>

<div class="background-image-selector">
  {#if loading}
    <div class="loading-state">
      <p>Cargando imágenes de fondo...</p>
    </div>
  {:else if error}
    <div class="error-state">
      <p>{error}</p>
    </div>
  {:else if images.length === 0}
    <div class="empty-state">
      <Image size={48} strokeWidth={1.5} />
      <p>No hay imágenes de fondo disponibles</p>
      <p class="empty-hint">
        Coloca las imágenes PNG en <code>/static/templates/</code>
      </p>
    </div>
  {:else}
    <div class="images-grid">
      {#each images as image (image.id)}
        <button
          type="button"
          class="image-card"
          class:selected={selectedImageId === image.id}
          on:click={() => selectImage(image.id)}
        >
          <div class="image-wrapper">
            <img
              src={image.imagePath}
              alt={image.name}
              class="background-image-preview"
              loading="lazy"
              on:error={(e) => {
                // Fallback if image doesn't exist
                e.currentTarget.style.display = "none";
              }}
            />
            <div class="image-overlay">
              {#if selectedImageId === image.id}
                <div class="selected-badge">
                  <Check size={24} strokeWidth={2.5} />
                </div>
              {/if}
            </div>
          </div>
          <div class="image-info">
            <h3 class="image-name">{image.name}</h3>
            {#if image.description}
              <p class="image-description">{image.description}</p>
            {/if}
            {#if image.resolution}
              <div class="image-meta">
                <span class="resolution">
                  {image.resolution.width}x{image.resolution.height}
                </span>
              </div>
            {/if}
          </div>
        </button>
      {/each}
    </div>
  {/if}
</div>

<style>
  .background-image-selector {
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

  .images-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: var(--spacing-lg);
    padding: var(--spacing-md) 0;
  }

  .image-card {
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

  .image-card:hover {
    border-color: var(--accent-primary);
    transform: translateY(-4px);
    box-shadow: 0 8px 16px rgba(0, 0, 0, 0.15);
  }

  .image-card.selected {
    border-color: var(--accent-primary);
    border-width: 3px;
    box-shadow: 0 0 0 3px rgba(0, 147, 247, 0.2);
  }

  .image-wrapper {
    position: relative;
    width: 100%;
    aspect-ratio: 16 / 9;
    background: var(--theme-bg-secondary);
    overflow: hidden;
  }

  .background-image-preview {
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
  }

  .image-overlay {
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

  .image-card:hover .image-overlay,
  .image-card.selected .image-overlay {
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

  .image-info {
    padding: var(--spacing-md);
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xs);
  }

  .image-name {
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

  .image-description {
    font-size: var(--text-sm);
    color: var(--text-secondary);
    margin: 0;
  }

  .image-meta {
    display: flex;
    gap: var(--spacing-md);
    margin-top: var(--spacing-xs);
    font-size: var(--text-xs);
    color: var(--text-secondary);
    opacity: 0.8;
  }

  .resolution {
    padding: 2px 8px;
    background: var(--theme-bg-secondary);
    border-radius: var(--radius-sm);
  }

  /* Responsive */
  @media (max-width: 768px) {
    .images-grid {
      grid-template-columns: 1fr;
      gap: var(--spacing-md);
    }

    .image-card:hover {
      transform: none;
    }
  }

  /* Prevent hover transform on touch devices */
  @media (hover: none) and (pointer: coarse) {
    .image-card:hover {
      transform: none;
      box-shadow: 0 8px 16px rgba(0, 0, 0, 0.15);
    }
  }
</style>














