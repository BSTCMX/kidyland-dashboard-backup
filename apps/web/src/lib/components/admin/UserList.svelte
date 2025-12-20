<script lang="ts">
  /**
   * UserList component - Displays users in a table with filters and pagination.
   */
  import { onMount } from "svelte";
  import { Button } from "@kidyland/ui";
  import type { User } from "@kidyland/shared/types";
  import {
    usersStore,
    filteredUsers,
    fetchUsers,
    setSearchFilter,
    setRoleFilter,
    clearFilters,
    activateUser,
    deactivateUser,
  } from "$lib/stores/users";
  import { hasRole, hasAnyRole, user } from "$lib/stores/auth";
  import { page } from "$app/stores";
  import { fetchAllSucursales, sucursalesAdminStore } from "$lib/stores/sucursales-admin";
  import UserForm from "./UserForm.svelte";
  import UserDeleteConfirm from "./UserDeleteConfirm.svelte";
  import LoadingSpinner from "./LoadingSpinner.svelte";
  import ErrorBanner from "./ErrorBanner.svelte";
  import { 
    Users, 
    UserPlus, 
    Edit, 
    Key, 
    Pause, 
    Trash2, 
    Search, 
    X,
    CheckCircle2,
    LayoutDashboard
  } from "lucide-svelte";
  import Badge from "$lib/components/shared/Badge.svelte";
  import PanelAccessSelector from "./PanelAccessSelector.svelte";

  // Reactive stores
  $: currentUser = $user;
  $: canEditBase = hasRole("super_admin");
  $: canView = hasAnyRole(["super_admin", "admin_viewer"]);
  
  // Check if we're in admin-viewer route (readonly)
  $: isReadonly = $page.url.pathname.startsWith("/admin-viewer");
  $: canEdit = canEditBase && !isReadonly;

  // Local state
  let searchInput = "";
  let roleFilter: "all" | User["role"] = "all";
  let selectedUser: User | null = null;
  let showCreateModal = false;
  let showEditModal = false;
  let showDeleteConfirm = false;
  let showPasswordModal = false;
  let showDeactivateModal = false;
  let currentModalMode: "create" | "edit" | "password" | "deactivate" = "create";
  let createButtonPosition: { top: number; left: number } | null = null;

  // Load users and sucursales on mount
  // IMPORTANT: Load sucursales first to ensure lookup map is ready before users render
  onMount(async () => {
    if (canView) {
      // Load sucursales first (await to ensure they're loaded)
      await fetchAllSucursales();
      // Then load users (sucursales are now available for lookup)
      await fetchUsers();
    }
  });

  // Watch for filter changes
  $: if (searchInput !== $usersStore.filters.search) {
    setSearchFilter(searchInput);
  }

  $: if (roleFilter !== $usersStore.filters.role) {
    setRoleFilter(roleFilter);
  }


  function handleSearch() {
    setSearchFilter(searchInput);
  }

  function handleClearFilters() {
    searchInput = "";
    roleFilter = "all";
    clearFilters();
  }

  function formatDate(dateString: string | null): string {
    if (!dateString) return "Nunca";
    try {
      return new Date(dateString).toLocaleDateString("es-ES", {
        year: "numeric",
        month: "short",
        day: "numeric",
      });
    } catch {
      return "Inválida";
    }
  }

  function getRoleLabel(role: User["role"]): string {
    const labels: Record<User["role"], string> = {
      super_admin: "Super Admin",
      admin_viewer: "Admin Viewer",
      recepcion: "Recepción",
      kidibar: "Kidibar",
      monitor: "Monitor",
    };
    return labels[role] || role;
  }

  // Helper function to get role badge variant (para Badge component)
  function getRoleBadgeVariant(role: User["role"]): 'success' | 'warning' | 'danger' | 'info' | 'primary' | 'secondary' {
    const roleVariants: Record<User["role"], 'success' | 'warning' | 'danger' | 'info' | 'primary' | 'secondary'> = {
      super_admin: "primary",
      admin_viewer: "info",
      recepcion: "success",
      kidibar: "warning",
      monitor: "secondary",
    };
    return roleVariants[role] || "secondary";
  }
  
  // Helper function to get status badge variant
  function getStatusBadgeVariant(isActive: boolean): 'success' | 'danger' {
    return isActive ? "success" : "danger";
  }

  // Create lookup map for sucursales (efficient O(1) lookup)
  // Format: Map<sucursal_id, "identifier - name">
  // IMPORTANT: Include ALL sucursales (not just active) to handle cases where
  // a user's assigned sucursal might be inactive but still valid for display
  // We don't filter by active because users might be assigned to inactive sucursales
  $: sucursalLookupMap = new Map(
    $sucursalesAdminStore.list.map((s) => [
      s.id,
      `${s.identifier} - ${s.name}`,
    ])
  );

  /**
   * Get sucursal name from sucursal_id.
   * Returns formatted string "identifier - name" or "—" if not found/null.
   */
  function getSucursalName(sucursalId: string | null | undefined): string {
    if (!sucursalId) {
      return "—";
    }
    return sucursalLookupMap.get(sucursalId) || "—";
  }

  async function handleActivate(id: string) {
    const result = await activateUser(id);
    if (result) {
      await fetchUsers($usersStore.pagination.page);
    }
  }

  async function handleDeactivate(id: string) {
    const result = await deactivateUser(id);
    if (result) {
      showDeactivateModal = false;
      selectedUser = null;
      await fetchUsers($usersStore.pagination.page);
    }
  }

  async function handleUserCreated() {
    showCreateModal = false;
    createButtonPosition = null;
    // Reload sucursales in case new ones were created, then reload users
    await fetchAllSucursales();
    await fetchUsers($usersStore.pagination.page);
  }

  async function handleUserUpdated() {
    showEditModal = false;
    selectedUser = null;
    // Reload sucursales in case user's sucursal_id changed, then reload users
    await fetchAllSucursales();
    await fetchUsers($usersStore.pagination.page);
  }

  async function handleUserDeleted() {
    showDeleteConfirm = false;
    selectedUser = null;
    await fetchUsers($usersStore.pagination.page);
  }

  function handlePasswordChanged() {
    showPasswordModal = false;
    selectedUser = null;
  }

  let createButtonElement: HTMLElement | null = null;
  
  function handleCreateButtonClick(event: MouseEvent) {
    event.preventDefault();
    event.stopPropagation();
    
    // Get button element from ref or event target
    const target = event.currentTarget as HTMLElement;
    const buttonElement = createButtonElement || target.closest('.create-user-button-wrapper') as HTMLElement || target;
    
    if (!buttonElement) {
      console.error('Could not find button element');
      return;
    }
    
    const rect = buttonElement.getBoundingClientRect();
    // Position modal directly in front of the button
    // Use viewport coordinates (getBoundingClientRect gives viewport-relative, no need for scrollY)
    const modalWidth = 672; // max-w-2xl = 672px
    const modalMaxHeight = 600; // Altura máxima estimada del modal con todos los campos
    const spacing = 20;
    
    // Calculate position relative to viewport (not document)
    let left = Math.max(spacing, rect.right + spacing);
    let top = rect.top;
    
    // If there's not enough space on the right, position to the left
    if (left + modalWidth > window.innerWidth) {
      left = Math.max(spacing, rect.left - modalWidth - spacing);
    }
    
    // Calculate available space below and above button
    const spaceBelow = window.innerHeight - rect.bottom;
    const spaceAbove = rect.top;
    
    // If there's not enough space below, try to position above
    if (spaceBelow < modalMaxHeight && spaceAbove > spaceBelow) {
      // Position above button
      top = Math.max(spacing, rect.top - modalMaxHeight - spacing);
    } else if (top + modalMaxHeight > window.innerHeight) {
      // If still doesn't fit, center it in viewport
      top = Math.max(spacing, (window.innerHeight - modalMaxHeight) / 2);
    }
    
    createButtonPosition = {
      top: top,
      left: left
    };
    
    console.log('[UserList] Button rect:', rect, 'Calculated position:', createButtonPosition);
    
    showCreateModal = true;
    console.log('[UserList] showCreateModal set to true, position:', createButtonPosition);
  }
  
  // Debug: log when showCreateModal changes
  $: if (typeof console !== 'undefined') {
    console.log('[UserList] showCreateModal changed:', showCreateModal);
  }
