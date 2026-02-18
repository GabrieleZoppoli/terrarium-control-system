# Open-Source Climate Simulation for Highland Cloud Forest Terrariums: A Node-RED-Based Control System with PID Humidity Management and Colombian Weather Data Integration

**Authors**: `[PLACEHOLDER — author names and affiliations]`

**Corresponding author**: `[PLACEHOLDER — email]`

---

## Abstract

We present an open-source environmental control system for simulating highland cloud forest (tepui) climates within a closed terrarium, designed to maintain conditions suitable for approximately 120 plant species across genera including *Heliamphora*, *Dracula*, *Sophronitis*, *Nepenthes*, and highland *Dendrobium*. The system, built on the Node-RED visual programming platform with InfluxDB time-series storage and Grafana visualization, integrates real-time weather data from four Colombian highland cities to generate dynamic temperature and humidity setpoints with a 15-hour time shift. A gain-scheduled PID controller (Kp=50, Ki=0.5, Kd=10) modulates fan speed in response to humidity error, while a compact compressor-based refrigeration unit (Vitrifrigo ND50) provides active cooling. An Arduino Mega communicates via a custom text-based serial protocol, and door-mounted reed switches trigger a safety mode that protects both plants and equipment during maintenance. The system achieves typical conditions of 13.5–24.3°C and 75–98% relative humidity within a Mediterranean-climate room (Genoa, Italy) and has operated continuously for over two years with minimal human intervention, demonstrating that commodity hardware and open-source software can replicate challenging montane microclimates. All control flows, monitoring dashboards, and documentation are available as supplementary materials.

**Keywords**: cloud forest terrarium, environmental control, PID controller, Node-RED, tepui climate, vapor pressure deficit, open-source horticulture, gain scheduling

---

## 1. Introduction

Highland cloud forests, particularly the tepui table-top mountains of the Guiana Highlands in Venezuela, harbor extraordinary plant diversity adapted to narrow environmental envelopes: cool temperatures (10–22°C), persistent high humidity (80–100% RH), frequent fog immersion, and moderate light filtered through clouds (Rull & Vegas-Vilarrúbia, 2006). Cultivating these species outside their native range — especially in Mediterranean climates with hot, dry summers — presents formidable challenges for both botanical institutions and private growers.

Traditional terrarium approaches rely on fixed environmental setpoints (e.g., 18°C day / 14°C night, 90% RH constant), which fail to capture the dynamic variability that characterizes cloud forest environments. Natural tepui climates exhibit stochastic weather-driven fluctuations: sudden temperature drops during rain events, diurnal fog cycles, and seasonal variation in cloud cover. Static control not only oversimplifies the environment but may fail to provide the thermal and humidity cues that many cloud forest species require for phenological processes including flowering and seed set.

This paper describes an open-source control system that addresses these limitations through three key innovations:

1. **Weather-referenced setpoints**: Rather than programming fixed targets, the system ingests real-time meteorological data from four Colombian highland cities (Chinchiná, Medellín, Bogotá, Sonsón) at elevations of 1,300–2,600 m, applying a 15-hour time shift to align South American daytime weather with European nighttime conditions and vice versa. This produces naturalistic, continuously varying setpoints within biologically appropriate ranges.

2. **PID humidity management**: A proportional-integral-derivative controller modulates fan speed in response to the difference between target and actual humidity, providing smooth, responsive control that avoids the oscillation and hysteresis artifacts of simpler bang-bang approaches.

3. **Complete open-source stack**: Every component — from the control logic (Node-RED), to the time-series database (InfluxDB), to the monitoring dashboards (Grafana) — uses freely available, community-supported software running on a single Raspberry Pi. This makes the system reproducible by hobbyists and small institutions without proprietary hardware or licensing costs.

The system has maintained approximately 120 species from multiple cloud forest genera in a 1.5 × 0.6 × 1.1 m terrarium in Genoa, Italy for over two years, demonstrating long-term reliability and horticultural effectiveness.

---

## 2. Materials and Methods

### 2.1 Terrarium Construction

The current terrarium ("Version 2") is an evolution of an earlier, smaller enclosure ("Version 1"), both designed as weather-mimicking biotopes (WMBs) for highland cloud forest species. This section describes the physical construction of both iterations, with emphasis on the current system.

#### 2.1.1 Supporting Scaffold and Placement

The terrarium is placed in an area of the apartment that does not receive direct sunlight, avoiding solar heat gain that would increase cooling load and risk overheating during system failures. The supporting scaffold is a semi-industrial weatherproof aluminum alloy unit (2.20 m high × 3.20 m wide × 0.50 m deep, approximately 300 kg), chosen after experience with a wood scaffold for Version 1 that suffered waterproof coating degradation and swelling after four years. Aluminum alloy is preferred over wood for its corrosion resistance, non-combustibility, and structural rigidity, though it conducts electricity and provides limited thermal insulation. All electrical lines incorporate drip loops (U-shaped cable routing below connection points) to prevent water ingress to outlets, following standard aquarium practice.

#### 2.1.2 Choice of Enclosure Material

Three materials were evaluated for the enclosure: tempered glass, polycarbonate (Lexan), and polymethylmethacrylate (PMMA/acrylic, Plexiglas). The selection criteria included optical transparency, thermal conductivity (lambda-value), impact resistance, weight, machinability (drilling and cutting), chemical resistance, fire resistance, UV stability, and cost.

| Property | Tempered Glass | Polycarbonate | Acrylic (PMMA) |
|----------|---------------|---------------|----------------|
| Transparency | Good | ~88% | Highest |
| Thermal conductivity | Variable | 0.19–0.22 W/mK | 0.19–0.22 W/mK |
| Impact resistance | Low | Excellent (200× glass) | Moderate |
| Weight | Heaviest | Medium | Lightest |
| Machinability | Non-drillable | Easy | Easy |
| Fire resistance | Fireproof | Good | Combustible |
| UV/yellowing | Good | Yellows over time | Good long-term |
| Cost | Highest | Medium | Lowest |

Acrylic (PMMA) was selected for both WMB versions due to its superior transparency, low weight, ease of modification, and lower cost. Its drawbacks — lower impact resistance and combustibility — were judged acceptable given the indoor, controlled environment.

**Assembly methods**: Acrylic panels can be solvent-welded using dichloromethane (DCM), which fuses panels into a monolithic structure within seconds. However, DCM is highly volatile, toxic (possible carcinogen), and will permanently stain acrylic wherever it contacts the surface unintentionally. Version 1 was assembled with L-shaped aluminum profiles and two-component epoxy plus crystalline silicone (c-Si), which proved not to be watertight long-term. Version 2 used laser-cut panels with DCM solvent welding plus c-Si sealant, achieving a watertight enclosure verified by a one-week flood test with 30 liters of water. Critically, acetoxy silicones (a-Si) must never be used with acrylic, as they release acetic acid that corrodes and permanently stains the material.

