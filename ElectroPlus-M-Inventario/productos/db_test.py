import os
import mysql.connector
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de la base de datos
db_config = {
    'host': os.getenv('MYSQL_HOST'),
    'user': os.getenv('MYSQL_USER'),
    'password': os.getenv('MYSQL_PASSWORD'),
    'database': os.getenv('MYSQL_DATABASE'),
    'port': os.getenv('MYSQL_PORT')
}

def execute_sql_file(filename):
    try:
        # Conectar a la base de datos
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        
        print(f"Conexión exitosa a {db_config['host']}!")
        
        # Leer y ejecutar el archivo SQL
        with open(filename, 'r', encoding='utf-8') as file:
            sql_commands = file.read().split(';')
            
            for command in sql_commands:
                if command.strip():
                    try:
                        cursor.execute(command)
                        print(f"Comando ejecutado exitosamente: {command[:50]}...")
                    except Exception as e:
                        print(f"Error ejecutando comando: {str(e)}")
                        print(f"Comando problemático: {command[:100]}")
        
        # Confirmar los cambios
        conn.commit()
        print("Todos los datos han sido insertados correctamente!")
        
    except Exception as e:
        print(f"Error de conexión: {str(e)}")
    
    finally:
        if 'conn' in locals():
            conn.close()
            print("Conexión cerrada.")

if __name__ == "__main__":
    # Ejecutar el archivo de datos de prueba
    sql_file = "D:/ElectroPluz(web)/sql/test_data.sql"
    execute_sql_file(sql_file)