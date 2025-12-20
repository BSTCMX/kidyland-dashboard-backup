# 🔍 ANÁLISIS DETALLADO - GAPS CRÍTICOS DE TESTING

**Fecha:** 2025-01-XX  
**Objetivo:** Mapeo exhaustivo de endpoints, lógica de negocio y tests faltantes

---

## 📋 CATALOG ROUTER - ANÁLISIS COMPLETO

### Endpoints Identificados (16 endpoints, 0% coverage)

#### SUCURSALES (4 endpoints)

**1. GET `/sucursales`**
- **Permisos:** `super_admin`, `admin_viewer`
- **Lógica:** Lista todas las sucursales
- **Tests Faltantes:**
  - ✅ Listar sucursales (super_admin)
  - ✅ Listar sucursales (admin_viewer)
  - ❌ Denegar acceso (recepcion, kidibar, monitor)
  - ❌ Lista vacía cuando no hay sucursales
  - ❌ Filtrado por active/inactive (si aplica)

**2. POST `/sucursales`**
- **Permisos:** `super_admin` únicamente
- **Lógica:** Crea nueva sucursal
- **Validaciones:** Schema `SucursalCreate`
- **Tests Faltantes:**
  - ✅ Crear sucursal (super_admin)
  - ❌ Denegar acceso (admin_viewer, recepcion, etc.)
  - ❌ Validación campos requeridos (name, address)
  - ❌ Validación timezone válido
  - ❌ Validación UUID format
  - ❌ Duplicados (si aplica)

**3. PUT `/sucursales/{sucursal_id}`**
- **Permisos:** `super_admin` únicamente
- **Lógica:** Actualiza sucursal existente (partial update)
- **Validaciones:** Schema `SucursalUpdate`, 404 si no existe
- **Tests Faltantes:**
  - ✅ Actualizar sucursal (super_admin)
  - ❌ 404 cuando sucursal no existe
  - ❌ Denegar acceso (otros roles)
  - ❌ Partial update (solo algunos campos)
  - ❌ Validación campos inválidos

**4. DELETE `/sucursales/{sucursal_id}`**
- **Permisos:** `super_admin` únicamente
- **Lógica:** Soft delete (set `active=False`)
- **Validaciones:** 404 si no existe
- **Tests Faltantes:**
  - ✅ Soft delete (super_admin)
  - ❌ 404 cuando sucursal no existe
  - ❌ Denegar acceso (otros roles)
  - ❌ Verificar que active=False después de delete
  - ❌ No eliminar físicamente (soft delete)

---

#### PRODUCTS (4 endpoints)

**5. GET `/products`**
- **Permisos:** `super_admin`, `admin_viewer`, `kidibar`
- **Lógica:** Lista productos, filtro opcional por `sucursal_id`
- **Tests Faltantes:**
  - ✅ Listar productos (super_admin)
  - ✅ Listar productos (admin_viewer)
  - ✅ Listar productos (kidibar)
  - ❌ Denegar acceso (recepcion, monitor)
  - ❌ Filtro por sucursal_id
  - ❌ Lista vacía cuando no hay productos
  - ❌ Solo productos activos (si aplica)

**6. POST `/products`**
- **Permisos:** `super_admin` únicamente
- **Lógica:** Crea nuevo producto
- **Validaciones:** Schema `ProductCreate`
- **Tests Faltantes:**
  - ✅ Crear producto (super_admin)
  - ❌ Denegar acceso (otros roles)
  - ❌ Validación campos requeridos
  - ❌ Validación price_cents > 0
  - ❌ Validación stock_qty >= 0
  - ❌ Validación threshold_alert_qty >= 0
  - ❌ Validación sucursal_id existe

**7. PUT `/products/{product_id}`**
- **Permisos:** `super_admin` únicamente
- **Lógica:** Actualiza producto (partial update)
- **Validaciones:** 404 si no existe
- **Tests Faltantes:**
  - ✅ Actualizar producto (super_admin)
  - ❌ 404 cuando producto no existe
  - ❌ Denegar acceso (otros roles)
  - ❌ Partial update (solo algunos campos)
  - ❌ Actualizar stock_qty
  - ❌ Validación campos inválidos

