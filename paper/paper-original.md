---
output:
  pdf_document:
    latex_engine: xelatex
---

# Weather-Mimicking Terrarium for Convergent Cloud Forest Species: Open-Source Climate Simulation Using Colombian Highland Meteorological Data

**Authors**: `[PLACEHOLDER — author names and affiliations]`

**Corresponding author**: `[PLACEHOLDER — email]`

---

## Abstract

We describe a weather-mimicking terrarium system that cultivates approximately 120 plant species from convergent cloud forests on five continents — Venezuelan tepuis, the Colombian and Ecuadorian Andes, the highlands of Papua New Guinea, the Brazilian Atlantic Forest, and montane Borneo-Sumatra — within a single 1.5 x 0.6 x 1.1 m enclosure in Genoa, Italy. The system ingests real-time meteorological data from four Colombian highland cities (1,300-2,600 m elevation) and applies a 15-hour time shift to generate continuously varying temperature and humidity setpoints, reproducing the stochastic weather dynamics of tropical montane environments rather than static fixed-point control. A dynamic photoperiod derived from the Colombian reference latitude (~5 deg N) provides seasonally varying day length that tracks the natural cycle at the weather source. The co-cultivation of species from geographically disjunct cloud forests demonstrates that these ecosystems converge on similar climatic envelopes worldwide, allowing species from separate evolutionary lineages to coexist under shared conditions. A three-regime fan control strategy adapts the PID controller's error signal based on temperature: humidity-driven control under normal conditions, temperature-driven evaporative cooling in a 24-25 deg C transition band before the compressor activates, and humidity-driven control with active mechanical refrigeration above 25 deg C. A wet-bulb temperature analysis revealed that evaporative fan cooling becomes counterproductive when the terrarium temperature drops below the room's wet-bulb temperature (~16.6 deg C), at which point the system automatically disengages ventilation fans and relies solely on compressor-based refrigeration. The control system, built entirely on open-source software (Node-RED, InfluxDB, Grafana) running on a Raspberry Pi with an Arduino Mega for hardware I/O, has operated continuously for over three years with minimal human intervention. All control flows, firmware, dashboards, and analysis scripts are provided as supplementary materials.

**Keywords**: cloud forest terrarium, convergent evolution, weather simulation, wet-bulb temperature, dynamic photoperiod, highland carnivorous plants, three-regime PID control, Node-RED, open-source horticulture

---

## 1. Introduction

Highland cloud forests — from the tepui table-top mountains of the Guiana Highlands in Venezuela to the Andes, the highlands of Papua New Guinea, and montane Borneo-Sumatra — harbor extraordinary plant diversity adapted to narrow environmental envelopes: cool temperatures (10-22 deg C), persistent high humidity (80-100% RH), frequent fog immersion, and moderate light filtered through clouds (Rull & Vegas-Vilarrubia, 2006). At higher elevations, particularly on tepui summits above 2,500 m, nighttime temperatures can drop below 5 deg C and occasionally approach freezing. Cultivating these species outside their native range — especially in Mediterranean climates with hot, dry summers — presents formidable challenges for both botanical institutions and private growers.

The central difficulty is nighttime cooling. While maintaining high humidity in a sealed terrarium is straightforward, achieving the 4-8 deg C nocturnal temperature drops characteristic of tropical highlands — in a room at 22 deg C — requires active refrigeration. Previous approaches to this problem have included evaporative cooling (limited by room wet-bulb temperature, as this paper demonstrates), thermoelectric (Peltier) modules (insufficient cooling capacity for enclosures larger than approximately 50 liters), and portable air conditioning units (oversized, noisy, and difficult to integrate with humidity control). Compressor-based marine refrigeration, as used in this system, provides sufficient cooling power to drive terrarium temperatures below the room's wet-bulb temperature — a regime inaccessible to evaporative methods — while being compact enough for domestic installation.

Traditional terrarium approaches also rely on fixed environmental setpoints (e.g., 18 deg C day / 14 deg C night, 90% RH constant), which fail to capture the dynamic variability that characterizes cloud forest environments. Natural cloud forest climates exhibit stochastic weather-driven fluctuations: sudden temperature drops during rain events, diurnal fog cycles, and seasonal variation in cloud cover. Static control not only oversimplifies the environment but may fail to provide the thermal and humidity cues that many cloud forest species require for phenological processes including flowering and seed set.

This paper describes an open-source control system that addresses these limitations through five key innovations:

1. **Weather-mimicking from real Colombian data**: Rather than programming fixed targets, the system ingests real-time meteorological data from four Colombian highland cities (Chinchina, Medellin, Bogota, Sonson) at elevations of 1,300-2,600 m, applying a 15-hour time shift to align South American daytime weather with European nighttime conditions and vice versa. This produces naturalistic, continuously varying setpoints within biologically appropriate ranges, including stochastic perturbations from rain events and seasonal shifts that would be impossible to replicate with fixed schedules. The photoperiod is also derived from the Colombian reference latitude, providing seasonally varying day length that tracks the natural cycle at the weather source (Section 2.4.6).

2. **Convergent cloud forest concept**: Cloud forests worldwide — from Venezuelan tepuis to the Colombian Andes, the highlands of Papua New Guinea, the Brazilian Atlantic Forest, and montane Borneo-Sumatra — converge on remarkably similar climatic envelopes despite their geographic isolation. This convergence means that species from separate evolutionary lineages share broadly compatible environmental tolerances. A single terrarium tuned to the common envelope of cloud forest conditions can therefore support species from multiple continents simultaneously, a principle we have validated over three years of co-cultivation with approximately 120 species.

3. **Three-regime temperature/humidity fan control**: The PID controller adapts its error signal based on temperature conditions. Under normal conditions (below 24 deg C), fans are driven by humidity error. In a 24-25 deg C transition band, the controller switches to temperature-driven mode, attempting evaporative cooling before the energy-intensive compressor activates. Above 25 deg C, mechanical refrigeration engages and the controller reverts to humidity-driven fan control (Section 2.4.3).

4. **Wet-bulb temperature insight**: Evaporative cooling via ventilation fans is thermodynamically limited by the room's wet-bulb temperature. When the terrarium temperature drops below this threshold — typically around 20:00-21:00 each evening — fans cease to provide cooling and instead inject warm, humid room air that the compressor must then fight. The system now detects this crossover automatically and disengages ventilation fans, relying solely on mechanical refrigeration for overnight cooling.

5. **Complete open-source stack**: Every component — from the control logic (Node-RED), to the time-series database (InfluxDB), to the monitoring dashboards (Grafana) — uses freely available, community-supported software running on a single Raspberry Pi. A PID humidity controller with gain scheduling provides smooth fan speed modulation, and comprehensive data logging enables both operational monitoring and experimental analysis. This makes the system reproducible by hobbyists and small institutions without proprietary hardware or licensing costs.

The system has maintained approximately 120 species from multiple cloud forest genera in a 1.5 x 0.6 x 1.1 m terrarium in Genoa, Italy for over three years, demonstrating long-term reliability and horticultural effectiveness.

---

## 2. Materials and Methods

### 2.1 Terrarium Construction

The terrarium is a custom-built acrylic enclosure designed as a weather-mimicking biotope for highland cloud forest species. This section describes the physical construction.

#### 2.1.1 Supporting Scaffold and Placement

The terrarium is placed in an area of the apartment that does not receive direct sunlight, avoiding solar heat gain that would increase cooling load and risk overheating during system failures. The supporting scaffold is a semi-industrial weatherproof aluminum alloy unit (2.20 m high x 3.20 m wide x 0.50 m deep, approximately 300 kg). Aluminum alloy is preferred over wood for its corrosion resistance, non-combustibility, and structural rigidity — a wooden scaffold used in an earlier iteration suffered waterproof coating degradation and swelling after four years in the high-humidity environment. All electrical lines incorporate drip loops (U-shaped cable routing below connection points) to prevent water ingress to outlets, following standard aquarium practice.

#### 2.1.2 Choice of Enclosure Material

Three materials were evaluated for the enclosure: tempered glass, polycarbonate (Lexan), and polymethylmethacrylate (PMMA/acrylic, Plexiglas). The selection criteria included optical transparency, thermal conductivity (lambda-value), impact resistance, weight, machinability (drilling and cutting), chemical resistance, fire resistance, UV stability, and cost.

| Property | Tempered Glass | Polycarbonate | Acrylic (PMMA) |
|----------|---------------|---------------|----------------|
| Transparency | Good | ~88% | Highest |
| Thermal conductivity | Variable | 0.19-0.22 W/mK | 0.19-0.22 W/mK |
| Impact resistance | Low | Excellent (200x glass) | Moderate |
| Weight | Heaviest | Medium | Lightest |
| Machinability | Non-drillable | Easy | Easy |
| Fire resistance | Fireproof | Good | Combustible |
| UV/yellowing | Good | Yellows over time | Good long-term |
| Cost | Highest | Medium | Lowest |

Acrylic (PMMA) was selected for its superior transparency, low weight, ease of modification, and lower cost. Its drawbacks — lower impact resistance and combustibility — were judged acceptable given the indoor, controlled environment.

**Assembly methods**: Acrylic panels can be solvent-welded using dichloromethane (DCM), which fuses panels into a monolithic structure within seconds. However, DCM is highly volatile, toxic (possible carcinogen), and will permanently stain acrylic wherever it contacts the surface unintentionally. The enclosure uses laser-cut panels with DCM solvent welding plus crystalline silicone (c-Si) sealant, achieving a watertight enclosure verified by a one-week flood test with 30 liters of water. Critically, acetoxy silicones (a-Si) must never be used with acrylic, as they release acetic acid that corrodes and permanently stains the material.

#### 2.1.3 Enclosure Dimensions and Zones

