# DCI-1 v4 — implementation report

**The protocol is not frozen and no confirmatory generation has run.**

## 1. The v4 root, and what was added

```
dci1/src/dci1v4/            the implementation (77 files)
dci1/tests_v4/              the canonical suite (T1-T14 + anti-regression)
dci1/tools/                 build_topics_v4.py, prefreeze_checks_v4.py,
                            run_stage_v4.py, tests_support.py
dci1/docs/v4_prefreeze/     one JSON per check, C1 to C20
docs/v4_traceability.md     requirement -> code -> test
dci1/evidence/dci1-v4/      registered evidence (gitignored)
dci1/durable_root/dci1-v4/  durable mirror (gitignored)
```

Fourteen commits on `feat/dci1v4-fresh-study`, 123 files changed.

## 2. Nothing historical was modified

`git diff --name-only main..HEAD` touches **zero** files under `dci1/src/dci1v3`,
`dci1/src/dci1`, `dci1/tests_v3`, `dci1/reports/br_pilot_v4`,
`dci1/evidence/dci1-v3` or `dci1/evidence/br-pilot-v4`. The v3 suite passes
unchanged (481 tests, v3 + v4 together).

## 3. Isolation, and how it is enforced

* No scientific import of `dci1v3`, any v2 package, or the pilot tool —
  checked by AST over every module in the package.
* `engine/context.py` refuses at construction any v4 study root that resolves
  inside a v2, v3 or pilot tree, or that contains one.
* The §10.2 carry-over is a **data-level byte comparison**: the v3 files are
  read with `ast.literal_eval`, never imported, never executed, never modified.
* `engine/guards.py` admits an analysis input **positively** — it must prove it
  is a registered v4 artifact — with one sanctioned door, `design_evidence_read`,
  for the checks that must read the v3 cache or the pilot, which stamps every
  result non-confirmatory.
* The §6.1 firewall is static: `protocol/constants.py` performs no filesystem
  access at all, and `models/registry.py` binds no name that reads another
  model's record.

## 4. Infrastructure reused, and why it is study-independent

`exploratory/vllm_backend` only. Its contract module is stdlib-only, imports no
DCI implementation and no torch or vLLM, and carries no scientific assumption:
it receives prompt text and a seed and returns generated text, token counts and
a finish reason. It is wrapped by the v4-owned adapter
`dci1v4/generation/backend.py`, which is the only module in the package that
names it — asserted by a test.

Everything else with a v3 counterpart is reimplemented in v4's namespace:
filesystem primitives, signing, the artifact ledger, the path function, the
transition log, the dispatcher, environment capture, and the annotation
interface.

## 5. Carry-over

`carry_over_record()` verifies 17 symbols byte-identical against the v3 files
and the forty boundary cases byte-identical with a matching specification hash.
Eight of the seventeen are the §10.2 carry-over proper (the construct string,
both segmentation functions, and the four counting functions); nine are
compatibility evidence for the word-length and family statistics.

## 6. Model and backend configuration

Four registered replications, in the registered execution order, each pinned to
a full 40-character revision that is present locally:

| # | model | revision | thinking |
|---|---|---|---|
| 1 | google/gemma-3n-E2B-it | 5e092ebca197… | unavailable |
| 2 | google/gemma-3n-E4B-it | c1221e9c62e3… | unavailable |
| 3 | Qwen/Qwen3-4B | 1cfa9a720891… | **disabled** via `enable_thinking: false` |
| 4 | Qwen/Qwen3-4B-Instruct-2507 | cdbee75f17c0… | unavailable |

Backend vLLM 0.15.1+rocm720, torch 2.9.1+rocm7.2.0, Radeon RX 7900 XTX
(gfx1100), TP=1, bfloat16, enforce-eager, temperature 0.7, top_p 0.9, top_k 50,
single phase, NO_THINKING, offline hub. Judge registry: `openai/gpt-oss-20b`,
disjoint from the four replications and refused as a judge for any of them.

