# DCI-1 v6 — preregistration-readiness memo

> **This memo is HISTORY, not the registered protocol.** v6 was adopted and
> registered on 2026-08-26; the registered text is
> [`user-notes/DCI1_preregistration_v6.md`](../../../user-notes/DCI1_preregistration_v6.md)
> and the registered decisions are
> [`researcher_decisions.json`](researcher_decisions.json). Sections are added
> here in order and **never rewritten**: where a later pass superseded an
> earlier conclusion, the earlier one is marked and the later one restates it.
> §13 is the 2026-08-26 red-team pass and §14 the adoption pass. If a
> statement here disagrees with the preregistration, the preregistration is
> what the study registered.
>
> Two supersessions are load-bearing and are flagged where they occur:
> **§3.2's P3 block and §13.4 both describe a one-time m\* reselection that
> was withdrawn** — m\* is frozen at Gate 2 and `GATE_2_75_COMPOSED_PROBE`
> may terminate a replication but never move the operating point (§14.1) —
> and **§13.3's residual table was computed under that withdrawn rule**; the
> current one is §14.2.
>
> §15 is the apparatus-fault pass of 2026-08-26, added after §14. It records
> amendment A15 and corrects one sentence in §14: adoption and registration
> did not happen on the same day's first attempt, and §14.5's account of the
> registered state was written before the study was registered.

**Status when this memo was written: NOT ADOPTED, NOT REGISTERED.** No manifest
existed, no stage had run, and no behavioural row could be generated against
anything here. This memo audits
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

> **Scope superseded by §12.** The two scope limits stated at the end of
> this section were the reason to widen it: the probe now covers all ten
> of §13.14's slot-and-order exposure classes, derived from Gate 4's own
> cell set rather than listed, and `assert_probe_covers_gate4_classes`
> refuses a shape that leaves one uncovered. S4's `FOCAL_AIM`-equivalent
> placement is replaced by placement at Gate 2's measured $\iota_A$, which
> is where §13.8 puts a companion; S3's feature-group requirement is
> dropped, per §12.5. What remains true is every guarantee: temporal,
> structural, informational and directional.

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

> **SUPERSEDED by §14.1.** P3.4's reselection was withdrawn by the researcher
> on 2026-08-26, before any v6 row existed. The registered rule is: m\* is
> frozen at Gate 2, the probe measures composed headroom at m\* and at no
> other severity, and P3.6's terminal status is the whole of the failure
> branch. P3.1's admissibility requirement, P3.2's margin, P3.3's pass and
> P3.5's no-path-back all stand. Kept because it is what the specification
> said when the decision set was audited.

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

### 3.3 Headroom margin — see §4, and then §12.4, which replaces the constant
with a per-entry projected interval.

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

> **Answered in §12.1, and (c) stands with a reason it did not have.** The
> sub-split contrast is not a diagnostic beside the margin: it is the
> estimator of the only non-sampling term in the whole error budget, because
> §6.2 cuts calibration_a and the composed set from one seeded shuffle while
> §34 D3's calibration_b is newly authored. Residual sd 0.0284, halved to
> 0.0142 by the pooling.

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

> **Superseded by §12.3. The recommendation below — (b), enlarge the composed
> set — is not executable in this repository**: §6.2's sequestered eighth was
> never materialised here, so 'take 24 topics from it' is an act of authoring
> topics rather than a change to a constant. The derivation is (a), with the
> precision reasoning moved into Gate 2.75's projection. §12.2 has the
> measurement the recommendation lacked: 0.121 and 0.190 false-termination
> probability at 24 topics on the two replications that were in band.

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

> **Superseded by §12.4.** The question was the wrong one: the error a
> constant was to absorb is sampling, it is measurable per entry, and it now
> lives in a projected Gate-4 interval built by §13.4's own device. What is
> left of D23 is the allowance *beyond* the two measured terms and its
> derived value is 0.0.

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

> **Answered in §12.5.** `probe_only_in_library`, three families authored,
> and S3's 'a feature group no selectable family uses' requirement **dropped**
> — it would need a new statistic, which reorders `FEATURE_GROUP_IDS` and
> therefore `selection.group_key`'s reference-selection tie-break.

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

### R7 — Should §12.6 certify coverage at a *point* of $\iota_A$, or over an interval? (new, 2026-08-25)

**Not a blocker.** A hardening option with a measurement attached, raised by
the audit recorded in §10.

§12.6 evaluates the identification-coverage criterion, spends its two expansion
rounds and **freezes the candidate vocabulary** at `iota_a_prescreen`: A's
compliance on the 24 pre-screen topics at one draw, at the severity nearest
§12.3's aim. The quantity the references are actually matched to is Gate 2's
`iota_a` — 192 calibration topics, four draws, at $n^\*$ — measured two stages
later, when the vocabulary is frozen and the expansion is spent. §13.4 already
acknowledges the movement; nothing acts on it.

**Measured, on the four closed v5 tables** (`iota_a_prescreen` → Gate 2's
`iota_a`; each replication's own round-0 table, and each baseline reproduces
its signed verdict exactly before anything else is reported):

| replication | drift | C4 straddling groups | C3 near rungs | decisive |
|---|---:|---:|---:|---|
| `gemma-3n-e2b-it` | −0.073 | 4 → 4 | 32 → 35 | False → False |
| `gemma-3n-e4b-it` | +0.015 | 5 → 5 | 34 → 36 | False → False |
| `qwen3-4b` | +0.046 | 5 → 5 | 30 → 26 | False → False |
| `qwen3-4b-instruct-2507` | −0.092 | 8 → 8 | 31 → 34 | True → True |

**No decisive condition changes on any of the four.** The gap is structural
and the realised exposure is small.

