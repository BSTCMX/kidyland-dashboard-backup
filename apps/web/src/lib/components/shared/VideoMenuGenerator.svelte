<script lang="ts">
  /**
   * VideoMenuGenerator component - Generates animated menu video using HTML5 Canvas.
   * 
   * Creates animated canvas with Kidyland branding, services, and products.
   * Uses MediaRecorder API for video capture.
   */
  import { onMount, onDestroy } from "svelte";
  import { user } from "$lib/stores/auth";
  import { fetchServices, activeServices } from "$lib/stores/services";
  import { fetchProducts, availableProducts } from "$lib/stores/products";
  import { fetchAllPackages, packagesAdminStore } from "$lib/stores/packages-admin";
  import { drawMenuFrame, KIDYLAND_COLORS, type ServiceItem, type ProductItem, type PackageItem } from "$lib/utils/video-canvas";
  import { exportToPDFHighQuality, exportToMP4 } from "$lib/utils/video-export";
  import { Button } from "@kidyland/ui";
  import { createEventDispatcher } from "svelte";
  import ItemSelector from "./ItemSelector.svelte";
  import { 
    List, 
    Play, 
    Pause, 
    Video, 
    FileText, 
    Download 
  } from "lucide-svelte";

  export let width: number = 1920;  // 1080p width
  export let height: number = 1080; // 1080p height
  export let fps: number = 25;      // 25 FPS
  export let duration: number = 15; // 15 seconds

  const dispatch = createEventDispatcher();

  let canvas: HTMLCanvasElement;
  let ctx: CanvasRenderingContext2D | null = null;
  let animationFrameId: number | null = null;
  let frame = 0;
  let isRecording = false;
  let isPlaying = false;
  let allServices: ServiceItem[] = [];
  let allProducts: ProductItem[] = [];
  let allPackages: PackageItem[] = [];
  let selectedServiceIds: string[] = [];
  let selectedProductIds: string[] = [];
  let selectedPackageIds: string[] = [];
  let showItemSelector = false;
  let isExportingPDF = false;
  let isExportingMP4 = false;
  let mp4Progress = 0;
  let lastRecordedWebMBlob: Blob | null = null;
  let error: string | null = null;

  // Computed: filtered items based on selection
  // Filter items based on selected IDs, or show all if nothing is selected yet (during initialization)
  $: services = selectedServiceIds.length === 0 && allServices.length > 0
    ? allServices // Show all during initialization
    : allServices.filter((s) => selectedServiceIds.includes(s.id));
  
  $: products = selectedProductIds.length === 0 && allProducts.length > 0
    ? allProducts // Show all during initialization
    : allProducts.filter((p) => selectedProductIds.includes(p.id));
  
  $: packages = selectedPackageIds.length === 0 && allPackages.length > 0
    ? allPackages // Show all during initialization
    : allPackages.filter((p) => selectedPackageIds.includes(p.id));

  onMount(async () => {
    // Initialize canvas
    if (canvas) {
      canvas.width = width;
      canvas.height = height;
      ctx = canvas.getContext("2d");
      
      // Load data
      const currentUser = $user;
      if (currentUser?.sucursal_id) {
        try {
          await Promise.all([
            fetchServices(currentUser.sucursal_id),
            fetchProducts(currentUser.sucursal_id),
            fetchAllPackages(currentUser.sucursal_id),
          ]);
          
          allServices = $activeServices.map((s) => ({
            id: s.id,
            name: s.name,
            price_cents: s.duration_prices && Object.keys(s.duration_prices).length > 0
              ? Math.min(...Object.values(s.duration_prices))
              : 0,
            durations_allowed: s.durations_allowed,
            duration_prices: s.duration_prices, // Pass full duration_prices map for displaying all prices
          }));
          
          allProducts = $availableProducts.map((p) => ({
            id: p.id,
            name: p.name,
            price_cents: p.price_cents,
            stock_qty: p.stock_qty,
          }));
          
          // Map packages from store
          allPackages = $packagesAdminStore.list
            .filter((pkg) => pkg.active !== false) // Only active packages
            .map((pkg) => ({
              id: pkg.id,
              name: pkg.name,
              price_cents: pkg.price_cents,
              description: pkg.description || undefined,
            }));

          // Initialize with all items selected (only if not already set)
          // This prevents overriding user selection if ItemSelector was opened before
          if (selectedServiceIds.length === 0 && allServices.length > 0) {
            selectedServiceIds = allServices.map((s) => s.id);
          }
          if (selectedProductIds.length === 0 && allProducts.length > 0) {
            selectedProductIds = allProducts.map((p) => p.id);
          }
          if (selectedPackageIds.length === 0 && allPackages.length > 0) {
            selectedPackageIds = allPackages.map((p) => p.id);
          }
          
          // Start preview animation
          startPreview();
        } catch (e: any) {
          error = e.message || "Error loading data";
        }
      }
    }
  });

  onDestroy(() => {
    stopAnimation();
  });

  function startPreview() {
    if (!ctx || isPlaying) return;
    
    isPlaying = true;
    frame = 0;
    animate();
  }

  function stopPreview() {
    isPlaying = false;
    stopAnimation();
  }

  function animate() {
    if (!ctx || !isPlaying) return;
    
    // Draw frame
    drawMenuFrame(ctx, width, height, services, products, packages, KIDYLAND_COLORS, frame);
    
    frame++;
    
    // Loop animation (restart after duration)
    const maxFrames = fps * duration;
    if (frame >= maxFrames) {
      frame = 0; // Loop
    }
    
    // Continue animation
    animationFrameId = requestAnimationFrame(() => {
      setTimeout(() => animate(), 1000 / fps);
    });
  }

  function stopAnimation() {
    if (animationFrameId !== null) {
      cancelAnimationFrame(animationFrameId);
      animationFrameId = null;
    }
  }

  async function startRecording() {
    if (!canvas || isRecording) return;
    
    try {
      // Check MediaRecorder support
      if (!window.MediaRecorder) {
        throw new Error("MediaRecorder API no está soportado en este navegador");
      }
      
      // Get canvas stream
      const stream = canvas.captureStream(fps);
      
      // Create MediaRecorder
      const mimeType = MediaRecorder.isTypeSupported("video/webm;codecs=vp9")
        ? "video/webm;codecs=vp9"
        : MediaRecorder.isTypeSupported("video/webm")
        ? "video/webm"
        : "video/webm"; // Fallback
      
      const recorder = new MediaRecorder(stream, {
        mimeType,
        videoBitsPerSecond: 2500000, // 2.5 Mbps quality
      });
      
      const chunks: Blob[] = [];
      
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunks.push(event.data);
        }
      };
      
      recorder.onstop = () => {
        const blob = new Blob(chunks, { type: mimeType });
        const url = URL.createObjectURL(blob);
        
        // Save blob for MP4 conversion
        lastRecordedWebMBlob = blob;
        
        // Trigger download
        const link = document.createElement("a");
        link.href = url;
        link.download = `kidyland_menu_${new Date().toISOString().split("T")[0]}.webm`;
        link.style.display = "none";
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        // Cleanup
        setTimeout(() => URL.revokeObjectURL(url), 100);
        
        dispatch("exported", { url, blob });
        isRecording = false;
      };
      
      recorder.onerror = (event) => {
        error = "Error durante la grabación del video";
        isRecording = false;
        dispatch("error", { error });
      };
      
      // Start recording
      isRecording = true;
      recorder.start();
      dispatch("recording-started");
      
      // Stop after duration
      setTimeout(() => {
        if (recorder.state === "recording") {
          recorder.stop();
          stream.getTracks().forEach((track) => track.stop());
        }
      }, duration * 1000);
      
    } catch (e: any) {
      error = e.message || "Error al iniciar grabación";
      isRecording = false;
      dispatch("error", { error });
    }
  }

  function stopRecording() {
    // Recording stops automatically after duration
    // This is just for UI feedback
    isRecording = false;
  }

  function handleItemSelectionChange(event: CustomEvent<{ services: string[]; products: string[]; packages: string[] }>) {
    const { services: newServices, products: newProducts, packages: newPackages } = event.detail;
    
    // Update selections
    selectedServiceIds = newServices;
    selectedProductIds = newProducts;
    selectedPackageIds = newPackages;
    
    // Restart preview with new selection if playing
    if (isPlaying) {
      stopPreview();
      // Small delay to ensure state is updated
      setTimeout(() => {
        startPreview();
      }, 100);
    } else if (ctx) {
      // If not playing, at least update the canvas to show current state
      drawMenuFrame(ctx, width, height, services, products, packages, KIDYLAND_COLORS, 0);
    }
  }

  async function handleExportPDF() {
    if (!canvas || isExportingPDF) return;

    try {
      isExportingPDF = true;
      error = null;

      // Ensure canvas is up to date by drawing current frame
      if (ctx) {
        drawMenuFrame(ctx, width, height, services, products, packages, KIDYLAND_COLORS, frame);
      }

      await exportToPDFHighQuality(canvas);
      dispatch("exported-pdf", { success: true });
    } catch (e: any) {
      error = e.message || "Error al exportar PDF";
      dispatch("error", { error });
    } finally {
      isExportingPDF = false;
    }
  }

  async function handleExportMP4() {
    if (!lastRecordedWebMBlob || isExportingMP4) {
      error = "Por favor, primero graba un video (WebM) antes de convertir a MP4";
      return;
    }

    try {
      isExportingMP4 = true;
      mp4Progress = 0;
      error = null;

      await exportToMP4(
        lastRecordedWebMBlob,
        `kidyland_menu_${new Date().toISOString().split("T")[0]}`,
        (progress) => {
          mp4Progress = progress;
        },
        {
          fps: fps, // Pass the fps parameter to ensure correct frame rate in output
        }
      );

      dispatch("exported-mp4", { success: true });
    } catch (e: any) {
      error = e.message || "Error al exportar MP4";
      dispatch("error", { error });
    } finally {
      isExportingMP4 = false;
      mp4Progress = 0;
    }
  }
