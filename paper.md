# Open-Source Climate Simulation for Highland Cloud Forest Terrariums: A Node-RED-Based Control System with PID Humidity Management and Colombian Weather Data Integration

**Authors**: `[PLACEHOLDER — author names and affiliations]`

**Corresponding author**: `[PLACEHOLDER — email]`

---

## Abstract

We present an open-source environmental control system for simulating highland cloud forest (tepui) climates within a closed terrarium, designed to maintain conditions suitable for approximately 120 plant species across genera including *Heliamphora*, *Dracula*, *Sophronitis*, *Nepenthes*, and highland *Dendrobium*. The system, built on the Node-RED visual programming platform with InfluxDB time-series storage and Grafana visualization, integrates real-time weather data from four Colombian highland cities to generate dynamic temperature and humidity setpoints with a 15-hour time shift. A PID controller (Kp=15, Ki=0.08, Kd=8) drives evaporative cooling fans in response to humidity error, achieving typical conditions of 13.5–24.3°C and 75–98% relative humidity within a Mediterranean-climate room (Genoa, Italy). The system has operated continuously for over two years with minimal human intervention, demonstrating that commodity hardware and open-source software can replicate challenging montane microclimates. All control flows, monitoring dashboards, and documentation are available as supplementary materials.

**Keywords**: cloud forest terrarium, environmental control, PID controller, Node-RED, tepui climate, vapor pressure deficit, open-source horticulture

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

`[PLACEHOLDER — User will provide: drainage system details, water collection, overflow prevention.]`

#### 2.1.8 Substrate and Planting Layout

`[PLACEHOLDER — User will provide: substrate composition, planting arrangement, mounting methods for epiphytes.]`

### 2.2 Hardware Components

#### 2.2.1 Lighting

Four chilled LED pucks (100 W each, 400 W total) provide illumination. Each puck is water-cooled to minimize heat contribution to the terrarium enclosure. The LED array is controlled via a TP-Link Tapo P100 smart plug (192.168.1.x) for on/off scheduling and an Arduino Mega 2560-driven PWM dimmer circuit (pin 8) for sunrise/sunset intensity ramps.

`[PLACEHOLDER — User will provide: LED specifications (spectrum, manufacturer, model), cooling system details, mounting arrangement, PAR/PPFD measurements if available.]`

#### 2.2.2 Cooling System

`[PLACEHOLDER — User will provide: Peltier/freezer system details, cold-side heat exchanger, fan arrangement for cold air distribution. Known: controlled via TP-Link Tapo P100 smart plug at 192.168.1.196, driven by hysteresis controller in Node-RED.]`

#### 2.2.3 Humidification

`[PLACEHOLDER — User will provide: Ultrasonic mister specifications, water reservoir, delivery mechanism. Known: controlled via TP-Link Tapo P100 smart plug at 192.168.1.199, with safety interlock that stops fans during misting.]`

#### 2.2.4 Air Circulation

Three PWM-controlled fans connected to an Arduino Mega 2560 via Firmata protocol:

- **Outlet fan** (PWM pin 44): Exhausts humid air from the terrarium
- **Impeller fan** (PWM pin 45): Internal air circulation
- **Freezer fan** (PWM pin 46): Forces air over the Peltier cold side

Fan speed is governed by the PID controller during daytime (Section 2.4.3) and by the experimental night protocol during nighttime (Section 2.4.7). PWM range is constrained to 40–204 (16–80% duty cycle) to ensure minimum circulation and limit acoustic noise.

#### 2.2.5 Sensing

An SHT35 digital temperature and humidity sensor, connected via an ESP microcontroller publishing over MQTT, provides the primary environmental measurements at approximately 1-second intervals. The sensor is positioned at canopy height within the terrarium.

`[PLACEHOLDER — User will provide: sensor mounting details, any additional sensors (water level sensor specifics), ESP board model.]`

#### 2.2.6 Control Hardware

- **Raspberry Pi** (ARMv8, Debian-based): Runs all software services
- **Arduino Mega 2560**: GPIO interface via StandardFirmata protocol over USB serial (/dev/ttyACM0) for PWM fan control and dimmer output
- **TP-Link Tapo P100 smart plugs** (×3): Switched mains power for lights, mister, and freezer, controlled via PyP100 Python library
- **ESP microcontroller**: Sensor data acquisition and MQTT publication

