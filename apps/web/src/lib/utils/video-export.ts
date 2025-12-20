/**
 * Video export utilities - Export canvas to PDF and MP4 formats.
 * 
 * Provides functions to export canvas content to different formats.
 */

import jsPDF from "jspdf";
import type { FFmpeg } from "@ffmpeg/ffmpeg";
// Dynamic imports for FFmpeg utilities (browser-only, cannot be imported in SSR)
// These will be imported only when needed in loadFFmpeg()

/**
 * Export canvas to PDF.
 * 
 * @param canvas - HTMLCanvasElement to export
 * @param filename - Optional filename (without extension)
 * @param quality - Image quality (0-1, default: 0.95)
 * @returns Promise that resolves when PDF is downloaded
 */
export async function exportToPDF(
  canvas: HTMLCanvasElement,
  filename: string = `kidyland_menu_${new Date().toISOString().split("T")[0]}`,
  quality: number = 0.95
): Promise<void> {
  try {
    // Convert canvas to image data
    const canvasDataUrl = canvas.toDataURL("image/png", quality);
    
    // Create PDF with canvas dimensions (maintaining aspect ratio)
    const pdfWidth = canvas.width;
    const pdfHeight = canvas.height;
    
    // jsPDF works in points (1/72 inch), so we need to convert pixels
    // Standard PDF page sizes: A4 = 595x842 points (at 72 DPI)
    // We'll use a landscape orientation if width > height
    const isLandscape = pdfWidth > pdfHeight;
    const pdf = new jsPDF({
      orientation: isLandscape ? "landscape" : "portrait",
      unit: "pt",
      format: [pdfWidth, pdfHeight],
    });

    // Add image to PDF (full page)
    pdf.addImage(canvasDataUrl, "PNG", 0, 0, pdfWidth, pdfHeight, undefined, "FAST");

    // Save PDF
    pdf.save(`${filename}.pdf`);
  } catch (error: any) {
    throw new Error(`Error exporting to PDF: ${error.message}`);
  }
}

/**
 * Type for page rendering function used in multi-page PDF export.
 * 
 * This function should draw the specified page on the canvas.
 * The canvas will be captured after this function completes.
 * 
 * @param canvas - Canvas element to draw on
 * @param pageIndex - Zero-based page index to render (0 for first page)
 * @param totalPages - Total number of pages
 * @returns Promise that resolves when the page is fully rendered
 */
export type DrawPageFunction = (
  canvas: HTMLCanvasElement,
  pageIndex: number,
  totalPages: number
) => Promise<void>;

/**
 * Export canvas to PDF with high quality rendering.
 * 
 * Uses direct canvas.toDataURL() with requestAnimationFrame to ensure
 * the canvas is fully rendered before export.
 * 
 * @param canvas - HTMLCanvasElement to export
 * @param filename - Optional filename (without extension)
 * @param quality - Image quality (0-1, default: 0.95)
 * @returns Promise that resolves when PDF is downloaded
 */
export async function exportToPDFHighQuality(
  canvas: HTMLCanvasElement,
  filename: string = `kidyland_menu_${new Date().toISOString().split("T")[0]}`,
  quality: number = 0.95
): Promise<void> {
  try {
    // Wait for next frame to ensure canvas is fully rendered
    // This is critical for canvas that may be animating or updating
    await new Promise<void>((resolve) => {
      requestAnimationFrame(() => {
        requestAnimationFrame(() => {
          // Double RAF ensures we wait for the next paint cycle
          resolve();
        });
      });
    });

    // Convert canvas to image data directly (no cloning needed)
    // cloneNode() doesn't copy canvas content, so we use the original canvas
    const canvasDataUrl = canvas.toDataURL("image/png", quality);

    // Validate that we got valid image data (not empty/black)
    if (!canvasDataUrl || canvasDataUrl === "data:," || canvasDataUrl.length < 100) {
      throw new Error("Canvas appears to be empty or not fully rendered. Please wait a moment and try again.");
    }

    // Create PDF with canvas dimensions (maintaining aspect ratio)
    const pdfWidth = canvas.width;
    const pdfHeight = canvas.height;

    if (pdfWidth === 0 || pdfHeight === 0) {
      throw new Error("Canvas dimensions are invalid");
    }

    // jsPDF works in points (1/72 inch), so we use pixel dimensions directly
    // Standard PDF page sizes: A4 = 595x842 points (at 72 DPI)
    const isLandscape = pdfWidth > pdfHeight;
    const pdf = new jsPDF({
      orientation: isLandscape ? "landscape" : "portrait",
      unit: "pt",
      format: [pdfWidth, pdfHeight],
    });

    // Add image to PDF (full page)
    pdf.addImage(canvasDataUrl, "PNG", 0, 0, pdfWidth, pdfHeight, undefined, "FAST");

    // Save PDF
    pdf.save(`${filename}.pdf`);
  } catch (error: any) {
    throw new Error(`Error exporting to PDF: ${error.message}`);
  }
}

