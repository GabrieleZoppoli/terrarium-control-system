# Manuscript rebuild survey — 2026-05-11

**Purpose.** The four paper drafts in `paper/` were last edited 2026-03-08 (commit `0c8a190`). Since then ~2 months of operational changes, experiments, and learnings have accumulated, and a public Hugo site (`website/`) has come online as a living companion to the papers. This survey maps post-2026-03-08 material to the four drafts on three axes:

- **Promote** — new findings that belong *inside* the papers.
- **Demote** — existing paper content that's now better served by a short pointer to the website + a Zenodo deposit.
- **Cross-ref** — explicit `→ see [website page]` insertions so the papers and the site work as a unit.

This is a **survey**, not edits. The output is a punch list for the user to approve/redirect before any draft is actually rewritten.

**Sources surveyed:** all 4 paper TOCs; all 40+ memory entries; the full `website/content/` tree; the public ledger feed; the per-species pages; the blog posts; the docs (`docs/architecture.md`, `pid-controller.md`, `schema.md`).

**Critical decision needed up front (see §6):** Zenodo deposit strategy for the website snapshot, so paper cross-references resolve in perpetuity.

---

## 1. Shared consistency table (cite these uniformly across all 4 drafts)

The most-cited operational numbers, verified against `static/data/collection.csv`, `data/ledger.json`, and the system memory entries on 2026-05-11. If any draft cites a different value, it's wrong.

**Scope note.** Numbers below describe **the highland cabinet contents only** — not the broader plant collection (outdoor, windowsill, shelves). The user has been explicit: papers report on the cabinet, not on all accessions. The collection-wide totals are recorded at the bottom of this section for completeness, but should not appear as headline figures in any draft.

### 1A. Cabinet contents — the headline numbers

