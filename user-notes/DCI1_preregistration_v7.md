# Preregistration: DCI-1 v7

*When two verifiable instructions are composed, which one is delivered, how
much is lost, and does the loss depend on the identity of the companion beyond
its difficulty?*

---

## status

    status: ADOPTED

**Adopted 2026-08-28.** This document is the design DCI-1 v7 commits to. It
was drafted 2026-08-27, its §13.14 was revised on 2026-08-28 before adoption
(A2, V10, after the boundary audit), and it was adopted on 2026-08-28. All
twenty-six of §7's decisions and the three blocking §33 items are closed on
`dci1/reports/dci1v7/researcher_decisions.json`, with each value, its
evidence, who took it and when; D0–D22, D24 and D25 are re-taken at the
values v6's researcher adopted, each with a `carried_from` block naming v6's
record (and through it v5's), and D27 is closed on v7's own evidence.
`dci1/src/dci1v7/protocol/manifest.assert_documents_adopted` reads the line
above, so a draft cannot function as a registration by existing, and
adoption is a researcher act no code performs.

**Zero v7 behavioural rows existed when this line changed.** No v7 stage had
run and no v7 manifest existed. Everything below was therefore written before
any v7 outcome could be observed, which is what makes it a preregistration
rather than a report.
It was written **after** the closed v6 study had been read in full, and §4 and
§8 say exactly which v6 observations it responds to and how.

**This is a superseding registration, not a v6 amendment.** v6's §32.3 —
carried verbatim from v5 — freezes every component of §13, including §13.14,
from the first Gate-2.5 record, and all four v6 replications hold one. v6's
§32.1 forbids using an amendment to weaken a criterion so that a gate passes,
and three v6 replications terminated on the criterion this document withdraws.
Neither rule has an exception, and this document does not ask for one. v6 is
**closed** (`dci1/reports/dci1v6/closure.json`, zero survivors of four); its
verdicts stand as v6 outcomes under v6's rule; v7 is a new registration with
its own evidence tree, its own seeds and its own stage records. §3 sets this
out.

## 0. What this document is, and what it incorporates

v7 is **v6's protocol with a named, enumerated set of amendments**, and v6 was
v5's with a named, enumerated set. Rather than copy the text and risk a copy
that drifts, this document incorporates v6's preregistration **by content
hash** — and through it v5's — and then states, in full, every place where v7
differs.

> **Base text.** `user-notes/DCI1_preregistration_v6.md`, as it stands after
> its amendments A15, A16 and A17:
> `sha256(path + bytes) = ef7d17871130636994874f0da13b037986d4c275f37182314ced31e0fc6dda92`
> (the hash v6 *registered* was `95db6df4…`; A16 and A17 were adopted after
> registration and moved it, which is the fact §2 A4 responds to).
>
> v6 incorporates `user-notes/DCI1_preregistration_v5.md`,
> `sha256(path + bytes) = ebb27c152275b623f94cb07277dfebd1823b87d4d7b59e0fa9624041fb8ef751`.
>
> Every section of v5's document — §§1–34 — as amended by v6's A1–A17 is the
> registered text of v7 except where an amendment below replaces or extends
> it. Where an amendment is silent, the incorporated text governs verbatim.

`dci1/src/dci1v7/protocol/revision.py` enumerates every difference from v6 as
a `Change` with an executable check (V1–V10), and `assert_changes_realised` is
on the registration path, so a listed change the code does not make stops
stage 1. `revision.V9` compares the twelve `ESTIMAND_LAYER` modules byte for
byte against v6's, so the estimands are not merely *said* to be unchanged.

## 1. What v7 does not change

Carried without amendment, and each is executable rather than asserted:

- the primary question, `Delta_j`, `Delta_R`, `Xi`, `delta_difficulty` and the
  order contrasts; the estimators, the block bootstrap with **one index draw
  per replicate**, the studentised maximum-modulus simultaneous intervals,
  §17.2's refit-per-replicate;
- the claim ladder L1–L4 with **L5 permanently withheld**, the multiplicity
  families F1–F11, **every licensing threshold** — L3a at 0.10, L3b at 0.25,
  L3c at 0.10, the ±0.10 equivalence region, and every §16.2 precision
  precondition;
- §6.1's cross-replication firewall — four replications, each analysed
  separately, **never pooled**, no cross-model scalar carrying a claim;
- interaction-blind reference selection, §13.11's schema refusal of any
  composed outcome reaching it, and §12.5's sequence: *propose → measure solo,
  chance and counterfactual-chance → freeze the vocabulary and the selection
  rule → only then observe composed outcomes*;
- **every admission threshold**: §13.4's `HEADROOM_BAND` [0.10, 0.90], the
  lift floor 0.20, the chance ceiling 0.75 / 0.85, §13.6's projected band
  [0.10, 0.90] and displacement bound 0.25, §13.7's equivalence bound 0.20,
  §13.8's calipers, §12.6's C1–C8 including C4's ≥6 groups / ≥3 rungs / ≥0.40
  span, §13.15's support requirements, §34 D17's construct floor, §34 D18's
  near-form precondition. **§13.4's and §13.6's bands were derived, in v5, by
  contracting §13.14's composed-headroom band by 0.05 on each side. The
  values do not move; the derivation is now historical** (A2);
- §6.2's topic bank and its seeded per-area cut, unchanged in every set size;
- §12.3's selection of n\* and m\* from solo curves, §12.4's regime adequacy,
  and v6 A13: **m\* is frozen at Gate 2** and no later stage may move it;
- D6-style **irreversible** non-identification; the prospective freeze before
  any confirmatory data; one-shot masking and unmasking; the write-once stage
  lifecycle; §32.1 and §32.3 exactly as written;
- v6's A5 (the probe's ten-class shape and its stand-ins), A10 (the three
  `probe_only` families, non-selectable by construction), A15 (a stage-1
  readiness verdict is a refusal), A16 (a coordinate-less rung is dropped from
  §12.6) and A17 (an unplaceable stand-in is recorded);
