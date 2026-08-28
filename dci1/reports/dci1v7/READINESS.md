# DCI-1 v7: the composed contrast is estimated, not gated

*The audit that motivated v7, the statistical argument for it, and what it
does and does not resolve. Written 2026-08-27, after the closed v6 study had
been read in full and before any v7 row exists. Numbers are read from signed
v6 records; every one is cited to its record.*

---

## 1. What v6 did at Gate 2.75 and Gate 4, verified from the code

The request that produced v7 asked first for an independent verification of
what v6's composed-headroom logic actually does. Read from
`dci1/src/dci1v6/stages/composed_probe.py` and `run/gates_run.py` at commit
`76ae840`:

- **Gate 4** (`gate4_payload`) generated every registered cell type of the
  admitted arms on §6.2's 24 composed topics at `M_CAL = 4`, computed each
  cell × slot compliance, and raised `COMPOSED_HEADROOM_FAILURE` for **any**
  entry with `not (0.05 <= value <= 0.95)`. Every slot of every cell — the
  target's, the focal's, each companion's own compliance in its solo cell —
  was tested independently. No contrast was computed. No comparison between
  the A+B and R+B cells was made.
- **Gate 2.75** (`severity_verdict`, `entry_verdict`, `probe_disposition`)
  measured `solo:A`, `solo:B` and both orders of `pair:A+B` on the 192
  calibration topics at `M_CAL`, projected each *determinate* entry forward to
  Gate 4's sample size — half-width
  `z * sqrt(s2/24 + s2/192 + residual_sd^2)` with `s2` the entry's own
  between-topic variance and `residual_sd = 0.0142` under §34 D23/D26 — and
  raised `COMPOSED_HEADROOM_UNREACHABLE` when any projected interval left
  [0.05, 0.95]. Stand-in-dependent entries were judged against the band and
  recorded, gating nothing (A13, A17).

So the earlier audit's finding holds: **neither gate required `A+B ≈ R+B`**.
Both inspected each composed rate independently against an absolute band.
Nothing in either gate read the paired contrast the study estimates.

## 2. What that did to v6

All four replications are terminal on the evidence tree
(`dci1/reports/dci1v6/closure.json`, `CLOSURE.md`):

| replication | stage | status | the number |
|---|---|---|---|
| `qwen3-4b` | Gate 2.75, m\* = 12 | `COMPOSED_HEADROOM_UNREACHABLE` | `pair:B+A` B = 0.891 (s²_topic 0.0645, 192 topics), projected 0.779–1.002; **B solo 0.747** |
| `qwen3-4b-instruct-2507` | Gate 2.75, m\* = 11 | `COMPOSED_HEADROOM_UNREACHABLE` | `pair:A+B` B = 0.875 → 0.994; `pair:B+A` B = 0.924 → 1.024; **B solo 0.779** |
| `gemma-3n-e4b-it` | Gate 4, m\* = 9 | `COMPOSED_HEADROOM_FAILURE` | `solo:CL` = 0.958 (companion's own solo cell; calibrated solo 0.686) |
| `gemma-3n-e2b-it` | pre-freeze audit, m\* = 10 | `PREFREEZE_AUDIT_FAILURE` | Gate 4 passed; `protocol_hashes_agree` failed (A16/A17 edited the registered document), and `support_satisfied` failed (Gate 3C: `REFERENCE_SUPPORT_NOT_IDENTIFIED`) |

On both Qwens the treated arm showed a **delivery gain**: B's compliance rose
by 0.10–0.15 under A while A's own compliance fell by 0.2–0.35 (A under B:
0.355/0.322 from a solo 0.706 on `qwen3-4b`; 0.630/0.595 from 0.591 on the
2507 checkpoint). Read as the estimands read it, that is $D(B \leftarrow A)
< 0$, $D(A \leftarrow B) > 0$, and a large $\Lambda$ — three identified primary
estimands the study stopped short of. What no v6 record can say is $\Delta_R$,
because no Qwen replication reached Gate 3.

