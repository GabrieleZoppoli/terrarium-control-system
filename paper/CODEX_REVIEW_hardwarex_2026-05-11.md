# Codex adversarial review — HardwareX draft (2026-05-11)

**Reviewer posture:** hostile-but-helpful HardwareX referee. **Client:** the author. **Calibrated against:** SURVEY + Pi-Claude's review; old headline fixes not repeated unless still unresolved.

## TL;DR

- **Submission verdict: BLOCK** — the draft is stronger than the prior version, but still has unresolved placeholders, source-code/manuscript contradictions, and non-auditable quantitative claims that would trigger desk return or major revision.
- The 3 most damaging issues:
  1. The manuscript describes watchdog/reliability behavior that contradicts the checked-in watchdog script.
  2. The power section mixes incompatible denominators: `211.4 kWh`, `94.3 days`, `2.60 kWh/day`, and `€253/year` cannot all be true together.
  3. HardwareX reproducibility requirements are not met: BOM costs/suppliers, Zenodo locations, figures, wiring diagram, and key safety scripts are missing or placeholdered.

## Tier 1 — Blocking issues

1. **Placeholder pollution remains submission-blocking**

   **Location:** `paper/hardwarex.md:L3,L5,L18,L19,L25,L73-L83,L103-L173,L229,L329,L445,L557,L567,L635,L647,L655,L678,L684`.

   **Attack:** HardwareX reviewers cannot evaluate a draft with unresolved author metadata, total cost, repository DOI, figure placeholders, companion-paper refs, and a mostly empty BOM. HardwareX repository guidance requires complete design files in an approved repository, not `[PLACEHOLDER — Zenodo DOI]` rows.

   **Proposed fix:** Fill or remove every placeholder before submission; archive the full reproducibility package in Zenodo/OSF/Mendeley and replace all DOI/URL/ref placeholders.

   **Placeholder enumeration:** authors `L3`; corresponding email `L5`; hardware cost `L18`; repository DOI `L19`; companion website/ref placeholders in abstract `L25`; design-file DOI placeholders `L73-L83`; BOM unit/total/source placeholders for every component row `L103-L113,L119-L122,L128-L133,L139-L142,L148,L154-L165,L171`; BOM verification note `L173`; assembly photos `L229,L445`; wiring schematic `L329`; validation figures `L557,L567,L635`; companion URL `L647`; CPN ref `L655`; reference-list TODO `L678`; acknowledgments `L684`.

2. **Design-file summary does not match the repository**

   **Location:** `paper/hardwarex.md:L73-L83,L519,L531,L631`; repo files under `scripts/`, `analysis/`, `firmware/`, `nodered/`.

   **Attack:** The table lists `statistical-analysis/*.py`, but the repo uses `analysis/*.py`; it lists `meross_script.py`, while the manuscript relies on `meross_daemon.py`; it omits `mister-failsafe.py`, `meross-daemon.service`, `esp-water-level.ino`, `snapshot-capture.sh`, and any `terrarium-health.py`. Worse, `paper/hardwarex.md:L631` says `terrarium-health.py` is in the Design Files, but no such file is visible in the repository snapshot.

   **Proposed fix:** Make the design-file table a literal manifest of the submitted archive, add all safety/daemon/systemd/firmware files, and either commit `terrarium-health.py` or remove claims depending on it.

3. **Watchdog narrative contradicts checked-in code**

   **Location:** `paper/hardwarex.md:L91,L527,L603`; `scripts/arduino-watchdog.sh:L2,L17,L179-L190`; `docs/architecture.md:L186-L205`.

   **Attack:** The manuscript claims “watchdog v10”, 15-second checks, USB sysfs re-authorize, and 15–30 s recovery. The checked-in script says “v7”, `CHECK_INTERVAL=60`, and heartbeat failure triggers direct reboot, not USB reauthorization.

   **Proposed fix:** Either submit the real v10 script/service and supporting logs, or rewrite the paper to match v7 and recompute all recovery/uptime claims.