The enclosure measures 150 cm wide x ~60 cm deep x 110 cm high (external dimensions), weighing approximately 100 kg empty. All structural panels are laser-cut for precise edge smoothness required by DCM solvent welding. Thermal insulation (1 cm XPS with diamond Mylar) is applied to the exterior of the enclosure, leaving the interior surfaces smooth for easier cleaning and maximizing usable internal volume. Access is via two sliding front panels on alloy guides with c-Si adhesion.

The 110 cm height creates three distinct climatic zones via a mid-height perforated acrylic shelf:

1. **Upper zone** (above shelf, high light): *Heliamphora* species, *Brocchinia reducta*, and high-light miniature orchids
2. **Middle zone** (shelf level, intermediate light): Epiphytic *Utricularia* (*U. alpina*, *U. campbelliana*, *U. quelchii*) in kokedama-style sphagnum, and intermediate-light orchids
3. **Lower zone** (below shelf, low light, coolest): *Dracula* orchids, *Phragmipedium*, *Restrepia*, highland *Nepenthes*, and highland ferns such as *Lecanopteris*

#### 2.1.4 Acrylic Panel Specifications

The enclosure was constructed from 20 laser-cut acrylic (PMMA) panels plus 6 structural triangles, fabricated according to detailed technical drawings (see Supplementary File S6). All dimensions below are in centimeters unless otherwise noted. All cuts are laser-squared unless otherwise specified.

**Table 1.** Main structural panels.

| Panel(s) | Qty | Dimensions (W x H) | Thickness | Material | Function |
|-----------|-----|---------------------|-----------|----------|----------|
| 1 | 1 | 145 x ~55 | 10 mm | Clear acrylic | Floor panel |
| 2 | 1 | 145 x ~115 | 10 mm | Clear acrylic | Back wall (with 2x 12 cm and 2x 2 cm circular holes for ventilation and cable pass-throughs) |
| 3 | 1 | 145 x 115 | 10 mm | Clear acrylic | Inner back / shelf support (with 1x 3 cm hole at 6.5 cm from left, 20 cm from bottom) |
| 4, 5 | 2 | 49 x 115 | 10 mm | Clear acrylic | Side panels (with 2x 10 cm notches on left edge, and holes: 1x 6 cm at 20 cm right / 4 cm up, 2x 1.6 cm for cable pass-throughs) |
| 6, 7 | 2 | 73.5 x 94.6 | 8 mm | Clear acrylic | Sliding front access panels (with 1x 1.5 cm hole at 10 cm from right, 46.6 cm from bottom) |
| 8, 9 | 2 | 145 x 10 | 20 mm | Clear acrylic | Bottom rail / shelf support tracks |

**Table 2.** Internal shelf and structural panels.

| Panel(s) | Qty | Dimensions | Thickness | Material | Function |
|-----------|-----|------------|-----------|----------|----------|
| 10, 11 | 2 | 57 x 46.5 and 71.5 x 46.5 | 8 mm | Perforated clear acrylic (Square 15 pattern) | Mid-height shelf floor (allows air and water circulation between upper and lower zones) |
| 12 | 1 | 123 x varies | 5 mm | Clear acrylic | Shelf front lip (with 3x 12 cm holes at 1 cm from top, spaced 34.5 cm apart, 9 cm from edges) |
| 13 | 1 | 123 x varies | 5 mm | Clear acrylic | Shelf structural support |
| 14, 15 | 2 | 51.5 x 6 | 5 mm | Clear acrylic | Shelf side brackets |
| Triangles | 6 | Triangular | 5 mm | Clear acrylic | Corner reinforcement brackets |

**Table 3.** Reflective and decorative panels.

| Panel(s) | Qty | Dimensions | Thickness | Material | Function |
|-----------|-----|------------|-----------|----------|----------|
| 16-20 | 5 | Various (see Supplementary File S6) | 2 mm | Silver mirror acrylic | Interior reflective surfaces for light distribution |

The back wall (Panel 2) features two pairs of circular holes: two 12 cm diameter holes positioned at 33 cm and 100 cm from the lower-left corner and 19 cm above the base serve as primary ventilation ports (fan mounting points for the outlet and impeller fans); two 2 cm diameter holes near the top edge (at 38 cm and 105 cm from the left, 2 cm below the top) provide cable pass-throughs for sensor wiring and power lines.

The side panels (Panels 4 and 5) incorporate 2 x 10 cm rectangular notches along the left edge to accommodate the sliding front panel guide rails. Each side panel has a 6 cm hole (20 cm from the notch corner, 4 cm up) for additional ventilation or drainage, plus two 1.6 cm cable pass-through holes.

#### 2.1.5 2022 Add-On Panels

A supplementary set of panels was fabricated in 2022 to add light-blocking, ventilation, and reflective elements:

**Table 4.** Add-on panels (2022 revision).

| Component | Qty | Dimensions (cm) | Thickness | Material | Function |
|-----------|-----|------------------|-----------|----------|----------|
| Panel A | 1 | 40 x 37 | 4 mm | Black acrylic | Light-blocking baffle |
| Panel B | 2 | 33 x 30 | 4 mm | Black acrylic | Light-blocking side baffles |
| Panel C | 1 | 65 x 40 | 4 mm | Black acrylic | Upper light shield |
| Panel D | 1 | 85 x 60 x 25 (stepped) | 4 mm | Black acrylic | Rear light/heat shield |
| Perforated E | 1 | 155 x 30 | 3 mm | Perforated clear acrylic (Square 15) | Ventilation grille |
| Perforated F | 1 | 153 x 24 | 3 mm | Perforated clear acrylic (Square 15) | Ventilation grille |
| Mirror G | 1 | 153 x varies | 2 mm | Silver mirror acrylic | Additional reflective surface |
| Mirror H | 1 | See drawings | 2 mm | Silver mirror acrylic | Additional reflective surface |
| Trapezoids | 6 | 55 x 13 x 2.5 (trapezoidal) | 3 mm | Clear acrylic | Light diffusion elements |

The black acrylic panels serve as light baffles to prevent light leakage from the LED pucks into the room and to block direct light from reaching heat-sensitive species in the lower zone. The additional perforated panels improve passive airflow, while the mirror panels increase light utilization efficiency by reflecting otherwise lost photons back into the growing volume.

#### 2.1.6 Drainage and Water Management

Two separate 40-liter reservoirs sit below the terrarium on the lowest shelf of the scaffold. The first reservoir supplies the MistKing misting pump; the second collects condensate from the evaporator plate. The PT14 evaporator (Section 2.2.2) generates condensate that drains via a small channel below the evaporator into the condensate reservoir by gravity. Misting runoff drains through the terrarium floor — the floor panel is slightly tilted toward a rear drainage hole — and is collected in the same condensate reservoir.

Water level in the misting reservoir is monitored by an ESP8266 microcontroller paired with an HC-SR04 ultrasonic distance sensor mounted at the top of the reservoir. The sensor measures the air gap above the water surface, from which the water level is calculated and published via MQTT. This provides a low-water alert on the Node-RED Dashboard and is logged to InfluxDB as the `water_level_local` measurement.

#### 2.1.7 Substrate and Planting Layout

The planting layout exploits the three climatic zones created by the mid-height shelf (Section 2.1.3):

**Epiphytes** — *Dracula*, *Masdevallia*, *Sophronitis* (syn. *Cattleya*), *Leptotes*, *Vanda pumila*, and New Guinea *Dendrobium* (including *D. victoriae-reginae*) are mounted on virgin cork bark slabs and tree fern plaques using sphagnum moss pads secured with monofilament line. Cork bark is preferred for its longevity in high-humidity conditions; tree fern is used for species that benefit from a consistently moist root zone. Mounted plants hang from stainless-steel hooks on the back wall and side panels across all three zones.

**Highland carnivorous plants** — *Heliamphora* species and *Brocchinia reducta* are grown in the upper zone in a substrate of akadama and long-fiber sphagnum, topped with a layer of living *Sphagnum* moss that maintains surface moisture while the mineral akadama component provides drainage and structural stability. This combination approximates the acidic, low-nutrient, free-draining conditions of tepui summit soils. Epiphytic *Utricularia* of section *Orchidioides* (*U. alpina*, *U. quelchii*, and *U. campbelliana*) are grown kokedama-style — wrapped in balls of living *Sphagnum* moss suspended from the shelf — where they produce their characteristic orchid-like flowers and stolons. Highland *Nepenthes* species are planted in kanuma (Japanese volcanic pumice) mixed with long-fiber sphagnum and placed directly on the terrarium floor without saucers, where the cooler temperatures and high ambient humidity support active pitcher production. The absence of saucers prevents waterlogging while the terrarium's persistently high humidity eliminates the need for supplementary moisture trays.

The emphasis throughout is on drainage and airflow: no substrate sits in standing water, all mounts allow air circulation around roots, and the perforated shelf permits vertical air movement between zones.

### 2.2 Hardware Components

#### 2.2.1 Lighting

Four ChilLED Logic Puck V3 LED modules provide illumination, each rated at approximately 100 W (400 W total nameplate). The pucks use Samsung LM301B diodes (244 per puck), which offer high photosynthetic photon efficacy (~2.5 umol/J at chip level) across a broad spectrum suitable for plant growth. Each puck is mounted on a 140 mm aluminium pin heatsink for passive thermal management. Supplementary 12 V axial fans are mounted above the heatsinks to increase convective dissipation, ensuring that LED junction temperatures remain within specification. The pucks and heatsinks reside above the terrarium enclosure, so their thermal output does not contribute to the internal heat load.

The four pucks are wired in parallel and powered by a Mean Well HLG-480H-48A LED driver (480 W, 48 V / 10 A, 95% efficiency, IP65-rated). The driver provides constant-voltage output to the pucks. Master power is switched by a TP-Link Tapo P100 smart plug (192.168.1.55), and intensity is controlled via an Arduino Mega PWM output on pin 8 that drives the driver's analog dimming input. The heatsink fans run directly from the 12 V supply and are not under microcontroller control.

