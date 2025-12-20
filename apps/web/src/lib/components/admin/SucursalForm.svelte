<script lang="ts">
  /**
   * SucursalForm component - Create/Edit sucursal modal form.
   */
  import { Modal } from "@kidyland/ui";
  import { AlertCircle } from "lucide-svelte";
  import type { Sucursal } from "@kidyland/shared/types";
  import type { SucursalCreate, SucursalUpdate } from "$lib/stores/sucursales-admin";
  import { createSucursal, updateSucursal } from "$lib/stores/sucursales-admin";
  import { createEventDispatcher } from "svelte";

  export let open = false;
  export let sucursal: Sucursal | null = null; // If provided, edit mode; otherwise, create mode

  const dispatch = createEventDispatcher();

  // Form state
  let formData: SucursalCreate = {
    identifier: "",
    name: "",
    address: "",
    timezone: "America/Mexico_City",
    active: true,
  };

  let errors: Record<string, string> = {};
  let loading = false;

  // Guard flag and previous value tracking for form initialization (Patrón 4: Híbrido)
  // Prevents reactive statement from re-executing during user input
  let formInitialized = false;
  let prevSucursal: Sucursal | null = null;
  let prevOpen = false;

  // Common timezones for Mexico
  const timezones = [
    { value: "America/Mexico_City", label: "Ciudad de México (GMT-6)" },
    { value: "America/Tijuana", label: "Tijuana (GMT-8)" },
    { value: "America/Hermosillo", label: "Hermosillo (GMT-7)" },
    { value: "America/Mazatlan", label: "Mazatlán (GMT-7)" },
    { value: "America/Merida", label: "Mérida (GMT-6)" },
    { value: "America/Monterrey", label: "Monterrey (GMT-6)" },
    { value: "America/Chihuahua", label: "Chihuahua (GMT-7)" },
  ];

  // Initialize form when sucursal or open changes (Patrón 4: Híbrido con guard flag y previous value tracking)
  // Only executes when sucursal/open actually change, not during user input
  $: {
    // Check if sucursal or open actually changed (not just re-evaluated)
    const sucursalChanged = sucursal !== prevSucursal;
    const openChanged = open !== prevOpen;
    
    // Only initialize if:
    // 1. Modal is opening (open changed from false to true) OR
    // 2. Sucursal actually changed (different sucursal object) OR
    // 3. Form hasn't been initialized yet for this open state
    const shouldInitialize = open && (openChanged || sucursalChanged || !formInitialized);
    
    if (shouldInitialize) {
      if (sucursal) {
        // Edit mode: initialize from sucursal
        formData = {
          identifier: sucursal.identifier,
          name: sucursal.name,
          address: sucursal.address || "",
          timezone: sucursal.timezone,
          active: sucursal.active,
        };
        errors = {};
      } else {
        // Create mode: initialize empty form
        formData = {
          identifier: "",
          name: "",
          address: "",
          timezone: "America/Mexico_City",
          active: true,
        };
        errors = {};
      }
      
      // Mark as initialized and update previous values
      formInitialized = true;
      prevSucursal = sucursal;
      prevOpen = open;
    } else if (!open) {
      // Modal closed: reset initialization flag
      formInitialized = false;
      prevSucursal = null;
      prevOpen = false;
    }
  }

  function validateForm(): boolean {
    errors = {};

    if (!formData.identifier.trim()) {
      errors.identifier = "Identificador es requerido";
    } else if (formData.identifier.trim().length > 20) {
      errors.identifier = "El identificador no puede exceder 20 caracteres";
    } else if (!/^[a-z0-9_-]+$/i.test(formData.identifier.trim())) {
      errors.identifier = "El identificador solo puede contener letras, números, guiones y guiones bajos";
    }

    if (!formData.name.trim()) {
      errors.name = "Nombre es requerido";
    }

    if (formData.name.length > 100) {
      errors.name = "El nombre no puede exceder 100 caracteres";
    }

    if (formData.address && formData.address.length > 255) {
      errors.address = "La dirección no puede exceder 255 caracteres";
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
      if (sucursal) {
        // Update mode
        const updateData: SucursalUpdate = {
          identifier: formData.identifier,
          name: formData.name,
          address: formData.address || undefined,
          timezone: formData.timezone,
          active: formData.active,
        };
        const updated = await updateSucursal(sucursal.id, updateData);
        if (updated) {
          dispatch("success");
        }
      } else {
        // Create mode
        const created = await createSucursal(formData);
        if (created) {
          dispatch("success");
        }
      }
    } catch (error: any) {
      errors.submit = error.message || "Error al guardar sucursal";
    } finally {
      loading = false;
    }
  }
