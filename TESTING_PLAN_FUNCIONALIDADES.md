# 🧪 PLAN DE TESTING - FUNCIONALIDADES IMPLEMENTADAS

**Fecha:** 2025-01-XX  
**Objetivo:** Validar funcionalidades implementadas en FASE 2 y FASE 3

---

## 📋 RESUMEN DE FUNCIONALIDADES A TESTEAR

### ✅ **FASE 2: Alertas Timer**
1. Sistema de notificaciones global
2. Integración con alertas timer
3. Visualización mejorada de alertas

### ✅ **FASE 3: Gestión Sucursales**
1. CRUD completo de sucursales
2. Selector de sucursal en dashboard

---

## 🧪 TESTING FASE 2: ALERTAS TIMER

### **1. Sistema de Notificaciones Global**

#### **1.1 Store de Notificaciones (`notifications.ts`)**
- [ ] **Test:** Verificar que el store se inicializa correctamente
  - Estado inicial debe tener `list: []`
- [ ] **Test:** Agregar notificación
  - `addNotification()` debe crear ID único
  - Notificación debe aparecer en `list`
  - Auto-dismiss debe funcionar después de `duration`
- [ ] **Test:** Remover notificación
  - `removeNotification(id)` debe eliminar la notificación correcta
- [ ] **Test:** Helper functions (`notify.success`, `notify.error`, etc.)
  - Cada tipo debe crear notificación con tipo correcto
  - Duración por defecto debe ser correcta

#### **1.2 Componente ToastNotification**
- [ ] **Test:** Renderizado básico
  - Debe mostrar cuando hay notificaciones
  - No debe mostrar cuando `list` está vacío
- [ ] **Test:** Tipos de notificación
  - Success: icono ✅, color verde
  - Error: icono ❌, color rojo
  - Warning: icono ⚠️, color amarillo
  - Info: icono ℹ️, color azul
- [ ] **Test:** Auto-dismiss
  - Notificación debe desaparecer después de `duration`
  - Notificaciones persistentes no deben auto-dismiss
- [ ] **Test:** Cerrar manualmente
  - Botón "✕" debe cerrar la notificación
- [ ] **Test:** Responsive
  - Debe adaptarse a pantallas móviles
  - Container debe ajustarse en mobile

#### **1.3 Integración en Layout**
- [ ] **Test:** Componente en `+layout.svelte`
  - `ToastNotification` debe estar importado
  - Debe renderizarse en todas las páginas
  - Debe estar en posición fixed (top-right)

### **2. Integración con Alertas Timer**

#### **2.1 Store Timers (`timers.ts`)**
- [ ] **Test:** WebSocket connection
  - `connectTimerWebSocket()` debe crear conexión
  - `disconnectTimerWebSocket()` debe cerrar conexión
- [ ] **Test:** Recepción de mensajes WebSocket
  - Mensaje `timers_update` debe actualizar lista
  - Mensaje `timer_alert` debe detectar nuevas alertas
- [ ] **Test:** Detección de nuevas alertas
  - Debe comparar con `previousAlertTimers`
  - Solo debe notificar alertas nuevas (no duplicadas)
- [ ] **Test:** Notificaciones de alertas
  - Debe mostrar notificación cuando timer entra en rango de alerta
  - Debe indicar minutos restantes (5, 10, 15 min)
  - Debe incluir nombre del niño si está disponible

#### **2.2 Componentes de Timers**

##### **2.2.1 Recepción Timers (`/recepcion/timers`)**
- [ ] **Test:** Visualización de alertas
  - Timer con status `alert` debe mostrar badge
  - Badge debe mostrar minutos restantes
  - Card debe tener animación pulse
  - Card debe tener borde amarillo
- [ ] **Test:** WebSocket updates
  - Cambios en timers deben reflejarse en tiempo real
  - Alertas deben aparecer automáticamente

##### **2.2.2 Monitor Timers (`/monitor/timers`)**
- [ ] **Test:** Visualización de alertas
  - Timer con status `alert` debe mostrar badge
  - Card debe tener animación pulse
- [ ] **Test:** WebSocket updates
  - Cambios en timers deben reflejarse en tiempo real

### **3. Flujo Completo de Alertas**

