import mysql.connector

config = {
    'user': 'root',
    'password': 'KcUGUxDNtKEiCrcWQiHfEsZDCeZetBFm',
    'host': 'interchange.proxy.rlwy.net',
    'port': '38168',
    'database': 'railway',
}

try:
    cnx = mysql.connector.connect(**config)
    cursor = cnx.cursor()

    print("Conexión exitosa a la base de datos!")
    
    # Probar consultas simples
    cursor.execute("SHOW TABLES")
    print("\nTablas en la base de datos:")
    for table in cursor:
        print(table[0])

    cursor.close()
    cnx.close()

except mysql.connector.Error as err:
    print(f"Error: {err}")