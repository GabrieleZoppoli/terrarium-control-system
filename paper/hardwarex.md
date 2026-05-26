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

We present the design, construction, and four-year validation of an open-source weather-mimicking terrarium system that simulates highland cloud-forest climates using real-time meteorological data. The system ingests current weather from four Colombian highland cities (1,300–2,600 m elevation) and applies a 15-hour backward lookup against the locally archived time-series to generate continuously varying temperature and humidity setpoints. Combined with the 7-hour Italy-to-Colombia time-zone offset, the shift produces a phase-aligned daily cycle in which Colombian afternoon highs drive cabinet warmth at Italian midday and Colombian pre-dawn lows drive cabinet cooling at Italian midnight — reproducing the stochastic weather of tropical montane environments without inverting the day/night cycle. The enclosure is a ~1 m³ acrylic cabinet (1.5 × 0.6 × 1.1 m), and a dynamic photoperiod derived from the Colombian reference latitude (~5°N) drives a raised-cosine LED schedule (Light Curve C, deployed 2026-05-04) that provides seasonally varying day length and a +23 % daily-integrated-PAR uplift over the prior step schedule. The control system — built entirely on open-source software (Node-RED, InfluxDB, Grafana) running on a Raspberry Pi with an Arduino Mega for hardware I/O — implements a two-regime PID fan-control strategy (humidity-driven below 24 °C, temperature-driven at or above 24 °C, with the temperature-driven regime persisting through compressor engagement so that fans continue to act as a ceiling-defence cooling actuator). An instrumental-variables (2SLS) characterisation of the fan-to-humidity loop quantifies the causal effect of fan PWM on cabinet humidity at −0.34 % RH per +10 PWM units (95 % CI: −0.68 to −0.005; p = 0.047; n = 1,353), and a heat-balance regression over 80.3 days at 5-min cadence (n = 17,773; HC3 robust SEs) attributes the cooling work to the marine compressor (−1.01 °C/hr when active) with fan PWM showing no statistically detectable sensible-heat effect. An eleven-layer safety chain, evolved reactively in response to specific in-production failure modes and audited against a three-class detector-fragility taxonomy (dependency-loop / state-desync / stale-input-latch), handles operator and hardware failure modes. The system has operated continuously since May 2022 (four years at time of writing) at a measured power draw of **2.63 kWh/day (~€288/year at €0.30/kWh)**, currently maintaining **75 living accessions across 31 plant genera** drawn from three biogeographic provinces of the convergent cloud-forest biome (Neotropical highlands: Guayanan tepui, Andes, Brazilian Atlantic Forest; Southeast Asian highlands; Papua New Guinea / Oceania). All design files, control flows, firmware, dashboards, and analysis scripts are released under the CERN Open Hardware Licence v2 Permissive (CERN-OHL-P-2.0). Live cabinet conditions, build photographs, and operational logs are maintained at a companion website [21] (citable Zenodo DOI assigned at deposit); companion papers describe the horticultural results for carnivorous plants [18] and orchids [19], and the conservation/freeware-flagship synthesis appears in [20].

**Keywords**: open-source hardware, cloud forest terrarium, weather simulation, PID control, instrumental variables, causal inference, Node-RED, environmental monitoring, Raspberry Pi

---

## 1. Hardware in Context

Highland cloud forests — particularly the tepui table-top mountains of the Guiana Highlands in Venezuela — harbor extraordinary plant diversity adapted to narrow environmental envelopes: cool temperatures (10–22 deg C), persistent high humidity (80–100% RH), frequent fog immersion, and moderate light filtered through clouds [1]. Cultivating these species outside their native range presents formidable challenges, especially in climates with hot, dry summers.

Traditional terrarium controllers rely on fixed environmental setpoints (e.g., 18 deg C day / 14 deg C night, 90% RH constant), which fail to capture the stochastic variability that characterizes cloud forest environments. Natural tepui climates exhibit weather-driven fluctuations: sudden temperature drops during rain events, diurnal fog cycles, and seasonal variation in cloud cover. Static control oversimplifies the environment and may fail to provide the thermal and humidity cues that cloud forest species require for phenological processes.

Commercial terrarium controllers such as the MistKing HygroStat and similar products provide basic hysteresis control of humidity and temperature, but none ingest real-time weather data to produce dynamic setpoints. At the other end of the spectrum, laboratory growth chambers (Percival, Conviron) offer precise environmental control at costs of EUR 10,000–50,000+, with proprietary software that limits customization and data access.

A number of open-source environmental control systems have been described in HardwareX and adjacent venues, providing relevant reference designs but stopping short of the weather-mimicking concept. McDowell et al. (2021) [4] describe an internet-connected temperature controller for plant-growth experiments, providing a clean open-hardware template for sensor + actuator + remote-management but with fixed-setpoint control. Lau & Subbiah (2020) [5] present HumidOSH, a self-contained environmental chamber with relative-humidity and fan-speed control, focused on a single bench-top humidity envelope rather than diurnal or weather-driven variation. Sánchez et al. (2020) [6] document OpenTCC, a low-cost open-source temperature-control chamber demonstrating that compressor or Peltier hardware can be controlled cleanly from an open stack, again with fixed setpoints. Yuan et al. (2022) [7] develop an IoT framework for feedback control of photosynthetic activity in *Arabidopsis* — the closest conceptual prior art, since it closes a control loop on a biological signal rather than a programmed schedule, but it does not ingest external weather data. Iucci et al. (2026) [8] describe a compact modular hydroponic greenhouse with environmental sensing and control, aimed at production rather than ex-situ conservation of native-climate species. To our knowledge, **no published open-source system ingests real-time meteorological data from a geographically distinct reference site and applies a time-zone-aware phase shift to drive continuously varying environmental setpoints**, which is the gap the present design fills for terrarium-scale ex-situ conservation of cloud-forest taxa.

The system described here addresses this gap through six key innovations:

1. **Weather-mimicking from real meteorological data**: Real-time data from four Colombian highland cities generates stochastic, continuously varying setpoints that reproduce natural weather dynamics, including rain events and seasonal variation. When the live pipeline is stale (>10 min since last successful refresh), the controller transparently substitutes a 14-day rolling historical curve that itself is rebuilt every six hours from the InfluxDB archive, so the fallback follows seasonal drift without operator intervention.

2. **Two-regime PID fan control with ceiling-defence cooling**: The controller adapts its error signal based on cabinet temperature: humidity-driven below 24 °C, temperature-driven at or above 24 °C. The temperature-driven regime persists through compressor engagement — fans continue to act as an active ceiling-defence cooling actuator throughout the day even when the marine refrigerator is running, rather than being relinquished to the compressor.

3. **Causal characterisation of fan-mediated humidity control**: A randomised A/B fan-schedule experiment (n = 1,353 nighttime 5-min observations) enables an instrumental-variables (2SLS) estimate of the fan-PWM-to-humidity coefficient that is decorrelated from the PID's reaction to humidity disturbances. The companion 80.3-day heat-balance regression (n = 17,773; HC3) attributes essentially all the cooling work to the marine compressor and treats fan PWM as the humidity actuator — published quantification rather than a tuning heuristic.

4. **Dynamic photoperiod with raised-cosine LED schedule**: Day length is computed daily from the weather-source latitude, clamped to a biologically reasonable 10–14 h envelope, and bounds a raised-cosine LED brightness curve (Light Curve C, deployed 2026-05-04) centred on the source-latitude solar noon. The curve delivers a +23 % daily-integrated-PAR uplift over the prior step-schedule design and produces a smoother diurnal radiant load that the cooling chain can track without on/off transients at lights-on and lights-off.

5. **Eleven-layer safety chain with documented evolution + detector-fragility taxonomy**: Independent safety layers (door interlock, mister duration failsafe, freezer daytime gate, wet-bulb fan-off gate, manual-override timeout, USB-serial watchdog, LED-fault watchdog, power-vs-commanded cross-check, weather staleness fallback, Pi↔Arduino serial-link CRC integrity, mister water-level gate) accumulated over four years of operation in response to specific in-production failure modes. The deployment dates and incident provenance for each layer are recorded in a paper-bound single-source-of-truth YAML (`paper/safety_chain_deployment_dates.yaml`). A three-class detector-fragility taxonomy (dependency-loop, state-desync, stale-input-latch) audits each layer's failure modes against the others.

6. **Complete open-source stack**: All hardware and software components use freely available, commodity parts, making the system reproducible by hobbyists and small institutions. A live companion website (citable Zenodo DOI assigned at deposit) hosts current cabinet readings, photographic build documentation, and the operational blog.

---

## 2. Hardware Description

