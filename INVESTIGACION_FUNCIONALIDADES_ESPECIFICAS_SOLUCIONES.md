# 🔍 INVESTIGACIÓN Y SOLUCIONES - FUNCIONALIDADES ESPECÍFICAS

**Fecha:** 2025-01-XX  
**Objetivo:** Investigar estado actual y proponer soluciones para funcionalidades pendientes

---

## 📋 RESUMEN EJECUTIVO

| Funcionalidad | Estado Backend | Estado Frontend | Acción Requerida | Effort |
|---------------|----------------|-----------------|------------------|--------|
| **Alertas timer 5/10/15 min** | ✅ Completo | ⚠️ Parcial | Implementar notificaciones visuales | 4-6h |
| **Selector timer vs día** | ✅ Completo | ✅ Completo | Testing + validación | 2-3h |
| **Quantify servicios** | ✅ Completo | ✅ Completo | Testing + validación | 2-3h |
| **Timer delay 3 minutos** | ✅ Completo | ✅ Completo | Testing + validación | 2-3h |
| **Vista previa paneles** | ❌ Faltante | ❌ Faltante | Implementar completo | 12-16h |
| **Gestión sucursales UI** | ✅ Completo | ❌ Faltante | Implementar UI CRUD | 4-6h |
| **Selector sucursal dashboard** | ✅ Completo | ❌ Faltante | Implementar selector | 2-3h |

---

## 1. ⚠️ ALERTAS TIMER 5/10/15 MIN

### 📊 Estado Actual

**Backend:**
- ✅ Modelo `Service.alerts_config` (JSON) con `ServiceAlert` objects
- ✅ Background task `check_timer_alerts()` en `main.py` que verifica timers cada 5 segundos
- ✅ `TimerService.get_timers_ending_soon()` identifica timers con alertas
- ✅ WebSocket envía mensaje `timer_alert` cuando hay alertas
- ✅ Timer status cambia a `"alert"` cuando está en rango de alerta

**Frontend:**
- ✅ Store `timers.ts` recibe mensaje `timer_alert` del WebSocket
- ✅ Componentes de timers muestran status `"alert"` con estilo visual (borde amarillo)
- ❌ **NO hay notificaciones visuales/audibles** cuando se activa una alerta
- ❌ **NO se muestra qué alerta específica se activó** (5, 10, o 15 min)
- ❌ **NO hay sistema de notificaciones** (toasts, banners, sonidos)

### 🔍 Análisis Técnico

**Backend Flow:**
```python
# packages/api/main.py
async def check_timer_alerts():
    # Cada 5 segundos:
    # 1. Obtiene timers activos
    # 2. Para cada timer, verifica alerts_config del servicio
    # 3. Si time_left está en rango de alerta, cambia status a "alert"
    # 4. Envía mensaje WebSocket "timer_alert" con timers actualizados
```

**Frontend Flow Actual:**
```typescript
// apps/web/src/lib/stores/timers.ts
// Recibe mensaje "timer_alert" pero solo actualiza lista de timers
// No muestra notificación ni indica qué alerta específica
```

### ✅ Solución Propuesta

#### **Backend (Ya está completo, solo validar):**
- ✅ Verificar que `check_timer_alerts()` funciona correctamente
- ✅ Verificar que WebSocket envía `timer_alert` con información completa
- ⚠️ **MEJORA:** Incluir en mensaje WebSocket qué alerta específica se activó (5, 10, 15 min)

#### **Frontend (Implementar):**

1. **Sistema de Notificaciones (2-3h)**
   - Crear `NotificationStore` para manejar notificaciones globales
   - Crear componente `ToastNotification.svelte` para mostrar toasts
   - Integrar en `+layout.svelte` para mostrar notificaciones globales

2. **Mejora Timer Alerts (2-3h)**
   - Modificar `timers.ts` para detectar nuevas alertas y mostrar notificación
   - Mostrar qué alerta específica se activó (ej: "⚠️ Timer termina en 5 minutos")
   - Agregar sonido opcional (configurable)
   - Mejorar visualización en componentes de timers con badge de alerta

**Estructura Propuesta:**
```
apps/web/src/lib/
├── stores/
│   └── notifications.ts          # NUEVO: Store de notificaciones
└── components/
    └── shared/
        └── ToastNotification.svelte  # NUEVO: Componente toast
```

