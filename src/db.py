import sqlite3
import os

DB_PATH = os.environ.get('DB_PATH', 'data.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    # People
    c.execute('''CREATE TABLE IF NOT EXISTS people (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    )''')

    # Device metadata
    c.execute('''CREATE TABLE IF NOT EXISTS devices (
        mac TEXT PRIMARY KEY,
        person_id INTEGER,
        category TEXT,
        FOREIGN KEY(person_id) REFERENCES people(id)
    )''')

    # Device usage history
    c.execute('''CREATE TABLE IF NOT EXISTS usage_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mac TEXT,
        time INTEGER,
        rx_bytes INTEGER,
        tx_bytes INTEGER,
        FOREIGN KEY(mac) REFERENCES devices(mac)
    )''')

    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
