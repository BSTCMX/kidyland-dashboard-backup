# 📋 PLAN DE ACCIÓN - CORRECCIÓN CATALOG ROUTER TESTS

**Objetivo:** Corregir tests del Catalog Router manteniendo Clean Architecture, código modular y escalable.

**Enfoque:** Corrección manual, pieza por pieza, validando cada paso.

---

## 🎯 PRINCIPIOS DE CORRECCIÓN

### Clean Architecture
- ✅ Separación de concerns (fixtures, helpers, tests)
- ✅ Código reutilizable y modular
- ✅ Sin hardcodeo, siempre dinámico

### Patrones a Seguir
1. **Fixtures de usuario:** Usar fixtures existentes (`test_superadmin`, `test_admin_viewer`, etc.)
2. **Tokens:** Usar `create_access_token(data={"sub": user.username})` directamente
3. **AsyncClient:** Usar `ASGITransport(app=app)` (ya corregido)
4. **Setup:** Usar `setup_dependencies` fixture (ya implementado)

---

## 📊 ANÁLISIS DE PROBLEMAS

### Problema 1: Fixtures de Usuario Faltantes
**Ubicación:** ~40 tests  
**Solución:** Agregar fixtures de usuario en parámetros de función

### Problema 2: Tokens Incorrectos
**Ubicación:** ~40 tests  
**Solución:** Reemplazar referencias a `*_token` con `create_access_token()`

### Problema 3: Variables No Definidas
**Ubicación:** Tests que usan variables sin fixtures  
**Solución:** Agregar fixtures necesarios

---

## 🗺️ PLAN DE CORRECCIÓN POR FASES

### **FASE 1: CREAR HELPERS REUTILIZABLES** (Base Sólida)

#### 1.1 Helper para Crear Tokens
**Objetivo:** Centralizar creación de tokens para evitar duplicación

**Implementación:**
```python
# Helper function (no fixture, para ser más flexible)
def get_auth_token(user: User) -> str:
    """Create JWT token for a user."""
    return create_access_token(data={"sub": user.username})
```

**Ubicación:** Al inicio del archivo, después de imports

