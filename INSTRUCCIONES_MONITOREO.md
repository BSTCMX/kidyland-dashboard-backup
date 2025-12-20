# 📋 INSTRUCCIONES PARA MONITOREAR ERRORES

## 🔍 CÓMO VER LOS LOGS DEL SERVIDOR

### Opción 1: Terminal donde se ejecuta `pnpm dev`

1. Ve a la terminal donde ejecutaste `pnpm dev`
2. Busca líneas que digan:
   - `ERROR`
   - `Error`
   - `500`
   - Stack trace

### Opción 2: Ver logs guardados

```bash
cd /Users/Jorge/Documents/kidyland
tail -f /tmp/kidyland-frontend-debug.log
```

### Opción 3: Reiniciar servidor y ver errores

```bash
cd /Users/Jorge/Documents/kidyland/apps/web
pnpm dev
# Los errores aparecerán en esta terminal
```

---

## 📝 QUÉ BUSCAR EN LOS LOGS

### Errores comunes:

1. **Import errors:**
   ```
   Error: Cannot find module '...'
   Error: Failed to resolve import '...'
   ```

2. **SSR errors:**
   ```
   ReferenceError: window is not defined
   ReferenceError: document is not defined
   ```

3. **Component errors:**
   ```
   Error: Component '...' failed to render
   ```

4. **Build errors:**
   ```
   [vite] error building...
   ```

---

## 🎯 PRÓXIMOS PASOS

**Por favor:**
1. Copia el error completo que aparece en la terminal del servidor
2. O comparte una captura de pantalla del error
3. Así podré identificar y corregir el problema exacto

---

**¡Gracias por tu paciencia!** 🚀

