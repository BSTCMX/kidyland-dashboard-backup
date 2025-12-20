/**
 * Sales history store for viewing past sales.
 * 
 * Used by recepcion and kidibar modules.
 */
import { writable, get as getStore } from "svelte/store";
import type { Writable } from "svelte/store";
import type { Sale, Sucursal } from "@kidyland/shared/types";
import { get } from "@kidyland/utils";
import { getApiUrlWithPath } from "$lib/utils/api-config";
import { getToken } from "$lib/stores/auth";

export interface SalesHistoryState {
  list: Sale[];
  current: Sale | null;
  loading: boolean;
  error: string | null;
  pagination: {
    page: number;
    pageSize: number; // 25, 50, or 100
    hasMore: boolean;
  };
  filters: {
    startDate: string | null;
    endDate: string | null;
    tipo: string | null;
  };
}

const initialState: SalesHistoryState = {
  list: [],
  current: null,
  loading: false,
  error: null,
  pagination: {
    page: 1,
    pageSize: 25, // Default: 25 records per page
    hasMore: false,
  },
  filters: {
    startDate: null,
    endDate: null,
    tipo: null,
  },
};

export const salesHistoryStore: Writable<SalesHistoryState> = writable(initialState);

/**
 * Fetch sales with optional filters and pagination.
 * 
 * @param package_type - Filter package sales by package type (service, product). Only valid when tipo='package'
 * @param include_package_type - Include package sales of specified type along with tipo filter. Example: tipo='product' + include_package_type='product' returns both product sales and product packages
 */
export async function fetchSales(
  sucursalId?: string,
  startDate?: string,
  endDate?: string,
  tipo?: string,
  skip: number = 0,
  limit: number = 25, // Default: 25 records per page
  package_type?: string,
  include_package_type?: string
): Promise<void> {
  salesHistoryStore.update((state) => ({ ...state, loading: true, error: null }));

  try {
    const params = new URLSearchParams();
    if (sucursalId) params.append("sucursal_id", sucursalId);
    if (startDate) params.append("start_date", startDate);
    if (endDate) params.append("end_date", endDate);
    if (tipo) params.append("tipo", tipo);
    if (package_type) params.append("package_type", package_type);
    if (include_package_type) params.append("include_package_type", include_package_type);
    params.append("skip", skip.toString());
    // Request limit + 1 to determine if there are more pages
    // This is more accurate than checking if sales.length === limit
    params.append("limit", (limit + 1).toString());

    const sales = await get<Sale[]>(`/sales?${params.toString()}`);
    
    // Calculate if there are more pages
    // If we got more than `limit` records, there are more pages
    // We only show `limit` records, keeping the extra one for detection
    const hasMore = sales.length > limit;
    const salesToShow = hasMore ? sales.slice(0, limit) : sales;
    
    // Calculate current page from skip and limit
    const currentPage = Math.floor(skip / limit) + 1;
    
    salesHistoryStore.update((state) => ({
      ...state,
      list: salesToShow,
      loading: false,
      pagination: {
        page: currentPage,
        pageSize: limit,
        hasMore,
      },
      filters: {
        startDate: startDate || null,
        endDate: endDate || null,
        tipo: tipo || null,
      },
    }));
  } catch (error: any) {
    salesHistoryStore.update((state) => ({
      ...state,
      error: error.message || "Error loading sales",
      loading: false,
    }));
  }
}

/**
 * Set page size for pagination.
 * Resets to page 1 when page size changes.
 */
export function setPageSize(pageSize: number): void {
  salesHistoryStore.update((state) => ({
    ...state,
    pagination: {
      ...state.pagination,
      pageSize,
      page: 1, // Reset to page 1 when changing page size
      hasMore: false, // Will be updated on next fetch
    },
  }));
}

/**
 * Set current page for pagination.
 */
export function setPage(page: number): void {
  salesHistoryStore.update((state) => ({
    ...state,
    pagination: {
      ...state.pagination,
      page: Math.max(1, page), // Ensure page is at least 1
    },
  }));
}

