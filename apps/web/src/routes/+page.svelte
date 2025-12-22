<script lang="ts">
  /**
   * Login page - Root route for authentication.
   * 
   * Handles user login and redirects to appropriate dashboard based on role.
   */
  import { onMount } from "svelte";
  import { goto } from "$app/navigation";
  import { user, login, getRoleRoute } from "$lib/stores/auth";
  import { Button } from "@kidyland/ui";
  import AnimatedTitle from "$lib/components/shared/AnimatedTitle.svelte";
  import { Eye, EyeOff, LogIn } from "lucide-svelte";
  import InstallButton from "$lib/components/pwa/InstallButton.svelte";
  import "../app.css";
  import "$lib/styles/animations.css";
  import "$lib/styles/dashboard-theme.css";

  // Form state
  let username = "";
  let password = "";
  let showPassword = false;
  let loading = false;
  let error: string | null = null;

  // Redirect if already authenticated
  $: if ($user) {
    const roleRoute = getRoleRoute();
    if (roleRoute) {
      goto(roleRoute);
    }
  }

  async function handleSubmit(event: Event) {
    event.preventDefault();
    
    // Validate inputs
    if (!username.trim() || !password.trim()) {
      error = "Por favor, completa todos los campos";
      return;
    }

    loading = true;
    error = null;

    try {
      // Log in development for debugging
      if (import.meta.env.DEV) {
        console.log("[Login Page] Submitting form - username:", username.trim());
      }
      
      await login(username.trim(), password);
      
      // Redirect handled by login function
      if (import.meta.env.DEV) {
        console.debug("[Login Page] Login successful, redirecting...");
      }
    } catch (err: any) {
      // Enhanced error handling with logging
      const errorMessage = err.message || "Error al iniciar sesión. Verifica tus credenciales.";
      error = errorMessage;
      
      if (import.meta.env.DEV) {
        console.error("[Login Page] Login error:", {
          message: err.message,
          name: err.name,
          stack: err.stack
        });
      }
    } finally {
      loading = false;
    }
  }

  function togglePasswordVisibility() {
    showPassword = !showPassword;
  }
</script>

<div class="login-page">
  <div class="login-container">
    <div class="login-header">
      <AnimatedTitle text="Kidyland" size="md" />
      <p class="login-subtitle">Sistema de gestión</p>
    </div>

    <form on:submit={handleSubmit} class="login-form">
      {#if error}
        <div class="error-banner" role="alert">
          {error}
        </div>
      {/if}

      <div class="input-group">
        <label for="username" class="input-label">Usuario</label>
        <input
          id="username"
          type="text"
          bind:value={username}
          disabled={loading}
          placeholder="Ingresa tu usuario"
          required
          autocomplete="username"
          class="input"
        />
      </div>

             <div class="input-group">
               <label for="password" class="input-label">Contraseña</label>
               <div class="password-input-wrapper">
                 {#if showPassword}
                   <input
                     id="password"
                     type="text"
                     bind:value={password}
                     disabled={loading}
                     placeholder="Ingresa tu contraseña"
                     required
                     autocomplete="current-password"
                     class="input password-input"
                   />
                 {:else}
                   <input
                     id="password"
                     type="password"
                     bind:value={password}
                     disabled={loading}
                     placeholder="Ingresa tu contraseña"
                     required
                     autocomplete="current-password"
                     class="input password-input"
                   />
                 {/if}
                 <button
                   type="button"
                   on:click={togglePasswordVisibility}
                   class="password-toggle"
                   tabindex="-1"
                   aria-label={showPassword ? "Ocultar contraseña" : "Mostrar contraseña"}
                 >
                   {#if showPassword}
                     <EyeOff size={20} strokeWidth={1.5} />
                   {:else}
                     <Eye size={20} strokeWidth={1.5} />
                   {/if}
                 </button>
               </div>
             </div>

      <Button
        type="submit"
        variant="brutalist"
        disabled={loading}
        class="login-button"
      >
        {#if loading}
          <span class="spinner"></span>
          Iniciando sesión...
        {:else}
          <LogIn size={20} strokeWidth={1.5} />
          Iniciar Sesión
        {/if}
      </Button>
    </form>
  </div>
  
  <!-- PWA Install Button - Fixed position, bottom right -->
  <InstallButton fixed={true} />
</div>

<style>
  .login-page {
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: var(--spacing-xl);
    background: var(--theme-bg-primary);
  }

  .login-container {
    width: 100%;
    max-width: 420px;
    padding: var(--spacing-2xl);
    background: var(--theme-bg-card);
    backdrop-filter: blur(16px) saturate(150%);
    -webkit-backdrop-filter: blur(16px) saturate(150%);
    border: 1px solid var(--border-primary);
    border-radius: 24px;
    box-shadow: 
      0 8px 32px rgba(0, 0, 0, 0.15),
      0 0 20px var(--glow-primary);
    overflow: visible;
    position: relative;
  }

  .login-header {
    text-align: center;
    margin-bottom: var(--spacing-2xl);
    overflow: visible;
    position: relative;
  }

  /* AnimatedTitle component handles its own styling */

  .login-subtitle {
    font-size: var(--text-base);
    color: var(--text-secondary);
    margin: 0;
  }

  .login-form {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-lg);
  }

  .error-banner {
    padding: var(--spacing-md);
    background: rgba(211, 5, 84, 0.1);
    border: 1px solid rgba(211, 5, 84, 0.3);
    border-radius: var(--radius-md);
    color: #d30554;
    font-size: var(--text-sm);
  }

  .input-group {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-sm);
  }

  .input-label {
    font-size: var(--text-sm);
    font-weight: 600;
    color: var(--text-primary);
  }

  .input {
    width: 100%;
    padding: var(--spacing-md);
    font-size: var(--text-base);
    font-family: var(--font-primary);
    background: var(--theme-bg-secondary);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
    color: var(--text-primary);
    transition: all 0.2s ease;
  }

  .input:focus {
    outline: none;
    border-color: var(--accent-primary);
    box-shadow: 0 0 0 3px rgba(0, 147, 247, 0.1);
  }

  .input:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .password-input-wrapper {
    position: relative;
    display: flex;
    align-items: center;
  }

  .password-input {
    padding-right: 48px;
  }

  .password-toggle {
    position: absolute;
    right: var(--spacing-sm);
    background: none;
    border: none;
    color: var(--text-secondary);
    cursor: pointer;
    padding: var(--spacing-xs);
    display: flex;
    align-items: center;
    justify-content: center;
    transition: color 0.2s ease;
  }

  .password-toggle:hover {
    color: var(--text-primary);
  }

  .login-button {
    width: 100%;
    margin-top: var(--spacing-md);
  }

  .spinner {
    display: inline-block;
    width: 16px;
    height: 16px;
    border: 2px solid currentColor;
    border-top-color: transparent;
    border-radius: 50%;
    animation: spin 0.6s linear infinite;
  }

  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }

  @media (max-width: 480px) {
    .login-container {
      padding: var(--spacing-xl);
    }
  }
</style>
