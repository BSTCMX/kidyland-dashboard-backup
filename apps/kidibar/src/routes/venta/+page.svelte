<script lang="ts">
  /**
   * Venta page - Product sale form for kidibar.
   * 
   * Main page for creating new product sales.
   */
  import ProductSaleForm from "$lib/components/ProductSaleForm.svelte";
  import { goto } from "$app/navigation";
</script>

<div class="venta-page">
  <div class="page-header">
    <button class="back-button" on:click={() => goto("/")}>← Volver</button>
    <h1 class="page-title">Nueva Venta - Productos</h1>
  </div>

  <ProductSaleForm />
</div>

<style>
  .venta-page {
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
    transition: all 0.2s ease;
  }

  .back-button:hover {
    background: var(--theme-bg-secondary);
    transform: translateY(-1px);
  }

  .page-title {
    font-family: var(--font-primary);
    font-size: var(--text-3xl);
    font-weight: 700;
    color: var(--text-primary);
  }

  @media (max-width: 768px) {
    .venta-page {
      padding: var(--spacing-md);
    }

    .page-title {
      font-size: var(--text-2xl);
    }
  }
</style>





























