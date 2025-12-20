<script lang="ts">
  /**
   * InventoryTimeSeriesChart - Time series chart for inventory stock.
   * 
   * Displays stock quantity, total value, or low stock count over time.
   * Responsive and accessible with reactive theme support.
   */
  import { onMount } from 'svelte';
  import ChartWrapper from '../sales/ChartWrapper.svelte';
  import { createTimeSeriesConfig } from '$lib/utils/charts/chartConfig';
  import { transformInventoryTimeSeriesData, type InventoryTimeSeriesDataPoint } from '$lib/utils/charts/chartHelpers';
  import {
    getChartThemeColors,
    getResponsiveFontSizes,
    createThemeObserver,
    themeColorsChanged,
    type ChartThemeColors
  } from '$lib/utils/charts/useChartTheme';
  import LoadingSpinner from '$lib/components/admin/LoadingSpinner.svelte';
  import ErrorBanner from '$lib/components/admin/ErrorBanner.svelte';

  export let data: InventoryTimeSeriesDataPoint[] = [];
  export let metric: 'stock_qty' | 'total_value' | 'low_stock_count' = 'stock_qty';
  export let height: string = '400px';
  export let loading: boolean = false;
  export let error: string | null = null;

  let chartConfig: any = null;
  let containerElement: HTMLElement;
  
  // Theme colors and font sizes for reactive updates
  let themeColors: ChartThemeColors = getChartThemeColors();
  let fontSizes = getResponsiveFontSizes();
  let themeUpdateTrigger = 0;

  // Update theme colors when component mounts or theme changes
  function updateThemeColors() {
    if (typeof window !== 'undefined' && containerElement) {
      const newColors = getChartThemeColors(containerElement);
      const newFontSizes = getResponsiveFontSizes();
      
      // Only update if colors or font sizes actually changed
      if (themeColorsChanged(themeColors, newColors) || 
          fontSizes.legend !== newFontSizes.legend ||
          fontSizes.tooltipTitle !== newFontSizes.tooltipTitle ||
          fontSizes.tooltipBody !== newFontSizes.tooltipBody ||
          fontSizes.axisTicks !== newFontSizes.axisTicks) {
        themeColors = newColors;
        fontSizes = newFontSizes;
        themeUpdateTrigger++; // Trigger reactive update
      }
    }
  }

  // Reactive statement to update chart config when data, theme, or metric changes
  $: {
    // Include themeUpdateTrigger to force recalculation when theme changes
    const _ = themeUpdateTrigger;
    
    if (data && data.length > 0 && containerElement) {
      const transformed = transformInventoryTimeSeriesData(data, metric);
      chartConfig = createTimeSeriesConfig(transformed, containerElement, themeColors, fontSizes);
    }
  }

  onMount(() => {
    updateThemeColors();
    
    // Listen for theme changes
    const cleanup = createThemeObserver(() => {
      updateThemeColors();
    });
    
    // Listen for window resize to update font sizes
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

<div class="time-series-chart" bind:this={containerElement}>
  {#if loading}
    <div class="chart-loading">
      <LoadingSpinner />
    </div>
  {:else if error}
    <ErrorBanner error={error} />
  {:else if !data || data.length === 0}
    <div class="chart-empty">
      <p>No hay datos disponibles para el período seleccionado.</p>
    </div>
  {:else if chartConfig}
    <ChartWrapper config={chartConfig} {height} />
  {/if}
</div>

<style>
  .time-series-chart {
    width: 100%;
    position: relative;
  }

  .chart-loading,
  .chart-empty {
    min-height: 400px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--text-secondary);
    font-style: italic;
  }
</style>



