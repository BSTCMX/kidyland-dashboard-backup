/**
 * Services store for managing services catalog.
 * 
 * Used by recepcion and admin modules.
 * Loads services from backend and provides reactive state.
 */
import { writable, derived } from "svelte/store";
import type { Writable } from "svelte/store";
import type { Service } from "@kidyland/shared/types";
import { get } from "@kidyland/utils";

export interface ServicesState {
  list: Service[];
  loading: boolean;
  error: string | null;
}

const initialState: ServicesState = {
  list: [],
  loading: false,
  error: null,
};

export const servicesStore: Writable<ServicesState> = writable(initialState);

/**
 * Fetch services for current sucursal.
 */
export async function fetchServices(sucursalId: string): Promise<void> {
  servicesStore.update((state) => ({ ...state, loading: true, error: null }));

  try {
    const services = await get<Service[]>(`/services?sucursal_id=${sucursalId}`);
    servicesStore.update((state) => ({
      ...state,
      list: services,
      loading: false,
    }));
  } catch (error: any) {
    servicesStore.update((state) => ({
      ...state,
      error: error.message || "Error loading services",
      loading: false,
    }));
  }
}

/**
 * Get active services only.
 */
export const activeServices = derived(servicesStore, ($store) =>
  $store.list.filter((service) => service.active !== false)
);

