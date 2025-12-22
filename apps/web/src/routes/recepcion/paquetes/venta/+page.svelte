<script lang="ts">
  /**
   * Venta page - Service package sale form for recepcion.
   * 
   * Main page for creating new service package sales with multi-selection.
   */
  import { onMount } from "svelte";
  import { goto } from "$app/navigation";
  import { user, hasAccessSecure, canEditSecure } from "$lib/stores/auth";
  import ServicePackageMultiSaleForm from "$lib/components/forms/ServicePackageMultiSaleForm.svelte";

  onMount(() => {
    // Verify user has access and can edit recepcion
    if (!$user || !hasAccessSecure("/recepcion") || !canEditSecure("recepcion")) {
      goto("/recepcion");
      return;
    }
  });
</script>

<div class="venta-page">
  <div class="page-header">
    <button class="back-button" on:click={() => goto("/recepcion/paquetes")}>← Volver</button>
    <h1 class="page-title">Nueva Venta - Paquetes de Servicios</h1>
  </div>

  <ServicePackageMultiSaleForm />
</div>

<style>
  .venta-page {
    min-height: 100vh;
    padding: var(--spacing-xl);
    background: var(--theme-bg-primary);
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
    font-size: var(--text-base);
    font-weight: 600;
    cursor: pointer;
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

  @media (max-width: 768px) {
    .venta-page {
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
      min-height: 44px; /* Minimum touch target size for accessibility */
    }
  }

  /* Prevent hover transform issues on touch devices */
  @media (hover: none) and (pointer: coarse) {
    .back-button:hover {
      transform: none;
    }
  }
</style>