4. **Power-consumption arithmetic is internally inconsistent**

   **Location:** `paper/hardwarex.md:L616-L623,L629,L633`; `website/data/ledger.json:L2-L12,L32-L40`.

   **Attack:** The paper says `211.4 kWh over 94.3 days` and `2.60 kWh/day`, but `211.4 / 94.3 = 2.24 kWh/day`, not 2.60. If `2.60 kWh/day` is retained, annual cost at `€0.30/kWh` is about `€285/year`, not `€253/year`; the ledger also says the Meross integral begins with the daemon window, not the full retention window.

   **Proposed fix:** Define the exact Meross denominator, separate retention-window counters from power-meter counters, and recompute daily/monthly/annual values from one consistent window.

5. **Power wiring contains a dangerous voltage contradiction**

   **Location:** `paper/hardwarex.md:L287-L294,L321-L325`.

   **Attack:** The fan table says fan groups are supplied at 12 V, but the power-distribution section says `24 V DC` feeds Noctua fans via MOSFET modules. A reader following the wrong line could over-voltage 12 V fans.

   **Proposed fix:** Correct the power tree, list each DC supply with voltage/current rating, and make the wiring diagram match the text.

6. **Safety chain is not reproducible and is partly contradicted by PID docs**

   **Location:** `paper/hardwarex.md:L517,L531,L535,L607-L610`; `docs/pid-controller.md:L159,L161-L165,L172-L176`.

   **Attack:** The paper says door safety commands all fans off and protects the operator from running fans during inspection, but the PID doc says manual `Max` intentionally bypasses door-safety fan shutdown while doors are open. That may be a legitimate maintenance feature, but the manuscript currently presents it as an invariant safety interlock.

   **Proposed fix:** State the real control priority: manual mode can bypass fan stop; freezer/mister/light safety still applies. Include the code path and event logs that prove the timeout catches stale manual mode.

7. **HardwareX archive policy is not satisfied**

   **Location:** `paper/hardwarex.md:L19,L73-L83`.

   **Attack:** HardwareX repository instructions say the complete design files must be in an approved repository such as Zenodo, OSF, or Mendeley Data, public at submission; GitHub alone is not enough because it is mutable. The draft still has DOI placeholders.

   **Proposed fix:** Publish a submission snapshot to an approved repository and cite its DOI in the specification table and design-file table. Source: HardwareX repository instructions, Zenodo record `10.5281/zenodo.3944758`.

8. **Refrigerant specification is likely wrong or at least unverified**

   **Location:** `paper/hardwarex.md:L128,L253,L511`.

   **Attack:** The BOM says `R404a`, but current Vitrifrigo ND50 OR2V documentation says the GR version has an R134a compressor, while other pages say units may be precharged or nitrogen-pressurized depending on configuration. A refrigerant mismatch is a safety/regulatory problem, not a cosmetic spec.

   **Proposed fix:** Verify from the actual unit label/manual; cite the exact SKU/configuration and state refrigerant/quick-coupling/precharge status precisely.

9. **Measurement-count contradiction remains**

   **Location:** `paper/hardwarex.md:L62,L79,L479,L646`; `docs/schema.md:L89`; `website/data/ledger.json:L23-L25`.

   **Attack:** The manuscript says 33 InfluxDB measurements in some places and 32 in others; `docs/schema.md` says 32, while the ledger says 33. A reviewer checking the design files will see the mismatch immediately.

   **Proposed fix:** Make `docs/schema.md`, the ledger, and the manuscript agree; if the 33rd measurement is new, add it to the schema table.

## Tier 2 — Major issues

1. **Novelty claim is still under-defended**

   **Location:** `paper/hardwarex.md:L39-L51`.

   **Attack:** “No published open-source system implements weather-mimicking control” is plausible but not yet defended against specific prior art. A reviewer will cite open plant-growth controllers, humidity chambers, and IoT growth-chamber frameworks unless the introduction distinguishes them.

   **Proposed fix:** Add 3–5 specific prior-art citations and state the distinction: fixed/programmed setpoints or plant-feedback control are not live meteorological setpoint generation for terrarium-scale cloud-forest simulation.

