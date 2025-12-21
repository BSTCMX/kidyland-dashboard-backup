<script lang="ts">
  /**
   * ForecastingSection - Orchestrator component for Forecasting reports.
   * 
   * Features:
   * - Generates predictions for single module or multiple modules (when module === "all")
   * - Integrates with all report sections data
   * - Mobile-first responsive design
   * - No horizontal scroll on mobile/tablet
   */
  import { onMount } from 'svelte';
  import { post } from "@kidyland/utils";
  import LoadingSpinner from '$lib/components/admin/LoadingSpinner.svelte';
  import ErrorBanner from '$lib/components/admin/ErrorBanner.svelte';
  import { Sparkles } from "lucide-svelte";
  import { isMobileOrTablet } from '$lib/utils/useBreakpoint';
  import { 
    generateSegmentedPredictions,
    resetPredictionLimit,
    fetchSalesTimeSeries,
    updateForecastingPredictions,
    clearForecastingPredictions,
    type SegmentedPredictionsResponse,
    type TimeSeriesReport,
    type TimeSeriesDataPoint 
  } from '$lib/stores/reports';
  import type { 
    SalesReport, 
    StockReport, 
    ServicesReport,
    ArqueosReport,
    CustomersByModuleReport,
    ModuleComparison 
  } from '$lib/stores/reports';
  import { reportsStore } from '$lib/stores/reports';
  import ForecastingKPIs from './ForecastingKPIs.svelte';
  import ForecastingTimeSeriesChart from './ForecastingTimeSeriesChart.svelte';
  import ForecastingModuleComparison from './ForecastingModuleComparison.svelte';
  import ForecastingCalendarHeatmap from './ForecastingCalendarHeatmap.svelte';
  import ForecastingDayOfWeekDistribution from './ForecastingDayOfWeekDistribution.svelte';
  import ForecastingPeakHoursHeatmap from './ForecastingPeakHoursHeatmap.svelte';

  export let sucursalId: string | null = null;
  export let startDate: string;
  export let endDate: string;
  export let module: "all" | "recepcion" | "kidibar" = "all";

  // Prediction generation state
  let forecastDays: number = 7;
  let predictionType: "sales" | "capacity" | "stock" | "all" = "sales";
  let predictionInProgress: boolean = false;
  let predictionError: string | null = null;
  let showResetButton: boolean = false;
  let resettingLimit: boolean = false;
  
  // Predictions data
  let predictionsData: SegmentedPredictionsResponse | null = null;
  
  // Active module view for comparison (when module === "all")
  let activeModuleView: "comparison" | "recepcion" | "kidibar" | "total" = "comparison";

  // Simple cache for predictions (5 minutes TTL)
  interface CacheEntry {
    data: SegmentedPredictionsResponse;
    timestamp: number;
    key: string;
  }
  
  let predictionsCache: CacheEntry | null = null;
  const CACHE_TTL_MS = 5 * 60 * 1000; // 5 minutes

  // Generate cache key from parameters
  function getCacheKey(): string {
    const modulesToRequest = module === "all" ? ["recepcion", "kidibar", "all"] : [module];
    const predictionTypes = predictionType === "all" ? ["sales", "capacity", "stock"] : [predictionType];
    return `${sucursalId || 'all'}_${forecastDays}_${modulesToRequest.join(',')}_${predictionTypes.join(',')}`;
  }

  // Check if cached data is still valid
  function getCachedPredictions(): SegmentedPredictionsResponse | null {
    if (!predictionsCache) return null;
    
    const now = Date.now();
    const age = now - predictionsCache.timestamp;
    const currentKey = getCacheKey();
    
    // Check if cache key matches and is not expired
    if (predictionsCache.key === currentKey && age < CACHE_TTL_MS) {
      return predictionsCache.data;
    }
    
    // Cache expired or key mismatch
    predictionsCache = null;
    return null;
  }

  // Store predictions in cache
  function cachePredictions(data: SegmentedPredictionsResponse) {
    predictionsCache = {
      data,
      timestamp: Date.now(),
      key: getCacheKey(),
    };
  }
  
  // Historical data from store (accessible but not automatically loaded)
  let historicalData: {
    sales: SalesReport | null;
    stock: StockReport | null;
    services: ServicesReport | null;
    arqueos: ArqueosReport | null;
    customers: CustomersByModuleReport | null;
    moduleComparison: ModuleComparison | null;
  } = {
    sales: null,
    stock: null,
    services: null,
    arqueos: null,
    customers: null,
    moduleComparison: null,
  };

  // Historical time series data for charts
  let historicalTimeSeriesData: TimeSeriesDataPoint[] = [];
  let timeSeriesLoading = false;

  // Reactive update of historical data from store
  $: {
    historicalData = {
      sales: $reportsStore.sales,
      stock: $reportsStore.stock,
      services: $reportsStore.services,
      arqueos: $reportsStore.arqueos,
      customers: $reportsStore.customers,
      moduleComparison: $reportsStore.moduleComparison,
    };
  }

  // Load historical time series data when filters change
  async function loadHistoricalTimeSeries() {
    timeSeriesLoading = true;
    try {
      const timeSeriesReport = await fetchSalesTimeSeries(
        sucursalId,
        startDate,
        endDate,
        module === "all" ? undefined : module
      );
      
      if (timeSeriesReport?.timeseries) {
        historicalTimeSeriesData = timeSeriesReport.timeseries;
      }
    } catch (error: any) {
      console.error("Error loading historical time series:", error);
      // Don't show error to user, just use empty array
      historicalTimeSeriesData = [];
    } finally {
      timeSeriesLoading = false;
    }
  }

  // Track previous params to detect changes
  let previousSucursalId: string | null = null;
  let previousStartDate: string | null = null;
  let previousEndDate: string | null = null;
  let previousModule: "all" | "recepcion" | "kidibar" = "all";

  // Fetch when params change
  $: {
    const paramsChanged = 
      sucursalId !== previousSucursalId ||
      startDate !== previousStartDate ||
      endDate !== previousEndDate ||
      module !== previousModule;

    if (paramsChanged) {
      previousSucursalId = sucursalId;
      previousStartDate = startDate;
      previousEndDate = endDate;
      previousModule = module;
      loadHistoricalTimeSeries();
    }
  }

  onMount(() => {
    loadHistoricalTimeSeries();
  });

  // Prediction type options with metadata
  interface PredictionTypeOption {
    value: "sales" | "capacity" | "stock" | "all";
    label: string;
    availableFor: Array<"all" | "recepcion" | "kidibar">;
    description: string;
    tooltipDisabled?: string;
  }

  const predictionTypeOptions: PredictionTypeOption[] = [
    { 
      value: "sales", 
      label: "Ventas", 
      availableFor: ["all", "recepcion", "kidibar"],
      description: "Predicción de ventas y revenue"
    },
    { 
      value: "capacity", 
      label: "Capacidad", 
      availableFor: ["all", "recepcion"],
      description: "Predicción de uso de capacidad (solo Recepción - servicios)",
      tooltipDisabled: "Solo disponible para Recepción (se basa en timers de servicios)"
    },
    { 
      value: "stock", 
      label: "Inventario", 
      availableFor: ["all", "kidibar"],
      description: "Predicción de necesidades de inventario (solo KidiBar - productos)",
      tooltipDisabled: "Solo disponible para KidiBar (se basa en productos)"
    },
    { 
      value: "all", 
      label: "Todos", 
      availableFor: ["all", "recepcion", "kidibar"],
      description: "Genera todos los tipos de predicción aplicables al módulo seleccionado"
    }
  ];

  // Filter available types based on current module
  $: availableTypes = predictionTypeOptions.filter(opt => 
    opt.availableFor.includes(module)
  );

  // Check if current predictionType is still valid for current module
  $: if (availableTypes.length > 0 && !availableTypes.some(opt => opt.value === predictionType)) {
    // Reset to first available type if current selection is invalid
    predictionType = availableTypes[0].value as typeof predictionType;
  }

  // Handle forecast days changes
  function handleForecastDaysChange(newValue: number) {
    if (newValue >= 1 && newValue <= 30) {
      forecastDays = newValue;
    }
  }

  // Get tooltip for option based on module
  function getOptionTooltip(option: PredictionTypeOption): string {
    if (option.availableFor.includes(module)) {
      return option.description;
    }
    return option.tooltipDisabled || option.description;
  }

  /**
   * Generate predictions based on module selection.
   * Uses cache if available and valid.
   */
  async function handleGeneratePredictions() {
    if (predictionInProgress) {
      return;
    }

    // Check cache first
    const cached = getCachedPredictions();
    if (cached) {
      predictionsData = cached;
      predictionError = null;
      return;
    }

    predictionInProgress = true;
    predictionError = null;
    predictionsData = null;

    try {
      let modulesToRequest: string[] = [];
      if (module === "all") {
        modulesToRequest = ["recepcion", "kidibar", "all"];
      } else {
        modulesToRequest = [module];
      }

      // Map prediction type to array - filter based on module applicability
      let predictionTypes: string[] = [];
      if (predictionType === "all") {
        // For "all", only include types applicable to the selected module(s)
        if (module === "all") {
          predictionTypes = ["sales", "capacity", "stock"]; // All types for comparison view
        } else if (module === "recepcion") {
          predictionTypes = ["sales", "capacity"]; // No stock for recepcion
        } else if (module === "kidibar") {
          predictionTypes = ["sales", "stock"]; // No capacity for kidibar
        }
      } else {
        predictionTypes = [predictionType];
      }

      const response = await generateSegmentedPredictions(
        sucursalId,
        forecastDays,
        modulesToRequest,
        predictionTypes
      );

      if (response && response.success) {
        predictionsData = response;
        cachePredictions(response); // Cache the result
        
        // Sync with global store for export functionality
        updateForecastingPredictions(
          response,
          module,
          predictionType,
          forecastDays,
          sucursalId,
          startDate,
          endDate
        );
      } else {
        throw new Error(response?.message || "Error al generar predicciones");
      }
    } catch (error: any) {
      console.error("Error generating predictions:", error);
      
      // Handle specific error cases
      if (error.message?.includes("429") || error.message?.includes("Too Many Requests") || error.message?.includes("Maximum prediction limit")) {
        predictionError = "Límite de predicciones alcanzado (10 por sesión). Usa el botón de abajo para resetear.";
        showResetButton = true;
      } else if (error.message?.includes("401") || error.message?.includes("Unauthorized")) {
        predictionError = "Sesión expirada. Por favor inicia sesión nuevamente.";
      } else if (error.message?.includes("Failed to fetch") || error.message?.includes("CORS")) {
        predictionError = "Error de conexión. Verifica que el servidor esté funcionando.";
      } else if (error.message?.includes("500") || error.message?.includes("Internal Server Error")) {
        predictionError = "Error en el servidor. Por favor intenta nuevamente.";
      } else {
        predictionError = error.message || "Error al generar predicciones. Por favor intenta nuevamente.";
      }
    } finally {
      predictionInProgress = false;
    }
  }

  async function handleResetLimit() {
    resettingLimit = true;
    try {
      const result = await resetPredictionLimit();
      if (result?.success) {
        predictionError = null;
        showResetButton = false;
        // Optionally automatically retry
        await handleGeneratePredictions();
      } else {
        predictionError = "Error al resetear el límite. Intenta nuevamente.";
      }
    } catch (error: any) {
      predictionError = `Error al resetear el límite: ${error.message || "Error desconocido"}`;
    } finally {
      resettingLimit = false;
    }
  }

  // Clear cache when parameters change
  $: {
    // Invalidate cache when key parameters change
    const _ = getCacheKey(); // This will cause reactive update
    if (predictionsCache && predictionsCache.key !== getCacheKey()) {
      predictionsCache = null;
      // Also clear global store if parameters changed (indicating new context)
      if (sucursalId !== previousSucursalId || 
          startDate !== previousStartDate || 
          endDate !== previousEndDate || 
          module !== previousModule) {
        clearForecastingPredictions();
      }
    }
  }

  $: useMobile = $isMobileOrTablet;
