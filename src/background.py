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
                active_clients = c.get_clients()
            except Exception as e:
                # Token expired?
                app._controller = None
                c = get_unifi_controller()
                users = c.get_users()
                active_clients = c.get_clients()

            app._cached_users = users
            app._last_fetch = time.time()

            now = int(time.time() * 1000)

            conn = get_db()
            cursor = conn.cursor()

            # Map active clients for easy byte lookup
            active_map = {c.get('mac'): c for c in active_clients}

            for u in users:
                mac = u.get('mac')

                # Active clients have accurate session rx/tx bytes
                if mac in active_map:
                    rx = active_map[mac].get('rx_bytes', 0)
                    tx = active_map[mac].get('tx_bytes', 0)
                else:
                    # If offline, use historical or 0.
                    # Since we only diff between data points, if they are offline,
                    # we should probably just fetch the last known bytes from our DB and duplicate it
                    # so the diff is 0.
                    cursor.execute("SELECT rx_bytes, tx_bytes FROM usage_history WHERE mac = %s ORDER BY time DESC LIMIT 1", (mac,))
                    last_record = cursor.fetchone()
                    if last_record:
                        rx = last_record['rx_bytes']
                        tx = last_record['tx_bytes']
                    else:
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