- **nineteen stages**, in v6's order and under v6's predecessor rule. Stage 11
  is renamed `GATE_4_COMPOSED_CONTRAST`; its record file, its position and its
  inputs are v6's.

**No threshold moves anywhere in this document.** v7 withdraws a criterion; it
lowers no bar, adds no family, widens no caliper and moves no operating point.
`revision.V8` checks the absence rather than trusting it.

## 2. The amendments

### A1 — the absolute composed-headroom criterion is withdrawn as a terminal requirement (§13.14, §28.3, §18 stages 8 and 11)

**What is withdrawn.** v5's §13.14: *"Every registered cell type is generated
on the 24 composed-validation topics … and its compliance rate is evaluated
independently against the band [0.05, 0.95] for each of its constraints …
Any cell type outside the band returns `COMPOSED_HEADROOM_FAILURE`."* And v6's
A5/A13: a determinate probe entry whose projected Gate-4 interval left that
band returned `COMPOSED_HEADROOM_UNREACHABLE` at Gate 2.75. Both statuses
leave §28.3's vocabulary and join `WITHDRAWN_STATUSES` with the reason
recorded; no module in `dci1v7` can raise either, and a test asserts the
converse of v6's A8 regression for each (every status in force has a raise
path; a withdrawn status has none).

**Why.** The quantity the study exists to estimate is a **paired contrast
between composed cells**. Per configuration,

$$\Delta_R \;=\; \tfrac{1}{3}\textstyle\sum_j \mathbb{E}[\bar X_{B,\,B+R_j}] \;-\; \mathbb{E}[\bar X_{B,\,A+B}],$$

formed inside each block, with the solo baseline cancelled (§11.3). A
compliance rate near 0 or 1 in one of those cells is a property of **one arm**.
It does not make a difference of rates undefined, and it does not make the
comparison uninterpretable; what it can do to the *contrast* is specific,
bounded, and stated in A2. The withdrawn criterion inspected each arm's
marginal rate against an absolute band and ended the replication when one
approached an edge. On the closed v6 study it ended:

| replication | stage | what fired | what it was |
|---|---|---|---|
| `qwen3-4b` | Gate 2.75 | `pair:B+A`, B = 0.891, projected interval to 1.002 | B's compliance **rose** under A from its solo 0.747 — a delivery gain on the treated arm |
| `qwen3-4b-instruct-2507` | Gate 2.75 | `pair:A+B`, B = 0.875 → 0.994; `pair:B+A`, B = 0.924 → 1.024 | the same, from a solo 0.779 |
| `gemma-3n-e4b-it` | Gate 4 | `solo:CL` = 0.958 | the broad-class control's **own solo compliance** on 24 topics — a quantity that enters no primary estimand |

A delivery gain on the treated arm is a measurement of $D(B \leftarrow A)$
with a sign. Under the withdrawn rule it was a reason to stop measuring.

**What stays.** A and every reference are still vetted prospectively, before
any composed cell is read, by the whole of §12 and §13.1–§13.13 and §13.15:
solo calibration on both splits, chance correction and $\iota$, vacuity,
witnesses, the interaction gate, two independent calibration splits, the
support requirements, the construct floor. Nothing in that machinery reads a
composed outcome and nothing in it changes. What v7 declines to do is let a
composed outcome — after A and R are frozen — make the arm it was measured on
*invalid by fiat*.

**What still ends a replication before the freeze.** Everything §28.3 lists
that is not about a composed rate: qualification, apparatus, response length,
the outcome constraints' ranges, grid resolution, regime adequacy (including
B's solo vacuity ceiling of 0.10 and the graded non-degeneracy shares), the
construct floor, the pre-freeze audit, and Gate 1's measurement rule. Eleven
statuses, twelve when §34 D6 is closed at `terminal`. The construct-validity
safeguards that make an outcome *meaningful* — verifier processing failures
(§14.2, retained and reported, never excluded), truncation (§12.1's cap
selection and §14.2's retention), missing draws (a cell fails closed short of
$M$), duplicates (§14.2), vacuity (§12.4 at calibration; F6 and the
vacuity-forced recomputation at analysis) — are exactly as registered. None of
them is a band on a composed rate.

