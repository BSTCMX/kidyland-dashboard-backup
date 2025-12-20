<script lang="ts">
  /**
   * SalesHistory component - Displays sales history with filters and print functionality.
   */
  import { onMount } from "svelte";
  import { Button, Input } from "@kidyland/ui";
  import type { Sale } from "@kidyland/shared/types";
  import {
    salesHistoryStore,
    fetchSales,
    fetchTodaySales,
    fetchSaleById,
    printTicket,
    getTicketHtml,
    setPageSize,
    setPage,
  } from "$lib/stores/sales-history";
  import { user } from "$lib/stores/auth";
  import LoadingSpinner from "../admin/LoadingSpinner.svelte";
  import ErrorBanner from "../admin/ErrorBanner.svelte";
  import { FileText, RefreshCw, Eye, Printer } from "lucide-svelte";

  export let saleType: "service" | "product" | "package" | "all" | "product_package" = "all";
  export let packageType: "service" | "product" | undefined = undefined; // Optional: filter packages by type when saleType="package"
  export let sucursalId: string | undefined = undefined; // Optional: allows super_admin to specify sucursal_id via query params

  // Local state
  let showTodayOnly = true;
  let selectedSale: Sale | null = null;
  let showSaleDetails = false;
  let ticketHtml: string | null = null;
  let loadingTicket = false;

  $: currentUser = $user;
  // Use prop sucursalId if provided, otherwise use current user's sucursal_id
  // This allows super_admin to specify sucursal_id via query params
  $: targetSucursalId = sucursalId || currentUser?.sucursal_id || undefined;
  
  // No need to filter in frontend - backend handles all filtering
  $: filteredSales = $salesHistoryStore.list;

  // Column configuration interface
  interface ColumnConfig {
    key: string;
    label: string;
    width: string; // CSS grid width (e.g., "1fr", "1.5fr")
    show: (saleType: string, packageType?: string) => boolean;
    renderCell: (sale: Sale) => any; // Function to render cell content
  }

  // Get all column configurations
  function getColumnConfig(): ColumnConfig[] {
    return [
      {
        key: "date",
        label: "Fecha/Hora",
        width: "1.5fr",
        show: () => true, // Always show
        renderCell: (sale) => formatDate(sale.timestamps.created_at)
      },
      {
        key: "type",
        label: "Tipo",
        width: "1fr",
        show: () => true, // Always show
        renderCell: (sale) => getSaleTypeLabel(sale.tipo)
      },
      {
        key: "payer",
        label: "Pagador",
        width: "1.2fr",
        show: () => true, // Always show
        renderCell: (sale) => sale.payer.name || "N/A"
      },
      {
        key: "phone",
        label: "Teléfono",
        width: "1fr",
        show: (st, pt) => st === "product_package" || (st === "package" && pt === "service"), // Kidibar (product_package) OR Recepción paquetes de servicios
        renderCell: (sale) => sale.payer.phone && sale.payer.phone.trim() ? sale.payer.phone : null
      },
      {
        key: "children",
        label: "Niño",
        width: "1fr",
        show: (st, pt) => st === "service" || (st === "package" && pt === "service"), // Recepción servicios O Recepción paquetes de servicios (NO Kidibar)
        renderCell: (sale) => sale.children && sale.children.length > 0 ? formatChildren(sale.children) : null
      },
      {
        key: "scheduled_date",
        label: "Fecha Programada",
        width: "1fr",
        show: (st, pt) => st === "package" && pt === "service", // Only for service packages
        renderCell: (sale) => sale.scheduled_date ? formatScheduledDate(sale.scheduled_date) : null
      },
      {
        key: "total",
        label: "Total",
        width: "1fr",
        show: () => true, // Always show
        renderCell: (sale) => formatPrice(sale.pricing.total_cents)
      },
      {
        key: "payment_method",
        label: "Método Pago",
        width: "1fr",
        show: () => true, // Always show
        renderCell: (sale) => sale.payment.method
      },
      {
        key: "actions",
        label: "Acciones",
        width: "2fr",
        show: () => true, // Always show
        renderCell: () => null // Actions are rendered separately
      }
    ];
  }

  // Get visible columns based on saleType and packageType
  $: visibleColumns = getColumnConfig().filter(col => col.show(saleType, packageType));

  // Calculate dynamic grid-template-columns CSS
  $: gridColumns = visibleColumns.map(col => col.width).join(" ");

  onMount(() => {
    if (targetSucursalId) {
      // Determine tipo, package_type, and include_package_type based on saleType
      let tipo: string | undefined;
      let package_type_param: string | undefined;
      let include_package_type: string | undefined;
      
      if (saleType === "product_package") {
        // Unified view: products + product packages
        tipo = "product";
        include_package_type = "product";
        package_type_param = undefined;
      } else if (saleType === "package" && packageType) {
        // Filter packages by type (e.g., service packages only)
        tipo = "package";
        package_type_param = packageType;
        include_package_type = undefined;
      } else if (saleType === "all") {
        tipo = undefined;
        package_type_param = undefined;
        include_package_type = undefined;
      } else {
        tipo = saleType;
        package_type_param = undefined;
        include_package_type = undefined;
      }
      
      if (showTodayOnly) {
        // Pass tipo, package_type, and include_package_type to fetchTodaySales
        fetchTodaySales(
          targetSucursalId,
          tipo,
          0, // skip = 0 for first page
          $salesHistoryStore.pagination.pageSize,
          package_type_param,
          include_package_type
        );
      } else {
        // Initial load with pagination (page 1, skip=0)
        fetchSales(
          targetSucursalId,
          undefined,
          undefined,
          tipo,
          0, // skip = 0 for first page
          $salesHistoryStore.pagination.pageSize,
          package_type_param,
          include_package_type
        );
      }
    }
  });

  function formatPrice(cents: number): string {
    return `$${(cents / 100).toFixed(2)}`;
  }

  function formatDate(dateString: string): string {
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

  function formatScheduledDate(dateString: string): string {
    try {
      // scheduled_date comes as YYYY-MM-DD format
      const date = new Date(dateString + "T00:00:00"); // Add time to avoid timezone issues
      return date.toLocaleDateString("es-ES", {
        year: "numeric",
        month: "short",
        day: "numeric",
      });
    } catch {
      return dateString;
    }
  }

  function getSaleTypeLabel(tipo: string): string {
    const labels: Record<string, string> = {
      service: "Servicio",
      product: "Producto",
      day: "Día",
      package: "Paquete",
    };
    return labels[tipo] || tipo;
  }

  function formatChildren(children: any[] | null | undefined): string {
    // Normalize: ensure children is always an array
    // Handle cases where children might be null, undefined, or not an array
    if (!children) {
      return "N/A";
    }
    
    // Ensure it's an array
    const childrenArray = Array.isArray(children) ? children : [children];
    
    if (childrenArray.length === 0) {
      return "N/A";
    }
    
    return childrenArray
      .map((child) => {
        const name = child?.name || "Sin nombre";
        const age = child?.age ? ` (${child.age})` : "";
        return `${name}${age}`;
      })
      .join(", ");
  }

  async function handlePrint(saleId: string) {
    try {
      await printTicket(saleId);
    } catch (error: any) {
      console.error("Error printing ticket:", error);
    }
  }

  async function handleViewDetails(saleId: string) {
    loadingTicket = true;
    ticketHtml = null;
    selectedSale = null;
    showSaleDetails = false;
    
    try {
      // Fetch both sale data and ticket HTML in parallel
      const [sale, html] = await Promise.all([
        fetchSaleById(saleId),
        getTicketHtml(saleId).catch((err) => {
          console.warn("Could not load ticket HTML, will show sale details only:", err);
          return null; // Return null if ticket HTML fails, but don't break the flow
        }),
      ]);
      
      if (sale) {
        selectedSale = sale;
        ticketHtml = html; // Can be null if getTicketHtml failed
        showSaleDetails = true;
      } else {
        console.error("Could not load sale data");
      }
    } catch (error: any) {
      console.error("Error loading sale or ticket:", error);
      // Fallback: try to load just the sale data
      try {
        const sale = await fetchSaleById(saleId);
        if (sale) {
          selectedSale = sale;
          ticketHtml = null; // Explicitly set to null if we couldn't load it
          showSaleDetails = true;
        }
      } catch (fallbackError: any) {
        console.error("Error in fallback loading:", fallbackError);
      }
    } finally {
      loadingTicket = false;
    }
  }

  async function handleFilterChange() {
    if (targetSucursalId) {
      // Determine tipo, package_type, and include_package_type based on saleType
      let tipo: string | undefined;
      let package_type: string | undefined;
      let include_package_type: string | undefined;
      
      if (saleType === "product_package") {
        // Unified view: products + product packages
        tipo = "product";
        include_package_type = "product";
        package_type = undefined;
      } else if (saleType === "package" && packageType) {
        // Filter packages by type (e.g., service packages only)
        tipo = "package";
        package_type = packageType;
        include_package_type = undefined;
      } else if (saleType === "all") {
        tipo = undefined;
        package_type = undefined;
        include_package_type = undefined;
      } else {
        tipo = saleType;
        package_type = undefined;
        include_package_type = undefined;
      }
      
      if (showTodayOnly) {
        // Calculate skip from current page and pageSize for today's sales
        const currentSkip = ($salesHistoryStore.pagination.page - 1) * $salesHistoryStore.pagination.pageSize;
        await fetchTodaySales(
          currentUser.sucursal_id,
          tipo,
          currentSkip,
          $salesHistoryStore.pagination.pageSize,
          package_type,
          include_package_type
        );
      } else {
        // Use pagination for full history
        // Calculate skip from current page and pageSize
        const currentSkip = ($salesHistoryStore.pagination.page - 1) * $salesHistoryStore.pagination.pageSize;
        await fetchSales(
          currentUser.sucursal_id,
          undefined,
          undefined,
          tipo,
          currentSkip,
          $salesHistoryStore.pagination.pageSize,
          package_type,
          include_package_type
        );
      }
    }
  }

  async function handlePageChange(newPage: number) {
    setPage(newPage);
    await handleFilterChange();
  }

  async function handlePageSizeChange(newSize: number) {
    setPageSize(newSize);
    setPage(1); // Reset to page 1 when changing page size
    await handleFilterChange();
  }

  // Handle checkbox change explicitly to avoid reactive statement loops
  async function handleTodayOnlyChange() {
    // Reset to page 1 when toggling filter
    setPage(1);
    await handleFilterChange();
  }
</script>

<div class="sales-history-container">
  <div class="page-header">
    <h1 class="page-title">
      <FileText size={28} strokeWidth={1.5} />
      Historial de Ventas
    </h1>
    <div class="header-actions">
      <label class="filter-toggle">
        <input 
          type="checkbox" 
          bind:checked={showTodayOnly} 
          class="checkbox-input" 
          on:change={handleTodayOnlyChange}
        />
        <span class="checkbox-label">Solo Hoy</span>
      </label>
      <label class="page-size-selector">
        <span>Registros por página:</span>
        <select
          value={$salesHistoryStore.pagination.pageSize}
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

  {#if $salesHistoryStore.error}
    <ErrorBanner error={$salesHistoryStore.error} />
  {/if}

  {#if $salesHistoryStore.loading}
    <LoadingSpinner message="Cargando ventas..." />
  {:else if filteredSales.length === 0}
    <div class="empty-state">
      <p>No hay ventas registradas</p>
    </div>
  {:else}
    <!-- Desktop: Grid layout (table-like) -->
    <div class="sales-grid-container">
      <div class="grid-headers" style="grid-template-columns: {gridColumns};">
        {#each visibleColumns as column}
          <div class="grid-header">{column.label}</div>
        {/each}
      </div>
      <div class="sales-grid" style="grid-template-columns: {gridColumns};">
        {#each filteredSales as sale (sale.id)}
          <div class="sale-grid-item">
            {#each visibleColumns as column}
              {#if column.key === "actions"}
                <div class="grid-cell actions-cell">
                  <Button
                    variant="brutalist"
                    size="small"
                    on:click={() => handleViewDetails(sale.id)}
                  >
                    <Eye size={16} strokeWidth={1.5} />
                    Ver
                  </Button>
                  <Button
                    variant="brutalist"
                    size="small"
                    on:click={() => handlePrint(sale.id)}
                  >
                    <Printer size={16} strokeWidth={1.5} />
                    Imprimir
                  </Button>
                </div>
              {:else if column.key === "type"}
                <div class="grid-cell">
                  <span class="type-badge">{column.renderCell(sale)}</span>
                </div>
              {:else if column.key === "total"}
                <div class="grid-cell total-amount">{column.renderCell(sale)}</div>
              {:else if column.key === "phone"}
                <div class="grid-cell">
                  {#if column.renderCell(sale)}
                    <span class="phone-display">{column.renderCell(sale)}</span>
                  {:else}
                    <span class="empty">—</span>
                  {/if}
                </div>
              {:else if column.key === "children"}
                <div class="grid-cell">
                  {#if column.renderCell(sale)}
                    <span class="children-display">{column.renderCell(sale)}</span>
                  {:else}
                    <span class="empty">—</span>
                  {/if}
                </div>
              {:else if column.key === "scheduled_date"}
                <div class="grid-cell">
                  {#if column.renderCell(sale)}
                    <span class="scheduled-date-display">{column.renderCell(sale)}</span>
                  {:else}
                    <span class="empty">—</span>
                  {/if}
                </div>
              {:else}
                <div class="grid-cell">{column.renderCell(sale)}</div>
              {/if}
            {/each}
          </div>
        {/each}
      </div>
    </div>

    <!-- Mobile: Cards layout -->
    <div class="sales-cards">
      {#each $salesHistoryStore.list as sale (sale.id)}
        <div class="sale-card">
          <div class="sale-card-header">
            <h3 class="sale-card-title">{sale.payer.name || "N/A"}</h3>
            <span class="type-badge">{getSaleTypeLabel(sale.tipo)}</span>
          </div>
          <div class="sale-card-body">
            {#each visibleColumns as column}
              {#if column.key !== "actions" && column.key !== "type" && column.key !== "payer"}
                {#if column.key === "phone"}
                  {#if column.renderCell(sale)}
                    <div class="sale-card-row">
                      <span class="sale-card-label">{column.label}:</span>
                      <span class="sale-card-value">{column.renderCell(sale)}</span>
                    </div>
                  {/if}
                {:else if column.key === "children"}
                  {#if column.renderCell(sale)}
                    <div class="sale-card-row">
                      <span class="sale-card-label">{column.label}:</span>
                      <span class="sale-card-value children-list">{column.renderCell(sale)}</span>
                    </div>
                  {/if}
                {:else if column.key === "scheduled_date"}
                  {#if column.renderCell(sale)}
                    <div class="sale-card-row">
                      <span class="sale-card-label">{column.label}:</span>
                      <span class="sale-card-value scheduled-date-display">{column.renderCell(sale)}</span>
                    </div>
                  {/if}
                {:else if column.key === "total"}
                  <div class="sale-card-row">
                    <span class="sale-card-label">{column.label}:</span>
                    <span class="sale-card-value total-amount">{column.renderCell(sale)}</span>
                  </div>
                {:else}
                  <div class="sale-card-row">
                    <span class="sale-card-label">{column.label}:</span>
                    <span class="sale-card-value">{column.renderCell(sale)}</span>
                  </div>
                {/if}
              {/if}
            {/each}
          </div>
          <div class="sale-card-actions">
            <Button
              variant="brutalist"
              size="small"
              on:click={() => handleViewDetails(sale.id)}
            >
              <Eye size={16} strokeWidth={1.5} />
              Ver
            </Button>
            <Button
              variant="brutalist"
              size="small"
              on:click={() => handlePrint(sale.id)}
            >
              <Printer size={16} strokeWidth={1.5} />
              Imprimir
            </Button>
          </div>
        </div>
      {/each}
    </div>

    <!-- Pagination Controls -->
    {#if $salesHistoryStore.pagination.hasMore || $salesHistoryStore.pagination.page > 1}
      <div class="pagination-controls">
        <Button
          variant="brutalist"
          disabled={$salesHistoryStore.pagination.page === 1 || $salesHistoryStore.loading}
          on:click={() => handlePageChange($salesHistoryStore.pagination.page - 1)}
        >
          ← Anterior
        </Button>
        <span class="page-info">
          Página {$salesHistoryStore.pagination.page}
        </span>
        <Button
          variant="brutalist"
          disabled={!$salesHistoryStore.pagination.hasMore || $salesHistoryStore.loading}
          on:click={() => handlePageChange($salesHistoryStore.pagination.page + 1)}
        >
          Siguiente →
        </Button>
      </div>
    {/if}
  {/if}

  <!-- Sale Details Modal / Ticket Preview -->
  {#if showSaleDetails && selectedSale}
    <div class="modal-overlay" on:click={() => (showSaleDetails = false)}>
      <div class="modal-content ticket-modal" on:click|stopPropagation>
        <div class="modal-header">
          <h2>Vista Previa del Ticket</h2>
          <button class="close-button" on:click={() => (showSaleDetails = false)}>×</button>
        </div>
        
        {#if loadingTicket}
          <div class="ticket-loading">
            <LoadingSpinner />
            <p>Cargando ticket...</p>
          </div>
        {:else if ticketHtml}
          <div class="ticket-preview">
            {@html ticketHtml}
          </div>
        {:else}
          <!-- Fallback: Show sale details if ticket HTML is not available -->
          <div class="sale-details">
            <div class="detail-row">
              <span class="detail-label">ID:</span>
              <span class="detail-value">{selectedSale.id}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">Fecha:</span>
              <span class="detail-value">{formatDate(selectedSale.timestamps.created_at)}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">Tipo:</span>
              <span class="detail-value">{getSaleTypeLabel(selectedSale.tipo)}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">Pagador:</span>
              <span class="detail-value">{selectedSale.payer.name || "N/A"}</span>
            </div>
            {#each visibleColumns as column}
              {#if column.key === "phone" && column.show(saleType, packageType)}
                {#if column.renderCell(selectedSale)}
                  <div class="detail-row">
                    <span class="detail-label">{column.label}:</span>
                    <span class="detail-value">{column.renderCell(selectedSale)}</span>
                  </div>
                {/if}
              {:else if column.key === "scheduled_date" && column.show(saleType, packageType)}
                {#if column.renderCell(selectedSale)}
                  <div class="detail-row">
                    <span class="detail-label">{column.label}:</span>
                    <span class="detail-value">{column.renderCell(selectedSale)}</span>
                  </div>
                {/if}
              {:else if column.key === "children"}
                {#if column.renderCell(selectedSale)}
                  <div class="detail-row">
                    <span class="detail-label">Niños:</span>
                    <span class="detail-value children-list">{column.renderCell(selectedSale)}</span>
                  </div>
                {/if}
              {/if}
            {/each}
            <div class="detail-row">
              <span class="detail-label">Subtotal:</span>
              <span class="detail-value">{formatPrice(selectedSale.pricing.subtotal_cents)}</span>
            </div>
            {#if selectedSale.pricing.discount_cents > 0}
              <div class="detail-row">
                <span class="detail-label">Descuento:</span>
                <span class="detail-value">{formatPrice(selectedSale.pricing.discount_cents)}</span>
              </div>
            {/if}
            <div class="detail-row total">
              <span class="detail-label">Total:</span>
              <span class="detail-value">{formatPrice(selectedSale.pricing.total_cents)}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">Método de Pago:</span>
              <span class="detail-value">{selectedSale.payment.method}</span>
            </div>
          </div>
        {/if}
        
        <div class="modal-actions">
          <Button variant="primary" on:click={() => handlePrint(selectedSale.id)}>
            <Printer size={18} strokeWidth={2} />
            <span>Imprimir Ticket</span>
          </Button>
          <Button variant="secondary" on:click={() => (showSaleDetails = false)}>
            Cerrar
          </Button>
        </div>
      </div>
    </div>
  {/if}
</div>

<style>
  .sales-history-container {
    padding: var(--spacing-xl);
  }

  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--spacing-xl);
    flex-wrap: wrap;
    gap: var(--spacing-md);
  }

  .page-title {
    font-family: var(--font-primary);
    font-size: var(--text-3xl);
    font-weight: 700;
    color: var(--text-primary);
    margin: 0;
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    
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

  .page-title :global(svg) {
    flex-shrink: 0;
    color: var(--accent-primary);
    filter: drop-shadow(0 0 8px var(--glow-primary));
  }

  .header-actions {
    display: flex;
    gap: var(--spacing-md);
    align-items: center;
  }

  .filter-toggle {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    color: var(--text-primary);
    cursor: pointer;
    padding: var(--spacing-sm) var(--spacing-md);
    background: var(--theme-bg-elevated);
    border: 2px solid var(--accent-primary);
    border-radius: var(--radius-md);
    box-shadow: 3px 3px 0px 0px var(--accent-primary);
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    font-weight: 600;
  }

  .filter-toggle:hover {
    box-shadow: none;
    border-width: 3px;
    transform: translate(3px, 3px);
    background: var(--accent-primary);
    color: var(--text-inverse);
  }

  .filter-toggle:active {
    transform: translate(2px, 2px);
    transition-duration: 0.1s;
  }

  .checkbox-input {
    width: 18px;
    height: 18px;
    cursor: pointer;
    accent-color: var(--accent-primary);
  }

  .checkbox-label {
    font-weight: 500;
    user-select: none;
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
  .sales-grid-container {
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
    box-sizing: border-box; /* Ensure consistent box model */
  }

  /* Grid Headers - Desktop only */
  .grid-headers {
    display: none; /* Hidden on mobile */
  }

  /* Sales Grid - Desktop table-like layout */
  .sales-grid {
    display: grid;
    grid-template-columns: 1fr; /* Mobile: single column */
    gap: 0;
    width: 100%;
  }

  /* Sale Grid Item - Desktop: transparent container */
  .sale-grid-item {
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

  /* Desktop: Grid layout with proper column distribution - TABLE-LIKE */
  @media (min-width: 769px) {
    /* Show headers on desktop - grid-template-columns is set dynamically via style binding */
    .grid-headers {
      display: grid;
      gap: 0;
      background: linear-gradient(135deg, var(--theme-bg-secondary) 0%, var(--theme-bg-elevated) 100%);
      border-bottom: 2px solid var(--border-primary);
      position: sticky;
      top: 0;
      z-index: 10;
      box-sizing: border-box; /* Ensure consistent box model */
      min-width: 0; /* Prevent overflow */
    }

    /* Grid header cell */
    .grid-header {
      padding: 0.875rem 0.625rem; /* Match grid-cell padding for perfect alignment */
      display: flex;
      align-items: center;
      font-weight: 700;
      font-size: 0.75rem;
      color: var(--text-secondary);
      text-transform: uppercase;
      letter-spacing: 0.1em;
      white-space: nowrap;
      text-align: left;
      border-right: 1px solid var(--border-primary); /* Match grid-cell border for perfect alignment */
      box-sizing: border-box; /* Ensure border is included in width calculation */
      min-width: 0; /* Prevent overflow */
      overflow: hidden; /* Prevent content overflow */
    }

    .grid-header:last-child {
      border-right: none; /* Remove border from last column to match grid-cell */
    }

    /* Sales grid - grid-template-columns is set dynamically via style binding */
    .sales-grid {
      gap: 0; /* No gaps to simulate table */
      box-sizing: border-box; /* Ensure consistent box model */
      min-width: 0; /* Prevent overflow */
    }

    /* Sale grid item - display: contents makes it transparent */
    .sale-grid-item {
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
      box-sizing: border-box; /* Ensure border is included in width calculation */
      min-width: 0; /* Prevent overflow */
      overflow: hidden; /* Prevent content overflow */
    }

    .grid-cell:last-child {
      border-right: none;
    }

    /* Row hover effect */
    .sale-grid-item:hover .grid-cell {
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
    .sales-grid-container {
      display: none !important; /* Hide grid on mobile */
    }

    .sales-cards {
      display: grid !important;
      grid-template-columns: 1fr;
      gap: var(--spacing-md);
    }
  }

  /* Desktop: Hide cards, show grid */
  @media (min-width: 769px) {
    .sales-cards {
      display: none !important; /* Hide cards on desktop */
    }
  }

  /* Sales Cards - Mobile layout */
  .sales-cards {
    display: none; /* Hidden by default (desktop) */
  }

  .sale-card {
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

  .sale-card:hover {
    transform: translateY(-4px);
    border-color: rgba(0, 147, 247, 0.5);
    box-shadow: 
      0 12px 32px rgba(0, 0, 0, 0.2),
      0 0 30px var(--glow-primary),
      0 0 40px var(--glow-secondary),
      inset 0 1px 0 rgba(255, 255, 255, 0.1);
  }

  .sale-card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--spacing-md);
    padding-bottom: var(--spacing-md);
    border-bottom: 1px solid var(--border-primary);
  }

  .sale-card-title {
    font-size: var(--text-lg);
    font-weight: 700;
    color: var(--text-primary);
    margin: 0;
  }

  .sale-card-body {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-sm);
    margin-bottom: var(--spacing-md);
  }

  .sale-card-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .sale-card-label {
    font-weight: 600;
    color: var(--text-secondary);
    font-size: var(--text-sm);
  }

  .sale-card-value {
    color: var(--text-primary);
    font-size: var(--text-sm);
  }

  .sale-card-actions {
    display: flex;
    gap: var(--spacing-sm);
    flex-wrap: wrap;
  }

  /* Legacy table styles - kept for compatibility */
  .sales-table-container {
    overflow-x: auto;
    background: var(--theme-bg-card);
    backdrop-filter: blur(16px) saturate(150%);
    -webkit-backdrop-filter: blur(16px) saturate(150%);
    border: 1px solid var(--border-primary);
    border-radius: 16px;
    box-shadow: 
      0 8px 24px rgba(0, 0, 0, 0.15),
      0 0 20px var(--glow-primary),
      inset 0 1px 0 rgba(255, 255, 255, 0.05);
    margin-bottom: var(--spacing-xl);
    display: none; /* Hidden - using grid instead */
  }

  .sales-table {
    width: 100%;
    border-collapse: collapse;
    background: transparent;
  }

  .sales-table thead {
    background: linear-gradient(135deg, var(--theme-bg-secondary) 0%, var(--theme-bg-elevated) 100%);
    position: sticky;
    top: 0;
    z-index: 10;
  }

  .sales-table th {
    padding: 0.75rem 0.625rem;
    text-align: left;
    font-weight: 700;
    font-size: 0.75rem;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.1em;
    white-space: nowrap;
    border-bottom: 2px solid var(--border-primary);
  }

  .sales-table tbody tr {
    background: var(--theme-bg-elevated);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    border-bottom: 1px solid var(--border-primary);
  }

  .sales-table tbody tr:hover {
    background: var(--theme-bg-secondary);
    transform: translateY(-2px);
    box-shadow: 
      0 4px 12px rgba(0, 0, 0, 0.1),
      0 0 10px var(--glow-primary);
  }

  .sales-table td {
    padding: 0.875rem 0.625rem;
    font-size: 0.9375rem;
    line-height: 1.5;
    color: var(--text-primary);
    border-right: 1px solid var(--border-primary);
  }

  .sales-table td:last-child {
    border-right: none;
  }

  .type-badge {
    display: inline-block;
    padding: var(--spacing-xs) var(--spacing-sm);
    border-radius: var(--radius-sm);
    font-size: var(--text-sm);
    font-weight: 600;
    background: var(--theme-bg-card);
    backdrop-filter: blur(8px) saturate(150%);
    -webkit-backdrop-filter: blur(8px) saturate(150%);
    border: 1px solid var(--border-primary);
    color: var(--text-primary);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }

  .total-amount {
    font-weight: 700;
    font-size: var(--text-base);
    color: var(--accent-success);
    text-shadow: 0 0 10px var(--glow-success);
  }

  .actions {
    display: flex;
    gap: var(--spacing-sm);
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

  .ticket-modal {
    max-width: 500px;
    width: 95%;
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
      0 2px 4px rgba(0, 0, 0, 0.1),
      inset 0 1px 0 rgba(255, 255, 255, 0.1);
  }

  .close-button:hover {
    background: var(--accent-danger);
    border-color: var(--accent-danger);
    color: #ffffff;
    box-shadow: 
      0 4px 8px rgba(211, 5, 84, 0.3),
      0 0 10px var(--glow-danger),
      inset 0 1px 0 rgba(255, 255, 255, 0.2);
    transform: scale(1.05);
  }

  .close-button:active {
    transform: scale(0.95);
  }

  .ticket-loading {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: var(--spacing-xl);
    gap: var(--spacing-md);
    background: var(--theme-bg-card);
    backdrop-filter: blur(8px) saturate(150%);
    -webkit-backdrop-filter: blur(8px) saturate(150%);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
    box-shadow: 
      0 4px 12px rgba(0, 0, 0, 0.1),
      0 0 10px var(--glow-primary);
  }

  .ticket-loading p {
    color: var(--text-primary);
    font-size: var(--text-base);
    font-weight: 500;
  }

  .ticket-preview {
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(8px) saturate(150%);
    -webkit-backdrop-filter: blur(8px) saturate(150%);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
    padding: var(--spacing-lg);
    margin-bottom: var(--spacing-lg);
    box-shadow: 
      0 4px 12px rgba(0, 0, 0, 0.15),
      0 0 10px var(--glow-primary),
      inset 0 1px 0 rgba(255, 255, 255, 0.1);
    overflow-x: auto;
  }

  .ticket-preview :global(*) {
    max-width: 100%;
  }

  .modal-content h2 {
    margin: 0 0 var(--spacing-lg) 0;
    color: var(--text-primary);
    font-family: var(--font-primary);
    font-size: var(--text-2xl);
    font-weight: 700;
    
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

  .sale-details {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-md);
  }

  .detail-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: var(--spacing-sm) 0;
    border-bottom: 1px solid var(--border-primary);
  }

  .detail-row.total {
    border-top: 2px solid var(--accent-primary);
    border-bottom: 2px solid var(--accent-primary);
    padding: var(--spacing-md) 0;
    font-weight: 700;
    background: rgba(0, 147, 247, 0.05);
    border-radius: var(--radius-md);
    padding: var(--spacing-md);
    margin: var(--spacing-sm) 0;
  }

  .detail-row.total .detail-value {
    color: var(--accent-primary);
    text-shadow: 0 0 10px var(--glow-primary);
    font-size: var(--text-xl);
  }

  .detail-label {
    font-weight: 600;
    color: var(--text-secondary);
  }

  .detail-value {
    color: var(--text-primary);
    font-family: var(--font-mono);
  }

  .detail-value.children-list {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
    max-width: 100%;
    font-family: var(--font-body);
  }

  .children-display {
    font-size: var(--text-sm);
    color: var(--text-primary);
    line-height: 1.4;
    display: flex;
    flex-wrap: wrap;
    gap: 4px 8px;
    max-width: 200px;
  }

  .children-display.empty {
    color: var(--text-muted);
    font-style: italic;
  }

  .phone-display {
    color: var(--text-primary);
    font-weight: 500;
  }

  .scheduled-date-display {
    color: var(--text-primary);
    font-weight: 500;
  }

  .empty {
    color: var(--text-secondary);
    font-style: italic;
  }

  .sale-card-value.children-list {
    display: flex;
    flex-wrap: wrap;
    gap: 4px 8px;
    justify-content: flex-end;
    text-align: right;
    max-width: 100%;
  }

  .modal-actions {
    display: flex;
    gap: var(--spacing-md);
    justify-content: flex-end;
    margin-top: var(--spacing-xl);
    padding-top: var(--spacing-lg);
    border-top: 1px solid var(--border-primary);
  }

  .modal-actions :global(.btn) {
    min-width: 140px;
    height: 48px;
    font-size: 16px;
    font-weight: 600;
  }

  @media (max-width: 768px) {
    .sales-history-container {
      padding: var(--spacing-md);
    }

    .page-header {
      flex-direction: column;
      align-items: stretch;
      gap: var(--spacing-md);
    }

    .page-title {
      font-size: var(--text-2xl);
      text-align: center;
    }

    .page-title :global(svg) {
      margin-right: 8px;
    }

    .header-actions {
      flex-direction: column;
      width: 100%;
      gap: var(--spacing-sm);
    }

    .filter-toggle,
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

    .sale-card-actions {
      flex-direction: column;
    }

    .sale-card-actions :global(.btn-brutalist) {
      width: 100%;
      min-height: 48px;
      justify-content: center;
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
    .sales-table th,
    .sales-table td {
      padding: var(--spacing-sm) var(--spacing-xs);
      font-size: var(--text-sm);
    }
  }

  /* Prevent hover transform issues on touch devices */
  @media (hover: none) and (pointer: coarse) {
    .sale-grid-item:hover .grid-cell {
      transform: none;
      box-shadow: none;
    }

    .sale-card:hover {
      transform: none;
      box-shadow: 
        0 8px 24px rgba(0, 0, 0, 0.15),
        0 0 20px var(--glow-primary),
        inset 0 1px 0 rgba(255, 255, 255, 0.05);
    }

    .filter-toggle:hover,
    .page-size-selector:hover {
      transform: none;
      box-shadow: 3px 3px 0px 0px var(--accent-primary);
      border-width: 2px;
      background: var(--theme-bg-elevated);
      color: var(--text-primary);
    }
  }
</style>




















