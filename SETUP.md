# Setup Guide - Kidyland Monorepo

Guía completa para configurar el monorepo Kidyland con todas las herramientas de calidad.

## 📋 Prerrequisitos

- Node.js >= 18.20.0 (detectado: v18.20.8)
- pnpm >= 8.15.0 (detectado: 8.15.0)
- Python 3.13+ (detectado: 3.13.7)

**⚠️ IMPORTANTE:** Este proyecto está configurado para funcionar **100% localmente**. No se requiere instalar nada globalmente.

## 🚀 Instalación Inicial

### 0. Verificar compatibilidad del entorno

```bash
# Ejecutar script de verificación
./scripts/check-env.sh
```

Este script verifica que tu entorno sea compatible con el proyecto.

### 1. Instalar dependencias del monorepo (LOCAL)

```bash
# Desde la raíz del proyecto
pnpm install
```

Esto instalará **localmente** (en `node_modules/`):
- Todas las dependencias de frontend (ESLint, Prettier, TypeScript, etc.)
- Husky para Git hooks
- commitlint para validación de commits
- **NO se instala nada globalmente**

### 2. Instalar dependencias del backend (LOCAL en venv)

```bash
cd packages/api

# Crear entorno virtual LOCAL (obligatorio)
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias de producción (LOCAL en venv)
pip install -r requirements.txt

# Instalar dependencias de desarrollo (LOCAL en venv)
pip install -r requirements-dev.txt
```

**⚠️ Importante:** Todo se instala en `packages/api/venv/`. No se toca Python global ni pip global.

### 3. Configurar Git hooks (LOCAL)

```bash
# Desde la raíz
pnpm prepare
```

Esto configurará Husky con los hooks:
- `pre-commit` - Ejecuta lint-staged
- `pre-push` - Ejecuta validación completa
- `commit-msg` - Valida formato de commits

### 4. Verificar instalación

```bash
# Verificar que todo funciona
pnpm validate

# Verificar backend
pnpm lint:api
pnpm typecheck:api
```

## ✅ Verificación

Después de la instalación, verifica:

1. **Frontend tools**:
   ```bash
   pnpm lint
   pnpm format
   pnpm typecheck
   ```

2. **Backend tools**:
   ```bash
   pnpm lint:api
   pnpm format:api
   pnpm typecheck:api
   ```

3. **Git hooks**:
   ```bash
   # Hacer un cambio y commitear
   echo "test" > test.txt
   git add test.txt
   git commit -m "test: verify hooks"
   # Debería ejecutar lint-staged automáticamente
   ```

## 🔧 Configuración de Editor

### VS Code

Recomendado instalar extensiones:
- ESLint
- Prettier
- Svelte for VS Code
- Python
- EditorConfig for VS Code

Configuración recomendada en `.vscode/settings.json`:
```json
{
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": true
  },
  "[svelte]": {
    "editor.defaultFormatter": "svelte.svelte-vscode"
  },
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter",
    "editor.formatOnSave": true
  }
}
```

## 🚀 Deployment en Fly.io

Este proyecto está configurado para deployment en Fly.io usando Alpine Linux 3.20.

### Preparación

1. **Verificar Dockerfiles:**
   - Backend: `infra/docker/Dockerfile.api`
   - Frontend: `infra/docker/Dockerfile.web`

2. **Configurar Fly.io:**
   ```bash
   fly launch
   # Seguir instrucciones interactivas
   ```

3. **Deploy:**
   ```bash
   # Backend
   fly deploy --dockerfile infra/docker/Dockerfile.api
   
   # Frontend (ajustar según app)
   fly deploy --dockerfile infra/docker/Dockerfile.web
   ```

Ver [COMPATIBILITY_ALPINE_FLYIO_2025.md](./COMPATIBILITY_ALPINE_FLYIO_2025.md) para detalles completos.

## 📚 Próximos Pasos

- Lee [QUALITY_TOOLS.md](./QUALITY_TOOLS.md) para entender todas las herramientas
- Lee [PNPM_GUIDE.md](./PNPM_GUIDE.md) para comandos de pnpm
- Lee [COMPATIBILITY_ALPINE_FLYIO_2025.md](./COMPATIBILITY_ALPINE_FLYIO_2025.md) para deployment
- Lee [README.md](./README.md) para información general del monorepo

## 🐛 Troubleshooting

### pnpm install falla

```bash
# Limpiar cache
pnpm store prune

# Reinstalar
rm -rf node_modules pnpm-lock.yaml
pnpm install
```

### Git hooks no funcionan

```bash
# Reinstalar hooks
pnpm prepare

# Verificar permisos
chmod +x .husky/*/.husky/_/husky.sh
```

### Python tools no se encuentran

Asegúrate de estar en el entorno virtual:
```bash
cd packages/api
source venv/bin/activate  # O venv\Scripts\activate en Windows
```

