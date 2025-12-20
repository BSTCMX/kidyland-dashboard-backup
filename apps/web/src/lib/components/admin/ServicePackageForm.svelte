<script lang="ts">
  /**
   * ServicePackageForm component - Create/Edit service package modal form.
   * Specialized form for packages containing only services.
   * Price is always manual (services don't have individual prices in packages).
   */
  import { Modal, Button } from "@kidyland/ui";
  import { AlertCircle, Trash2, Info } from "lucide-svelte";
  import type { Package, Service } from "@kidyland/shared/types";
  import type { PackageCreate, PackageUpdate } from "$lib/stores/packages-admin";
  import { createPackage, updatePackage } from "$lib/stores/packages-admin";
  import { fetchAllServices, servicesAdminStore } from "$lib/stores/services-admin";
  import { fetchAllSucursales, sucursalesAdminStore } from "$lib/stores/sucursales-admin";
  import { createEventDispatcher } from "svelte";
  import MultiSelectDropdown, { type Option } from "$lib/components/shared/MultiSelectDropdown.svelte";

  export let open = false;
  export let package_: Package | null = null; // If provided, edit mode; otherwise, create mode
  export let sucursalId: string = "";

  const dispatch = createEventDispatcher();

  // Form state
  let formData: PackageCreate = {
    name: "",
    sucursal_id: sucursalId,
    description: "",
    price_cents: 0,
    included_items: [],
    active: true,
  };

  let priceInput = "";
  let errors: Record<string, string> = {};
  let loading = false;

  // Guard flag and previous value tracking for form initialization (Patrón 4: Híbrido)
  let formInitialized = false;
  let prevPackage: Package | null = null;
  let prevOpen = false;

  // Item management - only services
  interface SelectedItem {
    type: "service";
    id: string;
    name: string;
    duration_minutes?: number; // Optional: not required for services in packages
    configured: boolean; // Always true for services
  }

  let selectedServices: string[] = [];
  let itemsList: SelectedItem[] = [];
  // Initialize selectedSucursal from props to avoid race condition in reactive statements
  let selectedSucursal: string[] = sucursalId ? [sucursalId] : [];

  // Load sucursales when modal opens
  let sucursalesLoaded = false;
  $: if (open && !sucursalesLoaded) {
    fetchAllSucursales();
    sucursalesLoaded = true;
  }
  $: if (!open) {
    sucursalesLoaded = false;
  }

  // Load services when modal opens or sucursal changes
  let servicesLoaded = false;
  // Initialize from prop to avoid race condition - reactive statement will use this correctly
  let lastLoadedSucursalId: string | null = sucursalId || null;
  
  async function loadServices(sucursalIdToLoad: string | null) {
    await fetchAllServices(sucursalIdToLoad || undefined);
    servicesLoaded = true;
    lastLoadedSucursalId = sucursalIdToLoad;
  }

  // Load services only after form is initialized and when sucursal changes
  // Guard flag prevents execution during initialization phase
  $: if (open && formInitialized) {
    const currentSucursalId = selectedSucursal.length > 0 ? selectedSucursal[0] : null;
    const sucursalChanged = currentSucursalId !== lastLoadedSucursalId;
    
    // Load if not loaded yet OR if sucursal changed
    if (!servicesLoaded || sucursalChanged) {
      loadServices(currentSucursalId);
      lastLoadedSucursalId = currentSucursalId;
    }
  }
  
  $: if (!open) {
    servicesLoaded = false;
    // Reset to prop value when modal closes
    lastLoadedSucursalId = sucursalId || null;
  }

  // Convert sucursales to Option format
  $: sucursalOptions = $sucursalesAdminStore.list
    .filter((s) => s.active)
    .map((s) => ({
      value: s.id,
      label: `${s.identifier} - ${s.name}`,
    })) as Option[];

  // Initialize form when package or open changes (Patrón 4: Híbrido)
  $: {
    const packageChanged = package_ !== prevPackage;
    const openChanged = open !== prevOpen;
    const shouldInitialize = open && (openChanged || packageChanged || !formInitialized);
    
    if (shouldInitialize) {
      if (package_) {
        // Edit mode: initialize from package (only services)
        const serviceItems = (package_.included_items || []).filter((item: any) => item.service_id);
        
        formData = {
          name: package_.name,
          sucursal_id: package_.sucursal_id,
          description: package_.description || "",
          price_cents: package_.price_cents,
          included_items: serviceItems,
          active: package_.active !== false,
        };
        priceInput = (package_.price_cents / 100).toFixed(2);
        // Update selectedSucursal if different from prop (edit mode)
        if (package_.sucursal_id && !selectedSucursal.includes(package_.sucursal_id)) {
          selectedSucursal = [package_.sucursal_id];
        }
        // Sync lastLoadedSucursalId
        if (package_.sucursal_id && lastLoadedSucursalId !== package_.sucursal_id) {
          lastLoadedSucursalId = package_.sucursal_id;
        }
        
        itemsList = serviceItems.map((item: any) => {
          const service = $servicesAdminStore.list.find((s) => s.id === item.service_id);
          return {
            type: "service" as const,
            id: item.service_id || "",
            name: service?.name || "Desconocido",
            duration_minutes: item.duration_minutes, // Optional: can be undefined
            configured: true, // Services are always configured
          };
        });
        
        selectedServices = itemsList.map((i) => i.id);
        errors = {};
      } else {
        // Create mode: initialize empty form
        formData = {
          name: "",
          sucursal_id: sucursalId || "",
          description: "",
          price_cents: 0,
          included_items: [],
          active: true,
        };
        priceInput = "";
        itemsList = [];
        selectedServices = [];
        // selectedSucursal already initialized from props, but update if different
        if (sucursalId && !selectedSucursal.includes(sucursalId)) {
          selectedSucursal = [sucursalId];
        }
        // Ensure lastLoadedSucursalId is in sync
        if (sucursalId && lastLoadedSucursalId !== sucursalId) {
          lastLoadedSucursalId = sucursalId;
        }
        errors = {};
      }
      
      formInitialized = true;
      prevPackage = package_;
      prevOpen = open;
    } else if (!open) {
      formInitialized = false;
      prevPackage = null;
      prevOpen = false;
    }
  }

  // Sync selectedSucursal to formData.sucursal_id
  $: formData.sucursal_id = selectedSucursal.length > 0 ? selectedSucursal[0] : "";

  $: availableServices = $servicesAdminStore.list.filter((s) => s.active !== false);

  // Prepare options for MultiSelectDropdown
  $: serviceOptions = availableServices.map((s): Option => ({
    value: s.id,
    label: s.name,
    disabled: false,
    metadata: {},
  }));

  // Handle sucursal selection
  function handleSucursalChange(selected: (string | number)[]) {
    selectedSucursal = selected.map((v) => String(v));
    if (selectedSucursal.length > 1) {
      selectedSucursal = [selectedSucursal[0]];
    }
  }

  function validateForm(): boolean {
    errors = {};

    if (!formData.name.trim()) {
      errors.name = "Nombre es requerido";
    }

    if (!formData.sucursal_id) {
      errors.sucursal_id = "Sucursal es requerida";
    }

    if (formData.price_cents <= 0) {
      errors.price = "Precio debe ser mayor a 0";
    }

    if (itemsList.length === 0) {
      errors.items = "Al menos un servicio es requerido";
    }

    return Object.keys(errors).length === 0;
  }

  // Handle service selection
  function handleServicesChange(selected: (string | number)[]) {
    selectedServices = selected.map((v) => String(v));
    
    // Add new services to itemsList
    // Services in packages are included as-is (no timer, no duration tracking needed)
    for (const serviceId of selectedServices) {
      if (!itemsList.some((item) => item.id === serviceId)) {
        const service = availableServices.find((s) => s.id === serviceId);
        if (service) {
          // Services in packages don't need duration_minutes (they're included, not timed)
          itemsList = [
            ...itemsList,
            {
              type: "service" as const,
              id: serviceId,
              name: service.name,
              duration_minutes: undefined, // Optional: not required for services in packages
              configured: true, // Services are always configured (no editing needed)
            },
          ];
        }
      }
    }

    // Remove unselected services
    itemsList = itemsList.filter((item) => selectedServices.includes(item.id));
  }

  // Remove item
  function removeItem(itemId: string) {
    itemsList = itemsList.filter((item) => item.id !== itemId);
    selectedServices = selectedServices.filter((id) => id !== itemId);
  }

  // Handle manual price input
  function handlePriceInput() {
    const inputValue = parseFloat(priceInput);
    if (!isNaN(inputValue) && inputValue > 0) {
      formData.price_cents = Math.round(inputValue * 100);
    }
  }

  async function handleSubmit() {
    if (!validateForm()) {
      return;
    }

    loading = true;
    errors = {};

    try {
      // Parse price (always manual for services)
      const priceValue = parseFloat(priceInput);
      if (isNaN(priceValue) || priceValue <= 0) {
        errors.price = "Precio inválido";
        loading = false;
        return;
      }
      formData.price_cents = Math.round(priceValue * 100);

      // Convert itemsList to included_items format (only services)
      formData.included_items = itemsList.map((item) => ({
        product_id: undefined,
        service_id: item.id,
        quantity: undefined,
        duration_minutes: item.duration_minutes, // Optional: not required for services in packages
      }));

      if (package_) {
        // Update mode
        const updateData: PackageUpdate = {
          name: formData.name,
          description: formData.description,
          price_cents: formData.price_cents,
          included_items: formData.included_items,
          active: formData.active,
        };
        await updatePackage(package_.id, updateData);
        dispatch("success");
      } else {
        // Create mode
        await createPackage(formData);
        dispatch("success");
      }
    } catch (error: any) {
      errors.submit = error.message || "Error al guardar paquete";
    } finally {
      loading = false;
    }
  }