#### 2.1.3 Version 1 — First Iteration

The first WMB was 120 cm wide × 40 cm deep × 45 cm high, constrained by its placement in a corridor. Panels were 4 mm thick, circular-saw-cut acrylic with rough edges. Internal thermal insulation consisted of 5 mm extruded polystyrene (XPS, lambda-value 0.03–0.04 W/mK) panels with diamond Mylar reflective sheeting glued to the inner face to maximize light distribution. Access was via sliding acrylic panes on aluminum alloy guides, chosen over hinged doors to minimize structural strain and spatial obstruction in the corridor setting.

#### 2.1.4 Version 2 — Current Enclosure

The current enclosure measures 150 cm wide × ~60 cm deep × 110 cm high (external dimensions), weighing approximately 100 kg empty. All structural panels are laser-cut for precise edge smoothness required by DCM solvent welding. Thermal insulation (1 cm XPS with diamond Mylar) is applied to the exterior of the enclosure, leaving the interior surfaces smooth for easier cleaning and maximizing usable internal volume. Access is again via two sliding front panels on alloy guides with c-Si adhesion.

The increased height of Version 2 creates three distinct climatic zones via a mid-height perforated acrylic shelf:

1. **Upper zone** (above shelf, high light): *Heliamphora* species and high-light miniature orchids
2. **Middle zone** (shelf level, intermediate light): Highland *Nepenthes* species and epiphytic *Utricularia* (*U. alpina*, *U. campbelliana*, *U. jamesoniana*, *U. quelchii*)
3. **Lower zone** (below shelf, low light, coolest): *Dracula* orchids, *Phragmipedium*, *Restrepia*, and highland ferns such as *Lecanopteris*

#### 2.1.5 Acrylic Panel Specifications

The enclosure was constructed from 20 laser-cut acrylic (PMMA) panels plus 6 structural triangles, fabricated according to detailed technical drawings (see Supplementary File S6). All dimensions below are in centimeters unless otherwise noted. All cuts are laser-squared unless otherwise specified.

**Table 1.** Main structural panels (Version 2 enclosure).

| Panel(s) | Qty | Dimensions (W × H) | Thickness | Material | Function |
|-----------|-----|---------------------|-----------|----------|----------|
| 1 | 1 | 145 × ~55 | 10 mm | Clear acrylic | Floor panel |
| 2 | 1 | 145 × ~115 | 10 mm | Clear acrylic | Back wall (with 2× 12 cm and 2× 2 cm circular holes for ventilation and cable pass-throughs) |
| 3 | 1 | 145 × 115 | 10 mm | Clear acrylic | Inner back / shelf support (with 1× 3 cm hole at 6.5 cm from left, 20 cm from bottom) |
| 4, 5 | 2 | 49 × 115 | 10 mm | Clear acrylic | Side panels (with 2× 10 cm notches on left edge, and holes: 1× 6 cm at 20 cm right / 4 cm up, 2× 1.6 cm for cable pass-throughs) |
| 6, 7 | 2 | 73.5 × 94.6 | 8 mm | Clear acrylic | Sliding front access panels (with 1× 1.5 cm hole at 10 cm from right, 46.6 cm from bottom) |
| 8, 9 | 2 | 145 × 10 | 20 mm | Clear acrylic | Bottom rail / shelf support tracks |

**Table 2.** Internal shelf and structural panels.

| Panel(s) | Qty | Dimensions | Thickness | Material | Function |
|-----------|-----|------------|-----------|----------|----------|
| 10, 11 | 2 | 57 × 46.5 and 71.5 × 46.5 | 8 mm | Perforated clear acrylic (Square 15 pattern) | Mid-height shelf floor (allows air and water circulation between upper and lower zones) |
| 12 | 1 | 123 × varies | 5 mm | Clear acrylic | Shelf front lip (with 3× 12 cm holes at 1 cm from top, spaced 34.5 cm apart, 9 cm from edges) |
| 13 | 1 | 123 × varies | 5 mm | Clear acrylic | Shelf structural support |
| 14, 15 | 2 | 51.5 × 6 | 5 mm | Clear acrylic | Shelf side brackets |
| Triangles | 6 | Triangular | 5 mm | Clear acrylic | Corner reinforcement brackets |

**Table 3.** Reflective and decorative panels.

| Panel(s) | Qty | Dimensions | Thickness | Material | Function |
|-----------|-----|------------|-----------|----------|----------|
| 16–20 | 5 | Various (see Supplementary File S6) | 2 mm | Silver mirror acrylic | Interior reflective surfaces for light distribution |

The back wall (Panel 2) features two pairs of circular holes: two 12 cm diameter holes positioned at 33 cm and 100 cm from the lower-left corner and 19 cm above the base serve as primary ventilation ports (fan mounting points for the outlet and impeller fans); two 2 cm diameter holes near the top edge (at 38 cm and 105 cm from the left, 2 cm below the top) provide cable pass-throughs for sensor wiring and power lines.

The side panels (Panels 4 and 5) incorporate 2 × 10 cm rectangular notches along the left edge to accommodate the sliding front panel guide rails. Each side panel has a 6 cm hole (20 cm from the notch corner, 4 cm up) for additional ventilation or drainage, plus two 1.6 cm cable pass-through holes.

#### 2.1.6 2022 Add-On Panels

A supplementary set of panels was fabricated in 2022 to add light-blocking, ventilation, and reflective elements:

**Table 4.** Add-on panels (2022 revision).

| Component | Qty | Dimensions (cm) | Thickness | Material | Function |
|-----------|-----|------------------|-----------|----------|----------|
| Panel A | 1 | 40 × 37 | 4 mm | Black acrylic | Light-blocking baffle |
| Panel B | 2 | 33 × 30 | 4 mm | Black acrylic | Light-blocking side baffles |
| Panel C | 1 | 65 × 40 | 4 mm | Black acrylic | Upper light shield |
| Panel D | 1 | 85 × 60 × 25 (stepped) | 4 mm | Black acrylic | Rear light/heat shield |
| Perforated E | 1 | 155 × 30 | 3 mm | Perforated clear acrylic (Square 15) | Ventilation grille |
| Perforated F | 1 | 153 × 24 | 3 mm | Perforated clear acrylic (Square 15) | Ventilation grille |
| Mirror G | 1 | 153 × varies | 2 mm | Silver mirror acrylic | Additional reflective surface |
| Mirror H | 1 | See drawings | 2 mm | Silver mirror acrylic | Additional reflective surface |
| Trapezoids | 6 | 55 × 13 × 2.5 (trapezoidal) | 3 mm | Clear acrylic | Light diffusion elements |

