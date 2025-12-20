# 🗺️ ROADMAP ESTRATÉGICO - TESTING KIDYLAND

**Fecha:** 2025-01-XX  
**Estado Actual:** 125/125 tests backend pasando (Auth, Catalog, Operations completos)  
**Objetivo:** Sistema 100% validado con Clean Architecture

---

## 📊 ANÁLISIS DE ESTADO ACTUAL

### ✅ BACKEND - COMPLETADO (125 tests)
- **Auth Router:** 30/30 tests ✅ (100%)
- **Catalog Router:** 53/53 tests ✅ (100%)
- **Operations Router:** 42/42 tests ✅ (100%)

### ⚠️ BACKEND - PENDIENTE
- **Sales Router:** Tests básicos existentes, faltan edge cases
- **Timers Router:** Tests básicos existentes, falta WebSocket testing
- **Reports Router:** Tests básicos existentes, faltan gaps
- **Users Router:** Tests en `routers/test_users_endpoints.py`, validar completitud
- **Exports Router:** Sin tests

### ⚠️ FRONTEND - CRÍTICO (5% coverage estimado)
- **Stores críticos:** 16+ stores sin tests
  - `apps/web/src/lib/stores/`: auth.ts, sales.ts, timers.ts, metrics.ts, day-operations.ts
  - `apps/reception/src/lib/stores/`: services.ts, sales.ts
  - `apps/kidibar/src/lib/stores/`: products.ts, sales.ts
  - `apps/admin/src/lib/stores/`: users.ts, metrics.ts
- **Components críticos:** Sin tests
  - ServiceSaleForm, ProductSaleForm, TimerCard, etc.
- **Packages:** Tests básicos en `packages/ui` y `packages/utils`

### ⚠️ E2E - SIN TESTS
- Flujos críticos sin validar end-to-end

---

## 🎯 PATRONES ESTABLECIDOS (MANTENER)

### Backend Testing Pattern
```python
# Estructura de tests
tests/integration/test_{router}_endpoints.py
├─ Helper fixtures (setup_dependencies, get_auth_token)
├─ Test classes por endpoint group
│  ├─ Test{EndpointGroup}Endpoints
│  │  ├─ Tests por rol (5 roles)
│  │  ├─ Tests de validaciones
│  │  └─ Tests de edge cases
└─ Clean Architecture preservada
```

### Frontend Testing Pattern (a establecer)
```typescript
// Estructura de tests stores
tests/stores/{store_name}.test.ts
├─ Setup con mocks
├─ Tests de estado inicial
├─ Tests de acciones
├─ Tests de efectos
└─ Tests de edge cases
```

### Principios
- ✅ Clean Architecture
- ✅ Código modular y escalable
- ✅ Sin hardcoding
- ✅ Dinámico y responsivo
- ✅ Fixtures reutilizables
- ✅ Helpers centralizados

---

## 🚀 ROADMAP PRIORIZADO

### **FASE 1: COMPLETAR BACKEND TESTING** ⭐ (4-6h)
**Objetivo:** Backend 90%+ coverage completo

#### 1.1 Sales Router - Edge Cases (1-2h)
**Prioridad:** ALTA (funcionalidad core del negocio)

**Tests a implementar:**
- ✅ POST `/sales/{id}/extend` - Extender timer
- ✅ POST `/sales/{id}/print` - Imprimir ticket
- ✅ Validaciones de items (service vs product)
- ✅ Cálculo de totales (subtotal, discount, total)
- ✅ Permisos por rol (recepcion, kidibar)

**Archivo:** `tests/integration/test_sales_endpoints.py` (expandir existente)

**Patrón:** Mismo que Operations Router (TestSalesEndpoints, TestSalesExtendEndpoints, etc.)

---

#### 1.2 Timers Router - WebSocket Testing (1-2h)
**Prioridad:** ALTA (funcionalidad real-time crítica)

