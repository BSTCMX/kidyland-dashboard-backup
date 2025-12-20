/**
 * Background Images Store - Manages background image loading and selection state.
 * 
 * Handles loading background image configurations and managing selected background image state.
 * Follows the same pattern as other stores in the codebase (products, services, etc.).
 */
import { writable, derived, type Writable, type Readable } from "svelte/store";
import { DEFAULT_BACKGROUND_IMAGES, type BackgroundImage } from "$lib/schemas/background-image-schema";

export interface BackgroundImagesState {
  /** List of available background images */
  images: BackgroundImage[];
  /** Currently selected background image ID */
  selectedImageId: string | null;
  /** Loading state */
  loading: boolean;
  /** Error message if any */
  error: string | null;
}

const initialState: BackgroundImagesState = {
  images: [],
  selectedImageId: null,
  loading: false,
  error: null,
};

function createBackgroundImagesStore() {
  const { subscribe, set, update }: Writable<BackgroundImagesState> = writable(initialState);

  return {
    subscribe,
    
    /**
     * Load background images from configuration.
     * 
     * Currently loads from DEFAULT_BACKGROUND_IMAGES, but can be extended
     * to load from an API endpoint in the future.
     */
    async loadImages(): Promise<void> {
      update((state) => ({ ...state, loading: true, error: null }));
      
      try {
        // For now, use default images
        // In the future, this could fetch from an API
        const images = DEFAULT_BACKGROUND_IMAGES;
        
        update((state) => ({
          ...state,
          images,
          loading: false,
          error: null,
          // Auto-select first image if none selected
          selectedImageId: state.selectedImageId || images[0]?.id || null,
        }));
      } catch (error: any) {
        update((state) => ({
          ...state,
          loading: false,
          error: error.message || "Error al cargar imágenes de fondo",
        }));
      }
    },
    
    /**
     * Select a background image by ID.
     */
    selectImage(imageId: string | null): void {
      update((state) => ({
        ...state,
        selectedImageId: imageId,
      }));
    },
    
    /**
     * Get the currently selected background image.
     */
    getSelectedImage(): BackgroundImage | null {
      let selected: BackgroundImage | null = null;
      const unsubscribe = subscribe((state) => {
        if (state.selectedImageId) {
          selected = state.images.find((img) => img.id === state.selectedImageId) || null;
        }
      });
      unsubscribe();
      return selected;
    },
    
    /**
     * Reset store to initial state.
     */
    reset(): void {
      set(initialState);
    },
  };
}

export const backgroundImagesStore = createBackgroundImagesStore();

/**
 * Derived store for the currently selected background image.
 */
export const selectedBackgroundImage: Readable<BackgroundImage | null> = derived(
  backgroundImagesStore,
  ($store) => {
    if (!$store.selectedImageId) return null;
    return $store.images.find((img) => img.id === $store.selectedImageId) || null;
  }
);














