# Weather-Mimicking Terrarium Cultivation of Highland Carnivorous Plants: Four Years of *Heliamphora*, *Nepenthes*, and *Utricularia* sect. *Orchidioides*

**Authors**: `[PLACEHOLDER — author names and affiliations]`

**Corresponding author**: `[PLACEHOLDER — email]`

---

## Abstract

We describe the cultivation of highland carnivorous plants in a weather-mimicking terrarium over a period of four years (May 2022 to present). The system, housed in a ~1 m³ (1.5 × 0.6 × 1.1 m) insulated acrylic enclosure in Genoa, Italy, uses a marine compressor (Vitrifrigo ND50 with Danfoss variable-speed compressor, R134a refrigerant) to achieve nighttime temperatures as low as 13.5 °C in a room at 22 °C. Rather than fixed environmental setpoints, the system ingests real-time meteorological data from four Colombian highland cities (Chinchina, Medellín, Bogotá, Sonsón; 1,300–2,600 m) and applies a 15-hour backward lookup against the archived time-series; combined with the 7-hour Italy-to-Colombia time-zone offset, this phase-aligns the cabinet's daily cycle with Italian local time while preserving the stochastic weather content from the Colombian source. A dynamic photoperiod derived from the Colombian reference latitude (~5° N) provides seasonally varying day length. Under these conditions, nine living *Heliamphora* accessions (tepui summit endemics from the Guiana Highlands), nine highland *Nepenthes* (upper montane species from Sumatra, Sulawesi, and the Philippines), one living *Utricularia* of section *Orchidioides* (*U. quelchii*, Ilu Tepui provenance), and one *Brocchinia reducta* (Guiana Shield bromeliad) are maintained alongside approximately 55 non-carnivorous accessions (27 orchid and other plant genera) from the Andes, the Brazilian Atlantic Forest, Papua New Guinea, and other Southeast Asian highlands. Although these carnivorous taxa occupy ecologically distinct habitats — open tepui summits, Southeast Asian montane forest, Pantepui cliff faces — their temperature and humidity tolerances overlap sufficiently to permit co-cultivation in a single enclosure. Their different light requirements are accommodated by the inverse-square light gradient from overhead LED sources, creating a vertical irradiance gradient within the terrarium. Continuous environmental data over the 80.3-day Meross-instrumented window (2026-02-18 to 2026-05-10) show that the marine compressor performs essentially all of the active cooling work (−1.01 °C/hr when active, 95 % CI: −1.05 to −0.97; n = 17,773), while ventilation fans operate as humidity regulators (causal effect quantified by instrumental-variables 2SLS at −0.34 % RH per +10 PWM units, 95 % CI: −0.68 to −0.005; p = 0.047; n = 1,353). The first inflorescence of *U. quelchii* after three years of pure vegetative growth was recorded in April–May 2026, with two flowers fully open by Day 21. The full control system design is described in a companion publication [ref to HardwareX paper].

---

## 1. Introduction

Highland carnivorous plants — *Heliamphora* from the Venezuelan tepuis, *Nepenthes* from the upper montane mossy forests of Sumatra, Sulawesi, the Philippines, and (more famously) Borneo, epiphytic *Utricularia* of section *Orchidioides*, and the carnivorous bromeliad *Brocchinia reducta* — are among the most challenging plants in cultivation. These taxa occupy ecologically distinct habitats across the tropics. *Heliamphora* and *Brocchinia reducta* are species of the Guiana Shield, with *Heliamphora* endemic to the tepui table-top mountains and *B. reducta* ranging across the broader shield from Venezuela (Bolívar) to Guyana and northern Brazil (Roraima) per POWO; both grow in open, fog-immersed summit meadows and peat bogs at 1,500–3,000 m — exposed, treeless environments distinct from tropical montane cloud forest *sensu* Hamilton, Juvik & Scatena (1995) (Rull & Vegas-Vilarrubia 2006; Berry & Riina 2005). Highland *Nepenthes* inhabit upper montane mossy forests at similar elevations (1,500–3,000 m), growing as scrambling vines in the forest understory and canopy margins; the cabinet population sampled here is centred on Sumatra (*aristolochioides*, *inermis*, *jamban*, *tenuis*), Sulawesi (*pitopangii*, *glabrata*), and the Philippines (*argentii*, *micramphora*), with no Bornean accession currently in the cabinet (the most familiar Bornean species — *N. villosa*, *N. lowii*, *N. edwardsiana*, *N. rajah* — are noted here for biogeographic completeness but cultivation results for them in this system are not reported). *Utricularia* of section *Orchidioides* are Neotropical epiphytes spanning tepui cliff faces (*U. quelchii*, *U. campbelliana*) and Andean / Central American cloud-forest canopies (*U. alpina*, *U. jamesoniana*); the cabinet currently maintains a single *U. quelchii* of Ilu Tepui provenance (first flowering recorded April–May 2026; see §4.4).

Despite these ecological differences, the climatic tolerances of these species overlap substantially. Cool temperatures (10–22 deg C), persistent high humidity (80–100% RH), and frequent fog or cloud contact are common to tepui summits, Southeast Asian upper montane forests, and Neotropical cloud forest canopies alike — a consequence of the physical constraints of tropical mountain meteorology, which produces broadly similar temperature and humidity regimes at comparable elevations regardless of longitude. At higher elevations, particularly on tepui summits above 2,500 m, nighttime temperatures can drop below 5 deg C and occasionally approach freezing. This climatic overlap is what makes co-cultivation possible: the habitats are different, but the key environmental parameters — temperature range, humidity, and fog exposure — are shared. A remaining challenge is accommodating their different light requirements: *Heliamphora* and *Brocchinia* grow fully exposed on treeless tepui summits, while *Nepenthes* grow in the shade of montane forest. In this system, the inverse square law from overhead LED sources creates a natural light gradient within the terrarium — strong irradiance near the top, substantially lower at the bottom — allowing high-light tepui species and shade-adapted montane forest species to coexist in a single enclosure without separate lighting zones.