During normal operation, the pucks run at 40-60% of slider range (corresponding to slider positions 40-60 in the Node-RED Dashboard). Due to the two-stage dimming system described in Section 2.6, the actual power output is approximately 24-36% of the LEDs' full rated capacity. A midday intensity boost (Section 2.4.6) ramps from 40% to 60% over 30 minutes, holds for approximately 2.5 hours centered on midday, then ramps back down, simulating the brief clearing events common on tepui summits.

#### 2.2.2 Cooling System

The cooling system is based on a Vitrifrigo ND50 OR2-V marine refrigeration unit, which uses a BD50F Danfoss variable-speed compressor (12/24 V DC, 31 W nominal draw) with R404a refrigerant. The compressor unit measures 360 x 155 x 135 mm and sits on the shelf below the terrarium.

The evaporator is a Vitrifrigo PT14 stainless steel plate (1220 x 280 mm), mounted vertically on the back wall of the terrarium at mid-height. Cold refrigerant circulates through the plate, cooling the surrounding air. Condensate forms on the plate surface and drains via gravity into the condensate reservoir below (Section 2.1.6).

Three Noctua NF-F12 iPPC-2000 IP67 fans (120 mm, 2000 RPM, 12 V) are evenly spaced on a plexiglas plate mounted in front of the evaporator. The plate is inclined at approximately 30 degrees from vertical, so that warm terrarium air is drawn against the cold evaporator surface and the cooled air is directed downward through a slit between the bottom of the plate and the terrarium wall. These evaporator fans are controlled via Arduino PWM pin 44 (Timer 5, 25 kHz) and run at 255 PWM when the compressor is active (maximum airflow across the evaporator) and 168 PWM when the compressor is off (gentle circulation to prevent thermal stratification).

The compressor unit also includes a condenser with radiator fins that must reject the heat extracted from the terrarium plus the compressor's own waste heat. The original equipment fans were replaced in February 2026 with a pair of Noctua NF-A12x25 G2 PWM fans in a push-pull configuration on the condenser radiator, which produced a measurable improvement in cooling depth (Section 3.1). These condenser fans are not under Arduino control; they run whenever the compressor unit is powered.

An additional pair of internal circulation fans (Noctua NF-F12 iPPC-2000 IP67, 120 mm, 2000 RPM, 12 V) are mounted inside the terrarium to promote general air movement past the evaporator plate and throughout the enclosure. These run on Arduino pin 12 (Timer 1, 25 kHz) and follow the same control schedule as the evaporator fans: 168 PWM when the compressor is off (gentle circulation) and 255 PWM when the compressor is active (maximum cold air distribution from the evaporator).

The compressor is switched on and off via a TP-Link Tapo P100 smart plug (192.168.1.196), driven by a hysteresis controller in the Temperature tab (Section 2.4.5). Total system power consumption is monitored by a Meross MSS310 energy-monitoring smart plug at 192.168.1.92, which reports instantaneous wattage to Node-RED every 2 minutes.

#### 2.2.3 Humidification

The humidification system uses a MistKing Standard diaphragm pump (24 V), which pressurizes water from the 40-liter misting reservoir and delivers it through a network of nozzles inside the terrarium. A ZipDrip anti-drip valve on the main line prevents residual dripping between misting events. The system produces a fine fog with an approximate droplet size of 50 um.

The nozzle array consists of 20 nozzle points distributed across the terrarium ceiling: one quadruple-nozzle assembly, six double-nozzle assemblies, and four single nozzles, providing even fog coverage across the enclosure volume. The MistKing pump is powered via a TP-Link Tapo P100 smart plug (192.168.1.199) and controlled by a hysteresis algorithm in the Humidity tab (Section 2.4.4).

A critical safety interlock ensures that all fans stop when the mister is active (Section 2.4.4), preventing the fog plume from being dispersed before it can saturate the terrarium air.

#### 2.2.4 Air Circulation

Four groups of PWM-controlled fans are connected to an Arduino Mega 2560 via a custom serial protocol (Section 2.2.6):

- **Outlet fan** (PWM pin 45): Noctua 60 mm fan exhausting humid air from the terrarium through a rear ventilation port
- **Impeller fan** (PWM pin 46): Noctua 60 mm fan drawing external air into the terrarium through the opposite ventilation port
- **Evaporator fans** (PWM pin 44): Three Noctua NF-F12 iPPC-2000 IP67 fans (120 mm) on a plexiglas plate in front of the evaporator (Section 2.2.2)
- **Circulation fans** (PWM pin 12): Two Noctua NF-F12 iPPC-2000 IP67 fans (120 mm) for general internal air movement

All fan PWM signals use 25 kHz phase-correct PWM generated by hardware timers on the Arduino Mega: Timer 5 drives pins 44, 45, and 46, while Timer 1 drives pin 12. The 25 kHz frequency is above the audible range, avoiding acoustic noise from the switching frequency.

Because each PWM channel drives multiple fans in parallel, the Arduino PWM outputs do not connect directly to the fans' 4-pin PWM signal inputs. When multiple 4-pin fans share a single PWM signal line, their internal pull-up resistors and input capacitances interact, causing unreliable speed control. Instead, each fan group is driven through an IRF520N MOSFET driver module that switches the fan supply rail (12 V for all fan groups). The Arduino's 5 V PWM output drives the MOSFET gate, and the MOSFET switches power to all fans in the group simultaneously. This power-switching approach eliminates inter-fan signal interference and provides clean speed control regardless of the number of fans per channel. An alternative approach for single-fan configurations would be to drive the 4-pin PWM input directly, using 220 ohm series resistors to isolate individual fan inputs when multiple fans share a signal line.

The outlet and impeller fans are governed by the PID controller during daytime (Section 2.4.3), with PWM constrained to 50-230 (20-90% duty cycle) via gain scheduling. The evaporator and circulation fans follow the compressor state: 168 PWM (gentle circulation) when the compressor is off, 255 PWM (maximum airflow) when the compressor is active, and 0 PWM during misting events.

#### 2.2.5 Sensing

The primary environmental sensor is a Sensirion SHT35 digital temperature and humidity module (+/-0.1 deg C, +/-1.5% RH accuracy), connected to an ESP8266 microcontroller that publishes readings over MQTT at approximately 1-second intervals. The sensor is positioned at mid-canopy height (~50 cm above the terrarium floor), roughly centered in the enclosure to provide representative readings across the growing volume.

The same ESP8266 board also reads an HC-SR04 ultrasonic distance sensor mounted above the misting reservoir to monitor water level (Section 2.1.6).

A separate room-environment sensor — another SHT module connected to a DietPi-based Raspberry Pi at 192.168.1.94 — provides ambient room temperature and humidity readings. The main control Pi polls this remote sensor via HTTP every 60 seconds, storing the values in InfluxDB as `room_temperature` and `room_humidity`. These room readings serve as covariates for environmental analysis, provide the inputs for wet-bulb temperature calculation (Section 2.4.11), and are displayed alongside terrarium data on the Dashboard charts.

#### 2.2.6 Control Hardware

- **Raspberry Pi** (ARMv8, Debian-based): Runs all software services (Node-RED, InfluxDB, Grafana, MQTT broker, watchdog)
- **Arduino Mega 2560**: GPIO interface via a custom text-based serial protocol at 115200 baud over USB (`/dev/ttyACM0`). The protocol uses newline-terminated ASCII commands: `P<pin>,<value>` for PWM output, `Q` for status query, `H,<value>` for heartbeat, and `D<pin>,<0|1>` for door state. This replaced the StandardFirmata protocol in February 2026 for improved reliability and debuggability (see Supplementary File S7 for the full Arduino sketch)
- **TP-Link Tapo P100 smart plugs** (x3): Switched mains power for lights (192.168.1.55), mister (192.168.1.199), and compressor (192.168.1.196), controlled via the PyP100 Python library from within Node-RED Python function nodes
- **Meross MSS310 smart plug**: Energy-monitoring plug at 192.168.1.92 on the master power line, reporting instantaneous power consumption via the Meross cloud API every 2 minutes
- **ESP8266 microcontroller**: Sensor data acquisition (SHT35 + ultrasonic water level) and MQTT publication
- **IRF520N MOSFET driver modules** (x4): One per fan group, switching the fan supply rail (12 V or 24 V) under 25 kHz PWM control from the Arduino (see Section 2.2.4)
- **Reed switches** (x2): Magnetic door sensors on both sliding front panels, wired to Arduino digital inputs D22 (left) and D24 (right) with internal pull-up resistors

### 2.3 Software Architecture

The control system employs a layered architecture (Figure 1) running entirely on a single Raspberry Pi:

```
+--------------------------------------------------------------+
|                       Grafana v10.2                           |
|                 (Visualization, port 3000)                    |
+--------------------------------------------------------------+
|                      InfluxDB v1.8                            |
|               (Time-series storage, port 8086)                |
+--------------------------------------------------------------+
|                     Node-RED v3.1.3                           |
|            (Control logic engine, port 1880)                  |
|  +---------+----------+----------+------------------------+  |
|  | Lights  | Humidity |   Temp   |     Fans               |  |
|  |   Tab   |   Tab    |   Tab    | PID + Door Safety      |  |
|  +---------+----------+----------+------------------------+  |
|  | Weather |  Charts  | Utilities|                        |  |
|  |   Tab   |   Tab    |   Tab    |                        |  |
|  +---------+----------+----------+------------------------+  |
+----------+------------------+---------------+-----------------+
|   MQTT   |  Custom Serial   |   PyP100      |  Meross Cloud   |
| (:1883)  | (USB, 115200)    |  (TCP/IP)     |    (HTTPS)      |
+----------+------------------+---------------+-----------------+
|  ESP +   |  Arduino Mega    | Tapo P100 x3  |  Meross MSS310  |
|  SHT35   | 5 PWM + 2 doors  | light/mist/   |  (power meter)  |
|  sensor  |  + heartbeat     |  compressor   |                 |
+----------+------------------+---------------+-----------------+
```

