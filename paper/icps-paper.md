# Weather-Mimicking Terrarium for Convergent Cloud Forest Species: Open-Source Climate Simulation, Compressor Cooling, and Four Years of Co-Cultivating Highland Carnivorous Plants, Orchids, and Epiphytes

**Authors**: Gabriele Zoppoli — Department of Internal Medicine and Medical Specialties (DiMI), University of Genoa, Genoa, Italy; IRCCS Ospedale Policlinico San Martino, Genoa, Italy

**Corresponding author**: gabriele.zoppoli@unige.it

---

## Abstract

We describe a weather-mimicking terrarium system that cultivates 75 living accessions across 31 plant genera from convergent cloud-forest and tepui environments on three continents — the Guayanan tepuis of Venezuela, the Colombian and Ecuadorian Andes, the Brazilian Atlantic Forest, the highlands of Papua New Guinea, and the upper montane forests of Sumatra, Sulawesi, and the Philippines — within a single ~1 m³ (1.5 × 0.6 × 1.1 m) enclosure in Genoa, Italy. The system ingests real-time meteorological data from four Colombian highland cities (Chinchina, Medellín, Bogotá, Sonsón; 1,300–2,600 m) and applies a 15-hour backward lookup against the locally archived time-series; combined with the 7-hour Italy-to-Colombia time-zone offset, this phase-aligns the cabinet's daily cycle with Italian local time while preserving the stochastic weather content from the Colombian source (without the shift, the time-zone offset alone would invert the day/night cycle and produce biologically wrong cool-during-Italian-afternoon conditions). A dynamic photoperiod derived from the Colombian reference latitude (~5° N) provides seasonally varying day length. Under these conditions, nine *Heliamphora* accessions (tepui summit specialists), nine highland *Nepenthes* (Sumatra, Sulawesi, Philippines; no Bornean accession in the current cabinet), one *Utricularia quelchii* (section *Orchidioides*, Ilu Tepui provenance, first flowering April–May 2026), one *Brocchinia reducta* (Guiana Shield bromeliad), six *Dracula* and five *Masdevallia* orchids (Andes), three *Dendrobium* of PNG section *Oxyglossum* (*D. cuthbertsonii*, *D. cyanocentrum*, *D. hellwigianum*) and one Philippine *D. victoriae-reginae* (section *Calcarifera* per POWO/IOSPE — not *Oxyglossum* as sometimes claimed in the orchid literature), and the former-*Sophronitis* rupicolous group from the Brazilian Atlantic Forest (*S. coccinea*, *S. brevipedunculata*, *S. wittigiana* rosea, *S. pygmaea*) are maintained alongside ferns, mosses, and other epiphytes — all under identical conditions. A marine compressor unit (Vitrifrigo ND50, R134a refrigerant) routinely drives the terrarium to 13.5 °C in a room at 22 °C, accessing a thermal regime inaccessible to evaporative cooling. A three-regime fan control strategy adapts the PID controller's error signal based on temperature: humidity-driven control under normal conditions, temperature-driven evaporative cooling in a 24–25 °C transition band, and humidity-driven control with active mechanical refrigeration above 25 °C. A heat-balance regression over the 80.3-day Meross-instrumented window (n = 17,773 5-min observations, HC3 robust SEs; full results in the companion paper) attributes essentially all of the active cooling work to the compressor (−1.01 °C/hr when active), and an instrumental-variables (2SLS) analysis quantifies the fan-to-humidity coupling at −0.34 % RH per +10 PWM units (95 % CI: −0.68 to −0.005; p = 0.047; n = 1,353), establishing fan PWM as the humidity actuator. A multi-layer safety chain (door-open interlock, freezer daytime gate, manual-override timeout, power cross-check, LED-fault watchdog) evolved over four years in response to nine specific failure modes; the full deployment chronology is tabulated in `paper/safety_chain_deployment_dates.yaml`. The control system, built entirely on open-source software (Node-RED, InfluxDB, Grafana) running on a Raspberry Pi with an Arduino Mega for hardware I/O, has operated continuously for four years at a measured power draw of **2.63 kWh/day (~€288/year at €0.30/kWh)**. All source code, firmware, dashboards, and analysis scripts are available at https://github.com/GabrieleZoppoli/terrarium-control-system; a public companion website mirrors live conditions, build photographs, and operational logs.

**Keywords**: cloud forest terrarium, convergent evolution, weather simulation, instrumental variables, causal inference, dynamic photoperiod, *Heliamphora*, *Nepenthes*, *Dracula*, *Utricularia*, *Dendrobium*, three-regime PID control, marine compressor cooling, open-source horticulture

---

## 1. Introduction

Tropical highland environments — from the Guayanan tepui table-top mountains in Venezuela to the Andes, the highlands of Papua New Guinea, the Brazilian Atlantic Forest highlands, and the upper montane forests of Sumatra, Sulawesi, and the Philippines — harbour extraordinary plant diversity adapted to narrow environmental envelopes: cool temperatures (10–22 °C), persistent high humidity (80–100 % RH), frequent fog or cloud immersion, and moderate light filtered through cloud (Rull & Vegas-Vilarrubia 2006). At higher elevations, particularly on tepui summits above 2,500 m, nighttime temperatures can drop below 5 °C and occasionally approach freezing. Cultivating these species outside their native range — especially in Mediterranean climates with hot, dry summers — presents formidable challenges for both botanical institutions and private growers. We use the term "convergent cloud forest" advisedly: in the strict Hamilton–Juvik–Scatena (1995) and Bruijnzeel et al. (2011) sense, the tepui summit grasslands and shrublands are not tropical montane cloud forest (TMCF) — they are largely treeless tepuiana with a quite different vegetation physiognomy — but they share the *climatic* envelope that defines TMCF. It is this climatic convergence, not vegetation-type identity, that permits the co-cultivation described in this paper.

The central difficulty is nighttime cooling. While maintaining high humidity in a sealed terrarium is straightforward, achieving the 4--8 deg C nocturnal temperature drops characteristic of tropical highlands — in a room at 22 deg C — requires active refrigeration. The hobby has developed several approaches to this problem, each with characteristic limitations.

Evaporative cooling — using misting and ventilation fans to cool by evaporation — is the most accessible method. However, it has a hard thermodynamic limit: evaporation can only cool the air down to the wet-bulb temperature, a value determined by the room's temperature and humidity. In a typical room at 22 deg C and 58% relative humidity, this floor is approximately 16.6 deg C. Below that point, fan-driven evaporative cooling has no further capacity to reduce air temperature, and fans operate as humidity injectors rather than coolers (the fan-to-humidity coupling is quantified causally in §4.3; the heat-balance attribution for this system is in the companion paper).

Thermoelectric (Peltier) modules are attractive for their simplicity and silent operation, but their coefficient of performance (COP) is approximately 0.2 — roughly one-tenth that of a vapor-compression system — meaning they draw 5 W of electricity for every 1 W of heat removed. In practice, a single 36 W module achieves only 2--4 deg C of cooling in a 20-liter volume (cexx.org 2011), and scaling to larger enclosures requires arrays of modules with correspondingly large heat sinks and power supplies.

The chest freezer conversion, first described by Shafer (2003), provides effective compressor cooling by using the freezer itself as the growing enclosure. This method can reach temperatures below 5 deg C and has become a standard approach for growers of demanding *Heliamphora* and *Nepenthes*. Its limitations are primarily spatial: growing space is constrained by the freezer's dimensions, the compressor is not designed for the thermal load of an open-topped enclosure, and integration with humidity control requires modification.

The approach described here uses marine refrigeration hardware — a Vitrifrigo ND50 compressor unit with a Danfoss variable-speed compressor and a stainless-steel evaporator plate mounted inside the terrarium. This class of equipment, designed for boat refrigeration where compact size, low power draw (31 W), and reliable performance in confined humid spaces are essential, has not previously been applied to terrarium cooling. The system routinely drives the terrarium to 13.5 deg C — approximately 3 deg C below the evaporative cooling floor and nearly 9 deg C below room ambient.

