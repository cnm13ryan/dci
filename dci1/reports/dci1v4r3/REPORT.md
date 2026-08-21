# DCI-1 v4r3, stage 3: what the candidate library delivered

**Protocol:** DCI-1 v4 revision 3, adopted and registered 2026-08-21
(`dci1/DECISIONS_V4R3.md` A0). **Not frozen. No confirmatory data.**
**Stage:** `REGIME_SCREEN` — §12.1's completion cap, §12.2's dense ladder
screen, §12.6's candidate expansion and coverage criterion.
**Topics:** the 24 pre-screen topics only, on every model. The
composed-validation 24, the confirmatory 384 and the sequestered 96 are
untouched, audited over generated rows (`topic_audit.json`).
**Canonical verifier hash:** `1b90bfe9c2bf1436f1c840e053b1f9843ddc7c54b89f02d2668da517a5518947`.

This report states what the stage measured. It licenses no claim about the
effect of companion identity: no composed cell exists, and none may exist
before Gate 1.

---

## 1. The headline

**One replication of four can carry the difficulty spectrum.**

| Model | cap | rows | ι_A | n | eligible rungs | families | groups above ι_A | expansion rounds | §12.6 coverage |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| gemma-3n-e2b-it | 512 | 4,920 | 0.526 | 1 | 54 | 13 | 4 | 0 | **PASS** |
| gemma-3n-e4b-it | 512 | 6,048 | 0.750 | 3 | 59 | 12 | 2 | 2 | fail: C2, C4 |
| qwen3-4b | 512 | 6,048 | 0.750 | 2 | 67 | 13 | 3 | 2 | fail: C4 |
| qwen3-4b-instruct-2507 | 512 | 6,048 | 0.542 | 5 | 39 | 11 | 3 | 2 | fail: C4 |

The three failures record `DIFFICULTY_SUPPORT_NOT_IDENTIFIED` **at design
time** and run §8.6's **no-spectrum** variant: 29 cells instead of 47, with the
core matrix, the class arm and the load-0 cell intact. $\Delta_R$,
$\Delta_j$, $\Lambda$, $\Xi$, the reciprocal reference effects and
$\Delta_{\text{class}}$ remain identified and remain primary; only
$\delta_{\text{diff}}$ is withheld. Dropping the core matrix as well would
discard identified estimands because an unidentified one is unavailable.

That is a registered outcome, not a fallback: no band was widened, no vacuity
ceiling lowered and no severity authored to reach coverage.

If Gate 3 reproduces this picture on the calibration sample, the confirmatory
study costs **411,648** generations rather than 577,536 — one replication at 47
cells and three at 29.

**Cost of learning this: 4,920–6,048 generations per model.** The confirmatory
design is 144,384. §12.6 exists to move this question in front of that spend,
and on three of four models it did.

---

## 2. The v4r2 blocker is fixed, measured under v4r3's own instrument

§12.4 caps $B$'s realised solo vacuity at 0.10. Under the v4r2 prompt the
Gate-2 calibration screen measured **0.208–0.870** at every rung of both grids
on all four models, which is why v4r2 cannot start.

Under §8.5's answer-length stem, on v4r3's own pre-screen:

| Model | max B solo vacuity over m ∈ {7,…,12} |
|---|---:|
| gemma-3n-e2b-it | **0.000** |
| gemma-3n-e4b-it | **0.000** |
| qwen3-4b | **0.000** |
| qwen3-4b-instruct-2507 | **0.042** |

Every rung clears the ceiling on every model. The completion cap is 512 on all
four, with truncation **0.000** at every cap tested.

$B$'s pre-screen solo curve puts an in-band severity inside the *registered*
focal grid on three models (m = 9 on E2B, m = 10 on E4B and on
qwen3-4b-instruct-2507). On qwen3-4b the registered grid tops out at 0.458 and
§12.3's escalation to {11, 12} is required — which is the per-model behaviour
§7.2 registered the escalation rule to produce, rather than a flat widening
that would have moved m* on the other three.

---

