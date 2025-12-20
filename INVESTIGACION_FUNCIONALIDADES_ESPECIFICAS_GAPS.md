# 🔍 INVESTIGACIÓN EXHAUSTIVA - FUNCIONALIDADES ESPECÍFICAS vs IMPLEMENTACIÓN

**Fecha:** 2025-01-XX  
**Metodología:** Comparación funcionalidad específica por funcionalidad específica  
**Estado:** ⚠️ **GAPS CRÍTICOS IDENTIFICADOS - ROADMAP DETALLADO**

---

## 📋 FUNCIONALIDADES ESPECÍFICAS - ANÁLISIS COMPLETO

### 👑 SUPER ADMIN

#### Dashboard/Métricas

| Funcionalidad Específica | Estado Actual | Backend Gap | Frontend Gap | Effort | Criticidad |
|---------------------------|---------------|-------------|--------------|--------|------------|
| **Dashboard métricas todas sucursales** | ✅ Implementado | ✅ Completo | ✅ Completo | - | 🟡 CORE |
| **Botón maestro actualizar métricas** | ✅ Implementado | ✅ `/reports/refresh` | ✅ `RefreshButton.svelte` | - | 🟡 CORE |
| **Análisis inteligente métricas** | ✅ Implementado | ✅ Predicciones ML | ✅ `PredictionsPanel.svelte` | - | 🟢 ENHANCEMENT |
| **Reportes imprimibles Excel/PDF** | ❌ Faltante | ❌ No endpoints export | ❌ No componentes export | **8-10h** | 🟢 ENHANCEMENT |

**DETALLES:**

- ✅ **Dashboard métricas:** `apps/web/src/routes/admin/+page.svelte` muestra métricas de ventas, stock, servicios
- ✅ **Botón maestro:** `RefreshButton.svelte` con validaciones (2s mínimo, 30 max por sesión)
- ✅ **Análisis inteligente:** `PredictionsPanel.svelte` con predicciones de ventas, capacidad, stock
- ❌ **Export Excel/PDF:** No existe funcionalidad de export. Necesita:
  - Backend: Endpoints `GET /reports/export/excel`, `GET /reports/export/pdf`
  - Frontend: Botones "Exportar Excel" y "Exportar PDF" en dashboard
  - Librerías: `openpyxl` (Excel), `reportlab` o `weasyprint` (PDF)

#### Gestión Sucursales

| Funcionalidad Específica | Estado Actual | Backend Gap | Frontend Gap | Effort | Criticidad |
|---------------------------|---------------|-------------|--------------|--------|------------|
| **Ver sucursales disponibles** | ✅ Implementado | ✅ `GET /sucursales` | ⚠️ No UI dedicada | **4-6h** | 🟡 CORE |
| **Crear sucursal** | ✅ Implementado | ✅ `POST /sucursales` | ⚠️ No UI dedicada | **4-6h** | 🟡 CORE |
| **Métricas específicas por sucursal** | ✅ Implementado | ✅ Query param `sucursal_id` | ⚠️ No selector sucursal | **2-3h** | 🟡 CORE |

**DETALLES:**

- ✅ **Backend:** Endpoints completos para sucursales
- ⚠️ **Frontend:** No hay ruta `/admin/sucursales` ni componentes `SucursalList.svelte`, `SucursalForm.svelte`
- ⚠️ **Selector sucursal:** Dashboard no tiene dropdown para filtrar por sucursal

#### Gestión Servicios

| Funcionalidad Específica | Estado Actual | Backend Gap | Frontend Gap | Effort | Criticidad |
|---------------------------|---------------|-------------|--------------|--------|------------|
| **Definir nombre juego/servicio** | ✅ Implementado | ✅ Modelo `Service.name` | ⚠️ No UI CRUD | **8-10h** | 🚨 BLOQUEADOR |
| **Precio por uso acorde timer** | ✅ Implementado | ✅ `base_price_per_slot` | ⚠️ No UI CRUD | **8-10h** | 🚨 BLOQUEADOR |
| **Implementar media hora en media hora** | ✅ Implementado | ✅ `durations_allowed` JSON | ⚠️ No UI CRUD | **8-10h** | 🚨 BLOQUEADOR |
| **Alertas 5/10/15 min configurables** | ⚠️ Parcial | ✅ `alerts_config` JSON | ❌ No UI configuración | **6-8h** | 🚨 BLOQUEADOR |
| **Modalidad timer Y por día** | ✅ Implementado | ✅ `tipo: "service"` o `"day"` | ⚠️ No selector en venta | **4-6h** | 🟡 CORE |
| **Sistema paquetes genéricos** | ❌ Faltante | ⚠️ Modelo existe | ❌ No endpoints ni UI | **12-16h** | 🟡 CORE |
| **Exportar video con branding** | ❌ Faltante | ❌ No existe | ❌ No existe | **20-24h** | 🟢 ENHANCEMENT |

