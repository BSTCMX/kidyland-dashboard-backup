/**
 * Lucide Icon Loader - Utility to load and render Lucide icons on Canvas.
 * 
 * Pre-renders SVG icons to Image objects for efficient canvas rendering.
 * Uses lucide-svelte icons converted to SVG data URLs.
 */

// Icon SVG paths from Lucide (manually extracted for performance)
// These are the actual SVG paths used by lucide-svelte for the icons we need
const ICON_SVGS: Record<string, string> = {
  gamepad2: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <line x1="6" y1="11" x2="10" y2="11"></line>
    <line x1="8" y1="9" x2="8" y2="13"></line>
    <line x1="15" y1="12" x2="15.01" y2="12"></line>
    <line x1="18" y1="10" x2="18.01" y2="10"></line>
    <path d="M17.32 5H6.68a4 4 0 0 0-3.978 4.426l.58 4.148A4 4 0 0 0 7.26 17h9.48a4 4 0 0 0 3.978-3.426l.58-4.148A4 4 0 0 0 17.32 5z"></path>
    <path d="M9 11V9"></path>
  </svg>`,
  popcorn: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <path d="M18 11c.7 0 1.2-.7 1.1-1.4l-.4-2.6c-.1-.5-.5-.9-1-.9H6.3c-.5 0-.9.4-1 .9l-.4 2.6c-.1.7.4 1.4 1.1 1.4z"></path>
    <path d="M7 7h10"></path>
    <path d="M9 11v6"></path>
    <path d="M15 11v6"></path>
    <path d="M7 15h10"></path>
    <path d="M17 11V9a2 2 0 0 0-2-2H9a2 2 0 0 0-2 2v2"></path>
  </svg>`,
  package: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <path d="M21 10V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 18v-8z"></path>
    <polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline>
    <line x1="12" y1="22.08" x2="12" y2="12"></line>
  </svg>`,
};

/**
 * Cache for pre-rendered icon images
 */
const iconImageCache: Map<string, HTMLImageElement> = new Map();

/**
 * Convert SVG string to data URL
 */
function svgToDataUrl(svgString: string, color: string = "currentColor", size: number = 24): string {
  // Replace currentColor with actual color
  const coloredSvg = svgString.replace(/currentColor/g, color);
  
  // Add explicit size if not present
  const sizedSvg = coloredSvg.replace(
    'viewBox="0 0 24 24"',
    `viewBox="0 0 24 24" width="${size}" height="${size}"`
  );
  
  const svgBlob = new Blob([sizedSvg], { type: "image/svg+xml;charset=utf-8" });
  return URL.createObjectURL(svgBlob);
}

/**
 * Load a Lucide icon as an Image object for canvas rendering.
 * 
 * @param iconName - Name of the icon (e.g., 'gamepad2', 'popcorn', 'package')
 * @param color - Color for the icon (default: '#ffffff')
 * @param size - Size in pixels (default: 48)
 * @returns Promise that resolves to HTMLImageElement
 */
export async function loadLucideIcon(
  iconName: keyof typeof ICON_SVGS,
  color: string = "#ffffff",
  size: number = 48
): Promise<HTMLImageElement> {
  const cacheKey = `${iconName}-${color}-${size}`;
  
  // Return cached icon if available
  if (iconImageCache.has(cacheKey)) {
    const cached = iconImageCache.get(cacheKey)!;
    // Verify image is loaded
    if (cached.complete && cached.naturalWidth > 0) {
      return Promise.resolve(cached);
    }
  }
  
  // Create new image
  return new Promise((resolve, reject) => {
    const svgString = ICON_SVGS[iconName];
    if (!svgString) {
      reject(new Error(`Icon "${iconName}" not found`));
      return;
    }
    
    const dataUrl = svgToDataUrl(svgString, color, size);
    const img = new Image();
    
    img.onload = () => {
      iconImageCache.set(cacheKey, img);
      resolve(img);
      // Clean up data URL after a short delay
      setTimeout(() => URL.revokeObjectURL(dataUrl), 100);
    };
    
    img.onerror = () => {
      URL.revokeObjectURL(dataUrl);
      reject(new Error(`Failed to load icon "${iconName}"`));
    };
    
    img.src = dataUrl;
  });
}

/**
 * Pre-load all commonly used icons for better performance.
 * 
 * Call this once during app initialization or when needed.
 */
export async function preloadCommonIcons(color: string = "#ffffff"): Promise<void> {
  const iconNames: Array<keyof typeof ICON_SVGS> = ["gamepad2", "popcorn", "package"];
  const sizes = [32, 48, 64]; // Common sizes
  
  const loadPromises: Promise<HTMLImageElement>[] = [];
  
  for (const iconName of iconNames) {
    for (const size of sizes) {
      loadPromises.push(loadLucideIcon(iconName, color, size).catch(() => {
        // Silently fail for preload - will load on demand if needed
        return null as any;
      }));
    }
  }
  
  await Promise.all(loadPromises);
}

/**
 * Draw a Lucide icon on canvas at specified position.
 * 
 * @param ctx - Canvas rendering context
 * @param iconName - Name of the icon
 * @param x - X position
 * @param y - Y position
 * @param size - Size in pixels
 * @param color - Icon color
 * @returns Promise that resolves when icon is drawn
 */
export async function drawLucideIcon(
  ctx: CanvasRenderingContext2D,
  iconName: keyof typeof ICON_SVGS,
  x: number,
  y: number,
  size: number = 48,
  color: string = "#ffffff"
): Promise<void> {
  try {
    const icon = await loadLucideIcon(iconName, color, size);
    // Center the icon at x, y
    ctx.drawImage(icon, x - size / 2, y - size / 2, size, size);
  } catch (error) {
    console.error(`Failed to draw icon ${iconName}:`, error);
    // Fallback: draw a simple circle placeholder
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.arc(x, y, size / 4, 0, Math.PI * 2);
    ctx.fill();
  }
}

