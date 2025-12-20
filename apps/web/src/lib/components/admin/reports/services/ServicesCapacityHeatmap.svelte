<script lang="ts">
  /**
   * ServicesCapacityHeatmap - Capacity utilization heatmap by hour and day.
   * 
   * Displays a heatmap showing service capacity utilization patterns.
   */
  import { onMount } from 'svelte';
  import { fetchServicesCapacity, type ServicesCapacityReport, type ServicesCapacityDataPoint } from '$lib/stores/reports';
  import LoadingSpinner from '$lib/components/admin/LoadingSpinner.svelte';
  import ErrorBanner from '$lib/components/admin/ErrorBanner.svelte';

  export let sucursalId: string | null = null;
  export let startDate: string;
  export let endDate: string;

  let capacityData: ServicesCapacityReport | null = null;
  let loading = false;
  let error: string | null = null;

  let previousSucursalId: string | null = null;
  let previousStartDate: string | null = null;
  let previousEndDate: string | null = null;

  async function loadCapacityData() {
    loading = true;
    error = null;

    try {
      const report = await fetchServicesCapacity(sucursalId, startDate, endDate);
      capacityData = report;
    } catch (err: any) {
      console.error('Error loading capacity data:', err);
      error = err.message || 'Error al cargar datos de capacidad';
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
      loadCapacityData();
    }
  }

  onMount(() => {
    loadCapacityData();
  });

  function getColorForIntensity(intensity: number): string {
    // Intensity is 0-1, map to colors
    if (intensity === 0) return 'var(--theme-bg-secondary)';
    if (intensity <= 0.25) return '#86efac'; // Light green (low)
    if (intensity <= 0.5) return '#fde047'; // Yellow (moderate)
    if (intensity <= 0.75) return '#fb923c'; // Orange (high)
    return '#ef4444'; // Red (very high)
  }

  // Group data by day of week and hour
  $: groupedData = capacityData ? (() => {
    const groups: { [key: string]: ServicesCapacityDataPoint[] } = {};
    capacityData.heatmap.forEach(point => {
      const date = new Date(point.date);
      const dayOfWeek = date.getDay(); // 0 = Sunday, 6 = Saturday
      const key = `${dayOfWeek}-${point.hour}`;
      if (!groups[key]) {
        groups[key] = [];
      }
      groups[key].push(point);
    });
    return groups;
  })() : {};

  // Calculate average intensity for each day-hour combination
  $: heatmapMatrix = (() => {
    const matrix: { [key: string]: { intensity: number; count: number } } = {};
    Object.entries(groupedData).forEach(([key, points]) => {
      const totalIntensity = points.reduce((sum, p) => sum + p.intensity, 0);
      matrix[key] = {
        intensity: totalIntensity / points.length,
        count: points.reduce((sum, p) => sum + p.active_count, 0)
      };
    });
    return matrix;
  })();

  const dayNames = ['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb'];
  const hours = Array.from({ length: 24 }, (_, i) => i);
</script>

