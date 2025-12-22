/**
 * Video Canvas utilities - Animation engine for Kidyland menu videos.
 * 
 * Generates animated canvas with branding, services, and products.
 * Used by VideoMenuGenerator component.
 */
import { calculateDynamicGrid, calculatePagesNeeded, getItemsForPage } from "./canvas-layout";
import { drawLucideIcon, loadLucideIcon } from "./lucide-icon-loader";
import { get } from "svelte/store";
import { layoutEditorStore } from "../stores/layout-editor";

export interface CanvasConfig {
  width: number;
  height: number;
  fps: number;
  duration: number; // seconds
}

export interface ServiceItem {
  id: string;
  name: string;
  price_cents: number; // Minimum price (backward compatibility)
  durations_allowed: number[];
  duration_prices?: Record<number, number>; // Optional: {duration_minutes: price_cents} for displaying all prices
}

export interface ProductItem {
  id: string;
  name: string;
  price_cents: number;
  stock_qty: number;
}

export interface PackageItem {
  id: string;
  name: string;
  price_cents: number;
  description?: string;
}

export interface BrandingColors {
  primary: string;    // #0093F7
  success: string;   // #3DAD09
  danger: string;   // #D30554
  warning: string;   // #FFCE00
  background: string; // Dark theme
  text: string;      // White
}

export const KIDYLAND_COLORS: BrandingColors = {
  primary: "#0093F7",
  success: "#3DAD09",
  danger: "#D30554",
  warning: "#FFCE00",
  background: "#1a1a1a",
  text: "#FFFFFF",
};

/**
 * Calculate proportional font sizes based on base fontSize.
 * 
 * These proportions maintain visual hierarchy:
 * - Title: 100% of base (already handled separately)
 * - Item name: 75% of base
 * - Price: 67% of base (slightly smaller than name for hierarchy)
 * - Details (duration, description): 50% of base
 * 
 * @param baseFontSize - Base font size from layout editor (default: 48px)
 * @returns Object with calculated font sizes
 */
function calculateFontSizes(baseFontSize: number | null): {
  title: number;
  itemName: number;
  price: number;
  details: number;
  packageDescription: number;
  serviceDurationPrice: number;
} {
  const base = baseFontSize ?? 48; // Default to 48px if not specified
  
  return {
    title: base,                    // 100% - for section titles
    itemName: Math.round(base * 0.75),   // 75% - for service/product/package names
    price: Math.round(base * 0.67),      // 67% - for prices (slightly smaller)
    details: Math.round(base * 0.5),     // 50% - for duration, descriptions
    packageDescription: Math.round(base * 0.625), // 62.5% - for package descriptions (larger than details for better readability)
    serviceDurationPrice: Math.round(base * 0.625), // 62.5% - for service durations and prices (same as packageDescription for consistency)
  };
}

/**
 * Format duration in minutes to a human-readable string.
 * Examples: 30 -> "30min", 60 -> "1h", 90 -> "1h 30min"
 */
function formatDuration(minutes: number): string {
  if (minutes < 60) {
    return `${minutes}min`;
  }
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  if (mins === 0) {
    return `${hours}h`;
  }
  return `${hours}h ${mins}min`;
}

/**
 * Format price in cents to a dollar string.
 * Example: 5000 -> "$50.00"
 */
function formatPrice(cents: number): string {
  return `$${(cents / 100).toFixed(2)}`;
}

/**
 * Format duration and price pair for horizontal display.
 * Example: (30, 5000) -> "30min $50.00"
 */
function formatDurationPrice(duration: number, priceCents: number): string {
  return `${formatDuration(duration)} ${formatPrice(priceCents)}`;
}

