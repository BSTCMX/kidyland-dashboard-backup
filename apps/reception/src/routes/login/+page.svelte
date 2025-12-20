<script lang="ts">
  /**
   * Login page for reception app.
   */
  import { login, user } from "@kidyland/utils";
  import { goto } from "$app/navigation";
  import { Button, Input } from "@kidyland/ui";
  import { onMount } from "svelte";

  let username = "";
  let password = "";
  let loading = false;
  let error: string | null = null;

  onMount(() => {
    // Redirect if already logged in
    if ($user) {
      goto("/");
    }
  });

  async function handleLogin() {
    if (!username || !password) {
      error = "Por favor completa todos los campos";
      return;
    }

    try {
      loading = true;
      error = null;
      await login(username, password);
      goto("/");
    } catch (e: any) {
      error = e.message || "Error al iniciar sesión";
    } finally {
      loading = false;
    }
  }
</script>

<div class="min-h-screen flex items-center justify-center bg-gray-100">
  <div class="bg-white p-8 rounded-lg shadow-md w-full max-w-md">
    <h1 class="text-2xl font-bold mb-6 text-center">Iniciar Sesión - Recepción</h1>

    {#if error}
      <div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
        {error}
      </div>
    {/if}

    <form on:submit|preventDefault={handleLogin}>
      <Input
        label="Usuario"
        bind:value={username}
        required
        disabled={loading}
      />

      <Input
        label="Contraseña"
        type="password"
        bind:value={password}
        required
        disabled={loading}
      />

      <Button type="submit" disabled={loading} class="w-full">
        {loading ? "Iniciando sesión..." : "Iniciar Sesión"}
      </Button>
    </form>
  </div>
</div>
































