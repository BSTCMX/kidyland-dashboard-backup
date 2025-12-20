# 🧪 TESTING MANUAL - PASO 3: FORMULARIO VENTA RECEPCIÓN

**Fecha:** 2025-01-XX  
**Objetivo:** Validar flujo completo de registro de venta de servicio

---

## 📋 CHECKLIST DE TESTING

### ✅ 1. NAVEGACIÓN

#### 1.1 Acceso a Formulario de Venta
- [ ] Login como usuario `recepcion`
- [ ] Navegar a página principal de recepción
- [ ] Verificar botón "➕ Nueva Venta" visible
- [ ] Click en "Nueva Venta"
- [ ] Verificar que navega a `/venta`
- [ ] Verificar que se muestra formulario de venta

#### 1.2 Navegación entre Steps
- [ ] Verificar indicador de pasos (1, 2, 3)
- [ ] Verificar que paso 1 está activo inicialmente
- [ ] Completar paso 1 y click "Siguiente"
- [ ] Verificar que avanza a paso 2
- [ ] Click "Anterior" en paso 2
- [ ] Verificar que regresa a paso 1

---

### ✅ 2. PASO 1: SELECCIÓN DE SERVICIO

#### 2.1 Cargar Servicios
- [ ] Verificar que servicios se cargan automáticamente al montar componente
- [ ] Verificar que solo se muestran servicios activos
- [ ] Verificar que dropdown muestra nombres de servicios

#### 2.2 Seleccionar Servicio
- [ ] Seleccionar un servicio del dropdown
- [ ] Verificar que se muestra selector de duración
- [ ] Verificar que duraciones disponibles son correctas
- [ ] Seleccionar una duración
- [ ] Verificar que se muestra precio calculado
- [ ] Verificar que precio es correcto según duración

#### 2.3 Validaciones Paso 1
- [ ] Intentar avanzar sin seleccionar servicio → Botón deshabilitado
- [ ] Seleccionar servicio pero no duración → Botón deshabilitado
- [ ] Seleccionar servicio y duración → Botón habilitado

---

### ✅ 3. PASO 2: INFORMACIÓN DEL CLIENTE

#### 3.1 Campos del Formulario
- [ ] Verificar campo "Nombre del Niño" (requerido)
- [ ] Verificar campo "Nombre del Pagador" (requerido)
- [ ] Verificar campo "Teléfono" (opcional)
- [ ] Verificar campo "Descuento" (opcional)

#### 3.2 Ingresar Datos
- [ ] Ingresar nombre del niño: "Juan Pérez"
- [ ] Ingresar nombre del pagador: "María Pérez"
- [ ] Ingresar teléfono: "555-1234"
- [ ] Ingresar descuento: "5.00"
- [ ] Verificar que total se actualiza con descuento

#### 3.3 Validaciones Paso 2
- [ ] Intentar avanzar sin nombre del niño → Botón deshabilitado
- [ ] Ingresar solo nombre del niño → Botón deshabilitado
- [ ] Ingresar nombre del niño y pagador → Botón habilitado
- [ ] Verificar que teléfono es opcional

---

### ✅ 4. PASO 3: MÉTODO DE PAGO

#### 4.1 Pago en Efectivo
- [ ] Seleccionar "Efectivo" como método de pago
- [ ] Verificar que se muestra campo "Efectivo Recibido"
- [ ] Verificar que NO se muestra campo "Código de Autorización"
- [ ] Ingresar efectivo recibido menor al total → Verificar mensaje "Faltan $X"
- [ ] Ingresar efectivo recibido igual al total → Verificar cambio = $0.00
- [ ] Ingresar efectivo recibido mayor al total → Verificar cambio calculado

#### 4.2 Pago con Tarjeta
- [ ] Seleccionar "Tarjeta" como método de pago
- [ ] Verificar que se muestra campo "Código de Autorización"
- [ ] Verificar que NO se muestra campo "Efectivo Recibido"
- [ ] Ingresar código de autorización
- [ ] Verificar que botón "Confirmar Venta" está habilitado

#### 4.3 Pago Mixto
- [ ] Seleccionar "Mixto" como método de pago
- [ ] Verificar que se muestran AMBOS campos (efectivo y código)
- [ ] Ingresar efectivo parcial
- [ ] Ingresar código de autorización
- [ ] Verificar que botón está habilitado

#### 4.4 Validaciones Paso 3
- [ ] Efectivo: Sin monto ingresado → Botón deshabilitado
- [ ] Efectivo: Monto menor al total → Botón deshabilitado
- [ ] Efectivo: Monto igual o mayor → Botón habilitado
- [ ] Tarjeta: Sin código → Botón deshabilitado
- [ ] Tarjeta: Con código → Botón habilitado
- [ ] Mixto: Al menos uno completado → Botón habilitado

