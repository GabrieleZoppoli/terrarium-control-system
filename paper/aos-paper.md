# Cloud Forest in a Box: Growing Highland Orchids with Real-Time Weather Simulation

**Author**: `[PLACEHOLDER — author name]`

`[PLACEHOLDER — author bio, 2-3 sentences: affiliation, location, growing experience]`

---

It started with a simple question: what if my terrarium could experience real cloud-forest weather?

Growing highland orchids in a Mediterranean climate — Genoa, Italy, where summer afternoons regularly push past 30 °C — is a constant battle against heat and dryness. *Dracula*, *Masdevallia*, the PNG *Dendrobium* miniatures, and the small Brazilian *Sophronitis* and *Laelia* all want the same thing: cool, foggy, year-round. The usual answer is a thermostat: set it to 18 °C, hold humidity at 90 %, and hope. But the cloud forests these plants come from are not flat numbers. They are *weather* — sudden temperature drops with afternoon storms, fog rolling in at dusk, a brief sunny clearing at midday, seasonal shifts in cloud cover. A fixed-setpoint cabinet replaces all of that with a single tone. Could a terrarium play the song instead?

Four years ago (May 2022) I built one that tries. Instead of programming fixed temperatures and humidities, the cabinet pulls real-time weather from four Colombian highland cities — Chinchina, Medellín, Bogotá, and Sonsón, between 1,300 and 2,600 m — and uses their conditions to set its own targets. A 15-hour backward look at the archived data, combined with the 7-hour time-zone offset between Italy (UTC+2) and Colombia (UTC−5), keeps the cabinet's day/night cycle phase-aligned with Italian local time: when it is mid-afternoon in Colombia (and the cabinet is reading that data), it is mid-day in Genoa; when Colombian pre-dawn lows are arriving, it is the middle of an Italian night. The cabinet experiences a stochastic tropical-highland day driven by real weather, not a fixed schedule, but on the right clock.

The results have been encouraging. Seventy-five living accessions across 31 plant genera — from convergent cloud forests on three continents — coexist in a single ~1 m³ enclosure (1.5 × 0.6 × 1.1 m). Orchids from the Andes, the Brazilian Atlantic Forest, the Philippine highlands, and Papua New Guinea grow side by side with Venezuelan tepui carnivores and Sumatran-Sulawesi-Philippine highland pitcher plants — all under the same weather-driven conditions, day after day, for four years.

---

## The Convergent Cloud-Forest Concept

The idea behind this cabinet is not new but is underappreciated: tropical cloud forests around the world settle into surprisingly similar climates. Stand on a Colombian mountaintop at 2,000 m, an Atlantic Forest ridge in the Brazilian Serra do Mar, or a foggy slope in central New Guinea highlands, and the readings come out close: cool (10–22 °C), persistently humid (above 80 %), often in fog, with moderate light filtered through cloud. The trick is that tropical mountain meteorology — adiabatic cooling on a moist parcel as it rises, orographic lifting against the slope, cloud deck forming at a roughly fixed condensation height — produces similar microclimates at similar elevations, regardless of which mountain you are on.

For an orchid grower, that means the geographic-isolation story matters less for cultivation than the climatic envelope. Colombian *Dracula simia* and *D. pholeodytes*, PNG *Dendrobium cuthbertsonii* and *D. cyanocentrum*, and Brazilian *Sophronitis coccinea* and *Laelia ghillanyi* evolved millions of years apart on different continents — but their native cloud forests overlap closely in temperature, humidity, and fog exposure. In my cabinet they grow side by side with Venezuelan *Heliamphora* and highland *Nepenthes* from Sumatra, Sulawesi, and the Philippines. Four years of co-cultivation is the practical argument for convergence.

A genuinely separate thread is the *light* requirement. Tepui *Heliamphora* and Brazilian rupicolous *Sophronitis* grow in the open; *Dracula* and *Masdevallia* are deep-shade understory plants. A single overhead LED setup cannot give both groups the same light — but the inverse-square law gives it for free along the vertical axis. Plants nearest the lamps see the brightest light; plants on the lower shelf see a small fraction of that. The cabinet's three growing tiers solve the light-gradient problem with geometry rather than separate fixtures.

---

## The Setup

The cabinet is a ~1 m³ acrylic box (1.5 × 0.6 × 1.1 m, W × D × H) sitting on a heavy aluminium scaffold, with sliding front panels for access and a layer of insulation (extruded polystyrene, faced with reflective Mylar) wrapped around the outside. Inside, a perforated acrylic shelf at mid-height splits the volume into three growing tiers:

- **Upper tier** (closest to the LEDs): the brightest position. Home to *Heliamphora*, the rupicolous *Sophronitis* and *Laelia*, and the Cattleya-s.s. miniatures that tolerate high light.
- **Middle tier** (around shelf level, intermediate): hanging baskets of highland *Nepenthes*, mounted *Utricularia quelchii*, and mid-light *Dendrobium*.
- **Lower tier** (below the shelf, low light, coolest): *Dracula*, *Masdevallia*, *Restrepia*, the small Pleurothallidinae, and the *Phragmipedium*.

Cooling comes from a small marine compressor unit (Vitrifrigo ND50, pre-charged with R134a) mounted *above* the cabinet, with refrigerant lines running down to a stainless-steel evaporator plate mounted *horizontally* on the rear wall, near the cabinet floor. Cold air sinks to the bottom and rises by convection as it warms — which is why the deepest, dimmest tier is also reliably the coolest. Misting is a MistKing diaphragm pump pushing water up to a network of about twenty nozzle points on the ceiling. A Raspberry Pi runs everything, with no daily intervention required.

`[PLACEHOLDER — overview photo of the complete terrarium showing the three growing tiers, mounted orchids, and equipment placement. Suggested: a wide front-on shot in normal "lights-on" condition with the *Heliamphora* and *Sophronitis* visible on the upper shelf and *Dracula* / *Masdevallia* visible below.]`

---

## How the Weather Simulation Works

Four Colombian highland cities (Chinchina ~1,300 m, Medellín ~1,500 m, Sonsón ~2,475 m, Bogotá ~2,640 m) act as the weather source. Their current temperature and humidity are polled, archived, and averaged across the four to give a single setpoint trace.

The 15-hour backward look is the trick that keeps the cabinet's daily cycle aligned with Italian local time rather than Colombian local time. Italy is seven hours ahead of Colombia: if the cabinet simply tracked *current* Colombian weather, an Italian noon would be a Colombian dawn (cold and damp), and the cabinet would invert the natural day-cold/night-warm cycle. Looking 15 hours back in the locally archived series fixes the alignment. At Italian noon, the cabinet retrieves the Colombian state from yesterday afternoon (warm, slightly drier); at Italian midnight, it retrieves the Colombian state from early-morning today (cool, near-saturated). The cabinet's plants experience the *kind* of weather that a Colombian highland location would deliver, but on a daily rhythm that matches their lighting cycle and the room's day/night temperature swing.

What happens when the internet goes down? The system maintains a rolling 14-day historical curve — a smoothed average of the past two weeks of weather — and uses it as a fallback. The cabinet keeps following a realistic diurnal profile until the live data resumes.

The weather *events* are where the simulation earns its name. When an afternoon rainstorm sweeps through the Chinchina region — something that happens regularly in the Colombian coffee belt — the system's temperature target drops sharply and the humidity setpoint jumps toward saturation. In the cabinet, this turns into a burst of misting and a tighter compressor cycle, simulating a fog-immersion event. These events are not programmed; they emerge from real weather, and they vary from day to day, week to week, season to season. The orchids encounter conditions that are much closer to what they evolved with than any fixed schedule could deliver.

Lighting follows a dynamic photoperiod calculated daily from the Colombian reference latitude (~5° N) and clamped to a 10–14 h range. Near the equator, day length varies by only about 34 minutes through the year, but the cabinet allows a slightly wider seasonal swing for the benefit of the higher-latitude orchids. The LED schedule is a raised-cosine curve through the photoperiod, with a soft 30-minute dawn ramp and peak intensity centred on solar noon — closer to a Colombian highland day than the on/off step schedule most hobbyist controllers use.

One of the more counter-intuitive findings after four years of logged data: at night, the ventilation fans actually *warm* the cabinet rather than cool it. Once the cabinet temperature drops below the *wet-bulb* temperature of the surrounding room air — the lowest temperature reachable by evaporation alone, around 16.6 °C in a typical Italian living-room — pumping room air in adds more sensible heat than evaporation can carry away. The system now automatically disengages the outlet and impeller fans in the evening once that threshold is crossed and relies on the compressor for the deeper cooling. The practical lesson for growers running compressor-cooled cabinets: if you are running fans through the night, you may be working against yourself.

---

## The Orchids

The orchid collection occupies about 60 of the cabinet's 75 living accessions, drawn from six main groups.

### *Dracula*

