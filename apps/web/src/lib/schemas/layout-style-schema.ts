/**
 * Layout Style Schema - Type definitions for menu board layout configurations.
 * 
 * Defines the structure for layout styles used in video/PDF export.
 * Separated from background images for better modularity.
 */

export interface TemplateLayout {
  /** Grid configuration for items arrangement */
  grid: {
    /** Number of columns in the grid */
    columns: number;
    /** Gap between items in pixels */
    gap: number;
    /** Padding around the grid in pixels */
    padding: number;
  };
  /** Header section configuration */
  header?: {
    /** Height of header in pixels */
    height: number;
    /** Position: "top" | "center" | "bottom" */
    position?: "top" | "center" | "bottom";
  };
  /** Footer section configuration */
  footer?: {
    /** Height of footer in pixels */
    height: number;
    /** Position: "top" | "center" | "bottom" */
    position?: "top" | "center" | "bottom";
  };
}

export interface TemplateBranding {
  /** Logo position in the template */
  logoPosition?: "top-left" | "top-center" | "top-right" | "center" | "bottom-left" | "bottom-center" | "bottom-right";
  /** Color scheme */
  colors: {
    /** Primary brand color */
    primary: string;
    /** Success/accent color */
    success: string;
    /** Optional text color override */
    text?: string;
    /** Optional background color override */
    background?: string;
  };
}

export interface LayoutStyle {
  /** Unique identifier for the layout style */
  id: "modern" | "classic" | "minimal";
  /** Display name of the layout style */
  name: string;
  /** Description of the layout style */
  description: string;
  /** Layout configuration */
  layout: TemplateLayout;
  /** Branding configuration */
  branding?: TemplateBranding;
  /** Resolution for which this layout is optimized */
  resolution?: {
    width: number;
    height: number;
  };
}

/**
 * Default layout styles configuration.
 * 
 * These layouts define how items are arranged on the menu board.
 * Can be combined with any background image.
 */
export const DEFAULT_LAYOUT_STYLES: LayoutStyle[] = [
  {
    id: "modern",
    name: "Distribución Moderna",
    description: "Grid de 3 columnas, ideal para mostrar muchos items",
    layout: {
      grid: {
        columns: 3,
        gap: 20,
        padding: 40,
      },
      header: {
        height: 200,
        position: "top",
      },
      footer: {
        height: 100,
        position: "bottom",
      },
    },
    branding: {
      logoPosition: "top-left",
      colors: {
        primary: "#0093F7",
        success: "#3DAD09",
      },
    },
    resolution: {
      width: 1920,
      height: 1080,
    },
  },
  {
    id: "classic",
    name: "Distribución Clásica",
    description: "Grid de 2 columnas, más espacioso y fácil de leer",
    layout: {
      grid: {
        columns: 2,
        gap: 30,
        padding: 50,
      },
      header: {
        height: 180,
        position: "top",
      },
      footer: {
        height: 120,
        position: "bottom",
      },
    },
    branding: {
      logoPosition: "top-center",
      colors: {
        primary: "#0093F7",
        success: "#3DAD09",
      },
    },
    resolution: {
      width: 1920,
      height: 1080,
    },
  },
  {
    id: "minimal",
    name: "Distribución Minimalista",
    description: "Grid de 4 columnas, máximo aprovechamiento del espacio",
    layout: {
      grid: {
        columns: 4,
        gap: 15,
        padding: 30,
      },
      header: {
        height: 150,
        position: "top",
      },
    },
    branding: {
      logoPosition: "top-right",
      colors: {
        primary: "#0093F7",
        success: "#3DAD09",
      },
    },
    resolution: {
      width: 1920,
      height: 1080,
    },
  },
];














