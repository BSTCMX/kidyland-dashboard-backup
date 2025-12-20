# Shared Package

Paquete TypeScript compartido con tipos y utilidades comunes.
Define interfaces, tipos y funciones compartidas entre todas las aplicaciones del monorepo.

## Instalación

Este paquete se instala automáticamente como workspace dependency usando pnpm:

```bash
# Desde cualquier app o package
pnpm add @kidyland/shared --workspace
```

## Uso

```typescript
import { User, Sale, Timer } from '@kidyland/shared';
```

