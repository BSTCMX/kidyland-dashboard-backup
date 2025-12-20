<script lang="ts">
  /**
   * CustomersTrends - Comprehensive trends and behavior analysis component.
   */
  import { onMount } from 'svelte';
  import { get } from '@kidyland/utils/api';
  import { formatPrice } from '$lib/stores/reports';
  import LoadingSpinner from '$lib/components/admin/LoadingSpinner.svelte';
  import ErrorBanner from '$lib/components/admin/ErrorBanner.svelte';
  import ChartWrapper from '$lib/components/admin/reports/sales/ChartWrapper.svelte';
  import { TrendingUp, TrendingDown, Minus, AlertTriangle, Users, UserCheck, UserX } from 'lucide-svelte';

  export let sucursalId: string | null = null;
  export let startDate: string | null = null;
  export let endDate: string | null = null;

  interface ChurnIndicators {
    at_risk_count: number;
    hibernating_count: number;
    lost_count: number;
    cannot_lose_count: number;
    churn_probability: number;
  }

  interface SegmentBehavior {
    [segment: string]: {
      customer_count: number;
      percentage: number;
      trend: string;
      growth_rate: number;
    };
  }

  interface TemporalComparison {
    current_period: {
      total_customers: number;
      champions: number;
      at_risk: number;
    };
    previous_period: {
      total_customers: number;
      champions: number;
      at_risk: number;
    } | null;
    changes: {
      customer_growth: number;
      customer_growth_rate: number;
      champions_change: number;
      at_risk_change: number;
    } | null;
    error?: string;
  }

  interface TrendsAnalysis {
    retention_trends: {
      periods: string[];
      retention_rates: number[];
      trend: string;
      average_retention: number;
    };
    churn_indicators: ChurnIndicators;
    segment_behavior: SegmentBehavior;
    temporal_comparisons: TemporalComparison;
    summary: {
      total_customers: number;
      new_customers: number;
      period: {
        start_date: string;
        end_date: string;
      };
    };
  }

  let loading = true;
  let error: string | null = null;
  let trendsData: TrendsAnalysis | null = null;

  const segmentLabels: Record<string, string> = {
    champions: 'Campeones',
    loyal_customers: 'Clientes Leales',
    potential_loyalists: 'Potenciales Leales',
    new_customers: 'Clientes Nuevos',
    promising: 'Prometedores',
    need_attention: 'Necesitan Atención',
    about_to_sleep: 'A Punto de Dormir',
    at_risk: 'En Riesgo',
    cannot_lose: 'No Podemos Perder',
    hibernating: 'Hibernando',
    lost: 'Perdidos'
  };

  async function fetchTrends() {
    loading = true;
    error = null;

    try {
      const params = new URLSearchParams();
      if (sucursalId) params.append('sucursal_id', sucursalId);
      if (startDate) params.append('start_date', startDate);
      if (endDate) params.append('end_date', endDate);

      trendsData = await get<TrendsAnalysis>(`/reports/customers/trends?${params.toString()}`);
    } catch (err: any) {
      error = err.message || 'Error al cargar análisis de tendencias';
    } finally {
      loading = false;
    }
  }

  function getTrendIcon(trend: string) {
    if (trend === 'increasing') return TrendingUp;
    if (trend === 'decreasing') return TrendingDown;
    return Minus;
  }

  function getTrendColor(trend: string) {
    if (trend === 'increasing') return 'var(--accent-success)';
    if (trend === 'decreasing') return 'var(--accent-danger)';
    return 'var(--text-secondary)';
  }

  function getChurnSeverity(probability: number): 'low' | 'medium' | 'high' {
    if (probability < 10) return 'low';
    if (probability < 25) return 'medium';
    return 'high';
  }

  // Get theme colors for Chart.js (Chart.js doesn't support CSS variables directly)
  let textPrimaryColor = '#111827'; // Default light mode
  let textSecondaryColor = '#6b7280'; // Default light mode
  let bgCardColor = '#ffffff'; // Default light mode
  let themeUpdateTrigger = 0; // Trigger to force chart update

  // Chart configuration - must be declared before reactive statement
  let segmentChartConfig: any = null;

  // Update theme colors when component mounts or theme changes
  function updateThemeColors() {
    if (typeof window !== 'undefined') {
      const root = document.documentElement;
      const computedStyle = getComputedStyle(root);
      const newTextPrimary = computedStyle.getPropertyValue('--text-primary').trim() || '#111827';
      const newTextSecondary = computedStyle.getPropertyValue('--text-secondary').trim() || '#6b7280';
      const newBgCard = computedStyle.getPropertyValue('--theme-bg-card').trim() || '#ffffff';
      
      // Only update if colors actually changed
      if (newTextPrimary !== textPrimaryColor || 
          newTextSecondary !== textSecondaryColor || 
          newBgCard !== bgCardColor) {
        textPrimaryColor = newTextPrimary;
        textSecondaryColor = newTextSecondary;
        bgCardColor = newBgCard;
        themeUpdateTrigger++; // Trigger reactive update
      }
    }
  }

  // Chart data for segment distribution
  $: segmentChartData = trendsData ? {
    labels: Object.keys(trendsData.segment_behavior).map(key => segmentLabels[key] || key),
    datasets: [{
      label: 'Clientes por Segmento',
      data: Object.values(trendsData.segment_behavior).map(s => s.customer_count),
      backgroundColor: [
        'rgba(34, 197, 94, 0.8)',   // Champions - green
        'rgba(59, 130, 246, 0.8)',  // Loyal - blue
        'rgba(251, 191, 36, 0.8)',  // Potential - yellow
        'rgba(147, 51, 234, 0.8)',  // New - purple
        'rgba(249, 115, 22, 0.8)',  // Promising - orange
        'rgba(239, 68, 68, 0.8)',   // At Risk - red
        'rgba(107, 114, 128, 0.8)', // Hibernating - gray
      ]
    }]
  } : null;

  // Reactive statement to update chart config when data or theme changes
  $: {
    // Include themeUpdateTrigger to force recalculation when theme changes
    const _ = themeUpdateTrigger;
    segmentChartConfig = segmentChartData ? {
      type: 'doughnut' as const,
      data: segmentChartData,
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'right' as const,
            labels: {
              color: textPrimaryColor,
              font: {
                size: 12,
                family: 'system-ui, -apple-system, sans-serif'
              },
              padding: 12,
              usePointStyle: true,
              pointStyle: 'circle'
            }
          },
          tooltip: {
            backgroundColor: bgCardColor,
            titleColor: textPrimaryColor,
            bodyColor: textPrimaryColor,
            borderColor: textSecondaryColor,
            borderWidth: 1,
            padding: 12,
            titleFont: {
              size: 14,
              weight: '600',
              family: 'system-ui, -apple-system, sans-serif'
            },
            bodyFont: {
              size: 13,
              family: 'system-ui, -apple-system, sans-serif'
            },
            callbacks: {
              label: (context: any) => {
                const label = context.label || '';
                const value = context.parsed || 0;
                const total = context.dataset.data.reduce((a: number, b: number) => a + b, 0);
                const percentage = ((value / total) * 100).toFixed(1);
                return `${label}: ${value} (${percentage}%)`;
              }
            }
          }
        }
      }
    } : null;
  }

  // Track previous params to detect changes
  let previousSucursalId: string | null = null;
  let previousStartDate: string | null = null;
  let previousEndDate: string | null = null;
  
  // Fetch when params change
  $: {
    const paramsChanged = 
      sucursalId !== previousSucursalId ||
      startDate !== previousStartDate ||
      endDate !== previousEndDate;
    
    if (paramsChanged) {
      previousSucursalId = sucursalId;
      previousStartDate = startDate;
      previousEndDate = endDate;
      fetchTrends();
    }
  }

  onMount(() => {
    updateThemeColors();
    fetchTrends();
    
    // Listen for theme changes
    const observer = new MutationObserver(() => {
      updateThemeColors();
    });
    
    if (typeof window !== 'undefined') {
      observer.observe(document.documentElement, {
        attributes: true,
        attributeFilter: ['data-theme']
      });
    }
    
    return () => {
      observer.disconnect();
    };
  });
