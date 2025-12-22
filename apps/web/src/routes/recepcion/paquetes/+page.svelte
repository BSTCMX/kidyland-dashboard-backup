<script lang="ts">
  /**
   * Packages section page for reception.
   * 
   * Displays service packages available for sale.
   * Only shows packages that contain services (not products).
   * Uses PackageList component for consistent display with service names.
   */
  import { onMount } from "svelte";
  import { goto } from "$app/navigation";
  import { page } from "$app/stores";
  import { user, canEditSecure } from "$lib/stores/auth";
  import PackageList from "$lib/components/admin/PackageList.svelte";
  import PackageSalesHistoryBar from "$lib/components/shared/PackageSalesHistoryBar.svelte";
  import { Button } from "@kidyland/ui";
  import { ShoppingCart } from "lucide-svelte";

  $: canSell = canEditSecure("recepcion");
</script>

<div class="packages-page">
  <PackageSalesHistoryBar />
  
  <div class="page-header">
    <div>
      <h1 class="page-title">Paquetes</h1>
      <p class="page-description">
        Paquetes de servicios disponibles para venta.
      </p>
    </div>
    {#if canSell}
      <Button variant="brutalist" on:click={() => goto("/recepcion/paquetes/venta")}>
        <ShoppingCart size={18} strokeWidth={1.5} style="display: inline-block; vertical-align: middle; margin-right: 6px;" />
        Nueva Venta
      </Button>
    {/if}
  </div>

  {#if $user}
    <PackageList module="recepcion" filterByType={true} hideCreateEdit={true} />
  {/if}
</div>

<style>
  .packages-page {
    width: 100%;
  }

  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: var(--spacing-md);
    margin-bottom: var(--spacing-xl);
    flex-wrap: wrap;
  }

  .page-title {
    font-family: var(--font-primary);
    font-size: var(--text-3xl);
    font-weight: 700;
    color: var(--text-primary);
    margin: 0 0 var(--spacing-md) 0;
  }

  .page-description {
    font-size: var(--text-lg);
    color: var(--text-secondary);
    margin: 0;
  }

  @media (max-width: 768px) {
    .page-header {
      flex-direction: column;
      align-items: stretch;
      gap: var(--spacing-sm);
    }

    .page-title {
      font-size: var(--text-2xl);
      text-align: center;
    }

    .page-description {
      text-align: center;
    }

    /* Ensure Nueva Venta button is full width on mobile */
    .page-header :global(button) {
      width: 100%;
      min-height: 44px; /* Minimum touch target size for accessibility */
      justify-content: center;
    }
  }

  /* Prevent hover transform issues on touch devices */
  @media (hover: none) and (pointer: coarse) {
    .page-header :global(button:hover) {
      transform: none;
    }
  }
</style>

