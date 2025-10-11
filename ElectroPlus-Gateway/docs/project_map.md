# Mapa del proyecto ElectroPlus (Gateway)

Fecha: 11 de octubre de 2025 (Actualizado)

Objetivo: documento que mapea archivos importantes del proyecto, sus conexiones (URLs/vistas/templates/static), gaps (rutas o includes faltantes) y recomendaciones para arreglar el front-end.

---

## Instrucciones de uso

- Cada sección detalla: `Archivo`, `Conecta con`, `Tipo de conexión`, `Estado actual`, y `Recomendación/Acción`.
- Las recomendaciones están priorizadas (P0 = crítico, P1 = importante, P2 = deseable).
- Revisa especialmente las secciones "Decisiones de templates" y "Correcciones realizadas".

---

## Resumen ejecutivo

- Estructura principal:
  - Gateway principal: `ElectroPlus-Gateway/`
  - Apps del frontend: `storefront` (público), `sales` (carrito/ventas), `inventory` (admin), `gateway_app` (auth/core)
  - Microservicios: VENTAS, INVENTARIO (conexión vía settings.MICROSERVICES)

- Estado actual (11/Oct/2025):
  - Views Auth: Unificado en `gateway_app/views.py` (eliminado views_auth.py por duplicación)
  - Templates: Eliminados duplicados, manteniendo versiones canónicas en paths correctos
  - Autenticación: Centralizada en gateway_app, delegación a microservicios
  - Carrito: Duplicación entre storefront/sales pendiente de resolver

---

## Decisiones de templates (11/Oct/2025)

### Templates mantenidos (canonical):

1. Home page:
   - Mantener: `storefront/templates/storefront/home.html`
   - Razón: Mejor estructura y contenido (carousel, secciones destacadas)
   - Mejoras incorporadas: 
     - Manejo de errores de `shop/home.html`
     - Sistema de notificaciones toast

2. Footer:
   - Mantener: `storefront/templates/includes/footer.html`
   - Razón: Más completo, incluye:
     - Newsletter con modal y JS
     - Íconos Font Awesome
     - Links dinámicos con urls nombradas
     - Estructura responsive mejorada

3. Base templates:
   - Principal: `storefront/templates/base.html`
   - Dashboard: `storefront/templates/dashboard/base.html`

### Templates eliminados/archivados:

Backups en `storefront/templates/archive/`:
- `storefront-includes-navbar.html.bak`
- `storefront-includes-footer.html.bak`
- `storefront-base-base.html.bak`
- `dashboard-base.html.bak`

---

## Correcciones realizadas (gateway_app/gateway_core)

### gateway_app:

1. Estructura actual:
```
gateway_app/
  __init__.py
  views.py           # Unificado: auth + dashboard views
  models.py          # User, Profile, etc.
  forms.py           # LoginForm, RegisterForm
  urls.py           # Auth routes + dashboard routes
```

2. Cambios principales:
- ✓ Eliminado: `views_auth.py` (código migrado a `views.py`)
- ✓ Simplificado: rutas de autenticación en `urls.py`
- ✓ Unificado: manejo de sesión/auth en un solo lugar

3. Funciones importantes en views.py:
```python
# Auth core
authenticate_with_service()  # Conexión a microservicio
login_view()               # Vista form tradicional
login_api()               # Endpoint API
register_view()           # Registro form
register_api()            # Registro API

# Dashboards
dashboard_view()          # Router según rol
admin_dashboard()         # Stats admin
employee_dashboard()      # Vista empleado
customer_dashboard()      # Vista cliente
```

### gateway_core:

1. URLs principales (urls.py):
```python
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('storefront.urls')),        # Frontend público
    path('shop/', include('sales.urls')),        # Carrito/ventas
    path('dashboard/', include('inventory.urls')), # Admin
    path('auth/', include('gateway_app.urls')),   # Autenticación
]
```

2. Settings relevantes:
```python
INSTALLED_APPS = [
    'storefront',
    'sales',
    'inventory',
    'gateway_app',
    # ...
]

TEMPLATES = {
    'DIRS': [
        BASE_DIR / 'templates',
        BASE_DIR / 'storefront' / 'templates',
    ],
    'context_processors': [
        'storefront.context_processors.cart',
        'storefront.context_processors.categories',
    ]
}

MICROSERVICES = {
    'VENTAS': {'BASE_URL': '...', 'API_KEY': '...'},
    'INVENTARIO': {'BASE_URL': '...', 'API_KEY': '...'},
}
```


