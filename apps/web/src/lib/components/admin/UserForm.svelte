<script lang="ts">
  /**
   * UserForm component - Create/Edit user modal form.
   */
  import { Modal } from "@kidyland/ui";
  import FloatingInput from "$lib/components/shared/FloatingInput.svelte";
  import type { User } from "@kidyland/shared/types";
  import type { UserCreate, UserUpdate } from "$lib/stores/users";
  import { createUser, updateUser, changePassword, deactivateUser } from "$lib/stores/users";
  import { createEventDispatcher, onMount } from "svelte";
  import { 
    User as UserIcon, 
    Lock, 
    Shield, 
    Building2,
    CheckCircle2,
    AlertCircle,
    Eye,
    EyeOff
  } from "lucide-svelte";
  import { fetchAllSucursales, sucursalesAdminStore } from "$lib/stores/sucursales-admin";

  export let open = false;
  export let user: User | null = null; // If provided, edit mode; otherwise, create mode
  export let anchorPosition: { top: number; left: number } | null = null;
  export let mode: "create" | "edit" | "password" | "deactivate" = "create"; // Modal mode

  const dispatch = createEventDispatcher();

  // Form state
  let formData: {
    username?: string;
    name?: string;
    role?: User["role"];
    password?: string;
    sucursal_id?: string | null;
  } = {
    username: "",
    name: "",
    role: "monitor",
    password: "",
  };

  let errors: Record<string, string> = {};
  let loading = false;
  let showPassword = false;
  let passwordStrength = 0;
  let confirmPassword = ""; // For password change mode
  
  // Estados para detectar :invalid del navegador (validación HTML5 nativa)
  let usernameInvalid = false;
  let nameInvalid = false;
  let roleInvalid = false;
  let passwordInvalid = false;

  // Guard flag and previous value tracking for form initialization (Patrón 4: Híbrido)
  // Prevents reactive statement from re-executing during user input
  let formInitialized = false;
  let prevUser: User | null = null;
  let prevOpen = false;
  let prevMode: "create" | "edit" | "password" | "deactivate" = "create";

  // Load sucursales on mount
  onMount(async () => {
    await fetchAllSucursales();
  });

  // Initialize form when user, open, or mode changes (Patrón 4: Híbrido con guard flag y previous value tracking)
  // Only executes when user/open/mode actually change, not during user input
  $: {
    // Check if user, open, or mode actually changed (not just re-evaluated)
    const userChanged = user !== prevUser;
    const openChanged = open !== prevOpen;
    const modeChanged = mode !== prevMode;
    
    // Only initialize if:
    // 1. Modal is opening (open changed from false to true) OR
    // 2. User actually changed (different user object) OR
    // 3. Mode changed OR
    // 4. Form hasn't been initialized yet for this open state
    const shouldInitialize = open && (openChanged || userChanged || modeChanged || !formInitialized);
    
    if (shouldInitialize) {
      if (user && mode !== "create") {
        // Edit mode: initialize from user
        formData = {
          name: user.name,
          username: user.username,
          role: user.role,
          sucursal_id: user.sucursal_id,
          password: "", // Empty in edit mode
        };
        errors = {};
        confirmPassword = "";
        // Reset invalid states
        usernameInvalid = false;
        nameInvalid = false;
        roleInvalid = false;
        passwordInvalid = false;
      } else if (!user && mode === "create") {
        // Create mode: initialize empty form
        formData = {
          username: "",
          name: "",
          role: "monitor",
          password: "",
          sucursal_id: null,
        };
        errors = {};
        confirmPassword = "";
        // Reset invalid states
        usernameInvalid = false;
        nameInvalid = false;
        roleInvalid = false;
        passwordInvalid = false;
      }
      
      // Mark as initialized and update previous values
      formInitialized = true;
      prevUser = user;
      prevOpen = open;
      prevMode = mode;
    } else if (!open) {
      // Modal closed: reset initialization flag
      formInitialized = false;
      prevUser = null;
      prevOpen = false;
      prevMode = "create";
    }
  }

  // Función para detectar estado :invalid del navegador
  function checkInvalidity(element: HTMLInputElement | HTMLSelectElement | null, field: 'username' | 'name' | 'role' | 'password') {
    if (!element) return;
    const isInvalid = !element.validity.valid;
    if (field === 'username') usernameInvalid = isInvalid;
    else if (field === 'name') nameInvalid = isInvalid;
    else if (field === 'role') roleInvalid = isInvalid;
    else if (field === 'password') passwordInvalid = isInvalid;
  }

  const roles: User["role"][] = [
    "super_admin",
    "admin_viewer",
    "recepcion",
    "kidibar",
    "monitor",
  ];

  const roleLabels: Record<User["role"], string> = {
    super_admin: "Super Admin",
    admin_viewer: "Admin Viewer",
    recepcion: "Recepción",
    kidibar: "Kidibar",
    monitor: "Monitor",
  };

  function validateUsername(username: string): string | null {
    if (!username) return "Username es requerido";
    if (username.length < 3 || username.length > 50) {
      return "Username debe tener entre 3 y 50 caracteres";
    }
    if (!/^[a-zA-Z0-9_]+$/.test(username)) {
      return "Username solo puede contener letras, números y guiones bajos";
    }
    return null;
  }

  function validatePassword(password: string, isEdit: boolean): string | null {
    if (isEdit && !password) return null; // Password optional in edit mode
    if (!password) return "Password es requerido";
    if (password.length < 8) {
      return "Password debe tener al menos 8 caracteres";
    }
    if (!/(?=.*[A-Z])/.test(password)) {
      return "Password debe contener al menos una mayúscula";
    }
    if (!/(?=.*\d)/.test(password)) {
      return "Password debe contener al menos un número";
    }
    return null;
  }

  function validateForm(): boolean {
    errors = {};

    if (mode === "password") {
      const passwordError = validatePassword(formData.password || "", false);
      if (passwordError) {
        errors.password = passwordError;
      }
      if (formData.password !== confirmPassword) {
        errors.confirmPassword = "Las passwords no coinciden";
      }
      return Object.keys(errors).length === 0;
    }

    if (mode === "deactivate") {
      return true; // No validation needed for deactivate
    }

    // Create or Edit mode
    if (mode === "create" || mode === "edit") {
      const usernameError = validateUsername(formData.username || "");
      if (usernameError) {
        errors.username = usernameError;
      }

      if (!formData.name || formData.name.trim().length === 0) {
        errors.name = "Nombre es requerido";
      }

      if (!formData.role) {
        errors.role = "Rol es requerido";
      }

      const passwordError = validatePassword(formData.password || "", !!user);
      if (passwordError) {
        errors.password = passwordError;
      }
    }

    return Object.keys(errors).length === 0;
  }

  async function handleSubmit() {
    if (!validateForm()) return;

    loading = true;
    try {
      if (mode === "password" && user) {
        // Change password
        const success = await changePassword(user.id, {
          new_password: formData.password!,
        });
        if (success) {
          dispatch("passwordChanged");
          dispatch("close");
        }
      } else if (mode === "deactivate" && user) {
        // Deactivate user
        const updated = await deactivateUser(user.id);
        if (updated) {
          dispatch("deactivated");
          dispatch("close");
        }
      } else if (user) {
        // Edit mode
        const updateData: UserUpdate = {
          name: formData.name,
          username: formData.username,
          role: formData.role,
          sucursal_id: formData.sucursal_id,
        };
        if (formData.password) {
          updateData.password = formData.password;
        }
        const updated = await updateUser(user.id, updateData);
        if (updated) {
          dispatch("updated");
          dispatch("close");
        }
      } else {
        // Create mode
        const createData: UserCreate = {
          username: formData.username!,
          name: formData.name!,
          role: formData.role!,
          password: formData.password!,
          sucursal_id: formData.sucursal_id,
        };
        const created = await createUser(createData);
        if (created) {
          dispatch("created");
          dispatch("close");
        }
      }
    } catch (error: any) {
      errors.submit = error.message || "Error al procesar la acción";
    } finally {
      loading = false;
    }
  }

  function handleClose() {
    dispatch("close");
  }
  
  function handleModalClose() {
    handleClose();
  }
  
  // Calculate password strength
  $: if (formData.password) {
    let strength = 0;
    if (formData.password.length >= 8) strength++;
    if (formData.password.length >= 12) strength++;
    if (/(?=.*[A-Z])/.test(formData.password)) strength++;
    if (/(?=.*\d)/.test(formData.password)) strength++;
    if (/(?=.*[!@#$%^&*])/.test(formData.password)) strength++;
    passwordStrength = Math.min(strength, 5);
  } else {
    passwordStrength = 0;
  }

  function getPasswordStrengthColor(strength: number): string {
    if (strength <= 2) return "#ef4444"; // red
    if (strength <= 3) return "#f59e0b"; // amber
    return "#10b981"; // green
  }

  function getPasswordStrengthLabel(strength: number): string {
    if (strength <= 2) return "Débil";
    if (strength <= 3) return "Media";
    return "Fuerte";
  }
</script>

<Modal 
  {open} 
  title={
    mode === "password" ? "Cambiar Password" :
    mode === "deactivate" ? "Desactivar Usuario" :
    user ? "Editar Usuario" : "Crear Usuario"
  } 
  size="lg" 
  anchorPosition={null}
  on:close={handleModalClose}
>
  {#if mode === "deactivate" && user}
    <!-- Deactivate confirmation -->
    <div class="deactivate-content">
      <p class="message">
        ¿Estás seguro de que deseas desactivar al usuario <strong>{user.username}</strong>?
      </p>
      <div class="user-info">
        <p><strong>Username:</strong> {user.username}</p>
        <p><strong>Nombre:</strong> {user.name}</p>
        <p><strong>Rol:</strong> {roleLabels[user.role]}</p>
      </div>
      {#if errors.submit}
        <div class="error-banner">{errors.submit}</div>
      {/if}
      <div class="form-footer">
        <button type="button" class="btn btn-secondary" on:click={handleClose} disabled={loading}>
          Cancelar
        </button>
        <button type="button" class="btn btn-danger" on:click={handleSubmit} disabled={loading}>
          {loading ? "Desactivando..." : "Desactivar"}
        </button>
      </div>
    </div>
  {:else if mode === "password" && user}
    <!-- Password change mode -->
    <form on:submit|preventDefault={handleSubmit} class="user-form">
      <div class="user-info">
        <p><strong>Usuario:</strong> {user.username}</p>
        <p><strong>Nombre:</strong> {user.name}</p>
      </div>

      <!-- Nueva Password -->
      <div class="input-wrapper password-wrapper">
        {#if showPassword}
          <input
            id="new-password-input"
            type="text"
            bind:value={formData.password}
            required
            disabled={loading}
            placeholder="Nueva Password *"
            class="input password-input"
            class:error={!!errors.password}
            aria-describedby="help-new-password"
          />
        {:else}
          <input
            id="new-password-input"
            type="password"
            bind:value={formData.password}
            required
            disabled={loading}
            placeholder="Nueva Password *"
            class="input password-input"
            class:error={!!errors.password}
            aria-describedby="help-new-password"
          />
        {/if}
        <button
          type="button"
          class="password-toggle"
          on:click={() => (showPassword = !showPassword)}
          disabled={loading}
          aria-label={showPassword ? "Ocultar contraseña" : "Mostrar contraseña"}
        >
          {#if showPassword}
            <EyeOff size={18} />
          {:else}
            <Eye size={18} />
          {/if}
        </button>
      </div>
      <p id="help-new-password" class="help-text">
        Mínimo 8 caracteres. Incluye mayúsculas, minúsculas, números y símbolos para mayor seguridad
      </p>
      {#if formData.password}
        <div class="password-strength">
          <div class="password-strength-bars">
            {#each Array(5) as _, i}
              <div
                class="strength-bar"
                class:active={i < passwordStrength}
                style="background-color: {i < passwordStrength ? getPasswordStrengthColor(passwordStrength) : 'var(--border-primary)'}"
              ></div>
            {/each}
          </div>
          <span class="strength-label" style="color: {getPasswordStrengthColor(passwordStrength)}">
            {getPasswordStrengthLabel(passwordStrength)}
          </span>
        </div>
      {/if}
      {#if errors.password}
        <p class="error-text">
          <AlertCircle size={14} />
          {errors.password}
        </p>
      {/if}

      <!-- Confirmar Password -->
      <div class="input-wrapper">
        <input
          id="confirm-password-input"
          type="password"
          bind:value={confirmPassword}
          required
          disabled={loading}
          placeholder="Confirmar Password *"
          class="input"
          class:error={!!errors.confirmPassword}
          aria-describedby="help-confirm-password"
        />
      </div>
      <p id="help-confirm-password" class="help-text">
        Ingresa la misma contraseña para confirmar que la escribiste correctamente
      </p>
      {#if errors.confirmPassword}
        <p class="error-text">
          <AlertCircle size={14} />
          {errors.confirmPassword}
        </p>
      {/if}

      {#if errors.submit}
        <div class="error-banner">{errors.submit}</div>
      {/if}

      <div class="form-footer">
        <button type="button" class="btn btn-secondary" on:click={handleClose} disabled={loading}>
          Cancelar
        </button>
        <button type="submit" class="btn btn-primary" disabled={loading}>
          {loading ? "Cambiando..." : "Cambiar Password"}
        </button>
      </div>
    </form>
  {:else}
    <!-- Create or Edit mode -->
    <form on:submit|preventDefault={handleSubmit} class="user-form">
      <!-- Username -->
      <div class="input-wrapper">
        <input
          id="username-input"
          type="text"
          bind:value={formData.username}
          disabled={loading || !!user}
          placeholder="Username *"
          class="input"
          class:error={!!errors.username || usernameInvalid}
          aria-describedby="help-username"
          on:input={(e) => checkInvalidity(e.currentTarget, 'username')}
          on:blur={(e) => checkInvalidity(e.currentTarget, 'username')}
        />
      </div>
      <p id="help-username" class="help-text">
        Nombre de usuario único para iniciar sesión (ej: jperez, admin)
      </p>
      {#if errors.username}
        <p class="error-text">
          <AlertCircle size={14} />
          {errors.username}
        </p>
      {/if}

      <!-- Name -->
      <div class="input-wrapper">
        <input
          id="name-input"
          type="text"
          bind:value={formData.name}
          disabled={loading}
          placeholder="Nombre Completo *"
          class="input"
          class:error={!!errors.name || nameInvalid}
          aria-describedby="help-name"
          on:input={(e) => checkInvalidity(e.currentTarget, 'name')}
          on:blur={(e) => checkInvalidity(e.currentTarget, 'name')}
        />
      </div>
      <p id="help-name" class="help-text">
        Nombre completo del usuario (ej: Juan Pérez)
      </p>
      {#if errors.name}
        <p class="error-text">
          <AlertCircle size={14} />
          {errors.name}
        </p>
      {/if}

      <!-- Role -->
      <div class="input-wrapper">
        <select
          id="role-select"
          bind:value={formData.role}
          disabled={loading}
          class="input"
          class:error={!!errors.role || roleInvalid}
          aria-describedby="help-role"
          on:blur={(e) => checkInvalidity(e.currentTarget, 'role')}
          on:change={(e) => checkInvalidity(e.currentTarget, 'role')}
        >
          <option value="" disabled selected>Rol *</option>
          {#each roles as role}
            <option value={role}>{roleLabels[role]}</option>
          {/each}
        </select>
      </div>
      <p id="help-role" class="help-text">
        Rol que determina los permisos y acceso del usuario
      </p>
      {#if errors.role}
        <p class="error-text">
          <AlertCircle size={14} />
          {errors.role}
        </p>
      {/if}

      <!-- Password -->
      <div class="input-wrapper password-wrapper">
        {#if showPassword}
          <input
            id="password-input"
            type="text"
            bind:value={formData.password}
            required={!user}
            disabled={loading}
            placeholder={user ? "Nueva Password (opcional)" : "Password *"}
            class="input password-input"
            class:error={!!errors.password || passwordInvalid}
            aria-describedby="help-password"
            on:blur={(e) => checkInvalidity(e.currentTarget, 'password')}
            on:input={(e) => checkInvalidity(e.currentTarget, 'password')}
          />
        {:else}
          <input
            id="password-input"
            type="password"
            bind:value={formData.password}
            required={!user}
            disabled={loading}
            placeholder={user ? "Nueva Password (opcional)" : "Password *"}
            class="input password-input"
            class:error={!!errors.password || passwordInvalid}
            aria-describedby="help-password"
            on:blur={(e) => checkInvalidity(e.currentTarget, 'password')}
            on:input={(e) => checkInvalidity(e.currentTarget, 'password')}
          />
        {/if}
        <button
          type="button"
          class="password-toggle"
          on:click={() => (showPassword = !showPassword)}
          disabled={loading}
          aria-label={showPassword ? "Ocultar contraseña" : "Mostrar contraseña"}
        >
          {#if showPassword}
            <EyeOff size={18} />
          {:else}
            <Eye size={18} />
          {/if}
        </button>
      </div>
      <p id="help-password" class="help-text">
        Mínimo 8 caracteres. Incluye mayúsculas, minúsculas, números y símbolos para mayor seguridad
      </p>
      {#if formData.password && !user}
        <div class="password-strength">
          <div class="password-strength-bars">
            {#each Array(5) as _, i}
              <div
                class="strength-bar"
                class:active={i < passwordStrength}
                style="background-color: {i < passwordStrength ? getPasswordStrengthColor(passwordStrength) : 'var(--border-primary)'}"
              ></div>
            {/each}
          </div>
          <span class="strength-label" style="color: {getPasswordStrengthColor(passwordStrength)}">
            {getPasswordStrengthLabel(passwordStrength)}
          </span>
        </div>
      {/if}
      {#if errors.password}
        <p class="error-text">
          <AlertCircle size={14} />
          {errors.password}
        </p>
      {/if}

      <!-- Sucursal (optional) -->
      <div class="input-wrapper">
        <select
          id="sucursal-select"
          class="input"
          value={formData.sucursal_id || ""}
          disabled={loading || $sucursalesAdminStore.loading}
          aria-describedby="help-sucursal"
          on:change={(e) => {
            const val = e.currentTarget.value;
            formData.sucursal_id = val && val.trim() ? val : null;
          }}
        >
          <option value="">— Sin sucursal —</option>
          {#each $sucursalesAdminStore.list.filter((s) => s.active) as sucursal}
            <option value={sucursal.id}>
              {sucursal.identifier} - {sucursal.name}
            </option>
          {/each}
        </select>
      </div>
      <p id="help-sucursal" class="help-text">
        Deja sin sucursal o selecciona una sucursal para asignar al usuario.
      </p>

      {#if errors.submit}
        <div class="error-banner">{errors.submit}</div>
      {/if}

      <div class="form-footer">
        <button type="button" class="btn btn-secondary" on:click={handleClose} disabled={loading}>
          Cancelar
        </button>
        <button type="submit" class="btn btn-primary" disabled={loading}>
          {loading 
            ? (user ? "Guardando..." : "Creando...") 
            : (user ? "Guardar Cambios" : "Crear Usuario")}
        </button>
      </div>
    </form>
  {/if}
</Modal>

<style>
  /* ... existing styles ... */
  .deactivate-content {
    padding: var(--spacing-md) 0;
  }

  .message {
    font-size: var(--text-base);
    color: var(--text-primary);
    margin-bottom: var(--spacing-lg);
    line-height: 1.6;
    font-family: var(--font-body);
  }

  .user-info {
    background: #303245;
    padding: 16px;
    border-radius: 12px;
    margin-top: 20px;
    margin-bottom: 0;
    border: 0;
  }

  .user-info p {
    margin: 8px 0;
    color: #eee;
    font-size: 14px;
  }

  .user-info p:first-child {
    margin-top: 0;
  }

  .user-info p:last-child {
    margin-bottom: 0;
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

  [data-theme="dark"] .error-banner {
    background: rgba(211, 5, 84, 0.2);
  }

  /* Espaciado simplificado - ya no necesario sin .cut */

  /* Input Wrapper - Simplificado sin .cut */
  .input-wrapper {
    width: 100%;
    margin-bottom: 16px;
    position: relative;
  }

  .input-wrapper.password-wrapper {
    position: relative;
  }

  /* Inputs simplificados - estilo moderno pero simple */
  .input {
    width: 100%;
    margin-bottom: 0;
    background: rgba(48, 52, 69, 0.8);
    border: 1px solid rgba(0, 0, 0, 0.3);
    border-radius: 8px;
    outline: none;
    padding: 12px 16px;
    font-size: 14px;
    color: #eee;
    text-shadow: 1px 1px 1px rgba(0, 0, 0, 0.3);
    box-shadow: inset 0 -5px 45px rgba(100, 100, 100, 0.1), 0 1px 1px rgba(255, 255, 255, 0.1);
    transition: box-shadow 0.3s ease, border-color 0.3s ease, background-color 0.3s ease;
    font-family: sans-serif;
    box-sizing: border-box;
  }

  .input::placeholder {
    color: #808097;
    opacity: 0.8;
  }

  .input:focus {
    box-shadow: inset 0 -5px 45px rgba(100, 100, 100, 0.2), 0 1px 1px rgba(255, 255, 255, 0.2);
    border-color: rgba(0, 147, 247, 0.5);
    background: rgba(58, 61, 82, 0.9);
  }

  .input:disabled {
    opacity: 0.6;
    cursor: not-allowed;
    background: rgba(48, 52, 69, 0.5);
  }

  .input.error {
    border: 2px solid #dc2f55;
    background: rgba(220, 47, 85, 0.1);
  }

  .input.error:focus {
    border-color: #dc2f55;
    box-shadow: inset 0 -5px 45px rgba(220, 47, 85, 0.2), 0 1px 1px rgba(255, 255, 255, 0.2);
  }

  /* Select styling */
  .input-wrapper select.input {
    cursor: pointer;
    appearance: none;
    -webkit-appearance: none;
    -moz-appearance: none;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%23eee' d='M6 9L1 4h10z'/%3E%3C/svg%3E");
    background-repeat: no-repeat;
    background-position: right 16px center;
    padding-right: 40px;
  }

  .password-input {
    padding-right: 48px;
  }

  .password-toggle {
    position: absolute;
    right: 12px;
    top: 50%;
    transform: translateY(-50%);
    background: transparent;
    border: none;
    color: var(--text-secondary, #808097);
    cursor: pointer;
    padding: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: color 0.2s ease;
    z-index: 1;
  }

  .password-toggle:hover {
    color: var(--text-primary, #eee);
  }

  .password-toggle:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  /* Help text - mejorado */
  .help-text {
    font-size: 12px;
    color: #808097;
    margin-top: 6px;
    margin-bottom: 0;
    padding-left: 4px;
    line-height: 1.4;
  }

  .password-strength {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-top: 8px;
    margin-bottom: 0;
  }

  .password-strength-bars {
    display: flex;
    gap: 4px;
    flex: 1;
  }

  .strength-bar {
    height: 4px;
    flex: 1;
    border-radius: 2px;
    transition: background-color 0.2s ease, transform 0.2s ease;
  }

  .strength-bar.active {
    transform: scaleY(1.2);
  }

  .strength-label {
    font-size: 12px;
    font-weight: 600;
    min-width: 80px;
    text-align: right;
  }

  /* Error text - mejorado */
  .error-text {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-top: 6px;
    margin-bottom: 0;
    font-size: 12px;
    color: #dc2f55;
    padding-left: 4px;
    line-height: 1.4;
  }

  .error-text svg {
    flex-shrink: 0;
  }

  /* Form Footer - Botones modernos pero simples */
  .form-footer {
    display: flex;
    gap: 12px;
    justify-content: flex-end;
    margin-top: 32px;
    padding-top: 0;
    border-top: none;
  }

  /* Botones estilo moderno pero simple - inspirado en el ejemplo */
  .btn {
    display: inline-block;
    padding: 10px 20px;
    margin-bottom: 0;
    font-size: 14px;
    line-height: 1.5;
    text-align: center;
    vertical-align: middle;
    cursor: pointer;
    border: 1px solid transparent;
    border-radius: 6px;
    font-weight: 600;
    font-family: sans-serif;
    transition: all 0.2s ease;
    box-sizing: border-box;
    text-decoration: none;
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.1), 0 1px 2px rgba(0, 0, 0, 0.1);
  }

  .btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
    pointer-events: none;
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

  .btn-danger {
    background: linear-gradient(to bottom, #ef4444, #dc2626);
    background-color: #dc2626;
    border-color: #b91c1c;
    color: #ffffff;
    text-shadow: 0 -1px 0 rgba(0, 0, 0, 0.25);
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.2), 0 1px 2px rgba(0, 0, 0, 0.2);
  }

  .btn-danger:hover:not(:disabled) {
    background: linear-gradient(to bottom, #f87171, #ef4444);
    background-color: #ef4444;
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.2), 0 2px 4px rgba(0, 0, 0, 0.3);
  }

  .btn-danger:active:not(:disabled) {
    background: linear-gradient(to bottom, #dc2626, #b91c1c);
    background-color: #b91c1c;
    box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.2);
  }

  .btn-block {
    width: 100%;
    display: block;
  }

  /* Responsive: Mobile */
  @media (max-width: 640px) {
    .form-footer {
      flex-direction: column;
    }
  }
</style>
