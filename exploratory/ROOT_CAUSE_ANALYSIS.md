# Root-cause analysis — PRs #15, #16, #17

Every entry follows **symptom → reproduction → root cause → affected claims →
fix → regression test → post-fix result**.

Established root causes are separated from hypotheses. Where a defect turned out
to be latent — real, but never triggered by data collected so far — that is
stated with the audit that establishes it, because "we fixed it and no number
moved" is a different scientific position from "we fixed it and the results
changed".

Work spans three worktrees, which are kept separate on purpose. No file was
copied between them; each branch carries its own repair for its own lineage.

| worktree | branch | PR |
|---|---|---|
| `dci-natural-reasoning-headline` | `exp/natural-reasoning-headline` | #15 |
| `dci-cheapest-rocm-study` | `exp/dci-cheapest-rocm-study` | #17 |
| `dci-cross-model` | `exp/cross-model-transport` | #16 |

---

## Summary

Ten reviewed defects, plus two found while reproducing them. Nine are
**latent** — real fail-open paths that the data collected so far never
exercised. Three changed a published artifact.

| # | defect | class | numbers moved? |
|---|---|---|---|
| N1 | shared-seed grid fallback | canonical-data/provenance; replicate-independence | no (both files present) |
| N2 | guards enforced after writing | validity-gate | no (guards passing) |
| N3 | "any thinking at all" overclaim | claim overreach; cap-bound | **yes — figure and doc** |
| N4 | tail sensitivity share and pairing | denominator/aggregation; replicate | **yes — robustness table** |
| R1 | `fillna("")` scores apparatus failures | technical-failure classification; denominator | no (0 technical failures) |
| R2 | verifier merges sentences after abbreviation + opener | verifier/parser | no (0 rows change) |
| X1 | `MODE_SUSPECT` admitted | validity-gate; execution-condition | no (no suspect cell admitted) |
| X2 | Kimi markerless output scored as answer | channel error | no (Kimi never ran) |
| X3 | both arm rates share one denominator | denominator/aggregation | no (arms balanced) |
| X4 | canonical status from line count | canonical-data/provenance | no (runs intact) |
| X5† | results doc cannot be regenerated | provenance/reproducibility | **yes — doc rebuilt** |
| X6† | replicate audit skips malformed groups | replicate-independence | no |

† found while reproducing the reviewed defects, not raised in review.

---

## A. Natural-reasoning worktree (PR #15)

### N1 — the deprecated shared-seed grid was a silent fallback

**Symptom.** `plotdata.load_all_reasoning` preferred `s18_reseeded.jsonl` "when
it exists" and otherwise read `s18_reasoning.jsonl`, whose own surrounding
comment explains why it is deprecated.

**Reproduction.** A run directory containing the deprecated grid and the natural
file but not the re-seeded grid. Before the fix this loaded and concatenated
without complaint; the test asserts `FileNotFoundError`.

The underlying data defect is measured rather than assumed:

```
s18_reasoning.jsonl    390 / 400 replicate pairs byte-identical   (1 seed)
s18_reseeded.jsonl       0 / 400 replicate pairs byte-identical
natural_reasoning.jsonl  0 /  80 replicate pairs byte-identical
```

**Root cause.** The loader ranked availability above validity. `runs/` is
gitignored, so a regenerated or partially transferred directory is exactly the
situation in which the deprecated file is present and the re-seeded one is not —
the fallback was the likely path on a fresh checkout, not a remote one.

**Affected claims.** Every capped-ladder point, had it fired. In the deprecated
grid two draws count once, so intervals are too narrow by roughly √2 and the
capped curve would have been drawn on a different sampling regime from the
natural point beside it.

**Fix.** Missing canonical input is a stop condition. `dci-natural-reasoning-headline@c636b4d`

**Regression test.** `tests/test_canonical_inputs.py` — 4 tests, including one
asserting the fixture still reproduces the shared-seed defect it guards against.

