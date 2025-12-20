<script lang="ts">
  /**
   * SalesBarChart - Bar chart for sales data.
   * 
   * Displays revenue or sales count by category.
   * Responsive and accessible with reactive theme support.
   */
  import { onMount } from 'svelte';
  import ChartWrapper from './ChartWrapper.svelte';
  import { createBarChartConfig } from '$lib/utils/charts/chartConfig';
  import { transformGroupedData, type GroupedDataPoint } from '$lib/utils/charts/chartHelpers';
  import {
    getChartThemeColors,
    getResponsiveFontSizes,
    createThemeObserver,
    themeColorsChanged,
    type ChartThemeColors
  } from '$lib/utils/charts/useChartTheme';
  import LoadingSpinner from '$lib/components/admin/LoadingSpinner.svelte';
  import ErrorBanner from '$lib/components/admin/ErrorBanner.svelte';

  export let data: GroupedDataPoint[] = [];
  export let label: string = 'Valor';
  export let height: string = '400px';
  export let loading: boolean = false;
  export let error: string | null = null;
  export let horizontal: boolean = false;

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

  // Reactive statement to update chart config when data, theme, or horizontal changes
  $: {
    // Include themeUpdateTrigger to force recalculation when theme changes
    const _ = themeUpdateTrigger;
    
    if (data && data.length > 0 && containerElement) {
      const transformed = transformGroupedData(data, label);
      const config = createBarChartConfig(transformed, containerElement, themeColors, fontSizes);
      
      // Set horizontal if needed
      if (horizontal) {
        config.options.indexAxis = 'y';
      }
      
      chartConfig = config;
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

<div class="bar-chart" bind:this={containerElement}>
  {#if loading}
    <div class="chart-loading">
      <LoadingSpinner />
    </div>
  {:else if error}
    <ErrorBanner error={error} />
  {:else if !data || data.length === 0}
    <div class="chart-empty">
      <p>No hay datos disponibles para mostrar.</p>
    </div>
  {:else if chartConfig}
    <ChartWrapper config={chartConfig} {height} />
  {/if}
</div>

<style>
  .bar-chart {
    width: 100%;
    background: var(--theme-bg-card);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-lg, 12px);
    padding: var(--spacing-lg, 1.5rem);
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  }

  .chart-loading,
  .chart-empty {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 400px;
    color: var(--text-secondary);
  }

  .chart-empty p {
    margin: 0;
    font-size: var(--text-base, 1rem);
  }

  @media (max-width: 640px) {
    .bar-chart {
      padding: var(--spacing-md, 1rem);
    }
  }
</style>

