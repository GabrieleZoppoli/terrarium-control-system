# Adversarial review — `hardwarex.md` (state as of 2026-05-11)

**Reviewer stance.** I'm reading this as a HardwareX reviewer who *wants* the paper to publish — it's a strong system and the weather-mimicking framing is genuinely novel — but who will reject anything that obstructs reproducibility, overclaims the data, or doesn't reflect the current operating state of the system. I have access to the cabinet's live data, memory notes, and website (which a real reviewer would not, but the paper's *authors* do, so I'm flagging gaps the authors should close before submission).

Severity tags: **B**locking (cannot submit), **M**ajor (will trigger reviewer demands), **m**inor (polish), **n**it (copyedit). Every issue includes proposed fix.

---

## A. Numbers that contradict the verified state of the system (B)

These appear in the abstract and §1 and propagate everywhere. They will be the first thing a reviewer with access to your data flags.

| Where | Current text | Verified value (2026-05-11) | Fix |
|---|---|---|---|
| Abstract L25 | "approximately 120 cloud forest species from five continents" | **76 living accessions, 75 distinct taxa, 32 genera, 4 continents** | Rewrite the line. Use 76/32/4 and add the genus distribution (top 6: *Nepenthes* 9, *Heliamphora* 9, *Dracula* 6, *Sophronitis* 5, *Masdevallia* 5, *Dendrobium* 5). The "120" appears to count the entire collection, not the cabinet. **B** |
| Abstract L25 | "operated continuously for over three years" | **Four years (May 2022 → present)** | Change to "four years" or "since 2022". **B** |
| §2 L61 | "validated over 3+ years with ~120 species from five continents" | Same as abstract | Same fix. **B** |
| §5.2.2 L253 | "evaporator plate horizontally inside the **upper region** of the enclosure" | Evaporator is mounted **horizontally in the lower portion of the back wall** (~20 cm from cabinet floor per back-panel schematic `panel-03-with-radiator.png`). Cold air sinks naturally to the floor. | Rewrite paragraph + amend §5.2.2.2 ("near the top" → "in the lower portion of the back wall"). This is a structural error; reviewers will spot it the moment they see the photos. **B** |
| §7.1 table L521 | "Relative humidity target: clamped 70–90%" | Verified envelope is **75–95 %** (floor raised 2026-04-30) | Update the target column to 75-95 %. **M** |
| §1 L33 | "10–22 deg C, persistent high humidity (80–100% RH)" describing tepui native conditions | These are reasonable but cite Rull & Vegas-Vilarrubia 2006 directly for the numeric ranges; right now the citation is at the end of the paragraph and reads like a general claim | Add per-claim citation. **m** |

---

## B. Placeholder pollution (B)

The paper has **24 `[PLACEHOLDER]` markers** spread across BOM (cost, source), Zenodo DOIs (every design file row), figures (every Grafana screenshot, every photo), §7.7 Power Consumption (the *entire* section is a placeholder line), and references. As-is, the paper cannot be reviewed because the BOM is empty, no figures exist, and §7.7 is missing.

**Critical, in order of submission-blocking severity:**

1. **§4 BOM** — all unit costs, total costs, supplier links are blank. HardwareX *requires* a usable BOM. **B**
2. **§3 Design Files** — every Zenodo DOI is blank. Must deposit and link before submission. **B**
3. **§7.7 Power Consumption** — the entire body is a placeholder. You have **94 days of measured Meross data** (2.60 kWh/day, mean 109.9 W, p95 202.6 W, max 492.9 W, hour-of-day profile). The placeholder is the most embarrassing single gap; fill from `data/ledger.json` immediately. **B**
4. **Figures** — every "PLACEHOLDER — Grafana screenshot showing X" needs a real figure. You have the snapshot pipeline already running; pull from `/highland/dashboard/`. **B**
5. **Author names, affiliations, corresponding author, total cost** — must be filled for submission. **B**

---

## C. Claims that have shifted or were overstated (M)

### C.1 The "no published open-source system implements weather-mimicking control" novelty claim

§1 L39 makes the strongest claim in the paper. A reviewer will want this defended. Currently the paragraph names only "greenhouse automation platforms and plant growth monitoring systems" generically.

**Fix:** add a paragraph citing 3-5 *specific* prior open-source environmental controllers (HardwareX has several — search "growth chamber", "phytotron", "environmental control" in their archive). Show that each one uses **fixed setpoints, not weather-data-driven setpoints**, then position your work as the gap-filler. Without this, the novelty claim is unsupported. **M**

