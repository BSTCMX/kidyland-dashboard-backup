# Herramientas de Calidad de Código

Este monorepo está configurado con herramientas de calidad de código para mantener estándares y consistencia.

**Versiones Configuradas (2025):**
- **Frontend:** SvelteKit 1.30.x, Svelte 4.2.x, TypeScript 5.6+, ESLint 9.x, Prettier 3.3.x
- **Backend:** Python 3.13.7, FastAPI 0.115+, ruff 0.6+, black 24.10+, mypy 1.11+
- **Node.js:** >= 18.20.0 (compatible con SvelteKit 1.x)

**Nota:** Usamos SvelteKit 1.30.x porque requiere Node.js >= 18.20.0. Para SvelteKit 2.x necesitarías Node.js >= 20.0.0.

## 🛠️ Herramientas Instaladas

### Frontend (TypeScript/Svelte)

- **ESLint** - Linting de código
- **Prettier** - Formateo automático
- **TypeScript** - Type checking en modo strict
- **svelte-check** - Validación de componentes Svelte

### Backend (Python)

- **ruff** - Linter rápido para Python
- **black** - Formateador de código Python
- **mypy** - Type checking estático

### Git Hooks

- **Husky** - Git hooks
- **lint-staged** - Ejecutar linters solo en archivos staged
- **commitlint** - Validación de mensajes de commit (Conventional Commits)

## 📋 Comandos Disponibles

### Desde la raíz del monorepo

```bash
# Linting
pnpm lint              # Lint en todos los workspaces
pnpm lint:fix          # Lint y auto-fix en todos los workspaces

# Formateo
pnpm format            # Formatear código en todos los workspaces

# Type checking
pnpm typecheck         # Type check en todos los workspaces

# Validación completa
pnpm validate          # Ejecuta lint + typecheck

# Backend específico
pnpm lint:api          # Lint del backend (ruff)
pnpm format:api         # Formatear backend (ruff + black)
pnpm typecheck:api      # Type check del backend (mypy)
```

### Desde un workspace específico

```bash
# Ejecutar en un workspace
pnpm --filter <workspace-name> lint
pnpm --filter <workspace-name> lint:fix
pnpm --filter <workspace-name> format
pnpm --filter <workspace-name> typecheck
```

## 🔧 Configuraciones

### TypeScript

- **Modo strict activado** en `tsconfig.json` raíz
- Todas las apps/packages extienden esta configuración
- Reglas estrictas: no `any`, no `unknown` no controlado, exhaustiveness checking

### ESLint

- Configuración en `.eslintrc.cjs` (raíz)
- Reglas para TypeScript, Svelte, e imports
- Cada app SvelteKit debe tener su propio `.eslintrc.cjs` que extienda la raíz

### Prettier

- Configuración en `.prettierrc` y `prettier.config.cjs`
- Plugins para Svelte
- Reglas estrictas de espacios, comillas y longitud de línea

### Python (Backend)

- Configuración unificada en `packages/api/pyproject.toml`
- ruff: linting rápido
- black: formateo
- mypy: type checking estricto

## 🪝 Git Hooks

### Pre-commit

Ejecuta automáticamente:
- ESLint en archivos JS/TS/Svelte staged
- Prettier en todos los archivos staged
- svelte-check en apps SvelteKit
- ruff + black en archivos Python

### Pre-push

Ejecuta:
- `pnpm validate` (lint + typecheck completo)

### Commit-msg

Valida que los mensajes de commit sigan Conventional Commits:
- `feat:`, `fix:`, `docs:`, `style:`, `refactor:`, `perf:`, `test:`, `build:`, `ci:`, `chore:`, `revert:`

Ejemplos:
```
feat(admin): add user management page
fix(api): resolve database connection issue
docs(readme): update installation instructions
```

## 📝 Agregar Herramientas a Nueva App SvelteKit

Cuando crees una nueva app SvelteKit:

1. **Copiar configuraciones**:
   ```bash
   cp templates/eslintrc.cjs apps/<app-name>/.eslintrc.cjs
   cp templates/tsconfig.json apps/<app-name>/tsconfig.json
   ```

2. **Agregar scripts** al `package.json` de la app (ver `templates/package.json`)

3. **Instalar dependencias**:
   ```bash
   pnpm install
   ```

## 🚫 Ignorar Archivos

Los siguientes archivos están ignorados por los linters:
- `node_modules/`
- `dist/`, `build/`, `.svelte-kit/`
- `__pycache__/`, `*.pyc`
- Archivos de configuración

Ver `.eslintignore` y `.prettierignore` para la lista completa.

## 🔍 Troubleshooting

### ESLint no encuentra módulos

Asegúrate de que cada app tenga su propio `.eslintrc.cjs` que extienda la configuración raíz.

### Prettier no formatea archivos Svelte

Verifica que `prettier-plugin-svelte` esté instalado en el workspace.

### mypy falla en imports

Algunos módulos externos pueden necesitar type stubs. Agrega `ignore_missing_imports = true` en `pyproject.toml` para esos módulos específicos.

### Husky no ejecuta hooks

Ejecuta:
```bash
pnpm prepare
```

Esto reinstala los hooks de Husky.