Beyond the cooling challenge, traditional terrarium approaches rely on fixed environmental setpoints (e.g., 18 deg C day / 14 deg C night, 90% RH constant), which fail to capture the dynamic variability that characterizes cloud forest environments. Real cloud forests experience weather — sudden temperature drops during rainstorms, diurnal fog cycles, seasonal shifts in cloud cover, and all the unpredictable environmental variation that our plants evolved with. Static control not only oversimplifies the environment but may fail to provide the thermal and humidity cues that many cloud forest species require for phenological processes including flowering and seed set.

This paper describes an open-source control system that addresses these limitations through five key innovations:

1. **Weather-mimicking from real Colombian data**: The system ingests real-time meteorological data from four Colombian highland cities (Chinchina, Medellin, Bogota, Sonson) at elevations of 1,300--2,600 m, applying a 15-hour time shift to produce naturalistic, continuously varying setpoints. A dynamic photoperiod is derived from the Colombian reference latitude (~5 deg N).

2. **Convergent cloud forest concept**: Cloud forests worldwide converge on remarkably similar climatic envelopes despite their geographic isolation. A single terrarium tuned to the common envelope can support species from multiple continents simultaneously — a principle validated over four years of co-cultivation with 75 living accessions across 31 plant genera.

3. **Marine compressor cooling**: The Vitrifrigo ND50 provides sufficient cooling capacity to drive terrarium temperatures well below the room's wet-bulb temperature, accessing a thermal regime inaccessible to evaporative methods.

4. **Causal characterisation of fan-driven humidity control**: A randomised A/B fan-schedule experiment (n = 1,353 nighttime 5-min observations) enables an instrumental-variables (2SLS) estimate of the fan-PWM-to-humidity coefficient that is decorrelated from the PID's reaction to humidity disturbances; the companion 80.3-day heat-balance regression (n = 17,773; HC3) attributes essentially all of the active cooling work to the marine compressor and characterises fan PWM as the humidity actuator.

5. **Complete open-source stack**: Every component — Node-RED, InfluxDB, Grafana — runs on a single Raspberry Pi, with all source code, firmware, and dashboards freely available.

The system has maintained 75 living accessions across 31 plant genera from cloud forest genera across three continents in a ~1 m³ (1.5 × 0.6 × 1.1 m) terrarium in Genoa, Italy for over four years, demonstrating long-term reliability and horticultural effectiveness.

---

## 2. Materials and Methods

### 2.1 Terrarium Construction

The terrarium is a custom-built acrylic (PMMA) enclosure measuring ~1 m³ (1.5 × 0.6 × 1.1 m) (external dimensions), assembled by solvent welding laser-cut panels with dichloromethane and sealing with crystalline silicone. The enclosure weighs approximately 100 kg empty. External insulation — 1 cm extruded polystyrene laminated with diamond Mylar reflective sheeting — reduces heat gain and improves cooling efficiency. Access is via two sliding front panels on alloy guides. The enclosure is placed in an area of the apartment that does not receive direct sunlight, reducing cooling load.

The supporting scaffold is a semi-industrial aluminium alloy unit (2.20 x 3.20 x 0.50 m, approximately 300 kg). Aluminium was chosen over wood after an earlier wooden scaffold suffered waterproof coating degradation and swelling after four years in the high-humidity environment.

The 110 cm height creates three distinct climatic zones via a mid-height perforated acrylic shelf:

1. **Upper zone** (above shelf, high light): *Heliamphora* species, *Brocchinia reducta*, rupicolous *Cattleya*, *Dendrobium* sect. *Oxyglossum*, and high-light miniatures
2. **Middle zone** (shelf level, intermediate light): Epiphytic *Utricularia* sect. *Orchidioides* (kokedama-style), highland *Nepenthes* hanging baskets, *Masdevallia*, *Restrepia*
3. **Lower zone** (below shelf, low light, coolest): *Dracula* orchids, *Phragmipedium*, highland ferns, shade-adapted *Nepenthes*

### 2.2 Hardware Components

**Lighting**: Four ChilLED Logic Puck V3 modules (100 W each, 244 Samsung LM301B LEDs per puck) on 140 mm aluminium pin heatsinks with 12 V cooling fans. The Mean Well HLG-480H-48A LED driver's internal potentiometer limits maximum output to approximately 60% of rated power (a hardware fail-safe), and an Arduino PWM signal provides a second dimming stage. The effective operating range is 24--36% of the LEDs' full rated capacity. This two-stage approach ensures that even a software error cannot drive the LEDs to full power, protecting shade-adapted species in the lower zone.

**Cooling**: Vitrifrigo ND50 compressor unit with Danfoss BD50F variable-speed compressor (31 W draw) mounted above the terrarium, with refrigerant lines passing through the enclosure top to a PT14 stainless-steel evaporator plate (1,220 × 280 mm) installed horizontally inside the enclosure. Three Noctua NF-F12 iPPC-2000 IP67 fans (12 V, 120 mm) mounted on a plexiglass baffle angled approximately 30 degrees below the evaporator direct cold air downward through a slit, exploiting the natural downward flow of dense cold air. Condenser fans (Noctua NF-A12x25 G2, push-pull on the external radiator above) are powered directly, not Arduino-controlled.

Marine refrigeration is a distinct hardware category from the general "compressor cooling" approaches summarised in the introduction (chest-freezer conversions, aquarium chillers, modified portable air conditioners). The Vitrifrigo ND50 is designed and shipped as a complete split-system unit — compressor, condenser, refrigerant lines, evaporator plate — sized for boat refrigerators and small marine cold-storage cabinets. Three practical consequences are worth highlighting for hobbyist and small-institution replicators:

1. **Easy to install.** The condenser end of the unit is mounted externally; the evaporator plate (a flat stainless-steel panel) is bolted inside the enclosure; the pre-formed refrigerant line set runs between the two. There is no mechanical work on the cold loop, no field plumbing of compressor + condenser + expansion device, and no system charging — the assembly is a sequence of bolts and gaskets.
2. **Customizable to enclosure size.** Vitrifrigo and equivalent marine-refrigeration vendors offer multiple compressor / evaporator combinations spanning roughly 30–200 L cold-storage capacity, and the evaporator plates come in several footprint sizes. A grower sizing a terrarium between ~0.3 m³ and ~3 m³ can pick a matched unit without custom engineering; the ND50 used here is at the upper end of that range and was sized for the present 1 m³ cabinet with comfortable headroom.
3. **Pre-charged refrigerant loop.** The unit ships with a factory-sealed, pre-charged R134a loop. Installation does not require an F-gas certification in EU/UK jurisdictions because no work is performed on the refrigerant circuit (the legal requirement applies to filling, topping up, or any operation that opens the loop). This removes a significant skills barrier that has historically limited DIY compressor-based terrarium cooling to chest-freezer conversions (where the manufacturer has done the charge work and the unit is sold as a complete appliance) or to growers willing to pay for a refrigeration engineer's time. The trade-off is that any repair on the cold loop *does* require certification, so a faulty unit is replaced or serviced by a marine-refrigeration shop rather than user-repaired.

The split-system architecture — external compressor with refrigerant piping to an internal evaporator — is the same configuration used in marine refrigerators and is mechanical refrigeration, not evaporative cooling.

**Humidification**: MistKing diaphragm pump (located on a shelf below the terrarium) supplies water through tubing to 20 mist nozzle points distributed across the enclosure ceiling, controlled via TP-Link Tapo P100 smart plug (192.168.1.199). A 40-liter reservoir on the same shelf feeds the pump; a second 40-liter tank collects condensate from the evaporator.

**Air circulation**: Two groups of PWM-controlled fans — two Noctua NF-F12 iPPC-2000 for internal circulation (pin 12) and two Noctua 60 mm fans for outlet (pin 45) and impeller (pin 46) ventilation. All fans are driven at 25 kHz via IRF520N MOSFET modules switching the 12 V power rails.

**Sensing**: Sensirion SHT35 temperature/humidity sensor (+/-0.1 deg C, +/-1.5% RH) connected to an ESP8266 microcontroller publishing to MQTT at ~1 Hz. An HC-SR04P ultrasonic distance sensor on the same ESP monitors water level in the mister reservoir.