**Superseded in part by V6-E04 (2026-08-25).** The drift table above is a
comparison *across two samples* — an $\iota(R)$ table measured on 24
pre-screen topics at one draw, read against an $\iota_A$ measured on 192
calibration topics at four — so what it reports is part the reference point
moving and part the two samples, and it separates neither. §11.2 replaces it
with a paired reading on the calibration basis, and that reading **gates**
(§34 D6's existing disposition, no drift threshold). The numbers below stand
as what was measured; they are no longer the reading a decision should rest on.

**Options.** (a) ~~Leave §12.6 as registered and keep the Gate-3A diagnostic
`coverage_at_measured_iota_a`~~ — **taken off the table by V6-E04**: the field
no longer exists and the criterion is now re-evaluated where selection works.
(b) Certify
C1–C4 over an interval $[\iota_A^{\text{pre}} - w, \iota_A^{\text{pre}} + w]$
with $w$ fixed before data, so the expansion is spent on coverage that survives
the drift. (c) Re-open a bounded expansion at Gate 3A when the diagnostic shows
a decisive condition lost — which re-opens the vocabulary after Gate 2 has run,
and is the option with the largest surface.

**Scientific consequence.** (b) is strictly stricter and would have changed no
v5 verdict; it costs reserve rungs and screen rows on every replication, for a
failure mode not observed in four. (c) buys recovery and pays for it by making
the frozen vocabulary conditional on a later stage — which is the property
§12.6 froze it to avoid.

**Implementation consequence.** (a) is done. (b) is a change to
`coverage_criterion`'s signature and to §12.6's registered text, plus a value
for $w$. (c) is a new expansion caller at Gate 3A, new provenance, and a new
terminal branch.

**Recommendation: (a)** — record it, do not gate on it, and revisit if a
replication's diagnostic shows a decisive condition lost. Taking (b) or (c) on
four replications where the criterion was drift-invariant would be tuning
against a failure that has not been observed.

---

## 6. Blockers to adoption and registration

Ordered. Nothing below is waivable, and none may be resolved by weakening a
guard.

**Updated 2026-08-25 after the implementation pass.** A blocker is marked
**OPEN** only when it is still a blocker; the ones the implementation
discharged say what discharged them, because a list that quietly shrinks tells
a reader nothing about what was done.

> **Blockers restated 2026-08-25 by §12.** Four of the seven v6 decisions now
> have a derivation rather than an open question — D19, D20, D21 and D23 — and
> D24's population is authored. **None of them is closed**, because closing a
> §34 decision is an act recorded on `reports/dci1v6/researcher_decisions.json`
> and no code may create that file. The binding blocker is therefore now
> **blocker 10, and it is larger than this list said**: the record must carry
> all twenty-six closures, D0–D18 included. Those nineteen are closed on v5's
> record and carrying them into a new registration is the researcher's act, not
> a transcription.

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
4. **OPEN as a decision, but its recommended branch is now known to be
   unavailable — the §6.2 topic-set arithmetic**, pending D21. §12.3: the
   `enlarge_composed_set` branch would have to draw from a sequestered eighth
   that was never materialised in this repository, so it is an act of authoring
   topics and not a change to a constant. `composed_topic_plan` still carries
   all three branches and still refuses while the decision is open.
   `budget.composed_topic_plan` carries all three branches and refuses while
   the decision is open; the `enlarge_composed_set` branch computes
   `N_COMPOSED` 24 → 48 and `N_SEQUESTERED` 96 → 72 and raises if the bank
   cannot carry it. The bank is governed and the change is the researcher's.
5. **Discharged.** `COMPOSED_HEADROOM_UNREACHABLE` is in `TERMINAL_STATUSES`
   and in `NEW_TERMINAL_STATUSES`, raised from `probe_disposition`, and
   covered by the A8 AST regression that walks every module for a status in
   force with no reachable `raise` — which is the V5-E32 fix.
6. **DISCHARGED 2026-08-25 — the stand-ins now exist.** `PS1`, `PS2` and `PS3`
   are registered `probe_only` families (§12.5); `assert_library_sizes` asserts
   `probe_only_families: 3` and `selectable_families: 37`, and three added
   counts show the selectable population is unmoved at v5's 326 and 632. What
   remains open is D24 itself, which selects whether they live in §7.10's
   library or in a separate vocabulary. *Superseded text follows.*
   ~~OPEN — the stand-ins do not exist.~~ The `probe_only` *mechanism* is
   implemented and its guards are live on the empty population;
   `assert_library_sizes` now asserts `probe_only_families: 0` and
   `selectable_families: 37`, so authoring one fails loudly. Which stand-ins
   exist is D24 and it is the researcher's.
7. **Discharged.** §33 check 8 reads both records —
   `audit_prefreeze.NAME_SCANNED_RECORDS` names Gate 4 and Gate 2.75, each
   with its own admissible outcomes and its own required refusals — and a
   missing probe record is UNRESOLVED, which blocks the freeze.
8. **DISCHARGED in part 2026-08-25, and restated.** The probe now covers the
   `solo:companion` class the `gemma-3n-e4b-it` failure was in, and all nine
   other classes; what it still cannot cover is the companion's **identity**,
   because the reference is selected two stages later. That is the limit the
   preregistration must state, and `composed_probe.PROBE_SCOPE_LIMITS` states
   it in those terms. *Superseded text follows.*
   ~~OPEN — Change 2 does not cover the `gemma-3n-e4b-it` failure mode.~~ Not
   a blocker to registration, but it must be *stated* in the v6
   preregistration. `composed_probe.PROBE_SCOPE_LIMITS` carries it and the
   probe record does too, so it is on the artifact; what remains is the
   document.
9. **Discharged.** `CHANGES_SCIENTIFIC.md` carries three entries dated
   2026-08-25: V6-E01, V6-E02, and the v6 implementation with what it does
   and does not change.
10. **OPEN, and the binding blocker — the v6 §34 decisions carry no researcher
    record.** Restated 2026-08-25: this is not only about D19–D25. `RECORD_PATH`
    is read at import for **all twenty-six**, so D0–D18 — v5's, closed on v5's
    own record — are UNRESOLVED in v6 too, and carrying a closure from one
    registration into another is a researcher act with its own evidence, not a
    copy. *Original text follows.*
    `dci1/reports/dci1v6/researcher_decisions.json` does not exist and must
    not be created by code. Until the researcher writes one, every decision is
    UNRESOLVED at import and no stage can run. The test suite reads a
    *fixture* copy of v5's record so it can exercise the paths D0–D18 select;
    that fixture is in `tests_v6/` and can never reach the registered path.

11. **New, 2026-08-25, and DISCHARGED — V6-E03, in four parts.** The
    probe's re-selection branch could not execute: Gate 2 recorded kappa(R|B)
    at its own m\* only, and §13.11's own guard correctly refused the table at
    the probe's. Gate 2 now records a column, and Gate 2.5 a §13.1 pool, for
    every *admissible* severity — signed before the probe observes a composed
    cell, so §30 holds by construction. The probe is confined to
    `focal_admissible` (§12.3's band **and** §12.4 **and** §34 D17, each
    evaluated at that severity). The freeze binds B, the pool and the
    earliest-failing components at the probe's operating point, not Gate 2's.
    And B is rebuilt through `focal_constraint`, so §7.2's extension survives
    the freeze → confirmatory boundary. `scenarios.scenario_probe_reselects_`
    `the_operating_point` drives the whole branch to `GATE_5_FREEZE`.

12. **New, and OPEN as a researcher decision only — R7.** §12.6 certifies
    coverage and freezes the vocabulary at `iota_a_prescreen`; references are
    matched at Gate 2's `iota_a`, which moved by 0.015 to 0.092 on the four v5
    replications. No decisive condition changes under that drift on any of the
    four, so this is not a blocker. **Updated by V6-E04:** Gate 3A no longer
    records `coverage_at_measured_iota_a`; it records
    `coverage_at_calibrated_iota_a`, the same criterion evaluated on the
    calibration basis where $\iota(R)$, the coordinate, the vacuity and
    $\iota_A$ all come from one set of cases — and a lost decisive condition
    there is a §13.15 design-time failure under §34 D6. What remains open as
    R7 is the narrower question: whether §12.6 should *certify* over an
    interval of $\iota_A$ at the screen, rather than at a point.

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

---

## 10. Identification audit (added 2026-08-25)

**Question asked.** Can v6, as implemented, deliver a credible prospective test
of the central question — *does the identity of the companion instruction
change compliance with the focal instruction beyond the generic difficulty of
satisfying two instructions?* — with the matched-companion counterfactual,
reference support **and** composed headroom surviving simultaneously on the
same replication, before confirmatory generation?

**Verdict: READY WITH CONDITIONS.** Every mechanically closable route to
another avoidable `NOT_IDENTIFIED` is closed; what remains is researcher
judgement, listed in §5 and §6.

### 10.1 The causal comparison, checked rather than asserted

$\Delta_R = \overline{\text{compliance}}(B \mid B{+}R_j) - \text{compliance}(B
\mid A{+}B)$ isolates companion *identity* only if the two composed cells match
on everything else. In v6 they do, and none of it is new:

| condition | where | status |
|---|---|---|
| instruction count | both cells are load 2 by construction (`design.cells`) | unchanged |
| position | both orders measured; `CONFIGURATIONS`, `ORDER_CONTRASTS` | unchanged |
| difficulty | §13.8's caliper on $\iota$ against $\iota_A$ | unchanged |
| structural class / tier / feature group | §13.8, §13.15's 3 groups, ≥2 Tier-1 | unchanged |
| non-vacuity under B | §13.6's $\kappa(R\mid B)$ | **repaired** — read at the operating point |
| interaction-blindness | §13.11's closed schema, §30 | unchanged, and strengthened |

`revision.V9` compares the **twelve** modules that carry the estimand layer —
`analysis/{estimators,observations,intervals,bootstrap,masking}`,
`design/cells`, `stages/{selection,support,stability,interaction,`
`calibration_table}`, `protocol/identification` — against v5's and requires
them byte-identical modulo the namespace token. They are. Every v6 repair is
upstream of estimation.

### 10.2 What the audit found, and what was done

**V6-E03, in four parts, all repaired.** See `CHANGES_SCIENTIFIC.md`. In
short: the probe's re-selection branch could not execute (Gate 2 held
$\kappa(R\mid B)$ at its own $m^\*$ only); the probe could move $B$ to a
severity §12.4 or D17 would have refused; the freeze bound $B$ at the pre-probe
severity that confirmatory generation then renders; and $B$ could not be
rebuilt at §7.2's extension. The first is the important one — it made v6's
whole answer to v5's Gate-4 failure unreachable, and no test had driven it.

**R7, recorded not closed.** §12.6 certifies coverage at `iota_a_prescreen` and
references are matched at Gate 2's `iota_a`; measured drift on the four v5
replications is 0.015–0.092 and flips no decisive condition on any of them.
Gate 3A records the recomputation; §5 R7 states the options.

### 10.3 The two conditions, and where each is established

| | established at | before | on the same replication? |
|---|---|---|---|
| **reference support, with margin** | `GATE_3C_IDENTIFICATION` — §13.15: ≥8 structurally eligible Tier-1/2 families entering calibration, ≥5 passing the full V(R) on both splits, 3 used and **2 frozen unused** | Gate 4, the pre-freeze audit and the freeze | yes — sequential gates on one tree |
| **composed headroom, while the operating point can still move** | `GATE_2_75_COMPOSED_PROBE` — §13.14's band unchanged, with a margin $\delta$ inside it | reference calibration, so $m^\*$ can still move | yes |

The margin — 6 straddling groups at the screen against 5 qualifying families
after calibration, and 5 qualifying against 3 used — is the registered supply
cushion and no part of it was moved. The ordering guarantees simultaneity: a
replication reaching `GATE_5_FREEZE` has passed both, on its own tree.

### 10.4 Minimum additional pre-freeze checks

Everything below is **already on the mandatory path** unless marked otherwise.

