<script lang="ts">
  /**
   * Users management page.
   * 
   * Displays user list with filters, pagination, and CRUD operations.
   * Only accessible to super_admin.
   */
  import { onMount } from "svelte";
  import { goto } from "$app/navigation";
  import { user, hasAccessSecure, canEditSecure } from "$lib/stores/auth";
  import UserList from "$lib/components/admin/UserList.svelte";

  onMount(() => {
    // Verify user has access and can edit admin - uses secure checks that verify token-store consistency
    if (!$user || !hasAccessSecure("/admin") || !canEditSecure("admin")) {
      goto("/admin");
      return;
    }
  });
</script>

<UserList />




