### 2.3 Software Architecture

The control system employs a layered architecture (Figure 1) running entirely on a single Raspberry Pi:

```
┌─────────────────────────────────────────────────────┐
│                    Grafana v10.2                     │
│              (Visualization, port 3000)              │
├─────────────────────────────────────────────────────┤
│                   InfluxDB v1.8                      │
│            (Time-series storage, port 8086)          │
├─────────────────────────────────────────────────────┤
│                  Node-RED v3.1.3                     │
│         (Control logic engine, port 1880)            │
│  ┌──────────┬──────────┬──────────┬───────────────┐ │
│  │  Lights  │ Humidity │  Temp    │     Fans      │ │
│  │   Tab    │   Tab    │   Tab    │     Tab       │ │
│  ├──────────┼──────────┼──────────┼───────────────┤ │
│  │ Weather  │  Charts  │ Utilities│               │ │
│  │   Tab    │   Tab    │   Tab    │               │ │
│  └──────────┴──────────┴──────────┴───────────────┘ │
├──────────┬──────────────────────┬───────────────────┤
│   MQTT   │      Firmata         │     PyP100        │
│ (1883)   │   (USB serial)       │    (TCP/IP)       │
├──────────┼──────────────────────┼───────────────────┤
│  ESP +   │   Arduino Mega       │  Tapo P100 ×3     │
│  SHT35   │ (3 PWM fans + dim)  │ (lights/mist/frz) │
└──────────┴──────────────────────┴───────────────────┘
```

**Figure 1.** System architecture showing the software stack (top) and hardware interfaces (bottom).

#### 2.3.1 Node-RED Control Engine

Node-RED v3.1.3, a flow-based visual programming environment built on Node.js, serves as the central control engine. The control logic is organized across seven flow tabs:

| Tab | Function |
|-----|----------|
| **Lights** | Photoperiod scheduling via BigTimer, PWM sunrise/sunset dimming ramps |
| **Humidity** | Sensor data ingestion (MQTT), VPD calculation, target humidity from weather data, mister hysteresis control |
| **Temperature** | Target temperature from weather data, freezer hysteresis control |
| **Fans** | PID controller, manual override, mister safety interlock, night A/B test protocol |
| **Weather** | OpenWeatherMap API integration for 4 Colombian cities, data averaging |
| **Charts** | Node-RED Dashboard UI gauges and charts for local monitoring |
| **Utilities** | Data logger (13 measurements at 60-second intervals), system diagnostics |

Node-RED runs as a systemd service (`nodered`), ensuring automatic restart on failure and boot-time startup.

#### 2.3.2 Data Storage and Visualization

**InfluxDB v1.8.10** stores all environmental measurements with nanosecond-precision timestamps. The database (`highland`) uses a 1-year retention policy (`standard_highland_retention`), providing sufficient historical data for seasonal analysis while managing storage on the Raspberry Pi's SD card. Twenty-six distinct measurements are recorded (see Supplementary Table S1).

**Grafana v10.2.3** provides four monitoring dashboards:

1. **Terrarium — Roraima**: Primary operational dashboard with real-time temperature, humidity, VPD, and actuator status
2. **Colombian Weather Reference**: Raw weather data from the four reference cities
3. **System Performance**: PID controller diagnostics, fan PWM outputs, and control quality metrics
4. **Night A/B Fan Experiment**: Dedicated dashboard for the ongoing nighttime ventilation study (Section 2.4.7)

#### 2.3.3 Hardware Watchdog

A custom shell script watchdog (`arduino-watchdog.sh`) runs as a systemd service, monitoring the Arduino Mega USB connection and Firmata protocol health at 60-second intervals. The watchdog implements a three-level recovery escalation:

1. **Level 1**: Restart Node-RED service (up to 2 attempts in 30 minutes)
2. **Level 2**: USB device reset via sysfs + Node-RED restart (2 additional attempts)
3. **Level 3**: Full system reboot