</script>

<Modal 
  open={open} 
  title={sucursal ? "Editar Sucursal" : "Crear Sucursal"}
  size="lg"
  anchorPosition={null}
  on:close={() => dispatch("close")}
>
  <form on:submit|preventDefault={handleSubmit} class="sucursal-form">
    <!-- Identificador -->
    <div class="input-wrapper">
      <input
        id="identifier"
        type="text"
        bind:value={formData.identifier}
        placeholder="Identificador *"
        required
        disabled={loading}
        maxlength="20"
        class="input"
        class:error={!!errors.identifier}
        aria-describedby="help-identifier"
      />
    </div>
    <p id="help-identifier" class="help-text">
      Código único para identificar la sucursal. Solo letras, números, guiones y guiones bajos (máx. 20 caracteres)
    </p>
    {#if errors.identifier}
      <p class="error-text">
        <AlertCircle size={14} />
        {errors.identifier}
      </p>
    {/if}

    <!-- Nombre -->
    <div class="input-wrapper">
      <input
        id="name"
        type="text"
        bind:value={formData.name}
        placeholder="Nombre *"
        required
        disabled={loading}
        class="input"
        class:error={!!errors.name}
        aria-describedby="help-name"
      />
    </div>
    <p id="help-name" class="help-text">
      Nombre completo de la sucursal (ej: Sucursal Centro, Sucursal Norte)
    </p>
    {#if errors.name}
      <p class="error-text">
        <AlertCircle size={14} />
        {errors.name}
      </p>
    {/if}

    <!-- Dirección -->
    <div class="input-wrapper">
      <input
        id="address"
        type="text"
        bind:value={formData.address}
        placeholder="Dirección"
        disabled={loading}
        class="input"
        class:error={!!errors.address}
        aria-describedby="help-address"
      />
    </div>
    <p id="help-address" class="help-text">
      Dirección física de la sucursal (opcional)
    </p>
    {#if errors.address}
      <p class="error-text">
        <AlertCircle size={14} />
        {errors.address}
      </p>
    {/if}

    <!-- Zona Horaria -->
    <div class="input-wrapper">
      <select
        id="timezone"
        class="input select"
        bind:value={formData.timezone}
        disabled={loading}
        aria-describedby="help-timezone"
      >
        {#each timezones as tz}
          <option value={tz.value}>{tz.label}</option>
        {/each}
      </select>
    </div>
    <p id="help-timezone" class="help-text">
      Zona horaria donde se encuentra la sucursal. Se usa para reportes y registros de tiempo
    </p>

    <!-- Activa -->
    <div class="checkbox-wrapper">
      <label class="checkbox-label">
        <input
          id="active-checkbox"
          type="checkbox"
          bind:checked={formData.active}
          disabled={loading}
          aria-describedby="help-active"
        />
        <span>Activa</span>
      </label>
      <p id="help-active" class="help-text">
        Las sucursales inactivas no aparecerán en las listas de selección
      </p>
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
        {loading ? "Guardando..." : sucursal ? "Actualizar" : "Crear"}
      </button>
    </div>
  </form>
</Modal>

<style>
  .sucursal-form {
    display: flex;
    flex-direction: column;
  }

  /* Input Wrapper - Estilo simplificado como UserForm */
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

  .input.select {
    cursor: pointer;
    appearance: none;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%2365657b' d='M6 9L1 4h10z'/%3E%3C/svg%3E");
    background-repeat: no-repeat;
    background-position: right 16px center;
    padding-right: 40px;
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
  }
</style>






