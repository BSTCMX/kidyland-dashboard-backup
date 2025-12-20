# 🧪 TESTING E2E MANUAL - PASO 2 KIDYLAND

**Fecha:** 2025-01-XX  
**Objetivo:** Validar todos los flujos críticos del dashboard de usuarios

---

## 📋 CHECKLIST DE TESTING

### ✅ 1. AUTENTICACIÓN

#### 1.1 Login con Username/Password
- [ ] Abrir `http://localhost:8000/docs`
- [ ] POST `/auth/login`
- [ ] Payload: `{"username": "test_user", "password": "Test1234"}`
- [ ] Verificar respuesta 200 con JWT token
- [ ] Verificar que NO hay campo `email` en respuesta

**Resultado esperado:**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user": {
    "id": "...",
    "username": "test_user",
    "name": "...",
    "role": "...",
    // NO debe haber campo "email"
  }
}
```

#### 1.2 Login con Usuario Inexistente
- [ ] POST `/auth/login` con username que no existe
- [ ] Verificar respuesta 401
- [ ] Verificar mensaje: "Invalid username or password"

#### 1.3 Login con Password Incorrecta
- [ ] POST `/auth/login` con password incorrecta
- [ ] Verificar respuesta 401
- [ ] Verificar mensaje: "Invalid username or password"

---

### ✅ 2. NAVEGACIÓN Y PERMISOS

#### 2.1 Acceso como super_admin
- [ ] Login con usuario super_admin
- [ ] Navegar a `/admin/users`
- [ ] Verificar que se muestra lista de usuarios
- [ ] Verificar botón "Crear Usuario" visible
- [ ] Verificar botones de acción (Editar, Eliminar) visibles

#### 2.2 Acceso como admin_viewer
- [ ] Login con usuario admin_viewer
- [ ] Navegar a `/admin/users`
- [ ] Verificar que se muestra lista de usuarios
- [ ] Verificar que NO hay botón "Crear Usuario"
- [ ] Verificar que NO hay botones de acción (solo lectura)

#### 2.3 Acceso sin permisos
- [ ] Login con usuario recepcion/kidibar/monitor
- [ ] Intentar navegar a `/admin/users`
- [ ] Verificar redirección o mensaje de error 403

---

### ✅ 3. CRUD USUARIOS (super_admin)

#### 3.1 Crear Usuario
- [ ] Click en "Crear Usuario"
- [ ] Llenar formulario:
  - Username: `test_user_new`
  - Nombre: `Test User New`
  - Rol: `recepcion`
  - Password: `Test1234`
- [ ] Click en "Guardar"
- [ ] Verificar que usuario se crea exitosamente
- [ ] Verificar que aparece en la lista
- [ ] Verificar que NO hay campo email en el usuario creado

#### 3.2 Validaciones al Crear
- [ ] Username muy corto (< 3 chars) → Error esperado
- [ ] Username muy largo (> 50 chars) → Error esperado
- [ ] Username con caracteres especiales → Error esperado
- [ ] Password muy corta (< 8 chars) → Error esperado
- [ ] Password sin mayúscula → Error esperado
- [ ] Password sin número → Error esperado
- [ ] Username duplicado → Error esperado

#### 3.3 Listar Usuarios
- [ ] Verificar que se cargan usuarios correctamente
- [ ] Verificar paginación (si hay más de 20 usuarios)
- [ ] Verificar filtros:
  - Búsqueda por username/nombre
  - Filtro por rol
- [ ] Verificar que NO hay columna email en la tabla

#### 3.4 Editar Usuario
- [ ] Click en "Editar" en un usuario
- [ ] Modificar nombre
- [ ] Modificar rol
- [ ] (Opcional) Cambiar password
- [ ] Click en "Guardar"
- [ ] Verificar que cambios se guardan
- [ ] Verificar que NO hay campo email en el formulario

#### 3.5 Cambiar Password
- [ ] Click en "Password" en un usuario
- [ ] Ingresar nueva password: `NewPass123`
- [ ] Click en "Cambiar Password"
- [ ] Verificar éxito
- [ ] Probar login con nueva password

#### 3.6 Activar Usuario
- [ ] Seleccionar usuario inactivo
- [ ] Click en "Activar"
- [ ] Verificar que usuario se activa
- [ ] Verificar cambio de estado en la lista

#### 3.7 Desactivar Usuario
- [ ] Seleccionar usuario activo (que NO sea último super_admin)
- [ ] Click en "Desactivar"
- [ ] Confirmar acción
- [ ] Verificar que usuario se desactiva
- [ ] Verificar cambio de estado en la lista

#### 3.8 Eliminar Usuario
- [ ] Seleccionar usuario (que NO sea último super_admin activo)
- [ ] Click en "Eliminar"
- [ ] Confirmar acción
- [ ] Verificar que usuario se elimina
- [ ] Verificar que desaparece de la lista

#### 3.9 Protección Último Super Admin
- [ ] Intentar eliminar último super_admin activo
- [ ] Verificar error: "Cannot delete last active super_admin"
- [ ] Intentar desactivar último super_admin activo
- [ ] Verificar error: "Cannot deactivate last active super_admin"

---

### ✅ 4. RESPONSIVE DESIGN

#### 4.1 Mobile (< 768px)
- [ ] Abrir en viewport mobile (360px, 481px)
- [ ] Verificar que tabla se convierte en cards
- [ ] Verificar que sidebar tiene hamburger menu
- [ ] Verificar que sidebar se colapsa/expande
- [ ] Verificar que overlay aparece cuando sidebar está abierto
- [ ] Verificar que botones son touch-friendly (min 48x48px)
- [ ] Verificar que filtros se apilan verticalmente
- [ ] Verificar que formularios son usables

#### 4.2 Tablet (768px - 1023px)
- [ ] Abrir en viewport tablet (768px)
- [ ] Verificar que tabla tiene scroll horizontal
- [ ] Verificar que sidebar está visible
- [ ] Verificar que layout es funcional

#### 4.3 Desktop (> 1024px)
- [ ] Abrir en viewport desktop (1024px, 1280px, 1440px, 1920px)
- [ ] Verificar que tabla se muestra completa
- [ ] Verificar que sidebar está siempre visible
- [ ] Verificar que grid se adapta correctamente

---

### ✅ 5. DARK MODE

#### 5.1 Toggle Dark Mode
- [ ] Click en botón de tema (☀️/🌙)
- [ ] Verificar que tema cambia
- [ ] Verificar que se persiste en localStorage
- [ ] Recargar página y verificar que tema se mantiene

#### 5.2 Dark Mode en Todos los Viewports
- [ ] Activar dark mode
- [ ] Probar en mobile, tablet, desktop
- [ ] Verificar que todos los componentes se ven correctamente
- [ ] Verificar contraste de texto
- [ ] Verificar que botones son visibles

---

### ✅ 6. EDGE CASES

#### 6.1 Lista Vacía
- [ ] Eliminar todos los usuarios (excepto super_admin)
- [ ] Verificar que se muestra mensaje apropiado
- [ ] Verificar que botón "Crear Usuario" sigue visible

#### 6.2 Búsqueda Sin Resultados
- [ ] Buscar username que no existe
- [ ] Verificar que se muestra mensaje apropiado
- [ ] Verificar que filtros funcionan correctamente

#### 6.3 Errores de Red
- [ ] Desconectar internet
- [ ] Intentar crear usuario
- [ ] Verificar que se muestra error apropiado
- [ ] Verificar que UI no se rompe

---

## 📊 RESULTADOS ESPERADOS

### ✅ Todos los Tests Deben Pasar

**Funcionalidad:**
- ✅ Login funciona con username/password
- ✅ CRUD usuarios funciona completamente
- ✅ Validaciones funcionan correctamente
- ✅ Permisos por rol funcionan correctamente

**UX/UI:**
- ✅ Responsive funciona en todos los viewports
- ✅ Dark mode funciona correctamente
- ✅ Componentes son touch-friendly
- ✅ Navegación es fluida

**Clean Architecture:**
- ✅ Sin campo email en ningún lugar
- ✅ Separación de capas preservada
- ✅ Sin hardcoding
- ✅ Modular y escalable

---

## 🐛 ISSUES ENCONTRADOS

### (Documentar aquí cualquier issue encontrado)

1. **Issue 1:** [Descripción]
   - **Severidad:** Alta/Media/Baja
   - **Reproducción:** [Pasos]
   - **Fix:** [Solución]

---

## ✅ CONCLUSIÓN

- [ ] Todos los flujos críticos probados
- [ ] Todos los tests pasan
- [ ] Issues documentados
- [ ] Fixes aplicados
- [ ] Validación final completada

**Estado:** ⏳ **PENDIENTE DE EJECUTAR**

---

**📄 Este checklist debe completarse manualmente probando la aplicación en el navegador.**





























