<script lang="ts">
  /**
   * Sucursales management page.
   * 
   * Displays sucursal list with CRUD operations.
   */
  import { onMount } from "svelte";
  import { goto } from "$app/navigation";
  import { user, hasAccessSecure, canEditSecure } from "$lib/stores/auth";
  import SucursalList from "$lib/components/admin/SucursalList.svelte";

  onMount(() => {
    if (!$user || !hasAccessSecure("/admin")) {
      goto("/admin");
      return;
    }
  });
</script>

<SucursalList />

<!-- Styles handled by SucursalList component -->

