<script lang="ts">
  /**
   * BackToPanelButton - Button to return to super_admin panel.
   * 
   * Displays a floating button in the corner to navigate back to admin dashboard.
   * Only visible for super_admin users.
   */
  import { goto } from "$app/navigation";
  import { user, hasRole } from "$lib/stores/auth";
  import { ArrowLeft } from "lucide-svelte";

  function handleBackToAdmin() {
    goto("/admin");
  }

  $: isSuperAdmin = hasRole("super_admin");
  $: showButton = isSuperAdmin && $user;
</script>

{#if showButton}
  <button
    class="back-to-panel-button"
    on:click={handleBackToAdmin}
    aria-label="Regresar a Panel Admin"
    title="Regresar a Panel Admin"
  >
    <ArrowLeft size={20} strokeWidth={2} />
    <span class="button-text">Admin</span>
  </button>
{/if}

<style>
  .back-to-panel-button {
    position: fixed;
    bottom: 2rem;
    right: 2rem;
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    padding: var(--spacing-md) var(--spacing-lg);
    background: var(--accent-primary);
    color: var(--text-inverse);
    border: none;
    border-radius: var(--radius-lg);
    box-shadow: 
      0 8px 24px rgba(0, 147, 247, 0.3),
      0 0 20px var(--glow-primary);
    cursor: pointer;
    font-weight: 600;
    font-size: var(--text-base);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    z-index: 1000;
    min-height: 48px;
    min-width: 48px;
  }

  .back-to-panel-button:hover {
    transform: translateY(-2px);
    box-shadow: 
      0 12px 32px rgba(0, 147, 247, 0.4),
      0 0 30px var(--glow-primary),
      0 0 40px var(--glow-secondary);
    background: var(--accent-primary-hover);
  }

  .back-to-panel-button:active {
    transform: translateY(0);
  }

  .button-text {
    display: inline-block;
  }

  @media (max-width: 768px) {
    .back-to-panel-button {
      bottom: 1rem;
      right: 1rem;
      padding: var(--spacing-sm) var(--spacing-md);
    }

    .button-text {
      display: none;
    }
  }
</style>
























