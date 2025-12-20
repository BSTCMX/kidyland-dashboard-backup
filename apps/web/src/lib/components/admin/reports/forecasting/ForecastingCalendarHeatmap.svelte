<script lang="ts">
  /**
   * ForecastingCalendarHeatmap - Calendar heatmap visualization for forecast predictions.
   * 
   * Displays a calendar grid with color-coded days based on predicted revenue intensity.
   * Reuses pattern from ArqueosHeatmap.svelte.
   * Responsive and accessible.
   */
  import { formatPrice } from '$lib/stores/reports';
  import type { SegmentedPredictionsResponse } from '$lib/stores/reports';

  export let predictionsData: SegmentedPredictionsResponse | null = null;
  export let moduleKey: "recepcion" | "kidibar" | "total" | null = null;

  // Get forecast data for the specified module
  $: forecastData = predictionsData && moduleKey && predictionsData.predictions[moduleKey]?.sales?.forecast 
    ? predictionsData.predictions[moduleKey].sales.forecast 
    : [];

  // Calculate intensity levels for revenue prediction
  function calculateIntensity(revenue: number, minRevenue: number, maxRevenue: number): number {
    if (maxRevenue === minRevenue) return 0;
    const ratio = (revenue - minRevenue) / (maxRevenue - minRevenue);
    
    // Map to 0-4 scale (matching ArqueosHeatmap pattern)
    if (ratio < 0.2) return 0; // Very low
    if (ratio < 0.4) return 1; // Low
    if (ratio < 0.6) return 2; // Medium
    if (ratio < 0.8) return 3; // High
    return 4; // Very high
  }

  // Process forecast data with intensity levels
  $: processedData = forecastData.length > 0 ? (() => {
    const revenues = forecastData
      .map((day: any) => day.predicted_revenue_cents || 0)
      .filter((rev: number) => rev >= 0);
    
    if (revenues.length === 0) return [];
    
    const minRevenue = Math.min(...revenues);
    const maxRevenue = Math.max(...revenues);
    
    return forecastData.map((day: any) => {
      const revenue = day.predicted_revenue_cents || 0;
      return {
        date: day.date,
        revenue: revenue,
        count: day.predicted_count || 0,
        intensity: calculateIntensity(revenue, minRevenue, maxRevenue),
        day_of_week: day.day_of_week || getDayOfWeekName(day.date),
        day_of_week_factor: day.day_of_week_factor || 1.0
      };
    });
  })() : [];

  // Get intensity color class (matching ArqueosHeatmap pattern)
  function getIntensityClass(intensity: number): string {
    const classes = [
      'intensity-very-low',  // 0
      'intensity-low',       // 1
      'intensity-medium',    // 2
      'intensity-high',      // 3
      'intensity-very-high'  // 4
    ];
    return classes[intensity] || 'intensity-very-low';
  }

  // Get intensity label
  function getIntensityLabel(intensity: number): string {
    const labels = [
      'Muy Bajo',
      'Bajo',
      'Medio',
      'Alto',
      'Muy Alto'
    ];
    return labels[intensity] || 'Muy Bajo';
  }

  // Group data by month for better visualization
  $: groupedByMonth = processedData.length > 0 ? (() => {
    const groups: { [key: string]: typeof processedData } = {};
    processedData.forEach(point => {
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

  // Get day of week name
  function getDayOfWeekName(dateStr: string): string {
    const date = new Date(dateStr);
    return date.toLocaleDateString('es-ES', { weekday: 'long' });
  }

  // Format month label
  function formatMonthLabel(monthKey: string): string {
    const [year, month] = monthKey.split('-');
    const date = new Date(parseInt(year), parseInt(month) - 1, 1);
    return date.toLocaleDateString('es-ES', { month: 'long', year: 'numeric' });
  }

  // Get days in month
  function getDaysInMonth(year: number, month: number): number {
    return new Date(year, month, 0).getDate();
  }

  // Get first day of month (0 = Sunday, 6 = Saturday)
  function getFirstDayOfMonth(year: number, month: number): number {
    return new Date(year, month - 1, 1).getDay();
  }

  // Create calendar grid for a month
  function createCalendarGrid(monthKey: string, data: typeof processedData): Array<{ date: string | null; dayData: any | null }> {
    const [year, month] = monthKey.split('-').map(Number);
    const daysInMonth = getDaysInMonth(year, month);
    const firstDay = getFirstDayOfMonth(year, month);
    
    const grid: Array<{ date: string | null; dayData: any | null }> = [];
    
    // Add empty cells for days before month starts
    for (let i = 0; i < firstDay; i++) {
      grid.push({ date: null, dayData: null });
    }
    
    // Add days of month
    for (let day = 1; day <= daysInMonth; day++) {
      const dateStr = `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
      const dayData = data.find((d: any) => d.date === dateStr) || null;
      grid.push({ date: dateStr, dayData });
    }
    
    return grid;
  }

  let hoveredDate: string | null = null;
</script>

<div class="forecasting-calendar-heatmap">
  {#if !predictionsData || !moduleKey || processedData.length === 0}
    <div class="empty-state">
      <p>No hay datos de predicción disponibles para mostrar el calendario.</p>
    </div>
  {:else}
    <div class="heatmap-container">
      <div class="heatmap-header">
        <h3 class="section-title">Calendario de Predicciones</h3>
        <div class="intensity-legend">
          <span class="legend-label">Intensidad de Revenue:</span>
          <div class="legend-items">
            <div class="legend-item">
              <span class="legend-color intensity-very-low"></span>
              <span class="legend-text">Muy Bajo</span>
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
              <span class="legend-color intensity-very-high"></span>
              <span class="legend-text">Muy Alto</span>
            </div>
          </div>
        </div>
      </div>

      <div class="heatmap-content">
        {#each Object.entries(groupedByMonth) as [monthKey, monthData]}
            {@const calendarGrid = createCalendarGrid(monthKey, monthData)}
          <div class="month-group">
            <h4 class="month-title">{formatMonthLabel(monthKey)}</h4>
            <div class="calendar-grid-wrapper">
              <div class="calendar-grid">
                <div class="weekday-header">
                <div class="weekday-cell">Dom</div>
                <div class="weekday-cell">Lun</div>
                <div class="weekday-cell">Mar</div>
                <div class="weekday-cell">Mié</div>
                <div class="weekday-cell">Jue</div>
                <div class="weekday-cell">Vie</div>
                <div class="weekday-cell">Sáb</div>
              </div>
              
              <div class="calendar-days">
                {#each calendarGrid as cell}
                  {#if cell.date}
                    {@const intensity = cell.dayData?.intensity ?? 0}
                    {@const dateStr = cell.date}
                    <div
                      class="calendar-day {getIntensityClass(intensity)}"
                      class:has-data={cell.dayData !== null}
                      on:mouseenter={() => hoveredDate = dateStr}
                      on:mouseleave={() => hoveredDate = null}
                      role="button"
                      tabindex="0"
                    >
                      <span class="day-number">{getDayNumber(dateStr)}</span>
                      {#if cell.dayData}
                        <span class="day-revenue-indicator" title={formatPrice(cell.dayData.revenue)}></span>
                      {/if}
                    </div>
                  {:else}
                    <div class="calendar-day empty"></div>
                  {/if}
                {/each}
                </div>
              </div>
            </div>
          </div>
        {/each}
      </div>

      {#if hoveredDate}
        {@const hoveredData = processedData.find((d) => d.date === hoveredDate)}
        {#if hoveredData}
          <div class="tooltip">
            <div class="tooltip-date">{new Date(hoveredDate).toLocaleDateString('es-ES', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}</div>
            <div class="tooltip-content">
              <div class="tooltip-item">
                <span class="tooltip-label">Revenue:</span>
                <span class="tooltip-value">{formatPrice(hoveredData.revenue)}</span>
              </div>
              <div class="tooltip-item">
                <span class="tooltip-label">Ventas:</span>
                <span class="tooltip-value">{hoveredData.count}</span>
              </div>
              <div class="tooltip-item">
                <span class="tooltip-label">Intensidad:</span>
                <span class="tooltip-value">{getIntensityLabel(hoveredData.intensity)}</span>
              </div>
              {#if hoveredData.day_of_week_factor !== undefined && hoveredData.day_of_week_factor !== 1.0}
                <div class="tooltip-item">
                  <span class="tooltip-label">Factor Día:</span>
                  <span class="tooltip-value">{hoveredData.day_of_week_factor.toFixed(2)}x</span>
                </div>
              {/if}
            </div>
          </div>
        {/if}
      {/if}
    </div>
  {/if}
</div>

<style>
  .forecasting-calendar-heatmap {
    width: 100%;
  }

  .empty-state {
    text-align: center;
    padding: var(--spacing-xl);
    color: var(--text-secondary);
    font-style: italic;
  }

  .heatmap-container {
    position: relative;
  }

  .heatmap-header {
    margin-bottom: var(--spacing-lg);
  }

  .section-title {
    font-size: var(--text-xl);
    font-weight: 700;
    color: var(--text-primary);
    margin: 0 0 var(--spacing-md) 0;
  }

  .intensity-legend {
    display: flex;
    align-items: center;
    gap: var(--spacing-md);
    flex-wrap: wrap;
  }

  .legend-label {
    font-size: var(--text-sm);
    color: var(--text-secondary);
    font-weight: 500;
  }

  .legend-items {
    display: flex;
    gap: var(--spacing-md);
    flex-wrap: wrap;
  }

  .legend-item {
    display: flex;
    align-items: center;
    gap: var(--spacing-xs);
  }

  .legend-color {
    width: 16px;
    height: 16px;
    border-radius: var(--radius-sm);
    border: 1px solid var(--border-primary);
  }

  .legend-text {
    font-size: var(--text-xs);
    color: var(--text-secondary);
  }

  .heatmap-content {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xl);
  }

  .month-group {
    width: 100%;
  }

  .month-title {
    font-size: var(--text-lg);
    font-weight: 600;
    color: var(--text-primary);
    margin: 0 0 var(--spacing-md) 0;
    text-transform: capitalize;
  }

  .calendar-grid-wrapper {
    width: 100%;
    overflow-x: auto;
    overflow-y: visible;
    /* Enable smooth scrolling on mobile */
    -webkit-overflow-scrolling: touch;
    /* Add subtle scroll indicator */
    scrollbar-width: thin;
    scrollbar-color: var(--border-primary) transparent;
  }

  /* When inside module-view (individual views), remove forced scroll - let it fit viewport */
  :global(.module-view) .calendar-grid-wrapper {
    overflow-x: visible; /* No forced scroll, let grid adjust to viewport */
  }

  .calendar-grid-wrapper::-webkit-scrollbar {
    height: 8px;
  }

  .calendar-grid-wrapper::-webkit-scrollbar-track {
    background: var(--theme-bg-secondary);
    border-radius: var(--radius-sm);
  }

  .calendar-grid-wrapper::-webkit-scrollbar-thumb {
    background: var(--border-primary);
    border-radius: var(--radius-sm);
  }

  .calendar-grid-wrapper::-webkit-scrollbar-thumb:hover {
    background: var(--accent-primary);
  }

  .calendar-grid {
    width: 100%;
    min-width: 350px; /* Force scroll on mobile when needed */
  }

  /* When inside module-view (individual views), remove min-width to allow natural viewport fitting */
  :global(.module-view) .calendar-grid {
    min-width: unset; /* Let grid adjust to available width */
  }

  .weekday-header {
    display: grid;
    grid-template-columns: repeat(7, 1fr);
    gap: var(--spacing-xs);
    margin-bottom: var(--spacing-xs);
  }

  .weekday-cell {
    font-size: var(--text-xs);
    font-weight: 600;
    color: var(--text-secondary);
    text-align: center;
    padding: var(--spacing-xs);
  }

  .calendar-days {
    display: grid;
    grid-template-columns: repeat(7, minmax(40px, 1fr));
    gap: var(--spacing-xs);
  }

  .calendar-day {
    aspect-ratio: 1;
    min-width: 32px;
    min-height: 32px;
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-sm);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    position: relative;
    background: var(--theme-bg-secondary);
    cursor: pointer;
    transition: all 0.2s;
  }

  .calendar-day.empty {
    border: none;
    background: transparent;
    cursor: default;
  }

  .calendar-day.has-data:hover {
    transform: scale(1.1);
    z-index: 10;
    box-shadow: var(--shadow-md);
    border-color: var(--accent-primary);
  }

  .calendar-day .day-number {
    font-size: var(--text-xs);
    font-weight: 600;
    /* Color will be overridden by intensity classes when needed */
  }

  .day-revenue-indicator {
    position: absolute;
    bottom: 2px;
    width: 4px;
    height: 4px;
    border-radius: 50%;
    background: var(--accent-primary);
  }

  /* Intensity colors - Enhanced visibility for light/dark mode */
  .intensity-very-low {
    /* Light gray with better contrast */
    background: #f3f4f6;
    border-color: #d1d5db;
    color: var(--text-primary);
  }

  /* Dark mode adjustment */
  :global([data-theme="dark"]) .intensity-very-low {
    background: #374151;
    border-color: #4b5563;
    color: var(--text-primary);
  }

  .intensity-low {
    /* Light blue with better visibility */
    background: #dbeafe;
    border-color: #93c5fd;
    color: #1e40af;
  }

  :global([data-theme="dark"]) .intensity-low {
    background: #1e3a8a;
    border-color: #3b82f6;
    color: #dbeafe;
  }

  .intensity-medium {
    /* Yellow with better contrast */
    background: #fef08a;
    border-color: #facc15;
    color: #854d0e;
  }

  :global([data-theme="dark"]) .intensity-medium {
    background: #ca8a04;
    border-color: #facc15;
    color: #fef08a;
  }

  .intensity-high {
    /* Orange with better visibility */
    background: #fed7aa;
    border-color: #f97316;
    color: #9a3412;
  }

  :global([data-theme="dark"]) .intensity-high {
    background: #ea580c;
    border-color: #fb923c;
    color: #fed7aa;
  }

  .intensity-very-high {
    /* Red with maximum visibility */
    background: #fecaca;
    border-color: #f87171;
    color: #991b1b;
  }

  :global([data-theme="dark"]) .intensity-very-high {
    background: #dc2626;
    border-color: #ef4444;
    color: #fee2e2;
  }

  .tooltip {
    position: absolute;
    background: var(--theme-bg-elevated);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
    padding: var(--spacing-md);
    box-shadow: var(--shadow-lg);
    z-index: 100;
    min-width: 200px;
    pointer-events: none;
  }

  .tooltip-date {
    font-size: var(--text-sm);
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: var(--spacing-sm);
    text-transform: capitalize;
  }

  .tooltip-content {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xs);
  }

  .tooltip-item {
    display: flex;
    justify-content: space-between;
    font-size: var(--text-xs);
  }

  .tooltip-label {
    color: var(--text-secondary);
  }

  .tooltip-value {
    color: var(--text-primary);
    font-weight: 500;
  }

  /* Responsive adjustments */
  @media (max-width: 640px) {
    .calendar-grid-wrapper {
      /* Enable horizontal scroll on mobile with edge-to-edge UX */
      margin-left: calc(var(--spacing-lg) * -1);
      margin-right: calc(var(--spacing-lg) * -1);
      padding-left: var(--spacing-lg);
      padding-right: var(--spacing-lg);
      padding-bottom: var(--spacing-xs);
    }

    /* In module-view (individual views), remove negative margins - let it fit naturally */
    :global(.module-view) .calendar-grid-wrapper {
      margin-left: 0;
      margin-right: 0;
      padding-left: 0;
      padding-right: 0;
    }

    .calendar-days {
      grid-template-columns: repeat(7, minmax(32px, 1fr));
      min-width: 280px; /* Ensure scroll on very small screens */
    }

    /* In module-view, remove min-width to allow natural fitting */
    :global(.module-view) .calendar-days {
      min-width: unset;
    }

    .calendar-day {
      min-width: 28px;
      min-height: 28px;
    }

    .day-number {
      font-size: 10px;
    }

    .legend-items {
      gap: var(--spacing-sm);
    }

    .intensity-legend {
      flex-direction: column;
      align-items: flex-start;
    }
  }
</style>

