# Preregistration: DCI-1 v6

*When two verifiable instructions are composed, which one is delivered, how
much is lost, and does the loss depend on the identity of the companion beyond
its difficulty?*

---

## status

    status: DRAFT_NOT_ADOPTED

**This document is a draft and the study is not registered.** No v6 manifest
exists, no v6 stage has run, no v6 behavioural row has been generated, and all
twenty-seven of §34's decisions are `UNRESOLVED` — including D0–D18, which v5's
researcher closed on v5's own record and which only the researcher can carry
into a new registration.
`dci1/src/dci1v6/protocol/manifest.assert_documents_adopted` refuses a
registration while the line above says `DRAFT_NOT_ADOPTED`, so this file cannot
function as a registration by existing. Adopting it is a researcher act: it
means the design below is the one the study commits to, and no code may make
that claim on the researcher's behalf.

## 0. What this document is, and what it incorporates

v6 is **v5's protocol with a named, enumerated set of amendments**. Rather than
copy 3,794 lines and risk a copy that drifts from the text it claims to
reproduce, this document incorporates v5's preregistration **by content hash**
and then states, in full, every place where v6 differs.

> **Base text.** `user-notes/DCI1_preregistration_v5.md`
> `sha256(path + bytes) = ebb27c152275b623f94cb07277dfebd1823b87d4d7b59e0fa9624041fb8ef751`
>
> Every section of that document — §§1–34 — is the registered text of v6
> except where an amendment below replaces or extends it. Where an amendment
> is silent, v5's text governs verbatim.

`protocol/revision.V9` checks the twelve `ESTIMAND_LAYER` modules byte-identical
to v5's, so the estimands are not merely *said* to be unchanged.

## 1. What v6 does not change

Carried without amendment, and each is executable rather than asserted:

- the primary question, `Delta_j`, `Delta_R`, `Xi`, `delta_difficulty` and the
  order contrasts; the estimators, the block bootstrap, §17.2's
  refit-per-replicate;
- the claim ladder L1–L4 with **L5 permanently withheld**, and the multiplicity
  families F1–F11;
- §6.1's cross-replication firewall — four replications, each analysed
  separately, **never pooled**, no cross-model scalar carrying a claim — and
  §15's consequence that there is no cross-model multiplicity family;
- interaction-blind reference selection, and §13.11's schema refusal of any
  composed outcome reaching it;
- **every substantive threshold**: §13.4's `HEADROOM_BAND` [0.10, 0.90],
  §13.5's calipers, §13.8's matching, §13.14's `COMPOSED_HEADROOM_BAND`
  [0.05, 0.95], §12.6's C1–C8 including C4's ≥6 qualifying feature groups, ≥3
  eligible rungs per straddling family and ≥0.40 within-family span, and
  §13.15's support requirements. §34 D17's construct floor and §34 D18's
  near-form precondition are **open decisions in v6**, not carried thresholds
  — v5's researcher closed them at `floor` and `precondition` on v5's own
  record, and only the researcher can carry a closure into a new
  registration. They are listed here because v6 proposes no change to either;
  see A13;
- §6.2's topic bank and its seeded per-area cut, unchanged in every set size:
  24 pre-screen, 96 calibration-A, 96 calibration-B, 24 composed, 384
  confirmatory, 96 sequestered;
- D6-style **irreversible** non-identification; the prospective freeze before
  any confirmatory data; one-shot masking and unmasking; §32.1's prohibition
  on using an amendment to weaken a criterion so that a gate passes and
  §32.3's freeze of §13 from the first Gate-2.5 record (earlier drafts of this
  document cited these as "§31", which is *Release*); §32's supersession
  rules;
  the write-once stage lifecycle with `verifier_source_hash` re-read at stage
  entry and exit.

**No threshold is relaxed anywhere in this document.** Every amendment adds
measurement, adds supply, or repairs a mechanism that could not deliver what a
registered rule already asked of it.

## 2. The amendments

### A1 — §12.6's expansion can reach the reserve it was widened for (V6-E01)