</script>

<div class="customers-trends-container">
  {#if loading}
    <LoadingSpinner />
  {:else if error}
    <ErrorBanner {error} />
  {:else if trendsData}
    <!-- Summary Cards -->
    <div class="trends-summary-grid">
      <div class="summary-card">
        <div class="summary-header">
          <Users size={20} />
          <h4 class="summary-title">Total Clientes</h4>
        </div>
        <div class="summary-value">{trendsData.summary.total_customers}</div>
        {#if trendsData.temporal_comparisons.changes}
          <div class="summary-change" class:positive={trendsData.temporal_comparisons.changes.customer_growth >= 0}>
            {trendsData.temporal_comparisons.changes.customer_growth >= 0 ? '+' : ''}
            {trendsData.temporal_comparisons.changes.customer_growth} 
            ({trendsData.temporal_comparisons.changes.customer_growth_rate >= 0 ? '+' : ''}
            {trendsData.temporal_comparisons.changes.customer_growth_rate}%)
          </div>
        {/if}
      </div>

      <div class="summary-card">
        <div class="summary-header">
          <UserCheck size={20} />
          <h4 class="summary-title">Nuevos Clientes</h4>
        </div>
        <div class="summary-value">{trendsData.summary.new_customers}</div>
      </div>

      <div class="summary-card" class:churn-high={getChurnSeverity(trendsData.churn_indicators.churn_probability) === 'high'} class:churn-medium={getChurnSeverity(trendsData.churn_indicators.churn_probability) === 'medium'}>
        <div class="summary-header">
          <AlertTriangle size={20} />
          <h4 class="summary-title">Probabilidad de Churn</h4>
        </div>
        <div class="summary-value">{trendsData.churn_indicators.churn_probability}%</div>
        <div class="summary-subtitle">
          {trendsData.churn_indicators.at_risk_count} en riesgo, 
          {trendsData.churn_indicators.hibernating_count} hibernando
        </div>
      </div>

      <div class="summary-card">
        <div class="summary-header">
          <UserX size={20} />
          <h4 class="summary-title">Clientes Perdidos</h4>
        </div>
        <div class="summary-value">{trendsData.churn_indicators.lost_count}</div>
      </div>
    </div>

    <!-- Temporal Comparisons -->
    {#if trendsData.temporal_comparisons.changes}
      <div class="comparison-section">
        <h3 class="section-title">Comparativa Temporal</h3>
        <div class="comparison-grid">
          <div class="comparison-card">
            <h4 class="comparison-label">Crecimiento de Clientes</h4>
            <div class="comparison-value" class:positive={trendsData.temporal_comparisons.changes.customer_growth >= 0}>
              {trendsData.temporal_comparisons.changes.customer_growth >= 0 ? '+' : ''}
              {trendsData.temporal_comparisons.changes.customer_growth}
            </div>
            <div class="comparison-percentage">
              {trendsData.temporal_comparisons.changes.customer_growth_rate >= 0 ? '+' : ''}
              {trendsData.temporal_comparisons.changes.customer_growth_rate}%
            </div>
          </div>

          <div class="comparison-card">
            <h4 class="comparison-label">Cambio en Campeones</h4>
            <div class="comparison-value" class:positive={trendsData.temporal_comparisons.changes.champions_change >= 0}>
              {trendsData.temporal_comparisons.changes.champions_change >= 0 ? '+' : ''}
              {trendsData.temporal_comparisons.changes.champions_change}
            </div>
          </div>

          <div class="comparison-card">
            <h4 class="comparison-label">Cambio en Riesgo</h4>
            <div class="comparison-value" class:positive={trendsData.temporal_comparisons.changes.at_risk_change <= 0}>
              {trendsData.temporal_comparisons.changes.at_risk_change >= 0 ? '+' : ''}
              {trendsData.temporal_comparisons.changes.at_risk_change}
            </div>
          </div>
        </div>
      </div>
    {/if}

    <!-- Segment Distribution Chart -->
    {#if segmentChartConfig}
      <div class="chart-section">
        <h3 class="section-title">Distribución por Segmento</h3>
        <div class="chart-container">
          <ChartWrapper config={segmentChartConfig} />
        </div>
      </div>
    {/if}

    <!-- Segment Behavior Table -->
    <div class="segment-behavior-section">
      <h3 class="section-title">Comportamiento por Segmento</h3>
      <div class="segment-table-container">
        <table class="segment-table">
          <thead>
            <tr>
              <th>Segmento</th>
              <th>Clientes</th>
              <th>Porcentaje</th>
              <th>Tendencia</th>
            </tr>
          </thead>
          <tbody>
            {#each Object.entries(trendsData.segment_behavior) as [segment, data]}
              {@const TrendIcon = getTrendIcon(data.trend)}
              {@const trendColor = getTrendColor(data.trend)}
              <tr>
                <td class="segment-name">{segmentLabels[segment] || segment}</td>
                <td class="segment-count">{data.customer_count}</td>
                <td class="segment-percentage">{data.percentage}%</td>
                <td class="segment-trend">
                  <div class="trend-indicator">
                    <TrendIcon size={16} style="color: {trendColor}" />
                    <span style="color: {trendColor}">{data.trend}</span>
                  </div>
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    </div>

    <!-- Churn Indicators Detail -->
    <div class="churn-detail-section">
      <h3 class="section-title">Indicadores de Churn</h3>
      <div class="churn-grid">
        <div class="churn-card" class:severity-high={getChurnSeverity(trendsData.churn_indicators.churn_probability) === 'high'}>
          <div class="churn-label">En Riesgo</div>
          <div class="churn-value">{trendsData.churn_indicators.at_risk_count}</div>
        </div>
        <div class="churn-card">
          <div class="churn-label">Hibernando</div>
          <div class="churn-value">{trendsData.churn_indicators.hibernating_count}</div>
        </div>
        <div class="churn-card">
          <div class="churn-label">Perdidos</div>
          <div class="churn-value">{trendsData.churn_indicators.lost_count}</div>
        </div>
        <div class="churn-card">
          <div class="churn-label">No Podemos Perder</div>
          <div class="churn-value">{trendsData.churn_indicators.cannot_lose_count}</div>
        </div>
      </div>
    </div>
  {:else}
    <div class="empty-state">
      <p>No hay datos disponibles para el análisis de tendencias.</p>
    </div>
  {/if}
</div>

<style>
  .customers-trends-container {
    width: 100%;
  }

  .trends-summary-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: var(--spacing-md);
    margin-bottom: var(--spacing-lg);
  }

  .summary-card {
    padding: var(--spacing-lg);
    background: var(--theme-bg-card);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
    transition: all 0.2s ease;
  }

  .summary-card:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-md);
  }

  .summary-card.churn-high {
    border-color: var(--accent-danger);
    background: rgba(239, 68, 68, 0.05);
  }

  .summary-card.churn-medium {
    border-color: var(--accent-warning);
    background: rgba(251, 191, 36, 0.05);
  }

  .summary-header {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    margin-bottom: var(--spacing-md);
  }

  .summary-title {
    font-size: var(--text-sm);
    font-weight: 500;
    color: var(--text-secondary);
    margin: 0;
  }

  .summary-value {
    font-size: var(--text-2xl);
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: var(--spacing-xs);
  }

  .summary-change {
    font-size: var(--text-sm);
    color: var(--text-secondary);
  }

  .summary-change.positive {
    color: var(--accent-success);
  }

  .summary-subtitle {
    font-size: var(--text-xs);
    color: var(--text-secondary);
    margin-top: var(--spacing-xs);
  }

  .section-title {
    font-size: var(--text-lg);
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: var(--spacing-md);
  }

  .comparison-section {
    margin-bottom: var(--spacing-lg);
    padding: var(--spacing-lg);
    background: var(--theme-bg-elevated);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
  }

  .comparison-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: var(--spacing-md);
  }

  .comparison-card {
    padding: var(--spacing-md);
    background: var(--theme-bg-card);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
    text-align: center;
  }

  .comparison-label {
    font-size: var(--text-sm);
    color: var(--text-secondary);
    margin-bottom: var(--spacing-sm);
  }

  .comparison-value {
    font-size: var(--text-2xl);
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: var(--spacing-xs);
  }

  .comparison-value.positive {
    color: var(--accent-success);
  }

  .comparison-percentage {
    font-size: var(--text-sm);
    color: var(--text-secondary);
  }

  .chart-section {
    margin-bottom: var(--spacing-lg);
    padding: var(--spacing-lg);
    background: var(--theme-bg-elevated);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
  }

  .chart-container {
    height: 400px;
    position: relative;
  }

  .segment-behavior-section {
    margin-bottom: var(--spacing-lg);
  }

  .segment-table-container {
    overflow-x: auto;
    background: var(--theme-bg-card);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
  }

  .segment-table {
    width: 100%;
    border-collapse: collapse;
  }

  .segment-table thead {
    background: var(--theme-bg-elevated);
  }

  .segment-table th {
    padding: var(--spacing-md);
    text-align: left;
    font-size: var(--text-sm);
    font-weight: 600;
    color: var(--text-secondary);
    border-bottom: 2px solid var(--border-primary);
  }

  .segment-table td {
    padding: var(--spacing-md);
    border-bottom: 1px solid var(--border-primary);
    font-size: var(--text-sm);
    color: var(--text-primary);
  }

  .segment-table tbody tr:hover {
    background: var(--theme-bg-elevated);
  }

  .segment-name {
    font-weight: 500;
  }

  .segment-count {
    text-align: center;
    font-variant-numeric: tabular-nums;
  }

  .segment-percentage {
    text-align: center;
    font-variant-numeric: tabular-nums;
  }

  .trend-indicator {
    display: flex;
    align-items: center;
    gap: var(--spacing-xs);
  }

  .churn-detail-section {
    margin-bottom: var(--spacing-lg);
  }

  .churn-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: var(--spacing-md);
  }

  .churn-card {
    padding: var(--spacing-md);
    background: var(--theme-bg-card);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
    text-align: center;
  }

  .churn-card.severity-high {
    border-color: var(--accent-danger);
    background: rgba(239, 68, 68, 0.05);
  }

  .churn-label {
    font-size: var(--text-sm);
    color: var(--text-secondary);
    margin-bottom: var(--spacing-sm);
  }

  .churn-value {
    font-size: var(--text-2xl);
    font-weight: 600;
    color: var(--text-primary);
  }

  .empty-state {
    text-align: center;
    padding: var(--spacing-xl);
    color: var(--text-secondary);
  }

  @media (max-width: 768px) {
    .trends-summary-grid {
      grid-template-columns: 1fr;
    }

    .comparison-grid {
      grid-template-columns: 1fr;
    }

    .churn-grid {
      grid-template-columns: repeat(2, 1fr);
    }

    .chart-container {
      height: 300px;
    }
  }
</style>