**Power monitoring**: A Meross MSS310 smart plug on the master power line reports instantaneous power consumption. A persistent Python daemon maintains a single authenticated session to the Meross cloud API and publishes readings to the local MQTT broker every 2 seconds, avoiding the overhead of repeated authentication. The daemon runs as a systemd service and automatically reconnects on failure.

**Control**: Raspberry Pi 4 running Node-RED v3.1.3 (control logic), InfluxDB 1.8.10 (33 time-series measurements at 60 s intervals for continuous channels plus event-driven actuator-change logging), Grafana 10.2.3 (4 monitoring dashboards), and Mosquitto MQTT broker. An Arduino Mega 2560 provides hardware I/O via a custom text-based serial protocol at 115,200 baud.

### 2.3 Climate Simulation

The system queries the OpenWeatherMap API for current weather conditions at four Colombian highland cities:

| City | Elevation | Latitude | Role |
|------|-----------|----------|------|
| Chinchina | ~1,300 m | 4.98 deg N | Warm reference |
| Medellin | ~1,500 m | 6.25 deg N | Mid-elevation reference |
| Sonson | ~2,475 m | 5.71 deg N | Cool reference |
| Bogota | ~2,640 m | 4.71 deg N | Cool/high reference |

Temperature and humidity values are heavily averaged — a 15-minute rolling mean across all four cities — and clamped to the operating range 12–24 °C and 75–95 % RH (the humidity floor was raised from 70 % to 75 % on 2026-04-30 to better match Pantepui *Heliamphora* and *Utricularia* preferences). The 15-hour backward look against the locally archived Colombian time-series, combined with the 7-hour Italy-to-Colombia time-zone offset, phase-aligns the cabinet's daily cycle with Italian local time: at Italian noon the controller retrieves Colombian data from the previous afternoon (warm, slightly drier), and at Italian midnight it retrieves Colombian data from the same-day pre-dawn (cool, near-saturated). Without the shift, the time-zone offset alone would invert the natural day/night cycle (cool during Italian afternoon, warm during Italian night) — biologically wrong. The shift is therefore a deliberate phase correction, not a delay; the stochastic weather content is preserved. Cross-validation over a representative 7-day window (n = 154 hourly pairs) gave Pearson r = 0.73 between cabinet target temperature and Chinchinà temperature 15 h prior; residual variance is dominated by the 24 °C target ceiling clamp.

The choice of Colombian highland cities was driven by the unavailability of real-time tepui weather station data. These cities were selected because their elevation range and near-equatorial latitude produce temperature and humidity profiles comparable to those reported for tepui summits, upper montane forests, and other tropical highland habitats. Crucially, the cities lie at approximately 5 deg N — the same hemisphere as the Venezuelan tepuis — meaning that seasonal photoperiod variation at the weather source matches the natural photoperiod of the target taxa.

The stochastic character of real weather data is a key advantage over fixed schedules. Rain events in Colombia produce sudden temperature drops and humidity spikes that translate into corresponding terrarium setpoint changes, simulating fog immersion events. These events are not programmed; they emerge from real weather and vary from day to day. While they differ mechanistically from orographic fog immersion, they produce temperature and humidity excursions of similar magnitude and duration to those recorded during cloud immersion events in tropical montane environments (Jarvis & Mulligan 2011).

If the internet connection is lost, the system falls back to a historical daily curve built from the previous 14 days of recorded weather data — a smoothed 288-slot (5-minute resolution) daily profile reconstructed every 6 hours from InfluxDB — preserving a realistic diurnal pattern rather than reverting to flat defaults.

### 2.4 Light Regime

A dynamic photoperiod is computed daily from the latitude of Chinchina (4.98 deg N). At this near-equatorial latitude, the natural annual variation is only ~34 minutes between solstices (11 h 43 min to 12 h 17 min). The system clamps the computed day length to a 10--14 hour range — intentionally wider than the natural variation to benefit companion species from higher latitudes (e.g., Brazilian *Cattleya* at ~22 deg S) and to provide a stronger potential flowering stimulus. The lit period is centered on 13:15 local time.

Two dimmer channels provide intensity variation simulating natural light transitions: a 30-minute dawn/dusk ramp (slider 0 to 40, 40 steps at 45 s) and a 30-minute midday brightness boost (slider 40 to 60, 20 steps at 90 s) that begins proportionally through the day.

The inverse square law from overhead LED sources creates a continuous light gradient within the terrarium. Rather than fighting this gradient, the system exploits it: high-light species (*Heliamphora*, which grow fully exposed on tepui summits) occupy the upper zone directly beneath the LEDs, while shade-adapted species (*Dracula*, which grow in deep forest understory) occupy the lower zone. A single lighting system thus approximates the distinct light environments these species require.

### 2.5 Substrate and Mounting

**Heliamphora and Brocchinia reducta**: Upper zone, in akadama (Japanese fired clay) mixed with long-fiber sphagnum, topped with living *Sphagnum* moss. Akadama provides drainage; living sphagnum maintains surface moisture and creates acidic, low-nutrient conditions approximating tepui summit peat bogs.

**Utricularia sect. Orchidioides** (current cabinet representative: *U. quelchii* Ilu Tepui only — *U. alpina* lives on a separate non-cabinet shelf in the broader collection): Kokedama-style — wrapped in a ball of living *Sphagnum*, hung from the back wall at mid-height. The kokedama form provides the aerial, moisture-saturated root environment these species inhabit on tepui cliff faces.

**Highland Nepenthes**: Kanuma (Japanese volcanic pumice) mixed with long-fiber sphagnum, placed on the terrarium floor without saucers. The persistently high ambient humidity (82--95% RH) eliminates the need for supplementary moisture trays.

**Orchids (Dracula, Masdevallia, Restrepia, Dendrobium, Cattleya)**: Mounted on cork bark with sphagnum moss pads. *Dracula* mounts are positioned to allow inflorescences to hang freely below. *Dendrobium* sect. *Oxyglossum* on tree fern plaques in the upper zone.

**Phragmipedium**: Lower zone, in sphagnum-based media.

### 2.6 Fan Control and PID Algorithm

The gain-scheduled PID controller operates in three regimes based on temperature:

- **Normal** (T < 24 deg C): Fans driven by humidity error (target humidity minus actual humidity). This is the default operating mode for most of the day-night cycle.
- **Warm** (24--25 deg C, compressor off): Controller switches to temperature-driven mode, using fans for evaporative cooling before the energy-intensive compressor activates. Temperature error is scaled by a factor of 5 to match the PID's humidity-tuned gain structure.
- **Hot** (>= 25 deg C, compressor on): Mechanical refrigeration engages. Controller reverts to humidity-driven fan control, with the compressor providing the primary temperature reduction.

PID parameters: Kp=50, Ki=0.5, Kd=10, with gain scheduling that reduces effective proportional gain to 7.5 within +/-1.5% of the humidity setpoint to eliminate near-setpoint oscillation. A derivative filter (alpha=0.12) and integral wind-up decay (5%/s when error < 2%) provide stability. Fan speed output is clamped between BASE_SPEED=50 and MAX_SPEED=230 PWM, with a rate limit of 20 PWM per cycle to protect the serial communication link.

Fans are disabled between 00:00 and 04:00 (night period). A morning humidity blast from 04:00--07:00 runs fans at maximum speed (PWM 255) to drive off overnight condensation.

### 2.7 Wet-Bulb Fan-Off Gate (deployed firmware, deprecated rationale)

The wet-bulb temperature is computed in real time from room sensor data using the Stull (2011) approximation. When the terrarium temperature drops below the room's wet-bulb temperature — typically around 20:00–21:00 each evening — the deployed firmware blocks the outlet and impeller fans, relying solely on evaporator fans and the compressor for overnight cooling; the gate reopens at 04:00.

The original thermodynamic rationale for the gate — that sub-WBT fan operation imports room sensible heat at a rate large enough to be worth blocking — was derived from a 27-day preliminary heat-balance regression. A subsequent 80.3-day rerun on n = 17,773 5-minute observations (companion paper, §7.4) does not support that quantity once fan PWM is modelled at its native resolution: the per-PWM fan effect on cabinet-temperature derivative is statistically indistinguishable from zero. The firmware path is retained as a deployed feature, but the paper does not advance the gate as a load-bearing finding.