| Number | Value | Source | Cite in |
|---|---:|---|---|
| Continuous operation since | **May 2022** (4 years as of 2026-05) | Photo evidence + "8 mo / 13 mo" notes in original draft; corrected 2026-05-02 | All |
| Living accessions in cabinet | **76** | `collection.csv` filtered `status=alive AND location=highland` | All §3 |
| Distinct taxa in cabinet | **75** (one duplicate accession) | Same | All §3 |
| Distinct genera in cabinet | **32** | Same | All §3 |
| Historical losses (4 years) | 14 lost + 1 given = **15 over 4 years** (~3.7 %/yr) | `collection.csv` highland + status ≠ alive | HardwareX §6.4 + §7.6, ICPS §6.3 (no-dry-rest tradeoff), CPN §5 |
| Biogeographic spread | **4 continents** (S America: tepui, Andes, Atlantic Forest; Africa: *Aerangis*; Asia: highland *Nepenthes* + *Holcoglossum* + *Schoenorchis*; Oceania: PNG *Dendrobium*/*Mediocalcar*/*Ceratochilus*/*Phymatidium*) | Genus list cross-checked against type localities | All — **drop any "5 continents" wording**, use 4 |
| Top genera by accession count | *Nepenthes* (9), *Heliamphora* (9), *Dracula* (6), *Sophronitis* (5), *Masdevallia* (5), *Dendrobium* (5) | `collection.csv` | All §3 introduction |

### 1B. Physical configuration (from `memory/physical-layout.md`)

| Component | Value | Cite in |
|---|---|---|
| Enclosure interior dimensions | 1.5 × 0.6 × 1.1 m (W × D × H) | All |
| Cabinet volume | **~1 m³** (1.5 × 0.6 × 1.1 = 0.99 m³; round in body text) | HardwareX §2, ICPS §2.1 |
| Cooling system | Vitrifrigo ND50 + Danfoss BD50F compressor (**above** terrarium); Vitrifrigo PT14 evaporator **horizontal in the lower portion of the back wall** (cutout at ~20 cm from cabinet floor per build schematic `panel-03-with-radiator.png`). **Not near the top** — the earlier draft and the prior memory note saying "near the top" were wrong. | HardwareX §5.2, ICPS §2.2 |
| Cold-air distribution | Evaporator is *low and horizontal*; the 3× Noctua NF-F12 iPPC-2000 fans on the 30°-inclined plexiglass plate push cold air downward through the lower slit. Cold air pools near the floor, rises by convection. This explains the **inverse light/temperature stratification**: high-light + warmer up top (closer to LEDs, away from evaporator), shade + cooler near floor (closer to cold-air pool). | HardwareX §5.2 + §7.1 |
| Refrigerant routing | Sealed pass-through through top of cabinet | HardwareX §5.2 |
| Below-cabinet shelf | Condensate collection tank + MistKing reservoir + MistKing diaphragm pump | HardwareX §5.1.4 |
| LED arrangement | 4× ChilLED Logic Puck V3, 244× Samsung LM301B each, on 140 mm pin heatsinks + 12 V fans (not water-cooled), with **two-stage dimming**: Mean Well screw potentiometer (~60 % hardware ceiling) + PWM dynamic ramp on top | HardwareX §4.2 + §7.7 |

### 1C. Operational performance — measured

| Number | Value | Source | Cite in |
|---|---:|---|---|
| Total energy logged | **211.4 kWh over 94.3 days** (since 2026-02-04 daemon start; window not full 4-year history) | `ledger.json` electricity | HardwareX §7.7, ICPS §4 |
| Daily consumption | **2.60 kWh/day** verified | Same; mean 109.9 W, median 110.7 W, p95 202.6 W, max 492.9 W | HardwareX §7.7 |
| Monthly consumption | **68.2 kWh/month** at the current operating regime | Same | HardwareX §7.7 |
| Hour-of-day profile | Night 60–90 W (compressor + base) / midday peak 170–180 W (lights peak ± compressor overlap) | `ledger.json` electricity note | HardwareX §7.7 |
| Annualised cost (€0.30/kWh) | **~€253/year** (extrapolated from €20.5/month observed) | `ledger.json` cost_eur | All — operational footnote |
| Mist cycle count | **1,439 over 94.3 days** (post-2026-02-04 logged; pre-rotation history not in window) | `ledger.json` mist_cycles | HardwareX §7.7, ICPS §4 |
| Mist cycles per day | **15.3/day average** in the window (regime-aware since 2026-05-05; pre-2026-05-05 ran on simpler trigger) | Derived from monthly: 464 cycles / 30.4 d | HardwareX §6.2, ICPS §2.6 |
| Fog hours (RH ≥ 95 %) | **118.2 h** in window = **1.25 h/day** | `ledger.json` fog_hours | HardwareX §7.1, ICPS §4.1 |
| Data points logged | **3,114,287 across 33 measurements** in the InfluxDB retention window | `ledger.json` data_points | HardwareX §7 intro, ICPS §4 intro |
| Wet-bulb floor (room 22 °C / 58 % RH) | 16.6 °C | `memory/wetbulb-analysis.md` | HardwareX §7.4, ICPS §5, CPN §2 |
| Cooling equilibrium | 13.6 °C cabinet at 21.6 °C room (Δ = 8.1 K) | `memory/cooling-capacity-tests.md`, tests 2026-02-26/27/28 | HardwareX §7.1, ICPS §4.4 |
| Deepest cabinet temp achieved | 12.3 °C | Same | HardwareX §7.1, ICPS §4.4 |
| Target temp envelope | 12–24 °C (Colombian curve, clamped) | `memory/freezer-baseline-255-temp.md` | All |
| Humidity operating envelope | **75–95 %** (floor 75 % since 2026-04-30, cap 95 %) | `memory/humidity-target-floor-80.md` | All — supersedes any "60–90 %" or "70–95 %" wording in older drafts |
| Photoperiod range | 10–14 h (clamped from Chinchina at 4.98 °N, centred on 13:15 CEST solar noon) | `memory/light-curve-c.md` | HardwareX §6.2, ICPS §2.4 |
| Light curve regime | **Raised cosine since 2026-05-04** (Curve C), floor=35 / peak=70 PWM at solar noon | `memory/light-curve-c.md` | HardwareX §6.2, ICPS §2.4 |
| **PPFD at canopy** | **PENDING DIRECT MEASUREMENT** (PAR sensor not yet installed). The "+23 % DLI" figure derived from PWM-curve integration is for *internal tuning record*; it must not appear in the final papers. Paper-grade numbers require: PPFD at upper canopy + lower canopy, midday peak and noon-integrated DLI in mol·m⁻²·d⁻¹, measured with a quantum sensor. | All papers — flag as a pending experiment before submission |
| Effective max LED draw | ~280 W LED + ~30 W base = **~310 W during peak ramp** | Cross-check ledger p95 + cabinet wiring | HardwareX §4.2 + §7.7 |

### 1D. Collection-wide totals (informational only — NOT cabinet)

For completeness, the broader plant collection (used only in passing acknowledgments, never as the headline figure):

| Group | Living count |
|---|---:|
| Highland cabinet | 76 |
| Outdoor | 82 |
| Windowsill | 75 |
| Shelves (other indoor) | 43 |
| Other / seasonal / blank | ~17 |
| **Total alive across all locations** | **~293** |

The ledger's "380 plants × 0.36 g/day" CO₂-scrubbed estimate is a coarse, model-based number that approximates the wider collection plus some duplicate counts; **do not cite it as a cabinet figure**.

### Decisions needed before this table is locked

- **Continent count.** The collection.csv supports "4 continents" cleanly (S America, Africa, Asia, Oceania). Older drafts may say 5. Should I change all to 4, or do you want to count North America somewhere (e.g., *Phragmipedium* extending into Central America)?
- **Cabinet vs collection framing.** The papers should consistently say "76 accessions across 32 genera in a ~1 m³ cabinet" rather than "120 species, 440 accessions across 5 continents". Confirm.
- **May 2022 start date.** All drafts should align on "May 2022 → present, four years of continuous operation". Confirm.
- **Pending experiment: PPFD measurement.** Buy/borrow a quantum PAR sensor and measure: (i) PPFD at upper canopy under Curve C peak; (ii) PPFD at lower canopy under same; (iii) daily DLI in mol·m⁻²·d⁻¹ (integrate the curve over the photoperiod). These are *the* numbers reviewers will look for in HardwareX §7.1 and ICPS §4.1. The "+23 %" figure is for the internal experiment log only.
- **No-deltas rule (NEW).** Drop all "+X % vs previous" framings from the papers. Report final operating-state numbers (PPFD, DLI, kWh/day, fog hours, mist cycles/day) as the *measured present-day reality* of the cabinet. The papers are about *what the cabinet is and does*, not about iterations of the controller. Internal change-history belongs in the operational memo / website blog, not the paper.

---

## 2. HardwareX draft survey

### 2A. Promote (new content to add)

| New material | Insertion point | Word budget | Source |
|---|---|---:|---|
| **Custom serial protocol** (replaced Firmata 2026-02-16) | §5.6 Arduino Firmware — add a paragraph; §2.7 Hardware Description — note text-based protocol with `P<pin>,<val>` syntax | ~200 | `memory/changes-feb16-17.md` |
| **Door safety mode** | §6.6 Safety Considerations — replace generic safety text with the door-open → fans off / freezer off / light 60 % chain + 3 s debounce | ~250 | `memory/door-safety.md`, `changes-feb16-17.md` |
| **Three-regime fan control with WBT gate + lights-off latch** | §7.3 — expand. The 2026-05-07 freezer-latch addition (wbt gate now requires freezer-on at least once after lights-off) is novel and worth a paragraph | ~250 | `MEMORY.md` "Lights-off Fan Gate" section |
| **Freezer daytime gate** (2026-04-11) | §6.6 + §7.6 — describes how runaway-cooling is bounded by an 08-20 CEST hard gate | ~150 | `memory/freezer-daytime-gate.md` |
| **Health-monitoring & STUCK RELAY safety chain** | §6.6 + §7.6 — terrarium-health.py cross-check, hysteresis, transition-window guard, fresh re-poll. Just landed today; complete in `docs/architecture.md` already | ~300 | `memory/terrarium-health-stuck-relay-fix-2026-05-11.md` |
| **Manual-mode 30-min watchdog** | §6.6 — operator-override timeout pattern. Mention the 2026-05-09 incident motivation (14 h fans-off near-miss) anonymised as "an operator-input persistence failure mode" | ~200 | `memory/manual-fan-mode-30min-revert.md` |
| **LED fault watchdog + transient counter** | §7.6 — driver-output anomaly detection (300-380 W "cap-limited" mode, sustained vs transient). Hardware paper context: failure mode of dim-line connectors on Mean Well drivers | ~250 | `memory/led-fault-watchdog.md`, `memory/led-transient-counter.md` |
| **Light Curve C** (raised cosine since 2026-05-04) | §6.2 Daily Operation — replace the "three-step 40-60-40" wording with the raised-cosine description; cite +23 % DLI redistribution | ~200 | `memory/light-curve-c.md` |
| **Regime-aware mister + audit findings** | §6.2 + §7.6 — humidity-driven trigger (≥1 day / ≥2 night), 10 s day / 20 s night durations. Cite the 2026-05-11 audit conclusion: **don't tune to per-event Δ; tune to operating point**. Ceiling-effect at high baseline RH. | ~350 | `memory/mist-tuning-audit-2026-05-11.md` |
| **Snapshot publishing pipeline** | New §6.7 or appendix — Tailscale Funnel + conditions-server + render pipeline. Justifies the website cross-references | ~250 | `memory/snapshot-publishing-pipeline.md` |
| **Weather staleness fallback** | §6.1 + §7.5 — historical curve fallback when OWM pipeline goes stale (>10 min) | ~150 | `memory/weather-staleness-fallback.md` |
| **Cooling test 2026-02-26/27/28 results** | §7.1 — table of T(t), equilibrium, deepest, recovery. Already implicit but formalise it | ~150 | `memory/cooling-capacity-tests.md` (file exists per paper-status.md) |
| **Power consumption ledger** | §7.7 — replace any estimate with the actual measured numbers from the public ledger (mist cycles, kWh, fog hours, water reservoir) | ~200 | `website/data/ledger.json`, ledger captions |

### 2B. Demote (move to website + link)

| Current content | Why demote | Replace with |
|---|---|---|
| §4 Bill of Materials full table (rows 99–175) | Long, will rot, hard to maintain in two places | Short BOM **summary table** (categories + ~6 headline items + total cost) → "Full machine-readable BOM and live links at `<website>/highland/docs/architecture/#bom`" with Zenodo DOI of frozen snapshot |
| §5.1 Enclosure Construction step-by-step photos | Better served by website photo gallery | One photo + "Step-by-step construction with photos: `<website>/highland/photos/`" + Zenodo DOI |
| §5.2 Hardware Assembly (the dimmer board, sensor mounting details) | Detailed in `panel-drawings/` already; website has the drawings | Inline summary figure (the panel drawing) + "Detailed assembly photos and CAD files: `<website>/highland/docs/`" |
| §5.3 Electronics Wiring full pin-by-pin table | Reference material, not narrative | Short table of *interface families* (Arduino PWM, Tapo plugs, ESP8266 MQTT) → "Full pin assignments: `docs/architecture.md` + Zenodo" |
| §5.4–5.7 Software Installation step-by-step | Will date faster than the paper; better as a website how-to | One paragraph "Software stack: Node-RED v3.1.3 + InfluxDB 1.8 + Grafana 10.2 + Mosquitto on Raspberry Pi 4." → "Install guide at `<website>/highland/docs/architecture/`" |
| §6.5 Troubleshooting | Operational, will accumulate | Move entirely to website; paper notes "Troubleshooting and known operational anomalies maintained at `<website>/highland/docs/operations/`" |

### 2C. Cross-ref (insert pointers without removing)

| Section | Pointer to add |
|---|---|
| Abstract / end | "Live system status, photos, and operational blog at `<website>`; archival Zenodo snapshot at DOI `<TBD>`." |
| §1 Hardware in Context | "Detailed species inventory and per-genus rationale: `<website>/collection/`" |
| §2 Hardware Description | "Live conditions JSON + dashboard PNGs at `<website>/highland/live/`" |
| §6.3 Dashboard Monitoring | "Public mirror of the operator dashboard at `<website>/highland/dashboard/` (refreshed every 15 min via Tailscale Funnel)" |
| §7 Validation | "Real-time validation data continues to accrue; archived analysis scripts and CSVs at `<website>/highland/docs/` and the repository's `analysis/`" |

---

## 3. CPN draft survey (Carnivorous Plant Newsletter)

Scope reminder: *Heliamphora*, highland *Nepenthes*, *Utricularia* sect. *Orchidioides*, *Brocchinia reducta*. Academic horticultural framing.

### 3A. Promote

| New material | Insertion point | Word budget | Source |
|---|---|---:|---|
| **3-year cultivation record updated to 4 years** | §1 Intro + §5 Discussion — change "three years" to "four years (since May 2022)" | trivial | Memory correction |
| **First-bloom record of *Utricularia quelchii*** | §3 Species Cultivated → expand the *U. quelchii* subsection. Two-flower opening at Day 21 was a milestone | ~250 | `website/content/blog/first-bloom-utricularia-quelchii/` |
| **Mold incident + deep-clean protocol** (2026-04-30) | New §5.x or §2 maintenance subsection — first deep clean after 4 years, traced to a single dead fan creating a stagnant corner. Physan-20 protocol | ~300 | `memory/deep-cleaning-2026-04-30.md`, blog post |
| **Evaporator cleaning protocol** | §2 Materials/Methods or §5 Discussion — first cleaning of the cooling-coil after 4 years; before/after photos and effect on cooling capacity | ~200 | `memory/evaporator-cleaned-2026-04-30.md` |
| **No-dry-rest tradeoff with revised data** (4 years now) | §5 Discussion — extends the existing tradeoff section with concrete flowering vs survival data | ~250 | Existing memory + species notes |
| **Heliamphora flowering & growth data** | §3 + §4 — pull what's in the website species pages | ~300 | `website/content/collection/genera/heliamphora/`, individual species pages |
| **The Light Curve C experience for high-light *Heliamphora* and lowland *Nepenthes*** | §4 — note the +23 % DLI move and the expectation that 2026-05-25 followup will quantify the response | placeholder, fill 2026-05-26 | `memory/light-curve-c.md` |

### 3B. Demote

| Current content | Why | Replace with |
|---|---|---|
| §2 Materials and Methods full hardware description | Mostly duplicates HardwareX | One paragraph summary + "Full hardware paper: companion HardwareX submission, DOI `<TBD>`. Live system and full BOM at `<website>`" |
| §3 long taxonomic descriptions | Will compete with monographs | Tighten to *cultivation-relevant* features only; full taxonomic detail + photos at website species pages |

### 3C. Cross-ref

| Section | Pointer |
|---|---|
| §3 each species subsection | "Per-accession photos and provenance: `<website>/collection/{genus}/{species-slug}/`" |
| §4 Environmental Results | "Live conditions stream and 12-month dashboards at `<website>/highland/dashboard/`" |
| End | "Cabinet build, full BOM, and operational blog at `<website>`" |

---

## 4. AoS draft survey (American Orchid Society — *Orchids*)

Scope reminder: popular/horticultural, first-person, orchids only (*Dracula*, *Masdevallia*/*Restrepia*, rupicolous *Cattleya*, *Dendrobium* sect. *Oxyglossum*, *Phragmipedium*).

