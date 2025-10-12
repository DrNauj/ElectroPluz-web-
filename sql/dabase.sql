-- Creación de la base de datos para ElectroPlus S.A.C.
USE railway;

-- -----------------------------------------------------
-- Tabla de Categorías de productos
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS Categorias (
  id INT NOT NULL AUTO_INCREMENT,
  nombre VARCHAR(45) NOT NULL,
  descripcion TEXT NULL,
  slug VARCHAR(150) NULL,
  PRIMARY KEY (id),
  UNIQUE INDEX idx_categorias_slug (slug)
);

-- -----------------------------------------------------
-- Tabla de Proveedores
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS Proveedores (
  id INT NOT NULL AUTO_INCREMENT,
  nombre VARCHAR(100) NOT NULL,
  direccion VARCHAR(255) NULL,
  telefono VARCHAR(20) NULL,
  email VARCHAR(100) NULL,
  PRIMARY KEY (id)
);

-- -----------------------------------------------------
-- Tabla de Productos
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS Productos (
  id INT NOT NULL AUTO_INCREMENT,
  nombre VARCHAR(100) NOT NULL,
  descripcion TEXT NULL,
  precio DECIMAL(10,2) NOT NULL,
  precio_original DECIMAL(10,2) NULL,
  descuento DECIMAL(5,2) NULL,
  stock INT NOT NULL,
  id_categoria INT NOT NULL,
  id_proveedor INT NOT NULL,
  slug VARCHAR(150) NULL,
  PRIMARY KEY (id),
  UNIQUE INDEX idx_productos_slug (slug),
  INDEX fk_producto_categoria_idx (id_categoria ASC),
  INDEX fk_producto_proveedor_idx (id_proveedor ASC),
  CONSTRAINT fk_producto_categoria
    FOREIGN KEY (id_categoria)
    REFERENCES Categorias (id)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT fk_producto_proveedor
    FOREIGN KEY (id_proveedor)
    REFERENCES Proveedores (id)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION
);

-- -----------------------------------------------------
-- Tabla de Clientes
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS Clientes (
  id INT NOT NULL AUTO_INCREMENT,
  nombres VARCHAR(100) NOT NULL,
  apellidos VARCHAR(100) NOT NULL,
  email VARCHAR(100) NOT NULL,
  telefono VARCHAR(20) NULL,
  direccion VARCHAR(255) NULL,
  PRIMARY KEY (id),
  UNIQUE INDEX email_UNIQUE (email ASC)
);

-- -----------------------------------------------------
-- Tabla de Usuarios (para gestión interna: Admin, Vendedor, Almacén, Gerente)
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS Usuarios (
  id INT NOT NULL AUTO_INCREMENT,
  nombre_usuario VARCHAR(50) NOT NULL,
  contrasena VARCHAR(255) NOT NULL,
  rol ENUM('Administrador', 'Vendedor', 'Almacén', 'Gerente') NOT NULL,
  PRIMARY KEY (id),
  UNIQUE INDEX nombre_usuario_UNIQUE (nombre_usuario ASC)
);

-- -----------------------------------------------------
-- Tabla de Ventas (o Pedidos)
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS Ventas (
  id INT NOT NULL AUTO_INCREMENT,
  fecha_venta DATETIME NOT NULL,
  total DECIMAL(10,2) NOT NULL,
  estado ENUM('Pendiente', 'En Proceso', 'Enviado', 'Entregado', 'Cancelado', 'Reembolsado') NOT NULL,
  id_cliente INT NOT NULL,
  id_usuario INT NOT NULL,
  PRIMARY KEY (id),
  INDEX fk_venta_cliente_idx (id_cliente ASC),
  INDEX fk_venta_usuario_idx (id_usuario ASC),
  CONSTRAINT fk_venta_cliente
    FOREIGN KEY (id_cliente)
    REFERENCES Clientes (id)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT fk_venta_usuario
    FOREIGN KEY (id_usuario)
    REFERENCES Usuarios (id)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION
);

-- -----------------------------------------------------
-- Tabla de Detalle de Ventas (para productos vendidos en cada venta)
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS DetalleVenta (
  id INT NOT NULL AUTO_INCREMENT,
  id_venta INT NOT NULL,
  id_producto INT NOT NULL,
  cantidad INT NOT NULL,
  precio_unitario DECIMAL(10,2) NOT NULL,
  PRIMARY KEY (id),
  INDEX fk_detalle_venta_venta_idx (id_venta ASC),
  INDEX fk_detalle_venta_producto_idx (id_producto ASC),
  CONSTRAINT fk_detalle_venta_venta
    FOREIGN KEY (id_venta)
    REFERENCES Ventas (id)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT fk_detalle_venta_producto
    FOREIGN KEY (id_producto)
    REFERENCES Productos (id)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION
);

