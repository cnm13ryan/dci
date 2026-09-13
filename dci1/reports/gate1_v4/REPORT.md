# Track 2 — Gate 1 through §10.2 and §10.4

**Gate 1 is NOT approved.** Nothing is sealed, no one-shot artifact is
claimed, no labelling session was started, and no registered evidence was
written. Every artifact below lives under `dci1/reports/gate1_v4/`.

---

## 1. The independence constraint, stated first

The annotator available to this study is the study author. §10.3 requires an
annotator **independent of the design and analysis team**, so its criterion
cannot be met — not by labelling more items, and not by labelling them
better. The registered consequence is explicit and is a permitted outcome:

| step | disposition |
|---|---|
| identification status | `HUMAN_VALIDATION_UNAVAILABLE` |
| §10.3 criterion | **not waived**; routed to §10.4 |
| measurement basis | `autorater_calibration_approved`, on explicit researcher approval |
| every claim | carries the registered §10.5 scope sentence |

**Author-performed labels are diagnostic evidence and §10.4 hierarchy
input.** They are never described as independent validation, in any
artifact, at any point. The v3 record already carries the same disposition
for its 120 author labels and nothing here changes it.

---

## 2. Scope: A and B only

§10.2 requires the full evidence set for every family verifier Gate 3 could
admit. The reference pool is under revision — the registered pool is
falsified and Amendment B is not adopted — so family verifier work would be
spent on families that may not exist. A's exact-count rule and B's
word-length rule are done here in full.

Extending the focal grid changes B's severity grid and not B's rule, so B's
§10.2 work was safe to do before Track 1 reported. It was, and Track 1 does
not disturb it.

---

## 3. §10.2 verifier correctness, for A and B

Artifact: `section_10_2.json`.

### The response pool

| item | value |
|---|---|
| rows read | 16,128 |
| distinct texts | **13,953** |
| pool hash | `ec0462a46d1f35113ee42f80fb3b930b…` |
| provenance | the §12.2 dense ladder screen, all three §12.1 cap screens and the Gate 0 pilot, on all four models, read only |

§10.2 says "every calibration response". Gate 1 is stage 4 and Gate 2 has
not run, so **no calibration response exists yet**. The pool used is every
genuine v4 generation on disk — the largest natural response population
available at Gate 1, roughly twenty times the size of the §10.3 sample. It
is not the calibration pool, and the determinism and reimplementation lines
must be re-run over that pool when it exists. The limitation is recorded on
the artifact itself, not only here.

### The five lines

| line | requirement | result |
|---|---|---|
| **Determinism** | three executions on three separate processes, agreement exactly 1.000 | **1.000** — 28 batches, 84 processes, 167,436 verdicts per process, every batch exactly 1.000 |
| **Boundary suite, A** | ≥ 40 cases, the §24 enumeration, frozen before qualification | **48 cases** (40 carried byte-identically from v3 + 8 authored for v4), agreement **1.0**, 14 coverage categories |
| **Boundary suite, B** | authored for v4 in full, ≥ 40 cases | **45 cases**, all v4-authored, agreement **1.0**, 22 coverage categories |
| **Independent reimplementation** | prose-only second implementation, agreement exactly 1.000 | **1.000** over 14,046 texts × 12 instruments; minimum per-instrument agreement 1.0; zero disagreements |
| **Adversarial corpus** | every enumerated boundary case, with realised frequency in genuine generations | corpus of 372 items; realised incidence computed over all 13,953 natural responses |
| **Carry-over** | names the source, records every hash, refuses on mismatch | **not refused**; 17 symbols byte-identical to the v3 artifacts |

Boundary suite hash `c996a52ecbff834e04268d9b34001910…`, 0 case failures. Canonical verifier hash `f5d4f7e74e757769ec43d7007b012168…`.

**A's boundary coverage:** `adjacent-punctuation`, `capitalisation`, `combining-marks`, `concatenated-copies`, `empty-response`, `hyphenation`, `non-breaking-and-soft-hyphen`, `non-latin-characters`, `repeated-words`, `sentence-boundary-punctuation`, `truncation-mid-word`, `unicode-lookalikes`, `unicode-punctuation`, `zero-width-characters`.

