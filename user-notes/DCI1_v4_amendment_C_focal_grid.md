# Amendment C (draft) — the extended focal grid

**Status: DRAFT. NOT ADOPTED. Nothing in the registered protocol, the
verifiers, the grids or the code has been changed by this document.**

Companion to Amendment A (the prompt stem) and Amendment B (the reference
pool). Evidence: `dci1/reports/bgrid_screen_v4/REPORT.md`, screen protocol hash
`6a63ba782db0de6e1c4d80763065dda7ced1279e3c8ddcc097c7119087f4fff2`, a
non-confirmatory design screen.

---

## 1. What is proposed

Extend §7.1's focal severity grid for B from

    FOCAL_GRID = (7, 8, 9, 10)

to

    FOCAL_GRID = (7, 8, 9, 10, 11, 12)

B's **rule is unchanged**: every word in the answer has at most m letters,
scored as `focal_statistic(text) <= m` where `focal_statistic` is the longest
alphabetic run. Only the severity range moves. The four §7.1 wordings are
already parameterised on m and render at 11 and 12 from the same four strings;
the B-grid screen proved the rendering byte-identical to the registered
`focal_wordings` on all four registered rungs, and the scoring verdict-identical
over the twenty-response fixture suite.

Nothing else in §7 changes. `TARGET_GRID`, `REFERENCE_LADDERS`, `FOCAL_BAND`,
`FOCAL_AIM`, the caliper, the non-vacuity threshold and the vacuity maximum are
untouched.

---

## 2. Why it is proposed

Amendment A's floored stem removes B-side vacuity: it takes the vacuous share
of B's passes from 0.15–1.00 down to 0.00–0.10, and makes the raw and
length-restricted `D(B←A)` converge. That is the only known fix for a primary
estimand whose baseline is otherwise carried almost entirely by four-to-eleven
word answers — honest B-solo compliance under the current stem is **0.042** at
three separate severities on qwen3-4b-instruct-2507.

But B is length-monotone. Forcing length makes B strictly harder, and on the
registered grid {7, 8, 9, 10} that pushes qwen3-4b off the bottom of the focal
band:

| model | registered grid under floored | Gate 2 outcome |
|---|---|---|
| gemma-3n-e2b-it | 0.417 0.417 0.417 0.917 | m\* = 10 |
| gemma-3n-e4b-it | 0.500 0.625 0.667 0.750 | m\* = 10 |
| **qwen3-4b** | 0.042 0.125 0.167 0.375 | **FOCAL_RANGE_EXHAUSTED** |
| qwen3-4b-instruct-2507 | 0.125 0.417 0.375 0.667 | m\* = 10 |

At m = 11 and m = 12 qwen3-4b reaches 0.625 and 0.875, both inside the
registered band. **An extended grid is the only known route to an honest B on
all four models.**

---

## 3. Interaction with Amendment A

The two amendments are **not separable**.

- **Stem without extended grid.** qwen3-4b terminates at Gate 2 with
  `FOCAL_RANGE_EXHAUSTED`. Replicated across two independent screens; the gap
  to the band floor is 2.3 standard errors.
- **Extended grid without stem.** Pointless, and mildly harmful. Under the
  current stem B's compliance is already at or above the band on most rungs and
  the extra rungs only push it further up (0.958–1.000 at m = 11 and 12 on all
  four models). The vacuity is untouched, so the estimand stays dishonest.
- **Both.** Every model has an in-band rung. This is the only combination that
  yields a measurable, honest B on all four replications.

Amendment A should therefore not be adopted alone. If Amendment A is rejected,
Amendment C has no purpose and should be rejected with it.

---

## 4. The §7.1 change required

In `dci1/src/dci1v4/verifiers/constraints.py`:

```python
-FOCAL_GRID = (7, 8, 9, 10)                          # B: m
+FOCAL_GRID = (7, 8, 9, 10, 11, 12)                  # B: m
```

Consequences that follow mechanically and must be re-executed, not assumed:

1. **The canonical verifier hash changes.** `constraints.py` is inside the
   §10.6 semantic module set, so every one of the eleven bound entry points
   refuses until Gate 1 is re-frozen. §10.2 re-opens for B.