v5's `expansion_round` selected per family by a bracketing rule that admits
only reserve rungs lying strictly *between* the two measured edges that bracket
`iota_A`. Every Tier-1 rung between those edges is already in the round-0
ladder, so the rule returned an empty pick set for every Tier-1 family on every
replication, in both rounds: **32 reserve rungs per replication were
provisioned for C4's within-family span and were never measurable.**

v6 replaces the per-family selection with E1–E6 (`stages/regime`), which admits
reserve rungs by ascending `|iota - iota_A|` within the frozen reserve, subject
to the registered per-family and per-round caps. The caps, the reserve, the
rounds and C1–C8 are unchanged. `tools/v6_expansion_dryrun.py` replays v5's
rule and v6's side by side on the four signed v5 pre-screen tables and refuses
to report unless its baseline reproduces each signed coverage verdict exactly.

### A2 — the expansion's own measurements are visible to the criterion (V6-E02)

`run_expansion` extended its working table with raw `difficulty_table` rows,
which carry no `eligible` field, and `coverage_criterion` filters on `eligible`
before anything else. The three replications that ran an expansion measured 93,
96 and 99 reserve rungs and their recorded coverage was evaluated over 174, 179
and 174 eligible rungs against 208, 211 and 229 actually measured and carried.

v6 carries the eligibility field through the expansion. **This is not a
re-verdict of v5**: v5's coverage is what v5's registered code computed over the
rows that code passed it, those records are signed, D6 is irreversible, and
`qwen3-4b`'s `REFERENCE_SUPPORT_NOT_IDENTIFIED` remains that replication's
terminal outcome.

### A3 — reference support is evaluated at the *calibrated* `iota_A`

§12.6 spends its expansion rounds and freezes the candidate vocabulary at
`iota_a_prescreen`: A's compliance on the 24 pre-screen topics at one draw. The
quantity references are matched to is Gate 2's `iota_A` — 192 calibration
topics, four draws — measured two stages later.

v6 re-evaluates §12.6's coverage criterion at Gate 3A **on the calibration
basis**, where `iota(R)`, the difficulty coordinate, the solo vacuity and
`iota_A` all come from the same 192 topics at `M_CAL` draws. It is a paired
reading on one set of cases, not a comparison across two samples, and a lost
decisive condition there is a §13.15 **design-time failure** disposed of under
§34 D6's existing rule. **There is no drift threshold and no new terminal
status.** The pre-screen reading is recorded beside it and gates nothing.

C4 is unchanged: ≥6 qualifying feature groups, ≥3 eligible rungs per straddling
family, ≥0.40 within-family span.

### A4 — one implementation of the support criterion, for every caller

The registered stage, the operating-point search and the development pilot call
one pure kernel (`stages/feasibility`). A development prescreen that evaluated a
proxy for §13.15 could report a library feasible that the registered gate would
refuse; it cannot now, because there is no second implementation to disagree
with.

### A5 — `GATE_2_75_COMPOSED_PROBE`, a nineteenth stage

Between `GATE_2_5_CANDIDATE_QUALIFICATION` and `GATE_3A_REFERENCE_CALIBRATION`.
`STAGE_SEQUENCE` becomes 19; `PREDECESSOR` derives from the sequence, so the
transition rules need no change. The stage generates rows and is in
`GENERATION_STAGES` and `VERIFIER_BOUND_ENTRY_POINTS`.

**Why.** m\* is chosen at Gate 2 from B's *solo* curve and §13.14 checks
composed compliance only at Gate 4, after the references are selected,
calibrated and bound. On the closed v5 study all four replications sat within
0.054 of the ceiling or over it once B was composed, and one terminated there
with every earlier gate passed. The measurement that would have shown it was
available two stages earlier and nobody took it.

**Scope — every slot and order class §13.14 audits.** §8.1's 56 cell types and
95 cell × slot entries fall into ten classes under (arm, the roles of the slots
in prompt order), where a role is *target* (A, fixed at n\*), *focal* (B, fixed
at m\*) or *companion* (selected two stages later). The probe runs one cell per
class: A and B where the class names them, and a frozen `probe_only` stand-in
where it names a companion. The partition is derived from
`design.cells.cell_types` and `assert_probe_covers_gate4_classes` refuses a
probe shape leaving a class uncovered — a hand-written list is how the first
version of this stage came to protect one slot while believing it protected the
design. 18 cell types; three are read off the Gate-2 record; 15 are generated
per probed severity.

