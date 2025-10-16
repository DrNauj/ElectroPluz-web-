from django.core.management.base import BaseCommand
from django.utils.text import slugify
from storefront.models import Category, Product
from dashboard.models import Branch, Inventory
from django.db import transaction

class Command(BaseCommand):
    help = 'Crea datos de prueba para la tienda'

    def handle(self, *args, **kwargs):
        # Categorías
        categories = [
            {
                'name': 'Laptops',
                'description': 'Computadoras portátiles para todo uso'
            },
            {
                'name': 'Smartphones',
                'description': 'Teléfonos inteligentes de última generación'
            },
            {
                'name': 'Tablets',
                'description': 'Tablets y dispositivos 2 en 1'
            },
            {
                'name': 'Accesorios',
                'description': 'Accesorios para dispositivos electrónicos'
            }
        ]

        # Productos por categoría
        products = {
            'Laptops': [
                {
                    'name': 'Laptop Pro X1',
                    'description': 'Laptop profesional con Intel i7, 16GB RAM, 512GB SSD',
                    'price': 1299.99,
                    'stock': 50
                },
                {
                    'name': 'Laptop Gaming Y2',
                    'description': 'Laptop gaming con RTX 3060, AMD Ryzen 7, 32GB RAM',
                    'price': 1599.99,
                    'stock': 30
                }
            ],
            'Smartphones': [
                {
                    'name': 'SmartPhone Elite',
                    'description': 'Smartphone de gama alta con cámara 108MP',
                    'price': 899.99,
                    'stock': 100
                },
                {
                    'name': 'SmartPhone Lite',
                    'description': 'Smartphone económico con gran batería',
                    'price': 299.99,
                    'stock': 150
                }
            ],
            'Tablets': [
                {
                    'name': 'Tablet Pro 12',
                    'description': 'Tablet de 12 pulgadas con stylus incluido',
                    'price': 699.99,
                    'stock': 40
                },
                {
                    'name': 'Tablet Mini',
                    'description': 'Tablet compacta de 8 pulgadas',
                    'price': 299.99,
                    'stock': 60
                }
            ],
            'Accesorios': [
                {
                    'name': 'Auriculares Wireless Pro',
                    'description': 'Auriculares inalámbricos con cancelación de ruido',
                    'price': 199.99,
                    'stock': 200
                },
                {
                    'name': 'Mouse Gaming RGB',
                    'description': 'Mouse gaming con 16000 DPI y RGB',
                    'price': 79.99,
                    'stock': 150
                }
            ]
        }

        # Sucursales
        branches = [
            {
                'name': 'Tienda Central',
                'address': 'Av. Principal 123',
                'phone': '(01) 234-5678'
            },
            {
                'name': 'Sucursal Norte',
                'address': 'Calle Norte 456',
                'phone': '(01) 987-6543'
            }
        ]

        with transaction.atomic():
            # Crear categorías
            created_categories = {}
            for cat_data in categories:
                category, created = Category.objects.get_or_create(
                    name=cat_data['name'],
                    defaults={
                        'slug': slugify(cat_data['name']),
                        'description': cat_data['description']
                    }
                )
                created_categories[cat_data['name']] = category
                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f'Categoría "{cat_data["name"]}" creada')
                    )

            # Crear productos
            created_products = []
            for cat_name, prods in products.items():
                category = created_categories[cat_name]
                for prod_data in prods:
                    product, created = Product.objects.get_or_create(
                        name=prod_data['name'],
                        defaults={
                            'slug': slugify(prod_data['name']),
                            'category': category,
                            'description': prod_data['description'],
                            'price': prod_data['price'],
                            'stock': prod_data['stock']
                        }
                    )
                    created_products.append(product)
                    if created:
                        self.stdout.write(
                            self.style.SUCCESS(f'Producto "{prod_data["name"]}" creado')
                        )

            # Crear sucursales
            created_branches = []
            for branch_data in branches:
                branch, created = Branch.objects.get_or_create(
                    name=branch_data['name'],
                    defaults={
                        'address': branch_data['address'],
                        'phone': branch_data['phone']
                    }
                )
                created_branches.append(branch)
                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f'Sucursal "{branch_data["name"]}" creada')
                    )

            # Crear inventario
            for product in created_products:
                for branch in created_branches:
                    inventory, created = Inventory.objects.get_or_create(
                        product=product,
                        branch=branch,
                        defaults={
                            'quantity': product.stock // len(created_branches),
                            'min_stock': 5
                        }
                    )
                    if created:
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'Inventario creado para {product.name} en {branch.name}'
                            )
                        )