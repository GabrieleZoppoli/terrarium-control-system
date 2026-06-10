# Weather-Mimicking Terrarium Cultivation of Highland Carnivorous Plants: Four Years of *Heliamphora*, *Nepenthes*, and *Utricularia* sect. *Orchidioides*

**Authors**: Gabriele Zoppoli — Department of Internal Medicine and Medical Specialties (DiMI), University of Genoa, Genoa, Italy; IRCCS Ospedale Policlinico San Martino, Genoa, Italy

**Corresponding author**: gabriele.zoppoli@unige.it

---

## Abstract

We describe the cultivation of highland carnivorous plants in a weather-mimicking terrarium over four years (May 2022 to present). The system, housed in a ~1 m³ (1.5 × 0.6 × 1.1 m) insulated acrylic enclosure in Genoa, Italy, uses a marine compressor unit (Vitrifrigo ND50) with an internal evaporator plate to reach nighttime temperatures as low as 13.5 °C in a room at 22 °C — about 3 °C below the evaporative-cooling floor of a misting-and-fans system. Rather than fixed setpoints, it ingests real-time weather from four Colombian highland cities (Chinchiná, Medellín, Bogotá, Sonsón; 1,300–2,640 m) and time-shifts them to phase-align the cabinet's daily cycle with Italian local time, preserving the stochastic, weather-driven variability of the source; a dynamic photoperiod from the Colombian reference latitude (~5° N) provides naturalistic day length. Under these conditions, nine living *Heliamphora* accessions (Guiana Highlands tepui endemics), nine highland *Nepenthes* (Sumatra, Sulawesi, and the Philippines — no Bornean accession), one *Utricularia* of section *Orchidioides* (*U. quelchii*, Ilu Tepui provenance), and one *Brocchinia reducta* (Guiana Shield carnivorous bromeliad) are maintained alongside companion orchids, ferns, and bromeliads — 75 living accessions across 31 plant genera in total. Although these carnivorous taxa occupy ecologically distinct habitats — open, treeless tepui (Pantepui) summits, Southeast Asian montane forest, and tepui cliff faces — their temperature and humidity tolerances overlap sufficiently to permit co-cultivation in one enclosure, with their differing light requirements met by the vertical irradiance gradient from overhead LEDs. The first inflorescence of *U. quelchii*, after three years of purely vegetative growth, was recorded in April–May 2026, with two flowers fully open by Day 21. The full control-system design, energy budget (~2.63 kWh/day), and eleven-layer safety architecture are given in a companion engineering paper [companion HardwareX paper] and on the project website (https://highlandcloudforest.com).

---

## 1. Introduction

Highland carnivorous plants — *Heliamphora* from the Venezuelan tepuis, highland *Nepenthes* from the upper montane mossy forests of Sumatra, Sulawesi, and the Philippines, epiphytic *Utricularia* of section *Orchidioides*, and the carnivorous bromeliad *Brocchinia reducta* — are among the most challenging plants in cultivation. These taxa occupy ecologically distinct habitats across the tropics. *Heliamphora* and *Brocchinia reducta* are species of the Guiana Shield, with *Heliamphora* endemic to the tepui table-top mountains and *B. reducta* ranging across the broader shield from Venezuela (Bolívar) to Guyana and northern Brazil (Roraima) per POWO; both grow in open, fog-immersed summit meadows and peat bogs at 1,500–3,000 m — exposed, treeless Pantepui environments, distinct from the forested tropical montane cloud forest (TMCF) *sensu* Hamilton, Juvik & Scatena (1995), although the climate envelopes overlap within bounds (Rull & Vegas-Vilarrubia 2006; Berry & Riina 2005). Highland *Nepenthes* inhabit upper montane mossy forests at similar elevations (1,500–3,000 m), growing as scrambling vines in the forest understory and canopy margins; the cabinet population sampled here is centred on Sumatra (*aristolochioides*, *inermis*, *jamban*, *tenuis*), Sulawesi (*pitopangii*, *glabrata*), and the Philippines (*argentii*, *micramphora*), with no Bornean accession in the cabinet (the most familiar Bornean species — *N. villosa*, *N. lowii*, *N. edwardsiana*, *N. rajah* — are noted here only for biogeographic completeness; cultivation results for them in this system are not reported). *Utricularia* of section *Orchidioides* are Neotropical epiphytes and lithophytes of tepui cliff faces and cloud-forest canopies; the cabinet maintains a single section-*Orchidioides* representative, *U. quelchii* of Ilu Tepui provenance (first flowering recorded April–May 2026; see §3.3).

Despite these ecological differences, the climatic tolerances of these species overlap substantially. Cool temperatures (10–22 °C), persistent high humidity (80–100% RH), and frequent fog or cloud contact are common to tepui summits, Southeast Asian upper montane forests, and Neotropical cloud forest canopies alike — a consequence of the physical constraints of tropical mountain meteorology, which produces broadly similar temperature and humidity regimes at comparable elevations regardless of longitude. At higher elevations, particularly on tepui summits above 2,500 m, nighttime temperatures can drop below 5 °C and occasionally approach freezing. This climatic overlap is what makes co-cultivation possible: the habitats are different, but the key environmental parameters — temperature range, humidity, and fog exposure — are shared. A remaining challenge is accommodating their different light requirements: *Heliamphora* and *Brocchinia* grow fully exposed on treeless tepui summits, while *Nepenthes* grow in the shade of montane forest. In this system, the inverse square law from overhead LED sources creates a natural light gradient within the terrarium — strong irradiance near the top, substantially lower at the bottom — allowing high-light tepui species and shade-adapted montane forest species to coexist in a single enclosure without separate lighting zones.

The central challenge in cultivating these species is not maintaining high humidity in a sealed enclosure — that is straightforward — but achieving meaningful nighttime temperature drops. In a room at 22 °C, the terrarium must be actively cooled by 4–8 °C every night, year-round, to simulate the nocturnal conditions of tropical highlands. The hobby has developed several approaches to this problem, each with characteristic limitations.

