<script lang="ts">
  /**
   * SucursalList component - Displays sucursales in a table with CRUD operations.
   */
  import { onMount } from "svelte";
  import { Button } from "@kidyland/ui";
  import type { Sucursal } from "@kidyland/shared/types";
  import {
    sucursalesAdminStore,
    fetchAllSucursales,
    createSucursal,
    updateSucursal,
    deleteSucursal,
  } from "$lib/stores/sucursales-admin";
  import { canEdit } from "$lib/stores/auth";
  import SucursalForm from "./SucursalForm.svelte";
  import LoadingSpinner from "./LoadingSpinner.svelte";
  import ErrorBanner from "./ErrorBanner.svelte";
  import { notify } from "$lib/stores/notifications";
  import { 
    Building2, 
    Plus, 
    Edit, 
    Trash2 
  } from "lucide-svelte";
  import Badge from "$lib/components/shared/Badge.svelte";

  // Reactive stores
  $: canEditSucursales = canEdit("admin");

  // Local state
  let selectedSucursal: Sucursal | null = null;
  let showCreateModal = false;
  let showEditModal = false;
  let showDeleteConfirm = false;

  // Load sucursales on mount
  onMount(() => {
    if (canEditSucursales) {
      fetchAllSucursales();
    }
  });

  async function handleDelete() {
    if (selectedSucursal && canEditSucursales) {
      try {
        const success = await deleteSucursal(selectedSucursal.id);
        if (success) {
          notify.success("Sucursal eliminada", "La sucursal ha sido desactivada correctamente");
          showDeleteConfirm = false;
          selectedSucursal = null;
        }
      } catch (error: any) {
        notify.error("Error", error.message || "No se pudo eliminar la sucursal");
      }
    }
  }

  function handleCreateSuccess() {
    showCreateModal = false;
    fetchAllSucursales();
    notify.success("Sucursal creada", "La sucursal ha sido creada correctamente");
  }

  function handleUpdateSuccess() {
    showEditModal = false;
    selectedSucursal = null;
    fetchAllSucursales();
    notify.success("Sucursal actualizada", "La sucursal ha sido actualizada correctamente");
  }
</script>

