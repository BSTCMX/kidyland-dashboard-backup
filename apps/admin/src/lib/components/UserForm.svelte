<script lang="ts">
  /**
   * UserForm component - Create/Edit user modal form.
   */
  import { Modal, Button, Input } from "@kidyland/ui";
  import type { User } from "@kidyland/shared/types";
  import type { UserCreate, UserUpdate } from "$lib/stores/users";
  import { createUser, updateUser } from "$lib/stores/users";
  import { createEventDispatcher } from "svelte";

  export let open = false;
  export let user: User | null = null; // If provided, edit mode; otherwise, create mode

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

  // Initialize form when user changes
  $: if (user && open) {
    formData = {
      name: user.name,
      username: user.username,
      role: user.role,
      sucursal_id: user.sucursal_id,
      password: "", // Empty in edit mode
    };
    errors = {};
  } else if (!user && open) {
    formData = {
      username: "",
      name: "",
      role: "monitor",
      password: "",
      sucursal_id: null,
    };
    errors = {};
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
    const isEdit = !!user;

    // Validate username
    const usernameError = validateUsername(formData.username || "");
    if (usernameError) errors.username = usernameError;

    // Validate name
    if (!formData.name) {
      errors.name = "Nombre es requerido";
    }

    // Validate password (required for create, optional for edit)
    if (!isEdit || formData.password) {
      const passwordError = validatePassword(formData.password || "", isEdit);
      if (passwordError) errors.password = passwordError;
    }

    // Validate role
    if (!formData.role) {
      errors.role = "Rol es requerido";
    }

    return Object.keys(errors).length === 0;
  }

  async function handleSubmit() {
    if (!validateForm()) return;

    loading = true;
    try {
      if (user) {
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
          open = false;
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
          open = false;
        }
      }
    } catch (error: any) {
      errors.submit = error.message || "Error al guardar usuario";
    } finally {
      loading = false;
    }
  }

  function handleClose() {
    open = false;
    dispatch("close");
  }
</script>

<Modal {open} title={user ? "Editar Usuario" : "Crear Usuario"} size="lg">
  <form on:submit|preventDefault={handleSubmit}>
    <!-- Username -->
    <Input
      label="Username"
      bind:value={formData.username}
      error={errors.username}
      required
      disabled={loading || !!user}
      placeholder="usuario123"
    />

    <!-- Name -->
    <Input
      label="Nombre Completo"
      bind:value={formData.name}
      error={errors.name}
      required
      disabled={loading}
      placeholder="Juan Pérez"
    />

    <!-- Role -->
    <div class="form-group">
      <label class="form-label">
        Rol <span class="required">*</span>
      </label>
      <select
        bind:value={formData.role}
        disabled={loading}
        class="form-select"
        class:error={!!errors.role}
      >
        {#each roles as role}
          <option value={role}>{roleLabels[role]}</option>
        {/each}
      </select>
      {#if errors.role}
        <p class="error-text">{errors.role}</p>
      {/if}
    </div>

    <!-- Password -->
    <Input
      label={user ? "Nueva Password (opcional)" : "Password"}
      type="password"
      bind:value={formData.password}
      error={errors.password}
      required={!user}
      disabled={loading}
      placeholder={user ? "Dejar vacío para mantener" : "Password123"}
    />

    <!-- Sucursal ID (optional) -->
    <Input
      label="Sucursal ID (opcional)"
      bind:value={formData.sucursal_id}
      disabled={loading}
      placeholder="UUID de sucursal"
    />

    <!-- Submit error -->
    {#if errors.submit}
      <div class="error-banner">{errors.submit}</div>
    {/if}
  </form>

  <!-- Footer buttons -->
  <div slot="footer">
    <Button type="button" variant="secondary" on:click={handleClose} disabled={loading}>
      Cancelar
    </Button>
    <Button type="button" on:click={handleSubmit} disabled={loading}>
      {loading ? "Guardando..." : user ? "Actualizar" : "Crear"}
    </Button>
  </div>
</Modal>

<style>
  .form-group {
    margin-bottom: var(--spacing-lg);
  }

  .form-label {
    display: block;
    font-size: var(--text-sm);
    font-weight: 500;
    color: var(--text-primary);
    margin-bottom: var(--spacing-sm);
    font-family: var(--font-body);
  }

  .required {
    color: var(--accent-danger);
  }

  .form-select {
    width: 100%;
    padding: var(--spacing-sm) var(--spacing-md);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
    font-size: var(--text-base);
    background: var(--theme-bg-elevated);
    color: var(--text-primary);
    transition: border-color 0.2s ease;
    font-family: var(--font-body);
  }

  .form-select:focus {
    outline: none;
    border-color: var(--accent-primary);
    box-shadow: 0 0 0 3px rgba(0, 147, 247, 0.1);
  }

  .form-select:disabled {
    background: var(--theme-bg-secondary);
    cursor: not-allowed;
    opacity: 0.6;
  }

  .form-select.error {
    border-color: var(--accent-danger);
  }

  .error-text {
    margin-top: var(--spacing-xs);
    font-size: var(--text-sm);
    color: var(--accent-danger);
  }

  .error-banner {
    background: rgba(211, 5, 84, 0.1);
    border: 1px solid var(--accent-danger);
    color: var(--accent-danger);
    padding: var(--spacing-md);
    border-radius: var(--radius-md);
    margin-bottom: var(--spacing-md);
    font-size: var(--text-sm);
  }

  [data-theme="dark"] .error-banner {
    background: rgba(211, 5, 84, 0.2);
  }

  .form-input {
    width: 100%;
    padding: var(--spacing-sm) var(--spacing-md);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
    font-size: var(--text-base);
    background: var(--theme-bg-elevated);
    color: var(--text-primary);
    transition: border-color 0.2s ease;
    font-family: var(--font-body);
  }

  .form-input:focus {
    outline: none;
    border-color: var(--accent-primary);
    box-shadow: 0 0 0 3px rgba(0, 147, 247, 0.1);
  }

  .form-input:disabled {
    background: var(--theme-bg-secondary);
    cursor: not-allowed;
    opacity: 0.6;
  }
</style>

