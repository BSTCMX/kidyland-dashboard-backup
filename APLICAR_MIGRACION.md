# 🔧 APLICAR MIGRACIÓN SQL - INSTRUCCIONES

## 📋 OPCIÓN 1: Script Python (Recomendado)

### Ejecutar script de migración:

```bash
cd packages/api
python3 apply_migration_final.py
```

Este script:
- ✅ Usa SQLAlchemy (ya configurado)
- ✅ Verifica estado antes y después
- ✅ Es idempotente (puede ejecutarse múltiples veces)
- ✅ Sigue Clean Architecture

---

## 📋 OPCIÓN 2: Neon Dashboard (Alternativa)

### Pasos:

1. Abrir Neon Dashboard: https://console.neon.tech
2. Seleccionar tu proyecto
3. Ir a **"SQL Editor"**
4. Copiar y pegar este SQL:

```sql
ALTER TABLE users DROP COLUMN IF EXISTS email;
DROP INDEX IF EXISTS ix_users_email;
```

5. Ejecutar
6. Verificar:

```sql
SELECT column_name 
FROM information_schema.columns 
WHERE table_name = 'users' AND column_name = 'email';
```

**Debe retornar 0 filas**

---

## 📋 OPCIÓN 3: psql (Si está disponible)

### Para Neon Local:
```bash
psql -h localhost -p 5432 -U neon -d kidyland -f packages/api/migrations/remove_email_field.sql
```

### Para Neon Serverless:
```bash
psql 'postgresql://...?sslmode=require' -f packages/api/migrations/remove_email_field.sql
```

---

## ✅ VERIFICACIÓN POST-MIGRACIÓN

Después de aplicar la migración, verificar:

```sql
-- Verificar columna
SELECT column_name 
FROM information_schema.columns 
WHERE table_name = 'users' AND column_name = 'email';
-- Debe retornar 0 filas

-- Verificar índice
SELECT indexname 
FROM pg_indexes 
WHERE tablename = 'users' AND indexname = 'ix_users_email';
-- Debe retornar 0 filas
```

---

## 🎯 RESULTADO ESPERADO

- ✅ Columna `email` eliminada de tabla `users`
- ✅ Índice `ix_users_email` eliminado
- ✅ Sistema funciona con Username + Password + Role únicamente

---

## 📝 NOTAS

- La migración usa `IF EXISTS` para ser idempotente
- No afecta datos existentes (solo elimina columna)
- Compatible con Neon (local y serverless)
- Sigue Clean Architecture (usa SQLAlchemy del proyecto)


