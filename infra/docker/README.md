# Docker Infrastructure

Dockerfiles y configuraciones de runtime para contenedores.
Definiciones de imágenes Docker y configuraciones para el entorno de ejecución.

## 🐳 Dockerfiles Disponibles

### Backend (FastAPI)

**Archivo:** `Dockerfile.api`

**Base:** `python:3.12-alpine3.20`

**Características:**
- ✅ Optimizado para Alpine Linux 3.20 (musl libc)
- ✅ Python 3.12.x (compatible con Alpine 3.20)
- ✅ Compiladores incluidos para dependencias que requieren build
- ✅ Usuario no-root para seguridad
- ✅ Health check configurado
- ✅ Multi-stage build para reducir tamaño

**Uso:**
```bash
# Build
docker build -f infra/docker/Dockerfile.api -t kidyland-api .

# Run
docker run -p 8000:8000 kidyland-api
```

### Frontend (SvelteKit)

**Archivo:** `Dockerfile.web`

**Base:** `node:18-alpine3.20`

**Características:**
- ✅ Node.js 18.x en Alpine
- ✅ pnpm 8.15.0
- ✅ SvelteKit 1.30.x compatible
- ✅ Usuario no-root
- ✅ Build optimizado para producción
- ✅ Health check configurado

**Uso:**
```bash
# Build (ajustar app name)
docker build -f infra/docker/Dockerfile.web -t kidyland-admin .

# Run
docker run -p 3000:3000 kidyland-admin
```

## 🔧 Configuración para Fly.io

Ver `../fly/fly.toml` para configuración de Fly.io.

## 📝 Notas Importantes

### Backend

1. **Python 3.12 vs 3.13:**
   - Alpine 3.20 tiene Python 3.12.x en repositorios estables
   - Python 3.13 requiere repositorios edge o compilación desde source
   - **Decisión:** Usar Python 3.12.x para estabilidad

2. **psycopg2-binary → asyncpg:**
   - `psycopg2-binary` no funciona en musl (wheels para glibc)
   - **Solución:** Usar `asyncpg` (mejor para async, sin problemas musl)

3. **Compiladores:**
   - Se instalan durante build, luego se eliminan para reducir tamaño
   - Rust/Cargo necesarios para `cryptography`

### Frontend

1. **Adapter:**
   - Usar `@sveltejs/adapter-node` para SSR en Fly.io
   - Ajustar `Dockerfile.web` según el adapter usado

2. **Monorepo:**
   - Ajustar paths en Dockerfile según la app que se despliegue
   - Cada app puede tener su propio Dockerfile

## 🚀 Deployment

### Fly.io

```bash
# Backend
fly deploy --dockerfile infra/docker/Dockerfile.api

# Frontend (ajustar según app)
fly deploy --dockerfile infra/docker/Dockerfile.web
```

## 📊 Tamaños de Imágenes

- **Backend:** ~150MB (con dependencias)
- **Frontend:** ~250MB (con Node.js y dependencias)

## ✅ Compatibilidad

- ✅ Alpine Linux 3.20
- ✅ musl libc
- ✅ Fly.io
- ✅ Sin dependencias problemáticas