/**
 * Draw text with enhanced contrast for readability over backgrounds.
 * 
 * Clean Architecture: Reusable utility function for text rendering with contrast.
 * 
 * This function draws text with optional stroke and shadow to improve readability
 * when text is rendered over complex backgrounds (especially background images).
 * 
 * @param ctx - Canvas 2D rendering context
 * @param text - Text string to render
 * @param x - X coordinate
 * @param y - Y coordinate
 * @param options - Optional rendering options
 * @param options.strokeWidth - Width of text stroke outline (default: 2)
 * @param options.strokeColor - Color of stroke (default: "rgba(0, 0, 0, 0.8)")
 * @param options.shadowBlur - Blur radius for shadow (default: 4)
 * @param options.shadowColor - Color of shadow (default: "rgba(0, 0, 0, 0.5)")
 * @param options.shadowOffsetX - Horizontal shadow offset (default: 2)
 * @param options.shadowOffsetY - Vertical shadow offset (default: 2)
 * @param options.enableStroke - Enable stroke outline (default: true)
 * @param options.enableShadow - Enable shadow effect (default: true)
 */
export function drawTextWithContrast(
  ctx: CanvasRenderingContext2D,
  text: string,
  x: number,
  y: number,
  options: {
    strokeWidth?: number;
    strokeColor?: string;
    shadowBlur?: number;
    shadowColor?: string;
    shadowOffsetX?: number;
    shadowOffsetY?: number;
    enableStroke?: boolean;
    enableShadow?: boolean;
  } = {}
): void {
  // Default options for optimal contrast
  const {
    strokeWidth = 2,
    strokeColor = "rgba(0, 0, 0, 0.8)",
    shadowBlur = 4,
    shadowColor = "rgba(0, 0, 0, 0.5)",
    shadowOffsetX = 2,
    shadowOffsetY = 2,
    enableStroke = true,
    enableShadow = true,
  } = options;

  // Save current context state
  ctx.save();

  // Configure shadow (drawn first, behind text)
  if (enableShadow) {
    ctx.shadowBlur = shadowBlur;
    ctx.shadowColor = shadowColor;
    ctx.shadowOffsetX = shadowOffsetX;
    ctx.shadowOffsetY = shadowOffsetY;
  } else {
    // Disable shadow
    ctx.shadowBlur = 0;
    ctx.shadowOffsetX = 0;
    ctx.shadowOffsetY = 0;
  }

  // Draw stroke outline (if enabled) - provides strong contrast
  if (enableStroke) {
    ctx.strokeStyle = strokeColor;
    ctx.lineWidth = strokeWidth;
    ctx.lineJoin = "round";
    ctx.lineCap = "round";
    ctx.strokeText(text, x, y);
  }

  // Draw filled text (on top of stroke/shadow)
  // Shadow is applied to fillText, so we need to reset shadow for stroke
  if (enableStroke && enableShadow) {
    // Re-apply shadow for fill (stroke doesn't use shadow)
    ctx.shadowBlur = shadowBlur;
    ctx.shadowColor = shadowColor;
    ctx.shadowOffsetX = shadowOffsetX;
    ctx.shadowOffsetY = shadowOffsetY;
  }
  ctx.fillText(text, x, y);

  // Restore context state
  ctx.restore();
}

/**
 * Draw Kidyland branding header on canvas.
 */
export function drawBrandingHeader(
  ctx: CanvasRenderingContext2D,
  width: number,
  height: number,
  colors: BrandingColors
): void {
  // Background gradient
  const gradient = ctx.createLinearGradient(0, 0, width, 0);
  gradient.addColorStop(0, colors.primary);
  gradient.addColorStop(0.5, colors.success);
  gradient.addColorStop(1, colors.primary);
  
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, width, 160); // Increased header height for larger fonts
  
  // Title (scaled for 1920x1080 digital signage: 72px minimum)
  ctx.fillStyle = colors.text;
  ctx.font = "bold 72px Arial, sans-serif";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText("KIDYLAND", width / 2, 50);
  
  // Subtitle (scaled for 1920x1080 digital signage: 36px minimum)
  ctx.font = "36px Arial, sans-serif";
  ctx.fillText("Menú de Servicios y Productos", width / 2, 100);
  
  // Decorative line
  ctx.strokeStyle = colors.warning;
  ctx.lineWidth = 4; // Slightly thicker for better visibility
  ctx.beginPath();
  ctx.moveTo(width * 0.1, 150);
  ctx.lineTo(width * 0.9, 150);
  ctx.stroke();
}

