<script lang="ts">
  /**
   * ForecastingTimeSeriesChart - Time series chart showing historical data + predictions.
   * 
   * Features:
   * - Historical data (solid line)
   * - Predicted data (dashed line)
   * - Confidence intervals (optional)
   * - Responsive design
   */
  import { onMount } from 'svelte';
  import ChartWrapper from '../sales/ChartWrapper.svelte';
  import { createTimeSeriesConfig } from '$lib/utils/charts/chartConfig';
  import { transformTimeSeriesData, type TimeSeriesDataPoint } from '$lib/utils/charts/chartHelpers';
  import {
    getChartThemeColors,
    getResponsiveFontSizes,
    createThemeObserver,
    themeColorsChanged,
    type ChartThemeColors
  } from '$lib/utils/charts/useChartTheme';
  import LoadingSpinner from '$lib/components/admin/LoadingSpinner.svelte';
  import ErrorBanner from '$lib/components/admin/ErrorBanner.svelte';
  import type { SegmentedPredictionsResponse } from '$lib/stores/reports';

  export let predictionsData: SegmentedPredictionsResponse | null = null;
  export let moduleKey: "recepcion" | "kidibar" | "total" | null = null;
  export let historicalData: TimeSeriesDataPoint[] = []; // Historical data from reports
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

  // Combine historical and predicted data
  function combineHistoricalAndPredicted(
    historical: TimeSeriesDataPoint[],
    predictions: SegmentedPredictionsResponse | null,
    key: string | null
  ): { historical: TimeSeriesDataPoint[], predicted: TimeSeriesDataPoint[], allData: TimeSeriesDataPoint[] } {
    const predicted: TimeSeriesDataPoint[] = [];

    if (predictions && key && predictions.predictions[key]?.sales) {
      const salesPred = predictions.predictions[key].sales;
      
      // Handle both formats: forecast array or direct forecast property
      const forecast = salesPred.forecast || (salesPred as any)?.forecast;
      
      if (Array.isArray(forecast)) {
        forecast.forEach((day: any) => {
          if (day && day.date && (day.predicted_revenue_cents !== undefined || day.predicted_revenue !== undefined)) {
            const revenue = day.predicted_revenue_cents || day.predicted_revenue || 0;
            const count = day.predicted_count || day.predicted_sales_count || 0;
            predicted.push({
              date: day.date,
              revenue: revenue,
              sales_count: count,
              atv: count > 0 ? revenue / count : 0,
            });
          }
        });
      }
    }

    // Combine all data for chart
    const allData = [...historical, ...predicted];

    return { historical, predicted, allData };
  }

  // Reactive statement to update chart config
  $: {
    const _ = themeUpdateTrigger;
    
    if (containerElement && predictionsData && moduleKey) {
      const { historical, predicted, allData } = combineHistoricalAndPredicted(
        historicalData,
        predictionsData,
        moduleKey
      );

      if (allData.length > 0) {
        // Transform data for chart
        const transformed = transformTimeSeriesData(allData, 'revenue');
        
        // Create base config
        const baseConfig = createTimeSeriesConfig(transformed, containerElement, themeColors, fontSizes);
        
        // Modify to show historical vs predicted with different styles
        if (baseConfig.data && baseConfig.data.datasets && baseConfig.data.datasets.length > 0) {
          const dataset = baseConfig.data.datasets[0];
          
          // Find the split point between historical and predicted
          const splitIndex = historical.length;
          
          if (splitIndex > 0 && predicted.length > 0) {
            // Get confidence level to calculate bands
            const salesPred = predictionsData.predictions[moduleKey]?.sales;
            const confidence = salesPred?.confidence || predictionsData.overall_confidence || 'medium';
            
            // Calculate confidence intervals (percentage variation based on confidence level)
            const confidenceRanges: { [key: string]: number } = {
              'high': 0.10,   // ±10% for high confidence
              'medium': 0.20, // ±20% for medium confidence
              'low': 0.35     // ±35% for low confidence
            };
            const confidenceRange = confidenceRanges[confidence] || 0.20;
            
            // Extract predicted values
            const predictedValues = dataset.data.slice(splitIndex) as number[];
            const predictedLabels = baseConfig.data.labels?.slice(splitIndex) || [];
            
            // Calculate upper and lower bounds
            const upperBounds = predictedValues.map(value => value * (1 + confidenceRange));
            const lowerBounds = predictedValues.map(value => Math.max(0, value * (1 - confidenceRange)));
            
            // Create confidence band datasets (fill area between upper and lower)
            const confidenceColor = themeColors.accent || '#f59e0b';
            const confidenceAlpha = '20'; // ~12.5% opacity
            
            baseConfig.data.datasets = [
              {
                ...dataset,
                label: 'Histórico',
                data: dataset.data.slice(0, splitIndex),
                borderColor: themeColors.primary || '#0093f7',
                backgroundColor: themeColors.primary ? `${themeColors.primary}33` : '#0093f733',
                borderWidth: 2,
                borderDash: [],
                pointRadius: 3,
                pointHoverRadius: 5,
                fill: false,
              },
              // Upper confidence bound (hidden line, only for fill)
              {
                label: 'Límite Superior',
                data: [...Array(splitIndex).fill(null), ...upperBounds],
                borderColor: 'transparent',
                backgroundColor: 'transparent',
                borderWidth: 0,
                pointRadius: 0,
                fill: '+1', // Fill to next dataset (lower bound)
                tension: 0.4,
                order: 3,
              },
              // Lower confidence bound (hidden line, only for fill)
              {
                label: 'Límite Inferior',
                data: [...Array(splitIndex).fill(null), ...lowerBounds],
                borderColor: 'transparent',
                backgroundColor: `${confidenceColor}${confidenceAlpha}`,
                borderWidth: 0,
                pointRadius: 0,
                fill: false,
                tension: 0.4,
                order: 3,
              },
              // Prediction line
              {
                ...dataset,
                label: 'Predicción',
                data: dataset.data.slice(splitIndex),
                borderColor: confidenceColor,
                backgroundColor: `${confidenceColor}33`,
                borderWidth: 2,
                borderDash: [5, 5],
                pointRadius: 3,
                pointHoverRadius: 5,
                fill: false,
                order: 2,
              },
            ];
          } else {
            // Only one dataset
            dataset.label = historical.length > 0 ? 'Histórico' : 'Predicción';
            dataset.fill = false;
          }
        }
        
        chartConfig = baseConfig;
      } else {
        chartConfig = null;
      }
    } else {
      chartConfig = null;
    }
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

<div class="forecasting-chart" bind:this={containerElement}>
  {#if loading}
    <div class="chart-loading">
      <LoadingSpinner />
    </div>
  {:else if error}
    <ErrorBanner error={error} />
  {:else if !chartConfig}
    <div class="chart-empty">
      <p>No hay datos disponibles para mostrar el gráfico.</p>
    </div>
  {:else if chartConfig}
    <ChartWrapper config={chartConfig} {height} />
  {/if}
</div>

<style>
  .forecasting-chart {
    width: 100%;
    position: relative;
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

