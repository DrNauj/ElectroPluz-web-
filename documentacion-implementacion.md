# DOCUMENTACIÓN DE IMPLEMENTACIÓN (UNIFICADA)

Este archivo fue consolidado en `documentacion_unificada.md` para evitar duplicación.

Por favor consulta `documentacion_unificada.md` en la raíz del repositorio para la versión completa y actualizada de la documentación de implementación, configuración, modelos, endpoints y pasos de despliegue.

Resumen rápido:
- DB: MySQL (Railway) — ver `documentacion_unificada.md`.
- Endpoints y modelos: implementados en `ElectroPlus-M-Inventario` y `ElectroPlus-M-Ventas`.

-----

Archivo maestro: `documentacion_unificada.md`
   - ID (AutoField, primary_key)
   - Nombre (CharField, max_length=45)
   - Descripción (TextField, opcional)

2. **Proveedor**
   - ID (AutoField, primary_key)
   - Nombre (CharField, max_length=100)
   - Dirección (CharField, max_length=255, opcional)
   - Teléfono (CharField, max_length=20, opcional)
   - Email (EmailField, max_length=100, opcional)

3. **Producto**
   - ID (AutoField, primary_key)
   - Nombre (CharField, max_length=100)
   - Descripción (TextField, opcional)
   - Precio (DecimalField, max_digits=10, decimal_places=2)
   - Stock (IntegerField)
   - Categoría (ForeignKey a Categoria)
   - Proveedor (ForeignKey a Proveedor)

4. **HistorialInventario**
   - ID (AutoField, primary_key)
   - Producto (ForeignKey a Producto)
   - Tipo de Movimiento (CharField con choices)
   - Cantidad (IntegerField)
   - Fecha (DateTimeField)

#### M-Ventas (ventas/models.py)

1. **Usuario**
   - ID (AutoField, primary_key)
   - Nombre de Usuario (CharField, unique=True)
   - Contraseña (CharField)
   - Rol (CharField con choices)

2. **Cliente**
   - ID (AutoField, primary_key)
   - Nombres (CharField)
   - Apellidos (CharField)
   - Email (EmailField, unique=True)
   - Teléfono (CharField, opcional)
   - Dirección (CharField, opcional)

3. **Venta**
   - ID (AutoField, primary_key)
   - Fecha de Venta (DateTimeField)
   - Total (DecimalField)
   - Estado (CharField con choices)
   - Cliente (ForeignKey a Cliente)
   - Usuario (ForeignKey a Usuario)

4. **DetalleVenta**
   - ID (AutoField, primary_key)
   - Venta (ForeignKey a Venta)
   - Cantidad (IntegerField)
   - Precio Unitario (DecimalField)

5. **Devolucion**
   - ID (AutoField, primary_key)
   - Venta (ForeignKey a Venta)
   - Fecha de Devolución (DateTimeField)
   - Motivo (TextField, opcional)

### 1.3 Datos de Prueba Verificados

Se han verificado los siguientes datos en la base de datos:

#### Categorías
- Electrodomésticos
- Computadoras
- Smartphones
- Audio y Video
- Gaming

#### Productos (ejemplos)
- Laptop HP 15 ($2,499.99)
- Samsung Galaxy S21 ($3,299.99)
- Smart TV LG 55" ($2,799.99)
- PlayStation 5 ($2,999.99)
- Refrigeradora Samsung ($3,499.99)

### 1.4 API REST de Inventario

Se han implementado los siguientes endpoints REST para el microservicio de inventario:

#### Endpoints Disponibles

1. **Categorías** (`/api/categorias/`)
   - `GET /api/categorias/` - Listar todas las categorías
   - `GET /api/categorias/{id}/` - Obtener una categoría específica

2. **Proveedores** (`/api/proveedores/`)
   - `GET /api/proveedores/` - Listar todos los proveedores
   - `GET /api/proveedores/{id}/` - Obtener un proveedor específico

3. **Productos** (`/api/productos/`)
   - `GET /api/productos/` - Listar todos los productos
   - `GET /api/productos/{id}/` - Obtener un producto específico
   - `PATCH /api/productos/{id}/actualizar_stock/` - Actualizar el stock de un producto

4. **Historial de Inventario** (`/api/historial/`)
   - `GET /api/historial/` - Listar todos los movimientos
   - `GET /api/historial/?producto={id}` - Filtrar movimientos por producto

#### Documentación de la API

- Documentación interactiva: `/api/swagger/`
- Esquema OpenAPI: `/api/schema/`
- Documentación detallada: `/docs/`

#### Funcionalidades Implementadas