The central challenge in cultivating these species is not maintaining high humidity in a sealed enclosure — that is straightforward — but achieving meaningful nighttime temperature drops. In a room at 22 deg C, the terrarium must be actively cooled by 4–8 deg C every night, year-round, to simulate the nocturnal conditions of tropical highlands. The hobby has developed several approaches to this problem, each with characteristic limitations.

Evaporative cooling — using misting and ventilation fans to cool by evaporation — is the most accessible method. However, it has a hard thermodynamic limit: evaporation can only cool the air down to the wet-bulb temperature, a value determined by the room's temperature and humidity. In a typical room at 22 deg C and 58% relative humidity, this floor is approximately 16.6 deg C. Below that point, ventilation fans no longer extract heat by evaporation; their role shifts entirely to humidity regulation (see Section 5.3 for the causal quantification of fan-to-humidity coupling in this system). This means evaporative methods alone cannot reach the 10–15 deg C nighttime temperatures characteristic of the mid-to-high-elevation habitats where these species originate.

Thermoelectric (Peltier) modules are attractive for their simplicity and silent operation, but their coefficient of performance (COP) is approximately 0.2 — roughly one-tenth that of a vapor-compression system — meaning they draw 5 W of electricity for every 1 W of heat removed. In practice, a single 36 W module achieves only 2–4 deg C of cooling in a 20-liter volume (cexx.org 2011), and scaling to larger enclosures requires arrays of modules with correspondingly large heat sinks and power supplies.

The chest freezer conversion, first described in this journal by Shafer (2003), provides effective compressor cooling by using the freezer itself as the growing enclosure with a plexiglas lid replacing the original top. This method can reach temperatures below 5 deg C — cold enough for ultra-highland species — and has become a standard approach for growers of demanding *Heliamphora* and *Nepenthes*. Its limitations are primarily spatial: growing space is constrained by the freezer's dimensions, the compressor is not designed for the thermal load of an open-topped enclosure, and the aesthetic result is a chest freezer in the living room. Aquarium chillers circulating cold water through radiators or coiled tubing inside a terrarium offer more flexibility, but their cooling capacity is often marginal — they are designed for small water-temperature differentials, not sustained 8–10 deg C air-temperature drops — and they introduce condensation problems on the cold heat-exchanger surfaces. Modified portable air conditioners with external thermostats (e.g., CoolBot) provide adequate cooling power and have been used successfully for large enclosures and greenhouses, though their integration with sealed, high-humidity terraria requires careful management of the evaporator's dehumidifying effect.

The approach described here uses marine refrigeration hardware — a Vitrifrigo ND50 compressor unit with a Danfoss variable-speed compressor and a stainless-steel evaporator plate mounted inside the terrarium. This class of equipment, designed for boat refrigeration where compact size, low power draw (31 W), 12/24 V DC operation, and reliable performance in confined humid spaces are essential, has not previously been applied to terrarium cooling. The evaporator plate doubles as a condensation surface, and its large area (1220 x 280 mm) provides gentle, distributed cooling rather than the point-source cold spots of coiled tubing or radiators. The system routinely drives the terrarium to 13.5 deg C — approximately 3 deg C below the evaporative cooling floor and nearly 9 deg C below room ambient — while operating silently and drawing less power than a standard light bulb.

Beyond the cooling challenge, traditional terrarium approaches rely on fixed environmental setpoints (e.g., 18 deg C day / 14 deg C night at 90% RH), which maintain plants alive but fail to capture the stochastic variability of real tropical highland weather: sudden temperature drops during rain events, diurnal fog cycles, seasonal shifts in cloud cover, and the dynamic interplay of temperature and humidity that characterizes tropical montane climates.

This paper describes the horticultural results of cultivating *Heliamphora*, *Nepenthes*, *Utricularia* sect. *Orchidioides*, *Brocchinia reducta*, and other carnivorous taxa in a terrarium that uses real-time weather data to drive its environmental setpoints. Rather than fixed schedules, the system ingests current meteorological conditions from four Colombian highland cities (Chinchina, Medellin, Bogota, Sonson; 1,300–2,600 m elevation) and applies a 15-hour time shift to generate naturalistic, continuously varying conditions within the terrarium. The full technical description of the control system is presented in a companion paper `[ref to HardwareX]`; here we focus on the cultivation approach and plant responses.

A key conceptual framework for this work is the observation that tropical highland habitats — whether open tepui summits, Andean cloud forests, upper montane forests of Sumatra and the Philippines, or the highlands of Papua New Guinea — share broadly overlapping climatic envelopes despite their geographic isolation and ecological differences. This climatic overlap means that a single terrarium tuned to their common temperature and humidity requirements can support species from multiple continents and habitat types simultaneously, rather than requiring separate enclosures for each biogeographic region. The carnivorous plants discussed here share the terrarium with approximately 55 orchids, ferns, bromeliads, and other epiphytes from these climatically compatible tropical highland habitats — all maintained under identical conditions.

---

## 2. Materials and Methods

### 2.1 Terrarium Overview

The terrarium measures ~1 m³ (1.5 × 0.6 × 1.1 m) (external dimensions), constructed from laser-cut acrylic (PMMA) panels solvent-welded with dichloromethane and sealed with crystalline silicone. The enclosure is externally insulated with 1 cm extruded polystyrene laminated with diamond Mylar reflective sheeting. Access is via two sliding front panels.

A mid-height perforated acrylic shelf divides the enclosure into three climatic zones:

1. **Upper zone** (above shelf, highest light): *Heliamphora* species, *Brocchinia reducta*, and high-light miniatures
2. **Middle zone** (shelf level, intermediate light): *Utricularia* sect. *Orchidioides* (kokedama-style), intermediate-light orchids
3. **Lower zone** (below shelf, lowest light, coolest): Highland *Nepenthes*, shade-adapted orchids, ferns

The vertical light gradient created by the inverse square law from overhead LED sources is exploited as a design feature: high-light species (*Heliamphora*, which grow fully exposed on tepui summits) occupy the upper zone, while shade-adapted species are placed progressively lower. A single lighting system thus approximates the distinct light environments these species occupy in nature.

