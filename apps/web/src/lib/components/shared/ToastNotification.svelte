<script lang="ts">
  /**
   * ToastNotification component - Displays toast notifications.
   * 
   * Shows notifications in a toast container with auto-dismiss.
   * Supports different types: success, error, warning, info.
   */
  import { onMount } from "svelte";
  import { notificationsStore, removeNotification, type Notification } from "$lib/stores/notifications";
  import { Button } from "@kidyland/ui";
  import { CheckCircle, XCircle, AlertTriangle, Info } from "lucide-svelte";
  import type { ComponentType } from "svelte";

  let containerRef: HTMLDivElement;

  $: notifications = $notificationsStore.list;

  function getIconComponent(type: Notification["type"]): ComponentType {
    switch (type) {
      case "success":
        return CheckCircle;
      case "error":
        return XCircle;
      case "warning":
        return AlertTriangle;
      case "info":
        return Info;
      default:
        return Info;
    }
  }

  function getColorClass(type: Notification["type"]): string {
    switch (type) {
      case "success":
        return "toast-success";
      case "error":
        return "toast-error";
      case "warning":
        return "toast-warning";
      case "info":
        return "toast-info";
      default:
        return "toast-info";
    }
  }
</script>

{#if notifications.length > 0}
  <div class="toast-container" bind:this={containerRef} role="region" aria-live="polite" aria-label="Notificaciones">
    {#each notifications as notification (notification.id)}
        <div
          class="toast {getColorClass(notification.type)}"
          role="alert"
          aria-live={notification.type === "error" ? "assertive" : "polite"}
      >
        <div class="toast-content">
          <div class="toast-icon">
            <svelte:component this={getIconComponent(notification.type)} size={20} />
          </div>
          <div class="toast-text">
            <div class="toast-title">{notification.title}</div>
            {#if notification.message}
              <div class="toast-message">{notification.message}</div>
            {/if}
          </div>
        </div>

        {#if notification.action}
          <div class="toast-actions">
            <Button
              variant="secondary"
              size="small"
              on:click={notification.action.handler}
            >
              {notification.action.label}
            </Button>
          </div>
        {/if}

        <button
          class="toast-close"
          on:click={() => removeNotification(notification.id)}
          aria-label="Cerrar notificación"
          title="Cerrar"
        >
          ✕
        </button>
      </div>
    {/each}
  </div>
{/if}

<style>
  .toast-container {
    position: fixed;
    top: var(--spacing-lg);
    right: var(--spacing-lg);
    z-index: 10000;
    display: flex;
    flex-direction: column;
    gap: var(--spacing-sm);
    max-width: 400px;
    width: 100%;
    pointer-events: none;
  }

  .toast {
    display: flex;
    align-items: flex-start;
    gap: var(--spacing-md);
    padding: var(--spacing-md);
    background: var(--theme-bg-elevated);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
    box-shadow: var(--shadow-lg);
    pointer-events: auto;
    animation: slideIn 0.3s ease-out;
    min-height: 48px;
  }

  @keyframes slideIn {
    from {
      transform: translateX(100%);
      opacity: 0;
    }
    to {
      transform: translateX(0);
      opacity: 1;
    }
  }

  .toast-content {
    display: flex;
    align-items: flex-start;
    gap: var(--spacing-sm);
    flex: 1;
  }

  .toast-icon {
    font-size: var(--text-xl);
    flex-shrink: 0;
    line-height: 1;
  }

  .toast-text {
    flex: 1;
    min-width: 0;
  }

  .toast-title {
    font-weight: 600;
    font-size: var(--text-base);
    color: var(--text-primary);
    margin-bottom: var(--spacing-xs);
  }

  .toast-message {
    font-size: var(--text-sm);
    color: var(--text-secondary);
    line-height: 1.4;
  }

  .toast-actions {
    display: flex;
    align-items: center;
    gap: var(--spacing-xs);
    flex-shrink: 0;
  }

  .toast-close {
    background: transparent;
    border: none;
    color: var(--text-secondary);
    font-size: var(--text-lg);
    cursor: pointer;
    padding: var(--spacing-xs);
    line-height: 1;
    flex-shrink: 0;
    min-width: 32px;
    min-height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: var(--radius-sm);
    transition: all 0.2s ease;
  }

  .toast-close:hover {
    background: var(--theme-bg-secondary);
    color: var(--text-primary);
  }

  .toast-close:focus {
    outline: 2px solid var(--accent-primary);
    outline-offset: 2px;
  }

  /* Type-specific colors */
  .toast-success {
    border-left: 4px solid var(--accent-success);
  }

  .toast-error {
    border-left: 4px solid var(--accent-danger);
  }

  .toast-warning {
    border-left: 4px solid var(--accent-warning);
  }

  .toast-info {
    border-left: 4px solid var(--accent-primary);
  }

  /* Responsive */
  @media (max-width: 768px) {
    .toast-container {
      top: var(--spacing-md);
      right: var(--spacing-md);
      left: var(--spacing-md);
      max-width: none;
    }

    .toast {
      padding: var(--spacing-sm) var(--spacing-md);
    }

    .toast-title {
      font-size: var(--text-sm);
    }

    .toast-message {
      font-size: var(--text-xs);
    }
  }
</style>

