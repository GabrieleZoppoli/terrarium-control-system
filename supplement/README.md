# Highland Cloud Forest Terrarium Control System

An open-source environmental control system for simulating tepui (highland cloud forest) climates in enclosed terrariums, using real-time Colombian weather data and PID-based humidity management.

## Overview

This system maintains approximately 120 cloud forest plant species (*Heliamphora*, *Dracula*, *Sophronitis*, highland *Nepenthes*, New Guinea *Dendrobium*, and more) in a 1.5 × 0.6 × 1.1 m terrarium located in Genoa, Italy. It achieves 13.5–24.3°C temperature range and 75–98% relative humidity by integrating weather data from four Colombian highland cities with a PID controller for fan-based humidity management.

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     MONITORING LAYER                         │
│  ┌────────────────────┐    ┌─────────────────────────────┐   │
│  │   Grafana v10.2    │    │    Node-RED Dashboard UI    │   │
│  │    (port 3000)     │    │       (port 1880/ui)        │   │
│  │  4 dashboards      │    │  Gauges, charts, controls   │   │
│  └────────┬───────────┘    └──────────┬──────────────────┘   │
│           │                           │                       │
├───────────┼───────────────────────────┼───────────────────────┤
│           │        STORAGE LAYER      │                       │
│  ┌────────▼───────────────────────────▼──────────────────┐   │
│  │              InfluxDB v1.8.10 (port 8086)             │   │
│  │         Database: "highland" — 26 measurements        │   │
│  │            1-year retention, 60s write interval        │   │
│  └───────────────────────┬───────────────────────────────┘   │
│                          │                                    │
├──────────────────────────┼────────────────────────────────────┤
│                   CONTROL LAYER                               │
│  ┌───────────────────────▼───────────────────────────────┐   │
│  │              Node-RED v3.1.3 (port 1880)              │   │
│  │                                                        │   │
│  │  ┌─────────┐ ┌──────────┐ ┌─────────┐ ┌───────────┐  │   │
│  │  │ Lights  │ │ Humidity │ │  Temp   │ │   Fans    │  │   │
│  │  │ BigTimer│ │ VPD calc │ │ Freezer │ │ PID ctrl  │  │   │
│  │  │ Dimmer  │ │ Mister   │ │ Hyster. │ │ Night A/B │  │   │
│  │  └─────────┘ └──────────┘ └─────────┘ └───────────┘  │   │
│  │  ┌─────────┐ ┌──────────┐ ┌──────────────────────┐   │   │
│  │  │ Weather │ │  Charts  │ │     Utilities        │   │   │
│  │  │ 4 cities│ │  Gauges  │ │ Data Logger (13 out) │   │   │
│  │  └─────────┘ └──────────┘ └──────────────────────┘   │   │
│  └───────────────────────────────────────────────────────┘   │
│                                                               │
├───────────────────────────────────────────────────────────────┤
│                   HARDWARE INTERFACE LAYER                     │
│                                                               │
│  ┌──────────┐    ┌─────────────────┐    ┌─────────────────┐  │
│  │   MQTT   │    │    Firmata      │    │    PyP100       │  │
│  │  :1883   │    │  USB serial     │    │   TCP/IP        │  │
│  └────┬─────┘    └───────┬─────────┘    └───────┬─────────┘  │
│       │                  │                      │             │
├───────┼──────────────────┼──────────────────────┼─────────────┤
│       │           PHYSICAL LAYER                │             │
│  ┌────▼─────┐    ┌───────▼─────────┐    ┌───────▼─────────┐  │
│  │  ESP +   │    │  Arduino Mega   │    │ Tapo P100 ×3    │  │
│  │  SHT35   │    │  2560           │    │                 │  │
│  │  sensor  │    │  Pin 44: Outlet │    │ .55:  Lights    │  │
│  │          │    │  Pin 45: Impel. │    │ .199: Mister    │  │
│  │          │    │  Pin 46: Freezer│    │ .196: Freezer   │  │
│  │          │    │  Pin 8:  Dimmer │    │                 │  │
│  └──────────┘    └─────────────────┘    └─────────────────┘  │
└───────────────────────────────────────────────────────────────┘
```

## Repository Contents

| File | Description |
|------|-------------|
| `flows-sanitized.json` | Node-RED flows with credentials removed |
| `flows-README.md` | Flow import guide and tab descriptions |
| `arduino-watchdog.sh` | Watchdog script for Arduino/Firmata health |
| `systemd/arduino-watchdog.service` | systemd service unit for watchdog |
| `grafana/*.json` | Exported Grafana dashboard definitions |
| `schema.md` | InfluxDB measurement schema (26 measurements) |
| `architecture.md` | Detailed system architecture documentation |
| `pid-controller.md` | PID algorithm documentation with equations |
| `LICENSE` | MIT License |

## Quick Start

### Prerequisites

- Raspberry Pi (or any Linux system) with Node.js 18+
- Arduino Mega 2560 with StandardFirmata sketch uploaded
- InfluxDB 1.8.x
- Grafana 10.x
- MQTT broker (e.g., Mosquitto)

### Installation

1. **Install Node-RED**:
   ```bash
   bash <(curl -sL https://raw.githubusercontent.com/node-red/linux-installers/master/deb/update-nodejs-and-nodered)
   sudo systemctl enable nodered
   ```

2. **Install required Node-RED nodes** (see `flows-README.md` for complete list):
   ```bash
   cd ~/.node-red
   npm install node-red-contrib-bigtimer \
               node-red-contrib-ioplugin \
               node-red-node-openweathermap \
               node-red-contrib-influxdb \
               node-red-node-smooth \
               node-red-contrib-python-function-ps \
               node-red-contrib-dynamic-dimmer
   ```

3. **Install InfluxDB 1.8**:
   ```bash
   sudo apt install influxdb
   sudo systemctl enable influxdb
   influx -execute "CREATE DATABASE highland"
   influx -execute "CREATE RETENTION POLICY standard_highland_retention ON highland DURATION 365d REPLICATION 1 DEFAULT"
   ```

4. **Install Grafana**:
   ```bash
   sudo apt install grafana
   sudo systemctl enable grafana-server
   ```

5. **Import Node-RED flows**: See `flows-README.md` for detailed instructions.

6. **Import Grafana dashboards**: Import the JSON files from `grafana/` via the Grafana UI (Dashboards → Import → Upload JSON file).

7. **Configure credentials**: Update the three Python function nodes in the flows with your TP-Link Tapo account credentials and smart plug IP addresses.

8. **Install watchdog** (optional):
   ```bash
   sudo cp arduino-watchdog.sh /usr/local/bin/
   sudo chmod +x /usr/local/bin/arduino-watchdog.sh
   sudo cp systemd/arduino-watchdog.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable arduino-watchdog
   sudo systemctl start arduino-watchdog
   ```

## Environmental Performance

| Parameter | Range Achieved | Target |
|-----------|---------------|--------|
| Temperature | 13.5–24.3°C | 12–24°C |
| Humidity | 75–98% RH | 70–90% |
| VPD | 0.03–0.64 kPa | < 0.8 kPa |
| Diurnal swing | 4–8°C | Natural variation |

## Key Design Decisions

- **Weather-based setpoints** instead of fixed values — produces naturalistic climate variation
- **PID controller** for humidity/fan management — smoother than bang-bang control
- **Safety interlocks** — fans stop during misting to prevent fog dispersal
- **Comprehensive logging** — 26 measurements for long-term analysis and experimentation
- **Automatic recovery** — watchdog handles Arduino disconnections without human intervention

## License

MIT License — see `LICENSE` file.

## Citation

If you use this system in your research, please cite:

```
[PLACEHOLDER — citation details will be added after publication]
```