/**
 * Draw services section on canvas.
 */
export async function drawServicesSection(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  width: number,
  services: ServiceItem[],
  colors: BrandingColors,
  frame: number
): Promise<number> {
  if (services.length === 0) return 0;
  
  // Get manual config if available
  const editorState = get(layoutEditorStore);
  const manualConfig = editorState.mode === "manual" ? editorState.manualConfig : null;
  
  // Calculate dynamic grid layout (use manual values if provided)
  const grid = calculateDynamicGrid({
    itemCount: services.length,
    availableWidth: width,
    preferredColumns: manualConfig?.columns ?? 2,
    minItemWidth: 300,
    maxItemWidth: 900,
    gap: manualConfig?.gap ?? 30,
    padding: manualConfig?.padding ?? 40,
    itemHeight: 80,
  });
  
  // Calculate section height dynamically
  const titleHeight = 80;
  const sectionHeight = grid.totalHeight + titleHeight;
  
  // Section background (semi-transparent if over background image)
  ctx.fillStyle = "rgba(26, 26, 26, 0.8)"; // Semi-transparent dark
  ctx.fillRect(x, y, width, sectionHeight);
  
  // Calculate proportional font sizes based on manual config
  const fontSizes = calculateFontSizes(manualConfig?.fontSize ?? null);
  
  // Section title with icon (use calculated fontSize)
  ctx.fillStyle = colors.primary;
  ctx.font = `bold ${fontSizes.title}px Arial, sans-serif`;
  ctx.textAlign = "left";
  
  // Draw icon next to text (icon is 40px, text starts 50px from x + padding)
  const iconX = x + grid.padding + 20;
  const iconY = y + 50;
  try {
    await drawLucideIcon(ctx, "gamepad2", iconX, iconY, 40, colors.primary);
  } catch (error) {
    // Fallback if icon fails to load - continue without icon
    console.warn("Failed to load gamepad icon:", error);
  }
  
  // Draw text label
  ctx.fillText("SERVICIOS", x + grid.padding + 60, y + 60);
  
  // Draw all services using dynamic grid (no limits)
  services.forEach((service, index) => {
    const col = index % grid.columns;
    const row = Math.floor(index / grid.columns);
    const itemX = x + grid.padding + col * (grid.itemWidth + grid.gap);
    const itemY = y + titleHeight + grid.padding + row * (grid.itemHeight + grid.gap);
    
    // Animate entrance (slide in from left)
    const animationOffset = Math.max(0, 30 - frame * 2);
    const finalX = itemX - animationOffset;
    
    // Service card background
    ctx.fillStyle = "rgba(0, 147, 247, 0.15)";
    ctx.fillRect(finalX, itemY, grid.itemWidth, grid.itemHeight - 15);
    
    // Service name (uses calculated itemName fontSize)
    ctx.fillStyle = colors.text;
    ctx.font = `bold ${fontSizes.itemName}px Arial, sans-serif`;
    ctx.textAlign = "left";
    // Truncate text if too long
    const maxNameWidth = grid.itemWidth - 30;
    let serviceName = service.name;
    const metrics = ctx.measureText(serviceName);
    if (metrics.width > maxNameWidth) {
      while (ctx.measureText(serviceName + "...").width > maxNameWidth && serviceName.length > 0) {
        serviceName = serviceName.slice(0, -1);
      }
      serviceName += "...";
    }
    // Use drawTextWithContrast for better readability over backgrounds
    drawTextWithContrast(ctx, serviceName, finalX + 15, itemY + 35, {
      strokeWidth: Math.max(1, Math.round(fontSizes.itemName / 24)), // Proportional stroke width
      enableStroke: true,
      enableShadow: true,
    });
    
    // Duration and prices info - display all available durations/prices horizontally
    if (service.durations_allowed.length > 0) {
      ctx.fillStyle = colors.warning;
      ctx.font = `${fontSizes.serviceDurationPrice}px Arial, sans-serif`; // Use larger font size for better readability
      ctx.textAlign = "left";
      
      // Sort durations to display in ascending order
      const sortedDurations = [...service.durations_allowed].sort((a, b) => a - b);
      
      // Build horizontal list of duration/price pairs
      const durationPricePairs: string[] = [];
      for (const duration of sortedDurations) {
        // Get price from duration_prices if available, otherwise calculate proportionally from base price
        let priceCents: number;
        if (service.duration_prices && service.duration_prices[duration] !== undefined) {
          priceCents = service.duration_prices[duration];
        } else {
          // Fallback: calculate proportionally from minimum duration and price
          const minDuration = Math.min(...service.durations_allowed);
          const basePriceCents = service.price_cents;
          priceCents = Math.round((duration / minDuration) * basePriceCents);
        }
        durationPricePairs.push(formatDurationPrice(duration, priceCents));
      }
      
      // Join with separator and render
      const durationPriceText = durationPricePairs.join(" | ");
      const maxWidth = grid.itemWidth - 30;
      let displayText = durationPriceText;
      
      // Truncate if too long (measure and cut if necessary)
      const textMetrics = ctx.measureText(displayText);
      if (textMetrics.width > maxWidth) {
        // Try to fit by removing pairs from the end
        let pairsToShow = durationPricePairs.length;
        while (pairsToShow > 1) {
          const truncated = durationPricePairs.slice(0, pairsToShow - 1).join(" | ") + "...";
          if (ctx.measureText(truncated).width <= maxWidth) {
            displayText = truncated;
            break;
          }
          pairsToShow--;
        }
        // If still too long with one pair, truncate the single pair text
        if (pairsToShow === 1 && ctx.measureText(displayText).width > maxWidth) {
          while (ctx.measureText(displayText + "...").width > maxWidth && displayText.length > 0) {
            displayText = displayText.slice(0, -1);
          }
          displayText += "...";
        }
      }
      
      // Use drawTextWithContrast for better readability over backgrounds
      drawTextWithContrast(ctx, displayText, finalX + 15, itemY + 65, {
        strokeWidth: Math.max(1, Math.round(fontSizes.serviceDurationPrice / 24)), // Proportional stroke width
        enableStroke: true,
        enableShadow: true,
      });
    }
  });
  
  return sectionHeight;
}

