<script lang="ts">
  /**
   * Products view page (Read-only).
   * 
   * Displays product list in read-only mode for admin_viewer role.
   */
  import { onMount } from "svelte";
  import { goto } from "$app/navigation";
  import { user, hasAccessSecure } from "$lib/stores/auth";
  import ProductList from "$lib/components/admin/ProductList.svelte";

  onMount(() => {
    if (!$user || !hasAccessSecure("/admin-viewer")) {
      goto("/admin-viewer");
      return;
    }
  });
</script>

<ProductList />




















