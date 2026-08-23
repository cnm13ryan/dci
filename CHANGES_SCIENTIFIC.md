# Scientifically consequential changes

Not a commit log. An entry belongs here only when a change alters what a number
means: experimental design, prompts, instruction wordings, order or load,
decoding, caps, seeds, verifiers, parsers, answer extraction, metrics, estimators
or interval code, or the admission rules that decide which data an analysis reads.

Refactors, renames, tests, tooling and documentation do not get an entry unless
they change one of those.

Newest first. Started 2026-08-13; earlier history is in `git log`, the per-round
reports under `exploratory/`, and `docs/migration_ledger.csv`.

---

## 2026-08-23 — v5 pre-data accounting amendment: the registered budget contradicted §19's pilot

**Standing.** `dci1/reports/dci1v5/amendment_register.md` entry **A2**.
Registration `70608e5d…` (commit `5e35ca6`) is superseded by
`b040b343f626f095dd8a352b6b0fab9b7db87b797d82c843831783550ab1d106`
(commit `cd4b1b1`), together with the `PROTOCOL_REGISTERED` and
`QUALIFIED` records of all four replications — all retained, none deleted.
**No v5 model response exists**, so nothing is invalidated: `QUALIFIED` reads
no behavioural rate by construction (§19).

**What was wrong.** `design/budget.py` costed §19's procedural pilot as
`12 topics × 4 draws × 5` = 240. §19 registers the pilot as "the full 56-cell
plan, both orders, and the registered wording allocation … with $M = 4$" —
`12 × 4 × 56` = **2,688**. The literal `5` is the base arm's cell count: the
term was written as though the whole calibration burden were arm-independent,
which its other three terms are and the pilot is not.
`run/qualification_run.pilot_payload` always built the full plan, so **the
registered design was never wrong and the arithmetic over it was**.

| Term | Registered | Corrected |
|---|---:|---:|
| §19 pilot, per model | 240 | **2,688** |
| calibration, per model | 100,992 | **103,440** |
| per model | 283,776 | **286,224** |
| **study total** | **1,135,104** | **1,144,896** |

*What it changes about the meaning of a number.* Nothing about any measured
quantity — no arm, cell, block, draw, topic, severity, threshold, estimand or
rule moves, and the D1 decision (`four_models_56_cells`) is untouched. What
changes is the registered *cost*, upward by 0.86%, and the D1 packet's three
non-adopted options are recosted with it. Their ranking does not change.

**Two things tightened rather than merely fixed.** `calibration_burden` now
takes the cell count, so the pilot term follows the arm set and the previous
signature's blind spot is gone; and the pilot budget is now asserted in tests
*against what the runner builds* rather than against a literal, so the two
cannot drift apart again. The `supersede_registration` guard also moved: it
refused any stage record past stage 1, which would have made this correction
impossible after qualification. It now refuses at `GATE_0_APPARATUS`, the first
stage that puts a model response on disk — the boundary it was reaching for.

**Comparability.** v4r4 evidence untouched. The researcher-decision record
moved from `a5ec3986…` to `b3fd9185…`: one derived `consequences` line of D1
quoted the old total. Every closure's `value`, `decided_by`, `decided_on` and
`evidence` is unchanged, as are U2 = A2 and P1 = confirmed.

---

## 2026-08-23 — v5 pre-data engineering amendment: three defects that made the registered study unexecutable, and a superseded registration

**Standing.** The registration signed at manifest
`2960a1fc44f036abd4729f7628095475018672adfac609bb2244a8763ba00ded` (producing
commit `f895646`) is **superseded** by
`70608e5d5880c6ed2b8bbea1379b47061f60ea3f0705c374d0df581bc39bda2c` (producing commit
`5e35ca6`), which carries a stage-1 record for all four registered models —
the first time that has been possible. The superseded one is retained in full,
not deleted:
`dci1/evidence/dci1v5/registration/superseded/2960a1fc…/` holds the manifest
and the supersession record, and each replication's stage-1 record is retained
under its own `superseded/2960a1fc…/`. **No v5 observation existed under it and
none exists now**, so nothing is invalidated and no number moves — the whole
point of doing this before Stage 2 rather than after.

**Why an entry at all.** None of the three touches a threshold, an estimand, an
arm, a prompt, a wording, a verifier, a seed, a cap, a decoding policy, an
estimator or a reference-selection rule. Every registered scientific value is
byte-identical. They get an entry because the third one changes what a *row*
records about its own provenance, and because superseding a signed registration
is exactly the kind of event this file exists to make findable.

**V5-E1 — three of four registered models could never enter `QUALIFIED`.**
`run/registration_run.registration_payload` called
`manifest.sign_registration` unconditionally, which does `write_json_once` on
the **study-level** manifest, while `engine/transitions.assert_predecessor_passed`
requires a **per-model** stage-1 record. So the second replication's Stage 1
raised `IntegrityError` and `gemma-3n-e4b-it`, `qwen3-4b` and
`qwen3-4b-instruct-2507` had no legal path into the lifecycle. Now
`manifest.ensure_registration` signs on the first call and, on every later one,
verifies the signature, **rebuilds the manifest from the running code and
compares by hash**, and requires the same producing commit. D1's four-model
design was unreachable in practice; it is reachable now.

**V5-E2 — the pinned backend was unreachable for four of the five generating
stages.** `GATE_0_APPARATUS`, `REGIME_SCREEN`, `GATE_2_FOCAL_CALIBRATION` and
`GATE_4_COMPOSED_HEADROOM` each read `generate = generate or fake_backend(...)`.
That is unconditional and admits no override — `run/execute.run_backend` was
reachable only from `CONFIRMATORY_GENERATION` — and `run/cli.py`, the only
production entry point, passes no `generate`. **The documented way to run Gate 0
would have signed fabricated text into the registered evidence tree**, and
nothing downstream refuses a synthetic row in the registered namespace.
`execute.resolve_generate` now decides: in the registered namespace `generate`
must be absent and resolves to the pinned backend, and an injected callable is
refused outright; the deterministic stand-in is built only in the synthetic
namespace. This is the guard `assert_synthetic_only` already applied to
`topic_limit` and `block_limit`, extended to the larger substitution it had
been left off.

*What it changes about the meaning of a number.* Nothing retrospectively — no
row exists. Prospectively it is the difference between a Gate 1, Gate 2 and
Gate 4 measured on the registered model and one measured on a fixture.

**V5-E3 — `synthetic` said how the runner was called, not what wrote the text.**
`run/execute.py` stamped `"synthetic": generate is not None`. Combined with
V5-E2 that made every row of those four stages synthetic *by definition*, and
it also meant a real backend injected into one of them would produce rows
stamped synthetic. The flag is now taken from the generator's own provenance,
and `fake_backend` stamps each raw row so the flag survives a resumed run.
`CLASSIFICATION` moved from `DCI-1 PROTOCOL v5 (DRAFTED, NOT ADOPTED, NOT
FROZEN)` — which had not moved at adoption, so the first signed manifest
carried a label contradicting its own adoption block — to `DCI-1 PROTOCOL v5
(ADOPTED AND REGISTERED, NOT FROZEN)`. The old string is retained in
`SUPERSEDED_CLASSIFICATIONS`, because records under the superseded registration
carry it.

**Comparability.** v4r4 evidence is untouched. The superseded registration and
the new one bind identical scientific content; they differ in producing commit,
in `classification`, and in the new one naming what it supersedes. Records under
the superseded registration are retained and are *not* evidence for anything —
there are none past stage 1.

`dci1/tests_v5/test_amendment_pre_data.py` holds fifteen tests, one per failure
mode, including a static check that no runner reintroduces the `or
fake_backend(...)` shape and a four-model registration walk — the harness walks
one model, which is why none of this was caught.

---

## 2026-08-23 — v5 adopted: the remaining fifteen §34 decisions, U2, P1, and a construct floor whose denominator was wrong

**Standing.** v5 is **adopted and registered**. All nineteen §34 decisions
carry a value, U2 is resolved at A2, P1 is confirmed,
`manifest.signing_blockers()` returns `[]`, and the registration manifest is
signed. **No v5 observation exists**: no model has been loaded, no prompt
generated, no calibration measurement taken, no gate run on model output. No
existing number moves, because there are none.

[`dci1/reports/dci1v5/researcher_decisions.json`](dci1/reports/dci1v5/researcher_decisions.json) ·
[`dci1/reports/dci1v5/v5_adoption_checklist.md`](dci1/reports/dci1v5/v5_adoption_checklist.md)

**D17 — a construct floor on $m^*$: $\kappa^{B}(m^{*}) \le 0.50$.** Against
the standing proposal, which registered no floor. §12.3 selects the focal
severity on *compliance*, which says nothing about whether $B$ is still the
construct it is named after; the floor refuses a selected $m^*$ at which more
than half of unconstrained answers already satisfy $B$. The refusal reads the
**point** estimate; the Wilson upper bound is reported beside it and a new
identification status, `CONSTRUCT_FLOOR_MARGINAL`, is recorded when the
interval straddles the threshold. A selected $m^*$ that satisfies the
compliance band and fails the floor ends the replication at
`FOCAL_RANGE_EXHAUSTED` **before any confirmatory generation**.

*What it changes about the meaning of a future number.* A $D(B \leftarrow A)$
measured at a severity where $B$ does nothing was previously admissible with a
limitation attached; it is now not measurable at all. The trade is registered
and accepted: the study would rather report that no honest operating point
exists for a model than report an effect measured against an instruction that
does nothing. On the development curve the floor admits $m^* \le 12$ and
refuses $m^* \ge 13$; all four v4r4 operating points (10, 10, 12, 10) survive
it, so it excludes the region v5's grid extension opened and does not
retrospectively invalidate the predecessor's severities.

*Where the number lives.* Not in the code. `stages/construct_strength.py`
carries no threshold; the quantity, the value, the semantics and the derivation
are fields of the D17 closure in `researcher_decisions.json`, read by
`registered_floor()` and bound into the manifest by hash. `signing_blockers()`
reports `FLOOR_NOT_SPECIFIED` if a `floor` closure ever arrives without them.

**The estimator defect closing D17 surfaced — the consequential half of this
entry.** The threshold was derived from $\kappa^{B}$ measured on **load-zero**
answers. Gate 2's registered `chance` rate is computed over every row where the
severity was *absent*, which in the focal grid includes the $B$-solo cells at
the other seven severities — answers written under a stated length budget,
which satisfy a looser budget far more often than an unconstrained answer does.
Applying the threshold to that rate would have been a threshold calibrated on
one estimator and applied to another under the same name.

`execute.cell_rates` gained an `arm` filter and `instance_rates` an optional
`unconstrained_arm`; Gate 2 now computes both rates and records both
(`load_zero_chance_curves` beside `chance_curves`, with
`n_topics_load_zero`), and `assert_construct_floor` reads the load-zero curve.
**Every other chance quantity is untouched and keeps the denominator it was
defined with** — §13.6's $\kappa(R \mid B)$ is deliberately measured *under*
$B$, and changing it would have altered what every reference admission means.
Nothing retrospective is affected: no v5 chance rate has ever been computed.

*A fixture that could not have caught it.* The synthetic harness gave
$\kappa^{B}$ no curve at all — flat at 0.67 across every severity — because it
conflated "B stated and scripted to fail" with "B not stated", so the same
answer shape served both. It now draws an unconstrained answer's longest word
from a length distribution shaped after the measured development curve, and
scripts a $B$-failing row as one word past its stated budget. The walk's
$\kappa^{B}$ now runs 0.000 at $m = 7$ to 0.823 at $m = 14$. **These are
fixture numbers and nothing reads them as evidence**; what they buy is a
harness in which the floor can both pass and refuse.

**U2 — §11.8's tier-indicator secondary is adopted at A2.** $\alpha_f$ ranges
over the three **core** families and a Tier-2 point sits at the unweighted mean
core intercept plus $\gamma$, so the fit is five parameters over twelve points
and full rank. As written the section did not identify the fit at all, and the
four admissible repairs estimate different $\gamma$s — which is why it was a
researcher decision. `gamma_tier` now means *the Tier-2 offset from the
difficulty line the three core families define, at equal weight over them*.
A1 is never constructed, A3 is never constructed, and A4 remains constructed
and **non-adopted**: `TierFit.adopted` reports it and
`spectrum.assert_adopted_formulation` refuses it on any reporting path. Nothing
primary moves — sampling, reference selection, the arm set and every primary
claim are unchanged, and $\gamma$ licenses no claim level.

**D1 — the registered design: five arms, four models, 56 cells, 384 blocks,
$M = 8$; 1,144,896 generations (1,135,104 as first registered; see the 2026-08-23 accounting amendment).** The near-form arm is now *registered* rather
than merely permitted, so R1's only mitigation is in the design and the strong
L3c is reachable. The budget derivation moved out of `tools/v5_compute_budget.py`
into `dci1v5.design.budget`, because the manifest binds it and a manifest cannot
import a tool: the figure the signature carries is one the code reproduces.

**D4 — all eight Tier-1 markers, with four accepted limitations.** No marker
moves. The limitations — `though`'s near-synonymy with `however` and its two
syntactic frames, `namely`'s possible appositive interaction with word length,
`overall`'s natural rate, and the vocabulary-wide spread in how unnatural the
forced production is — are registered in
`verifiers.constraints.D4_ACCEPTED_LIMITATIONS`, bound into the manifest, and
reported alongside `REFERENCE_POOL_SAME_FORM` on every L3 statement. A
**population hash** over the eight families, words, roles, statistic ids,
ladders and reserves makes a post-adoption substitution detectable rather than
merely forbidden.

**The remaining eleven, and P1.** D0 `adopt`, D2 `no_load_three`, D5
`lexicographic`, D7 `0.90`, D8 `0.75`, D9 `unavailable`, D10 `one_companion`,
D11 `carry`, D12 `direction_and_sesoi_only`, D13 `primary_tier`, D14
`iota_primary`, D15 `both_transfer` — each at the document's own standing
proposal. Two carry a recorded objection that the closure does **not** answer:
R13 against D7's 0.90 and R2 against D15's transfer. P1's corrected §7.10
wording is confirmed; nothing executable changed, and Tier 3 was **not** made
spectrum-eligible.

**Red-team status.** R1 resolved by D18, R11 by D16, R14 by D17, R16 by D6.
**R5 is not resolved and no rule will resolve it**: $\kappa^{B}$ is measured
under $B$, so the reference set is a function of how each model writes under
its own $B$ at its own $m^*$, and $\Delta_R$'s meaning is not exchangeable
across models. It is an accepted permanent limitation, reported separately from
the blocking findings, and it is why no cross-model scalar carries a claim.

**Comparability.** Nothing in v4r4, v4r3, v3 or v2 is affected. No v5 number
existed before this change and none exists after it.

---

## 2026-08-22 — four §34 decisions taken, and the 96 Calibration-B questions authored

**Standing.** v5 is still **drafted, not adopted**. No v5 stage record exists
under `dci1/evidence/dci1v5/`, no v5 topic has been consumed, no model has
generated a v5 response, and the registration manifest still refuses to be
signed. **What changed is that four of §34's nineteen decisions are now
closed** — by the researcher, on the record — and two of them went against the
preregistration's own standing proposal. No existing number moves, because
there are none: nothing in this repository has ever produced a v5 observation.

[`dci1/reports/dci1v5/researcher_decisions.json`](dci1/reports/dci1v5/researcher_decisions.json) ·
[`dci1/reports/dci1v5/v5_adoption_checklist.md`](dci1/reports/dci1v5/v5_adoption_checklist.md)

**D18 — the near-form arm is a precondition of the STRONG L3c.** Against the
standing proposal. L3c now carries a registered `claim_scope`: `strong` — *no
pair-specific excess*, the source memo's refutation verdict — requires the
near-form arm to have run and produced a $\Delta_{\text{near}}$ interval;
without the arm the scope is `same_form_only` and the statement licenses only
*no excess relative to same-form exact-count companions*.
`claims.assert_l3c_scope` checks the invariant on the built statement, so the
strong conclusion is **unreachable** without the arm rather than qualified.
A new identification status, `L3C_STRONG_CONCLUSION_WITHHELD`, records the
absence on the record.

*What it changes about the meaning of a future number:* an L3c emitted by a
replication without the near-form arm was previously the memo's refutation
verdict with a sentence attached. It is now a different, narrower claim with a
different name. Nothing retrospective is affected — no v5 L3c has ever been
emitted — but the 47-cell compute option in D1 is no longer a cheaper version
of the same study, and `d1_arm_compute_decision.md` says so.

**D16 — Calibration-B measures the complete carried population.** Against the
standing proposal, which restricted it to Calibration-A's survivors. §13.7
becomes a test of the candidate landscape's stability rather than a
re-confirmation of a set already selected once. About 35,000 further
generations per replication.

*Consequence for the run layer:* at that volume an accidental repeat is
expensive, so a row's reuse key is now its **complete scientific identity** —
study, protocol identity, stage, decoding policy, model revision, topic,
**split**, block, cell, constituents, wording, prompt and seed. The split is in
the key explicitly, not by consequence of the prompts differing, so no
Calibration-A generation can ever satisfy a Calibration-B row. Generation and
scoring have separate keys: rescoring happens from the text on every pass, so a
verifier change invalidates every verdict without regenerating a token. The
previous key was (row id, prompt hash, seed), which would have reused across a
changed completion cap, a changed model revision and a changed protocol
identity.

**D6 — an unbuildable reference set is an identification status, and the
non-identification is irreversible.** As proposed, plus the half the proposal
did not state. The reference-dependent estimand set is **derived** from §15's
registered families by one rule (`protocol/identification.py`): 48 of the 70
registered members, including $\Delta_R$, $\Xi$, $\delta_{\text{difficulty}}$,
all of F2, F3, F4, F7, F8, the nine F6 contrasts against a reference and
$\text{Ord}_{\bar R}$. The 22 that survive include $D(B{\leftarrow}A)$,
$D(A{\leftarrow}B)$, $\Lambda$, $\Delta_{\text{near}}$ and
$\Delta_{\text{broad}}$. Gate 3C writes the set, the freeze carries it, and
`assert_not_rehabilitated` refuses four named paths — a later gate, a frozen
backup, the broad-class control, and an observed composed outcome read as
evidence the pool was adequate after all.

*What this fixes:* `analysis_run._licensed` blocked five members under
`REFERENCE_SUPPORT_NOT_IDENTIFIED`. The other 43 were attempted, produced no
vector, and were recorded `not_computable` — "the design was never asked"
rather than "§34 D6's verdict". The final report is now checked against the
frozen set.

**D3 — the 96 Calibration-B questions exist.**
`dci1/src/dci1v5/topics/data/calibration_b_v5.json`: 96 questions, eight per
subject area, deterministic ids, frozen ordering, content hash, disjoint from
all five other topic sets in **both** id and question text. Authored on
2026-08-22 — before any v5 Calibration-A measurement and before any v5
selection outcome existed, so no question could have been written to be kind to
a candidate that had already survived; `topics/calibration_b.PROVENANCE` states
that in checkable terms. §13.7's two-split machinery is executable for the
first time, and `load_bank()` now returns a complete bank.

*A defect this exposed:* §6.2's one mechanically-checkable authoring rule — no
form requirement in the question text — read `question["text"]`, and the schema
field is `question`. It had been scanning the empty string for every topic in
the bank and had never rejected anything.

**Comparability.** Nothing to compare. No v5 observation exists, no v4r4 number
is touched, and v4r4's evidence manifest verifies unchanged. The four closures
change what *future* v5 numbers will mean, which is why they are here.

