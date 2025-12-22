<script lang="ts">
  /**
   * KidiBar layout - Main layout for KidiBar routes.
   * 
   * Provides navigation sidebar and theme toggle.
   * Accessible to kidibar, recepcion, admin_viewer, monitor roles.
   */
  import { onMount } from "svelte";
  import { goto } from "$app/navigation";
  import { user, hasAccessSecure, logout } from "$lib/stores/auth";
  import { resolvedTheme } from "$lib/stores/theme";
  import ThemeToggle from "$lib/components/shared/ThemeToggle.svelte";
  import Logo from "$lib/components/shared/Logo.svelte";
  import { page } from "$app/stores";
  import { ROLE_ROUTES } from "$lib/types";
  import type { UserRole } from "$lib/types";
  import { getNavLink } from "$lib/utils/navigation";

  // Reactive access check - computed once and reactive to user changes
  // Uses secure checks that verify token-store consistency
  $: canAccess = $user && hasAccessSecure("/kidibar");
  $: currentTheme = $resolvedTheme;
  $: currentPath = $page.url.pathname;

  // Local state
  let sidebarOpen = false;
  let showLogoutConfirm = false;

  function toggleSidebar() {
    sidebarOpen = !sidebarOpen;
  }

  function closeSidebar() {
    sidebarOpen = false;
  }
  
  function confirmLogout() {
    showLogoutConfirm = true;
  }
  
  function cancelLogout() {
    showLogoutConfirm = false;
  }
  
  function handleLogout() {
    showLogoutConfirm = false;
    logout();
  }

  onMount(() => {
    // Redirect if user doesn't have access (backup check)
    // Primary protection is reactive conditional rendering below
    // Uses secure checks that verify token-store consistency
    if (!$user || !hasAccessSecure("/kidibar")) {
      goto("/");
      return;
    }
  });

  import { 
    LayoutDashboard, 
    ShoppingBag, 
    Package, 
    FileText,
    LogOut,
    BarChart3
  } from "lucide-svelte";
  
  // Roles that have a main panel defined in ROLE_ROUTES
  // These roles can access other panels and need a button to return to their main panel
  const rolesWithMainPanel: UserRole[] = ["super_admin", "admin_viewer", "monitor", "recepcion", "kidibar"];
  
  // Reactive: determine if we should show return button and where to redirect
  $: userMainPanelRoute = $user?.role ? ROLE_ROUTES[$user.role as keyof typeof ROLE_ROUTES] : null;
  $: currentPanelBase = currentPath.startsWith("/kidibar") ? "/kidibar" : currentPath;
  $: showReturnButton = 
    $user && 
    userMainPanelRoute &&
    rolesWithMainPanel.includes($user.role as UserRole) &&
    userMainPanelRoute !== currentPanelBase;
  
  function handleReturnToMainPanel() {
    if (userMainPanelRoute) {
      goto(userMainPanelRoute);
    }
  }
  
  const kidibarNavItems = [
    { route: "/kidibar", label: "Dashboard", icon: LayoutDashboard },
    { route: "/kidibar/productos", label: "Productos", icon: ShoppingBag },
    { route: "/kidibar/paquetes", label: "Paquetes", icon: Package },
    { route: "/kidibar/ventas", label: "Historial", icon: FileText },
    { route: "/kidibar/reportes", label: "Reportes", icon: BarChart3 },
  ];
</script>

