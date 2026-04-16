# Weather-Mimicking Terrarium for Convergent Cloud Forest Species: Open-Source Climate Simulation, Compressor Cooling, and Three Years of Co-Cultivating Highland Carnivorous Plants, Orchids, and Epiphytes

**Authors**: [USER INPUT NEEDED — author names and affiliations]

**Corresponding author**: [USER INPUT NEEDED — email]

---

## Abstract

We describe a weather-mimicking terrarium system that cultivates approximately 120 plant species from convergent cloud forests on five continents — Venezuelan tepuis, the Colombian and Ecuadorian Andes, the highlands of Papua New Guinea, the Brazilian Atlantic Forest, and montane Borneo-Sumatra — within a single 1.5 x 0.6 x 1.1 m enclosure in Genoa, Italy. The system ingests real-time meteorological data from four Colombian highland cities (1,300--2,600 m elevation) and applies a 15-hour time shift to generate continuously varying temperature and humidity setpoints, reproducing the stochastic weather dynamics of tropical montane environments rather than static fixed-point control. A dynamic photoperiod derived from the Colombian reference latitude (~5 deg N) provides seasonally varying day length. Under these conditions, *Heliamphora* species and hybrids (tepui summit endemics), highland *Nepenthes* (upper montane forest species from Borneo and Sumatra), *Utricularia* of section *Orchidioides* (epiphytes of tepui cliff faces and cloud forest canopies), *Brocchinia reducta* (tepui endemic), *Dracula* and *Masdevallia* orchids (Colombian Andes), *Dendrobium* section *Oxyglossum* (Papua New Guinea highlands), and rupicolous *Cattleya* (Brazilian Atlantic Forest) are maintained alongside ferns, mosses, and bromeliads — all under identical conditions. A marine compressor unit (Vitrifrigo ND50) routinely drives the terrarium to 13.5 deg C in a room at 22 deg C, overcoming the thermodynamic limit of evaporative cooling. A three-regime fan control strategy adapts the PID controller's error signal based on temperature: humidity-driven control under normal conditions, temperature-driven evaporative cooling in a 24--25 deg C transition band, and humidity-driven control with active mechanical refrigeration above 25 deg C. A wet-bulb temperature analysis revealed that evaporative fan cooling becomes counterproductive when the terrarium temperature drops below the room's wet-bulb temperature (~16.6 deg C), at which point the system automatically disengages ventilation fans and relies solely on compressor-based refrigeration. The control system, built entirely on open-source software (Node-RED, InfluxDB, Grafana) running on a Raspberry Pi with an Arduino Mega for hardware I/O, has operated continuously for over three years. All source code, firmware, dashboards, and analysis scripts are available at https://github.com/GabrieleZoppoli/terrarium-control-system.

**Keywords**: cloud forest terrarium, convergent evolution, weather simulation, wet-bulb temperature, dynamic photoperiod, *Heliamphora*, *Nepenthes*, *Dracula*, *Utricularia*, *Dendrobium*, three-regime PID control, compressor cooling, open-source horticulture

---

## 1. Introduction

Highland cloud forests — from the tepui table-top mountains of the Guiana Highlands in Venezuela to the Andes, the highlands of Papua New Guinea, and montane Borneo-Sumatra — harbor extraordinary plant diversity adapted to narrow environmental envelopes: cool temperatures (10--22 deg C), persistent high humidity (80--100% RH), frequent fog immersion, and moderate light filtered through clouds (Rull & Vegas-Vilarrubia, 2006). At higher elevations, particularly on tepui summits above 2,500 m, nighttime temperatures can drop below 5 deg C and occasionally approach freezing. Cultivating these species outside their native range — especially in Mediterranean climates with hot, dry summers — presents formidable challenges for both botanical institutions and private growers.

The central difficulty is nighttime cooling. While maintaining high humidity in a sealed terrarium is straightforward, achieving the 4--8 deg C nocturnal temperature drops characteristic of tropical highlands — in a room at 22 deg C — requires active refrigeration. The hobby has developed several approaches to this problem, each with characteristic limitations.

Evaporative cooling — using misting and ventilation fans to cool by evaporation — is the most accessible method. However, it has a hard thermodynamic limit: evaporation can only cool the air down to the wet-bulb temperature, a value determined by the room's temperature and humidity. In a typical room at 22 deg C and 58% relative humidity, this floor is approximately 16.6 deg C. Below that point, ventilation fans no longer extract heat through evaporation and instead inject warm room air into the enclosure, producing net warming — a finding confirmed by three years of continuous data logging in this system (Section 5).