---

## 3. Species Cultivated

The terrarium supports 75 living accessions across 31 plant genera from convergent cloud-forest and tepuiana environments across three continents (Neotropical highlands of South America, Southeast Asian highlands, and Papua New Guinea / Oceania). The successful co-cultivation of these species in a single enclosure with shared environmental conditions demonstrates the convergent nature of cloud forest climates worldwide.

### 3.1 Venezuelan Tepui: *Heliamphora*

*Heliamphora* (sun pitchers, Sarraceniaceae) are the flagship tepui species, grown in the upper zone. Multiple species and hybrids produce mature pitchers, divide regularly, and produce flower scapes under the weather-variable conditions. The saturated substrates and persistent VPD below 0.4 kPa are critical for maintaining pitcher fluid and nectar spoon hydration.

Nine living *Heliamphora* species and hybrids are currently cultivated, all sourced from Andreas Wistuba (Mannheim, Germany). Cabinet residence times within the cohort span ten years (the March 2016 cohort) to two years (the 2023 cohort, including *H. macdonaldae* and *H. minor* var. *pilosa* Clone 3); the longest-tenured *Heliamphora* therefore antedate the four-year continuous run of the present cabinet and were transferred in from the previous-generation enclosure.

| Taxon | Provenance | Acquired |
|-------|-----------|----------|
| *H. pulchella* | Akopan-tepui | March 2016 |
| *H. purpurascens* × *ionasi* 'Red Giant' | hybrid (AW selection) | March 2016 |
| *H. minor* Clone 4 | — | March 2016 |
| *H. pulchella* | Amuri-tepui (separate provenance from the Akopan plant) | May 2016 |
| *H. minor* 'Burgundy Black' | clonal selection | October 2016 |
| *H.* 'Godzilla' | AW-H_Godz | July 2021 |
| *H. ionasi* 'Elegance' | clonal selection | January 2023 |
| *H. macdonaldae* (Cerro Duida) ISC | — | January 2023 |
| *H. minor* var. *pilosa* (Auyán) Clone 3 | — | March 2023 |

All nine accessions are alive and growing in the cabinet (filtered from `collection.csv` on `location=highland AND status=alive`, 2026-05-12). No *Heliamphora* losses have occurred during cabinet residency, making the genus the most reliable in the collection on a per-accession basis.

[USER INPUT NEEDED — Cultivation observations:
- Pitcher production rates and division frequency
- Flowering events and seed set
- Coloration changes (anthocyanin responses to light/temperature)
- Photos: mature plants in situ, pitcher detail showing nectar spoons, flower scapes]

### 3.2 Other Carnivorous Taxa

Several additional carnivorous genera are cultivated as companion plants in the terrarium. While not all originate from cloud forests, they tolerate the cool, humid conditions and occupy niches within the terrarium microclimate.

*Genlisea* (corkscrew plants) have been difficult: only *G. africana* survives from four species trialled. *G. aurea*, *G. flexuosa*, and *G. violacea* were all lost, suggesting the terrarium conditions may be too cool for these largely tropical lowland species.

*Pinguicula* (butterworts) are represented by 13 surviving plants from 22 acquired, a 59% survival rate. Mexican species and hybrids (*P.* 'Apasionada', *P. agnata* x *gypsicola*, *P. reticulata*, *P. ehlersiae*, *P. esseriana*, and others) perform well. The tropical species *P. primuliflora* and the large-growing *P. gigantea* were lost repeatedly (3 plants each), likely due to the cool nighttime temperatures.

*Drosera* (sundews) include 10 surviving species from 19 acquired. *D. capensis* forms (typical, 'Red', 'Broad Leaf', 'Hairy Form', 'Bainskloof') are the most reliable. Notable survivors also include three tuberous Australian species from Allen Lowrie (*D. tubaestylis*, *D. macrantha* subsp. *eremaea*, *D. zonaria*).

*Brocchinia reducta*, the carnivorous bromeliad of the Guiana Shield, is cultivated in the upper zone alongside *Heliamphora* in the same akadama/sphagnum substrate topped with living *Sphagnum* (collection.csv id=413, alive, location=highland). Per POWO its native range spans Venezuela (Bolívar) to Guyana and Brazil (Roraima) within the wet tropical biome — broader than the "tepui-summit endemic" sometimes attributed to it — so it sits comfortably alongside the *Heliamphora* under shared upper-zone irradiance and the temperature/humidity regime described in §4.1.

[USER INPUT NEEDED — additional cultivation observations: which *Drosera* and *Pinguicula* listed above are physically in the highland cabinet vs. on a windowsill / non-cabinet shelf in the broader collection (the lists above currently aggregate the highland-tab subset of `location=highland AND status=alive` filtered from `collection.csv`, 2026-05-12). Photos for each genus.]

### 3.3 Tepui and Cloud Forest Epiphytes: *Utricularia* sect. *Orchidioides*

Neotropical epiphytic *Utricularia* of section *Orchidioides* — native to tepui cliff faces (the red-flowered species *U. quelchii* and *U. campbelliana*) and Andean / Central-American cloud-forest canopies (*U. alpina*, *U. jamesoniana*) — are grown kokedama-style: each plant wrapped in a ball of living *Sphagnum* moss, hung from the back wall at mid-height under direct misting. The cabinet currently maintains a single accession of the section:

| Taxon | Source | Status | Provenance |
|-------|--------|--------|------------|
| *U. quelchii* | Klein Carnivors (early 2023) | Alive, first flowering April–May 2026 | Ilu Tepui |

Earlier *U. alpina* and *U. campbelliana* attempts have not survived in the cabinet (separate from a *U. alpina* still maintained on a non-cabinet shelf in the broader collection). The *U. quelchii* result is the substantive cultivation outcome reportable for this section. After three years of pure vegetative growth — steady leaf addition, no inflorescences — the plant produced its first scape on 20 April 2026, with two buds emerging from the driest portion of the kokedama (the ~2 cm of moss against the cabinet wall). The larger bud opened on 7 May 2026 (Day 17), displaying the full section *Orchidioides* gestalt of a hooded magenta galea, yellow-cream throat with two red callus blotches, and broad pink lower lip; the second bud opened on 11 May 2026 (Day 21). Coloration was uniform across both flowers — Ilu Tepui pink, less deep-red than the Roraima phenotype documented by Taylor (1989), as expected for a clone of stated Ilu provenance. Substrate was live *Sphagnum* only, foliar feed Akerne Orchid Mix at half a teaspoon per three litres applied twice monthly, no special treatment in the months preceding the bloom.

The flowering record is significant for two reasons. First, *U. quelchii* under cultivation is uncommon and *U. quelchii* under cultivation that flowers is rarer still; this is the first such record for this terrarium and adds to a small documented set internationally. Second, the inflorescence emergence from the *driest* portion of the kokedama is suggestive — continuous saturation may not be the floral cue, and seasonal water availability gradients within the mounting substrate may matter more than mean RH. The hypothesis is testable by creating intentional moisture-gradient kokedama mounts for the next acquisition cohort.

`[PLACEHOLDER — photos: the plant before flowering, the 20-April first-bud, the Day-17 open flower, the Day-21 two-flowers-open frame. The companion blog post `content/blog/first-bloom-utricularia-quelchii/` carries the full image set.]`

### 3.4 Colombian and Ecuadorian Andes: *Dracula* and *Masdevallia*

*Dracula* orchids (Pleurothallidinae) are the primary Andean representatives, mounted on cork bark in the lower zone where temperatures are coolest and light levels lowest — conditions approximating the deep shade of Andean cloud forest understory at 1,800--2,500 m. Six accessions are currently in the cabinet (collection.csv `location=highland AND status=alive`, 2026-05-12):