### 4A. Promote

| New material | Insertion point | Word budget | Source |
|---|---|---:|---|
| **Species of the Week vignettes** (3 published so far) | §The Orchids → integrate the *Dracula pholeodytes*, *U. quelchii* (also orchid-adjacent), and *Heliamphora* (carnivorous, but the SOTW format is the model) stories | ~400 total | Three SOTW blog posts |
| **The afternoon humidity-creep diagnosis story** (Light Curve C blog) | §Lessons Learned — perfect anecdote: chasing a fan problem that turned out to be a lighting problem | ~300 | `website/content/blog/light-curve-c/` |
| **The four-year mold story** | §Lessons Learned — opening hook for the "what you don't see until you empty the cabinet" lesson | ~250 | Deep-clean blog post |
| **Restrict humidity discussion to the practical range that orchid growers care about** | §How the Weather Simulation Works | ~150 | Operating envelope from §1 here |

### 4B. Demote

| Current content | Why | Replace with |
|---|---|---|
| §The Setup hardware bullet list | Not what *Orchids* readers want | One paragraph: "Compressor-cooled cabinet with weather-driven setpoints. Build details at `<website>` and in the companion HardwareX paper." |
| §How the Weather Simulation Works technical detail | Same | Keep the *idea* (15 h time-shift, Colombian highland data); demote the implementation specifics to the linked HardwareX paper |