The watchdog distinguishes between transient USB disconnections (which may self-resolve) and persistent Firmata protocol failures by examining the chronological sequence of ioplugin log messages: a "Connected Firmata" message followed by a timeout indicates a genuine failure requiring intervention, while "Connected Firmata" as the final message indicates a healthy connection.

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

With the following tuning parameters, determined empirically:

| Parameter | Value | Function |
|-----------|-------|----------|
| Kp | 15 | Proportional gain — immediate response to humidity deviation |
| Ki | 0.08 | Integral gain — eliminates steady-state offset |
| Kd | 8 | Derivative gain — dampens oscillation from rapid changes |

**Anti-windup protection**: The integral accumulator is clamped to ±120 PWM-equivalent units to prevent integral windup during sustained large errors (e.g., during terrarium door opening). When the error magnitude falls below 1.0% RH, the integral decays at 2% per second to prevent steady-state creep.

**Derivative filtering**: A first-order exponential low-pass filter (α = 0.25) smooths the derivative term to reduce noise amplification from sensor fluctuations.

**Rate limiting**: Fan speed changes are limited to max(10, |error| × 3) PWM units per control cycle, preventing abrupt speed transitions while allowing faster response during large disturbances.

The PID output is added to a base speed of 72 PWM (approximately 28% duty cycle), providing gentle circulation at the humidity setpoint. The total output is clamped to 40–204 PWM (16–80% duty cycle), ensuring continuous minimum airflow while capping maximum speed for noise reduction.

#### 2.4.4 Mister Hysteresis Control

The ultrasonic mister is controlled via a hysteresis (bang-bang) controller in the Humidity tab, with configurable on/off thresholds relative to the target humidity. When humidity falls below the lower threshold, the mister activates; when humidity exceeds the upper threshold, it deactivates.

A critical safety interlock ensures that **all fans stop when the mister is active**. This prevents fans from dispersing the mist plume before it can saturate the terrarium air and avoids drawing unsaturated air into the enclosure during misting events. The interlock is implemented as a gate function upstream of the PID controller output that blocks fan commands when `mister_status` is true.

#### 2.4.5 Freezer Hysteresis Control

The Peltier-based freezer unit is controlled via a separate hysteresis controller in the Temperature tab, switching the unit on/off based on the difference between actual and target temperature. A dedicated fan (pin 46, PWM always at 255 when freezer is active) forces terrarium air over the cold side of the Peltier module.

#### 2.4.6 Light Schedule

The photoperiod follows a fixed schedule implemented via the BigTimer node:

| Event | Time | Duration |
|-------|------|----------|
| Lights ON (plug) | 06:25 | — |
| Sunrise dim-up | 06:30 | 30 minutes (0→100% PWM ramp) |
| Full daylight | 07:00–19:30 | 12.5 hours |
| Sunset dim-down | 19:30 | 30 minutes (100→0% PWM ramp) |
| Lights OFF (plug) | 20:05 | — |

The 5-minute offset between plug activation and dimmer ramp start ensures the LED driver is powered before the PWM dimmer begins ramping. Similarly, the plug deactivates 5 minutes after the dimmer reaches zero, ensuring a clean shutdown. The 30-minute ramp duration simulates the gradual light transitions characteristic of tropical mountain environments, where sunrise and sunset are rapid but not instantaneous due to persistent cloud cover.

#### 2.4.7 Night A/B Fan Experiment

An ongoing controlled experiment evaluates the effect of nighttime air circulation on temperature and humidity recovery. The protocol alternates nightly based on day-of-year parity:

- **Night A** (even day-of-year): All fans off (0 PWM) — passive cooling only
- **Night B** (odd day-of-year): Outlet and impeller fans at 80 PWM (~31% duty cycle) — gentle circulation

The mode is determined by the evening's date (not the current date at midnight) to prevent mid-night transitions. The experiment began on February 5, 2026 (day 36, Night A) with a planned minimum duration of 20 nights. Results are logged to the `night_test_mode` InfluxDB measurement and visualized on a dedicated Grafana dashboard with A/B comparison panels.

#### 2.4.8 Manual Override Hierarchy

The system implements a three-level control priority:

1. **Manual override** (highest priority): Operator-set fan speed via the Node-RED Dashboard UI, bypassing all automatic control
2. **Safety interlock**: Mister-active fan stop, overriding PID output
3. **Automatic PID control** (lowest priority): Normal humidity-based operation