The black acrylic panels serve as light baffles to prevent light leakage from the LED pucks into the room and to block direct light from reaching heat-sensitive species in the lower zone. The additional perforated panels improve passive airflow, while the mirror panels increase light utilization efficiency by reflecting otherwise lost photons back into the growing volume.

#### 2.1.7 Drainage and Water Management

Two separate 40-liter reservoirs sit below the terrarium on the lowest shelf of the scaffold. The first reservoir supplies the MistKing misting pump; the second collects condensate from the evaporator plate. The PT14 evaporator (Section 2.2.2) generates condensate that drains via a small channel below the evaporator into the condensate reservoir by gravity. Misting runoff drains through the terrarium floor — the floor panel is slightly tilted toward a rear drainage hole — and is collected in the same condensate reservoir.

Water level in the misting reservoir is monitored by an ESP8266 microcontroller paired with an HC-SR04 ultrasonic distance sensor mounted at the top of the reservoir. The sensor measures the air gap above the water surface, from which the water level is calculated and published via MQTT. This provides a low-water alert on the Node-RED Dashboard and is logged to InfluxDB as the `water_level_local` measurement.

#### 2.1.8 Substrate and Planting Layout

The planting layout exploits the three climatic zones created by the mid-height shelf (Section 2.1.4):

**Epiphytes** — *Dracula*, *Masdevallia*, *Sophronitis* (syn. *Cattleya*), *Leptotes*, *Vanda pumila*, and New Guinea *Dendrobium* (including *D. victoriae-reginae*) are mounted on virgin cork bark slabs and tree fern plaques using sphagnum moss pads secured with monofilament line. Cork bark is preferred for its longevity in high-humidity conditions; tree fern is used for species that benefit from a consistently moist root zone. Mounted plants hang from stainless-steel hooks on the back wall and side panels across all three zones.

**Carnivorous plants** — *Heliamphora* species are grown in the upper zone in live *Sphagnum* moss, which maintains root moisture while providing the acidic, low-nutrient substrate these plants require. Epiphytic *Utricularia* (sect. *Orchidioides*: *U. alpina*, *U. quelchii*, and others) are mounted on vertical cork panels where they colonize the moss layer.

**Highland *Nepenthes*** — Miniature highland species are planted in hanging baskets filled with a mix of coarse orchid bark, perlite, and long-fiber sphagnum. The baskets hang from the shelf level, placing the pitchers in the middle zone's intermediate-light, high-humidity environment.

The emphasis throughout is on drainage and airflow: no substrate sits in standing water, all mounts allow air circulation around roots, and the perforated shelf permits vertical air movement between zones.

### 2.2 Hardware Components

#### 2.2.1 Lighting

Four ChilLED Logic Puck V3 LED modules provide illumination, each rated at approximately 100 W (400 W total nameplate). The pucks use Samsung LM301B diodes, which offer high photosynthetic photon efficacy across a broad spectrum suitable for plant growth. Each puck incorporates a self-contained water-cooling loop (sealed radiator and pump), ensuring that the LED heat is dissipated outside the terrarium enclosure rather than contributing to the internal thermal load.

The four pucks are wired in parallel and powered by a Mean Well HLG-480H-48A LED driver (480 W, 48 V / 10 A, 95% efficiency, IP65-rated). The driver provides constant-voltage output to the pucks. Master power is switched by a TP-Link Tapo P100 smart plug (192.168.1.55), and intensity is controlled via an Arduino Mega PWM output on pin 8 that drives the driver's analog dimming input.

During normal operation, the pucks run at 40–60% of their rated power (corresponding to slider positions 40–60 in the Node-RED Dashboard), producing moderate light levels appropriate for cloud forest species that naturally grow under persistent cloud cover. A midday intensity boost (Section 2.4.6) ramps from 40% to 60% between 11:00 and 11:30, holds until 13:00, then ramps back down, simulating the brief clearing events common on tepui summits.

#### 2.2.2 Cooling System

The cooling system is based on a Vitrifrigo ND50 OR2-V marine refrigeration unit, which uses a BD50F Danfoss variable-speed compressor (12/24 V DC, 31 W nominal draw) with R404a refrigerant. The compressor unit measures 360 × 155 × 135 mm and sits on the shelf below the terrarium.

The evaporator is a Vitrifrigo PT14 stainless steel plate (1220 × 280 mm), mounted vertically on the back wall of the terrarium at mid-height. Cold refrigerant circulates through the plate, cooling the surrounding air. Condensate forms on the plate surface and drains via gravity into the condensate reservoir below (Section 2.1.7).

An airflow shroud constructed from transparent Plexiglas encloses the evaporator plate and directs cold air circulation. The shroud is open at the bottom and angled approximately 30° downward, creating a chimney effect: warm terrarium air is drawn in from above by the fans, passes over the cold evaporator surface, and exits as cooled air at the lower portion of the terrarium. Two Noctua NF-F12 iPPC-24V fans (IP67-rated, 3000 RPM maximum, 24 V) are mounted in push-pull configuration on the shroud, replacing the original equipment fans for improved airflow and reduced acoustic noise. These fans are controlled via Arduino PWM pin 44 (Timer 5, 25 kHz).

An additional pair of internal circulation fans, also Noctua NF-F12 iPPC-24V units, are mounted separately to promote general air movement within the terrarium. These run on Arduino pin 12 (Timer 1, 25 kHz) and follow the same control logic as the evaporator fans: they run at 168 PWM when the compressor is off (gentle circulation) and ramp to 255 PWM when the compressor is active (maximum cold air distribution).

The compressor is switched on and off via a TP-Link Tapo P100 smart plug (192.168.1.196), driven by a hysteresis controller in the Temperature tab (Section 2.4.5). Total system power consumption is monitored by a Meross MSS310 energy-monitoring smart plug at 192.168.1.92, which reports instantaneous wattage to Node-RED every 10 minutes.

#### 2.2.3 Humidification

The humidification system uses a MistKing Standard diaphragm pump (24 V), which pressurizes water from the 40-liter misting reservoir and delivers it through a network of nozzles inside the terrarium. A ZipDrip anti-drip valve on the main line prevents residual dripping between misting events. The system produces a fine fog with an approximate droplet size of 50 μm.

The nozzle array consists of 20 nozzle points distributed across the terrarium ceiling: one quadruple-nozzle assembly, six double-nozzle assemblies, and four single nozzles, providing even fog coverage across the enclosure volume. The MistKing pump is powered via a TP-Link Tapo P100 smart plug (192.168.1.199) and controlled by a hysteresis algorithm in the Humidity tab (Section 2.4.4).

A critical safety interlock ensures that all fans stop when the mister is active (Section 2.4.4), preventing the fog plume from being dispersed before it can saturate the terrarium air.

#### 2.2.4 Air Circulation

