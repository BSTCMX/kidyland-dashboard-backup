<script lang="ts">
  /**
   * ExecutiveSummaryHeader - Health Scorecard component.
   * 
   * Displays overall health score with breakdown by category.
   */
  import type { OverallHealth } from "$lib/stores/reports";
  import { TrendingUp, TrendingDown, Minus, Activity } from "lucide-svelte";

  export let health: OverallHealth;

  $: statusColors = {
    excellent: "var(--accent-success)",
    good: "var(--accent-primary)",
    warning: "#f59e0b",
    critical: "var(--accent-danger)"
  };

  $: statusLabels = {
    excellent: "Excelente",
    good: "Bueno",
    warning: "Advertencia",
    critical: "Crítico"
  };

  $: trendIcon = health.trend === "improving" ? TrendingUp :
                  health.trend === "declining" ? TrendingDown : Minus;

  $: trendColor = health.trend === "improving" ? "var(--accent-success)" :
                   health.trend === "declining" ? "var(--accent-danger)" :
                   "var(--text-secondary)";
</script>

<div class="health-header">
  <div class="health-main">
    <div class="health-score-card">
      <div class="score-circle" style="--score: {health.score}; --color: {statusColors[health.status]}">
        <div class="score-value">{health.score}</div>
        <div class="score-label">Health Score</div>
      </div>
      <div class="health-status">
        <Activity size={20} />
        <span class="status-text" style="color: {statusColors[health.status]}">
          {statusLabels[health.status]}
        </span>
        <svelte:component this={trendIcon} size={16} style="color: {trendColor}" />
      </div>
    </div>

    <div class="health-breakdown">
      <div class="breakdown-item">
        <div class="breakdown-label">Financiero</div>
        <div class="breakdown-bar">
          <div 
            class="breakdown-fill" 
            style="width: {health.breakdown.financial}%; background: var(--accent-primary);"
          ></div>
        </div>
        <div class="breakdown-value">{health.breakdown.financial}%</div>
      </div>

      <div class="breakdown-item">
        <div class="breakdown-label">Operacional</div>
        <div class="breakdown-bar">
          <div 
            class="breakdown-fill" 
            style="width: {health.breakdown.operational}%; background: var(--accent-info);"
          ></div>
        </div>
        <div class="breakdown-value">{health.breakdown.operational}%</div>
      </div>

      <div class="breakdown-item">
        <div class="breakdown-label">Inventario</div>
        <div class="breakdown-bar">
          <div 
            class="breakdown-fill" 
            style="width: {health.breakdown.inventory}%; background: var(--accent-warning);"
          ></div>
        </div>
        <div class="breakdown-value">{health.breakdown.inventory}%</div>
      </div>

      <div class="breakdown-item">
        <div class="breakdown-label">Efectivo</div>
        <div class="breakdown-bar">
          <div 
            class="breakdown-fill" 
            style="width: {health.breakdown.cash}%; background: var(--accent-success);"
          ></div>
        </div>
        <div class="breakdown-value">{health.breakdown.cash}%</div>
      </div>

      <div class="breakdown-item">
        <div class="breakdown-label">Clientes</div>
        <div class="breakdown-bar">
          <div 
            class="breakdown-fill" 
            style="width: {health.breakdown.customer}%; background: #8b5cf6;"
          ></div>
        </div>
        <div class="breakdown-value">{health.breakdown.customer}%</div>
      </div>
    </div>
  </div>
</div>

<style>
  .health-header {
    width: 100%;
    margin-bottom: var(--spacing-xl);
  }

  .health-main {
    display: grid;
    grid-template-columns: auto 1fr;
    gap: var(--spacing-xl);
    align-items: center;
    padding: var(--spacing-lg);
    background: var(--theme-bg-card);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-md);
  }

  .health-score-card {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: var(--spacing-md);
  }

  .score-circle {
    width: 120px;
    height: 120px;
    border-radius: 50%;
    background: conic-gradient(
      var(--color) 0deg,
      var(--color) calc(var(--score) * 3.6deg),
      var(--border-primary) calc(var(--score) * 3.6deg),
      var(--border-primary) 360deg
    );
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    position: relative;
  }

  .score-circle::before {
    content: '';
    position: absolute;
    width: 90px;
    height: 90px;
    border-radius: 50%;
    background: var(--theme-bg-card);
  }

  .score-value {
    position: relative;
    font-size: var(--text-3xl);
    font-weight: 700;
    color: var(--text-primary);
    z-index: 1;
  }

  .score-label {
    position: relative;
    font-size: var(--text-xs);
    color: var(--text-secondary);
    z-index: 1;
    text-align: center;
  }

  .health-status {
    display: flex;
    align-items: center;
    gap: var(--spacing-xs);
    font-size: var(--text-sm);
    font-weight: 600;
  }

  .status-text {
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .health-breakdown {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-md);
    flex: 1;
  }

  .breakdown-item {
    display: grid;
    grid-template-columns: 100px 1fr auto;
    gap: var(--spacing-md);
    align-items: center;
  }

  .breakdown-label {
    font-size: var(--text-sm);
    color: var(--text-secondary);
    font-weight: 500;
  }

  .breakdown-bar {
    height: 8px;
    background: var(--theme-bg-secondary);
    border-radius: var(--radius-full);
    overflow: hidden;
  }

  .breakdown-fill {
    height: 100%;
    border-radius: var(--radius-full);
    transition: width 0.3s ease;
  }

  .breakdown-value {
    font-size: var(--text-sm);
    font-weight: 600;
    color: var(--text-primary);
    min-width: 40px;
    text-align: right;
  }

  @media (max-width: 768px) {
    .health-main {
      grid-template-columns: 1fr;
      gap: var(--spacing-lg);
    }

    .health-score-card {
      width: 100%;
    }

    .breakdown-item {
      grid-template-columns: 80px 1fr auto;
      gap: var(--spacing-sm);
    }
  }
</style>


