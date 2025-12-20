# 🗺️ MAPEO ARQUITECTÓNICO COMPLETO - ESTADO ACTUAL POST FASE 2

**Fecha:** 2025-01-XX  
**Objetivo:** Documentar exactamente la estructura actual del proyecto después de FASE 2

---

## 📁 ESTRUCTURA DE CARPETAS REAL

### Apps Existentes

```
apps/
├── admin/          ✅ EXISTE - App separada completa
├── web/            ✅ EXISTE - App consolidada (FASE 2)
├── reception/      ✅ EXISTE - App separada (NO migrada completamente)
├── kidibar/        ✅ EXISTE - App separada (NO migrada completamente)
└── monitor/        ✅ EXISTE - App separada (NO migrada completamente)
```

### Estado de Migración

**✅ COMPLETAMENTE MIGRADO:**
- `apps/web/` - Nueva app consolidada con recepcion, kidibar, monitor

**❌ NO MIGRADO (Siguen existiendo):**
- `apps/reception/` - App original sigue existiendo
- `apps/kidibar/` - App original sigue existiendo
- `apps/monitor/` - App original sigue existiendo

**✅ NO TOCADO (Como solicitado):**
- `apps/admin/` - App completa e independiente

---

## 🎯 APPS/WEB - ESTRUCTURA DE ROUTES

### Routes Existentes en `apps/web/src/routes/`

```
apps/web/src/routes/
├── +layout.svelte          ✅ Root layout con role-based routing
├── +page.svelte            ✅ Login page
├── admin/                  ✅ Existe (placeholder)
│   └── +page.svelte
├── admin-viewer/           ✅ Existe (placeholder)
│   └── +page.svelte
├── recepcion/              ✅ Existe (migrado de apps/reception)
│   ├── +page.svelte
│   ├── venta/
│   │   └── +page.svelte
│   └── timers/
│       └── +page.svelte
├── kidibar/                ✅ Existe (migrado de apps/kidibar)
│   ├── +page.svelte
│   ├── venta/
│   │   └── +page.svelte
│   └── inventario/
│       └── +page.svelte
└── monitor/                ✅ Existe (migrado de apps/monitor)
    ├── +page.svelte
    └── timers/
        └── +page.svelte
```

---

## 🔐 LOGIN FLOW Y ROUTING

### Role-Based Routing (apps/web)

**Definido en:** `apps/web/src/lib/types.ts`

```typescript
export const ROLE_ROUTES: Record<UserRole, string> = {
  super_admin: "/admin",
  admin_viewer: "/admin-viewer",
  recepcion: "/recepcion",
  kidibar: "/kidibar",
  monitor: "/monitor",
};
```

### Login Flow Actual

1. **Usuario hace login** → `POST /auth/login`
2. **Backend retorna** → `{ access_token, user: { role, ... } }`
3. **Auth store redirige** → Según `ROLE_ROUTES[user.role]`

**Redirecciones por Rol:**
- `super_admin` → `/admin` (en apps/web)
- `admin_viewer` → `/admin-viewer` (en apps/web)
- `recepcion` → `/recepcion` (en apps/web)
- `kidibar` → `/kidibar` (en apps/web)
- `monitor` → `/monitor` (en apps/web)

### ⚠️ PROBLEMA IDENTIFICADO

**Super_admin y Admin_viewer están siendo redirigidos a `apps/web`**, pero:
- `apps/web/routes/admin/` es solo un **placeholder**
- `apps/web/routes/admin-viewer/` es solo un **placeholder**
- La funcionalidad real está en `apps/admin/`

---

## 🏗️ ADMIN-VIEWER IMPLEMENTACIÓN

### Estado Actual

**❌ NO ESTÁ IMPLEMENTADO EN apps/web**

**✅ EXISTE EN apps/admin**

`apps/admin/` tiene:
- Dashboard completo
- Gestión de usuarios (CRUD)
- Gestión de servicios/productos
- Reportes y métricas
- **Permisos diferenciados** por rol (super_admin vs admin_viewer)

### Cómo Funciona Admin-Viewer en apps/admin

