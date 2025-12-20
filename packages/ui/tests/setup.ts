/**
 * Vitest setup for UI components.
 */
import "@testing-library/jest-dom";
import { vi } from "vitest";

// Mock SvelteKit $app modules
vi.mock("$app/environment", () => ({
  browser: true,
  dev: false,
  building: false,
  version: "1.0.0",
}));

vi.mock("$app/navigation", () => ({
  goto: vi.fn(),
  invalidate: vi.fn(),
  preloadData: vi.fn(),
  preloadCode: vi.fn(),
}));
































