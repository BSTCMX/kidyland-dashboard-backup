<script lang="ts">
  /**
   * ComparisonCard component - Displays a metric with comparison to previous period.
   * 
   * Shows current value, percentage change, and trend indicator.
   */
  import { TrendingUp, TrendingDown, Minus } from "lucide-svelte";
  import type { ComparisonData } from "$lib/stores/reports";
  import { formatPrice, formatPercentChange } from "$lib/stores/reports";

  export let title: string;
  export let comparison: ComparisonData;
  export let formatValue: (value: number) => string = (v) => v.toString();
  export let showCurrency: boolean = false;

  $: displayValue = showCurrency 
    ? formatPrice(comparison.current)
    : formatValue(comparison.current);
  
  $: changeDisplay = formatPercentChange(comparison.change_percent);
  $: trendIcon = comparison.trend === "up" 
    ? TrendingUp 
    : comparison.trend === "down" 
    ? TrendingDown 
    : Minus;
  $: trendColor = comparison.trend === "up"
    ? "var(--accent-success)"
    : comparison.trend === "down"
    ? "var(--accent-danger)"
    : "var(--text-secondary)";
</script>

<div class="comparison-card">
  <div class="card-header">
    <h3 class="card-title">{title}</h3>
  </div>
  
  <div class="card-content">
    <div class="metric-value">{displayValue}</div>
    
    <div class="comparison-info" class:trend-up={comparison.trend === "up"} class:trend-down={comparison.trend === "down"} class:trend-stable={comparison.trend === "stable"}>
      <svelte:component this={trendIcon} size={16} strokeWidth={2} />
      <span class="change-text">{changeDisplay}</span>
      <span class="change-label">vs período anterior</span>
    </div>
  </div>
</div>

<style>
  .comparison-card {
    background: var(--theme-bg-card);
    backdrop-filter: blur(16px) saturate(150%);
    -webkit-backdrop-filter: blur(16px) saturate(150%);
    border: 1px solid var(--border-primary);
    border-radius: 16px;
    padding: var(--spacing-lg);
    box-shadow: 
      0 8px 24px rgba(0, 0, 0, 0.15),
      0 0 20px var(--glow-primary),
      inset 0 1px 0 rgba(255, 255, 255, 0.05);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }

  .comparison-card:hover {
    transform: translateY(-4px);
    border-color: rgba(0, 147, 247, 0.5);
    box-shadow: 
      0 12px 32px rgba(0, 0, 0, 0.2),
      0 0 30px var(--glow-primary),
      0 0 40px var(--glow-secondary),
      inset 0 1px 0 rgba(255, 255, 255, 0.1);
  }

  .card-header {
    margin-bottom: var(--spacing-md);
  }

  .card-title {
    font-size: var(--text-sm);
    font-weight: 600;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin: 0;
  }

  .card-content {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-sm);
  }

  .metric-value {
    font-size: var(--text-3xl);
    font-weight: 700;
    color: var(--accent-primary);
    line-height: 1.2;
  }

  .comparison-info {
    display: flex;
    align-items: center;
    gap: var(--spacing-xs);
    font-size: var(--text-sm);
    padding: var(--spacing-xs) var(--spacing-sm);
    border-radius: var(--radius-sm);
    background: var(--theme-bg-elevated);
  }

  .comparison-info.trend-up {
    color: var(--accent-success);
  }

  .comparison-info.trend-down {
    color: var(--accent-danger);
  }

  .comparison-info.trend-stable {
    color: var(--text-secondary);
  }

  .change-text {
    font-weight: 600;
  }

  .change-label {
    color: var(--text-secondary);
    font-size: var(--text-xs);
    margin-left: auto;
  }

  @media (max-width: 768px) {
    .comparison-card {
      padding: var(--spacing-md);
    }

    .metric-value {
      font-size: var(--text-2xl);
    }

    .comparison-info {
      flex-wrap: wrap;
    }

    .change-label {
      width: 100%;
      margin-left: 0;
      margin-top: var(--spacing-xs);
    }
  }
</style>