<div class="sucursales-container">
  <!-- Main Content: Sucursales Management -->
  <div class="sucursales-main">
    <!-- Header with create button -->
    <div class="sucursales-header">
      <h1 class="page-title">
        <Building2 size={32} strokeWidth={1.5} style="display: inline-block; vertical-align: middle; margin-right: 12px;" />
        Gestión de Sucursales
      </h1>
      
      {#if canEditSucursales}
        <div class="create-sucursal-button-wrapper">
          <Button 
            variant="brutalist"
            on:click={() => (showCreateModal = true)}
          >
            <Plus size={18} strokeWidth={1.5} style="display: inline-block; vertical-align: middle; margin-right: 6px;" />
            Crear Sucursal
          </Button>
        </div>
      {/if}
    </div>

    <!-- Error banner -->
    <ErrorBanner error={$sucursalesAdminStore.error} />

    <!-- Loading state -->
    {#if $sucursalesAdminStore.loading}
      <LoadingSpinner message="Cargando sucursales..." />
    {:else if $sucursalesAdminStore.list.length === 0}
      <div class="empty-state">
        <p>No hay sucursales registradas</p>
        {#if canEditSucursales}
          <Button variant="brutalist" on:click={() => (showCreateModal = true)}>
            <Plus size={18} strokeWidth={1.5} style="display: inline-block; vertical-align: middle; margin-right: 6px;" />
            Crear Primera Sucursal
          </Button>
        {/if}
      </div>
    {:else}
      <!-- Sucursales Grid (Future-Proof CSS Grid Pattern #1) -->
      <!-- Desktop: Grid layout, Mobile: Cards layout -->
      <div class="sucursales-grid-container">
        <!-- Desktop Grid Headers (hidden on mobile) -->
        <div class="grid-headers">
          <div class="grid-header">Identificador</div>
          <div class="grid-header">Nombre</div>
          <div class="grid-header">Dirección</div>
          <div class="grid-header">Zona Horaria</div>
          <div class="grid-header">Estado</div>
          {#if canEditSucursales}
            <div class="grid-header">Acciones</div>
          {/if}
        </div>

        <!-- Sucursales Grid Items -->
        <div class="sucursales-grid">
          {#each $sucursalesAdminStore.list as sucursal (sucursal.id)}
            <div class="sucursal-grid-item">
              <!-- Identificador -->
              <div class="grid-cell identifier-cell" title={sucursal.identifier}>
                <span class="font-mono text-sm identifier-badge">{sucursal.identifier}</span>
              </div>
              
              <!-- Nombre -->
              <div class="grid-cell name-cell">
                {sucursal.name}
              </div>
              
              <!-- Dirección -->
              <div class="grid-cell address-cell">
                {sucursal.address || "—"}
              </div>
              
              <!-- Zona Horaria -->
              <div class="grid-cell timezone-cell">
                <span class="font-mono text-sm">{sucursal.timezone}</span>
              </div>
              
              <!-- Estado -->
              <div class="grid-cell status-cell">
                <Badge variant={sucursal.active ? "success" : "danger"} size="sm">
                  {sucursal.active ? "Activa" : "Inactiva"}
                </Badge>
              </div>
              
              <!-- Acciones -->
              {#if canEditSucursales}
                <div class="grid-cell actions-cell">
                  <div class="actions-group">
                    <Button
                      variant="brutalist"
                      on:click={() => {
                        selectedSucursal = sucursal;
                        showEditModal = true;
                      }}
                    >
                      <Edit size={16} strokeWidth={1.5} style="display: inline-block; vertical-align: middle; margin-right: 4px;" />
                      Editar
                    </Button>
                    <Button
                      variant="brutalist-danger"
                      on:click={() => {
                        selectedSucursal = sucursal;
                        showDeleteConfirm = true;
                      }}
                      disabled={!sucursal.active}
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

      <!-- Sucursales cards (Mobile - Enhanced) -->
      <div class="sucursales-cards">
        {#each $sucursalesAdminStore.list as sucursal (sucursal.id)}
          <div class="sucursal-card">
            <div class="sucursal-card-header">
              <h3 class="sucursal-card-title">{sucursal.name}</h3>
              <Badge variant={sucursal.active ? "success" : "danger"} size="sm">
                {sucursal.active ? "Activa" : "Inactiva"}
              </Badge>
            </div>
            <div class="sucursal-card-body">
              <div class="sucursal-card-row">
                <span class="sucursal-card-label">Identificador:</span>
                <span class="sucursal-card-value font-mono identifier-badge">{sucursal.identifier}</span>
              </div>
              <div class="sucursal-card-row">
                <span class="sucursal-card-label">Dirección:</span>
                <span class="sucursal-card-value">{sucursal.address || "—"}</span>
              </div>
              <div class="sucursal-card-row">
                <span class="sucursal-card-label">Zona Horaria:</span>
                <span class="sucursal-card-value font-mono">{sucursal.timezone}</span>
              </div>
            </div>
            {#if canEditSucursales}
              <div class="sucursal-card-actions">
                <Button
                  variant="brutalist"
                  on:click={() => {
                    selectedSucursal = sucursal;
                    showEditModal = true;
                  }}
                >
                  <Edit size={16} strokeWidth={1.5} style="display: inline-block; vertical-align: middle; margin-right: 4px;" />
                  Editar
                </Button>
                <Button
                  variant="brutalist-danger"
                  on:click={() => {
                    selectedSucursal = sucursal;
                    showDeleteConfirm = true;
                  }}
                  disabled={!sucursal.active}
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
{#if showCreateModal}
  <SucursalForm
    open={showCreateModal}
    sucursal={null}
    on:close={() => (showCreateModal = false)}
    on:success={handleCreateSuccess}
  />
{/if}

<!-- Edit Modal -->
{#if showEditModal && selectedSucursal}
  <SucursalForm
    open={showEditModal}
    sucursal={selectedSucursal}
    on:close={() => {
      showEditModal = false;
      selectedSucursal = null;
    }}
    on:success={handleUpdateSuccess}
  />
{/if}

  <!-- Delete Confirm -->
  {#if showDeleteConfirm && selectedSucursal}
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
        ¿Estás seguro de que deseas desactivar la sucursal <strong>{selectedSucursal.name}</strong>?
      </p>
      <p class="modal-warning">
        ⚠️ Esta acción desactivará la sucursal (soft delete). No se eliminará permanentemente.
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
  .sucursales-container {
    padding: var(--spacing-xl);
    max-width: 1600px;
    margin: 0 auto;
    background: var(--theme-bg-primary);
    min-height: 100vh;
    width: 100%;
    max-width: 100vw; /* Ensure container doesn't exceed viewport */
    box-sizing: border-box;
    overflow-x: hidden; /* Prevent horizontal scroll on container */
  }

  .sucursales-main {
    width: 100%;
    min-width: 0;
  }

  .sucursales-header {
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

  /* FUTURE-PROOF CSS GRID PATTERN #1 - Zero alignment issues */
  .sucursales-grid-container {
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
  .sucursales-grid-container::before {
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

  /* Sucursales Grid - Future-proof auto-responsive */
  .sucursales-grid {
    display: grid;
    grid-template-columns: 1fr; /* Mobile: single column */
    gap: 0;
    width: 100%;
  }

  /* Desktop: Fixed 6-column grid (5 columns + 1 for actions if canEdit) */
  @media (min-width: 769px) {
    .sucursales-grid {
      grid-template-columns: 1fr 1.5fr 1.5fr 1.2fr 1fr 2fr !important;
      gap: 0 !important;
    }
  }

  /* Sucursal Grid Item - CRITICAL: display: contents makes container transparent */
  .sucursal-grid-item {
    display: contents; /* Default: transparent container for table-like layout */
  }

  /* Mobile: Override display: contents to show cards */
  @media (max-width: 768px) {
    .sucursal-grid-item {
      display: block;
      padding: var(--spacing-md);
      border-bottom: 1px solid var(--border-primary);
      background: var(--theme-bg-elevated);
      border-radius: var(--radius-lg);
      margin-bottom: var(--spacing-sm);
    }

    .sucursal-grid-item:last-child {
      border-bottom: none;
      margin-bottom: 0;
    }

    .grid-cell {
      border-right: none;
      border-bottom: 1px solid var(--border-primary);
      padding: var(--spacing-sm) 0;
      display: block;
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
      grid-template-columns: 1fr 1.5fr 1.5fr 1.2fr 1fr 2fr; /* 6 columns when canEdit */
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

    /* Sucursales grid - 6 columns on desktop when canEdit is true */
    .sucursales-grid {
      grid-template-columns: 1fr 1.5fr 1.5fr 1.2fr 1fr 2fr; /* 6 columns - matches headers */
      gap: 0;
    }

    /* Sucursal grid item - display: contents makes it transparent */
    .sucursal-grid-item {
      display: contents;
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
    .sucursal-grid-item:hover .grid-cell {
      background: linear-gradient(90deg, var(--theme-bg-secondary) 0%, transparent 100%);
      transform: translateY(-1px);
      box-shadow: 0 2px 8px rgba(0, 147, 247, 0.1);
    }

    /* Borde izquierdo aparece en hover */
    .sucursal-grid-item:hover .grid-cell:first-child::before {
      opacity: 1;
    }

    /* Specific cell styling */
    .identifier-cell {
      font-family: 'Courier New', monospace;
      font-size: 0.875rem;
    }

    .name-cell {
      font-weight: 600;
      color: var(--text-primary);
    }

    .address-cell {
      color: var(--text-secondary);
    }

    .timezone-cell {
      font-family: 'Courier New', monospace;
      font-size: 0.875rem;
      color: var(--text-muted);
    }

    .actions-cell {
      justify-content: flex-start;
      gap: 0.5rem;
      flex-wrap: wrap;
    }
  }

  .identifier-badge {
    display: inline-block;
    padding: var(--spacing-xs) var(--spacing-sm);
    background: var(--theme-bg-secondary);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-sm);
    font-weight: 600;
    color: var(--accent-primary);
    letter-spacing: 0.5px;
  }

  .actions-group {
    display: flex;
    gap: var(--spacing-sm);
    flex-wrap: wrap;
  }

  .modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: var(--theme-bg-overlay);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
    padding: var(--spacing-lg);
  }

  .modal-content {
    background: var(--theme-bg-elevated);
    border-radius: var(--radius-lg);
    padding: var(--spacing-xl);
    max-width: 500px;
    width: 100%;
    box-shadow: var(--shadow-xl);
  }

  .modal-title {
    font-family: var(--font-primary);
    font-size: var(--text-2xl);
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: var(--spacing-md);
  }

  .modal-message {
    color: var(--text-secondary);
    margin-bottom: var(--spacing-md);
  }

  .modal-warning {
    color: var(--accent-warning);
    font-size: var(--text-sm);
    margin-bottom: var(--spacing-lg);
    padding: var(--spacing-sm);
    background: rgba(255, 206, 0, 0.1);
    border-radius: var(--radius-sm);
  }

  .form-footer {
    display: flex;
    gap: 12px;
    justify-content: flex-end;
    margin-top: 32px;
    padding-top: 0;
    border-top: none;
  }

  /* Botones con el nuevo estilo */
  .btn {
    background-color: var(--accent-primary, #08d);
    border-radius: 12px;
    border: 0;
    box-sizing: border-box;
    color: #eee;
    cursor: pointer;
    font-size: 18px;
    height: 50px;
    text-align: center;
    width: auto;
    min-width: 120px;
    padding: 0 24px;
    font-family: sans-serif;
    font-weight: 600;
    transition: background-color 0.2s ease;
    display: inline-flex;
    align-items: center;
    justify-content: center;
  }

  .btn-secondary {
    background: linear-gradient(to bottom, #f5f5f5, #e6e6e6);
    background-color: #e6e6e6;
    border-color: #d4d4d4;
    color: #333333;
    text-shadow: 0 1px 1px rgba(255, 255, 255, 0.75);
  }

  .btn-secondary:hover {
    background: linear-gradient(to bottom, #ffffff, #f5f5f5);
    background-color: #f5f5f5;
    border-color: #d4d4d4;
  }

  .btn-secondary:active {
    background: linear-gradient(to bottom, #e6e6e6, #d4d4d4);
    background-color: #d4d4d4;
    box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.1);
  }

  .btn-danger {
    background: linear-gradient(to bottom, #ef4444, #dc2626);
    background-color: #dc2626;
    border-color: #b91c1c;
    color: #ffffff;
    text-shadow: 0 -1px 0 rgba(0, 0, 0, 0.25);
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.2), 0 1px 2px rgba(0, 0, 0, 0.2);
  }

  .btn-danger:hover {
    background: linear-gradient(to bottom, #f87171, #ef4444);
    background-color: #ef4444;
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.2), 0 2px 4px rgba(0, 0, 0, 0.3);
  }

  .btn-danger:active {
    background: linear-gradient(to bottom, #dc2626, #b91c1c);
    background-color: #b91c1c;
    box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.2);
  }

  @media (max-width: 640px) {
    .form-footer {
      flex-direction: column;
    }
  }

  /* Mobile: Hide grid, show cards */
  @media (max-width: 768px) {
    .sucursales-grid-container {
      display: none !important;
    }

    .sucursales-cards {
      display: grid !important;
      grid-template-columns: 1fr;
      gap: var(--spacing-md);
    }

    .sucursales-container {
      padding: var(--spacing-md);
    }

    .sucursales-header {
      flex-direction: column;
      align-items: stretch;
      gap: var(--spacing-md);
    }

    .page-title {
      font-size: var(--text-2xl);
      text-align: center;
    }

    .create-sucursal-button-wrapper {
      width: 100%;
    }

    .create-sucursal-button-wrapper :global(button) {
      width: 100%;
      min-height: 44px; /* Minimum touch target size for accessibility */
      justify-content: center;
    }

    .empty-state :global(button) {
      width: 100%;
      min-height: 44px; /* Minimum touch target size for accessibility */
      justify-content: center;
    }

    .sucursal-card {
      background: var(--theme-bg-elevated);
      border: 2px solid var(--border-primary);
      border-radius: var(--radius-xl);
      padding: var(--spacing-lg);
      box-shadow: var(--shadow-md);
      transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
      position: relative;
      overflow: hidden;
    }

    .sucursal-card::before {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      height: 3px;
      background: linear-gradient(90deg, var(--accent-primary), var(--accent-success));
      opacity: 0;
      transition: opacity 0.3s ease;
    }

    .sucursal-card:hover {
      transform: translateY(-2px);
      box-shadow: var(--shadow-lg);
      border-color: var(--accent-primary);
    }

    .sucursal-card:hover::before {
      opacity: 1;
    }

    .sucursal-card-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: var(--spacing-md);
      padding-bottom: var(--spacing-md);
      border-bottom: 1px solid var(--border-primary);
    }

    .sucursal-card-title {
      font-family: var(--font-primary);
      font-size: var(--text-lg);
      font-weight: 700;
      color: var(--text-primary);
      margin: 0;
    }

    .sucursal-card-body {
      display: flex;
      flex-direction: column;
      gap: var(--spacing-sm);
      margin-bottom: var(--spacing-md);
    }

    .sucursal-card-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: var(--text-sm);
    }

    .sucursal-card-label {
      color: var(--text-secondary);
      font-weight: 500;
    }

    .sucursal-card-value {
      color: var(--text-primary);
    }

    .sucursal-card-actions {
      display: flex;
      flex-direction: column;
      gap: var(--spacing-sm);
      margin-top: var(--spacing-md);
      padding-top: var(--spacing-md);
      border-top: 1px solid var(--border-primary);
    }

    .sucursal-card-actions {
      flex-direction: column;
      gap: var(--spacing-sm);
      flex-wrap: nowrap;
    }

    .sucursal-card-actions :global(button) {
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
    .create-sucursal-button-wrapper :global(.btn-brutalist:hover),
    .empty-state :global(.btn-brutalist:hover),
    .sucursal-card-actions :global(.btn-brutalist:hover),
    .sucursal-card-actions :global(.btn-brutalist-danger:hover),
    .actions-group :global(.btn-brutalist:hover),
    .actions-group :global(.btn-brutalist-danger:hover) {
      transform: none;
    }

    .create-sucursal-button-wrapper :global(.btn-brutalist:hover),
    .empty-state :global(.btn-brutalist:hover),
    .actions-group :global(.btn-brutalist:hover) {
      box-shadow: 3px 3px 0px 0px var(--accent-primary);
      border-width: 2px;
    }

    .sucursal-card-actions :global(.btn-brutalist-danger:hover),
    .actions-group :global(.btn-brutalist-danger:hover) {
      box-shadow: 3px 3px 0px 0px var(--accent-danger);
      border-width: 2px;
    }

    .sucursal-card:hover {
      transform: none;
    }
  }

  /* Desktop: Show grid, hide cards - TABLE-LIKE LAYOUT */
  @media (min-width: 769px) {
    .sucursales-grid-container {
      display: block !important;
    }

    .sucursales-cards {
      display: none !important;
    }

    .sucursales-grid {
      display: grid !important;
      grid-template-columns: 1fr 1.5fr 1.5fr 1.2fr 1fr 2fr !important;
      gap: 0 !important;
    }
  }
</style>

