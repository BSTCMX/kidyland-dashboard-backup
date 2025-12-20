# 🚀 GUÍA DE CONFIGURACIÓN - STACK DE TESTING

**Fecha:** 2025-01-XX  
**Objetivo:** Guía paso a paso para configurar el stack completo de testing

---

## 📋 PREREQUISITOS

- Node.js >= 18.20.0
- Python >= 3.13
- pnpm >= 8.15.0
- Git

---

## 🔧 CONFIGURACIÓN BACKEND

### **Paso 1: Instalar Dependencias de Testing**

```bash
cd packages/api

# Activar entorno virtual
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias de desarrollo
pip install -r requirements-dev.txt
```

### **Paso 2: Verificar Configuración**

```bash
# Verificar pytest está instalado
pytest --version

# Ejecutar tests existentes
pytest tests/unit/ -v

# Verificar coverage
pytest --cov=. --cov-report=term-missing
```

### **Paso 3: Crear Test de Ejemplo**

Crear `packages/api/tests/unit/test_example.py`:

```python
import pytest

@pytest.mark.unit
def test_example():
    """Example unit test."""
    assert 1 + 1 == 2
```

### **Paso 4: Ejecutar Tests**

```bash
# Desde raíz del proyecto
pnpm test:api

# Solo unitarios
pnpm test:api:unit

# Con coverage
pnpm test:api:coverage
```

---

## 🔧 CONFIGURACIÓN FRONTEND

### **Paso 1: Instalar Dependencias**

```bash
# Desde raíz del proyecto
pnpm install

# Esto instalará todas las dependencias de testing en apps/web
```

### **Paso 2: Verificar Configuración**

```bash
# Verificar vitest está instalado
cd apps/web
pnpm exec vitest --version

# Verificar playwright está instalado
pnpm exec playwright --version
```

### **Paso 3: Instalar Navegadores de Playwright**

```bash
cd apps/web
pnpm exec playwright install
```

### **Paso 4: Crear Test de Ejemplo**

El archivo `apps/web/src/lib/stores/__tests__/notifications.test.ts` ya existe como ejemplo.

### **Paso 5: Ejecutar Tests**

```bash
# Desde raíz del proyecto
pnpm test:web

# Con UI interactiva
pnpm test:web:ui

# Con coverage
pnpm test:web:coverage

# E2E tests
pnpm test:web:e2e
```

---

## 🧪 ESTRUCTURA DE TESTS RECOMENDADA

### **Backend (Python)**

```
packages/api/tests/
├── unit/
│   ├── services/
│   │   ├── test_sale_service.py
│   │   └── test_timer_service.py
│   └── test_*.py
├── integration/
│   ├── routers/
│   │   ├── test_sales_endpoints.py
│   │   └── test_timers_endpoints.py
│   └── test_*.py
└── conftest.py
```

**Convenciones:**
- Tests unitarios: `test_*.py` en `tests/unit/`
- Tests de integración: `test_*.py` en `tests/integration/`
- Usar markers: `@pytest.mark.unit`, `@pytest.mark.integration`

### **Frontend (SvelteKit)**

```
apps/web/
├── src/
│   ├── lib/
│   │   ├── stores/
│   │   │   └── __tests__/
│   │   │       ├── notifications.test.ts
│   │   │       └── timers.test.ts
│   │   └── components/
│   │       └── __tests__/
│   │           └── ToastNotification.test.svelte
└── e2e/
    ├── auth.spec.ts
    ├── sales.spec.ts
    └── timers.spec.ts
```

**Convenciones:**
- Tests unitarios: `*.test.ts` o `*.spec.ts` junto al código
- Tests E2E: `*.spec.ts` en `e2e/`
- Tests de componentes: `*.test.svelte` o `*.test.ts`

---

## 📝 EJEMPLOS DE TESTS

### **Backend: Test Unitario**

```python
# packages/api/tests/unit/test_example.py
import pytest
from services.example_service import ExampleService

@pytest.mark.unit
@pytest.mark.asyncio
async def test_example_service(test_db):
    """Test example service."""
    service = ExampleService()
    result = await service.doSomething(test_db)
    assert result is not None
```

### **Frontend: Test de Store**

```typescript
// apps/web/src/lib/stores/__tests__/example.test.ts
import { describe, it, expect } from 'vitest';
import { get } from 'svelte/store';
import { exampleStore, doSomething } from '../example';

describe('example store', () => {
  it('should work correctly', () => {
    doSomething();
    const state = get(exampleStore);
    expect(state.value).toBe('expected');
  });
});
```

### **Frontend: Test de Componente**

```typescript
// apps/web/src/lib/components/__tests__/Example.test.svelte
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/svelte';
import Example from '../Example.svelte';

describe('Example component', () => {
  it('should render correctly', () => {
    render(Example, { prop: 'value' });
    expect(screen.getByText('Expected Text')).toBeInTheDocument();
  });
});
```

### **Frontend: Test E2E**

```typescript
// apps/web/e2e/example.spec.ts
import { test, expect } from '@playwright/test';

test('should navigate to page', async ({ page }) => {
  await page.goto('/');
  await expect(page).toHaveTitle(/Kidyland/i);
});
```

---

## 🎯 COMANDOS ÚTILES

### **Backend**

```bash
# Ejecutar tests con output detallado
pytest -v -s

# Ejecutar solo tests marcados como "unit"
pytest -m unit

# Ejecutar tests y generar coverage HTML
pytest --cov=. --cov-report=html
# Luego abrir: packages/api/htmlcov/index.html

# Ejecutar tests en paralelo (más rápido)
pytest -n auto

# Ejecutar tests con timeout
pytest --timeout=10
```

### **Frontend**

```bash
# Ejecutar tests en modo watch
vitest --watch

# Ejecutar tests con UI
vitest --ui

# Ejecutar tests con coverage
vitest --coverage

# Ejecutar solo tests que contengan "notifications"
vitest -t notifications

# Ejecutar E2E tests en modo headed (ver navegador)
playwright test --headed

# Ejecutar E2E tests en modo debug
playwright test --debug
```

---

## 🔍 TROUBLESHOOTING

### **Backend: "pytest: command not found"**
```bash
# Verificar que está en el venv
which pytest  # Debe mostrar ruta del venv

# Reinstalar
pip install -r requirements-dev.txt
```

### **Frontend: "vitest: command not found"**
```bash
# Verificar instalación
pnpm list vitest

# Reinstalar
pnpm install
```

### **Frontend: "playwright: command not found"**
```bash
# Instalar navegadores
pnpm exec playwright install
```

### **Tests E2E fallan en CI pero no localmente**
- Verificar que `webServer` está configurado correctamente
- Aumentar `timeout` en `playwright.config.ts`
- Verificar que el servidor se inicia correctamente

---

## 📚 RECURSOS ADICIONALES

- [Vitest Documentation](https://vitest.dev/)
- [Playwright Documentation](https://playwright.dev/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Testing Library Svelte](https://testing-library.com/docs/svelte-testing-library/intro/)

---

**✅ Una vez completada esta guía, el stack de testing estará completamente configurado y listo para usar.**





























