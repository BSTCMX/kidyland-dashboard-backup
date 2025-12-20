<script lang="ts">
  /**
   * ServiceList component - Displays services in a table with CRUD operations.
   */
  import { onMount } from "svelte";
  import { Button } from "@kidyland/ui";
  import type { Service } from "@kidyland/shared/types";
  import {
    servicesAdminStore,
    fetchAllServices,
    createService,
    updateService,
    deleteService,
  } from "$lib/stores/services-admin";
import { canEdit, hasRole } from "$lib/stores/auth";
import { user } from "$lib/stores/auth";
import { getModulePermissions } from "$lib/utils/permissions";
import { getServiceFilterSucursalId } from "$lib/utils/service-filters";
import ServiceForm from "./ServiceForm.svelte";
  import LoadingSpinner from "./LoadingSpinner.svelte";
  import ErrorBanner from "./ErrorBanner.svelte";
  import { 
    Gamepad2, 
    Plus, 
    Edit, 
    Trash2 
  } from "lucide-svelte";
  import Badge from "$lib/components/shared/Badge.svelte";

  // Reactive stores
  $: currentUser = $user;
  $: adminPerms = currentUser ? getModulePermissions(currentUser.role, "admin") : null;
  $: canViewServices = adminPerms?.canAccess ?? false;
  $: canEditServices = adminPerms?.canEdit ?? false;

  // Local state
  let selectedService: Service | null = null;
  let showCreateModal = false;
  let showEditModal = false;
  let showDeleteConfirm = false;

  // Load services on mount
  // Logic: super_admin and admin_viewer see all services (no filter), other users see filtered by sucursal_id
  onMount(() => {
    if (canViewServices) {
      const filterSucursalId = getServiceFilterSucursalId(currentUser);
      fetchAllServices(filterSucursalId);
    }
  });

  function formatPrice(cents: number): string {
    return `$${(cents / 100).toFixed(2)}`;
  }

  function formatDurations(durations: number[]): string {
    return durations.map((d) => `${d} min`).join(", ");
  }

  /**
   * Get prices in the order of durations_allowed (preserves original order).
   * Returns array of {duration, price} tuples in the same order as durations_allowed.
   */
  function getPricesInOrder(
    durationsAllowed: number[],
    durationPrices: Record<number, number> | undefined
  ): Array<{ duration: number; price: number }> {
    if (!durationPrices || !durationsAllowed || durationsAllowed.length === 0) {
      return [];
    }

    // Iterate over durations_allowed to preserve original order
    return durationsAllowed
      .filter((duration) => durationPrices[duration] !== undefined)
      .map((duration) => ({
        duration,
        price: durationPrices[duration],
      }));
  }

  /**
   * Format a single price entry (duration + price).
   */
  function formatPriceEntry(duration: number, price: number): string {
    return `${duration}min: ${formatPrice(price)}`;
  }

  /**
   * Format price list with intelligent truncation.
   * Shows all prices if ≤5, otherwise shows first 5 + "..."
   */
  function formatPriceList(
    pricesInOrder: Array<{ duration: number; price: number }>,
    maxVisible: number = 5
  ): string {
    if (pricesInOrder.length === 0) {
      return "N/A";
    }

    // If all prices are the same, show single price (optimization)
    const uniquePrices = new Set(pricesInOrder.map((p) => p.price));
    if (uniquePrices.size === 1) {
      return formatPrice(pricesInOrder[0].price);
    }

    // If within limit, show all
    if (pricesInOrder.length <= maxVisible) {
      return pricesInOrder
        .map((p) => formatPriceEntry(p.duration, p.price))
        .join(", ");
    }

    // Truncate: show first maxVisible + "..."
    const visible = pricesInOrder.slice(0, maxVisible);
    const formatted = visible
      .map((p) => formatPriceEntry(p.duration, p.price))
      .join(", ");
    return `${formatted}, ...`;
  }

  /**
   * Format prices per slot for display.
   * Preserves the order of durations_allowed (not sorted by value).
   * Shows all prices if ≤5, otherwise truncates with "..."
   */
  function formatPriceRange(
    durationsAllowed: number[],
    durationPrices: Record<number, number> | undefined
  ): string {
    const pricesInOrder = getPricesInOrder(durationsAllowed, durationPrices);
    return formatPriceList(pricesInOrder);
  }

  async function handleDelete() {
    if (selectedService && canEditServices) {
      const success = await deleteService(selectedService.id);
      if (success) {
        showDeleteConfirm = false;
        selectedService = null;
        // Refresh list with appropriate filter based on role
        const filterSucursalId = getServiceFilterSucursalId(currentUser);
        fetchAllServices(filterSucursalId);
      }
    }
  }

  function handleCreateSuccess() {
    showCreateModal = false;
    // Refresh list with appropriate filter based on role
    const filterSucursalId = getServiceFilterSucursalId(currentUser);
    fetchAllServices(filterSucursalId);
  }

  function handleUpdateSuccess() {
    showEditModal = false;
    selectedService = null;
    // Refresh list with appropriate filter based on role
    const filterSucursalId = getServiceFilterSucursalId(currentUser);
    fetchAllServices(filterSucursalId);
  }