## Estado actual de rutas y templates

### App: storefront (frontend público)

| URL | Vista | Template | Estado | Notas |
|-----|-------|----------|--------|-------|
| `/` | `storefront.views.home` | `storefront/home.html` | ✓ OK | Template actualizado |
| `/productos/` | `views.product_list` | `shop/product_list.html` | ⚠️ Path mismatch | Decidir ubicación |
| `/producto/<slug>/` | `views.product_detail` | `shop/product_detail.html` | ⚠️ Path mismatch | Decidir ubicación |
| `/carrito/` | `views.cart` | `shop/cart.html` | ⚠️ Duplicado | Conflicto con sales |

### App: sales (carrito/checkout)

| URL | Vista | Template | Estado | Notas |
|-----|-------|----------|--------|-------|
| `/shop/cart/` | `sales.views.cart_view` | `sales/cart.html` | ⚠️ Duplicado | Conflicto con storefront |
| `/shop/checkout/` | `views.checkout` | `sales/checkout.html` | ✓ OK | Verificar microservicio |

### App: inventory (admin)

| URL | Vista | Template | Estado | Notas |
|-----|-------|----------|--------|-------|
| `/dashboard/` | `views.dashboard_home` | `inventory/dashboard/home.html` | ✓ OK | - |
| `/dashboard/products/` | `views.product_management` | `inventory/product_management.html` | ✓ OK | - |

### App: gateway_app (auth)

| URL | Vista | Template | Estado | Notas |
|-----|-------|----------|--------|-------|
| `/auth/login/` | `views.login_view` | `auth/login.html` | ✓ OK | Unificado en views.py |
| `/auth/register/` | `views.register_view` | `auth/register.html` | ✓ OK | Unificado en views.py |
| `/auth/dashboard/` | `views.dashboard_view` | (redirecciones) | ✓ OK | Router por rol |


### Áreas pendientes de revisión (P0 = crítico)

1. [P0] Carrito duplicado:
   - `storefront.cart`: Session-based, context processor
   - `sales.cart`: Session + DB Order
   - Decisión pendiente: ¿Centralizar en storefront o sales?

2. [P0] Templates shop vs raíz:
   - Actual: Vistas buscan en `storefront/` pero templates en `storefront/shop/`
   - Opciones:
     a) Mover templates de shop/ a raíz
     b) Actualizar vistas para usar shop/
     c) Definir nueva estructura

3. [P1] Microservicios:
   - Verificar manejo de errores/timeout
   - Implementar fallbacks para desarrollo
   - Documentar endpoints y payloads

4. [P2] Optimizaciones:
   - Revisar context processors (¿cachear categories?)
   - Validar STATIC_URL y collectstatic
   - Implementar tests de templates


## Comandos útiles (testing)

```bash
# Verificar templates
python manage.py check

# Test carrito
python manage.py test storefront.tests.test_cart
python manage.py test sales.tests.test_cart

# Probar microservicios
python manage.py test gateway_app.tests.test_microservices
```

---

## Siguiente fase recomendada

1. Definir ubicación final de templates shop/
2. Resolver duplicación de carrito
3. Implementar tests de integración
4. Documentar API microservicios

Nota: Las decisiones sobre templates están tomadas y documentadas. Esperando confirmación para:
- Mover templates de shop/ a ubicación final
- Consolidar implementación de carrito
- Generar tests automáticos