Four groups of PWM-controlled fans are connected to an Arduino Mega 2560 via a custom serial protocol (Section 2.2.6):

- **Outlet fan** (PWM pin 45): Exhausts humid air from the terrarium through a rear ventilation port
- **Impeller fan** (PWM pin 46): Draws external air into the terrarium through the opposite ventilation port
- **Freezer fans** (PWM pin 44): Two Noctua NF-F12 iPPC-24V fans in the evaporator shroud (Section 2.2.2)
- **Circulation fans** (PWM pin 12): Two Noctua NF-F12 iPPC-24V fans for general internal air movement

All fan PWM signals use 25 kHz phase-correct PWM generated by hardware timers on the Arduino Mega: Timer 5 drives pins 44, 45, and 46, while Timer 1 drives pin 12. The 25 kHz frequency is above the audible range and compatible with Noctua 4-pin PWM fan inputs.

The outlet and impeller fans are governed by the PID controller during daytime (Section 2.4.3), with PWM constrained to 50–230 (20–90% duty cycle) via gain scheduling. The freezer and circulation fans follow the compressor state: 168 PWM (gentle circulation) when the compressor is off, 255 PWM (maximum airflow) when the compressor is active, and 0 PWM during misting events.

#### 2.2.5 Sensing

The primary environmental sensor is a Sensirion SHT35 digital temperature and humidity module (±0.1°C, ±1.5% RH accuracy), connected to an ESP8266 microcontroller that publishes readings over MQTT at approximately 1-second intervals. The sensor is positioned at mid-canopy height (~50 cm above the terrarium floor), roughly centered in the enclosure to provide representative readings across the growing volume.

The same ESP8266 board also reads an HC-SR04 ultrasonic distance sensor mounted above the misting reservoir to monitor water level (Section 2.1.7).

A separate room-environment sensor — another SHT module connected to a DietPi-based Raspberry Pi at 192.168.1.94 — provides ambient room temperature and humidity readings. The main control Pi polls this remote sensor via HTTP every 60 seconds, storing the values in InfluxDB as `room_temperature` and `room_humidity`. These room readings serve as covariates for environmental analysis and are displayed alongside terrarium data on the Dashboard charts.

#### 2.2.6 Control Hardware

- **Raspberry Pi** (ARMv8, Debian-based): Runs all software services (Node-RED, InfluxDB, Grafana, MQTT broker, watchdog)
- **Arduino Mega 2560**: GPIO interface via a custom text-based serial protocol at 115200 baud over USB (`/dev/ttyACM0`). The protocol uses newline-terminated ASCII commands: `P<pin>,<value>` for PWM output, `Q` for status query, `H,<value>` for heartbeat, and `D<pin>,<0|1>` for door state. This replaced the StandardFirmata protocol in February 2026 for improved reliability and debuggability (see Supplementary File S7 for the full Arduino sketch)
- **TP-Link Tapo P100 smart plugs** (×3): Switched mains power for lights (192.168.1.55), mister (192.168.1.199), and compressor (192.168.1.196), controlled via the PyP100 Python library from within Node-RED Python function nodes
- **Meross MSS310 smart plug**: Energy-monitoring plug at 192.168.1.92 on the master power line, reporting instantaneous power consumption via the Meross cloud API every 10 minutes
- **ESP8266 microcontroller**: Sensor data acquisition (SHT35 + ultrasonic water level) and MQTT publication
- **Reed switches** (×2): Magnetic door sensors on both sliding front panels, wired to Arduino digital inputs D22 (left) and D24 (right) with internal pull-up resistors

### 2.3 Software Architecture

The control system employs a layered architecture (Figure 1) running entirely on a single Raspberry Pi:

```
┌──────────────────────────────────────────────────────────────┐
│                       Grafana v10.2                           │
│                 (Visualization, port 3000)                    │
├──────────────────────────────────────────────────────────────┤
│                      InfluxDB v1.8                            │
│               (Time-series storage, port 8086)                │
├──────────────────────────────────────────────────────────────┤
│                     Node-RED v3.1.3                           │
│            (Control logic engine, port 1880)                  │
│  ┌─────────┬──────────┬──────────┬────────────────────────┐  │
│  │ Lights  │ Humidity │   Temp   │     Fans               │  │
│  │   Tab   │   Tab    │   Tab    │ PID + Door Safety      │  │
│  ├─────────┼──────────┼──────────┼────────────────────────┤  │
│  │ Weather │  Charts  │ Utilities│                        │  │
│  │   Tab   │   Tab    │   Tab    │                        │  │
│  └─────────┴──────────┴──────────┴────────────────────────┘  │
├──────────┬──────────────────┬──────────────┬─────────────────┤
│   MQTT   │  Custom Serial   │   PyP100     │  Meross Cloud   │
│ (:1883)  │ (USB, 115200)    │  (TCP/IP)    │    (HTTPS)      │
├──────────┼──────────────────┼──────────────┼─────────────────┤
│  ESP +   │  Arduino Mega    │ Tapo P100 ×3 │  Meross MSS310  │
│  SHT35   │ 5 PWM + 2 doors  │ light/mist/  │  (power meter)  │
│  sensor  │  + heartbeat     │  compressor  │                 │
└──────────┴──────────────────┴──────────────┴─────────────────┘
```

**Figure 1.** System architecture showing the software stack (top) and hardware interfaces (bottom).

#### 2.3.1 Node-RED Control Engine

Node-RED v3.1.3, a flow-based visual programming environment built on Node.js, serves as the central control engine. The control logic is organized across seven flow tabs:

| Tab | Function |
|-----|----------|
| **Lights** | Photoperiod scheduling via BigTimer, PWM sunrise/sunset/midday dimming ramps, startup recovery |
| **Humidity** | Sensor data ingestion (MQTT), VPD calculation, target humidity from weather data, mister hysteresis control |
| **Temperature** | Target temperature from weather data, compressor hysteresis control |
| **Fans** | Gain-scheduled PID controller, door safety mode, manual override, mister safety interlock |
| **Weather** | OpenWeatherMap API integration for 4 Colombian cities, data averaging, weather fallback |
| **Charts** | Node-RED Dashboard UI gauges and charts for local monitoring, room data overlay |
| **Utilities** | Data logger (14 measurements at 60-second intervals), serial parser, Meross power monitoring, system diagnostics |

Node-RED runs as a systemd service (`nodered`), ensuring automatic restart on failure and boot-time startup.

#### 2.3.2 Data Storage and Visualization

**InfluxDB v1.8.10** stores all environmental measurements with nanosecond-precision timestamps. The database (`highland`) uses a 1-year retention policy (`standard_highland_retention`), providing sufficient historical data for seasonal analysis while managing storage on the Raspberry Pi's SD card. Twenty-six distinct measurements are recorded (see Supplementary Table S1).