</script>

<div class="video-generator-container">
  <div class="header-actions">
    <Button
      variant="brutalist"
      size="small"
      on:click={() => showItemSelector = !showItemSelector}
    >
      {#if showItemSelector}
        <List size={18} strokeWidth={1.5} style="display: inline-block; vertical-align: middle; margin-right: 6px;" />
        Cerrar Selector
      {:else}
        <List size={18} strokeWidth={1.5} style="display: inline-block; vertical-align: middle; margin-right: 6px;" />
        Seleccionar Items
      {/if}
    </Button>
  </div>

  {#if showItemSelector}
    <div class="selector-container">
      <ItemSelector
        bind:selectedServices={selectedServiceIds}
        bind:selectedProducts={selectedProductIds}
        bind:selectedPackages={selectedPackageIds}
        on:change={handleItemSelectionChange}
      />
    </div>
  {/if}

  <div class="canvas-container">
    <canvas
      bind:this={canvas}
      class="menu-canvas"
    ></canvas>
  </div>

  {#if error}
    <div class="error-banner" role="alert">
      {error}
    </div>
  {/if}

  <div class="controls">
    <div class="info">
      <p class="info-text">
        {#if isRecording}
          ⏺️ Grabando... ({duration}s)
        {:else if isPlaying}
          ▶️ Vista previa
        {:else}
          ⏸️ Pausado
        {/if}
      </p>
      <p class="info-details">
        Resolución: {width}x{height} | FPS: {fps} | Duración: {duration}s
      </p>
    </div>

    <div class="actions">
      {#if !isPlaying}
        <Button variant="brutalist" size="small" on:click={startPreview}>
          <Play size={18} strokeWidth={1.5} style="display: inline-block; vertical-align: middle; margin-right: 6px;" />
          Vista Previa
        </Button>
      {:else}
        <Button variant="brutalist" size="small" on:click={stopPreview}>
          <Pause size={18} strokeWidth={1.5} style="display: inline-block; vertical-align: middle; margin-right: 6px;" />
          Detener
        </Button>
      {/if}

      <Button
        variant="brutalist"
        size="small"
        on:click={startRecording}
        disabled={isRecording || !isPlaying}
      >
        {#if isRecording}
          <Video size={18} strokeWidth={1.5} style="display: inline-block; vertical-align: middle; margin-right: 6px;" />
          Grabando...
        {:else}
          <Video size={18} strokeWidth={1.5} style="display: inline-block; vertical-align: middle; margin-right: 6px;" />
          Exportar Video (WebM)
        {/if}
      </Button>

      <Button
        variant="brutalist"
        size="small"
        on:click={handleExportPDF}
        disabled={isExportingPDF || !canvas}
      >
        {#if isExportingPDF}
          <FileText size={18} strokeWidth={1.5} style="display: inline-block; vertical-align: middle; margin-right: 6px;" />
          Exportando PDF...
        {:else}
          <FileText size={18} strokeWidth={1.5} style="display: inline-block; vertical-align: middle; margin-right: 6px;" />
          Exportar PDF
        {/if}
      </Button>

      <Button
        variant="brutalist"
        size="small"
        on:click={handleExportMP4}
        disabled={isExportingMP4 || !lastRecordedWebMBlob}
      >
        {#if isExportingMP4}
          <Download size={18} strokeWidth={1.5} style="display: inline-block; vertical-align: middle; margin-right: 6px;" />
          Convirtiendo a MP4... {mp4Progress}%
        {:else}
          <Download size={18} strokeWidth={1.5} style="display: inline-block; vertical-align: middle; margin-right: 6px;" />
          Exportar MP4
        {/if}
      </Button>
    </div>
  </div>
</div>

<style>
  .video-generator-container {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-lg);
    padding: var(--spacing-lg);
    background: var(--theme-bg-elevated);
    border-radius: var(--radius-lg);
    border: 1px solid var(--border-primary);
  }

  .header-actions {
    display: flex;
    justify-content: flex-end;
    margin-bottom: var(--spacing-md);
  }

  .header-actions :global(button) {
    min-height: 44px;
  }

  .selector-container {
    margin-bottom: var(--spacing-md);
  }

  .canvas-container {
    display: flex;
    justify-content: center;
    align-items: center;
    background: var(--theme-bg-secondary);
    border-radius: var(--radius-md);
    padding: var(--spacing-md);
    overflow: hidden;
  }

  .menu-canvas {
    max-width: 100%;
    height: auto;
    border-radius: var(--radius-sm);
    box-shadow: var(--shadow-lg);
  }

  .error-banner {
    padding: var(--spacing-md);
    background: rgba(211, 5, 84, 0.1);
    border: 1px solid var(--accent-danger);
    border-radius: var(--radius-md);
    color: var(--accent-danger);
    text-align: center;
  }

  .controls {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: var(--spacing-md);
  }

  .info {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xs);
  }

  .info-text {
    font-weight: 600;
    color: var(--text-primary);
    margin: 0;
  }

  .info-details {
    font-size: var(--text-sm);
    color: var(--text-secondary);
    margin: 0;
  }

  .actions {
    display: flex;
    gap: var(--spacing-sm);
    flex-wrap: wrap;
  }

  /* Tablet */
  @media (min-width: 769px) and (max-width: 1024px) {
    .video-generator-container {
      padding: var(--spacing-lg);
    }

    .controls {
      flex-wrap: wrap;
    }

    .actions {
      flex: 1;
      justify-content: flex-end;
    }

    .actions :global(button) {
      min-width: 150px;
    }
  }

  /* Mobile */
  @media (max-width: 768px) {
    .video-generator-container {
      padding: var(--spacing-md);
      gap: var(--spacing-md);
    }

    .header-actions {
      width: 100%;
      justify-content: stretch;
    }

    .header-actions :global(button) {
      width: 100%;
      min-height: 44px; /* Minimum touch target size for accessibility */
      justify-content: center;
    }

    .selector-container {
      margin-bottom: var(--spacing-sm);
    }

    .canvas-container {
      padding: var(--spacing-sm);
    }

    .menu-canvas {
      width: 100%;
      height: auto;
    }

    .controls {
      flex-direction: column;
      align-items: stretch;
      gap: var(--spacing-md);
    }

    .info {
      text-align: center;
    }

    .info-text {
      font-size: var(--text-base);
    }

    .info-details {
      font-size: var(--text-xs);
    }

    .actions {
      width: 100%;
      flex-direction: column;
      gap: var(--spacing-sm);
    }

    .actions :global(button) {
      width: 100%;
      min-height: 44px; /* Minimum touch target size for accessibility */
      justify-content: center;
    }

    .error-banner {
      font-size: var(--text-sm);
      padding: var(--spacing-sm) var(--spacing-md);
    }
  }

  /* Prevent hover transform issues on touch devices */
  @media (hover: none) and (pointer: coarse) {
    .header-actions :global(button:hover),
    .actions :global(button:hover) {
      transform: none;
    }
  }
</style>










