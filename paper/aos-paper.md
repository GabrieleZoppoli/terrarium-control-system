# Cloud Forest in a Box: Growing Highland Orchids with Real-Time Weather Simulation

**Author**: `[PLACEHOLDER — author name]`

`[PLACEHOLDER — author bio, 2-3 sentences: affiliation, location, growing experience]`

---

It started with a simple question: what if my terrarium could experience real cloud forest weather?

Growing highland orchids in a Mediterranean climate — Genoa, Italy, where summer temperatures regularly exceed 30 deg C — is a constant battle against heat and dryness. *Dracula*, *Masdevallia*, *Dendrobium victoriae-reginae*, and the rupicolous *Cattleya* species from the Brazilian highlands all demand cool, humid conditions year-round. Traditional terrarium approaches use fixed environmental targets: set the thermostat to 18 deg C, keep humidity at 90%, and hope for the best. But real cloud forests are not static. They experience weather — sudden temperature drops during rainstorms, diurnal fog cycles, seasonal shifts in cloud cover, brief sunny clearings at midday. Could a terrarium simulate that?

Over three years ago, I built a system that tries. Instead of programming fixed temperatures and humidity levels, the terrarium receives real-time weather data from four Colombian highland cities — Chinchina, Medellin, Bogota, and Sonson, at elevations of 1,300 to 2,600 meters — and uses their current conditions to set its own targets. A 15-hour time shift aligns Colombian daytime with my nighttime, so the terrarium's daily rhythm tracks real tropical mountain weather, complete with rain events, seasonal variation, and all the unpredictability that our orchids evolved with.

The results have been encouraging. Approximately 120 species from cloud forests on five continents coexist in a single 1.5 x 0.6 x 1.1 meter enclosure: orchids from the Andes, Papua New Guinea, and Brazil growing alongside Venezuelan tepui carnivorous plants and Asian highland pitcher plants — all under the same weather-driven conditions.

---

## The Convergent Cloud Forest Concept

The fundamental idea behind this terrarium is not new, but it is underappreciated: cloud forests worldwide share remarkably similar climates. Whether you are standing on a Colombian mountaintop at 2,000 meters, a tepui summit in Venezuela, a highland ridge in Papua New Guinea, or a misty peak in the Brazilian Atlantic Forest, you encounter the same basic conditions — cool temperatures (10–22 deg C), persistent humidity above 80%, frequent fog or cloud immersion, and moderate light filtered through the cloud layer.

This convergence is driven by physics. At similar tropical elevations, adiabatic cooling, orographic lifting, and cloud formation produce broadly similar microclimates regardless of longitude. Species evolving independently in these convergent environments face similar selective pressures and develop similar tolerances, even though they share no recent evolutionary history.

The practical consequence for growers is profound: *Dracula vampira* from the Colombian Andes, *Dendrobium victoriae-reginae* from Papua New Guinea, and rupicolous *Cattleya* from the Brazilian highlands can share a single terrarium because their native cloud forests, though separated by thousands of kilometers and millions of years of independent evolution, converge on the same environmental envelope. In my terrarium, these species grow side by side with tepui *Heliamphora* and Bornean *Nepenthes* — all thriving under identical conditions. Three years of co-cultivation is the strongest practical argument for this approach.

---

## The Setup

The terrarium is a 1.5 x 0.6 x 1.1 meter acrylic enclosure mounted on a heavy-duty aluminium scaffold. Two sliding front panels provide maintenance access. External insulation — extruded polystyrene with reflective Mylar — reduces heat gain and improves cooling efficiency.

The height of the enclosure is the critical design dimension. A perforated acrylic shelf at mid-height divides the interior into three growing zones:

- **Upper zone** (above the shelf, high light): Closest to the four LED pucks overhead. Home to *Heliamphora* and the most light-hungry orchid miniatures.
- **Middle zone** (shelf level, intermediate light): Hanging baskets of highland *Nepenthes* and mounts of epiphytic *Utricularia* live here, along with intermediate-light orchids.
- **Lower zone** (below the shelf, low light, coolest): This is *Dracula* and *Masdevallia* territory — the shadiest, coolest part of the enclosure, mimicking the deep understory where these orchids grow in nature.

The inverse square law is your friend here. Light intensity drops with the square of the distance from the source, so species at the bottom receive a fraction of what species at the top get. Rather than fighting this gradient, I use it: it naturally creates the distinct light environments that different orchid genera require.

Cooling comes from a small marine compressor unit (Vitrifrigo ND50) mounted above the terrarium, with refrigerant lines running down to a stainless steel evaporator plate installed horizontally inside the enclosure — the same compressor-and-pipes architecture used in boat refrigerators, not evaporative cooling. Four groups of fans — controlled by a Raspberry Pi computer — manage airflow. Below the terrarium sit a MistKing diaphragm pump, a water reservoir, and a condensate collection tank. The pump pushes water up through tubing to a network of 20 nozzle points across the ceiling that produce a fine fog. The whole system is automated: the computer adjusts fans, misting, cooling, and lighting based on the weather data, with no daily human intervention required.