| Taxon | Source | Notes |
|-------|--------|-------|
| *D. lotax* | Großräschener Orchideen | Mounted; March 2016 — longest-tenured *Dracula* |
| *D. vlad-tepes* | Großräschener Orchideen | February 2016 |
| *D. simia* (selected) | Ecuagenera Europe | November 2022 |
| *D. pholeodytes* | Ecuagenera Europe | March 2023 |
| *D.* Raven 'Jet' | Ecuagenera | Hybrid |
| *D.* 'Fake' *hirsuta* 'Yellow' | Ecuagenera Europe | Horticultural-label ID uncertain |

*Masdevallia* includes 5 surviving species from 7 acquired:

| Taxon | Source | Status |
|-------|--------|--------|
| *M. decumana* | Grossraschener Orchideen | Alive |
| *M. xanthina* (red form) | Grossraschener Orchideen | Alive |
| *M. lucernula* | Grossraschener Orchideen | Alive |
| *M.* Devil's Heart | Ecuagenera Europe | Alive (hybrid) |
| *M. caudata* 'Gigi' | Ecuagenera | Alive |
| *M. glandulosa* | Grossraschener Orchideen | Lost |
| *M. coccinea* 'Anchota' | Ecuagenera Europe | Lost |

The losses of *M. glandulosa* (a warm-growing species despite its cloud forest origin) and *M. coccinea* 'Anchota' represent a 29% attrition rate, substantially higher than *Dracula* (0%). The surviving *Masdevallia* produce sequential blooms from the same inflorescences.

*Restrepia* — the hinged-labellum Andean Pleurothallidinae genus — is represented in the cabinet by three living accessions, all acquired in November 2022 from Ecuagenera: *R. vasquezii*, *R. sanguinea*, and *R. trichoglossa* var. *xanthina*. All three are mounted on cork bark in the lower zone alongside the *Dracula*.

[USER INPUT NEEDED — Cultivation observations: flowering frequency and seasonal patterns for *Dracula* and *Restrepia*; photos showing *Dracula* labellum detail, *Masdevallia* sequential blooms, the hinged-labellum *Restrepia* flowers.]

### 3.5 Miniature Pleurothallidinae and Neotropical Orchids

Beyond *Dracula* and *Masdevallia*, the terrarium houses a diverse assemblage of miniature Pleurothallidinae and allied genera, all mounted on cork bark or tree fern:

| Taxon | Source | Status |
|-------|--------|--------|
| *Platystele baqueroi* | Ecuagenera Europe | Alive |
| *Pleurothallis leptotifolia* | Orchideria di Morosolo | Alive |
| *Lepanthopsis astrophora* | Varesina Orchidee | Alive |
| *Comparetia falcata* | Orchids & more | Alive |
| *Macroclinium manabinum* | Orchids & more | Alive |
| *Phymatidium tillandsioides* | Orchideria di Morosolo | Alive |
| *Ornithocephalus estradae* | Varesina Orchidee | Lost |
| *Oerstedella centradenia* | Orchids & more | Alive |
| *Nageliella purpurea* | Orchids & more | Alive |
| *Oncidium cheirophorum* | Varesina Orchidee | Alive |
| *Tolumnia hawkesiana* | Orchideria di Morosolo | Alive |

These miniature orchids collectively occupy small niches throughout the terrarium — mounted on cork bark scraps, wedged into branch forks, or established on the moss carpet. Their survival rate (10 of 11, 91%) reflects their compatibility with the persistent high-humidity regime.

A single *Phragmipedium kovachii* (CITES Appendix I, acquired November 2022 from Ecuagenera under the standard licensed-dealer CITES paperwork for artificially-propagated specimens) is grown in moss in the middle zone. The species was the subject of significant controversy following its 2002 description, and licensed-vendor sourcing is essential; the cabinet's specimen has been alive since acquisition and remains in vegetative growth.

[USER INPUT NEEDED — Cultivation observations: flowering observations for the miniature Pleurothallidinae and the *P. kovachii*; representative photos of the cork-mount cluster.]

### 3.6 Papua New Guinea Highlands: *Dendrobium* sect. *Oxyglossum*

*Dendrobium* section *Oxyglossum*, the jewel-coloured Papua New Guinea highlands miniatures, is represented in the cabinet by three living accessions: *D. cuthbertsonii* 'Yellow', *D. cyanocentrum* 'Blau', and *D. hellwigianum*. These species — native to the PNG highlands at 1,500–3,000 m — are mounted on tree-fern plaques in the upper zone in live *Sphagnum*, and produce small, intensely coloured flowers (red, orange, blue, and white) that are uncharacteristic of the more familiar large-flowered *Dendrobium*. Their success in the cabinet alongside Andean and tepui plants is one of the demonstrations of climatic convergence in this work: PNG highland *Dendrobium* evolved in complete geographic isolation from Andean *Dracula* and Pantepui *Heliamphora*, yet thrive under the cabinet's shared conditions because their respective tropical highland environments share a similar climatic envelope.

A fourth Australasian-region *Dendrobium* in the cabinet, *D. victoriae-reginae*, requires a more careful note. Despite the species's colloquial reputation as a "blue dendrobium" associated with New Guinea, its native range per POWO is the Philippines (mossy montane forests at 1,300–2,700 m), and IOSPE places it in section *Calcarifera* — not *Oxyglossum*. It is therefore a Philippine highland representative in the cabinet rather than a PNG one; its cultural requirements (cool, humid, moderately bright) are essentially identical to the Oxyglossum group, which is why it grows successfully alongside them. We retain it here as a single subsection paragraph rather than as part of the *Oxyglossum* listing to keep the taxonomy honest. A fifth cabinet *Dendrobium*, *D. trantuanii*, is a Vietnamese highland species in yet another section; it is included here for completeness in §3.9.

Nine miniature and highland *Dendrobium* are cultivated:

| Taxon | Source | Status | Notes |
|-------|--------|--------|-------|
| *D. victoriae-reginae* | Orchis Mundi | Alive | **Sect. *Calcarifera* (POWO/IOSPE), Philippine** — not *Oxyglossum*. Blue-purple flowers |
| *D. cuthbertsonii* 'Yellow' | Claessen Orchids | Alive | Sect. *Oxyglossum*; 5.5 cm |
| *D. cuthbertsonii* | Grossraschener Orchideen | Lost | Sect. *Oxyglossum*; mounted |
| *D. hellwigianum* | Ecuagenera Europe | Alive | PNG highlands |
| *D. cyanocentrum* 'Blau' | Grossraschener Orchideen | Alive | Blue form |
| *D. jenkinsii* | Grossraschener Orchideen | Alive | Miniature; South/Southeast Asia |
| *D. lamyaiae* | Currlin Orchideen | Alive | Thai miniature |
| *D. Betty Goto* f. coerulea | Celandroni Orchidee | Alive | Miniature hybrid |
| *D. trantuanii* | Growlist | Alive | Vietnamese miniature |

The single loss (*D. cuthbertsonii*) — a notoriously challenging sect. *Oxyglossum* species that demands near-constant moisture and cool temperatures — was replaced successfully with a second clone. The 89% survival rate across the genus confirms that miniature and highland *Dendrobium* are excellent candidates for convergent cloud forest cultivation, provided species requiring dry rest are excluded.

[USER INPUT NEEDED — Cultivation observations:
- Flowering frequency and season
- Growth rate and cane production
- Photos: blue-purple flowers, whole-plant shots on mounts]

### 3.7 Brazilian Atlantic Forest Highlands: Rupicolous *Cattleya*, *Sophronitis*, *Laelia*, and *Leptotes*

*Cattleya* subg. *Sophronitis* (syn. *Sophronitis*), *Laelia*, and *Leptotes* — miniature rupicolous orchids from the Brazilian Atlantic Forest highlands at 800--2,000 m — are mounted on cork bark in the upper and middle zones. The Brazilian highland species are notable because their native habitat — cool, moist mountaintops along the Atlantic coast — is climatically convergent with Andean cloud forests despite being separated by the Amazon basin.

