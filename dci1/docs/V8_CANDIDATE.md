# DCI-1 v8 candidate — design of record (prospective; not registered)

**Status (2026-08-29, branch `dev/v8-canonical`, worktree `../dci-v8-canonical`).**
Development candidate only. No v8 preregistration, stage, manifest, seed
domain or evidence tree exists; nothing here has generated a token. Every
number from stored evidence is a read-only, development-level replay on the
signed v6/v7 trees and the completed rehearsals; every other number is
synthetic. v7 is historical evidence and its code is untouched by this
candidate except for the already-validated §13.11 chance-column fix
(7f89dae), which is merged here and not on the study branch.

**What was reconciled.** Four lines, in this order, with merge commits:
`fix/v8-verifier-unification` (5197c82: one marker counter for A and MK1–8,
package `dci1v8` → moved to `dci1v8dev.verifiers`), `fix/v7-chance-basis`
(7f89dae: §13.2's κ_c measured on the unconstrained cells, V14),
`dev/v7-difficulty-spectrum` (cab39ee: the C4 / ladder / wording-parse
diagnosis and the reference-support landscape, reports + tools),
`dev/v8-prescreen-redesign` (5635b9a, committed from its worktree on this
date: the pre-screen, spectrum, coverage, backup, wording and extension
candidate). From `maint/v7-docs-marker-unification` (uncommitted, edits
`dci1v7` in place) only the grammatical-number rule, the README banner and
`VERSION_DRIFT.md` were taken, re-implemented in `dci1v8dev` so that no
hash-bound or V9-pinned v7 module moves; its in-place `s0_count` change is
superseded by the v8 verifier layer. Code: `dci1/src/dci1v8dev/`; tests:
`dci1/tests_v8dev/` (200); tools: `dci1/tools/v8_*.py`; reports:
`dci1/reports/dci1v8dev/`; constants with provenance: `dci1v8dev/rules.py`.

---

## 1. The pipeline

| stage | module | what it does |
|---|---|---|
| clean wording | `wordings.py`, `wording_v8.py`, `verifiers/` | the four exact-count frames all say "the word X"; every other template renders the right grammatical number; A and MK1–8 counted by one function |
| broad discovery | v7's §12.2 regime screen, unchanged in cost (326 rungs × 24 topics × 1 draw + A's grid + one unconstrained cell) | the pre-screen κ is read on the **unconstrained cell** (`chance_basis.build_prescreen_cache`), not over other candidates' solo answers |
| uncertainty-aware pre-screen | `prescreen/screen.py` | Beta posteriors per rung, ι_A re-selected inside every draw, joint random-effects draws per family, P(support both sides) → ACCEPT / REJECT / RESAMPLE |
| adaptive severity expansion | `prescreen/extension.py`, `prescreen/rescreen.py` | a one-sided REJECT with unmeasured reserve in the deficient direction becomes RESAMPLE with the next reserve severities; bounded by the reserve and by 3 batches |
| LOCAL/SPECTRUM rung retention | `prescreen/retention.py` | spectrum families carry five roles (hard extreme, intermediate-hard, near-A, intermediate-easy, easy extreme); local families their four rungs most likely inside the caliper; class/near-form arms their few rungs |
| full calibration (+ one extension round) | v7's Gate 2 at 192 × 4, corrected chance column; `extension.calibration_extension_plan` | a spectrum family whose admissible rungs do not reach a side, with reserve left, gets ≤ 2 reserve rungs on that side, once |
| separate LOCAL / SPECTRUM validity | `spectrum/validity.py` | §3 below |
| deterministic spectrum selection | `spectrum/selection.py` | §8 below |
| coverage + projected-precision gate | `spectrum/coverage.py` | §4 below; admissible backups `spectrum/backups.py` |
| end to end | `e2e.py`, `tools/v8_pipeline_validation.py` | the whole chain on a synthetic world with seeded draws at the registered sample sizes |

## 2. The chance basis (both tables)

