/**
 * Services admin store for CRUD operations.
 * 
 * Used by admin module for managing services.
 */
import { writable, get } from "svelte/store";
import type { Writable } from "svelte/store";
import type { Service } from "@kidyland/shared/types";
import { get as apiGet, post, put, del } from "@kidyland/utils";
import { servicesStore } from "./services";
import { user } from "./auth";
import { getServicesBroadcastChannel } from "$lib/utils/broadcast-channel";
import { getServiceFilterSucursalId } from "$lib/utils/service-filters";

export interface ServiceCreate {
  name: string;
  sucursal_id?: string; // Optional: can be derived from sucursales_ids by backend
  sucursales_ids?: string[]; // New: support for multiple sucursales (at least one required)
  durations_allowed: number[];
  duration_prices: Record<number, number>; // Required: {duration_minutes: price_cents} for flexible pricing
  alerts_config: Array<{
    minutes_before: number;
    sound?: string; // Kept for backward compatibility
    sound_enabled?: boolean; // New: enable/disable sound for this alert
    sound_loop?: boolean; // New: loop sound continuously until stopped
  }>;
  active?: boolean;
}

export interface ServiceUpdate {
  name?: string;
  sucursal_id?: string; // Kept for backward compatibility
  sucursales_ids?: string[]; // New: support for multiple sucursales
  durations_allowed?: number[];
  duration_prices?: Record<number, number>; // Optional: {duration_minutes: price_cents} for flexible pricing
  alerts_config?: Array<{
    minutes_before: number;
    sound?: string; // Kept for backward compatibility
    sound_enabled?: boolean; // New: enable/disable sound for this alert
    sound_loop?: boolean; // New: loop sound continuously until stopped
  }>;
  active?: boolean;
}

export interface ServicesAdminState {
  list: Service[];
  loading: boolean;
  error: string | null;
}

const initialState: ServicesAdminState = {
  list: [],
  loading: false,
  error: null,
};

export const servicesAdminStore: Writable<ServicesAdminState> = writable(initialState);

/**
 * Initialize BroadcastChannel listeners for cross-tab synchronization.
 * This function should be called once when the module loads (browser only).
 */
function initializeBroadcastChannelListeners() {
  // Only initialize in browser environment
  if (typeof window === 'undefined') {
    return;
  }

  const broadcastChannel = getServicesBroadcastChannel();
  
  // Listen for service events from other tabs
  broadcastChannel.on('service-created', (service: Service) => {
    // Update admin store if service doesn't exist
    servicesAdminStore.update((state) => {
      const exists = state.list.some((s) => s.id === service.id);
      if (!exists) {
        if (import.meta.env?.DEV) {
          console.debug('[BroadcastChannel] Received service-created event, adding to store:', {
            serviceId: service.id,
            serviceName: service.name,
          });
        }
        return {
          ...state,
          list: [service, ...state.list],
        };
      }
      return state;
    });
    
    // Also sync to servicesStore if it belongs to current user's sucursal
    const currentUserSucursalId = getCurrentUserSucursalId();
    if (service.active !== false && currentUserSucursalId && serviceBelongsToSucursal(service, currentUserSucursalId)) {
      servicesStore.update((state) => {
        const exists = state.list.some((s) => s.id === service.id);
        if (!exists) {
          return {
            ...state,
            list: [service, ...state.list],
          };
        }
        return {
          ...state,
          list: state.list.map((s) => (s.id === service.id ? service : s)),
        };
      });
    }
  });
  
  broadcastChannel.on('service-updated', (service: Service) => {
    // Update admin store
    servicesAdminStore.update((state) => ({
      ...state,
      list: state.list.map((s) => (s.id === service.id ? service : s)),
    }));
    
    // Also sync to servicesStore if it belongs to current user's sucursal
    const currentUserSucursalId = getCurrentUserSucursalId();
    if (currentUserSucursalId) {
      const belongsToSucursal = serviceBelongsToSucursal(service, currentUserSucursalId);
      const isActive = service.active !== false;
      
      servicesStore.update((state) => {
        const exists = state.list.some((s) => s.id === service.id);
        if (exists) {
          if (belongsToSucursal && isActive) {
            return {
              ...state,
              list: state.list.map((s) => (s.id === service.id ? service : s)),
            };
          } else {
            return {
              ...state,
              list: state.list.filter((s) => s.id !== service.id),
            };
          }
        } else if (belongsToSucursal && isActive) {
          return {
            ...state,
            list: [service, ...state.list],
          };
        }
        return state;
      });
    }
  });
  
  broadcastChannel.on('service-deleted', (serviceId: string) => {
    // Remove from admin store
    servicesAdminStore.update((state) => ({
      ...state,
      list: state.list.filter((s) => s.id !== serviceId),
    }));
    
    // Also remove from servicesStore
    servicesStore.update((state) => ({
      ...state,
      list: state.list.filter((s) => s.id !== serviceId),
    }));
  });
  
  broadcastChannel.on('service-refresh', () => {
    // Refresh services list when requested from another tab
    // Use role-based filtering: super_admin sees all, others see filtered
    const currentUser = get(user);
    const filterSucursalId = getServiceFilterSucursalId(currentUser);
    fetchAllServices(filterSucursalId);
  });
}