## 3. Why coverage fails, and what fails

The binding condition is **C4** on all three failures: at least four feature
groups must contain a family that straddles ι_A with at least three eligible
rungs spanning at least 0.40 in ι.

| Model | groups with an eligible rung above ι_A | groups with a **well-formed straddling** family |
|---|---|---|
| gemma-3n-e2b-it | capital, comma, one_letter, y_final | capital, comma, one_letter, y_final (**4**) |
| gemma-3n-e4b-it | capital, comma | comma (**1**) |
| qwen3-4b | capital, comma, y_final | capital, comma, y_final (**3**) |
| qwen3-4b-instruct-2507 | comma, letter_a, one_letter | letter_a, one_letter (**2**) |

The structure behind it is visible in the per-family table: **a
character-budget family's instructed-compliance curve rarely crosses ι_A with
usable density on both sides.** Most families top out below ι_A; the comma
budget sits uniformly above it. On qwen3-4b, RF5 spans ι 0.810–0.947 entirely
above ι_A = 0.750 while RF7's twelve eligible rungs span 0.125–0.591 entirely
below it. `b_initial` supplies **no** eligible rung at all on the two Qwens, in
either predicate form.

**On qwen3-4b the margin is what binds, not feasibility.** Three groups supply
a well-formed straddling family, which is exactly what §13.6 needs; C4 asks for
four so that a family failing at calibration what it passed at pre-screen does
not by itself force the reduced design. On E4B and qwen3-4b-instruct-2507 even
the bare minimum of three is unmet.

---

## 4. The coordinate, and the finding that matters most

§13.3 registers **instructed compliance** ι = (solo − κ)/(1 − κ) as the
difficulty coordinate and keeps raw solo compliance as a reported secondary.
Running §12.6's criterion on the secondary coordinate:

| Model | registered coordinate | secondary coordinate |
|---|---|---|
| gemma-3n-e2b-it | PASS | PASS |
| gemma-3n-e4b-it | **fail** | PASS |
| qwen3-4b | **fail** | PASS |
| qwen3-4b-instruct-2507 | **fail** | PASS |

**The spectrum is identifiable on raw solo compliance on all four models and on
instructed compliance on one.** That is not an argument for switching
coordinates. It is a measurement of why the coordinate was registered.

The rungs that sit *above* A on the raw coordinate — the ones that would form
the spectrum's upper arm — are largely satisfied without being stated:

| Model | rungs above A on raw solo | of those, **anti-productive** | mean chance compliance of those |
|---|---:|---:|---:|
| gemma-3n-e2b-it | 39 | 21 | 0.689 |
| gemma-3n-e4b-it | 35 | 17 | 0.635 |
| qwen3-4b | 36 | 12 | 0.668 |
| qwen3-4b-instruct-2507 | 77 | 44 | 0.728 |

*Anti-productive* means ι ≤ 0: stating the constraint does not make the model
satisfy it more often than not stating it. **A spectrum built on the secondary
coordinate would have its upper arm made of instructions that do nothing.**

Across the whole measured vocabulary the same pathology is large:
**75/204, 78/251, 84/251 and 106/251** measured constraint instances are
anti-productive — 31% to 42%.

---

## 5. The class arm

Every model admits an eligible class companion **within §13.7's 0.15 match
caliper of ι_A**: CL7:80, CL8:25, CL7:30 and CL7:40 respectively. v4r2 had no
class arm at all, and the pairwise-matrix screen's single production companion
cost B +0.601 and +0.632 where A cost +0.086 and +0.228 — a Δ_class between
companions of wildly different difficulty.

The rate lower bounds registered for this purpose (CP4, CP7) appear among the
matched candidates on three of four models, so the addition earned its place
even where a count lower bound also matched.

`COMPANION_CLASS_NOT_MATCHED` still attaches to every L3 statement, because the
*reference pool* is budget class throughout. What the arm buys is a
difficulty-matched bound on how much of any excess could be a class effect.

---

## 6. Gate 1: every measurement criterion passes; the gate does not