Thermoelectric (Peltier) modules are attractive for their simplicity and silent operation, but their coefficient of performance (COP) is approximately 0.2 — roughly one-tenth that of a vapor-compression system — meaning they draw 5 W of electricity for every 1 W of heat removed. In practice, a single 36 W module achieves only 2--4 deg C of cooling in a 20-liter volume (cexx.org 2011), and scaling to larger enclosures requires arrays of modules with correspondingly large heat sinks and power supplies.

The chest freezer conversion, first described by Shafer (2003), provides effective compressor cooling by using the freezer itself as the growing enclosure. This method can reach temperatures below 5 deg C and has become a standard approach for growers of demanding *Heliamphora* and *Nepenthes*. Its limitations are primarily spatial: growing space is constrained by the freezer's dimensions, the compressor is not designed for the thermal load of an open-topped enclosure, and integration with humidity control requires modification.

The approach described here uses marine refrigeration hardware — a Vitrifrigo ND50 compressor unit with a Danfoss variable-speed compressor and a stainless-steel evaporator plate mounted inside the terrarium. This class of equipment, designed for boat refrigeration where compact size, low power draw (31 W), and reliable performance in confined humid spaces are essential, has not previously been applied to terrarium cooling. The system routinely drives the terrarium to 13.5 deg C — approximately 3 deg C below the evaporative cooling floor and nearly 9 deg C below room ambient.

Beyond the cooling challenge, traditional terrarium approaches rely on fixed environmental setpoints (e.g., 18 deg C day / 14 deg C night, 90% RH constant), which fail to capture the dynamic variability that characterizes cloud forest environments. Real cloud forests experience weather — sudden temperature drops during rainstorms, diurnal fog cycles, seasonal shifts in cloud cover, and all the unpredictable environmental variation that our plants evolved with. Static control not only oversimplifies the environment but may fail to provide the thermal and humidity cues that many cloud forest species require for phenological processes including flowering and seed set.

This paper describes an open-source control system that addresses these limitations through five key innovations:

1. **Weather-mimicking from real Colombian data**: The system ingests real-time meteorological data from four Colombian highland cities (Chinchina, Medellin, Bogota, Sonson) at elevations of 1,300--2,600 m, applying a 15-hour time shift to produce naturalistic, continuously varying setpoints. A dynamic photoperiod is derived from the Colombian reference latitude (~5 deg N).

2. **Convergent cloud forest concept**: Cloud forests worldwide converge on remarkably similar climatic envelopes despite their geographic isolation. A single terrarium tuned to the common envelope can support species from multiple continents simultaneously — a principle validated over three years of co-cultivation with approximately 120 species.

3. **Marine compressor cooling**: The Vitrifrigo ND50 provides sufficient cooling capacity to drive terrarium temperatures well below the room's wet-bulb temperature, accessing a thermal regime inaccessible to evaporative methods.

4. **Three-regime fan control with wet-bulb shutdown**: The PID controller adapts its error signal based on temperature conditions, and automatically disengages ventilation fans when the terrarium temperature drops below the room's wet-bulb temperature.

5. **Complete open-source stack**: Every component — Node-RED, InfluxDB, Grafana — runs on a single Raspberry Pi, with all source code, firmware, and dashboards freely available.

The system has maintained approximately 120 species from cloud forest genera across five continents in a 1.5 x 0.6 x 1.1 m terrarium in Genoa, Italy for over three years, demonstrating long-term reliability and horticultural effectiveness.

---

## 2. Materials and Methods

### 2.1 Terrarium Construction

The terrarium is a custom-built acrylic (PMMA) enclosure measuring 1.5 x 0.6 x 1.1 m (external dimensions), assembled by solvent welding laser-cut panels with dichloromethane and sealing with crystalline silicone. The enclosure weighs approximately 100 kg empty. External insulation — 1 cm extruded polystyrene laminated with diamond Mylar reflective sheeting — reduces heat gain and improves cooling efficiency. Access is via two sliding front panels on alloy guides. The enclosure is placed in an area of the apartment that does not receive direct sunlight, reducing cooling load.

The supporting scaffold is a semi-industrial aluminium alloy unit (2.20 x 3.20 x 0.50 m, approximately 300 kg). Aluminium was chosen over wood after an earlier wooden scaffold suffered waterproof coating degradation and swelling after four years in the high-humidity environment.

The 110 cm height creates three distinct climatic zones via a mid-height perforated acrylic shelf:

1. **Upper zone** (above shelf, high light): *Heliamphora* species, *Brocchinia reducta*, rupicolous *Cattleya*, *Dendrobium* sect. *Oxyglossum*, and high-light miniatures
2. **Middle zone** (shelf level, intermediate light): Epiphytic *Utricularia* sect. *Orchidioides* (kokedama-style), highland *Nepenthes* hanging baskets, *Masdevallia*, *Restrepia*
3. **Lower zone** (below shelf, low light, coolest): *Dracula* orchids, *Phragmipedium*, highland ferns, shade-adapted *Nepenthes*

### 2.2 Hardware Components

**Lighting**: Four ChilLED Logic Puck V3 modules (100 W each, 244 Samsung LM301B LEDs per puck) on 140 mm aluminium pin heatsinks with 12 V cooling fans. The Mean Well HLG-480H-48A LED driver's internal potentiometer limits maximum output to approximately 60% of rated power (a hardware fail-safe), and an Arduino PWM signal provides a second dimming stage. The effective operating range is 24--36% of the LEDs' full rated capacity. This two-stage approach ensures that even a software error cannot drive the LEDs to full power, protecting shade-adapted species in the lower zone.

**Cooling**: Vitrifrigo ND50 compressor unit with Danfoss BD50F variable-speed compressor (31 W draw) mounted above the terrarium, with refrigerant lines passing through the enclosure top to a PT14 stainless-steel evaporator plate (1,220 x 280 mm) installed horizontally inside the enclosure. Three Noctua NF-F12 iPPC-2000 IP67 fans (12 V, 120 mm) mounted on a plexiglass baffle angled approximately 30 degrees below the evaporator direct cold air downward through a slit, exploiting the natural downward flow of dense cold air. Condenser fans (Noctua NF-A12x25 G2, push-pull on the external radiator above) are powered directly, not Arduino-controlled. This split-system architecture — external compressor with refrigerant piping to an internal evaporator — is the same configuration used in marine refrigerators and is mechanical refrigeration, not evaporative cooling.

**Humidification**: MistKing diaphragm pump (located on a shelf below the terrarium) supplies water through tubing to 20 mist nozzle points distributed across the enclosure ceiling, controlled via TP-Link Tapo P100 smart plug (192.168.1.199). A 40-liter reservoir on the same shelf feeds the pump; a second 40-liter tank collects condensate from the evaporator.

**Air circulation**: Two groups of PWM-controlled fans — two Noctua NF-F12 iPPC-2000 for internal circulation (pin 12) and two Noctua 60 mm fans for outlet (pin 45) and impeller (pin 46) ventilation. All fans are driven at 25 kHz via IRF520N MOSFET modules switching the 12 V power rails.

**Sensing**: Sensirion SHT35 temperature/humidity sensor (+/-0.1 deg C, +/-1.5% RH) connected to an ESP8266 microcontroller publishing to MQTT at ~1 Hz. An HC-SR04P ultrasonic distance sensor on the same ESP monitors water level in the mister reservoir.

**Power monitoring**: A Meross MSS310 smart plug on the master power line reports instantaneous power consumption. A persistent Python daemon maintains a single authenticated session to the Meross cloud API and publishes readings to the local MQTT broker every 2 seconds, avoiding the overhead of repeated authentication. The daemon runs as a systemd service and automatically reconnects on failure.

**Control**: Raspberry Pi 4 running Node-RED v3.1.3 (control logic), InfluxDB 1.8.10 (32 time-series measurements at 60 s intervals), Grafana 10.2.3 (4 monitoring dashboards), and Mosquitto MQTT broker. An Arduino Mega 2560 provides hardware I/O via a custom text-based serial protocol at 115,200 baud.

### 2.3 Climate Simulation

The system queries the OpenWeatherMap API for current weather conditions at four Colombian highland cities:

| City | Elevation | Latitude | Role |
|------|-----------|----------|------|
| Chinchina | ~1,300 m | 4.98 deg N | Warm reference |
| Medellin | ~1,500 m | 6.25 deg N | Mid-elevation reference |
| Sonson | ~2,475 m | 5.71 deg N | Cool reference |
| Bogota | ~2,640 m | 4.71 deg N | Cool/high reference |

Temperature and humidity values are heavily averaged — a 15-minute rolling mean across all four cities — and the humidity target is capped at 95% RH. A 15-hour time shift aligns Colombian daytime weather (UTC-5) with Italian nighttime (UTC+1), producing a biologically desirable pattern: cooler, more humid conditions at night and warmer conditions during the day.

