from database import get_connection

conn = get_connection()
print("DB connected!")
conn.close()
