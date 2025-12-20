# PROMPT CURSOR: EJECUTAR MIGRACIÓN Y VALIDACIÓN EN TERMINAL

## 🎯 OBJETIVO

Ejecutar migración SQL y validación completa **directamente en terminal integrado de Cursor**, mostrando output completo.

## 🚨 REGLAS DE EJECUCIÓN

- ✅ **USAR TERMINAL INTEGRADO** de Cursor
- ✅ **MOSTRAR OUTPUT** en panel de terminal
- ✅ **EJECUTAR comandos** directamente (no solo crear scripts)
- ✅ **REPORTAR resultados** desde terminal

## 📋 SECUENCIA DE EJECUCIÓN

### PASO 1: Aplicar Migración SQL

**EJECUTAR en terminal integrado:**
```bash
cd packages/api
python3 apply_migration_final.py
```

**MOSTRAR output completo** en terminal.

**Verificar:**
- ✅ Migración aplicada exitosamente
- ✅ Columna email eliminada
- ✅ Índice eliminado

---

### PASO 2: Ejecutar Tests Backend

**EJECUTAR en terminal integrado:**
```bash
cd packages/api
python3 -m pytest tests/ -v
```

**MOSTRAR output completo** en terminal.

**Verificar:**
- ✅ Todos los tests pasando
- ✅ Sin errores relacionados con email

---

### PASO 3: Compilar Frontend

**EJECUTAR en terminal integrado:**
```bash
cd apps/admin
pnpm build
```

**MOSTRAR output completo** en terminal.

**Verificar:**
- ✅ Compilación exitosa
- ✅ Sin errores relacionados con email

---

### PASO 4: Verificación Final

**EJECUTAR en terminal integrado:**
```bash
cd ../..
grep -r "email" packages/api/models/user.py packages/api/schemas/user.py packages/shared/src/types.ts apps/admin/src/lib/components/UserForm.svelte 2>&1 | grep -v "node_modules" | grep -v "venv"
```

**MOSTRAR output completo** en terminal.

**Verificar:**
- ✅ Sin referencias a email en archivos clave

---

## ✅ RESULTADO ESPERADO

- ✅ Migración SQL aplicada
- ✅ Tests backend pasando
- ✅ Frontend compilando sin errores
- ✅ Sistema funcionando con Username + Password + Role únicamente

## 🚨 SI HAY ERRORES

**REPORTAR inmediatamente con:**
- Output completo del comando que falló
- Mensaje de error específico
- Stack trace si aplica

---

## 📝 INSTRUCCIONES PARA CURSOR

1. **EJECUTAR en terminal integrado**: `cd packages/api`
2. **EJECUTAR en terminal integrado**: `python3 apply_migration_final.py`
3. **MOSTRAR output completo** en terminal
4. **EJECUTAR en terminal integrado**: `python3 -m pytest tests/ -v`
5. **MOSTRAR output completo** en terminal
6. **EJECUTAR en terminal integrado**: `cd apps/admin && pnpm build`
7. **MOSTRAR output completo** en terminal
8. **REPORTAR resultados** desde terminal

---

**IMPORTANTE:** No solo crear scripts, **EJECUTARLOS** y mostrar output completo.