**Figure 1.** System architecture showing the software stack (top) and hardware interfaces (bottom).

#### 2.3.1 Node-RED Control Engine

Node-RED v3.1.3, a flow-based visual programming environment built on Node.js, serves as the central control engine. The control logic is organized across seven flow tabs:

| Tab | Function |
|-----|----------|
| **Lights** | Dynamic photoperiod calculator, unified light scheduler, PWM sunrise/sunset/midday dimming ramps, startup recovery |
| **Humidity** | Sensor data ingestion (MQTT), VPD calculation, target humidity from weather data, mister hysteresis control |
| **Temperature** | Target temperature from weather data, compressor hysteresis control |
| **Fans** | Gain-scheduled PID controller, door safety mode, wet-bulb temperature gate, manual override, mister safety interlock |
| **Weather** | OpenWeatherMap API integration for 4 Colombian cities, data averaging, weather fallback |
| **Charts** | Node-RED Dashboard UI gauges and charts for local monitoring, room data overlay |
| **Utilities** | Data logger (16 measurements at 60-second intervals), serial parser, Meross power monitoring, system diagnostics |

Node-RED runs as a systemd service (`nodered`), ensuring automatic restart on failure and boot-time startup.

#### 2.3.2 Data Storage and Visualization

**InfluxDB v1.8.10** stores all environmental measurements with nanosecond-precision timestamps. The database (`highland`) uses a 1-year retention policy (`standard_highland_retention`), providing sufficient historical data for seasonal analysis while managing storage on the Raspberry Pi's SD card. Thirty-two distinct measurements are recorded (see Supplementary Table S1).

**Grafana v10.2.3** provides four monitoring dashboards:

1. **Terrarium — Roraima**: Primary operational dashboard with real-time temperature, humidity, VPD, and actuator status
2. **Colombian Weather Reference**: Raw weather data from the four reference cities
3. **System Performance**: PID controller diagnostics, fan PWM outputs, and control quality metrics
4. **Night A/B Fan Experiment**: Dedicated dashboard for the nighttime ventilation study (Section 2.4.7), now serving as historical reference

#### 2.3.3 Hardware Watchdog

A custom shell script watchdog (`arduino-watchdog.sh`, v10) runs as a systemd service, monitoring the Arduino Mega USB connection and serial communication health at 15-second intervals. The watchdog performs a four-step health check:

1. USB device `/dev/arduino` exists (device enumeration via udev symlink)
2. Node-RED systemd service is active
3. Node-RED has the serial port open (`lsof` check)
4. GPIO heartbeat is alive (last `arduino_status` value in InfluxDB within 30 seconds)

Recovery strategy depends on the failure type. For Node-RED process failures (steps 2-3), the watchdog attempts Node-RED restarts. For heartbeat failures (step 4), the watchdog performs a USB sysfs reset by toggling the `authorized` attribute of the Arduino's USB port, which resets the USB-serial bridge without a full system reboot. The Arduino re-enumerates within approximately 15 seconds, and Node-RED reconnects automatically. A 60-second cooldown between recovery attempts prevents reset loops.

### 2.4 Control Algorithms

#### 2.4.1 Weather Data Integration and Setpoint Generation

The system queries the OpenWeatherMap API at regular intervals for current weather conditions at four Colombian highland cities:

| City | Elevation | Role |
|------|-----------|------|
| Chinchina | ~1,300 m | Warm reference |
| Medellin | ~1,500 m | Mid-elevation reference |
| Sonson | ~2,475 m | Cool reference |
| Bogota | ~2,640 m | Cool/high reference |

The choice of Colombian highland cities was driven by necessity: historical tepui meteorological data was not available as a real-time API when the project began. These cities were selected because their real-time weather closely mimics tepui and cloud forest conditions in temperature, humidity, and diurnal range. Critically, the Colombian cities lie at approximately 5 deg N latitude — the same hemisphere as the Venezuelan tepuis (5-6 deg N) and close to the terrarium's location in Genoa (44 deg N, but with a 15-hour time shift that preserves the seasonal phase). This latitudinal alignment means the seasonal photoperiod variation at the weather source matches the natural photoperiod of the target biome, providing a coherent basis for the dynamic photoperiod calculation (Section 2.4.6).

Temperature and humidity values from these cities are averaged and then clamped to safe operating ranges: 12-24 deg C for temperature and 70-90% for relative humidity. These bounds prevent the compressor from running continuously during cold nights (which would exceed its duty cycle) while still permitting the naturally low nighttime temperatures and high humidity that characterize cloud forest conditions.

A **15-hour time shift** is applied to align Colombian daytime weather (UTC-5) with Genoa nighttime (UTC+1), producing the desired pattern where terrarium nighttime temperatures correspond to the current Colombian daytime conditions. This creates naturalistic diurnal variation: the terrarium experiences cooler conditions at night (when Colombian daytime mountain temperatures are moderate) and warmer conditions during the day.

Two stages of averaging smooth the setpoints. The InfluxDB query retrieves data from a 30-minute window centered on the 15-hour mark, and a rolling mean across the last 60 readings from all four cities (~15 minutes of incoming data) further damps transient API fluctuations. Because the data is already 15 hours old, this aggressive smoothing incurs no responsiveness penalty while preserving meaningful weather changes (e.g., rain events producing sudden cooling and humidity spikes that translate into the terrarium environment).

#### 2.4.2 Vapor Pressure Deficit Calculation

Vapor Pressure Deficit (VPD) is calculated continuously from temperature (*T*, deg C) and relative humidity (*RH*, %) using the Magnus formula:

**Saturated Vapor Pressure (SVP)**:

    SVP = 0.6108 * exp(17.27 * T / (T + 237.3))    [kPa]

**Actual Vapor Pressure (AVP)**:

    AVP = SVP * (RH / 100)    [kPa]

**Vapor Pressure Deficit**:

    VPD = SVP - AVP    [kPa]

Cloud forest species generally thrive at VPD values below 0.4 kPa, corresponding to near-saturation conditions. The system logs VPD continuously, providing a physiologically meaningful metric for assessing environmental suitability beyond simple humidity readings.

#### 2.4.3 Three-Regime PID Fan Controller

The core fan control algorithm is a discrete PID controller that modulates outlet and impeller fan speed, operating in one of three regimes depending on the terrarium temperature:

| Regime | Temperature | Error Signal | Freezer | Rationale |
|--------|------------|--------------|---------|-----------|
| **Normal** | < 24 deg C | Humidity error | Per weather target | Standard humidity-driven control |
| **Warm** | 24-25 deg C, freezer off | Temperature error | Delayed | Attempt evaporative cooling before compressor |
| **Hot** | >= 25 deg C | Humidity error | Active | Compressor handles temperature; fans manage humidity |

In **normal mode** (the predominant operating regime during most of the year), the error signal is:

    error = current_humidity - target_humidity

A positive error (too humid) increases fan speed to accelerate air exchange; a negative error (too dry) reduces fan speed, allowing the mister to raise humidity without opposition.

In **warm mode**, when the terrarium temperature rises above 24 deg C but the compressor has not yet activated, the controller switches to a temperature-based error signal:

    error = (current_temperature - 24.0) * TEMP_ERROR_SCALE

where TEMP_ERROR_SCALE = 5 maps a 0-1 deg C temperature excess into 0-5 PID-equivalent units, comparable to typical humidity errors of 0-5% RH. This allows the PID to ramp fans aggressively to attempt evaporative cooling before the energy-intensive compressor activates. The freezer activates when the terrarium temperature exceeds the weather-derived target by more than 0.25 deg C (hysteresis), providing a transition band where fans attempt evaporative cooling before the compressor engages.

In **hot mode**, when the compressor engages (temperature exceeds 25 deg C), the controller reverts to humidity-based error since the compressor now handles temperature reduction.

**Mode transitions** reset the PID integral, derivative, and last-error state to prevent fan speed jumps from accumulated integral terms under a different error regime. The current control mode (`pid_control_mode`: 0=humidity, 1=temperature) is logged to InfluxDB for analysis.

In all three regimes, the PID output is computed as:

    u(t) = Kp * e(t) + Ki * integral(e) + Kd * de/dt

The tuning parameters, determined empirically and adjustable at runtime via the Node-RED Dashboard, are: Kp=50, Ki=0.5, Kd=10. The PID output is added to a base speed of 50 PWM (~20% duty cycle), and the total is clamped to 40-230 PWM (16-90% duty cycle).

**Gain scheduling** prevents rapid fan oscillation near the setpoint while maintaining aggressive response to large disturbances. A gain factor (*g*) scales the effective Kp and Kd based on error magnitude: *g*=0.15 for |error| <= 1.5 units (effective Kp=7.5), *g*=1.0 for |error| >= 4.0 units (full Kp=50), with linear interpolation between. This eliminated the +/-25 PWM oscillations that occurred with fixed gains when humidity hovered within +/-0.5% of the setpoint. Anti-windup protection, derivative filtering, and rate limiting details are provided in Supplementary File S5.

#### 2.4.4 Mister Hysteresis Control

The ultrasonic mister is controlled via a hysteresis (bang-bang) controller in the Humidity tab, with configurable on/off thresholds relative to the target humidity. When humidity falls below the lower threshold, the mister activates; when humidity exceeds the upper threshold, it deactivates.

A critical safety interlock ensures that **all fans stop when the mister is active**. This prevents fans from dispersing the mist plume before it can saturate the terrarium air and avoids drawing unsaturated air into the enclosure during misting events. The interlock is implemented as a gate function upstream of the PID controller output that blocks fan commands when `mister_status` is true.

#### 2.4.5 Freezer Hysteresis Control

