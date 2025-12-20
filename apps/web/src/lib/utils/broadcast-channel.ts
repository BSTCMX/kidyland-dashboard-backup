/**
 * BroadcastChannel utility for cross-tab synchronization.
 * 
 * Provides a simple API to synchronize stores between browser tabs/windows.
 * Uses the BroadcastChannel API which is supported in modern browsers.
 * 
 * Usage:
 *   import { createBroadcastChannel } from '$lib/utils/broadcast-channel';
 *   const channel = createBroadcastChannel('services-sync');
 *   channel.on('service-created', (data) => { ... });
 *   channel.emit('service-created', serviceData);
 */

export type BroadcastEventType = 
  | 'service-created'
  | 'service-updated'
  | 'service-deleted'
  | 'service-refresh'
  | 'product-created'
  | 'product-updated'
  | 'product-deleted'
  | 'product-refresh'
  | 'stock-alerts-updated';

export interface BroadcastEvent {
  type: BroadcastEventType;
  data: any;
  timestamp: number;
}

/**
 * Check if BroadcastChannel is supported in the current browser.
 */
export function isBroadcastChannelSupported(): boolean {
  return typeof BroadcastChannel !== 'undefined';
}

/**
 * Create a BroadcastChannel for cross-tab synchronization.
 * 
 * @param channelName - Name of the channel (must be same across tabs)
 * @returns BroadcastChannel instance with helper methods
 */
export function createBroadcastChannel(channelName: string) {
  if (!isBroadcastChannelSupported()) {
    // Return a no-op implementation if not supported
    return {
      on: () => {},
      emit: () => {},
      close: () => {},
      isSupported: false,
    };
  }

  const channel = new BroadcastChannel(channelName);
  const listeners: Map<BroadcastEventType, Set<(data: any) => void>> = new Map();

  // Listen to messages from other tabs
  channel.addEventListener('message', (event: MessageEvent<BroadcastEvent>) => {
    const { type, data } = event.data;
    const typeListeners = listeners.get(type);
    if (typeListeners) {
      typeListeners.forEach((listener) => {
        try {
          listener(data);
        } catch (error) {
          console.error(`[BroadcastChannel] Error in listener for ${type}:`, error);
        }
      });
    }
  });

  return {
    /**
     * Subscribe to a specific event type.
     * 
     * @param type - Event type to listen for
     * @param listener - Callback function to execute when event is received
     * @returns Unsubscribe function
     */
    on(type: BroadcastEventType, listener: (data: any) => void): () => void {
      if (!listeners.has(type)) {
        listeners.set(type, new Set());
      }
      listeners.get(type)!.add(listener);

      // Return unsubscribe function
      return () => {
        const typeListeners = listeners.get(type);
        if (typeListeners) {
          typeListeners.delete(listener);
          if (typeListeners.size === 0) {
            listeners.delete(type);
          }
        }
      };
    },

    /**
     * Emit an event to all other tabs/windows.
     * 
     * @param type - Event type
     * @param data - Data to send
     */
    emit(type: BroadcastEventType, data: any): void {
      const event: BroadcastEvent = {
        type,
        data,
        timestamp: Date.now(),
      };
      channel.postMessage(event);
    },

    /**
     * Close the channel and clean up.
     */
    close(): void {
      listeners.clear();
      channel.close();
    },

    /**
     * Check if BroadcastChannel is supported.
     */
    isSupported: true,
  };
}

/**
 * Create a singleton BroadcastChannel for services synchronization.
 * This ensures all parts of the app use the same channel instance.
 */
let servicesChannelInstance: ReturnType<typeof createBroadcastChannel> | null = null;

export function getServicesBroadcastChannel() {
  if (!servicesChannelInstance) {
    servicesChannelInstance = createBroadcastChannel('kidyland-services-sync');
  }
  return servicesChannelInstance;
}

/**
 * Create a singleton BroadcastChannel for products synchronization.
 * This ensures all parts of the app use the same channel instance.
 */
let productsChannelInstance: ReturnType<typeof createBroadcastChannel> | null = null;

export function getProductsBroadcastChannel() {
  if (!productsChannelInstance) {
    productsChannelInstance = createBroadcastChannel('kidyland-products-sync');
  }
  return productsChannelInstance;
}


