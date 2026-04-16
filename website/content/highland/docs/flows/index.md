---
title: "Node-RED Flows Guide"
description: "Flow import guide and tab-by-tab description"
---


## Overview

`flows-sanitized.json` contains the complete Node-RED control logic for the highland cloud forest terrarium, organized across 7 flow tabs. Credentials have been replaced with placeholders.

## Before Importing

### 1. Install Node-RED

```bash
bash <(curl -sL https://raw.githubusercontent.com/node-red/linux-installers/master/deb/update-nodejs-and-nodered)
sudo systemctl enable nodered
sudo systemctl start nodered
```

### 2. Install Required Node Packages

All packages must be installed in your Node-RED user directory (`~/.node-red/`):

```bash
cd ~/.node-red

npm install \
  node-red-contrib-bigtimer \
  node-red-node-openweathermap \
  node-red-contrib-influxdb \
  node-red-node-smooth \
  node-red-contrib-python-function-ps \
  node-red-contrib-dynamic-dimmer \
  node-red-contrib-sun-position \
  node-red-node-rbe \
  node-red-contrib-stoptimer-varidelay \
  node-red-contrib-aggregator \
  node-red-contrib-hysteresis \
  node-red-contrib-ui-led \
  node-red-contrib-ui-statetrail \
  node-red-dashboard \
  node-red-node-serialport
```

Note: `node-red-contrib-ioplugin` is no longer required (Firmata protocol was replaced by custom serial).

### 3. Install Python Dependencies

The Tapo smart plug control uses Python function nodes, and the Meross power monitoring daemon requires the `meross-iot` library:

```bash
pip3 install PyP100 meross-iot paho-mqtt
```

### 4. Install External Services

- **InfluxDB 1.8.x**: Time-series database for logging
- **MQTT broker** (e.g., Mosquitto): For sensor data ingestion
- **Grafana 10.x** (optional): For dashboards

```bash
sudo apt install influxdb mosquitto
influx -execute "CREATE DATABASE highland"
influx -execute "CREATE RETENTION POLICY standard_highland_retention ON highland DURATION 365d REPLICATION 1 DEFAULT"
```

## Importing the Flows

1. Open Node-RED in your browser: `http://<your-pi-ip>:1880`
2. Click the hamburger menu (☰) → **Import**
3. Select **Clipboard** tab
4. Click **select a file to import** and choose `flows-sanitized.json`
5. Select **Import to: new flow** (recommended) or **current flow**
6. Click **Import**
7. Click **Deploy** to activate

## Post-Import Configuration

### Credentials (REQUIRED)

Three Python function nodes contain `YOUR_EMAIL` and `YOUR_PASSWORD` placeholders. You must update these with your TP-Link Tapo account credentials:

1. **Lights tab** → Python function node (controls light plug)
2. **Humidity tab** → Python function node (controls mister plug)
3. **Temperature tab** → Python function node (controls compressor plug)

Double-click each node, find the `email` and `password` variables, and replace the placeholders. Also update the `ip` variable to match your Tapo plug IP addresses.

### Serial Port

The serial port node is configured for `/dev/ttyACM0` at 115200 baud with newline delimiter. Upload the `arduino-terrarium.ino` sketch to your Arduino Mega via `arduino-cli`:

```bash
arduino-cli compile --fqbn arduino:avr:mega ~/arduino-terrarium/
arduino-cli upload --fqbn arduino:avr:mega -p /dev/ttyACM0 ~/arduino-terrarium/
```

### InfluxDB Connection

The InfluxDB server node is configured for `localhost:8086`, database `highland`. If your InfluxDB is on a different host or uses a different database name, update the InfluxDB configuration node (visible in the config sidebar).

### MQTT Broker

The MQTT broker node is configured for `localhost:1883`. Update if your broker is elsewhere. Also verify the MQTT topic matches your ESP sensor's publish topic.

### OpenWeatherMap API

The weather nodes require a free OpenWeatherMap API key. Double-click any OpenWeatherMap node and enter your key in the configuration.