| URL (completa) | Pattern | Vista (módulo:función) | Plantilla referenciada | Plantilla encontrada (ruta) | Estado | Observaciones / Recomendación |
|---|---|---|---|---|---|---|
| `/` | `` | `storefront.views.home` | `storefront/home.html` | `storefront/templates/storefront/home.html` | Exists | OK |
| `/productos/` | `productos/` | `storefront.views.product_list` | `storefront/product_list.html` | `storefront/templates/storefront/shop/product_list.html` (existe) | Mismatch | Vista busca `storefront/product_list.html` pero template está en `storefront/shop/` — mover o actualizar vista.
| `/producto/<slug:slug>/` | `producto/<slug:slug>/` | `storefront.views.product_detail` | `storefront/product_detail.html` | `storefront/templates/storefront/shop/product_detail.html` (existe) | Mismatch | Ver arriba.
| `/categoria/<slug:slug>/` | `categoria/<slug:slug>/` | `storefront.views.category` | `storefront/category.html` | `storefront/templates/storefront/shop/category.html` ? | Check | Si `shop/category.html` existe, actualizar vista; si no, crear template.
| `/buscar/` | `buscar/` | `storefront.views.search` | `storefront/search_results.html` | `storefront/templates/storefront/shop/search_results.html` ? | Check | Revisar ubicación exacta.
| `/ofertas/` | `ofertas/` | `storefront.views.ofertas` | `storefront/ofertas.html` | `storefront/templates/storefront/shop/ofertas.html` ? | Check | Revisar ubicación.
| `/carrito/` | `carrito/` | `storefront.views.cart` | `storefront/cart.html` | `storefront/templates/storefront/shop/cart.html` (existe) | Mismatch | Duplicación funcional: `sales` también provee carrito. Recomiendo centralizar en `storefront` o exportar API común.
| `/carrito/agregar/` | `carrito/agregar/` | `storefront.views.cart_add` | (POST handler) | N/A | Exists (API) | API basada en sesión.
| `/checkout/` | `checkout/` | `storefront.views.checkout` | `storefront/checkout.html` | `storefront/templates/storefront/shop/checkout.html` (existe) | Mismatch | Ver arriba.
| `/checkout/confirmar/` | `checkout/confirmar/` | `storefront.views.checkout_confirm` | `storefront/checkout_confirm.html` | Missing | Missing | Crear o actualizar referencia.
| `/perfil/` | `perfil/` | `storefront.views.profile` | `storefront/profile.html` | Missing | Missing | Depende de integración con microservicio; placeholder recomendado.
| `/pedidos/` | `pedidos/` | `storefront.views.orders` | `storefront/orders.html` | Missing | Missing | Requiere integración MS Ventas; placeholder posible.
| `/sobre-nosotros/` | `sobre-nosotros/` | `storefront.views.about` | `storefront/about.html` | `storefront/templates/storefront/about.html` ? | Check | Revisar si existe; crear si falta.
| `/api/cart/add/` | `api/cart/add/` | `storefront.views.api_cart_add` | JSON response | N/A | Exists | OK (session-based)
| `/api/cart/update/` | `api/cart/update/` | `storefront.views.api_cart_update` | JSON response | N/A | Exists | OK
| `/api/cart/remove/` | `api/cart/remove/` | `storefront.views.api_cart_remove` | JSON response | N/A | Exists | OK
| `/api/checkout/validate/` | `api/checkout/validate/` | `storefront.views.api_checkout_validate` | JSON response | N/A | Exists/Check | OK if implemented

**Notas generales `storefront`:**
- Hay plantillas activas bajo `storefront/templates/storefront/shop/`. Las vistas en `storefront.views` refieren plantillas en `storefront/` (sin `shop/`). Esto causa muchos "Mismatch". Opciones:
  1. Mover los templates `shop/*` a `storefront/` (preferible si no hay colisiones).
  2. Actualizar las vistas para renderizar `storefront/shop/<template>.html`.
  3. Definir convención y aplicar consistentemente (documentaré cambios si me das OK).
- Carrito: hay implementación de carrito/API en `storefront` (session-cart) y duplicada en `sales`. Recomiendo consolidar en una sola capa (p.ej. `storefront.cart` como servicio, con endpoints API consumidos por `sales` si necesario).

### App: sales (mount: `/shop/`)

