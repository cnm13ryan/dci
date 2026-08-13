# Focal-ladder calibration — `NONDEGENERATE_FOCAL_NOT_IDENTIFIED`

**Decision timestamp:** 2026-08-11T21:24:36Z
**Code commit:** `6f5f8bb8587f1f2f97661a04b4d1ca214907f553`
**Run directory:** `runs/mechanism_and_focal_repair_20260811T204943Z/focal_calibration/`
`EXPLORATORY_NO_EVIDENCE`.

## Why

Round 11's focal instruction was satisfied in 0.000–0.138 of focal-arm rows and
"focal only" occurred in 7 of 640, so the four-state decomposition collapsed to
*neither → target only* and could not test whether the model can be pushed toward
preserving A versus preserving B. The repair was to shorten the required chain of
sentence-length increases until all four states are empirically possible.

## Calibration material

**Tasks CAL13–CAL32** from the `calibration` split — 20 tasks, disjoint from the
20 evaluation tasks (PLT01–PLT20) and from the CAL01–CAL12 block used for the
boundary-control preflight, so no set of topics does double duty. No run in this
repository had previously used the split.

720 generations: 3 rungs × 2 backgrounds × 20 tasks × 3 replicates × {b = 0,
b = 4096}. QAC. **No priority cue in any row**, so no rung could have been chosen
for the priority pattern it produces.

## The ladder

The target is fixed: `A` — *"Write exactly 4 sentences."*

### B3 = `B` (the existing focal, unchanged wording)

> Make each sentence strictly longer than the preceding sentence when measured by
> word count.

Verifier: the frozen `v_increasing_lengths` — `L1 < L2 < L3 < L4` over every
sentence found.

### B2 = `X_B_INC2`

> Make sentence 2 strictly longer than sentence 1, and sentence 3 strictly longer
> than sentence 2, when measured by word count. Sentence 4 may be any length.

Verifier: `v_increasing_prefix(text, k=3)` — `L1 < L2 < L3` over the first three
sentences.

### B1 = `X_B_INC1`

> Make sentence 2 strictly longer than sentence 1 when measured by word count.
> Sentences 3 and 4 may be any length.

Verifier: `v_increasing_prefix(text, k=2)` — `L1 < L2`.

### Verifier definition

`v_increasing_prefix` is a **prefix of the frozen rule**, not a new idea: the same
`split_sentences`, the same `word_tokens`, the same strict `>` comparison, the
same `fraction_status` scoring, and the same "unscorable when too short"
convention. Tests assert it reproduces `v_increasing_lengths` exactly at `k = 4`,
that it is monotone (passing rung k implies passing rung k−1), and that **it never
reads the sentence count** — sentences beyond the k-th are ignored, so no rung can
be satisfied or broken by writing more of them. That independence is what keeps
the focal from being a restatement of the target.

## Pass rates

Primary background `X_PAREN_FREE`, by reasoning condition:

| rung | b | target | focal | background | sentences |
|---|---|---|---|---|---|
| B | 0 | 0.533 | 0.000 | 1.000 | 4.47 |
| B | 4096 | 0.983 | 0.067 | 0.800 | 3.98 |
| X_B_INC2 | 0 | 0.617 | 0.000 | 0.983 | 4.38 |
| X_B_INC2 | 4096 | 1.000 | 0.517 | 0.917 | 4.00 |
| X_B_INC1 | 0 | 0.933 | 0.067 | 1.000 | 4.07 |
| X_B_INC1 | 4096 | 0.983 | 0.867 | 0.917 | 3.98 |

**The ladder does what it was built to do on the focal rate:** pooled focal
compliance climbs **0.033 → 0.258 → 0.467**.

## Four-state distributions

Primary background, pooled over reasoning conditions:

| rung | both | target only | focal only | neither |
|---|---|---|---|---|
| B | 0.033 | 0.725 | **0.000** | 0.242 |
| X_B_INC2 | 0.258 | 0.550 | **0.000** | 0.192 |
| X_B_INC1 | 0.458 | 0.500 | **0.008** | 0.033 |

## Selection rule and its result

Applied in the fixed order B → X_B_INC2 → X_B_INC1, taking the first rung that
clears every gate:

| gate | B | X_B_INC2 | X_B_INC1 |
|---|---|---|---|
| focal pass in [0.25, 0.75] | 0.033 ✗ | 0.258 ✓ | 0.467 ✓ |
| target pass in [0.15, 0.85] | 0.758 ✓ | 0.808 ✓ | **0.958 ✗** |
| P(both) ≥ 0.05 | 0.033 ✗ | 0.258 ✓ | 0.458 ✓ |
| P(target only) ≥ 0.05 | 0.725 ✓ | 0.550 ✓ | 0.500 ✓ |
| P(focal only) ≥ 0.05 | **0.000 ✗** | **0.000 ✗** | **0.008 ✗** |
| technical invalidity ≤ 0.02 | 0.000 ✓ | 0.000 ✓ | 0.000 ✓ |
| **verdict** | fail | fail | fail |

`X_B_INC2` clears every gate but one.

## Selected candidate

**None.** `NONDEGENERATE_FOCAL_NOT_IDENTIFIED`. The priority re-test is stopped.

## The diagnosis is not the one the repair assumed

The failing gate is not "the focal is too hard". Focal compliance rose by a factor
of fourteen across the ladder and P(both) rose with it, 0.033 → 0.258 → 0.458.
What never appeared is **focal only**: 0.000, 0.000, 0.008.

Under the parenthetical background, **A and B do not compete.** As the focal gets
easier the probability moves into *both*, never into *focal only*. Whenever this
model can satisfy the length ordering, it can also write four sentences — so there
is no regime in which it must choose, and an explicit priority instruction would
have nothing to act on. The one thing that reliably makes the target fail is not
a harder focal instruction at all; it is the boundary-capable mark of
Experiment 1.

## Why no further rung was constructed

§15 permits a further variant only if all three are unusable, and §17 and §32
direct a stop when no prespecified rung passes. The observed direction settles
it: every easier rung moves probability into *both* and pushes the target further
toward its ceiling — `X_B_INC1` is already at **0.958**, outside its gate — which
is the opposite of what the failing gate needs. Weakening B further would make
`P(focal only)` smaller, not larger.

## One observation recorded but not acted on

Under the **semicolon** background, `X_B_INC1` shows **P(focal only) = 0.133** at
b = 0 and **0.183** at b = 4096 — above the gate. The gates are specified on the
parenthetical background, and switching to the background that happens to pass
would be selecting the condition that gives the wanted result. It is recorded
here because it points the same way as Experiment 1: the focal-only state, which
an arbitration account needs, appears only once a boundary-capable mark is
present to damage the target.