---

### ✅ 5. CONFIRMACIÓN Y CREACIÓN DE VENTA

#### 5.1 Procesar Venta
- [ ] Completar todos los pasos
- [ ] Click en "Confirmar Venta"
- [ ] Verificar que botón muestra "Procesando..." durante carga
- [ ] Verificar que se muestra paso 4 (confirmación)

#### 5.2 Confirmación Exitosa
- [ ] Verificar mensaje "¡Venta Registrada Exitosamente!"
- [ ] Verificar que se muestra ID de venta
- [ ] Verificar que se muestra ID de timer (si se creó)
- [ ] Verificar que se muestra total pagado
- [ ] Verificar botón "Nueva Venta"

#### 5.3 Verificar Timer Creado
- [ ] Volver a página principal de recepción
- [ ] Verificar que timer aparece en lista de timers activos
- [ ] Verificar que nombre del niño es correcto
- [ ] Verificar que tiempo restante es correcto
- [ ] Verificar que WebSocket actualiza timer en tiempo real

---

### ✅ 6. MANEJO DE ERRORES

#### 6.1 Errores de API
- [ ] Simular error de red (desconectar internet)
- [ ] Intentar crear venta
- [ ] Verificar que se muestra mensaje de error
- [ ] Verificar que formulario no se resetea
- [ ] Verificar que se puede reintentar

#### 6.2 Errores de Validación
- [ ] Intentar crear venta sin sucursal asignada
- [ ] Verificar mensaje de error apropiado
- [ ] Verificar que no se envía request al backend

#### 6.3 Errores de Backend
- [ ] Crear venta con servicio inexistente (si es posible)
- [ ] Verificar que backend retorna error
- [ ] Verificar que frontend muestra error
- [ ] Verificar que formulario se mantiene con datos ingresados

---

### ✅ 7. RESPONSIVE Y UX

#### 7.1 Mobile (< 768px)
- [ ] Abrir en viewport mobile
- [ ] Verificar que formulario es usable
- [ ] Verificar que botones son touch-friendly (min 48px)
- [ ] Verificar que campos son legibles
- [ ] Verificar que indicador de pasos se adapta

#### 7.2 Tablet (768px - 1023px)
- [ ] Abrir en viewport tablet
- [ ] Verificar que layout es funcional
- [ ] Verificar que formulario se ve bien

#### 7.3 Desktop (> 1024px)
- [ ] Abrir en viewport desktop
- [ ] Verificar que formulario está centrado
- [ ] Verificar que ancho máximo es apropiado

---

### ✅ 8. INTEGRACIÓN CON BACKEND

#### 8.1 Request a POST /sales
- [ ] Abrir DevTools → Network
- [ ] Crear una venta completa
- [ ] Verificar que se envía POST a `/sales`
- [ ] Verificar payload correcto:
  - `tipo: "service"`
  - `sucursal_id` correcto
  - `usuario_id` correcto
  - `items` con servicio y duración
  - `payer_name` y `payer_phone`
  - `payment_method` correcto
  - `total_cents` calculado correctamente

#### 8.2 Response del Backend
- [ ] Verificar que response incluye `sale_id`
- [ ] Verificar que response incluye `timer_id` (si es servicio)
- [ ] Verificar que response incluye `sale` completo
- [ ] Verificar que response incluye `timer` (si se creó)

#### 8.3 Integración con Timers
- [ ] Verificar que timer se crea automáticamente
- [ ] Verificar que timer tiene `child_name` correcto
- [ ] Verificar que timer tiene `start_at` y `end_at` correctos
- [ ] Verificar que timer tiene `status: "active"`

---

## 🐛 ISSUES ENCONTRADOS

### (Documentar aquí cualquier issue encontrado)

1. **Issue 1:** [Descripción]
   - **Severidad:** Alta/Media/Baja
   - **Reproducción:** [Pasos]
   - **Fix:** [Solución]

---

## ✅ CONCLUSIÓN

- [ ] Todos los flujos críticos probados
- [ ] Todos los tests pasan
- [ ] Issues documentados
- [ ] Fixes aplicados
- [ ] Integración con backend verificada
- [ ] Timer se crea correctamente
- [ ] Responsive funciona en todos los viewports

**Estado:** ⏳ **PENDIENTE DE EJECUTAR**

---

**📄 Este checklist debe completarse manualmente probando la aplicación en el navegador.**





























