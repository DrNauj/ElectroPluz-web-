import sqlite3

conn = sqlite3.connect('ElectroPlus-Gateway-New/db.sqlite3')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print("Tablas en db.sqlite3:")
for table in tables:
    print(table[0])
conn.close()
