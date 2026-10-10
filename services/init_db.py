import mysql.connector
import os
import logging
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)


def init_database():
    db = None

    try:
        # ---------------- CONNECT ----------------
        db = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASS"),
            database=os.getenv("DB_NAME"),
            charset="utf8mb4"
        )

        cur = db.cursor()

        # ---------------- USERS TABLE ----------------
        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(100) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            institute VARCHAR(255) NOT NULL,
            roll_no VARCHAR(100) NOT NULL,
            birth_date DATE NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB;
        """)

        # ---------------- PREDICTIONS TABLE ----------------
        cur.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            studytime INT NOT NULL,
            failures INT NOT NULL,
            absences INT NOT NULL,
            health INT NOT NULL,
            G1 INT NOT NULL,
            G2 INT NOT NULL,
            predicted_score FLOAT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

            CONSTRAINT fk_predictions_user
                FOREIGN KEY (user_id) REFERENCES users(id)
                ON DELETE CASCADE
        ) ENGINE=InnoDB;
        """)

        # ---------------- OTP TABLE ----------------
        cur.execute("""
        CREATE TABLE IF NOT EXISTS password_otp (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            email VARCHAR(255) NOT NULL,
            otp VARCHAR(10) NOT NULL,
            expires_at DATETIME NOT NULL,

            CONSTRAINT fk_otp_user
                FOREIGN KEY (user_id) REFERENCES users(id)
                ON DELETE CASCADE
        ) ENGINE=InnoDB;
        """)

        # ---------------- SAFE INDEX CREATION ----------------

        # users.username index
        cur.execute("""
        SELECT COUNT(1) FROM INFORMATION_SCHEMA.STATISTICS
        WHERE table_schema = DATABASE()
        AND table_name = 'users'
        AND index_name = 'idx_users_username'
        """)

        if cur.fetchone()[0] == 0:
            cur.execute("CREATE INDEX idx_users_username ON users(username)")

        # predictions.user_id index
        cur.execute("""
        SELECT COUNT(1) FROM INFORMATION_SCHEMA.STATISTICS
        WHERE table_schema = DATABASE()
        AND table_name = 'predictions'
        AND index_name = 'idx_predictions_user_id'
        """)

        if cur.fetchone()[0] == 0:
            cur.execute("CREATE INDEX idx_predictions_user_id ON predictions(user_id)")

        db.commit()

        logging.info("✅ MySQL tables created / updated successfully.")

    except mysql.connector.Error as e:
        logging.error(f"Database initialization failed: {e}")

    finally:
        if db and db.is_connected():
            db.close()


if __name__ == "__main__":
    init_database()