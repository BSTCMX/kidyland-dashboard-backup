# 🔍 ANÁLISIS: Working Directory vs pnpm Workspace

**Fecha:** 2024-12-04  
**Hipótesis:** Problema de working directory con pnpm workspace

---

## 📊 RESULTADO

**Ejecutado desde:** `/Users/Jorge/Documents/kidyland/apps/web`  
**Error persiste:** ❌ Sí

**Stack trace muestra:**
```
/Users/Jorge/Documents/kidyland/node_modules/.pnpm/...
```

**Análisis:**
- ✅ Ejecutamos desde `apps/web` (correcto)
- ❌ Pero pnpm workspace usa `node_modules` del ROOT
- ⚠️ SvelteKit busca el alias `__SERVER__` en contexto del root

---

## 🔍 PROBLEMA IDENTIFICADO

**pnpm workspace structure:**
- Todos los `node_modules` están en el root del monorepo
- `apps/web/node_modules` es un symlink al root
- SvelteKit necesita resolver alias virtuales en el contexto correcto

**El alias `__SERVER__` se genera en:**
- `.svelte-kit/generated/server/internal.js` (en `apps/web/`)

**Pero Vite busca en:**
- Contexto del root del monorepo (`/Users/Jorge/Documents/kidyland/`)

---

## 💡 CONCLUSIÓN

El problema NO es el working directory desde donde ejecutamos, sino cómo pnpm workspace estructura los `node_modules` y cómo SvelteKit/Vite resuelve alias virtuales en ese contexto.

El stack trace confirma que está usando node_modules del root, lo cual es normal en pnpm workspace, pero SvelteKit no puede resolver el alias `__SERVER__` correctamente en ese contexto.

---

## 🎯 WORKAROUND CONFIRMADO

**Build + Preview funciona** porque en build mode, SvelteKit resuelve los alias correctamente.

**Dev mode falla** porque la resolución de alias virtuales en tiempo real no funciona con pnpm workspace structure.

