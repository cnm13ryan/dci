# DCI-1 v6 — preregistration-readiness memo

**Status: NOT ADOPTED, NOT REGISTERED.** No manifest exists, no stage has run,
and no behavioural row may be generated against anything here. This memo audits
[`../../../user-notes/DCI1_v6_proposal.md`](../../../user-notes/DCI1_v6_proposal.md)
against the closed v5 record and turns what follows mechanically from the
scientific intent into an exact specification. What does **not** follow
mechanically is listed in §5 and is the researcher's.

**Classification of the v5 evidence used here: DEVELOPMENT_EVIDENCE.** v5 is
read only for survival, identification and headroom. No effect quantity is
estimated, compared or interpreted; nothing here is evidence about `Delta_j`,
`Delta_R` or `Xi`; and the three `REFERENCE_SUPPORT_NOT_IDENTIFIED` verdicts
are never read as null results. Per §30's precedent, anything fitted here is
prospectively tested by v6 and v6 may not claim these choices generalise.

Every number below that is not a registered constant is computed by
[`tools/v6_readiness_evidence.py`](../../tools/v6_readiness_evidence.py) into
[`readiness_evidence.json`](readiness_evidence.json), from signed v5 stage
records whose hash and signature are verified on read. The two replications
that raised at Gate 4 wrote no Gate-4 record; their headroom tables are
recomputed from retained scored rows by `gate4_payload`'s own rule, and the
tool aborts unless the recomputation reproduces every value in the two signed
Gate-4 records and every failing cell in the two signed terminal reports. It
does — 21 checks, all agreeing — and the per-replication row totals it derives
independently reproduce `reports/dci1v5/closure.json` exactly.

---

## 0. Headline

The proposal's scientific intent is sound and is carried forward unchanged. Its
two mechanisms are not yet executable, and the audit found one thing the
proposal does not know:

> **§12.6's candidate expansion cannot reach a single Tier-1 reserve rung, on
> any replication, in either round.** The Tier-1 reserve was widened from
> 1..10 to 1..12 *specifically* to supply C4's within-family span, and the
> rule that reads the reserve is structurally incapable of selecting from it.
> 32 rungs per replication were provisioned and never measurable.

This does not change any v5 outcome and nothing here re-opens v5: the C4
verdicts are correct given what was measured, the records stand, and no
replication is re-run. It changes the **diagnosis**: part of what
`survival_diagnosis.md` attributes to library shape is the expansion rule
being unable to use the library it already has. Change 1 must therefore begin
with reachability, not with authoring.

The audit also found that the proposal's `delta = 0.05` is smaller than the
error the probe would have to absorb, and that Change 2's probe cannot see the
failure mode that actually terminated `gemma-3n-e4b-it`. Both are quantified
in §4.

**Added 2026-08-25, after implementation began.** Repairing V6-E01 exposed a
second defect in the same rule, independent of it and larger — **V6-E02** —
and §9 records what has since been built. Both are read from
[`expansion_dryrun.json`](expansion_dryrun.json), produced by
[`tools/v6_expansion_dryrun.py`](../../tools/v6_expansion_dryrun.py), which
replays v5's rule and v6's side by side on the four signed pre-screen tables
and refuses to report anything unless its baseline reproduces each signed
coverage verdict exactly.

> **§12.6's expansion measured rungs its own coverage criterion could not
> see.** `run_expansion` extended its working table with raw
> `difficulty_table` rows, which carry no `eligible` field, and
> `coverage_criterion` filters on `eligible` before anything else. The three
> replications that ran an expansion measured 93, 96 and 99 reserve rungs
> across two rounds; their recorded coverage was evaluated over 174, 179 and
> 174 eligible rungs against 208, 211 and 229 actually measured **and
> carried**. Over the full measured table, `qwen3-4b` reaches `C4 = True` and
> `decisive_met = True` where its signed record has both False.

**That is not a re-verdict and may not be cited as one.** v5's coverage is what
v5's registered code computed over the rows that code passed it; the record is
signed, D6 is irreversible, and `qwen3-4b`'s
`REFERENCE_SUPPORT_NOT_IDENTIFIED` remains that replication's terminal outcome.
It is development evidence about the v5 *implementation*, obtained after
closure. It narrows the diagnosis further and in the same direction: V6-E01
stopped the expansion reaching the reserve C4 needed, and V6-E02 stopped
anything it did reach from counting.

---

## 1. Carried forward unchanged

Everything the proposal lists under *What v6 keeps unchanged* is confirmed
against the implementation and carried without amendment:

- the primary question, `Delta_j`, `Delta_R`, `Xi`, and the companion-specific
  identification goal;