| §10.2 criterion | result |
|---|---|
| three-process determinism | agreement **1.000**, 3 processes × 348 instruments × a declared 800-response sample |
| boundary suites | agreement **1.000**, 136 frozen cases × 348 instruments, suite hash `65e47257782e` |
| independent reimplementation, tier 1 | the nine counted statistics, the word count, $S_0$ and $B$'s statistic, on **every one of the 24,352 responses** — 292,224 comparisons, agreement **1.000** |
| independent reimplementation, tier 2 | the full verdict vector over all 348 instruments — 522,000 vectors on a declared 1,500-response sample that contains the frozen boundary corpus in full, agreement **1.000** |
| segmenter differential | agreement **1.000** over all **1,114,112** Unicode codepoints; exactly one case-folding splitter, `U+0130` |
| §7.5 witnesses | **25,337** realisable pairs; 0 joint-satisfiability and 0 non-entailment failures |
| §7.5 wording suite | **27,840** verdicts, 0 disagreements |
| §24 adversarial corpus | every enumerated phenomenon covered by the 136-case corpus |
| §24 realised frequency | over **24,216** genuine responses: `case_folding_split`, `combining_mark`, `empty`, `fullwidth`, `non_breaking_space`, `single_word`, `soft_hyphen`, `wordless` and `zero_width` were **never observed** |
| §10.2 carry-over | $A$'s v3 chain intact; what is *not* carried is named and reasoned |
| §12.5 topic audit | reserved sets unspent over all 24,216 rows |

**The two-tier split is declared, not implied.** Tier 1 is the half of §10.2
that is about *reading the text* — it is where the U+0130 defect surfaced — and
it runs on every response because it costs one pass per response per
implementation. Tier 2 is 348 times that work per response and can only
disagree where tier 1 does, or where the two implementations read the same
statistic and apply a different predicate; its sample always contains the whole
frozen boundary corpus, so no enumerated phenomenon is sampled away.

**The realised-frequency line is the point of §24, and it is easy to skip.**
Nine enumerated phenomena have realised frequency **zero** in 24,216 genuine
responses — including the case-folding split that §7.0's correction is about.
The instruments are validated on them by construction and by the corpus, and by
the data not at all. Saying so is more useful than a corpus that quietly
implies otherwise.

§10.3 records `HUMAN_VALIDATION_UNAVAILABLE`: no annotator independent of the
design and analysis team exists, and author labels are never described as
independent validation.

### 6.1 §10.4's development phase, and why the pathway is not ready

The §10.4 development phase ran on v4r3's own pool — 22,968 items from the
§12.2 screen, split deterministically into 11,479 development and 11,489
calibration items (disjoint, hash `f91515c3679c`), 18 strata of
*predicate form × verifier class × fail margin*, judged on a stratum-balanced
72-item subsample at concurrency one. The held-out half is hashed and
**never judged**; the single-shot freeze and the one-shot calibration are
**not claimed**.

| §10.4 criterion | v4prompt-medium | v4prompt-high |
|---|---|---|
| 1. valid deterministic execution | exactly repeatable | exactly repeatable |
| 2. adequate output cap, no problematic truncation | **23/72 truncated** | **40/72 truncated** |
| 3. valid parsing and coverage | 0.681 | 0.444 |
| 4. agreement with human labels | outstanding: no annotator | outstanding |
| (reported, never a criterion) agreement with the verifier | 0.918 (n=49) | 0.969 (n=32) |

**Neither condition survives criterion 2, and the selection therefore has no
answer.** Where both do produce a label they agree on 25 of 27 paired items
(0.926).

**The cause is diagnosable and is a property of the enlarged instrument
population.** Truncation is essentially absent on the outcome constraints and
rises with how much counting the rule demands:

| instrument group | v4prompt-medium | v4prompt-high |
|---|---:|---:|
| $A$, exact count of one word | 0/12 | 1/12 |
| $B$, longest word | 0/12 | 4/12 |
| count budget | 6/12 | 6/12 |
| count lower bound | 0/12 | 8/12 |
| rate budget | 8/12 | 9/12 |
| **rate lower bound** | 9/12 | **12/12** |

