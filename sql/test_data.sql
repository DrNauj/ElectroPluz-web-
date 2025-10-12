-- Datos de prueba para las tablas principales

-- Insertar Categorías
INSERT INTO Categorias (nombre, descripcion, slug) VALUES
('Electrodomésticos', 'Aparatos eléctricos para el hogar', 'electrodomesticos'),
('Computadoras', 'Equipos de cómputo y accesorios', 'computadoras'),
('Smartphones', 'Teléfonos móviles inteligentes', 'smartphones'),
('Audio y Video', 'Equipos de entretenimiento', 'audio-y-video'),
('Gaming', 'Consolas y videojuegos', 'gaming'),
('Laptops', 'Computadoras portátiles y accesorios', 'laptops'),
('Tablets', 'Tablets y accesorios', 'tablets'),
('Smart Home', 'Dispositivos para el hogar inteligente', 'smart-home'),
('Networking', 'Equipos de red y conectividad', 'networking'),
('Impresoras', 'Impresoras y suministros', 'impresoras'),
('Almacenamiento', 'Discos duros y unidades de almacenamiento', 'almacenamiento'),
('Periféricos', 'Teclados, mouse y otros periféricos', 'perifericos'),
('Monitores', 'Pantallas y monitores', 'monitores'),
('Cámaras', 'Cámaras digitales y accesorios', 'camaras'),
('Componentes PC', 'Componentes para computadoras', 'componentes-pc');

-- Insertar Proveedores
INSERT INTO Proveedores (nombre, direccion, telefono, email) VALUES
('TechCorp S.A.', 'Av. Principal 123', '987654321', 'ventas@techcorp.com'),
('ElectroImport', 'Calle Comercio 456', '987654322', 'pedidos@electroimport.com'),
('Digital Solutions', 'Jr. Tecnología 789', '987654323', 'info@digisolutions.com'),
('Gaming World', 'Av. Gamers 321', '987654324', 'compras@gamingworld.com'),
('SmartTech', 'Calle Smart 654', '987654325', 'contacto@smarttech.com'),
('PC Components', 'Av. Hardware 789', '987654326', 'ventas@pccomponents.com'),
('Mobile World', 'Jr. Smartphones 456', '987654327', 'info@mobileworld.com'),
('Network Plus', 'Calle Redes 123', '987654328', 'ventas@networkplus.com'),
('Gaming Pro', 'Av. ESports 456', '987654329', 'info@gamingpro.com'),
('Computer Land', 'Jr. Software 789', '987654330', 'ventas@computerland.com');

-- Insertar Productos
INSERT INTO Productos (nombre, descripcion, precio, stock, id_categoria, id_proveedor, slug) VALUES
-- Electrodomésticos
('Refrigeradora Samsung RT35', 'Refrigeradora No Frost de 450L', 2499.99, 10, 1, 1, 'refrigeradora-samsung-rt35'),
('Lavadora LG F1400', 'Lavadora automática de 14kg', 1899.99, 15, 1, 2, 'lavadora-lg-f1400'),
('Microondas Panasonic NN-ST', 'Microondas digital 1.2cu', 299.99, 20, 1, 3, 'microondas-panasonic-nn-st'),
('Cocina Indurama Valencia', 'Cocina 6 hornillas con horno', 899.99, 8, 1, 2, 'cocina-indurama-valencia'),

-- Computadoras
('PC Gamer RTX4080', 'PC Gaming de alto rendimiento', 4999.99, 5, 2, 1, 'pc-gamer-rtx4080'),
('iMac 24" M1', 'iMac con chip M1 y pantalla Retina', 3499.99, 7, 2, 3, 'imac-24-m1'),
('PC Oficina i5-12400', 'PC para trabajo y productividad', 1499.99, 12, 2, 6, 'pc-oficina-i5-12400'),
('Mini PC Intel NUC', 'Computadora compacta para oficina', 899.99, 15, 2, 6, 'mini-pc-intel-nuc'),

-- Smartphones
('iPhone 15 Pro Max', 'iPhone último modelo 256GB', 4999.99, 10, 3, 7, 'iphone-15-pro-max'),
('Samsung S23 Ultra', 'Galaxy S23 Ultra 512GB', 4499.99, 8, 3, 1, 'samsung-s23-ultra'),
('Xiaomi 13 Pro', 'Xiaomi flagship 256GB', 2999.99, 15, 3, 7, 'xiaomi-13-pro'),
('Google Pixel 8', 'Google Pixel 8 128GB', 2499.99, 10, 3, 7, 'google-pixel-8'),

-- Audio y Video
('Smart TV Samsung 65"', 'TV QLED 4K 65"', 2999.99, 8, 4, 1, 'smart-tv-samsung-65'),
('Soundbar Sony HT-A7000', 'Barra de sonido 7.1.2ch', 1499.99, 12, 4, 3, 'soundbar-sony-ht-a7000'),
('Proyector Epson EF-100', 'Proyector láser portátil', 1299.99, 6, 4, 2, 'proyector-epson-ef-100'),
('Home Theater LG LHB655', 'Sistema de teatro en casa 5.1', 899.99, 10, 4, 2, 'home-theater-lg-lhb655'),

-- Gaming
('PS5 Digital Edition', 'PlayStation 5 versión digital', 1999.99, 10, 5, 4, 'ps5-digital-edition'),
('Xbox Series X', 'Consola Xbox Series X 1TB', 1999.99, 8, 5, 4, 'xbox-series-x'),
('Nintendo Switch OLED', 'Nintendo Switch modelo OLED', 899.99, 15, 5, 9, 'nintendo-switch-oled'),
('Gaming Chair Pro', 'Silla gamer ergonómica', 399.99, 20, 5, 9, 'gaming-chair-pro'),

