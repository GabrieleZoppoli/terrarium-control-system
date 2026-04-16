# Highland Cloud Forest Terrarium Control System

An open-source environmental control system for simulating tropical highland cloud forest climates in enclosed terrariums, using real-time Colombian weather data, gain-scheduled PID humidity management, compressor-based cooling, and dynamic photoperiod control.

## Overview

This system maintains approximately 120 cloud forest plant species (*Heliamphora*, *Dracula*, *Dendrobium* sect. *Oxyglossum*, *Cattleya* subg. *Sophronitis*, highland *Nepenthes*, *Utricularia* sect. *Orchidioides*, and more) in a 1.5 x 0.6 x 1.1 m terrarium in Genoa, Italy. It achieves 13.5--24.3 C temperature range and 75--98% relative humidity by integrating real-time weather data from four Colombian highland cities (1,300--2,600 m elevation) with a three-regime PID controller and a Vitrifrigo ND50 marine compressor.

Species from convergent cloud forests worldwide -- Venezuelan tepuis, Colombian Andes, Papua New Guinea highlands, Brazilian Atlantic Forest, and montane Borneo-Sumatra -- coexist because their native environments converge on similar climatic envelopes despite geographic isolation.

**[Website](https://gabrielezoppoli.github.io/terrarium-control-system/)** | **[Paper](paper/icps-paper.md)** | **[Technical Docs](docs/)**

## Key Features

- **Weather-mimicking setpoints** from 4 Colombian cities with 15-hour time shift
- **Marine compressor cooling** to 13.5 C (3 C below evaporative limit)
- **Three-regime PID fan control**: humidity-driven, temperature-driven, or compressor-assisted
- **Wet-bulb temperature shutdown**: fans automatically disengage when evaporative cooling becomes counterproductive
- **Dynamic photoperiod** computed from Colombian latitude (4.98 N)
- **32 InfluxDB measurements** logged every 60 seconds
- **Door safety mode** with automatic protection during maintenance
- **Historical weather fallback** from 14-day smoothed curves

## Repository Structure

```
terrarium-control-system/
+-- paper/                      # ICPS/CPN consolidated paper
+-- firmware/
|   +-- arduino-terrarium/      # Arduino Mega custom serial protocol
|   +-- esp-water-level/        # ESP8266 water level sensor
+-- nodered/
|   +-- flows-sanitized.json    # Node-RED flows (credentials removed)
|   +-- flows-README.md         # Import guide and tab descriptions
+-- grafana/                    # 4 exported dashboard definitions
+-- scripts/
|   +-- arduino-watchdog.sh     # USB serial health monitor
|   +-- mister-failsafe.py      # Cron-based mister safety cutoff
|   +-- meross_daemon.py        # Persistent power monitoring daemon (MQTT)
|   +-- meross_script.py        # Legacy power script (replaced by daemon)
|   +-- snapshot-capture.sh     # Grafana dashboard screenshots
+-- systemd/
|   +-- arduino-watchdog.service # USB serial health monitor
|   +-- meross-daemon.service    # Persistent power monitoring
+-- analysis/                   # Statistical analysis scripts
+-- docs/                       # Architecture, schema, PID docs
+-- website/                    # Hugo site (Blowfish theme)
```

## Architecture

```
SHT35 + ESP8266 --> MQTT --> Node-RED --> Arduino Mega (PWM fans, dimmer)
                              |    |
                              |    +--> Tapo P100 (lights, mister, compressor)
                              |
                              +--> InfluxDB --> Grafana
```

Node-RED runs 7 flow tabs (Lights, Humidity, Temperature, Fans, Weather, Charts, Utilities) on a Raspberry Pi 4. The Arduino Mega provides 5 PWM outputs (dimmer, circulation, evaporator, outlet, impeller fans) and 2 door sensor inputs via a text-based serial protocol at 115,200 baud.

## Environmental Performance

| Parameter | Range Achieved | Typical |
|-----------|---------------|---------|
| Temperature | 13.5--24.3 C | 15--22 C |
| Humidity | 75--98% RH | 82--95% |
| VPD | 0.03--0.64 kPa | 0.08--0.45 kPa |
| Diurnal swing | 4--8 C | 6 C |

## Quick Start

See the [technical documentation](docs/) for detailed setup instructions.

1. Flash Arduino firmware: `arduino-cli upload -p /dev/ttyUSB0 --fqbn arduino:avr:mega firmware/arduino-terrarium/`
2. Install Node-RED and required nodes (see `nodered/flows-README.md`)
3. Import flows from `nodered/flows-sanitized.json`
4. Set up InfluxDB and Grafana
5. Configure Tapo plug credentials in the Python function nodes

## License

CERN Open Hardware Licence Version 2 -- Strongly Reciprocal (CERN-OHL-S v2). See [LICENSE](LICENSE).

## Citation

If you use this system in your research, please cite:

[USER INPUT NEEDED -- citation will be added after publication]

See also `CITATION.cff` for machine-readable citation metadata.
