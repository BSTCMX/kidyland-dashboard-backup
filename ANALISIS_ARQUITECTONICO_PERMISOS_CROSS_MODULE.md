# 🏗️ ANÁLISIS ARQUITECTÓNICO - PERMISOS CROSS-MODULE KIDYLAND

**Fecha:** 2025-01-XX  
**Objetivo:** Evaluar viabilidad técnica de permisos cross-module antes de implementar FASE 2

---

## 📊 MATRIZ DE PERMISOS PROPUESTA

### Acceso por Módulo

| Rol | Admin | Admin-Viewer | Recepción | Kidibar | Monitor |
|-----|-------|--------------|-----------|---------|---------|
| `super_admin` | ✅ FULL | ✅ FULL | ✅ FULL | ✅ FULL | ✅ FULL |
| `admin_viewer` | ✅ READ | ✅ READ | ✅ READ | ✅ READ | ✅ READ |
| `recepcion` | ❌ No | ❌ No | ✅ FULL | ✅ READ+ | ❌ No |
| `kidibar` | ❌ No | ❌ No | ❌ No | ✅ FULL | ❌ No |
| `monitor` | ❌ No | ❌ No | ✅ READ | ✅ READ | ✅ FULL |

### Permisos Granulares

- **FULL**: Crear, leer, actualizar, eliminar
- **READ**: Solo visualización
- **READ+**: Visualización + algunas acciones de supervisión
- **No**: Sin acceso

---

## ✅ VIABILIDAD ARQUITECTÓNICA

### **1. SvelteKit + Clean Architecture: ✅ VIABLE**

**Análisis:**
- SvelteKit soporta routing dinámico y guards
- Clean Architecture permite separar permisos en capa de aplicación
- Stores reactivos facilitan permisos granulares
- No requiere cambios en backend (permisos ya existen)

**Conclusión:** ✅ **100% VIABLE** con patterns modernos

---

## 🎯 ESTRATEGIA DE IMPLEMENTACIÓN RECOMENDADA

### **APPROACH: D) HÍBRIDO ESTRATÉGICO**

**Razón:** Combinación de route-level guards + component-level props + store-level permissions = máximo control y flexibilidad.

---

### **CAPA 1: ROUTE-LEVEL GUARDS** (Base de Seguridad)

**Implementación:**
```typescript
// lib/utils/permissions.ts
export interface ModulePermissions {
  canAccess: boolean;
  canEdit: boolean;
  canCreate: boolean;
  canDelete: boolean;
}

export function getModulePermissions(
  userRole: UserRole,
  module: 'admin' | 'recepcion' | 'kidibar' | 'monitor'
): ModulePermissions {
  const permissions = {
    super_admin: {
      admin: { canAccess: true, canEdit: true, canCreate: true, canDelete: true },
      recepcion: { canAccess: true, canEdit: true, canCreate: true, canDelete: true },
      kidibar: { canAccess: true, canEdit: true, canCreate: true, canDelete: true },
      monitor: { canAccess: true, canEdit: true, canCreate: true, canDelete: true },
    },
    admin_viewer: {
      admin: { canAccess: true, canEdit: false, canCreate: false, canDelete: false },
      recepcion: { canAccess: true, canEdit: false, canCreate: false, canDelete: false },
      kidibar: { canAccess: true, canEdit: false, canCreate: false, canDelete: false },
      monitor: { canAccess: true, canEdit: false, canCreate: false, canDelete: false },
    },
    recepcion: {
      admin: { canAccess: false, canEdit: false, canCreate: false, canDelete: false },
      recepcion: { canAccess: true, canEdit: true, canCreate: true, canDelete: true },
      kidibar: { canAccess: true, canEdit: false, canCreate: false, canDelete: false }, // READ+
      monitor: { canAccess: false, canEdit: false, canCreate: false, canDelete: false },
    },
    kidibar: {
      admin: { canAccess: false, canEdit: false, canCreate: false, canDelete: false },
      recepcion: { canAccess: false, canEdit: false, canCreate: false, canDelete: false },
      kidibar: { canAccess: true, canEdit: true, canCreate: true, canDelete: true },
      monitor: { canAccess: false, canEdit: false, canCreate: false, canDelete: false },
    },
    monitor: {
      admin: { canAccess: false, canEdit: false, canCreate: false, canDelete: false },
      recepcion: { canAccess: true, canEdit: false, canCreate: false, canDelete: false },
      kidibar: { canAccess: true, canEdit: false, canCreate: false, canDelete: false },
      monitor: { canAccess: true, canEdit: true, canCreate: true, canDelete: true },
    },
  };

  return permissions[userRole]?.[module] || {
    canAccess: false,
    canEdit: false,
    canCreate: false,
    canDelete: false,
  };
}
```

