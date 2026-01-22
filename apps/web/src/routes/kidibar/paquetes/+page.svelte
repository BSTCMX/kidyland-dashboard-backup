<script lang="ts">
  /**
   * Packages section page for KidiBar.
   * 
   * Displays list of product packages available for sale in KidiBar.
   * Uses centralized permission system for role-based access control.
   */
  import { onMount } from "svelte";
  import { goto } from "$app/navigation";
  import { user, hasAccessSecure, canCreateSales } from "$lib/stores/auth";
  import PackageList from "$lib/components/admin/PackageList.svelte";
  import { Button } from "@kidyland/ui";
  import { ShoppingCart } from "lucide-svelte";

  $: canSell = canCreateSales($user?.role, "kidibar");

  function handleNewSale() {
    goto("/kidibar/paquetes/venta");
  }

  onMount(() => {
    if (!$user || !hasAccessSecure("/kidibar")) {
      goto("/kidibar");
      return;
    }
  });
</script>

<div class="packages-page">
  <div class="page-header">
    <div>
      <h1 class="page-title">Paquetes</h1>
      <p class="page-description">
        Paquetes de productos disponibles para venta en KidiBar.
      </p>
    </div>
    {#if canSell}
      <Button variant="brutalist" on:click={handleNewSale}>
        <ShoppingCart size={18} strokeWidth={1.5} style="display: inline-block; vertical-align: middle; margin-right: 6px;" />
        Nueva Venta
      </Button>
    {/if}
  </div>

  {#if $user}
    <PackageList module="kidibar" filterByType={true} hideCreateEdit={true} />
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
</style>
