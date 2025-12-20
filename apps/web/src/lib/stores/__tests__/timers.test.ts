/**
 * Tests for timers store.
 * 
 * Covers WebSocket connections, alerts, and timer management.
 */
import { describe, it, expect, beforeEach, vi } from "vitest";
import { get } from "svelte/store";
import {
  timersStore,
  fetchActiveTimers,
  connectTimerWebSocket,
  disconnectTimerWebSocket,
} from "../timers";
import * as notificationsStore from "../notifications";

// Mock dependencies
vi.mock("@kidyland/utils", () => ({
  get: vi.fn(),
  createTimerWebSocket: vi.fn(),
}));

vi.mock("../notifications", () => ({
  notify: {
    warning: vi.fn(),
  },
}));

import { get as apiGet, createTimerWebSocket } from "@kidyland/utils";
import { notify } from "../notifications";

describe("timers store", () => {
  beforeEach(() => {
    timersStore.set({
      list: [],
      loading: false,
      error: null,
      wsConnected: false,
    });
    vi.clearAllMocks();
  });

  describe("initial state", () => {
    it("should have initial state", () => {
      const state = get(timersStore);
      expect(state.list).toEqual([]);
      expect(state.loading).toBe(false);
      expect(state.error).toBeNull();
      expect(state.wsConnected).toBe(false);
    });
  });

  describe("fetchActiveTimers", () => {
    it("should fetch and transform timers successfully", async () => {
      const mockApiResponse = [
        {
          timer_id: "timer-1",
          sale_id: "sale-1",
          child_name: "Test Child",
          child_age: 5,
          time_left: 30, // minutes
          status: "active",
          start_at: "2024-01-01T10:00:00Z",
          end_at: "2024-01-01T11:00:00Z",
        },
        {
          timer_id: "timer-2",
          sale_id: "sale-2",
          time_left: 15,
          status: "active",
          start_at: "2024-01-01T10:30:00Z",
          end_at: "2024-01-01T11:00:00Z",
        },
      ];

      vi.mocked(apiGet).mockResolvedValue(mockApiResponse);

      await fetchActiveTimers("sucursal-1");

      const state = get(timersStore);
      expect(state.loading).toBe(false);
      expect(state.error).toBeNull();
      expect(state.list).toHaveLength(2);
      expect(state.list[0].id).toBe("timer-1");
      expect(state.list[0].time_left_seconds).toBe(1800); // 30 minutes * 60
      expect(state.list[0].child_name).toBe("Test Child");
      expect(state.list[0].child_age).toBe(5);
    });

    it("should set loading state during fetch", async () => {
      let resolveApi: (value: any) => void;
      const apiPromise = new Promise((resolve) => {
        resolveApi = resolve;
      });

      vi.mocked(apiGet).mockReturnValue(apiPromise as any);

      const fetchPromise = fetchActiveTimers("sucursal-1");

      // Check loading is true
      expect(get(timersStore).loading).toBe(true);

      // Resolve the API call
      resolveApi!([]);
      await fetchPromise;

      // Check loading is false after completion
      expect(get(timersStore).loading).toBe(false);
    });

    it("should handle errors and update store", async () => {
      vi.mocked(apiGet).mockRejectedValue(new Error("API Error"));

      await fetchActiveTimers("sucursal-1");

      const state = get(timersStore);
      expect(state.error).toBe("API Error");
      expect(state.loading).toBe(false);
    });

    it("should transform time_left from minutes to seconds", async () => {
      vi.mocked(apiGet).mockResolvedValue([
        {
          timer_id: "timer-1",
          time_left: 5, // 5 minutes
          status: "active",
          start_at: "2024-01-01T10:00:00Z",
          end_at: "2024-01-01T10:05:00Z",
        },
      ]);

      await fetchActiveTimers("sucursal-1");

      const state = get(timersStore);
      expect(state.list[0].time_left_seconds).toBe(300); // 5 * 60
    });
  });

  describe("connectTimerWebSocket", () => {
    let mockWebSocket: any;

    beforeEach(() => {
      mockWebSocket = {
        connect: vi.fn(),
        disconnect: vi.fn(),
      };
      vi.mocked(createTimerWebSocket).mockReturnValue(mockWebSocket);
    });

    it("should connect WebSocket and update store", () => {
      connectTimerWebSocket("sucursal-1", "test-token");

      expect(createTimerWebSocket).toHaveBeenCalledWith(
        "sucursal-1",
        expect.objectContaining({
          onMessage: expect.any(Function),
          onError: expect.any(Function),
          onClose: expect.any(Function),
        })
      );
      expect(mockWebSocket.connect).toHaveBeenCalled();
      expect(get(timersStore).wsConnected).toBe(true);
    });

    it("should disconnect existing connection before connecting new one", () => {
      // First connection
      connectTimerWebSocket("sucursal-1", "token-1");
      const firstWs = vi.mocked(createTimerWebSocket).mock.results[0].value;

      // Second connection
      connectTimerWebSocket("sucursal-2", "token-2");

      expect(firstWs.disconnect).toHaveBeenCalled();
    });

    it("should handle timers_update message", () => {
      connectTimerWebSocket("sucursal-1", "test-token");

      const onMessage = vi.mocked(createTimerWebSocket).mock.calls[0][1].onMessage;
      
      const mockTimers = [
        { timer_id: "timer-1", time_left: 30, status: "active" },
        { timer_id: "timer-2", time_left: 15, status: "active" },
      ];

      onMessage({
        type: "timers_update",
        timers: mockTimers,
      });

      const state = get(timersStore);
      expect(state.list).toHaveLength(2);
      expect(state.wsConnected).toBe(true);
    });

    it("should handle timer_alert message and show notifications", () => {
      connectTimerWebSocket("sucursal-1", "test-token");

      const onMessage = vi.mocked(createTimerWebSocket).mock.calls[0][1].onMessage;
      
      const mockAlertTimers = [
        {
          timer_id: "timer-1",
          time_left: 3, // 3 minutes - should trigger 5 min alert
          status: "alert",
          child_name: "Test Child",
        },
      ];

      onMessage({
        type: "timer_alert",
        timers: mockAlertTimers,
      });

      // Check that notify.warning was called (may be called with different messages)
      expect(notify.warning).toHaveBeenCalled();
      const callArgs = vi.mocked(notify.warning).mock.calls[0];
      expect(callArgs[0]).toContain("Timer termina");
      expect(callArgs[1]).toContain("Test Child");

      const state = get(timersStore);
      expect(state.list).toHaveLength(1);
    });

    it("should show different alert messages based on time_left", () => {
      // Disconnect any existing connection first
      disconnectTimerWebSocket();
      vi.clearAllMocks();
      
      connectTimerWebSocket("sucursal-1", "test-token");
      const onMessage = vi.mocked(createTimerWebSocket).mock.calls[0][1].onMessage;

      // Test 5 minutes alert
      onMessage({
        type: "timer_alert",
        timers: [{ timer_id: "timer-1", time_left: 3, status: "alert" }],
      });
      expect(notify.warning).toHaveBeenCalledWith(
        expect.stringContaining("5 minutos"),
        expect.any(String),
        8000
      );

      // Disconnect and reconnect to reset previousAlertTimers
      disconnectTimerWebSocket();
      vi.clearAllMocks();
      connectTimerWebSocket("sucursal-1", "test-token");
      const onMessage2 = vi.mocked(createTimerWebSocket).mock.calls[0][1].onMessage;

      // Test 10 minutes alert
      onMessage2({
        type: "timer_alert",
        timers: [{ timer_id: "timer-2", time_left: 8, status: "alert" }],
      });
      expect(notify.warning).toHaveBeenCalledWith(
        expect.stringContaining("10 minutos"),
        expect.any(String),
        8000
      );

      // Disconnect and reconnect again
      disconnectTimerWebSocket();
      vi.clearAllMocks();
      connectTimerWebSocket("sucursal-1", "test-token");
      const onMessage3 = vi.mocked(createTimerWebSocket).mock.calls[0][1].onMessage;

      // Test 15 minutes alert
      onMessage3({
        type: "timer_alert",
        timers: [{ timer_id: "timer-3", time_left: 12, status: "alert" }],
      });
      expect(notify.warning).toHaveBeenCalledWith(
        expect.stringContaining("15 minutos"),
        expect.any(String),
        8000
      );
    });

    it("should only show notification for new alerts", () => {
      // Disconnect any existing connection first
      disconnectTimerWebSocket();
      vi.clearAllMocks();
      
      connectTimerWebSocket("sucursal-1", "test-token");
      const onMessage = vi.mocked(createTimerWebSocket).mock.calls[0][1].onMessage;

      // First alert - new timer entering alert state
      onMessage({
        type: "timer_alert",
        timers: [{ timer_id: "timer-1", time_left: 3, status: "alert" }],
      });

      // Should show notification for new alert
      expect(notify.warning).toHaveBeenCalled();
      const firstCallCount = vi.mocked(notify.warning).mock.calls.length;
      expect(firstCallCount).toBeGreaterThan(0);
      
      // Same alert again (timer already in alert state, should not trigger new notification)
      onMessage({
        type: "timer_alert",
        timers: [{ timer_id: "timer-1", time_left: 2, status: "alert" }],
      });

      // Should not have additional calls (same timer already alerted)
      expect(vi.mocked(notify.warning).mock.calls.length).toBe(firstCallCount);
    });

    it("should handle WebSocket errors", () => {
      connectTimerWebSocket("sucursal-1", "test-token");
      const onError = vi.mocked(createTimerWebSocket).mock.calls[0][1].onError;

      onError(new Error("WebSocket error"));

      const state = get(timersStore);
      expect(state.error).toBe("WebSocket connection error");
      expect(state.wsConnected).toBe(false);
    });

    it("should handle WebSocket close", () => {
      connectTimerWebSocket("sucursal-1", "test-token");
      const onClose = vi.mocked(createTimerWebSocket).mock.calls[0][1].onClose;

      onClose();

      const state = get(timersStore);
      expect(state.wsConnected).toBe(false);
    });

    it("should handle connection errors gracefully", () => {
      vi.mocked(createTimerWebSocket).mockImplementation(() => {
        throw new Error("Connection failed");
      });

      connectTimerWebSocket("sucursal-1", "test-token");

      const state = get(timersStore);
      expect(state.error).toBe("Connection failed");
      expect(state.wsConnected).toBe(false);
    });
  });

  describe("disconnectTimerWebSocket", () => {
    it("should disconnect WebSocket and update store", () => {
      const mockWebSocket = {
        connect: vi.fn(),
        disconnect: vi.fn(),
      };
      vi.mocked(createTimerWebSocket).mockReturnValue(mockWebSocket);

      connectTimerWebSocket("sucursal-1", "test-token");
      disconnectTimerWebSocket();

      expect(mockWebSocket.disconnect).toHaveBeenCalled();
      expect(get(timersStore).wsConnected).toBe(false);
    });

    it("should handle disconnect when no connection exists", () => {
      // Should not throw
      expect(() => disconnectTimerWebSocket()).not.toThrow();
    });
  });
});

