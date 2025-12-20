# Kidyland API

Backend FastAPI para el sistema Kidyland.

## Propósito

Este backend proporciona la API REST para todas las aplicaciones del monorepo:
- Admin (Super Admin)
- Admin Viewer (solo lectura)
- Reception (Panel de recepción)
- KidiBar (Venta de productos)
- Monitor (Visualización de timers)

## Tecnologías

- **FastAPI**: Framework web moderno y rápido para Python
- **SQLAlchemy**: ORM para gestión de base de datos
- **Neon**: Base de datos PostgreSQL serverless y local

## Conexión a Neon

El backend se conecta a Neon usando dos modos:

### Local (Neon Local Connect)
```
DATABASE_URL="postgres://neon:npg@localhost:5432/kidyland"
```

### Producción (Neon Serverless)
```
DATABASE_URL="postgresql://...?sslmode=require&channel_binding=require"
```

## Estructura Modular

```
packages/api/
├── main.py              # FastAPI app principal
├── database.py          # Configuración SQLAlchemy + Neon
├── core/                # Configuración y utilidades
│   ├── config.py        # Settings con Pydantic
│   └── security.py      # JWT utilities
├── models/              # Modelos SQLAlchemy
├── routers/             # Endpoints agrupados
└── middleware/          # Auth y roles
```

## Estado Actual

⚠️ **Este es solo el skeleton inicial.**

- Estructura base creada
- Endpoints definidos como placeholders
- Modelos vacíos (se llenarán en Prompt 4)
- Sin lógica de negocio implementada

## Ejecución

Desde la raíz del monorepo (recomendado):

```bash
pnpm dev:api
```

O manualmente:

```bash
cd packages/api
uvicorn main:app --reload
```

O desde la raíz:

```bash
uvicorn packages.api.main:app --reload
```

## Endpoints Disponibles

- `GET /health` - Health check
- `POST /auth/login` - Autenticación
- `GET /sucursales` - Listar sucursales
- `POST /sucursales` - Crear sucursal
- `GET /services` - Listar servicios
- `GET /products` - Listar productos
- `POST /sales` - Crear venta
- `GET /timers/active` - Timers activos
- `POST /day/close` - Cerrar día

Todos los endpoints devuelven `501 Not Implemented` hasta que se implemente la lógica.
