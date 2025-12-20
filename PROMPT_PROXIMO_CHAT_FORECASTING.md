# 📋 PROMPT PARA PRÓXIMO CHAT - SECCIÓN FORECASTING EN REPORTES

## 🎯 CONTEXTO DEL PROYECTO KIDYLAND

### Arquitectura y Estructura
- **Proyecto monorepo** con Clean Architecture
- **Backend:** FastAPI (Python) en `packages/api/`
- **Frontend:** SvelteKit en `apps/web/`
- **Estructura modular:** servicios, routers, modelos, stores
- **Sin git aún** (todo en local)

### Cómo Iniciar el Proyecto

#### Backend (FastAPI)
```bash
cd /Users/Jorge/Documents/kidyland/packages/api
source venv/bin/activate  # Activar entorno virtual
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
- **Puerto:** 8000
- **Docs:** http://localhost:8000/docs
- **Health:** http://localhost:8000/health
- **Logs:** `/tmp/kidyland-backend.log` (si se usa el script)
- **Variables de entorno:** Archivo `.env` en `packages/api/`
  - `DATABASE_URL`: conexión PostgreSQL
  - `SECRET_KEY`: clave secreta para JWT

#### Frontend (SvelteKit)
```bash
cd /Users/Jorge/Documents/kidyland/apps/web
pnpm dev
```
- **Puerto:** 5179 (configurado en `vite.config.ts`)
- **Hot reload activo**
- **Logs:** `/tmp/kidyland-frontend.log` (si se usa el script)

### Comandos Importantes

#### Compilación y Validación
```bash
# Frontend - Verificar sintaxis
cd apps/web
pnpm run check

# Backend - Verificar sintaxis Python
cd packages/api
python3 -m py_compile services/report_service.py routers/reports.py

# Ver logs del backend
tail -100 /tmp/kidyland-backend.log | grep -E "error|Error|Exception"

