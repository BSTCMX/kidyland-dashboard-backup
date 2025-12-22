/**
 * Day operations store - Day start/close operations.
 * 
 * Handles day start and close operations with cash reconciliation.
 */
import { writable } from "svelte/store";
import { get, post } from "@kidyland/utils/api";

export interface DayOperationsState {
  dayStatus: {
    isOpen: boolean;
    openedAt?: string;
    closedAt?: string;
    currentBusinessDate?: string; // YYYY-MM-DD format in sucursal timezone
    dayStart?: {
      id: string;
      sucursal_id: string;
      usuario_id: string;
      started_at: string;
      initial_cash_cents: number;
      is_active: boolean;
      created_at: string;
      updated_at: string;
    };
  } | null;
  loading: boolean;
  error: string | null;
}

export const dayOperationsStore = writable<DayOperationsState>({
  dayStatus: null,
  loading: false,
  error: null,
});

/**
 * Fetch day status for a sucursal.
 * 
 * @param sucursalId - Sucursal ID to fetch day status for
 */
export async function fetchDayStatus(sucursalId: string): Promise<void> {
  dayOperationsStore.update((state) => ({ ...state, loading: true, error: null }));
  
  try {
    const response = await get<{
      is_open: boolean;
      day_start: {
        id: string;
        sucursal_id: string;
        usuario_id: string;
        started_at: string;
        initial_cash_cents: number;
        is_active: boolean;
        created_at: string;
        updated_at: string;
      } | null;
      current_date: string;
      current_business_date?: string; // YYYY-MM-DD format in sucursal timezone
    }>(`/operations/day/status?sucursal_id=${sucursalId}`);
    
    dayOperationsStore.update((state) => ({
      ...state,
      dayStatus: {
        isOpen: response.is_open,
        openedAt: response.day_start?.started_at,
        currentBusinessDate: response.current_business_date,
        dayStart: response.day_start || undefined,
      },
      loading: false,
    }));
  } catch (error: any) {
    dayOperationsStore.update((state) => ({
      ...state,
      loading: false,
      error: error.message || "Error al obtener estado del día",
    }));
    throw error;
  }
}

/**
 * Start day for a sucursal.
 * 
 * @param data - Day start data with sucursal_id and initial_cash_cents
 */
export async function startDay(data: {
  sucursal_id: string;
  initial_cash_cents: number;
}): Promise<boolean> {
  dayOperationsStore.update((state) => ({ ...state, loading: true, error: null }));
  
  try {
    const response = await post<{
      success: boolean;
      message: string;
      day_start: {
        id: string;
        sucursal_id: string;
        usuario_id: string;
        started_at: string;
        initial_cash_cents: number;
        is_active: boolean;
        created_at: string;
        updated_at: string;
      };
    }>("/operations/day/start", {
      sucursal_id: data.sucursal_id,
      initial_cash_cents: data.initial_cash_cents,
    });
    
    // Refresh day status after starting
    await fetchDayStatus(data.sucursal_id);
    
    dayOperationsStore.update((state) => ({
      ...state,
      loading: false,
    }));
    
    return response.success;
  } catch (error: any) {
    dayOperationsStore.update((state) => ({
      ...state,
      loading: false,
      error: error.message || "Error al iniciar el día",
    }));
    throw error;
  }
}

/**
 * Close day with cash reconciliation.
 * 
 * @param data - Day close data with sucursal_id, date, physical_count_cents, etc.
 * system_total_cents is optional - backend will calculate it automatically if not provided.
 */
export interface DayClosePreview {
  expected_total_cents: number;
  initial_cash_cents: number;
  cash_received_total_cents: number;
  breakdown: {
    total_revenue_cents: number;
    total_sales_count: number;
    revenue_by_payment_method: Record<string, number>;
    revenue_by_type: Record<string, number>;
  };
  business_date: string; // YYYY-MM-DD format
  timezone: string;
  period: {
    start_datetime: string;
    end_datetime: string;
  };
}

/**
 * Preview day close calculations without actually closing the day.
 * 
 * @param sucursalId - Sucursal ID to preview day close for
 * @param module - Optional module context: 'kidibar' to filter only product sales, 'recepcion' for all sales
 * @returns Preview data with expected totals and breakdown
 */
export async function previewDayClose(sucursalId: string, module?: "kidibar" | "recepcion"): Promise<DayClosePreview> {
  try {
    const moduleParam = module ? `&module=${module}` : "";
    const preview = await get<DayClosePreview>(
      `/operations/day/close/preview?sucursal_id=${sucursalId}${moduleParam}`
    );
    return preview;
  } catch (error: any) {
    throw new Error(error.message || "Error al obtener el preview del cierre de día");
  }
}

export async function closeDay(data: {
  sucursal_id: string;
  date: string; // YYYY-MM-DD format
  system_total_cents?: number; // Optional: backend calculates automatically if not provided
  physical_count_cents: number;
  totals?: Record<string, any>;
  notes?: string; // Optional notes/observations
}): Promise<{
  id: string;
  sucursal_id: string;
  usuario_id: string;
  date: string;
  system_total_cents: number;
  physical_count_cents: number;
  difference_cents: number;
  totals: Record<string, any> | null;
  notes?: string | null;
  created_at: string;
  updated_at: string;
}> {
  dayOperationsStore.update((state) => ({ ...state, loading: true, error: null }));
  
  try {
    const response = await post<{
      success: boolean;
      message: string;
      day_close: {
        id: string;
        sucursal_id: string;
        usuario_id: string;
        date: string;
        system_total_cents: number;
        physical_count_cents: number;
        difference_cents: number;
        totals: Record<string, any> | null;
        notes?: string | null;
        created_at: string;
        updated_at: string;
      };
    }>("/operations/day/close", {
      sucursal_id: data.sucursal_id,
      date: data.date,
      ...(data.system_total_cents !== undefined && { system_total_cents: data.system_total_cents }),
      physical_count_cents: data.physical_count_cents,
      totals: data.totals || null,
      notes: data.notes || null,
    });
    
    if (!response.success) {
      throw new Error(response.message || "Error al cerrar el día");
    }
    
    // Refresh day status after closing
    await fetchDayStatus(data.sucursal_id);
    
    dayOperationsStore.update((state) => ({
      ...state,
      loading: false,
    }));
    
    return response.day_close;
  } catch (error: any) {
    dayOperationsStore.update((state) => ({
      ...state,
      loading: false,
      error: typeof error === 'string' ? error : (error?.message || "Error al cerrar el día"),
    }));
    throw error;
  }
}