**B's boundary coverage:** `adjacent-punctuation`, `apostrophised-forms`, `capitalisation`, `comma-budget`, `digits-and-symbols-adjacent`, `doubled-letters`, `empty-output`, `extreme-word-length`, `hyphenated-forms`, `initial-letter-b`, `letter-a`, `markdown-emphasis`, `non-latin-script`, `repeated-words`, `sentence-boundary-punctuation`, `single-letter-words`, `single-token-output`, `suffix-ing`, `suffix-y`, `unicode-lookalikes`, `unicode-punctuation`, `zero-width-characters`.

### Carry-over detail

The rule is byte-identity of the construct string, the segmentation source,
the counting source, and the forty case texts with their expectations. All
hold:

| role | symbols |
|---|---|
| `carry_over` | `alpha_runs`, `words_lower`, `TARGET_WORD`, `s0_count`, `s1_count`, `s2_count`, `s3_preprocess`, `s3_count` |
| `compatibility` | `focal_statistic`, `_rf1`, `_rf2`, `_rf3`, `_rf4`, `_rf5`, `_rf6`, `_rf7`, `_rf8` |

The `compatibility` entries are not required by the carry-over rule — B and
the families are authored for v4 — but the identity is what lets check C6
read v3 solo cells as an anchor without re-scoring them under a different
rule.

**§10.2 verdict for A and B: every line met.** `A_and_B_meet_10_2 = True`.

---

## 4. §10.4 autorater pathway, for the A and B classes

Artifact: `section_10_4_development.json`. **Development phase only.**

### What is deliberately not done

| §10.4 step | state |
|---|---|
| single-shot signed freeze | **single-shot; not claimed** |
| one-shot calibration | **one-shot; not claimed** |
| held-out half | derived and hashed, never judged; it stays untouched for the real one-shot calibration |

**Why.** both bind the canonical verifier hash, and Amendment C would change it by changing FOCAL_GRID, which is inside the §10.6 semantic module set. Spending a one-shot on a hash that is likely to be superseded would require an explicit invalidation to recover.

Everything before the freeze is done: the split derivation, the serialised
judge execution, the repeatability check, the paired condition comparison,
and selection under the §10.4 hierarchy as far as the hierarchy can be
carried without human labels.

### The response pool and the split

| item | value |
|---|---|
| items | 1152 (768 A-class, 384 B-class) |
| source | the registered §12.2 dense ladder screen, read only |
| development / calibration | 575 / 577, **disjoint** |
| split hash | `7db4c260b3e2b3a2aa0427bac8777c51…` |

| stratum | items | development | calibration |
|---|---|---|---|
| `A:fail:margin_larger` | 182 | 91 | 91 |
| `A:fail:margin_one` | 196 | 98 | 98 |
| `A:pass` | 390 | 195 | 195 |
| `B:fail:margin_larger` | 53 | 26 | 27 |
| `B:fail:margin_one` | 39 | 19 | 20 |
| `B:pass` | 292 | 146 | 146 |

The paired comparison runs on a stratum-balanced subsample of the
**development half only**: 48 items, 8 `A:fail:margin_larger`, 8 `A:fail:margin_one`, 8 `A:pass`, 8 `B:fail:margin_larger`, 8 `B:fail:margin_one`, 8 `B:pass`, hash `02e9a20fabed41b2…`. Derivation: deterministic round-robin over strata in item-id order across the development half.

### The judging conditions

One condition is one hashed configuration. Two axes were varied: the prompt
version and the rendered reasoning effort. All four run **serialised at
concurrency one** (§10.4, T-15), greedy, cap 2,048, judge
`openai/gpt-oss-20b` at pinned revision `6cee5e81…` from a registry disjoint
from the four study models.

