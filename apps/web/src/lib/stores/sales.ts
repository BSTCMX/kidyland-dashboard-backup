/**
 * Sales store - Consolidated for recepcion and kidibar.
 * 
 * Handles both service sales (reception) and product sales (kidibar).
 * Unified interface with module-specific functions.
 */
import { writable } from "svelte/store";
import type { Writable } from "svelte/store";
import { post } from "@kidyland/utils/api";
import type { Sale, Timer, Product, Service } from "@kidyland/shared/types";
import { canEdit } from "./auth";

// ========== SERVICE SALES (RECEPCION) ==========

export interface ChildInfo {
  name: string;
  age?: number;
}

export interface ServiceSaleFormData {
  serviceId: string;
  durationMinutes: number;
  quantity?: number; // Quantity of services (default 1, or children.length if children provided)
  serviceType?: "timer" | "day"; // Timer or day-based service
  startDelayMinutes?: number; // Delay before starting timer (default 0)
  childName?: string; // Legacy single-child format (deprecated, use children array)
  childAge?: number; // Legacy single-child format (deprecated, use children array)
  children?: ChildInfo[]; // Multi-child format (preferred)
  payerName: string;
  payerPhone?: string;
  payerSignature?: string;  // Base64 encoded signature
  paymentMethod: "cash" | "card" | "transfer";
  cashReceivedCents?: number;
  cardAuthCode?: string;
  transferReference?: string;
  discountCents?: number;
}

// ========== PRODUCT SALES (KIDIBAR) ==========

export interface ProductSaleItem {
  productId: string;
  quantity: number;
  unitPriceCents: number;
}

// ========== PACKAGE SALES (RECEPCION) ==========

export interface PackageSaleFormData {
  packageId: string;
  quantity?: number; // Quantity of packages (default 1)
  scheduledDate?: string; // Scheduled date in YYYY-MM-DD format
  childName?: string; // Optional: only used by recepcion for service packages
  childAge?: number;
  payerName?: string; // Optional: can be omitted for quick product sales (kidibar)
  payerPhone?: string;
  payerSignature?: string;  // Base64 encoded signature
  paymentMethod: "cash" | "card" | "transfer";
  cashReceivedCents?: number;
  cardAuthCode?: string;
  transferReference?: string;
  discountCents?: number; // Optional: discount applied at package level
}

export interface ProductSaleFormData {
  items: ProductSaleItem[];
  payerName?: string; // Optional: can be omitted for quick product sales (kidibar)
  payerPhone?: string;
  paymentMethod: "cash" | "card" | "transfer";
  cashReceivedCents?: number;
  cardAuthCode?: string;
  transferReference?: string;
  discountCents?: number;
}

// ========== SHARED TYPES ==========

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

// ========== SERVICE SALES FUNCTIONS ==========

/**
 * Get price for a specific duration from duration_prices.
 * Falls back to the closest available duration price.
 */
function getPriceForDuration(
  durationPrices: Record<number, number>,
  durationsAllowed: number[],
  durationMinutes: number
): number {
  // If exact duration exists, use it
  if (durationPrices[durationMinutes] !== undefined) {
    return durationPrices[durationMinutes];
  }
  
  // Find the closest duration that is <= durationMinutes
  const validDurations = durationsAllowed
    .filter(d => d <= durationMinutes)
    .sort((a, b) => b - a); // Sort descending
  
  if (validDurations.length > 0) {
    const closestDuration = validDurations[0];
    if (durationPrices[closestDuration] !== undefined) {
      return durationPrices[closestDuration];
    }
  }
  
  // Fallback to minimum duration price
  const minDuration = Math.min(...durationsAllowed);
  if (durationPrices[minDuration] !== undefined) {
    return durationPrices[minDuration];
  }
  
  // Last resort: return 0 if no price found
  return 0;
}

/**
 * Calculate price for a service based on duration.
 * 
 * Uses duration_prices to get the price for the specific duration.
 * If exact duration not found, uses closest available duration price.
 */
export function calculateServicePrice(
  service: { duration_prices: Record<number, number>; durations_allowed: number[] },
  durationMinutes: number
): number {
  return getPriceForDuration(service.duration_prices, service.durations_allowed, durationMinutes);
}

/**
 * Create a sale with service item (reception).
 * 
 * This will automatically create a timer if the item is a service.
 * Validates permissions before creating.
 */
