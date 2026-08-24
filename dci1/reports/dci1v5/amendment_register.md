# DCI-1 v5 — the §32 amendment register

Append-only. One entry per amendment, carrying the amendment text, its timing
relative to every affected artifact, what it supersedes, and what it leaves
untouched. §32 requires exactly those four things and this file is the single
register it names.

An entry is never edited after the artifact it affects exists. A correction to
an entry is a new entry.

---

## A1 — pre-data engineering amendment (2026-08-23)

**Author.** Researcher, on the Phase-0 pre-execution report of 2026-08-23.

**Timing, relative to every affected artifact.**

| Artifact | State when the amendment was adopted |
|---|---|
| §34 decisions D0–D18 | all closed, none reopened |
| U2, P1 | resolved (A2 / confirmed), neither reopened |
| Registration manifest `2960a1fc…` | signed, verified, **superseded by this amendment** |
| Stage 1 `PROTOCOL_REGISTERED` | run for `gemma-3n-e2b-it` only; record retained, superseded |
| Stages 2–18, all models | **never run** |
| v5 model responses | **none exist**, on any model, at any stage |
| v5 calibration measurements | **none exist** |
| Gate 2.5 / §13 components | never begun, so §32's clause 3 is not engaged |
| v4r4 evidence | untouched, and untouched by this amendment |

It is therefore a **pre-data** amendment under §32's first paragraph:
prospective by definition, because no confirmatory data exist under this
version and none exist under the superseded registration either.

**Amendment text.** Three defects were found in the pre-execution sweep. None
is a scientific quantity; each made the registered lifecycle unexecutable or
its provenance untrue.

1. **V5-E1 — registration is study-level, its record is per model.**
   `run/registration_run.registration_payload` called
   `manifest.sign_registration` on every invocation, which writes the
   study-level manifest under write-once semantics, while
   `engine/transitions.assert_predecessor_passed` requires the replication's
   own stage-1 record. The second replication therefore raised
   `IntegrityError` and three of the four registered models had no legal path
   into `QUALIFIED`. **Amended:** `manifest.ensure_registration` signs on the
   first call and thereafter verifies the signature, rebuilds the manifest
   from the running code, compares by hash, and requires the same producing
   commit. A replication registering at another commit, or against a manifest
   its own code no longer reproduces, is refused.

2. **V5-E2 — the generative seam was not reachable and not guarded.**
   `GATE_0_APPARATUS`, `REGIME_SCREEN`, `GATE_2_FOCAL_CALIBRATION` and
   `GATE_4_COMPOSED_HEADROOM` each read `generate = generate or
   fake_backend(...)`. That substitutes unconditionally and admits no
   override, so `run/execute.run_backend` — the pinned backend — was reachable
   only from `CONFIRMATORY_GENERATION`, and `run/cli.py`, the only production
   entry point, passes no generator. The documented way to run Gate 0 would
   have signed fabricated text into the registered evidence tree, and no
   downstream rule refuses a synthetic row in the registered namespace.
   **Amended:** `execute.resolve_generate` decides. In the registered
   namespace `generate` must be absent and resolves to the pinned backend, and
   an injected callable is refused; the deterministic stand-in is constructed
   only in the synthetic namespace. This is the guard `assert_synthetic_only`
   already applied to `topic_limit` and `block_limit`, extended to the larger
   substitution it had been left off.

3. **V5-E3 — a row's provenance recorded the call shape.**
   `run/execute.py` stamped `"synthetic": generate is not None`, so every row
   of the four runners above was synthetic by definition and a real backend
   injected into one of them would still have been stamped synthetic.
   **Amended:** the flag is taken from the generator's own provenance, and
   `fake_backend` stamps each raw row so the flag survives a resumed run.
   Separately, `CLASSIFICATION` had not moved at adoption and still read
   `DCI-1 PROTOCOL v5 (DRAFTED, NOT ADOPTED, NOT FROZEN)`; it is now
   `DCI-1 PROTOCOL v5 (ADOPTED AND REGISTERED, NOT FROZEN)`, with the old
   string retained in `SUPERSEDED_CLASSIFICATIONS` because records under the
   superseded registration carry it.

**What it supersedes.** Registration manifest
`2960a1fc44f036abd4729f7628095475018672adfac609bb2244a8763ba00ded`, producing
commit `f8956465fb1525c738ba7f79b49698141b3c1f82`, and the `gemma-3n-e2b-it`
stage-1 record signed under it. Both are **retained, not deleted**:
`dci1/evidence/dci1v5/registration/superseded/2960a1fc…/` holds the manifest
and a supersession record, and the stage record is retained under the model's
own `superseded/2960a1fc…/`. `engine/paths.is_superseded` excludes retained
files from every current pool while the durability audit still counts them.
The replacement manifest names the superseded one in its `supersedes` field.

**The replacement.** Manifest
`70608e5d5880c6ed2b8bbea1379b47061f60ea3f0705c374d0df581bc39bda2c`, producing
commit `5e35ca687c52af86640f167fe145c20d52af36a9`, signed 2026-08-23 with a
stage-1 record for **all four** registered replications — which is the first
time that has been possible.

**What it leaves untouched.** Everything the study measures or decides:

- every §34 closure and its evidence, D17's floor spec included;
- U2 = A2 and P1 = confirmed;
- the five arms, 56 cells, 384 blocks, $M = 8$, four models and the
  1,172,544-generation budget (corrected by A2, then A3);
- the eight Tier-1 markers, their population hash and their four accepted
  limitations;
- both calibration topic banks and the split identity;
- the candidate library, every severity ladder and every reserve;
- every threshold, estimand, multiplicity family, claim level, identification
  status and terminal status;
- every prompt, wording, verifier, seed, cap and decoding policy;
- §13's reference-selection rules in full;
- v4r4's evidence.

Verified rather than asserted: the replacement manifest was diffed against the
superseded one, leaf by leaf. **Seven fields differ and every other binding is
byte-identical.**

| Field | Why it moved |
|---|---|
| `classification` | V5-E3 — the label that had not moved at adoption |
| `revision_changes.classification` | the same string, echoed by `revision_record()` |
| `producing_commit` | `f895646` → `5e35ca6`, the amendment commit |
| `protocol_hash` | §32 of the preregistration now names this register; a documentation edit, no scientific text changed |
| `supersedes` | new; names `2960a1fc…` |
| `adoption` | records the amendment's provenance beside the original approval |
| `manifest_hash` | consequent on the six above |

