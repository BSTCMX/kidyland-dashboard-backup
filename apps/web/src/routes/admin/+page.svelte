<script lang="ts">
  /**
   * Admin Dashboard - Main page with metrics and refresh button.
   * 
   * Features:
   * - Master refresh button
   * - Display of sales, stock, and services metrics
   * - Reactive updates from metrics store
   */
  import { onMount } from "svelte";
  import { goto } from "$app/navigation";
  import { user, hasAccessSecure, canEditSecure } from "$lib/stores/auth";
  import RefreshButton from "$lib/components/admin/RefreshButton.svelte";
  import PredictionsPanel from "$lib/components/admin/PredictionsPanel.svelte";
  import ExportButton from "$lib/components/shared/ExportButton.svelte";
  import SucursalSelector from "$lib/components/admin/SucursalSelector.svelte";
  import PeriodSelector from "$lib/components/admin/PeriodSelector.svelte";
  import { metricsStore, formattedRevenue, formattedATV, timeSinceLastRefresh, refreshMetrics, fetchTopCustomersByModule } from "$lib/stores/metrics";
  import { periodStore, initializePeriod, selectedDays } from "$lib/stores/period";
  import { sucursalesAdminStore, fetchAllSucursales } from "$lib/stores/sucursales-admin";
  import { writable } from "svelte/store";
  import { getPageSEOTags } from "$lib/utils/seo";
  import { 
    LayoutDashboard, 
    FileSpreadsheet, 
    FileText, 
    RefreshCw, 
    DollarSign, 
    Package, 
    Clock, 
    Sparkles,
    CheckCircle,
    AlertTriangle,
    TrendingUp,
    ShoppingBag,
    Zap,
    Users,
    ClipboardList,
    ShoppingCart,
    BarChart3
  } from "lucide-svelte";

  // Selected sucursal for filtering
  let selectedSucursalId: string | null = null;

  function handleSucursalSelect(sucursalId: string | null) {
    selectedSucursalId = sucursalId;
    // Sucursal change only updates selection - RefreshButton will use the new sucursal
    // User must click RefreshButton to actually refresh metrics with new sucursal
    // This prevents automatic concurrent calls
  }

  // Create mapping from sucursal_id to sucursal_name for display
  $: sucursalNameMap = new Map(
    $sucursalesAdminStore.list.map(s => [s.id, s.name])
  );

  // Helper function to get sucursal name from ID
  function getSucursalName(sucursalId: string): string {
    return sucursalNameMap.get(sucursalId) || `Sucursal ${sucursalId.slice(0, 8)}`;
  }

  onMount(() => {
    // Load sucursales for name mapping
    if (canEditSecure("admin")) {
      fetchAllSucursales();
    }
    
    // Early return: verify user has access and can edit admin BEFORE executing any logic
    // Uses secure checks that verify token-store consistency
    if (!$user || !hasAccessSecure("/admin") || !canEditSecure("admin")) {
      goto("/");
      return;
    }

    // Initialize period store
    initializePeriod(30);

    // No automatic data loading - user must click RefreshButton to load metrics
    // This prevents concurrent calls and gives user control over when to refresh
  });
  
  function handlePeriodChange(event: CustomEvent<{ days: number }>): void {
    // Period change only updates the store - RefreshButton will use the new period
    // User must click RefreshButton to actually refresh metrics with new period
    // This prevents automatic concurrent calls
  }
</script>

