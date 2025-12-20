<script lang="ts">
  /**
   * Products section page for KidiBar.
   * 
   * Provides access to product-related functionality:
   * - Nueva Venta (New Sale)
   */
  import { user, hasAccess } from "$lib/stores/auth";
  import { getModulePermissions } from "$lib/utils/permissions";
  import { ShoppingBag } from "lucide-svelte";
</script>

<div class="products-page">
  <div class="page-header">
    <div>
      <h1 class="page-title">Productos</h1>
      <p class="page-description">
        Productos disponibles para venta en KidiBar.
      </p>
    </div>
  </div>

  {#if $user}
    {@const kidibarPerms = getModulePermissions($user.role, "kidibar")}
    
    <div class="products-grid">
      {#if kidibarPerms?.canCreate}
        <a href="/kidibar/venta" class="product-card primary">
          <div class="card-icon">
            <ShoppingBag size={32} strokeWidth={1.5} />
          </div>
          <h3>Nueva Venta</h3>
          <p>Registrar venta de productos</p>
          <span class="card-link">Crear Venta →</span>
        </a>
      {/if}
    </div>
  {/if}
</div>

<style>
  .products-page {
    width: 100%;
  }

  .page-header {
    margin-bottom: var(--spacing-xl);
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

  .products-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: var(--spacing-xl);
  }

  .product-card {
    padding: var(--spacing-xl);
    background: var(--theme-bg-card);
    backdrop-filter: blur(16px) saturate(150%);
    -webkit-backdrop-filter: blur(16px) saturate(150%);
    border: 1px solid var(--border-primary);
    border-radius: 16px;
    box-shadow: 
      0 8px 24px rgba(0, 0, 0, 0.15),
      0 0 20px var(--glow-primary),
      inset 0 1px 0 rgba(255, 255, 255, 0.05);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    min-height: 200px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    text-decoration: none;
    color: inherit;
  }

  .product-card.primary {
    border-color: var(--accent-primary);
    background: linear-gradient(135deg, var(--theme-bg-card) 0%, rgba(0, 147, 247, 0.1) 100%);
  }

  .product-card:hover {
    transform: translateY(-4px);
    border-color: rgba(0, 147, 247, 0.5);
    box-shadow: 
      0 12px 32px rgba(0, 0, 0, 0.2),
      0 0 30px var(--glow-primary),
      0 0 40px var(--glow-secondary),
      inset 0 1px 0 rgba(255, 255, 255, 0.1);
  }

  .card-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 64px;
    height: 64px;
    background: rgba(0, 147, 247, 0.1);
    border-radius: var(--radius-lg);
    color: var(--accent-primary);
    margin-bottom: var(--spacing-md);
  }

  .product-card h3 {
    font-size: var(--text-xl);
    font-weight: 700;
    margin: 0 0 var(--spacing-sm) 0;
    color: var(--text-primary);
  }

  .product-card p {
    color: var(--text-secondary);
    margin: 0 0 var(--spacing-lg) 0;
    flex: 1;
  }

  .card-link {
    color: var(--accent-primary);
    font-weight: 600;
    text-decoration: none;
    transition: color 0.2s ease;
    display: inline-block;
  }

  .product-card:hover .card-link {
    color: var(--accent-primary-hover);
  }

  @media (max-width: 768px) {
    .products-grid {
      grid-template-columns: 1fr;
    }
  }

  /* Prevent hover transform issues on touch devices */
  @media (hover: none) and (pointer: coarse) {
    .product-card:hover {
      transform: none;
    }
  }
</style>