</script>

<Modal 
  open={open} 
  title={package_ ? "Editar Paquete de Servicios" : "Crear Paquete de Servicios"}
  size="lg"
  anchorPosition={null}
  on:close={() => dispatch("close")}
>
  <form on:submit|preventDefault={handleSubmit} class="package-form">
    <!-- Nombre del Paquete -->
    <div class="input-wrapper">
      <input
        id="package-name"
        type="text"
        bind:value={formData.name}
        placeholder="Nombre del Paquete *"
        required
        disabled={loading}
        class="input"
        class:error={!!errors.name}
        aria-describedby="help-package-name"
      />
    </div>
    <p id="help-package-name" class="help-text">
      Nombre del paquete promocional (ej: Paquete Familiar, Paquete Deluxe)
    </p>
    {#if errors.name}
      <p class="error-text">
        <AlertCircle size={14} />
        {errors.name}
      </p>
    {/if}

    <!-- Descripción -->
    <div class="input-wrapper">
      <input
        id="package-description"
        type="text"
        bind:value={formData.description}
        placeholder="Descripción"
        disabled={loading}
        class="input"
        aria-describedby="help-package-description"
      />
    </div>
    <p id="help-package-description" class="help-text">
      Descripción detallada del paquete y lo que incluye (opcional)
    </p>

    <!-- Precio (Manual) -->
    <div class="input-wrapper price-input-wrapper">
      <input
        id="price"
        type="number"
        step="0.01"
        min="0"
        value={priceInput}
        on:input={(e) => {
          priceInput = e.currentTarget.value;
          handlePriceInput();
        }}
        placeholder="Precio (en pesos) *"
        required
        disabled={loading}
        class="input"
        class:error={!!errors.price}
        aria-describedby="help-price"
      />
      <div class="price-actions">
        <span class="price-indicator manual">
          <Info size={14} />
          Manual (servicios)
        </span>
      </div>
    </div>
    <p id="help-price" class="help-text">
      Precio de venta del paquete en pesos mexicanos (MXN). Los servicios no tienen precio individual en paquetes.
    </p>
    {#if errors.price}
      <p class="error-text">
        <AlertCircle size={14} />
        {errors.price}
      </p>
    {/if}

    <!-- Sucursal -->
    <div class="form-group">
      <MultiSelectDropdown
        options={sucursalOptions}
        selectedValues={selectedSucursal}
        placeholder="Seleccionar sucursal"
        label="Sucursal"
        disabled={loading}
        error={!!errors.sucursal_id}
        required={true}
        ariaDescribedBy="help-sucursal"
        on:change={(e) => handleSucursalChange(e.detail)}
      />
      <p id="help-sucursal" class="help-text">
        Selecciona la sucursal donde estará disponible este paquete
      </p>
      {#if errors.sucursal_id}
        <p class="error-text">
          <AlertCircle size={14} />
          {errors.sucursal_id}
        </p>
      {/if}
    </div>

    <div class="checkbox-wrapper">
      <label class="checkbox-label">
        <input
          id="package-active"
          type="checkbox"
          bind:checked={formData.active}
          aria-describedby="help-package-active"
        />
        Paquete Activo
      </label>
      <p id="help-package-active" class="help-text">
        Los paquetes inactivos no estarán disponibles para venta en recepción y kidibar
      </p>
    </div>

    <!-- Services Section -->
    <div class="items-section">
      <h3 class="section-title">Servicios Incluidos</h3>

      <div class="items-selection-group">
        <MultiSelectDropdown
          options={serviceOptions}
          selectedValues={selectedServices}
          placeholder="Seleccionar servicios"
          label="Servicios"
          disabled={loading}
          error={false}
          required={false}
          ariaDescribedBy="help-services"
          on:change={(e) => handleServicesChange(e.detail)}
        />
        <p id="help-services" class="help-text">
          Selecciona uno o más servicios para incluir en el paquete. Los servicios se rentan por día/duración (sin timer).
        </p>
      </div>

      {#if errors.items}
        <p class="error-text">
          <AlertCircle size={14} />
          {errors.items}
        </p>
      {/if}

      <!-- Items List -->
      {#if itemsList.length > 0}
        <div class="items-list">
          {#each itemsList as item (item.id)}
            <div class="item-card configured">
              <div class="item-header">
                <div class="item-info">
                  <strong>{item.name}</strong>
                  <span class="item-type-badge">Servicio</span>
                  <span class="item-config-display item-service-note">Incluido (sin timer)</span>
                </div>
                <div class="item-actions">
                  <button
                    type="button"
                    class="btn-icon btn-icon-danger"
                    on:click={() => removeItem(item.id)}
                    disabled={loading}
                    aria-label="Eliminar"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
            </div>
          {/each}
        </div>
      {:else}
        <p class="help-text">No hay servicios agregados. Selecciona servicios arriba para agregarlos al paquete.</p>
      {/if}
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
        {loading ? "Guardando..." : package_ ? "Actualizar" : "Crear"}
      </button>
    </div>
  </form>
</Modal>

<style>
  /* Styles copied from PackageForm for consistency */
  .package-form {
    display: flex;
    flex-direction: column;
  }

  .input-wrapper {
    position: relative;
    width: 100%;
    margin-bottom: 16px;
  }

  .price-input-wrapper {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .price-input-wrapper .input {
    flex: 1;
  }

  .price-actions {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-top: 4px;
  }

  .price-indicator {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 0.75rem;
    font-weight: 500;
    background: rgba(59, 130, 246, 0.1);
    color: var(--accent-primary, #3b82f6);
    border: 1px solid rgba(59, 130, 246, 0.2);
  }

  .price-indicator.manual {
    background: rgba(245, 158, 11, 0.1);
    color: var(--accent-warning, #f59e0b);
    border-color: rgba(245, 158, 11, 0.2);
  }

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
    margin-bottom: 0;
    font-size: 12px;
    color: #dc2f55;
    padding-left: 4px;
  }

  .checkbox-wrapper {
    margin-bottom: 16px;
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

  .items-section {
    padding: var(--spacing-md);
    background: var(--theme-bg-secondary);
    border-radius: var(--radius-md);
    border: 1px solid var(--border-primary);
  }

  .section-title {
    font-size: var(--text-lg);
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: var(--spacing-md);
  }

  .items-selection-group {
    margin-bottom: var(--spacing-md);
  }

  .items-list {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-md);
    margin-top: var(--spacing-md);
  }

  .item-card {
    padding: var(--spacing-md);
    background: var(--theme-bg-primary);
    border-radius: var(--radius-md);
    border: 2px solid var(--border-primary);
    transition: all 0.2s ease;
  }

  .item-card.configured {
    border-color: var(--accent-primary, #0093f7);
  }

  .item-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: var(--spacing-md);
  }

  .item-info {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 8px;
    color: var(--text-primary);
    font-size: var(--text-base);
  }

  .item-info strong {
    font-size: var(--text-lg);
    font-weight: 600;
  }

  .item-type-badge {
    display: inline-block;
    padding: 4px 8px;
    background: var(--theme-bg-secondary);
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 500;
    color: var(--text-secondary);
    width: fit-content;
  }

  .item-config-display {
    color: var(--text-secondary);
    font-size: 0.875rem;
  }

  .item-service-note {
    font-style: italic;
    color: var(--text-secondary, rgba(148, 163, 184, 0.8));
  }

  .item-actions {
    display: flex;
    gap: 8px;
    align-items: center;
  }

  .btn-icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 32px;
    height: 32px;
    padding: 0;
    background: transparent;
    border: 1px solid var(--border-primary);
    border-radius: 6px;
    color: var(--text-primary);
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .btn-icon:hover:not(:disabled) {
    background: var(--theme-bg-secondary);
    border-color: var(--accent-primary, #0093f7);
    color: var(--accent-primary, #0093f7);
  }

  .btn-icon:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .btn-icon-danger:hover:not(:disabled) {
    border-color: var(--accent-danger, #dc2f55);
    color: var(--accent-danger, #dc2f55);
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
  }

  .btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .btn-primary {
    background: linear-gradient(to bottom, #6eb6de, #4a77d4);
  }

  .btn-primary:hover:not(:disabled) {
    background: linear-gradient(to bottom, #7ec6ee, #5a87e4);
  }

  .btn-secondary {
    background: var(--theme-bg-secondary);
    border: 1px solid var(--border-primary);
    color: var(--text-primary);
  }

  .btn-secondary:hover:not(:disabled) {
    background: var(--theme-bg-primary);
    border-color: var(--accent-primary, #0093f7);
  }

  .form-group {
    margin-bottom: 16px;
  }
</style>