### Position Configuration

The `position-config` node uses:
- Latitude: 5.19485 (Venezuelan tepui reference for astronomical calculations)
- Longitude: 8.944381 (Genoa, Italy for local sunrise/sunset)

Adjust the longitude to your location if astronomical times should reflect your local conditions.

### Meross Power Monitoring (Optional)

Power monitoring uses a persistent daemon (`meross_daemon.py`) that maintains a single session to the Meross cloud API and publishes readings to MQTT every 2 seconds. This is far more efficient than the previous approach of spawning a new Python process every 120 seconds with a full login/logout cycle.

**Setup:**

1. Edit `scripts/meross_daemon.py` and set your credentials:
   - `EMAIL`: Your Meross account email
   - `PASSWORD`: Your Meross account password
   - `PLUG_NAME`: Your plug's name in the Meross app

2. Install and start the systemd service:
   ```bash
   sudo cp systemd/meross-daemon.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable --now meross-daemon
   ```

3. Verify it is publishing:
   ```bash
   mosquitto_sub -t meross/power/watts -C 3
   ```

Node-RED subscribes to `meross/power/watts` via an MQTT-in node on the Utilities tab. The daemon also accepts `on`/`off` commands on `meross/power/command`. If you don't have a Meross plug, disable the MQTT-in node (`meross_mqtt_in_001`) on the Utilities tab.

## Flow Tab Descriptions

### Tab 1: Lights
Controls the photoperiod schedule and LED dimming with sunrise/sunset and midday intensity variation.

**Key nodes**:
- **BigTimer**: Fixed schedule 06:25–20:05 (times in minutes-since-midnight: starttime=385, endtime=1205)
- **Dynamic Dimmer #1**: Dawn/dusk ramp (slider 0↔40, 40 steps × 45s = 30 min)
- **Dynamic Dimmer #2**: Midday ramp (slider 40↔60, 20 steps × 90s = 30 min)
- **Function nodes**: Dawn/Dusk/Midday start=0/start=1 nodes force explicit ramp direction
- **Startup brightness**: Detects mid-ramp restarts, issues partial start for on-schedule completion
- **Pin 8 writer**: Sends `P8,<value>` via serial; door safety gated (forces PWM 102 when doors open)
- **Python function**: Tapo P100 plug control with door safety gate

**Flow**: BigTimer triggers on/off → Tapo plug powers LEDs → Dimmer ramps PWM for sunrise/midday/sunset effect

### Tab 2: Humidity
Ingests sensor data, calculates VPD, manages mister.

**Key nodes**:
- **MQTT In**: Receives SHT35 temperature + humidity from ESP
- **VPD Calculator** (function): Computes Vapor Pressure Deficit using Magnus formula
- **Target humidity**: Derived from Colombian weather data (upper cap 95% RH)
- **Humidity difference**: target − actual, feeds PID controller on Fans tab
- **Hysteresis**: Controls mister on/off around target humidity
- **Python function**: Tapo P100 plug control for mister (with door safety gate)
- **Mist counter**: Tracks daily mist events with persistence across reboots

### Tab 3: Temperature
Manages compressor-based cooling.

**Key nodes**:
- **Target temperature**: Derived from Colombian weather data (clamped 12--24°C)
- **Temperature difference**: target − actual
- **Hysteresis**: Controls compressor on/off based on temperature error
- **Python function**: Tapo P100 plug control for compressor (with door safety gate)

### Tab 4: Fans
Core PID controller, door safety, and fan management.

