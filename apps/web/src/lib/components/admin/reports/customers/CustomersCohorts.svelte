<script lang="ts">
  /**
   * CustomersCohorts - Cohort analysis component.
   */
  import { onMount } from 'svelte';
  import { get } from '@kidyland/utils/api';
  import LoadingSpinner from '$lib/components/admin/LoadingSpinner.svelte';
  import ErrorBanner from '$lib/components/admin/ErrorBanner.svelte';

  export let sucursalId: string | null = null;
  export let startDate: string | null = null;
  export let endDate: string | null = null;

  interface CohortPeriod {
    period: string;
    period_index: number;
    active_customers: number;
    retention_rate: number;
  }

  interface Cohort {
    cohort_period: string;
    cohort_size: number;
    periods: CohortPeriod[];
  }

  interface CohortAnalysis {
    cohorts: Cohort[];
    summary: {
      total_cohorts: number;
      average_retention: number;
    };
  }

  let loading = true;
  let error: string | null = null;
  let cohortData: CohortAnalysis | null = null;
  let cohortType: 'monthly' | 'weekly' | 'daily' = 'monthly';

  async function fetchCohorts() {
    loading = true;
    error = null;

    try {
      const params = new URLSearchParams();
      if (sucursalId) params.append('sucursal_id', sucursalId);
      if (startDate) params.append('start_date', startDate);
      if (endDate) params.append('end_date', endDate);
      params.append('cohort_type', cohortType);

      cohortData = await get<CohortAnalysis>(`/reports/customers/cohorts?${params.toString()}`);
    } catch (err: any) {
      error = err.message || 'Error al cargar análisis de cohortes';
    } finally {
      loading = false;
    }
  }

  function handleCohortTypeChange(event: Event) {
    const target = event.target as HTMLSelectElement;
    if (target) {
      cohortType = target.value as 'monthly' | 'weekly' | 'daily';
      fetchCohorts();
    }
  }

  // Track previous params to detect changes
  let previousSucursalId: string | null = null;
  let previousStartDate: string | null = null;
  let previousEndDate: string | null = null;
  
  // Fetch when params change
  $: {
    const paramsChanged = 
      sucursalId !== previousSucursalId ||
      startDate !== previousStartDate ||
      endDate !== previousEndDate;
    
    if (paramsChanged) {
      previousSucursalId = sucursalId;
      previousStartDate = startDate;
      previousEndDate = endDate;
      fetchCohorts();
    }
  }

  onMount(() => {
    fetchCohorts();
  });
</script>

