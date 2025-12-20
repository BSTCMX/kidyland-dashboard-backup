# Kidyland Monorepo

Monorepo para el sistema Kidyland gestionado con **pnpm**.

## 🚀 Inicio Rápido

### Prerrequisitos

- Node.js >= 18.20.0 (detectado: v18.20.8)
- pnpm >= 8.15.0 (detectado: 8.15.0)
- Python 3.13+ (detectado: 3.13.7)

**Nota:** Este proyecto está configurado para usar **SvelteKit 1.30.x** (compatible con Node 18). Para usar SvelteKit 2.x necesitarías Node.js >= 20.0.0.

### Instalación

```bash
# Verificar compatibilidad del entorno
./scripts/check-env.sh

# Instalar todas las dependencias del monorepo (LOCAL, no global)
pnpm install

# Configurar backend Python (LOCAL, en venv)
cd packages/api
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

**⚠️ Importante:** Este proyecto NO requiere instalaciones globales. Todo se instala localmente en el proyecto.

## 📦 Estructura del Monorepo

```
kidyland/
├── apps/              # Aplicaciones SvelteKit
│   ├── admin/         # Super Admin
│   ├── admin-viewer/  # Admin Viewer (read-only)
│   ├── reception/     # Panel de recepción
│   ├── kidibar/       # KidiBar product selling
│   └── monitor/       # Timer display
│
├── packages/          # Paquetes compartidos
│   ├── api/          # Backend FastAPI
│   ├── shared/       # Tipos TypeScript compartidos
│   └── ui/           # Componentes Svelte compartidos
│
├── infra/            # Configuración de infraestructura
│   ├── fly/          # fly.io deploy configs
│   └── docker/       # Dockerfiles
│
└── docs/             # Documentación
    ├── api-spec/     # OpenAPI specs
    └── ux/           # Wireframes y mockups
```

## 🛠️ Comandos Disponibles

### Desarrollo

```bash
# Ejecutar backend (FastAPI)
pnpm dev:api

# Ejecutar frontend (cuando esté configurado)
pnpm dev:web

# Ejecutar backend + frontend simultáneamente
pnpm dev
```

### Calidad de Código

```bash
# Linting y formateo
pnpm lint              # Lint en todos los workspaces
pnpm lint:fix          # Lint y auto-fix
pnpm format            # Formatear código

# Type checking
pnpm typecheck         # Type check en todos los workspaces
pnpm validate          # Lint + typecheck completo

# Backend específico
pnpm lint:api          # Lint del backend (ruff)
pnpm format:api         # Formatear backend (ruff + black)
pnpm typecheck:api      # Type check del backend (mypy)
```

### Instalación de Dependencias

```bash
# Instalar dependencias en todo el monorepo
pnpm install

# Agregar dependencia a un workspace específico
pnpm add <package> --filter <workspace>