---

## 2026-08-22 — the v5 lifecycle executed end to end on synthetic fixtures, and eleven defects that only appear when a stage runs

**Standing unchanged.** v5 is still **drafted, not adopted**. No v5 stage
record exists under `dci1/evidence/dci1v5/`, no Calibration-B question has been
authored, no v5 topic has been consumed, no model has generated a v5 response,
and §34's nineteen decisions are all `UNRESOLVED`. No number anywhere in this
repository moves. v4r4's evidence manifest verifies unchanged.

[`dci1/reports/dci1v5/v5_implementation_status.md`](dci1/reports/dci1v5/v5_implementation_status.md) ·
[`dci1/reports/dci1v5/v5_reconciliation.md`](dci1/reports/dci1v5/v5_reconciliation.md) ·
[`dci1/reports/dci1v5/v5_producer_consumer.md`](dci1/reports/dci1v5/v5_producer_consumer.md)

**What changed.** The `run/` layer now exists — eighteen stage runners on one
driver — and an engineering harness walks all eighteen with no model, in the
`synthetic` namespace, under a temporary evidence root. Walking it found
eleven defects. **Nine of them are in code that would have produced or read
v5's numbers**, which is why this is here and not in the commit log. None
changes an existing result, because there are no v5 results; each would have
changed a future one.

**1. §9.1's absent verdicts were written with no slot.** `generate_and_score`
labelled a score from the cell's *stated* constituents, so every verdict on an
instrument the prompt did not state was written `slot: null`. Two consequences.
κ(R|B) — §13.6's entire input, and the reason v5 scores every instance on every
row — is indexed by slot and was therefore unreadable through
`ObservationTable`. And §25's load-0 cell, where **every** verdict is absent by
§9.1, produced one indistinguishable key per block, so its chance rates
collapsed onto each other. The slot now comes from the replication's slot map,
which is the binding that defines what a slot is; an instance the map does not
bind falls back to its own label.

**2. `ObservationTable` tested presence before the arm, so §25's chance
observations were never indexed as chance.** A load-0 verdict is an absent
verdict by §9.1 *and* a chance observation by §25; the two are different
quantities read off different cells, and the arm is what separates them.
Testing `present` first routed every one of them into the κ index. The
difficulty coordinate is `(solo − chance)/(1 − chance)`, so nothing that reads
chance could have been formed on real rows.

**3. A composed cell's companion was read off the row's whole score list.**
With §9.1 scoring every registered instrument on every row, that list holds one
entry per instrument, so the "companion" became whichever instrument happened
to sort first — naming an unstated instrument as the companion and collapsing
distinct composed cells onto one index key. The companion is now the cell's
other **stated** constituent.

**4. `delta_difficulty` was registered and never computed.** It is a member of
F1, §11.7 defines its estimator, §17.2 defines its refit-per-replicate
bootstrap, and `bootstrap_family` already accepted a callable member for
exactly this purpose — and nothing built the `SpectrumInput` or called it. Two
consequences: the quantity was absent from the analysis, and F1's studentised
maximum-modulus critical value was taken over **five members instead of six**,
so every F1 interval was narrower than §15 registers.

**5. §20 names `Delta_R` as not computable in the masked phase and the code
computed it.** `MASKED_PHASE_FORBIDDEN_MEMBERS` listed `delta_difficulty` and
the fit's coefficients but not `Delta_R`, so the masked record carried an
estimate of the study's primary quantity formed against a permuted assignment
of companions — the one number the mask exists to withhold. Added, and the
withheld members are now recorded on the masked record by name.

**6. `assert_delta_difficulty_not_masked` read a key no estimate record
carries.** It scanned `result["families"]`; the record's shape is
`configurations` / `cross_configuration`. The guard ran over an empty dict on
every masked run and could not fail. It now reads the record's own shape,
including the interval families, and it is what caught defect 5 staying fixed.

**7. §20's masked-view cleanliness rule was never applied to the artifact.**
`assert_masked_view_clean` existed and no caller invoked it. It is now on the
path that writes the masked view.

**8. `MASKED_VIEW_EXCLUDED_FIELDS` excluded `arm`, which is not
companion-identifying, and the exclusion made the masked analysis
unconstructable.** The mask permutes labels *within* an (outcome,
configuration, block) group, and every composed member of such a group carries
the same `arm`; the field is constant across everything the permutation could
have swapped, so it narrows the true companion not at all. Meanwhile the masked
analysis cannot tell §25's load-0 cell from a solo cell without it. `arm`,
`present`, `draws` and `processing_failures` now travel with the masked view;
`cell_id` and the true `companion_slot` do not, and the cell's identity is
carried as a pseudonym derived under the sealed mask key. The integration test
asserts the constancy property over the written artifact rather than leaving
the argument in prose.

**9. §31's result table emitted six of its twenty-one fields**, and
`_intervals` computed the standard error and the marginal bounds and then
discarded them. Every §31 field is now filled from a signed record: the
difficulty coordinate and the reference-pool tier from the freeze, the bounds
and the standard error from the bootstrap, the cell counts from the
confirmatory record, the variance decomposition from the freeze's own
`variance_reestimate` with its source named, and the achieved detectable
effect as §16.3's reading of the realised simultaneous half-width, with the
derivation travelling on the row. `iota_a` and `solo_compliance_a` were
declared as read by Gate 5 and were not read; they are now bound.

**10. §33 check 8 read a declaration of absence as the thing it forbids.** The
check scans a Gate-4 record for a field naming an outcome-driven selection, and
Gate 4 carried `no_substitution_after_failure` — §13.14's refusal, in prose.
Declarations now live in one `declared_refusals` block that the scan skips and
the check **requires**: omitting the refusal used to pass and now fails.

**11. §33 check 15 had no producer and reported `UNRESOLVED` forever.** It
scans the v5 artifact texts and every caller passed none. `collect_artifact_texts`
now supplies them from a declaration the check itself owns, so check 15 is
discharged at `PREFREEZE_AUDIT` as §33 states. Only check 14 — which reads the
final-report table — is deferred, and `run/final_report_checks.py` discharges it
at `FINAL_REPORT` along with twelve traceability checks that only become
checkable once the table exists.

**Comparability.** Nothing to compare: no v5 artifact existed before this pass
and none exists after it that is not synthetic. v4r4 is untouched and
`tools/v4r4_evidence_manifest.py --verify` reports `OK`, 0 missing, 0 changed.

**What the synthetic walk does and does not say.** It says the v5 execution
plumbing runs end to end: eighteen signed stage records, a design derived from
an admitted arm set, a complete confirmatory draw matrix, a sealed mask, a
one-shot unmask and a §31 table every field of which traces to a record. It
says **nothing** about whether v5's matching procedure will work prospectively
on a real model. The fixtures are engineered to be satisfiable; that is what
makes them useful for finding plumbing defects and useless as evidence.

---

## 2026-08-22 — DCI-1 v5 implemented in its own namespace, and three latent defects in carried code found by running it

**Standing unchanged.** v5 is still **drafted, not adopted**. No v5 stage
record exists, no topic has been authored, no instrument has been measured,
and no number in this repository moves. What changed is that the protocol now
has an implementation — `dci1/src/dci1v5/`, `dci1/tests_v5/` — whose
open-decision registry makes the draft state executable: §34's nineteen
decisions are `UNRESOLVED`, `PROTOCOL_REGISTERED` depends on all of them, and
no v5 stage can run.

[`dci1/reports/dci1v5/v5_implementation_status.md`](dci1/reports/dci1v5/v5_implementation_status.md) ·
[`dci1/reports/dci1v5/v5_reconciliation.md`](dci1/reports/dci1v5/v5_reconciliation.md)

**Why this belongs here rather than in the commit log.** Three of the changes
are to *carried* verifier machinery, and one of them is a defect that would
have produced a scientific finding where there was a construction fault.

**1. `joint_witness` satisfied only the first exact-count constraint of a
pair, and built an exact sentence count as loose terminators.** Neither
mattered in v4r4, whose library held one exact-count reference family (`CX1`)
and no sentence-exact family. In v5 both are ordinary: a realisable pair can
carry two exact counts, and `XC3` is an exact sentence count. Run unfixed over
v5's population the carried suite reported **2,016 non-entailment failures**,
every one of which was a witness the constructor built wrongly rather than a
pair whose obligation cannot be discharged. Generalised, the suite discharges
**20,332 realisable pairs with zero joint-satisfiability and zero
non-entailment failures**. *Affected results: none.* v4r4's suite ran over
v4r4's population, where the two paths are unreachable, and its Gate-1
evidence stands.

**2. §7.7's realistic-witness rule is narrower than the preregistration's two
examples.** Computed over the whole declared range, `CL7:125`, `130`, `135`
and `140` have no witness inside the 60–120 word stem band, and nothing else
in the library does. §7.7 names `130` and `140`; `125` and `135` are reserve
rungs of the same family and the general statement is unchanged. The check
also required a padding rule that preserves sentence structure: appending
filler after a full stop adds an unterminated tail, which §9.2 counts as one
more sentence, so a witness for *exactly q sentences* padded naively becomes a
witness for q + 1.

**3. `assert_feature_words_are_specific` cannot hold unconditionally in v5.**
v4r4 chose every witness-breaking word for orthogonality. v5's eight marker
words are registered by §7.6 and their letters are what English makes them:
`whereas` contains an `a` and ends in `s`, `indeed` and `overall` have doubled
letters and are vowel-initial. None of that can be designed away without
changing the vocabulary, and none of it can bite: every colliding numerator
belongs to a Tier-3 family, and §7.4 with §13.10 keeps a Tier-3 companion
beside B alone. The check is now scoped to pairs that can share a cell, asks
`assert_pair_realisable` rather than assuming, and records every tolerated
collateral feature with the reason.

