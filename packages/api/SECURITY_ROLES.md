# Security & Role-Based Access Control

## Role Hierarchy

### 🔴 SUPER_ADMIN
- **Full Control**: CRUD completo en todo el sistema
- **User Management**: Único rol que puede crear, actualizar y eliminar usuarios
- **Role Assignment**: Define el rol de cada usuario al crearlo
- **Password Management**: Define las contraseñas de todos los usuarios
- **System Configuration**: Acceso total a configuración del sistema

### 🟡 ADMIN_VIEWER
- **Read-Only Access**: Ve TODO lo que ve Super Admin
- **Zero Permissions**: No puede editar, crear ni eliminar nada
- **View Only**: Solo lectura en todos los endpoints

### 🟢 RECEPCIÓN
- **Daily Operations**: Operaciones diarias (ventas, timers, arqueo)
- **Sales Management**: Puede crear ventas y gestionar timers
- **Day Close**: Puede realizar cierre de día
- **Restrictions**: No puede crear usuarios ni configurar el sistema

### 🔵 KIDIBAR
- **Products Only**: Solo productos y ventas de productos
- **Product Sales**: Puede vender productos
- **Restrictions**: No acceso a servicios/timers ni configuración

### ⚪ MONITOR
- **View Only**: Solo vista de timers activos
- **Zero Input**: No puede realizar ninguna acción, solo visualizar
- **Display Only**: Endpoint de solo lectura para timers

## Security Implementation

### Middleware Usage

```python
from utils.auth import require_role

# Solo super_admin
@router.post("/users", dependencies=[Depends(require_role("super_admin"))])
def create_user():
    pass

# Múltiples roles permitidos
@router.get("/reports", dependencies=[Depends(require_role(["super_admin", "admin_viewer"]))])
def get_reports():
    pass

# Solo recepcion
@router.post("/sales", dependencies=[Depends(require_role("recepcion"))])
def create_sale():
    pass

# Múltiples roles (kidibar y recepcion pueden vender productos)
@router.post("/products/sell", dependencies=[Depends(require_role(["kidibar", "recepcion"]))])
def sell_product():
    pass
```

## User Management Security

### Endpoints Protegidos

| Endpoint | Method | Allowed Roles | Description |
|----------|--------|---------------|-------------|
| `/users` | POST | `super_admin` | Crear usuario |
| `/users` | GET | `super_admin`, `admin_viewer` | Listar usuarios |
| `/users/{id}` | GET | `super_admin`, `admin_viewer` | Ver usuario |
| `/users/{id}` | PUT | `super_admin` | Actualizar usuario |
| `/users/{id}` | DELETE | `super_admin` | Eliminar usuario |

### Security Rules

1. **Super Admin Only**: Solo `super_admin` puede crear, actualizar o eliminar usuarios
2. **Role Immutability**: Los usuarios finales NO pueden cambiar su propio rol
3. **Password Control**: Las contraseñas son definidas por Super Admin al crear usuarios
4. **Permission Enforcement**: Todos los permisos son verificados por middleware antes de ejecutar endpoints

## Implementation Files

- `packages/api/utils/auth.py`: Función `require_role()` para verificación de roles
- `packages/api/routers/users.py`: Endpoints de gestión de usuarios con protección
- `packages/api/middleware/auth.py`: Middleware base para autenticación JWT (pendiente implementación)

## Notes

- Los roles son inmutables por el usuario final
- Solo Super Admin puede modificar roles
- Las contraseñas son definidas por Super Admin
- Todos los permisos son enforced por middleware
