**Beneficios:**
- ✅ Código DRY (Don't Repeat Yourself)
- ✅ Fácil de mantener
- ✅ Consistente en todos los tests

---

### **FASE 2: CORREGIR TESTSUCURSALESENDPOINTS** (13 tests)

#### 2.1 Tests GET (4 tests)
**Tests a corregir:**
- `test_get_sucursales_super_admin` ✅ Ya correcto
- `test_get_sucursales_admin_viewer` ✅ Ya correcto
- `test_get_sucursales_forbidden_recepcion` ❌ Falta fixture
- `test_get_sucursales_forbidden_kidibar` ❌ Falta fixture
- `test_get_sucursales_empty_list` ❌ Falta fixture

**Correcciones:**
1. Agregar `test_user: User` en `test_get_sucursales_forbidden_recepcion`
2. Agregar `test_kidibar: User` en `test_get_sucursales_forbidden_kidibar`
3. Agregar `test_superadmin: User` en `test_get_sucursales_empty_list`
4. Reemplazar tokens con `get_auth_token(user)`

#### 2.2 Tests POST (3 tests)
**Tests a corregir:**
- `test_create_sucursal_super_admin` ❌ Falta fixture
- `test_create_sucursal_forbidden_admin_viewer` ❌ Falta fixture
- `test_create_sucursal_validation_required_fields` ❌ Falta fixture

**Correcciones:**
1. Agregar `test_superadmin: User` en todos
2. Agregar `test_admin_viewer: User` donde corresponda
3. Reemplazar tokens

#### 2.3 Tests PUT (3 tests)
**Tests a corregir:**
- `test_update_sucursal_super_admin` ❌ Falta fixture
- `test_update_sucursal_not_found` ❌ Falta fixture
- `test_update_sucursal_partial_update` ❌ Falta fixture

**Correcciones:**
1. Agregar `test_superadmin: User` en todos
2. Reemplazar tokens

#### 2.4 Tests DELETE (3 tests)
**Tests a corregir:**
- `test_delete_sucursal_super_admin` ❌ Falta fixture
- `test_delete_sucursal_not_found` ❌ Falta fixture
- `test_delete_sucursal_forbidden_admin_viewer` ❌ Falta fixture

**Correcciones:**
1. Agregar `test_superadmin: User` en todos
2. Agregar `test_admin_viewer: User` donde corresponda
3. Reemplazar tokens

**Validación FASE 2:**
```bash
pytest tests/integration/test_catalog_endpoints.py::TestSucursalesEndpoints -v
```
**Objetivo:** 13/13 tests passing ✅

---

### **FASE 3: CORREGIR TESTPRODUCTSENDPOINTS** (14 tests)

#### 3.1 Tests GET (5 tests)
**Correcciones similares a FASE 2.1**

#### 3.2 Tests POST (3 tests)
**Correcciones similares a FASE 2.2**

#### 3.3 Tests PUT (3 tests)
**Correcciones similares a FASE 2.3**

#### 3.4 Tests DELETE (3 tests)
**Correcciones similares a FASE 2.4**

**Validación FASE 3:**
```bash
pytest tests/integration/test_catalog_endpoints.py::TestProductsEndpoints -v
```
**Objetivo:** 14/14 tests passing ✅

---

### **FASE 4: CORREGIR TESTSERVICESENDPOINTS** (13 tests)

**Misma estructura que FASE 2 y 3**

**Validación FASE 4:**
```bash
pytest tests/integration/test_catalog_endpoints.py::TestServicesEndpoints -v
```
**Objetivo:** 13/13 tests passing ✅

---

### **FASE 5: CORREGIR TESTPACKAGESENDPOINTS** (15 tests)

**Misma estructura que FASE 2, 3 y 4**

**Nota especial:** Ya corregido factory Package (`included_items`)

**Validación FASE 5:**
```bash
pytest tests/integration/test_catalog_endpoints.py::TestPackagesEndpoints -v
```
**Objetivo:** 15/15 tests passing ✅

---

### **FASE 6: VALIDACIÓN FINAL Y COVERAGE**

#### 6.1 Ejecutar Suite Completa
```bash
pytest tests/integration/test_catalog_endpoints.py -v
```
**Objetivo:** 55/55 tests passing ✅

#### 6.2 Verificar Coverage
```bash
pytest tests/integration/test_catalog_endpoints.py --cov=routers/catalog --cov-report=term-missing
```
**Objetivo:** Coverage >90% ✅

#### 6.3 Verificar Tests Existentes No Se Rompieron
```bash
pytest tests/integration/ -v
```
**Objetivo:** Todos los tests existentes siguen pasando ✅

---

## 🔧 PLANTILLA DE CORRECCIÓN

### Antes (Incorrecto):
```python
async def test_get_sucursales_forbidden_recepcion(
    self,
    test_db,
):
    """Test GET /sucursales denied for recepcion role."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            "/sucursales",
            headers={"Authorization": f"Bearer {recepcion_token}"}  # ❌ Variable no definida
        )
```

### Después (Correcto):
```python
async def test_get_sucursales_forbidden_recepcion(
    self,
    test_db,
    test_user: User,  # ✅ Agregar fixture
):
    """Test GET /sucursales denied for recepcion role."""
    token = get_auth_token(test_user)  # ✅ Usar helper
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            "/sucursales",
            headers={"Authorization": f"Bearer {token}"}  # ✅ Token correcto
        )
```

---

## 📝 CHECKLIST DE CORRECCIÓN POR TEST

Para cada test, verificar:

- [ ] **Fixtures de usuario presentes** (si el test requiere autenticación)
- [ ] **Token creado con `get_auth_token(user)`** (no usar variables `*_token`)
- [ ] **Headers correctos** (`Authorization: Bearer {token}`)
- [ ] **Fixtures de datos presentes** (sucursal, product, service, package según corresponda)
- [ ] **Assertions claras y específicas**
- [ ] **Sin hardcodeo** (usar fixtures dinámicos)

---

## 🎯 ORDEN DE EJECUCIÓN

1. ✅ **FASE 1:** Crear helper `get_auth_token()`
2. ⏳ **FASE 2:** Corregir TestSucursalesEndpoints (13 tests)
3. ⏳ **FASE 3:** Corregir TestProductsEndpoints (14 tests)
4. ⏳ **FASE 4:** Corregir TestServicesEndpoints (13 tests)
5. ⏳ **FASE 5:** Corregir TestPackagesEndpoints (15 tests)
6. ⏳ **FASE 6:** Validación final y coverage

---

## 🚨 REGLAS DE VALIDACIÓN

### Después de cada fase:
1. ✅ Ejecutar tests de esa clase
2. ✅ Verificar que todos pasen
3. ✅ Revisar código por hardcodeo
4. ✅ Verificar modularidad

### Antes de avanzar a siguiente fase:
- ✅ Tests actuales 100% passing
- ✅ Código limpio y modular
- ✅ Sin errores de linting

---

## 📊 MÉTRICAS DE ÉXITO

### Por Fase:
- **FASE 1:** Helper creado y funcionando
- **FASE 2:** 13/13 tests passing
- **FASE 3:** 14/14 tests passing
- **FASE 4:** 13/13 tests passing
- **FASE 5:** 15/15 tests passing

### Final:
- **Total:** 55/55 tests passing
- **Coverage:** >90% Catalog Router
- **Tests existentes:** Todos pasando
- **Código:** Limpio, modular, sin hardcodeo

---

## 🎬 SIGUIENTE PASO

**EMPEZAR CON FASE 1:** Crear helper `get_auth_token()`

¿Procedemos con FASE 1?





























