> **Superseded as the design of record on 2026-08-29 (evening) by
> [`V8_CANDIDATE.md`](V8_CANDIDATE.md)** — the canonical v8 development branch
> `dev/v8-canonical` consolidated this note's code with the verifier
> unification, the §13.11 chance-column fix and the maintenance-branch wording
> repairs, re-ran every backtest on the **corrected chance basis** (the numbers
> below were computed on the recorded zero column and the biased pre-screen
> chance rate; they are kept as the record of that first pass), moved every
> threshold into `dci1v8dev/rules.py` with its provenance, and chose the
> coverage offsets (0.10/0.10, span 0.20) by simulation rather than the
> 0.15/0.10/0.25 stated here. Sections 1, 2, 4 and 6–8 remain the mechanism
> descriptions; for every number, read `V8_CANDIDATE.md` and the JSON under
> `reports/dci1v8dev/`.

# DCI-1 v8 development candidate: the reference pre-screen, the spectrum rules, and the exact-count wording

**Status: DEVELOPMENT CANDIDATE, not a registration.** Everything below was
built on 2026-08-29 in the isolated worktree `dci-v8-prescreen` (branch
`dev/v8-prescreen-redesign`, from the study head `3ea82b2`), read-only over
the signed v6/v7 evidence trees and the four completed development
rehearsals. No registered constant, rule, record or evidence root was
touched; no GPU work was run. Numbers from stored evidence are development
numbers; numbers from simulation are synthetic. The code is
`dci1/src/dci1v8dev/`, the tests `dci1/tests_v8dev/`, the tools
`dci1/tools/v8_*.py`, the machine-readable results
`dci1/reports/dci1v8dev/prescreen/*.json` (each with a `.md` rendering).

The pipeline this proposes, conceptually:

    broad discovery -> uncertainty-aware pre-screen (+ targeted second pass,
    reserve extension) -> calibration (+ one bounded extension round)
    -> separate LOCAL / SPECTRUM validity -> deterministic spectrum selection
    -> selected-coverage identification -> freeze -> B+X / X+B generation
    -> Delta_R + difficulty-response analysis

---

## 1. The contradiction, located

v5–v7 carry one stability verdict per candidate and reuse it for two arms
that want opposite things.

