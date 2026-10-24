import getpass
import mysql.connector

password = getpass.getpass("MySQL root sifresi: ")

connection = mysql.connector.connect(
    host="localhost",
    port=3306,
    user="root",
    password=password,
    database="cardiorag",
)

cursor = connection.cursor()
cursor.execute("SHOW TABLES")

print("MySQL baglantisi basarili!")
for (table_name,) in cursor.fetchall():
    print("-", table_name)

cursor.close()
connection.close()