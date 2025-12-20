/**
 * Tests for API client.
 */
import { describe, it, expect, beforeEach, vi } from "vitest";
import { apiRequest, get, post, del } from "../src/api";
import { token } from "../src/auth";

// Mock fetch
global.fetch = vi.fn();

// Mock $app/navigation
vi.mock("$app/navigation", () => ({
  goto: vi.fn(),
}));

// Mock auth
vi.mock("../src/auth", async () => {
  const actual = await vi.importActual("../src/auth");
  return {
    ...actual,
    getToken: vi.fn(() => "test_token"),
    logout: vi.fn(),
  };
});

describe("API client", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("apiRequest", () => {
    it("should include Authorization header when token exists", async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        status: 200,
        headers: new Headers({ "content-type": "application/json" }),
        json: async () => ({ data: "test" }),
      });

      await apiRequest("/test");

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining("/test"),
        expect.objectContaining({
          headers: expect.objectContaining({
            Authorization: "Bearer test_token",
          }),
        })
      );
    });

    it("should handle 401 and logout", async () => {
      const { logout } = await import("../src/auth");
      
      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => ({ detail: "Unauthorized" }),
      });

      await expect(apiRequest("/test")).rejects.toThrow("Authentication required");
      expect(logout).toHaveBeenCalled();
    });

    it("should throw error on non-ok response", async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => ({ detail: "Server error" }),
      });

      await expect(apiRequest("/test")).rejects.toThrow("Server error");
    });
  });

  describe("get", () => {
    it("should make GET request", async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        status: 200,
        headers: new Headers({ "content-type": "application/json" }),
        json: async () => ({ data: "test" }),
      });

      const result = await get("/test");

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining("/test"),
        expect.objectContaining({ method: "GET" })
      );
      expect(result).toEqual({ data: "test" });
    });
  });

  describe("post", () => {
    it("should make POST request with data", async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        status: 200,
        headers: new Headers({ "content-type": "application/json" }),
        json: async () => ({ success: true }),
      });

      await post("/test", { key: "value" });

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining("/test"),
        expect.objectContaining({
          method: "POST",
          body: JSON.stringify({ key: "value" }),
        })
      );
    });
  });
});
