**DETALLES:**

- ✅ **Backend Modelo:** `Service` tiene `name`, `base_price_per_slot`, `durations_allowed`, `alerts_config`
- ⚠️ **Backend CRUD:** Solo `GET /services` y `POST /services`. Faltan `PUT /services/{id}` y `DELETE /services/{id}`
- ❌ **Frontend CRUD:** `apps/web/src/routes/admin/services/+page.svelte` es solo placeholder
- ⚠️ **Alertas configurables:** Backend tiene `alerts_config` pero no hay UI para configurar umbrales 5/10/15 min
- ❌ **Paquetes:** Modelo `Package` existe pero no hay endpoints ni UI
- ❌ **Export video:** Funcionalidad completamente faltante (requiere generación de video con branding)

#### Gestión Productos

| Funcionalidad Específica | Estado Actual | Backend Gap | Frontend Gap | Effort | Criticidad |
|---------------------------|---------------|-------------|--------------|--------|------------|
| **Inventario con stock disponible** | ✅ Implementado | ✅ `Product.stock_qty` | ⚠️ No UI edición | **8-10h** | 🚨 BLOQUEADOR |
| **Precio por producto** | ✅ Implementado | ✅ `Product.price_cents` | ⚠️ No UI CRUD | **8-10h** | 🚨 BLOQUEADOR |
| **Casilla "disponible para paquete"** | ✅ Implementado | ✅ `enabled_for_package` | ⚠️ No UI CRUD | **8-10h** | 🟡 CORE |
| **Cantidad a descontar en paquete** | ✅ Implementado | ✅ `package_deduction_qty` | ⚠️ No UI CRUD | **8-10h** | 🟡 CORE |
| **Alertas stock bajo configurables** | ✅ Implementado | ✅ `threshold_alert_qty` | ⚠️ No UI configuración | **4-6h** | 🟡 CORE |
| **Exportar video productos** | ❌ Faltante | ❌ No existe | ❌ No existe | **20-24h** | 🟢 ENHANCEMENT |

**DETALLES:**

- ✅ **Backend Modelo:** `Product` tiene todos los campos necesarios
- ⚠️ **Backend CRUD:** Solo `GET /products` y `POST /products`. Faltan `PUT /products/{id}` y `DELETE /products/{id}`
- ❌ **Frontend CRUD:** `apps/web/src/routes/admin/products/+page.svelte` es solo placeholder
- ⚠️ **Configuración alertas:** No hay UI para configurar `threshold_alert_qty` por producto

#### Gestión Usuarios

| Funcionalidad Específica | Estado Actual | Backend Gap | Frontend Gap | Effort | Criticidad |
|---------------------------|---------------|-------------|--------------|--------|------------|
| **Crear/eliminar accesos** | ✅ Implementado | ✅ CRUD completo | ✅ `UserList.svelte` | - | 🟡 CORE |
| **Username + password (sin email)** | ✅ Implementado | ✅ Sin email | ✅ Sin email | - | 🟡 CORE |
| **Vista previa tiempo real paneles** | ❌ Faltante | ❌ No existe | ❌ No existe | **12-16h** | 🟢 ENHANCEMENT |

**DETALLES:**

- ✅ **CRUD usuarios:** Completamente implementado
- ❌ **Vista previa paneles:** No hay funcionalidad para previsualizar cómo se ve cada panel para cada rol

---

### 🎮 RECEPCIÓN

#### Operación Diaria

