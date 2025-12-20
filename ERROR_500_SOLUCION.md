# 🚨 ERROR 500 - SOLUCIÓN

**Problema:** Error 500 Internal Server Error
**Causa probable:** Componente `MascotLogo` usando `Image()` durante SSR

---

## 🔧 CORRECCIÓN

El componente `MascotLogo` está intentando usar `new Image()` que puede fallar durante SSR.

**Solución:** Asegurar que todos los accesos a APIs del navegador estén dentro de `onMount()` o con checks de `typeof window`.

---

## ✅ ARCHIVOS A VERIFICAR

1. `MascotLogo.svelte` - Ya tiene `onMount()` ✓
2. `Logo.svelte` - Solo usa `<img>` tag ✓
3. `Tagline.svelte` - Solo texto ✓
4. `ThemeToggle.svelte` - Ya tiene checks de `window` ✓

---

## 🔍 PRÓXIMOS PASOS

1. Verificar logs del servidor
2. Aislar componente problemático
3. Aplicar corrección

