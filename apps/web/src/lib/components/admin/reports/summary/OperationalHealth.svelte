<script lang="ts">
  /**
   * OperationalHealth - Operational KPIs overview component.
   */
  import type { OperationalKPIs } from "$lib/stores/reports";
  import { Activity, Package, DollarSign, AlertCircle } from "lucide-svelte";

  export let operationalKPIs: OperationalKPIs;

  function formatPercent(value: number): string {
    return `${value.toFixed(1)}%`;
  }
</script>

<div class="operational-health">
  <h3 class="section-title">Salud Operacional</h3>
  
  <div class="operational-grid">
    <!-- Active Services -->
    <div class="metric-card">
      <div class="metric-header">
        <Activity size={20} class="metric-icon" />
        <span class="metric-label">Servicios Activos</span>
      </div>
      <div class="metric-value">{operationalKPIs.activeServices}</div>
      <div class="metric-subtitle">En uso actualmente</div>
    </div>

    <!-- Utilization Rate -->
    <div class="metric-card">
      <div class="metric-header">
        <Activity size={20} class="metric-icon" />
        <span class="metric-label">Tasa de Utilización</span>
      </div>
      <div class="metric-value" style="color: {operationalKPIs.utilizationRate >= 70 ? 'var(--accent-success)' : operationalKPIs.utilizationRate >= 50 ? 'var(--accent-warning)' : 'var(--accent-danger)'}">
        {formatPercent(operationalKPIs.utilizationRate)}
      </div>
      <div class="metric-progress">
        <div 
          class="progress-bar" 
          style="width: {operationalKPIs.utilizationRate}%; background: {operationalKPIs.utilizationRate >= 70 ? 'var(--accent-success)' : operationalKPIs.utilizationRate >= 50 ? 'var(--accent-warning)' : 'var(--accent-danger)'};"
        ></div>
      </div>
    </div>

    <!-- Stock Health -->
    <div class="metric-card">
      <div class="metric-header">
        <Package size={20} class="metric-icon" />
        <span class="metric-label">Salud de Inventario</span>
      </div>
      <div class="metric-value" style="color: {operationalKPIs.stockHealth >= 80 ? 'var(--accent-success)' : operationalKPIs.stockHealth >= 60 ? 'var(--accent-warning)' : 'var(--accent-danger)'}">
        {formatPercent(operationalKPIs.stockHealth)}
      </div>
      <div class="metric-subtitle">Productos con stock adecuado</div>
      <div class="metric-progress">
        <div 
          class="progress-bar" 
          style="width: {operationalKPIs.stockHealth}%; background: {operationalKPIs.stockHealth >= 80 ? 'var(--accent-success)' : operationalKPIs.stockHealth >= 60 ? 'var(--accent-warning)' : 'var(--accent-danger)'};"
        ></div>
      </div>
    </div>

    <!-- Arqueos Accuracy -->
    <div class="metric-card">
      <div class="metric-header">
        <DollarSign size={20} class="metric-icon" />
        <span class="metric-label">Precisión Arqueos</span>
      </div>
      <div class="metric-value" style="color: {operationalKPIs.arqueosAccuracy >= 90 ? 'var(--accent-success)' : operationalKPIs.arqueosAccuracy >= 70 ? 'var(--accent-warning)' : 'var(--accent-danger)'}">
        {formatPercent(operationalKPIs.arqueosAccuracy)}
      </div>
      <div class="metric-subtitle">Coincidencias perfectas</div>
      {#if operationalKPIs.discrepancyRate > 0}
        <div class="metric-warning">
          <AlertCircle size={14} />
          <span>Tasa de discrepancias: {formatPercent(operationalKPIs.discrepancyRate)}</span>
        </div>
      {/if}
    </div>
  </div>
</div>

<style>
  .operational-health {
    width: 100%;
    margin-bottom: var(--spacing-xl);
  }

  .section-title {
    font-size: var(--text-xl);
    font-weight: 700;
    color: var(--text-primary);
    margin: 0 0 var(--spacing-lg) 0;
  }

  .operational-grid {
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
    margin-bottom: var(--spacing-xs);
  }

  .metric-subtitle {
    font-size: var(--text-xs);
    color: var(--text-secondary);
    margin-bottom: var(--spacing-sm);
  }

  .metric-progress {
    width: 100%;
    height: 6px;
    background: var(--theme-bg-secondary);
    border-radius: var(--radius-full);
    overflow: hidden;
    margin-top: var(--spacing-sm);
  }

  .progress-bar {
    height: 100%;
    border-radius: var(--radius-full);
    transition: width 0.3s ease;
  }

  .metric-warning {
    display: flex;
    align-items: center;
    gap: var(--spacing-xs);
    margin-top: var(--spacing-sm);
    padding: var(--spacing-xs);
    background: rgba(239, 68, 68, 0.1);
    border-radius: var(--radius-sm);
    font-size: var(--text-xs);
    color: var(--accent-danger);
  }

  @media (max-width: 640px) {
    .operational-grid {
      grid-template-columns: 1fr;
    }
  }
</style>