2. **Reliability claims need an audit trail**

   **Location:** `paper/hardwarex.md:L603-L612`.

   **Attack:** `99.4 % uptime`, `mean inter-stall interval ≈ 36 h`, and `22 s ± 6 s` recovery are strong claims but lack event count, query, denominator, exclusion rules, and planned-reboot handling. The section also mixes 94-day evidence with features deployed on 2026-05-09 or 2026-05-11, which cannot support 94-day reliability conclusions.

   **Proposed fix:** Add a reliability table with feature, deployment date, eligible window, event count, false positives, mean recovery, and exact Influx/journal query.

3. **Power methodology is not reproducible enough**

   **Location:** `paper/hardwarex.md:L616-L631`; `scripts/meross_daemon.py:L47`; `docs/architecture.md:L55,L126,L266`; `website/data/ledger.json:L11-L12`.

   **Attack:** The paper says the Meross daemon polls every 30 s; the script says 2 s; architecture says both 2 s and 30 s; ledger says cadence varied 2/30/120 s. This can be handled, but only if the paper describes the actual integration method and window.

   **Proposed fix:** State that kWh is a trapezoidal integral over irregular samples, give the raw query/script, and explicitly say which subsystems are metered.

4. **IV/2SLS result is too compressed for a stats reviewer**

   **Location:** `paper/hardwarex.md:L565`; `analysis/02_iv_causal_model.py:L53-L65,L89-L120,L168-L213`.

   **Attack:** The manuscript reports only `−0.37 % per +10 PWM (p < 0.05)` and asserts the IV “removed” endogeneity bias. It omits first-stage F, number of nights, reduced-form effect, confidence interval, clustered/night-level robustness, and exclusion-assumption discussion.

   **Proposed fix:** Report first-stage F, N rows, N nights, A/B balance, CI, night-clustered or nightly aggregate result, and soften “removed bias” to “addressed the main simultaneity concern under the stated assumptions.”

5. **Wet-bulb heat-balance regression is presented without statistical support**

   **Location:** `paper/hardwarex.md:L581-L593`; `analysis/deconvolution.py:L93-L190`.

   **Attack:** The table gives exact-looking effects (`−2.03 °C/hr`, `+0.37 °C/hr`, `+0.58 °C/hr`) but no N, R², standard errors, CI, model formula, or residual diagnostics. The analysis script uses least squares but does not compute uncertainty.

   **Proposed fix:** Add model equation, N, R², CI/SE, and clarify “preliminary”; otherwise move the numbers to supplementary analysis.

6. **Sensor and actuator specification is incomplete**

   **Location:** `paper/hardwarex.md:L103-L111,L296-L302,L451-L467,L541-L555`; `docs/architecture.md:L37-L59`.

   **Attack:** The docs mention SHT35 accuracy and sampling, but the manuscript lacks sensor accuracy, calibration, drift checks, water-level calibration, Meross accuracy, and actuator failure modes in one reproducible table. HardwareX readers need to know what can be substituted and what cannot.

   **Proposed fix:** Add a “Sensors and actuators” table: model, measured variable, accuracy, sampling/logging cadence, calibration, control mode, failure mode, and mitigation.

7. **Lighting validation is still pending**

   **Location:** `paper/hardwarex.md:L555,L658`; survey `L67`.

   **Attack:** The draft correctly avoids the old `+23 % DLI` framing, but it still says PPFD/DLI are pending. At submission, “pending quantum sensor” is a validation gap for a plant-growth hardware paper.

   **Proposed fix:** Measure upper/lower canopy PPFD at peak and integrated DLI under Curve C, then replace the pending language with measured values.