/**
 * Draw products section on canvas.
 * 
 * Note: This is an async function to support icon loading.
 */
export async function drawProductsSection(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  width: number,
  products: ProductItem[],
  colors: BrandingColors,
  frame: number
): Promise<number> {
  if (products.length === 0) return 0;
  
  // Get manual config if available
  const editorState = get(layoutEditorStore);
  const manualConfig = editorState.mode === "manual" ? editorState.manualConfig : null;
  
  // Calculate dynamic grid layout (use manual values if provided)
  const grid = calculateDynamicGrid({
    itemCount: products.length,
    availableWidth: width,
    preferredColumns: manualConfig?.columns ?? 3,
    minItemWidth: 250,
    maxItemWidth: 600,
    gap: manualConfig?.gap ?? 30,
    padding: manualConfig?.padding ?? 40,
    itemHeight: 80,
  });
  
  // Calculate section height dynamically
  const titleHeight = 80;
  const sectionHeight = grid.totalHeight + titleHeight;
  
  // Section background (semi-transparent if over background image)
  ctx.fillStyle = "rgba(26, 26, 26, 0.8)";
  ctx.fillRect(x, y, width, sectionHeight);
  
  // Calculate proportional font sizes based on manual config
  const fontSizes = calculateFontSizes(manualConfig?.fontSize ?? null);
  
  // Section title with icon (use calculated fontSize)
  ctx.fillStyle = colors.success;
  ctx.font = `bold ${fontSizes.title}px Arial, sans-serif`;
  ctx.textAlign = "left";
  
  // Draw icon next to text
  const iconX = x + grid.padding + 20;
  const iconY = y + 50;
  try {
    await drawLucideIcon(ctx, "popcorn", iconX, iconY, 40, colors.success);
  } catch (error) {
    // Fallback if icon fails to load
    console.warn("Failed to load popcorn icon:", error);
  }
  
  // Draw text label
  ctx.fillText("PRODUCTOS", x + grid.padding + 60, y + 60);
  
  // Draw all products using dynamic grid (no limits)
  products.forEach((product, index) => {
    const col = index % grid.columns;
    const row = Math.floor(index / grid.columns);
    const itemX = x + grid.padding + col * (grid.itemWidth + grid.gap);
    const itemY = y + titleHeight + grid.padding + row * (grid.itemHeight + grid.gap);
    
    // Animate entrance (fade in)
    const animationAlpha = Math.min(1, frame / 15);
    
    // Product card background
    ctx.globalAlpha = animationAlpha;
    ctx.fillStyle = "rgba(61, 173, 9, 0.15)";
    ctx.fillRect(itemX, itemY, grid.itemWidth, grid.itemHeight - 15);
    ctx.globalAlpha = 1;
    
    // Product name (uses calculated itemName fontSize)
    ctx.fillStyle = colors.text;
    ctx.font = `bold ${fontSizes.itemName}px Arial, sans-serif`;
    ctx.textAlign = "left";
    // Truncate text if too long
    const maxNameWidth = grid.itemWidth - 30;
    let productName = product.name;
    const metrics = ctx.measureText(productName);
    if (metrics.width > maxNameWidth) {
      while (ctx.measureText(productName + "...").width > maxNameWidth && productName.length > 0) {
        productName = productName.slice(0, -1);
      }
      productName += "...";
    }
    // Use drawTextWithContrast for better readability over backgrounds
    drawTextWithContrast(ctx, productName, itemX + 15, itemY + 35, {
      strokeWidth: Math.max(1, Math.round(fontSizes.itemName / 24)), // Proportional stroke width
      enableStroke: true,
      enableShadow: true,
    });
    
    // Price (uses calculated price fontSize)
    const price = `$${(product.price_cents / 100).toFixed(2)}`;
    ctx.fillStyle = colors.success;
    ctx.font = `bold ${fontSizes.price}px Arial, sans-serif`;
    ctx.textAlign = "right";
    // Use drawTextWithContrast for better readability over backgrounds
    drawTextWithContrast(ctx, price, itemX + grid.itemWidth - 15, itemY + 35, {
      strokeWidth: Math.max(1, Math.round(fontSizes.price / 24)), // Proportional stroke width
      strokeColor: "rgba(0, 0, 0, 0.9)", // Darker stroke for colored text
      enableStroke: true,
      enableShadow: true,
    });
    
    // Note: Stock information is intentionally omitted for public menu displays
  });
  
  return sectionHeight;
}

