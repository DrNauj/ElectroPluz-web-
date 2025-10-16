from django.core.management.base import BaseCommand
from storefront.models import Category, Product
from django.db import transaction

class Command(BaseCommand):
    help = 'Corrige las categorías y limpia productos duplicados'

    CATEGORY_MAPPING = {
        'Electrodomésticos': ['electrodomesticos', 'smart-home'],
        'Computadoras': ['computadoras', 'laptops', 'tablets'],
        'Smartphones': ['smartphones', 'tablets'],
        'Audio y Video': ['audio-y-video', 'monitores'],
        'Gaming': ['gaming', 'componentes-pc'],
        'Accesorios': ['perifericos', 'almacenamiento', 'networking']
    }

    def handle(self, *args, **kwargs):
        self.stdout.write('Iniciando corrección de categorías...')

        with transaction.atomic():
            # Crear categorías principales si no existen
            for category_name in self.CATEGORY_MAPPING.keys():
                Category.objects.get_or_create(
                    name=category_name,
                    slug=category_name.lower().replace(' ', '-')
                )

            # Desactivar productos duplicados
            seen_names = {}
            for product in Product.objects.all():
                if product.name in seen_names:
                    # Si ya existe un producto con este nombre, mantener el más reciente
                    if product.created_at > seen_names[product.name].created_at:
                        seen_names[product.name].is_active = False
                        seen_names[product.name].save()
                        seen_names[product.name] = product
                    else:
                        product.is_active = False
                        product.save()
                else:
                    seen_names[product.name] = product

            # Limpiar categorías duplicadas
            for main_category in self.CATEGORY_MAPPING.keys():
                categories = Category.objects.filter(name=main_category)
                if categories.count() > 1:
                    # Mantener la categoría más antigua y fusionar los productos
                    main_cat = categories.order_by('id').first()
                    for other_cat in categories.exclude(id=main_cat.id):
                        Product.objects.filter(category=other_cat).update(category=main_cat)
                        other_cat.delete()
                    self.stdout.write(f'Fusionadas categorías duplicadas de {main_category}')

            # Agrupar productos en las categorías correctas
            for main_category, subcategories in self.CATEGORY_MAPPING.items():
                try:
                    category = Category.objects.get(name=main_category)
                    for product in Product.objects.filter(is_active=True):
                        # Asignar productos a la categoría correcta basado en su nombre y descripción
                        if any(subcategory in product.name.lower() or subcategory in product.description.lower() 
                              for subcategory in subcategories):
                            product.category = category
                            product.save()
                except Category.DoesNotExist:
                    self.stderr.write(f'No se encontró la categoría {main_category}')

            self.stdout.write(self.style.SUCCESS('Corrección completada con éxito'))
            
            # Mostrar resumen
            for category in Category.objects.all():
                product_count = Product.objects.filter(category=category, is_active=True).count()
                self.stdout.write(f'Categoría {category.name}: {product_count} productos activos')