# Fly.io Infrastructure

Configuraciones de despliegue para fly.io.
Archivos de configuración para el despliegue y gestión de aplicaciones en la plataforma fly.io.

## 📋 Configuración

### fly.toml

**Archivo:** `fly.toml`

**Configuración para:**
- Backend API (FastAPI)
- Health checks configurados
- Auto-scaling habilitado
- HTTPS forzado

### Deployment

```bash
# Inicializar Fly.io (solo primera vez)
fly launch

# Deploy backend
fly deploy --dockerfile infra/docker/Dockerfile.api

# Ver logs
fly logs

# Escalar
fly scale count 2
```

## 🔧 Variables de Entorno

Configurar en Fly.io dashboard o vía CLI:

```bash
fly secrets set DATABASE_URL="postgresql://..."
fly secrets set SECRET_KEY="..."
fly secrets set ENVIRONMENT="production"
```

## 📊 Monorepo Strategy

**Estrategia:** Múltiples apps (uno por servicio)

1. **Backend API:**
   - App: `kidyland-api`
   - Dockerfile: `infra/docker/Dockerfile.api`

2. **Frontend Apps:**
   - App: `kidyland-admin` (ejemplo)
   - Dockerfile: `infra/docker/Dockerfile.web`

## ✅ Health Checks

- Endpoint: `/health`
- Interval: 30s
- Timeout: 3s
- Grace period: 5s

## 🚀 Best Practices

1. **Regiones:**
   - Primary: `iad` (Washington D.C.)
   - Ajustar según ubicación de usuarios

2. **Scaling:**
   - Min machines: 1
   - Auto-start/stop habilitado

3. **Security:**
   - HTTPS forzado
   - Secrets en Fly.io secrets (no en código)
