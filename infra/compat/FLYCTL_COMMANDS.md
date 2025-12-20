# 🚀 Comandos flyctl - Referencia Rápida

**IMPORTANTE:** Estos comandos son solo para referencia. NO se ejecutarán automáticamente.

---

## 🔍 Comandos de Validación (Solo Lectura)

### Verificar Versión

```bash
fly version
```

**Salida esperada:**
```
flyctl v0.x.x
```

### Verificar Configuración

```bash
# Validar fly.toml sin deploy
fly config validate --config infra/fly/fly.toml
```

**Qué verifica:**
- Sintaxis del archivo
- Campos requeridos
- Tipos de datos
- Referencias válidas

### Verificar Entorno

```bash
# Diagnóstico completo del entorno
fly doctor
```

**Qué verifica:**
- Conexión a Fly.io
- WireGuard configurado
- Autenticación
- Docker disponible (opcional, no requerido para Fly Builder)
- Variables de entorno locales

**Si falla:**
- Revisar autenticación: `fly auth whoami`
- Revisar WireGuard: `fly wireguard status`
- Revisar configuración de red

---

## 📋 Comandos de Inspección (Solo Lectura)

### Ver Estado de App

```bash
# Estado general
fly status

# Estado detallado
fly status --all
```

### Ver Logs

```bash
# Logs en tiempo real
fly logs

# Logs de build
fly logs --build

# Logs de una máquina específica
fly machine logs <machine-id>
```

### Ver Configuración

```bash
# Ver configuración actual
fly config show

# Ver secrets (nombres, no valores)
fly secrets list
```

### SSH a Máquina

```bash
# Conectar a máquina
fly ssh console

# Ejecutar comando específico
fly ssh console -C "env | grep PORT"
```

---

## 🚀 Comandos de Deploy (NO EJECUTAR AÚN)

### Primera Vez

```bash
# 1. Inicializar app (solo primera vez)
fly launch --config infra/fly/fly.toml

# 2. Configurar secrets
fly secrets set DATABASE_URL="postgresql://..."
fly secrets set SECRET_KEY="..."
fly secrets set ENVIRONMENT="production"

# 3. Deploy con debug (recomendado primera vez)
LOG_LEVEL=debug fly deploy --config infra/fly/fly.toml --dockerfile infra/docker/Dockerfile.api
```

### Deploys Subsecuentes

```bash
# Deploy normal
fly deploy --config infra/fly/fly.toml

# Deploy con logs
fly deploy --config infra/fly/fly.toml && fly logs

# Deploy forzando rebuild
fly deploy --config infra/fly/fly.toml --no-cache
```

---

## 🔧 Comandos de Configuración

### Secrets

```bash
# Agregar secret
fly secrets set KEY="value"

# Agregar múltiples secrets
fly secrets set KEY1="value1" KEY2="value2"

# Ver secrets (nombres)
fly secrets list

# Eliminar secret
fly secrets unset KEY
```

### Variables de Entorno

```bash
# Variables de entorno (no secretas)
# Se configuran en fly.toml bajo [env]
# O vía:
fly config env set KEY="value"
```

---

## 🐛 Troubleshooting

### Si Health Checks Fallan

```bash
# 1. Ver logs
fly logs

# 2. SSH y verificar
fly ssh console
# Dentro: netstat -tlnp | grep 8000
# Dentro: env | grep PORT

# 3. Verificar configuración
fly config show
```

### Si Build Falla

```bash
# 1. Ver logs de build
fly logs --build

# 2. Verificar Dockerfile
fly config validate --config infra/fly/fly.toml

# 3. Rebuild sin cache
fly deploy --config infra/fly/fly.toml --no-cache
```

### Si App No Inicia

```bash
# 1. Ver logs
fly logs

# 2. Ver estado
fly status

# 3. Verificar secrets
fly secrets list

# 4. SSH y debug
fly ssh console
```

---

## 📊 Comandos de Monitoreo

### Ver Métricas

```bash
# Métricas de app
fly metrics

# Métricas de máquina específica
fly machine status <machine-id>
```

### Ver Escalado

```bash
# Ver configuración de escalado
fly scale show

# Ver máquinas
fly machine list
```

---

## ⚠️ Comandos NO Permitidos (Solo Referencia)

Estos comandos NO se ejecutarán automáticamente:

- ❌ `fly deploy` - Requiere acción manual
- ❌ `fly machine create` - Requiere acción manual
- ❌ `fly scale count` - Requiere acción manual
- ❌ `fly apps create` - Requiere acción manual
- ❌ `fly secrets set` - Requiere acción manual

---

## ✅ Checklist de Comandos Pre-Deploy

Antes del primer deploy, ejecutar:

- [ ] `fly version` - Verificar versión
- [ ] `fly doctor` - Verificar entorno
- [ ] `fly config validate --config infra/fly/fly.toml` - Validar configuración
- [ ] `fly auth whoami` - Verificar autenticación
- [ ] Configurar secrets manualmente
- [ ] Ejecutar deploy manualmente

---

**Última actualización:** Diciembre 2025
































