<script lang="ts">
  /**
   * PriorityInsightsPanel - Display top actionable insights.
   */
  import type { Insight } from "$lib/stores/reports";
  import { AlertCircle, TrendingUp, TrendingDown, AlertTriangle, Info, ChevronRight } from "lucide-svelte";
  import { goto } from "$app/navigation";

  export let insights: Insight[];

  function getInsightIcon(type: Insight["type"]) {
    switch (type) {
      case "opportunity":
        return TrendingUp;
      case "risk":
        return AlertCircle;
      case "alert":
        return AlertTriangle;
      case "trend":
        return TrendingDown;
      default:
        return Info;
    }
  }

  function getInsightColor(type: Insight["type"], priority: Insight["priority"]) {
    if (type === "opportunity") return "var(--accent-success)";
    if (type === "risk" || type === "alert") {
      return priority === "high" ? "var(--accent-danger)" : "#f59e0b";
    }
    return "var(--accent-info)";
  }

  function handleInsightClick(insight: Insight) {
    if (insight.linkToSection) {
      goto(`/admin/reports#${insight.linkToSection}`);
    }
  }

  $: priorityLabels = {
    high: "Alta",
    medium: "Media",
    low: "Baja"
  };

  $: typeLabels = {
    opportunity: "Oportunidad",
    risk: "Riesgo",
    alert: "Alerta",
    trend: "Tendencia"
  };
</script>

<div class="insights-panel">
  <h3 class="section-title">Insights Prioritarios</h3>
  
  {#if insights.length === 0}
    <div class="empty-state">
      <Info size={24} />
      <p>No hay insights disponibles en este momento.</p>
    </div>
  {:else}
    <div class="insights-list">
      {#each insights as insight (insight.title)}
        <div 
          class="insight-card {insight.priority} {insight.type}"
          class:actionable={insight.actionable}
          role={insight.actionable ? "button" : undefined}
          tabindex={insight.actionable ? 0 : undefined}
          on:click={() => insight.actionable && handleInsightClick(insight)}
          on:keydown={(e) => insight.actionable && e.key === "Enter" && handleInsightClick(insight)}
        >
          <div class="insight-icon" style="color: {getInsightColor(insight.type, insight.priority)}">
            <svelte:component this={getInsightIcon(insight.type)} size={20} />
          </div>
          
          <div class="insight-content">
            <div class="insight-header">
              <span class="insight-type-badge" style="background: {getInsightColor(insight.type, insight.priority)}">
                {typeLabels[insight.type]}
              </span>
              <span class="insight-priority">{priorityLabels[insight.priority]}</span>
            </div>
            
            <h4 class="insight-title">{insight.title}</h4>
            <p class="insight-description">{insight.description}</p>
            
            <div class="insight-footer">
              <span class="insight-impact">Impacto: {insight.impact}</span>
              {#if insight.actionable}
                <span class="insight-action">
                  Ver detalles
                  <ChevronRight size={14} />
                </span>
              {/if}
            </div>
          </div>
        </div>
      {/each}
    </div>
  {/if}
</div>

<style>
  .insights-panel {
    width: 100%;
    margin-bottom: var(--spacing-xl);
  }

  .section-title {
    font-size: var(--text-xl);
    font-weight: 700;
    color: var(--text-primary);
    margin: 0 0 var(--spacing-lg) 0;
  }

  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: var(--spacing-xl);
    text-align: center;
    color: var(--text-secondary);
    gap: var(--spacing-md);
  }

  .insights-list {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-md);
  }

  .insight-card {
    display: flex;
    gap: var(--spacing-md);
    padding: var(--spacing-lg);
    background: var(--theme-bg-card);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
    box-shadow: var(--shadow-sm);
    transition: all 0.2s ease;
  }

  .insight-card.actionable {
    cursor: pointer;
  }

  .insight-card.actionable:hover {
    transform: translateX(4px);
    box-shadow: var(--shadow-md);
    border-color: var(--accent-primary);
  }

  .insight-card.actionable:focus {
    outline: 2px solid var(--accent-primary);
    outline-offset: 2px;
  }

  .insight-card.high {
    border-left: 4px solid var(--accent-danger);
  }

  .insight-card.medium {
    border-left: 4px solid #f59e0b;
  }

  .insight-card.low {
    border-left: 4px solid var(--accent-info);
  }

  .insight-icon {
    flex-shrink: 0;
    margin-top: 2px;
  }

  .insight-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xs);
  }

  .insight-header {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    margin-bottom: var(--spacing-xs);
  }

  .insight-type-badge {
    font-size: var(--text-xs);
    font-weight: 600;
    color: white;
    padding: 2px 8px;
    border-radius: var(--radius-sm);
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .insight-priority {
    font-size: var(--text-xs);
    color: var(--text-secondary);
    font-weight: 500;
  }

  .insight-title {
    font-size: var(--text-base);
    font-weight: 600;
    color: var(--text-primary);
    margin: 0;
  }

  .insight-description {
    font-size: var(--text-sm);
    color: var(--text-secondary);
    margin: 0;
    line-height: 1.5;
  }

  .insight-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: var(--spacing-xs);
    padding-top: var(--spacing-sm);
    border-top: 1px solid var(--border-primary);
  }

  .insight-impact {
    font-size: var(--text-xs);
    color: var(--text-secondary);
    font-weight: 500;
  }

  .insight-action {
    display: flex;
    align-items: center;
    gap: var(--spacing-xs);
    font-size: var(--text-xs);
    color: var(--accent-primary);
    font-weight: 600;
  }

  @media (max-width: 640px) {
    .insight-card {
      flex-direction: column;
      gap: var(--spacing-sm);
    }

    .insight-footer {
      flex-direction: column;
      align-items: flex-start;
      gap: var(--spacing-xs);
    }
  }
</style>


