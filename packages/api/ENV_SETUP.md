# Variables de Entorno

Crea un archivo `.env` en `packages/api/` con las siguientes variables:

## Producción (Neon Serverless - SSL required)

```env
DATABASE_URL="postgresql://neondb_owner:npg_tHCaWNJK5Y0h@ep-snowy-wildflower-aak1qeuk-pooler.westus3.azure.neon.tech/neondb?sslmode=require&channel_binding=require"
SECRET_KEY="your-production-secret-key"
ENVIRONMENT="production"
```

## Local (Neon Local Connect)

```env
DATABASE_URL="postgres://neon:npg@localhost:5432/kidyland"
SECRET_KEY="dev-secret-key"
ENVIRONMENT="development"
```

**Nota:** Reemplaza `kidyland` por el nombre de tu base de datos local si es diferente.
































