import time
import threading

from db import get_db

def poll_unifi():
    from app import _cached_users, _last_fetch, get_unifi_controller
    import app

    while True:
        try:
            c = get_unifi_controller()
            try:
                users = c.get_users()
            except Exception as e:
                # Token expired?
                app._controller = None
                c = get_unifi_controller()
                users = c.get_users()

            app._cached_users = users
            app._last_fetch = time.time()

            now = int(time.time() * 1000)

            conn = get_db()
            cursor = conn.cursor()


            for u in users:
                mac = u.get('mac')
                rx = u.get('rx_bytes', 0)
                tx = u.get('tx_bytes', 0)

                # Make sure device exists in devices table
                cursor.execute('INSERT IGNORE INTO devices (mac) VALUES (%s)', (mac,))

                cursor.execute('INSERT INTO usage_history (mac, time, rx_bytes, tx_bytes) VALUES (%s, %s, %s, %s)',
                               (mac, now, rx, tx))

            conn.commit()
            conn.close()

        except Exception as e:
            print("Background poll error:", e)

        # Poll every 5 minutes
        time.sleep(300)

def start_background_task():
    t = threading.Thread(target=poll_unifi, daemon=True)
    t.start()