**Uso en Routes:**
```typescript
// routes/kidibar/+page.svelte
import { user } from '$lib/stores/auth';
import { getModulePermissions } from '$lib/utils/permissions';

$: permissions = $user ? getModulePermissions($user.role, 'kidibar') : null;

onMount(() => {
  if (!$user || !permissions?.canAccess) {
    goto('/');
  }
});
```

**Ventajas:**
- ✅ Seguridad a nivel de ruta (imposible acceder sin permisos)
- ✅ Redirect automático si no tiene acceso
- ✅ Fácil de testear y mantener

---

### **CAPA 2: STORE-LEVEL PERMISSIONS** (Lógica de Negocio)

**Implementación:**
```typescript
// lib/stores/auth.ts (extendido)
export function hasAccess(route: string): boolean {
  const currentUser = get(user);
  if (!currentUser) return false;

  const routePermissions: Record<string, UserRole[]> = {
    '/admin': ['super_admin'],
    '/admin-viewer': ['admin_viewer', 'super_admin'],
    '/recepcion': ['super_admin', 'admin_viewer', 'recepcion', 'monitor'],
    '/kidibar': ['super_admin', 'admin_viewer', 'recepcion', 'kidibar', 'monitor'],
    '/monitor': ['super_admin', 'admin_viewer', 'monitor'],
  };

  const allowedRoles = routePermissions[route] || [];
  return allowedRoles.includes(currentUser.role);
}

export function canEdit(module: string): boolean {
  const currentUser = get(user);
  if (!currentUser) return false;

  const editPermissions: Record<string, UserRole[]> = {
    'admin': ['super_admin'],
    'recepcion': ['super_admin', 'recepcion'],
    'kidibar': ['super_admin', 'kidibar'],
    'monitor': ['super_admin'],
  };

  const allowedRoles = editPermissions[module] || [];
  return allowedRoles.includes(currentUser.role);
}
```

**Uso en Stores:**
```typescript
// lib/stores/sales.ts
import { canEdit } from '$lib/stores/auth';

export async function createSale(...) {
  if (!canEdit('recepcion')) {
    throw new Error('No tienes permisos para crear ventas');
  }
  // ... lógica de creación
}
```

**Ventajas:**
- ✅ Permisos centralizados en auth store
- ✅ Reutilizable en cualquier componente/store
- ✅ Fácil de mantener y actualizar

---

### **CAPA 3: COMPONENT-LEVEL PROPS** (UX Granular)

**Implementación:**
```typescript
// lib/components/shared/EditableCard.svelte
<script lang="ts">
  import { user } from '$lib/stores/auth';
  import { canEdit } from '$lib/stores/auth';

  export let module: string;
  export let data: any;

  $: readonly = !canEdit(module);
  $: showActions = !readonly;
</script>

<div class="card">
  <slot />
  
  {#if showActions}
    <div class="actions">
      <Button on:click={handleEdit}>Editar</Button>
      <Button variant="danger" on:click={handleDelete}>Eliminar</Button>
    </div>
  {:else}
    <div class="readonly-badge">Solo Lectura</div>
  {/if}
</div>
```