/**
 * Draw packages section on canvas.
 * 
 * Note: This is an async function to support icon loading.
 */
export async function drawPackagesSection(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  width: number,
  packages: PackageItem[],
  colors: BrandingColors,
  frame: number
): Promise<number> {
  if (packages.length === 0) return 0;
  
  // Get manual config if available
  const editorState = get(layoutEditorStore);
  const manualConfig = editorState.mode === "manual" ? editorState.manualConfig : null;
  
  // Calculate dynamic grid layout (use manual values if provided)
  const grid = calculateDynamicGrid({
    itemCount: packages.length,
    availableWidth: width,
    preferredColumns: manualConfig?.columns ?? 2,
    minItemWidth: 350,
    maxItemWidth: 900,
    gap: manualConfig?.gap ?? 30,
    padding: manualConfig?.padding ?? 40,
    itemHeight: 100,
  });
  
  // Calculate section height dynamically
  const titleHeight = 80;
  const sectionHeight = grid.totalHeight + titleHeight;
  
  // Section background (semi-transparent if over background image)
  ctx.fillStyle = "rgba(26, 26, 26, 0.8)";
  ctx.fillRect(x, y, width, sectionHeight);
  
  // Calculate proportional font sizes based on manual config
  const fontSizes = calculateFontSizes(manualConfig?.fontSize ?? null);
  
  // Section title with icon (use calculated fontSize)
  ctx.fillStyle = colors.warning;
  ctx.font = `bold ${fontSizes.title}px Arial, sans-serif`;
  ctx.textAlign = "left";
  
  // Draw icon next to text
  const iconX = x + grid.padding + 20;
  const iconY = y + 50;
  try {
    await drawLucideIcon(ctx, "package", iconX, iconY, 40, colors.warning);
  } catch (error) {
    // Fallback if icon fails to load
    console.warn("Failed to load package icon:", error);
  }
  
  // Draw text label
  ctx.fillText("PAQUETES", x + grid.padding + 60, y + 60);
  
  // Draw all packages using dynamic grid (no limits)
  packages.forEach((pkg, index) => {
    const col = index % grid.columns;
    const row = Math.floor(index / grid.columns);
    const itemX = x + grid.padding + col * (grid.itemWidth + grid.gap);
    const itemY = y + titleHeight + grid.padding + row * (grid.itemHeight + grid.gap);
    
    // Animate entrance (scale in)
    const animationScale = Math.min(1, frame / 20);
    const centerX = itemX + grid.itemWidth / 2;
    const centerY = itemY + grid.itemHeight / 2;
    
    // Package card background with gradient
    const gradient = ctx.createLinearGradient(itemX, itemY, itemX + grid.itemWidth, itemY + grid.itemHeight);
    gradient.addColorStop(0, "rgba(255, 206, 0, 0.15)");
    gradient.addColorStop(1, "rgba(255, 206, 0, 0.05)");
    ctx.fillStyle = gradient;
    
    // Apply scale animation
    ctx.save();
    ctx.translate(centerX, centerY);
    ctx.scale(animationScale, animationScale);
    ctx.translate(-centerX, -centerY);
    
    ctx.fillRect(itemX, itemY, grid.itemWidth, grid.itemHeight - 15);
    
    // Package name (uses calculated itemName fontSize)
    ctx.fillStyle = colors.text;
    ctx.font = `bold ${fontSizes.itemName}px Arial, sans-serif`;
    ctx.textAlign = "left";
    // Truncate text if too long
    const maxNameWidth = grid.itemWidth - 30;
    let packageName = pkg.name;
    const metrics = ctx.measureText(packageName);
    if (metrics.width > maxNameWidth) {
      while (ctx.measureText(packageName + "...").width > maxNameWidth && packageName.length > 0) {
        packageName = packageName.slice(0, -1);
      }
      packageName += "...";
    }
    // Use drawTextWithContrast for better readability over backgrounds
    drawTextWithContrast(ctx, packageName, itemX + 15, itemY + 35, {
      strokeWidth: Math.max(1, Math.round(fontSizes.itemName / 24)), // Proportional stroke width
      enableStroke: true,
      enableShadow: true,
    });
    
    // Price (prominent, uses calculated price fontSize)
    const price = `$${(pkg.price_cents / 100).toFixed(2)}`;
    ctx.fillStyle = colors.warning;
    ctx.font = `bold ${fontSizes.price}px Arial, sans-serif`;
    ctx.textAlign = "right";
    // Use drawTextWithContrast for better readability over backgrounds
    drawTextWithContrast(ctx, price, itemX + grid.itemWidth - 15, itemY + 35, {
      strokeWidth: Math.max(1, Math.round(fontSizes.price / 24)), // Proportional stroke width
      strokeColor: "rgba(0, 0, 0, 0.9)", // Darker stroke for colored text
      enableStroke: true,
      enableShadow: true,
    });
    
    // Description (if available, uses larger packageDescription fontSize for better readability)
    if (pkg.description) {
      ctx.fillStyle = colors.text;
      ctx.font = `${fontSizes.packageDescription}px Arial, sans-serif`;
      ctx.textAlign = "left";
      const maxWidth = grid.itemWidth - 30;
      let description = pkg.description;
      const descMetrics = ctx.measureText(description);
      if (descMetrics.width > maxWidth) {
        while (ctx.measureText(description + "...").width > maxWidth && description.length > 0) {
          description = description.slice(0, -1);
        }
        description += "...";
      }
      // Use drawTextWithContrast for better readability over backgrounds
      drawTextWithContrast(ctx, description, itemX + 15, itemY + 75, {
        strokeWidth: Math.max(1, Math.round(fontSizes.packageDescription / 24)), // Proportional stroke width
        enableStroke: true,
        enableShadow: true,
      });
    }
    
    ctx.restore();
  });
  
  return sectionHeight;
}