Evaporative cooling — using misting and ventilation fans to cool by evaporation — is the most accessible method. However, it has a hard thermodynamic limit: evaporation can only cool the air down to the wet-bulb temperature, a value determined by the room's temperature and humidity. In a typical room at 22 °C and 58% relative humidity, this floor is approximately 16.6 °C. Below that point, ventilation fans no longer extract heat by evaporation; their role shifts entirely to humidity regulation (see Section 5.3 for the causal quantification of fan-to-humidity coupling in this system). This means evaporative methods alone cannot reach the 10–15 °C nighttime temperatures characteristic of the mid-to-high-elevation habitats where these species originate.

Thermoelectric (Peltier) modules are attractive for their simplicity and silent operation, but their coefficient of performance (COP) is approximately 0.2 — roughly one-tenth that of a vapor-compression system — meaning they draw 5 W of electricity for every 1 W of heat removed. In practice, a single 36 W module achieves only 2–4 °C of cooling in a 20-liter volume (cexx.org 2011), and scaling to larger enclosures requires arrays of modules with correspondingly large heat sinks and power supplies.

The chest freezer conversion, first described in this journal by Shafer (2003), provides effective compressor cooling by using the freezer itself as the growing enclosure with a plexiglas lid replacing the original top. This method can reach temperatures below 5 °C — cold enough for ultra-highland species — and has become a standard approach for growers of demanding *Heliamphora* and *Nepenthes*. Its limitations are primarily spatial: growing space is constrained by the freezer's dimensions, the compressor is not designed for the thermal load of an open-topped enclosure, and the aesthetic result is a chest freezer in the living room. Aquarium chillers circulating cold water through radiators or coiled tubing inside a terrarium offer more flexibility, but their cooling capacity is often marginal — they are designed for small water-temperature differentials, not sustained 8–10 °C air-temperature drops — and they introduce condensation problems on the cold heat-exchanger surfaces. Modified portable air conditioners with external thermostats (e.g., CoolBot) provide adequate cooling power and have been used successfully for large enclosures and greenhouses, though their integration with sealed, high-humidity terraria requires careful management of the evaporator's dehumidifying effect.