<div class="dashboard-container">
  <div class="dashboard-header">
    <h1 class="dashboard-title">
      <LayoutDashboard size={32} strokeWidth={1.5} style="display: inline-block; vertical-align: middle; margin-right: 12px;" />
      Dashboard Admin
    </h1>
    <div class="header-actions">
      <SucursalSelector
        bind:selectedSucursalId
        onSelect={handleSucursalSelect}
      />
      <div class="export-buttons">
        <ExportButton
          exportType="excel"
          reportType="dashboard"
          sucursalId={selectedSucursalId || $user?.sucursal_id}
          variant="brutalist"
          size="small"
          useWizard={true}
        />
        <ExportButton
          exportType="pdf"
          reportType="dashboard"
          sucursalId={selectedSucursalId || $user?.sucursal_id}
          variant="brutalist"
          size="small"
          useWizard={true}
        />
      </div>
      <RefreshButton {selectedSucursalId} />
    </div>
  </div>

  {#if $metricsStore.error}
    <div class="error-banner">
      {$metricsStore.error}
    </div>
  {/if}

  {#if !$metricsStore.hasInitialData && !$metricsStore.refreshInProgress}
    <div class="empty-state-banner">
      <p>
        <BarChart3 size={20} strokeWidth={1.5} style="display: inline-block; vertical-align: middle; margin-right: 8px;" />
        Presiona el botón <strong>"Actualizar"</strong> para cargar las métricas del dashboard.
      </p>
    </div>
  {/if}

  <div class="metrics-grid">
    <!-- Sales Metrics -->
    <div class="metric-card">
      <div class="metric-header">
        <h2 class="metric-title">
          <DollarSign size={24} strokeWidth={1.5} style="display: inline-block; vertical-align: middle; margin-right: 8px;" />
          Ventas
        </h2>
        <span class="metric-date-badge">Hoy</span>
      </div>
      {#if $metricsStore.sales}
        <div class="metric-content">
          <div class="metric-value">{$formattedRevenue}</div>
          <div class="metric-label">Total Revenue</div>
          
          <div class="metric-row">
            <span class="metric-label">Ticket Promedio:</span>
            <span class="metric-value-small">{$formattedATV}</span>
          </div>
          
          <div class="metric-row">
            <span class="metric-label">Total Ventas:</span>
            <span class="metric-value-small">{$metricsStore.sales.sales_count}</span>
          </div>
          
          <div class="metric-row">
            <span class="metric-label">Por Tipo:</span>
            <div class="metric-detail">
              {#each Object.entries($metricsStore.sales.revenue_by_type) as [type, revenue]}
                <div class="metric-item">
                  {type}: ${(revenue / 100).toFixed(2)}
                </div>
              {/each}
            </div>
          </div>
        </div>
      {:else}
        <div class="metric-empty">
          Presiona "Actualizar" para cargar métricas de ventas
        </div>
      {/if}
    </div>

    <!-- Stock Metrics -->
    <div class="metric-card">
      <div class="metric-header">
        <h2 class="metric-title">
          <Package size={24} strokeWidth={1.5} style="display: inline-block; vertical-align: middle; margin-right: 8px;" />
          Inventario
        </h2>
        <span class="metric-date-badge">Hoy</span>
      </div>
      {#if $metricsStore.stock}
        <div class="metric-content">
          <div class="metric-value">{$metricsStore.stock.total_products}</div>
          <div class="metric-label">Total Productos</div>
          
          <div class="metric-row">
            <span class="metric-label">Valor Total:</span>
            <span class="metric-value-small">
              ${($metricsStore.stock.total_stock_value_cents / 100).toFixed(2)}
            </span>
          </div>
          
          {#if $metricsStore.stock.alerts_count > 0}
            <div class="alert-badge">
              ⚠️ {$metricsStore.stock.alerts_count} alertas de stock bajo
            </div>
            
            <div class="alerts-list">
              {#each $metricsStore.stock.low_stock_alerts.slice(0, 5) as alert}
                <div class="alert-item">
                  {alert.product_name}: {alert.stock_qty} unidades
                </div>
              {/each}
            </div>
          {:else}
            <div class="metric-success">✅ Sin alertas de stock</div>
          {/if}
        </div>
      {:else}
        <div class="metric-empty">
          Presiona "Actualizar" para cargar métricas de inventario
        </div>
      {/if}
    </div>

    <!-- Services Metrics -->
    <div class="metric-card">
      <div class="metric-header">
        <h2 class="metric-title">
          <Clock size={24} strokeWidth={1.5} style="display: inline-block; vertical-align: middle; margin-right: 8px;" />
          Servicios
        </h2>
        <span class="metric-date-badge">Hoy</span>
      </div>
      {#if $metricsStore.services}
        <div class="metric-content">
          <div class="metric-value">{$metricsStore.services.active_timers_count}</div>
          <div class="metric-label">Timers Activos</div>
          
          <div class="metric-row">
            <span class="metric-label">Total Servicios:</span>
            <span class="metric-value-small">{$metricsStore.services.total_services}</span>
          </div>
          
          <div class="metric-row">
            <span class="metric-label">Por Sucursal:</span>
            <div class="metric-detail">
              {#each Object.entries($metricsStore.services.services_by_sucursal) as [sucursalId, count]}
                <div class="metric-item">
                  {getSucursalName(sucursalId)}: {count}
                </div>
              {/each}
            </div>
          </div>
        </div>
      {:else}
        <div class="metric-empty">
          Presiona "Actualizar" para cargar métricas de servicios
        </div>
      {/if}
    </div>
    
    <!-- Peak Hours Card -->
    <div class="metric-card">
      <div class="metric-header">
        <h2 class="metric-title">
          <TrendingUp size={24} strokeWidth={1.5} style="display: inline-block; vertical-align: middle; margin-right: 8px;" />
          Horas Pico
        </h2>
        <PeriodSelector variant="dropdown" size="small" showLabel={false} on:change={handlePeriodChange} />
      </div>
      {#if $metricsStore.peak_hours}
        {#if $metricsStore.peak_hours.peak_hours && $metricsStore.peak_hours.peak_hours.length > 0}
          <div class="metric-content">
            <div class="metric-value">
              {$metricsStore.peak_hours.busiest_hour?.hour ?? 0}:00h
            </div>
            <div class="metric-label">Hora más ocupada</div>
            
            <div class="metric-row">
              <span class="metric-label">Ventas en hora pico:</span>
              <span class="metric-value-small">{$metricsStore.peak_hours.busiest_hour?.sales_count ?? 0}</span>
            </div>
            
            <div class="metric-detail">
              <div style="font-size: var(--text-sm); color: var(--text-secondary); margin-top: var(--spacing-sm);">
                Top 5 horas:
              </div>
              {#each $metricsStore.peak_hours.peak_hours.slice(0, 5) as peak}
                <div class="metric-item">
                  {peak.hour}:00h - {peak.sales_count} ventas
                </div>
              {/each}
            </div>
          </div>
        {:else}
          <div class="metric-empty">
            <div style="margin-bottom: var(--spacing-xs); font-size: var(--text-sm);">
              Fecha: {$metricsStore.peak_hours.date || 'N/A'}
            </div>
            No hay datos de horas pico para esta fecha.
            {#if $metricsStore.peak_hours.sucursal_id}
              <div style="margin-top: var(--spacing-xs); font-size: var(--text-xs); color: var(--text-muted);">
                Intenta seleccionar una fecha con ventas registradas.
              </div>
            {/if}
          </div>
        {/if}
      {:else}
        <div class="metric-empty">
          Presiona "Actualizar" para cargar métricas de horas pico
        </div>
      {/if}
    </div>
    
    <!-- Top Products Card -->
    <div class="metric-card">
      <div class="metric-header">
        <h2 class="metric-title">
          <ShoppingBag size={24} strokeWidth={1.5} style="display: inline-block; vertical-align: middle; margin-right: 8px;" />
          Productos Top
        </h2>
        <PeriodSelector variant="dropdown" size="small" showLabel={false} on:change={handlePeriodChange} />
      </div>
      {#if $metricsStore.top_products && $metricsStore.top_products.top_products && $metricsStore.top_products.top_products.length > 0}
        <div class="metric-content">
          <div class="metric-label">Últimos {$metricsStore.top_products.period_days} días</div>
          
          <div class="metric-detail">
            {#each $metricsStore.top_products.top_products.slice(0, 5) as product, index}
              <div class="metric-row" style="padding: var(--spacing-sm) 0; border-top: 1px solid var(--border-primary);">
                <span style="font-weight: 600; color: var(--text-primary);">
                  {index + 1}. {product.product_name}
                </span>
                <span style="color: var(--text-secondary);">
                  {product.quantity_sold} vendidos
                </span>
              </div>
            {/each}
          </div>
        </div>
      {:else}
        <div class="metric-empty">
          Presiona "Actualizar" para cargar métricas de productos top
        </div>
      {/if}
    </div>
    
    <!-- Top Services Card -->
    <div class="metric-card">
      <div class="metric-header">
        <h2 class="metric-title">
          <Zap size={24} strokeWidth={1.5} style="display: inline-block; vertical-align: middle; margin-right: 8px;" />
          Servicios Top
        </h2>
        <PeriodSelector variant="dropdown" size="small" showLabel={false} on:change={handlePeriodChange} />
      </div>
      {#if $metricsStore.top_services && $metricsStore.top_services.top_services && $metricsStore.top_services.top_services.length > 0}
        <div class="metric-content">
          <div class="metric-label">Últimos {$metricsStore.top_services.period_days} días</div>
          
          <div class="metric-detail">
            {#each $metricsStore.top_services.top_services.slice(0, 5) as service, index}
              <div class="metric-row" style="padding: var(--spacing-sm) 0; border-top: 1px solid var(--border-primary);">
                <span style="font-weight: 600; color: var(--text-primary);">
                  {index + 1}. {service.service_name}
                </span>
                <span style="color: var(--text-secondary);">
                  {service.usage_count} usos
                </span>
              </div>
            {/each}
          </div>
        </div>
      {:else}
        <div class="metric-empty">
          Presiona "Actualizar" para cargar métricas de servicios top
        </div>
      {/if}
    </div>
    
    <!-- Top Customers Card (Segmented by Module) -->
    <div class="metric-card">
      <div class="metric-header">
        <h2 class="metric-title">
          <Users size={24} strokeWidth={1.5} style="display: inline-block; vertical-align: middle; margin-right: 8px;" />
          Clientes Top
        </h2>
        <PeriodSelector variant="dropdown" size="small" showLabel={false} on:change={handlePeriodChange} />
      </div>
      {#if $metricsStore.top_customers_by_module}
        <div class="metric-content">
          <div class="metric-label">Últimos {$metricsStore.top_customers_by_module.period_days} días</div>
          
          <!-- Reception Customers -->
          {#if $metricsStore.top_customers_by_module.recepcion?.top_customers?.length > 0}
            <div class="module-customers-section">
              <div class="module-header">
                <ClipboardList size={18} strokeWidth={1.5} class="module-icon" />
                <span class="module-title">Recepción</span>
              </div>
              <div class="customers-list">
                {#each $metricsStore.top_customers_by_module.recepcion.top_customers.slice(0, 5) as customer, index}
                  <div class="customer-item">
                    <div class="customer-info">
                      <span class="customer-rank">{index + 1}.</span>
                      <span class="customer-name">{customer.customer_name}</span>
                      {#if customer.child_age}
                        <span class="customer-age">({customer.child_age} años)</span>
                      {/if}
                    </div>
                    <div class="customer-stats">
                      <span class="stat-visits">{customer.visit_count} {customer.visit_count === 1 ? 'visita' : 'visitas'}</span>
                      <span class="stat-revenue">${((customer.total_revenue_cents || 0) / 100).toFixed(2)}</span>
                    </div>
                  </div>
                {/each}
              </div>
            </div>
          {/if}
          
          <!-- KidiBar Customers -->
          {#if $metricsStore.top_customers_by_module.kidibar?.top_customers?.length > 0}
            <div class="module-customers-section">
              <div class="module-header">
                <ShoppingCart size={18} strokeWidth={1.5} class="module-icon" />
                <span class="module-title">KidiBar</span>
              </div>
              <div class="customers-list">
                {#each $metricsStore.top_customers_by_module.kidibar.top_customers.slice(0, 5) as customer, index}
                  <div class="customer-item">
                    <div class="customer-info">
                      <span class="customer-rank">{index + 1}.</span>
                      <span class="customer-name">{customer.customer_name}</span>
                    </div>
                    <div class="customer-stats">
                      <span class="stat-visits">{customer.visit_count} {customer.visit_count === 1 ? 'visita' : 'visitas'}</span>
                      <span class="stat-revenue">${((customer.total_revenue_cents || 0) / 100).toFixed(2)}</span>
                    </div>
                  </div>
                {/each}
              </div>
            </div>
          {/if}
          
          {#if (!$metricsStore.top_customers_by_module.recepcion?.top_customers?.length && !$metricsStore.top_customers_by_module.kidibar?.top_customers?.length)}
            <div class="metric-empty" style="margin-top: var(--spacing-md);">
              No hay datos de clientes para el período seleccionado
            </div>
          {/if}
        </div>
      {:else if $metricsStore.top_customers?.top_customers?.length > 0}
        <!-- Fallback to legacy top_customers if segmented data not available -->
        <div class="metric-content">
          <div class="metric-label">Últimos {$metricsStore.top_customers.period_days} días (Recepción)</div>
          
          <div class="metric-detail">
            {#each $metricsStore.top_customers.top_customers.slice(0, 5) as customer, index}
              <div class="metric-row" style="padding: var(--spacing-sm) 0; border-top: 1px solid var(--border-primary);">
                <div style="flex: 1;">
                  <span style="font-weight: 600; color: var(--text-primary);">
                    {index + 1}. {customer.child_name}
                  </span>
                  {#if customer.child_age}
                    <span style="color: var(--text-secondary); font-size: var(--text-sm);">
                      ({customer.child_age} años)
                    </span>
                  {/if}
                </div>
                <div style="display: flex; flex-direction: column; align-items: flex-end; gap: 2px;">
                  <span style="color: var(--text-secondary); font-size: var(--text-sm);">
                    {customer.visit_count} {customer.visit_count === 1 ? 'visita' : 'visitas'}
                  </span>
                  <span style="color: var(--text-primary); font-size: var(--text-xs);">
                    ${((customer.total_revenue_cents || 0) / 100).toFixed(2)}
                  </span>
                </div>
              </div>
            {/each}
          </div>
        </div>
      {:else}
        <div class="metric-empty">
          Presiona "Actualizar" para cargar métricas de clientes top
        </div>
      {/if}
    </div>
  </div>

  {#if $metricsStore.lastRefresh && $timeSinceLastRefresh}
    <div class="last-refresh">
      Última actualización: {$timeSinceLastRefresh}
    </div>
  {/if}

  <!-- Predictions Panel (Bajo Demanda) -->
  <PredictionsPanel />
</div>

<style>
  .dashboard-container {
    min-height: 100vh;
    background: var(--theme-bg-primary);
    padding: var(--spacing-xl);
  }

  .dashboard-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--spacing-xl);
    flex-wrap: wrap;
    gap: var(--spacing-md);
  }

  .header-actions {
    display: flex;
    align-items: center;
    gap: var(--spacing-md);
    flex-wrap: wrap;
  }

  .export-buttons {
    display: flex;
    gap: var(--spacing-sm);
    flex-wrap: wrap;
  }

  .dashboard-title {
    font-family: var(--font-primary);
    font-size: var(--text-3xl);
    font-weight: 700;
    color: var(--text-primary);
    margin: 0;
    
    /* Efecto 3D - solo sombreado, sin animaciones */
    text-shadow: 
      0 0.05em 0 rgba(0, 0, 0, 0.1),
      0 0.1em 0 rgba(0, 0, 0, 0.1),
      0 0.15em 0 rgba(0, 0, 0, 0.1),
      0 0.2em 0 rgba(0, 0, 0, 0.1),
      0 0.25em 0 rgba(0, 0, 0, 0.1),
      0 0.25em 0.02em rgba(0, 0, 0, 0.15),
      0 0.28em 0.2em rgba(0, 0, 0, 0.25);
  }

  .error-banner {
    background: rgba(211, 5, 84, 0.1);
    border: 1px solid var(--accent-danger);
    color: var(--accent-danger);
    padding: var(--spacing-md);
    border-radius: var(--radius-md);
    margin-bottom: var(--spacing-lg);
  }

  .empty-state-banner {
    background: rgba(59, 130, 246, 0.1);
    border: 1px solid var(--accent-primary);
    color: var(--accent-primary);
    padding: var(--spacing-lg);
    border-radius: var(--radius-md);
    margin-bottom: var(--spacing-lg);
    text-align: center;
    font-size: 1rem;
  }

  .empty-state-banner p {
    margin: 0;
  }

  .metrics-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: var(--spacing-xl);
    margin-bottom: var(--spacing-xl);
  }

  .metric-card {
    background: var(--theme-bg-card);
    backdrop-filter: blur(16px) saturate(150%);
    -webkit-backdrop-filter: blur(16px) saturate(150%);
    border: 1px solid var(--border-primary);
    border-radius: 16px;
    padding: var(--spacing-xl);
    box-shadow: 
      0 8px 24px rgba(0, 0, 0, 0.15),
      0 0 20px var(--glow-primary),
      inset 0 1px 0 rgba(255, 255, 255, 0.05);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }
  
  .metric-card:hover {
    transform: translateY(-4px);
    border-color: rgba(0, 147, 247, 0.5);
    box-shadow: 
      0 12px 32px rgba(0, 0, 0, 0.2),
      0 0 30px var(--glow-primary),
      0 0 40px var(--glow-secondary),
      inset 0 1px 0 rgba(255, 255, 255, 0.1);
  }

  .metric-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--spacing-lg);
    gap: var(--spacing-sm);
    flex-wrap: wrap;
  }
  
  .metric-title {
    font-size: clamp(var(--text-lg), 2.5vw, var(--text-xl));
    font-weight: 700;
    margin: 0;
    color: var(--text-primary);
    flex: 1;
    min-width: 0;
  }
  
  .metric-date-badge {
    display: inline-flex;
    align-items: center;
    padding: var(--spacing-xs) var(--spacing-sm);
    background: var(--accent-primary);
    color: white;
    border-radius: var(--radius-sm);
    font-size: clamp(var(--text-xs), 1.5vw, var(--text-sm));
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    white-space: nowrap;
    flex-shrink: 0;
  }

  .metric-content {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-md);
  }

  .metric-value {
    font-size: var(--text-3xl);
    font-weight: 700;
    color: var(--accent-primary);
  }

  .metric-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--spacing-md);
    gap: var(--spacing-sm);
    flex-wrap: wrap;
  }
  
  .metric-date-badge {
    display: inline-flex;
    align-items: center;
    padding: var(--spacing-xs) var(--spacing-sm);
    background: var(--accent-primary);
    color: white;
    border-radius: var(--radius-sm);
    font-size: var(--text-xs);
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    white-space: nowrap;
  }
  
  .metric-label {
    font-size: var(--text-sm);
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .metric-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: var(--spacing-sm) 0;
    border-top: 1px solid var(--border-primary);
  }

  .metric-value-small {
    font-weight: 600;
    color: var(--text-primary);
  }

  .metric-detail {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xs);
    margin-top: var(--spacing-sm);
  }

  .metric-item {
    font-size: var(--text-sm);
    color: var(--text-secondary);
  }

  .metric-empty {
    color: var(--text-muted);
    font-style: italic;
    text-align: center;
    padding: var(--spacing-xl);
  }

  /* Module Customers Section Styles */
  .module-customers-section {
    margin-top: var(--spacing-lg);
    padding-top: var(--spacing-lg);
    border-top: 1px solid var(--border-primary);
  }
  
  .module-section {
    margin-top: var(--spacing-lg);
    padding-top: var(--spacing-lg);
    border-top: 1px solid var(--border-primary);
  }
  
  .module-section:first-of-type {
    margin-top: var(--spacing-md);
    padding-top: var(--spacing-md);
    border-top: none;
  }

  .module-header {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    margin-bottom: var(--spacing-md);
    padding-bottom: var(--spacing-sm);
  }

  .module-header :global(.lucide-clipboard-list),
  .module-header :global(.lucide-shopping-cart) {
    color: var(--accent-primary);
    flex-shrink: 0;
  }

  .module-title {
    font-size: clamp(var(--text-sm), 2vw, var(--text-base));
    font-weight: 600;
    color: var(--accent-primary);
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .customers-list {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xs);
  }

  .customer-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: var(--spacing-sm) 0;
    border-top: 1px solid var(--border-primary);
    transition: all 0.2s ease;
    gap: var(--spacing-sm);
  }

  .customer-item:first-child {
    border-top: none;
  }

  .customer-item:hover {
    background: rgba(0, 147, 247, 0.05);
    padding-left: var(--spacing-xs);
    padding-right: var(--spacing-xs);
    border-radius: var(--radius-sm);
    transform: translateX(2px);
  }

  .customer-info {
    display: flex;
    align-items: center;
    gap: var(--spacing-xs);
    flex: 1;
    flex-wrap: wrap;
  }

  .customer-rank {
    font-weight: 700;
    color: var(--accent-primary);
    font-size: var(--text-sm);
    min-width: 1.5rem;
  }

  .customer-name {
    font-weight: 600;
    color: var(--text-primary);
    font-size: var(--text-base);
  }

  .customer-age {
    color: var(--text-secondary);
    font-size: var(--text-sm);
  }

  .customer-stats {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 2px;
    flex-shrink: 0;
  }

  .stat-visits {
    color: var(--text-secondary);
    font-size: var(--text-sm);
  }

  .stat-revenue {
    color: var(--text-primary);
    font-size: var(--text-xs);
    font-weight: 600;
  }

  .alert-badge {
    background: rgba(255, 206, 0, 0.1);
    border: 1px solid var(--accent-warning);
    color: var(--accent-warning);
    padding: var(--spacing-sm) var(--spacing-md);
    border-radius: var(--radius-md);
    font-weight: 600;
    margin-top: var(--spacing-sm);
  }

  .alerts-list {
    margin-top: var(--spacing-sm);
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xs);
  }

  .alert-item {
    font-size: var(--text-sm);
    color: var(--accent-danger);
    padding: var(--spacing-xs) 0;
  }

  .metric-success {
    color: var(--accent-success);
    font-weight: 500;
    margin-top: var(--spacing-sm);
  }

  .last-refresh {
    text-align: center;
    color: var(--text-muted);
    font-size: var(--text-sm);
    margin-top: var(--spacing-xl);
  }

  @media (max-width: 768px) {
    .dashboard-container {
      padding: var(--spacing-md);
    }

    .dashboard-header {
      flex-direction: column;
      align-items: stretch;
      gap: var(--spacing-md);
    }

    .dashboard-title {
      font-size: var(--text-2xl);
      text-align: center;
    }

    .header-actions {
      flex-direction: column;
      width: 100%;
      gap: var(--spacing-sm);
      flex-wrap: nowrap;
    }

    .export-buttons {
      width: 100%;
      flex-direction: column;
      gap: var(--spacing-sm);
      flex-wrap: nowrap;
    }

    .export-buttons :global(button) {
      width: 100%;
      min-height: 44px; /* Minimum touch target size for accessibility */
      justify-content: center;
    }

    /* RefreshButton container optimization */
    .header-actions :global(.refresh-button-container) {
      width: 100%;
    }

    .header-actions :global(.refresh-button-container button) {
      width: 100%;
      min-height: 44px;
      justify-content: center;
    }

    /* SucursalSelector optimization */
    .header-actions :global(.sucursal-selector) {
      width: 100%;
    }

    .metrics-grid {
      grid-template-columns: 1fr;
    }
  }

  /* Prevent hover transform issues on touch devices */
  @media (hover: none) and (pointer: coarse) {
    .export-buttons :global(.btn-brutalist:hover),
    .header-actions :global(.refresh-button:hover) {
      transform: none;
      box-shadow: 3px 3px 0px 0px var(--accent-primary);
      border-width: 2px;
    }
  }
</style>