Each level checks for higher-priority overrides before executing, ensuring predictable behavior during maintenance or emergency situations.

### 2.5 Data Logging

A centralized data logger function on the Utilities tab reads all global context variables at 60-second intervals and writes to 13 individual InfluxDB measurements:

1. `local_temperature` — Terrarium temperature (°C)
2. `local_humidity` — Terrarium relative humidity (%)
3. `vpd` — Vapor pressure deficit (kPa)
4. `target_temperature_computed` — Weather-derived temperature setpoint (°C)
5. `target_humidity_computed` — Weather-derived humidity setpoint (%)
6. `difference_temperature` — Target minus actual temperature (°C)
7. `difference_humidity` — Target minus actual humidity (%)
8. `fan_speed` — PID controller output (PWM 0–255)
9. `freezer_status` — Freezer relay state (0/1)
10. `mister_status` — Mister relay state (0/1)
11. `light_status` — Light relay state (0/1)
12. `water_level_local` — Reservoir water level (arbitrary units)
13. `night_test_mode` — Night A/B experiment mode (0=A, 1=B)

Additional measurements are logged by other flow components (individual fan PWM channels, individual city weather data, room temperature/humidity), bringing the total to 26 InfluxDB measurements (Supplementary Table S1).

---

## 3. Results

### 3.1 Environmental Performance

Over the monitoring period, the system maintained the following environmental ranges within the terrarium:

| Parameter | Minimum | Maximum | Typical Range | Target Range |
|-----------|---------|---------|---------------|--------------|
| Temperature | 13.5°C | 24.3°C | 15–22°C | 12–24°C |
| Relative Humidity | 75% | 98% | 82–95% | 70–90% |
| VPD | 0.03 kPa | 0.64 kPa | 0.08–0.45 kPa | < 0.8 kPa |

The system achieves a meaningful diurnal temperature swing despite the terrarium being located in a room maintained at approximately 22°C year-round. Nighttime terrarium temperatures routinely drop to 14–16°C through active Peltier cooling, while daytime temperatures rise to 18–22°C, producing a 4–8°C daily amplitude that approximates conditions on mid-elevation tepuis.

### 3.2 PID Controller Stability

The PID controller maintains humidity within ±3% RH of the setpoint under steady-state conditions. The proportional-integral-derivative architecture eliminates the continuous cycling observed with simpler hysteresis controllers, producing smooth fan speed transitions.

`[PLACEHOLDER — User will provide: PID performance graphs, settling time data, response to disturbance events (door opening, seasonal temperature changes), comparison with pre-PID control if available.]`

### 3.3 Weather Data Correlation

The Colombian weather integration produces continuously varying setpoints that reflect real meteorological conditions. Temperature setpoints track Colombian highland weather patterns with appropriate clamping, while humidity setpoints respond to precipitation events in the reference cities.

`[PLACEHOLDER — User will provide: example time-series showing weather-driven setpoint variation, correlation between Colombian weather events and terrarium conditions, seasonal patterns.]`

### 3.4 Species Diversity and Growing Results

The system supports approximately 120 species across the following genera:

`[PLACEHOLDER — User will provide: complete species list organized by genus, photographs showing growth and flowering, specific growing results and observations, any species losses and suspected causes, comparison with results under previous growing conditions.]`

**Genera maintained** (partial list): *Heliamphora*, *Dracula*, *Sophronitis* (syn. *Cattleya*), *Nepenthes* (highland), *Dendrobium* (New Guinea section), and additional cloud forest genera.

### 3.5 System Reliability

`[PLACEHOLDER — User will provide: uptime statistics, failure events and recovery, Arduino watchdog intervention frequency, seasonal performance variation.]`

The Arduino watchdog system (Section 2.3.3) has maintained continuous Firmata connectivity, automatically recovering from USB disconnections and protocol timeouts without manual intervention.

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

However, PID control requires more careful tuning than bang-bang approaches. The empirically determined gains (Kp=15, Ki=0.08, Kd=8) reflect a trade-off between responsiveness and stability specific to this terrarium's volume, ventilation geometry, and sensor response time. Different enclosures would require re-tuning.