| condition | prompt | effort | config hash |
|---|---|---|---|
| `carried-high` | `gate1-judge/2.0.0` | high | `87763084451f` |
| `carried-medium` | `gate1-judge/2.0.0` | medium | `2e284c67ee3f` |
| `v4prompt-high` | `gate1-judge-v4/1.0.0` | high | `61d9d0f3d42d` |
| `v4prompt-medium` | `gate1-judge-v4/1.0.0` | medium | `df3d3e4eb9bd` |

### Results, paired on the same items

| condition | coverage | truncation | s/item | valid | invalid | refusal |
|---|---|---|---|---|---|---|
| `carried-high` | **0.479** | **0.521** | 81.9 | 23 | 25 | 0 |
| `carried-medium` | **0.938** | **0.042** | 31.7 | 45 | 3 | 0 |
| `v4prompt-high` | **0.875** | **0.125** | 53.2 | 42 | 6 | 0 |
| `v4prompt-medium` | **1.000** | **0.000** | 25.9 | 48 | 0 | 0 |

### Repeatability (criterion 1)

| condition | items | pairwise agreement | exactly repeatable |
|---|---|---|---|
| `carried-high` | 16 | 1.000 | **True** |
| `carried-medium` | 16 | 1.000 | **True** |
| `v4prompt-high` | 16 | 1.000 | **True** |
| `v4prompt-medium` | 16 | 1.000 | **True** |

### Cross-device determinism (additive to criterion 1)

A check none of the four conditions gives on its own: the same items,
the same hashed configuration, the other GPU. Serialised execution at
concurrency one is supposed to make the device irrelevant, and T-15
rests on that. Not a condition, and it takes no part in the selection.

| condition | device | items | labels identical | agreement | device inert |
|---|---|---|---|---|---|
| `v4prompt-high` | 0 | 16 | 16/16 | **1.000** | **True** |

Non-verdicts are compared rather than dropped: a device that changed
*which* items reach a verdict would be a device effect too. The two
invalid-output items agree as well, so even the truncation pattern is
reproduced across cards.

### Selection under the §10.4 hierarchy

The hierarchy is applied in order and a later criterion never overrides
an earlier one. But criterion 2 says "absence of **problematic**
truncation" and criterion 3 "**valid** parsing and coverage" — threshold
words, with no threshold registered. Two readings follow and **they do
not agree on whether criterion 4 is reached**, so both are reported.

#### Reading 1 — ranking

Take the best value at each criterion.

| # | criterion | values | surviving | decided |
|---|---|---|---|---|
| 1 | valid deterministic execution | `carried-high` True, `carried-medium` True, `v4prompt-high` True, `v4prompt-medium` True | `carried-high`, `carried-medium`, `v4prompt-high`, `v4prompt-medium` | no |
| 2 | adequate output cap and absence of problematic truncation | `carried-high` 25/48, `carried-medium` 2/48, `v4prompt-high` 6/48, `v4prompt-medium` 0/48 | `v4prompt-medium` | **yes** |

Surviving: `v4prompt-medium`. Criterion 4 reached: **False**.

#### Reading 2 — threshold

Eliminate only a condition that is *distinguishably* worse than
the best — its 95% Wilson interval not overlapping the best
condition's. Turns the threshold words into a decision without
inventing a constant.

| # | criterion | values | surviving | decided |
|---|---|---|---|---|
| 1 | valid deterministic execution | `carried-high` True, `carried-medium` True, `v4prompt-high` True, `v4prompt-medium` True | `carried-high`, `carried-medium`, `v4prompt-high`, `v4prompt-medium` | no |
| 2 | adequate output cap and absence of problematic truncation | `carried-high` 25/48, `carried-medium` 2/48, `v4prompt-high` 6/48, `v4prompt-medium` 0/48 | `carried-medium`, `v4prompt-high`, `v4prompt-medium` | no |
| 3 | valid parsing and coverage | `carried-medium` 45/48, `v4prompt-high` 42/48, `v4prompt-medium` 48/48 | `carried-medium`, `v4prompt-high`, `v4prompt-medium` | no |
| 4 | agreement with human labels | — | `carried-medium`, `v4prompt-high`, `v4prompt-medium` | no |

