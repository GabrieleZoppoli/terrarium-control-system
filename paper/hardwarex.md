# Weather-Mimicking Terrarium for Cloud Forest Species: An Open-Source Climate Simulation System Using Real-Time Meteorological Data

**Authors**: `[PLACEHOLDER — author names and affiliations]`

**Corresponding author**: `[PLACEHOLDER — email]`

---

## Specifications Table

| | |
|---|---|
| **Hardware name** | Weather-Mimicking Biotope (WMB) — Cloud Forest Terrarium Controller |
| **Subject area** | Environmental science and ecology; Biological sciences (botany, conservation); Engineering (control systems) |
| **Hardware type** | Environmental monitoring and control |
| **Closest commercial analogue** | Terrarium controllers (MistKing HygroStat, TerraControl Pro); growth chambers (Percival, Conviron) |
| **Open-source license** | CERN Open Hardware Licence v2 — Permissive (CERN-OHL-P-2.0) |
| **Cost of hardware** | `[PLACEHOLDER — total estimated cost in EUR/USD]` |
| **Source file repository** | `[PLACEHOLDER — Zenodo DOI after upload]` |

---

## Abstract

We present the design, construction, and validation of an open-source weather-mimicking terrarium system that simulates highland cloud forest climates using real-time meteorological data. The system ingests current weather conditions from four Colombian highland cities (1,300–2,600 m elevation) and applies a 15-hour time shift to generate continuously varying temperature and humidity setpoints, reproducing the stochastic weather dynamics of tropical montane environments within a 1.5 x 0.6 x 1.1 m acrylic enclosure. A dynamic photoperiod derived from the Colombian reference latitude (~5 deg N) provides seasonally varying day length. The control system — built entirely on open-source software (Node-RED, InfluxDB, Grafana) running on a Raspberry Pi with an Arduino Mega for hardware I/O — implements a three-regime fan control strategy that switches between humidity-driven and temperature-driven PID control depending on thermal conditions, and a wet-bulb temperature gate that automatically disengages ventilation fans when evaporative cooling becomes thermodynamically counterproductive. The system has operated continuously for over three years with minimal human intervention, maintaining conditions suitable for approximately 120 cloud forest species from five continents. All design files, control flows, firmware, dashboards, and analysis scripts are provided under the CERN Open Hardware Licence. Companion publications describe the horticultural results for carnivorous plants [ref] and orchids [ref].

**Keywords**: open-source hardware, cloud forest terrarium, weather simulation, PID control, wet-bulb temperature, Node-RED, environmental monitoring, Raspberry Pi

---

## 1. Hardware in Context

Highland cloud forests — particularly the tepui table-top mountains of the Guiana Highlands in Venezuela — harbor extraordinary plant diversity adapted to narrow environmental envelopes: cool temperatures (10–22 deg C), persistent high humidity (80–100% RH), frequent fog immersion, and moderate light filtered through clouds [1]. Cultivating these species outside their native range presents formidable challenges, especially in climates with hot, dry summers.

Traditional terrarium controllers rely on fixed environmental setpoints (e.g., 18 deg C day / 14 deg C night, 90% RH constant), which fail to capture the stochastic variability that characterizes cloud forest environments. Natural tepui climates exhibit weather-driven fluctuations: sudden temperature drops during rain events, diurnal fog cycles, and seasonal variation in cloud cover. Static control oversimplifies the environment and may fail to provide the thermal and humidity cues that cloud forest species require for phenological processes.

Commercial terrarium controllers such as the MistKing HygroStat and similar products provide basic hysteresis control of humidity and temperature, but none ingest real-time weather data to produce dynamic setpoints. At the other end of the spectrum, laboratory growth chambers (Percival, Conviron) offer precise environmental control at costs of EUR 10,000–50,000+, with proprietary software that limits customization and data access.

In the open-source domain, several environmental control systems have been described in HardwareX and similar venues, including greenhouse automation platforms and plant growth monitoring systems. However, to our knowledge, no published open-source system implements weather-mimicking control — the ingestion of real-time meteorological data to drive continuously varying environmental setpoints — for terrarium-scale applications.

The system described here addresses this gap through five key innovations:

1. **Weather-mimicking from real meteorological data**: Real-time data from four Colombian highland cities generates stochastic, continuously varying setpoints that reproduce natural weather dynamics, including rain events and seasonal variation.

2. **Three-regime PID fan control**: The controller adapts its error signal based on temperature: humidity-driven below 24 deg C, temperature-driven in a 24–25 deg C transition band to attempt evaporative cooling before compressor activation, and humidity-driven with active refrigeration above 25 deg C.

3. **Wet-bulb temperature insight**: Automated detection and response to the thermodynamic limit of evaporative cooling, disengaging ventilation fans when the terrarium temperature falls below the room's wet-bulb temperature.

4. **Dynamic photoperiod**: Day length computed daily from the weather source latitude, providing seasonally varying light schedules coherent with the weather data.

5. **Complete open-source stack**: All hardware and software components use freely available, commodity parts, making the system reproducible by hobbyists and small institutions.

---

## 2. Hardware Description

The Weather-Mimicking Biotope (WMB) is an acrylic terrarium with integrated cooling, humidification, lighting, and ventilation, controlled by a Raspberry Pi running Node-RED with an Arduino Mega for hardware I/O. The system continuously adjusts environmental conditions based on real-time weather data from Colombian highland cities, simulating the stochastic climate of tropical cloud forests.

Applications for researchers and educators include:

- **Ex-situ conservation**: Maintaining cloud forest species from multiple biogeographic regions in a single enclosure, validated over 3+ years with ~120 species from five continents
- **Plant physiology studies**: Comprehensive data logging (32 InfluxDB measurements at 60-second intervals) enables analysis of plant responses to naturalistic environmental variation
- **Control systems education**: The system demonstrates PID control, gain scheduling, hysteresis control, wet-bulb thermodynamics, and multi-regime switching in an accessible, visual programming environment (Node-RED)
- **Template for other biomes**: The weather-mimicking architecture can be adapted to any biome by changing the reference weather stations (e.g., fog desert, alpine, lowland tropical)
- **Low-cost alternative to growth chambers**: Total hardware cost is a fraction of commercial growth chambers, with comparable or superior environmental control for this application

---

## 3. Design Files Summary

| File name | File type | Open-source license | Location |
|---|---|---|---|
| `flows-sanitized.json` | Node-RED flow configuration | CERN-OHL-P-2.0 | `[PLACEHOLDER — Zenodo DOI]` |
| `arduino-terrarium.ino` | Arduino Mega firmware (C++) | CERN-OHL-P-2.0 | `[PLACEHOLDER — Zenodo DOI]` |
| `grafana/*.json` | Grafana dashboard exports (4 dashboards) | CERN-OHL-P-2.0 | `[PLACEHOLDER — Zenodo DOI]` |
| `arduino-watchdog.sh` | Serial watchdog script (Bash) | CERN-OHL-P-2.0 | `[PLACEHOLDER — Zenodo DOI]` |
| `arduino-watchdog.service` | Systemd service for watchdog | CERN-OHL-P-2.0 | `[PLACEHOLDER — Zenodo DOI]` |
| `meross_script.py` | Power monitoring script (Python) | CERN-OHL-P-2.0 | `[PLACEHOLDER — Zenodo DOI]` |
| `schema.md` | InfluxDB measurement schema (32 measurements) | CERN-OHL-P-2.0 | `[PLACEHOLDER — Zenodo DOI]` |
| `architecture.md` | System architecture documentation | CERN-OHL-P-2.0 | `[PLACEHOLDER — Zenodo DOI]` |
| `pid-controller.md` | PID algorithm documentation | CERN-OHL-P-2.0 | `[PLACEHOLDER — Zenodo DOI]` |
| `statistical-analysis/*.py` | Analysis scripts (OLS, IV/2SLS, wet-bulb) | CERN-OHL-P-2.0 | `[PLACEHOLDER — Zenodo DOI]` |
| `S6-panel-drawings-*.docx` | Acrylic panel technical drawings | CERN-OHL-P-2.0 | `[PLACEHOLDER — Zenodo DOI]` |

**flows-sanitized.json**: Complete Node-RED flow configuration (~435 nodes across 7 tabs) with credentials removed. Covers all control logic: weather integration, PID fan control, three-regime switching, wet-bulb gate, dynamic photoperiod, door safety, mister hysteresis, data logging, and dashboard UI.

**arduino-terrarium.ino**: Custom text-based serial protocol firmware for Arduino Mega 2560. Handles PWM output on 5 channels (25 kHz phase-correct on Timers 1 and 5), door reed switch inputs with interrupt-based reading, heartbeat generation, and status reporting.

**Grafana dashboards**: Four monitoring dashboards — primary operational (temperature, humidity, VPD, actuator status), Colombian weather reference, system performance (PID diagnostics, fan PWM), and A/B experiment historical reference.

**arduino-watchdog.sh**: Watchdog v10 script monitoring USB connection health at 15-second intervals with four-step health checks and USB sysfs reset recovery.

**Acrylic panel drawings**: Original fabrication specifications for all structural panels (20 panels + 6 triangles + 2022 add-on set) with dimensions, hole positions, and material callouts.

---

## 4. Bill of Materials

### 4.1 Control Electronics

| Component | Qty | Description | Unit cost | Total cost | Source | Material type |
|---|---|---|---|---|---|---|
| Raspberry Pi 4 Model B (4 GB) | 1 | Main controller | `[PLACEHOLDER]` | `[PLACEHOLDER]` | `[PLACEHOLDER]` | Electronics |
| Arduino Mega 2560 (clone, CP210x USB) | 1 | GPIO interface | `[PLACEHOLDER]` | `[PLACEHOLDER]` | `[PLACEHOLDER]` | Electronics |
| ESP8266 (NodeMCU or generic) | 1 | Sensor data acquisition | `[PLACEHOLDER]` | `[PLACEHOLDER]` | `[PLACEHOLDER]` | Electronics |
| Sensirion SHT35 breakout | 1 | Temperature/humidity sensor | `[PLACEHOLDER]` | `[PLACEHOLDER]` | `[PLACEHOLDER]` | Electronics |
| HC-SR04P ultrasonic sensor | 1 | Water level monitoring | `[PLACEHOLDER]` | `[PLACEHOLDER]` | `[PLACEHOLDER]` | Electronics |
| IRF520N MOSFET driver module | 4 | Fan power switching | `[PLACEHOLDER]` | `[PLACEHOLDER]` | `[PLACEHOLDER]` | Electronics |
| Magnetic reed switch | 2 | Door sensors | `[PLACEHOLDER]` | `[PLACEHOLDER]` | `[PLACEHOLDER]` | Electronics |
| TP-Link Tapo P100 smart plug | 3 | Mains switching (lights, mister, compressor) | `[PLACEHOLDER]` | `[PLACEHOLDER]` | `[PLACEHOLDER]` | Electronics |
| Meross MSS310 smart plug | 1 | Energy monitoring | `[PLACEHOLDER]` | `[PLACEHOLDER]` | `[PLACEHOLDER]` | Electronics |
| MicroSD card (32 GB+) | 1 | Pi storage | `[PLACEHOLDER]` | `[PLACEHOLDER]` | `[PLACEHOLDER]` | Electronics |
| USB hub (powered) | 1 | Arduino + ESP connections | `[PLACEHOLDER]` | `[PLACEHOLDER]` | `[PLACEHOLDER]` | Electronics |

