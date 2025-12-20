/**
 * Canvas Layout Utilities - Dynamic grid calculation for canvas rendering.
 * 
 * Provides functions to calculate optimal grid layouts for rendering items
 * on canvas without hardcoded limits, with automatic spacing adjustments.
 */

export interface GridConfig {
  /** Number of columns in the grid */
  columns: number;
  /** Width of each item in pixels */
  itemWidth: number;
  /** Height of each item in pixels */
  itemHeight: number;
  /** Gap between items in pixels */
  gap: number;
  /** Padding around the grid in pixels */
  padding: number;
  /** Number of rows needed for all items */
  rows: number;
  /** Total height needed for all items */
  totalHeight: number;
}

export interface DynamicGridOptions {
  /** Total number of items to display */
  itemCount: number;
  /** Available width in pixels */
  availableWidth: number;
  /** Preferred number of columns (will be adjusted if needed) */
  preferredColumns?: number;
  /** Minimum item width in pixels */
  minItemWidth?: number;
  /** Maximum item width in pixels */
  maxItemWidth?: number;
  /** Gap between items in pixels */
  gap?: number;
  /** Padding around grid in pixels */
  padding?: number;
  /** Item height in pixels */
  itemHeight?: number;
}

/**
 * Calculate optimal grid layout dynamically based on item count and available space.
 * 
 * Automatically adjusts columns to fit items optimally without hardcoded limits.
 * 
 * @param options - Grid calculation options
 * @returns Grid configuration with calculated dimensions
 */
export function calculateDynamicGrid(options: DynamicGridOptions): GridConfig {
  const {
    itemCount,
    availableWidth,
    preferredColumns = 3,
    minItemWidth = 200,
    maxItemWidth = 600,
    gap = 30,
    padding = 40,
    itemHeight = 80,
  } = options;

  if (itemCount === 0) {
    return {
      columns: 0,
      itemWidth: 0,
      itemHeight,
      gap,
      padding,
      rows: 0,
      totalHeight: 0,
    };
  }

  // Calculate available width for items (excluding padding)
  const availableItemsWidth = availableWidth - (padding * 2);
  
  // Try preferred columns first
  let columns = preferredColumns;
  let itemWidth = Math.floor((availableItemsWidth - (gap * (columns - 1))) / columns);
  
  // Adjust if item width is too small or too large
  if (itemWidth < minItemWidth && columns > 1) {
    // Reduce columns to increase item width
    while (itemWidth < minItemWidth && columns > 1) {
      columns--;
      itemWidth = Math.floor((availableItemsWidth - (gap * (columns - 1))) / columns);
    }
  } else if (itemWidth > maxItemWidth) {
    // Increase columns to decrease item width (but not beyond item count)
    while (itemWidth > maxItemWidth && columns < itemCount) {
      columns++;
      itemWidth = Math.floor((availableItemsWidth - (gap * (columns - 1))) / columns);
    }
  }
  
  // Ensure we don't have more columns than items
  columns = Math.min(columns, itemCount);
  
  // Recalculate item width with final column count
  itemWidth = Math.floor((availableItemsWidth - (gap * (columns - 1))) / columns);
  
  // Ensure item width respects min/max bounds
  itemWidth = Math.max(minItemWidth, Math.min(maxItemWidth, itemWidth));
  
  // Calculate rows needed
  const rows = Math.ceil(itemCount / columns);
  
  // Calculate total height needed
  const totalHeight = (rows * itemHeight) + ((rows - 1) * gap) + (padding * 2);
  
  return {
    columns,
    itemWidth,
    itemHeight,
    gap,
    padding,
    rows,
    totalHeight,
  };
}

/**
 * Calculate section height dynamically based on item count.
 * 
 * @param itemCount - Number of items in the section
 * @param itemHeight - Height of each item
 * @param gap - Gap between items
 * @param padding - Padding around section
 * @param maxColumns - Maximum columns to use
 * @returns Height needed for the section
 */
export function calculateSectionHeight(
  itemCount: number,
  itemHeight: number,
  gap: number,
  padding: number,
  maxColumns: number
): number {
  if (itemCount === 0) return 0;
  
  const rows = Math.ceil(itemCount / maxColumns);
  return (rows * itemHeight) + ((rows - 1) * gap) + (padding * 2) + 80; // +80 for title
}

/**
 * Calculate how many pages are needed to display all content.
 * 
 * Divides content into pages that fit within the available canvas height.
 * 
 * @param totalContentHeight - Total height needed for all content (items + sections)
 * @param availableHeight - Available height per page (canvas height - reserved space)
 * @param headerHeight - Height reserved for header (if any)
 * @param footerHeight - Height reserved for footer (if any)
 * @returns Number of pages needed (minimum 1)
 */
export function calculatePagesNeeded(
  totalContentHeight: number,
  availableHeight: number,
  headerHeight: number = 0,
  footerHeight: number = 0
): number {
  // Available height per page = total - header - footer
  const effectiveHeightPerPage = availableHeight - headerHeight - footerHeight;
  
  if (effectiveHeightPerPage <= 0) {
    return 1; // Minimum 1 page even if calculation is invalid
  }
  
  if (totalContentHeight <= effectiveHeightPerPage) {
    return 1; // All content fits in one page
  }
  
  // Calculate pages needed (always round up)
  const pagesNeeded = Math.ceil(totalContentHeight / effectiveHeightPerPage);
  
  // Ensure at least 1 page
  return Math.max(1, pagesNeeded);
}

/**
 * Get items for a specific page using pagination.
 * 
 * @param allItems - Array of all items
 * @param pageIndex - Zero-based page index
 * @param itemsPerPage - Maximum number of items per page
 * @returns Array of items for the specified page
 */
export function getItemsForPage<T>(
  allItems: T[],
  pageIndex: number,
  itemsPerPage: number
): T[] {
  if (itemsPerPage <= 0 || pageIndex < 0) {
    return [];
  }
  
  const startIndex = pageIndex * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  
  return allItems.slice(startIndex, endIndex);
}

/**
 * Get items for a specific page using proportional division across multiple pages.
 * 
 * This divides items proportionally across pages, similar to how MenuPreview handles pagination.
 * Each page gets approximately the same number of items, rounded up.
 * 
 * @param allItems - Array of all items
 * @param pageIndex - Zero-based page index
 * @param totalPages - Total number of pages
 * @returns Array of items for the specified page
 */
export function getItemsForPageProportional<T>(
  allItems: T[],
  pageIndex: number,
  totalPages: number
): T[] {
  if (totalPages <= 0 || pageIndex < 0 || pageIndex >= totalPages) {
    return [];
  }
  
  if (totalPages === 1) {
    // Single page: return all items
    return [...allItems];
  }
  
  // Multi-page: divide items proportionally
  // Calculate items per page (rounded up)
  const itemsPerPage = Math.ceil(allItems.length / totalPages);
  const startIndex = pageIndex * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  
  return allItems.slice(startIndex, endIndex);
}

