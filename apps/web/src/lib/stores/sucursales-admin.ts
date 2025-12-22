/**
 * Sucursales admin store - CRUD operations for sucursales.
 * 
 * Used by admin module for managing sucursales.
 */
import { writable, get } from "svelte/store";
import type { Writable } from "svelte/store";
import { get as apiGet, post, put, del, createPromiseGuard } from "@kidyland/utils";
import type { Sucursal } from "@kidyland/shared/types";

export interface SucursalCreate {
  identifier: string;  // e.g., "suc01"
  name: string;
  address?: string;
  timezone?: string;
  active?: boolean;
}

export interface SucursalUpdate {
  identifier?: string;  // e.g., "suc01"
  name?: string;
  address?: string;
  timezone?: string;
  active?: boolean;
}

export interface SucursalesAdminState {
  list: Sucursal[];
  loading: boolean;
  error: string | null;
}

const initialState: SucursalesAdminState = {
  list: [],
  loading: false,
  error: null,
};

export const sucursalesAdminStore: Writable<SucursalesAdminState> = writable(initialState);

// Promise guard to prevent concurrent fetch operations
const fetchGuard = createPromiseGuard<Sucursal[]>();

// Cache with TTL: prevent redundant requests
let lastFetchTime: number = 0;
const CACHE_DURATION_MS = 60000; // 1 minute cache

/**
 * Fetch all sucursales.
 * 
 * Clean Architecture: Prevents duplicate requests with Promise Guard and TTL cache.
 * - Uses Promise Guard to prevent concurrent requests (reuses same promise)
 * - Uses TTL cache to skip fetch if data is fresh (within CACHE_DURATION_MS)
 * - Invalidates cache on mutations (create/update/delete)
 * 
 * @param force - Force fetch even if cache is valid (default: false)
 */
export async function fetchAllSucursales(force: boolean = false): Promise<void> {
  const currentState = get(sucursalesAdminStore);
  const now = Date.now();
  
  // Guard 1: Check TTL cache (skip if data is fresh and not forced)
  if (!force && currentState.list.length > 0 && (now - lastFetchTime) < CACHE_DURATION_MS) {
    return Promise.resolve();
  }

  // Guard 2: Use Promise Guard to prevent concurrent requests
  return fetchGuard.execute(async () => {
    sucursalesAdminStore.update((state) => ({ ...state, loading: true, error: null }));

    try {
      const sucursales = await apiGet<Sucursal[]>("/sucursales");
      lastFetchTime = Date.now();
      sucursalesAdminStore.update((state) => ({
        ...state,
        list: sucursales,
        loading: false,
      }));
    } catch (error: any) {
      sucursalesAdminStore.update((state) => ({
        ...state,
        error: error.message || "Error loading sucursales",
        loading: false,
      }));
      throw error;
    }
  });
}

/**
 * Create a new sucursal.
 */
export async function createSucursal(sucursalData: SucursalCreate): Promise<Sucursal | null> {
  sucursalesAdminStore.update((state) => ({ ...state, loading: true, error: null }));

  try {
    const newSucursal = await post<Sucursal>("/sucursales", sucursalData);
    lastFetchTime = 0; // Invalidate cache after create
    sucursalesAdminStore.update((state) => ({
      ...state,
      list: [newSucursal, ...state.list],
      loading: false,
    }));
    return newSucursal;
  } catch (error: any) {
    sucursalesAdminStore.update((state) => ({
      ...state,
      error: error.message || "Error creating sucursal",
      loading: false,
    }));
    throw error;
  }
}

/**
 * Update an existing sucursal.
 */
export async function updateSucursal(
  sucursalId: string,
  sucursalData: SucursalUpdate
): Promise<Sucursal | null> {
  sucursalesAdminStore.update((state) => ({ ...state, loading: true, error: null }));

  try {
    const updatedSucursal = await put<Sucursal>(`/sucursales/${sucursalId}`, sucursalData);
    lastFetchTime = 0; // Invalidate cache after update
    sucursalesAdminStore.update((state) => ({
      ...state,
      list: state.list.map((s) => (s.id === sucursalId ? updatedSucursal : s)),
      loading: false,
    }));
    return updatedSucursal;
  } catch (error: any) {
    sucursalesAdminStore.update((state) => ({
      ...state,
      error: error.message || "Error updating sucursal",
      loading: false,
    }));
    throw error;
  }
}

/**
 * Delete (soft delete) a sucursal.
 */
export async function deleteSucursal(sucursalId: string): Promise<boolean> {
  sucursalesAdminStore.update((state) => ({ ...state, loading: true, error: null }));

  try {
    await del(`/sucursales/${sucursalId}`);
    lastFetchTime = 0; // Invalidate cache after delete
    sucursalesAdminStore.update((state) => ({
      ...state,
      list: state.list.filter((s) => s.id !== sucursalId),
      loading: false,
    }));
    return true;
  } catch (error: any) {
    sucursalesAdminStore.update((state) => ({
      ...state,
      error: error.message || "Error deleting sucursal",
      loading: false,
    }));
    throw error;
  }
}

