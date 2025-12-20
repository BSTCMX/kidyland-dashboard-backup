<script lang="ts">
  /**
   * Packages admin page.
   */
  import { onMount } from "svelte";
  import { goto } from "$app/navigation";
  import { user, hasAccessSecure } from "$lib/stores/auth";
  import PackageList from "$lib/components/admin/PackageList.svelte";

  onMount(() => {
    // Verify user has access to admin
    if (!$user || !hasAccessSecure("/admin")) {
      goto("/");
      return;
    }
  });
</script>

<PackageList />




