**§18 stages 8 and 11 have one outcome each, `PASS`.** Each records; neither
decides. `audit_prefreeze.NAME_SCANNED_RECORDS` admits no other outcome on
either record, and the Gate-4 record must now declare, beside §13.14's
no-selection and no-substitution refusals, that no composed rate terminates a
replication.

**Both directions of the change are declared (§32.2).** Relative to v6 this is
a **loosening** with respect to what ends a replication: a replication whose
composed rates sit at an edge now continues to the freeze where it previously
stopped. It is adoptable *not* because it lets replications continue — that is
the direction §32.1 scrutinises — but because the criterion it withdraws was a
statement about marginal arm rates and the estimand is a contrast. A2 says
what the contrast-level reading is; §5 says why it is coherent. Nothing here
was chosen by computing which rule lets the most replications through: the
withdrawal is total, and the only threshold the replacement reads is the
registered SESOI.

### A2 — what a composed rate at 0 or 1 does to a contrast (new §13.14)

§13.14 is replaced by the following, implemented in
`dci1/src/dci1v7/analysis/boundary.py` and run in three places on one rule.

**Revised 2026-08-28, before adoption (V10).** A focused statistical audit
of this section — `dci1/reports/dci1v7/boundary_audit/DECISION_MEMO.md`,
with the simulation on the registered procedure beside it — kept readings 2
and 3 as written and changed reading 1: a structural zero is no longer a
veto on every classification. Its decision interval is the allowance of
reading 2 alone, symmetric about zero, so it has no direction by
construction; an equivalence-type reading is licensed exactly when that
interval satisfies the registered rule. The reasons are in §5 below and in
the memo; no threshold moves.

**§13.14 (v7). Boundary readings of a composed contrast.** For every
registered member that is a fixed linear combination of cell means —
$D(c \leftarrow g)$, $\Lambda$, $\Delta_R$, $\Delta_j$, $\Delta^A$,
$\Delta_{\text{near}}$, $\Delta_{\text{broad}}$ and the five order contrasts
— the analysis reads three things off the member's own constituent cells on
the blocks it is estimated on. $\delta_{\text{diff}}$ refits per replicate and
$\Xi$'s bracket is read through $\Delta_R$'s cells; neither carries a reading
of its own.

