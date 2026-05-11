# Codex adversarial review — ICPS draft (2026-05-11)

**Reviewer posture:** hostile-but-helpful ICPS / CPN synthesis referee. **Client:** the author. **Calibrated against:** SURVEY + HardwareX + CPN companion + prior Codex reviews.

## TL;DR

- **Verdict: BLOCK / MAJOR REVISIONS.** The synthesis idea is publishable, but the current draft would be returned because §6.1 overclaims convergence, §3 is not aligned with the accession ledger, and the quantitative analyses are not reproducible as written.
- **Top 3 issues:** §6.1 confuses “shared cultivation envelope” with “climatic convergence”; §3 contains multiple botanical and inventory contradictions; §4.3/§5 use causal/regression language without enough model reporting.
- **Pass B must do one hard reset:** rebuild §3 from `collection.csv`, narrow §6.1 to “co-cultivation within a bounded artificial temperature/RH/VPD envelope,” and either fully report the IV/regression analyses or demote them to preliminary engineering evidence.

## §6.1 Convergent Cloud Forest thesis — dedicated section

1. **Tepui summits are not cloud forest in the ordinary TMCF sense.**  
   `paper/icps-paper.md:447` calls the compared habitats “geographically disjunct cloud forests” while also naming “open, treeless tepui summits.” A reviewer will object that tropical montane cloud forest is a forest/cloud-immersion concept, not a synonym for every wet tropical mountain habitat.  
   **Defensive hedge:** Use “cloud-immersed tropical montane habitats” or “high-humidity montane habitats,” and reserve “cloud forest” for actual forest systems.

2. **Envelope overlap is not climatic identity.**  
   `paper/icps-paper.md:449` leans on lapse rate and cloud immersion to imply cross-continental equivalence, but the draft does not compare photoperiod, fog deposition, wind, UV, substrate chemistry, pH, nutrient availability, or seasonal drought. The evidence shows that selected taxa tolerate one engineered envelope, not that the native climates are interchangeable.  
   **Defensive hedge:** Claim “sufficient overlap in temperature/RH/VPD for co-cultivation,” not “climatic convergence” without qualification.

3. **The single-enclosure result is confounded by deliberate micro-zoning.**  
   The draft’s abstract and §6.1 imply common conditions, but `paper/icps-paper.md:57-61`, `paper/icps-paper.md:104`, and `paper/icps-paper.md:469` admit vertical gradients, different light zones, and a single mid-canopy sensor. Plants are not all experiencing one uniform climate.  
   **Defensive hedge:** Describe the result as “one enclosure with vertical microhabitat zoning,” and avoid saying taxa were grown under identical conditions.

4. **The loss pattern does not yet support the dry-rest boundary claim.**  
   `paper/icps-paper.md:453` and `paper/icps-paper.md:463` say losses were concentrated in dry-rest taxa, but the highland nonalive ledger includes taxa such as *Masdevallia*, *Mediocalcar*, *Aerangis*, *Chiloschista*, *Holcoglossum*, and *Fernandezia*, not just dry-rest Brazilian rupicolous orchids. As written, “confirming” the dry-rest hypothesis is stronger than the data allow.  
   **Defensive hedge:** Provide a cause-coded loss table and say the no-dry-rest regime “appears most limiting for some seasonally resting taxa.”

5. **“Validated by four years” is too broad.**  
   `paper/icps-paper.md:37`, `paper/icps-paper.md:453`, and `paper/icps-paper.md:488` imply four-year validation across the whole 76-accession collection. Many accessions are more recent, and some genera have multi-year flowering or decline cycles.  
   **Defensive hedge:** Say the system has operated since May 2022, but report residence time per accession and restrict “four-year success” to plants actually present that long.

## Tier 1 — Blocking issues

1. **§6.1 overclaims the core thesis.**  
   The claim is defensible only if narrowed. Current language at `paper/icps-paper.md:445-453` moves from “similar high humidity and cool nights” to “same cultivation strategy across tepui, Andes, PNG, Sundaland, and Brazil.” That is too large for the evidence.

