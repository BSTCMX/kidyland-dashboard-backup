# ✅ CHECKLIST DE TESTING MANUAL

**Fecha:** 2025-01-XX  
**Funcionalidades:** FASE 2 (Alertas Timer) + FASE 3 (Sucursales)

---

## 🚀 PREPARACIÓN

- [ ] Backend corriendo en `http://localhost:8000`
- [ ] Frontend corriendo en `http://localhost:5173` (o puerto configurado)
- [ ] Usuario `super_admin` creado y funcional
- [ ] Usuario `recepcion` creado y funcional
- [ ] Al menos 1 sucursal creada en BD
- [ ] Al menos 1 servicio creado en BD

---

## 🧪 TESTING FASE 2: ALERTAS TIMER

### **1. Sistema de Notificaciones**

#### **1.1 Verificar Store de Notificaciones**
- [ ] Abrir consola del navegador (F12)
- [ ] Ejecutar en consola: `import { notify } from '$lib/stores/notifications'`
- [ ] Ejecutar: `notify.success('Test', 'Mensaje de prueba')`
- [ ] **Resultado esperado:** Toast notification aparece en top-right
- [ ] **Resultado esperado:** Toast desaparece después de 5 segundos
- [ ] Probar: `notify.error('Error', 'Mensaje de error')`
- [ ] **Resultado esperado:** Toast rojo con icono ❌
- [ ] Probar: `notify.warning('Advertencia', 'Mensaje')`
- [ ] **Resultado esperado:** Toast amarillo con icono ⚠️

#### **1.2 Verificar Componente ToastNotification**
- [ ] Navegar a cualquier página (ej: `/admin`)
- [ ] **Resultado esperado:** No hay toasts visibles (lista vacía)
- [ ] Hacer clic en botón "Actualizar" en dashboard
- [ ] **Resultado esperado:** Si hay error, toast de error aparece
- [ ] Si hay éxito, verificar que toast de éxito aparece

### **2. Integración con Alertas Timer**

#### **2.1 Crear Timer para Testing**
- [ ] Login como usuario `recepcion`
- [ ] Navegar a `/recepcion/venta`
- [ ] Crear venta de servicio:
  - Seleccionar servicio
  - Seleccionar duración (ej: 30 min)
  - Completar datos del niño
  - Completar pago
  - Confirmar venta
- [ ] **Resultado esperado:** Timer se crea correctamente
- [ ] **Resultado esperado:** Venta se registra correctamente

#### **2.2 Verificar Alertas en Tiempo Real**
- [ ] Navegar a `/recepcion/timers`
- [ ] **Resultado esperado:** Timer aparece en lista
- [ ] **Resultado esperado:** WebSocket muestra "🟢 Conectado"
- [ ] Esperar a que timer entre en rango de alerta (5/10/15 min)
- [ ] **Resultado esperado:** Toast notification aparece automáticamente
- [ ] **Resultado esperado:** Mensaje: "⚠️ Timer termina en X minutos"
- [ ] **Resultado esperado:** Timer card muestra badge de alerta
- [ ] **Resultado esperado:** Timer card tiene animación pulse
- [ ] **Resultado esperado:** Borde del card es amarillo

#### **2.3 Verificar Monitor de Timers**
- [ ] Login como usuario `monitor` (o cambiar rol temporalmente)
- [ ] Navegar a `/monitor/timers`
- [ ] **Resultado esperado:** Timers activos se muestran
- [ ] **Resultado esperado:** Alertas se muestran con badge
- [ ] **Resultado esperado:** Animación pulse funciona

### **3. Casos Especiales**

#### **3.1 Múltiples Alertas**
- [ ] Crear múltiples timers que entren en alerta simultáneamente
- [ ] **Resultado esperado:** Cada timer muestra su propia notificación
- [ ] **Resultado esperado:** No hay duplicación de notificaciones

#### **3.2 WebSocket Desconectado**
- [ ] Desconectar internet temporalmente
- [ ] **Resultado esperado:** WebSocket muestra "🔴 Desconectado"
- [ ] Reconectar internet
- [ ] **Resultado esperado:** WebSocket se reconecta automáticamente

---

## 🧪 TESTING FASE 3: GESTIÓN SUCURSALES

### **1. CRUD de Sucursales**

#### **1.1 Listar Sucursales**
- [ ] Login como `super_admin`
- [ ] Navegar a `/admin/sucursales`
- [ ] **Resultado esperado:** Lista de sucursales se carga
- [ ] **Resultado esperado:** Tabla muestra: Nombre, Dirección, Zona Horaria, Estado, Acciones
- [ ] **Resultado esperado:** Botón "➕ Crear Sucursal" visible

#### **1.2 Crear Sucursal**
- [ ] Hacer clic en "➕ Crear Sucursal"
- [ ] **Resultado esperado:** Modal se abre
- [ ] **Resultado esperado:** Título: "Crear Sucursal"
- [ ] Llenar formulario:
  - Nombre: "Sucursal Test"
  - Dirección: "Calle Test 123"
  - Zona Horaria: Seleccionar "Ciudad de México"
  - Activa: ✅ (marcado)
- [ ] Hacer clic en "Crear"
- [ ] **Resultado esperado:** Modal se cierra
- [ ] **Resultado esperado:** Toast notification: "Sucursal creada"
- [ ] **Resultado esperado:** Nueva sucursal aparece en lista

#### **1.3 Editar Sucursal**
- [ ] Hacer clic en "✏️ Editar" en una sucursal
- [ ] **Resultado esperado:** Modal se abre con datos prellenados
- [ ] **Resultado esperado:** Título: "Editar Sucursal"
- [ ] Modificar nombre: "Sucursal Test Editada"
- [ ] Hacer clic en "Actualizar"
- [ ] **Resultado esperado:** Modal se cierra
- [ ] **Resultado esperado:** Toast notification: "Sucursal actualizada"
- [ ] **Resultado esperado:** Cambios se reflejan en lista

