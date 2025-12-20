<script lang="ts">
  /**
   * CustomerInsights - Customer KPIs overview component.
   */
  import type { CustomerKPIs } from "$lib/stores/reports";
  import { formatPrice, formatPercentChange } from "$lib/stores/reports";
  import { Users, UserPlus, DollarSign, TrendingUp, TrendingDown, Minus } from "lucide-svelte";

  export let customerKPIs: CustomerKPIs;

  $: trendIcon = customerKPIs.customerGrowth?.trend === "up" ? TrendingUp :
                  customerKPIs.customerGrowth?.trend === "down" ? TrendingDown : Minus;

  $: trendColor = customerKPIs.customerGrowth?.trend === "up" ? "var(--accent-success)" :
                   customerKPIs.customerGrowth?.trend === "down" ? "var(--accent-danger)" :
                   "var(--text-secondary)";
</script>

<div class="customer-insights">
  <h3 class="section-title">Métricas de Clientes</h3>
  
  <div class="customer-grid">
    <!-- Unique Customers -->
    <div class="metric-card primary">
      <div class="metric-header">
        <Users size={20} class="metric-icon" />
        <span class="metric-label">Clientes Únicos</span>
      </div>
      <div class="metric-value">{customerKPIs.uniqueCustomers}</div>
      {#if customerKPIs.customerGrowth}
        <div class="metric-trend" style="color: {trendColor}">
          <svelte:component this={trendIcon} size={16} />
          <span>{formatPercentChange(customerKPIs.customerGrowth.change_percent)}</span>
        </div>
      {/if}
    </div>

    <!-- New Customers -->
    <div class="metric-card highlight">
      <div class="metric-header">
        <UserPlus size={20} class="metric-icon" />
        <span class="metric-label">Clientes Nuevos</span>
      </div>
      <div class="metric-value">{customerKPIs.newCustomers}</div>
      {#if customerKPIs.uniqueCustomers > 0}
        <div class="metric-subtitle">
          {((customerKPIs.newCustomers / customerKPIs.uniqueCustomers) * 100).toFixed(1)}% del total
        </div>
      {/if}
    </div>

    <!-- Average Revenue per Customer -->
    <div class="metric-card">
      <div class="metric-header">
        <DollarSign size={20} class="metric-icon" />
        <span class="metric-label">Revenue Promedio por Cliente</span>
      </div>
      <div class="metric-value">{formatPrice(customerKPIs.avgRevenuePerCustomer)}</div>
      <div class="metric-subtitle">
        {customerKPIs.uniqueCustomers > 0 
          ? `Basado en ${customerKPIs.uniqueCustomers} clientes únicos`
          : 'Sin datos disponibles'}
      </div>
    </div>

    <!-- Top Customers -->
    <div class="metric-card">
      <div class="metric-header">
        <Users size={20} class="metric-icon" />
        <span class="metric-label">Clientes Top</span>
      </div>
      <div class="metric-value">{customerKPIs.topCustomersCount}</div>
      <div class="metric-subtitle">Clientes activos identificados</div>
    </div>
  </div>
</div>

<style>
  .customer-insights {
    width: 100%;
    margin-bottom: var(--spacing-xl);
  }

  .section-title {
    font-size: var(--text-xl);
    font-weight: 700;
    color: var(--text-primary);
    margin: 0 0 var(--spacing-lg) 0;
  }

  .customer-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(min(250px, 100%), 1fr));
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

  .metric-subtitle {
    font-size: var(--text-xs);
    color: var(--text-secondary);
    margin-top: var(--spacing-xs);
  }

  @media (max-width: 640px) {
    .customer-grid {
      grid-template-columns: 1fr;
    }
  }
</style>