| Funcionalidad Específica | Estado Actual | Backend Gap | Frontend Gap | Effort | Criticidad |
|---------------------------|---------------|-------------|--------------|--------|------------|
| **Botón "Iniciar día"** | ❌ Faltante | ❌ No endpoint | ❌ No componente | **6-8h** | 🚨 BLOQUEADOR |
| **Registrar hora y sincronizar** | ❌ Faltante | ❌ No modelo `DayStart` | ❌ No lógica | **6-8h** | 🚨 BLOQUEADOR |
| **Botón "Cerrar día"** | ⚠️ Parcial | ✅ `POST /day/close` | ❌ No UI | **6-8h** | 🚨 BLOQUEADOR |
| **Arqueo con diferencias** | ⚠️ Parcial | ✅ Calcula diferencias | ❌ No UI visualización | **6-8h** | 🚨 BLOQUEADOR |
| **Ingresar dinero contado** | ⚠️ Parcial | ✅ `physical_count_cents` | ❌ No formulario | **4-6h** | 🚨 BLOQUEADOR |
| **Historial completo arqueos** | ❌ Faltante | ❌ No endpoint | ❌ No componente | **4-6h** | 🟡 CORE |
| **Alertas si hay diferencias** | ⚠️ Parcial | ✅ Calcula diferencia | ❌ No notificaciones | **2-3h** | 🟡 CORE |

**DETALLES:**

- ❌ **Iniciar día:** No existe `POST /day/start` ni modelo `DayStart`. Necesita:
  - Backend: Modelo `DayStart`, endpoint `POST /day/start`, validación de solo un día abierto
  - Frontend: `DayStartForm.svelte`, ruta `/recepcion/iniciar-dia`
- ⚠️ **Cerrar día:** Backend existe pero falta UI completa:
  - Backend: ✅ `POST /day/close` calcula diferencias
  - Frontend: ❌ No hay `DayCloseForm.svelte`, no hay visualización de diferencias
- ❌ **Historial arqueos:** No hay `GET /day/close/history` ni componente `DayCloseHistory.svelte`

#### Ventas Servicios

| Funcionalidad Específica | Estado Actual | Backend Gap | Frontend Gap | Effort | Criticidad |
|---------------------------|---------------|-------------|--------------|--------|------------|
| **Seleccionar juego solicitado** | ✅ Implementado | ✅ `GET /services` | ✅ `ServiceSelector.svelte` | - | 🚨 BLOQUEADOR |
| **Escoger timer o por día** | ⚠️ Parcial | ✅ `tipo: "service"` o `"day"` | ❌ No selector en UI | **4-6h** | 🟡 CORE |
| **Quantify (agregar/quitar) desde 0** | ⚠️ Parcial | N/A | ⚠️ Solo duración, no cantidad | **4-6h** | 🟡 CORE |
| **Seleccionar por paquete** | ❌ Faltante | ❌ No endpoints paquetes | ❌ No selector paquetes | **8-12h** | 🟡 CORE |
| **Formulario ticket manual** | ❌ Faltante | ❌ No campos adicionales | ❌ No formulario completo | **8-10h** | 🚨 BLOQUEADOR |
| **Nombre del niño** | ✅ Implementado | ✅ `child_name` en timer | ✅ En `ServiceSaleForm` | - | 🚨 BLOQUEADOR |
| **Edad** | ❌ Faltante | ❌ No campo en modelo | ❌ No campo en formulario | **2-3h** | 🟡 CORE |
| **Adulto responsable** | ⚠️ Parcial | ✅ `payer_name` | ✅ En formulario | - | 🚨 BLOQUEADOR |
| **Hora entrada/salida** | ⚠️ Parcial | ✅ `start_at`, `end_at` en timer | ❌ No se muestra en ticket | **2-3h** | 🟡 CORE |
| **Firma adulto responsable** | ❌ Faltante | ❌ No campo | ❌ No captura firma | **6-8h** | 🟢 ENHANCEMENT |
| **Timer inicia 3 min después ticket** | ❌ Faltante | ❌ No delay configurable | ❌ No lógica delay | **4-6h** | 🟡 CORE |
| **Opción extender timer** | ⚠️ Parcial | ✅ `POST /sales/{id}/extend` | ❌ No botón en UI | **4-6h** | 🚨 BLOQUEADOR |
| **Alertas timer configurables** | ⚠️ Parcial | ✅ WebSocket alerts | ⚠️ Básico, no configurables | **6-8h** | 🚨 BLOQUEADOR |

