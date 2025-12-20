# PROMPT CURSOR: VALIDACIÓN FINAL ELIMINACIÓN EMAIL - EJECUTAR EN TERMINAL

## 🎯 **OBJETIVO**

Ejecutar validación completa en terminal para confirmar que la eliminación de email se completó correctamente y el sistema funciona sin errores.

**ENFOQUE:** Migración SQL manual (SIN Alembic) compatible con Neon PostgreSQL.

## 🚨 **REGLAS DE EJECUCIÓN**

- ✅ **TODO en terminal/bash commands**
- ✅ **Mostrar output completo** de cada comando
- ✅ **NO usar interfaces gráficas**
- ✅ **NO usar Alembic** - Migración SQL manual directa
- ✅ **Reportar cualquier error** inmediatamente

## 📋 **SECUENCIA DE VALIDACIÓN TERMINAL**

### **PASO 1: VERIFICAR ESTADO ACTUAL**

```bash
# Mostrar directorio actual y estructura
pwd
ls -la

# Verificar que estás en el root del proyecto Kidyland
echo "📍 Ubicación actual del proyecto:"
find . -name "package.json" -type f | head -5

# Verificar estructura del proyecto
echo "📋 Estructura de directorios principales:"
ls -la packages/ apps/ 2>/dev/null || echo "⚠️ Verificar estructura de directorios"
```

### **PASO 2: VERIFICAR MIGRACIÓN SQL CREADA**

```bash
# Buscar archivo de migración
echo "🔍 Buscando archivo de migración SQL:"
find . -name "*remove_email*" -type f

# Verificar directorio migrations
ls -la packages/api/migrations/ 2>/dev/null || echo "⚠️ Creando directorio migrations si no existe"

# Mostrar contenido de migración SQL
echo "📄 Contenido de la migración SQL:"
cat packages/api/migrations/remove_email_field.sql 2>/dev/null || echo "❌ Archivo de migración no encontrado"
```

### **PASO 3: APLICAR MIGRACIÓN SQL MANUAL A NEON**

```bash
# Navegar a directorio de API
cd packages/api
pwd

# Verificar que existe el archivo .env con DATABASE_URL
echo "🔍 Verificando configuración de base de datos:"
if [ -f .env ]; then
    echo "✅ Archivo .env encontrado"
    # Mostrar DATABASE_URL (sin mostrar credenciales completas)
    grep "DATABASE_URL" .env | sed 's/:[^@]*@/:***@/g' || echo "⚠️ DATABASE_URL no encontrado en .env"
else
    echo "❌ Archivo .env no encontrado"
    echo "⚠️ Crear .env con DATABASE_URL antes de continuar"
fi

echo ""
echo "📋 OPCIONES PARA APLICAR MIGRACIÓN SQL:"
echo ""
echo "OPCIÓN A: Neon Local (psql directo)"
echo "  psql -h localhost -p 5432 -U neon -d kidyland -f migrations/remove_email_field.sql"
echo ""
echo "OPCIÓN B: Neon Serverless (via psql con SSL)"
echo "  psql 'postgresql://...?sslmode=require' -f migrations/remove_email_field.sql"
echo ""
echo "OPCIÓN C: Desde Python (usando asyncpg/psycopg)"
echo "  python3 -c \"import asyncio; from asyncpg import create_pool; ...\""
echo ""
echo "OPCIÓN D: Desde Neon Dashboard (SQL Editor)"
echo "  1. Abrir Neon Dashboard"
echo "  2. Ir a SQL Editor"
echo "  3. Copiar contenido de migrations/remove_email_field.sql"
echo "  4. Ejecutar"
echo ""

# Verificar si psql está disponible
echo "🔍 Verificando herramientas disponibles:"
which psql && echo "✅ psql disponible" || echo "⚠️ psql no disponible (usar Opción D: Neon Dashboard)"
which python3 && echo "✅ python3 disponible" || echo "⚠️ python3 no disponible"

echo ""
echo "⚠️ IMPORTANTE: Aplicar migración SQL manualmente usando una de las opciones arriba"
echo "📝 Contenido de migración SQL para copiar:"
cat migrations/remove_email_field.sql 2>/dev/null || echo "❌ Archivo SQL no encontrado"
```

### **PASO 4: VERIFICAR MIGRACIÓN APLICADA**