**Verdict — two rules, because the entries are not the same kind of evidence,
and only one of them decides anything.**

> **Determinate entries** — `solo:A`, `solo:B` and both orders of `pair:A+B`,
> whose every constituent is a real registered instrument that actually enters
> the estimand — pass iff their **projected Gate-4 interval** lies inside the
> evaluated band: half-width `z * sqrt(s2/N_COMPOSED + s2/n_probe +
> residual_sd^2)`, with `s2` that entry's own between-topic variance measured
> in this stage and `z` at §13.4's registered 95%. The device and the level
> are §13.4's own — contract the band, and apply it to the *interval* so an
> imprecisely measured value cannot sit on the boundary. What `residual_sd`
> and the evaluated band are is §34 D23's and §34 D26's; see A14. The
> family-wise half-width over the six determinate entries is computed and
> recorded beside each verdict and read by nothing.
>
> **Stand-in-dependent entries** — every entry of a cell containing a stand-in,
> including its A and B slots, because B's compliance beside a stand-in is not
> B's compliance beside the reference — are judged against §13.14's
> **registered** band, with no margin at all, and the verdict is **recorded
> and gates nothing**. See A13.
>
> A severity is admissible for m\* iff every **determinate** entry passes its
> own test.

**§13.14's band is unchanged.** The projection is a margin *inside* [0.05,
0.95]; Gate 4 still applies the registered band to the registered composed set.

**The transfer is recorded, not absorbed.** Under §34 D20's
`calibration_with_measured_transfer` the probe measures every entry on **both**
of §13.7's 96-topic sub-splits and records the realised movement per entry.
That movement is not a diagnostic: §6.2 cuts Calibration-A and the composed set
from one seeded per-area shuffle, so those two are exchangeable and the
difference between them is sampling, while §34 D3's Calibration-B is newly
authored and is not — so a pooled estimate carries **half** of whatever offset
the authored half introduces, and that half is the entire non-sampling term in
the error budget. `residual_sd = 0.0142` is a v5-fitted estimate of its size and
`measured_split_transfer` is the same quantity on this replication. It **gates
nothing**, deliberately: a rule that re-tuned the margin from the transfer it
was measuring would fit a design constant to the replication it is about to
judge.

**Stand-ins (S1–S5, as amended).** A stand-in is a registered instrument
carrying `probe_only = True`, excluded by construction from every selectable
pool: it may not be carried by the screen, qualified at Gate 2.5, calibrated at
Gate 3A or bound to any slot at Gate 3B. `assert_selectable` refuses one at
each of those points and `assert_no_probe_only_selection_path` refuses, by
name, any function that would promote one. Three are registered — `PS1`
(`capital_word`, exact count), `PS2` (`semicolon`, count lower bound), `PS3`
(`y_final`, rate lower bound) — spanning three of §7.3's five predicate forms,
including the one no selectable family exercises.

> **S3 as amended.** The stand-ins **reuse registered counted statistics** under
> forms no selectable family carries, and do *not* introduce a new feature
> group. Every one of §7.6's twenty-two statistics is already carried, so a new
> group would need a new statistic; `FEATURE_GROUP_IDS` is a sorted tuple and
> `selection._group_order` reads a group's index in it as a reference-selection
> tie-break, so adding a group reorders that tie-break for every selectable
> family sorting after it. A probe-only instrument that changed which reference
> gets selected is precisely the failure `probe_only` exists to prevent. What
> S2 actually requires — that no probed cell can be a B+R cell by instrument
> identity — follows from distinct *kinds*, which come free.

> **S4 as amended.** Each stand-in is probed at the severity of **its own solo
> ladder** nearest Gate 2's measured `iota_A`, inside §13.4's band, because
> §13.8 matches a reference's `iota(R)` to `iota_A` and that is where the design
> puts a companion. The ladder is measured in this stage on §12.5's 24
> pre-screen topics at `LADDER_SCREEN_DRAWS`, decides nothing but the severity,
> and is never in §12.2's table. `iota_A` does not depend on m\*, so
> re-selecting the operating point never moves a stand-in.

