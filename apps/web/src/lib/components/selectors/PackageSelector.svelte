<script lang="ts">
  /**
   * PackageSelector component - Select a single package.
   * 
   * Displays available packages and allows selecting one.
   * Based on ProductSelector pattern, adapted for packages.
   */
  import { createEventDispatcher } from "svelte";
  import type { Package } from "@kidyland/shared/types";
  import { Button } from "@kidyland/ui";
  import { Package as PackageIcon } from "lucide-svelte";

  export let packages: Package[] = [];
  export let selectedPackageId: string = "";
  export let error: string | null = null;

  const dispatch = createEventDispatcher<{
    change: { packageId: string };
  }>();

  $: selectedPackage = packages.find((p) => p.id === selectedPackageId);

  function handlePackageChange(event: Event) {
    const target = event.target as HTMLSelectElement;
    selectedPackageId = target.value;
    dispatch("change", { packageId: selectedPackageId });
  }

  function formatPrice(cents: number): string {
    return `$${(cents / 100).toFixed(2)}`;
  }
</script>

<div class="package-selector">
  <div class="form-group">
    <label for="package-select" class="label">
      <PackageIcon size={16} strokeWidth={1.5} />
      Paquete <span class="required">*</span>
    </label>
    <select
      id="package-select"
      class="select"
      value={selectedPackageId}
      on:change={handlePackageChange}
      disabled={packages.length === 0}
    >
      <option value="">Selecciona un paquete</option>
      {#each packages as pkg}
        <option value={pkg.id}>
          {pkg.name} - {formatPrice(pkg.price_cents)}
        </option>
      {/each}
    </select>
  </div>

  {#if selectedPackage}
    <div class="package-details">
      {#if selectedPackage.description}
        <p class="description">{selectedPackage.description}</p>
      {/if}
      <div class="price">Precio: {formatPrice(selectedPackage.price_cents)}</div>
    </div>
  {/if}

  {#if error}
    <div class="error-message" role="alert">{error}</div>
  {/if}
</div>

<style>
  .package-selector {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-md);
  }

  .form-group {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-sm);
  }

  .label {
    display: flex;
    align-items: center;
    gap: var(--spacing-xs);
    font-size: var(--text-sm);
    font-weight: 600;
    color: var(--text-primary);
  }

  .required {
    color: #d30554;
  }

  .select {
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

  .select:focus {
    outline: none;
    border-color: var(--accent-primary);
    box-shadow: 0 0 0 3px rgba(0, 147, 247, 0.1);
  }

  .select:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .package-details {
    padding: var(--spacing-md);
    background: var(--theme-bg-secondary);
    border: 1px solid var(--border-secondary);
    border-radius: var(--radius-md);
  }

  .description {
    margin: 0 0 var(--spacing-sm) 0;
    color: var(--text-secondary);
    font-size: var(--text-sm);
  }

  .price {
    font-weight: 600;
    color: var(--accent-primary);
    font-size: var(--text-base);
  }

  .error-message {
    padding: var(--spacing-sm);
    background: rgba(211, 5, 84, 0.1);
    border: 1px solid rgba(211, 5, 84, 0.3);
    border-radius: var(--radius-sm);
    color: #d30554;
    font-size: var(--text-sm);
  }
</style>
