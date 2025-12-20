<script lang="ts">
  /**
   * FloatingInput - Input con floating labels estilo moderno
   * Adaptado del estilo proporcionado, manteniendo Clean Architecture
   */
  export let value: string = "";
  export let placeholder: string = "";
  export let type: string = "text";
  export let label: string = "";
  export let error: string = "";
  export let disabled = false;
  export let required = false;
  export let id: string | undefined = undefined;
  
  let className: string = "";
  export { className as class };
  
  import { createEventDispatcher } from "svelte";
  
  const dispatch = createEventDispatcher();
  
  let inputId = id || `floating-input-${Math.random().toString(36).substr(2, 9)}`;
  let isFocused = false;
  let hasValue = false;
  
  $: hasValue = !!value;
  $: isFloating = isFocused || hasValue;
  
  function handleInput(event: Event) {
    const target = event.target as HTMLInputElement;
    value = target.value;
  }
  
  function handleFocus() {
    isFocused = true;
  }
  
  function handleBlur() {
    isFocused = false;
  }
</script>

<div class="input-container {className}" class:has-error={!!error}>
  <input
    {...$$restProps}
    {type}
    {value}
    {placeholder}
    {disabled}
    {required}
    id={inputId}
    on:input={handleInput}
    on:focus={handleFocus}
    on:blur={handleBlur}
    class="floating-input"
    class:error={!!error}
    class:disabled={disabled}
  />
  
  {#if label}
    <div class="cut" class:cut-short={label.length < 10}></div>
    <label for={inputId} class="placeholder" class:floating={isFloating}>
      {label}
      {#if required}
        <span class="required-asterisk">*</span>
      {/if}
    </label>
  {/if}
  
  {#if error}
    <p class="error-text">
      {error}
    </p>
  {/if}
</div>

<style>
  .input-container {
    height: 50px;
    position: relative;
    width: 100%;
    margin-bottom: var(--spacing-md);
  }

  .floating-input {
    background-color: var(--input-bg, #303245);
    border-radius: 12px;
    border: 0;
    box-sizing: border-box;
    color: var(--text-primary, #eee);
    font-size: 18px;
    height: 100%;
    outline: 0;
    padding: 4px 20px 0;
    width: 100%;
    font-family: var(--font-body, sans-serif);
    transition: all 0.2s ease;
  }

  .floating-input:focus {
    background-color: var(--input-bg-focus, #3a3d52);
  }

  .floating-input.error {
    border: 2px solid var(--accent-danger, #dc2f55);
  }

  .floating-input.disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .cut {
    background-color: var(--theme-bg-elevated, #15172b);
    border-radius: 10px;
    height: 20px;
    left: 20px;
    position: absolute;
    top: -20px;
    transform: translateY(0);
    transition: transform 200ms;
    width: 76px;
  }

  .cut-short {
    width: 50px;
  }

  /* Solo aplicar transform si NO hay error */
  .input-container:not(.has-error) .floating-input:focus ~ .cut,
  .input-container:not(.has-error) .floating-input:not(:placeholder-shown) ~ .cut,
  .input-container:not(.has-error) .floating-input:not([value=""]) ~ .cut {
    transform: translateY(8px);
  }

  /* Ocultar cut cuando hay error */
  .input-container.has-error .cut,
  .input-container.has-error .floating-input:focus ~ .cut,
  .input-container.has-error .floating-input:not(:placeholder-shown) ~ .cut,
  .input-container.has-error .floating-input:not([value=""]) ~ .cut {
    display: none !important;
    opacity: 0 !important;
    visibility: hidden !important;
    pointer-events: none !important;
    background-color: transparent !important;
    height: 0 !important;
    width: 0 !important;
    overflow: hidden !important;
    transform: none !important;
  }

  .placeholder {
    color: var(--text-muted, #65657b);
    font-family: var(--font-body, sans-serif);
    left: 20px;
    line-height: 14px;
    pointer-events: none;
    position: absolute;
    transform-origin: 0 50%;
    transition: transform 200ms, color 200ms;
    top: 20px;
    font-size: 18px;
  }

  .placeholder.floating,
  .floating-input:focus ~ .placeholder,
  .floating-input:not(:placeholder-shown) ~ .placeholder,
  .floating-input:not([value=""]) ~ .placeholder {
    transform: translateY(-30px) translateX(10px) scale(0.75);
  }

  .floating-input:not(:placeholder-shown) ~ .placeholder {
    color: var(--text-secondary, #808097);
  }

  .floating-input:focus ~ .placeholder {
    color: var(--accent-primary, #dc2f55);
  }

  .required-asterisk {
    color: var(--accent-danger, #dc2f55);
    margin-left: 2px;
  }

  .error-text {
    margin-top: var(--spacing-xs);
    font-size: var(--text-sm);
    color: var(--accent-danger, #dc2f55);
    padding-left: 4px;
    margin-bottom: 0;
  }

  /* Asegurar que el error-text no se superponga con el placeholder */
  .input-container.has-error .placeholder {
    transform: translateY(-30px) translateX(10px) scale(0.75);
  }

  /* Dark theme adjustments */
  [data-theme="dark"] .floating-input {
    background-color: #303245;
  }

  [data-theme="dark"] .floating-input:focus {
    background-color: #3a3d52;
  }

  [data-theme="dark"] .cut {
    background-color: var(--theme-bg-elevated);
  }
</style>