1. **Login en apps/admin** → Usuario con rol `admin_viewer`
2. **Backend valida permisos** → Solo lectura en todos los endpoints
3. **Frontend oculta botones** → Edit/Create/Delete no visibles
4. **Misma UI que super_admin** → Pero sin acciones de escritura

### ⚠️ INCONSISTENCIA ARQUITECTÓNICA

- `apps/web` redirige `super_admin` y `admin_viewer` a rutas que son placeholders
- `apps/admin` tiene la funcionalidad real pero no está conectado al routing de `apps/web`

---

## 🧭 NAVEGACIÓN CROSS-MODULE

### En apps/web

**✅ NavigationSidebar.svelte** implementado:
- Muestra módulos según permisos del usuario
- Indicadores visuales de readonly
- Navegación fluida entre módulos

**Permisos Cross-Module:**
- `recepcion` → Puede ver `kidibar` (readonly)
- `monitor` → Puede ver `recepcion` + `kidibar` (readonly)
- `super_admin` → Puede ver todo (full access)
- `admin_viewer` → Puede ver todo (readonly)

### En apps/admin

**❌ NO HAY NAVEGACIÓN CROSS-MODULE**

`apps/admin` es una app completamente separada:
- No tiene sidebar para ir a recepcion/kidibar/monitor
- Es una app independiente con su propio routing
- No está conectada con `apps/web`

---

## 📦 PACKAGE.JSON - DEPLOYMENT STRUCTURE

### Apps con package.json

```
apps/
├── admin/package.json       ✅ Existe - Deploy separado
├── web/package.json         ✅ Existe - Deploy separado
├── reception/package.json   ✅ Existe - Deploy separado (legacy)
├── kidibar/package.json     ✅ Existe - Deploy separado (legacy)
└── monitor/package.json     ✅ Existe - Deploy separado (legacy)
```

### Estado de Deployment

**ACTUALMENTE:**
- 5 apps separadas = 5 deploys potenciales
- `apps/admin` → Deploy independiente
- `apps/web` → Deploy independiente (nuevo)
- `apps/reception`, `apps/kidibar`, `apps/monitor` → Legacy (no se usan)

**OBJETIVO (Single Deploy):**
- 1 app consolidada = 1 deploy
- `apps/web` con todas las rutas

---

## 🗺️ DIAGRAMA ARQUITECTÓNICO ACTUAL

```
┌─────────────────────────────────────────────────────────────┐
│                    KIDYLAND MONOREPO                        │
└─────────────────────────────────────────────────────────────┘

┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│   apps/admin/    │  │    apps/web/    │  │  apps/reception/ │
│                  │  │                  │  │  (LEGACY)        │
│ ✅ Funcional     │  │ ✅ Nuevo (FASE2)│  │ ❌ No usado      │
│ ✅ Completo      │  │ ✅ Consolidado   │  │                  │
│ ✅ Independiente │  │ ✅ Recepcion     │  └──────────────────┘
│                  │  │ ✅ Kidibar       │
│ Routes:          │  │ ✅ Monitor      │  ┌──────────────────┐
│ - /admin/users   │  │                  │  │  apps/kidibar/   │
│ - /admin/dash    │  │ Routes:          │  │  (LEGACY)        │
│                  │  │ - /recepcion     │  │ ❌ No usado      │
│ Login:           │  │ - /kidibar       │  │                  │
│ ❌ No conectado  │  │ - /monitor        │  └──────────────────┘
│    a apps/web    │  │ - /admin (placeholder)
│                  │  │ - /admin-viewer (placeholder)
└──────────────────┘  │                  │  ┌──────────────────┐
                      │ Login Flow:       │  │  apps/monitor/  │
                      │ ✅ Role-based     │  │  (LEGACY)        │
                      │ ✅ Redirects      │  │ ❌ No usado      │
                      │ ⚠️  Admin routes  │  │                  │
                      │    son placeholders│ └──────────────────┘
                      └──────────────────┘
```

---

## 🚨 PREGUNTAS CRÍTICAS - RESPUESTAS

### 1. ¿Super_admin usa apps/admin o apps/web?

**RESPUESTA:** 
- **ACTUALMENTE:** `apps/web` redirige a `/admin` (placeholder)
- **REALIDAD:** La funcionalidad está en `apps/admin`
- **PROBLEMA:** Hay una desconexión entre routing y funcionalidad