| check | evidence required | data? | decides |
|---|---|---|---|
| §12.6 C1–C6 after the expansion | pre-screen table | existing | design-time `REFERENCE_SUPPORT_NOT_IDENTIFIED` |
| §12.4 + D17 **at every admissible severity** | Gate 2's own curves | existing, no new rows | which severities the probe may move to |
| §13.6 $\kappa(R\mid B)$ at the operating point | Gate 2's B-solo cells at each admissible severity | existing, no new rows | which candidates qualify |
| §13.15's support with 2 frozen backups | Gate 3A/3B | existing | D6, and the admitted arm set |
| P3.2 composed margin at $m^\*$ | probe rows | **new rows** — 11 cells × the probe split × $M_{\rm cal}$ | $m^\*$ stands, moves once, or `COMPOSED_HEADROOM_UNREACHABLE` |
| §13.14 headroom on the *selected* references | 24 reserved composed topics | existing plan | `COMPOSED_HEADROOM_FAILURE` |
| §12.6 re-read on the **calibration** basis at the measured $\iota_A$ | Gate 3A | existing, no new rows | a lost decisive condition is a §13.15 design-time failure under D6 — see §11 |

**One pilot is required and it is not started:** the R1/D19 measurement — 32
Tier-1 reserve rungs × 24 pre-screen topics × 1 draw = **768 rows per
replication, 3,072 total** — which decides whether the repaired expansion lands
inside $p_{\rm solo}\in[0.10,0.90]$ and what span it buys. It cannot be
answered from closed v5 data. Nothing has been generated.

### 10.5 Remaining routes to an avoidable `NOT_IDENTIFIED`

| route | disposition |
|---|---|
| expansion cannot reach the reserve C4 needs | **closed** — V6-E01 |
| rungs the expansion measures are invisible to C4 | **closed** — V6-E02 |
| the operating point moves and the pool does not follow | **closed** — V6-E03 |
| the probe moves $B$ to a severity Gate 2 would refuse | **closed** — `focal_admissible` |
| the freeze runs the design at the rejected severity | **closed** — V6-E03 |
| coverage certified at a drifting $\iota_A$ | **closed** — V6-E04: the criterion is re-evaluated on the basis selection works on, and it gates. R7's *interval* question stands and is separate |
| $\delta$ too small to absorb the probe-to-Gate-4 transfer | **open — R5/D23**, and §4 shows the needed margin is above the examined range |
| Gate 4 fails on a **companion** slot | **open and stated** — `PROBE_SCOPE_LIMITS`; the probe protects the B slot only |
| the reserve exists but does not qualify | **open — R1/D19**; the pilot is now a §13.15 feasibility measurement, not a solo-band check (§11) |
| development measures a proxy for the registered criterion | **closed** — V6-E04: one implementation, pinned to the four signed v5 records |
| the operating point moves and support is discovered two stages later | **closed** — V6-E04: §13.15's five-family minimum filters the search order, free |


---

## 11. Controlled reuse across stages (added 2026-08-25)

**The question this section answers.** Which stages already score the same
model, constraints, topics and draws — and what therefore does *not* need a
fresh sample. The audit changed the design: a full-slot composed headroom stage
was drafted and **not built**, because it would have been a second sample of
what Gate 4 already measures, on a *different* topic set, and would therefore
have carried the very transfer error (§4.a) it existed to remove.

### 11.1 What each stage scores

| stage | topics | draws | cells | scores absent instances? |
|---|---:|---:|---|---|
| `REGIME_SCREEN` (§12.2) | 24 pre-screen | 1 | solo, every registered rung + A + B | — |
| `GATE_0_APPARATUS` (§19) | 12 pre-screen | `PILOT_DRAWS` | the **full** design, composed included | fixture instruments; §19 declares them non-evidence |
| `GATE_2` pass 1 | 192 calibration | `M_CAL` | unconstrained, A-grid solo, B-grid solo | **yes** — every carried candidate, on every cell |
| `GATE_2` pass 2 | 192 calibration | `M_CAL` | one solo cell per carried candidate | **yes** — every other candidate, **and B at m\*** |
| `GATE_2_5` | — | — | none: it generates nothing | — |
| `GATE_2_75` | §34 D20's split | `M_CAL` | unconstrained, B solo, stand-in solo, B×stand-in both orders | — |
| `GATE_3A/3B/3C` | — | — | none: pure over Gate 2 and Gate 2.5 | — |
| `GATE_4` (§13.14) | 24 reserved composed | `M_CAL` | the full design of the admitted arms | — |

### 11.2 What is now shared rather than re-measured

| quantity | measured at | reused by | was it duplicated before? |
|---|---|---|---|
| $\iota(R)$, solo, chance, vacuity per candidate | Gate 2, 192×`M_CAL` | §12.6's calibrated re-reading, §13.7, §13.8–§13.12, §13.15 | the criterion was re-read on the *pre-screen* table against a *calibration* $\iota_A$ — two samples |
| $\kappa(R\mid B)$ at every admissible severity | Gate 2's B-solo cells | Gate 2.5, Gate 3A | already free (V6-E03) |
| the §13.1 qualified pool per severity | Gate 2.5 | the search order, Gate 3A, Gate 3C, the freeze | already free (V6-E03) |
| §13.15's five-family minimum per severity | Gate 2.5 | the probe's search order | it was not computed at all; the search would otherwise re-bootstrap §13.7 at 10,000 resamples per candidate for a verdict already signed |
| the unconstrained cell and `solo:B` | Gate 2, at every focal severity | the probe, **when the case is identical** | yes — 2 of 11 probe cells, re-drawn per probed severity |
| each candidate's pre-screen solo and chance | the screen | joined onto §13.11's table | the columns existed and **nothing ever filled them** |
| B at m\* while R is instructed | Gate 2 pass 2, as an absent instance | recorded; read by nothing | never extracted |
| each bound instrument's solo compliance | Gate 2 | Gate 4's `split_transfer`, paired by instrument | §4.a built this by hand from the closed run |

### 11.3 What genuinely still needs new data

**Load-2 compliance on the real instruments, and nothing else.** Every
pre-composition quantity §13 reads is available from cells that already exist;
no stage before Gate 4 puts two admissible constraints in one prompt. Gate 0
does render the full composed design, but on **fixture** instruments that §19
declares can never be calibration evidence, so it is not a substitute.

Two consequences, both stated rather than engineered around:

1. **The stand-in probe is the only pre-Gate-4 composed measurement**, and a
   stand-in is not the eventual reference. That limit is `PROBE_SCOPE_LIMITS`
   and it is unchanged.
2. **The pilot that decides R1/D19 needs rows.** Whether a Tier-1 family the
   researcher *adds* passes the full V(R) on these models is not in the closed
   data — an unauthored instrument has never been measured. What changed is
   what the pilot must evaluate: the §13.15 criterion with margin, through
   `stages/feasibility`, not "does the rung land in the solo band".

### 11.4 The one number this produced that changes what the pilot is for

`reference_feasibility.json`, over the four signed v5 replications:

| replication | §13.15 met | margin: eligible T1/2 | qualified families | Tier-1 core |
|---|---|---:|---:|---:|
| `gemma-3n-e2b-it` | no | +3 | +7 | **0** |
| `gemma-3n-e4b-it` | no | +3 | +7 | **+1** |
| `qwen3-4b` | no | +3 | +6 | **0** |
| `qwen3-4b-instruct-2507` | **yes** | +3 | +6 | **+1** |

The binding requirement is `min_tier1_core` on **4 of 4**, never the family
count. A library extension that adds families without adding **Tier-1
structural** capacity moves the requirement that was not binding — and R1's
reserve extension is a Tier-1 extension, which is the reading this supports.

*The frozen-backup count is deliberately not a margin:* `freeze_backups`
returns `spare[:2]`, so its length equals the requirement whenever the
requirement is met, and reporting it would put a zero in every row.

### 11.5 What the reuse costs and saves, in rows

Per replication, at §34 D20's `calibration_pooled` (192 topics) and
`M_CAL = 4`, with D24's three stand-ins:

| | cells | rows per probed severity |
|---|---:|---:|
| probe as drafted | 11 | 8,448 |
| probe with Gate 2's two cells read, not re-drawn | 9 | 6,912 |
| **saved** | 2 | **1,536 (18.2%)** |

The saving applies **only** when the probe's topic identifiers and draw count
are Gate 2's; `shared_cell_verdict` refuses otherwise and records why, so
closing D20 at `reserved_composed` simply returns the probe to 11 cells.

On the synthetic harness eight severities are §12.3-eligible and six are
admissible, so the probe's worst case is 6 × 8,448 = **50,688** rows as
drafted and 6 × 6,912 = **41,472** with the reuse. Each severity the
five-family filter removes from the order saves a further **6,912**, and the
common case — m\* passes at the first attempt — is one severity either way.

**Against this, one thing got more expensive and it should be said.** Before
V6-E03 the re-selection branch could not execute at all, so in practice the
probe always measured exactly one severity. Repairing it made the registered
P3 procedure reachable, and a reachable procedure that may measure six
severities costs more than a broken one that could measure one. The filter and
the reuse pull that back; they do not make it free.

### 11.6 The Gate-4 exposure that is *not* new data

