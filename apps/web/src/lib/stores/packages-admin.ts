/**
 * Packages admin store for CRUD operations.
 * 
 * Used by admin module for managing packages.
 */
import { writable } from "svelte/store";
import type { Writable } from "svelte/store";
import type { Package } from "@kidyland/shared/types";
import { get, post, put, del } from "@kidyland/utils";

export interface PackageCreate {
  name: string;
  sucursal_id: string;
  description?: string;
  price_cents: number;
  included_items: Array<{
    product_id?: string;
    service_id?: string;
    quantity?: number; // For products
    duration_minutes?: number; // For services (optional)
  }>;
  active?: boolean;
}

export interface PackageUpdate {
  name?: string;
  description?: string;
  price_cents?: number;
  included_items?: Array<{
    product_id?: string;
    service_id?: string;
    quantity?: number; // For products
    duration_minutes?: number; // For services (optional)
  }>;
  active?: boolean;
}

export interface PackagesAdminState {
  list: Package[];
  loading: boolean;
  error: string | null;
}

const initialState: PackagesAdminState = {
  list: [],
  loading: false,
  error: null,
};

export const packagesAdminStore: Writable<PackagesAdminState> = writable(initialState);

/**
 * Fetch all packages (admin view).
 */
export async function fetchAllPackages(sucursalId?: string): Promise<void> {
  packagesAdminStore.update((state) => ({ ...state, loading: true, error: null }));

  try {
    const url = sucursalId ? `/packages?sucursal_id=${sucursalId}` : "/packages";
    const packages = await get<Package[]>(url);
    packagesAdminStore.update((state) => ({
      ...state,
      list: packages,
      loading: false,
    }));
  } catch (error: any) {
    packagesAdminStore.update((state) => ({
      ...state,
      error: error.message || "Error loading packages",
      loading: false,
    }));
  }
}

/**
 * Create a new package.
 */
export async function createPackage(packageData: PackageCreate): Promise<Package | null> {
  packagesAdminStore.update((state) => ({ ...state, loading: true, error: null }));

  try {
    const package_ = await post<Package>("/packages", packageData);
    packagesAdminStore.update((state) => ({
      ...state,
      list: [package_, ...state.list],
      loading: false,
    }));
    return package_;
  } catch (error: any) {
    packagesAdminStore.update((state) => ({
      ...state,
      error: error.message || "Error creating package",
      loading: false,
    }));
    throw error;
  }
}

/**
 * Update an existing package.
 */
export async function updatePackage(
  packageId: string,
  packageData: PackageUpdate
): Promise<Package | null> {
  packagesAdminStore.update((state) => ({ ...state, loading: true, error: null }));

  try {
    const package_ = await put<Package>(`/packages/${packageId}`, packageData);
    packagesAdminStore.update((state) => ({
      ...state,
      list: state.list.map((p) => (p.id === packageId ? package_ : p)),
      loading: false,
    }));
    return package_;
  } catch (error: any) {
    packagesAdminStore.update((state) => ({
      ...state,
      error: error.message || "Error updating package",
      loading: false,
    }));
    throw error;
  }
}

/**
 * Delete (soft delete) a package.
 */
export async function deletePackage(packageId: string): Promise<void> {
  packagesAdminStore.update((state) => ({ ...state, loading: true, error: null }));

  try {
    await del(`/packages/${packageId}`);
    packagesAdminStore.update((state) => ({
      ...state,
      list: state.list.filter((p) => p.id !== packageId),
      loading: false,
    }));
  } catch (error: any) {
    packagesAdminStore.update((state) => ({
      ...state,
      error: error.message || "Error deleting package",
      loading: false,
    }));
    throw error;
  }
}