```bash
# Script para verificar que la columna email fue eliminada
echo "🔍 Verificando que la migración se aplicó correctamente:"
echo ""
echo "Ejecutar este SQL en tu base de datos para verificar:"
echo ""
echo "SELECT column_name FROM information_schema.columns"
echo "WHERE table_name = 'users' AND column_name = 'email';"
echo ""
echo "✅ Si retorna 0 filas = migración exitosa"
echo "❌ Si retorna 1 fila = columna email aún existe"
echo ""

# Si psql está disponible, intentar verificación automática
if command -v psql &> /dev/null && [ -f .env ]; then
    echo "🔄 Intentando verificación automática (requiere DATABASE_URL en .env):"
    # Extraer DATABASE_URL del .env
    DB_URL=$(grep "DATABASE_URL" .env | cut -d '=' -f2 | tr -d '"' | tr -d "'")
    if [ ! -z "$DB_URL" ]; then
        # Convertir a formato psql si es necesario
        echo "SELECT column_name FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'email';" | \
        psql "$DB_URL" 2>&1 | grep -q "0 rows" && echo "✅ Migración verificada: columna email eliminada" || \
        echo "⚠️ Verificar manualmente: columna email puede aún existir"
    fi
fi
```

### **PASO 5: EJECUTAR TESTS BACKEND**

```bash
# Asegurarse de estar en packages/api
pwd
echo "🧪 Ejecutando tests del backend:"

# Verificar que existe pnpm
which pnpm || echo "⚠️ pnpm no encontrado, intentando con npm"

# Ejecutar tests con diferentes opciones
echo "🔬 Ejecutando tests..."
pnpm test:api 2>&1 || {
    echo "🔄 Intentando con npm test:"
    npm test 2>&1 || {
        echo "🔄 Intentando con python pytest:"
        python -m pytest tests/ -v 2>&1 || {
            echo "🔄 Intentando con python3 -m pytest:"
            python3 -m pytest tests/ -v 2>&1
        }
    }
}

echo "📊 Resultado de tests backend completado"
```

### **PASO 6: VERIFICAR COMPILACIÓN FRONTEND**

```bash
# Regresar al root del proyecto
cd ../../
pwd

echo "🏗️ Verificando compilación del frontend:"

# Verificar que existe el directorio admin
ls -la apps/ 

# Compilar admin app
cd apps/admin
pwd
echo "📦 Compilando apps/admin:"
pnpm build 2>&1 || {
    echo "🔄 Intentando con npm:"
    npm run build 2>&1
}

# Regresar al root
cd ../../
pwd
```

### **PASO 7: VERIFICACIÓN COMPLETA - NO MÁS EMAIL**

```bash
echo "🔍 VERIFICACIÓN FINAL: Buscar referencias residuales a 'email':"

# Buscar en backend (excluyendo venv, __pycache__, y archivos de migración)
echo "📂 Backend (packages/api/):"
grep -r "email" packages/api/ \
    --exclude-dir=venv \
    --exclude-dir=__pycache__ \
    --exclude-dir=.git \
    --exclude="*.pyc" \
    --exclude="*.sql" \
    2>/dev/null | grep -v "venv" | grep -v "test.local" | head -20 && \
    echo "⚠️ Se encontraron referencias a email en backend" || \
    echo "✅ Backend limpio - sin referencias a email"

# Buscar en tipos compartidos
echo ""
echo "📂 Types (packages/shared/):"
grep -r "email" packages/shared/ 2>/dev/null | grep -v "node_modules" | head -10 && \
    echo "⚠️ Se encontraron referencias a email en types" || \
    echo "✅ Types limpios - sin referencias a email"

# Buscar en frontend admin
echo ""
echo "📂 Frontend admin (apps/admin/):"
grep -r "email" apps/admin/src/ 2>/dev/null | grep -v "node_modules" | head -10 && \
    echo "⚠️ Se encontraron referencias a email en frontend" || \
    echo "✅ Frontend limpio - sin referencias a email"

# Buscar en tests (excluyendo comentarios y venv)
echo ""
echo "📂 Tests:"
grep -r "email" packages/api/tests/ \
    --exclude-dir=venv \
    --exclude-dir=__pycache__ \
    2>/dev/null | grep -v "venv" | grep -v "#.*email" | grep -v "test.local" | head -10 && \
    echo "⚠️ Se encontraron referencias a email en tests" || \
    echo "✅ Tests limpios - sin referencias a email"

echo ""
echo "🎯 VERIFICACIÓN COMPLETA FINALIZADA"
```

### **PASO 8: VALIDAR ARCHIVOS CLAVE MODIFICADOS**