/**
 * Draw footer with branding info.
 */
export function drawFooter(
  ctx: CanvasRenderingContext2D,
  width: number,
  height: number,
  colors: BrandingColors
): void {
  const footerY = height - 80; // Increased footer height
  
  // Footer background (semi-transparent if over background image)
  ctx.fillStyle = "rgba(26, 26, 26, 0.8)";
  ctx.fillRect(0, footerY, width, 80);
  
  // Footer text (scaled: 28px)
  ctx.fillStyle = colors.text;
  ctx.font = "28px Arial, sans-serif";
  ctx.textAlign = "center";
  ctx.fillText("Visítanos y disfruta de la mejor experiencia", width / 2, footerY + 40);
  
  // Decorative line
  ctx.strokeStyle = colors.primary;
  ctx.lineWidth = 3; // Slightly thicker
  ctx.beginPath();
  ctx.moveTo(width * 0.1, footerY);
  ctx.lineTo(width * 0.9, footerY);
  ctx.stroke();
}

/**
 * Draw complete menu frame on canvas with pagination support.
 * 
 * @param hasBackground - If true, don't clear canvas (background image already drawn)
 * @param pageIndex - Zero-based index of current page (0 for first page)
 * @param totalPages - Total number of pages (1 if no pagination needed)
 * @param showFooter - Whether to show footer (typically only on last page)
 * 
 * Note: Items passed should already be filtered for the current page.
 * This function simply renders what it receives.
 * Note: This is an async function to support icon loading.
 */
