<script lang="ts">
  /**
   * ProductForm component - Create/Edit product modal form.
   */
  import { Modal } from "@kidyland/ui";
  import { AlertCircle } from "lucide-svelte";
  import type { Product } from "@kidyland/shared/types";
  import type { ProductCreate, ProductUpdate } from "$lib/stores/products-admin";
  import { createProduct, updateProduct } from "$lib/stores/products-admin";
  import { fetchAllSucursales, sucursalesAdminStore } from "$lib/stores/sucursales-admin";
  import MultiSelectDropdown from "$lib/components/shared/MultiSelectDropdown.svelte";
  import { createEventDispatcher } from "svelte";

  // Option interface for MultiSelectDropdown (matches MultiSelectDropdown.svelte)
  interface Option {
    value: string | number;
    label: string;
  }

  export let open = false;
  export let product: Product | null = null; // If provided, edit mode; otherwise, create mode
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

  // Form state
  let formData: ProductCreate = {
    name: "",
    sucursales_ids: sucursalId ? [sucursalId] : [],
    price_cents: 0,
    stock_qty: 0,
    threshold_alert_qty: 0,
    enabled_for_package: false,
    package_deduction_qty: 0,
    active: true,
  };

  let selectedSucursales: string[] = []; // Selected sucursales from multi-select
  let priceInput = "";
  let packageDeductionInput = "";
  let errors: Record<string, string> = {};
  let loading = false;

  // Guard flag and previous value tracking for form initialization (Patrón 4: Híbrido)
  // Prevents reactive statement from re-executing during user input
  let formInitialized = false;
  let prevProduct: Product | null = null;
  let prevOpen = false;

  // Convert sucursales to Option format
  $: sucursalOptions = $sucursalesAdminStore.list
    .filter((s) => s.active)
    .map((s) => ({
      value: s.id,
      label: `${s.identifier} - ${s.name}`,
    })) as Option[];

  // Initialize form when product or open changes (Patrón 4: Híbrido con guard flag y previous value tracking)
  // Only executes when product/open actually change, not during user input
  $: {
    // Check if product or open actually changed (not just re-evaluated)
    const productChanged = product !== prevProduct;
    const openChanged = open !== prevOpen;
    
    // Only initialize if:
    // 1. Modal is opening (open changed from false to true) OR
    // 2. Product actually changed (different product object) OR
    // 3. Form hasn't been initialized yet for this open state
    const shouldInitialize = open && (openChanged || productChanged || !formInitialized);
    
    if (shouldInitialize) {
      if (product) {
        // Edit mode: initialize from product
        const productSucursales = product.sucursales_ids || (product.sucursal_id ? [product.sucursal_id] : []);
        formData = {
          name: product.name,
          sucursales_ids: productSucursales,
          price_cents: product.price_cents,
          stock_qty: product.stock_qty,
          threshold_alert_qty: product.threshold_alert_qty,
          enabled_for_package: product.enabled_for_package,
          package_deduction_qty: product.package_deduction_qty,
          active: product.active !== false,
        };
        selectedSucursales = productSucursales;
        priceInput = (product.price_cents / 100).toFixed(2);
        packageDeductionInput = (product.package_deduction_qty / 100).toFixed(2);
        errors = {};
      } else {
        // Create mode: initialize empty form
        const defaultSucursales = sucursalId ? [sucursalId] : [];
        formData = {
          name: "",
          sucursales_ids: defaultSucursales,
          price_cents: 0,
          stock_qty: 0,
          threshold_alert_qty: 0,
          enabled_for_package: false,
          package_deduction_qty: 0,
          active: true,
        };
        selectedSucursales = defaultSucursales;
        priceInput = "";
        packageDeductionInput = "";
        errors = {};
      }
      
      // Mark as initialized and update previous values
      formInitialized = true;
      prevProduct = product;
      prevOpen = open;
    } else if (!open) {
      // Modal closed: reset initialization flag
      formInitialized = false;
      prevProduct = null;
      prevOpen = false;
    }
  }

  // Sync selectedSucursales to formData.sucursales_ids (always sync, even if empty)
  $: formData.sucursales_ids = [...selectedSucursales];

  function validateForm(): boolean {
    errors = {};

    if (!formData.name.trim()) {
      errors.name = "Nombre es requerido";
    }

    // Validate sucursales_ids (required for creation)
    if (!selectedSucursales || selectedSucursales.length === 0) {
      errors.sucursales = "Al menos una sucursal es requerida";
    }

    // Validate price from input (before conversion to cents)
    const priceValue = parseFloat(priceInput);
    if (isNaN(priceValue) || priceValue <= 0) {
      errors.price = "Precio debe ser mayor a 0";
    }

    if ((formData.stock_qty ?? 0) < 0) {
      errors.stock = "Stock no puede ser negativo";
    }

    if ((formData.threshold_alert_qty ?? 0) < 0) {
      errors.threshold = "Umbral de alerta no puede ser negativo";
    }

    // Validate package deduction if enabled
    if (formData.enabled_for_package) {
      const deductionValue = parseFloat(packageDeductionInput);
      if (isNaN(deductionValue) || deductionValue < 0) {
        errors.packageDeduction = "Descuento debe ser mayor o igual a 0";
      } else {
        // Validate that deduction doesn't exceed product price
        const deductionCents = Math.round(deductionValue * 100);
        const priceCents = Math.round(priceValue * 100);
        if (deductionCents > priceCents) {
          errors.packageDeduction = "El descuento no puede ser mayor al precio del producto";
        }
      }
    }

    return Object.keys(errors).length === 0;
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

      // Parse package deduction (only if enabled for package)
      if (formData.enabled_for_package) {
        const deductionValue = parseFloat(packageDeductionInput);
        if (isNaN(deductionValue) || deductionValue < 0) {
          errors.packageDeduction = "Descuento inválido";
          loading = false;
          return;
        }
        formData.package_deduction_qty = Math.round(deductionValue * 100);
      } else {
        formData.package_deduction_qty = 0;
      }

      // Validate sucursales before submitting
      if (selectedSucursales.length === 0) {
        errors.sucursales = "Al menos una sucursal es requerida";
        loading = false;
        return;
      }
      formData.sucursales_ids = [...selectedSucursales];

      if (product) {
        // Update mode
        const updateData: ProductUpdate = {
          name: formData.name,
          price_cents: formData.price_cents,
          stock_qty: formData.stock_qty,
          threshold_alert_qty: formData.threshold_alert_qty,
          enabled_for_package: formData.enabled_for_package,
          package_deduction_qty: formData.package_deduction_qty,
          active: formData.active,
          sucursales_ids: formData.sucursales_ids,
        };
        const updated = await updateProduct(product.id, updateData);
        if (updated) {
          dispatch("success");
        }
      } else {
        // Create mode - backend will derive sucursal_id from sucursales_ids if needed
        const createData: ProductCreate = {
          name: formData.name,
          sucursales_ids: formData.sucursales_ids,
          price_cents: formData.price_cents,
          stock_qty: formData.stock_qty,
          threshold_alert_qty: formData.threshold_alert_qty,
          enabled_for_package: formData.enabled_for_package,
          package_deduction_qty: formData.package_deduction_qty,
          active: formData.active !== false,
        };
        const created = await createProduct(createData);
        if (created) {
          dispatch("success");
        }
      }
    } catch (error: any) {
      // Better error handling for API errors
      let errorMessage = "Error al guardar producto";
      if (error?.response?.data?.detail) {
        // FastAPI validation errors
        if (typeof error.response.data.detail === "string") {
          errorMessage = error.response.data.detail;
        } else if (Array.isArray(error.response.data.detail)) {
          // Multiple validation errors - format them nicely
          const errorDetails = error.response.data.detail
            .map((err: any) => {
              const field = err?.loc?.[err.loc.length - 1] || "campo";
              const msg = err?.msg || JSON.stringify(err);
              return `${field}: ${msg}`;
            })
            .join(", ");
          errorMessage = `Errores de validación: ${errorDetails}`;
        } else {
          errorMessage = JSON.stringify(error.response.data.detail);
        }
      } else if (error?.message) {
        errorMessage = error.message;
      }
      errors.submit = errorMessage;
      
      // Log full error for debugging
      if (typeof window !== 'undefined' && import.meta.env?.DEV) {
        console.error('[ProductForm] Error creating/updating product:', {
          error,
          response: error?.response,
          formData,
        });
      }
    } finally {
      loading = false;
    }
  }