Hardware components include four ChilLED Logic Puck V3 LED modules (100 W each, Samsung LM301B diodes), a Vitrifrigo ND50 compressor with PT14 evaporator plate for cooling, a MistKing diaphragm pump misting system, four groups of PWM-controlled fans, and a Sensirion SHT35 sensor for temperature and humidity monitoring. Full hardware and software details are described in `[ref to HardwareX paper]`.

### 2.2 Climate Simulation

The system queries the OpenWeatherMap API for current weather conditions at four Colombian highland cities:

| City | Elevation | Role |
|------|-----------|------|
| Chinchina | ~1,300 m | Warm reference |
| Medellin | ~1,500 m | Mid-elevation reference |
| Sonson | ~2,475 m | Cool reference |
| Bogota | ~2,640 m | Cool/high reference |

Temperature and humidity values are heavily averaged — a 15-minute rolling mean across all four cities — and clamped to safe operating ranges (12–24 °C, 75–95 % RH; the humidity floor was raised from 70 % to 75 % on 2026-04-30 to better match Pantepui *Heliamphora* and Pantepui *Utricularia* preferences). Because the system reads weather data from 15 hours in the past, this aggressive smoothing incurs no responsiveness penalty. The 15-hour backward look, combined with the 7-hour Italy-to-Colombia time-zone offset, phase-aligns the cabinet's daily cycle with Italian local time rather than Colombian: at Italian noon the controller retrieves Colombian data from the previous afternoon (warm, slightly drier), and at Italian midnight it retrieves Colombian data from the same-day pre-dawn (cool, near-saturated). Without the shift, the time-zone offset alone would invert the day/night cycle and produce cool conditions during the Italian afternoon — biologically wrong. The shift is therefore a phase correction, not a delay.

The choice of Colombian highland cities was driven by the unavailability of real-time tepui weather station data when the project began. These cities were selected because their elevation range (1,300–2,600 m) and near-equatorial latitude produce temperature and humidity profiles comparable to those reported for tepui summits, upper montane forests, and other tropical highland habitats where the cultivated species originate. Crucially, the cities lie at approximately 5 deg N latitude — the same hemisphere as the Venezuelan tepuis (5–6 deg N) — meaning that seasonal photoperiod variation at the weather source matches the natural photoperiod of the target taxa.

If the internet connection is lost, the system falls back to a smoothed historical daily curve built from the previous 14 days of recorded weather data across all four cities, preserving a realistic diurnal setpoint profile rather than reverting to flat defaults.

The stochastic character of real weather data is a key advantage over fixed schedules. Rain events in the Colombian reference cities produce sudden setpoint changes in the terrarium — temperature drops of several degrees within an hour accompanied by humidity targets approaching saturation. These perturbations are not programmed; they emerge from the weather data feed and vary from day to day. While they are not direct simulations of tepui fog immersion (which is driven by orographic lifting and trade-wind convergence rather than by convective rainfall), they introduce the kind of unpredictable environmental variation that fixed schedules cannot provide, and they produce temperature and humidity excursions within the same range that tepui-summit weather stations record during cloud immersion events (Adlassnig et al. 2010).

### 2.3 Light Regime

A dynamic photoperiod is computed daily from the latitude of Chinchina (4.98 deg N) using the standard solar declination equation. At this near-equatorial latitude, the natural annual variation is only ~34 minutes between solstices, producing a day length of approximately 11h43m to 12h17m — characteristic of equatorial highlands where "winter comes every night and summer every day" (the diurnal temperature range of 10–12 deg C exceeds the annual variation in monthly means of 2–3 deg C). Although such minimal photoperiod variation has been shown to trigger seasonal responses in some equatorial organisms, the system clamps the computed day length to a 10–14 hour range. This intentionally wider variation may benefit companion species from higher latitudes (e.g., Brazilian *Sophronitis* at ~22 deg S, where natural photoperiod variation exceeds 2.5 hours) and provides a stronger potential flowering stimulus for species that respond to day-length changes. The lit period is centered on 13:15 local time.

The lighting system employs two-stage dimming. The Mean Well LED driver's internal potentiometer is adjusted to limit maximum output to approximately 60% of rated power (a hardware fail-safe). The Arduino PWM signal then operates as a second dimming stage within this range. During normal operation, the effective output is approximately 24–36% of the LEDs' full rated capacity.

As of 2026-05-04, the LED schedule is a **raised-cosine curve** through the photoperiod (replacing the prior 40–60–40 step schedule), with a soft 30-minute dawn ramp and peak intensity centred on solar noon. The peak slider setting is ~70 of 100 (corresponding to a measured cabinet peak power of ~220 W from the LEDs + ancillary daytime fan/heatsink overhead, see §4.6) — closer to a Pantepui-summit midday than the step schedule provided. The curve change has produced more naturalistic-looking afternoon humidity profiles in the cabinet relative to the previous step schedule.

### 2.4 Substrate and Mounting

**Heliamphora and Brocchinia reducta**: Grown in the upper zone in a substrate of akadama (Japanese fired clay granules) mixed with long-fiber sphagnum, topped with a layer of living *Sphagnum* moss. The akadama provides drainage and structural stability while the living sphagnum maintains surface moisture and creates the acidic, low-nutrient conditions these plants require. This combination approximates the free-draining, waterlogged-surface conditions of tepui summit peat bogs. Pots are positioned directly beneath the LED pucks for maximum light.

**Utricularia sect. Orchidioides** (*U. quelchii*, Ilu Tepui provenance — the only section *Orchidioides* representative currently in the cabinet; *U. alpina* lives elsewhere in the broader collection on a separate shelf, not in this terrarium): Grown kokedama-style — wrapped in a ball of living *Sphagnum* moss, hung from the back wall at mid-height where humidity remains consistently above 85 % under direct misting. The kokedama form provides the aerial, moisture-saturated root environment these species inhabit on tepui cliff faces, while allowing stolons to trail freely.

