# The clause-boundary mechanism test

`EXPLORATORY_NO_EVIDENCE`. Run directory:
`runs/mechanism_and_focal_repair_20260811T204943Z/` (gitignored; this report is
the tracked copy).

## Question

Rounds 7–11 removed every proposed explanation of why the semicolon background
produces unusually persistent interference: free-versus-fixed placement
(falsified), single-character atomicity (refuted by the ellipsis), the mark
merely appearing in the output, wording length, and simple response chaining.

One account survived: **a semicolon can stand where a sentence boundary could
stand, and both constraints it interferes with — "exactly four sentences" and
"increasing sentence lengths" — are defined over sentences.** A mark that is
equally unattached and equally free to place, but that has no clause-joining use,
should then interfere much less.

This is the first *positive* test of that account rather than another
elimination.

## Control-selection preflight

Candidates were fixed in advance at `°` and `*`, with the matched wording
template. **288 generations on 12 `calibration` tasks** — a split no run in this
repository had used, with zero topic overlap with the 20 evaluation tasks. The
preflight design **contains no focal-arm row**, so focal-versus-reference
interference is not computable from it; the control could not have been chosen on
the outcome the main experiment measures.

Measured for each mark, isolated and combined with A and `C_L3`:

| mark | combined compliance | markup collision | count > 1 | malformed | words | sentences |
|---|---|---|---|---|---|---|
| semicolon (reference) | 0.896 | 0.000 | 0.000 | 0.000 | 48.3 | 3.98 |
| **degree `°`** | **0.729** | **0.000** | 0.062 | 0.000 | 47.8 | 3.88 |
| asterisk `*` | 0.208 | 0.188 | **0.792** | 0.000 | 43.4 | 4.00 |

**The asterisk is unusable.** 79.2% of its combined answers contain more than one
asterisk: the model writes `*emphasis**` and bullet lists, and `LIST_MARKER`
strips a leading `* ` for segmentation while `v_exact_char_total` still counts it.
This hazard was pinned by tests committed before any generation
(`test_asterisk_markdown_hazard_is_real_and_is_measured_not_assumed`); the
preflight measured its size.

**A correction to my own gate, recorded.** The first version of the preflight
scored criterion 2 as "the answer contains markdown anywhere" and disqualified
**both** candidates, printing `BOUNDARY_CONTROL_NOT_IDENTIFIED`. That gate was
wrong: it flagged degree-symbol answers whose prose contained
`**temperature sensor**`, which cannot change a degree-symbol count. Markup
*built from the counted character* is 0.000 for `°` and 0.188 for `*`. The
corrected criterion is the one the pre-generation tests already pinned, so the
definition was not invented to rescue a candidate. The original output is kept at
`boundary_control_preflight/report_gate_v1.txt`.

## Frozen control

`X_DEGREE_FREE` — *"Use exactly 1 degree symbol (°) in the whole answer, and
place it wherever you judge best."* Byte-identical to the semicolon instruction
apart from the mark name, asserted by test and again at design time in all 160
matched groups.

Recorded before the main run: its compliance is **0.167 below** the semicolon's,
which is the main limitation of the comparison.

## Main design

640 generations. `Qwen/Qwen3-4B` @ `1cfa9a72`, vLLM 0.15.1+rocm720, TP = 2,
bf16, T = 0.7, top-p 0.9, 512-token answer allowance — the Round 11 condition
unchanged, read from its manifest. QAC, arms {B, `C_L3`}, backgrounds
{semicolon, degree}, b ∈ {0, 4096}, the 20 evaluation tasks, 4 scientific seeds
from `blake2b(20260812 | task_id | replicate | phase)`.

## Raw rates

| background | b | arm | A-failure | arm constraint | background compliance | sentences | answer tokens |
|---|---|---|---|---|---|---|---|
| degree | 0 | B | 0.113 | 0.050 | 0.500 | 3.68 | 167 |
| degree | 0 | C_L3 | 0.013 | 0.338 | 0.412 | 3.99 | 60 |
| degree | 4096 | B | 0.062 | 0.237 | 0.675 | 3.93 | 201 |
| degree | 4096 | C_L3 | 0.100 | 0.900 | 0.912 | 3.89 | 64 |
| semicolon | 0 | B | **0.725** | 0.000 | 0.938 | **2.29** | 140 |
| semicolon | 0 | C_L3 | 0.037 | 0.475 | 0.775 | 3.96 | 61 |
| semicolon | 4096 | B | **0.512** | 0.050 | 0.825 | 3.31 | 179 |
| semicolon | 4096 | C_L3 | 0.037 | 0.912 | 1.000 | 3.96 | 61 |

0 technical failures, 1 truncation in 640, leakage ≤ 0.003, cap-hit 0.013.

## τ and Δ_boundary