**Post-fix result.** Latent: both files are present, so no published number
moves. `natural_analysis.py` had always hard-coded the correct file; only the
figure path was permissive. That inconsistency is now gone.

### N2 — canonical CSVs were written before the guards were consulted

**Symptom.** `guard()` appended failures to `_FAILURES`; `main()` read that list
on its last line, after all eight canonical CSVs had been written.

**Reproduction.** Monkeypatch `_FAILURES` to non-empty, run `main()` against a
sentinel CSV holding known content, assert the sentinel survives.

**Root cause.** The gate computed the right verdict and enforced it in the wrong
place. The nonzero exit status reaches an operator; the corrupted CSV reaches
every downstream figure script.

**Affected claims.** None realised — all guards currently pass — but any future
guard failure would have published its own corrupted artifacts.

**Fix.** Verdict enforced immediately after `load_canonical`, before `OUT` is
created. `dci-natural-reasoning-headline@cdde134`

**Regression test.** `tests/test_guard_ordering.py` — 3 tests: a failed guard
overwrites nothing, creates nothing, and a clean run still writes all eight.

**Post-fix result.** Latent. `ALL GUARDS PASSED` on the canonical run.

### N3 — "any thinking at all" claimed an untested range, on a truncated condition

**Symptom.** The headline figure asserted *"Any thinking at all fixes this
one"*.

**Reproduction.** Regenerating the canonical curve prints the cap-hit rate per
budget:

| budget | bracket cap-hit | semicolon cap-hit |
|---|---|---|
| 256 | **0.863** | **0.938** |
| 512 | 0.362 | **0.600** |
| 1024 | 0.075 | 0.287 |
| natural | 0.000 | 0.000 |

**Root cause.** Two distinct overreaches. No positive budget below 256 was ever
run, so the claim extrapolated across the entire untested 1–255 range. And 256
is not a small amount of thinking — 86% and 94% of rows were cut off there — so
the cap is part of the treatment, not a budget the model worked inside. The
semicolon peak at 512 (+0.625, the highest point on the chart) is also cap-bound
at 60%.

**Affected claims.** The headline callout, and `COLD_READER_TEST.md`, which
recorded the wording as the resolution of an earlier objection.

**Fix.** Callout now reads *"Gone by the smallest budget tested"*. Materially
cap-bound points (≥50%) are drawn hollow with an on-figure key.
`dci-natural-reasoning-headline@8cac2f0`

**Regression test.** None — this is a wording and rendering change, not a
computation. The cap-hit rates that motivate it are published in
`canonical_capped_and_natural_curve.csv` and asserted by the canonical guards.

**Post-fix result.** No estimate changed. What the figure asserts about the
estimates changed, and the cold-reader record now carries the withdrawal.

### N4 — the advertised tail share was half the share removed, from one arm

**Symptom.** Rows labelled "drop longest 5%" and "10%".

**Reproduction.** Each background cell holds 80 rows. Before the fix:

```
drop longest 5%    rows_kept 78   → 2 of 80 removed = 2.5%
drop longest 10%   rows_kept 76   → 4 of 80 removed = 5%
```

**Root cause.** Two compounding errors. The count was
`int(share * len(natural) / 4)` — a constant 40, unrelated to the cell being
trimmed. And the drop was applied to the pooled cell: the estimator is a paired
focal-minus-reference contrast, focal traces run systematically longer, so the
tail is almost entirely focal. On the adversarial fixture the four longest rows
in a cell are all focal, which the regression test now pins.

**Affected claims.** The published robustness table only, which is descriptive.
No headline estimate depends on it.

**Fix.** Share taken per arm; `rows_kept_focal`/`rows_kept_reference` published
so balance is checkable. `dci-natural-reasoning-headline@74414f3`

**Regression test.** `tests/test_tail_sensitivity.py` — 6 tests.

