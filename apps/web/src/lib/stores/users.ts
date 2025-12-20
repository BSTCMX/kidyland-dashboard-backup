/**
 * Users store for user management.
 * 
 * Manages state for user list, current user, pagination, and filters.
 * Provides reactive updates for user management components.
 */
import { writable, derived, get } from "svelte/store";
import type { Writable } from "svelte/store";
import type { User } from "@kidyland/shared/types";
import { get as apiGet, post, put, del } from "@kidyland/utils";

// Types
export type RoleEnum = User["role"] | "all";

export interface UserCreate {
  username: string;
  name: string;
  role: User["role"];
  password: string;
  sucursal_id?: string | null;
}

export interface UserUpdate {
  name?: string;
  username?: string;
  role?: User["role"];
  password?: string;
  sucursal_id?: string | null;
  is_active?: boolean;
}

export interface ChangePasswordRequest {
  new_password: string;
}

export interface UsersState {
  list: User[];
  current: User | null;
  loading: boolean;
  error: string | null;
  pagination: {
    page: number;
    total: number;
    hasMore: boolean;
  };
  filters: {
    search: string;
    role: RoleEnum;
  };
}

const initialState: UsersState = {
  list: [],
  current: null,
  loading: false,
  error: null,
  pagination: {
    page: 1,
    total: 0,
    hasMore: false,
  },
  filters: {
    search: "",
    role: "all",
  },
};

export const usersStore = writable<UsersState>(initialState);

/**
 * Load users list from API.
 */
export async function fetchUsers(
  page: number = 1,
  limit: number = 20,
  activeOnly: boolean = false
): Promise<void> {
  usersStore.update((state) => ({ ...state, loading: true, error: null }));

  try {
    const skip = (page - 1) * limit;
    const users = await apiGet<User[]>(
      `/users?skip=${skip}&limit=${limit}&active_only=${activeOnly}`
    );

    usersStore.update((state) => ({
      ...state,
      list: users,
      loading: false,
      pagination: {
        page,
        total: users.length,
        hasMore: users.length === limit,
      },
    }));
  } catch (error: any) {
    usersStore.update((state) => ({
      ...state,
      loading: false,
      error: error.message || "Error loading users",
    }));
  }
}

/**
 * Alias for fetchUsers (backward compatibility).
 */
export const loadUsers = fetchUsers;

/**
 * Get a single user by ID.
 */
export async function getUserById(id: string): Promise<User | null> {
  usersStore.update((state) => ({ ...state, loading: true, error: null }));

  try {
    const user = await apiGet<User>(`/users/${id}`);
    usersStore.update((state) => ({
      ...state,
      current: user,
      loading: false,
    }));
    return user;
  } catch (error: any) {
    usersStore.update((state) => ({
      ...state,
      loading: false,
      error: error.message || "Error loading user",
    }));
    return null;
  }
}

/**
 * Create a new user.
 */
export async function createUser(userData: UserCreate): Promise<User | null> {
  usersStore.update((state) => ({ ...state, loading: true, error: null }));

  try {
    const user = await post<User>("/users", userData);
    
    // Add to list
    usersStore.update((state) => ({
      ...state,
      list: [user, ...state.list],
      loading: false,
    }));
    
    return user;
  } catch (error: any) {
    usersStore.update((state) => ({
      ...state,
      loading: false,
      error: error.message || "Error creating user",
    }));
    return null;
  }
}

/**
 * Update an existing user.
 */
export async function updateUser(
  id: string,
  userData: UserUpdate
): Promise<User | null> {
  usersStore.update((state) => ({ ...state, loading: true, error: null }));

  try {
    const user = await put<User>(`/users/${id}`, userData);
    
    // Update in list
    usersStore.update((state) => ({
      ...state,
      list: state.list.map((u) => (u.id === id ? user : u)),
      current: state.current?.id === id ? user : state.current,
      loading: false,
    }));
    
    return user;
  } catch (error: any) {
    usersStore.update((state) => ({
      ...state,
      loading: false,
      error: error.message || "Error updating user",
    }));
    return null;
  }
}