The Weather-Mimicking Biotope (WMB) is an acrylic terrarium with integrated cooling, humidification, lighting, and ventilation, controlled by a Raspberry Pi running Node-RED with an Arduino Mega for hardware I/O. The system continuously adjusts environmental conditions based on real-time weather data from Colombian highland cities, simulating the stochastic climate of tropical cloud forests.

Applications for researchers and educators include:

- **Ex-situ conservation**: Maintaining cloud-forest species from multiple biogeographic regions in a single enclosure, validated over four years with 75 living accessions across 31 plant genera from three biogeographic provinces (Neotropical highlands, Southeast Asian highlands, Papua New Guinea / Oceania)
- **Plant physiology studies**: Comprehensive data logging (33 InfluxDB measurements at 60-second intervals for continuous channels plus event-driven actuator-change logging; 3.1 million data points in the current 1-year retention window) enables analysis of plant responses to naturalistic environmental variation
- **Control systems education**: The system demonstrates PID control with gain scheduling, hysteresis control, multi-regime switching, instrumental-variables causal estimation of an actuator-to-state coupling, and a documented production-grade safety chain in an accessible, visual programming environment (Node-RED)
- **Template for other biomes**: The weather-mimicking architecture can be adapted to any biome by changing the reference weather stations (e.g., fog desert, alpine, lowland tropical) and the photoperiod-source latitude
- **Low-cost alternative to growth chambers**: Total hardware cost is a fraction of commercial growth chambers (€10,000–50,000+ for Percival/Conviron-class equipment), at a measured operational footprint of **2.63 kWh/day (~€288/year at €0.30/kWh)** for environmental control comparable to or superior to those instruments in this application class

---

## 3. Design Files Summary

| File name | File type | Open-source license | Location |
|---|---|---|---|
| `nodered/flows-sanitized.json` | Node-RED flow configuration | CERN-OHL-P-2.0 | `[Zenodo DOI — TBD]` |
| `firmware/arduino-terrarium.ino` | Arduino Mega firmware (C++) | CERN-OHL-P-2.0 | `[Zenodo DOI — TBD]` |
| `grafana/*.json` | Grafana dashboard exports (4 dashboards) | CERN-OHL-P-2.0 | `[Zenodo DOI — TBD]` |
| `scripts/arduino-watchdog.sh` | Serial watchdog script v10 (Bash) | CERN-OHL-P-2.0 | `[Zenodo DOI — TBD]` |
| `systemd/arduino-watchdog.service` | Systemd unit for the watchdog | CERN-OHL-P-2.0 | `[Zenodo DOI — TBD]` |
| `scripts/meross_daemon.py` | Meross MSS310 power-monitor daemon (Python, polled, publishes to MQTT + InfluxDB) | CERN-OHL-P-2.0 | `[Zenodo DOI — TBD]` |
| `systemd/meross-daemon.service` | Systemd unit for the Meross daemon | CERN-OHL-P-2.0 | `[Zenodo DOI — TBD]` |
| `scripts/terrarium-health.py` | Health-monitor cron script (Gmail + WhatsApp alerts; STUCK-RELAY auto-fix; LED-fault watchdog readout) | CERN-OHL-P-2.0 | `[Zenodo DOI — TBD]` |
| `scripts/mister-failsafe.py` | Mister cron failsafe (Tapo plug force-OFF if `on_time > 150 s`) | CERN-OHL-P-2.0 | `[Zenodo DOI — TBD]` |
| `scripts/snapshot-capture.sh` | Snapshot capture for the public companion-site mirror | CERN-OHL-P-2.0 | `[Zenodo DOI — TBD]` |
| `docs/schema.md` | InfluxDB measurement schema (33 measurements) | CERN-OHL-P-2.0 | `[Zenodo DOI — TBD]` |
| `docs/architecture.md` | System architecture documentation, including the layered safety chain | CERN-OHL-P-2.0 | `[Zenodo DOI — TBD]` |
| `docs/pid-controller.md` | PID algorithm documentation (gain schedule, anti-windup, manual-override semantics) | CERN-OHL-P-2.0 | `[Zenodo DOI — TBD]` |
| `analysis/*.py` | Analysis scripts (OLS heat-balance, IV/2SLS causal estimate, wet-bulb characterization, cooling-test reports) | CERN-OHL-P-2.0 | `[Zenodo DOI — TBD]` |
| `paper/energy_sot_*.yaml` | Single-source-of-truth block for the Meross-measured kWh figures cited throughout the manuscript | CERN-OHL-P-2.0 | `[Zenodo DOI — TBD]` |
| `S6-panel-drawings-*.docx` | Acrylic panel technical drawings | CERN-OHL-P-2.0 | `[Zenodo DOI — TBD]` |

**flows-sanitized.json**: Complete Node-RED flow configuration (~435 nodes across 7 tabs) with credentials removed. Covers all control logic: weather integration, PID fan control with two-regime switching, wet-bulb gate, dynamic photoperiod with Light Curve C, door safety, regime-aware mister hysteresis with water-level gate, data logging, and dashboard UI.

**arduino-terrarium.ino**: Custom text-based serial protocol firmware for Arduino Mega 2560. Handles PWM output on 5 channels (25 kHz phase-correct on Timers 1 and 5), door reed switch inputs with interrupt-based reading, heartbeat generation, and status reporting.

**Grafana dashboards**: Four monitoring dashboards — primary operational (temperature, humidity, VPD, actuator status), Colombian weather reference, system performance (PID diagnostics, fan PWM), and A/B experiment historical reference.

**scripts/arduino-watchdog.sh**: Watchdog v10 script monitoring USB connection health at 15-second intervals with four-step health checks and USB sysfs reset recovery.

**scripts/meross_daemon.py**: Long-running Python daemon that polls the Meross MSS310 in-line energy meter (variable cadence 2–120 s) and publishes power readings via MQTT into InfluxDB. Coexists with the older `meross_script.py` (single-shot variant, retained for compatibility); production deployments should use the daemon.

**scripts/terrarium-health.py**: Cron-driven (every 5 min) health monitor that cross-checks Tapo commanded state against Meross measured power, raises green/yellow/red conditions to Gmail + WhatsApp, runs the STUCK-RELAY auto-fix when the freezer is drawing power while commanded off, and reads the NR LED-fault flag. Includes N-sample hysteresis (3 polls) and a 120 s freezer-transition window to suppress poll-skew false positives. Credentials are placeholders in the published file.

**scripts/mister-failsafe.py**: Independent of Node-RED, runs every minute, force-commands the mister Tapo plug OFF if the plug's reported `on_time` exceeds 150 s. Last-resort guard against water damage from a controller hang or stuck relay.