**8. DELETE `/products/{product_id}`**
- **Permisos:** `super_admin` únicamente
- **Lógica:** Soft delete (set `active=False`)
- **Validaciones:** 404 si no existe
- **Tests Faltantes:**
  - ✅ Soft delete (super_admin)
  - ❌ 404 cuando producto no existe
  - ❌ Denegar acceso (otros roles)
  - ❌ Verificar que active=False
  - ❌ No eliminar físicamente

---

#### SERVICES (4 endpoints)

**9. GET `/services`**
- **Permisos:** `super_admin`, `admin_viewer`, `recepcion`
- **Lógica:** Lista servicios, filtro opcional por `sucursal_id`
- **Tests Faltantes:**
  - ✅ Listar servicios (super_admin)
  - ✅ Listar servicios (admin_viewer)
  - ✅ Listar servicios (recepcion)
  - ❌ Denegar acceso (kidibar, monitor)
  - ❌ Filtro por sucursal_id
  - ❌ Lista vacía cuando no hay servicios
  - ❌ Solo servicios activos (si aplica)

**10. POST `/services`**
- **Permisos:** `super_admin` únicamente
- **Lógica:** Crea nuevo servicio
- **Validaciones:** Schema `ServiceCreate`
- **Tests Faltantes:**
  - ✅ Crear servicio (super_admin)
  - ❌ Denegar acceso (otros roles)
  - ❌ Validación campos requeridos
  - ❌ Validación base_price_per_slot > 0
  - ❌ Validación durations_allowed no vacío
  - ❌ Validación alerts_config formato correcto
  - ❌ Validación sucursal_id existe

**11. PUT `/services/{service_id}`**
- **Permisos:** `super_admin` únicamente
- **Lógica:** Actualiza servicio (partial update)
- **Validaciones:** 404 si no existe
- **Tests Faltantes:**
  - ✅ Actualizar servicio (super_admin)
  - ❌ 404 cuando servicio no existe
  - ❌ Denegar acceso (otros roles)
  - ❌ Partial update
  - ❌ Actualizar alerts_config
  - ❌ Validación campos inválidos

**12. DELETE `/services/{service_id}`**
- **Permisos:** `super_admin` únicamente
- **Lógica:** Soft delete (set `active=False`)
- **Validaciones:** 404 si no existe
- **Business Rule:** ⚠️ **CRÍTICO** - No debería permitir borrar si tiene ventas activas
- **Tests Faltantes:**
  - ✅ Soft delete (super_admin)
  - ❌ 404 cuando servicio no existe
  - ❌ Denegar acceso (otros roles)
  - ❌ **Verificar que active=False**
  - ❌ **Validar que no tiene ventas activas** (business rule)
  - ❌ **Validar que no tiene timers activos** (business rule)

---

#### PACKAGES (4 endpoints)

**13. GET `/packages`**
- **Permisos:** `super_admin`, `admin_viewer`, `recepcion`
- **Lógica:** Lista paquetes, filtro opcional por `sucursal_id`, **solo activos** (`active=True`)
- **Tests Faltantes:**
  - ✅ Listar paquetes (super_admin)
  - ✅ Listar paquetes (admin_viewer)
  - ✅ Listar paquetes (recepcion)
  - ❌ Denegar acceso (kidibar, monitor)
  - ❌ Filtro por sucursal_id
  - ❌ **Solo paquetes activos** (filtro automático)
  - ❌ Lista vacía cuando no hay paquetes

**14. POST `/packages`**
- **Permisos:** `super_admin` únicamente
- **Lógica:** Crea nuevo paquete
- **Validaciones:** Schema `PackageCreate`
- **Tests Faltantes:**
  - ✅ Crear paquete (super_admin)
  - ❌ Denegar acceso (otros roles)
  - ❌ Validación campos requeridos
  - ❌ Validación price_cents > 0
  - ❌ Validación items formato correcto
  - ❌ Validación sucursal_id existe

**15. PUT `/packages/{package_id}`**
- **Permisos:** `super_admin` únicamente
- **Lógica:** Actualiza paquete (partial update)
- **Validaciones:** 404 si no existe
- **Tests Faltantes:**
  - ✅ Actualizar paquete (super_admin)
  - ❌ 404 cuando paquete no existe
  - ❌ Denegar acceso (otros roles)
  - ❌ Partial update
  - ❌ Actualizar items
  - ❌ Validación campos inválidos

