<script lang="ts">
  /**
   * SalesAdvancedMetrics - Advanced sales metrics component.
   * 
   * Displays calculated metrics like CLV, purchase frequency, etc.
   * Based on available sales data.
   */
  import { TrendingUp, Users, Repeat, DollarSign } from 'lucide-svelte';
  import { formatPrice } from '$lib/stores/reports';

  export let salesCount: number = 0;
  export let totalRevenueCents: number = 0;
  export let averageTransactionValueCents: number = 0;
  export let uniqueCustomers: number = 0; // This would need to come from backend

  // Calculate metrics
  $: averageRevenuePerCustomer = uniqueCustomers > 0 
    ? totalRevenueCents / uniqueCustomers 
    : 0;
  
  $: purchaseFrequency = uniqueCustomers > 0 
    ? salesCount / uniqueCustomers 
    : 0;
  
  $: customerLifetimeValue = averageRevenuePerCustomer * purchaseFrequency;
</script>

<div class="advanced-metrics">
  <h3 class="section-title">Métricas Avanzadas</h3>
  <div class="metrics-grid">
    {#if uniqueCustomers > 0}
      <div class="metric-card">
        <div class="metric-icon">
          <Users size={24} strokeWidth={1.5} />
        </div>
        <div class="metric-content">
          <h4 class="metric-title">Clientes Únicos</h4>
          <div class="metric-value">{uniqueCustomers}</div>
        </div>
      </div>

      <div class="metric-card">
        <div class="metric-icon">
          <DollarSign size={24} strokeWidth={1.5} />
        </div>
        <div class="metric-content">
          <h4 class="metric-title">Revenue por Cliente</h4>
          <div class="metric-value">{formatPrice(averageRevenuePerCustomer)}</div>
        </div>
      </div>

      <div class="metric-card">
        <div class="metric-icon">
          <Repeat size={24} strokeWidth={1.5} />
        </div>
        <div class="metric-content">
          <h4 class="metric-title">Frecuencia de Compra</h4>
          <div class="metric-value">{purchaseFrequency.toFixed(2)}</div>
          <div class="metric-subtitle">compras por cliente</div>
        </div>
      </div>

      <div class="metric-card">
        <div class="metric-icon">
          <TrendingUp size={24} strokeWidth={1.5} />
        </div>
        <div class="metric-content">
          <h4 class="metric-title">CLV Aproximado</h4>
          <div class="metric-value">{formatPrice(customerLifetimeValue)}</div>
          <div class="metric-subtitle">Customer Lifetime Value</div>
        </div>
      </div>
    {:else}
      <div class="metric-card empty">
        <p>Las métricas avanzadas requieren datos de clientes únicos.</p>
        <p class="metric-note">Estos datos se pueden obtener del backend.</p>
      </div>
    {/if}
  </div>
</div>

<style>
  .advanced-metrics {
    width: 100%;
  }

  .section-title {
    font-size: var(--text-xl, 1.25rem);
    font-weight: 700;
    color: var(--text-primary);
    margin: 0 0 var(--spacing-lg, 1.5rem) 0;
  }

  .metrics-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(min(250px, 100%), 1fr));
    gap: var(--spacing-md, 1rem);
  }

  .metric-card {
    background: var(--theme-bg-card);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md, 8px);
    padding: var(--spacing-lg, 1.5rem);
    display: flex;
    align-items: center;
    gap: var(--spacing-md, 1rem);
    transition: all 0.3s ease;
  }

  .metric-card:hover {
    border-color: var(--accent-primary);
    box-shadow: 0 4px 12px rgba(0, 147, 247, 0.1);
  }

  .metric-card.empty {
    flex-direction: column;
    text-align: center;
    padding: var(--spacing-xl, 2rem);
  }

  .metric-icon {
    color: var(--accent-primary);
    flex-shrink: 0;
  }

  .metric-content {
    flex: 1;
  }

  .metric-title {
    font-size: var(--text-sm, 0.875rem);
    font-weight: 600;
    color: var(--text-secondary);
    margin: 0 0 var(--spacing-xs, 0.5rem) 0;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .metric-value {
    font-size: var(--text-2xl, 1.5rem);
    font-weight: 700;
    color: var(--text-primary);
    margin: 0;
  }

  .metric-subtitle {
    font-size: var(--text-xs, 0.75rem);
    color: var(--text-secondary);
    margin: var(--spacing-xs, 0.5rem) 0 0 0;
  }

  .metric-note {
    font-size: var(--text-sm, 0.875rem);
    color: var(--text-muted);
    margin: var(--spacing-sm, 0.75rem) 0 0 0;
    font-style: italic;
  }

  @media (max-width: 640px) {
    .metrics-grid {
      grid-template-columns: 1fr;
    }
  }
</style>