### 4C. Cross-ref

| Section | Pointer |
|---|---|
| §The Setup | "Full build, photos, dashboards: `<website>`" |
| Each species subsection | Link to website species page |
| §Resources | "Live conditions: `<website>/highland/live/`; growth/flowering blog: `<website>/blog/`" |

---

## 5. ICPS draft survey (comprehensive synthesis)

Scope reminder: full convergent cloud forest narrative — all 9 species groups + technical. The most paper-heavy draft.

### 5A. Promote

ICPS gets the **superset** of what HardwareX, CPN, AoS each get individually, since it's the synthesis paper. Additionally:

| New material | Insertion point | Word budget | Source |
|---|---|---:|---|
| **Convergent cloud-forest framing now demonstrably tested across 4 years** | §1 + §6 — strengthen the convergence argument with the 4-year operational record | ~300 | Combine memory entries + ledger |
| **All operational learnings (mist audit, ceiling effect, fan baselines, watchdogs)** | §2.6 + §4.3 + new §4.6 "Operational Learnings" | ~1500 | Memory + new §4 |
| **Phenological observations table** — expand with 4 years of bloom dates per species | §4.5 — currently exists, needs the 2025-26 data | ~400 | Species pages + observations |
| **Cross-continental morphological convergence note** — tepui *Heliamphora* / Andean *Masdevallia* / PNG *Dendrobium* / Bornean *Nepenthes* all share micro-climate envelope; the cabinet *demonstrates* that envelope is sufficient | §6.1 + §6.2 — sharpen | ~250 | Existing draft + new framing |
| **Dendrogram / phylogenetic distance vs co-cultivation success** | §6.x — if Mac-Claude's dendrogram has the data, frame as "phylogenetically distant species cohabit fine when the *micro-climate* converges" | placeholder | `website/content/collection/dendrogram/` |

