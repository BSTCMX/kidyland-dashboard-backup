<script lang="ts">
  /**
   * Root layout for admin app.
   * 
   * Imports global styles and sets up theme.
   */
  import "../app.css";
  import { onMount } from "svelte";
  import { resolvedTheme } from "$lib/stores/theme";

  // Apply theme on mount
  onMount(() => {
    // Theme is already applied by theme store, but ensure it's set
    $resolvedTheme;
  });
</script>

<slot />


