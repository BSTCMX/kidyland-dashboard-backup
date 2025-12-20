/**
 * Templates Store - Manages template loading and selection state.
 * 
 * Handles loading template configurations and managing selected template state.
 */
import { writable, derived, type Writable, type Readable } from "svelte/store";
import { DEFAULT_TEMPLATES, type Template } from "$lib/schemas/template-schema";

export interface TemplatesState {
  /** List of available templates */
  templates: Template[];
  /** Currently selected template ID */
  selectedTemplateId: string | null;
  /** Loading state */
  loading: boolean;
  /** Error message if any */
  error: string | null;
}

const initialState: TemplatesState = {
  templates: [],
  selectedTemplateId: null,
  loading: false,
  error: null,
};

function createTemplatesStore() {
  const { subscribe, set, update }: Writable<TemplatesState> = writable(initialState);

  return {
    subscribe,
    
    /**
     * Load templates from configuration.
     * 
     * Currently loads from DEFAULT_TEMPLATES, but can be extended
     * to load from an API endpoint in the future.
     */
    async loadTemplates(): Promise<void> {
      update((state) => ({ ...state, loading: true, error: null }));
      
      try {
        // For now, use default templates
        // In the future, this could fetch from an API
        const templates = DEFAULT_TEMPLATES;
        
        update((state) => ({
          ...state,
          templates,
          loading: false,
          error: null,
          // Auto-select first template if none selected
          selectedTemplateId: state.selectedTemplateId || templates[0]?.id || null,
        }));
      } catch (error: any) {
        update((state) => ({
          ...state,
          loading: false,
          error: error.message || "Error al cargar templates",
        }));
      }
    },
    
    /**
     * Select a template by ID.
     */
    selectTemplate(templateId: string | null): void {
      update((state) => ({
        ...state,
        selectedTemplateId: templateId,
      }));
    },
    
    /**
     * Get the currently selected template.
     */
    getSelectedTemplate(): Template | null {
      let selected: Template | null = null;
      const unsubscribe = subscribe((state) => {
        if (state.selectedTemplateId) {
          selected = state.templates.find((t) => t.id === state.selectedTemplateId) || null;
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

export const templatesStore = createTemplatesStore();

/**
 * Derived store for the currently selected template.
 */
export const selectedTemplate: Readable<Template | null> = derived(
  templatesStore,
  ($store) => {
    if (!$store.selectedTemplateId) return null;
    return $store.templates.find((t) => t.id === $store.selectedTemplateId) || null;
  }
);