# Ver logs del frontend
tail -100 /tmp/kidyland-frontend.log | grep -E "error|Error"
```

#### Limpiar Cache (si hay problemas)
```bash
cd apps/web
rm -rf .svelte-kit node_modules/.vite
pnpm dev  # Reiniciar servidor
```

---

## 📊 ESTADO ACTUAL DEL PROYECTO

### Admin Dashboard (`/admin`)
**Ubicación:** `apps/web/src/routes/admin/+page.svelte`

**Componente de Predicciones:**
- **Archivo:** `apps/web/src/lib/components/admin/PredictionsPanel.svelte`
- **Store:** `apps/web/src/lib/stores/metrics.ts`
- **Funciones clave:**
  - `updatePredictions()` - Actualiza predicciones en el store
  - `setPredictionInProgress()` - Controla estado de carga
  - `setPredictionError()` - Maneja errores

**Tipos de Predicciones en Dashboard:**
```typescript
interface PredictionsState {
  sales: PredictionData | null;           // Predicción de ventas
  capacity: PredictionData | null;         // Predicción de capacidad
  stock: PredictionData | null;            // Predicción de stock
  sales_by_type: PredictionData | null;   // Ventas por tipo
  peak_hours: PredictionData | null;       // Horas pico
  busiest_days: PredictionData | null;    // Días más ocupados
  generatedAt: number;                    // Timestamp de generación
  forecastDays: number;                    // Días de pronóstico
  predictionInProgress: boolean;          // Estado de carga
  error: string | null;                   // Errores
}
```

**Lógica de Predicciones:**
- El dashboard ya tiene un sistema funcional de predicciones
- **Endpoint usado:** `POST /reports/predictions/generate` (línea 520 en reports.py)
- **Servicio backend:** `PredictionService` en `packages/api/services/prediction_service.py`
- Genera predicciones basadas en datos históricos
- Muestra múltiples tipos de predicciones (ventas, capacidad, stock, etc.)
- Usa `forecastDays` para definir el horizonte de pronóstico (1-30 días, default: 7)
- Tiene validaciones de rate limiting (5 segundos entre predicciones, máximo 10 por sesión)
- Soporta predicciones "enhanced" con segmentación por módulo (Recepción, KidiBar)

### Admin Reports (`/admin/reports`)
**Ubicación:** `apps/web/src/routes/admin/reports/+page.svelte`

**Estado Actual:**
- ✅ **Ventas:** Completo con gráficos avanzados, métricas, análisis temporal
- ✅ **Inventario:** Completo con heatmap, movimiento, reorden, forecast, alertas
- ✅ **Servicios:** Completo con utilización, performance, capacidad, peak hours
- ✅ **Arqueos:** Completo con heatmap, tendencias, anomalías, comparaciones
- ✅ **Clientes:** Completo con RFM, cohortes, tendencias, paginación
- ⏳ **Forecasting:** Tab existente pero con placeholder básico
- ⏳ **Resumen Ejecutivo:** Tab existente pero con placeholder básico

**Tab Forecasting Actual:**
- Existe en `+page.svelte` (línea 729)
- Muestra datos básicos del store: `$reportsStore.forecast`
- Estructura básica con información del método, confianza, módulo
- Lista de días con predicciones de revenue y count
- **Problema:** No está completamente funcional, solo muestra datos si existen

**Estructura Actual del Forecast en Reports:**
```svelte
{:else if activeTab === "forecasting"}
  <div class="tab-panel">
    <h2 class="tab-title">Forecasting</h2>
    {#if $reportsStore.loading}
      <LoadingSpinner />
    {:else if $reportsStore.error}
      <ErrorBanner error={$reportsStore.error} />
    {:else if $reportsStore.forecast}
      <!-- Muestra información básica del forecast -->
      <!-- Lista de días con predicciones -->
    {:else}
      <p>No hay datos de forecasting disponibles...</p>
    {/if}
  </div>
```

---

## 🎯 OBJETIVO: IMPLEMENTAR SECCIÓN FORECASTING EN REPORTES

### Requisitos

1. **Reutilizar Lógica del Dashboard:**
   - La sección de Forecasting en reportes debe usar la **misma lógica** que el `PredictionsPanel` del dashboard
   - Aprovechar todos los datos disponibles de las secciones de reportes (Ventas, Inventario, Servicios, Arqueos, Clientes)
   - Mantener consistencia con el sistema de predicciones existente

2. **Funcionalidades Necesarias:**
   - **Múltiples tipos de predicciones:**
     - Predicción de ventas (usando datos de sección Ventas)
     - Predicción de capacidad (usando datos de sección Servicios)
     - Predicción de stock (usando datos de sección Inventario)
     - Predicción de arqueos (usando datos de sección Arqueos)
     - Predicción de comportamiento de clientes (usando datos de sección Clientes)
   
   - **Visualizaciones avanzadas:**
     - Gráficos de series temporales con proyecciones
     - Comparación histórico vs. predicción
     - Intervalos de confianza
     - Métricas de precisión del modelo
   
   - **Configuración:**
     - Selector de horizonte de pronóstico (días)
     - Selector de método de predicción (si hay múltiples)
     - Filtros por módulo (Recepción, KidiBar, Todos)
     - Filtros por sucursal
     - Filtros por rango de fechas (período histórico)

3. **Integración con Datos de Reportes:**
   - Aprovechar endpoints existentes:
     - `/reports/sales/timeseries` - Para predicción de ventas
     - `/reports/services/timeseries` - Para predicción de servicios
     - `/reports/inventory/timeseries` - Para predicción de inventario
     - `/reports/arqueos/timeseries` - Para predicción de arqueos
     - `/reports/customers/*` - Para predicción de comportamiento
   
   - Usar datos históricos de las secciones ya implementadas
   - Aplicar modelos de predicción sobre estos datos

4. **Arquitectura:**
   - **Backend:** 
     - **Opción A (Recomendada):** Reutilizar endpoints existentes:
       - `POST /reports/predictions/generate` - Ya existe, usado por dashboard
       - `POST /reports/predictions/generate/enhanced` - Ya existe, con segmentación por módulo
       - `GET /reports/arqueos/predictions` - Ya existe
       - `GET /reports/inventory/forecast` - Ya existe
       - Adaptar estos endpoints para aceptar filtros de reportes (fechas, sucursal, módulo)
     
     - **Opción B:** Crear nuevos endpoints específicos para reportes:
       - `/reports/forecasting/sales` - Predicción de ventas con filtros de reportes
       - `/reports/forecasting/capacity` - Predicción de capacidad con filtros
       - `/reports/forecasting/stock` - Predicción de stock con filtros
       - `/reports/forecasting/arqueos` - Predicción de arqueos con filtros
       - `/reports/forecasting/customers` - Predicción de clientes con filtros
       - `/reports/forecasting/all` - Todas las predicciones con filtros
   
   - **Frontend:** Crear componente `ForecastingSection.svelte`
     - Similar a `PredictionsPanel.svelte` pero adaptado para reportes
     - Integrar con filtros globales (sucursal, módulo, fechas) de `+page.svelte`
     - Visualizaciones avanzadas con Chart.js (reutilizar componentes de Ventas)
     - Comparación histórico vs. predicción
     - Gráficos de series temporales con proyecciones futuras

---

## 📝 PROMPT PARA EL PRÓXIMO CHAT

```
Analiza el estado actual del proyecto Kidyland y procede con la implementación de la sección Forecasting en Admin Reports.

CONTEXTO:
- Proyecto monorepo: Backend FastAPI (Python) en packages/api/, Frontend SvelteKit en apps/web/
- Admin Dashboard (/admin) ya tiene PredictionsPanel funcional con lógica de predicciones
- Admin Reports (/admin/reports) tiene secciones completas: Ventas, Inventario, Servicios, Arqueos, Clientes
- La sección Forecasting en reportes existe pero solo muestra placeholder básico

OBJETIVO:
Implementar la sección Forecasting en reportes que:
1. Reutilice la lógica similar/igual a PredictionsPanel del dashboard
2. Aproveche todos los datos disponibles de las secciones de reportes
3. Proporcione visualizaciones avanzadas con gráficos y comparaciones
4. Permita configuración de horizonte de pronóstico, método, y filtros

REQUISITOS TÉCNICOS:
- Mantener Clean Architecture
- Código modular, escalable, reutilizable
- Sin hardcoding, todo dinámico y responsivo
- Usar compilación, logs y tests para validación continua
- Implementar pieza por pieza sin romper funcionalidad existente

INVESTIGACIÓN REQUERIDA:
1. Analizar cómo funciona PredictionsPanel en el dashboard
2. Identificar qué endpoints y lógica usa
3. Determinar cómo adaptar esa lógica para reportes
4. Investigar patrones de forecasting avanzado 2025
5. Comparar con arquitectura existente
6. Evaluar compatibilidad y trade-offs
7. Seleccionar solución apropiada, future-proof, minimalista, robusta

NO GENERES CÓDIGO AÚN:
Solo proporciona un diagnóstico completo con:
- Análisis de PredictionsPanel actual
- Propuesta de arquitectura para Forecasting en reportes
- Plan de implementación por fases
- Comparación de opciones (reutilizar vs. crear nuevo)
- Recomendaciones técnicas

Criterios de evaluación:
- ✅ Mantiene Clean Architecture
- ✅ No rompe servicios existentes
- ✅ Escalable y mantenible
- ✅ Performance adecuado
- ✅ Validar funcionamiento en todo tipo de casos
```

---

## 🔍 ARCHIVOS CLAVE A REVISAR

### Frontend
- `apps/web/src/routes/admin/+page.svelte` - Dashboard principal con PredictionsPanel
- `apps/web/src/lib/components/admin/PredictionsPanel.svelte` - Componente de predicciones del dashboard
- `apps/web/src/lib/stores/metrics.ts` - Store con lógica de predicciones
- `apps/web/src/routes/admin/reports/+page.svelte` - Página de reportes (línea 729: sección forecasting)
- `apps/web/src/lib/stores/reports.ts` - Store de reportes

### Backend
- `packages/api/routers/reports.py` - Endpoints de reportes
  - **Línea 520:** `POST /reports/predictions/generate` - Genera predicciones (similar a dashboard)
  - **Línea 1640:** `POST /reports/predictions/generate/enhanced` - Predicciones mejoradas con segmentación por módulo
  - **Línea 1244:** `GET /reports/arqueos/predictions` - Predicciones de arqueos
  - **Línea 1519:** `GET /reports/inventory/forecast` - Forecast de inventario
- `packages/api/services/report_service.py` - Lógica de reportes
- `packages/api/services/prediction_service.py` - **Servicio de predicciones** (usado por dashboard)
  - `PredictionService` - Clase principal
  - `generate_all_predictions()` - Genera todas las predicciones
  - Métodos específicos para cada tipo de predicción

---

## 📌 NOTAS IMPORTANTES

1. **No usar git aún** - Todo está en local
2. **Validación continua** - Usar compilación, logs, tests
3. **Implementación incremental** - Pieza por pieza
4. **Reutilización** - Aprovechar código existente del dashboard
5. **Consistencia** - Mantener mismo estilo y patrones que otras secciones de reportes

---

## 🚀 PRÓXIMOS PASOS SUGERIDOS

1. Analizar `PredictionsPanel.svelte` y `metrics.ts` para entender lógica actual
2. Identificar qué endpoints del backend usa el dashboard para predicciones
3. Diseñar arquitectura para Forecasting en reportes
4. Proponer plan de implementación por fases
5. Implementar y validar