**No selected reference can enter this stage, and no B+R outcome can enter
reference selection.** Four independent guarantees, each enforced somewhere a
reader can point at: *temporal* (the stage precedes Gate 3B; no reference
exists), *structural* (`probe_only` is not selectable), *informational*
(§13.11's closed schema, plus §33 check 8's name scan extended to read this
record on the same terms as Gate 4's, with its own declared refusals), and
*directional* (`assert_probe_reads_no_reference` refuses by name and by source
any function here that would read a selection record).

**One re-selection, by a rule fixed before data (P3.1–P3.6).** The probed set
is the severity order Gate 2 froze — §12.3's own preference over
`focal_admissible`, which is §12.3's band **and** §12.4's regime adequacy
**and** §34 D17's floor, each evaluated at that severity — restricted by Gate
2.5 to severities that can meet §13.15's five-family minimum. Both are signed
before this stage generates a row, and Gate 2 records a κ(R|B) column and Gate
2.5 a §13.1 qualified pool for **every** admissible severity, so moving m\*
reads a pool that was already fixed rather than building one from what the
probe saw. m\* is probed first; if it passes it stands. If it fails, the probe
measures the rest of the frozen order and re-runs `select_operating_point`
**unchanged** over **Gate 2's own solo B curve** restricted to the severities
the probe admitted — the probe decides which severities are admissible, never
which is chosen. There is exactly one re-selection and no path back. If no
severity is admissible the replication terminates
`COMPOSED_HEADROOM_UNREACHABLE`, a §28 terminal status with a §28.3 report.

**Scope limits, registered rather than discovered at Gate 4.** The probe covers
every one of §13.14's ten exposure classes; what it cannot cover is the
companion's **identity**, because the reference in each companion slot is
selected two stages later. Gate 4 remains the only stage that measures the
actual references, on the reserved composed set, which this stage never
touches. Succeeding at A1–A4 raises the number of Gate-4 entries from 6 to as
many as 95, so the two bottlenecks are coupled forward in the direction that
makes v6 harder.

### A6 — `COMPOSED_HEADROOM_UNREACHABLE` registered as a §28 terminal status

Fourteen statuses in force. Raised from `probe_disposition` and nowhere else,
and covered automatically by the A8 regression that walks the AST of every
module for a status in force with no reachable `raise` — which is the fix for
v5's V5-E32 and is why this status cannot repeat it.

### A7 — §13.14's precision is left exactly as registered

READINESS R3 recommended enlarging §6.2's composed set from 24 topics to 48.
That is **not executable in this repository**: the sequestered eighth was never
materialised here — `dci1v4.topics.sequestered` holds opaque identities and
content hashes only, the texts are retained by the researcher outside the
repository, and `assert_no_materialisation` refuses any released question
colliding with a sequestered hash. Enlarging is an act of authoring topics, a
governed §6.2 change, and it spends the reserve §6.2 keeps for a future
uncontaminated rerun.

§13.14 therefore stands exactly as registered, and a v6 Gate-4 record is
exactly comparable with v5's. What v6 registers instead is the size of the
problem, measured: on the two v5 replications whose Gate-4 entries were **all
inside the band**, a joint topic bootstrap over their own realised entries puts
the chance that §13.14 nonetheless fires at **0.121** and **0.190**. A5's
projection attacks that by refusing operating points whose predicted Gate-4
entries sit within an interval's reach of the band. **v6 does not make Gate 4
more precise; it makes Gate 4's verdict less marginal.**

### A8 — confirmatory licensing is per replication (§34 D22)

Each replication that independently reaches `GATE_5_FREEZE` with §34 D6
identified may enter confirmatory generation. **Another replication's failure
does not suppress a valid model-specific result.** Two or more independently
identified and frozen replications are required for any replicated or
generalised study-level statement; a single survivor licenses only its own
registered L1–L4 ladder; **L5 remains permanently withheld** and is withheld by
design, not for want of survivors.

§6.1 registers four replications each analysed separately with no cross-model
scalar carrying a claim, and §15 registers that there is no cross-model
multiplicity family — so there is no registered study-level claim that a
two-survivor precondition would protect. Under a two-survivor rule v6's minimum
useful outcome is nothing; under this one it is one model's confirmed or
refuted ladder.

### A9 — what v6 says when exactly one replication survives (§34 D25)

Registered **before data**, so that the number of survivors cannot be read
afterwards as a licence. The two admissible readings are written out in
`run.lifecycle.SINGLE_SURVIVOR_STATEMENTS` and a closure selects one of them
rather than licensing a sentence to be composed later:

> **`survivor_ladder_only`.** Exactly one replication reached `GATE_5_FREEZE`
> identified. Its own L1–L4 claim ladder stands as registered, for that model
> and that model only. Nothing above it is said: no replicated finding, no
> cross-model comparison, and no generalisation — L5 is withheld by design and
> is not withheld for want of survivors. The other replications' terminal
> statuses are reported as terminal statuses and are never evidence about the
> effect.
>
> **`no_study_level_statement`.** Exactly one replication reached
> `GATE_5_FREEZE` identified. The study makes no statement at study level; the
> surviving replication's record stands on its own and is read as a
> single-model result.

The zero-survivor and many-survivor sentences follow from §6.1 and the claim
ladder and are not decisions; `run.lifecycle.study_level_statement` emits all
three, and **`dci1/tools/v6_closure.py` calls it**, writing
`reports/dci1v6/closure.json`. Until 2026-08-26 nothing called it: the
nineteen-stage lifecycle is per replication and its `FINAL_REPORT` stage writes
one report per model, so a statement about the study as a whole had no stage to
live in and D25's closure changed no artifact. The closure record follows the
precedent of `reports/dci1v5/closure.json`; it counts survivors from signed
records and quotes the registered sentence, and it estimates nothing.

### A10 — the library grows by three non-selectable instruments

37 families → 40. The counts `assert_library_sizes` asserts move accordingly
(round-0 severities 326 → 350, declared 632 → 656, instruments 650 → 674,
verifiers 39 → 42), and three counts are added to show that the pool §12.2
screens, §12.6 expands and §12.7 calibrates did **not** move:
`selectable_families` 37, `selectable_round_0_severities` 326,
`selectable_declared_severities` 632 — v5's values exactly. §12.2's screen
filters to the selectable pool and re-asserts it rung by rung.

The canonical `verifier_source_hash` moves. No v6 record exists at the old
hash, so nothing is superseded; the §10.2 declared instrument population is
re-certified at the new hash over 674 instances by §10.7-R5's suites, and the
650-instance evidence does not cover the three added families and is not
claimed to.

### A11 — the model panel is unchanged

The four registered replications stand. All four passed Gate 0, the regime
screen and Gates 1, 2, 2.5, 3A, 3B and 3C under v5, so the panel is not failing
on apparatus, regime or measurement; C4 missed by 2, 1 and 1 groups against a
requirement of 6; and both v6 mechanisms are about the library and the
operating point and are exercised by every replication, so a fifth model would
add a replication rather than a test of the mechanism. If held-out models are
added later, the selection rule must be fixed before registration, must rest on
published architecture and parameter-count diversity plus §6.1's servability
requirement, and **may not read any v5 or v4r4 outcome** — a model chosen
because it looked likely to survive would make v6's survival rate
uninterpretable.

### A12 — no new reference families

The v5 shortage was confounded by A1 and A2, both of which are repaired
prospectively. The proposed L1–L4 authoring expansion is **not adopted** and
remains available only as a later §32 amendment, if the correctly functioning
mechanism itself demonstrates inadequate support. The 3,072-row development
re-screen that would have separated the two has **not been run**.

### A13 — focal-only reselection: only real instruments may move m\*

Registered as an amendment because it changes what m\* is a function of.

The probe may re-select m\* once, and **only the six determinate entries
decide whether a severity is admissible**. A stand-in-dependent entry is
measured, judged against §13.14's registered band, and recorded under
`standin_findings`; it cannot remove a severity from the admissible set and it
cannot raise `COMPOSED_HEADROOM_UNREACHABLE`.

**Why.** `PS1`–`PS3` are non-selectable by construction and, by A10's design,
carry a predicate form no selectable family exercises. Under the rule this
replaces, an instrument that can never be a reference could choose the
operating point at which `Delta_j` and `Delta_R` are estimated, and could end a
replication. That is a defect in identification, not a conservative margin.
What remains true is that m\* is now a *composition*-determined quantity rather
than the solo-determined one v5 used — but every cell that determines it is a
cell of real registered instruments that the confirmatory design actually runs.

**This is a loosening relative to the rule it replaces, and it is declared as
one.** A replication whose every severity failed solely on stand-in-dependent
entries previously terminated; it now proceeds. No threshold moved: §13.14's
band, §13.4's device and level, and the determinate test are all unchanged.

**What the stand-in rows buy, then.** Of the 15 cells generated per probed
severity, 2 are determinate and 13 contain a stand-in — 1,536 rows decide m\*
and 9,984 are a prospective structural-risk record of the slot and order
classes Gate 4 will audit. Across four replications at the modal one probed
severity that is 39,936 rows, about 3% of the study's generation budget, for
evidence that gates nothing by design. It is retained deliberately: a class
whose only probe evidence is stand-in-dependent is otherwise audited for the
first time at Gate 4, which is the failure A5 exists to move earlier.

### A14 — the residual allowance is two decisions, not one

§34 D23 was one entry until 2026-08-26 and it carried a defect the red team
found: its registered text described an allowance **beyond** the measured
`composed_probe.RESIDUAL_SD = 0.0142`, and `entry_verdict` passed its value
straight in **as** `residual_sd`. Closing it at 0.0 would therefore have
deleted the one measured non-sampling term this document, the reference-design
spec and the decision register all promise is carried. The two readings also
differ in *units*.

It is now two decisions, both executable:

> **§34 D23 — what it means.** `projection_sd`: D26's number **is** the
> `residual_sd` in the projection's quadrature, and 0.0142 is applied nowhere.
> `beyond_the_measured_sd`: the projection always carries the measured 0.0142
> and D26's number contracts §13.14's band linearly on top.
>
> **§34 D26 — how large it is.** A number in [0.0, 0.45), range-checked at
> closure rather than at the stage that reads it.

**No derived value survives.** The 2026-08-25 derivation gave 0.0 on the ground
that the calibration-to-composed transfer is sampling — observed variance
0.00430 against the 0.00515 the sample sizes imply. That is a statement about
**dispersion**. What an allowance protects against is a common shift of one
replication's entries, and `precision_design.json` itself says a real
composed-set effect *"would appear as a common per-model shift and not as
instrument noise"* — and then does not estimate that shift. It is +0.045 over
thirteen observations; taking the four per-model means as the unit gives 0.0397
with a 95% interval of about (−0.025, +0.104), and the artifact's own 95% upper
bound on the residual sd is 0.0687, 4.8× the measured 0.0142.

`reports/dci1v6/residual_sensitivity.json` costs the grid under focal-only
reselection instead of proposing a point. Its finding: **every replication
retains an admissible operating point at every one of the six policies**, so
feasibility does not discriminate. What does discriminate is which severities
survive — at 0.0 and 0.0142 the four replications admit 4/3/4/4 of their eight
measured severities and three keep their v5 m\*; at 0.0687 they admit 3/3/2/3
and **all four** would re-select. The choice is a judgment about conservatism
under thirteen observations and this document does not make it.

## 3. §34: the registered open decisions

Twenty-seven. D0–D18 are v5's, carried forward and requiring their own closure
on v6's record; D19–D26 are v6's. `protocol/decisions` blocks each dependent stage
and each dependent function while one is open, and `assert_transition_legal`
refuses a stage with an open decision, so an unclosed decision stops the study
rather than silently defaulting.

| id | question | derivation available |
|---|---|---|
| D19 | reachability repair alone, or repair plus new families | acceptance (A12) |
| D20 | does the probe spend §6.2's reserved composed set | `calibration_with_measured_transfer` (A5) |
| D21 | §13.14's precision | acceptance (A7) |
| D22 | what licenses confirmatory generation | `per_replication` (A8) |
| D23 | what the residual allowance *means* | none — two executable readings (A14) |
| D24 | where the stand-ins are registered | `probe_only_in_library` (A10) |
| D25 | the single-survivor statement | two registered sentences (A9) |
| D26 | how large the residual allowance is | **none** (A14) |

**Thirteen of the twenty-seven are acceptances, not selections.** The
2026-08-26 red team found that D2, D5, D7–D15, D19 and D21 offered alternative
values the implementation carried **no branch for** — closing at one would have
registered a study the code cannot run, silently, because nothing read the
value. Each such alternative moves to `unimplemented_alternatives` on the
register, where it is recorded rather than deleted, and `close()` refuses it by
name. Adopting one of them is a §32 amendment *with an implementation*, not a
closure. The count of §34 entries is unchanged apart from D26.

**§34 D0's refusing value now refuses.** `do_not_adopt` was read by nothing, so
closing there signed a manifest exactly as `adopt` did; `signing_blockers` now
raises `NOT_ADOPTED`.

**§34 D16, D17 and D18 carried the wrong proposal until 2026-08-26.** The
register held v5's *pre-adoption draft* text — `a_survivors`, `no_floor`,
`not_a_precondition` — in every case the branch v5's researcher rejected, and
in every case the weaker one. `reports/dci1v5/researcher_decisions.json`
records `complete_population`, `floor` and `precondition`, and the register now
quotes those with v5's evidence. Carrying them into v6 remains a researcher act.

**A derivation is not a closure.** Each is recorded as a standing proposal in
`protocol/decisions` with its evidence, and every one of them is `UNRESOLVED`
until the researcher writes `dci1/reports/dci1v6/researcher_decisions.json`.
No code may write that file.

## 4. Provenance, and the honest statement about fitting

v6's design was chosen after reading the **closed** v5 study. §32.2 requires
that a change adopted after a gate has run is declared as adopted *because*
that gate ran, rather than presented as independent, and §32.1 names "add a
family" among the things a gate failure is not an occasion for. So, plainly:

**v5's Gate 4 fired, and `GATE_2_75_COMPOSED_PROBE` and the three `probe_only`
families `PS1`–`PS3` exist because it did.** Neither is a weakening: the probe
adds a measurement and can only make a replication terminate earlier, and the
three families are non-selectable by construction, so §7.10's reference pool is
unmoved at v5's 37 families, 326 round-0 and 632 declared severities. But they
are not independent of the outcome that prompted them and this document does
not present them as though they were.

Four quantities are fitted to v5 observations:

1. `composed_probe.RESIDUAL_SD = 0.0142`, half the measured
   calibration_a-vs-calibration_b residual;
2. the decision to leave §13.14 as registered rather than change its
   criterion, which rests on the measured false-termination rate;
3. the choice of `iota_A` as the stand-ins' placement target, which is §13.8's
   registered rule but was checked against v5's realised curves;
4. the grid `reports/dci1v6/residual_sensitivity.json` sweeps, whose three
   magnitudes are all read off the closed v5 record.

Per §30's precedent, **retrospective behaviour on v5 is not prospective
validation.** v6 is the prospective test of these choices and may not claim
they generalise. Every v5 quantity read in designing v6 is classified
`DEVELOPMENT_EVIDENCE`; no v5 row is v6 confirmatory evidence; the three
`REFERENCE_SUPPORT_NOT_IDENTIFIED` verdicts are never read as null results; and
v5's records, verdicts, terminal statuses and D6 irreversibility stand exactly
as signed.

Development evidence: `dci1/reports/dci1v6/readiness_evidence.json`,
`precision_design.json`, `expansion_dryrun.json`,
`reference_feasibility.json`, `residual_sensitivity.json`. Producers:
`dci1/tools/v6_readiness_evidence.py`, `v6_precision_design.py`,
`v6_expansion_dryrun.py`, `v6_reference_feasibility.py`,
`v6_residual_sensitivity.py`. The study's closing record is
`reports/dci1v6/closure.json`, written by `v6_closure.py`; it is a registered
outcome, not development evidence, and no v6 stage has produced one. The machine-readable reference design is
`dci1/reports/dci1v6/reference_design_spec.json`, generated by
`dci1/tools/v6_reference_design_spec.py` from the registered code so that a
spec disagreeing with the implementation is not expressible.