-- -----------------------------------------------------
-- Tabla de HistorialCompras (para registrar las compras de cada cliente)
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS HistorialCompras (
  id INT NOT NULL AUTO_INCREMENT,
  id_cliente INT NOT NULL,
  id_venta INT NOT NULL,
  fecha_compra DATETIME NOT NULL,
  total DECIMAL(10,2) NOT NULL,
  PRIMARY KEY (id),
  INDEX fk_historial_cliente_idx (id_cliente ASC),
  INDEX fk_historial_venta_idx (id_venta ASC),
  CONSTRAINT fk_historial_cliente
    FOREIGN KEY (id_cliente)
    REFERENCES Clientes (id)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT fk_historial_venta
    FOREIGN KEY (id_venta)
    REFERENCES Ventas (id)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION
);

-- -----------------------------------------------------
-- Tabla de Devoluciones (para registrar productos devueltos)
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS Devoluciones (
  id INT NOT NULL AUTO_INCREMENT,
  id_venta INT NOT NULL,
  fecha_devolucion DATETIME NOT NULL,
  motivo TEXT NULL,
  PRIMARY KEY (id),
  INDEX fk_devolucion_venta_idx (id_venta ASC),
  CONSTRAINT fk_devolucion_venta
    FOREIGN KEY (id_venta)
    REFERENCES Ventas (id)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION
);

-- -----------------------------------------------------
-- Tabla de Detalle de Devoluciones (para registrar los productos específicos devueltos)
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS DetalleDevolucion (
  id INT NOT NULL AUTO_INCREMENT,
  id_devolucion INT NOT NULL,
  id_producto INT NOT NULL,
  cantidad_devuelta INT NOT NULL,
  PRIMARY KEY (id),
  INDEX fk_detalle_devolucion_devolucion_idx (id_devolucion ASC),
  INDEX fk_detalle_devolucion_producto_idx (id_producto ASC),
  CONSTRAINT fk_detalle_devolucion_devolucion
    FOREIGN KEY (id_devolucion)
    REFERENCES Devoluciones (id)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT fk_detalle_devolucion_producto
    FOREIGN KEY (id_producto)
    REFERENCES Productos (id)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION
);

-- -----------------------------------------------------
-- Tabla de Auditoría (para rastrear cambios importantes)
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS Auditoria (
  id INT NOT NULL AUTO_INCREMENT,
  tabla_afectada VARCHAR(50) NOT NULL,
  id_registro INT NOT NULL,
  tipo_accion ENUM('INSERT', 'UPDATE', 'DELETE') NOT NULL,
  fecha_accion DATETIME NOT NULL,
  id_usuario INT NOT NULL,
  detalles TEXT NULL,
  PRIMARY KEY (id),
  INDEX fk_auditoria_usuario_idx (id_usuario ASC),
  CONSTRAINT fk_auditoria_usuario
    FOREIGN KEY (id_usuario)
    REFERENCES Usuarios (id)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION
);

-- -----------------------------------------------------
-- Tabla de Cupones (para gestionar promociones y cupones de descuento)
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS Cupones (
  id INT NOT NULL AUTO_INCREMENT,
  codigo VARCHAR(20) NOT NULL UNIQUE,
  tipo_descuento ENUM('Porcentaje', 'Cantidad Fija') NOT NULL,
  valor DECIMAL(10,2) NOT NULL,
  fecha_inicio DATETIME NOT NULL,
  fecha_fin DATETIME NOT NULL,
  valido_para_producto_id INT NULL,
  PRIMARY KEY (id),
  INDEX fk_cupon_producto_idx (valido_para_producto_id ASC),
  CONSTRAINT fk_cupon_producto
    FOREIGN KEY (valido_para_producto_id)
    REFERENCES Productos (id)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION
);

-- -----------------------------------------------------
-- Tabla para registrar el uso de los cupones
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS UsoCupones (
  id INT NOT NULL AUTO_INCREMENT,
  id_cupon INT NOT NULL,
  id_venta INT NOT NULL,
  fecha_uso DATETIME NOT NULL,
  PRIMARY KEY (id),
  INDEX fk_usocupones_cupon_idx (id_cupon ASC),
  INDEX fk_usocupones_venta_idx (id_venta ASC),
  CONSTRAINT fk_usocupones_cupon
    FOREIGN KEY (id_cupon)
    REFERENCES Cupones (id)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT fk_usocupones_venta
    FOREIGN KEY (id_venta)
    REFERENCES Ventas (id)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION
);

