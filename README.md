# Unifi UDM Pro Client Manager

A web application to view and manage clients connected to a Unifi UDM Pro.

## Features
* List all connected and known devices.
* Pause/Unpause data (Block/Unblock) for individual devices.
* View data usage history (Download/Upload) over various timeframes (6h, 12h, 3d, 1w, 1m).

## Environment Variables

Configure the application by setting the following environment variables:

* `UNIFI_HOST`: IP address or hostname of the UDM Pro (default: 192.168.1.1)
* `UNIFI_USER`: Username with administrative access
* `UNIFI_PASS`: Password for the user
* `UNIFI_VERSION`: Unifi Controller version string (default: UDMP-unifiOS for UDM Pro)
* `UNIFI_SITE`: Unifi site ID (default: default)
* `UNIFI_PORT`: Unifi Controller port (default: 443)

## Running Locally

1. Install dependencies:
   ```bash
   pip install flask pyunifi
   ```
2. Set environment variables.
3. Run the app:
   ```bash
   python src/app.py
   ```

## Docker

A Dockerfile is provided for easy deployment.

```bash
docker build -t unifi-manager .
docker run -p 5000:5000 -e UNIFI_HOST='192.168.1.1' -e UNIFI_USER='admin' -e UNIFI_PASS='password' unifi-manager
```