### 2. ¿Admin_viewer existe? ¿Dónde?

**RESPUESTA:**
- **SÍ EXISTE** en `apps/admin`
- **NO EXISTE** funcionalmente en `apps/web` (solo placeholder)
- **FUNCIONA** correctamente en `apps/admin` con permisos readonly

### 3. ¿Hay navegación unificada o apps separadas?

**RESPUESTA:**
- **apps/web:** ✅ Tiene navegación unificada (NavigationSidebar)
- **apps/admin:** ❌ No tiene navegación cross-module
- **RESULTADO:** Apps separadas sin conexión

### 4. ¿Cuántos package.json hay?

**RESPUESTA:**
- **5 package.json** (admin, web, reception, kidibar, monitor)
- **2 activos** (admin, web)
- **3 legacy** (reception, kidibar, monitor - no se usan)

### 5. ¿Cómo funciona el single deploy que queremos?

**RESPUESTA ACTUAL:**
- ❌ **NO funciona como single deploy**
- Hay 2 apps activas (admin, web)
- `apps/web` tiene placeholders para admin que no funcionan

**OBJETIVO:**
- ✅ 1 app (`apps/web`) con todas las rutas
- ✅ 1 package.json
- ✅ 1 deploy

---

## 📊 RESUMEN EJECUTIVO

### Estado Actual

| Componente | Estado | Ubicación | Notas |
|------------|--------|-----------|-------|
| **Super_admin** | ⚠️ Parcial | `apps/admin` (funcional) + `apps/web` (placeholder) | Desconexión |
| **Admin_viewer** | ⚠️ Parcial | `apps/admin` (funcional) + `apps/web` (placeholder) | Desconexión |
| **Recepcion** | ✅ Completo | `apps/web/routes/recepcion` | Migrado |
| **Kidibar** | ✅ Completo | `apps/web/routes/kidibar` | Migrado |
| **Monitor** | ✅ Completo | `apps/web/routes/monitor` | Migrado |
| **Navegación** | ⚠️ Parcial | Solo en `apps/web` | `apps/admin` aislado |

### Problemas Identificados

1. **Desconexión Admin:**
   - `apps/web` redirige a rutas admin que son placeholders
   - `apps/admin` tiene funcionalidad real pero no está conectado

2. **Apps Legacy:**
   - `apps/reception`, `apps/kidibar`, `apps/monitor` siguen existiendo
   - No se están usando pero ocupan espacio

3. **Deployment:**
   - 2 apps activas = 2 deploys necesarios
   - No es single deploy como se quería

---

## 🎯 RECOMENDACIONES

### Opción A: Consolidar apps/admin en apps/web

**Pros:**
- ✅ Single deploy
- ✅ Navegación unificada
- ✅ Arquitectura consistente

**Contras:**
- ⚠️ Requiere migrar toda la funcionalidad de admin
- ⚠️ Tiempo de desarrollo adicional

### Opción B: Mantener separado pero conectar

**Pros:**
- ✅ No requiere migración
- ✅ Mantiene apps/admin intacto

**Contras:**
- ❌ 2 deploys necesarios
- ❌ Navegación fragmentada

### Opción C: Híbrido (Recomendado)

**Estrategia:**
1. **FASE 3:** Migrar funcionalidad admin a `apps/web/routes/admin/`
2. **FASE 4:** Eliminar apps legacy (reception, kidibar, monitor)
3. **FASE 5:** Decidir si mantener `apps/admin` como referencia o eliminarlo

**Resultado:**
- ✅ Single deploy (`apps/web`)
- ✅ Navegación unificada
- ✅ Arquitectura limpia

---

## ✅ CONCLUSIÓN

**Estado Actual:**
- FASE 2 completada parcialmente
- Recepcion, Kidibar, Monitor migrados a `apps/web`
- Admin sigue en `apps/admin` (no migrado)
- Hay desconexión entre routing y funcionalidad

**Próximos Pasos:**
1. Decidir estrategia para admin (migrar o mantener separado)
2. Eliminar apps legacy (reception, kidibar, monitor)
3. Completar single deploy con todas las rutas en `apps/web`





