8. **Commercial growth-chamber comparison is unsupported**

   **Location:** `paper/hardwarex.md:L37,L65,L633`.

   **Attack:** `EUR 10,000–50,000+`, `1.5–3 kWh/h`, and “comparable or superior” are uncited and invite reviewer pushback from anyone with chamber datasheets. The wording also compares a hobby/research cabinet to certified commercial instruments without matched specs.

   **Proposed fix:** Cite specific Percival/Conviron models and datasheets, compare only volume/power/cost bands, and remove “superior” unless supported by quantified spec-by-spec evidence.

9. **Software installation instructions are under-specified**

   **Location:** `paper/hardwarex.md:L337-L377,L393-L408`; `docs/architecture.md:L130-L152`.

   **Attack:** The manuscript lists only a subset of Node-RED dependencies; the architecture doc lists many more. A reader importing `flows-sanitized.json` will fail without the full palette list, Python packages, systemd units, cron entries, and credential placeholders.

   **Proposed fix:** Either include the full dependency/install table in the paper or point to an archived install guide that is complete and versioned.

10. **Open-source claim overstates proprietary dependencies**

   **Location:** `paper/hardwarex.md:L25,L51,L654`.

   **Attack:** The controller stack is open-source, but Tapo plugs, Meross cloud power metering, and OpenWeatherMap are proprietary/cloud dependencies. HardwareX can accept commodity parts, but the phrase “built entirely on open-source software” is too broad.

   **Proposed fix:** Rephrase to “open-source control software running on commodity hardware; smart plugs and weather/power APIs are replaceable dependencies,” then document substitutions.

11. **Humidity envelope needs regime/date precision**

   **Location:** `paper/hardwarex.md:L543-L551`; survey `L64`.

   **Attack:** The table presents `75–95 %` as the target envelope over the 94-day window, but the survey says the 75 % floor is a current-regime setting since 2026-04-30. A reviewer may ask whether the 94-day performance metrics are current-regime or mixed-regime.

   **Proposed fix:** Split “current target envelope” from “94-day observed distribution,” and give the date when the 75 % floor became active.

## Tier 3 — Minor / style

- Abstract is ~277 words; HardwareX guide says abstract must not exceed 250 words.
- `deg C` and `°C` are mixed throughout; standardize to `°C`.
- `Chinchina` should be consistently `Chinchiná` unless ASCII-only style is intentional.
- Reference style is inconsistent: `[1]` style in §1, author-year in §7.1/§7.4.
- References `[2]`, `[4]`, `[5]`, `[6]`, `[7]` appear orphaned or not cited by bracket number.
- Add DOIs for Rull & Vegas-Vilarrúbia, Stull, Givnish, and all prior-art papers.
- `paper/hardwarex.md:L633` uses `kWh/h`; use `kW` or `kWh/day` consistently.
- `paper/hardwarex.md:L385` creates symlink `esp32` while the hardware is described as ESP8266.
- `paper/hardwarex.md:L647` says public verification at `<URL>` but no URL is supplied.
- `paper/hardwarex.md:L553` says “routinely drops to 14–16 °C” but §7.1 table minimum is 13.5 °C; not contradictory, but define routine vs observed min.
- `paper/hardwarex.md:L565` “companion papers” and `[ref]` should not appear until those manuscripts have stable citation labels.
- The accession count spot-check matches the survey: 76 living highland accessions, 75 taxa, 32 genera.

## Novelty defence

1. **McDowell, K., Zhong, Y., Webster, K., Gonzalez, H. J., Trimble, A. Z., & Mora, C. (2021). “Comprehensive temperature controller with internet connectivity for plant growth experiments.” HardwareX, 10, e00238. DOI: 10.1016/j.ohx.2021.e00238.**  
   **How to defend:** Cite it as plant-growth open hardware with internet-connected temperature control, then distinguish WMB as multi-variable weather-driven setpoint generation rather than temperature-only fixed/programmed control.