Surviving: `carried-medium`, `v4prompt-high`, `v4prompt-medium`. Criterion 4 reached: **True**.

**Both readings agree on `v4prompt-medium`.** Under
the ranking reading it is selected outright at criterion 2; under the
threshold reading it is one of three survivors and criterion 4 decides
between them.

The ranking reading decides on a difference of **two items out of
forty-eight** (`v4prompt-medium` 0/48 against `carried-medium` 2/48),
which is not a distinguishable difference. That is why the threshold
reading is reported beside it rather than as a footnote.

The rejected alternative under both readings is `carried-high`: 25/48
truncated, coverage 0.479. It is the carried v3 prompt at high reasoning
effort, and it is eliminated by a margin nothing else comes close to.

### Agreement with the deterministic verifier

Reported for every condition and **not** a selection criterion — §10.4's
fourth criterion is agreement with *human* labels, and selecting the
judge that best matches the verifier would make the held-out evaluation
circular. It is shown because it says what the truncation numbers do not.

| condition | `A:fail:margin_larger` | `A:fail:margin_one` | `A:pass` | `B:fail:margin_larger` | `B:fail:margin_one` | `B:pass` | overall |
|---|---|---|---|---|---|---|---|
| `carried-high` | -- | 1.000 | 1.000 | 1.000 | 1.000 | 0.750 | **0.957** |
| `carried-medium` | 0.125 | 0.625 | 1.000 | 1.000 | 0.800 | 1.000 | **0.756** |
| `v4prompt-high` | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | **1.000** |
| `v4prompt-medium` | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | **1.000** |

**This is the finding the truncation table hides.** The carried prompt at
medium effort does not merely lose items — when it does return a verdict
it is wrong in a structured way, agreeing with the verifier on only
**0.125** of A-class fail items whose margin is larger than one. That is
the instrument bleed visible in its reasoning transcript: it injects the
constrained token into its own justification and then labels SATISFIES.
Both v4-prompt conditions sit at 1.000 in every stratum.

`carried-high`'s 0.957 is computed on the 23 of 48 items that reached a
verdict at all, so it is not comparable with the others.

### What criterion 4 actually needs

Under the threshold reading three conditions survive to criterion 4.
Conditions that never disagree cannot be separated by any number of
labels, so only the discordant items carry information.

| item | value |
|---|---|
| conditions still alive | `carried-medium`, `v4prompt-high`, `v4prompt-medium` |
| discordant items | **11** |
| by stratum | `A:fail:margin_larger` 7, `A:fail:margin_one` 3, `B:fail:margin_one` 1 |
| matched concordant controls | 11 |
| **total to label** | **22** |
| estimated time | **11–22 minutes** |

`v4prompt-high` and `v4prompt-medium` are discordant on **zero** of
the 42 items where both return a verdict — behaviourally the same
judge. So the whole criterion-4 question is `carried-medium` against
the v4 prompt, on 11 items, 10 of which are A-class fail items —
exactly the stratum where `carried-medium`'s verifier agreement
collapses.

*these are author labels: diagnostic evidence and §10.4 hierarchy input, never independent validation.*

### Discordance between conditions

| pair | items compared | discordant |
|---|---|---|
| carried-high vs carried-medium | 23 | **1** |
| carried-high vs v4prompt-high | 21 | **1** |
| carried-high vs v4prompt-medium | 23 | **1** |
| carried-medium vs v4prompt-high | 39 | **9** |
| carried-medium vs v4prompt-medium | 45 | **11** |
| v4prompt-high vs v4prompt-medium | 42 | **0** |

---

## 5. The sealed final-check set (C4)

### The v3 set

| item | value |
|---|---|
| expected sha256 | `f8831598e275487037e6e51cd85e1df2b33c8e359d13836e500e9ab7b881d7a3` |
| measured sha256 | `f8831598e275487037e6e51cd85e1df2b33c8e359d13836e500e9ab7b881d7a3` |
| **untouched** | **True** |
| verification method | file digest only; no item id was read, displayed or used |

Verified by file digest alone. **No item id from the v3 set was read,
displayed or used.** The seal exists to keep the set from influencing any
decision, and a hash check does not.

