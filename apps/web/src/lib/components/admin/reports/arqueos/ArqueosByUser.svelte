<script lang="ts">
  /**
   * ArqueosByUser - Analysis by user component.
   */
  import { onMount } from 'svelte';
  import { fetchArqueosByUser, formatPrice, type ArqueosByUserReport } from '$lib/stores/reports';
  import LoadingSpinner from '$lib/components/admin/LoadingSpinner.svelte';
  import ErrorBanner from '$lib/components/admin/ErrorBanner.svelte';

  export let sucursalId: string | null = null;
  export let startDate: string;
  export let endDate: string;
  export let selectedModule: "all" | "recepcion" | "kidibar" = "all";

  let userData: ArqueosByUserReport | null = null;
  let loading = false;
  let error: string | null = null;

  let previousSucursalId: string | null = null;
  let previousStartDate: string | null = null;
  let previousEndDate: string | null = null;
  let previousModule: "all" | "recepcion" | "kidibar" = "all";

  async function loadUserData() {
    loading = true;
    error = null;

    try {
      const report = await fetchArqueosByUser(sucursalId, startDate, endDate, selectedModule);
      userData = report;
    } catch (err: any) {
      console.error('Error loading user data:', err);
      error = err.message || 'Error al cargar análisis por usuario';
    } finally {
      loading = false;
    }
  }

  $: {
    const paramsChanged = 
      sucursalId !== previousSucursalId ||
      startDate !== previousStartDate ||
      endDate !== previousEndDate ||
      selectedModule !== previousModule;

    if (paramsChanged) {
      previousSucursalId = sucursalId;
      previousStartDate = startDate;
      previousEndDate = endDate;
      previousModule = selectedModule;
      loadUserData();
    }
  }

  onMount(() => {
    loadUserData();
  });
</script>

<div class="arqueos-by-user">
  {#if loading}
    <LoadingSpinner />
  {:else if error}
    <ErrorBanner {error} />
  {:else if userData && userData.users.length > 0}
    <div class="by-user-container">
      <h3 class="section-title">Análisis por Usuario</h3>
      <p class="section-description">Usuarios ordenados por total de diferencias absolutas</p>
      
      <div class="users-table">
        <div class="table-header">
          <div class="table-cell">Usuario</div>
          <div class="table-cell">Rol</div>
          <div class="table-cell">Arqueos</div>
          <div class="table-cell">Perfectos</div>
          <div class="table-cell">Discrepancias</div>
          <div class="table-cell">Tasa</div>
          <div class="table-cell">Diferencia Promedio</div>
          <div class="table-cell">Total Absoluto</div>
        </div>
        
        {#each userData.users as user (user.user_id)}
          <div class="table-row">
            <div class="table-cell user-name">{user.user_name}</div>
            <div class="table-cell user-role">{user.user_role}</div>
            <div class="table-cell">{user.arqueos_count}</div>
            <div class="table-cell perfect">{user.perfect_matches}</div>
            <div class="table-cell discrepancy">{user.discrepancies}</div>
            <div class="table-cell rate" class:high={user.discrepancy_rate > 20} class:medium={user.discrepancy_rate > 10 && user.discrepancy_rate <= 20}>
              {user.discrepancy_rate.toFixed(1)}%
            </div>
            <div class="table-cell" class:positive={user.avg_difference_cents > 0} class:negative={user.avg_difference_cents < 0}>
              {formatPrice(user.avg_difference_cents)}
            </div>
            <div class="table-cell total">{formatPrice(user.total_abs_difference_cents)}</div>
          </div>
        {/each}
      </div>
    </div>
  {:else}
    <div class="placeholder-content">
      <p>No hay datos de usuarios disponibles.</p>
    </div>
  {/if}
</div>

<style>
  .arqueos-by-user {
    width: 100%;
  }

  .by-user-container {
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
    font-size: var(--text-sm, 0.875rem);
    color: var(--text-secondary);
    margin: 0 0 var(--spacing-lg, 1.25rem) 0;
  }

  .users-table {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xs, 0.5rem);
    overflow-x: auto;
  }

  .table-header,
  .table-row {
    display: grid;
    grid-template-columns: 1.5fr 1fr 0.8fr 0.8fr 0.8fr 0.8fr 1.2fr 1.2fr;
    gap: var(--spacing-sm, 0.75rem);
    padding: var(--spacing-sm, 0.75rem);
    min-width: 800px;
  }

  .table-header {
    background: var(--theme-bg-secondary);
    border-bottom: 2px solid var(--border-primary);
    font-weight: 600;
    font-size: var(--text-sm, 0.875rem);
    color: var(--text-secondary);
    position: sticky;
    top: 0;
    z-index: 10;
  }

  .table-row {
    border-bottom: 1px solid var(--border-primary);
    transition: background 0.2s ease;
  }

  .table-row:hover {
    background: var(--theme-bg-secondary);
  }

  .table-cell {
    font-size: var(--text-sm, 0.875rem);
    color: var(--text-primary);
    display: flex;
    align-items: center;
  }

  .user-name {
    font-weight: 600;
  }

  .user-role {
    text-transform: capitalize;
    color: var(--text-secondary);
  }

  .perfect {
    color: var(--accent-success, #10B981);
  }

  .discrepancy {
    color: var(--accent-error, #EF4444);
  }

  .rate.high {
    color: var(--accent-error, #EF4444);
    font-weight: 700;
  }

  .rate.medium {
    color: var(--accent-warning, #F59E0B);
    font-weight: 600;
  }

  .total {
    font-weight: 600;
  }

  .positive {
    color: var(--accent-success, #10B981);
  }

  .negative {
    color: var(--accent-error, #EF4444);
  }

  .placeholder-content {
    padding: var(--spacing-2xl, 3rem);
    text-align: center;
    color: var(--text-secondary);
    font-style: italic;
  }

  @media (max-width: 768px) {
    .table-header,
    .table-row {
      grid-template-columns: 1fr;
      gap: var(--spacing-xs, 0.5rem);
    }

    .table-cell::before {
      content: attr(data-label);
      font-weight: 600;
      margin-right: var(--spacing-xs, 0.5rem);
      color: var(--text-secondary);
    }
  }
</style>