The approach described here adds a further option to this toolkit: marine refrigeration hardware — a Vitrifrigo ND50 compressor unit with a Danfoss variable-speed compressor and a stainless-steel evaporator plate mounted inside the terrarium. The unit ships as a complete factory-sealed split system (compressor, condenser, pre-charged refrigerant lines, evaporator plate) sized for boat refrigerators, so installation is mechanical rather than refrigeration work and requires no F-gas certification, no field plumbing, and no system charging — removing a skills barrier that has historically confined DIY compressor cooling to chest-freezer conversions. The large evaporator plate (1220 × 280 mm) doubles as a condensation surface and provides gentle, distributed cooling rather than the point-source cold spots of coiled tubing or radiators. The system routinely drives the terrarium to 13.5 °C — approximately 3 °C below the evaporative cooling floor and nearly 9 °C below room ambient — while operating quietly and at modest power. The full mechanical and electronic design, parts list, and energy budget are given in the companion engineering paper [companion HardwareX paper] and on the project website (https://highlandcloudforest.com); here we treat the cooling hardware only as far as the cultivation results require.

Beyond the cooling challenge, traditional terrarium approaches rely on fixed environmental setpoints (e.g., 18 °C day / 14 °C night at 90% RH), which maintain plants alive but fail to capture the stochastic variability of real tropical highland weather: sudden temperature drops during rain events, diurnal fog cycles, seasonal shifts in cloud cover, and the dynamic interplay of temperature and humidity that characterizes tropical montane climates.

This paper describes the horticultural results of cultivating *Heliamphora*, *Nepenthes*, *Utricularia* sect. *Orchidioides*, *Brocchinia reducta*, and other carnivorous taxa in a terrarium that uses real-time weather data to drive its environmental setpoints. Rather than fixed schedules, the system ingests current meteorological conditions from four Colombian highland cities (Chinchiná, Medellín, Bogotá, Sonsón; 1,300–2,640 m elevation) and time-shifts them to generate naturalistic, continuously varying conditions within the terrarium. The full technical description of the control system is presented in a companion engineering paper `[companion HardwareX paper]` and on the project website (https://highlandcloudforest.com); here we focus on the cultivation approach and plant responses.

A key conceptual framework for this work is the observation that tropical highland habitats — whether open tepui summits, Andean cloud forests, upper montane forests of Sumatra and the Philippines, or the highlands of Papua New Guinea — share broadly overlapping climatic envelopes despite their geographic isolation and ecological differences. This climatic overlap means that a single terrarium tuned to their common temperature and humidity requirements can support species from multiple continents and habitat types simultaneously, rather than requiring separate enclosures for each biogeographic region. The cabinet holds 75 living accessions across 31 plant genera; the carnivorous taxa discussed here share the terrarium with companion orchids, ferns, and bromeliads from these climatically compatible tropical highland habitats — all maintained under identical conditions.

---

## 2. Materials and Methods

### 2.1 Terrarium Overview

The terrarium measures ~1 m³ (1.5 × 0.6 × 1.1 m) (external dimensions), constructed from laser-cut acrylic (PMMA) panels solvent-welded with dichloromethane and sealed with crystalline silicone. The enclosure is externally insulated with 1 cm extruded polystyrene laminated with diamond Mylar reflective sheeting. Access is via two sliding front panels.

A mid-height perforated acrylic shelf divides the enclosure into three climatic zones:

1. **Upper zone** (above shelf, highest light): *Heliamphora* species, *Brocchinia reducta*, and high-light miniatures
2. **Middle zone** (shelf level, intermediate light): *Utricularia* sect. *Orchidioides* (kokedama-style), intermediate-light orchids
3. **Lower zone** (below shelf, lowest light, coolest): Highland *Nepenthes*, shade-adapted orchids, ferns

The vertical light gradient created by the inverse square law from overhead LED sources is exploited as a design feature: high-light species (*Heliamphora*, which grow fully exposed on tepui summits) occupy the upper zone, while shade-adapted species are placed progressively lower. A single lighting system thus approximates the distinct light environments these species occupy in nature.

Hardware components include four ChilLED Logic Puck V3 LED modules (100 W each, Samsung LM301B diodes), a Vitrifrigo ND50 compressor with internal evaporator plate for cooling, a MistKing diaphragm-pump misting system, four groups of fans, and a Sensirion SHT35 sensor for temperature and humidity monitoring. Full hardware and software details, the parts list, and the control firmware are described in the companion engineering paper `[companion HardwareX paper]` and published open-source on the project website (https://highlandcloudforest.com).

### 2.2 Climate Simulation

The system queries the OpenWeatherMap API for current weather conditions at four Colombian highland cities:

| City | Elevation | Role |
|------|-----------|------|
| Chinchiná | ~1,300 m | Warm reference |
| Medellín | ~1,500 m | Mid-elevation reference |
| Sonsón | ~2,475 m | Cool reference |
| Bogotá | ~2,640 m | Cool/high reference |

Temperature and humidity values are averaged across all four cities and clamped to safe operating ranges (12–24 °C, 75–95 % RH; the humidity floor was raised from 70 % to 75 % on 2026-04-30 to better match Pantepui *Heliamphora* and *Utricularia* preferences). The data are time-shifted so that the cabinet's daily cycle phase-aligns with Italian local time rather than Colombian: warm, slightly drier conditions arrive in the Italian afternoon and cool, near-saturated conditions arrive overnight. The result is a continuously varying, weather-driven setpoint profile rather than a fixed schedule. The mechanics of the time-shift and the internet-loss fallback (a smoothed 14-day historical curve) are detailed in the companion engineering paper.

The choice of Colombian highland cities was driven by the unavailability of real-time tepui weather station data when the project began. These cities were selected because their elevation range (1,300–2,640 m) and near-equatorial latitude (~5° N) produce temperature and humidity profiles comparable to those reported for tepui summits, upper montane forests, and other tropical highland habitats where the cultivated species originate — and, lying in the same hemisphere and latitude band as the Venezuelan tepuis (5–6° N), their seasonal photoperiod variation matches the natural photoperiod of the target taxa.

The stochastic character of real weather data is a key advantage over fixed schedules. Rain events in the Colombian reference cities produce sudden setpoint changes in the terrarium — temperature drops of several degrees within an hour accompanied by humidity targets approaching saturation. These perturbations are not programmed; they emerge from the weather data feed and vary from day to day. While they are not direct simulations of tepui fog immersion (which is driven by orographic lifting and trade-wind convergence rather than by convective rainfall), they introduce the kind of unpredictable environmental variation that fixed schedules cannot provide, and they produce temperature and humidity excursions within the same range that tepui-summit weather stations record during cloud immersion events (Adlassnig et al. 2010).

### 2.3 Light Regime

A dynamic photoperiod is computed daily from the near-equatorial latitude of the Colombian reference (~5° N). At this latitude the natural annual day-length variation is small (~34 minutes between solstices), characteristic of equatorial highlands where "winter comes every night and summer every day" — the diurnal temperature range (10–12 °C) exceeds the annual variation in monthly means (2–3 °C). The computed day length is clamped to a 10–14 hour range, a margin that also suits companion species from higher latitudes (e.g., Brazilian *Sophronitis* at ~22° S). The lit period is centred on 13:15 local time.

Light intensity follows a raised-cosine curve through the photoperiod, with a soft dawn ramp and peak intensity centred on solar noon — closer to a Pantepui-summit midday profile than a flat on/off schedule. The intensity is held well below the LEDs' rated capacity by a two-stage dimming arrangement (a hardware ceiling plus a software ramp); the electronics of this are described in the companion engineering paper. The high irradiance directly beneath the LED array, falling off with the inverse square of distance, is exploited as a design feature (§2.1, §5.2).

### 2.4 Substrate and Mounting

**Heliamphora and Brocchinia reducta**: Grown in the upper zone in a substrate of akadama (Japanese fired clay granules) mixed with long-fiber sphagnum, topped with a layer of living *Sphagnum* moss. The akadama provides drainage and structural stability while the living sphagnum maintains surface moisture and creates the acidic, low-nutrient conditions these plants require. This combination approximates the free-draining, waterlogged-surface conditions of tepui summit peat bogs. Pots are positioned directly beneath the LED pucks for maximum light.

**Utricularia sect. Orchidioides** (*U. quelchii*, Ilu Tepui provenance — the only section *Orchidioides* representative currently in the cabinet; *U. alpina* lives elsewhere in the broader collection on a separate shelf, not in this terrarium): Grown kokedama-style — wrapped in a ball of living *Sphagnum* moss, hung from the back wall at mid-height where humidity remains consistently above 85 % under direct misting. The kokedama form provides the aerial, moisture-saturated root environment these species inhabit on tepui cliff faces, while allowing stolons to trail freely.

**Highland Nepenthes**: Planted in kanuma (Japanese volcanic pumice) mixed with long-fiber sphagnum and placed directly on the terrarium floor in the lower zone, without saucers. The kanuma provides excellent drainage and aeration while the sphagnum retains moisture around the roots. The absence of saucers prevents waterlogging — the terrarium's persistently high ambient humidity (82–95% RH) eliminates the need for supplementary moisture trays that highland *Nepenthes* growers typically rely on. The lower zone provides the coolest temperatures, benefiting these species.

`[PHOTO NEEDED: substrate-preparation / mounting sequence for each group — akadama+sphagnum repotting (Heliamphora/Brocchinia), kokedama wrapping (U. quelchii), and kanuma potting (Nepenthes). No substrate-prep frames currently exist in the website asset library; these would need to be shot. In-situ established-plant frames do exist (see §3 photo shortlists below) and can substitute if a process sequence is not feasible.]`

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

`[AUTHOR TO PROVIDE: first-hand cultivation observations per species or group — these are the author's own records and must not be inferred. Suggested fields: pitcher production cadence (new pitchers per growth point per month or per season during the active growing phase); division/offset frequency; any flowering events with month and whether seed set was achieved; anthocyanin/coloration changes correlated with light or temperature; observed size progression from acquisition to current state. Once provided, this can be stitched into a paragraph-per-species.]`

**Photos (existing assets, ranked).** Close-ups exist for 6 of the 9 accessions on the website asset library (`static/img/collection/heliamphora/`):
- Rank 1 (strongest-performer pitcher detail): `heliamphora-ionasi-elegance.jpg` (plus `-2`, `-3`) or `heliamphora-godzilla.jpg` (plus `-2`).
- Rank 2 (coloration interest): `heliamphora-minor-burgundy-black.jpg`; `heliamphora-minor-var-pilosa-auyan-clone-3.jpg` (plus `-2`..`-4`).
- Rank 3 (provenance series): `heliamphora-macdonaldae-cerro-duida-isc.jpg` (plus `-2`..`-6`); `heliamphora-purpurascens-x-ionasii-red-giant.jpg` (plus `-2`, `-3`).
- Upper-zone wide shot: use a highland-interior frame, e.g. `static/img/highland/interior/interior_2025-02-15_IMG_0391.jpg`.
- `[PHOTO NEEDED: *H. pulchella* (Akopan Tepui), *H. pulchella* (Amuri Tepui), and *H. minor* Clone 4 — 3 of the 9 accessions have no close-up asset.]`

**Losses.** None. A filter of `collection.csv` on `genus=Heliamphora AND location=highland` returns zero `lost` or `given` rows: all nine *Heliamphora* accessions acquired since 2016 remain alive in the cabinet.

### 3.2 Highland *Nepenthes*

Nine living accessions in the cabinet (with one ID-uncertain horticultural specimen), grouped here by region of origin. None are Bornean (the most famous highland Bornean species — *N. villosa*, *N. lowii*, *N. edwardsiana*, *N. rajah* — are absent from the present cabinet; the species below cover Sumatra, Sulawesi, and the Philippines).

**Sumatra (4):** *N. aristolochioides* (Sumatra, Clone NM03; alive since January 2023), *N. inermis* (Gunung Gadut, alive since March 2016 — the longest-tenured *Nepenthes* in the cabinet), *N. tenuis* 'Reddish Leaves' (West Sumatra, alive since May 2016), *N. jamban* (alive since November 2025).

**Sulawesi (2):** *N. pitopangii* 'Ivory Coloured Form' Clone 01 (alive since March 2024), *N. glabrata*.

**Philippines (2):** *N. argentii* (Mt. Guiting-Guiting, Sibuyan, alive since June 2023), *N. micramphora* (Mindanao, alive since June 2023).

**Horticultural label, identity uncertain (1):** *N.* 'Fake Pitopangii' — originally sold as *N. pitopangii* 'Ivory Coloured Form' but with morphology that does not match the species; retained in the cabinet because its cultural requirements have proven compatible with the cohort, but its taxonomic status is treated as horticultural-label-only.

Cultivation uniform across the cohort: 4–6 inch perforated terracotta or net pots in a kanuma/perlite/sphagnum mix (approximately 2:1:1 by volume), topped with living *Sphagnum*. Plants grow either as rosettes on the cabinet floor or, in the case of climbing forms, with the leading stem trained up to mid-height; mature stems develop both lower and upper pitchers. No saucers; the cabinet's misting + condensate cycle maintains substrate moisture without standing water in the pots. Free draining at the bottom of the cabinet feeds the condensate reservoir.

`[AUTHOR TO PROVIDE: pitcher-production observations across the cohort — cadence, whether both upper and lower pitchers develop on the climbing forms, and any extended dormancies. The prior draft asserted "steady pitcher production with no extended dormancies"; this is a first-hand cultivation claim and should be confirmed or restated by the author rather than assumed.]`

**Photos (existing assets, ranked).** Close-ups exist for 6 of the 9 accessions on the website asset library (`static/img/collection/nepenthes/`):
- Rank 1 (signature shot): `nepenthes-aristolochioides-sumatra-clonenm03.jpg` (plus `-2`..`-4`) — the fenestrated/"windowed" upper pitcher.
- Rank 2 (recently-described form): `nepenthes-jamban.jpg` — toilet-bowl pitcher of *N. jamban*.
- Rank 3 (Sulawesi/Philippine representatives): `nepenthes-glabrata.jpg` (plus `-2`..`-5`); `nepenthes-tenuis-reddish-leaves-west-sumatra.jpg` (plus `-2`..`-4`); `nepenthes-pitopangii-ivory-colored-form-clone01.jpg`; `nepenthes-argentii.jpg`.
- Cabinet-floor wide shot: use a highland-interior frame (`static/img/highland/interior/`).
- `[PHOTO NEEDED: *N. inermis*, *N.* 'Fake Pitopangii', and *N. micramphora* — 3 of the 9 accessions have no close-up asset.]`

**Losses.** None within the highland cohort. The only non-alive *Nepenthes* in the ledger is *N. ampullaria* 'Lime Twist' (acquired February 2017, given away 2017) — a lowland species that was never part of the highland cabinet cohort and is not a cabinet failure. All nine highland accessions remain alive.

### 3.3 *Utricularia* sect. *Orchidioides*

**Cabinet contents: one accession, *Utricularia quelchii* (Ilu Tepui provenance)** — acquired early 2023 from Carnivors & More (C. & C. Klein) and grown kokedama-style in a 10 cm perforated terracotta, hung on the back wall at mid-height under direct misting. Substrate: live *Sphagnum* only. Foliar feed: Akerne Orchid Mix at half a teaspoon per three litres, two applications per month.

Three years of pure vegetative growth (steady leaf addition, no inflorescences) preceded the first flowering, recorded as follows:

- **20 April 2026** — First inflorescence observed: an erect, red-purple peduncle bearing two buds, emerging from the *driest* portion of the kokedama (the ~2 cm of moss against the cabinet wall, not the wetter pot interior). The location is suggestive: continuous saturation may not be the floral cue.
- **7 May 2026** — Day 17. The larger of the two buds opened, displaying the full section *Orchidioides* gestalt: hooded magenta galea, yellow-cream throat with two red callus blotches, and a broad pink lower lip.
- **11 May 2026** — Day 21. The second bud opened. Both flowers held on the same scape; colour was uniform across both (no shift toward the deeper red of the Roraima phenotype documented by Taylor 1989, consistent with the Ilu Tepui clonal origin).

Flowers persisted into senescence over the following weeks (observation ongoing at time of writing). Across its cabinet residence (acquired February 2023; ~3 years), the plant progressed from three or four leaves to a fully established rosette occupying the entire pot, with stolons trailing through the surrounding *Sophronitis* aerial roots above. No prior flowering attempt was observed during the vegetative period. These dates, the bloom sequence, and the accompanying photographs are documented in the project's website blog post (Zoppoli 2026, "First bloom: *Utricularia quelchii*, three years in," https://highlandcloudforest.com).

This is the first record of *U. quelchii* flowering in this terrarium and adds to the small body of cultivation records for the species outside its native range. *U. alpina* (held elsewhere in the broader collection, *not* in this cabinet) and other *Utricularia* outside section *Orchidioides* are not included in this report.

**Photos (existing assets, ranked).** All bloom-sequence frames exist on the website (`static/img/collection/utricularia/`):
- Rank 1 (suggested cover candidate — both flowers open at Day 21): `utricularia-quelchii-14.jpg`.
- Rank 2 (single open flower, peak saturation): `utricularia-quelchii-7.jpg`; three-quarters view with the second bud still closed: `utricularia-quelchii-9.jpg`.
- Rank 3 (pre-flowering / bud stage, 20 April): `utricularia-quelchii.jpg` (the first-catch two-bud frame), `utricularia-quelchii-2.jpg`, `utricularia-quelchii-3.jpg`.
- In-situ context (kokedama on the cabinet wall below the *Sophronitis*): `static/img/highland/interior/interior_2026-04-20_coccinea-bloom.jpg`.
- A clean triptych of `-7` (opening), `-9` (three-quarters), and `-14` (both open) is recommended.

### 3.4 *Brocchinia reducta* and Other Carnivorous Taxa

*Brocchinia reducta* is cultivated in the upper zone alongside *Heliamphora*, in the same akadama/sphagnum substrate topped with living *Sphagnum*. As a Guiana Shield species (POWO: native range Venezuela [Bolívar] to Guyana and Brazil [Roraima], in the wet tropical biome — broader than the "tepui summit endemic" sometimes attributed to it), it thrives under the high irradiance of the upper zone and the same temperature and humidity regime as the *Heliamphora*.

`[AUTHOR TO PROVIDE: first-hand observations on *Brocchinia reducta* — growth rate and rosette size since acquisition; tank-fluid behaviour and any observed prey capture; offset/pup production. These are the author's own records.]`

**Photo (existing asset).** One frame exists: `static/img/collection/brocchinia/brocchinia-reducta.jpg`. `[PHOTO NEEDED: a rosette top-down showing the reflective, water-filled tank — the diagnostic carnivorous feature — if not captured in the existing frame.]`

**Other carnivorous taxa in the cabinet.** A filter of `collection.csv` on `location=highland AND status=alive` returns no other carnivorous genera in the cabinet beyond *Heliamphora*, *Nepenthes*, *Utricularia* (sect. *Orchidioides*: *U. quelchii*), and *Brocchinia*. The collection's other carnivores (numerous *Drosera*, *Dionaea*, *Sarracenia*, *Pinguicula*, *Cephalotus*, *Genlisea*; a historical *Catopsis berteroniana*, now lost) are grown outdoors or on separate shelves, outside this terrarium, and are therefore outside the scope of this paper. `[AUTHOR TO CONFIRM: whether any carnivorous taxon not captured by the highland filter should nonetheless be reported as a cabinet resident.]`

---

## 4. Environmental Results

### 4.1 Temperature and Humidity

Over the monitoring period (four years), the terrarium maintained the following conditions:

| Parameter | Minimum | Maximum | Typical range | Target range |
|---|---|---|---|---|
| Temperature | 13.5 °C | 24.3 °C | 15–22 °C | Weather-derived (clamped 12–24 °C) |
| Relative humidity | 75 % | 98 % | 83–95 % | Weather-derived (clamped 75–95 % since 2026-04-30) |
| VPD | 0.03 kPa | 0.64 kPa | 0.08–0.45 kPa | < 0.8 kPa |

The system achieves a 4–8 °C diurnal temperature swing, with nighttime temperatures routinely dropping to 14–16 °C through active compressor cooling and daytime temperatures rising to 18–22 °C. This approximates the diurnal range at 2,000–2,800 m in the tropical highlands where the cultivated species originate.

VPD values below 0.4 kPa, corresponding to near-saturation conditions, are maintained for the majority of the 24-hour cycle. This is critical for *Heliamphora* pitcher health (preventing desiccation of pitcher fluid and nectar spoons) and for the delicate stolons of epiphytic *Utricularia*.

### 4.2 Diurnal Temperature Swing

The 4–8 °C diurnal swing is consistent with field measurements from tepui summits. Adlassnig et al. (2010) recorded daytime temperatures of 15–21 °C and nighttime lows of 5–13 °C within a *Heliamphora nutans* population on Roraima (2,810 m). The terrarium's swing is somewhat narrower than these extremes but falls well within the operating range of the cultivated species.

The diurnal swing has several functional consequences:

- **Condensation on cold surfaces**: Nighttime cooling drives the evaporator plate surface below the dew point of the terrarium air, causing condensation that drips onto plants and substrates. This is not the same process as advective fog immersion on tepui summits — which is driven by orographic lifting of moisture-laden air — but it produces a similar functional outcome: liquid water deposition on aerial plant surfaces during cool periods.
- **Seasonal variation**: As Colombian weather patterns shift through the year (the bimodal wet seasons centered on April–May and October–November), the terrarium conditions vary correspondingly, potentially providing phenological cues for flowering — though this remains to be formally tested.

### 4.3 Stochastic Weather Events

Rain events in the Colombian reference cities produce sudden setpoint changes in the terrarium — temperature drops of several degrees within an hour accompanied by humidity targets approaching saturation. While these perturbations differ mechanistically from tepui fog immersion (Section 2.2), they produce temperature and humidity excursions of similar magnitude and duration to those recorded during cloud immersion events in tropical montane environments (Jarvis & Mulligan 2011). Some experienced *Heliamphora* growers associate rapid temperature drops with improved vigor, though this has not been formally tested.

`[AUTHOR TO PROVIDE: figures from the logged InfluxDB/Grafana data. The underlying series exist and are exportable; specific frames to select are (1) a representative 7-day temperature and humidity trace with weather-driven excursions visible; (2) a 24-hour diurnal cycle showing the 4–8 °C swing and the humidity pattern; (3) a seasonal comparison (e.g., a cool/wet vs. warm period). These are data-export-and-render tasks, not first-hand observations, and can be generated from the system logs.]`

### 4.4 Phenological Observations

`[AUTHOR TO PROVIDE: first-hand phenological correlations — these depend on the author's flowering and growth records and must not be inferred. Open questions to address if the data support them: whether *Heliamphora* flower preferentially at certain times of year; whether the *U. quelchii* inflorescence (April–May 2026) coincided with the April–May Colombian wet season / a temperature-drop episode; whether growth rate varies seasonally; whether *Nepenthes* pitcher production shows a seasonal pattern. The *U. quelchii* bloom timing is documented (§3.3); any causal link to environmental events remains the author's to assert or withhold.]`

---

## 5. Discussion

### 5.1 Weather-Mimicking vs. Fixed Setpoints for Carnivorous Plant Cultivation

The use of real-time weather data to drive terrarium setpoints represents a departure from conventional fixed-schedule environmental control. For carnivorous plants — especially tepui endemics adapted to dynamic, weather-driven environments — this approach offers several potential advantages:

**Naturalistic variability**: Fixed setpoints produce monotonous conditions that differ from the dynamic, weather-driven environments where these species evolved. Weather-referenced setpoints introduce stochastic variation within biologically safe bounds. Whether this variation provides phenological cues that fixed setpoints lack remains undemonstrated in this system, but the infrastructure for testing this hypothesis is in place. What is clear is that the plants have thrived under four years of continuous variation, suggesting at minimum that they tolerate — and may benefit from — conditions that change unpredictably within their natural climate envelope.

**Seasonal tracking**: The dynamic photoperiod (Section 2.3) and the seasonal variation in Colombian weather data provide longer-timescale variation that tracks the natural annual cycle at the tepui latitude. Whether this variation meaningfully affects *Heliamphora* flowering frequency or *Utricularia* growth patterns remains to be formally tested, but the infrastructure for such studies is in place through the system's comprehensive data logging.

**Revealing operational insights**: The weather-mimicking approach, with its continuous environmental variation and data logging, revealed the physical limit of evaporative cooling: when the terrarium temperature drops to approximately 16.6 °C in the evening (a threshold determined by the room's temperature and humidity), ventilation fans cease to provide cooling and instead inject warm room air. This counterintuitive finding — that running fans at night can *warm* a terrarium — has practical implications for any grower using ventilation-based cooling (Section 5.3).

### 5.2 Climatic Overlap Across Distinct Highland Habitats

A central finding of this work is the successful co-cultivation of carnivorous plants from ecologically distinct tropical highland habitats in a single enclosure. The carnivorous taxa discussed here occupy very different niches in nature: *Heliamphora* and *Brocchinia reducta* grow on open, treeless tepui (Pantepui) summits (Guiana Highlands, ~5° N, 1,500–2,800 m); the cabinet's highland *Nepenthes* grow as scrambling vines in upper montane mossy forests of Sumatra, Sulawesi, and the Philippines (~0–6° N, 1,500–3,000 m); and *Utricularia* sect. *Orchidioides* — represented in the cabinet by *U. quelchii* — are Neotropical epiphytes and lithophytes of tepui cliff faces and cloud-forest canopies. These habitats differ in vegetation structure, light regime, substrate, and species composition — an open tepui summit meadow bears no ecological resemblance to a forested upper montane *Nepenthes* slope; the climate-envelope overlap with tropical montane cloud forest *sensu* Hamilton, Juvik & Scatena (1995) is therefore bounded, not an identity.

Nevertheless, the physical climate at these sites overlaps substantially. The saturated adiabatic lapse rate in the tropics is approximately 0.5–0.6 °C per 100 m of elevation gain. At 2,000–2,800 m — the elevation band occupied by most of the species discussed here — this produces mean temperatures of 10–18 °C regardless of longitude, because the dominant thermal forcing is altitude, not geography. Roraima's summit (2,810 m) records daytime temperatures of 15–21 °C and nighttime lows of 5–13 °C within *Heliamphora* populations (Adlassnig et al. 2010). The high-elevation *Nepenthes* mountains of Borneo show comparable ranges (e.g., *N. villosa* at ~2,400–3,200 m on Mount Kinabalu; *N. edwardsiana* generally lower, ~1,500–2,700 m) — cited here as biogeographic comparison, not as cabinet taxa. Cloud-immersion frequencies of roughly half to most of nighttime hours are typical of tropical montane cloud forests globally (Jarvis & Mulligan 2011), driving humidity regimes of 80–100 % RH at these elevations. It is this climatic convergence — not ecological similarity — that permits co-cultivation. Species from separate evolutionary lineages and distinct habitat types have adapted to similar temperature and humidity ranges because these parameters are governed by altitude and the physics of saturated air masses rather than by the ecological community in which the species is embedded.

The remaining obstacle to co-cultivation is light. *Heliamphora* and *Brocchinia reducta*, adapted to fully exposed tepui summits where there is no tree canopy, require high irradiance. Highland *Nepenthes*, growing in the understory and margins of montane forests, require substantially less. In this system, the inverse square law from overhead LED sources provides a natural solution: light intensity falls off with the square of the distance from the source, creating a continuous gradient from high irradiance directly beneath the LEDs (upper zone, where tepui summit species are placed) to much lower irradiance at the terrarium floor (lower zone, where *Nepenthes* sit). A single lighting array thus accommodates the full range of light requirements without physical barriers or independently controlled fixtures, making the multi-habitat co-cultivation concept practically achievable.

The practical implication is that growers of highland carnivorous plants need not maintain separate terraria for tepui *Heliamphora*, Asian *Nepenthes*, and Neotropical *Utricularia*. A single enclosure tuned to the shared temperature and humidity requirements of tropical highland species, with a vertical light gradient, can accommodate all three along with companion orchids, ferns, and bromeliads from climatically compatible habitats.

### 5.3 Nighttime Cooling: Marine-Compressor Refrigeration and Fan-Mediated Humidity Control

The defining challenge of highland carnivorous plant cultivation — achieving meaningful nocturnal temperature drops in a domestic setting — has driven considerable innovation in the hobby. The chest freezer conversion (Shafer 2003), aquarium chillers with internal heat exchangers, modified portable air conditioners, and Peltier arrays have all been employed with varying success (see Introduction). The approach described here — marine refrigeration hardware with an internal evaporator plate — adds another option to this toolkit, with advantages in integration and long-term reliability for medium-to-large enclosures.

Two practical lessons emerge from four years of continuous data that are useful to any grower cooling a highland terrarium, independent of the specific hardware. **First, the compressor does essentially all of the cooling and the fans do essentially none of it.** A formal attribution of the cabinet's heat budget (a regression of cabinet-temperature change on compressor state, lights, and the room-to-cabinet temperature difference, over the 80.3-day metered window) finds that the marine compressor accounts for all the active cooling work, while ventilation fan speed has no measurable effect on cabinet temperature. **Second, the fans are humidity actuators, not cooling actuators.** When the terrarium is warmer than the room's wet-bulb temperature (~16.6 °C for a room at 22 °C / 58 % RH), running fans cools by evaporation; once the cabinet drops below that wet-bulb floor — which it does every night under active compressor cooling — the same fans inject sensible heat and become a net *warming* load. A causal analysis of a randomised fan-schedule experiment confirms that fan speed primarily moves humidity, not temperature.

The practical implication for growers is that **temperature and humidity should be driven by separate actuators**: let the compressor (or chest freezer, chiller, or air conditioner) set temperature, and let the fans set humidity, rather than relying on ventilation to do both. In this system the controller holds cabinet humidity within the weather-derived target band (75–95 % RH) with the fans while the compressor cycles to the temperature setpoint, and the two loops do not meaningfully interfere. The full regression tables, the instrumental-variables causal model, the statistical detail, and the replication scripts are reported in the companion engineering paper `[companion HardwareX paper]`.

### 5.4 Additional Practical Insights

**No dry rest periods**: The persistent high humidity required by *Heliamphora* and *Utricularia* precludes dry rest periods. Dry-rest-demanding species — most of the *Cattleya* alliance with strong dry-rest cues, and many *Dendrobium* section *Callista* — were excluded from the cabinet pre-emptively rather than tested-and-lost, because the cabinet's continuous high humidity is fundamentally incompatible with their flowering cycle. The losses that did occur within the introduced cohort over four years reflect a heterogeneous set of cultivation incompatibilities (warm-growing species too cool, sun-loving species too shaded, *Sophronitis pygmaea* humidity sensitivity, *Genlisea* tropical-lowland species too cool, occasional CITES-import customs failure for *Laelia briegeri*) rather than a single thematic cause. Climate-envelope compatibility is therefore best read as a pre-condition for inclusion in the cohort, not as a post-hoc explanation of survival rates within it.

**Silent airflow failures are dangerous.** A loose crimp on the power cable of one of the three fans on the evaporator-coil array let it stop without alarming. The remaining two fans kept the cabinet on temperature, so no thermal alarm fired, but the back-left corner stopped getting airflow. Black saprophytic mould slowly accumulated on the insulation panel through Q1 2026, and was eventually noticed because what initially looked like *Botrytis* on a *Dracula pholeodytes* bud turned out to be a saprophyte living off stagnant condensate. The cleanup episode itself was carried out on 2026-05-01: full evacuation of the cabinet, Physan-20 cleaning of all surfaces (10 mL per 5 L water), repair of the failed fan connection, and a careful re-install, after which conditions returned to normal within 24 h. The episode emphasised two things: redundancy in fan arrays masks individual failures, and the safety chain should track per-channel airflow not just aggregate temperature.

`[AUTHOR TO PROVIDE: other cultivation insights from four years of operation — these are first-hand and must not be inferred:]`
- `[AUTHOR TO PROVIDE: water quality — RO vs. tap, any conductivity/TDS targets]`
- `[AUTHOR TO PROVIDE: pest management in the enclosed system — pests observed and treatments used]`
- `[AUTHOR TO PROVIDE: living-Sphagnum replacement frequency by zone]`
- `[AUTHOR TO PROVIDE: Mediterranean-summer heat strategies (beyond the room-placement and continuous-compressor notes already in §5.5)]`

### 5.5 Limitations

- **Single sensor**: Environmental data comes from one sensor positioned at mid-canopy height. Temperature stratification within the enclosure is certain — the upper zone near the LEDs (where *Heliamphora* grow) is warmer than the lower zone, and microclimate at the evaporator plate surface differs from mid-air conditions. The reported temperatures should be understood as representative of mid-canopy conditions, not of the full range experienced by individual plants.
- **No formal growth metrics**: While we report general cultivation success over four years, systematic measurements of pitcher production rates, division frequency, or biomass accumulation have not been conducted. Claims of "successful cultivation" are based on sustained growth, division, and the absence of decline rather than on quantitative comparison with other growers' results or with wild growth rates.
- **Not cold enough for ultra-highland species**: The system's minimum temperature of 13.5 °C, while sufficient for mid-elevation species, falls short of the sub-10 °C nighttime temperatures recorded on higher tepui summits (>2,500 m) and the near-freezing conditions experienced by ultra-highland *Nepenthes* such as *N. villosa* and *N. lamii*. A chest freezer conversion (Shafer 2003) remains more appropriate for growers targeting these extreme species.
- **Light-heat tradeoff**: Every watt of LED output becomes a watt of heat load inside the enclosure, so the lighting contributes a substantial fraction of the cooling load that the compressor must remove. This tradeoff limits the achievable combination of high light intensity and low temperature — a constraint relevant to all enclosed cultivation systems, and the reason the LEDs run well below their rated output.
- **Mediterranean summer challenge**: During the hottest summer weeks (room temperatures reaching 27–28 °C), the compressor runs continuously and nighttime temperatures may not drop below 16–17 °C. The terrarium's placement in a room without direct sunlight mitigates but does not eliminate this limitation.
- **Heat-balance scope**: The compressor-versus-fans attribution (Section 5.3) holds over the routine operating range observed in this system (fan speeds at or below the levels used in normal running); whether fans remain thermally negligible at substantially higher airflow has not been tested. The supporting regression and its statistics are reported in the companion engineering paper.

---

## 6. Conclusions

The weather-mimicking approach is viable for long-term cultivation of highland carnivorous plants, with *Heliamphora*, highland *Nepenthes*, *Utricularia* sect. *Orchidioides*, and *Brocchinia reducta* maintained successfully for over four years under continuously varying conditions derived from real-time Colombian highland weather data.

Marine compressor refrigeration — using hardware designed for boat refrigeration — provides an effective and reliable cooling method for medium-to-large highland terraria, complementing the existing toolkit of chest freezer conversions (Shafer 2003), aquarium chillers, and modified air conditioners. The system routinely cools the terrarium to 13.5 °C in a room at 22 °C, with four years of continuous operation confirming long-term reliability. The most broadly applicable horticultural finding is that temperature and humidity should be driven by separate actuators: let the compressor (or whichever cooling appliance) set temperature, and let the fans set humidity, rather than asking ventilation to do both — a separation that generalises across cooling hardware. Unattended long-term operation is underwritten by an eleven-layer safety architecture that evolved over four years in response to real failure modes (including the airflow failure described in §5.4) and by an operator-alert chain that notifies on any non-normal condition; both are described in the companion engineering paper `[companion HardwareX paper]`, with the layer-by-layer deployment chronology in its supplementary materials.

The co-cultivation of carnivorous plants from ecologically distinct tropical highland habitats — tepui summit *Heliamphora* and the Guiana Shield bromeliad *Brocchinia reducta*, upper montane forest *Nepenthes*, and the tepui-cliff epiphyte *Utricularia quelchii* (sect. *Orchidioides*) — in a single enclosure is validated by four years of successful growth. These taxa occupy different ecological niches in nature, but their climatic tolerances overlap because tropical highland environments worldwide share similar temperature and humidity regimes at comparable elevations.

The full control system is open-source and described in a companion engineering paper `[companion HardwareX paper]`, with build photos, live conditions, blog posts, and the complete parts list on the project website (https://highlandcloudforest.com), enabling other growers and institutions to replicate or adapt the approach. A companion paper `[companion AoS/Orchids paper]` describes the orchid cultivation results from the same system.

---

## Acknowledgments

`[AUTHOR TO PROVIDE: acknowledgments text — e.g., vendors (Andreas Wistuba; Christian & Claudia Klein / Carnivors & More), family members credited in the collection records, and any reviewers or collaborators the author wishes to thank.]`

Portions of this manuscript were prepared with the assistance of an AI language model (Anthropic Claude). The system design, data collection, analysis, and all horticultural decisions are entirely the work of the authors.

---

## References

Adlassnig, W., Pranjić, K., Mayer, E., Steinhauser, G., Hejjas, F. & Lichtscheidl, I.K. 2010. The abiotic environment of *Heliamphora nutans* (Sarraceniaceae): pedological and microclimatic observations on Roraima Tepui. *Brazilian Archives of Biology and Technology* 53(2): 425–430.

Berry, P.E. & Riina, R. 2005. Insights into the diversity of the Pantepui flora and the biogeographic complexity of the Guayana Shield. *Biologiske Skrifter* 55: 145–167.

Clarke, C. 1997. *Nepenthes of Borneo.* Natural History Publications, Kota Kinabalu.

Clarke, C. 2001. *Nepenthes of Sumatra and Peninsular Malaysia.* Natural History Publications, Kota Kinabalu.

Hamilton, L.S., Juvik, J.O. & Scatena, F.N. (eds.) 1995. *Tropical Montane Cloud Forests.* Ecological Studies 110. Springer-Verlag, New York.

Jarvis, A. & Mulligan, M. 2011. The climate of cloud forests. In Bruijnzeel, L.A., Scatena, F.N. & Hamilton, L.S. (eds.), *Tropical Montane Cloud Forests: Science for Conservation and Management.* Cambridge University Press. pp. 39–56.

McPherson, S. 2007. *Pitcher Plants of the Americas.* The McDonald & Woodward Publishing Company.

Rull, V. & Vegas-Vilarrúbia, T. 2006. Unexpected biodiversity loss under global warming in the neotropical Guayana Highlands: a preliminary appraisal. *Global Change Biology* 12: 1–6.

Rull, V., Montoya, E., Nogué, S., Safont, E. & Vegas-Vilarrúbia, T. 2019. Climatic and ecological history of Pantepui and surrounding areas. In Rull, V. & Vegas-Vilarrúbia, T. (eds.), *Biodiversity of Pantepui: The Pristine "Lost World" of the Neotropical Guiana Highlands.* Academic Press. pp. 37–57.

Shafer, J. 2003. A novel method for the cultivation of *Nepenthes villosa*. *Carnivorous Plant Newsletter* 32(1): 20–23.

Taylor, P. 1989. *The Genus Utricularia — A Taxonomic Monograph.* Kew Bulletin Additional Series XIV. Royal Botanic Gardens, Kew. [Section *Orchidioides* and the *quelchii*/*campbelliana* characters: pp. 42–59.]

Zoppoli, G. 2026. First bloom: *Utricularia quelchii*, three years in. Highland Cloud Forest project website (blog post, 20 April 2026, updated 7 and 11 May 2026). https://highlandcloudforest.com (accessed June 2026).

cexx.org. 2011. Peltier element efficiency. https://www.cexx.org/peltier.htm (accessed February 2026).

`[AUTHOR TO PROVIDE / FINALIZE on submission: the following references are cited or recommended but need final bibliographic resolution:]`
- `[AUTHOR TO PROVIDE: full citation + DOI for the companion HardwareX engineering paper once assigned.]`
- `[AUTHOR TO PROVIDE: full citation for the companion AoS/Orchids paper once assigned.]`
- `[AUTHOR TO PROVIDE: Givnish, T.J. et al. 2014. Adaptive radiation, correlated and contingent evolution, and net species diversification in Bromeliaceae. — add full citation if the Brocchinia/Bromeliaceae carnivory context is retained; currently not cited in the body, so include only if a supporting sentence is added.]`
- `[AUTHOR TO PROVIDE: a Fleischmann reference on Utricularia sect. Orchidioides if a sentence requiring it is added; the genus authority cited in the body is Taylor (1989). Note: the blog's Fleischmann 2012 Monograph of the genus Genlisea is NOT the appropriate Utricularia authority.]`
