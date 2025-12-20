<script lang="ts">
  /**
   * CustomersSection - Main container for customer reports with submenu navigation.
   */
  import CustomersSubTabs from './CustomersSubTabs.svelte';
  import CustomersList from './CustomersList.svelte';
  import CustomersSummary from './CustomersSummary.svelte';
  import CustomersRFM from './CustomersRFM.svelte';
  import CustomersCohorts from './CustomersCohorts.svelte';
  import CustomersTrends from './CustomersTrends.svelte';
  
  export let sucursalId: string | null = null;
  export let startDate: string | null = null;
  export let endDate: string | null = null;

  type SubTabId = 'summary' | 'list' | 'rfm' | 'cohorts' | 'trends';
  let activeSubTab: SubTabId = 'summary';

  function handleSubTabChange(tabId: string) {
    activeSubTab = tabId as SubTabId;
  }
</script>

<div class="customers-section">
  <CustomersSubTabs {activeSubTab} onSubTabChange={handleSubTabChange} />

  {#if activeSubTab === 'summary'}
    <CustomersSummary {sucursalId} {startDate} {endDate} />
  {:else if activeSubTab === 'list'}
    <CustomersList {sucursalId} {startDate} {endDate} />
  {:else if activeSubTab === 'rfm'}
    <CustomersRFM {sucursalId} {startDate} {endDate} />
  {:else if activeSubTab === 'cohorts'}
    <CustomersCohorts {sucursalId} {startDate} {endDate} />
  {:else if activeSubTab === 'trends'}
    <CustomersTrends {sucursalId} {startDate} {endDate} />
  {/if}
</div>

<style>
  .customers-section {
    width: 100%;
  }

  .sub-tab-content {
    padding: var(--spacing-xl);
    text-align: center;
    background: var(--theme-bg-card);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
    margin-top: var(--spacing-md);
  }

  .sub-tab-title {
    font-size: var(--text-xl);
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: var(--spacing-md);
  }

  .coming-soon {
    color: var(--text-secondary);
    font-size: var(--text-base);
  }
</style>