**analysis/**: Python scripts for the published analyses, including the OLS heat-balance regression, the IV/2SLS causal estimate of the fan effect on humidity, the wet-bulb temperature characterization, and the maximum-cooling-capacity test reports.

**Acrylic panel drawings**: Original fabrication specifications for all structural panels (20 panels + 6 triangles + 2022 add-on set) with dimensions, hole positions, and material callouts.

---

## 4. Bill of Materials

> **BOM completion status (2026-05-13).** Component names, quantities, descriptions, and material types in the tables below have been mechanically cross-checked against §2 Hardware Description and §5 Build Instructions and are accurate as of this commit. **Unit cost, total cost, and source/supplier columns are pending a receipt sweep**: hardware receipts for this project are not in the repository — they sit in the author's Gmail vendor-order history and (for hardware-store items) in paper receipts. Each subsection below tags its likely receipt source with explicit Gmail-search hints so the Pass-D sweep can be completed in a single user-driven session. All quantities and component identities are unaffected by the sweep; only the cost / source columns will populate.

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

*Pass-D Gmail-sweep hints for §4.1*: Raspberry Pi 4 4 GB — search `from:noreply@raspberrypi.com OR from:amazon Pi 4`; Arduino Mega clone (CP210x) and ESP8266 NodeMCU — search `AZ-Delivery OR Banggood OR Amazon Mega 2560`; Sensirion SHT35 breakout — search `Adafruit OR Mouser SHT35` (likely Adafruit board ~€20); HC-SR04P + IRF520N + reed switches + USB hub — Amazon/Banggood commodity orders, search `HC-SR04P` and `IRF520`; TP-Link Tapo P100 ×3 — search `Tapo P100 order`; Meross MSS310 — search `Meross MSS310 order`; microSD — search `SanDisk OR Samsung microSD`.

### 4.2 Lighting

| Component | Qty | Description | Unit cost | Total cost | Source | Material type |
|---|---|---|---|---|---|---|
| ChilLED Logic Puck V3 (100 W) | 4 | LED grow light modules (244x Samsung LM301B) | `[PLACEHOLDER]` | `[PLACEHOLDER]` | `[PLACEHOLDER]` | Electronics |
| 140 mm aluminium pin heatsink | 4 | Passive thermal management | `[PLACEHOLDER]` | `[PLACEHOLDER]` | `[PLACEHOLDER]` | Metal |
| 12 V axial fan (heatsink cooling) | 4 | Convective heatsink cooling | `[PLACEHOLDER]` | `[PLACEHOLDER]` | `[PLACEHOLDER]` | Electronics |
| Mean Well HLG-480H-48A LED driver | 1 | 480 W, 48 V / 10 A, IP65 | `[PLACEHOLDER]` | `[PLACEHOLDER]` | `[PLACEHOLDER]` | Electronics |

*Pass-D Gmail-sweep hints for §4.2*: ChilLED Logic Puck V3 ×4 — search `chilledgrowlights.com OR ChilLED order` (likely a single order); 140 mm aluminium pin heatsink ×4 + 12 V axial fans ×4 — search `Aliexpress OR Amazon heatsink 140 mm`; Mean Well HLG-480H-48A — search `Mouser OR Meanwell HLG-480` (likely Mouser/Digi-Key).

### 4.3 Cooling

| Component | Qty | Description | Unit cost | Total cost | Source | Material type |
|---|---|---|---|---|---|---|
| Vitrifrigo ND50 OR2-V compressor unit | 1 | BD50F Danfoss variable-speed, R134a (HFC, ODP=0, GWP₁₀₀≈1430); factory-sealed, no F-gas certification required for installation | `[PLACEHOLDER]` | `[PLACEHOLDER]` | `[PLACEHOLDER]` | Mechanical |
| Vitrifrigo PT14 evaporator plate | 1 | 1220 x 280 mm stainless steel | `[PLACEHOLDER]` | `[PLACEHOLDER]` | `[PLACEHOLDER]` | Metal |
| Noctua NF-F12 iPPC-2000 IP67 (120 mm, 2000 RPM, 12 V) | 5 | Evaporator plate fans (x3) + circulation fans (x2) | `[PLACEHOLDER]` | `[PLACEHOLDER]` | `[PLACEHOLDER]` | Electronics |
| Noctua NF-A12x25 G2 PWM (120 mm, 12 V) | 2 | Condenser radiator fans in push-pull configuration | `[PLACEHOLDER]` | `[PLACEHOLDER]` | `[PLACEHOLDER]` | Electronics |
| Plexiglas plate | 1 | Evaporator airflow plate, inclined 30 deg with slit below | `[PLACEHOLDER]` | `[PLACEHOLDER]` | `[PLACEHOLDER]` | Plastic |

*Pass-D Gmail-sweep hints for §4.3*: Vitrifrigo ND50 OR2-V compressor unit + PT14 evaporator plate — search `Vitrifrigo order OR boatequipment OR Marine Outlet`; this is the highest single-item cost in the BOM, likely a single Italian marine-refrigeration supplier order (May 2022 install date). Noctua NF-F12 iPPC-2000 IP67 ×5 — search `Caseking OR Amazon NF-F12 iPPC`; Noctua NF-A12x25 G2 ×2 — search `Caseking OR Amazon NF-A12x25 G2` (separate later order from the iPPC industrial fans). Plexiglas plate — same source as the §4.6 acrylic order (local laser-cutter receipts, paper).

### 4.4 Humidification

| Component | Qty | Description | Unit cost | Total cost | Source | Material type |
|---|---|---|---|---|---|---|
| MistKing Standard diaphragm pump (24 V) | 1 | Misting system pump | `[PLACEHOLDER]` | `[PLACEHOLDER]` | `[PLACEHOLDER]` | Mechanical |
| MistKing nozzle assemblies | ~20 | Quad (x1), double (x6), single (x4) | `[PLACEHOLDER]` | `[PLACEHOLDER]` | `[PLACEHOLDER]` | Plastic/metal |
| ZipDrip anti-drip valve | 1 | Prevents residual dripping | `[PLACEHOLDER]` | `[PLACEHOLDER]` | `[PLACEHOLDER]` | Plastic |
| Tubing and fittings | 1 set | MistKing-compatible | `[PLACEHOLDER]` | `[PLACEHOLDER]` | `[PLACEHOLDER]` | Plastic |

*Pass-D Gmail-sweep hints for §4.4*: complete MistKing system (pump + nozzles + ZipDrip + tubing) — search `mistking.com order` (typically a single bundled order; nozzle counts and quad/double/single mix are listed in the table).

### 4.5 Ventilation

| Component | Qty | Description | Unit cost | Total cost | Source | Material type |
|---|---|---|---|---|---|---|
| Noctua 60 mm fan (12 V) | 2 | Outlet ventilation fan (×1, pin 45) + impeller ventilation fan (×1, pin 46), rear ventilation ports per §2.2 | `[PLACEHOLDER]` | `[PLACEHOLDER]` | `[PLACEHOLDER]` | Electronics |

*Pass-D Gmail-sweep hints for §4.5*: Noctua 60 mm fans (typically NF-A6x25 5V) ×2 — search `Caseking OR Amazon Noctua 60 mm` (may be the same Caseking order as the §4.3 NF-A12x25 G2 or a separate later top-up).

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

*Pass-D Gmail-and-paper-sweep hints for §4.6*: laser-cut acrylic panels (PMMA 10/8/5 mm, mirror 2 mm, black 4 mm, perforated 3 mm) — Italian laser-cutter receipt (paper); the user's local custom shop, single panel-order invoice. XPS insulation + Mylar reflective + DCM + c-Si silicone — local hardware-store paper receipts (Leroy Merlin / Brico / Ferramenta). Aluminium scaffold + door tracks — workshop / metal-supplier paper receipt (2022 install).

### 4.7 Reservoirs and Plumbing

| Component | Qty | Description | Unit cost | Total cost | Source | Material type |
|---|---|---|---|---|---|---|
| 40-liter reservoir | 2 | Misting supply + condensate collection | `[PLACEHOLDER]` | `[PLACEHOLDER]` | `[PLACEHOLDER]` | Plastic |

*Pass-D Gmail-sweep hints for §4.7*: 40-L food-grade plastic reservoirs ×2 — search `Amazon OR DIY-store reservoir` (commodity; may be from the same MistKing order if bundled, otherwise hardware-store paper receipt).

---

**Top-of-BOM consolidated Pass-D action list** (single user session, ~30 min in Gmail):

1. `Vitrifrigo` (ND50 OR2-V + PT14 evaporator) — single Italian marine-refrigeration supplier order, May 2022 area.
2. `chilledgrowlights.com` — Logic Puck V3 ×4 order.
3. `Mouser` or `Meanwell` — HLG-480H-48A LED driver.
4. `Caseking` or `Amazon` Noctua — NF-F12 iPPC-2000 IP67 ×5 + NF-A12x25 G2 ×2 + 60 mm ×2 (likely two or three separate orders).
5. `mistking.com` — pump + nozzles + ZipDrip + tubing bundled order.
6. `Tapo P100` Amazon order — ×3.
7. `Meross MSS310` Amazon order — ×1.
8. `Adafruit` or `Mouser` SHT35 breakout — ×1.
9. `Amazon` / `AZ-Delivery` commodity electronics order(s) — Pi 4, Arduino Mega clone, ESP8266, HC-SR04P, IRF520N, reed switches, USB hub, microSD.
10. Paper receipts — laser-cut acrylic panels, XPS + Mylar, DCM + silicone, aluminium scaffold + door tracks, 40-L reservoirs.

Once those ten threads are pulled, the cost / total / source columns can be filled mechanically. The component identities and quantities in the tables above are already verified against §2 and §5; the sweep will not change them.

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

The Vitrifrigo ND50 is a split-system marine refrigeration unit shipped pre-charged with R134a (HFC, ozone-depletion potential = 0, GWP₁₀₀ ≈ 1430) in a sealed circuit; no F-gas handling certification is required for installation. The compressor and condenser are mounted external to the cooled space, with refrigerant lines connecting them through a sealed pass-through to a separate evaporator plate inside. The compressor unit sits above the terrarium, and the evaporator plate is mounted **horizontally on the rear wall in the lower portion of the enclosure** (cutout centred at ~20 cm above the cabinet floor — see back-panel drawing `panel-03-with-radiator` in the Design Files). This is mechanical refrigeration — not evaporative cooling.

Marine refrigeration is a distinct hardware category from the better-known DIY compressor-cooling routes (chest-freezer conversions, aquarium chillers, modified portable air conditioners) and three replicator-relevant properties recommend it for terrarium use: (i) **installation is mechanical, not refrigeration work** — the unit ships as a complete factory-assembled split system, so no field plumbing of the cold loop and no system charging is required; (ii) **the unit class scales to enclosure size** — Vitrifrigo and equivalent marine-refrigeration vendors offer compressor/evaporator combinations spanning roughly 30–200 L cold-storage capacity with several evaporator plate footprints, so terraria between ~0.3 m³ and ~3 m³ can be matched without custom engineering; (iii) **factory-sealed pre-charged loop = no F-gas certification needed for installation** under EU/UK rules (the certification requirement applies to filling or topping up the refrigerant, not to installing a sealed unit), removing a skills barrier that has historically restricted DIY compressor-based terrarium cooling. Repairs on the cold loop *do* require certification — a faulty unit is replaced or serviced by a marine-refrigeration shop rather than user-repaired.

The low evaporator placement establishes a desirable vertical climate gradient inside the cabinet. Cold (and therefore dense) air sinking from the evaporator plate pools near the cabinet floor and rises by convection as it warms, while the LEDs are mounted above the cabinet. The result is **a warmer, brighter upper canopy and a cooler, shadier floor** — the inverse-stratified arrangement reproduces the natural moss-and-bryophyte zonation found near the base of cloud forest trunks and rocks.

1. Place the Vitrifrigo ND50 OR2-V compressor unit on a frame or shelf above the terrarium, with adequate clearance for the condenser radiator and fans to exhaust heat away from the enclosure.

2. Mount the Vitrifrigo PT14 evaporator plate horizontally on the inside of the rear wall, with the upper face of the plate ~20 cm above the cabinet floor. Route the refrigerant lines from the compressor through a sealed pass-through in the top panel. Ensure the evaporator's condensate drain leads, via gravity, to the condensate reservoir on the shelf below the terrarium.

3. Mount a plexiglas baffle in front of the evaporator plate, inclined approximately 30° from horizontal. Leave a slit between the lower edge of the baffle and the cabinet floor so that the cold air sinking off the evaporator is channelled downward and discharged at floor level.

4. Evenly space three Noctua NF-F12 iPPC-2000 IP67 fans on the plexiglas baffle, oriented to draw warm interior air across the evaporator surface.

5. Mount two additional Noctua NF-F12 iPPC-2000 IP67 fans separately within the cabinet for general internal circulation.

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
- **12 V DC**: All internal Noctua fans (NF-F12 iPPC-2000 evaporator + circulation, 60 mm outlet + impeller, NF-A12x25 condenser push/pull). The IRF520N MOSFET modules switch the 12 V power rail at 25 kHz; the fans' own 4-pin PWM inputs are left unconnected. Heatsink-fan supply (4× 12 V axial above the LED pucks) shares the same rail.
- **24 V DC**: MistKing diaphragm pump only.
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

- **Weather polling**: Current conditions fetched from four Colombian cities and heavily smoothed (15-minute rolling mean) into temperature/humidity setpoints. The 15-hour data buffer makes aggressive smoothing cost-free. If the live pipeline is stale (>10 min), the controller transparently substitutes a smoothed 14-day rolling historical daily curve that is itself rebuilt from the InfluxDB archive every six hours, so the fallback follows seasonal drift without operator intervention.
- **Photoperiod calculation and Light Curve C**: Day length is computed daily from the Chinchina latitude (clamped to 10–14 h) and bounds a raised-cosine brightness curve (Light Curve C) centred on the source-latitude solar noon. The curve replaced the prior two-step ramp (deployed 2026-05-04) and delivers a +23 % daily-integrated-PAR uplift while smoothing diurnal radiant-load transients.
- **PID fan control (two regimes)**: Below 24 °C, the PID drives fans on humidity error (humidity-driven regime); at or above 24 °C, the PID switches to temperature error and continues to drive fans on temperature even after compressor engagement (temperature-driven regime, retained as a ceiling-defence cooling actuator throughout daylight LED load).
- **Mister control**: A regime-aware humidity hysteresis controller fires the mister when humidity drops below the lower threshold, with automatic fan shutdown during misting events. The mister command is also gated by an upstream water-level precondition (ESP MQTT tank-percent ≥ 10 % and < 5 min old) so dry-run cannot be initiated.
- **Compressor control**: Hysteresis controller activates the compressor when temperature exceeds 25 °C (daytime, with a thermal-override that lifts the daytime gate if the cabinet runs warmer than 25 °C) or the weather-capped target (nighttime).
- **Wet-bulb gate**: After lights-off, outlet and impeller fans shut down between the first compressor engagement and 05:00 (latched until the window closes), reducing fan-mediated room-air mixing during the cool nocturnal phase.
- **Data logging**: A continuous stream of 33 InfluxDB measurements at 60-second cadence (continuous channels) plus event-driven actuator-change logging; the 1-year retention window typically holds ~3.1 million data points.

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

#### Build-time hazards

- **Electrical safety with water**: All mains wiring must use drip loops. Smart plugs and power supplies should be positioned where they cannot be splashed. The IP65-rated Mean Well driver provides moisture protection for the LED driver.
- **DCM handling**: Dichloromethane is volatile and toxic. Use only in well-ventilated areas during construction.
- **Compressor refrigerant**: The Vitrifrigo unit ships pre-charged with R134a and factory-sealed; no F-gas certification is required for installation. Refilling or any work on the sealed loop *does* require certification in EU/UK jurisdictions.

#### Operational safety chain

The system runs unattended for months at a time, and the layered safety architecture below evolved over the four-year operating history of the cabinet (May 2022 to present) in response to specific real-world failure modes — ten of the eleven layers were added reactively as failure modes were encountered, not designed up-front. Each layer operates independently of the others; failure of one does not disable the rest. All layers log to the InfluxDB time-series database for post-hoc audit. Deployment dates per layer are sourced from `paper/safety_chain_deployment_dates.yaml` in the Design Files, which triangulates Node-RED flow-backup filenames, systemd unit-file mtimes, the operator's memory journal, and in-repo `git log` evidence; the earliest *reconstructible* deployment is 2026-02-06 (the Arduino USB-serial watchdog systemd install), but layers with the same identifiers had earlier precursors that are not preserved on disk — the NR backup directory was started 2026-02-08 as a flow-edit-discipline practice and pre-February-2026 revisions are no longer available for archaeology.

The chain is also audited against a **three-class detector-fragility taxonomy** that catalogues how a safety detector itself can fail: (i) **dependency-loop** — the detector's input depends on the same chain it is supposed to detect failures in (e.g., a stuck-relay check whose own poll path shares state with the actuator it would auto-fix); (ii) **state-desync** — the detector compares asynchronously polled signals whose update cadences differ, so single-sample comparisons race during transitions; (iii) **stale-input-latch** — the detector consumes an upstream signal that is "fresh" by clock but frozen by content (e.g., a cached weather global re-served indefinitely after upstream failure). Every layer in the chain has been audited against this taxonomy and its mitigations (N-sample hysteresis, transition-window suppression, freshness timestamps, fail-closed defaults) are noted inline in the per-layer descriptions below.

1. **Door safety interlock** (deployed 2026-02-16). Two magnetic reed switches on the sliding front doors are read by the Arduino. When either door opens for more than 3 seconds (debounce against vibration), Node-RED commands all internal fans off, the compressor off, the mister off, and the LEDs to 60% (working-illumination brightness). All systems restore automatically when both doors close. The interlock protects the plants from cold-air loss with the door open, protects the operator from running fans during inspection, and protects the misting pump from spraying outside the enclosure. **Operator-initiated maintenance override**: when the Dashboard fan-mode toggle is set to `manual` (Max or Pause), the door-safety chain still cuts the compressor, mister, and LEDs on door-open, but the fan stop/restore is bypassed — by design, so the operator can run airflow at full while cleaning or drying the enclosure with the lid off. This deliberate exception is documented in `docs/pid-controller.md`; the manual-override timeout (item 5 below) ensures the bypass is bounded in time.

2. **Mister duration failsafe** (deployed 2026-04-16). A cron-driven Python script (`mister-failsafe.py`) runs every minute and force-commands the mister Tapo plug OFF if the reported on-time exceeds 150 s. This bounds water damage from a Node-RED hang, a stuck Tapo relay, or a controller misconfiguration.

3. **Freezer daytime gate** (deployed 2026-04-11). Within Node-RED, the compressor is blocked from running during 08:00–20:00 CEST regardless of setpoint error. This guards against a stale or extreme nighttime target carrying over into daylight and producing runaway cooling that overshoots safe biological ranges. The layer was added the day after a 2026-04-10 Tailscale-DNS outage froze the OpenWeatherMap target at a nighttime value for 18 h, causing the freezer to chase a stale low setpoint into the morning.

4. **Wet-bulb fan-off gate** (deployed 2026-02-25; **rationale deprecated 2026-05-12**). After lights-off, the outlet and impeller fans are disengaged once the cabinet temperature falls below the room's wet-bulb temperature. The gate was originally introduced under the hypothesis that sub-WBT fan operation imports room sensible heat at a measurable rate; the 80.3-day heat-balance analysis on the larger dataset (§7.4) finds no statistically detectable fan effect on cabinet-temperature derivative when fan PWM is modelled at its native resolution. The gate's current empirical role is therefore limited to reducing fan duty cycle (and, indirectly, fan-mediated room-air mixing) during the cool nocturnal window; the firmware path is retained as a deployed feature but the paper does not advance it as a load-bearing finding.

5. **Manual-override timeout** (deployed 2026-05-09). The Dashboard provides operator buttons (Auto / Pause / Max) that bypass automatic fan control. To protect against an unintended persistent override (e.g., a "pause" left active after maintenance), a watchdog reverts the override to AUTO after 30 minutes of no fresh operator input. The persistence timestamp lives in a persisted global so the timeout survives controller restarts. The layer was added after a 2026-05-09 near-miss in which Pause was left active for 14 h, internal fans at 0 PWM, cabinet temperature climbed to 27.8 °C for ~5 h.

6. **Arduino USB-serial watchdog** (deployed 2026-02-06; active-recovery logic added 2026-02-17, cold-start bug fixed 2026-04-08). A bash script (`arduino-watchdog.sh`) runs as a systemd service, monitoring the Arduino's heartbeat byte on analog input A0. If the heartbeat is silent for >30 s, the script performs a USB sysfs re-authorize on the affected port, restoring serial communication in 15–30 s. The watchdog was developed in response to a recurring Pi-4 USB hub stall (Section 7.6).

7. **LED-fault watchdog** (deployed 2026-05-04; model recalibrated 2026-05-05). The PWM dim-signal line to the Mean Well driver is a known weak point; an intermittent connector float drives the driver to its cap-limited maximum, producing a 280–377 W draw with no command. Node-RED monitors the Meross-reported power and the commanded dim level; sustained mismatch for 90 s flags a fault and disables the LED Tapo plug. Brief transients are counted separately (see Section 7.6) without triggering a hard shutdown. The flat-threshold version landed 2026-05-04 in response to a +200 W Mean Well runaway observed that day; the model-based detector that is currently deployed (`expected = base + 2.8 × eff_slider + 170 W if freezer-on`) replaced it 2026-05-05 after the flat threshold false-tripped during normal Curve C peak draw.

8. **Power-vs-commanded cross-check / STUCK-RELAY auto-fix** (deployed 2026-04-11; hysteresis hardened 2026-05-11). An out-of-process Python monitor (`terrarium-health.py`, cron `*/5 * * * *`) compares the Meross MSS310 instantaneous power reading against an expected wattage computed from the commanded Tapo states and the current dimmer slider position. Three guards prevent false positives that would otherwise propagate into harmful auto-fix commands: (i) N-sample hysteresis — STUCK is declared only after three consecutive 5-minute cycles of >70 W excess; (ii) transition-window suppression — the check is skipped within 120 s of any freezer state change, when Tapo cache and Meross averaging are demonstrably out of sync; (iii) fresh re-poll before action — the Tapo state is re-fetched immediately before any auto-fix cycle, and the action is skipped if the plug is already in the desired state. The underlying cross-check was cron-resident from 2026-04-11; the three guards were added 2026-05-11 after two false STUCK-RELAY events on 2026-05-10/11 traced to Tapo/Meross polling-skew races. The power model was refit from seven days of clean (freezer-OFF, mister-OFF) measurements; see Section 7.6.

9. **Weather staleness fallback** (deployed 2026-04-10; further hardened 2026-05-15). If the OpenWeatherMap pipeline has not refreshed the setpoint in 10 minutes (network outage, API quota, DNS error), Node-RED transparently substitutes a smoothed 14-day historical daily curve for the live data. The 14-day curve is itself **rebuilt every six hours** from a rolling InfluxDB query against the locally archived Colombian time-series, so the fallback automatically follows seasonal drift without operator intervention. The cabinet continues to follow naturalistic-looking setpoints rather than the controller's last-known-good static value. The 14-day curve substrate itself was deployed 2026-03-05; the 10-minute staleness trigger that makes this a *safety* layer (rather than a passive default) was added 2026-04-10 after the same Tailscale-DNS outage that motivated the freezer daytime gate (item 3 above); subsequent hardening on 2026-05-14/15 ensured the fallback drives the freezer-hysteresis threshold and the OWM-staleness branch, not only the cached globals. Detector-fragility class: stale-input-latch (mitigated by the 10-minute freshness check on `target_weather_updated` and a separate stamp on the OWM city-poll path).

10. **Pi↔Arduino serial-link integrity** (deployed 2026-05-18). Every command written to the Arduino is a single, atomic newline-terminated payload (one `write()` syscall per command, no bundling of multiple commands into a single kernel write) carrying a CRC-8 byte that the Arduino validates before any GPIO write. The Arduino replies `ERR_CRC` on mismatch and the Pi retries on any `ERR` class, not only on timeout. This closes a 91-day failure class (2026-02-16 → 2026-05-18) in which kernel splitting of multi-line bundled writes at unlucky byte boundaries caused the Arduino parser to see truncated commands (e.g. `P8,1` rather than `P8,134`), latching wrong PWM values for one ramp tick and producing visible brightness or fan-speed spikes; the bug had previously been hypothesised as hardware/EMI rather than an OS-layer write-splitting artefact. Defence-in-depth: the atomic-write rule precludes the diagnosed root cause at the OS layer, and the CRC byte at the controller layer catches any partial command that would otherwise slip through if the atomic-write rule regressed.

11. **Mister water gate** (deployed 2026-05-18). Upstream of the mister Python node, an ESP8266 ultrasonic sensor publishes tank-level percent via MQTT every 10 s. A gate function rejects any mister "on" command if the most recent tank-percent message is older than 5 minutes (stale-sensor, fail-closed) or below 10 % (low-reservoir). All mist sources — the regime-aware humidity-driven trigger, the dawn-mist cron inject, and the Dashboard manual button — funnel through the same gate, so the precondition is checked once at the authority boundary rather than per-source. This eliminates the precondition for the dry-run pump damage class observed on 2026-03-02 (empty reservoir, mister still firing); the older mister-duration failsafe (layer 2) bounds the worst-case damage of a started cycle but does not prevent starting one without water, so the two layers are complementary rather than redundant. Detector-fragility class: stale-input-latch (mitigated by the 5-minute freshness window and a fail-closed default).

The health-monitor reports a green/yellow/red status every five minutes and pushes immediate notifications (Gmail + WhatsApp via CallMeBot) on any non-green condition with a 30-minute dedupe window. A six-hourly green digest confirms the system is alive. Since the deployment of the per-section sitrep digest (2026-05-25), two scheduled emails per day at 07:00 and 21:00 also deliver a five-section operational snapshot (operating envelope, stack health, pending checkpoints, recent activity, no-go signals) that an operator can read in under a minute.

---

## 7. Validation and Characterization

### 7.1 Environmental Performance

Two monitoring windows are reported separately across §7: the **94-day full-sensor InfluxDB-retention window** (per-minute environmental and actuator data, covering the rolling retention horizon at the time of writing) and the **80.3-day Meross-instrumented window** (2026-02-18 → 2026-05-10) for power, uptime, and heat-balance regressions that depend on the Meross daemon's deployment date. Over the 94-day full-sensor window, the cabinet maintained:

| Parameter | Minimum | Maximum | Typical range | Target envelope |
|---|---|---|---|---|
| Temperature | 13.5 °C | 24.3 °C | 15–22 °C | Weather-derived, clamped to 12–24 °C |
| Relative humidity | 75 % | 98 % | 83–95 % | Weather-derived, clamped to 75–95 % |
| VPD | 0.03 kPa | 0.64 kPa | 0.08–0.45 kPa | < 0.8 kPa |
| Time at RH ≥ 95 % ("fog hours") | — | — | 1.25 h/day (94-day average) | Naturalistic — set indirectly via weather mapping |
| Time outside target ± 2 % RH | — | — | < 8 % of operating hours | < 10 % |

The cabinet achieves a meaningful diurnal temperature swing despite the room running at approximately 22 °C year-round. Nighttime cabinet temperature routinely drops to 14–16 °C under active compressor cooling, while daytime temperature rises to 18–22 °C, producing a 4–8 °C daily amplitude that approximates conditions on mid-elevation tepuis [Rull & Vegas-Vilarrúbia, 2006].

Light operates on a raised-cosine schedule with a 60 % hardware ceiling (Mean Well driver potentiometer) and a software-controlled PWM ramp on top. The photoperiod is computed daily from the Chinchina reference latitude (4.98 °N), clamped to 10–14 h to provide seasonal variation without the abrupt cliffs that would occur at extreme equatorial latitudes. The dim curve is centred on solar noon (≈13:15 CEST at the cabinet's installation site) and produces a peak measured cabinet power draw of 220 W ± 3 W (n = 255 measurements at midday, freezer and mister off). Direct measurement of canopy PPFD (μmol·m⁻²·s⁻¹) and integrated daily DLI (mol·m⁻²·d⁻¹) is pending the installation of a quantum sensor and will be reported in the final submission.

`[PLACEHOLDER — Grafana screenshots: representative 24-hour and 7-day temperature/humidity cycles; available from companion website `<URL>/highland/dashboard/` for current snapshots]`

### 7.2 PID Controller Stability

The gain-scheduled PID controller maintains humidity within ±3 % RH of the setpoint under steady-state conditions, producing smooth fan-speed transitions that eliminate the continuous cycling characteristic of simpler hysteresis controllers.

The gain scheduling was critical: with fixed gains, the controller exhibited ±25 PWM oscillations near the setpoint. After implementing the gain schedule (effective Kp = 7.5 within ±1.5 % of target, full Kp = 50 for errors ≥ 4 %), these oscillations were eliminated. Anti-windup limits the integral term to ±120 PWM-equivalent, and a low-pass filter (α = 0.12) attenuates derivative noise from sensor jitter.

The causal effect of the fans on cabinet humidity was estimated using a controlled A/B experiment conducted from December 2025 to February 2026, in which the night fans alternated nightly between off and PWM = 80. Treating the day-of-experiment indicator as an instrumental variable in a two-stage least-squares specification removes the endogeneity bias of regressing humidity on the PID-driven fan speed (the PID drives the fans *in response to* humidity, so OLS would yield a reverse-causal coefficient). The IV/2SLS estimate is **−0.34 % RH per +10 PWM of fan speed (95 % CI: −0.68 to −0.005; p = 0.047; n = 1,353 nighttime 5-minute observations; first-stage F = 22.5)**. The naive OLS comparator returns +0.15 % per +10 PWM — the wrong sign — confirming the reverse-causal bias of the simple regression. By comparison, compressor activation produces a −15.9 % long-run humidity effect; the compressor is the dominant dehumidification actuator, with PID-driven fans providing fine adjustment within the compressor's hysteresis band. The night-fan A/B experiment was retired in February 2026 once the coefficient was characterised; raw data and analysis scripts remain in the project repository under `analysis/02_iv_causal_model.py`. A follow-on morning-fan A/B (April–May 2026) was retired after 13 days when the treatment effect (≤ 0.5 % RH, p = 0.91) fell inside the residual noise band.

`[PLACEHOLDER — Grafana screenshot showing PID response to a humidity disturbance; companion website serves a live PID-diagnostics dashboard at `<URL>/highland/dashboard/`]`

### 7.3 Two-Regime Fan Control

The two-regime strategy (Section 6.2) switches the PID's error signal based on cabinet temperature:

- **Normal regime** (< 24 °C): PID drives fans based on humidity error. This is the predominant operating mode during most of the year — Italian shoulder seasons and the cabinet's nighttime envelope sit well below the 24 °C threshold, so humidity is the actuator's primary target.
- **Hot regime** (≥ 24 °C): PID switches to temperature error scaled by TEMP_ERROR_SCALE = 5 (mapping 0–1 °C excess to 0–5 PID-equivalent units). Fans ramp aggressively to act as a ceiling-defence cooling actuator. **The temperature-driven regime persists through compressor engagement** — fans are not relinquished to the compressor when the freezer activates, because daytime LED radiant load is continuous and the compressor alone cannot maintain a stable ceiling against it without the fans running in T-PID mode. This is the principal architectural change from the prior three-regime design (active 2026-02-25 → 2026-05-25), in which a separate "Hot regime with compressor on" reverted to H-PID and relinquished thermal control entirely to the compressor; the simplified two-regime control was deployed 2026-05-25 immediately before the first daytime freezer engagements of summer 2026 (Genoa room temperature stepped up by +2.7 °C overnight on 2026-05-22, surfacing the daytime ceiling-defence requirement).

Mode transitions reset the integral, derivative, and last-error state to prevent discontinuities. The current control mode is logged to InfluxDB (`pid_control_mode`: 0 = humidity, 1 = temperature) for analysis. In Hot regime the error is computed against a **hardcoded 24.0 °C** ceiling rather than against the dynamic `target_temp`, so the fans always defend the 24 °C ceiling regardless of where the slow weather-derived setpoint sits.

### 7.4 Heat-Balance Decomposition

A heat-balance regression decomposes actuator contributions to the cabinet's temperature dynamics. Model:

`dT_cab/dt = α₀ + α₁(T_room − T_cab) + α₂·fan_PWM + α₃·freezer_on + α₄·light_on + α₅·fan_PWM·freezer_on + ε`

fit by OLS with HC3 robust standard errors to n = 17,773 5-minute observations over the 80.3-day Meross-instrumented window (2026-02-18 → 2026-05-10). Cabinet-temperature derivative computed by centred finite difference. Full structured output and script in `paper/heat_balance_run_2026-05-12.yaml` and `analysis/heat_balance_rerun.py` (Design File row 86).

| Term | Coefficient | 95 % CI | p | R² |
|---|---:|:---:|---:|---:|
| Compressor (freezer active) | −1.01 °C/hr | [−1.05, −0.97] | <10⁻³⁰⁰ | — |
| Room↔cabinet passive exchange (per +1 K gradient) | +0.17 °C/hr | [+0.14, +0.19] | <10⁻⁴⁰ | — |
| LEDs (lights on) | −0.34 °C/hr | [−0.44, −0.25] | <10⁻¹¹ | — |
| Fan PWM (continuous, per PWM unit 0–255) | +0.0002 °C/hr | [−0.0002, +0.0005] | 0.33 | — |
| Model fit (Model 2, full sample) | — | — | F = 545 (p < 10⁻³⁰⁰) | 0.163 |

The marine compressor performs essentially all of the active cooling work. The steady passive room↔cabinet exchange (+0.17 °C/hr per K gradient) is the only term that opposes compressor cycling on the temperature axis; LEDs contribute a small negative term once their power load is factored. **Fan PWM, modelled at its native resolution (0–255), shows no statistically detectable effect on the cabinet-temperature derivative** in this 80.3-day dataset (95 % CI brackets zero; p = 0.33).

A comparison model substituting a binary `fans_on` indicator for the continuous PWM signal returns a positive coefficient of +0.27 °C/hr (95 % CI [+0.13, +0.40]; p = 1.4 × 10⁻⁴). This is a schedule-confound artefact, not a fan-specific effect: in this system, the outlet and impeller fans are commanded ON whenever the freezer activates and during the bright part of the day, so a binary `fans_on` regressor absorbs covariance from the freezer and the lights. The smallest eigenvalue of the binary-model design matrix is 1.44 × 10⁻²⁷, confirming near-singularity. Once the fan signal is modelled at full PWM resolution, the apparent +0.27 °C/hr "fan warming" dissolves into the freezer and light terms.

The architectural reading is that **fan PWM is the high-resolution humidity actuator** (its causal effect on humidity is quantified separately in §7.2 at −0.34 % RH per +10 PWM, IV/2SLS), not a sensible-heat term. Room conditions over the same window were consistent at 22.1 ± 0.7 °C and 57.9 ± 5.2 % RH, corresponding to a wet-bulb temperature of 16.6 ± 0.9 °C (Stull 2011); the cabinet routinely crossed below this threshold at 20:00–21:00 each evening as the compressor drove temperatures down. The wet-bulb fan-off gate documented in §6.6 (layer 4) was originally introduced under the hypothesis that sub-WBT fan operation imported room sensible heat at a rate of +0.37 °C/hr derived from a 27-day preliminary regression; the full 80.3-day rerun does not support that quantity at the per-PWM resolution at which the controller actually drives the fans, and the gate's empirical benefit on cabinet temperature is statistically null in this system. The gate is retained in the deployed firmware as a documented hardware feature; the paper does not advance it as a load-bearing finding.

### 7.5 Weather Correlation

The Colombian weather integration produces continuously varying setpoints that reflect real meteorological conditions. The 15-hour backward lookup against the locally archived Colombian time-series is best understood in combination with the 7-hour Italy-to-Colombia time-zone offset: their sum (~22 hours) is close to a full diurnal cycle, so the cabinet's target at any Italian local time tracks Colombian weather from approximately the same time-of-day, one day earlier. Concretely, at Italian noon (10:00 UTC) the controller retrieves Colombian conditions from 15 h prior (19:00 UTC yesterday = 14:00 Colombian local time, afternoon, warm and slightly drier), and at Italian midnight (22:00 UTC) it retrieves Colombian data from 07:00 UTC same day = 02:00 Colombian local time, the pre-dawn minimum (cool and near-saturated). Without the 15-hour shift, the cabinet would be driven by current Colombian conditions and the time-zone offset would produce a biologically inverted cycle — cool/humid during the Italian afternoon and warm/drier overnight. The shift is therefore not a stochastic delay but a deliberate phase correction that aligns the cabinet's day/night cycle with Italian local time while preserving the stochastic weather content from the Colombian source. Cross-validated against the cabinet's own measured target temperature over a representative 7-day window (n = 154 hourly pairs), the cabinet target tracks the 15 h–prior Chinchinà temperature with Pearson r = 0.73; the residual variance is dominated by the 24 °C target ceiling clamp that bounds the warmest daytime targets.

The stochastic character of real weather data is a key advantage over fixed schedules. Rain events in Colombia produce corresponding setpoint changes, creating sudden environmental perturbations — simulated fog immersion events — that vary from day to day and season to season.

### 7.6 System Reliability

The primary recurring fault is a USB-serial stall in which the Arduino's CP210x bridge enters a stuck state, silently halting communication after variable periods (mean inter-stall interval ≈ 36 h in the current configuration; this appears to be a hardware-level interaction with the Pi 4's internal USB hub rather than a protocol issue). The serial watchdog (`arduino-watchdog.sh`, systemd service, 15-second check interval) detects absent heartbeat bytes and triggers a USB-sysfs re-authorize on the affected port; mean recovery time from stall detection to restored I/O is 22 s (std 6 s) across the logged events in the current monitoring window.

Beyond the serial watchdog, the eleven-layer safety chain described in Section 6.6 evolved over the four-year operating history of the cabinet (May 2022 to present) in response to specific failure modes encountered during operation — the chain was built reactively rather than designed up-front, and is audited against a three-class detector-fragility taxonomy (dependency-loop, state-desync, stale-input-latch) before each layer is added or modified. The earliest *reconstructible* deployment is 2026-02-06 (Arduino USB-serial watchdog systemd install); per-layer deployment dates are listed in §6.6 above and triangulated from artefact evidence in `paper/safety_chain_deployment_dates.yaml`. The Node-RED flow-backup directory began on 2026-02-08 as a flow-edit-discipline practice, and pre-February-2026 revisions of these layers are not preserved on disk; the four-year framing therefore refers to the cabinet's continuous operating history, not to artefact-reconstructible safety-chain history. Five of the eleven layers — the manual-override timeout (layer 5, 2026-05-09), the LED-fault watchdog (layer 7, 2026-05-04 with 2026-05-05 model recalibration), the STUCK-RELAY hysteresis hardening on the power-vs-commanded cross-check (layer 8, 2026-05-11), the Pi↔Arduino serial-link CRC integrity (layer 10, 2026-05-18), and the mister water gate (layer 11, 2026-05-18) — landed during or after the 80.3-day Meross-instrumented window, so they underwrite *future* reliability rather than retrospective 80-day reliability per `uptime_sot_2026-05-13.yaml#note_for_pass_c`.

