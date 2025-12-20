<script lang="ts">
  /**
   * CustomersList - Paginated list of customers with filters and sorting.
   */
  import { onMount } from 'svelte';
  import { customersStore, fetchCustomersList, updateCustomersFilters, setCustomersPageSize, nextCustomersPage, previousCustomersPage, goToCustomersPage } from '$lib/stores/customers';
  import { formatPrice } from '$lib/stores/reports';
  import LoadingSpinner from '$lib/components/admin/LoadingSpinner.svelte';
  import ErrorBanner from '$lib/components/admin/ErrorBanner.svelte';
  import PeriodSelector from '$lib/components/admin/reports/sales/PeriodSelector.svelte';
  import SucursalSelector from '$lib/components/admin/SucursalSelector.svelte';
  import { ChevronLeft, ChevronRight, ArrowUpDown } from 'lucide-svelte';

  export let sucursalId: string | null = null;
  export let startDate: string | null = null;
  export let endDate: string | null = null;

  // Local filters with override capability
  // If local filters are set, they override global filters
  let localStartDate: string | null = null;
  let localEndDate: string | null = null;
  let hasLocalDateOverride = false;

  let selectedModule: string | null = null;
  let sortBy: 'revenue' | 'visits' | 'recency' = 'revenue';
  let sortOrder: 'asc' | 'desc' = 'desc';
  let pageSize: number = 25;

  // Reactive store subscription
  $: customers = $customersStore;
  
  // Track if component is mounted to avoid fetching before mount
  let isMounted = false;

  // Use local filters if set, otherwise use global filters
  $: effectiveStartDate = hasLocalDateOverride ? localStartDate : startDate;
  $: effectiveEndDate = hasLocalDateOverride ? localEndDate : endDate;

  function fetchCustomers() {
    if (!isMounted) return;
    
    const currentPage = customers?.pagination?.page || 1;
    
    fetchCustomersList(
      sucursalId,
      effectiveStartDate,
      effectiveEndDate,
      selectedModule,
      currentPage,
      pageSize,
      sortBy,
      sortOrder
    );
  }

  function handlePeriodChange(event: CustomEvent<{ startDate: string; endDate: string }>) {
    // Set local override
    localStartDate = event.detail.startDate;
    localEndDate = event.detail.endDate;
    hasLocalDateOverride = true;
    
    updateCustomersFilters({ startDate: localStartDate, endDate: localEndDate });
    // Reset to page 1 when filters change
    goToCustomersPage(1);
    fetchCustomers();
  }

  function resetToGlobalFilters() {
    hasLocalDateOverride = false;
    localStartDate = null;
    localEndDate = null;
    updateCustomersFilters({ startDate: startDate, endDate: endDate });
    goToCustomersPage(1);
    fetchCustomers();
  }

  function handleSucursalChange(sucursalId: string | null) {
    updateCustomersFilters({ sucursalId });
    goToCustomersPage(1);
    fetchCustomers();
  }

  function handleModuleSelectChange(event: Event) {
    const target = event.target as HTMLSelectElement;
    if (target) {
      const module = target.value === 'all' ? null : target.value;
      handleModuleChange(module);
    }
  }

  function handleModuleChange(module: string | null) {
    selectedModule = module;
    updateCustomersFilters({ module });
    goToCustomersPage(1);
    fetchCustomers();
  }

  function handlePageSizeSelectChange(event: Event) {
    const target = event.target as HTMLSelectElement;
    if (target) {
      handlePageSizeChange(Number(target.value));
    }
  }

  function handleSortChange(field: 'revenue' | 'visits' | 'recency') {
    if (sortBy === field) {
      sortOrder = sortOrder === 'asc' ? 'desc' : 'asc';
    } else {
      sortBy = field;
      sortOrder = 'desc';
    }
    updateCustomersFilters({ sortBy, order: sortOrder });
    goToCustomersPage(1);
    fetchCustomers();
  }

  function handlePageSizeChange(newSize: number) {
    pageSize = newSize;
    setCustomersPageSize(newSize);
    goToCustomersPage(1);
    fetchCustomers();
  }

  function handleNextPage() {
    nextCustomersPage();
    fetchCustomers();
  }

  function handlePreviousPage() {
    previousCustomersPage();
    fetchCustomers();
  }

  function formatDate(dateString: string | null): string {
    if (!dateString) return 'N/A';
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('es-ES', { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric' 
      });
    } catch {
      return 'N/A';
    }
  }

  onMount(() => {
    isMounted = true;
    fetchCustomers();
  });
