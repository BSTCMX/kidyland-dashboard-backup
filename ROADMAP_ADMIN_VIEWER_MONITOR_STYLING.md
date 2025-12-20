# 🎨 ROADMAP: Estilización Admin-Viewer y Monitor Dashboards

**Fecha:** 2025-01-XX  
**Objetivo:** Estilizar admin-viewer y monitor para que sean IDÉNTICOS a sus homólogos (admin y recepcion respectivamente)

---

## 📋 PRINCIPIO FUNDAMENTAL

✅ **NO TOCAR:**
- Componentes de `kidibar/`, `recepcion/`, `admin/` (super_admin) que ya funcionan
- Componentes compartidos: `UserList`, `ServiceList`, `ProductList` (ya detectan readonly automáticamente)
- Stores y lógica de negocio existente

✅ **SÍ MODIFICAR:**
- Solo páginas de rutas: `admin-viewer/*` y `monitor/*`
- Solo estilos CSS y estructura HTML para igualar homólogos
- Agregar readonly banners donde corresponda

---

## 🔍 DIAGNÓSTICO: Comparación de Estilos

### **1. ADMIN vs ADMIN-VIEWER**

#### **1.1 Layout (`+layout.svelte`)**

**Admin (`/admin/+layout.svelte`):**
- ✅ Logo component con `sidebar-logo-container` (120px x 120px)
- ✅ `sidebar-actions-absolute` con `ThemeToggle` component y botón cerrar
- ✅ `sidebar-header` con padding `72px 24px 24px 24px`
- ✅ `user-section` con avatar, nombre, rol
- ✅ `logout-section` con botón logout en esquina inferior
- ✅ Text-shadow 3D en `sidebar-title`
- ✅ Nav links con iconos Lucide-Svelte (componentes dinámicos)

**Admin-Viewer (`/admin-viewer/+layout.svelte`):**
- ❌ NO tiene Logo component
- ❌ NO tiene `sidebar-actions-absolute` (tiene theme-toggle inline diferente)
- ❌ NO tiene `user-section`
- ❌ NO tiene `logout-section`
- ❌ Nav items con emojis estáticos (no Lucide-Svelte)
- ✅ Tiene readonly banner sticky (correcto, mantener)

**Diferencias Identificadas:**
1. Falta Logo component y container
2. Falta estructura `sidebar-actions-absolute` con ThemeToggle
3. Falta `user-section` completo
4. Falta `logout-section` con botón
5. Nav items deben usar Lucide-Svelte icons en lugar de emojis
6. Text-shadow 3D debe estar igual

---

#### **1.2 Dashboard Principal (`+page.svelte`)**

**Admin (`/admin/+page.svelte`):**
- ✅ `dashboard-header` con:
  - `dashboard-title` con text-shadow 3D
  - `header-actions` con:
    - `SucursalSelector` component
    - `export-buttons` con ExportButton (variant="brutalist")
    - `RefreshButton` component
- ✅ `empty-state-banner` (azul, informativo)
- ✅ `metrics-grid` con `metric-card`
- ✅ `metric-card` tiene:
  - `metric-header` con:
    - `metric-title` (con icono Lucide inline)
    - `metric-date-badge` ("Hoy") O `PeriodSelector` (variant="dropdown")
  - `metric-content` con estructura completa
- ✅ Estilos CSS:
  - `metric-header`: `display: flex; justify-content: space-between; align-items: center;`
  - `metric-date-badge`: badge azul con estilo específico
  - Hover effects completos
  - `module-customers-section` para clientes segmentados

**Admin-Viewer (`/admin-viewer/+page.svelte`):**
- ❌ NO tiene `SucursalSelector`
- ❌ `header-actions` diferente (sin SucursalSelector)
- ❌ ExportButton con `variant="secondary"` (debe ser "brutalist")
- ❌ NO tiene `empty-state-banner`
- ❌ `metric-card` NO tiene `metric-header`
- ❌ `metric-title` directamente sin header wrapper
- ❌ NO tiene `metric-date-badge` ni `PeriodSelector`
- ❌ NO tiene estructura `module-customers-section`
- ✅ Tiene readonly banner (correcto, mantener)

**Diferencias Identificadas:**
1. Falta `SucursalSelector` en header
2. ExportButton debe usar `variant="brutalist"` no "secondary"
3. Falta `empty-state-banner` (azul informativo)
4. `metric-card` debe tener `metric-header` wrapper
5. Cada metric debe tener `metric-date-badge` o `PeriodSelector` según corresponda
6. Estilos CSS deben ser idénticos (hover, spacing, etc.)