#### **3.1 Escenario: Timer entra en rango de alerta**
1. [ ] Timer activo con 6 minutos restantes
2. [ ] Backend detecta que está en rango de alerta (5 min)
3. [ ] Backend envía mensaje WebSocket `timer_alert`
4. [ ] Frontend recibe mensaje
5. [ ] Frontend detecta que es nueva alerta
6. [ ] Frontend muestra notificación toast: "⚠️ Timer termina en 5 minutos"
7. [ ] Timer card muestra badge de alerta
8. [ ] Timer card tiene animación pulse

#### **3.2 Escenario: Múltiples alertas**
1. [ ] Múltiples timers entran en rango de alerta
2. [ ] Cada uno debe mostrar notificación individual
3. [ ] No debe duplicar notificaciones para el mismo timer

#### **3.3 Escenario: Alertas 5/10/15 minutos**
1. [ ] Timer con 16 min restantes → No alerta
2. [ ] Timer con 15 min restantes → Alerta "15 minutos"
3. [ ] Timer con 10 min restantes → Alerta "10 minutos"
4. [ ] Timer con 5 min restantes → Alerta "5 minutos"

---

## 🧪 TESTING FASE 3: GESTIÓN SUCURSALES

### **1. Backend Endpoints**

#### **1.1 PUT /sucursales/{id}**
- [ ] **Test:** Actualizar sucursal existente
  - Debe actualizar campos proporcionados
  - Debe retornar sucursal actualizada
- [ ] **Test:** Validación
  - Sucursal no encontrada → 404
  - Solo `super_admin` puede actualizar
- [ ] **Test:** Campos opcionales
  - Debe permitir actualizar solo algunos campos
  - Campos no proporcionados no deben cambiar

#### **1.2 DELETE /sucursales/{id}**
- [ ] **Test:** Soft delete
  - Debe establecer `active = False`
  - No debe eliminar físicamente
- [ ] **Test:** Validación
  - Sucursal no encontrada → 404
  - Solo `super_admin` puede eliminar

### **2. Frontend Store (`sucursales-admin.ts`)**

#### **2.1 Funciones CRUD**
- [ ] **Test:** `fetchAllSucursales()`
  - Debe cargar todas las sucursales
  - Debe actualizar `list` en store
  - Debe manejar errores correctamente
- [ ] **Test:** `createSucursal()`
  - Debe crear nueva sucursal
  - Debe agregar a `list`
  - Debe retornar sucursal creada
- [ ] **Test:** `updateSucursal()`
  - Debe actualizar sucursal existente
  - Debe actualizar en `list`
  - Debe retornar sucursal actualizada
- [ ] **Test:** `deleteSucursal()`
  - Debe eliminar de `list`
  - Debe retornar `true` si exitoso

### **3. Componentes Frontend**

#### **3.1 SucursalList.svelte**
- [ ] **Test:** Renderizado básico
  - Debe mostrar tabla con sucursales
  - Debe mostrar loading state
  - Debe mostrar empty state si no hay sucursales
- [ ] **Test:** Columnas de tabla
  - Nombre, Dirección, Zona Horaria, Estado, Acciones
- [ ] **Test:** Botones de acción
  - "Crear Sucursal" solo visible para `super_admin`
  - "Editar" solo visible para `super_admin`
  - "Eliminar" solo visible para `super_admin` y solo si activa
- [ ] **Test:** Modal de confirmación
  - Debe aparecer al hacer clic en "Eliminar"
  - Debe mostrar nombre de sucursal
  - Debe confirmar soft delete

#### **3.2 SucursalForm.svelte**
- [ ] **Test:** Modo creación
  - Formulario debe estar vacío
  - Título: "Crear Sucursal"
- [ ] **Test:** Modo edición
  - Formulario debe estar prellenado
  - Título: "Editar Sucursal"
- [ ] **Test:** Campos del formulario
  - Nombre (requerido, max 100 caracteres)
  - Dirección (opcional, max 255 caracteres)
  - Zona Horaria (selector con opciones de México)
  - Activa (checkbox)
- [ ] **Test:** Validación
  - Nombre vacío → error
  - Nombre > 100 caracteres → error
  - Dirección > 255 caracteres → error
- [ ] **Test:** Submit
  - Crear: debe llamar `createSucursal()`
  - Editar: debe llamar `updateSucursal()`
  - Debe emitir evento `success` al completar
  - Debe cerrar modal al completar

#### **3.3 SucursalSelector.svelte**
- [ ] **Test:** Renderizado
  - Solo visible para `super_admin`
  - Debe mostrar dropdown con sucursales activas