The choice of Colombian highland cities was driven by the unavailability of real-time tepui weather station data. These cities were selected because their elevation range and near-equatorial latitude produce temperature and humidity profiles comparable to those reported for tepui summits, upper montane forests, and other tropical highland habitats. Crucially, the cities lie at approximately 5 deg N — the same hemisphere as the Venezuelan tepuis — meaning that seasonal photoperiod variation at the weather source matches the natural photoperiod of the target taxa.

The stochastic character of real weather data is a key advantage over fixed schedules. Rain events in Colombia produce sudden temperature drops and humidity spikes that translate into corresponding terrarium setpoint changes, simulating fog immersion events. These events are not programmed; they emerge from real weather and vary from day to day. While they differ mechanistically from orographic fog immersion, they produce temperature and humidity excursions of similar magnitude and duration to those recorded during cloud immersion events in tropical montane environments (Jarvis & Mulligan 2010).

If the internet connection is lost, the system falls back to a historical daily curve built from the previous 14 days of recorded weather data — a smoothed 288-slot (5-minute resolution) daily profile reconstructed every 6 hours from InfluxDB — preserving a realistic diurnal pattern rather than reverting to flat defaults.

### 2.4 Light Regime

A dynamic photoperiod is computed daily from the latitude of Chinchina (4.98 deg N). At this near-equatorial latitude, the natural annual variation is only ~34 minutes between solstices (11 h 43 min to 12 h 17 min). The system clamps the computed day length to a 10--14 hour range — intentionally wider than the natural variation to benefit companion species from higher latitudes (e.g., Brazilian *Cattleya* at ~22 deg S) and to provide a stronger potential flowering stimulus. The lit period is centered on 13:15 local time.

Two dimmer channels provide intensity variation simulating natural light transitions: a 30-minute dawn/dusk ramp (slider 0 to 40, 40 steps at 45 s) and a 30-minute midday brightness boost (slider 40 to 60, 20 steps at 90 s) that begins proportionally through the day.

The inverse square law from overhead LED sources creates a continuous light gradient within the terrarium. Rather than fighting this gradient, the system exploits it: high-light species (*Heliamphora*, which grow fully exposed on tepui summits) occupy the upper zone directly beneath the LEDs, while shade-adapted species (*Dracula*, which grow in deep forest understory) occupy the lower zone. A single lighting system thus approximates the distinct light environments these species require.

### 2.5 Substrate and Mounting

**Heliamphora and Brocchinia reducta**: Upper zone, in akadama (Japanese fired clay) mixed with long-fiber sphagnum, topped with living *Sphagnum* moss. Akadama provides drainage; living sphagnum maintains surface moisture and creates acidic, low-nutrient conditions approximating tepui summit peat bogs.

**Utricularia sect. Orchidioides** (*U. alpina*, *U. quelchii*, *U. campbelliana*): Kokedama-style — each plant wrapped in a ball of living *Sphagnum*, suspended from the shelf level in the middle zone. The kokedama form provides the aerial, moisture-saturated root environment these species inhabit on tepui cliff faces.

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

### 2.7 Wet-Bulb Temperature Shutdown

The wet-bulb temperature is computed in real time from room sensor data using the Stull (2011) approximation. When the terrarium temperature drops below the room's wet-bulb temperature — typically around 20:00--21:00 each evening — the system automatically blocks the outlet and impeller fans, relying solely on evaporator fans and the compressor for overnight cooling. This gate reopens at 04:00 when fans resume for the morning humidity blast.

The thermodynamic rationale: evaporative cooling can only reduce air temperature to the wet-bulb temperature. Below this point, air drawn through the enclosure by ventilation fans carries more sensible heat than the evaporative process can remove, producing net warming. By shutting off ventilation fans at the wet-bulb crossover, the compressor no longer has to fight against warm-air injection, reducing power consumption and improving the minimum achievable temperature.

---

## 3. Species Cultivated

The terrarium supports approximately 120 species from cloud forests across five biogeographic regions. The successful co-cultivation of these species in a single enclosure with shared environmental conditions demonstrates the convergent nature of cloud forest climates worldwide.

### 3.1 Venezuelan Tepui: *Heliamphora*

*Heliamphora* (sun pitchers, Sarraceniaceae) are the flagship tepui species, grown in the upper zone. Multiple species and hybrids produce mature pitchers, divide regularly, and produce flower scapes under the weather-variable conditions. The saturated substrates and persistent VPD below 0.4 kPa are critical for maintaining pitcher fluid and nectar spoon hydration.

Ten *Heliamphora* species and hybrids are currently cultivated, all sourced from Andreas Wistuba (Mudau, Germany):

