<script lang="ts">
  /**
   * Tagline component - Displays a tagline or slogan.
   */
  export let text: string = "";
  export let variant: "default" | "large" = "default";
</script>

{#if text}
  <p class="tagline tagline-{variant}">
    {text}
  </p>
{/if}

<style>
  .tagline {
    color: var(--text-secondary);
    margin: 0;
    font-weight: 400;
  }

  .tagline-default {
    font-size: var(--text-sm);
  }

  .tagline-large {
    font-size: var(--text-base);
  }
</style>
