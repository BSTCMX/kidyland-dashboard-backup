<script lang="ts">
  /**
   * Products management page.
   * 
   * Displays product list with CRUD operations.
   */
  import { onMount } from "svelte";
  import { goto } from "$app/navigation";
  import { user, hasAccessSecure } from "$lib/stores/auth";
  import ProductList from "$lib/components/admin/ProductList.svelte";

  onMount(() => {
    if (!$user || !hasAccessSecure("/admin")) {
      goto("/admin");
      return;
    }
  });
</script>

<ProductList />

<!-- Styles handled by ProductList component -->

