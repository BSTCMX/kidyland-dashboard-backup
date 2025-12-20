<script lang="ts">
  /**
   * ErrorBanner component - Displays error messages.
   */
  export let error: string | null = null;
  export let dismissible: boolean = true;

  let visible = true;

  $: if (error) {
    visible = true;
  }

  function handleDismiss() {
    visible = false;
  }
</script>

{#if error && visible}
  <div class="error-banner">
    <div class="error-content">
      <span class="error-icon">⚠️</span>
      <p class="error-message">{error}</p>
    </div>
    {#if dismissible}
      <button
        type="button"
        class="error-dismiss"
        on:click={handleDismiss}
        aria-label="Dismiss error"
      >
        ✕
      </button>
    {/if}
  </div>
{/if}

<style>
  .error-banner {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: var(--spacing-md);
    padding: var(--spacing-md) var(--spacing-lg);
    background: rgba(211, 5, 84, 0.1);
    border: 1px solid var(--accent-danger);
    border-radius: var(--radius-md);
    margin-bottom: var(--spacing-md);
  }

  [data-theme="dark"] .error-banner {
    background: rgba(211, 5, 84, 0.2);
  }

  .error-content {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    flex: 1;
  }

  .error-icon {
    font-size: var(--text-lg);
    flex-shrink: 0;
  }

  .error-message {
    color: var(--accent-danger);
    font-size: var(--text-sm);
    font-weight: 500;
    margin: 0;
  }

  .error-dismiss {
    background: none;
    border: none;
    color: var(--accent-danger);
    font-size: var(--text-lg);
    cursor: pointer;
    padding: var(--spacing-xs);
    line-height: 1;
    transition: opacity 0.2s ease;
    flex-shrink: 0;
  }

  .error-dismiss:hover {
    opacity: 0.7;
  }
</style>