-- Laptops
('MacBook Pro 16"', 'MacBook Pro M2 Max 32GB', 5999.99, 5, 6, 3, 'macbook-pro-16'),
('Lenovo Legion Pro 7', 'Laptop gaming RTX 4090', 4999.99, 7, 6, 6, 'lenovo-legion-pro-7'),
('Dell XPS 15', 'Laptop premium para trabajo', 3999.99, 8, 6, 10, 'dell-xps-15'),
('ASUS ROG Zephyrus', 'Laptop gaming delgada', 3499.99, 10, 6, 6, 'asus-rog-zephyrus'),

-- Tablets
('iPad Pro 12.9"', 'iPad Pro M2 256GB', 2499.99, 10, 7, 3, 'ipad-pro-12-9'),
('Samsung Tab S9 Ultra', 'Tablet Android premium', 1999.99, 12, 7, 1, 'samsung-tab-s9-ultra'),
('Xiaomi Pad 6 Pro', 'Tablet Android económica', 699.99, 15, 7, 7, 'xiaomi-pad-6-pro'),

-- Smart Home
('Echo Show 15', 'Pantalla inteligente Alexa', 399.99, 20, 8, 5, 'echo-show-15'),
('Nest Hub Max', 'Pantalla inteligente Google', 379.99, 15, 8, 5, 'nest-hub-max'),
('Ring Doorbell Pro', 'Timbre inteligente con cámara', 299.99, 25, 8, 5, 'ring-doorbell-pro'),

-- Networking
('Router ASUS ROG Rapture', 'Router gaming WiFi 6E', 899.99, 8, 9, 8, 'router-asus-rog-rapture'),
('Switch TP-Link 24 puertos', 'Switch gigabit administrable', 399.99, 12, 9, 8, 'switch-tp-link-24p'),
('Ubiquiti UniFi AP', 'Access point empresarial', 299.99, 15, 9, 8, 'ubiquiti-unifi-ap'),

-- Impresoras
('Impresora HP LaserJet Pro', 'Impresora láser color', 799.99, 10, 10, 6, 'hp-laserjet-pro'),
('Epson EcoTank L8180', 'Impresora fotográfica', 1299.99, 8, 10, 2, 'epson-ecotank-l8180'),
('Brother DCP-T720DW', 'Impresora multifuncional', 499.99, 15, 10, 10, 'brother-dcp-t720dw'),

-- Almacenamiento
('SSD Samsung 990 Pro 2TB', 'SSD NVMe PCIe 4.0', 399.99, 20, 11, 1, 'ssd-samsung-990-pro'),
('WD Black 4TB', 'Disco duro gaming', 199.99, 25, 11, 6, 'wd-black-4tb'),
('Seagate IronWolf 8TB', 'Disco duro NAS', 299.99, 15, 11, 10, 'seagate-ironwolf-8tb'),

-- Periféricos
('Teclado Logitech G Pro X', 'Teclado mecánico gaming', 299.99, 20, 12, 9, 'teclado-logitech-g-pro-x'),
('Mouse Razer Viper V2', 'Mouse gaming inalámbrico', 199.99, 25, 12, 9, 'mouse-razer-viper-v2'),
('Webcam Logitech Brio', 'Webcam 4K HDR', 299.99, 15, 12, 6, 'webcam-logitech-brio'),

-- Monitores
('Monitor LG 27GP950', 'Monitor gaming 4K 144Hz', 1299.99, 8, 13, 2, 'monitor-lg-27gp950'),
('Samsung Odyssey G9', 'Monitor ultra-wide 49"', 1999.99, 5, 13, 1, 'samsung-odyssey-g9'),
('Dell U2723QE', 'Monitor 4K profesional', 999.99, 10, 13, 10, 'dell-u2723qe'),

-- Cámaras
('Sony A7 IV', 'Cámara mirrorless full-frame', 2999.99, 5, 14, 3, 'sony-a7-iv'),
('Canon R6 Mark II', 'Cámara mirrorless profesional', 2799.99, 6, 14, 2, 'canon-r6-mark-ii'),
('GoPro Hero 11 Black', 'Cámara de acción 5.3K', 499.99, 15, 14, 5, 'gopro-hero-11-black'),

-- Componentes PC
('CPU Ryzen 9 7950X', 'Procesador AMD tope de gama', 799.99, 10, 15, 6, 'cpu-ryzen-9-7950x'),
('GPU RTX 4090', 'Tarjeta gráfica gaming', 1999.99, 5, 15, 6, 'gpu-rtx-4090'),
('RAM DDR5 64GB', 'Memoria RAM gaming RGB', 399.99, 15, 15, 6, 'ram-ddr5-64gb'),
('Laptop HP 15', 'Laptop HP 15.6" Core i5', 2499.99, 50, 2, 1, 'laptop-hp-15'),
('Samsung Galaxy S21', 'Smartphone Samsung última generación', 3299.99, 30, 3, 5, 'samsung-galaxy-s21'),
('Smart TV LG 55"', 'Televisor LED Smart 4K', 2799.99, 25, 4, 2, 'smart-tv-lg-55'),
('PlayStation 5', 'Consola de videojuegos', 2999.99, 20, 5, 4, 'playstation-5'),
('Refrigeradora Samsung', 'Refrigeradora No Frost 500L', 3499.99, 15, 1, 2, 'refrigeradora-samsung');

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