**Post-fix result.** Table regenerated. Headline unchanged (semicolon +0.400,
bracket +0.000); see the before/after in `SCIENTIFIC_CLAIM_AUDIT.md`. The
corrected version also reveals task loss at the deepest exclusion (n_tasks
20 → 19 and 18) that the pooled drop had concealed.

---

## B. Cheapest-ROCm worktree (PR #17)

### R1 — `fillna("")` turned apparatus failures into target failures

**Symptom.** `score()` opened with `frame["raw_final_answer"].fillna("")`.

**Reproduction.** Score a frame containing a row flagged
`technical_failure=True`; before the fix it received `A_pass=0`,
`A_failure=1.0`, arbitration state `"neither"`, and entered τ.

**Root cause.** The empty string is a valid input to every verifier and every
verifier fails it. Substituting it erased the distinction between "the apparatus
broke" and "the model wrote a non-compliant answer" before any estimand saw the
row.

**Affected claims.** τ, Δ, Γ and every arbitration summary — in principle.

**Fix.** Explicit three-state taxonomy assigned from the harness record before
any verifier runs: `VALID_ANSWER`, `NO_FINAL_ANSWER` (model behaviour — still
scored, because excluding it would condition on a treatment-affected outcome),
`TECHNICAL_FAILURE` (apparatus — NaN, leaves every behavioural estimand).
`dci-cheapest-rocm-study@ece245a`

**Regression test.** `tests/test_generation_states.py` — 10 tests, including one
that adds apparatus failures to a frame and asserts τ is unmoved.

**Post-fix result.** Latent. Audit across all run data: **0 technical failures
in the 47,452 rows carrying the field**, and `raw_final_answer` is present and
non-empty in all 19,850 rows. No published number moves.

### R2 — the sentence verifier merged sentences after an abbreviation

**Symptom.** `_ends_sentence` resolved its ambiguous cases with
`following[0].isupper()`.

**Reproduction.**

```
It ended at 6 p.m. "Tomorrow begins early."   → 1 sentence  (should be 2)
It ended at 6 p.m. (Tomorrow begins early.)   → 1 sentence  (should be 2)
It ended at 6 p.m. *Tomorrow* begins early.   → 1 sentence  (should be 2)
He waited... "Then it began."                 → 1 sentence  (should be 2)
The meeting ran late. "We will resume."       → 2 sentences (control, correct)
```

The ellipsis case was not raised in review; it shares the branch.

**Root cause.** When the next sentence opens with punctuation, `following[0]` is
that punctuation, which is never upper-case, so the boundary was rejected.

**Affected claims.** Potentially every exact-sentence-count outcome, which is
the primary outcome. The framework's sharpest concern applies: a verifier can be
accurate overall and still bias τ if its errors fall differentially across arms.

**Fix.** Capitalisation test looks through a closed set of opening quotes,
brackets and Markdown marks. `dci-cheapest-rocm-study@8643526`

**Regression test.** `tests/unit/test_verifier_opening_punctuation.py` — 29
adversarial cases plus regression guards keeping the closed convention closed.

**Post-fix result.** Latent, and the differential-error question is answered
directly. Recounting every stored generation under both rules:

| corpus | answers | rows whose count changes | focal (B) | reference (C_L3) |
|---|---|---|---|---|
| cheapest-ROCm | 19,850 | **0** | 0 | 0 |
| natural-reasoning | 5,440 | **0** | 0 | 0 |

No published number moves, and no arm-differential verifier error is introduced
or removed. The defect is real and was never triggered by data collected so far.

**Propagation note.** The other two worktrees carry their own copy of
`src/dci/verifiers/rules.py` and were audited (above) but deliberately *not*
patched by copying. The fix belongs to the branch where it was reported and
should reach the others by ordinary merge, not by cross-worktree copying.

---

## C. Cross-model worktree (PR #16)

### X1 — `MODE_SUSPECT` entered the scientific matrix

**Symptom.** `admission()` rejected `MODE_FAILED` and let everything else pass.