### C.2 The IV/2SLS result in §7.2 is from a now-removed experiment

§7.2 L534 cites:

> An IV/2SLS analysis using a controlled A/B experiment (alternating nightly fan-on/fan-off) as an instrument confirmed the fans' causal effect on humidity: each +10 PWM of fan speed causes a -0.37% reduction in humidity

This result is valid, but it comes from the **night-fan A/B experiment, which was suspended on 2026-02-18** (per `memory/morning-ab-experiment.md` and `MEMORY.md`). The paper reads as if the experiment is ongoing. A reviewer who checks the flows.json will find no active A/B logic.

**Fix:** rewrite as a single completed experiment, past tense, with the date range. Add a clear footnote that "the experiment was retired in February 2026 after the causal effect was characterized; the result is reproducible from the InfluxDB archive". **M**

### C.3 §7.4 wet-bulb heat-balance table

The temperature-effect numbers (−2.03 °C/h freezer, +0.37 °C/h fans, +0.58 °C/h passive) are presented without confidence intervals, without sample size, without R². A reviewer will demand:
- N hours of data analyzed
- R² of the regression
- 95 % CI on each coefficient
- Whether the regression respects PID endogeneity (`memory/causal-inference-lessons.md` flagged this exact pitfall — OLS fan→humidity is reverse-causal when PID is active)

**Fix:** add the underlying statistics; cite the IV/2SLS approach to address endogeneity. If the existing analysis in `analysis/02_iv_causal_model.py` doesn't already produce these numbers, run it and report. **M**

### C.4 §7.6 "System Reliability" is qualitative only

The section reads:

> The watchdog v10 mitigates this by detecting absent heartbeat messages and performing a USB sysfs reset, reducing recovery time to ~15–30 seconds.

But there's no uptime figure, no MTBF, no count of how many stall events occurred over the 4 years (or even the 94-day Meross window), no recovery time histogram. The paper is silent on the *measurable reliability* of a system that's been running for 4 years and has 3.1 million data points.

**Fix:** add a quantitative paragraph. From the journal logs you can extract: total stall events / month, mean recovery time, percent uptime by service. Even rough numbers ("watchdog triggered ~N times/month, mean recovery 22 s, system uptime >99 %") would close the gap. **M**

### C.5 Operational learnings since 2026-03-08 absent entirely

The paper does not mention:

- **Door safety mode** (a real safety feature)
- **Freezer daytime gate** (08-20 CEST, prevents runaway cooling)
- **Manual-mode 30-min watchdog** (operator-input timeout, deployed after a 14 h near-miss)
- **LED fault watchdog + transient counter** (driver-output anomaly detection)
- **STUCK RELAY power cross-check + hysteresis/transition guards** (just landed today)
- **Regime-aware mister with the 2026-05-11 audit finding** ("tune to operating point, not per-event Δ")
- **Light Curve C** (raised cosine LED schedule, since 2026-05-04)
- **Weather staleness fallback** (historical 14-day curve when OWM stale > 10 min)
- **Snapshot publishing pipeline** (Tailscale Funnel → public dashboard)

Several of these are *the* novel safety/control patterns a HardwareX reader would benefit from. They should at minimum appear in §6.6 Safety Considerations and §7.6 Reliability. The Light Curve C raised-cosine pattern is paper-worthy on its own (clean, replicable, with measured before/after data — see however §D.3 below on how to present it).

**Fix:** add a "§6.x Safety chain and operational monitoring" subsection that names the chain (door-safety + WBT gate + freezer daytime gate + manual-mode timeout + power cross-check + LED watchdog + terrarium-health.py) and points to the architecture doc for the full description. **M**

---

## D. Where the paper currently overclaims or misframes (M)

### D.1 "five continents" → 4

Already in §A but worth repeating: the cabinet contents span South America, Africa, Asia, Oceania. Not five.

### D.2 "Cannot provide species-specific dry rest periods in a shared enclosure"

§7.8 Limitations L601. This is correct but understated — it should be paired with the *positive* tradeoff: the system *does* protect moisture-dependent species (Heliamphora, Dracula) from desiccation during what would have been a dry rest period. The limitation as written reads as a failure; reframe as a designed tradeoff. **m**

### D.3 "+23 % DLI" — the wrong framing for a paper

The Light Curve C blog post (and your earlier comment in this session) is a story of *improvement from a prior state*. That's appropriate for a blog. A HardwareX paper should describe the **final operating regime**, not its iteration history. Reporting "+23 % vs prior" is internal-tuning language; reviewers want absolute numbers.

