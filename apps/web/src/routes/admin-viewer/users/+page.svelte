<script lang="ts">
  /**
   * Users management page (Read-only).
   * 
   * Displays user list with filters, pagination.
   * Only accessible to admin_viewer and super_admin.
   * Read-only: No create/edit/delete buttons.
   */
  import { onMount } from "svelte";
  import { goto } from "$app/navigation";
  import { user, hasAccessSecure } from "$lib/stores/auth";
  import UserList from "$lib/components/admin/UserList.svelte";

  onMount(() => {
    // Verify user has access to admin-viewer
    if (!$user || !hasAccessSecure("/admin-viewer")) {
      goto("/admin-viewer");
      return;
    }
  });
</script>

<UserList />




