The Vitrifrigo ND50 compressor unit (Section 2.2.2) is controlled via a hysteresis controller in the Temperature tab, switching the compressor on/off via its Tapo P100 smart plug based on the difference between actual and target temperature. The freezer target is fixed at 24.75 deg C with +0.25 deg C hysteresis — the compressor activates when the terrarium temperature exceeds 25 deg C and deactivates when it falls to 24.75 deg C. A night cap function also sets the target to 24.75 deg C when the weather-derived value exceeds 24 deg C, preventing unnecessary compressor cycling during warm periods. When the compressor activates, the evaporator fans (pin 44) and circulation fans (pin 12) ramp to 255 PWM to maximize cold air distribution; when it deactivates, these fans reduce to 168 PWM for gentle background circulation.

#### 2.4.6 Dynamic Photoperiod

The photoperiod is computed daily from the latitude of Chinchina, Colombia (4.98 deg N), the primary weather reference city, using the standard solar declination equation:

    declination = 23.45 * sin(2 * pi / 365 * (day_of_year - 81))
    cos(hour_angle) = -tan(latitude) * tan(declination)
    day_length = 2 * acos(cos(hour_angle)) * 12 / pi    [hours]

The calculated day length is clamped to the range 10-14 hours for safety (though at 5 deg N the unclamped range is only 11h43m to 12h17m — a 34-minute annual variation). The lit period is centered on 13:15 local (Genoa) time, which was the midpoint of the previous fixed schedule and preserves backward compatibility. All schedule times are derived proportionally from the computed day length:

| Event | Derivation | Example (equinox, 12h00m) | Example (Dec solstice, 11h43m) |
|-------|------------|---------------------------|-------------------------------|
| Lights ON (plug) | dawn_ramp - 5 min | 06:40 | 06:49 |
| Dawn ramp start | sunrise - 30 min | 06:45 | 06:54 |
| Sunrise (40%) | center - day_length/2 | 07:15 | 07:24 |
| Midday ramp-up | sunrise + 37.5% of day | ~11:46 | ~11:51 |
| Midday ramp-down | sunrise + 62.5% of day | ~14:44 | ~14:40 |
| Sunset (40%) | center + day_length/2 | 19:15 | 19:07 |
| Dusk ramp end | sunset + 30 min | 19:45 | 19:37 |
| Lights OFF (plug) | dusk_ramp + 35 min | 19:50 | 19:42 |

Two independent dynamic dimmer channels provide the intensity variation: Dimmer #1 handles dawn (0 to 40 on the slider) and dusk (40 to 0) over 30-minute ramps (40 steps x 45 seconds); Dimmer #2 handles the midday boost (40 to 60 and back) over 30-minute ramps (20 steps x 90 seconds). The midday boost simulates the brief clearing events common on tepui summits.

A unified scheduler function node receives 1-minute ticks, reads the photoperiod globals, and dispatches Tapo on/off commands and dimmer ramp triggers at the computed times. This replaces the previous fixed-time BigTimer and time-inject nodes.

The slider value is inverted by a range node before being written to the Arduino PWM pin: lower PWM values produce brighter light (the LED driver dims proportionally to the PWM signal). The 5-minute offset between plug activation and dimmer ramp start ensures the LED driver is powered before the PWM dimmer begins ramping. The 30-minute ramp duration simulates the gradual light transitions characteristic of tropical mountain environments.

A startup recovery node detects when Node-RED restarts during a ramp window and calculates the elapsed fraction using the dynamic photoperiod times, issuing a partial-ramp command so the dimmer finishes on schedule rather than restarting the full 30-minute ramp from scratch. The photoperiod calculator runs at 5 seconds after startup; the startup brightness node runs at 10 seconds, ensuring the schedule is available before brightness is set.

#### 2.4.7 Night A/B Fan Experiment

A controlled experiment evaluated the effect of nighttime air circulation on temperature and humidity. The protocol alternated nightly based on day-of-year parity:

- **Night A** (even day-of-year): All fans off (0 PWM) — passive cooling only
- **Night B** (odd day-of-year): Outlet and impeller fans at 80 PWM (~31% duty cycle) — gentle circulation

The mode was determined by the evening's date (not the current date at midnight) to prevent mid-night transitions. The experiment ran from February 5 to February 18, 2026 (13 nights: 7 Night A, 6 Night B). Results were analyzed using OLS regression, IV/2SLS with the A/B assignment as an instrument for fan speed, and hour-by-hour adjusted profiles (see Supplementary File S8 for the full analysis scripts).

Key findings from the IV/2SLS analysis: each +10 PWM of fan speed causes a -0.37% reduction in humidity. Hour-by-hour analysis showed that nighttime fans at 80 PWM cool the terrarium significantly during the evening hours (20:00-23:00, adjusted effect -0.75 to -1.4 deg C) but produce slight warming after midnight (+0.3 to +0.55 deg C) as fans draw warmer room air into the enclosure. This asymmetric temporal pattern motivated the wet-bulb temperature investigation described in Section 2.4.11.

Based on these findings, the A/B experiment was suspended and the fan schedule was adjusted: the PID controller now remains active from 05:00 to midnight, capturing the evening cooling benefit, while fans are off from midnight to 05:00 to avoid the late-night warming effect.

#### 2.4.8 Door Safety Mode

Two magnetic reed switches (one per sliding front panel) are wired to Arduino digital inputs D22 and D24 with internal pull-up resistors. A 3-second software debounce in the door controller node suppresses spurious open/close events from contact bounce — the door must remain open for 3 consecutive seconds before the safety mode activates.

When either door opens, the system enters door safety mode:

1. All fans stop immediately (pins 12, 44, 45, 46 -> 0 PWM)
2. Compressor turns off (Tapo plug blocked from turning on)
3. Mister turns off (Tapo plug blocked from turning on)
4. Lights set to 60% brightness (PWM 102) regardless of current dimmer state, providing working light for maintenance

All Tapo plug commands pass through gate nodes that block inappropriate actions during door safety mode (e.g., the compressor gate blocks "on" commands, the light gate blocks "off" commands). Fan writer nodes check the `door_safety_active` global flag and suppress PID output while the flag is set.

When all doors close, the system restores the previous state: fan speeds resume from the PID controller, Tapo plugs return to their pre-opening states (saved on door open), and the dimmer restores its last commanded brightness.

#### 2.4.9 Startup Recovery

A startup brightness node runs once after Node-RED deploys, determining the correct light state based on the current time and the dynamically computed photoperiod schedule (Section 2.4.6). If the system restarts during one of the four ramp windows (dawn, midday-up, midday-down, dusk), the node calculates the elapsed fraction of the ramp and issues a partial-start command to the appropriate dimmer, so the ramp completes on schedule rather than restarting from scratch. Outside ramp windows, the node simply sets the correct static brightness level (0, 40, or 60 on the slider). The photoperiod calculator runs first (at 5 seconds after deploy), followed by the startup brightness node (at 10 seconds), ensuring the dynamic schedule times are available before brightness decisions are made.

#### 2.4.10 Control Priority Hierarchy

The system implements a five-level control priority:

1. **Door safety** (highest priority): Door open overrides all automatic control, forces safe state
2. **Manual override**: Operator-set fan speed via the Node-RED Dashboard UI
3. **Safety interlock**: Mister-active fan stop, overriding PID output
4. **Wet-bulb temperature gate**: Post-sunset fan shutdown when terrarium temperature is at or below room wet-bulb
5. **Automatic PID control** (lowest priority): Three-regime humidity/temperature-based operation (Section 2.4.3)

Each level checks for higher-priority overrides before executing, ensuring predictable behavior during maintenance or emergency situations.

#### 2.4.11 Wet-Bulb Temperature Shutdown

After sunset, evaporative cooling via ventilation fans becomes counterproductive when the terrarium temperature approaches the room's wet-bulb temperature. The wet-bulb temperature represents the thermodynamic limit of evaporative cooling: it is the lowest temperature that can be achieved by evaporating water into air at a given temperature and humidity. Once the terrarium temperature reaches this floor, fans can no longer provide net cooling — they instead inject sensible heat from the warmer room air, which the compressor must then work harder to remove.

The room's wet-bulb temperature is calculated using the Stull (2011) approximation from room temperature (*T*, deg C) and relative humidity (*RH*, %):

    Tw = T * atan(0.151977 * (RH + 8.313659)^0.5)
         + atan(T + RH)
         - atan(RH - 1.676331)
         + 0.00391838 * RH^1.5 * atan(0.023101 * RH)
         - 4.686035

This formula provides accuracy within +/-0.3 deg C over the range of conditions encountered in the system (Stull, 2011).

A wet-bulb temperature gate node intercepts the PID controller output for the outlet and impeller fans. After 18:00, when the terrarium temperature (*T_terrarium*) falls to or below the room wet-bulb temperature (*Tw_room*), the gate engages and sets the outlet and impeller fans to 0 PWM. Once engaged, the shutdown remains active until a timed reset at 04:29, before the PID controller resumes at 05:00. During daytime hours, the gate operates in pass-through mode, allowing normal PID control.

This mechanism prevents the system from fighting itself: without the gate, the PID controller would increase fan speed in response to rising humidity (caused by the lack of evaporative cooling), drawing in warm room air that raises the temperature, which the compressor must then counteract. The wet-bulb gate breaks this cycle by recognizing when fan-based cooling has reached its thermodynamic limit and deferring entirely to mechanical refrigeration.

### 2.5 Data Logging

A centralized data logger function on the Utilities tab reads all global context variables at 60-second intervals and writes to 16 individual InfluxDB measurements:

1. `local_temperature` — Terrarium temperature (deg C)
2. `local_humidity` — Terrarium relative humidity (%)
3. `vpd` — Vapor pressure deficit (kPa)
4. `target_temperature_computed` — Weather-derived temperature setpoint (deg C)
5. `target_humidity_computed` — Weather-derived humidity setpoint (%)
6. `difference_temperature` — Target minus actual temperature (deg C)
7. `difference_humidity` — Target minus actual humidity (%)
8. `fan_speed` — PID controller output (PWM 0-255)
9. `freezer_status` — Compressor relay state (0/1)
10. `mister_status` — Mister relay state (0/1)
11. `light_status` — Light relay state (0/1)
12. `water_level_local` — Reservoir water level (%)
13. `night_test_mode` — Night A/B experiment mode (0=A, 1=B, -1=suspended)
14. `power_consumption` — System power draw (W, via Meross MSS310, logged every 2 minutes)
15. `wbt_shutdown_active` — Wet-bulb temperature gate state (0/1)
16. `pid_control_mode` — Active PID regime (0=humidity, 1=temperature)

