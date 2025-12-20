<script lang="ts">
  /**
   * UserDeleteConfirm component - Confirmation modal for delete/deactivate actions.
   */
  import { Modal, Button } from "@kidyland/ui";
  import type { User } from "@kidyland/shared/types";
  import { deleteUser } from "$lib/stores/users";
  import { createEventDispatcher } from "svelte";

  export let open = false;
  export let user: User | null = null;
  export let action: "delete" | "deactivate" = "delete";

  const dispatch = createEventDispatcher();

  let loading = false;
  let error: string | null = null;

  async function handleConfirm() {
    if (!user) return;

    loading = true;
    error = null;

    try {
      if (action === "delete") {
        const success = await deleteUser(user.id);
        if (success) {
          dispatch("deleted");
          open = false;
        } else {
          error = "Error al eliminar usuario";
        }
      } else {
        // Deactivate is handled by parent
        dispatch("deleted");
      }
    } catch (err: any) {
      error = err.message || "Error al procesar la acción";
    } finally {
      loading = false;
    }
  }

  function handleClose() {
    open = false;
    dispatch("close");
  }

  $: title = action === "delete" ? "Eliminar Usuario" : "Desactivar Usuario";
  $: message =
    action === "delete"
      ? `¿Estás seguro de que deseas eliminar al usuario "${user?.username}"? Esta acción no se puede deshacer.`
      : `¿Estás seguro de que deseas desactivar al usuario "${user?.username}"?`;
  $: confirmText = action === "delete" ? "Eliminar" : "Desactivar";
  $: confirmVariant = action === "delete" ? "danger" : "secondary";
</script>

<Modal {open} {title} size="md">
  {#if user}
    <div class="confirm-content">
      <p class="message">{message}</p>

      <div class="user-info">
        <p><strong>Username:</strong> {user.username}</p>
        <p><strong>Nombre:</strong> {user.name}</p>
        <p><strong>Rol:</strong> {user.role}</p>
      </div>

      {#if error}
        <div class="error-banner">{error}</div>
      {/if}
    </div>

    <div slot="footer">
      <Button variant="secondary" on:click={handleClose} disabled={loading}>
        Cancelar
      </Button>
      <Button
        variant={confirmVariant}
        on:click={handleConfirm}
        disabled={loading}
      >
        {loading ? "Procesando..." : confirmText}
      </Button>
    </div>
  {/if}
</Modal>

<style>
  .confirm-content {
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
    background: var(--theme-bg-secondary);
    padding: var(--spacing-md);
    border-radius: var(--radius-md);
    margin-bottom: var(--spacing-md);
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
    font-size: var(--text-sm);
  }

  [data-theme="dark"] .error-banner {
    background: rgba(211, 5, 84, 0.2);
  }
</style>

