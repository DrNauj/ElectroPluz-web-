from types import SimpleNamespace

def get_mock_categories():
    return [
        SimpleNamespace(
            id=1,
            name='Laptops',
            slug='laptops',
            description='Computadoras portátiles de última generación'
        ),
        SimpleNamespace(
            id=2,
            name='Smartphones',
            slug='smartphones',
            description='Teléfonos inteligentes de las mejores marcas'
        ),
        SimpleNamespace(
            id=3,
            name='Accesorios',
            slug='accesorios',
            description='Complementos y accesorios para tus dispositivos'
        ),
        SimpleNamespace(
            id=4,
            name='Gaming',
            slug='gaming',
            description='Equipos y accesorios para gaming'
        ),
        SimpleNamespace(
            id=5,
            name='Componentes PC',
            slug='componentes-pc',
            description='Componentes para armar o mejorar tu PC'
        )
    ]

def get_mock_products():
    return [
        SimpleNamespace(
            id=1,
            name='Laptop ASUS ROG Strix G15',
            slug='asus-rog-strix-g15',
            category=SimpleNamespace(name='Laptops'),
            description='Laptop gaming con AMD Ryzen 9, RTX 3060, 16GB RAM, 512GB SSD',
            price=5999.99,
            stock=10,
            image='https://dlcdnwebimgs.asus.com/gain/28C10362-7188-44C4-A19E-97528F4E5794'
        ),
        SimpleNamespace(
            id=2,
            name='iPhone 15 Pro Max',
            slug='iphone-15-pro-max',
            category=SimpleNamespace(name='Smartphones'),
            description='El iPhone más potente con chip A17 Pro, cámara de 48MP, 256GB',
            price=4999.99,
            stock=15,
            image='https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/iphone-15-pro-max-black-titanium-select?wid=1200&hei=1200&fmt=jpeg&qlt=95'
        ),
        SimpleNamespace(
            id=3,
            name='Teclado Mecánico Logitech G Pro X',
            slug='logitech-g-pro-x',
            category=SimpleNamespace(name='Gaming'),
            description='Teclado mecánico gaming con switches GX Blue, RGB, formato TKL',
            price=599.99,
            stock=20,
            image='https://resource.logitechg.com/w_1000,c_limit,q_auto,f_auto,dpr_auto/d_transparent.gif/content/dam/gaming/en/products/pro-x-keyboard/pro-x-keyboard-gallery/deu-pro-x-keyboard-gallery-1.png'
        ),
        SimpleNamespace(
            id=4,
            name='Monitor Samsung Odyssey G7',
            slug='samsung-odyssey-g7',
            category=SimpleNamespace(name='Gaming'),
            description='Monitor gaming curvo 32", 240Hz, 1440p, HDR600, G-Sync',
            price=2499.99,
            stock=8,
            image='https://images.samsung.com/is/image/samsung/p6pim/latin/lc32g75tqslxzp/gallery/latin-odyssey-g7-lc32g75tqslxzp-front-black-thumbnail-536076123'
        ),
        SimpleNamespace(
            id=5,
            name='NVIDIA GeForce RTX 4070',
            slug='nvidia-rtx-4070',
            category=SimpleNamespace(name='Componentes PC'),
            description='Tarjeta gráfica gaming con 12GB GDDR6X, Ray Tracing',
            price=3299.99,
            stock=5,
            image='https://dlcdnwebimgs.asus.com/gain/F57C2227-7B50-4EF4-9E0A-4B75B4199F91/w1000'
        ),
        SimpleNamespace(
            id=6,
            name='AirPods Pro 2da Gen',
            slug='airpods-pro-2',
            category=SimpleNamespace(name='Accesorios'),
            description='Auriculares inalámbricos con cancelación de ruido activa',
            price=999.99,
            stock=25,
            image='https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/MQD83?wid=1144&hei=1144&fmt=jpeg&qlt=95'
        )
    ]