2. **§3 is not ledger-safe.**  
   `paper/icps-paper.md:140` says 76 living accessions across 32 genera, which matches the survey, but many subsection tables do not match `website/static/data/collection.csv`. Examples: Heliamphora is stated as ten alive at `paper/icps-paper.md:146-161`, while the survey and CSV show nine; *Utricularia quelchii* is said lost at `paper/icps-paper.md:192-195`, while the CSV has it alive and the May 2026 blog has it flowering; Brocchinia is marked “not found” at `paper/icps-paper.md:180`, while the CSV includes *B. reducta* alive.

3. **§3 mixes highland cabinet plants with shelves/windowsill plants.**  
   `paper/icps-paper.md:235-253`, `paper/icps-paper.md:258-278`, and `paper/icps-paper.md:334-360` include several taxa that the CSV places on shelves or windowsill, not in the highland terrarium. This corrupts the “single enclosure” evidence base.

4. **Dendrobium taxonomy and geography are vulnerable.**  
   `paper/icps-paper.md:260` frames *Dendrobium victoriae-reginae* with PNG section *Oxyglossum* taxa. POWO gives *D. victoriae-reginae* as Philippine, while AOS describes section *Oxyglossum* as centered in New Guinea and lists a different sectional set. This should be corrected to avoid an easy botanical rejection.

5. **Brazilian “rupicolous Cattleya” framing is too loose.**  
   `paper/icps-paper.md:285-303` treats *Cattleya*, *Laelia*, *Leptotes*, and *Sophronitis* as one Brazilian rupicolous cloud-forest group. But the CSV *Cattleya* are *C. aclandiae* and *C. walkeriana* clones; POWO places both primarily in seasonally dry tropical biomes. The paper must identify species and avoid implying all are highland cloud-forest rupicoles.

6. **Nepenthes geography repeats a known error.**  
   `paper/icps-paper.md:312` says Borneo, Sumatra, Philippines. The current living highland Nepenthes list in `collection.csv` is Sumatra, Sulawesi, and Philippines; no living highland Bornean Nepenthes is present.

7. **§4.3 IV/2SLS is not reproducible and overstates causality.**  
   `paper/icps-paper.md:392` says IV/2SLS “confirmed” a causal fan effect, but the paper does not report the instrument, identification assumption, first-stage strength, sample size, night count, controls, standard errors, confidence interval, or time window. A stats reviewer will return this.

8. **§5 heat-balance regression is under-specified.**  
   `paper/icps-paper.md:425-433` reports coefficients but not the model equation, N, resampling interval, date window, R², SE/CI, residual treatment, or whether fans are measured PWM or schedule proxy. The coefficients are therefore not interpretable as published marginal effects.

9. **§4.4 cooling tests overstate evidence from n=3.**  
   `paper/icps-paper.md:396-406` says the tests “established” cooling limits and equilibrium. The underlying script treats one night as compromised/partial and only Night 3 as the definitive equilibrium run. State this as engineering characterization, not inference.

10. **Quantitative state is internally inconsistent.**  
    `paper/icps-paper.md:377` says humidity target/source is 70–90%, while the survey says current envelope is 75–95% since 2026-04-30. `paper/icps-paper.md:478` says 32 measurements; the survey says 33. `paper/icps-paper.md:372` says four years of monitoring, but several reported analytics are from 94-day or 18-day windows.

## Tier 2 — Major issues

1. **Methods do not support the statistical results.**  
   §2 describes hardware and control logic, but not the IV design, heat-balance model, cooling-test selection criteria, or uncertainty treatment.

2. **§6.3 needs the actual loss inventory.**  
   `paper/icps-paper.md:461-465` should include a concise table: taxon, status, cabinet location, acquisition/residence time, suspected failure mode, and whether dry rest is botanically expected.

3. **§4.5 phenology is currently not a section.**  
   `paper/icps-paper.md:408-415` is all `[USER INPUT NEEDED]`. Minimum viable version: dated first bloom/flowering/growth events for *Utricularia quelchii*, *Heliamphora*, *Nepenthes*, *Dracula/Masdevallia*, and Brazilian orchids, with event date and supporting observation.

4. **The manuscript must distinguish historical observations from current regime.**  
   The 75% RH floor is a current setpoint since 2026-04-30, not necessarily a four-year observed lower bound. Similar caution applies to raised-cosine lighting from 2026-05-04.

