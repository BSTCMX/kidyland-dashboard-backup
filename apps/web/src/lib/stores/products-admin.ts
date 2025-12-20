/**
 * Products admin store for CRUD operations.
 * 
 * Used by admin module for managing products.
 * Also synchronizes with productsStore for reception/kidibar modules.
 */
import { writable, get } from "svelte/store";
import type { Writable } from "svelte/store";
import type { Product } from "@kidyland/shared/types";
import { get as apiGet, post, put, del } from "@kidyland/utils";
import { productsStore } from "./products";
import { user } from "./auth";
import { getProductsBroadcastChannel } from "$lib/utils/broadcast-channel";

export interface ProductCreate {
  name: string;
  sucursales_ids: string[]; // Required: at least one sucursal
  sucursal_id?: string; // Optional: for backward compatibility
  price_cents: number;
  stock_qty?: number;
  threshold_alert_qty?: number;
  enabled_for_package?: boolean;
  package_deduction_qty?: number;
  active?: boolean;
}

export interface ProductUpdate {
  name?: string;
  sucursales_ids?: string[]; // Optional: can update sucursales
  sucursal_id?: string; // Optional: for backward compatibility
  price_cents?: number;
  stock_qty?: number;
  threshold_alert_qty?: number;
  enabled_for_package?: boolean;
  package_deduction_qty?: number;
  active?: boolean;
}

export interface ProductsAdminState {
  list: Product[];
  loading: boolean;
  error: string | null;
}

const initialState: ProductsAdminState = {
  list: [],
  loading: false,
  error: null,
};

export const productsAdminStore: Writable<ProductsAdminState> = writable(initialState);

/**
 * Initialize BroadcastChannel listeners for cross-tab synchronization.
 * This function should be called once when the module loads (browser only).
 */
function initializeBroadcastChannelListeners() {
  // Only initialize in browser environment
  if (typeof window === 'undefined') {
    return;
  }

  const broadcastChannel = getProductsBroadcastChannel();
  
  // Listen for product events from other tabs
  broadcastChannel.on('product-created', (product: Product) => {
    // Update admin store if product doesn't exist
    productsAdminStore.update((state) => {
      const exists = state.list.some((p) => p.id === product.id);
      if (!exists) {
        if (import.meta.env?.DEV) {
          console.debug('[BroadcastChannel] Received product-created event, adding to store:', {
            productId: product.id,
            productName: product.name,
          });
        }
        return {
          ...state,
          list: [product, ...state.list],
        };
      }
      return state;
    });
    
    // Also sync to productsStore if it belongs to current user's sucursal
    const currentUserSucursalId = getCurrentUserSucursalId();
    if (product.active !== false && currentUserSucursalId && productBelongsToSucursal(product, currentUserSucursalId)) {
      productsStore.update((state) => {
        const exists = state.list.some((p) => p.id === product.id);
        if (!exists) {
          return {
            ...state,
            list: [product, ...state.list],
          };
        }
        return {
          ...state,
          list: state.list.map((p) => (p.id === product.id ? product : p)),
        };
      });
    }
  });
  
  broadcastChannel.on('product-updated', (product: Product) => {
    // Update admin store
    productsAdminStore.update((state) => ({
      ...state,
      list: state.list.map((p) => (p.id === product.id ? product : p)),
    }));
    
    // Also sync to productsStore if it belongs to current user's sucursal
    const currentUserSucursalId = getCurrentUserSucursalId();
    if (currentUserSucursalId) {
      const belongsToSucursal = productBelongsToSucursal(product, currentUserSucursalId);
      const isActive = product.active !== false;
      
      productsStore.update((state) => {
        const exists = state.list.some((p) => p.id === product.id);
        
        if (exists) {
          if (belongsToSucursal && isActive) {
            // Update existing product if it belongs to sucursal and is active
            return {
              ...state,
              list: state.list.map((p) => (p.id === product.id ? product : p)),
            };
          } else {
            // Remove product if it no longer belongs to sucursal or is inactive
            return {
              ...state,
              list: state.list.filter((p) => p.id !== product.id),
            };
          }
        } else if (belongsToSucursal && isActive) {
          // Add new active product if it belongs to sucursal
          return {
            ...state,
            list: [product, ...state.list],
          };
        }
        
        // No changes needed
        return state;
      });
    }
  });
  
  broadcastChannel.on('product-deleted', (productId: string) => {
    // Update admin store
    productsAdminStore.update((state) => ({
      ...state,
      list: state.list.filter((p) => p.id !== productId),
    }));
    
    // Also remove from productsStore
    productsStore.update((state) => ({
      ...state,
      list: state.list.filter((p) => p.id !== productId),
    }));
  });
  
  broadcastChannel.on('product-refresh', () => {
    // Refresh products list when triggered from another tab
    const currentUserSucursalId = getCurrentUserSucursalId();
    if (currentUserSucursalId) {
      fetchAllProducts(currentUserSucursalId).catch((error) => {
        console.error('[BroadcastChannel] Error refreshing products:', error);
      });
    }
  });
}

