from django.core.management.base import BaseCommand
from django.conf import settings
from storefront.models import Product, Category
from django.utils.text import slugify
from decimal import Decimal
import requests
import json
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Sincroniza productos y categorías desde la API de inventario'
    
    API_BASE_URL = 'http://localhost:8001/api'
    PRODUCTS_URL = f'{API_BASE_URL}/productos/'
    CATEGORIES_URL = f'{API_BASE_URL}/categorias/'

    def fetch_from_api(self, url):
        """Obtiene datos desde una URL de la API"""
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Error al obtener datos de {url}: {e}")
            self.stderr.write(f"Error de API: {e}")
            return None

    def sync_categories(self):
        """Sincroniza las categorías desde la API"""
        api_categories = self.fetch_from_api(self.CATEGORIES_URL)
        if api_categories is None:
            return False

        categories_synced = 0
        for api_cat in api_categories:
            try:
                category, created = Category.objects.update_or_create(
                    slug=api_cat.get('slug', slugify(api_cat['nombre'])),
                    defaults={
                        'name': api_cat['nombre'],
                        'description': api_cat.get('descripcion', '')
                    }
                )
                categories_synced += 1
                status = "Creada" if created else "Actualizada"
                self.stdout.write(f"{status} categoría: {category.name}")
            except Exception as e:
                logger.error(f"Error sincronizando categoría {api_cat.get('nombre', 'unknown')}: {e}")
                self.stderr.write(f"Error en categoría: {e}")

        return categories_synced > 0

    def fetch_products_from_api(self):
        """Obtiene los productos desde la API de inventario"""
        return self.fetch_from_api(self.PRODUCTS_URL)

    def sync_product(self, api_product):
        """Sincroniza un producto individual con la información de la API"""
        try:
            # Logging detallado del producto recibido
            self.stdout.write(f"\nProcesando producto: {api_product.get('nombre', 'unknown')}")
            self.stdout.write(f"Datos recibidos: {json.dumps(api_product, indent=2)}")

            # Obtener o crear la categoría
            category_id = api_product.get('categoria')
            if isinstance(category_id, (int, str)):
                try:
                    category = Category.objects.get(id=category_id)
                    self.stdout.write(f"Categoría encontrada: {category.name}")
                except Category.DoesNotExist:
                    self.stdout.write(f"Categoría {category_id} no encontrada, intentando obtener de la API...")
                    # Intentar obtener la categoría de la API
                    category_url = f"{self.CATEGORIES_URL}{category_id}/"
                    category_data = self.fetch_from_api(category_url)
                    if category_data:
                        category, created = Category.objects.get_or_create(
                            slug=category_data.get('slug', slugify(category_data['nombre'])),
                            defaults={
                                'name': category_data['nombre'],
                                'description': category_data.get('descripcion', '')
                            }
                        )
                        self.stdout.write(f"Categoría {'creada' if created else 'encontrada'}: {category.name}")
                    else:
                        category = None
                        self.stdout.write("No se pudo obtener la información de la categoría")
            else:
                category = None
                self.stdout.write("No se proporcionó ID de categoría válido")

            # Preparar datos del producto
            product_data = {
                'name': api_product['nombre'],
                'description': api_product['descripcion'],
                'price': Decimal(str(api_product['precio']).replace(',', '')),
                'stock': api_product['stock'],
                'is_active': api_product.get('activo', True),
                'image': api_product.get('imagen', ''),
                'category': category
            }

            # Manejar precio original
            if api_product.get('precio_original'):
                product_data['original_price'] = Decimal(str(api_product['precio_original']).replace(',', ''))
            else:
                product_data['original_price'] = None

            # Crear o actualizar el producto
            slug = api_product.get('slug', slugify(api_product['nombre']))
            product, created = Product.objects.update_or_create(
                slug=slug,
                defaults=product_data
            )

            self.stdout.write(f"Producto {'creado' if created else 'actualizado'}: {product.name}")
            self.stdout.write(f"Precio: {product.price}, Original: {product.original_price}")

            if not created:
                # Actualizar producto existente
                product.name = api_product['nombre']
                product.description = api_product['descripcion']
                product.price = Decimal(str(api_product['precio']))
                product.original_price = Decimal(str(api_product.get('precio_original', 0)))
                product.stock = api_product['stock']
                product.is_active = api_product['activo']
                product.image = api_product.get('imagen', '')
                product.save()

            return product, created
        except Exception as e:
            logger.error(f"Error al sincronizar producto {api_product.get('nombre', 'unknown')}: {e}")
            return None, False

    def handle(self, *args, **kwargs):
        """Maneja la sincronización de productos y categorías con la API"""
        self.stdout.write(self.style.SUCCESS("Iniciando sincronización con la API de inventario..."))
        
        # Sincronizar categorías primero
        self.stdout.write("\nSincronizando categorías...")
        if not self.sync_categories():
            self.stderr.write(self.style.ERROR('Error sincronizando categorías'))
            return

        # Obtener y sincronizar productos
        self.stdout.write("\nSincronizando productos...")
        api_products = self.fetch_products_from_api()
        if api_products is None:
            self.stderr.write(self.style.ERROR('No se pudieron obtener los productos de la API'))
            return

        # Contadores para el reporte
        created_count = 0
        updated_count = 0
        error_count = 0

        # Procesar cada producto de la API
        for api_product in api_products:
            try:
                product, created = self.sync_product(api_product)
                if product:
                    if created:
                        created_count += 1
                        self.stdout.write(f"Creado nuevo producto: {product.name}")
                    else:
                        updated_count += 1
                        self.stdout.write(f"Actualizado producto: {product.name}")
                else:
                    error_count += 1
            except Exception as e:
                error_count += 1
                self.stderr.write(f"Error procesando producto: {e}")

        # Desactivar productos que ya no existen en la API
        api_slugs = {p['slug'] for p in api_products}
        for product in Product.objects.all():
            if product.slug not in api_slugs:
                product.is_active = False
                product.save()
                self.stdout.write(f"Desactivado producto no existente en API: {product.name}")

        # Mostrar resumen
        self.stdout.write(self.style.SUCCESS(
            f'\nSincronización completada:\n'
            f'- Productos nuevos: {created_count}\n'
            f'- Productos actualizados: {updated_count}\n'
            f'- Errores: {error_count}'
        ))