| URL (completa) | Pattern | Vista | Plantilla referenciada | Plantilla encontrada | Estado | Observaciones |
|---|---|---|---|---|---|---|
| `/shop/` | `` | `sales.views.shop_home` | `sales/shop_home.html` | `sales/templates/sales/shop_home.html` ? | Check | Ver si redirigir a `storefront:home` en lugar de duplicar.
| `/shop/cart/` | `cart/` | `sales.views.cart_view` | `sales/cart.html` | `sales/templates/sales/cart.html` (existe) | Exists | Doble implementación de carrito: sales vs storefront.
| `/shop/checkout/` | `checkout/` | `sales.views.checkout` | `sales/checkout.html` | `sales/templates/sales/checkout.html` (existe) | Exists | Duplicación de checkout.
| `/shop/order/confirmation/<order_number>/` | `order/confirmation/<str:order_number>/` | `sales.views.order_confirmation` | `sales/order_confirmation.html` | `sales/templates/sales/order_confirmation.html` (existe) | Exists | OK
| `/shop/api/cart/add/` | `api/cart/add/` | `sales.views.cart_add` | JSON | N/A | Exists | API similar a `storefront` — considerar unificar.
| `/shop/api/process-order/` | `api/process-order/` | `sales.views.process_order` | JSON | N/A | Exists | Implementa creación local de Order + ajuste de stock; overlap con `storefront.checkout_confirm` que delega a microservicio.

**Notas `sales`:**
- `sales` contiene una implementación completa de carrito y checkout (session-based + Order model usage). Esto compite con la lógica en `storefront`. Decide una única fuente de verdad: si `sales` es la app responsable por procesos de venta, entonces `storefront` debe delegar a `sales` o usar su API; si `storefront` es el frontend, `sales` debería exponer APIs.

### App: inventory (mount: `/dashboard/`)

| URL (completa) | Pattern | Vista | Plantilla referenciada | Plantilla encontrada | Estado | Observaciones |
|---|---|---|---|---|---|---|
| `/dashboard/` | `` | `inventory.views.dashboard_home` | `inventory/dashboard/admin_dashboard.html` | `inventory/templates/inventory/dashboard/admin_dashboard.html` (existe) | Exists | OK (admin)
| `/dashboard/products/` | `products/` | `inventory.views.product_management` | `inventory/product_management.html` | `inventory/templates/inventory/product_management.html` (exists) | Exists | OK
| `/dashboard/api/products/` | `api/products/` | `inventory.views.product_list_create` | JSON | N/A | Exists | API ok

**Notas `inventory`:**
- El dashboard está centralizado aquí y no parece duplicar lógica con `storefront`/`sales`.

### App: gateway_app (mount: `/auth/`)

| URL (completa) | Pattern | Vista | Plantilla referenciada | Plantilla encontrada | Estado | Observaciones |
|---|---|---|---|---|---|---|
| `/auth/login/` | `login/` | `gateway_app.views.login_view` | `auth/login.html` | `storefront/templates/auth/login.html` ? | Check | Ver ubicación exacta de `auth/login.html` — puede estar en `templates/auth/`.
| `/auth/register/` | `register/` | `gateway_app.views.register_view` | `auth/register.html` | `storefront/templates/auth/register.html` ? | Check | Requiere verificación.
| `/auth/dashboard/` | `dashboard/` | `gateway_app.views.dashboard_view` | redirects to role dashboards | N/A | Exists | Admin/employee/customer dashboards render templates en `dashboard/` paths.
| `/auth/api/login/` | `api/login/` | `gateway_app.views.login_api` | JSON | N/A | Exists | OK

**Notas `gateway_app`:**
- `gateway_app` actúa como gateway hacia microservicios (VENTAS/INVENTARIO). Sus vistas tie­nen lógica de conexión a microservicios y renderizan plantillas de `auth`/`dashboard`. Asegurar que las plantillas `auth/*` y `dashboard/*` estén en el path de templates configurado.

## Detecciones de funciones duplicadas / áreas para consolidar

1. Carrito y APIs de carrito:
  - `storefront.views` implementa: `cart`, `cart_add`, `cart_update`, `cart_remove`, `api_cart_*`.
  - `sales.views` implementa funciones equivalentes: `cart_view`, `cart_add`, `cart_update`, `cart_remove`, `process_order`.
  - Recomendación: elegir una implementación (preferible: `storefront.cart` como servicio reusado) y exponer API en una sola app. Actualizar la otra app para consumir esa API.