### 5B. Demote

| Current content | Why | Replace with |
|---|---|---|
| §2.2 Hardware Components long table | Duplicates HardwareX | "See companion HardwareX paper, DOI `<TBD>`; full BOM at `<website>`" |
| §2.3 Climate Simulation implementation detail | Same | Conceptual paragraph; implementation in HardwareX |
| Long taxonomic enumerations in §3 | Will compete with monographs | Cultivation-relevant + key references only |

### 5C. Cross-ref

| Section | Pointer |
|---|---|
| Throughout §3 | Per-species cross-refs to website species pages |
| §4 | Dashboard + ledger cross-refs |
| §7 Conclusions | "Open-source build, live data, and operational record continue at `<website>`" |

---

## 6. Website cross-reference inventory

What's currently on the website that the papers can point to (verified 2026-05-11):

| Path | Contents | Paper relevance |
|---|---|---|
| `/highland/_index.md` | Section landing | All papers can link from §1 |
| `/highland/docs/architecture/` | Auto-synced from `docs/architecture.md` | HardwareX §5, ICPS §2 |
| `/highland/docs/pid-controller/` | Synced from `docs/pid-controller.md` | HardwareX §7.2, ICPS §2.6 |
| `/highland/docs/flows/` | Node-RED flow narrative | HardwareX §5.5 |
| `/highland/dashboard/` | Live Grafana snapshot | All papers §4/§7 |
| `/highland/live/` | conditions.json snapshot | All papers |
| `/highland/photos/` | Build and interior photos | HardwareX §5.1 |
| `/highland/webcam/` | (placeholder — hardware TBD) | Future |
| `/inventions/zeer-pot-darlingtonia/` | Zeer pot for *Darlingtonia* | CPN (companion experiment) |
| `/inventions/drosera-regia/` | *Drosera regia* setup | CPN (companion) |
| `/inventions/easier-environments/` | Simpler companion cabinets | Mention in ICPS §6 |
| `/collection/_index.md` | Section landing | All §3 |
| `/collection/dendrogram/` | Phylogenetic tree visualization | ICPS §6 |
| `/collection/genera/{genus}/` | Per-genus pages | CPN, AoS, ICPS §3 |
| `/collection/species/{species}/` | Per-species pages | CPN, AoS, ICPS §3 |
| `/collection/wishlists/` | Want lists | Mention in conclusions |
| `/blog/first-bloom-utricularia-quelchii/` | *U. quelchii* flowering record | CPN §3 |
| `/blog/highland-cabinet-deep-clean/` | 4-year mold + deep clean | CPN §5, AoS lessons, HardwareX §6.4 |
| `/blog/light-curve-c/` | Lighting redesign | HardwareX §7.1, ICPS §4.1, AoS lessons |
| `/blog/species-of-the-week-*/` × 3 | SOTW vignettes | AoS, CPN |
| `/blog/welcome/` | Site intro | All — mention in acknowledgments |
| `/data/ledger.json` | Mist cycles / kWh / fog hours, refreshed weekly | HardwareX §7.7, ICPS §4 |
| `/data/collection.csv` | Canonical accessions list | All §3 |