Gate 4 evaluates **96** cell × slot entries over 56 cell types. **15** of them
are solo cells, and a solo cell measures a quantity Gate 2 already measured for
that instrument — on 192 calibration topics rather than 24 composed ones. That
is not a duplication that can be removed, because §13.14's verdict is
deliberately taken on the reserved set; but it is a duplication that can be
*reported*, and `GATE_4.split_transfer` now reports it paired by instrument.

This matters because one of v5's two terminations was a **companion slot in a
solo cell** — that is this movement and not a composition effect at all. §4.a
measured it by hand across the closed run at mean absolute 0.064 and maximum
0.189. Recording it per replication is what stops the next protocol version
having to rebuild that table from raw rows.

---

## 12. The design pass of 2026-08-25 (added after §11)

§§3–7 were written before the precision of Gate 4 had been measured and before
the probe's scope had been derived from Gate 4's own cell set. Both are now
done, and what they returned changes four of §5's six decisions from open
questions into derivations. **Nothing below closes a decision**: closing one is
a researcher act on `reports/dci1v6/researcher_decisions.json`, which does not
exist and which no code may create. What changed is that four of them now have
an answer that follows from the registered protocol and from measurement, and
two of those answers are the opposite of what this memo recommended.

Everything numeric here is computed by
[`tools/v6_precision_design.py`](../../tools/v6_precision_design.py) into
[`precision_design.json`](precision_design.json), from signed v5 stage records
and the scored rows they were computed from. The tool refuses to report
anything unless its own baseline reproduces the two signed Gate-4 headroom
tables and the two signed terminal reports exactly — 21 checks, all agreeing,
the same 21 §0 already relies on.

### 12.1 The split transfer is not a bias. It is Gate 4's own sampling error

§4.a asked $\delta$ to absorb a calibration→composed movement whose realised
magnitude reached 0.189 and reported that it "separates neither" the sampling
half from the real one. Separated:

| quantity | value |
|---|---:|
| observed variance of the 13 transfers | 0.004297 |
| variance the two sample sizes imply | 0.005153 |
| residual | **−0.000856** |

The observed spread is *smaller* than sampling alone predicts. There is no
detectable systematic component, and §6.2 says why there should not be:
`dci1v4.topics.split.cut_area` cuts the pre-screen, calibration_a, composed,
confirmatory and sequestered sets out of **one seeded per-area shuffle**, so
they are exchangeable draws from one stratified population. A constant chosen
to cover 0.189 would have been a design constant absorbing sampling noise.

**One component is not exchangeable, and it is measurable.** §34 D3's
`calibration_b` is *newly authored*, not part of §6.2's cut, and it supplies 96
of the 192 topics a pooled probe measures on. Paired by instrument across
§13.7's two sub-splits on the same closed record:

| quantity | value |
|---|---:|
| mean $\iota_a - \iota_b$ | +0.011 |
| mean $\lvert\iota_a - \iota_b\rvert$ | 0.046 |
| observed variance | 0.003369 |
| sampling variance | 0.002561 |
| residual sd | **0.0284** |
| carried by a pooled probe ($\times \tfrac12$) | **0.0142** |

That 0.0142 is the whole non-sampling error budget, it is what
`composed_probe.RESIDUAL_SD` carries, and §34 D20's
`calibration_with_measured_transfer` branch is the estimator that puts the
same quantity on the record per entry, in the stage, at the moment the margin
is applied — `GATE_2_75_COMPOSED_PROBE.measured_split_transfer`, which **gates
nothing** because a rule that re-tuned the margin from the transfer it was
measuring would be fitting a design constant to the replication it is about to
judge. R2's recommendation (c) stands, with a reason it did not have: the
sub-split contrast is not a diagnostic, it is a measurement of the only term
the design cannot make vanish.

### 12.2 How precise one §13.14 entry is, and how often Gate 4 fires on a replication that is in band

73 realised cell × slot entries across the four replications, per-topic:

| quantity | value |
|---|---:|
| median SE of one entry at 24 topics | 0.0607 |
| median SE in the upper region ($p \ge 0.75$, 22 entries) | 0.0450 |
| median topic-level ICC | **0.350** |

The ICC is the number that decides which lever exists: at $\rho = 0.35$ a
fourth draw within a topic buys very little and only topics buy precision,
which is why every option below moves `N_COMPOSED` and none moves `M_CAL`.

A **joint** topic bootstrap — joint because one replication's entries share one
topic set, so treating them as independent understates the family — over each
replication's own realised entries, 10,000 resamples at §13.7's registered
count:

| replication | entries | outside the band as measured | P(some entry outside) at 24 | at 48 | at 96 |
|---|---:|---:|---:|---:|---:|
| `gemma-3n-e2b-it` | 11 | 0 | **0.121** | 0.044 | 0.007 |
| `qwen3-4b` | 6 | 0 | **0.190** | 0.074 | 0.017 |
| `gemma-3n-e4b-it` | 11 | 2 | 0.992 | — | — |
| `qwen3-4b-instruct-2507` | 45 | 2 | 1.000 | — | — |

The first two rows are the finding: **a replication whose entries are all
inside §13.14's band still fires roughly one time in six to eight**, on a
re-draw of the composed topic set. This is what §4.c called "the largest single
lever on v6 survival" and it is now a number. The full five-arm set audits 95
entries; no replication ran it, and that rate is not measurable from v5.

### 12.3 R3/D21: the enlargement branch is not executable in this repository

R3 recommended enlarging the composed set 24 → 48, taking the difference from
the sequestered eighth. **The sequestered eighth was never materialised here.**
`load_bank` carries zero sequestered questions; `dci1v4.topics.sequestered`
holds opaque identities and content hashes only; the texts are retained by the
researcher outside the repository; and `assert_no_materialisation` refuses any
released question colliding with a sequestered hash on every load. Enlarging is
therefore not a change to a constant — it is an act of authoring topics, a
governed §6.2 change, and it spends the reserve §6.2 keeps for a future
uncontaminated rerun.

That leaves `as_registered` and `interval_criterion`, and the second changes
what §13.14 *means* and breaks comparability with v5's Gate 4 — which R3 itself
says should not be bundled with this work. **The derivation is
`as_registered`,** and the precision reasoning moves to where it can go without
touching a reviewed definition: Gate 2.75's projection, which is new code with
no v5 counterpart to be comparable with, and which refuses an operating point
whose predicted Gate-4 entries sit within an interval's reach of the band. v6
does not make Gate 4 more precise. It makes Gate 4's verdict less marginal.

### 12.4 R5/D23: $\delta$ was the wrong instrument, and what replaces it

§4 examined $\{0.025, 0.05, 0.075\}$ and concluded the needed margin lay above
the range. It did, for a quantity that should never have been a constant. The
rule is now per entry and by what the entry is evidence for:

> **Determinate entries** — `solo:A`, `solo:B` and both orders of `pair:A+B`,
> whose constituents are the real registered instruments A at $n^*$ and B at
> $m^*$ — pass iff their **projected Gate-4 interval** lies inside §13.14's
> registered band:
> $\hat p \pm z\sqrt{\hat s^2/N_{\text{composed}} + \hat s^2/n_{\text{probe}} + \sigma_r^2}$,
> with $\hat s^2$ that entry's own between-topic variance measured in the same
> stage, $z$ at §13.4's registered 95%, and $\sigma_r = 0.0142$ from §12.1.
> The device and the level are §13.4's own — contract the band, apply it to
> the *interval* so an imprecisely measured value cannot sit on the boundary —
> and using a different convention for the same device in the same protocol
> would have been an unregistered choice.
>
> **Stand-in-dependent entries** — every entry of a cell containing a stand-in,
> including the A and B slots of those cells, because B's compliance beside a
> stand-in is not B's compliance beside the reference — pass iff the measured
> value lies inside §13.14's registered band, **with no margin at all**. A
> failure is a real composed cell of real instruments leaving the band. A pass
> certifies nothing about a reference, and the record says so rather than
> implying otherwise.

The family-wise half-width over the six determinate entries is computed and
recorded beside every verdict, so the more conservative Bonferroni reading is
on the artifact rather than in an argument. It is deliberately conservative:
the six entries share one topic set, so their errors are correlated.

**What is left of D23** is the allowance beyond those two measured terms, and
its derived value is **0.0**. `precision_design.json` also carries the 95%
upper bound on a residual thirteen observations could have missed
(sd ≤ 0.0687), because a derivation that reported only a point estimate of zero
would be reckless.

**What the rule does to the operating point, on the closed v5 curves.** Applied
to each replication's own measured solo-B curve and its own per-severity
between-topic variance — a determinate entry, so this is the rule's own test:

| replication | v5's $m^*$ | solo B | half-width | slack to 0.95 | passes? | severities that do pass |
|---|---:|---:|---:|---:|---|---|
| `gemma-3n-e2b-it` | 10 | 0.8060 | 0.1193 | **+0.025** | yes | 7, 8, 9, 10 |
| `gemma-3n-e4b-it` | 10 | 0.8672 | 0.1096 | **−0.027** | **no** | 7, 8, 9 |
| `qwen3-4b` | 12 | 0.7695 | 0.1407 | **+0.040** | yes | 9, 10, 11, 12 |
| `qwen3-4b-instruct-2507` | 11 | 0.7734 | 0.1412 | **+0.035** | yes | 8, 9, 10, 11 |

