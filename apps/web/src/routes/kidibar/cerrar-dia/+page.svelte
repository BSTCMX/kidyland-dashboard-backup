<script lang="ts">
  /**
   * Day Close page - Close current day for KidiBar.
   * Reuses DayCloseForm component from recepcion.
   */
  import { onMount } from "svelte";
  import { goto } from "$app/navigation";
  import { user, hasAccessSecure } from "$lib/stores/auth";
  import { fetchDayStatus, dayOperationsStore } from "$lib/stores/day-operations";
  import { canExecuteDayOperations } from "$lib/utils/permissions";
  import DayCloseForm from "$lib/components/forms/DayCloseForm.svelte";

  onMount(() => {
    // Verify user has access to kidibar
    if (!$user || !hasAccessSecure("/kidibar")) {
      goto("/kidibar");
      return;
    }

    // Fetch day status
    if ($user?.sucursal_id) {
      fetchDayStatus($user.sucursal_id);
    }
  });

  $: canExecute = canExecuteDayOperations($user?.role);

  function handleSuccess() {
    // Redirect to kidibar dashboard after successful day close
    goto("/kidibar");
  }
</script>

<div class="day-close-page">
  <div class="page-header">
    <button class="back-button" on:click={() => goto("/kidibar/reportes")}>← Volver</button>
    <h1 class="page-title">Cerrar Día</h1>
  </div>

  {#if $dayOperationsStore.error}
    <div class="error-banner">{$dayOperationsStore.error}</div>
  {/if}

  <DayCloseForm
    sucursalId={$user?.sucursal_id || ""}
    readOnly={!canExecute}
    module="kidibar"
    on:success={handleSuccess}
  />
</div>

<style>
  .day-close-page {
    min-height: 100vh;
    background: var(--theme-bg-primary);
    padding: var(--spacing-lg);
  }

  .page-header {
    display: flex;
    align-items: center;
    gap: var(--spacing-md);
    margin-bottom: var(--spacing-xl);
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
    font-size: var(--text-3xl);
    font-weight: 700;
    color: var(--text-primary);
    margin: 0;
    
    /* Efecto 3D - solo sombreado, sin animaciones */
    text-shadow: 
      0 0.05em 0 rgba(0, 0, 0, 0.1),
      0 0.1em 0 rgba(0, 0, 0, 0.1),
      0 0.15em 0 rgba(0, 0, 0, 0.1),
      0 0.2em 0 rgba(0, 0, 0, 0.1),
      0 0.25em 0 rgba(0, 0, 0, 0.1),
      0 0.25em 0.02em rgba(0, 0, 0, 0.15),
      0 0.28em 0.2em rgba(0, 0, 0, 0.25);
  }

  .error-banner {
    padding: var(--spacing-md);
    background: rgba(211, 5, 84, 0.1);
    border: 1px solid rgba(211, 5, 84, 0.3);
    border-radius: var(--radius-md);
    color: #d30554;
    margin-bottom: var(--spacing-xl);
  }

  @media (max-width: 768px) {
    .day-close-page {
      padding: var(--spacing-md);
    }

    .page-header {
      flex-direction: column;
      align-items: stretch;
      gap: var(--spacing-sm);
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