The signed v5–v7 Gate-2 tables carry `chance_compliance = 0.0` for every
candidate; the §13.11 fix measures it on the grid runs' unconstrained cells.
The first v8 backtests inherited the zero column (they reconstructed κ from
the recorded ι), so their V_chance and lift verdicts were vacuous and every ι
was raw solo. **Every replay on this branch reads the corrected basis**
(`dci1v8dev/chance_basis.py`; cache `reports/dci1v8dev/chance_basis/`,
checked against `run/execute.cell_rates` on 15 (label, split) samples per
replication) and refuses the recorded column unless asked for by name. The
pre-screen's own `chance` is a second, different basis (`instance_rates`
over every absent row, other candidates' solo answers included): it differs
from the unconstrained cell with SD 0.21 on Tier-3 budget families (0.005 on
Tier 1), which is why 18 caliper rungs first looked chance-dominated at the
screen. v8 reads the regime screen's unconstrained cell (ladder and
expansion runs, 24 topics × 1 draw) for the screen as well.

## 3. LOCAL_VALID and SPECTRUM_VALID

* **LOCAL_VALID** — v7's full V(R) unchanged, folded stability included:
  V_spec, V_sat, V_head, V_chance, V_struct, V_inter, V_stab (§13.7 with
  V_diff in condition 1), V_diff (|ι_R − ι_A| ≤ 0.10 on the pooled table, the
  Newcombe region, the secondary caliper). Nothing Δ_R relies on is weakened.
* **SPECTRUM_VALID** — in evaluation order: V_spec, V_sat, **V_coord**,
  V_chance, V_struct, **V_inter_s**, **V_stab (unfolded)**, **V_pos**.
  V_coord: raw solo inside the guard band (0.10, 0.95) (v5's registered,
  never-applied `SPECTRUM_ELIGIBILITY_BAND`), vacuity ≤ 0.10, lift ≥ 0.20,
  κ < 0.99, SE(ι) ≤ 0.05 from the per-topic values. V_inter_s: the
  displacement bound ≤ 0.25 and the projection under B inside the guard band.
  V_stab unfolded: §13.7 conditions 2 and 3 verbatim, condition 1 on
  V_coord/V_chance/V_inter_s — no V_diff, no headroom band. V_pos:
  |ι − ι_A| ≥ 0.05. A spectrum point is never asked to be close to A.

**The leak, traced and removed.** (1) `stability.SPLIT_ADMISSIBILITY_COMPONENTS`
includes V_diff; (2) `feasibility.calibration_at` computes one verdict per
candidate in the core slot and hands it to both arms; (3)
`selection.select_spectrum_triple` keeps V_stab, which only reads (1). On
the corrected basis the v7 (folded) spectrum pool spans 0.11–0.16 in ι on the
twelve replications; the unfolded pool spans ≈ 0.2–0.9. Executable:
`tests_v8dev/test_spectrum.py::test_the_leak_is_the_folded_v_diff…`.

## 4. What replaces C4

`selected_coverage` on the **selected** set, before any composed cell exists:
≥ 2 spectrum-valid points strictly below A and ≥ 2 above, from ≥ 2 families
on each side; one point at or beyond **0.10** below A and one at or beyond
**0.10** above; total span ≥ **0.20**; every selected coordinate with
SE(ι) ≤ **0.05**; projected SE of §11.8's common slope at the registered
allocation (384 × 8, measured per-point SE 0.013 and block correlation 0.60)
≤ **0.05**. Ladder monotonicity (`prescreen/ladder.py`) steers retention and
the second pass and is not a gate.

**Why these numbers** (`tools/v8_coverage_simulation.py` →
`reports/dci1v8dev/coverage_simulation.md`): among candidate rules replayed
on the same simulated designs (3 families × 2 points; true offsets 0.05–0.30;
calibration SE(ι) 0.02–0.08; confirmatory SE(d) 0.015), with truth = realised
SE(β̂) ≤ 0.05, A bracketed after re-measurement, attenuation ≤ 10 %, the
loosest rule with PPV ≥ 0.95 is 0.10/0.10/0.20/SE(ι) ≤ 0.05 (PPV 0.954,
recall 0.63); the first candidate's 0.15/0.10/0.25 gives PPV 0.975 for recall
0.44. SE(β̂) ≤ 0.05 is a 95 % half-width of ≈ 0.10 per unit ι (one SESOI per
unit of difficulty; 0.01 over the 0.10 caliper); the realised designs on the
twelve replications beat it by 2–4×. Errors-in-variables attenuation at
confirmatory precision is 2 % at ±0.10 within family and 8 % at ±0.05.

## 5. Spectrum eligibility: what went, what stayed

