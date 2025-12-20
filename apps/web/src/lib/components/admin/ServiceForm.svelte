<script lang="ts">
  /**
   * ServiceForm component - Create/Edit service modal form.
   */
  import { Modal } from "@kidyland/ui";
  import { AlertCircle, Volume2, VolumeX } from "lucide-svelte";
  import type { Service } from "@kidyland/shared/types";
  import type { ServiceCreate, ServiceUpdate } from "$lib/stores/services-admin";
  import { createService, updateService } from "$lib/stores/services-admin";
  import { fetchAllSucursales, sucursalesAdminStore } from "$lib/stores/sucursales-admin";
  import MultiSelectDropdown from "$lib/components/shared/MultiSelectDropdown.svelte";
  import { createEventDispatcher } from "svelte";

  // Option interface for MultiSelectDropdown (matches MultiSelectDropdown.svelte)
  interface Option {
    value: string | number;
    label: string;
  }

  export let open = false;
  export let service: Service | null = null; // If provided, edit mode; otherwise, create mode
  export let sucursalId: string = "";

  const dispatch = createEventDispatcher();

  // Load sucursales when modal opens (only once, not on every open change)
  let sucursalesLoaded = false;
  $: if (open && !sucursalesLoaded) {
    fetchAllSucursales();
    sucursalesLoaded = true;
  }
  // Reset when modal closes
  $: if (!open) {
    sucursalesLoaded = false;
  }

  // Available duration options (every 30 minutes, from 30 to 240 minutes)
  const durationOptions = [
    { value: 30, label: "30 minutos" },
    { value: 60, label: "1 hora" },
    { value: 90, label: "1.5 horas" },
    { value: 120, label: "2 horas" },
    { value: 150, label: "2.5 horas" },
    { value: 180, label: "3 horas" },
    { value: 210, label: "3.5 horas" },
    { value: 240, label: "4 horas" },
  ];

  // Available alert options (5, 10, 15 minutes)
  const alertOptions = [
    { value: 5, label: "5 minutos" },
    { value: 10, label: "10 minutos" },
    { value: 15, label: "15 minutos" },
  ];

  // Form state
  let formData: ServiceCreate = {
    name: "",
    sucursales_ids: sucursalId ? [sucursalId] : [],
    durations_allowed: [],
    duration_prices: {},
    alerts_config: [],
    active: true,
  };

  let selectedDurations: number[] = []; // Selected durations from multi-select
  let selectedSucursales: string[] = []; // Selected sucursales from multi-select
  let selectedAlerts: number[] = []; // Selected alert minutes (5, 10, 15)
  let errors: Record<string, string> = {};
  let loading = false;

  // Sound configuration per alert (minutes_before -> { enabled, loop })
  let alertSoundConfig: Record<number, { enabled: boolean; loop: boolean }> = {};
  
  // Audio element for sound preview
  let previewAudio: HTMLAudioElement | null = null;
  let previewingMinutes: number | null = null;

  // Duration pricing configuration (duration_minutes -> price_pesos)
  // Automatically shown when durations are selected
  let durationPriceConfig: Record<number, number> = {};

  // Guard flag and previous value tracking for form initialization (Patrón 4: Híbrido)
  // Prevents reactive statement from re-executing during user input
  let formInitialized = false;
  let prevService: Service | null = null;
  let prevOpen = false;

  // Convert duration options to Option format
  $: durationOptionsFormatted = durationOptions.map((opt) => ({
    value: opt.value,
    label: opt.label,
  })) as Option[];

  // Convert alert options to Option format
  $: alertOptionsFormatted = alertOptions.map((opt) => ({
    value: opt.value,
    label: opt.label,
  })) as Option[];

  // Convert sucursales to Option format
  $: sucursalOptions = $sucursalesAdminStore.list
    .filter((s) => s.active)
    .map((s) => ({
      value: s.id,
      label: `${s.identifier} - ${s.name}`,
    })) as Option[];

  // Initialize form when service or open changes (Patrón 4: Híbrido con guard flag y previous value tracking)
  // Only executes when service/open actually change, not during user input
  $: {
    // Check if service or open actually changed (not just re-evaluated)
    const serviceChanged = service !== prevService;
    const openChanged = open !== prevOpen;
    
    // Only initialize if:
    // 1. Modal is opening (open changed from false to true) OR
    // 2. Service actually changed (different service object) OR
    // 3. Form hasn't been initialized yet for this open state
    const shouldInitialize = open && (openChanged || serviceChanged || !formInitialized);
    
    if (shouldInitialize) {
      if (service) {
        // Edit mode: initialize from service
        formData = {
          name: service.name,
          sucursales_ids: service.sucursales_ids || (service.sucursal_id ? [service.sucursal_id] : []),
          durations_allowed: service.durations_allowed,
          duration_prices: service.duration_prices || {},
          alerts_config: service.alerts_config || [],
          active: service.active !== false,
        };
        selectedDurations = [...service.durations_allowed];
        selectedSucursales = service.sucursales_ids || (service.sucursal_id ? [service.sucursal_id] : []);
        selectedAlerts = (service.alerts_config || []).map((a: { minutes_before: number }) => a.minutes_before);
        
        // Initialize duration pricing configuration from service
        // IMPORTANT: Initialize for ALL selected durations, even if price doesn't exist in service.duration_prices
        durationPriceConfig = {};
        if (service.duration_prices && Object.keys(service.duration_prices).length > 0) {
          // Convert from cents to pesos for display
          Object.keys(service.duration_prices).forEach((key) => {
            durationPriceConfig[Number(key)] = service.duration_prices[Number(key)] / 100;
          });
        }
        // Ensure all selected durations have a price config entry (even if 0)
        selectedDurations.forEach((duration) => {
          if (durationPriceConfig[duration] === undefined) {
            // If duration doesn't have a price, initialize with 0 (user must fill)
            durationPriceConfig[duration] = 0;
          }
        });
        
        // Initialize sound configuration from existing alerts
        alertSoundConfig = {};
        (service.alerts_config || []).forEach((alert: { minutes_before: number; sound_enabled?: boolean; sound_loop?: boolean }) => {
          alertSoundConfig[alert.minutes_before] = {
            enabled: alert.sound_enabled ?? false,
            loop: alert.sound_loop ?? false,
          };
        });
        
        errors = {};
      } else {
        // Create mode: initialize empty form
        const defaultSucursales = sucursalId ? [sucursalId] : [];
        formData = {
          name: "",
          sucursales_ids: defaultSucursales,
          durations_allowed: [],
          duration_prices: {},
          alerts_config: [],
          active: true,
        };
        selectedDurations = [];
        selectedSucursales = defaultSucursales;
        selectedAlerts = [];
        alertSoundConfig = {};
        durationPriceConfig = {};
        errors = {};
      }
      
      // Mark as initialized and update previous values
      formInitialized = true;
      prevService = service;
      prevOpen = open;
    } else if (!open) {
      // Modal closed: reset initialization flag
      formInitialized = false;
      prevService = null;
      prevOpen = false;
    }
  }

  // Sync selectedDurations to formData.durations_allowed (always sync, even if empty)
  $: formData.durations_allowed = [...selectedDurations];

  // Sync selectedSucursales to formData.sucursales_ids (always sync, even if empty)
  $: formData.sucursales_ids = [...selectedSucursales];

  // Sync selectedAlerts to formData.alerts_config with sound configuration
  $: formData.alerts_config = selectedAlerts.map((min) => {
    const soundConfig = alertSoundConfig[min] || { enabled: false, loop: false };
    return {
      minutes_before: min,
      sound_enabled: soundConfig.enabled,
      sound_loop: soundConfig.loop,
    };
  });

  // Guard: Ensure all selected durations have a price config entry (safety net)
  // This reactive statement acts as a safety guard, but handleDurationsChange
  // already guarantees initialization, so this is just an extra layer of protection
  $: if (selectedDurations.length > 0) {
    let needsUpdate = false;
    const updatedConfig = { ...durationPriceConfig };
    
    selectedDurations.forEach((duration) => {
      if (updatedConfig[duration] === undefined || isNaN(updatedConfig[duration])) {
        updatedConfig[duration] = 0;
        needsUpdate = true;
      }
    });
    
    // Only update if we need to initialize missing properties
    // This should rarely trigger since handleDurationsChange handles initialization
    if (needsUpdate) {
      durationPriceConfig = updatedConfig;
    }
  }

  // Sync durationPriceConfig to formData.duration_prices (convert pesos to cents)
  // This reactive statement only READS durationPriceConfig, never writes to it
  // Since we use value + on:input (not bind:value), this cannot interfere with user input
  // on:input updates durationPriceConfig directly, and this statement only syncs to formData
  // CRITICAL: Always sync when durationPriceConfig or selectedDurations change
  // This ensures formData.duration_prices is always up-to-date before submit
  $: if (selectedDurations.length > 0) {
    const pricesInCents: Record<number, number> = {};
    
    selectedDurations.forEach((duration) => {
      const price = durationPriceConfig[duration];
      // Include price if it's defined and valid (not NaN, >= 0)
      // Always include all selected durations, even if price is 0 (validation will catch invalid ones)
      if (price !== undefined && !isNaN(price) && price >= 0) {
        pricesInCents[duration] = Math.round(price * 100);
      } else {
        // If price is invalid, set to 0 (will be caught by validation)
        pricesInCents[duration] = 0;
      }
    });
    
    // Always update formData.duration_prices to ensure it's in sync
    // The comparison logic was causing issues where changes weren't detected
    // By always updating, we guarantee formData is current before submit
    formData.duration_prices = pricesInCents;
  } else {
    // Only clear if it's not already empty
    if (Object.keys(formData.duration_prices || {}).length > 0) {
      formData.duration_prices = {};
    }
  }

  function validateForm(): boolean {
    errors = {};

    if (!formData.name.trim()) {
      errors.name = "Nombre es requerido";
    }

    if (!selectedSucursales || selectedSucursales.length === 0) {
      errors.sucursales = "Al menos una sucursal es requerida";
    }

    if (selectedDurations.length === 0) {
      errors.durations = "Al menos una duración es requerida";
    }

    // Validate that all selected durations have prices (all required)
    const missingPrices = selectedDurations.filter((d) => {
      const price = durationPriceConfig[d];
      return price === undefined || price <= 0 || isNaN(price);
    });
    if (missingPrices.length > 0) {
      errors.durationPrices = `Debes asignar un precio válido a todas las duraciones seleccionadas`;
    }

    return Object.keys(errors).length === 0;
  }


  function handleDurationsChange(event: CustomEvent<(string | number)[]>) {
    const newSelectedDurations = event.detail.map((val) => Number(val));
    
    // CRITICAL: Initialize ALL duration price config entries BEFORE updating state
    // This guarantees that all properties exist when inputs render (Patrón 5)
    const newDurationPriceConfig: Record<number, number> = {};
    
    // Preserve existing prices for durations that are still selected, initialize new ones with 0
    newSelectedDurations.forEach((d) => {
      const existingPrice = durationPriceConfig[d];
      // Always ensure a valid number (not undefined, not NaN)
      newDurationPriceConfig[d] = (existingPrice !== undefined && !isNaN(existingPrice)) ? existingPrice : 0;
    });
    
    // Update state atomically: durationPriceConfig FIRST, then selectedDurations
    // This ensures reactive statements see complete data when they execute
    durationPriceConfig = newDurationPriceConfig; // Update first to guarantee properties exist
    selectedDurations = newSelectedDurations; // Then update selected durations
  }

  function handleSucursalesChange(event: CustomEvent<(string | number)[]>) {
    selectedSucursales = event.detail.map((val) => String(val));
  }

  function handleAlertsChange(event: CustomEvent<(string | number)[]>) {
    const newSelectedAlerts = event.detail.map((val) => Number(val));
    
    // Remove sound config for alerts that are no longer selected
    const removedAlerts = selectedAlerts.filter((min) => !newSelectedAlerts.includes(min));
    removedAlerts.forEach((min) => {
      delete alertSoundConfig[min];
    });
    
    // Initialize sound config for newly added alerts (if not already present)
    const addedAlerts = newSelectedAlerts.filter((min) => !selectedAlerts.includes(min));
    addedAlerts.forEach((min) => {
      if (!alertSoundConfig[min]) {
        alertSoundConfig[min] = { enabled: false, loop: false };
      }
    });
    
    // Update selectedAlerts and trigger reactivity
    selectedAlerts = newSelectedAlerts;
    alertSoundConfig = { ...alertSoundConfig };
  }

  function handleSoundEnabledChange(minutes: number, enabled: boolean) {
    if (!alertSoundConfig[minutes]) {
      alertSoundConfig[minutes] = { enabled: false, loop: false };
    }
    alertSoundConfig[minutes].enabled = enabled;
    // If sound is disabled, also disable loop
    if (!enabled) {
      alertSoundConfig[minutes].loop = false;
    }
    // Trigger reactivity
    alertSoundConfig = { ...alertSoundConfig };
  }

  function handleSoundLoopChange(minutes: number, loop: boolean) {
    if (!alertSoundConfig[minutes]) {
      alertSoundConfig[minutes] = { enabled: false, loop: false };
    }
    alertSoundConfig[minutes].loop = loop;
    // If loop is enabled, also enable sound
    if (loop) {
      alertSoundConfig[minutes].enabled = true;
    }
    // Trigger reactivity
    alertSoundConfig = { ...alertSoundConfig };
  }

  function previewSound(minutes: number) {
    // Stop any currently playing preview
    stopSoundPreview();

    // Create audio element if it doesn't exist
    if (!previewAudio) {
      previewAudio = new Audio("/sounds/alert.mp3");
      previewAudio.addEventListener("ended", () => {
        if (previewingMinutes === minutes && alertSoundConfig[minutes]?.loop) {
          // If loop is enabled, restart the sound
          previewAudio?.play().catch((err) => {
            console.error("Error playing sound preview:", err);
          });
        } else {
          previewingMinutes = null;
        }
      });
    }

    // Get sound configuration for this alert
    const soundConfig = alertSoundConfig[minutes] || { enabled: false, loop: false };
    
    if (!soundConfig.enabled) {
      // If sound is not enabled, just play once for preview
      previewAudio.loop = false;
    } else {
      // Use the configured loop setting
      previewAudio.loop = soundConfig.loop;
    }

    previewingMinutes = minutes;
    previewAudio.play().catch((err) => {
      console.error("Error playing sound preview:", err);
      previewingMinutes = null;
    });
  }

  function stopSoundPreview() {
    if (previewAudio) {
      previewAudio.pause();
      previewAudio.currentTime = 0;
    }
    previewingMinutes = null;
  }

  // Cleanup on modal close
  $: if (!open) {
    stopSoundPreview();
  }


  async function handleSubmit() {
    if (!validateForm()) {
      return;
    }

    loading = true;
    errors = {};

    try {
      // Validate durations
      if (selectedDurations.length === 0) {
        errors.durations = "Al menos una duración válida es requerida";
        loading = false;
        return;
      }
      formData.durations_allowed = [...selectedDurations];
      
      // CRITICAL: Ensure duration_prices is synced before submit
      // Force sync from durationPriceConfig to formData.duration_prices
      // This guarantees that the latest user input is included in the submission
      const pricesInCents: Record<number, number> = {};
      selectedDurations.forEach((duration) => {
        const price = durationPriceConfig[duration];
        if (price !== undefined && !isNaN(price) && price >= 0) {
          pricesInCents[duration] = Math.round(price * 100);
        }
      });
      formData.duration_prices = pricesInCents;

      // Validate sucursales
      if (selectedSucursales.length === 0) {
        errors.sucursales = "Al menos una sucursal es requerida";
        loading = false;
        return;
      }
      formData.sucursales_ids = [...selectedSucursales];
      
      // Backend requires sucursal_id (use first from sucursales_ids)
      // The backend will handle the conversion, but we need to provide it
      if (selectedSucursales.length > 0) {
        formData.sucursal_id = selectedSucursales[0];
      }

      if (service) {
        // Update mode
        const updateData: ServiceUpdate = {
          name: formData.name,
          sucursales_ids: formData.sucursales_ids,
          durations_allowed: formData.durations_allowed,
          duration_prices: formData.duration_prices,
          alerts_config: formData.alerts_config,
          active: formData.active,
        };
        // Also include sucursal_id for update if we have sucursales_ids
        if (formData.sucursales_ids && formData.sucursales_ids.length > 0) {
          updateData.sucursal_id = formData.sucursales_ids[0];
        }
        const updated = await updateService(service.id, updateData);
        if (updated) {
          dispatch("success");
        }
      } else {
        // Create mode - backend will derive sucursal_id from sucursales_ids if needed
        const createData: ServiceCreate = {
          name: formData.name,
          sucursales_ids: formData.sucursales_ids,
          durations_allowed: formData.durations_allowed,
          duration_prices: formData.duration_prices,
          alerts_config: formData.alerts_config,
          active: formData.active !== false,
        };
        // Only include sucursal_id if we have it, backend will derive from sucursales_ids if needed
        if (formData.sucursal_id) {
          createData.sucursal_id = formData.sucursal_id;
        }
        const created = await createService(createData);
        if (created) {
          dispatch("success");
        }
      }
    } catch (error: any) {
      // Better error handling for API errors
      let errorMessage = "Error al guardar servicio";
      if (error?.response?.data?.detail) {
        // FastAPI validation errors
        if (typeof error.response.data.detail === "string") {
          errorMessage = error.response.data.detail;
        } else if (Array.isArray(error.response.data.detail)) {
          // Multiple validation errors
          const errorDetails = error.response.data.detail
            .map((err: any) => err?.msg || JSON.stringify(err))
            .join(", ");
          errorMessage = `Errores de validación: ${errorDetails}`;
        } else {
          errorMessage = JSON.stringify(error.response.data.detail);
        }
      } else if (error?.message) {
        errorMessage = error.message;
      }
      errors.submit = errorMessage;
    } finally {
      loading = false;
    }
  }
