import os
import django
from django.utils.text import slugify
from django.db import connection

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inventario_core.settings')
django.setup()

from productos.models import Categoria, Producto, Proveedor

def check_table_contents(cursor, table_name):
    try:
        cursor.execute(f'SELECT COUNT(*) FROM `{table_name}`')
        count = cursor.fetchone()[0]
        print(f"Tabla {table_name}: {count} registros")
        
        if count > 0:
            cursor.execute(f'SELECT * FROM `{table_name}` LIMIT 3')
            rows = cursor.fetchall()
            print(f"Primeros 3 registros de {table_name}:")
            for row in rows:
                print(f"  {row}")
    except Exception as e:
        print(f"Info: {str(e)}")

def execute_sql_file(file_path, is_schema=False):
    print(f"Ejecutando archivo SQL: {file_path}")
    print(f"Tipo: {'Esquema' if is_schema else 'Datos'}")
    
    # Leer el contenido del archivo SQL
    with open(file_path, 'r', encoding='utf-8') as sql_file:
        sql_content = sql_file.read()
    
    # Agregar USE railway al principio si no está
    if not sql_content.lower().strip().startswith('use railway'):
        sql_content = 'USE railway;\n\n' + sql_content
    
    if not is_schema:
        # Solo reemplazar nombres de tabla si es archivo de datos
        tables = ['Categorias', 'Proveedores', 'Productos', 'Usuarios', 'Clientes']
        for table in tables:
            # Reemplazar sin backticks por versión con backticks
            sql_content = sql_content.replace(f'INSERT INTO {table}', f'INSERT INTO `{table}`')
            # También reemplazar versión en minúsculas por si acaso
            sql_content = sql_content.replace(f'INSERT INTO {table.lower()}', f'INSERT INTO `{table}`')
    
    # Procesar el contenido para remover comentarios y dividir en statements
    lines = []
    for line in sql_content.split('\n'):
        line = line.strip()
        if line and not line.startswith('--'):
            lines.append(line)
    
    # Unir las líneas y dividir por punto y coma
    sql_content_clean = '\n'.join(lines)
    sql_statements = []
    
    # Dividir por punto y coma y filtrar statements vacíos
    for stmt in sql_content_clean.split(';'):
        stmt = stmt.strip()
        if stmt:
            sql_statements.append(stmt)
    
    print(f"\nNúmero de statements SQL encontrados: {len(sql_statements)}")
    print("\nStatements a ejecutar:")
    for i, stmt in enumerate(sql_statements, 1):
        print(f"\n{i}. {stmt[:200]}...")
    
    # Ejecutar cada statement dentro de una transacción
    with connection.cursor() as cursor:
        try:
            # Iniciar transacción
            cursor.execute("START TRANSACTION")
            
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
            
            if not is_schema:
                try:
                    # Solo verificar tablas existentes para datos
                    cursor.execute("SHOW TABLES")
                    tables = cursor.fetchall()
                    existing_tables = {table[0].lower() for table in tables}
                    
                    print("\nTablas existentes:", existing_tables)
                    
                    if 'productos' in existing_tables:
                        print("\nLimpiando datos existentes antes de insertar nuevos...")
                        cursor.execute("TRUNCATE TABLE `Productos`")
                        cursor.execute("TRUNCATE TABLE `Categorias`")
                        cursor.execute("TRUNCATE TABLE `Proveedores`")
                        if 'usuarios' in existing_tables:
                            cursor.execute("TRUNCATE TABLE `Usuarios`")
                        if 'clientes' in existing_tables:
                            cursor.execute("TRUNCATE TABLE `Clientes`")
                except Exception as e:
                    print(f"Info: {str(e)} (ignorando si las tablas no existen)")
                    pass
            
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
            
            # Ahora ejecutar los statements
            for statement in sql_statements:
                try:
                    print(f"\nEjecutando SQL:\n{statement}")
                    
                    # Dividir statements que contienen múltiples VALUES
                    if 'INSERT INTO' in statement.upper() and 'VALUES' in statement.upper():
                        try:
                            cursor.execute(statement)
                            affected = cursor.rowcount
                            print(f"✓ Statement SQL ejecutado correctamente - {affected} filas afectadas")
                        except Exception as insert_error:
                            if 'You have an error in your SQL syntax' in str(insert_error):
                                # Intentar dividir en múltiples inserts
                                table = statement.split('INSERT INTO')[1].split('(')[0].strip()
                                columns = statement.split('(')[1].split(')')[0]
                                values_list = statement.split('VALUES')[1].strip()
                                values = [v.strip() for v in values_list.split('),(')]
                                
                                print(f"Dividiendo en {len(values)} inserts individuales...")
                                for value in values:
                                    value = value.strip('()')
                                    insert_stmt = f"INSERT INTO {table} ({columns}) VALUES ({value})"
                                    print(f"Ejecutando: {insert_stmt}")
                                    cursor.execute(insert_stmt)
                                    affected = cursor.rowcount
                                    print(f"✓ Insert individual ejecutado - {affected} filas afectadas")
                            else:
                                raise insert_error
                    else:
                        cursor.execute(statement)
                        if statement.lower().strip().startswith('select'):
                            results = cursor.fetchall()
                            print(f"Resultados: {results}")
                        else:
                            affected = cursor.rowcount
                            print(f"✓ Statement SQL ejecutado correctamente - {affected} filas afectadas")
                except Exception as e:
                    print(f"\n⚠ Error ejecutando SQL: {e}")
                    print(f"Statement problemático:\n{statement}")
                    raise e
            
            # Commit la transacción si todo fue exitoso
            cursor.execute("COMMIT")
            print("\n✓ Transacción completada exitosamente")
            
            if not is_schema:
                print("\nEstado final de las tablas:")
                for table in ['Categorias', 'Proveedores', 'Productos']:
                    check_table_contents(cursor, table)
            
        except Exception as e:
            # Rollback en caso de error
            cursor.execute("ROLLBACK")
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
            print(f"\n⚠ Error: se hizo rollback de la transacción - {str(e)}")
            raise e

