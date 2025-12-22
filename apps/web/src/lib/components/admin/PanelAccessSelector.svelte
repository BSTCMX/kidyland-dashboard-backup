<script lang="ts">
  /**
   * PanelAccessSelector component - Quick navigation to different panels.
   * 
   * Shows which panels each role can access and provides quick navigation buttons
   * for super_admin to test different modules.
   */
import { goto } from "$app/navigation";
  import { user, hasAccess, hasRole } from "$lib/stores/auth";
  import { ROLE_ROUTES } from "$lib/types";
  import { sucursalesAdminStore } from "$lib/stores/sucursales-admin";
  import SucursalSelector from "./SucursalSelector.svelte";
  import { 
    LayoutDashboard,
    ShoppingCart,
    UtensilsCrossed,
    Monitor,
    ArrowRight,
    CheckCircle2,
    XCircle
  } from "lucide-svelte";
  import { Button } from "@kidyland/ui";

  interface PanelInfo {
    route: string;
    label: string;
    icon: any;
    roles: string[];
    description: string;
  }

  const panels: PanelInfo[] = [
    {
      route: "/admin",
      label: "Administración",
      icon: LayoutDashboard,
      roles: ["super_admin"],
      description: "Gestión completa del sistema"
    },
    {
      route: "/admin-viewer",
      label: "Visualización",
      icon: LayoutDashboard,
      roles: ["super_admin", "admin_viewer"],
      description: "Vista de solo lectura"
    },
    {
      route: "/recepcion",
      label: "Recepción",
      icon: UtensilsCrossed,
      roles: ["super_admin", "admin_viewer", "recepcion", "monitor"],
      description: "Gestión de servicios y timers"
    },
    {
      route: "/kidibar",
      label: "KidiBar",
      icon: ShoppingCart,
      roles: ["super_admin", "admin_viewer", "recepcion", "kidibar", "monitor"],
      description: "Ventas de productos"
    },
    {
      route: "/monitor",
      label: "Monitor",
      icon: Monitor,
      roles: ["super_admin", "admin_viewer", "monitor"],
      description: "Visualización de timers activos"
    }
  ];

  function canAccessPanel(panel: PanelInfo): boolean {
    return hasAccess(panel.route);
  }

  function handlePanelClick(route: string) {
    // For super_admin accessing /monitor, add query param to indicate monitor context
    // This allows recepcion layout to show "Monitor" branding
    let targetRoute = route;
    let queryParams = new URLSearchParams();
    
    if (selectedSucursalId) {
      queryParams.set("sucursal_id", selectedSucursalId);
    }
    
    // If super_admin accesses /monitor, add view_as=monitor to preserve branding
    if (route === "/monitor" && hasRole("super_admin")) {
      queryParams.set("view_as", "monitor");
    }
    
    const queryString = queryParams.toString();
    const url = queryString ? `${targetRoute}?${queryString}` : targetRoute;
    
    goto(url);
  }

  function getRoleAccessInfo(panel: PanelInfo): { canAccess: boolean; roleList: string } {
    const canAccess = canAccessPanel(panel);
    const roleList = panel.roles.join(", ");
    return { canAccess, roleList };
  }

  // Filter out the current user's main panel from the list
  // e.g., super_admin shouldn't see /admin in the selector (it's their main panel)
  $: userMainPanelRoute = $user?.role ? ROLE_ROUTES[$user.role as keyof typeof ROLE_ROUTES] : null;
  $: filteredPanels = panels.filter(panel => panel.route !== userMainPanelRoute);
  
  // Sucursal selection for super_admin when accessing visualization panels
  // Starts empty - user must manually select a sucursal (same pattern as UserForm)
  let selectedSucursalId: string | null = null;
  
  // Handle sucursal selection - save to localStorage for persistence
  // Note: selectedSucursalId is updated automatically via bind:, we only need to persist it
  function handleSucursalSelect(sucursalId: string | null) {
    // Save to localStorage for persistence across panel navigations
    // The bind:selectedSucursalId already updates the variable, so we only persist here
    if (sucursalId) {
      localStorage.setItem("panel_access_selected_sucursal_id", sucursalId);
    } else {
      localStorage.removeItem("panel_access_selected_sucursal_id");
    }
  }
  
  // Reactive statement to persist to localStorage when selectedSucursalId changes via binding
  // This ensures localStorage stays in sync with the bound variable
  $: if (selectedSucursalId) {
    localStorage.setItem("panel_access_selected_sucursal_id", selectedSucursalId);
  } else {
    localStorage.removeItem("panel_access_selected_sucursal_id");
  }

  // Determine if a panel requires sucursal_id for super_admin
  // All panels except /admin require sucursal_id when accessed by super_admin
  function requiresSucursalForSuperAdmin(panelRoute: string): boolean {
    return hasRole("super_admin") && panelRoute !== "/admin";
  }

  // Reactive helper: Determine if panel button should be disabled
  // This reactive statement ensures the disabled state updates when selectedSucursalId changes
  // Disabled if super_admin and panel requires sucursal but none selected
  function isPanelButtonDisabled(panelRoute: string): boolean {
    return requiresSucursalForSuperAdmin(panelRoute) && !selectedSucursalId;
  }
  
  // Reactive variable that tracks if any panel button should be disabled
  // This ensures Svelte detects changes to selectedSucursalId and re-renders buttons
  $: hasSelectedSucursal = selectedSucursalId !== null;