**DETALLES:**

- ✅ **Seleccionar juego:** `ServiceSelector.svelte` permite seleccionar servicio y duración
- ⚠️ **Timer o por día:** Backend soporta ambos tipos pero UI solo permite timer. Falta selector
- ⚠️ **Quantify:** Actualmente solo se puede seleccionar duración, no cantidad de servicios
- ❌ **Paquetes:** No hay selector de paquetes en `ServiceSaleForm.svelte`
- ❌ **Formulario ticket manual completo:** Faltan campos:
  - Edad del niño
  - Firma del adulto responsable
  - Visualización de hora entrada/salida en ticket
- ❌ **Timer delay 3 min:** No hay lógica para iniciar timer 3 minutos después de imprimir ticket
- ⚠️ **Extender timer:** Backend existe pero no hay botón "Extender" en `timers/+page.svelte`
- ⚠️ **Alertas configurables:** WebSocket envía alertas pero no hay UI para configurar umbrales 5/10/15 min

#### Ventas Productos

| Funcionalidad Específica | Estado Actual | Backend Gap | Frontend Gap | Effort | Criticidad |
|---------------------------|---------------|-------------|--------------|--------|------------|
| **Ver stock disponible tiempo real** | ✅ Implementado | ✅ `GET /products` | ✅ `ProductSelector.svelte` | - | 🚨 BLOQUEADOR |
| **Quantify productos (agregar/quitar)** | ✅ Implementado | N/A | ✅ Carrito con +/- | - | 🚨 BLOQUEADOR |
| **Sincronización inventario tiempo real** | ✅ Implementado | ✅ WebSocket stock alerts | ✅ WebSocket integrado | - | 🟡 CORE |
| **Ticket productos info básica** | ⚠️ Parcial | ✅ Datos en venta | ❌ No componente ticket | **4-6h** | 🚨 BLOQUEADOR |

**DETALLES:**

- ✅ **Stock tiempo real:** `ProductSelector.svelte` muestra stock y WebSocket actualiza
- ✅ **Quantify:** Carrito permite agregar/quitar productos con botones +/-
- ⚠️ **Ticket productos:** No hay componente `Ticket.svelte` para imprimir

#### Estadísticas Recepción

| Funcionalidad Específica | Estado Actual | Backend Gap | Frontend Gap | Effort | Criticidad |
|---------------------------|---------------|-------------|--------------|--------|------------|
| **Ventas productos y servicios** | ❌ Faltante | ❌ No `GET /sales` | ❌ No componente | **8-10h** | 🟡 CORE |
| **Inventario productos** | ✅ Implementado | ✅ `GET /stock/alerts` | ✅ `inventario/+page.svelte` | - | 🟡 CORE |
| **Tickets generados** | ❌ Faltante | ❌ No contador tickets | ❌ No métrica | **4-6h** | 🟢 ENHANCEMENT |
| **Horas pico** | ❌ Faltante | ❌ No análisis horas pico | ❌ No visualización | **8-10h** | 🟢 ENHANCEMENT |
| **Actualización tiempo real** | ⚠️ Parcial | ✅ WebSocket | ⚠️ Solo timers/stock | **4-6h** | 🟡 CORE |

**DETALLES:**

- ❌ **Ventas:** No hay `GET /sales` para listar ventas del día
- ❌ **Tickets generados:** No hay contador ni métrica de tickets
- ❌ **Horas pico:** No hay análisis de horas con más ventas
- ⚠️ **Tiempo real:** WebSocket solo para timers y stock, no para ventas

---

### 🍿 KIDIBAR/SNACKS