**Implementación:**
- `notifications.ts`: Store con array de notificaciones activas
- `ToastNotification.svelte`: Componente que muestra toasts con auto-dismiss
- Modificar `timers.ts`: Detectar cambios en alertas y emitir notificaciones
- Modificar `recepcion/timers/+page.svelte`: Mostrar badge con minutos restantes

**Testing:**
- Verificar que notificaciones aparecen cuando timer entra en rango de alerta
- Verificar que se muestra correctamente qué alerta (5/10/15 min)
- Verificar que sonido funciona (si se implementa)
- Verificar que notificaciones no se duplican

---

## 2. ✅ SELECTOR TIMER VS DÍA

### 📊 Estado Actual

**Backend:**
- ✅ Acepta `serviceType: "timer" | "day"` en creación de venta
- ✅ Crea timer solo si `serviceType === "timer"`
- ✅ Si `serviceType === "day"`, no crea timer

**Frontend:**
- ✅ Radio buttons en `ServiceSaleForm.svelte` (líneas 197-214)
- ✅ Valor por defecto: `"timer"`
- ✅ Se envía correctamente al backend

### 🔍 Análisis Técnico

**Implementación Actual:**
```svelte
<!-- ServiceSaleForm.svelte -->
<div class="radio-group">
  <label class="radio-label">
    <input type="radio" value="timer" bind:group={serviceType} />
    <span>⏱️ Timer</span>
  </label>
  <label class="radio-label">
    <input type="radio" value="day" bind:group={serviceType} />
    <span>📅 Por Día</span>
  </label>
</div>
```

**Backend Handling:**
```python
# packages/api/services/sale_service.py
# Crea timer solo si tipo es "service" (timer)
# Si tipo es "day", no crea timer
```

### ✅ Solución Propuesta

**Estado:** ✅ **IMPLEMENTADO CORRECTAMENTE**

**Acción Requerida:**
1. **Testing Manual (1-2h)**
   - Probar crear venta con "Timer" → Verificar que se crea timer
   - Probar crear venta con "Por Día" → Verificar que NO se crea timer
   - Verificar que UI muestra correctamente la selección

2. **Testing Automatizado (1h)**
   - Agregar test E2E para flujo completo
   - Verificar que backend recibe correctamente el tipo

**No requiere cambios de código**, solo validación y testing.

---

## 3. ✅ QUANTIFY SERVICIOS

### 📊 Estado Actual

**Backend:**
- ✅ Acepta `quantity` en creación de venta
- ✅ Calcula `subtotal_cents = unitPriceCents * quantity`
- ✅ Crea múltiples `SaleItem` si quantity > 1

**Frontend:**
- ✅ Controles +/- en `ServiceSelector.svelte` (líneas 109-135)
- ✅ Input numérico para cantidad
- ✅ Cálculo de precio total: `price * quantity`
- ✅ Se envía correctamente al backend

### 🔍 Análisis Técnico

**Implementación Actual:**
```svelte
<!-- ServiceSelector.svelte -->
<div class="quantity-controls">
  <button on:click={decrementQuantity}>−</button>
  <input type="number" bind:value={quantity} min="1" />
  <button on:click={incrementQuantity}>+</button>
</div>
```

**Cálculo de Precio:**
```typescript
// ServiceSelector.svelte
$: calculatedPrice = selectedService && selectedDuration
  ? Math.ceil(selectedDuration / Math.min(...selectedService.durations_allowed)) *
    selectedService.base_price_per_slot * quantity
  : 0;
```

### ✅ Solución Propuesta

**Estado:** ✅ **IMPLEMENTADO CORRECTAMENTE**

**Acción Requerida:**
1. **Testing Manual (1-2h)**
   - Probar con quantity = 1, 2, 5, 10
   - Verificar que precio se calcula correctamente
   - Verificar que backend recibe correctamente la cantidad
   - Verificar que se crean múltiples SaleItem si quantity > 1

2. **Testing Automatizado (1h)**
   - Agregar test E2E para flujo con diferentes cantidades
   - Verificar cálculo de precios

**No requiere cambios de código**, solo validación y testing.

---

## 4. ✅ TIMER DELAY 3 MINUTOS

### 📊 Estado Actual

**Backend:**
- ✅ Campo `start_delay_minutes` en modelo `Timer`
- ✅ Acepta `start_delay_minutes` en creación de timer
- ✅ Calcula `start_at = now + delay_minutes`

