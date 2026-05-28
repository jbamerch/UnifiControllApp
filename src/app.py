from flask import Flask, render_template, request, jsonify
from pyunifi.controller import Controller
import os
import time
from db import init_db, get_db
from background import start_background_task

# Initialize DB and start background task



app = Flask(__name__)

# Configuration (ideally from environment variables)
UNIFI_HOST = os.environ.get('UNIFI_HOST', '192.168.1.1')
UNIFI_USER = os.environ.get('UNIFI_USER', 'admin')
UNIFI_PASS = os.environ.get('UNIFI_PASS', 'password')
UNIFI_VERSION = os.environ.get('UNIFI_VERSION', 'UDMP-unifiOS') # Assuming UDMP-unifiOS for UDM Pro
UNIFI_SITE = os.environ.get('UNIFI_SITE', 'default')
UNIFI_PORT = int(os.environ.get('UNIFI_PORT', '443'))

def get_unifi_controller():
    return Controller(
        UNIFI_HOST,
        UNIFI_USER,
        UNIFI_PASS,
        UNIFI_PORT,
        UNIFI_VERSION,
        site_id=UNIFI_SITE,
        ssl_verify=False
    )

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/clients')
def clients():
    try:
        c = get_unifi_controller()
        users_data = c.get_users()

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT mac, person_id, category, is_hidden, custom_name FROM devices")
        db_devices = {row['mac']: {'person_id': row['person_id'], 'category': row['category'], 'is_hidden': row['is_hidden'], 'custom_name': row['custom_name']} for row in cursor.fetchall()}

        cursor.execute("SELECT id, name FROM people")
        people = {row['id']: row['name'] for row in cursor.fetchall()}
        conn.close()

        for u in users_data:
            mac = u.get('mac')
            if mac in db_devices:
                u['category'] = db_devices[mac]['category']
                u['is_hidden'] = db_devices[mac]['is_hidden']
                u['custom_name'] = db_devices[mac]['custom_name']
                pid = db_devices[mac]['person_id']
                u['person_id'] = pid
                if pid and pid in people:
                    u['person_name'] = people[pid]
            else:
                u['is_hidden'] = 0
                u['custom_name'] = None

        return jsonify(users_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/client/<mac>/history')
def client_history(mac):
    try:
        endtime = int(time.time() * 1000)
        # 30 days
        starttime = endtime - (30 * 86400 * 1000)

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT time, rx_bytes, tx_bytes FROM usage_history WHERE mac = %s AND time >= %s ORDER BY time ASC", (mac, starttime))
        rows = cursor.fetchall()
        conn.close()

        history = []
        for r in rows:
            history.append({
                'time': r['time'],
                'rx_bytes': r['rx_bytes'],
                'tx_bytes': r['tx_bytes']
            })

        return jsonify(history)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/client/<mac>/block', methods=['POST'])
def block_client(mac):
    try:
        c = get_unifi_controller()
        c.block_client(mac)
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/client/<mac>/unblock', methods=['POST'])
def unblock_client(mac):
    try:
        c = get_unifi_controller()
        c.unblock_client(mac)
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/people', methods=['GET', 'POST'])
def manage_people():
    conn = get_db()
    cursor = conn.cursor()
    if request.method == 'POST':
        name = request.json.get('name')
        if name:
            try:
                cursor.execute("INSERT INTO people (name) VALUES (%s)", (name,))
                conn.commit()
            except:
                pass # Probably exists

    cursor.execute("SELECT id, name FROM people")
    people = [{'id': r['id'], 'name': r['name']} for r in cursor.fetchall()]
    conn.close()
    return jsonify(people)

@app.route('/api/device/<mac>/update', methods=['POST'])
def update_device(mac):
    data = request.json
    person_id = data.get('person_id')
    category = data.get('category')
    is_hidden = data.get('is_hidden')
    custom_name = data.get('custom_name')

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT IGNORE INTO devices (mac) VALUES (%s)", (mac,))

    if person_id is not None:
        if person_id == '':
            cursor.execute("UPDATE devices SET person_id = NULL WHERE mac = %s", (mac,))
        else:
            cursor.execute("UPDATE devices SET person_id = %s WHERE mac = %s", (person_id, mac))

    if category is not None:
        cursor.execute("UPDATE devices SET category = %s WHERE mac = %s", (category, mac))

    if is_hidden is not None:
        cursor.execute("UPDATE devices SET is_hidden = %s WHERE mac = %s", (is_hidden, mac))

    if custom_name is not None:
        if custom_name == '':
            cursor.execute("UPDATE devices SET custom_name = NULL WHERE mac = %s", (mac,))
        else:
            cursor.execute("UPDATE devices SET custom_name = %s WHERE mac = %s", (custom_name, mac))

    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})

@app.route('/api/person/<int:person_id>/<action>', methods=['POST'])
def block_person(person_id, action):
    if action not in ['block', 'unblock']:
        return jsonify({'error': 'Invalid action'}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT mac FROM devices WHERE person_id = %s", (person_id,))
    macs = [r['mac'] for r in cursor.fetchall()]
    conn.close()

    c = get_unifi_controller()
    for mac in macs:
        try:
            if action == 'block':
                c.block_client(mac)
            else:
                c.unblock_client(mac)
        except Exception as e:
            print(f"Error {action}ing {mac}: {e}")

    return jsonify({'status': 'success', 'affected': len(macs)})



if __name__ == '__main__':
    init_db()
    start_background_task()
    app.run(host='0.0.0.0', port=5000)