**16. DELETE `/packages/{package_id}`**
- **Permisos:** `super_admin` únicamente
- **Lógica:** Soft delete (set `active=False`)
- **Validaciones:** 404 si no existe
- **Tests Faltantes:**
  - ✅ Soft delete (super_admin)
  - ❌ 404 cuando paquete no existe
  - ❌ Denegar acceso (otros roles)
  - ❌ Verificar que active=False
  - ❌ No eliminar físicamente

---

### 📊 RESUMEN CATALOG ROUTER

**Total Endpoints:** 16  
**Tests Necesarios Estimados:** ~80-100 tests  
**Complejidad:** Media-Alta (permisos múltiples, validaciones, business rules)

**Gaps Críticos:**
1. ❌ **0% coverage** - Ningún endpoint testado
2. ❌ **Business rules no validadas** (ej: no borrar servicio con ventas)
3. ❌ **Permisos cross-role** no testados
4. ❌ **Validaciones de schema** no testadas
5. ❌ **Edge cases** (listas vacías, 404s, soft deletes)

---

## 📋 OPERATIONS ROUTER - ANÁLISIS COMPLETO

### Endpoints Identificados (5 endpoints, 0% coverage)

#### DAY OPERATIONS (4 endpoints)

**1. POST `/day/start`**
- **Permisos:** `recepcion` únicamente
- **Lógica:** Inicia día para sucursal
- **Business Rules:**
  - ✅ Valida que no haya día activo (llama `DayStartService.get_active_day()`)
  - ✅ Usa `current_user.sucursal_id` si no se proporciona
  - ✅ Crea `DayStart` con `is_active=True`
  - ✅ Lanza `ValueError` si día ya está activo
- **Validaciones:**
  - `sucursal_id` requerido (o usar user.sucursal_id)
  - `initial_cash_cents` requerido
- **Tests Faltantes:**
  - ✅ Iniciar día (recepcion)
  - ❌ Denegar acceso (super_admin, admin_viewer, kidibar, monitor)
  - ❌ **Validar que no hay día activo** (business rule)
  - ❌ **Error cuando día ya está activo** (ValueError → 400)
  - ❌ Usar sucursal_id del usuario si no se proporciona
  - ❌ Error cuando usuario no tiene sucursal_id
  - ❌ Validación initial_cash_cents > 0
  - ❌ Crear DayStart con is_active=True
  - ❌ Timestamp started_at se guarda correctamente

**2. GET `/day/status`**
- **Permisos:** `recepcion` únicamente
- **Lógica:** Obtiene estado del día (abierto/cerrado)
- **Business Rules:**
  - ✅ Llama `DayStartService.get_day_status()`
  - ✅ Retorna `is_open`, `day_start` (si existe), `current_date`
  - ✅ Usa `current_user.sucursal_id` si no se proporciona
- **Tests Faltantes:**
  - ✅ Obtener estado día abierto (recepcion)
  - ✅ Obtener estado día cerrado (recepcion)
  - ❌ Denegar acceso (otros roles)
  - ❌ Usar sucursal_id del usuario si no se proporciona
  - ❌ Error cuando usuario no tiene sucursal_id
  - ❌ is_open=True cuando hay día activo
  - ❌ is_open=False cuando no hay día activo
  - ❌ day_start=None cuando no hay día activo
  - ❌ day_start con datos cuando hay día activo

**3. POST `/day/close`**
- **Permisos:** `recepcion` únicamente
- **Lógica:** Cierra día, calcula totales, reconcilia
- **Business Rules:**
  - ✅ Calcula `system_total_cents` desde ventas del día
  - ✅ Calcula `difference_cents = physical_count_cents - system_total_cents`
  - ✅ Crea `DayClose` con totals JSON
  - ✅ Cierra día activo (llama `DayStartService.close_active_day()`)
  - ✅ Calcula sale_count, system_cash_cents
- **Validaciones:**
  - `sucursal_id` requerido
  - `date` requerido
  - `physical_count_cents` requerido
- **Tests Faltantes:**
  - ✅ Cerrar día (recepcion)
  - ❌ Denegar acceso (otros roles)
  - ❌ **Calcular system_total_cents desde ventas**
  - ❌ **Calcular difference_cents correctamente**
  - ❌ **Cerrar día activo** (is_active=False)
  - ❌ Cerrar día sin ventas (system_total=0)
  - ❌ Cerrar día con múltiples ventas
  - ❌ Totals JSON contiene sale_count, system_cash_cents
  - ❌ Validación campos requeridos
  - ❌ Error cuando no hay día activo (si aplica)

