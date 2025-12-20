/**
 * Tests for sales store.
 * 
 * Covers service sales, product sales, validations, and permissions.
 */
import { describe, it, expect, beforeEach, vi } from "vitest";
import { get } from "svelte/store";
import {
  salesStore,
  createServiceSale,
  createProductSale,
  calculateServicePrice,
  calculateProductSaleTotal,
  resetSalesStore,
  type ServiceSaleFormData,
  type ProductSaleFormData,
} from "../sales";
import * as authStore from "../auth";

// Mock dependencies
vi.mock("../auth", () => ({
  canEdit: vi.fn(),
}));

vi.mock("@kidyland/utils", () => ({
  post: vi.fn(),
}));

import { post } from "@kidyland/utils";

describe("sales store", () => {
  beforeEach(() => {
    resetSalesStore();
    vi.clearAllMocks();
  });

  describe("initial state", () => {
    it("should have initial state with submitting false", () => {
      const state = get(salesStore);
      expect(state.submitting).toBe(false);
      expect(state.error).toBeNull();
      expect(state.lastSale).toBeNull();
    });
  });

  describe("calculateServicePrice", () => {
    it("should calculate price based on duration and slots", () => {
      const service = {
        base_price_per_slot: 1000,
        durations_allowed: [30, 60, 90],
      };
      
      const price = calculateServicePrice(service, 60);
      // 60 minutes / 30 (min slot) = 2 slots * 1000 = 2000
      expect(price).toBe(2000);
    });

    it("should round up to next slot", () => {
      const service = {
        base_price_per_slot: 1000,
        durations_allowed: [30, 60, 90],
      };
      
      const price = calculateServicePrice(service, 45);
      // 45 minutes / 30 = 1.5 slots, rounded up = 2 slots * 1000 = 2000
      expect(price).toBe(2000);
    });
  });

  describe("calculateProductSaleTotal", () => {
    it("should sum all item totals", () => {
      const items: ProductSaleFormData["items"] = [
        { productId: "1", quantity: 2, unitPriceCents: 500 },
        { productId: "2", quantity: 1, unitPriceCents: 1000 },
      ];
      
      const total = calculateProductSaleTotal(items);
      expect(total).toBe(2000); // (2 * 500) + (1 * 1000)
    });

    it("should return 0 for empty items", () => {
      const total = calculateProductSaleTotal([]);
      expect(total).toBe(0);
    });
  });

  describe("createServiceSale", () => {
    const mockService = {
      id: "service-1",
      base_price_per_slot: 1000,
      durations_allowed: [30, 60, 90],
    };

    const formData: ServiceSaleFormData = {
      serviceId: "service-1",
      durationMinutes: 60,
      childName: "Test Child",
      payerName: "Test Payer",
      paymentMethod: "cash",
    };

    it("should create service sale successfully", async () => {
      vi.mocked(authStore.canEdit).mockReturnValue(true);
      
      const mockResponse = {
        sale_id: "sale-1",
        timer_id: "timer-1",
        sale: {
          id: "sale-1",
          tipo: "service",
          total_cents: 2000,
        },
        timer: {
          id: "timer-1",
          status: "active",
        },
      };

      vi.mocked(post).mockResolvedValue(mockResponse);

      const result = await createServiceSale(
        formData,
        "sucursal-1",
        "user-1",
        mockService
      );

      expect(result).toEqual(mockResponse);
      expect(get(salesStore).lastSale).toEqual(mockResponse);
      expect(get(salesStore).submitting).toBe(false);
      expect(get(salesStore).error).toBeNull();
    });

    it("should throw error if user cannot edit recepcion", async () => {
      vi.mocked(authStore.canEdit).mockReturnValue(false);

      await expect(
        createServiceSale(formData, "sucursal-1", "user-1", mockService)
      ).rejects.toThrow("No tienes permisos para crear ventas de servicios");
    });

    it("should handle errors and update store", async () => {
      vi.mocked(authStore.canEdit).mockReturnValue(true);
      vi.mocked(post).mockRejectedValue(new Error("API Error"));

      await expect(
        createServiceSale(formData, "sucursal-1", "user-1", mockService)
      ).rejects.toThrow();

      expect(get(salesStore).error).toBe("API Error");
      expect(get(salesStore).submitting).toBe(false);
    });

    it("should calculate price correctly with quantity", async () => {
      vi.mocked(authStore.canEdit).mockReturnValue(true);
      
      const formDataWithQuantity: ServiceSaleFormData = {
        ...formData,
        quantity: 2,
      };

      vi.mocked(post).mockResolvedValue({
        sale_id: "sale-1",
        timer_id: "timer-1",
        sale: { id: "sale-1" },
        timer: { id: "timer-1" },
      });

      await createServiceSale(
        formDataWithQuantity,
        "sucursal-1",
        "user-1",
        mockService
      );

      const callArgs = vi.mocked(post).mock.calls[0][1] as any;
      expect(callArgs.subtotal_cents).toBe(4000); // 2 slots * 2 quantity * 1000
    });

    it("should include discount in total", async () => {
      vi.mocked(authStore.canEdit).mockReturnValue(true);
      
      const formDataWithDiscount: ServiceSaleFormData = {
        ...formData,
        discountCents: 500,
      };

      vi.mocked(post).mockResolvedValue({
        sale_id: "sale-1",
        timer_id: "timer-1",
        sale: { id: "sale-1" },
        timer: { id: "timer-1" },
      });

      await createServiceSale(
        formDataWithDiscount,
        "sucursal-1",
        "user-1",
        mockService
      );

      const callArgs = vi.mocked(post).mock.calls[0][1] as any;
      expect(callArgs.total_cents).toBe(1500); // 2000 - 500
      expect(callArgs.discount_cents).toBe(500);
    });

    it("should include optional fields when provided", async () => {
      vi.mocked(authStore.canEdit).mockReturnValue(true);
      
      const formDataWithExtras: ServiceSaleFormData = {
        ...formData,
        childAge: 5,
        payerPhone: "1234567890",
        payerSignature: "data:image/png;base64,...",
        startDelayMinutes: 15,
      };

      vi.mocked(post).mockResolvedValue({
        sale_id: "sale-1",
        timer_id: "timer-1",
        sale: { id: "sale-1" },
        timer: { id: "timer-1" },
      });

      await createServiceSale(
        formDataWithExtras,
        "sucursal-1",
        "user-1",
        mockService
      );

      const callArgs = vi.mocked(post).mock.calls[0][1] as any;
      expect(callArgs.child_age).toBe(5);
      expect(callArgs.payer_phone).toBe("1234567890");
      expect(callArgs.payer_signature).toBe("data:image/png;base64,...");
      expect(callArgs.items[0].start_delay_minutes).toBe(15);
    });
  });

  describe("createProductSale", () => {
    const formData: ProductSaleFormData = {
      items: [
        { productId: "product-1", quantity: 2, unitPriceCents: 500 },
        { productId: "product-2", quantity: 1, unitPriceCents: 1000 },
      ],
      payerName: "Test Payer",
      paymentMethod: "cash",
    };

    it("should create product sale successfully", async () => {
      vi.mocked(authStore.canEdit).mockReturnValue(true);
      
      const mockResponse = {
        sale_id: "sale-1",
        timer_id: null,
        sale: {
          id: "sale-1",
          tipo: "product",
          total_cents: 2000,
        },
        timer: null,
      };

      vi.mocked(post).mockResolvedValue(mockResponse);

      const result = await createProductSale(
        formData,
        "sucursal-1",
        "user-1"
      );

      expect(result).toEqual(mockResponse);
      expect(get(salesStore).lastSale).toEqual(mockResponse);
      expect(get(salesStore).submitting).toBe(false);
    });

    it("should throw error if user cannot edit kidibar", async () => {
      vi.mocked(authStore.canEdit).mockReturnValue(false);

      await expect(
        createProductSale(formData, "sucursal-1", "user-1")
      ).rejects.toThrow("No tienes permisos para crear ventas de productos");
    });

    it("should calculate total from items", async () => {
      vi.mocked(authStore.canEdit).mockReturnValue(true);
      
      vi.mocked(post).mockResolvedValue({
        sale_id: "sale-1",
        timer_id: null,
        sale: { id: "sale-1" },
        timer: null,
      });

      await createProductSale(formData, "sucursal-1", "user-1");

      const callArgs = vi.mocked(post).mock.calls[0][1] as any;
      expect(callArgs.subtotal_cents).toBe(2000);
      expect(callArgs.total_cents).toBe(2000);
    });

    it("should include discount in total", async () => {
      vi.mocked(authStore.canEdit).mockReturnValue(true);
      
      const formDataWithDiscount: ProductSaleFormData = {
        ...formData,
        discountCents: 300,
      };

      vi.mocked(post).mockResolvedValue({
        sale_id: "sale-1",
        timer_id: null,
        sale: { id: "sale-1" },
        timer: null,
      });

      await createProductSale(formDataWithDiscount, "sucursal-1", "user-1");

      const callArgs = vi.mocked(post).mock.calls[0][1] as any;
      expect(callArgs.total_cents).toBe(1700); // 2000 - 300
    });

    it("should set submitting state during API call", async () => {
      vi.mocked(authStore.canEdit).mockReturnValue(true);
      
      let resolvePost: (value: any) => void;
      const postPromise = new Promise((resolve) => {
        resolvePost = resolve;
      });
      
      vi.mocked(post).mockReturnValue(postPromise as any);

      const salePromise = createProductSale(formData, "sucursal-1", "user-1");
      
      // Check submitting is true
      expect(get(salesStore).submitting).toBe(true);
      
      // Resolve the API call
      resolvePost!({
        sale_id: "sale-1",
        timer_id: null,
        sale: { id: "sale-1" },
        timer: null,
      });
      
      await salePromise;
      
      // Check submitting is false after completion
      expect(get(salesStore).submitting).toBe(false);
    });
  });

  describe("resetSalesStore", () => {
    it("should reset store to initial state", () => {
      salesStore.update((state) => ({
        ...state,
        submitting: true,
        error: "Test error",
        lastSale: { sale_id: "test", timer_id: null, sale: {} as any, timer: null },
      }));

      resetSalesStore();

      const state = get(salesStore);
      expect(state.submitting).toBe(false);
      expect(state.error).toBeNull();
      expect(state.lastSale).toBeNull();
    });
  });
});

