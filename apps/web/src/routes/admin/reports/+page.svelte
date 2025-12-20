<script lang="ts">
  /**
   * Reports page - Advanced analytics and reporting dashboard.
   * 
   * Features:
   * - Modular tabs for different report sections
   * - Global filters (date, sucursal, module)
   * - Interactive visualizations
   * - Export capabilities
   */
  import { onMount } from "svelte";
  import { goto } from "$app/navigation";
  import { user, hasAccessSecure, canEditSecure } from "$lib/stores/auth";
  import SucursalSelector from "$lib/components/admin/SucursalSelector.svelte";
  import ExportButton from "$lib/components/shared/ExportButton.svelte";
  import ComparisonCard from "$lib/components/shared/ComparisonCard.svelte";
  import { reportsStore, executiveSummaryStore, fetchAllReports, formatPrice } from "$lib/stores/reports";
  import LoadingSpinner from "$lib/components/admin/LoadingSpinner.svelte";
  import ErrorBanner from "$lib/components/admin/ErrorBanner.svelte";
  import ResponsiveTabs from "$lib/components/admin/ResponsiveTabs.svelte";
  import type { Tab } from "$lib/components/admin/ResponsiveTabs.svelte";
  import SalesTimeSeriesChart from "$lib/components/admin/reports/sales/SalesTimeSeriesChart.svelte";
  import SalesPieChart from "$lib/components/admin/reports/sales/SalesPieChart.svelte";
  import SalesBarChart from "$lib/components/admin/reports/sales/SalesBarChart.svelte";
  import SalesAdvancedMetrics from "$lib/components/admin/reports/sales/SalesAdvancedMetrics.svelte";
  import PeriodSelector from "$lib/components/admin/reports/sales/PeriodSelector.svelte";
  import { fetchSalesTimeSeries, type TimeSeriesDataPoint } from "$lib/stores/reports";
  import type { GroupedDataPoint } from "$lib/utils/charts/chartHelpers";
import CustomersSection from "$lib/components/admin/reports/customers/CustomersSection.svelte";
import ArqueosSection from "$lib/components/admin/reports/arqueos/ArqueosSection.svelte";
import InventorySection from "$lib/components/admin/reports/inventory/InventorySection.svelte";
import ServicesSection from "$lib/components/admin/reports/services/ServicesSection.svelte";
import ForecastingSection from "$lib/components/admin/reports/forecasting/ForecastingSection.svelte";
  import ExecutiveSummaryHeader from "$lib/components/admin/reports/summary/ExecutiveSummaryHeader.svelte";
  import FinancialOverview from "$lib/components/admin/reports/summary/FinancialOverview.svelte";
  import OperationalHealth from "$lib/components/admin/reports/summary/OperationalHealth.svelte";
  import CustomerInsights from "$lib/components/admin/reports/summary/CustomerInsights.svelte";
  import PriorityInsightsPanel from "$lib/components/admin/reports/summary/PriorityInsightsPanel.svelte";
  import ForecastIntegration from "$lib/components/admin/reports/summary/ForecastIntegration.svelte";
  import { 
    LayoutDashboard,
    DollarSign,
    Package,
    Clock,
    Users,
    TrendingUp,
    FileText,
    Sparkles
  } from "lucide-svelte";

  // Tab management
  type TabId = "summary" | "sales" | "inventory" | "services" | "arqueos" | "customers" | "forecasting";
  let activeTab: TabId = "summary";

  // Define tabs configuration
  const tabs: Tab[] = [
    { id: "summary", label: "Resumen Ejecutivo", icon: LayoutDashboard },
    { id: "sales", label: "Ventas", icon: DollarSign },
    { id: "inventory", label: "Inventario", icon: Package },
    { id: "services", label: "Servicios", icon: Clock },
    { id: "arqueos", label: "Arqueos", icon: FileText },
    { id: "customers", label: "Clientes", icon: Users },
    { id: "forecasting", label: "Forecasting", icon: Sparkles },
  ];

  function handleTabChange(tabId: string) {
    activeTab = tabId as TabId;
  }

  // Global filters (defaults for all sections)
  let selectedSucursalId: string | null = null;
  let selectedModule: "all" | "recepcion" | "kidibar" = "all";
  let startDate: string = new Date(new Date().setDate(new Date().getDate() - 30)).toISOString().split("T")[0];
  let endDate: string = new Date().toISOString().split("T")[0];

  // Sales section local filters (can override global)
  let salesLocalDateOverride = false;
  let salesLocalStartDateValue: string | null = null;
  let salesLocalEndDateValue: string | null = null;

  // Effective dates for sales section (local override or global)
  $: salesEffectiveStartDate = salesLocalDateOverride ? salesLocalStartDateValue : startDate;
  $: salesEffectiveEndDate = salesLocalDateOverride ? salesLocalEndDateValue : endDate;

  // Time series data
  let timeSeriesData: TimeSeriesDataPoint[] = [];
  let timeSeriesLoading = false;
  let timeSeriesError: string | null = null;

  // Transformed data for charts
  let revenueByTypeData: GroupedDataPoint[] = [];
  let revenueByPaymentData: GroupedDataPoint[] = [];

  // Transform revenue by type data
  $: if ($reportsStore.sales?.revenue_by_type) {
    revenueByTypeData = Object.entries($reportsStore.sales.revenue_by_type).map(([type, revenue]) => ({
      label: type.charAt(0).toUpperCase() + type.slice(1),
      value: revenue
    }));
  } else {
    revenueByTypeData = [];
  }

  // Transform revenue by payment method data
  $: if ($reportsStore.sales?.revenue_by_payment_method) {
    revenueByPaymentData = Object.entries($reportsStore.sales.revenue_by_payment_method).map(([method, revenue]) => ({
      label: method.charAt(0).toUpperCase() + method.slice(1),
      value: revenue
    }));
  } else {
    revenueByPaymentData = [];
  }

  async function handleSucursalSelect(sucursalId: string | null) {
    selectedSucursalId = sucursalId;
    await refreshReports();
  }

  async function handleModuleChange(module: "all" | "recepcion" | "kidibar") {
    selectedModule = module;
    await refreshReports();
  }

  async function handleDateRangeChange(start: string, end: string) {
    startDate = start;
    endDate = end;
    await refreshReports();
  }

  async function refreshReports(useLocalDates: boolean = false, localStart?: string, localEnd?: string) {
    const effectiveStartDate = useLocalDates && localStart ? localStart : startDate;
    const effectiveEndDate = useLocalDates && localEnd ? localEnd : endDate;
    
    await fetchAllReports(
      selectedSucursalId || $user?.sucursal_id || null,
      effectiveStartDate,
      effectiveEndDate,
      selectedModule
    );
    
    // Fetch time series data
    await loadTimeSeriesData(useLocalDates, localStart, localEnd);
  }

  async function loadTimeSeriesData(useLocalDates: boolean = false, localStart?: string, localEnd?: string) {
    timeSeriesLoading = true;
    timeSeriesError = null;
    
    try {
      const effectiveStartDate = useLocalDates && localStart ? localStart : startDate;
      const effectiveEndDate = useLocalDates && localEnd ? localEnd : endDate;
      
      const timeSeriesReport = await fetchSalesTimeSeries(
        selectedSucursalId || $user?.sucursal_id || null,
        effectiveStartDate,
        effectiveEndDate,
        selectedModule
      );
      
      if (timeSeriesReport) {
        timeSeriesData = timeSeriesReport.timeseries || [];
      }
    } catch (error: any) {
      console.error("Error loading time series data:", error);
      timeSeriesError = error.message || "Error al cargar datos temporales";
    } finally {
      timeSeriesLoading = false;
    }
  }

  function handleModuleSelectChange(event: Event) {
    const target = event.target as HTMLSelectElement;
    if (target) {
      handleModuleChange(target.value as "all" | "recepcion" | "kidibar");
    }
  }

  function handleStartDateChange(event: Event) {
    const target = event.target as HTMLInputElement;
    if (target) {
      handleDateRangeChange(target.value, endDate);
    }
  }

  function handleEndDateChange(event: Event) {
    const target = event.target as HTMLInputElement;
    if (target) {
      handleDateRangeChange(startDate, target.value);
    }
  }

  onMount(async () => {
    if (!$user || !hasAccessSecure("/admin") || !canEditSecure("admin")) {
      goto("/admin");
      return;
    }
    
    // Load initial reports
    await refreshReports();
  });

  // Reload time series when dates change
  $: if (startDate && endDate) {
    loadTimeSeriesData();
  }
