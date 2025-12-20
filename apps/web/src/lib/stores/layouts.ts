/**
 * Layouts Store - Manages layout style loading and selection state.
 * 
 * Handles loading layout style configurations and managing selected layout state.
 * Follows the same pattern as other stores in the codebase (products, services, etc.).
 */
import { writable, derived, type Writable, type Readable } from "svelte/store";
import { DEFAULT_LAYOUT_STYLES, type LayoutStyle } from "$lib/schemas/layout-style-schema";
import { backgroundImagesStore } from "./background-images";
import type { BackgroundImage } from "$lib/schemas/background-image-schema";

export interface LayoutsState {
  /** List of available layout styles */
  layouts: LayoutStyle[];
  /** Currently selected layout style ID */
  selectedLayoutId: string | null;
  /** Loading state */
  loading: boolean;
  /** Error message if any */
  error: string | null;
}

const initialState: LayoutsState = {
  layouts: [],
  selectedLayoutId: null,
  loading: false,
  error: null,
};

function createLayoutsStore() {
  const { subscribe, set, update }: Writable<LayoutsState> = writable(initialState);

  return {
    subscribe,
    
    /**
     * Load layout styles from configuration.
     * 
     * Currently loads from DEFAULT_LAYOUT_STYLES, but can be extended
     * to load from an API endpoint in the future.
     */
    async loadLayouts(): Promise<void> {
      update((state) => ({ ...state, loading: true, error: null }));
      
      try {
        // For now, use default layouts
        // In the future, this could fetch from an API
        const layouts = DEFAULT_LAYOUT_STYLES;
        
        update((state) => ({
          ...state,
          layouts,
          loading: false,
          error: null,
          // Auto-select first layout if none selected
          selectedLayoutId: state.selectedLayoutId || layouts[0]?.id || null,
        }));
      } catch (error: any) {
        update((state) => ({
          ...state,
          loading: false,
          error: error.message || "Error al cargar estilos de layout",
        }));
      }
    },
    
    /**
     * Select a layout style by ID.
     */
    selectLayout(layoutId: string | null): void {
      update((state) => ({
        ...state,
        selectedLayoutId: layoutId,
      }));
    },
    
    /**
     * Get the currently selected layout style.
     */
    getSelectedLayout(): LayoutStyle | null {
      let selected: LayoutStyle | null = null;
      const unsubscribe = subscribe((state) => {
        if (state.selectedLayoutId) {
          selected = state.layouts.find((layout) => layout.id === state.selectedLayoutId) || null;
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

export const layoutsStore = createLayoutsStore();

/**
 * Derived store for the currently selected layout style.
 */
export const selectedLayoutStyle: Readable<LayoutStyle | null> = derived(
  layoutsStore,
  ($store) => {
    if (!$store.selectedLayoutId) return null;
    return $store.layouts.find((layout) => layout.id === $store.selectedLayoutId) || null;
  }
);

/**
 * Combined menu configuration derived from background image and layout.
 * 
 * This provides a unified interface for components that need both
 * background image and layout information.
 */
export interface MenuConfig {
  backgroundImage: BackgroundImage | null;
  layoutStyle: LayoutStyle | null;
}

export const menuConfig: Readable<MenuConfig> = derived(
  [backgroundImagesStore, layoutsStore],
  ([$bgStore, $layoutStore]) => {
    const backgroundImage = $bgStore.selectedImageId
      ? $bgStore.images.find((img) => img.id === $bgStore.selectedImageId) || null
      : null;
    
    const layoutStyle = $layoutStore.selectedLayoutId
      ? $layoutStore.layouts.find((layout) => layout.id === $layoutStore.selectedLayoutId) || null
      : null;
    
    return {
      backgroundImage,
      layoutStyle,
    };
  }
);

