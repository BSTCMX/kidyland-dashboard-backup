# ✅ Checklist de Preparación Fly.io - Kidyland

**Estado:** 🟡 **PENDIENTE DE DEPLOY**  
**Fecha:** Diciembre 2025

---

## 📋 Pre-Deploy Checklist

### 1. Verificación de Entorno Local

- [x] Node.js 18.20.8 detectado
- [x] Python 3.13.7 detectado
- [x] pnpm 8.15.0 detectado
- [x] macOS 12.7.6 compatible
- [x] Arquitectura Intel x86_64 compatible

### 2. Compatibilidad Alpine 3.20

- [x] Backend: Python 3.12.x compatible
- [x] Frontend: Node.js 18.x compatible
- [x] Todas las dependencias validadas
- [x] psycopg2-binary → asyncpg (reemplazado)
- [x] Multi-stage builds configurados

### 3. Dockerfiles

#### Backend (`infra/docker/Dockerfile.api`)

- [x] Base: `python:3.12-alpine3.20`
- [x] Multi-stage build implementado
- [x] Compiladores en build stage
- [x] Compiladores eliminados en runtime
- [x] Usuario no-root configurado
- [x] Health check configurado
- [x] Escucha en `0.0.0.0` y `PORT` env
- [x] Variables de entorno correctas

#### Frontend (`infra/docker/Dockerfile.web`)

- [x] Base: `node:18-alpine3.20`
- [x] Multi-stage build implementado
- [x] pnpm 8.15.0 configurado
- [x] Build de SvelteKit configurado
- [x] Usuario no-root configurado
- [x] Health check configurado
- [x] Escucha en `0.0.0.0` y `PORT` env
- [x] Adapter-node compatible

### 4. Fly.io Configuration (`infra/fly/fly.toml`)

- [x] App name configurado
- [x] Primary region configurado
- [x] Dockerfile path correcto
- [x] Build target correcto (`runtime`)
- [x] `internal_port` configurado (8000 backend, 3000 frontend)
- [x] Health checks configurados
- [x] Grace period adecuado (10s)
- [x] Auto-start/stop configurado
- [x] HTTPS forzado
- [x] Variables de entorno documentadas

### 5. Código de Aplicación

#### Backend

- [x] Health check endpoint: `/health`
- [x] Escucha en `0.0.0.0` (configurado en CMD)
- [x] Usa `PORT` env variable
- [x] Sin hardcoded ports

#### Frontend

- [ ] ⚠️ **PENDIENTE:** Configurar adapter-node para usar `PORT` env
- [ ] ⚠️ **PENDIENTE:** Configurar host `0.0.0.0` en adapter-node
- [x] Build output en `build/` directory

### 6. Dependencias

#### Backend (`packages/api/requirements.txt`)

- [x] fastapi==0.115.0
- [x] uvicorn[standard]==0.32.0
- [x] asyncpg==0.29.0 (reemplazo de psycopg2-binary)
- [x] Todas las dependencias compatibles con Alpine

#### Frontend

- [x] SvelteKit 1.30.x (compatible con Node 18)
- [x] Svelte 4.2.x
- [x] Vite 5.4.x
- [x] Todas las dependencias compatibles

### 7. Documentación

- [x] `ALPINE_COMPATIBILITY.md` creado
- [x] `FLY_READY_CHECKLIST.md` creado (este archivo)
- [x] `PRE_DEPLOY_NOTES.md` creado
- [x] `ENV_ANALYSIS.md` actualizado
- [x] READMEs actualizados

---

## 🔍 Comandos de Validación (Solo Lectura)

### Verificar flyctl

```bash
# Verificar versión
fly version

# Verificar configuración (sin deploy)
fly config validate --config infra/fly/fly.toml

# Verificar entorno (sin deploy)
fly doctor
```

### Validar Dockerfiles Localmente (Opcional)

```bash
# Lint Dockerfile (sin build completo)
docker run --rm -i hadolint/hadolint < infra/docker/Dockerfile.api
docker run --rm -i hadolint/hadolint < infra/docker/Dockerfile.web
```

---

## ⚠️ Acciones Pendientes ANTES de Deploy

### 1. Configurar Variables de Entorno en Fly.io

```bash
# Estas deben configurarse ANTES del primer deploy
fly secrets set DATABASE_URL="postgresql://..."
fly secrets set SECRET_KEY="..."
fly secrets set ENVIRONMENT="production"
```

### 2. Ajustar Código Frontend

**Archivo:** `apps/admin/src/hooks.server.ts` o similar

```typescript
// Asegurar que adapter-node use PORT y 0.0.0.0
export const handle = async ({ event, resolve }) => {
  // ... código existente
};

// En svelte.config.js, verificar adapter-node config:
// adapter: adapter({
//   out: 'build',
//   precompress: false,
//   envPrefix: '',
// })
```

**Verificar:** El servidor debe escuchar en `0.0.0.0` y usar `process.env.PORT`

### 3. Probar Build Localmente (Opcional)

```bash
# Backend (solo para verificar que compila)
docker build -f infra/docker/Dockerfile.api -t kidyland-api-test .

# Frontend (solo para verificar que compila)
docker build -f infra/docker/Dockerfile.web -t kidyland-admin-test .
```

---

## 🚀 Comandos de Deploy (NO EJECUTAR AÚN)

### Primera Vez

```bash
# 1. Inicializar app (solo primera vez)
fly launch --config infra/fly/fly.toml

# 2. Configurar secrets
fly secrets set DATABASE_URL="..."
fly secrets set SECRET_KEY="..."

# 3. Deploy con debug
LOG_LEVEL=debug fly deploy --config infra/fly/fly.toml --dockerfile infra/docker/Dockerfile.api
```

### Deploys Subsecuentes

```bash
# Deploy normal
fly deploy --config infra/fly/fly.toml

# Deploy con logs
fly deploy --config infra/fly/fly.toml && fly logs
```

---

## 🔍 Post-Deploy Verification

### Verificar Estado

```bash
# Ver estado de máquinas
fly status

# Ver logs
fly logs

# SSH a máquina (debug)
fly ssh console
```

### Verificar Health Checks

```bash
# Verificar health check endpoint
curl https://kidyland-api.fly.dev/health
```

---

## ⚠️ Troubleshooting Común

### Health Checks Failing

1. Aumentar `grace_period` en `fly.toml` (actual: 10s)
2. Verificar que app escucha en `0.0.0.0`
3. Verificar que `internal_port` coincide con app
4. Revisar logs: `fly logs`

### Build Fails

1. Verificar que compiladores están en build stage
2. Verificar que Rust está instalado (para cryptography)
3. Revisar logs de build: `fly logs --build`

### Runtime Errors

1. Verificar variables de entorno: `fly secrets list`
2. Verificar que PORT env está disponible
3. SSH y verificar: `fly ssh console`

---

## ✅ Estado Final

**🟡 LISTO PARA DEPLOY (Pendiente de acciones manuales)**

- ✅ Dockerfiles optimizados
- ✅ fly.toml configurado
- ✅ Dependencias validadas
- ⚠️ Pendiente: Configurar secrets en Fly.io
- ⚠️ Pendiente: Ajustar código frontend para PORT env
- ⚠️ Pendiente: Ejecutar deploy

---

**Última actualización:** Diciembre 2025
































