/**
 * Layout Preview Utilities - Generate visual previews of layout styles.
 * 
 * Creates canvas-based previews showing grid structure and spacing.
 */

import type { LayoutStyle } from "$lib/schemas/layout-style-schema";

/**
 * Generate a canvas preview of a layout style.
 * 
 * @param layoutStyle - The layout style to preview
 * @param size - Preview size in pixels (default: 200x112, maintaining 16:9 aspect ratio)
 * @returns Data URL of the preview image, or null if generation fails
 */
export function generateLayoutPreview(
  layoutStyle: LayoutStyle,
  size: { width: number; height: number } = { width: 200, height: 112 }
): string | null {
  try {
    const canvas = document.createElement("canvas");
    canvas.width = size.width;
    canvas.height = size.height;
    const ctx = canvas.getContext("2d");
    
    if (!ctx) return null;

    // Background
    ctx.fillStyle = "#1a1a1a";
    ctx.fillRect(0, 0, size.width, size.height);

    const { grid, header, footer } = layoutStyle.layout;

    // Draw header area
    if (header) {
      const headerHeight = Math.floor((size.height * header.height) / 1080);
      ctx.fillStyle = "rgba(0, 147, 247, 0.3)";
      ctx.fillRect(0, 0, size.width, headerHeight);
      
      // Header border
      ctx.strokeStyle = "rgba(0, 147, 247, 0.5)";
      ctx.lineWidth = 1;
      ctx.strokeRect(0, 0, size.width, headerHeight);
    }

    // Draw footer area
    if (footer) {
      const footerHeight = Math.floor((size.height * footer.height) / 1080);
      const footerY = size.height - footerHeight;
      ctx.fillStyle = "rgba(61, 173, 9, 0.3)";
      ctx.fillRect(0, footerY, size.width, footerHeight);
      
      // Footer border
      ctx.strokeStyle = "rgba(61, 173, 9, 0.5)";
      ctx.lineWidth = 1;
      ctx.strokeRect(0, footerY, size.width, footerHeight);
    }

    // Calculate grid area
    const headerHeight = header ? Math.floor((size.height * header.height) / 1080) : 0;
    const footerHeight = footer ? Math.floor((size.height * footer.height) / 1080) : 0;
    const gridHeight = size.height - headerHeight - footerHeight;
    const gridPadding = Math.floor((size.width * grid.padding) / 1920);
    const gridGap = Math.floor((size.width * grid.gap) / 1920);
    
    const gridX = gridPadding;
    const gridY = headerHeight + gridPadding;
    const gridWidth = size.width - (gridPadding * 2);
    const gridAreaHeight = gridHeight - (gridPadding * 2);

    // Calculate item dimensions
    const totalGapWidth = gridGap * (grid.columns - 1);
    const itemWidth = Math.floor((gridWidth - totalGapWidth) / grid.columns);
    const estimatedRows = Math.max(2, Math.floor(gridAreaHeight / (itemWidth * 0.6)));
    const totalGapHeight = gridGap * (estimatedRows - 1);
    const itemHeight = Math.floor((gridAreaHeight - totalGapHeight) / estimatedRows);

    // Draw grid items (simplified preview - show first few items)
    ctx.fillStyle = "rgba(255, 255, 255, 0.1)";
    ctx.strokeStyle = "rgba(255, 255, 255, 0.2)";
    ctx.lineWidth = 1;

    const maxPreviewItems = Math.min(grid.columns * 2, 8); // Show max 2 rows or 8 items
    for (let i = 0; i < maxPreviewItems; i++) {
      const row = Math.floor(i / grid.columns);
      const col = i % grid.columns;
      
      const x = gridX + col * (itemWidth + gridGap);
      const y = gridY + row * (itemHeight + gridGap);
      
      ctx.fillRect(x, y, itemWidth, itemHeight);
      ctx.strokeRect(x, y, itemWidth, itemHeight);
    }

    // Draw column indicator
    ctx.fillStyle = "rgba(0, 147, 247, 0.5)";
    ctx.font = `bold ${Math.floor(size.width / 15)}px Arial, sans-serif`;
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    const centerY = headerHeight + gridPadding + gridAreaHeight / 2;
    ctx.fillText(`${grid.columns} columnas`, size.width / 2, centerY);

    return canvas.toDataURL("image/png");
  } catch (error) {
    console.error("Error generating layout preview:", error);
    return null;
  }
}














