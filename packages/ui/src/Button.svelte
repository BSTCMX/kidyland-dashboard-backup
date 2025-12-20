<script lang="ts">
  /**
   * Button component with customizable styles.
   */
  export let type: "button" | "submit" | "reset" = "button";
  export let variant: "primary" | "secondary" | "danger" | "brutalist" | "brutalist-danger" = "primary";
  export let disabled = false;
  let className: string = "";
  export { className as class };
  
  $: variantClasses = {
    primary: "bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500",
    secondary: "bg-gray-200 text-gray-800 hover:bg-gray-300 focus:ring-gray-500",
    danger: "bg-red-600 text-white hover:bg-red-700 focus:ring-red-500",
    brutalist: "btn-brutalist",
    "brutalist-danger": "btn-brutalist-danger",
  };
  
  $: isBrutalist = variant === "brutalist" || variant === "brutalist-danger";
</script>

<button
  {...$$restProps}
  type={type}
  disabled={disabled}
  class="{isBrutalist ? variantClasses[variant] : 'px-4 py-2 rounded font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed ' + variantClasses[variant]} {className}"
  on:click
>
  <slot />
</button>