**Grafana v10.2.3** provides four monitoring dashboards:

1. **Terrarium — Roraima**: Primary operational dashboard with real-time temperature, humidity, VPD, and actuator status
2. **Colombian Weather Reference**: Raw weather data from the four reference cities
3. **System Performance**: PID controller diagnostics, fan PWM outputs, and control quality metrics
4. **Night A/B Fan Experiment**: Dedicated dashboard for the nighttime ventilation study (Section 2.4.7), now serving as historical reference

#### 2.3.3 Hardware Watchdog

A custom shell script watchdog (`arduino-watchdog.sh`, v7) runs as a systemd service, monitoring the Arduino Mega USB connection and serial communication health at 60-second intervals. The watchdog performs a four-step health check:

1. USB device `/dev/ttyACM0` exists (device enumeration)
2. Node-RED systemd service is active
3. Node-RED has the serial port open (`lsof` check)
4. GPIO heartbeat is alive (last `arduino_status` value in InfluxDB within 3 minutes)

Recovery strategy depends on the failure type. For Node-RED process failures (steps 2–3), the watchdog attempts up to 2 Node-RED restarts within a 30-minute window before escalating to a full system reboot. For heartbeat failures (step 4), the watchdog reboots the system directly — experience showed that Node-RED restarts do not resolve serial stall conditions (Section 4.5), making intermediate recovery attempts futile.

A reboot cooldown prevents reboot loops: if the system has been up less than 10 minutes, the reboot is deferred to the next check cycle. A 5-minute grace period after Node-RED starts allows time for the serial connection and initial heartbeats before the GPIO liveness check activates. Before each reboot, the watchdog logs a diagnostic snapshot (process state, memory, last serial messages, USB kernel messages) to aid root-cause analysis.

### 2.4 Control Algorithms

#### 2.4.1 Weather Data Integration and Setpoint Generation

The system queries the OpenWeatherMap API at regular intervals for current weather conditions at four Colombian highland cities:

| City | Elevation | Role |
|------|-----------|------|
| Chinchiná | ~1,300 m | Warm reference |
| Medellín | ~1,500 m | Mid-elevation reference |
| Sonsón | ~2,475 m | Cool reference |
| Bogotá | ~2,640 m | Cool/high reference |

Temperature and humidity values from these cities are averaged to produce raw setpoints, which are then clamped to safe operating ranges:

- **Temperature**: 12–24°C
- **Humidity**: 70–90% RH

A **15-hour time shift** is applied to align Colombian daytime weather (UTC-5) with Genoa nighttime (UTC+1), producing the desired pattern where terrarium nighttime temperatures correspond to the current Colombian daytime conditions. This creates naturalistic diurnal variation: the terrarium experiences cooler conditions at night (when Colombian daytime mountain temperatures are moderate) and warmer conditions during the day.

The 30-minute averaging window smooths transient API fluctuations while preserving meaningful weather changes (e.g., rain events producing sudden cooling and humidity spikes that translate into the terrarium environment).

#### 2.4.2 Vapor Pressure Deficit Calculation

Vapor Pressure Deficit (VPD) is calculated continuously from temperature (*T*, °C) and relative humidity (*RH*, %) using the Magnus formula:

**Saturated Vapor Pressure (SVP)**:

    SVP = 0.6108 × exp(17.27 × T / (T + 237.3))    [kPa]

**Actual Vapor Pressure (AVP)**:

    AVP = SVP × (RH / 100)    [kPa]

**Vapor Pressure Deficit**:

    VPD = SVP − AVP    [kPa]

Cloud forest species generally thrive at VPD values below 0.4 kPa, corresponding to near-saturation conditions. The system logs VPD continuously, providing a physiologically meaningful metric for assessing environmental suitability beyond simple humidity readings.

#### 2.4.3 PID Humidity Controller

The core control algorithm is a discrete PID controller that modulates fan speed in response to humidity error:

    error = current_humidity − target_humidity

A positive error (too humid) increases fan speed to accelerate evaporative cooling and air exchange; a negative error (too dry) reduces fan speed, allowing the mister to raise humidity without opposition.

The PID output is computed as:

    u(t) = Kp × e(t) + Ki × ∫e(τ)dτ + Kd × de/dt

With the following tuning parameters, determined empirically and adjustable at runtime via the Node-RED Dashboard:

| Parameter | Value | Function |
|-----------|-------|----------|
| Kp | 50 | Proportional gain — immediate response to humidity deviation |
| Ki | 0.5 | Integral gain — eliminates steady-state offset |
| Kd | 10 | Derivative gain — dampens oscillation from rapid changes |

**Gain scheduling**: To prevent rapid fan oscillation near the humidity setpoint while maintaining aggressive response to large disturbances, the controller applies a gain factor (*g*) that scales the effective Kp and Kd based on the magnitude of the current error:

- |error| ≤ 1.5% RH: *g* = 0.15 (effective Kp = 7.5, gentle control near target)
- |error| ≥ 4.0% RH: *g* = 1.0 (full Kp = 50, aggressive response to large deviations)
- Between 1.5% and 4.0%: *g* is linearly interpolated

This gain scheduling eliminated the ±25 PWM oscillations that occurred with fixed gains when the humidity hovered within ±0.5% of the setpoint.

**Anti-windup protection**: The integral accumulator is clamped to ±120 PWM-equivalent units to prevent integral windup during sustained large errors (e.g., during terrarium door opening). When the error magnitude falls below 2.0% RH, the integral decays at 5% per second to prevent steady-state creep and accelerate wind-down after humidity spikes.

**Derivative filtering**: A first-order exponential low-pass filter (α = 0.12) heavily smooths the derivative term to reduce noise amplification from sensor fluctuations while preserving response to genuine rapid humidity changes.

**Rate limiting**: Fan speed changes are limited to max(10, |error| × 3) PWM units per control cycle (maximum 20 PWM per cycle to protect the serial link), preventing abrupt speed transitions while allowing faster response during large disturbances.

The PID output is added to a base speed of 50 PWM (approximately 20% duty cycle), providing gentle circulation at the humidity setpoint. The total output is clamped to 40–230 PWM (16–90% duty cycle), ensuring continuous minimum airflow while providing sufficient headroom for high-humidity events.

#### 2.4.4 Mister Hysteresis Control

The ultrasonic mister is controlled via a hysteresis (bang-bang) controller in the Humidity tab, with configurable on/off thresholds relative to the target humidity. When humidity falls below the lower threshold, the mister activates; when humidity exceeds the upper threshold, it deactivates.

A critical safety interlock ensures that **all fans stop when the mister is active**. This prevents fans from dispersing the mist plume before it can saturate the terrarium air and avoids drawing unsaturated air into the enclosure during misting events. The interlock is implemented as a gate function upstream of the PID controller output that blocks fan commands when `mister_status` is true.

