# Documentación Unificada — ElectroPlus Microservicios

Última actualización: 2025-10-06

Este documento consolida la implementación, pruebas, problemas y recomendaciones de seguridad para los microservicios de ElectroPlus (M-Inventario, M-Ventas) y el API Gateway.

## Resumen ejecutivo
- Microservicios: M-Inventario (productos/stock) y M-Ventas (ventas, clientes).
- API Gateway: punto central para consolidar/combinar datos y exponer una única API al frontend.
- BD: MySQL (Railway) compartida por ambos microservicios.
- Estado: Servicios locales arrancan correctamente; endpoints básicos y flujo de venta integrados funcionan (ver sección de pruebas).

## Contenido
1. Arquitectura y stack
2. Configuración y cómo ejecutar (desarrollo)
3. Modelos y endpoints principales
4. Seguridad y autenticación inter-servicios
5. Pruebas realizadas y resultados
6. Problemas encontrados y soluciones aplicadas
7. Recomendaciones y próximos pasos

---

## 1. Arquitectura y stack
- Python 3.10+
- Django 4.2+/5.x (proyecto usa Django 5.2.7 localmente)
- Django REST Framework
- MySQL (Railway) con `mysqlclient`
- drf-spectacular para OpenAPI/Swagger
- django-cors-headers para CORS
- requests para comunicación entre microservicios

Estructura principal (resumen):
- ElectroPlus-M-Inventario/
  - inventario_core/ (settings, urls)
  - productos/ (models, serializers, views, urls)
- ElectroPlus-M-Ventas/
  - ventas_core/
  - ventas/ (models, serializers, views, urls)
- ElectroPlus-Gateway/
  - gateway_core/
  - gateway_app/ (views, serializers, urls)

## 2. Configuración y cómo ejecutar (desarrollo)
Requisitos: tener Python 3.10+, crear y activar venv, instalar dependencias.

PowerShell (Windows) — pasos mínimos:

```powershell
# Desde la raíz del workspace
python -m venv venv
.\venv\Scripts\Activate.ps1

# Instalar dependencias (ejemplo)
pip install -r requirements.txt
# Si no existe requirements.txt, instalar manualmente:
pip install django djangorestframework mysqlclient django-cors-headers drf-spectacular requests

# Migraciones y levantar servicios (en tres terminales separados):
# M-Inventario
cd .\ElectroPlus-M-Inventario
python manage.py migrate
python manage.py runserver 8001

# M-Ventas
cd ..\ElectroPlus-M-Ventas
python manage.py migrate
python manage.py runserver 8002

# API Gateway
cd ..\ElectroPlus-Gateway
python manage.py migrate
python manage.py runserver 8000
```

Endpoints de documentación (Gateway):
- http://localhost:8000/api/swagger/
- http://localhost:8000/api/schema/

> Nota: En desarrollo se permite CORS amplio; en producción restringir orígenes y configurar variables de entorno en Railway.

## 3. Modelos y endpoints principales
Resumen de modelos (ver `productos/models.py` y `ventas/models.py`):
- Categoria, Proveedor, Producto, HistorialInventario
- Usuario, Cliente, Venta, DetalleVenta, Devolucion

Endpoints implementados (resumen):
- M-Inventario
  - `GET /api/productos/` — listar productos
  - `GET /api/productos/{id}/` — detalle producto
  - `POST /api/productos/` — crear (si aplica)
  - `PATCH /api/productos/{id}/actualizar_stock/` — actualizar stock (entrada/salida)
  - `GET /api/categorias/`, `GET /api/proveedores/`
  - `GET /api/historial/` — historial de movimientos
- M-Ventas
  - `POST /api/ventas/` — crear venta (orquesta llamadas a M-Inventario para actualizar stock)
  - `GET /api/ventas/`, `GET /api/ventas/{id}/`
  - Endpoints para clientes, usuarios, devoluciones