</script>

<div class="forecasting-section">
  <!-- Controls Section -->
  <div class="controls-section">
    <div class="controls-header">
      <h3 class="section-title">Configuración de Predicciones</h3>
    </div>
    
    <div class="controls-grid">
      <div class="control-group">
        <label for="forecast-days">Días a predecir:</label>
        <input
          id="forecast-days"
          type="number"
          min="1"
          max="30"
          step="1"
          value={forecastDays}
          on:input={(e) => {
            const target = e.currentTarget;
            const val = parseInt(target.value, 10);
            if (!isNaN(val)) {
              handleForecastDaysChange(val);
            }
          }}
          disabled={predictionInProgress}
          class="forecast-input"
          aria-label="Días a predecir"
        />
      </div>
      
      <div class="control-group">
        <label for="prediction-type">Tipo:</label>
        <select
          id="prediction-type"
          bind:value={predictionType}
          disabled={predictionInProgress}
          class="type-select"
          title={predictionTypeOptions.find(opt => opt.value === predictionType)?.description || ""}
        >
          {#each availableTypes as option}
            <option 
              value={option.value}
              title={getOptionTooltip(option)}
            >
              {option.label}
            </option>
          {/each}
        </select>
        {#if module === "all" && (predictionType === "capacity" || predictionType === "stock" || predictionType === "all")}
          <p class="control-hint">
            {#if predictionType === "capacity"}
              ⓘ Capacidad solo se aplicará a Recepción
            {:else if predictionType === "stock"}
              ⓘ Inventario solo se aplicará a KidiBar
            {:else if predictionType === "all"}
              ⓘ Se generarán todos los tipos aplicables a cada módulo
            {/if}
          </p>
        {/if}
      </div>
      
      <div class="control-group generate-button-group">
        <button
          on:click={handleGeneratePredictions}
          disabled={predictionInProgress}
          class="generate-button"
          class:disabled={predictionInProgress}
          class:loading={predictionInProgress}
        >
          <Sparkles size={18} strokeWidth={1.5} style="display: inline-block; vertical-align: middle; margin-right: 6px;" />
          {predictionInProgress
            ? "Generando..."
            : "Generar Predicciones"}
        </button>
      </div>
    </div>

    {#if predictionError}
      <div class="error-banner">
        <span class="error-banner-text">{predictionError}</span>
        {#if showResetButton}
          <button
            on:click={handleResetLimit}
            disabled={resettingLimit}
            class="reset-limit-button"
          >
            {resettingLimit ? "Reseteando..." : "🔄 Resetear Límite"}
          </button>
        {/if}
      </div>
    {/if}
  </div>

  <!-- Predictions Display Section -->
  {#if predictionsData && predictionsData.success}
    <div class="predictions-display">
      <!-- Module Selection Tabs (only when module === "all") -->
      {#if module === "all" && predictionsData.predictions.total}
        {#if useMobile}
          <!-- Mobile: Dropdown -->
          <div class="module-selector-mobile">
            <select 
              class="module-select"
              bind:value={activeModuleView}
              aria-label="Seleccionar vista de módulo"
            >
              <option value="comparison">Comparación</option>
              <option value="recepcion">Recepción</option>
              <option value="kidibar">KidiBar</option>
              <option value="total">Total</option>
            </select>
          </div>
        {:else}
          <!-- Desktop: Tabs -->
          <div class="module-selector-desktop">
            <button
              class="module-tab"
              class:active={activeModuleView === "comparison"}
              on:click={() => activeModuleView = "comparison"}
            >
              Comparación
            </button>
            <button
              class="module-tab"
              class:active={activeModuleView === "recepcion"}
              on:click={() => activeModuleView = "recepcion"}
            >
              Recepción
            </button>
            <button
              class="module-tab"
              class:active={activeModuleView === "kidibar"}
              on:click={() => activeModuleView = "kidibar"}
            >
              KidiBar
            </button>
            <button
              class="module-tab"
              class:active={activeModuleView === "total"}
              on:click={() => activeModuleView = "total"}
            >
              Total
            </button>
          </div>
        {/if}
      {/if}

      <!-- Predictions Content -->
      <div class="predictions-content">
        {#if module === "all" && predictionsData.predictions.total}
          {#if activeModuleView === "comparison"}
            <!-- Comparison view: Show side-by-side comparison -->
            <ForecastingModuleComparison 
              {predictionsData} 
              historicalData={historicalTimeSeriesData}
              {forecastDays}
            />
          {:else if activeModuleView === "recepcion" && predictionsData.predictions.recepcion}
            <!-- Recepcion view -->
            <div class="module-view">
              <ForecastingKPIs {predictionsData} moduleKey="recepcion" />
              
              <div class="chart-section">
                <h4 class="chart-title">Revenue: Histórico vs Predicción</h4>
                <ForecastingTimeSeriesChart 
                  {predictionsData} 
                  moduleKey="recepcion" 
                  historicalData={historicalTimeSeriesData}
                />
              </div>

              <div class="chart-section">
                <ForecastingCalendarHeatmap {predictionsData} moduleKey="recepcion" />
              </div>

              <div class="chart-section">
                <ForecastingDayOfWeekDistribution {predictionsData} moduleKey="recepcion" />
              </div>

              <div class="chart-section">
                <ForecastingPeakHoursHeatmap {predictionsData} moduleKey="recepcion" forecastDays={forecastDays} />
              </div>
            </div>
          {:else if activeModuleView === "kidibar" && predictionsData.predictions.kidibar}
            <!-- Kidibar view -->
            <div class="module-view">
              <ForecastingKPIs {predictionsData} moduleKey="kidibar" />
              
              <div class="chart-section">
                <h4 class="chart-title">Revenue: Histórico vs Predicción</h4>
                <ForecastingTimeSeriesChart 
                  {predictionsData} 
                  moduleKey="kidibar" 
                  historicalData={historicalTimeSeriesData}
                />
              </div>

              <div class="chart-section">
                <ForecastingCalendarHeatmap {predictionsData} moduleKey="kidibar" />
              </div>

              <div class="chart-section">
                <ForecastingDayOfWeekDistribution {predictionsData} moduleKey="kidibar" />
              </div>

              <div class="chart-section">
                <ForecastingPeakHoursHeatmap {predictionsData} moduleKey="kidibar" forecastDays={forecastDays} />
              </div>
            </div>
          {:else if activeModuleView === "total" && predictionsData.predictions.total}
            <!-- Total view -->
            <div class="module-view">
              <ForecastingKPIs {predictionsData} moduleKey="total" />
              
              <div class="chart-section">
                <h4 class="chart-title">Revenue: Histórico vs Predicción</h4>
                <ForecastingTimeSeriesChart 
                  {predictionsData} 
                  moduleKey="total" 
                  historicalData={historicalTimeSeriesData}
                />
              </div>

              <div class="chart-section">
                <ForecastingCalendarHeatmap {predictionsData} moduleKey="total" />
              </div>

              <div class="chart-section">
                <ForecastingDayOfWeekDistribution {predictionsData} moduleKey="total" />
              </div>

              <div class="chart-section">
                <ForecastingPeakHoursHeatmap {predictionsData} moduleKey="total" forecastDays={forecastDays} />
              </div>
            </div>
          {/if}
        {:else}
          <!-- Single module view -->
          {#if module === "recepcion" && predictionsData.predictions.recepcion}
            <div class="module-view">
              <ForecastingKPIs {predictionsData} moduleKey="recepcion" />
              
              <div class="chart-section">
                <h4 class="chart-title">Revenue: Histórico vs Predicción</h4>
                <ForecastingTimeSeriesChart 
                  {predictionsData} 
                  moduleKey="recepcion" 
                  historicalData={historicalTimeSeriesData}
                />
              </div>

              <div class="chart-section">
                <ForecastingCalendarHeatmap {predictionsData} moduleKey="recepcion" />
              </div>

              <div class="chart-section">
                <ForecastingDayOfWeekDistribution {predictionsData} moduleKey="recepcion" />
              </div>

              <div class="chart-section">
                <ForecastingPeakHoursHeatmap {predictionsData} moduleKey="recepcion" forecastDays={forecastDays} />
              </div>
            </div>
          {:else if module === "kidibar" && predictionsData.predictions.kidibar}
            <div class="module-view">
              <ForecastingKPIs {predictionsData} moduleKey="kidibar" />
              
              <div class="chart-section">
                <h4 class="chart-title">Revenue: Histórico vs Predicción</h4>
                <ForecastingTimeSeriesChart 
                  {predictionsData} 
                  moduleKey="kidibar" 
                  historicalData={historicalTimeSeriesData}
                />
              </div>

              <div class="chart-section">
                <ForecastingCalendarHeatmap {predictionsData} moduleKey="kidibar" />
              </div>

              <div class="chart-section">
                <ForecastingDayOfWeekDistribution {predictionsData} moduleKey="kidibar" />
              </div>

              <div class="chart-section">
                <ForecastingPeakHoursHeatmap {predictionsData} moduleKey="kidibar" forecastDays={forecastDays} />
              </div>
            </div>
          {/if}
        {/if}
      </div>

      <!-- Confidence Badge -->
      <div class="confidence-info">
        <span class="confidence-badge" class:high={predictionsData.overall_confidence === "high"} class:medium={predictionsData.overall_confidence === "medium"} class:low={predictionsData.overall_confidence === "low"}>
          Confianza: {predictionsData.overall_confidence.toUpperCase()}
        </span>
        <span class="elapsed-time">
          Generado en {predictionsData.elapsed_seconds}s
        </span>
      </div>
    </div>
  {:else if !predictionInProgress && !predictionError}
    <div class="empty-state">
      <div class="empty-state-content">
        <p class="empty-state-message">Presiona "Generar Predicciones" para ver análisis y proyecciones</p>
        
        <!-- Historical Data Availability Summary -->
        {#if historicalData.sales || historicalData.stock || historicalData.services || historicalData.arqueos || historicalData.customers}
          <div class="historical-data-summary">
            <h4 class="data-summary-title">Datos históricos disponibles:</h4>
            <div class="data-availability-grid">
              {#if historicalData.sales}
                <div class="data-availability-item available">
                  <span class="data-icon">✓</span>
                  <span class="data-label">Ventas</span>
                </div>
              {/if}
              {#if historicalData.stock}
                <div class="data-availability-item available">
                  <span class="data-icon">✓</span>
                  <span class="data-label">Inventario</span>
                </div>
              {/if}
              {#if historicalData.services}
                <div class="data-availability-item available">
                  <span class="data-icon">✓</span>
                  <span class="data-label">Servicios</span>
                </div>
              {/if}
              {#if historicalData.arqueos}
                <div class="data-availability-item available">
                  <span class="data-icon">✓</span>
                  <span class="data-label">Arqueos</span>
                </div>
              {/if}
              {#if historicalData.customers}
                <div class="data-availability-item available">
                  <span class="data-icon">✓</span>
                  <span class="data-label">Clientes</span>
                </div>
              {/if}
              {#if historicalData.moduleComparison}
                <div class="data-availability-item available">
                  <span class="data-icon">✓</span>
                  <span class="data-label">Comparación de Módulos</span>
                </div>
              {/if}
            </div>
            <p class="data-hint-text">
              Las predicciones se generan utilizando estos datos históricos junto con análisis avanzados.
            </p>
          </div>
        {:else}
          <div class="no-data-hint">
            <p class="hint-text">
              💡 Los datos históricos se cargarán automáticamente cuando navegues a otras secciones de reportes o ajustes los filtros globales.
            </p>
          </div>
        {/if}
      </div>
    </div>
  {/if}
</div>

<style>
  .forecasting-section {
    width: 100%;
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xl, 1.5rem);
  }

  .controls-section {
    background: var(--theme-bg-card);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
    padding: var(--spacing-lg);
  }

  .controls-header {
    margin-bottom: var(--spacing-md);
  }

  .section-title {
    font-size: var(--text-xl, 1.25rem);
    font-weight: 700;
    color: var(--text-primary);
    margin: 0;
  }

  .controls-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(min(200px, 100%), 1fr));
    gap: var(--spacing-md);
    align-items: end;
  }

  .control-group {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xs);
  }

  .control-group label {
    font-size: var(--text-sm);
    color: var(--text-secondary);
    font-weight: 500;
  }

  .forecast-input,
  .type-select {
    border: 2px solid var(--accent-primary);
    box-shadow: 3px 3px 0px 0px var(--accent-primary);
    background-color: var(--theme-bg-elevated);
    color: var(--text-primary);
    font-weight: 600;
    border-radius: var(--radius-md);
    padding: var(--spacing-sm);
    font-size: var(--text-sm);
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  }

  .forecast-input {
    width: 100%;
    max-width: 120px;
    text-align: center;
  }

  .forecast-input:focus,
  .type-select:focus {
    outline: none;
    box-shadow: none;
    border-width: 3px;
    transform: translate(3px, 3px);
    background-color: var(--accent-primary);
    color: var(--text-inverse);
  }

  .forecast-input:hover:not(:disabled):not(:focus),
  .type-select:hover:not(:disabled):not(:focus) {
    border-color: var(--accent-primary);
    box-shadow: 2px 2px 0px 0px var(--accent-primary);
  }

  .forecast-input:disabled,
  .type-select:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .type-select {
    width: 100%;
    cursor: pointer;
  }

  .control-hint {
    font-size: var(--text-xs);
    color: var(--text-secondary);
    margin-top: var(--spacing-xs);
    font-style: italic;
    line-height: 1.4;
  }

  .generate-button-group {
    align-items: stretch;
  }

  .generate-button {
    border: 2px solid var(--accent-primary);
    box-shadow: 3px 3px 0px 0px var(--accent-primary);
    background-color: var(--theme-bg-elevated);
    color: var(--accent-primary);
    font-weight: 600;
    padding: var(--spacing-sm) var(--spacing-md);
    border-radius: var(--radius-md);
    cursor: pointer;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    font-size: var(--text-base);
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 44px; /* Minimum touch target */
  }

  .generate-button:hover:not(.disabled) {
    box-shadow: none;
    border-width: 3px;
    transform: translate(3px, 3px);
    background-color: var(--accent-primary);
    color: var(--text-inverse);
  }

  .generate-button:active:not(.disabled) {
    transform: translate(2px, 2px);
    transition-duration: 0.1s;
  }

  .generate-button.disabled,
  .generate-button.loading {
    opacity: 0.5;
    cursor: not-allowed;
    box-shadow: 1px 1px 0px 0px var(--accent-primary);
  }

  .generate-button.loading {
    animation: pulse 1.5s ease-in-out infinite;
  }

  @keyframes pulse {
    0%, 100% {
      opacity: 0.6;
    }
    50% {
      opacity: 0.8;
    }
  }

  .error-banner {
    background: rgba(239, 68, 68, 0.1);
    border: 1px solid #ef4444;
    color: #ef4444;
    padding: var(--spacing-md);
    border-radius: var(--radius-md);
    margin-top: var(--spacing-md);
    display: flex;
    flex-direction: column;
    gap: var(--spacing-sm);
    align-items: center;
    font-weight: 500;
  }

  .error-banner-text {
    text-align: center;
  }

  .reset-limit-button {
    background: var(--accent-primary);
    color: var(--theme-bg-primary);
    border: none;
    border-radius: var(--radius-sm);
    padding: var(--spacing-xs) var(--spacing-md);
    font-size: var(--text-sm);
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
    margin-top: var(--spacing-xs);
  }

  .reset-limit-button:hover:not(:disabled) {
    opacity: 0.9;
    transform: translateY(-1px);
  }

  .reset-limit-button:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .predictions-display {
    background: var(--theme-bg-card);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
    padding: var(--spacing-lg);
  }

  .module-selector-mobile {
    margin-bottom: var(--spacing-lg);
  }

  .module-select {
    width: 100%;
    padding: var(--spacing-sm);
    border: 2px solid var(--border-primary);
    border-radius: var(--radius-md);
    background: var(--theme-bg-elevated);
    color: var(--text-primary);
    font-size: var(--text-base);
    min-height: 44px;
  }

  .module-selector-desktop {
    display: flex;
    gap: var(--spacing-xs);
    margin-bottom: var(--spacing-lg);
    border-bottom: 2px solid var(--border-primary);
  }

  .module-tab {
    padding: var(--spacing-sm) var(--spacing-md);
    background: transparent;
    border: none;
    border-bottom: 2px solid transparent;
    color: var(--text-secondary);
    font-size: var(--text-sm);
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
    margin-bottom: -2px;
  }

  .module-tab:hover {
    color: var(--text-primary);
  }

  .module-tab.active {
    color: var(--accent-primary);
    border-bottom-color: var(--accent-primary);
    font-weight: 600;
  }

  .predictions-content {
    min-height: 200px;
  }

  .module-view {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xl);
  }

  .chart-section {
    width: 100%;
  }

  .chart-title {
    font-size: var(--text-lg);
    font-weight: 600;
    color: var(--text-primary);
    margin: 0 0 var(--spacing-md) 0;
  }

  .confidence-info {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: var(--spacing-lg);
    padding-top: var(--spacing-lg);
    border-top: 1px solid var(--border-primary);
    flex-wrap: wrap;
    gap: var(--spacing-sm);
  }

  .confidence-badge {
    display: inline-block;
    padding: var(--spacing-xs) var(--spacing-sm);
    border-radius: var(--radius-md);
    font-size: var(--text-xs);
    font-weight: 600;
  }

  .confidence-badge.high {
    background: #10b981;
    color: white;
  }

  .confidence-badge.medium {
    background: #f59e0b;
    color: white;
  }

  .confidence-badge.low {
    background: #ef4444;
    color: white;
  }

  .elapsed-time {
    font-size: var(--text-xs);
    color: var(--text-secondary);
  }

  .empty-state {
    background: var(--theme-bg-card);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
    padding: var(--spacing-2xl);
  }

  .empty-state-content {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: var(--spacing-lg);
  }

  .empty-state-message {
    text-align: center;
    color: var(--text-primary);
    font-size: var(--text-lg);
    font-weight: 500;
    margin: 0;
  }

  .historical-data-summary {
    width: 100%;
    max-width: 600px;
    background: var(--theme-bg-elevated);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
    padding: var(--spacing-lg);
  }

  .data-summary-title {
    font-size: var(--text-base);
    font-weight: 600;
    color: var(--text-primary);
    margin: 0 0 var(--spacing-md) 0;
  }

  .data-availability-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
    gap: var(--spacing-sm);
    margin-bottom: var(--spacing-md);
  }

  .data-availability-item {
    display: flex;
    align-items: center;
    gap: var(--spacing-xs);
    padding: var(--spacing-xs) var(--spacing-sm);
    border-radius: var(--radius-sm);
    font-size: var(--text-sm);
  }

  .data-availability-item.available {
    background: rgba(16, 185, 129, 0.1);
    border: 1px solid rgba(16, 185, 129, 0.3);
    color: #10b981;
  }

  .data-icon {
    font-weight: 700;
    font-size: var(--text-base);
  }

  .data-label {
    font-weight: 500;
  }

  .data-hint-text {
    font-size: var(--text-sm);
    color: var(--text-secondary);
    margin: 0;
    text-align: center;
    font-style: italic;
  }

  .no-data-hint {
    width: 100%;
    max-width: 500px;
  }

  .hint-text {
    text-align: center;
    font-size: var(--text-sm);
    color: var(--text-secondary);
    margin: 0;
  }

  /* Responsive adjustments */
  @media (max-width: 640px) {
    .controls-grid {
      grid-template-columns: 1fr;
    }

    .generate-button-group {
      grid-column: 1;
    }

    .generate-button {
      width: 100%;
    }

    .forecast-input {
      max-width: 100%;
    }

    .confidence-info {
      flex-direction: column;
      align-items: flex-start;
    }

    .module-view pre {
      font-size: 10px;
    }
  }

  @media (min-width: 641px) and (max-width: 1024px) {
    .controls-grid {
      grid-template-columns: repeat(2, 1fr);
    }

    .generate-button-group {
      grid-column: 1 / -1;
    }
  }
</style>