| Funcionalidad Específica | Estado Actual | Backend Gap | Frontend Gap | Effort | Criticidad |
|---------------------------|---------------|-------------|--------------|--------|------------|
| **Iniciar día (solo productos)** | ❌ Faltante | ❌ No endpoint específico | ❌ No componente | **6-8h** | 🟡 CORE |
| **Cerrar día (solo productos)** | ❌ Faltante | ❌ No endpoint específico | ❌ No componente | **6-8h** | 🟡 CORE |
| **Misma funcionalidad recepción (solo productos)** | ✅ Implementado | ✅ `POST /sales` productos | ✅ `ProductSaleForm.svelte` | - | 🚨 BLOQUEADOR |
| **Sin acceso servicios/timers** | ✅ Implementado | ✅ Permisos backend | ✅ Route guards | - | 🟡 CORE |
| **Estadísticas solo productos** | ❌ Faltante | ❌ No filtro por tipo | ❌ No componente | **6-8h** | 🟡 CORE |

**DETALLES:**

- ✅ **Ventas productos:** Completamente implementado
- ❌ **Iniciar/cerrar día:** No hay endpoints específicos para kidibar (solo productos)
- ❌ **Estadísticas:** No hay dashboard específico para kidibar con solo métricas de productos

---

### 📺 MONITOR

| Funcionalidad Específica | Estado Actual | Backend Gap | Frontend Gap | Effort | Criticidad |
|---------------------------|---------------|-------------|--------------|--------|------------|
| **Solo viewer panel recepción tiempo real** | ✅ Implementado | ✅ WebSocket | ✅ `timers/+page.svelte` | - | 🚨 BLOQUEADOR |
| **Sin registro ventas/productos/tickets** | ✅ Implementado | ✅ Permisos readonly | ✅ Sin botones edición | - | 🟡 CORE |
| **Solo visualización timers y métricas** | ✅ Implementado | ✅ Permisos | ✅ UI readonly | - | 🟡 CORE |

**DETALLES:**

- ✅ **Monitor:** Completamente funcional según requisitos
- ⚠️ **Mejoras posibles:** Alertas visuales/sonoras más destacadas (no crítico)

---

## 🚨 GAPS CRÍTICOS - TABLA CONSOLIDADA

| Funcionalidad | Estado | Backend Gap | Frontend Gap | Database Gap | Effort | Criticidad |
|---------------|--------|-------------|--------------|--------------|--------|------------|
| **Iniciar día** | ❌ 0% | `POST /day/start`, modelo `DayStart` | `DayStartForm.svelte` | Tabla `day_starts` | **6-8h** | 🚨 BLOQUEADOR |
| **Cerrar día UI** | ⚠️ 50% | ✅ Existe | `DayCloseForm.svelte`, visualización diferencias | - | **6-8h** | 🚨 BLOQUEADOR |
| **Historial arqueos** | ❌ 0% | `GET /day/close/history` | `DayCloseHistory.svelte` | - | **4-6h** | 🟡 CORE |
| **Imprimir tickets** | ❌ 0% | `POST /sales/{id}/print` | `Ticket.svelte` | - | **8-10h** | 🚨 BLOQUEADOR |
| **Formulario ticket completo** | ⚠️ 60% | Campo `age`, `signature` | Campos edad, firma | `age` en timer, `signature` en sale | **8-10h** | 🚨 BLOQUEADOR |
| **Timer delay 3 min** | ❌ 0% | Lógica delay en creación timer | UI configuración delay | - | **4-6h** | 🟡 CORE |
| **Extender timer UI** | ⚠️ 50% | ✅ Existe | `ExtendTimerModal.svelte`, botón en timers | - | **4-6h** | 🚨 BLOQUEADOR |
| **Alertas timer 5/10/15 min configurables** | ⚠️ 40% | ✅ `alerts_config` existe | UI configuración umbrales | - | **6-8h** | 🚨 BLOQUEADOR |
| **Sistema paquetes completo** | ❌ 0% | `GET/POST/PUT/DELETE /packages` | `PackageList.svelte`, `PackageForm.svelte` | - | **12-16h** | 🟡 CORE |
| **CRUD servicios completo** | ⚠️ 30% | `PUT/DELETE /services/{id}` | `ServiceList.svelte`, `ServiceForm.svelte` | - | **8-10h** | 🚨 BLOQUEADOR |
| **CRUD productos completo** | ⚠️ 30% | `PUT/DELETE /products/{id}` | `ProductList.svelte`, `ProductForm.svelte` | - | **8-10h** | 🚨 BLOQUEADOR |
| **Historial ventas** | ❌ 0% | `GET /sales`, `GET /sales/{id}`, `GET /sales/today` | `SalesHistory.svelte` | - | **8-10h** | 🚨 BLOQUEADOR |
| **Estadísticas recepción** | ❌ 0% | Endpoints estadísticas por sucursal | Dashboard recepción | - | **8-10h** | 🟡 CORE |
| **Export Excel/PDF** | ❌ 0% | `GET /reports/export/excel`, `GET /reports/export/pdf` | Botones export | - | **8-10h** | 🟢 ENHANCEMENT |
| **Export video branding** | ❌ 0% | Generación video servicios/productos | UI export | - | **20-24h** | 🟢 ENHANCEMENT |
| **Selector timer vs día** | ⚠️ 50% | ✅ Backend soporta | Selector en `ServiceSaleForm` | - | **4-6h** | 🟡 CORE |
| **Quantify servicios (cantidad)** | ⚠️ 50% | N/A | Selector cantidad en `ServiceSelector` | - | **4-6h** | 🟢 ENHANCEMENT |

