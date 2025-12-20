<script lang="ts">
  /**
   * ServiceSelector component - Select service and duration.
   * 
   * Displays available services and allows selection of service and duration.
   */
  import type { Service } from "@kidyland/shared/types";

  export let selectedServiceId: string = "";
  export let selectedDuration: number = 0;
  export let services: Service[] = [];
  export let error: string | null = null;

  $: availableDurations = selectedServiceId
    ? services.find((s) => s.id === selectedServiceId)?.durations_allowed || []
    : [];

  $: selectedService = services.find((s) => s.id === selectedServiceId);

  function handleServiceChange(event: Event) {
    const target = event.target as HTMLSelectElement;
    selectedServiceId = target.value;
    selectedDuration = 0; // Reset duration when service changes
  }

  function handleDurationChange(event: Event) {
    const target = event.target as HTMLSelectElement;
    selectedDuration = parseInt(target.value, 10);
  }

  function formatDuration(minutes: number): string {
    if (minutes < 60) {
      return `${minutes} min`;
    }
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    if (mins === 0) {
      return `${hours} ${hours === 1 ? "hora" : "horas"}`;
    }
    return `${hours}h ${mins}min`;
  }

  function formatPrice(cents: number): string {
    return `$${(cents / 100).toFixed(2)}`;
  }

  $: calculatedPrice = selectedService && selectedDuration && selectedService.duration_prices
    ? (selectedService.duration_prices[selectedDuration] || 
       selectedService.duration_prices[Math.min(...selectedService.durations_allowed)] || 
       0)
    : 0;
</script>

<div class="service-selector">
  <div class="form-group">
    <label for="service-select" class="label">
      Servicio <span class="required">*</span>
    </label>
    <select
      id="service-select"
      class="select"
      value={selectedServiceId}
      on:change={handleServiceChange}
      disabled={services.length === 0}
    >
      <option value="">Seleccione un servicio</option>
      {#each services as service}
        <option value={service.id}>{service.name}</option>
      {/each}
    </select>
    {#if services.length === 0}
      <p class="help-text">Cargando servicios...</p>
    {/if}
  </div>

  {#if selectedServiceId && availableDurations.length > 0}
    <div class="form-group">
      <label for="duration-select" class="label">
        Duración <span class="required">*</span>
      </label>
      <select
        id="duration-select"
        class="select"
        value={selectedDuration}
        on:change={handleDurationChange}
      >
        <option value="0">Seleccione duración</option>
        {#each availableDurations as duration}
          <option value={duration}>{formatDuration(duration)}</option>
        {/each}
      </select>
    </div>

    {#if selectedDuration > 0 && calculatedPrice > 0}
      <div class="price-preview">
        <div class="price-label">Precio Total:</div>
        <div class="price-value">{formatPrice(calculatedPrice)}</div>
      </div>
    {/if}
  {/if}

  {#if error}
    <div class="error-message">{error}</div>
  {/if}
</div>

<style>
  .service-selector {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-lg);
  }

  .form-group {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-sm);
  }

  .label {
    font-weight: 600;
    font-size: var(--text-base);
    color: var(--text-primary);
  }

  .required {
    color: var(--accent-danger);
  }

  .select {
    width: 100%;
    min-height: 48px;
    padding: var(--spacing-sm) var(--spacing-md);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
    font-size: var(--text-base);
    background: var(--theme-bg-elevated);
    color: var(--text-primary);
    transition: border-color 0.2s ease;
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

  .help-text {
    font-size: var(--text-sm);
    color: var(--text-muted);
  }

  .price-preview {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: var(--spacing-md);
    background: var(--theme-bg-secondary);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
  }

  .price-label {
    font-weight: 600;
    color: var(--text-secondary);
  }

  .price-value {
    font-size: var(--text-xl);
    font-weight: 700;
    color: var(--accent-primary);
    font-family: var(--font-secondary);
  }

  .error-message {
    padding: var(--spacing-sm) var(--spacing-md);
    background: rgba(211, 5, 84, 0.1);
    border: 1px solid var(--accent-danger);
    border-radius: var(--radius-md);
    color: var(--accent-danger);
    font-size: var(--text-sm);
  }

</style>

