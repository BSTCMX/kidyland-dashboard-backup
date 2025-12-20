<script lang="ts">
  /**
   * Root layout with role-based routing.
   * 
   * Handles authentication and automatic redirect based on user role.
   */
  import { onMount } from "svelte";
  import { goto } from "$app/navigation";
  import { page } from "$app/stores";
  import { user, getRoleRoute, hasAccess } from "$lib/stores/auth";
  import { ROLE_ROUTES } from "$lib/types";
  import ToastNotification from "$lib/components/shared/ToastNotification.svelte";
  import "../app.css";
  import "$lib/styles/animations.css";
  import "$lib/styles/dashboard-theme.css";

  // Public routes that don't require authentication
  const publicRoutes = ["/"];

  // Check if current route is public
  $: isPublicRoute = publicRoutes.includes($page.url.pathname);

  // Check if user is authenticated
  $: isAuthenticated = $user !== null;

  // Get current user's role route
  $: userRoleRoute = isAuthenticated ? getRoleRoute() : null;

  onMount(() => {
    // Allow access to public routes (login) even if user exists in localStorage
    // The login page will handle its own redirect logic if user is already authenticated
    if (!isAuthenticated && !isPublicRoute) {
      goto("/");
      return;
    }

    // Only redirect authenticated users away from login if they're already on a protected route
    // This prevents blocking access to the login page
    if (isAuthenticated && userRoleRoute) {
      const currentPath = $page.url.pathname;
      
      // If user is on root (login page), redirect to their role route
      // The login page component will handle redirect if needed via reactive statement
      if (currentPath === "/") {
        goto(userRoleRoute);
        return;
      }

      // Clean Architecture: Check access permissions first (single source of truth)
      // This allows superadmin and other roles with cross-panel access to navigate freely
      // Superadmin should have access to all panels (admin, admin-viewer, recepcion, kidibar, monitor)
      if (!hasAccess(currentPath)) {
        // User doesn't have access to this route, redirect to their default role route
        const userRole = $user?.role;
        if (userRole) {
          const allowedRoute = ROLE_ROUTES[userRole as keyof typeof ROLE_ROUTES];
          if (allowedRoute) {
            goto(allowedRoute);
          }
        }
        return;
      }

      // For non-superadmin roles: verify route matches their default role route
      // This prevents regular users from accessing routes outside their default panel
      // But allows access if routePermissions explicitly allow it (checked above)
      const userRole = $user?.role;
      if (userRole && userRole !== "super_admin") {
        const roleRoutes = Object.values(ROLE_ROUTES);
        const isOnRoleRoute = roleRoutes.some((route) => currentPath.startsWith(route));
        
        // If user is not on any role route and doesn't have explicit permission, redirect
        // Note: hasAccess() already checked above, so this is just for non-standard routes
        if (!isOnRoleRoute && !currentPath.startsWith(userRoleRoute)) {
          goto(userRoleRoute);
          return;
        }
      }
    }
  });
</script>

<slot />

<!-- Global Toast Notifications -->
<ToastNotification />

<style>
  :global(body) {
    margin: 0;
    padding: 0;
    font-family: var(--font-body, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif);
    background: var(--theme-bg-primary, #ffffff);
    color: var(--text-primary, #1e293b);
  }

  :global(*) {
    box-sizing: border-box;
  }

  /* CSS Variables - Kidyland Branding Global */
  :global(:root) {
    /* Background Colors */
    --theme-bg-primary: #ffffff;
    --theme-bg-secondary: #f8fafc;
    --theme-bg-elevated: #ffffff;
    --theme-bg-overlay: rgba(0, 0, 0, 0.5);

    /* Accent Colors - Kidyland */
    --kidyland-blue: #0093f7;
    --kidyland-green: #3dad09;
    --kidyland-pink: #d30554;
    --kidyland-yellow: #ffce00;

    --accent-primary: var(--kidyland-blue);
    --accent-primary-hover: #0077cc;
    --accent-success: var(--kidyland-green);
    --accent-success-hover: #2d8a07;
    --accent-warning: var(--kidyland-yellow);
    --accent-warning-hover: #e6b800;
    --accent-danger: var(--kidyland-pink);
    --accent-danger-hover: #b00445;

    /* Text Colors */
    --text-primary: #1e293b;
    --text-secondary: #475569;
    --text-muted: #94a3b8;
    --text-inverse: #ffffff;

    /* Border Colors */
    --border-primary: #e2e8f0;
    --border-secondary: #cbd5e1;

    /* Typography - Kidyland Branding */
    --font-primary: "Orbitron", "Beam Visionary", system-ui, sans-serif;
    --font-secondary: "Orbitron", "MLB Blue Jays Modern", -apple-system, sans-serif;
    --font-body: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;

    /* Font Sizes */
    --text-xs: 12px;
    --text-sm: 14px;
    --text-base: 16px;
    --text-lg: 18px;
    --text-xl: 20px;
    --text-2xl: 24px;
    --text-3xl: 32px;
    --text-4xl: 40px;

    /* Spacing */
    --spacing-xs: 0.25rem;
    --spacing-sm: 0.5rem;
    --spacing-md: 1rem;
    --spacing-lg: 1.5rem;
    --spacing-xl: 2rem;
    --spacing-2xl: 3rem;

    /* Border Radius */
    --radius-sm: 0.375rem;
    --radius-md: 0.5rem;
    --radius-lg: 0.75rem;
    --radius-xl: 1rem;

    /* Shadows */
    --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
    --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1);

    /* Touch Targets */
    --touch-target-min: 48px;
    --button-height: 56px;
  }

  /* Light Mode - Con buen contraste (por defecto) */
  :global(:root) {
    --theme-bg-card: rgba(255, 255, 255, 0.98);
    --glow-primary: rgba(0, 147, 247, 0.2);
    --glow-secondary: rgba(211, 5, 84, 0.15);
    --glow-success: rgba(61, 173, 9, 0.2);
    
    /* Texto oscuro para contraste en light mode */
    --text-primary: #0f172a;
    --text-secondary: #475569;
    --text-muted: #64748b;
    
    /* Input backgrounds para light mode */
    --input-bg: #ffffff;
    --input-bg-focus: #f8fafc;
  }
  
  /* Dark Mode - Consistente con Login */
  :global([data-theme="dark"]) {
    --theme-bg-primary: #0f172a;
    --theme-bg-secondary: #1e293b;
    --theme-bg-elevated: #1e293b;
    --theme-bg-overlay: rgba(0, 0, 0, 0.7);
    --theme-bg-card: rgba(30, 41, 59, 0.95);

    --text-primary: rgba(248, 250, 252, 0.98);
    --text-secondary: rgba(203, 213, 225, 0.95);
    --text-muted: rgba(148, 163, 184, 0.8);
    --text-inverse: #f8fafc;

    --border-primary: rgba(0, 147, 247, 0.3);
    --border-secondary: rgba(71, 85, 105, 0.6);
    
    /* Input backgrounds para dark mode */
    --input-bg: #303245;
    --input-bg-focus: #3a3d52;
    
    /* Glow effects - Kidyland colors */
    --glow-primary: rgba(0, 147, 247, 0.3);
    --glow-secondary: rgba(211, 5, 84, 0.2);
    --glow-success: rgba(61, 173, 9, 0.3);
  }
</style>