---

## 🗺️ ROADMAP PRIORIZADO

### SPRINT 1: BLOQUEADORES CRÍTICOS (Estimado: 4-5 días)

**Sin estas funcionalidades NO puede operar diariamente**

#### 1.1 Imprimir Tickets (8-10 horas)
- **Backend:** `POST /sales/{id}/print` endpoint
  - Generar formato ticket con logo, datos venta, items, total, fecha/hora
  - Retornar HTML/PDF imprimible
- **Frontend:** `Ticket.svelte` component
  - Formato: Logo Kidyland, datos venta, items, total, fecha/hora
  - Botón "Imprimir" usando `window.print()` o API impresora
  - Mostrar después de crear venta
- **Justificación:** Sin tickets no hay comprobante de venta legal

#### 1.2 Historial de Ventas (8-10 horas)
- **Backend:** 
  - `GET /sales?skip=X&limit=Y&sucursal_id=Z&date=YYYY-MM-DD`
  - `GET /sales/{id}` - Obtener venta específica
  - `GET /sales/today` - Ventas del día actual
- **Frontend:**
  - `SalesHistory.svelte` component
  - Rutas `/recepcion/ventas` y `/kidibar/ventas`
  - Filtros: Por fecha, por tipo, por usuario
  - Botón "Reimprimir ticket" en cada venta
- **Justificación:** Necesario para seguimiento y reimpresión de tickets

#### 1.3 Extender Timer UI (4-6 horas)
- **Backend:** ✅ Ya existe `POST /sales/{id}/extend`
- **Frontend:**
  - Botón "Extender" en cada timer en `timers/+page.svelte`
  - `ExtendTimerModal.svelte` - Modal para ingresar minutos a agregar
  - Validaciones: Solo números positivos
- **Justificación:** Recepción necesita extender timers frecuentemente

#### 1.4 CRUD Servicios Completo (8-10 horas)
- **Backend:**
  - `PUT /services/{id}` - Actualizar servicio
  - `DELETE /services/{id}` - Eliminar servicio (soft delete)
- **Frontend:**
  - `ServiceList.svelte` - Lista con filtros
  - `ServiceForm.svelte` - Formulario crear/editar
  - Ruta `/admin/services` funcional
  - Validaciones: Duraciones, precios, alertas
- **Justificación:** Admin necesita gestionar servicios completamente

#### 1.5 CRUD Productos Completo (8-10 horas)
- **Backend:**
  - `PUT /products/{id}` - Actualizar producto
  - `DELETE /products/{id}` - Eliminar producto (soft delete)
- **Frontend:**
  - `ProductList.svelte` - Lista con filtros
  - `ProductForm.svelte` - Formulario crear/editar
  - Ruta `/admin/products` funcional
  - Validaciones: Stock, precios, umbrales
- **Justificación:** Admin necesita gestionar productos completamente

#### 1.6 Formulario Ticket Completo (8-10 horas)
- **Backend:**
  - Agregar campo `age` a modelo `Timer` (opcional)
  - Agregar campo `signature` a modelo `Sale` (opcional, JSON base64)
- **Frontend:**
  - Campo "Edad" en `ServiceSaleForm.svelte`
  - Campo "Firma" (canvas o upload) en `ServiceSaleForm.svelte`
  - Mostrar hora entrada/salida en ticket