**Highland Nepenthes**: Planted in kanuma (Japanese volcanic pumice) mixed with long-fiber sphagnum and placed directly on the terrarium floor in the lower zone, without saucers. The kanuma provides excellent drainage and aeration while the sphagnum retains moisture around the roots. The absence of saucers prevents waterlogging — the terrarium's persistently high ambient humidity (82–95% RH) eliminates the need for supplementary moisture trays that highland *Nepenthes* growers typically rely on. The lower zone provides the coolest temperatures, benefiting these species.

`[PLACEHOLDER — photos showing substrate preparation and mounting techniques for each group]`

---

## 3. Species Cultivated

The cabinet has run continuously for four years (May 2022 to present); cabinet *residence times*, however, span a much wider range. Across the 75 currently-alive accessions, individual residence times run from ten years (*N. inermis*, March 2016) to six months (*N. jamban*, November 2025), and the cohort discussed below is the cumulative result of acquisitions, losses, and replacements across that period. The four-year framing in §1 and §6 refers to continuous system operation, not to any individual plant's tenure.

### 3.1 *Heliamphora*

Nine living accessions in the cabinet, all currently sourced from Andreas Wistuba (Mannheim, Germany), with provenance spanning Akopan Tepui, Amuri Tepui, Auyán-tepui, and Cerro Duida plus selected horticultural clones and a single hybrid (Table 1). All occupy the upper zone of the cabinet alongside *Brocchinia reducta*, under direct LED irradiance and the same temperature/humidity regime described in §4.1.

**Table 1.** Living highland *Heliamphora* accessions, current cabinet (filtered from `collection.csv` on `location=highland AND status=alive`, 2026-05-12).

| Taxon | Provenance / clone | Acquired |
|---|---|---|
| *H. pulchella* | Akopan Tepui | March 2016 |
| *H. purpurascens × ionasi* 'Red Giant' | hybrid (AW selection) | March 2016 |
| *H. minor* Clone 4 | — | March 2016 |
| *H. pulchella* | Amuri Tepui | May 2016 |
| *H. minor* 'Burgundy Black' | clonal selection | October 2016 |
| *H.* 'Godzilla' | AW-H_Godz | July 2021 |
| *H. ionasi* 'Elegance' | clonal selection | January 2023 |
| *H. macdonaldae* (Cerro Duida) ISC | — | January 2023 |
| *H. minor* var. *pilosa* (Auyán) Clone 3 | — | March 2023 |

Cabinet residence times within the *Heliamphora* cohort range from ten years (the March 2016 cohort: *pulchella* Akopan, *minor* Clone 4, *purpurascens × ionasi*) to two years (the 2023 cohort: *ionasi* 'Elegance', *macdonaldae*, *minor* var. *pilosa* Clone 3). The longest-tenured plants therefore antedate the four-year continuous run of the present cabinet — they were transferred in from the previous-generation enclosure described in §1.

`[USER INPUT — cultivation observations per species or group. Suggested fields to fill in: pitcher production cadence (new pitchers per growth point per month or per season, especially during the active growing phase); division/offset frequency; any flowering events with month and notes on whether seed set was achieved; anthocyanin response or other coloration changes correlated with light or temperature; observed size progression from acquisition photograph to current state. Pi-Claude or Mac-Claude can stitch this into a tidy paragraph or paragraph-per-species once provided.]`

`[USER INPUT — selection of in-situ cabinet photos: ideally one wide shot showing the upper-zone cluster, plus a pitcher-detail close-up of one of the strongest performers (suggest *H. ionasi* 'Elegance' or *H.* 'Godzilla'). Companion website has assets at `static/img/collection/heliamphora/` for several but not all accessions; gaps documented in the photo-coverage table in the AOS-paper draft.]`

`[USER INPUT — losses summary if any. Note for the author: collection.csv as filtered above returns 9 alive accessions; the historical record (status=lost rows for genus=Heliamphora, location=highland) should be cross-referenced for the loss list with hypothesised cause per accession.]`

### 3.2 Highland *Nepenthes*

Nine living accessions in the cabinet (with one ID-uncertain horticultural specimen), grouped here by region of origin. None are Bornean (the most famous highland Bornean species — *N. villosa*, *N. lowii*, *N. edwardsiana*, *N. rajah* — are absent from the present cabinet; the species below cover Sumatra, Sulawesi, and the Philippines).

**Sumatra (4):** *N. aristolochioides* (Sumatra, Clone NM03; alive since January 2023), *N. inermis* (Gunung Gadut, alive since March 2016 — the longest-tenured *Nepenthes* in the cabinet), *N. tenuis* 'Reddish Leaves' (West Sumatra, alive since May 2016), *N. jamban* (alive since November 2025).

**Sulawesi (2):** *N. pitopangii* 'Ivory Coloured Form' Clone 01 (alive since March 2024), *N. glabrata*.

**Philippines (2):** *N. argentii* (Mt. Guiting-Guiting, Sibuyan, alive since June 2023), *N. micramphora* (Mindanao, alive since June 2023).

**Horticultural label, identity uncertain (1):** *N.* 'Fake Pitopangii' — originally sold as *N. pitopangii* 'Ivory Coloured Form' but with morphology that does not match the species; retained in the cabinet because its cultural requirements have proven compatible with the cohort, but its taxonomic status is treated as horticultural-label-only.

Cultivation uniform across the cohort: 4–6 inch perforated terracotta or net pots in a kanuma/perlite/sphagnum mix (approximately 2:1:1 by volume), topped with living *Sphagnum*. Plants grow either as rosettes on the cabinet floor or, in the case of climbing forms, with the leading stem trained up to mid-height; mature stems develop both lower and upper pitchers. No saucers; the cabinet's misting + condensate cycle maintains substrate moisture without standing water in the pots. Free draining at the bottom of the cabinet feeds the condensate reservoir.

Pitcher production has been steady across the cohort, with no extended dormancies observed; the cabinet's continuous high humidity and 4–8 °C diurnal swing reproduces the conditions of the Sumatran and Philippine upper montane forest closely enough to support both upper and lower pitcher development on most accessions.

`[PLACEHOLDER — photos: a wide shot of the cabinet floor with several Nepenthes visible; a close-up of *N. aristolochioides* upper pitcher (the "fenestrated cap" feature is photogenic); a *N. jamban* pitcher detail (the genus's most distinctive recently-described form).]`

