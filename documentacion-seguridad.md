# Documentación de Seguridad - ElectroPlus Microservicios

## Estado Actual y Tareas Pendientes

### Implementado:
1. Configuración básica de CORS para desarrollo
   - Orígenes permitidos: localhost:3000 y 127.0.0.1:3000
   - Configuración temporal para desarrollo del frontend

### Pendiente:

#### 1. Sistema de Identificación de Productos
  ```
  Laptop HP 15 → com0hp015int
  - com0: Computadora
  - hp: Marca HP
  - 015: Modelo 15
  - int: Procesador Intel
  ```
Este archivo fue consolidado en `documentacion_unificada.md`.

Consulta `documentacion_unificada.md` para el estado de seguridad, tareas pendientes, y recomendaciones detalladas.
  - Facilita búsquedas y clasificación
  - Mejora trazabilidad del inventario

#### 2. Seguridad de Autenticación
- Implementar hashing para contraseñas de usuarios
- Sistema de login seguro
- Tokens de autenticación para sesiones

#### 3. Seguridad Entre Microservicios
- Implementar middleware de autenticación
- Claves por servicio (recomendado): usar `SECRET_<SERVICIO>` en variables de entorno o tokens HMAC/JWT
- En desarrollo anterior se usó `SECRET_KEY_MICRO` para validación; se ha eliminado por motivos de mantenimiento y claridad. Reemplazar por `SECRET_INVENTARIO`, `SECRET_VENTAS`, etc., o por tokens firmados.

### 2. Rate Limiting
Se han implementado límites de tasa para prevenir abusos:
- Usuarios anónimos: 100 peticiones por día
- Usuarios autenticados: 1000 peticiones por día

### 3. CORS (Cross-Origin Resource Sharing)
Configuración de CORS para permitir peticiones desde el frontend:

Orígenes permitidos:
- http://localhost:3000 (desarrollo)
- http://127.0.0.1:3000 (desarrollo)

Métodos HTTP permitidos:
- DELETE
- GET
- OPTIONS
- PATCH
- POST
- PUT

### 4. Seguridad General
Se han implementado las siguientes medidas de seguridad:

- **Content Type Nosniff**: Previene ataques de tipo MIME sniffing
  ```python
  SECURE_CONTENT_TYPE_NOSNIFF = True
  ```

- **XSS Protection**: Activa la protección XSS del navegador
  ```python
  SECURE_BROWSER_XSS_FILTER = True
  ```

- **Clickjacking Protection**: Previene ataques de clickjacking
  ```python
  X_FRAME_OPTIONS = 'DENY'
  ```

- **Cookies Seguras**: 
  ```python
  CSRF_COOKIE_SECURE = True
  SESSION_COOKIE_SECURE = True
  ```

## Buenas Prácticas de Seguridad

1. Variables de Entorno
   - Las claves secretas y configuraciones sensibles se manejan a través de variables de entorno
   - No se incluyen credenciales en el código fuente

2. Validación de Datos
   - Se utilizan los serializadores de Django REST Framework para validar los datos de entrada
   - Se implementan validaciones personalizadas para reglas de negocio específicas

3. Comunicación Segura
   - La comunicación entre microservicios está protegida por tokens
   - Se implementa rate limiting para prevenir abusos

## Recomendaciones para Producción

1. SSL/TLS
   - Habilitar HTTPS en producción
   - Configurar certificados SSL válidos

2. Ajustes de Seguridad Adicionales
   - Deshabilitar DEBUG en producción
   - Configurar ALLOWED_HOSTS apropiadamente
   - Implementar backup y planes de recuperación

3. Monitoreo
   - Implementar logging de eventos de seguridad
   - Monitorear intentos de acceso no autorizados
   - Revisar regularmente los logs de rate limiting

4. Actualizaciones
   - Mantener todas las dependencias actualizadas
   - Revisar regularmente las actualizaciones de seguridad de Django