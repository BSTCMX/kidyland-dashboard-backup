/**
 * Sales store for managing sales operations.
 * 
 * Handles sale creation, state management, and integration with timers.
 */
import { writable } from "svelte/store";
import type { Writable } from "svelte/store";
import { post } from "@kidyland/utils/api";
import type { Sale, Timer } from "@kidyland/shared/types";

export interface SaleFormData {
  serviceId: string;
  durationMinutes: number;
  childName: string;
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
  timer: Timer | null;
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
 * Calculate price for a service based on duration.
 * 
 * Price = (duration_minutes / slot_duration) * base_price_per_slot
 * Where slot_duration is typically 30 or 60 minutes.
 */
export function calculateServicePrice(
  service: { base_price_per_slot: number; durations_allowed: number[] },
  durationMinutes: number
): number {
  // Find the slot duration (usually the minimum duration allowed)
  const slotDuration = Math.min(...service.durations_allowed);
  
  // Calculate number of slots
  const slots = Math.ceil(durationMinutes / slotDuration);
  
  // Calculate total price in cents
  return slots * service.base_price_per_slot;
}

/**
 * Create a sale with service item.
 * 
 * This will automatically create a timer if the item is a service.
 */
export async function createSale(
  formData: SaleFormData,
  sucursalId: string,
  userId: string,
  service: { id: string; base_price_per_slot: number; durations_allowed: number[] }
): Promise<SaleResponse> {
  salesStore.update((state) => ({
    ...state,
    submitting: true,
    error: null,
  }));

  try {
    // Calculate pricing
    const unitPriceCents = calculateServicePrice(service, formData.durationMinutes);
    const subtotalCents = unitPriceCents;
    const discountCents = formData.discountCents || 0;
    const totalCents = subtotalCents - discountCents;

    // Build sale item
    const saleItem = {
      type: "service",
      ref_id: formData.serviceId,
      quantity: 1,
      unit_price_cents: unitPriceCents,
      subtotal_cents: subtotalCents,
      duration_minutes: formData.durationMinutes,
    };

    // Build sale payload
    const salePayload = {
      tipo: "service",
      sucursal_id: sucursalId,
      usuario_id: userId,
      items: [saleItem],
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





