`[PLACEHOLDER — historical losses for the *Nepenthes* group, if any. The current alive count is 9; the historical record shows one *N. ampullaria* 'Lime Twist' given away in 2017, which is a lowland species and not a cabinet failure.]`

### 3.3 *Utricularia* sect. *Orchidioides*

**Cabinet contents: one accession, *Utricularia quelchii* (Ilu Tepui provenance)** — acquired early 2023 from Carnivors & More (C. & C. Klein) and grown kokedama-style in a 10 cm perforated terracotta, hung on the back wall at mid-height under direct misting. Substrate: live *Sphagnum* only. Foliar feed: Akerne Orchid Mix at half a teaspoon per three litres, two applications per month.

Three years of pure vegetative growth (steady leaf addition, no inflorescences) preceded the first flowering, recorded as follows:

- **20 April 2026** — First inflorescence observed: an erect, red-purple peduncle bearing two buds, emerging from the *driest* portion of the kokedama (the ~2 cm of moss against the cabinet wall, not the wetter pot interior). The location is suggestive: continuous saturation may not be the floral cue.
- **7 May 2026** — Day 17. The larger of the two buds opened, displaying the full section *Orchidioides* gestalt: hooded magenta galea, yellow-cream throat with two red callus blotches, and a broad pink lower lip.
- **11 May 2026** — Day 21. The second bud opened. Both flowers held on the same scape; colour was uniform across both (no shift toward the deeper red of the Roraima phenotype documented by Taylor 1989, consistent with the Ilu Tepui clonal origin).

Flowers persisted for approximately three weeks before senescence (observation ongoing). Across the four-year cabinet residence, the plant has progressed from three or four leaves to a fully established rosette occupying the entire pot, with stolons trailing through the surrounding *Sophronitis* aerial roots above. No prior flowering attempt was observed during the vegetative period.

This is the first published record of *U. quelchii* flowering in this terrarium and adds to the small body of cultivation records for the species outside its native range.

The companion *U. campbelliana* (also Ilu-sourced, separate cabinet acquisition) and *U. alpina* (broader collection, *not* in this cabinet) are not included in this report.

`[PLACEHOLDER — photos: kokedama in situ showing the plant before flowering; the 20-April first-bud frame; the open Day-17 flower; the Day-21 two-flowers-open photograph (suggested cover-image candidate). All eight photos exist on the companion website blog post; recommend using utricularia-quelchii-7.jpg (single open flower), utricularia-quelchii-14.jpg (both open), and utricularia-quelchii-9.jpg (three-quarters view) as a triptych.]`

### 3.4 *Brocchinia reducta* and Other Carnivorous Taxa

*Brocchinia reducta* is cultivated in the upper zone alongside *Heliamphora*, in the same akadama/sphagnum substrate topped with living *Sphagnum*. As a Guiana Shield species (POWO: native range Venezuela [Bolívar] to Guyana and Brazil [Roraima], in the wet tropical biome — broader than the "tepui summit endemic" sometimes attributed to it), it thrives under the high irradiance of the upper zone and the same temperature and humidity regime as the *Heliamphora*.

`[PLACEHOLDER — observations on Brocchinia reducta:]`
- `[Growth rate, rosette size]`
- `[Tank fluid observations — prey capture?]`
- `[Offset production]`

`[PLACEHOLDER — list any additional carnivorous plants maintained in the system:]`
- `[Drosera species?]`
- `[Catopsis berteroniana?]`
- `[Any other genera?]`

`[PLACEHOLDER — brief notes and photos for each]`

---

## 4. Environmental Results

### 4.1 Temperature and Humidity

Over the monitoring period (four years), the terrarium maintained the following conditions:

| Parameter | Minimum | Maximum | Typical range | Target range |
|---|---|---|---|---|
| Temperature | 13.5 deg C | 24.3 deg C | 15–22 deg C | Weather-derived (clamped 12–24 deg C) |
| Relative humidity | 75 % | 98 % | 83–95 % | Weather-derived (clamped 75–95 % since 2026-04-30) |
| VPD | 0.03 kPa | 0.64 kPa | 0.08–0.45 kPa | < 0.8 kPa |

The system achieves a 4–8 deg C diurnal temperature swing, with nighttime temperatures routinely dropping to 14–16 deg C through active compressor cooling and daytime temperatures rising to 18–22 deg C. This approximates the diurnal range at 2,000–2,800 m in the tropical highlands where the cultivated species originate.

VPD values below 0.4 kPa, corresponding to near-saturation conditions, are maintained for the majority of the 24-hour cycle. This is critical for *Heliamphora* pitcher health (preventing desiccation of pitcher fluid and nectar spoons) and for the delicate stolons of epiphytic *Utricularia*.

### 4.2 Diurnal Temperature Swing

The 4–8 deg C diurnal swing is consistent with field measurements from tepui summits. Adlassnig et al. (2010) recorded daytime temperatures of 15–21 deg C and nighttime lows of 5–13 deg C within a *Heliamphora nutans* population on Roraima (2,810 m). The terrarium's swing is somewhat narrower than these extremes but falls well within the operating range of the cultivated species.

The diurnal swing has several functional consequences:

- **Condensation on cold surfaces**: Nighttime cooling drives the evaporator plate surface below the dew point of the terrarium air, causing condensation that drips onto plants and substrates. This is not the same process as advective fog immersion on tepui summits — which is driven by orographic lifting of moisture-laden air — but it produces a similar functional outcome: liquid water deposition on aerial plant surfaces during cool periods.
- **Seasonal variation**: As Colombian weather patterns shift through the year (the bimodal wet seasons centered on April–May and October–November), the terrarium conditions vary correspondingly, potentially providing phenological cues for flowering — though this remains to be formally tested.

### 4.3 Stochastic Weather Events

Rain events in the Colombian reference cities produce sudden setpoint changes in the terrarium — temperature drops of several degrees within an hour accompanied by humidity targets approaching saturation. While these perturbations differ mechanistically from tepui fog immersion (Section 2.2), they produce temperature and humidity excursions of similar magnitude and duration to those recorded during cloud immersion events in tropical montane environments (Jarvis & Mulligan 2011). Some experienced *Heliamphora* growers associate rapid temperature drops with improved vigor, though this has not been formally tested.