**Frontend:**
- ✅ Checkbox en `ServiceSaleForm.svelte` (línea 224)
- ✅ Se envía `startDelayMinutes: 3` si checkbox está marcado
- ✅ Label: "Iniciar timer 3 minutos después de imprimir ticket"

### 🔍 Análisis Técnico

**Implementación Actual:**
```svelte
<!-- ServiceSaleForm.svelte -->
<label class="checkbox-label">
  <input
    type="checkbox"
    bind:checked={startDelay3Minutes}
  />
  <span>Iniciar timer 3 minutos después de imprimir ticket</span>
</label>
```

**Backend Handling:**
```python
# packages/api/services/sale_service.py
# Calcula start_at = datetime.utcnow() + timedelta(minutes=start_delay_minutes)
```

### ✅ Solución Propuesta

**Estado:** ✅ **IMPLEMENTADO CORRECTAMENTE**

**Acción Requerida:**
1. **Testing Manual (1-2h)**
   - Probar crear venta CON delay → Verificar que timer inicia 3 min después
   - Probar crear venta SIN delay → Verificar que timer inicia inmediatamente
   - Verificar que `start_at` en timer es correcto

2. **Testing Automatizado (1h)**
   - Agregar test para verificar cálculo de `start_at`
   - Verificar que timer no está activo durante el delay

**No requiere cambios de código**, solo validación y testing.

---

## 5. ❌ VISTA PREVIA PANELES

### 📊 Estado Actual

**Backend:**
- ❌ No existe endpoint para preview
- ❌ No existe funcionalidad de preview

**Frontend:**
- ❌ No existe componente de preview
- ❌ No existe ruta para preview

### 🔍 Análisis Técnico

**Requisito:**
- Super admin debe poder ver cómo se ve cada panel para cada rol
- Preview debe ser en tiempo real (no screenshot estático)
- Debe mostrar exactamente lo que vería cada rol

### ✅ Solución Propuesta

#### **Backend (4-6h):**

1. **Endpoint Preview (2-3h)**
   ```python
   # packages/api/routers/admin.py
   @router.get("/admin/preview/{role}")
   async def preview_panel(role: str, ...):
       """
       Generate preview data for a specific role.
       Returns same data that role would see in their dashboard.
       """
       # Retornar datos simulados para el rol
       # No requiere autenticación real del rol
   ```

2. **Preview Service (2-3h)**
   ```python
   # packages/api/services/preview_service.py
   class PreviewService:
       async def get_preview_data(role: str, sucursal_id: str):
           # Generar datos de preview para el rol
           # Incluir: métricas, timers, ventas, etc.
   ```

#### **Frontend (8-10h):**

1. **Preview Modal Component (4-5h)**
   ```svelte
   <!-- apps/web/src/lib/components/admin/PreviewModal.svelte -->
   <!-- Modal que muestra preview de cada panel -->
   <!-- Usa iframe o componente renderizado -->
   ```

2. **Preview Store (2-3h)**
   ```typescript
   // apps/web/src/lib/stores/preview.ts
   // Store para manejar datos de preview
   ```

3. **Integración en User Management (2h)**
   - Agregar botón "Vista Previa" en `UserList.svelte`
   - Abrir modal con preview del panel del rol seleccionado

**Estructura Propuesta:**
```
packages/api/
├── routers/
│   └── admin.py              # Agregar endpoint /admin/preview/{role}
└── services/
    └── preview_service.py    # NUEVO: Lógica de preview

apps/web/src/
├── lib/
│   ├── stores/
│   │   └── preview.ts        # NUEVO: Store de preview
│   └── components/
│       └── admin/
│           └── PreviewModal.svelte  # NUEVO: Modal de preview
```

**Implementación Detallada:**

**Backend:**
- Endpoint `/admin/preview/{role}` que retorna datos simulados
- Datos incluyen: métricas, timers, ventas, productos, etc.
- No requiere autenticación del rol específico (solo super_admin)

**Frontend:**
- Modal que muestra preview usando componentes reales
- Renderiza dashboard del rol seleccionado con datos simulados
- Permite navegar entre diferentes vistas del rol

**Testing:**
- Verificar que preview muestra correctamente cada rol
- Verificar que datos simulados son realistas
- Verificar que preview no afecta datos reales

---

## 6. ❌ GESTIÓN SUCURSALES UI

### 📊 Estado Actual