export async function drawMenuFrame(
  ctx: CanvasRenderingContext2D,
  width: number,
  height: number,
  services: ServiceItem[],
  products: ProductItem[],
  packages: PackageItem[] = [],
  colors: BrandingColors,
  frame: number,
  hasBackground: boolean = false,
  pageIndex: number = 0,
  totalPages: number = 1,
  showFooter: boolean = false
): Promise<void> {
  // Only clear canvas if no background image exists
  // If background exists, it was already drawn in MenuPreview.drawFrame()
  if (!hasBackground) {
    ctx.fillStyle = colors.background;
    ctx.fillRect(0, 0, width, height);
  }
  
  // Draw header only on first page if no background
  if (!hasBackground && pageIndex === 0) {
    drawBrandingHeader(ctx, width, height, colors);
  }
  
  // Start Y position
  let currentY = hasBackground ? 20 : (pageIndex === 0 ? 180 : 20);
  const sectionGap = 20;
  
  // Services section
  if (services.length > 0) {
    const sectionHeight = await drawServicesSection(ctx, 0, currentY, width, services, colors, frame);
    currentY += sectionHeight + sectionGap;
  }
  
  // Packages section
  if (packages.length > 0) {
    const sectionHeight = await drawPackagesSection(ctx, 0, currentY, width, packages, colors, frame);
    currentY += sectionHeight + sectionGap;
  }
  
  // Products section
  if (products.length > 0) {
    const sectionHeight = await drawProductsSection(ctx, 0, currentY, width, products, colors, frame);
    currentY += sectionHeight + sectionGap;
  }
  
  // Draw footer only if requested (typically on last page)
  if (showFooter) {
    drawFooter(ctx, width, height, colors);
  }
}

/**
 * Calculate total content height for all sections.
 * 
 * This is used to determine pagination needs.
 */
