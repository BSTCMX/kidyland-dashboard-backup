<script lang="ts">
  /**
   * Layout for reception app.
   */
  import { onMount } from "svelte";
  import { user, logout } from "@kidyland/utils";
  import { goto } from "$app/navigation";
  import { page } from "$app/stores";

  onMount(() => {
    // Redirect to login if not authenticated
    if (!$user) {
      goto("/login");
    }
  });
</script>

<nav class="bg-blue-600 text-white p-4 mb-4">
  <div class="container mx-auto flex justify-between items-center">
    <h1 class="text-xl font-bold">Recepción</h1>
    <div class="flex items-center gap-4">
      {#if $user}
        <span>{$user.name}</span>
        <button
          on:click={() => {
            logout();
            goto("/login");
          }}
          class="px-3 py-1 bg-blue-700 rounded hover:bg-blue-800"
        >
          Salir
        </button>
      {/if}
    </div>
  </div>
</nav>

<main>
  <slot />
</main>
































