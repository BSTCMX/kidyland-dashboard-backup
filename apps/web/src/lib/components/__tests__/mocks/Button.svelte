<script lang="ts">
  export let variant: string = "primary";
  export let disabled: boolean = false;
  export let type: string = "button";
</script>

<button {type} {disabled} data-testid="button">
  <slot />
</button>





