**Uso:**
```svelte
<!-- routes/kidibar/+page.svelte -->
<EditableCard module="kidibar" {data}>
  <!-- contenido -->
</EditableCard>
```

**Ventajas:**
- ✅ UX granular (muestra/oculta acciones por componente)
- ✅ Indicadores visuales de readonly
- ✅ Reutilizable en múltiples módulos

---

## 🧭 NAVEGACIÓN CROSS-MODULE

### **Sidebar Dinámico con Permisos**

**Implementación:**
```svelte
<!-- lib/components/shared/NavigationSidebar.svelte -->
<script lang="ts">
  import { user, hasAccess } from '$lib/stores/auth';
  import { getModulePermissions } from '$lib/utils/permissions';

  const navItems = [
    { route: '/admin', label: 'Administración', icon: '⚙️', module: 'admin' },
    { route: '/admin-viewer', label: 'Visualización', icon: '👁️', module: 'admin' },
    { route: '/recepcion', label: 'Recepción', icon: '🎮', module: 'recepcion' },
    { route: '/kidibar', label: 'KidiBar', icon: '🍿', module: 'kidibar' },
    { route: '/monitor', label: 'Monitor', icon: '📺', module: 'monitor' },
  ];

  $: visibleItems = navItems.filter(item => {
    if (!$user) return false;
    return hasAccess(item.route);
  });

  $: itemPermissions = (item) => {
    if (!$user) return null;
    return getModulePermissions($user.role, item.module);
  };
</script>

<nav class="sidebar">
  {#each visibleItems as item}
    {@const perms = itemPermissions(item)}
    <a
      href={item.route}
      class="nav-item"
      class:readonly={!perms?.canEdit}
    >
      <span class="icon">{item.icon}</span>
      <span class="label">{item.label}</span>
      {#if !perms?.canEdit}
        <span class="readonly-badge">👁️</span>
      {/if}
    </a>
  {/each}
</nav>
```

**Ventajas:**
- ✅ Navegación dinámica según permisos
- ✅ Indicadores visuales de readonly
- ✅ UX intuitiva

---

## ⚡ OPTIMIZACIONES DE PERFORMANCE

### **1. Code Splitting por Módulo**

```typescript
// routes/kidibar/+page.svelte
import { onMount } from 'svelte';

let KidibarDashboard;

onMount(async () => {
  if (hasAccess('/kidibar')) {
    KidibarDashboard = (await import('./KidibarDashboard.svelte')).default;
  }
});
```

**Beneficio:** Solo carga código del módulo accesible

### **2. Lazy Load Stores**

```typescript
// lib/stores/index.ts
export async function loadStoresForModule(module: string) {
  const stores = {
    recepcion: () => import('./recepcion'),
    kidibar: () => import('./kidibar'),
    admin: () => import('./admin'),
  };

  return stores[module]?.() || null;
}
```

**Beneficio:** Stores se cargan solo cuando se necesitan

### **3. Permission Caching**

```typescript
// lib/utils/permissions.ts
const permissionCache = new Map<string, ModulePermissions>();

export function getModulePermissions(
  userRole: UserRole,
  module: string
): ModulePermissions {
  const key = `${userRole}:${module}`;
  
  if (permissionCache.has(key)) {
    return permissionCache.get(key)!;
  }

  const permissions = calculatePermissions(userRole, module);
  permissionCache.set(key, permissions);
  
  return permissions;
}
```

**Beneficio:** Evita recalcular permisos en cada render

---

## 🧪 TESTABILIDAD

### **Unit Tests de Permisos**

```typescript
// lib/utils/permissions.test.ts
import { describe, it, expect } from 'vitest';
import { getModulePermissions } from './permissions';

describe('Permissions', () => {
  it('recepcion can access kidibar readonly', () => {
    const perms = getModulePermissions('recepcion', 'kidibar');
    expect(perms.canAccess).toBe(true);
    expect(perms.canEdit).toBe(false);
  });

  it('kidibar cannot access recepcion', () => {
    const perms = getModulePermissions('kidibar', 'recepcion');
    expect(perms.canAccess).toBe(false);
  });
});
```

