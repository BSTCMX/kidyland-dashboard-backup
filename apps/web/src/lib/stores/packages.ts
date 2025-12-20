/**
 * Packages store - Simple store for package data.
 * 
 * Note: Most functionality is in packages-admin.ts.
 * This file may be used for simpler package operations or as a legacy store.
 */
import { writable } from "svelte/store";
import type { Writable } from "svelte/store";
import type { Package } from "@kidyland/shared/types";

export interface PackagesState {
  list: Package[];
  loading: boolean;
  error: string | null;
}

const initialState: PackagesState = {
  list: [],
  loading: false,
  error: null,
};

export const packagesStore: Writable<PackagesState> = writable(initialState);
