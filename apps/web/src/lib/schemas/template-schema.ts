/**
 * Template Schema - Type definitions for menu board templates.
 * 
 * Defines the structure for template configurations used in video/PDF export.
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

export interface Template {
  /** Unique identifier for the template */
  id: string;
  /** Display name of the template */
  name: string;
  /** Description of the template */
  description?: string;
  /** Path to the template background image (relative to /static/) */
  image: string;
  /** Layout configuration */
  layout: TemplateLayout;
  /** Branding configuration */
  branding?: TemplateBranding;
  /** Resolution for which this template is optimized */
  resolution?: {
    width: number;
    height: number;
  };
}

/**
 * Default templates configuration.
 * 
 * These templates will be loaded from /static/templates/
 * The user should place template images in that folder.
 */
export const DEFAULT_TEMPLATES: Template[] = [
  {
    id: "template-modern",
    name: "Template Moderno",
    description: "Diseño moderno con grid de 3 columnas",
    image: "/templates/template-modern.png",
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
    id: "template-classic",
    name: "Template Clásico",
    description: "Diseño clásico con grid de 2 columnas",
    image: "/templates/template-classic.png",
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
    id: "template-minimal",
    name: "Template Minimalista",
    description: "Diseño minimalista con grid de 4 columnas",
    image: "/templates/template-minimal.png",
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
