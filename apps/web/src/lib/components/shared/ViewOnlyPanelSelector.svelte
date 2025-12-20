<script lang="ts">
  /**
   * ViewOnlyPanelSelector - Panel selector for read-only access.
   * 
   * Displays available panels that the user can view (read-only).
   * Used by admin_viewer, recepcion, and monitor roles.
   */
  import { goto } from "$app/navigation";
  import { user, hasAccess } from "$lib/stores/auth";
  import { getModulePermissions } from "$lib/utils/permissions";
  import { 
    LayoutDashboard, 
    Receipt, 
    ShoppingBag, 
    Eye,
    ArrowRight
  } from "lucide-svelte";

  interface PanelOption {
    name: string;
    route: string;
    icon: typeof LayoutDashboard;
    description: string;
  }

  $: availablePanels = getAvailablePanels();

  function getAvailablePanels(): PanelOption[] {
    if (!$user) return [];

    const panels: PanelOption[] = [];
    const currentRole = $user.role;

    // Admin Viewer: can view recepcion and kidibar only
    if (currentRole === "admin_viewer") {
      if (hasAccess("/recepcion")) {
        panels.push({
          name: "Recepción",
          route: "/recepcion",
          icon: Receipt,
          description: "Vista de recepción (solo lectura)"
        });
      }
      if (hasAccess("/kidibar")) {
        panels.push({
          name: "KidiBar",
          route: "/kidibar",
          icon: ShoppingBag,
          description: "Vista de KidiBar (solo lectura)"
        });
      }
    }

    // Recepción: can view kidibar only
    if (currentRole === "recepcion") {
      const kidibarPerms = getModulePermissions(currentRole, "kidibar");
      if (kidibarPerms?.canAccess) {
        panels.push({
          name: "KidiBar",
          route: "/kidibar",
          icon: ShoppingBag,
          description: "Vista de KidiBar (solo lectura)"
        });
      }
    }

    // Monitor: can view kidibar only (monitor IS recepcion, so no need to show recepcion panel)
    if (currentRole === "monitor") {
      const kidibarPerms = getModulePermissions(currentRole, "kidibar");
      
      if (kidibarPerms?.canAccess) {
        panels.push({
          name: "KidiBar",
          route: "/kidibar",
          icon: ShoppingBag,
          description: "Vista de KidiBar (solo lectura)"
        });
      }
    }

    return panels;
  }

  function handleNavigate(route: string) {
    goto(route);
  }
</script>

{#if availablePanels.length > 0}
  <div class="panel-selector">
    <div class="selector-header">
      <Eye size={20} strokeWidth={1.5} />
      <h3 class="selector-title">Paneles Disponibles</h3>
    </div>
    <div class="panels-grid">
      {#each availablePanels as panel}
        {@const Icon = panel.icon}
        <button
          class="panel-card"
          on:click={() => handleNavigate(panel.route)}
          aria-label={`Ir a ${panel.name}`}
        >
          <div class="panel-icon">
            <Icon size={24} strokeWidth={1.5} />
          </div>
          <div class="panel-content">
            <h4 class="panel-name">{panel.name}</h4>
            <p class="panel-description">{panel.description}</p>
          </div>
          <ArrowRight size={18} strokeWidth={2} class="panel-arrow" />
        </button>
      {/each}
    </div>
  </div>
{/if}

<style>
  .panel-selector {
    background: var(--theme-bg-card);
    backdrop-filter: blur(16px) saturate(150%);
    -webkit-backdrop-filter: blur(16px) saturate(150%);
    border: 1px solid var(--border-primary);
    border-radius: 16px;
    padding: var(--spacing-xl);
    box-shadow: 
      0 8px 24px rgba(0, 0, 0, 0.15),
      0 0 20px var(--glow-primary),
      inset 0 1px 0 rgba(255, 255, 255, 0.05);
    margin-bottom: var(--spacing-xl);
    width: 100%;
  }

  .selector-header {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    margin-bottom: var(--spacing-lg);
  }

  .selector-title {
    font-size: var(--text-lg);
    font-weight: 700;
    color: var(--text-primary);
    margin: 0;
  }

  .panels-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: var(--spacing-md);
  }

  .panel-card {
    display: flex;
    align-items: center;
    gap: var(--spacing-md);
    padding: var(--spacing-lg);
    background: var(--theme-bg-elevated);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
    cursor: pointer;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    text-align: left;
    min-height: 80px;
    width: 100%;
    touch-action: manipulation;
    -webkit-tap-highlight-color: transparent;
  }

  .panel-card:active {
    transform: scale(0.98);
  }

  .panel-card:hover {
    transform: translateY(-2px);
    border-color: var(--accent-primary);
    box-shadow: 
      0 8px 16px rgba(0, 0, 0, 0.1),
      0 0 20px var(--glow-primary);
  }

  .panel-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 48px;
    height: 48px;
    min-width: 48px;
    min-height: 48px;
    background: rgba(0, 147, 247, 0.1);
    border-radius: var(--radius-md);
    color: var(--accent-primary);
    flex-shrink: 0;
  }

  .panel-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xs);
    min-width: 0; /* Allows text truncation */
  }

  .panel-name {
    font-size: var(--text-base);
    font-weight: 600;
    color: var(--text-primary);
    margin: 0;
    line-height: 1.4;
  }

  .panel-description {
    font-size: var(--text-sm);
    color: var(--text-secondary);
    margin: 0;
    line-height: 1.4;
  }

  .panel-arrow {
    color: var(--text-secondary);
    flex-shrink: 0;
    transition: transform 0.2s ease;
    min-width: 18px;
  }

  .panel-card:hover .panel-arrow,
  .panel-card:focus .panel-arrow {
    transform: translateX(4px);
    color: var(--accent-primary);
  }

  /* Mobile optimizations */
  @media (max-width: 768px) {
    .panel-selector {
      padding: var(--spacing-md);
      border-radius: 12px;
      margin-bottom: var(--spacing-lg);
    }

    .selector-header {
      margin-bottom: var(--spacing-md);
    }

    .selector-title {
      font-size: var(--text-base);
    }

    .panels-grid {
      grid-template-columns: 1fr;
      gap: var(--spacing-sm);
    }

    .panel-card {
      min-height: 64px;
      padding: var(--spacing-md);
      gap: var(--spacing-sm);
      border-radius: 12px;
    }

    .panel-icon {
      width: 44px;
      height: 44px;
      min-width: 44px;
      min-height: 44px;
    }

    .panel-name {
      font-size: var(--text-sm);
    }

    .panel-description {
      font-size: var(--text-xs);
    }

    .panel-arrow {
      width: 16px;
      height: 16px;
    }
  }

  /* Small mobile devices */
  @media (max-width: 480px) {
    .panel-selector {
      padding: var(--spacing-sm);
    }

    .panel-card {
      min-height: 56px;
      padding: var(--spacing-sm) var(--spacing-md);
    }

    .panel-icon {
      width: 40px;
      height: 40px;
      min-width: 40px;
      min-height: 40px;
    }
  }
</style>

