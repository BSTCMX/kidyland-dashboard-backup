<script lang="ts">
  /**
   * Services section page for reception.
   * 
   * Provides access to service-related functionality:
   * - Nueva Venta (New Sale)
   * - Timers Activos (Active Timers)
   * - Historial de Ventas (Sales History)
   */
  import { page } from "$app/stores";
  import { user, hasAccess } from "$lib/stores/auth";
  import { getModulePermissions } from "$lib/utils/permissions";
  import { preserveQueryParams } from "$lib/utils/navigation";
  import { 
    Receipt, 
    Clock, 
    FileText 
  } from "lucide-svelte";
</script>

<div class="services-page">
  <div class="page-header">
    <div>
      <h1 class="page-title">Servicios</h1>
      <p class="page-description">
        Gestiona ventas de servicios, timers activos y historial de ventas.
      </p>
    </div>
  </div>

  {#if $user}
    {@const recepcionPerms = getModulePermissions($user.role, "recepcion")}
    
    <div class="services-grid">
    {#if recepcionPerms?.canCreate}
      <a href="/recepcion/venta" class="service-card primary">
        <div class="card-icon">
          <Receipt size={32} strokeWidth={1.5} />
        </div>
        <h3>Nueva Venta</h3>
        <p>Registrar venta de servicio y crear timer</p>
        <span class="card-link">Crear Venta →</span>
      </a>
    {/if}

    {#if recepcionPerms?.canAccess}
      <a href="/recepcion/timers" class="service-card">
        <div class="card-icon">
          <Clock size={32} strokeWidth={1.5} />
        </div>
        <h3>Timers Activos</h3>
        <p>Ver y gestionar timers activos</p>
        <span class="card-link">Ver Timers →</span>
      </a>
    {/if}

    {#if recepcionPerms?.canAccess}
      <a href={preserveQueryParams("/recepcion/ventas", $page.url)} class="service-card">
        <div class="card-icon">
          <FileText size={32} strokeWidth={1.5} />
        </div>
        <h3>Historial de Ventas</h3>
        <p>Ver todas las ventas registradas</p>
        <span class="card-link">Ver Historial →</span>
      </a>
    {/if}
    </div>
  {/if}
</div>

<style>
  .services-page {
    width: 100%;
  }

  .page-header {
    margin-bottom: var(--spacing-xl);
  }

  .page-title {
    font-family: var(--font-primary);
    font-size: var(--text-3xl);
    font-weight: 700;
    color: var(--text-primary);
    margin: 0 0 var(--spacing-md) 0;
  }

  .page-description {
    font-size: var(--text-lg);
    color: var(--text-secondary);
    margin: 0;
  }

  .services-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: var(--spacing-xl);
  }

  .service-card {
    padding: var(--spacing-xl);
    background: var(--theme-bg-card);
    backdrop-filter: blur(16px) saturate(150%);
    -webkit-backdrop-filter: blur(16px) saturate(150%);
    border: 1px solid var(--border-primary);
    border-radius: 16px;
    box-shadow: 
      0 8px 24px rgba(0, 0, 0, 0.15),
      0 0 20px var(--glow-primary),
      inset 0 1px 0 rgba(255, 255, 255, 0.05);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    min-height: 200px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    text-decoration: none;
    color: inherit;
  }

  .service-card.primary {
    border-color: var(--accent-primary);
    background: linear-gradient(135deg, var(--theme-bg-card) 0%, rgba(0, 147, 247, 0.1) 100%);
  }

  .service-card:hover {
    transform: translateY(-4px);
    border-color: rgba(0, 147, 247, 0.5);
    box-shadow: 
      0 12px 32px rgba(0, 0, 0, 0.2),
      0 0 30px var(--glow-primary),
      0 0 40px var(--glow-secondary),
      inset 0 1px 0 rgba(255, 255, 255, 0.1);
  }

  .card-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 64px;
    height: 64px;
    background: rgba(0, 147, 247, 0.1);
    border-radius: var(--radius-lg);
    color: var(--accent-primary);
    margin-bottom: var(--spacing-md);
  }

  .service-card h3 {
    font-size: var(--text-xl);
    font-weight: 700;
    margin: 0 0 var(--spacing-sm) 0;
    color: var(--text-primary);
  }

  .service-card p {
    color: var(--text-secondary);
    margin: 0 0 var(--spacing-lg) 0;
    flex: 1;
  }

  .card-link {
    color: var(--accent-primary);
    font-weight: 600;
    text-decoration: none;
    transition: color 0.2s ease;
    display: inline-block;
  }

  .service-card:hover .card-link {
    color: var(--accent-primary-hover);
  }

  @media (max-width: 768px) {
    .services-grid {
      grid-template-columns: 1fr;
    }
  }
</style>