#### 2.4.5 Freezer Hysteresis Control

The Vitrifrigo ND50 compressor unit (Section 2.2.2) is controlled via a hysteresis controller in the Temperature tab, switching the compressor on/off via its Tapo P100 smart plug based on the difference between actual and target temperature. When the compressor activates, the evaporator fans (pin 44) and circulation fans (pin 12) ramp to 255 PWM to maximize cold air distribution; when it deactivates, these fans reduce to 168 PWM for gentle background circulation.

#### 2.4.6 Light Schedule

The photoperiod follows a fixed schedule implemented via the BigTimer node, with two independent dynamic dimmer channels providing sunrise/sunset and midday intensity variation:

| Event | Time | Dimmer | Duration | Slider |
|-------|------|--------|----------|--------|
| Lights ON (plug) | 06:25 | — | — | — |
| Dawn ramp-up | 06:30 | #1 | 30 min (40 steps × 45 s) | 0 → 40 |
| Morning plateau | 07:00–11:00 | — | 4 hours | 40 |
| Midday ramp-up | 11:00 | #2 | 30 min (20 steps × 90 s) | 40 → 60 |
| Midday plateau | 11:30–13:00 | — | 1.5 hours | 60 |
| Midday ramp-down | 13:00 | #2 | 30 min (20 steps × 90 s) | 60 → 40 |
| Afternoon plateau | 13:30–19:30 | — | 6 hours | 40 |
| Dusk ramp-down | 19:30 | #1 | 30 min (40 steps × 45 s) | 40 → 0 |
| Lights OFF (plug) | 20:05 | — | — | — |

The slider value is inverted by a range node before being written to the Arduino PWM pin: lower PWM values produce brighter light (the LED driver dims proportionally to the PWM signal). The 5-minute offset between plug activation and dimmer ramp start ensures the LED driver is powered before the PWM dimmer begins ramping. The 30-minute ramp duration simulates the gradual light transitions characteristic of tropical mountain environments.

A startup recovery node detects when Node-RED restarts during a ramp window and calculates the elapsed fraction, issuing a partial-ramp command so the dimmer finishes on schedule rather than restarting the full 30-minute ramp from scratch.

#### 2.4.7 Night A/B Fan Experiment

A controlled experiment evaluated the effect of nighttime air circulation on temperature and humidity. The protocol alternated nightly based on day-of-year parity:

- **Night A** (even day-of-year): All fans off (0 PWM) — passive cooling only
- **Night B** (odd day-of-year): Outlet and impeller fans at 80 PWM (~31% duty cycle) — gentle circulation

The mode was determined by the evening's date (not the current date at midnight) to prevent mid-night transitions. The experiment ran from February 5 to February 18, 2026 (13 nights: 7 Night A, 6 Night B). Results were analyzed using OLS regression, IV/2SLS with the A/B assignment as an instrument for fan speed, and hour-by-hour adjusted profiles (see Supplementary File S8 for the full analysis scripts).

Key findings from the IV/2SLS analysis: each +10 PWM of fan speed causes a −0.37% reduction in humidity (the OLS estimate has the wrong sign due to PID simultaneity bias). Hour-by-hour analysis showed that nighttime fans at 80 PWM cool the terrarium significantly during the evening hours (20:00–23:00, adjusted effect −0.75 to −1.4°C) but produce slight warming after midnight (+0.3 to +0.55°C) as fans draw warmer room air into the enclosure.

Based on these findings, the A/B experiment was suspended and the fan schedule was adjusted: the PID controller now remains active from 06:30 to midnight (was 06:30–20:00), capturing the evening cooling benefit, while fans are off from midnight to 06:30 to avoid the late-night warming effect.

#### 2.4.8 Door Safety Mode

Two magnetic reed switches (one per sliding front panel) are wired to Arduino digital inputs D22 and D24 with internal pull-up resistors. A 3-second software debounce in the door controller node suppresses spurious open/close events from contact bounce — the door must remain open for 3 consecutive seconds before the safety mode activates.

When either door opens, the system enters door safety mode:

1. All fans stop immediately (pins 12, 44, 45, 46 → 0 PWM)
2. Compressor turns off (Tapo plug blocked from turning on)
3. Mister turns off (Tapo plug blocked from turning on)
4. Lights set to 60% brightness (PWM 102) regardless of current dimmer state, providing working light for maintenance

All Tapo plug commands pass through gate nodes that block inappropriate actions during door safety mode (e.g., the compressor gate blocks "on" commands, the light gate blocks "off" commands). Fan writer nodes check the `door_safety_active` global flag and suppress PID output while the flag is set.

When all doors close, the system restores the previous state: fan speeds resume from the PID controller, Tapo plugs return to their pre-opening states (saved on door open), and the dimmer restores its last commanded brightness.

#### 2.4.9 Startup Recovery

A startup brightness node runs once after Node-RED deploys, determining the correct light state based on the current time. If the system restarts during one of the four ramp windows (dawn, midday-up, midday-down, dusk), the node calculates the elapsed fraction of the ramp and issues a partial-start command to the appropriate dimmer, so the ramp completes on schedule rather than restarting from scratch. Outside ramp windows, the node simply sets the correct static brightness level (0, 40, or 60 on the slider).

#### 2.4.10 Control Priority Hierarchy

The system implements a four-level control priority:

1. **Door safety** (highest priority): Door open overrides all automatic control, forces safe state
2. **Manual override**: Operator-set fan speed via the Node-RED Dashboard UI
3. **Safety interlock**: Mister-active fan stop, overriding PID output
4. **Automatic PID control** (lowest priority): Normal humidity-based operation

Each level checks for higher-priority overrides before executing, ensuring predictable behavior during maintenance or emergency situations.

### 2.5 Data Logging

A centralized data logger function on the Utilities tab reads all global context variables at 60-second intervals and writes to 14 individual InfluxDB measurements:

1. `local_temperature` — Terrarium temperature (°C)
2. `local_humidity` — Terrarium relative humidity (%)
3. `vpd` — Vapor pressure deficit (kPa)
4. `target_temperature_computed` — Weather-derived temperature setpoint (°C)
5. `target_humidity_computed` — Weather-derived humidity setpoint (%)
6. `difference_temperature` — Target minus actual temperature (°C)
7. `difference_humidity` — Target minus actual humidity (%)
8. `fan_speed` — PID controller output (PWM 0–255)
9. `freezer_status` — Compressor relay state (0/1)
10. `mister_status` — Mister relay state (0/1)
11. `light_status` — Light relay state (0/1)
12. `water_level_local` — Reservoir water level (arbitrary units)
13. `night_test_mode` — Night A/B experiment mode (0=A, 1=B, −1=suspended)
14. `power_consumption` — System power draw (W, via Meross MSS310, logged every 10 minutes)