**Three under-specifications in the preregistration, one reading implemented
each, all recorded.** §13.8's discourse-role spread does not say what a Tier-2
member with no role contributes (implemented: `none` is not a role); §11.8's
tier-indicator secondary fit is **singular** as written, because a family
intercept per near-form control makes γ collinear (implemented: α ranges over
the three core families and a Tier-2 point sits at their average plus γ); and
§13.8's "less restrictive severity" is undefined for an exact count
(implemented from §7.10's own statement that higher q is harder). None changes
a decision rule; the second would have made an F8 secondary unidentified.

**One protocol tension escalated and not edited.** §7.10 says Tier-3 families
are admissible "to the spectrum and to the broad-class slot only", while §7.4
and §13.12 make a Tier-3 spectrum rung unreachable — the spectrum inherits its
core family's tier and the core pool is Tier 1/2. Operationally the two agree;
the sentence names a path no rule can exercise. The implementation follows
§7.4.

**Eight stale documentation values corrected**, none of them a threshold, a
band or a count: the changelog said fourteen open decisions where §34 lists
nineteen; the spec file pointed at §33 for the open decisions, named a
`terminal_status_when_unmet` that §13.15 says is an identification status,
listed a `class_same_form` slot that does not exist, and called the `comma`
statistic `comma_character`; and §7.6's list of registered marker statistics
still named `marker_notably` and `marker_finally`, which §7.6's own rule 3 and
§7.10's table contradict.

**Affected results: none.** No v4r4 record, evidence file or source line is
touched. v5 reads v4r4 *code* in exactly one place —
`dci1v5/verifiers/carryover.py`, which runs both revisions' numerators over
the frozen corpus and refuses on disagreement — and admits no v4r4 row
anywhere.

---

## 2026-08-22 — DCI-1 v5 drafted: the reference pool inverts class, and two v4r4 documentation values are corrected

**Standing.** v5 is **drafted, not adopted**. No v5 stage record exists, no v5
topic has been authored, no v5 instrument has been measured, and no number in
this repository moves because of it. It is here because it registers the
disposition of every v4r4 quantity and because two corrections to existing
artifacts fell out of drafting it.

[`user-notes/DCI1_preregistration_v5.md`](user-notes/DCI1_preregistration_v5.md) ·
[`user-notes/DCI1_v4r4_to_v5_changelog.md`](user-notes/DCI1_v4r4_to_v5_changelog.md) ·
[`dci1/reports/dci1v5/`](dci1/reports/dci1v5/)

**Why there is a v5.** v4r4 completed with two of four replications confirmed,
both on the 8-cell reduced design, and every companion-specific estimand —
`Δ_R`, `Δ_j`, `δ_difficulty`, `Ξ`, `D(B←R_j)`, `D(R_j←B)` — `NOT_IDENTIFIED`
study-wide. The reference-construction procedure did not deliver a usable
counterfactual on any surviving replication. v4r4 was frozen and produced
confirmatory data, so under v4r3 §31 a scientific change creates a new protocol
version.

**1. The core reference pool inverts constraint class.** v4r3 §13.1 says the
reference occupies A's slot and must resemble A; v4r3 §7.3 then forbids
production families from the reference pool. v5 §7.5 resolves the contradiction
in favour of §13.1: the core pool becomes exact counts of a short marker word —
same predicate form as A, differing only in which word and how many — and
v4r4's budget families move to the spectrum and broad-class arms. Measured
justification, on v4r4's own library and measurements: applying v5's full
validity stack leaves **3, 0, 0 and 0** qualifying families in the budget pool
across the four replications and **4, 4, 2 and 3** in the production pool
v4r3 excluded, unchanged at every stage of the stack
([`d5_gate_attrition.json`](dci1/reports/dci1v5/development/d5_gate_attrition.json)).
**Consequence for statements:** `COMPANION_CLASS_NOT_MATCHED` leaves every L3
statement and narrows to the broad-class arm; `REFERENCE_POOL_SAME_FORM`
replaces it and says the opposite thing — that v5's excess is relative to
companions *very* like A.

**2. A new pre-composition interaction gate, and the quantity it reads.**
`κ(R|B)` is R's verifier run on responses written under B **alone**, where R is
absent. Under §9.1's presence rule it costs zero extra generations. The gate is
`0.10 ≤ κ(R|B) + ι_R(1−κ(R|B)) ≤ 0.90`. On `gemma-3n-e2b-it`, the one v4r4
replication that composed a reference with B, the projection separated 4 of 4
Gate-4 failures from 16 passing checks with no false alarm, median absolute
error 0.067
([`d4_interaction_projection.json`](dci1/reports/dci1v5/development/d4_interaction_projection.json)).
**It reads no composed cell**: Δ_R reads `X_B` in the `B+R_j` cells and
`κ(R|B)` reads `X_R` in the `B`-solo cell.

**3. Raw compliance becomes an admission gate and ι is demoted.** v4r4 admitted
on ι alone, bounded chance only at 0.99, and read no raw solo compliance before
Gate 4 — which is why `CL8:3` at solo 0.9740 and chance 0.9323 was admitted as
the closest eligible rung and terminated its replication on its own **solo**
cell. v5 adds a Wilson-interval headroom band of [0.10, 0.90], an
instruction-lift floor of 0.20 and a chance ceiling of 0.75, and evaluates ι
**last** of eight lexicographic components.

**4. Two calibration splits and a high-recall screen.** The pre-screen distance
caliper is removed: measured pre-screen→calibration |Δι| has median 0.0709 and
**35.7% of candidates move further than the whole width of the 0.10 caliper**
they then have to clear. v5 doubles the calibration sample to 192 topics —
taking the caliper from 2.10 to 2.96 standard errors without moving the number
— and requires independent admissibility on two disjoint 96-topic splits
([`d3_split_half_stability.json`](dci1/reports/dci1v5/development/d3_split_half_stability.json)).

**5. Direct order estimands, and the L4 fix.** v4r4 registered no
cross-configuration contrast, so its observed Λ sign reversal could not be
tested and cannot be tested from its artifacts. v5 registers `Ord_A`, `Ord_B`,
`Ord_Λ`, `Ord_R̄` and `Ord_CL` in a new family F11 licensing claim level L4b,
with F1's membership unchanged so no primary interval widens. `emit_l4` becomes
`emit_l4a`, comparing the classification of each **named member** rather than
the set of levels reached, with three registered regression tests including
v4r4's `gemma-3n-e4b-it` pattern. **v4r4's invalidated L4 field is not
recomputed**; the fix is prospective.

**6. Corrections to two existing documents, neither of which moves a number.**

- [`dci1/reports/dci1v4r4/SCIENTIFIC_FOLLOWUP_EVIDENCE.md`](dci1/reports/dci1v4r4/SCIENTIFIC_FOLLOWUP_EVIDENCE.md)
  §6 quotes `REFERENCE_CALIPER` 0.075 and `REFERENCE_PRESCREEN_CALIPER` 0.10.
  The registered values in `dci1v4r4/protocol/constants.py` are **0.10** and
  **0.15**, and that package's own machine-readable companion
  `02_admission_landscape.json` records 0.10 and 0.15. The prose is wrong and
  the artifact is right. **No admission verdict in that package is affected**,
  because every verdict was produced by calling the registered selection
  functions rather than by reapplying a quoted threshold.
- `dci1v4r4/verifiers/constraints.py` documents `N_SEVERITIES` as 190 and
  `N_DECLARED_SEVERITIES` as 334 against computed values of **254** and
  **510**; `protocol/constants.py` comments `N_CONFIRMATORY # 408` and
  `N_SEQUESTERED # 72` against computed **384** and **96**. The computed values
  are what the code used and what every record carries. These are stale
  v4r3-era comments and nothing reads them.

**Affected results: none.** v4r4's estimates, records and terminal reports are
unchanged and unreinterpreted. v5's own status is that five scientific degrees
of freedom remain open
([`v5_prereg_redteam.md`](dci1/reports/dci1v5/v5_prereg_redteam.md)) and
nineteen registered decisions must be closed before its first stage can pass.

**Development evidence is design fitting, not validation.** Every v5 threshold
was chosen after observing the whole of v4r4, and
[`reference_design_development.md`](dci1/reports/dci1v5/reference_design_development.md)
§9 lists the nine things that analysis does not establish.

## 2026-08-22 — the whole pipeline below Gate 1 executed for the first time, and nineteen defects moved what a v4r4 record says

**Scope.** Nothing below Gate 1 in v4r4 had ever run under any codebase: v4r2
stopped at Gate 2 under different code and v4r3 stopped at Gate 1. Gates 2, 3,
4 and 5, the confirmatory generation, the masked analysis, the unmask and the
final analysis all executed here for the first time. Every
defect below is *a reader with no producer* or its close relative — code
reading a key, an attribute or an exception class that nothing on the executing
path writes or raises. None of them changes a registered rule; each changes
whether the registered rule was actually applied. No confirmatory data exists
under any revision, and no DCI estimand has been computed.

**1. Gate 2 read a `cell_rates` contract that has never existed.** Seven call
sites asked `cell_rates(...)` for `["solo"]` and `["chance"]` — keys it does
not return — and called it without its required `present=` argument. Gate 2
crashed on `gemma-3n-e2b-it` *after* all 16,128 calibration generations. The
repair adds `run/execute.instance_rates`, which mirrors the certified
`run/regime_screen.difficulty_table_from_rows`: the present cell and the
absent cell of one instance, with the topic as the averaging unit.
**Affected results:** none existed. Gate 2 could not previously produce a
record at all.

**2. §12.3's focal escalation had three readers and no producer.**
`focal_extension_measured` was read by the freeze, by the regime report and by
`focal_severities`, and no code path wrote it. §7.2's extension — B at m = 11
and m = 12, measured only when the registered grid supplies no eligible
severity — was therefore unreachable, and a replication needing it would have
recorded `FOCAL_RANGE_EXHAUSTED` instead. `run_gate2` now decides the
escalation from `select_focal_severity` over the registered grid, measures the
two extension rungs into a separate run directory so the banked registered rows
survive, and takes the union. **Affected results:** `qwen3-4b` is the
replication that needed it. Its registered grid tops out at m = 10 with solo
compliance 0.411, below `FOCAL_BAND`; the extension gives 11 → 0.659 and
12 → 0.742, and m\* = 12 was selected. Without the fix that replication would
have been terminal at Gate 2 on a rung §7.2 registers.

**3. The extended focal curve was built over all six severities.**
`select_focal_severity` raises on a curve containing a registered rung, so the
first escalation implementation refused itself. The union is now formed over
`FOCAL_EXTENSION` only. **Affected results:** none; caught before any record
was written.

**4. `design_variant_for` forced every replication to the reduced design.** It
read `getattr(result, "core_references", ())` and `SelectionResult` holds the
admitted references at `core["core_references"]`, so the default fired on every
call. §8.6 acts on the *variant*, so `gemma-3n-e2b-it` — three admitted core
references, six spectrum severities, `design` "full" — was assigned an 8-cell
design that estimates neither `delta_difficulty` nor Ξ. **Affected results:**
the first four Gate-3 records, superseded through the registered restart
mechanism at 7eb1947 and retained under
`evidence/dci1v4r4/<model>/superseded/7eb19472dfc4/`. The re-run records are
the current ones. The fixture that should have caught this had encoded the
defect as expected behaviour — `FakeSelection` carried `core_references` as a
plain attribute, matching the `getattr` call rather than the certified object —
and is repaired to use `SelectionResult`.

**5. A gate terminal could not be caught by the driver that runs the gate.**
`stages/gates.py` declared its own `TerminalStatus(Exception)`, unrelated to
`dci1v4.errors.TerminalStatus`, which is what `tools/run_v4r4.py::_run_stage`
catches. A `REGIME_NOT_FOUND`, a `FOCAL_RANGE_EXHAUSTED` or a
`COMPOSED_HEADROOM_FAILURE` would have escaped as an unhandled traceback: no
terminal report written, no transition logged, and a replication that had
failed a registered gate with nothing on disk saying so. The class now
subclasses the one the driver catches, carries `status` inside the record as
well as on the exception, and `_run_stage` reads `terminal.status` rather than
`args[0]`, which the two classes fill differently. **Affected results:** none —
no v4r4 gate has gone terminal. The consequence would have been a *missing*
terminal record, never a false PASS.

**6. Gate 4's band table could pass on cells it never saw.** §13.10 evaluates
every registered cell type against [0.05, 0.95]; `gate4_payload` reports the
failures among the rates it is *handed*, so a table that lost a cell type
reports no failure for it and an empty table passes outright.
`run_gate4` now checks the table's shape against the design the cells were
built from, before the predicate runs. **Affected results:** none; added
before Gate 4 was ever run.

**7. Two slots bound to one instance could merge silently.**
`design_run.attach_slots` built its instance→slot index as a dict
comprehension, so a second slot bound to the same (family, severity) replaced
the first and every verdict for that instance was attributed to one of the two.
`assert_slot_map_usable` checks uniqueness only across the slots the *variant
needs*, and a reduced replication carries admitted-but-unused references in its
map — `qwen3-4b` carries `R1 = RF11:21` and `R2 = CR5:8` — which are scored as
§25 chance verdicts and must be unambiguous too. **Affected results:** none;
no current slot map has a collision, checked.

**8. Gate 5 could not have passed on any replication, for six reasons.** §18.1
binds every scientific degree of freedom and refuses while one is missing, and
five of its fields had readers with no producer plus one rule that read *empty*
as *missing*. `chat_template_hash` came from a registration-manifest field that
has never existed — and it is not decorative, because the backend renders every
prompt through `tokenizer.apply_chat_template`, so the template is part of the
model-facing text; `hardware_record` was `{}` because `cmd_gate5` never passed
one; `environment_digest` and `dependency_digest` defaulted to the literal
`"-"`, which is not empty, so the completeness rule *accepted* it and two
provenance fields could have frozen as a placeholder; `gate1_measurement_basis`
was read from `reports/dci1v4r4/gate1_measurement.json`, which is the name of
the stage-record file and not of any report this study writes, so the basis was
always `UNKNOWN` and §33's D9 never closed. `tools/v4r4_backend_provenance.py`
now produces the first three from the tokenizer of the pinned revision and from
the backend's own provenance sidecars — the hardware the evidence came off, not
the machine that runs the freeze — and the basis comes from the signed
`GATE_1_MEASUREMENT` record. **Affected results:** none; no freeze existed.

**9. §8.6's reduced design could not be recorded in the freeze.** §8.6 says the
branch "is decided by the deterministic Gate 3 rule before any confirmatory
generation and is recorded in the freeze", and `core_references` and
`spectrum_severities` are legitimately empty under it — which
`check_completeness` reported as missing fields. `VARIANT_EXEMPTIONS` now lets a
field be empty **only** when the variant Gate 3 recorded does not identify it
*and* the record carries the §13.8 status for that non-identification, and
`identification_statuses` becomes a bound freeze field so the emptiness is a
recorded decision rather than a gap. **Affected results:** the two replications
that survive Gate 4 both run the reduced design, so without this the study could
not freeze at all. No threshold, caliper or estimand changed.

**10. §26's durability gate had no caller.** `assert_durable_before_freeze`
existed, was tested, and nothing on the execution path called it, so the freeze
recorded the durability report as a field without ever putting it to the rule.
It is on `run_freeze` now. A terminal report is also `CRITICAL_SUFFIXES` now,
and `_run_stage` mirrors it: a replication that fails a registered gate produces
exactly one signed artifact saying so, and `evidence/` is gitignored, so that
was the one class of v4r4 result living in a single copy. **Affected results:**
none, and the gate passes.

**11. The durable mirror had two artifacts competing for one path.**
`write_stage_record` writes the signed record at `<stage>/records/<f>.json` and
an unsigned reader copy at `<stage>/<f>.json`; `mirror_records` flattened the
first into `<durable>/<stage>/<f>.json` — the second's relative path. A
whole-tree replication then landed the reader copy on top of the signed mirror,
and the durable copy of every stage record in the study silently became the
unsigned one. Nothing was lost, because the same replication wrote the signed
record at its own relative path, but the phrase "the durable copy of the signed
record" had stopped meaning what it says. The mirror reproduces the evidence
layout exactly now, so one path is one artifact. **Affected results:** none; the
signed records themselves were never touched, and every mirror is byte-verified
again.

**12. §20's masking declaration asserted the full-design case unconditionally.**
The note that travels into every masked record said that no registered estimand
reads a singleton-companion slot as an OUTCOME. That is true of the 47-cell
design and false of §8.6's 8-cell one, where `A`'s only companion is `B` and
`D(A ← B)` is a registered reduced-design estimand. The note now states both
cases: on the reduced design the masked phase protects `D(B ← A)`,
`D(B ← CL)` and Λ, and does not protect the reciprocal direction.
**Affected results:** no number moves; a false statement about what the mask
protects would have travelled with every reduced-design masked artifact.

**13. §6.2's reserved-set audit asked whether a reserved topic had been touched
at all.** That was the right question while nothing had reached Gate 4 and the
wrong one afterwards: §13.10 spends the 24 composed-validation topics and is
registered to. `tools/topic_reservation_audit_v4.py` decides per stage now —
`composed` is Gate 4's, `confirmatory` is the confirmatory generation's,
`sequestered` is nobody's — and reports the licensed spend separately from the
offences. **Affected results:** none. The guarantee is narrower and true rather
than broader and about to become false; `sequestered` remains in no stage's
permission.

**14. No confirmatory generation was licensable on any replication.** §21's one
door, `assert_generation_licensed`, required a freeze field called
`verifier_source_hash` — the name of the *function* that computes the hash, and
of no field §18.1 registers; the freeze binds `canonical_verifier_hash`. Every
valid freeze record was refused. The test fixture standing in for a freeze
record carried the same non-existent name, so the fixture matched the check
rather than the record and the two agreed with each other about a study neither
could run. **This is the third fixture in this study to encode a defect as the
expected behaviour** (after `FakeSelection` and the stale stage literals). Both
sides now read the registered name, the fixture is checked against
`FREEZE_FIELDS`, and a test licenses generation from a freeze record the study
really wrote. **Affected results:** none; no confirmatory row existed.

**15. §21's selective-rerun guard was documented and not called.**
`assert_no_selective_rerun` refuses a row set that is not the plan's own —
duplicated identities, or rows the plan does not contain. `confirmatory_run`'s
docstring said it sees the union; nothing called it. The wider completeness
check refuses the same two conditions, so the effect was there and the guard
that names §21 was not; it is on the path now. **Affected results:** none.

**16. Three of the five registered claim levels had no emitter, and the two
surviving replications need exactly those.** §17.5 says "one guarded emitter
exists per claim level"; `analysis/claims.py` held `emit_l3` alone, and
`_claims` short-circuited to a single **non-emitted** L3 statement as soon as
Δ_R or Ξ were unidentified. So a replication running §8.6's reduced design
produced no claim of any kind — while §28's status table says of
`EXCESS_NOT_IDENTIFIED` that "L1 and L2 proceed under the reduced design;
L3a–L3c are withheld", and while the reduced design's identified estimand set is
exactly L1's two members and L2's one. `emit_l1`, `emit_l2` and `emit_l4` now
exist and implement §3.2's table verbatim: L1 needs the F1 simultaneous interval
for the named D(c←g) to have a lower bound above 0 and the outcome constraint to
have solo headroom; L2 needs Λ's interval to exclude 0 **and** L1 for both
directions; L4 needs the same classification in every registered configuration.
§17.3's `INSUFFICIENT_PRECISION` attaches as a status without suppressing a
resolved direction, §17.4's vacuity-forced agreement is required before either
level is licensed, and §11.4's `POSITION_CONFOUNDED` travels with every L1
statement in the shifted configuration. `solo_headroom` is derived from the
frozen n\* and m\* — §12.3 selects them only from severities inside the
registered bands — rather than defaulted. **Affected results:** none had been
computed; the final analysis of both surviving replications rests on these
emitters, and 17 tests state each licensing rule against §3.2's table.

**17. §17.4's reporting half travelled with no statement.** The clause has two
halves. The licensing half — a claim is licensed only when the primary and the
vacuity-forced recomputation license the same claim — is item 16 above. The
reporting half says the primary estimands "are reported with a fixed block
stating that composition changed how often the outcome constraint could bind,
and the F5 vacuity-forced recomputation is reported beside them as
partial-identification bounds." `f6_gate` computed `binds` into the result
table and nothing attached it to a statement. A binding gate now puts
`C.VACUITY_QUALIFICATION_SENTENCE` and the F5 bounds on every emitted L1 and L2
statement, and puts nothing there when it does not bind. **Affected results:**
none had been computed.

**18. §3.2's L4 gate is per named member; `emit_l4` compares level sets.**
§3.2 licenses L1 on "the named $D(c \\leftarrow g)$" and §28.1 pairs
*Replication* with *Configuration dependence* — "**the quantity** is
configuration-dependent" — so L4 asks whether each named member reached the
same level in every configuration. `emit_l4` compares the set of levels any
member reached, and `run/analysis_run.py` hands it a list of level names with
the member identity already discarded, so the emitter cannot distinguish
replication from a swap. **Affected results:** `gemma-3n-e4b-it`'s emitted L4.
Both of its configurations reach L1, but `D(A←B)` reaches it in
`outcome_first` only and `D(B←A)` in `outcome_second` only — each member's
classification flips. **That record's `claims.L4` is invalidated; the
registered reading is *Configuration dependence*.** `qwen3-4b` is unaffected:
`D(A←B)` reaches L1 in both configurations, so the emitted and registered
readings agree.

**It is not repaired in this revision, and the protocol is the reason.**
`run_unmasked_analysis` refuses an unmasked analysis under an
`analysis_code_hash` differing from the masked seal, and §20 forbids
regenerating a mask after semantic identities are known. Editing `emit_l4`
would therefore either strand both replications or require a forbidden
re-mask. `tools/v4r4_final_report.py` recomputes the registered per-member
reading beside the emitted field as `l4_registered_reading`, and
`tests_v4r4/test_l4_replication_defect.py` characterizes the sealed behaviour
so a silent fix fails loudly. The correction belongs to the next revision.

**19. The post-freeze delta reported provenance accretion as a scientific
change.** Three §18.1 fields enumerate the evidence tree — `hardware_record`
lists the backend provenance sidecars, `environment_digest` hashes a record
containing it, and `durability_record` counts the files in both roots — so all
three moved the moment confirmatory generation landed, and the delta reported
`scientific_state_unchanged: false`. A field that can only move is not
evidence that the frozen science changed, and a false alarm there trains a
reader to ignore the real one. They are not allowlisted: each is now
re-compared on the part that would mean something, and a move is excused only
when that comparison finds it unchanged. All three are unchanged for both
replications. **Affected results:** none; the freeze records never moved.

**Comparability.** Every v4r4 record written before 7eb1947 at Gate 2 or later
is superseded or was never written. v4r3 and earlier are untouched: the
`gates.py` of `dci1v4r3` still carries its own `TerminalStatus`, and that
revision is closed.

---

## 2026-08-21 — v4r3 closes at Gate 1; v4r4 adopts a deterministic Gate 1, removes CP4/CP7, and passes

**Scope.** A protocol revision, taken prospectively, before Gate 2 and before
any freeze, with no confirmatory data in existence and no DCI estimand — ΔR,
δ_difficulty, Ξ — ever computed under either revision. Nothing in v2, v3, v4r2
or v4r3 is edited, recomputed or reinterpreted. `dci1/DECISIONS_V4R4.md` B0–B7,
`user-notes/DCI1_v4r3_to_v4r4_changelog.md`, `RESEARCH_STATE.md` §4m.

**0. v4r3 is closed at its own criterion — no result moves.** Terminal state
`GATE_1_MEASUREMENT` / `MEASUREMENT_EVIDENCE_INSUFFICIENT`, under §18 stage 4
as registered at the time: §10.2 plus §10.3 or §10.4. §10.3 had no independent
annotator; §10.4, §10.4-R and §10.4-R2 each failed their own criteria; the
§10.7-R5 amendment then blocked on a wording. `closure.json` records that
state, hashes the six reports and 22 stage records it rests on, and writes one
new file without editing any. **Affected results:** none. v4r3's Gate-1 refusal
is not converted into a pass by anything below, and neither reviewer pathway is
described as having succeeded.

**1. Gate 1's measurement criterion, in v4r4, is deterministic by construction
— measurement basis.** R4-1. §18 stage 4 is §10.2 plus **§10.7 A–E**:
specification validity, implementation validity, independent reimplementation,
adversarial/boundary/**mutation** validation, provenance binding. Ten
conditions, none a reviewer-agreement threshold, and `gate1_payload` refuses
`human_validated`, `autorater_calibration_approved` and
`human_validation_unavailable` before it reads any evidence. §10.3/§10.4
artifacts travel as labelled supplementary diagnostics.
**Affected results:** what the study may *assert* is unchanged. The basis v4r4
can write is `deterministic_measurement_validated`, which is not
`human_validated`, so §10.5's scope sentence attaches permanently: the outcomes
are verifier-defined. §10.5's second question — would an independent human
reproduce these verdicts? — is exactly as unanswered as it was. **Old and new
are not comparable as measurement bases and must never be pooled**; §31-R4
registers the objection that an amendment must not weaken a criterion to make a
gate pass, and the counter it offers is checkable rather than rhetorical.

**2. `CP4` and `CP7` are removed from the candidate population — instruments,
wordings, coverage.** R4-2, decided as B3. Four wordings — *"Give {q} percent
of words doubled letters"*, *"Make {q} percent of words carry letter a"* and
their pairs — state the severity as a target and name no bound, so the prose
does not distinguish the registered `100·S/W ≥ q` from an `== q` reading. The
two agree at `q` and disagree on every answer past it, where the verifier
records a pass: a one-sided leniency in the *treatment*. The families are
removed under §10.2's registered removal rule. Vocabulary 30 → **28**
families; instrument population 584 → **524**; the `rate_lower_bound` predicate
form leaves the study, and the class arm becomes {count lower bound, exact
count}. The **canonical verifier hash therefore moves**, `41edc84c` →
`09f0675c`, and §10.6 forbids carrying the old one forward on the grounds that
behaviour looks unchanged — so the behavioural equivalence is *measured*: both
revisions' predicates over 524 instruments × 164 frozen cases, **85,936
verdicts, zero disagreements**.
**Affected results:** every v4r3 row generated under a `CP4` or `CP7`
instrument. Those rows are real generations and real v4r3 evidence; they are
classified `HISTORICAL_ONLY` and are evidence about nothing v4r4 measures. No
v4r4 coverage condition changed on any model — C1–C6 read `reference`-role rows
and both families are `class_control`, which is a property of §12.6's criterion
and is separately confirmed by the run; C7 holds on all four; ι_A moves on
none. The decision read only the §12.2 pre-screen difficulty table and **no
composed outcome**. `dci1/reports/dci1v4r4/cp4_cp7_analysis.json`.

**3. A prose-to-predicate invariant becomes a Gate-1 condition — instruction
wordings.** R4-3, §10.7 A′, decided as B4 and confirmed as B6. Every
model-facing wording must expose the comparison direction of the predicate that
scores it, by naming an operator from the registered direction lexicon
(`at most`/`no more than`/…; `at least`/`no fewer than`/…; `exactly`) or by a
construction registered as entailing one and admissible for that operator. A
target quantity with no operator fails the gate. **One construction is
registered**, the requirement verb: *needs {q}* is a necessity operator, so
`necessary(S = q)` and `S ≥ q` select the same answers, and it is admissible
for `≥` alone. 56 wordings rely on it — `CL7`'s and `CL8`'s fourth templates at
28 severities each — and B6 accepts it, so those rows are **not** regenerated;
the alternative branch would have cost 1,536 generations.
**Affected results:** none, in either direction. No live wording is changed, so
no measurement taken under one is invalidated. The `q = 1` plural mismatch
(*"Exactly 1 semicolons…"*, 45 wordings) is classified awkward-but-unambiguous
and does not block, unchanged from §4k. The **wording hash is new**,
`b9b258c5`, because the removed families' templates left the file.

**4. Evidence crosses the revision boundary only through a ledger — admission
rules.** R4-4/R4-6, §26-R4, decided as B5. Pilot and regime-screen
*generations* carry as `RECOMPUTED_FROM_EXISTING_RAW_DATA`: the model at its
pinned revision, the decoding configuration and the rendered prompt determine a
generation, and none of those changed. Every derived quantity — verdict,
compliance, vacuity, the §12.2 table, §12.6 coverage, §12.3's shortlist — is
computed again under v4r4's verifier hash. Reuse requires all seven invariants
to hold, and the two that could have been assumed are measured instead: the
85,936-verdict semantic comparison above, and **42,240 constraint sentences**
stored on carried rows checked byte-identical to the wordings v4r4 renders, 0
mismatched, 0 unparsed. Six v4r3 artifacts are `HISTORICAL_ONLY`, two
`NOT_APPLICABLE`, and **nothing is `INVALIDATED_AND_REGENERATED`**.
**Affected results:** v4r4's Gate 0 and regime screen are the same generations
v4r3 drew, scored under a different verifier hash and reported under a
different study id, and the ledger says so on its face rather than presenting
them as native. Two consequences are counted, not hidden: v4r4's seed domain
carries its study id, so carried rows are reproducible from v4r3's seed
schedule and not v4r4's; and a carried Gate 0 exercises every §19 check except
the backend call itself, which the stage record names.
`dci1/reports/dci1v4r4/evidence_reuse_ledger.json`.

**5. Gate 1 passes on all four replications — gate status.** All ten conditions
met. Determinism 1.000 over 3 processes; independent reimplementation exact at
`per_instrument_min` 1.000 across **628,800 verdicts** on 36,164 responses, with
a segmenter differential over all 1,114,112 codepoints; 164 boundary/adversarial
cases and 92,148 witness pairs pass; the specification audit covers 30 kinds
across 5 forms with 0 ambiguous; mutation validation separates every meaningful
reading with **0 undetected and 0 contradictions**; 0 wordings block. Hashes
bind: verifier `09f0675c`, wordings `b9b258c5`, specification `1704ddc3`,
mutation `a91f6220`, protocol `1e7a7b2d`, decision `df630dec`.
**Affected results:** this licenses Gate 2 and nothing else. It is not a claim
that human readers agree with the verifier, and the scope sentence in item 1
stands over everything downstream of it.
`dci1/reports/dci1v4r4/gate1_decision.json`.

**6. A coverage limitation is recorded rather than repaired — candidate
population.** B7 closes E5 by **declining** §12.6's registered candidate
expansion. C4 is met on all four models, but three of them —
`gemma-3n-e2b-it`, `qwen3-4b`, `qwen3-4b-instruct-2507` — meet it with exactly
four well-formed straddling feature groups, so every one is load-bearing and
there is no leave-one-family-out margin.
**Affected results:** any Gate-3 or Gate-4 result on those three models is
conditional on all four of its straddling groups holding, and that
conditionality travels with the result. The fragility is **inherited**: the
same sweep on v4r3's 30-family population returns the same families, so R4-2
did not cause it. Expanding the pool after seeing a coverage result would have
been an adaptive design choice, which is what §12.6's expansion rule exists to
keep out of the study's discretion. `dci1/reports/dci1v4r4/coverage.json`.

**7. The protocol hash moves after Gate 1, and the delta is resolvable —
provenance identifiers.** B6 and B7 were entered in the decisions register
after Gate 1 returned PASS and before Gate 2 began. The register is a protocol
document, so `protocol_hash` moved `1e7a7b2d` → `63f558b6`.
**Affected results:** no measurement and no payload byte. No Gate-1 record was
rewritten and no gate was re-run; the sealed records still name the old hashes
and still verify. `dci1/reports/dci1v4r4/register_amendment.json` proves the
delta is confined to `DECISIONS_V4R4.md` — the other three protocol documents
are byte-identical — and that the verifier, wordings, specification, mutation
and measurement-rule hashes did not move with it. A citation of `1e7a7b2d`
resolves through that file.

**8. The durable-mirror check was failing open, and four signed records had
one copy — provenance identifiers.** Assembling the Gate-1 checkpoint exposed a
defect in the integrity tool, inherited in shape from v4r3.
`mirror_records` replicates the contents of `<stage>/records/` into
`<durable>/<stage>/`, so the durable copy sits one level shallower than the
live one; the checker looked for a `records/` component that never exists,
reported `durable_present: false` on all 16 records, and then forgave itself —
the clause was `if durable.exists() and not mirrored`, so a *missing* mirror
raised no problem. Check 3 compared **zero bytes** while the report said
`passed: true`. Separately, §18 stage 1's qualification command never called
`mirror_records` at all, so the four `QUALIFIED` records existed only under
gitignored `evidence/`.
**Affected results:** no number, no payload byte and no signature. The checker
now compares the right path and **fails closed**; `cmd_qualify` mirrors on
every run outside its write-once branch; `tools/v4r4_mirror_records.py`
replicated the four missing records through `store.replicate` and
`store.assert_replicated`, which verify every byte and rewrite nothing that
already matched. Two test assertions now require `durable_present` and
`durable_mirror_matches` on every record. The same shape exists in v4r3's
durable tree, which is preserved as it stands and not repaired: v4r3 is closed,
and its records are historical evidence rather than a live second copy.

---

## 2026-08-21 — v4r3: §10.4-R2's outcome, and four stage records re-sealed

**Scope.** No v4r3 measurement moves. One class of record identifier does.

**1. §10.4-R2 failed and the autorater pathway stopped — measurement basis.**
The microcase audit's development half returned FAIL on registered criterion 5:
per-kind sensitivity 0.231 on `denominator_swap` against a floor of 0.50 set
before any microcase was judged. Criteria 2, 3, 4 and overall 5 passed. By
§10.4-R2's own stopping rule the LLM-validator pathway stops; the calibration
half is untouched and `mc-high`/`mc-low` were not run, for reasons recorded in
`DECISIONS_V4R3.md` A8 and `dci1/reports/dci1v4r3/section_10_4R2_outcome.json`.
**Affected results:** none, because the validator never scored anything —
§10.4-R2 keeps the deterministic verifier as the study's only scorer. What
changes is the *available* measurement basis: `human_validation_unavailable`
is now a standing condition and §10.3 is the only registered route left. Gate 1
refuses, no freeze occurs, no confirmatory generation begins.

**2. Four regime-screen stage records were re-sealed — provenance identifiers.**
`canonical_json` sorts integer dict keys numerically and string keys
lexicographically. §12.2's payload carries `completion_cap.table`, keyed by the
completion caps 512, 768 and 1024, so the hash computed over the in-memory
payload and the hash computed over the JSON it was written to differed, and
`verify_signed` rejected all four v4r3 regime records. `assert_transition_legal`
therefore refused every transition out of `REGIME_SCREEN`: Gate 1 could not have
written a stage record even had its measurement basis been licensed.
`dci1v4r3.engine.transitions.on_the_wire` now signs the wire form, and
`write_stage_record` verifies what it just produced. `tools/v4r3_reseal_records.py`
re-sealed the eight affected files (four records, two roots) after proving for
each that the stored hash was exactly `sha_obj` of *that* payload with its
numeric keys read back as integers — a proof an altered payload could not
satisfy. **Affected results:** no number and no payload byte. The `record_hash`
and `signature` of the four `REGIME_SCREEN` records changed; a citation of the
old hash `6556a2d6` / `5e2f1a45` / `6c71cc79` / `75f5008e` now resolves through
`dci1/reports/dci1v4r3/record_signature_repair.json`, which carries both. Old
and new records are the same evidence.

**3. A wording observation, recorded and not acted on — instruction wordings.**
Sixteen of the twenty-four families that admit severity 1 carry at least one
registered wording whose numeral and noun disagree in number: "Exactly 1
semicolons", "Use the word thus exactly 1 times", "At most 1 words may begin
with b". Six such rungs are eligible inside a §12.3 shortlist, and two of them —
`CX1:1` and `CX2:1` — are the exact form, where the plural noun plausibly
invites the *at least* reading rather than the exact one. `CX2:1` is the item
one of the 25 human annotations disagreed on, and the human's label is exactly
what the registered `inequality_flip` reading gives. A's carried template
special-cases the singular (`"time" if n == 1 else "times"`); no family template
does. **Affected results:** none yet. Changing a template changes the prompt
text of live rungs and re-opens a coverage result that currently passes on all
four models, so it is an amendment for the researcher and not a fix. Recorded
in `dci1/reports/dci1v4r3/gate1_decision.json`.

---

## 2026-08-21 — v4r3 repair pass: §10.4 replaced, three guards added

**Scope.** Prospective. No v4r3 number moves and nothing in v2, v3, v4r2 or the
four v4r2 design screens is edited, reinterpreted or recomputed.

**1. §10.4's judging task is replaced — measurement instrument.** Amendment R1,
registered as §10.4-R and changelog C26, decided in `DECISIONS_V4R3.md` A5. The
original task asked an LLM judge whether a response obeys a rule; for a rate
predicate over a hundred-word answer that is an enumeration, and neither
registered condition survived criterion 2 on v4r3's pool — truncation 23/72 and
40/72 against 0/48 for the same configuration on v4r2's pool of A and B alone,
rising monotonically with how much counting the rule demanded. §10.4-R asks
whether the deterministic *operationalization* faithfully implements the written
instruction, with the arithmetic shown rather than requested, and plants one
defect from a registered closed list of six in half the cards so that
sensitivity is measurable and the check is not a test of agreeableness.

**The deterministic verifier is unchanged and remains the study's scorer.** No
compliance rate, cell mean, estimand or claim reads anything the validator
produces. Every threshold was registered at commit `f657de2` before any card was
judged. §10.4's evidence is retained: it judges a different question and the two
pathways must never be pooled.

**2. §12.1's cap probe is sealed — provenance, no number affected.** The probe
generates composed `A + B` prompts by registered design, and their scored rows
carried per-constituent verdicts from which `D(B ← A)` at `A:8 + B:7` was
derivable. No registered procedure read them and no record contained them, so no
existing value changes; the probe is now projected onto §12.1's three registered
fields before the cap decision, and later stages read a restricted artifact.

**3. The stage machine now exists — governance.** `STAGE_SEQUENCE` was a list of
strings nothing read, which is how the §12.2 regime screen ran before
`QUALIFIED` and `GATE_0_APPARATUS`. The existing screen evidence is recorded
`ADOPTED_OUT_OF_ORDER`; it remains registered diagnostic evidence, it does not
satisfy any later stage's predecessor requirement, and the stage must be re-run
in order under the bound producing commit before Gate 1 can rest on it.

**4. The implementation is committed — provenance.** Every earlier v4r3 record
named a producing commit that did not contain the code that produced it. §18
stage 1 now passes and binds.

---

## 2026-08-21 — DCI-1 v4r3 adopted, registered, and executed to the regime screen

**Scope.** Prospective. Nothing in v2, v3, v4r2 or the four v4r2 design screens
is edited, reinterpreted or recomputed. v4r2 produced no confirmatory estimate
of any quantity, so no confirmatory result is affected by anything below.

**Adoption.** The researcher adopted DCI-1 v4 revision 3 on 2026-08-21
(`dci1/DECISIONS_V4R3.md` A0), and every study-wide rule is bound into a signed
manifest at `dci1/evidence/dci1v4r3/registration/`. v4r2 §31 makes a pre-freeze
change a revision, and v4r2 was never frozen and stands at `REGIME_SCREEN` on
all four models, so the boundary is v4r3 and not v5.

Four changes below alter what a number means. The full account, with evidence
and per-change classification, is
`user-notes/DCI1_v4r2_to_v4r3_changelog.md` (C1–C26).

**1. The lexical rule's composition order is corrected — measurement.**
v4r2's `words_lower` lower-cases the whole response and then segments; §7.0's
prose segments the answer and lower-cases each word for the suffix and letter
tests. §10.2's independent reimplementation, written from the prose by a
process that read no primary source, disagreed with the primary on the
`one_letter` statistic, and §10.2 adjudicates against the prose.

Scope, enumerated executably over the whole Unicode range: **exactly one
character** differs. `İ` (U+0130) lower-cases to `i` plus U+0307 COMBINING DOT
ABOVE, which is not alphabetic, so folding first splits the word — `İstanbul`
becomes two words of one and seven letters, and B at m = 7 would pass an answer
containing an eight-letter word. **Realised frequency in the 285,936 rows every
v4-era process has generated: zero.** No historical number moves;
`dci1v4r3.verifiers.statistics.assert_agrees_with_v4r2` states the equivalence
executably rather than claiming it.

**A is untouched and its v3 carry-over survives.** §9.2 registers S0 as
lower-case-then-segment in its own words, and the carried counting function
implements exactly that.

**2. The candidate reference population is rebuilt — design and measurement.**
Eight count-budget families over 94 severities become a registered *grammar*:
nine counted statistics × four predicate forms, 20 families, 190 severities
measured at round 0 and **334 in the declared candidate library**. The
canonical verifier hash changes and Gate 1's instrument population becomes 348
constraint instances over the whole declared range.

**3. Feature groups, and three references that measure three things — design.**
§7.5's witness suite, run over every pair of distinct families at every declared
severity, failed non-entailment **1,748 times in two structural shapes**: a
count budget at q = 0 entails the rate budget of the same numerator at every q,
and RF6 at q = 0 entails every CR6 severity. For such a pair no response
satisfies the first and fails the second, so the obligation is unsatisfiable
rather than unmet. §7.0 now registers eight **feature groups** and §13.4 admits
three core references from three different *groups*, not three different
families. 25,337 realisable pairs; all discharged.

**4. The allocation is 384 blocks at M = 8, not 408 at M = 4 — design.**
An earlier v4r3 draft moved the topic split to 34/6 per area so that 408 blocks
would meet every §16.2 precision precondition at M = 4. **That allocation is not
executable**: the released bank holds 528 questions and the other 96 exist only
as identities and content hashes, so the extra confirmatory topics could only
come from text no v4-era process can read. With the block count fixed at 384, M
is the only lever. 384 blocks at M = 8 meets every precondition under both φ
settings, **carries v4r2's topic split unchanged**, and keeps the sequestered
set at 96. Cost: 144,384 generations per model, 577,536 across four.

**5. §8.6 gains a third design variant — design.** A coverage failure withholds
`delta_difficulty` and nothing else, so a model with three admitted core
references but failed coverage runs a **29-cell no-spectrum** design rather
than the 8-cell reduced one. Routing it to the reduced design would discard six
identified primary estimands because a seventh is unavailable.

**Execution.** Registration, qualification, the stage-3 regime screen and
Gate 1's §10.2 evidence are executed under the signed manifest, on the
registered pre-screen topics only. No composed cell has been generated and no
gate after stage 3 has been run.

**§10.4's development phase changes what blocks Gate 1.** Run on v4r3's own
22,968-item pool, **neither registered judging condition survives §10.4's
criterion 2**: truncation 23/72 and 40/72, where the same configuration
truncated 0 of 48 on the v4r2 pool of A and B alone. Truncation is absent on
the outcome constraints and rises with the counting a rule demands, reaching
12/12 on rate lower bounds — the judge exhausts its 2,048-token cap enumerating
words to evaluate a rate. So §10.4 is not merely awaiting a signature: it has
an unmet criterion whose cause is the instrument population this revision
registered. The single-shot freeze and the one-shot calibration remain
unclaimed and the held-out half is hashed and never judged.

**One event worth recording.** The §10.6 verifier binding fired during
development: a hashed module was edited while the ladder screen was generating,
and the stage refused to place 4,920 rows rather than scoring them under a hash
that had moved. No row was mixed; the stage was re-run under a settled hash,
and the raw generations were reused only after an identity check on row id,
prompt hash and seed.

---

## 2026-08-21 — five reported quantities were misdescribed in the v4 summaries; corrected

**No artifact, estimate, verifier, threshold or code path changed.** Every
number below was already recorded correctly in the producing artifact. What was
wrong was the prose that summarised it, in documents that other documents then
quoted. Corrected in place, with the correction recorded here rather than
silently.

**1. B's solo vacuity range under the registered prompt.** Reported as
`0.208–0.659` in `RESEARCH_STATE.md` §4e/§4g, `ENDPOINT_2026-08-20.md` §1/§9,
`INVESTIGATION_2026-08-20.md`, this file, `DCI1_v4r2_to_v4r3_changelog.md` C1
and `DCI1_preregistration_v4r3.md` §2.3(a). Recomputed from
`cal_screen_v4/results.json:regime_adequacy_by_rung` over all 24 rungs on all
four models: **minimum 0.2083, maximum 0.8698**. `0.208–0.659` is the range of
the four **per-model minima** (0.339 / 0.208 / 0.312 / 0.659), which is what the
**min** column of `cal_screen_v4/REPORT.md` correctly reports; the summaries
transcribed that column as a range of values. The finding is unaffected and
slightly strengthened — no rung on either grid passes the 0.10 ceiling on any
model, and the true margin is 2× to 8.7× rather than 2× to 6×.

**2. "Intervals disjoint" on E2B.** `RESEARCH_STATE.md` §4f, `ENDPOINT` §5 and
§6, and this file's `focal_losses` entry stated that `D(B←CR6:7)` and `D(B←A)`
have disjoint intervals. They overlap on both scales — percentile
[+0.121, +0.207] against [+0.031, +0.143], simultaneous [+0.113, +0.216] against
[+0.016, +0.157]. The claim itself is correct and is carried by the registered
**paired** estimator, which is the right one: `Δ_1 = D(B←A) − D(B←CR6:7)` =
**−0.078, simultaneous [−0.134, −0.023]**, entirely below zero. Comparing two
marginal intervals is not a test of their difference and the wording is
withdrawn. On E4B the corresponding `Δ_3` = +0.022 [−0.044, +0.088] includes
zero, so no reference out-damages A there.

**3. "Under the mean reading nothing runs on any model under any stem."**
Stated in `RESEARCH_STATE.md` §4e and `INVESTIGATION` §7. Contradicted by
`cal_screen_v4/results.json`: qwen3-4b-instruct-2507 at m = 10 under the floored
stem has `feasible_mean_reading = true`, and `cal_screen_v4/REPORT.md` says so
itself — *"m = 10 is the only rung on any model feasible under both readings of
the graded clause"*. Corrected to: nothing runs on three of four models under
either stem, with that one exception; under the registered stem nothing is
feasible under either reading anywhere, because §12.4 fails on vacuity first.
This matters because it changes the framing of the §12.4 researcher decision.

**4. The matrix screen's reference sets were not admitted by the registered
§13.2.** Their disposition is *"conditions 1 and 3-6 as registered on the 96
calibration topics; condition 2 with its registered one-draw §12.2 input,
applied where that input exists"*. The summaries quoted `Δ_R` without it. Two
sensitivities in the same artifact are load-bearing: under
`strict_registered_precision` E2B admits five families and **RF2, one of the
three actually used, is not among them**; under `sensitivity_condition_2_at_M_cal`
E2B admits only `CL7, CL8, CR4`, all production-class, which would make `Δ_R` a
contrast between production companions. Condition 2's own input has a median
paired SE of 0.104 at one draw against a 0.15 caliper. Scope notes added to
`RESEARCH_STATE.md` §4f and `ENDPOINT` §5.

**5. Two interval conventions circulated for the same estimands.**
`RESEARCH_STATE.md` §4f quotes **percentile** intervals, `ENDPOINT` §5
**simultaneous** ones. Both are in `results.json` and both labels were honest,
but E2B's `Δ_R` **excludes zero on one and includes it on the other**
([+0.009, +0.087] against [−0.002, +0.098]) and §4f carried no label. Both
sections now state their convention and say that the simultaneous scale — the
one the registered rules apply to — governs where they disagree.

**Which results are affected.** None. No estimate, interval, artifact or
verdict moves; `reports/matrix_screen_v4/results.json` was regenerated and
diffed key-by-key against its predecessor with **0 values changed, 0 keys added,
0 keys removed**. Old and new remain fully comparable. What changes is what the
summaries say the artifacts contain.

**One code change, numerically inert.** `matrix_screen_v4/analysis.py` now
routes both the V5 difficulty line and the length line through a named
`fit_points()` helper instead of two inline comprehensions, so the invariant
that A (and the production-class companion) are excluded from a line used to
predict A lives on the execution path. The regression test that guarded it was
a source-text assertion counting a string literal; it is replaced by a
behavioural test that gives A extreme leverage, perturbs A's own delivery loss
across four orders of magnitude, and asserts the fitted line does not move.
`dci1` suite: 408 passed.

---

## 2026-08-21 — DCI-1 v4 revision 3: a hybrid difficulty-spectrum design, proposed

**Status: PROPOSED, NOT ADOPTED.** No registered v4r2 constant, verifier, grid,
ladder, wording, threshold or evidence record has been changed. The new
protocol lives in `user-notes/DCI1_preregistration_v4r3.md` and its executable
form in `dci1/src/dci1v4r3/`, a sibling package that `dci1v4` neither imports
nor can read. Adoption is decision **D0** of §33 and is the researcher's.

**Why a revision and not v5.** v4r2 §31: *"Before study-wide freeze, any change
is a revision of this document."* v4r2 was never registered, never frozen and
produced **no confirmatory data** — all four replications stand at
`REGIME_SCREEN` and no model has run Gate 1 or Gate 2. So the change is a
revision, exactly as v4r1 → v4r2 was, for the same reason.

**What changed, and on what evidence.** Twenty-one changes, each with its
evidence, classification and effect on interpretation, in
`user-notes/DCI1_v4r2_to_v4r3_changelog.md`. The four that move the science:

- **The prompt carries a uniform answer-length sentence** (§8.5). v4r2's §9.3
  registered a 20-word non-vacuity threshold on the reasoning that the topic
  space asks for 60–120 word answers, and its prompts never said so. On the
  registered calibration sample B's solo vacuity is at least 0.208, and up to
  0.870, at every focal severity on all four models against a 0.10 maximum, and 0.000–0.060 under the
  stem. `reports/cal_screen_v4/`, `reports/fs_screen_v4/`.

- **The difficulty coordinate becomes instructed compliance**,
  `(solo − chance)/(1 − chance)`, with raw solo compliance demoted to a
  registered secondary coordinate (§13.3). A is an exact-count production
  constraint whose chance rate is **0.000**; every count budget is prefix-closed
  and its matched rungs run 0.52–0.89. Twelve of twelve references in the matrix
  screen are matched to A on raw solo compliance and **two of twelve** on
  instructed compliance, and two are anti-productive.
  `reports/section_13_2_v4/instructed_compliance.json`. This is the **harder**
  criterion: it moves twelve of twelve previously matched companions out of the
  caliper and makes the reduced design more likely, not less.

- **A difficulty spectrum and `delta_difficulty`** (§11.7, §13.6). Each of the
  three core reference families supplies two further severities, one strictly
  harder than A and one strictly easier, and A's loss is differenced against a
  family-aware line fitted on the nine non-A companions with **A excluded**.
  This closes v4r2 §33's registered open decision **V5** in favour of both
  matching and spanning, at linear rather than quadratic cost: a spectrum
  companion pairs with B alone.

- **Ξ is promoted to the primary family and gates the wording of every L3
  statement** (§3.2, §11.6). In `reports/matrix_screen_v4/` the two largest Δ_R
  values in the study sit beside Ξ = −0.036 and −0.009 — A damaging the
  references about as much as it damages B. A quantity that decides how a claim
  reads belongs in the family the claim reads.

**Two v4r2 defects resolved.** §12.4's graded clause is read as a **share**: the
mean reading declares degenerate exactly the severities §12.3 declares eligible,
on every model under every prompt, and a clause that contradicts its own
neighbour is a defect rather than a reading. §33 D3 asks the researcher to
confirm it, and §12.4 states plainly that it is also the reading under which the
study can run. The focal grid **escalates** to m ∈ {11, 12} only when the
registered grid supplies no eligible severity, because a flat extension moves
m\* on a model whose registered grid already works.

**A registered limitation made explicit rather than discovered.** The reference
pool is budget class throughout and A is production class, so
`COMPANION_CLASS_NOT_MATCHED` attaches to **every** L3 statement with a fixed
sentence, and a one-companion class arm bounds how much that could matter
without estimating it. In the matrix screen a production-class companion cost B
+0.601 and +0.632 where A cost +0.086 and +0.228.

**Which results are affected.** **None.** v4r2 produced no confirmatory
estimate of any quantity, and every screen number stands as recorded. What
changes is what the design would measure. v4r2 rows and v4r3 rows are never
comparable and are structurally prevented from meeting: `STUDY_ID` is
`dci1v4r3`, deliberately hyphen-free, because `dci1v4`'s admission guard tests
`startswith("dci1-v4")` and `"dci1-v4r3"` would have passed it.

**Allocation.** 47 cells per block, 408 blocks, M = 4: **76,704 generations per
model and 306,816 across four**, against v4r2's 38,400 and 153,600. The binding
member is `D` at φ = 0.37, which fails its 0.05 precondition at 384 blocks once
the primary family carries six members. The sequestered set falls from 96 topics
to 72 because a 624-question bank cannot supply both.
`dci1/tools/allocation_v4r3.py` reproduces v4r2's published §16.2 row exactly
under an executable assertion, so the only thing that changed in the new row is
the estimand set.

**Safeguards.** `dci1/tests_v4r3/` — 127 tests, all passing, mapped to the
failure modes a spectrum design makes possible: a fit through the point it
predicts, an extrapolated residual reported as a measurement, a bootstrap that
does not refit, a selection rule that can see a composed outcome, a family
bypassing Gate 1, a freeze that does not bind a new rule, and a prose number the
code does not produce. The last of those caught a real disagreement during the
dry run — the preregistration said 45 calibration cells where the shortlist caps
give 41 — and the preregistration was corrected.

**Artifacts.** `user-notes/DCI1_preregistration_v4r3.md` (2,523 lines),
`user-notes/DCI1_v4r2_to_v4r3_changelog.md`, `dci1/src/dci1v4r3/`,
`dci1/tests_v4r3/`, `dci1/tools/{allocation_v4r3,dry_run_v4r3}.py`,
`dci1/reports/{v4r3_change_map.md,allocation_v4r3.json,v4r3_dry_run.json}`.
Full `dci1` suite: **831 pass**, against a 705 baseline, 76 s.

## 2026-08-19 — DCI-1 v4: a fresh study, and two findings that move v4r2's own numbers

**What changed.** A complete implementation of `DCI1_preregistration_v4r2.md`
under `dci1/src/dci1v4/`, isolated from v2, v3 and the B+R pilot: its own
namespace, its own evidence and durable roots, its own root seeds and
`dci1v4:` domain strings, its own 624-topic bank, and no scientific import of
any earlier DCI module. The protocol is **not frozen** and no confirmatory
generation has run; Gate 5 and confirmatory generation are implemented and
refuse to execute.

**What measurement changed for v4.** Everything, relative to v3, because v4r2
is a different protocol: the primitive is the per-constraint compliance vector
rather than target failure; the outcome scale is compliance rather than
failure; references are matched to **A** on solo compliance rather than to B on
solo failure; order is a cell-level factor; all M draws enter the cell mean and
no draw selector exists; a composed generation yields two observations. None of
this reinterprets a v3 number: v3's evidence tree is untouched and v4 reads it
only as design evidence, through one guarded door that stamps every result
non-confirmatory.

**What measurement changed for v4r2's registered constants.** Two pre-freeze
checks produced figures that differ from the ones v4r2 carries, and both bear
on decisions the researcher has not yet made.

* **C6, the companion-difficulty anchor.** v4r2 §13.1 and the change summary
  report the reference-minus-A solo gap as +0.198 (E2B) and +0.210 (E4B),
  taking `P(A solo)` from the v3 confirmatory target-alone arm and the
  reference rates from the Gate 2A cells on a different topic set. Reading
  `solo:A:<n*>` from the Gate 2A cache instead puts A and every reference on
  the same 96 topics and the same estimator, which is what C6 asks for, and
  the gap is **+0.164 (E2B) and +0.101 (E4B)**. Only 4 of 32 measured rungs
  sit within the registered 0.10 caliper of A on the v3 four-point grid.
* **C12, the allocation.** §16.1 registers phi = 0.27 under an assumed
  among-reference correlation of 1 and phi ~ 0.37 under 0.5, both fitted to
  the pilot's reported interval widths. Estimated directly from the pilot rows
  on the outcome the design uses — B re-scored under the v4 instrument at the
  pilot's own m\* — the among-reference correlation is **0.72** and phi is
  **0.556 (E2B) and 0.441 (E4B)** pooled. Pooled phi carries the pilot's
  order variance, which the v4 design cannot have because order is
  within-block; estimated inside each order stratum it is **0.395**. At 0.395
  the registered 384 blocks at M = 4 still meets every precision precondition,
  by 0.0008 on the half-width of D. At phi = 0.44 it stops qualifying and the
  registered menu rule moves to 480 blocks at M = 4, 48,000 generations per
  model.

**Which results are affected.** No existing result. v3's evidence, its records
and its reported numbers are unchanged and unreinterpreted; the B+R pilot's
rows are unchanged and were re-scored from raw text under the current v4
instrument with agreement 1.000 against its recorded verdicts (C13). What the
two findings affect is prospective: the feasibility of the §13.2 caliper (C7)
and the choice of allocation (V1), both of which are still open.

**Comparability.** v3 and v4 numbers are not comparable and are never compared:
different estimands, different outcome scale, different topics, different
instrument population, different design. C18 confirms the one algebraic bridge
that does exist — v4's demoted Delta^A reproduces v3's recorded
`secondary.pooled_swap_effect` exactly from the v3 rows, at -0.009548611 and
+0.065104167 — and confirms the compliance/failure identity that makes the
demotion argument rest on rows rather than on a summary.

**A third finding, from the real-model screens, in four of four replications.**
All four registered models completed QUALIFIED, GATE_0_APPARATUS and
REGIME_SCREEN; each selected cap 512; 15,264 real generations in total.

The dense ladder **does** reach A: five or six of the eight families carry a
rung within the 0.10 caliper in every model, against 4 of 32 rungs on the v3
four-point grid. But **not one of the 64 matched rungs across the four models
survives §13.2's family-solo-vacuity condition** — 13, 9, 24 and 18 matched
rungs, zero surviving in each case, leaving zero viable families everywhere.

The mechanism is structural rather than incidental, and it is measured on
identical prompts: unconstrained, gemma-3n-E2B-it writes 329 words and
Qwen3-4B writes 282; with one constraint, 121 and 49; with two, 80 and 25. A's
solo compliance is low, so matching it needs a restrictive "at most q"; a
restrictive budget constraint is satisfied by writing a shorter answer; and a
shorter answer makes the pass vacuous. Of the 4,873 vacuous passes across the
four screens, **seven** were truncations. §13.2 condition 1 and condition 6
pull against each other by construction.

§13.2 is evaluated at Gate 2 on 96 topics at M = 4, not on these screening
samples, so this is not an admission decision. It is decision-relevant for V3
(the caliper), V4 (the 20-word threshold, whose §9.3 justification — a topic
space asking for sixty to one hundred and twenty word answers — holds
unconstrained and does not describe what any of the four models produces once a
constraint is present) and V5 (difficulty-spanning references would not need
the reference to be as hard as A). It is reported rather than resolved. If it
holds at Gate 2, every replication takes the §8.6 reduced design with
`EXCESS_NOT_IDENTIFIED` and L3 — the study's headline claim level — is withheld
in all four.

**A fourth finding: two Qwen grid boundaries.** Neither Qwen model's operating
regime existed anywhere in the corpus. Qwen3-4B is squeezed at both edges of
the registered grids — n\* would be 1, the floor, and m\* would be 10, the
ceiling and the only eligible value, its B curve reading 0.25 / 0.58 / 0.54 /
0.75 against a [0.60, 0.95] band. A small shift at Gate 2 puts it into
`TARGET_RANGE_EXHAUSTED` or `FOCAL_RANGE_EXHAUSTED`, which are statements about
the registered grid and never about the model. Qwen3-4B-Instruct-2507 is the
mirror image on the A side, 0.92 at both n = 1 and n = 2 falling to 0.12 by
n = 8. The thinking-disabled path was validated on real data: zero
`<think>`/`</think>` leakage in 1,200 Qwen3-4B pilot draws.

**The same screen also measures trap T-7.** At cap 512 the constrained
truncation rate is 0.028 and the zero-constraint rate is 0.917. Had the
zero-constraint prompts entered the cap criterion, no registered cap would have
qualified (0.250 even at 1024) and the replication would have terminated
`RESPONSE_LENGTH_INCOMPATIBLE` before measuring anything.

**Evidence.** `dci1/docs/v4_prefreeze/` (one JSON per check, C1 to C20),
`docs/v4_traceability.md`, `dci1/tests_v4/` (324 tests: T1 to T14 plus the
anti-regression group), and the signed v4 records under
`dci1/evidence/dci1-v4/`.

---

## 2026-08-13 — figure data admission: the guard moved onto the mandatory path

**What changed.** `plotdata.load_all_reasoning` refused the deprecated shared-seed
grid, and four tests enforced that. `make_figures.py::build` never called it: it
called `plotdata.load_reasoning` directly on `s18_reasoning.jsonl` and
concatenated `s18_transition.jsonl`. The admission check now lives in
`load_reasoning` itself, keyed by a `NON_ADMISSIBLE` table mirroring the status
column in `REASONING_DATA_PROVENANCE.md`, with an explicit
`allow_non_admissible=True` opt-in used only to evidence the defect.
`build()` routes through `load_all_reasoning`.

**What measurement changed.** Which rows reach a figure. The previous path mixed
two sampling regimes on one curve:

* `s18_reasoning.jsonl` — DEPRECATED, one shared seed for all 160 requests, so
  390/400 nominal replicate pairs are byte-identical: two draws counted once;
* `s18_transition.jsonl` — FOREIGN, Round 10 transition budgets, 98.4% duplicate
  replicate pairs, already deprecated as curve-shape evidence.

**Which results are affected.** Everything `make_figures.py` wrote:
`reasoning_rows.csv`, `reasoning_cells.csv`, `reasoning_tau_and_delta.csv`,
`reasoning_timing.csv`, and figures fig01–fig18.

A later audit found the identical bypass in a **second** script:
`round10_analysis.py` loaded `s18_reasoning.jsonl` and appended
`s18_transition.jsonl` onto one curve, and writes `round10_s18.csv`. Its S18 cell
now loads `s18_reseeded.jsonl` only and is relabelled `S18 · QAC k=3`, since it no
longer includes the transition budgets. Its sibling cells
(`round10_s25/s26/s27.csv`) glob `*_reasoning.jsonl` inside their own run
directories and were never affected.

**Not** affected: `figure1_headline.*` and the natural-endpoint numbers, which
`make_headline.py` built through the guarded loader all along; the `natural_*.csv`
family; and `natural_analysis.py`, which already loaded `s18_reseeded.jsonl` and
printed a refusal notice for the deprecated grid.

**Comparability.** Old and new are **not** comparable for anything that reads the
capped curve's shape. The observable symptom is that the committed
`reasoning_rows.csv` carries `reasoning_budget` values 320/384/448/640, which a
guarded export cannot contain.

**Current interpretation.** The affected exports are marked
`SUPERSEDED_NOT_REGENERABLE_HERE` in
`exploratory/figures/reasoning_compute/data/PROVENANCE.json`. They are retained,
not deleted, because `runs/` is absent from this checkout and they are the only
surviving copy of the scored rows. Regeneration needs the workstation that holds
`runs/stageS18_reasoning_design_*/`. Point estimates in the seed-corrected
literature were previously reported as surviving the reseeding; the fine
curve-shape claims from the transition budgets were already deprecated
independently, so this change is expected to confirm rather than overturn the
published reading — but that is a prediction until the regeneration runs.

**Evidence.** `exploratory/tests/test_canonical_inputs.py` —
`test_the_raw_loader_itself_refuses_non_admissible_evidence`,
`test_the_figure_builder_uses_the_guarded_loader`, and
`test_no_production_script_names_a_non_admissible_generation_file`, which
generalises the second: it resolves loader call sites by AST across every script,
so a guard asserted at the one call site someone remembered cannot let a second
call site survive — which is exactly how `round10_analysis.py` was missed. It
checks USE, not mention, so a script that names a deprecated file in order to
refuse it does not trip.

---

## 2026-08-13 — figure timing no longer depends on an agent scratchpad

**What changed.** `make_figures.py` copied two driver logs from
`/tmp/claude-1000/-home-cnm13ryan-git-dci/<session-uuid>/scratchpad/` into the run
directory. That path belongs to a coding-agent session on a different host and
does not exist anywhere else. Logs are now read from the run directory only.

**What measurement changed.** Nothing behavioural. The time axis (fig09) and
`reasoning_timing.csv` are reconstructable only where the logs were already
preserved beside the generations; otherwise the timing frame is empty and the
figure is skipped, which the code already handled.

**Evidence.** `test_no_tracked_script_depends_on_an_ephemeral_session_path`.

## 2026-08-20 — durable replication moved to the stage exit (operational)

**What changed.** `engine/dispatch.run_stage` now replicates to
`durable_root/` *after* the signed stage record and its transition-log entry
are written, and verifies the copy with `store.assert_replicated`. The stage
bodies replicated before returning, so the record itself — written afterwards
by the dispatcher — was the one file guaranteed not to be mirrored.
`stages/registration.register` likewise now mirrors the manifest.

**Which results are affected.** None numerically. Four `regime_screen.json`
records, the registration manifest, four transition logs and three backend logs
had no current second copy; the mirror has been completed and verified
(157 files, `assert_replicated` passes). No evidence content changed — the
missing files were copied, not regenerated.

**Comparability.** Old and new remain fully comparable. This is a durability
defect in replication ordering, not a change to what any number means.

**Also.** `generation/backend.run_backend` now starts the backend in its own
process group with `PR_SET_PDEATHSIG`, and tears the group down on every exit
path. Three `vllm_backend` parents had survived their driver by twelve hours.
No effect on generated content: the backend binary, plan and seeds are unchanged.

## 2026-08-20 — FORM × STEM screen (non-confirmatory design evidence)

**What changed.** Nothing registered. A new non-confirmatory screen
(`dci1/src/fs_screen_v4/`, evidence at `dci1/evidence/fs-screen-v4/`,
protocol hash `98f8ee0da826b5023e24c32f8b33d9fce1f645372742d6a0c2edec4f086755e5`)
generated 13,392 rows across the four registered models to test two candidate
answers to the length channel documented in the 2026-08-20 diagnostic. It has
the same standing as the B+R pilot: design evidence, non-confirmatory, refused
by the v4 positive-admission guard, and it enters no v4 estimator.

**Which results are affected.** None. No registered constant, verifier,
threshold, grid, ladder, wording or protocol text was changed; the canonical
verifier hash still equals the one in the signed registration manifest, and a
test asserts it. The registered §12.2 ladder screen and §12.1 cap set were read
for the `count × current` baseline and were not regenerated.

**Comparability.** Screen rows are NOT comparable with registered v4 evidence
and must never be pooled with it: they carry a different stage label, a
different seed root (202608200, domain `fsscreen:gen:v1`) and, in the `floored`
arm, a different prompt template. The `current`-stem baselines reproduce the
registered records exactly, which is what makes the two arms comparable *with
each other*.

**What it found.** The registered pool fails the §13.2 condition-1 ∧ condition-6
conjunction with bootstrap P(≥3 families) of 0.000–0.001 on all four models;
candidate non-budget forms reach 0.41–0.88. A uniform answer-length stem removes
B-solo vacuity (0.39–1.00 → 0.00–0.17) and makes the raw and length-restricted
D(B←A) converge, but drives both Qwen models to `FOCAL_RANGE_EXHAUSTED`.
Two amendments are drafted in `user-notes/` and **neither is adopted**.

## 2026-08-20 — B-grid screen, and a correction to the FORM × STEM reading

**What changed.** Nothing registered. A second non-confirmatory screen
(`dci1/src/bgrid_screen_v4/`, evidence at `dci1/evidence/bgrid-screen-v4/`,
protocol hash
`6a63ba782db0de6e1c4d80763065dda7ced1279e3c8ddcc097c7119087f4fff2`) generated
2,112 rows across the four registered models to measure B's solo curve under the
floored stem at m ∈ {7,…,12}. Same standing as the FORM × STEM screen and the
B+R pilot: design evidence, non-confirmatory, refused by the v4
positive-admission guard, entering no v4 estimator.

`m = 11` and `m = 12` are **screen-only**. `FOCAL_GRID` is unchanged at
(7, 8, 9, 10); `Constraint("B", 11)` and `focal_wordings(11)` still raise, and
`tests_v4/test_bgrid_screen_isolation.py` pins both. The screen's own renderer
and scorer for the two extension rungs are proved byte-identical and
verdict-identical to the registered ones on every registered rung.

**Which results are affected.** One. The FORM × STEM screen reported that the
floored stem drives **both** Qwen replications to `FOCAL_RANGE_EXHAUSTED` on the
registered focal grid. That reading is **superseded for
qwen3-4b-instruct-2507** and stands for qwen3-4b.

| model | FORM × STEM, m = 10, floored | B-grid, m = 10, floored | registered-grid outcome |
|---|---|---|---|
| qwen3-4b | 0.333 | 0.375 | `FOCAL_RANGE_EXHAUSTED`, replicated, 2.3 SE below the floor |
| qwen3-4b-instruct-2507 | 0.542 | 0.667 | **flips**: exhausted there, m\* = 10 here |

Neither measurement is wrong. Both are single draws on the same 24 pre-screen
topics under different seed roots, and the mean absolute rung-level gap between
the two screens is 0.031–0.125. The FORM × STEM report flagged this specific
call as marginal (0.54 against a 0.60 floor, ≈ 1.5 topics); it was. The
FORM × STEM rows are **not** invalidated and are not corrected — the observation
stands and the interpretation drawn from it does not.

**Comparability.** B-grid rows are NOT comparable with registered v4 evidence
and must never be pooled with it: different stage label, different seed root
(202608210, domain `bgrid:gen:v1`), and in the floored arm a different prompt
template. The current-stem B rungs at m = 7…10 are read from the registered
§12.2 ladder screen without regeneration and reproduce it exactly.

**What it found.** An honest focal severity exists at m ≤ 12 on all four models,
but the frozen §1.4 rule returns **MARGINAL**, not PASS: qwen3-4b-instruct-2507's
only two in-band rungs are both 0.667, within one clustered standard error of the
band floor. The floored stem removes B-side vacuity on all four models (maximum
vacuous share of passes 0.000–0.100) without being obeyed — the Qwens satisfy the
60–120 word instruction only 29–38% of the time — and it re-anchors A on every
model (n\* 4, 1, 1, 3 → 1, 2, 2, 5). Amendment C is drafted in `user-notes/` and
**not adopted**.

## 2026-08-20 — Gate 1: §10.2 evidence for A and B, and a defect in the carried judge prompt

**What changed.** No registered code, constant or artifact. Three new tools
(`dci1/tools/gate1_evidence_v4.py`, `gate1_readiness_v4.py`,
`gate1_autorater_v4.py`) execute registered procedures and write to
`dci1/reports/gate1_v4/`. Gate 1 is **not** approved, the §10.4 single-shot
freeze and one-shot calibration are **not** claimed, the v4 final-check set is
prepared but **not** sealed, and no labelling session was started.

**Which results are affected.** None retroactively. §10.2 is now met for A's
exact-count rule and B's word-length rule over 13,953 distinct genuine
responses: three-process determinism 1.000, boundary suites 48 A cases and 45 B
cases at 1.000, prose-only reimplementation 1.000, carry-over not refused (17
symbols byte-identical to v3). The response pool is the pre-screen and pilot
population, **not** the solo-calibration pool, which does not exist until Gate 2;
the determinism and reimplementation lines must be re-run over that pool when it
does.

**A defect in a carried artifact.** The v3 judge prompt `gate1-judge/2.0.0` is
carried byte-identically, and it does not survive v4's second instrument. Every
registered B wording says "the answer" — "Every word in the answer must have at
most 7 letters" — and after the prompt's trailing `Answer:` the judge reads that
as binding on **its own reply**. Its reasoning transcript says so explicitly
("we must ensure that the answer itself has at most 7 letters"). At high
reasoning effort it then spends the whole 2,048-token cap composing a compliant
reply and never reaches its verdict: **coverage 0.25, truncation 0.75**. At
medium effort it does not truncate but still injects the constrained token into
its own justification and emits labels that contradict their own stated reason.

This does not invalidate any v3 number: v3's only instrument was the exact-count
rule and its judging was done under the same prompt, so v3 remains internally
consistent under its own conditions. It does mean the carried prompt cannot be
inherited for v4. A v4 prompt version `gate1-judge-v4/1.0.0` is authored and
measured against it as a paired condition; **neither is registered**, and the
selection is recorded as §10.4 development evidence only.

**A sharp edge in `dci1v4.stages.autorater.build_config`.** `CONFIG_FIELDS`
does not include the rendered reasoning condition, and `build_config` keeps only
declared fields. A caller passing `chat_template_kwargs` as a sibling of
`decoding` has it silently dropped, so medium-effort and high-effort
configurations — which demonstrably produce different judgments — hash
identically and `assert_no_config_drift` cannot tell them apart. The v4 driver
places it inside `decoding`, which is a declared field, and
`tests_v4/test_gate1_autorater_config.py` pins both the workaround and the
failure mode. **The registered helper was not modified.**

## 2026-08-20 — §12.4's graded-degeneracy clause is ambiguous, and for B it is incoherent or inert

**What changed.** Nothing. This records a preregistration defect found while
cross-checking the Gate-2 calibration screen, not a change to any code or
artifact.

**The defect.** §12.4 requires "the graded distribution of each outcome
constraint" to be non-degenerate, "meaning it is not concentrated above 0.99 or
below 0.01". `gates.gate2_payload` accepts `graded_distribution` as one float
per constraint and compares it against `GRADED_DEGENERACY_HIGH = 0.99`. **It
does not say which float.** Every caller in the repository was checked: an
arbitrary probe in `tests_v4/test_t6_stage_machine.py` and the calibration
screen, which correctly runs both. No registered caller has ever fixed the
reading, so the ambiguity is open in the code as well as in the prose.

**For B the two readings are not merely different, they are the two ends of the
protocol.** B's graded score is `1 − (words over m)/(total words)`, which cannot
fall far from 1 for any plausible response — a failing sixty-word answer with
two over-length words scores 0.967.

- **Mean reading** — mean graded rises with compliance and crosses 0.99 *inside*
  the focal band. Measured on the B-grid screen's floored B-solo cells, it fires
  on every in-band rung of three of four models. So §12.3 declares a rung
  eligible and §12.4 declares the same rung degenerate: **two registered
  criteria in direct contradiction**.
- **Share reading** — B scores 1.0 when it passes and, empirically, above 0.99
  when it fails in 65 of 18,432 rows (0.0035). The share is therefore the pass
  rate plus 0.0035, and exceeding 0.99 would need compliance above 0.99, which
  the focal band already caps at 0.95. It fires on **no** in-band rung on any
  model under either stem. **Inert.**

**The defect is specific to B.** On A the clause behaves as written: measured on
the same screen's floored A-solo cells, mean graded runs 0.646–1.000 and the
share 0.333–1.000, and it fires only on two near-ceiling
qwen3-4b-instruct-2507 rungs whose compliance is 1.000 — which is the degeneracy
it exists to catch. The exact-count form has a graded score that varies; the
word-length budget's does not.

**Which results are affected.** None retrospectively — Gate 2 has not run. Going
forward the choice decides whether any replication starts: under the mean
reading **no rung of any grid is feasible on any model under either stem**.

**Disposition.** A V-decision for the researcher, recorded in
`user-notes/DCI1_v4_amendment_C_focal_grid.md` and belonging in
`DCI1_v4r2_unresolved_decisions.md`. Not decided here. Both readings are
reported wherever the quantity appears.

**Provenance.** The two-reading problem was found by the sibling session
`dci-79` on the 96-topic calibration screen; the contradiction-with-§12.3
framing and the A-side characterisation are from this session's B-grid rows.
Both are cross-checked on independent samples.

## 2026-08-20 — v3 re-analysis: what the confirmatory rows identify, and a correction to a quantity quoted from them

**What changed.** Nothing registered, and nothing in the v3 evidence tree. A
read-only re-analysis (`dci1/tools/v3_reciprocal_reanalysis.py`, results at
`dci1/reports/v3_reanalysis/`) recomputes from the closed v3 confirmatory and
Gate 2A caches. v3 remains closed and `dci1/RESULTS_V3.md` stands.

**What it establishes, and why it belongs here.** The v3 confirmatory design
carries `A`, `AB`, `AR1`, `AR2`, `AR3` and `TOPIC` on the same 384 blocks and
**no solo cell for B or for any reference**. So `D(A←B)`, `D(A←R_j)`, `Δ^A`,
`Δ^A_j`, companion uptake and joint success are identified with same-topic
pairing, and `D(B←A)`, `D(R_j←A)`, `D(R_j←B)`, `Λ`, `Δ_R` and `Ξ` are **not
identified from these rows at all** — each needs a solo baseline on the
confirmatory topics that v3 never generated. That is a rule about which data an
analysis may read, which is why it is recorded here rather than only in a
report.

**Which results are affected.** One. `dci1/reports/companion_identity_review.md`
(2026-08-20, same day, earlier) quotes

| model | "D(B←A)" | "D(R̄←A)" |
|---|---:|---:|
| E2B | 0.468 | 0.582 |
| E4B | 0.316 | 0.727 |

Those numbers are arithmetically reproduced by the new tool and they are **not
delivery losses**: each subtracts a composed rate measured on the 384
confirmatory topics from a solo rate measured on the 96 Gate 2A calibration
topics. The sets are disjoint and the contrast is unpaired. They are re-labelled
as an unpaired cross-set diagnostic and may not be quoted as `D(B←A)` or
`D(R̄←A)`. The topic-set shift is now measured for the one constraint that
exists on both sets — A at n\*, same estimator — at **−0.046 (E2B)** and
**−0.105 (E4B)**, so the qualitative reading survives a shift of that size; the
larger confound is that on E4B the references are satisfied in 4–8% of composed
responses, so their loss sits near its ceiling by construction.

**What is added.** Block bootstrap over the 384 confirmatory blocks, 10,000
resamples, resampled within order stratum; studentised maximum-modulus
simultaneous intervals over the three per-reference contrasts; the order
stratification; the uptake and joint-success tables; and the response-length
record. Check `C18` recorded point estimates only, and this reproduces its Δ^A
to 1.4 × 10⁻¹⁷ on both Gemmas, which fixes the provenance.

Δ^A = **+0.0639 [+0.0405, +0.0871]** (E2B) and **+0.0737 [+0.0519, +0.0951]**
(E4B) on all 16 draws — positive, excluding zero, and **below the 0.10
generic-load threshold** on both. On E2B the three per-reference components are
+0.056, +0.142 and −0.006, so the §13.4 heterogeneity qualifier fires; on E4B
they agree within 0.010. On E2B `D(A←B)` is +0.058 in one order and +0.217 in
the other.

**And a retrospective finding about v3's own reference admission.** v3
registered no non-vacuity predicate; §9.3's twenty-word threshold is a v4
registration. Applying it to v3's Gate 2A solo cells as a re-description:
**A's solo cell has a vacuous-pass rate of 0.000 at 269–323 mean words, and
every admitted reference has 0.43–0.90 at 9–30 mean words** (E2B RF3:5 is 0.823
at 14 words; E4B RF3:5 is 0.896 at 9 words). v3's §18 rule matched references to
B within 0.10 on solo failure, and on both models that matching was performed on
quantities in which a majority of the passes were the model declining to answer.
It explains what `RESULTS_V3.md` flagged without explaining — the admitted
references were satisfied in 2–8% of composed responses on E4B. Applying §17.4
to the pilot's reciprocal losses says the same thing from the other side: five
of six `D(R_j←B)` become strongly negative once vacuous passes are recoded.
**No v3 row or verdict is invalidated**: v3 was internally consistent under its
own rules, and its rules contained no vacuity gate. What this shows is that
v4's §9.3 predicate and §12.4 ceiling answer a defect that was already present
and already load-bearing.

**Δ^A survives the registered §17.4 vacuity bound.** Recomputed with every
vacuous pass forced to a failure, it is +0.0634 and +0.0720 against +0.0639 and
+0.0737 — a change of −0.0005 and −0.0017, on 9 and 39 vacuous passes in 24,576
composed rows. The same bound removes 72–82% of the B+R pilot's Δ. The asymmetry
is what a length-monotone budget outcome does that an exact-count production
outcome does not.

**And the length differential is order-dependent, which the pooled number
hides.** In the `added_first` configuration the `AB` and `AR̄` cells differ by
two to seven mean words and the length-matched Δ^A is **+0.047 on both models**
— the cleanest estimate these rows contain, and squarely in the generic-load
region. In `target_first` the references run 50–70 words longer, longer answers
make the exact-count constraint harder, and matching therefore *raises* the
estimate to +0.212 and +0.130 on four and three supported bins. Δ^A, the length
differential and the order are one entangled system on this design.

**Comparability.** Δ^A on all cached draws is **not** the v3 registered
`pooled_swap_effect`, which selected one draw of sixteen under the v3 selector
and is −0.0095 on E2B. Both are correct under their own rule and C18 records the
distinction. Nothing here is comparable with v4, which is a different protocol.

## 2026-08-20 — the B+R pilot's Δ is near-collinear with response length

**What changed.** Nothing registered, and nothing in the pilot's or v3's
evidence trees. A read-only re-analysis (`dci1/tools/pilot_length_channel.py`,
results at `dci1/reports/pilot_reanalysis/`) recomputes from
`evidence/br-pilot-v4/<model>/cache.jsonl` and the v3 confirmatory `AB` rows.

**Which results are affected.** The B+R pilot's headline, and with it the
support for promoting `Δ_R` to a primary estimand in v4r2 §11.3. The pilot
reports Δ = +0.343 (E2B) and +0.375 (E4B), classified `H1_PAIR_SPECIFIC`. **The
rows are not invalidated and the estimate is not withdrawn.** What changes is
what it can be read as evidence for.

**Three findings, in order.**

1. **Vacuity, on the registered bound, carries most of it.** §17.4 registers
   the partial-identification recomputation — every vacuous pass forced to a
   failure, no row dropped, nothing conditioned on. Under it Δ is **+0.0950**
   (E2B) and **+0.0678** (E4B) against +0.3433 and +0.3751 as reported: **both
   below the 0.10 generic-load threshold**. `P(B|A)` does not move — the A+B
   responses average 128–139 words and are never vacuous — while `P(B|R̄)` falls
   from 0.688 to 0.439 and 0.819 to 0.512, because 36% of the pilot's B+R
   responses are under twenty words. The *restriction* to ≥ 20 words gives the
   opposite answer (+0.3484, +0.3599), and §9.3 says why it is not the
   protocol's answer: removing vacuous passes "would condition on a consequence
   of the treatment". The restriction is a collider-conditioned sub-population;
   the forcing is the registered bound. **And §17.4's last sentence settles the
   disposition**: "a claim is licensed only when the primary and the
   vacuity-forced recomputation license the same claim; otherwise the axis is
   reported unresolved with both bounds". +0.343 would support pair-specific and
   +0.095 supports generic load, so by the registered rule the pilot's Δ axis is
   **unresolved**, with both bounds reported — a stronger and more
   protocol-faithful disposition than either "it is a vacuity artifact" or "it
   survives".
2. **The two cells differ five-fold in response length.** The pilot's B+R̄
   generations average 24.8 words (median 23); the v3 `AB` rows its P(B|A) term
   comes from average 127.9 and 139.1 (median 126, 137). B at m\* = 7 is a
   max-word-length budget, so its difficulty rises with word count. Within
   word-count bins the identity contrast disappears: weighted over bins with at
   least twenty responses in both cells, the gap is **−0.057** (E2B) and
   **−0.003** (E4B).
3. **The two cells are nearly separated on the mediator.** Only two of six bins
   carry twenty responses in both, holding 9.1% of the A+B rows and 28.3% of the
   B+R rows (E2B); 7.8% and 30.6% (E4B). So the length-adjusted contrast is
   weakly identified and the raw contrast largely compares two disjoint length
   regimes. Response length is a consequence of the companion (§13.3) and §22
   registers it as a mediator the primary estimand is never conditioned on;
   these are sub-population comparisons and not a causal decomposition.

**The pilot declared the cross-set structure and defended it by topic-set
exchangeability** (`protocol.json`, `reused_baselines.cross_set_note`). The
finding is that the declared defence does not reach the mediator: exchangeable
topics do not buy comparable response lengths.

**Two confounds, and only one survives into v4.** The *source* confound — Δ's
two terms coming from two studies — v4 eliminates by construction, because §8.1
puts A+B and B+R_j on every block. The *class* confound does not go away: every
registered reference family and B are `S ≤ q` budgets whose pass sets are
downward-closed under prefix, and A is the only production constraint in the
pool. A budget companion helps a budget outcome by letting length collapse, so
`Δ_R` as registered measures A's damage plus the control's help, with the second
term structurally non-positive in expectation. The pilot's own numbers show it:
`D_B_from_Rbar` = **−0.059** on E4B, `D_B_from_RF6@4` = −0.167, and reciprocally
`D_RF1@5_from_B` = −0.063 and `D_RF2@5_from_B` = −0.115.

**Comparability.** Everything above is a re-description of the same rows under
the same verifier hash `2059509d…`; no verdict was recomputed under a different
rule. The pilot's own estimates stand as recorded and are not superseded — they
are qualified. A future citation of Δ = +0.34 without the length qualification
is a misreading of the record, not of the number.

**A related figure that moves in the other direction.** On the A side, within v3
and on the same 384 blocks, the arms separate on length by only 1.15–1.44×
(E2B) and 1.24–1.34× (E4B), all six word-count bins carry at least thirty
responses in all four arms, and Δ^A **survives** length matching: +0.064 raw
against +0.118 matched (E2B), +0.074 against +0.059 (E4B). See the same-day
entry on the v3 re-analysis.

---

## 2026-08-20 — the screen's witness constructor reported construction failures as entailment claims

**What changed.** `dci1/src/fs_screen_v4/witnesses.py` now enforces the envelope
it previously only documented. `verify_candidate_pair` and `joint_witness` build
their "candidate satisfied, companion failed" witness by appending
`FOCAL_VIOLATOR`, a long word — which fails **B** and moves **no** reference
family's statistic. Applied to a reference family the construction therefore
fails to produce a violating text, and the function reported that failure as
`CR6@7 appears to entail RF3@4`: a false scientific claim, raised by the
machinery whose whole purpose is to certify that no such entailment holds.
Reproduced for CR6, CR4 and CL1 against RF1, RF3 and RF6. A new
`assert_in_envelope` refuses any companion outside `("A", "B")` and names the
reason; two tests in `dci1/tests_v4/test_fs_screen_isolation.py` pin it.

**Found by** the sibling session `dci-79`, which hit it while building the
matrix screen's witness check and bounded its own call site. Reproduced and
fixed at the source here.

**Which results are affected: none.** The FORM × STEM screen only ever called
the function with A and B companions, which are inside the envelope.
`verify_all` still certifies 576 compositions, and the frozen screen protocol
payload at `dci1/reports/fs_screen_v4/screen_protocol.json`
(`98f8ee0d…6755e5`) is byte-identical apart from `producing_commit`, which
floats with HEAD by design. Every screen number stays comparable. The defect was
latent: it could only fire on a call the screen never makes.

**Why it is recorded here anyway.** The failure mode is not a crash but a
*wrong verdict with the right shape*, on a §7.3 certification path. Anyone
extending the screen to a larger pool would have met it, and its natural reading
is the opposite of the truth.

**Related, and larger: Amendment B's cost list was incomplete.**
`user-notes/DCI1_v4_amendment_B_reference_pool.md` §5 costed the new predicates,
CR6's numerator, the canonical verifier hash and the Gate 1 instrument set. It
omitted §7.3's witness obligation over the enlarged pool, which is quadratic in
the pool: under §6's recommended adoption set (CR7, CR4, CR6) the pool goes from
106 instances / 4,910 pairs to 130 / 7,646, of which **2,448 pairs have no
constructive certificate** against the 288 candidate × A/B compositions the
screen proved. Three classes are uncovered — candidate × reference,
candidate × candidate, and anything involving B at m = 11 or 12, which the
registered `Constraint` constructor refuses by design. Recorded as §5a of that
document, with the adoption sequence corrected to include building the missing
constructor before the boundary suite. **Nothing was adopted.** The cost
disappears if the registered pool clears three families under Amendment A's
stem.

**Not a hole, checked and cleared.** The same investigation raised, and then
retracted, a suspected gap in §13.2 condition 5 (witnesses against *every* other
admitted reference) on the grounds that `admit_family` checks only A and B.
There is no gap: `verifiers.witnesses.verify_all_witnesses` certifies
`all_pairs()` — every unordered pair of distinct kinds over
`registered_instances()`, reference × reference included — pool-wide before any
selection. Independently recomputed here as 4,910 pairs in 45 kind-pair classes,
3,750 of them reference × reference, and confirmed against the signed stage-1
`qualification.json` of all four models, each recording
`pairs=4910, kind_pairs=45, witnesses_verified=true`.

## 2026-08-20 — the Gate-2 calibration screen: the registered prompt cannot start, and the registered reference pool was length-falsified

**What changed.** Nothing registered. A third non-confirmatory screen
(`dci1/src/cal_screen_v4/`, evidence at `dci1/evidence/cal-screen-v4/`, main-arm
protocol hash `fd49e5d4…` with per-model hashes for the three later arms) ran
the §12.3, §12.4 and §13.2 procedures on the **registered calibration sample** —
the 96 solo-calibration topics at the registered M_cal = 4 — which is the sample
§13.2 admits against and which no earlier screen had used. Same standing as the
FORM × STEM, B-grid and B+R work: design evidence, non-confirmatory, refused by
the v4 positive-admission guard, entering no v4 estimator.

The registered code does the deciding. `cal_screen_v4/admission.py` runs §13.2
and is required to reproduce `dci1v4.stages.gates.admit_family` byte for byte,
reason strings included, over a constructed input on RF1;
`dci1v4.stages.gates.select_severity` performs §12.3 selection itself. The
`current`-stem arm renders through `dci1v4.design.prompts.render`, asserted
byte-identical at zero, one and two constraints, so §12.4's finding is a
statement about the registered design and not about a lookalike.

**Which results are affected.**

1. **§12.4 regime adequacy, on the registered basis.** B's realised solo vacuity
   rate under the **registered prompt** is **at least 0.208, and up to 0.870**,
   at **every** rung of m ∈ {7,…,12} on **all four** models, against a maximum
   of 0.10. (Per-model minima 0.339 / 0.208 / 0.312 / 0.659.) There is no m
   that could pass. Every replication returns `REGIME_NOT_FOUND` before any
   reference question is reached. Under a uniform 60–120 word instruction the
   same cells are 0.000–0.060 and every rung passes. This replicates the B-grid
   screen's 24-topic reading on the sample the gate is actually evaluated on.
2. **The registered reference pool is not falsified — it was length-falsified.**
   Under the floored stem, on the calibration set, registered families clear
   §13.2 conditions 1 and 6 simultaneously on every model, with solo vacuity of
   0.000 at essentially every rung, against 0 of 64 under the current stem.
   Counting families with a rung clearing conditions 1 and 6 at the same
   severity: **E2B 3 (RF2, RF3, RF8), E4B 4 (RF2, RF3, RF6, RF8), qwen3-4b 1
   (RF7), qwen3-4b-instruct-2507 4 (RF1, RF2, RF3, RF7)**. Three of four models
   reach the §13.2 requirement of three **from the registered pool alone**, so
   **Amendment B is unnecessary on those three** — and with it the canonical
   verifier hash change, the Gate 1 instrument re-freeze, the boundary-suite
   extension and the §5a witness obligation. Amendment B §1's argument that the
   pool "crosses A's compliance level *only* through the vacuity channel" is
   true under the current stem and false under the floored one.
3. **Amendment C should be per-model, not global.** Under the floored stem the
   registered focal grid supplies an in-band m\* on three of four models — E2B
   m = 10, E4B m = 9, qwen3-4b-instruct-2507 m = 10 — and only qwen3-4b returns
   `FOCAL_RANGE_EXHAUSTED`. On qwen3-4b-instruct-2507 a global extension is
   actively harmful: §12.3 moves m\* from 10 to 11, and 10 is the only rung on
   any model feasible under both readings of §12.4's graded clause. Recorded as
   a superseding note in `user-notes/DCI1_v4_amendment_C_focal_grid.md`.
4. **§13.2 condition 2 decides substantially on noise.** Its input is a §12.2
   measurement — 24 topics at one draw — and the median paired standard error of
   the quantity it bounds at 0.15 is **0.10–0.12** on the FORM × STEM screen's
   own floored rows, so a truly matched reference is rejected about a fifth of
   the time. On qwen3-4b it rejects CR4:13 and CR6:10, whose calibration-set
   distances from A are −0.042 and −0.013. Four dispositions are computed and
   all four reported: as registered; applied only where an input exists;
   with the input measured at M_cal on the same 24 topics; and switched off as a
   §23-style sensitivity. **No reference decision rests on the last one.**
   Measuring condition 2's input at M_cal moves A's pre-screen anchor by −0.114,
   +0.136, +0.156 and −0.073 across the four models and swings the
   admitted-family count **7 → 3, 5 → 6, 3 → 5, 7 → 4**. On qwen3-4b the M_cal
   count equals the condition-2-off count exactly. The criterion is moving
   because its reference point is moving, in both directions, on a quantity
   whose single-draw standard error is about 0.10 against a caliper of 0.15.
   The matrix screen uses the **registered-precision** disposition, not the
   better-measured one: §12.2 registers one draw, and letting a screen-invented
   precision upgrade choose the design would be the screen deciding a protocol
   question.
5. **Response length.** Under the floored stem the solo cells of A, B, the
   candidates and the registered pool sit within a factor of ~1.5 of each other
   in median words, against the 5.1–5.6× separation in the B+R pilot's Δ. The
   stem is therefore what puts the two cells whose difference is Δ_R into a
   common length regime — see the same-day entry on the pilot.

**Comparability.** Screen rows are NOT comparable with registered v4 evidence and
must never be pooled with it: a different seed root (202608220, domain
`calscreen:gen:v1`, a distinct stage label per arm) and, in every arm but one, a
different prompt template. The `current`-stem B cells are byte-identical in
construction to the registered ones, which is what licenses the §12.4 reading.

**What is not adopted.** Nothing. Amendments A, B and C remain drafts; the
registered pool, ladders, calipers, grids, bands and thresholds are unchanged,
and a test asserts it.

---

## 2026-08-20 — the screens now report the registered §17.4 vacuity bound, not only the restriction

**What changed.** `fs_screen_v4.analysis.b_side` and
`bgrid_screen_v4.analysis.d_b_from_a` gained `D_B_from_A_forced`,
`b_solo_forced` and `b_composed_forced`. The existing `D_B_from_A_raw` and
`D_B_from_A_long_only` are unchanged, and no pre-existing value in either
`results.json` moved — the regeneration is purely additive apart from the
`collider_caveat` text, which now names the registered alternative.

**Why.** `D_B_from_A_long_only` **drops** rows failing the §9.3 non-vacuity
predicate, separately in each arm. §9.3 registers the opposite operation and
says why in terms: vacuous passes count as passes in the primary estimand
"because response shortening under composition is a candidate mechanism rather
than a nuisance, and removing them would condition on a consequence of the
treatment", and they are handled by "the registered partial-identification
recomputation of §17.4, in which every primary estimand is recomputed with all
vacuous passes forced to failures". The restriction is a collider-conditioned
sub-population; the forcing is the registered bound. Both are now reported and
labelled.

**What it shows, and it is not small.** On the FORM × STEM screen's own rows:

| model | stem | raw | §17.4 forced | ≥20 w only | vacuous share |
|---|---|---:|---:|---:|---:|
| E2B | current | +0.375 | **+0.000** | +0.250 | 0.474 |
| E2B | floored | +0.208 | **+0.208** | +0.208 | 0.000 |
| E4B | current | +0.333 | **+0.042** | +0.230 | 0.389 |
| E4B | floored | +0.375 | **+0.375** | +0.375 | 0.000 |
| Qwen3-4B | current | +0.125 | **−0.042** | −0.071 | 1.000 |
| Qwen3-4B | floored | +0.000 | **+0.000** | −0.007 | 0.000 |
| Qwen3-4B-Inst | current | +0.042 | **−0.375** | −0.333 | 0.944 |
| Qwen3-4B-Inst | floored | −0.167 | **−0.208** | −0.199 | 0.167 |

Under the current stem the bound annihilates D(B←A) on E2B and reverses its
sign on both Qwens. Under the floored stem raw and forced are identical on
three of four models. §17.4 licenses a claim only when the primary estimate and
the forced recomputation license the same claim, so **under the current stem
this axis is unresolved by rule and under the floored stem it is not.** That is
a third argument for Amendment A, independent of the reference pool and of the
focal grid.

**Which results are affected.** No screen verdict changes: the §2.4 reference
and B-side criteria, the §1.4 B-grid verdict and every compliance figure are
computed from quantities that did not move. What changes is that a reader can
no longer take the ≥20-word column as a corrected estimate — the registered
bound now sits beside it, and on the current stem it disagrees.

**Provenance.** The objection is `dci-79`'s, raised against its own earlier
sensitivity analysis of the B+R pilot: it had tested vacuity by restricting to
≥20-word responses (Δ_R +0.343 → +0.348, +0.375 → +0.360, apparently unmoved),
which drops 36% of the B+R arm and 0% of the A+B arm. Under §17.4's forcing
Δ_R is **+0.095** and **+0.068**, both below the 0.10 generic-load threshold.
Recomputed independently here from the raw pilot rows and the registered
verifier: +0.0952 and +0.0678, and the restriction drops 36.3% against 0.1%.
The movement is entirely in `P(B|R̄)` (0.688 → 0.439, 0.819 → 0.512); `P(B|A)`
does not move at all (0.3442 → 0.3441, 0.4443 → 0.4443), because the A+B
responses average 128–139 words and are never vacuous.

**Consequence for the pilot's headline.** The frozen pilot result
`dci1/reports/br_pilot_v4/result.json` is untouched and its raw Δ_R stands as
recorded. But raw licenses PAIR_SPECIFIC (> 0.25) and the §17.4 bound licenses
generic load (< 0.10), so under §17.4 the correct disposition is **the axis
reported unresolved with both bounds**, not either reading alone. The earlier
`CHANGES_SCIENTIFIC.md` characterisation "Δ is not a vacuity artifact (holds at
≥20 words)" rested on the restriction and should not be quoted.

## 2026-08-20 — the pairwise-matrix screen: Δ_R, Ξ, the reciprocal losses and the companion-difficulty relation, estimated for the first time

**What changed.** Nothing registered. A fourth non-confirmatory screen
(`dci1/src/matrix_screen_v4/`, evidence at `dci1/evidence/matrix-screen-v4/`,
per-model protocol hashes in `dci1/reports/matrix_screen_v4/`) ran the
registered §8.1 cell set — five solo cells and ten unordered pairs in both
orders — plus a V5 difficulty-spanning arm, a production-class companion arm and
the §25 unconstrained cell, on 120 blocks at the registered M = 4 under the
floored stem. Same standing as every other screen: design evidence,
non-confirmatory, refused by the positive-admission guard, entering no v4
estimator.

**Why it is here.** Four quantities that bear directly on the scientific
question had never been estimated in this constraint vocabulary by any stage of
this study: `Δ_R`, `Ξ`, `D(R_j←A)` and the companion-difficulty → `D(B←companion)`
relation. Check C12 records the last-but-one as `BLOCKED`; the FORM × STEM report
says the same from the other side. The B+R pilot has `D(R_j←B)` and no
reference-on-reference cell; v3 has neither.

**The topic decision, recorded because it touches §6.2.** 120 blocks: the 24
pre-screen topics and the 96 solo-calibration topics. The 24
composed-validation topics are **excluded** — §13.6 evaluates every registered
composed cell type on exactly those topics at exactly this M_cal, and generating
composed cells there first would make Gate 4 a check of cells it had already
seen. Using solo(96) for composed cells is outside §6.2's literal wording; the
frozen protocol records the basis in full, including that the researcher's
ratification reached this session **relayed by a peer session rather than
directly**. Every quantity is also reported on the 24 pre-screen blocks alone,
which are disjoint from the 96 the reference severities were selected on and
need no ratification.

**The safeguard.** The reference set, n\*, m\*, the spanning rungs and the class
companion are inputs to this screen and outputs of the calibration screen, hashed
into the frozen protocol before generation, with an explicit bar on revising any
of them on this screen's evidence (§13.3).

**What it cannot support.** No L1, L2 or L3 statement: §17.3's precision
preconditions need 384 blocks. At 120 blocks Δ_R's projected half-width is
0.059–0.063 against a precondition of 0.05, and **Ξ's is 0.111–0.116 against
thresholds of 0.10 and 0.25** — it can show sign and rough size and cannot
settle outcome specificity. (Achieved half-widths came in at roughly half the
projection — 0.032–0.045 for Δ_R, 0.037–0.055 for Ξ — because measured
intra-block ρ is 0.53–0.69 against the 0.5 assumed. Δ_R therefore *meets*
§17.3's 0.05 width precondition numerically. This changes nothing: the
preconditions are conjunctive with 384 confirmatory blocks, an approved Gate 1
and a frozen verifier hash, none of which exist. Recorded so the pre-stated
projection is not quoted as the achieved precision.) The reference set is provisional: if Gate 3 later
admits different families, every per-reference number here is about constraints
that are not in the study.

**What it found.** 64,800 generations, 10,000-resample block bootstrap, readings
fixed in `dci1/reports/matrix_screen_v4/REPORT.md` §7b before any cell was
scored.

- **Δ_R is small and, for the first time in this study, resolved.** +0.048
  [+0.009, +0.087] on E2B, +0.101 [+0.056, +0.146] on E4B, +0.011
  [−0.020, +0.044] on qwen3-4b, −0.024 [−0.067, +0.019] on
  qwen3-4b-instruct-2507. Three of four lie entirely within the ±0.10
  equivalence band; E4B spans the 0.10 generic-load threshold and is
  **unresolved at the achieved precision**. None approaches 0.25.
- **§17.4 licenses the reading rather than voiding it.** Compliance and
  vacuity-forced Δ_R agree on all four models (+0.048, +0.101, +0.007, −0.053),
  landing in the same §7b row, because floored-stem calibration vacuity runs
  0.000–0.060. This is the first axis in the study to satisfy §17.4's
  agreement rule; under the *registered* stem the FORM × STEM screen failed it.
- **Constraint class dominates companion identity.** A production-class
  companion costs B **+0.601** (E2B, CL7:80) and **+0.632** (E4B, CL8:25) of its
  compliance where A costs +0.086 and +0.228, so Δ_class is **−0.515** and
  **−0.404**: A is the *gentler* production companion by five- to seven-fold.
  On qwen3-4b-instruct-2507 Δ_class is +0.087 [+0.046, +0.130], inside the
  equivalence band. qwen3-4b has no class arm (its Δ_R₂ is the class contrast).
- **A's excess over the companion-difficulty line is a length effect.** Residual
  from the difficulty line +0.055 and +0.098 on the Gemmas; refit on the length
  shift each companion induces and A's residual is **−0.010, +0.010, −0.006,
  +0.008** — within ±0.010 on all four models. Reached independently of, and
  agreeing with, the B+R pilot re-analysis entry above. Length is reported
  beside the estimand and never inside it (§22).
- **Ξ does not support pair specificity.** −0.036 (E2B) and −0.009 (E4B): §7b's
  "A damages the references about as much as it damages B" row, an A-general /
  constraint-class reading. Positive on the Qwens (+0.131, +0.090) only because
  A *improves* reference compliance there (D(R̄←A) = −0.095, −0.180) while
  D(B←A) is itself negative (−0.039, −0.095). §25 accidental compliance is
  0.52–0.89 for the references against 0.000 for A, so the reference side is
  near-ceiling.
- **New and unregistered: a focal-position effect larger than the identity
  effect.** B loses **0.288** (E2B) and **0.350** (E4B) of its compliance purely
  by being stated second; A shows none (|effect| ≤ 0.063). Consequently Δ_R
  computed within a single order configuration **changes sign on all four
  models** (E2B +0.326 vs −0.231; E4B +0.450 vs −0.249), because §8.4's
  registered order puts the focal constraint in different positions in the
  A-cell and the R-cells. Pooled Δ_R balances this; a single-order Δ_R does not.

**Which results this affects, and comparability.** No existing number changes.
Nothing registered is amended. The entry records four quantities estimated for
the first time and one channel — focal position — that no prior stage of this
study measured or controlled for. Prior single-order or order-unbalanced
estimates in this constraint vocabulary are **not comparable** to a pooled Δ_R
and should not be read as identity effects; §8.1 already mandates both orders
for the confirmatory design, and this screen is the evidence for why that
requirement is load-bearing rather than precautionary.

**Provenance.** `dci1/src/matrix_screen_v4/`, rows at
`dci1/evidence/matrix-screen-v4/`, per-model protocol hashes frozen before
generation (E2B `54d5d61c60b2…`, E4B `ba2b12d82497…`, qwen3-4b `78733f69c99a…`,
qwen3-4b-instruct-2507 `931cae4a5935…`), analysis in
`dci1/reports/matrix_screen_v4/results.json`, report in the sibling `REPORT.md`.

## 2026-08-20 — the matrix screen's V5 and length lines were fitted through A, and A's length residual is not identified at all

**What changed.** `dci1/src/matrix_screen_v4/analysis.py`. Both the V5
companion-difficulty line and the response-length line were fitted on the
companions with `arm in ("matched", "spanning")` — a set that **includes A** —
and the resulting line was then used to predict A and report A's residual from
it. The keys were even named `line_fitted_on_non_A_companions`, which was
false. Both fits now exclude A, the key is
`line_fitted_on_budget_companions_excluding_A`, and each result carries a new
`A_within_support_of_fit` block recording whether A's predictor value lies
inside the range the line was actually fitted over.

**Why it matters.** Predicting a point from a fit containing that point is
circular, and the bias is not small when the point carries leverage. A is the
only companion in the pool that substantially changes response length, so on the
length line A was the sole point in its region and the line was effectively
pinned to it.

**Which numbers change.** Only the two residuals. Every estimand — `D(B←A)`,
`D(B←R_j)`, `Δ_R`, `Δ_j`, `Ξ`, `Λ`, the reciprocal losses, `Δ_class`, the order
contrasts, both scales, all configurations — is **numerically unchanged**,
verified by diffing the full artifact before and after: maximum absolute change
across every pre-existing estimand is **0.0**.

| residual | as first reported (A in the fit) | corrected (A excluded) | identified? |
|---|---|---|---|
| difficulty, E2B | +0.055 | **+0.067** | yes — A at 0.562 inside [0.335, 0.735] |
| difficulty, E4B | +0.098 | **+0.118** | yes — A at 0.719 inside [0.531, 0.838] |
| difficulty, qwen3-4b | −0.042 | **−0.050** | yes |
| difficulty, qwen3-4b-instruct-2507 | −0.040 | **−0.048** | yes |
| length, E2B | −0.010 | −0.117 | **NO** — others [−9, −1], A **+15** |
| length, E4B | +0.010 | +0.126 | **NO** — others [−8, −3], A **+8** |
| length, qwen3-4b | −0.006 | −0.012 | **NO** — others [−5, +4], A **−8** |
| length, qwen3-4b-instruct-2507 | +0.008 | +0.024 | **NO** — others [−10, −1], A **−16** |

**Consequence for the reading, and a retraction.** The entry above
("the pairwise-matrix screen…") stated: "**A's excess over the
companion-difficulty line is a length effect** … refit on the length shift each
companion induces and A's residual is within ±0.010 on all four models." That
sentence is **withdrawn**. It was an artefact of A's presence in its own fit.
Two corrected statements replace it:

1. **The difficulty residual is identified and larger than first reported.** A
   sits above the difficulty line by +0.067 (E2B) and **+0.118** (E4B) — the
   latter above the 0.10 generic-load threshold — and below it on both Qwens.
   Companion difficulty alone does not account for A on the Gemmas.
2. **The length account is neither confirmed nor refuted — it is
   unidentified.** A's length shift lies outside the range spanned by every
   other companion on all four models, so the line extrapolates to A. Companion
   identity and length shift are **collinear across this companion set**, which
   is the same collinearity the B+R pilot showed between its two arms, now shown
   to hold *within* the matrix design. Separating them requires a companion
   matched to A on length shift; the pool contains none.

**Comparability.** No prior result is invalidated: the affected quantities were
first reported in this session's entry above and nowhere else, and no registered
artifact carries them. `dci1/reports/matrix_screen_v4/REPORT.md` §9.3 and §10,
`RESEARCH_STATE.md` §4f and `dci1/reports/INVESTIGATION_2026-08-20.md` are
corrected in place and each records the supersession.

**Additive at the same time, not a correction.** `D(B←R_j)` — the focal loss
against each reference separately — was computed per block but belonged to no
multiplicity family, so it was never bootstrapped onto the artifact. It is now
reported as the `focal_losses` family. It shows that on E2B an **admitted
registered-pool reference out-damages A**: the paired swap
`Δ_1 = D(B←A) − D(B←CR6:7)` is **−0.078, simultaneous [−0.134, −0.023]**,
entirely below zero, with `D(B←CR6:7)` = +0.165 against `D(B←A)` = +0.086. The
two marginal intervals overlap, so the paired contrast is the estimator that
carries this; on E4B `D(B←RF2:8)` = +0.206 against +0.228, paired
Δ_3 = +0.022 [−0.044, +0.088], which includes zero. Adding this family
changes no existing interval, because those members previously sat in no family
at all.

**Safeguards.** Three tests in
`dci1/tests_v4/test_cal_and_matrix_screen_isolation.py` (now 28) pin the
invariants: both fits must drop A, the old misleading key must not reappear,
`_within_support` must report non-identification, and `focal_losses` must name
quantities the estimator actually produces.

## 2026-08-20 — whether the registered reference pool supplies three references depends on a §13.2 reading the protocol does not fix

**What changed.** Nothing in code or evidence. A qualification to the
calibration-screen entry above, which reported that "three of four models reach
the §13.2 requirement of three **from the registered pool alone**, so **Amendment
B is unnecessary on those three**".

**The gap.** That count is of families clearing §13.2 **conditions 1 and 6**.
Conditions 1 and 6 are two of six, and most of the qualifying rungs have **no
§12.2 pre-screen measurement at all**, so condition 2 — the disjoint 24-topic
confirmation — cannot be evaluated on them. §13.2 does not say whether a
condition that cannot be evaluated abstains or fails, and the answer decides the
conclusion:

| disposition on an unmeasurable condition 2 | E2B | E4B | qwen3-4b | qwen3-4b-instruct-2507 | three from the registered pool? |
|---|---:|---:|---:|---:|---|
| **abstain** — apply condition 2 only where its input exists | 3 | 4 | 1 | 4 | three of four models |
| **reject** — an unmeasurable condition fails | 1 | 2 | 1 | 2 | **no model** |

Under abstain the earlier statement holds as written. Under reject the
registered pool reaches three on no model and **Amendment B is necessary
everywhere**. Both dispositions were computed by the screen and both are on the
artifact — the abstain result at `matrix_reference_set.admitted_families` and
the reject result at `matrix_reference_set.strict_registered_precision`. The
matrix screen declares abstain in its frozen protocol and reports reject beside
it. Neither is a claim.

**Status.** This is a **preregistration ambiguity of the same kind as §12.4's
graded clause**, and it is a researcher decision, not a measurement. Recorded
so the "Amendment B is unnecessary" reading is never quoted without the
disposition it depends on.

**A structural fact that does not depend on the reading.** Three references
exist on every model under every disposition — the enlarged pool admits 5, 3, 3
and 5 families. But on **E4B and qwen3-4b the third slot can only be filled by a
lower-bound (production-class) family**. On those two models the
constraint-class confound therefore moves *inside* the reference set rather than
sitting beside it as a control, and `Δ_R` on qwen3-4b is consequently a mean over
one production and two budget companions. The matrix screen records this on its
frozen protocol and repeats it wherever qwen3-4b's `Δ_R` appears.

**Affected documents.** `dci1/reports/cal_screen_v4/REPORT.md` and
`RESEARCH_STATE.md` §4e now carry both dispositions. The earlier entry stands as
written and is qualified here rather than edited.


---

## 2026-08-20 — §13.2 is not ambiguous; the withdrawal of the entry above

**What changed.** `dci1/src/dci1v4/stages/regime.py` gains
`assert_shortlist_is_measured`, called by `regime_screen_payload`. Five tests in
`tests_v4/test_t6_stage_machine.py`; one fixture corrected. No threshold,
caliper, band, criterion, ladder, wording or grid moves, and the canonical
verifier hash is unchanged at `f5d4f7e74e757769ec43d7007b012168…`. New
artifacts: `dci1/reports/section_13_2_v4/{REPORT.md,resolution.json}`.

**The withdrawal.** The entry above says §13.2 "does not say whether a condition
that cannot be evaluated abstains or fails" and calls it a preregistration
ambiguity and a researcher decision. **That is wrong and is withdrawn.** So is
`dci1/reports/INVESTIGATION_2026-08-20.md`'s statement that this reading is the
study's smallest remaining blocker.

**Why.** §13.2's feasible set is a subset of §12.2's shortlist, and every member
of that shortlist has a pre-screen value by construction:

- §12.2 measures **all 94 reference rungs** — and A's full *n* grid — on the 24
  pre-screen topics, then writes the shortlist of at most three per family;
- §12.3 measures **only shortlisted severities** on the 96 calibration topics;
- §13.2 condition 1 is a caliper on that 96-topic measurement, so a rung §12.3
  never measured cannot be a §13.2 candidate at all.

Condition 2 therefore always has its input. Verified on the four registered
`REGIME_SCREEN` records: 94 of 94 rungs measured on every model, 24 shortlisted
rungs on every model, **none** without a pre-screen value. Where the case is
constructed anyway, `gates.admit_family` already fixes it — a missing value
yields the rejection reason `"no pre-screen measurement"`, executed and recorded
in `resolution.json`. **Abstain is not a reading of §13.2; it was invented by
the screens for their own use.**

**Why the screens met the case.** Both reasons are properties of the screens.
They ran §13.2 over rungs outside the §12.2 shortlist, and their floored-stem
pre-screen came from the FORM × STEM screen, which measured only some rungs
under that stem. Neither is a property of the protocol.

**Comparability.** The screen tables headed *abstain* and *reject* are unchanged
and remain valid as what they are — §13.2 run over a rung set the registered
pipeline would not present to it. They are not two readings of the registered
rule, and neither count is the registered pool's admission result. **The
registered §13.2 has not been run on any model, because Gate 2 has not run.**

**Neutral between the stems.** A stem change re-measures §12.1, §12.2, §12.3 and
§13.2 — Amendment A's own §5.1 says so — and §12.2 re-run under any stem
supplies condition 2's input for all 94 rungs exactly as it does now. This
resolution is therefore not an argument for or against Amendment A.

**Affected documents.** `dci1/reports/cal_screen_v4/REPORT.md` §6,
`dci1/reports/INVESTIGATION_2026-08-20.md`, `RESEARCH_STATE.md` §4e.

---

## 2026-08-20 — the prose-only reimplementation segmented on the wrong character class

**What changed.** `dci1/src/dci1v4/verifiers/independent.py` — the §10.2
independent reimplementation — replaces the regular-expression class
`[^\W\d_]+` with a `unicodedata.category` test. Test
`test_the_two_implementations_use_different_mechanisms` corrected;
`test_both_implementations_read_the_same_character_class` added, comparing the
two segmentations over the whole BMP plus the astral letter blocks.

**The defect.** §7.2 registers "a word is a maximal run of **alphabetic**
characters". `[^\W\d_]` is not that class: it is a word character that is
neither a decimal digit nor an underscore, and it additionally admits **1,151
characters in Unicode categories No and Nl** — subscripts, superscripts,
fractions, Roman numerals. The primary (`verifiers/words.py`, `ch.isalpha()`)
agrees with the registered prose, so **the defect was in the validation
instrument and not in the instrument under study**.

**How it surfaced.** Extending the §10.2 evidence from A and B to the eight
registered families. On the genuine generation `Answer: H₂O` the faulty class
ran `H`, the subscript two and `O` into one word, so **RF3** — at most *q* words
with one letter — read 0 where the primary reads 2. The disagreement is
invisible on A (the target is a fixed string) and on B (the longest word is 6
letters either way at every registered *m*), which is why 14,046 texts at
twelve A-and-B instruments had reported agreement exactly 1.000.

**What is affected, and what is not.**

- **No stored verdict changes.** `independent.py` is outside `SEMANTIC_MODULES`,
  the canonical verifier hash is unchanged, and no execution path lets the
  reimplementation reach a stored verdict (§10.1 invariant 3).
- **No existing estimate changes.** Every screen, pilot and v3 number was
  produced by the primary.
- **The A-and-B §10.2 line is re-verified, not invalidated.** Re-run under the
  corrected module over the same 14,046 texts: agreement exactly 1.000 on all
  twelve instruments, no disagreements. `reports/gate1_v4/section_10_2.json`
  stands as written.
- **The independence argument is preserved.** The primary walks characters
  against `str.isalpha`; the reimplementation groups runs against
  `unicodedata.category`. Python defines `str.isalpha` as general category Lm,
  Lt, Lu, Ll or Lo, so the two reach the same registered property by routes that
  share no code, and a test now checks they agree character by character rather
  than pinning a pattern literal.

**A fixture had encoded the defect as the expectation.**
`test_the_two_implementations_use_different_mechanisms` asserted
`independent._WORD.pattern == r"[^\W\d_]+"`. The registered prose is the
reference and the primary agrees with it, so correcting the code required
correcting the fixture. That is recorded here rather than done silently.

**Construct note, unresolved and out of scope.** Whether splitting `H₂O` into
`H` and `O` is the right operationalisation of "word" is §10.5's third question,
which §9.3 and §24 bound and this study does not resolve. What is settled here
is only that both implementations now compute the rule §7.2 registers.

---

## 2026-08-20 — §13.2's caliper matches on raw solo compliance; §25 already measured why that is not comparable

**What changed.** Nothing in code, evidence or any estimate. A derived analysis
over artifacts that already exist:
`dci1/reports/section_13_2_v4/instructed_compliance.json`, produced by
`dci1/tools/instructed_compliance_v4.py`.

**The observation.** §13.1 says the reference estimates "what would composing B
with a **comparable** non-A companion have cost", and §13.2 operationalises
comparable as raw solo compliance within 0.10 of A's. §25 separately measures
the rate at which an answer carrying **no constraint at all** satisfies each
constraint by chance, records it, and does not feed it into admission. Netting
the second out of the first, `(solo − chance)/(1 − chance)`, on the pairwise
matrix screen's own reference sets:

| model | A solo → instructed | R₁ | R₂ | R₃ |
|---|---|---|---|---|
| E2B | 0.562 → **0.562** | 0.644 → 0.071 | 0.644 → 0.266 | 0.598 → 0.040 |
| E4B | 0.719 → **0.719** | 0.744 → 0.320 | 0.742 → 0.421 | 0.642 → **−0.550** |
| Qwen3-4B | 0.710 → **0.710** | 0.698 → 0.249 | 0.740 → 0.150 | 0.640 → 0.626 |
| Qwen3-4B-Inst | 0.592 → **0.592** | 0.623 → 0.210 | 0.633 → **−2.321** | 0.610 → 0.600 |

**Twelve of twelve references are matched to A on solo compliance; two of twelve
on instructed compliance; two are anti-productive**, meaning stating the
constraint makes the model satisfy it less often than not stating it.

**Why it is structural.** A is an exact-count production constraint, so an
unconstrained answer essentially never satisfies it and A's chance rate is
0.000 on all four models. B and all eight registered families are prefix-closed
`S ≤ q` budgets and are satisfied by chance often. The caliper therefore equates
companions that differ in how much of their compliance the instruction produced,
and the divergence tracks the production/budget divide rather than the model.
This is the same prefix-closure asymmetry already on the record, now measured on
the matching criterion itself.

**Direction of bias, and it is the conservative direction.** A reference whose
instructed compliance is near zero is, for most items, not a binding second
instruction, so `D(B←R_j)` approaches the cost of composing B with an inert
sentence and `Δ_R` is biased **upward**. The screen's `Δ_R` is small on every
model regardless, so the bias runs against the positive reading rather than
producing it.

**What this is not.** No quantity is adjusted, reweighted or re-estimated; no
new matching criterion is proposed; no amendment is decided. The reference sets
above are the calibration screen's, not Gate 3's, and Gate 3 has not run. The
analysis reads no delivery loss, no composed contrast and no outcome, and could
have been run before any composed cell was generated.

**Affected documents.** `dci1/reports/ENDPOINT_2026-08-20.md` §5 and §6, where
it is added as a researcher decision that — unlike the amendment decisions —
is settleable from §25's registered measurement with no new generation.

## 2026-08-21 — DCI-1 v4r3 amendment R3: the candidate library is extended

**What changed.** §7.0's candidate grammar gains six counted statistics
(`t_initial`, `s_final`, `vowel_initial`, `sentence`, `marker_thus`,
`semicolon`), six feature groups, a fifth predicate form (exact count,
`S == q`, production class) and ten families (`RF9`–`RF12`, `CR9`–`CR12`
as budget references; `CX1`–`CX2` as exact-count class controls). Registered
prospectively as `user-notes/DCI1_preregistration_v4r3.md` §7.0-R3 and changelog
entry C27, before any solo compliance of any added family was measured.

Two witness-construction inputs moved as a consequence and are part of the same
change: the filler corpus (`topic` and `unit` carried the new `t_initial` and
`vowel_initial` features) and two breaking words (`o` and `area`, both
vowel-initial). Both are now checked by executable assertions rather than by
inspection.

**Which results are affected.** The canonical verifier hash moves from
`1b90bfe9…` to the R3 hash, so the v4r3 registration manifest is superseded and
re-signed, and the §10.2 declared instrument population goes from 348 to 584
instances over 164 boundary cases. **The 348-instrument Gate 1 evidence does not
cover the ten added families and is not claimed to**; the whole population is
re-certified at the new hash.

**Comparability.** Old and new stay comparable for every family that existed
before: no row is regenerated, no row is rescored, and no statistic of the
original nine numerators returns a different value on any text. The added
families are measured in their own §12.2 screen on the same 24 development
topics at the same completion cap. `dci1/reports/dci1v4r3/expansion_diagnosis.json`
was computed against the pre-R3 library and remains the record of why R3 exists;
its numbers are not comparable with a post-R3 coverage report and are not meant
to be.

## 2026-08-21 — v4r3: Gate 1's measurement criterion replaced (§10.7-R5)

**What changed.** §18 stage 4 required *§10.2 for every verifier in the final
instrument population, **plus §10.3 or §10.4***. Amendment §10.7-R5 replaces
that with *§10.2 **plus §10.7-R5 A–E***: a specification audit, deterministic
implementation validation, independent reimplementation, adversarial/boundary/
**mutation** validation, and provenance/hash binding. Ten conditions, none of
them a human or autorater agreement threshold. §10.3, §10.4, §10.4-R and
§10.4-R2 are reclassified **supplementary/diagnostic** and are no longer
mandatory Gate-1 prerequisites.

A fourth measurement basis is registered, `deterministic_measurement_validated`,
and a terminal status, `SPECIFICATION_AMBIGUOUS`. Two hashes are newly bound
into the Gate-1 record: the specification audit and **every model-facing
wording of the final population**, which §10.6 never covered because a wording
cannot move the verifier hash. `run/analysis_run.py` now emits §10.5's scope
sentence on every analysis record, which §10.5 always required and the code did
not do.

**Timing.** Adopted before Gate 2, before any freeze, and before any
confirmatory generation: all four replications stood at `REGIME_SCREEN`, no
`gate1_measurement.json` existed anywhere in the v4r3 tree, and no estimand had
been computed. It is adopted **after** §10.4-R2 failed and because of what that
failure showed, and §31's objection to exactly that is registered inside the
amendment rather than argued away.

**Which results are affected.** No stored number changes. No row is
regenerated, no row is rescored, no threshold, caliper, candidate identity,
seed, estimand, difficulty coordinate or verifier moves; the canonical verifier
hash stays `41edc84c…`. What changes is which rule Gate 1 is decided under, and
therefore what a Gate-1 record means. `reports/dci1v4r3/gate1_decision.json`
records the decision under the **former** rule and is preserved unchanged and
not described as having passed. §10.4-R2 stands **FAILED** under its own
stopping rule; §10.3 stands unavailable; neither is described anywhere as
having succeeded.

**Comparability.** A Gate-1 record written under R5 is not comparable with a v3
or v4r2 Gate-1 record: those rest on §10.2 plus a human or autorater pathway,
and this one does not. Every claim under it carries §10.5's scope sentence
permanently — *the outcomes are verifier-defined and support no claim about
compliance as an independent human would judge it* — so no statement licensed
under R5 is a statement about human-judged compliance. A later completed §10.3
would supersede the basis rather than be blocked by it.

**What the amended gate returned.** `SPECIFICATION_AMBIGUOUS`, failing
condition 8 alone: two of the four wordings of `CP4` and `CP7` state the
severity as a target and name no bound, so the prose does not distinguish the
registered `>= q` from an `== q` reading. Gate 2 is not licensed. The finding
and its two remediation paths are `dci1/DECISIONS_V4R3.md` A14;
`dci1/reports/dci1v4r3/gate1_r5_decision.json`,
`specification_audit.json`, `wording_review.json`, `mutation_validation.json`.