---

## 7. Open questions / decisions needed from user

1. **Zenodo deposit strategy.** Pick one before any "see `<website>`" reference goes into a draft:
   - **Option A**: Single Zenodo deposit at submission, snapshot of `website/` + `paper/<this-draft>/` + `nodered/` + `firmware/` + `analysis/`. Cite once in §1.
   - **Option B**: Three Zenodo deposits — one per major artefact (website snapshot, code repo state, data tables). Cite each separately.
   - **Option C**: GitHub release tag only, no Zenodo. Tradeoff: not archival.
2. **4-year vs 3-year framing.** All drafts to be updated to "May 2022 → present (4 years)"? Confirm.
3. **Order of submission.** If HardwareX is the "system paper" everything else cites, draft order should be HardwareX → CPN → AoS → ICPS. Confirm.
4. **Authors + affiliations.** Still placeholders in all 4 drafts. Will affect acknowledgments.
5. **Website's Italian language coverage** (about half the pages have `.it.md`) — should the papers acknowledge it, or treat the EN version as authoritative for citations?
6. **The 2026-05-09 fans-off incident** as a documented near-miss: include it in HardwareX §6 (Operation/Safety) as a "real-world failure mode and its mitigation" case study? It's a strong story for the safety chain.
7. **Light Curve C 2026-05-25 followup** — the 3-week experiment finishes mid-month. HardwareX §7.1 and ICPS §4.1 should wait for that data before final draft.

