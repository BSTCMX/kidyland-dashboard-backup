/**
 * Display settings store - Vista Display config per sucursal.
 *
 * Used by:
 * - /recepcion/timers: write config (zero_alert: sound_enabled, sound_loop)
 * - /display: read config to play sound when timer reaches 0
 *
 * Clean Architecture: single source of truth from API; no hardcoded defaults.
 */
import { writable, get } from "svelte/store";
import type { Writable } from "svelte/store";
import { get as apiGet, getPublic as apiGetPublic, put } from "@kidyland/utils";
import type { DisplaySettings, ZeroAlertConfig } from "@kidyland/shared/types";

const DEFAULT_ZERO_ALERT: ZeroAlertConfig = {
  sound_enabled: false,
  sound_loop: false,
};

export interface DisplaySettingsState {
  /** Keyed by sucursal_id */
  bySucursal: Record<string, DisplaySettings>;
  loading: boolean;
  saving: boolean;
  error: string | null;
}

const initialState: DisplaySettingsState = {
  bySucursal: {},
  loading: false,
  saving: false,
  error: null,
};

export const displaySettingsStore: Writable<DisplaySettingsState> =
  writable(initialState);

/**
 * Fetch display settings for a sucursal (authenticated; for Recepción form prefill).
 */
export async function fetchDisplaySettings(
  sucursalId: string
): Promise<DisplaySettings> {
  if (!sucursalId) {
    return { zero_alert: { ...DEFAULT_ZERO_ALERT } };
  }
  displaySettingsStore.update((s) => ({ ...s, loading: true, error: null }));
  try {
    const data = await apiGet<DisplaySettings>(
      `/sucursales/${sucursalId}/display-settings`
    );
    const settings: DisplaySettings = {
      zero_alert: {
        sound_enabled: data?.zero_alert?.sound_enabled ?? false,
        sound_loop: data?.zero_alert?.sound_loop ?? false,
      },
    };
    displaySettingsStore.update((s) => ({
      ...s,
      bySucursal: { ...s.bySucursal, [sucursalId]: settings },
      loading: false,
    }));
    return settings;
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : "Error loading display settings";
    displaySettingsStore.update((s) => ({
      ...s,
      loading: false,
      error: message,
    }));
    return { zero_alert: { ...DEFAULT_ZERO_ALERT } };
  }
}

/**
 * Fetch display settings via public endpoint (no auth). For Vista Display (kiosk/TV).
 */
export async function fetchDisplaySettingsPublic(
  sucursalId: string
): Promise<DisplaySettings> {
  if (!sucursalId) {
    return { zero_alert: { ...DEFAULT_ZERO_ALERT } };
  }
  displaySettingsStore.update((s) => ({ ...s, loading: true, error: null }));
  try {
    const data = await apiGetPublic<DisplaySettings>(
      `/sucursales/${sucursalId}/display-settings/public`
    );
    const settings: DisplaySettings = {
      zero_alert: {
        sound_enabled: data?.zero_alert?.sound_enabled ?? false,
        sound_loop: data?.zero_alert?.sound_loop ?? false,
      },
    };
    displaySettingsStore.update((s) => ({
      ...s,
      bySucursal: { ...s.bySucursal, [sucursalId]: settings },
      loading: false,
    }));
    return settings;
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : "Error loading display settings";
    displaySettingsStore.update((s) => ({
      ...s,
      loading: false,
      error: message,
    }));
    return { zero_alert: { ...DEFAULT_ZERO_ALERT } };
  }
}

/**
 * Update display settings for a sucursal (from Ventana Timers).
 */
export async function updateDisplaySettings(
  sucursalId: string,
  payload: { zero_alert?: Partial<ZeroAlertConfig> }
): Promise<DisplaySettings> {
  if (!sucursalId) {
    throw new Error("sucursal_id required");
  }
  displaySettingsStore.update((s) => ({ ...s, saving: true, error: null }));
  try {
    const data = await put<DisplaySettings>(
      `/sucursales/${sucursalId}/display-settings`,
      payload
    );
    const settings: DisplaySettings = {
      zero_alert: {
        sound_enabled: data?.zero_alert?.sound_enabled ?? false,
        sound_loop: data?.zero_alert?.sound_loop ?? false,
      },
    };
    displaySettingsStore.update((s) => ({
      ...s,
      bySucursal: { ...s.bySucursal, [sucursalId]: settings },
      saving: false,
    }));
    return settings;
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : "Error saving display settings";
    displaySettingsStore.update((s) => ({
      ...s,
      saving: false,
      error: message,
    }));
    throw err;
  }
}

/**
 * Get cached display settings for a sucursal (no fetch).
 */
export function getDisplaySettings(sucursalId: string): DisplaySettings {
  const state = get(displaySettingsStore);
  const cached = state.bySucursal[sucursalId];
  if (cached) return cached;
  return { zero_alert: { ...DEFAULT_ZERO_ALERT } };
}