-- -----------------------------------------------------
-- Tabla para reportes de ventas mensuales
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS ReporteMensualVentas (
  id INT NOT NULL AUTO_INCREMENT,
  anio INT NOT NULL,
  mes INT NOT NULL,
  total_ventas DECIMAL(12,2) NOT NULL,
  total_productos_vendidos INT NOT NULL,
  total_transacciones INT NOT NULL,
  PRIMARY KEY (id),
  UNIQUE INDEX anio_mes_UNIQUE (anio ASC, mes ASC)
);

-- -----------------------------------------------------
-- Tabla para reportes de productos más vendidos
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS ReporteMensualProductos (
  id INT NOT NULL AUTO_INCREMENT,
  anio INT NOT NULL,
  mes INT NOT NULL,
  id_producto INT NOT NULL,
  cantidad_vendida INT NOT NULL,
  PRIMARY KEY (id),
  INDEX fk_reporte_producto_idx (id_producto ASC),
  CONSTRAINT fk_reporte_producto
    FOREIGN KEY (id_producto)
    REFERENCES Productos (id)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION
);

-- -----------------------------------------------------
-- Tabla para un historial detallado de movimientos de inventario
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS HistorialInventario (
  id INT NOT NULL AUTO_INCREMENT,
  id_producto INT NOT NULL,
  tipo_movimiento ENUM('Entrada', 'Salida por Venta', 'Salida por Devolución', 'Ajuste') NOT NULL,
  cantidad INT NOT NULL,
  fecha DATETIME NOT NULL,
  id_usuario INT NOT NULL,
  PRIMARY KEY (id),
  INDEX fk_historial_inventario_producto_idx (id_producto ASC),
  INDEX fk_historial_inventario_usuario_idx (id_usuario ASC),
  CONSTRAINT fk_historial_inventario_producto
    FOREIGN KEY (id_producto)
    REFERENCES Productos (id)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT fk_historial_inventario_usuario
    FOREIGN KEY (id_usuario)
    REFERENCES Usuarios (id)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION
);

-- -----------------------------------------------------
-- Tabla para el seguimiento del estado de las ventas
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS SeguimientoVentas (
  id INT NOT NULL AUTO_INCREMENT,
  id_venta INT NOT NULL,
  estado_anterior VARCHAR(50) NULL,
  estado_nuevo VARCHAR(50) NOT NULL,
  fecha_cambio DATETIME NOT NULL,
  id_usuario INT NOT NULL,
  PRIMARY KEY (id),
  INDEX fk_seguimiento_venta_idx (id_venta ASC),
  INDEX fk_seguimiento_usuario_idx (id_usuario ASC),
  CONSTRAINT fk_seguimiento_venta
    FOREIGN KEY (id_venta)
    REFERENCES Ventas (id)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT fk_seguimiento_usuario
    FOREIGN KEY (id_usuario)
    REFERENCES Usuarios (id)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION
);

-- -----------------------------------------------------
-- Tabla para el envío de notificaciones
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS Notificaciones (
  id INT NOT NULL AUTO_INCREMENT,
  id_usuario INT NOT NULL,
  mensaje TEXT NOT NULL,
  fecha_creacion DATETIME NOT NULL,
  leido TINYINT(1) NOT NULL DEFAULT 0,
  PRIMARY KEY (id),
  INDEX fk_notificacion_usuario_idx (id_usuario ASC),
  CONSTRAINT fk_notificacion_usuario
    FOREIGN KEY (id_usuario)
    REFERENCES Usuarios (id)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION
);

-- -----------------------------------------------------
-- Tabla para las metas de ventas
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS MetasVentas (
  id INT NOT NULL AUTO_INCREMENT,
  id_usuario INT NOT NULL,
  anio INT NOT NULL,
  mes INT NOT NULL,
  monto_meta DECIMAL(10,2) NOT NULL,
  PRIMARY KEY (id),
  INDEX fk_metas_ventas_usuario_idx (id_usuario ASC),
  UNIQUE INDEX usuario_anio_mes_UNIQUE (id_usuario ASC, anio ASC, mes ASC),
  CONSTRAINT fk_metas_ventas_usuario
    FOREIGN KEY (id_usuario)
    REFERENCES Usuarios (id)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION
);