Six living *Dracula* in the lower (coolest, shadiest) tier. By accession: *D. simia*, *D. lotax*, *D. vlad-tepes*, *D. pholeodytes*, the *D.* Raven 'Jet' hybrid, and one ID-uncertain *D.* 'Fake' *hirsuta* 'Yellow'. Geographic origins span Colombia (*pholeodytes*, *vlad-tepes*) and Ecuador (*simia*, *lotax*), with the hybrid carrying *D. vampira* (Ecuadorian) in its parentage.

Cultivation: mounted on cork-bark slabs or in small net pots with live *Sphagnum*, hung on the back wall of the lower tier. Inflorescences emerge through the moss pad and hang below the mount, exactly as in nature. *D. simia* and *D. lotax* have flowered repeatedly; *D. pholeodytes* set a stunning early-2026 bud that the deep-clean episode (see Lessons) interrupted. The hybrid *Raven 'Jet'* and the smaller-flowered species bloom throughout the year with no obvious seasonal cue.

`[PLACEHOLDER — photos: mounted-on-cork wall shot of two or three plants together; close-up of a *D. simia* or *D. lotax* flower (the genus's most photogenic feature); a *D. pholeodytes* in bud for the deep-clean lessons section.]`

### *Masdevallia*, *Restrepia*, and other Pleurothallidinae

