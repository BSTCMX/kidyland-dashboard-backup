<script lang="ts">
  /**
   * CustomersRFM - RFM (Recency, Frequency, Monetary) analysis component.
   */
  import { onMount } from 'svelte';
  import { get } from '@kidyland/utils/api';
  import { formatPrice } from '$lib/stores/reports';
  import LoadingSpinner from '$lib/components/admin/LoadingSpinner.svelte';
  import ErrorBanner from '$lib/components/admin/ErrorBanner.svelte';

  export let sucursalId: string | null = null;
  export let startDate: string | null = null;
  export let endDate: string | null = null;

  interface RFMCustomer {
    customer_name: string;
    module: 'recepcion' | 'kidibar';
    recency_days: number;
    frequency: number;
    monetary_cents: number;
    r_score: number;
    f_score: number;
    m_score: number;
    rfm_score: string;
  }

  interface RFMAnalysis {
    segments: {
      champions: RFMCustomer[];
      loyal_customers: RFMCustomer[];
      potential_loyalists: RFMCustomer[];
      new_customers: RFMCustomer[];
      promising: RFMCustomer[];
      need_attention: RFMCustomer[];
      about_to_sleep: RFMCustomer[];
      at_risk: RFMCustomer[];
      cannot_lose: RFMCustomer[];
      hibernating: RFMCustomer[];
      lost: RFMCustomer[];
    };
    summary: {
      total_customers: number;
      segment_counts: Record<string, number>;
    };
  }

  let loading = true;
  let error: string | null = null;
  let rfmData: RFMAnalysis | null = null;
  let expandedSegment: string | null = null;

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

  const segmentColors: Record<string, string> = {
    champions: 'var(--accent-success)',
    loyal_customers: 'var(--accent-primary)',
    potential_loyalists: 'var(--accent-warning)',
    new_customers: 'var(--accent-primary)',
    promising: 'var(--accent-warning)',
    need_attention: 'var(--accent-warning)',
    about_to_sleep: 'var(--accent-warning)',
    at_risk: 'var(--accent-danger)',
    cannot_lose: 'var(--accent-danger)',
    hibernating: 'var(--text-muted)',
    lost: 'var(--text-muted)'
  };

  async function fetchRFM() {
    loading = true;
    error = null;

    try {
      const params = new URLSearchParams();
      if (sucursalId) params.append('sucursal_id', sucursalId);
      if (startDate) params.append('start_date', startDate);
      if (endDate) params.append('end_date', endDate);

      rfmData = await get<RFMAnalysis>(`/reports/customers/rfm?${params.toString()}`);
    } catch (err: any) {
      error = err.message || 'Error al cargar análisis RFM';
    } finally {
      loading = false;
    }
  }

  function toggleSegment(segment: string) {
    expandedSegment = expandedSegment === segment ? null : segment;
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
      fetchRFM();
    }
  }

  onMount(() => {
    fetchRFM();
  });
</script>