Every replication retains admissible operating points, and the one the rule
refuses at $m^*$ is `gemma-3n-e4b-it` — the replication that in fact terminated
at Gate 4. Note also that the half-width is *smaller* where compliance is
higher, because the between-topic variance is: the rule is not a constant band
and does not behave like one. That is a property of the rule computed on
development evidence and it is **not** a re-verdict, not a claim the rule would
have saved anything, and not evidence that it generalises: §30's precedent
applies and v6 tests it prospectively. `precision_design.json`'s
`operating_point_feasibility` carries the whole table with its own refusal to
report unless the baseline reproduces the signed records.

### 12.5 R6/D24: the stand-ins exist, and S3's group requirement was dropped for a reason

Three `probe_only` families are authored — `PS1` (`capital_word`, exact count),
`PS2` (`semicolon`, count lower bound), `PS3` (`y_final`, rate lower bound).
S3 asked additionally that each declare a `feature_group` used by no selectable
family. **That requirement is dropped and must not be reinstated.** All
twenty-two of §7.6's statistics are carried, so a new group needs a new
statistic; `FEATURE_GROUP_IDS` is a *sorted* tuple and `selection.group_key`
reads a group's index in it as a reference-selection tie-break; so adding a
group reorders the tie-break for every selectable family sorting after it. A
probe-only instrument that changed which reference gets selected is precisely
the failure `probe_only` exists to prevent. Reusing registered statistics under
forms no selectable family carries gives distinct *kinds* — which is what S2
actually needs — at no cost to the group index, the verifier population or
§12.6's counts.

`assert_library_sizes` now asserts ten numbers, three of which exist to show
that nothing moved where it matters: `selectable_families` 37,
`selectable_round_0_severities` 326, `selectable_declared_severities` 632 —
v5's values exactly.

### 12.6 R1/D19 and R4/D22

Unchanged in substance and now stated as the direction v6 takes: `D19` at
`reachability_only`, with library extension available only as a later amendment
if the correctly functioning mechanism itself proves insufficient, and the
3,072-row development measurement of §7 step 3 **not run**; `D22` at
`per_replication`, with `D25`'s single-survivor sentence written out in
`run.lifecycle.SINGLE_SURVIVOR_STATEMENTS` so that closing D25 selects a
registered sentence instead of licensing one to be composed after the survivor
count is known.

### 12.7 The compute this design costs

Every figure is computed by
[`tools/v6_compute_budget.py`](../../tools/v6_compute_budget.py) into
[`development/d1_compute_budget.json`](development/d1_compute_budget.json) from
the code's own constants and the arm-derived cell set; none is transcribed. A
*generation* is one model response — one prompt at one draw.

**Gate 2.75, the new term**, per replication:

| term | rows |
|---|---:|
| stand-in solo ladder — 24 rungs × 24 pre-screen topics × 1 draw, **once** | 576 |
| one probed severity — 15 generated cells × 192 topics × 4 draws | 11,520 |
| **modal cost, $m^*$ passes** | **12,096** |
| ceiling, all 10 admissible severities probed | 115,776 |
| *not* drawn: cells read off the Gate-2 record, per severity | 3 cells / 2,304 rows |

The ceiling is reached only when every admissible severity is probed; P3.3
stops at the first pass, and Gate 2.5 has already removed severities that
cannot meet §13.15's five-family minimum.

**The whole replication**, at §34 D1's registered 56-cell option:

| term | generations |
|---|---:|
| §12.2 ladder screen — 342 rungs × 24 topics × 1 draw | 8,208 |
| §12.3 focal grids — 192 topics × 4 draws | 13,824 |
| §12.7 candidate calibration — both splits | 86,016 |
| §19 pilot — 56 cells × 12 topics × 4 draws | 2,688 |
| *calibration subtotal* | *110,736* |
| **Gate 2.75 (new), modal** | **12,096** |
| Gate 4 composed headroom — 56 cells × 24 topics × 4 draws | 5,376 |
| §8.3 greedy sensitivity | 5,376 |
| confirmatory — 56 cells × 384 blocks × 8 draws | 172,032 |
| **per replication, modal** | **305,616** |
| four replications | **1,222,464** |

Two terms are conditional and are named rather than folded into a figure a
replication is expected to spend, because both stop early by rule: §12.6's
expansion ceiling is 4,224 screen rows plus 36,864 candidate-calibration rows,
and Gate 2.75's is 115,776. At both ceilings a replication costs 409,296 and
four cost 1,637,184 — an upper bound nothing is expected to reach, and the
honest one to plan against.

**What the probe costs, relative to what it protects.** 12,096 generations is
4.0% of a replication's modal cost and 7.0% of its confirmatory run. Its
purpose is to refuse an operating point *before* the confirmatory 172,032 is
spent, on a replication that would otherwise terminate at Gate 4 with every
earlier gate passed — which is exactly what happened to two of v5's four.

### 12.8 What is *not* resolved by any of this

The researcher decision record does not exist and no code may create it. Until
it does, **all twenty-six** of D0–D25 are `UNRESOLVED` at import — including
D0–D18, which v5's researcher closed on v5's record and which only the
researcher can carry into v6 — and `assert_transition_legal` refuses stage 1.
Everything in §§12.1–12.7 is a derivation available *to* that act; none of it is
that act.

### 12.9 The two governed documents now exist as **drafts**, and are refused

`user-notes/DCI1_preregistration_v6.md` and
[`reference_design_spec.json`](reference_design_spec.json) exist. Both declare
`DRAFT_NOT_ADOPTED`, and `manifest.assert_documents_adopted` adds a
`DRAFT_DOCUMENT` blocker while either does — because `document_hashes` only
refuses a *missing* document, and a complete draft is exactly the thing that
could be mistaken for a registration by being present. Silence reads as a draft
too: a document with no declared status is refused, because the safe reading of
silence here is the one that refuses.

Two things about them are worth knowing before reading either:

- the preregistration **incorporates v5's text by content hash**
  (`ebb27c15…`) and then states every amendment in full, rather than copying
  3,794 lines that could drift from the text they claim to reproduce;
- the reference-design spec is **generated from the registered code** by
  [`tools/v6_reference_design_spec.py`](../../tools/v6_reference_design_spec.py),
  so a spec that disagrees with the implementation is not expressible. v5's
  equivalent was written by hand.

[`development/researcher_decisions_PROPOSAL.json`](development/researcher_decisions_PROPOSAL.json)
carries the seven v6 decisions in the shape the record takes, with each
derivation and its evidence. **It is not the record**, it is not at
`RECORD_RELPATH`, `protocol/decisions` does not read it, and it deliberately
omits D0–D18: those are v5's, closed on v5's own record, and carrying a closure
into a new registration is a researcher act with its own evidence rather than a
transcription.

---

## 13. The red-team pass of 2026-08-26 (added after §12)

§12 recorded a design pass. This records an **audit of the decision set that
pass produced**, and two of its findings were blocking. Nothing in §§1–12 is
deleted; where a conclusion is superseded it is marked here.

### 13.1 The register proposed three branches v5's researcher rejected

`protocol/decisions` carried v5's **pre-adoption draft** proposals for D16,
D17 and D18. `reports/dci1v5/researcher_decisions.json` records what was
actually closed:

| id | register said (until 2026-08-26) | v5 closed at | which is |
|---|---|---|---|
| D16 | `a_survivors` | `complete_population` | ~35,000 more rows per replication |
| D17 | `no_floor` | `floor` (κ_B(m\*) ≤ 0.50) | a registered threshold |
| D18 | `not_a_precondition` | `precondition` | L3c requires the near-form arm |

In all three the register proposed the **weaker** branch, while
`user-notes/DCI1_preregistration_v6.md` §1 asserted the stronger one was
carried and `design.budget.calibration_burden` already costed
`complete_population`. D17 compounds it: the floor is one of the three
conditions `focal_admissible` conjoins, so `no_floor` **enlarges** the set of
severities `GATE_2_75` may re-select m\* among. A researcher accepting the
register's own proposals would have relaxed two substantive thresholds and
widened probe survival, by inconsistency rather than intent.

**Fixed.** The register now quotes v5's closures with v5's evidence and says
in each entry what it used to say. Carrying them into v6 is still a researcher
act with its own evidence.

### 13.2 §34 D23 did not mean what four documents said it meant

`entry_verdict` passed D23's value straight into `projected_halfwidth` as
`residual_sd`. So D23 **was** the quadrature term, while the preregistration
(A5), the decision register, `researcher_decisions_PROPOSAL.json` and
`reference_design_spec.json`'s `verdict_rule` all described it as an allowance
*beyond* a separately-carried `RESIDUAL_SD = 0.0142`. The proposed `D23 = 0.0`
would therefore have removed the measured non-sampling term from every
determinate verdict. `RESIDUAL_SD` reached production only as a default
argument the verdict path always overrode, and `margin_band()` had no caller
at all. The units differ too: an sd in a quadrature and a linear band
contraction are not interchangeable, and 0.05 buys +0.098 of half-width under
one reading and 0.05 of band under the other.

