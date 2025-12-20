/**
 * Tests for Input component.
 */
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/svelte";
import userEvent from "@testing-library/user-event";
import Input from "../src/Input.svelte";

describe("Input", () => {
  it("should render input with label", () => {
    render(Input, { props: { label: "Username", value: "" } });
    expect(screen.getByText("Username")).toBeInTheDocument();
  });

  it("should show required indicator", () => {
    render(Input, { props: { label: "Email", required: true, value: "" } });
    expect(screen.getByText("*")).toBeInTheDocument();
  });

  it("should display error message", () => {
    render(Input, {
      props: { label: "Email", value: "", error: "Invalid email" },
    });
    expect(screen.getByText("Invalid email")).toBeInTheDocument();
  });

  it("should update value on input", async () => {
    const user = userEvent.setup();
    const { component } = render(Input, {
      props: {
        label: "Username",
        value: "",
      },
    });

    const input = screen.getByLabelText("Username");
    await user.type(input, "testuser");

    // Value is bound internally, check that input has the value
    expect((input as HTMLInputElement).value).toBe("testuser");
  });

  it("should be disabled when disabled prop is true", () => {
    const { container } = render(Input, {
      props: { label: "Email", value: "", disabled: true },
    });
    const input = container.querySelector("input");
    expect(input?.disabled).toBe(true);
  });
});