// Initialize listeners on module load (browser only)
if (typeof window !== 'undefined') {
  initializeBroadcastChannelListeners();
}

/**
 * Check if a product belongs to a specific sucursal.
 * 
 * @param product - Product to check
 * @param sucursalId - Sucursal ID to check against
 * @returns true if product belongs to sucursal, false otherwise
 */
export function productBelongsToSucursal(product: Product, sucursalId: string | null | undefined): boolean {
  if (!sucursalId || !product) {
    // Logging for debugging (only in development)
    if (typeof window !== 'undefined' && import.meta.env?.DEV) {
      console.debug('[productBelongsToSucursal] Returning false:', {
        reason: !sucursalId ? 'no sucursalId' : 'no product',
        productId: product?.id,
        productName: product?.name,
      });
    }
    return false;
  }

  // Check sucursal_id (backward compatibility)
  if (product.sucursal_id === sucursalId) {
    if (typeof window !== 'undefined' && import.meta.env?.DEV) {
      console.debug('[productBelongsToSucursal] Match found via sucursal_id:', {
        productId: product.id,
        productName: product.name,
        sucursalId,
      });
    }
    return true;
  }

  // Check sucursales_ids array (new: support for multiple sucursales)
  if (product.sucursales_ids && Array.isArray(product.sucursales_ids) && product.sucursales_ids.length > 0) {
    if (product.sucursales_ids.includes(sucursalId)) {
      if (typeof window !== 'undefined' && import.meta.env?.DEV) {
        console.debug('[productBelongsToSucursal] Match found via sucursales_ids:', {
          productId: product.id,
          productName: product.name,
          sucursalId,
          sucursalesIds: product.sucursales_ids,
        });
      }
      return true;
    }
  }

  // Logging for debugging (only in development)
  if (typeof window !== 'undefined' && import.meta.env?.DEV) {
    console.debug('[productBelongsToSucursal] No match, returning false:', {
      productId: product.id,
      productName: product.name,
      sucursalId,
      productSucursalId: product.sucursal_id,
      productSucursalesIds: product.sucursales_ids,
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
 * Fetch all products (admin view).
 */
export async function fetchAllProducts(sucursalId?: string): Promise<void> {
  productsAdminStore.update((state) => ({ ...state, loading: true, error: null }));

  try {
    const url = sucursalId ? `/products?sucursal_id=${sucursalId}` : "/products";
    const products = await apiGet<Product[]>(url);
    productsAdminStore.update((state) => ({
      ...state,
      list: products,
      loading: false,
    }));
  } catch (error: any) {
    productsAdminStore.update((state) => ({
      ...state,
      error: error.message || "Error loading products",
      loading: false,
    }));
  }
}

/**
 * Create a new product.
 * Also updates the general productsStore for synchronization with reception/kidibar.
 */
export async function createProduct(productData: ProductCreate): Promise<Product | null> {
  productsAdminStore.update((state) => ({ ...state, loading: true, error: null }));

  try {
    const product = await post<Product>("/products", productData);
    
    // Update admin store
    productsAdminStore.update((state) => ({
      ...state,
      list: [product, ...state.list],
      loading: false,
    }));
    
    // Emit broadcast event for cross-tab synchronization
    if (typeof window !== 'undefined') {
      const broadcastChannel = getProductsBroadcastChannel();
      broadcastChannel.emit('product-created', product);
    }
    
    // Also update general productsStore if product is active and belongs to current user's sucursal
    // Only sync if the product belongs to the current user's sucursal (security + correctness)
    const currentUserSucursalId = getCurrentUserSucursalId();
    
    // Logging for debugging (only in development)
    if (typeof window !== 'undefined' && import.meta.env?.DEV) {
      console.debug('[createProduct] Checking sync conditions:', {
        productId: product.id,
        productName: product.name,
        isActive: product.active !== false,
        currentUserSucursalId,
        productSucursalId: product.sucursal_id,
      });
    }
    
    if (product.active !== false && currentUserSucursalId && productBelongsToSucursal(product, currentUserSucursalId)) {
      productsStore.update((state) => {
        // Check if product already exists (avoid duplicates)
        const exists = state.list.some((p) => p.id === product.id);
        if (!exists) {
          if (typeof window !== 'undefined' && import.meta.env?.DEV) {
            console.debug('[createProduct] Syncing product to productsStore (new):', {
              productId: product.id,
              productName: product.name,
            });
          }
          return {
            ...state,
            list: [product, ...state.list],
          };
        }
        // If exists, update it
        if (typeof window !== 'undefined' && import.meta.env?.DEV) {
          console.debug('[createProduct] Syncing product to productsStore (update):', {
            productId: product.id,
            productName: product.name,
          });
        }
        return {
          ...state,
          list: state.list.map((p) => (p.id === product.id ? product : p)),
        };
      });
    } else {
      // Logging when sync is skipped (only in development)
      if (typeof window !== 'undefined' && import.meta.env?.DEV) {
        console.debug('[createProduct] Skipping sync to productsStore:', {
          productId: product.id,
          productName: product.name,
          reason: !(product.active !== false) ? 'product inactive' : 
                  !currentUserSucursalId ? 'no user sucursal' : 
                  'product does not belong to user sucursal',
          belongsToSucursal: currentUserSucursalId ? productBelongsToSucursal(product, currentUserSucursalId) : false,
        });
      }
    }
    
    return product;
  } catch (error: any) {
    productsAdminStore.update((state) => ({
      ...state,
      error: error.message || "Error creating product",
      loading: false,
    }));
    return null;
  }
}

/**
 * Update an existing product.
 * Also updates the general productsStore for synchronization with reception/kidibar.
 */
export async function updateProduct(
  productId: string,
  productData: ProductUpdate
): Promise<Product | null> {
  productsAdminStore.update((state) => ({ ...state, loading: true, error: null }));

  try {
    const product = await put<Product>(`/products/${productId}`, productData);
    
    // Update admin store
    productsAdminStore.update((state) => ({
      ...state,
      list: state.list.map((p) => (p.id === productId ? product : p)),
      loading: false,
    }));
    
    // Emit broadcast event for cross-tab synchronization
    if (typeof window !== 'undefined') {
      const broadcastChannel = getProductsBroadcastChannel();
      broadcastChannel.emit('product-updated', product);
    }
    
    // Also update general productsStore if product belongs to current user's sucursal
    const currentUserSucursalId = getCurrentUserSucursalId();
    if (currentUserSucursalId) {
      const belongsToSucursal = productBelongsToSucursal(product, currentUserSucursalId);
      const isActive = product.active !== false;
      
      productsStore.update((state) => {
        const exists = state.list.some((p) => p.id === productId);
        
        if (exists) {
          if (belongsToSucursal && isActive) {
            // Update existing product if it belongs to sucursal and is active
            return {
              ...state,
              list: state.list.map((p) => (p.id === productId ? product : p)),
            };
          } else {
            // Remove product if it no longer belongs to sucursal or is inactive
            return {
              ...state,
              list: state.list.filter((p) => p.id !== productId),
            };
          }
        } else if (belongsToSucursal && isActive) {
          // Add new active product if it belongs to sucursal
          return {
            ...state,
            list: [product, ...state.list],
          };
        }
        
        // No changes needed
        return state;
      });
    }
    
    return product;
  } catch (error: any) {
    productsAdminStore.update((state) => ({
      ...state,
      error: error.message || "Error updating product",
      loading: false,
    }));
    return null;
  }
}

/**
 * Delete (deactivate) a product.
 * Also updates the general productsStore for synchronization with reception/kidibar.
 */
export async function deleteProduct(productId: string): Promise<boolean> {
  productsAdminStore.update((state) => ({ ...state, loading: true, error: null }));

  try {
    await del(`/products/${productId}`);
    
    // Update admin store
    productsAdminStore.update((state) => ({
      ...state,
      list: state.list.filter((p) => p.id !== productId),
      loading: false,
    }));
    
    // Emit broadcast event for cross-tab synchronization
    if (typeof window !== 'undefined') {
      const broadcastChannel = getProductsBroadcastChannel();
      broadcastChannel.emit('product-deleted', productId);
    }
    
    // Also remove from general productsStore
    productsStore.update((state) => ({
      ...state,
      list: state.list.filter((p) => p.id !== productId),
    }));
    
    return true;
  } catch (error: any) {
    productsAdminStore.update((state) => ({
      ...state,
      error: error.message || "Error deleting product",
      loading: false,
    }));
    return false;
  }
}