**Fixed by splitting it.** §34 D23 is now the **reading** — `projection_sd` or
`beyond_the_measured_sd`, both executable — and §34 D26 the **magnitude**, a
number in [0.0, 0.45) that `decisions.close` range-checks at closure rather
than at the stage five steps later. `severity_verdict`, `entry_verdict` and
`probe_disposition` take the band and the projection sd as separate arguments,
so neither can substitute for the other again.

### 13.3 §12.4's derivation of δ = 0 does not survive, and no value replaces it

§12.4 concluded 0.0 because the transfer's observed variance (0.00430) is below
the sampling variance the sample sizes imply (0.00515). **That is a statement
about dispersion.** What an allowance protects against is a *common shift of
one replication's entries*, and `precision_design.json` names that quantity
itself — *"a real set effect would appear as a common per-model shift and not
as instrument noise"* — and then does not estimate it.

It is **+0.045** over the thirteen realised movements. The four per-model means
are −0.013, +0.076, +0.029, +0.067; taking them as the unit gives 0.0397, SE
0.0204, and a 95% interval on t₃ of about **(−0.025, +0.104)**. `RESIDUAL_SD =
0.0142` sits near the bottom of it. The artifact's own `residual_sd_upper_95`
is **0.0687**, 4.8× the measured value.

And `operating_point_feasibility` was computed at `residual_used = 0.0` and at
no other value — so the evidence that every replication retains an operating
point existed only at the value it was being used to justify.

`tools/v6_residual_sensitivity.py` sweeps the grid instead, writing
`residual_sensitivity.json`.

> **The table below is SUPERSEDED.** It was computed under the focal-only
> *reselection* rule of §13.4, which the researcher replaced on 2026-08-26
> with a **frozen m\***. Its columns "admissible severities" and "m\*
> survives" describe a search that no longer exists. The current table, on the
> same grid and the same closed v5 measurements, is **§14.2**. This one is
> kept because it is what was in front of the researcher when §34 D26 was
> being framed.

| reading | magnitude | evaluated band | half-width at median s² | admissible severities (of 8) | m\* survives |
|---|---:|---|---:|---|---|
| `projection_sd` | 0.0 | [0.05, 0.95] | 0.1138 | 4 / 3 / 4 / 4 | 3 of 4 |
| `projection_sd` | 0.0142 | [0.05, 0.95] | 0.1172 | 4 / 3 / 4 / 4 | 3 of 4 |
| `projection_sd` | 0.0687 | [0.05, 0.95] | 0.1763 | 3 / 3 / 2 / 3 | 0 of 4 |
| `beyond_the_measured_sd` | 0.0 | [0.05, 0.95] | 0.1172 | 4 / 3 / 4 / 4 | 3 of 4 |
| `beyond_the_measured_sd` | 0.0142 | [0.0642, 0.9358] | 0.1172 | 4 / 3 / 4 / 4 | 3 of 4 |
| `beyond_the_measured_sd` | 0.0687 | [0.1187, 0.8813] | 0.1172 | 3 / 3 / 2 / 3 | 0 of 4 |

Two things follow. **Feasibility does not discriminate**: every replication
retains an admissible operating point at every policy, which answers the
circularity §12.4 left open. **The readings barely discriminate either** — at a
given magnitude they select the same severities — so the live question is the
magnitude, and specifically whether to buy 0.0687's conservatism, which would
make all four replications re-select rather than three of four keeping their
v5 m\*. Scope limit on the table: `solo:B` is the only one of the six
determinate entries v5 measured on the calibration split, so these are a
**lower** bound on how often the rule bites.

### 13.4 Focal-only reselection (researcher decision, 2026-08-26)

> **SUPERSEDED the same day by §14.1.** The reselection half of this decision
> was withdrawn: m\* is now frozen at Gate 2 and the probe may terminate but
> never move it. The determinate-only half stands unchanged.

The probe could move m\* — and terminate a replication — on entries containing
`PS1`–`PS3`, instruments that are non-selectable by construction and that A10
gives a predicate form no selectable family carries. The researcher's decision:
**only the six determinate entries decide.** Registered as preregistration A13,
including the declaration that it is a *loosening* of the rule it replaces, and
including what the stand-in rows now buy — 1,536 rows per probed severity decide
m\*, 9,984 are a structural-risk record that gates nothing.

### 13.5 Decisions that could not affect execution

Thirteen entries offered alternatives the implementation had no branch for, so
closing at one would have registered a study the code cannot run — silently,
because nothing read the value. D2, D5, D7–D15, D19 and D21 are now
**acceptances**; each withdrawn alternative moves to
`unimplemented_alternatives`, which `as_dict` carries into the registration
payload, and `close()` refuses it by name. D20 lost `calibration_pooled` for
the same reason in a sharper form: it and `calibration_with_measured_transfer`
mapped to the same 192 pooled topics and produced identical records.

Two more of the same kind, fixed rather than retired:

- **D0's `do_not_adopt` refused nothing.** No code read D0, so the value
  meaning "this study does not run" signed a manifest exactly as `adopt` did.
  `signing_blockers` now raises `NOT_ADOPTED`.
- **D25 had no caller.** `study_level_statement` was invoked by no stage —
  the lifecycle is per replication and `FINAL_REPORT` writes one report per
  model, so a study-level sentence had nowhere to live. `tools/v6_closure.py`
  now writes `reports/dci1v6/closure.json`, following
  `reports/dci1v5/closure.json`'s precedent. It counts survivors from signed
  records and quotes the registered sentence; it estimates nothing.

### 13.6 Citations corrected

- §1 of the preregistration cited "§31's prohibition on post-outcome repair,
  reselection or re-expansion". v5's §31 is **Release**; the prohibition is
  §32.1 and §32.3, and v6 incorporates v5 by content hash, so the citation
  resolved to the wrong text.
- `selection.group_key` → `selection._group_order` in the preregistration and
  the proposal record.
- `budget.calibration_burden` and `analysis_run._raw_coordinate_secondary`
  both said a decision "is closed at" a value. Both are v5 sentences in v6
  modules; both decisions are `UNRESOLVED` here.
- §32.2 requires that a change adopted after a gate ran be declared as such.
  Preregistration §4 declared two fitted quantities and did not declare that
  `GATE_2_75` and `PS1`–`PS3` exist because v5's Gate 4 fired. It now does.

### 13.7 What the red team did **not** overturn

The identification firewall, the exposure-class derivation, the two-tier
verdict, `probe_only` non-selectability, the §6.2 exchangeability argument for
the *dispersion* of the transfer, D22's per-replication licensing, and A3's
recalibrated coverage read. §13.14, §13.4, C4 and every other substantive
threshold are untouched.


## 14. The adoption pass of 2026-08-26 (added after §13)

§13 audited the decision set. This records what the researcher then **decided**,
and the state the study was registered in. Nothing in §§1–13 is deleted; where a
conclusion is superseded it is marked there and restated here.

### 14.1 m\* is frozen at Gate 2. The probe may stop, not steer

The researcher withdrew the reselection half of §13.4. The rule that was
registered:

1. §12.3 selects m\* from B's solo curve at `GATE_2_FOCAL_CALIBRATION`.
2. m\* is **frozen** there.
3. `GATE_2_75_COMPOSED_PROBE` measures composed headroom **at m\* and at no
   other severity**.
4. It passes, or it terminates the replication `COMPOSED_HEADROOM_UNREACHABLE`.
   There is no third branch.
5. The six determinate entries — `solo:A`, `solo:B`, `pair:A+B`, `pair:B+A` —
   are the only ones that can fail the verdict. `PS1`–`PS3` are measured,
   judged against §13.14's registered band and recorded under
   `standin_findings`; they gate nothing and enter no selectable pool and no
   confirmatory estimator.
6. Existing Gate-2 solo measurements are reused where the case is identical,
   which `shared_cell_verdict` checks by topic identity and draw count.

**The reason, stated as identification and not as caution.** `Delta_j` and
`Delta_R` are defined *at an operating point*. A stage that could move that
point using composed outcomes would be choosing where the estimand is measured
after §12.3 had already chosen — and would give a replication with poor
composed headroom a route to a severity that reported better. Headroom may
decide **whether** the frozen design is viable. It may never decide **where**.

**What it costs, declared.** This is a **tightening**: a replication whose m\*
lacks composed headroom now stops where it previously moved and continued. v6
buys the early measurement and explicitly does not buy the rescue.

**Enforced in three places rather than described in one.**
`composed_probe.probe_disposition` refuses a probe table carrying any severity
but m\*; `composed_probe.assert_m_star_unmoved` runs on the producing path
before the record is written; `gates_run.effective_m_star` checks the written
record against Gate 2's on every downstream read. Two synthetic scenarios drive
both outcomes end to end, and `test_operating_point_invariants` pins the AST:
the only expression `probe_disposition` ever writes into `m_star_out` is its
own `m_star` argument.

