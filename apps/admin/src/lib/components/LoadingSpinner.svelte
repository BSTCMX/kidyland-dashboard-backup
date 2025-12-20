<script lang="ts">
  /**
   * LoadingSpinner component - Displays a loading spinner.
   */
  export let size: "sm" | "md" | "lg" = "md";
  export let message: string = "";

  $: sizeClasses = {
    sm: "w-4 h-4",
    md: "w-8 h-8",
    lg: "w-12 h-12",
  };
</script>

<div class="loading-spinner-container">
  <div class="spinner {sizeClasses[size]}" />
  {#if message}
    <p class="loading-message">{message}</p>
  {/if}
</div>

<style>
  .loading-spinner-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: var(--spacing-md);
    padding: var(--spacing-xl);
  }

  .spinner {
    border: 3px solid var(--border-primary);
    border-top-color: var(--accent-primary);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }

  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }

  .loading-message {
    color: var(--text-secondary);
    font-size: var(--text-sm);
    text-align: center;
  }
</style>