**4. GET `/day/close/history`**
- **Permisos:** `recepcion` únicamente
- **Lógica:** Historial de cierres de día
- **Business Rules:**
  - ✅ Filtro por `sucursal_id` (usa user.sucursal_id si no se proporciona)
  - ✅ Filtro opcional por `start_date` y `end_date`
  - ✅ Ordenado por fecha descendente (más reciente primero)
- **Tests Faltantes:**
  - ✅ Obtener historial (recepcion)
  - ❌ Denegar acceso (otros roles)
  - ❌ Filtro por sucursal_id
  - ❌ Filtro por start_date
  - ❌ Filtro por end_date
  - ❌ Filtro combinado (start_date + end_date)
  - ❌ Orden descendente por fecha
  - ❌ Lista vacía cuando no hay cierres
  - ❌ Usar sucursal_id del usuario si no se proporciona

#### STOCK ALERTS (1 endpoint)

**5. GET `/stock/alerts`**
- **Permisos:** `super_admin`, `admin_viewer`, `recepcion`
- **Lógica:** Productos con stock bajo (≤ threshold)
- **Business Rules:**
  - ✅ Llama `StockService.get_stock_alerts()`
  - ✅ Filtro por `sucursal_id` (requerido)
  - ✅ Ordenado por stock_qty ascendente (más bajo primero)
- **Tests Faltantes:**
  - ✅ Obtener alertas (super_admin)
  - ✅ Obtener alertas (admin_viewer)
  - ✅ Obtener alertas (recepcion)
  - ❌ Denegar acceso (kidibar, monitor)
  - ❌ Filtro por sucursal_id (requerido)
  - ❌ Solo productos con stock_qty <= threshold_alert_qty
  - ❌ Ordenado por stock_qty ascendente
  - ❌ Lista vacía cuando no hay alertas
  - ❌ Error cuando sucursal_id no se proporciona

---

### 📊 RESUMEN OPERATIONS ROUTER

**Total Endpoints:** 5  
**Tests Necesarios Estimados:** ~40-50 tests  
**Complejidad:** Alta (lógica de negocio compleja, cálculos, validaciones)

**Gaps Críticos:**
1. ❌ **0% coverage** - Ningún endpoint testado
2. ❌ **Business rules críticas** no validadas (día activo, cálculos)
3. ❌ **Cálculos financieros** no testados (system_total, difference)
4. ❌ **Integración con servicios** no testada (DayStartService, DayCloseService)
5. ❌ **Edge cases** (cerrar sin ventas, múltiples días, etc.)

---

## 📋 AUTHENTICATION ROUTER - ANÁLISIS COMPLETO

### Endpoints Identificados (2 endpoints, ~40% coverage)

#### AUTH ENDPOINTS

**1. POST `/auth/login`**
- **Permisos:** Público (no requiere autenticación)
- **Lógica:** Autentica usuario, retorna JWT
- **Business Rules:**
  - ✅ Busca usuario por username
  - ✅ Verifica password con `verify_password()`
  - ✅ Actualiza `last_login` timestamp
  - ✅ Crea JWT token con `create_access_token()`
  - ✅ Retorna `LoginResponse` con token y user
- **Tests Existentes:**
  - ✅ Login exitoso (test_user/recepcion)
  - ✅ Login con credenciales inválidas
- **Tests Faltantes:**
  - ❌ **Login con cada rol** (super_admin, admin_viewer, recepcion, kidibar, monitor)
  - ❌ **Verificar que token contiene role correcto**
  - ❌ **Verificar que last_login se actualiza**
  - ❌ Usuario inactivo (is_active=False)
  - ❌ Usuario no existe
  - ❌ Password incorrecto
  - ❌ Validación campos requeridos (username, password)

**2. GET `/auth/me`**
- **Permisos:** Requiere autenticación (cualquier rol)
- **Lógica:** Retorna usuario actual
- **Business Rules:**
  - ✅ Valida JWT token
  - ✅ Retorna `UserRead` del usuario autenticado
- **Tests Existentes:**
  - ✅ Get current user con token válido
  - ✅ Get current user con token inválido
- **Tests Faltantes:**
  - ❌ **Get current user con cada rol**
  - ❌ **Token expirado** (usar `expired_token` fixture)
  - ❌ **Token inválido** (formato incorrecto)
  - ❌ **Token sin usuario** (usuario eliminado después de token)
  - ❌ **Sin token** (401)

