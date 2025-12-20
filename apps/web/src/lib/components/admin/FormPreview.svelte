<script lang="ts">
  /**
   * FormPreview component - Shows real-time preview of user being created/edited.
   * Desktop sidebar component for better UX.
   */
  import { 
    User as UserIcon, 
    Shield, 
    Building2,
    CheckCircle2,
    Clock,
    Calendar
  } from "lucide-svelte";
  import Badge from "$lib/components/shared/Badge.svelte";

  export let formData: {
    username?: string;
    name?: string;
    role?: string;
    password?: string;
    sucursal_id?: string | null;
  } | null = null;

  export let isEdit = false;

  const roleLabels: Record<string, string> = {
    super_admin: "Super Admin",
    admin_viewer: "Admin Viewer",
    recepcion: "Recepción",
    kidibar: "Kidibar",
    monitor: "Monitor",
  };

  function getRoleBadgeVariant(role: string | undefined): 'success' | 'warning' | 'danger' | 'info' | 'primary' | 'secondary' {
    if (!role) return "secondary";
    const roleVariants: Record<string, 'success' | 'warning' | 'danger' | 'info' | 'primary' | 'secondary'> = {
      super_admin: "primary",
      admin_viewer: "info",
      recepcion: "success",
      kidibar: "warning",
      monitor: "secondary",
    };
    return roleVariants[role] || "secondary";
  }
</script>

<div class="form-preview">
  <div class="preview-header">
    <h3 class="preview-title">
      <UserIcon size={20} />
      Vista Previa
    </h3>
  </div>

  <div class="preview-content">
    {#if !formData || (!formData.username && !formData.name)}
      <div class="preview-empty">
        <p>Completa el formulario para ver la vista previa</p>
      </div>
    {:else}
      <div class="preview-card">
        <div class="preview-avatar">
          <UserIcon size={32} />
        </div>
        
        <div class="preview-info">
          <h4 class="preview-name">
            {formData.name || "Sin nombre"}
          </h4>
          <p class="preview-username">
            @{formData.username || "usuario"}
          </p>
        </div>

        <div class="preview-details">
          <div class="preview-detail-item">
            <Shield size={16} />
            <span class="detail-label">Rol:</span>
            {#if formData.role}
              <Badge variant={getRoleBadgeVariant(formData.role)} size="sm">
                {roleLabels[formData.role]}
              </Badge>
            {:else}
              <span class="detail-value-muted">No asignado</span>
            {/if}
          </div>

          {#if formData.sucursal_id}
            <div class="preview-detail-item">
              <Building2 size={16} />
              <span class="detail-label">Sucursal:</span>
              <span class="detail-value">{formData.sucursal_id.substring(0, 8)}...</span>
            </div>
          {/if}

          {#if isEdit}
            <div class="preview-detail-item">
              <Clock size={16} />
              <span class="detail-label">Estado:</span>
              <Badge variant="info" size="sm">Editando</Badge>
            </div>
          {:else}
            <div class="preview-detail-item">
              <CheckCircle2 size={16} />
              <span class="detail-label">Estado:</span>
              <Badge variant="success" size="sm">Nuevo</Badge>
            </div>
          {/if}
        </div>
      </div>

      <div class="preview-help">
        <h5>Información</h5>
        <ul>
          <li>El username debe ser único</li>
          <li>La password debe tener al menos 8 caracteres</li>
          <li>El rol determina los permisos del usuario</li>
          {#if formData.role === "kidibar" || formData.role === "recepcion"}
            <li>Este rol tendrá acceso a su módulo específico</li>
          {/if}
        </ul>
      </div>
    {/if}
  </div>
</div>

<style>
  .form-preview {
    background: var(--theme-bg-elevated);
    border: 2px solid var(--border-primary);
    border-radius: var(--radius-xl);
    padding: var(--spacing-lg);
    height: fit-content;
    position: sticky;
    top: var(--spacing-lg);
  }

  .preview-header {
    margin-bottom: var(--spacing-lg);
    padding-bottom: var(--spacing-md);
    border-bottom: 2px solid var(--border-primary);
  }

  .preview-title {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    font-size: var(--text-lg);
    font-weight: 700;
    color: var(--text-primary);
    margin: 0;
  }

  .preview-title svg {
    color: var(--accent-primary);
  }

  .preview-empty {
    text-align: center;
    padding: var(--spacing-2xl);
    color: var(--text-muted);
  }

  .preview-card {
    background: var(--theme-bg-secondary);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-lg);
    padding: var(--spacing-lg);
    margin-bottom: var(--spacing-lg);
  }

  .preview-avatar {
    width: 64px;
    height: 64px;
    border-radius: 50%;
    background: linear-gradient(135deg, var(--accent-primary), var(--accent-success));
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto var(--spacing-md);
    color: white;
  }

  .preview-info {
    text-align: center;
    margin-bottom: var(--spacing-lg);
  }

  .preview-name {
    font-size: var(--text-xl);
    font-weight: 700;
    color: var(--text-primary);
    margin: 0 0 var(--spacing-xs) 0;
  }

  .preview-username {
    font-size: var(--text-sm);
    color: var(--text-muted);
    font-family: monospace;
    margin: 0;
  }

  .preview-details {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-md);
  }

  .preview-detail-item {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    font-size: var(--text-sm);
  }

  .preview-detail-item svg {
    color: var(--text-muted);
    flex-shrink: 0;
  }

  .detail-label {
    color: var(--text-secondary);
    font-weight: 500;
    min-width: 60px;
  }

  .detail-value {
    color: var(--text-primary);
    font-weight: 600;
  }

  .detail-value-muted {
    color: var(--text-muted);
    font-style: italic;
  }

  .preview-help {
    background: var(--theme-bg-secondary);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-lg);
    padding: var(--spacing-md);
  }

  .preview-help h5 {
    font-size: var(--text-sm);
    font-weight: 600;
    color: var(--text-primary);
    margin: 0 0 var(--spacing-sm) 0;
  }

  .preview-help ul {
    margin: 0;
    padding-left: var(--spacing-lg);
    color: var(--text-secondary);
    font-size: var(--text-xs);
    line-height: 1.6;
  }

  .preview-help li {
    margin-bottom: var(--spacing-xs);
  }

  /* Mobile: Hide preview */
  @media (max-width: 1199px) {
    .form-preview {
      display: none;
    }
  }
</style>

