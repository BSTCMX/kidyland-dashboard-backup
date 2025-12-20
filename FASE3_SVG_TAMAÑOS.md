# ✅ SVG - TAMAÑOS RECOMENDADOS (Respuesta Directa)

## 🎯 RESPUESTA RÁPIDA

**SÍ, SVG es suficiente para ambos.** Solo configura el `viewBox` así:

---

## 📐 TAMAÑOS DEL VIEWBOX

### **FAVICON SVG**

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
  <!-- Tu diseño aquí -->
</svg>
```

**Recomendación:** `viewBox="0 0 512 512"`  
- ✅ Se ve perfecto en todos los tamaños
- ✅ Alta calidad en pantallas Retina/4K
- ✅ Ligero (< 5KB)

**Ubicación:** `/apps/web/static/favicon.svg`

---

### **LOGO SVG**

**Depende de las proporciones de tu logo:**

#### **Si es CUADRADO:**
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 400">
  <!-- Tu logo aquí -->
</svg>
```

#### **Si es HORIZONTAL (más ancho que alto):**
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 200">
  <!-- Tu logo aquí -->
</svg>
```
*Ratio 3:1 (ajusta según tu diseño real)*

#### **Si es VERTICAL (más alto que ancho):**
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 400">
  <!-- Tu logo aquí -->
</svg>
```

**Recomendación:** 
- ✅ `viewBox="0 0 400 200"` si es horizontal típico (2:1)
- ✅ `viewBox="0 0 400 400"` si es cuadrado
- ✅ Ajusta según proporciones reales de tu diseño

**Ubicación:** `/apps/web/static/logo.svg`

---

## 💡 LO IMPORTANTE

1. ✅ **El viewBox NO es el tamaño físico** - Solo define proporciones
2. ✅ **El navegador lo escala automáticamente** - Se ve perfecto en cualquier tamaño
3. ✅ **NO pongas width/height en el SVG** - Lo controlamos con CSS

---

## ✅ RESUMEN

| Archivo | viewBox Recomendado | Ubicación |
|---------|-------------------|-----------|
| **favicon.svg** | `0 0 512 512` | `/static/favicon.svg` |
| **logo.svg** | `0 0 400 200` (o según proporciones) | `/static/logo.svg` |

---

## 🚀 PRÓXIMOS PASOS

1. ✅ Crear/optimizar `favicon.svg` con `viewBox="0 0 512 512"`
2. ✅ Crear `logo.svg` con viewBox según proporciones
3. ✅ Colocar ambos en `/apps/web/static/`
4. ✅ Listo! 🎉

---

**¿Cuál es la forma de tu logo?** (cuadrado, horizontal, vertical)  
Te doy el viewBox exacto 🎯