</script>

<div class="reports-page">
  <div class="reports-header">
    <div class="header-title">
      <LayoutDashboard size={32} strokeWidth={1.5} />
      <h1 class="page-title">Reportes Avanzados</h1>
    </div>
    
    <div class="header-actions">
      <div class="export-buttons">
        <ExportButton
          exportType="excel"
          reportType="reports"
          sucursalId={selectedSucursalId || $user?.sucursal_id}
          startDate={startDate}
          endDate={endDate}
          variant="brutalist"
          size="small"
          useWizard={true}
          activeTab={activeTab}
          module={selectedModule}
        />
        <ExportButton
          exportType="pdf"
          reportType="reports"
          sucursalId={selectedSucursalId || $user?.sucursal_id}
          startDate={startDate}
          endDate={endDate}
          variant="brutalist"
          size="small"
          useWizard={true}
          activeTab={activeTab}
          module={selectedModule}
        />
      </div>
    </div>
  </div>

  <!-- Global Filters -->
  <div class="filters-section">
    <div class="filters-grid">
      <div class="filter-group">
        <label for="sucursal-filter">Sucursal:</label>
        <SucursalSelector
          bind:selectedSucursalId
          onSelect={handleSucursalSelect}
        />
      </div>

      <div class="filter-group">
        <label for="module-filter">Módulo:</label>
        <select
          id="module-filter"
          bind:value={selectedModule}
          on:change={handleModuleSelectChange}
          class="filter-select"
        >
          <option value="all">Todos</option>
          <option value="recepcion">Recepción</option>
          <option value="kidibar">KidiBar</option>
        </select>
      </div>

      <div class="filter-group">
        <label for="start-date">Fecha Inicio:</label>
        <input
          id="start-date"
          type="date"
          bind:value={startDate}
          on:change={handleStartDateChange}
          class="filter-input"
        />
      </div>

      <div class="filter-group">
        <label for="end-date">Fecha Fin:</label>
        <input
          id="end-date"
          type="date"
          bind:value={endDate}
          on:change={handleEndDateChange}
          class="filter-input"
        />
      </div>
    </div>
  </div>

  <!-- Tabs Navigation -->
  <div class="tabs-container">
    <ResponsiveTabs 
      {tabs} 
      activeTab={activeTab} 
      onTabChange={handleTabChange} 
    />

    <!-- Tab Content -->
    <div class="tab-content">
      {#if activeTab === "summary"}
        <div class="tab-panel">
          <div class="executive-summary-header">
            <h2 class="tab-title">Resumen Ejecutivo</h2>
            <p class="tab-description">Vista consolidada de métricas principales, insights y proyecciones</p>
          </div>
          
          {#if $reportsStore.loading}
            <LoadingSpinner />
          {:else if $reportsStore.error}
            <ErrorBanner error={$reportsStore.error} />
          {:else if $executiveSummaryStore}
            <div class="executive-summary-content">
              <!-- Health Scorecard Header -->
              <ExecutiveSummaryHeader health={$executiveSummaryStore.overallHealth} />

              <!-- Financial Overview -->
              <FinancialOverview financialKPIs={$executiveSummaryStore.financialKPIs} />

              <!-- Operational Health -->
              <OperationalHealth operationalKPIs={$executiveSummaryStore.operationalKPIs} />

              <!-- Customer Insights -->
              <CustomerInsights customerKPIs={$executiveSummaryStore.customerKPIs} />

              <!-- Priority Insights Panel -->
              {#if $executiveSummaryStore.topInsights.length > 0}
                <PriorityInsightsPanel insights={$executiveSummaryStore.topInsights} />
              {/if}

              <!-- Module Breakdown (when module comparison is available) -->
              {#if $executiveSummaryStore.moduleBreakdown && selectedModule === "all"}
                <div class="module-comparison-section">
                  <h3 class="section-title">Comparación por Módulo</h3>
                  <div class="module-comparison-grid">
                    <div class="module-card recepcion">
                      <h4 class="module-title">Recepción</h4>
                      <div class="module-metrics">
                        <div class="module-metric">
                          <span class="metric-label">Revenue:</span>
                          <span class="metric-value">{formatPrice($executiveSummaryStore.moduleBreakdown.recepcion.revenue)}</span>
                        </div>
                        <div class="module-metric">
                          <span class="metric-label">Ventas:</span>
                          <span class="metric-value">{$executiveSummaryStore.moduleBreakdown.recepcion.salesCount}</span>
                        </div>
                        <div class="module-metric">
                          <span class="metric-label">ATV:</span>
                          <span class="metric-value">{formatPrice($executiveSummaryStore.moduleBreakdown.recepcion.atv)}</span>
                        </div>
                        {#if $executiveSummaryStore.moduleBreakdown.comparison}
                          <div class="module-metric">
                            <span class="metric-label">Participación:</span>
                            <span class="metric-value">{$executiveSummaryStore.moduleBreakdown.comparison.participation.recepcion_percent.toFixed(1)}%</span>
                          </div>
                        {/if}
                      </div>
                    </div>
                    
                    <div class="module-card kidibar">
                      <h4 class="module-title">KidiBar</h4>
                      <div class="module-metrics">
                        <div class="module-metric">
                          <span class="metric-label">Revenue:</span>
                          <span class="metric-value">{formatPrice($executiveSummaryStore.moduleBreakdown.kidibar.revenue)}</span>
                        </div>
                        <div class="module-metric">
                          <span class="metric-label">Ventas:</span>
                          <span class="metric-value">{$executiveSummaryStore.moduleBreakdown.kidibar.salesCount}</span>
                        </div>
                        <div class="module-metric">
                          <span class="metric-label">ATV:</span>
                          <span class="metric-value">{formatPrice($executiveSummaryStore.moduleBreakdown.kidibar.atv)}</span>
                        </div>
                        {#if $executiveSummaryStore.moduleBreakdown.comparison}
                          <div class="module-metric">
                            <span class="metric-label">Participación:</span>
                            <span class="metric-value">{$executiveSummaryStore.moduleBreakdown.comparison.participation.kidibar_percent.toFixed(1)}%</span>
                          </div>
                        {/if}
                      </div>
                    </div>
                  </div>
                </div>
              {/if}

              <!-- Forecast Integration -->
              {#if $executiveSummaryStore.forecastProjections}
                <ForecastIntegration 
                  forecastProjections={$executiveSummaryStore.forecastProjections}
                  currentRevenue={$executiveSummaryStore.financialKPIs.totalRevenue}
                />
              {/if}
            </div>
          {:else}
            <div class="placeholder-content">
              <p>No hay datos disponibles. Ajusta los filtros y vuelve a intentar.</p>
            </div>
          {/if}
        </div>
      {:else if activeTab === "sales"}
        <div class="tab-panel">
          <div class="tab-header-with-filters">
            <div class="tab-header-text">
              <h2 class="tab-title">Ventas</h2>
              <p class="tab-description">Análisis detallado de ventas con comparaciones temporales</p>
            </div>
            {#if selectedModule !== "all"}
              <div class="module-filter-badge" title="Filtro de módulo activo">
                <span class="badge-icon">🔍</span>
                <span class="badge-text">
                  {selectedModule === "recepcion" ? "Recepción" : "KidiBar"}
                </span>
              </div>
            {/if}
          </div>
          
          <!-- Period Selector with local override -->
          <div class="period-selector-section">
            <div class="period-selector-header">
              <h3 class="period-selector-title">Período de Análisis</h3>
              {#if salesLocalDateOverride}
                <button
                  class="reset-filter-button"
                  on:click={() => {
                    salesLocalDateOverride = false;
                    salesLocalStartDateValue = null;
                    salesLocalEndDateValue = null;
                    refreshReports();
                  }}
                  title="Usar filtros globales"
                  aria-label="Resetear a filtros globales"
                >
                  <span class="reset-icon">↻</span>
                  Usar globales
                </button>
              {/if}
            </div>
            <PeriodSelector
              startDate={salesEffectiveStartDate || ''}
              endDate={salesEffectiveEndDate || ''}
              on:change={async (e) => {
                salesLocalStartDateValue = e.detail.startDate;
                salesLocalEndDateValue = e.detail.endDate;
                salesLocalDateOverride = true;
                // Use local dates for refresh without modifying global dates
                await refreshReports(true, e.detail.startDate, e.detail.endDate);
              }}
            />
            {#if salesLocalDateOverride}
              <div class="override-indicator">
                <span class="override-badge">Filtro local activo</span>
              </div>
            {/if}
          </div>
          
          {#if $reportsStore.loading}
            <LoadingSpinner />
          {:else if $reportsStore.error}
            <ErrorBanner error={$reportsStore.error} />
          {:else if $reportsStore.sales}
            <div class="sales-grid">
              <!-- KPIs Principales -->
              <div class="kpis-section">
                <h3 class="section-title">Métricas Principales</h3>
                <div class="kpis-grid">
                  {#if $reportsStore.salesComparison}
                    <ComparisonCard
                      title="Total Revenue"
                      comparison={$reportsStore.salesComparison}
                      showCurrency={true}
                    />
                  {:else}
                    <div class="metric-card">
                      <h4 class="metric-title">Total Revenue</h4>
                      <div class="metric-value">{formatPrice($reportsStore.sales.total_revenue_cents)}</div>
                    </div>
                  {/if}
                  
                  <div class="metric-card">
                    <h4 class="metric-title">Total Ventas</h4>
                    <div class="metric-value">{$reportsStore.sales.sales_count}</div>
                  </div>
                  
                  <div class="metric-card">
                    <h4 class="metric-title">Ticket Promedio (ATV)</h4>
                    <div class="metric-value">{formatPrice($reportsStore.sales.average_transaction_value_cents)}</div>
                  </div>
                </div>
              </div>

              <!-- Time Series Chart -->
              <div class="time-series-section">
                <h3 class="section-title">Tendencia de Ventas</h3>
                <SalesTimeSeriesChart
                  data={timeSeriesData}
                  metric="revenue"
                  height="400px"
                  loading={timeSeriesLoading}
                  error={timeSeriesError}
                />
              </div>

              <!-- Revenue por Tipo (Pie Chart) -->
              {#if revenueByTypeData.length > 0}
                <div class="revenue-by-type-section">
                  <h3 class="section-title">Revenue por Tipo</h3>
                  <SalesPieChart
                    data={revenueByTypeData}
                    label="Revenue"
                    height="350px"
                    chartType="doughnut"
                  />
                </div>
              {/if}

              <!-- Revenue por Método de Pago (Bar Chart) -->
              {#if revenueByPaymentData.length > 0}
                <div class="revenue-by-payment-section">
                  <h3 class="section-title">Revenue por Método de Pago</h3>
                  <SalesBarChart
                    data={revenueByPaymentData}
                    label="Revenue"
                    height="350px"
                  />
                </div>
              {/if}

              <!-- Advanced Metrics -->
              <div class="advanced-metrics-section">
                <SalesAdvancedMetrics
                  salesCount={$reportsStore.sales.sales_count}
                  totalRevenueCents={$reportsStore.sales.total_revenue_cents}
                  averageTransactionValueCents={$reportsStore.sales.average_transaction_value_cents}
                  uniqueCustomers={$reportsStore.sales.unique_customers || 0}
                />
              </div>

              <!-- Comparación Módulos (solo cuando no hay filtro de módulo activo) -->
              {#if $reportsStore.moduleComparison && selectedModule === "all"}
                <div class="module-comparison-section">
                  <h3 class="section-title">Comparación por Módulo</h3>
                  <div class="module-comparison-grid">
                    <div class="module-card recepcion">
                      <h4 class="module-title">Recepción</h4>
                      <div class="module-metrics">
                        <div class="module-metric">
                          <span class="metric-label">Revenue:</span>
                          <span class="metric-value">{formatPrice($reportsStore.moduleComparison.recepcion.revenue_cents)}</span>
                        </div>
                        <div class="module-metric">
                          <span class="metric-label">Ventas:</span>
                          <span class="metric-value">{$reportsStore.moduleComparison.recepcion.sales_count}</span>
                        </div>
                        <div class="module-metric">
                          <span class="metric-label">ATV:</span>
                          <span class="metric-value">{formatPrice($reportsStore.moduleComparison.recepcion.atv_cents)}</span>
                        </div>
                      </div>
                    </div>
                    <div class="module-card kidibar">
                      <h4 class="module-title">KidiBar</h4>
                      <div class="module-metrics">
                        <div class="module-metric">
                          <span class="metric-label">Revenue:</span>
                          <span class="metric-value">{formatPrice($reportsStore.moduleComparison.kidibar.revenue_cents)}</span>
                        </div>
                        <div class="module-metric">
                          <span class="metric-label">Ventas:</span>
                          <span class="metric-value">{$reportsStore.moduleComparison.kidibar.sales_count}</span>
                        </div>
                        <div class="module-metric">
                          <span class="metric-label">ATV:</span>
                          <span class="metric-value">{formatPrice($reportsStore.moduleComparison.kidibar.atv_cents)}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              {:else if selectedModule !== "all"}
                <div class="module-filter-notice">
                  <div class="filter-notice-content">
                    <span class="filter-notice-icon">ℹ️</span>
                    <div class="filter-notice-text">
                      <p class="filter-notice-title">Filtro de módulo activo</p>
                      <p class="filter-notice-description">
                        Mostrando solo datos de <strong>{selectedModule === "recepcion" ? "Recepción" : "KidiBar"}</strong>. 
                        La comparación por módulos está disponible cuando se selecciona "Todos" en el filtro global.
                      </p>
                    </div>
                  </div>
                </div>
              {/if}
            </div>
          {:else}
            <div class="placeholder-content">
              <p>No hay datos de ventas disponibles. Ajusta los filtros y vuelve a intentar.</p>
            </div>
          {/if}
        </div>
      {:else if activeTab === "inventory"}
        <div class="tab-panel">
          <div class="tab-header-with-filters">
            <div class="tab-header-text">
              <h2 class="tab-title">Inventario</h2>
              <p class="tab-description">Análisis avanzado de inventario y rotación de stock</p>
            </div>
          </div>
          
          <InventorySection 
            sucursalId={selectedSucursalId}
            startDate={startDate}
            endDate={endDate}
          />
        </div>
      {:else if activeTab === "services"}
        <div class="tab-panel">
          <div class="tab-header-with-filters">
            <div class="tab-header-text">
              <h2 class="tab-title">Servicios</h2>
              <p class="tab-description">Análisis avanzado de servicios y utilización</p>
            </div>
          </div>
          
          <ServicesSection 
            sucursalId={selectedSucursalId}
            startDate={startDate}
            endDate={endDate}
          />
        </div>
      {:else if activeTab === "arqueos"}
        <div class="tab-panel">
          <div class="tab-header-with-filters">
            <div class="tab-header-text">
              <h2 class="tab-title">Arqueos</h2>
              <p class="tab-description">Historial y análisis de arqueos de caja</p>
            </div>
            {#if selectedModule !== "all"}
              <div class="module-filter-badge" title="Filtro de módulo activo">
                <span class="badge-icon">🔍</span>
                <span class="badge-text">
                  {selectedModule === "recepcion" ? "Recepción" : "KidiBar"}
                </span>
              </div>
            {/if}
          </div>
          
          {#if $reportsStore.loading}
            <LoadingSpinner />
          {:else if $reportsStore.error}
            <ErrorBanner error={$reportsStore.error} />
          {:else if $reportsStore.arqueos}
            <div class="arqueos-grid">
              <div class="metrics-section">
                <h3 class="section-title">Métricas Generales</h3>
                <div class="metrics-grid">
                  <div class="metric-card">
                    <h4 class="metric-title">Total Arqueos</h4>
                    <div class="metric-value">{$reportsStore.arqueos.total_arqueos}</div>
                  </div>
                  
                  <div class="metric-card">
                    <h4 class="metric-title">Coincidencias Perfectas</h4>
                    <div class="metric-value">{$reportsStore.arqueos.perfect_matches}</div>
                    <div class="metric-subtitle">
                      {($reportsStore.arqueos.perfect_matches / $reportsStore.arqueos.total_arqueos * 100).toFixed(1)}% del total
                    </div>
                  </div>
                  
                  <div class="metric-card">
                    <h4 class="metric-title">Discrepancias</h4>
                    <div class="metric-value">{$reportsStore.arqueos.discrepancies}</div>
                    <div class="metric-subtitle">
                      Tasa: {$reportsStore.arqueos.discrepancy_rate?.toFixed(1) || '0.0'}%
                    </div>
                  </div>
                  
                  <div class="metric-card">
                    <h4 class="metric-title">Diferencia Total</h4>
                    <div class="metric-value">{formatPrice($reportsStore.arqueos.total_difference_cents || 0)}</div>
                  </div>
                </div>
              </div>
              
              {#if $reportsStore.arqueos.recent_arqueos && $reportsStore.arqueos.recent_arqueos.length > 0}
                <div class="recent-section">
                  <h3 class="section-title">Arqueos Recientes</h3>
                  <div class="arqueos-list">
                    {#each $reportsStore.arqueos.recent_arqueos as arqueo}
                      <div class="arqueo-item">
                        <div class="arqueo-date">{new Date(arqueo.date).toLocaleDateString('es-MX', { day: 'numeric', month: 'short', year: 'numeric' })}</div>
                        <div class="arqueo-details">
                          <div class="arqueo-detail">
                            <span class="detail-label">Sistema:</span>
                            <span class="detail-value">{formatPrice(arqueo.system_total_cents)}</span>
                          </div>
                          <div class="arqueo-detail">
                            <span class="detail-label">Físico:</span>
                            <span class="detail-value">{formatPrice(arqueo.physical_count_cents)}</span>
                          </div>
                          <div class="arqueo-detail">
                            <span class="detail-label">Diferencia:</span>
                            <span class="detail-value" class:positive={arqueo.difference_cents > 0} class:negative={arqueo.difference_cents < 0}>
                              {formatPrice(arqueo.difference_cents)}
                            </span>
                          </div>
                        </div>
                      </div>
                    {/each}
                  </div>
                </div>
              {/if}

              <!-- Advanced Visualizations Section -->
              <ArqueosSection
                sucursalId={selectedSucursalId || $user?.sucursal_id || null}
                startDate={startDate}
                endDate={endDate}
                selectedModule={selectedModule}
              />
            </div>
          {:else}
            <div class="placeholder-content">
              <p>No hay datos de arqueos disponibles. Ajusta los filtros y vuelve a intentar.</p>
            </div>
          {/if}
        </div>
      {:else if activeTab === "customers"}
        <div class="tab-panel">
          <h2 class="tab-title">Clientes</h2>
          <p class="tab-description">Análisis avanzado de clientes con segmentación y métricas</p>
          
          <CustomersSection 
            sucursalId={selectedSucursalId}
            startDate={startDate}
            endDate={endDate}
          />
        </div>
      {:else if activeTab === "forecasting"}
        <div class="tab-panel">
          <div class="tab-header-with-filters">
            <div class="tab-header-text">
              <h2 class="tab-title">Forecasting</h2>
              <p class="tab-description">Predicciones y proyecciones avanzadas con análisis profundo</p>
            </div>
          </div>
          
          <ForecastingSection 
            sucursalId={selectedSucursalId}
            startDate={startDate}
            endDate={endDate}
            module={selectedModule}
          />
        </div>
      {/if}
    </div>
  </div>
</div>

<style>
  .reports-page {
    min-height: 100vh;
    background: var(--theme-bg-primary);
    padding: var(--spacing-xl);
  }

  .reports-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--spacing-xl);
    flex-wrap: wrap;
    gap: var(--spacing-md);
  }

  .header-title {
    display: flex;
    align-items: center;
    gap: var(--spacing-md);
  }

  .page-title {
    font-family: var(--font-primary);
    font-size: var(--text-3xl);
    font-weight: 700;
    color: var(--text-primary);
    margin: 0;
    text-shadow: 
      0 0.05em 0 rgba(0, 0, 0, 0.1),
      0 0.1em 0 rgba(0, 0, 0, 0.1),
      0 0.15em 0 rgba(0, 0, 0, 0.1),
      0 0.2em 0 rgba(0, 0, 0, 0.1),
      0 0.25em 0 rgba(0, 0, 0, 0.1),
      0 0.25em 0.02em rgba(0, 0, 0, 0.15),
      0 0.28em 0.2em rgba(0, 0, 0, 0.25);
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

  .filters-section {
    background: var(--theme-bg-card);
    backdrop-filter: blur(16px) saturate(150%);
    -webkit-backdrop-filter: blur(16px) saturate(150%);
    border: 1px solid var(--border-primary);
    border-radius: 16px;
    padding: var(--spacing-lg);
    margin-bottom: var(--spacing-xl);
    box-shadow: 
      0 8px 24px rgba(0, 0, 0, 0.15),
      0 0 20px var(--glow-primary),
      inset 0 1px 0 rgba(255, 255, 255, 0.05);
  }

  .filters-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: var(--spacing-md);
  }

  .filter-group {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xs);
  }

  .filter-group label {
    font-size: var(--text-sm);
    color: var(--text-secondary);
    font-weight: 500;
  }

  .filter-select,
  .filter-input {
    padding: var(--spacing-sm) var(--spacing-md);
    background: var(--theme-bg-elevated);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
    color: var(--text-primary);
    font-size: var(--text-base);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }

  .filter-select:focus,
  .filter-input:focus {
    outline: none;
    border-color: var(--accent-primary);
    box-shadow: 0 0 0 3px rgba(0, 147, 247, 0.1);
  }

  .tabs-container {
    background: var(--theme-bg-card);
    backdrop-filter: blur(16px) saturate(150%);
    -webkit-backdrop-filter: blur(16px) saturate(150%);
    border: 1px solid var(--border-primary);
    border-radius: 16px;
    overflow: hidden;
    box-shadow: 
      0 8px 24px rgba(0, 0, 0, 0.15),
      0 0 20px var(--glow-primary),
      inset 0 1px 0 rgba(255, 255, 255, 0.05);
    padding: var(--spacing-sm);
  }

  .tab-content {
    padding: var(--spacing-xl);
  }

  .tab-panel {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-lg);
  }

  .tab-title {
    font-family: var(--font-primary);
    font-size: clamp(var(--text-xl), 4vw, var(--text-2xl));
    font-weight: 700;
    color: var(--text-primary);
    margin: 0;
  }

  .tab-description {
    font-size: var(--text-base);
    color: var(--text-secondary);
    margin: 0;
  }

  .tab-header-with-filters {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: var(--spacing-lg);
    margin-bottom: var(--spacing-xl);
  }

  .tab-header-text {
    flex: 1;
  }

  .module-filter-badge {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    background: var(--theme-bg-card);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md, 8px);
    padding: var(--spacing-sm) var(--spacing-md);
    font-size: var(--text-sm);
    color: var(--text-primary);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }

  .badge-icon {
    font-size: var(--text-base);
  }

  .badge-text {
    font-weight: 600;
    text-transform: capitalize;
  }

  .module-filter-notice {
    background: var(--theme-bg-card);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-lg, 12px);
    padding: var(--spacing-lg);
    margin-top: var(--spacing-xl);
  }

  .filter-notice-content {
    display: flex;
    gap: var(--spacing-md);
    align-items: flex-start;
  }

  .filter-notice-icon {
    font-size: var(--text-xl);
    flex-shrink: 0;
  }

  .filter-notice-text {
    flex: 1;
  }

  .filter-notice-title {
    font-size: var(--text-base);
    font-weight: 600;
    color: var(--text-primary);
    margin: 0 0 var(--spacing-xs) 0;
  }

  .filter-notice-description {
    font-size: var(--text-sm);
    color: var(--text-secondary);
    margin: 0;
    line-height: 1.5;
  }

  .filter-notice-description strong {
    color: var(--text-primary);
    font-weight: 600;
  }

  .placeholder-content {
    padding: var(--spacing-2xl);
    text-align: center;
    color: var(--text-muted);
    font-style: italic;
  }

  .summary-grid {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xl);
  }

  .kpis-section,
  .module-comparison-section {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-md);
  }

  .section-title {
    font-size: var(--text-xl);
    font-weight: 700;
    color: var(--text-primary);
    margin: 0;
  }

  .kpis-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(min(250px, 100%), 1fr));
    gap: var(--spacing-lg);
  }

  .metric-card {
    background: var(--theme-bg-card);
    backdrop-filter: blur(16px) saturate(150%);
    -webkit-backdrop-filter: blur(16px) saturate(150%);
    border: 1px solid var(--border-primary);
    border-radius: 16px;
    padding: var(--spacing-lg);
    box-shadow: 
      0 8px 24px rgba(0, 0, 0, 0.15),
      0 0 20px var(--glow-primary),
      inset 0 1px 0 rgba(255, 255, 255, 0.05);
  }

  .metric-title {
    font-size: var(--text-sm);
    font-weight: 600;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin: 0 0 var(--spacing-sm) 0;
  }

  .metric-value {
    font-size: clamp(var(--text-xl), 5vw, var(--text-3xl));
    font-weight: 700;
    color: var(--accent-primary);
    line-height: 1.2;
  }

  .module-comparison-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(min(300px, 100%), 1fr));
    gap: var(--spacing-lg);
  }

  .module-card {
    background: var(--theme-bg-card);
    backdrop-filter: blur(16px) saturate(150%);
    -webkit-backdrop-filter: blur(16px) saturate(150%);
    border: 1px solid var(--border-primary);
    border-radius: 16px;
    padding: var(--spacing-lg);
    box-shadow: 
      0 8px 24px rgba(0, 0, 0, 0.15),
      0 0 20px var(--glow-primary),
      inset 0 1px 0 rgba(255, 255, 255, 0.05);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }

  .module-card:hover {
    transform: translateY(-4px);
    border-color: rgba(0, 147, 247, 0.5);
    box-shadow: 
      0 12px 32px rgba(0, 0, 0, 0.2),
      0 0 30px var(--glow-primary),
      0 0 40px var(--glow-secondary),
      inset 0 1px 0 rgba(255, 255, 255, 0.1);
  }

  .module-card.recepcion {
    border-left: 4px solid var(--accent-primary);
  }

  .module-card.kidibar {
    border-left: 4px solid var(--accent-success);
  }

  .module-title {
    font-size: var(--text-lg);
    font-weight: 700;
    color: var(--text-primary);
    margin: 0 0 var(--spacing-md) 0;
  }

  .module-metrics {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-sm);
  }

  .module-metric {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: var(--spacing-sm) 0;
    border-top: 1px solid var(--border-primary);
  }

  .module-metric:first-child {
    border-top: none;
  }

  .module-metric .metric-label {
    font-size: var(--text-sm);
    color: var(--text-secondary);
  }

  .module-metric .metric-value {
    font-size: var(--text-base);
    font-weight: 600;
    color: var(--text-primary);
  }

  .arqueos-grid,
  .customers-grid,
  .forecast-grid {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xl);
  }

  .metrics-section {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-md);
  }

  .metrics-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(min(200px, 100%), 1fr));
    gap: var(--spacing-lg);
  }

  .metric-subtitle {
    font-size: var(--text-sm);
    color: var(--text-secondary);
    margin-top: var(--spacing-xs);
  }

  .recent-section {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-md);
  }

  .arqueos-list,
  .customers-list,
  .forecast-list {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-md);
  }

  .arqueo-item,
  .customer-item,
  .forecast-item {
    background: var(--theme-bg-card);
    backdrop-filter: blur(16px) saturate(150%);
    -webkit-backdrop-filter: blur(16px) saturate(150%);
    border: 1px solid var(--border-primary);
    border-radius: 16px;
    padding: var(--spacing-lg);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }

  .arqueo-item:hover,
  .customer-item:hover,
  .forecast-item:hover {
    transform: translateY(-2px);
    border-color: rgba(0, 147, 247, 0.5);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
  }

  .arqueo-date,
  .customer-name,
  .forecast-date {
    font-size: var(--text-lg);
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: var(--spacing-sm);
  }

  .arqueo-details,
  .customer-stats,
  .forecast-details {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xs);
  }

  .arqueo-detail,
  .forecast-detail {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: var(--spacing-xs) 0;
  }

  .detail-label {
    font-size: var(--text-sm);
    color: var(--text-secondary);
  }

  .detail-value {
    font-size: var(--text-base);
    font-weight: 600;
    color: var(--text-primary);
  }

  .detail-value.positive {
    color: var(--accent-success);
  }

  .detail-value.negative {
    color: var(--accent-danger);
  }

  .customer-age {
    font-size: var(--text-sm);
    color: var(--text-secondary);
    margin-bottom: var(--spacing-xs);
  }

  .stat {
    font-size: var(--text-sm);
    color: var(--text-secondary);
    margin-right: var(--spacing-md);
  }

  .module-customers-section {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-md);
  }

  .forecast-info {
    background: var(--theme-bg-card);
    backdrop-filter: blur(16px) saturate(150%);
    -webkit-backdrop-filter: blur(16px) saturate(150%);
    border: 1px solid var(--border-primary);
    border-radius: 16px;
    padding: var(--spacing-lg);
  }

  .info-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: var(--spacing-md);
    margin-top: var(--spacing-md);
  }

  .info-item {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xs);
  }

  .info-label {
    font-size: var(--text-sm);
    color: var(--text-secondary);
  }

  .info-value {
    font-size: var(--text-base);
    font-weight: 600;
    color: var(--text-primary);
  }

  .info-value.high {
    color: var(--accent-success);
  }

  .info-value.medium {
    color: var(--accent-warning);
  }

  .info-value.low {
    color: var(--accent-danger);
  }

  .forecast-list-section {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-md);
  }

  /* Sales Tab Styles */
  .sales-grid {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xl);
  }

  .revenue-by-type-section {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-md);
  }

  .revenue-type-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(min(200px, 100%), 1fr));
    gap: var(--spacing-lg);
  }

  .revenue-type-card {
    background: var(--theme-bg-card);
    backdrop-filter: blur(16px) saturate(150%);
    -webkit-backdrop-filter: blur(16px) saturate(150%);
    border: 1px solid var(--border-primary);
    border-radius: 16px;
    padding: var(--spacing-lg);
    text-align: center;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }

  .revenue-type-card:hover {
    transform: translateY(-2px);
    border-color: rgba(0, 147, 247, 0.5);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
  }

  .revenue-type-title {
    font-size: var(--text-base);
    font-weight: 600;
    color: var(--text-secondary);
    margin: 0 0 var(--spacing-sm) 0;
  }

  .revenue-type-value {
    font-size: var(--text-2xl);
    font-weight: 700;
    color: var(--accent-primary);
    margin-bottom: var(--spacing-xs);
  }

  .revenue-type-percent {
    font-size: var(--text-sm);
    color: var(--text-muted);
  }

  /* Inventory Tab Styles */
  .inventory-grid {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xl);
  }

  .alerts-section {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-md);
  }

  .alerts-list {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-md);
  }

  .alert-item {
    background: var(--theme-bg-card);
    backdrop-filter: blur(16px) saturate(150%);
    -webkit-backdrop-filter: blur(16px) saturate(150%);
    border: 1px solid var(--accent-danger);
    border-left: 4px solid var(--accent-danger);
    border-radius: 16px;
    padding: var(--spacing-lg);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }

  .alert-item:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(220, 38, 38, 0.2);
  }

  .alert-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--spacing-md);
  }

  .alert-product-name {
    font-size: var(--text-lg);
    font-weight: 700;
    color: var(--text-primary);
    margin: 0;
  }

  .alert-badge {
    background: var(--accent-danger);
    color: white;
    padding: var(--spacing-xs) var(--spacing-sm);
    border-radius: var(--radius-sm);
    font-size: var(--text-xs);
    font-weight: 600;
  }

  .alert-details {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xs);
  }

  .alert-detail {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .detail-value.alert {
    color: var(--accent-danger);
    font-weight: 700;
  }

  .no-alerts-section {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-md);
  }

  .no-alerts-card {
    background: var(--theme-bg-card);
    backdrop-filter: blur(16px) saturate(150%);
    -webkit-backdrop-filter: blur(16px) saturate(150%);
    border: 1px solid var(--accent-success);
    border-left: 4px solid var(--accent-success);
    border-radius: 16px;
    padding: var(--spacing-xl);
    text-align: center;
  }

  .no-alerts-title {
    font-size: var(--text-xl);
    font-weight: 700;
    color: var(--accent-success);
    margin: 0 0 var(--spacing-sm) 0;
  }

  .no-alerts-description {
    font-size: var(--text-base);
    color: var(--text-secondary);
    margin: 0;
  }

  /* Services Tab Styles */
  .services-grid {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xl);
  }

  .peak-hours-section {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-md);
  }

  .peak-hours-list {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-md);
  }

  .peak-hour-item {
    background: var(--theme-bg-card);
    backdrop-filter: blur(16px) saturate(150%);
    -webkit-backdrop-filter: blur(16px) saturate(150%);
    border: 1px solid var(--border-primary);
    border-radius: 16px;
    padding: var(--spacing-lg);
    display: flex;
    justify-content: space-between;
    align-items: center;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }

  .peak-hour-item:hover {
    transform: translateY(-2px);
    border-color: rgba(0, 147, 247, 0.5);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
  }

  .peak-hour-time {
    font-size: var(--text-lg);
    font-weight: 700;
    color: var(--text-primary);
  }

  .peak-hour-stats {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
  }

  .peak-hour-label {
    font-size: var(--text-sm);
    color: var(--text-secondary);
  }

  .peak-hour-value {
    font-size: var(--text-base);
    font-weight: 600;
    color: var(--accent-primary);
  }

  .sales-breakdown-section {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-md);
  }

  .sales-breakdown-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(min(200px, 100%), 1fr));
    gap: var(--spacing-lg);
  }

  .breakdown-card {
    background: var(--theme-bg-card);
    backdrop-filter: blur(16px) saturate(150%);
    -webkit-backdrop-filter: blur(16px) saturate(150%);
    border: 1px solid var(--border-primary);
    border-radius: 16px;
    padding: var(--spacing-lg);
    text-align: center;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }

  .breakdown-card:hover {
    transform: translateY(-2px);
    border-color: rgba(0, 147, 247, 0.5);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
  }

  .breakdown-title {
    font-size: var(--text-base);
    font-weight: 600;
    color: var(--text-secondary);
    margin: 0 0 var(--spacing-sm) 0;
  }

  .breakdown-value {
    font-size: var(--text-2xl);
    font-weight: 700;
    color: var(--accent-primary);
  }

  /* Period Selector Section Styles */
  .period-selector-section {
    margin-bottom: var(--spacing-lg);
    padding: var(--spacing-md);
    background: var(--theme-bg-elevated);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
  }

  .period-selector-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--spacing-md);
  }

  .period-selector-title {
    font-size: var(--text-base);
    font-weight: 600;
    color: var(--text-primary);
    margin: 0;
  }

  .reset-filter-button {
    display: flex;
    align-items: center;
    gap: var(--spacing-xs);
    padding: var(--spacing-xs) var(--spacing-sm);
    background: var(--theme-bg-card);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-sm);
    color: var(--text-secondary);
    font-size: var(--text-xs);
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .reset-filter-button:hover {
    background: var(--accent-primary);
    color: var(--text-inverse);
    border-color: var(--accent-primary);
  }

  .reset-icon {
    font-size: var(--text-sm);
  }

  .override-indicator {
    margin-top: var(--spacing-sm);
  }

  .override-badge {
    display: inline-block;
    padding: var(--spacing-xs) var(--spacing-sm);
    background: var(--accent-primary);
    color: var(--text-inverse);
    border-radius: var(--radius-sm);
    font-size: var(--text-xs);
    font-weight: 500;
  }

  /* Mobile-first responsive breakpoints */
  @media (max-width: 640px) {
    .reports-page {
      padding: var(--spacing-sm);
    }

    .reports-header {
      flex-direction: column;
      align-items: stretch;
      gap: var(--spacing-md);
    }

    .header-title {
      justify-content: center;
    }

    .page-title {
      font-size: clamp(var(--text-lg), 6vw, var(--text-2xl));
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

    .filters-grid {
      grid-template-columns: 1fr;
      gap: var(--spacing-sm);
    }

    .tab-content {
      padding: var(--spacing-sm);
    }

    .kpis-grid,
    .module-comparison-grid,
    .metrics-grid {
      grid-template-columns: 1fr;
      gap: var(--spacing-md);
    }

    .module-card {
      padding: var(--spacing-md);
    }

    .summary-grid {
      gap: var(--spacing-lg);
    }
  }

  @media (min-width: 641px) and (max-width: 1024px) {
    .reports-page {
      padding: var(--spacing-md);
    }

    .header-actions {
      flex-wrap: wrap;
    }

    .export-buttons {
      flex-wrap: wrap;
    }

    .kpis-grid {
      grid-template-columns: repeat(auto-fit, minmax(min(220px, 100%), 1fr));
    }

    .module-comparison-grid {
      grid-template-columns: repeat(auto-fit, minmax(min(280px, 100%), 1fr));
    }
  }

  /* Prevent hover transform issues on touch devices */
  @media (hover: none) and (pointer: coarse) {
    .export-buttons :global(.btn-brutalist:hover) {
      transform: none;
      box-shadow: 3px 3px 0px 0px var(--accent-primary);
      border-width: 2px;
    }
  }

</style>