// Initialize listeners when module loads (browser only)
if (typeof window !== 'undefined') {
  initializeBroadcastChannelListeners();
}

/**
 * Helper function to check if a service belongs to a specific sucursal.
 * 
 * A service belongs to a sucursal if:
 * - service.sucursal_id matches the sucursalId, OR
 * - service.sucursales_ids array contains the sucursalId
 * 
 * @param service - The service to check
 * @param sucursalId - The sucursal ID to check against
 * @returns true if the service belongs to the sucursal, false otherwise
 */
export function serviceBelongsToSucursal(service: Service, sucursalId: string | null | undefined): boolean {
  if (!sucursalId || !service) {
    // Logging for debugging (only in development)
    if (typeof window !== 'undefined' && import.meta.env?.DEV) {
      console.debug('[serviceBelongsToSucursal] Returning false:', {
        reason: !sucursalId ? 'no sucursalId' : 'no service',
        serviceId: service?.id,
        serviceName: service?.name,
      });
    }
    return false;
  }

  // Check primary sucursal_id (backward compatibility)
  if (service.sucursal_id === sucursalId) {
    if (typeof window !== 'undefined' && import.meta.env?.DEV) {
      console.debug('[serviceBelongsToSucursal] Match found via sucursal_id:', {
        serviceId: service.id,
        serviceName: service.name,
        sucursalId,
      });
    }
    return true;
  }

  // Check sucursales_ids array (multiple sucursales support)
  if (service.sucursales_ids && Array.isArray(service.sucursales_ids)) {
    // Handle both string and UUID formats
    const found = service.sucursales_ids.some((id) => {
      const idStr = typeof id === 'string' ? id : String(id);
      const sucursalIdStr = typeof sucursalId === 'string' ? sucursalId : String(sucursalId);
      return idStr === sucursalIdStr;
    });
    
    if (typeof window !== 'undefined' && import.meta.env?.DEV) {
      if (found) {
        console.debug('[serviceBelongsToSucursal] Match found via sucursales_ids:', {
          serviceId: service.id,
          serviceName: service.name,
          sucursalId,
          sucursales_ids: service.sucursales_ids,
        });
      } else {
        console.debug('[serviceBelongsToSucursal] No match in sucursales_ids:', {
          serviceId: service.id,
          serviceName: service.name,
          sucursalId,
          sucursales_ids: service.sucursales_ids,
        });
      }
    }
    
    return found;
  }

  // Logging for debugging (only in development)
  if (typeof window !== 'undefined' && import.meta.env?.DEV) {
    console.debug('[serviceBelongsToSucursal] No match, returning false:', {
      serviceId: service.id,
      serviceName: service.name,
      sucursalId,
      hasSucursalesIds: !!service.sucursales_ids,
      sucursalesIdsType: typeof service.sucursales_ids,
      isArray: Array.isArray(service.sucursales_ids),
    });
  }

  return false;
}

/**
 * Get current user's sucursal_id from auth store.
 * 
 * @returns The current user's sucursal_id or null
 */
function getCurrentUserSucursalId(): string | null {
  const currentUser = get(user);
  return currentUser?.sucursal_id || null;
}

/**
 * Fetch all services (admin view).
 */
export async function fetchAllServices(sucursalId?: string): Promise<void> {
  servicesAdminStore.update((state) => ({ ...state, loading: true, error: null }));

  try {
    const url = sucursalId ? `/services?sucursal_id=${sucursalId}` : "/services";
    const services = await apiGet<Service[]>(url);
    servicesAdminStore.update((state) => ({
      ...state,
      list: services,
      loading: false,
    }));
  } catch (error: any) {
    servicesAdminStore.update((state) => ({
      ...state,
      error: error.message || "Error loading services",
      loading: false,
    }));
  }
}

/**
 * Create a new service.
 */
/**
 * Create a new service.
 * Also updates the general servicesStore for synchronization with reception/mobile.
 */