#### **1.4 Eliminar Sucursal (Soft Delete)**
- [ ] Hacer clic en "🗑️ Eliminar" en una sucursal activa
- [ ] **Resultado esperado:** Modal de confirmación aparece
- [ ] **Resultado esperado:** Mensaje: "¿Estás seguro de que deseas desactivar la sucursal..."
- [ ] Hacer clic en "Eliminar"
- [ ] **Resultado esperado:** Modal se cierra
- [ ] **Resultado esperado:** Sucursal desaparece de lista (o muestra como inactiva)
- [ ] **Nota:** Verificar en BD que `active = False` (soft delete)

#### **1.5 Validaciones**
- [ ] Intentar crear sucursal sin nombre
- [ ] **Resultado esperado:** Error: "Nombre es requerido"
- [ ] Intentar crear sucursal con nombre > 100 caracteres
- [ ] **Resultado esperado:** Error: "El nombre no puede exceder 100 caracteres"
- [ ] Intentar crear sucursal con dirección > 255 caracteres
- [ ] **Resultado esperado:** Error: "La dirección no puede exceder 255 caracteres"

### **2. Selector de Sucursal en Dashboard**

#### **2.1 Verificar Selector**
- [ ] Navegar a `/admin` (dashboard)
- [ ] **Resultado esperado:** Selector "Filtrar por Sucursal" visible en header
- [ ] **Resultado esperado:** Selector muestra "Todas las sucursales" por defecto
- [ ] **Resultado esperado:** Dropdown lista todas las sucursales activas

#### **2.2 Filtrar Métricas**
- [ ] Seleccionar una sucursal específica del dropdown
- [ ] **Resultado esperado:** Selección se guarda en localStorage
- [ ] Hacer clic en "🔄 Actualizar"
- [ ] **Resultado esperado:** Métricas se actualizan para sucursal seleccionada
- [ ] **Resultado esperado:** Export buttons usan sucursal seleccionada
- [ ] Recargar página
- [ ] **Resultado esperado:** Selección se mantiene (desde localStorage)

#### **2.3 Valor por Defecto**
- [ ] Limpiar localStorage: `localStorage.removeItem('admin_selected_sucursal_id')`
- [ ] Recargar página
- [ ] **Resultado esperado:** Selector muestra sucursal del usuario actual (si tiene)

### **3. Permisos y Seguridad**

#### **3.1 Permisos de Usuario**
- [ ] Login como `admin_viewer`
- [ ] Intentar navegar a `/admin/sucursales`
- [ ] **Resultado esperado:** Redirige a `/admin-viewer` (solo lectura)
- [ ] Login como `recepcion`
- [ ] Intentar navegar a `/admin/sucursales`
- [ ] **Resultado esperado:** Redirige a `/recepcion` (sin acceso)

#### **3.2 Backend Security**
- [ ] Intentar crear sucursal como `admin_viewer` (usando API directamente)
- [ ] **Resultado esperado:** 403 Forbidden
- [ ] Intentar actualizar sucursal como `recepcion`
- [ ] **Resultado esperado:** 403 Forbidden

---

## 🔍 VERIFICACIÓN DE INTEGRACIÓN

### **1. Verificar que Todo Funciona Junto**
- [ ] Crear sucursal nueva
- [ ] Crear usuario asignado a esa sucursal
- [ ] Login como ese usuario
- [ ] Crear venta de servicio
- [ ] Verificar que timer se crea correctamente
- [ ] Verificar que alertas funcionan
- [ ] **Resultado esperado:** Todo funciona sin conflictos

### **2. Verificar Performance**
- [ ] Abrir DevTools → Network
- [ ] Navegar entre páginas
- [ ] **Resultado esperado:** No hay requests innecesarios
- [ ] **Resultado esperado:** WebSocket se mantiene conectado
- [ ] **Resultado esperado:** No hay memory leaks (verificar Memory tab)

### **3. Verificar Responsive**
- [ ] Abrir en móvil (o DevTools mobile view)
- [ ] Navegar a `/admin/sucursales`
- [ ] **Resultado esperado:** Tabla es responsive (scroll horizontal si necesario)
- [ ] **Resultado esperado:** Formularios son mobile-friendly
- [ ] **Resultado esperado:** Botones tienen tamaño mínimo 48px
- [ ] **Resultado esperado:** Toast notifications se adaptan a pantalla pequeña

---

## 📝 REGISTRO DE ISSUES

### **Issues Encontrados:**

1. **Issue #1:**
   - Descripción: 
   - Pasos para reproducir:
   - Resultado esperado:
   - Resultado actual:
   - Severidad: [Alta/Media/Baja]

2. **Issue #2:**
   - Descripción:
   - Pasos para reproducir:
   - Resultado esperado:
   - Resultado actual:
   - Severidad: [Alta/Media/Baja]

---

## ✅ RESUMEN FINAL

### **FASE 2: Alertas Timer**
- [ ] Sistema de notificaciones: ✅ / ❌
- [ ] Integración con timers: ✅ / ❌
- [ ] Visualización mejorada: ✅ / ❌

### **FASE 3: Sucursales**
- [ ] CRUD completo: ✅ / ❌
- [ ] Selector en dashboard: ✅ / ❌
- [ ] Permisos correctos: ✅ / ❌

### **General**
- [ ] Sin errores en consola: ✅ / ❌
- [ ] Responsive funciona: ✅ / ❌
- [ ] Performance aceptable: ✅ / ❌

---

**Tester:** _______________  
**Fecha:** _______________  
**Comentarios:** _______________





