The reliability evidence the chain has accumulated over the 80.3-day Meross-instrumented window (2026-02-18 → 2026-05-10) is summarised in the following entries:

- **Stuck-relay detections.** Two false-positive STUCK-RELAY events fired on 2026-05-10/11 before the power-vs-commanded cross-check was hardened. Root cause: the lights-power model under-estimated draw at the raised-cosine peak. The model was refit from seven days of clean (freezer-OFF, mister-OFF) data and now lands within 4 % of the measured 220 W peak (Section 7.7); no false positives have occurred since. Three independent guards (N-sample hysteresis, transition-window suppression, fresh re-poll before action) collectively bound the auto-fix to genuine, sustained anomalies.
- **Door-safety activations.** Door-safety mode triggered on every maintenance access (mean 2.4 events per week in the current window) and restored normal operation on every door close, with no observed false interlock and no failed restore.
- **Manual-override timeout.** The 30-minute auto-revert was added on 2026-05-09 after an operator pressed "Pause" and did not return; the override persisted for 14 hours with all internal fans at 0 PWM. Cabinet temperature climbed to 27.8 °C (3.8 °C above the daily setpoint) for ~5 hours; no plant losses were observed but the incident was a near-miss. Since the timeout was deployed, no override has been left active beyond 30 minutes.
- **LED transient counts.** The Mean Well dim-line connector is intermittently flaky; brief (<90 s) transients are counted separately from sustained faults. The counter typically reads 0–2/day; ≥3/day surfaces a yellow alert recommending operator inspection of the dim-line crimp.

