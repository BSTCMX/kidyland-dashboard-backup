/**
 * Day close history store for viewing past day closes (arqueos).
 * 
 * Used by recepcion module to view history of day closes.
 */
import { writable } from "svelte/store";
import type { Writable } from "svelte/store";
import { get } from "@kidyland/utils/api";

export interface DayClose {
  id: string;
  sucursal_id: string;
  usuario_id: string;
  date: string; // YYYY-MM-DD format
  system_total_cents: number;
  physical_count_cents: number;
  difference_cents: number;
  totals: Record<string, any> | null;
  notes?: string | null; // Optional notes/observations for the day close
  created_at: string;
  updated_at: string;
  started_at?: string | null; // ISO format datetime string (from totals JSON, hybrid pattern)
  closed_at?: string | null; // ISO format datetime string (alias for created_at)
}

export interface DayCloseHistoryState {
  list: DayClose[];
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
  };
}

const initialState: DayCloseHistoryState = {
  list: [],
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
  },
};

export const dayCloseHistoryStore: Writable<DayCloseHistoryState> = writable(initialState);

/**
 * Fetch day closes with optional filters and pagination.
 */
export async function fetchDayCloseHistory(
  sucursalId?: string,
  startDate?: string,
  endDate?: string,
  skip: number = 0,
  limit: number = 25 // Default: 25 records per page
): Promise<void> {
  dayCloseHistoryStore.update((state) => ({ ...state, loading: true, error: null }));

  try {
    const params = new URLSearchParams();
    if (sucursalId) params.append("sucursal_id", sucursalId);
    if (startDate) params.append("start_date", startDate);
    if (endDate) params.append("end_date", endDate);
    params.append("skip", skip.toString());
    // Request limit + 1 to determine if there are more pages
    // This is more accurate than checking if dayCloses.length === limit
    params.append("limit", (limit + 1).toString());

    const dayCloses = await get<DayClose[]>(`/operations/day/closes?${params.toString()}`);
    
    // Calculate if there are more pages
    // If we got more than `limit` records, there are more pages
    // We only show `limit` records, keeping the extra one for detection
    const hasMore = dayCloses.length > limit;
    const dayClosesToShow = hasMore ? dayCloses.slice(0, limit) : dayCloses;
    
    // Calculate current page from skip and limit
    const currentPage = Math.floor(skip / limit) + 1;
    
    dayCloseHistoryStore.update((state) => ({
      ...state,
      list: dayClosesToShow,
      loading: false,
      pagination: {
        page: currentPage,
        pageSize: limit,
        hasMore,
      },
      filters: {
        startDate: startDate || null,
        endDate: endDate || null,
      },
    }));
  } catch (error: any) {
    dayCloseHistoryStore.update((state) => ({
      ...state,
      error: error.message || "Error loading day close history",
      loading: false,
    }));
  }
}

/**
 * Set page size for pagination.
 * Resets to page 1 when page size changes.
 */
export function setPageSize(pageSize: number): void {
  dayCloseHistoryStore.update((state) => ({
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
  dayCloseHistoryStore.update((state) => ({
    ...state,
    pagination: {
      ...state.pagination,
      page: Math.max(1, page), // Ensure page is at least 1
    },
  }));
}