{#if !$user}
  <div class="loading-container">
    <p>Cargando...</p>
  </div>
{:else if !canAccess}
  <div class="error-container">
    <p>No tienes permisos para acceder a esta sección.</p>
  </div>
{:else}
  <div class="kidibar-layout">
    <!-- Mobile Overlay -->
    {#if sidebarOpen}
      <div
        class="sidebar-overlay"
        on:click={closeSidebar}
        on:keydown={(e) => e.key === "Escape" && closeSidebar()}
        role="button"
        tabindex="0"
      ></div>
    {/if}

    <!-- Sidebar -->
    <aside class="sidebar" class:open={sidebarOpen}>
      <!-- Actions absolute en esquina superior derecha -->
      <div class="sidebar-actions-absolute">
        <ThemeToggle />
        <button
          class="sidebar-close"
          on:click={closeSidebar}
          aria-label="Close sidebar"
          title="Cerrar menú"
        >
          ✕
        </button>
      </div>
      
      <div class="sidebar-header">
        <!-- Logo centrado arriba en espacio cuadrado -->
        <div class="sidebar-logo-container">
          <div class="logo-with-glow">
            <Logo size="md" variant="default" />
          </div>
        </div>
        
        <!-- Título centrado abajo del logo -->
        <h2 class="sidebar-title">KidiBar</h2>
      </div>

      <nav class="sidebar-nav">
        {#each kidibarNavItems as item}
          <a
            href={getNavLink(item.route, $page.url)}
            class="nav-link"
            class:active={currentPath === item.route || (item.route !== "/kidibar" && currentPath.startsWith(item.route))}
            on:click={closeSidebar}
          >
            <span class="nav-icon">
              <svelte:component this={item.icon} size={20} strokeWidth={1.5} />
            </span>
            <span class="nav-label">{item.label}</span>
          </a>
        {/each}
      </nav>
      
      <!-- User Section -->
      {#if $user}
        <div class="user-section">
          <div class="user-info">
            <div class="user-avatar">
              <span class="user-initial">{$user.name[0].toUpperCase()}</span>
            </div>
            <div class="user-details">
              <span class="user-name">{$user.name}</span>
              <span class="user-role">{$user.role.replace('_', ' ')}</span>
            </div>
          </div>
        </div>
      {/if}
      
      <!-- Return to Main Panel Button (for super_admin, admin_viewer, monitor) -->
      {#if showReturnButton && userMainPanelRoute}
        <div class="return-to-panel-section">
          <button 
            class="return-button" 
            on:click={handleReturnToMainPanel}
            aria-label="Volver a Panel Principal"
            title="Volver a Panel Principal"
          >
            <LayoutDashboard size={20} strokeWidth={1.5} />
            <span>Volver a Panel Principal</span>
          </button>
        </div>
      {/if}
      
      <!-- Logout Button en esquina inferior izquierda -->
      <div class="logout-section">
        <button 
          class="logout-button-bottom" 
          on:click={confirmLogout}
          aria-label="Cerrar sesión"
          title="Cerrar sesión"
        >
          <LogOut size={20} strokeWidth={1.5} />
          <span>Salir</span>
        </button>
      </div>
    </aside>

    <!-- Main Content -->
    <main class="main-content">
      <!-- Mobile Menu Button -->
      <button
        class="mobile-menu-button"
        on:click={toggleSidebar}
        aria-label="Toggle menu"
        title="Abrir menú"
      >
        ☰
      </button>
      <slot />
    </main>
  </div>
{/if}

<!-- Logout Confirmation Modal -->
{#if showLogoutConfirm}
  <div class="modal-overlay" on:click={cancelLogout} role="dialog" aria-modal="true">
    <div class="modal-content" on:click|stopPropagation>
      <div class="modal-header">
        <h3 class="modal-title">¿Cerrar sesión?</h3>
      </div>
      <div class="modal-body">
        <p>¿Estás seguro de que deseas cerrar sesión?</p>
      </div>
      <div class="modal-actions">
        <button class="btn-cancel" on:click={cancelLogout}>Cancelar</button>
        <button class="btn-confirm" on:click={handleLogout}>Cerrar sesión</button>
      </div>
    </div>
  </div>
{/if}

<style>
  .loading-container,
  .error-container {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 100vh;
    padding: var(--spacing-xl);
    text-align: center;
    font-size: var(--text-lg);
    color: var(--text-secondary);
  }

  .error-container {
    color: var(--accent-danger);
  }

  .kidibar-layout {
    display: flex;
    min-height: 100vh;
    background: var(--theme-bg-primary);
  }

  .sidebar {
    width: 280px;
    background: var(--theme-bg-elevated);
    border-right: 1px solid var(--border-primary);
    padding: 0;
    display: flex;
    flex-direction: column;
    position: sticky;
    top: 0;
    height: 100vh;
    overflow-y: auto;
    z-index: 100;
    transition: transform 0.3s ease;
  }
  
  /* Actions absolute en esquina - NO interfieren con layout */
  .sidebar-actions-absolute {
    position: absolute;
    top: 16px;
    right: 16px;
    display: flex;
    gap: 8px;
    align-items: center;
    z-index: 10;
  }

  .sidebar-header {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 72px 24px 24px 24px;
    border-bottom: 1px solid var(--border-primary);
  }
  
  /* Logo en espacio cuadrado (120px x 120px) */
  .sidebar-logo-container {
    width: 120px;
    height: 120px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 16px;
  }

  .sidebar-title {
    font-family: var(--font-primary);
    font-size: var(--text-xl);
    font-weight: 700;
    color: var(--text-primary);
    margin: 0;
    text-align: center;
    
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

  .sidebar-close {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 32px;
    height: 32px;
    background: var(--theme-bg-secondary);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-sm);
    color: var(--text-secondary);
    cursor: pointer;
    font-size: var(--text-lg);
    transition: all 0.2s ease;
  }

  .sidebar-close:hover {
    background: var(--theme-bg-primary);
    color: var(--text-primary);
    border-color: rgba(211, 5, 84, 0.5);
  }

  .sidebar-nav {
    flex: 1;
    padding: var(--spacing-md);
    overflow-y: auto;
  }

  .nav-link {
    display: flex;
    align-items: center;
    gap: var(--spacing-md);
    padding: var(--spacing-md);
    color: var(--text-secondary);
    text-decoration: none;
    border-radius: var(--radius-md);
    transition: all 0.2s ease;
    margin-bottom: var(--spacing-xs);
  }

  .nav-link:hover {
    background: var(--theme-bg-secondary);
    color: var(--text-primary);
  }

  .nav-link.active {
    background: var(--theme-bg-secondary);
    color: var(--accent-primary);
    font-weight: 600;
  }

  .nav-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 24px;
    height: 24px;
  }

  .nav-label {
    font-size: var(--text-base);
  }

  .user-section {
    padding: var(--spacing-md);
    border-top: 1px solid var(--border-primary);
  }

  .user-info {
    display: flex;
    align-items: center;
    gap: var(--spacing-md);
  }

  .user-avatar {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    background: linear-gradient(135deg, #d30554, #b00445);
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-weight: 600;
    font-size: var(--text-lg);
  }

  .user-details {
    display: flex;
    flex-direction: column;
    flex: 1;
  }

  .user-name {
    font-size: var(--text-sm);
    font-weight: 600;
    color: var(--text-primary);
  }

  .user-role {
    font-size: var(--text-xs);
    color: var(--text-secondary);
    text-transform: capitalize;
  }

  .return-to-panel-section {
    padding: var(--spacing-md);
    border-top: 1px solid var(--border-primary);
  }
  
  .return-button {
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: var(--spacing-sm);
    padding: var(--spacing-md);
    background: rgba(0, 147, 247, 0.1);
    border: 1px solid var(--accent-primary);
    border-radius: var(--radius-md);
    color: var(--accent-primary);
    font-weight: 600;
    font-size: var(--text-sm);
    cursor: pointer;
    transition: all 0.2s ease;
  }
  
  .return-button:hover {
    background: rgba(0, 147, 247, 0.2);
    border-color: var(--accent-primary);
    transform: translateY(-1px);
    box-shadow: 0 2px 8px rgba(0, 147, 247, 0.2);
  }
  
  .return-button:active {
    transform: translateY(0);
  }
  
  .logout-section {
    padding: var(--spacing-md);
    border-top: 1px solid var(--border-primary);
  }
  
  .logout-button-bottom {
    display: flex;
    align-items: center;
    gap: var(--spacing-md);
    width: 100%;
    padding: var(--spacing-md);
    background: var(--theme-bg-secondary);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
    cursor: pointer;
    color: var(--text-secondary);
    transition: all 0.2s ease;
    font-size: var(--text-base);
    font-weight: 500;
    min-height: 48px;
  }

  .logout-button-bottom:hover {
    background: var(--theme-bg-elevated);
    transform: translateY(-2px);
    border-color: rgba(211, 5, 84, 0.5);
    color: #d30554;
  }
  
  .logout-button-bottom span {
    flex: 1;
    text-align: left;
  }
  
  /* Modal de confirmación */
  .modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.7);
    backdrop-filter: blur(4px);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 10000;
    padding: var(--spacing-lg);
  }
  
  .modal-content {
    background: var(--theme-bg-elevated);
    border: 1px solid var(--border-primary);
    border-radius: 16px;
    max-width: 480px;
    width: 100%;
    padding: var(--spacing-xl);
    box-shadow: 
      0 20px 60px rgba(0, 0, 0, 0.4),
      0 0 0 1px rgba(0, 147, 247, 0.2);
  }
  
  .modal-header {
    margin-bottom: var(--spacing-lg);
  }
  
  .modal-title {
    font-family: var(--font-primary);
    font-size: var(--text-2xl);
    font-weight: 700;
    color: var(--text-primary);
    margin: 0;
  }
  
  .modal-body {
    margin-bottom: var(--spacing-xl);
  }
  
  .modal-body p {
    font-size: var(--text-lg);
    color: var(--text-secondary);
    line-height: 1.6;
    margin: 0;
  }
  
  .modal-actions {
    display: flex;
    gap: var(--spacing-md);
    justify-content: flex-end;
  }
  
  .btn-cancel,
  .btn-confirm {
    padding: 12px 24px;
    border-radius: 10px;
    font-weight: 600;
    font-size: 1rem;
    cursor: pointer;
    transition: all 0.2s ease;
    border: none;
  }
  
  .btn-cancel {
    background: var(--theme-bg-secondary);
    color: var(--text-primary);
    border: 1px solid var(--border-primary);
  }
  
  .btn-cancel:hover {
    background: var(--theme-bg-primary);
    transform: translateY(-2px);
  }
  
  .btn-confirm {
    background: linear-gradient(135deg, #d30554, #b00445);
    color: white;
    box-shadow: 
      0 4px 12px rgba(211, 5, 84, 0.3),
      0 0 20px rgba(211, 5, 84, 0.2);
  }
  
  .btn-confirm:hover {
    background: linear-gradient(135deg, #b00445, #8a0336);
    transform: translateY(-2px);
    box-shadow: 
      0 6px 16px rgba(211, 5, 84, 0.4),
      0 0 30px rgba(211, 5, 84, 0.3);
  }

  .main-content {
    flex: 1;
    padding: var(--spacing-xl);
    overflow-x: hidden;
  }

  .mobile-menu-button {
    display: none;
    position: fixed;
    top: var(--spacing-md);
    left: var(--spacing-md);
    z-index: 101;
    min-width: 48px;
    min-height: 48px;
    padding: var(--spacing-sm);
    background: var(--theme-bg-elevated);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
    cursor: pointer;
    font-size: var(--text-xl);
    transition: all 0.2s ease;
    color: var(--text-primary);
    box-shadow: var(--shadow-md);
    align-items: center;
    justify-content: center;
  }

  .mobile-menu-button:hover {
    background: var(--theme-bg-secondary);
    transform: scale(1.05);
  }

  .sidebar-overlay {
    display: none;
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    z-index: 99;
    backdrop-filter: blur(4px);
  }

  /* Mobile: Sidebar as drawer */
  @media (max-width: 768px) {
    .sidebar {
      position: fixed;
      left: 0;
      top: 0;
      transform: translateX(-100%);
      box-shadow: var(--shadow-xl);
      z-index: 100;
    }

    .sidebar.open {
      transform: translateX(0);
    }

    .sidebar-overlay {
      display: block;
    }

    .sidebar-close {
      display: block;
    }

    .mobile-menu-button {
      display: flex;
    }

    .main-content {
      padding: var(--spacing-md);
      padding-top: calc(var(--spacing-md) + 48px + var(--spacing-md));
    }

    .user-section {
      padding-top: var(--spacing-md);
      gap: var(--spacing-sm);
    }

    .user-name {
      font-size: var(--text-sm);
    }

    .user-role {
      font-size: var(--text-xs);
    }

    .logout-button-bottom {
      padding: var(--spacing-xs) var(--spacing-sm);
      font-size: var(--text-sm);
    }
  }

  /* Tablet and Desktop: Sidebar always visible */
  @media (min-width: 769px) {
    .sidebar {
      position: sticky;
      transform: translateX(0);
    }

    .sidebar-overlay {
      display: none;
    }

    .sidebar-close {
      display: none;
    }

    .mobile-menu-button {
      display: none;
    }

    .main-content {
      padding: var(--spacing-xl);
    }
  }

  /* Prevent hover transform issues on touch devices */
  @media (hover: none) and (pointer: coarse) {
    .logout-button-bottom:hover {
      transform: none;
    }
    
    .nav-link:hover {
      transform: none;
    }
  }
</style>

