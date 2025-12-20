<script lang="ts">
  /**
   * Layout for kidibar app.
   */
  import { onMount } from "svelte";
  import { user, logout } from "@kidyland/utils";
  import { goto } from "$app/navigation";

  onMount(() => {
    // Redirect to login if not authenticated
    if (!$user) {
      goto("/login");
    }
  });
</script>

<nav class="bg-blue-600 text-white p-4 mb-4">
  <div class="container mx-auto flex justify-between items-center">
    <h1 class="text-xl font-bold">KidiBar</h1>
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

<style>
  :global(body) {
    margin: 0;
    padding: 0;
    font-family: var(--font-body, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif);
    background: var(--theme-bg-primary, #ffffff);
    color: var(--text-primary, #1e293b);
  }

  :global(*) {
    box-sizing: border-box;
  }

  /* Import CSS variables from admin app if available, or define defaults */
  :global(:root) {
    --theme-bg-primary: #ffffff;
    --theme-bg-secondary: #f8fafc;
    --theme-bg-elevated: #ffffff;
    --accent-primary: #0093f7;
    --accent-primary-hover: #0077cc;
    --accent-success: #3dad09;
    --accent-warning: #ffce00;
    --accent-danger: #d30554;
    --text-primary: #1e293b;
    --text-secondary: #475569;
    --text-muted: #94a3b8;
    --text-inverse: #ffffff;
    --border-primary: #e2e8f0;
    --font-primary: "Beam Visionary", system-ui, sans-serif;
    --font-secondary: "MLB Blue Jays Modern", -apple-system, sans-serif;
    --font-body: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    --text-xs: 12px;
    --text-sm: 14px;
    --text-base: 16px;
    --text-lg: 18px;
    --text-xl: 20px;
    --text-2xl: 24px;
    --text-3xl: 32px;
    --spacing-xs: 0.25rem;
    --spacing-sm: 0.5rem;
    --spacing-md: 1rem;
    --spacing-lg: 1.5rem;
    --spacing-xl: 2rem;
    --spacing-2xl: 3rem;
    --radius-sm: 0.375rem;
    --radius-md: 0.5rem;
    --radius-lg: 0.75rem;
    --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
    --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
  }

  :global([data-theme="dark"]) {
    --theme-bg-primary: #061338;
    --theme-bg-secondary: #0f1629;
    --theme-bg-elevated: #1a2035;
    --text-primary: #f8fafc;
    --text-secondary: #cbd5e1;
    --text-muted: #94a3b8;
    --border-primary: #334155;
  }
</style>





























