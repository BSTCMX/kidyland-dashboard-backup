# 📝 Notas Pre-Deploy - Kidyland

**IMPORTANTE:** Leer antes del primer deploy a Fly.io

---

## 🔧 Ajustes Requeridos en Código

### Backend (FastAPI)

#### ✅ Ya Configurado

El `Dockerfile.api` ya está configurado para:
- Escuchar en `0.0.0.0` (requerido por Fly.io)
- Usar variable de entorno `PORT` (inyectada por Fly.io)
- Health check en `/health`

**Comando en Dockerfile:**
```dockerfile
CMD ["sh", "-c", "uvicorn packages.api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
```

**No requiere cambios en código Python.**

---

### Frontend (SvelteKit)

#### ⚠️ Requiere Ajustes

**Problema:** SvelteKit adapter-node debe configurarse para:
1. Escuchar en `0.0.0.0` (no solo localhost)
2. Usar `process.env.PORT` (inyectado por Fly.io)

#### Solución: Configurar adapter-node

**Archivo:** `apps/admin/svelte.config.js` (o `svelte.config.ts`)

```javascript
import adapter from '@sveltejs/adapter-node';

export default {
  kit: {
    adapter: adapter({
      out: 'build',
      precompress: false,
      envPrefix: '',
    }),
  },
};
```

**Archivo:** `apps/admin/src/hooks.server.ts` (o crear si no existe)

```typescript
// Asegurar que el servidor escucha en 0.0.0.0
// Esto se maneja automáticamente por adapter-node, pero verificar
```

**Archivo:** `apps/admin/src/server.js` (o donde se inicializa el servidor)

Si adapter-node genera un servidor personalizado, asegurar:

```javascript
const port = process.env.PORT || 3000;
const host = '0.0.0.0'; // IMPORTANTE para Fly.io

server.listen(port, host, () => {
  console.log(`Server listening on ${host}:${port}`);
});
```

**Nota:** adapter-node debería manejar esto automáticamente, pero verificar en la documentación de SvelteKit 1.30.x.

---

## 🔐 Variables de Entorno Requeridas

### Backend

Configurar en Fly.io antes del deploy:

```bash
fly secrets set DATABASE_URL="postgresql://user:pass@host:port/db?sslmode=require"
fly secrets set SECRET_KEY="tu-secret-key-seguro"
fly secrets set ENVIRONMENT="production"
```

### Frontend

Si el frontend necesita variables de entorno:

```bash
fly secrets set PUBLIC_API_URL="https://kidyland-api.fly.dev"
```

**Nota:** Variables con prefijo `PUBLIC_` son accesibles en el cliente (SvelteKit).

---

## 🐳 Dockerfile Considerations

### Backend

- ✅ Multi-stage build implementado
- ✅ Compiladores eliminados en runtime
- ✅ Usuario no-root
- ✅ Health check configurado
- ✅ PORT env variable

### Frontend

- ✅ Multi-stage build implementado
- ✅ Solo build output en runtime
- ✅ Usuario no-root
- ✅ Health check configurado
- ⚠️ Verificar que adapter-node respeta PORT env

---

## 🚀 Comandos de Deploy

### Primera Vez

```bash
# 1. Verificar flyctl
fly version

# 2. Verificar configuración (sin deploy)
fly config validate --config infra/fly/fly.toml

# 3. Verificar entorno
fly doctor

# 4. Inicializar app (solo primera vez)
fly launch --config infra/fly/fly.toml

# 5. Configurar secrets
fly secrets set DATABASE_URL="..."
fly secrets set SECRET_KEY="..."
fly secrets set ENVIRONMENT="production"

# 6. Deploy con debug (primera vez)
LOG_LEVEL=debug fly deploy --config infra/fly/fly.toml --dockerfile infra/docker/Dockerfile.api
```

### Deploys Subsecuentes

```bash
# Deploy normal
fly deploy --config infra/fly/fly.toml

# Deploy con logs en tiempo real
fly deploy --config infra/fly/fly.toml && fly logs
```

---

## 🔍 Validación Post-Deploy

### Verificar Estado

```bash
# Estado de máquinas
fly status

# Logs en tiempo real
fly logs

# Logs de una máquina específica
fly machine logs <machine-id>
```

### Verificar Health Checks

```bash
# Health check endpoint
curl https://kidyland-api.fly.dev/health

# Debe retornar: {"status": "ok"}
```

### SSH para Debug

```bash
# Conectar a máquina
fly ssh console

# Dentro de la máquina, verificar:
# - Variables de entorno: env | grep PORT
# - Proceso corriendo: ps aux
# - Logs: cat /var/log/...
```

---

## ⚠️ Troubleshooting

### Health Checks Failing

**Síntomas:**
- `fly status` muestra health checks fallando
- App no responde en `/health`

**Soluciones:**
1. Aumentar `grace_period` en `fly.toml`:
   ```toml
   [[http_service.checks]]
     grace_period = "15s"  # Aumentar de 10s
   ```

2. Verificar que app escucha en `0.0.0.0`:
   ```bash
   fly ssh console
   netstat -tlnp | grep 8000
   # Debe mostrar: 0.0.0.0:8000
   ```

3. Verificar que `internal_port` coincide:
   ```toml
   [http_service]
     internal_port = 8000  # Debe coincidir con PORT env
   ```

### Build Fails

**Síntomas:**
- Build falla durante `pip install` o compilación

**Soluciones:**
1. Verificar que compiladores están en build stage
2. Verificar logs de build: `fly logs --build`
3. Verificar que Rust está instalado (para cryptography)

### App No Inicia

**Síntomas:**
- Máquina creada pero app no responde

**Soluciones:**
1. Verificar logs: `fly logs`
2. Verificar variables de entorno: `fly secrets list`
3. SSH y verificar proceso: `fly ssh console`
4. Verificar que PORT env está disponible

---

## 📋 Checklist Pre-Deploy Final

- [ ] flyctl instalado y actualizado
- [ ] `fly doctor` ejecutado sin errores críticos
- [ ] `fly config validate` pasa sin errores
- [ ] Secrets configurados en Fly.io
- [ ] Código frontend ajustado para PORT env (si necesario)
- [ ] Dockerfiles probados localmente (opcional)
- [ ] Health checks configurados correctamente
- [ ] `internal_port` coincide con app
- [ ] App escucha en `0.0.0.0`

---

## ✅ Estado Actual

**🟡 CONFIGURACIÓN LISTA - PENDIENTE DE DEPLOY**

- ✅ Dockerfiles optimizados
- ✅ fly.toml configurado
- ✅ Dependencias validadas
- ⚠️ Pendiente: Configurar secrets
- ⚠️ Pendiente: Ajustar código frontend (si necesario)
- ⚠️ Pendiente: Ejecutar deploy

---

**Última actualización:** Diciembre 2025
































