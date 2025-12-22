<script lang="ts">
  /**
   * Monitor layout - Redirects all monitor routes to recepcion layout.
   * 
   * Monitor role now uses the recepcion layout which provides full navigation
   * (Dashboard, Servicios, Paquetes, Reportes) while maintaining "Monitor" branding.
   * 
   * This layout redirects all /monitor/* routes to /recepcion/* equivalents.
   * The recepcion layout already handles the "Monitor" branding when role is "monitor".
   */
  import { onMount } from "svelte";
  import { goto } from "$app/navigation";
  import { user, hasAccessSecure } from "$lib/stores/auth";
  import { page } from "$app/stores";

  onMount(() => {
    // Redirect if user doesn't have access
    if (!$user || !hasAccessSecure("/monitor")) {
      goto("/");
      return;
    }

    // Redirect both monitor role and super_admin to recepcion
    // This allows both to use the full recepcion layout with all navigation items
    // super_admin will see "Monitor" branding via query param
    const currentPath = $page.url.pathname;
    const searchParams = new URLSearchParams($page.url.search);
    
    // Add view_as=monitor for super_admin to preserve branding
    if ($user.role === "super_admin" && !searchParams.has("view_as")) {
      searchParams.set("view_as", "monitor");
    }
    
    const queryString = searchParams.toString() ? `?${searchParams.toString()}` : "";
    
    // Map monitor routes to recepcion routes
    if (currentPath === "/monitor") {
      goto(`/recepcion${queryString}`);
    } else if (currentPath === "/monitor/timers") {
      goto(`/recepcion/timers${queryString}`);
    } else if (currentPath.startsWith("/monitor/")) {
      // For any other /monitor/* route, redirect to /recepcion equivalent
      const subPath = currentPath.replace("/monitor", "/recepcion");
      goto(`${subPath}${queryString}`);
    }
  });
</script>

<!-- Redirecting to recepcion layout... -->
<div class="loading-container">
  <p>Redirigiendo...</p>
</div>

<style>
  .loading-container {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 100vh;
    padding: var(--spacing-xl);
    text-align: center;
    font-size: var(--text-lg);
    color: var(--text-secondary);
  }
</style>