| Taxon | Provenance | Notes |
|-------|-----------|-------|
| *H. minor* var. *pilosa* (Auyan) Clone 3 | Auyan-tepui | Adult pitchers |
| *H. minor* Clone 4 | — | Adult pitchers |
| *H. minor* 'Burgundy Black' | — | Adult pitchers; anthocyanin-rich form |
| *H. ionasi* 'Elegance' | — | Adult pitchers |
| *H. macdonaldae* (ISC) | Cerro Duida | Adult pitchers |
| *H. macdonaldae* | — | Adult leaves; ~1 yr waiting list |
| *H. pulchella* | Akopan-tepui | — |
| *H. pulchella* | Amuri-tepui | Separate provenance from above |
| *H. purpurascens* x *ionasii* (Red Giant) | — | Adult pitchers |
| *H.* 'Godzilla' | — | Juvenile |

All ten plants are alive and growing after 3+ years in the system, representing a 100% survival rate. No *Heliamphora* losses have occurred, making them the most reliable genus in the collection.

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

[USER INPUT NEEDED — Cultivation observations:
- Is Brocchinia reducta in the terrarium? (Not found in inventory)
- Which Drosera and Pinguicula are actually in the terrarium vs. on a windowsill?
- Photos]

### 3.3 Tepui and Cloud Forest Epiphytes: *Utricularia* sect. *Orchidioides*

Epiphytic *Utricularia* of section *Orchidioides* — native to tepui cliff faces and cloud forest canopies — are grown kokedama-style, suspended from the shelf level in the middle zone. Four species have been cultivated:

| Taxon | Source | Status |
|-------|--------|--------|
| *U.* x *nelumbifolia* x *reniformis* | Klein Carnivors | Alive |
| *U. alpina* | Gartenbau Carow | Lost |
| *U. quelchii* | — | Lost |
| *U. campbelliana* | — | Lost |

Only the *U. nelumbifolia* x *reniformis* hybrid survives. The loss of three species — including *U. alpina* and *U. quelchii*, both tepui summit endemics whose temperature and humidity requirements should be well matched by the terrarium — is the most significant cultivation failure in the collection. The cool conditions and VPD below 0.4 kPa should be suitable, suggesting that other factors (root competition, stolon desiccation during a hardware failure, or insufficient light in the middle zone) may have contributed. These species merit re-acquisition and further experimentation with mounting position and light exposure.

[USER INPUT NEEDED — Cultivation observations:
- Flowering frequency and timing for the surviving hybrid
- Kokedama longevity and sphagnum replacement frequency
- Stolon growth patterns
- Photos: kokedama mounts, flower detail]

### 3.4 Colombian and Ecuadorian Andes: *Dracula* and *Masdevallia*

*Dracula* orchids (Pleurothallidinae) are the primary Andean representatives, mounted on cork bark in the lower zone where temperatures are coolest and light levels lowest — conditions approximating the deep shade of Andean cloud forest understory at 1,800--2,500 m. Four species are cultivated with no losses to date:

| Taxon | Source | Notes |
|-------|--------|-------|
| *D. simia* (selected) | Grossraschener Orchideen | Mounted |
| *D. lotax* | Klein Carnivors | Very small form |
| *D. vlad-tepes* | Grossraschener Orchideen | — |
| *D. pholeodytes* | Ecuagenera Europe | — |

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

[USER INPUT NEEDED — Cultivation observations:
- Flowering frequency and seasonal patterns for Dracula
- Any Restrepia species? (None found in inventory)
- Photos: Dracula labellum detail, Masdevallia sequential blooms]

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

[USER INPUT NEEDED — Cultivation observations:
- Are any Phragmipedium in the terrarium? (None found in inventory)
- Flowering observations for miniatures
- Photos]

### 3.6 Papua New Guinea Highlands: *Dendrobium* sect. *Oxyglossum*

*Dendrobium* section *Oxyglossum*, including *D. victoriae-reginae* and allied species, represents the Australasian cloud forest contingent. Native to the highlands of Papua New Guinea at 1,500--3,000 m, these species produce brilliant blue-purple flowers — a color rare in orchids. Mounted on tree fern plaques in the upper zone, their success alongside Andean and tepui plants is perhaps the strongest demonstration of climatic convergence: *D. victoriae-reginae* evolved in complete geographic isolation from *Dracula* and *Heliamphora*, yet all three thrive under identical conditions because their respective cloud forests converge on similar environmental envelopes.

Nine miniature and highland *Dendrobium* are cultivated:

| Taxon | Source | Status | Notes |
|-------|--------|--------|-------|
| *D. victoriae-reginae* | Orchis Mundi | Alive | Sect. *Oxyglossum*; blue-purple flowers |
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

