<script lang="ts">
  /**
   * FinancialOverview - Financial KPIs overview component.
   */
  import type { FinancialKPIs } from "$lib/stores/reports";
  import { formatPrice, formatPercentChange } from "$lib/stores/reports";
  import { DollarSign, TrendingUp, TrendingDown, Minus, Target } from "lucide-svelte";

  export let financialKPIs: FinancialKPIs;

  $: trendIcon = financialKPIs.revenueTrend?.trend === "up" ? TrendingUp :
                  financialKPIs.revenueTrend?.trend === "down" ? TrendingDown : Minus;

  $: trendColor = financialKPIs.revenueTrend?.trend === "up" ? "var(--accent-success)" :
                   financialKPIs.revenueTrend?.trend === "down" ? "var(--accent-danger)" :
                   "var(--text-secondary)";
</script>

<div class="financial-overview">
  <h3 class="section-title">Métricas Financieras</h3>
  
  <div class="financial-grid">
    <!-- Total Revenue -->
    <div class="metric-card primary">
      <div class="metric-header">
        <DollarSign size={20} class="metric-icon" />
        <span class="metric-label">Revenue Total</span>
      </div>
      <div class="metric-value">{formatPrice(financialKPIs.totalRevenue)}</div>
      
      {#if financialKPIs.revenueTrend}
        <div class="metric-trend" style="color: {trendColor}">
          <svelte:component this={trendIcon} size={16} />
          <span>{formatPercentChange(financialKPIs.revenueTrend.change_percent)}</span>
          <span class="trend-label">vs período anterior</span>
        </div>
      {/if}
    </div>

    <!-- ATV -->
    <div class="metric-card">
      <div class="metric-header">
        <Target size={20} class="metric-icon" />
        <span class="metric-label">Ticket Promedio (ATV)</span>
      </div>
      <div class="metric-value">{formatPrice(financialKPIs.atv)}</div>
    </div>

    <!-- Projected Revenue -->
    {#if financialKPIs.projectedRevenue}
      <div class="metric-card highlight">
        <div class="metric-header">
          <TrendingUp size={20} class="metric-icon" />
          <span class="metric-label">Revenue Proyectado (7 días)</span>
        </div>
        <div class="metric-value">{formatPrice(financialKPIs.projectedRevenue)}</div>
        <div class="metric-note">Basado en forecasting</div>
      </div>
    {/if}

    <!-- Revenue by Module -->
    {#if financialKPIs.revenueByModule}
      <div class="metric-card breakdown">
        <div class="metric-header">
          <span class="metric-label">Revenue por Módulo</span>
        </div>
        <div class="module-breakdown">
          <div class="module-item">
            <span class="module-label">Recepción</span>
            <span class="module-value">{formatPrice(financialKPIs.revenueByModule.recepcion)}</span>
          </div>
          <div class="module-item">
            <span class="module-label">KidiBar</span>
            <span class="module-value">{formatPrice(financialKPIs.revenueByModule.kidibar)}</span>
          </div>
          <div class="module-item total">
            <span class="module-label">Total</span>
            <span class="module-value">{formatPrice(financialKPIs.revenueByModule.total)}</span>
          </div>
        </div>
      </div>
    {/if}
  </div>
</div>

<style>
  .financial-overview {
    width: 100%;
    margin-bottom: var(--spacing-xl);
  }

  .section-title {
    font-size: var(--text-xl);
    font-weight: 700;
    color: var(--text-primary);
    margin: 0 0 var(--spacing-lg) 0;
  }

  .financial-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(min(280px, 100%), 1fr));
    gap: var(--spacing-lg);
  }

  .metric-card {
    padding: var(--spacing-lg);
    background: var(--theme-bg-card);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
    box-shadow: var(--shadow-sm);
    transition: all 0.2s ease;
  }

  .metric-card:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-md);
    border-color: var(--accent-primary);
  }

  .metric-card.primary {
    border-color: var(--accent-primary);
    border-width: 2px;
  }

  .metric-card.highlight {
    border-color: var(--accent-success);
    background: rgba(34, 197, 94, 0.05);
  }

  .metric-header {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    margin-bottom: var(--spacing-md);
  }

  .metric-icon {
    color: var(--accent-primary);
  }

  .metric-label {
    font-size: var(--text-sm);
    color: var(--text-secondary);
    font-weight: 500;
  }

  .metric-value {
    font-size: var(--text-2xl);
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: var(--spacing-sm);
  }

  .metric-trend {
    display: flex;
    align-items: center;
    gap: var(--spacing-xs);
    font-size: var(--text-sm);
    font-weight: 600;
  }

  .trend-label {
    font-size: var(--text-xs);
    color: var(--text-secondary);
    font-weight: 400;
  }

  .metric-note {
    font-size: var(--text-xs);
    color: var(--text-secondary);
    margin-top: var(--spacing-xs);
  }

  .module-breakdown {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-md);
  }

  .module-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: var(--spacing-sm);
    border-radius: var(--radius-sm);
    background: var(--theme-bg-secondary);
  }

  .module-item.total {
    border-top: 1px solid var(--border-primary);
    padding-top: var(--spacing-md);
    margin-top: var(--spacing-xs);
    background: transparent;
    font-weight: 600;
  }

  .module-label {
    font-size: var(--text-sm);
    color: var(--text-secondary);
  }

  .module-value {
    font-size: var(--text-base);
    font-weight: 600;
    color: var(--text-primary);
  }

  .module-item.total .module-label,
  .module-item.total .module-value {
    font-size: var(--text-base);
    color: var(--text-primary);
  }

  @media (max-width: 640px) {
    .financial-grid {
      grid-template-columns: 1fr;
    }
  }
</style>