Byte-identical across the amendment: the models and their revisions, the design
and budget, every threshold including D17's floor block, the decision record
and its hash, the open-item resolutions, the marker population and its hash,
both topic-bank hashes and the split identity, the candidate library, the
estimands, the multiplicity families, the claim ladder, the masking
specification, the seeds, the selection rules, the measurement basis, the reuse
ledger and the red-team block.

**This amendment does not weaken a criterion to make a gate pass.** No gate had
run. It adds refusals — three of them — and removes none.

---

## A2 — pre-data accounting amendment (2026-08-23)

**Author.** Researcher, on the V5-E4 report of 2026-08-23.

**Timing, relative to every affected artifact.**

| Artifact | State when the amendment was adopted |
|---|---|
| Registration manifest `70608e5d…` (A1's) | signed, verified, **superseded by this amendment** |
| Stage 1 `PROTOCOL_REGISTERED` | PASS on all four replications; records retained, superseded |
| Stage 2 `QUALIFIED` | PASS on all four replications; records retained, superseded |
| Stage 3 `GATE_0_APPARATUS` onward | **never run**, on any model |
| v5 model responses | **none exist**, on any model, at any stage |
| Gate 2.5 / §13 components | never begun, so §32's clause 3 is not engaged |
| v4r4 evidence | untouched |

Still a **pre-data** amendment: `QUALIFIED` reads no behavioural rate by
construction (§19) and `PROTOCOL_REGISTERED` produces none, so no observation
exists under the superseded registration.

**Amendment text — V5-E4: the registered budget contradicted §19's design.**

`design/budget.py`'s `calibration_burden` costed the §19 pilot as

    C.PILOT_TOPICS * C.PILOT_DRAWS * 5          # 12 x 4 x 5 = 240

where §19 registers "the full 56-cell plan, both orders, and the registered
wording allocation, at fixture values that cannot become calibration evidence,
with $M = 4$" — `12 x 4 x 56 = 2,688`. The literal `5` is the base arm's cell
count; the term had been written as though calibration were entirely
arm-independent, which the other three terms are and the pilot is not.

`run/qualification_run.pilot_payload` always built the full plan from
`design_cells(blocks, arms, draws=PILOT_DRAWS)`. **The registered design was
never wrong; the arithmetic over it was.** Nothing executable read the figure —
the pre-freeze `generation_budget` check recomputes only the confirmatory term
— so this would have surfaced, if at all, as a 0.86% overrun nobody could
explain.

| Term | As registered | Corrected |
|---|---:|---:|
| §19 pilot, per model | 240 | **2,688** |
| calibration, per model | 100,992 | **103,440** |
| per model, total | 283,776 | **286,224** |
| **study total** | **1,135,104** | **1,144,896** |

`calibration_burden` now takes the cell count, so the pilot term follows the
arm set and a design with fewer cells has a cheaper pilot — which the previous
signature could not express. The three non-adopted D1 options are recosted with
it; **the ranking in the D1 packet's §6 does not change**, and neither does the
decision: five arms, 56 cells, 384 blocks, $M = 8$, four models.

**What it supersedes.** Registration manifest
`70608e5d5880c6ed2b8bbea1379b47061f60ea3f0705c374d0df581bc39bda2c`, producing
commit `5e35ca687c52af86640f167fe145c20d52af36a9`, and the
`PROTOCOL_REGISTERED` and `QUALIFIED` records of **all four** replications.
All are retained under `superseded/70608e5d…/`, none deleted. The
`supersede_registration` guard moved with this amendment: it refused any stage
record past stage 1, which would have made this correction impossible after
qualification; it now refuses at `GATE_0_APPARATUS`, the first stage that puts
a model response on disk. That is the boundary the guard was reaching for —
`QUALIFIED` carries no observation — and it is asserted in
`tests_v5/test_amendment_pre_data.py` against `GENERATION_STAGES` rather than
written as a number.

**What it leaves untouched.** Every scientific quantity, exactly as A1 lists
them, and additionally the D1 *decision* itself. The researcher-decision
record's D1 entry changed in one derived `consequences` line — the budget
figure it quoted — and its hash moved from `a5ec3986…` to `b3fd9185…`
accordingly. The `value`, `decided_by`, `decided_on` and `evidence` of every
closure are unchanged, as are U2 = A2 and P1 = confirmed.

**The replacement.** Manifest
`b040b343f626f095dd8a352b6b0fab9b7db87b797d82c843831783550ab1d106`, producing
commit `cd4b1b1c58fcee6a95db1bbfc22f8ac6170be4aa`, signed 2026-08-23, with
`PROTOCOL_REGISTERED` and `QUALIFIED` re-run to PASS on all four replications.
Its `design.d1_registered` equals what `dci1v5.design.budget` recomputes, which
is asserted rather than assumed. The supersession chain is
`2960a1fc…` → `70608e5d…` → `b040b343…`.

**This amendment does not weaken a criterion to make a gate pass.** No gate had
run. It corrects a cost figure upward and tightens the pilot's derivation so
the budget and the runner cannot disagree again.

---

## A3 — preregistered-rule restoration (2026-08-23)

**Author.** Researcher, on the V5-E6 report of 2026-08-23.

**Timing, relative to every affected artifact.**

| Artifact | State when the amendment was adopted |
|---|---|
| Registration manifest `b040b343…` (A2's) | signed, verified, **superseded** |
| Stage 1–2, all four replications | PASS; retained, superseded |
| `GATE_0_APPARATUS`, `REGIME_SCREEN`, `GATE_1_MEASUREMENT` on both gemmas | PASS; **invalidated and retained** |
| `GATE_2_FOCAL_CALIBRATION` | **no record on any model** — halted mid-stage |
| Gate 2.5 / §13 components | never begun, so §32's clause 3 is not engaged |
| Confirmatory rows | none, on any model |
| v4r4 evidence | untouched |

§32's pre-freeze window is therefore still open, and this is a restoration of
registered rules rather than a change to them: **every rule below was already
in the preregistration and already implemented. None was on the execution
path.**

**V5-E6 — calibration measured a population §12.7 excludes.**
`run/gates_run.gate2_payload` built the candidate set from
`regime_record["carried_set"]`. §12.2 is *high-recall by construction* and
carries every structurally admissible rung; §12.7 then says what calibration
measures: "all 88 Tier-1 and Tier-2 rungs … **plus at most 24 Tier-3 rungs**,
ordered by ascending pre-screen $\lvert\iota - \iota_A\rvert$".
`stages/regime.calibration_priority` computes exactly that and
`run/regime_run.py` **records it on the regime record**; Gate 2 read its
neighbour. On the real screen, identical on both gemmas:

| | |
|---|---:|
| Tier-1/2 rungs | 88 |
| Tier-3 measured, cap 24 | 24 |
| **§12.7 population** | **112** |
| Tier-3 dropped for budget | 214 |
| **what Gate 2 read** | **326** |

**This is the reference pool, not a cost.** The 214 excluded rungs entered
§13.7's calibration table, and from there Gate 2.5's qualification and Gate
3B's selection. **Restored:** Gate 2 reads `calibration_priority`, and
`assert_calibration_population` checks the measured set against the cap on the
mandatory path — because the wrong population is not malformed, merely larger,
and every row in it verifies.

**V5-E8 — §12.3's focal escalation had no caller.**
`stages/regime.select_focal` measures the registered grid, then asks for
§7.2's {15, 16} when no severity is eligible **or when the selection sits at
the grid top and the bracketing rule cannot be met**. It signals that with
`extension_required`. Gate 2 read only `selected`, which produced two distinct
wrong outcomes:

* nothing eligible → `selected` is `None` → `FOCAL_RANGE_EXHAUSTED` was
  raised **without measuring the extension**: a registered terminal status
  emitted where the protocol says escalate. A false scientific finding.
* eligible at the grid top → `selected` is the top rung and **not** `None` →
  Gate 2 accepted it silently, and §12.3's bracketing rule was never applied.

Either way the grid extension to 16 — R14's objection, and the region §34
D17's floor was derived to police — was **unreachable in the registered
lifecycle**. **Restored:** the escalation has a caller, the extension is
measured when asked for, selection re-runs over the union, and
`focal_extension_measured` and `focal_grid_measured` go on the Gate-2 record
(§6.1 already lists the extension as model-adaptive).

**V5-E7 — the focal-grid budget term.** It costed one split's topics and
omitted the unconstrained cell, so it read 6,912 where Gate 2 generates
13,824. §12.7 registers "A's grid, B's grid and the unconstrained cell" on
both splits, and the code matched it. The conditional extension is now named
separately (1,536 rows) rather than folded into a budget the study is expected
to spend.

| Term | A2 | A3 |
|---|---:|---:|
| focal grids | 6,912 | **13,824** |
| candidate calibration | 86,016 | 86,016 (now *asserted* at 112 rungs) |
| calibration, per model | 103,440 | **110,352** |
| per model | 286,224 | **293,136** |
| **study total** | 1,144,896 | **1,172,544** |
| conditional focal extension | — | 1,536/model, only on escalation |

**What it supersedes, and what it invalidates.** Manifest
`b040b343f626f095dd8a352b6b0fab9b7db87b797d82c843831783550ab1d106` at commit
`cd4b1b1c58fcee6a95db1bbfc22f8ac6170be4aa`, and with it the **behavioural
chains of `gemma-3n-e2b-it` and `gemma-3n-e4b-it`** — Gate 0, the regime
screen and Gate 1 on each. Those records are individually valid: none reads
the calibration population. They are invalidated all the same, because the
replication they belong to is being restarted and a chain half under one
registration and half under another is not a replication anybody can audit.

Everything is **retained, not deleted**, under
`superseded/b040b343…/`, with an `invalidated.json` per replication naming the
stages discarded and the row count that went with them.
`supersede_registration` refuses a generated chain outright unless the
researcher names it in `invalidating` with a reason: §32 calls this a
discarded replication rather than a re-registration, and the difference has to
be said rather than performed by a file move.

**No row from the abandoned runs is reused.** Retention moves the whole tree,
including `backend_runs`, off the path `run/execute._reusable_rows` reads, so
a restarted stage cannot resume into a discarded one even by accident. That is
asserted, not assumed.

**What it leaves untouched.** Every §34 closure, U2 = A2, P1, the arms, cells,
blocks, draws, models and revisions, the eight markers, both topic banks, the
candidate library, every threshold including D17's floor, the estimands,
multiplicity families, claim ladder, masking, seeds and selection rules. The
decision record is unchanged in this amendment.

**The replacement.** Manifest
`d0485a6d39d0fcf8232f111d80ef570ccae75670c9e7cb3f54d2c008b9cad501`, producing
commit `c94bffe3e7832c711e7f9c29870b26f243710e17`, signed 2026-08-23, with
`PROTOCOL_REGISTERED` and `QUALIFIED` PASS on all four replications. The
supersession chain is `2960a1fc…` → `70608e5d…` → `b040b343…` → `d0485a6d…`.
**430,080 behavioural rows are retained and invalidated** (274,944 on
`gemma-3n-e2b-it`, 155,136 on `gemma-3n-e4b-it`); the live path holds none.

**This amendment does not weaken a criterion to make a gate pass.** It adds
one assertion and one escalation path, both of which make Gate 2 *harder* to
pass than it was: a capped population, and a bracketing rule that now actually
runs.

---

## A4 — preregistered-rule restoration, stages 3–18 (2026-08-24)

**Author.** Researcher, on the stage 3–18 execution-path audit of 2026-08-24.

**Timing, relative to every affected artifact.**

| Artifact | State when the amendment was adopted |
|---|---|
| Registration manifest `d0485a6d…` (A3's) | signed and verified; **not yet superseded** — see *Registration* below |
| Stage 1–2, all four replications | PASS under `d0485a6d…` |
| `GATE_0_APPARATUS`, `REGIME_SCREEN`, `GATE_1_MEASUREMENT` on both gemmas | PASS under `d0485a6d…`; **no longer reusable** |
| `GATE_2_FOCAL_CALIBRATION` | **no signed record on any model**, on any registration |
| Gate 2.5 / §13 components | never begun, so §32's clause 3 is not engaged |
| Reference selection, Gate 4, the freeze | never reached |
| Confirmatory rows, masking, unmasking | none, on any model |
| v4r4 evidence | untouched |

§32's pre-Gate-2.5 window is therefore still open. **No reference has been
selected, no freeze exists, and no composed outcome has been observed**, so
every repair below is prospective with respect to every quantity that could
influence selection.

**What was already observed, and what it did not decide.** Limited real output
from the abandoned gemma chains had been seen operationally before this audit:
Gate 0 PASS on all four models, the regime screen executing, Gate 1
determinism holding, and the size of the high-recall carried set. **No
scientific choice below was made in response to any of it.** Every repair is
dictated by a rule already written in the preregistration; where the
preregistration does not determine a rule, nothing was chosen and the study is
blocked instead (open item U4).

### The defect class

Most of the nineteen defects in this entry are one defect repeated:

> the preregistered rule exists; `stages/` or `analysis/` implements it
> correctly; `tests_v5/` covers it; and `run/` never calls it, or calls it
> with a neighbouring field.

Nothing in the repository could see that, because every instrument asked a
different question: the tests asked *does this function behave*, the
producer/consumer contract asked *is this field declared*, and the synthetic
lifecycle asked *does the happy path complete*. The audit tooling added here
asks the question that was missing — *does the registered rule lie on the path
a replication takes* — and asks it against a real run.

### V5-E9 — fifty-eight of §15's seventy-eight family members had no producer

`run/analysis_run.estimate_all` formed twenty members. **F5 (9), F6 (14), F7
(6) and F8 (11) were computed nowhere**, and F2, F3, F9 and F10 were computed
in part: their $D(c \leftarrow g)$ members were never formed. The missing
members appeared in neither `not_identified` nor `not_computable` — they were
absent, which reads as a family that does not exist rather than one the design
did not identify. `_intervals` then skipped each empty family with a bare
`continue`, so §31's table carried no F5–F8 row and no reason for its absence.

What each missing family carries:

* **F5** — §17.4's partial-identification bounds. `Observation` has produced
  `non_vacuous_compliance` and `graded_threshold` at draw level since the
  observation layer was written, and nothing read them. Without F5 the
  vacuity-forced recomputation does not exist, so §17.4's licensing rule — *a
  claim is licensed only when the primary and the recomputation license the
  same claim* — was vacuously satisfied at every emitter.
* **F6** — the gate on §17.4's whole interpretation. `vacuity_difference`
  existed and had no caller.
* **F7** — the reciprocal estimands §13.4's lift floor was derived to protect.
* **F8** — §11.8's tier-indicator secondary: $\hat\beta$, the three core
  intercepts and $\hat\gamma$. **This is the fit U2 was resolved at A2 to make
  estimable**, and `fit_with_tier_indicator` had no production caller, so the
  resolution bought nothing.

**Restored:** every registered member is formed from one registry, so a family
cannot lose a member by nobody writing its line; each absent member is
recorded `NOT_IDENTIFIED` or `NOT_COMPUTABLE` with the registered reason; and
a family with no computable member gets an interval entry that says so.
`_licensed` now blocks F5's two recodings of `delta_difficulty` and F8's five
fit parameters with the same status that blocks `delta_difficulty` itself.

**No estimator changed.** Every member is formed by a function that already
existed, with the arguments §15 registers for it.

### V5-E10 — three of the five claim emitters had no production caller

`run/analysis_run._statements` called `emit_l1` and nothing else. `emit_l2`,
`emit_l3` and `emit_l4b` were reachable only from tests, and `emit_l4a` was
reached only by the final-report self-check, never as an emission. A complete
synthetic lifecycle emitted `{'L1': 2}` and the final report carried no other
statement.

**L3 is where $\Delta_R$ lives** — the study's central registered question —
and L3c is the refutation verdict §34 D18 was closed at `precondition` to
protect. As wired, the lifecycle could not emit it on any data.

**Restored:** `_statements` calls all five, in §18's registered order, with
the inputs §3.2 and §17 register for each: L1 per named member with its F5
recomputation; L2 gated on both L1 directions; L3 with the joint reading,
$\Xi$'s gate, the support diagnostic, the near-form availability D18 reads,
F2's heterogeneity qualifier, §13.8's realised gaps and §17.4's agreement
verdict; L4a per member across configurations; L4b per F11 member.
**Every precondition is still enforced by the emitter itself.** A caller now
exists; what licenses a claim is unchanged.

### V5-E11 — two registered terminal statuses had no production condition

`REGIME_NOT_FOUND` and `GRID_RESOLUTION_INSUFFICIENT` appeared in
`TERMINAL_STATUSES` and nowhere else in the source.

* **§12.4's regime adequacy was never evaluated.** The Gate-2 record carried a
  key named `adequacy` containing the two *thresholds* and no verdict. The
  section's own words — *"Condition 3 is a statement about a **share**, not
  about a mean; read as a statement about the mean it fires on every severity
  §12.3 declares eligible"* — were anticipated in `constants.py`, which has
  carried `GRADED_DEGENERACY_HIGH`, `GRADED_DEGENERACY_LOW`,
  `GRADED_DEGENERACY_SHARE_MAX` and `GRADED_CLAUSE_READING = "share"` from the
  beginning. Neither share was computed. **Restored:** `cell_rates` forms both
  shares at response level, `regime_adequacy` evaluates all three conditions,
  and Gate 2 raises `REGIME_NOT_FOUND` when any fails.
* **§12.3's grid-resolution diagnosis did not exist.** A grid that passes
  *through* a band between two adjacent registered severities is a statement
  about the registered ladder; an exhausted range is a statement about the
  model. Both were reported as the latter. **Restored:** `grid_resolution`
  detects the straddle and Gate 2 raises the registered status, which takes
  precedence over `*_RANGE_EXHAUSTED`.

The other eleven registered statuses were traced to a production raiser and
are reachable; `MEASUREMENT_NOT_ESTABLISHED`,
`MEASUREMENT_EVIDENCE_INSUFFICIENT` and `SPECIFICATION_AMBIGUOUS` are raised
inside `stages/gate1.py`, which the Gate-1 runner calls.

### V5-E12 — §12.6's expansion could not run, and its failure branch was ignored

`stages/regime.run_expansion` and `expansion_round` implement §12.6 exactly
and had no production caller. The consequence is larger than an unreachable
mechanism: `coverage["decisive_met"]` is read **only inside `run_expansion`**,
so a replication whose identification-coverage criterion was unmet proceeded
with the core and spectrum arms and reported $\Delta_R$ and
$\delta_{\text{diff}}$ — the exact outcome §12.6 registers as forbidden:

> If two rounds complete and C1–C6 are still not all met … the replication
> records `REFERENCE_SUPPORT_NOT_IDENTIFIED` **at design time**, runs without
> the core and spectrum arms, and never reports a $\Delta_R$ or a
> $\delta_{\text{diff}}$ obtained from an unqualified pool.

**Restored:** the regime screen runs the expansion to its registered stopping
rule, generating only newly admitted rungs on the same 24 pre-screen topics at
the same cap; the carried set and §12.7's priority are recomputed over the
expanded table; the disposition goes on the regime record; and Gate 3C reads
it, so a design-time failure drops the arms through §34 D6's existing
machinery rather than through a new rule.

### V5-E13 — §12.6's C7 and C8 verdicts were computed and dropped

Failing C7 drops the broad-class arm and failing C8 drops the near-form arm.
`coverage_criterion` returns exactly those statuses and Gate 3C read only
`carried_set` from the regime record, re-deriving arm availability from the
selection record alone. A replication whose screen said
`CLASS_ARM_NOT_AVAILABLE` could still admit a broad-class arm.
**Restored:** an arm is available when the screen admitted it **and**
selection bound a companion for it.

### V5-E14 — three registered executable agreement checks had no caller

§11.3, §11.7 and §11.8 each register an executable check that a quantity's two
algebraic forms agree to $10^{-9}$, because the solo baseline must cancel
exactly for the contrast to be a contrast among composed cells.
`assert_delta_r_forms`, `assert_order_forms` and
`assert_algebraic_forms_agree` were all implemented and none ran, so §18's
steps 8 and 9 asserted nothing. **Restored:** all three run in the unmasked
analysis and their worst discrepancies go on the record.

### V5-E15 — §23's projection audit was the empty list

§31 releases *"the projection audit: realised $\hat p_c$ against realised
composed compliance for every companion in every composed cell, with the
absolute error distribution"*, and §18 step 17 computes it.
`projection_audit` was `[]` on the analysis record and on the final report,
and `displacement_vector` and `projected_compliance_vector` had no caller — so
the one registered check on §13.6's admission rule reported nothing.
**Restored:** the audit is computed per companion per configuration, with the
registered allowance beside it, and it licenses nothing.

### V5-E16 — §31's table mislabelled its own claim level and cell

Every per-configuration row carried `claim_level` `"L1"` and `cell`
`"pair:A+B"`, so F4's matrix components and F2's companion losses were
released as L1 estimates read from the primary pair. §17.5 requires a
statement to name **the cell the composed term was read from**.
**Restored:** the claim level is the level the member supports, from the
registered ladder, and members registered to no level are `secondary` in §15's
own word; the cell is derived from the member's own name in §8.4's registered
slot order, so $D(R_1 \leftarrow A)$ and $D(A \leftarrow R_1)$ name the one
cell they were both read from.

### V5-E17 / V5-E19 — two registered guards ran only in tests

`validity.assert_lexicographic_order` is §19 test 3 — *the recorded reason is
the earliest failing component, checked on the object rather than on the
algorithm* — and `stability.assert_iota_a_stable` is §13.7's rule that
$\iota_A$ meets the same equivalence bound as every candidate, which matters
because **§12.2 measured $\iota_A$ itself moving by up to 0.048 between
stages** and every §13.8 distance is measured from it. Neither ran in
production. **Restored:** the first runs inside `qualify_candidates`; the
second runs at Gate 3A, from A's per-topic vector, which Gate 2 now records.

### V5-E20 — the coverage criterion was evaluated on an empty row set

`coverage_criterion` filters `[r for r in table if r.get("eligible")]` and the
production caller passed the §12.2 difficulty table, whose rows carry `kind`
and `tier` and no `eligible` key at all. Every condition was therefore
evaluated over **zero** rungs and C1–C6 were False on every replication,
silently, because nothing read the verdict. **Restored:** `coverage_rows`
builds the shape the criterion registers — family, structural tier, feature
group, constraint class, $\iota$ and an eligibility verdict — from the
registered family metadata. The eligibility predicate itself is **not**
determined by the preregistration; see U4 below.

### V5-E21 — $\iota_A$ was read from the wrong severity

§12.6: *"Write $\iota_A$ for the pre-screen instructed compliance of A at the
severity whose solo compliance is nearest §12.3's aim."* The runner took the
first A row in the difficulty table — the smallest severity of the target
grid. Every §12.6 distance, and C1's *strictly below and strictly above*, was
measured from the wrong point on A's own curve. On the synthetic fixture the
difference is $\iota_A = 0.875$ against $0.708$. **Restored:** the severity is
chosen by distance from `TARGET_AIM`, and the record names which severity was
used and under what rule.

### V5-E22 — §3.2's L1 identification gate was asserted, not measured

`emit_l1` takes `solo_headroom` and §12 makes it the gate: *the outcome
constraint has no solo headroom, so the L1 identification gate does not hold*.
The analysis passed the literal `True`. B's realised solo compliance at $m^*$
is the quantity the gate is a statement about and no record carried it past
Gate 2. **Restored:** Gate 2 records `solo_compliance_b`, the freeze binds it
beside `solo_compliance_a`, and the gate is evaluated per named member — B for
$D(B \leftarrow A)$ and A for $D(A \leftarrow B)$.

### V5-E23 — a declared reader that reads nothing

`run/contracts.py` declared Gate 5 and the final report as readers of Gate 2's
`construct_strength`, and neither reads it. §34 D17's verdict still reaches the
freeze — Gate 2's `identification_statuses` carry `CONSTRUCT_FLOOR_MARGINAL`
and `freeze_run` unions them — and §31 releases the Gate-2 record itself, so
the registered requirement is met and the *declaration* was the thing that was
wrong. It is corrected, and it is the first finding of the new consumption
audit: a declared reader with nothing behind it is now a reported defect
instead of a line nobody checks.

### V5-E24 — a family that could not straddle $\iota_A$ lost its core slot

`stages/selection.select_all` called `admit_core_references` with the default
`require_spectrum=True` and never fell back. §13.12 registers the opposite:
core selection re-runs excluding a family that cannot supply a triple, *"until
three families each supply a complete triple **or the qualified list is
exhausted. Exhaustion sets `DIFFICULTY_SUPPORT_NOT_IDENTIFIED` and the
spectrum arm is not generated.**"* — and §8.1: *"a replication that cannot
identify the spectrum still estimates $\Delta_R$, $\Delta_j$, $\Xi$ and the
reciprocal matrix."* Exhaustion drops the **spectrum**, not the core. As
written, a pool that could not straddle $\iota_A$ lost its core references
too, which is the exact coupling that produced v4r4's F5 failure,
re-implemented. **Restored:** the spectrum-coupled pass runs first; if it
admits no core set the selection re-runs with `require_spectrum=False`, and
the record carries `DIFFICULTY_SUPPORT_NOT_IDENTIFIED` with the reason.

*Found by the researcher's own audit of 2026-08-23
(`user-notes/AUDIT_2026-08-23_v5_design_execution.md` §4 item 4), not by this
sweep. The sweep's instruments ask whether a registered rule is on the path;
this rule is on the path and takes the wrong branch, which is a different
question and needs the section read against the code.*

### V5-E25 — $\iota_A$ was not measured on the pre-screen at all

`run/regime_run._screen_rungs` iterates `FAMILIES`, which is the candidate
library and **excludes the two outcome constraints**. So A was never measured
on the pre-screen, `iota_a_prescreen` was null on every real regime record, and
§12.6's *"pre-screen instructed compliance of A"* — the point every §12.6
distance is taken from — did not exist. `difficulty_table` says so in its own
comment: *"A and B are the outcome constraints. They are measured here because
§12.2's table is what fixes iota_A."* The rung list disagreed with it.

Two consequences beyond the criterion: §12.7's Tier-3 ordering was computed
against the literal `0.5` rather than $\iota_A$, and that ordering decides
which Tier-3 rungs calibration measures; and the null $\iota_A$ is why V5-E20
could never have been noticed from the record — `coverage` reported
`{"holds": false, "reason": "iota_A is not measured on the pre-screen"}` beside
`outcome: PASS`.

**Restored:** the screen measures A's target grid and B's focal grid,
`design/budget.screen_rungs` counts them so the budget and the runner cannot
disagree, and the record names the severity $\iota_A$ was taken from. The
registered pre-screen therefore costs 1,536 more rows per model.

| | A3 | A4 |
|---|---:|---:|
| ladder screen, rows/model | 6,672 | **8,208** |
| calibration, rows/model | 110,352 | **110,736** |
| per model | 293,136 | **293,520** |
| **study** | **1,172,544** | **1,174,080** |

*Found by the researcher's audit of 2026-08-23 (§4 item 1), not by this sweep:
the synthetic harness has always added A and B to its own screen, so the
lifecycle ran with an $\iota_A$ the production runner does not produce. **A
harness that supplies what it is testing does not test it** — the same lesson
A1 recorded about the generation seam, in a different place.*

### V5-E28 — §7.2's escalation had a caller and refused to run

A3 restored the caller for §12.3's focal escalation. The branch itself then
refused: `measure_grid` builds `Constraint("B", q)` for q in {15, 16}, and
`Constraint.__post_init__` rejects an extension severity unless the caller
sets `extended` --- *"only this flag does, and only §12.3 sets it"*. So the
first replication that actually needed the escalation would have died in the
instrument layer, and `b_star` and `slot_map_from_record` would have died the
same way at every later reconstruction of B at an extension m*.

**A3's repair had never once executed**: the synthetic lifecycle's focal curve
always found a rung inside the registered grid, so the escalation was reached
by no test and by no walk. It was the *scenario suite* that ran it --- the
first time anything put the production path into that branch --- and the
branch raised on its first instruction.

**Restored:** the extension grid is built with `extended=True`, and every
reconstruction of B from a recorded m* goes through one function that decides
the flag from the severity.

This is the clearest single argument for the scenario matrix. A restored rule
that no run exercises is a restored rule nobody has checked, and "the caller
exists" is not the same claim as "the branch runs".

### U4 (opened, unresolved) — what makes a pre-screen rung *eligible* is not determined

§12.6 evaluates the coverage criterion *"on the pre-screen table with
eligibility as §13's band on $\iota$ and its vacuity ceiling."* §13 registers
a vacuity ceiling of 0.10 and one band, $[0.10, 0.90]$ — and **that band is
registered on the raw solo compliance $p_{\text{solo}}(R)$, not on $\iota$.**
§13 registers no band on $\iota$ at all; §13.8 constrains $\iota$ only through
calipers relative to $\iota_A$. The sentence therefore names a band on a
quantity §13 does not band, and two readings are admissible:

| | Rule | What it changes |
|---|---|---|
| **E1** | $\iota \in [0.10, 0.90]$ and pre-screen solo vacuity $\le 0.10$ | reads the sentence literally; excludes a high-chance rung whose $p_{\text{solo}}$ is in band |
| **E2** | $p_{\text{solo}} \in [0.10, 0.90]$ and pre-screen solo vacuity $\le 0.10$ | reads *"§13's band"* as the rule §13 registers; excludes a rung whose $\iota$ is in band but whose $p_{\text{solo}}$ is not |

They admit different rungs, so they can produce different C1–C6 verdicts, a
different expansion, a different admitted arm set, and therefore a difference
in **whether $\Delta_R$ is identified at all**. This is not a formatting
choice and nothing here chose it. Both constructions are built by name;
`stages/regime.coverage_eligibility` refuses to run either until a researcher
resolves U4, and `assert_no_blocking_open_items` refuses the registration
manifest while it is open.

### V5-E26 — §20's withheld set matched a member's exact name

`estimate_all` withheld the masked-phase members by exact string against
`MASKED_PHASE_FORBIDDEN_MEMBERS`, and F5's recodings of $\Delta_R$ and
$\delta_{\text{diff}}$ are different strings for the same quantity computed
against the same permuted assignment of companions. With F5 restored, the
masked phase computed `Delta_R|vacuity_forced` — a value for the study's
primary quantity, in the phase the mask exists to withhold it from.

**Caught by the guard on the sealed record**, which matches on the stem:
`assert_delta_difficulty_not_masked` refused the masked analysis and the
lifecycle stopped there. **Restored:** the withholding matches on the stem
too, so the rule and the check that enforces it read the member the same way.
`gamma_tier` was also added to the forbidden set: it is the fifth coefficient
of the same §11.8 fit as $\hat\beta$ and the three intercepts, §20 names
*"the fit's coefficients"*, and its absence could not be noticed while F8 had
no producer on any path.

This one is worth stating plainly: **restoring a registered rule made a
registered guard fire, and the guard was right.** That is the shape a working
safeguard has, and it is the reason the withheld set is now derived from §15's
member list rather than typed out.

### A precedence this amendment had to fix in its own work

Extending `_licensed` (V5-E9) to block F5's recodings and F8's coefficients
with the difficulty status made that status **shadow** §20's masking reason:
on a replication whose spectrum arm was dropped, the masked record said
`delta_difficulty` was `DIFFICULTY_SUPPORT_NOT_IDENTIFIED` where §20 says
`MASKED_PHASE`. Both are true and they are different facts — one is about
what the replication can ever identify, the other about what *this phase* may
compute — and §20's is the one that holds in the masked phase whatever the
design says.

The synthetic lifecycle's own §20 test caught it. The withholding check now
runs before the identification check in every recorder, which is the order
`record()` has always used.

### V5-E27 — §18 step 14's raw-coordinate secondary fit is not implemented, and is NOT repaired here

§18 step 14 reads *"Repeat steps 9 and 12 on the raw-coordinate secondary
fit"*, and §31 releases *"the fitted difficulty relation: slope, family
intercepts, per-companion residuals, the support diagnostic and its bootstrap
share, the tier-indicator secondary, **and the same on the raw coordinate**"*.
`SECONDARY_DIFFICULTY_COORDINATE = "raw_solo_compliance"` has been in
`constants.py` from the beginning and **nothing in the repository fits
anything on it**. This is a missing implementation rather than an unreachable
one, and it is left open deliberately:

* **Step 9 on the raw coordinate is mechanical** — the same fit with
  $p_{\text{solo}}$ where $\iota$ stands — and could be written from the
  section.
* **Step 12 is not.** Step 12 is *"compute simultaneous intervals within each
  declared family"*, and §15 declares no family containing a raw-coordinate
  member. Implementing it means choosing what the interval is over — a
  one-member family, a parallel F1, or something else — and those are
  different multiplicity corrections over different member sets.

Reporting it as a diagnostic without an interval, or inventing the family, are
both choices, and neither is this amendment's to make. **It is a
Tier-secondary reported quantity that licenses no claim**, so the study is not
blocked on it the way it is blocked on U4; it is recorded here so that the
absence is a known gap rather than something a reader of §31 discovers in the
released table.

### One thing this amendment does NOT correct

`reports/dci1v5/researcher_decisions.json` states D1's derived budget as
1,144,896 — A2's figure. A3 moved it to 1,172,544 and did not update the
decision record, and this amendment moves it to 1,174,080. **The decision
itself is unchanged** — five arms, 56 cells, 384 blocks, M = 8, four models —
and only the arithmetic over it has moved twice since the line was written.
The line is a researcher artifact and is not rewritten here; it is regenerated
with the superseding registration, whose manifest binds the figure the running
code computes.

### Registration

**No superseding registration was created in this amendment.** U4 is a
`RESEARCHER_DECISION_REQUIRED` open item, so §18 stage 1 records
`REGISTRATION_INCOMPLETE` by the registered rule, and creating a registration
that ignored it would be the thing the machinery exists to prevent.
Registration `d0485a6d…` therefore remains the active record of what produced
the existing evidence, and the existing gemma chains are **retained and
not deleted**.

They are, however, **not reusable**: every one of them was produced before
this audit, under a screen whose coverage criterion evaluated an empty set,
whose $\iota_A$ came from the wrong severity, and whose expansion could not
run. Their invalidation, the superseding registration and the re-qualification
of all four replications are one operation and it is the first action after
U4 is resolved.

**What this amendment leaves untouched.** Every §34 closure, U2 = A2, P1, the
five arms, 56 cells, 384 blocks, M = 8, the eight markers, both topic banks,
the candidate library, every threshold including D17's floor and D18's
precondition, the estimands, the multiplicity families, the claim ladder and
its levels, the masking specification, the seeds, the models and revisions,
and every selection criterion. **No threshold moved and no criterion was
weakened.** Six of the twelve repairs make a gate strictly harder to pass than
it was — §12.4's adequacy, §12.6's expansion disposition, C7/C8's arm drops,
the three algebraic-form assertions, §19's lexicographic check and §13.7's
$\iota_A$ equivalence all refuse conditions that previously passed unexamined.

**Tests added.** `tests_v5/test_execution_path.py` — one regression per defect,
including the canonical `calibration_priority`-versus-`carried_set`
assertion on real payloads; `tests_v5/scenarios.py` — thirteen conditional
scenarios driving the production path into registered branches the happy path
never takes; `tools/v5_execution_path_audit.py` — the registered-rule ledger,
proved against a real run; and `run/field_access.py`, which makes *observed*
consumption a fact the contract audit can check instead of a declaration it
has to trust.

---

## A5 — the two questions A4 left open, closed (2026-08-24)

**Author.** Researcher, on the pre-Gate-2.5 execution-path audit of
2026-08-24. A4 found nineteen execution-path defects and repaired them, and
ended with two things it would not decide for itself: one preregistration
ambiguity that blocked registration (U4) and one registered quantity with no
implementation (V5-E27). This entry closes both. **No new scientific rule is
introduced by either closure.**

**Timing, relative to every affected artifact.**

| Artifact | State when this amendment was adopted |
|---|---|
| §34 decisions D0–D18 | all closed, none reopened |
| U1, U2, U3, P1 | resolved; none reopened |
| U4 | **resolved at E2 by this amendment** |
| Registration manifest `d0485a6d…` | signed, verified, **superseded by this amendment** |
| Stage 1 `PROTOCOL_REGISTERED` | held by all four models under `d0485a6d…`; records retained, superseded |
| `QUALIFIED` | held by all four; superseded and re-run |
| `GATE_0_APPARATUS` and later | **never run under this amendment**; the two gemma chains that reached Gate 1 and a partial Gate 2 are retained and invalidated |
| Signed `GATE_2_FOCAL_CALIBRATION` record | **none exists on any model**, so §32's clause 3 is not engaged |
| Reference selection, freeze, confirmatory data, masking, unmasking | never run, on any model |
| v4r4 evidence | untouched |

It is therefore a **pre-data** amendment: no confirmatory measurement exists
under v5 at any registration, and none was produced while making it. **Zero
new real model generations occurred.**

### U4 — resolved at **E2**

§12.6 evaluated the coverage criterion *"on the pre-screen table with
eligibility as §13's band on $\iota$ and its vacuity ceiling."* §13.4's table
registers the headroom band $[0.10, 0.90]$ on the **raw solo compliance**
$p_{\text{solo}}(R)$ and registers no band on $\iota$; §13.8 constrains
$\iota$ only through calipers *relative to* $\iota_A$, which are relative and
not absolute. The sentence therefore named a band on a quantity §13 does not
band.

**Adopted: E2.** A pre-screen rung is eligible when

$$p_{\text{solo}}(R) \in [0.10, 0.90] \quad\text{and}\quad \text{pre-screen solo vacuity} \le 0.10 .$$

**The coverage criterion itself does not move.** C1–C8 are still stated in
$\iota$ and still position every rung by $\iota$ relative to $\iota_A$ —
span, bracketing, the 0.15 caliper region and C4's 0.40 span are unchanged.
Eligibility is the only thing E2 decides, and it decides it with a threshold
§13.4 already registers.

**E1 is non-adopted, and the ground is that it would have invented a
threshold.** Applying §13's band *numbers* to $\iota$ is an absolute band on
$\iota$, and no section registers one. Under §33's classification that is a
new rule and therefore an amendment to §13, not a reading of §12.6. E1 stays
constructible by name so the comparison remains inspectable —
`stages.regime.coverage_eligibility(formulation="E1")` — and no reporting path
can reach it.

**What it changes.** The eligible set is determined, so §12.6's C1–C8 evaluate
over a non-empty set, the reserve-expansion loop has a defined trigger, and
`REFERENCE_SUPPORT_NOT_IDENTIFIED` is reachable under a rule a researcher
took. The two readings admit different rungs and could therefore have differed
in C1–C6, in the admitted arm set, and in **whether $\Delta_R$ is identified
at all** — which is why this blocked registration rather than being recorded
as a preference.

**Where it is durable.** `reports/dci1v5/researcher_decisions.json`, under
`open_items`, with the author, the date, the evidence and the consequences.
The registration manifest binds that file's hash, so the resolution moves only
by amendment. `coverage_eligibility` reads the **resolution**, not a literal:
`tests_v5/test_execution_path.py::test_the_coverage_eligibility_rule_still_fails_closed`
reopens U4 and asserts the rule refuses rather than defaulting to E2.

**§12.6's sentence is amended** to state the band on $p_{\text{solo}}$
explicitly, in `user-notes/DCI1_preregistration_v5.md`, carrying the reason.

### V5-E27 — the raw-coordinate secondary fit, implemented as registered and no further

A4 recorded §18 step 14 — *"Repeat steps 9 and 12 on the raw-coordinate
secondary fit"* — as unimplemented, and declined to implement it because step
12 computes *simultaneous intervals within each declared family* and §15
declares no family containing a raw-coordinate member. Choosing one would have
been choosing a multiplicity set.

**It does not have to be chosen, and the reason is in §15 itself.** §15's own
list of quantities *"reported with marginal intervals only and supporting no
claim"* names **the raw-coordinate replication of the fit**. So the protocol
already says what interval the replication gets, and it is not a simultaneous
one. The disposition is therefore:

| §18 step 14's half | Disposition |
|---|---|
| **Step 9**, on the raw coordinate | **Executed in full**: the fit on the nine non-$A$ points, $A$'s exclusion, §13.13's support conditions, $\delta_{\text{diff}}$ in both algebraic forms with the agreement assertion, and the block bootstrap with a refit per replicate. |
| **Step 12**, on the raw coordinate | **`NOT_REGISTERED_FOR_INFERENCE`**, recorded on the artifact with its reason. Marginal percentile intervals from the same bootstrap are reported in its place, which is what §15 registers. |

**No family was invented and no member was added to one.**
`tests_v5/test_execution_path.py::test_no_raw_coordinate_family_was_invented`
asserts that §15's declared members contain no raw-coordinate member, because
adding one would change the simultaneous width of every claim that family
carries.

**The one thing the raw fit is licensed to do, it now does.** §17.6's
coordinate-agreement paragraph and §34 D14's closure — *"$\iota$ remains
primary, raw solo secondary, `DIFFICULTY_COORDINATE_DEPENDENT` on
disagreement"* — both needed a raw-coordinate fit, and with none in existence
the status was unreachable and D14's closure bound nothing.
`analysis.claims.coordinate_agreement` now compares the two L3d/L3e
classifications and returns a **status, never a level**: the registered
coordinate decides which classification is emitted and the secondary decides
only whether the statement carries the status. The
`coordinate_dependent` scenario drives a real disagreement — primary L3e, raw
L3d — and asserts the emitted level is still the primary's.

**Two defects were found while wiring it**, both of the class A4 named:

* `run/analysis_run._strip_vectors` builds the record from an **explicit key
  list**, so the raw replication was computed and dropped before it reached
  the artifact. This is the same function that had already lost §11.3/§11.7's
  agreement checks once. A regression now asserts the key is in it.
* `protocol/constants.py` already registered
  `SECONDARY_DIFFICULTY_COORDINATE = "raw_solo_compliance"`, and the first
  cut of this work defined a second constant of the same name with a
  different value, shadowing it. The registered names are used and
  `analysis.spectrum.assert_coordinate` refuses any third one.

### Evidence: preserved and invalidated

The two gemma chains produced under `d0485a6d…` — 30,592 rows on
`gemma-3n-e2b-it` and 15,104 on `gemma-3n-e4b-it`, plus 430,080 rows already
retained under `superseded/` from earlier registrations — are **retained in
full and none is deleted**. They are **invalidated for reuse**: every one was
produced under a screen whose coverage criterion evaluated an empty set, whose
$\iota_A$ came from the wrong severity, whose §7.2 escalation would have
refused on its first instruction, and whose expansion could not run. §26's
reuse ledger admits a row only when its complete scientific identity matches,
and the superseding registration changes that identity, so no invalidated row
is reachable by live reuse.

### Registration

One superseding registration is created, and all four models are re-qualified
under it. Nothing beyond `QUALIFIED` is run: the next legal action for every
model is `GATE_0_APPARATUS`, and it was not taken.

**What this amendment leaves untouched.** Every §34 closure, U1, U2 = A2, U3,
P1, the five arms, 56 cells, 384 blocks, M = 8, the eight markers, both topic
banks, the candidate library, every threshold including §13.4's band, §13.8's
calipers, D17's floor and D18's precondition, the estimands, the multiplicity
families, the claim ladder and its levels, the masking specification, the
seeds, the models and revisions, and every selection criterion. **No threshold
moved, no criterion was weakened, and no family gained or lost a member.**
