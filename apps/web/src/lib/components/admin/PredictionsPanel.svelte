<script lang="ts">
  /**
   * PredictionsPanel component - Panel for generating and displaying predictions.
   * 
   * Features:
   * - Button to generate predictions on demand
   * - Display of sales, capacity, and stock predictions
   * - Visual feedback and error handling
   * - Only loads when user explicitly requests it
   */
  import { post } from "@kidyland/utils";
  import {
    metricsStore,
    updatePredictions,
    setPredictionInProgress,
    setPredictionError,
    type SalesPrediction,
    type CapacityPrediction,
    type StockPrediction,
    type SalesByTypePrediction,
    type PeakHoursPrediction,
    type BusiestDaysPrediction,
  } from "$lib/stores/metrics";
  import { 
    Sparkles, 
    DollarSign, 
    Timer, 
    Package, 
    CheckCircle, 
    Users, 
    Lightbulb, 
    BarChart3, 
    Clock, 
    Calendar 
  } from "lucide-svelte";

  // Component state
  // Initialize forecastDays from store or default to 7
  let forecastDays = $metricsStore.predictions.forecastDays || 7;
  let predictionType = "all";
  let lastPredictionTime = 0;
  let predictionCount = 0;
  let activeTypeTab: "products" | "services" | "packages" = "products";
  
  // Reactive disabled state for class directive
  $: disabled = $metricsStore.predictions.predictionInProgress;

  // Sync lastPredictionTime from store (read-only)
  $: {
    if ($metricsStore.predictions.generatedAt) {
      lastPredictionTime = $metricsStore.predictions.generatedAt;
    }
  }

  // Handle forecastDays changes - update store when user changes value
  function handleForecastDaysChange(newValue: number) {
    if (newValue >= 1 && newValue <= 90) {
      forecastDays = newValue;
      // Update store to persist the value
      $metricsStore.predictions.forecastDays = newValue;
    }
  }

  /**
   * Handle generate predictions button click.
   */
  async function handleGeneratePredictions() {
    const currentState = $metricsStore.predictions;
    const currentTime = Date.now();

    // Validation 1: Check if prediction is already in progress
    if (currentState.predictionInProgress) {
      return;
    }

    // Validation 2: Check minimum time between predictions (5 seconds)
    if (currentState.generatedAt) {
      const timeSinceLast = currentTime - currentState.generatedAt;
      if (timeSinceLast < 5000) {
        const remaining = ((5000 - timeSinceLast) / 1000).toFixed(1);
        setPredictionError(`Espera ${remaining}s antes de generar predicciones nuevamente`);
        return;
      }
    }

    // Validation 3: Check maximum prediction count (10 per session)
    // Note: This is tracked in backend, but we can show a warning
    if (predictionCount >= 10) {
      setPredictionError("Límite de predicciones alcanzado (10). Por favor espera.");
      return;
    }

    // Set prediction in progress
    setPredictionInProgress(true);
    setPredictionError(null);

    try {
      // Call predictions endpoint
      const response = await post<{
        success: boolean;
        message: string;
        predictions: {
          sales?: SalesPrediction;
          capacity?: CapacityPrediction;
          stock?: StockPrediction;
          sales_by_type?: SalesByTypePrediction;
          peak_hours?: PeakHoursPrediction;
          busiest_days?: BusiestDaysPrediction;
        };
        elapsed_seconds: number;
        confidence: string;
        forecast_days: number;
      }>("/reports/predictions/generate", {
        forecast_days: forecastDays,
        prediction_type: predictionType,
      });

      if (response.success && response.predictions) {
        // Update store with predictions
        updatePredictions(response.predictions, response.forecast_days);
        predictionCount++;
      } else {
        throw new Error(response.message || "Error al generar predicciones");
      }
    } catch (error: any) {
      console.error("Error generating predictions:", error);

      // Handle specific error cases
      if (error.message?.includes("429") || error.message?.includes("wait")) {
        setPredictionError("Demasiadas solicitudes. Por favor espera unos segundos.");
      } else if (error.message?.includes("401") || error.message?.includes("Unauthorized")) {
        setPredictionError("Sesión expirada. Por favor inicia sesión nuevamente.");
      } else if (error.message?.includes("Failed to fetch") || error.message?.includes("CORS")) {
        setPredictionError("Error de conexión. Verifica que el servidor esté funcionando.");
      } else if (error.message?.includes("500") || error.message?.includes("Internal Server Error")) {
        setPredictionError("Error en el servidor. Por favor intenta nuevamente.");
      } else {
        setPredictionError(error.message || "Error al generar predicciones. Por favor intenta nuevamente.");
      }
    } finally {
      // Reset is handled by updatePredictions or setPredictionError
      setTimeout(() => {
        setPredictionInProgress(false);
      }, 100);
    }
  }