---

#### **1.3 Reports (`/admin/reports/+page.svelte` vs `/admin-viewer/reports/+page.svelte`)**

**Admin Reports:**
- ✅ Estructura completa con:
  - `reports-header` con `header-title` y `header-actions`
  - `filters-section` con card styling completo
  - `tabs-container` con ResponsiveTabs
  - `metric-card` y `metrics-grid` en cada tab
- ✅ Text-shadow 3D en `page-title`
- ✅ Estilos completos de filters, cards, etc.

**Admin-Viewer Reports:**
- ❌ Solo stub "próximamente"
- ❌ NO tiene estructura real

**Diferencias Identificadas:**
1. Copiar estructura completa de admin/reports
2. Remover botones de edición/creación
3. Mantener readonly banner
4. Mantener estilos idénticos

---

### **2. RECEPCION vs MONITOR**

#### **2.1 Layout (`+layout.svelte`)**

**Recepcion (`/recepcion/+layout.svelte`):**
- ✅ Logo component con `sidebar-logo-container` (120px x 120px)
- ✅ `sidebar-actions-absolute` con `ThemeToggle` component
- ✅ `sidebar-header` con padding `72px 24px 24px 24px`
- ✅ `user-section` con avatar, nombre, rol
- ✅ `logout-section` con botón logout
- ✅ Text-shadow 3D en `sidebar-title`
- ✅ Nav links con iconos Lucide-Svelte

**Monitor (`/monitor/+page.svelte` - actual):**
- ❌ NO tiene layout separado (es solo una page)
- ❌ NO tiene sidebar estructurado
- ❌ NO tiene Logo
- ❌ NO tiene user-section
- ❌ Tiene nav inline diferente
- ✅ Tiene readonly indicators básicos

**Diferencias Identificadas:**
1. Crear `+layout.svelte` para monitor (igual a recepcion)
2. Agregar Logo component
3. Agregar `sidebar-actions-absolute` con ThemeToggle
4. Agregar `user-section`
5. Agregar `logout-section`
6. Nav links con Lucide-Svelte icons

---

#### **2.2 Dashboard Principal (`+page.svelte`)**

**Recepcion (`/recepcion/+page.svelte`):**
- ✅ `dashboard-page` wrapper
- ✅ `dashboard-container` con `max-width: 1400px; margin: 0 auto;`
- ✅ `dashboard-header` con:
  - `page-title` con text-shadow 3D
  - `page-description`
  - `header-actions` con RefreshButton
- ✅ `ViewOnlyPanelSelector` component
- ✅ `stats-grid` con `stat-card`
- ✅ `stat-card` tiene:
  - `stat-header` con icono Lucide y `h3`
  - `stat-value` (número grande)
  - `stat-description` o `stat-details`
  - Estilos específicos de recepcion

**Monitor (`/monitor/+page.svelte` - actual):**
- ❌ Estructura diferente (no usa `dashboard-container`)
- ❌ NO tiene `dashboard-header` igual
- ❌ NO tiene `stats-grid` con `stat-card`
- ❌ Tiene cards diferentes (`dashboard-card` vs `stat-card`)
- ✅ Tiene `ViewOnlyPanelSelector` (correcto)

**Diferencias Identificadas:**
1. Cambiar estructura a `dashboard-page` > `dashboard-container`
2. Cambiar `dashboard-card` por `stat-card`
3. Cambiar `dashboard-grid` por `stats-grid`
4. Agregar `stat-header`, `stat-value`, `stat-description` según recepcion
5. Copiar estilos CSS completos de recepcion
6. Agregar readonly banner si es necesario

---

## 📝 ROADMAP DETALLADO

### **FASE 1: Admin-Viewer Layout** ⏱️ ~1 hora

**Archivo:** `apps/web/src/routes/admin-viewer/+layout.svelte`

**Tareas:**
1. ✅ Agregar Logo component y `sidebar-logo-container`
2. ✅ Reemplazar theme-toggle inline por `ThemeToggle` component en `sidebar-actions-absolute`
3. ✅ Agregar `user-section` completo (avatar, nombre, rol)
4. ✅ Agregar `logout-section` con botón logout
5. ✅ Cambiar nav items de emojis a Lucide-Svelte icons
6. ✅ Agregar text-shadow 3D en `sidebar-title`
7. ✅ Copiar estilos CSS completos de admin layout
8. ✅ Mantener readonly banner sticky