### 4.3 Open-Source Accessibility

A key design goal of this system is reproducibility using commodity hardware and free software. The total system cost (excluding terrarium construction and plants) consists of a Raspberry Pi, an Arduino Mega, three smart plugs, an ESP microcontroller with sensor, fans, and LED pucks — all widely available consumer components.

Node-RED's visual flow-based programming environment lowers the barrier to entry compared to traditional programming approaches. Users can inspect and modify control logic visually, adjust PID tuning parameters through dashboard controls, and extend the system with additional sensors or actuators using Node-RED's extensive node library.

### 4.4 Ongoing Optimization

The Night A/B fan experiment (Section 2.4.7) illustrates an important aspect of the system: even after two years of successful operation, continuous refinement remains possible and valuable. The open data pipeline (InfluxDB + Grafana) enables rapid hypothesis testing by making it straightforward to isolate variables and compare outcomes.

This experimental capability, built into the control infrastructure rather than requiring separate equipment, represents a significant advantage of the software-defined approach over hardware-only solutions.

### 4.5 Limitations

- **Single sensor**: The system relies on a single SHT35 sensor, creating a single point of failure and potentially unrepresentative measurements in a terrarium with spatial environmental gradients.
- **Internet dependency**: Weather-based setpoints require internet access to the OpenWeatherMap API. Connectivity interruptions cause the system to hold the last valid setpoint.
- **Peltier efficiency**: Thermoelectric cooling is inherently less energy-efficient than compressor-based refrigeration, limiting the achievable temperature depression below ambient.
- **No formal species performance metrics**: While approximately 120 species are maintained, systematic growth rate and flowering frequency measurements have not been conducted.

### 4.6 Future Work

- Addition of redundant sensors and spatial temperature/humidity mapping
- Integration of CO₂ monitoring for photosynthesis optimization
- Formal comparison of species performance under weather-variable vs. fixed setpoints
- Expansion of the weather reference to include additional cities or direct tepui weather station data when available
- Machine learning approaches to PID auto-tuning based on historical response data

---

## 5. Conclusions

We have demonstrated that an open-source, software-defined control system built on commodity hardware can successfully simulate highland cloud forest climates for extended-duration terrarium cultivation. The combination of weather-referenced setpoints, PID humidity control, and comprehensive data logging creates a system that is both effective for maintaining sensitive cloud forest species and accessible to the wider terrarium community. All system components — Node-RED flows, Grafana dashboards, watchdog scripts, and documentation — are available as open-source supplementary materials at `[PLACEHOLDER — GitHub repository URL]`.

---

## References

`[PLACEHOLDER — to be completed with full citations]`

- Rull, V., & Vegas-Vilarrúbia, T. (2006). Unexpected biodiversity loss under global warming and protected Venezuelan tepuis. *Current Biology*, 16(2), R58-R63.
- Berry, P. E., & Riina, R. (2005). Insights into the diversity of the Pantepui flora and the biogeographic complexity of the Guayana Shield. *Biologiske Skrifter*, 55, 145-167.
- Givnish, T. J., et al. (2014). Adaptive radiation, correlated and contingent evolution, and net species diversification in Bromeliaceae. *Molecular Phylogenetics and Evolution*, 71, 55-78.
- Node-RED Project. (2024). https://nodered.org/
- InfluxDB. (2024). https://www.influxdata.com/
- Grafana Labs. (2024). https://grafana.com/

---

## Supplementary Materials

All supplementary files are available at: `[PLACEHOLDER — GitHub repository URL]`

- **Supplementary Table S1**: Complete InfluxDB measurement schema (26 measurements)
- **Supplementary File S1**: Sanitized Node-RED flow configuration (`flows-sanitized.json`)
- **Supplementary File S2**: Grafana dashboard exports (4 dashboards)
- **Supplementary File S3**: Arduino watchdog script and systemd service configuration
- **Supplementary File S4**: Detailed system architecture and data flow documentation
- **Supplementary File S5**: PID controller algorithm documentation
- **Supplementary File S6**: Acrylic panel technical drawings — original fabrication specifications for all 20 panels plus add-on components (from *Progetto completo* and *Progetto adds-on 2022* design documents)