<div class="customers-cohorts-container">
  <div class="cohorts-header">
    <h3 class="cohorts-title">Análisis de Cohortes</h3>
    <div class="cohorts-controls">
      <label class="control-label">Tipo de Cohorte:</label>
      <select
        class="cohort-type-select"
        value={cohortType}
        on:change={handleCohortTypeChange}
      >
        <option value="monthly">Mensual</option>
        <option value="weekly">Semanal</option>
        <option value="daily">Diario</option>
      </select>
    </div>
  </div>

  {#if loading}
    <LoadingSpinner />
  {:else if error}
    <ErrorBanner {error} />
  {:else if cohortData && cohortData.cohorts.length > 0}
    <div class="cohorts-summary">
      <div class="summary-card">
        <span class="summary-label">Total de Cohortes:</span>
        <span class="summary-value">{cohortData.summary.total_cohorts}</span>
      </div>
      <div class="summary-card">
        <span class="summary-label">Retención Promedio:</span>
        <span class="summary-value">{cohortData.summary.average_retention}%</span>
      </div>
    </div>

    <div class="cohorts-table-container">
      <table class="cohorts-table">
        <thead>
          <tr>
            <th>Cohorte</th>
            <th>Tamaño</th>
            <th>Períodos</th>
          </tr>
        </thead>
        <tbody>
          {#each cohortData.cohorts as cohort}
            <tr>
              <td class="cohort-period">{cohort.cohort_period}</td>
              <td class="cohort-size">{cohort.cohort_size}</td>
              <td class="cohort-periods">
                {#if cohort.periods.length > 0}
                  <div class="periods-list">
                    {#each cohort.periods.slice(0, 6) as period}
                      <div class="period-item">
                        <span class="period-label">{period.period}:</span>
                        <span class="period-value">{period.active_customers} ({period.retention_rate}%)</span>
                      </div>
                    {/each}
                    {#if cohort.periods.length > 6}
                      <div class="more-periods">+{cohort.periods.length - 6} períodos más</div>
                    {/if}
                  </div>
                {:else}
                  <span class="no-periods">Sin datos de períodos</span>
                {/if}
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {:else}
    <div class="empty-state">
      <p>No hay datos disponibles para el análisis de cohortes.</p>
    </div>
  {/if}
</div>

<style>
  .customers-cohorts-container {
    width: 100%;
  }

  .cohorts-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--spacing-lg);
    padding: var(--spacing-md);
    background: var(--theme-bg-elevated);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
  }

  .cohorts-title {
    font-size: var(--text-xl);
    font-weight: 600;
    color: var(--text-primary);
    margin: 0;
  }

  .cohorts-controls {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
  }

  .control-label {
    font-size: var(--text-sm);
    color: var(--text-secondary);
    font-weight: 500;
  }

  .cohort-type-select {
    padding: var(--spacing-sm);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
    background: var(--theme-bg-card);
    color: var(--text-primary);
    font-size: var(--text-sm);
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .cohort-type-select:hover {
    border-color: var(--accent-primary);
  }

  .cohort-type-select:focus {
    outline: none;
    border-color: var(--accent-primary);
    box-shadow: 0 0 0 3px rgba(0, 147, 247, 0.1);
  }

  .cohorts-summary {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: var(--spacing-md);
    margin-bottom: var(--spacing-lg);
  }

  .summary-card {
    padding: var(--spacing-md);
    background: var(--theme-bg-card);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xs);
  }

  .summary-label {
    font-size: var(--text-sm);
    color: var(--text-secondary);
  }

  .summary-value {
    font-size: var(--text-xl);
    font-weight: 600;
    color: var(--text-primary);
  }

  .cohorts-table-container {
    overflow-x: auto;
    background: var(--theme-bg-card);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
  }

  .cohorts-table {
    width: 100%;
    border-collapse: collapse;
  }

  .cohorts-table thead {
    background: var(--theme-bg-elevated);
  }

  .cohorts-table th {
    padding: var(--spacing-md);
    text-align: left;
    font-size: var(--text-sm);
    font-weight: 600;
    color: var(--text-secondary);
    border-bottom: 2px solid var(--border-primary);
  }

  .cohorts-table td {
    padding: var(--spacing-md);
    border-bottom: 1px solid var(--border-primary);
    font-size: var(--text-sm);
    color: var(--text-primary);
  }

  .cohorts-table tbody tr:hover {
    background: var(--theme-bg-elevated);
  }

  .cohort-period {
    font-weight: 500;
  }

  .cohort-size {
    text-align: center;
    font-variant-numeric: tabular-nums;
  }

  .periods-list {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xs);
  }

  .period-item {
    display: flex;
    justify-content: space-between;
    font-size: var(--text-xs);
  }

  .period-label {
    color: var(--text-secondary);
  }

  .period-value {
    font-weight: 500;
    color: var(--text-primary);
  }

  .more-periods {
    font-size: var(--text-xs);
    color: var(--text-secondary);
    font-style: italic;
    margin-top: var(--spacing-xs);
  }

  .no-periods {
    color: var(--text-secondary);
    font-style: italic;
  }

  .empty-state {
    text-align: center;
    padding: var(--spacing-xl);
    color: var(--text-secondary);
  }

  @media (max-width: 768px) {
    .cohorts-header {
      flex-direction: column;
      align-items: flex-start;
      gap: var(--spacing-md);
    }

    .cohorts-table {
      font-size: var(--text-xs);
    }

    .cohorts-table th,
    .cohorts-table td {
      padding: var(--spacing-sm);
    }
  }
</style>



