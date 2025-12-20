<script lang="ts">
  /**
   * Day Close History page - View history of day closes for KidiBar.
   * Reuses DayCloseHistory component from recepcion.
   */
  import { onMount } from "svelte";
  import { goto } from "$app/navigation";
  import { page } from "$app/stores";
  import { user, hasAccessSecure } from "$lib/stores/auth";
  import DayCloseHistory from "$lib/components/shared/DayCloseHistory.svelte";

  onMount(() => {
    // Verify user has access to kidibar
    if (!$user || !hasAccessSecure("/kidibar")) {
      goto("/kidibar");
      return;
    }
  });

  // Get effective sucursal_id: prioritize query param, then user's sucursal_id
  // This allows super_admin to access arqueos history with a specific sucursal via query params
  $: effectiveSucursalId = $page.url.searchParams.get('sucursal_id') || $user?.sucursal_id || "";
</script>

<div class="arqueos-page">
  <div class="page-header">
    <button class="back-button" on:click={() => goto("/kidibar/reportes")}>← Volver</button>
    <h1 class="page-title">Historial de Arqueos</h1>
  </div>

  <DayCloseHistory sucursalId={effectiveSucursalId} />
</div>

<style>
  .arqueos-page {
    min-height: 100vh;
    background: var(--theme-bg-primary);
  }

  .page-header {
    display: flex;
    align-items: center;
    gap: var(--spacing-md);
    padding: var(--spacing-lg);
    background: var(--theme-bg-elevated);
    border-bottom: 1px solid var(--border-primary);
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
    font-size: var(--text-3xl);
    font-weight: 700;
    color: var(--text-primary);
    margin: 0;
  }

  @media (max-width: 768px) {
    .page-header {
      flex-direction: column;
      align-items: stretch;
      gap: var(--spacing-sm);
      padding: var(--spacing-md);
    }

    .page-title {
      font-size: var(--text-2xl);
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





