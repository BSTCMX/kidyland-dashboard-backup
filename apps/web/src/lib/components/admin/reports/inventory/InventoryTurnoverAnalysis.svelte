<script lang="ts">
  /**
   * InventoryTurnoverAnalysis - Analysis of inventory turnover rates.
   * 
   * Displays turnover rate, days on hand, and categorizes products as fast/slow/normal movers.
   */
  import { onMount } from 'svelte';
  import { fetchInventoryTurnover, type InventoryTurnoverReport, type InventoryTurnoverProduct } from '$lib/stores/reports';
  import LoadingSpinner from '$lib/components/admin/LoadingSpinner.svelte';
  import ErrorBanner from '$lib/components/admin/ErrorBanner.svelte';
  import { TrendingUp, TrendingDown, Minus } from 'lucide-svelte';

  export let sucursalId: string | null = null;
  export let startDate: string;
  export let endDate: string;

  let turnoverData: InventoryTurnoverReport | null = null;
  let loading = false;
  let error: string | null = null;

  let previousSucursalId: string | null = null;
  let previousStartDate: string | null = null;
  let previousEndDate: string | null = null;

  async function loadTurnoverData() {
    loading = true;
    error = null;

    try {
      const report = await fetchInventoryTurnover(sucursalId, startDate, endDate);
      turnoverData = report;
    } catch (err: any) {
      console.error('Error loading turnover data:', err);
      error = err.message || 'Error al cargar análisis de rotación';
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
      loadTurnoverData();
    }
  }

  onMount(() => {
    loadTurnoverData();
  });

  function getCategoryColor(category: string): string {
    if (category === "fast") return "var(--accent-success, #10B981)";
    if (category === "slow") return "var(--accent-error, #EF4444)";
    return "var(--text-secondary)";
  }

  function getCategoryIcon(category: string) {
    if (category === "fast") return TrendingUp;
    if (category === "slow") return TrendingDown;
    return Minus;
  }
</script>

<div class="inventory-turnover">
  {#if loading}
    <LoadingSpinner />
  {:else if error}
    <ErrorBanner {error} />
  {:else if turnoverData}
    <div class="turnover-container">
      <h3 class="section-title">Análisis de Rotación de Inventario</h3>
      
      <!-- Summary Cards -->
      <div class="summary-grid">
        <div class="summary-card">
          <h4 class="summary-title">Total Productos</h4>
          <div class="summary-value">{turnoverData.summary.total_products}</div>
        </div>
        <div class="summary-card">
          <h4 class="summary-title">Rotación Promedio</h4>
          <div class="summary-value">{turnoverData.summary.average_turnover.toFixed(2)}x</div>
        </div>
        <div class="summary-card fast">
          <h4 class="summary-title">Fast Movers</h4>
          <div class="summary-value">{turnoverData.summary.fast_movers}</div>
        </div>
        <div class="summary-card slow">
          <h4 class="summary-title">Slow Movers</h4>
          <div class="summary-value">{turnoverData.summary.slow_movers}</div>
        </div>
        <div class="summary-card">
          <h4 class="summary-title">Normal Movers</h4>
          <div class="summary-value">{turnoverData.summary.normal_movers}</div>
        </div>
      </div>

      <!-- Products Table -->
      <div class="products-table-section">
        <h4 class="table-title">Productos por Rotación</h4>
        <div class="table-container">
          <table class="turnover-table">
            <thead>
              <tr>
                <th>Producto</th>
                <th>Stock Actual</th>
                <th>Cantidad Vendida</th>
                <th>Tasa de Rotación</th>
                <th>Días en Inventario</th>
                <th>Categoría</th>
              </tr>
            </thead>
            <tbody>
              {#each turnoverData.products as product (product.product_id)}
                {@const CategoryIcon = getCategoryIcon(product.category)}
                {@const categoryColor = getCategoryColor(product.category)}
                <tr>
                  <td class="product-name">{product.product_name}</td>
                  <td>{product.current_stock}</td>
                  <td>{product.quantity_sold}</td>
                  <td class="turnover-rate">{product.turnover_rate.toFixed(2)}x</td>
                  <td class="days-on-hand">{product.days_on_hand.toFixed(1)} días</td>
                  <td>
                    <span class="category-badge" style="color: {categoryColor}">
                      <svelte:component this={CategoryIcon} size={14} />
                      <span>{product.category === "fast" ? "Rápido" : product.category === "slow" ? "Lento" : "Normal"}</span>
                    </span>
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
      <p>No hay datos de rotación disponibles.</p>
    </div>
  {/if}
</div>

<style>
  .inventory-turnover {
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
    margin: 0 0 var(--spacing-lg, 1.5rem) 0;
  }

  .summary-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
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

  .summary-card.fast {
    border-left: 4px solid var(--accent-success, #10B981);
  }

  .summary-card.slow {
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

  .turnover-table {
    width: 100%;
    border-collapse: collapse;
    font-size: var(--text-sm, 0.875rem);
  }

  .turnover-table thead {
    background: var(--theme-bg-secondary);
    border-bottom: 2px solid var(--border-primary);
  }

  .turnover-table th {
    padding: var(--spacing-sm, 0.75rem);
    text-align: left;
    font-weight: 600;
    color: var(--text-primary);
  }

  .turnover-table td {
    padding: var(--spacing-sm, 0.75rem);
    border-bottom: 1px solid var(--border-primary);
    color: var(--text-secondary);
  }

  .turnover-table tbody tr:hover {
    background: var(--theme-bg-secondary);
  }

  .product-name {
    font-weight: 500;
    color: var(--text-primary);
  }

  .turnover-rate {
    font-weight: 600;
    color: var(--text-primary);
  }

  .days-on-hand {
    color: var(--text-secondary);
  }

  .category-badge {
    display: inline-flex;
    align-items: center;
    gap: var(--spacing-xs, 0.5rem);
    font-size: var(--text-xs, 0.75rem);
    font-weight: 500;
  }

  .placeholder-content {
    text-align: center;
    padding: var(--spacing-xl, 2rem);
    color: var(--text-secondary);
    font-style: italic;
  }

  @media (max-width: 768px) {
    .summary-grid {
      grid-template-columns: repeat(2, 1fr);
    }

    .table-container {
      font-size: var(--text-xs, 0.75rem);
    }

    .turnover-table th,
    .turnover-table td {
      padding: var(--spacing-xs, 0.5rem);
    }
  }
</style>



