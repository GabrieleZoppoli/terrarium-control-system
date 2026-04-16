---
title: "System Architecture"
description: "Hardware layers, communication protocols, and software stack"
---


## Hardware Overview

### Raspberry Pi (Control Hub)

The Raspberry Pi runs all software services and serves as the central controller:

- **OS**: Debian-based Linux (kernel 6.1.0, ARMv8)
- **Services**: Node-RED, InfluxDB, Grafana, Mosquitto MQTT broker, arduino-watchdog
- **Network**: Ethernet/WiFi for weather API access and remote monitoring

### Arduino Mega 2560 (GPIO Interface)

Connected via USB serial (`/dev/ttyACM0`) at 115200 baud, running a custom text-based protocol (see `arduino-terrarium.ino`). The protocol replaced StandardFirmata in February 2026 for improved reliability and debuggability.

**Serial protocol**:
- Pi → Arduino: `P<pin>,<value>` (PWM), `Q` (query all states), `H,<value>` (heartbeat config)
- Arduino → Pi: `READY` (boot), `H,<value>` (heartbeat every 2s), `D<pin>,<0|1>` (door state), `OK,P<pin>,<value>` (ack), `S,P8=...,P12=...,P44=...,P45=...,P46=...` (status)

**Pin assignments**:
| Pin | Type | Timer | Function |
|-----|------|-------|----------|
| 8 | PWM Output | Timer 4 (~490 Hz) | LED dimmer (sunrise/sunset ramp) |
| 12 | PWM Output | Timer 1 (25 kHz) | Internal circulation fans (OC1B) |
| 44 | PWM Output | Timer 5 (25 kHz) | Freezer/evaporator fans (OC5C) |
| 45 | PWM Output | Timer 5 (25 kHz) | Outlet fan — humidity exhaust (OC5B) |
| 46 | PWM Output | Timer 5 (25 kHz) | Impeller fan — air intake (OC5A) |
| A0 | Analog Input | — | Heartbeat reference (analog read sent every 2s) |
| D22 | Digital Input | — | Left door reed switch (INPUT_PULLUP, LOW=open) |
| D24 | Digital Input | — | Right door reed switch (INPUT_PULLUP, LOW=open) |

**USB device path**: `/sys/bus/usb/devices/1-1.1` (vendor `2341:0042`)

**PWM frequency**: Pins 12, 44, 45, 46 use 25 kHz phase-correct PWM (ICRn=320, prescaler=1). This is above the audible range and compatible with Noctua 4-pin PWM fan inputs. Pin 8 uses the default ~490 Hz, which is fine for the LED driver's analog dimming input.

### ESP8266 + SHT35 Sensor

Publishes temperature and humidity readings to the MQTT broker at approximately 1-second intervals. The SHT35 provides ±0.1°C temperature and ±1.5% RH accuracy. The same ESP8266 reads an HC-SR04 ultrasonic distance sensor for water level monitoring.

**MQTT topic structure**: `[configured per installation]`

### TP-Link Tapo P100 Smart Plugs (×3)

Switched mains power for high-current loads, controlled via the PyP100 Python library from within Node-RED Python function nodes.

| Plug | IP Address | Controls |
|------|------------|----------|
| Lights | 192.168.1.55 | 4×100W ChilLED Logic Puck V3 array |
| Mister | 192.168.1.199 | MistKing diaphragm pump |
| Compressor | 192.168.1.196 | Vitrifrigo ND50 compressor unit |

### Meross MSS310 Smart Plug

Energy-monitoring plug at 192.168.1.92 on the master power line. A persistent Python daemon (`meross_daemon.py`) maintains a single authenticated session to the Meross cloud API (iotx-eu.meross.com) and publishes instantaneous power readings to the local MQTT broker (`meross/power/watts`) every 2 seconds. This replaced an earlier approach that spawned a new process every 120 seconds, each performing a full login/discover/logout cycle. The daemon also accepts on/off commands via MQTT (`meross/power/command`), enabling sub-second response to the dashboard panic button. It runs as a systemd service (`meross-daemon`) with automatic restart on failure.

### Door Reed Switches (×2)

Magnetic reed switches on both sliding front panels, wired to Arduino D22 (left) and D24 (right) with internal pull-up resistors. Door open = LOW. The Arduino polls at 100ms intervals, reports on state change plus periodic 10s heartbeat. A 3-second software debounce in Node-RED suppresses contact bounce.

## Software Stack

### Node-RED v3.1.3 (Control Engine)

**Port**: 1880
**Service**: `systemctl status nodered`
**Config dir**: `~/.node-red/`

Seven flow tabs organize the control logic:

#### Lights Tab
- **Photoperiod Calculator** (function): Computes day length for Chinchiná (4.98°N) using solar declination. Clamped 10–14h, centered on 13:15 Genoa time. Fires at startup (5s delay) and daily at 00:05.
- **Unified Light Scheduler** (function): Receives 1-minute ticks, reads computed photoperiod globals. Controls Tapo on/off and dimmer ramp triggers at dynamically calculated times.
- **Dynamic Dimmer #1**: 30-minute PWM ramp at dawn/dusk, slider 0↔40
- **Dynamic Dimmer #2**: 30-minute midday ramp (proportional to day length), slider 40↔60
- **Startup brightness**: Detects ramp-window restarts using dynamic photoperiod times, issues partial-start for on-schedule completion
- **Pin 8 writer**: Sends `P8,<value>` via serial; stores `last_dimmer_pwm`, forces PWM 102 during door safety
- **Python function**: Tapo P100 control for light plug (with door safety gate)
- *Disabled*: BigTimer (fixed schedule), 4 time-inject nodes, 4 ramp function nodes — replaced by dynamic scheduler

#### Humidity Tab
- **MQTT In**: Receives SHT35 temperature + humidity from ESP
- **VPD Calculator** (function): Computes Vapor Pressure Deficit using Magnus formula
- **Target humidity**: Derived from Colombian weather data (upper cap 95% RH)
- **Humidity difference**: target − actual, feeds PID controller on Fans tab
- **Hysteresis**: Controls mister on/off around target humidity
- **Python function**: Tapo P100 plug control for mister (with door safety gate)

#### Temperature Tab
- **Target temperature**: Derived from Colombian weather data (clamped 12--24°C)
- **Temperature difference**: target − actual
- **Hysteresis**: Controls compressor on/off based on temperature error
- **Python function**: Tapo P100 plug control for compressor (with door safety gate)

#### Fans Tab
- **PID Controller** (function): Three-regime gain-scheduled fan speed control (Kp=50, Ki=0.5, Kd=10). Normal mode (T<24°C): humidity PID. Warm mode (24–25°C, freezer off): temperature PID for evaporative cooling. Hot mode (≥25°C): humidity PID with freezer active.
- **Day/Night Check**: Within-time-switch, 04:00–00:00 (midnight)
- **Night Mode (A/B Suspended)**: Always outputs 0 (A/B code preserved in comments for reactivation)
- **Mister Interlock** (function): Stops all fans when mister is active
- **Manual Override**: Dashboard slider, highest priority control
- **Fan writers**: 4 serial output nodes (outlet pin 45, impeller pin 46, evaporator pin 44, circulation pin 12), all door-safety gated
- **RBE nodes**: Report-by-exception logging for fan PWM changes
- **Door safety controller**: OR-tracks both doors, 3s debounce, triggers safety mode
- **Door safety outputs**: 4 outputs (serial fan stop, compressor off, mister off, lights to 60%)

#### Weather Tab
- **OpenWeatherMap** nodes: Four instances for Chinchiná, Medellín, Bogotá, Sonsón
- **Aggregator/Smooth**: Averages and smooths weather values (30-min InfluxDB window + 15-min rolling mean across 4 cities)
- **Position config**: lat=5.19485 (tepui reference), lon=8.944381 (Genoa) for astronomical calculations
- **Weather fallback**: Historical 14-day daily curve (288 slots, two-pass smoothed) when API is unreachable; ultimate fallback (day T=24/H=85, night T=14/H=90) if no historical data
- **Historical curve builder**: Rebuilds every 6 hours from InfluxDB; applies 15-hour time shift baked into curve slots

#### Charts Tab
- **Dashboard UI** components: Gauges (temp, humidity, VPD), time-series charts, status LEDs
- **3-series charts**: Temperature and humidity charts show current (blue), target (red), and room (green)
- **Room data inject**: 60s repeat, reads global room_temperature/room_humidity
- **Chart persistence**: Data saved to flow context, restored on startup via inject nodes
- Real-time and historical visualization within the Node-RED Dashboard

#### Utilities Tab
- **Data Logger**: Function node with 16 outputs, triggered every 60 seconds
- Each output connects to an individual InfluxDB out node
- Reads all global context variables and writes to the `highland` database
- **Serial config**: Serial port node at 115200 baud, \n delimiter
- **Serial parser**: Parses heartbeat (H,val), door states (D22/D24), error messages
- **Meross power monitoring**: MQTT subscription (`meross/power/watts`) from persistent daemon → parse → UI + InfluxDB (2s updates)
- **Mist counter persistence**: Saves/restores today's and yesterday's mist counts across reboots
- **Resend PWM**: Periodically re-sends current fan speeds to prevent stale serial state

### Node-RED Node Dependencies

Required npm packages (install in `~/.node-red/`):