- [ ] **Test:** Opciones
  - "Todas las sucursales" (valor vacío)
  - Lista de sucursales activas
- [ ] **Test:** Selección
  - Debe emitir `onSelect` al cambiar
  - Debe guardar en localStorage
  - Debe cargar desde localStorage al montar
- [ ] **Test:** Valor por defecto
  - Debe usar sucursal del usuario actual si disponible
  - Debe usar valor de localStorage si existe

### **4. Integración en Dashboard**

#### **4.1 Admin Dashboard (`/admin`)**
- [ ] **Test:** Selector de sucursal
  - Debe aparecer en header
  - Debe estar antes de botones de export
- [ ] **Test:** Filtrado de métricas
  - Al seleccionar sucursal, métricas deben filtrarse
  - Export buttons deben usar sucursal seleccionada
  - Refresh button debe usar sucursal seleccionada

#### **4.2 Navegación**
- [ ] **Test:** Ruta `/admin/sucursales`
  - Debe estar en menú de navegación
  - Debe mostrar `SucursalList`
  - Debe estar protegida (solo `super_admin`)

---

## 🔍 CHECKLIST DE VALIDACIÓN TÉCNICA

### **Arquitectura y Código**
- [ ] **Clean Architecture:** Separación de capas respetada
- [ ] **Modularidad:** Componentes reutilizables
- [ ] **Type Safety:** TypeScript sin errores
- [ ] **Sin Hardcodeo:** Todo dinámico desde backend
- [ ] **Responsive:** Mobile-first, touch targets 48px+
- [ ] **Error Handling:** Manejo de errores en todos los casos

### **Integración**
- [ ] **Stores:** Todos los stores funcionan correctamente
- [ ] **Componentes:** Todos los componentes se importan sin errores
- [ ] **Rutas:** Todas las rutas están protegidas correctamente
- [ ] **WebSocket:** Conexión y desconexión funcionan
- [ ] **API:** Todos los endpoints funcionan correctamente

### **UX/UI**
- [ ] **Notificaciones:** Aparecen y desaparecen correctamente
- [ ] **Loading States:** Se muestran durante cargas
- [ ] **Error States:** Se muestran mensajes de error claros
- [ ] **Empty States:** Se muestran cuando no hay datos
- [ ] **Animaciones:** Funcionan sin afectar performance

---

## 🚀 PROCEDIMIENTO DE TESTING

### **Paso 1: Preparación**
1. Verificar que backend está corriendo
2. Verificar que frontend está corriendo
3. Tener usuario `super_admin` listo para login
4. Tener datos de prueba (sucursales, timers activos)

### **Paso 2: Testing FASE 2 (Alertas Timer)**
1. Login como usuario con rol `recepcion`
2. Crear venta de servicio que genere timer
3. Esperar a que timer entre en rango de alerta
4. Verificar notificaciones y visualización

### **Paso 3: Testing FASE 3 (Sucursales)**
1. Login como `super_admin`
2. Navegar a `/admin/sucursales`
3. Probar CRUD completo
4. Verificar selector en dashboard

### **Paso 4: Testing de Integración**
1. Verificar que todas las funcionalidades trabajan juntas
2. Verificar que no hay conflictos
3. Verificar performance

---

## 📝 REPORTE DE TESTING

### **Resultados Esperados**
- ✅ Todas las funcionalidades funcionan correctamente
- ✅ No hay errores en consola
- ✅ No hay errores de TypeScript
- ✅ UX es fluida y responsive
- ✅ Integración con backend funciona

### **Issues Encontrados**
- [ ] Issue 1: [Descripción]
- [ ] Issue 2: [Descripción]
- [ ] Issue 3: [Descripción]

---

## ✅ CRITERIOS DE ACEPTACIÓN

### **FASE 2: Alertas Timer**
- [x] Sistema de notificaciones funciona globalmente
- [x] Alertas timer muestran notificaciones correctamente
- [x] Visualización de alertas es clara y visible
- [x] No hay duplicación de notificaciones

### **FASE 3: Sucursales**
- [x] CRUD completo funciona correctamente
- [x] Selector de sucursal funciona en dashboard
- [x] Filtrado de métricas funciona
- [x] Permisos están correctamente implementados

---

**Nota:** Este documento debe actualizarse con los resultados reales del testing.





