**Backend:**
- ✅ Endpoint `GET /sucursales` - Listar sucursales
- ✅ Endpoint `POST /sucursales` - Crear sucursal
- ✅ Modelo `Sucursal` completo
- ✅ Schemas `SucursalCreate`, `SucursalRead`
- ❌ **Faltan:** `PUT /sucursales/{id}` y `DELETE /sucursales/{id}`

**Frontend:**
- ❌ No existe ruta `/admin/sucursales`
- ❌ No existe componente `SucursalList.svelte`
- ❌ No existe componente `SucursalForm.svelte`

### 🔍 Análisis Técnico

**Backend Endpoints Existentes:**
```python
# packages/api/routers/catalog.py
@router.get("/sucursales")      # ✅ Existe
@router.post("/sucursales")     # ✅ Existe
# ❌ Faltan PUT y DELETE
```

**Modelo Sucursal:**
```python
# packages/api/models/sucursal.py
class Sucursal:
    id: UUID
    name: str
    address: str | None
    timezone: str (default: "America/Mexico_City")
    active: bool
    created_at: datetime
    updated_at: datetime
```

### ✅ Solución Propuesta

#### **Backend (1-2h):**

1. **Agregar Endpoints CRUD Completos**
   ```python
   # packages/api/routers/catalog.py
   @router.put("/sucursales/{sucursal_id}")      # NUEVO
   @router.delete("/sucursales/{sucursal_id}")   # NUEVO
   ```

2. **Agregar Schema Update**
   ```python
   # packages/api/schemas/sucursal.py
   class SucursalUpdate(BaseModel):  # NUEVO
       name: Optional[str] = None
       address: Optional[str] = None
       timezone: Optional[str] = None
       active: Optional[bool] = None
   ```

#### **Frontend (3-4h):**

1. **Store de Sucursales (1h)**
   ```typescript
   // apps/web/src/lib/stores/sucursales-admin.ts
   // Similar a services-admin.ts y products-admin.ts
   ```

2. **Componente SucursalList (1h)**
   ```svelte
   <!-- apps/web/src/lib/components/admin/SucursalList.svelte -->
   <!-- Similar a ServiceList.svelte -->
   ```

3. **Componente SucursalForm (1h)**
   ```svelte
   <!-- apps/web/src/lib/components/admin/SucursalForm.svelte -->
   <!-- Similar a ServiceForm.svelte -->
   ```

4. **Ruta Admin (30min)**
   ```svelte
   <!-- apps/web/src/routes/admin/sucursales/+page.svelte -->
   ```

5. **Agregar a Navegación (30min)**
   - Agregar `/admin/sucursales` a `adminNavItems` en `+layout.svelte`

**Estructura Propuesta:**
```
packages/api/
├── routers/
│   └── catalog.py              # Agregar PUT/DELETE /sucursales
└── schemas/
    └── sucursal.py             # Agregar SucursalUpdate

apps/web/src/
├── lib/
│   ├── stores/
│   │   └── sucursales-admin.ts # NUEVO: Store de sucursales
│   └── components/
│       └── admin/
│           ├── SucursalList.svelte  # NUEVO
│           └── SucursalForm.svelte # NUEVO
└── routes/
    └── admin/
        └── sucursales/
            └── +page.svelte   # NUEVO
```

**Testing:**
- Verificar CRUD completo funciona
- Verificar validaciones (nombre requerido, timezone válido)
- Verificar que solo super_admin puede crear/editar/eliminar

---

## 7. ❌ SELECTOR SUCURSAL EN DASHBOARD

### 📊 Estado Actual

**Backend:**
- ✅ Endpoints aceptan `sucursal_id` como query param
- ✅ Si no se proporciona, usa `current_user.sucursal_id`
- ✅ Endpoint `GET /sucursales` para listar todas

**Frontend:**
- ❌ Dashboard admin NO tiene selector de sucursal
- ❌ Siempre muestra métricas de la sucursal del usuario actual
- ❌ No permite filtrar por otra sucursal

### 🔍 Análisis Técnico

**Dashboard Actual:**
```svelte
<!-- apps/web/src/routes/admin/+page.svelte -->
<!-- RefreshButton usa $user?.sucursal_id -->
<!-- No hay selector para cambiar sucursal -->
```

**Backend Endpoints:**
```python
# Todos los endpoints de reports aceptan sucursal_id opcional
# Si no se proporciona, usa current_user.sucursal_id
```

