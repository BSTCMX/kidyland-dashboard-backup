/**
 * Background Image Schema - Type definitions for menu board background images.
 * 
 * Defines the structure for background images used in video/PDF export.
 * Separated from layout configuration for better modularity.
 */

export interface BackgroundImage {
  /** Unique identifier for the background image */
  id: string;
  /** Display name of the background image */
  name: string;
  /** Description of the background image */
  description?: string;
  /** Path to the background image (relative to /static/) */
  imagePath: string;
  /** Resolution for which this image is optimized */
  resolution?: {
    width: number;
    height: number;
  };
}

/**
 * Default background images configuration.
 * 
 * These images should be placed in /static/templates/
 * Images should be exactly 1920x1080 pixels for optimal quality.
 */
export const DEFAULT_BACKGROUND_IMAGES: BackgroundImage[] = [
  {
    id: "background-modern",
    name: "Fondo Moderno",
    description: "Diseño moderno y dinámico",
    imagePath: "/templates/template-modern.png",
    resolution: {
      width: 1920,
      height: 1080,
    },
  },
  {
    id: "background-classic",
    name: "Fondo Clásico",
    description: "Diseño clásico y elegante",
    imagePath: "/templates/template-classic.png",
    resolution: {
      width: 1920,
      height: 1080,
    },
  },
  {
    id: "background-minimal",
    name: "Fondo Minimalista",
    description: "Diseño minimalista y limpio",
    imagePath: "/templates/template-minimal.png",
    resolution: {
      width: 1920,
      height: 1080,
    },
  },
];














