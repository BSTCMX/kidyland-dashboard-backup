<script lang="ts">
  /**
   * Services management page.
   * 
   * Displays service list with CRUD operations.
   */
  import { onMount } from "svelte";
  import { goto } from "$app/navigation";
  import { user, hasAccessSecure, canEditSecure } from "$lib/stores/auth";
  import ServiceList from "$lib/components/admin/ServiceList.svelte";

  onMount(() => {
    if (!$user || !hasAccessSecure("/admin")) {
      goto("/admin");
      return;
    }
  });
</script>

<ServiceList />

<!-- Styles handled by ServiceList component -->