/**
 * Export multiple pages of canvas content to PDF.
 * 
 * This function iterates through pages, renders each page using the provided
 * drawPageFunction, captures the canvas state, and adds it to the PDF.
 * 
 * @param canvas - HTMLCanvasElement to export (will be modified during export)
 * @param drawPageFunction - Function that renders a specific page on the canvas
 * @param totalPages - Total number of pages to export (must be >= 1)
 * @param filename - Optional filename (without extension)
 * @param quality - Image quality (0-1, default: 0.95)
 * @param onProgress - Optional progress callback (0-100)
 * @returns Promise that resolves when PDF is downloaded
 */
export async function exportToPDFMultiPage(
  canvas: HTMLCanvasElement,
  drawPageFunction: DrawPageFunction,
  totalPages: number,
  filename: string = `kidyland_menu_${new Date().toISOString().split("T")[0]}`,
  quality: number = 0.95,
  onProgress?: (progress: number) => void
): Promise<void> {
  // Validate inputs
  if (!canvas) {
    throw new Error("Canvas is required for PDF export");
  }

  if (typeof totalPages !== "number" || totalPages < 1 || !Number.isInteger(totalPages)) {
    throw new Error(`Invalid totalPages: must be an integer >= 1, got ${totalPages}`);
  }

  if (typeof drawPageFunction !== "function") {
    throw new Error("drawPageFunction must be a function");
  }

  const pdfWidth = canvas.width;
  const pdfHeight = canvas.height;

  if (pdfWidth === 0 || pdfHeight === 0) {
    throw new Error("Canvas dimensions are invalid");
  }

  try {
    onProgress?.(0);

    // Validation: Log total pages for debugging (dev only)
    if (import.meta.env?.DEV) {
      console.log(`[PDF Export] Starting multi-page export: ${totalPages} page(s)`);
    }

    // Create PDF with canvas dimensions (maintaining aspect ratio)
    const isLandscape = pdfWidth > pdfHeight;
    const pdf = new jsPDF({
      orientation: isLandscape ? "landscape" : "portrait",
      unit: "pt",
      format: [pdfWidth, pdfHeight],
    });

    // Track data URLs to detect duplicate pages (debugging)
    const pageDataUrls: string[] = [];

    // Iterate through each page
    for (let pageIndex = 0; pageIndex < totalPages; pageIndex++) {
      // Update progress
      const pageProgress = Math.round((pageIndex / totalPages) * 90); // 0-90% for rendering
      onProgress?.(pageProgress);

      // Log page rendering start (dev only)
      if (import.meta.env?.DEV) {
        console.log(`[PDF Export] Rendering page ${pageIndex + 1} of ${totalPages}`);
      }

      // Render the page on canvas using provided function
      await drawPageFunction(canvas, pageIndex, totalPages);

      // Wait for next frame to ensure canvas is fully rendered
      // Double RAF ensures we wait for the next paint cycle
      await new Promise<void>((resolve) => {
        requestAnimationFrame(() => {
          requestAnimationFrame(() => {
            resolve();
          });
        });
      });

      // Capture canvas as image
      const canvasDataUrl = canvas.toDataURL("image/png", quality);

      // Validate that we got valid image data
      if (!canvasDataUrl || canvasDataUrl === "data:," || canvasDataUrl.length < 100) {
        throw new Error(
          `Page ${pageIndex + 1} appears to be empty or not fully rendered. ` +
          `Please ensure drawPageFunction properly renders the page.`
        );
      }

      // Debug: Check if this page is duplicate of previous (dev only)
      if (import.meta.env?.DEV && pageDataUrls.length > 0) {
        const isDuplicate = pageDataUrls.some((prevUrl) => prevUrl === canvasDataUrl);
        if (isDuplicate) {
          console.warn(
            `[PDF Export] Warning: Page ${pageIndex + 1} appears to be duplicate of previous page. ` +
            `Canvas may not be clearing properly between pages.`
          );
        }
      }
      pageDataUrls.push(canvasDataUrl);

      // Add new page (except for first page)
      if (pageIndex > 0) {
        pdf.addPage();
      }

      // Add image to PDF (full page)
      pdf.addImage(canvasDataUrl, "PNG", 0, 0, pdfWidth, pdfHeight, undefined, "FAST");

      // Small delay to ensure jsPDF processes the page addition
      // This helps prevent potential race conditions in jsPDF's internal state
      if (pageIndex < totalPages - 1) {
        // Only delay between pages, not after last page
        await new Promise<void>((resolve) => setTimeout(resolve, 50));
      }
    }

    // Final progress
    onProgress?.(95);

    // Validate PDF was created with correct number of pages
    const pdfPageCount = pdf.getNumberOfPages();
    if (import.meta.env?.DEV) {
      console.log(
        `[PDF Export] Export complete: ${pdfPageCount} page(s) in PDF (expected ${totalPages})`
      );
      if (pdfPageCount !== totalPages) {
        console.warn(
          `[PDF Export] Warning: PDF has ${pdfPageCount} pages but expected ${totalPages}`
        );
      }
    }

    // Save PDF
    pdf.save(`${filename}.pdf`);
    onProgress?.(100);
  } catch (error: any) {
    // Reset progress on error
    onProgress?.(0);
    throw new Error(`Error exporting multi-page PDF: ${error.message}`);
  }
}

