# System Architecture

## Hardware Overview

### Raspberry Pi (Control Hub)

The Raspberry Pi runs all software services and serves as the central controller:

- **OS**: Debian-based Linux (kernel 6.1.0, ARMv8)
- **Services**: Node-RED, InfluxDB, Grafana, Mosquitto MQTT broker, arduino-watchdog
- **Network**: Ethernet/WiFi for weather API access and remote monitoring

### Arduino Mega 2560 (GPIO Interface)

Connected via USB serial (`/dev/ttyACM0`), running StandardFirmata firmware. Communicates with Node-RED via the `node-red-contrib-ioplugin` Firmata client.

**Pin assignments**:
| Pin | Type | Function |
|-----|------|----------|
| 8 | PWM Output | LED dimmer (sunrise/sunset ramp) |
| 44 | PWM Output | Outlet fan (humidity exhaust) |
| 45 | PWM Output | Impeller fan (internal circulation) |
| 46 | PWM Output | Freezer fan (cold air distribution) |

**USB device path**: `/sys/bus/usb/devices/1-1.1` (vendor `2341:0042`)

### ESP Microcontroller + SHT35 Sensor

Publishes temperature and humidity readings to the MQTT broker at approximately 1-second intervals. The SHT35 provides ±0.1°C temperature and ±1.5% RH accuracy.

**MQTT topic structure**: `[configured per installation]`

### TP-Link Tapo P100 Smart Plugs (×3)

Switched mains power for high-current loads, controlled via the PyP100 Python library from within Node-RED Python function nodes.

| Plug | IP Address | Controls |
|------|------------|----------|
| Lights | 192.168.1.x | 4×100W LED puck array |
| Mister | 192.168.1.x | Ultrasonic misting unit |
| Freezer | 192.168.1.x | Peltier cooling unit |

## Software Stack

### Node-RED v3.1.3 (Control Engine)

**Port**: 1880
**Service**: `systemctl status nodered`
**Config dir**: `~/.node-red/`

Seven flow tabs organize the control logic:

#### Lights Tab
- **BigTimer** node: Fixed schedule 06:25–20:05 (starttime=385, endtime=1205 in minutes-since-midnight)
- **Dynamic Dimmer**: 30-minute PWM ramp at sunrise (06:30) and sunset (19:30)
- **Python function**: Tapo P100 control for light plug
- BigTimer special codes: 5000–5006 represent astronomical events (dawn, sunrise, etc.)

#### Humidity Tab
- **MQTT In**: Receives SHT35 sensor data
- **VPD Calculator**: Magnus formula — SVP, AVP, VPD computation
- **Target humidity**: Weather-derived setpoint with 70–90% clamping
- **Mister control**: Hysteresis controller with Python function for Tapo plug
- **Humidity difference**: Computes target − actual for PID input

#### Temperature Tab
- **Target temperature**: Weather-derived setpoint with 12–24°C clamping
- **Freezer control**: Hysteresis controller with Python function for Tapo plug
- **Temperature difference**: Computes target − actual

#### Fans Tab
- **PID Controller**: Core humidity-based fan speed calculation (see `pid-controller.md`)
- **Day/Night Check**: Within-time-switch node, 06:30–20:00 schedule
- **Night A/B Test**: Alternating night protocol (even=fans off, odd=fans 80 PWM)
- **Mister interlock**: Gates PID output — blocks fan commands when mister is active
- **Manual override**: Dashboard UI slider, highest priority control
- **GPIO outputs**: Three PWM output nodes to Arduino pins 44, 45, 46

#### Weather Tab
- **OpenWeatherMap** nodes: Four instances for Chinchiná, Medellín, Bogotá, Sonsón
- **Aggregator/Smooth**: Averages and smooths weather values (30-min window)
- **Position config**: lat=5.19485 (tepui reference), lon=8.944381 (Genoa) for astronomical calculations

#### Charts Tab
- **Dashboard UI** components: Gauges (temp, humidity, VPD), time-series charts, status LEDs
- Real-time and historical visualization within the Node-RED Dashboard

#### Utilities Tab
- **Data Logger**: Function node with 13 outputs, triggered every 60 seconds
- Each output connects to an individual InfluxDB out node
- Reads all global context variables and writes to the `highland` database

### Node-RED Node Dependencies

Required npm packages (install in `~/.node-red/`):

| Package | Node Types Used |
|---------|-----------------|
| `node-red-contrib-bigtimer` | bigtimer |
| `node-red-contrib-ioplugin` | ioplugin, gpio in, gpio out |
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

### InfluxDB v1.8.10 (Time-Series Storage)

**Port**: 8086
**Database**: `highland`
**Retention**: 365 days (`standard_highland_retention`)
**Measurements**: 26 (see `schema.md`)

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
| Night A/B Fan Experiment | `night-ab-test` | A/B comparison with night mode shading |

### Arduino Watchdog v3

**Script**: `/usr/local/bin/arduino-watchdog.sh`
**Service**: `arduino-watchdog.service`
**Log**: `/var/log/arduino-watchdog.log`
**Check interval**: 60 seconds

Four-stage health check:
1. USB device `/dev/ttyACM0` exists
2. Node-RED systemd service is active
3. Node-RED has the serial port open (`lsof`)
4. Firmata is genuinely connected (last log line analysis)

Three-level recovery escalation:
1. Restart Node-RED (2× within 30 min window)
2. USB reset via sysfs + NR restart (2× more)
3. Full system reboot

## Data Flow

```
SHT35 Sensor
    │
    ▼ (MQTT)
ESP Microcontroller ──► MQTT Broker (:1883)
                              │
                              ▼
                        Node-RED
                         │    │    │
    ┌────────────────────┘    │    └────────────────────┐
    ▼                         ▼                         ▼
Humidity Tab             Temperature Tab           Weather Tab
  │ VPD calc               │ Freezer hysteresis     │ 4 cities
  │ Target humidity         │ Target temperature     │ Averaging
  │ Mister control          │                        │
  │ Diff calculation        │                        │
  └──────────┬──────────────┘                        │
             │                                        │
             ▼                                        │
         Fans Tab ◄───────────────────────────────────┘
           │ PID controller
           │ Night A/B test
           │ Mister interlock
           │ Manual override
           │
    ┌──────┼──────┐
    ▼      ▼      ▼
 Pin 44  Pin 45  Pin 46    (via Firmata → Arduino Mega)
 Outlet  Impel.  Freezer

         All tabs
           │
           ▼
      Utilities Tab
        Data Logger
           │
           ▼
      InfluxDB (:8086)
           │
           ▼
      Grafana (:3000)
```

## Systemd Services

| Service | Purpose | Restart Policy |
|---------|---------|----------------|
| `nodered` | Node-RED control engine | Always, managed by watchdog |
| `influxdb` | Time-series database | on-failure |
| `grafana-server` | Visualization | on-failure |
| `mosquitto` | MQTT broker | on-failure |
| `arduino-watchdog` | Arduino/Firmata health monitor | Always, RestartSec=10 |