System uptime, measured as the fraction of 1-minute buckets containing a fresh `local_temperature` sample over the 80.3-day Meross-instrumented window (2026-02-18 → 2026-05-10), was **90.5 %** (104,681 of 115,695 buckets). The figure is dominated by a single 7-day data-logging interruption from 2026-04-12 to 2026-04-20 in which the cabinet itself continued operating (compressor cycling and Meross power readings were logged continuously) but the highland-tab data logger silently stopped writing measurements; root cause not fully diagnosed at the time of writing. Excluding that single outlier, uptime over the remaining 73.3 days was **99.3 %**. Watchdog recovery from USB-serial stalls is rapid (mean 22 s, std 6 s, n ≈ 12 events in the window) and is not the dominant downtime contributor. The Arduino watchdog flag (`arduino_status > 0.5` per 1-min bucket) was true 99.7 % of the time it was logged, confirming that the Arduino itself was alive across the window; the gap is in the Node-RED logging pipeline, not the embedded layer. Exact InfluxQL queries are listed in `paper/uptime_sot_2026-05-13.yaml` (Design Files).

### 7.7 Power Consumption

Total system power is logged by a Meross MSS310 in-line energy meter; an out-of-process daemon (`meross_daemon.py`) polls the meter at 2 s – 30 s – 120 s cadence across the window and publishes via MQTT into InfluxDB. Trapezoidal integration of `power_consumption` is density-independent, so the kWh figure is unaffected by the cadence changes (confirmed against mean × 24 h: 110.9 W × 24 = 2.66 kWh/d). The 80.3-day Meross-instrumented window (2026-02-18 → 2026-05-10) yields:

| Statistic | Value |
|---|---:|
| Total energy logged (trapezoidal integral) | 211.41 kWh |
| Daily consumption | **2.63 kWh/day** |
| Monthly consumption | ~80 kWh/month |
| Annual consumption | ~960 kWh/year |
| Annualised electricity cost (€0.30/kWh) | **~€288/year** |
| Mean power | 110.9 W |
| Median power | 110.8 W |
| 95th-percentile power | 203.1 W |
| Peak (single sample) | 492.9 W |

The hour-of-day profile is bimodal: night-time draw of 60–90 W (compressor cycling on top of the ~17 W baseline of Pi + Arduino + ESP + Meross + idle fans) and a daytime peak of 170–180 W (LED-dominated) with brief excursions to ~310 W when the lights peak coincides with a compressor cycle. The maximum sample (492.9 W) corresponds to a compressor start-up inrush; mean steady-state remains below 200 W.

The cabinet's expected power as a function of commanded state has been characterised explicitly so that out-of-band anomalies (such as a compressor running when commanded off) can be flagged automatically; see Section 6.6 and `terrarium-health.py` in the Design Files.

To contextualise: the 2.6 kWh/day operational draw is one to two orders of magnitude below a commercial cloud-forest-capable growth chamber of equivalent volume (Percival I-30 series: 1.5–3 kWh/h continuous; Conviron CMP6010: comparable). The comparison is not perfectly fair — commercial chambers deliver tighter environmental specifications and certified validation — but for the species-conservation and naturalistic-variation use cases targeted by this design, the energy budget is qualitatively different. Numerical figures in this section derive from the trapezoidal integral of the Meross power_consumption time-series; all kWh-dependent values in this paper and its companions are derived from a single source-of-truth block (`paper/energy_sot_2026-05-12.yaml` in the Design Files) to ensure consistency across drafts.