## 7. Test groups

320 tests, all passing; the v3 suite is unaffected.

| group | tests |
|---|---|
| T1 authority and isolation | 12 |
| T2 model execution | 13 |
| T3 constraints, graded, predicates, witnesses | 31 |
| T4 topics, prompts, cells, allocation, row schema | 19 |
| T5 verifiers and measurement | 26 |
| T6 stage machine and gates | 22 |
| T7 cached evidence integrity | 13 |
| T8 verifier-hash binding (the five C5 cases) | 10 |
| T9 statistics | 22 |
| T10 claim ladder | 20 |
| T11 masking | 10 |
| T12 provenance and reporting | 21 |
| T13 pilot, missingness, contamination, provenance | 11 |
| T14 end-to-end, CPU-only and synthetic | 3 |
| anti-regression (v3 / revision 1 / legacy) | 33 |
| statistics additions (F5, S1-S3, Delta^A gates) | 4 |
| instrument contract (pre-existing, updated) | 54 |

## 8. Defects the tests found, and what was done

Each was fixed rather than asserted around.

1. **The registered exact-tie rule was decided by floating point.** §12.3 breaks
   an exact tie with the smaller n. Binary floating point makes |0.75−0.70| and
   |0.65−0.70| unequal in the seventeenth decimal, so an A curve of 0.75/0.65
   selected the *larger* n. Selection keys are now rounded before comparison.
2. **F5 was registered with six members and implemented with four.** The two
   graded-threshold members were missing. Added, with the threshold applied at
   the draw level rather than to a cell mean, and a test that every family's
   membership matches the register exactly.
3. **Gate 1 could pass on `human_validation_unavailable` alone.** §18 passes
   Gate 1 on §10.2 **plus §10.3 or §10.4**; that basis is the state in which
   neither has completed. It now returns MEASUREMENT_EVIDENCE_INSUFFICIENT.
4. **The §6.1 registration manifest did not exist.** Every study-wide rule must
   be fixed in a signed manifest before the first qualification. Implemented;
   qualification now fails closed without it, and fails closed when the running
   code no longer implements what was registered. The evidence tree produced
   before it existed was parked as superseded and re-run.
5. **The root-overlap check refused the registered context itself**, because it
   compared the shared `evidence/` parent rather than the per-study subtree.
6. **The backend plan used the wrong key names**, so the pinned revision never
   reached vLLM and the first real run blocked on an unresolvable snapshot.

## 9. Pre-freeze checks

