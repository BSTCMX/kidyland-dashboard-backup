<script lang="ts">
  /**
   * ArqueosHeatmap - Calendar heatmap visualization for arqueos discrepancies.
   * 
   * Displays a calendar grid with color-coded days based on discrepancy intensity.
   * Responsive and accessible.
   */
  import { onMount } from 'svelte';
  import { fetchArqueosHeatmap, formatPrice, type ArqueosHeatmapDataPoint, type ArqueosHeatmapReport } from '$lib/stores/reports';
  import LoadingSpinner from '$lib/components/admin/LoadingSpinner.svelte';
  import ErrorBanner from '$lib/components/admin/ErrorBanner.svelte';

  export let sucursalId: string | null = null;
  export let startDate: string;
  export let endDate: string;
  export let selectedModule: "all" | "recepcion" | "kidibar" = "all";

  let heatmapData: ArqueosHeatmapReport | null = null;
  let loading = false;
  let error: string | null = null;
  let hoveredDate: string | null = null;

  // Track previous params
  let previousSucursalId: string | null = null;
  let previousStartDate: string | null = null;
  let previousEndDate: string | null = null;
  let previousModule: "all" | "recepcion" | "kidibar" = "all";

  async function loadHeatmapData() {
    loading = true;
    error = null;

    try {
      const report = await fetchArqueosHeatmap(
        sucursalId,
        startDate,
        endDate,
        selectedModule
      );

      heatmapData = report;
    } catch (err: any) {
      console.error('Error loading heatmap data:', err);
      error = err.message || 'Error al cargar datos del heatmap';
    } finally {
      loading = false;
    }
  }

  // Fetch when params change
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
      loadHeatmapData();
    }
  }

  onMount(() => {
    loadHeatmapData();
  });

  // Get intensity color class
  function getIntensityClass(intensity: number): string {
    const classes = [
      'intensity-perfect',   // 0
      'intensity-low',       // 1
      'intensity-medium',    // 2
      'intensity-high',      // 3
      'intensity-critical'   // 4
    ];
    return classes[intensity] || 'intensity-perfect';
  }

  // Get intensity label
  function getIntensityLabel(intensity: number): string {
    const labels = [
      'Perfecto',
      'Bajo',
      'Medio',
      'Alto',
      'Crítico'
    ];
    return labels[intensity] || 'Perfecto';
  }

  // Group data by month for better visualization
  $: groupedByMonth = heatmapData ? (() => {
    const groups: { [key: string]: ArqueosHeatmapDataPoint[] } = {};
    heatmapData.heatmap.forEach(point => {
      const date = new Date(point.date);
      const monthKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
      if (!groups[monthKey]) {
        groups[monthKey] = [];
      }
      groups[monthKey].push(point);
    });
    return groups;
  })() : {};

  // Get day of week for a date (0 = Sunday, 6 = Saturday)
  function getDayOfWeek(dateStr: string): number {
    const date = new Date(dateStr);
    return date.getDay();
  }

  // Get day number
  function getDayNumber(dateStr: string): number {
    const date = new Date(dateStr);
    return date.getDate();
  }

  // Format month label
  function formatMonthLabel(monthKey: string): string {
    const [year, month] = monthKey.split('-');
    const date = new Date(parseInt(year), parseInt(month) - 1, 1);
    return date.toLocaleDateString('es-ES', { month: 'long', year: 'numeric' });
  }
</script>