export async function createServiceSale(
  formData: ServiceSaleFormData,
  sucursalId: string,
  userId: string,
  service: { id: string; duration_prices: Record<number, number>; durations_allowed: number[] }
): Promise<SaleResponse> {
  // Validate permissions
  if (!canEdit("recepcion")) {
    throw new Error("No tienes permisos para crear ventas de servicios");
  }

  salesStore.update((state) => ({
    ...state,
    submitting: true,
    error: null,
  }));

  try {
    // Calculate pricing
    // For multi-child sales, quantity = number of children
    // For legacy single-child sales, quantity = 1
    const quantity = formData.children && formData.children.length > 0 
      ? formData.children.length 
      : (formData.quantity || 1);
    const unitPriceCents = calculateServicePrice(service, formData.durationMinutes);
    const subtotalCents = unitPriceCents * quantity; // Price per slot * number of children
    const discountCents = formData.discountCents || 0;
    const totalCents = subtotalCents - discountCents;

    // Build sale item
    const saleItem = {
      type: formData.serviceType === "day" ? "day" : "service",
      ref_id: formData.serviceId,
      quantity: quantity,
      unit_price_cents: unitPriceCents,
      subtotal_cents: subtotalCents,
      duration_minutes: formData.durationMinutes,
      // Default delay is 3 minutes for service sales (business rule)
      start_delay_minutes: formData.startDelayMinutes !== undefined ? formData.startDelayMinutes : 3,
    };

    // Build sale payload
    const salePayload: any = {
      tipo: "service",
      sucursal_id: sucursalId,
      usuario_id: userId,
      items: [saleItem],
      subtotal_cents: subtotalCents,
      discount_cents: discountCents,
      total_cents: totalCents,
      payer_name: formData.payerName || null,
      payer_phone: formData.payerPhone || null,
      payer_signature: formData.payerSignature || null,
      payment_method: formData.paymentMethod,
      cash_received_cents: formData.cashReceivedCents || null,
      card_auth_code: formData.cardAuthCode || null,
      transfer_reference: formData.transferReference || null,
      // Multi-child format (preferred)
      children: formData.children && formData.children.length > 0
        ? formData.children.map(child => ({
            name: child.name,
            age: child.age || null,
          }))
        : null,
      // Legacy single-child format (for backward compatibility)
      child_name: formData.children && formData.children.length > 0 
        ? null 
        : (formData.childName || null),
      child_age: formData.children && formData.children.length > 0 
        ? null 
        : (formData.childAge || null),
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

// ========== PRODUCT SALES FUNCTIONS ==========

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
 * Create a sale with product items (kidibar).
 * 
 * Products don't create timers, only services do.
 * Validates permissions before creating.
 */
export async function createProductSale(
  formData: ProductSaleFormData,
  sucursalId: string,
  userId: string
): Promise<SaleResponse> {
  // Validate permissions
  if (!canEdit("kidibar")) {
    throw new Error("No tienes permisos para crear ventas de productos");
  }

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
      payer_name: formData.payerName || null,
      payer_phone: formData.payerPhone || null,
      payment_method: formData.paymentMethod,
      cash_received_cents: formData.cashReceivedCents || null,
      card_auth_code: formData.cardAuthCode || null,
      transfer_reference: formData.transferReference || null,
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

// ========== PACKAGE SALES FUNCTIONS ==========

/**
 * Create a sale with package item (reusable for both recepcion and kidibar).
 * 
 * Packages are sold as complete units. The backend will handle
 * the services/products included in the package.
 * 
 * Validates permissions: user must have edit permissions for either recepcion or kidibar,
 * as both roles can create package sales (service packages for recepcion, product packages for kidibar).
 * This aligns with backend validation which allows both roles.
 */
export async function createPackageSale(
  formData: PackageSaleFormData,
  sucursalId: string,
  userId: string,
  packagePriceCents: number
): Promise<SaleResponse> {
  // Validate permissions: both recepcion and kidibar can create package sales
  // This aligns with backend validation: require_role(["recepcion", "kidibar"])
  if (!canEdit("recepcion") && !canEdit("kidibar")) {
    throw new Error("No tienes permisos para crear ventas de paquetes");
  }

  salesStore.update((state) => ({
    ...state,
    submitting: true,
    error: null,
  }));

  try {
    // Calculate pricing
    const quantity = formData.quantity || 1;
    const unitPriceCents = packagePriceCents;
    const subtotalCents = unitPriceCents * quantity;
    const discountCents = formData.discountCents || 0;
    const totalCents = subtotalCents - discountCents;

    // Build sale item
    const saleItem = {
      type: "package",
      ref_id: formData.packageId,
      quantity: quantity,
      unit_price_cents: unitPriceCents,
      subtotal_cents: subtotalCents,
    };

    // Build sale payload
    const salePayload: any = {
      tipo: "package",
      sucursal_id: sucursalId,
      usuario_id: userId,
      items: [saleItem],
      subtotal_cents: subtotalCents,
      discount_cents: discountCents,
      total_cents: totalCents,
      payer_name: formData.payerName || null,
      payer_phone: formData.payerPhone || null,
      payer_signature: formData.payerSignature || null,
      payment_method: formData.paymentMethod,
      cash_received_cents: formData.cashReceivedCents || null,
      card_auth_code: formData.cardAuthCode || null,
      transfer_reference: formData.transferReference || null,
      child_name: formData.childName || null,
      child_age: formData.childAge || null,
      scheduled_date: formData.scheduledDate || null, // Scheduled date for package
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
    const errorMessage = error.message || "Error creating package sale";
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

