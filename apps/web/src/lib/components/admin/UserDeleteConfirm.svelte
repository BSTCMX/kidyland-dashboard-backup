<script lang="ts">
  /**
   * UserDeleteConfirm component - Confirmation modal for delete/deactivate actions.
   */
  import { Modal } from "@kidyland/ui";
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
      ? `¿Estás seguro de que deseas eliminar al usuario "${user?.username}"?`
      : `¿Estás seguro de que deseas desactivar al usuario "${user?.username}"?`;
  $: confirmText = action === "delete" ? "Eliminar" : "Desactivar";
  $: confirmVariant = action === "delete" ? "danger" : "secondary";
</script>

<Modal 
  {open} 
  {title} 
  size="md"
  anchorPosition={null}
  on:close={handleClose}
>
  {#if user}
    <div class="confirm-content">
      <p class="message">{message}</p>

      {#if action === "delete"}
        <p class="warning-message">
          ⚠️ El usuario se eliminará permanentemente después de 30 días. Podrás recuperarlo durante este período.
        </p>
      {/if}

      <div class="user-info">
        <p><strong>Username:</strong> {user.username}</p>
        <p><strong>Nombre:</strong> {user.name}</p>
        <p><strong>Rol:</strong> {user.role}</p>
      </div>

      {#if error}
        <div class="error-banner">{error}</div>
      {/if}

      <div class="form-footer">
        <button 
          type="button" 
          class="btn btn-secondary" 
          on:click={handleClose} 
          disabled={loading}
        >
          Cancelar
        </button>
        <button
          type="button"
          class="btn {confirmVariant === 'danger' ? 'btn-danger' : 'btn-secondary'}"
          on:click={handleConfirm}
          disabled={loading}
        >
          {loading ? "Procesando..." : confirmText}
        </button>
      </div>
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

  .warning-message {
    font-size: var(--text-sm);
    color: var(--accent-warning);
    margin-bottom: var(--spacing-md);
    padding: var(--spacing-sm) var(--spacing-md);
    background: rgba(255, 206, 0, 0.1);
    border: 1px solid var(--accent-warning);
    border-radius: var(--radius-md);
    line-height: 1.5;
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
    border: 1px solid var(--accent-danger);
    color: var(--accent-danger);
    padding: var(--spacing-md);
    border-radius: var(--radius-md);
    font-size: var(--text-sm);
  }

  [data-theme="dark"] .error-banner {
    background: rgba(211, 5, 84, 0.2);
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

  /* Responsive: Mobile */
  @media (max-width: 640px) {
    .form-footer {
      flex-direction: column;
    }
  }
</style>

