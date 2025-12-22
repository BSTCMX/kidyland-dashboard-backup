<script lang="ts">
  /**
   * PackageForm component - Create/Edit package modal form.
   */
  import { Modal, Button } from "@kidyland/ui";
  import { AlertCircle, Trash2, Edit2 } from "lucide-svelte";
  import type { Package, Product, Service } from "@kidyland/shared/types";
  import type { PackageCreate, PackageUpdate } from "$lib/stores/packages-admin";
  import { createPackage, updatePackage } from "$lib/stores/packages-admin";
  import { fetchAllProducts, productsAdminStore } from "$lib/stores/products-admin";
  import { fetchAllServices, servicesAdminStore } from "$lib/stores/services-admin";
  import { fetchAllSucursales, sucursalesAdminStore } from "$lib/stores/sucursales-admin";
  import { createEventDispatcher } from "svelte";
  import MultiSelectDropdown, { type Option } from "$lib/components/shared/MultiSelectDropdown.svelte";
  import PackageItemConfig from "./PackageItemConfig.svelte";
  import {
    inferPackageType,
    calculatePackagePrice,
    isPriceAutoCalculated,
    formatPackageType,
  } from "$lib/utils/package-helpers";

  export let open = false;
  export let package_: Package | null = null; // If provided, edit mode; otherwise, create mode
  export let sucursalId: string = "";

  const dispatch = createEventDispatcher();

  // Form state
  let formData: PackageCreate = {
    name: "",
    sucursales_ids: sucursalId ? [sucursalId] : [],
    description: "",
    price_cents: 0,
    included_items: [],
    active: true,
  };

  let priceInput = "";
  let errors: Record<string, string> = {};
  let loading = false;
  let isPriceManual = false; // Track if user manually edited price (Patrón 3: Híbrido)

  // Guard flag and previous value tracking for form initialization (Patrón 4: Híbrido)
  // Prevents reactive statement from re-executing during user input
  let formInitialized = false;
  let prevPackage: Package | null = null;
  let prevOpen = false;

  // Item management - Patrón 5 (Híbrido)
  interface SelectedItem {
    type: "product" | "service";
    id: string;
    name: string;
    quantity?: number; // For products
    duration_minutes?: number; // For services
    configured: boolean; // Whether quantity/duration is configured
    editing: boolean; // Whether currently being edited
  }

  let selectedProducts: string[] = [];
  let selectedServices: string[] = [];
  let itemsList: SelectedItem[] = [];
  let configuringItemId: string | null = null; // ID of item currently being configured
  let selectedSucursal: string[] = []; // Selected sucursal (array for MultiSelectDropdown compatibility)

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

  // Load products and services when modal opens or sucursal changes
  let productsServicesLoaded = false;
  let lastLoadedSucursalId: string | null = null;
  
  async function loadProductsAndServices(sucursalIdToLoad: string | null) {
    await Promise.all([
      fetchAllProducts(sucursalIdToLoad || undefined),
      fetchAllServices(sucursalIdToLoad || undefined),
    ]);
    productsServicesLoaded = true;
    lastLoadedSucursalId = sucursalIdToLoad;
  }

  $: if (open) {
    const currentSucursalId = selectedSucursal.length > 0 ? selectedSucursal[0] : null;
    const sucursalChanged = currentSucursalId !== lastLoadedSucursalId;
    const shouldLoad = !productsServicesLoaded || sucursalChanged;
    
    if (shouldLoad) {
      loadProductsAndServices(currentSucursalId);
    }
  }
  
  // Reset when modal closes
  $: if (!open) {
    productsServicesLoaded = false;
    lastLoadedSucursalId = null;
  }

  // Convert sucursales to Option format
  $: sucursalOptions = $sucursalesAdminStore.list
    .filter((s) => s.active)
    .map((s) => ({
      value: s.id,
      label: `${s.identifier} - ${s.name}`,
    })) as Option[];

  // Initialize form when package or open changes (Patrón 4: Híbrido con guard flag y previous value tracking)
  // Only executes when package/open actually change, not during user input
  $: {
    // Check if package or open actually changed (not just re-evaluated)
    const packageChanged = package_ !== prevPackage;
    const openChanged = open !== prevOpen;
    
    // Only initialize if:
    // 1. Modal is opening (open changed from false to true) OR
    // 2. Package actually changed (different package object) OR
    // 3. Form hasn't been initialized yet for this open state
    const shouldInitialize = open && (openChanged || packageChanged || !formInitialized);
    
    if (shouldInitialize) {
      if (package_) {
        // Edit mode: initialize from package
        formData = {
          name: package_.name,
          sucursales_ids: package_.sucursales_ids || (package_.sucursal_id ? [package_.sucursal_id] : []),
          description: package_.description || "",
          price_cents: package_.price_cents,
          included_items: package_.included_items || [],
          active: package_.active !== false,
        };
        priceInput = (package_.price_cents / 100).toFixed(2);
        selectedSucursal = package_.sucursales_ids || (package_.sucursal_id ? [package_.sucursal_id] : []);
        itemsList = (package_.included_items || []).map((item) => {
          const product = $productsAdminStore.list.find((p) => p.id === item.product_id);
          const service = $servicesAdminStore.list.find((s) => s.id === item.service_id);
          const isProduct = !!item.product_id;
          // Products need quantity to be configured, services are always configured (included as-is, no timer)
          const isConfigured = isProduct 
            ? (item.quantity !== undefined && item.quantity > 0)
            : true; // Services are always configured (no editing needed)
          return {
            type: isProduct ? "product" : "service",
            id: item.product_id || item.service_id || "",
            name: product?.name || service?.name || "Desconocido",
            quantity: item.quantity,
            duration_minutes: item.duration_minutes, // Stored for backend, but not displayed/editable for services
            configured: isConfigured,
            editing: false, // Services don't need editing
          };
        });
        // Initialize selected arrays from itemsList
        selectedProducts = itemsList.filter((i) => i.type === "product").map((i) => i.id);
        selectedServices = itemsList.filter((i) => i.type === "service").map((i) => i.id);
        errors = {};
        
        // Check if price was manually set (Patrón 3: Híbrido)
        // Use setTimeout to ensure itemsList and products are fully loaded
        setTimeout(() => {
          const currentType = inferPackageType(
            itemsList.map((item) => ({
              product_id: item.type === "product" ? item.id : undefined,
              service_id: item.type === "service" ? item.id : undefined,
              quantity: item.quantity,
              duration_minutes: item.duration_minutes,
            }))
          );
          const calculated = calculatePackagePrice(itemsList, $productsAdminStore.list);
          isPriceManual = !isPriceAutoCalculated(
            package_.price_cents,
            calculated,
            currentType
          );
        }, 0);
      } else {
        // Create mode: initialize empty form
        formData = {
          name: "",
          sucursales_ids: sucursalId ? [sucursalId] : [],
          description: "",
          price_cents: 0,
          included_items: [],
          active: true,
        };
        priceInput = "";
        itemsList = [];
        selectedProducts = [];
        selectedServices = [];
        isPriceManual = false; // Reset manual flag for new package
        selectedSucursal = sucursalId ? [sucursalId] : [];
        configuringItemId = null;
        errors = {};
      }
      
      // Mark as initialized and update previous values
      formInitialized = true;
      prevPackage = package_;
      prevOpen = open;
    } else if (!open) {
      // Modal closed: reset initialization flag
      formInitialized = false;
      prevPackage = null;
      prevOpen = false;
    }
  }

  // Sync selectedSucursal to formData.sucursales_ids
  $: formData.sucursales_ids = selectedSucursal;

  $: availableProducts = $productsAdminStore.list.filter((p) => p.active !== false);
  $: availableServices = $servicesAdminStore.list.filter((s) => s.active !== false);

  // Infer package type from items (Opción A: Inferido)
  $: packageType = inferPackageType(
    itemsList.map((item) => ({
      product_id: item.type === "product" ? item.id : undefined,
      service_id: item.type === "service" ? item.id : undefined,
      quantity: item.quantity,
      duration_minutes: item.duration_minutes,
    }))
  );

  // Calculate automatic price for products (Patrón 3: Híbrido)
  $: calculatedPriceCents = calculatePackagePrice(itemsList, availableProducts);

  // Determine if price should be auto-calculated or manual
  $: shouldAutoCalculate = packageType !== "service" && !isPriceManual;

  // Update price input reactively when calculated price changes (only if auto-calculate)
  $: if (shouldAutoCalculate && calculatedPriceCents > 0) {
    priceInput = (calculatedPriceCents / 100).toFixed(2);
    formData.price_cents = calculatedPriceCents;
  }

  // Prepare options for MultiSelectDropdown with stock info
  $: productOptions = availableProducts.map((p): Option => ({
    value: p.id,
    label: p.name,
    disabled: p.stock_qty === 0,
    metadata: { stock_qty: p.stock_qty },
  }));

  $: serviceOptions = availableServices.map((s): Option => ({
    value: s.id,
    label: s.name,
    disabled: false,
    metadata: {},
  }));

  // Format duration for display
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

  // Handle sucursal selection (now supports multiple sucursales)
  function handleSucursalChange(selected: (string | number)[]) {
    selectedSucursal = selected.map((v) => String(v));
  }

  function validateForm(): boolean {
    errors = {};

    if (!formData.name.trim()) {
      errors.name = "Nombre es requerido";
    }

    if (!formData.sucursales_ids || formData.sucursales_ids.length === 0) {
      errors.sucursal_id = "Al menos una sucursal es requerida";
    }

    if (formData.price_cents <= 0) {
      errors.price = "Precio debe ser mayor a 0";
    }

    if (itemsList.length === 0) {
      errors.items = "Al menos un item es requerido";
    }

    // Validate all items are configured
    // Products need quantity, services are always configured (included as-is)
    const unconfiguredItems = itemsList.filter((item) => 
      item.type === "product" && !item.configured
    );
    if (unconfiguredItems.length > 0) {
      errors.items = "Todos los productos deben tener cantidad configurada";
    }

    // Validate stock for products
    for (const item of itemsList) {
      if (item.type === "product") {
        const product = availableProducts.find((p) => p.id === item.id);
        if (product && item.quantity && item.quantity > product.stock_qty) {
          errors.items = `Stock insuficiente para ${item.name}. Disponible: ${product.stock_qty}`;
          break;
        }
      }
    }

    return Object.keys(errors).length === 0;
  }

  // Handle product selection
  function handleProductsChange(selected: (string | number)[]) {
    selectedProducts = selected.map((v) => String(v));
    
    // Add new products to itemsList
    for (const productId of selectedProducts) {
      if (!itemsList.some((item) => item.id === productId && item.type === "product")) {
        const product = availableProducts.find((p) => p.id === productId);
        if (product) {
          const defaultQuantity = 1;
          const isValid = product.stock_qty >= defaultQuantity;
          itemsList = [
            ...itemsList,
            {
              type: "product",
              id: productId,
              name: product.name,
              quantity: defaultQuantity,
              configured: isValid, // Auto-configure if stock is available
              editing: !isValid, // Start editing if stock is insufficient
            },
          ];
          if (!isValid) {
            configuringItemId = productId; // Start configuring this item
          }
        }
      }
    }

    // Remove unselected products
    itemsList = itemsList.filter((item) => 
      item.type !== "product" || selectedProducts.includes(item.id)
    );
  }

  // Handle service selection
  function handleServicesChange(selected: (string | number)[]) {
    selectedServices = selected.map((v) => String(v));
    
    // Add new services to itemsList
    // Services in packages are included as-is (no timer, no duration tracking needed)
    for (const serviceId of selectedServices) {
      if (!itemsList.some((item) => item.id === serviceId && item.type === "service")) {
        const service = availableServices.find((s) => s.id === serviceId);
        if (service) {
          // Services in packages don't need duration_minutes (they're included, not timed)
          // But we still need to store a default duration for backend validation
          const defaultDuration = service.durations_allowed?.[0] || 30; // Default to 30 min if none
          itemsList = [
            ...itemsList,
            {
              type: "service",
              id: serviceId,
              name: service.name,
              duration_minutes: defaultDuration, // Stored for backend, but not displayed/editable
              configured: true, // Services are always configured (no editing needed)
              editing: false, // Services don't need editing
            },
          ];
        }
      }
    }

    // Remove unselected services
    itemsList = itemsList.filter((item) => 
      item.type !== "service" || selectedServices.includes(item.id)
    );
  }

  // Handle quantity change for products
  function handleQuantityChange(itemId: string, quantity: number) {
    itemsList = itemsList.map((item) => {
      if (item.id === itemId && item.type === "product") {
        const product = availableProducts.find((p) => p.id === itemId);
        const isValid = product ? quantity > 0 && quantity <= product.stock_qty : quantity > 0;
        return {
          ...item,
          quantity,
          configured: isValid,
        };
      }
      return item;
    });
  }

  // Handle duration change for services
  function handleDurationChange(itemId: string, durationMinutes: number) {
    itemsList = itemsList.map((item) => {
      if (item.id === itemId && item.type === "service") {
        const service = availableServices.find((s) => s.id === itemId);
        const isValid = service 
          ? service.durations_allowed?.includes(durationMinutes) || false
          : durationMinutes > 0;
        return {
          ...item,
          duration_minutes: durationMinutes,
          configured: isValid,
        };
      }
      return item;
    });
  }

  // Toggle edit mode for item
  function toggleEditItem(itemId: string) {
    itemsList = itemsList.map((item) => ({
      ...item,
      editing: item.id === itemId ? !item.editing : false,
    }));
    configuringItemId = itemsList.find((i) => i.id === itemId && i.editing)?.id || null;
  }

  // Remove item
  function removeItem(itemId: string) {
    itemsList = itemsList.filter((item) => item.id !== itemId);
    // Also remove from selected arrays
    selectedProducts = selectedProducts.filter((id) => id !== itemId);
    selectedServices = selectedServices.filter((id) => id !== itemId);
  }

  async function handleSubmit() {
    if (!validateForm()) {
      return;
    }

    loading = true;
    errors = {};

    try {
      // Parse price
      const priceValue = parseFloat(priceInput);
      if (isNaN(priceValue) || priceValue <= 0) {
        errors.price = "Precio inválido";
        loading = false;
        return;
      }
      formData.price_cents = Math.round(priceValue * 100);

      // Convert itemsList to included_items format
      formData.included_items = itemsList.map((item) => ({
        product_id: item.type === "product" ? item.id : undefined,
        service_id: item.type === "service" ? item.id : undefined,
        quantity: item.quantity,
        duration_minutes: item.duration_minutes,
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
  title={package_ ? "Editar Paquete" : "Crear Paquete"}
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

    <!-- Precio -->
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
      {#if packageType !== "service" && calculatedPriceCents > 0}
        <div class="price-actions">
          {#if isPriceManual}
            <button
              type="button"
              class="btn-reset-price"
              on:click={resetToCalculatedPrice}
              disabled={loading}
              title="Restaurar precio calculado automáticamente"
              aria-label="Restaurar precio calculado"
            >
              <RotateCcw size={16} />
              <span>Restaurar</span>
            </button>
          {/if}
          <span class="price-indicator" class:manual={isPriceManual}>
            {#if isPriceManual}
              <Info size={14} />
              Manual
            {:else}
              <Info size={14} />
              Auto-calculado
            {/if}
          </span>
        </div>
      {:else if packageType === "service"}
        <span class="price-indicator manual">
          <Info size={14} />
          Manual (servicios)
        </span>
      {/if}
    </div>
    <p id="help-price" class="help-text">
      {#if packageType === "service"}
        Precio de venta del paquete en pesos mexicanos (MXN). Los servicios no tienen precio individual en paquetes.
      {:else if packageType === "product"}
        Precio calculado automáticamente desde los productos incluidos. Puedes editarlo manualmente si es necesario.
      {:else}
        Precio calculado automáticamente desde los productos incluidos. Los servicios no afectan el precio. Puedes editarlo manualmente si es necesario.
      {/if}
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

      <!-- Items Section - Patrón 5 (Híbrido) -->
      <div class="items-section">
        <h3 class="section-title">Items Incluidos</h3>

        <!-- Productos Selection -->
        <div class="items-selection-group">
          <MultiSelectDropdown
            options={productOptions}
            selectedValues={selectedProducts}
            placeholder="Seleccionar productos"
            label="Productos"
            disabled={loading}
            error={false}
            required={false}
            showMetadata={true}
            ariaDescribedBy="help-products"
            on:change={(e) => handleProductsChange(e.detail)}
          />
          <p id="help-products" class="help-text">
            Selecciona uno o más productos para incluir en el paquete. Los productos sin stock aparecen deshabilitados.
          </p>
        </div>

        <!-- Servicios Selection -->
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

        <!-- Items List with Inline Configuration -->
        {#if itemsList.length > 0}
          <div class="items-list">
            {#each itemsList as item (item.id)}
              <div class="item-card" class:configured={item.configured} class:editing={item.editing}>
                <div class="item-header">
                  <div class="item-info">
                    <strong>{item.name}</strong>
                    <span class="item-type-badge">{item.type === "product" ? "Producto" : "Servicio"}</span>
                    {#if item.configured}
                      {#if item.type === "product"}
                        <span class="item-config-display">Cantidad: {item.quantity}</span>
                      {:else}
                        <span class="item-config-display item-service-note">Incluido (sin timer)</span>
                      {/if}
                    {:else}
                      <span class="item-config-warning">⚠️ Configuración pendiente</span>
                    {/if}
                  </div>
                  <div class="item-actions">
                    {#if item.type === "product"}
                      <!-- Products can be edited (quantity) -->
                      <button
                        type="button"
                        class="btn-icon"
                        on:click={() => toggleEditItem(item.id)}
                        disabled={loading}
                        aria-label={item.editing ? "Cancelar edición" : "Editar"}
                      >
                        <Edit2 size={16} />
                      </button>
                    {/if}
                    <!-- Both products and services can be removed -->
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

                <!-- Inline Configuration (only for products) -->
                {#if item.type === "product" && (item.editing || !item.configured)}
                  <div class="item-config-wrapper">
                    <PackageItemConfig
                      itemType="product"
                      product={availableProducts.find((p) => p.id === item.id)}
                      quantity={item.quantity || 1}
                      onQuantityChange={(qty) => handleQuantityChange(item.id, qty)}
                      error={undefined}
                      disabled={loading}
                    />
                  </div>
                {/if}
              </div>
            {/each}
          </div>
        {:else}
          <p class="help-text">No hay items agregados. Selecciona productos o servicios arriba para agregarlos al paquete.</p>
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
  .package-form {
    display: flex;
    flex-direction: column;
  }

  /* Input Wrapper - Estilo simplificado como ProductForm */
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

  .btn-reset-price {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 12px;
    background: var(--accent-primary, #3b82f6);
    color: white;
    border: none;
    border-radius: 6px;
    font-size: 0.875rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .btn-reset-price:hover:not(:disabled) {
    background: var(--accent-primary-hover, #2563eb);
    transform: translateY(-1px);
  }

  .btn-reset-price:disabled {
    opacity: 0.5;
    cursor: not-allowed;
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

  .item-card.editing {
    border-color: var(--accent-primary, #0093f7);
    box-shadow: 0 0 0 3px rgba(0, 147, 247, 0.1);
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

  .item-config-warning {
    color: var(--accent-warning, #f59e0b);
    font-size: 0.875rem;
    font-weight: 500;
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

  .item-config-wrapper {
    margin-top: var(--spacing-md);
    padding-top: var(--spacing-md);
    border-top: 1px solid var(--border-primary);
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
  @media (max-width: 640px) {
    .form-footer {
      flex-direction: column;
    }

    .item-header {
      flex-direction: column;
      align-items: stretch;
    }

    .item-actions {
      justify-content: flex-end;
    }
  }
</style>