On both Gemmas, Gate 3C had already recorded `REFERENCE_SUPPORT_NOT_IDENTIFIED`
under V6-E04's calibrated coverage re-read, so $\Delta_R$ was unidentified on
both before Gate 4 ran. **Withdrawing the headroom criterion opens nothing for
the Gemmas.** It opens the Qwens' path to Gate 3, where §13's unchanged
machinery decides whether a reference set exists.
*(Superseded 2026-08-28 by A6/A8 — §9 below: a non-identified replication continues on its base and class arms; "opens nothing" conflated Δ_R's non-identification with the end of the replication.)*

## 3. Is the proposed change statistically coherent?

Yes, and the reason is the one the request gives. The registered estimand is

$$\Delta_R = \tfrac{1}{3}\textstyle\sum_j \mathbb{E}[\bar X_{B,\,B+R_j}] - \mathbb{E}[\bar X_{B,\,A+B}],$$

a within-block difference of cell means (§11.3), estimated by the mean of
per-block differences and bootstrapped by block (§14.1, §17.1). None of that
requires a cell mean to lie inside an interval. A Bernoulli rate at 0 or 1
does three specific things to a contrast, and v7 §13.14 names each:

1. **It hides that arm's sampling variability from the bootstrap.** The
   remedy is the score (Wilson) bound at the unit count — the interval the
   design already uses for a proportion (§13.4) — applied to the contrast
   through the arm's weight in the direction the boundary opens. At 384
   blocks it is 0.0099. Conservative; derived; small against the SESOI.
2. **It makes the attainable range asymmetric.** With B delivered under A at
   $a$ and under the reference mean at $\bar r$, $\Delta_R = \bar r - a \in
   [-a,\, 1-a] \cap [\bar r - 1,\, \bar r]$. An arm above $1 - \text{SESOI}$
   closes one direction at the SESOI by arithmetic. That is a fact about the
   *reading* of a verdict, not about its validity: L3c licensed with $a =
   0.92$ is a valid refutation of the pair-specific hypothesis — A does not
   cost B more than the references because A does not cost B anything — and
   the statement should say which. v7 records the compressed direction and
   the arm that closes it on the statement and changes no licensing rule.
3. **When every cell it differences is at the same exact boundary, it is a
   structural zero.** Zero variance is not infinite precision. v7 withholds
   every classification and every equivalence from such a member, which is
   the reading `RESEARCH_STATE.md` §4 already gives a saturated target.

The paired block bootstrap is the right resampling unit because the block is
the registered unit of assignment, pairing and clustering; the topic-level ICC
measured on v5's Gate-4 rows was 0.35, so treating arms as independent would
overstate precision by that share of the topic variance. Gate 4 and the probe
in v7 form their projections with the **same** functions and the same
one-index-draw construction, and the probe's contrasts are checked against
the estimators' algebraic forms on a synthetic table.

## 4. Conceptual problems the request did not name

1. **A v6 amendment is illegal under v6's own §32.** §32.3 freezes §13 from
   the first Gate-2.5 record and all four replications hold one; §32.1
   forbids weakening a criterion so that a gate passes, and three
   replications terminated on exactly this criterion; §28 makes a terminal
   status irreversible with no lifting path (A15 refuses "any §28 status").
   The request anticipated this. v7 is a superseding registration with its
   own evidence tree and seeds; v6's four verdicts stand.
2. **The fourth termination is a lifecycle hole, not a scientific verdict,
   and it would recur.** `gemma-3n-e2b-it` passed Gate 4 and terminated at
   the pre-freeze audit because A16 and A17 — both correct, both declared —
   edited the registered document after rows existed, and v6 had no way to
   bind a post-registration amendment (`supersede_registration` needs zero
   observations; `retire_apparatus_fault` needs zero rows). §32's own text
   describes an append-only register; nothing implemented it. v7 A4
   implements it (`amend_registration`, `document_binding`, a signed chain
   the audit and the freeze read) and makes §32.3 executable. Incident:
   `dci1/reports/dci1v6/incidents/2026-08-27_prefreeze_protocol_hash.md`.
3. **The Gemmas are not rescued by anything here.** Their Gate-3C
   non-identification is §34 D6, irreversible, and is a finding about
   reference supply on those models (V6-E04). A reader of the changelog who
   expected "remove the gate, four replications proceed" should expect two.
4. **A projection at Gate 4 is composed-outcome information before the
   confirmatory budget is spent, and a human can act on it.** No code path
   reads it, and the register now says a projection is not a licence to
   withhold generation (§34 D22's text). The one human decision point a
   composed outcome can reach is an amendment, which A4 makes a signed,
   declared record that refuses §13.
5. **Structural zeros are more likely on 24 topics than on 384**, so Gate
   4's projection is deliberately not a gate and drops no arm: dropping the
   core arm on a 24-topic exact boundary would be a design decision taken
   from a composed outcome, and the confirmatory blocks decide.
6. **The withdrawal is a loosening, and §32.1 is not decidable by code.**
   v7 declares it as one (preregistration §8) and the argument for its
   adoptability is §3 above, not the count of replications it lets through.
   The A4 record requires every future amendment to declare its direction.
   *(Superseded 2026-08-28 by A6/A8 — §9 below.)*

## 5. What v7 changes, executably (`protocol/revision.py`)

| id | change | check |
|---|---|---|
| V1 | `COMPOSED_HEADROOM_FAILURE` and `COMPOSED_HEADROOM_UNREACHABLE` withdrawn; no module can raise either | vocabulary + AST walk (the converse of A8) |
| V2 | `analysis/boundary.py`: structural zero, arm at boundary with Wilson allowance, compressed direction | behavioural on synthetic contrasts |
| V3 | Gate 2.75 records the paired contrasts at the frozen m\* and has one outcome | behavioural: a ceiling records and returns PASS; a second severity is refused |
| V4 | Gate 4 reads its rows as an observation table, projects every registered contrast, has one outcome | source + `GATE4_OUTCOME` |
| V5 | the analysis attaches the statuses, widens decision intervals, withholds classification from a structural zero, names $\Delta_R$'s direction | source + `delta_r_reading` on a structural zero |
| V6 | §26 restated on the estimand | signature of `methodological_success` |
| V7 | post-registration amendments bindable; §32.3 executable | `amend_registration`, `document_binding` exist and refuse §13 |
| V8 | no threshold moves | every band, caliper, SESOI, claim threshold and precondition equals v5's |
| V9 | the estimand layer is byte-identical to v6's (twelve modules; `support.methodological_success` the one named exception) | byte comparison |
| V10 | (2026-08-28, after the boundary audit) a structural zero is read on its allowance interval ±h_n rather than vetoing every classification: no direction by construction, L3c at 384 blocks, nothing at 24, with the status and `STRUCTURAL_ZERO_SENTENCE` | behavioural: ±h_n, L3c at `C.N_BLOCKS`, `[]` at 24, no direction, the sentence exists |

## 6. What remains non-identifiable, in order of where it is decided

`REFERENCE_SUPPORT_NOT_IDENTIFIED` (Gate 3C, irreversible);
`DIFFICULTY_SUPPORT_NOT_IDENTIFIED` (δ_diff only); a structural zero on the
confirmatory blocks (no classification; projected at Gate 4; `NOT_MET` on §26;
never terminal); `INSUFFICIENT_PRECISION` (§17.3; equivalence and threshold
statements withheld, direction still reported); F6's vacuity gate (§17.4). A
marginal composed rate at 0.03 or 0.97 is not on this list.

## 7. The state v7 is in

**Adopted 2026-08-28** (added after the paragraph below, which is retained as
written on 2026-08-27). The researcher's instruction of 2026-08-28 directed
that the draft, as revised by the boundary audit (V10), be adopted,
registered and executed as the prospective confirmatory study. The
twenty-six §34 decisions and the three §33 items are closed on
`reports/dci1v7/researcher_decisions.json` — twenty-five re-taken at v6's
adopted values with `carried_from` blocks, D27 on v7's own evidence — both
governed documents declare `ADOPTED`, `reference_design_spec.json` derives
`ADOPTED`, and `plan_registration` reports `can_register`. Zero v7
behavioural rows existed at that moment. Registration, execution and the
per-replication outcomes are recorded in `RESEARCH_STATE.md` §4am and
`CHANGES_SCIENTIFIC.md` (2026-08-28, adoption entry).

*As written 2026-08-27:* `DRAFT_NOT_ADOPTED`. Both governed documents declare it, the decision record
does not exist, and `plan_registration` reports `DRAFT_DOCUMENT`. Adoption is
the researcher's: close §34's twenty-six decisions on
`reports/dci1v7/researcher_decisions.json` (a proposal in that shape is at
`development/researcher_decisions_PROPOSAL.json`; twenty-five carry v6's
values and D27 is v7's), change the preregistration's status line, regenerate
the spec. Zero v7 rows exist. v7 re-runs its pre-composed stages under its
own seed domain rather than carrying v6's records: the isolation guards are
load-bearing and the pre-composed evidence is cheap against the confirmatory
budget; a carry mechanism was considered and not built.

**Compute, unchanged from v6.** Five arms, four models, 56 cells, 1,174,080
generations at the registered design; Gate 2.75 costs 12,096 rows per
replication and Gate 4 up to 5,376.

## 8. What was verified before writing this

`dci1/tests_v7/`: the copied v6 suite ported to v7 (every test that asserted
the withdrawn verdict now asserts its absence and a raise-path-free package),
plus `test_boundary.py`, `test_composed_contrast.py`,
`test_amendment_chain.py` and a rewritten `test_composed_probe.py`. The
synthetic nineteen-stage walk and every registered branch scenario run under
the new rule, including the v6 Qwen case (`probe_records_a_ceiling_on_the_
treated_arm`) and the v5/v6 Gate-4 case (`gate4_records_a_boundary`), both of
which now pass through to the pre-freeze audit. The v6 suite is untouched and
green (613 passed).

**Self-audit of the port (2026-08-28).** The v6 -> v7 diff was re-read file by
file against the intended change, and every consumer of a withdrawn symbol was
grepped for. Four defects were found and fixed before anything ran on a
model: the registration manifest had bound an on-disk `amendments.at_signing`
list that `ensure_registration`'s rebuild-and-compare would have rejected after
the first amendment (it now binds only the rule and the chain location); a
structural zero on `Delta_R` was read by `claims.l3_vacuity_agrees` as a
vacuity disagreement instead of a no-classification reading; two `except
Exception` sites in `analysis/boundary.py` and `stages/composed_contrast.py`
would have turned a defect in those modules into "no boundary reading" (they
now catch only the table's own `IntegrityError` / `ProtocolError`); and
`revision._package_modules` skipped a module that failed to import, which
would have left V1's raise-path scan with a hole. A dead helper, a stale skip
on the A16 evidence test, `tests_v7` missing from `pyproject`'s testpaths, and
three copied `reports/dci1v7/...` paths that never existed were also removed.
On the final tree: `tests_v7` 641 passed, `tests_v6` 613 passed, the root
suite 131 passed; the producer/consumer contract regenerates at 169 fields
and 0 defects; the execution-path audit regenerates at 74 of 74 rules
agreeing over 19 scenarios; `reference_design_spec.json` regenerates
byte-identical; ruff
shows no finding in the v7 trees that the v6 trees do not also carry (the
repository is not ruff-clean, and no type checker is configured). Nothing
here is committed and the registration remains `DRAFT_NOT_ADOPTED`.

**Boundary audit (2026-08-28).** Before adoption, §13.14's machinery was
audited statistically rather than for implementation fidelity:
`dci1/reports/dci1v7/boundary_audit/DECISION_MEMO.md`, produced by
`dci1/tools/v7_boundary_audit.py` running the production interval procedure
on 39,000 simulated paired experiments. The Wilson allowance is kept (it is
what holds family coverage at nominal when a cell sits at an exact boundary);
the structural-zero veto is withdrawn as V10 (a structural zero is read on
its allowance interval — no direction by construction, L3c at 384 blocks,
nothing at 24 — with the status and a registered sentence); Gate 4 is shown
non-adaptive consumer by consumer, and the freeze now binds m\* through the
checked Gate 2 = Gate 2.75 equality; the sign convention is verified on
deterministic tables. `CHANGES_SCIENTIFIC.md` 2026-08-28.

## 9. After the run: A6–A8 (2026-08-28)

Everything above was written before v7 ran and is retained as written. Two
of its readings are **superseded** by the in-place amendments of 2026-08-28
(preregistration A6–A8; `CHANGES_SCIENTIFIC.md` "v7 amended in place";
`RESEARCH_STATE.md` §4an):

- §2's table and §4 item 3 ("the Gemmas are not rescued by anything here;
  their Gate-3C non-identification is §34 D6, irreversible") conflated the
  irreversibility of Δ_R's non-identification with the end of the
  replication. D6 registers that a non-identified replication *continues* on
  its surviving arms; what stopped it was the pre-freeze audit's
  `support_satisfied` check — listed here as non-waivable in §2's table —
  which required §13.15 to have been *met* and which A6 withdraws for the
  registered invariant.
- §6's list is unchanged in what is non-identifiable, and changed in what it
  costs: under A7 a lost §12.6 spectrum condition (C2, C4) is
  `DIFFICULTY_SUPPORT_NOT_IDENTIFIED` and costs the spectrum arm alone; the
  core arm and Δ_R stand when §13.8, §13.7 and §13.15 hold. All four v7
  replications lost C4 alone.

The four v7 terminal reports stand; nothing here re-verdicts them.

