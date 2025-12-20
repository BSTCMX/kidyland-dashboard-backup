/**
 * Tests for PaymentForm component.
 * 
 * Covers payment method validation, form submit handling, and error states.
 */
import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/svelte";
import PaymentForm from "../forms/PaymentForm.svelte";

describe("PaymentForm", () => {
  const defaultProps = {
    totalCents: 10000, // $100.00
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("payment method selection", () => {
    it("should render payment method select", () => {
      render(PaymentForm, { props: defaultProps });
      
      const paymentSelect = screen.getByLabelText(/método de pago/i);
      expect(paymentSelect).toBeInTheDocument();
    });

    it("should default to cash payment", () => {
      render(PaymentForm, { props: defaultProps });
      
      const paymentSelect = screen.getByLabelText(/método de pago/i) as HTMLSelectElement;
      expect(paymentSelect.value).toBe("cash");
    });

    it("should switch to card payment", async () => {
      render(PaymentForm, { props: defaultProps });
      
      const paymentSelect = screen.getByLabelText(/método de pago/i) as HTMLSelectElement;
      await fireEvent.change(paymentSelect, { target: { value: "card" } });
      
      expect(paymentSelect.value).toBe("card");
    });
  });

  describe("cash payment", () => {
    it("should show cash received input", () => {
      render(PaymentForm, { props: defaultProps });
      
      const cashInput = screen.getByLabelText(/efectivo recibido/i);
      expect(cashInput).toBeInTheDocument();
    });

    it("should display change when cash exceeds total", async () => {
      render(PaymentForm, { props: defaultProps });
      
      const cashInput = screen.getByLabelText(/efectivo recibido/i);
      await fireEvent.input(cashInput, { target: { value: "150" } }); // $150 for $100 total
      
      await waitFor(() => {
        expect(screen.getByText(/cambio/i)).toBeInTheDocument();
      });
    });

    it("should show error when cash is insufficient", async () => {
      render(PaymentForm, { props: defaultProps });
      
      const cashInput = screen.getByLabelText(/efectivo recibido/i);
      await fireEvent.input(cashInput, { target: { value: "50" } }); // Less than $100
      
      await waitFor(() => {
        expect(screen.getByText(/faltan/i)).toBeInTheDocument();
      });
    });
  });

  describe("card payment", () => {
    it("should show card auth code input when card is selected", async () => {
      render(PaymentForm, { props: { ...defaultProps, paymentMethod: "card" } });
      
      await waitFor(() => {
        const authCodeInput = screen.getByLabelText(/código de autorización/i);
        expect(authCodeInput).toBeInTheDocument();
      });
    });

    it("should allow entering auth code", async () => {
      render(PaymentForm, { props: { ...defaultProps, paymentMethod: "card" } });
      
      const authCodeInput = screen.getByLabelText(/código de autorización/i);
      await fireEvent.input(authCodeInput, { target: { value: "AUTH123" } });
      
      expect((authCodeInput as HTMLInputElement).value).toBe("AUTH123");
    });
  });

  describe("mixed payment", () => {
    it("should show both cash and card inputs", async () => {
      render(PaymentForm, { props: { ...defaultProps, paymentMethod: "mixed" } });
      
      await waitFor(() => {
        expect(screen.getByLabelText(/efectivo recibido/i)).toBeInTheDocument();
        expect(screen.getByLabelText(/código de autorización/i)).toBeInTheDocument();
      });
    });

    it("should allow entering both cash and card details", async () => {
      render(PaymentForm, { props: { ...defaultProps, paymentMethod: "mixed" } });
      
      const cashInput = screen.getByLabelText(/efectivo recibido/i);
      await fireEvent.input(cashInput, { target: { value: "50" } }); // $50
      
      const authCodeInput = screen.getByLabelText(/código de autorización/i);
      await fireEvent.input(authCodeInput, { target: { value: "AUTH123" } });
      
      expect((cashInput as HTMLInputElement).value).toBe("50");
      expect((authCodeInput as HTMLInputElement).value).toBe("AUTH123");
    });
  });

  describe("total display", () => {
    it("should display total amount", () => {
      render(PaymentForm, { props: defaultProps });
      
      expect(screen.getByText(/\$100\.00/)).toBeInTheDocument();
    });

    it("should update when total changes", () => {
      render(PaymentForm, { props: { ...defaultProps, totalCents: 5000 } });
      
      expect(screen.getByText(/\$50\.00/)).toBeInTheDocument();
    });
  });

  describe("error display", () => {
    it("should display error message when provided", () => {
      render(PaymentForm, { props: { ...defaultProps, error: "Payment error" } });
      
      expect(screen.getByText("Payment error")).toBeInTheDocument();
    });

    it("should not display error when null", () => {
      render(PaymentForm, { props: { ...defaultProps, error: null } });
      
      expect(screen.queryByText(/error/i)).not.toBeInTheDocument();
    });
  });

  describe("change calculation", () => {
    it("should calculate and display change for cash payment", async () => {
      render(PaymentForm, { props: defaultProps });
      
      const cashInput = screen.getByLabelText(/efectivo recibido/i);
      await fireEvent.input(cashInput, { target: { value: "150" } }); // $150 for $100 total
      
      await waitFor(() => {
        expect(screen.getByText(/cambio/i)).toBeInTheDocument();
        expect(screen.getByText(/\$50\.00/)).toBeInTheDocument(); // Change
      });
    });
  });
});