/**
 * Parse FFmpeg time string (HH:MM:SS.mmm format) to seconds.
 * 
 * Examples:
 * - "00:00:14.92" -> 14.92
 * - "00:01:23.456" -> 83.456
 * - "01:30:00" -> 5400
 * 
 * @param timeString - Time string in HH:MM:SS.mmm format
 * @returns Time in seconds, or null if parsing fails
 */
function parseFFmpegTime(timeString: string): number | null {
  try {
    // Match HH:MM:SS.mmm or HH:MM:SS format
    const timeMatch = timeString.match(/^(\d{2}):(\d{2}):(\d{2})(?:\.(\d+))?$/);
    if (!timeMatch) {
      return null;
    }
    
    const hours = parseInt(timeMatch[1], 10);
    const minutes = parseInt(timeMatch[2], 10);
    const seconds = parseInt(timeMatch[3], 10);
    const milliseconds = timeMatch[4] ? parseFloat(`0.${timeMatch[4]}`) : 0;
    
    return hours * 3600 + minutes * 60 + seconds + milliseconds;
  } catch (error) {
    return null;
  }
}

/**
 * Parse FFmpeg log message to extract progress information.
 * 
 * Extracts:
 * - Duration: "Duration: 00:00:14.92"
 * - Current time: "time=00:00:00.27"
 * 
 * @param logMessage - FFmpeg log message
 * @returns Object with duration and currentTime in seconds, or null if not found
 */