1. **Structural zero.** When every cell the contrast differences sits at the
   *same* exact boundary — every block mean exactly 0, or every block mean
   exactly 1 — the contrast is 0 with zero *observed* variance. The member
   records `COMPOSED_CONTRAST_STRUCTURAL_ZERO` and carries the marker
   `STRUCTURAL_ZERO`. Its **decision interval is reading 2's allowance
   alone**, $\pm h_n$ with $h_n$ the Wilson half-width at the block count
   ($h_{384} = 0.0099$; $h_{24} = 0.138$), and every §17 rule reads that
   interval as it reads any other. Two consequences follow by arithmetic
   rather than by a rule: **no directional classification is reachable** —
   L1, L2, L3a, L3b and L4b are not emitted, and the direction is
   `DIRECTION_UNRESOLVED` — and **an equivalence-type reading is licensed
   exactly when $\pm h_n$ satisfies the registered rule**: at 384 blocks
   it lies inside the $\pm 0.10$ region and meets the 0.05 precondition,
   so L3c (and $\Delta_{\text{near}}$'s "below") is read; on Gate 4's 24
   topics it does neither. A statement so read carries the status and the
   registered sentence `STRUCTURAL_ZERO_SENTENCE`: *the bound is the
   allowance at the registered block count, not observed variation, and the
   composed set did not discriminate between A and its companions on the
   registered task distribution; the excess is bounded, not measured.*
   $D(A \leftarrow B)$ reads A's cells and is unaffected by B's. (Until
   2026-08-28 this reading vetoed every classification; §5 says why that
   was withdrawn.)
2. **An arm at a boundary.** When at least one constituent cell is at an
   exact boundary, the block bootstrap sees no variance from that cell and the
   simultaneous interval is too narrow in the direction that would move the
   cell off its edge. The only sampling statement the design licenses about a
   rate observed at 0 or 1 over $n$ blocks is the 95% Wilson interval at $n$:
   at 384 blocks a rate observed at 1.0 is at least 0.990. The **decision
   interval** — what every §17 rule and every emitter reads — is the
   simultaneous interval widened, **in the open direction only**, by each
   boundary constituent's absolute weight times that half-width (0.0099 at
   384 blocks; a third of it for one reference in $\Delta_R$'s mean). The
   simultaneous interval is reported unchanged beside it. The member records
   `COMPOSED_ARM_AT_BOUNDARY`. The widening is conservative: it makes every
   licensing rule harder to satisfy, never easier.
3. **A compressed direction.** For a two-arm contrast — positive weights
   summing to one, negative to minus one, which is every member above except
   $\Lambda$ and $\text{Ord}_\Lambda$ — write $L_P$ and $L_N$ for the observed
   levels of the positive and negative arms. By arithmetic,
   $\Delta \le 1 - L_N$ and $\Delta \ge -L_N$; $\Delta \le L_P$ and
   $\Delta \ge L_P - 1$. So the contrast **cannot reach** $+\text{SESOI}$ when
   $L_N > 1 - \text{SESOI}$ or $L_P < \text{SESOI}$, and cannot reach
   $-\text{SESOI}$ when $L_P > 1 - \text{SESOI}$ or $L_N < \text{SESOI}$. For
   $\Delta_R$ the negative arm is B under A and the positive arm is B under
   the reference mean, so B delivered under A above 0.90 closes the
   *excess* direction — L3a and L3b are unattainable by arithmetic — and a
   reference mean above 0.90 closes the *comparative-advantage* direction.
   The member records `COMPOSED_CONTRAST_RANGE_COMPRESSED` with the direction,
   the arm and its level, and the attainable range given each arm. **The
   licensing rules read the decision interval exactly as registered.** A
   compressed direction changes no verdict; it says, on the statement, that
   the verdict in that direction followed from an arm's level rather than
   from a comparison that could have gone the other way. When B is delivered
   under A at 0.92 and L3c is licensed, the statement says so.

`CONTRAST_COMPRESSION_LEVEL = 1 − SESOI = 0.90` and the Wilson level 0.95 are
the only numbers the rule reads, and both are registered already. The
(0.05, 0.95) band survives as `COMPOSED_PROXIMITY_BAND`, **descriptive**: it
classifies a cell as *near* a floor or ceiling on a stage record and anchors
§13.4's and §13.6's derivations. It gates nothing.

**Where the rule runs.** Three times, on one function, so that the
qualification a statement carries at the end was projected before the freeze:

- `GATE_2_75_COMPOSED_PROBE` (A1 as amended here; v6's A5 shape and stand-ins
  retained under §34 D27): at the frozen m\*, on the 192 calibration topics at
  $M_{\text{cal}}$, the six determinate entries are combined into the paired
  per-topic contrasts $D(B \leftarrow A)$, $D(A \leftarrow B)$ and $\Lambda$
  in each configuration and $\text{Ord}_A$, $\text{Ord}_B$, $\text{Ord}_\Lambda$
  across them — the algebraic forms §11.2 and §11.7 register, checked against
  the estimators on a synthetic table — bootstrapped over topics with §17.1's
  one-index-draw construction, read through the rule, and projected to the
  confirmatory half-width (below). Stand-in-dependent entries are classified
  for proximity and recorded under `standin_proximity`; they enter no
  contrast. Gate 2 records `solo_topic_values`, the per-topic solo vectors,
  so the pairing is inside the topic and reuses no second sample.
- `GATE_4_COMPOSED_CONTRAST` (§18 stage 11): the rows on §6.2's 24 composed
  topics become an `ObservationTable` over topics as blocks, every registered
  contrast the admitted arms supply is formed by the confirmatory estimators
  themselves, each family is bootstrapped, each member is read through the
  rule and projected. The per-cell compliance table v5 recorded is kept as a
  descriptive record with each entry's proximity. The freeze binds the
  projection (`composed_contrast_projection`).
- `UNMASKED_ANALYSIS`: the same, realised on the 384 confirmatory blocks; the
  decision intervals and statuses feed the emitters; the record carries the
  realised readings beside the Gate-4 projection and whether they agree.

**Projected precision, recorded and not gated.** For every contrast the probe
and Gate 4 form, the confirmatory half-width is projected from the measured
between-topic variance of the paired contrast and the draw component
estimated from each constituent's own binomial variance inside a topic
(bias-corrected by $m/(m-1)$), re-combined by §16.1's form at the registered
$M = 8$ and 384 blocks, at the family's Šidák planning constant — the constant
§16.2's table is quoted at. It is recorded beside the member's §16.2
precondition and labelled `PROJECTION_NOT_REGISTERED_FOR_INFERENCE`. It gates
nothing: §17.3's precision precondition is evaluated on the realised
confirmatory interval, `INSUFFICIENT_PRECISION` is its registered consequence,
and a replication that reaches Gate 5 is run. **This is the answer to whether
a precision gate is still necessary: no.** The consequence of inadequate
precision is already registered and non-terminal, and a 24-topic projection
of a 384-block half-width is a projection.

**Direction is a named outcome (§28.1).** Three rows are added, reading the
decision interval and no new threshold:

| Outcome | Condition | Licensed statement |
|---|---|---|
| Local excess resolved | $\Delta_R$ lower bound above 0 | `A_HARMS_MORE`: $A$ costs $B$ more than the same-form matched companions do, in this configuration |
| Comparative delivery advantage resolved | $\Delta_R$ upper bound below 0 | `A_COMPARATIVELY_BETTER`: the matched companions cost $B$ more than $A$ does; $A$ produces comparatively better delivery of $B$ |
| … beyond the smallest effect of interest | the corresponding bound beyond $\pm 0.10$ | the advantage or excess exceeds the SESOI |

An interval compatible with 0 is `DIRECTION_UNRESOLVED`. Every L3 statement
carries the direction, the decision interval and the boundary reading. The
rows L3a, L3b and L3c license are unchanged; what changes is that "$A$ is
better than its matched references" is now a named finding rather than the
absence of L3a.

### A3 — §26's success criterion, restated on the estimand

v5 §26's methodological objective read *"… those controls survive Gate 4's
composed-headroom validation **without replacement**."* The without-replacement
guarantee stands on its own — `gates_run.assert_no_substitution_path` and
`selection.assert_no_backup_substitution` — and the clause that named a
withdrawn criterion is restated:

> Before Gate 5, v7 identifies a sufficiently redundant set of stable,
> structurally appropriate, non-degenerate reference controls — at least five
> families passing the full $V(R)$ on both calibration splits, three used and
> two frozen — and the composed contrast $\Delta_R$ those controls define is
> **estimable** on Gate 4's composed set: not a structural zero, in either
> configuration.

Recorded `MET` / `NOT_MET` on the Gate-3C and Gate-4 records as before. A
structural zero there records `NOT_MET` and terminates nothing; the
confirmatory blocks decide.

### A4 — a post-registration amendment is bindable (§32)

**The gap.** `gemma-3n-e2b-it` passed every scientific gate of v6 — Gate 4
included — and terminated at `PREFREEZE_AUDIT` on `protocol_hashes_agree`: the
preregistration on disk was not the one the registration bound, because A16
and A17 had been adopted, correctly and with full disclosure, *after*
registration and after rows existed. v6's lifecycle had two ways to change a
registered document and neither covered that case: `supersede_registration`
is admissible only before any observation, and `retire_apparatus_fault` retires
one stage-1 verdict before any row. §32 describes an append-only register;
nothing implemented it, and a correct amendment ended the study's one surviving
replication.

**The rule.** `registration_run.amend_registration` writes a signed,
write-once record under `registration/amendments/<sequence>_<id>.json`
carrying: the document hashes **before** (the chain head) and **after** (the
files on disk); the amendment's id, reason and the sections it touches; its
declared direction relative to the criterion it touches (`tightening`,
`loosening`, `neutral`); the §32.2 disclosure in the researcher's words; and,
per replication, the stage reached, the terminal status if any, and the number
of behavioural rows on the tree at adoption. `manifest.document_binding` walks
the chain from the registered hashes, refusing a link that does not extend the
head; the pre-freeze audit's `protocol_hashes_agree` compares the documents on
disk against the chain head; the freeze binds the chain and the registered
hash beside the hash in force. The CLI is `dci1v7 amend`.

**§32.3 is executable.** An amendment naming any §13 section is refused once
any replication holds a Gate-2.5 record. **§32.1 is not decidable by code**;
the record requires the direction to be declared and the disclosure written,
so that a reader can judge it, and the registration manifest binds the rule.

### A5 — §34: two decisions withdrawn, one added

v6's **D23** (what the Gate-2.75 residual allowance *means*) and **D26** (how
large it is) parameterised the projected-interval verdict A1 withdraws. No v7
function reads either; they are withdrawn with their consumer and named in
`decisions.WITHDRAWN_DECISION_IDS` so the numbering stays legible. The measured
0.0142 stays on v6's record as development evidence about the authored
sub-split. **D27** (acceptance): the probe stage is retained as a recording
stage — it is the only pre-selection measurement of $D(B \leftarrow A)$ on 192
topics, it records before any reference is chosen whether the A arm sits where
$\Delta_R$'s excess direction is compressed, and its stand-in cells remain a
structural-risk record of the classes Gate 4 measures; dropping it is a change
to §18's sequence with no implementation here. Twenty-six entries; §7.

