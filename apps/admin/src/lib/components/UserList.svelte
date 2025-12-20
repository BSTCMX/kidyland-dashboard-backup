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
  import { hasRole, hasAnyRole } from "@kidyland/utils/auth";
  import { user } from "@kidyland/utils/auth";
  import UserForm from "./UserForm.svelte";
  import UserDeleteConfirm from "./UserDeleteConfirm.svelte";
  import UserChangePasswordModal from "./UserChangePasswordModal.svelte";
  import LoadingSpinner from "./LoadingSpinner.svelte";
  import ErrorBanner from "./ErrorBanner.svelte";

  // Reactive stores
  $: currentUser = $user;
  $: canEdit = hasRole("super_admin");
  $: canView = hasAnyRole(["super_admin", "admin_viewer"]);

  // Local state
  let searchInput = "";
  let roleFilter: "all" | User["role"] = "all";
  let selectedUser: User | null = null;
  let showCreateModal = false;
  let showEditModal = false;
  let showDeleteConfirm = false;
  let showPasswordModal = false;
  let showDeactivateConfirm = false;

  // Load users on mount
  onMount(() => {
    if (canView) {
      fetchUsers();
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

  function getRoleBadgeClass(role: User["role"]): string {
    // Use CSS variables for consistent theming
    return "role-badge-base";
  }

  function getRoleBadgeStyle(role: User["role"]): string {
    const styles: Record<User["role"], string> = {
      super_admin: "background: rgba(147, 51, 234, 0.2); color: #a855f7;",
      admin_viewer: "background: rgba(0, 147, 247, 0.2); color: var(--accent-primary);",
      recepcion: "background: rgba(61, 173, 9, 0.2); color: var(--accent-success);",
      kidibar: "background: rgba(255, 206, 0, 0.2); color: var(--accent-warning);",
      monitor: "background: rgba(148, 163, 184, 0.2); color: var(--text-muted);",
    };
    return styles[role] || styles.monitor;
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
      showDeactivateConfirm = false;
      selectedUser = null;
      await fetchUsers($usersStore.pagination.page);
    }
  }

  async function handleUserCreated() {
    showCreateModal = false;
    await fetchUsers($usersStore.pagination.page);
  }

  async function handleUserUpdated() {
    showEditModal = false;
    selectedUser = null;
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
</script>

<div class="users-container">
  {#if !canView}
    <div class="error-banner">
      No tienes permisos para ver usuarios.
    </div>
  {:else}
    <!-- Header with filters -->
    <div class="users-header">
      <h1 class="page-title">👥 Gestión de Usuarios</h1>
      
      {#if canEdit}
        <Button on:click={() => (showCreateModal = true)}>
          ➕ Crear Usuario
        </Button>
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
      
      <Button variant="secondary" on:click={handleClearFilters}>
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
      <!-- Users table (Desktop) -->
      <div class="table-container">
        <table class="users-table">
          <thead>
            <tr>
              <th>Username</th>
              <th>Nombre</th>
              <th>Rol</th>
              <th>Estado</th>
              <th>Último Login</th>
              <th>Creado</th>
              {#if canEdit}
                <th>Acciones</th>
              {/if}
            </tr>
          </thead>
          <tbody>
            {#each $filteredUsers as user (user.id)}
              <tr>
                <td class="font-mono text-sm">{user.username}</td>
                <td>{user.name}</td>
                <td>
                  <span
                    class="role-badge {getRoleBadgeClass(user.role)}"
                    style={getRoleBadgeStyle(user.role)}
                  >
                    {getRoleLabel(user.role)}
                  </span>
                </td>
                <td>
                  <span class="status-badge {user.is_active ? 'active' : 'inactive'}">
                    {user.is_active ? "Activo" : "Inactivo"}
                  </span>
                </td>
                <td class="date-cell">
                  {formatDate(user.last_login)}
                </td>
                <td class="date-cell">
                  {formatDate(user.created_at)}
                </td>
                {#if canEdit}
                  <td class="actions-cell">
                    <div class="actions-group">
                      <Button
                        variant="secondary"
                        on:click={() => {
                          selectedUser = user;
                          showEditModal = true;
                        }}
                      >
                        ✏️ Editar
                      </Button>
                      <Button
                        variant="secondary"
                        on:click={() => {
                          selectedUser = user;
                          showPasswordModal = true;
                        }}
                      >
                        🔑 Password
                      </Button>
                      {#if user.is_active}
                        <Button
                          variant="secondary"
                          on:click={() => {
                            selectedUser = user;
                            showDeactivateConfirm = true;
                          }}
                        >
                          ⏸️ Desactivar
                        </Button>
                      {:else}
                        <Button
                          variant="secondary"
                          on:click={() => {
                            selectedUser = user;
                            handleActivate(user.id);
                          }}
                        >
                          ▶️ Activar
                        </Button>
                      {/if}
                      <Button
                        variant="danger"
                        on:click={() => {
                          selectedUser = user;
                          showDeleteConfirm = true;
                        }}
                      >
                        🗑️ Eliminar
                      </Button>
                    </div>
                  </td>
                {/if}
              </tr>
            {/each}
          </tbody>
        </table>
      </div>

      <!-- Users cards (Mobile) -->
      <div class="users-cards">
        {#each $filteredUsers as user (user.id)}
          <div class="user-card">
            <div class="user-card-header">
              <h3 class="user-card-title">{user.name}</h3>
              <span
                class="role-badge {getRoleBadgeClass(user.role)}"
                style={getRoleBadgeStyle(user.role)}
              >
                {getRoleLabel(user.role)}
              </span>
            </div>
            <div class="user-card-body">
              <div class="user-card-row">
                <span class="user-card-label">Username:</span>
                <span class="user-card-value font-mono">{user.username}</span>
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
                  variant="secondary"
                  on:click={() => {
                    selectedUser = user;
                    showEditModal = true;
                  }}
                >
                  ✏️ Editar
                </Button>
                <Button
                  variant="secondary"
                  on:click={() => {
                    selectedUser = user;
                    showPasswordModal = true;
                  }}
                >
                  🔑 Cambiar Password
                </Button>
                {#if user.is_active}
                  <Button
                    variant="secondary"
                    on:click={() => {
                      selectedUser = user;
                      showDeactivateConfirm = true;
                    }}
                  >
                    ⏸️ Desactivar
                  </Button>
                {:else}
                  <Button
                    variant="secondary"
                    on:click={() => {
                      selectedUser = user;
                      handleActivate(user.id);
                    }}
                  >
                    ▶️ Activar
                  </Button>
                {/if}
                <Button
                  variant="danger"
                  on:click={() => {
                    selectedUser = user;
                    showDeleteConfirm = true;
                  }}
                >
                  🗑️ Eliminar
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
  {/if}

  <!-- Modals -->
  {#if showCreateModal}
    <UserForm
      open={showCreateModal}
      on:close={() => (showCreateModal = false)}
      on:created={handleUserCreated}
    />
  {/if}

  {#if showEditModal && selectedUser}
    <UserForm
      open={showEditModal}
      user={selectedUser}
      on:close={() => {
        showEditModal = false;
        selectedUser = null;
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
    <UserChangePasswordModal
      open={showPasswordModal}
      user={selectedUser}
      on:close={() => {
        showPasswordModal = false;
        selectedUser = null;
      }}
      on:changed={handlePasswordChanged}
    />
  {/if}

  {#if showDeactivateConfirm && selectedUser}
    <UserDeleteConfirm
      open={showDeactivateConfirm}
      user={selectedUser}
      action="deactivate"
      on:close={() => {
        showDeactivateConfirm = false;
        selectedUser = null;
      }}
      on:deleted={() => handleDeactivate(selectedUser!.id)}
    />
  {/if}
</div>

<style>
  .users-container {
    padding: var(--spacing-xl);
    max-width: 1400px;
    margin: 0 auto;
    background: var(--theme-bg-primary);
    min-height: 100vh;
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
    padding: var(--spacing-sm) var(--spacing-md);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
    font-size: var(--text-base);
    background: var(--theme-bg-elevated);
    color: var(--text-primary);
    transition: border-color 0.2s ease;
  }

  .search-input:focus {
    outline: none;
    border-color: var(--accent-primary);
    box-shadow: 0 0 0 3px rgba(0, 147, 247, 0.1);
  }

  .role-select {
    width: 100%;
    padding: var(--spacing-sm) var(--spacing-md);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
    font-size: var(--text-base);
    background: var(--theme-bg-elevated);
    color: var(--text-primary);
    transition: border-color 0.2s ease;
  }

  .role-select:focus {
    outline: none;
    border-color: var(--accent-primary);
    box-shadow: 0 0 0 3px rgba(0, 147, 247, 0.1);
  }

  .empty-state {
    text-align: center;
    padding: var(--spacing-2xl);
    color: var(--text-muted);
  }

  .table-container {
    overflow-x: auto;
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-lg);
    margin-bottom: var(--spacing-lg);
    background: var(--theme-bg-elevated);
    box-shadow: var(--shadow-sm);
  }

  .users-table {
    width: 100%;
    border-collapse: collapse;
    background: transparent;
  }

  .users-table thead {
    background: var(--theme-bg-secondary);
  }

  .users-table th {
    padding: var(--spacing-md);
    text-align: left;
    font-weight: 600;
    font-size: var(--text-sm);
    color: var(--text-secondary);
    border-bottom: 2px solid var(--border-primary);
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .users-table td {
    padding: var(--spacing-md);
    border-bottom: 1px solid var(--border-primary);
    color: var(--text-primary);
  }

  .users-table tbody tr:hover {
    background: var(--theme-bg-secondary);
  }

  .users-table tbody tr:last-child td {
    border-bottom: none;
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
  }

  .actions-group {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
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
  }

  .page-info {
    color: var(--text-secondary);
    font-weight: 500;
    font-size: var(--text-sm);
  }

  /* Mobile: Convert table to cards */
  @media (max-width: 768px) {
    .users-container {
      padding: var(--spacing-md);
    }

    .users-header {
      flex-direction: column;
      align-items: stretch;
    }

    .filters-section {
      flex-direction: column;
    }

    .filter-group {
      min-width: 100%;
    }

    /* Hide table on mobile, show cards instead */
    .table-container {
      display: none;
    }

    .users-cards {
      display: grid;
      grid-template-columns: 1fr;
      gap: var(--spacing-md);
    }

    .user-card {
      background: var(--theme-bg-elevated);
      border: 1px solid var(--border-primary);
      border-radius: var(--radius-lg);
      padding: var(--spacing-lg);
      box-shadow: var(--shadow-sm);
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
    }

    .actions-group .btn {
      width: 100%;
      min-height: 48px;
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