| rule | verdict for a spectrum slot |
|---|---|
| V_head band [0.10, 0.90] on the Wilson interval | **removed** — a composed-headroom band for reciprocal estimands the spectrum has none of; it capped a chance-free reference at p ≈ 0.855 |
| V_inter projected band [0.10, 0.90] | **replaced** by the guard band (0.10, 0.95) on the projection |
| displacement ≤ 0.25; κ ≤ 0.75 with Wilson upper ≤ 0.85; lift ≥ 0.20; vacuity ≤ 0.10; κ < 0.99; two-split equivalence ±0.20; V_spec/V_sat/V_struct | **kept** |
| V_diff (caliper, Newcombe, secondary caliper) | **local only** |
| new: SE(ι) ≤ 0.05; V_pos ≥ 0.05 | the point must be pinnable and not the core's territory |

Boundaries are tested one step either side (`test_eligibility_boundary.py`);
a chance-free 0.93 rung is spectrum-valid and selected high, chance-dominated,
vacuous and degenerate rungs fail at V_coord (`test_e2e.py`, world
`extremes`; `spectrum_scenarios.md`).

## 6. The wording instrument

    v8-w0  Use the word X exactly q time(s).                       (= v7)
    v8-w1  Your answer must contain the word X exactly q time(s).
    v8-w2  Include the word X exactly q time(s) in your answer.
    v8-w3  The word X must appear exactly q time(s).                (= v7)