# Agregar dependencia de desarrollo
pnpm add -D <package> --filter <workspace>
```

## 📝 Workspaces

Este monorepo usa **pnpm workspaces** definidos en `pnpm-workspace.yaml`:

- `apps/*` - Todas las aplicaciones SvelteKit
- `packages/*` - Paquetes compartidos (API, shared, UI)

## ⚠️ Importante

**Este proyecto usa exclusivamente pnpm. NO uses npm o yarn.**

- Todas las instalaciones deben usar `pnpm add` o `pnpm add -D`
- Los workspaces se manejan con `pnpm-workspace.yaml`
- Los scripts del monorepo usan comandos pnpm

## 🔧 Configuración

### Backend (FastAPI)

Ver `packages/api/README.md` para instrucciones de configuración del backend.

### Frontend (SvelteKit)

**Versión:** SvelteKit 1.30.x (compatible con Node 18.20.8)

Las aplicaciones SvelteKit se crearán dentro de `apps/` usando:

```bash
cd apps/<app-name>
pnpm create svelte@latest . --template skeleton
# Luego instalar dependencias específicas de SvelteKit 1.30.x
```

**Nota:** Usamos SvelteKit 1.30.x en lugar de 2.x porque requiere Node.js >= 20.0.0. Cuando actualices a Node 20+, podrás migrar a SvelteKit 2.x.

## 🎯 Herramientas de Calidad

Este monorepo incluye herramientas de calidad de código configuradas:

- **ESLint** + **Prettier** para frontend (TypeScript/Svelte)
- **ruff** + **black** + **mypy** para backend (Python)
- **Husky** + **lint-staged** para Git hooks automáticos
- **commitlint** para validación de commits (Conventional Commits)
- **TypeScript strict mode** activado globalmente

Ver [QUALITY_TOOLS.md](./QUALITY_TOOLS.md) para documentación completa.

## 🧪 Testing

Este proyecto incluye un stack completo de testing para garantizar calidad y confiabilidad.

### Backend Testing (Python/FastAPI)

**Herramientas:**
- `pytest` - Framework de testing
- `pytest-asyncio` - Soporte async
- `pytest-cov` - Coverage reporting
- `httpx` - TestClient async
- `faker` - Generación de datos de prueba

**Comandos:**
```bash
# Ejecutar todos los tests
pnpm test:api

# Solo tests unitarios
pnpm test:api:unit

# Solo tests de integración
pnpm test:api:integration

# Con coverage
pnpm test:api:coverage

# En modo watch (requiere pytest-watch)
pnpm test:api:watch

# En paralelo
pnpm test:api:parallel
```

**Instalación:**
```bash
cd packages/api
pip install -r requirements-dev.txt
```

**Cobertura objetivo:** 70% mínimo

### Frontend Testing (SvelteKit)

**Herramientas:**
- `vitest` - Framework de testing unitario
- `@testing-library/svelte` - Testing de componentes
- `playwright` - E2E testing
- `msw` - Mocking de API (opcional)

**Comandos:**
```bash
# Tests unitarios
pnpm test:web

# Tests con UI interactiva
pnpm test:web:ui

# Tests con coverage
pnpm test:web:coverage

# Tests en modo watch
pnpm test:web --watch

# Tests E2E
pnpm test:web:e2e

# E2E con UI
pnpm test:web:e2e --ui

# E2E en modo debug
pnpm test:web:e2e --debug
```

### Estructura de Tests

```
packages/api/tests/
├── unit/              # Tests unitarios (rápidos, aislados)
├── integration/       # Tests de integración (requieren DB)
└── conftest.py        # Fixtures compartidas

apps/web/
├── src/
│   └── **/*.test.ts   # Tests unitarios (vitest)
└── e2e/               # Tests E2E (playwright)
```

### CI/CD

Los tests se ejecutan automáticamente en cada push y PR mediante GitHub Actions.

**Workflow:** `.github/workflows/test.yml`

**Incluye:**
- Tests backend (unit + integration)
- Tests frontend (unit)
- Tests E2E (playwright)
- Coverage reporting
- Upload a Codecov (opcional)

Ver [TESTING_STACK_ANALISIS_COMPLETO.md](./TESTING_STACK_ANALISIS_COMPLETO.md) para documentación completa.

## 🚀 Deployment

### Fly.io + Alpine Linux

Este proyecto está configurado para deployment en Fly.io usando Alpine Linux 3.20:

- ✅ **Backend:** Dockerfile optimizado para Alpine (Python 3.12, musl libc)
- ✅ **Frontend:** Dockerfile para SvelteKit en Alpine (Node 18)
- ✅ **Compatibilidad:** Todas las dependencias validadas para musl libc

**Cambios importantes:**
- `psycopg2-binary` → `asyncpg` (compatible con musl)
- Python 3.12.x en producción (Alpine 3.20 stable)

Ver [COMPATIBILITY_ALPINE_FLYIO_2025.md](./COMPATIBILITY_ALPINE_FLYIO_2025.md) para análisis completo.

## 📚 Documentación Adicional

- [Setup Guide](./SETUP.md) - Guía de instalación completa
- [Quality Tools](./QUALITY_TOOLS.md) - Herramientas de calidad de código
- [PNPM Guide](./PNPM_GUIDE.md) - Guía de uso de pnpm
- [Alpine/Fly.io Compatibility](./COMPATIBILITY_ALPINE_FLYIO_2025.md) - Triangulación de compatibilidad
- [API Backend](./packages/api/README.md) - Documentación del backend
- [Shared Types](./packages/shared/README.md) - Tipos compartidos
- [UI Components](./packages/ui/README.md) - Componentes UI
- [Docker Infrastructure](./infra/docker/README.md) - Dockerfiles y configuración
- [Fly.io Configuration](./infra/fly/README.md) - Configuración de deployment