### The v4 set

Per C4 the v3 set may not be reused: it was composed for the exact-count
rule alone and cannot exercise the word-length rule or any family verifier.

| item | value |
|---|---|
| state | **PREPARED, NOT SEALED** |
| items | 40 |
| content hash | `4ea2620953da693d53c692493c22cffd…` |
| strata | `A:fail:margin_larger` 7, `A:fail:margin_one` 7, `A:pass` 7, `B:fail:margin_larger` 7, `B:fail:margin_one` 6, `B:pass` 6 |
| reserved before the dev/calibration split | True |
| derivation | deterministic round-robin over the six instrument x class x fail-margin strata in item-id order over the registered §12.2 ladder screen pool |

**It is not sealed, for two reasons.** Sealing is a Gate 1 act and Gate 1
is not approved. And the set is provisional: it covers A and B only, so it
must be re-derived once the reference pool is final — a final-check set that
cannot exercise an admitted instrument is not a final check of it. The
derivation is deterministic, so re-deriving it over the final pool is a
re-run, not a judgement call.

When it is sealed the registered rules apply: sealed at Gate 1 and its hash recorded; opened at most once, after every autorater choice is frozen; never used for tuning; never rerun after a failure to obtain a better result.

---

## 6. Verifier-hash binding (C5)

`tests_v4/test_t8_verifier_binding.py` — **all pass**.

The protected set is the union of **11 entry points**: `ladder_screen`, `solo_calibration`, `reference_admission`, `composed_headroom`, `freeze`, `confirmatory_generation`, `scoring`, `resume_restart`, `analysis`, `unmasking`, `report_generation`.

| required case | result |
|---|---|
| a committed semantic change fails every protected stage closed | **PASSED** |
| an irrelevant source change produces no false mismatch | **PASSED** |
| an unchanged verifier succeeds | **PASSED** |
| reverting succeeds | **PASSED** |
| stored verdict provenance traces to the verifier that produced it | **PASSED** |

Four further cases pass beyond the five required:

- `test_an_unregistered_entry_point_is_refused` — PASSED
- `test_before_gate1_the_binding_records_rather_than_compares` — PASSED
- `test_the_frozen_hash_is_never_silently_updated` — PASSED
- `test_the_protected_set_is_the_union_of_eleven_entry_points` — PASSED
- `test_the_semantic_module_set_covers_graded_scores_and_predicates` — PASSED

Canonical verifier hash `f5d4f7e74e757769ec43d7007b012168…`.

---

## 7. The annotation sample sizing

**No labelling session has been started.** §2.5 requires the author to size
and agree one first, and this is that sizing.

### The population

| stratum | items |
|---|---|
| `A:fail:margin_larger` | 182 |
| `A:fail:margin_one` | 196 |
| `A:pass` | 390 |
| `B:fail:margin_larger` | 53 |
| `B:fail:margin_one` | 39 |
| `B:pass` | 292 |
| **total** | **1152** |

Sampling seed `202608193`. Source: the registered §12.2 ladder
screen, one item per (constraint, response) pair the model actually saw.

### The rate

Measured from this annotator's own v3 sessions rather than assumed: 56 items
in 52.4 minutes and 64 items in 69.2 minutes, median inter-item gaps 49.2 s
and 27.7 s. That is **30–60 seconds per item**.

### The two numbers

| | §10.3 sizing | §10.4 sizing |
|---|---|---|
| rule | min(150, N_c) per class per instrument, fail class split by realised margin | enough paired items to separate the judging conditions |
| items | **692** | the discordant set plus a matched concordant control |
| estimated time | **5.8–11.5 hours** | see §4 |
| what it buys | **nothing Gate 1 can use** — the basis stays `HUMAN_VALIDATION_UNAVAILABLE` however many items are labelled, because the annotator is not independent | the fourth criterion of the §10.4 hierarchy, the only one the judge run cannot decide on its own |

Per-stratum breakdown at the §10.3 rule:

| stratum | population | registered sample | reachable |
|---|---|---|---|
| `A:fail:margin_larger` | 182 | 150 | yes |
| `A:fail:margin_one` | 196 | 150 | yes |
| `A:pass` | 390 | 150 | yes |
| `B:fail:margin_larger` | 53 | 53 | yes |
| `B:fail:margin_one` | 39 | 39 | yes |
| `B:pass` | 292 | 150 | yes |

Every stratum is large enough for the one-sided 95% Wilson upper bound to
reach 0.10 at zero disagreements, which needs n ≥ 25. No stratum
returns `MEASUREMENT_EVIDENCE_INSUFFICIENT` on population grounds.

### Required properties of any session

- blind: no arm, model label, companion, verifier verdict or other annotator's work visible
- tool-assisted: the annotator marks each qualifying feature and the interface tallies the annotator's OWN marks; no automatic detection, highlighting, counting or normalisation
- chained, hash-pinned records
- seeded stratified sample, per instrument
- fail-class stratification by realised margin: exactly one against larger, reported separately

**Why tool-assisted and not automatic.** all four v3 human-to-verifier disagreements were unaided off-by-one counting errors at margin one, and four independent recounts reproduced the verifier every time. Automatic counting would remove the disagreement by removing the measurement.

The v3 tooling under `autorater_forensics/experiments/human_review/`
already has all of these and is reused, not rewritten. Its reviewer-facing
definitions are A-specific (an occurrence-count instruction), so a B-class
definition set has to be authored in the same shape before a B session —
an addition to the tooling, not a change to it.

---

## 8. What remains before Gate 1 can be approved

In order, and none of it is optional:

1. **The reference pool must be final.** §10.2 requires the full evidence
   set for every family verifier Gate 3 could admit. The registered pool is
   falsified; Amendments A, B and C are drafted and none is adopted. Until
   the pool is decided there is no instrument population to validate.
2. **§10.2 for every admitted family verifier.** Determinism, a frozen
   boundary suite of at least forty authored cases each, an independent
   reimplementation, and an adversarial corpus. Nothing carries over: the
   family suites are authored for v4 in full.
3. **Re-run §10.2's determinism and reimplementation over the calibration
   pool** once Gate 2 produces one. The 13,953-response pool used here is
   the pre-screen population, not the calibration population.
4. **The §10.4 fourth criterion.** Author labels on the discordant set,
   sized in §7 and not started.
5. **The single-shot freeze and the one-shot calibration**, against a
   canonical verifier hash that is final. Both are deliberately unclaimed
   here precisely so they are available then.
6. **Seal a v4 final-check set** derived over the final instrument
   population, and record its hash in the Gate 1 record.
7. **Explicit researcher approval** writing
   `measurement_basis = autorater_calibration_approved`, with
   `HUMAN_VALIDATION_UNAVAILABLE` as the identification status and the
   §10.5 scope sentence attached to every claim.

**What this track did settle:** A's exact-count rule and B's word-length
rule are Gate-1-ready on §10.2. C4 and C5 are complete. The judge pathway
is executed and characterised as far as it can be without human labels, and
the carried judge prompt has been shown unusable for the B class before it
could be inherited into a freeze.

---

## 9. Artifacts

| path | contents |
|---|---|
| `reports/gate1_v4/section_10_2.json` | the §10.2 evidence for A and B |
| `reports/gate1_v4/readiness_c4_c5_sizing.json` | C4, C5 and the sizing |
| `reports/gate1_v4/section_10_4_development.json` | the judge pathway |
| `reports/gate1_v4/conditions/*.json` | one file per judging condition |
| `reports/gate1_v4/judge_runs/` | every raw judge run directory |
| `reports/gate1_v4/REPORT.md` | this report |
| `tools/gate1_evidence_v4.py` | executes §10.2 |
| `tools/gate1_readiness_v4.py` | executes C4, C5 and the sizing |
| `tools/gate1_autorater_v4.py` | executes the §10.4 development phase |
| `tests_v4/test_gate1_autorater_config.py` | 12 tests pinning the hashed-configuration invariants |