| Check | Status | Evidence or blocker |
|---|---|---|
| C1 boundary suites, adversarial corpora, independent reimplementations | COMPLETE | 10 instruments; A-side 48 cases (40 carried byte-identical + 8 authored), B-side and each family 45; agreement 1.000 everywhere; three-process determinism 1.000; prose-only reimplementation 1.000; 372-item adversarial corpus exercising every enumerated case |
| C2 graded scores and non-vacuity predicates | COMPLETE | 530 checks, 0 mismatches, both inside the canonical verifier hash |
| C3 annotator availability, autorater comparison | **BLOCKED** | No independent annotator is obtainable by this process, and §10.4 requires *explicit researcher approval* to write the basis. The pathway is implemented and tested; only the judge execution and the approval are outstanding |
| C4 sealed final-check set | COMPLETE | **A new v4 set is required**: v4's instrument population is five primary instruments and the v3 set was composed for the exact-count rule alone. The v3 set stays sealed and is unreachable from the package |
| C5 verifier-hash binding | COMPLETE | 11 entry points; all five regression cases |
| C6 exact solo compliance of the exact-count constraint | COMPLETE | See §10 |
| C7 does a matched reference severity exist | **BLOCKED → partially answered** | See §11 |
| C7b realised companion-difficulty gap is estimable | COMPLETE | Every block carries A's solo cell and every reference solo cell; the estimator reads the same blocks; the 0.15 qualifier is attached by the emitter |
| C8 operating regime for the two Qwen models | **BLOCKED → in progress** | Needs §12 per model |
| C9 witnesses for all ten pairs | COMPLETE | 4,910 pairs over 45 distinct kind pairs, joint satisfiability and both non-entailment directions |
| C10 realised vacuity at the 20-word threshold | **BLOCKED** | Needs Gate 2 / Gate 4 calibration cells |
| C11 accidental compliance and per-cell truncation | **BLOCKED → partially answered** | See §12 |
| C12 re-estimate the variance constants | PARTIAL | See §13 |
| C13 re-score the pilot B+R rows | COMPLETE | 576 rows per model re-scored from raw text under the v4 instrument; agreement **1.000** with the recorded verdicts, 0 severities outside the v4 ladder |
| C14 duplicate-generation rate | PARTIAL | Computed on every cache fill; the realised v4 figure needs v4 generations |
| C15 deprecated-and-foreign guard | COMPLETE | Refuses the legacy corpus, the v3 trees and the pilot cache; positive admission |
| C16 within-block formation of every contrast | COMPLETE | Every term of every contrast is looked up by the same block id; 0 cross-set terms |
| C17 topic authoring and the seeded split | COMPLETE | 624 authored, 528 released, 96 sequestered, split hash recorded |
| C18 the Δ^A identity | COMPLETE | See §14 |
| C19 memo threshold provenance | COMPLETE | Memo hash, quoted §G row 1 lines and both dates recorded in the signed manifest |
| C20 the pilot's non-confirmatory status | COMPLETE | Enforced by the one door every pilot read passes through |

## 10. C6 — the companion-difficulty anchor moves when the estimator is fixed

The change summary's figure took P(A solo) from the v3 confirmatory
target-alone arm and the reference rates from the Gate 2A cells on a different
topic set. Reading `solo:A:<n*>` from the same cache puts A and every reference
on the same 96 topics and the same estimator, which is exactly what C6 asks
for:

| model | v3 n* | A solo at n*, same topics | mean reference − A | v4r2 §13.1 figure |
|---|---|---|---|---|
| E2B | 5 | 0.7083 | **+0.164** | +0.198 |
| E4B | 7 | 0.6875 | **+0.101** | +0.210 |

Both are smaller than the registered figure, E4B substantially. Only 4 of the
32 measured rungs sit within the 0.10 caliper of A on the v3 four-point grid,
which is the quantitative form of "matching to A needs harder severities than
v3 ever selected".

These rows are design evidence. They enter no v4 estimator.

## 11. C7 × C10 — the ladder reaches A, and then the vacuity condition removes every rung

**All four registered replications completed QUALIFIED → GATE_0_APPARATUS →
REGIME_SCREEN.** Every one selected cap 512 and passed.

**C7: the dense ladder does reach A.** Anchored on A at each model's own
pre-screen best, five or six of the eight families carry a rung inside the 0.10
caliper in every model — against 4 of 32 rungs on the v3 four-point grid. The
ladder interiors are what make matching to A possible at all, which is what
C7 asks.

**C10: and not one of those rungs survives §13.2's vacuity condition.**

| model | anchor n | A | families reaching A | matched rungs | surviving condition 6 | mean words | share under 20 |
|---|---:|---:|---:|---:|---:|---:|---:|
| gemma-3n-E2B-it | 4 | 0.667 | 6 | 13 | **0** | 55.7 | 0.466 |
| gemma-3n-E4B-it | 1 | 0.667 | 5 | 9 | **0** | 48.2 | 0.497 |
| Qwen3-4B | 1 | 0.708 | 6 | 24 | **0** | 31.6 | 0.621 |
| Qwen3-4B-Instruct-2507 | 3 | 0.708 | 5 | 18 | **0** | 64.2 | 0.542 |

**Zero of sixty-four matched rungs, in four of four replications, across two
architectures.** Of the 4,873 vacuous passes across all four screens, **seven**
were truncations; the rest are short answers.

