# Plan de Reestructuración Frontend ElectroPluz

## 🔄 Estado Actual y Cambios Realizados

### ✅ Completado
1. Limpieza inicial de vistas (`gateway_app/views.py`):
   - Reorganización de imports y docstrings
   - Implementación de vistas públicas (home, category)
   - Implementación de funcionalidad de carrito
   - Configuración de proxies API para microservicios
   - Validación con `manage.py check` exitosa

2. Autenticación y Dashboards:
   - Separación de vistas de autenticación en `views_auth.py`
   - Implementación de autenticación basada en sesión
   - Redirección post-login según rol de usuario

### 🚧 En Progreso
1. Validación de rutas y templates:
   - Pruebas de carga de home/catalog
   - Verificación de carrito y checkout
   - Pruebas de APIs de productos/ventas

## 📋 Tareas Pendientes por Prioridad

### 1️⃣ Prioridad Alta - Reestructuración de Apps

1. Crear nuevas apps Django:
```bash
python manage.py startapp storefront
python manage.py startapp sales
python manage.py startapp inventory
```

2. Migrar contenido actual:
- [ ] Mover vistas públicas a `storefront/views.py`
- [ ] Mover lógica de ventas a `sales/views.py`
- [ ] Mover gestión de inventario a `inventory/views.py`

3. Configurar settings.py:
- [ ] Añadir nuevas apps a INSTALLED_APPS
- [ ] Verificar STATIC_URL y STATICFILES_DIRS
- [ ] Configurar variables de entorno para microservicios

### 2️⃣ Prioridad Alta - Migración de Templates y Auth

1. Migrar templates a nuevas apps:
- [ ] Mover templates relevantes de gateway_app a sus respectivas apps
- [ ] Eliminar carpeta templates obsoleta de gateway_app
- [ ] Actualizar referencias en las vistas

2. Implementar nuevo sistema de autenticación:
- [ ] Crear componente de notificación para login/registro
- [ ] Implementar autenticación vía modal/popup
- [ ] Eliminar templates antiguos de auth
- [ ] Actualizar views_auth.py para responder JSON

3. Restructurar templates por app:
- [ ] `storefront/templates/base.html` (plantilla base global)
- [ ] `storefront/templates/shop/` (catálogo y carrito)
- [ ] `inventory/templates/inventory/` (dashboard)

### 3️⃣ Prioridad Alta - Reorganización de Archivos Estáticos

1. Migrar archivos estáticos:
- [ ] Revisar y mover archivos de gateway_app/static a sus respectivas apps
- [ ] Eliminar carpeta static obsoleta de gateway_app
- [ ] Actualizar referencias en templates

2. Organizar static files por app:
```
storefront/static/storefront/
  ├── css/
  │   ├── global.css
  │   ├── auth-modal.css   # Nuevo estilo para modal de auth
  │   └── navbar.css
  └── js/
      ├── main.js
      └── auth-modal.js    # Nuevo JS para autenticación

sales/static/sales/
  ├── css/
  │   ├── catalog.css
  │   └── cart.css
  └── js/
      ├── cart.js
      └── product-gallery.js

inventory/static/inventory/
  ├── css/
  │   └── dashboard.css
  └── js/
      ├── inventory-management.js
      └── api-client.js    # Cliente para M-Inventario
```

### 4️⃣ Prioridad Media - Integración con Microservicios

1. Integración con M-Inventario:
- [ ] Implementar cliente API para M-Inventario
- [ ] Configurar endpoints en inventory/views.py
- [ ] Manejar errores de conexión y timeout
- [ ] Implementar caché de datos cuando sea apropiado

2. Comunicación Frontend-Backend:
- [ ] Implementar endpoints REST por app
- [ ] Actualizar llamadas AJAX/fetch para nuevo auth modal
- [ ] Configurar CSRF para peticiones asíncronas
- [ ] Implementar manejo de errores en UI

3. Optimización y Limpieza:
- [ ] Eliminar código legacy en gateway_app
- [ ] Revisar y actualizar dependencias
- [ ] Optimizar carga de assets estáticos
- [ ] Implementar lazy loading donde sea apropiado

## 🔍 Puntos de Verificación

### Frontend
- [x] Navegación básica implementada
- [-] Estilos cargan parcialmente (faltan imágenes)
- [x] JavaScript base funcionando
- [x] Responsive design base implementado

### Backend
- [-] Autenticación funciona parcialmente
- [ ] APIs no responden correctamente
- [x] Manejo de errores implementado
- [x] Logs configurados y funcionando

### Problemas Detectados y Soluciones

1. Sistema de Autenticación
   - Problema: Sistema actual usa páginas completas
   - Solución: Implementar modal/notificación de login
   - Tarea: Crear nuevos endpoints JSON y UI moderna

2. Archivos Legacy en gateway_app
   - Problema: Templates y static files en ubicación antigua
   - Solución: Migrar a nuevas apps y eliminar obsoletos
   - Tarea: Mover archivos y actualizar referencias

3. Integración con M-Inventario
   - Problema: Errores de conexión y timeout
   - Solución: Implementar cliente API robusto con retry
   - Ubicación: ElectroPlus-M-Inventario (microservicio)

## 📈 Próximos Pasos Inmediatos

1. ✅ Crear nuevas apps Django
2. 🚧 Implementar nuevo sistema de autenticación
   - [ ] Crear modal/notificación de login
   - [ ] Actualizar endpoints de auth para JSON
   - [ ] Migrar lógica de autenticación

3. 🚧 Migración de archivos
   - [ ] Mover templates de gateway_app a nuevas apps
   - [ ] Mover archivos estáticos de gateway_app
   - [ ] Eliminar carpetas obsoletas

4. 🚧 Integración con M-Inventario
   - [ ] Implementar cliente API robusto
   - [ ] Manejar errores y timeouts
   - [ ] Configurar caché de datos

5. 🚧 Limpieza final
   - [ ] Eliminar código legacy
   - [ ] Verificar todas las rutas
   - [ ] Probar flujos completos

## 🎯 Objetivo Final

Sistema modular y mantenible con:
- Separación clara de responsabilidades
- Código reutilizable y DRY
- Experiencia de usuario mejorada
- Base sólida para futuras mejoras

---

## 📝 Notas de Implementación

1. Mantener compatibilidad con microservicios existentes
2. Documentar cambios en README
3. Realizar pruebas después de cada migración
4. Mantener respaldos de archivos críticos

## ⚠️ Consideraciones de Seguridad

1. Validar todos los inputs de usuario
2. Implementar CSRF en todas las formas
3. Verificar permisos en vistas protegidas
4. Sanitizar datos en templates