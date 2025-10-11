# Diagnóstico del Gateway (ElectroPlus)

Fecha: 2025-10-11

## Resumen ejecutivo

Realicé un diagnóstico completo del proyecto Gateway (`ElectroPlus-Gateway`). Se comprobaron dependencias, entorno Python, configuración de Django, migraciones, puertos y disponibilidad de los microservicios, y estado de las pruebas de integración.

Hallazgos principales:
- Dependencias listadas en `requirements.txt` presentes en el entorno. `django-debug-toolbar` fue instalado durante el diagnóstico.
- El entorno Python activo apunta a: `C:\Users\Juan-PC\AppData\Local\Programs\Python\Python310\python.exe` (no se detectó un `VIRTUAL_ENV` activo desde las variables de entorno en el momento de la comprobación).
- Existe un archivo `.env` en el directorio del Gateway con configuraciones (se muestran abajo) — contiene credenciales sensibles; se enmascaran en este informe.
- Las apps definidas en `INSTALLED_APPS` incluyen `gateway_app`, `storefront`, `inventory`, `rest_framework` y `debug_toolbar`.
- Puertos: 8001 y 8002 están escuchando en la máquina (servicios de M-Inventario y M-Ventas). El Gateway (8000) no estaba escuchando al inicio del diagnóstico; se arrancó manualmente durante la sesión y ahora responde.
- Migraciones: las migraciones de `debug_toolbar` estaban pendientes antes de la instalación; aplicar `migrate` es necesario tras instalar nuevas apps.
- Las pruebas de integración están escritas para una versión anterior que espera un `GatewayViewSet` (ViewSet) mientras que el proyecto actual implementa vistas basadas en funciones; esto causa errores de importación.

---

## Detalle técnico

### 1) Dependencias

Archivo `requirements.txt` (contenido):

```
Django==5.2.7
djangorestframework==3.16.1
django-cors-headers==4.9.0
drf-spectacular==0.28.0
gunicorn==23.0.0
python-dotenv==1.1.1
requests==2.32.5
responses==0.25.2
pytest==8.3.2
```

Salida `pip freeze` (resumen):
- Django==5.2.7
- djangorestframework==3.16.1
- django-cors-headers==4.9.0
- django-debug-toolbar==6.0.0
- drf-spectacular==0.28.0
- gunicorn==23.0.0
- python-dotenv==1.1.1
- requests==2.32.5
- responses==0.25.2
- pytest==8.3.2
- mysql-connector-python / mysqlclient presentes

Observación: Las dependencias principales están instaladas y coinciden con `requirements.txt`. No se detectaron conflictos críticos en el listado.


### 2) Entorno Python y virtualenv

- Python ejecutable: `C:\Users\Juan-PC\AppData\Local\Programs\Python\Python310\python.exe`
- `VIRTUAL_ENV` no detectada en variables (la variable `$env:VIRTUAL_ENV` estaba vacía). Sin embargo, usted activó el venv poco antes (según el contexto de terminal), por lo que recomiendo confirmar que está activado en la sesión donde ejecute `start.bat`.

Recomendación: active el virtualenv con:

```powershell
& D:/ElectroPluz-web-/venv/Scripts/Activate.ps1
``` 

y luego confirme con:

```powershell
python --version
where python
pip freeze
```


### 3) Variables de entorno y `.env`

El proyecto usa `python-dotenv` para cargar `.env` desde `BASE_DIR / '.env'`.

Archivo `.env` detectado (se enmascararon valores sensibles):

```
DEBUG=True
SECRET_KEY=***** (oculto)
ALLOWED_HOSTS=localhost,127.0.0.1
MYSQL_HOST=interchange.proxy.rlwy.net
MYSQL_USER=root
MYSQL_PASSWORD=***** (oculto)
MYSQL_DATABASE=railway
MYSQL_PORT=38168
INVENTARIO_API_KEY=***** (oculto)
VENTAS_API_KEY=***** (oculto)
INVENTARIO_URL=http://localhost:8001/api/
VENTAS_URL=http://localhost:8002/api/
```

Observación: el Gateway está configurado para usar una base MySQL remota (host `interchange.proxy.rlwy.net` y puerto `38168`) pero `DATABASES` en `settings.py` está configurado para SQLite (db.sqlite3). Esto sugiere una posible inconsistencia: el `.env` indica MySQL mientras `settings.py` actualmente usa SQLite.

Recomendación: Verificar si `gateway_core/settings.py` debería usar MySQL en producción/desarrollo y ajustar `DATABASES` para leer de `.env` cuando aplique.


### 4) Configuración de Django (`gateway_core/settings.py`)

- `INSTALLED_APPS` incluye: `gateway_app`, `storefront`, `inventory`, `rest_framework`, `debug_toolbar`.
- `MIDDLEWARE` incluye `debug_toolbar.middleware.DebugToolbarMiddleware` y middlewares personalizados de `gateway_app`.
- `STATICFILES_DIRS` apuntan a directorios que existen (`static`, `storefront/static`, `inventory/static`). Se creó `static` durante el diagnóstico.
- `MICROSERVICES` se carga desde `.env` correctamente.

Observaciones:
- Se observó una advertencia al iniciar el servidor sobre `STATICFILES_DIRS` que se resolvió creando `static/`.
- Se detectaron migraciones pendientes para `debug_toolbar` tras la instalación; ejecutar `python manage.py migrate` es necesario.


### 5) Migraciones y base de datos

Estado de migraciones (muestreo): antes de instalar `debug_toolbar` había migraciones pendientes de esa app. Ejecutar:

```powershell
cd ElectroPlus-Gateway
python manage.py migrate
```

aplica las migraciones pendientes.