**Fix:** measure and report **PPFD at upper canopy and lower canopy** (μmol·m⁻²·s⁻¹) at midday peak, and **daily DLI** (mol·m⁻²·d⁻¹) at upper and lower canopy. These are paper-grade numbers. The current Curve C parameters (floor=35, peak=70 PWM, raised cosine, photoperiod clamped 10-14 h) are the *description*; PPFD/DLI is the *characterization*. **B** for paper-readiness. Requires buying/borrowing a quantum PAR sensor — flag as a pre-submission experiment.

### D.4 §7.1 RH minimum of 75 % is recent

The "75 % minimum" in the §7.1 table corresponds to the **2026-04-30 floor raise**, not the full 4-year history. Earlier (pre-2026-04-30) the floor was 70 % or unclamped. A reviewer might ask which regime the 75-98 % numbers describe.

**Fix:** clarify "since the 2026-04-30 humidity floor was set to 75 %" or give the long-run distribution (which is what the ledger and 94-day Meross window provide) separately from the current-regime envelope. **m**

---

## E. Reproducibility issues (M)

### E.1 The Node-RED flow is referenced as `flows-sanitized.json` (§3) — but it doesn't exist yet

`flows.json` exists in the live install (`/home/pi/.node-red/flows.json`) but the **sanitized version** (credentials removed) is not yet in the repo. This is a *blocker* for the open-source claim. Without it, no reader can install the flows. **B**

**Fix:** write a sanitizer (substitute Tapo/Meross/OWM creds with `<REDACTED>` placeholders; remove any private dashboards), commit as `nodered/flows-sanitized.json`, update the §3 reference.

### E.2 BOM categories are too coarse for purchase

§4 lists "Aluminium alloy scaffold" with no model number, "MistKing Standard pump (24 V)" with no SKU, "Tapo P100" with no firmware version, "Mean Well HLG-480H-48A" — at least the LED driver has a part number. A HardwareX BOM should be **purchasable from the table**.

**Fix:** add SKUs, supplier URLs (live + Wayback snapshot for posterity), and minimum-acceptable specifications. The website's `/highland/docs/` could host the full-detail table; paper carries the summary. **M**

### E.3 §5.2.2 Cooling System Installation lacks the refrigerant-handling note

The Vitrifrigo ND50 is a **pre-charged marine refrigeration unit** — but the install steps don't say so explicitly. A reader who tries to refit a generic split-system from parts will fail. The "pre-charged, sealed system, no F-gas certification required for installation" framing is the actual selling point of this build.

**Fix:** add a sentence in §5.2.2.1: "The Vitrifrigo ND50 ships pre-charged with R134a [verify refrigerant] in a sealed circuit; no refrigerant handling or F-gas certification is required for installation. Refrigerant lines connect via quick-couplers; do not disassemble the sealed loop." **M**

### E.4 §5.3 wiring is missing the IRF520N gate-resistor detail

§5.2.4 mentions IRF520N MOSFET modules but §5.3 doesn't show the gate-pull-down or any current limiting. The IRF520N module has internal gate-pull-down; a reader using a discrete IRF520N (not the module) will fry the Arduino without it.

**Fix:** clarify "use the IRF520N **driver module** (not bare MOSFET) — module includes gate-pull-down resistor". **m**

---

## F. Style / structure (m, n)

### F.1 No reference to the website

The Hugo site at `<website>` carries photos, build timeline, live conditions, dashboard, blog narrative, species pages, ledger. The paper makes zero reference to it. Demoting paper content to the website + Zenodo snapshot would make the paper *tighter and more reproducible* — but only if the paper actually links there.

**Fix (mechanical, ~1 h):** add "Live system snapshots, build photos, and operational record are maintained at `<website-URL>` (archival snapshot: Zenodo DOI `<TBD>`)" to the abstract end, §1 end, and §7 intro. See `SURVEY_2026-05-11_manuscript_rebuild.md` for the full cross-reference list. **m**

### F.2 References list is too thin

Only 7 references, of which 3 are software project URLs (Node-RED, InfluxDB, Grafana). A HardwareX paper of this length and ambition typically carries 20-30 references covering:
- Prior open-source environmental controllers (specific papers, not generic mentions)
- Cloud forest ecology references beyond Rull & Vegas-Vilarrubia
- PID control textbook references (you cite none)
- Wet-bulb thermodynamics beyond Stull 2011 (e.g., Sadeghi et al. 2013, or the ISO psychrometric standard)
- Each species cited in the abstract should have a habitat citation in §1