**Estilos a copiar exactamente:**
- `.sidebar-actions-absolute` (position absolute, top right)
- `.sidebar-logo-container` (120px x 120px)
- `.user-section`, `.user-avatar`, `.user-initial`, `.user-details`
- `.logout-section`, `.logout-button-bottom`
- Text-shadow 3D en `.sidebar-title`

---

### **FASE 2: Admin-Viewer Dashboard** ⏱️ ~1.5 horas

**Archivo:** `apps/web/src/routes/admin-viewer/+page.svelte`

**Tareas:**
1. ✅ Agregar `SucursalSelector` en `header-actions`
2. ✅ Cambiar ExportButton `variant="secondary"` → `variant="brutalist"`
3. ✅ Agregar `empty-state-banner` (azul informativo) igual a admin
4. ✅ Envolver `metric-title` en `metric-header` wrapper
5. ✅ Agregar `metric-date-badge` ("Hoy") o `PeriodSelector` según corresponda
6. ✅ Actualizar estilos CSS para igualar admin:
   - `.metric-header` (flex, space-between)
   - `.metric-date-badge` (badge azul)
   - Hover effects idénticos
7. ✅ Agregar `module-customers-section` para clientes segmentados (si aplica)
8. ✅ Mantener readonly banner

**Estructura de metric-card a replicar:**
```svelte
<div class="metric-card">
  <div class="metric-header">
    <h2 class="metric-title">
      <Icon size={24} />
      Título
    </h2>
    <span class="metric-date-badge">Hoy</span>
    <!-- O PeriodSelector según corresponda -->
  </div>
  <div class="metric-content">
    <!-- contenido -->
  </div>
</div>
```

---

### **FASE 3: Admin-Viewer Products** ⏱️ ~15 min

**Archivo:** `apps/web/src/routes/admin-viewer/products/+page.svelte`

**Tareas:**
1. ✅ Reemplazar stub por `<ProductList />` component
2. ✅ ProductList ya detecta readonly automáticamente (no necesita cambios)
3. ✅ Mantener readonly banner si se desea (opcional, ya ProductList maneja)

**Código:**
```svelte
<script lang="ts">
  import { onMount } from "svelte";
  import { goto } from "$app/navigation";
  import { user, hasAccessSecure } from "$lib/stores/auth";
  import ProductList from "$lib/components/admin/ProductList.svelte";

  onMount(() => {
    if (!$user || !hasAccessSecure("/admin-viewer")) {
      goto("/admin-viewer");
      return;
    }
  });
</script>

<ProductList />
```

---

### **FASE 4: Admin-Viewer Reports** ⏱️ ~2 horas

**Archivo:** `apps/web/src/routes/admin-viewer/reports/+page.svelte`

**Tareas:**
1. ✅ Copiar estructura completa de `/admin/reports/+page.svelte`
2. ✅ Remover/reemplazar `canEditSecure("admin")` checks (ya será readonly automático)
3. ✅ Mantener todos los estilos CSS idénticos
4. ✅ Agregar readonly banner al inicio
5. ✅ Verificar que ExportButton funcione (solo lectura de datos)
6. ✅ NO remover filtros ni visualizaciones (solo acciones de edición si las hay)

**Estructura a copiar:**
- `reports-page` wrapper
- `reports-header` con `header-title` y `header-actions`
- `filters-section` (card styling)
- `tabs-container` con ResponsiveTabs
- Todos los estilos CSS completos

**Consideraciones:**
- Reports es principalmente visualización (ya es casi readonly)
- Solo verificar que no haya botones de edición/creación ocultos
- Mantener todos los filtros y visualizaciones

---

### **FASE 5: Monitor Layout** ⏱️ ~1.5 horas

**Archivo:** `apps/web/src/routes/monitor/+layout.svelte` (CREAR NUEVO)

**Tareas:**
1. ✅ Crear archivo `+layout.svelte` nuevo
2. ✅ Copiar estructura completa de `/recepcion/+layout.svelte`
3. ✅ Cambiar "Recepción" → "Monitor" en textos
4. ✅ Cambiar nav items según monitor (timers, recepción readonly, kidibar readonly)
5. ✅ Agregar readonly banner sticky (si aplica)
6. ✅ Mantener todos los estilos CSS idénticos
7. ✅ Agregar Logo component
8. ✅ Agregar `user-section` y `logout-section`

**Nav items para Monitor:**
```typescript
const monitorNavItems = [
  { route: "/monitor", label: "Dashboard", icon: Monitor },
  { route: "/monitor/timers", label: "Timers", icon: Clock },
  // Links a recepcion/kidibar readonly según permisos
];
```

