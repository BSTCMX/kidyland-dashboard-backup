/**
 * Tests for auth store.
 * 
 * Covers login, logout, permissions, and JWT lifecycle.
 */
import { describe, it, expect, beforeEach, vi } from "vitest";
import { get } from "svelte/store";
import { browser } from "$app/environment";
import { goto } from "$app/navigation";
import { user, token, login, logout, getToken, getUser, hasRole, hasAnyRole, getRoleRoute, hasAccess, canEdit } from "../auth";

// Mock dependencies
vi.mock("$app/environment", () => ({
  browser: true,
}));

vi.mock("$app/navigation", () => ({
  goto: vi.fn(),
}));

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};

Object.defineProperty(window, "localStorage", {
  value: localStorageMock,
});

// Mock fetch
global.fetch = vi.fn();

describe("auth store", () => {
  beforeEach(() => {
    // Reset stores
    user.set(null);
    token.set(null);
    
    // Clear mocks
    vi.clearAllMocks();
    localStorageMock.getItem.mockReturnValue(null);
  });

  describe("initialization", () => {
    it("should initialize with null user and token", () => {
      expect(get(user)).toBeNull();
      expect(get(token)).toBeNull();
    });

    it("should sync token to localStorage when set", () => {
      token.set("test-token");
      expect(localStorageMock.setItem).toHaveBeenCalledWith("auth_token", "test-token");
    });

    it("should sync user to localStorage when set", () => {
      const testUser = { id: "1", username: "test", role: "recepcion" };
      user.set(testUser);
      expect(localStorageMock.setItem).toHaveBeenCalledWith("auth_user", JSON.stringify(testUser));
    });

    it("should remove token from localStorage when cleared", () => {
      token.set("test-token");
      token.set(null);
      expect(localStorageMock.removeItem).toHaveBeenCalledWith("auth_token");
    });

    it("should remove user from localStorage when cleared", () => {
      user.set({ id: "1", username: "test", role: "recepcion" });
      user.set(null);
      expect(localStorageMock.removeItem).toHaveBeenCalledWith("auth_user");
    });
  });

  describe("login", () => {
    it("should successfully login with valid credentials", async () => {
      const mockUser = {
        id: "1",
        username: "testuser",
        role: "recepcion",
        sucursal_id: "suc-1",
      };
      
      const mockResponse = {
        access_token: "test-token",
        token_type: "bearer",
        user: mockUser,
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockResponse,
      });

      await login("testuser", "password123");

      expect(get(token)).toBe("test-token");
      expect(get(user)).toEqual(mockUser);
      expect(localStorageMock.setItem).toHaveBeenCalledWith("auth_token", "test-token");
      expect(localStorageMock.setItem).toHaveBeenCalledWith("auth_user", JSON.stringify(mockUser));
    });

    it("should throw error on invalid credentials", async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => ({ detail: "Invalid credentials" }),
      });

      await expect(login("testuser", "wrongpass")).rejects.toThrow("Invalid credentials");
      expect(get(token)).toBeNull();
      expect(get(user)).toBeNull();
    });

    it("should handle 401 and logout", async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => ({ detail: "Unauthorized" }),
      });

      await expect(login("testuser", "wrongpass")).rejects.toThrow();
      expect(goto).toHaveBeenCalledWith("/");
    });

    it("should redirect to role route after successful login", async () => {
      const mockUser = {
        id: "1",
        username: "testuser",
        role: "recepcion",
        sucursal_id: "suc-1",
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({
          access_token: "test-token",
          user: mockUser,
        }),
      });

      await login("testuser", "password123");

      expect(goto).toHaveBeenCalled();
    });
  });

  describe("logout", () => {
    it("should clear user and token", () => {
      user.set({ id: "1", username: "test", role: "recepcion" });
      token.set("test-token");

      logout();

      expect(get(user)).toBeNull();
      expect(get(token)).toBeNull();
      expect(localStorageMock.removeItem).toHaveBeenCalledWith("auth_token");
      expect(localStorageMock.removeItem).toHaveBeenCalledWith("auth_user");
      expect(goto).toHaveBeenCalledWith("/");
    });
  });

  describe("getToken", () => {
    it("should return current token", () => {
      token.set("test-token");
      expect(getToken()).toBe("test-token");
    });

    it("should return null when no token", () => {
      token.set(null);
      expect(getToken()).toBeNull();
    });
  });

  describe("getUser", () => {
    it("should return current user", () => {
      const testUser = { id: "1", username: "test", role: "recepcion" };
      user.set(testUser);
      expect(getUser()).toEqual(testUser);
    });

    it("should return null when no user", () => {
      user.set(null);
      expect(getUser()).toBeNull();
    });
  });

  describe("hasRole", () => {
    it("should return true when user has the role", () => {
      user.set({ id: "1", username: "test", role: "recepcion" });
      expect(hasRole("recepcion")).toBe(true);
    });

    it("should return false when user has different role", () => {
      user.set({ id: "1", username: "test", role: "recepcion" });
      expect(hasRole("super_admin")).toBe(false);
    });

    it("should return false when no user", () => {
      user.set(null);
      expect(hasRole("recepcion")).toBe(false);
    });
  });

  describe("hasAnyRole", () => {
    it("should return true when user has one of the roles", () => {
      user.set({ id: "1", username: "test", role: "recepcion" });
      expect(hasAnyRole(["recepcion", "kidibar"])).toBe(true);
    });

    it("should return false when user has none of the roles", () => {
      user.set({ id: "1", username: "test", role: "recepcion" });
      expect(hasAnyRole(["super_admin", "admin_viewer"])).toBe(false);
    });

    it("should return false when no user", () => {
      user.set(null);
      expect(hasAnyRole(["recepcion"])).toBe(false);
    });
  });

  describe("getRoleRoute", () => {
    it("should return route for user role", () => {
      user.set({ id: "1", username: "test", role: "recepcion" });
      expect(getRoleRoute()).toBe("/recepcion");
    });

    it("should return null when no user", () => {
      user.set(null);
      expect(getRoleRoute()).toBeNull();
    });
  });

  describe("hasAccess", () => {
    it("should return true for allowed route", () => {
      user.set({ id: "1", username: "test", role: "recepcion" });
      expect(hasAccess("/recepcion")).toBe(true);
    });

    it("should return false for restricted route", () => {
      user.set({ id: "1", username: "test", role: "recepcion" });
      expect(hasAccess("/admin")).toBe(false);
    });

    it("should return false when no user", () => {
      user.set(null);
      expect(hasAccess("/recepcion")).toBe(false);
    });

    it("should check route prefixes", () => {
      user.set({ id: "1", username: "test", role: "recepcion" });
      expect(hasAccess("/recepcion/ventas")).toBe(true);
    });
  });

  describe("canEdit", () => {
    it("should return true when user can edit module", () => {
      user.set({ id: "1", username: "test", role: "recepcion" });
      expect(canEdit("recepcion")).toBe(true);
    });

    it("should return false when user cannot edit module", () => {
      user.set({ id: "1", username: "test", role: "recepcion" });
      expect(canEdit("admin")).toBe(false);
    });

    it("should return false when no user", () => {
      user.set(null);
      expect(canEdit("recepcion")).toBe(false);
    });

    it("should allow super_admin to edit all modules", () => {
      user.set({ id: "1", username: "admin", role: "super_admin" });
      expect(canEdit("admin")).toBe(true);
      expect(canEdit("recepcion")).toBe(true);
      expect(canEdit("kidibar")).toBe(true);
    });
  });
});

