/**
 * Sales store for managing sales operations in Kidibar.
 * 
 * Handles product sales creation, state management.
 * Based on sales.ts from reception app, adapted for products.
 */
import { writable } from "svelte/store";
import type { Writable } from "svelte/store";
import { post } from "@kidyland/utils/api";
import type { Sale, Product } from "@kidyland/shared/types";

export interface ProductSaleItem {
  productId: string;
  quantity: number;
  unitPriceCents: number;
}

export interface ProductSaleFormData {
  items: ProductSaleItem[];
  payerName: string;
  payerPhone?: string;
  paymentMethod: "cash" | "card" | "mixed";
  cashReceivedCents?: number;
  cardAuthCode?: string;
  discountCents?: number;
}

export interface SaleResponse {
  sale_id: string;
  timer_id: string | null;
  sale: Sale;
  timer: null; // Products don't create timers
}

export interface SalesState {
  submitting: boolean;
  error: string | null;
  lastSale: SaleResponse | null;
}

const initialState: SalesState = {
  submitting: false,
  error: null,
  lastSale: null,
};

export const salesStore: Writable<SalesState> = writable(initialState);

/**
 * Calculate total price for product sale items.
 */
export function calculateProductSaleTotal(items: ProductSaleItem[]): number {
  return items.reduce(
    (total, item) => total + item.unitPriceCents * item.quantity,
    0
  );
}

/**
 * Create a sale with product items.
 * 
 * Products don't create timers, only services do.
 */
export async function createProductSale(
  formData: ProductSaleFormData,
  sucursalId: string,
  userId: string
): Promise<SaleResponse> {
  salesStore.update((state) => ({
    ...state,
    submitting: true,
    error: null,
  }));

  try {
    // Calculate pricing
    const subtotalCents = calculateProductSaleTotal(formData.items);
    const discountCents = formData.discountCents || 0;
    const totalCents = subtotalCents - discountCents;

    // Build sale items
    const saleItems = formData.items.map((item) => ({
      type: "product",
      ref_id: item.productId,
      quantity: item.quantity,
      unit_price_cents: item.unitPriceCents,
      subtotal_cents: item.unitPriceCents * item.quantity,
    }));

    // Build sale payload
    const salePayload = {
      tipo: "product",
      sucursal_id: sucursalId,
      usuario_id: userId,
      items: saleItems,
      subtotal_cents: subtotalCents,
      discount_cents: discountCents,
      total_cents: totalCents,
      payer_name: formData.payerName,
      payer_phone: formData.payerPhone || null,
      payment_method: formData.paymentMethod,
      cash_received_cents: formData.cashReceivedCents || null,
      card_auth_code: formData.cardAuthCode || null,
    };

    // Create sale via API
    const response = await post<SaleResponse>("/sales", salePayload);

    salesStore.update((state) => ({
      ...state,
      submitting: false,
      lastSale: response,
    }));

    return response;
  } catch (error: any) {
    const errorMessage = error.message || "Error creating sale";
    salesStore.update((state) => ({
      ...state,
      submitting: false,
      error: errorMessage,
    }));
    throw error;
  }
}

/**
 * Reset sales store to initial state.
 */
export function resetSalesStore(): void {
  salesStore.set(initialState);
}





