The judge spends its 2,048-token cap enumerating and counting words to evaluate
a rate, and never reaches a verdict. On the v4r2 pool — $A$ and $B$ alone —
the same `v4prompt-medium` configuration truncated **0 of 48**. The regression
is caused by the pool v4r3 registered, not by the judge configuration drifting.

**What this means for Gate 1.** §10.4 is *not* merely awaiting a signature. Its
criterion 2 is unmet on v4r3's population, and the registered hierarchy stops
there. The obvious repair is a further registered condition with a larger
output cap, or a judge prompt that does not require the judge to enumerate —
both are permitted prospective development, because the single-shot freeze has
not been claimed and nothing here is frozen.

### 6.2 The gate's recorded outcome

`MEASUREMENT_EVIDENCE_INSUFFICIENT`, with one observed failure: the measurement
basis is `human_validation_unavailable`, because §10.3 found no independent
annotator and §10.4 has not been approved. **Two things stand between the study
and Gate 1, in this order**: §10.4's criterion 2, which is an engineering
problem with a diagnosed cause; and then the researcher's explicit approval,
which no agent may write.

---

## 7. Stage order, provenance, and the repair pass (2026-08-21, later)

An evidence audit found four defects. Three were the same shape --- a rule the
preregistration states in prose with nothing on the execution path enforcing
it --- and all four are now repaired.

**The implementation was uncommitted.** Every stage record named producing
commit `6954dd65`, which did not contain `src/dci1v4r3` at all, and §18's
`clean_worktree` and `tracked_implementation` refused the study for exactly
that reason. Committed. §18 stage 1 now **PASSES** and binds to the commit that
contains the code.

**There was no stage machine.** `STAGE_SEQUENCE` existed as a list of strings
and nothing read it, which is how the §12.2 regime screen came to run before
`QUALIFIED` and `GATE_0_APPARATUS` --- not by a decision, but because no guard
existed to refuse it. `dci1v4r3/engine/transitions.py` now enforces in-order,
once, terminal-is-terminal and §18.1's post-freeze rule against the
predecessor's verified hash and signature, and logs every *attempted*
transition including refusals.

The existing screen evidence is recorded `ADOPTED_OUT_OF_ORDER`. Checked
against real state, Gate 1 is refused for the right reason:

    GATE_1_MEASUREMENT: REGIME_SCREEN recorded 'ADOPTED_OUT_OF_ORDER',
    not PASS; GATE_1_MEASUREMENT may not run

The rows are real, they remain registered diagnostic evidence, and every
quantity in sections 1-6 is still re-derivable from them under the frozen
verifier hash each row carries. What they cannot do is satisfy a predecessor
requirement they were generated before the existence of. **The screen must be
re-run in order under the bound commit before Gate 1 can rest on it**, using
the same reserved development topics and the same registered procedure --- not
to seek different rates, but because the ordering is part of what the record
claims.

**§12.1's cap probe leaked a composed outcome.** The probe generates composed
`A + B` prompts by registered design --- a cap has to be adequate where the
answer is hardest to write --- so 72 composed generations per replication went
through the shared scorer and their rows carry `passed` for both constituents.
Nothing read the field and no record contained it, so no reported value moves;
but `D(B <- A)` at `A:8 + B:7` was derivable from stored evidence, and an
unread field is a weaker guarantee than an unreachable one. The probe is now
projected onto §12.1's three registered fields before the cap decision sees it,
later stages read a restricted artifact, and the selection modules are checked
by parsing rather than by running that they cannot name the field at all.

**§18 stage 2 `GATE_0_APPARATUS` is now implemented and walked.** §19's pilot ---
47 cells x 12 topics x M = 4 = 2,256 draws, all eight acceptance conditions,
the mask cycle, byte mutation, durable restore, and a fully redacted result
table carrying a fitted difficulty relation, a support diagnostic and a
`delta_difficulty` row --- runs end to end on the CPU-only synthetic seam. It
has not yet been run for record on a real model.

