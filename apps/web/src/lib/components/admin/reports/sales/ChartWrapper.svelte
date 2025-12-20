<script lang="ts">
  /**
   * ChartWrapper - Generic wrapper component for Chart.js charts in Svelte.
   * 
   * Handles Chart.js lifecycle, SSR compatibility, and responsive updates.
   * Follows Clean Architecture principles.
   */
  import { onMount, onDestroy, afterUpdate } from 'svelte';
  import { browser } from '$app/environment';
  import type { ChartConfiguration, Chart } from 'chart.js';

  export let config: ChartConfiguration;
  export let height: string = '400px';

  let canvasElement: HTMLCanvasElement;
  let chartInstance: Chart | null = null;

  onMount(() => {
    if (!browser || !canvasElement) return;

    // Dynamic import to avoid SSR issues
    import('chart.js/auto').then(({ Chart: ChartJS }) => {
      if (canvasElement && !chartInstance) {
        chartInstance = new ChartJS(canvasElement, config);
      }
    });
  });

  afterUpdate(() => {
    if (!browser || !chartInstance || !canvasElement) return;

    // Update chart when config changes
    chartInstance.data = config.data;
    chartInstance.options = config.options;
    chartInstance.update('none'); // 'none' prevents animation on data updates
  });

  onDestroy(() => {
    if (chartInstance) {
      chartInstance.destroy();
      chartInstance = null;
    }
  });
</script>

<div class="chart-container" style="height: {height}; position: relative;">
  <canvas bind:this={canvasElement}></canvas>
</div>

<style>
  .chart-container {
    width: 100%;
    position: relative;
  }

  .chart-container canvas {
    max-width: 100%;
    height: auto;
  }
</style>