`[PLACEHOLDER — Grafana charts showing:]`
- `[Representative 7-day temperature and humidity trace with weather events visible]`
- `[24-hour diurnal cycle showing temperature swing and humidity pattern]`
- `[Seasonal comparison if data available (e.g., summer vs. winter)]`

### 4.4 Phenological Observations

`[PLACEHOLDER — any observed correlations between environmental conditions and plant phenology:]`
- `[Do Heliamphora flower more at certain times of year?]`
- `[Do Utricularia flowering events correlate with temperature drops or humidity spikes?]`
- `[Any observable growth rate changes with season?]`
- `[Pitcher production timing in Nepenthes — seasonal pattern?]`

---

## 5. Discussion

### 5.1 Weather-Mimicking vs. Fixed Setpoints for Carnivorous Plant Cultivation

The use of real-time weather data to drive terrarium setpoints represents a departure from conventional fixed-schedule environmental control. For carnivorous plants — especially tepui endemics adapted to dynamic, weather-driven environments — this approach offers several potential advantages:

**Naturalistic variability**: Fixed setpoints produce monotonous conditions that differ from the dynamic, weather-driven environments where these species evolved. Weather-referenced setpoints introduce stochastic variation within biologically safe bounds. Whether this variation provides phenological cues that fixed setpoints lack remains undemonstrated in this system, but the infrastructure for testing this hypothesis is in place. What is clear is that the plants have thrived under four years of continuous variation, suggesting at minimum that they tolerate — and may benefit from — conditions that change unpredictably within their natural climate envelope.

**Seasonal tracking**: The dynamic photoperiod (Section 2.3) and the seasonal variation in Colombian weather data provide longer-timescale variation that tracks the natural annual cycle at the tepui latitude. Whether this variation meaningfully affects *Heliamphora* flowering frequency or *Utricularia* growth patterns remains to be formally tested, but the infrastructure for such studies is in place through the system's comprehensive data logging.

