<script lang="ts">
  /**
   * UserChangePasswordModal component - Modal for changing user password.
   */
  import { Modal, Button, Input } from "@kidyland/ui";
  import type { User } from "@kidyland/shared/types";
  import { changePassword } from "$lib/stores/users";
  import { createEventDispatcher } from "svelte";

  export let open = false;
  export let user: User | null = null;

  const dispatch = createEventDispatcher();

  let newPassword = "";
  let confirmPassword = "";
  let errors: Record<string, string> = {};
  let loading = false;

  function validatePassword(password: string): string | null {
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

    const passwordError = validatePassword(newPassword);
    if (passwordError) {
      errors.newPassword = passwordError;
    }

    if (newPassword !== confirmPassword) {
      errors.confirmPassword = "Las passwords no coinciden";
    }

    return Object.keys(errors).length === 0;
  }

  async function handleSubmit() {
    if (!user || !validateForm()) return;

    loading = true;
    try {
      const success = await changePassword(user.id, {
        new_password: newPassword,
      });
      if (success) {
        dispatch("changed");
        newPassword = "";
        confirmPassword = "";
        errors = {};
        open = false;
      }
    } catch (error: any) {
      errors.submit = error.message || "Error al cambiar password";
    } finally {
      loading = false;
    }
  }

  function handleClose() {
    open = false;
    newPassword = "";
    confirmPassword = "";
    errors = {};
    dispatch("close");
  }
</script>

<Modal open={open} title="Cambiar Password" size="md">
  {#if user}
    <form on:submit|preventDefault={handleSubmit}>
      <div class="user-info">
        <p><strong>Usuario:</strong> {user.username}</p>
        <p><strong>Nombre:</strong> {user.name}</p>
      </div>

      <Input
        label="Nueva Password"
        type="password"
        bind:value={newPassword}
        error={errors.newPassword}
        required
        disabled={loading}
        placeholder="Password123"
      />

      <Input
        label="Confirmar Password"
        type="password"
        bind:value={confirmPassword}
        error={errors.confirmPassword}
        required
        disabled={loading}
        placeholder="Password123"
      />

      {#if errors.submit}
        <div class="error-banner">{errors.submit}</div>
      {/if}

      <div class="modal-actions">
        <Button type="button" variant="secondary" on:click={handleClose} disabled={loading}>
          Cancelar
        </Button>
        <Button type="button" on:click={handleSubmit} disabled={loading}>
          {loading ? "Cambiando..." : "Cambiar Password"}
        </Button>
      </div>
    </form>
  {/if}
</Modal>

<style>
  .user-info {
    background: var(--theme-bg-secondary);
    padding: var(--spacing-md);
    border-radius: var(--radius-md);
    margin-bottom: var(--spacing-lg);
    border: 1px solid var(--border-primary);
  }

  .user-info p {
    margin: var(--spacing-sm) 0;
    color: var(--text-secondary);
    font-size: var(--text-sm);
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

  .modal-actions {
    display: flex;
    gap: var(--spacing-md);
    justify-content: flex-end;
    margin-top: var(--spacing-xl);
    padding-top: var(--spacing-lg);
    border-top: 1px solid var(--border-primary);
  }
</style>

