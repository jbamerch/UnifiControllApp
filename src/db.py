import pymysql
import os
import time

DB_HOST = os.environ.get('DB_HOST', '127.0.0.1')
DB_PORT = int(os.environ.get('DB_PORT', '3306'))
DB_USER = os.environ.get('DB_USER', 'unifi_user')
DB_PASS = os.environ.get('DB_PASS', 'unifi_pass')
DB_NAME = os.environ.get('DB_NAME', 'unifi_manager')

def get_db():
    return pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME,
        cursorclass=pymysql.cursors.DictCursor
    )

def init_db():
    # Wait for MySQL to be ready
    for _ in range(30):
        try:
            conn = pymysql.connect(
                host=DB_HOST,
                port=DB_PORT,
                user=DB_USER,
                password=DB_PASS
            )
            c = conn.cursor()
            c.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
            conn.commit()
            conn.close()
            break
        except Exception as e:
            time.sleep(2)

    conn = get_db()
    c = conn.cursor()

    # People
    c.execute('''CREATE TABLE IF NOT EXISTS people (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255) UNIQUE NOT NULL
    )''')

    # Device metadata
    c.execute('''CREATE TABLE IF NOT EXISTS devices (
        mac VARCHAR(17) PRIMARY KEY,
        person_id INT,
        category VARCHAR(50),
        FOREIGN KEY(person_id) REFERENCES people(id)
    )''')

    # Device usage history
    c.execute('''CREATE TABLE IF NOT EXISTS usage_history (
        id INT AUTO_INCREMENT PRIMARY KEY,
        mac VARCHAR(17),
        time BIGINT,
        rx_bytes BIGINT,
        tx_bytes BIGINT,
        FOREIGN KEY(mac) REFERENCES devices(mac)
    )''')

    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
