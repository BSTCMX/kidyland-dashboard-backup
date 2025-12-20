<script lang="ts">
  /**
   * DayCloseHistory component - Displays day close history (arqueos) with filters and details.
   * Styled to match SalesHistory component.
   */
  import { onMount } from "svelte";
  import { Button, Input } from "@kidyland/ui";
  import type { DayClose } from "$lib/stores/day-close-history";
  import {
    dayCloseHistoryStore,
    fetchDayCloseHistory,
    setPageSize,
    setPage,
  } from "$lib/stores/day-close-history";
  import { user } from "$lib/stores/auth";
  import LoadingSpinner from "../admin/LoadingSpinner.svelte";
  import ErrorBanner from "../admin/ErrorBanner.svelte";
  import { FileText, RefreshCw, Eye } from "lucide-svelte";
  import CashReconciliation from "./CashReconciliation.svelte";

  export let sucursalId: string = "";

  // Local state
  let startDateFilter = "";
  let endDateFilter = "";
  let selectedDayClose: DayClose | null = null;
  let showDetails = false;

  $: currentUser = $user;
  $: targetSucursalId = sucursalId || currentUser?.sucursal_id || "";

  onMount(() => {
    if (targetSucursalId) {
      // Initial load
      const currentSkip = ($dayCloseHistoryStore.pagination.page - 1) * $dayCloseHistoryStore.pagination.pageSize;
      fetchDayCloseHistory(
        targetSucursalId,
        undefined,
        undefined,
        currentSkip,
        $dayCloseHistoryStore.pagination.pageSize
      );
    }
  });

  function formatPrice(cents: number): string {
    return `$${(cents / 100).toFixed(2)}`;
  }

  function formatDate(dateString: string | Date): string {
    try {
      const date = typeof dateString === 'string' 
        ? new Date(dateString + "T00:00:00") 
        : dateString;
      return date.toLocaleDateString("es-ES", {
        year: "numeric",
        month: "short",
        day: "numeric",
      });
    } catch {
      return typeof dateString === 'string' ? dateString : dateString.toString();
    }
  }

  function formatDateTime(dateString: string): string {
    try {
      const date = new Date(dateString);
      return date.toLocaleString("es-ES", {
        year: "numeric",
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return dateString;
    }
  }

  function handleViewDetails(dayClose: DayClose) {
    selectedDayClose = dayClose;
    showDetails = true;
  }

  async function handleFilterChange() {
    if (targetSucursalId) {
      // Reset to page 1 when filtering
      setPage(1);
      const currentSkip = 0; // Page 1 = skip 0
      await fetchDayCloseHistory(
        targetSucursalId,
        startDateFilter || undefined,
        endDateFilter || undefined,
        currentSkip,
        $dayCloseHistoryStore.pagination.pageSize
      );
    }
  }

  async function handlePageChange(newPage: number) {
    setPage(newPage);
    const currentSkip = (newPage - 1) * $dayCloseHistoryStore.pagination.pageSize;
    await fetchDayCloseHistory(
      targetSucursalId,
      startDateFilter || undefined,
      endDateFilter || undefined,
      currentSkip,
      $dayCloseHistoryStore.pagination.pageSize
    );
  }

  async function handlePageSizeChange(newSize: number) {
    setPageSize(newSize);
    setPage(1); // Reset to page 1 when changing page size
    const currentSkip = 0;
    await fetchDayCloseHistory(
      targetSucursalId,
      startDateFilter || undefined,
      endDateFilter || undefined,
      currentSkip,
      newSize
    );
  }

  // Helper function for safe number conversion
  function safeToNumber(value: any): number {
    if (typeof value === 'number') return value;
    if (typeof value === 'string') {
      const parsed = Number(value);
      return isNaN(parsed) ? 0 : parsed;
    }
    return 0;
  }
</script>

<div class="day-close-history-container">
  <div class="page-header">
    <div class="header-actions">
      <div class="date-filters">
        <label class="date-filter-label">
          <span class="date-label-text">Desde:</span>
          <input
            type="date"
            bind:value={startDateFilter}
            class="date-input"
          />
        </label>
        <label class="date-filter-label">
          <span class="date-label-text">Hasta:</span>
          <input
            type="date"
            bind:value={endDateFilter}
            class="date-input"
          />
        </label>
      </div>
      <label class="page-size-selector">
        <span>Registros por página:</span>
        <select
          value={$dayCloseHistoryStore.pagination.pageSize}
          on:change={(e) => handlePageSizeChange(Number(e.currentTarget.value))}
          class="page-size-select"
        >
          <option value={25}>25</option>
          <option value={50}>50</option>
          <option value={100}>100</option>
        </select>
      </label>
      <Button variant="brutalist" size="small" on:click={handleFilterChange}>
        <RefreshCw size={16} strokeWidth={1.5} />
        Actualizar
      </Button>
    </div>
  </div>

  {#if $dayCloseHistoryStore.error}
    <ErrorBanner error={$dayCloseHistoryStore.error} />
  {/if}

  {#if $dayCloseHistoryStore.loading}
    <LoadingSpinner message="Cargando arqueos..." />
  {:else if $dayCloseHistoryStore.list.length === 0}
    <div class="empty-state">
      <p>No hay arqueos registrados para los filtros seleccionados.</p>
    </div>
  {:else}
    <!-- Desktop: Grid layout (table-like) -->
    <div class="day-closes-grid-container">
      <div class="grid-headers">
        <div class="grid-header">Fecha</div>
        <div class="grid-header">Hora Inicio</div>
        <div class="grid-header">Fecha/Hora Cierre</div>
        <div class="grid-header">Total Sistema</div>
        <div class="grid-header">Dinero Contado</div>
        <div class="grid-header">Diferencia</div>
        <div class="grid-header">Acciones</div>
      </div>
      <div class="day-closes-grid">
        {#each $dayCloseHistoryStore.list as dayClose (dayClose.id)}
          <div class="day-close-grid-item">
            <div class="grid-cell" data-label="Fecha">{formatDate(dayClose.date)}</div>
            <div class="grid-cell" data-label="Hora Inicio">
              {dayClose.started_at ? formatDateTime(dayClose.started_at) : "N/A"}
            </div>
            <div class="grid-cell" data-label="Fecha/Hora Cierre">
              {dayClose.closed_at ? formatDateTime(dayClose.closed_at) : (dayClose.created_at ? formatDateTime(dayClose.created_at) : "N/A")}
            </div>
            <div class="grid-cell total-amount" data-label="Total Sistema">{formatPrice(dayClose.system_total_cents)}</div>
            <div class="grid-cell total-amount" data-label="Dinero Contado">{formatPrice(dayClose.physical_count_cents)}</div>
            <div class="grid-cell" data-label="Diferencia" class:difference-positive={dayClose.difference_cents > 0} class:difference-negative={dayClose.difference_cents < 0} class:difference-zero={dayClose.difference_cents === 0}>
              <span class="difference-value">
                {dayClose.difference_cents > 0 ? "+" : ""}{formatPrice(dayClose.difference_cents)}
              </span>
            </div>
            <div class="grid-cell actions-cell" data-label="Acciones">
              <Button
                variant="brutalist"
                size="small"
                on:click={() => handleViewDetails(dayClose)}
              >
                <Eye size={16} strokeWidth={1.5} />
                Ver
              </Button>
            </div>
          </div>
        {/each}
      </div>
    </div>

    <!-- Mobile: Cards layout -->
    <div class="day-closes-cards">
      {#each $dayCloseHistoryStore.list as dayClose (dayClose.id)}
        <div class="day-close-card">
          <div class="day-close-card-header">
            <h3 class="day-close-card-title">{formatDate(dayClose.date)}</h3>
            <span class="difference-badge" class:positive={dayClose.difference_cents > 0} class:negative={dayClose.difference_cents < 0} class:zero={dayClose.difference_cents === 0}>
              {dayClose.difference_cents > 0 ? "+" : ""}{formatPrice(dayClose.difference_cents)}
            </span>
          </div>
          <div class="day-close-card-body">
            {#if dayClose.started_at}
              <div class="day-close-card-row">
                <span class="day-close-card-label">Hora Inicio:</span>
                <span class="day-close-card-value">{formatDateTime(dayClose.started_at)}</span>
              </div>
            {/if}
            {#if dayClose.closed_at || dayClose.created_at}
              <div class="day-close-card-row">
                <span class="day-close-card-label">Fecha/Hora Cierre:</span>
                <span class="day-close-card-value">{formatDateTime(dayClose.closed_at || dayClose.created_at)}</span>
              </div>
            {/if}
            <div class="day-close-card-row">
              <span class="day-close-card-label">Total Sistema:</span>
              <span class="day-close-card-value total-amount">{formatPrice(dayClose.system_total_cents)}</span>
            </div>
            <div class="day-close-card-row">
              <span class="day-close-card-label">Dinero Contado:</span>
              <span class="day-close-card-value total-amount">{formatPrice(dayClose.physical_count_cents)}</span>
            </div>
            {#if dayClose.totals}
              {#if dayClose.totals.total_sales_count !== undefined}
                <div class="day-close-card-row">
                  <span class="day-close-card-label">Ventas:</span>
                  <span class="day-close-card-value">{dayClose.totals.total_sales_count}</span>
                </div>
              {/if}
              {#if dayClose.totals.total_revenue_cents !== undefined}
                <div class="day-close-card-row">
                  <span class="day-close-card-label">Ingresos Totales:</span>
                  <span class="day-close-card-value">{formatPrice(dayClose.totals.total_revenue_cents)}</span>
                </div>
              {/if}
            {/if}
          </div>
          <div class="day-close-card-actions">
            <Button
              variant="brutalist"
              size="small"
              on:click={() => handleViewDetails(dayClose)}
            >
              <Eye size={16} strokeWidth={1.5} />
              Ver Detalles
            </Button>
          </div>
        </div>
      {/each}
    </div>

    <!-- Pagination Controls -->
    {#if $dayCloseHistoryStore.pagination.hasMore || $dayCloseHistoryStore.pagination.page > 1}
      <div class="pagination-controls">
        <Button
          variant="brutalist"
          disabled={$dayCloseHistoryStore.pagination.page === 1 || $dayCloseHistoryStore.loading}
          on:click={() => handlePageChange($dayCloseHistoryStore.pagination.page - 1)}
        >
          ← Anterior
        </Button>
        <span class="page-info">
          Página {$dayCloseHistoryStore.pagination.page}
        </span>
        <Button
          variant="brutalist"
          disabled={!$dayCloseHistoryStore.pagination.hasMore || $dayCloseHistoryStore.loading}
          on:click={() => handlePageChange($dayCloseHistoryStore.pagination.page + 1)}
        >
          Siguiente →
        </Button>
      </div>
    {/if}
  {/if}

  <!-- Day Close Details Modal -->
  {#if showDetails && selectedDayClose}
    <div class="modal-overlay" on:click={() => (showDetails = false)}>
      <div class="modal-content" on:click|stopPropagation>
        <div class="modal-header">
          <h2>Detalles del Arqueo</h2>
          <button class="close-button" on:click={() => (showDetails = false)}>×</button>
        </div>
        
        <div class="modal-body">
          <CashReconciliation dayClose={selectedDayClose} />
        </div>
        
        <div class="modal-actions">
          <Button variant="secondary" on:click={() => (showDetails = false)}>
            Cerrar
          </Button>
        </div>
      </div>
    </div>
  {/if}
</div>

<style>
  .day-close-history-container {
    padding: var(--spacing-xl);
  }

  .page-header {
    display: flex;
    justify-content: flex-end;
    align-items: center;
    margin-bottom: var(--spacing-xl);
    flex-wrap: wrap;
    gap: var(--spacing-md);
  }

  .header-actions {
    display: flex;
    gap: var(--spacing-md);
    align-items: center;
  }

  .date-filters {
    display: flex;
    gap: var(--spacing-sm);
    align-items: center;
  }

  .date-filter-label {
    display: flex;
    align-items: center;
    gap: var(--spacing-xs);
  }

  .date-label-text {
    font-size: var(--text-sm);
    font-weight: 600;
    color: var(--text-primary);
    white-space: nowrap;
  }

  .date-input {
    min-width: 150px;
    height: 40px;
    font-size: var(--text-base);
    padding: 0 15px;
    background-color: var(--input-bg);
    border-radius: 12px;
    border: 1px solid var(--border-primary);
    box-sizing: border-box;
    color: var(--text-primary);
    outline: 0;
    font-family: var(--font-body, sans-serif);
    transition: all 0.2s ease;
  }

  .date-input:focus {
    background-color: var(--input-bg-focus);
    border-color: var(--accent-primary);
  }

  .page-size-selector {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    color: var(--text-primary);
    padding: var(--spacing-sm) var(--spacing-md);
    background: var(--theme-bg-elevated);
    border: 2px solid var(--accent-primary);
    border-radius: var(--radius-md);
    box-shadow: 3px 3px 0px 0px var(--accent-primary);
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    font-weight: 600;
  }

  .page-size-selector.disabled {
    opacity: 0.6;
    cursor: not-allowed;
    pointer-events: none;
    box-shadow: 1px 1px 0px 0px var(--border-primary);
  }

  .page-size-selector:hover:not(.disabled) {
    box-shadow: none;
    border-width: 3px;
    transform: translate(3px, 3px);
    background: var(--accent-primary);
    color: var(--text-inverse);
  }

  .page-size-selector:active:not(.disabled) {
    transform: translate(2px, 2px);
    transition-duration: 0.1s;
  }

  .page-size-selector span {
    font-size: var(--text-sm);
    white-space: nowrap;
  }

  .page-size-selector select,
  .page-size-select {
    padding: var(--spacing-xs) var(--spacing-sm);
    border: none;
    border-radius: var(--radius-sm);
    background: transparent;
    color: inherit;
    font-size: var(--text-sm);
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
    outline: none;
    -webkit-appearance: none;
    -moz-appearance: none;
    appearance: none;
    background-image: url('data:image/svg+xml;utf8,<svg fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg"><path fill-rule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clip-rule="evenodd"></path></svg>');
    background-repeat: no-repeat;
    background-position: right 0.5rem center;
    background-size: 1em;
    padding-right: 1.5rem;
  }

  .page-size-selector select:disabled,
  .page-size-select:disabled {
    cursor: not-allowed;
    opacity: 0.6;
  }

  .page-size-selector:hover:not(.disabled) select,
  .page-size-selector:hover:not(.disabled) .page-size-select {
    color: var(--text-inverse);
  }

  .page-size-selector select:focus:not(:disabled),
  .page-size-select:focus:not(:disabled) {
    outline: none;
  }

  .empty-state {
    text-align: center;
    padding: var(--spacing-2xl);
    color: var(--text-secondary);
    background: var(--theme-bg-card);
    backdrop-filter: blur(16px) saturate(150%);
    -webkit-backdrop-filter: blur(16px) saturate(150%);
    border: 1px solid var(--border-primary);
    border-radius: 16px;
    box-shadow: 
      0 8px 24px rgba(0, 0, 0, 0.15),
      0 0 20px var(--glow-primary),
      inset 0 1px 0 rgba(255, 255, 255, 0.05);
  }

  /* Grid Container - Desktop table-like layout */
  .day-closes-grid-container {
    width: 100%;
    margin-bottom: var(--spacing-lg);
    background: var(--theme-bg-card);
    backdrop-filter: blur(16px) saturate(150%);
    -webkit-backdrop-filter: blur(16px) saturate(150%);
    border: 1px solid var(--border-primary);
    border-radius: 16px;
    box-shadow: 
      0 8px 24px rgba(0, 0, 0, 0.15),
      0 0 20px var(--glow-primary),
      inset 0 1px 0 rgba(255, 255, 255, 0.05);
    position: relative;
    overflow: hidden;
  }

  /* Grid Headers - Desktop only */
  .grid-headers {
    display: none; /* Hidden on mobile */
  }

  /* Day Closes Grid - Desktop table-like layout */
  .day-closes-grid {
    display: grid;
    grid-template-columns: 1fr; /* Mobile: single column */
    gap: 0;
    width: 100%;
  }

  /* Day Close Grid Item - Desktop: transparent container */
  .day-close-grid-item {
    display: contents; /* Default: transparent container for table-like layout */
  }

  /* Grid Cell - Individual data cell */
  .grid-cell {
    padding: var(--spacing-md) var(--spacing-sm);
    display: flex;
    align-items: center;
    font-size: var(--text-sm);
    color: var(--text-primary);
    word-wrap: break-word;
    overflow-wrap: break-word;
  }

  .grid-cell.total-amount {
    font-weight: 700;
    font-size: var(--text-base);
    color: var(--accent-success);
    text-shadow: 0 0 10px var(--glow-success);
  }

  .grid-cell.difference-positive .difference-value {
    color: var(--accent-success);
    font-weight: 700;
    text-shadow: 0 0 10px var(--glow-success);
  }

  .grid-cell.difference-negative .difference-value {
    color: var(--accent-danger);
    font-weight: 700;
  }

  .grid-cell.difference-zero .difference-value {
    color: var(--accent-warning);
    font-weight: 700;
  }

  .grid-cell.actions-cell {
    gap: var(--spacing-sm);
    flex-wrap: wrap;
  }

  /* Desktop: Grid layout with proper column distribution - TABLE-LIKE */
  @media (min-width: 769px) {
    /* Show headers on desktop */
    .grid-headers {
      display: grid;
      grid-template-columns: 1.2fr 1.5fr 1.5fr 1.2fr 1.2fr 1.2fr 1.8fr; /* 7 columns */
      gap: 0;
      background: linear-gradient(135deg, var(--theme-bg-secondary) 0%, var(--theme-bg-elevated) 100%);
      border-bottom: 2px solid var(--border-primary);
      position: sticky;
      top: 0;
      z-index: 10;
    }

    /* Grid header cell */
    .grid-header {
      padding: 0.75rem 0.625rem;
      font-weight: 700;
      font-size: 0.75rem;
      color: var(--text-secondary);
      text-transform: uppercase;
      letter-spacing: 0.1em;
      white-space: nowrap;
      text-align: left;
    }

    /* Day closes grid - 5 columns on desktop */
    .day-closes-grid {
      grid-template-columns: 1.2fr 1.5fr 1.5fr 1.2fr 1.2fr 1.2fr 1.8fr; /* 7 columns - matches headers */
      gap: 0; /* No gaps to simulate table */
    }

    /* Day close grid item - display: contents makes it transparent */
    .day-close-grid-item {
      display: contents; /* CRÍTICO: contenedor transparente, celdas alineadas al grid padre */
    }

    /* Grid cells on desktop - table-like appearance */
    .grid-cell {
      padding: 0.875rem 0.625rem;
      font-size: 0.9375rem;
      line-height: 1.5;
      border-right: 1px solid var(--border-primary);
      background: var(--theme-bg-elevated);
      transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
      position: relative;
    }

    .grid-cell:last-child {
      border-right: none;
    }

    /* Row hover effect */
    .day-close-grid-item:hover .grid-cell {
      background: linear-gradient(90deg, var(--theme-bg-secondary) 0%, transparent 100%);
      transform: translateY(-1px);
      box-shadow: 0 2px 8px rgba(0, 147, 247, 0.1);
    }

    .actions-cell {
      display: flex;
      gap: var(--spacing-sm);
      align-items: center;
    }
  }

  /* Mobile: Hide grid, show cards */
  @media (max-width: 768px) {
    .day-closes-grid-container {
      display: none !important; /* Hide grid on mobile */
    }

    .day-closes-cards {
      display: grid !important;
      grid-template-columns: 1fr;
      gap: var(--spacing-md);
    }
  }

  /* Desktop: Hide cards, show grid */
  @media (min-width: 769px) {
    .day-closes-cards {
      display: none !important; /* Hide cards on desktop */
    }
  }

  /* Day Close Cards - Mobile layout */
  .day-closes-cards {
    display: none; /* Hidden by default (desktop) */
  }

  .day-close-card {
    background: var(--theme-bg-card);
    backdrop-filter: blur(16px) saturate(150%);
    -webkit-backdrop-filter: blur(16px) saturate(150%);
    border: 1px solid var(--border-primary);
    border-radius: 16px;
    padding: var(--spacing-lg);
    box-shadow: 
      0 8px 24px rgba(0, 0, 0, 0.15),
      0 0 20px var(--glow-primary),
      inset 0 1px 0 rgba(255, 255, 255, 0.05);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }

  .day-close-card:hover {
    transform: translateY(-4px);
    border-color: rgba(0, 147, 247, 0.5);
    box-shadow: 
      0 12px 32px rgba(0, 0, 0, 0.2),
      0 0 30px var(--glow-primary),
      0 0 40px var(--glow-secondary),
      inset 0 1px 0 rgba(255, 255, 255, 0.1);
  }

  .day-close-card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--spacing-md);
    padding-bottom: var(--spacing-md);
    border-bottom: 1px solid var(--border-primary);
  }

  .day-close-card-title {
    font-size: var(--text-lg);
    font-weight: 700;
    color: var(--text-primary);
    margin: 0;
  }

  .difference-badge {
    padding: var(--spacing-xs) var(--spacing-sm);
    border-radius: var(--radius-sm);
    font-size: var(--text-sm);
    font-weight: 700;
  }

  .difference-badge.positive {
    background: rgba(34, 197, 94, 0.1);
    border: 1px solid var(--accent-success);
    color: var(--accent-success);
  }

  .difference-badge.negative {
    background: rgba(211, 5, 84, 0.1);
    border: 1px solid var(--accent-danger);
    color: var(--accent-danger);
  }

  .difference-badge.zero {
    background: rgba(255, 206, 0, 0.1);
    border: 1px solid var(--accent-warning);
    color: var(--accent-warning);
  }

  .day-close-card-body {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-sm);
    margin-bottom: var(--spacing-md);
  }

  .day-close-card-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .day-close-card-label {
    font-weight: 600;
    color: var(--text-secondary);
    font-size: var(--text-sm);
  }

  .day-close-card-value {
    color: var(--text-primary);
    font-size: var(--text-sm);
  }

  .day-close-card-value.total-amount {
    font-weight: 700;
    color: var(--accent-success);
    text-shadow: 0 0 10px var(--glow-success);
  }

  .day-close-card-actions {
    display: flex;
    gap: var(--spacing-sm);
    flex-wrap: wrap;
  }

  .pagination-controls {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: var(--spacing-md);
    margin-top: var(--spacing-xl);
    padding: var(--spacing-lg);
    background: var(--theme-bg-card);
    backdrop-filter: blur(16px) saturate(150%);
    -webkit-backdrop-filter: blur(16px) saturate(150%);
    border: 1px solid var(--border-primary);
    border-radius: 16px;
    box-shadow: 
      0 4px 12px rgba(0, 0, 0, 0.15),
      0 0 10px var(--glow-primary);
  }

  .page-info {
    font-size: var(--text-base);
    color: var(--text-primary);
    font-weight: 600;
    padding: var(--spacing-sm) var(--spacing-md);
    background: var(--theme-bg-elevated);
    border-radius: var(--radius-md);
    border: 1px solid var(--border-primary);
  }

  .modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.6);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
    backdrop-filter: blur(8px) saturate(150%);
    -webkit-backdrop-filter: blur(8px) saturate(150%);
  }

  .modal-content {
    background: var(--theme-bg-card);
    backdrop-filter: blur(16px) saturate(150%);
    -webkit-backdrop-filter: blur(16px) saturate(150%);
    padding: var(--spacing-xl);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-lg);
    max-width: 600px;
    width: 90%;
    max-height: 90vh;
    overflow-y: auto;
    box-shadow: 
      0 8px 24px rgba(0, 0, 0, 0.2),
      0 0 20px var(--glow-primary),
      0 0 40px var(--glow-secondary),
      inset 0 1px 0 rgba(255, 255, 255, 0.1);
  }

  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--spacing-lg);
    padding-bottom: var(--spacing-md);
    border-bottom: 1px solid var(--border-primary);
  }

  .modal-header h2 {
    margin: 0;
    font-family: var(--font-primary);
    font-size: var(--text-2xl);
    font-weight: 700;
    color: var(--text-primary);
    
    /* Efecto 3D - solo sombreado, sin animaciones */
    text-shadow: 
      0 0.05em 0 rgba(0, 0, 0, 0.1),
      0 0.1em 0 rgba(0, 0, 0, 0.1),
      0 0.15em 0 rgba(0, 0, 0, 0.1),
      0 0.2em 0 rgba(0, 0, 0, 0.1),
      0 0.25em 0 rgba(0, 0, 0, 0.1),
      0 0.25em 0.02em rgba(0, 0, 0, 0.15),
      0 0.28em 0.2em rgba(0, 0, 0, 0.25);
  }

  .close-button {
    background: var(--theme-bg-secondary);
    border: 2px solid var(--border-primary);
    font-size: 24px;
    line-height: 1;
    color: var(--text-primary);
    cursor: pointer;
    padding: 0;
    width: 36px;
    height: 36px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    transition: all 0.2s ease;
    font-weight: 600;
    box-shadow: 
      0 2px 8px rgba(0, 0, 0, 0.1),
      0 0 10px var(--glow-primary);
  }

  .close-button:hover {
    background: var(--accent-danger);
    border-color: var(--accent-danger);
    color: #ffffff;
    box-shadow: 0 0 20px rgba(211, 5, 84, 0.3);
    transform: translateY(-2px);
  }

  .close-button:active {
    transform: translateY(0);
  }

  .modal-body {
    margin-bottom: var(--spacing-lg);
  }

  .modal-actions {
    display: flex;
    justify-content: flex-end;
    gap: var(--spacing-md);
    padding-top: var(--spacing-md);
    border-top: 1px solid var(--border-primary);
  }

  /* Responsive: Mobile */
  @media (max-width: 768px) {
    .day-close-history-container {
      padding: var(--spacing-md);
    }

    .page-header {
      flex-direction: column;
      align-items: stretch;
      gap: var(--spacing-md);
    }

    .header-actions {
      flex-direction: column;
      width: 100%;
      gap: var(--spacing-sm);
    }

    .date-filters {
      flex-direction: column;
      width: 100%;
      gap: var(--spacing-sm);
    }

    .date-filter-label {
      width: 100%;
      flex-direction: column;
      align-items: flex-start;
      gap: var(--spacing-xs);
    }

    .date-label-text {
      font-size: var(--text-xs);
    }

    .date-input {
      width: 100%;
      min-width: auto;
    }

    .page-size-selector {
      width: 100%;
      justify-content: space-between;
    }

    .header-actions :global(.btn-brutalist) {
      width: 100%;
      min-height: 48px;
      justify-content: center;
      display: flex !important;
      align-items: center;
      gap: var(--spacing-xs);
    }

    .day-close-card-actions {
      flex-direction: column;
    }

    .day-close-card-actions :global(.btn-brutalist) {
      width: 100%;
      min-height: 48px;
    }

    .pagination-controls {
      flex-direction: column;
      gap: var(--spacing-sm);
    }

    .pagination-controls :global(.btn) {
      width: 100%;
      min-height: 48px;
    }

    .modal-content {
      width: 95%;
      padding: var(--spacing-md);
    }
  }

  /* Tablet adjustments */
  @media (min-width: 769px) and (max-width: 1024px) {
    .grid-headers {
      grid-template-columns: 1fr 1.2fr 1.2fr 1fr 1fr 1fr 1.5fr; /* 7 columns - adjusted for smaller screens */
    }

    .day-closes-grid {
      grid-template-columns: 1fr 1.2fr 1.2fr 1fr 1fr 1fr 1.5fr; /* 7 columns - adjusted for smaller screens */
    }
  }

  /* Prevent hover transform issues on touch devices */
  @media (hover: none) and (pointer: coarse) {
    .day-close-card:hover {
      transform: none;
    }

    .day-close-grid-item:hover .grid-cell {
      transform: none;
    }
  }
</style>