| Taxon | Source | Status | Notes |
|-------|--------|--------|-------|
| *Cattleya aclandiae* (selected cross) | Grossraschener Orchideen | Alive | — |
| *C. walkeriana* f. semialba 'Tokyo No.1' AM/AOS | Claessen Orchids | Alive | 10 cm |
| *C. walkeriana* coerulea 'Blu Monarch' x 'ABC' | Lo Scrigno di Nebbia | Alive | — |
| *Sophronitis coccinea* f. aurea ('Atsumi' x 'Perfection') | Celandroni Orchidee | Alive | SM/JOGA Japan selection |
| *S. brevipedunculata* | Lo Scrigno di Nebbia | Alive | — |
| *S. wittigiana* rosea | Lo Scrigno di Nebbia | Alive | — |
| *S. pygmaea* (x2) | Grossraschener Orchideen | Lost (both) | — |
| *Laelia ghillanyi* | Grossraschener Orchideen | Alive | — |
| *L. milleri* | eBay | Alive | — |
| *L. lundii* coerulea | Nardotto e Capello | Alive | — |
| *L. briegeri* | Ecuagenera | Lost | CITES import |
| *Leptotes bicolor* | Orchideria di Morosolo | Alive | Mounted |
| *Isabelia pulchella* | Varesina Orchidee | Alive | Mounted |

The combined survival rate for this Brazilian contingent is 77% (10 of 13). The double loss of *S. pygmaea* — the smallest species in the genus — suggests it may be too sensitive for year-round high humidity, while the larger *Sophronitis* (*S. coccinea*, *S. brevipedunculata*, *S. wittigiana*) and all *Cattleya* have thrived.

[USER INPUT NEEDED — Cultivation observations:
- Flowering frequency and color form notes
- Response to the lack of dry rest period
- Photos: vivid flowers against green moss]

### 3.8 Southeast Asia: Highland *Nepenthes*

Highland *Nepenthes* from Sumatra, Sulawesi, and the Philippines (1,500–3,000 m) are grown in kanuma/sphagnum on the terrarium floor, where the coolest temperatures and persistently high humidity support active pitcher production without moisture trays. The cabinet does not currently include any Bornean accession (the most famous highland Bornean species — *N. villosa*, *N. lowii*, *N. edwardsiana*, *N. rajah* — are noted here for biogeographic completeness only).

| Taxon | Source | Status | Origin |
|-------|--------|--------|--------|
| *N. aristolochioides* (Clone NM03) | Andreas Wistuba | Alive | Sumatra |
| *N. inermis* | Andreas Wistuba | Alive | Gunung Gadut, Sumatra |
| *N. tenuis* 'Reddish Leaves' | Andreas Wistuba | Alive | West Sumatra |
| *N. jamban* | Giardino Carnivoro | Alive | Barisan Mountains, Sumatra |
| *N. pitopangii* 'Ivory Colored Form' Clone:01 | Andreas Wistuba | Alive | Sulawesi |
| *N.* 'Fake Pitopangii' | Andreas Wistuba | Alive | Mislabelled clone |
| *N. argentii* | Giardino Carnivoro | Alive | Sibuyan, Philippines |
| *N. micramphora* | Giardino Carnivoro | Alive | Mt. Hamiguitan, Philippines |
| *N. glabrata* | Karnivores.com | Alive | Sulawesi |

One plant (*N. ampullaria* 'Lime Twist') was given away as a lowland species incompatible with the cool regime. All remaining 9 highland species are alive and growing, a 100% survival rate matching that of *Heliamphora*. The collection emphasizes Sumatran endemics (*N. aristolochioides*, *N. inermis*, *N. tenuis*, *N. jamban*) — species adapted to upper montane forests at 1,800--2,500 m — alongside the Philippine endemics *N. argentii* and *N. micramphora* from similar elevations.

[USER INPUT NEEDED — Cultivation observations:
- Pitcher production (lower vs. upper pitchers)
- Climbing vs. rosette behavior and growth rate
- Temperature tolerance during summer heat spikes
- Photos: pitcher diversity, growth habit]

### 3.9 Southeast Asian Miniature Orchids and Companion Plants

The terrarium houses a diverse group of miniature orchids from Southeast and East Asia:

| Taxon | Source | Status | Notes |
|-------|--------|--------|-------|
| *Neofinetia falcata* 'Benitengu' | Celandroni Orchidee | Alive | — |
| *N. falcata* 'Akausagi' | Negie Orchids, Japan | Alive | Near blooming size |
| *N. falcata* | Grossraschener Orchideen | Alive | — |
| *Neostylis* Lou Sneary | Celandroni Orchidee | Alive | *N. falcata* x *Rhynchostylis coelestis* |
| *Holcoglossum flavescens* | Celandroni Orchidee | Alive | — |
| *H. tsii* | Orchids & more | Alive | — |
| *H. amesianum* | Claessen Orchids | Alive | — |
| *H. quasispinifolium* | Nardotto e Capello | Lost | — |
| *Vanda coerulescens* | Celandroni Orchidee | Alive | Miniature |
| *V. nana* | Claessen Orchids | Alive | Miniature |
| *Gastrochilus japonicus* | Varesina Orchidee | Alive | Mounted |
| *Chiloschista himalaica* | Orchids & more | Alive | Leafless miniature |
| *Cleisostoma arietinum* | Orchids & more | Alive | — |
| *Schoenorchis pachyacris* | Growlist | Alive | — |
| *Ceratochilus biglandulosus* | Grossraschener Orchideen | Alive | — |
| *Maxillaria sophronitis* | Orchids & more | Alive | — |
| *Maxillaria tenuifolia* | — | Alive | Coconut-scented flowers |

Companion plants include living *Sphagnum* (2 species surviving: *S. papillosum* and *S. fallax*; *S. girgensohnii* was lost), which serves as both substrate surface and moisture indicator.

[USER INPUT NEEDED:
- Highland fern species present
- Small bromeliads or other companion plants
- Which species arrived naturally vs. intentionally planted
- Photos]

---

## 4. Environmental Results

### 4.1 Temperature and Humidity

Over four years of monitoring, the terrarium maintained the following conditions:

| Parameter | Minimum | Maximum | Typical Range | Target Source |
|-----------|---------|---------|---------------|--------------|
| Temperature | 13.5 deg C | 24.3 deg C | 15--22 deg C | Weather-derived (clamped 12--24 deg C) |
| Relative Humidity | 75% | 98% | 82--95% | Weather-derived (clamped 75--95% since 2026-04-30) |
| VPD | 0.03 kPa | 0.64 kPa | 0.08--0.45 kPa | < 0.8 kPa |

The system achieves a 4--8 deg C diurnal temperature swing despite the terrarium being located in a room at approximately 22 deg C. Nighttime temperatures routinely drop to 14--16 deg C through active compressor cooling, while daytime temperatures rise to 18--22 deg C. This range is consistent with field measurements from tepui summits: Adlassnig et al. (2010) recorded daytime temperatures of 15--21 deg C and nighttime lows of 5--13 deg C within a *Heliamphora nutans* population on Roraima (2,810 m).

VPD values below 0.4 kPa, corresponding to near-saturation conditions, are maintained for the majority of the 24-hour cycle. This is critical for *Heliamphora* pitcher health (preventing desiccation of pitcher fluid and nectar spoons) and for the delicate stolons of epiphytic *Utricularia*.

### 4.2 Weather Data Integration

The Colombian weather integration produces continuously varying setpoints that reflect real meteorological conditions. The 15-hour backward lookup is best understood in combination with the 7-hour Italy-to-Colombia time-zone offset: their sum (~22 hours) is close to a full diurnal cycle, so the cabinet's target at any Italian local time tracks Colombian weather from approximately the same time-of-day, one day earlier. At Italian noon the controller retrieves Colombian conditions from 15 h prior (= Colombian local 14:00 the previous day, afternoon, warm and slightly drier), and at Italian midnight it retrieves Colombian data from 02:00 Colombian local time the same day (the pre-dawn minimum, cool and near-saturated). The pairing produces the natural diurnal pattern of cloud-forest environments — warmer/drier days, cooler/wetter nights — phase-aligned to Italian local time. Without the shift, the time-zone offset alone would invert the pattern.