### 4.2 Lighting

| Component | Qty | Description | Unit cost | Total cost | Source | Material type |
|---|---|---|---|---|---|---|
| ChilLED Logic Puck V3 (100 W) | 4 | LED grow light modules (244x Samsung LM301B) | `[PLACEHOLDER]` | `[PLACEHOLDER]` | `[PLACEHOLDER]` | Electronics |
| 140 mm aluminium pin heatsink | 4 | Passive thermal management | `[PLACEHOLDER]` | `[PLACEHOLDER]` | `[PLACEHOLDER]` | Metal |
| 12 V axial fan (heatsink cooling) | 4 | Convective heatsink cooling | `[PLACEHOLDER]` | `[PLACEHOLDER]` | `[PLACEHOLDER]` | Electronics |
| Mean Well HLG-480H-48A LED driver | 1 | 480 W, 48 V / 10 A, IP65 | `[PLACEHOLDER]` | `[PLACEHOLDER]` | `[PLACEHOLDER]` | Electronics |

### 4.3 Cooling

| Component | Qty | Description | Unit cost | Total cost | Source | Material type |
|---|---|---|---|---|---|---|
| Vitrifrigo ND50 OR2-V compressor unit | 1 | BD50F Danfoss variable-speed, R404a | `[PLACEHOLDER]` | `[PLACEHOLDER]` | `[PLACEHOLDER]` | Mechanical |
| Vitrifrigo PT14 evaporator plate | 1 | 1220 x 280 mm stainless steel | `[PLACEHOLDER]` | `[PLACEHOLDER]` | `[PLACEHOLDER]` | Metal |
| Noctua NF-F12 iPPC-2000 IP67 (120 mm, 2000 RPM, 12 V) | 5 | Evaporator plate fans (x3) + circulation fans (x2) | `[PLACEHOLDER]` | `[PLACEHOLDER]` | `[PLACEHOLDER]` | Electronics |
| Noctua 60 mm fan | 2 | Outlet fan (x1) + impeller fan (x1) | `[PLACEHOLDER]` | `[PLACEHOLDER]` | `[PLACEHOLDER]` | Electronics |
| Noctua NF-A12x25 G2 PWM (120 mm, 12 V) | 2 | Condenser radiator fans in push-pull configuration | `[PLACEHOLDER]` | `[PLACEHOLDER]` | `[PLACEHOLDER]` | Electronics |
| Plexiglas plate | 1 | Evaporator airflow plate, inclined 30 deg with slit below | `[PLACEHOLDER]` | `[PLACEHOLDER]` | `[PLACEHOLDER]` | Plastic |

### 4.4 Humidification

| Component | Qty | Description | Unit cost | Total cost | Source | Material type |
|---|---|---|---|---|---|---|
| MistKing Standard diaphragm pump (24 V) | 1 | Misting system pump | `[PLACEHOLDER]` | `[PLACEHOLDER]` | `[PLACEHOLDER]` | Mechanical |
| MistKing nozzle assemblies | ~20 | Quad (x1), double (x6), single (x4) | `[PLACEHOLDER]` | `[PLACEHOLDER]` | `[PLACEHOLDER]` | Plastic/metal |
| ZipDrip anti-drip valve | 1 | Prevents residual dripping | `[PLACEHOLDER]` | `[PLACEHOLDER]` | `[PLACEHOLDER]` | Plastic |
| Tubing and fittings | 1 set | MistKing-compatible | `[PLACEHOLDER]` | `[PLACEHOLDER]` | `[PLACEHOLDER]` | Plastic |

### 4.5 Ventilation

| Component | Qty | Description | Unit cost | Total cost | Source | Material type |
|---|---|---|---|---|---|---|
| 12 V fans (outlet + impeller) | 2 | Rear ventilation port fans | `[PLACEHOLDER]` | `[PLACEHOLDER]` | `[PLACEHOLDER]` | Electronics |

### 4.6 Enclosure

| Component | Qty | Description | Unit cost | Total cost | Source | Material type |
|---|---|---|---|---|---|---|
| Clear acrylic (PMMA) 10 mm | ~2 m^2 | Floor, back wall, side panels, inner back | `[PLACEHOLDER]` | `[PLACEHOLDER]` | `[PLACEHOLDER]` | Plastic |
| Clear acrylic (PMMA) 8 mm | ~1 m^2 | Sliding doors, shelf, support tracks | `[PLACEHOLDER]` | `[PLACEHOLDER]` | `[PLACEHOLDER]` | Plastic |
| Clear acrylic (PMMA) 5 mm | ~0.5 m^2 | Shelf lips, brackets, triangles | `[PLACEHOLDER]` | `[PLACEHOLDER]` | `[PLACEHOLDER]` | Plastic |
| Silver mirror acrylic 2 mm | ~0.5 m^2 | Reflective panels (x5 + add-ons) | `[PLACEHOLDER]` | `[PLACEHOLDER]` | `[PLACEHOLDER]` | Plastic |
| Black acrylic 4 mm | ~0.5 m^2 | Light-blocking baffles (add-on set) | `[PLACEHOLDER]` | `[PLACEHOLDER]` | `[PLACEHOLDER]` | Plastic |
| Perforated acrylic (Square 15) 3 mm | ~0.5 m^2 | Ventilation grilles, shelf floor | `[PLACEHOLDER]` | `[PLACEHOLDER]` | `[PLACEHOLDER]` | Plastic |
| XPS insulation (1 cm) | ~2 m^2 | Exterior thermal insulation | `[PLACEHOLDER]` | `[PLACEHOLDER]` | `[PLACEHOLDER]` | Foam |
| Diamond Mylar reflective sheeting | ~2 m^2 | Laminated to XPS insulation | `[PLACEHOLDER]` | `[PLACEHOLDER]` | `[PLACEHOLDER]` | Plastic/foil |
| Dichloromethane (DCM) | ~100 mL | Solvent welding (use with ventilation!) | `[PLACEHOLDER]` | `[PLACEHOLDER]` | `[PLACEHOLDER]` | Chemical |
| Crystalline silicone sealant (c-Si) | 1 tube | Joint sealing (NOT acetoxy silicone) | `[PLACEHOLDER]` | `[PLACEHOLDER]` | `[PLACEHOLDER]` | Chemical |
| Aluminium alloy scaffold | 1 | 2.20 x 3.20 x 0.50 m, ~300 kg | `[PLACEHOLDER]` | `[PLACEHOLDER]` | `[PLACEHOLDER]` | Metal |
| Aluminium alloy guides | 2 | Sliding door tracks | `[PLACEHOLDER]` | `[PLACEHOLDER]` | `[PLACEHOLDER]` | Metal |