</script>

  <div class="panel-access-selector">
  <div class="selector-header">
    <h3 class="selector-title">
      <LayoutDashboard size={20} />
      Acceso a Paneles
    </h3>
    <p class="selector-subtitle">
      Navegación rápida para probar diferentes módulos
    </p>
  </div>

  <!-- Sucursal Selector for super_admin -->
  {#if hasRole("super_admin")}
    <div class="sucursal-selector-wrapper">
      <SucursalSelector
        bind:selectedSucursalId
        onSelect={handleSucursalSelect}
        allowAll={false}
        persistToLocalStorage={false}
      />
    </div>
  {/if}

  <div class="panels-grid">
    {#each filteredPanels as panel (panel.route)}
      {@const accessInfo = getRoleAccessInfo(panel)}
      {@const Icon = panel.icon}
      
      <div class="panel-card" class:accessible={accessInfo.canAccess}>
        <div class="panel-card-header">
          <div class="panel-icon">
            <Icon size={24} />
          </div>
          <div class="panel-status">
            {#if accessInfo.canAccess}
              <CheckCircle2 size={16} class="status-icon accessible" />
            {:else}
              <XCircle size={16} class="status-icon restricted" />
            {/if}
          </div>
        </div>

        <div class="panel-card-body">
          <h4 class="panel-label">{panel.label}</h4>
          <p class="panel-description">{panel.description}</p>
          
          <div class="panel-roles">
            <span class="roles-label">Roles:</span>
            <span class="roles-list">{accessInfo.roleList}</span>
          </div>
        </div>

        <div class="panel-card-footer">
          {#if hasRole("super_admin")}
            <div class="panel-button-wrapper">
              <Button
                variant="brutalist"
                on:click={() => handlePanelClick(panel.route)}
                class="panel-button"
                disabled={requiresSucursalForSuperAdmin(panel.route) && !hasSelectedSucursal}
                title={requiresSucursalForSuperAdmin(panel.route) && !hasSelectedSucursal ? "Debes seleccionar una sucursal antes de acceder al panel" : ""}
              >
                Ir a Panel
                <ArrowRight size={16} />
              </Button>
              {#if requiresSucursalForSuperAdmin(panel.route) && !hasSelectedSucursal}
                <p class="panel-button-hint">Selecciona una sucursal primero</p>
              {/if}
            </div>
          {:else if accessInfo.canAccess}
            <Button
              variant="brutalist"
              on:click={() => handlePanelClick(panel.route)}
              class="panel-button"
            >
              Acceder
              <ArrowRight size={16} />
            </Button>
          {:else}
            <div class="no-access">
              Sin acceso
            </div>
          {/if}
        </div>
      </div>
    {/each}
  </div>
</div>

<style>
  .panel-access-selector {
    background: var(--theme-bg-card);
    backdrop-filter: blur(16px) saturate(150%);
    -webkit-backdrop-filter: blur(16px) saturate(150%);
    border: 1px solid var(--border-primary);
    border-radius: 16px;
    padding: var(--spacing-lg);
    height: fit-content;
    box-shadow: 
      0 8px 24px rgba(0, 0, 0, 0.15),
      0 0 20px var(--glow-primary),
      inset 0 1px 0 rgba(255, 255, 255, 0.05);
    width: 100%;
  }

  /* Desktop: Compact horizontal layout for top bar */
  @media (min-width: 1200px) {
    .panel-access-selector {
      padding: var(--spacing-md) var(--spacing-lg);
      border-radius: 12px;
      box-shadow: 
        0 4px 12px rgba(0, 0, 0, 0.1),
        0 0 10px var(--glow-primary),
        inset 0 1px 0 rgba(255, 255, 255, 0.05);
    }
  }

  .selector-header {
    margin-bottom: var(--spacing-lg);
    padding-bottom: var(--spacing-md);
    border-bottom: 2px solid var(--border-primary);
  }

  /* Desktop: Compact header for horizontal layout */
  @media (min-width: 1200px) {
    .selector-header {
      margin-bottom: var(--spacing-md);
      padding-bottom: var(--spacing-sm);
      border-bottom-width: 1px;
    }
  }

  .selector-title {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    font-size: var(--text-lg);
    font-weight: 700;
    color: var(--text-primary);
    margin: 0 0 var(--spacing-xs) 0;
    
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

  .selector-title svg {
    color: var(--accent-primary);
  }

  .selector-subtitle {
    font-size: var(--text-sm);
    color: var(--text-muted);
    margin: 0;
  }

  .panels-grid {
    display: grid;
    grid-template-columns: 1fr;
    gap: var(--spacing-md);
  }

  /* Desktop: Grid layout for consistent card sizes */
  @media (min-width: 1200px) {
    .panels-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: var(--spacing-md);
      overflow-x: visible;
    }
  }

  .panel-card {
    background: var(--theme-bg-card);
    backdrop-filter: blur(16px) saturate(150%);
    -webkit-backdrop-filter: blur(16px) saturate(150%);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-lg);
    padding: var(--spacing-md);
    box-shadow: 
      0 8px 24px rgba(0, 0, 0, 0.15),
      0 0 20px var(--glow-primary),
      inset 0 1px 0 rgba(255, 255, 255, 0.05);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    flex-shrink: 0; /* Prevent cards from shrinking in horizontal layout */
    position: relative;
    overflow: hidden;
  }

  /* Hover effect - Hybrid card10 + metric-card */
  .panel-card:hover {
    transform: translateY(-4px);
    border-color: rgba(0, 147, 247, 0.5);
    box-shadow: 
      0 20px 60px rgba(0, 0, 0, 0.3),
      0 0 30px var(--glow-primary),
      0 0 40px var(--glow-secondary),
      inset 0 1px 0 rgba(255, 255, 255, 0.1);
  }

  /* Desktop: Better space utilization - cards now have consistent sizes via grid */
  @media (min-width: 1200px) {
    .panel-card {
      min-width: auto;
      max-width: none;
      height: 100%; /* Ensure cards fill grid cell height consistently */
      padding: var(--spacing-md);
      border-width: 1px;
      border-radius: var(--radius-md);
      box-shadow: 
        0 4px 12px rgba(0, 0, 0, 0.1),
        0 0 10px var(--glow-primary),
        inset 0 1px 0 rgba(255, 255, 255, 0.05);
    }

    .panel-card:hover {
      transform: translateY(-2px);
      box-shadow: 
        0 12px 32px rgba(0, 0, 0, 0.2),
        0 0 20px var(--glow-primary),
        inset 0 1px 0 rgba(255, 255, 255, 0.1);
    }
  }

  .panel-card.accessible {
    border-color: var(--accent-success);
    background: rgba(61, 173, 9, 0.05);
  }

  .panel-card:not(.accessible) {
    opacity: 0.7;
  }

  .panel-card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--spacing-sm);
  }

  .panel-icon {
    width: 40px;
    height: 40px;
    border-radius: var(--radius-md);
    background: linear-gradient(135deg, var(--accent-primary), var(--accent-success));
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
  }

  /* Desktop: Smaller icon for horizontal layout */
  @media (min-width: 1200px) {
    .panel-icon {
      width: 32px;
      height: 32px;
    }

    .panel-icon svg {
      width: 18px;
      height: 18px;
    }
  }

  .panel-status {
    display: flex;
    align-items: center;
  }

  .status-icon.accessible {
    color: var(--accent-success);
  }

  .status-icon.restricted {
    color: var(--accent-danger);
  }

  .panel-card-body {
    margin-bottom: var(--spacing-md);
  }

  /* Desktop: Compact body for horizontal layout */
  @media (min-width: 1200px) {
    .panel-card-body {
      margin-bottom: var(--spacing-sm);
    }
  }

  .panel-label {
    font-size: var(--text-base);
    font-weight: 600;
    color: var(--text-primary);
    margin: 0 0 var(--spacing-xs) 0;
  }

  /* Desktop: Smaller label for horizontal layout */
  @media (min-width: 1200px) {
    .panel-label {
      font-size: var(--text-sm);
      margin: 0 0 0.25rem 0;
    }
  }

  .panel-description {
    font-size: var(--text-xs);
    color: var(--text-secondary);
    margin: 0 0 var(--spacing-sm) 0;
    line-height: 1.4;
  }

  /* Desktop: Hide description in horizontal layout to save space */
  @media (min-width: 1200px) {
    .panel-description {
      display: none;
    }
  }

  .panel-roles {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xs);
    font-size: var(--text-xs);
  }

  /* Desktop: Compact roles display for horizontal layout */
  @media (min-width: 1200px) {
    .panel-roles {
      font-size: 0.625rem; /* 10px */
      gap: 0.125rem;
      margin-bottom: var(--spacing-xs);
    }
  }

  .roles-label {
    color: var(--text-muted);
    font-weight: 500;
  }

  .roles-list {
    color: var(--text-secondary);
    font-family: monospace;
  }

  .panel-card-footer {
    display: flex;
    justify-content: flex-end;
  }

  .panel-button-wrapper {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    width: 100%;
    gap: var(--spacing-xs);
  }

  .panel-button {
    display: flex;
    align-items: center;
    gap: var(--spacing-xs);
    min-width: auto;
    padding: var(--spacing-sm) var(--spacing-md);
  }

  /* Desktop: Compact button for horizontal layout */
  @media (min-width: 1200px) {
    .panel-button-wrapper {
      width: 100%;
    }

    .panel-button {
      padding: 0.375rem 0.625rem; /* 6px 10px */
      font-size: 0.75rem; /* 12px */
      width: 100%;
      justify-content: center;
    }

    .panel-button svg {
      width: 12px;
      height: 12px;
    }

    .panel-button-hint {
      font-size: 0.625rem; /* 10px */
      text-align: center;
    }
  }

  .panel-button-hint {
    font-size: var(--text-xs);
    color: var(--accent-warning);
    margin: var(--spacing-xs) 0 0 0;
    font-weight: 500;
    text-align: center;
    width: 100%;
  }

  .no-access {
    font-size: var(--text-xs);
    color: var(--text-muted);
    font-style: italic;
    padding: var(--spacing-sm);
  }

  /* Mobile optimizations */
  @media (max-width: 768px) {
    .panel-access-selector {
      padding: var(--spacing-md);
      border-radius: 12px;
    }

    .selector-header {
      margin-bottom: var(--spacing-md);
      padding-bottom: var(--spacing-sm);
    }

    .selector-title {
      font-size: var(--text-base);
    }

    .selector-subtitle {
      font-size: var(--text-xs);
    }

    .panels-grid {
      gap: var(--spacing-sm);
    }

    .panel-card {
      padding: var(--spacing-sm) var(--spacing-md);
      border-radius: 12px;
    }

    .panel-icon {
      width: 36px;
      height: 36px;
    }

    .panel-label {
      font-size: var(--text-sm);
    }

    .panel-description {
      font-size: var(--text-xs);
    }

    .panel-button {
      width: 100%;
      justify-content: center;
      min-height: 44px; /* Touch target */
    }
  }

  /* Small mobile devices */
  @media (max-width: 480px) {
    .panel-access-selector {
      padding: var(--spacing-sm);
    }

    .panel-card {
      padding: var(--spacing-sm);
    }

    .panel-icon {
      width: 32px;
      height: 32px;
    }
  }

  /* Prevent hover transform issues on touch devices */
  @media (hover: none) and (pointer: coarse) {
    .panel-card:hover {
      transform: none;
      box-shadow: 
        0 8px 24px rgba(0, 0, 0, 0.15),
        0 0 20px var(--glow-primary),
        inset 0 1px 0 rgba(255, 255, 255, 0.05);
      border-color: var(--border-primary);
    }

    .panel-card.accessible:hover {
      border-color: var(--accent-success);
    }

    .panel-button:hover,
    .panel-card-footer :global(.btn-brutalist:hover) {
      transform: none;
      box-shadow: 3px 3px 0px 0px var(--accent-primary);
      border-width: 2px;
    }
  }

</style>