`[PLACEHOLDER — overview photo of the complete terrarium showing the three growing zones, mounted orchids, and equipment placement]`

---

## How the Weather Simulation Works

Four Colombian highland cities serve as the weather source: Chinchina (~1,300 m), Medellin (~1,500 m), Sonson (~2,475 m), and Bogota (~2,640 m). The system polls their current temperature and humidity every few minutes and heavily averages the values — a 15-minute rolling mean across all four cities — to produce smooth, gradually changing targets.

The key trick is the 15-hour time shift. Colombian daytime (UTC-5) maps onto Italian nighttime (UTC+1), so when it is a warm afternoon in the Colombian coffee belt, my terrarium is experiencing its coolest nighttime temperatures. The result is a naturalistic diurnal cycle: cooler, more humid conditions at night and warmer, drier conditions during the day — exactly the pattern our orchids experience in nature.

What happens when the internet goes down? The system maintains a rolling 14-day historical curve — a smoothed average of the daily weather cycle from all four cities — and uses it as a fallback. Instead of jumping to crude fixed values, the terrarium follows a realistic diurnal profile until the connection is restored.

But the real magic is in the weather events. When an afternoon rainstorm sweeps through the Chinchina region — something that happens regularly in the Colombian highlands — the system's temperature target drops suddenly and humidity spikes toward saturation. In the terrarium, this translates into a burst of misting and compressor activity that simulates a fog immersion event. These events are not programmed. They emerge from real weather, and they vary from day to day, week to week, season to season. The orchids experience something much closer to actual cloud forest conditions than any fixed schedule could provide.

The lighting follows a dynamic photoperiod calculated daily from the Colombian latitude (about 5 deg N). Near the equator, day length varies only about 34 minutes through the year — from 11 hours 43 minutes at the December solstice to 12 hours 17 minutes at the June solstice. A gradual 30-minute dawn ramp simulates the slow tropical sunrise, and a midday brightness boost mimics the brief clearing events common on cloud forest mountaintops when the sun briefly breaks through the cloud layer.

One of the most surprising discoveries after three years of data collection was about nighttime cooling. I had assumed that running fans at night would help cool the terrarium by exchanging warm internal air with cooler room air. Analysis of the data showed the opposite: once the terrarium temperature drops below a threshold called the wet-bulb temperature — the lowest temperature achievable through evaporation alone — the fans actually *warm* the terrarium by pumping in room air whose heat content exceeds what evaporation can remove. The system now automatically shuts off the ventilation fans in the evening once this threshold is crossed, relying entirely on the compressor for overnight cooling. The lesson for growers: if you are running fans at night in a cooled terrarium, you may be working against yourself.

---

## The Orchids

### *Dracula*

`[PLACEHOLDER — species list. Typical taxa for this type of system:]`
- `[Drac. vampira]`
- `[Drac. chimaera]`
- `[Drac. erythrochaete]`
- `[Drac. bella]`
- `[Others]`

`[PLACEHOLDER — cultivation notes:]`
- `[Mounted on cork bark in the lower zone — describe mounting technique]`
- `[Inflorescences emerge through the moss pad and hang below the mount, just as in nature]`
- `[Flowering frequency — year-round? Seasonal peaks?]`
- `[Which species have done best? Any that struggled?]`

`[PLACEHOLDER — photos (6 megapixel minimum, JPEG, separate files):]`
- `[Habitat shot showing mounted plants in the terrarium]`
- `[Flower close-ups — Dracula flowers are among the most photogenic of all orchids]`
- `[Mounting technique detail]`

### *Masdevallia* and *Restrepia*

`[PLACEHOLDER — species list]`

`[PLACEHOLDER — cultivation notes:]`
- `[Lower and middle zone placement]`
- `[Sequential blooms from the same inflorescence — a delight of the genus]`
- `[Restrepia: insect-mimicking flowers produced repeatedly from the same leaf axils]`
- `[Any temperature-sensitivity observations?]`

`[PLACEHOLDER — photos:]`
- `[Masdevallia flowers — the bright colors and unusual shapes are perfect for AOS]`
- `[Restrepia showing the characteristic hinged labellum]`

### Rupicolous *Cattleya* (formerly *Sophronitis*)

`[PLACEHOLDER — species list. Follow current RHS-accepted nomenclature:]`
- `[C. coccinea]`
- `[C. cernua]`
- `[C. wittigiana]`
- `[Others]`

`[PLACEHOLDER — cultivation notes:]`
- `[Mounted on cork bark, upper and middle zones]`
- `[These miniature beauties from the Brazilian Atlantic Forest highlands are among the most vivid orchids in cultivation]`
- `[Flowering frequency — some species flower multiple times per year]`
- `[Color forms if relevant]`

`[PLACEHOLDER — photos:]`
- `[The brilliant red/orange flowers will make spectacular AOS photographs]`
- `[Plants mounted on cork bark showing their miniature habit]`