| Package | Node Types Used |
|---------|-----------------|
| `node-red-contrib-bigtimer` | bigtimer |
| `node-red-node-openweathermap` | openweathermap |
| `node-red-contrib-influxdb` | influxdb out, influxdb in |
| `node-red-node-smooth` | smooth |
| `node-red-contrib-python-function-ps` | python-function-ps |
| `node-red-contrib-dynamic-dimmer` | dynamic-dimmer |
| `node-red-contrib-sun-position` | position-config, within-time-switch, time-inject |
| `node-red-node-rbe` | rbe |
| `node-red-contrib-stoptimer-varidelay` | stoptimer-varidelay |
| `node-red-contrib-aggregator` | aggregator |
| `node-red-contrib-hysteresis` | hysteresis |
| `node-red-contrib-ui-led` | ui_led |
| `node-red-contrib-ui-statetrail` | ui_statetrail |
| `node-red-dashboard` | ui_base, ui_tab, ui_group, ui_gauge, ui_chart, ui_text, ui_button, ui_slider, ui_spacer |
| `node-red-node-serialport` | serial in, serial out, serial port |

Note: `node-red-contrib-ioplugin` is no longer required (Firmata removed).

### InfluxDB v1.8.10 (Time-Series Storage)

**Port**: 8086
**Database**: `highland`
**Retention**: 365 days (`standard_highland_retention`)
**Measurements**: 32 (see `schema.md`)

Query interface:
```bash
# CLI (recommended)
influx -database highland -execute 'SELECT last("value") FROM "local_temperature"'

# HTTP POST
curl -s -XPOST 'http://localhost:8086/query' --data-urlencode "db=highland" --data-urlencode "q=SELECT last(\"value\") FROM \"local_temperature\""
```

Note: `curl -sG` (GET) returns empty results — always use POST or the CLI.

### Grafana v10.2.3 (Visualization)

**Port**: 3000
**Default credentials**: admin/admin (change on first login in production)

Four dashboards:

| Dashboard | UID | Purpose |
|-----------|-----|---------|
| Terrarium — Roraima | `terrarium-roraima` | Primary monitoring: temp, humidity, VPD, actuator status |
| Colombian Weather Reference | `colombian-weather-ref` | Raw weather from 4 cities |
| System Performance | `system-performance` | PID diagnostics, fan PWM, control quality |
| Night A/B Fan Experiment | `night-ab-test` | Historical A/B comparison (experiment suspended) |

### Arduino Watchdog v7

**Script**: `/usr/local/bin/arduino-watchdog.sh`
**Service**: `arduino-watchdog.service`
**Log**: `/var/log/arduino-watchdog.log`
**Check interval**: 60 seconds

Four-step health check:
1. USB device `/dev/ttyACM0` exists
2. Node-RED systemd service is active
3. Node-RED has the serial port open (`lsof`)
4. GPIO heartbeat alive (last `arduino_status` in InfluxDB within 3 minutes)

Recovery strategy:
- **NR process issues** (steps 2–3): Up to 2 NR restarts in 30 min, then reboot
- **Heartbeat dead** (step 4): Reboot directly (NR restarts don't fix serial stall)
- **Reboot cooldown**: Skip if system uptime < 10 min
- **GPIO grace period**: 5 min after NR start before checking heartbeat
- **Diagnostics**: Snapshot logged before every reboot (PID, FDs, memory, dmesg)

## Data Flow

```
SHT35 Sensor
    │
    ▼ (MQTT)
ESP8266 ──────────► MQTT Broker (:1883)
                          │
                          ▼
                    Node-RED
                     │    │    │    │
    ┌────────────────┘    │    │    └──────────────────┐
    ▼                     ▼    ▼                       ▼
Humidity Tab         Temp Tab  Fans Tab            Weather Tab
  │ VPD calc           │       │ PID controller      │ 4 cities
  │ Target humidity    │       │ Door safety          │ Averaging
  │ Mister control     │       │ Mister interlock     │ Fallback
  │ Diff calculation   │       │ Manual override      │
  └──────────┬─────────┘       │                      │
             │                 │                      │
             ▼                 ▼                      │
         Fans Tab ◄───────────────────────────────────┘
           │
    ┌──────┼──────┬──────┐
    ▼      ▼      ▼      ▼
 Pin 12  Pin 44  Pin 45  Pin 46    (via custom serial → Arduino)
 Circ.   Freezer Outlet  Impel.

         All tabs
           │
           ▼
      Utilities Tab
        Data Logger + Serial Parser + Meross
           │
           ▼
      InfluxDB (:8086)
           │
           ▼
      Grafana (:3000)

    Door Reed Switches (D22, D24)
           │
           ▼ (serial from Arduino)
      Serial Parser → Door Controller → Door Safety
                                            │
                                    ┌───────┼───────┬──────────┐
                                    ▼       ▼       ▼          ▼
                               Fans OFF  Compressor Mister   Lights
                              (P12-P46)   OFF       OFF      60%
```

## Systemd Services

| Service | Purpose | Restart Policy |
|---------|---------|----------------|
| `nodered` | Node-RED control engine | Always, managed by watchdog |
| `influxdb` | Time-series database | on-failure |
| `grafana-server` | Visualization | on-failure |
| `mosquitto` | MQTT broker | on-failure |
| `arduino-watchdog` | Arduino serial health monitor | Always, RestartSec=10 |