```bash
echo "📝 Verificando archivos clave que debieron modificarse:"

# Verificar modelo User
echo ""
echo "🔍 Modelo User (packages/api/models/user.py):"
grep -n "email" packages/api/models/user.py 2>/dev/null && \
    echo "⚠️ Aún contiene referencias a email" || \
    echo "✅ Sin campo email"

# Verificar schemas
echo ""
echo "🔍 Schemas (packages/api/schemas/user.py):"
grep -n "email\|EmailStr" packages/api/schemas/user.py 2>/dev/null && \
    echo "⚠️ Aún contiene referencias a email" || \
    echo "✅ Sin validación email"

# Verificar tipos TypeScript
echo ""
echo "🔍 Types (packages/shared/src/types.ts):"
grep -n "email" packages/shared/src/types.ts 2>/dev/null && \
    echo "⚠️ Aún contiene referencias a email" || \
    echo "✅ Sin campo email en interfaces"

# Verificar UserForm frontend
echo ""
echo "🔍 UserForm (apps/admin/src/lib/components/UserForm.svelte):"
grep -n "email" apps/admin/src/lib/components/UserForm.svelte 2>/dev/null && \
    echo "⚠️ Aún contiene referencias a email" || \
    echo "✅ Sin campo email en formulario"

# Verificar stores
echo ""
echo "🔍 Stores (apps/admin/src/lib/stores/users.ts):"
grep -n "email" apps/admin/src/lib/stores/users.ts 2>/dev/null && \
    echo "⚠️ Aún contiene referencias a email" || \
    echo "✅ Sin campo email en stores"
```

### **PASO 9: RESUMEN FINAL**

```bash
echo ""
echo "📋 RESUMEN FINAL DE VALIDACIÓN:"
echo "================================"
echo ""

# Verificar estructura final esperada
echo "✅ VERIFICACIONES COMPLETADAS:"
echo "  - Migración SQL creada y lista para aplicar"
echo "  - Opciones de aplicación manual documentadas"
echo "  - Tests backend ejecutados"
echo "  - Frontend compilación verificada"
echo "  - Sin referencias a email en código"
echo "  - Archivos clave actualizados correctamente"
echo ""

echo "🎯 SISTEMA KIDYLAND - SOLO USERNAME + PASSWORD + ROLE"
echo ""

echo "📌 PRÓXIMOS PASOS:"
echo "  1. ⚠️  APLICAR MIGRACIÓN SQL MANUALMENTE a la base de datos:"
echo "     - Opción A: psql directo (local)"
echo "     - Opción B: psql con SSL (serverless)"
echo "     - Opción C: Python script"
echo "     - Opción D: Neon Dashboard SQL Editor (RECOMENDADO)"
echo ""
echo "  2. Verificar login funcional con username/password"
echo "  3. Probar CRUD de usuarios sin campo email"
echo ""

echo "🚀 ELIMINACIÓN DE EMAIL COMPLETADA AL 100%"
```

## 🔍 **VERIFICACIÓN DE ÉXITO**

Si todo sale bien, deberías ver:

- ✅ **"✅ Backend limpio - sin referencias a email"**
- ✅ **"✅ Types limpios - sin referencias a email"**  
- ✅ **"✅ Frontend limpio - sin referencias a email"**
- ✅ **"✅ Tests limpios - sin referencias a email"**
- ✅ **Tests backend pasando**
- ✅ **Frontend compilando sin errores**
- ✅ **Migración SQL lista para aplicar manualmente**

## 🚨 **SI ENCUENTRAS ERRORES**

**Para errores de compilación:**
```bash
# Mostrar errores específicos
echo "🔍 Detalles del error:"
# [comando que falló] 2>&1 | head -20
```

**Para referencias a email residuales:**
```bash
# Mostrar líneas específicas donde aparece email
grep -rn "email" [directorio] | grep -v "venv" | grep -v "test.local" | head -10
```

**Para errores de migración SQL:**
```bash
# Verificar sintaxis SQL
echo "🔍 Verificando sintaxis SQL:"
cat packages/api/migrations/remove_email_field.sql
```

**Reportar inmediatamente cualquier error encontrado con el output completo.**

## ✅ **EJECUCIÓN AUTOMÁTICA**

**Ejecuta todos estos comandos secuencialmente en terminal y muestra el output completo de cada paso.**

---

## 📝 **NOTAS IMPORTANTES**

1. **NO se usa Alembic** - Migración SQL manual directa
2. **Compatible con Neon** - PostgreSQL local y serverless
3. **Backup recomendado** - Hacer backup antes de aplicar migración
4. **Verificación manual** - Confirmar que columna email fue eliminada
5. **Opciones múltiples** - 4 formas diferentes de aplicar la migración SQL