A and MK1–8 differ only in the marker (`assert_v8_wordings`). Every other
family renders v7's text byte-for-byte at every severity but 1, where
*1 semicolon*, *1 word*, *1 word contains* replace the hard-coded plural
(`wordings.number_fields`, `assert_grammatical_number`: 2,668 renderings).
`v8_wording_source_hash` binds the bytes. The evidence for the repair is
`reports/dci1v8dev/prescreen/wording_audit.md` (w1/w2 marker-absent 46–53 %
on Gemma, 92–100 % for *though*/*namely*); the reliability of the repaired
frames is a v8 Gate-1 question, not a claim — no stored row was scored under
them, and no historical output is reinterpreted.

## 7. Severity expansion

Pre-screen: a family REJECTED with a one-sided deficiency, whose other side
is at least plausible (P ≥ reject) and whose reserve holds unmeasured
severities in the deficient direction, is RESAMPLED with the next reserve
severities (`UNEXPLORED_RESERVE`); each batch adds ≤ 2 reserve rungs by
restrictiveness (v6 E3's direction), ≤ 3 batches. Calibration: one round of
≤ 2 reserve rungs per deficient side for a spectrum-candidate family. The
2507 case (q = 1..8 above 0.90 solo, difficulty at q = 9–10) is the synthetic
world `too_easy_reserve`: reserve picks 9–12, reserve rungs forwarded,
identified (simulation: accepted 0.73–0.97, FP 0; v7's certificate: 0.00).

## 8. Pre-screen, retention, backups, selection

* **Pre-screen.** P(support both) ≥ 0.80 → ACCEPT; ≤ 0.20 → REJECT; else
  RESAMPLE (24 fresh topics per batch, every measured rung + reserve picks +
  A's grid; ≤ 3 batches; then posterior majority at 0.50, recorded
  `AMBIGUOUS_AT_MAX`). Chosen by `tools/v8_prescreen_simulation.py`
  (8 archetypes × 2 A-curves, 200 replicates): pooled FP 0.147 / FN 0.093
  (legacy certificate 0.16–0.20 / 0.33–0.41); the FP is concentrated in the
  2507-like *borderline* archetype whose true event sits on the offset.
  Local label at P(inside caliper) ≥ 0.25, derived from the 24-topic
  posterior width (an edge rung reads inside with P ≈ 0.34).
* **Retention.** Spectrum families: five roles from rungs with
  P(admissible) ≥ 0.5, feature-group diversity first, ≤ 8 families; local
  families: four rungs by P(inside caliper), ≤ 12 families; class arm 2,
  near-form 3. Every spectrum family's carried geometry is recorded
  (`spectrum_geometry`: extremes, reach of each offset).
* **Backups.** A family unused in the core set with a rung passing the full
  LOCAL rule from a core-admissible tier; §13.15's count recomputed on that
  basis; Gate 2.5's list reported as what it is. Tier-3, V_stab-failing and
  out-of-caliper families cannot count (`test_backups.py`).
* **Selection** (pre-composition inputs only; the closed §13.11 schema
  refuses a composed column before the function is reached, and the rule
  modules name no composed field — `test_e2e.py`, `pipeline_validation.md`):
  per family the valid rung at or below ι_A − 0.05 nearest ι_A − 0.20 and the
  one at or above ι_A + 0.05 nearest ι_A + 0.15; straddling families ranked
  by within-family leverage, taken preferring an unrepresented feature
  group, ≤ 4; a deficient side filled by one-sided pairs (separation ≥ 0.05);
  `selected_coverage` on the result is the identification status. Order
  invariant and deterministic (same record from a permuted table and from
  the same seed; a world that differs only in a composed outcome gives the
  same record).

## 9. Results (development-level)

**Retrospective, twelve stored replications, corrected chance basis**
(`reports/dci1v8dev/prescreen/backtest.md`, `spectrum_backtest.md`,
`pipeline_validation.md`):

* Family-level screen against the calibrated support-both truth: legacy
  certificate precision 0.46 / recall 0.70 / FPR 0.13; new final accept
  (emulated second pass, conservative) 0.73 / 0.72 / 0.04; stage-1 accept
  alone 0.83 / 0.41.
* Pre-screen passes that failed calibration: 53 of 93 — retention artefact
  32, noisy span 9, eligibility trimming 6, missing side 3, ι_A moved 3.
* **The 32 retention artefacts, examined:** 6 refuted at the screen; 9
  accepted after the emulated second pass and forwarded with their spaced set
  (4 with a rung beyond each offset); 17 undecidable — their dropped extremes
  were never calibrated, so the emulation could not measure them; only 5 of
  32 have an admissible rung at or beyond both offsets at the screen, and 19
  rest on chance-inflated budget rungs (`CL7:10/20/30`, `RF12:8`, `RF6:9–12`,
  `RF5:7–10`, …). The historical "coverage destroyed by retention" was
  mostly coverage the legacy C4 eligibility counted without a chance check.
  The spaced retention is still the right rule — it carries the geometry of
  every accepted family by construction — but the measured gain on the stored
  replications is ~5 families, not 30.
* Local references: 105 of 117 calibrated, admissible caliper rungs are
  forwarded by the new retention (10 not labelled at the screen — Tier-3
  rungs whose 24-draw chance basis places them elsewhere — 1 lost to the
  family cap, 1 to ι_A movement on 2507); §12.7 forwards all 117 at 2–3× the
  cost.
* Rungs forwarded to calibration: 40–64 per replication (§12.7: 112–140);
  calibration 30.7k–49.2k generations (86k–107.5k); second pass
  6.7k–11.9k generations.
* Spectrum replay: identified on **12/12** replications against v7's 2/12 (Gate 3B; both lost again to C4 on the calibrated basis); spectrum-valid pools of 37–81 rungs spanning ≈ 0.20–0.94 in ι where v7's folded pool spanned 0.07–0.18; 2–4 families, 4–8 points, offsets 0.18–0.31 below / 0.13–0.32 above A, projected SE(β̂) 0.013–0.028; §13.15's "≥ 5 families passing the full V(R)" met on the admissible basis on 11/12 (v7 gemma-3n-e4b-it has three admissible families and no backup); a recorded frozen backup is inadmissible on 10/12 (CR5/CR6 Tier 3 on every Gemma and Qwen tree; MK1/MK2 failing the full rule on others).

**Synthetic, end to end** (`pipeline_validation.md`): wide, outlier,
too-easy-reserve, extremes and wording-repaired worlds identified (SE(β̂)
0.014–0.024, 3–4 families, 6–8 points, spans 0.35–0.57); one-sided and flat
worlds not identified with the reason named; the *narrow* world (true
support just at the offsets) is a conservative miss; families confused by the
v7 frames are accepted only under the v8 frames; true local families found
6/6, 4/4, 3/4; 12–36 rungs forwarded; 16k–37k generations to the freeze.

## 10. Compute

Per model, to the freeze: pre-screen ≈ 8k (unchanged) + second pass 7–12k +
calibration 31–49k (+ A's grid 6k, + extension ≤ 25k worst case, typically
0–6k) ≈ **55–75k generations** (v7: ≈ 100–115k). After the freeze, the
spectrum arm: 6–8 references × (solo:X, B+X, X+B) × 384 × 8 = **55k–74k**.
At the observed Gate-2 throughput (qwen3-4b 15.5 rows/s, gemma-e4b 4.7)
that is ≈ 1–1.5 h (qwen) / 3.5–4.5 h (gemma-e4b) to the freeze and about
the same again for the spectrum arm, per card.

## 11. Remaining uncertainties before a v8 freeze

1. **The repaired frames are untested on a model.** Their reliability, and
   *namely*/*instead* on Gemma under any frame, is what the pilot measures.
2. **The second pass has only been emulated** (carved from Calibration-A's
   per-topic rows; no reserve, no A-grid re-measurement). Its real operating
   point is the pilot's first result.
3. **ι_A moves between 24 and 192 topics** by up to 0.28 on the 2507
   checkpoint; the screen's posterior (SD 0.04–0.12) absorbs most of it, and
   the calibrated ι_A basis discrepancy (record vs unconstrained cell,
   ≤ 0.026) is reported, not resolved.
4. **The core selection in `e2e.py` is a stand-in** for §13.8; the v8 run
   layer must call the registered kernel.
5. **The v8 run layer exists but has run on no model** (2026-08-30,
   `dci1v8dev/run`, `docs/V8_PILOT.md`): nine stages, CLI, pilot manifest,
   `dci1v8:*` seed domain, isolated evidence roots, the §13.11 producer on
   the corrected basis, the wording allocation under the v8 frames, and a
   synthetic nine-stage walk. Its first real result is the pilot's.
6. The coverage simulation's truth is a modelling choice (SE ≤ 0.05,
   bracketing, ≤ 10 % attenuation); the geometry grid uses three families.