Additional measurements are logged by other flow components (individual fan PWM channels, individual city weather data, room temperature/humidity), bringing the total to 27 InfluxDB measurements (Supplementary Table S1).

---

## 3. Results

### 3.1 Environmental Performance

Over the monitoring period, the system maintained the following environmental ranges within the terrarium:

| Parameter | Minimum | Maximum | Typical Range | Target Range |
|-----------|---------|---------|---------------|--------------|
| Temperature | 13.5°C | 24.3°C | 15–22°C | 12–24°C |
| Relative Humidity | 75% | 98% | 82–95% | 70–90% |
| VPD | 0.03 kPa | 0.64 kPa | 0.08–0.45 kPa | < 0.8 kPa |

The system achieves a meaningful diurnal temperature swing despite the terrarium being located in a room maintained at approximately 22°C year-round. Nighttime terrarium temperatures routinely drop to 14–16°C through active compressor cooling, while daytime temperatures rise to 18–22°C, producing a 4–8°C daily amplitude that approximates conditions on mid-elevation tepuis.

### 3.2 PID Controller Stability

The PID controller maintains humidity within ±3% RH of the setpoint under steady-state conditions. The proportional-integral-derivative architecture eliminates the continuous cycling observed with simpler hysteresis controllers, producing smooth fan speed transitions.

The introduction of gain scheduling (Section 2.4.3) significantly improved near-setpoint behavior. With fixed gains (Kp=50), the controller exhibited rapid ±25 PWM oscillations when the humidity hovered within ±0.5% of the target — the proportional term was large enough to overshoot in alternating directions. After gain scheduling (effective Kp=7.5 within ±1.5% of target), these oscillations were eliminated, and the fan speed transitions became smooth and gradual.

An IV/2SLS analysis using the Night A/B experiment (Section 2.4.7) as an instrument confirmed that the PID-controlled fans do reduce humidity: each +10 PWM of fan speed causes a −0.37% reduction in humidity (p < 0.05). The OLS estimate yields a positive coefficient (+0.05% per +10 PWM) due to PID simultaneity bias — the controller increases fan speed *because* humidity is high, creating a spurious positive association. The instrumental variable approach resolves this by exploiting the experimentally assigned fan speed variation. The compressor is the dominant cooling and dehumidification actuator (−15.9% humidity long-run effect when active), with the PID fans providing fine-tuning within the compressor's hysteresis band.

### 3.3 Weather Data Correlation

The Colombian weather integration produces continuously varying setpoints that reflect real meteorological conditions. Temperature setpoints track Colombian highland weather patterns with appropriate clamping, while humidity setpoints respond to precipitation events in the reference cities.

The 15-hour time shift between Colombian local time (UTC−5) and Italian local time (UTC+1/+2) means that Colombian daytime conditions (typically 16–22°C, 60–80% RH at the reference elevations) map onto Italian nighttime, while Colombian nighttime conditions (typically 12–16°C, 85–95% RH) map onto Italian daytime. This produces a biologically desirable pattern: the terrarium experiences cooler, more humid conditions at night and warmer, drier conditions during the day, mirroring the natural diurnal cycle of cloud forest environments.

The 30-minute averaging window across all four cities smooths transient API fluctuations while preserving meaningful weather events. Sudden cooling and humidity spikes from rain events in Colombia translate into corresponding terrarium setpoint changes within the hour, creating stochastic variation that mimics natural fog immersion events on tepui summits. A weather fallback provides sensible default setpoints (day: 24°C/85% RH; night: 14°C/90% RH) if the OpenWeatherMap API is temporarily unreachable.

### 3.4 Species Diversity and Growing Results

The system supports approximately 120 species across orchid, carnivorous plant, and fern genera. The primary genera include:

**Orchids** — *Dracula* and *Masdevallia* (pleurothallid alliance, mounted on cork bark in the lower zone), *Sophronitis* (syn. *Cattleya*, Brazilian miniatures on cork bark), *Leptotes* (mounted), *Vanda pumila*, *Dendrobium victoriae-reginae* and other New Guinea section *Dendrobium* species (mounted on tree fern in the upper zone). These genera flower regularly under the system's conditions, with *Dracula* and *Sophronitis* producing blooms throughout the year.

**Carnivorous plants** — *Heliamphora* species (grown in live *Sphagnum* in the upper zone) produce mature pitchers and divide steadily, indicating sustained suitability of the temperature and humidity regime. Miniature highland *Nepenthes* species in hanging baskets maintain active trap production with new pitchers forming continuously. Epiphytic *Utricularia* sect. *Orchidioides* (*U. alpina*, *U. quelchii*, and related species) colonize cork mounts and produce their characteristic orchid-like flowers.

**Other epiphytes** — Highland ferns, small bromeliads, and various mosses fill the lower zone and provide ground cover, contributing to the overall humidity buffering of the system.

The diversity of genera successfully maintained — spanning Neotropical cloud forest orchids, Guiana Highland carnivorous plants, and Australasian *Dendrobium* — demonstrates that the weather-variable setpoint approach can simultaneously satisfy species with overlapping but not identical environmental requirements.

### 3.5 System Reliability

The primary reliability challenge is a recurring serial stall condition in which the Arduino Mega's ATmega16U2 USB-to-serial bridge chip enters a stuck state, silently stopping all serial communication after 1–5 hours of normal operation. This issue predates the current custom serial protocol and was also observed with StandardFirmata, indicating a hardware-level problem rather than a protocol-level one. No kernel errors or USB disconnect events are logged when the stall occurs.

The watchdog v7 (Section 2.3.3) mitigates this by detecting the absence of heartbeat messages and rebooting the system directly — experience showed that Node-RED restarts alone do not resolve the stall. The typical recovery time from stall detection to full system restoration is approximately 8 minutes (60-second detection interval + boot time + Node-RED startup + serial reconnection + GPIO grace period).

Between stall events, the system operates autonomously without human intervention. The weather fallback mechanism (Section 2.4.1) ensures that temporary internet outages do not disrupt control by holding the last valid setpoints and reverting to sensible defaults. The door safety mode (Section 2.4.8) provides automatic protection during maintenance, and the startup recovery node (Section 2.4.9) handles graceful recovery from reboots that occur during light-dimming ramp windows.

---

## 4. Discussion

### 4.1 Weather-Based vs. Fixed Setpoints

The use of real-time weather data from Colombian highlands as the basis for terrarium setpoints represents a departure from conventional fixed-schedule environmental control. This approach offers several advantages:

**Naturalistic variability**: Fixed setpoints produce monotonous conditions that may fail to provide environmental cues for phenological processes. Weather-referenced setpoints introduce stochastic variation within safe bounds — rain events in Colombia produce sudden cooling and humidity spikes that translate into the terrarium environment, simulating the fog immersion events characteristic of tepui habitats.