/**
 * Delete a user.
 */
export async function deleteUser(id: string): Promise<boolean> {
  usersStore.update((state) => ({ ...state, loading: true, error: null }));

  try {
    await del(`/users/${id}`);
    
    // Remove from list
    usersStore.update((state) => ({
      ...state,
      list: state.list.filter((u) => u.id !== id),
      current: state.current?.id === id ? null : state.current,
      loading: false,
    }));
    
    return true;
  } catch (error: any) {
    usersStore.update((state) => ({
      ...state,
      loading: false,
      error: error.message || "Error deleting user",
    }));
    return false;
  }
}

/**
 * Change user password (admin).
 */
export async function changePassword(
  id: string,
  passwordData: ChangePasswordRequest
): Promise<boolean> {
  usersStore.update((state) => ({ ...state, loading: true, error: null }));

  try {
    await post(`/users/${id}/change-password`, passwordData);
    usersStore.update((state) => ({ ...state, loading: false }));
    return true;
  } catch (error: any) {
    usersStore.update((state) => ({
      ...state,
      loading: false,
      error: error.message || "Error changing password",
    }));
    return false;
  }
}

/**
 * Activate a user.
 */
export async function activateUser(id: string): Promise<User | null> {
  usersStore.update((state) => ({ ...state, loading: true, error: null }));

  try {
    const user = await post<User>(`/users/${id}/activate`);
    
    // Update in list
    usersStore.update((state) => ({
      ...state,
      list: state.list.map((u) => (u.id === id ? user : u)),
      current: state.current?.id === id ? user : state.current,
      loading: false,
    }));
    
    return user;
  } catch (error: any) {
    usersStore.update((state) => ({
      ...state,
      loading: false,
      error: error.message || "Error activating user",
    }));
    return null;
  }
}

/**
 * Deactivate a user.
 */
export async function deactivateUser(id: string): Promise<User | null> {
  usersStore.update((state) => ({ ...state, loading: true, error: null }));

  try {
    const user = await post<User>(`/users/${id}/deactivate`);
    
    // Update in list
    usersStore.update((state) => ({
      ...state,
      list: state.list.map((u) => (u.id === id ? user : u)),
      current: state.current?.id === id ? user : state.current,
      loading: false,
    }));
    
    return user;
  } catch (error: any) {
    usersStore.update((state) => ({
      ...state,
      loading: false,
      error: error.message || "Error deactivating user",
    }));
    return null;
  }
}

/**
 * Set search filter.
 */
export function setSearchFilter(search: string): void {
  usersStore.update((state) => ({
    ...state,
    filters: { ...state.filters, search },
  }));
}

/**
 * Set role filter.
 */
export function setRoleFilter(role: RoleEnum): void {
  usersStore.update((state) => ({
    ...state,
    filters: { ...state.filters, role },
  }));
}

/**
 * Clear filters.
 */
export function clearFilters(): void {
  usersStore.update((state) => ({
    ...state,
    filters: { search: "", role: "all" },
  }));
}

/**
 * Reset store to initial state.
 */
export function resetUsersStore(): void {
  usersStore.set(initialState);
}

/**
 * Derived store for filtered users.
 */
export const filteredUsers = derived(usersStore, ($usersStore) => {
  let filtered = $usersStore.list;

  // Apply search filter
  if ($usersStore.filters.search) {
    const search = $usersStore.filters.search.toLowerCase();
    filtered = filtered.filter(
      (user) =>
        user.username.toLowerCase().includes(search) ||
        user.name.toLowerCase().includes(search)
    );
  }

  // Apply role filter
  if ($usersStore.filters.role !== "all") {
    filtered = filtered.filter((user) => user.role === $usersStore.filters.role);
  }

  return filtered;
});