Additional measurements are logged by other flow components (individual fan PWM channels including circulation fan PWM, mist events, individual city weather data, room temperature/humidity, room wet-bulb temperature), bringing the total to 32 InfluxDB measurements (Supplementary Table S1).

### 2.6 Light Gradient and Two-Stage Dimming

The inverse square law from overhead LED sources creates a continuous light gradient within the terrarium. Light intensity falls off with the square of the distance from the pucks, meaning that species at the top of the enclosure (directly beneath the LEDs) receive substantially higher irradiance than those at the bottom. This physical property is exploited as a design feature rather than a limitation: high-light species such as *Heliamphora* — which grow fully exposed on tepui summits — are placed in the upper zone, while shade-adapted species such as *Dracula* orchids — which grow beneath dense canopy in nature — occupy the lower zone. Intermediate species are positioned on the mid-height shelf. A single lighting system thus approximates the distinct light environments these species occupy in nature, without physical barriers or multiple independently controlled fixtures.

The system employs a two-stage dimming approach. The Mean Well HLG-480H-48A LED driver includes a screw-driven potentiometer that sets a hardware ceiling on the maximum output. This potentiometer has been adjusted to limit driver output to approximately 60% of the LEDs' full rated power. The Arduino PWM signal on pin 8 then operates as a second dimming stage within this hardware-limited range: when the Node-RED slider reads 100%, the actual light output is ~60% of the LEDs' rated maximum; when the slider reads 50%, the output is ~30% of rated maximum.

This two-stage architecture provides a fail-safe mechanism. Even if the software erroneously commands 100% brightness — due to a bug, a reboot glitch, or a manual override error — the hardware potentiometer physically prevents the LEDs from exceeding approximately 60% of rated power. This cap protects the shade-adapted species in the lower zone, which could be damaged by full-power illumination. It also reduces thermal load on the terrarium, simplifying the cooling system's task. The potentiometer setting was determined empirically based on the light requirements of the most shade-sensitive species in the collection.

---

## 3. Results

### 3.1 Environmental Performance

Over the monitoring period, the system maintained the following environmental ranges within the terrarium:

| Parameter | Minimum | Maximum | Typical Range | Target Range |
|-----------|---------|---------|---------------|--------------|
| Temperature | 13.5 deg C | 24.3 deg C | 15-22 deg C | Weather-derived (clamped 12-24 deg C) |
| Relative Humidity | 75% | 98% | 82-95% | Weather-derived (clamped 70-90%) |
| VPD | 0.03 kPa | 0.64 kPa | 0.08-0.45 kPa | < 0.8 kPa |

The system achieves a meaningful diurnal temperature swing despite the terrarium being located in a room maintained at approximately 22 deg C year-round. Nighttime terrarium temperatures routinely drop to 14-16 deg C through active compressor cooling, while daytime temperatures rise to 18-22 deg C, producing a 4-8 deg C daily amplitude that approximates conditions on mid-elevation tepuis.

### 3.2 PID Controller Stability

The gain-scheduled PID controller maintains humidity within +/-3% RH of the setpoint under steady-state conditions, producing smooth fan speed transitions that eliminate the continuous cycling characteristic of simpler hysteresis controllers. The gain scheduling (Section 2.4.3) was critical: with fixed gains, the controller exhibited rapid +/-25 PWM oscillations near the setpoint; after scheduling (effective Kp=7.5 within +/-1.5% of target), these oscillations were eliminated.

An IV/2SLS analysis using the Night A/B experiment (Section 2.4.7) as an instrument confirmed the PID-controlled fans' causal effect on humidity: each +10 PWM of fan speed causes a -0.37% reduction in humidity (p < 0.05). The compressor is the dominant cooling and dehumidification actuator (-15.9% humidity long-run effect when active), with the PID fans providing fine-tuning within the compressor's hysteresis band.

### 3.3 Weather Data Correlation

The Colombian weather integration produces continuously varying setpoints that reflect real meteorological conditions. The 15-hour time shift between Colombian local time (UTC-5) and Italian local time (UTC+1/+2) means that Colombian daytime conditions (typically 16-22 deg C, 60-80% RH at the reference elevations) map onto Italian nighttime, while Colombian nighttime conditions (typically 12-16 deg C, 85-95% RH) map onto Italian daytime. This produces a biologically desirable pattern: the terrarium experiences cooler, more humid conditions at night and warmer, drier conditions during the day, mirroring the natural diurnal cycle of cloud forest environments.

The stochastic character of real weather data is a key advantage over fixed schedules. Rain events in Colombia — which can drop temperatures by several degrees within an hour and push humidity to near-saturation — translate into corresponding terrarium setpoint changes, creating the kind of sudden environmental perturbations that cloud forest species experience naturally. For example, an afternoon rainstorm in the Chinchina-Medellin region (arriving as a nighttime event in Genoa after the 15-hour shift) will lower the target temperature and raise the target humidity, prompting the compressor to activate and the mister to fire, simulating a fog immersion event. These events are not programmed; they emerge organically from the weather data feed and vary from day to day and season to season.

The two-stage averaging (30-minute InfluxDB window plus 15-minute rolling mean across all four cities) smooths transient API fluctuations while preserving meaningful weather events — an aggressive smoothing window made possible by the 15-hour data buffer. If the OpenWeatherMap API becomes temporarily unreachable — due to internet outage or service interruption — the system falls back to a historical daily curve constructed from the previous 14 days of recorded weather data. Every six hours, the system queries InfluxDB for 5-minute-binned averages of all four cities' temperature and humidity readings, collapses them into a single 288-slot daily profile (one slot per 5 minutes), applies two-pass circular smoothing, and stores the result. During a fallback event, the current time of day indexes directly into this curve, providing a realistic diurnal setpoint that tracks the shape of the actual weather cycle rather than reverting to flat defaults. An ultimate fallback (day: 24 deg C/85% RH; night: 14 deg C/90% RH) is retained for the edge case where no historical data is available (e.g., immediately after a fresh installation).

### 3.4 Species Diversity and Convergent Cloud Forest Cultivation

The system supports approximately 120 species from cloud forests across five biogeographic regions, organized here by region of origin. The successful co-cultivation of these species in a single enclosure with shared environmental conditions demonstrates the convergent nature of cloud forest climates worldwide.

#### 3.4.1 Venezuelan Tepui (Guiana Highlands)

*Heliamphora* species represent the flagship tepui group, grown in the upper zone in akadama/sphagnum substrate topped with living *Sphagnum* moss (Section 2.1.7). Multiple species and hybrids produce mature pitchers, divide regularly, and produce flower scapes under the system's conditions, demonstrating that the weather-variable setpoints provide adequate simulation of their native tepui summit environment (2,000-2,800 m elevation, 10-20 deg C, persistent cloud immersion). *Brocchinia reducta*, a carnivorous bromeliad from the same tepui summits, is grown in the same akadama/sphagnum substrate and maintains its characteristic tank rosettes.

*Utricularia* of section *Orchidioides* — including *U. alpina*, *U. quelchii*, and *U. campbelliana* — are grown kokedama-style in balls of living *Sphagnum* moss suspended from the shelf level. These species, native to tepui cliff faces and cloud forest canopies, produce their characteristic orchid-like flowers regularly. *U. quelchii*, which is endemic to a small number of tepui summits, grows vigorously in the middle zone where humidity remains consistently above 85%.

#### 3.4.2 Colombian and Ecuadorian Andes

*Dracula* orchids (pleurothallid alliance) are the primary Andean representatives, mounted on cork bark in the lower zone where temperatures are coolest and light levels lowest — conditions that approximate the deep shade of Andean cloud forest understory at 1,800-2,500 m elevation. Several species produce their distinctive, intricate flowers throughout the year, with the inflorescences emerging through the moss pad and hanging below the mount as they do in nature.

*Masdevallia* and *Restrepia* species occupy similar niches in the lower and middle zones. *Masdevallia* species flower freely, with some producing sequential blooms from the same inflorescence over several months. *Restrepia*, with their insect-mimicking flowers, bloom repeatedly from the same leaf axils.

*Phragmipedium* species (Andean slipper orchids) are grown in the lower zone in sphagnum-based media. These moisture-loving orchids thrive in the persistently high humidity and produce their characteristic pouch-like flowers.

#### 3.4.3 PNG Highlands (Australasia)

*Dendrobium* section *Oxyglossum*, including *D. victoriae-reginae* and allied species, represents the Australasian cloud forest contingent. These species are native to the highlands of Papua New Guinea at elevations of 1,500-3,000 m, where temperatures and humidity closely parallel those of Andean cloud forests despite being separated by the entire Pacific Ocean. Mounted on tree fern plaques in the upper zone, they produce their brilliant blue-purple flowers, confirming the compatibility of PNG highland conditions with the Neotropical-derived climate simulation.

The success of these species alongside Andean and tepui plants is perhaps the strongest demonstration of climatic convergence: *D. victoriae-reginae* evolved in geographic isolation from *Dracula* and *Heliamphora*, yet all three thrive under identical temperature and humidity regimes because their respective cloud forests converge on similar environmental envelopes.

#### 3.4.4 Brazilian Atlantic Forest Highlands

*Sophronitis* (syn. *Cattleya*) species — miniature rupicolous orchids from the Brazilian Atlantic Forest highlands at 1,000-2,000 m — are mounted on cork bark across the upper and middle zones. These species produce their vivid red-orange flowers, with some species flowering multiple times per year. *Leptotes* species, also from the Brazilian Atlantic Forest, occupy similar positions and produce their small but proportionally large flowers regularly.