</script>

<Modal 
  open={open} 
  title={service ? "Editar Servicio" : "Crear Servicio"}
  size="lg"
  anchorPosition={null}
  on:close={() => dispatch("close")}
>
  <form on:submit|preventDefault={handleSubmit} class="service-form">
    <!-- Nombre del Servicio -->
    <div class="input-wrapper">
      <input
        id="service-name"
        type="text"
        bind:value={formData.name}
        placeholder="Nombre del Servicio *"
        required
        disabled={loading}
        class="input"
        class:error={!!errors.name}
      />
    </div>
    {#if errors.name}
      <p class="error-text">
        <AlertCircle size={14} />
        {errors.name}
      </p>
    {/if}

    <!-- Sucursales (required, multiple) -->
    <MultiSelectDropdown
      options={sucursalOptions}
      selectedValues={selectedSucursales}
      placeholder="Seleccionar sucursales *"
      label="Sucursales"
      disabled={loading || ($sucursalesAdminStore.loading && sucursalOptions.length === 0)}
      error={!!errors.sucursales}
      required={true}
      on:change={handleSucursalesChange}
    />
    {#if errors.sucursales}
      <p class="error-text">
        <AlertCircle size={14} />
        {errors.sucursales}
      </p>
    {/if}

    <!-- Duraciones Permitidas - Selector Múltiple -->
    <MultiSelectDropdown
      options={durationOptionsFormatted}
      selectedValues={selectedDurations}
      placeholder="Seleccionar duraciones *"
      label="Duraciones Permitidas"
      disabled={loading}
      error={!!errors.durations}
      required={true}
      on:change={handleDurationsChange}
    />
    {#if errors.durations}
      <p class="error-text">
        <AlertCircle size={14} />
        {errors.durations}
      </p>
    {/if}
    <p class="help-text">
      Selecciona una o más duraciones permitidas
    </p>

    <!-- Precios por Duración - Tabla Simple -->
    {#if selectedDurations.length > 0}
      <div class="duration-pricing-section">
        <h3 class="section-title">Precios por Duración</h3>
        <p class="help-text">Configura el precio específico para cada duración seleccionada</p>
        
        <table class="duration-pricing-table">
          <thead>
            <tr>
              <th>Duración</th>
              <th>Precio (pesos)</th>
            </tr>
          </thead>
          <tbody>
            {#each selectedDurations as duration (duration)}
              {@const durationOption = durationOptions.find((opt) => opt.value === duration)}
              {@const priceValue = durationPriceConfig[duration] ?? 0}
              <tr>
                <td class="duration-cell">
                  <span class="duration-label">{durationOption?.label || `${duration} minutos`}</span>
                </td>
                <td class="price-cell">
                  <input
                    id="price-{duration}"
                    type="number"
                    step="0.01"
                    min="0"
                    value={durationPriceConfig[duration] ?? 0}
                    on:input={(e) => {
                      const inputValue = e.currentTarget.value;
                      const numValue = parseFloat(inputValue);
                      // Update durationPriceConfig directly (Patrón 2: value + on:input)
                      if (!isNaN(numValue) && numValue >= 0) {
                        durationPriceConfig[duration] = numValue;
                        durationPriceConfig = { ...durationPriceConfig }; // Trigger reactivity
                      } else if (inputValue === "" || inputValue === "-") {
                        // Allow empty or negative sign temporarily while typing
                        // Don't update state yet, let user finish typing
                      }
                    }}
                    on:blur={(e) => {
                      // Validate and correct value on blur
                      const inputValue = e.currentTarget.value;
                      const numValue = parseFloat(inputValue);
                      if (isNaN(numValue) || numValue < 0) {
                        // Invalid value: reset to 0
                        durationPriceConfig[duration] = 0;
                        durationPriceConfig = { ...durationPriceConfig }; // Trigger reactivity
                        e.currentTarget.value = "0";
                      } else {
                        // Valid value: ensure it's stored
                        durationPriceConfig[duration] = numValue;
                        durationPriceConfig = { ...durationPriceConfig }; // Trigger reactivity
                      }
                    }}
                    disabled={loading}
                    class="duration-price-input"
                    class:error={errors.durationPrices && (priceValue === undefined || priceValue <= 0 || isNaN(priceValue))}
                    aria-label="Precio para {durationOption?.label}"
                  />
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
      {#if errors.durationPrices}
        <p class="error-text">
          <AlertCircle size={14} />
          {errors.durationPrices}
        </p>
      {/if}
    {/if}

    <!-- Alerts Configuration - MultiSelectDropdown -->
    <div class="alerts-dropdown-wrapper">
      <MultiSelectDropdown
        options={alertOptionsFormatted}
        selectedValues={selectedAlerts}
        placeholder="Seleccionar alertas"
        label="Configuración de Alertas"
        disabled={loading}
        error={false}
        required={false}
        on:change={handleAlertsChange}
      />
      <p class="help-text">
        Selecciona los minutos antes de que termine el timer para activar alertas (5, 10, 15 minutos)
      </p>
    </div>

    <!-- Sound Configuration per Alert -->
    {#if selectedAlerts.length > 0}
      <div class="sound-config-section" class:has-alerts={selectedAlerts.length > 0}>
        <h3 class="section-title">Configuración de Sonido por Alerta</h3>
        <p class="help-text">Configura el sonido para cada alerta seleccionada</p>
        
        <div class="sound-config-list">
          {#each selectedAlerts as minutes (minutes)}
            {@const soundConfig = alertSoundConfig[minutes] || { enabled: false, loop: false }}
            {@const isPreviewing = previewingMinutes === minutes}
            <div class="sound-config-item">
              <div class="sound-config-header">
                <span class="sound-config-label">
                  ⏰ Alerta a los {minutes} minutos
                </span>
              </div>
              
              <div class="sound-config-options">
                <label class="sound-checkbox-label">
                  <input
                    type="checkbox"
                    checked={soundConfig.enabled}
                    on:change={(e) => handleSoundEnabledChange(minutes, e.currentTarget.checked)}
                    disabled={loading}
                  />
                  <span>Activar sonido</span>
                </label>
                
                <label class="sound-checkbox-label" class:disabled={!soundConfig.enabled}>
                  <input
                    type="checkbox"
                    checked={soundConfig.loop}
                    on:change={(e) => handleSoundLoopChange(minutes, e.currentTarget.checked)}
                    disabled={loading || !soundConfig.enabled}
                  />
                  <span>Repetir continuamente</span>
                </label>
              </div>
              
              <div class="sound-preview-actions">
                {#if isPreviewing}
                  <button
                    type="button"
                    class="btn btn-secondary btn-small"
                    on:click={stopSoundPreview}
                    disabled={loading}
                  >
                    <VolumeX size={14} />
                    Detener
                  </button>
                {:else}
                  <button
                    type="button"
                    class="btn btn-secondary btn-small"
                    on:click={() => previewSound(minutes)}
                    disabled={loading}
                  >
                    <Volume2 size={14} />
                    Probar sonido
                  </button>
                {/if}
              </div>
            </div>
          {/each}
        </div>
      </div>
    {/if}

    <!-- Servicio Activo -->
    <div class="checkbox-wrapper">
      <label class="checkbox-label">
        <input
          type="checkbox"
          bind:checked={formData.active}
          disabled={loading}
        />
        <span>Servicio Activo</span>
      </label>
      <p class="help-text">Los servicios inactivos no aparecerán en las listas de selección</p>
    </div>

    {#if errors.submit}
      <div class="error-banner">{errors.submit}</div>
    {/if}

    <div class="form-footer">
      <button 
        type="button" 
        class="btn btn-secondary" 
        on:click={() => dispatch("close")} 
        disabled={loading}
      >
        Cancelar
      </button>
      <button 
        type="submit" 
        class="btn btn-primary" 
        disabled={loading}
      >
        {loading ? "Guardando..." : service ? "Actualizar" : "Crear"}
      </button>
    </div>
  </form>
</Modal>

<style>
  .service-form {
    display: flex;
    flex-direction: column;
    position: relative;
    z-index: 1; /* Base z-index for form content */
  }

  /* Input Wrapper - Estilo simplificado como SucursalForm */
  .input-wrapper {
    position: relative;
    width: 100%;
    margin-bottom: 16px;
  }

  /* Inputs simplificados - estilo moderno pero simple */
  .input {
    width: 100%;
    margin-bottom: 0;
    background-color: var(--input-bg, #303245);
    border-radius: 12px;
    border: 1px solid var(--border-primary, #444);
    box-sizing: border-box;
    color: var(--text-primary, #eee);
    font-size: 18px;
    height: 50px;
    outline: 0;
    padding: 0 20px;
    font-family: var(--font-body, sans-serif);
    transition: all 0.2s ease;
  }

  .input:focus {
    background-color: var(--input-bg-focus, #3a3d52);
    border-color: var(--accent-primary, #0093f7);
  }

  .input.error {
    border: 2px solid var(--accent-danger, #dc2f55);
  }

  .input:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .input::placeholder {
    color: var(--text-muted, #65657b);
    opacity: 1;
  }



  .help-text {
    font-size: 12px;
    color: #808097;
    margin-top: 4px;
    margin-bottom: 0;
    padding-left: 4px;
  }

  .error-text {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-top: 4px;
    margin-bottom: 16px;
    font-size: 12px;
    color: #dc2f55;
    padding-left: 4px;
  }

  .checkbox-wrapper {
    margin-bottom: 16px;
  }

  /* Alerts Dropdown Wrapper - Extra spacing before sound config */
  .alerts-dropdown-wrapper {
    margin-bottom: 24px; /* Extra space before sound config section appears */
  }

  .checkbox-label {
    display: flex;
    align-items: center;
    gap: 8px;
    cursor: pointer;
    user-select: none;
    color: var(--text-primary, #eee);
    font-size: 16px;
  }

  .checkbox-label input[type="checkbox"] {
    width: 20px;
    height: 20px;
    cursor: pointer;
    accent-color: var(--accent-primary, #0093f7);
  }

  /* Sound Configuration Section */
  .sound-config-section {
    position: relative;
    z-index: 0; /* Lower than dropdowns (3000) - should not interfere */
    margin-top: 0; /* No top margin since wrapper handles spacing */
    padding: var(--spacing-lg, 20px); /* Increased padding for better breathing room */
    background: var(--theme-bg-secondary, rgba(48, 50, 69, 0.5));
    border-radius: var(--radius-md);
    border: 1px solid var(--border-primary, rgba(148, 163, 184, 0.2));
    margin-bottom: 24px; /* Increased from 16px for better spacing */
    isolation: isolate; /* Create new stacking context to prevent interference */
  }

  .sound-config-section.has-alerts {
    margin-top: 0; /* No extra margin, wrapper handles it */
  }

  .section-title {
    font-size: var(--text-lg, 18px);
    font-weight: 600;
    color: var(--text-primary, #eee);
    margin-bottom: var(--spacing-sm, 8px);
  }

  .sound-config-list {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-lg, 20px); /* Increased gap between items */
    margin-top: var(--spacing-lg, 20px); /* Increased top margin */
  }

  .sound-config-item {
    position: relative;
    z-index: 0; /* Lower than dropdowns */
    padding: var(--spacing-lg, 20px); /* Increased padding for better spacing */
    background: var(--theme-bg-primary, rgba(15, 23, 42, 0.8));
    border-radius: var(--radius-sm, 8px);
    border: 1px solid var(--border-primary, rgba(148, 163, 184, 0.2));
    isolation: isolate; /* Create new stacking context */
  }

  .sound-config-header {
    margin-bottom: var(--spacing-md, 16px); /* Increased from sm to md for better spacing */
  }

  .sound-config-label {
    font-size: var(--text-base, 16px);
    font-weight: 600;
    color: var(--text-primary, #eee);
  }

  .sound-config-options {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-md, 12px); /* Increased gap between checkboxes */
    margin-bottom: var(--spacing-lg, 20px); /* Increased bottom margin */
  }

  .sound-checkbox-label {
    display: flex;
    align-items: center;
    gap: 8px;
    cursor: pointer;
    user-select: none;
    color: var(--text-primary, #eee);
    font-size: var(--text-sm, 14px);
  }

  .sound-checkbox-label.disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .sound-checkbox-label input[type="checkbox"] {
    width: 18px;
    height: 18px;
    cursor: pointer;
    accent-color: var(--accent-primary, #0093f7);
  }

  .sound-checkbox-label.disabled input[type="checkbox"] {
    cursor: not-allowed;
  }

  .sound-preview-actions {
    display: flex;
    justify-content: flex-start;
    margin-top: var(--spacing-sm, 8px); /* Add top margin for separation */
  }

  .btn-small {
    height: 36px;
    font-size: 14px;
    padding: 0 16px;
    min-width: auto;
  }

  /* Duration Pricing Section */
  .duration-pricing-section {
    position: relative;
    z-index: 0;
    margin-top: 24px;
    padding: var(--spacing-lg, 20px);
    background: var(--theme-bg-secondary, rgba(48, 50, 69, 0.5));
    border-radius: var(--radius-md);
    border: 1px solid var(--border-primary, rgba(148, 163, 184, 0.2));
    margin-bottom: 24px;
    isolation: isolate;
  }

  /* Duration Pricing Table Styles */
  .duration-pricing-table {
    width: 100%;
    border-collapse: collapse;
    margin-top: var(--spacing-md, 16px);
    background: var(--theme-bg-primary, rgba(15, 23, 42, 0.8));
    border-radius: var(--radius-sm, 8px);
    overflow: hidden;
  }

  .duration-pricing-table thead {
    background: var(--theme-bg-secondary, rgba(48, 50, 69, 0.8));
  }

  .duration-pricing-table th {
    padding: var(--spacing-md, 16px);
    text-align: left;
    font-size: var(--text-sm, 14px);
    font-weight: 600;
    color: var(--text-primary, #eee);
    border-bottom: 2px solid var(--border-primary, rgba(148, 163, 184, 0.2));
  }

  .duration-pricing-table td {
    padding: var(--spacing-md, 16px);
    border-bottom: 1px solid var(--border-primary, rgba(148, 163, 184, 0.1));
  }

  .duration-pricing-table tbody tr:last-child td {
    border-bottom: none;
  }

  .duration-pricing-table tbody tr:hover {
    background: var(--theme-bg-secondary, rgba(48, 50, 69, 0.3));
  }

  .duration-cell {
    width: 40%;
  }

  .duration-label {
    font-size: var(--text-base, 16px);
    font-weight: 500;
    color: var(--text-primary, #eee);
  }

  .price-cell {
    width: 60%;
  }

  .duration-price-input {
    width: 100%;
    padding: 0.75rem 1rem;
    font-size: 1rem;
    background: var(--input-bg, #303245);
    border: 2px solid var(--border-primary, #444);
    border-radius: 8px;
    color: var(--text-primary, #eee);
    transition: all 0.2s ease;
    box-sizing: border-box;
  }

  .duration-price-input:focus {
    outline: none;
    border-color: var(--accent-primary, #0093f7);
    background: var(--input-bg-focus, #3a3d52);
    box-shadow: 0 0 0 3px rgba(0, 147, 247, 0.1);
  }

  .duration-price-input:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .duration-price-input.error {
    border-color: var(--accent-danger, #dc2f55);
  }


  .error-banner {
    background: rgba(211, 5, 84, 0.1);
    border: 2px solid var(--accent-danger);
    color: var(--accent-danger);
    padding: var(--spacing-md);
    border-radius: var(--radius-lg);
    margin-bottom: var(--spacing-md);
    font-size: var(--text-sm);
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
  }

  .form-footer {
    display: flex;
    gap: 12px;
    justify-content: flex-end;
    margin-top: 32px;
    padding-top: 0;
    border-top: none;
  }

  /* Botones con el nuevo estilo */
  .btn {
    background-color: var(--accent-primary, #08d);
    border-radius: 12px;
    border: 0;
    box-sizing: border-box;
    color: #eee;
    cursor: pointer;
    font-size: 18px;
    height: 50px;
    text-align: center;
    width: auto;
    min-width: 120px;
    padding: 0 24px;
    font-family: sans-serif;
    font-weight: 600;
    transition: background-color 0.2s ease;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
  }

  .btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .btn-primary {
    background: linear-gradient(to bottom, #6eb6de, #4a77d4);
    background-color: #4a77d4;
    border-color: #3762bc;
    color: #ffffff;
    text-shadow: 0 -1px 0 rgba(0, 0, 0, 0.25);
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.2), 0 1px 2px rgba(0, 0, 0, 0.2);
  }

  .btn-primary:hover:not(:disabled) {
    background: linear-gradient(to bottom, #7fc3e5, #5a87e4);
    background-color: #5a87e4;
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.2), 0 2px 4px rgba(0, 0, 0, 0.3);
  }

  .btn-primary:active:not(:disabled) {
    background: linear-gradient(to bottom, #4a77d4, #3762bc);
    background-color: #3762bc;
    box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.2);
  }

  .btn-secondary {
    background: linear-gradient(to bottom, #f5f5f5, #e6e6e6);
    background-color: #e6e6e6;
    border-color: #d4d4d4;
    color: #333333;
    text-shadow: 0 1px 1px rgba(255, 255, 255, 0.75);
  }

  .btn-secondary:hover:not(:disabled) {
    background: linear-gradient(to bottom, #ffffff, #f5f5f5);
    background-color: #f5f5f5;
    border-color: #d4d4d4;
  }

  .btn-secondary:active:not(:disabled) {
    background: linear-gradient(to bottom, #e6e6e6, #d4d4d4);
    background-color: #d4d4d4;
    box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.1);
  }

          /* Responsive: Mobile */
          @media (max-width: 768px) {

    .form-footer {
      flex-direction: column;
    }

    .form-footer .btn {
      width: 100%;
    }
  }

  @media (max-width: 640px) {
    .form-footer {
      flex-direction: column;
    }
  }
</style>
