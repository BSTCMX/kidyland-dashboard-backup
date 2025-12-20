/**
 * Sucursales admin store - CRUD operations for sucursales.
 * 
 * Used by admin module for managing sucursales.
 */
import { writable } from "svelte/store";
import type { Writable } from "svelte/store";
import { get, post, put, del } from "@kidyland/utils";
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

/**
 * Fetch all sucursales.
 */
export async function fetchAllSucursales(): Promise<void> {
  sucursalesAdminStore.update((state) => ({ ...state, loading: true, error: null }));

  try {
    const sucursales = await get<Sucursal[]>("/sucursales");
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
  }
}

/**
 * Create a new sucursal.
 */
export async function createSucursal(sucursalData: SucursalCreate): Promise<Sucursal | null> {
  sucursalesAdminStore.update((state) => ({ ...state, loading: true, error: null }));

  try {
    const newSucursal = await post<Sucursal>("/sucursales", sucursalData);
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

