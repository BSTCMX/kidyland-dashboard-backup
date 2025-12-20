<script lang="ts">
  /**
   * Ventas page - Sales history for KidiBar.
   * 
   * Shows unified history of product and package sales.
   */
  import { onMount } from "svelte";
  import { goto } from "$app/navigation";
  import { page } from "$app/stores";
  import { user, hasAccessSecure } from "$lib/stores/auth";
  import SalesHistory from "$lib/components/shared/SalesHistory.svelte";

  onMount(() => {
    if (!$user || !hasAccessSecure("/kidibar")) {
      goto("/kidibar");
    }
  });

  // Get effective sucursal_id: prioritize query param, then user's sucursal_id
  // This allows super_admin to access sales history with a specific sucursal via query params
  $: effectiveSucursalId = $page.url.searchParams.get('sucursal_id') || $user?.sucursal_id || undefined;
</script>

<div class="ventas-page">
  <div class="page-header">
    <button class="back-button" on:click={() => goto("/kidibar")}>← Volver</button>
    <h1 class="page-title">Historial de Ventas</h1>
  </div>

  <!-- Use SalesHistory with saleType="product_package" to show unified product and package sales -->
  <SalesHistory saleType="product_package" sucursalId={effectiveSucursalId} />
</div>

<style>
  .ventas-page {
    min-height: 100vh;
    background: var(--theme-bg-primary);
  }

  .page-header {
    display: flex;
    align-items: center;
    gap: var(--spacing-md);
    padding: var(--spacing-lg);
    border-bottom: 1px solid var(--border-primary);
    flex-wrap: wrap;
  }

  .back-button {
    min-width: 48px;
    min-height: 48px;
    padding: var(--spacing-sm) var(--spacing-md);
    background: var(--theme-bg-elevated);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
    color: var(--text-primary);
    cursor: pointer;
    font-size: var(--text-base);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }

  .back-button:hover {
    background: var(--theme-bg-secondary);
    transform: translateY(-2px);
    border-color: rgba(0, 147, 247, 0.5);
    box-shadow: 0 4px 12px rgba(0, 147, 247, 0.2);
  }

  .page-title {
    font-family: var(--font-primary);
    font-size: var(--text-2xl);
    font-weight: 700;
    color: var(--text-primary);
    margin: 0;
  }

  @media (max-width: 768px) {
    .page-header {
      flex-direction: column;
      align-items: stretch;
      gap: var(--spacing-sm);
    }

    .page-title {
      font-size: var(--text-xl);
      text-align: center;
    }

    .back-button {
      width: 100%;
      justify-content: center;
    }
  }

  /* Prevent hover transform issues on touch devices */
  @media (hover: none) and (pointer: coarse) {
    .back-button:hover {
      transform: none;
    }
  }
</style>