</script>

<div class="predictions-panel">
  <div class="panel-header">
    <h2 class="panel-title">
      <Sparkles size={28} strokeWidth={1.5} style="display: inline-block; vertical-align: middle; margin-right: 12px;" />
      Predicciones y Análisis
    </h2>
  
    <div class="controls">
      <div class="control-group">
        <label for="forecast-days">Días a predecir:</label>
        <input
          id="forecast-days"
          type="number"
          min="1"
          max="90"
          step="1"
          value={forecastDays}
          on:input={(e) => {
            const target = e.currentTarget;
            const val = parseInt(target.value, 10);
            if (!isNaN(val)) {
              handleForecastDaysChange(val);
            }
          }}
          on:change={(e) => {
            const target = e.currentTarget;
            const val = parseInt(target.value, 10);
            if (!isNaN(val)) {
              handleForecastDaysChange(val);
            } else {
              // Reset to valid value if invalid
              target.value = forecastDays.toString();
            }
          }}
          disabled={$metricsStore.predictions.predictionInProgress}
          class="forecast-input"
          aria-label="Días a predecir"
        />
      </div>
      
      <div class="control-group">
        <label for="prediction-type">Tipo:</label>
        <select
          id="prediction-type"
          bind:value={predictionType}
          disabled={$metricsStore.predictions.predictionInProgress}
          class="type-select"
        >
          <option value="all">Todas</option>
          <option value="sales">Ventas</option>
          <option value="capacity">Capacidad</option>
          <option value="stock">Inventario</option>
        </select>
      </div>
      
      <button
        on:click={handleGeneratePredictions}
        disabled={disabled}
        class="generate-button"
        class:disabled={disabled}
        class:loading={$metricsStore.predictions.predictionInProgress}
      >
        <Sparkles size={18} strokeWidth={1.5} style="display: inline-block; vertical-align: middle; margin-right: 6px;" />
        {$metricsStore.predictions.predictionInProgress
          ? "Generando..."
          : "Generar predicciones"}
      </button>
    </div>
  </div>

  {#if $metricsStore.predictions.error}
    <div class="error-banner">
      {$metricsStore.predictions.error}
    </div>
  {/if}

  {#if $metricsStore.predictions.generatedAt}
    <div class="predictions-content">
      <!-- Sales Predictions -->
      {#if $metricsStore.predictions.sales && $metricsStore.predictions.sales.forecast.length > 0}
        <div class="prediction-card">
          <h3 class="card-title">
            <DollarSign size={20} strokeWidth={1.5} style="display: inline-block; vertical-align: middle; margin-right: 8px;" />
            Predicción de Ventas
          </h3>
          <div class="confidence-badge" class:high={$metricsStore.predictions.sales.confidence === "high"} class:medium={$metricsStore.predictions.sales.confidence === "medium"} class:low={$metricsStore.predictions.sales.confidence === "low"}>
            Confianza: {$metricsStore.predictions.sales.confidence.toUpperCase()}
          </div>
          
          <div class="forecast-list">
            {#each $metricsStore.predictions.sales.forecast.slice(0, 7) as day}
              <div class="forecast-item">
                <span class="forecast-date">{new Date(day.date).toLocaleDateString()}</span>
                <span class="forecast-value">
                  ${(day.predicted_revenue_cents / 100).toFixed(2)}
                </span>
                <span class="forecast-count">{day.predicted_count} ventas</span>
              </div>
            {/each}
          </div>
          
          {#if $metricsStore.predictions.sales.trend_factor}
            <div class="trend-info">
              Factor de tendencia: {$metricsStore.predictions.sales.trend_factor}
            </div>
          {/if}
        </div>
      {/if}

      <!-- Capacity Predictions -->
      {#if $metricsStore.predictions.capacity && $metricsStore.predictions.capacity.forecast.length > 0}
        <div class="prediction-card">
          <h3 class="card-title">
            <Timer size={20} strokeWidth={1.5} style="display: inline-block; vertical-align: middle; margin-right: 8px;" />
            Predicción de Capacidad
          </h3>
          <div class="confidence-badge" class:high={$metricsStore.predictions.capacity.confidence === "high"} class:medium={$metricsStore.predictions.capacity.confidence === "medium"} class:low={$metricsStore.predictions.capacity.confidence === "low"}>
            Confianza: {$metricsStore.predictions.capacity.confidence.toUpperCase()}
          </div>
          
          <div class="forecast-list">
            {#each $metricsStore.predictions.capacity.forecast.slice(0, 7) as day}
              <div class="forecast-item">
                <span class="forecast-date">{new Date(day.date).toLocaleDateString()}</span>
                <span class="forecast-value">{day.predicted_active_timers} timers</span>
                <span class="forecast-utilization">
                  {(day.utilization_rate * 100).toFixed(0)}% utilización
                </span>
              </div>
            {/each}
          </div>
        </div>
      {/if}

      <!-- Stock Predictions -->
      {#if $metricsStore.predictions.stock && $metricsStore.predictions.stock.reorder_suggestions.length > 0}
        <div class="prediction-card">
          <h3 class="card-title">
            <Package size={20} strokeWidth={1.5} style="display: inline-block; vertical-align: middle; margin-right: 8px;" />
            Sugerencias de Reorden
          </h3>
          <div class="confidence-badge" class:high={$metricsStore.predictions.stock.confidence === "high"} class:medium={$metricsStore.predictions.stock.confidence === "medium"} class:low={$metricsStore.predictions.stock.confidence === "low"}>
            Confianza: {$metricsStore.predictions.stock.confidence.toUpperCase()}
          </div>
          
          <div class="reorder-list">
            {#each $metricsStore.predictions.stock.reorder_suggestions.slice(0, 10) as suggestion}
              <div class="reorder-item" class:urgent={suggestion.days_until_out_of_stock <= 3}>
                <div class="reorder-header">
                  <span class="product-name">{suggestion.product_name}</span>
                  <span class="days-until">
                    {suggestion.days_until_out_of_stock} días restantes
                  </span>
                </div>
                <div class="reorder-details">
                  <span>Stock actual: {suggestion.current_stock}</span>
                  <span>Uso diario predicho: {suggestion.predicted_daily_usage.toFixed(1)}</span>
                  <span class="recommended-qty">
                    Recomendado: {suggestion.recommended_reorder_qty} unidades
                  </span>
                </div>
              </div>
            {/each}
          </div>
        </div>
      {:else if $metricsStore.predictions.stock}
        <div class="prediction-card">
          <div class="no-suggestions">
            <CheckCircle size={20} strokeWidth={1.5} style="display: inline-block; vertical-align: middle; margin-right: 8px;" />
            No hay sugerencias de reorden en este momento
          </div>
        </div>
      {/if}

      <!-- Top Customers Info (for predictions context) -->
      {#if $metricsStore.top_customers && $metricsStore.top_customers.top_customers && $metricsStore.top_customers.top_customers.length > 0}
        <div class="prediction-card">
          <h3 class="card-title">
            <Users size={20} strokeWidth={1.5} style="display: inline-block; vertical-align: middle; margin-right: 8px;" />
            Clientes Top (Contexto para Predicciones)
          </h3>
          <div class="info-badge">
            Últimos {$metricsStore.top_customers.period_days} días
          </div>
          
          <div class="customers-list">
            {#each $metricsStore.top_customers.top_customers.slice(0, 5) as customer, index}
              <div class="customer-item">
                <div class="customer-header">
                  <span class="customer-rank">#{index + 1}</span>
                  <span class="customer-name">
                    {customer.child_name}
                    {#if customer.child_age}
                      <span class="customer-age">({customer.child_age} años)</span>
                    {/if}
                  </span>
                </div>
                <div class="customer-stats">
                  <span class="stat-item">
                    <span class="stat-label">Visitas:</span>
                    <span class="stat-value">{customer.visit_count}</span>
                  </span>
                  <span class="stat-item">
                    <span class="stat-label">Total gastado:</span>
                    <span class="stat-value">${((customer.total_revenue_cents || 0) / 100).toFixed(2)}</span>
                  </span>
                  <span class="stat-item">
                    <span class="stat-label">Promedio por visita:</span>
                    <span class="stat-value">
                      ${((customer.total_revenue_cents || 0) / (customer.visit_count || 1) / 100).toFixed(2)}
                    </span>
                  </span>
                </div>
              </div>
            {/each}
          </div>
          
          <div class="customers-note">
            <Lightbulb size={16} strokeWidth={1.5} style="display: inline-block; vertical-align: middle; margin-right: 6px;" />
            <small>
              Estos clientes frecuentes son considerados en las predicciones de ventas y capacidad
            </small>
          </div>
        </div>
      {/if}

      <!-- Sales by Type Predictions -->
      {#if $metricsStore.predictions.sales_by_type && $metricsStore.predictions.sales_by_type.forecast}
        <div class="prediction-card">
          <h3 class="card-title">
            <BarChart3 size={20} strokeWidth={1.5} style="display: inline-block; vertical-align: middle; margin-right: 8px;" />
            Predicción de Ventas por Tipo
          </h3>
          <div class="confidence-badge" class:high={$metricsStore.predictions.sales_by_type.confidence === "high"} class:medium={$metricsStore.predictions.sales_by_type.confidence === "medium"} class:low={$metricsStore.predictions.sales_by_type.confidence === "low"}>
            Confianza: {$metricsStore.predictions.sales_by_type.confidence.toUpperCase()}
          </div>
          
          <div class="type-tabs">
            <button
              class="type-tab"
              class:active={activeTypeTab === "products"}
              on:click={() => activeTypeTab = "products"}
              type="button"
            >
              Productos
            </button>
            <button
              class="type-tab"
              class:active={activeTypeTab === "services"}
              on:click={() => activeTypeTab = "services"}
              type="button"
            >
              Servicios
            </button>
            <button
              class="type-tab"
              class:active={activeTypeTab === "packages"}
              on:click={() => activeTypeTab = "packages"}
              type="button"
            >
              Paquetes
            </button>
          </div>
          
          <div class="forecast-list">
            {#if activeTypeTab === "products" && $metricsStore.predictions.sales_by_type.forecast.products}
              {#each $metricsStore.predictions.sales_by_type.forecast.products.slice(0, 7) as day}
                <div class="forecast-item">
                  <span class="forecast-date">{new Date(day.date).toLocaleDateString()}</span>
                  <span class="forecast-value">
                    ${(day.predicted_revenue_cents / 100).toFixed(2)}
                  </span>
                  <span class="forecast-count">{day.predicted_count} ventas</span>
                </div>
              {/each}
            {:else if activeTypeTab === "services" && $metricsStore.predictions.sales_by_type.forecast.services}
              {#each $metricsStore.predictions.sales_by_type.forecast.services.slice(0, 7) as day}
                <div class="forecast-item">
                  <span class="forecast-date">{new Date(day.date).toLocaleDateString()}</span>
                  <span class="forecast-value">
                    ${(day.predicted_revenue_cents / 100).toFixed(2)}
                  </span>
                  <span class="forecast-count">{day.predicted_count} ventas</span>
                </div>
              {/each}
            {:else if activeTypeTab === "packages" && $metricsStore.predictions.sales_by_type.forecast.packages}
              {#each $metricsStore.predictions.sales_by_type.forecast.packages.slice(0, 7) as day}
                <div class="forecast-item">
                  <span class="forecast-date">{new Date(day.date).toLocaleDateString()}</span>
                  <span class="forecast-value">
                    ${(day.predicted_revenue_cents / 100).toFixed(2)}
                  </span>
                  <span class="forecast-count">{day.predicted_count} ventas</span>
                </div>
              {/each}
            {/if}
          </div>
        </div>
      {/if}

      <!-- Peak Hours Predictions -->
      {#if $metricsStore.predictions.peak_hours && $metricsStore.predictions.peak_hours.forecast.length > 0}
        <div class="prediction-card">
          <h3 class="card-title">
            <Clock size={20} strokeWidth={1.5} style="display: inline-block; vertical-align: middle; margin-right: 8px;" />
            Predicción de Horas Pico
          </h3>
          <div class="confidence-badge" class:high={$metricsStore.predictions.peak_hours.confidence === "high"} class:medium={$metricsStore.predictions.peak_hours.confidence === "medium"} class:low={$metricsStore.predictions.peak_hours.confidence === "low"}>
            Confianza: {$metricsStore.predictions.peak_hours.confidence.toUpperCase()}
          </div>
          
          <div class="forecast-list">
            {#each $metricsStore.predictions.peak_hours.forecast.slice(0, 7) as day}
              <div class="forecast-item">
                <div class="forecast-header">
                  <span class="forecast-date">{new Date(day.date).toLocaleDateString()}</span>
                  {#if day.busiest_hour}
                    <span class="busiest-hour">
                      Hora más ocupada: {day.busiest_hour.hour}:00 ({day.busiest_hour.expected_activity.toFixed(1)} actividad)
                    </span>
                  {/if}
                </div>
                {#if day.predicted_peak_hours.length > 0}
                  <div class="peak-hours-list">
                    {#each day.predicted_peak_hours as peak}
                      <span class="peak-hour-badge">
                        {peak.hour}:00 ({peak.expected_activity.toFixed(1)})
                      </span>
                    {/each}
                  </div>
                {/if}
              </div>
            {/each}
          </div>
        </div>
      {/if}

      <!-- Busiest Days Predictions -->
      {#if $metricsStore.predictions.busiest_days && $metricsStore.predictions.busiest_days.forecast.length > 0}
        <div class="prediction-card">
          <h3 class="card-title">
            <Calendar size={20} strokeWidth={1.5} style="display: inline-block; vertical-align: middle; margin-right: 8px;" />
            Días Más Ocupados
          </h3>
          <div class="confidence-badge" class:high={$metricsStore.predictions.busiest_days.confidence === "high"} class:medium={$metricsStore.predictions.busiest_days.confidence === "medium"} class:low={$metricsStore.predictions.busiest_days.confidence === "low"}>
            Confianza: {$metricsStore.predictions.busiest_days.confidence.toUpperCase()}
          </div>
          
          <div class="forecast-list">
            {#each $metricsStore.predictions.busiest_days.forecast.slice(0, 7) as day}
              <div class="forecast-item" class:top-rank={day.rank <= 3}>
                <div class="forecast-header">
                  <span class="forecast-date">
                    {new Date(day.date).toLocaleDateString()} ({day.day_of_week})
                  </span>
                  <span class="rank-badge">#{day.rank}</span>
                </div>
                <span class="forecast-value">
                  Actividad predicha: ${(day.predicted_activity / 100).toFixed(2)}
                </span>
              </div>
            {/each}
          </div>
        </div>
      {/if}

      {#if $metricsStore.predictions.generatedAt}
        <div class="generated-at">
          Generado: {new Date($metricsStore.predictions.generatedAt).toLocaleString()}
        </div>
      {/if}
    </div>
  {:else}
    <div class="empty-state">
      <p>Presiona "Generar predicciones" para ver análisis y proyecciones</p>
    </div>
  {/if}
</div>

<style>
  .predictions-panel {
    background: var(--theme-bg-card);
    backdrop-filter: blur(16px) saturate(150%);
    -webkit-backdrop-filter: blur(16px) saturate(150%);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-lg);
    padding: var(--spacing-xl);
    margin-top: var(--spacing-xl);
    box-shadow: 
      0 8px 24px rgba(0, 0, 0, 0.15),
      0 0 20px var(--glow-primary, rgba(0, 147, 247, 0.3)),
      inset 0 1px 0 rgba(255, 255, 255, 0.05);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }

  /* Hover effect - Hybrid card10 + metric-card */
  .predictions-panel:hover {
    transform: translateY(-4px);
    border-color: rgba(0, 147, 247, 0.5);
    box-shadow: 
      0 20px 60px rgba(0, 0, 0, 0.3),
      0 0 30px var(--glow-primary, rgba(0, 147, 247, 0.4)),
      0 0 40px var(--glow-secondary, rgba(139, 92, 246, 0.3)),
      inset 0 1px 0 rgba(255, 255, 255, 0.1);
  }

  .panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--spacing-lg);
    flex-wrap: wrap;
    gap: var(--spacing-md);
  }

  .panel-title {
    font-size: var(--text-2xl);
    font-weight: 700;
    color: var(--text-primary);
    margin: 0;
    display: flex;
    align-items: center;
  }

  .controls {
    display: flex;
    gap: var(--spacing-md);
    align-items: center;
    flex-wrap: wrap;
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

  /* Brutalist style for input and select */
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
    width: 80px;
    text-align: center;
  }

  .forecast-input:focus,
  .type-select:focus {
    outline: none;
    box-shadow: none;
    border-width: 3px;
    transform: translate(3px, 3px);
    background-color: var(--accent-primary);
    color: var(--text-inverse, white);
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
    box-shadow: 1px 1px 0px 0px var(--accent-primary);
  }

  .type-select {
    width: 120px;
    cursor: pointer;
  }

  /* Brutalist style for generate button */
  .generate-button {
    border: 2px solid var(--accent-primary);
    box-shadow: 3px 3px 0px 0px var(--accent-primary);
    background-color: var(--theme-bg-elevated);
    color: var(--accent-primary);
    font-weight: 600;
    padding: var(--spacing-md) var(--spacing-lg);
    border-radius: var(--radius-md);
    cursor: pointer;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    font-size: var(--text-base);
    display: inline-flex;
    align-items: center;
  }

  .generate-button:hover:not(.disabled) {
    box-shadow: none;
    border-width: 3px;
    transform: translate(3px, 3px);
    background-color: var(--accent-primary);
    color: var(--text-inverse, white);
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
    background-color: var(--theme-bg-elevated);
    color: var(--accent-primary);
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
    border: 1px solid var(--accent-danger);
    color: var(--accent-danger);
    padding: var(--spacing-md);
    border-radius: var(--radius-md);
    margin-bottom: var(--spacing-md);
    text-align: center;
    font-weight: 500;
  }

  .predictions-content {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-lg);
  }

  .prediction-card {
    background: var(--theme-bg-secondary);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
    padding: var(--spacing-lg);
    box-shadow: var(--shadow-sm);
    transition: all 0.2s ease;
  }

  .prediction-card:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-md);
    border-color: var(--accent-primary);
  }

  .card-title {
    font-size: var(--text-xl);
    font-weight: 700;
    color: var(--text-primary);
    margin: 0 0 var(--spacing-md) 0;
    display: flex;
    align-items: center;
  }

  .confidence-badge {
    display: inline-block;
    padding: var(--spacing-xs) var(--spacing-sm);
    border-radius: var(--radius-sm);
    font-size: var(--text-xs);
    font-weight: 600;
    margin-bottom: var(--spacing-md);
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .confidence-badge.high {
    background: var(--accent-success);
    color: white;
  }

  .confidence-badge.medium {
    background: var(--accent-warning, #f59e0b);
    color: white;
  }

  .confidence-badge.low {
    background: var(--accent-danger);
    color: white;
  }

  .forecast-list {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-sm);
  }

  .forecast-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: var(--spacing-md);
    background: var(--theme-bg-card);
    border-radius: var(--radius-md);
    gap: var(--spacing-md);
    flex-wrap: wrap;
  }

  .forecast-date {
    font-weight: 600;
    color: var(--text-secondary);
    min-width: 120px;
    font-size: var(--text-sm);
  }

  .forecast-value {
    font-size: var(--text-xl);
    font-weight: 700;
    color: var(--accent-primary);
  }

  .forecast-count,
  .forecast-utilization {
    color: var(--text-secondary);
    font-size: var(--text-sm);
  }

  .trend-info {
    margin-top: var(--spacing-md);
    padding-top: var(--spacing-md);
    border-top: 1px solid var(--border-primary);
    color: var(--text-secondary);
    font-size: var(--text-sm);
  }

  .reorder-list {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-md);
  }

  .reorder-item {
    padding: var(--spacing-md);
    background: var(--theme-bg-card);
    border-radius: var(--radius-md);
    border-left: 4px solid var(--accent-primary);
  }

  .reorder-item.urgent {
    border-left-color: var(--accent-danger);
    background: rgba(239, 68, 68, 0.1);
  }

  .reorder-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--spacing-sm);
    flex-wrap: wrap;
    gap: var(--spacing-xs);
  }

  .product-name {
    font-weight: 600;
    color: var(--text-primary);
    font-size: var(--text-base);
  }

  .days-until {
    font-size: var(--text-sm);
    color: var(--accent-warning, #f59e0b);
    font-weight: 600;
  }

  .reorder-item.urgent .days-until {
    color: var(--accent-danger);
  }

  .reorder-details {
    display: flex;
    gap: var(--spacing-md);
    font-size: var(--text-sm);
    color: var(--text-secondary);
    flex-wrap: wrap;
  }

  .recommended-qty {
    color: var(--accent-success);
    font-weight: 600;
  }

  .no-suggestions {
    text-align: center;
    color: var(--accent-success);
    padding: var(--spacing-xl);
    font-weight: 500;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .generated-at {
    text-align: center;
    color: var(--text-secondary);
    font-size: var(--text-sm);
    margin-top: var(--spacing-md);
    padding-top: var(--spacing-md);
    border-top: 1px solid var(--border-primary);
  }

  .empty-state {
    text-align: center;
    color: var(--text-secondary);
    padding: var(--spacing-xl);
    font-style: italic;
  }

  .info-badge {
    display: inline-block;
    padding: var(--spacing-xs) var(--spacing-sm);
    background: var(--theme-bg-elevated);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-sm);
    font-size: var(--text-xs);
    color: var(--text-secondary);
    margin-bottom: var(--spacing-md);
  }

  .customers-list {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-md);
  }

  .customer-item {
    padding: var(--spacing-md);
    background: var(--theme-bg-card);
    border-radius: var(--radius-md);
    border-left: 4px solid var(--accent-primary);
  }

  .customer-header {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    margin-bottom: var(--spacing-sm);
  }

  .customer-rank {
    background: var(--accent-primary);
    color: white;
    padding: 2px 8px;
    border-radius: var(--radius-sm);
    font-size: var(--text-xs);
    font-weight: 700;
  }

  .customer-name {
    font-weight: 600;
    color: var(--text-primary);
    font-size: var(--text-base);
  }

  .customer-age {
    color: var(--text-secondary);
    font-weight: 400;
    font-size: var(--text-sm);
  }

  .customer-stats {
    display: flex;
    gap: var(--spacing-md);
    flex-wrap: wrap;
  }

  .stat-item {
    display: flex;
    gap: var(--spacing-xs);
    font-size: var(--text-sm);
  }

  .stat-label {
    color: var(--text-secondary);
  }

  .stat-value {
    font-weight: 600;
    color: var(--text-primary);
  }

  .customers-note {
    margin-top: var(--spacing-md);
    padding-top: var(--spacing-md);
    border-top: 1px solid var(--border-primary);
    color: var(--text-secondary);
    font-size: var(--text-sm);
    display: flex;
    align-items: flex-start;
    gap: var(--spacing-xs);
  }

  .customers-note small {
    flex: 1;
  }

  .type-tabs {
    display: flex;
    gap: var(--spacing-sm);
    margin-bottom: var(--spacing-md);
    border-bottom: 2px solid var(--border-primary);
  }

  .type-tab {
    padding: var(--spacing-sm) var(--spacing-md);
    cursor: pointer;
    color: var(--text-secondary);
    border: none;
    background: transparent;
    border-bottom: 2px solid transparent;
    margin-bottom: -2px;
    transition: all 0.2s ease;
    font-size: var(--text-sm);
    font-weight: 500;
  }

  .type-tab:hover {
    color: var(--text-primary);
  }

  .type-tab.active {
    color: var(--accent-primary);
    border-bottom-color: var(--accent-primary);
    font-weight: 600;
  }

  .forecast-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    width: 100%;
    margin-bottom: var(--spacing-sm);
    flex-wrap: wrap;
    gap: var(--spacing-xs);
  }

  .busiest-hour {
    font-size: var(--text-sm);
    color: var(--accent-warning, #f59e0b);
    font-weight: 600;
  }

  .peak-hours-list {
    display: flex;
    gap: var(--spacing-sm);
    flex-wrap: wrap;
    margin-top: var(--spacing-sm);
  }

  .peak-hour-badge {
    background: rgba(99, 102, 241, 0.2);
    border: 1px solid var(--accent-primary);
    border-radius: var(--radius-sm);
    padding: var(--spacing-xs) var(--spacing-sm);
    font-size: var(--text-xs);
    color: var(--accent-primary);
  }

  .rank-badge {
    background: var(--accent-primary);
    color: white;
    padding: var(--spacing-xs) var(--spacing-sm);
    border-radius: var(--radius-sm);
    font-size: var(--text-xs);
    font-weight: 700;
  }

  .forecast-item.top-rank {
    border-left: 4px solid var(--accent-success);
    background: rgba(34, 197, 94, 0.1);
  }

  /* Mobile: Optimize panel header and controls for touch devices */
  @media (max-width: 768px) {
    .panel-header {
      flex-direction: column;
      align-items: stretch;
      gap: var(--spacing-md);
    }

    .panel-title {
      font-size: var(--text-xl);
      text-align: center;
      justify-content: center;
    }

    .controls {
      flex-direction: column;
      width: 100%;
      gap: var(--spacing-md);
      flex-wrap: nowrap;
    }

    .control-group {
      width: 100%;
    }

    .forecast-input,
    .type-select {
      width: 100%;
      min-height: 44px; /* Minimum touch target size for accessibility */
      text-align: left;
    }

    .forecast-input {
      text-align: center;
    }

    .generate-button {
      width: 100%;
      min-height: 44px; /* Minimum touch target size for accessibility */
      justify-content: center;
    }

    .forecast-item {
      flex-direction: column;
      align-items: flex-start;
    }

    .forecast-date {
      min-width: auto;
      width: 100%;
    }
  }

  /* Prevent hover transform issues on touch devices */
  @media (hover: none) and (pointer: coarse) {
    .generate-button:hover {
      transform: none;
      box-shadow: 3px 3px 0px 0px var(--accent-primary);
      border-width: 2px;
    }

    .forecast-input:hover:not(:disabled):not(:focus),
    .type-select:hover:not(:disabled):not(:focus) {
      transform: none;
    }

    .predictions-panel:hover {
      transform: none;
    }
  }
</style>
