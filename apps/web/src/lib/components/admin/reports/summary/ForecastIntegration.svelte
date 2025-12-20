<script lang="ts">
  /**
   * ForecastIntegration - Forecast projections vs current performance.
   */
  import type { ForecastProjection, FinancialKPIs } from "$lib/stores/reports";
  import { formatPrice } from "$lib/stores/reports";
  import { TrendingUp, TrendingDown, Target, AlertCircle } from "lucide-svelte";

  export let forecastProjections: ForecastProjection;
  export let currentRevenue: number;

  $: confidenceLabels = {
    high: "Alta",
    medium: "Media",
    low: "Baja"
  };

  $: confidenceColors = {
    high: "var(--accent-success)",
    medium: "#f59e0b",
    low: "var(--accent-danger)"
  };

  $: gap7Days = forecastProjections.next7Days.projectedRevenue - (currentRevenue / 4); // Approximate weekly revenue
  $: gap30Days = forecastProjections.next30Days.projectedRevenue - (currentRevenue / 4 * 4); // Approximate monthly revenue
</script>

<div class="forecast-integration">
  <h3 class="section-title">Proyecciones y Forecasting</h3>
  
  <div class="forecast-grid">
    <!-- Next 7 Days -->
    <div class="forecast-card">
      <div class="forecast-header">
        <Target size={20} class="forecast-icon" />
        <span class="forecast-label">Próximos 7 Días</span>
        <span 
          class="confidence-badge" 
          style="background: {confidenceColors[forecastProjections.next7Days.confidence]}"
        >
          {confidenceLabels[forecastProjections.next7Days.confidence]}
        </span>
      </div>
      
      <div class="forecast-content">
        <div class="projected-revenue">
          <div class="projected-label">Revenue Proyectado</div>
          <div class="projected-value">{formatPrice(forecastProjections.next7Days.projectedRevenue)}</div>
        </div>
        
        <div class="projected-count">
          <div class="projected-label">Ventas Proyectadas</div>
          <div class="projected-value">{forecastProjections.next7Days.projectedCount}</div>
        </div>

        {#if gap7Days !== 0}
          <div class="projected-gap" class:positive={gap7Days > 0} class:negative={gap7Days < 0}>
            <svelte:component this={gap7Days > 0 ? TrendingUp : TrendingDown} size={14} />
            <span>
              {gap7Days > 0 ? "+" : ""}{formatPrice(gap7Days)} 
              {gap7Days > 0 ? "más" : "menos"} que el promedio actual
            </span>
          </div>
        {/if}
      </div>
    </div>

    <!-- Next 30 Days -->
    <div class="forecast-card">
      <div class="forecast-header">
        <Target size={20} class="forecast-icon" />
        <span class="forecast-label">Próximos 30 Días</span>
        <span 
          class="confidence-badge" 
          style="background: {confidenceColors[forecastProjections.next30Days.confidence]}"
        >
          {confidenceLabels[forecastProjections.next30Days.confidence]}
        </span>
      </div>
      
      <div class="forecast-content">
        <div class="projected-revenue">
          <div class="projected-label">Revenue Proyectado</div>
          <div class="projected-value">{formatPrice(forecastProjections.next30Days.projectedRevenue)}</div>
        </div>
        
        <div class="projected-count">
          <div class="projected-label">Ventas Proyectadas</div>
          <div class="projected-value">{forecastProjections.next30Days.projectedCount}</div>
        </div>

        {#if gap30Days !== 0}
          <div class="projected-gap" class:positive={gap30Days > 0} class:negative={gap30Days < 0}>
            <svelte:component this={gap30Days > 0 ? TrendingUp : TrendingDown} size={14} />
            <span>
              {gap30Days > 0 ? "+" : ""}{formatPrice(gap30Days)} 
              {gap30Days > 0 ? "más" : "menos"} que el promedio actual
            </span>
          </div>
        {/if}
      </div>
    </div>

    <!-- Overall Confidence -->
    <div class="forecast-card info">
      <div class="forecast-header">
        <AlertCircle size={20} class="forecast-icon" />
        <span class="forecast-label">Nivel de Confianza General</span>
      </div>
      
      <div class="confidence-content">
        <div 
          class="confidence-value" 
          style="color: {confidenceColors[forecastProjections.overallConfidence]}"
        >
          {confidenceLabels[forecastProjections.overallConfidence]}
        </div>
        <div class="confidence-note">
          Basado en análisis histórico y patrones identificados
        </div>
      </div>
    </div>
  </div>
</div>

<style>
  .forecast-integration {
    width: 100%;
    margin-bottom: var(--spacing-xl);
  }

  .section-title {
    font-size: var(--text-xl);
    font-weight: 700;
    color: var(--text-primary);
    margin: 0 0 var(--spacing-lg) 0;
  }

  .forecast-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(min(300px, 100%), 1fr));
    gap: var(--spacing-lg);
  }

  .forecast-card {
    padding: var(--spacing-lg);
    background: var(--theme-bg-card);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
    box-shadow: var(--shadow-sm);
    transition: all 0.2s ease;
  }

  .forecast-card:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-md);
    border-color: var(--accent-primary);
  }

  .forecast-card.info {
    border-color: var(--accent-info);
    background: rgba(59, 130, 246, 0.05);
  }

  .forecast-header {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    margin-bottom: var(--spacing-md);
    flex-wrap: wrap;
  }

  .forecast-icon {
    color: var(--accent-primary);
  }

  .forecast-label {
    font-size: var(--text-sm);
    color: var(--text-secondary);
    font-weight: 600;
    flex: 1;
  }

  .confidence-badge {
    font-size: var(--text-xs);
    font-weight: 600;
    color: white;
    padding: 4px 8px;
    border-radius: var(--radius-sm);
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .forecast-content {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-md);
  }

  .projected-revenue,
  .projected-count {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xs);
  }

  .projected-label {
    font-size: var(--text-xs);
    color: var(--text-secondary);
    font-weight: 500;
  }

  .projected-value {
    font-size: var(--text-xl);
    font-weight: 700;
    color: var(--text-primary);
  }

  .projected-gap {
    display: flex;
    align-items: center;
    gap: var(--spacing-xs);
    padding: var(--spacing-sm);
    border-radius: var(--radius-sm);
    font-size: var(--text-xs);
    font-weight: 600;
    margin-top: var(--spacing-xs);
  }

  .projected-gap.positive {
    background: rgba(34, 197, 94, 0.1);
    color: var(--accent-success);
  }

  .projected-gap.negative {
    background: rgba(239, 68, 68, 0.1);
    color: var(--accent-danger);
  }

  .confidence-content {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xs);
  }

  .confidence-value {
    font-size: var(--text-2xl);
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .confidence-note {
    font-size: var(--text-xs);
    color: var(--text-secondary);
    line-height: 1.5;
  }

  @media (max-width: 640px) {
    .forecast-grid {
      grid-template-columns: 1fr;
    }
  }
</style>


