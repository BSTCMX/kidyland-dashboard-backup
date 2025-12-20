/**
 * Download utility - Helper functions for file downloads.
 * 
 * Handles auto-download of files from blob URLs or API endpoints.
 * Mobile-compatible with fallback for browsers that block auto-downloads.
 */

/**
 * Download a file from a blob URL.
 * 
 * @param blobUrl - Blob URL to download
 * @param filename - Filename for the download
 */
export function downloadFromBlob(blobUrl: string, filename: string): void {
  const link = document.createElement("a");
  link.href = blobUrl;
  link.download = filename;
  link.style.display = "none";
  
  // Trigger download
  document.body.appendChild(link);
  link.click();
  
  // Cleanup
  setTimeout(() => {
    document.body.removeChild(link);
    URL.revokeObjectURL(blobUrl);
  }, 100);
}

/**
 * Download a file from an API endpoint.
 * 
 * @param url - API endpoint URL
 * @param filename - Filename for the download
 * @param token - Optional JWT token for authentication
 * @returns Promise that resolves when download starts
 */
export async function downloadFromApi(
  url: string,
  filename: string,
  token?: string
): Promise<void> {
  try {
    const headers: HeadersInit = {};
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
    
    const response = await fetch(url, {
      method: "GET",
      headers,
    });
    
    if (!response.ok) {
      throw new Error(`Download failed: ${response.statusText}`);
    }
    
    // Get blob from response
    const blob = await response.blob();
    
    // Create blob URL
    const blobUrl = URL.createObjectURL(blob);
    
    // Trigger download
    downloadFromBlob(blobUrl, filename);
  } catch (error) {
    console.error("Error downloading file:", error);
    throw error;
  }
}

/**
 * Check if browser supports auto-download.
 * 
 * @returns true if auto-download is likely to work
 */
export function supportsAutoDownload(): boolean {
  // Most modern browsers support auto-download
  // iOS Safari may require user gesture
  const userAgent = navigator.userAgent.toLowerCase();
  const isIOS = /iphone|ipad|ipod/.test(userAgent);
  const isSafari = /safari/.test(userAgent) && !/chrome/.test(userAgent);
  
  // iOS Safari may block auto-downloads
  if (isIOS && isSafari) {
    return false;
  }
  
  return true;
}





























