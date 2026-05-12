# Mac-Claude counter-review of round-2 Codex pass — 2026-05-13

## Frame

Round-2 Codex pass dispatched 2026-05-13 against the four Pass-B drafts
(`hardwarex.md` f482a40, `aos-paper.md` f2c10fb, `cpn-paper.md` caf5c8a,
`icps-paper.md` b41f62a). Each brief listed the Pi-Claude reversals + the
energy SoT + the round-1 reviews + my counter-review as priors to keep
Codex from re-litigating closed items.

20 attacks total: 5 BLOCK, 14 MAJOR, 1 MINOR.

This memo verifies each attack against primary sources / repo state /
arithmetic, labels each **ACT / ADDRESS / ACKNOWLEDGE**, surfaces what
Codex missed, and flags the items Pi-Claude or the user must adjudicate.

Source-of-truth files used for verification: `paper/energy_sot_2026-05-12.yaml`,
`website/static/data/collection.csv` (filter `location=highland AND status=alive`
after my A. somalensis fix — commit `1375a25`), `docs/schema.md` (= 33 after
Pi-Claude's e621435), `scripts/arduino-watchdog.sh` (= v10 after f17ac63),
`scripts/terrarium-health.py` (= deployed copy after e621435), Crossref API
for citation existence, POWO + IOSPE for taxonomy where applicable.

---

## A. HardwareX (5 attacks, 2 BLOCK + 3 MAJOR)

### A.1 — BOM still placeholder-heavy ⇒ **ACT** (Codex right)

`[PLACEHOLDER]` is in every BOM cost / source / quantity cell (§4.1–§4.7, L114–186) and in the §1 Specs Table cost row (L18). HardwareX policy requires a complete BOM. The author has receipts in `Plant_Inventory.xlsx`, in Gmail vendor history, and on vendor sites (Vitrifrigo, Noctua, ChilLED, Mean Well, MistKing, Tapo, Meross, Raspberry Pi, Arduino, SHT35, HC-SR04P). This is mechanical extraction, not blocked by anything external. Pre-submission must-fix.

### A.2 — Design files not publication-grade ⇒ **ACT** (Codex right)

All `Location` cells in §3 (L73–88) say `[Zenodo DOI — TBD]`. Acrylic panel drawings are `S6-panel-drawings-*.docx`. HardwareX's reviewer guide explicitly prefers open CAD formats (STEP / DXF / SVG) so a builder in another lab can reproduce panels without owning MS Word. Wiring schematic placeholder at L343, assembly photos at L242 / L459. None of this can be deferred past submission: HardwareX bounces manuscripts with PLACEHOLDER design files. The Zenodo deposit is a single-evening task once the BOM is done.

### A.3 — 94-day vs 80.3-day window contradiction ⇒ **ACT** (Codex right)

Three different windows are now in §7 and they collide:

- §7.1 L557 "Over the current 94-day monitoring window"
- §7.6 L619 "Beyond the serial watchdog ... 94-day Meross-instrumented window"
- §7.7 L630 "The 94-day Meross-instrumented window (2026-02-04 → 2026-05-10) yields:"
- §7.7 L634 (in the same table) "Total energy logged ... 211.41 kWh over 80.3 days (2026-02-18 → 2026-05-10)"
- §7.6 L626 "The system's operating uptime ... was 99.4 % over the 94-day window"

The conditions/sensor data does cover ~94 days (InfluxDB `since` = 2026-02-04). The Meross power data covers ~80.3 days (daemon start 2026-02-18). The two are different windows and the manuscript currently calls both "the 94-day Meross-instrumented window." Pass-C: each numeric claim must declare its actual window. Suggest the §7 header reads "two monitoring windows — full sensor (94 d) and Meross-instrumented (80.3 d) — are reported separately below."

Note: §6.2 L493 still says "32 total" measurements (stale; schema now 33). Mechanical fix.

### A.4 — 99.4 % uptime + late-deployed fixes ⇒ **ACT** (definition) + **ADDRESS** (scoping)

Two distinct sub-attacks:

(a) **Definition.** "99.4 % uptime" needs to state the denominator (per-minute samples?), the numerator definition ("Arduino watchdog healthy" — by what check?), and the exact Flux/SQL query. Reviewers will ask. The author can pull this from the watchdog systemd log or from an InfluxDB query against the heartbeat measurement.

(b) **Scoping.** §7.6 L623 admits the manual-override timeout was added on 2026-05-09 — one day before the monitoring window cutoff (2026-05-10). §7.6 L621 admits the STUCK-RELAY hardening landed 2026-05-10/11. These cannot underwrite a "94-day window" claim. Rewrite the safety-chain section as either "evolution of the safety chain over four years" (with deployment dates per layer) or "current configuration since 2026-05-11" (a much shorter validation window). The first option is more honest and matches the four-year-operation framing of the abstract.

### A.5 — Stats missing ⇒ **ACT** (Codex right)

§7.2 L579 IV/2SLS: -0.37 % humidity per +10 PWM, p < 0.05. Needs N, first-stage F (weak-instrument check), 95% CI, exclusion-restriction defence (one paragraph: the day-of-experiment indicator is plausibly exogenous to humidity-residual because the schedule was set before any individual day's humidity was observed). The `analysis/02_iv_causal_model.py` script presumably outputs these; user must run + paste.

§7.4 L597–605 heat-balance table: needs N (hours), SEs / 95 % CI per row, R², and the model formula (presumably `dT/dt = α·freezer + β·fan + γ·(T_terr - T_room) + ε` or similar). The `analysis/01_heat_balance.py` script is in the repo.

Same fix carries over to ICPS §4.3 / §4.4.

---

## B. AoS *Orchids* (5 attacks, 1 BLOCK + 4 MAJOR)

### B.1 — CITES / provenance wording ⇒ **ACT** (Codex right, with nuance)

Three problem strings:

- L81 "*S. pygmaea* (Brazil import)" — Brazilian *Sophronitis* are CITES App. II. "Import" without explicit "CITES-permitted artificially-propagated specimen via [licensed dealer]" reads as smuggling-adjacent to AOS readership. The user knows the actual chain of custody (Grossräschener Orchideen per collection.csv, both lost) — restate with the licensed vendor name and "artificially-propagated."
- L95–99 *P. kovachii* — CITES App. I. "Legally-acquired horticultural propagation" doesn't name the source or permit chain. Collection.csv id=420 says Ecuagenera, Nov 2022, €114.24 — that's a licensed dealer with CITES paperwork. State that explicitly: "acquired November 2022 from Ecuagenera (Ecuador) under the standard licensed-dealer CITES paperwork for artificially-propagated *Phrag. kovachii*." This removes the legal-credibility ambiguity entirely.
- L163 "the cabinet's role as ex-situ refuge for moisture-dependent species" — Codex flags that "ex-situ refuge" is over-claim. Strictly, the cabinet is private cultivation, not a recognised ex-situ conservation programme. Soften to "cultivation context" or "long-term private cultivation."

### B.2 — *P. kovachii* / *Restrepia* inventory contradiction ⇒ **ACT** for ICPS, not AoS

The AoS draft is right (collection.csv id=420 P. kovachii alive in highland, id=419/421/422 three *Restrepia* alive in highland). The ICPS draft's §3.5 USER_INPUT block at L226 ("Any Restrepia species? (None found in inventory)") and L249 ("Are any Phragmipedium in the terrarium? (None found in inventory)") is the bug. Whoever wrote ICPS §3.5 missed two species groups. Pass-C: replace both ICPS USER_INPUT lines with the cultivation entries.

Aside: the AoS draft's "Three *Restrepia*" claim (L73) names *vasquezii*, *sanguinea*, *trichoglossa var. xanthina* — all three are id-confirmed in collection.csv. Photo coverage: 2 of 3 photographed (no *R. trichoglossa* photo on Mac side — gap, see §F).

### B.3 — Not orchid-led enough for *Orchids* ⇒ **ADDRESS**

The opener "It started with a simple question: what if my terrarium could experience real cloud-forest weather?" is concept-led, not orchid-led. AOS *Orchids* readers want a story that opens with an orchid. The single best opener material the cabinet has is the *Sophronitis coccinea* 'Big One' × 'Hinomaru' 4N GM/WOC bloom — the article should open with a sentence about it (the photo is already rank 1), then unfold the cabinet context. Demote the Utricularia-bloom "most striking individual result" line at L113 to a "Notable non-orchid highlight" sidebar or remove. Pi-Claude or user to rewrite the opener; structural change but small (~10 lines).

### B.4 — Light-gradient overclaim ⇒ **ADDRESS** (soften, don't measure)

"Three distinct growing environments for free" (L111) and "geometry rather than separate fixtures" (L25) are over-confident without PPFD numbers. But AOS isn't HardwareX — PPFD measurement is not a submission requirement. The honest fix is wording, not measurement: "a coarse three-tier light gradient" or "three meaningfully different light levels" instead of "three distinct growing environments." Direct PPFD measurement is already flagged in HardwareX §7.1 as pending the quantum sensor.

### B.5 — Dry-rest Cattleya paragraph cedes ground ⇒ **ACKNOWLEDGE**

L83 "Both have been alive and growing in the cabinet — slowly, no flowering yet" and L117 "No dry rest means some losses." Codex's attack: this hands skeptics their objection. But this is **intentional honesty** that an AOS audience values. *aclandiae* / *walkeriana* under year-round moisture is a deliberate horticultural choice with documented tradeoffs, and the article should be honest about it. Pass-C can tighten by leading with positive results (Sophronitis blooming, miniature Pleurothallidinae sequential bloom, Dracula simia / lotax repeat flowering) before the Cattleya admission — but the admission itself stays.

---

## C. CPN (5 attacks, 1 BLOCK + 3 MAJOR + 1 MINOR)

### C.1 — *Heliamphora* §3.1 PLACEHOLDER + count conflict with ICPS ⇒ **ACT** (Codex right)

CPN abstract L11 says nine. ICPS §3.1 table lists ten and says "All ten plants are alive" (ICPS L161). Collection.csv ground truth: 9 alive in highland after my A. somalensis edit. The ICPS table includes "*H. macdonaldae* — Adult leaves; ~1 yr waiting list" (L156) which is a waiting-list specimen, not a current cabinet plant. ICPS table must drop that row to land at 9. CPN §3.1 must be backfilled with the same 9 entries (taxon, provenance, vendor, residence-time-since-acquisition, observed pitcher production cadence, photographs) — the author has the data; the placeholder block at L96–119 needs user input. This is the highest-priority CPN gap.

### C.2 — Four-year claim folds in recent acquisitions ⇒ **ADDRESS**

§1 L11 "four years (May 2022 to present)" is the system framing — true; the cabinet has run four years. But §3.2 *N. jamban* alive since Nov 2025 (~6 mo); §3.3 *U. quelchii* since early 2023 (3 yr); some Sumatran *Nepenthes* since 2016 (10 yr). The four-year claim is for the cabinet, not for each accession.

Pass-C fix: add a single sentence in §1 or §3 introduction — "Cabinet residence times across the current 75 accessions range from 10 years (*N. inermis*, March 2016) to 6 months (*N. jamban*, November 2025); the four-year framing refers to continuous system operation." Then the headline framing is honest without contradicting the discussion.

### C.3 — Climatology citations not clearly supporting cited claims ⇒ **ADDRESS**

Verified via Crossref:

- Adlassnig 2010 — `doi:10.1590/s1516-89132010000200022`, *Brazilian Archives of Biology and Technology* 53(2):425–430. Real paper. The title scopes it to "*Heliamphora nutans* ... on Roraima Tepui." So:
  - CPN L194 cites Adlassnig for "Bogota (2,640 m) shows a similar ~12 deg C diurnal range" — but Adlassnig doesn't discuss Bogotá. Citation misattribution; remove the citation from that Bogotá sentence or replace with a Colombian-meteorology source.
  - Adlassnig support for Roraima 15–21 / 5–13 deg C bands is presumably in the paper; verify on read.
- Jarvis & Mulligan 2011 — `doi:10.1017/cbo9780511778384.005`, "The climate of cloud forests," in *Tropical Montane Cloud Forests: Science for Conservation and Management* (the Bruijnzeel et al. volume). Real chapter, year 2011 (CPN cites it as 2010 — minor edit). Whether it reports the specific "50–80 % nighttime cloud immersion" figure (CPN L236) is plausible but unconfirmed; the chapter is WorldClim-based and does report cloud-immersion frequencies. User should pull the chapter and verify the exact number; if not in this chapter, swap citation to one of the volume's other chapters or to Bruijnzeel & Veneklaas 1998 *Ecology*.

In neither case did Codex find a hallucinated citation — both exist. The issue is precision of attribution. Pass-C cleanup.

### C.4 — Wet-bulb result over-scoped ⇒ **ACT**

CPN §5.3 L248: "the system's data show approximately +0.37 deg C/hr of fan-attributable warming once the terrarium temperature drops below the room wet-bulb temperature."

This conflates two HardwareX §7.4 results: (i) the global heat-balance fan coefficient = +0.37 deg C/hr (cabinet-wide, all conditions); (ii) the WBT-crossover interaction term, which is what describes the "once below WBT" regime, with the linear-fade reaching zero at +0.3 °C above WBT.

The +0.37 figure isn't a "below-WBT" quantity — it's a global one. The "below WBT" framing in CPN attributes a global coefficient to a regime-specific behaviour. Pass-C rewrite: "Above WBT, fans contribute a net evaporative cooling; below WBT, the same fans produce a net warming approaching the +0.37 deg C/hr sensible-heat injection rate" — or even cleaner, cite the HardwareX-style linear-fade model directly.

### C.5 — Deep-clean date self-contradictory ⇒ **ACT** (trivial)

CPN §5.4 L258: "In early 2026 (deep-clean episode of May 2026)." Internally contradictory. AOS L67 / L119: "early-2026." Mac-side asset evidence: `website/static/img/highland/interior/interior_2026-05-01_deep-clean.jpg` exists, dated 2026-05-01.

So the deep-clean cleanup happened ~early May 2026; the *cause* (fan crimp failure, mould accumulation, *D. pholeodytes* bud loss) developed across early 2026. Both papers should standardise on: "the mould accumulated through Q1 2026; the deep-clean cleanup itself was on 2026-05-01." Single-sentence fix.

---

## D. ICPS (5 attacks, 1 BLOCK + 4 MAJOR)

### D.1 — Collection boundary broken ⇒ **ACT** (Codex right, biggest item)

§3 must be rebuilt against `collection.csv` filtered `location=highland AND status=alive`. After my A. somalensis edit (commit `1375a25`), this filter returns exactly 75 rows across 31 genera, matching the abstract.

Specific known errors in ICPS §3:

- §3.1 *Heliamphora* table lists 10; should be 9. The "*H. macdonaldae* — Adult leaves; ~1 yr waiting list" row (L156) is a waiting-list specimen not currently in the cabinet. Drop or mark explicitly "ordered, not yet received."
- §3.2 USER_INPUT "Is Brocchinia reducta in the terrarium? (Not found in inventory)" (L180–181) — wrong; collection.csv id=413 *B. reducta* alive in highland. Replace.
- §3.4 *Dracula* table lists 4 (simia / lotax / vlad-tepes / pholeodytes); collection.csv has 6 in highland (add Raven 'Jet' hybrid id=396 and the ID-uncertain hirsuta/xanthina id=variable). AoS draft has the full 6.
- §3.5 USER_INPUT "Any Restrepia species? (None found in inventory)" (L223–226) — wrong; three Restrepia in highland (vasquezii, sanguinea, trichoglossa var. xanthina). Replace.
- §3.5 USER_INPUT "Are any Phragmipedium in the terrarium? (None found in inventory)" (L248–249) — wrong; *P. kovachii* id=420 alive in highland. Replace.
- §3.6 the body says "is represented in the cabinet by three living accessions" (L255, Oxyglossum count) but then the table at L262–271 lists 9 *Dendrobium* alive (which is the total Dendrobium count, not Oxyglossum). The text/table distinction is fine but should be explicit ("Three Oxyglossum + one Calcarifera (*D. victoriae-reginae*) + five other-section *Dendrobium* = nine alive accessions; see Table X").
- The §3.6 single-loss "*D. cuthbertsonii* was replaced successfully with a second clone" (L273) is correct (table shows the original Grossräschener lost, the Claessen 'Yellow' alive).

This is the single biggest Pass-C item. Time cost: ~60 minutes of careful CSV → manuscript transcription.

### D.2 — Convergence dataset selectively delimited ⇒ **ADDRESS**

ICPS abstract sells "75 accessions ... from convergent cloud-forest environments." But §3.2 mentions *Genlisea africana* (West African savanna, NOT cloud forest), Mexican *Pinguicula* (subtropical, not tropical-cloud), Asian *Drosera* (varied). And AOS L101–103 lists some smaller-representation genera (e.g., *Maxillaria sophronitis*, *Holcoglossum*, *Schoenorchis*) that span lowland-tropical and seasonally-dry biomes.

Defence: every cabinet has some companion species that tolerate the conditions without being native to the target biome. The thesis is climatic convergence of cloud forests, not biogeographic purity of the cohort.

Pass-C fix: add an honest sentence to §3 introduction — "Of the 75 living accessions, the great majority originate from tropical highland cloud-forest or tepui environments and represent the cohort on which the convergence claim is grounded; a small minority (e.g., some *Pinguicula*, *Genlisea africana*, and *Aerangis somalensis*) are companion taxa from neighbouring biomes that tolerate the conditions but are not part of the convergence cohort." The "75 accessions" headline stays; the convergence claim becomes scoped to the cloud-forest subset.

(Aside: *Aerangis somalensis* itself is no longer in the highland cabinet — fixed in commit `1375a25` — so the abstract / discussion no longer needs to handle it as a counter-example.)

### D.3 — Stale params ⇒ **ACT**

- §4.1 humidity-target row (L374) says "Weather-derived (clamped 70--90%)". §2.3 body (L90) says clamped 75–95 % since 2026-04-30. Table is stale.
- §6.5 (L475) and Supplementary Materials (L546) both say "32 InfluxDB measurements" / "(32 measurements)". Schema is 33 since e621435. Both stale.

Mechanical Pass-C fixes.

### D.4 — IV/2SLS + cooling-equilibrium claims ⇒ **ACT** + **ADDRESS**

Same IV/2SLS fix as A.5. Plus: the §4.4 "Maximum Cooling Capacity" table (L395–403) reports "cooling duration" of 9.5 / 9.5 / 9.9 h and calls Night 3's 13.6 °C the "equilibrium" minimum. A 9.9-h test isn't strictly an equilibrium — overnight thermal mass is still cooling. Either rename to "near-equilibrium" / "9-10h minimum" or run a 24-h test before claiming equilibrium.

### D.5 — No-dry-rest attrition pattern asserted, uneven ⇒ **ADDRESS**

§6.3 L458–462 says losses concentrated in dry-rest taxa "confirming that moisture tolerance rather than geographic origin determines compatibility." But the actual loss pattern doesn't support this cleanly:

- *Pinguicula* losses (P. primuliflora, P. gigantea) — tropical and Mexican, NOT dry-rest.
- *Masdevallia* losses (*coccinea* 'Anchota', *glandulosa*) — temperature/humidity mismatches, NOT dry-rest.
- *Sophronitis pygmaea* losses ×2 — humidity sensitivity, NOT dry-rest.
- *L. briegeri* lost on CITES import — customs failure, NOT dry-rest.
- *Genlisea* losses (3 of 4) — tropical lowland, NOT dry-rest.
- *D. cuthbertsonii* loss — moisture-loving Oxyglossum, NOT dry-rest.

Codex is right. The dry-rest narrative is over-tidy.

The defensible version: "Dry-rest demanding species (*Cattleya* alliance with strong dry-rest cues, *Dendrobium* section *Callista*) were excluded from the cabinet pre-emptively because the cabinet's continuous high humidity is fundamentally incompatible with their flowering cycle. The losses that did occur within the cohort reflect a heterogeneous set of cultivation incompatibilities (warm-growing species too cool, sun-loving species too shaded, *S. pygmaea* humidity sensitivity, *Genlisea* tropical-lowland species too cool, etc.), and not a single thematic cause." This is honest and more useful to a cultivator reader.

---

## E. What Codex missed (4 items)

### E.1 — CO2-scrub baseline uses the whole 380-plant collection, not the 75-plant cabinet

Found while running the ledger script. `data/ledger.json` reports:

```json
"co2_scrubbed": {
  "kg": 13.2,
  "method": "380 plants × 0.36 g/day × days_alive",
  "note": "model-based, not sensed"
}
```

The kWh figure is cabinet-only (Meross meters the cabinet power strip per `electricity.source`). All other ledger metrics are cabinet-only. But the CO2 figure uses the entire 380-plant collection (outdoor + windowsill + shelves + seasonal + highland). This is inconsistent: the homepage ledger reads as "the cabinet's environmental impact," and the CO2 row implies the cabinet scrubs 13.2 kg / 4.17 kg/month — that's the collection's claim, not the cabinet's.

Cabinet-only CO2 at 75 plants × 0.36 g/day × 96 d ≈ 2.6 kg total / ~0.8 kg/month.

This is a Pi-side calc bug. Surface to Pi-Claude. (None of the four manuscripts cite the CO2 number, so it's not a paper-Pass-C item, but it's a homepage-credibility item.)

### E.2 — HardwareX §3 design file table doesn't include `energy_sot_2026-05-12.yaml`-style file as a real Zenodo artefact

§3 L87 lists `paper/energy_sot_*.yaml` as a CERN-OHL-P-2.0 Design File. This is actually a SoT for the manuscript itself, not a hardware artefact. Whether HardwareX wants this in the design-file archive vs treated as a supplementary table is editor-dependent — pre-submission ask. If kept, the file name in the table needs the actual date suffix, not a glob.

### E.3 — §6.6 layered-safety chain has 9 numbered items in HardwareX but the four-year-evolution framing is buried

A reader wondering why a 4-year-running cabinet needs nine safety layers will assume each layer was added in response to a failure. The current §6.6 prose says so generically ("layered safety architecture has been developed in response to specific real-world failure modes") but doesn't date each layer. Pair this with the A.4 deployment-date scoping fix to produce a "failure-mode → safety-layer → deployment date" mini-table somewhere in §6 or §7.6. Substantially strengthens the credibility of the architecture.

### E.4 — None of the four drafts mentions the new `terrarium-health.py` Gmail / WhatsApp / CallMeBot alert chain in a credible way

HardwareX §6.6 #8 names `terrarium-health.py` and §3 design-files row references it, but doesn't describe what the operator-on-the-other-end experience is (Gmail subject lines? WhatsApp message format? the 30-min dedupe? the 6-h green digest?). For a system that "runs unattended for months at a time" this matters. The companion papers (CPN / AOS / ICPS) can each carry a one-sentence "the system pings me on Gmail + WhatsApp on any non-green condition" reassurance, especially for hobbyist audiences who worry about runaway compressor / mister failures while the operator is away.

---

## F. Pass-C action ladder

Drafts ranked by total round-2 attack severity (Codex's own BLOCK / MAJOR counts), with the cross-cutting items split out so the propagation work happens once:

**Cross-cutting (do these first):**

1. **§3 cabinet rebuild from `collection.csv`** (HWX implicit + AoS B.2 + CPN C.1 + ICPS D.1). 60–90 min user time. After this, all four drafts' §3 should agree.
2. **Energy-window phrasing standardisation** (HWX A.3). Sweep all four drafts for "94-day" → either "94-day sensor window" or "80.3-day power-window" as appropriate. Mechanical.
3. **Schema 32 → 33 sweep** (HWX implicit + ICPS D.3). Already fixed in `docs/schema.md`; needs sweep in all four manuscripts' supplementary / appendix mentions.
4. **Humidity-clamp 70 → 75** (ICPS D.3). One-line fix per draft.
5. **Deep-clean date** (CPN C.5). Standardise on "Q1 2026 development + 2026-05-01 cleanup."
6. **No-dry-rest attrition narrative rewrite** (ICPS D.5 + CPN implicit). Replace "losses concentrated in dry-rest taxa" with the pre-emptive-exclusion + heterogeneous-loss framing.

**Per-paper after cross-cutting:**

- **HardwareX**: BOM extraction (A.1) + design-file Zenodo deposit + CAD conversion (A.2) + stats addendum (A.5) + safety-chain timeline rewrite (A.4 + E.3). User-blocking on BOM + Zenodo.
- **AoS**: CITES wording fixes (B.1) + orchid-led opener rewrite (B.3) + light-gradient softening (B.4). All Mac-side prose work; the user can review at the end.
- **CPN**: §3.1 *Heliamphora* backfill (C.1, blocked on user for cultivation observations) + four-year clarification sentence (C.2) + Adlassnig/Jarvis-Mulligan citation precision (C.3) + wet-bulb +0.37 mis-scoping fix (C.4). C.1 is the dominant time cost.
- **ICPS**: §3 cabinet rebuild dominates (D.1, already in cross-cutting). Stats addendum (D.4) shares with HWX A.5. Convergence-scope honesty sentence (D.2). Cooling-equilibrium re-wording (D.4).

**Pi-side asks (separate HANDOFF section):**

- E.1 — `co2_scrubbed` plant-count bug (380 vs ~75).
- A.4(a) — uptime query / definition for the 99.4 % claim.
- A.5 — first-stage F + CIs for the IV/2SLS run.
- Citation-detail verifications where Adlassnig 2010 and Jarvis & Mulligan 2011 supply specific quantitative claims (CPN C.3).
- Whether the cabinet temperature can hold 24 h of equilibrium cooling for a proper D.4 max-cooling-capacity test (or accept the "near-equilibrium" wording).

**Photo coverage gaps (separate HANDOFF section, see counter-review §F continued below for the table):**

| AoS rank | Subject | Mac-side asset | Status |
|---|---|---|---|
| 1 | *Sophronitis coccinea* 'Big One' × 'Hinomaru' 4N GM/WOC | `sophronitis/sophronitis-coccinea-big-one-x-hinomaru-4n-gmwoc{,2,3}.jpg` | ✅ covered |
| 2 | Front-on wide cabinet shot, three growing tiers, lights-on | `highland/interior/interior_2025-02-15_IMG_0391.jpg` + 2026-04-20 coccinea-bloom + 2026-05-01 deep-clean | ✅ adequate; a fresh 2026 lights-on wide would be ideal |
| 3 | *Dendrobium cuthbertsonii* 'Yellow' close-up | `dendrobium/dendrobium-cuthbertsonii-yellow{,2..6}.jpg` | ✅ covered |
| 4 | *Dracula simia* or *D. lotax* flower close-up | `dracula/dracula-simia{,2}.jpg` + `dracula-lotax{,2..6}.jpg` | ✅ covered |
| 5 | *U. quelchii* April–May 2026 inflorescence | `utricularia/utricularia-quelchii-{2..16}.jpg` + `highland/interior/interior_2026-04-20_coccinea-bloom.jpg` | ✅ covered (-7, -9, -14 named in ICPS §3.3) |
| 6 | Cork-mount wall group shot | not directly mapped; some interior shots show the cork wall | ⚠️ probably covered by existing interior shots; may want a dedicated frame |
| 7 | *Dendrobium victoriae-reginae* flower | `dendrobium/dendrobium-victoriae-reginae{,2}.jpg` | ✅ covered (2 frames) |
| 8 | *Masdevallia* flower close-up | `masdevallia/masdevallia-decumana{,2..5}.jpg` + `devils-heart...` | ✅ covered |
| 9 | *Restrepia* hinged labellum | `restrepia/restrepia-vasquezii{,2}.jpg` + `restrepia-sanguinea{,2}.jpg` | ⚠️ 2 of 3 *Restrepia* photographed; no *R. trichoglossa var. xanthina* shot |
| 10 | *Phragmipedium kovachii* in vegetative growth | **no `phragmipedium/` directory exists on Mac** | ❌ **missing entirely** — directory not created |

Also gaps:

- **No `phragmipedium/` photo directory at all** despite `collection.csv` id=420 *P. kovachii* alive in highland. User to shoot or skip rank-10 photo.
- **Missing Heliamphora photos**: *H. minor* Clone 4, *H. pulchella* Akopan, *H. pulchella* Amuri — 3 of the 9 highland Heliamphora unphotographed.
- **Missing Nepenthes photos**: *N. inermis*, *N.* 'Fake Pitopangii', *N. micramphora* — 3 of the 9 highland Nepenthes unphotographed.
- **No *Restrepia trichoglossa var. xanthina* photo**.

The first three photos for the AoS plan are the high-impact ones (cover-bloom, cabinet wide, PNG miniature) and all are well covered. The largest gap is the *Phragmipedium* — if rank 10 must ship, user shoots one; if the article ships without rank 10, that's the cheapest path.

---

## G. Codex's overall posture, observed across both rounds

Codex round 2 is much more focused on **structural / cohort-accounting / window-consistency** issues than on the round-1 taxonomic and citation accuracy issues. The reason is that Pi-Claude's Pass-B closed the round-1 taxonomic gaps cleanly (*D. victoriae-reginae*, *Brocchinia reducta*, 15-h shift wording) — Codex couldn't re-attack those. What's left is the structural rigour layer: cohort denominators, residency-time framing, statistical reporting, BOM completeness, deployment-date scoping for safety-chain claims.

That layer is exactly what HardwareX / ICPS / CPN reviewers will hit hardest. The round-2 BLOCK + MAJOR labels are credible: a HardwareX referee will return Pass-B-as-is for revisions on the BOM and design-file gaps; an ICPS referee will return on the §3 cohort accounting; an AOS editor may bounce on the CITES-wording issue. Pi-Claude's Pass-B was a major step up from round-1 state; round-3 (Pass C) closes out the remaining structural and accounting work.

The counter-review's recommendation, given all this: do not start per-paper Pass-C until the cross-cutting items (rebuild §3 from collection.csv, energy-window phrasing standardisation, schema 33 sweep, attrition narrative rewrite) are done. Each cross-cutting fix lands in 1–4 drafts at once. After that, the per-paper polish work shrinks substantially.