| estimand | b = 0 | b = 4096 |
|---|---|---|
| τ, degree (non-boundary) | +0.100 [+0.025, +0.188] | **−0.037** [−0.150, +0.062] |
| τ, semicolon (boundary-capable) | +0.688 [+0.537, +0.825] | +0.475 [+0.375, +0.575] |
| **Δ_boundary** | **+0.588** [+0.438, +0.738] | **+0.512** [+0.375, +0.662] |
| Γ (4096 − 0) | — | −0.075 [−0.212, +0.075] |

**The headline is Δ_boundary at b = 4096 = +0.512 [+0.375, +0.662].**

Reasoning does not close the gap: Γ's interval contains zero. Under the
non-boundary mark, reasoning drives τ to zero and slightly past it; under the
semicolon it stays near +0.5.

## Task-level heterogeneity

| b | mean Δ | tasks positive | tasks negative | top-3 share |
|---|---|---|---|---|
| 0 | +0.588 | 17/20 | **0** | 0.26 |
| 4096 | +0.512 | 19/20 | **0** | 0.32 |

Per-replicate Δ: +0.650, +0.650, +0.600, +0.450 at b = 0; +0.450, +0.700, +0.600,
+0.300 at b = 4096. All eight positive. Neither one task nor one seed drives it.

## The mechanism variable separates completely

`splice_count` — the repository's own audited proxy for "this mark is standing
where a sentence boundary could stand", revised after a human audit in Round 7 —
computed on both marks with the same code, on rows where the background was
actually produced:

| background | b | arm | stands at a boundary | mean relative position | sentences |
|---|---|---|---|---|---|
| degree | 0 | B | **0.000** | 0.92 | 3.73 |
| degree | 4096 | B | **0.000** | 0.70 | 3.96 |
| semicolon | 0 | B | **0.920** | 0.38 | **2.33** |
| semicolon | 4096 | B | **0.939** | 0.30 | 3.29 |

The manipulation did exactly what it was built to do. The semicolon is produced
standing where a sentence boundary could stand in 89–94% of answers and the
degree symbol in **none**, in every cell. The semicolon condition also writes
about 1.5 fewer sentences at b = 0 — the target is "exactly 4".

This is descriptive: it is a property of the produced text, and nothing above is
conditioned on it.

## Manual checks

54 outputs read: 20 across all conditions, 10 target-only, all 4 focal-only, 10
both, 10 from the largest-swing cell. The registry segmenter and an independent
character-scanning segmenter (different algorithm class, no shared helpers, no
shared abbreviation table) agreed on **52 of 54**.

**Both disagreements were the same artefact, and it was then measured across all
640 rows.** All **12** disagreements in the full run are degree rows, and
**100%** of them contain a `°` unit ending a sentence — `…drop below 20°C. This
practice…` — which the production segmenter does not split. Among the 23 degree
rows carrying that pattern, `A_pass` is **0.478**, against **0.963** in the other
degree rows. The semicolon condition has **0** disagreements.

**Direction:** the artefact suppresses the registry sentence count in the degree
condition only, which pushes the degree arm toward A-*failure*, inflating τ_degree
and therefore **deflating** Δ_boundary. **+0.512 is a lower bound with respect to
it.**

## Interpretation

**The clause-boundary hypothesis is supported**, on the directive's own reading:
the semicolon produces materially greater focal-versus-reference interference
than the matched non-boundary symbol at high reasoning, the mechanism variable
separates the two conditions completely, and the two background manipulations are
comparable — though not equal — in compliance.

The strongest form the claim can take is: *within these conditions, a mark that
can occupy a sentence boundary interferes with sentence-defined constraints, and
an otherwise identically specified mark that cannot does not.*

## What was falsified

* **"The semicolon effect is about a mark being present and freely placed."**
  Falsified. The degree symbol is one mark, exactly one, freely placed, in the
  identical sentence — and τ under it is **−0.037** at b = 4096.
* **"Reasoning erodes whatever the semicolon does."** Not supported here:
  Γ = −0.075 [−0.212, +0.075]. The gap is as large without reasoning as with it.

## What remains possible

* **The account is still correlational at the level of the mark's *use*.** The
  intervention assigns the *instruction*, and the boundary behaviour follows. It
  has not been shown that forcing a semicolon *not* to stand at a boundary
  removes the interference — `X_NO_SEMI_SPLICE` exists in the registry and was
  never crossed with this design.
* **Compliance is not equal** (0.500–0.675 against 0.825–0.938 in the focal arm).
  The compliant-only split points the other way (+0.530, +0.566), but it is
  post-treatment and cannot settle it.
* **One model, one order, one load, one task set.** Nothing here says whether the
  boundary account transports; Round 11 found the semicolon amplification itself
  does not transport to SmolLM3-3B.
* **`°` may be unusual in a second way.** It is matched on count, scope,
  placement freedom, wording and response length, but it is not a punctuation
  mark at all. A boundary-incapable *punctuation* mark would be a sharper control.