### ✅ Solución Propuesta

#### **Frontend (2-3h):**

1. **Store de Sucursales (30min)**
   - Reutilizar o crear store simple para listar sucursales
   - Solo necesita `GET /sucursales`

2. **Selector Component (1h)**
   ```svelte
   <!-- apps/web/src/lib/components/admin/SucursalSelector.svelte -->
   <!-- Dropdown para seleccionar sucursal -->
   <!-- Similar a otros selectores -->
   ```

3. **Integración en Dashboard (1h)**
   - Agregar `SucursalSelector` en header del dashboard
   - Actualizar `RefreshButton` para usar sucursal seleccionada
   - Actualizar `metricsStore` para usar sucursal seleccionada

**Estructura Propuesta:**
```
apps/web/src/
├── lib/
│   ├── stores/
│   │   └── sucursales.ts      # NUEVO: Store simple para listar
│   └── components/
│       └── admin/
│           └── SucursalSelector.svelte  # NUEVO: Selector dropdown
└── routes/
    └── admin/
        └── +page.svelte        # Modificar: Agregar selector
```

**Implementación:**
- Selector muestra todas las sucursales (solo super_admin)
- Al seleccionar, actualiza métricas para esa sucursal
- Guarda selección en localStorage para persistencia
- Por defecto, usa sucursal del usuario actual

**Testing:**
- Verificar que selector muestra todas las sucursales
- Verificar que métricas se actualizan al cambiar sucursal
- Verificar que solo super_admin ve el selector

---

## 📊 RESUMEN DE SOLUCIONES

### ✅ **Solo Requieren Testing (No código nuevo):**
1. **Selector timer vs día** - 2-3h testing
2. **Quantify servicios** - 2-3h testing
3. **Timer delay 3 minutos** - 2-3h testing

### ⚠️ **Requieren Implementación Parcial:**
1. **Alertas timer 5/10/15 min** - 4-6h (sistema notificaciones)

### ❌ **Requieren Implementación Completa:**
1. **Vista previa paneles** - 12-16h (backend + frontend)
2. **Gestión sucursales UI** - 4-6h (backend PUT/DELETE + frontend CRUD)
3. **Selector sucursal dashboard** - 2-3h (frontend selector)

---

## 🎯 PRIORIZACIÓN RECOMENDADA

### **FASE 1: Testing de Funcionalidades Existentes (1 día)**
- Testing selector timer vs día
- Testing quantify servicios
- Testing timer delay 3 minutos
- **Resultado:** Validar que funcionalidades implementadas funcionan correctamente

### **FASE 2: Alertas Timer (1 día)**
- Implementar sistema de notificaciones
- Mejorar visualización de alertas
- **Resultado:** Alertas funcionan completamente

### **FASE 3: Sucursales (1 día)**
- Backend: PUT/DELETE endpoints
- Frontend: CRUD completo + selector en dashboard
- **Resultado:** Gestión completa de sucursales

### **FASE 4: Vista Previa Paneles (2 días)**
- Backend: Preview service + endpoints
- Frontend: Preview modal + integración
- **Resultado:** Super admin puede previsualizar paneles

---

## ⏱️ ESTIMACIÓN TOTAL

| Fase | Tiempo | Prioridad |
|------|--------|-----------|
| FASE 1: Testing | 1 día | 🚨 CRÍTICO |
| FASE 2: Alertas | 1 día | 🟡 IMPORTANTE |
| FASE 3: Sucursales | 1 día | 🟡 IMPORTANTE |
| FASE 4: Preview | 2 días | 🟢 ENHANCEMENT |
| **TOTAL** | **5 días** | |

---

## ✅ CONCLUSIÓN

**Estado General:**
- ✅ 3 funcionalidades están **completamente implementadas** (solo necesitan testing)
- ⚠️ 1 funcionalidad está **parcialmente implementada** (alertas timer)
- ❌ 3 funcionalidades están **completamente faltantes** (preview, sucursales UI, selector)

**Recomendación:**
1. Empezar con **FASE 1** (testing) para validar lo existente
2. Continuar con **FASE 2** (alertas) para completar funcionalidad parcial
3. Implementar **FASE 3** (sucursales) para funcionalidad crítica
4. Dejar **FASE 4** (preview) para después (es enhancement)

**Tiempo total estimado:** 5 días de trabajo para completar todas las funcionalidades.





