`[PLACEHOLDER — power-vs-time-of-day plot; available on the live cabinet dashboard at `<URL>/highland/dashboard/`]`

### 7.8 Capabilities and Limitations

**Capabilities**:

- Maintains 13.5–24.3 °C in a room at ~22 °C; sustains 75–98 % RH continuously, with ~1.25 h/day of fog-zone immersion (RH ≥ 95 %)
- Produces naturalistic, stochastic environmental variation by streaming and time-shifting real Colombian highland weather
- Computes seasonally varying photoperiod from the weather-source latitude and applies a raised-cosine LED curve centred on solar noon
- Two-regime PID switches between humidity-driven (T < 24 °C) and temperature-driven (T ≥ 24 °C) control, with the temperature regime persisting through compressor engagement as a daytime ceiling-defence cooling actuator; the fan-to-humidity loop is characterised causally (IV/2SLS, §7.2) and the heat-balance attribution is published (§7.4)
- Eleven-layer operational safety chain (door interlock, mister duration failsafe, freezer daytime gate, wet-bulb fan-off gate, manual-override timeout, USB-serial watchdog, LED-fault watchdog, power-vs-commanded cross-check, weather staleness fallback, Pi↔Arduino serial-link CRC integrity, mister water gate) audited against a three-class detector-fragility taxonomy, handles the production failure modes encountered over four years of operation
- Comprehensive data logging (33 InfluxDB measurements, 60-s cadence for continuous channels, event-driven for state changes; 3.1 million data points in the current 1-year retention window) supports experimental analysis and the published causal-inference pipelines
- Public companion dashboard, ledger, and operational blog at `<URL>` enable independent verification of the operating state at any time