Rain events in Colombia translate into corresponding terrarium setpoint changes — temperature drops of several degrees within an hour accompanied by humidity targets approaching saturation — creating the sudden environmental perturbations that cloud forest species experience naturally. These events emerge from the weather data feed and vary from day to day, week to week, and season to season, providing the kind of stochastic environmental variation that fixed schedules cannot replicate.

### 4.3 PID Controller Performance

The gain-scheduled PID controller maintains humidity within +/-3% RH of the setpoint under steady-state conditions. An instrumental-variables (2SLS) analysis using a randomised A/B night-mode schedule as instrument estimates the PID-controlled fans' causal effect on humidity at **-0.34% RH per +10 PWM of fan speed (95% CI: -0.68 to -0.005; p = 0.047; n = 1,353 nighttime 5-min observations; first-stage F = 22.5)**. The naive OLS comparator returns +0.15% per +10 PWM — the wrong sign — confirming that simple regression captures the controller's reaction to humidity rather than the fans' causal effect, and motivating the IV approach. The compressor is the dominant cooling and dehumidification actuator (-15.9% humidity long-run effect when active), with the PID fans providing fine-tuning within the compressor's hysteresis band. Heat-balance attribution: the 80.3-day rerun (n = 17,773 5-min observations, HC3 robust SEs) attributes essentially all of the active cooling work to the compressor (-1.01 °C/hr when active, 95% CI: -1.05 to -0.97); full details in the companion HardwareX paper §7.4.

### 4.4 Maximum Cooling Capacity

Three nights of forced-cooling tests (compressor on continuously, evaporator and circulation fans at maximum, ventilation fans off) established the system's thermal limits:

| Metric | Night 1 | Night 2 | Night 3 (near-equilibrium) |
|--------|---------|---------|----------------------|
| Starting temperature | 17.9 deg C | 17.3 deg C | 17.9 deg C |
| Minimum temperature | 12.3 deg C | 13.2 deg C | 13.6 deg C |
| Room temperature | 22.6 deg C | 21.4 deg C | 21.6 deg C |
| Delta T (room to min) | 10.3 deg C | 8.2 deg C | 8.1 deg C |
| Cooling duration | 9.5 h | 9.5 h | 9.9 h |

The near-equilibrium minimum of 13.6 deg C on Night 3 (cabinet within ~0.5 deg C of steady state at test end, after 9.9 h of continuous compressor operation) is 3.0 deg C below the room wet-bulb temperature — demonstrating that the marine compressor accesses a thermal regime inaccessible to evaporative methods. A thermal mass plateau at 15.6 +/- 0.2 deg C was observed for approximately 38 minutes on 2 of 3 nights. The 9.5–9.9 h tests are reported here as near-equilibrium rather than equilibrium; a 24-h forced-cooling test would convert the language to fully rigorous and is on the future-work list.

### 4.5 Phenological Observations

[USER INPUT NEEDED — Observed correlations between environmental conditions and plant phenology:
- Do Heliamphora flower more at certain times of year?
- Do Utricularia flowering events correlate with temperature drops or humidity spikes?
- Observable growth rate changes with season?
- Pitcher production timing in Nepenthes — seasonal pattern?
- Orchid flowering frequency — any correlation with photoperiod or weather events?]

---

## 5. Discussion

### 5.1 Convergent Cloud Forest Cultivation

A central finding of this work is that species from geographically disjunct cloud forests can be co-cultivated in a single enclosure tuned to their shared climatic envelope. The carnivorous and non-carnivorous taxa discussed here occupy very different niches in nature: *Heliamphora* and *Brocchinia reducta* grow on open, treeless tepui summits; *Dracula* orchids inhabit deep Andean cloud forest understory; highland *Nepenthes* scramble through upper montane mossy forests; *Dendrobium* sect. *Oxyglossum* grows in the highlands of Papua New Guinea; rupicolous *Cattleya* clings to exposed rock faces in the Brazilian Atlantic Forest. These habitats differ in vegetation structure, light regime, substrate, and species composition — a tepui summit meadow bears no ecological resemblance to a Sumatran upper montane mossy forest.

Nevertheless, the physical climate at these sites overlaps substantially. The saturated adiabatic lapse rate in the tropics is approximately 0.5--0.6 deg C per 100 m of elevation gain. At 2,000--2,800 m — the elevation band occupied by most of the species discussed here — this produces mean temperatures of 10--18 deg C regardless of longitude, because the dominant thermal forcing is altitude, not geography. Cloud immersion frequencies of 50--80% of nighttime hours are typical of tropical montane cloud forests globally (Jarvis & Mulligan 2011), driving humidity regimes of 80--100% RH at these elevations. It is this climatic convergence — not ecological similarity — that permits co-cultivation.

The practical implication is that growers of highland cloud forest species need not maintain separate terraria for tepui *Heliamphora*, Asian *Nepenthes*, Andean *Dracula*, and PNG *Dendrobium*. A single enclosure tuned to the shared temperature and humidity requirements, with a vertical light gradient to accommodate different irradiance needs, can house all of them together.

Four years of successful co-cultivation — with species from three continents growing, flowering, and propagating side by side — validates this convergent cultivation concept. Climate-envelope compatibility is best read as a *pre-condition for inclusion in the cohort* rather than a post-hoc explanation of survival within it: dry-rest-demanding species (most of the *Cattleya* alliance with strong dry-rest cues, *Dendrobium* section *Callista*) were excluded pre-emptively, while the losses that did occur within the introduced cohort reflect a heterogeneous set of cultivation incompatibilities (warm-growing species too cool, sun-loving species too shaded, *Sophronitis pygmaea* humidity sensitivity, *Genlisea* tropical-lowland species too cool, occasional CITES-import customs failure) rather than a single thematic cause. Of the 75 currently-living accessions, the great majority originate from tropical highland cloud-forest or tepui environments and represent the cohort on which the convergence claim is grounded; a small minority (e.g., some *Pinguicula*, *Genlisea africana*) are companion taxa from neighbouring biomes that tolerate the conditions without being part of the convergence cohort.

### 5.2 Weather-Based vs. Fixed Setpoints

The use of real-time weather data represents a departure from conventional fixed-schedule control. Weather-referenced setpoints introduce stochastic variation within safe bounds — rain events in Colombia produce sudden cooling and humidity spikes that simulate fog immersion events, and the daily conditions vary in ways that would be impossible to program manually.

While not formally tested, we hypothesize that weather-driven environmental variation may improve flowering frequency and overall vigor compared to static conditions, as it more closely approximates the dynamic environments to which these species are adapted. The rich dataset generated by weather-variable control also enabled the IV/2SLS causal characterisation of the fan-to-humidity coupling (§4.3) and the companion paper's heat-balance attribution — analyses that would have been far more difficult under monotonous fixed-setpoint operation.

### 5.3 The No-Dry-Rest Tradeoff

The persistent high humidity required by *Heliamphora*, *Utricularia*, and *Dracula* precludes dry rest periods. Dry-rest-demanding species — most of the *Cattleya* alliance with strong dry-rest cues, and *Dendrobium* section *Callista* — were excluded from the cabinet pre-emptively rather than tested-and-lost, because the cabinet's continuous high humidity is fundamentally incompatible with their flowering cycle. The losses that did occur within the introduced cohort over four years (Table-listed losses in §3.2 *Pinguicula* / *Drosera* / *Genlisea*, §3.4 *Masdevallia*, §3.7 *Sophronitis* / *Laelia*) reflect a heterogeneous set of cultivation incompatibilities — *Pinguicula* losses were tropical and Mexican (not dry-rest); *Masdevallia* losses (*coccinea* 'Anchota', *glandulosa*) were temperature/humidity mismatches; *S. pygmaea* losses (×2) reflected humidity sensitivity; *Genlisea* losses were tropical lowland; *L. briegeri* lost on CITES import — not a single thematic cause. Climate-envelope compatibility is therefore a pre-condition for inclusion in the cohort, not a post-hoc explanation of survival within it.

This is a fundamental tradeoff of the single-biome approach. The system selects for species compatible with continuous high moisture, which is precisely the defining feature shared by convergent cloud forests worldwide.

### 5.4 Limitations