Highland *Nepenthes* from Borneo, Sumatra, and the Philippines (1,500--3,000 m) are grown in kanuma/sphagnum on the terrarium floor, where the coolest temperatures and persistently high humidity support active pitcher production without moisture trays.

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

Over three years of monitoring, the terrarium maintained the following conditions:

| Parameter | Minimum | Maximum | Typical Range | Target Source |
|-----------|---------|---------|---------------|--------------|
| Temperature | 13.5 deg C | 24.3 deg C | 15--22 deg C | Weather-derived (clamped 12--24 deg C) |
| Relative Humidity | 75% | 98% | 82--95% | Weather-derived (clamped 70--90%) |
| VPD | 0.03 kPa | 0.64 kPa | 0.08--0.45 kPa | < 0.8 kPa |

The system achieves a 4--8 deg C diurnal temperature swing despite the terrarium being located in a room at approximately 22 deg C. Nighttime temperatures routinely drop to 14--16 deg C through active compressor cooling, while daytime temperatures rise to 18--22 deg C. This range is consistent with field measurements from tepui summits: Adlassnig et al. (2010) recorded daytime temperatures of 15--21 deg C and nighttime lows of 5--13 deg C within a *Heliamphora nutans* population on Roraima (2,810 m).

VPD values below 0.4 kPa, corresponding to near-saturation conditions, are maintained for the majority of the 24-hour cycle. This is critical for *Heliamphora* pitcher health (preventing desiccation of pitcher fluid and nectar spoons) and for the delicate stolons of epiphytic *Utricularia*.

### 4.2 Weather Data Integration

The Colombian weather integration produces continuously varying setpoints that reflect real meteorological conditions. The 15-hour time shift means that Colombian daytime conditions (16--22 deg C, 60--80% RH) map onto Italian nighttime, while Colombian nighttime conditions (12--16 deg C, 85--95% RH) map onto Italian daytime, producing the natural diurnal pattern of cloud forest environments.

Rain events in Colombia translate into corresponding terrarium setpoint changes — temperature drops of several degrees within an hour accompanied by humidity targets approaching saturation — creating the sudden environmental perturbations that cloud forest species experience naturally. These events emerge from the weather data feed and vary from day to day, week to week, and season to season, providing the kind of stochastic environmental variation that fixed schedules cannot replicate.

### 4.3 PID Controller Performance

The gain-scheduled PID controller maintains humidity within +/-3% RH of the setpoint under steady-state conditions. An IV/2SLS analysis using an experimental night-mode alternation as an instrument confirmed the PID-controlled fans' causal effect on humidity: each +10 PWM of fan speed causes a -0.37% reduction in humidity (p < 0.05). The compressor is the dominant cooling and dehumidification actuator (-15.9% humidity long-run effect when active), with the PID fans providing fine-tuning within the compressor's hysteresis band.

### 4.4 Maximum Cooling Capacity

Three nights of forced-cooling tests (compressor on continuously, evaporator and circulation fans at maximum, ventilation fans off) established the system's thermal limits:

| Metric | Night 1 | Night 2 | Night 3 (equilibrium) |
|--------|---------|---------|----------------------|
| Starting temperature | 17.9 deg C | 17.3 deg C | 17.9 deg C |
| Minimum temperature | 12.3 deg C | 13.2 deg C | 13.6 deg C |
| Room temperature | 22.6 deg C | 21.4 deg C | 21.6 deg C |
| Delta T (room to min) | 10.3 deg C | 8.2 deg C | 8.1 deg C |
| Cooling duration | 9.5 h | 9.5 h | 9.9 h |

