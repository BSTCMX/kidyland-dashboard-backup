# Guía de pnpm para Kidyland

Este monorepo usa **pnpm** exclusivamente. NO uses npm o yarn.

## Instalación de pnpm

```bash
# Con npm (solo para instalar pnpm)
npm install -g pnpm

# O con Homebrew (macOS)
brew install pnpm

# O con curl
curl -fsSL https://get.pnpm.io/install.sh | sh -
```

## Comandos Básicos

### Instalación

```bash
# Instalar todas las dependencias del monorepo
pnpm install

# Instalar dependencia en un workspace específico
pnpm add <package> --filter <workspace-name>

# Instalar dependencia de desarrollo
pnpm add -D <package> --filter <workspace-name>

# Instalar dependencia en la raíz
pnpm add <package> -w
```

### Desarrollo

```bash
# Ejecutar backend
pnpm dev:api

# Ejecutar una app específica
pnpm --filter admin dev
pnpm --filter reception dev
pnpm --filter kidibar dev

# Ejecutar backend + frontend
pnpm dev
```

### Workspaces

```bash
# Listar todos los workspaces
pnpm -r list

# Ejecutar comando en todos los workspaces
pnpm -r <command>

# Ejecutar comando en workspace específico
pnpm --filter <workspace-name> <command>
```

## Crear Nueva App SvelteKit

```bash
# 1. Navegar a la carpeta de la app
cd apps/<app-name>

# 2. Crear proyecto SvelteKit con pnpm
pnpm create svelte@latest .

# 3. Instalar dependencias
pnpm install

# 4. Ejecutar en desarrollo
pnpm dev
```

## Agregar Dependencias Compartidas

```bash
# Agregar @kidyland/shared a una app
pnpm add @kidyland/shared --filter admin --workspace

# Agregar @kidyland/ui a una app
pnpm add @kidyland/ui --filter admin --workspace
```

## Estructura de Workspaces

Los workspaces están definidos en `pnpm-workspace.yaml`:

- `apps/*` - Aplicaciones SvelteKit
- `packages/*` - Paquetes compartidos

## Configuración

El archivo `.npmrc` en la raíz configura pnpm:

- `shamefully-hoist=false` - Mantiene estructura de node_modules estricta
- `strict-peer-dependencies=false` - Permite dependencias peer flexibles
- `auto-install-peers=true` - Instala automáticamente peer dependencies

## Migración desde npm/yarn

Si encuentras referencias a npm o yarn en el proyecto:

1. Reemplaza `npm install` → `pnpm install`
2. Reemplaza `npm run` → `pnpm run` o solo `pnpm`
3. Reemplaza `yarn add` → `pnpm add`
4. Reemplaza `yarn dev` → `pnpm dev`

## Troubleshooting

### Limpiar cache

```bash
pnpm store prune
```

### Reinstalar todo

```bash
rm -rf node_modules
rm pnpm-lock.yaml
pnpm install
```

### Verificar versión

```bash
pnpm --version
```

Debe ser >= 8.0.0
































