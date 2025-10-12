import os
import django
from django.utils.text import slugify
from django.db import connection

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inventario_core.settings')
django.setup()

def generate_category_slugs():
    """Genera slugs para todas las categorías que no tengan uno."""
    with connection.cursor() as cursor:
        # Primero agregar la columna si no existe
        try:
            cursor.execute("""
                ALTER TABLE `Categorias` 
                ADD COLUMN `slug` varchar(50),
                ADD UNIQUE INDEX `idx_categorias_slug` (`slug`);
            """)
            print("Columna slug agregada exitosamente a Categorias")
        except Exception as e:
            if "Duplicate column name" not in str(e):
                raise
            print("La columna slug ya existe en Categorias")

        # Obtener categorías sin slug
        cursor.execute("SELECT id, nombre FROM Categorias WHERE slug IS NULL OR slug = ''")
        categorias = cursor.fetchall()
        print(f"Encontradas {len(categorias)} categorías sin slug")
        
        # Generar y actualizar slugs
        for id_categoria, nombre in categorias:
            base_slug = slugify(nombre)
            slug = base_slug
            counter = 1
            
            # Buscar un slug único
            while True:
                cursor.execute("SELECT COUNT(*) FROM Categorias WHERE slug = %s", [slug])
                if cursor.fetchone()[0] == 0:
                    break
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            # Actualizar la categoría con el slug único
            cursor.execute("UPDATE Categorias SET slug = %s WHERE id = %s", [slug, id_categoria])
            print(f"Generado slug '{slug}' para la categoría '{nombre}'")

if __name__ == '__main__':
    generate_category_slugs()