- interaction-blind reference selection; no B+R composed outcome may enter
  reference selection (§13.11's schema refusal);
- D6-style **irreversible** non-identification;
- a prospective freeze before any confirmatory data, one-shot masking, §31's
  prohibition on post-outcome repair, reselection or re-expansion;
- the claim ladder L1–L4 with **L5 permanently withheld**, the multiplicity
  families F1–F11, the estimators, the block bootstrap, §17.2's
  refit-per-replicate;
- **every threshold**: §13.4's `HEADROOM_BAND` $[0.10,0.90]$, §13.8's
  calipers, §13.14's `COMPOSED_HEADROOM_BAND` $[0.05,0.95]$, C4's
  ≥6 groups / ≥3 rungs / ≥0.40 span, D17's construct floor, D18's precondition;
- U4 = E2 (eligibility on $p_{\text{solo}}$), carried as resolved;
- §6.1's cross-replication firewall: four replications, each analysed
  separately, **never pooled**, no cross-model scalar carrying a claim;
- the write-once stage lifecycle (18 stages, 19 if §3.2 is adopted),
  `verifier_source_hash` at stage entry and
  exit, §19's non-waivable prefreeze checks, §32 supersession, and one
  scientific stage per checkpoint.

**No threshold is relaxed anywhere in this memo.** Every specified change adds
measurement or supply, or repairs a mechanism that cannot deliver what the
registered rule asks of it.

---

## 2. Proposed modifications, as audited

| # | proposal | audit verdict |
|---|---|---|
| **1** | extend the candidate library (L1–L4) | **Re-scoped.** A reachability defect must be fixed first; whether new authoring is *also* needed is not answerable without one cheap development measurement. §3.1 |
| **2** | `GATE_2_75_COMPOSED_PROBE` with margin $\delta$ | **Specified, with two scope limits the proposal does not state.** §3.2 |
| **3** | `delta = 0.05` | **Not defensible as stated.** The probe *measures* the composition term, so $\delta$ has to absorb the residual — the calibration→composed split transfer, which reached **+0.189** across slots and exceeded 0.05 on two of four B slots, plus an unmeasured stand-in→reference term on top. §4 |
| **4** | ≥2 survivors before *any* confirmatory generation | **Conflicts with §6.1 and the claim ladder.** §5, decision R4 |
| **5** | model panel unchanged | **Sufficient, conditionally.** §3.5 |

The proposal's framing of the probe as using "no outcome quantity" is
**corrected** throughout: the probe measures *compliance*, which is the same
kind of quantity §13.14 already governs, on the calibration split. It is blind
to any *reference* and to any *composed contrast*, which is what makes it
interaction-blind. It is not free of outcomes.

---

## 3. Deterministic operational specification

### 3.1 Candidate-library extension (Change 1)

**C4 itself is unchanged**: `COVERAGE_MIN_STRADDLING_FAMILIES = 6`,
`COVERAGE_MIN_RUNGS_PER_STRADDLING_FAMILY = 3`,
`COVERAGE_MIN_WITHIN_FAMILY_SPAN = 0.40`.

#### 3.1.a The reachability defect (V6-E01)

`stages/regime.expansion_round` admits, per family: if the family's measured
rungs bracket $\iota_A$, the reserve rungs lying **strictly between** the two
adjacent measured edges that bracket it; otherwise the reserve rungs
immediately beyond the extreme measured severity on the deficient side.
Direction is by restrictiveness, not by raw severity.

Replaying that rule on all four signed pre-screen tables, from the registered
round-0 ladders:

| replication | Tier-1 rungs admitted, round 1 | Tier-1 rungs admitted in the signed run | rounds run |
|---|---|---|---|
| `gemma-3n-e2b-it` | none | none | 2 |
| `gemma-3n-e4b-it` | none | none | 2 |
| `qwen3-4b` | none | none | 2 |
| `qwen3-4b-instruct-2507` | none | none | 0 |

Two independent reasons, both structural:

1. **Straddling families take the bracketing branch, and it is always empty.**
   The bracketing edges are the most restrictive measured rung below $\iota_A$
   and the least restrictive above it. Every rung between those two is already
   in the round-0 ladder 1..8, so the pick set is empty. On
   `gemma-3n-e2b-it`, `MK1` has edges $q = 2$ and $q = 8$ and unmeasured
   reserve $\{9,10,11,12\}$ — all beyond the upper edge, none between.
2. **One-sided families are one-sided *below*, and the branch goes the wrong
   way.** With every measured rung harder than A, the rule goes easier; the
   unmeasured Tier-1 reserve is harder. Empty again.

And the deeper point: **interpolation cannot raise a span at all.** C4's span
is $\max\iota - \min\iota$ over a family's eligible rungs. A rung admitted
strictly between two measured edges cannot lie outside their range. So on the
one condition that failed — C4, and on three replications specifically its
0.40 span — the registered expansion mechanism is incapable of helping *by
construction*, whatever the model does.

The families that missed C4 on span alone (`marker_thus` 0.21–0.38,
`marker_hence` 0.29–0.33, `marker_namely` 0.29, `marker_indeed` 0.29,
`letter_a` 0.36, `sentence` 0.37) are exactly the ones stranded in branch 1.

#### 3.1.a′ The second defect (V6-E02), found while repairing the first

`run_expansion` extends its working table with whatever `measure()` returns,
and the production `measure_reserve` returns raw `difficulty_table` rows.
Those carry `family`, `severity` and `iota` — and no `eligible`, no
`structural_tier`, no `feature_group`, no `constraint_class`.
`coverage_criterion`'s first line is `rows = [r for r in table if
r.get("eligible")]`. So every rung the expansion measured was silently dropped
from the criterion the expansion exists to satisfy.

| replication | rounds | rungs the expansion measured | eligible rungs the criterion used | eligible rungs actually measured | `decisive_met` signed | over the full table |
|---|---:|---:|---:|---:|---|---|
| `gemma-3n-e2b-it` | 2 | 93 | 174 | 208 | False | False |
| `gemma-3n-e4b-it` | 2 | 96 | 179 | 211 | False | False |
| `qwen3-4b` | 2 | 99 | 174 | 229 | False | **True** |
| `qwen3-4b-instruct-2507` | 0 | — | 164 | 164 | True | True |

The recomputation is validated before it is reported: restricting the table to
the round-0 rungs reproduces each signed `expansion.coverage` **exactly**, on
all four replications, and the tool aborts if it does not. So the rule applied
is the registered rule and the only thing that differs is which rows reach it.

**The standing of the `qwen3-4b` row.** DEVELOPMENT_EVIDENCE about the v5
implementation. It is not a re-verdict, not a recomputed result, and not
evidence that any replication was identified: v5's coverage is what v5's code
computed, the record is signed, D6 is irreversible, and no v5 replication is
re-run or re-read. It is reported because v6 must not repeat the defect and
because it narrows the diagnosis.

**The repair.** `measure()` returns rows in the criterion's own shape, and
`assert_coverage_shape` refuses any other — on the mandatory path, so the same
class of defect raises instead of passing.

#### 3.1.b Specification: reachability repair

A deterministic replacement for `expansion_round`'s per-family selection,
reading only $\iota$ and severity, picking only from the frozen reserve,
deterministic given the table, and preserving the ≤4-rungs-per-family-per-round
and ≤2-round caps:

> **E1 — deficiency.** For each family, compute over its *eligible* measured
> rungs: `has_below`, `has_above`, `n_rungs`, and `span`. Evaluate C4's three
> conditions in the registered order and take the **first unmet** one as the
> family's deficiency: `MISSING_SIDE` (¬`has_below` ∨ ¬`has_above`), then
> `TOO_FEW_RUNGS` (`n_rungs` < 3), then `SPAN_SHORT` (`span` < 0.40). A
> family that meets all three already contributes a straddling group and is
> skipped. Exactly one deficiency drives direction, so E2 is single-valued.
>
> **E2 — direction.** `MISSING_SIDE` → extend toward the absent side, by
> restrictiveness, exactly as today. `TOO_FEW_RUNGS` → interpolate, exactly as
> today. `SPAN_SHORT` → **extend outward from both extremes**, alternating
> harder-then-easier by restrictiveness, starting from the extreme whose
> unmeasured reserve is non-empty; this is the branch that does not exist
> today and it is the whole repair.
>
> **E3 — ordering.** Within a direction, candidates are ordered by
> restrictiveness distance from the extreme they extend, nearest first; ties
> by ascending raw severity. Deterministic and independent of any outcome.
>
> **E4 — stopping.** Unchanged: the loop stops the moment C1–C6 pass;
> `EXPANSION_MAX_ROUNDS = 2`;
> `EXPANSION_MAX_RUNGS_PER_FAMILY_PER_ROUND = 4`; an empty plan records
> `CANDIDATE_RESERVE_EXHAUSTED`.
>
> **E5 — non-monotonic $\iota$.** $\iota$ is measurably non-monotonic in
> severity for the marker families (on `gemma-3n-e2b-it`, `MK1` runs
> 0.581, 0.792, 0.792, 0.750, 0.541, 0.458, 0.416, 0.417). The rule therefore
> never assumes monotonicity: it orders **candidates** by restrictiveness (a
> structural property of the predicate, known before any data) and evaluates
> **deficiency** on measured $\iota$ after the fact. A rung that fails to move
> $\iota$ outward is a measurement, not an error; the next round simply sees
> the updated table. `MISSING_SIDE` and `SPAN_SHORT` may select the same
> severity, which is admitted once.
>
> **E6 — no new authoring.** E1–E5 select only from §7.10's already-frozen
> reserve. The reserve is unchanged, the vocabulary stays frozen, and
> `assert_no_zero_rung` / `assert_marker_vocabulary` / `assert_library_sizes`
> are unchanged.

**Upper bound on what this can buy, and its honest limit.** For a chance-free
marker $\iota = p_{\text{solo}}$, and §12.6's eligibility floors
$p_{\text{solo}}$ at 0.10, so the largest span a family can reach is
$\max\iota_{\text{eligible}} - 0.10$. Across the **14** near-miss families
(straddling, ≥3 rungs, missing only the 0.40 span) on the four replications,
that bound runs **0.608 to 0.775** — every one of them clears 0.40 with room,
so C4's span is reachable *in principle* on all of them.

Whether the added rungs actually land there is **not knowable from closed v5
data**: it needs the measurement in §7.3. `MK1` on `gemma-3n-e2b-it` had
already flattened at 0.417 and 0.416 by $q = 7, 8$ and may not fall further.
**This memo does not claim the repair would have saved any v5 replication, and
no such claim may be made.**

#### 3.1.c Specification: L1–L4, conditional on §3.1.b

The proposal's L1–L4 stand **only if** §3.1.b proves insufficient, which one
cheap development measurement decides (§7). Restated exactly, for that case:

- **L1 (extension target).** Per family, extend the frozen reserve until the
  measured $\iota$ span on the development models reaches ≥ 0.55, or the next
  rung by restrictiveness falls outside $p_{\text{solo}} \in [0.10, 0.90]$,
  whichever comes first. 0.55 = 0.40 + the largest observed
  screen→calibration attrition. **The 0.55 target is design fitting on v5 and
  is prospectively tested by v6, not established by it.**
- **L2 (supply target).** ≥10 feature groups per development model carrying a
  straddling family. C4 requires 6.
- **L3 (structural distinctness).** A new family declares a **new
  `feature_group` and a new `discourse_role`** under §7.3, is not another
  marker count, and satisfies `Family.__post_init__` in full: form/class
  agreement, ladder ⊆ reserve, §7.6's marker rules where they apply, §7.7's
  non-entailment obligation against every registered family, and §10.2
  carry-over evidence for its counting statistic — a **new** numerator earns
  its own §10.2 evidence and cannot borrow one.
- **L4 (freezing point).** The library is fixed and hashed **before v6
  registration**: it is verifier semantics, so it sits inside the modules
  `verifier_source_hash()` covers, the manifest binds that hash, and no rung
  may be added after `GATE_0_APPARATUS`. §32 supersession is the only legal
  route to a different library, and past Gate 0 it discards the replication.

**Ordering, severity and hashing are therefore fully determined**: severity
order is `restrictiveness_key`, which already exists and is already the
registered notion of direction; the freeze point is the existing
`verifier_source_hash` boundary; no new hashing mechanism is required.

### 3.2 `GATE_2_75_COMPOSED_PROBE` (Change 2)

**Placement.** Between `GATE_2_5_CANDIDATE_QUALIFICATION` and `GATE_3A`.
`STAGE_SEQUENCE` becomes 19 stages; `STAGE_ARTIFACT_TYPE` gains an entry
mapping it to `calibration_record`; `STAGE_RECORD_FILES` gains
`gate2_75_composed_probe.json`; `GENERATION_STAGES` gains the stage;
`VERIFIER_BOUND_ENTRY_POINTS` gains `composed_probe`. `PREDECESSOR` derives
from the sequence, so `assert_predecessor_passed` and
`assert_transition_legal` need no change. The runner takes `device` and is
therefore picked up automatically by `cli.generating_stages()`, which derives
from the signature (A6).

**Inputs.** The Gate-2 record ($m^*$, $n^*$, B's solo curve over the measured
focal grid) and the Gate-2.5 record (the qualified pool — read for **nothing
but its existence**; the probe must not read which candidates qualified).
It does **not** read Gate 3A, 3B or 3C, which have not run.

**Topic split, draws, cells, scoring.** Calibration split, pooled A and B
(`N_CALIBRATION = 192` topics), `M_CAL` draws, scored by the same
`generate_and_score` path and the same verifier hash as every other stage. Per
probed severity $m$: `solo:B`, and `pair:B+S` and `pair:S+B` for each frozen
stand-in $S$, plus the unconstrained cell.

**Prospectively frozen structural stand-ins (P1) — specified.** The proposal
says "structural stand-ins" without saying what one is, and the choice is
load-bearing, because v5 shows the composed lift on B depends strongly on
which companion and in which order:

| replication | composed lift on B, by cell | spread |
|---|---|---|
| `gemma-3n-e2b-it` | A+B −0.167 · B+A +0.021 · B+CL +0.104 · CL+B −0.073 | **0.271** |
| `gemma-3n-e4b-it` | A+B −0.198 · B+A −0.031 · B+CL +0.031 · CL+B −0.083 | **0.229** |
| `qwen3-4b` | A+B +0.052 · B+A +0.052 | 0.000 |
| `qwen3-4b-instruct-2507` | eight cells, +0.052 to +0.177 | **0.125** |

A stand-in that is not the eventual reference estimates the lift with that
order of error, and **A is the worst available stand-in**: it is the study's
own target constraint and it *lowers* B on two replications where a reference
*raises* it. The specification is therefore:

> **S1.** A stand-in is a registered instrument carrying `probe_only = True`.
> **S2.** A `probe_only` instrument is excluded by construction from
> `FAMILY_IDS`'s selectable pool: it may not be carried by the screen,
> qualified at Gate 2.5, calibrated at Gate 3A, or bound to any slot at Gate
> 3B. This is enforced the way §13.14's no-substitution guarantee is —
> a static assertion that no function admits one, plus a runtime refusal in
> `carry_candidate` and in `slot_map_from_record`.
> **S3.** Three stand-ins are frozen pre-registration, spanning §7.3's
> structural range: one Tier-1-shaped exact-count marker, one budget-form
> count, one lower-bound form. Each declares a `feature_group` and
> `discourse_role` **not used by any selectable family**, so no stand-in can
> collide with a later reference's group.
> **S4.** Each stand-in's probe severity is chosen from its own solo curve
> measured **in this stage**, targeting `FOCAL_AIM`-equivalent compliance by
> `select_operating_point`'s existing rule. No reference, no candidate and no
> composed contrast enters that choice.
> **S5.** Stand-ins are frozen with the library at §3.1.c L4 and are covered
> by `verifier_source_hash`.

**Proof that selected B+R outcomes cannot enter this stage or reference
selection.** Four independent guarantees. Two already exist unchanged (1, 3's
schema half); one is new specification (2); one is an extension that must be
written (3's audit half):

1. **Temporal.** The stage runs before `GATE_3A`. No reference exists: Gate 3B
   has not run, `slot_map` is empty, and `assert_predecessor_passed` refuses
   any stage whose predecessor has not recorded PASS. There is no R to compose.
2. **Structural (S2).** Stand-ins are not selectable, so no probed cell can
   ever be a $B{+}R$ cell even by coincidence of instrument identity.
3. **Informational.** §13.11's schema refusal already rejects any composed
   outcome reaching reference selection: `load_calibration_table` takes a
   closed schema, and a composed-outcome field has nowhere to land. **One
   extension is required and does not come free**: §33 check 8 today reads the
   **Gate-4 record only** (`audit_prefreeze._check_8(gate4_record)`), scanning
   its fields for `SELECTION_TOKENS` and requiring the `DECLARED_REFUSALS_KEY`
   block. It must be extended to read the Gate-2.75 record on the same terms,
   with its own declared refusals — otherwise the probe is the one generating
   stage whose record no name-scan audits.
4. **Directional.** The stage writes one value that a later stage reads —
   $m^*$ — and $m^*$ is B's own severity, not a reference. Add
   `assert_probe_reads_no_reference` to the stage module in the style of
   `assert_no_substitution_path`, refusing by name any function that would
   read a selection record.

**One-time $m^*$ reselection (P3) — specified.**

> **P3.1.** Let $\mathcal{M}$ be the severities Gate 2 recorded as *eligible*
> (`focal_selection["eligible"]`) — the registered grid, plus §7.2's extension
> iff §12.3 escalated. The probe measures $m^*$ first.
> **P3.2.** $m$ **passes the margin** iff every probed cell of that $m$, on
> every evaluated slot, lies inside $[0.05 + \delta,\ 0.95 - \delta]$.
> **P3.3.** If $m^*$ passes, it stands and no reselection occurs. Record
> `reselected: false`.
> **P3.4.** If $m^*$ fails, probe the remaining $m \in \mathcal{M}$ in
> ascending order, then re-apply `select_operating_point` **unchanged** — same
> `FOCAL_BAND`, same `FOCAL_AIM`, `prefer_smaller=True` — over **Gate 2's own
> solo B curve**, with the grid restricted to the severities that passed
> P3.2. The selection input is the already-measured solo curve, not the probe;
> the probe decides only *which severities are admissible*, never which is
> chosen. Record `reselected: true` with the full probed table. One
> re-selection, by a rule fixed before data, over a set fixed at Gate 2.
> **P3.5.** No second reselection exists. There is no path from a Gate-3,
> Gate-4 or prefreeze outcome back to this stage; `assert_transition_legal`
> makes the record write-once and `assert_no_post_freeze_mutation` blocks a
> later rewrite.
> **P3.6.** If **no** $m \in \mathcal{M}$ passes P3.2, raise
> `COMPOSED_HEADROOM_UNREACHABLE`.

**`COMPOSED_HEADROOM_UNREACHABLE` — registered as a §28 terminal status.**
Added to `TERMINAL_STATUSES` (14 in force); raised via `TerminalStatus` with
`gate = GATE_2_75_COMPOSED_PROBE`, `criterion` naming §13.14's band and the
registered $\delta$, `observed` carrying the full probed table, and
`strongest_permissible_statement = C.TERMINAL_SENTENCE`. A §28.3
`terminal_report.json` is written. **The A8 regression test that walks the AST
of every module for a status in force with no reachable `raise` covers it
automatically** — that test is why this status cannot repeat V5-E32.

**Two scope limits the proposal does not state.**

- **The probe protects the B slot only.** Gate 4 evaluates every slot of every
  registered cell type. `gemma-3n-e4b-it` failed on `solo:CL` = 0.9583 — a
  *companion* slot in a *solo* cell, with no composition and no B involved. No
  probe at $m^*$ against a stand-in can see that, because CL is selected two
  stages later. One of the four registered Gate-4 failure entries is of this
  kind. **Change 2 as specified would not have prevented `gemma-3n-e4b-it`'s
  termination.**
- **Success at Change 1 multiplies exposure at Gate 4.** The number of
  cell × slot entries audited against the hard band is derived from the
  admitted arm set: base 6, base+class 11, base+core 45, base+core+class 50,
  all five arms **95**. Change 1 exists to make identification succeed, so it
  mechanically raises Gate-4 exposure by up to 16×, each entry measured on 24
  topics. The two bottlenecks are independent *as counterfactuals on v5* — and
  they are **coupled going forward**, in the direction that makes v6 harder.

### 3.3 Headroom margin — see §4.

### 3.4 Confirmatory licensing — see §5, decision R4.

### 3.5 Model panel

**The existing four-model panel is sufficient, conditionally on §3.1.b.** The
reasoning uses v5 as development evidence only:

- All four replications passed Gate 0, the regime screen, and Gates 1, 2, 2.5,
  3A, 3B and 3C. The panel is not failing on apparatus, regime or measurement.
- C4 missed by 2, 1 and 1 groups against a requirement of 6, with 3–4
  span-short families per model available to close it. This is a near miss on
  three of four, not a panel that cannot reach the criterion.
- $\iota_A$ spans 0.624–0.708 across the panel and the number of straddling
  groups tracks it inversely (0.624 → 8 groups; 0.708 → 5). The panel already
  supplies the contrast that makes that relationship visible.

**Adding models would not materially strengthen prospective validation of
Changes 1–2**, because both changes are about the *library* and the *operating
point*, and both are exercised by every replication. A fifth model adds a
replication, not a test of the mechanism.

**If the researcher nonetheless wants held-out models**, the selection rule
must be fixed before v6 registration and must not read v5 outcomes:

> **M1.** Selection is on published architecture-family and parameter-count
> diversity relative to the registered four, plus the §6.1 requirement that
> the exact revision be pinnable and locally servable under the ROCm stack.
> **M2.** No v5 or v4r4 outcome — survival, $\iota_A$, C4 count, Gate-4
> margin — may enter the choice. A model chosen because it *looked* likely to
> survive would make v6's survival rate uninterpretable.
> **M3.** The panel is fixed in the manifest before `GATE_0_APPARATUS`, as §6.1
> already requires.

**Recommendation: keep the four.** Revisit only if §7's development
measurement shows §3.1.b insufficient *and* L1–L4 insufficient.

---

## 4. No-new-data sensitivity: $\delta \in \{0.025, 0.05, 0.075\}$

**$\delta = 0.05$ is treated here as a proposed, v5-informed design choice, and
this section does not choose among the three.** It reports what closed v5
evidence says each would have done. No v5 replication is re-verdicted.

### 4.a What the margin has to absorb

The worst B cell decomposes exactly — calibration solo at $m^*$, plus the
calibration→composed split transfer, plus the composition term:

| replication | $m^*$ | cal. solo B | split transfer | composition | worst B cell | total over cal. solo |
|---|---:|---:|---:|---:|---|---:|
| `gemma-3n-e2b-it` | 10 | 0.8060 | −0.0143 | +0.1042 | 0.8958 `pair:B+CL` | **+0.0898** |
| `gemma-3n-e4b-it` | 10 | 0.8672 | **+0.0807** | +0.0312 | 0.9792 `pair:B+CL` | **+0.1120** |
| `qwen3-4b` | 12 | 0.7695 | **+0.0742** | +0.0521 | 0.8958 `pair:A+B` | **+0.1263** |
| `qwen3-4b-instruct-2507` | 11 | 0.7734 | +0.0391 | **+0.1771** | 0.9896 `pair:B+R1` | **+0.2161** |

A probe on the calibration split **measures** the composition term (against a
stand-in) and must **budget**, in $\delta$, for two errors it does not measure:

1. **Split transfer**, calibration → composed. Across all 13 solo slot
   measurements available on the closed run, the realised movement of one
   instrument's own solo compliance between the split it is *admitted* on
   (§13.4, 192 topics) and the split it is *audited* on (§13.14, 24 topics)
   is: mean absolute **0.064**, maximum **+0.189**
   (`gemma-3n-e4b-it`, `RF12:7` in the CL slot: 0.7695 → 0.9583). Part is
   sampling error at 24 topics and part is a real topic-set difference; this
   memo separates neither and reports the realised movement only.
2. **Stand-in → selected reference.** Not measurable from v5 at all: v5 never
   composed B with a stand-in. The nearest available bound is the
   companion-and-order spread of the composed lift on B, §3.2: **0.125 to
   0.271** on three of four replications.

**None of the three covers term 1 at its maximum (0.189).** 0.075 exceeds term
1's *mean* absolute value (0.064) by 0.011, which leaves essentially nothing
for term 2; 0.025 and 0.05 do not reach the mean at all.

### 4.b What each $\delta$ flags, applied to the realised Gate-4 tables

Descriptive only. This asks how discriminating each margin is; it does not
re-run Gate 4 and does not change any recorded verdict.

| $\delta$ | margin band | `e2b` (11 entries) | `e4b` (11) | `qwen3-4b` (6) | `qwen-instruct` (45) |
|---|---|---|---|---|---|
| 0.025 | [0.075, 0.925] | 0 | 4 (2 real) | 0 | 10 (2 real) |
| 0.050 | [0.100, 0.900] | 0 | 6 (2 real) | 0 | 11 (2 real) |
| 0.075 | [0.125, 0.875] | 1 | 6 (2 real) | 2 | 13 (2 real) |

"real" = also outside §13.14's registered $[0.05, 0.95]$, i.e. an actual band
violation rather than a margin flag.

Reading, stated carefully:

- **Every $\delta$ separates the two terminated replications from the two that
  passed**, which is the minimum a margin must do.
- **$\delta = 0.025$ already flags both terminations.** Raising to 0.05 adds
  two further flags on `e4b` and one on `qwen-instruct`, all margin-only.
  Raising to 0.075 begins flagging the *survivors* (`e2b` at `pair:B+CL`
  0.8958; `qwen3-4b` at both A+B and B+A 0.8958) — i.e. at 0.075 the margin
  starts costing operating points that in fact cleared the band.
- On this evidence **the three $\delta$ values are not well separated by their
  discrimination**, and are separated by their **cost**: larger $\delta$
  shrinks $\mathcal{M}$ and raises the `COMPOSED_HEADROOM_UNREACHABLE` rate.
- **The binding constraint is not $\delta$'s value at all.** All three are
  smaller than the split transfer the probe must absorb (§4.a). Choosing among
  them without addressing the split changes little; addressing the split
  changes a great deal. That is decision R2 and R3.

### 4.c The Gate-4 precision mismatch

Falling out of §4.a, and material to v6 whether or not Change 2 is adopted:
§13.4 admits a companion on 192 calibration topics × `M_CAL` draws, and
§13.14 audits it on **24** reserved composed topics × `M_CAL` draws — a hard
binary verdict against a fixed band, on 12.5% of the topics the admission
decision used. On the full arm set that verdict is taken over **95**
cell × slot entries at that precision. This is a registered design property,
not a defect, and no threshold change is proposed. It is surfaced because it
is the largest single lever on v6 survival, it is untouched by the proposal,
and any change to it is a researcher decision (R3).

---

## 5. Unresolved researcher decisions

Each would materially alter the estimand, the evidential interpretation, or
the scientific design. **None is taken here.** Every stage that depends on one
must be blocked by `protocol/decisions.py` in the v6 tree, exactly as §34's
nineteen v5 decisions are, so that no stage can run while one is open.

### R1 — Does Change 1 begin with reachability, authoring, or both?

| option | consequence |
|---|---|
| **(a) Reachability only** (§3.1.b), then re-measure | Cheapest and least invasive. The vocabulary stays frozen, no §10.2 evidence is needed, no new construct enters the study. Risk: the repair may not deliver the span, and v6 registers with the same C4 exposure. |
| **(b) Reachability + L1–L4** | Highest probability of clearing C4. Cost: new families need §10.2 carry-over evidence, §7.7 non-entailment against every registered family, and Gate 1 measurement evidence. Adds ≥1 registered construct to the study's scope. |
| **(c) L1–L4 only** | **Not defensible.** Leaves a mechanism that provably cannot reach its own reserve; new families would inherit the same unreachability. |

**Recommendation: (a), then decide.** The measurement in §7 separates them for
~0.8k rows per replication, and (b) remains fully available afterwards.
Registering (b) before knowing whether (a) suffices would add constructs to
the estimand's supporting apparatus that may be unnecessary — and §30's
precedent then makes v6 the prospective test of *those* too.

### R2 — Which split does the probe run on, and what does $\delta$ then cover?

| option | consequence |
|---|---|
| **(a) Calibration split, $\delta$ absorbs the transfer** (as proposed) | Spends no reserved topics, and the probe is measured on 192 topics — the most precise option available. Requires $\delta$ to cover a transfer whose realised magnitude reached 0.189, plus an unmeasured stand-in term; at that size $\mathcal{M}$ shrinks sharply and `COMPOSED_HEADROOM_UNREACHABLE` may become the modal outcome. |
| **(b) Probe on the reserved composed split** | Removes the split-transfer term *as a bias*. But §6.2 spends a reserved set once, so this needs `COMPOSED_PER_AREA` 2 → 4 (`N_COMPOSED` 24 → 48, `N_SEQUESTERED` 96 → 72) with a registered disjoint half per stage — and the probe then runs on **24** topics, so it trades a bias for roughly 2.8× the sampling variance. It does not make the probe more accurate; it makes it differently wrong. |
| **(c) Calibration split, and measure the transfer** | The probe measures its stand-ins on both calibration sub-splits (A and B are already independent 96-topic splits, and §13.7 already uses them this way) and records the realised split-to-split movement alongside the margin verdict. $\delta$ is then *checked against a measurement made in the same stage* rather than assumed. Costs no reserved topics and no extra rows — the two sub-splits are already generated. |

**Recommendation: (c), and treat (b) as a question about Gate 4's own
precision rather than about the probe** — which is R3. (c) is the only option
that makes $\delta$ auditable at the moment it is applied, and it uses
machinery §13.7 already registers. It does not eliminate the
calibration→composed transfer; nothing available does, because the composed
set may be measured once. It makes the size of the assumption visible on the
record instead of buried in a constant.

### R3 — Is Gate 4's 24-topic precision left as registered?

| option | consequence |
|---|---|
| **(a) Leave it** | No amendment. Gate 4 stays a 24-topic binary verdict over up to 95 entries. Preserves exact comparability of the §13.14 criterion with v5. |
| **(b) Enlarge the composed set** (couples to R2(b)) | Halves the sampling component of the split transfer and of the extreme-value bias over 95 entries. Cost is rows only; the *criterion* $[0.05, 0.95]$ is untouched, so this is **not** a threshold relaxation. |
| **(c) Evaluate the band on an interval rather than a point** | Principled — it is what §13.4 already does, admitting on the *interval* precisely so an imprecisely measured candidate cannot sit on the boundary. But it changes what §13.14 *means* and is not comparable with v5's Gate 4. |

**Recommendation: (b).** It is the only change in this memo that attacks the
sampling half of §4.a's transfer at its source, it leaves the criterion
$[0.05, 0.95]$ untouched so it is **not** a threshold relaxation, and it costs
rows only. Its price is `N_SEQUESTERED` 96 → 72, which is a governed change to
§6.2's bank and therefore the researcher's. (c) is a change to a reviewed
scientific definition and should not be bundled with this work.

### R4 — What licenses confirmatory generation?

| option | consequence |
|---|---|
| **(A) ≥2 identified Gate-5 survivors before *any* confirmatory generation** (as proposed) | **Withholds every registered claim from a legitimately identified, frozen replication because a *different* replication failed.** §6.1 registers four replications "each analysed separately, each a moderator level and never pooled", and **L5 — generalisation — is *never* licensed by this design**. So there is no registered study-level claim that a 2-survivor rule protects. Compute: 0 or ~2 × 110k confirmatory rows; nothing in between. |
| **(B) Each independently identified and frozen replication may generate; ≥2 survivors required only for replicated/generalised study-level statements** | Matches §6.1 and the claim ladder exactly: L1–L4 are per-replication and per-member, L4a is across *configurations* (orders) within a replication, not across models. A single survivor yields its own registered claim ladder and nothing above it. Compute scales with the number of survivors and with each one's admitted arm set (§8.a). |

**The registered ambiguity this decision rested on is now closed — by the
registered text, not by a choice.** The question was real: §11.1's glossary
defines a configuration as the tuple *(model checkpoint, position of the
outcome constraint)*, while `protocol/constants.py` registers
`CONFIGURATIONS = (outcome_first, outcome_second)` — position only — and the
analysis runs per `ModelTree`. Four registered passages settle it, and none of
them is code:

1. **§15, first paragraph.** "Families are declared per configuration, meaning
   per (model, position of the outcome constraint) — with one exception, F11,
   which is declared **across the two configurations of one model**… **There
   is no cross-model multiplicity family, because this protocol licenses no
   pooled-across-model estimand.**" So in this protocol "across
   configurations", applied to a family or a contrast, names the two positions
   of one model.
2. **§3.2's L4b row** gates on "Both configurations analysed" and reads F11,
   which §15 has just declared across the two configurations of one model.
   L4a and L4b are registered as complementary and indexed the same way.
3. **§11.1.** "There are two configurations per model", and the analysis runs
   per replication — so the model index is the `ModelTree`, and the tuple that
   varies inside it is the position. The glossary and the constant agree once
   the model index is read as the tree rather than as an element of the tuple.
4. **§6.1 and L5.** Replications are "each analysed separately… never pooled",
   no cross-model scalar carries a claim, and generalisation is never licensed.

§19's registered L4a regression test is the same reading made executable: it
reproduces v4r4's `gemma-3n-e4b-it` pattern, which is a pattern *within one
model* across its two positions. **L4a is within-replication.**
`analysis/claims.CONFIGURATION_SCOPE` carries the derivation and
`assert_configuration_scope` refuses a caller who widens the set; §33 check 9
runs it. This is a resolved definitional item and **not** a researcher
decision — putting it to the researcher would ask them to choose something the
preregistration already says. What R4 still turns on is unaffected: under
either reading, option A protects no registered claim.

**Recommendation: (B), with the study-level language registered explicitly.**
Option A introduces a cross-replication dependency the preregistration does not
have anywhere else, and its stated rationale — that v5's single survivor was a
single point of failure — is an argument about *Gate 4* survival, not about
what a frozen replication's data is worth. Under (B), v6's minimum useful
outcome is one model's confirmed or refuted ladder; under (A) it is nothing.

Note that (B) still needs one registration: **v6 must state, before data, what
it will and will not say when exactly one replication survives**, so that the
number of survivors cannot be read after the fact as a licence.

### R5 — Is $\delta$ fixed now, and at what value?

Deliberately left open, and it should stay open until R2 and R3 are settled,
because both change what $\delta$ has to cover. Under R2(a) or R2(c) with
Gate 4 left as registered, none of 0.025, 0.05 or 0.075 covers the realised
split transfer (§4.a) and the choice among them is close to arbitrary. Under
R3(b) the sampling half of that transfer shrinks and a small $\delta$ becomes
more defensible — but by how much is not measurable from closed v5 data, since
it needs the enlarged composed set to exist.

**No value is recommended here**, and the evidence does not license one: what
§4 establishes is that the needed margin lies *above* the examined range on
this data, which is a finding about the range, not a choice within it.
Whatever is chosen is a v5-informed design choice, prospectively tested by v6
and not established by it.

### R6 — Do the stand-ins enter the study's registered instrument set?

S1–S5 create three instruments that are measured but never selectable.
**Options:** register them as `probe_only` families inside §7.10's library
(they are then covered by `verifier_source_hash`, Gate 1 certification and the
§30 ledger, at the cost of appearing in the library's declared counts); or
register them as a separate frozen probe vocabulary with its own hash.
**Recommendation: the former** — one hash, one certification path, one place a
reviewer looks. But it changes `N_FAMILIES` and every derived count asserted in
`constraints.py`, so it is a visible change to the registered library and is
the researcher's to approve.

---

## 6. Blockers to adoption and registration

Ordered. Nothing below is waivable, and none may be resolved by weakening a
guard.

**Updated 2026-08-25 after the implementation pass.** A blocker is marked
**OPEN** only when it is still a blocker; the ones the implementation
discharged say what discharged them, because a list that quietly shrinks tells
a reader nothing about what was done.

1. **OPEN — the researcher decisions.** Registered as §34 D19–D25 in
   `dci1v6/protocol/decisions.py`, all UNRESOLVED. D19–D24 are R1–R6; D25 is
   the single-survivor statement R4's recommended branch requires registered
   before data. Each blocks its dependent stages, `assert_decisions_permit` is
   wired for the new stage, and every accessor —
   `composed_probe.probe_split`, `.margin`, `.standins`,
   `budget.composed_topic_plan`, `lifecycle.confirmatory_licensed` — refuses
   through `decisions.choice` rather than defaulting.
2. **Discharged.** V6-E01 is repaired in `dci1v6/stages/regime` (E1–E6) and
   **V6-E02** with it. `tools/v6_expansion_dryrun.py` replays both rules on
   the four signed v5 tables: v5's admits no Tier-1 reserve rung anywhere,
   v6's admits them on every replication.
3. **OPEN — no v6 preregistration document exists**, and no v6
   reference-design spec. `dci1v6.PREREGISTRATION` names
   `user-notes/DCI1_preregistration_v6.md`; `manifest.document_hashes` raises
   `Blocker` because it is not there, so no manifest can be signed. This is
   now an executable refusal with a test on it, not a note.
4. **OPEN — the §6.2 topic-set arithmetic**, pending D21.
   `budget.composed_topic_plan` carries all three branches and refuses while
   the decision is open; the `enlarge_composed_set` branch computes
   `N_COMPOSED` 24 → 48 and `N_SEQUESTERED` 96 → 72 and raises if the bank
   cannot carry it. The bank is governed and the change is the researcher's.
5. **Discharged.** `COMPOSED_HEADROOM_UNREACHABLE` is in `TERMINAL_STATUSES`
   and in `NEW_TERMINAL_STATUSES`, raised from `probe_disposition`, and
   covered by the A8 AST regression that walks every module for a status in
   force with no reachable `raise` — which is the V5-E32 fix.
6. **OPEN — the stand-ins do not exist.** The `probe_only` *mechanism* is
   implemented and its guards are live on the empty population;
   `assert_library_sizes` now asserts `probe_only_families: 0` and
   `selectable_families: 37`, so authoring one fails loudly. Which stand-ins
   exist is D24 and it is the researcher's.
7. **Discharged.** §33 check 8 reads both records —
   `audit_prefreeze.NAME_SCANNED_RECORDS` names Gate 4 and Gate 2.75, each
   with its own admissible outcomes and its own required refusals — and a
   missing probe record is UNRESOLVED, which blocks the freeze.
8. **OPEN — Change 2 does not cover the `gemma-3n-e4b-it` failure mode.** Not
   a blocker to registration, but it must be *stated* in the v6
   preregistration. `composed_probe.PROBE_SCOPE_LIMITS` carries it and the
   probe record does too, so it is on the artifact; what remains is the
   document.
9. **Discharged.** `CHANGES_SCIENTIFIC.md` carries three entries dated
   2026-08-25: V6-E01, V6-E02, and the v6 implementation with what it does
   and does not change.
10. **New, and OPEN — the v6 §34 decisions carry no researcher record.**
    `dci1/reports/dci1v6/researcher_decisions.json` does not exist and must
    not be created by code. Until the researcher writes one, every decision is
    UNRESOLVED at import and no stage can run. The test suite reads a
    *fixture* copy of v5's record so it can exercise the paths D0–D18 select;
    that fixture is in `tests_v6/` and can never reach the registered path.

**Not a blocker, and explicitly so:** none of this touches v5. v5's records,
verdicts, terminal statuses and D6 irreversibility stand exactly as signed.
The `qwen3-4b` recomputation in §3.1.a′ is development evidence about the v5
implementation and is not a re-verdict.

---

## 7. Next coding-agent task

**Updated 2026-08-25.** Steps 1, 2 and 4 are done and §9 records what they
produced. Step 3 is the one measurement that decides R1/D19 and **it is new
behavioural data, so it is not started**. Steps 5 and 6 remain, and 6 has been
done in the sense the code allows — the budget machinery is recomputed and
committed, but the option it costs depends on D1, D21 and D22.

**What remains, in order, and all of it after the researcher decides:**

- **Step 3, and only with explicit approval: the R1/D19 measurement.**
  Re-screen the four models' Tier-1 reserve rungs $q \in \{9,10,11,12\}$ on
  the 24 pre-screen topics at 1 draw: 32 rungs × 24 rows = **768 rows per
  replication, 3,072 total**. It measures whether the extension lands inside
  $p_{\text{solo}} \in [0.10, 0.90]$ and what span it buys — which is what
  separates R1(a) from R1(b), and it cannot be answered from closed v5 data.
  It uses only §12.5's development topic sets and carries no confirmatory
  standing. **Nothing has been generated.**
- **Step 5: author the v6 preregistration document** and the v6
  reference-design spec, and wire `protocol_hash` to them. Until then
  `manifest.document_hashes` raises and no manifest can be signed. This is a
  researcher act.
- **Step 6′: close D19–D25 on a researcher record.** Writing
  `dci1/reports/dci1v6/researcher_decisions.json` is a researcher act and no
  code may do it. Until it exists every decision is UNRESOLVED and no stage
  runs.
- **Step 7: author the stand-ins**, if D24 closes at `probe_only_in_library`.
  This changes `assert_library_sizes`' counts and will fail the assertion
  until the new counts are written in — which is the visibility R6 asks for.
- **Then, and not before: Gate 0.**

---

### 7.1 The original plan, for the record

Ordered, one stage per checkpoint, fail-closed, and **stopping before any new
real behavioural data**:

1. **Implement §3.1.b (E1–E6)** as a replacement for `expansion_round`'s
   per-family selection, in the v6 tree. Regression tests: (i) the four signed
   v5 pre-screen tables as fixtures, asserting the new rule admits ≥1 Tier-1
   reserve rung where the old admits none; (ii) determinism — same table, same
   plan; (iii) the caps hold; (iv) a non-monotonic-$\iota$ fixture built from
   `MK1` on `gemma-3n-e2b-it`; (v) picks ⊆ frozen reserve, always.
   **These fixtures are v5 development evidence used as test data; they are
   not v6 evidence and produce no v6 row.**
2. **Add a `--dry-run` expansion replay** to the v6 CLI that reports, per
   family, what E1–E6 *would* admit given an existing screen table — so step 3
   below is a report over a measurement, not a second run.
3. **The one development measurement that decides R1.** Re-screen the four
   models' Tier-1 reserve rungs $q \in \{9,10,11,12\}$ on the 24 pre-screen
   topics at 1 draw: 32 rungs × 24 rows = **768 rows per replication, 3,072
   total**. It measures whether the extension lands inside
   $p_{\text{solo}} \in [0.10, 0.90]$ and what span it buys. **This is new
   behavioural data and must not be generated until the researcher approves
   it**; it is a v6 *development* measurement, it uses only §12.5's
   development topic sets, and it carries no confirmatory standing.
4. **Implement `GATE_2_75_COMPOSED_PROBE`** per §3.2 — stage constants,
   record file, runner taking `device`, S1–S5 stand-ins,
   `assert_probe_reads_no_reference`, the `DECLARED_REFUSALS_KEY` block, P3.1–
   P3.6, `COMPOSED_HEADROOM_UNREACHABLE` in `TERMINAL_STATUSES`, **and
   §33 check 8 extended from the Gate-4 record to the probe record**, with a
   test that deleting the probe's declared refusals fails the check.
   The A8 AST test covers the raise path automatically; add a direct test that
   a probe with no passing severity raises, and a test that a `probe_only`
   instrument is refused by `carry_candidate` and by `slot_map_from_record`.
5. **Author the v6 preregistration document** and wire `protocol_hash` to it.
6. **Recompute the budget** with `tools/v6_compute_budget.py` (a v6 copy of
   the v5 tool) once R1, R3 and R4 are settled, and commit the JSON.

**Stop there.** No v6 registration, no manifest, no Gate 0.

---

## 8. Compute, lifecycle and provenance

### 8.a Budget

Realised v5, per replication, from the retained rows (independently
reproducing `closure.json`):

| replication | Gate 0 | regime screen | Gate 2 | Gate 4 | total |
|---|---:|---:|---:|---:|---:|
| `gemma-3n-e2b-it` | 2,688 | 10,728 | 100,608 | 768 | **114,792** |
| `gemma-3n-e4b-it` | 2,688 | 10,800 | 102,144 | 768 | **116,400** |
| `qwen3-4b` | 2,688 | 10,872 | 100,608 | 480 | **114,648** |
| `qwen3-4b-instruct-2507` | 2,688 | 8,448 | 99,840 | 2,496 | **113,472** |

Gates 1, 2.5, 3A, 3B and 3C produced no rows: Gate 2.5's $\kappa(R|B)$ needs
no generation of its own (§9.1's presence rule), and `gate3a_payload` reads
Gate 2's `calibration_rows` rather than generating — so although §12's
`GENERATION_STAGES` names Gate 3A, it generated nothing on any replication.
Study total **459,312**.

Marginal cost of each change, per replication, derived from the code's own
constants:

| change | driver | added rows |
|---|---|---:|
| §3.1.b reachability repair, Tier-1 only | 32 Tier-1 reserve rungs enter the screen (24 rows each) | **+768** |
| §3.1.b reachability repair, ceiling | §12.6 permits ≤4 rungs per family per round over 2 rounds; across the library that bounds the expansion at 176 rungs | **up to +4,224** |
| §3.1.b, downstream | §12.7 measures **every** carried Tier-1/Tier-2 rung — the 24-rung Tier-3 cap does not absorb them — at 768 rows per rung. 32 Tier-1 rungs is +24,576; the ceiling is 48 Tier-1/2 rungs | **+24,576, up to +36,864** |
| §3.2 probe, $m^*$ only | 11 cells × 192 pooled calibration topics × `M_CAL`. **Corrected**: the cell set is `2 + 3n` for $n$ stand-ins — unconstrained, B solo, **each stand-in solo**, and both orders of B with each. The stand-in solo cells are not optional, because S4 reads each stand-in's operating point from its own solo curve measured in this stage and the composed lift is measured against it. An earlier count here said 8 cells and omitted them | **+8,448** |
| §3.2 probe, worst case | every severity of §7.1's grid plus §7.2's extension eligible and probed — the code-derived ceiling, 10 severities. On v5's records the realised eligible sets were smaller | **up to +84,480** |
| R3(b), if taken | `N_COMPOSED` 24 → 48 at Gate 4, on the admitted arm set. On v5's realised arm sets that was +480 to +2,496; on D1's registered 56 cells it is 5,376 → 10,752 | **+480 to +5,376** |
| L1–L4, if R1(b) | proportional to added rungs; the proposal's +25–40% on screen and Gate 2 | +25k to +40k |

**Per replication to freeze, under R1(a) + R3(b), from the code's own
constants:**

| term | rows |
|---|---:|
| v5's four calibration terms (screen, focal grids, candidate calibration, pilot) | 110,736 |
| §12.6's expansion, **screen** rows at its ceiling | +4,224 |
| §12.6's expansion, **candidate-calibration** rows at its ceiling | +36,864 |
| Gate 2.75, $m^*$ only / at the ceiling | +8,448 / +84,480 |
| Gate 4 at `N_COMPOSED = 48` (R3(b)); 5,376 if R3(a) | +10,752 |
| **total, expansion not firing and $m^*$ passing** | **~130,000** |
| **total, everything at its ceiling** | **~247,000** |

Four replications to freeze therefore span **~520,000 to ~988,000**, and no
single figure inside that range is more honest than the range: both new terms
are conditional on measurements nobody has made. v5 realised ~115,000 per
replication. Every number here is recomputed by
[`tools/v6_compute_budget.py`](../../tools/v6_compute_budget.py) into
[`development/d1_compute_budget.json`](development/d1_compute_budget.json),
with §12.6's expansion and the probe carried as **named conditional terms**
rather than folded into a figure a replication is expected to spend: the
expansion stops the moment C1–C6 pass and skips any family already meeting
C4, and the probe stops the moment $m^*$ passes its margin.

**v5's budget did not carry the expansion term at all**, and on v5's records
that was harmless for the wrong reason — V6-E02 meant the 93 to 99 rungs it
measured bought nothing. Under the repaired rule the term is real: at most 176
reserve rungs are admissible across the library under §12.6's ≤4-per-family-
per-round and ≤2-round caps, and at most 48 of those are Tier-1 or Tier-2, so
§12.7 — which measures **every** carried Tier-1/2 rung, the 24-rung Tier-3 cap
not absorbing them — carries them at 768 rows each.

**Confirmatory generation is not a single number**: it is
`n_cells(admitted arms) × 384 blocks × 8 draws`, plus §8.3's greedy
sensitivity run, so it scales with what a replication *identifies* — which is
exactly what Change 1 exists to increase.

| admitted arms | cells | confirmatory | + greedy |
|---|---:|---:|---:|
| base | 5 | 15,360 | 480 |
| base + class | 8 | 24,576 | 768 |
| base + core | 26 | 79,872 | 2,496 |
| base + core + class | 29 | 89,088 | 2,784 |
| all five (D1's registered option) | 56 | **172,032** | 5,376 |

The proposal's "~110,000" is v5's *calibration* burden (110,736), not its
confirmatory one. Under R4(B) the confirmatory total is the sum over
survivors, each at its own arm set; under R4(A) it is either zero or the sum
over ≥2, with nothing in between. On D1's registered 56-cell option, two
survivors cost **~355,000** confirmatory rows and four cost **~710,000**
(confirmatory plus greedy).

### 8.b Lifecycle, terminal outcomes, resumability, masking, freeze

Unchanged from v5 except where stated:

- **19 stages**, with `GATE_2_75_COMPOSED_PROBE` between 2.5 and 3A. Stage
  records write-once via `fs.write_json_once`; `assert_predecessor_passed`
  requires a signed PASS; `assert_transition_legal` refuses a second write;
  `assert_no_post_freeze_mutation` blocks any rewrite at or before the freeze.
- **Terminal statuses**: v5's thirteen plus `COMPOSED_HEADROOM_UNREACHABLE`
  (14). `REFERENCE_SUPPORT_NOT_IDENTIFIED` remains admitted to
  `terminal_statuses_in_force()` only when D6 resolves to `terminal`. Every
  status in force has a reachable `raise` — enforced by the A8 AST test, which
  is the V5-E32 fix and covers the new status without modification.
- **Resumability** is engineering-level only: a run interrupted by an
  engineering fault resumes valid exact rows. A scientific gate failure is a
  result and is never resumed, repaired or re-verdicted.
- **Provenance**: `verifier_source_hash()` compared at stage entry and exit,
  failing closed if the source moves mid-run; `protocol_identity` binds each
  row to the manifest hash; §19's `ARTIFACT_CHECKS` including
  `clean_worktree`, `producing_commit_clean`, `protocol_hashes_agree` and
  `support_satisfied`, none waivable, UNRESOLVED never PASS.
- **Masking and freeze**: unchanged. One-shot masking, `MASK_NAMESPACES`
  fixed, `BACKUPS_MAY_SUBSTITUTE_AFTER_GATE_4 = False` with the guarantee
  being that no substitution function exists —
  `assert_no_substitution_path` continues to enforce it by name, and the same
  pattern is extended to the probe as `assert_probe_reads_no_reference`.
- **Supersession**: §32 unchanged. The line is at `GATE_0_APPARATUS`; a
  superseded registration carrying generated rows is a **discarded
  replication**, `invalidated.json` marks `reusable: false`, and invalidated
  rows never re-enter a live study.
- **Execution**: one scientific stage per invocation — complete, sign, mirror,
  verify, return control, then explicitly launch the successor. Both RX 7900
  XTXs run as two independent TP=1 lanes pinned through the backend `device`
  argument, which the CLI forwards only to stages whose runner signature
  accepts it (A6).

---

## 9. Implementation status (added 2026-08-25)

**Nothing here is registered and no v6 row exists.** `dci1/src/dci1v6` is a
package that cannot run: twenty-six §34 decisions are UNRESOLVED, the two
governed documents §18 stage 1 binds do not exist, and
`assert_transition_legal` refuses every stage whose decisions are open. Three
independent refusals, any one of which is sufficient.

### 9.1 What was built

| area | what exists | where |
|---|---|---|
| namespace | `dci1v6`, study id `dci1v6`, `FOREIGN_STUDY_PREFIXES` naming `dci1v5`, evidence root `dci1/evidence/dci1v6` (which does not exist) | `dci1v6/__init__.py`, `engine/context.py` |
| V6-E01 | E1–E6: C4's first unmet condition is the deficiency; `SPAN_SHORT` extends **outward from both extremes** | `stages/regime.expansion_plan_for_family` |
| V6-E02 | `measure()` returns rows in the criterion's shape; `assert_coverage_shape` refuses any other, on the mandatory path | `stages/regime`, `run/regime_run.measure_reserve` |
| the probe | placement, record schema, P3.1–P3.6, the cell shape, `assert_probe_reads_no_reference`, the declared refusals, the scope limits | `stages/composed_probe.py`, `run/gates_run.gate2_75_payload` |
| terminal status | `COMPOSED_HEADROOM_UNREACHABLE`, raised from `probe_disposition` | `protocol/constants`, `stages/composed_probe` |
| stand-ins | the `probe_only` category and its guards, live on an empty population | `verifiers/constraints`, `stages/regime.carry_candidate`, `run/gates_run.slot_map_from_record` |
| audits | §33 check 8 over both records; check 9 extended with L4a's scope; the producer/consumer contract; `generating_stages` picking the probe up from the signature | `stages/audit_prefreeze`, `run/contracts`, `run/cli` |
| licensing | `confirmatory_licensed`, both D22 branches, on the confirmatory path before a row is generated | `run/lifecycle`, `run/confirmatory_run` |
| budget | the confirmatory term as `n_cells × 384 × 8`, plus the expansion and probe as named conditional terms | `design/budget`, `tools/v6_compute_budget.py` |
| the changes themselves | eight registered changes, each with an executable check, asserted on the registration path | `protocol/revision.py` |

**One thing the extended check found immediately, worth recording.** Running
§33 check 8 over the probe record failed it — on the probe's own `reselected`
field, because `reselect` is one of §13.14's five forbidden tokens and P3.3
requires the record to carry exactly that field. An outcome-driven selection
and a registered pre-data one read identically to a name scan, which is the
same problem `declared_refusals` exists for one level down. The resolution is
**one named field with a stated reason** in
`audit_prefreeze.NAME_SCANNED_RECORDS`, not a pattern and not a blanket: any
other field of that record naming a selection still fails, the exempted field
must actually be present so a stale exemption cannot sit unexercised, and the
record must still declare `no_second_reselection_exists`. Gate 4's entry has
no exemptions at all.

### 9.2 What the decisions block, by name

| decision | READINESS | blocks stages | blocks calls |
|---|---|---|---|
| D19 | R1 | `PROTOCOL_REGISTERED` | — |
| D20 | R2 | registration, `GATE_2_75_COMPOSED_PROBE` | `composed_probe.probe_split` |
| D21 | R3 | registration, `GATE_4_COMPOSED_HEADROOM` | `budget.composed_topic_plan` |
| D22 | R4 | registration, `CONFIRMATORY_GENERATION` | `lifecycle.confirmatory_licensed` |
| D23 | R5 | registration, the probe | `composed_probe.margin` |
| D24 | R6 | registration, the probe | `composed_probe.standins` |
| D25 | — | registration, `CONFIRMATORY_GENERATION` | — |

D25 is not in the memo's original six. It is what R4's recommended branch
requires: **v6 must state, before data, what it will and will not say when
exactly one replication survives**, so the number of survivors cannot be read
afterwards as a licence.

### 9.2a What was run against it

| instrument | result |
|---|---|
| `tests_v6` | **490 passed**, including the full **19-stage** synthetic lifecycle end to end: registration → probe → freeze → confirmatory → mask → unmask → final report, in an isolated repository the harness builds and commits, with every provenance rule unwaived |
| producer/consumer contract | **0 defects**, 124 fields across 18 artifacts, **124 exercised** by a real walk, 19 of 19 stages reached; all 12 of the probe's contracted fields written and read |
| execution-path audit | **53 of 53** registered rules hold their expected status — 51 `VERIFIED_REACHABLE`, 2 `VERIFIED_CONDITIONAL` — over 15 conditional scenarios, with 0 contract defects. The three new probe rules and the two new expansion rules are all reachable on the path a replication takes |
| `tests_v5`, `dci1/tests*`, root `tests/unit` | 451 / 1,780 (+10 skipped) / 2,575 (+1 xfailed), all passing — v5 is untouched |

The execution-path audit asks the question the other three cannot: *does the
registered rule lie on the path a replication takes.* It is why V6-E01's
repair is not merely implemented but **observed executing** while the
lifecycle runs.

### 9.3 What is deliberately not implemented

- **The stand-ins themselves.** S1–S5 specify what a stand-in *is*; which
  three exist is D24, and authoring one changes the registered library's
  asserted counts.
- **A value for δ.** `composed_probe.margin` reads D23 and validates that the
  closure leaves §13.14's band with an interior. §4 establishes that the
  needed margin lies *above* the examined range, which is a finding about the
  range and not a choice within it.
- **The topic split and the Gate-4 precision.** Both branches of D20 and all
  three of D21 exist in the source and none is reachable while the decision is
  open.
- **The v6 preregistration and reference-design spec.** Governed documents,
  and a researcher act.
- **Any behavioural data.** Zero rows.

### 9.4 One thing the memo raised that turned out not to be a decision

The §11.1-versus-`CONFIGURATIONS` question in R4 is **closed by the registered
text** — §15's "no cross-model multiplicity family", §3.2's L4b gate, §11.1's
"two configurations per model", §6.1's firewall and L5's permanent withholding
all point one way. L4a is within-replication.
`analysis/claims.CONFIGURATION_SCOPE` carries the derivation,
`assert_configuration_scope` enforces it, and §33 check 9 runs it. Putting it
to the researcher would have been asking them to choose something the
preregistration already says.