The mechanism is structural rather than incidental, and it is measured on
identical prompts:

| model | unconstrained | one constraint | two constraints |
|---|---:|---:|---:|
| gemma-3n-E2B-it | 329 words | 121 | 80 |
| Qwen3-4B | 282 words | 49 | **25** |

Both models write long answers unprompted, so this is constraint-driven
shortening, not a model style — exactly the mediator §22 registers and the
reason §13.3 refuses response length as a matching criterion. A's solo
compliance is low, so matching it needs a restrictive "at most q"; a
restrictive budget constraint is satisfied by writing a shorter answer; and a
shorter answer makes the pass vacuous. §13.2 condition 1 and condition 6 pull
against each other by construction.

**What this is and is not.** These are screening samples: 24 topics, one draw
per cell. §13.2 is evaluated at Gate 2 on 96 topics at M = 4, and the
pre-screen supplies only the shortlist and the §13.2 condition-2 confirmation.
This is not an admission decision. But it reproduces in every registered model,
and if it holds at Gate 2 every replication takes the §8.6 reduced design with
`EXCESS_NOT_IDENTIFIED`, and **L3 — the level carrying the study's
discriminating question — is withheld in all four.**

It bears on three open decisions at once: **V3** (the caliper), **V4** (the
20-word threshold, which §9.3 justifies by a topic space that "asks for sixty
to one hundred and twenty word answers" — true unconstrained, and not what
either family of model produces once a constraint is present), and **V5**
(difficulty-spanning references would not need the reference to be as hard as
A, and would sidestep the tension). Reported, not resolved.

## 11b. C8 — the two Qwen replications, and two grid boundaries

Neither Qwen model's operating regime existed anywhere in the corpus; both
terminated v3 at Gate 2A before the question arose. Both now have curves.

| model | A curve, n = 1…8 | eligible n | B curve, m = 7…10 | eligible m |
|---|---|---|---|---|
| gemma-3n-E2B-it | .33 .38 .46 .67 .50 .42 .46 .42 | 4, 5 | .83 .88 .83 .96 | 7, 8, 9 |
| gemma-3n-E4B-it | .67 .54 .67 .79 .62 .58 .42 .50 | 1–6, 8 | .67 .83 .83 .92 | 7–10 |
| **Qwen3-4B** | .71 .62 .46 .50 .42 .42 .25 .17 | 1, 2, 4 | **.25 .58 .54 .75** | **10 only** |
| Qwen3-4B-Instruct-2507 | .92 .92 .71 .62 .46 .29 .25 .12 | 3, 4 | .71 .79 .92 .88 | 7–10 |

**Qwen3-4B is squeezed at both grid edges**: n\* would be 1, the floor, and m\*
would be 10, the ceiling and the only eligible value. A small shift at Gate 2's
calibration measurement puts it into `TARGET_RANGE_EXHAUSTED` or
`FOCAL_RANGE_EXHAUSTED` — which are statements about the registered grid, never
about the model. Qwen3-4B-Instruct is the mirror image on the A side: 0.92 at
both n = 1 and n = 2, dropping to 0.12 by n = 8.

The thinking-disabled path was also validated on real generations: **zero
`<think>`/`</think>` leakage in 1,200 Qwen3-4B pilot draws**, through the chat
template's own `enable_thinking` switch, as §6.1 requires.

## 12. C11 / T-7 — the completion cap, measured

E2B, the §12.1 cap-selection set (96 prompts, 24 per load):

| cap | truncation, constrained prompts | truncation, zero-constraint prompts | mean words, load 0 / 1 / 2 |
|---:|---:|---:|---:|
| 512 | **0.028** | **0.917** | 329 / 121 / 80 |
| 768 | 0.000 | 0.417 | 454 / 127 / 80 |
| 1024 | 0.000 | 0.250 | 513 / 126 / 80 |

