# Node-RED Flows — Import Guide

## Overview

`flows-sanitized.json` contains the complete Node-RED control logic for the highland cloud forest terrarium, organized across 7 flow tabs with 393 nodes. Credentials have been replaced with placeholders.

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
  node-red-contrib-ioplugin \
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
  node-red-dashboard
```

### 3. Install Python Dependencies

The Tapo smart plug control uses Python function nodes:

```bash
pip3 install PyP100
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
3. **Temperature tab** → Python function node (controls freezer plug)

Double-click each node, find the `email` and `password` variables, and replace the placeholders. Also update the `ip` variable to match your Tapo plug IP addresses.

### InfluxDB Connection

The InfluxDB server node is configured for `localhost:8086`, database `highland`. If your InfluxDB is on a different host or uses a different database name, update the InfluxDB configuration node (visible in the config sidebar).

### MQTT Broker

The MQTT broker node is configured for `localhost:1883`. Update if your broker is elsewhere. Also verify the MQTT topic matches your ESP sensor's publish topic.

### Arduino/Firmata

The ioplugin node expects an Arduino Mega on `/dev/ttyACM0` running StandardFirmata. Upload the StandardFirmata sketch to your Arduino via the Arduino IDE before deploying.

### OpenWeatherMap API

The weather nodes require a free OpenWeatherMap API key. Double-click any OpenWeatherMap node and enter your key in the configuration.

### Position Configuration

The `position-config` node uses:
- Latitude: 5.19485 (Venezuelan tepui reference for astronomical calculations)
- Longitude: 8.944381 (Genoa, Italy for local sunrise/sunset)

Adjust the longitude to your location if astronomical times should reflect your local conditions.

## Flow Tab Descriptions

### Tab 1: Lights
Controls the photoperiod schedule and LED dimming.

**Key nodes**:
- **BigTimer**: Fixed schedule 06:25–20:05 (times in minutes-since-midnight: starttime=385, endtime=1205)
- **Dynamic Dimmer**: 30-minute sunrise ramp starting 06:30, 30-minute sunset ramp starting 19:30
- **Python function**: Tapo P100 plug control for light power
- **GPIO out (pin 8)**: PWM dimmer signal to Arduino

**Flow**: BigTimer triggers on/off → Tapo plug powers LEDs → Dimmer ramps PWM for sunrise/sunset effect

### Tab 2: Humidity
Ingests sensor data, calculates VPD, manages mister.

**Key nodes**:
- **MQTT In**: Receives SHT35 temperature + humidity from ESP
- **VPD Calculator** (function): Computes Vapor Pressure Deficit using Magnus formula
- **Target humidity**: Derived from Colombian weather data, clamped to 70–90% RH
- **Humidity difference**: target − actual, feeds PID controller on Fans tab
- **Hysteresis**: Controls mister on/off around target humidity
- **Python function**: Tapo P100 plug control for mister

### Tab 3: Temperature
Manages freezer-based cooling.

**Key nodes**:
- **Target temperature**: Derived from Colombian weather data, clamped to 12–24°C
- **Temperature difference**: target − actual
- **Hysteresis**: Controls freezer on/off based on temperature error
- **Python function**: Tapo P100 plug control for freezer
- **GPIO out (pin 46)**: Freezer fan PWM (always 255 when freezer is on)

### Tab 4: Fans
Core PID controller and fan management.

**Key nodes**:
- **PID Controller** (function): Humidity-based fan speed calculation (Kp=15, Ki=0.08, Kd=8)
- **Day/Night Check**: Within-time-switch, 06:30–20:00
- **Night A/B Test** (function): Alternating night protocol (even day=fans off, odd day=fans 80 PWM)
- **Mister Interlock** (function): Stops fans when mister is active
- **Manual Override**: Dashboard slider, bypasses all automatic control
- **GPIO out (pins 44, 45)**: Outlet and impeller fan PWM outputs
- **RBE nodes**: Report-by-exception logging for fan PWM changes

### Tab 5: Weather
Fetches and processes Colombian highland weather data.

**Key nodes**:
- **OpenWeatherMap** (×4): Chinchiná, Medellín, Bogotá, Sonsón
- **Aggregator/Smooth**: 30-minute averaging window
- **Position config**: Astronomical calculations for dawn/dusk reference

The 15-hour time shift between Colombia (UTC−5) and Italy (UTC+1) means Colombian daytime weather maps to Italian nighttime conditions, producing natural diurnal variation.

### Tab 6: Charts
Node-RED Dashboard UI for local monitoring.

**Key nodes**:
- **Gauges**: Temperature, humidity, VPD
- **Charts**: Time-series of environmental conditions
- **LEDs**: Status indicators for actuators
- **State trails**: Historical on/off visualization

Access at: `http://<your-pi-ip>:1880/ui`

### Tab 7: Utilities
Data logging and system diagnostics.

**Key nodes**:
- **Data Logger** (function): 13 outputs, reads global context every 60 seconds
- **InfluxDB out** (×13): One per measurement, writing to `highland` database
- **Inject** (60s interval): Triggers the data logger

## Node Type Reference

| Node Type | Package | Count | Purpose |
|-----------|---------|-------|---------|
| `function` | core | ~25 | Custom JavaScript logic |
| `change` | core | ~20 | Set/modify message properties |
| `switch` | core | ~15 | Route messages by condition |
| `inject` | core | ~10 | Timed triggers |
| `debug` | core | ~10 | Development/troubleshooting |
| `bigtimer` | node-red-contrib-bigtimer | 3 | Schedule control with astronomical times |
| `influxdb out` | node-red-contrib-influxdb | 16 | Write to InfluxDB |
| `influxdb in` | node-red-contrib-influxdb | 2 | Read from InfluxDB |
| `mqtt in` | core | 2 | Receive MQTT messages |
| `openweathermap` | node-red-node-openweathermap | 4 | Weather API |
| `gpio out` | node-red-contrib-ioplugin | 4 | Arduino PWM outputs |
| `python-function-ps` | node-red-contrib-python-function-ps | 3 | Tapo plug control |
| `hysteresis` | node-red-contrib-hysteresis | 2 | Bang-bang control |
| `dynamic-dimmer` | node-red-contrib-dynamic-dimmer | 1 | LED sunrise/sunset ramp |
| `rbe` | node-red-node-rbe | 3 | Report-by-exception |
| `smooth` | node-red-node-smooth | 4 | Moving average |
| `aggregator` | node-red-contrib-aggregator | 2 | Multi-input averaging |
| `ui_*` | node-red-dashboard | ~40 | Dashboard UI components |

## Troubleshooting

**Nodes show "missing type"**: Install the required npm package for that node type (see table above).

**InfluxDB write errors**: Verify InfluxDB is running (`systemctl status influxdb`) and the `highland` database exists.

**Arduino not connecting**: Check `/dev/ttyACM0` exists, StandardFirmata is uploaded, and no other process holds the serial port.

**Weather nodes show errors**: Verify your OpenWeatherMap API key is configured and the free tier hasn't been rate-limited.

**Tapo plug control fails**: Ensure `PyP100` is installed, credentials are correct, and the plug IPs are reachable from the Pi.
