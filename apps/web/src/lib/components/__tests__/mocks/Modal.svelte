<script lang="ts">
  export let open = false;
</script>

{#if open}
  <div data-testid="modal">
    <slot />
  </div>
{/if}





