1. **Serializers**
   - Serialización básica y detallada de productos
   - Manejo de relaciones anidadas (productos con categorías y proveedores)
   - Campos de solo lectura para proteger datos críticos

2. **ViewSets**
   - Operaciones CRUD para productos
   - Endpoints de solo lectura para datos maestros (categorías y proveedores)
   - Endpoint especial para actualización de stock con validación

3. **Manejo de Transacciones**
   - Actualización atómica de stock
   - Registro automático en historial de inventario
   - Validación de stock suficiente

### 1.5 API REST de Ventas

Se han implementado los siguientes endpoints REST para el microservicio de ventas:

#### Endpoints Disponibles

1. **Usuarios** (`/api/usuarios/`)
   - `GET /api/usuarios/` - Listar todos los usuarios
   - `GET /api/usuarios/{id}/` - Obtener un usuario específico

2. **Clientes** (`/api/clientes/`)
   - `GET /api/clientes/` - Listar todos los clientes
   - `POST /api/clientes/` - Crear un nuevo cliente
   - `GET /api/clientes/{id}/` - Obtener un cliente específico
   - `PUT/PATCH /api/clientes/{id}/` - Actualizar un cliente
   - `DELETE /api/clientes/{id}/` - Eliminar un cliente

3. **Ventas** (`/api/ventas/`)
   - `GET /api/ventas/` - Listar todas las ventas
   - `POST /api/ventas/` - Crear una nueva venta
   - `GET /api/ventas/{id}/` - Obtener una venta específica
   - `POST /api/ventas/{id}/cambiar_estado/` - Actualizar el estado de una venta

4. **Devoluciones** (`/api/devoluciones/`)
   - `GET /api/devoluciones/` - Listar todas las devoluciones
   - `POST /api/devoluciones/` - Crear una nueva devolución
   - `GET /api/devoluciones/{id}/` - Obtener una devolución específica

#### Funcionalidades Implementadas

1. **Serializers**
   - Validación de datos de entrada
   - Manejo de relaciones anidadas
   - Serializers específicos para creación y lectura

2. **ViewSets**
   - Control de acceso basado en roles
   - Manejo de transacciones distribuidas
   - Actualización automática de stock

3. **Integración con M-Inventario**
   - Verificación de stock antes de venta
   - Actualización atómica de stock
   - Manejo de errores en comunicación

### 1.6 Pruebas de Integración

Se ha implementado y verificado exitosamente la comunicación entre los microservicios a través de una prueba de venta completa:

#### Test Case: Proceso de Venta
```plaintext
=== Flujo de Venta ===
1. Verificación de Datos Maestros
   ✓ Cliente: Juan Pérez (creado/encontrado)
   ✓ Vendedor: vendedor1 (Rol: Vendedor)

2. Verificación de Inventario
   ✓ Producto: Laptop HP 15
   ✓ Stock Inicial: 50 unidades

3. Creación de Venta
   ✓ Venta registrada (#4)
   ✓ Detalle: 2 unidades a $2,499.99 c/u

4. Actualización de Inventario
   ✓ Stock reducido: -2 unidades
   ✓ Nuevo stock: 48 unidades
   ✓ Historial registrado con usuario

5. Actualización de Estado
   ✓ Estado final: "En Proceso"
```

#### Resultados de la Integración

1. **Comunicación entre Servicios**
   - Verificación exitosa de stock en M-Inventario
   - Actualización automática de inventario desde M-Ventas
   - Registro de movimientos con trazabilidad (id_usuario)

2. **Manejo de Transacciones**
   - Validación previa de stock suficiente
   - Actualización atómica de inventario
   - Registro sincronizado de venta y movimientos

3. **Estructura de Datos**
   - Relaciones mantenidas entre tablas
   - Integridad referencial preservada
   - Historial completo de operaciones

### 1.7 Próximos Pasos

1. Implementar autenticación entre servicios.
   - Nota: La variable `SECRET_KEY_MICRO` fue usada originalmente para autenticación entre servicios y ha sido eliminada. Recomendamos definir claves por servicio (`SECRET_INVENTARIO`, `SECRET_VENTAS`) o usar tokens HMAC/JWT.
   - Añadir middleware de autenticación
   - Configurar claves secretas en variables de entorno
   - Validar tokens en cada request

2. Configurar CORS y seguridad adicional
   - Habilitar CORS para el frontend
   - Implementar rate limiting
   - Configurar logs de seguridad

3. Implementar API Gateway
   - Configurar ruteo de requests
   - Implementar agregación de datos
   - Manejar autenticación centralizada