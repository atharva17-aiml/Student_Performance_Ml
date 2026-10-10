import sqlite3
import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

SQLITE_DB = "users.db"

MYSQL_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASS", ""),
    "database": os.getenv("DB_NAME", "student_ml"),
}

print("Connecting to SQLite...")

sqlite_conn = sqlite3.connect(SQLITE_DB)
sqlite_cur = sqlite_conn.cursor()

sqlite_cur.execute("""
    SELECT id, username, password
    FROM users
""")

old_users = sqlite_cur.fetchall()

print(f"Found {len(old_users)} users in users.db")

sqlite_conn.close()

print("Connecting to MySQL...")

mysql_conn = mysql.connector.connect(**MYSQL_CONFIG)
mysql_cur = mysql_conn.cursor()

for old_id, username, password_hash in old_users:

    mysql_cur.execute(
        "SELECT id FROM users WHERE username = %s",
        (username,)
    )

    existing = mysql_cur.fetchone()

    if existing:
        print(f"SKIPPED: {username} already exists")
        continue

    role = "admin" if username.lower() == "admin" else "user"

    mysql_cur.execute("""
        INSERT INTO users
        (
            username,
            password,
            institute,
            roll_no,
            birth_date,
            role
        )
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (
        username,
        password_hash,
        None,
        None,
        None,
        role
    ))

    print(f"MIGRATED: {username} -> {role}")

mysql_conn.commit()

mysql_cur.close()
mysql_conn.close()

print()
print("================================")
print("USER MIGRATION COMPLETE")
print("================================")