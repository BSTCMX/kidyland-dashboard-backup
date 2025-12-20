/**
 * Products store for managing products catalog.
 * 
 * Loads products from backend and provides reactive state.
 * Based on services.ts pattern from reception app.
 */
import { writable, derived } from "svelte/store";
import type { Writable } from "svelte/store";
import type { Product } from "@kidyland/shared/types";
import { get } from "@kidyland/utils/api";

export interface ProductsState {
  list: Product[];
  loading: boolean;
  error: string | null;
}

const initialState: ProductsState = {
  list: [],
  loading: false,
  error: null,
};

export const productsStore: Writable<ProductsState> = writable(initialState);

/**
 * Fetch products for current sucursal.
 */
export async function fetchProducts(sucursalId: string): Promise<void> {
  productsStore.update((state) => ({ ...state, loading: true, error: null }));

  try {
    const products = await get<Product[]>(`/products?sucursal_id=${sucursalId}`);
    productsStore.update((state) => ({
      ...state,
      list: products,
      loading: false,
    }));
  } catch (error: any) {
    productsStore.update((state) => ({
      ...state,
      error: error.message || "Error loading products",
      loading: false,
    }));
  }
}

/**
 * Get active products with stock available.
 */
export const availableProducts = derived(productsStore, ($store) =>
  $store.list.filter(
    (product) => product.active !== false && product.stock_qty > 0
  )
);





