---

### 📊 PERMISOS CROSS-MODULE - ANÁLISIS

**Matrix de Permisos Identificada:**

| Endpoint | super_admin | admin_viewer | recepcion | kidibar | monitor |
|----------|-------------|-------------|-----------|---------|---------|
| GET /sucursales | ✅ | ✅ | ❌ | ❌ | ❌ |
| POST /sucursales | ✅ | ❌ | ❌ | ❌ | ❌ |
| GET /products | ✅ | ✅ | ❌ | ✅ | ❌ |
| POST /products | ✅ | ❌ | ❌ | ❌ | ❌ |
| GET /services | ✅ | ✅ | ✅ | ❌ | ❌ |
| POST /services | ✅ | ❌ | ❌ | ❌ | ❌ |
| GET /packages | ✅ | ✅ | ✅ | ❌ | ❌ |
| POST /packages | ✅ | ❌ | ❌ | ❌ | ❌ |
| POST /day/start | ❌ | ❌ | ✅ | ❌ | ❌ |
| GET /day/status | ❌ | ❌ | ✅ | ❌ | ❌ |
| POST /day/close | ❌ | ❌ | ✅ | ❌ | ❌ |
| GET /day/close/history | ❌ | ❌ | ✅ | ❌ | ❌ |
| GET /stock/alerts | ✅ | ✅ | ✅ | ❌ | ❌ |
| POST /sales | ❌ | ❌ | ✅ | ✅ | ❌ |
| GET /sales | ✅ | ✅ | ✅ | ✅ | ❌ |
| GET /timers/active | ✅ | ✅ | ✅ | ✅ | ✅ |

**Tests Faltantes de Permisos:**
- ❌ **Matrix completa de permisos** (cada endpoint con cada rol)
- ❌ **403 Forbidden** cuando rol no tiene acceso
- ❌ **401 Unauthorized** cuando no hay token
- ❌ **Cross-module permissions** (ej: recepcion puede ver kidibar readonly)

---

## 📋 SALES ROUTER - EDGE CASES FALTANTES

### Endpoints Parcialmente Testados

**1. POST `/sales`** (parcialmente testado)
- **Tests Existentes:**
  - ✅ Crear venta con servicio → crea timer
  - ✅ Crear venta requiere autenticación
- **Tests Faltantes:**
  - ❌ **Timer delay 3 minutos** (`start_delay_minutes`)
  - ❌ **Validación edad niño** (si aplica)
  - ❌ **Firma pagador** (si aplica)
  - ❌ **Tipo servicio** (timer vs día)
  - ❌ **Rollback en errores WebSocket**
  - ❌ **Venta con múltiples items**
  - ❌ **Venta con producto + servicio**
  - ❌ **Permisos** (recepcion y kidibar pueden crear)

**2. POST `/sales/{sale_id}/extend`** (parcialmente testado)
- **Tests Existentes:**
  - ✅ Extender timer vía endpoint
- **Tests Faltantes:**
  - ❌ **Permisos** (solo recepcion)
  - ❌ **404 cuando sale no tiene timer**
  - ❌ **Error cuando timer no está activo**
  - ❌ **Validación minutes > 0**

**3. POST `/sales/{sale_id}/print`** (no testado)
- **Tests Faltantes:**
  - ❌ Generar ticket HTML
  - ❌ Permisos (recepcion, kidibar, super_admin, admin_viewer)
  - ❌ 404 cuando sale no existe
  - ❌ Formato HTML correcto
  - ❌ Incluir timer info si existe

---

## 📊 RESUMEN GENERAL DE GAPS

### Backend - Coverage Estimado

| Router | Endpoints | Tests Existentes | Tests Necesarios | Coverage |
|--------|-----------|------------------|------------------|----------|
| Catalog | 16 | 0 | ~80-100 | 0% |
| Operations | 5 | 0 | ~40-50 | 0% |
| Auth | 2 | 4 | ~15-20 | ~40% |
| Sales | 6 | 3 | ~20-30 | ~30% |
| Timers | 1 | 1 | ~5-10 | ~20% |
| Reports | 5 | Parcial | ~15-20 | ~30% |
| Exports | 2 | 0 | ~10-15 | 0% |
| Users | 5 | Parcial | ~10-15 | ~40% |

