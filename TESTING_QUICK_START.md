# 🚀 QUICK START - TESTING RÁPIDO

**Guía rápida para validar funcionalidades implementadas**

---

## ⚡ TESTING RÁPIDO (5 minutos)

### **1. Verificar Sistema de Notificaciones (1 min)**
1. Abrir consola del navegador (F12)
2. Ejecutar:
```javascript
import { notify } from '$lib/stores/notifications';
notify.success('Test', 'Sistema de notificaciones funciona');
```
3. ✅ **Esperado:** Toast verde aparece en top-right y desaparece en 5 segundos

### **2. Verificar CRUD Sucursales (2 min)**
1. Login como `super_admin`
2. Navegar a `/admin/sucursales`
3. ✅ **Esperado:** Lista de sucursales se carga
4. Hacer clic en "➕ Crear Sucursal"
5. Llenar formulario y crear
6. ✅ **Esperado:** Toast "Sucursal creada" + sucursal aparece en lista

### **3. Verificar Selector en Dashboard (1 min)**
1. Navegar a `/admin`
2. ✅ **Esperado:** Selector "Filtrar por Sucursal" visible en header
3. Seleccionar sucursal del dropdown
4. ✅ **Esperado:** Selección se mantiene al recargar (localStorage)

### **4. Verificar Alertas Timer (1 min)**
1. Login como `recepcion`
2. Crear venta de servicio (genera timer)
3. Navegar a `/recepcion/timers`
4. ✅ **Esperado:** Timer aparece + WebSocket "🟢 Conectado"
5. **Nota:** Para probar alertas, necesitas esperar o modificar timer en BD

---

## 🔍 VERIFICACIÓN DE CÓDIGO

### **Imports Correctos:**
- ✅ `timers.ts`: `createTimerWebSocket` desde `@kidyland/utils/websocket`
- ✅ `timers.ts`: `notify` desde `./notifications`
- ✅ `+layout.svelte`: `ToastNotification` importado
- ✅ `sucursales-admin.ts`: Tipos desde `@kidyland/shared/types`

### **Archivos Creados:**
- ✅ `notifications.ts` - Store de notificaciones
- ✅ `ToastNotification.svelte` - Componente toast
- ✅ `sucursales-admin.ts` - Store CRUD sucursales
- ✅ `SucursalList.svelte` - Lista de sucursales
- ✅ `SucursalForm.svelte` - Formulario crear/editar
- ✅ `SucursalSelector.svelte` - Selector para dashboard

### **Backend Endpoints:**
- ✅ `PUT /sucursales/{id}` - Actualizar sucursal
- ✅ `DELETE /sucursales/{id}` - Soft delete sucursal

---

## 📋 CHECKLIST RÁPIDO

- [ ] Backend corriendo
- [ ] Frontend corriendo
- [ ] Login como `super_admin` funciona
- [ ] Ruta `/admin/sucursales` accesible
- [ ] CRUD sucursales funciona
- [ ] Selector en dashboard funciona
- [ ] Notificaciones aparecen
- [ ] Sin errores en consola

---

## 🐛 ISSUES COMUNES

### **Error: "createTimerWebSocket is not defined"**
- **Solución:** Verificar que import es: `import { createTimerWebSocket } from "@kidyland/utils/websocket"`

### **Error: "notify is not defined"**
- **Solución:** Verificar que import es: `import { notify } from "./notifications"`

### **ToastNotification no aparece**
- **Solución:** Verificar que está en `+layout.svelte` y no en layout específico

### **Selector no muestra sucursales**
- **Solución:** Verificar que usuario tiene permisos `super_admin`

---

**✅ Si todos los checks pasan, las funcionalidades están listas para uso en producción.**





