</script>

<div class="services-container">
  <!-- Main Content: Services Management -->
  <div class="services-main">
    <!-- Header with create button -->
    <div class="services-header">
      <h1 class="page-title">
        <Gamepad2 size={32} strokeWidth={1.5} style="display: inline-block; vertical-align: middle; margin-right: 12px;" />
        Gestión de Servicios
      </h1>
      
      {#if canEditServices}
        <div class="create-service-button-wrapper">
          <Button 
            variant="brutalist"
            on:click={() => (showCreateModal = true)}
          >
            <Plus size={18} strokeWidth={1.5} style="display: inline-block; vertical-align: middle; margin-right: 6px;" />
            Crear Servicio
          </Button>
        </div>
      {/if}
    </div>

    <!-- Error banner -->
    <ErrorBanner error={$servicesAdminStore.error} />

    <!-- Loading state -->
    {#if $servicesAdminStore.loading}
      <LoadingSpinner message="Cargando servicios..." />
    {:else if $servicesAdminStore.list.length === 0}
      <div class="empty-state">
        <p>No hay servicios registrados</p>
        {#if canEditServices}
          <Button variant="brutalist" on:click={() => (showCreateModal = true)}>
            <Plus size={18} strokeWidth={1.5} style="display: inline-block; vertical-align: middle; margin-right: 6px;" />
            Crear Primer Servicio
          </Button>
        {/if}
      </div>
    {:else}
      <!-- Services Grid (Future-Proof CSS Grid Pattern #1) -->
      <!-- Desktop: Grid layout, Mobile: Cards layout -->
      <div class="services-grid-container">
        <!-- Desktop Grid Headers (hidden on mobile) -->
        <div class="grid-headers" class:readonly={!canEditServices}>
          <div class="grid-header">Nombre</div>
          <div class="grid-header">Duración</div>
          <div class="grid-header">Precios por Slot</div>
          <div class="grid-header">Alertas</div>
          <div class="grid-header">Estado</div>
          {#if canEditServices}
            <div class="grid-header">Acciones</div>
          {/if}
        </div>

        <!-- Services Grid Items -->
        <div class="services-grid" class:readonly={!canEditServices}>
          {#each $servicesAdminStore.list as service (service.id)}
            <div class="service-grid-item">
              <!-- Nombre -->
              <div class="grid-cell name-cell">
                {service.name}
              </div>
              
              <!-- Duración -->
              <div class="grid-cell duration-cell">
                {formatDurations(service.durations_allowed)}
              </div>
              
              <!-- Precios por Slot -->
              <div class="grid-cell price-cell">
                {formatPriceRange(service.durations_allowed, service.duration_prices)}
              </div>
              
              <!-- Alertas -->
              <div class="grid-cell alerts-cell">
                {service.alerts_config?.length > 0
                  ? `${service.alerts_config.length} configuradas`
                  : "Sin alertas"}
              </div>
              
              <!-- Estado -->
              <div class="grid-cell status-cell">
                <Badge variant={service.active !== false ? "success" : "danger"} size="sm">
                  {service.active !== false ? "Activo" : "Inactivo"}
                </Badge>
              </div>
              
              <!-- Acciones -->
              {#if canEditServices}
                <div class="grid-cell actions-cell">
                  <div class="actions-group">
                    <Button
                      variant="brutalist"
                      on:click={() => {
                        selectedService = service;
                        showEditModal = true;
                      }}
                    >
                      <Edit size={16} strokeWidth={1.5} style="display: inline-block; vertical-align: middle; margin-right: 4px;" />
                      Editar
                    </Button>
                    <Button
                      variant="brutalist-danger"
                      on:click={() => {
                        selectedService = service;
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

      <!-- Services cards (Mobile - Enhanced) -->
      <div class="services-cards">
        {#each $servicesAdminStore.list as service (service.id)}
          <div class="service-card">
            <div class="service-card-header">
              <h3 class="service-card-title">{service.name}</h3>
              <Badge variant={service.active !== false ? "success" : "danger"} size="sm">
                {service.active !== false ? "Activo" : "Inactivo"}
              </Badge>
            </div>
            <div class="service-card-body">
              <div class="service-card-row">
                <span class="service-card-label">Duración:</span>
                <span class="service-card-value">{formatDurations(service.durations_allowed)}</span>
              </div>
              <div class="service-card-row">
                <span class="service-card-label">Precios por Slot:</span>
                <span class="service-card-value">
                  {formatPriceRange(service.durations_allowed, service.duration_prices)}
                </span>
              </div>
              <div class="service-card-row">
                <span class="service-card-label">Alertas:</span>
                <span class="service-card-value">
                  {service.alerts_config?.length > 0
                    ? `${service.alerts_config.length} configuradas`
                    : "Sin alertas"}
                </span>
              </div>
            </div>
            {#if canEditServices}
              <div class="service-card-actions">
                <Button
                  variant="brutalist"
                  on:click={() => {
                    selectedService = service;
                    showEditModal = true;
                  }}
                >
                  <Edit size={16} strokeWidth={1.5} style="display: inline-block; vertical-align: middle; margin-right: 4px;" />
                  Editar
                </Button>
                <Button
                  variant="brutalist-danger"
                  on:click={() => {
                    selectedService = service;
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
{#if showCreateModal && canEditServices}
  <ServiceForm
    open={showCreateModal}
    service={null}
    sucursalId={currentUser?.sucursal_id || ""}
    on:close={() => (showCreateModal = false)}
    on:success={handleCreateSuccess}
  />
{/if}

<!-- Edit Modal -->
{#if showEditModal && selectedService && canEditServices}
  <ServiceForm
    open={showEditModal}
    service={selectedService}
    sucursalId={currentUser?.sucursal_id || ""}
    on:close={() => {
      showEditModal = false;
      selectedService = null;
    }}
    on:success={handleUpdateSuccess}
  />
{/if}

<!-- Delete Confirm -->
{#if showDeleteConfirm && selectedService}
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
        ¿Estás seguro de que deseas eliminar el servicio <strong>{selectedService.name}</strong>?
      </p>
      <p class="modal-warning">
        ⚠️ El servicio se eliminará permanentemente después de 30 días. Podrás recuperarlo durante este período.
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
  .services-container {
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

  .services-main {
    width: 100%;
    min-width: 0;
  }

  .services-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--spacing-xl);
    flex-wrap: wrap;
    gap: var(--spacing-md);
  }

  @media (max-width: 768px) {
    .services-header {
      flex-direction: column;
      align-items: stretch;
      gap: var(--spacing-md);
    }

    .page-title {
      font-size: var(--text-2xl);
      text-align: center;
    }

    .create-service-button-wrapper {
      width: 100%;
    }

    .create-service-button-wrapper :global(button) {
      width: 100%;
      min-height: 44px; /* Minimum touch target size for accessibility */
      justify-content: center;
    }

    .empty-state :global(button) {
      width: 100%;
      min-height: 44px; /* Minimum touch target size for accessibility */
      justify-content: center;
    }

    .service-card-actions {
      flex-direction: column;
      gap: var(--spacing-sm);
      flex-wrap: nowrap;
    }

    .service-card-actions :global(button) {
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
    .create-service-button-wrapper :global(.btn-brutalist:hover),
    .empty-state :global(.btn-brutalist:hover),
    .service-card-actions :global(.btn-brutalist:hover),
    .service-card-actions :global(.btn-brutalist-danger:hover),
    .actions-group :global(.btn-brutalist:hover),
    .actions-group :global(.btn-brutalist-danger:hover) {
      transform: none;
    }

    .create-service-button-wrapper :global(.btn-brutalist:hover),
    .empty-state :global(.btn-brutalist:hover),
    .actions-group :global(.btn-brutalist:hover) {
      box-shadow: 3px 3px 0px 0px var(--accent-primary);
      border-width: 2px;
    }

    .service-card-actions :global(.btn-brutalist-danger:hover),
    .actions-group :global(.btn-brutalist-danger:hover) {
      box-shadow: 3px 3px 0px 0px var(--accent-danger);
      border-width: 2px;
    }

    .service-card:hover {
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
  .services-grid-container {
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
  .services-grid-container::before {
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

  /* Services Grid - Future-proof auto-responsive */
  /* Mobile: single column (will be hidden, cards shown instead) */
  .services-grid {
    display: grid;
    grid-template-columns: 1fr; /* Mobile: single column */
    gap: 0;
    width: 100%;
  }

  /* Desktop: Fixed 6-column grid for table-like layout (5 columns + 1 for actions if canEdit) */
  @media (min-width: 769px) {
    .services-grid {
      grid-template-columns: 1.5fr 1.2fr 1fr 1fr 0.9fr 2fr !important;
      gap: 0 !important;
    }
    
    /* Readonly modifier: 5 columns when canEditServices=false (no Acciones column) */
    .services-grid.readonly {
      grid-template-columns: 1.5fr 1.2fr 1fr 1fr 0.9fr !important; /* 5 columns without Acciones */
    }
  }

  /* Service Grid Item - CRITICAL: display: contents makes container transparent */
  /* On mobile, we need to override to show cards */
  .service-grid-item {
    display: contents; /* Default: transparent container for table-like layout */
  }

  /* Mobile: Override display: contents to show cards */
  @media (max-width: 768px) {
    .service-grid-item {
      display: block; /* Show as block for card layout on mobile */
      padding: var(--spacing-md);
      border-bottom: 1px solid var(--border-primary);
      background: var(--theme-bg-elevated);
      border-radius: var(--radius-lg);
      margin-bottom: var(--spacing-sm);
    }

    .service-grid-item:last-child {
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
      grid-template-columns: 1.5fr 1.2fr 1fr 1fr 0.9fr 2fr; /* 6 columns when canEdit */
      gap: 0;
      background: linear-gradient(135deg, var(--theme-bg-secondary) 0%, var(--theme-bg-elevated) 100%);
      border-bottom: 2px solid var(--border-primary);
      position: sticky;
      top: 0;
      z-index: 10;
    }
    
    /* Readonly modifier: 5 columns when canEditServices=false (no Acciones column) */
    .grid-headers.readonly {
      grid-template-columns: 1.5fr 1.2fr 1fr 1fr 0.9fr; /* 5 columns without Acciones */
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

    /* Services grid - 6 columns on desktop when canEdit is true */
    /* CRITICAL: Fixed columns for table-like layout */
    .services-grid {
      grid-template-columns: 1.5fr 1.2fr 1fr 1fr 0.9fr 2fr; /* 6 columns - matches headers */
      gap: 0; /* No gaps to simulate table */
    }
    
    /* Readonly modifier: 5 columns when canEditServices=false (no Acciones column) */
    .services-grid.readonly {
      grid-template-columns: 1.5fr 1.2fr 1fr 1fr 0.9fr; /* 5 columns without Acciones */
    }

    /* Service grid item - display: contents makes it transparent */
    /* Cells align directly to parent grid */
    .service-grid-item {
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
    .service-grid-item:hover .grid-cell {
      background: linear-gradient(90deg, var(--theme-bg-secondary) 0%, transparent 100%);
      transform: translateY(-1px);
      box-shadow: 0 2px 8px rgba(0, 147, 247, 0.1);
    }

    /* Borde izquierdo aparece en hover */
    .service-grid-item:hover .grid-cell:first-child::before {
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

    .actions-cell {
      justify-content: flex-start;
      gap: 0.5rem;
      flex-wrap: wrap;
    }
  }

  /* Mobile: Hide grid, show cards */
  @media (max-width: 768px) {
    .services-grid-container {
      display: none !important; /* Hide grid on mobile */
    }

    .services-cards {
      display: grid !important;
      grid-template-columns: 1fr;
      gap: var(--spacing-md);
    }
  }

  /* Desktop: Hide cards, show grid - TABLE-LIKE LAYOUT */
  @media (min-width: 769px) {
    .services-grid-container {
      display: block !important; /* Show grid on desktop */
    }

    .services-cards {
      display: none !important; /* Hide cards on desktop */
    }

    /* Ensure grid is visible and properly structured */
    .services-grid {
      display: grid !important;
      grid-template-columns: 1.5fr 1.2fr 1fr 1fr 0.9fr 2fr !important;
      gap: 0 !important;
    }
  }

  /* Service Cards (Mobile) */
  .service-card {
    background: var(--theme-bg-elevated);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-lg);
    padding: var(--spacing-lg);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: var(--shadow-sm);
  }

  .service-card:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-md);
    border-color: var(--accent-primary);
  }

  .service-card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--spacing-md);
    padding-bottom: var(--spacing-md);
    border-bottom: 1px solid var(--border-primary);
  }

  .service-card-title {
    font-size: var(--text-lg);
    font-weight: 700;
    color: var(--text-primary);
    margin: 0;
  }

  .service-card-body {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-sm);
    margin-bottom: var(--spacing-md);
  }

  .service-card-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: var(--spacing-xs) 0;
  }

  .service-card-label {
    font-weight: 600;
    color: var(--text-secondary);
    font-size: var(--text-sm);
  }

  .service-card-value {
    color: var(--text-primary);
    font-size: var(--text-sm);
    text-align: right;
  }

  .service-card-actions {
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