## 3. Why this is a superseding registration and not a v6 amendment

Three registered rules, each carried unchanged into v7, decide it:

1. **§32.3.** *"No component of §13 changes after Gate 2.5 begins on the first
   replication."* All four v6 replications hold a `GATE_2_5` record. §13.14 is
   a component of §13.
2. **§32.1.** *"An amendment is never used to weaken a criterion in order to
   make a gate pass."* Two v6 replications terminated at Gate 2.75 and one at
   Gate 4 on the criterion A1 withdraws. Whatever the argument for the
   withdrawal, adopting it inside v6 would be that sentence's textbook case.
3. **§28's irreversibility.** A §28 terminal status mechanically disables
   every later command for that replication, and v6 has no lifecycle path
   that lifts one — by design (v6 A15 built the one retirement path to refuse
   *"any §28 status"*).

So v6 closes with zero survivors and four terminal statuses that **stand**:
`COMPOSED_HEADROOM_UNREACHABLE` on both Qwens, `COMPOSED_HEADROOM_FAILURE` on
`gemma-3n-e4b-it`, `PREFREEZE_AUDIT_FAILURE` on `gemma-3n-e2b-it`. v7 does not
re-verdict them, does not carry a v6 stage record as its own predecessor, does
not reuse a v6 row, and re-runs its pre-composed stages under its own seed
domain. `dci1v7.FOREIGN_STUDY_PREFIXES` names `dci1v6`; `engine/guards` refuses
its trees as analysis input; `reuse_ledger` classifies its four terminal
reports and its closure record `HISTORICAL_OUTCOME` and its probe and Gate-4
records `DEVELOPMENT_EVIDENCE`.

