<script lang="ts">
  /**
   * ArqueosRecommendations - Actionable recommendations component.
   */
  import { onMount } from 'svelte';
  import { fetchArqueosRecommendations, type ArqueosRecommendationsReport } from '$lib/stores/reports';
  import LoadingSpinner from '$lib/components/admin/LoadingSpinner.svelte';
  import ErrorBanner from '$lib/components/admin/ErrorBanner.svelte';
  import { AlertCircle, CheckCircle, Info, Lightbulb } from 'lucide-svelte';

  export let sucursalId: string | null = null;
  export let selectedModule: "all" | "recepcion" | "kidibar" = "all";

  let recommendationsData: ArqueosRecommendationsReport | null = null;
  let loading = false;
  let error: string | null = null;

  let previousSucursalId: string | null = null;
  let previousModule: "all" | "recepcion" | "kidibar" = "all";

  async function loadRecommendationsData() {
    loading = true;
    error = null;

    try {
      const report = await fetchArqueosRecommendations(sucursalId, selectedModule);
      recommendationsData = report;
    } catch (err: any) {
      console.error('Error loading recommendations data:', err);
      error = err.message || 'Error al cargar recomendaciones';
    } finally {
      loading = false;
    }
  }

  $: {
    const paramsChanged = 
      sucursalId !== previousSucursalId ||
      selectedModule !== previousModule;

    if (paramsChanged) {
      previousSucursalId = sucursalId;
      previousModule = selectedModule;
      loadRecommendationsData();
    }
  }

  onMount(() => {
    loadRecommendationsData();
  });

  function getPriorityIcon(priority: string) {
    if (priority === "high") return AlertCircle;
    if (priority === "medium") return Info;
    if (priority === "low") return CheckCircle;
    return Lightbulb;
  }

  function getPriorityColor(priority: string): string {
    if (priority === "high") return "var(--accent-error, #EF4444)";
    if (priority === "medium") return "var(--accent-warning, #F59E0B)";
    if (priority === "low") return "var(--accent-success, #10B981)";
    return "var(--accent-primary, #0093F7)";
  }
</script>

<div class="arqueos-recommendations">
  {#if loading}
    <LoadingSpinner />
  {:else if error}
    <ErrorBanner {error} />
  {:else if recommendationsData}
    <div class="recommendations-container">
      <div class="recommendations-header">
        <h3 class="section-title">Recomendaciones</h3>
        {#if recommendationsData.summary}
          <p class="summary-text">{recommendationsData.summary}</p>
        {/if}
      </div>
      
      {#if recommendationsData.recommendations.length === 0}
        <div class="no-recommendations">
          <CheckCircle size={24} style="color: var(--accent-success, #10B981)" />
          <p>No hay recomendaciones en este momento. Los procesos están funcionando correctamente.</p>
        </div>
      {:else}
        <div class="recommendations-list">
          {#each recommendationsData.recommendations as rec (rec.title)}
            {@const PriorityIcon = getPriorityIcon(rec.priority)}
            <div class="recommendation-item" style="border-left-color: {getPriorityColor(rec.priority)}">
              <div class="recommendation-icon">
                <PriorityIcon size={24} style="color: {getPriorityColor(rec.priority)}" />
              </div>
              <div class="recommendation-content">
                <div class="recommendation-header">
                  <h4 class="recommendation-title">{rec.title}</h4>
                  <span class="recommendation-priority" style="background: {getPriorityColor(rec.priority)}20; color: {getPriorityColor(rec.priority)}">
                    {rec.priority === "high" ? "Alta" : rec.priority === "medium" ? "Media" : rec.priority === "low" ? "Baja" : "Info"}
                  </span>
                </div>
                <p class="recommendation-description">{rec.description}</p>
                <div class="recommendation-action">
                  <strong>Acción:</strong> {rec.action}
                </div>
                <div class="recommendation-impact">
                  <strong>Impacto:</strong> {rec.impact}
                </div>
              </div>
            </div>
          {/each}
        </div>
      {/if}
    </div>
  {:else}
    <div class="placeholder-content">
      <p>No hay datos de recomendaciones disponibles.</p>
    </div>
  {/if}
</div>

<style>
  .arqueos-recommendations {
    width: 100%;
  }

  .recommendations-container {
    background: var(--theme-bg-card);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-lg, 12px);
    padding: var(--spacing-lg, 1.5rem);
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  }

  .recommendations-header {
    margin-bottom: var(--spacing-lg, 1.25rem);
  }

  .section-title {
    font-size: var(--text-xl, 1.25rem);
    font-weight: 700;
    color: var(--text-primary);
    margin: 0 0 var(--spacing-sm, 0.75rem) 0;
  }

  .summary-text {
    font-size: var(--text-sm, 0.875rem);
    color: var(--text-secondary);
    margin: 0;
  }

  .no-recommendations {
    padding: var(--spacing-xl, 1.5rem);
    text-align: center;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: var(--spacing-md, 1rem);
    color: var(--text-secondary);
  }

  .recommendations-list {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-md, 1rem);
  }

  .recommendation-item {
    display: flex;
    gap: var(--spacing-md, 1rem);
    padding: var(--spacing-md, 1rem);
    background: var(--theme-bg-secondary);
    border: 1px solid var(--border-primary);
    border-left-width: 4px;
    border-radius: var(--radius-md, 8px);
  }

  .recommendation-icon {
    flex-shrink: 0;
  }

  .recommendation-content {
    flex: 1;
  }

  .recommendation-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--spacing-xs, 0.5rem);
    gap: var(--spacing-sm, 0.75rem);
  }

  .recommendation-title {
    font-size: var(--text-base, 1rem);
    font-weight: 600;
    color: var(--text-primary);
    margin: 0;
    flex: 1;
  }

  .recommendation-priority {
    font-size: var(--text-xs, 0.75rem);
    font-weight: 600;
    padding: var(--spacing-xs, 0.5rem) var(--spacing-sm, 0.75rem);
    border-radius: var(--radius-sm, 4px);
    text-transform: uppercase;
  }

  .recommendation-description {
    font-size: var(--text-sm, 0.875rem);
    color: var(--text-secondary);
    margin: var(--spacing-xs, 0.5rem) 0;
  }

  .recommendation-action,
  .recommendation-impact {
    font-size: var(--text-sm, 0.875rem);
    color: var(--text-primary);
    margin-top: var(--spacing-xs, 0.5rem);
  }

  .recommendation-action strong,
  .recommendation-impact strong {
    color: var(--text-primary);
    font-weight: 600;
  }

  .placeholder-content {
    padding: var(--spacing-2xl, 3rem);
    text-align: center;
    color: var(--text-secondary);
    font-style: italic;
  }
</style>



