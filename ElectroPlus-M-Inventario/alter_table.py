import os
import django
from django.db import connection

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inventario_core.settings')
django.setup()

def alter_table():
    with connection.cursor() as cursor:
        # Desactivar restricciones de clave foránea
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        
        # Ejecutar ALTER TABLE
        alter_sql = """
        ALTER TABLE Productos
        ADD COLUMN precio_original DECIMAL(10,2) NULL,
        ADD COLUMN descuento DECIMAL(5,2) NULL;
        """
        cursor.execute(alter_sql)
        
        # Reactivar restricciones de clave foránea
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        
        # Verificar la estructura de la tabla
        cursor.execute("DESCRIBE Productos")
        structure = cursor.fetchall()
        print("\nEstructura de la tabla Productos:")
        for column in structure:
            print(column)

if __name__ == '__main__':
    try:
        print("Ejecutando ALTER TABLE...")
        alter_table()
        print("\n✓ ALTER TABLE ejecutado exitosamente")
    except Exception as e:
        print(f"\n⚠ Error: {str(e)}")