| where | what it does | consequence |
|---|---|---|
| `dci1v7/stages/stability.py` `SPLIT_ADMISSIBILITY_COMPONENTS = ("V_head", "V_chance", "V_inter", "V_diff")` | §13.7 condition 1 asks for admissibility on each split **including V_diff** (§13.8's ±0.10 caliper to ι_A, the Newcombe region, the ±0.15 secondary caliper) | a rung is "stable" only if it is also *matched* on both splits |
| `dci1v7/stages/feasibility.py::calibration_at` | computes `stability_verdict` once per candidate, in the default slot `core_reference`, and hands the same map to core admission and to spectrum selection | the spectrum reads the core's folded verdict |
| `dci1v7/stages/selection.py::select_spectrum_triple` | evaluates `SPECTRUM_COMPONENTS` = all but `V_diff` — but `V_stab` is among them and `_v_stab` only *reads* the folded verdict | a spectrum rung must sit inside ±0.10 of ι_A on both splits |

Measured on the twelve stored replications (`spectrum_backtest.json`): the
pool §13.12 could draw from spans **0.07–0.16** in ι (8–23 rungs), so the
registered ±0.20 targets were unreachable by construction; v6 qwen3-4b met C4
6/6 and bound zero triples. C4 itself (six feature groups each with a family
spanning 0.40 over §12.6-eligible rungs) gates the spectrum on a quantity the
spectrum could not use.

Two further couplings were found while tracing this:

* `support.evaluate_support` counts §13.15's "≥ 5 families passing the full
  V(R)" from **Gate 2.5's list** (no `V_stab`, no `V_diff`) and
  `freeze_backups` takes its first two unused entries in sorted order with no
  tier filter: on 10 of 12 replications a recorded frozen backup is not an
  admissible core reference (`CR5`/`CR6`, Tier 3).
* `SPECTRUM_ELIGIBILITY_BAND = (0.10, 0.95)` is registered in
  `protocol/constants.py` and written into the manifest, and no code applies
  it: spectrum rungs pass `V_head`'s [0.10, 0.90] Wilson band, which admits a
  chance-free reference only up to p_solo ≈ 0.855 at n = 192.

## 2. The instrument: which wording frames were unreliable

`tools/v8_wording_audit.py` (→ `wording_audit.json/.md`) streams the Gate-2
candidate rows (192 topics × 4 draws per rung, 48 topics per frame) of the
twelve replications and reads, for A and MK1–MK8, the wording index and the
verifier's counted statistic. The four frames are A's, with the marker
substituted (§7.8):

| frame | text | reads the target as a *word*? |
|---|---|---|
| w0 | Use the word X exactly q times. | yes |
| w1 | Your answer must contain X exactly q times. | **no** |
| w2 | Include X exactly q times in your answer. | **no** |
| w3 | The word X must appear exactly q times. | yes |

Pooled over the eight marker families (zero-marker share = the marker does
not appear at all):

| model | w0 zero | w1 zero | w2 zero | w3 zero | dominant miss | robust frames (majority vote over families × replications) |
|---|---|---|---|---|---|---|
| gemma-3n-e2b-it | 0.23 | **0.46–0.53** | **0.48–0.53** | 0.14 | undershoot/absent | w3 |
| gemma-3n-e4b-it | 0.21 | 0.25–0.27 | 0.23–0.25 | 0.09 | undershoot | w0, w3 |
| qwen3-4b | 0.01 | 0.21 | 0.10 | 0.04 | **overshoot** (0.41–0.47) | w0, w3 |
| qwen3-4b-instruct-2507 | 0.00 | 0.07 | 0.14 | 0.00 | mixed, exact 0.63–0.73 | w0, w1, w3 |

For markers that can be read as connectives the effect is total: under w1/w2
"though" (MK3) and "namely" (MK6) are absent from 92–100% of Gemma answers,
while w3 gives MK6 0.70–0.86 compliance on gemma-e2b. One ambiguity survives
w0: "Use the word namely exactly 3 times" is read with *namely* as an
appositive on Gemma (marker absent in 50–98%), while w3 is followed. A's own
frames show the same pattern (w1 on Gemma: 0.10 at q = 1–2 vs 0.75–0.82
under w0/w2/w3; w0 on the 2507 checkpoint fails A specifically at q ≥ 5).

**Mechanism → rule.** A frame is interpreted reliably when the target is
introduced as *the word X* and X sits immediately before the count or the
verb. **The v8 set** (`dci1v8dev/wording_v8.py`, prospective; the two
repaired frames are strings no stored row was scored under):

    v8-w0  Use the word X exactly q times.                    (= w0)
    v8-w1  Your answer must contain the word X exactly q times.
    v8-w2  Include the word X exactly q times in your answer.
    v8-w3  The word X must appear exactly q times.            (= w3)

`assert_v8_wordings` tests: every frame names "the word X" exactly once, X is
followed by the count or the verb, A and MK frames are identical up to the
marker, "time/times" follows q, each frame is a minimal edit of its v7
counterpart (only the tokens "the word" inserted), and the §7.7 length
caliper against A holds. The reliability of the repaired frames is a v8
Gate-1 / regime-screen question, not a claim.

### 2b. Which MK families become ladders once the frames are repaired

Ladders reconstructed on the robust frames (`wording_audit.md`, "MK ladders"):

| model | usable after repair (monotone, spans 0.42–0.90) | too easy over q ≤ 8 (needs the reserve) | genuinely problematic |
|---|---|---|---|
| gemma-3n-e2b-it | MK1, MK4, MK5, MK8 (MK8 moves from "all below A", span 0.22, to usable, span 0.51) | MK2 | **MK3** ("though": flat 0.33–0.53, all below A), **MK6** ("namely": q = 1 anomaly, ρ ≈ −0.3), **MK7** ("instead": marker absent in 55–58% even under w3; span 0.05–0.28) |
| gemma-3n-e4b-it | MK1, MK2, MK4, MK5, MK8 | — (A itself too easy) | MK3 (reaches below only), MK6 (all below A, absent 40%), **MK7** (absent 77%, flat 0.07–0.17) |
| qwen3-4b | MK1, MK2, MK3, MK4, MK5, MK8 (MK3/MK4 overshoot 0.78–0.92 but stay monotone, spans 0.85–0.90) | MK6 | MK7 reaches below only (max 0.74) |
| qwen3-4b-instruct-2507 | MK3, MK4, MK8 | **MK1, MK2, MK5, MK6, MK7** (min 0.45–0.60 > ι_A − 0.15) | — |

So: wording confusion explains the *apparent* flatness of MK1/MK2/MK4/MK5/MK8
on the Gemmas and the non-monotonic reads of MK2/MK4/MK6 on gemma-e2b; MK7
("instead") on Gemma and MK3 ("though") on gemma-e2b are flat for a reason
the wording does not fix; on the Qwens flatness was never the issue — the
2507 grids are too short and qwen3-4b's misses are overshoot, i.e. genuine
difficulty. `wording_simulation.json` shows the audit statistic detects
absent-marker frames 100% of the time with 0% false flags on a truly flat
ladder, and that the repair recovers a steep ladder's true span while a truly
flat one stays flat. A's own ladder on gemma-e2b is non-monotone under every
frame (0.55–0.72), which is a finding about A on that checkpoint.

## 3. Severity-range exploration

`tools/v8_severity_range_audit.py` (→ `severity_range_audit.md`) extrapolates
each repaired ladder (logit-linear in q) to the severity reaching ι_A − 0.15:
on the 2507 checkpoint MK1/MK2/MK5/MK6/MK7 need q ≈ 9–10 (inside the frozen
reserve to 12); qwen3-4b's MK6 needs q ≈ 8.2; gemma-e2b's MK2 is too shallow
for the reserve to help; every other family reaches the region within q ≤ 8.
§12.6's expansion — the only rule that measures the reserve — ran on none of
the twelve replications, because the noisy 24-topic certificate said C1–C6
held.

**The v8 rule** (`dci1v8dev/prescreen/extension.py`, wired into the screen
and the second pass):

1. *Pre-screen reach.* A family whose posterior probability of an admissible
   rung at or beyond a side's offset is below `p_reach` is reach-deficient on
   that side. A family the screen would otherwise REJECT for a missing side
   is instead sent to the second pass with the next reserve severities in
   that direction (`UNEXPLORED_RESERVE`) whenever the reserve still holds
   unmeasured severities there — a noisy sample that *appears* to reach, or
   appears not to, does not stop the extension; the posterior does. Bounded
   by the reserve and by `max_batches`.
2. *Calibration reach.* After calibration, a spectrum-candidate family whose
   admissible rungs do not reach a side's region, with reserve severities
   left in that direction, receives one calibration round of up to two
   reserve rungs on that side (`calibration_extension_plan`). One round,
   capped, recorded.

## 4. Local vs spectrum validity (`dci1v8dev/spectrum/validity.py`)

* **LOCAL = v7's full V(R), unchanged**, folded stability included: a core
  reference must be matched on the pooled table and admissible-and-matched on
  each split. Nothing Δ_R relies on is weakened.
* **SPECTRUM**, in evaluation order: `V_spec`, `V_sat`, **`V_coord`**,
  `V_chance`, `V_struct`, **`V_inter_s`**, **`V_stab` (unfolded)**, **`V_pos`**.

### 4b. Which eligibility rules were removing useful extremes, and what replaces them

| registered rule | derivation | protects | verdict for a spectrum slot |
|---|---|---|---|
| `V_head` band [0.10, 0.90] on the Wilson interval | §13.14's composed-headroom band (0.05, 0.95) contracted | the reference's *own* composed compliance (reciprocal estimands D(R←B)) | **not applicable**: `SPECTRUM_ESTIMANDS` has no reciprocal member; it removes every chance-free rung above p ≈ 0.855 |
| `V_inter` projected band [0.10, 0.90] | the same band on R's projection under B | the same | **not applicable** as a headroom band |
| `V_inter` displacement ≤ 0.25 | B must not move the regime the coordinate was measured in | the coordinate | **kept** |
| `V_chance` κ ≤ 0.75, Wilson-upper ≤ 0.85 | variance amplification of ι, chance domination | the coordinate | **kept** |
| lift ≥ 0.20; vacuity ≤ 0.10; κ < 0.99 | a real, non-vacuous, defined instruction | the coordinate | **kept** |
| `V_stab` equivalence ±0.20 on both splits | a pinnable coordinate | the coordinate | **kept**, with condition 1 read on the spectrum's own components |
| `V_diff` (caliper, Newcombe, secondary caliper) | matching to A | Δ_R | **local only** |

`V_coord` = point solo rate inside the registered-but-unapplied
`SPECTRUM_ELIGIBILITY_BAND` (0.10, 0.95) (a degeneracy guard on the point, not
a headroom band), vacuity ≤ 0.10, lift ≥ 0.20, κ < 0.99, and **SE(ι) ≤ 0.05**
from the per-topic values. `V_inter_s` = the displacement bound plus the
projection inside the same guard band. `V_pos` = |ι − ι_A| ≥ 0.05. On the
twelve replications the spectrum-valid pool grows from 8–23 rungs spanning
0.07–0.16 (v7's folded pool) to **41–81 rungs spanning ≈ 0.21–0.94**, of
which 2–13 per replication lie in the 0.855–0.95 window `V_head` excluded
(`spectrum_backtest.md`). Degenerate, vacuous and chance-dominated rungs are
still refused (`spectrum_scenarios.md`, `tests_v8dev/test_spectrum.py`).

## 5. What replaces C4 (`dci1v8dev/spectrum/coverage.py`)

Identification is decided on the **selected** set, before any composed cell
exists, in the shape §13.13 already uses on the confirmatory data:

1. ≥ 2 spectrum-valid points strictly below A and ≥ 2 strictly above;
2. from ≥ 2 families on each side;
3. one point at or beyond 0.15 below A and one at or beyond 0.10 above
   (asymmetric because the band is: with A aimed at 0.70 solo the easy side
   has ~0.25 of room to the guard band);
4. total span ≥ 0.25; every selected coordinate with SE(ι) ≤ 0.05;
5. the projected SE of §11.8's common slope at the registered allocation
   (384 blocks × 8 draws), from the measured per-point precision and
   block correlation, ≤ 0.05.

Condition 5 is what makes "how much spread is needed" computed rather than
asserted. Under §11.8 (one intercept per family) the slope is identified from
within-family spread only — `SE(β̂) = σ√(1−ρ)/√Σ_f Σ_s (d_fs − d̄_f)²` — and
on the completed rehearsal `dci1v7-development/qwen3-4b` the per-companion
D(B←R) has SE 0.0133 with between-companion block correlation 0.58
(`spectrum_precision.md`, recomputed read-only). Consequences:

* v7's realised core set (one rung per family) has **zero leverage**: β is
  not identified from it at all;
* three families × two points at ±0.10 give SE(β̂) ≈ 0.034 (95% half-width
  0.07 per unit ι); SE(β̂) ≤ 0.05 needs leverage ≥ 0.027, i.e. three
  families × two points at ±0.07;
* δ_diff's planning half-width is ≈ 0.023 at any of these spreads once A is
  bracketed, against its registered precondition 0.05;
* the old 0.40 within-family span was ~4× what precision needs and
  unreachable on the easy side.

Family-ladder quality (`prescreen/ladder.py`: Spearman ρ, significant
reversals, WLS slope, 68% conservative range → STRONG / USABLE_NOISY / FLAT /
NON_MONOTONIC) is a **discovery diagnostic** that steers retention and the
second pass; it is not the identification gate.

## 6. The deterministic spectrum-selection rule (`dci1v8dev/spectrum/selection.py`)

Inputs: the spectrum-valid pooled rows, ι_A on the same table, the core
references, the rule's constants. No composed quantity can enter (§13.11's
closed schema refuses it before the function is reached; `tests_v8dev`
asserts it).

1. Per family: the **low** point is the valid rung at or below ι_A − 0.05
   nearest ι_A − 0.20; the **high** point the valid rung at or above
   ι_A + 0.05 nearest ι_A + 0.15. A family with both is *straddling*; its
   points are the two plus its core rung when it is a core family.
2. Straddling families are ranked by within-family leverage and taken in
   that order **preferring an unrepresented feature group**, up to four.
3. If a side is still uncovered, one-sided families add their two farthest-
   apart valid rungs on that side (separation ≥ 0.05; a single point carries
   no leverage), by leverage and diversity.
4. `selected_coverage` on the final set is the spectrum arm's identification
   status at design time.

Tie-breaks: structural tier, registered feature-group order, less
restrictive severity, family id. Replayed on the twelve replications the rule
binds 6–8 spectrum references from 3–4 families with offsets 0.21–0.31 below
and 0.14–0.35 above A, total spans 0.35–0.62 and projected SE(β̂) 0.013–0.022
(`spectrum_backtest.md`): **identified on 12/12**, against v7's 2/12 at Gate
3B (both lost again to C4 on the calibrated basis).

## 7. Backups (`dci1v8dev/spectrum/backups.py`)

A backup is a family, unused in the core set, with a rung passing the
**full LOCAL rule** (folded stability and `V_diff` included) from a tier the
core slot admits. §13.15's "≥ 5 families passing the full V(R)" is recomputed
on that basis (met on 11/12 replications; gemma-3n-e4b-it has exactly three
admissible families and no backup) and Gate 2.5's list is reported as what it
is: the set worth calibrating.

## 8. The pre-screen (`dci1v8dev/prescreen/`)

Stage 1 (unchanged cost, 326 rungs × 24 topics × 1 draw): every rung gets a
Beta posterior from its counts (topic-clustered effective size for repeated
draws; measured ICC 0.40); A's grid gets one with §12.3's severity selection
re-run inside every draw; each family's ladder is drawn **jointly** from an
empirical-Bayes random-effects posterior around its trend in restrictiveness
(`statistics.hierarchical_draws`: one lucky extreme, or many rungs near a
boundary, cannot certify a family); and the calibration-basis geometry is
evaluated on every draw under three readings — §12.6-eligible (for C4),
local-admissible (band [0.10, 0.90] + chance/lift; the local event),
spectrum-admissible (guard band [0.10, 0.95] + chance/lift; the support
events). Per family: P(C4), P(support below), P(support above),
P(support both), P(local), ladder class, comparators (raw max–min,
conservative spans at 68/80/90%, shrinkage span).

Statuses on P(support both): `SCREEN_ACCEPT` (≥ accept), `SCREEN_REJECT`
(≤ reject), otherwise `SCREEN_RESAMPLE`; a REJECT for a side the family has
never measured toward, with reserve left, becomes RESAMPLE with extension.
Labels, separate from statuses: `SPECTRUM_REFERENCE_CANDIDATE` (accepted
family) and `LOCAL_REFERENCE_CANDIDATE` (a rung with P(local) ≥ 0.5).

Stage 2 (`rescreen.py`): families in the middle band receive a batch — every
measured rung plus up to two reserve severities in the deficient direction
(v6 E3's direction rule), and A's grid — on 24 fresh topics at one draw
(fresh topics beat repeated draws at ICC 0.40); re-screen; repeat until the
family leaves the band or three batches are spent; a family still undecided
is resolved by the posterior majority and recorded `AMBIGUOUS_AT_MAX`. The
maximum cost is a function of the configuration alone
(`max_cost_generations`).

Stage 3 (`retention.py`): a spectrum family carries a spaced subset by role
(HARD_EXTREME, INTERMEDIATE_HARD, NEAR_A, INTERMEDIATE_EASY, EASY_EXTREME —
as many as exist, five at most); a local family its three rungs most likely
inside the caliper; the class and near-form arms their few C7/C8 rungs;
feature-group diversity first. §12.7's rule (every Tier-1/2 rung + the 24
Tier-3 rungs nearest A) is reproduced beside it for comparison.

Thresholds are chosen **prospectively** on the synthetic operating
characteristics (`simulation.md`, §9 below) and the backtest reads them from
that file; the leave-one-model-out section of the backtest is labelled
retrospective development.

## 9. Simulation and backtest results

All numbers below are generated by the tools named in `reports/dci1v8dev/prescreen/README.md`; the JSON files are the record.

### 9.1 Synthetic operating characteristics (`simulation.md`)

120 replicates per archetype and A-curve; FP/FN against the true event on the true parameters; the legacy screen is the v7 per-family C4 certificate on the 24-topic point estimates.

Prospective choice (minimise FP + FN over archetypes (equal weight, both A curves); tie-break: smaller resample fraction, larger d_below, lower accept):

**event = support_both, offsets below/above = 0.15/0.15, accept = 0.8, reject = 0.2, final-at-max = 0.5** → pooled FP 0.076, FN 0.134, resampled 0.56.

| archetype | A curve | true event | legacy pass | legacy FP | legacy FN | new accept | new FP | new FN | resampled | batches | P(cal C4 \| legacy pass) | P(cal event \| new accept) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| wide | qwen3-4b-like (iota_A~0.68) | True | 0.89 | 0.00 | 0.11 | 1.00 | 0.00 | 0.00 | 0.39 | 0.62 | 1.00 | 1.00 |
| narrow_noisy | qwen3-4b-like (iota_A~0.68) | False | 0.11 | 0.11 | 0.00 | 0.01 | 0.01 | 0.00 | 0.63 | 1.18 | 0.00 | 0.00 |
| borderline | qwen3-4b-like (iota_A~0.68) | True | 0.33 | 0.33 | 0.00 | 0.81 | 0.00 | 0.19 | 0.86 | 2.02 | 0.10 | 0.76 |
| one_sided | qwen3-4b-like (iota_A~0.68) | False | 0.30 | 0.30 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | — |
| flat | qwen3-4b-like (iota_A~0.68) | False | 0.03 | 0.03 | 0.00 | 0.00 | 0.00 | 0.00 | 0.22 | 0.23 | 0.00 | — |
| outlier | qwen3-4b-like (iota_A~0.68) | True | 0.84 | 0.00 | 0.16 | 1.00 | 0.00 | 0.00 | 0.57 | 0.93 | 1.00 | 0.97 |
| ceiling | qwen3-4b-like (iota_A~0.68) | True | 0.88 | 0.00 | 0.12 | 1.00 | 0.00 | 0.00 | 0.46 | 0.68 | 1.00 | 1.00 |
| too_easy_reserve | qwen3-4b-like (iota_A~0.68) | True | 0.00 | 0.00 | 1.00 | 0.71 | 0.00 | 0.29 | 1.00 | 2.67 | — | 1.00 |
| wide | qwen-2507-like (iota_A~0.55) | True | 0.88 | 0.00 | 0.12 | 0.99 | 0.00 | 0.01 | 0.55 | 0.88 | 1.00 | 1.00 |
| narrow_noisy | qwen-2507-like (iota_A~0.55) | False | 0.14 | 0.14 | 0.00 | 0.02 | 0.02 | 0.00 | 0.81 | 1.67 | 0.00 | 0.00 |
| borderline | qwen-2507-like (iota_A~0.55) | False | 0.28 | 0.28 | 0.00 | 0.58 | 0.58 | 0.00 | 0.90 | 2.44 | 0.09 | 0.03 |
| one_sided | qwen-2507-like (iota_A~0.55) | False | 0.41 | 0.00 | 0.59 | 0.00 | 0.00 | 0.00 | 0.02 | 0.02 | 0.82 | — |
| flat | qwen-2507-like (iota_A~0.55) | False | 0.07 | 0.07 | 0.00 | 0.00 | 0.00 | 0.00 | 0.25 | 0.33 | 0.00 | — |
| outlier | qwen-2507-like (iota_A~0.55) | True | 0.89 | 0.00 | 0.11 | 1.00 | 0.00 | 0.00 | 0.68 | 1.17 | 1.00 | 0.99 |
| ceiling | qwen-2507-like (iota_A~0.55) | True | 0.85 | 0.00 | 0.15 | 1.00 | 0.00 | 0.00 | 0.63 | 0.97 | 1.00 | 0.98 |
| too_easy_reserve | qwen-2507-like (iota_A~0.55) | True | 0.00 | 0.00 | 1.00 | 0.33 | 0.00 | 0.68 | 1.00 | 2.69 | — | 0.90 |

### 9.2 Backtest on the twelve stored replications (`backtest.md`, `failure_table.md`)

Screen configuration: {'source': '/home/cnm13ryan/git/dci-v8-prescreen/dci1/reports/dci1v8dev/prescreen/simulation.json', 'event': 'support_both', 'd_below': 0.15, 'd_above': 0.15, 'accept': 0.8, 'reject': 0.2, 'final_accept_at': 0.5, 'fp': 0.0763888888888889, 'fn': 0.13375, 'objective': 0.2101388888888889, 'fraction_resampled': 0.5604166666666666}. The second pass is emulated from Calibration-A's per-topic rows (no reserve, no A-grid re-measurement); 'Calibration-B only' shares no topic with the carved batches.

**Truth: calibrated C4 (production, pooled)**

| screen | predicted + | true + | TP | FP | FN | precision | recall | FPR |
|---|---|---|---|---|---|---|---|---|
| legacy (pre-screen C4 per family) | 90 | 47 | 41 | 49 | 6 | 0.46 | 0.87 | 0.12 |
| new stage 1 accept | 11 | 47 | 9 | 2 | 38 | 0.82 | 0.19 | 0.01 |
| new stage 1 accept-or-resample | 165 | 47 | 37 | 128 | 10 | 0.22 | 0.79 | 0.32 |
| new final accept (emulated second pass) | 37 | 47 | 25 | 12 | 22 | 0.68 | 0.53 | 0.03 |

**Truth: calibrated support-both (pooled)**

| screen | predicted + | true + | TP | FP | FN | precision | recall | FPR |
|---|---|---|---|---|---|---|---|---|
| legacy (pre-screen C4 per family) | 90 | 45 | 36 | 54 | 9 | 0.40 | 0.80 | 0.14 |
| new stage 1 accept | 11 | 45 | 9 | 2 | 36 | 0.82 | 0.20 | 0.01 |
| new stage 1 accept-or-resample | 165 | 45 | 40 | 125 | 5 | 0.24 | 0.89 | 0.31 |
| new final accept (emulated second pass) | 37 | 45 | 28 | 9 | 17 | 0.76 | 0.62 | 0.02 |

**Truth: calibrated support-both (Calibration-B only)**

| screen | predicted + | true + | TP | FP | FN | precision | recall | FPR |
|---|---|---|---|---|---|---|---|---|
| legacy (pre-screen C4 per family) | 90 | 46 | 36 | 54 | 10 | 0.40 | 0.78 | 0.14 |
| new stage 1 accept | 11 | 46 | 10 | 1 | 36 | 0.91 | 0.22 | 0.00 |
| new stage 1 accept-or-resample | 165 | 46 | 43 | 122 | 3 | 0.26 | 0.93 | 0.31 |
| new final accept (emulated second pass) | 37 | 46 | 29 | 8 | 17 | 0.78 | 0.63 | 0.02 |

**Truth: calibrated C4 (Calibration-B only)**

| screen | predicted + | true + | TP | FP | FN | precision | recall | FPR |
|---|---|---|---|---|---|---|---|---|
| legacy (pre-screen C4 per family) | 90 | 48 | 43 | 47 | 5 | 0.48 | 0.90 | 0.12 |
| new stage 1 accept | 11 | 48 | 9 | 2 | 39 | 0.82 | 0.19 | 0.01 |
| new stage 1 accept-or-resample | 165 | 48 | 38 | 127 | 10 | 0.23 | 0.79 | 0.32 |
| new final accept (emulated second pass) | 37 | 48 | 25 | 12 | 23 | 0.68 | 0.52 | 0.03 |

Pre-screen PASS → calibration FAIL: 49 of 90 family-level passes. Causes: NOISY_SPAN_INFLATION 9, ELIGIBILITY_TRIMMING 7, MISSING_SIDE 1, IOTA_A_MOVED 2, RETENTION_ARTIFACT 30.

| tree | model | legacy groups pre → cal | pass→fail | stage-1 accept/resample | final accept (calibrated true) | forwarded new / legacy | re-screen gens | calibration gens new / legacy |
|---|---|---|---|---|---|---|---|---|
| v7 | gemma-3n-e2b-it | 6 → 2 | 5 | 1/11 | 1 (1) | 29 / 132 | 9792 | 22272 / 101376 |
| v7 | gemma-3n-e4b-it | 11 → 4 | 7 | 4/11 | 5 (4) | 43 / 140 | 10128 | 33024 / 107520 |
| v7 | qwen3-4b | 6 → 5 | 1 | 0/16 | 5 (3) | 36 / 112 | 10080 | 27648 / 86016 |
| v7 | qwen3-4b-instruct-2507 | 10 → 4 | 6 | 0/15 | 3 (2) | 36 / 112 | 9864 | 27648 / 86016 |
| v6 | gemma-3n-e2b-it | 6 → 3 | 4 | 1/8 | 1 (1) | 29 / 134 | 7368 | 22272 / 102912 |
| v6 | gemma-3n-e4b-it | 10 → 3 | 8 | 4/13 | 4 (3) | 40 / 132 | 10848 | 30720 / 101376 |
| v6 | qwen3-4b | 9 → 6 | 4 | 0/14 | 3 (3) | 35 / 112 | 9840 | 26880 / 86016 |
| v6 | qwen3-4b-instruct-2507 | 0 → 5 | 0 | 0/10 | 2 (2) | 26 / 119 | 7152 | 19968 / 91392 |
| dev | qwen3-4b | 7 → 5 | 2 | 0/15 | 4 (3) | 35 / 112 | 9840 | 26880 / 86016 |
| r3 | qwen3-4b | 6 → 5 | 1 | 1/14 | 6 (4) | 38 / 112 | 9648 | 29184 / 86016 |
| r3 | gemma-3n-e2b-it | 7 → 1 | 7 | 0/10 | 0 (0) | 25 / 112 | 6408 | 19200 / 86016 |
| r4 | qwen3-4b-instruct-2507 | 8 → 4 | 4 | 0/17 | 3 (2) | 35 / 112 | 10464 | 26880 / 86016 |

Local-reference recovery: 135 families calibrated inside the ±0.10 caliper; kept by the new retention 92, by §12.7 135.

**retrospective development (LOMO)** (stage1_p vs calibration_support_both, min recall 0.75):

| held-out model | chosen accept | test precision | test recall | test FPR | test n+ |
|---|---|---|---|---|---|
| gemma-3n-e2b-it | 0.35 | 0.40 | 0.67 | 0.03 | 3 |
| gemma-3n-e4b-it | 0.3 | 0.70 | 1.00 | 0.04 | 7 |
| qwen3-4b | 0.25 | 0.69 | 0.96 | 0.08 | 23 |
| qwen3-4b-instruct-2507 | 0.4 | 0.62 | 0.42 | 0.03 | 12 |

**retrospective development (LOMO)** (stage1_p_c4 vs calibration_c4, min recall 0.75):

| held-out model | chosen accept | test precision | test recall | test FPR | test n+ |
|---|---|---|---|---|---|
| gemma-3n-e2b-it | 0.8 | 0.40 | 0.33 | 0.03 | 6 |
| gemma-3n-e4b-it | 0.7 | 0.47 | 1.00 | 0.12 | 7 |
| qwen3-4b | 0.55 | 0.72 | 1.00 | 0.06 | 21 |
| qwen3-4b-instruct-2507 | 0.8 | 0.70 | 0.54 | 0.03 | 13 |

### 9.3 Constructed-pool scenarios (`spectrum_scenarios.md`)

| scenario | expectation | old C4 | families meeting old C4 | new status | beyond V_head | rejections |
|---|---|---|---|---|---|---|
| local_not_spectrum | local valid rungs exist; spectrum NOT identified | False | — | DIFFICULTY_SUPPORT_NOT_IDENTIFIED | 0 | {"MK1:5": "V_pos", "MK1:6": "V_pos", "MK2:4": "V_pos", "MK2:5": "V_pos", "MK3:4": "V_pos", "MK3:5": "V_pos"} |
| spectrum_without_old_c4 | no family spans 0.40 (old C4 fails); new rule identified | False | — | DIFFICULTY_SUPPORT_IDENTIFIED | 0 | {"MK1:5": "V_pos", "MK2:5": "V_pos", "MK3:5": "V_pos"} |
| extreme_stable_survives | MK1:1 at 0.93 is spectrum-valid (beyond V_head) and selected high | False | — | DIFFICULTY_SUPPORT_IDENTIFIED | 2 | {"MK1:4": "V_pos", "MK2:4": "V_pos"} |
| degenerate_rejected | RF6:1 (kappa 0.995) no coordinate; RF7:2 vacuous; CR5:3 chance 0.8 fail | False | — | DIFFICULTY_SUPPORT_NOT_IDENTIFIED | 0 | {"MK1:5": "V_pos", "RF6:1": "V_coord", "RF7:2": "V_coord", "CR5:3": "V_coord"} |
| expansion_recovers_hard_side | no valid rung <= iota_A - 0.15 before; picks 9,10; after: reaches_below (one family alone cannot satisfy two-families-per-side, so the coverage status is informational here) | False | MK8 | DIFFICULTY_SUPPORT_NOT_IDENTIFIED | 2 | {"MK8:1": "V_coord", "MK8:2": "V_coord", "MK8:3": "V_coord", "MK8:9": "V_pos"} |
