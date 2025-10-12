import os
import django
from django.utils.text import slugify
from django.db import connection

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inventario_core.settings')
django.setup()

def generate_slugs():
    """Genera slugs para todos los productos que no tengan uno."""
    with connection.cursor() as cursor:
        # Primero agregar la columna si no existe
        try:
            cursor.execute("""
                ALTER TABLE `Productos` 
                ADD COLUMN `slug` varchar(150),
                ADD UNIQUE INDEX `idx_productos_slug` (`slug`);
            """)
            print("Columna slug agregada exitosamente")
        except Exception as e:
            if "Duplicate column name" not in str(e):
                raise
            print("La columna slug ya existe")

        # Obtener productos sin slug
        cursor.execute("SELECT id, nombre FROM Productos WHERE slug IS NULL OR slug = ''")
        productos = cursor.fetchall()
        print(f"Encontrados {len(productos)} productos sin slug")
        
        # Generar y actualizar slugs
        for id_producto, nombre in productos:
            base_slug = slugify(nombre)
            slug = base_slug
            counter = 1
            
            # Buscar un slug único
            while True:
                cursor.execute("SELECT COUNT(*) FROM Productos WHERE slug = %s", [slug])
                if cursor.fetchone()[0] == 0:
                    break
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            # Actualizar el producto con el slug único
            cursor.execute("UPDATE Productos SET slug = %s WHERE id = %s", [slug, id_producto])
            print(f"Generado slug '{slug}' para el producto '{nombre}'")

if __name__ == '__main__':
    generate_slugs()