2. Checkout / Procesamiento de pedidos:
  - `storefront.checkout_confirm` delega el pedido al microservicio de Ventas.
  - `sales.process_order` crea Order y actualiza stock localmente.
  - Recomendación: decidir si el flujo debe delegar a microservicios (arquitectura distribuida) o manejarse localmente. Mantener un único flujo para evitar inconsistencias.

3. Plantillas duplicadas/variantes:
  - Había versiones duplicadas de `includes/navbar.html`, `includes/footer.html` y varias bases. Ya archivadas y eliminadas de las rutas activas.
  - Recomendación: mantener `storefront/templates/includes/` y `storefront/templates/storefront/base.html` como canonical; mover o actualizar cualquier plantilla en `shop/` según convención decidida.

## Pasos recomendados y próximos cambios automáticos (opcional)

1. (Automático, opcional) Generar CSV con las filas de la tabla anterior para revisión en Excel/Sheets. (Puedo generarlo ahora).
2. (Manual) Decidir convención: "vistas renderizan `storefront/<page>.html`" vs "vistas renderizan `storefront/shop/<page>.html`". Si eliges mover templates a `storefront/` lo hago de forma segura y actualizo las rutas referenciadas.
3. Consolidar el carrito en una sola app: refactor simple para que `sales` importe/consuma `storefront.cart` API.
4. Ejecutar smoke tests (GET `/`, GET product page, POST add-to-cart) y reportar resultados.

---

He dejado un registro de las eliminaciones en la sección "Cambios realizados durante esta sesión" y las copias de seguridad siguen en `storefront/templates/archive/` por si quieres recuperar algo.

Dime si quieres que:
- genere el CSV exportable ahora (sí/no),
- mueva automáticamente los templates `shop/*` a `storefront/` para eliminar los mismatches (sí/no),
- o que empiece por ejecutar smoke tests (necesitaré arrancar el servidor de dev local y te mostraré resultados).

---

Si quieres, genero ahora:
- una tabla automática (CSV/Markdown) que liste `urlpatterns` por app y la plantilla asociada (si existe),
- o un script de smoke tests (3 pruebas básicas) y lo añado al repo.

Dime qué prefieres y sigo con el siguiente paso.

---

## Tabla automática: rutas (urlpatterns) -> template usado (estado)

La siguiente tabla muestra las rutas (por app), la plantilla que la vista intenta renderizar y el estado (Exists = encontrada, Missing = no encontrada). Use esto para localizar rápidamente plantillas faltantes o rutas con nombres inconsistentes.

### App: storefront

| Ruta (pattern) | Vista | Template en la vista | Estado | Recomendación |
|---|---|---:|---:|---|
| '' | views.home | `storefront/home.html` | Exists | - |
| productos/ | views.product_list | `storefront/product_list.html` | Missing | Actualizar vista para usar `storefront/shop/...` o mover template a `storefront/product_list.html` |
| producto/<slug:slug>/ | views.product_detail | `storefront/product_detail.html` | Missing (template en `storefront/shop/product_detail.html`) | Unificar rutas o mover template |
| categoria/<slug:slug>/ | views.category | `storefront/category.html` | Missing | Crear template o actualizar vista para `storefront/shop/...` |
| buscar/ | views.search | `storefront/search.html` | Missing | Crear template |
| ofertas/ | views.ofertas | `storefront/ofertas.html` | Missing | Crear template |
| carrito/ | views.cart | `storefront/cart.html` | Missing (hay `storefront/shop/cart.html`) | Unificar ubicación de template |
| checkout/ | views.checkout | `storefront/checkout.html` | Missing (hay `storefront/shop/checkout.html`) | Unificar ubicación de template |
| checkout/confirmar/ | views.checkout_confirm | `storefront/checkout_confirm.html` | Missing | Crear template |
| perfil/ | views.profile | `storefront/profile.html` | Missing | Crear template |
| perfil/editar/ | views.profile_edit | `storefront/profile_edit.html` | Missing | Crear template |
| pedidos/ | views.orders | `storefront/orders.html` | Missing | Crear template |
| pedido/<str:order_id>/ | views.order_detail | `storefront/order_detail.html` | Missing | Crear template |
| sobre-nosotros/ | views.about | `storefront/about.html` | Missing | Crear template |
| contacto/ | views.contact | `storefront/contact.html` | Missing | Crear template |
| faq/ | views.faq | `storefront/faq.html` | Missing | Crear template |
| envios/ | views.shipping | `storefront/shipping.html` | Missing | Crear template |
| devoluciones/ | views.returns | `storefront/returns.html` | Missing | Crear template |
| garantia/ | views.warranty | `storefront/warranty.html` | Missing | Crear template |
| privacidad/ | views.privacy | `storefront/privacy.html` | Missing | Crear template |
| terminos/ | views.terms | `storefront/terms.html` | Missing | Crear template |
| api/cart/add/ | views.api_cart_add | JSON | Exists | - |
| api/cart/update/ | views.api_cart_update | JSON | Exists | - |
| api/cart/remove/ | views.api_cart_remove | JSON | Exists | - |
| api/checkout/validate/ | views.api_checkout_validate | JSON | Exists | - |

