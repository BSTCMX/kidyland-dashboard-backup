/**
 * Tests for auth store and utilities.
 */
import { describe, it, expect, beforeEach, vi } from "vitest";
import { get } from "svelte/store";
import { login, logout, user, token, hasRole, hasAnyRole } from "../src/auth";
import type { User as UserType } from "@kidyland/shared/types";

// Mock fetch
global.fetch = vi.fn();

// Mock $app/environment
vi.mock("$app/environment", () => ({
  browser: true,
}));

// Mock $app/navigation
vi.mock("$app/navigation", () => ({
  goto: vi.fn(),
}));

describe("auth store", () => {
  beforeEach(() => {
    // Reset stores
    user.set(null);
    token.set(null);
    vi.clearAllMocks();
  });

  describe("login", () => {
    it("should login successfully with valid credentials", async () => {
      const mockUser: UserType = {
        id: "123",
        username: "testuser",
        name: "Test User",
        role: "recepcion",
        sucursal_id: null,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        last_login: null,
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({
          access_token: "test_token",
          token_type: "bearer",
          user: mockUser,
        }),
      });

      await login("testuser", "password123");

      expect(get(token)).toBe("test_token");
      expect(get(user)).toEqual(mockUser);
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining("/auth/login"),
        expect.objectContaining({
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ username: "testuser", password: "password123" }),
        })
      );
    });

    it("should handle 401 error and logout", async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => ({ detail: "Invalid credentials" }),
      });

      await expect(login("testuser", "wrongpass")).rejects.toThrow();

      expect(get(token)).toBeNull();
      expect(get(user)).toBeNull();
    });

    it("should throw error on login failure", async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => ({ detail: "Server error" }),
      });

      await expect(login("testuser", "password")).rejects.toThrow("Server error");
    });
  });

  describe("logout", () => {
    it("should clear user and token", () => {
      user.set({
        id: "123",
        username: "testuser",
        name: "Test User",
        role: "recepcion",
        sucursal_id: null,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        last_login: null,
      });
      token.set("test_token");

      logout();

      expect(get(user)).toBeNull();
      expect(get(token)).toBeNull();
    });
  });

  describe("hasRole", () => {
    it("should return true if user has the role", () => {
      user.set({
        id: "123",
        username: "testuser",
        name: "Test User",
        role: "recepcion",
        sucursal_id: null,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        last_login: null,
      });

      expect(hasRole("recepcion")).toBe(true);
      expect(hasRole("super_admin")).toBe(false);
    });

    it("should return false if no user", () => {
      user.set(null);
      expect(hasRole("recepcion")).toBe(false);
    });
  });

  describe("hasAnyRole", () => {
    it("should return true if user has any of the roles", () => {
      user.set({
        id: "123",
        username: "testuser",
        name: "Test User",
        role: "recepcion",
        sucursal_id: null,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        last_login: null,
      });

      expect(hasAnyRole(["recepcion", "super_admin"])).toBe(true);
      expect(hasAnyRole(["super_admin", "admin_viewer"])).toBe(false);
    });
  });
});
































