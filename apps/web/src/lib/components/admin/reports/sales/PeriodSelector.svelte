<script lang="ts">
  /**
   * PeriodSelector - Interactive period selector for reports.
   * 
   * Allows users to quickly select common periods or custom date ranges.
   */
  import { Calendar, ChevronLeft, ChevronRight } from 'lucide-svelte';
  import { createEventDispatcher } from 'svelte';

  export let startDate: string;
  export let endDate: string;

  const dispatch = createEventDispatcher<{
    change: { startDate: string; endDate: string };
  }>();

  const presetPeriods = [
    { label: 'Hoy', days: 0 },
    { label: 'Últimos 7 días', days: 7 },
    { label: 'Últimos 30 días', days: 30 },
    { label: 'Últimos 90 días', days: 90 },
    { label: 'Este mes', custom: true },
    { label: 'Mes pasado', custom: true },
  ];

  function selectPreset(period: typeof presetPeriods[0]) {
    const today = new Date();
    let newStartDate: Date;
    let newEndDate: Date = new Date(today);

    if (period.label === 'Este mes') {
      newStartDate = new Date(today.getFullYear(), today.getMonth(), 1);
      newEndDate = new Date(today);
    } else if (period.label === 'Mes pasado') {
      const lastMonth = new Date(today.getFullYear(), today.getMonth() - 1, 1);
      newStartDate = lastMonth;
      newEndDate = new Date(today.getFullYear(), today.getMonth(), 0);
    } else {
      newStartDate = new Date(today);
      newStartDate.setDate(today.getDate() - period.days);
    }

    const startStr = newStartDate.toISOString().split('T')[0];
    const endStr = newEndDate.toISOString().split('T')[0];

    dispatch('change', { startDate: startStr, endDate: endStr });
  }

  function handleStartDateChange(event: Event) {
    const target = event.target as HTMLInputElement;
    if (target.value) {
      dispatch('change', { startDate: target.value, endDate });
    }
  }

  function handleEndDateChange(event: Event) {
    const target = event.target as HTMLInputElement;
    if (target.value) {
      dispatch('change', { startDate, endDate: target.value });
    }
  }
</script>

<div class="period-selector">
  <div class="selector-header">
    <Calendar size={18} strokeWidth={1.5} />
    <h4 class="selector-title">Período</h4>
  </div>

  <div class="preset-buttons">
    {#each presetPeriods as period}
      <button
        class="preset-button"
        on:click={() => selectPreset(period)}
        type="button"
      >
        {period.label}
      </button>
    {/each}
  </div>

  <div class="custom-dates">
    <div class="date-input-group">
      <label for="start-date-selector">Desde:</label>
      <input
        id="start-date-selector"
        type="date"
        bind:value={startDate}
        on:change={handleStartDateChange}
        class="date-input"
      />
    </div>
    <div class="date-input-group">
      <label for="end-date-selector">Hasta:</label>
      <input
        id="end-date-selector"
        type="date"
        bind:value={endDate}
        on:change={handleEndDateChange}
        class="date-input"
      />
    </div>
  </div>
</div>

<style>
  .period-selector {
    background: var(--theme-bg-card);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md, 8px);
    padding: var(--spacing-md, 1rem);
  }

  .selector-header {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm, 0.75rem);
    margin-bottom: var(--spacing-md, 1rem);
  }

  .selector-title {
    font-size: var(--text-base, 1rem);
    font-weight: 600;
    color: var(--text-primary);
    margin: 0;
  }

  .preset-buttons {
    display: flex;
    flex-wrap: wrap;
    gap: var(--spacing-xs, 0.5rem);
    margin-bottom: var(--spacing-md, 1rem);
  }

  .preset-button {
    padding: var(--spacing-xs, 0.5rem) var(--spacing-sm, 0.75rem);
    background: var(--theme-bg-elevated);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-sm, 4px);
    color: var(--text-secondary);
    font-size: var(--text-sm, 0.875rem);
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .preset-button:hover {
    background: var(--accent-primary);
    color: white;
    border-color: var(--accent-primary);
  }

  .custom-dates {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: var(--spacing-md, 1rem);
  }

  .date-input-group {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xs, 0.5rem);
  }

  .date-input-group label {
    font-size: var(--text-sm, 0.875rem);
    color: var(--text-secondary);
    font-weight: 500;
  }

  .date-input {
    padding: var(--spacing-sm, 0.75rem);
    background: var(--theme-bg-elevated);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-sm, 4px);
    color: var(--text-primary);
    font-size: var(--text-base, 1rem);
  }

  .date-input:focus {
    outline: none;
    border-color: var(--accent-primary);
    box-shadow: 0 0 0 3px rgba(0, 147, 247, 0.1);
  }

  @media (max-width: 640px) {
    .custom-dates {
      grid-template-columns: 1fr;
    }

    .preset-buttons {
      justify-content: center;
    }
  }
</style>



