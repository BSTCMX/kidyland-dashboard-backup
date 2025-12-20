# 🔐 Password Hashing Migration - passlib → bcrypt

**Fecha:** Diciembre 2025  
**Motivo:** Compatibilidad con Python 3.13 + Alpine/musl

---

## 📊 INVESTIGACIÓN DE COMPATIBILIDAD

### ❌ Problemas con passlib

1. **Python 3.13**: El módulo `crypt` fue eliminado en Python 3.13, y `passlib` depende de él
2. **bcrypt 4.1.0+**: Eliminó el atributo `__about__` que `passlib` necesita
3. **Mantenimiento**: `passlib` no está siendo activamente mantenido
4. **Alpine/musl**: Requiere compilación, puede fallar sin compiladores

### ✅ Solución: bcrypt directo

**Ventajas:**
- ✅ Compatible con Python 3.13
- ✅ Wheels precompiladas para Alpine/musl disponibles
- ✅ Activamente mantenido
- ✅ API simple y directa
- ✅ Mismo algoritmo (bcrypt) - hashes compatibles

**Desventajas:**
- ⚠️ Cambio menor en código (migración simple)

---

## 🔄 CAMBIOS IMPLEMENTADOS

### 1. requirements.txt
```diff
- passlib[bcrypt]==1.7.4
+ bcrypt==4.2.0
```

### 2. core/security.py
```python
# Antes (passlib):
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
return pwd_context.hash(password)
return pwd_context.verify(plain_password, hashed_password)

# Después (bcrypt directo):
import bcrypt
def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
```

### 3. Compatibilidad de hashes
- ✅ **Hashes existentes**: Los hashes generados con passlib/bcrypt son compatibles
- ✅ **Nuevos hashes**: Se generan con bcrypt directo
- ✅ **Verificación**: Funciona con ambos formatos

---

## 🧪 VALIDACIÓN

### Test Local
```bash
cd packages/api
source venv/bin/activate
python test_password_hashing.py
```

### Test Docker Alpine
```bash
docker build -f infra/docker/Dockerfile.api -t kidyland-api-test .
docker run --rm kidyland-api-test python test_password_hashing.py
```

---

## ✅ RESULTADO ESPERADO

1. ✅ Tests pasan en local (Python 3.13)
2. ✅ Tests pasan en Docker Alpine
3. ✅ Hashes existentes siguen funcionando
4. ✅ Nuevos hashes se generan correctamente
5. ✅ Verificación funciona en ambos casos

---

## 📝 NOTAS

- **Migración sin breaking changes**: Hashes existentes siguen funcionando
- **Seguridad mantenida**: Mismo algoritmo bcrypt, misma seguridad
- **Performance**: Similar o mejor (sin capa de abstracción)
- **Alpine compatibility**: Wheels precompiladas disponibles

---

**Estado:** ✅ **MIGRACIÓN COMPLETA - LISTA PARA PRODUCCIÓN**
