2. **The §7.3 witness matrix grows.** `registered_instances()` gains two B
   instances, so the unordered-pair count rises and `verify_all_witnesses`
   must be re-run. `FOCAL_VIOLATOR = "prohibitions"` is twelve letters and
   **would no longer fail B at m = 12** — it must be replaced with a longer
   token, and `assert_token_orthogonality`'s check that the violator exceeds
   the loosest m must be re-established.
3. **The B-side boundary suite must be re-audited** at the two new severities.
   The case texts do not change; the expected verdicts at m = 11 and m = 12 are
   new and must be authored and frozen before qualification.
4. **The §12.2 ladder screen grows** by two B rungs per model.
5. **Every §12.3 selection at Gate 2 re-runs** on the 96 solo-calibration
   topics under the final prompt.

---

## 5. The consequence for the reference pool

**Every reference rate must be re-screened under the final prompt.** Reference
solo compliance depends on the stem through response length in exactly the way
B's does — that is the mechanism, not a coincidence — and the §13.2 caliper is
measured against A, whose anchor the stem also moves:

| model | n\* under the current stem | n\* under the floored stem |
|---|---|---|
| gemma-3n-e2b-it | 4 | 1 |
| gemma-3n-e4b-it | 1 | 2 |
| qwen3-4b | 1 | 2 |
| qwen3-4b-instruct-2507 | 3 | 5 |

The anchor moves on all four models. Every §13.2 condition 1 caliper judgment
made under the current stem is therefore void, including the FORM × STEM
screen's candidate-family results, which are the evidence for Amendment B.
**Amendments A, B and C must be evaluated together on one re-screen under the
final prompt, or not at all.**

---

## 6. Why m ≤ 12 and not further

The screen grid was frozen at m = 12 before the first generation precisely so
that a model needing m > 12 would be *reported* rather than accommodated. None
does. m = 12 is also close to the point where B stops being a constraint: the
median realised max word length under the floored stem is 9–11 letters on all
four models, so at m = 12 most models pass by default (0.875–1.000) and B
carries almost no information.

If a later re-screen shows a model needing m > 12, the correct response is to
record that B is not a usable focal constraint for that model, not to widen the
grid again.

---

## 7. Evidence status, stated plainly

The B-grid screen returned **MARGINAL**, not PASS.

Every model has an in-band rung, but qwen3-4b-instruct-2507's two in-band rungs
are both 0.667, which is 0.71 and 0.69 standard errors above the band floor.
Under §1.4 that requires **a fresh-topic confirmation before any grid
amendment**.

Two further instabilities are on the record and are not resolved:

- The Instruct model's `FOCAL_RANGE_EXHAUSTED` call at m = 10 **flipped**
  between two independent draws on the same 24 topics (0.542, then 0.667).
- Under the floored stem the Instruct model's A curve has only two eligible
  rungs and both sit exactly on the 0.50 target-band floor. One topic fewer and
  it would be `TARGET_RANGE_EXHAUSTED`.

Both are properties of a 24-topic, single-draw development sample, which has now
been spent three times. Gate 2 measures on 96 disjoint topics at M = 4, and
nothing in these screens has been shown to predict it.

---

## 8. What happens if neither amendment is adopted

The registered design proceeds with a prompt that produces four-to-eleven word
answers on the Qwens, and `D(B←A)` on those two replications is estimated
against a baseline whose honest compliance is **0.000** and **0.042**. The
numbers would be computable and would mean nothing about instruction
compliance: they would be a measurement of how often a model emits a short
enough answer.

That is the alternative this amendment exists to avoid, and it should be stated
in those terms when the decision is made.

---

## 9. Outcome

**Not adopted.** `FOCAL_GRID` is unchanged at (7, 8, 9, 10). m = 11 and m = 12
exist only inside `dci1/src/bgrid_screen_v4/`, which the registered code
refuses: `Constraint("B", 11)` raises and `focal_wordings(11)` raises, and
`tests_v4/test_bgrid_screen_isolation.py` pins both.

Blocked on the same thing as Amendments A and B: a fresh-topic confirmation
under the final prompt, on topics that are not the 24 pre-screen ones. Adoption
must precede Gate 1, because it changes the canonical verifier hash and re-opens
§10.2 for B.