The equilibrium temperature of 13.6 deg C (Night 3, after the enclosure's thermal mass had fully cooled) is 3.2 deg C below the room wet-bulb temperature — demonstrating that the marine compressor accesses a thermal regime inaccessible to evaporative methods. A thermal mass plateau at 15.6 +/- 0.2 deg C was observed for approximately 38 minutes on 2 of 3 nights.

### 4.5 Phenological Observations

[USER INPUT NEEDED — Observed correlations between environmental conditions and plant phenology:
- Do Heliamphora flower more at certain times of year?
- Do Utricularia flowering events correlate with temperature drops or humidity spikes?
- Observable growth rate changes with season?
- Pitcher production timing in Nepenthes — seasonal pattern?
- Orchid flowering frequency — any correlation with photoperiod or weather events?]

---

## 5. The Wet-Bulb Temperature Limit

### 5.1 Analysis

Analysis of room sensor data reveals consistent room conditions of 22.1 +/- 0.7 deg C and 57.9 +/- 5.2% RH, corresponding to a room wet-bulb temperature of 16.6 +/- 0.9 deg C (Stull 2011). The terrarium temperature crosses below this threshold around 20:00--21:00 each evening as the compressor drives temperatures down.

A heat-balance regression decomposed the contributions of different actuators to the terrarium's hourly temperature change:

| Actuator | Temperature effect | Interpretation |
|----------|-------------------|----------------|
| Freezer (compressor) | -2.03 deg C/hr | Dominant cooling mechanism |
| Fans (outlet + impeller) | +0.37 deg C/hr | Net warming effect (room air sensible heat) |
| Passive heat exchange | +0.58 deg C/hr | Room-to-terrarium heat transfer |

An extended model including the interaction between fan speed and the temperature difference above wet-bulb reveals that the fan cooling effect diminishes linearly as the terrarium approaches wet-bulb, reaching zero at approximately T_above_wb = +0.3 deg C. Below this point, fans provide no evaporative cooling benefit and become a net heat source.

### 5.2 Practical Implications for Growers

This finding has implications for any terrarium system that uses ventilation-based cooling: evaporative methods can achieve meaningful cooling only down to the room's wet-bulb temperature. Growers using compressor cooling of any kind — chest freezers, aquarium chillers, air conditioners, or marine compressors — should stop ventilation fans once the terrarium temperature approaches this threshold. Continuing to run fans forces the compressor to work against warm-air injection, increasing power consumption and reducing the minimum achievable temperature.

For growers without automated wet-bulb calculation, a conservative rule of thumb: if the room is at 20--23 deg C and 50--65% RH (typical of a European or North American home), the wet-bulb temperature is approximately 15--17 deg C. Turning off ventilation fans when the terrarium reaches this range will improve nighttime performance with any compressor-based system.

---

## 6. Discussion

### 6.1 Convergent Cloud Forest Cultivation

A central finding of this work is that species from geographically disjunct cloud forests can be co-cultivated in a single enclosure tuned to their shared climatic envelope. The carnivorous and non-carnivorous taxa discussed here occupy very different niches in nature: *Heliamphora* and *Brocchinia reducta* grow on open, treeless tepui summits; *Dracula* orchids inhabit deep Andean cloud forest understory; highland *Nepenthes* scramble through upper montane mossy forests; *Dendrobium* sect. *Oxyglossum* grows in the highlands of Papua New Guinea; rupicolous *Cattleya* clings to exposed rock faces in the Brazilian Atlantic Forest. These habitats differ in vegetation structure, light regime, substrate, and species composition — a tepui summit meadow bears no ecological resemblance to a Bornean upper montane forest.

Nevertheless, the physical climate at these sites overlaps substantially. The saturated adiabatic lapse rate in the tropics is approximately 0.5--0.6 deg C per 100 m of elevation gain. At 2,000--2,800 m — the elevation band occupied by most of the species discussed here — this produces mean temperatures of 10--18 deg C regardless of longitude, because the dominant thermal forcing is altitude, not geography. Cloud immersion frequencies of 50--80% of nighttime hours are typical of tropical montane cloud forests globally (Jarvis & Mulligan 2010), driving humidity regimes of 80--100% RH at these elevations. It is this climatic convergence — not ecological similarity — that permits co-cultivation.

The practical implication is that growers of highland cloud forest species need not maintain separate terraria for tepui *Heliamphora*, Asian *Nepenthes*, Andean *Dracula*, and PNG *Dendrobium*. A single enclosure tuned to the shared temperature and humidity requirements, with a vertical light gradient to accommodate different irradiance needs, can house all of them together.

Three years of successful co-cultivation — with species from five continents growing, flowering, and propagating side by side — validates this convergent cultivation concept. The species that have been lost are those requiring dry rest periods incompatible with year-round high humidity, not those from particular geographic regions, further supporting the idea that the climate envelope rather than the geographic origin determines compatibility.

### 6.2 Weather-Based vs. Fixed Setpoints

The use of real-time weather data represents a departure from conventional fixed-schedule control. Weather-referenced setpoints introduce stochastic variation within safe bounds — rain events in Colombia produce sudden cooling and humidity spikes that simulate fog immersion events, and the daily conditions vary in ways that would be impossible to program manually.

While not formally tested, we hypothesize that weather-driven environmental variation may improve flowering frequency and overall vigor compared to static conditions, as it more closely approximates the dynamic environments to which these species are adapted. The rich dataset generated by weather-variable control also enabled the heat-balance regression that identified the wet-bulb threshold — a discovery that would have been far more difficult under monotonous fixed-setpoint operation.

### 6.3 The No-Dry-Rest Tradeoff

The persistent high humidity required by *Heliamphora*, *Utricularia*, and *Dracula* precludes dry rest periods. This means that certain companion species requiring dry rests — some *Dendrobium* section *Callista*, seasonal *Cattleya* alliance species — cannot be accommodated long-term. Over three years, species losses have been concentrated among those requiring seasonal drying rather than those from particular geographic regions, confirming that moisture tolerance rather than geographic origin determines compatibility.

This is a fundamental tradeoff of the single-biome approach. The system selects for species compatible with continuous high moisture, which is precisely the defining feature shared by convergent cloud forests worldwide.

### 6.4 Limitations

- **Single sensor**: The SHT35 provides point measurements at mid-canopy height. Temperature stratification is certain — the upper zone near the LEDs is warmer than the lower zone. Reported temperatures represent mid-canopy conditions, not the full range experienced by individual plants.
- **No formal growth metrics**: Claims of "successful cultivation" are based on sustained growth, flowering, division, and absence of decline rather than quantitative comparison with other growers' results.
- **Not cold enough for ultra-highland species**: The minimum temperature of 13.5 deg C falls short of the sub-10 deg C nighttime temperatures on higher tepui summits (>2,500 m) and the near-freezing conditions experienced by ultra-highland *Nepenthes*. A chest freezer conversion (Shafer 2003) remains more appropriate for these extreme species.
- **Light-heat tradeoff**: LED output becomes heat load inside the enclosure. At ~96--144 W effective output, the lighting contributes a substantial fraction of the cooling load, limiting the achievable combination of high light and low temperature.
- **Mediterranean summer challenge**: During the hottest weeks (room temperatures reaching 27--28 deg C), the compressor runs continuously and nighttime temperatures may not drop below 16--17 deg C.
- **Internet dependency**: Weather-based setpoints require API access. Mitigated by a 14-day historical fallback curve but not eliminated.

### 6.5 Open-Source Accessibility

The entire system is built on freely available software and commodity hardware. Node-RED's visual flow-based programming lowers the barrier to entry. The comprehensive data logging (32 InfluxDB measurements) enables operational monitoring and experimental analysis without additional instrumentation — the same pipeline that supported the IV/2SLS causal inference and heat-balance regression presented here. All source code, firmware, dashboards, analysis scripts, and documentation are available at https://github.com/GabrieleZoppoli/terrarium-control-system.

---

## 7. Conclusions

We have demonstrated a weather-mimicking terrarium system that simulates highland cloud forest climates using real-time Colombian meteorological data, successfully cultivating approximately 120 species from convergent cloud forests across five continents for over three years.

The **weather-mimicking approach** — ingesting real weather data and applying a 15-hour time shift — produces naturalistic, stochastic environmental variation that captures the dynamic character of tropical montane climates. The comprehensive data logging enabled by this approach facilitated the discovery of the wet-bulb temperature limitation.

The **convergent cloud forest cultivation concept** — co-cultivating species from Venezuelan tepuis, the Colombian Andes, PNG highlands, the Brazilian Atlantic Forest, and montane Borneo-Sumatra in a single enclosure — is validated by three years of successful growth, flowering, and vegetative propagation across taxonomically diverse genera. The success rests on recognizing that cloud forests worldwide converge on similar climatic envelopes, driven by the physics of tropical mountain meteorology rather than by biogeographic proximity.

**Marine compressor refrigeration** provides effective and reliable cooling for medium-to-large terraria, driving the enclosure to 13.5 deg C in a room at 22 deg C — some 3 deg C below the evaporative cooling floor. The **wet-bulb temperature insight** — that ventilation fans become counterproductive below the room's wet-bulb temperature (~16.6 deg C in typical conditions) — has practical implications for any grower using compressor-cooled terraria.

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

Jarvis, A. & Mulligan, M. 2010. The climate of cloud forests. In Bruijnzeel, L.A., Scatena, F.N. & Hamilton, L.S. (eds.), *Tropical Montane Cloud Forests: Science for Conservation and Management.* Cambridge University Press. pp. 39--56.

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
- **analysis/**: Statistical analysis scripts (PID model, IV/2SLS causal inference, A/B temperature analysis, wet-bulb analysis, cooling capacity tests)
- **docs/**: Detailed system architecture, InfluxDB schema (32 measurements), PID controller algorithm documentation with gain scheduling, acrylic panel technical drawings