**Seasonal adaptation**: As Colombian weather patterns shift seasonally, the terrarium setpoints automatically adjust, providing longer-timescale variation without manual reprogramming.

**Biological hypothesis**: While not formally tested in this study, we hypothesize that weather-driven environmental variation may improve flowering frequency and overall vigor in cloud forest species compared to static conditions, as it more closely approximates the dynamic environments to which these species are adapted.

### 4.2 PID vs. Bang-Bang Control

The PID controller for humidity management offers significant advantages over the hysteresis (bang-bang) approach used for temperature (freezer) and humidification (mister) control:

- **Reduced cycling**: Hysteresis controllers produce characteristic on-off oscillation around setpoints. The PID controller's continuous fan speed modulation eliminates this cycling, producing smoother environmental transitions.
- **Anticipatory response**: The derivative term detects rapid humidity changes (e.g., mister activation) and preemptively adjusts fan speed, reducing overshoot.
- **Steady-state precision**: The integral term eliminates offset, maintaining humidity closer to target over extended periods.

However, PID control requires more careful tuning than bang-bang approaches. The empirically determined gains (Kp=50, Ki=0.5, Kd=10) and gain scheduling thresholds (Section 2.4.3) reflect a trade-off between responsiveness and stability specific to this terrarium's volume, ventilation geometry, and sensor response time. Different enclosures would require re-tuning, though the gain scheduling approach — reducing proportional response near the setpoint — should transfer well to other systems.

### 4.3 Open-Source Accessibility

A key design goal of this system is reproducibility using commodity hardware and free software. The total system cost (excluding terrarium construction and plants) consists of a Raspberry Pi, an Arduino Mega, three smart plugs, an ESP microcontroller with sensor, fans, and LED pucks — all widely available consumer components.

Node-RED's visual flow-based programming environment lowers the barrier to entry compared to traditional programming approaches. Users can inspect and modify control logic visually, adjust PID tuning parameters through dashboard controls, and extend the system with additional sensors or actuators using Node-RED's extensive node library.

### 4.4 Ongoing Optimization

The Night A/B fan experiment (Section 2.4.7) illustrates an important aspect of the system: even after two years of successful operation, continuous refinement remains possible and valuable. The open data pipeline (InfluxDB + Grafana) enabled rapid hypothesis testing — the experiment ran for only 13 nights before producing actionable findings (extend fan schedule to midnight, suspend fans after midnight) that were immediately implemented as a configuration change.

This experimental capability, built into the control infrastructure rather than requiring separate equipment, represents a significant advantage of the software-defined approach over hardware-only solutions. The same data pipeline supported rigorous IV/2SLS causal inference that correctly resolved the PID simultaneity bias, demonstrating that hobbyist-scale terrarium systems can produce publication-quality analytical results.

### 4.5 Limitations

- **Single sensor**: The system relies on a single SHT35 sensor, creating a single point of failure and potentially unrepresentative measurements in a terrarium with spatial environmental gradients.
- **Internet dependency**: Weather-based setpoints require internet access to the OpenWeatherMap API, and the Meross power monitoring relies on a cloud API. Connectivity interruptions cause the system to hold the last valid setpoints (with sensible fallback defaults), but the cloud dependency for power monitoring is a design weakness that could be addressed by local energy metering.
- **Serial stall**: The Arduino Mega's ATmega16U2 USB-serial bridge periodically enters a stuck state after 1–5 hours, requiring a full system reboot. This appears to be a hardware-level issue (possibly related to the clone board's USB chip) and persists across protocol changes. Replacing the board with one using a CH340G USB chip may resolve the issue.
- **No formal species performance metrics**: While approximately 120 species are maintained, systematic growth rate and flowering frequency measurements have not been conducted.

### 4.6 Future Work

- Addition of redundant sensors and spatial temperature/humidity mapping
- Integration of CO₂ monitoring for photosynthesis optimization
- Formal comparison of species performance under weather-variable vs. fixed setpoints
- Expansion of the weather reference to include additional cities or direct tepui weather station data when available
- Machine learning approaches to PID auto-tuning based on historical response data

---

## 5. Conclusions

We have demonstrated that an open-source, software-defined control system built on commodity hardware can successfully simulate highland cloud forest climates for extended-duration terrarium cultivation. The combination of weather-referenced setpoints, gain-scheduled PID humidity control, door safety interlocks, and comprehensive data logging creates a system that is both effective for maintaining sensitive cloud forest species and accessible to the wider terrarium community. The IV/2SLS analysis of the Night A/B experiment provided causal evidence that the PID-controlled fans reduce humidity by −0.37% per +10 PWM — a finding that would be missed by naive regression due to simultaneity bias, illustrating the value of embedding experimental capabilities directly into the control infrastructure. All system components — Node-RED flows, Arduino firmware, Grafana dashboards, watchdog scripts, statistical analysis code, and documentation — are available as open-source supplementary materials.

---

## References

- Rull, V., & Vegas-Vilarrúbia, T. (2006). Unexpected biodiversity loss under global warming and protected Venezuelan tepuis. *Current Biology*, 16(2), R58-R63.
- Berry, P. E., & Riina, R. (2005). Insights into the diversity of the Pantepui flora and the biogeographic complexity of the Guayana Shield. *Biologiske Skrifter*, 55, 145-167.
- Givnish, T. J., et al. (2014). Adaptive radiation, correlated and contingent evolution, and net species diversification in Bromeliaceae. *Molecular Phylogenetics and Evolution*, 71, 55-78.
- Node-RED Project. (2026). https://nodered.org/
- InfluxDB. (2026). https://www.influxdata.com/
- Grafana Labs. (2026). https://grafana.com/

---

## Supplementary Materials

- **Supplementary Table S1**: Complete InfluxDB measurement schema (27 measurements)
- **Supplementary File S1**: Sanitized Node-RED flow configuration (`flows-sanitized.json`)
- **Supplementary File S2**: Grafana dashboard exports (4 dashboards)
- **Supplementary File S3**: Arduino watchdog v7 script and systemd service configuration
- **Supplementary File S4**: Detailed system architecture and data flow documentation
- **Supplementary File S5**: PID controller algorithm documentation with gain scheduling
- **Supplementary File S6**: Acrylic panel technical drawings — original fabrication specifications for all 20 panels plus add-on components (from *Progetto completo* and *Progetto adds-on 2022* design documents)
- **Supplementary File S7**: Arduino Mega firmware (`arduino-terrarium.ino`) — custom serial protocol sketch
- **Supplementary File S8**: Statistical analysis scripts (OLS, IV/2SLS, hourly A/B profiles) with data export tools
- **Supplementary File S9**: Meross power monitoring script