**Revealing operational insights**: The weather-mimicking approach, with its continuous environmental variation and data logging, revealed the physical limit of evaporative cooling: when the terrarium temperature drops to approximately 16.6 deg C in the evening (a threshold determined by the room's temperature and humidity), ventilation fans cease to provide cooling and instead inject warm room air. This counterintuitive finding — that running fans at night can *warm* a terrarium — has practical implications for any grower using ventilation-based cooling (Section 5.3).

### 5.2 Climatic Overlap Across Distinct Highland Habitats

A central finding of this work is the successful co-cultivation of carnivorous plants from ecologically distinct tropical highland habitats in a single enclosure. The carnivorous taxa discussed here occupy very different niches in nature: *Heliamphora* and *Brocchinia reducta* grow on open, treeless tepui summits (Guiana Highlands, ~5 deg N, 1,500–2,800 m); highland *Nepenthes* grow as scrambling vines in upper montane mossy forests (Borneo-Sumatra, 0–6 deg N, 1,500–3,000 m); and *Utricularia* sect. *Orchidioides* are epiphytes of tepui cliff faces and cloud forest canopies (pan-tropical, 1,500–2,800 m). These habitats differ in vegetation structure, light regime, substrate, and species composition — a tepui summit meadow bears no ecological resemblance to a Bornean upper montane forest.

Nevertheless, the physical climate at these sites overlaps substantially. The saturated adiabatic lapse rate in the tropics is approximately 0.5–0.6 deg C per 100 m of elevation gain. At 2,000–2,800 m — the elevation band occupied by most of the species discussed here — this produces mean temperatures of 10–18 deg C regardless of longitude, because the dominant thermal forcing is altitude, not geography. Roraima's summit (2,810 m) records daytime temperatures of 15–21 deg C and nighttime lows of 5–13 deg C within *Heliamphora* populations (Adlassnig et al. 2010). Mount Kinabalu in Borneo (where *N. villosa* and *N. edwardsiana* grow at 2,400–3,200 m) shows comparable ranges. Cloud immersion frequencies of 50–80% of nighttime hours are typical of tropical montane cloud forests globally (Jarvis & Mulligan 2011), driving humidity regimes of 80–100% RH at these elevations. It is this climatic convergence — not ecological similarity — that permits co-cultivation. Species from separate evolutionary lineages and distinct habitat types have adapted to similar temperature and humidity ranges because these parameters are governed by altitude and the physics of saturated air masses rather than by the ecological community in which the species is embedded.

The remaining obstacle to co-cultivation is light. *Heliamphora* and *Brocchinia reducta*, adapted to fully exposed tepui summits where there is no tree canopy, require high irradiance. Highland *Nepenthes*, growing in the understory and margins of montane forests, require substantially less. In this system, the inverse square law from overhead LED sources provides a natural solution: light intensity falls off with the square of the distance from the source, creating a continuous gradient from high irradiance directly beneath the LEDs (upper zone, where tepui summit species are placed) to much lower irradiance at the terrarium floor (lower zone, where *Nepenthes* sit). A single lighting array thus accommodates the full range of light requirements without physical barriers or independently controlled fixtures, making the multi-habitat co-cultivation concept practically achievable.

The practical implication is that growers of highland carnivorous plants need not maintain separate terraria for tepui *Heliamphora*, Asian *Nepenthes*, and Neotropical *Utricularia*. A single enclosure tuned to the shared temperature and humidity requirements of tropical highland species, with a vertical light gradient, can accommodate all three along with companion orchids, ferns, and bromeliads from climatically compatible habitats.

### 5.3 Nighttime Cooling: Marine-Compressor Refrigeration and Fan-Mediated Humidity Control

The defining challenge of highland carnivorous plant cultivation — achieving meaningful nocturnal temperature drops in a domestic setting — has driven considerable innovation in the hobby. The chest freezer conversion (Shafer 2003), aquarium chillers with internal heat exchangers, modified portable air conditioners, and Peltier arrays have all been employed with varying success (see Introduction). The approach described here — marine refrigeration hardware with an internal evaporator plate — adds another option to this toolkit, with advantages in integration, efficiency, and long-term reliability for medium-to-large enclosures.

Continuous environmental data permit a quantitative attribution of the system's heat budget. An OLS regression of the 5-minute cabinet-temperature derivative on actuator state (freezer-on, lights-on, fan PWM) and the room–cabinet temperature gradient, fit to n = 17,773 observations over the 80.3-day Meross-instrumented window (2026-02-18 to 2026-05-10) with HC3 robust standard errors, attributes the temperature work as follows:

| Term | Coefficient | 95 % CI | p |
|---|---:|:---:|---:|
| Compressor (freezer active) | −1.01 °C/hr | [−1.05, −0.97] | <10⁻³⁰⁰ |
| Passive room↔cabinet exchange (per +1 K gradient) | +0.17 °C/hr | [+0.14, +0.19] | <10⁻⁴⁰ |
| LEDs (lights on) | −0.34 °C/hr | [−0.44, −0.25] | <10⁻¹¹ |
| Fan PWM (continuous, per PWM unit 0–255) | +0.0002 °C/hr | [−0.0002, +0.0005] | 0.33 |

The marine compressor performs essentially all of the active cooling work; the only steady opposing term is the passive room→cabinet heat exchange that compressor cycling must counter. The fan PWM coefficient, modelled at full resolution, is statistically indistinguishable from zero: fans do not measurably warm or cool the cabinet on the sensible-heat axis (n = 17,773, full structured output in `[ref to HardwareX]` §7.4).

Fans, then, are not part of the thermal control loop. Their role is humidity regulation, which is quantified causally by an instrumental-variables analysis. Across a randomised 9-week A/B fan-schedule experiment (December 2025 to February 2026), a 2SLS estimator using the schedule indicator as instrument recovers a structural fan→humidity coefficient of **−0.34 % RH per +10 PWM units** (95 % CI: −0.68 to −0.005; p = 0.047; n = 1,353 nighttime 5-minute observations; first-stage F = 22.5). The naive OLS estimate has the opposite sign (+0.15 % per +10 PWM) because the controller drives fan PWM in response to humidity; the OLS regression therefore captures the controller's reaction, not the fans' causal effect. The IV/2SLS estimator recovers the structural coefficient. Full method and replication script in the companion paper `[ref to HardwareX]` §7.2.

The architectural implication is that **compressor cycling and fan PWM should be treated as actuators on independent control loops** — compressor for temperature, fans for humidity. In this system, the controller modulates fan PWM continuously to hold cabinet humidity within the weather-derived target band (75–95 % RH), while the marine compressor cycles to track the temperature setpoint. The same separation is available to any grower running compressor-based cooling alongside ventilation, regardless of the specific cooling hardware: temperature is set by compressor cycling, humidity by fan PWM, and the two loops do not meaningfully interact on either physical axis.

### 5.4 Additional Practical Insights

**No dry rest periods**: The persistent high humidity required by *Heliamphora* and *Utricularia* precludes dry rest periods. Dry-rest-demanding species — most of the *Cattleya* alliance with strong dry-rest cues, and many *Dendrobium* section *Callista* — were excluded from the cabinet pre-emptively rather than tested-and-lost, because the cabinet's continuous high humidity is fundamentally incompatible with their flowering cycle. The losses that did occur within the introduced cohort over four years reflect a heterogeneous set of cultivation incompatibilities (warm-growing species too cool, sun-loving species too shaded, *Sophronitis pygmaea* humidity sensitivity, *Genlisea* tropical-lowland species too cool, occasional CITES-import customs failure for *Laelia briegeri*) rather than a single thematic cause. Climate-envelope compatibility is therefore best read as a pre-condition for inclusion in the cohort, not as a post-hoc explanation of survival rates within it.

**Silent airflow failures are dangerous.** A loose crimp on the power cable of one of the three fans on the evaporator-coil array let it stop without alarming. The remaining two fans kept the cabinet on temperature, so no thermal alarm fired, but the back-left corner stopped getting airflow. Black saprophytic mould slowly accumulated on the insulation panel through Q1 2026, and was eventually noticed because what initially looked like *Botrytis* on a *Dracula pholeodytes* bud turned out to be a saprophyte living off stagnant condensate. The cleanup episode itself was carried out on 2026-05-01: full evacuation of the cabinet, Physan-20 cleaning of all surfaces (10 mL per 5 L water), repair of the failed fan connection, and a careful re-install, after which conditions returned to normal within 24 h. The episode emphasised two things: redundancy in fan arrays masks individual failures, and the safety chain should track per-channel airflow not just aggregate temperature.

`[PLACEHOLDER — other cultivation insights gained over four years:]`
- `[Water quality observations — RO or tap, conductivity targets]`
- `[Pest management in the enclosed system — pests observed and treatments used]`
- `[Sphagnum replacement frequency by zone]`
- `[Seasonal challenges — Mediterranean summer heat strategies]`

### 5.5 Limitations

- **Single sensor**: Environmental data comes from one sensor positioned at mid-canopy height. Temperature stratification within the enclosure is certain — the upper zone near the LEDs (where *Heliamphora* grow) is warmer than the lower zone, and microclimate at the evaporator plate surface differs from mid-air conditions. The reported temperatures should be understood as representative of mid-canopy conditions, not of the full range experienced by individual plants.
- **No formal growth metrics**: While we report general cultivation success over four years, systematic measurements of pitcher production rates, division frequency, or biomass accumulation have not been conducted. Claims of "successful cultivation" are based on sustained growth, division, and the absence of decline rather than on quantitative comparison with other growers' results or with wild growth rates.
- **Not cold enough for ultra-highland species**: The system's minimum temperature of 13.5 deg C, while sufficient for mid-elevation species, falls short of the sub-10 deg C nighttime temperatures recorded on higher tepui summits (>2,500 m) and the near-freezing conditions experienced by ultra-highland *Nepenthes* such as *N. villosa* and *N. lamii*. A chest freezer conversion (Shafer 2003) remains more appropriate for growers targeting these extreme species.
- **Light-heat tradeoff**: Every watt of LED output becomes a watt of heat load inside the enclosure. At 400 W nameplate (reduced to ~96–144 W effective output by the two-stage dimming system), the lighting contributes a substantial fraction of the cooling load that the compressor must remove. This tradeoff limits the achievable combination of high light intensity and low temperature — a constraint relevant to all enclosed cultivation systems.
- **Mediterranean summer challenge**: During the hottest summer weeks (room temperatures reaching 27–28 deg C), the compressor runs continuously and nighttime temperatures may not drop below 16–17 deg C. The terrarium's placement in a room without direct sunlight mitigates but does not eliminate this limitation.
- **Heat-balance scope**: The heat-balance regression (Section 5.3) attributes cabinet-temperature variance to the marine compressor, lights, and the room-to-cabinet gradient with statistical robustness over 80.3 days at 5-minute cadence (n = 17,773). Fan PWM is the high-resolution humidity actuator and its effect on cabinet temperature is statistically indistinguishable from zero in this dataset; whether the same decoupling holds at fan-PWM levels above the routine operating range (≤ 200 PWM in this system) has not been tested.

---

## 6. Conclusions

The weather-mimicking approach is viable for long-term cultivation of highland carnivorous plants, with *Heliamphora*, highland *Nepenthes*, *Utricularia* sect. *Orchidioides*, and *Brocchinia reducta* maintained successfully for over four years under continuously varying conditions derived from real-time Colombian highland weather data.

Marine compressor refrigeration — using hardware designed for boat refrigeration — provides an effective and reliable cooling method for medium-to-large highland terraria, complementing the existing toolkit of chest freezer conversions (Shafer 2003), aquarium chillers, and modified air conditioners. The system routinely cools the terrarium to 13.5 deg C in a room at 22 deg C, with four years of continuous operation confirming long-term reliability. The most broadly applicable architectural finding is that compressor cycling and fan PWM should be treated as independent actuators on independent control loops: the compressor as the temperature actuator (−1.01 °C/hr when active in this system) and fan PWM as the humidity actuator (causal effect of −0.34 % RH per +10 PWM units, IV/2SLS, n = 1,353). This decoupling generalises across cooling hardware — chest freezers, aquarium chillers, air conditioners, or marine compressors all admit the same separation — and is implemented here through a multi-layer safety architecture whose evolution over the four-year operating period is documented in the companion paper `[ref to HardwareX]`.

The co-cultivation of carnivorous plants from ecologically distinct tropical highland habitats — tepui summit endemics (*Heliamphora*, *Brocchinia reducta*), upper montane forest species (highland *Nepenthes*), and cloud forest epiphytes (*Utricularia* sect. *Orchidioides*) — in a single enclosure is validated by four years of successful growth. These taxa occupy different ecological niches in nature, but their climatic tolerances overlap because tropical highland environments worldwide share similar temperature and humidity regimes at comparable elevations.

The full control system is open-source and described in a companion paper `[ref to HardwareX]`, enabling other growers and institutions to replicate or adapt the approach. A companion paper `[ref to AOS]` describes the orchid cultivation results from the same system.

---

## Acknowledgments

`[PLACEHOLDER — acknowledgments text]`

Portions of this manuscript were prepared with the assistance of an AI language model (Anthropic Claude). The system design, data collection, analysis, and all horticultural decisions are entirely the work of the authors.

---

## References

Adlassnig, W., Pranjić, K., Mayer, E., Steinhauser, G., Hejjas, F. & Lichtscheidl, I.K. 2010. The abiotic environment of *Heliamphora nutans* (Sarraceniaceae): pedological and microclimatic observations on Roraima Tepui. *Brazilian Archives of Biology and Technology* 53(2): 425–430.

Berry, P.E. & Riina, R. 2005. Insights into the diversity of the Pantepui flora and the biogeographic complexity of the Guayana Shield. *Biologiske Skrifter* 55: 145–167.

Clarke, C. 1997. *Nepenthes of Borneo.* Natural History Publications, Kota Kinabalu.

Clarke, C. 2001. *Nepenthes of Sumatra and Peninsular Malaysia.* Natural History Publications, Kota Kinabalu.

Jarvis, A. & Mulligan, M. 2011. The climate of cloud forests. In Bruijnzeel, L.A., Scatena, F.N. & Hamilton, L.S. (eds.), *Tropical Montane Cloud Forests: Science for Conservation and Management.* Cambridge University Press. pp. 39–56.

McPherson, S. 2007. *Pitcher Plants of the Americas.* The McDonald & Woodward Publishing Company.

Rull, V. & Vegas-Vilarrúbia, T. 2006. Unexpected biodiversity loss under global warming in the neotropical Guayana Highlands: a preliminary appraisal. *Global Change Biology* 12: 1–6.

Rull, V., Montoya, E., Nogué, S., Safont, E. & Vegas-Vilarrúbia, T. 2019. Climatic and ecological history of Pantepui and surrounding areas. In Rull, V. & Vegas-Vilarrúbia, T. (eds.), *Biodiversity of Pantepui: The Pristine "Lost World" of the Neotropical Guiana Highlands.* Academic Press. pp. 37–57.

Shafer, J. 2003. A novel method for the cultivation of *Nepenthes villosa*. *Carnivorous Plant Newsletter* 32(1): 20–23.

Taylor, P. 1999. Lentibulariaceae. In Steyermark, J.A., Berry, P.E., Yatskievych, K. & Holst, B.K. (eds.), *Flora of the Venezuelan Guayana,* Vol. 5: Eriocaulaceae–Lentibulariaceae. Missouri Botanical Garden Press. pp. 782–803.

cexx.org. 2011. Peltier element efficiency. https://www.cexx.org/peltier.htm (accessed February 2026).

`[PLACEHOLDER — add remaining references:]`
- `[Fleischmann, A. on Utricularia sect. Orchidioides revision]`
- `[Givnish, T.J. et al. 2014. Adaptive radiation, correlated and contingent evolution, and net species diversification in Bromeliaceae.]`
- `[Ref to HardwareX companion paper]`
- `[Ref to AOS companion paper]`