The Brazilian highland species are notable because their native habitat — cool, moist mountaintops along the Atlantic coast — is climatically convergent with Andean cloud forests despite being separated by the Amazon basin. The same temperature and humidity ranges that support Andean *Dracula* also satisfy Brazilian *Sophronitis*.

#### 3.4.5 Pan-Tropical Highland Epiphytes

Highland *Nepenthes* species from Borneo and Sumatra (1,500-3,000 m elevation) are grown in kanuma/sphagnum substrate placed directly on the terrarium floor without saucers (Section 2.1.7), where the coolest temperatures and persistently high ambient humidity support active pitcher production without supplementary moisture trays. These represent the Southeast Asian contribution to the convergent cloud forest collection.

Highland ferns, including *Lecanopteris* (ant-ferns from the Malay Archipelago), occupy the lower zone and contribute to the overall humidity buffering. Mosses from various sources colonize available surfaces, forming a living substrate layer that stabilizes humidity and provides rooting medium for epiphytes.

*Vanda pumila* and small bromeliads complete the pan-tropical assemblage.

#### 3.4.6 Evidence for Climatic Convergence

The co-cultivation of species from five biogeographic regions over three years provides empirical evidence that cloud forest climates converge on a shared environmental envelope worldwide. Species from Venezuelan tepuis (5 deg N, 2,500 m), the Colombian Andes (5-7 deg N, 1,500-2,600 m), the PNG highlands (6 deg S, 2,000-3,000 m), the Brazilian Atlantic Forest (22 deg S, 1,500 m), and montane Borneo (6 deg N, 1,500-3,000 m) all maintain healthy growth, produce flowers, and in many cases propagate vegetatively under identical conditions: 13.5-24.3 deg C, 75-98% RH, and moderate light filtered through the vertical gradient.

Natural selection over the three-year operational period has been informative. Species that have been lost tend to be those requiring pronounced dry rest periods to initiate flowering — a requirement incompatible with the year-round high humidity maintained for moisture-dependent species such as *Dracula* and *Heliamphora*. This includes certain *Dendrobium* section *Callista* and seasonal *Cattleya* alliance species. The system therefore selects for species compatible with continuous high moisture, which is precisely the defining feature shared by convergent cloud forests worldwide. Moisture-dependent species from all five regions thrive together because persistent humidity is the common thread linking their disparate native habitats.

### 3.5 Wet-Bulb Temperature Results

Analysis of room sensor data reveals consistent room conditions of 22.1+/-0.7 deg C and 57.9+/-5.2% RH, corresponding to a room wet-bulb temperature of 16.6+/-0.9 deg C calculated using the Stull (2011) formula. The terrarium temperature crosses below this wet-bulb threshold around 20:00-21:00 each evening as the compressor drives temperatures down. By 03:00, the terrarium typically reaches 1.7 deg C below wet-bulb (achievable only through mechanical refrigeration), and by 06:00 it has risen back to approximately the wet-bulb temperature.

A preliminary heat-balance regression (R-squared=0.24, based on the February 6-24 operational period) decomposed the contributions of different actuators to the terrarium's hourly temperature change:

| Actuator | Temperature effect | Interpretation |
|----------|-------------------|----------------|
| Freezer (compressor) | -2.03 deg C/hr | Dominant cooling mechanism |
| Fans (outlet + impeller) | +0.37 deg C/hr | Net warming effect (room air sensible heat) |
| Passive heat exchange | +0.58 deg C/hr | Room-to-terrarium heat transfer |

An extended model including the interaction between fan speed and the temperature difference above wet-bulb (T_above_wb) reveals that the fan cooling effect diminishes linearly as the terrarium approaches wet-bulb, reaching zero at approximately T_above_wb = +0.3 deg C. Below this point, fans provide no evaporative cooling benefit and become a net heat source.

These preliminary results confirm the thermodynamic argument: once the terrarium temperature falls to or below the room's wet-bulb temperature, ventilation fans can no longer provide evaporative cooling and instead inject sensible heat. The wet-bulb shutdown gate (Section 2.4.11) implements this finding operationally. Clean data collection began on February 24, 2026, with a planned reanalysis after 10-15 days of stable operation under the current configuration.

### 3.6 System Reliability

The primary reliability challenge is a recurring serial stall condition in which the Arduino Mega's USB-to-serial bridge chip enters a stuck state, silently stopping all serial communication after variable periods of normal operation. This issue predates the current custom serial protocol and was also observed with StandardFirmata, indicating a hardware-level problem — likely related to the Raspberry Pi 4's internal USB hub — rather than a protocol-level one. No kernel errors or USB disconnect events are logged when the stall occurs.

The watchdog v10 (Section 2.3.3) mitigates this by detecting the absence of heartbeat messages and performing a USB sysfs reset, toggling the Arduino's `authorized` attribute to reset the USB-serial bridge without a full system reboot, reducing recovery time to approximately 15-30 seconds. A 60-second cooldown prevents reset loops.

Between stall events, the system operates autonomously without human intervention. The weather fallback mechanism (Section 2.4.1) ensures that temporary internet outages do not disrupt control: the system holds the last valid setpoints and, if those expire, substitutes a smoothed historical daily curve derived from the previous 14 days of weather data. The door safety mode (Section 2.4.8) provides automatic protection during maintenance, and the startup recovery node (Section 2.4.9) handles graceful recovery from reboots that occur during light-dimming ramp windows.

---

## 4. Discussion

### 4.1 Weather-Based vs. Fixed Setpoints

The use of real-time weather data from Colombian highlands as the basis for terrarium setpoints represents a departure from conventional fixed-schedule environmental control. This approach offers several advantages:

**Naturalistic variability**: Fixed setpoints produce monotonous conditions that may fail to provide environmental cues for phenological processes. Weather-referenced setpoints introduce stochastic variation within safe bounds — rain events in Colombia produce sudden cooling and humidity spikes that translate into the terrarium environment, simulating the fog immersion events characteristic of cloud forest habitats.

**Seasonal adaptation**: As Colombian weather patterns shift seasonally, the terrarium setpoints automatically adjust, providing longer-timescale variation without manual reprogramming.

**Biological hypothesis**: While not formally tested in this study, we hypothesize that weather-driven environmental variation may improve flowering frequency and overall vigor in cloud forest species compared to static conditions, as it more closely approximates the dynamic environments to which these species are adapted.

**Revealing thermodynamic limits**: The weather-mimicking approach, with its comprehensive data logging, was instrumental in revealing the wet-bulb temperature limitation (Section 3.5). Under fixed setpoints, the crossover between evaporative-cooling-effective and evaporative-cooling-ineffective regimes would have been less visible, because the system would lack the continuous environmental variation needed to probe different operating points. The rich dataset generated by weather-variable control enabled the heat-balance regression that identified the wet-bulb threshold as the boundary between productive and counterproductive fan operation.

### 4.2 Convergent Cloud Forest Cultivation

A central finding of this work is that species from geographically disjunct cloud forests can be co-cultivated in a single enclosure tuned to their shared climatic envelope. Cloud forests on tepui summits (Venezuela), in the Andes (Colombia, Ecuador), in the highlands of Papua New Guinea, on Brazilian Atlantic Forest mountaintops, and in montane Borneo-Sumatra all converge on similar conditions: cool temperatures (typically 10-22 deg C), persistent high humidity (80-100% RH), frequent fog or cloud immersion, and moderate to low light beneath a persistent cloud layer.

This convergence is not coincidental — it reflects the physical constraints of tropical mountain meteorology. At similar elevations in the tropics, adiabatic cooling, orographic lifting, and the resulting cloud formation produce broadly similar microclimates regardless of longitude. Species evolving independently in these convergent environments face similar selective pressures: cool temperatures, constant moisture, and low light. They consequently develop similar environmental tolerances, even though they share no recent evolutionary history.

The practical implication is that a single-biome terrarium tuned to the common cloud forest envelope can accommodate species from multiple continents simultaneously. This differs fundamentally from typical terrarium approaches that target a single geographic region (e.g., "a tepui terrarium" or "an Andean cloud forest terrarium"). By recognizing the underlying climatic convergence, the system can maintain a taxonomically and biogeographically diverse collection that would otherwise require multiple separate enclosures with distinct environmental regimes.

Three years of successful co-cultivation — with species from five continents growing, flowering, and propagating side by side — validates this convergent cultivation concept at a practical level. The species that have been lost are those requiring dry rest periods incompatible with year-round high humidity, not those from particular geographic regions, further supporting the idea that the climate envelope rather than the geographic origin determines compatibility.

### 4.3 Nighttime Cooling: The Central Challenge

The defining technical challenge of highland cloud forest terraria is achieving meaningful nighttime temperature drops in a domestic setting. While many hobbyists and institutions successfully maintain high-humidity terraria for tropical lowland species, extending this approach to highland species requires solving a fundamentally different problem: the terrarium must be actively cooled well below ambient room temperature, every night, for years.

The approaches available to growers include evaporative cooling (misting combined with ventilation), thermoelectric (Peltier) modules, portable air conditioning units, and compressor-based refrigeration. Each has distinct limitations:

**Evaporative cooling** is the most accessible method, requiring only fans and a misting system. However, as the wet-bulb temperature analysis in this paper demonstrates (Section 3.5), evaporative cooling is thermodynamically limited by the room's wet-bulb temperature. In a typical indoor environment (22 deg C, 58% RH), the wet-bulb floor is approximately 16.6 deg C — insufficient to simulate the 10-14 deg C nighttime temperatures of mid-to-high-elevation cloud forests. Below the wet-bulb threshold, fans become counterproductive, injecting sensible heat rather than removing it. This finding has practical implications for any terrarium system relying on ventilation-based cooling: evaporative methods can achieve meaningful cooling only down to the room's wet-bulb temperature, which in most domestic environments falls short of the target range for highland species.