**Total Estimado:**
- **Endpoints:** ~42
- **Tests Existentes:** ~10-15
- **Tests Necesarios:** ~200-250
- **Coverage Actual:** ~45-50%
- **Coverage Objetivo:** 75%+

---

## 🎯 PRIORIZACIÓN DE IMPLEMENTACIÓN

### FASE 1: BLOQUEADORES CRÍTICOS (8-12h)

**1. Catalog Router Tests (4-6h) - PRIORIDAD #1**
- 16 endpoints
- ~80-100 tests
- CRUD completo + permisos + validaciones

**2. Operations Router Tests (3-4h) - PRIORIDAD #2**
- 5 endpoints
- ~40-50 tests
- Lógica de negocio compleja + cálculos

**3. Auth Completo (2-3h) - PRIORIDAD #3**
- Login por cada rol
- Permisos cross-module
- JWT lifecycle completo

**4. Sales Edge Cases (2-3h) - PRIORIDAD #4**
- Timer delay
- Extensión desde venta
- Validaciones adicionales

---

## 📝 ESTRUCTURA DE TESTS SUGERIDA

### Catalog Router
```
tests/integration/test_catalog_endpoints.py
├─ TestSucursalesEndpoints
│  ├─ test_get_sucursales
│  ├─ test_create_sucursal
│  ├─ test_update_sucursal
│  ├─ test_delete_sucursal
│  └─ test_permissions_sucursales
├─ TestProductsEndpoints
│  ├─ test_get_products
│  ├─ test_create_product
│  ├─ test_update_product
│  ├─ test_delete_product
│  └─ test_permissions_products
├─ TestServicesEndpoints
│  ├─ test_get_services
│  ├─ test_create_service
│  ├─ test_update_service
│  ├─ test_delete_service
│  └─ test_permissions_services
└─ TestPackagesEndpoints
   ├─ test_get_packages
   ├─ test_create_package
   ├─ test_update_package
   ├─ test_delete_package
   └─ test_permissions_packages
```

### Operations Router
```
tests/integration/test_operations_endpoints.py
├─ TestDayStartEndpoints
│  ├─ test_start_day
│  ├─ test_start_day_already_active
│  ├─ test_start_day_permissions
│  └─ test_start_day_validations
├─ TestDayStatusEndpoints
│  ├─ test_get_day_status_open
│  ├─ test_get_day_status_closed
│  └─ test_get_day_status_permissions
├─ TestDayCloseEndpoints
│  ├─ test_close_day
│  ├─ test_close_day_calculations
│  ├─ test_close_day_no_sales
│  └─ test_close_day_permissions
└─ TestDayCloseHistoryEndpoints
   ├─ test_get_history
   ├─ test_get_history_filters
   └─ test_get_history_permissions
```

### Auth Completo
```
tests/integration/test_auth_complete.py
├─ TestLoginByRole
│  ├─ test_login_super_admin
│  ├─ test_login_admin_viewer
│  ├─ test_login_recepcion
│  ├─ test_login_kidibar
│  └─ test_login_monitor
├─ TestCrossModulePermissions
│  ├─ test_recepcion_can_view_kidibar_readonly
│  └─ test_monitor_readonly_access
├─ TestJWTLifecycle
│  ├─ test_token_expiration
│  ├─ test_token_refresh
│  └─ test_token_validation
└─ TestUnauthorizedAccess
   ├─ test_403_forbidden
   ├─ test_401_unauthorized
   └─ test_role_based_access_matrix
```

---

## ✅ CRITERIOS DE ÉXITO

### Coverage Targets
- **Catalog Router:** 90%+ (todos los endpoints)
- **Operations Router:** 85%+ (lógica compleja)
- **Auth Router:** 90%+ (seguridad crítica)
- **Backend Global:** 75%+

### Tests Count Targets
- **Catalog:** +80 tests
- **Operations:** +40 tests
- **Auth:** +15 tests
- **Sales Edge Cases:** +10 tests
- **Total:** +145 tests mínimo

### Bloqueadores Resueltos
- [ ] Catalog CRUD 100% cubierto
- [ ] Operations day cycle 100% cubierto
- [ ] Auth por rol 100% cubierto
- [ ] Permisos cross-module validados
- [ ] Business rules críticas testadas

---

**SIGUIENTE PASO:** Implementar Catalog Router tests como prioridad #1.





