### 4.7 Reservoirs and Plumbing

| Component | Qty | Description | Unit cost | Total cost | Source | Material type |
|---|---|---|---|---|---|---|
| 40-liter reservoir | 2 | Misting supply + condensate collection | `[PLACEHOLDER]` | `[PLACEHOLDER]` | `[PLACEHOLDER]` | Plastic |

`[PLACEHOLDER — user to verify all quantities, add any missing components, and fill in costs and supplier links]`

---

## 5. Build Instructions

### 5.1 Enclosure Construction

#### 5.1.1 Material Selection and Cutting

Select acrylic (PMMA) as the enclosure material based on its superior transparency, low weight, ease of modification, and lower cost compared to tempered glass or polycarbonate. Order laser-cut panels according to the specifications in the Design Files (panel drawings). Laser cutting is strongly recommended over circular-saw cutting, as the edge smoothness is critical for successful solvent welding.

Material properties comparison:

| Property | Tempered Glass | Polycarbonate | Acrylic (PMMA) |
|----------|---------------|---------------|----------------|
| Transparency | Good | ~88% | Highest |
| Thermal conductivity | Variable | 0.19–0.22 W/mK | 0.19–0.22 W/mK |
| Impact resistance | Low | Excellent (200x glass) | Moderate |
| Weight | Heaviest | Medium | Lightest |
| Machinability | Non-drillable | Easy | Easy |
| Fire resistance | Fireproof | Good | Combustible |
| UV/yellowing | Good | Yellows over time | Good long-term |
| Cost | Highest | Medium | Lowest |

#### 5.1.2 Panel Fabrication

The enclosure requires 20 laser-cut panels plus 6 structural triangles (see Design Files S6 for full specifications). The main structural panels are:

- **Floor** (1x): 145 x ~55 cm, 10 mm clear acrylic
- **Back wall** (1x): 145 x ~115 cm, 10 mm clear acrylic, with 2x 12 cm ventilation holes and 2x 2 cm cable pass-throughs
- **Inner back / shelf support** (1x): 145 x 115 cm, 10 mm clear acrylic
- **Side panels** (2x): 49 x 115 cm, 10 mm clear acrylic, with notches for door guides and ventilation holes
- **Sliding front doors** (2x): 73.5 x 94.6 cm, 8 mm clear acrylic
- **Bottom rails** (2x): 145 x 10 cm, 20 mm clear acrylic

Internal components include perforated shelf panels (8 mm, Square 15 pattern), shelf support brackets (5 mm), and corner reinforcement triangles (5 mm). Reflective panels (2 mm silver mirror acrylic) and the 2022 add-on set (black light baffles, additional perforated grilles) complete the panel set.

#### 5.1.3 Assembly

1. **Dry-fit all panels** to verify dimensions before solvent welding. Laser-cut edges should mate precisely.

2. **Solvent weld using dichloromethane (DCM)**:
   - Work in a well-ventilated area. DCM is volatile and toxic (possible carcinogen).
   - Apply DCM to the joint with a syringe or applicator bottle — capillary action draws it into the seam.
   - The weld sets within seconds and produces a monolithic bond.
   - **Critical**: DCM permanently stains acrylic on contact. Protect all visible surfaces with masking tape.

3. **Seal joints with crystalline silicone (c-Si)** after DCM welding for watertightness. **Never use acetoxy silicone (a-Si)** — it releases acetic acid that corrodes and permanently stains acrylic.

4. **Flood test**: Fill the completed enclosure with ~30 liters of water and leave for one week to verify watertightness before installing any hardware.

5. **Apply exterior insulation**: Laminate 1 cm XPS panels with diamond Mylar reflective sheeting and attach to the exterior of the back wall, side panels, and floor. Exterior placement leaves interior surfaces smooth for cleaning and maximizes usable volume.

6. **Install sliding door guides**: Attach aluminium alloy guides with c-Si adhesive for the two front sliding panels.

`[PLACEHOLDER — step-by-step assembly photos]`

#### 5.1.4 Drainage

Tilt the floor panel slightly toward a rear drainage hole. The shelf below the terrarium hosts three items: the MistKing diaphragm pump, a 40-liter water reservoir feeding the pump, and a 40-liter condensate collection tank receiving gravity drainage from the evaporator plate above.

### 5.2 Hardware Assembly

#### 5.2.1 Lighting Installation

1. Mount four ChilLED Logic Puck V3 modules on 140 mm aluminium pin heatsinks above the terrarium enclosure. The pucks and heatsinks reside above the enclosure so their thermal output does not contribute to the internal heat load.

2. Mount 12 V axial fans above each heatsink for supplementary convective cooling.