**Tests a implementar:**
- ✅ WebSocket connection establecida
- ✅ Timer updates en tiempo real
- ✅ Reconnection logic
- ✅ Multi-client support
- ✅ Permisos WebSocket

**Archivo:** `tests/integration/test_timers_endpoints.py` (expandir) + `test_websocket.py` (mejorar)

**Patrón:** Usar `websocket_mocks.py` existente, seguir patrón de tests async

---

#### 1.3 Reports Router - Gaps (1h)
**Prioridad:** MEDIA (analytics, no bloqueante)

**Tests a implementar:**
- ✅ Validar todos los endpoints de reports
- ✅ Cache invalidation
- ✅ Prediction endpoints
- ✅ Permisos (super_admin, admin_viewer)

**Archivo:** `tests/integration/test_reports_endpoints.py` (expandir existente)

**Patrón:** Mismo que otros routers

---

#### 1.4 Users Router - Validación (30min)
**Prioridad:** MEDIA (ya tiene tests, validar completitud)

**Acción:**
- ✅ Revisar `tests/integration/routers/test_users_endpoints.py`
- ✅ Validar que todos los endpoints están cubiertos
- ✅ Agregar tests faltantes si es necesario

---

#### 1.5 Exports Router - Implementación (1h)
**Prioridad:** BAJA (feature pendiente, no crítico)

**Tests a implementar:**
- ✅ GET `/exports/excel` - Excel export
- ✅ GET `/exports/pdf` - PDF export
- ✅ Validaciones de parámetros
- ✅ Permisos

**Archivo:** `tests/integration/test_exports_endpoints.py` (nuevo)

**Nota:** Si exports no está implementado, documentar como pendiente

---

### **FASE 2: FRONTEND TESTING CRÍTICO** ⭐⭐ (6-8h)
**Objetivo:** Frontend 40%+ coverage, funcionalidad core validada

#### 2.1 Stores Críticos - Web App (3-4h)
**Prioridad:** ALTA (app principal)

**Stores a testear:**
1. **auth.ts** (2h)
   - Login/logout
   - Token management
   - User state
   - Role checks

2. **sales.ts** (1h)
   - Create sale
   - Sale state management
   - Items handling

3. **timers.ts** (1h)
   - Timer state
   - WebSocket integration
   - Real-time updates

4. **metrics.ts** (30min)
   - Metrics loading
   - Cache handling

**Archivos:** `apps/web/tests/stores/{store_name}.test.ts` (nuevos)

**Patrón:** Vitest + Svelte stores testing

---

#### 2.2 Stores Críticos - Reception App (1-2h)
**Prioridad:** ALTA (operaciones diarias)

**Stores a testear:**
1. **services.ts** (1h)
   - Service list
   - Service selection

2. **sales.ts** (1h)
   - Sale creation
   - Day operations integration

**Archivos:** `apps/reception/tests/stores/{store_name}.test.ts` (nuevos)

---

#### 2.3 Stores Críticos - Kidibar App (1h)
**Prioridad:** MEDIA (venta de productos)

**Stores a testear:**
1. **products.ts** (30min)
2. **sales.ts** (30min)

**Archivos:** `apps/kidibar/tests/stores/{store_name}.test.ts` (nuevos)

---

#### 2.4 Components Críticos (2h)
**Prioridad:** ALTA (UI core)

**Components a testear:**
1. **ServiceSaleForm** (30min)
   - Form validation
   - Service selection
   - Submit handling

2. **ProductSaleForm** (30min)
   - Product selection
   - Quantity handling

3. **TimerCard** (30min)
   - Timer display
   - Time calculations
   - Status updates

4. **DayOperationsPanel** (30min)
   - Day start/close
   - Status display

**Archivos:** `apps/web/tests/components/{component_name}.test.ts` (nuevos)

**Patrón:** Vitest + @testing-library/svelte

---

### **FASE 3: E2E TESTING** (8-10h)
**Objetivo:** User journeys 100% validados