export function calculateTotalContentHeight(
  width: number,
  services: ServiceItem[],
  products: ProductItem[],
  packages: PackageItem[]
): number {
  // Get manual config if available
  const editorState = get(layoutEditorStore);
  const manualConfig = editorState.mode === "manual" ? editorState.manualConfig : null;
  
  let totalHeight = 0;
  const sectionGap = 20;
  const titleHeight = 80; // Height for section titles
  
  // Services section height
  if (services.length > 0) {
    const servicesGrid = calculateDynamicGrid({
      itemCount: services.length,
      availableWidth: width,
      preferredColumns: manualConfig?.columns ?? 2,
      minItemWidth: 300,
      maxItemWidth: 900,
      gap: manualConfig?.gap ?? 30,
      padding: manualConfig?.padding ?? 40,
      itemHeight: 80,
    });
    totalHeight += servicesGrid.totalHeight + titleHeight + sectionGap;
  }
  
  // Packages section height
  if (packages.length > 0) {
    const packagesGrid = calculateDynamicGrid({
      itemCount: packages.length,
      availableWidth: width,
      preferredColumns: manualConfig?.columns ?? 2,
      minItemWidth: 300,
      maxItemWidth: 900,
      gap: manualConfig?.gap ?? 30,
      padding: manualConfig?.padding ?? 40,
      itemHeight: 100,
    });
    totalHeight += packagesGrid.totalHeight + titleHeight + sectionGap;
  }
  
  // Products section height
  if (products.length > 0) {
    const productsGrid = calculateDynamicGrid({
      itemCount: products.length,
      availableWidth: width,
      preferredColumns: manualConfig?.columns ?? 3,
      minItemWidth: 250,
      maxItemWidth: 600,
      gap: manualConfig?.gap ?? 30,
      padding: manualConfig?.padding ?? 40,
      itemHeight: 80,
    });
    totalHeight += productsGrid.totalHeight + titleHeight + sectionGap;
  }
  
  return totalHeight;
}

/**
 * Calculate total pages needed for all content.
 * 
 * This is a helper function that can be called from MenuPreview to determine pagination.
 */
export function calculateMenuPages(
  width: number,
  height: number,
  services: ServiceItem[],
  products: ProductItem[],
  packages: PackageItem[],
  hasBackground: boolean = false
): number {
  const headerHeight = hasBackground ? 0 : 160;
  const footerHeight = 80;
  const totalContentHeight = calculateTotalContentHeight(width, services, products, packages);
  const availableHeightPerPage = height - headerHeight - footerHeight;
  
  // CRITICAL FIX: Use availableHeightPerPage instead of height
  // This ensures pagination calculation uses the correct available space per page
  const pagesNeeded = calculatePagesNeeded(
    totalContentHeight,
    availableHeightPerPage,
    headerHeight,
    footerHeight
  );
  
  // Log calculation in dev mode for debugging (only when result changes)
  // Use a static variable to track last logged result to avoid excessive logging
  if (import.meta.env?.DEV) {
    const lastLogged = (calculateMenuPages as any).__lastLogged;
    const shouldLog = !lastLogged || 
      lastLogged.pagesNeeded !== pagesNeeded ||
      lastLogged.totalContentHeight !== totalContentHeight ||
      lastLogged.itemCounts?.services !== services.length ||
      lastLogged.itemCounts?.products !== products.length ||
      lastLogged.itemCounts?.packages !== packages.length;
    
    if (shouldLog) {
      console.log("[calculateMenuPages] Pagination calculation:", {
        totalContentHeight,
        availableHeightPerPage,
        height,
        headerHeight,
        footerHeight,
        pagesNeeded,
        hasBackground,
        itemCounts: {
          services: services.length,
          products: products.length,
          packages: packages.length,
        },
      });
      // Store last logged values to avoid duplicate logs
      (calculateMenuPages as any).__lastLogged = {
        pagesNeeded,
        totalContentHeight,
        itemCounts: {
          services: services.length,
          products: products.length,
          packages: packages.length,
        },
      };
    }
  }
  
  return pagesNeeded;
}
