**Key nodes**:
- **PID Controller** (function): Gain-scheduled humidity-based fan speed (Kp=50, Ki=0.5, Kd=10)
- **Day/Night Check**: Within-time-switch, 04:00–00:00 (midnight)
- **Night Mode (A/B Suspended)**: Always outputs 0. A/B code preserved in comments with reactivation instructions
- **Mister Interlock** (function): Stops all fans when mister is active (deletes topic to avoid RBE conflicts)
- **Manual Override**: Dashboard slider, bypasses all automatic control
- **Fan writers**: 4 serial output nodes — outlet (P45), impeller (P46), freezer (P44), circulation (P12), all door-safety gated
- **RBE nodes**: Report-by-exception logging for fan PWM changes
- **Door controller**: OR-tracks both doors, 3-second debounce
- **Door safety**: 4 outputs — fans off, compressor gate, mister gate, lights to 60%
- **Tapo gates**: Block inappropriate Tapo commands during door safety (compressor on, mister on, lights off)
- **High-humidity safety**: Forces outlet fan to 40 PWM when humidity > 90% and fans are 0

### Tab 5: Weather
Fetches and processes Colombian highland weather data.

**Key nodes**:
- **OpenWeatherMap** (×4): Chinchiná, Medellín, Bogotá, Sonsón
- **Aggregator/Smooth**: 30-minute InfluxDB window + 15-minute rolling mean (count=60 across 4 cities)
- **Position config**: Astronomical calculations for dawn/dusk reference
- **Weather fallback**: Historical 14-day daily curve (288 slots, two-pass smoothed) replaces flat defaults; ultimate fallback (day T=24/H=85, night T=14/H=90) if no historical data available
- **Historical curve builder**: Queries all 4 cities' InfluxDB data every 6 hours, builds smoothed diurnal profile with 15-hour time shift

The 15-hour time shift between Colombia (UTC−5) and Italy (UTC+1) means Colombian daytime weather maps to Italian nighttime conditions, producing natural diurnal variation.

### Tab 6: Charts
Node-RED Dashboard UI for local monitoring.

**Key nodes**:
- **Gauges**: Temperature, humidity, VPD
- **Charts**: Time-series with 3 series each — current (blue), target (red), room (green)
- **LEDs**: Status indicators for actuators
- **State trails**: Historical on/off visualization
- **Room data inject**: 60s repeat, pushes room sensor data to charts
- **Chart persistence**: Save/restore via flow context for data survival across restarts

Access at: `http://<your-pi-ip>:1880/ui`

### Tab 7: Utilities
Data logging, serial communication, power monitoring, and system diagnostics.

**Key nodes**:
- **Serial config**: 115200 baud, newline delimiter, `/dev/ttyACM0`
- **Serial parser**: Routes incoming serial data — heartbeat (→ arduino_status), doors (→ door controller)
- **Data Logger** (function): 14 outputs, reads global context every 60 seconds
- **InfluxDB out** (×14+): One per measurement, writing to `highland` database
- **Meross power monitoring**: MQTT subscription (`meross/power/watts`) from persistent daemon → parse → UI text + InfluxDB (2s updates)
- **Mist counter persistence**: Startup inject → restore function → UI text nodes
- **Resend PWM**: Periodic re-send of current fan states to prevent stale serial
- **Send to All Fans**: Manual 4-output node for debugging (outlet, impeller, freezer, circulation)

## Troubleshooting

**Nodes show "missing type"**: Install the required npm package for that node type (see installation section).

**InfluxDB write errors**: Verify InfluxDB is running (`systemctl status influxdb`) and the `highland` database exists.

**Arduino not connecting**: Check `/dev/ttyACM0` exists, the `arduino-terrarium.ino` sketch is uploaded, and no other process holds the serial port. Never open `/dev/ttyACM0` manually while Node-RED is running.

**Weather nodes show errors**: Verify your OpenWeatherMap API key is configured and the free tier hasn't been rate-limited.

**Tapo plug control fails**: Ensure `PyP100` is installed, credentials are correct, and the plug IPs are reachable from the Pi.

**Door safety won't deactivate**: Check both reed switches — `door_safety_active` stays true until both D22 and D24 read HIGH (closed). The debounce requires doors to be stably closed.

**Fans stuck at 0 after misting**: This was a known RBE topic bug, now fixed. Ensure the "Stop All Fans" function deletes `msg.topic` rather than setting it to `"mister_override"`.