Gate 2's `operating_point_search_order`, its κ(R|B) column at every admissible
severity, and Gate 2.5's per-severity qualification are **retained and
re-purposed**. Nothing tries them in turn. The head of Gate 2.5's order is
where the two gates record their agreement about m\*, and the probe reads it
for exactly that check; the rest is a signed prospective record, costing no
rows, of where a reference set could have existed at all.

### 14.2 The residual grid, recomputed under the frozen-m\* rule

Replaces §13.3's table. Same closed v5 measurements, same six policies; the
quantity is now **whether the frozen m\* passes**, because that is what the
registered rule asks. Order: `gemma-3n-e2b-it`, `gemma-3n-e4b-it`, `qwen3-4b`,
`qwen3-4b-instruct-2507`.

| reading | magnitude | evaluated band | half-width at median s² | m\* passes | half-width at each m\* |
|---|---:|---|---:|---|---|
| `projection_sd` | 0.0 | [0.05, 0.95] | 0.1138 | Y N Y Y | 0.1193 / 0.1096 / 0.1407 / 0.1412 |
| `projection_sd` | **0.0142** | **[0.05, 0.95]** | **0.1172** | **Y N Y Y** | **0.1225 / 0.1131 / 0.1434 / 0.1439** |
| `projection_sd` | 0.0687 | [0.05, 0.95] | 0.1763 | N N N N | 0.1799 / 0.1736 / 0.1947 / 0.1951 |
| `beyond_the_measured_sd` | 0.0 | [0.05, 0.95] | 0.1172 | Y N Y Y | 0.1225 / 0.1131 / 0.1434 / 0.1439 |
| `beyond_the_measured_sd` | 0.0142 | [0.0642, 0.9358] | 0.1172 | Y N Y Y | 0.1225 / 0.1131 / 0.1434 / 0.1439 |
| `beyond_the_measured_sd` | 0.0687 | [0.1187, 0.8813] | 0.1172 | N N N N | 0.1225 / 0.1131 / 0.1434 / 0.1439 |

Three things follow, and the first is the one §13.3 could not see.

**The replication the rule stops is the one v5's Gate 4 stopped.** At every
policy the single failing m\* is `gemma-3n-e4b-it`'s — the replication v5
terminated `COMPOSED_HEADROOM_FAILURE` at Gate 4, with every earlier gate
passed. On v5's own measurements the probe finds that failure **two stages
earlier**, which is the thing `GATE_2_75` exists to do. It is
DEVELOPMENT_EVIDENCE about a v5 measurement under a v6 rule and is not a
re-verdict of v5.

**Feasibility was never the discriminator, and §13.3 read it the wrong way.**
§13.3 concluded "every replication retains an admissible operating point at
every policy", which was true of a *search* that no longer exists. Under the
frozen rule the question is per replication, and the answer separates: 0.0 and
0.0142 stop one of four, 0.0687 stops all four.

**The two readings differ only in where the number is spent.** At a given
magnitude they reach the same verdict here, because `solo:B`'s half-widths are
far from the band edges relative to the contraction. They are still different
quantities with different units, which is why §34 D23 exists.

Scope limit, unchanged: `solo:B` is the only one of the six determinate entries
v5 measured on the calibration split, so this is a **lower** bound on how often
the rule bites. Five of the six are measured for the first time when the stage
runs.

### 14.3 §34 D23 and D26, closed

**D23 = `projection_sd`.** The term three governed documents promise is carried
*is* a residual standard deviation — the estimated non-sampling difference
between the split the probe measures on and the split §13.14 audits on — and
the projection's error model is where a standard deviation belongs. §13.14's
band is left exactly as registered, which is what keeps a v6 Gate-4 record
comparable with v5's.

**D26 = 0.0142.** Not a chosen constant: the measured authored-sub-split
residual, 0.0284 paired by instrument on the signed closed-v5 records, halved
to 0.0142 by the pooling a 192-topic probe performs
(`precision_design.json`, `authored_subsplit.carried_by_a_pooled_probe.sd`).
Under `projection_sd` it enters the quadrature as itself, so the measurement is
carried exactly once and nothing is added to it. Its provenance is declared:
v5 DEVELOPMENT_EVIDENCE under §30, tested prospectively by §34 D20's measured
sub-split transfer, and v6 may not claim it generalises.

The closure was **not** made on the survival column of §14.2. 0.0 is rejected
because the derivation behind it was about dispersion, which is not what an
allowance protects against, and because it deletes a term the documents say is
carried; 0.0687 is rejected because it is an upper bound on the measurement
rather than the measurement.

### 14.4 D0–D18, carried

All nineteen are closed on v6's own record at **v5's actually adopted values,
with v5's own evidence quoted from `reports/dci1v5/researcher_decisions.json`**
and a `carried_from` block naming the record and the researcher who first took
each. §13.1's three corrected entries are carried at `complete_population`,
`floor` and `precondition`. D17's `FloorSpec` — quantity, value, semantics,
derivation — travels with it, because `construct_strength.registered_floor`
reads the record and carries no literal. §33's U2, U4 and P1 are re-resolved on
v6's record at `A2`, `E2` and `confirmed`.

### 14.5 The state the study registered in

`dci1/reports/dci1v6/researcher_decisions.json` exists and closes all
twenty-seven §34 decisions and all three blocking §33 items;
`manifest.signing_blockers()` reports nothing; both governed documents declare
`ADOPTED`. Zero v6 behavioural rows existed at the moment of registration, and
`RESEARCH_STATE.md` §4 records the manifest hash and the producing commit.

---

## 15. The apparatus-fault pass of 2026-08-26 (added after §14)

§14 closed the adoption pass and the study was committed at `0ba60e4`. What
follows is what happened when the registered study was executed for the first
time, and it is a section about the **apparatus**: no scientific rule, no
threshold, no estimand and no decision moved.

### 15.1 Three defects in the documented entry point

`python -m dci1v6.run.cli run --stage PROTOCOL_REGISTERED --model
gemma-3n-e2b-it` failed three times in a row.

| # | defect | why it was invisible |
|---|---|---|
| 1 | the CLI created no study signing key | every record is signed at write, so **no** stage could run; the integration harness creates its own key and never took this path |
| 2 | `--repo-root` never reached `run_registration`, whose default is `"."` | the harness passes an explicit root; only the real CLI defaults |
| 3 | a stage-1 readiness verdict wrote §28.3's terminal report | no v6 replication had ever been refused at stage 1 |

Defect 2 is what produced the record. Invoked from `dci1/`,
`assert_documents_adopted` looked for `user-notes/DCI1_preregistration_v6.md`
and `dci1/reports/dci1v6/reference_design_spec.json` **relative to the working
directory**, found neither, and reported both `missing`. Both exist and both
declare `ADOPTED` at `0ba60e4` — the very commit the resulting record cites.

Defect 3 turned that into a terminal outcome. `REGISTRATION_INCOMPLETE` was in
`C.TERMINAL_STATUSES`, so `run_stage` wrote `terminal_report.json` and
`assert_predecessor_passed` disabled every later stage for `gemma-3n-e2b-it`
permanently. §6.1 registers four replications; one mis-invoked command had
reduced them to three.

### 15.2 It was a hole, not an inconvenience

Two statements in the registered implementation could not both be true:

> `protocol/decisions.choice()`: *"…§18 stage 1 returns
> `REGISTRATION_INCOMPLETE` **until then**."*

> `engine/transitions.assert_predecessor_passed`: *"{model} is terminal at
> {status}; every later stage is mechanically disabled."*

"Until then" presupposes a later attempt. Every entry
`manifest.signing_blockers` can report — an open §34 decision, an unresolved
§33 question, a missing topic hash, an unapproved candidate population, an
unspecified floor, an unpinned model revision, a non-derivable design, a draft
document — names work a **researcher** has to do. If the first invocation that
finds any of it outstanding kills the replication, the whole vocabulary is
unreachable by construction: each blocker exists only to end whichever
replication discovers it.

### 15.3 Amendment A15

The researcher ruled the record an **apparatus fault**, retained the full
four-model panel, and adopted A15 as a prospective §32 amendment — after
adoption, before any behavioural row, declared under §32.2 in
`DCI1_preregistration_v6.md` §4.

**The criterion did not move.** `signing_blockers` decides readiness exactly as
it did, and a study that could not be registered still cannot be. What changed
is the kind of verdict: `run/lifecycle.ReadinessRefusal` fails closed, writes
no stage record and no terminal report, logs a `REFUSED` transition carrying
the blockers and the remedy, and leaves the replication free to attempt the
stage again. `C.READINESS_REFUSAL_STATUSES` and `C.TERMINAL_STATUSES` are
disjoint, asserted at import, and three structural refusals hold the line:
`TerminalStatus` will not carry a readiness status, `write_terminal_report`
will not write one, and `ReadinessRefusal` will not accept any gate but
`PROTOCOL_REGISTERED`. Every §28 terminal outcome — `COMPOSED_HEADROOM_FAILURE`,
`COMPOSED_HEADROOM_UNREACHABLE`, `PREFREEZE_AUDIT_FAILURE` and the rest — is as
irreversible as it was.