function parseFFmpegProgress(logMessage: string): {
  duration?: number;
  currentTime?: number;
} | null {
  const result: { duration?: number; currentTime?: number } = {};
  
  // Extract duration: "Duration: 00:00:14.92"
  const durationMatch = logMessage.match(/Duration:\s*([\d:\.]+)/);
  if (durationMatch) {
    const duration = parseFFmpegTime(durationMatch[1]);
    if (duration !== null) {
      result.duration = duration;
    }
  }
  
  // Extract current time: "time=00:00:00.27"
  const timeMatch = logMessage.match(/time=([\d:\.]+)/);
  if (timeMatch) {
    const currentTime = parseFFmpegTime(timeMatch[1]);
    if (currentTime !== null) {
      result.currentTime = currentTime;
    }
  }
  
  // Return null if no progress information found
  return Object.keys(result).length > 0 ? result : null;
}

/**
 * Lazy load FFmpeg instance.
 * This should be called only when MP4 export is needed to avoid loading ~30MB upfront.
 * 
 * Includes timeout and detailed error handling for better diagnostics.
 * 
 * @param timeout - Maximum time to wait for FFmpeg to load in milliseconds (default: 30000)
 * @returns Promise that resolves to FFmpeg instance
 */
let ffmpegInstance: FFmpeg | null = null;
let ffmpegLoading = false;
let ffmpegLoadPromise: Promise<FFmpeg> | null = null;

const DEFAULT_LOAD_TIMEOUT = 60000; // 60 seconds
const DEFAULT_CONVERSION_TIMEOUT = 300000; // 5 minutes for conversion

// FFmpeg core version - must match installed @ffmpeg/core package version
const FFMPEG_CORE_VERSION = "0.12.10";

/**
 * Get absolute URL for FFmpeg core files.
 * Uses window.location.origin to construct full URL from relative path.
 */
function getFFmpegCoreURL(relativePath: string): string {
  // In browser environment, use window.location.origin
  if (typeof window !== "undefined") {
    return `${window.location.origin}${relativePath}`;
  }
  // Fallback for SSR (should not happen in this context)
  return relativePath;
}

// Relative paths to FFmpeg core files served from static directory
// Files are copied to static/ffmpeg-core/ by vite-plugin-static-copy during build
const FFMPEG_CORE_RELATIVE_PATH = "/ffmpeg-core/ffmpeg-core.js";
const FFMPEG_WASM_RELATIVE_PATH = "/ffmpeg-core/ffmpeg-core.wasm";

/**
 * Load FFmpeg instance from local static files.
 * Core files are served from /ffmpeg-core/ directory (copied during build).
 * 
 * @param timeout - Maximum time to wait for FFmpeg to load in milliseconds (default: 60000)
 * @returns Promise that resolves to FFmpeg instance
 */
