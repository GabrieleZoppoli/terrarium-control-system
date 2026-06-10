# Node-RED Flows — Import Guide

## Overview

`flows-sanitized.json` contains the complete Node-RED control logic for the highland cloud forest terrarium, organized across 7 flow tabs (~486 nodes as of the current export). Credentials have been replaced with placeholders. This guide was refreshed June 2026 to match the deployed system; see "Recent architecture changes" at the end for features that supersede earlier descriptions.

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

The Tapo smart plug control uses Python function nodes (via the maintained `tapo` async library), and the Meross power monitor runs as a standalone systemd daemon:

```bash
pip3 install tapo meross-iot
```

Note: earlier revisions used the unmaintained `PyP100` library; the deployed system uses `tapo` (async `ApiClient`). The Meross integration is now a long-running daemon (`meross_daemon.py`) publishing to MQTT, not an inline `exec` of a one-shot script.

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

The `meross_script.py` requires Meross cloud credentials. Edit the script and replace `YOUR_EMAIL` and `YOUR_PASSWORD` with your Meross account credentials. Also update `PLUG_ID` to match your plug's name. If you don't have a Meross plug, disable the "Get energy" inject node on the Utilities tab.

## Flow Tab Descriptions

### Tab 1: Lights
Computes a dynamic, latitude-derived photoperiod and drives a raised-cosine LED brightness curve (Light Curve C).

**Key nodes**:
- **Photoperiod Calculator** (`photo_calc_fn_001`): Computes daily day length from the Chinchiná reference latitude (4.98° N), clamped to 10–14 h, centred on solar noon (~13:15 CEST); exposes `photo_light_on/off`, `photo_sunrise/sunset` globals.
- **Unified Light Scheduler** (`light_sched_fn_001`): Handles the Tapo on/off transitions only (replaced the earlier BigTimer fixed schedule).
- **Light Curve C** (`light_curve_fn_001` + 60 s tick): Raised-cosine brightness curve, floor 35 / peak 70 at solar noon, written to the slider → inverted PWM on pin 8. Replaced the prior two-step dynamic-dimmer ramp (disabled 2026-05-04).
- **Startup brightness** (`b7f27d1dd5437650`): On a mid-ramp restart, computes the elapsed fraction and issues a partial `start` so the curve completes on schedule.
- **Pin 8 writer**: Sends `P8,<value>` via serial; door-safety gated (forces PWM 102 ≈ 60 % when doors open).
- **Python function**: Tapo plug control (door-safety gated).

**Flow**: scheduler powers the LED plug on/off → Light Curve C continuously sets pin-8 PWM along the raised-cosine profile for a smooth sunrise → midday-peak → sunset radiant load.

Note: the `node-red-contrib-dynamic-dimmer` package is retained in the dependency list for backward compatibility but is no longer on the active light path (superseded by Light Curve C).

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
Manages compressor-based cooling with a target-relative hysteresis and a daytime gate.

**Key nodes**:
- **Target temperature**: Derived from Colombian weather data (clamped 12–24 °C) at night.
- **Freezer daytime gate** (`within-time-switch` → `Freezer target 24.75°C`): Between astronomical dawn and dusk the target is held at a hardcoded 24.75 °C (ON ≥ 25.25 °C, OFF ≤ 24.25 °C); the daytime gate is overridden when cabinet T ≥ 25 °C so cooling is never blocked when the cabinet runs warm.
- **Hysteresis** (±0.5 °C around the active target): Controls compressor on/off.
- **Python function**: Tapo plug control for the compressor (door-safety gated).

### Tab 4: Fans
Core PID controller, door safety, and fan management.

**Key nodes**:
- **PID Controller** (function): Gain-scheduled fan speed with a **two-regime** error signal — humidity-driven below 24 °C, temperature-driven at/above 24 °C (persisting through compressor engagement as a ceiling-defence cooling actuator). Gain schedule: effective Kp 7.5 within ±1.5 % of target, full Kp 50 for errors ≥ 4 %; MAX_SPEED 255, BASE_SPEED 50.
- **Day/Night Check**: Within-time-switch, 04:00–00:00 (midnight); fans off 00:00–04:00.
- **Night Mode (A/B Suspended)**: Outputs 0. A/B code preserved in comments with reactivation instructions.
- **Mister Interlock** (function): On a mist event, sets outlet/impeller (P45/P46) to 50 PWM and coil fans (P44/P12) to 0 (deletes topic to avoid RBE conflicts).
- **Manual Override**: Dashboard Auto/Pause/Max buttons; a 30-minute watchdog (`manual_mode_watchdog_fn_001`) auto-reverts a left-on override back to auto.
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
- **Data Logger** (function): 16 outputs, reads global context every 60 seconds (continuous channels); fan-PWM channels are logged separately via RBE on value change.
- **InfluxDB out** (×16+): One per measurement, writing to `highland` database (33 documented measurements across all sources; see `docs/schema.md`).
- **Meross power monitoring**: the `meross_daemon.py` systemd service polls the MSS310 (2–120 s cadence) and publishes to MQTT `meross/power/watts`; an MQTT-In node writes `power_consumption` to InfluxDB. (Replaces the earlier `exec`-of-`meross_script.py` approach.)
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

**Fans stuck at 0 after misting**: This was a known RBE topic bug, now fixed. Ensure the mister-interlock function deletes `msg.topic` rather than setting it to `"mister_override"`.

## Recent architecture changes

Features in the deployed system that supersede older descriptions a reader may find in earlier exports or the original paper draft:

- **Lighting**: the two-step dynamic-dimmer ramp was replaced on 2026-05-04 by a latitude-derived dynamic photoperiod (`photo_calc_fn_001`) plus a raised-cosine brightness curve (Light Curve C, `light_curve_fn_001`). The fixed BigTimer schedule was replaced by `light_sched_fn_001`.
- **Fan control**: the PID error signal is two-regime (humidity below 24 °C, temperature at/above 24 °C, persisting through compressor engagement). The outlet fan (pin 45) is capped at 110 PWM for quiet daytime baseline, with the cap lifted at T ≥ 24 °C.
- **Cooling**: the compressor has a daytime gate (hardcoded 24.75 °C target, dawn→dusk) overridden at T ≥ 25 °C.
- **Safety chain**: eleven layers (door interlock, mister duration failsafe, freezer daytime gate, wet-bulb fan-off gate [deprecated rationale], manual-override timeout, USB-serial watchdog, LED-fault watchdog, power-vs-commanded cross-check, weather staleness fallback, Pi↔Arduino serial CRC integrity, mister water-level gate). Deployment chronology in `paper/safety_chain_deployment_dates.yaml`.
- **Serial link**: every Pi→Mega command carries a CRC-8 byte and is written as a single atomic line; the Mega replies `ERR_CRC` on mismatch.
- **Weather fallback**: a rolling 14-day historical diurnal curve, rebuilt every 6 hours from the InfluxDB archive, transparently replaces the live feed when the pipeline is stale.
- **Plug control**: `tapo` async `ApiClient` (not `PyP100`); Meross via the `meross_daemon.py` systemd service.
