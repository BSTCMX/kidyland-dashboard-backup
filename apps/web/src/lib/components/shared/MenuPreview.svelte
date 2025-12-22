<script lang="ts">
  /**
   * MenuPreview component - Real-time preview of menu board with auto-update.
   * 
   * Automatically updates when items, background image, or layout changes.
   * Uses debouncing and requestAnimationFrame for performance.
   */
  import { onMount, onDestroy } from "svelte";
  import { drawMenuFrame, calculateMenuPages, calculateTotalContentHeight, KIDYLAND_COLORS, type ServiceItem, type ProductItem, type PackageItem } from "$lib/utils/video-canvas";
  import type { BackgroundImage } from "$lib/schemas/background-image-schema";
  import type { LayoutStyle } from "$lib/schemas/layout-style-schema";
  import { calculateAutoLayout } from "$lib/utils/layout-helpers";
  import { getItemsForPage } from "$lib/utils/canvas-layout";
  import { loadFFmpeg } from "$lib/utils/video-export";
  import { configureCanvasQuality } from "$lib/utils/canvas-quality";
  import { layoutEditorStore } from "$lib/stores/layout-editor";

  export let backgroundImage: BackgroundImage | null = null;
  export let layoutStyle: LayoutStyle | null = null;
  export let services: ServiceItem[] = [];
  export let products: ProductItem[] = [];
  export let packages: PackageItem[] = [];
  export let width: number = 1920;
  export let height: number = 1080;
  export let autoPlay: boolean = true;
  export let fps: number = 25;

  let canvas: HTMLCanvasElement;
  let ctx: CanvasRenderingContext2D | null = null;
  let animationFrameId: number | null = null;
  let previewTimeout: number | null = null;
  let frame = 0;
  let isPlaying = false;
  let lastUpdateTime = 0;
  let backgroundImageElement: HTMLImageElement | null = null;
  let backgroundImageLoaded = false;
  
  // Pagination state
  let currentPage = 0;
  let totalPages = 1;
  let pageItems: {
    services: ServiceItem[];
    products: ProductItem[];
    packages: PackageItem[];
  } = {
    services: [],
    products: [],
    packages: [],
  };
  const PAGE_DURATION = 5000; // 5 seconds per page

  // Debounce delay for updates (ms)
  const DEBOUNCE_DELAY = 300;
  const FRAME_DURATION = 1000 / fps; // ms per frame

  // Load background image when backgroundImage changes
  $: if (backgroundImage?.imagePath) {
    loadBackgroundImage(backgroundImage.imagePath);
  }

  // Calculate pages when items, dimensions, or layout config change
  // CRITICAL: Include layoutEditorStore in reactive dependencies to recalculate when manual config changes
  // Use a variable to track last calculated values to avoid excessive logging
  let lastPaginationState: {
    pages: number;
    totalItems: number;
    totalHeight: number;
    layoutMode: string;
  } | null = null;

  $: if (width && height && (services.length > 0 || products.length > 0 || packages.length > 0)) {
    const hasBg = backgroundImageElement && backgroundImageLoaded;
    const layoutConfig = $layoutEditorStore; // Subscribe to store changes
    
    // Recalculate pages (this will use current manualConfig if mode is manual)
    const calculatedPages = calculateMenuPages(width, height, services, products, packages, hasBg || false);
    
    // Log pagination calculation in dev mode for debugging (only when result changes)
    if (import.meta.env?.DEV) {
      const totalItems = services.length + products.length + packages.length;
      const totalHeight = calculateTotalContentHeight(width, services, products, packages);
      const availableHeight = height - (hasBg ? 0 : 160) - 80;
      
      const shouldLog = !lastPaginationState ||
        lastPaginationState.pages !== calculatedPages ||
        lastPaginationState.totalItems !== totalItems ||
        lastPaginationState.totalHeight !== totalHeight ||
        lastPaginationState.layoutMode !== layoutConfig.mode;
      
      if (shouldLog) {
        console.log("[MenuPreview] Pagination calculation:", {
          totalItems,
          totalHeight,
          availableHeight,
          calculatedPages,
          layoutMode: layoutConfig.mode,
          manualConfig: layoutConfig.mode === "manual" ? layoutConfig.manualConfig : null,
        });
        lastPaginationState = {
          pages: calculatedPages,
          totalItems,
          totalHeight,
          layoutMode: layoutConfig.mode,
        };
      }
    }
    
    totalPages = calculatedPages;
    
    // Reset to first page if current page is out of bounds
    if (currentPage >= totalPages) {
      currentPage = 0;
    }
    updatePageItems();
  }

  // Update page items when page or items change
  $: if (totalPages > 0) {
    updatePageItems();
  }

  // Reactive: Update preview when dependencies change
  $: if (backgroundImage && layoutStyle && backgroundImageLoaded && (services.length > 0 || products.length > 0 || packages.length > 0)) {
    scheduleUpdate();
  }

  function updatePageItems() {
    if (totalPages === 1) {
      // Single page: show all items
      pageItems = {
        services: [...services],
        products: [...products],
        packages: [...packages],
      };
      return;
    }

    // Multi-page: divide items proportionally
    // Simple approach: divide each section equally across pages
    const servicesPerPage = Math.ceil(services.length / totalPages);
    const productsPerPage = Math.ceil(products.length / totalPages);
    const packagesPerPage = Math.ceil(packages.length / totalPages);

    const startServices = currentPage * servicesPerPage;
    const startProducts = currentPage * productsPerPage;
    const startPackages = currentPage * packagesPerPage;

    pageItems = {
      services: services.slice(startServices, startServices + servicesPerPage),
      products: products.slice(startProducts, startProducts + productsPerPage),
      packages: packages.slice(startPackages, startPackages + packagesPerPage),
    };
  }

  function loadBackgroundImage(imagePath: string) {
    backgroundImageLoaded = false;
    backgroundImageElement = new Image();
    backgroundImageElement.crossOrigin = "anonymous"; // Enable CORS if needed
    
    backgroundImageElement.onload = () => {
      backgroundImageLoaded = true;
      scheduleUpdate();
    };
    
    backgroundImageElement.onerror = () => {
      console.error("Error loading background image:", imagePath);
      backgroundImageLoaded = false;
      // Fallback to solid color background
    };
    
    backgroundImageElement.src = imagePath;
  }

  onMount(() => {
    // Pre-load FFmpeg in background (non-blocking) for faster export later
    // This improves UX by loading FFmpeg while user is configuring the menu
    loadFFmpeg().catch((error) => {
      // Silently fail - FFmpeg will be loaded again when user exports
      if (import.meta.env?.DEV) {
        console.warn("[MenuPreview] FFmpeg preload failed (will retry on export):", error);
      }
    });

    if (canvas) {
      canvas.width = width;
      canvas.height = height;
      ctx = canvas.getContext("2d");
      
      // Configure canvas for optimal rendering quality
      // This ensures sharp text and graphics, especially important for exports
      if (ctx) {
        configureCanvasQuality(ctx);
      }
      
      if (autoPlay) {
        startPreview();
      } else {
        drawFrame(0);
      }
    }
  });

  onDestroy(() => {
    stopPreview();
    if (previewTimeout) {
      clearTimeout(previewTimeout);
    }
  });

  function scheduleUpdate() {
    // Debounce updates to avoid excessive redraws
    if (previewTimeout) {
      clearTimeout(previewTimeout);
    }

    previewTimeout = window.setTimeout(() => {
      if (!isPlaying) {
        drawFrame(0);
      }
    }, DEBOUNCE_DELAY);
  }

  function drawFrame(currentFrame: number) {
    if (!ctx || !backgroundImage || !layoutStyle) return;

    const hasBackgroundImage = backgroundImageElement && backgroundImageLoaded;

    // Only clear canvas if we don't have a background image
    // If we have a background image, we'll draw it first, then draw menu items on top
    if (!hasBackgroundImage) {
      ctx.clearRect(0, 0, width, height);
      // Fallback: use solid background color from layout branding or default
      ctx.fillStyle = layoutStyle.branding?.colors.background || KIDYLAND_COLORS.background;
      ctx.fillRect(0, 0, width, height);
    }

    // Draw background image if loaded (this goes first, before menu items)
    if (hasBackgroundImage && backgroundImageElement) {
      try {
        // Draw the background image exactly at canvas size (1920x1080, no scaling needed)
        ctx.drawImage(backgroundImageElement, 0, 0, width, height);
      } catch (error) {
        console.error("Error drawing background image:", error);
        // Fallback: clear and use solid color
        ctx.clearRect(0, 0, width, height);
        ctx.fillStyle = layoutStyle.branding?.colors.background || KIDYLAND_COLORS.background;
        ctx.fillRect(0, 0, width, height);
      }
    }

    // Draw menu frame with current page items (on top of background)
    // Note: drawMenuFrame is async due to icon loading, but we call it without await
    // for performance. Icons will be cached after first load.
    try {
      const showFooter = currentPage === totalPages - 1;
      drawMenuFrame(
        ctx,
        width,
        height,
        pageItems.services,
        pageItems.products,
        pageItems.packages,
        KIDYLAND_COLORS,
        currentFrame,
        hasBackgroundImage || false, // Pass flag to prevent clearing canvas in drawMenuFrame
        currentPage,
        totalPages,
        showFooter
      ).catch((error) => {
        console.error("Error drawing menu frame:", error);
      });
    } catch (error) {
      console.error("Error drawing menu frame:", error);
    }
  }

  function startPreview() {
    if (isPlaying) return;
    
    isPlaying = true;
    frame = 0;
    lastUpdateTime = performance.now();
    animate();
  }

  function stopPreview() {
    isPlaying = false;
    if (animationFrameId) {
      cancelAnimationFrame(animationFrameId);
      animationFrameId = null;
    }
  }

  function animate() {
    if (!isPlaying || !ctx || !backgroundImage || !layoutStyle) {
      return;
    }

    const now = performance.now();
    const elapsed = now - lastUpdateTime;

    // Only advance frame if enough time has passed
    if (elapsed >= FRAME_DURATION) {
      frame = (frame + 1) % (fps * 10); // 10 second loop
      
      // Advance page every PAGE_DURATION milliseconds
      const totalFramesPerPage = (PAGE_DURATION / 1000) * fps;
      const newPage = Math.floor(frame / totalFramesPerPage) % totalPages;
      if (newPage !== currentPage) {
        currentPage = newPage;
        updatePageItems();
      }
      
      lastUpdateTime = now;
      drawFrame(frame);
    }

    animationFrameId = requestAnimationFrame(animate);
  }

  // Public methods for external control
  export function play() {
    startPreview();
  }

  export function pause() {
    stopPreview();
    if (ctx) {
      drawFrame(frame);
    }
  }

  // Expose canvas element
  export function getCanvas(): HTMLCanvasElement | null {
    return canvas;
  }

  // Expose isPlaying state for external checks via method (not variable)
  // This follows the pattern of other exported methods (play, pause, getCanvas)
  // and is compatible with bind:this without requiring accessors
  export function getIsPlaying(): boolean {
    return isPlaying;
  }
