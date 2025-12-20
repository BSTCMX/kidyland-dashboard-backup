<script lang="ts">
  /**
   * MenuWizard component - Main wizard for creating menu videos/PDFs.
   * 
   * Implements multi-step flow:
   * Step 1: Export Type Selection
   * Step 2: Background Image Selection
   * Step 3: Layout Style Selection
   * Step 4: Sucursal Selection
   * Step 5: Items Selection & Arrangement
   * Step 6: Preview & Export
   */
  import { onMount } from "svelte";
  import { user } from "$lib/stores/auth";
  import { fetchServices, activeServices } from "$lib/stores/services";
  import { fetchProducts, availableProducts } from "$lib/stores/products";
  import { fetchAllPackages, packagesAdminStore } from "$lib/stores/packages-admin";
  import { fetchAllSucursales, sucursalesAdminStore } from "$lib/stores/sucursales-admin";
  import { backgroundImagesStore, selectedBackgroundImage } from "$lib/stores/background-images";
  import { layoutsStore, selectedLayoutStyle, menuConfig } from "$lib/stores/layouts";
  import { groupItems, type GroupingMode } from "$lib/utils/package-grouping";
  import { calculateMenuPages, drawMenuFrame, KIDYLAND_COLORS } from "$lib/utils/video-canvas";
  import type { ServiceItem, ProductItem, PackageItem } from "$lib/utils/video-canvas";
  import { getItemsForPageProportional } from "$lib/utils/canvas-layout";
  import type { DrawPageFunction } from "$lib/utils/video-export";
  import { exportToPDFHighQuality, exportToPDFMultiPage, exportToMP4 } from "$lib/utils/video-export";
  import WizardStep from "./WizardStep.svelte";
  import BackgroundImageSelector from "./BackgroundImageSelector.svelte";
  import LayoutStyleSelector from "./LayoutStyleSelector.svelte";
  import SucursalSelector from "../admin/SucursalSelector.svelte";
  import ItemsArrangement from "./ItemsArrangement.svelte";
  import MenuPreview from "./MenuPreview.svelte";
  import LayoutEditor from "./LayoutEditor.svelte";
  import { Button } from "@kidyland/ui";
  import { Video, FileText, Download } from "lucide-svelte";
  import { createEventDispatcher } from "svelte";

  const dispatch = createEventDispatcher();

  export let width: number = 1920;
  export let height: number = 1080;
  export let fps: number = 25;

  type ExportType = "video" | "pdf";
  type WizardStepType = "export-type" | "background-image" | "layout" | "sucursal" | "items" | "preview";

  let currentStep: WizardStepType = "export-type";
  let exportType: ExportType | null = null;
  let selectedSucursalId: string | null = null;
  let selectedServiceIds: string[] = [];
  let selectedProductIds: string[] = [];
  let selectedPackageIds: string[] = [];
  let groupingMode: GroupingMode = "all";
  
  // Grouped items based on grouping mode
  let groupedServices: ServiceItem[] = [];
  let groupedProducts: ProductItem[] = [];
  let groupedPackages: PackageItem[] = [];
  
  // Export state
  let isExportingPDF = false;
  let isExportingMP4 = false;
  let mp4Progress = 0;
  let error: string | null = null;
  
  // Loading state
  let isLoadingItems = false;
  let lastLoadedSucursalId: string | null = null;
  
  // Video recording state (for MP4 export)
  let lastRecordedWebMBlob: Blob | null = null;
  let previewComponent: any = null;
  let isRecording = false;
  const PAGE_DURATION = 5; // seconds per page
  let recordingDuration = 15; // seconds (calculated based on pages)
  let recorder: MediaRecorder | null = null;
  let canvasStream: MediaStream | null = null;
  
  // Calculate total pages and recording duration
  let totalPagesForExport = 1;
  $: if (width && height && ($selectedBackgroundImage || $selectedLayoutStyle)) {
    const hasBackground = $selectedBackgroundImage !== null;
    totalPagesForExport = calculateMenuPages(
      width,
      height,
      groupedServices,
      groupedProducts,
      groupedPackages,
      hasBackground
    );
    // Record one full cycle per page: totalPages × PAGE_DURATION + 1 second buffer
    recordingDuration = Math.max(15, (totalPagesForExport * PAGE_DURATION) + 1);
  }

  // Get canvas from preview component
  let canvas: HTMLCanvasElement | null = null;
  
  function updateCanvas() {
    if (previewComponent) {
      const previewCanvas = previewComponent.getCanvas();
      if (previewCanvas) {
        canvas = previewCanvas;
      }
    }
  }
  
  // Update canvas when preview component changes
  $: if (previewComponent) {
    updateCanvas();
  }

  async function startRecording() {
    if (!canvas || isRecording || !$selectedBackgroundImage || !$selectedLayoutStyle) {
      return;
    }

    try {
      // Check MediaRecorder support
      if (!window.MediaRecorder) {
        throw new Error("MediaRecorder API no está soportado en este navegador");
      }

      // Ensure preview is playing
      if (previewComponent) {
        previewComponent.play();
      }

      // Get canvas stream
      canvasStream = canvas.captureStream(fps);

      // Create MediaRecorder
      const mimeType = MediaRecorder.isTypeSupported("video/webm;codecs=vp9")
        ? "video/webm;codecs=vp9"
        : MediaRecorder.isTypeSupported("video/webm")
        ? "video/webm"
        : "video/webm";

      recorder = new MediaRecorder(canvasStream, {
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
        lastRecordedWebMBlob = blob;
        isRecording = false;

        // Stop canvas stream
        if (canvasStream) {
          canvasStream.getTracks().forEach((track) => track.stop());
          canvasStream = null;
        }

        // Auto-convert to MP4 if export type is video
        if (exportType === "video") {
          handleExportMP4();
        }
      };

      recorder.onerror = () => {
        error = "Error durante la grabación del video";
        isRecording = false;
        if (canvasStream) {
          canvasStream.getTracks().forEach((track) => track.stop());
          canvasStream = null;
        }
      };

      // Start recording
      isRecording = true;
      recorder.start();

      // Stop after duration
      setTimeout(() => {
        if (recorder && recorder.state === "recording") {
          recorder.stop();
        }
      }, recordingDuration * 1000);
    } catch (e: any) {
      error = e.message || "Error al iniciar grabación";
      isRecording = false;
    }
  }

  const steps: Array<{ id: WizardStepType; title: string; description?: string }> = [
    { id: "export-type", title: "Tipo de Exportación", description: "Selecciona el formato de salida" },
    { id: "background-image", title: "Seleccionar Imagen de Fondo", description: "Elige la imagen de fondo para tu menú" },
    { id: "layout", title: "Seleccionar Distribución", description: "Elige cómo se organizarán los items" },
    { id: "sucursal", title: "Seleccionar Sucursal", description: "Elije la sucursal para los items" },
    { id: "items", title: "Seleccionar Items", description: "Elige servicios, productos y paquetes" },
    { id: "preview", title: "Vista Previa y Exportar", description: "Revisa y exporta tu menú" },
  ];

  // Reactive: Update index and data when currentStep changes
  $: currentStepIndex = steps.findIndex((s) => s.id === currentStep);
  $: currentStepData = currentStepIndex >= 0 ? steps[currentStepIndex] : steps[0];

  onMount(async () => {
    // Load background images and layouts
    await Promise.all([
      backgroundImagesStore.loadImages(),
      layoutsStore.loadLayouts(),
    ]);
    
    // Initialize sucursal to current user's sucursal
    const currentUser = $user;
    if (currentUser?.sucursal_id) {
      selectedSucursalId = currentUser.sucursal_id;
      lastLoadedSucursalId = currentUser.sucursal_id;
      await loadSucursalItems(currentUser.sucursal_id);
    }
  });

  async function loadSucursalItems(sucursalId: string) {
    if (isLoadingItems) return; // Prevent concurrent loads
    
    isLoadingItems = true;
    try {
      await Promise.all([
        fetchServices(sucursalId),
        fetchProducts(sucursalId),
        fetchAllPackages(sucursalId),
      ]);
      
      // Map to ServiceItem/ProductItem/PackageItem format
      const services: ServiceItem[] = $activeServices.map((s) => ({
        id: s.id,
        name: s.name,
        price_cents: s.duration_prices && Object.keys(s.duration_prices).length > 0
          ? Math.min(...Object.values(s.duration_prices).map((v) => typeof v === 'number' ? v : 0))
          : 0,
        durations_allowed: s.durations_allowed,
        duration_prices: s.duration_prices, // Pass full duration_prices map for displaying all prices
      }));
      
      const products: ProductItem[] = $availableProducts.map((p) => ({
        id: p.id,
        name: p.name,
        price_cents: p.price_cents,
        stock_qty: p.stock_qty,
      }));
      
      const packages: PackageItem[] = $packagesAdminStore.list
        .filter((p) => p.active !== false)
        .map((p) => ({
          id: p.id,
          name: p.name,
          price_cents: p.price_cents,
          description: p.description || undefined,
        }));

      // Apply grouping
      applyGrouping(services, products, packages);
    } catch (e: any) {
      error = e.message || "Error al cargar items";
      console.error("Error loading items:", e);
    } finally {
      isLoadingItems = false;
    }
  }

  function applyGrouping(
    services: ServiceItem[],
    products: ProductItem[],
    allPackages: PackageItem[]
  ) {
    // Get actual Package objects from store for grouping logic
    const packagesFromStore = $packagesAdminStore.list.filter((p) => p.active !== false);
    
    const selectedServices = services.filter((s) => selectedServiceIds.includes(s.id));
    const selectedProducts = products.filter((p) => selectedProductIds.includes(p.id));
    
    const grouped = groupItems(selectedServices, selectedProducts, packagesFromStore, groupingMode);
    
    groupedServices = grouped.services;
    groupedProducts = grouped.products;
    groupedPackages = grouped.packages;
  }

  // Reactive: Apply grouping when selection or mode changes
  $: if (selectedSucursalId && (selectedServiceIds.length > 0 || selectedProductIds.length > 0)) {
    const services: ServiceItem[] = $activeServices
      .filter((s) => selectedServiceIds.includes(s.id))
      .map((s) => ({
        id: s.id,
        name: s.name,
        price_cents: s.duration_prices && Object.keys(s.duration_prices).length > 0
          ? Math.min(...Object.values(s.duration_prices).map((v) => typeof v === 'number' ? v : 0))
          : 0,
        durations_allowed: s.durations_allowed,
        duration_prices: s.duration_prices, // Pass full duration_prices map for displaying all prices
      }));
    
    const products: ProductItem[] = $availableProducts
      .filter((p) => selectedProductIds.includes(p.id))
      .map((p) => ({
        id: p.id,
        name: p.name,
        price_cents: p.price_cents,
        stock_qty: p.stock_qty,
      }));
    
    const allPackages: PackageItem[] = $packagesAdminStore.list
      .filter((p) => p.active !== false)
      .map((p) => ({
        id: p.id,
        name: p.name,
        price_cents: p.price_cents,
        description: p.description || undefined,
      }));
    
    applyGrouping(services, products, allPackages);
  }

  function handleNext() {
    const nextIndex = currentStepIndex + 1;
    if (nextIndex < steps.length) {
      currentStep = steps[nextIndex].id;
    }
  }

  function handleBack() {
    const prevIndex = currentStepIndex - 1;
    if (prevIndex >= 0) {
      currentStep = steps[prevIndex].id;
    }
  }

  // Reactive: Compute canGoNext based on current step and required data
  $: canGoNext = (() => {
    switch (currentStep) {
      case "export-type":
        return exportType !== null;
      case "background-image":
        return $selectedBackgroundImage !== null;
      case "layout":
        return $selectedLayoutStyle !== null;
      case "sucursal":
        return selectedSucursalId !== null;
      case "items":
        return selectedServiceIds.length > 0 || selectedProductIds.length > 0 || selectedPackageIds.length > 0;
      case "preview":
        return false; // Can't go forward from preview
      default:
        return false;
    }
  })();

  // Handle background image selection
  function handleBackgroundImageSelect(event: CustomEvent<{ imageId: string }>) {
    const { imageId } = event.detail;
    backgroundImagesStore.selectImage(imageId);
    // $selectedBackgroundImage will be updated reactively via store
  }

  // Handle layout style selection
  function handleLayoutStyleSelect(event: CustomEvent<{ layoutId: string }>) {
    const { layoutId } = event.detail;
    layoutsStore.selectLayout(layoutId);
    // $selectedLayoutStyle will be updated reactively via store
  }

  // Reactive: Load items when sucursal changes via bind:
  // Only load if sucursal changed and not currently loading
  $: if (selectedSucursalId && selectedSucursalId !== lastLoadedSucursalId && !isLoadingItems) {
    lastLoadedSucursalId = selectedSucursalId;
    loadSucursalItems(selectedSucursalId); // selectedSucursalId is guaranteed non-null here
  }

  function handleItemsChange(event: CustomEvent) {
    selectedServiceIds = event.detail.services || [];
    selectedProductIds = event.detail.products || [];
    selectedPackageIds = event.detail.packages || [];
    if (event.detail.groupingMode) {
      groupingMode = event.detail.groupingMode;
    }
  }

  /**
   * Ensure background image is loaded and ready for rendering.
   * 
   * @param imagePath - Path to the background image
   * @returns Promise that resolves to HTMLImageElement or null if no image or error
   */
  async function ensureBackgroundImageLoaded(
    imagePath: string | null | undefined
  ): Promise<HTMLImageElement | null> {
    if (!imagePath) {
      return null;
    }

    return new Promise((resolve) => {
      const img = new Image();
      img.crossOrigin = "anonymous"; // Enable CORS if needed

      img.onload = () => {
        resolve(img);
      };

      img.onerror = () => {
        // Return null on error (will use fallback solid color)
        if (import.meta.env?.DEV) {
          console.warn("Error loading background image for PDF export:", imagePath);
        }
        resolve(null);
      };

      img.src = imagePath;
    });
  }

  /**
   * Create a draw page function for multi-page PDF export.
   * 
   * This factory function captures the component's context and returns
   * a function that can render any page on the canvas.
   * 
   * @returns DrawPageFunction that renders a specific page
   */
  function createDrawPageFunction(): DrawPageFunction {
    // Capture current context from component scope
    const services = groupedServices;
    const products = groupedProducts;
    const packages = groupedPackages;
    const backgroundImage = $selectedBackgroundImage;
    const layoutStyle = $selectedLayoutStyle;
    const canvasWidth = width;
    const canvasHeight = height;

    // Pre-load background image once (will be reused for all pages)
    let backgroundImageElementPromise: Promise<HTMLImageElement | null> | null = null;

    return async (canvas: HTMLCanvasElement, pageIndex: number, totalPages: number) => {
      // Get canvas context
      const ctx = canvas.getContext("2d");
      if (!ctx) {
        throw new Error("Failed to get canvas context");
      }

      // Ensure background image is loaded (only load once, reuse for all pages)
      if (!backgroundImageElementPromise) {
        backgroundImageElementPromise = ensureBackgroundImageLoaded(
          backgroundImage?.imagePath || null
        );
      }
      const backgroundImageElement = await backgroundImageElementPromise;
      const hasBackgroundImage = backgroundImageElement !== null;

      // Get colors from layout or use default
      const colors = layoutStyle?.branding?.colors || KIDYLAND_COLORS;

      // Get items for this page using proportional division
      const pageServices = getItemsForPageProportional(services, pageIndex, totalPages);
      const pageProducts = getItemsForPageProportional(products, pageIndex, totalPages);
      const pagePackages = getItemsForPageProportional(packages, pageIndex, totalPages);

      // CRITICAL: Always clear canvas completely before drawing each page
      // This ensures each page starts fresh, preventing content from previous pages
      // from appearing in subsequent pages (which was causing only first page to export)
      ctx.clearRect(0, 0, canvasWidth, canvasHeight);

      // Draw background: either image or solid color
      if (hasBackgroundImage && backgroundImageElement) {
        try {
          // Draw background image covering entire canvas
          ctx.drawImage(backgroundImageElement, 0, 0, canvasWidth, canvasHeight);
        } catch (error) {
          // Fallback to solid color if image fails to draw
          if (import.meta.env?.DEV) {
            console.warn("Error drawing background image in PDF export:", error);
          }
          ctx.fillStyle = colors.background;
          ctx.fillRect(0, 0, canvasWidth, canvasHeight);
        }
      } else {
        // No background image: use solid color
        ctx.fillStyle = colors.background;
        ctx.fillRect(0, 0, canvasWidth, canvasHeight);
      }

      // Determine if this is the last page (for footer)
      const showFooter = pageIndex === totalPages - 1;

      // Draw menu frame for this page
      // Note: frame parameter is 0 for static PDF export (no animation)
      // IMPORTANT: hasBackgroundImage flag tells drawMenuFrame that canvas already has background
      // (we cleared and drew it above), so it should NOT clear/fill the canvas again
      await drawMenuFrame(
        ctx,
        canvasWidth,
        canvasHeight,
        pageServices,
        pageProducts,
        pagePackages,
        colors,
        0, // frame = 0 for static PDF export (no animation)
        hasBackgroundImage, // true = background already drawn, don't clear/fill canvas
        pageIndex,
        totalPages,
        showFooter
      );
    };
  }

  async function handleExportPDF() {
    if (!canvas || !$selectedBackgroundImage || !$selectedLayoutStyle) {
      error = "No hay canvas, imagen de fondo o layout seleccionado";
      return;
    }

    // Protection: Don't export PDF while recording video
    if (isRecording) {
      error = "No se puede exportar PDF mientras se está grabando video. Por favor, espera a que termine la grabación.";
      return;
    }

    try {
      isExportingPDF = true;
      error = null;

      // Save current preview state to restore later
      // Use getIsPlaying() method instead of direct property access
      // This follows Svelte best practices for component instance access
      const wasPlaying = previewComponent?.getIsPlaying() || false;

      // Pause preview animation during export to prevent conflicts
      if (previewComponent) {
        previewComponent.pause();
        // Small delay to ensure pause is processed
        await new Promise((resolve) => setTimeout(resolve, 100));
      }

      // CRITICAL: Recalculate totalPages directly to ensure we have the correct value
      // Reactive statements ($:) may not have executed before this async function,
      // so we recalculate to guarantee accuracy at export time
      const hasBackground = $selectedBackgroundImage !== null;
      const calculatedTotalPages = calculateMenuPages(
        width,
        height,
        groupedServices,
        groupedProducts,
        groupedPackages,
        hasBackground
      );

      // Logging for debugging (dev only)
      if (import.meta.env?.DEV) {
        console.log(
          `[PDF Export] Pages calculation: reactive=${totalPagesForExport}, calculated=${calculatedTotalPages}`
        );
        if (totalPagesForExport !== calculatedTotalPages) {
          console.warn(
            `[PDF Export] Warning: Reactive value (${totalPagesForExport}) differs from calculated value (${calculatedTotalPages}). Using calculated value.`
          );
        }
      }

      // Use calculated value (more reliable than reactive variable)
      const totalPagesToExport = calculatedTotalPages;

      // Use multi-page export if more than 1 page, otherwise use single-page export
      if (totalPagesToExport > 1) {
        // Create draw page function with current context
        const drawPageFunction = createDrawPageFunction();

        // Export multi-page PDF
        await exportToPDFMultiPage(
          canvas,
          drawPageFunction,
          totalPagesToExport,
          `kidyland_menu_${new Date().toISOString().split("T")[0]}`
        );
      } else {
        // Use existing single-page export for better performance when only 1 page
        await exportToPDFHighQuality(
          canvas,
          `kidyland_menu_${new Date().toISOString().split("T")[0]}`
        );
      }

      // Restore preview state after export
      if (previewComponent && wasPlaying) {
        // Small delay before resuming
        await new Promise((resolve) => setTimeout(resolve, 100));
        previewComponent.play();
      } else if (previewComponent) {
        // If was paused, at least redraw current frame
        previewComponent.pause();
      }

      dispatch("exported", { type: "pdf", success: true });
    } catch (e: any) {
      error = e.message || "Error al exportar PDF";
      // Ensure error is always a string for proper logging
      const errorMessage = typeof error === "string" ? error : String(error);
      dispatch("error", { error: errorMessage });

      // Try to restore preview state even on error
      if (previewComponent) {
        previewComponent.pause();
      }
    } finally {
      isExportingPDF = false;
    }
  }

  async function handleExportMP4() {
    if (!lastRecordedWebMBlob) {
      error = "Primero debes grabar el video";
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

      dispatch("exported", { type: "mp4", success: true });
      // Reset after successful export
      lastRecordedWebMBlob = null;
    } catch (e: any) {
      error = e.message || "Error al exportar MP4";
      // Ensure error is always a string for proper logging
      const errorMessage = typeof error === "string" ? error : String(error);
      dispatch("error", { error: errorMessage });
    } finally {
      isExportingMP4 = false;
      mp4Progress = 0;
    }
  }

  function handleExportTypeSelect(type: ExportType) {
    exportType = type;
  }
</script>

<div class="menu-wizard">
  {#if currentStep === "export-type"}
    <WizardStep
      stepNumber={currentStepIndex + 1}
      totalSteps={steps.length}
      title={currentStepData.title}
      description={currentStepData.description}
      canGoNext={canGoNext}
      canGoBack={false}
      on:next={handleNext}
      on:back={handleBack}
    >
      <div class="export-type-selection">
        <button
          type="button"
          class="export-type-button"
          class:selected={exportType === "video"}
          on:click={() => handleExportTypeSelect("video")}
        >
          <Video size={48} strokeWidth={1.5} />
          <h3>Crear Video</h3>
          <p>Exporta tu menú como video MP4 animado</p>
        </button>
        
        <button
          type="button"
          class="export-type-button"
          class:selected={exportType === "pdf"}
          on:click={() => handleExportTypeSelect("pdf")}
        >
          <FileText size={48} strokeWidth={1.5} />
          <h3>Crear PDF</h3>
          <p>Exporta tu menú como documento PDF</p>
        </button>
      </div>
    </WizardStep>

  {:else if currentStep === "background-image"}
    <WizardStep
      stepNumber={currentStepIndex + 1}
      totalSteps={steps.length}
      title={currentStepData.title}
      description={currentStepData.description}
      canGoNext={canGoNext}
      on:next={handleNext}
      on:back={handleBack}
    >
      <BackgroundImageSelector on:select={handleBackgroundImageSelect} />
    </WizardStep>

  {:else if currentStep === "layout"}
    <WizardStep
      stepNumber={currentStepIndex + 1}
      totalSteps={steps.length}
      title={currentStepData.title}
      description={currentStepData.description}
      canGoNext={canGoNext}
      on:next={handleNext}
      on:back={handleBack}
    >
      <LayoutStyleSelector on:select={handleLayoutStyleSelect} />
    </WizardStep>

  {:else if currentStep === "sucursal"}
    <WizardStep
      stepNumber={currentStepIndex + 1}
      totalSteps={steps.length}
      title={currentStepData.title}
      description={currentStepData.description}
      canGoNext={canGoNext}
      on:next={handleNext}
      on:back={handleBack}
    >
      <div class="sucursal-selection">
        <SucursalSelector
          bind:selectedSucursalId
        />
      </div>
    </WizardStep>

  {:else if currentStep === "items"}
    <WizardStep
      stepNumber={currentStepIndex + 1}
      totalSteps={steps.length}
      title={currentStepData.title}
      description={currentStepData.description}
      canGoNext={canGoNext}
      on:next={handleNext}
      on:back={handleBack}
    >
      <ItemsArrangement
        sucursalId={selectedSucursalId}
        bind:selectedServices={selectedServiceIds}
        bind:selectedProducts={selectedProductIds}
        bind:selectedPackages={selectedPackageIds}
        on:change={handleItemsChange}
      />
    </WizardStep>

  {:else if currentStep === "preview"}
    <WizardStep
      stepNumber={currentStepIndex + 1}
      totalSteps={steps.length}
      title={currentStepData.title}
      description={currentStepData.description}
      canGoNext={false}
      showNavigation={false}
    >
      <div class="preview-export-section">
        <div class="preview-with-editor">
          <MenuPreview
            bind:this={previewComponent}
            backgroundImage={$selectedBackgroundImage}
            layoutStyle={$selectedLayoutStyle}
            services={groupedServices}
            products={groupedProducts}
            packages={groupedPackages}
            {width}
            {height}
            {fps}
            autoPlay={true}
          />
          
          <LayoutEditor />
        </div>

        {#if error}
          <div class="error-banner" role="alert">
            {error}
          </div>
        {/if}

        <div class="export-actions">
          {#if exportType === "pdf"}
            <Button
              variant="brutalist"
              size="large"
              on:click={handleExportPDF}
              disabled={isExportingPDF || !$selectedBackgroundImage || !$selectedLayoutStyle || !canvas}
            >
              <Download size={20} strokeWidth={1.5} />
              {isExportingPDF ? "Exportando PDF..." : "Exportar PDF"}
            </Button>
          {:else if exportType === "video"}
            {#if !lastRecordedWebMBlob && !isRecording}
              <Button
                variant="brutalist"
                size="large"
                on:click={startRecording}
                disabled={!canvas || !$selectedBackgroundImage || !$selectedLayoutStyle || (groupedServices.length === 0 && groupedProducts.length === 0 && groupedPackages.length === 0)}
              >
                <Video size={20} strokeWidth={1.5} />
                Grabar Video ({recordingDuration}s)
              </Button>
            {:else if isRecording}
              <Button
                variant="brutalist"
                size="large"
                disabled={true}
              >
                <Video size={20} strokeWidth={1.5} />
                Grabando... ({recordingDuration}s)
              </Button>
            {:else}
              <Button
                variant="brutalist"
                size="large"
                on:click={handleExportMP4}
                disabled={isExportingMP4 || !lastRecordedWebMBlob}
              >
                <Download size={20} strokeWidth={1.5} />
                {isExportingMP4
                  ? `Convirtiendo MP4... ${Math.round(mp4Progress)}%`
                  : "Exportar MP4"}
              </Button>
            {/if}
          {/if}

          <Button
            variant="brutalist"
            size="large"
            on:click={() => (currentStep = "export-type")}
          >
            Crear Nuevo Menú
          </Button>
        </div>
      </div>
    </WizardStep>
  {/if}
</div>

<style>
  .menu-wizard {
    width: 100%;
  }

  .export-type-selection {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: var(--spacing-xl);
    padding: var(--spacing-lg) 0;
  }

  .export-type-button {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: var(--spacing-md);
    padding: var(--spacing-xl);
    border: 3px solid var(--border-primary);
    border-radius: var(--radius-lg);
    background: var(--theme-bg-primary);
    cursor: pointer;
    transition: all 0.2s;
    text-align: center;
    min-height: 250px;
  }

  .export-type-button:hover {
    border-color: var(--accent-primary);
    transform: translateY(-4px);
    box-shadow: 0 8px 16px rgba(0, 0, 0, 0.15);
  }

  .export-type-button.selected {
    border-color: var(--accent-primary);
    border-width: 4px;
    background: rgba(0, 147, 247, 0.1);
    box-shadow: 0 0 0 4px rgba(0, 147, 247, 0.2);
  }

  .export-type-button h3 {
    font-size: var(--text-2xl);
    font-weight: 700;
    color: var(--text-primary);
    margin: 0;
  }

  .export-type-button p {
    font-size: var(--text-base);
    color: var(--text-secondary);
    margin: 0;
  }

  .sucursal-selection {
    padding: var(--spacing-lg) 0;
  }

  .preview-export-section {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-lg);
  }

  .preview-with-editor {
    display: grid;
    grid-template-columns: 2fr 1fr;
    gap: var(--spacing-lg);
    align-items: start;
  }

  .error-banner {
    padding: var(--spacing-md);
    background: rgba(211, 5, 84, 0.1);
    border: 1px solid var(--accent-danger);
    border-radius: var(--radius-md);
    color: var(--accent-danger);
    text-align: center;
  }

  .export-actions {
    display: flex;
    gap: var(--spacing-md);
    justify-content: center;
    flex-wrap: wrap;
  }

  /* Responsive */
  @media (max-width: 768px) {
    .export-type-selection {
      grid-template-columns: 1fr;
      gap: var(--spacing-md);
    }

    .export-type-button {
      min-height: 200px;
      padding: var(--spacing-lg);
    }

    .export-actions {
      flex-direction: column;
    }

    .export-actions :global(button) {
      width: 100%;
    }

    .preview-with-editor {
      grid-template-columns: 1fr;
    }
  }

  /* Prevent hover transform on touch devices */
  @media (hover: none) and (pointer: coarse) {
    .export-type-button:hover {
      transform: none;
      box-shadow: 0 8px 16px rgba(0, 0, 0, 0.15);
    }
  }
</style>