</script>

  <div class="customers-list-container">
  <!-- Filters Section -->
  <div class="filters-section">
    <div class="filter-group">
      <div class="filter-header">
        <label class="filter-label">Período</label>
        {#if hasLocalDateOverride}
          <button
            class="reset-filter-button"
            on:click={resetToGlobalFilters}
            title="Usar filtros globales"
            aria-label="Resetear a filtros globales"
          >
            <span class="reset-icon">↻</span>
            Usar globales
          </button>
        {/if}
      </div>
      <PeriodSelector
        startDate={effectiveStartDate || ''}
        endDate={effectiveEndDate || ''}
        on:change={handlePeriodChange}
      />
      {#if hasLocalDateOverride}
        <div class="override-indicator">
          <span class="override-badge">Filtro local activo</span>
        </div>
      {/if}
    </div>

    <div class="filter-group">
      <label class="filter-label">Sucursal</label>
      <SucursalSelector
        selectedSucursalId={sucursalId}
        on:select={(e) => handleSucursalChange(e.detail)}
      />
    </div>

    <div class="filter-group">
      <label class="filter-label">Módulo</label>
      <select
        class="filter-select"
        value={selectedModule || 'all'}
        on:change={handleModuleSelectChange}
      >
        <option value="all">Todos</option>
        <option value="recepcion">Recepción</option>
        <option value="kidibar">KidiBar</option>
      </select>
    </div>

    <div class="filter-group">
      <label class="filter-label">Por página</label>
      <select
        class="filter-select"
        value={pageSize}
        on:change={handlePageSizeSelectChange}
      >
        <option value="10">10</option>
        <option value="25">25</option>
        <option value="50">50</option>
        <option value="100">100</option>
      </select>
    </div>
  </div>

  <!-- Loading State -->
  {#if !customers || customers.loading}
    <LoadingSpinner />
  {:else if customers.error}
    <ErrorBanner error={customers.error} />
  {:else if !customers.list || customers.list.length === 0}
    <div class="empty-state">
      <p>No se encontraron clientes con los filtros seleccionados.</p>
    </div>
  {:else}
    <!-- Customers Table -->
    <div class="table-container">
      <table class="customers-table">
        <thead>
          <tr>
            <th>
              <button
                class="sort-button"
                on:click={() => handleSortChange('revenue')}
                aria-label="Ordenar por revenue"
              >
                Cliente
                <ArrowUpDown size={14} />
              </button>
            </th>
            <th>Módulo</th>
            <th>
              <button
                class="sort-button"
                on:click={() => handleSortChange('visits')}
                aria-label="Ordenar por visitas"
              >
                Visitas
                <ArrowUpDown size={14} />
              </button>
            </th>
            <th>
              <button
                class="sort-button"
                on:click={() => handleSortChange('revenue')}
                aria-label="Ordenar por revenue"
              >
                Revenue Total
                <ArrowUpDown size={14} />
              </button>
            </th>
            <th>
              <button
                class="sort-button"
                on:click={() => handleSortChange('recency')}
                aria-label="Ordenar por última visita"
              >
                Última Visita
                <ArrowUpDown size={14} />
              </button>
            </th>
            <th>Primera Visita</th>
          </tr>
        </thead>
        <tbody>
          {#each customers.list as customer}
            <tr>
              <td class="customer-name-cell">
                <div class="customer-name">{customer.customer_name}</div>
                {#if customer.child_age}
                  <div class="customer-age">Edad: {customer.child_age}</div>
                {/if}
              </td>
              <td>
                <span class="module-badge" class:recepcion={customer.module === 'recepcion'} class:kidibar={customer.module === 'kidibar'}>
                  {customer.module === 'recepcion' ? 'Recepción' : 'KidiBar'}
                </span>
              </td>
              <td class="numeric-cell">{customer.visit_count}</td>
              <td class="numeric-cell">{formatPrice(customer.total_revenue_cents)}</td>
              <td>{formatDate(customer.last_visit_date)}</td>
              <td>{formatDate(customer.first_visit_date)}</td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>

    <!-- Pagination Controls -->
    <div class="pagination-section">
      <div class="pagination-info">
        Mostrando {customers.pagination ? (((customers.pagination.page - 1) * customers.pagination.pageSize) + 1) : 0} - 
        {customers.pagination ? Math.min(customers.pagination.page * customers.pagination.pageSize, customers.pagination.total) : 0} 
        de {customers.pagination?.total || 0} clientes
      </div>
      <div class="pagination-controls">
        <button
          class="pagination-button"
          disabled={!customers.pagination || customers.pagination.page === 1}
          on:click={handlePreviousPage}
          aria-label="Página anterior"
        >
          <ChevronLeft size={18} />
          Anterior
        </button>
        <span class="pagination-page">
          Página {customers.pagination?.page || 1}
        </span>
        <button
          class="pagination-button"
          disabled={!customers.pagination || !customers.pagination.hasMore}
          on:click={handleNextPage}
          aria-label="Página siguiente"
        >
          Siguiente
          <ChevronRight size={18} />
        </button>
      </div>
    </div>
  {/if}
</div>

<style>
  .customers-list-container {
    width: 100%;
  }

  .filters-section {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: var(--spacing-md);
    margin-bottom: var(--spacing-lg);
    padding: var(--spacing-md);
    background: var(--theme-bg-elevated);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
  }

  .filter-group {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xs);
  }

  .filter-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--spacing-xs);
  }

  .filter-label {
    font-size: var(--text-sm);
    font-weight: 500;
    color: var(--text-secondary);
  }

  .reset-filter-button {
    display: flex;
    align-items: center;
    gap: var(--spacing-xs);
    padding: var(--spacing-xs) var(--spacing-sm);
    background: var(--theme-bg-elevated);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-sm);
    color: var(--text-secondary);
    font-size: var(--text-xs);
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .reset-filter-button:hover {
    background: var(--accent-primary);
    color: var(--text-inverse);
    border-color: var(--accent-primary);
  }

  .reset-icon {
    font-size: var(--text-sm);
  }

  .override-indicator {
    margin-top: var(--spacing-xs);
  }

  .override-badge {
    display: inline-block;
    padding: var(--spacing-xs) var(--spacing-sm);
    background: var(--accent-primary);
    color: var(--text-inverse);
    border-radius: var(--radius-sm);
    font-size: var(--text-xs);
    font-weight: 500;
  }

  .filter-select {
    padding: var(--spacing-sm);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
    background: var(--theme-bg-elevated);
    color: var(--text-primary);
    font-size: var(--text-sm);
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .filter-select:hover {
    border-color: var(--accent-primary);
  }

  .filter-select:focus {
    outline: none;
    border-color: var(--accent-primary);
    box-shadow: 0 0 0 3px rgba(0, 147, 247, 0.1);
  }

  .table-container {
    overflow-x: auto;
    margin-bottom: var(--spacing-lg);
  }

  .customers-table {
    width: 100%;
    border-collapse: collapse;
    background: var(--theme-bg-card);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
    overflow: hidden;
  }

  .customers-table thead {
    background: var(--theme-bg-elevated);
  }

  .customers-table th {
    padding: var(--spacing-md);
    text-align: left;
    font-size: var(--text-sm);
    font-weight: 600;
    color: var(--text-secondary);
    border-bottom: 2px solid var(--border-primary);
  }

  .customers-table td {
    padding: var(--spacing-md);
    border-bottom: 1px solid var(--border-primary);
    font-size: var(--text-sm);
    color: var(--text-primary);
  }

  .customers-table tbody tr:hover {
    background: var(--theme-bg-elevated);
  }

  .sort-button {
    display: flex;
    align-items: center;
    gap: var(--spacing-xs, 0.5rem);
    background: transparent;
    border: none;
    cursor: pointer;
    font-size: inherit;
    font-weight: inherit;
    color: inherit;
    padding: 0;
  }

  .sort-button:hover {
    color: var(--accent-primary);
  }

  .customer-name-cell {
    min-width: 150px;
  }

  .customer-name {
    font-weight: 500;
    color: var(--text-primary);
  }

  .customer-age {
    font-size: var(--text-xs);
    color: var(--text-secondary);
    margin-top: var(--spacing-xs);
  }

  .module-badge {
    display: inline-block;
    padding: var(--spacing-xs, 0.25rem) var(--spacing-sm, 0.5rem);
    border-radius: var(--radius-sm, 0.25rem);
    font-size: var(--text-xs, 0.75rem);
    font-weight: 500;
  }

  .module-badge.recepcion {
    background: var(--color-recepcion, #e0f2fe);
    color: var(--color-recepcion-dark, #0369a1);
  }

  .module-badge.kidibar {
    background: var(--color-kidibar, #fef3c7);
    color: var(--color-kidibar-dark, #92400e);
  }

  .numeric-cell {
    text-align: right;
    font-variant-numeric: tabular-nums;
  }

  .empty-state {
    text-align: center;
    padding: var(--spacing-xl);
    color: var(--text-secondary);
  }

  .pagination-section {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: var(--spacing-md);
    background: var(--theme-bg-elevated);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
    flex-wrap: wrap;
    gap: var(--spacing-md);
  }

  .pagination-info {
    font-size: var(--text-sm);
    color: var(--text-secondary);
  }

  .pagination-controls {
    display: flex;
    align-items: center;
    gap: var(--spacing-md);
  }

  .pagination-button {
    display: flex;
    align-items: center;
    gap: var(--spacing-xs);
    padding: var(--spacing-sm) var(--spacing-md);
    background: var(--theme-bg-card);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
    color: var(--text-primary);
    font-size: var(--text-sm);
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .pagination-button:hover:not(:disabled) {
    background: var(--theme-bg-elevated);
    border-color: var(--accent-primary);
    color: var(--accent-primary);
  }

  .pagination-button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .pagination-page {
    font-size: var(--text-sm);
    font-weight: 500;
    color: var(--text-primary);
  }

  @media (max-width: 768px) {
    .filters-section {
      grid-template-columns: 1fr;
    }

    .customers-table {
      font-size: var(--text-xs, 0.75rem);
    }

    .customers-table th,
    .customers-table td {
      padding: var(--spacing-sm, 0.75rem);
    }

    .pagination-section {
      flex-direction: column;
      align-items: stretch;
    }

    .pagination-controls {
      justify-content: center;
    }
  }
</style>