def load_test_data():
    print("Cargando datos de prueba...")
    
    # Limpiar datos existentes
    print("Limpiando datos existentes...")
    with connection.cursor() as cursor:
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        cursor.execute("TRUNCATE TABLE Productos")
        cursor.execute("TRUNCATE TABLE Categorias")
        cursor.execute("TRUNCATE TABLE Proveedores")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")

    # Crear Categorías
    categorias_data = [
        ('Electrodomésticos', 'Aparatos eléctricos para el hogar'),
        ('Computadoras', 'Equipos de cómputo y accesorios'),
        ('Smartphones', 'Teléfonos móviles inteligentes'),
        ('Audio y Video', 'Equipos de entretenimiento'),
        ('Gaming', 'Consolas y videojuegos'),
    ]

    categorias = {}
    print("Creando categorías...")
    for nombre, descripcion in categorias_data:
        categoria = Categoria.objects.create(
            nombre=nombre,
            descripcion=descripcion,
            slug=slugify(nombre)
        )
        categorias[nombre] = categoria
        print(f"✓ Categoría creada: {nombre}")

    # Crear Proveedores
    proveedores_data = [
        ('TechCorp S.A.', 'Av. Principal 123', '987654321', 'ventas@techcorp.com'),
        ('ElectroImport', 'Calle Comercio 456', '987654322', 'pedidos@electroimport.com'),
        ('Digital Solutions', 'Jr. Tecnología 789', '987654323', 'info@digisolutions.com'),
        ('Gaming World', 'Av. Gamers 321', '987654324', 'compras@gamingworld.com'),
        ('SmartTech', 'Calle Smart 654', '987654325', 'contacto@smarttech.com')
    ]

    proveedores = {}
    print("\nCreando proveedores...")
    for nombre, direccion, telefono, email in proveedores_data:
        proveedor = Proveedor.objects.create(
            nombre=nombre,
            direccion=direccion,
            telefono=telefono,
            email=email
        )
        proveedores[nombre] = proveedor
        print(f"✓ Proveedor creado: {nombre}")

    # Crear Productos
    productos_data = [
        ('Laptop HP 15', 'Laptop HP 15.6" Core i5', 2499.99, 50, 'Computadoras', 'TechCorp S.A.'),
        ('Samsung Galaxy S21', 'Smartphone Samsung última generación', 3299.99, 30, 'Smartphones', 'SmartTech'),
        ('Smart TV LG 55"', 'Televisor LED Smart 4K', 2799.99, 25, 'Audio y Video', 'ElectroImport'),
        ('PlayStation 5', 'Consola de videojuegos', 2999.99, 20, 'Gaming', 'Gaming World'),
        ('Refrigeradora Samsung', 'Refrigeradora No Frost 500L', 3499.99, 15, 'Electrodomésticos', 'ElectroImport')
    ]

    print("\nCreando productos...")
    for nombre, descripcion, precio, stock, categoria_nombre, proveedor_nombre in productos_data:
        producto = Producto.objects.create(
            nombre=nombre,
            descripcion=descripcion,
            precio=precio,
            stock=stock,
            categoria=categorias[categoria_nombre],
            proveedor=proveedores[proveedor_nombre],
            slug=slugify(nombre)
        )
        print(f"✓ Producto creado: {nombre}")

    print("\n¡Datos de prueba cargados exitosamente!")

if __name__ == '__main__':
    try:
        # Primero ejecutar el archivo de esquema
        schema_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'sql', 'dabase.sql')
        if os.path.exists(schema_file_path):
            print("\n1. Creando esquema de la base de datos...")
            execute_sql_file(schema_file_path, is_schema=True)
        else:
            print("\n⚠ Advertencia: No se encontró el archivo de esquema (dabase.sql)")
            
        # Luego ejecutar el archivo de datos de prueba
        data_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'sql', 'test_data.sql')
        if os.path.exists(data_file_path):
            print("\n2. Cargando datos de prueba...")
            execute_sql_file(data_file_path, is_schema=False)
        else:
            print("\n⚠ Advertencia: No se encontró el archivo de datos (test_data.sql), usando método Django...")
            load_test_data()
        
        print("\n¡Proceso completado exitosamente!")
            
    except Exception as e:
        print(f"\n⚠ Error: {e}")
        import traceback
        traceback.print_exc()