<div class="arqueos-heatmap">
  {#if loading}
    <LoadingSpinner />
  {:else if error}
    <ErrorBanner {error} />
  {:else if heatmapData && heatmapData.heatmap.length > 0}
    <div class="heatmap-container">
      <div class="heatmap-header">
        <h3 class="section-title">Calendario de Discrepancias</h3>
        <div class="intensity-legend">
          <span class="legend-label">Intensidad:</span>
          <div class="legend-items">
            <div class="legend-item">
              <span class="legend-color intensity-perfect"></span>
              <span class="legend-text">Perfecto</span>
            </div>
            <div class="legend-item">
              <span class="legend-color intensity-low"></span>
              <span class="legend-text">Bajo</span>
            </div>
            <div class="legend-item">
              <span class="legend-color intensity-medium"></span>
              <span class="legend-text">Medio</span>
            </div>
            <div class="legend-item">
              <span class="legend-color intensity-high"></span>
              <span class="legend-text">Alto</span>
            </div>
            <div class="legend-item">
              <span class="legend-color intensity-critical"></span>
              <span class="legend-text">Crítico</span>
            </div>
          </div>
        </div>
      </div>

      {#each Object.entries(groupedByMonth) as [monthKey, monthData]}
        <div class="month-section">
          <h4 class="month-title">{formatMonthLabel(monthKey)}</h4>
          <div class="calendar-grid">
            <!-- Day of week headers -->
            <div class="day-header">Dom</div>
            <div class="day-header">Lun</div>
            <div class="day-header">Mar</div>
            <div class="day-header">Mié</div>
            <div class="day-header">Jue</div>
            <div class="day-header">Vie</div>
            <div class="day-header">Sáb</div>

            <!-- Empty cells for days before month starts -->
            {#each Array(getDayOfWeek(monthData[0].date)) as _}
              <div class="calendar-day empty"></div>
            {/each}

            <!-- Calendar days -->
            {#each monthData as point (point.date)}
              {@const dayOfWeek = getDayOfWeek(point.date)}
              {@const dayNumber = getDayNumber(point.date)}
              <div
                class="calendar-day {getIntensityClass(point.intensity)}"
                class:hovered={hoveredDate === point.date}
                on:mouseenter={() => hoveredDate = point.date}
                on:mouseleave={() => hoveredDate = null}
                title="Fecha: {point.date}, Diferencia: {formatPrice(point.difference_cents)}, Tasa: {point.discrepancy_rate}%"
              >
                <span class="day-number">{dayNumber}</span>
                {#if hoveredDate === point.date}
                  <div class="day-tooltip">
                    <div class="tooltip-date">{new Date(point.date).toLocaleDateString('es-ES', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}</div>
                    <div class="tooltip-metric">
                      <span class="tooltip-label">Diferencia:</span>
                      <span class="tooltip-value" class:positive={point.difference_cents > 0} class:negative={point.difference_cents < 0}>
                        {formatPrice(point.difference_cents)}
                      </span>
                    </div>
                    <div class="tooltip-metric">
                      <span class="tooltip-label">Tasa de discrepancia:</span>
                      <span class="tooltip-value">{point.discrepancy_rate}%</span>
                    </div>
                    <div class="tooltip-metric">
                      <span class="tooltip-label">Intensidad:</span>
                      <span class="tooltip-value">{getIntensityLabel(point.intensity)}</span>
                    </div>
                    {#if point.arqueos_count > 0}
                      <div class="tooltip-metric">
                        <span class="tooltip-label">Arqueos:</span>
                        <span class="tooltip-value">{point.arqueos_count}</span>
                      </div>
                    {/if}
                  </div>
                {/if}
              </div>
            {/each}
          </div>
        </div>
      {/each}

      <!-- Summary statistics -->
      <div class="heatmap-summary">
        <h4 class="summary-title">Resumen de Intensidades</h4>
        <div class="summary-grid">
          <div class="summary-item">
            <span class="summary-label">Perfectos:</span>
            <span class="summary-value">{heatmapData.intensity_scale.perfect}</span>
          </div>
          <div class="summary-item">
            <span class="summary-label">Bajos:</span>
            <span class="summary-value">{heatmapData.intensity_scale.low}</span>
          </div>
          <div class="summary-item">
            <span class="summary-label">Medios:</span>
            <span class="summary-value">{heatmapData.intensity_scale.medium}</span>
          </div>
          <div class="summary-item">
            <span class="summary-label">Altos:</span>
            <span class="summary-value">{heatmapData.intensity_scale.high}</span>
          </div>
          <div class="summary-item">
            <span class="summary-label">Críticos:</span>
            <span class="summary-value">{heatmapData.intensity_scale.critical}</span>
          </div>
        </div>
      </div>
    </div>
  {:else}
    <div class="placeholder-content">
      <p>No hay datos disponibles para el período seleccionado.</p>
    </div>
  {/if}
</div>

<style>
  .arqueos-heatmap {
    width: 100%;
  }

  .heatmap-container {
    background: var(--theme-bg-card);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-lg, 12px);
    padding: var(--spacing-lg, 1.5rem);
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  }

  .heatmap-header {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-md, 1rem);
    margin-bottom: var(--spacing-xl, 1.5rem);
  }

  .section-title {
    font-size: var(--text-xl, 1.25rem);
    font-weight: 700;
    color: var(--text-primary);
    margin: 0;
  }

  .intensity-legend {
    display: flex;
    align-items: center;
    gap: var(--spacing-md, 1rem);
    flex-wrap: wrap;
  }

  .legend-label {
    font-size: var(--text-sm, 0.875rem);
    color: var(--text-secondary);
    font-weight: 600;
  }

  .legend-items {
    display: flex;
    gap: var(--spacing-md, 1rem);
    flex-wrap: wrap;
  }

  .legend-item {
    display: flex;
    align-items: center;
    gap: var(--spacing-xs, 0.5rem);
  }

  .legend-color {
    width: 20px;
    height: 20px;
    border-radius: var(--radius-sm, 4px);
    border: 1px solid var(--border-primary);
  }

  .month-section {
    margin-bottom: var(--spacing-xl, 1.5rem);
  }

  .month-title {
    font-size: var(--text-lg, 1.125rem);
    font-weight: 600;
    color: var(--text-primary);
    margin: 0 0 var(--spacing-md, 1rem) 0;
    text-transform: capitalize;
  }

  .calendar-grid {
    display: grid;
    grid-template-columns: repeat(7, 1fr);
    gap: var(--spacing-xs, 0.5rem);
    margin-bottom: var(--spacing-lg, 1.25rem);
  }

  .day-header {
    font-size: var(--text-xs, 0.75rem);
    font-weight: 600;
    color: var(--text-secondary);
    text-align: center;
    padding: var(--spacing-xs, 0.5rem);
  }

  .calendar-day {
    aspect-ratio: 1;
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-sm, 4px);
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
    cursor: pointer;
    transition: all 0.2s ease;
    font-size: var(--text-xs, 0.75rem);
    color: var(--text-primary);
  }

  .calendar-day.empty {
    border: none;
    cursor: default;
  }

  .calendar-day:hover {
    transform: scale(1.1);
    z-index: 10;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
  }

  .day-number {
    font-weight: 600;
  }

  /* Intensity colors */
  .intensity-perfect {
    background: var(--accent-success, #10B981);
    color: white;
  }

  .intensity-low {
    background: #86EFAC;
    color: var(--text-primary);
  }

  .intensity-medium {
    background: #FDE047;
    color: var(--text-primary);
  }

  .intensity-high {
    background: #F59E0B;
    color: white;
  }

  .intensity-critical {
    background: var(--accent-error, #EF4444);
    color: white;
  }

  .day-tooltip {
    position: absolute;
    bottom: 100%;
    left: 50%;
    transform: translateX(-50%);
    margin-bottom: var(--spacing-xs, 0.5rem);
    background: var(--theme-bg-primary);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md, 8px);
    padding: var(--spacing-sm, 0.75rem);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
    z-index: 20;
    min-width: 200px;
    font-size: var(--text-sm, 0.875rem);
  }

  .tooltip-date {
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: var(--spacing-xs, 0.5rem);
    text-transform: capitalize;
  }

  .tooltip-metric {
    display: flex;
    justify-content: space-between;
    gap: var(--spacing-sm, 0.75rem);
    margin-bottom: var(--spacing-xs, 0.5rem);
  }

  .tooltip-metric:last-child {
    margin-bottom: 0;
  }

  .tooltip-label {
    color: var(--text-secondary);
  }

  .tooltip-value {
    color: var(--text-primary);
    font-weight: 600;
  }

  .tooltip-value.positive {
    color: var(--accent-success, #10B981);
  }

  .tooltip-value.negative {
    color: var(--accent-error, #EF4444);
  }

  .heatmap-summary {
    margin-top: var(--spacing-xl, 1.5rem);
    padding-top: var(--spacing-lg, 1.25rem);
    border-top: 1px solid var(--border-primary);
  }

  .summary-title {
    font-size: var(--text-lg, 1.125rem);
    font-weight: 600;
    color: var(--text-primary);
    margin: 0 0 var(--spacing-md, 1rem) 0;
  }

  .summary-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
    gap: var(--spacing-md, 1rem);
  }

  .summary-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: var(--spacing-sm, 0.75rem);
    background: var(--theme-bg-secondary);
    border-radius: var(--radius-md, 8px);
  }

  .summary-label {
    font-size: var(--text-sm, 0.875rem);
    color: var(--text-secondary);
  }

  .summary-value {
    font-size: var(--text-base, 1rem);
    font-weight: 600;
    color: var(--text-primary);
  }

  .placeholder-content {
    padding: var(--spacing-2xl, 3rem);
    text-align: center;
    color: var(--text-secondary);
    font-style: italic;
  }

  @media (max-width: 768px) {
    .calendar-grid {
      gap: var(--spacing-xs, 0.25rem);
    }

    .calendar-day {
      font-size: 0.625rem;
    }

    .day-tooltip {
      min-width: 150px;
      font-size: var(--text-xs, 0.75rem);
    }
  }
</style>