/**
 * Get timezone for a sucursal.
 * 
 * Uses a cache to avoid repeated API calls for the same sucursal.
 * Falls back to default timezone if the API call fails or user doesn't have permissions.
 * 
 * @param sucursalId - Sucursal ID to get timezone for
 * @returns Timezone string (e.g., "America/Mexico_City") or default "America/Mexico_City"
 */
const timezoneCache: Map<string, string> = new Map();

async function getSucursalTimezone(sucursalId?: string): Promise<string> {
  if (!sucursalId) {
    return "America/Mexico_City"; // Default timezone
  }
  
  // Check cache first
  if (timezoneCache.has(sucursalId)) {
    return timezoneCache.get(sucursalId)!;
  }
  
  try {
    // Try to get the specific sucursal by ID
    // This endpoint allows users to view their own sucursal
    const sucursal = await get<Sucursal>(`/sucursales/${sucursalId}`);
    const timezone = sucursal?.timezone || "America/Mexico_City";
    
    // Cache the result
    timezoneCache.set(sucursalId, timezone);
    return timezone;
  } catch (error) {
    // If we can't get the sucursal (e.g., not found or no permissions),
    // fall back to default timezone
    console.warn("Could not fetch sucursal timezone, using default:", error);
    // Cache the default to avoid repeated failed calls
    timezoneCache.set(sucursalId, "America/Mexico_City");
    return "America/Mexico_City";
  }
}

/**
 * Calculate start and end of today in a specific timezone, converted to UTC dates for backend.
 * 
 * Strategy:
 * 1. Get today's date (YYYY-MM-DD) in the target timezone
 * 2. Calculate the UTC times that correspond to 00:00:00 and 23:59:59.999 in that timezone
 * 3. Return the UTC dates in YYYY-MM-DD format for the backend query
 * 
 * @param timezone - IANA timezone string (e.g., "America/Mexico_City")
 * @returns Object with startDate and endDate in YYYY-MM-DD format (representing UTC dates)
 */
function getTodayDateRangeInTimezone(timezone: string): { startDate: string; endDate: string } {
  const now = new Date();
  
  // Get today's date string (YYYY-MM-DD) in the target timezone
  const dateFormatter = new Intl.DateTimeFormat("en-CA", {
    timeZone: timezone,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  });
  
  const todayInTZ = dateFormatter.format(now); // e.g., "2025-12-15"
  
  // Calculate timezone offset using a reference time (noon to avoid DST issues)
  const referenceUTC = new Date(`${todayInTZ}T12:00:00Z`); // Noon UTC
  const offsetMs = getTimezoneOffsetMs(timezone, referenceUTC);
  
  // Start of day: 00:00:00 in the timezone
  // If timezone is UTC-6 (offset = -6 hours = -21600000 ms):
  // - Midnight in timezone = 06:00 UTC (same day)
  // - Formula: UTC = local - offset, so UTC = 00:00 - (-6h) = 06:00
  const startOfDayLocal = new Date(`${todayInTZ}T00:00:00Z`); // Midnight UTC (temporary)
  const startOfDayUTC = new Date(startOfDayLocal.getTime() - offsetMs);
  
  // End of day: 23:59:59.999 in the timezone
  const endOfDayLocal = new Date(`${todayInTZ}T23:59:59.999Z`); // 23:59:59.999 UTC (temporary)
  const endOfDayUTC = new Date(endOfDayLocal.getTime() - offsetMs);
  
  return {
    startDate: startOfDayUTC.toISOString().split("T")[0],
    endDate: endOfDayUTC.toISOString().split("T")[0],
  };
}

/**
 * Get timezone offset in milliseconds for a given timezone and UTC date.
 * 
 * @param timezone - IANA timezone string
 * @param utcDate - UTC date to get offset for
 * @returns Offset in milliseconds (negative if timezone is behind UTC, positive if ahead)
 */
