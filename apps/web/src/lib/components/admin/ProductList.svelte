<script lang="ts">
  /**
   * ProductList component - Displays products in a table with CRUD operations.
   * 
   * @param module - Module context: "admin" (default) or "kidibar"
   * @param filterByType - If true, filter products by type (only for kidibar module)
   */
  import { onMount } from "svelte";
  import { Button } from "@kidyland/ui";
  import type { Product } from "@kidyland/shared/types";
  import {
    productsAdminStore,
    fetchAllProducts,
    createProduct,
    updateProduct,
    deleteProduct,
  } from "$lib/stores/products-admin";
  import { canEdit, hasRole } from "$lib/stores/auth";
  import { user } from "$lib/stores/auth";
  import { getModulePermissions } from "$lib/utils/permissions";
  import ProductForm from "./ProductForm.svelte";
  import LoadingSpinner from "./LoadingSpinner.svelte";
  import ErrorBanner from "./ErrorBanner.svelte";
  import { 
    ShoppingBag, 
    Plus, 
    Edit, 
    Trash2 
  } from "lucide-svelte";
  import Badge from "$lib/components/shared/Badge.svelte";

  // Props
  export let module: "admin" | "kidibar" = "admin";
  export let hideCreateEdit: boolean = false;

  // Reactive stores
  $: currentUser = $user;
  $: modulePerms = currentUser ? getModulePermissions(currentUser.role, module) : null;
  $: canViewProducts = modulePerms?.canAccess ?? false;
  $: canEditProducts = modulePerms?.canEdit ?? false;
  $: showCreateEditButtons = canEditProducts && !hideCreateEdit;
  
  // Products endpoint already returns only products (not services), so no filtering needed
  $: displayedProducts = $productsAdminStore.list;

  // Local state
  let selectedProduct: Product | null = null;
  let showCreateModal = false;
  let showEditModal = false;
  let showDeleteConfirm = false;

  // Load products on mount
  // Logic: super_admin and admin_viewer see all products (no filter), other users see filtered by sucursal_id
  onMount(() => {
    if (canViewProducts) {
      const filterSucursalId = currentUser?.sucursal_id || undefined;
      fetchAllProducts(filterSucursalId);
    }
  });

  function formatPrice(cents: number): string {
    return `$${(cents / 100).toFixed(2)}`;
  }

  async function handleDelete() {
    if (selectedProduct && canEditProducts) {
      const success = await deleteProduct(selectedProduct.id);
      if (success) {
        showDeleteConfirm = false;
        selectedProduct = null;
        // Refresh list using the same logic as onMount
        const filterSucursalId = currentUser?.sucursal_id || undefined;
        fetchAllProducts(filterSucursalId);
      }
    }
  }

  function handleCreateSuccess() {
    showCreateModal = false;
    // Refresh list using the same logic as onMount
    const filterSucursalId = currentUser?.sucursal_id || undefined;
    fetchAllProducts(filterSucursalId);
  }

  function handleUpdateSuccess() {
    showEditModal = false;
    selectedProduct = null;
    // Refresh list using the same logic as onMount
    const filterSucursalId = currentUser?.sucursal_id || undefined;
    fetchAllProducts(filterSucursalId);
  }
</script>