<div class="customers-rfm-container">
  {#if loading}
    <LoadingSpinner />
  {:else if error}
    <ErrorBanner {error} />
  {:else if rfmData}
    <div class="rfm-header">
      <h3 class="rfm-title">Análisis RFM</h3>
      <div class="rfm-summary">
        <div class="summary-item">
          <span class="summary-label">Total Clientes:</span>
          <span class="summary-value">{rfmData.summary.total_customers}</span>
        </div>
      </div>
    </div>

    <div class="segments-grid">
      {#each Object.entries(rfmData.segments) as [segmentKey, customers]}
        {@const segmentCount = customers.length}
        {@const segmentLabel = segmentLabels[segmentKey] || segmentKey}
        {@const segmentColor = segmentColors[segmentKey] || 'var(--text-secondary)'}
        
        {#if segmentCount > 0}
          <div class="segment-card">
            <div 
              class="segment-header"
              style="border-left-color: {segmentColor};"
              on:click={() => toggleSegment(segmentKey)}
              role="button"
              tabindex="0"
              on:keydown={(e) => e.key === 'Enter' && toggleSegment(segmentKey)}
            >
              <div class="segment-info">
                <h4 class="segment-title">{segmentLabel}</h4>
                <span class="segment-count">{segmentCount} clientes</span>
              </div>
              <div class="segment-toggle">
                {expandedSegment === segmentKey ? '−' : '+'}
              </div>
            </div>
            
            {#if expandedSegment === segmentKey}
              <div class="segment-content">
                <div class="customers-list">
                  {#each customers.slice(0, 50) as customer}
                    <div class="customer-item">
                      <div class="customer-main">
                        <span class="customer-name">{customer.customer_name}</span>
                        <span class="module-badge" class:recepcion={customer.module === 'recepcion'} class:kidibar={customer.module === 'kidibar'}>
                          {customer.module === 'recepcion' ? 'Recepción' : 'KidiBar'}
                        </span>
                      </div>
                      <div class="customer-metrics">
                        <div class="metric">
                          <span class="metric-label">RFM:</span>
                          <span class="metric-value">{customer.rfm_score}</span>
                        </div>
                        <div class="metric">
                          <span class="metric-label">Recencia:</span>
                          <span class="metric-value">{customer.recency_days} días</span>
                        </div>
                        <div class="metric">
                          <span class="metric-label">Frecuencia:</span>
                          <span class="metric-value">{customer.frequency}</span>
                        </div>
                        <div class="metric">
                          <span class="metric-label">Monetario:</span>
                          <span class="metric-value">{formatPrice(customer.monetary_cents)}</span>
                        </div>
                      </div>
                    </div>
                  {/each}
                  {#if customers.length > 50}
                    <div class="more-customers">
                      Y {customers.length - 50} clientes más...
                    </div>
                  {/if}
                </div>
              </div>
            {/if}
          </div>
        {/if}
      {/each}
    </div>
  {:else}
    <div class="empty-state">
      <p>No hay datos disponibles para el análisis RFM.</p>
    </div>
  {/if}
</div>

<style>
  .customers-rfm-container {
    width: 100%;
  }

  .rfm-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--spacing-lg);
    padding: var(--spacing-md);
    background: var(--theme-bg-elevated);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
  }

  .rfm-title {
    font-size: var(--text-xl);
    font-weight: 600;
    color: var(--text-primary);
    margin: 0;
  }

  .rfm-summary {
    display: flex;
    gap: var(--spacing-lg);
  }

  .summary-item {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xs);
  }

  .summary-label {
    font-size: var(--text-sm);
    color: var(--text-secondary);
  }

  .summary-value {
    font-size: var(--text-lg);
    font-weight: 600;
    color: var(--text-primary);
  }

  .segments-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: var(--spacing-md);
  }

  .segment-card {
    background: var(--theme-bg-card);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
    overflow: hidden;
    transition: all 0.2s ease;
  }

  .segment-card:hover {
    box-shadow: var(--shadow-md);
    transform: translateY(-2px);
  }

  .segment-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: var(--spacing-md);
    background: var(--theme-bg-elevated);
    border-left: 4px solid;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .segment-header:hover {
    background: var(--theme-bg-card);
  }

  .segment-info {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xs);
  }

  .segment-title {
    font-size: var(--text-base);
    font-weight: 600;
    color: var(--text-primary);
    margin: 0;
  }

  .segment-count {
    font-size: var(--text-sm);
    color: var(--text-secondary);
  }

  .segment-toggle {
    font-size: var(--text-xl);
    font-weight: 600;
    color: var(--text-secondary);
    user-select: none;
  }

  .segment-content {
    padding: var(--spacing-md);
    border-top: 1px solid var(--border-primary);
  }

  .customers-list {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-sm);
    max-height: 400px;
    overflow-y: auto;
  }

  .customer-item {
    padding: var(--spacing-sm);
    background: var(--theme-bg-elevated);
    border-radius: var(--radius-sm);
    border: 1px solid var(--border-primary);
  }

  .customer-main {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--spacing-xs);
  }

  .customer-name {
    font-weight: 500;
    color: var(--text-primary);
  }

  .module-badge {
    display: inline-block;
    padding: var(--spacing-xs) var(--spacing-sm);
    border-radius: var(--radius-sm);
    font-size: var(--text-xs);
    font-weight: 500;
  }

  .module-badge.recepcion {
    background: var(--color-recepcion, rgba(0, 147, 247, 0.1));
    color: var(--color-recepcion-dark, var(--accent-primary));
  }

  .module-badge.kidibar {
    background: var(--color-kidibar, rgba(255, 206, 0, 0.1));
    color: var(--color-kidibar-dark, var(--accent-warning));
  }

  .customer-metrics {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: var(--spacing-xs);
    font-size: var(--text-xs);
  }

  .metric {
    display: flex;
    justify-content: space-between;
  }

  .metric-label {
    color: var(--text-secondary);
  }

  .metric-value {
    font-weight: 500;
    color: var(--text-primary);
  }

  .more-customers {
    text-align: center;
    padding: var(--spacing-sm);
    color: var(--text-secondary);
    font-size: var(--text-sm);
    font-style: italic;
  }

  .empty-state {
    text-align: center;
    padding: var(--spacing-xl);
    color: var(--text-secondary);
  }

  @media (max-width: 768px) {
    .segments-grid {
      grid-template-columns: 1fr;
    }

    .rfm-header {
      flex-direction: column;
      align-items: flex-start;
      gap: var(--spacing-md);
    }
  }
</style>



