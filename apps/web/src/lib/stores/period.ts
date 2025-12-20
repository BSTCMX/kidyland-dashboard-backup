/**
 * Period store for managing selected time period in dashboard.
 * 
 * Provides reactive state for period selection (7, 15, 30 days, etc.)
 * and derived functions to calculate date ranges.
 * 
 * Follows Clean Architecture principles:
 * - Single source of truth for period state
 * - Reactive updates across components
 * - Easy to test and mock
 */
import { writable, derived, get } from "svelte/store";
import type { Writable, Readable } from "svelte/store";

/**
 * Default period options in days.
 */
export const PERIOD_OPTIONS = [7, 15, 30, 60, 90] as const;

export type PeriodOption = typeof PERIOD_OPTIONS[number];

/**
 * Period state interface.
 */
export interface PeriodState {
  selectedDays: number;
  startDate: string | null;
  endDate: string | null;
}

/**
 * Initial state: default to 30 days.
 */
const initialState: PeriodState = {
  selectedDays: 30,
  startDate: null,
  endDate: null,
};

/**
 * Main period store.
 */
export const periodStore: Writable<PeriodState> = writable(initialState);

/**
 * Calculate date range based on selected days.
 * 
 * @param days - Number of days to look back
 * @returns Object with start_date and end_date in ISO format
 */
export function calculateDateRange(days: number): { startDate: string; endDate: string } {
  const endDate = new Date();
  endDate.setHours(23, 59, 59, 999); // End of today
  
  const startDate = new Date();
  startDate.setDate(startDate.getDate() - days);
  startDate.setHours(0, 0, 0, 0); // Start of day
  
  return {
    startDate: startDate.toISOString().split('T')[0],
    endDate: endDate.toISOString().split('T')[0],
  };
}

/**
 * Update selected period and calculate date range.
 * 
 * @param days - Number of days to look back
 */
export function setPeriod(days: number): void {
  const { startDate, endDate } = calculateDateRange(days);
  
  periodStore.update((state) => ({
    ...state,
    selectedDays: days,
    startDate,
    endDate,
  }));
}

/**
 * Get current period state.
 */
export function getPeriodState(): PeriodState {
  return get(periodStore);
}

/**
 * Derived store for start date (reactive).
 */
export const startDate: Readable<string | null> = derived(
  periodStore,
  ($periodStore) => $periodStore.startDate
);

/**
 * Derived store for end date (reactive).
 */
export const endDate: Readable<string | null> = derived(
  periodStore,
  ($periodStore) => $periodStore.endDate
);

/**
 * Derived store for selected days (reactive).
 */
export const selectedDays: Readable<number> = derived(
  periodStore,
  ($periodStore) => $periodStore.selectedDays
);

/**
 * Initialize period store with default value.
 * Call this on app mount or dashboard load.
 */
export function initializePeriod(defaultDays: number = 30): void {
  setPeriod(defaultDays);
}




