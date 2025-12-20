/**
 * Notifications store - Global notification system.
 * 
 * Manages toast notifications, alerts, and user feedback messages.
 * Supports different notification types: success, error, warning, info.
 */
import { writable } from "svelte/store";
import type { Writable } from "svelte/store";

export type NotificationType = "success" | "error" | "warning" | "info";

export interface Notification {
  id: string;
  type: NotificationType;
  title: string;
  message?: string;
  duration?: number; // Auto-dismiss after milliseconds (0 = no auto-dismiss)
  persistent?: boolean; // If true, won't auto-dismiss
  action?: {
    label: string;
    handler: () => void;
  };
}

export interface NotificationsState {
  list: Notification[];
}

const initialState: NotificationsState = {
  list: [],
};

export const notificationsStore: Writable<NotificationsState> = writable(initialState);

/**
 * Generate unique ID for notification.
 */
function generateId(): string {
  return `notification-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Add a new notification.
 */
export function addNotification(notification: Omit<Notification, "id">): string {
  const id = generateId();
  const newNotification: Notification = {
    id,
    duration: 5000, // Default 5 seconds
    persistent: false,
    ...notification,
  };

  notificationsStore.update((state) => ({
    ...state,
    list: [...state.list, newNotification],
  }));

  // Auto-dismiss if duration is set and not persistent
  if (newNotification.duration && newNotification.duration > 0 && !newNotification.persistent) {
    setTimeout(() => {
      removeNotification(id);
    }, newNotification.duration);
  }

  return id;
}

/**
 * Remove a notification by ID.
 */
export function removeNotification(id: string): void {
  notificationsStore.update((state) => ({
    ...state,
    list: state.list.filter((n) => n.id !== id),
  }));
}

/**
 * Clear all notifications.
 */
export function clearNotifications(): void {
  notificationsStore.update((state) => ({
    ...state,
    list: [],
  }));
}

/**
 * Helper functions for common notification types.
 */
export const notify = {
  success: (title: string, message?: string, duration?: number) => {
    return addNotification({
      type: "success",
      title,
      message,
      duration: duration ?? 5000,
    });
  },

  error: (title: string, message?: string, duration?: number) => {
    return addNotification({
      type: "error",
      title,
      message,
      duration: duration ?? 7000, // Errors stay longer
    });
  },

  warning: (title: string, message?: string, duration?: number) => {
    return addNotification({
      type: "warning",
      title,
      message,
      duration: duration ?? 6000,
    });
  },

  info: (title: string, message?: string, duration?: number) => {
    return addNotification({
      type: "info",
      title,
      message,
      duration: duration ?? 5000,
    });
  },
};





























