<script lang="ts">
  /**
   * PackageList component - Displays packages in a table with CRUD operations.
   */
  import { onMount } from "svelte";
  import { Button } from "@kidyland/ui";
  import type { Package } from "@kidyland/shared/types";
  import {
    packagesAdminStore,
    fetchAllPackages,
    deletePackage,
  } from "$lib/stores/packages-admin";
  import { canEdit } from "$lib/stores/auth";
  import { user } from "$lib/stores/auth";
  import { getModulePermissions } from "$lib/utils/permissions";
  import ProductPackageForm from "./ProductPackageForm.svelte";
  import ServicePackageForm from "./ServicePackageForm.svelte";
  import LoadingSpinner from "./LoadingSpinner.svelte";
  import ErrorBanner from "./ErrorBanner.svelte";
  import { inferPackageType } from "$lib/utils/package-helpers";
  import { 
    Package as PackageIcon, 
    Plus, 
    Edit, 
    Trash2,
    ShoppingBag,
    Gamepad2
  } from "lucide-svelte";

  // Reactive stores
  $: currentUser = $user;
  $: adminPerms = currentUser ? getModulePermissions(currentUser.role, "admin") : null;
  $: canViewPackages = adminPerms?.canAccess ?? false;
  $: canEditPackages = adminPerms?.canEdit ?? false;

  // Local state
  let selectedPackage: Package | null = null;
  let showCreateProductModal = false;
  let showCreateServiceModal = false;
  let showEditModal = false;
  let showDeleteConfirm = false;
  let editPackageType: "product" | "service" | null = null;

  // Load packages on mount
  // Logic: super_admin and admin_viewer see all packages (no filter), other users see filtered by sucursal_id
  onMount(() => {
    if (canViewPackages) {
      const filterSucursalId = currentUser?.sucursal_id || undefined;
      fetchAllPackages(filterSucursalId);
    }
  });

  function formatPrice(cents: number): string {
    return `$${(cents / 100).toFixed(2)}`;
  }

  function formatItems(items: Package["included_items"]): string {
    if (!items || items.length === 0) return "Sin items";
    return `${items.length} item(s)`;
  }

  async function handleDelete() {
    if (selectedPackage && canEditPackages) {
      try {
        await deletePackage(selectedPackage.id);
        showDeleteConfirm = false;
        selectedPackage = null;
      } catch (error) {
        // Error handled by store
      }
    }
  }

  function handleCreateProductSuccess() {
    showCreateProductModal = false;
    // Refresh list using the same logic as onMount
    const filterSucursalId = currentUser?.sucursal_id || undefined;
    fetchAllPackages(filterSucursalId);
  }

  function handleCreateServiceSuccess() {
    showCreateServiceModal = false;
    // Refresh list using the same logic as onMount
    const filterSucursalId = currentUser?.sucursal_id || undefined;
    fetchAllPackages(filterSucursalId);
  }

  function handleCreateProductClick() {
    showCreateProductModal = true;
  }

  function handleCreateServiceClick() {
    showCreateServiceModal = true;
  }

  function handleEdit(pkg: Package) {
    selectedPackage = pkg;
    const inferredType = inferPackageType(pkg.included_items);
    // Only allow editing if it's a pure product or service package (not mixed)
    if (inferredType === "product" || inferredType === "service") {
      editPackageType = inferredType;
      showEditModal = true;
    } else {
      // Mixed packages cannot be edited with the current forms
      console.warn("Mixed packages cannot be edited with current forms");
    }
  }

  function handleUpdateSuccess() {
    showEditModal = false;
    selectedPackage = null;
    editPackageType = null;
    // Refresh list using the same logic as onMount
    const filterSucursalId = currentUser?.sucursal_id || undefined;
    fetchAllPackages(filterSucursalId);
  }
</script>

