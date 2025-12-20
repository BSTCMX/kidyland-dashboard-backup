<script lang="ts">
  /**
   * ForecastingDayOfWeekDistribution - Pie/Doughnut chart showing revenue distribution by day of week.
   * 
   * Displays predicted revenue distribution across days of the week.
   * Reuses SalesPieChart pattern with Chart.js.
   * Responsive and accessible.
   */
  import { onMount } from 'svelte';
  import ChartWrapper from '../sales/ChartWrapper.svelte';
  import { createPieChartConfig } from '$lib/utils/charts/chartConfig';
  import { transformGroupedData, type GroupedDataPoint, generateColorPalette } from '$lib/utils/charts/chartHelpers';
  import {
    getChartThemeColors,
    getResponsiveFontSizes,
    createThemeObserver,
    themeColorsChanged,
    type ChartThemeColors
  } from '$lib/utils/charts/useChartTheme';
  import LoadingSpinner from '$lib/components/admin/LoadingSpinner.svelte';
  import ErrorBanner from '$lib/components/admin/ErrorBanner.svelte';
  import { formatPrice } from '$lib/stores/reports';
  import type { SegmentedPredictionsResponse } from '$lib/stores/reports';

  export let predictionsData: SegmentedPredictionsResponse | null = null;
  export let moduleKey: "recepcion" | "kidibar" | "total" | null = null;
  export let height: string = '400px';
  export let chartType: 'pie' | 'doughnut' = 'doughnut';
  export let loading: boolean = false;
  export let error: string | null = null;

  let chartConfig: any = null;
  let containerElement: HTMLElement;
  
  // Theme colors and font sizes for reactive updates
  let themeColors: ChartThemeColors = getChartThemeColors();
  let fontSizes = getResponsiveFontSizes();
  let themeUpdateTrigger = 0;

  // Day names in Spanish (Monday = 0)
  const dayNames = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'];
  
  // Day names mapping for forecast data (day_of_week can be string or number)
  const dayNameMap: { [key: string]: number } = {
    'lunes': 0, 'martes': 1, 'miércoles': 2, 'miércoles': 2, 'miercoles': 2,
    'jueves': 3, 'viernes': 4, 'sábado': 5, 'sabado': 5, 'domingo': 6,
    'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3, 'friday': 4, 'saturday': 5, 'sunday': 6
  };

  // Transform forecast data to grouped data by day of week
  $: groupedData = predictionsData && moduleKey ? (() => {
    const salesPred = predictionsData.predictions[moduleKey]?.sales;
    
    // Check for error FIRST (before processing data)
    if (salesPred?.error) {
      return null; // Signal error (null instead of empty array)
    }
    
    // Then check for forecast data
    if (!salesPred || !salesPred.forecast || !Array.isArray(salesPred.forecast) || salesPred.forecast.length === 0) {
      return []; // Empty state (no error, just no data)
    }

    // Option 1: Use day_of_week_adjustments if available (more accurate)
    if (salesPred.day_of_week_adjustments) {
      const adjustments = salesPred.day_of_week_adjustments;
      const historicalAvg = salesPred.historical_avg_revenue_cents || 0;
      
      // Create data points from adjustments
      return dayNames.map((dayName, index) => {
        // Find adjustment for this day (adjustments might use different day name formats)
        let adjustment = 1.0;
        const lowerDayName = dayName.toLowerCase();
        
        // Try to find matching adjustment
        for (const [key, value] of Object.entries(adjustments)) {
          const lowerKey = key.toLowerCase();
          if (lowerKey.includes(lowerDayName) || dayNameMap[lowerKey] === index) {
            adjustment = typeof value === 'number' ? value : 1.0;
            break;
          }
        }
        
        // If not found, try by index (assuming adjustments are ordered by day)
        if (adjustment === 1.0 && Array.isArray(adjustments)) {
          adjustment = adjustments[index] || 1.0;
        } else if (adjustment === 1.0 && typeof adjustments === 'object') {
          // Try numeric keys
          adjustment = (adjustments as any)[index] || (adjustments as any)[dayName] || 1.0;
        }
        
        const predictedRevenue = historicalAvg * adjustment;
        return {
          label: dayName,
          value: predictedRevenue
        };
      }).filter(item => item.value > 0);
    }

    // Option 2: Aggregate from forecast array by day_of_week
    const dayTotals: { [key: string]: number } = {};
    salesPred.forecast.forEach((day: any) => {
      let dayName = day.day_of_week;
      
      // If day_of_week is a number, convert to day name
      if (typeof day.day_of_week === 'number') {
        dayName = dayNames[day.day_of_week] || `Día ${day.day_of_week}`;
      } else if (!dayName) {
        // Try to infer from date
        const date = new Date(day.date);
        dayName = dayNames[date.getDay()] || 'Desconocido';
      }
      
      if (!dayTotals[dayName]) {
        dayTotals[dayName] = 0;
      }
      dayTotals[dayName] += day.predicted_revenue_cents || 0;
    });

    return Object.entries(dayTotals)
      .map(([label, value]) => ({ label, value }))
      .sort((a, b) => {
        // Sort by day order
        const indexA = dayNames.indexOf(a.label);
        const indexB = dayNames.indexOf(b.label);
        return (indexA === -1 ? 999 : indexA) - (indexB === -1 ? 999 : indexB);
      });
  })() : [];

  // Update theme colors when component mounts or theme changes
  function updateThemeColors() {
    if (typeof window !== 'undefined' && containerElement) {
      const newColors = getChartThemeColors(containerElement);
      const newFontSizes = getResponsiveFontSizes();
      
      if (themeColorsChanged(themeColors, newColors) || 
          fontSizes.legend !== newFontSizes.legend ||
          fontSizes.tooltipTitle !== newFontSizes.tooltipTitle ||
          fontSizes.tooltipBody !== newFontSizes.tooltipBody ||
          fontSizes.axisTicks !== newFontSizes.axisTicks) {
        themeColors = newColors;
        fontSizes = newFontSizes;
        themeUpdateTrigger++;
      }
    }
  }

  // Reactive statement to update chart config
  $: {
    const _ = themeUpdateTrigger;
    
    if (groupedData && groupedData.length > 0 && containerElement) {
      const transformed = transformGroupedData(groupedData, 'Distribución por Día');
      const config = createPieChartConfig(transformed, containerElement, themeColors, fontSizes);
      
      // Override chart type
      config.type = chartType;
      
      // Customize tooltip to show formatted price
      if (config.options && config.options.plugins && config.options.plugins.tooltip) {
        const originalCallbacks = config.options.plugins.tooltip.callbacks || {};
        config.options.plugins.tooltip.callbacks = {
          ...originalCallbacks,
          label: (context: any) => {
            const label = context.label || '';
            const value = context.parsed || 0;
            const total = context.dataset.data.reduce((a: number, b: number) => a + b, 0);
            const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : '0';
            return `${label}: ${formatPrice(value)} (${percentage}%)`;
          }
        };
      }
      
      chartConfig = config;
    } else {
      chartConfig = null;
    }
  }

  // Helper function to calculate average adjustment from day_of_week_adjustments
  function getAverageAdjustment(adjustments: any): number {
    if (!adjustments || typeof adjustments !== 'object') return 1.0;
    const values = Object.values(adjustments) as number[];
    return values.length > 0 ? (values.reduce((a, b) => a + b, 0) / values.length) : 1.0;
  }

  onMount(() => {
    updateThemeColors();
    
    const cleanup = createThemeObserver(() => {
      updateThemeColors();
    });
    
    const handleResize = () => {
      updateThemeColors();
    };
    window.addEventListener('resize', handleResize);
    
    return () => {
      cleanup();
      window.removeEventListener('resize', handleResize);
    };
  });
