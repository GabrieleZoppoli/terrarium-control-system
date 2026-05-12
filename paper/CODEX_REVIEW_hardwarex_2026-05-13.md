# Codex adversarial review (round 2) — hardwarex.md

- **Reviewer**: Codex (gpt-5.5, xhigh reasoning effort), dispatched 2026-05-13 by Mac-Claude.
- **Target**: `paper/hardwarex.md` after Pi-Claude's Pass B (commits `4a5e2d2`, `f482a40`).
- **Priors fed**: SURVEY, REVIEW_HARDWAREX_2026-05-11, CODEX_REVIEW_hardwarex_2026-05-11, MAC_CLAUDE_COUNTER_REVIEW_2026-05-12, energy_sot_2026-05-12.yaml, HANDOFF.md reversals. Codex was told not to re-litigate the 15-h shift wording, 2.63 kWh/day, watchdog v10, R134a refrigerant, *D. victoriae-reginae* taxonomy, schema 33, or the Crossref-verified novelty-defence citations.
- **Mode**: A — attack pass only. Defence pass is in `paper/MAC_CLAUDE_COUNTER_REVIEW_2026-05-13.md`.
- **Verdict (Codex's own ranking)**: 2 BLOCK + 3 MAJOR. Drafts is not submission-ready.

---

## Attacks (verbatim from Codex)

1. The BOM is still not a BOM; it is an empty purchase table with cost/source placeholders.
   Why this lands: HardwareX reviewers cannot reproduce or price the build when every component row lacks unit cost, total cost, and supplier; the specification table also still has total hardware cost as `[PLACEHOLDER]`.
   Severity: BLOCK.
   Lines: 18, 114-186.

2. The design-file package is not publication-grade reproducible hardware yet.
   Why this lands: The archive DOI is still TBD, the submitted firmware path is wrong relative to the repo, acrylic drawings are only DOCX rather than CAD/open fabrication files, and wiring/assembly figures remain placeholders.
   Severity: BLOCK.
   Lines: 19, 73-88, 196, 213, 242, 343, 459.

3. The monitoring and power windows are now internally contradictory.
   Why this lands: §7.6 and §7.7 call the evidence a "94-day Meross-instrumented window," but the table's actual energy integral is 211.41 kWh over 80.3 days; a reviewer will suspect denominator confusion still contaminates reliability and power claims.
   Severity: MAJOR.
   Lines: 557, 619, 630, 634.

4. The safety-chain reliability claims are not auditable and overextend late-deployed fixes.
   Why this lands: "99.4 % uptime" lacks the exact query, denominator, event count, and definition of "Arduino watchdog healthy"; meanwhile the manual-timeout and hardened relay logic were deployed on 2026-05-09/10, so they cannot support a 94-day reliability claim.
   Severity: MAJOR.
   Lines: 619-626.

5. The validation section reports headline control results without enough statistical support.
   Why this lands: The IV/2SLS claim gives only an effect and p-value, with no first-stage F, CI, N/night count, or exclusion-restriction defence; the wet-bulb heat-balance coefficients likewise lack N, SE/CI, R², and model formula.
   Severity: MAJOR.
   Lines: 579, 597-605.

---

*Counter-review and ACT/ADDRESS/ACKNOWLEDGE labels in the companion file.*