**What v6's outcomes are, and are not.** Under v6's registered rule they are
correct terminations. Under v7's rule the same measurements would have been
recorded — a delivery gain on B under A on both Qwens, with the excess
direction of $\Delta_R$ compressed; a companion at proximity on
`gemma-3n-e4b-it` — and the replications would have continued to Gate 3 (the
Qwens) and the pre-freeze audit (the Gemma). **That is a statement about the
rule, not a re-verdict.** And it changes less than it might seem: both Gemma
replications recorded `REFERENCE_SUPPORT_NOT_IDENTIFIED` at Gate 3C under the
calibrated coverage re-read, so $\Delta_R$ was not identified on either before
Gate 4 ran; withdrawing the headroom criterion opens nothing for them. What it
opens is the Qwens' path to Gate 3, where §13's unchanged machinery decides
whether a reference set exists.

## 4. What v6 measured, and how v7 reads it

Under §30's precedent every v6 quantity read in designing v7 is
`DEVELOPMENT_EVIDENCE` or `HISTORICAL_OUTCOME`, no v6 row is v7 confirmatory
evidence, and no v6 terminal status is read as a null result.

Three v6 records are the measurements v7 responds to, read after the fact:

- **`qwen3-4b`, Gate 2.75, m\* = 12.** `solo:B` 0.747; `pair:A+B` B-slot
  0.790; `pair:B+A` B-slot 0.891, between-topic variance 0.0645 over 192
  topics; A's own compliance under B 0.355 and 0.322 against a solo 0.706.
- **`qwen3-4b-instruct-2507`, Gate 2.75, m\* = 11.** `solo:B` 0.779;
  `pair:A+B` B-slot 0.875; `pair:B+A` B-slot 0.924; A under B 0.630 and 0.595
  against a solo 0.591. Two stand-in-dependent entries at 0.957 and 0.951,
  recorded and gating nothing under v6's A13.
- **`gemma-3n-e4b-it`, Gate 4, m\* = 9, base and class arms.** `solo:CL`
  0.958 on 24 topics against a calibrated solo of 0.686 — a split transfer of
  +0.27 on the one bound companion.

**What these say.** On both Qwens, composing B with A *raised* B's delivery by
0.10–0.15 while A's own delivery fell by 0.2–0.35. Read as v7 reads it, that
is $D(B \leftarrow A) \approx -0.1$ to $-0.15$ (a gain), $D(A \leftarrow B)
\approx +0.3$ (a loss), and a large asymmetry $\Lambda$ — every one of them an
identified primary estimand v6 stopped short of. What no v6 record can say is
$\Delta_R$: no Qwen replication reached Gate 3, so whether the matched
references deliver B at 0.6 (an excess for A would then be impossible and a
comparative advantage of $-0.3$ likely) or at 0.95 (a comparison with no room
in either direction) is unmeasured.

**What is fitted to v6, stated plainly:** nothing numerical. The compression
level is $1 - \text{SESOI}$, the allowance is the Wilson half-width at the
registered block count, the structural-zero rule reads exact boundaries. What
is *chosen* in response to v6 is the withdrawal itself, and §8 declares it.

## 5. The statistical argument

**Coherence.** The registered estimand is a within-block difference of cell
means; its estimator is the mean of per-block differences; its uncertainty is
a block bootstrap. None of that requires any cell mean to lie inside an
interval. A Bernoulli rate at 0 or 1 makes two things true and one false:

- *true:* the bootstrap cannot see that arm's sampling variability. A2's
  allowance is the standard remedy — the Wilson (score) bound at the unit
  count is the interval the design licenses for a proportion observed at a
  boundary, and it is applied to the contrast through the arm's weight, in
  the direction the boundary opens. At 384 blocks it is 0.0099, one-tenth of
  the SESOI and one-fifth of $\Delta_R$'s precision precondition. It is
  conservative and it is derived.
- *true:* the contrast's attainable range is asymmetric. A2's compression
  reading states which direction the other arm's level has closed and at what
  magnitude, from the same arithmetic the estimand is defined by. It is a
  qualification on the statement, not a change to the rule, because the rule
  — a bound of the decision interval against a registered threshold — is
  already correct in the open direction, and in the closed direction it is
  correct *and* explained by the arm level. (The one case a reader might
  worry about — L3c licensed when B is delivered under A at 0.92 — is a valid
  refutation of the pair-specific hypothesis: $A$ does not cost $B$ more than
  its matched companions because $A$ does not cost $B$ anything. The
  statement now says that.)