<div class="packages-container">
  <!-- Main Content: Packages Management -->
  <div class="packages-main">
    <!-- Header with create button -->
    <div class="packages-header">
      <h1 class="page-title">
        <PackageIcon size={32} strokeWidth={1.5} style="display: inline-block; vertical-align: middle; margin-right: 12px;" />
        Gestión de Paquetes
      </h1>
      
      {#if canEditPackages}
        <div class="create-package-button-wrapper">
          <Button 
            variant="brutalist"
            on:click={handleCreateProductClick}
          >
            <ShoppingBag size={18} strokeWidth={1.5} style="display: inline-block; vertical-align: middle; margin-right: 6px;" />
            Crear Paquete de Productos
          </Button>
          <Button 
            variant="brutalist"
            on:click={handleCreateServiceClick}
          >
            <Gamepad2 size={18} strokeWidth={1.5} style="display: inline-block; vertical-align: middle; margin-right: 6px;" />
            Crear Paquete de Servicios
          </Button>
        </div>
      {/if}
    </div>

    <!-- Error banner -->
    <ErrorBanner error={$packagesAdminStore.error} />

    <!-- Loading state -->
    {#if $packagesAdminStore.loading}
      <LoadingSpinner message="Cargando paquetes..." />
    {:else if $packagesAdminStore.list.length === 0 && canViewPackages}
      <div class="empty-state">
        <p>No hay paquetes registrados</p>
        {#if canEditPackages}
          <div class="create-package-button-wrapper">
            <Button variant="brutalist" on:click={handleCreateProductClick}>
              <ShoppingBag size={18} strokeWidth={1.5} style="display: inline-block; vertical-align: middle; margin-right: 6px;" />
              Crear Paquete de Productos
            </Button>
            <Button variant="brutalist" on:click={handleCreateServiceClick}>
              <Gamepad2 size={18} strokeWidth={1.5} style="display: inline-block; vertical-align: middle; margin-right: 6px;" />
              Crear Paquete de Servicios
            </Button>
          </div>
        {/if}
      </div>
    {:else if !canViewPackages}
      <div class="empty-state">
        <p>No tienes permisos para ver paquetes.</p>
      </div>
    {:else}
      <!-- Packages Grid (Future-Proof CSS Grid Pattern #1) -->
      <!-- Desktop: Grid layout, Mobile: Cards layout -->
      <div class="packages-grid-container">
        <!-- Desktop Grid Headers (hidden on mobile) -->
        <div class="grid-headers">
          <div class="grid-header">Nombre</div>
          <div class="grid-header">Descripción</div>
          <div class="grid-header">Precio</div>
          <div class="grid-header">Items Incluidos</div>
          <div class="grid-header">Estado</div>
          {#if canEditPackages}
            <div class="grid-header">Acciones</div>
          {/if}
        </div>

        <!-- Packages Grid Items -->
        <div class="packages-grid">
          {#each $packagesAdminStore.list as pkg (pkg.id)}
            <div class="package-grid-item">
              <!-- Nombre -->
              <div class="grid-cell name-cell">
                {pkg.name}
              </div>
              
              <!-- Descripción -->
              <div class="grid-cell description-cell">
                {pkg.description || "—"}
              </div>
              
              <!-- Precio -->
              <div class="grid-cell price-cell">
                {formatPrice(pkg.price_cents)}
              </div>
              
              <!-- Items Incluidos -->
              <div class="grid-cell items-cell">
                {formatItems(pkg.included_items)}
              </div>
              
              <!-- Estado -->
              <div class="grid-cell status-cell">
                {pkg.active !== false ? "✅ Activo" : "❌ Inactivo"}
              </div>
              
              <!-- Acciones -->
              {#if canEditPackages}
                <div class="grid-cell actions-cell">
                  <div class="actions-group">
                  <Button
                    variant="brutalist"
                    on:click={() => handleEdit(pkg)}
                  >
                    <Edit size={16} strokeWidth={1.5} style="display: inline-block; vertical-align: middle; margin-right: 4px;" />
                    Editar
                  </Button>
                    <Button
                      variant="brutalist-danger"
                      on:click={() => {
                        selectedPackage = pkg;
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

      <!-- Packages cards (Mobile - Enhanced) -->
      <div class="packages-cards">
        {#each $packagesAdminStore.list as pkg (pkg.id)}
          <div class="package-card">
            <div class="package-card-header">
              <h3 class="package-card-title">{pkg.name}</h3>
              <span class="package-card-status">
                {pkg.active !== false ? "✅ Activo" : "❌ Inactivo"}
              </span>
            </div>
            <div class="package-card-body">
              <div class="package-card-row">
                <span class="package-card-label">Descripción:</span>
                <span class="package-card-value">{pkg.description || "—"}</span>
              </div>
              <div class="package-card-row">
                <span class="package-card-label">Precio:</span>
                <span class="package-card-value">{formatPrice(pkg.price_cents)}</span>
              </div>
              <div class="package-card-row">
                <span class="package-card-label">Items Incluidos:</span>
                <span class="package-card-value">{formatItems(pkg.included_items)}</span>
              </div>
            </div>
            {#if canEditPackages}
              <div class="package-card-actions">
                  <Button
                    variant="brutalist"
                    on:click={() => handleEdit(pkg)}
                  >
                    <Edit size={16} strokeWidth={1.5} style="display: inline-block; vertical-align: middle; margin-right: 4px;" />
                    Editar
                  </Button>
                <Button
                  variant="brutalist-danger"
                  on:click={() => {
                    selectedPackage = pkg;
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

<!-- Create Product Package Modal -->
{#if showCreateProductModal && canEditPackages}
  <ProductPackageForm
    open={showCreateProductModal}
    package_={null}
    sucursalId={currentUser?.sucursal_id || ""}
    on:close={() => (showCreateProductModal = false)}
    on:success={handleCreateProductSuccess}
  />
{/if}

<!-- Create Service Package Modal -->
{#if showCreateServiceModal && canEditPackages}
  <ServicePackageForm
    open={showCreateServiceModal}
    package_={null}
    sucursalId={currentUser?.sucursal_id || ""}
    on:close={() => (showCreateServiceModal = false)}
    on:success={handleCreateServiceSuccess}
  />
{/if}

<!-- Edit Modal - Product Package -->
{#if showEditModal && selectedPackage && editPackageType === "product" && canEditPackages}
  <ProductPackageForm
    open={showEditModal}
    package_={selectedPackage}
    sucursalId={currentUser?.sucursal_id || ""}
    on:close={() => {
      showEditModal = false;
      selectedPackage = null;
      editPackageType = null;
    }}
    on:success={handleUpdateSuccess}
  />
{/if}

<!-- Edit Modal - Service Package -->
{#if showEditModal && selectedPackage && editPackageType === "service" && canEditPackages}
  <ServicePackageForm
    open={showEditModal}
    package_={selectedPackage}
    sucursalId={currentUser?.sucursal_id || ""}
    on:close={() => {
      showEditModal = false;
      selectedPackage = null;
      editPackageType = null;
    }}
    on:success={handleUpdateSuccess}
  />
{/if}

<!-- Delete Confirm -->
{#if showDeleteConfirm && selectedPackage}
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
        ¿Estás seguro de que deseas eliminar el paquete <strong>{selectedPackage.name}</strong>?
      </p>
      <p class="modal-warning">
        ⚠️ Esta acción no se puede deshacer.
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
  .packages-container {
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

  .packages-main {
    width: 100%;
    min-width: 0;
  }

  .packages-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--spacing-xl);
    flex-wrap: wrap;
    gap: var(--spacing-md);
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

  .create-package-button-wrapper {
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
    align-items: center;
  }

  /* Mobile: Optimize header and button layout for touch devices */
  @media (max-width: 768px) {
    .packages-header {
      flex-direction: column;
      align-items: stretch;
      gap: var(--spacing-md);
    }

    .page-title {
      font-size: var(--text-2xl);
      text-align: center;
    }

    .create-package-button-wrapper {
      width: 100%;
      flex-direction: column;
      gap: var(--spacing-sm);
      flex-wrap: nowrap;
    }

    .create-package-button-wrapper :global(button) {
      width: 100%;
      min-height: 44px; /* Minimum touch target size for accessibility */
      justify-content: center;
    }

    /* Optimize empty state for mobile (when buttons are duplicated) */
    .empty-state {
      padding: var(--spacing-xl);
    }

    .empty-state .create-package-button-wrapper {
      width: 100%;
      margin-top: var(--spacing-md);
    }
  }

  /* Prevent hover transform issues on touch devices */
  @media (hover: none) and (pointer: coarse) {
    .create-package-button-wrapper :global(.btn-brutalist:hover),
    .empty-state .create-package-button-wrapper :global(.btn-brutalist:hover) {
      transform: none;
      box-shadow: 3px 3px 0px 0px var(--accent-primary);
      border-width: 2px;
    }
  }


  /* FUTURE-PROOF CSS GRID PATTERN #1 - Zero alignment issues */
  .packages-grid-container {
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
  .packages-grid-container::before {
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

  /* Packages Grid - Future-proof auto-responsive */
  .packages-grid {
    display: grid;
    grid-template-columns: 1fr; /* Mobile: single column */
    gap: 0;
    width: 100%;
  }

  /* Desktop: Fixed 6-column grid (5 columns + 1 for actions if canEdit) */
  @media (min-width: 769px) {
    .packages-grid {
      grid-template-columns: 1.5fr 1.5fr 1fr 1fr 0.8fr 2fr !important;
      gap: 0 !important;
    }
  }

  /* Package Grid Item - CRITICAL: display: contents makes container transparent */
  .package-grid-item {
    display: contents; /* Default: transparent container for table-like layout */
  }

  /* Mobile: Override display: contents to show cards */
  @media (max-width: 768px) {
    .package-grid-item {
      display: block; /* Show as block for card layout on mobile */
      padding: var(--spacing-md);
      border-bottom: 1px solid var(--border-primary);
      background: var(--theme-bg-elevated);
      border-radius: var(--radius-lg);
      margin-bottom: var(--spacing-sm);
    }

    .package-grid-item:last-child {
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
      grid-template-columns: 1.5fr 1.5fr 1fr 1fr 0.8fr 2fr; /* 6 columns when canEdit */
      gap: 0;
      background: linear-gradient(135deg, var(--theme-bg-secondary) 0%, var(--theme-bg-elevated) 100%);
      border-bottom: 2px solid var(--border-primary);
      position: sticky;
      top: 0;
      z-index: 10;
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

    /* Packages grid - 6 columns on desktop when canEdit is true */
    .packages-grid {
      grid-template-columns: 1.5fr 1.5fr 1fr 1fr 0.8fr 2fr; /* 6 columns - matches headers */
      gap: 0; /* No gaps to simulate table */
    }

    /* Package grid item - display: contents makes it transparent */
    .package-grid-item {
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

    /* Row hover effect */
    .package-grid-item:hover .grid-cell {
      background: linear-gradient(90deg, var(--theme-bg-secondary) 0%, transparent 100%);
      transform: translateY(-1px);
      box-shadow: 0 2px 8px rgba(0, 147, 247, 0.1);
    }

    /* Borde izquierdo aparece en hover */
    .package-grid-item:hover .grid-cell:first-child::before {
      opacity: 1;
    }

    /* Specific cell styling */
    .name-cell {
      font-weight: 600;
    }

    .description-cell {
      color: var(--text-secondary);
    }

    .price-cell {
      font-family: 'Courier New', monospace;
      font-size: 0.875rem;
      font-weight: 600;
      color: var(--accent-primary);
    }

    .items-cell {
      color: var(--text-secondary);
    }

    .actions-cell {
      justify-content: flex-start;
      gap: 0.5rem;
      flex-wrap: wrap;
    }
  }

  /* Mobile: Hide grid, show cards */
  @media (max-width: 768px) {
    .packages-grid-container {
      display: none !important; /* Hide grid on mobile */
    }

    .packages-cards {
      display: grid !important;
      grid-template-columns: 1fr;
      gap: var(--spacing-md);
    }
  }

  /* Desktop: Hide cards, show grid - TABLE-LIKE LAYOUT */
  @media (min-width: 769px) {
    .packages-grid-container {
      display: block !important; /* Show grid on desktop */
    }

    .packages-cards {
      display: none !important; /* Hide cards on desktop */
    }

    /* Ensure grid is visible and properly structured */
    .packages-grid {
      display: grid !important;
      grid-template-columns: 1.5fr 1.5fr 1fr 1fr 0.8fr 2fr !important;
      gap: 0 !important;
    }
  }

  /* Package Cards (Mobile) */
  .package-card {
    background: var(--theme-bg-elevated);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-lg);
    padding: var(--spacing-lg);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: var(--shadow-sm);
  }

  .package-card:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-md);
    border-color: var(--accent-primary);
  }

  .package-card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--spacing-md);
    padding-bottom: var(--spacing-md);
    border-bottom: 1px solid var(--border-primary);
  }

  .package-card-title {
    font-size: var(--text-lg);
    font-weight: 700;
    color: var(--text-primary);
    margin: 0;
  }

  .package-card-status {
    font-size: var(--text-sm);
    color: var(--text-secondary);
  }

  .package-card-body {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-sm);
    margin-bottom: var(--spacing-md);
  }

  .package-card-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: var(--spacing-xs) 0;
  }

  .package-card-label {
    font-weight: 600;
    color: var(--text-secondary);
    font-size: var(--text-sm);
  }

  .package-card-value {
    color: var(--text-primary);
    font-size: var(--text-sm);
    text-align: right;
  }

  .package-card-actions {
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

  /* Mobile: Optimize action buttons for touch devices */
  @media (max-width: 768px) {
    .package-card-actions {
      flex-direction: column;
      gap: var(--spacing-sm);
      flex-wrap: nowrap;
    }

    .package-card-actions :global(button) {
      width: 100%;
      min-height: 44px; /* Minimum touch target size for accessibility */
      justify-content: center;
    }

    /* Also optimize actions-group for grid view (if visible on mobile) */
    .actions-group {
      flex-direction: column;
      gap: var(--spacing-sm);
      flex-wrap: nowrap;
      width: 100%;
    }

    .actions-group :global(button) {
      width: 100%;
      min-height: 44px;
      justify-content: center;
    }
  }

  /* Prevent hover transform issues on touch devices for action buttons */
  @media (hover: none) and (pointer: coarse) {
    .package-card-actions :global(.btn-brutalist:hover),
    .package-card-actions :global(.btn-brutalist-danger:hover),
    .actions-group :global(.btn-brutalist:hover),
    .actions-group :global(.btn-brutalist-danger:hover) {
      transform: none;
    }

    .package-card-actions :global(.btn-brutalist:hover),
    .actions-group :global(.btn-brutalist:hover) {
      box-shadow: 3px 3px 0px 0px var(--accent-primary);
      border-width: 2px;
    }

    .package-card-actions :global(.btn-brutalist-danger:hover),
    .actions-group :global(.btn-brutalist-danger:hover) {
      box-shadow: 3px 3px 0px 0px var(--accent-danger);
      border-width: 2px;
    }
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