---

### **FASE 6: Monitor Dashboard** ⏱️ ~1 hora

**Archivo:** `apps/web/src/routes/monitor/+page.svelte`

**Tareas:**
1. ✅ Copiar estructura completa de `/recepcion/+page.svelte`
2. ✅ Cambiar `stats-grid` con `stat-card` (en lugar de `dashboard-grid` con `dashboard-card`)
3. ✅ Usar `recepcionStatsStore` (ya existe y funciona)
4. ✅ Mantener `ViewOnlyPanelSelector` existente
5. ✅ Cambiar estilos CSS para igualar recepcion:
   - `.dashboard-page` wrapper
   - `.dashboard-container` con max-width
   - `.stat-card` en lugar de `.dashboard-card`
   - `.stat-header`, `.stat-value`, `.stat-description`
6. ✅ Agregar readonly banner si es necesario
7. ✅ Mantener RefreshButton igual a recepcion

**Estructura a replicar:**
```svelte
<div class="dashboard-page">
  <div class="dashboard-container">
    <div class="dashboard-header">
      <div>
        <h1 class="page-title">Dashboard</h1>
        <p class="page-description">...</p>
      </div>
      <div class="header-actions">
        <RefreshButton />
      </div>
    </div>
    
    <ViewOnlyPanelSelector />
    
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-header">
          <Icon />
          <h3>Título</h3>
        </div>
        <div class="stat-value">Valor</div>
        <p class="stat-description">Descripción</p>
      </div>
    </div>
  </div>
</div>
```

---

## ✅ CHECKLIST DE VALIDACIÓN

### Admin-Viewer
- [ ] Layout tiene Logo, user-section, logout-section igual a admin
- [ ] Dashboard tiene SucursalSelector, ExportButton brutalist, empty-state-banner
- [ ] Metric-cards tienen metric-header con date-badge o PeriodSelector
- [ ] Estilos CSS idénticos a admin (hover, spacing, shadows)
- [ ] Products usa ProductList component
- [ ] Reports tiene estructura completa igual a admin
- [ ] Readonly banner visible y correcto

### Monitor
- [ ] Layout existe y tiene Logo, user-section, logout-section igual a recepcion
- [ ] Dashboard usa stats-grid con stat-card (no dashboard-grid)
- [ ] Estilos CSS idénticos a recepcion
- [ ] ViewOnlyPanelSelector funciona
- [ ] RecepcionStatsStore carga datos correctamente
- [ ] Readonly banner visible si aplica

---

## 🚨 RIESGOS Y MITIGACIONES

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Estilos no quedan idénticos | Media | Bajo | Comparar línea por línea con homólogo |
| Readonly banner interfiere con layout | Baja | Medio | Ajustar z-index y spacing si necesario |
| Componentes no detectan readonly | Baja | Alto | Ya validado en Users/Services, ProductList igual |
| Performance por estilos duplicados | Baja | Bajo | CSS es ligero, no hay overhead significativo |

---

## ⏱️ TIEMPO ESTIMADO TOTAL

**FASE 1:** Admin-Viewer Layout - 1 hora  
**FASE 2:** Admin-Viewer Dashboard - 1.5 horas  
**FASE 3:** Admin-Viewer Products - 15 min  
**FASE 4:** Admin-Viewer Reports - 2 horas  
**FASE 5:** Monitor Layout - 1.5 horas  
**FASE 6:** Monitor Dashboard - 1 hora  

**TOTAL: ~7.5 horas** (puede variar según complejidad de reports)

---

## 📌 NOTAS IMPORTANTES

1. **NO modificar componentes compartidos** - UserList, ServiceList, ProductList ya funcionan correctamente con readonly
2. **NO tocar rutas de admin, recepcion, kidibar** - Solo admin-viewer y monitor
3. **Copiar estilos exactamente** - Pixel-perfect match con homólogos
4. **Mantener readonly banners** - Son diferenciadores visuales importantes
5. **Validar permisos** - Asegurar que solo lectura funcione correctamente

---

## 🎯 CRITERIOS DE ÉXITO

✅ Admin-Viewer se ve **idéntico** a Admin (excepto readonly banner)  
✅ Monitor se ve **idéntico** a Recepcion (excepto readonly indicators)  
✅ Funcionalidad readonly funciona correctamente  
✅ No se rompe ninguna funcionalidad existente  
✅ Estilos son responsive y mantienen diseño original  
✅ Performance no se degrada

---

**Fin del Roadmap**