- API Gateway
  - `GET /api/gateway/` — índice del Gateway
  - `GET /api/gateway/productos-stock/` — productos con stock y estadísticas
  - `GET /api/gateway/{cliente_id}/resumen-cliente/` — resumen consolidado por cliente

## 4. Seguridad y autenticación inter-servicios
Implementación actual:
- Uso de una clave secreta por microservicio (MICROSERVICES in settings) y envío en header `Authorization: Bearer <KEY>` para llamadas internas.
- CORS configurado en Gateway (`CORS_ALLOW_ALL_ORIGINS=True` en desarrollo).

Pendientes / recomendaciones:
- Implementar middleware que valide la autenticación entre servicios.
  - Nota: la variable `SECRET_KEY_MICRO` fue eliminada recientemente del `.env`. Recomendamos usar claves por servicio (`SECRET_INVENTARIO`, `SECRET_VENTAS`, etc.) o tokens firmados (HMAC/JWT) para la autenticación entre servicios.
  - Cambiar a tokens firmados (HMAC o JWT con clave compartida) para mayor seguridad y trazabilidad.
- Registrar `request_id` y correlacionar logs entre servicios.
- No exponer claves en repositorio; usar variables de entorno en Railway.

## 5. Pruebas realizadas y resultados
Pruebas ejecutadas (resumen):
- GET `/api/productos/`, `/api/categorias/`, `/api/proveedores/` — OK, respuestas JSON correctas.
- `POST /api/productos/{id}/actualizar_stock/` — pruebas de entrada (+5) y salida (-2) realizadas con éxito; historial actualizado.
- Flujo de venta (M-Ventas -> llama a M-Inventario): venta creada y stock actualizado; transacción distribuida verificada en pruebas manuales.

Archivos con resultados de pruebas:
- `documentacion-pruebas.md` (resumen), ahora consolidado aquí.

## 6. Problemas encontrados y soluciones aplicadas
Problemas detectados durante la sesión:
- Servidores se detuvieron al cerrar terminales (laboral). Solución: reiniciar y activar `venv` antes de `runserver`.
- Dependencias faltantes: instalar paquetes (`djangorestframework`, `django-cors-headers`, `drf-spectacular`, `requests`).
- Migraciones pendientes en el Gateway: ejecutar `python manage.py migrate`.

Soluciones propuestas y aplicadas:
- Añadí scripts y pasos en la documentación para crear/activar `venv`, instalar dependencias y ejecutar migraciones.
- Gateway: agregado `gateway_app` con vistas, serializadores y rutas; agregado configuración DRF/CORS y documentación OpenAPI.

## 7. Recomendaciones y próximos pasos (priorizados)
1. Seguridad (alta): implementar middleware de autenticación inter-servicios y reemplazar clave fija por token con expiración o HMAC.
2. Tests automáticos (media-alta): escribir pruebas unitarias e integración (especialmente test de venta que verifica llamadas a inventario). Preferible usar pytest + pytest-django.
3. Observabilidad (media): configurar logging estructurado y correlación `request_id`.
4. Hardening y despliegue (media): preparar `Procfile`, Gunicorn, y variables de entorno en Railway; revisar `ALLOWED_HOSTS` y SSL.
5. Documentación (baja): pulir y publicar `README.md` en el repositorio con instrucciones de despliegue y pruebas.

---

## Archivos relevantes
- `documentacion-implementacion.md` — apuntado a esta unificación.
- `documentacion-pruebas.md` — apuntado a esta unificación.
- `documentacion-problemas.md` — apuntado a esta unificación.
- `documentacion-seguridad.md` — apuntado a esta unificación.


## Contacto y créditos
Autor: Equipo/Estudiante — Evidencia 3
Repositorio: (subir al GitHub del curso, incluir README final)


---

Si quieres, actualizo los archivos individuales para que sean breves apuntes que enlacen a este documento y luego genero un `README.md` breve con comandos de inicio y un checklist para la entrega final.