export async function createService(serviceData: ServiceCreate): Promise<Service | null> {
  servicesAdminStore.update((state) => ({ ...state, loading: true, error: null }));

  try {
    const service = await post<Service>("/services", serviceData);
    
    // Update admin store
    servicesAdminStore.update((state) => ({
      ...state,
      list: [service, ...state.list],
      loading: false,
    }));
    
    // Emit broadcast event for cross-tab synchronization
    if (typeof window !== 'undefined') {
      const broadcastChannel = getServicesBroadcastChannel();
      broadcastChannel.emit('service-created', service);
    }
    
    // Also update general servicesStore if service is active and belongs to current user's sucursal
    // Only sync if the service belongs to the current user's sucursal (security + correctness)
    const currentUserSucursalId = getCurrentUserSucursalId();
    
    // Logging for debugging (only in development)
    if (typeof window !== 'undefined' && import.meta.env?.DEV) {
      console.debug('[createService] Checking sync conditions:', {
        serviceId: service.id,
        serviceName: service.name,
        isActive: service.active !== false,
        currentUserSucursalId,
        serviceSucursalId: service.sucursal_id,
        serviceSucursalesIds: service.sucursales_ids,
      });
    }
    
    if (service.active !== false && currentUserSucursalId && serviceBelongsToSucursal(service, currentUserSucursalId)) {
      servicesStore.update((state) => {
        // Check if service already exists (avoid duplicates)
        const exists = state.list.some((s) => s.id === service.id);
        if (!exists) {
          if (typeof window !== 'undefined' && import.meta.env?.DEV) {
            console.debug('[createService] Syncing service to servicesStore (new):', {
              serviceId: service.id,
              serviceName: service.name,
            });
          }
          return {
            ...state,
            list: [service, ...state.list],
          };
        }
        // If exists, update it
        if (typeof window !== 'undefined' && import.meta.env?.DEV) {
          console.debug('[createService] Syncing service to servicesStore (update):', {
            serviceId: service.id,
            serviceName: service.name,
          });
        }
        return {
          ...state,
          list: state.list.map((s) => (s.id === service.id ? service : s)),
        };
      });
    } else {
      // Logging when sync is skipped (only in development)
      if (typeof window !== 'undefined' && import.meta.env?.DEV) {
        console.debug('[createService] Skipping sync to servicesStore:', {
          serviceId: service.id,
          serviceName: service.name,
          reason: !(service.active !== false) ? 'service inactive' : 
                  !currentUserSucursalId ? 'no user sucursal' : 
                  'service does not belong to user sucursal',
          belongsToSucursal: currentUserSucursalId ? serviceBelongsToSucursal(service, currentUserSucursalId) : false,
        });
      }
    }
    
    return service;
  } catch (error: any) {
    servicesAdminStore.update((state) => ({
      ...state,
      error: error.message || "Error creating service",
      loading: false,
    }));
    return null;
  }
}

/**
 * Update an existing service.
 */
/**
 * Update an existing service.
 * Also updates the general servicesStore for synchronization with reception/mobile.
 */
export async function updateService(
  serviceId: string,
  serviceData: ServiceUpdate
): Promise<Service | null> {
  servicesAdminStore.update((state) => ({ ...state, loading: true, error: null }));

  try {
    const service = await put<Service>(`/services/${serviceId}`, serviceData);
    
    // Update admin store
    servicesAdminStore.update((state) => ({
      ...state,
      list: state.list.map((s) => (s.id === serviceId ? service : s)),
      loading: false,
    }));
    
    // Emit broadcast event for cross-tab synchronization
    if (typeof window !== 'undefined') {
      const broadcastChannel = getServicesBroadcastChannel();
      broadcastChannel.emit('service-updated', service);
    }
    
    // Also update general servicesStore if service belongs to current user's sucursal
    const currentUserSucursalId = getCurrentUserSucursalId();
    if (currentUserSucursalId) {
      const belongsToSucursal = serviceBelongsToSucursal(service, currentUserSucursalId);
      const isActive = service.active !== false;
      
      servicesStore.update((state) => {
        const exists = state.list.some((s) => s.id === serviceId);
        
        if (exists) {
          if (belongsToSucursal && isActive) {
            // Update existing service if it belongs to sucursal and is active
            return {
              ...state,
              list: state.list.map((s) => (s.id === serviceId ? service : s)),
            };
          } else {
            // Remove service if it no longer belongs to sucursal or is inactive
            return {
              ...state,
              list: state.list.filter((s) => s.id !== serviceId),
            };
          }
        } else if (belongsToSucursal && isActive) {
          // Add new active service if it belongs to sucursal
          return {
            ...state,
            list: [service, ...state.list],
          };
        }
        
        // No changes needed
        return state;
      });
    }
    
    return service;
  } catch (error: any) {
    servicesAdminStore.update((state) => ({
      ...state,
      error: error.message || "Error updating service",
      loading: false,
    }));
    return null;
  }
}

/**
 * Delete (deactivate) a service.
 */
/**
 * Delete (deactivate) a service.
 * Also updates the general servicesStore for synchronization with reception/mobile.
 */
export async function deleteService(serviceId: string): Promise<boolean> {
  servicesAdminStore.update((state) => ({ ...state, loading: true, error: null }));

  try {
    await del(`/services/${serviceId}`);
    
    // Update admin store
    servicesAdminStore.update((state) => ({
      ...state,
      list: state.list.filter((s) => s.id !== serviceId),
      loading: false,
    }));
    
    // Emit broadcast event for cross-tab synchronization
    if (typeof window !== 'undefined') {
      const broadcastChannel = getServicesBroadcastChannel();
      broadcastChannel.emit('service-deleted', serviceId);
    }
    
    // Also remove from general servicesStore
    servicesStore.update((state) => ({
      ...state,
      list: state.list.filter((s) => s.id !== serviceId),
    }));
    
    return true;
  } catch (error: any) {
    servicesAdminStore.update((state) => ({
      ...state,
      error: error.message || "Error deleting service",
      loading: false,
    }));
    return false;
  }
}