- **Justificación:** Ticket debe tener información completa según requisitos

**Total Sprint 1:** 44-56 horas (5.5-7 días)

---

### SPRINT 2: CORE BUSINESS (Estimado: 5-6 días)

**Funcionalidades centrales del negocio**

#### 2.1 Iniciar/Cerrar Día Completo (12-16 horas)
- **Backend:**
  - Modelo `DayStart` con campos: `sucursal_id`, `usuario_id`, `started_at`, `initial_cash_cents`
  - `POST /day/start` - Iniciar día
  - `GET /day/status` - Estado del día (abierto/cerrado)
  - Mejorar `POST /day/close` para exponer diferencias claramente
- **Frontend:**
  - `DayStartForm.svelte` - Formulario iniciar día (hora, dinero inicial)
  - `DayCloseForm.svelte` - Formulario cerrar día (dinero contado)
  - `CashReconciliation.svelte` - Visualización de diferencias
  - Rutas `/recepcion/iniciar-dia`, `/recepcion/cerrar-dia`
  - Validaciones: Solo un día abierto a la vez
- **Justificación:** Control de sesiones diarias es crítico

#### 2.2 Historial Arqueos (4-6 horas)
- **Backend:**
  - `GET /day/close/history?sucursal_id=X&start_date=Y&end_date=Z`
- **Frontend:**
  - `DayCloseHistory.svelte` component
  - Ruta `/recepcion/arqueos`
  - Filtros: Por fecha, por sucursal
  - Visualización: Tabla con diferencias destacadas
- **Justificación:** Historial de arqueos nunca se borra según requisitos

#### 2.3 Alertas Timer Configurables (6-8 horas)
- **Backend:**
  - ✅ `alerts_config` ya existe en modelo `Service`
  - Mejorar WebSocket para respetar configuración por servicio
- **Frontend:**
  - UI en `ServiceForm.svelte` para configurar alertas 5/10/15 min
  - `TimerAlertNotification.svelte` - Notificaciones visuales mejoradas
  - Sonidos de alerta configurables
  - Cambio de color destacado (amarillo/rojo) según tiempo restante
- **Justificación:** Alertas configurables son críticas para operación

#### 2.4 Sistema Paquetes Completo (12-16 horas)
- **Backend:**
  - `GET /packages` - Listar paquetes
  - `POST /packages` - Crear paquete
  - `PUT /packages/{id}` - Actualizar paquete
  - `DELETE /packages/{id}` - Eliminar paquete
  - Integración: Vender paquetes desde `POST /sales` (tipo "package")
- **Frontend:**
  - `PackageList.svelte` - Lista de paquetes
  - `PackageForm.svelte` - Formulario crear/editar paquete
  - `PackageSelector.svelte` - Selector de paquetes en venta
  - Ruta `/admin/packages`
  - Integración: Selector de paquetes en `ServiceSaleForm.svelte`
- **Justificación:** Paquetes promocionales son importantes para negocio

#### 2.5 Estadísticas Recepción (8-10 horas)
- **Backend:**
  - `GET /reports/recepcion?sucursal_id=X&date=Y` - Métricas recepción
  - Análisis horas pico
- **Frontend:**
  - Dashboard recepción con métricas:
    - Ventas del día
    - Tickets generados
    - Horas pico
    - Inventario productos
  - Ruta `/recepcion/estadisticas`
- **Justificación:** Recepción necesita ver sus métricas

**Total Sprint 2:** 42-56 horas (5.5-7 días)

---

### SPRINT 3: ENHANCEMENTS (Estimado: 4-5 días)

**Mejoras que no bloquean operación pero mejoran UX**

#### 3.1 Export Excel/PDF (8-10 horas)
- **Backend:**
  - `GET /reports/export/excel?report_type=X&date=Y`
  - `GET /reports/export/pdf?report_type=X&date=Y`
  - Librerías: `openpyxl` (Excel), `reportlab` (PDF)
- **Frontend:**
  - Botones "Exportar Excel" y "Exportar PDF" en dashboard
  - Descarga automática de archivos
- **Justificación:** Reportes imprimibles mejoran gestión