### *Dendrobium* sect. *Oxyglossum* (PNG Highlands)

`[PLACEHOLDER — species list:]`
- `[Den. victoriae-reginae]`
- `[Any allied species]`

`[PLACEHOLDER — cultivation notes:]`
- `[Mounted on tree fern plaques in the upper zone]`
- `[The PNG-Andes convergence story: these orchids evolved in geographic isolation from Dracula and Masdevallia, yet all three thrive under identical conditions because their respective cloud forests converge on similar environments]`
- `[Flowering observations — the brilliant blue-purple flowers are unlike almost anything else in cultivation]`

`[PLACEHOLDER — photos:]`
- `[Den. victoriae-reginae in flower would be a highlight of the article]`
- `[Plant on tree fern plaque showing growth habit]`

### *Phragmipedium*

`[PLACEHOLDER — species list:]`
- `[Phrag. species grown in the lower zone]`

`[PLACEHOLDER — cultivation notes:]`
- `[Grown in sphagnum-based media in the lower zone]`
- `[Moisture-loving — thrive in the persistently high humidity]`
- `[Flowering observations]`

`[PLACEHOLDER — photos]`

### Other Highland Orchids

`[PLACEHOLDER — brief notes on any additional orchid genera:]`
- `[Leptotes — Brazilian Atlantic Forest miniatures]`
- `[Vanda pumila — if still in cultivation]`
- `[Any Pleurothallis alliance not covered above]`
- `[Any other genera]`

`[PLACEHOLDER — a brief note and photo for each]`

---

## Lessons Learned

Three years of growing highland orchids with weather simulation have taught me several things:

**The light gradient is your most valuable tool.** Rather than trying to provide uniform light — which would require compromises unsuitable for either high-light or shade-adapted species — exploit the inverse square law. Place *Cattleya* and *Dendrobium* near the top, *Masdevallia* and *Dracula* at the bottom, and intermediate growers in between. A single lighting system creates three distinct growing environments.

**Weather simulation beats fixed setpoints.** Whether the orchids are actually responding to the variable conditions with improved flowering or vigor is something I cannot prove without a controlled comparison. But I can say that the system produces environmental variation that feels more natural — sudden cool spells, humidity surges, gradual seasonal shifts — and the orchids seem to be doing well in it.

**The wet-bulb lesson: fans can warm your terrarium at night.** This was the most counterintuitive discovery. If your terrarium is cooled below the wet-bulb temperature of the surrounding room air — which happens any time you use mechanical cooling to drop temperatures significantly below room ambient — running ventilation fans actually heats the terrarium. The incoming room air carries more heat than evaporation can remove. The solution is simple: turn off the fans in the evening and let the compressor do the work alone.

**No dry rest means some losses.** The persistent high humidity required by *Dracula*, *Heliamphora*, and the epiphytic *Utricularia* precludes dry rest periods. Over three years, the orchids I have lost have primarily been those needing seasonal drying to initiate flowering — certain *Dendrobium* and *Cattleya* alliance species with pronounced rest requirements. If your priority species need dry rest, this is not the system for them. But for the many orchid genera that thrive in year-round moisture — the Pleurothallis alliance, the *Oxyglossum* dendrobiums, the rupicolous *Cattleya*, *Phragmipedium* — it works well.

`[PLACEHOLDER — any other practical tips for growers:]`
- `[Air circulation patterns — how important is internal airflow?]`
- `[Cork bark vs. tree fern: which species prefer which?]`
- `[Water quality considerations?]`
- `[Summer heat management tips for Mediterranean growers?]`
- `[Any pest management observations?]`

---

## Resources

The entire control system — software, firmware, hardware designs, dashboards, and analysis scripts — is freely available as open-source under the CERN Open Hardware Licence. A detailed engineering paper describing the full system design and construction is published in *HardwareX* [ref]. A companion article in the *Carnivorous Plant Newsletter* [ref] describes the cultivation results for *Heliamphora*, *Nepenthes*, and *Utricularia* from the same terrarium.

For growers interested in building a similar system, the *HardwareX* paper provides step-by-step instructions. The core components — a Raspberry Pi computer, an Arduino microcontroller, smart plugs, fans, and an LED lighting system — are all commodity items available from standard electronics suppliers. The Node-RED visual programming environment allows the control logic to be inspected and modified without traditional programming expertise.

---

## References

`[PLACEHOLDER — format per AOS style:]`
- `[Ref to HardwareX companion paper — full citation]`
- `[Ref to CPN companion paper — full citation]`
- `[Stull, R. 2011. Wet-Bulb Temperature from Relative Humidity and Air Temperature. J. Appl. Meteor. Climatol. 50:2267–2269.]`

`[PLACEHOLDER — additional references as needed for orchid nomenclature/taxonomy]`

---

*`[PLACEHOLDER — author contact information per AOS requirements]`*

*`[PLACEHOLDER — photo credits and captions list (6 megapixel minimum, JPEG, separate files, with captions provided separately from the text)]`*