**Thermoelectric (Peltier) modules** offer solid-state cooling without moving parts or refrigerants, but their cooling capacity scales poorly with enclosure volume. With a coefficient of performance (COP) typically below 1.0, a Peltier device generates more waste heat than useful cooling, requiring substantial heat sinking on the hot side. For enclosures larger than approximately 50 liters — far smaller than the 990-liter volume of the present system — Peltier modules cannot maintain the required temperature differential against continuous heat ingress from the room.

**Portable air conditioning units** provide adequate cooling power but are designed for room-scale applications and are difficult to integrate with the sealed, high-humidity environment of a terrarium. Duct routing, condensate management, and the cyclic compressor behavior of consumer AC units (designed for comfort cooling with wide hysteresis bands) make them poorly suited for the precise temperature control required by sensitive cloud forest species.

The **marine refrigeration unit** used in this system (Vitrifrigo ND50 with Danfoss BD50F variable-speed compressor) resolves these limitations. Originally designed for boat refrigeration — where compact size, low power draw, and reliable operation in confined spaces are essential — marine compressors provide sufficient cooling capacity to drive the terrarium temperature well below the room's wet-bulb temperature (routinely reaching 13.5 deg C, some 3 deg C below the wet-bulb floor and nearly 9 deg C below room ambient). The stainless-steel evaporator plate doubles as a condensation surface, continuously dehumidifying the air and producing condensate that is collected and recycled. The system's three-year operational record demonstrates that this approach is viable for long-term domestic use, achieving the kind of nighttime cooling that highland carnivorous plants, orchids, and other cloud forest species require but that evaporative and thermoelectric methods cannot reliably deliver.

### 4.4 PID vs. Bang-Bang Control

The PID controller for humidity management provides smoother fan speed transitions than the hysteresis (bang-bang) approach used for temperature and mister control, eliminating the continuous on-off cycling and producing more stable environmental conditions. The gain scheduling approach — reducing proportional response near the setpoint — is critical and should transfer well to other terrarium systems, though the specific tuning values (Kp=50, Ki=0.5, Kd=10) are specific to this enclosure's volume, ventilation geometry, and sensor response time.

### 4.5 Open-Source Accessibility

A key design goal of this system is reproducibility using commodity hardware and free software. The total system cost (excluding terrarium construction and plants) consists of a Raspberry Pi, an Arduino Mega, three smart plugs, an ESP microcontroller with sensor, fans, and LED pucks — all widely available consumer components.

Node-RED's visual flow-based programming environment lowers the barrier to entry compared to traditional programming approaches. Users can inspect and modify control logic visually, adjust PID tuning parameters through dashboard controls, and extend the system with additional sensors or actuators using Node-RED's extensive node library.

### 4.6 Ongoing Optimization

The Night A/B fan experiment (Section 2.4.7) and the subsequent wet-bulb temperature analysis illustrate an important aspect of the system: even after three years of successful operation, continuous refinement remains possible and valuable. The open data pipeline (InfluxDB + Grafana) enabled rapid hypothesis testing — the A/B experiment ran for only 13 nights before producing actionable findings, and the wet-bulb analysis was performed on routinely collected data without requiring any additional instrumentation.

This experimental capability, built into the control infrastructure rather than requiring separate equipment, represents a significant advantage of the software-defined approach over hardware-only solutions. The same data pipeline supported rigorous IV/2SLS causal inference and heat-balance regression, demonstrating that hobbyist-scale terrarium systems can produce publication-quality analytical results.

### 4.7 Limitations

- **Single sensor**: The system relies on a single SHT35 sensor, creating a single point of failure and potentially unrepresentative measurements in a terrarium with spatial environmental gradients.
- **Internet dependency**: Weather-based setpoints require internet access to the OpenWeatherMap API, and the Meross power monitoring relies on a cloud API. Connectivity interruptions are mitigated by a historical daily curve fallback (Section 3.3), but the cloud dependency for power monitoring is a design weakness that could be addressed by local energy metering.
- **Serial stall**: The Arduino Mega's USB-serial bridge periodically enters a stuck state. This appears to be related to the Raspberry Pi 4's internal USB hub and persists across protocol changes. The current mitigation (USB sysfs reset) avoids full system reboots but does not eliminate the underlying stall.
- **No species-specific seasonal regimes**: Some orchid species (notably certain *Dendrobium* and *Cattleya* alliance species) require a pronounced dry rest period to initiate flowering. In a shared enclosure optimized for persistent high humidity, implementing a dry rest for one species risks desiccation of neighboring moisture-dependent species such as *Dracula* and *Heliamphora*. The system therefore sacrifices some species-specific phenological triggers in favor of maintaining conditions safe for all inhabitants — a fundamental tradeoff of the single-biome approach. Species that have been lost over three years of operation have often been those with the strongest dry-rest requirements, suggesting that this limitation acts as a de facto selection pressure favoring species compatible with year-round high moisture.
- **No formal species performance metrics**: While approximately 120 species are maintained, systematic growth rate and flowering frequency measurements have not been conducted.
- **Preliminary wet-bulb analysis**: The heat-balance regression (R-squared=0.24) is based on a short and operationally noisy data period. Clean data collection is ongoing to produce more robust estimates.

### 4.8 Future Work

- Addition of redundant sensors and spatial temperature/humidity mapping
- Integration of CO2 monitoring for photosynthesis optimization
- Formal comparison of species performance under weather-variable vs. fixed setpoints
- Expansion of the weather reference to include additional cities or direct tepui weather station data when available
- Refined wet-bulb analysis with clean data to optimize the evening fan shutdown threshold
- Machine learning approaches to PID auto-tuning based on historical response data

---

## 5. Conclusions

We have demonstrated a weather-mimicking terrarium system that simulates highland cloud forest climates using real-time Colombian meteorological data, successfully cultivating approximately 120 species from convergent cloud forests across five continents for over three years.

The primary contribution is the weather-mimicking approach itself. By ingesting real weather data from four Colombian highland cities and applying a 15-hour time shift, the system produces naturalistic, stochastic environmental variation that captures the dynamic character of tropical montane climates — including rain events, diurnal fog cycles, and seasonal shifts — in a way that fixed setpoints cannot replicate. The comprehensive data logging enabled by this approach also facilitated the discovery of the wet-bulb temperature limitation.

The convergent cloud forest cultivation concept — co-cultivating species from Venezuelan tepuis, the Colombian Andes, PNG highlands, the Brazilian Atlantic Forest, and montane Borneo-Sumatra in a single enclosure — is validated by three years of successful growth, flowering, and vegetative propagation across taxonomically diverse genera. The success of this approach rests on the recognition that cloud forests worldwide converge on similar climatic envelopes, allowing species from independent evolutionary lineages to coexist under shared environmental conditions.

The wet-bulb temperature insight provides a thermodynamic explanation for the limits of evaporative fan cooling in terrarium systems. When the terrarium temperature falls below the room's wet-bulb temperature — typically around 20:00-21:00 each evening under our conditions — ventilation fans become counterproductive, and the system automatically defers to mechanical refrigeration. This finding, derived from routine operational data, has practical implications for any terrarium system that uses ventilation-based cooling in a room with finite humidity.

Finally, the entire system is built on open-source software (Node-RED, InfluxDB, Grafana) and commodity hardware (Raspberry Pi, Arduino Mega, smart plugs), making it reproducible by hobbyists and small institutions. The PID humidity controller with gain scheduling, door safety interlocks, and comprehensive data logging provide reliable automated operation, while the open data pipeline enables experimental analysis — including the IV/2SLS causal inference and heat-balance regression presented here — without additional instrumentation. All system components — Node-RED flows, Arduino firmware, Grafana dashboards, watchdog scripts, statistical analysis code, and documentation — are available as open-source supplementary materials.

---

## References

- Berry, P. E., & Riina, R. (2005). Insights into the diversity of the Pantepui flora and the biogeographic complexity of the Guayana Shield. *Biologiske Skrifter*, 55, 145-167.
- Givnish, T. J., et al. (2014). Adaptive radiation, correlated and contingent evolution, and net species diversification in Bromeliaceae. *Molecular Phylogenetics and Evolution*, 71, 55-78.
- Grafana Labs. (2026). https://grafana.com/
- InfluxDB. (2026). https://www.influxdata.com/
- Node-RED Project. (2026). https://nodered.org/
- Rull, V., & Vegas-Vilarrúbia, T. (2006). Unexpected biodiversity loss under global warming in the neotropical Guayana Highlands: a preliminary appraisal. *Global Change Biology*, 12, 1–6.
- Stull, R. (2011). Wet-Bulb Temperature from Relative Humidity and Air Temperature. *Journal of Applied Meteorology and Climatology*, 50(11), 2267-2269.

---

## Supplementary Materials

- **Supplementary Table S1**: Complete InfluxDB measurement schema (32 measurements, including wet-bulb temperature shutdown status and PID control mode)
- **Supplementary File S1**: Sanitized Node-RED flow configuration (`flows-sanitized.json`)
- **Supplementary File S2**: Grafana dashboard exports (4 dashboards)
- **Supplementary File S3**: Arduino watchdog v10 script and systemd service configuration
- **Supplementary File S4**: Detailed system architecture and data flow documentation
- **Supplementary File S5**: PID controller algorithm documentation with gain scheduling (including anti-windup, derivative filter, and rate limiting details)
- **Supplementary File S6**: Acrylic panel technical drawings — original fabrication specifications for all 20 panels plus add-on components (from *Progetto completo* and *Progetto adds-on 2022* design documents)
- **Supplementary File S7**: Arduino Mega firmware (`arduino-terrarium.ino`) — custom serial protocol sketch
- **Supplementary File S8**: Statistical analysis scripts (OLS, IV/2SLS, hourly A/B profiles, wet-bulb analysis, heat-balance regression) with data export tools
- **Supplementary File S9**: Meross power monitoring script
