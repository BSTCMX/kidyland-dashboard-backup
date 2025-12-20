<script lang="ts">
  /**
   * Services view page (Read-only).
   * 
   * Displays service list in read-only mode for admin_viewer role.
   */
  import { onMount } from "svelte";
  import { goto } from "$app/navigation";
  import { user, hasAccessSecure } from "$lib/stores/auth";
  import ServiceList from "$lib/components/admin/ServiceList.svelte";

  onMount(() => {
    if (!$user || !hasAccessSecure("/admin-viewer")) {
      goto("/admin-viewer");
      return;
    }
  });
</script>

<ServiceList />