</script>

<Modal 
  open={open} 
  title={product ? "Editar Producto" : "Crear Producto"}
  size="lg"
  anchorPosition={null}
  on:close={() => dispatch("close")}
>
  <form on:submit|preventDefault={handleSubmit} class="product-form">
    <!-- Sucursales MultiSelect -->
    <div class="sucursales-dropdown-wrapper">
      <MultiSelectDropdown
        options={sucursalOptions}
        selectedValues={selectedSucursales}
        placeholder="Seleccionar sucursales *"
        label="Sucursales"
        disabled={loading || ($sucursalesAdminStore.loading && sucursalOptions.length === 0)}
        error={!!errors.sucursales}
        required={true}
        ariaDescribedBy="help-sucursales"
        on:change={(event) => {
          selectedSucursales = event.detail.map((val) => String(val));
        }}
      />
    </div>
    <p id="help-sucursales" class="help-text">
      Selecciona una o más sucursales donde estará disponible este producto
    </p>
    {#if errors.sucursales}
      <p class="error-text">
        <AlertCircle size={14} />
        {errors.sucursales}
      </p>
    {/if}

    <!-- Nombre del Producto -->
    <div class="input-wrapper">
      <input
        id="product-name"
        type="text"
        bind:value={formData.name}
        placeholder="Nombre del Producto *"
        required
        disabled={loading}
        class="input"
        class:error={!!errors.name}
        aria-describedby="help-product-name"
      />
    </div>
    <p id="help-product-name" class="help-text">
      Ingresa el nombre del producto (ej: Nachos, Refresco, Palomitas)
    </p>
    {#if errors.name}
      <p class="error-text">
        <AlertCircle size={14} />
        {errors.name}
      </p>
    {/if}

    <!-- Precio -->
    <div class="input-wrapper">
      <input
        id="price"
        type="number"
        step="0.01"
        min="0"
        bind:value={priceInput}
        placeholder="Precio (en pesos) *"
        required
        disabled={loading}
        class="input"
        class:error={!!errors.price}
        aria-describedby="help-price"
      />
    </div>
    <p id="help-price" class="help-text">
      Precio de venta del producto en pesos mexicanos (MXN)
    </p>
    {#if errors.price}
      <p class="error-text">
        <AlertCircle size={14} />
        {errors.price}
      </p>
    {/if}

    <!-- Stock Disponible -->
    <div class="input-wrapper">
      <input
        id="stock"
        type="number"
        min="0"
        bind:value={formData.stock_qty}
        placeholder="Stock Disponible"
        disabled={loading}
        class="input"
        class:error={!!errors.stock}
        aria-describedby="help-stock"
      />
    </div>
    <p id="help-stock" class="help-text">
      Cantidad disponible en inventario. Se actualiza automáticamente al realizar ventas.
    </p>
    {#if errors.stock}
      <p class="error-text">
        <AlertCircle size={14} />
        {errors.stock}
      </p>
    {/if}

    <!-- Umbral de Alerta de Stock -->
    <div class="input-wrapper">
      <input
        id="threshold"
        type="number"
        min="0"
        bind:value={formData.threshold_alert_qty}
        placeholder="Umbral de Alerta de Stock"
        disabled={loading}
        class="input"
        class:error={!!errors.threshold}
        aria-describedby="help-threshold"
      />
    </div>
    <p id="help-threshold" class="help-text">
      Se alertará cuando el stock esté en o por debajo de este valor
    </p>
    {#if errors.threshold}
      <p class="error-text">
        <AlertCircle size={14} />
        {errors.threshold}
      </p>
    {/if}

    <!-- Disponible para Paquetes -->
    <div class="checkbox-wrapper">
      <label class="checkbox-label">
        <input
          id="enabled-for-package"
          type="checkbox"
          bind:checked={formData.enabled_for_package}
          disabled={loading}
          aria-describedby="help-enabled-for-package"
        />
        Disponible para Paquetes
      </label>
    </div>
    <p id="help-enabled-for-package" class="help-text">
      Activa esta opción si el producto puede incluirse en paquetes promocionales
    </p>

    <!-- Descuento en Paquete -->
    {#if formData.enabled_for_package}
      <div class="input-wrapper">
        <input
          id="package-deduction"
          type="number"
          step="0.01"
          min="0"
          bind:value={packageDeductionInput}
          placeholder="0.00"
          disabled={loading}
          class="input"
          class:error={!!errors.packageDeduction}
          aria-describedby="help-package-deduction"
        />
      </div>
      <p id="help-package-deduction" class="help-text">
        Descuento en pesos mexicanos (MXN) que se aplicará al precio del producto cuando se agregue a un paquete
      </p>
      {#if errors.packageDeduction}
        <p class="error-text">
          <AlertCircle size={14} />
          {errors.packageDeduction}
        </p>
      {/if}
    {/if}

    <!-- Producto Activo -->
    <div class="checkbox-wrapper">
      <label class="checkbox-label">
        <input
          id="product-active"
          type="checkbox"
          bind:checked={formData.active}
          disabled={loading}
          aria-describedby="help-product-active"
        />
        Producto Activo
      </label>
    </div>
    <p id="help-product-active" class="help-text">
      Los productos inactivos no estarán disponibles para venta en recepción y kidibar
    </p>

    {#if errors.submit}
      <div class="error-banner">
        <AlertCircle size={16} />
        {errors.submit}
      </div>
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
        {loading ? "Guardando..." : product ? "Actualizar" : "Crear"}
      </button>
    </div>
  </form>
</Modal>

<style>
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
    padding: var(--spacing-md) var(--spacing-lg);
    border-radius: var(--radius-md);
    font-size: var(--text-base);
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    border: none;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: var(--spacing-xs);
  }

  .btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .btn-secondary {
    background: var(--theme-bg-secondary);
    color: var(--text-primary);
    border: 1px solid var(--border-primary);
  }

  .btn-secondary:hover:not(:disabled) {
    background: var(--theme-bg-elevated);
    transform: translateY(-1px);
    box-shadow: var(--shadow-sm);
  }

  .btn-primary {
    background: var(--accent-primary);
    color: white;
  }

  .btn-primary:hover:not(:disabled) {
    background: #0078c7;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(0, 147, 247, 0.3);
  }

  .sucursales-dropdown-wrapper {
    margin-bottom: 16px;
  }

  @media (max-width: 768px) {
    .form-footer {
      flex-direction: column;
    }

    .btn {
      width: 100%;
    }
  }
</style>











