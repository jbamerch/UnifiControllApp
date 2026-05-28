from flask import Flask, render_template, request, jsonify
from pyunifi.controller import Controller
import os
import time

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
        # get_users returns all known clients (online and offline)
        # stat/sta returns active clients.
        # We can fetch both and merge to know who is online,
        # or just use stat/sta if only active ones are needed. Let's use get_users for all.
        users_data = c.get_users()
        # Ensure we can return them nicely
        return jsonify(users_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/client/<mac>/history')
def client_history(mac):
    try:
        c = get_unifi_controller()
        endtime = time.time()
        # Get hourly data for the past 30 days
        params = {
            "attrs": ["bytes", "rx_bytes", "tx_bytes", "time"],
            "macs": [mac],
            "start": int(endtime - 30 * 86400) * 1000,
            "end": int(endtime) * 1000,
        }

        # Depending on pyunifi version, use the available method to POST
        try:
            if hasattr(c, '_api_write'):
                res = c._api_write("stat/report/hourly.user", params)
            else:
                # The reviewer's suggested format
                url = c.url + "api/s/" + c.site_id + "/stat/report/hourly.user"
                if "api/s/" in c.url:
                    url = c.url + "stat/report/hourly.user"
                elif c.url.endswith('/'):
                    url = c.url + "api/s/" + c.site_id + "/stat/report/hourly.user"
                res = c._write(url, params)
        except Exception as api_err:
            try:
                res = c._write(c.url + 'stat/report/hourly.user', params)
            except Exception as backup_err:
                raise Exception(f"Failed to fetch history: {api_err} | {backup_err}")

        return jsonify(res)
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