**Reproduction.** An admission call with a `MODE_SUSPECT` verdict was admitted.

**Root cause.** Admission tested for the absence of outright failure rather than
for positive validity. Stage B/C raises `MODE_SUSPECT` for an empty final
answer, a trace opened and never closed, a reasoning trace appearing in the
native non-thinking mode, a thinking mode that never opened a block, and for
`WEIGHTS SUSPECT` — *not one trivial weight-integrity question answered
correctly, which is what a partially initialised load looks like*. Marker leak
and control-token residue were rejected separately; everything else was
admitted.

**Affected claims.** The `NO_THINKING` path is where this bites, because it
returns admitted with no later gate. `NATURAL_REASONING` must still clear
Stage E, which is the **only** reason the one suspect cell in the frozen matrix
(Qwen3.5-4B natural) was not admitted — luck, not design.

**Fix.** Requires `status == "MODE_VALID"`, so it also fails closed on any
verdict a future Stage B/C learns to emit. `dci-cross-model@74812d9`

**Regression test.** `tests/test_admission_gate.py` — 15 tests, one per Stage
B/C problem class.

**Post-fix result.** Latent. All four admitted `NO_THINKING` cells are
`MODE_VALID` today; no admitted cell changes.

### X2 — Kimi markerless output was scored as a final answer

**Symptom.** `DelimiterParser.extract_reasoning` ended `return None, text.strip()`.

**Reproduction.** Parsing text containing neither `◁think▷` nor `◁/think▷`
returned the whole generation as answer content.

**Root cause.** The class docstring already promised the opposite — *"this
returns an EMPTY answer in a thinking condition, because a scored scratchpad is
worse than a missing datum"*. The code contradicted its own contract. On an
always-thinking checkpoint, markerless output is what a failed reasoning
interface looks like, so scoring it manufactures a behavioural datum out of a
parser failure.

**Affected claims.** None realised: Kimi never reached generation. It is
`TP2_CAPACITY_BLOCKED` under vLLM TP=2 and `BACKEND_BLOCKED` on Transformers.
Had it run, every markerless row would have entered the verifiers.

**Fix.** Markerless output yields an empty answer; rows carry `channel_valid` so
the cell can be marked `CHANNEL_INVALID`. `raw_generation` still preserves the
text for diagnosis. `dci-cross-model@cf86a06`

**Regression test.** `tests/test_kimi_channel_validity.py` — 11 tests.

**Post-fix result.** Latent by circumstance rather than by design.

### X3 — both arm rates shared one denominator

**Symptom.** `headline()` weighted `A_fail_focal` and `A_fail_reference` with
`part["final_answers"]`, the background's combined answered-row count.

**Reproduction.** Two cells with mirrored arm counts (40 focal/1 reference and
1 focal/40 reference) and equal totals receive equal weight, so the published
focal rate stops equalling the rate over focal rows.

**Root cause.** The pooling assumed the arms answered at the same rate.
Arm-differential missingness is exactly what the report's own `missingness()`
section exists to detect.

**Affected claims.** "A-fail focal" and "A-fail ref" in the headline table.

**Fix.** Each rate pooled over the rows that produced it; both per-arm
denominators published; `fillna(0)` dropped so an arm with no answers leaves the
average instead of entering as a zero. `dci-cross-model@94b7e72`

**Regression test.** `tests/test_pooled_denominators.py` — 6 tests, including
the invariant the review asked for: the pooled rate equals the direct row-level
rate.

**Post-fix result.** Latent. Every current cell has balanced arms (80/80 and
160/160), so no published number moves. The invariant now holds by construction.

### X4 — canonical status was a line count

**Symptom.** `canonical_status` required only `len(rows) == EXPECTED_ROWS`.
`unique_row_ids` was computed one field earlier and never consulted.

**Reproduction.** A 160-row file with one design cell removed and another
duplicated in its place — right length, right task count, right arm set — was
labelled `CANONICAL`.

