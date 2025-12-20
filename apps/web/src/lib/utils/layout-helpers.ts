/**
 * Layout Helpers - Auto-layout algorithms for menu items.
 * 
 * Calculates optimal positions for items based on template layout configuration.
 */

import type { Template } from "$lib/schemas/template-schema";
import type { ServiceItem, ProductItem, PackageItem } from "$lib/utils/video-canvas";

export interface ItemPosition {
  /** Item identifier */
  id: string;
  /** Item name */
  name: string;
  /** Row position (1-based) */
  row: number;
  /** Column position (1-based) */
  col: number;
  /** Item type for styling */
  type: "service" | "product" | "package";
}

export interface LayoutResult {
  /** Calculated positions for all items */
  items: ItemPosition[];
  /** Total number of rows needed */
  totalRows: number;
  /** Total number of columns (from template) */
  totalCols: number;
}

/**
 * Calculate auto-layout positions for items using CSS Grid algorithm.
 * 
 * This function arranges items in a grid based on the template's column configuration.
 * Items are placed left-to-right, top-to-bottom.
 * 
 * @param services - Array of service items
 * @param products - Array of product items
 * @param packages - Array of package items
 * @param template - Template configuration with layout settings
 * @returns Layout result with calculated positions
 */
export function calculateAutoLayout(
  services: ServiceItem[],
  products: ProductItem[],
  packages: PackageItem[],
  template: Template
): LayoutResult {
  const columns = template.layout.grid.columns;
  const items: ItemPosition[] = [];

  // Combine all items into a single array with type information
  const allItems: Array<{
    id: string;
    name: string;
    type: "service" | "product" | "package";
  }> = [
    ...services.map((s) => ({ id: s.id, name: s.name, type: "service" as const })),
    ...products.map((p) => ({ id: p.id, name: p.name, type: "product" as const })),
    ...packages.map((p) => ({ id: p.id, name: p.name, type: "package" as const })),
  ];

  // Calculate positions using grid algorithm
  allItems.forEach((item, index) => {
    // Calculate row and column (1-based indexing)
    const row = Math.floor(index / columns) + 1;
    const col = (index % columns) + 1;

    items.push({
      id: item.id,
      name: item.name,
      row,
      col,
      type: item.type,
    });
  });

  // Calculate total rows needed
  const totalRows = Math.ceil(allItems.length / columns);

  return {
    items,
    totalRows,
    totalCols: columns,
  };
}

/**
 * Calculate item dimensions based on template layout.
 * 
 * Takes into account grid padding, gap, and available space.
 * 
 * @param template - Template configuration
 * @param canvasWidth - Canvas width in pixels
 * @param canvasHeight - Canvas height in pixels
 * @returns Item dimensions in pixels
 */
export function calculateItemDimensions(
  template: Template,
  canvasWidth: number,
  canvasHeight: number
): { width: number; height: number } {
  const { grid, header, footer } = template.layout;

  // Calculate available space for grid
  const headerHeight = header?.height || 0;
  const footerHeight = footer?.height || 0;
  const verticalPadding = grid.padding * 2;
  const availableHeight = canvasHeight - headerHeight - footerHeight - verticalPadding;

  // Calculate item width (accounting for gaps)
  const horizontalPadding = grid.padding * 2;
  const totalGapWidth = grid.gap * (grid.columns - 1);
  const itemWidth = Math.floor((canvasWidth - horizontalPadding - totalGapWidth) / grid.columns);

  // Calculate item height (estimate, could be improved with dynamic calculation)
  // For now, use a reasonable aspect ratio
  const estimatedRows = 10; // Rough estimate
  const totalGapHeight = grid.gap * (estimatedRows - 1);
  const itemHeight = Math.floor((availableHeight - totalGapHeight) / estimatedRows);

  return {
    width: Math.max(itemWidth, 100), // Minimum width
    height: Math.max(itemHeight, 80), // Minimum height
  };
}

/**
 * Calculate position (x, y) for an item based on its grid position.
 * 
 * @param item - Item position from layout
 * @param template - Template configuration
 * @param canvasWidth - Canvas width in pixels
 * @param canvasHeight - Canvas height in pixels
 * @returns Pixel coordinates { x, y }
 */
export function calculateItemPixelPosition(
  item: ItemPosition,
  template: Template,
  canvasWidth: number,
  canvasHeight: number
): { x: number; y: number } {
  const { grid, header } = template.layout;
  const dimensions = calculateItemDimensions(template, canvasWidth, canvasHeight);

  // Calculate X position
  const horizontalPadding = grid.padding;
  const x = horizontalPadding + (item.col - 1) * (dimensions.width + grid.gap);

  // Calculate Y position (accounting for header)
  const headerHeight = header?.height || 0;
  const verticalPadding = grid.padding;
  const y = headerHeight + verticalPadding + (item.row - 1) * (dimensions.height + grid.gap);

  return { x, y };
}
