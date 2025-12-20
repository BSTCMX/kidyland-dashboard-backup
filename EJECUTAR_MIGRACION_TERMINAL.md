# 🔧 EJECUTAR MIGRACIÓN - INSTRUCCIONES TERMINAL

## 📋 SECUENCIA DE EJECUCIÓN EN TERMINAL INTEGRADO

### PASO 1: Aplicar Migración SQL

```bash
cd packages/api
python3 apply_migration_final.py
```

**Output esperado:**
```
======================================================================
🚀 APLICANDO MIGRACIÓN SQL: ELIMINACIÓN DE CAMPO EMAIL
======================================================================

🔍 Verificando estado actual...
   ⚠️  Columna 'email' encontrada en tabla 'users'
   ⚠️  Índice 'ix_users_email' encontrado

📝 Aplicando migración SQL...
   ✅ Columna 'email' eliminada
   ✅ Índice 'ix_users_email' eliminado

✅ Verificando migración...
   ✅ Migración aplicada exitosamente!
   ✅ Columna 'email' eliminada de la tabla 'users'
   ✅ Índice 'ix_users_email' eliminado

======================================================================
🎉 MIGRACIÓN COMPLETADA EXITOSAMENTE
======================================================================
```

---

### PASO 2: Ejecutar Tests Backend

```bash
cd packages/api
python3 -m pytest tests/ -v
```

**Output esperado:**
- Todos los tests pasando
- Sin errores relacionados con email

---

### PASO 3: Compilar Frontend

```bash
cd apps/admin
pnpm build
```

**Output esperado:**
- Compilación exitosa
- Sin errores relacionados con email

---

## ✅ VERIFICACIÓN FINAL

Después de ejecutar todos los pasos, verificar:

```bash
# Verificar que no hay referencias a email en código
grep -r "email" packages/api/models/user.py packages/api/schemas/user.py
# Debe retornar: sin resultados

grep -r "email" packages/shared/src/types.ts
# Debe retornar: sin resultados

grep -r "email" apps/admin/src/lib/components/UserForm.svelte
# Debe retornar: sin resultados
```

---

## 🎯 RESULTADO ESPERADO

- ✅ Migración SQL aplicada
- ✅ Tests backend pasando
- ✅ Frontend compilando sin errores
- ✅ Sistema funcionando con Username + Password + Role únicamente

---

## 📝 NOTAS

- **Ejecutar en terminal integrado de Cursor**
- **Mostrar output completo de cada comando**
- **Reportar cualquier error inmediatamente**
- **Seguir Clean Architecture**
- **Usar solo pnpm como package manager**


