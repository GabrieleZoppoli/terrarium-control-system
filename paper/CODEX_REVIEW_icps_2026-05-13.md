# Codex adversarial review (round 2) — icps-paper.md

- **Reviewer**: Codex (gpt-5.5, xhigh reasoning effort), dispatched 2026-05-13 by Mac-Claude.
- **Target**: `paper/icps-paper.md` after Pi-Claude's Pass B (commit `b41f62a`).
- **Priors fed**: convergence thesis nuance, 15-h phase-correction wording, 2.63 kWh/day SoT, Nepenthes "no Bornean", *D. victoriae-reginae* taxonomy, *U. quelchii* bloom record, *Brocchinia reducta* Guiana Shield framing. Codex was told not to re-litigate these.
- **Mode**: A — attack only. Defence pass: `paper/MAC_CLAUDE_COUNTER_REVIEW_2026-05-13.md`.
- **Verdict**: 1 BLOCK + 4 MAJOR. The flagship synthesis is contested on cohort accounting, on convergence-claim scope, on stale control parameters, and on under-supported statistical claims.

---

## Attacks (verbatim)

1. [Collection boundary and survival denominators are still broken.]
   Why this lands: §3 mixes cabinet plants, non-cabinet plants, a waiting-list *Heliamphora*, and omitted accessions; the flagship outcomes become unauditable before a reviewer even reaches the thesis.
   Severity: BLOCK.
   Lines: 11, 140, 146-161, 180-181, 200-207, 223-249, 259-273; AoS 63-97.

2. [The convergence dataset is selectively delimited.]
   Why this lands: The abstract and §6 sell "75 living accessions" as cloud-forest/tepui evidence, while §3 admits non-cloud-forest carnivores and the companion orchid draft includes *Aerangis* outliers; this looks like post-hoc selection.
   Severity: MAJOR.
   Lines: 11, 140, 171-173, 442-450; AoS 101-103.

3. [Control parameters and schema are stale in reproducibility-critical places.]
   Why this lands: §2.3 says humidity is clamped 75-95%, but §4.1 still says 70-90%; InfluxDB is reported as 32 measurements in the system and supplement despite the current 33-measurement project state.
   Severity: MAJOR.
   Lines: 77, 90, 373-375, 475, 546.

4. [Quantitative methods overclaim the reported evidence.]
   Why this lands: The IV/2SLS claim gives only effect size and p-value, with no first-stage strength, exclusion rationale, CI, sample/window, or robustness; the "equilibrium" cooling claim rests on sub-10-hour tests.
   Severity: MAJOR.
   Lines: 389, 393-403.

5. [The no-dry-rest attrition explanation is asserted, not demonstrated.]
   Why this lands: Discussion says losses concentrate in dry-rest taxa, but §3 reports uneven attrition across *Genlisea*, *Masdevallia*, Brazilian miniatures, and a moisture-demanding *D. cuthbertsonii*; §4.5 has no phenology analysis.
   Severity: MAJOR.
   Lines: 173-177, 209-221, 273, 300, 405-412, 450, 458-462.

---

*Counter-review and ACT/ADDRESS/ACKNOWLEDGE labels in the companion file.*