#### 3.1 Critical Paths (4-5h)
**Prioridad:** ALTA

**Flujos a testear:**
1. **Login → Dashboard → Crear venta → Timer → Cerrar día** (2h)
2. **Admin CRUD → Recepción usar → Monitor ver** (2h)
3. **Cross-role permissions validation** (1h)

**Archivos:** `tests/e2e/{flow_name}.spec.ts` (nuevos)

**Patrón:** Playwright + fixtures reutilizables

---

#### 3.2 Edge Cases E2E (3-4h)
**Prioridad:** MEDIA

**Flujos a testear:**
- WebSocket disconnection/reconnection
- Token expiration handling
- Multi-sucursal operations
- Concurrent operations

---

### **FASE 4: EXPORT FEATURES** (16-20h)
**Prioridad:** BAJA (features pendientes)

**Nota:** Esta fase es para implementación de features, no testing. Si se implementan, agregar tests en FASE 1.5.

---

## 📋 ORDEN DE EJECUCIÓN RECOMENDADO

### **OPCIÓN A: COMPLETAR BACKEND PRIMERO** ⭐ (Recomendado)
**Razón:** Momentum perfecto, patrón establecido, base sólida

1. FASE 1.1 - Sales Router Edge Cases (1-2h)
2. FASE 1.2 - Timers Router WebSocket (1-2h)
3. FASE 1.3 - Reports Router Gaps (1h)
4. FASE 1.4 - Users Router Validación (30min)
5. FASE 1.5 - Exports Router (1h) o documentar pendiente

**Resultado:** Backend 90%+ coverage completo

**Luego:** FASE 2 (Frontend Testing)

---

### **OPCIÓN B: FRONTEND TESTING AHORA** ⭐⭐
**Razón:** Balance, UX crítico, riesgo alto (5% coverage)

1. FASE 2.1 - Stores Web App (3-4h)
2. FASE 2.2 - Stores Reception App (1-2h)
3. FASE 2.3 - Stores Kidibar App (1h)
4. FASE 2.4 - Components Críticos (2h)

**Resultado:** Frontend 40%+ coverage

**Luego:** FASE 1 (Completar Backend) o FASE 3 (E2E)

---

## 🎯 RECOMENDACIÓN FINAL

### **OPCIÓN A: COMPLETAR BACKEND PRIMERO** ⭐

**Ventajas:**
- ✅ Momentum perfecto (125 tests pasando)
- ✅ Patrón establecido y funcionando
- ✅ Base sólida antes de frontend
- ✅ Menos riesgo de regresiones
- ✅ Tiempo estimado menor (4-6h vs 6-8h)

**Desventajas:**
- ⚠️ Frontend sigue con bajo coverage

**Justificación:**
- Backend es la base de todo
- Frontend depende de backend estable
- Patrón backend está maduro y probado
- Completar backend da confianza total

---

## 📝 NOTAS IMPORTANTES

### Mantener Patrones
- ✅ Mismo patrón de tests que Catalog/Operations/Auth
- ✅ Fixtures reutilizables (`factories`, `jwt_helpers`)
- ✅ `setup_dependencies` con `autouse=True`
- ✅ `get_auth_token()` helper centralizado
- ✅ `ASGITransport` para todos los tests

### Clean Architecture
- ✅ No romper lógica existente
- ✅ No romper arquitectura
- ✅ Código modular y escalable
- ✅ Sin hardcoding
- ✅ Dinámico y responsivo

### Calidad
- ✅ Coverage 90%+ backend
- ✅ Coverage 40%+ frontend
- ✅ Todos los tests pasando
- ✅ Sin regresiones

---

## 🚀 SIGUIENTE PASO

**¿Procedemos con FASE 1.1 (Sales Router Edge Cases)?**

Esto completará el backend testing siguiendo el mismo patrón exitoso que hemos establecido.





























