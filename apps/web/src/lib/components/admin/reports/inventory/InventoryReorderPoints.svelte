<script lang="ts">
  /**
   * InventoryReorderPoints - Reorder points calculator and analysis.
   * 
   * Displays reorder points, safety stock, and days until stockout.
   */
  import { onMount } from 'svelte';
  import { fetchInventoryReorderPoints, formatPrice, type InventoryReorderPointsReport, type InventoryReorderPoint } from '$lib/stores/reports';
  import LoadingSpinner from '$lib/components/admin/LoadingSpinner.svelte';
  import ErrorBanner from '$lib/components/admin/ErrorBanner.svelte';
  import { AlertTriangle, CheckCircle } from 'lucide-svelte';

  export let sucursalId: string | null = null;
  export let startDate: string;
  export let endDate: string;

  let reorderData: InventoryReorderPointsReport | null = null;
  let loading = false;
  let error: string | null = null;

  let previousSucursalId: string | null = null;
  let previousStartDate: string | null = null;
  let previousEndDate: string | null = null;

  async function loadReorderData() {
    loading = true;
    error = null;

    try {
      const report = await fetchInventoryReorderPoints(sucursalId, startDate, endDate);
      reorderData = report;
    } catch (err: any) {
      console.error('Error loading reorder points data:', err);
      error = err.message || 'Error al cargar puntos de reorden';
    } finally {
      loading = false;
    }
  }

  $: {
    const paramsChanged = 
      sucursalId !== previousSucursalId ||
      startDate !== previousStartDate ||
      endDate !== previousEndDate;

    if (paramsChanged) {
      previousSucursalId = sucursalId;
      previousStartDate = startDate;
      previousEndDate = endDate;
      loadReorderData();
    }
  }

  onMount(() => {
    loadReorderData();
  });
</script>

