<script lang="ts">
  /**
   * InventoryMovementAnalysis - Fast and slow movers analysis.
   * 
   * Displays products categorized by movement rate (fast, slow, normal).
   */
  import { onMount } from 'svelte';
  import { fetchInventoryMovement, type InventoryMovementReport } from '$lib/stores/reports';
  import LoadingSpinner from '$lib/components/admin/LoadingSpinner.svelte';
  import ErrorBanner from '$lib/components/admin/ErrorBanner.svelte';
  import { TrendingUp, TrendingDown, Minus } from 'lucide-svelte';

  export let sucursalId: string | null = null;
  export let startDate: string;
  export let endDate: string;

  let movementData: InventoryMovementReport | null = null;
  let loading = false;
  let error: string | null = null;

  let previousSucursalId: string | null = null;
  let previousStartDate: string | null = null;
  let previousEndDate: string | null = null;

  async function loadMovementData() {
    loading = true;
    error = null;

    try {
      const report = await fetchInventoryMovement(sucursalId, startDate, endDate);
      movementData = report;
    } catch (err: any) {
      console.error('Error loading movement data:', err);
      error = err.message || 'Error al cargar análisis de movimiento';
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
      loadMovementData();
    }
  }

  onMount(() => {
    loadMovementData();
  });
</script>

<div class="inventory-movement">
  {#if loading}
    <LoadingSpinner />
  {:else if error}
    <ErrorBanner {error} />
  {:else if movementData}
    <div class="movement-container">
      <h3 class="section-title">Análisis de Movimiento de Productos</h3>
      
      <!-- Summary Cards -->
      <div class="summary-grid">
        <div class="summary-card">
          <h4 class="summary-title">Fast Movers</h4>
          <div class="summary-value fast">{movementData.summary.fast_movers}</div>
        </div>
        <div class="summary-card">
          <h4 class="summary-title">Slow Movers</h4>
          <div class="summary-value slow">{movementData.summary.slow_movers}</div>
        </div>
        <div class="summary-card">
          <h4 class="summary-title">Normal Movers</h4>
          <div class="summary-value">{movementData.summary.normal_movers}</div>
        </div>
      </div>

      <!-- Fast Movers -->
      {#if movementData.fast_movers && movementData.fast_movers.length > 0}
        <div class="movers-section">
          <h4 class="movers-title">
            <TrendingUp size={20} />
            Fast Movers (Alta Rotación)
          </h4>
          <div class="movers-list">
            {#each movementData.fast_movers as product (product.product_id)}
              <div class="mover-item fast">
                <div class="mover-name">{product.product_name}</div>
                <div class="mover-metrics">
                  <span class="mover-metric">Rotación: {product.turnover_rate.toFixed(2)}x</span>
                  <span class="mover-metric">Días: {product.days_on_hand.toFixed(1)}</span>
                </div>
              </div>
            {/each}
          </div>
        </div>
      {/if}

      <!-- Slow Movers -->
      {#if movementData.slow_movers && movementData.slow_movers.length > 0}
        <div class="movers-section">
          <h4 class="movers-title">
            <TrendingDown size={20} />
            Slow Movers (Baja Rotación)
          </h4>
          <div class="movers-list">
            {#each movementData.slow_movers as product (product.product_id)}
              <div class="mover-item slow">
                <div class="mover-name">{product.product_name}</div>
                <div class="mover-metrics">
                  <span class="mover-metric">Rotación: {product.turnover_rate.toFixed(2)}x</span>
                  <span class="mover-metric">Días: {product.days_on_hand.toFixed(1)}</span>
                </div>
              </div>
            {/each}
          </div>
        </div>
      {/if}
    </div>
  {:else}
    <div class="placeholder-content">
      <p>No hay datos de movimiento disponibles.</p>
    </div>
  {/if}
</div>

<style>
  .inventory-movement {
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

  .summary-value.fast {
    color: var(--accent-success, #10B981);
  }

  .summary-value.slow {
    color: var(--accent-error, #EF4444);
  }

  .movers-section {
    margin-top: var(--spacing-lg, 1.5rem);
  }

  .movers-title {
    font-size: var(--text-lg, 1.125rem);
    font-weight: 600;
    color: var(--text-primary);
    margin: 0 0 var(--spacing-md, 1rem) 0;
    display: flex;
    align-items: center;
    gap: var(--spacing-xs, 0.5rem);
  }

  .movers-list {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
    gap: var(--spacing-sm, 0.75rem);
  }

  .mover-item {
    background: var(--theme-bg-secondary);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md, 8px);
    padding: var(--spacing-sm, 0.75rem);
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xs, 0.5rem);
  }

  .mover-item.fast {
    border-left: 4px solid var(--accent-success, #10B981);
  }

  .mover-item.slow {
    border-left: 4px solid var(--accent-error, #EF4444);
  }

  .mover-name {
    font-weight: 600;
    color: var(--text-primary);
    font-size: var(--text-base, 1rem);
  }

  .mover-metrics {
    display: flex;
    gap: var(--spacing-md, 1rem);
    font-size: var(--text-sm, 0.875rem);
    color: var(--text-secondary);
  }

  .mover-metric {
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
    .movers-list {
      grid-template-columns: 1fr;
    }
  }
</style>