Nota: el proyecto contiene `db.sqlite3` en el directorio raíz (probablemente usado por defecto). Si la intención es usar MySQL (según `.env`), sincronizar `settings.py` y crear las credenciales de conexión es necesario.


### 6) Servicios y puertos

Comprobación netstat (resumen):
- Puerto 8001 -> LISTENING (PID asociado)
- Puerto 8002 -> LISTENING (PID asociado)
- El Gateway (8000) no estaba escuchando inicialmente; se lanzó durante el diagnóstico.

Prueba HTTP simple: no se pudo ejecutar un script inline POSIX en PowerShell por incompatibilidad del operador heredoc, pero se realizaron comprobaciones manuales durante la sesión. Al final, tras instalar `debug_toolbar` y aplicar cambios, el servidor del Gateway arrancó bajo `127.0.0.1:8000` en modo desarrollo.


### 7) Tests / Integración

- `tests/integration/test_gateway.py` intenta importar `GatewayViewSet` desde `gateway_app.views`. Actualmente `gateway_app.views` implementa vistas basadas en funciones (no existe `GatewayViewSet`), por lo que las pruebas fallan en la etapa de importación.

Recomendación: actualizar las pruebas para que utilicen las vistas actuales (por ejemplo, usando `APIClient` y llamando a las URLs en lugar de instanciar una ViewSet), o reintroducir/añadir una clase `GatewayViewSet` si esa API es necesaria para compatibilidad.


## Problemas detectados y recomendaciones (priorizadas)

1. Inconsistencia de base de datos:
   - Problema: `.env` contiene configuración MySQL, mientras `settings.py` usa SQLite.
   - Recomendación: decidir la DB que se usará y ajustar `gateway_core/settings.py` para leer credenciales de `.env`. Añadir instrucciones para crear la base y permisos, o documentar el uso de SQLite en desarrollo.

2. Migraciones pendientes:
   - Problema: migraciones de `debug_toolbar` (y posiblemente otras) no aplicadas.
   - Recomendación: ejecutar `python manage.py migrate` en el entorno correcto.

3. Virtualenv / entorno reproducible:
   - Problema: `VIRTUAL_ENV` no estaba establecido en la sesión usada para comprobar `pip freeze` (aunque activaste el venv más tarde). Usar siempre el venv del proyecto para evitar discrepancias.
   - Recomendación: documentar y automatizar la activación del venv en `start_services.ps1` o `start.bat`.

4. Tests desactualizados:
   - Problema: tests esperan `GatewayViewSet` (ViewSet) pero el código actual utiliza vistas funcionales.
   - Recomendación: actualizar tests/integration/test_gateway.py para usar `APIClient` o ajustar imports / mocks.

5. Codificación de salida en PowerShell:
   - Problema: caracteres acentuados aparecían mal en la salida.
   - Recomendación: configurar UTF-8 en PowerShell al inicio de `start.bat` / `start_services.ps1` con:

```powershell
$OutputEncoding = [Console]::OutputEncoding = [Text.UTF8Encoding]::UTF8
```

6. Seguridad de secretos:
   - Observación: `.env` contiene secretos en texto claro (SECRET_KEY, MYSQL_PASSWORD, API KEYS).
   - Recomendación: mover secretos a variables de entorno del sistema o a un secret manager; excluir `.env` de repositorio si contiene secretos reales.


## Pasos sugeridos para resolver y validar (ordenados)

1. Activar virtualenv y confirmar:

```powershell
& D:/ElectroPluz-web-/venv/Scripts/Activate.ps1
python --version
where python
pip freeze
```

2. Aplicar migraciones:

```powershell
cd ElectroPlus-Gateway
python manage.py migrate
```

3. Verificar que el Gateway arranque:

```powershell
cd ElectroPlus-Gateway
python manage.py runserver 8000
```

4. Ejecutar tests/integración (tras ajustar tests si hace falta):

```powershell
$env:DJANGO_SETTINGS_MODULE = 'gateway_core.settings'
python -m pytest tests/integration/test_gateway.py -v
```

5. Revisar la configuración de base de datos en `gateway_core/settings.py` y unificar con `.env`.

6. Actualizar `start_services.ps1` / `start.bat` para activar el venv automáticamente, establecer UTF-8 y exportar `DJANGO_SETTINGS_MODULE` y `PYTHONPATH` necesarios.


## Archivos relevantes revisados

- `ElectroPlus-Gateway/requirements.txt`
- `ElectroPlus-Gateway/gateway_core/settings.py`
- `ElectroPlus-Gateway/.env` (leído y enmascarado)
- `ElectroPlus-Gateway/storefront/urls.py` (corregido para `api_profile_edit` durante la sesión)
- `ElectroPlus-Gateway/gateway_app/views.py` (verificado: no contiene `GatewayViewSet`)
- `tests/integration/test_gateway.py` (detectada discrepancia con el código actual)


## Conclusión

El Gateway está mayormente listo: dependencias están instaladas, debug-toolbar instalado y `static/` creado. Los puntos críticos a atender son:
- Aplicar migraciones pendientes
- Asegurar que el entorno virtual se active durante los scripts de inicio
- Resolver la inconsistencia entre `.env` (MySQL) y `settings.py` (SQLite)
- Actualizar las pruebas de integración para reflejar la implementación actual (funciones en lugar de ViewSet) o reintroducir la API esperada.

Si quieres, puedo continuar con cualquiera de estas tareas de forma automática:
- aplicar migraciones y arrancar servicios de forma controlada (y luego ejecutar tests)
- actualizar las pruebas de integración para usar `APIClient` en lugar de `GatewayViewSet`
- ajustar `gateway_core/settings.py` para leer y usar MySQL desde `.env`
- mejorar `start_services.ps1` para activar venv, establecer encoding y variables de entorno automáticamente

Dime cuál prefieres y lo implemento ahora. 