</script>

<div class="users-container">
  {#if !canView}
    <div class="error-banner">
      No tienes permisos para ver usuarios.
    </div>
  {:else}
    <!-- Panel Access Selector - Horizontal Top Bar (Desktop only) -->
    {#if canEdit && hasRole("super_admin")}
      <div class="panel-access-top">
        <PanelAccessSelector />
      </div>
    {/if}

    <!-- Main Content: Users Management -->
    <div class="users-main">
        <!-- Header with filters -->
        <div class="users-header">
      <h1 class="page-title">
        <Users size={32} strokeWidth={1.5} style="display: inline-block; vertical-align: middle; margin-right: 12px;" />
        Gestión de Usuarios
      </h1>
      
      {#if canEdit}
        <div 
          class="create-user-button-wrapper"
          bind:this={createButtonElement}
        >
          <Button 
            variant="brutalist"
            on:click={handleCreateButtonClick}
          >
            <UserPlus size={18} strokeWidth={1.5} style="display: inline-block; vertical-align: middle; margin-right: 6px;" />
            Crear Usuario
          </Button>
        </div>
      {/if}
    </div>

    <!-- Filters -->
    <div class="filters-section">
      <div class="filter-group">
        <input
          type="text"
          placeholder="Buscar por username o nombre..."
          bind:value={searchInput}
          on:input={handleSearch}
          class="search-input"
        />
      </div>
      
      <div class="filter-group">
        <select bind:value={roleFilter} class="role-select">
          <option value="all">Todos los roles</option>
          <option value="super_admin">Super Admin</option>
          <option value="admin_viewer">Admin Viewer</option>
          <option value="recepcion">Recepción</option>
          <option value="kidibar">Kidibar</option>
          <option value="monitor">Monitor</option>
        </select>
      </div>
      
      <Button variant="brutalist" on:click={handleClearFilters}>
        Limpiar Filtros
      </Button>
    </div>

    <!-- Error banner -->
    <ErrorBanner error={$usersStore.error} />

    <!-- Loading state -->
    {#if $usersStore.loading}
      <LoadingSpinner message="Cargando usuarios..." />
    {:else if $filteredUsers.length === 0}
      <div class="empty-state">
        <p>No se encontraron usuarios.</p>
      </div>
    {:else}
      <!-- Users Grid (Future-Proof CSS Grid Pattern #1) -->
      <!-- Desktop: Grid layout, Mobile: Cards layout -->
      <div class="users-grid-container">
        <!-- Desktop Grid Headers (hidden on mobile) -->
        <div class="grid-headers" class:readonly={!canEdit}>
          <div class="grid-header">Username</div>
          <div class="grid-header">Nombre</div>
          <div class="grid-header">Rol</div>
          <div class="grid-header">Sucursal</div>
          <div class="grid-header">Estado</div>
          <div class="grid-header">Último Login</div>
          <div class="grid-header">Creado</div>
          {#if canEdit}
            <div class="grid-header">Acciones</div>
          {/if}
        </div>

        <!-- Users Grid Items -->
        <div class="users-grid" class:readonly={!canEdit}>
          {#each $filteredUsers as user (user.id)}
            <div class="user-grid-item">
              <!-- Username -->
              <div class="grid-cell username-cell" title={user.username || user.name || 'Sin username'}>
                <span class="font-mono text-sm">{user.username || user.name || '—'}</span>
              </div>
              
              <!-- Nombre -->
              <div class="grid-cell name-cell">
                {user.name || '—'}
              </div>
              
              <!-- Rol -->
              <div class="grid-cell role-cell">
                <Badge variant={getRoleBadgeVariant(user.role)} size="sm">
                  {getRoleLabel(user.role)}
                </Badge>
              </div>
              
              <!-- Sucursal -->
              <div class="grid-cell sucursal-cell">
                <span class="sucursal-name" class:empty={!user.sucursal_id}>
                  {getSucursalName(user.sucursal_id)}
                </span>
              </div>
              
              <!-- Estado -->
              <div class="grid-cell status-cell">
                <Badge variant={getStatusBadgeVariant(user.is_active)} size="sm">
                  {user.is_active ? "Activo" : "Inactivo"}
                </Badge>
              </div>
              
              <!-- Último Login -->
              <div class="grid-cell date-cell">
                {formatDate(user.last_login)}
              </div>
              
              <!-- Creado -->
              <div class="grid-cell date-cell">
                {formatDate(user.created_at)}
              </div>
              
              <!-- Acciones -->
              {#if canEdit}
                <div class="grid-cell actions-cell">
                  <div class="actions-group">
                    <Button
                      variant="brutalist"
                      on:click={() => {
                        selectedUser = user;
                        currentModalMode = "edit";
                        showEditModal = true;
                      }}
                    >
                      <Edit size={16} strokeWidth={1.5} style="display: inline-block; vertical-align: middle; margin-right: 4px;" />
                      Editar
                    </Button>
                    <Button
                      variant="brutalist"
                      on:click={() => {
                        selectedUser = user;
                        currentModalMode = "password";
                        showPasswordModal = true;
                      }}
                    >
                      <Key size={16} strokeWidth={1.5} style="display: inline-block; vertical-align: middle; margin-right: 4px;" />
                      Password
                    </Button>
                    {#if user.is_active}
                      <Button
                        variant="brutalist"
                        on:click={() => {
                          selectedUser = user;
                          currentModalMode = "deactivate";
                          showDeactivateModal = true;
                        }}
                      >
                        <Pause size={16} strokeWidth={1.5} style="display: inline-block; vertical-align: middle; margin-right: 4px;" />
                        Desactivar
                      </Button>
                    {:else}
                      <Button
                        variant="brutalist"
                        on:click={() => {
                          selectedUser = user;
                          handleActivate(user.id);
                        }}
                      >
                        <CheckCircle2 size={16} strokeWidth={1.5} style="display: inline-block; vertical-align: middle; margin-right: 4px;" />
                        Activar
                      </Button>
                    {/if}
                    <Button
                      variant="brutalist-danger"
                      on:click={() => {
                        selectedUser = user;
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

      <!-- Users cards (Mobile - Enhanced) -->
      <div class="users-cards">
        {#each $filteredUsers as user (user.id)}
          <div class="user-card">
            <div class="user-card-header">
              <h3 class="user-card-title">{user.name}</h3>
              <Badge variant={getRoleBadgeVariant(user.role)} size="sm">
                {getRoleLabel(user.role)}
              </Badge>
            </div>
            <div class="user-card-body">
              <div class="user-card-row">
                <span class="user-card-label">Username:</span>
                <span class="user-card-value font-mono">{user.username}</span>
              </div>
              <div class="user-card-row">
                <span class="user-card-label">Sucursal:</span>
                <span class="user-card-value sucursal-name">{getSucursalName(user.sucursal_id)}</span>
              </div>
              <div class="user-card-row">
                <span class="user-card-label">Estado:</span>
                <span class="status-badge {user.is_active ? 'active' : 'inactive'}">
                  {user.is_active ? "Activo" : "Inactivo"}
                </span>
              </div>
              <div class="user-card-row">
                <span class="user-card-label">Último Login:</span>
                <span class="user-card-value">{formatDate(user.last_login)}</span>
              </div>
              <div class="user-card-row">
                <span class="user-card-label">Creado:</span>
                <span class="user-card-value">{formatDate(user.created_at)}</span>
              </div>
            </div>
            {#if canEdit}
              <div class="user-card-actions">
                <Button
                  variant="brutalist"
                  on:click={() => {
                    selectedUser = user;
                    showEditModal = true;
                  }}
                >
                  <Edit size={16} strokeWidth={1.5} style="display: inline-block; vertical-align: middle; margin-right: 4px;" />
                  Editar
                </Button>
                <Button
                  variant="brutalist"
                  on:click={() => {
                    selectedUser = user;
                    showPasswordModal = true;
                  }}
                >
                  <Key size={16} strokeWidth={1.5} style="display: inline-block; vertical-align: middle; margin-right: 4px;" />
                  Cambiar Password
                </Button>
                {#if user.is_active}
                  <Button
                    variant="brutalist"
                    on:click={() => {
                      selectedUser = user;
                      showDeactivateModal = true;
                    }}
                  >
                    <Pause size={16} strokeWidth={1.5} style="display: inline-block; vertical-align: middle; margin-right: 4px;" />
                    Desactivar
                  </Button>
                {:else}
                  <Button
                    variant="brutalist"
                    on:click={() => {
                      selectedUser = user;
                      handleActivate(user.id);
                    }}
                  >
                    <CheckCircle2 size={16} strokeWidth={1.5} style="display: inline-block; vertical-align: middle; margin-right: 4px;" />
                    Activar
                  </Button>
                {/if}
                <Button
                  variant="brutalist-danger"
                  on:click={() => {
                    selectedUser = user;
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

      <!-- Pagination -->
      {#if $usersStore.pagination.hasMore}
        <div class="pagination">
          <Button
            variant="secondary"
            disabled={$usersStore.pagination.page === 1}
            on:click={() => fetchUsers($usersStore.pagination.page - 1)}
          >
            ← Anterior
          </Button>
          <span class="page-info">
            Página {$usersStore.pagination.page}
          </span>
          <Button
            variant="secondary"
            disabled={!$usersStore.pagination.hasMore}
            on:click={() => fetchUsers($usersStore.pagination.page + 1)}
          >
            Siguiente →
          </Button>
        </div>
      {/if}
    {/if}
    </div>

    <!-- Panel Access Selector - Vertical Sidebar (Mobile only) -->
    {#if canEdit && hasRole("super_admin")}
      <div class="panel-access-mobile">
        <PanelAccessSelector />
      </div>
    {/if}
  {/if}

  <!-- Modals -->
  {#if showCreateModal}
    <UserForm
      open={showCreateModal}
      mode="create"
      anchorPosition={createButtonPosition}
      on:close={() => {
        showCreateModal = false;
        createButtonPosition = null;
      }}
      on:created={handleUserCreated}
    />
  {/if}

  {#if showEditModal && selectedUser}
    <UserForm
      open={showEditModal}
      user={selectedUser}
      mode="edit"
      on:close={() => {
        showEditModal = false;
        selectedUser = null;
        currentModalMode = "create";
      }}
      on:updated={handleUserUpdated}
    />
  {/if}

  {#if showDeleteConfirm && selectedUser}
    <UserDeleteConfirm
      open={showDeleteConfirm}
      user={selectedUser}
      on:close={() => {
        showDeleteConfirm = false;
        selectedUser = null;
      }}
      on:deleted={handleUserDeleted}
    />
  {/if}

  {#if showPasswordModal && selectedUser}
    <UserForm
      open={showPasswordModal}
      user={selectedUser}
      mode="password"
      on:close={() => {
        showPasswordModal = false;
        selectedUser = null;
      }}
      on:passwordChanged={handleUserUpdated}
    />
  {/if}

  {#if showDeactivateModal && selectedUser}
    <UserForm
      open={showDeactivateModal}
      user={selectedUser}
      mode="deactivate"
      on:close={() => {
        showDeactivateModal = false;
        selectedUser = null;
      }}
      on:deactivated={handleUserUpdated}
    />
  {/if}
</div>

<style>
  .users-container {
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

  /* Panel Access Selector - Horizontal Top Bar (Desktop) */
  .panel-access-top {
    display: none; /* Hidden by default (mobile) */
  }

  /* Desktop: Show horizontal top bar */
  @media (min-width: 1200px) {
    .panel-access-top {
      display: block;
      position: sticky;
      top: 0;
      z-index: 100; /* High z-index to be on top */
      margin-bottom: var(--spacing-lg);
      background: var(--theme-bg-primary);
      padding-top: var(--spacing-md);
      padding-bottom: var(--spacing-md);
    }
  }

  /* Panel Access Selector - Vertical Sidebar (Mobile) */
  .panel-access-mobile {
    display: block;
    width: 100%;
    margin-bottom: var(--spacing-xl);
    margin-top: var(--spacing-xl);
  }

  /* Desktop: Hide mobile version */
  @media (min-width: 1200px) {
    .panel-access-mobile {
      display: none;
    }
  }

  .users-main {
    width: 100%;
    min-width: 0; /* Prevent grid overflow */
  }

  .users-header {
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

  .filters-section {
    display: flex;
    gap: var(--spacing-md);
    margin-bottom: var(--spacing-lg);
    flex-wrap: wrap;
  }

  .filter-group {
    flex: 1;
    min-width: 200px;
  }

  .search-input {
    width: 100%;
    padding: var(--spacing-md) var(--spacing-lg);
    border: 2px solid var(--border-primary);
    border-radius: var(--radius-lg);
    font-size: var(--text-base);
    background: var(--theme-bg-elevated);
    color: var(--text-primary);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
  }

  .search-input::placeholder {
    color: var(--text-muted);
    opacity: 0.7;
  }

  .search-input:focus {
    outline: none;
    border-color: var(--accent-primary);
    box-shadow: 0 0 0 4px rgba(0, 147, 247, 0.15), 0 4px 12px rgba(0, 147, 247, 0.1);
    transform: translateY(-1px);
  }

  .search-input:hover:not(:focus) {
    border-color: var(--border-secondary);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  }

  .role-select {
    width: 100%;
    padding: var(--spacing-md) var(--spacing-lg);
    border: 2px solid var(--border-primary);
    border-radius: var(--radius-lg);
    font-size: var(--text-base);
    background: var(--theme-bg-elevated);
    color: var(--text-primary);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    cursor: pointer;
    appearance: none;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%230093f7' d='M6 9L1 4h10z'/%3E%3C/svg%3E");
    background-repeat: no-repeat;
    background-position: right var(--spacing-md) center;
    padding-right: calc(var(--spacing-xl) + var(--spacing-md));
  }

  .role-select:focus {
    outline: none;
    border-color: var(--accent-primary);
    box-shadow: 0 0 0 4px rgba(0, 147, 247, 0.15), 0 4px 12px rgba(0, 147, 247, 0.1);
    transform: translateY(-1px);
  }

  .role-select:hover:not(:focus) {
    border-color: var(--border-secondary);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  }

  .empty-state {
    text-align: center;
    padding: var(--spacing-2xl);
    color: var(--text-muted);
  }

  /* FUTURE-PROOF CSS GRID PATTERN #1 - Zero alignment issues */
  .users-grid-container {
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
  .users-grid-container::before {
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

  /* Users Grid - Future-proof auto-responsive */
  /* Mobile: single column (will be hidden, cards shown instead) */
  .users-grid {
    display: grid;
    grid-template-columns: 1fr; /* Mobile: single column */
    gap: 0;
    width: 100%;
  }

  /* Desktop: Fixed 8-column grid for table-like layout */
  @media (min-width: 769px) {
    .users-grid {
      grid-template-columns: 1.2fr 1.5fr 1fr 1.2fr 0.9fr 1.3fr 1.4fr 2fr !important;
      gap: 0 !important;
    }
    
    /* Readonly modifier: 7 columns when canEdit=false */
    .users-grid.readonly {
      grid-template-columns: 1.2fr 1.5fr 1fr 1.2fr 0.9fr 1.3fr 1.4fr !important; /* 7 columns without Acciones */
    }
  }

  /* User Grid Item - CRITICAL: display: contents makes container transparent */
  /* On mobile, we need to override to show cards */
  .user-grid-item {
    display: contents; /* Default: transparent container for table-like layout */
  }

  /* Mobile: Override display: contents to show cards */
  @media (max-width: 768px) {
    .user-grid-item {
      display: block; /* Show as block for card layout on mobile */
      padding: var(--spacing-md);
      border-bottom: 1px solid var(--border-primary);
      background: var(--theme-bg-elevated);
      border-radius: var(--radius-lg);
      margin-bottom: var(--spacing-sm);
    }

    .user-grid-item:last-child {
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
      grid-template-columns: 1.2fr 1.5fr 1fr 1.2fr 0.9fr 1.3fr 1.4fr 2fr; /* 8 columns when canEdit */
      gap: 0;
      background: linear-gradient(135deg, var(--theme-bg-secondary) 0%, var(--theme-bg-elevated) 100%);
      border-bottom: 2px solid var(--border-primary);
      position: sticky;
      top: 0;
      z-index: 10;
    }
    
    /* Readonly modifier: 7 columns when canEdit=false (no Acciones column) */
    .grid-headers.readonly {
      grid-template-columns: 1.2fr 1.5fr 1fr 1.2fr 0.9fr 1.3fr 1.4fr; /* 7 columns without Acciones */
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

    /* Users grid - 8 columns on desktop when canEdit is true */
    /* CRITICAL: Fixed columns for table-like layout */
    .users-grid {
      grid-template-columns: 1.2fr 1.5fr 1fr 1.2fr 0.9fr 1.3fr 1.4fr 2fr; /* 8 columns - matches headers */
      gap: 0; /* No gaps to simulate table */
    }
    
    /* Readonly modifier: 7 columns when canEdit=false (no Acciones column) */
    .users-grid.readonly {
      grid-template-columns: 1.2fr 1.5fr 1fr 1.2fr 0.9fr 1.3fr 1.4fr; /* 7 columns without Acciones */
    }

    /* User grid item - display: contents makes it transparent */
    /* Cells align directly to parent grid */
    .user-grid-item {
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
    .user-grid-item:hover .grid-cell {
      background: linear-gradient(90deg, var(--theme-bg-secondary) 0%, transparent 100%);
      transform: translateY(-1px);
      box-shadow: 0 2px 8px rgba(0, 147, 247, 0.1);
    }

    /* Borde izquierdo aparece en hover */
    .user-grid-item:hover .grid-cell:first-child::before {
      opacity: 1;
    }

    /* Specific cell styling */
    .username-cell {
      font-family: 'Courier New', monospace;
      font-size: 0.875rem;
    }

    .sucursal-cell {
      font-size: 0.875rem;
    }

    .sucursal-name {
      color: var(--text-primary);
    }

    /* Style em dash for empty sucursal (muted color) */
    .sucursal-name.empty {
      color: var(--text-muted);
    }

    .date-cell {
      color: var(--text-muted);
      font-size: 0.875rem;
    }

    .sucursal-cell {
      font-size: 0.875rem;
    }

    .sucursal-name {
      color: var(--text-primary);
    }

    .sucursal-name.empty {
      color: var(--text-muted);
      font-style: italic;
    }

    .actions-cell {
      justify-content: flex-start;
      gap: 0.5rem;
      flex-wrap: wrap;
    }
  }

  /* Mobile: Hide grid, show cards */
  @media (max-width: 768px) {
    .users-grid-container {
      display: none !important; /* Hide grid on mobile */
    }

    .users-cards {
      display: grid !important;
      grid-template-columns: 1fr;
      gap: var(--spacing-md);
    }
  }

  /* Desktop: Hide cards, show grid - TABLE-LIKE LAYOUT */
  @media (min-width: 769px) {
    .users-grid-container {
      display: block !important; /* Show grid on desktop */
    }

    .users-cards {
      display: none !important; /* Hide cards on desktop */
    }

    /* Ensure grid is visible and properly structured */
    .users-grid {
      display: grid !important;
      grid-template-columns: 1.2fr 1.5fr 1fr 1.2fr 0.9fr 1.3fr 1.4fr 2fr !important;
      gap: 0 !important;
    }
    
    /* Readonly modifier override for desktop */
    .users-grid.readonly {
      grid-template-columns: 1.2fr 1.5fr 1fr 1.2fr 0.9fr 1.3fr 1.4fr !important; /* 7 columns without Acciones */
    }
  }

  .role-badge-base {
    display: inline-block;
    padding: var(--spacing-xs) var(--spacing-md);
    border-radius: 9999px;
    font-size: var(--text-xs);
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  [data-theme="dark"] .role-badge-base {
    opacity: 0.9;
  }

  .status-badge {
    display: inline-block;
    padding: var(--spacing-xs) var(--spacing-md);
    border-radius: 9999px;
    font-size: var(--text-xs);
    font-weight: 600;
    line-height: 1.3;
  }

  /* Desktop: Badges with better readability */
  @media (min-width: 769px) {
    .status-badge {
      padding: 0.375rem 0.625rem; /* 6px 10px - increased for readability */
      font-size: 0.75rem; /* 12px - increased from 11px */
      line-height: 1.3;
    }
  }

  .status-badge.active {
    background: rgba(61, 173, 9, 0.2);
    color: var(--accent-success);
  }

  [data-theme="dark"] .status-badge.active {
    background: rgba(61, 173, 9, 0.3);
  }

  .status-badge.inactive {
    background: rgba(211, 5, 84, 0.2);
    color: var(--accent-danger);
  }

  [data-theme="dark"] .status-badge.inactive {
    background: rgba(211, 5, 84, 0.3);
  }

  .actions-cell {
    white-space: nowrap;
    overflow: visible;
    position: relative;
  }

  /* Desktop: Ensure actions are fully visible */
  @media (min-width: 769px) {
    .actions-cell {
      overflow: visible;
      min-width: 0; /* No restrictive min-width - allow flexibility */
    }
  }

  .actions-group {
    display: flex;
    gap: 0.375rem; /* 6px - más compacto */
    flex-wrap: nowrap;
    align-items: center;
  }

  /* Desktop: Keep actions in a single row, more compact with tighter spacing */
  @media (min-width: 769px) {
    .actions-group {
      flex-wrap: wrap; /* Allow wrapping if needed */
      gap: 0.5rem; /* 8px - increased for better spacing */
    }

    /* Action buttons with better readability */
    .actions-group :global(button) {
      padding: 0.5rem 0.75rem; /* 8px vertical, 12px horizontal - increased for readability */
      font-size: 0.8125rem; /* 13px - increased from 12px */
      line-height: 1.3;
      min-height: auto;
      white-space: nowrap;
    }

    /* Icons in buttons */
    .actions-group :global(button) :global(svg) {
      width: 14px;
      height: 14px;
      margin-right: 0.375rem;
    }
  }

  /* Tablet: Allow wrapping if needed */
  @media (min-width: 481px) and (max-width: 768px) {
    .actions-group {
      flex-wrap: wrap;
    }
  }

  .pagination {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 1rem;
  }

  .date-cell {
    font-size: var(--text-sm);
    color: var(--text-muted);
    line-height: 1.4;
  }

  /* Desktop: Date cells with better readability */
  @media (min-width: 769px) {
    .date-cell {
      font-size: 0.875rem; /* 14px - increased from 13px */
      line-height: 1.4;
    }
  }

  .page-info {
    color: var(--text-secondary);
    font-weight: 500;
    font-size: var(--text-sm);
  }

  /* Mobile: Responsive adjustments */
  @media (max-width: 768px) {
    .users-container {
      padding: var(--spacing-md);
    }

    .users-header {
      flex-direction: column;
      align-items: stretch;
      gap: var(--spacing-md);
    }

    .page-title {
      font-size: var(--text-2xl);
      text-align: center;
    }

    .create-user-button-wrapper {
      width: 100%;
    }

    .create-user-button-wrapper :global(button) {
      width: 100%;
      min-height: 44px; /* Minimum touch target size for accessibility */
      justify-content: center;
    }

    .filters-section {
      flex-direction: column;
      gap: var(--spacing-sm);
      flex-wrap: nowrap;
    }

    .filter-group {
      min-width: 100%;
    }

    .filters-section :global(button) {
      width: 100%;
      min-height: 44px; /* Minimum touch target size for accessibility */
      justify-content: center;
    }

    .user-card {
      background: var(--theme-bg-elevated);
      border: 2px solid var(--border-primary);
      border-radius: var(--radius-xl);
      padding: var(--spacing-lg);
      box-shadow: var(--shadow-md);
      transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
      position: relative;
      overflow: hidden;
    }

    .user-card::before {
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

    .user-card:hover {
      transform: translateY(-2px);
      box-shadow: var(--shadow-lg);
      border-color: var(--accent-primary);
    }

    .user-card:hover::before {
      opacity: 1;
    }

    .user-card-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: var(--spacing-md);
      padding-bottom: var(--spacing-md);
      border-bottom: 1px solid var(--border-primary);
    }

    .user-card-title {
      font-family: var(--font-primary);
      font-size: var(--text-lg);
      font-weight: 700;
      color: var(--text-primary);
      margin: 0;
    }

    .user-card-body {
      display: flex;
      flex-direction: column;
      gap: var(--spacing-sm);
      margin-bottom: var(--spacing-md);
    }

    .user-card-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: var(--text-sm);
    }

    .user-card-label {
      color: var(--text-secondary);
      font-weight: 500;
    }

    .user-card-value {
      color: var(--text-primary);
    }

    .user-card-actions {
      display: flex;
      flex-direction: column;
      gap: var(--spacing-sm);
      margin-top: var(--spacing-md);
      padding-top: var(--spacing-md);
      border-top: 1px solid var(--border-primary);
    }

    .user-card-actions .btn {
      width: 100%;
      min-height: 48px;
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
    .create-user-button-wrapper :global(.btn-brutalist:hover),
    .filters-section :global(.btn-brutalist:hover),
    .user-card-actions :global(.btn-brutalist:hover),
    .user-card-actions :global(.btn-brutalist-danger:hover),
    .actions-group :global(.btn-brutalist:hover),
    .actions-group :global(.btn-brutalist-danger:hover) {
      transform: none;
    }

    .create-user-button-wrapper :global(.btn-brutalist:hover),
    .filters-section :global(.btn-brutalist:hover),
    .actions-group :global(.btn-brutalist:hover) {
      box-shadow: 3px 3px 0px 0px var(--accent-primary);
      border-width: 2px;
    }

    .user-card-actions :global(.btn-brutalist-danger:hover),
    .actions-group :global(.btn-brutalist-danger:hover) {
      box-shadow: 3px 3px 0px 0px var(--accent-danger);
      border-width: 2px;
    }

    .user-card:hover {
      transform: none;
    }
  }

  /* Desktop: Show table, hide cards */
  @media (min-width: 769px) {
    .users-cards {
      display: none;
    }

    .table-container {
      display: block;
    }
  }

  /* Tablet: Scrollable table */
  @media (min-width: 481px) and (max-width: 1023px) {
    .table-container {
      overflow-x: auto;
      -webkit-overflow-scrolling: touch;
    }

    .users-table {
      min-width: 800px;
    }
  }
</style>