#### 3.2 Selector Timer vs Día (4-6 horas)
- **Backend:** ✅ Ya soporta ambos tipos
- **Frontend:**
  - Radio buttons o selector en `ServiceSaleForm.svelte`
  - "Timer" vs "Por Día"
  - Ajustar formulario según selección
- **Justificación:** Algunos servicios pueden ser por día completo

#### 3.3 Timer Delay 3 Minutos (4-6 horas)
- **Backend:**
  - Campo `start_delay_minutes` en creación de timer
  - Lógica para iniciar timer X minutos después de creación
- **Frontend:**
  - Checkbox "Iniciar timer 3 minutos después" en `ServiceSaleForm.svelte`
  - Mensaje informativo al usuario
- **Justificación:** Permite tiempo para preparar antes de iniciar timer

#### 3.4 Quantify Servicios (Cantidad) (4-6 horas)
- **Backend:** N/A (frontend only)
- **Frontend:**
  - Selector cantidad en `ServiceSelector.svelte`
  - Botones +/- para cantidad
  - Calcular precio total según cantidad × duración
- **Justificación:** Permite vender múltiples servicios iguales

#### 3.5 Vista Previa Paneles (12-16 horas)
- **Backend:**
  - Endpoint para generar preview de cada panel por rol
- **Frontend:**
  - Modal "Vista Previa" en gestión usuarios
  - Mostrar cómo se ve cada panel para cada rol
- **Justificación:** Admin puede verificar permisos visualmente

#### 3.6 Export Video Branding (20-24 horas)
- **Backend:**
  - Generación de video con branding para servicios/productos
  - Librería: `moviepy` o `ffmpeg-python`
- **Frontend:**
  - Botones "Exportar Video" en gestión servicios/productos
  - Preview de video antes de exportar
- **Justificación:** Videos para menús digitales (como cines/McDonalds)

**Total Sprint 3:** 52-78 horas (6.5-10 días)

---

## 📊 RESUMEN EJECUTIVO

### Estado Actual vs Requisitos

| Categoría | % Implementado | Gaps Críticos |
|-----------|----------------|---------------|
| **Super Admin** | ~70% | CRUD servicios/productos, paquetes, export |
| **Recepción** | ~65% | Iniciar/cerrar día UI, tickets, historial, extender timer |
| **Kidibar** | ~75% | Iniciar/cerrar día, estadísticas |
| **Monitor** | ~90% | Mejoras menores en alertas |

### Tiempo Total Estimado

- **Sprint 1 (BLOQUEADORES):** 44-56 horas (5.5-7 días)
- **Sprint 2 (CORE):** 42-56 horas (5.5-7 días)
- **Sprint 3 (ENHANCEMENTS):** 52-78 horas (6.5-10 días)

**Total Completo:** 138-190 horas (17-24 días)

**Mínimo Viable (Sprint 1):** 44-56 horas (5.5-7 días)

---

## 🎯 CONCLUSIÓN

### Gaps Críticos Identificados:

1. ❌ **Iniciar/Cerrar día UI** - 0% frontend
2. ❌ **Imprimir tickets** - 0% completo
3. ❌ **Historial ventas** - 0% completo
4. ⚠️ **CRUD servicios/productos** - 30% (solo GET/POST)
5. ⚠️ **Extender timer UI** - 50% (backend existe, falta UI)
6. ⚠️ **Alertas configurables** - 40% (backend existe, falta UI)
7. ❌ **Sistema paquetes** - 0% completo
8. ❌ **Formulario ticket completo** - 60% (faltan edad, firma)

### Prioridad de Implementación:

1. **Sprint 1 (BLOQUEADORES):** 5.5-7 días - Sistema operativo básico
2. **Sprint 2 (CORE):** 5.5-7 días - Sistema completamente funcional
3. **Sprint 3 (ENHANCEMENTS):** 6.5-10 días - Sistema completo con mejoras

### Recomendación:

**Implementar Sprint 1 primero** para tener sistema operativo, luego Sprint 2 para completar funcionalidades core, y finalmente Sprint 3 para mejoras.

---

**📄 Este análisis proporciona gaps exactos funcionalidad por funcionalidad y roadmap detallado con estimaciones precisas.**





