3. Wire the four pucks in parallel to the Mean Well HLG-480H-48A LED driver (480 W, 48 V / 10 A, IP65).

4. Adjust the Mean Well driver's internal potentiometer to limit maximum output to approximately 60% of rated power. This hardware ceiling provides a fail-safe: even if the software erroneously commands 100% brightness, the LEDs cannot exceed ~60%, protecting shade-adapted species.

5. Connect the driver's analog dimming input to the Arduino's PWM pin 8. Note that lower PWM values produce brighter output (the driver dims proportionally to the PWM signal).

6. Wire the driver's mains input through a TP-Link Tapo P100 smart plug (for on/off scheduling).

#### 5.2.2 Cooling System Installation

The Vitrifrigo ND50 is a split-system marine refrigeration unit: the compressor and condenser are mounted external to the cooled space, with refrigerant lines connecting them to a separate evaporator plate inside. Installation places the compressor unit above the terrarium and the evaporator plate horizontally inside the upper region of the enclosure, with refrigerant lines passing through a sealed pass-through in the top panel. This is mechanical refrigeration — not evaporative cooling.

1. Place the Vitrifrigo ND50 OR2-V compressor unit on a frame or shelf above the terrarium, with adequate clearance for the condenser radiator and fans to exhaust heat away from the enclosure.

2. Mount the Vitrifrigo PT14 evaporator plate horizontally inside the terrarium, near the top of the enclosure. Route the refrigerant lines from the compressor down through a sealed pass-through in the top panel to the evaporator. Ensure the evaporator's condensate drain leads, via gravity, to the condensate reservoir on the shelf below the terrarium.

3. Mount a plexiglas baffle below the evaporator plate, inclined approximately 30 deg from horizontal. Leave a slit between one edge of the baffle and the enclosure wall so that the cold (and therefore dense) air sinking off the evaporator is channeled downward through the slit and distributed into the lower zones.

4. Evenly space three Noctua NF-F12 iPPC-2000 IP67 fans on the plexiglas baffle, oriented to draw warm interior air upward against the underside of the evaporator surface.

5. Mount two additional Noctua NF-F12 iPPC-2000 IP67 fans separately for general internal circulation.

6. Mount two Noctua NF-A12x25 G2 fans in push-pull configuration on the compressor's condenser radiator fins (not Arduino-controlled; these run whenever the compressor unit is powered).

7. Wire the compressor's mains input through a TP-Link Tapo P100 smart plug (for on/off control).

#### 5.2.3 Humidification System Installation

1. Install the MistKing Standard pump below the terrarium, connected to the 40-liter misting reservoir.

2. Route MistKing tubing through a cable pass-through to the terrarium ceiling.

3. Install the nozzle array: one quad-nozzle assembly, six double-nozzle assemblies, and four single nozzles distributed across the ceiling for even fog coverage (~20 nozzle points total).

4. Install a ZipDrip anti-drip valve on the main supply line.

5. Wire the MistKing pump's power through a TP-Link Tapo P100 smart plug (for on/off control).

#### 5.2.4 Fan Wiring

Wire each fan group through an IRF520N MOSFET driver module:

| Fan group | MOSFET gate → Arduino pin | Fan supply voltage | Purpose |
|---|---|---|---|
| Evaporator fans (3x Noctua NF-F12 iPPC-2000) | Pin 44 (Timer 5) | 12 V | Airflow across evaporator plate |
| Outlet fan (Noctua 60 mm) | Pin 45 (Timer 5) | 12 V | Exhaust humid air |
| Impeller fan (Noctua 60 mm) | Pin 46 (Timer 5) | 12 V | Draw external air in |
| Circulation fans (2x Noctua NF-F12 iPPC-2000) | Pin 12 (Timer 1) | 12 V | Internal air movement |

**Important**: Do not connect the Arduino PWM output to the fans' 4-pin PWM inputs when driving multiple fans per channel. The MOSFET module switches the power rail instead, eliminating inter-fan signal interference. For single-fan configurations, direct 4-pin PWM connection with a 220 ohm series resistor per fan is acceptable.

#### 5.2.5 Sensor Installation

1. Connect the SHT35 sensor to the ESP8266. Position the sensor at mid-canopy height (~50 cm above floor), roughly centered in the enclosure.

2. Mount the HC-SR04P ultrasonic sensor above the misting reservoir for water level monitoring.

3. Wire two magnetic reed switches to Arduino digital inputs D22 (left door) and D24 (right door) — the Arduino's internal pull-up resistors are enabled in firmware.

### 5.3 Electronics Wiring

#### 5.3.1 Arduino Mega Pin Assignments

| Pin | Type | Function | Notes |
|---|---|---|---|
| 8 | PWM output | Light dimmer | Standard PWM; lower value = brighter |
| 12 | PWM output | Circulation fans | Timer 1, 25 kHz phase-correct (OC1B) |
| 44 | PWM output | Evaporator fans | Timer 5, 25 kHz phase-correct (OC5C) |
| 45 | PWM output | Outlet fan | Timer 5, 25 kHz phase-correct (OC5B) |
| 46 | PWM output | Impeller fan | Timer 5, 25 kHz phase-correct (OC5A) |
| A0 | Analog input | Heartbeat signal | Watched by serial watchdog |
| D22 | Digital input | Left door reed switch | INPUT_PULLUP |
| D24 | Digital input | Right door reed switch | INPUT_PULLUP |

#### 5.3.2 Power Distribution

- **Mains (230 V AC)**: Through 3x Tapo P100 smart plugs → LED driver, MistKing pump, compressor
- **48 V DC**: Mean Well driver → 4x ChilLED pucks
- **24 V DC**: Separate supply → Noctua fans (via MOSFET modules), MistKing pump
- **12 V DC**: Separate supply → Outlet/impeller fans (via MOSFET modules), heatsink fans
- **5 V DC**: Raspberry Pi USB → Arduino Mega, ESP8266

