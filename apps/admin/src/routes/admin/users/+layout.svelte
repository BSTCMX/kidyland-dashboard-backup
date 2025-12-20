<script lang="ts">
  /**
   * Layout for admin users section.
   * 
   * Provides sidebar navigation and theme toggle.
   */
  import { onMount } from "svelte";
  import { goto } from "$app/navigation";
  import { hasAnyRole } from "@kidyland/utils/auth";
  import { user } from "@kidyland/utils/auth";
  import { themeStore, resolvedTheme, toggleTheme } from "$lib/stores/theme";

  $: canAccess = hasAnyRole(["super_admin", "admin_viewer"]);
  $: currentTheme = $resolvedTheme;

  // Local state
  let sidebarOpen = false;

  function toggleSidebar() {
    sidebarOpen = !sidebarOpen;
  }

  function closeSidebar() {
    sidebarOpen = false;
  }

  onMount(() => {
    if (!$user) {
      goto("/login");
    } else if (!canAccess) {
      goto("/");
    }
  });
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
  <div class="admin-layout">
    <!-- Mobile Overlay -->
    {#if sidebarOpen}
      <div class="sidebar-overlay" on:click={closeSidebar} on:keydown={(e) => e.key === 'Escape' && closeSidebar()} role="button" tabindex="0"></div>
    {/if}

    <!-- Sidebar -->
    <aside class="sidebar" class:open={sidebarOpen}>
      <div class="sidebar-header">
        <h2 class="sidebar-title">👥 Usuarios</h2>
        <div class="sidebar-header-actions">
          <button
            class="theme-toggle"
            on:click={toggleTheme}
            aria-label="Toggle theme"
            title="Cambiar tema"
          >
            {#if currentTheme === "dark"}
              ☀️
            {:else}
              🌙
            {/if}
          </button>
          <button
            class="sidebar-close"
            on:click={closeSidebar}
            aria-label="Close sidebar"
            title="Cerrar menú"
          >
            ✕
          </button>
        </div>
      </div>

      <nav class="sidebar-nav">
        <a href="/admin/users" class="nav-link" data-active="true" on:click={closeSidebar}>
          📋 Lista de Usuarios
        </a>
        <a href="/" class="nav-link" on:click={closeSidebar}>
          ← Volver al Dashboard
        </a>
      </nav>
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

  .admin-layout {
    display: flex;
    min-height: 100vh;
    background: var(--theme-bg-primary);
  }

  .sidebar {
    width: 280px;
    background: var(--theme-bg-elevated);
    border-right: 1px solid var(--border-primary);
    padding: var(--spacing-xl);
    display: flex;
    flex-direction: column;
    gap: var(--spacing-lg);
    position: sticky;
    top: 0;
    height: 100vh;
    overflow-y: auto;
    z-index: 100;
    transition: transform 0.3s ease;
  }

  .sidebar-header-actions {
    display: flex;
    gap: var(--spacing-sm);
    align-items: center;
  }

  .sidebar-close {
    display: none;
    min-width: 48px;
    min-height: 48px;
    padding: var(--spacing-sm);
    background: var(--theme-bg-secondary);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
    cursor: pointer;
    font-size: var(--text-lg);
    transition: all 0.2s ease;
    color: var(--text-primary);
  }

  .sidebar-close:hover {
    background: var(--theme-bg-elevated);
    transform: scale(1.05);
  }

  .sidebar-overlay {
    display: none;
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: var(--theme-bg-overlay);
    z-index: 99;
    backdrop-filter: blur(4px);
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
  }

  .mobile-menu-button:hover {
    background: var(--theme-bg-secondary);
    transform: scale(1.05);
  }

  .main-content {
    flex: 1;
    padding: var(--spacing-xl);
    overflow-x: hidden;
  }

  .sidebar-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--spacing-md);
  }

  .sidebar-title {
    font-family: var(--font-primary);
    font-size: var(--text-xl);
    font-weight: 700;
    color: var(--text-primary);
    margin: 0;
  }

  .theme-toggle {
    min-width: 48px;
    min-height: 48px;
    padding: var(--spacing-sm);
    background: var(--theme-bg-secondary);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
    cursor: pointer;
    font-size: var(--text-lg);
    transition: all 0.2s ease;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .theme-toggle:hover {
    background: var(--theme-bg-elevated);
    transform: scale(1.05);
  }

  .sidebar-nav {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-sm);
  }

  .nav-link {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    padding: var(--spacing-md);
    color: var(--text-secondary);
    text-decoration: none;
    border-radius: var(--radius-md);
    transition: all 0.2s ease;
    font-size: var(--text-base);
    font-weight: 500;
    min-height: 48px;
  }

  .nav-link:hover {
    background: var(--theme-bg-secondary);
    color: var(--text-primary);
  }

  .nav-link[data-active="true"] {
    background: var(--accent-primary);
    color: var(--text-inverse);
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
      display: block;
    }

    .main-content {
      padding: var(--spacing-md);
      padding-top: calc(var(--spacing-md) + 48px + var(--spacing-md));
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
</style>