---

## 8. Suggested execution order

Once decisions above are made:

1. **Pass A (shared numbers, 1-2 h):** update the consistency table across all 4 drafts. Mechanical edits; low risk.
2. **Pass B (HardwareX, 4-6 h):** the system paper is the cite-anchor for the other three. Promote + demote + cross-ref. Land first.
3. **Pause for 2026-05-25 Light Curve C followup data.**
4. **Pass C (ICPS, 4-6 h):** synthesis paper. Inherits HardwareX's restructured methods sections by reference.
5. **Pass D (CPN, 2-3 h):** narrower scope, mostly need the §3 species expansions + the mold/clean story.
6. **Pass E (AoS, 2-3 h):** narrative tightening + linking. Light edits because it's the popular piece.
7. **Final pass:** Zenodo deposits, DOI insertions, cross-paper consistency check.

Estimated total: **15-22 h** of focused work spread over 2-3 weeks after the 2026-05-25 followup data is in.

---

## 9. Items NOT included in this survey (out of scope)

- Author lists, affiliations, funding statements — user decisions.
- Figure preparation — separate pass after textual edits land.
- Translation of any paper into Italian — website is bilingual; papers will be EN only unless user says otherwise.
- Mac-Claude's territory: photo selection, dendrogram visualization, Zeer pot page detail. Cross-references *to* those pages are listed above; the pages themselves are out of scope for this survey.

---

*Survey produced by Pi-Claude, 2026-05-11. Pair with `memory/paper-status.md` (which lists the pre-2026-03-08 baseline) to see the full picture.*
