/**
 * Tests for Button component.
 */
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/svelte";
import userEvent from "@testing-library/user-event";
import Button from "../src/Button.svelte";

describe("Button", () => {
  it("should render button with text", () => {
    render(Button, { props: {} }, { children: "Click me" });
    expect(screen.getByText("Click me")).toBeInTheDocument();
  });

  it("should render with primary variant by default", () => {
    const { container } = render(Button, { props: {} }, { children: "Test" });
    const button = container.querySelector("button");
    expect(button?.className).toContain("bg-blue-600");
  });

  it("should render with secondary variant", () => {
    const { container } = render(Button, {
      props: { variant: "secondary" },
    }, { children: "Test" });
    const button = container.querySelector("button");
    expect(button?.className).toContain("bg-gray-200");
  });

  it("should be disabled when disabled prop is true", () => {
    const { container } = render(Button, {
      props: { disabled: true },
    }, { children: "Test" });
    const button = container.querySelector("button");
    expect(button?.disabled).toBe(true);
    expect(button?.className).toContain("disabled:opacity-50");
  });

  it("should handle click events", async () => {
    const user = userEvent.setup();
    const handleClick = vi.fn();
    
    const { component } = render(Button, {
      props: {},
    }, { children: "Click me" });
    
    component.$on("click", handleClick);

    const button = screen.getByText("Click me");
    await user.click(button);

    expect(handleClick).toHaveBeenCalled();
  });
});

