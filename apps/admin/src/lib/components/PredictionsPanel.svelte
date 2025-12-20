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
  } from "$lib/stores/metrics";

  // Component state
  let forecastDays = 7;
  let predictionType = "all";
  let lastPredictionTime = 0;
  let predictionCount = 0;

  // Subscribe to store
  $: {
    if ($metricsStore.predictions.generatedAt) {
      lastPredictionTime = $metricsStore.predictions.generatedAt;
    }
    forecastDays = $metricsStore.predictions.forecastDays;
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
      if (error.message?.includes("429")) {
        setPredictionError("Demasiadas solicitudes. Por favor espera.");
      } else if (error.message?.includes("401")) {
        setPredictionError("Sesión expirada. Por favor inicia sesión nuevamente.");
      } else {
        setPredictionError(error.message || "Error al generar predicciones");
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
    <h2 class="panel-title">🔮 Predicciones y Análisis</h2>
    
    <div class="controls">
      <div class="control-group">
        <label for="forecast-days">Días a predecir:</label>
        <input
          id="forecast-days"
          type="number"
          min="1"
          max="30"
          bind:value={forecastDays}
          disabled={$metricsStore.predictions.predictionInProgress}
          class="forecast-input"
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
        disabled={$metricsStore.predictions.predictionInProgress}
        class="generate-button"
        class:disabled
        class:loading={$metricsStore.predictions.predictionInProgress}
      >
        {$metricsStore.predictions.predictionInProgress
          ? "🔄 Generando..."
          : "🔮 Generar predicciones"}
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
          <h3 class="card-title">💰 Predicción de Ventas</h3>
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
          <h3 class="card-title">⏱️ Predicción de Capacidad</h3>
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
          <h3 class="card-title">📦 Sugerencias de Reorden</h3>
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
            ✅ No hay sugerencias de reorden en este momento
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
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 1rem;
    padding: 1.5rem;
    margin-top: 2rem;
    backdrop-filter: blur(10px);
  }

  .panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1.5rem;
    flex-wrap: wrap;
    gap: 1rem;
  }

  .panel-title {
    font-size: 1.5rem;
    font-weight: 700;
    color: #f0e7ff;
    margin: 0;
  }

  .controls {
    display: flex;
    gap: 1rem;
    align-items: center;
    flex-wrap: wrap;
  }

  .control-group {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  .control-group label {
    font-size: 0.875rem;
    color: #9ca3af;
  }

  .forecast-input,
  .type-select {
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 0.5rem;
    padding: 0.5rem;
    color: white;
    font-size: 0.875rem;
  }

  .forecast-input {
    width: 80px;
  }

  .type-select {
    width: 120px;
  }

  .generate-button {
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
    color: white;
    font-weight: 600;
    padding: 0.75rem 1.5rem;
    border-radius: 0.5rem;
    border: none;
    cursor: pointer;
    transition: all 0.2s ease;
    font-size: 1rem;
  }

  .generate-button:hover:not(.disabled) {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(99, 102, 241, 0.3);
  }

  .generate-button.disabled,
  .generate-button.loading {
    opacity: 0.6;
    cursor: not-allowed;
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
    background: #ef4444;
    color: white;
    padding: 1rem;
    border-radius: 0.5rem;
    margin-bottom: 1rem;
    text-align: center;
    font-weight: 500;
  }

  .predictions-content {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }

  .prediction-card {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 0.75rem;
    padding: 1.5rem;
  }

  .card-title {
    font-size: 1.25rem;
    font-weight: 700;
    color: #f0e7ff;
    margin: 0 0 1rem 0;
  }

  .confidence-badge {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: 0.5rem;
    font-size: 0.75rem;
    font-weight: 600;
    margin-bottom: 1rem;
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

  .forecast-list {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .forecast-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.75rem;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 0.5rem;
    gap: 1rem;
  }

  .forecast-date {
    font-weight: 600;
    color: #d1d5db;
    min-width: 120px;
  }

  .forecast-value {
    font-size: 1.25rem;
    font-weight: 700;
    color: #d946ef;
  }

  .forecast-count,
  .forecast-utilization {
    color: #9ca3af;
    font-size: 0.875rem;
  }

  .trend-info {
    margin-top: 1rem;
    padding-top: 1rem;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
    color: #9ca3af;
    font-size: 0.875rem;
  }

  .reorder-list {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .reorder-item {
    padding: 1rem;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 0.5rem;
    border-left: 4px solid #6366f1;
  }

  .reorder-item.urgent {
    border-left-color: #ef4444;
    background: rgba(239, 68, 68, 0.1);
  }

  .reorder-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.5rem;
  }

  .product-name {
    font-weight: 600;
    color: #f0e7ff;
  }

  .days-until {
    font-size: 0.875rem;
    color: #f59e0b;
    font-weight: 600;
  }

  .reorder-item.urgent .days-until {
    color: #ef4444;
  }

  .reorder-details {
    display: flex;
    gap: 1rem;
    font-size: 0.875rem;
    color: #9ca3af;
    flex-wrap: wrap;
  }

  .recommended-qty {
    color: #10b981;
    font-weight: 600;
  }

  .no-suggestions {
    text-align: center;
    color: #10b981;
    padding: 2rem;
    font-weight: 500;
  }

  .generated-at {
    text-align: center;
    color: #6b7280;
    font-size: 0.875rem;
    margin-top: 1rem;
    padding-top: 1rem;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
  }

  .empty-state {
    text-align: center;
    color: #6b7280;
    padding: 3rem;
    font-style: italic;
  }
</style>


