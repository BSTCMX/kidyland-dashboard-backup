<script lang="ts">
  /**
   * SucursalSelector component - Dropdown to select sucursal for filtering.
   * 
   * Used in admin dashboard to filter metrics by sucursal.
   * Only visible to super_admin.
   * 
   * Pattern: Reactive Statement with Guard Flag (Patrón #2) + Loading/Error States (Patrón #3)
   * - Always renders when user has permissions (avoids circular dependency)
   * - Uses reactive statement to fetch data when permissions available
   * - Handles loading/error/empty states for better UX
   */
  import { onMount, tick } from "svelte";
  import { user } from "$lib/stores/auth";
  import { fetchAllSucursales, sucursalesAdminStore } from "$lib/stores/sucursales-admin";
  import { canEdit } from "$lib/stores/auth";
  import LoadingSpinner from "./LoadingSpinner.svelte";
  import ErrorBanner from "./ErrorBanner.svelte";

  export let selectedSucursalId: string | null = null;
  export let onSelect: ((sucursalId: string | null) => void) | null = null;
  export let allowAll: boolean = true; // Default: true for backward compatibility
  export let persistToLocalStorage: boolean = true; // Default: true for backward compatibility

  $: canEditAdmin = canEdit("admin");
  $: currentUserSucursalId = $user?.sucursal_id;

  // Guard flag to prevent race conditions (Patrón #2)
  let sucursalesLoaded = false;

  // Reactive statement for fetching (Patrón #2) - executes when canEditAdmin becomes true
  $: if (canEditAdmin && !sucursalesLoaded) {
    fetchAllSucursales();
    sucursalesLoaded = true;
  }

  // Reset flag when permissions change
  $: if (!canEditAdmin) {
    sucursalesLoaded = false;
  }

  /**
   * Auto-select single sucursal when only one is available.
   * This function respects the parent's binding (won't override if selectedSucursalId already has a value).
   * Pattern: Reactive Statement with Guard (Patrón #3)
   * 
   * Reactive statement that executes when:
   * - Permissions are available (canEditAdmin)
   * - Sucursales are loaded (!loading)
   * - List has items (list.length > 0)
   * - No selection exists (!selectedSucursalId)
   * - Auto-selection is enabled (persistToLocalStorage === true)
   * 
   * When persistToLocalStorage=false, parent handles initialization (e.g., PanelAccessSelector)
   */
  $: if (canEditAdmin &&
         persistToLocalStorage &&
         !$sucursalesAdminStore.loading && 
         $sucursalesAdminStore.list.length > 0 && 
         !selectedSucursalId) {
    const activeSucursales = $sucursalesAdminStore.list.filter((s) => s.active);
    
    // Auto-select if exactly one active sucursal exists
    if (activeSucursales.length === 1) {
      selectedSucursalId = activeSucursales[0].id;
      onSelect?.(activeSucursales[0].id);
      
      // Persist to localStorage only if enabled
      if (persistToLocalStorage) {
        localStorage.setItem("admin_selected_sucursal_id", activeSucursales[0].id);
      }
    }
  }

  // Consolidated onMount: Load localStorage + set default sucursal
  // Priority: Parent binding > localStorage > currentUserSucursalId > auto-select single
  // When persistToLocalStorage=false, skip all initialization (parent handles it)
  onMount(async () => {
    if (!canEditAdmin) return;
    
    // When persistToLocalStorage=false, parent component handles initialization
    // (e.g., PanelAccessSelector wants manual selection, no auto-selection)
    if (!persistToLocalStorage) {
      return;
    }

    // Priority 1: Respect parent binding if already set (via bind:)
    if (selectedSucursalId) {
      return;
    }

    // Priority 2: Load from localStorage (only if persistToLocalStorage is enabled)
    if (persistToLocalStorage) {
      const saved = localStorage.getItem("admin_selected_sucursal_id");
      if (saved) {
        selectedSucursalId = saved;
        onSelect?.(selectedSucursalId);
        return;
      }
    }

    // Priority 3: Set default to current user's sucursal if available
    if (currentUserSucursalId) {
      selectedSucursalId = currentUserSucursalId;
      onSelect?.(selectedSucursalId);
      return;
    }

    // Priority 4: Wait for stores to update, then auto-select single sucursal if available
    await tick();
    // The reactive statement will handle auto-selection once stores are ready
  });

  function handleChange(event: Event) {
    const target = event.target as HTMLSelectElement;
    selectedSucursalId = target.value || null;
    onSelect?.(selectedSucursalId);
    
    // Save to localStorage for persistence (only if enabled)
    if (persistToLocalStorage) {
      if (selectedSucursalId) {
        localStorage.setItem("admin_selected_sucursal_id", selectedSucursalId);
      } else {
        localStorage.removeItem("admin_selected_sucursal_id");
      }
    }
  }
</script>

{#if canEditAdmin}
  <div class="sucursal-selector">
    <label for="sucursal-select" class="label">
      Filtrar por Sucursal
    </label>

    <!-- Error State (Patrón #3) -->
    <ErrorBanner error={$sucursalesAdminStore.error} />

    <!-- Loading State (Patrón #3) -->
    {#if $sucursalesAdminStore.loading}
      <div class="loading-state">
        <LoadingSpinner size="sm" message="Cargando sucursales..." />
      </div>
    <!-- Empty State (Patrón #3) -->
    {:else if $sucursalesAdminStore.list.length === 0}
      <div class="empty-state">
        <p class="empty-message">No hay sucursales disponibles</p>
      </div>
    <!-- Content State (Patrón #3) -->
    {:else}
      <select
        id="sucursal-select"
        class="select"
        value={selectedSucursalId || ""}
        on:change={handleChange}
        disabled={$sucursalesAdminStore.loading}
      >
        {#if allowAll}
          <option value="">Todas las sucursales</option>
        {:else}
          <option value="">Selecciona una sucursal</option>
        {/if}
        {#each $sucursalesAdminStore.list.filter((s) => s.active) as sucursal}
          <option value={sucursal.id}>{sucursal.name}</option>
        {/each}
      </select>
    {/if}
  </div>
{/if}

<style>
  .sucursal-selector {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xs);
    min-width: 200px;
  }

  .label {
    font-weight: 600;
    font-size: var(--text-sm);
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .select {
    width: 100%;
    min-height: 48px;
    padding: var(--spacing-sm) var(--spacing-md);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
    font-size: var(--text-base);
    background: var(--theme-bg-elevated);
    color: var(--text-primary);
    transition: border-color 0.2s ease;
    cursor: pointer;
  }

  .select:focus {
    outline: none;
    border-color: var(--accent-primary);
    box-shadow: 0 0 0 3px rgba(0, 147, 247, 0.1);
  }

  .select:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .loading-state {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 48px;
    padding: var(--spacing-sm);
  }

  .empty-state {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 48px;
    padding: var(--spacing-sm);
    border: 1px solid var(--border-secondary);
    border-radius: var(--radius-md);
    background: var(--theme-bg-secondary);
  }

  .empty-message {
    font-size: var(--text-sm);
    color: var(--text-secondary);
    margin: 0;
    text-align: center;
  }

  @media (max-width: 768px) {
    .sucursal-selector {
      min-width: 100%;
    }
  }
</style>


