**Ventaja:** Tests garantizan que permisos funcionan correctamente

---

## 📈 ESCALABILIDAD

### **Agregar Nuevos Roles**

```typescript
// Solo agregar entrada en matriz de permisos
const permissions = {
  // ... roles existentes
  nuevo_rol: {
    recepcion: { canAccess: true, canEdit: false },
    // ...
  },
};
```

**Ventaja:** Extensible sin modificar lógica existente

### **Agregar Nuevos Módulos**

```typescript
// Agregar módulo a matriz
const permissions = {
  super_admin: {
    // ... módulos existentes
    nuevo_modulo: { canAccess: true, canEdit: true, ... },
  },
};
```

**Ventaja:** Mismo pattern, fácil de mantener

---

## 🎨 USER EXPERIENCE

### **Indicadores Visuales**

1. **Badge "Solo Lectura"** en sidebar cuando `canEdit = false`
2. **Botones deshabilitados** en lugar de ocultos (mejor UX)
3. **Tooltips explicativos** ("Solo recepcion puede editar")
4. **Color coding**: Verde (editable), Amarillo (readonly), Rojo (sin acceso)

### **Navegación Fluida**

- Sidebar siempre visible con módulos accesibles
- Breadcrumbs para contexto cross-module
- Quick switch entre módulos relacionados

---

## 🚨 RIESGOS Y MITIGACIONES

### **Riesgo 1: Performance con Múltiples Módulos**

**Mitigación:**
- ✅ Lazy loading de componentes
- ✅ Code splitting por ruta
- ✅ Permission caching
- ✅ Stores se cargan bajo demanda

### **Riesgo 2: Complejidad de Mantenimiento**

**Mitigación:**
- ✅ Matriz de permisos centralizada
- ✅ Tests unitarios de permisos
- ✅ Documentación clara
- ✅ TypeScript para type safety

### **Riesgo 3: Inconsistencias entre Capas**

**Mitigación:**
- ✅ Single source of truth (auth store)
- ✅ Helpers reutilizables
- ✅ Validación en múltiples capas (defense in depth)

---

## ✅ RECOMENDACIÓN FINAL

### **APPROACH: D) HÍBRIDO ESTRATÉGICO**

**Implementación por Capas:**

1. **Route-Level Guards** (Seguridad base)
   - Protección de rutas
   - Redirect automático
   - Imposible acceder sin permisos

2. **Store-Level Permissions** (Lógica de negocio)
   - Validación en operaciones
   - Centralizado en auth store
   - Reutilizable

3. **Component-Level Props** (UX granular)
   - Props `readonly` en componentes
   - Indicadores visuales
   - Botones condicionales

**Orden de Implementación:**

1. ✅ **FASE 2.1:** Auth store con permisos (hasAccess, canEdit)
2. ✅ **FASE 2.2:** Route guards en cada módulo
3. ✅ **FASE 2.3:** Navigation sidebar dinámico
4. ✅ **FASE 2.4:** Component props readonly
5. ✅ **FASE 2.5:** Stores consolidados con validación de permisos

**Tiempo Estimado:** 4-5 horas (vs 3-4h sin permisos cross-module)

---

## 🎯 CONCLUSIÓN

### **✅ VIABILIDAD: 100%**

- ✅ Técnicamente viable en SvelteKit
- ✅ Alineado con Clean Architecture
- ✅ Patterns modernos 2025
- ✅ Escalable y mantenible
- ✅ Performance optimizado

### **✅ RECOMENDACIÓN: PROCEDER**

La arquitectura propuesta es sólida, escalable y sigue mejores prácticas. El approach híbrido ofrece:
- Seguridad robusta (route guards)
- Flexibilidad (component props)
- Mantenibilidad (store centralizado)
- Performance (lazy loading)

**¿Procedemos con FASE 2 actualizada con permisos cross-module?**





























