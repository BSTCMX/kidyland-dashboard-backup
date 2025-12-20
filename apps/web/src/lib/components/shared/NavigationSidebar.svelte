<script lang="ts">
  /**
   * Navigation Sidebar - Dynamic navigation based on user permissions.
   * 
   * Shows only accessible modules with readonly indicators.
   */
  import { user, hasAccess, canEdit } from "$lib/stores/auth";
  import { getModulePermissions } from "$lib/utils/permissions";
  import { page } from "$app/stores";
  import { goto } from "$app/navigation";

  interface NavItem {
    route: string;
    label: string;
    icon: string;
    module: "admin" | "recepcion" | "kidibar" | "monitor";
  }

  const navItems: NavItem[] = [
    { route: "/admin", label: "Administración", icon: "⚙️", module: "admin" },
    { route: "/admin-viewer", label: "Visualización", icon: "👁️", module: "admin" },
    { route: "/recepcion", label: "Recepción", icon: "🎮", module: "recepcion" },
    { route: "/kidibar", label: "KidiBar", icon: "🍿", module: "kidibar" },
    { route: "/monitor", label: "Monitor", icon: "📺", module: "monitor" },
  ];

  // Filter items based on user role
  // super_admin sees all, admin_viewer sees admin-viewer + others, etc.
  $: filteredItems = navItems.filter((item) => {
    if (!$user) return false;
    
    // Special handling for admin vs admin-viewer
    if (item.route === "/admin" && $user.role === "admin_viewer") {
      return false; // admin_viewer should see admin-viewer, not admin
    }
    if (item.route === "/admin-viewer" && $user.role === "super_admin") {
      return true; // super_admin can see both
    }
    
    return hasAccess(item.route);
  });

  $: visibleItems = filteredItems;

  $: itemPermissions = (item: NavItem) => {
    if (!$user) return null;
    return getModulePermissions($user.role, item.module);
  };

  $: currentPath = $page.url.pathname;

  function handleNavClick(item: NavItem, event: MouseEvent) {
    event.preventDefault();
    goto(item.route);
  }
</script>

<nav class="sidebar">
  <div class="sidebar-header">
    <h2 class="sidebar-title">Navegación</h2>
  </div>

  <div class="sidebar-nav">
    {#each visibleItems as item}
      {@const perms = itemPermissions(item)}
      <a
        href={item.route}
        class="nav-item"
        class:active={currentPath.startsWith(item.route)}
        class:readonly={!perms?.canEdit}
        on:click={(e) => handleNavClick(item, e)}
      >
        <span class="nav-icon">{item.icon}</span>
        <span class="nav-label">{item.label}</span>
        {#if !perms?.canEdit}
          <span class="readonly-badge" title="Solo Lectura">👁️</span>
        {/if}
      </a>
    {/each}
  </div>
</nav>

<style>
  .sidebar {
    width: 280px;
    background: var(--theme-bg-elevated);
    border-right: 1px solid var(--border-primary);
    padding: var(--spacing-xl);
    display: flex;
    flex-direction: column;
    gap: var(--spacing-lg);
    min-height: 100vh;
  }

  .sidebar-header {
    margin-bottom: var(--spacing-md);
  }

  .sidebar-title {
    font-family: var(--font-primary);
    font-size: var(--text-xl);
    font-weight: 700;
    color: var(--text-primary);
    margin: 0;
  }

  .sidebar-nav {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-sm);
  }

  .nav-item {
    display: flex;
    align-items: center;
    gap: var(--spacing-md);
    padding: var(--spacing-md);
    color: var(--text-secondary);
    text-decoration: none;
    border-radius: var(--radius-md);
    transition: all 0.2s ease;
    font-size: var(--text-base);
    font-weight: 500;
    min-height: 48px;
    position: relative;
  }

  .nav-item:hover {
    background: var(--theme-bg-secondary);
    color: var(--text-primary);
  }

  .nav-item.active {
    background: var(--accent-primary);
    color: var(--text-inverse);
  }

  .nav-item.readonly {
    opacity: 0.85;
  }

  .nav-item.readonly:hover {
    background: rgba(255, 206, 0, 0.1);
  }

  .nav-icon {
    font-size: var(--text-xl);
    width: 24px;
    text-align: center;
  }

  .nav-label {
    flex: 1;
  }

  .readonly-badge {
    font-size: var(--text-sm);
    opacity: 0.7;
  }

  @media (max-width: 768px) {
    .sidebar {
      width: 100%;
      min-height: auto;
      padding: var(--spacing-md);
    }
  }
</style>

