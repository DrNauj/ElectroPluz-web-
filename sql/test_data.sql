-- Datos de prueba para las tablas principales

-- Insertar Categorías
INSERT INTO Categorias (nombre, descripcion) VALUES
('Electrodomésticos', 'Aparatos eléctricos para el hogar'),
('Computadoras', 'Equipos de cómputo y accesorios'),
('Smartphones', 'Teléfonos móviles inteligentes'),
('Audio y Video', 'Equipos de entretenimiento'),
('Gaming', 'Consolas y videojuegos');

-- Insertar Proveedores
INSERT INTO Proveedores (nombre, direccion, telefono, email) VALUES
('TechCorp S.A.', 'Av. Principal 123', '987654321', 'ventas@techcorp.com'),
('ElectroImport', 'Calle Comercio 456', '987654322', 'pedidos@electroimport.com'),
('Digital Solutions', 'Jr. Tecnología 789', '987654323', 'info@digisolutions.com'),
('Gaming World', 'Av. Gamers 321', '987654324', 'compras@gamingworld.com'),
('SmartTech', 'Calle Smart 654', '987654325', 'contacto@smarttech.com');

-- Insertar Productos
INSERT INTO Productos (nombre, descripcion, precio, stock, id_categoria, id_proveedor) VALUES
('Laptop HP 15', 'Laptop HP 15.6" Core i5', 2499.99, 50, 2, 1),
('Samsung Galaxy S21', 'Smartphone Samsung última generación', 3299.99, 30, 3, 5),
('Smart TV LG 55"', 'Televisor LED Smart 4K', 2799.99, 25, 4, 2),
('PlayStation 5', 'Consola de videojuegos', 2999.99, 20, 5, 4),
('Refrigeradora Samsung', 'Refrigeradora No Frost 500L', 3499.99, 15, 1, 2);

-- Insertar Usuarios
INSERT INTO Usuarios (nombre_usuario, contrasena, rol) VALUES
('admin', 'admin123', 'Administrador'),
('vendedor1', 'vend123', 'Vendedor'),
('almacen1', 'alm123', 'Almacén'),
('gerente1', 'ger123', 'Gerente');

-- Insertar Clientes
INSERT INTO Clientes (nombres, apellidos, email, telefono, direccion) VALUES
('Juan', 'Pérez', 'juan@email.com', '923456789', 'Av. Lima 123'),
('María', 'García', 'maria@email.com', '934567890', 'Jr. Arequipa 456'),
('Carlos', 'López', 'carlos@email.com', '945678901', 'Calle Tacna 789'),
('Ana', 'Martínez', 'ana@email.com', '956789012', 'Av. Cusco 321'),
('Pedro', 'Sánchez', 'pedro@email.com', '967890123', 'Jr. Puno 654');