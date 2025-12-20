/**
 * Customers Store - State management for customer reports and analytics.
 */
import { writable } from 'svelte/store';
import { get } from '@kidyland/utils/api';

// Types
export interface Customer {
  customer_name: string;
  module: 'recepcion' | 'kidibar';
  child_age?: number | null;
  visit_count: number;
  total_revenue_cents: number;
  last_visit_date: string | null;
  first_visit_date: string | null;
}

export interface CustomersListResponse {
  customers: Customer[];
  pagination: {
    skip: number;
    limit: number;
    total: number;
    has_more: boolean;
  };
}

export interface CustomersState {
  list: Customer[];
  loading: boolean;
  error: string | null;
  pagination: {
    page: number;
    pageSize: number;
    total: number;
    hasMore: boolean;
  };
  filters: {
    sucursalId: string | null;
    startDate: string | null;
    endDate: string | null;
    module: string | null;
    sortBy: 'revenue' | 'visits' | 'recency';
    order: 'asc' | 'desc';
  };
}

const initialState: CustomersState = {
  list: [],
  loading: false,
  error: null,
  pagination: {
    page: 1,
    pageSize: 25,
    total: 0,
    hasMore: false,
  },
  filters: {
    sucursalId: null,
    startDate: null,
    endDate: null,
    module: null,
    sortBy: 'revenue',
    order: 'desc',
  },
};

export const customersStore = writable<CustomersState>(initialState);

/**
 * Fetch customers list with pagination and filters.
 */
export async function fetchCustomersList(
  sucursalId?: string | null,
  startDate?: string | null,
  endDate?: string | null,
  module?: string | null,
  page: number = 1,
  pageSize: number = 25,
  sortBy: 'revenue' | 'visits' | 'recency' = 'revenue',
  order: 'asc' | 'desc' = 'desc'
): Promise<void> {
  customersStore.update((state) => ({ ...state, loading: true, error: null }));

  try {
    const skip = (page - 1) * pageSize;
    const params = new URLSearchParams();
    
    if (sucursalId) params.append('sucursal_id', sucursalId);
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    if (module && module !== 'all') params.append('module', module);
    params.append('skip', skip.toString());
    params.append('limit', pageSize.toString());
    params.append('sort_by', sortBy);
    params.append('order', order);

    const response = await get<CustomersListResponse>(`/reports/customers/list?${params.toString()}`);
    
    customersStore.update((state) => ({
      ...state,
      list: response.customers,
      loading: false,
      pagination: {
        page,
        pageSize,
        total: response.pagination.total,
        hasMore: response.pagination.has_more,
      },
      filters: {
        sucursalId: sucursalId || null,
        startDate: startDate || null,
        endDate: endDate || null,
        module: module || null,
        sortBy,
        order,
      },
    }));
  } catch (error: any) {
    customersStore.update((state) => ({
      ...state,
      error: error.message || 'Error loading customers',
      loading: false,
    }));
  }
}

/**
 * Set page size for pagination.
 * Resets to page 1 when page size changes.
 */
export function setCustomersPageSize(pageSize: number): void {
  customersStore.update((state) => ({
    ...state,
    pagination: {
      ...state.pagination,
      pageSize,
      page: 1,
    },
  }));
}

/**
 * Go to next page.
 */
export function nextCustomersPage(): void {
  customersStore.update((state) => {
    if (state.pagination.hasMore) {
      return {
        ...state,
        pagination: {
          ...state.pagination,
          page: state.pagination.page + 1,
        },
      };
    }
    return state;
  });
}

/**
 * Go to previous page.
 */
export function previousCustomersPage(): void {
  customersStore.update((state) => {
    if (state.pagination.page > 1) {
      return {
        ...state,
        pagination: {
          ...state.pagination,
          page: state.pagination.page - 1,
        },
      };
    }
    return state;
  });
}

/**
 * Go to specific page.
 */
export function goToCustomersPage(page: number): void {
  customersStore.update((state) => ({
    ...state,
    pagination: {
      ...state.pagination,
      page: Math.max(1, page),
    },
  }));
}

/**
 * Update filters and reset to page 1.
 */
export function updateCustomersFilters(
  filters: Partial<CustomersState['filters']>
): void {
  customersStore.update((state) => ({
    ...state,
    filters: {
      ...state.filters,
      ...filters,
    },
    pagination: {
      ...state.pagination,
      page: 1,
    },
  }));
}

