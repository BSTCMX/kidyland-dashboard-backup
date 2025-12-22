/**
 * Canvas quality configuration utilities.
 * 
 * Clean Architecture: Centralized canvas quality settings.
 * Provides reusable functions to configure canvas context for optimal rendering quality.
 * 
 * This module ensures consistent high-quality rendering across all canvas operations,
 * particularly important for text rendering in PDF and video exports.
 */

/**
 * Configure canvas context for optimal rendering quality.
 * 
 * Sets image smoothing and quality properties to ensure sharp text and graphics.
 * This is critical for PDF and video exports where quality degradation is noticeable.
 * 
 * Clean Architecture: Reusable utility function, no hardcoding.
 * 
 * @param ctx - Canvas 2D rendering context to configure
 * @param options - Optional configuration overrides
 * @param options.imageSmoothingEnabled - Enable/disable image smoothing (default: true)
 * @param options.imageSmoothingQuality - Quality level: "low" | "medium" | "high" (default: "high")
 * 
 * @returns The configured context (for chaining if needed)
 */
export function configureCanvasQuality(
  ctx: CanvasRenderingContext2D,
  options: {
    imageSmoothingEnabled?: boolean;
    imageSmoothingQuality?: "low" | "medium" | "high";
  } = {}
): CanvasRenderingContext2D {
  // Default to high quality settings
  const {
    imageSmoothingEnabled = true,
    imageSmoothingQuality = "high",
  } = options;

  // Configure image smoothing (affects how images are scaled/interpolated)
  ctx.imageSmoothingEnabled = imageSmoothingEnabled;
  
  // Set smoothing quality (if supported by browser)
  // This property is supported in Chrome, Edge, Firefox, Safari
  if ("imageSmoothingQuality" in ctx) {
    (ctx as any).imageSmoothingQuality = imageSmoothingQuality;
  }

  // Note: textRenderingQuality is experimental and not widely supported
  // We skip it to maintain compatibility across browsers

  return ctx;
}