<div class="inventory-reorder-points">
  {#if loading}
    <LoadingSpinner />
  {:else if error}
    <ErrorBanner {error} />
  {:else if reorderData}
    <div class="reorder-container">
      <h3 class="section-title">Puntos de Reorden</h3>
      <p class="section-description">
        Cálculo basado en ventas promedio diarias y tiempo de entrega ({reorderData.summary.default_lead_time_days} días).
      </p>
      
      <!-- Summary -->
      <div class="summary-grid">
        <div class="summary-card">
          <h4 class="summary-title">Total Productos</h4>
          <div class="summary-value">{reorderData.summary.total_products}</div>
        </div>
        <div class="summary-card urgent">
          <h4 class="summary-title">Requieren Reorden</h4>
          <div class="summary-value">{reorderData.summary.needs_reorder_count}</div>
        </div>
      </div>

      <!-- Products Table -->
      <div class="products-table-section">
        <h4 class="table-title">Productos por Punto de Reorden</h4>
        <div class="table-container">
          <table class="reorder-table">
            <thead>
              <tr>
                <th>Producto</th>
                <th>Stock Actual</th>
                <th>Ventas Diarias</th>
                <th>Punto de Reorden</th>
                <th>Stock de Seguridad</th>
                <th>Días hasta Agotarse</th>
                <th>Estado</th>
              </tr>
            </thead>
            <tbody>
              {#each reorderData.reorder_points as product (product.product_id)}
                <tr class:needs-reorder={product.needs_reorder}>
                  <td class="product-name">{product.product_name}</td>
                  <td>{product.current_stock}</td>
                  <td>{product.daily_sales_avg.toFixed(2)}</td>
                  <td class="reorder-point">{product.reorder_point}</td>
                  <td>{product.safety_stock}</td>
                  <td class:urgent={product.days_until_stockout < 7} class:warning={product.days_until_stockout >= 7 && product.days_until_stockout < 14}>
                    {product.days_until_stockout === 999 ? 'N/A' : product.days_until_stockout}
                  </td>
                  <td>
                    {#if product.needs_reorder}
                      <span class="status-badge urgent">
                        <AlertTriangle size={14} />
                        <span>Reorden Urgente</span>
                      </span>
                    {:else}
                      <span class="status-badge ok">
                        <CheckCircle size={14} />
                        <span>OK</span>
                      </span>
                    {/if}
                  </td>
                </tr>
              {/each}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  {:else}
    <div class="placeholder-content">
      <p>No hay datos de puntos de reorden disponibles.</p>
    </div>
  {/if}
</div>

<style>
  .inventory-reorder-points {
    background: var(--theme-bg-card);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-lg, 12px);
    padding: var(--spacing-lg, 1.5rem);
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  }

  .section-title {
    font-size: var(--text-xl, 1.25rem);
    font-weight: 700;
    color: var(--text-primary);
    margin: 0 0 var(--spacing-xs, 0.5rem) 0;
  }

  .section-description {
    font-size: var(--text-base, 1rem);
    color: var(--text-secondary);
    margin-bottom: var(--spacing-lg, 1.5rem);
  }

  .summary-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: var(--spacing-md, 1rem);
    margin-bottom: var(--spacing-lg, 1.5rem);
  }

  .summary-card {
    background: var(--theme-bg-secondary);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md, 8px);
    padding: var(--spacing-md, 1rem);
    text-align: center;
  }

  .summary-card.urgent {
    border-left: 4px solid var(--accent-error, #EF4444);
  }

  .summary-title {
    font-size: var(--text-sm, 0.875rem);
    color: var(--text-secondary);
    margin: 0 0 var(--spacing-xs, 0.5rem) 0;
  }

  .summary-value {
    font-size: var(--text-2xl, 1.5rem);
    font-weight: 700;
    color: var(--text-primary);
  }

  .products-table-section {
    margin-top: var(--spacing-lg, 1.5rem);
  }

  .table-title {
    font-size: var(--text-lg, 1.125rem);
    font-weight: 600;
    color: var(--text-primary);
    margin: 0 0 var(--spacing-md, 1rem) 0;
  }

  .table-container {
    overflow-x: auto;
  }

  .reorder-table {
    width: 100%;
    border-collapse: collapse;
    font-size: var(--text-sm, 0.875rem);
  }

  .reorder-table thead {
    background: var(--theme-bg-secondary);
    border-bottom: 2px solid var(--border-primary);
  }

  .reorder-table th {
    padding: var(--spacing-sm, 0.75rem);
    text-align: left;
    font-weight: 600;
    color: var(--text-primary);
  }

  .reorder-table td {
    padding: var(--spacing-sm, 0.75rem);
    border-bottom: 1px solid var(--border-primary);
    color: var(--text-secondary);
  }

  .reorder-table tbody tr:hover {
    background: var(--theme-bg-secondary);
  }

  .reorder-table tbody tr.needs-reorder {
    background: rgba(239, 68, 68, 0.1);
  }

  .product-name {
    font-weight: 500;
    color: var(--text-primary);
  }

  .reorder-point {
    font-weight: 600;
    color: var(--text-primary);
  }

  .urgent {
    color: var(--accent-error, #EF4444);
    font-weight: 600;
  }

  .warning {
    color: var(--accent-warning, #F59E0B);
    font-weight: 500;
  }

  .status-badge {
    display: inline-flex;
    align-items: center;
    gap: var(--spacing-xs, 0.5rem);
    font-size: var(--text-xs, 0.75rem);
    font-weight: 500;
    padding: var(--spacing-xs, 0.5rem) var(--spacing-sm, 0.75rem);
    border-radius: var(--radius-sm, 4px);
  }

  .status-badge.urgent {
    background: rgba(239, 68, 68, 0.1);
    color: var(--accent-error, #EF4444);
  }

  .status-badge.ok {
    background: rgba(16, 185, 129, 0.1);
    color: var(--accent-success, #10B981);
  }

  .placeholder-content {
    text-align: center;
    padding: var(--spacing-xl, 2rem);
    color: var(--text-secondary);
    font-style: italic;
  }

  @media (max-width: 768px) {
    .summary-grid {
      grid-template-columns: 1fr;
    }
    .table-container {
      font-size: var(--text-xs, 0.75rem);
    }
    .reorder-table th,
    .reorder-table td {
      padding: var(--spacing-xs, 0.5rem);
    }
  }
</style>