export async function loadFFmpeg(timeout: number = DEFAULT_LOAD_TIMEOUT): Promise<FFmpeg> {
  // Return existing instance if already loaded
  if (ffmpegInstance) {
    return ffmpegInstance;
  }

  // Return existing promise if already loading
  if (ffmpegLoadPromise) {
    return ffmpegLoadPromise;
  }

  // Start loading from local static files
  ffmpegLoadPromise = (async () => {
    const loadStartTime = Date.now();
    
    try {
      ffmpegLoading = true;
      
      if (import.meta.env?.DEV) {
        console.log(`[FFmpeg] Starting load from local static files (version ${FFMPEG_CORE_VERSION})...`);
      }

      // Create timeout promise
      const timeoutPromise = new Promise<never>((_, reject) => {
        setTimeout(() => {
          reject(new Error(`FFmpeg load timeout after ${timeout}ms`));
        }, timeout);
      });

      // Load promise
      const loadPromise = (async () => {
        try {
          // Dynamic import to enable lazy loading
          const { FFmpeg } = await import("@ffmpeg/ffmpeg");
          
          // Create FFmpeg instance
          const ffmpeg = new FFmpeg();

          // Set logging (enabled in dev for diagnostics)
          if (import.meta.env?.DEV) {
            ffmpeg.on("log", ({ message }) => {
              console.log("[FFmpeg]", message);
            });
          }

          // Load core files from local static directory
          // Construct absolute URLs from relative paths
          const coreURL = getFFmpegCoreURL(FFMPEG_CORE_RELATIVE_PATH);
          const wasmURL = getFFmpegCoreURL(FFMPEG_WASM_RELATIVE_PATH);
          
          if (import.meta.env?.DEV) {
            console.log(`[FFmpeg] Loading core from: ${coreURL}`);
            console.log(`[FFmpeg] Loading WASM from: ${wasmURL}`);
          }
          
          // Dynamically import FFmpeg utilities (browser-only, cannot be imported statically in SSR)
          const { toBlobURL } = await import("@ffmpeg/util");
          
          // Try loading directly with URLs first (same-origin should work)
          // If this fails, try with toBlobURL
          try {
            await ffmpeg.load({
              coreURL: coreURL,
              wasmURL: wasmURL,
            });
          } catch (directError: any) {
            // If direct loading fails, try with toBlobURL
            if (import.meta.env?.DEV) {
              console.log(`[FFmpeg] Direct URL load failed, trying with toBlobURL:`, directError.message);
            }
            await ffmpeg.load({
              coreURL: await toBlobURL(coreURL, "text/javascript"),
              wasmURL: await toBlobURL(wasmURL, "application/wasm"),
            });
          }

          const elapsed = Date.now() - loadStartTime;
          if (import.meta.env?.DEV) {
            console.log(`[FFmpeg] Successfully loaded in ${elapsed}ms`);
          }

          // Cache instance
          ffmpegInstance = ffmpeg;
          ffmpegLoading = false;
          ffmpegLoadPromise = null;
          
          return ffmpeg;
        } catch (error: any) {
          const elapsed = Date.now() - loadStartTime;
          const errorMessage = error?.message || String(error);
          
          if (import.meta.env?.DEV) {
            console.error(`[FFmpeg] Failed to load after ${elapsed}ms:`, errorMessage);
          }
          
          throw error;
        }
      })();

      // Race between load and timeout
      return await Promise.race([loadPromise, timeoutPromise]);
      
    } catch (error: any) {
      ffmpegLoading = false;
      ffmpegLoadPromise = null; // Clear promise on error so retry is possible
      
      const elapsed = Date.now() - loadStartTime;
      const errorMessage = error?.message || String(error);
      
      // Provide specific error messages
      if (errorMessage.includes("timeout") || errorMessage.includes("Timeout")) {
        const coreURL = typeof window !== "undefined" 
          ? getFFmpegCoreURL(FFMPEG_CORE_RELATIVE_PATH) 
          : FFMPEG_CORE_RELATIVE_PATH;
        const wasmURL = typeof window !== "undefined" 
          ? getFFmpegCoreURL(FFMPEG_WASM_RELATIVE_PATH) 
          : FFMPEG_WASM_RELATIVE_PATH;
        
        throw new Error(
          `FFmpeg load timeout after ${elapsed}ms. ` +
          `Please ensure FFmpeg core files are available at ${coreURL} and ${wasmURL}`
        );
      }
      
      if (errorMessage.includes("Failed to fetch") || errorMessage.includes("404")) {
        const coreURL = typeof window !== "undefined" 
          ? getFFmpegCoreURL(FFMPEG_CORE_RELATIVE_PATH) 
          : FFMPEG_CORE_RELATIVE_PATH;
        const wasmURL = typeof window !== "undefined" 
          ? getFFmpegCoreURL(FFMPEG_WASM_RELATIVE_PATH) 
          : FFMPEG_WASM_RELATIVE_PATH;
        
        throw new Error(
          `FFmpeg core files not found. ` +
          `Expected files at ${coreURL} and ${wasmURL}. ` +
          `Please rebuild the application to ensure static files are copied correctly.`
        );
      }
      
      if (errorMessage.includes("failed to import")) {
        throw new Error(
          `FFmpeg failed to import core files. ` +
          `This may indicate a version mismatch or corrupted files. ` +
          `Please verify that @ffmpeg/core@${FFMPEG_CORE_VERSION} is installed correctly. ` +
          `Original error: ${errorMessage}`
        );
      }
      
      throw new Error(
        `Failed to load FFmpeg: ${errorMessage} (took ${elapsed}ms)`
      );
    }
  })();

  return ffmpegLoadPromise;
}

