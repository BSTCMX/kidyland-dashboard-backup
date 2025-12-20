/**
 * Layout Editor Store - Manages manual layout configuration overrides.
 * 
 * Allows users to manually adjust layout parameters (columns, padding, gap, fontSize)
 * with the option to reset to auto-calculation.
 * 
 * Follows the same pattern as other stores in the codebase (theme.ts, layouts.ts).
 */
import { writable, derived, type Writable, type Readable } from "svelte/store";

export interface LayoutEditorConfig {
  /** Number of columns (1-6) */
  columns: number | null;
  /** Padding in pixels (10-100) */
  padding: number | null;
  /** Gap between items in pixels (5-50) */
  gap: number | null;
  /** Font size in pixels (24-72) */
  fontSize: number | null;
}

export interface LayoutEditorState {
  /** Whether manual override is enabled */
  mode: "auto" | "manual";
  /** Manual configuration overrides (null values use auto) */
  manualConfig: LayoutEditorConfig;
}

const initialState: LayoutEditorState = {
  mode: "auto",
  manualConfig: {
    columns: null,
    padding: null,
    gap: null,
    fontSize: null,
  },
};

function createLayoutEditorStore() {
  const { subscribe, set, update }: Writable<LayoutEditorState> = writable(initialState);

  return {
    subscribe,
    
    /**
     * Set manual configuration override.
     * 
     * @param config - Partial configuration to override
     */
    setManualConfig(config: Partial<LayoutEditorConfig>): void {
      update((state) => ({
        ...state,
        mode: "manual",
        manualConfig: {
          ...state.manualConfig,
          ...config,
        },
      }));
    },
    
    /**
     * Reset to auto mode (clears all manual overrides).
     */
    resetToAuto(): void {
      set(initialState);
    },
    
    /**
     * Get active configuration (manual if mode is manual, otherwise null for auto).
     * 
     * @returns Active configuration or null if using auto
     */
    getActiveConfig(): LayoutEditorConfig | null {
      let activeConfig: LayoutEditorConfig | null = null;
      const unsubscribe = subscribe((state) => {
        if (state.mode === "manual") {
          activeConfig = state.manualConfig;
        } else {
          activeConfig = null;
        }
      });
      unsubscribe();
      return activeConfig;
    },
    
    /**
     * Check if a specific property is manually overridden.
     */
    isManualOverride(property: keyof LayoutEditorConfig): boolean {
      let isOverride = false;
      const unsubscribe = subscribe((state) => {
        isOverride = state.mode === "manual" && state.manualConfig[property] !== null;
      });
      unsubscribe();
      return isOverride;
    },
    
    /**
     * Reset store to initial state.
     */
    reset(): void {
      set(initialState);
    },
  };
}

export const layoutEditorStore = createLayoutEditorStore();

/**
 * Derived store for active configuration.
 * Returns manual config if mode is manual, otherwise null.
 */
export const activeLayoutConfig: Readable<LayoutEditorConfig | null> = derived(
  layoutEditorStore,
  ($store) => {
    if ($store.mode === "manual") {
      return $store.manualConfig;
    }
    return null;
  }
);