- **Single sensor**: The SHT35 provides point measurements at mid-canopy height. Temperature stratification is certain — the upper zone near the LEDs is warmer than the lower zone. Reported temperatures represent mid-canopy conditions, not the full range experienced by individual plants.
- **No formal growth metrics**: Claims of "successful cultivation" are based on sustained growth, flowering, division, and absence of decline rather than quantitative comparison with other growers' results.
- **Not cold enough for ultra-highland species**: The minimum temperature of 13.5 deg C falls short of the sub-10 deg C nighttime temperatures on higher tepui summits (>2,500 m) and the near-freezing conditions experienced by ultra-highland *Nepenthes*. A chest freezer conversion (Shafer 2003) remains more appropriate for these extreme species.
- **Light-heat tradeoff**: LED output becomes heat load inside the enclosure. At ~96--144 W effective output, the lighting contributes a substantial fraction of the cooling load, limiting the achievable combination of high light and low temperature.
- **Mediterranean summer challenge**: During the hottest weeks (room temperatures reaching 27--28 deg C), the compressor runs continuously and nighttime temperatures may not drop below 16--17 deg C.
- **Internet dependency**: Weather-based setpoints require API access. Mitigated by a 14-day historical fallback curve but not eliminated.

### 5.5 Open-Source Accessibility

The entire system is built on freely available software and commodity hardware. Node-RED's visual flow-based programming lowers the barrier to entry. The comprehensive data logging (33 InfluxDB measurements at 60-s cadence for continuous channels plus event-driven actuator-change logging) enables operational monitoring and experimental analysis without additional instrumentation — the same pipeline that supported the IV/2SLS causal inference reported here and the companion paper's heat-balance regression. All source code, firmware, dashboards, analysis scripts, and documentation are available at https://github.com/GabrieleZoppoli/terrarium-control-system.

---

## 6. Conclusions

We have demonstrated a weather-mimicking terrarium system that simulates highland cloud forest climates using real-time Colombian meteorological data, successfully cultivating 75 living accessions across 31 plant genera from convergent cloud forests across three continents for over four years.

The **weather-mimicking approach** — ingesting real weather data and applying a 15-hour time shift — produces naturalistic, stochastic environmental variation that captures the dynamic character of tropical montane climates. The comprehensive data logging enabled by this approach has supported the IV/2SLS causal characterisation of the fan-to-humidity coupling reported here (§4.3), and the companion paper's heat-balance attribution.

The **convergent cloud forest cultivation concept** — co-cultivating species from Venezuelan tepuis, the Colombian Andes, PNG highlands, the Brazilian Atlantic Forest, and the highland forests of Sumatra, Sulawesi, and the Philippines in a single enclosure — is validated by four years of successful growth, flowering, and vegetative propagation across taxonomically diverse genera. The success rests on recognizing that cloud forests worldwide converge on similar climatic envelopes, driven by the physics of tropical mountain meteorology rather than by biogeographic proximity.

**Marine compressor refrigeration** provides effective and reliable cooling for medium-to-large terraria, driving the enclosure to 13.5 deg C in a room at 22 deg C — some 3 deg C below the evaporative cooling floor. The 80.3-day heat-balance regression reported in the companion paper attributes essentially all of the active cooling work to the compressor (−1.01 °C/hr when active), and the most broadly applicable architectural finding is that compressor cycling and fan PWM should be treated as actuators on independent control loops — compressor for temperature, fan PWM for humidity. The fan-to-humidity coupling is characterised causally by an IV/2SLS analysis at −0.34 % RH per +10 PWM (95 % CI: −0.68 to −0.005; p = 0.047; n = 1,353).

The complete system is **open-source** and reproducible using commodity hardware, enabling other growers and institutions to replicate or adapt the approach.

---

## Acknowledgments

[USER INPUT NEEDED — acknowledgments text. Suggested: acknowledge plant sources, any institutional support, beta testers, community feedback.]

Portions of this manuscript were prepared with the assistance of an AI language model (Anthropic Claude). The system design, construction, data collection, plant cultivation, and all horticultural decisions are entirely the work of the author(s).

---

## References

Adlassnig, W., Pranjic, K., Mayer, E., Steinhauser, G., Hejjas, F. & Lichtscheidl, I.K. 2010. The abiotic environment of *Heliamphora nutans* (Sarraceniaceae): pedological and microclimatic observations on Roraima Tepui. *Brazilian Archives of Biology and Technology* 53(2): 425--430.

Berry, P.E. & Riina, R. 2005. Insights into the diversity of the Pantepui flora and the biogeographic complexity of the Guayana Shield. *Biologiske Skrifter* 55: 145--167.

cexx.org. 2011. Peltier element efficiency. https://www.cexx.org/peltier.htm (accessed February 2026).

Clarke, C. 1997. *Nepenthes of Borneo.* Natural History Publications, Kota Kinabalu.

Clarke, C. 2001. *Nepenthes of Sumatra and Peninsular Malaysia.* Natural History Publications, Kota Kinabalu.

Givnish, T.J., et al. 2014. Adaptive radiation, correlated and contingent evolution, and net species diversification in Bromeliaceae. *Molecular Phylogenetics and Evolution* 71: 55--78.

Jarvis, A. & Mulligan, M. 2011. The climate of cloud forests. In Bruijnzeel, L.A., Scatena, F.N. & Hamilton, L.S. (eds.), *Tropical Montane Cloud Forests: Science for Conservation and Management.* Cambridge University Press. pp. 39--56.

McPherson, S. 2007. *Pitcher Plants of the Americas.* The McDonald & Woodward Publishing Company.

Rull, V. & Vegas-Vilarrubia, T. 2006. Unexpected biodiversity loss under global warming in the neotropical Guayana Highlands: a preliminary appraisal. *Global Change Biology* 12: 1--6.

Rull, V., Montoya, E., Nogue, S., Safont, E. & Vegas-Vilarrubia, T. 2019. Climatic and ecological history of Pantepui and surrounding areas. In Rull, V. & Vegas-Vilarrubia, T. (eds.), *Biodiversity of Pantepui: The Pristine "Lost World" of the Neotropical Guiana Highlands.* Academic Press. pp. 37--57.

Shafer, J. 2003. A novel method for the cultivation of *Nepenthes villosa*. *Carnivorous Plant Newsletter* 32(1): 20--23.

Stull, R. 2011. Wet-Bulb Temperature from Relative Humidity and Air Temperature. *Journal of Applied Meteorology and Climatology* 50(11): 2267--2269.

Taylor, P. 1999. Lentibulariaceae. In Steyermark, J.A., Berry, P.E., Yatskievych, K. & Holst, B.K. (eds.), *Flora of the Venezuelan Guayana,* Vol. 5. Missouri Botanical Garden Press. pp. 782--803.

[USER INPUT NEEDED — additional references:
- Fleischmann, A. — Utricularia sect. Orchidioides revision
- Orchid taxonomy references (Pridgeon et al. for Pleurothallidinae; Chase et al. for Cattleya reclassification)
- Any additional habitat/ecology references]

---

## Supplementary Materials

All supplementary materials are available in the GitHub repository: https://github.com/GabrieleZoppoli/terrarium-control-system

- **firmware/**: Arduino Mega and ESP8266 firmware source code
- **nodered/**: Sanitized Node-RED flow configuration and import guide
- **grafana/**: Exported Grafana dashboard definitions (4 dashboards)
- **scripts/**: Arduino watchdog, mister failsafe, Meross power monitoring daemon, Grafana snapshot capture
- **systemd/**: Service configuration files
- **analysis/**: Statistical analysis scripts including `02_iv_causal_model.py` (IV/2SLS causal inference for fan-to-humidity), `heat_balance_rerun.py` (80.3-day heat-balance OLS with HC3 robust SEs), `cooling_test_publication.py` (near-equilibrium cooling tests), and the early-iteration PID-humidity / A-B-temperature / wet-bulb-analysis scripts retained for historical reproducibility
- **docs/**: Detailed system architecture, InfluxDB schema (33 measurements), PID controller algorithm documentation with gain scheduling, acrylic panel technical drawings