</script>

<div class="forecasting-dayofweek-distribution" bind:this={containerElement}>
  {#if loading}
    <div class="chart-loading">
      <LoadingSpinner />
    </div>
  {:else if error}
    <ErrorBanner error={error} />
  {:else if groupedData === null}
    <!-- Error state from backend -->
    {#if predictionsData && moduleKey}
      {@const salesPred = predictionsData.predictions[moduleKey]?.sales}
      <ErrorBanner error={salesPred?.message || salesPred?.error || "Error al generar predicciones"} />
    {:else}
      <ErrorBanner error="Error al generar predicciones" />
    {/if}
  {:else if !groupedData || groupedData.length === 0}
    <div class="chart-empty">
      <p>No hay datos disponibles para mostrar la distribución por día de la semana.</p>
    </div>
  {:else if chartConfig}
    <div class="chart-header">
      <h4 class="chart-title">Distribución de Revenue por Día de la Semana</h4>
      <div class="chart-summary">
        {#if predictionsData && moduleKey}
          {@const salesPred = predictionsData.predictions[moduleKey]?.sales}
          {#if salesPred?.day_of_week_adjustments}
            {@const avgAdjustment = getAverageAdjustment(salesPred.day_of_week_adjustments)}
            <p class="summary-text">
              Basado en ajustes por día de la semana (factor promedio: {avgAdjustment.toFixed(2)}x)
            </p>
          {/if}
        {/if}
      </div>
    </div>
    <ChartWrapper config={chartConfig} {height} />
  {/if}
</div>

<style>
  .forecasting-dayofweek-distribution {
    width: 100%;
    position: relative;
  }

  .chart-header {
    margin-bottom: var(--spacing-md);
  }

  .chart-title {
    font-size: var(--text-lg);
    font-weight: 600;
    color: var(--text-primary);
    margin: 0 0 var(--spacing-xs) 0;
  }

  .chart-summary {
    margin-top: var(--spacing-xs);
  }

  .summary-text {
    font-size: var(--text-xs);
    color: var(--text-secondary);
    font-style: italic;
    margin: 0;
  }

  .chart-loading,
  .chart-empty {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 300px;
    color: var(--text-secondary);
  }
</style>