**Safety**: All electrical lines running near or above the terrarium must incorporate drip loops (U-shaped cable routing below connection points) to prevent water ingress.

`[PLACEHOLDER — wiring diagram/schematic]`

### 5.4 Software Installation

#### 5.4.1 Raspberry Pi Setup

1. Install Raspberry Pi OS (Debian-based, ARMv8) on a MicroSD card.

2. Install Node-RED v3.x:
   ```
   bash <(curl -sL https://raw.githubusercontent.com/node-red/linux-installers/master/deb/update-nodejs-and-nodered)
   ```
   Enable the systemd service:
   ```
   sudo systemctl enable nodered
   ```

3. Install InfluxDB v1.8:
   ```
   sudo apt install influxdb
   ```
   Create the database:
   ```
   influx -execute "CREATE DATABASE highland"
   influx -execute "CREATE RETENTION POLICY standard_highland_retention ON highland DURATION 365d REPLICATION 1 DEFAULT"
   ```

4. Install Grafana:
   ```
   sudo apt install grafana
   sudo systemctl enable grafana-server
   ```

5. Install Mosquitto MQTT broker:
   ```
   sudo apt install mosquitto mosquitto-clients
   ```

6. Install Node-RED dependencies (from the Node-RED palette manager or command line):
   - `node-red-contrib-influxdb`
   - `node-red-dashboard`
   - `node-red-contrib-dynamic-dimmer`
   - `node-red-node-serialport`
   - `node-red-contrib-sun-position`

7. Install Python dependencies for Tapo P100 control:
   ```
   pip3 install PyP100
   ```

#### 5.4.2 Udev Rules

Create `/etc/udev/rules.d/99-arduino.rules` to create stable device symlinks:

```
SUBSYSTEM=="tty", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="ea60", SYMLINK+="arduino"
SUBSYSTEM=="tty", ATTRS{idVendor}=="1a86", ATTRS{idProduct}=="7523", SYMLINK+="esp32"
```

Reload:
```
sudo udevadm control --reload-rules && sudo udevadm trigger
```

### 5.5 Node-RED Flow Import and Configuration