</script>

<div class="menu-preview">
  <div class="preview-container">
    <canvas
      bind:this={canvas}
      class="preview-canvas"
      style="max-width: 100%; height: auto;"
    ></canvas>
  </div>
  
  {#if backgroundImage && layoutStyle && (services.length > 0 || products.length > 0 || packages.length > 0)}
    <div class="preview-info">
      <span class="info-text">
        Vista previa • {backgroundImage.name} • {layoutStyle.name} • {services.length + products.length + packages.length} items
        {#if totalPages > 1}
          • Página {currentPage + 1} de {totalPages}
        {/if}
      </span>
    </div>
  {:else if !backgroundImage || !layoutStyle}
    <div class="preview-empty">
      <p>Selecciona imagen de fondo y distribución para ver la vista previa</p>
    </div>
  {:else}
    <div class="preview-empty">
      <p>Selecciona items para ver la vista previa</p>
    </div>
  {/if}
</div>

<style>
  .menu-preview {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-md);
    width: 100%;
  }

  .preview-container {
    width: 100%;
    background: var(--theme-bg-secondary);
    border-radius: var(--radius-md);
    border: 2px solid var(--border-primary);
    padding: var(--spacing-md);
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 400px;
    overflow: auto;
  }

  .preview-canvas {
    display: block;
    border-radius: var(--radius-sm);
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
    max-width: 100%;
    height: auto;
  }

  .preview-info {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: var(--spacing-sm) var(--spacing-md);
    background: var(--theme-bg-secondary);
    border-radius: var(--radius-sm);
  }

  .info-text {
    font-size: var(--text-sm);
    color: var(--text-secondary);
    font-weight: 500;
  }

  .preview-empty {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: var(--spacing-xl);
    background: var(--theme-bg-secondary);
    border-radius: var(--radius-md);
    border: 2px dashed var(--border-primary);
    min-height: 200px;
  }

  .preview-empty p {
    font-size: var(--text-base);
    color: var(--text-secondary);
    margin: 0;
    text-align: center;
  }

  /* Responsive */
  @media (max-width: 768px) {
    .preview-container {
      padding: var(--spacing-sm);
      min-height: 300px;
    }

    .preview-canvas {
      max-width: 100%;
    }
  }
</style>