**Root cause.** Length is not identity. One cell contributing two draws and
another contributing none is a different experiment with the same arithmetic.
The replication audit could not catch it either: `replicate_duplication` built
pairs with `if len(answers) == 2`, silently dropping the malformed groups (X6).

**Affected claims.** The trust statement itself. `runs/` is gitignored, so the
manifest is all that stands between a reader and unreviewable artifacts.

**Fix.** Canonical status now requires the exact expected set of design
coordinates, each once, with unique row ids, the contract's task count and zero
malformed replicate groups. Missing, unexpected and duplicated cells are named
individually; contract identity is recorded beside the verdict.
`dci-cross-model@0368a13`

**Regression test.** `tests/test_manifest_identity.py` — 10 tests, including the
substitution case with a reconciling id count.

**Post-fix result.** All five main runs remain `CANONICAL` under the stricter
rule: 160/160 expected cells, no missing, unexpected or duplicated cells, no
malformed groups. The loophole closes without invalidating existing data.

### X5 — the results document could not be regenerated (not raised in review)

**Symptom.** `xm_actual_results.py` aborted with
`ValueError: cannot convert float NaN to integer`.

**Reproduction.** Run it against the five main run directories. Confirmed to
predate every change here by reproducing it on the unmodified file.

**Root cause.** Every main run stores `generation_ceiling: null`; pandas renders
an all-None column as float NaN; and the guard `int(value or 0)` does not catch
NaN because **NaN is truthy in Python** — `nan or 0` evaluates to `nan`. Two
call sites.

**Affected claims.** Reproducibility itself: a document asserting provenance
could not be rebuilt from the artifacts whose provenance it asserts.

**Fix.** NaN-safe conversion. A missing ceiling stays missing rather than
defaulting to 0, renders as "—" in tables, and reads as "generation ceiling NOT
RECORDED for this run" in prose. `dci-cross-model@0f117f7`

**Regression test.** None added; the fix is exercised every time the document is
rebuilt, which is now possible. This is a gap — see *Known gaps*.

**Post-fix result.** `ACTUAL_CROSS_MODEL_DCI_RESULTS.md` regenerates. The one
run that did record a ceiling still reports it (gemma-4-E4B-it, 39,517).

### X6 — the replicate audit skipped malformed groups

Folded into X4's fix and commit. `malformed_groups` and
`malformed_group_sizes` are now reported and block canonical status.

---

## Established root causes vs hypotheses

**Established** — reproduced deterministically, root cause identified in code,
regression test failing before the fix:

N1, N2, N4, R1, R2, X1, X2, X3, X4, X5, X6.

N3 is established as a claim defect: the cap-hit rates that make the wording
indefensible are measured, not inferred.

**Hypotheses, explicitly not established:**

* That the Qwen3.5 focal non-uptake reported in `SCIENTIFIC_CLAIM_AUDIT.md` is
  caused by the relational/local distinction. The association is strong and
  consistent across four checkpoints, but focal and reference differ in more
  than locality. Discriminating this is the subject of
  `NEXT_EXPERIMENT_DECISION.md`.
* That `TP2_REASONING_UNCLOSED` on Qwen3.5 is checklist-loop behaviour rather
  than a backend or parser fault. Untested either way.
* That the gemma target ceiling reflects genuine capability rather than an
  easier realised task. Not separable from the current data.

## Known gaps

* X5 has no regression test. It needs a fixture run directory with a null
  ceiling; the natural place is an integration test that rebuilds the document,
  which does not exist yet.
* The verifier repair is committed on one branch only, by design. Until the
  branches merge, the other two lineages carry the defect — audited as inert on
  their current corpora, but live for any new generation.
* `VERIFIER_UNCERTIFIED` and `UNSATISFIABLE` are implemented in the
  identification layer but wired to constants in the current reporting pass;
  neither has a live certification feed yet.
