import os
import django
import MySQLdb
from dotenv import load_dotenv

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ventas_core.settings')
django.setup()

load_dotenv()

def ejecutar_sql_desde_archivo(archivo):
    """
    Ejecuta un archivo SQL en la base de datos.
    """
    try:
        db = MySQLdb.connect(
            host=os.getenv('MYSQL_HOST', 'localhost'),
            user=os.getenv('MYSQL_USER', 'root'),
            passwd=os.getenv('MYSQL_PASSWORD', ''),
            db=os.getenv('MYSQL_DATABASE', 'railway'),
            port=int(os.getenv('MYSQL_PORT', 3306))
        )
        cursor = db.cursor()
        
        print(f"Ejecutando {archivo}...")
        with open(archivo, 'r', encoding='utf-8') as f:
            sql = f.read()
            statements = sql.split(';')
            for stmt in statements:
                if stmt.strip():
                    try:
                        cursor.execute(stmt)
                        print("Statement ejecutado correctamente")
                    except Exception as e:
                        print(f"Error en statement: {e}")
        
        db.commit()
        print(f"Archivo {archivo} ejecutado exitosamente")
        
    except Exception as e:
        print(f"Error al ejecutar {archivo}: {str(e)}")
    finally:
        if 'db' in locals():
            db.close()

# Primero importamos los modelos que necesitamos
from ventas.models import Cliente, Usuario

# Insertar Usuarios
usuarios = [
    {'nombre_usuario': 'admin', 'contrasena': 'admin123', 'rol': 'Administrador'},
    {'nombre_usuario': 'vendedor1', 'contrasena': 'vend123', 'rol': 'Vendedor'},
    {'nombre_usuario': 'almacen1', 'contrasena': 'alm123', 'rol': 'Almacén'},
    {'nombre_usuario': 'gerente1', 'contrasena': 'ger123', 'rol': 'Gerente'}
]

for user_data in usuarios:
    Usuario.objects.get_or_create(**user_data)

# Insertar Clientes
clientes = [
    {
        'nombres': 'Juan',
        'apellidos': 'Pérez',
        'email': 'juan@email.com',
        'telefono': '923456789',
        'direccion': 'Av. Lima 123'
    },
    {
        'nombres': 'María',
        'apellidos': 'García',
        'email': 'maria@email.com',
        'telefono': '934567890',
        'direccion': 'Jr. Arequipa 456'
    },
    {
        'nombres': 'Carlos',
        'apellidos': 'López',
        'email': 'carlos@email.com',
        'telefono': '945678901',
        'direccion': 'Calle Tacna 789'
    },
    {
        'nombres': 'Ana',
        'apellidos': 'Martínez',
        'email': 'ana@email.com',
        'telefono': '956789012',
        'direccion': 'Av. Cusco 321'
    },
    {
        'nombres': 'Pedro',
        'apellidos': 'Sánchez',
        'email': 'pedro@email.com',
        'telefono': '967890123',
        'direccion': 'Jr. Puno 654'
    }
]

for client_data in clientes:
    Cliente.objects.get_or_create(**client_data)

# Cargar datos SQL completos
print("\nCargando estructura de la base de datos...")
ejecutar_sql_desde_archivo('../sql/dabase.sql')

print("\nCargando datos de prueba...")
ejecutar_sql_desde_archivo('../sql/test_data.sql')

print("\nVerificando los datos cargados...")
print(f"Usuarios: {Usuario.objects.count()}")
print(f"Clientes: {Cliente.objects.count()}")

print("\nDatos cargados exitosamente en el servicio de Ventas")