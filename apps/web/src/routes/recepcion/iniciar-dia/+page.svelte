<script lang="ts">
  /**
   * Day Start page - Start a new day for recepcion.
   */
  import { onMount } from "svelte";
  import { goto } from "$app/navigation";
  import { user, hasAccessSecure } from "$lib/stores/auth";
  import { fetchDayStatus, dayOperationsStore } from "$lib/stores/day-operations";
  import DayStartForm from "$lib/components/forms/DayStartForm.svelte";

  onMount(() => {
    // Verify user has access to recepcion
    if (!$user || !hasAccessSecure("/recepcion")) {
      goto("/recepcion");
      return;
    }

    // Fetch day status
    if ($user?.sucursal_id) {
      fetchDayStatus($user.sucursal_id);
    }
  });

  function handleSuccess() {
    // Redirect to recepcion dashboard after successful day start
    goto("/recepcion");
  }
</script>

<div class="day-start-page">
  <div class="page-header">
    <button class="back-button" on:click={() => goto("/recepcion")}>← Volver</button>
    <h1 class="page-title">Iniciar Día</h1>
  </div>

  {#if $dayOperationsStore.error}
    <div class="error-banner">{$dayOperationsStore.error}</div>
  {/if}

  <DayStartForm
    sucursalId={$user?.sucursal_id || ""}
    on:success={handleSuccess}
  />
</div>

<style>
  .day-start-page {
    min-height: 100vh;
    background: var(--theme-bg-primary);
    padding: var(--spacing-lg);
  }

  .page-header {
    display: flex;
    align-items: center;
    gap: var(--spacing-md);
    margin-bottom: var(--spacing-xl);
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
    display: flex;
    align-items: center;
    justify-content: center;
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

  .error-banner {
    padding: var(--spacing-md);
    background: rgba(211, 5, 84, 0.1);
    border: 1px solid var(--accent-danger);
    border-radius: var(--radius-md);
    color: var(--accent-danger);
    margin-bottom: var(--spacing-lg);
  }

  @media (max-width: 768px) {
    .day-start-page {
      padding: var(--spacing-md);
    }

    .page-header {
      flex-direction: column;
      align-items: stretch;
      gap: var(--spacing-sm);
    }

    .back-button {
      width: 100%;
      justify-content: center;
      min-height: 44px;
    }
  }

  /* Prevent hover transform issues on touch devices */
  @media (hover: none) and (pointer: coarse) {
    .back-button:hover {
      transform: none;
    }
  }
</style>




