<div class="services-capacity-heatmap">
  {#if loading}
    <LoadingSpinner />
  {:else if error}
    <ErrorBanner {error} />
  {:else if capacityData && capacityData.heatmap.length > 0}
    <div class="capacity-container">
      <h3 class="section-title">Mapa de Calor de Capacidad</h3>
      <p class="section-description">Utilización de capacidad por día de la semana y hora.</p>
      
      <div class="heatmap-table-container">
        <table class="capacity-heatmap-table">
          <thead>
            <tr>
              <th class="day-header">Día / Hora</th>
              {#each hours as hour}
                <th class="hour-header">{hour}:00</th>
              {/each}
            </tr>
          </thead>
          <tbody>
            {#each dayNames as dayName, dayIndex}
              <tr>
                <td class="day-label">{dayName}</td>
                {#each hours as hour}
                  {@const key = `${dayIndex}-${hour}`}
                  {@const cellData = heatmapMatrix[key]}
                  {@const intensity = cellData?.intensity ?? 0}
                  {@const count = cellData?.count ?? 0}
                  <td 
                    class="heatmap-cell" 
                    style="background-color: {getColorForIntensity(intensity)};"
                    title="{dayName} {hour}:00 - Intensidad: {(intensity * 100).toFixed(0)}%, Activos: {count}"
                  >
                    <span class="cell-value">{count > 0 ? count : ''}</span>
                  </td>
                {/each}
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
      
      <div class="intensity-legend">
        <span class="legend-label">Intensidad:</span>
        <div class="legend-items">
          <div class="legend-item">
            <span class="legend-color intensity-low"></span>
            <span class="legend-text">Baja</span>
          </div>
          <div class="legend-item">
            <span class="legend-color intensity-moderate"></span>
            <span class="legend-text">Moderada</span>
          </div>
          <div class="legend-item">
            <span class="legend-color intensity-high"></span>
            <span class="legend-text">Alta</span>
          </div>
          <div class="legend-item">
            <span class="legend-color intensity-very-high"></span>
            <span class="legend-text">Muy Alta</span>
          </div>
        </div>
      </div>
    </div>
  {:else}
    <div class="placeholder-content">
      <p>No hay datos de capacidad disponibles para el período seleccionado.</p>
    </div>
  {/if}
</div>

<style>
  .services-capacity-heatmap {
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

  .heatmap-table-container {
    overflow-x: auto;
    margin-bottom: var(--spacing-lg, 1.5rem);
  }

  .capacity-heatmap-table {
    width: 100%;
    border-collapse: collapse;
    font-size: var(--text-xs, 0.75rem);
  }

  .capacity-heatmap-table thead {
    background: var(--theme-bg-secondary);
    border-bottom: 2px solid var(--border-primary);
  }

  .capacity-heatmap-table th {
    padding: var(--spacing-xs, 0.5rem);
    text-align: center;
    font-weight: 600;
    color: var(--text-primary);
    white-space: nowrap;
  }

  .day-header {
    position: sticky;
    left: 0;
    background: var(--theme-bg-secondary);
    z-index: 2;
  }

  .hour-header {
    min-width: 40px;
  }

  .capacity-heatmap-table td {
    padding: var(--spacing-xs, 0.5rem);
    text-align: center;
    border: 1px solid var(--border-primary);
  }

  .day-label {
    font-weight: 600;
    color: var(--text-primary);
    background: var(--theme-bg-secondary);
    position: sticky;
    left: 0;
    z-index: 1;
  }

  .heatmap-cell {
    min-width: 40px;
    height: 40px;
    cursor: pointer;
    transition: all 0.2s ease-in-out;
  }

  .heatmap-cell:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
    transform: scale(1.1);
    z-index: 10;
    position: relative;
  }

  .cell-value {
    font-weight: 600;
    color: var(--text-primary);
    font-size: var(--text-xs, 0.75rem);
  }

  .intensity-legend {
    display: flex;
    align-items: center;
    gap: var(--spacing-md, 1rem);
    flex-wrap: wrap;
    margin-top: var(--spacing-lg, 1.5rem);
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

  .legend-text {
    font-size: var(--text-sm, 0.875rem);
    color: var(--text-secondary);
  }

  .intensity-low { background-color: #86efac; }
  .intensity-moderate { background-color: #fde047; }
  .intensity-high { background-color: #fb923c; }
  .intensity-very-high { background-color: #ef4444; }

  .placeholder-content {
    text-align: center;
    padding: var(--spacing-xl, 2rem);
    color: var(--text-secondary);
    font-style: italic;
  }

  @media (max-width: 768px) {
    .capacity-heatmap-table {
      font-size: var(--text-xs, 0.75rem);
    }
    .heatmap-cell {
      min-width: 30px;
      height: 30px;
    }
    .hour-header {
      min-width: 30px;
    }
  }
</style>