- *false:* that the contrast is undefined. At a structural zero A2 reads
  zero observed variance as the allowance interval $\pm h_n$, not as
  infinite precision: no direction, and an equivalence reading only by the
  registered rule on that interval.

**Why the structural zero is read and not vetoed (2026-08-28).** The draft
first registered a structural zero as licensing nothing. The boundary audit
(`dci1/reports/dci1v7/boundary_audit/`) found that this was not a
statistical safeguard and withdrew it, before adoption, on three grounds.
(i) *Validity.* At a shared boundary the allowance interval $\pm h_n$ is a
valid interval for the true contrast at $\geq 95\%$ by construction: each
arm's true rate lies within $h_n$ of the boundary with one-sided confidence
97.5% under the block-as-unit model, and the two sides of the interval fail
on disjoint events. In simulation it covered in 1,000 of 1,000 experiments
at every shared-boundary process tried. (ii) *Type I error for equivalence.*
An L3c read there while $|\Delta_R| \geq 0.10$ requires every one of 3,072
draws on every differenced cell to be perfect while one arm's true rate is
at most 0.90 — probability below $0.9^{384}$ — so the veto protected
against nothing. (iii) *Coherence.* The veto made a table with 3,072 of
3,072 perfect draws license *less* than a table with 3,071 of 3,072, which
the rule already read as L3c with `COMPOSED_CONTRAST_RANGE_COMPRESSED`.
What the veto did carry — that the composed set did not discriminate and
that Claim B, the registered estimand on the registered task distribution,
is bounded rather than measured — is carried instead by the status, the
sentence and §26's `NOT_MET`, which is unchanged. Lifting the veto can add
only equivalence-type readings: the interval is symmetric about zero, so no
directional level is reachable. No threshold moves.

**Why the paired bootstrap is the right resampling unit.** §14.1 registers the
block — a topic with its wording and order allocation — as the unit of
assignment, pairing and clustering, and §17.1 resamples blocks carrying every
cell mean of a drawn block, both configurations together. $A{+}B$ and
$B{+}R_j$ cells of one block are answers to the same question under the same
wordings, and the topic-level ICC measured on v5's Gate-4 rows was 0.35;
treating the arms as independent would overstate precision by roughly that
share of the topic variance. The probe and Gate 4 reuse the same construction
over topics, and the probe's contrasts are checked against the estimators'
algebraic forms on a synthetic table so the projection is a projection of the
registered quantity and not of a look-alike.

**What can still make the contrast non-identifiable.** In order of where it
is decided:

1. `REFERENCE_SUPPORT_NOT_IDENTIFIED` at Gate 3C (§13.15, §34 D6,
   irreversible): fewer than five families through $V(R)$ or fewer than three
   core references. $\Delta_R$, $\Delta_j$, $\Xi$ and the spectrum are
   `NOT_IDENTIFIED`; the base arm's estimands are not. Both v6 Gemmas ended
   here in substance. **Unchanged.**
2. `DIFFICULTY_SUPPORT_NOT_IDENTIFIED` (§12.6, §13.13): $\delta_{\text{diff}}$
   only. **Unchanged.**
3. A **structural zero** on the confirmatory blocks (A2, revised
   2026-08-28): every composed cell $\Delta_R$ reads at the same exact
   boundary. No directional classification; L3c by the allowance interval
   at the registered block count, carrying the status and the sentence.
   Projected at Gate 4 and recorded as `NOT_MET` on §26; never terminal.
4. `INSUFFICIENT_PRECISION` (§17.3): the realised half-width above 0.05.
   Equivalence and threshold statements withheld; direction still reported.
   **Unchanged.**
5. F6's vacuity gate (§17.4): when composition changes how often B can bind,
   the primary estimate is reported beside its vacuity-forced recomputation
   and a claim is licensed only when both license it. **Unchanged**, and it is
   the registered treatment of a ceiling produced by vacuous passes.

Nothing else. In particular a marginal composed rate at 0.03 or 0.97 is not on
this list, and a compressed direction is a qualification, not a
non-identification.

## 6. Selection leakage: the firewall, unchanged and enumerated

Composed outcomes — the probe's, Gate 4's, the confirmatory blocks' — may not
choose which reference is selected, the reference severities, $m^*$, $n^*$,
the instruction order, the model or configuration, or any other design
quantity. v7 changes none of the mechanisms that enforce it and removes one
thing composed outcomes *could* do in v6 (end the replication), so the set of
decisions a composed outcome can reach is **strictly smaller** than in v6:

| decision | fixed by | before any composed cell is read | guard |
|---|---|---|---|
| $n^*$, $m^*$ | §12.3 on solo curves, Gate 2 | yes | A13: `probe_disposition` refuses any severity but m\*; `assert_m_star_unmoved`; `effective_m_star` on every read |
| the qualified pool | §13.1–§13.6 at Gate 2.5 | yes | §13.11's closed schema; §33 check 8's name scan over both composed records |
| the reference set, severities, backups | §13.7–§13.10, §13.12 at Gate 3A/3B | yes — Gate 2.75 precedes Gate 3A and no reference exists when it runs | `assert_probe_reads_no_reference`; `probe_only` non-selectable by construction; `assert_no_substitution_path`; §34 D6's four refused rehabilitation paths |
| the admitted arm set | §13.15 at Gate 3C | yes | Gate 4 admits, drops and reorders nothing; a structural-zero projection drops no arm (A2) |
| instruction order | §8.4: both orders in every block | by construction | `assert_order_forms` |
| model / configuration | §6.1: four replications, never pooled | by construction | `assert_configuration_scope` |
| whether to generate | §34 D22, per replication, a function of stages 1–12 passing | yes | a Gate-4 projection is not a licence to withhold generation (A5's D22 text) |

The one *human* decision point a composed outcome can reach is an amendment,
and A4 makes that a signed, declared, append-only record that refuses §13.

## 7. §34: the registered open decisions

Twenty-six. D0–D18 are v5's, D19–D22, D24 and D25 are v6's, each carried
forward and requiring its own closure on v7's record with a `carried_from`
block; D27 is v7's. D23 and D26 are withdrawn (A5). `protocol/decisions`
blocks each dependent stage and each dependent function while one is open, and
`assert_transition_legal` refuses a stage with an open decision.

| id | question | derivation available |
|---|---|---|
| D0–D18 | v5's nineteen | v6's closures, carried |
| D19 | reachability repair alone, or plus new families | acceptance |
| D20 | does the probe spend §6.2's reserved composed set | `calibration_with_measured_transfer` |
| D21 | how many topics Gate 4's projection is taken on | acceptance: 24, as registered |
| D22 | what licenses confirmatory generation | `per_replication`; a projection is not a licence to withhold |
| D24 | where the stand-ins are registered | `probe_only_in_library` |
| D25 | the single-survivor statement | two registered sentences |
| **D27** | retain the probe as a recording stage | acceptance (A5) |

**A derivation is not a closure.** Each is recorded as a standing proposal in
`protocol/decisions` with its evidence, and each is `UNRESOLVED` until the
researcher records it in `dci1/reports/dci1v7/researcher_decisions.json`, with
its value, its evidence, who took it and when.
`dci1/reports/dci1v7/development/researcher_decisions_PROPOSAL.json` is a
proposal in that shape and is not the record.

## 8. Provenance, and the honest statement about fitting

v7's design was chosen after reading the **closed** v6 study. §32.2 requires
that a change adopted after a gate has run is declared as adopted *because*
that gate ran, and §32.1 names weakening a criterion so that a gate passes as
what a gate failure is not an occasion for. So, plainly:

**Three v6 replications terminated on the composed-headroom criterion, and A1
withdraws it because they did.** The withdrawal is not independent of that
outcome and this document does not present it as though it were. What makes
it adoptable is the argument of §5 — the criterion gated a marginal rate and
the estimand is a contrast — and the fact that its replacement reads no
threshold that was not already registered, gates nothing, and is applied by
one rule at three places whose first application precedes the freeze. It is
declared a **loosening** with respect to what ends a replication.

**Nothing numerical is fitted to v6.** The two numbers A2 reads are the SESOI
and the Wilson level, both v5's. The v6 probe values in §4 are quoted so a
reader can see what the rule would have recorded; they were not used to set
anything.

**The fourth v6 termination is a lifecycle defect, and A4 responds to it.**
`gemma-3n-e2b-it`'s `PREFREEZE_AUDIT_FAILURE` is correct under the rule it had
and is retained as a v6 outcome; the incident is
`dci1/reports/dci1v6/incidents/2026-08-27_prefreeze_protocol_hash.md`.

**What the measured v6 quantities do and do not say.** They say what composing
B with A did to B on two models at one operating point on 192 calibration
topics: it raised it. They do not say what the matched references would have
done, because none was selected. v7 is the prospective test, and per §30's
precedent retrospective behaviour on v6 is not prospective validation; v7 may
not claim any of A2's readings generalise.

Development evidence: `dci1/reports/dci1v6/closure.json` and the four v6
terminal reports (historical outcomes); the v6 `GATE_2_75_COMPOSED_PROBE` and
`GATE_4_COMPOSED_HEADROOM` records; `dci1/reports/dci1v7/READINESS.md`, which
carries the audit this document rests on. The machine-readable design is
`dci1/reports/dci1v7/reference_design_spec.json`, generated by
`dci1/tools/v7_reference_design_spec.py` from the registered code so that a
spec disagreeing with the implementation is not expressible; it reports
`DRAFT_NOT_ADOPTED` until the three researcher acts it names are on the
record.