### App: sales

| Ruta (pattern) | Vista | Template en la vista | Estado | Recomendación |
|---|---|---:|---:|---|
| '' | views.shop_home | `sales/shop_home.html` | Missing | Crear `sales/shop_home.html` o redirigir a `storefront:home` |
| cart/ | views.cart_view | `sales/cart.html` | Exists | - |
| checkout/ | views.checkout | `sales/checkout.html` | Exists | - |
| order/confirmation/<str:order_number>/ | views.order_confirmation | `sales/order_confirmation.html` | Exists | - |
| api/cart/add/ | views.cart_add | JSON | Exists | - |
| api/cart/update/<int:item_id>/ | views.cart_update | JSON | Exists | - |
| api/cart/remove/<int:item_id>/ | views.cart_remove | JSON | Exists | - |
| api/process-order/ | views.process_order | JSON | Exists | - |

### App: inventory

| Ruta (pattern) | Vista | Template en la vista | Estado | Recomendación |
|---|---|---:|---:|---|
| '' | views.dashboard_home | `inventory/dashboard/home` (ej. `inventory/dashboard/admin_dashboard.html`) | Exists | - |
| products/ | views.product_management | `inventory/product_management.html` | Exists | - |
| products/import/ | views.product_import | Template/JSON | Exists? | Revisar implementación (API vs UI) |

### App: gateway_app (auth)

| Ruta (pattern) | Vista | Template / Tipo | Estado | Recomendación |
|---|---|---:|---:|---|
| api/login/ | views_auth.login_api | API JSON | Exists | - |
| api/logout/ | views_auth.logout_api | API JSON | Exists | - |
| api/register/ | views_auth.register_api | API JSON | Exists | - |
| api/check-auth/ | views_auth.check_auth | API JSON | Exists | - |

---

## Observaciones rápidas derivadas de la tabla

- Hay una clara inconsistencia entre las rutas esperadas por las vistas en `storefront/views.py` (templates ubicadas en `storefront/`) y las plantillas reales organizadas bajo `storefront/templates/storefront/shop/`.
- Soluciones rápidas posibles:
  1. Mover los templates de `storefront/templates/storefront/shop/*.html` a `storefront/templates/storefront/` (si no hay conflicto de nombres).
  2. O actualizar las vistas en `storefront/views.py` para renderizar las plantillas con la ruta actual (`storefront/shop/product_detail.html`, etc.).
  3. Unificar el patrón de templates (usar `storefront/<page>.html` o `storefront/shop/<page>.html`) y documentar la convención.

---

## Próximos pasos automáticos que puedo ejecutar ahora

1. Generar un CSV/tabla completa con todas las rutas del proyecto y marcar las plantillas faltantes (para exportar y revisar). (Puedo hacerlo ahora.)
2. Crear plantillas faltantes mínimas (placeholders) para que el servidor deje de romperse en esas rutas (opción rápida y reversible).
3. Actualizar las vistas para apuntar a las plantillas existentes bajo `storefront/shop/` (si prefieres no mover archivos).
4. Añadir tests de humo (3-5 pruebas) para validar home, producto y API de carrito.

Indícame cuál de estas acciones quieres que ejecute: generar CSV, crear placeholders, actualizar vistas, o añadir tests. Trabajaré en esa tarea y actualizaré `docs/project_map.md` con los resultados.