5. **Citation support is uneven.**  
   Stull is fine for wet-bulb calculation, but does not support cultivation claims. Jarvis & Mulligan/Bruijnzeel support cloud/fog climatology broadly, not the tepui-as-cloud-forest wording. Adlassnig supports Roraima microclimate comparison, not all Pantepui habitats. Shafer supports a freezer precedent, not this whole actuator design.

6. **Operational learnings from HardwareX are underused.**  
   The synthesis audience does not need the whole technical companion, but it does need a short safety/reliability paragraph: watchdog, fail-safe defaults, manual override, audited uptime window, power use, and mist/fog duty cycle.

7. **Light remains a weak point.**  
   The draft discusses photoperiod and PWM but still lacks direct PPFD/DLI. Since §6.1 invokes convergence across latitudes, this is not optional context.

8. **The weather-proxy/time-shift claim needs a worked example.**  
   `paper/icps-paper.md:386` says Colombian daytime maps to Italian night by a 15-hour shift. A reviewer will want one explicit timestamp example and the biological rationale.

9. **The conclusion repeats the overclaim.**  
   `paper/icps-paper.md:488` says the system validates the concept across continents. That should become “supports the practical feasibility of co-cultivating selected high-humidity montane taxa.”

## Tier 3 — Minor / style

1. **Title is too long.**  
   `paper/icps-paper.md:1` reads like a full abstract. CPN-style synthesis titles should be much shorter.

2. **Abstract is overloaded.**  
   `paper/icps-paper.md:9-12` packs too many numbers and claims into one paragraph. Trim and remove “identical” style implications.

3. **Fix placeholder blocks before review.**  
   Placeholders remain at `paper/icps-paper.md:3`, `:5`, `:163`, `:179`, `:197`, `:228`, `:253`, `:278`, `:305`, `:328`, `:360`, `:410`, `:498`, and `:532-535`.

4. **Use consistent units and characters.**  
   Standardize `°C`, `% RH`, `Chinchiná`, `Bogotá`, `Medellín`, `Sonsón`, and taxon hybrid symbols.

5. **Correct spelling/taxonomic names.**  
   `Comparetia` should likely be `Comparettia`. Check `Pleurothallis leptotifolia`. Standardize `ionasi` vs `ionasii`.

6. **Tables need provenance discipline.**  
   Every species table should have columns for status, location, provenance/source, and whether it is actually in the highland cabinet.

7. **Reference style is inconsistent.**  
   The references mix journal styles and include placeholder “additional references” notes. Clean before submission.

## §4.3 IV/2SLS + §5 heat-balance regression rigor

A stats-trained reviewer will demand the following for §4.3:

1. Name the instrument explicitly: night-mode assignment or experimental A/B night alternation.
2. State the estimand: humidity effect per +10 PWM during the relevant night window, not a universal fan effect.
3. State the exclusion restriction: assignment affects humidity only through fan speed, then discuss likely violations.
4. Report exact date window, row count, number of nights, number of A/B nights, and missing-data handling.
5. Report first-stage coefficient, first-stage F, reduced form, Wald/2SLS estimate, SE, CI, p-value, and covariance estimator.
6. Use night-clustered SE or night-level aggregation; row-level p-values are not credible with autocorrelated sensor data.
7. Report controls: room temperature, room RH, freezer state, hour terms, wet-bulb gate, light state, or whatever was actually used.
8. Include at least one robustness check: omit compressor-on periods, aggregate to night means, placebo daytime test, lag/differenced model, or room-condition stratification.
9. Replace “confirmed causal effect” with “estimated under the IV assumptions.”

For §5 heat-balance regression, a reviewer will demand:

1. Full equation for `dT/dt`, including passive room-gradient term, freezer term, fan term, light term, and any wet-bulb interaction.
2. Exact date window and sample size after resampling.
3. Units for every coefficient. Is fan effect binary on/off, per +10 PWM, or per full PWM range?
4. Clarify that `analysis/deconvolution.py` appears to use a schedule-based `fans_on` proxy, not measured fan PWM.
5. R², residual diagnostics, SE/CI, and treatment of serial autocorrelation.
6. Multicollinearity diagnostics or at least a condition-number/VIF table, because fan, freezer, light, and hour are schedule-correlated.
7. Confidence interval for the zero-crossing near wet bulb; otherwise keep the “near wet-bulb limit” as a qualitative engineering inference.
8. Label the model preliminary unless these diagnostics are supplied.

For §4.4 cooling tests:

1. Say “three forced-cooling runs, one compromised/partial, one definitive equilibrium run.”
2. Do not attach confidence language to 13.6 °C unless more runs are available.
3. Keep the value as an observed lower-bound characterization under those room conditions.

## Pass A → Pass B gap

Pass B is not polishing; it is a structural rebuild.

1. Rebuild §3 directly from `collection.csv`.
2. Separate “highland cabinet” from shelves/windowsill/outdoor plants.
3. Replace all “cloud forest” language with a controlled habitat vocabulary.
4. Rewrite §6.1 after the species rebuild, not before.
5. Add a compact methods subsection for IV, regression, and cooling tests.
6. Move HardwareX operational learnings into one synthesis-friendly paragraph or table.
7. Replace all `[USER INPUT NEEDED]` blocks with either data or deletion.
8. Harmonize counts across this draft, `cpn-paper.md`, `hardwarex.md`, and the survey: 76 living highland accessions, 75 taxa, 32 genera, 4 continents, 33 measurements, 75–95% current RH envelope.
9. Decide how to handle horticultural vs POWO taxonomy, especially *Heliamphora macdonaldae*, *Sophronitis/Laelia/Cattleya*, and named hybrids.

## Items requiring data the author does not yet have

1. Direct PPFD/DLI measurements under the current raised-cosine schedule.
2. Spatial temperature/RH/light map by shelf/height and front/back position.
3. Cause-coded loss table.
4. Accession residence times for all 76 living highland accessions.
5. Dated flowering, growth, and propagation evidence by accession.
6. Complete IV output table with first stage, reduced form, night-level robustness, and clustered uncertainty.
7. Complete heat-balance regression table with N, SE/CI, R², and diagnostics.
8. More replicated cooling tests, especially under summer room conditions.
9. A verified Colombian weather time-shift example.
10. A stable taxonomy policy for POWO vs horticultural labels.

## Items where this review disagrees with the SURVEY, HardwareX, CPN companion, or prior Codex reviews

1. I disagree with any SURVEY wording that would sharpen §6.1 into “demonstrates the envelope is sufficient” without the word “selected.” The data support selected taxa under artificial micro-zoning, not all taxa from those habitats.
2. The SURVEY’s “Bornean Nepenthes” framing should not be carried forward; the current living highland Nepenthes list is Sumatra, Sulawesi, and Philippines.
3. Do not import HardwareX power/reliability claims into this synthesis until the arithmetic and audit window are stated precisely.
4. The CPN companion is safer than this ICPS draft on tepui wording because it distinguishes open treeless tepui habitats from cloud forest. The synthesis should adopt that caution.
5. This review agrees with the prior CPN review that *Utricularia quelchii* must be treated as alive and flowering, not lost.
6. This review agrees with the prior HardwareX review that IV/2SLS and heat-balance claims need full reporting or demotion.

## External spot-check sources consulted

- POWO: [*Dendrobium victoriae-reginae*](https://powo.science.kew.org/taxon/urn:lsid:ipni.org:names:628914-1), Philippine native range.
- AOS: [*Dendrobium* sect. *Oxyglossum*](https://www.aos.org/explore-orchids/dendrobium-alliance/den-sec-oxyglossum), sectional distribution and culture.
- POWO: [*Cattleya aclandiae*](https://powo.science.kew.org/taxon/urn:lsid:ipni.org:names:621983-1) and [*Cattleya walkeriana*](https://powo.science.kew.org/taxon/urn:lsid:ipni.org:names:622278-1), seasonally dry biome notes.
- POWO: [*Brocchinia reducta*](https://powo.science.kew.org/taxon/urn:lsid:ipni.org:names:122255-1), Guiana Shield range.
- POWO: [*Utricularia quelchii*](https://powo.science.kew.org/taxon/urn:lsid:ipni.org:names:260834-2), Guiana Shield range and lithophyte/epiphyte habit.
- POWO: [*Dracula simia*](https://powo.science.kew.org/taxon/84019-2), Ecuador range.
- POWO: [*Heliamphora tatei* / *H. macdonaldae* synonymy](https://powo.science.kew.org/taxon/118880-2).
- Bruijnzeel et al. / Forest Service: [Tropical montane cloud forest state of knowledge](https://research.fs.usda.gov/treesearch/37810).