2. **Lau, S. K., & Subbiah, J. (2020). “HumidOSH: A self-contained environmental chamber with controls for relative humidity and fan speed.” HardwareX, 8, e00141. DOI: 10.1016/j.ohx.2020.e00141.**  
   **How to defend:** Cite it for open humidity-chamber precedent; distinguish WMB by plant cultivation, compressor cooling, meteorological setpoints, and long-term cloud-forest validation.

3. **Sánchez, C., Dessì, P., Duffy, M., & Lens, P. N. L. (2020). “OpenTCC: An open source low-cost temperature-control chamber.” HardwareX, 7, e00099. DOI: 10.1016/j.ohx.2020.e00099.**  
   **How to defend:** Cite it as open temperature-control chamber prior art; distinguish WMB by humidity/lighting/misting/weather ingestion and biological terrarium operation.

4. **Yuan, S., Tang, H., Fu, L. J., Tan, J. L., Govindjee, & Guo, Y. (2022). “An open Internet of Things (IoT)-based framework for feedback control of photosynthetic activities.” Photosynthetica, 60(1), 79–87. DOI: 10.32615/ps.2021.066.**  
   **How to defend:** This is the strongest conceptual prior art because it is an open plant-growth chamber framework for programmable feedback; distinguish WMB as exogenous live-weather mimicry for habitat simulation, not photosynthesis-model feedback control.

5. **Iucci, T., Maliqi, D., Sousa Rosa, S., & Marques, M. P. C. (2026). “A compact, modular and low-cost hydroponic greenhouse.” HardwareX, e00777. DOI: 10.1016/j.ohx.2026.e00777.**  
   **How to defend:** Cite it as current HardwareX controlled-environment plant hardware; distinguish WMB by stochastic weather-mapping, cool cloud-forest envelope, and four-year mixed-taxa cabinet validation.

## Items requiring data the author does not yet have

- Final Zenodo/OSF/Mendeley archive DOI with all design files, code, data, dashboards, and photos.
- Complete BOM: unit costs, total costs, suppliers, SKUs, acceptable substitutions, and total hardware cost.
- Actual assembly photos, wiring diagram, dashboard figures, PID disturbance figure, and power time-of-day plot.
- `terrarium-health.py` or equivalent safety-monitor source, plus install instructions.
- Reliability event export: serial stalls, watchdog recoveries, planned reboots, door events, manual overrides, LED faults, stuck-relay alerts.
- Exact uptime query and denominator definition.
- Corrected Meross power window, raw export/query, and annualized cost calculation.
- PPFD and DLI measurements using a quantum sensor at upper and lower canopy.
- Sensor calibration protocol or calibration evidence for SHT35, HC-SR04P, and Meross MSS310.
- Spatial temperature/RH gradient mapping if the vertical stratification claim is retained as more than qualitative.
- Commercial chamber datasheets for cost/power comparison.

## Items where this review disagrees with the SURVEY or Pi-Claude's prior review

- **Power window:** Survey says `211.4 kWh over 94.3 days` and `2.60 kWh/day`; ledger says the electricity integral is over the Meross daemon window, not the full `since → as_of` window. This must be adjudicated before submission.
- **Annual cost:** Survey says `~€253/year`; if `2.60 kWh/day` and `€0.30/kWh` are used, the annual cost is about `€285/year`.
- **Watchdog version:** Pi-Claude and the manuscript assume watchdog v10; checked-in `scripts/arduino-watchdog.sh` is v7 with 60-second checks and reboot-first heartbeat recovery.
- **Measurement count:** Survey/ledger use 33 measurements; `docs/schema.md` and parts of the manuscript say 32.
- **Safety monitor:** Survey says the STUCK-RELAY health monitor is complete in architecture docs, but the actual `terrarium-health.py` source is not present in the visible repo.
- **Refrigerant:** Pi-Claude suggested verifying R134a; the current BOM says R404a, while current Vitrifrigo documentation points to R134a or nitrogen-pressurized variants depending on model/configuration.