7. Gemma-3n-e4b (ι_A ≈ 0.73) has little room above A: on the stored
   replications the selection still binds ≥ 2 families above, but the
   margin is the smallest of the four models.

## 12. The next experiment (not run here)

Sequence: (1) a small solo/calibration pilot on one representative model —
**qwen3-4b-instruct-2507** (the model whose grids were too short and whose
ι_A moved most; qwen3-4b as the alternative if the reserve question is not
the priority) — through pre-screen, second pass, retention, calibration and
the extension round, under the v8 frames; (2) inspect only the prospectively
specified criteria: second-pass resolution (≤ 3 batches, `AMBIGUOUS_AT_MAX`
count), forwarded set (spectrum families with both extremes carried),
LOCAL-valid families ≥ 5, spectrum-valid points ≥ 2 per side from ≥ 2
families, selected coverage identified with projected SE(β̂) ≤ 0.05 --- and
the **wording diagnostic** (2026-08-30: the four frames measured separately
per (family, q), no pass/fail rule, no v7 reference; `V8_PILOT.md` §1a);
the researcher's five questions on Gate 2/3 are answered by
`tools/v8_wording_decision.py` (`V8_PILOT.md` §7);
(3) take the wording policy decision on solo/pre-screen/calibration evidence
and freeze v8; (4) only then generate the selected spectrum's B+X / X+B
cells and fit §11.8.

What runs today (CPU, this worktree, both GPUs untouched):

    cd dci1
    .venv/bin/python -m pytest tests_v8dev -q -p no:cacheprovider
    .venv/bin/python tools/v8_chance_basis_cache.py --evidence /path/to/dci1/evidence --verify
    .venv/bin/python tools/v8_coverage_simulation.py
    .venv/bin/python tools/v8_prescreen_simulation.py --sims 200      # ~12 min
    .venv/bin/python tools/v8_prescreen_backtest.py --evidence /path/to/dci1/evidence
    .venv/bin/python tools/v8_spectrum_backtest.py --evidence /path/to/dci1/evidence   # ~20 min
    .venv/bin/python tools/v8_pipeline_validation.py

The pilot's execution layer (2026-08-30; `dci1v8dev/run`,
`docs/V8_PILOT.md`) generates under the v8 wording hash into a root of its
own (`evidence/dci1v8-pilot`, never r3/r4/r5 --- refused by rule), uses
the Gate-2 producer from 7f89dae, binds `rules.py` and both instrument
hashes in a signed pilot manifest, evaluates the four criteria above on
signed records (`PILOT_REPORT`), and is driven per card by
`tools/run_v8_pilot.sh`:

    tools/run_v8_pilot.sh qwen3-4b-instruct-2507 <device> evidence/dci1v8-pilot <log_dir>

A v8 **preregistration** restating §9.2, §7.5/§7.8, §12.2/§12.6/§12.7,
§13.2, §13.7/§13.12/§13.13/§13.15 with `rules.py` as its constant table is
the freeze step, after the pilot; the pilot manifest is not it.