Five *Masdevallia* (*decumana*, *xanthina* red, *lucernula*, the *Devil's Heart* hybrid, *caudata* 'Gigi'), three *Restrepia* (*vasquezii*, *sanguinea*, *trichoglossa* var. *xanthina*), plus *Lepanthopsis astrophora* (× 2), *Platystele baqueroi*, *Pleurothallis leptotifolia*, and the wonderfully tiny *Phymatidium tillandsioides*.

These are the lower- and middle-tier specialists. *Masdevallia* like the cool understory and reward it with sequential blooms from the same inflorescence; the *Restrepia* throw their hinged, insect-mimicking flowers from the same leaf axils over and over; *Phymatidium tillandsioides* lives mounted on a small twig and produces white flowers that need a hand lens to appreciate. Year-round high humidity suits all of them; the lower tier's pooled cold air gives a useful nighttime drop without ever drying out.

`[PLACEHOLDER — photos: a *Masdevallia* inflorescence (bright colour and unusual shape — perfect for AOS); a *Restrepia* showing the hinged labellum; a macro of *Phymatidium* in flower if possible.]`

### *Sophronitis*, *Laelia*, and *Cattleya* — Brazilian highland and seasonally-dry miniatures

Brazilian Atlantic Forest miniatures are well represented in the upper tier. The rupicolous group (former *Sophronitis* sensu stricto, technically now within *Cattleya* under RHS nomenclature but still treated as *Sophronitis* in horticultural practice) includes *S. coccinea* f. *aurea*, the spectacular *S. coccinea* 'Big One' × 'Hinomaru' 4N GM/WOC, *S. brevipedunculata*, *S. wittigiana* rosea, and *S. pygmaea* (Brazil import). Three rupicolous *Laelia* (*L. ghillanyi*, *L. milleri*, *L. lundii* coerulea) sit alongside them, with the tiny *Isabelia pulchella* and two *Leptotes* (*bicolor* and *unicolor*) filling the same niche.

The most notable departure from textbook *Cattleya* culture is the presence of *C. aclandiae* and two color forms of *C. walkeriana* (*f. semialba* 'Tokyo No. 1' AM/AOS and *coerulea* 'Blu Monarch' × 'ABC') under year-round moisture. These two Brazilian species are usually grown with a pronounced dry rest to trigger flowering, and the textbook prediction would be that they sulk in a permanently humid cabinet. Both have been alive and growing in the cabinet — slowly, no flowering yet — but their long-term performance is one of the open questions of this experiment. If you absolutely depend on Cattleya-s.s. flowering, the conventional advice (dry rest after pseudobulb maturation) still applies; this cabinet is set up for moisture-dependent species and accepts that some of the seasonally-dry orchids will trade flowering for survival.

`[PLACEHOLDER — photos: the brilliant red *S. coccinea* 'Big One' × 'Hinomaru' flower (will make a spectacular AOS image); a cork-mount group shot of the rupicolous Sophronitis / Laelia / Isabelia / Leptotes assembly; a *C. walkeriana* coerulea growing without flowering.]`

### *Dendrobium* — Papua New Guinea highlands and the Philippine outlier

Five *Dendrobium* in the cabinet, but they split cleanly into two stories. The PNG / section *Oxyglossum* group — the small, jewel-coloured Australasian highlands group — is represented by *D. cuthbertsonii* 'Yellow', *D. cyanocentrum* 'Blau', and *D. hellwigianum*. These are the classic high-elevation New Guinea miniatures, growing in the upper tier on tree-fern plaques in live *Sphagnum*; their flowers are tiny and intensely coloured, a long way from the more familiar large-flowered *Dendrobium* hybrids of orchid shows. They thrive on the cabinet's cool, year-round-moist conditions.

The fifth is *Dendrobium victoriae-reginae*, the well-known "blue dendrobium". Despite the colloquial association with New Guinea, it is in fact endemic to the Philippines (POWO) and belongs to section *Calcarifera*, not *Oxyglossum* (IOSPE). It is the Philippine highland representative in the cabinet rather than a PNG one, but its cultural requirements — cool, humid, moderately bright — are essentially identical to the Oxyglossum group, which is why it grows happily alongside them. *D. trantuanii*, also in the cabinet, is a Vietnamese highland species in yet another section; it sits in the upper tier with the others.

`[PLACEHOLDER — photos: a *D. cuthbertsonii* 'Yellow' flower (small but intensely coloured); a *D. victoriae-reginae* flower in its characteristic blue, captioned as Philippine, sect. *Calcarifera*; the upper-tier tree-fern-plaque shelf as a group shot.]`

### *Phragmipedium kovachii*

One slipper in the cabinet, *Phragmipedium kovachii* — the famously controversial Peruvian species that arrived in cultivation in 2002 and triggered the largest CITES-related episode in modern orchid horticulture. The cabinet specimen is a legally-acquired horticultural propagation, kept in the lower tier in a sphagnum-dominated mix. *Kovachii* is moisture-loving and tolerates the cabinet's persistent high humidity well. A growing-only specimen at present; the well-documented difficulty of bringing this species to flower under cabinet conditions is part of the reason for cautious year-on-year observation rather than an expectation of bloom.

`[PLACEHOLDER — photo: the plant in growth (no flower yet); a brief caption noting the species's history and the cabinet's role as ex-situ refuge for moisture-dependent species.]`

### Smaller representation: *Aerangis*, *Holcoglossum*, *Schoenorchis*, *Chiloschista*, *Comparettia*, *Maxillaria*, *Mediocalcar*, *Macroclinium*, *Nageliella*, *Oerstedella*, *Oncidium*, *Ornitophora*

Single accessions of these genera fill out the cabinet's species list. Each is in the cabinet because its native climate is somewhere in the convergent cloud-forest envelope: PNG (*Mediocalcar bifolium*, *Ceratochilus jiewhoei*), Andean and Brazilian *Oncidium* relatives (*Comparettia*, *Macroclinium*, *Ornitophora*), Mexican/Central American highlands (*Oerstedella*, *Nageliella*), and Asian highlands (*Holcoglossum*, *Schoenorchis*, *Chiloschista*). Some are flowering regularly; most are vegetatively stable but not yet bloomed. The cabinet's purpose for these species is preservation and observation rather than show flowering.

---

## Lessons Learned

Four years of running this cabinet have taught me several things that I think generalise to anyone trying to cultivate highland orchids outside their native range.

**The light gradient is the most valuable design feature.** Rather than trying to give every plant the same light — which would force compromises hurting either the high-light or the shade-loving species — exploit the inverse-square law from your overhead LEDs. Place *Sophronitis*, *Laelia*, and the cabinet's high-light *Heliamphora* near the top; *Dracula* and *Masdevallia* on the floor; intermediate growers in between. A single light system gives you three distinct growing environments for free.

**Real weather beats fixed setpoints — at least it feels better and the plants don't object.** Whether the orchids are *actively responding* to the variable conditions with improved vigour or flowering is something I cannot prove without a controlled comparison. What I can say is that conditions in the cabinet feel more natural — sudden cool spells, humidity surges, gradual seasonal drifts — and the plants are doing well. None of the species that have established here have shown obvious deterioration over the years; many have flowered repeatedly. The most striking individual result was *Utricularia quelchii* finally putting up an inflorescence after three years of pure vegetative growth, in April–May 2026.

**The wet-bulb lesson: fans can warm your cabinet at night.** The most counter-intuitive finding. If you cool your cabinet below the wet-bulb temperature of the surrounding room — which happens whenever you push internal temperatures meaningfully below room ambient — running ventilation fans then actively heats the cabinet. The incoming room air carries more sensible heat than evaporation can remove. Simple fix: shut the fans off in the evening once the cabinet has crossed below the wet-bulb threshold and let the compressor work alone.

**No dry rest means some losses, and you should choose with eyes open.** The persistent high humidity that *Dracula*, *Heliamphora*, *Utricularia*, and the moisture-dependent miniatures need is fundamentally incompatible with the dry-rest cycle that some *Cattleya* alliance and certain *Dendrobium* sections (section *Callista* especially) need for flowering. Over four years, the orchids I have lost or that have stopped flowering have been concentrated in the dry-rest group — not in any particular geographic region. The cabinet's verdict has consistently been that climate envelope, not biogeographic origin, determines compatibility. If your priority species require dry rest, this is not the right system for them; if your priority species are moisture-dependent montane miniatures, it works well.

**Find the dead corner.** In early 2026 a faulty crimp on one of the evaporator-coil fans let one of three fans silently disconnect itself. The other two kept the cabinet on temperature, so no alarm went off — but the back-left corner stopped getting airflow, mould slowly built up on the insulation panel, and I eventually noticed because what I thought was botrytis on a *Dracula pholeodytes* bud was actually saprophytic growth living off condensation in the still corner. The full deep-clean (the first in four years) is in the companion blog post. The take-home for cabinet growers: airflow failures are often silent because the redundancy of multiple fans hides the loss of one. Look at corners.

`[PLACEHOLDER — additional practical tips:]`
- `[Cork bark vs tree fern: which species prefer which mount surface?]`
- `[Water quality / fertiliser regime — RO or tap, and what feed schedule]`
- `[Summer heat-management tips for Mediterranean growers]`
- `[Pest management observations after four years]`

---

## Resources

The entire control system — software, firmware, hardware designs, dashboards, and analysis scripts — is freely available as open source under the CERN Open Hardware Licence. A detailed engineering paper describing the full system design and construction is published in *HardwareX* [ref]. A companion article in the *Carnivorous Plant Newsletter* [ref] describes the cultivation results for *Heliamphora*, *Nepenthes*, and *Utricularia* from the same cabinet. A public companion website [URL — TBD] carries live cabinet conditions, build photos, per-species pages, and ongoing blog posts (including the *U. quelchii* first-bloom record and the deep-clean episode mentioned above).

For growers interested in building a similar system, the *HardwareX* paper provides step-by-step instructions. The core components — a Raspberry Pi, an Arduino microcontroller, smart plugs, fans, and an LED lighting system — are all commodity items from standard electronics suppliers. The Node-RED visual programming environment allows the control logic to be inspected and modified without traditional programming experience.

---

## References

- `[Companion HardwareX paper — full citation once published]`
- `[Companion CPN paper — full citation once published]`
- Stull, R. (2011). Wet-Bulb Temperature from Relative Humidity and Air Temperature. *Journal of Applied Meteorology and Climatology*, 50(11), 2267–2269.
- POWO (2026). *Dendrobium victoriae-reginae* — Plants of the World Online. Royal Botanic Gardens, Kew.
- IOSPE (2026). *Dendrobium victoriae-reginae* — Internet Orchid Species Photo Encyclopedia.
- Taylor, P. (1989). *The Genus Utricularia — A Taxonomic Monograph*. Kew Bulletin Additional Series XIV. (Cited for *U. quelchii* / section *Orchidioides*.)

`[PLACEHOLDER — additional citations as needed for orchid nomenclature and any AOS-style references the editor requires]`

---

*`[PLACEHOLDER — author contact information per AOS requirements]`*

*`[PLACEHOLDER — photo credits and captions list (6-megapixel minimum JPEG, separate files, captions in a separate document per AOS submission requirements). Suggested image set, ranked:]`*

1. *Sophronitis coccinea* 'Big One' × 'Hinomaru' in full flower — opening or hero image.
2. Front-on wide shot of the cabinet showing the three growing tiers under "lights on" conditions.
3. *Dendrobium cuthbertsonii* 'Yellow' flower close-up — the PNG/Oxyglossum highlight.
4. *Dracula simia* or *D. lotax* flower close-up — the Dracula genus's most photogenic specimen.
5. *Utricularia quelchii* bloom (the April–May 2026 inflorescence) — narrative highlight for the "Lessons" section.
6. Cork-mount wall group shot showing several mounted plants together — for the §The Setup section.
7. *Dendrobium victoriae-reginae* flower, captioned explicitly as Philippine / sect. *Calcarifera*.
8. *Masdevallia* (any colourful species) flower close-up.
9. *Restrepia* showing the hinged labellum.
10. *Phragmipedium kovachii* in vegetative growth, with a careful caption about the species's history.
