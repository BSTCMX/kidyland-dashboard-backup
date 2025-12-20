/**
 * Tests for ExtendTimerModal component.
 * 
 * Covers modal open/close, timer extension logic, and timers store integration.
 */
import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/svelte";
import ExtendTimerModal from "../shared/ExtendTimerModal.svelte";
import { post as apiPost } from "@kidyland/utils";
import type { Timer } from "@kidyland/shared/types";

// Mock API utilities
vi.mock("@kidyland/utils", () => ({
  get: vi.fn(),
  post: vi.fn(),
}));

// Mock @kidyland/ui components - Use actual components but simplify tests
// The components will render, we just need to ensure they work

describe("ExtendTimerModal", () => {
  const mockTimer: Timer = {
    id: "timer-1",
    sale_id: "sale-1",
    service_id: "service-1",
    child_name: "Test Child",
    child_age: 5,
    start_at: new Date().toISOString(),
    end_at: new Date(Date.now() + 3600000).toISOString(), // 1 hour from now
    status: "active",
    history: [],
  };

  const defaultProps = {
    timer: mockTimer,
    open: true,
    saleId: "sale-1",
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("modal visibility", () => {
    it("should render when open is true", () => {
      render(ExtendTimerModal, { props: { ...defaultProps, open: true } });
      // Modal renders the content when open - use getAllByText and check first
      const modalContents = screen.getAllByText(/extender timer/i);
      expect(modalContents.length).toBeGreaterThan(0);
    });

    it("should not render content when open is false", () => {
      render(ExtendTimerModal, { props: { ...defaultProps, open: false } });
      // Modal doesn't render content when closed
      const modalContent = screen.queryByText(/extender timer/i);
      expect(modalContent).not.toBeInTheDocument();
    });
  });

  describe("timer information display", () => {
    it("should display timer details", () => {
      render(ExtendTimerModal, { props: defaultProps });
      
      if (mockTimer.child_name) {
        expect(screen.getByText(mockTimer.child_name)).toBeInTheDocument();
      }
    });

    it("should display timer status", () => {
      render(ExtendTimerModal, { props: defaultProps });
      
      expect(screen.getByText(/estado/i)).toBeInTheDocument();
      expect(screen.getByText(mockTimer.status)).toBeInTheDocument();
    });
  });

  describe("extension input", () => {
    it("should have input for minutes to add", () => {
      render(ExtendTimerModal, { props: defaultProps });
      
      const minutesInput = screen.queryByLabelText(/minutos a agregar/i);
      expect(minutesInput).toBeInTheDocument();
    });

    it("should accept minutes input", async () => {
      render(ExtendTimerModal, { props: defaultProps });
      
      const minutesInput = screen.getByLabelText(/minutos a agregar/i) as HTMLInputElement;
      
      // Should accept positive numbers
      await fireEvent.input(minutesInput, { target: { value: "30" } });
      expect(minutesInput.value).toBe("30");
    });

    it("should have input field for minutes", () => {
      render(ExtendTimerModal, { props: defaultProps });
      
      const minutesInput = screen.queryByLabelText(/minutos a agregar/i);
      expect(minutesInput).toBeInTheDocument();
    });
  });

  describe("extension submission", () => {
    it("should call extend endpoint on submit", async () => {
      (apiPost as any).mockResolvedValue({});

      render(ExtendTimerModal, { props: defaultProps });
      
      await waitFor(async () => {
        const minutesInput = screen.getByLabelText(/minutos a agregar/i) as HTMLInputElement;
        await fireEvent.input(minutesInput, { target: { value: "30" } });
        
        const submitButton = screen.getByRole("button", { name: /extender timer/i });
        await fireEvent.click(submitButton);
      }, { timeout: 2000 });

      await waitFor(() => {
        expect(apiPost).toHaveBeenCalledWith(
          expect.stringContaining("/extend"),
          {}
        );
      }, { timeout: 2000 });
    });

    it("should handle extension errors", async () => {
      (apiPost as any).mockRejectedValue(new Error("Extension failed"));

      render(ExtendTimerModal, { props: defaultProps });
      
      // Wait for component to render
      await waitFor(() => {
        const minutesInput = screen.getByLabelText(/minutos a agregar/i);
        expect(minutesInput).toBeInTheDocument();
      }, { timeout: 2000 });
      
      const minutesInput = screen.getByLabelText(/minutos a agregar/i) as HTMLInputElement;
      await fireEvent.input(minutesInput, { target: { value: "30" } });
      
      // Find submit button by text content (multiple elements match "extender")
      const buttons = screen.getAllByRole("button");
      const submitButton = buttons.find(btn => 
        btn.textContent?.toLowerCase().includes("extender timer") || 
        (btn.textContent?.toLowerCase().includes("extender") && !btn.textContent?.toLowerCase().includes("cancelar"))
      );
      expect(submitButton).toBeDefined();
      await fireEvent.click(submitButton!);

      // Wait for error to be displayed
      // Error message can be "Error al extender el timer" or "Extension failed"
      await waitFor(() => {
        const errorBanner = screen.queryByText(/error al extender/i) || 
                           screen.queryByText(/extension failed/i) ||
                           screen.queryByText(/error/i);
        expect(errorBanner).toBeInTheDocument();
      }, { timeout: 3000 });
    });
  });

  describe("modal close", () => {
    it("should emit close event when cancel is clicked", async () => {
      const { component } = render(ExtendTimerModal, { props: defaultProps });
      
      let closeEmitted = false;
      component.$on("close", () => {
        closeEmitted = true;
      });

      const cancelButton = screen.getByRole("button", { name: /cancelar/i });
      await fireEvent.click(cancelButton);

      expect(closeEmitted).toBe(true);
    });

    it("should close after successful extension", async () => {
      (apiPost as any).mockResolvedValue({});

      const { component } = render(ExtendTimerModal, { props: defaultProps });
      
      let successEmitted = false;
      component.$on("success", () => {
        successEmitted = true;
      });

      await waitFor(async () => {
        const minutesInput = screen.getByLabelText(/minutos a agregar/i) as HTMLInputElement;
        await fireEvent.input(minutesInput, { target: { value: "30" } });
        
        const submitButton = screen.getByRole("button", { name: /extender timer/i });
        await fireEvent.click(submitButton);
      }, { timeout: 2000 });

      await waitFor(() => {
        expect(successEmitted).toBe(true);
      }, { timeout: 2000 });
    });
  });

  describe("validation", () => {
    it("should validate minutes is positive", async () => {
      render(ExtendTimerModal, { props: defaultProps });
      
      await waitFor(async () => {
        const minutesInput = screen.getByLabelText(/minutos a agregar/i) as HTMLInputElement;
        await fireEvent.input(minutesInput, { target: { value: "0" } });
        
        const submitButton = screen.getByRole("button", { name: /extender timer/i });
        await fireEvent.click(submitButton);
      }, { timeout: 2000 });

      await waitFor(() => {
        expect(screen.getByText(/válido/i)).toBeInTheDocument();
      }, { timeout: 2000 });
    });
  });
});