**Fix:** target 20-25 references; user-facing TODO. **M**

### F.3 §6.5 Troubleshooting

I don't see this section in the parts I read (paper §6 ends at §6.6 Safety Considerations). If §6.5 doesn't exist, the §6 anchor in the cross-references will break. **n** (check whether it exists; if not, add as a stub with "Detailed troubleshooting at `<website>/highland/docs/operations/`").

### F.4 The abstract is dense

§Abstract L25 packs too much. The system claims, the species count, the 4-year operation, the open-source license, and the companion papers all in one block. Split into 2-3 paragraphs (background → contribution → validation). **m**

### F.5 Power consumption is the most surprising number in the paper

§7.7 currently placeholder. **2.60 kWh/day** at €0.30/kWh = **€253/year** to run a 1 m³ cloud-forest cabinet with 4 years of uptime. That number alone is publication-grade — it's a clean answer to "what does this cost to run?" that no commercial growth chamber datasheet provides. Make it a headline figure in §7.7 and possibly the abstract. **M (positive: take the opportunity)**

---

## G. What's working (fair-reviewer balance)

A reviewer wouldn't only criticize; they'd note strengths so the recommendation is grounded.

- **The weather-mimicking concept is genuinely novel.** The 15 h time shift is creative and well-justified by the Genoa-vs-Colombia mapping; the paper makes the case clearly.
- **The three-regime PID switching is non-trivial control engineering.** The §6.2 description (now §7.3 in numbering) is one of the cleanest articulations I've seen of why a single error signal doesn't work for a system that has both humidity and temperature setpoints with overlapping actuators.
- **The wet-bulb gate is paper-quality on its own.** Even if everything else collapsed, "we detected that fans become a heat source below the room WBT and gated them" is a defensible contribution.
- **The 4-year operational record is a major asset.** Few HardwareX papers can claim that long an in-the-wild test. Lead with it.
- **The companion-paper strategy (CPN + AoS + ICPS) is well-conceived.** A reviewer who suspects "this is a thin pseudo-paper trying to look fat" will be reassured by the specialization split.
- **The licensing is right.** CERN-OHL-P-2.0 for hardware + permissive for software is the correct choice for an open-source paper.

---

## H. Suggested edit order (if the user takes this review)

1. **Fix the contradictions in §A** (1-2 h): regex-replace the species/continent/year numbers throughout, correct the evaporator location.
2. **Fill the placeholders in §B** (4-8 h): BOM, costs, figures, §7.7 power data, author names. The power section is the highest-value single fill.
3. **Sanitize and commit `flows-sanitized.json`** (1-2 h): unblocks the open-source claim.
4. **Run the PAR-sensor measurement** (1 h + sensor cost): PPFD upper + lower canopy, DLI under Curve C. This is the single most useful addition.
5. **Address §C overclaims and missing operational learnings** (3-4 h): rewrite the IV/2SLS section, add the safety chain to §6, add quantitative reliability to §7.6.
6. **Tighten §F style + references** (2-3 h): real reference list, abstract restructure, website cross-references.

Total: **~12-18 h** of focused work, plus the PAR sensor lead time.

**Don't** rebuild from scratch. The bones are sound; the gaps are specific. Treat this as a "revise and resubmit" punch-list.

---

## I. Decision point for the user

This review identifies what's broken in HardwareX. The other three drafts will have many of the same issues plus their own. Options:

1. **Apply this review to HardwareX first**, fix the issues, then I'll do CPN/AoS/ICPS reviews using HardwareX-corrected numbers as the consistent base. Cleanest sequence; ~30-40 h total work.
2. **Hand all four drafts to Mac-Claude** with this review + the SURVEY as context. Mac-Claude has the photo library and might be better positioned to address the figure placeholders specifically. Pi-Claude continues to support data/numbers/control-system questions on demand.
3. **Hybrid**: I produce the same review for CPN/AoS/ICPS now (2-3 h each); Mac-Claude takes the figure-curation pass; you do the final author-voice editing pass.

I'd suggest **option 1** if you want HardwareX submitted first and the others to follow, or **option 3** if you want all four moving in parallel.

---

*Reviewer: Pi-Claude, 2026-05-11. Companion documents: `SURVEY_2026-05-11_manuscript_rebuild.md`, `memory/paper-status.md`.*
