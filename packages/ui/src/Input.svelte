<script lang="ts">
  /**
   * Input component with label and error support.
   * Accepts standard HTML input attributes via $$restProps.
   */
  export let value: string = "";
  export let placeholder: string = "";
  export let type: string = "text";
  export let label: string = "";
  export let error: string = "";
  export let disabled = false;
  export let required = false;
  // Common HTML input attributes
  export let id: string | undefined = undefined;
  export let min: string | number | undefined = undefined;
  export let max: string | number | undefined = undefined;
  export let step: string | number | undefined = undefined;
  let className: string = "";
  export { className as class };
  
  function handleInput(event: Event) {
    const target = event.target as HTMLInputElement;
    value = target.value;
  }
</script>

<div class="mb-4">
  {#if label}
    <label class="block text-sm font-medium text-gray-700 mb-1">
      {label}
      {#if required}
        <span class="text-red-500">*</span>
      {/if}
    </label>
  {/if}
  
  <input
    {...$$restProps}
    type={type}
    {value}
    {placeholder}
    {disabled}
    {required}
    {id}
    {min}
    {max}
    {step}
    on:input={handleInput}
    class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed {className}"
    class:border-red-500={!!error}
  />
  
  {#if error}
    <p class="mt-1 text-sm text-red-600">{error}</p>
  {/if}
</div>




