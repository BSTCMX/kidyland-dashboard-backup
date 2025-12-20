# 🔺 Compatibilidad Alpine Linux 3.20 (musl libc) - 2025

**Base Image:** `alpine:3.20`  
**libc:** musl (no glibc)  
**Fecha:** Diciembre 2025

---

## 📊 Tabla de Compatibilidad de Dependencias

### Backend (Python 3.12.x)

| Paquete | Versión | Estado Wheel | Estado Build | Dependencias APK | Notas |
|---------|---------|--------------|--------------|------------------|-------|
| **fastapi** | 0.115.0 | ✅ Pure Python | ✅ OK | Ninguna | Sin problemas |
| **uvicorn** | 0.32.0 | ⚠️ Requiere build | ✅ OK | `gcc`, `musl-dev`, `python3-dev` | httptools compila bien |
| **pydantic** | 2.10.0 | ✅ Pure Python | ✅ OK | Ninguna | Sin problemas |
| **pydantic-settings** | 2.6.0 | ✅ Pure Python | ✅ OK | Ninguna | Sin problemas |
| **sqlalchemy** | 2.0.36 | ✅ Pure Python | ✅ OK | Ninguna | Sin problemas |
| **alembic** | 1.13.2 | ✅ Pure Python | ✅ OK | Ninguna | Sin problemas |
| **python-jose** | 3.3.0 | ✅ Pure Python | ✅ OK | Ninguna | Sin problemas |
| **cryptography** | (dep) | ⚠️ Requiere Rust | ✅ OK | `rust`, `cargo`, `libffi-dev`, `openssl-dev` | Compila con Rust |
| **passlib** | 1.7.4 | ✅ Pure Python | ✅ OK | Ninguna | Sin problemas |
| **python-multipart** | 0.0.6 | ⚠️ Requiere build | ✅ OK | `gcc`, `musl-dev`, `python3-dev` | Compila bien |
| **asyncpg** | 0.29.0 | ⚠️ Requiere build | ✅ OK | `gcc`, `musl-dev`, `postgresql-dev` | Mejor que psycopg2-binary |

### Frontend (Node.js 18.x)

| Paquete | Versión | Estado | Dependencias APK | Notas |
|---------|---------|--------|------------------|-------|
| **Node.js** | 18.x | ✅ Disponible | `nodejs`, `npm` | Repositorios Alpine |
| **pnpm** | 8.15.0 | ✅ Funciona | `corepack` (incluido) | Sin problemas |
| **SvelteKit** | 1.30.x | ✅ Compatible | Ninguna | Sin problemas musl |
| **Svelte** | 4.2.x | ✅ Compatible | Ninguna | Sin problemas |
| **Vite** | 5.4.x | ✅ Compatible | Ninguna | Sin problemas |
| **TypeScript** | 5.6+ | ✅ Compatible | Ninguna | Sin problemas |

---

## 🔧 Dependencias APK Necesarias

### Build Stage (temporal, se eliminan después)

```bash
# Compiladores C/C++
gcc
musl-dev
python3-dev
libffi-dev
openssl-dev

# PostgreSQL (para asyncpg)
postgresql-dev

# Rust (para cryptography)
rust
cargo
```

### Runtime Stage (permanentes)

```bash
# Runtime libraries
postgresql-libs

# Utilidades
curl
ca-certificates
```

---

## ⚠️ Problemas Conocidos y Soluciones

### 1. psycopg2-binary ❌

**Problema:**
- `psycopg2-binary` usa wheels precompilados para glibc
- No funciona en musl libc (Alpine)

**Solución Aplicada:**
- ✅ Reemplazado por `asyncpg==0.29.0`
- Mejor rendimiento para async
- Compila bien en musl

### 2. cryptography (Rust dependency)

**Problema:**
- Versiones recientes requieren Rust compiler
- Aumenta tiempo de build

**Solución Aplicada:**
- ✅ Instalar `rust` y `cargo` en build stage
- ✅ Eliminar después de build (multi-stage)
- ✅ Funciona correctamente

### 3. httptools (uvicorn dependency)

**Problema:**
- Requiere compilación C
- Necesita compiladores

**Solución Aplicada:**
- ✅ Instalar `gcc`, `musl-dev`, `python3-dev` en build stage
- ✅ Compila correctamente
- ✅ Eliminar después de build

### 4. python-multipart

**Problema:**
- Requiere compilación C

**Solución Aplicada:**
- ✅ Compila bien con compiladores instalados
- ✅ Sin problemas

---

## ✅ Dependencias 100% Compatibles (Sin Build)

Estas dependencias son Pure Python y no requieren compilación:

- ✅ fastapi
- ✅ pydantic
- ✅ pydantic-settings
- ✅ sqlalchemy
- ✅ alembic
- ✅ python-jose
- ✅ passlib

---

## 🚫 Dependencias que NO Funcionan en Alpine

### Binarios Precompilados para glibc

- ❌ `psycopg2-binary` → Reemplazado por `asyncpg`
- ❌ Cualquier wheel con `manylinux` (glibc) → Usar source o alternativas

---

## 📋 Checklist de Build

### Backend Build Stage

- [x] Instalar compiladores (gcc, musl-dev, python3-dev)
- [x] Instalar Rust/Cargo (para cryptography)
- [x] Instalar postgresql-dev (para asyncpg)
- [x] Instalar dependencias Python
- [x] Eliminar compiladores en runtime stage

### Frontend Build Stage

- [x] Instalar pnpm vía corepack
- [x] Instalar dependencias (incluyendo dev)
- [x] Build de SvelteKit
- [x] Copiar solo build output a runtime

---

## 🎯 Optimizaciones Aplicadas

1. **Multi-stage builds:**
   - Build stage: Compiladores y herramientas
   - Runtime stage: Solo runtime dependencies

2. **Eliminación de compiladores:**
   - Reducen tamaño de imagen final
   - Mejoran seguridad (menos superficie de ataque)

3. **Cache de layers:**
   - Requirements copiados primero
   - Código copiado después
   - Mejora tiempos de build

---

## ✅ Validación Final

**Estado:** ✅ **TODAS LAS DEPENDENCIAS COMPATIBLES**

- ✅ Backend: Todas las dependencias compilan/instalan correctamente
- ✅ Frontend: Sin problemas conocidos
- ✅ Sin dependencias problemáticas
- ✅ Multi-stage builds optimizados

---

**Última actualización:** Diciembre 2025
