The registered rule selects **512**, the smallest cap whose truncation over the
constrained prompts is at most 0.10, and records the zero-constraint rate of
0.917 separately.

This is trap T-7 measured rather than inferred. Had the zero-constraint prompts
entered the selection, **no registered cap would have qualified** — 0.250 at
1024 is still above 0.10 — and the replication would have terminated
`RESPONSE_LENGTH_INCOMPATIBLE` before measuring anything. v3's no-constraint
arm truncated in 322 and 333 of 384 responses for the same reason. §12.1's
split of the criterion is what keeps the replication alive, and the same rows
show why: one constraint cuts the mean answer from 329 words to 121, and a
second cuts it to 80. That is the §22 mediator, visible before any estimand.

## 13. C12 — the allocation, re-estimated from rows rather than from widths

§16.1 fits φ to the pilot's *reported interval widths* under an assumed
among-reference correlation. Estimating the components directly from the pilot
rows, on the outcome the design uses (B, re-scored under the v4 instrument at
the pilot's own m*):

| quantity | registered | realised |
|---|---|---|
| among-reference correlation | 1 (→ φ=0.27) or 0.5 (→ φ≈0.37) | **0.72** |
| φ, pooled | 0.27 / 0.37 | 0.556 (E2B), 0.441 (E4B) |
| φ, within order stratum | — | **0.395** |

The pooled figure carries the pilot's order variance: the pilot fixes one order
per topic and shares it across that topic's three reference cells, which v4
cannot do because order is within-block. The within-order figure is the one
that transfers.

Running the registered §16.3 menu rule at each:

| φ | half-width of D at 384 × M=4 | qualifies | menu rule selects |
|---|---|---|---|
| 0.27 | 0.0470 | yes | 384 × 4 (38,400) |
| 0.37 | 0.0488 | yes | 384 × 4 (38,400) |
| **0.395 (realised, within order)** | **0.0492** | **yes** | **384 × 4 (38,400)** |
| 0.498 (realised, pooled) | 0.0510 | no | 480 × 4 (48,000) |

**Recommendation for V1, not a decision.** The registered allocation survives
the transferable re-estimate — but by 0.0008 on the half-width of D. The
allocation stops qualifying at φ = 0.44. Given that the estimate comes from two
draws on 96 topics in a different constraint vocabulary, 384 × M=4 sits on the
boundary and 480 × M=4 is the robust choice. The rule selects 384; V1 decides.

## 14. C18 — the demotion argument now rests on the rows

Δ^A computed from the v3 rows under v3's own recorded draw selection
reproduces the recorded `secondary.pooled_swap_effect` exactly:

| model | computed | recorded | identity holds |
|---|---|---|---|
| E2B | −0.009548611 | −0.009548611 | yes |
| E4B | +0.065104167 | +0.065104167 | yes |

Both algebraic forms — mean_j C(A|A+R_j) − C(A|A+B) and F(A|A+B) −
mean_j F(A|A+R_j) — agree to machine precision. The all-draw figures differ
(+0.0639, +0.0737) for the same reason v4r2 gives for the pilot's P(B|A): they
answer a different question. v4 implements no draw selector; v3's selection was
read as recorded data.

## 15. Topics

624 newly authored questions, 52 in each of the twelve declared areas, each
verified against the four §6.2 authoring rules with a banned-vocabulary list
deliberately wider than v3's: v4 registers a comma-count family and an
upper-case-count family, so a question saying *comma* or *capital* would prime
a registered constraint. Six questions were rewritten when the check caught
them.

Zero overlap with the v3 bank, by question text and by content hash, including
the v3 sequestered hashes.

The seeded five-way cut gives 24 / 96 / 24 / 384 / 96, all disjoint, split hash
recorded in the signed manifest. `tools/build_topics_v4.py` is the access
control: 528 released questions enter the package, the 96 sequestered exist to
it only as opaque identities and content hashes, and the authoring source is
retained outside version control.

**Stated limitation.** The authoring process saw all 624. The seal is on the
execution path, which cannot reach 96 of them, not on the author.

## 16. Decisions I did not make, and the one I did

| # | decision | what was done |
|---|---|---|
| V1 | budget and allocation | menu rule implemented and **reported**; §13 above |
| V2 | load-three arm | not implemented; §5 exclusion stands |
| V3 | reference caliper | 0.10 with the Newcombe condition and the 0.15 realised-gap qualifier implemented |
| V4 | non-vacuity threshold | 20 words implemented; never tuned to a rate |
| V5 | matched vs difficulty-spanning | matched only |
| V6 | full or reduced design for the Qwens | **decided mechanically by Gate 3**, per model — the one this task decides |
| V7 | author or reuse topics | 624 authored |
| V8 | annotator availability | reported unavailable; the autorater pathway is implemented and awaits the researcher's explicit approval |
| V9 | second focal-like outcome | not implemented |

## 17. Three interpretation decisions the researcher should see

1. **The family wordings are not the §7.2 table strings.** The caliper is
   against A, whose canonical wording is six words; the table's family
   templates are eleven to twelve. No family stated in the table's own words
   could ever be admitted, at any severity, for any model. Four compact
   wordings per family were authored instead, each checked against the §7.2
   rule statement at every severity, and every one of the 94 registered
   severities now meets the caliper at every registered n.
2. **A configuration is the position of the outcome constraint.** §11.4 says
   Δ-type quantities are position-clean *in both configurations*; that only
   holds under this reading.
3. **The ladder shortlist's anchor** is A at the n whose pre-screen compliance
   is nearest the §12.3 aim, recorded as `anchor_n` on the regime record,
   because n* does not exist until Gate 2.

## 18. What blocks the freeze

* All nine registered open decisions (V1–V9) — the researcher's.
* C3: no independent annotator, and §10.4 requires explicit researcher
  approval to write the measurement basis. **Gate 1 cannot pass without it**,
  which is why Gates 2–4 are unreachable in this task even with GPU time
  available: they are downstream of Gate 1 in the registered sequence.
* C7, C8, C10, C11: real-model measurement at Gate 2 and Gate 4.
* C12: the A-versus-reference correlation is not recoverable from any existing
  corpus; the v4 design supplies it by construction.
* C14: the realised v4 duplicate rate.


## 19. Real-model execution status

Stages were run against the pinned backend in the registered model order,
through the same dispatcher every stage uses, so the §18 preconditions applied
to each: the predecessor's hash and signature, the §10.6 verifier binding, a
clean worktree, and invoked-source membership in the producing commit.

| model | QUALIFIED | GATE_0_APPARATUS | REGIME_SCREEN |
|---|---|---|---|
| gemma-3n-E2B-it | PASS | PASS | PASS (cap 512) |
| gemma-3n-E4B-it | PASS | PASS | PASS (cap 512) |
| Qwen3-4B | PASS | PASS | PASS (cap 512) |
| Qwen3-4B-Instruct-2507 | PASS | PASS | PASS (cap 512) |

**Every pre-confirmatory stage the environment supports has run, in the
registered model order, for all four replications.** Each Gate 0 committed
1,200 cached draws and met all eight §19 acceptance conditions; each regime
screen ran 3 × 96 cap-selection prompts and a 2,544-cell dense ladder. 15,264
real generations in total.

The two cards were run as two independent single-GPU queues — the registered
`tensor_parallel_size` is 1 and stays 1, so parallelism came from running two
models at once, never from splitting one across both.

**Gates 2, 3 and 4 are not reachable in this task even with GPU time
available.** They are downstream of GATE_1_MEASUREMENT in the registered
sequence, and Gate 1 requires §10.3 or §10.4. There is no independent
annotator, and §10.4 ends in *explicit researcher approval* writing the
measurement basis. That is the protocol reserving a decision, not an
implementation gap: the pathway is implemented and tested, and the dispatcher
refuses to run a stage whose predecessor has not passed.
