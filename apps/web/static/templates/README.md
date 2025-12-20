# Templates para Exportación de Menú

Esta carpeta contiene las imágenes de templates utilizadas para generar videos y PDFs de menús.

## Especificaciones

### Formato y Tamaño
- **Resolución:** 1920x1080px (Full HD)
- **Formato:** PNG (recomendado para calidad y transparencia)
- **Peso máximo:** < 500KB por imagen (optimizadas)
- **Nombres:** kebab-case (ej: `template-modern.png`)

## Archivos Requeridos

Coloca las siguientes imágenes en esta carpeta:

1. **template-modern.png** - Template Moderno (3 columnas)
2. **template-classic.png** - Template Clásico (2 columnas)  
3. **template-minimal.png** - Template Minimalista (4 columnas)

## Cómo Agregar Nuevos Templates

1. Agrega la imagen en esta carpeta con el nombre en kebab-case
2. Edita `/apps/web/src/lib/schemas/template-schema.ts`
3. Agrega la configuración del template en `DEFAULT_TEMPLATES`

Ejemplo:

```typescript
{
  id: "template-nuevo",
  name: "Template Nuevo",
  description: "Descripción del template",
  image: "/templates/template-nuevo.png",
  layout: {
    grid: { columns: 3, gap: 20, padding: 40 },
    // ... resto de configuración
  },
}
```

## Notas

- Las imágenes deben tener exactamente 1920x1080px para mantener consistencia
- Optimiza las imágenes antes de subirlas para mejor performance
- Los templates se cargan automáticamente al iniciar la aplicación