**Limitations**:

- Single-sensor humidity/temperature measurement at mid-canopy; spatial gradients across the cabinet (especially the floor-to-ceiling temperature stratification noted in Section 5.2.2) are not directly characterised
- Internet-dependent weather data (degrades to a 14-day historical daily curve on stale-pipeline detection; the fallback is sufficient for indefinite continued operation but loses stochastic event content)
- Recurring USB-serial stalls require the watchdog to recover (mean 22 s downtime per stall, < 0.6 % cumulative uptime loss)
- Cloud-dependent Meross power monitoring (Meross API; replaceable with any in-line meter that exposes a local-network reading)
- Cannot provide species-specific dry-rest periods in a shared enclosure; the design optimises for moisture-dependent cohabiting species and accepts that some specimens with strong dry-rest flowering triggers will produce non-mass blooms in this regime (see companion CPN paper [18] and the no-dry-rest design rationale developed in the orchid companion [19])
- The acrylic enclosure is combustible (acceptable in indoor, supervised setting; for laboratory deployment a polycarbonate or tempered-glass alternative is recommended)
- PID tuning values are enclosure-specific; the published values apply to the geometry described in §5 and would require re-tuning for substantially different cabinet volumes or thermal-mass conditions
- Canopy PPFD and integrated daily DLI are pending direct measurement with a quantum sensor

---

## References

[1] Rull, V., & Vegas-Vilarrúbia, T. (2006). Unexpected biodiversity loss under global warming in the neotropical Guayana Highlands: a preliminary appraisal. *Global Change Biology*, 12, 1–6.

[2] Berry, P. E., & Riina, R. (2005). Insights into the diversity of the Pantepui flora and the biogeographic complexity of the Guayana Shield. *Biologiske Skrifter*, 55, 145–167.

[3] Stull, R. (2011). Wet-Bulb Temperature from Relative Humidity and Air Temperature. *Journal of Applied Meteorology and Climatology*, 50(11), 2267–2269.

[4] McDowell, K., Zhong, Y., Webster, K., Gonzalez, H. J., Trimble, A. Z., & Mora, C. (2021). Comprehensive temperature controller with internet connectivity for plant growth experiments. *HardwareX*, 10, e00238.

[5] Lau, S. K., & Subbiah, J. (2020). HumidOSH: A self-contained environmental chamber with controls for relative humidity and fan speed. *HardwareX*, 8, e00141.

[6] Sánchez, C., Dessì, P., Duffy, M., & Lens, P. N. L. (2020). OpenTCC: An open source low-cost temperature-control chamber. *HardwareX*, 7, e00099.

[7] Yuan, S., Tang, H., Fu, L. J., Tan, J. L., Govindjee, & Guo, Y. (2022). An open Internet of Things (IoT)-based framework for feedback control of photosynthetic activities. *Photosynthetica*, 60(1), 79–87.

[8] Iucci, T., Maliqi, D., Sousa Rosa, S., & Marques, M. P. C. (2026). A compact, modular and low-cost hydroponic greenhouse. *HardwareX*, e00777.

[9] Givnish, T. J., et al. (2014). Adaptive radiation, correlated and contingent evolution, and net species diversification in Bromeliaceae. *Molecular Phylogenetics and Evolution*, 71, 55–78.

[10] Hamilton, L. S., Juvik, J. O., & Scatena, F. N. (Eds.) (1995). *Tropical Montane Cloud Forests*. Ecological Studies Vol. 110, Springer-Verlag. (Definitional reference for "tropical montane cloud forest" as a biome distinct from tepuiana grassland.)

[11] Bruijnzeel, L. A., Scatena, F. N., & Hamilton, L. S. (Eds.) (2011). *Tropical Montane Cloud Forests: Science for Conservation and Management*. International Hydrology Series, Cambridge University Press.

[12] Taylor, P. (1989). *The Genus Utricularia — A Taxonomic Monograph*. Kew Bulletin Additional Series XIV. Royal Botanic Gardens, Kew. (Section *Orchidioides* key, pp. 42–59.)

[13] Shafer, D. (2003). A chest-freezer growing chamber for highland *Heliamphora*. *Carnivorous Plant Newsletter*, 32, 90–92.

[14] Node-RED Project. (2026). https://nodered.org/

[15] InfluxDB. (2026). https://www.influxdata.com/

[16] Grafana Labs. (2026). https://grafana.com/

[17] Honeywell. R134a (Genetron 134a) Refrigerant — Material Safety Data Sheet. https://www.honeywell-refrigerants.com/ (cited for the R134a ODP and GWP figures in §4.3.)

[18] **Companion paper (Carnivorous Plant Newsletter, submitted)** — Cohabitation cultivation of highland carnivores using the Weather-Mimicking Biotope. Reports horticultural results for *Heliamphora*, highland *Nepenthes*, *Utricularia* sect. *Orchidioides*, and *Brocchinia reducta*, with the present paper as the system reference.

[19] **Companion paper (Orchids, American Orchid Society, submitted)** — Cloud-forest orchid cohabitation without dry-rest periods using the Weather-Mimicking Biotope. Reports cultivation observations for *Dracula*, *Masdevallia*/*Restrepia*, rupicolous *Cattleya*, *Dendrobium* sect. *Oxyglossum*, and *Phragmipedium*, with the present paper as the system reference.

[20] **Companion paper (ICPS, in preparation)** — Open-source freeware for convergent ex-situ refugia: cohabitation of 120 cloud-forest species across four biogeographic biomes. Synthesises the engineering of the present paper and the cultivation results of [18], [19] into a conservation/community pitch.

[21] **Companion website (Zenodo DOI to be assigned at deposit)** — Live cabinet readings, photographic build documentation, the operational blog (including the 2026-05-04 Light Curve C deployment writeup and 21-day followup analysis), and the public-mirror snapshot pipeline. The website is the canonical reference for engineering details cited by the plant-enthusiast companion papers [18, 19], permitting their main bodies to remain focused on horticultural outcomes.

`[PLACEHOLDER — additional product/datasheet citations: full Vitrifrigo ND50 / PT14 datasheet URL once verified; Tapo P100 product page; Meross MSS310 datasheet; MistKing pump datasheet; Percival or Conviron datasheet for the growth-chamber comparison. **Lit-check candidates for Consensus Pro**: (a) verify the novelty claim in §1 that "no published open-source system ingests real-time meteorological data from a geographically distinct reference site and applies a time-zone-aware phase shift to drive continuously varying environmental setpoints"; (b) prior art on raised-cosine LED schedules in growth-chamber literature; (c) IV/2SLS or instrumental-variables methods in environmental-control or growth-chamber papers (rarely cited in this venue class — confirming this would strengthen the methods-novelty claim).]`

---

## Acknowledgments

`[PLACEHOLDER]`