function getTimezoneOffsetMs(timezone: string, utcDate: Date): number {
  // Get the time components in UTC
  const utcHours = utcDate.getUTCHours();
  const utcMinutes = utcDate.getUTCMinutes();
  
  // Get the same moment's time components in the target timezone
  const tzFormatter = new Intl.DateTimeFormat("en-US", {
    timeZone: timezone,
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
  
  const tzParts = tzFormatter.formatToParts(utcDate);
  const tzHours = parseInt(tzParts.find((p) => p.type === "hour")?.value || "0", 10);
  const tzMinutes = parseInt(tzParts.find((p) => p.type === "minute")?.value || "0", 10);
  
  // Calculate offset: difference between timezone time and UTC time
  // If UTC is 12:00 and TZ is 06:00, offset = 6 - 12 = -6 hours (TZ is behind UTC)
  const offsetHours = tzHours - utcHours;
  const offsetMinutes = tzMinutes - utcMinutes;
  const offsetMs = (offsetHours * 60 + offsetMinutes) * 60000;
  
  return offsetMs;
}

/**
 * Fetch today's sales with pagination support.
 * Uses fetchSales internally with today's date range filters calculated in the sucursal's timezone.
 * Optionally filters by sale type (service, product, package, etc.).
 * 
 * @param sucursalId - Optional sucursal ID to filter by (used to get timezone)
 * @param tipo - Optional sale type filter
 * @param skip - Number of records to skip (for pagination), defaults to 0
 * @param limit - Maximum number of records to return, defaults to store's pageSize
 * @param package_type - Filter package sales by package type (service, product). Only valid when tipo='package'
 * @param include_package_type - Include package sales of specified type along with tipo filter
 */
export async function fetchTodaySales(
  sucursalId?: string,
  tipo?: string,
  skip: number = 0,
  limit?: number,
  package_type?: string,
  include_package_type?: string
): Promise<void> {
  // Get timezone for the sucursal
  const timezone = await getSucursalTimezone(sucursalId);
  
  // Calculate today's date range in the sucursal's timezone
  // This ensures we get all sales from "today" in the local timezone, not UTC
  const { startDate, endDate } = getTodayDateRangeInTimezone(timezone);
  
  // Use store's pageSize if limit not provided
  const pageSize = limit ?? getStore(salesHistoryStore).pagination.pageSize;
  
  // Reuse fetchSales with today's date filters
  // This unifies pagination logic and ensures consistency
  return fetchSales(sucursalId, startDate, endDate, tipo, skip, pageSize, package_type, include_package_type);
}

/**
 * Fetch a single sale by ID.
 */
export async function fetchSaleById(saleId: string): Promise<Sale | null> {
  salesHistoryStore.update((state) => ({ ...state, loading: true, error: null }));

  try {
    const sale = await get<Sale>(`/sales/${saleId}`);
    salesHistoryStore.update((state) => ({
      ...state,
      current: sale,
      loading: false,
    }));
    return sale;
  } catch (error: any) {
    salesHistoryStore.update((state) => ({
      ...state,
      error: error.message || "Error loading sale",
      loading: false,
    }));
    return null;
  }
}

/**
 * Get ticket HTML for a sale (without printing).
 * 
 * @param saleId - Sale ID to get ticket for
 * @returns HTML string of the ticket
 */
export async function getTicketHtml(saleId: string): Promise<string> {
  try {
    const apiUrl = getApiUrlWithPath(`/sales/${saleId}/print`);
    const token = getToken();
    
    if (!token) {
      throw new Error("Authentication required");
    }
    
    const response = await fetch(apiUrl, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      throw new Error("Error generating ticket");
    }

    // Get HTML content
    const html = await response.text();
    return html;
  } catch (error: any) {
    throw new Error(error.message || "Error getting ticket");
  }
}

/**
 * Print ticket for a sale.
 */
export async function printTicket(saleId: string): Promise<void> {
  try {
    const html = await getTicketHtml(saleId);
    
    // Open in new window for printing
    const printWindow = window.open("", "_blank");
    if (printWindow) {
      printWindow.document.write(html);
      printWindow.document.close();
      printWindow.focus();
      // Auto-print after a short delay
      setTimeout(() => {
        printWindow.print();
      }, 250);
    }
  } catch (error: any) {
    throw new Error(error.message || "Error printing ticket");
  }
}