1. Open the Node-RED editor (http://<pi-ip>:1880).

2. Import `flows-sanitized.json` via Menu → Import.

3. Configure credentials in the following nodes:
   - **Tapo P100 Python function nodes** (3x): Set IP addresses, email, and password for each smart plug
   - **OpenWeatherMap nodes**: Insert your API key
   - **Meross Python function node**: Set cloud credentials for power monitoring

4. Configure the serial port node to use `/dev/arduino` at 115200 baud.

5. Configure the MQTT nodes to connect to `localhost:1883`.

6. Deploy the flows.

### 5.6 Arduino Firmware Upload

1. Install the Arduino CLI:
   ```
   curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | sh
   arduino-cli core install arduino:avr
   ```

2. Upload the firmware:
   ```
   arduino-cli upload -p /dev/arduino --fqbn arduino:avr:mega -i arduino-terrarium.ino
   ```

   The firmware implements:
   - 25 kHz phase-correct PWM on Timer 1 (pin 12) and Timer 5 (pins 44, 45, 46)
   - Text-based serial protocol: `P<pin>,<val>` (PWM), `Q` (query), `H,<val>` (heartbeat), `D<pin>,<0|1>` (doors)
   - PWM zero fix: disconnects output compare register and drives pin LOW when value=0 to prevent MOSFET ghost pulses
   - Heartbeat generation on A0 for watchdog monitoring

### 5.7 Grafana Dashboard Import

1. Open Grafana (http://<pi-ip>:3000, default admin/admin).
2. Add InfluxDB as a data source: URL `http://localhost:8086`, database `highland`.
3. Import each dashboard JSON from the `grafana/` directory.

### 5.8 Watchdog Installation

1. Copy `arduino-watchdog.sh` to `/usr/local/bin/` and make executable.
2. Copy `arduino-watchdog.service` to `/etc/systemd/system/`.
3. Enable and start:
   ```
   sudo systemctl enable arduino-watchdog
   sudo systemctl start arduino-watchdog
   ```

`[PLACEHOLDER — step-by-step photos of assembly process]`

---

## 6. Operation Instructions

### 6.1 First Start and Calibration

1. Verify all Tapo P100 smart plugs are reachable on the network and controllable from Node-RED.

2. Verify the Arduino serial connection: the "Heartbeat" debug node in the Utilities tab should show periodic values.

3. Verify the SHT35 sensor publishes MQTT data: check the Humidity tab for incoming readings.

4. Fill the misting reservoir to capacity and verify the water level reading on the Dashboard.

5. Adjust the Mean Well driver potentiometer:
   - Set the Node-RED slider to 100%.
   - Observe light output and adjust the potentiometer screw until output is approximately 60% of maximum. This is a subjective assessment based on the light requirements of the most shade-sensitive species.

6. Verify fan operation: manually set each fan channel to test PWM values via the Dashboard and confirm rotation.

7. Set the OpenWeatherMap API key and verify weather data appears in the Weather tab.

### 6.2 Daily Operation

Under normal operation, the system requires no human intervention. The automated cycle includes:

- **Weather polling**: Current conditions fetched from four Colombian cities and heavily smoothed (15-minute rolling mean) into temperature/humidity setpoints. The 15-hour data buffer makes aggressive smoothing cost-free. If the API is unreachable, the system falls back to a smoothed 14-day historical daily curve.
- **Photoperiod calculation**: Day length computed daily from the Chinchina latitude; light on/off times, ramp schedules, and midday boost derived and executed automatically.
- **PID fan control**: Humidity or temperature error (depending on regime) drives outlet and impeller fan speed continuously.
- **Mister control**: Hysteresis controller fires the mister when humidity drops below the lower threshold, with automatic fan shutdown during misting events.
- **Compressor control**: Hysteresis controller activates the compressor when temperature exceeds 25 deg C (daytime) or the weather-capped target (nighttime).
- **Wet-bulb gate**: After 18:00, outlet and impeller fans shut down when the terrarium temperature falls to or below the room's wet-bulb temperature.
- **Data logging**: 16 measurements recorded every 60 seconds, plus event-driven fan PWM changes and other measurements (32 total).

### 6.3 Dashboard Monitoring

**Node-RED Dashboard** (http://<pi-ip>:1880/ui): Real-time gauges for temperature, humidity, VPD, fan speed, and actuator states. Manual override controls. Mist counter. Water level.

**Grafana** (http://<pi-ip>:3000): Historical charts with configurable time ranges. Four dashboards cover operational monitoring, weather reference, system performance, and experimental data.

### 6.4 Maintenance

- **Water refills**: Monitor the water level gauge on the Dashboard. Refill the misting reservoir when it drops below ~20%. The ultrasonic sensor provides the low-water alert.
- **Sensor cleaning**: The SHT35 sensor may accumulate mineral deposits from misting. Clean periodically with distilled water.
- **Condensate reservoir**: Empty when needed (overflow is not harmful but creates mess).
- **Door safety**: When opening the terrarium for maintenance, the door safety system automatically stops fans, compressor, and mister, and sets lights to 60% for working illumination. All systems restore when doors close.

### 6.5 Troubleshooting

| Symptom | Likely cause | Resolution |
|---|---|---|
| No fan response to PID | Serial stall | Wait ~15–30 s for watchdog auto-recovery; check watchdog service status |
| Fans spinning at PWM 0 | AVR phase-correct PWM ghost pulse | Verify firmware includes the PWM zero fix (output compare disconnect) |
| Weather data stale | API key expired or network issue | Check OpenWeatherMap API status; system falls back to 14-day historical curve automatically |
| Mister runs continuously | Tapo plug stuck or humidity sensor fault | Mister cron failsafe forces Tapo OFF after 150 s; check sensor readings |
| Temperature climbing despite compressor | Compressor Tapo plug unreachable | Check WiFi connectivity of plug at 192.168.1.196 |
| "Serial port not open" errors | USB disconnect | Watchdog performs USB sysfs reset; recovery takes ~15–30 s |

### 6.6 Safety Considerations

- **Electrical safety with water**: All mains wiring must use drip loops. Smart plugs and power supplies should be positioned where they cannot be splashed. The IP65-rated Mean Well driver provides moisture protection for the LED driver.
- **DCM handling**: Dichloromethane is volatile and toxic. Use only in well-ventilated areas during construction.
- **Compressor refrigerant**: R404a handling requires professional certification in many jurisdictions. The Vitrifrigo unit comes factory-sealed and should not require user intervention.
- **Mister failsafe**: A cron-based Python script (`mister-failsafe.py`) runs every minute and forces the mister Tapo plug OFF if the on-time exceeds 150 seconds, preventing water damage from a stuck-on mister.

---

## 7. Validation and Characterization

### 7.1 Environmental Performance

Over the monitoring period, the system maintained the following environmental ranges:

| Parameter | Minimum | Maximum | Typical range | Target range |
|---|---|---|---|---|
| Temperature | 13.5 deg C | 24.3 deg C | 15–22 deg C | Weather-derived (clamped 12–24 deg C) |
| Relative humidity | 75% | 98% | 82–95% | Weather-derived (clamped 70–90%) |
| VPD | 0.03 kPa | 0.64 kPa | 0.08–0.45 kPa | < 0.8 kPa |

The system achieves a meaningful diurnal temperature swing despite the terrarium being located in a room at approximately 22 deg C year-round. Nighttime terrarium temperatures routinely drop to 14–16 deg C through active compressor cooling, while daytime temperatures rise to 18–22 deg C, producing a 4–8 deg C daily amplitude that approximates conditions on mid-elevation tepuis.

`[PLACEHOLDER — Grafana screenshots showing representative 24-hour and 7-day temperature/humidity cycles]`

### 7.2 PID Controller Stability

The gain-scheduled PID controller maintains humidity within +/-3% RH of the setpoint under steady-state conditions, producing smooth fan speed transitions that eliminate the continuous cycling characteristic of simpler hysteresis controllers.

The gain scheduling was critical: with fixed gains, the controller exhibited rapid +/-25 PWM oscillations near the setpoint. After implementing gain scheduling — effective Kp = 7.5 within +/-1.5% of target, full Kp = 50 for errors >= 4% — these oscillations were eliminated.

An IV/2SLS analysis using a controlled A/B experiment (alternating nightly fan-on/fan-off) as an instrument confirmed the fans' causal effect on humidity: each +10 PWM of fan speed causes a -0.37% reduction in humidity (p < 0.05). The compressor is the dominant cooling and dehumidification actuator (-15.9% humidity long-run effect when active), with the PID fans providing fine-tuning within the compressor's hysteresis band.

`[PLACEHOLDER — Grafana screenshot showing PID response to a humidity disturbance]`

### 7.3 Three-Regime Fan Control

The three-regime strategy (Section 6.2) transitions smoothly between humidity-driven and temperature-driven control:

- **Normal regime** (< 24 deg C): PID drives fans based on humidity error. This is the predominant operating mode during most of the year.
- **Warm regime** (24–25 deg C, compressor off): PID switches to temperature error scaled by TEMP_ERROR_SCALE = 5, mapping 0–1 deg C temperature excess to 0–5 PID-equivalent units. Fans ramp aggressively to attempt evaporative cooling.
- **Hot regime** (>= 25 deg C, compressor on): PID reverts to humidity error since the compressor now handles temperature.

Mode transitions reset the integral, derivative, and last-error state to prevent discontinuities. The current control mode is logged to InfluxDB (`pid_control_mode`: 0 = humidity, 1 = temperature) for analysis.

### 7.4 Wet-Bulb Temperature Analysis

Room sensor data reveals consistent room conditions of 22.1 +/- 0.7 deg C and 57.9 +/- 5.2% RH, corresponding to a room wet-bulb temperature of 16.6 +/- 0.9 deg C (Stull, 2011 formula). The terrarium temperature crosses below this wet-bulb threshold around 20:00–21:00 each evening as the compressor drives temperatures down.

A preliminary heat-balance regression decomposed actuator contributions to the terrarium's hourly temperature change:

| Actuator | Temperature effect | Interpretation |
|---|---|---|
| Freezer (compressor) | -2.03 deg C/hr | Dominant cooling mechanism |
| Fans (outlet + impeller) | +0.37 deg C/hr | Net warming (room air sensible heat) |
| Passive heat exchange | +0.58 deg C/hr | Room-to-terrarium heat transfer |

An extended model including the interaction between fan speed and temperature difference above wet-bulb reveals that the fan cooling effect diminishes linearly as the terrarium approaches wet-bulb, reaching zero at approximately T_above_wb = +0.3 deg C. Below this point, fans provide no evaporative cooling benefit and become a net heat source.

The wet-bulb temperature gate (Section 6.2) implements this finding operationally, disengaging outlet and impeller fans when the terrarium temperature falls to or below the room wet-bulb temperature after 18:00.

### 7.5 Weather Correlation

The Colombian weather integration produces continuously varying setpoints that reflect real meteorological conditions. The 15-hour time shift means that Colombian daytime conditions (16–22 deg C, 60–80% RH) map onto Italian nighttime, while Colombian nighttime conditions (12–16 deg C, 85–95% RH) map onto Italian daytime, producing a biologically desirable pattern mirroring the natural diurnal cycle of cloud forest environments.

The stochastic character of real weather data is a key advantage over fixed schedules. Rain events in Colombia produce corresponding setpoint changes, creating sudden environmental perturbations — simulated fog immersion events — that vary from day to day and season to season.

### 7.6 System Reliability

The primary reliability challenge is a recurring serial stall in which the Arduino's USB-to-serial bridge enters a stuck state, silently stopping all serial communication after variable periods. This appears to be a hardware-level issue related to the Raspberry Pi 4's internal USB hub rather than a protocol-level problem.

The watchdog v10 mitigates this by detecting absent heartbeat messages and performing a USB sysfs reset (toggling the `authorized` attribute), reducing recovery time to ~15–30 seconds. Between stall events, the system operates autonomously without human intervention. Weather fallback (a smoothed 14-day historical daily curve replaces flat defaults), door safety, and startup recovery mechanisms ensure graceful handling of connectivity outages, maintenance access, and reboots.

### 7.7 Power Consumption

Total system power consumption is monitored by a Meross MSS310 energy-monitoring smart plug, reporting instantaneous wattage every 2 minutes. `[PLACEHOLDER — typical power consumption data: idle, compressor active, misting, full cooling]`

### 7.8 Capabilities and Limitations

**Capabilities**:

- Maintains 13.5–24.3 deg C temperature range in a room at ~22 deg C
- Maintains 75–98% RH continuously
- Produces naturalistic, stochastic environmental variation from real weather data
- Dynamic photoperiod tracks the natural season at the weather source latitude
- Three-regime PID control provides smooth, stable humidity management
- Automatic wet-bulb temperature detection prevents counterproductive fan operation
- Door safety mode protects plants and equipment during maintenance
- Comprehensive data logging enables experimental analysis
- Startup recovery handles reboots during dimming ramps
- Serial watchdog provides automatic USB reset recovery

**Limitations**:

- Single-sensor system; spatial gradients are not characterized
- Internet-dependent weather data (degrades gracefully to a 14-day historical daily curve)
- Recurring USB-serial stalls require watchdog mitigation (~15–30 s recovery per event)
- Cloud-dependent power monitoring (Meross API)
- Cannot provide species-specific dry rest periods in a shared enclosure
- Acrylic enclosure is combustible (acceptable in indoor, supervised setting)
- The specific PID tuning values are enclosure-specific and would need retuning for different geometries

---

## References

[1] Rull, V., & Vegas-Vilarrúbia, T. (2006). Unexpected biodiversity loss under global warming in the neotropical Guayana Highlands: a preliminary appraisal. *Global Change Biology*, 12, 1–6.

[2] Berry, P. E., & Riina, R. (2005). Insights into the diversity of the Pantepui flora and the biogeographic complexity of the Guayana Shield. *Biologiske Skrifter*, 55, 145–167.

[3] Stull, R. (2011). Wet-Bulb Temperature from Relative Humidity and Air Temperature. *Journal of Applied Meteorology and Climatology*, 50(11), 2267–2269.

[4] Givnish, T. J., et al. (2014). Adaptive radiation, correlated and contingent evolution, and net species diversification in Bromeliaceae. *Molecular Phylogenetics and Evolution*, 71, 55–78.

[5] Node-RED Project. (2026). https://nodered.org/

[6] InfluxDB. (2026). https://www.influxdata.com/

[7] Grafana Labs. (2026). https://grafana.com/

`[PLACEHOLDER — add additional references as needed, especially: relevant HardwareX papers on environmental controllers, commercial growth chamber references, MistKing/Tapo product references]`

---

## Acknowledgments

`[PLACEHOLDER]`