**The durable mirror held six files.** Fifty-three critical artifacts, every
raw and scored row among them, existed in one copy. `_mirror` had only ever
replicated stage records. Both roots now hold 147 files and the durability gate
passes --- with its limitation stated rather than implied: both roots are local
and on one device, so this establishes that two copies agree and that a restore
works, not off-machine durability.

### 7.1 §10.4 is replaced prospectively (amendment R1, C26)

§10.4's original task asked the judge whether a response obeys a rule. For a
rate predicate that is an enumeration, and the judge exhausted its 2,048-token
cap doing arithmetic without reaching a verdict. §10.4-R asks instead whether
the deterministic *operationalization* --- segmentation convention, numerator,
denominator, derived quantity, direction, threshold, verdict --- faithfully
implements the written instruction, with the arithmetic **shown** rather than
requested.

This is not merely the cheaper repair, and raising the cap was considered and
kept as the registered fallback. §10.2 already shows two independent
implementations agreeing at 1.000 over 24,352 responses; what agreement cannot
show is that either implements the construct the prose describes, since both
could share a misreading. Asking a judge to redo the arithmetic tests the
judge. Asking it to inspect the operationalization tests what §10.2 cannot
reach.

Half the judged cards carry one planted defect from a closed list of six ---
`denominator_swap`, `inequality_flip`, `off_by_one`, `segmentation_drift`,
`numerator_swap`, `vacuity_ignored` --- because a validator handed a correct
derivation and asked whether it is correct can score perfectly by always
agreeing. Sensitivity has a registered floor **per defect kind** as well as
overall, so a validator blind to one whole class cannot pass on the strength of
the others. Every threshold was registered at commit `f657de2`, before any card
was judged.

**The deterministic verifier remains the study's scorer.** No compliance rate,
cell mean, estimand or claim reads anything the validator produces, at any
stage. §10.4's original evidence is retained: it judges a different question,
it is the record of why R1 exists, and the two must never be pooled.

---

## 8. What this stage does not say

- **Nothing about companion identity.** No composed cell exists.
- **Nothing about which severities the study will use.** These are pre-screen
  values on 24 topics at one draw. n\*, m\*, the core references, the spectrum
  and the class companion are Gate 2 and Gate 3 decisions on the 96
  solo-calibration topics at M_cal = 4, and Gate 2 cannot run before Gate 1.
- **Nothing about whether the registered coordinate is the right one.** §33 D6
  closed that decision on evidence *before* these measurements. Reopening it
  now, having seen that the other coordinate delivers coverage, would be
  choosing a coordinate because it produces the design one wants — which is
  what §13.9 exists to prevent.

---

## 9. Artifacts

| | |
|---|---|
| signed registration manifest | `evidence/dci1v4r3/registration/registration_manifest.json` |
| per-model stage record | `evidence/dci1v4r3/<model>/REGIME_SCREEN/regime_record.json` |
| scored rows | `evidence/dci1v4r3/<model>/REGIME_SCREEN/backend_runs/*/scored.jsonl` |
| cross-model readout | `reports/dci1v4r3/regime_summary.json` |
| §10.2 evidence | `reports/dci1v4r3/gate1_evidence.json` |
| Gate 1 outcome | `reports/dci1v4r3/gate1_outcome.json` |
| topic-reservation audit | `reports/dci1v4r3/topic_audit.json` |
| §10.4 development phase | `reports/dci1v4r3/section_10_4_development.json` |
| §18 stage 1 record | `reports/dci1v4r3/qualification.json` |
| tracked evidence inventory | `reports/dci1v4r3/evidence_manifest.json` |

Reproduce with:

```
cd dci1
./.venv/bin/python tools/run_v4r3.py register
./.venv/bin/python tools/run_v4r3.py regime --model <model> --device <n>
./.venv/bin/python tools/v4r3_regime_report.py
./.venv/bin/python tools/v4r3_topic_audit.py
./.venv/bin/python tools/run_v4r3.py gate1
```