/**
 * Export WebM video blob directly (no conversion).
 * This is faster and more reliable than converting to MP4.
 * WebM is compatible with all modern browsers and video players.
 * 
 * @param webmBlob - WebM video blob from MediaRecorder
 * @param filename - Optional filename (without extension)
 * @returns Promise that resolves when WebM is downloaded
 */
export async function exportToWebM(
  webmBlob: Blob,
  filename: string = `kidyland_menu_${new Date().toISOString().split("T")[0]}`
): Promise<void> {
  try {
    // Create blob URL and trigger download
    const url = URL.createObjectURL(webmBlob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${filename}.webm`;
    link.style.display = "none";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    // Cleanup
    setTimeout(() => URL.revokeObjectURL(url), 100);
  } catch (error: any) {
    throw new Error(`Error exporting to WebM: ${error.message}`);
  }
}

/**
 * Export canvas recording (WebM) to MP4 format.
 * 
 * NOTE: This requires FFmpeg.wasm which may fail to load. 
 * Consider using exportToWebM() for a more reliable alternative.
 * 
 * @param webmBlob - WebM video blob from MediaRecorder
 * @param filename - Optional filename (without extension)
 * @param onProgress - Optional progress callback (0-100)
 * @param options - Optional conversion options
 * @param options.fps - Target frame rate for output (default: 25). Forces frame rate and removes duplicates.
 * @param options.width - Optional output width (if not provided, keeps input resolution)
 * @param options.height - Optional output height (if not provided, keeps input resolution)
 * @returns Promise that resolves when MP4 is downloaded
 */
export async function exportToMP4(
  webmBlob: Blob,
  filename: string = `kidyland_menu_${new Date().toISOString().split("T")[0]}`,
  onProgress?: (progress: number) => void,
  options?: {
    fps?: number;
    width?: number;
    height?: number;
  }
): Promise<void> {
  try {
    // Lazy load FFmpeg with progress tracking
    onProgress?.(10);
    
    const ffmpeg = await loadFFmpeg().catch((error: any) => {
      // Reset progress on error and re-throw
      onProgress?.(0);
      throw error;
    });

    // Write WebM file to FFmpeg filesystem
    onProgress?.(30);
    // Dynamically import fetchFile (browser-only, cannot be imported statically in SSR)
    const { fetchFile } = await import("@ffmpeg/util");
    const webmData = await fetchFile(webmBlob);
    ffmpeg.writeFile("input.webm", webmData);

    // Convert WebM to MP4 using H.264 codec
    onProgress?.(50);
    
    // Extract conversion options with defaults
    const targetFps = options?.fps ?? 25; // Default 25 fps
    const outputWidth = options?.width;
    const outputHeight = options?.height;
    
    // Build video filter chain: fps filter to remove duplicates and force correct frame rate
    // This is critical for MediaRecorder videos that may have incorrect frame rate metadata
    // (e.g., "1k tbr" which causes FFmpeg to process thousands of duplicate frames)
    const videoFilters: string[] = [`fps=${targetFps}`];
    
    // Add scale filter if output resolution is specified
    if (outputWidth !== undefined && outputHeight !== undefined) {
      videoFilters.push(`scale=${outputWidth}:${outputHeight}`);
    }
    
    const videoFilter = videoFilters.join(",");
    
    // Set up real-time progress tracking from FFmpeg logs
    let videoDuration: number | null = null;
    let conversionProgress = 50; // Start at 50% (after loading and file writing)
    const progressRange = 40; // Conversion takes 50% to 90% of total progress
    
    // Set up log handler for progress tracking
    const logHandler = ({ message }: { message: string }) => {
      if (import.meta.env?.DEV) {
        console.log("[FFmpeg]", message);
      }
      
      // Parse progress information from log
      const progressInfo = parseFFmpegProgress(message);
      if (!progressInfo) {
        return;
      }
      
      // Update video duration if found
      if (progressInfo.duration !== undefined) {
        videoDuration = progressInfo.duration;
      }
      
      // Calculate progress based on current time vs duration
      if (progressInfo.currentTime !== undefined && videoDuration !== null && videoDuration > 0) {
        const timeProgress = Math.min(progressInfo.currentTime / videoDuration, 1.0);
        conversionProgress = 50 + Math.round(timeProgress * progressRange);
        onProgress?.(conversionProgress);
      }
    };
    
    // Register log handler for this conversion
    ffmpeg.on("log", logHandler);
    
    // Set up conversion timeout using Promise.race
    let conversionTimeoutId: ReturnType<typeof setTimeout> | null = null;
    const conversionTimeoutPromise = new Promise<never>((_, reject) => {
      conversionTimeoutId = setTimeout(() => {
        ffmpeg.off("log", logHandler);
        reject(new Error(
          `FFmpeg conversion timeout after ${DEFAULT_CONVERSION_TIMEOUT}ms. ` +
          `Video may be too long or conversion too slow.`
        ));
      }, DEFAULT_CONVERSION_TIMEOUT);
    });
    
    try {
      // Build FFmpeg command arguments
      const ffmpegArgs: string[] = [
        "-i",
        "input.webm",
        // Video filter: fps filter removes duplicate frames and forces correct frame rate
        // This is essential for MediaRecorder videos that may have incorrect frame rate metadata (e.g., "1k tbr")
        "-vf",
        videoFilter,
        "-c:v",
        "libx264",
        "-preset",
        "ultrafast", // Fastest encoding (slightly larger file, acceptable quality)
        "-tune",
        "zerolatency", // Reduce latency for faster processing
        "-crf",
        "23", // Quality: lower = better quality but larger file (18-28 is good range)
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        "-movflags",
        "+faststart", // Enable fast start for web playback
        "output.mp4",
      ];
      
      // Use optimized parameters for faster conversion
      const execPromise = ffmpeg.exec(ffmpegArgs);
      
      // Race between conversion and timeout
      await Promise.race([execPromise, conversionTimeoutPromise]);
    } finally {
      // Cleanup: remove log handler and clear timeout
      ffmpeg.off("log", logHandler);
      if (conversionTimeoutId !== null) {
        clearTimeout(conversionTimeoutId);
      }
      
      // Ensure progress is set to 90% when conversion completes
      if (conversionProgress < 90) {
        conversionProgress = 90;
        onProgress?.(conversionProgress);
      }
    }

    // Read output MP4 file (readFile returns a Promise in v0.12.15+)
    onProgress?.(90);
    const mp4Data = await ffmpeg.readFile("output.mp4");

    // Cleanup FFmpeg filesystem
    try {
      ffmpeg.deleteFile("input.webm");
      ffmpeg.deleteFile("output.mp4");
    } catch (cleanupError) {
      // Ignore cleanup errors, they're not critical
      if (import.meta.env?.DEV) {
        console.warn("[FFmpeg] Cleanup warning:", cleanupError);
      }
    }

    // Create blob and trigger download
    // FileData is Uint8Array, which is compatible with Blob constructor
    const mp4Blob = new Blob([mp4Data as BlobPart], { type: "video/mp4" });
    const url = URL.createObjectURL(mp4Blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${filename}.mp4`;
    link.style.display = "none";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    // Cleanup
    setTimeout(() => URL.revokeObjectURL(url), 100);
    onProgress?.(100);
  } catch (error: any) {
    // Ensure progress is reset on error
    onProgress?.(0);
    
    // Provide more descriptive error message
    const errorMessage = error?.message || String(error);
    throw new Error(`Error exporting to MP4: ${errorMessage}`);
  }
}

/**
 * Check if FFmpeg is loaded.
 */
export function isFFmpegLoaded(): boolean {
  return ffmpegInstance !== null;
}

/**
 * Get FFmpeg loading status.
 */
export function isFFmpegLoading(): boolean {
  return ffmpegLoading;
}