<div class="products-container">
  <!-- Main Content: Products Management -->
  <div class="products-main">
    <!-- Header with create button -->
    <div class="products-header">
      <h1 class="page-title">
        <ShoppingBag size={32} strokeWidth={1.5} style="display: inline-block; vertical-align: middle; margin-right: 12px;" />
        Gestión de Productos
      </h1>
      
      {#if showCreateEditButtons}
        <div class="create-product-button-wrapper">
          <Button 
            variant="brutalist"
            on:click={() => (showCreateModal = true)}
          >
            <Plus size={18} strokeWidth={1.5} style="display: inline-block; vertical-align: middle; margin-right: 6px;" />
            Crear Producto
          </Button>
        </div>
      {/if}
    </div>

    <!-- Error banner -->
    <ErrorBanner error={$productsAdminStore.error} />

    <!-- Loading state -->
    {#if $productsAdminStore.loading}
      <LoadingSpinner message="Cargando productos..." />
    {:else if displayedProducts.length === 0 && canViewProducts}
      <div class="empty-state">
        <p>No hay productos registrados</p>
        {#if showCreateEditButtons}
          <Button variant="brutalist" on:click={() => (showCreateModal = true)}>
            <Plus size={18} strokeWidth={1.5} style="display: inline-block; vertical-align: middle; margin-right: 6px;" />
            Crear Primer Producto
          </Button>
        {/if}
      </div>
    {:else if !canViewProducts}
      <div class="empty-state">
        <p>No tienes permisos para ver productos.</p>
      </div>
    {:else}
      <!-- Products Grid (Future-Proof CSS Grid Pattern #1) -->
      <!-- Desktop: Grid layout, Mobile: Cards layout -->
      <div class="products-grid-container">
        <!-- Desktop Grid Headers (hidden on mobile) -->
        <div class="grid-headers" class:readonly={!showCreateEditButtons}>
          <div class="grid-header">Nombre</div>
          <div class="grid-header">Precio</div>
          <div class="grid-header">Stock</div>
          <div class="grid-header">Umbral Alerta</div>
          <div class="grid-header">Para Paquete</div>
          <div class="grid-header">Estado</div>
          {#if showCreateEditButtons}
            <div class="grid-header">Acciones</div>
          {/if}
        </div>

        <!-- Products Grid Items -->
        <div class="products-grid" class:readonly={!showCreateEditButtons}>
          {#each displayedProducts as product (product.id)}
            <div class="product-grid-item">
              <!-- Nombre -->
              <div class="grid-cell name-cell">
                {product.name}
              </div>
              
              <!-- Precio -->
              <div class="grid-cell price-cell">
                {formatPrice(product.price_cents)}
              </div>
              
              <!-- Stock -->
              <div class="grid-cell stock-cell" class:low-stock={product.stock_qty <= product.threshold_alert_qty}>
                {product.stock_qty}
              </div>
              
              <!-- Umbral Alerta -->
              <div class="grid-cell threshold-cell">
                {product.threshold_alert_qty}
              </div>
              
              <!-- Para Paquete -->
              <div class="grid-cell package-cell">
                {product.enabled_for_package ? "✅ Sí" : "❌ No"}
              </div>
              
              <!-- Estado -->
              <div class="grid-cell status-cell">
                <Badge variant={product.active !== false ? "success" : "danger"} size="sm">
                  {product.active !== false ? "Activo" : "Inactivo"}
                </Badge>
              </div>
              
              <!-- Acciones -->
              {#if showCreateEditButtons}
                <div class="grid-cell actions-cell">
                  <div class="actions-group">
                    <Button
                      variant="brutalist"
                      on:click={() => {
                        selectedProduct = product;
                        showEditModal = true;
                      }}
                    >
                      <Edit size={16} strokeWidth={1.5} style="display: inline-block; vertical-align: middle; margin-right: 4px;" />
                      Editar
                    </Button>
                    <Button
                      variant="brutalist-danger"
                      on:click={() => {
                        selectedProduct = product;
                        showDeleteConfirm = true;
                      }}
                    >
                      <Trash2 size={16} strokeWidth={1.5} style="display: inline-block; vertical-align: middle; margin-right: 4px;" />
                      Eliminar
                    </Button>
                  </div>
                </div>
              {/if}
            </div>
          {/each}
        </div>
      </div>

      <!-- Products cards (Mobile - Enhanced) -->
      <div class="products-cards">
        {#each displayedProducts as product (product.id)}
          <div class="product-card">
            <div class="product-card-header">
              <h3 class="product-card-title">{product.name}</h3>
              <Badge variant={product.active !== false ? "success" : "danger"} size="sm">
                {product.active !== false ? "Activo" : "Inactivo"}
              </Badge>
            </div>
            <div class="product-card-body">
              <div class="product-card-row">
                <span class="product-card-label">Precio:</span>
                <span class="product-card-value">{formatPrice(product.price_cents)}</span>
              </div>
              <div class="product-card-row">
                <span class="product-card-label">Stock:</span>
                <span class="product-card-value" class:low-stock={product.stock_qty <= product.threshold_alert_qty}>
                  {product.stock_qty}
                </span>
              </div>
              <div class="product-card-row">
                <span class="product-card-label">Umbral Alerta:</span>
                <span class="product-card-value">{product.threshold_alert_qty}</span>
              </div>
              <div class="product-card-row">
                <span class="product-card-label">Para Paquete:</span>
                <span class="product-card-value">
                  {product.enabled_for_package ? "✅ Sí" : "❌ No"}
                </span>
              </div>
            </div>
            {#if showCreateEditButtons}
              <div class="product-card-actions">
                <Button
                  variant="brutalist"
                  on:click={() => {
                    selectedProduct = product;
                    showEditModal = true;
                  }}
                >
                  <Edit size={16} strokeWidth={1.5} style="display: inline-block; vertical-align: middle; margin-right: 4px;" />
                  Editar
                </Button>
                <Button
                  variant="brutalist-danger"
                  on:click={() => {
                    selectedProduct = product;
                    showDeleteConfirm = true;
                  }}
                >
                  <Trash2 size={16} strokeWidth={1.5} style="display: inline-block; vertical-align: middle; margin-right: 4px;" />
                  Eliminar
                </Button>
              </div>
            {/if}
          </div>
        {/each}
      </div>
    {/if}
  </div>
</div>

<!-- Create Modal -->
{#if showCreateModal && showCreateEditButtons}
  <ProductForm
    open={showCreateModal}
    product={null}
    sucursalId={currentUser?.sucursal_id || ""}
    on:close={() => (showCreateModal = false)}
    on:success={handleCreateSuccess}
  />
{/if}

<!-- Edit Modal -->
{#if showEditModal && selectedProduct && showCreateEditButtons}
  <ProductForm
    open={showEditModal}
    product={selectedProduct}
    sucursalId={currentUser?.sucursal_id || ""}
    on:close={() => {
      showEditModal = false;
      selectedProduct = null;
    }}
    on:success={handleUpdateSuccess}
  />
{/if}

<!-- Delete Confirm -->
{#if showDeleteConfirm && selectedProduct}
  <div 
    class="modal-overlay" 
    on:click={() => (showDeleteConfirm = false)}
    on:keydown={(e) => e.key === "Escape" && (showDeleteConfirm = false)}
    role="button"
    tabindex="0"
    aria-label="Cerrar modal"
  >
    <div 
      class="modal-content" 
      on:click|stopPropagation
      role="dialog"
      aria-modal="true"
      aria-labelledby="delete-modal-title"
    >
      <h2 id="delete-modal-title" class="modal-title">Confirmar Eliminación</h2>
      <p class="modal-message">
        ¿Estás seguro de que deseas eliminar el producto <strong>{selectedProduct.name}</strong>?
      </p>
      <p class="modal-warning">
        ⚠️ Esta acción desactivará el producto (soft delete). No se eliminará permanentemente.
      </p>
      <div class="form-footer">
        <button 
          type="button" 
          class="btn btn-secondary" 
          on:click={() => (showDeleteConfirm = false)}
        >
          Cancelar
        </button>
        <button 
          type="button" 
          class="btn btn-danger" 
          on:click={handleDelete}
        >
          Eliminar
        </button>
      </div>
    </div>
  </div>
{/if}

<style>
  .products-container {
    padding: var(--spacing-xl);
    max-width: 1600px;
    margin: 0 auto;
    background: var(--theme-bg-primary);
    min-height: 100vh;
    width: 100%;
    max-width: 100vw;
    box-sizing: border-box;
    overflow-x: hidden;
  }

  .products-main {
    width: 100%;
    min-width: 0;
  }

  .products-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--spacing-xl);
    flex-wrap: wrap;
    gap: var(--spacing-md);
  }

  @media (max-width: 768px) {
    .products-header {
      flex-direction: column;
      align-items: stretch;
      gap: var(--spacing-md);
    }

    .page-title {
      font-size: var(--text-2xl);
      text-align: center;
    }

    .create-product-button-wrapper {
      width: 100%;
    }

    .create-product-button-wrapper :global(button) {
      width: 100%;
      min-height: 44px; /* Minimum touch target size for accessibility */
      justify-content: center;
    }

    .empty-state :global(button) {
      width: 100%;
      min-height: 44px; /* Minimum touch target size for accessibility */
      justify-content: center;
    }

    .product-card-actions {
      flex-direction: column;
      gap: var(--spacing-sm);
      flex-wrap: nowrap;
    }

    .product-card-actions :global(button) {
      width: 100%;
      min-height: 44px; /* Minimum touch target size for accessibility */
      justify-content: center;
    }

    .actions-group {
      flex-direction: column;
      width: 100%;
      gap: var(--spacing-sm);
      flex-wrap: nowrap;
    }

    .actions-group :global(button) {
      width: 100%;
      min-height: 44px; /* Minimum touch target size for accessibility */
      justify-content: center;
    }
  }

  /* Prevent hover transform issues on touch devices */
  @media (hover: none) and (pointer: coarse) {
    .create-product-button-wrapper :global(.btn-brutalist:hover),
    .empty-state :global(.btn-brutalist:hover),
    .product-card-actions :global(.btn-brutalist:hover),
    .product-card-actions :global(.btn-brutalist-danger:hover),
    .actions-group :global(.btn-brutalist:hover),
    .actions-group :global(.btn-brutalist-danger:hover) {
      transform: none;
    }

    .create-product-button-wrapper :global(.btn-brutalist:hover),
    .empty-state :global(.btn-brutalist:hover),
    .actions-group :global(.btn-brutalist:hover) {
      box-shadow: 3px 3px 0px 0px var(--accent-primary);
      border-width: 2px;
    }

    .product-card-actions :global(.btn-brutalist-danger:hover),
    .actions-group :global(.btn-brutalist-danger:hover) {
      box-shadow: 3px 3px 0px 0px var(--accent-danger);
      border-width: 2px;
    }

    .product-card:hover {
      transform: none;
    }
  }

  .page-title {
    font-family: var(--font-primary);
    font-size: var(--text-3xl);
    font-weight: 700;
    color: var(--text-primary);
    
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

  .empty-state {
    text-align: center;
    padding: var(--spacing-2xl);
    color: var(--text-muted);
  }

  /* FUTURE-PROOF CSS GRID PATTERN #1 - Zero alignment issues */
  .products-grid-container {
    width: 100%;
    margin-bottom: var(--spacing-lg);
    background: var(--theme-bg-elevated);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-xl);
    box-shadow: var(--shadow-md);
    backdrop-filter: blur(10px);
    position: relative;
    overflow: hidden;
  }

  /* Gradient top border - Kidyland branding */
  .products-grid-container::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: linear-gradient(90deg, var(--accent-primary), var(--accent-success), var(--accent-warning));
    opacity: 0.6;
    z-index: 1;
  }

  /* Grid Headers - Desktop only */
  .grid-headers {
    display: none; /* Hidden on mobile */
  }

  /* Products Grid - Future-proof auto-responsive */
  /* Mobile: single column (will be hidden, cards shown instead) */
  .products-grid {
    display: grid;
    grid-template-columns: 1fr; /* Mobile: single column */
    gap: 0;
    width: 100%;
  }

  /* Desktop: Fixed 7-column grid for table-like layout (6 columns + 1 for actions if canEdit) */
  @media (min-width: 769px) {
    .products-grid {
      grid-template-columns: 1.5fr 1fr 0.9fr 0.9fr 1fr 0.9fr 2fr !important;
      gap: 0 !important;
    }
    
    /* Readonly modifier: 6 columns when canEditProducts=false (no Acciones column) */
    .products-grid.readonly {
      grid-template-columns: 1.5fr 1fr 0.9fr 0.9fr 1fr 0.9fr !important; /* 6 columns without Acciones */
    }
  }

  /* Product Grid Item - CRITICAL: display: contents makes container transparent */
  /* On mobile, we need to override to show cards */
  .product-grid-item {
    display: contents; /* Default: transparent container for table-like layout */
  }

  /* Mobile: Override display: contents to show cards */
  @media (max-width: 768px) {
    .product-grid-item {
      display: block; /* Show as block for card layout on mobile */
      padding: var(--spacing-md);
      border-bottom: 1px solid var(--border-primary);
      background: var(--theme-bg-elevated);
      border-radius: var(--radius-lg);
      margin-bottom: var(--spacing-sm);
    }

    .product-grid-item:last-child {
      border-bottom: none;
      margin-bottom: 0;
    }

    .grid-cell {
      border-right: none;
      border-bottom: 1px solid var(--border-primary);
      padding: var(--spacing-sm) 0;
      display: block; /* Stack vertically on mobile */
    }

    .grid-cell:last-child {
      border-bottom: none;
    }
  }

  /* Grid Cell - Individual data cell */
  .grid-cell {
    padding: var(--spacing-md) var(--spacing-sm);
    display: flex;
    align-items: center;
    font-size: var(--text-sm);
    color: var(--text-primary);
    word-wrap: break-word;
    overflow-wrap: break-word;
  }

  /* Desktop: Grid layout with proper column distribution - TABLE-LIKE */
  @media (min-width: 769px) {
    /* Show headers on desktop */
    .grid-headers {
      display: grid;
      grid-template-columns: 1.5fr 1fr 0.9fr 0.9fr 1fr 0.9fr 2fr; /* 7 columns when canEdit */
      gap: 0;
      background: linear-gradient(135deg, var(--theme-bg-secondary) 0%, var(--theme-bg-elevated) 100%);
      border-bottom: 2px solid var(--border-primary);
      position: sticky;
      top: 0;
      z-index: 10;
    }
    
    /* Readonly modifier: 6 columns when canEditProducts=false (no Acciones column) */
    .grid-headers.readonly {
      grid-template-columns: 1.5fr 1fr 0.9fr 0.9fr 1fr 0.9fr; /* 6 columns without Acciones */
    }

    /* Grid header cell */
    .grid-header {
      padding: 0.75rem 0.625rem;
      font-weight: 700;
      font-size: 0.75rem;
      color: var(--text-secondary);
      text-transform: uppercase;
      letter-spacing: 0.1em;
      white-space: nowrap;
      text-align: left;
    }

    /* Products grid - 7 columns on desktop when canEdit is true */
    /* CRITICAL: Fixed columns for table-like layout */
    .products-grid {
      grid-template-columns: 1.5fr 1fr 0.9fr 0.9fr 1fr 0.9fr 2fr; /* 7 columns - matches headers */
      gap: 0; /* No gaps to simulate table */
    }
    
    /* Readonly modifier: 6 columns when canEditProducts=false (no Acciones column) */
    .products-grid.readonly {
      grid-template-columns: 1.5fr 1fr 0.9fr 0.9fr 1fr 0.9fr; /* 6 columns without Acciones */
    }

    /* Product grid item - display: contents makes it transparent */
    /* Cells align directly to parent grid */
    .product-grid-item {
      display: contents; /* CRÍTICO: contenedor transparente, celdas alineadas al grid padre */
    }

    /* Grid cells on desktop - table-like appearance */
    .grid-cell {
      padding: 0.875rem 0.625rem;
      font-size: 0.9375rem;
      line-height: 1.5;
      border-right: 1px solid var(--border-primary);
      background: var(--theme-bg-elevated);
      transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
      position: relative;
    }

    .grid-cell:last-child {
      border-right: none;
    }

    /* Borde izquierdo en primera celda - aparece en hover */
    .grid-cell:first-child::before {
      content: '';
      position: absolute;
      left: 0;
      top: 0;
      bottom: 0;
      width: 3px;
      background: var(--accent-primary);
      opacity: 0;
      transition: opacity 0.3s ease;
    }

    /* Row hover effect - Hybrid: gradient + transform + shadow */
    .product-grid-item:hover .grid-cell {
      background: linear-gradient(90deg, var(--theme-bg-secondary) 0%, transparent 100%);
      transform: translateY(-1px);
      box-shadow: 0 2px 8px rgba(0, 147, 247, 0.1);
    }

    /* Borde izquierdo aparece en hover */
    .product-grid-item:hover .grid-cell:first-child::before {
      opacity: 1;
    }

    /* Specific cell styling */
    .name-cell {
      font-weight: 600;
    }

    .price-cell {
      font-family: 'Courier New', monospace;
      font-size: 0.875rem;
    }

    .stock-cell.low-stock {
      color: var(--accent-warning);
      font-weight: 600;
    }

    .actions-cell {
      justify-content: flex-start;
      gap: 0.5rem;
      flex-wrap: wrap;
    }
  }

  /* Mobile: Hide grid, show cards */
  @media (max-width: 768px) {
    .products-grid-container {
      display: none !important; /* Hide grid on mobile */
    }

    .products-cards {
      display: grid !important;
      grid-template-columns: 1fr;
      gap: var(--spacing-md);
    }
  }

  /* Desktop: Hide cards, show grid - TABLE-LIKE LAYOUT */
  @media (min-width: 769px) {
    .products-grid-container {
      display: block !important; /* Show grid on desktop */
    }

    .products-cards {
      display: none !important; /* Hide cards on desktop */
    }

    /* Ensure grid is visible and properly structured */
    .products-grid {
      display: grid !important;
      grid-template-columns: 1.5fr 1fr 0.9fr 0.9fr 1fr 0.9fr 2fr !important;
      gap: 0 !important;
    }
    
    /* Readonly modifier override for desktop */
    .products-grid.readonly {
      grid-template-columns: 1.5fr 1fr 0.9fr 0.9fr 1fr 0.9fr !important; /* 6 columns without Acciones */
    }
  }

  /* Product Cards (Mobile) */
  .product-card {
    background: var(--theme-bg-elevated);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-lg);
    padding: var(--spacing-lg);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: var(--shadow-sm);
  }

  .product-card:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-md);
    border-color: var(--accent-primary);
  }

  .product-card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--spacing-md);
    padding-bottom: var(--spacing-md);
    border-bottom: 1px solid var(--border-primary);
  }

  .product-card-title {
    font-size: var(--text-lg);
    font-weight: 700;
    color: var(--text-primary);
    margin: 0;
  }

  .product-card-body {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-sm);
    margin-bottom: var(--spacing-md);
  }

  .product-card-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: var(--spacing-xs) 0;
  }

  .product-card-label {
    font-weight: 600;
    color: var(--text-secondary);
    font-size: var(--text-sm);
  }

  .product-card-value {
    color: var(--text-primary);
    font-size: var(--text-sm);
    text-align: right;
  }

  .product-card-value.low-stock {
    color: var(--accent-warning);
    font-weight: 600;
  }

  .product-card-actions {
    display: flex;
    gap: var(--spacing-sm);
    flex-wrap: wrap;
    padding-top: var(--spacing-md);
    border-top: 1px solid var(--border-primary);
  }

  .actions-group {
    display: flex;
    gap: var(--spacing-sm);
    flex-wrap: wrap;
  }

  /* Delete Confirm Modal */
  .modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
    backdrop-filter: blur(4px);
  }

  .modal-content {
    background: var(--theme-bg-primary);
    padding: var(--spacing-xl);
    border-radius: var(--radius-lg);
    max-width: 500px;
    width: 90%;
    box-shadow: var(--shadow-xl);
    border: 1px solid var(--border-primary);
  }

  .modal-title {
    font-size: var(--text-2xl);
    font-weight: 700;
    color: var(--text-primary);
    margin: 0 0 var(--spacing-md) 0;
  }

  .modal-message {
    color: var(--text-primary);
    margin-bottom: var(--spacing-md);
    line-height: 1.6;
  }

  .modal-warning {
    color: var(--accent-warning);
    font-weight: 600;
    margin-bottom: var(--spacing-lg);
    padding: var(--spacing-md);
    background: rgba(255, 193, 7, 0.1);
    border-radius: var(--radius-md);
    border-left: 3px solid var(--accent-warning);
  }

  .form-footer {
    display: flex;
    gap: var(--spacing-md);
    justify-content: flex-end;
    margin-top: var(--spacing-lg);
  }

  .btn {
    padding: var(--spacing-md) var(--spacing-lg);
    border-radius: var(--radius-md);
    font-size: var(--text-base);
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    border: none;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: var(--spacing-xs);
  }

  .btn-secondary {
    background: var(--theme-bg-secondary);
    color: var(--text-primary);
    border: 1px solid var(--border-primary);
  }

  .btn-secondary:hover {
    background: var(--theme-bg-elevated);
    transform: translateY(-1px);
    box-shadow: var(--shadow-sm);
  }

  .btn-danger {
    background: var(--accent-danger);
    color: white;
  }

  .btn-danger:hover {
    background: #b8043a;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(211, 5, 84, 0.3);
  }

  @media (max-width: 768px) {
    .form-footer {
      flex-direction: column;
    }

    .btn {
      width: 100%;
    }
  }
</style>