### 15.4 The record already written, retained

`run/registration_run.retire_apparatus_fault` is §32's retain-everything shape
applied to a *record* rather than to a manifest.
`supersede_registration` could not reach this case: it retires under
`superseded/<old manifest hash>/` and there was no manifest to name.

Six preconditions, each a refusal: the file hash must be the one named; the
signature must verify; the gate must be `PROTOCOL_REGISTERED`; the status must
be a readiness status, so no §28 terminal is retirable by this or any path; no
registration manifest may exist; and no behavioural row may exist anywhere in
the study, counted from the filesystem rather than believed. A seventh refuses
a replication that already holds any stage record.

Nothing is deleted. The signed report moves byte-identical to
`superseded/apparatus_fault/<record hash>/` in the evidence tree and in the
durable mirror — `paths.is_superseded` already excludes that path from every
current pool and the durability audit already counts it. The append-only
transition log keeps every row the failed attempt wrote, `TERMINAL` included.
The retirement record beside the report carries the retired payload verbatim,
the defect, the amendment, and the preconditions verified. And
`manifest.build_manifest` reads those records, so the retirement is **inside**
the signature of the registration that followed rather than beside it, and
`closure.json` reports it separately from the terminal statuses so a reader
cannot mistake it for a verdict about a model.

### 15.5 One correction to §14

§14 and this memo's banner were written on the morning of 2026-08-26 and say
v6 "was adopted and registered" that day, and §14.5 describes the registered
state as though registration had happened. It had not: adoption was complete
at `0ba60e4` and the registration attempt that followed failed on the three
defects above. Registration succeeded only after A15. The earlier sections are
left as written, per this memo's rule; this is the correction.

### 15.6 What A15 does not change

No threshold, estimand, criterion, population, model, reference family, arm,
seed, verifier, prompt, wording, claim ladder or headroom band. Not `m*`: A13's
freeze at Gate 2 stands, and `GATE_2_75_COMPOSED_PROBE` still may terminate a
replication and still may never move the operating point. §34 D23 remains
`projection_sd` and D26 remains `0.0142`. §6.1's four replications are four.

Zero v6 behavioural rows existed when the fault occurred, when A15 was
adopted, and when the corrected registration was signed. The incident record
is [`incidents/2026-08-26_stage1_apparatus_fault.md`](incidents/2026-08-26_stage1_apparatus_fault.md).

---

## 16. The coverage-criterion pass of 2026-08-26 (added after §15)

§15 closed the apparatus-fault pass and v6 was registered. This section is the
first one written **after a v6 measurement existed**, and it says so at the
top because everything in it was decided with the offending numbers already on
the evidence tree.

### 16.1 What happened

`PROTOCOL_REGISTERED`, `QUALIFIED` and `GATE_0_APPARATUS` passed on all four
replications — 2,688 real rows each, both discrete cards at TP=1.
`REGIME_SCREEN` then died on both replications that ran it, identically:

```
stages/regime.coverage_criterion:566
    below = [r for r in rows if tie_key(r["iota"]) < tie_key(iota_a)]
TypeError: type NoneType doesn't define __round__ method
```

§12.6's criterion read `iota` on every eligible rung, and one rung had none:
its measured chance compliance reached `CHANCE_DEGENERACY_MAX = 0.99`, the
registered point at which iota is undefined and §11.2 records
`DIFFICULTY_COORDINATE_DEGENERATE`.

### 16.2 Latent since v5, first triggered by data

`coverage_criterion` is byte-identical in v5 and v6. What changed is which
rungs reach it. U4's two registered constructions of §12.6's eligibility
predicate are `E1` (band on iota) and `E2` (band on raw solo), and A5 resolved
it at **E2** — under which a rung can be eligible on a measured solo while
having no position on the iota axis at all. Under E1 the case cannot arise.
v5 ran E2 as well and never met it: all of its coordinate-less rungs had solo
above 0.9166 and were ineligible for a different reason.

`reports/dci1v6/degenerate_iota_rungs.json` records all eighteen
coordinate-less rungs the two replications measured, from the generated rows
and with no model re-run. Exactly one per replication is E2-eligible.

| replication | rungs measured | coordinate-less | E2-eligible | that rung |
|---|---|---|---|---|
| `gemma-3n-e2b-it` | 410 | 9 | 1 | `CR7:56`, solo 0.8750, chance 0.99306 |
| `gemma-3n-e4b-it` | 404 | 9 | 1 | `CR7:56`, solo 0.8333, chance 0.99092 |

### 16.3 Amendment A16, and why its direction was adoptable

A rung with no coordinate is **dropped** from every condition and **recorded**
under `coordinate_undefined` with its status, its solo and its chance. U4 is
not reopened and §13.4's chance ceiling is not imported into §12.6.

Every one of C1–C8 is an existence or a count, so removing a rung can only make
a condition harder to meet. That is what made the rule adoptable after the
measurements were visible: it cannot be the thing that buys a replication a
pass, whichever rungs turn out degenerate. The alternative — keep the rung in
the counts that do not reference iota — is the open direction and could buy
one; it is rejected on that ground, not on what either produces.
`test_dropping_a_coordinateless_rung_can_never_help_a_condition_pass` asserts
the property rather than arguing it.

### 16.4 What C1–C8 returned

Computed on the rows already signed onto the evidence tree. Every `rows.jsonl`
verified byte-identical to its pre-amendment hash afterwards and no new backend
run directory was created: an analysis that crashed is not a reason to
re-measure a model.

| replication | C1–C8 | decisive | dropped | placed / before drop | statuses | cap | carried |
|---|---|---|---|---|---|---|---|
| `gemma-3n-e2b-it` | all True | met | `CR7:56` | 218 / 219 | none | 512 | 410 |
| `gemma-3n-e4b-it` | all True | met | `CR7:56` | 212 / 213 | none | 512 | 404 |

**The drop changed no verdict.** Coverage is met on the placed rungs alone, so
A16 neither rescued nor blocked either replication. That is stated because it
is the honest reading and not because it was the aim: had coverage failed, the
replication would have recorded `REFERENCE_SUPPORT_NOT_IDENTIFIED` at design
time and run without the core and spectrum arms, and that would have stood.

### 16.6 The first registered scientific outcome, and it is not A16's doing

All four replications completed `REGIME_SCREEN`. Three met §12.6's coverage
criterion; **`qwen3-4b-instruct-2507` did not.**

| replication | C1 | C2 | C3 | C4 | C5 | C6 | C7 | C8 | decisive | rounds | carried | dropped |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `gemma-3n-e2b-it` | T | T | T | T | T | T | T | T | met | 1 | 410 | `CR7:56` |
| `gemma-3n-e4b-it` | T | T | T | T | T | T | T | T | met | 1 | 404 | `CR7:56` |
| `qwen3-4b` | T | T | T | T | T | T | T | T | met | 0 | 326 | — |
| `qwen3-4b-instruct-2507` | **F** | **F** | T | **F** | T | T | **F** | **F** | **not met** | 2 | 422 | `RF3:8` |

After two expansion rounds `qwen3-4b-instruct-2507` records, at design time,
`REFERENCE_SUPPORT_NOT_IDENTIFIED`, `DIFFICULTY_SUPPORT_NOT_IDENTIFIED`,
`CLASS_ARM_NOT_AVAILABLE` and `NEAR_FORM_ARM_NOT_AVAILABLE`. These are
identification statuses, not terminal ones: the replication continues and runs
without the core and spectrum arms, exactly as §12.6 registers. **It is not
repaired.** No band is widened, no ceiling lowered, no severity authored, no
rung reinstated and no expansion round added.

**The drop is not why it failed, and that is checkable rather than asserted.**
The rung A16 dropped there is `RF3:8` — structural tier **3**. Of the five
failing conditions, C1, C2, C4 and C7 are all positions relative to `iota_A`,
which a rung with no coordinate cannot occupy under any reading; and C8 counts
**Tier-2** rungs and groups, which a Tier-3 rung is not. The two conditions a
coordinate-less rung could reach under the rejected reading (ii) — C5's count
of eligible rungs and C6's Tier-1/2 families — were already met. So reading
(ii) returns the identical verdict on this replication, and A16's direction
changed nothing about the failure. The same check on the two gemmas is
trivial: their conditions were all met with the dropped rung excluded.

### 16.5 What A16 does not change

No threshold, band, ceiling, estimand, population, model, reference family,
arm, seed, verifier, wording, claim ladder or headroom band. Not U4's
predicate, not `m*`, not §34 D23 or D26. `CHANCE_DEGENERACY_MAX` stays 0.99 and
§13.4's chance ceiling stays 0.75. No rung was reinstated and no model output
was regenerated. Incident:
[`incidents/2026-08-26_regime_screen_undefined_iota.md`](incidents/2026-08-26_regime_screen_undefined_iota.md).
