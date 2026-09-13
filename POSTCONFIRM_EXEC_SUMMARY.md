# DCI-1 v8.1 — post-confirmatory executive summary

*2026-09-10. The frozen registered confirmatory analysis and final report
ran once, on the complete row set, and returned `PASS` for all four models.*

## Primary result

Against three same-form companions matched to it on wording-conditioned
stand-alone difficulty, the focal instruction A costs compliance with B no
more than they do in **23 of the 24** preregistered model × wording-frame ×
prompt-order conditions — while composition itself moves B's compliance by
up to **49 percentage points**.

- Δ_R over the 24 cells: **−11.19 to +12.64 pp**; 18 negative, 6 positive.
- **23 of 24** joint decision intervals stop below +10 pp (`L3c`).
- The registered precision precondition is met in **24 of 24** cells;
  realised joint half-widths 1.05–3.24 pp. The smallness is measured.
- The exception: **Gemma-3n-E4B-it, frame 1, B second, Δ_R = +12.64 pp,
  joint CI [+9.62, +15.66]** → `INDETERMINATE@0.10`. The registered rule
  certifies neither an excess above +10 pp nor a bound below it, and the
  cell carries four registered qualifications.

## Model-level verdicts

| model | B first | B second |
|---|---|---|
| Qwen3-4B | `LOCAL_EQUIVALENT_SAME_FORM_ONLY` | `LOCAL_EQUIVALENT_SAME_FORM_ONLY` |
| Qwen3-4B-Instruct-2507 | `LOCAL_EQUIVALENT_SAME_FORM_ONLY` | `LOCAL_EQUIVALENT_SAME_FORM_ONLY` |
| Gemma-3n-E2B-it | `LOCAL_EQUIVALENT_SAME_FORM_ONLY` | `LOCAL_EQUIVALENT_SAME_FORM_ONLY` |
| Gemma-3n-E4B-it | `LOCAL_EQUIVALENT_SAME_FORM_ONLY` | **`FRAME_HETEROGENEOUS`** |

Every verdict carries `NEAR_FORM_UNAVAILABLE`: the design runs no near-form
arm, so the strong refutation verdict is unreachable and **no claim of the
form "A is not unusually harmful" is available**. §26 methodological success
is `MET` for both Gemma models and **`NOT_MET`** for both Qwen models — on
D(A←B)'s precision alone; every Δ_R interval meets its precondition.

## Major sensitivity findings

- **Reference set (F_REFSENS): changes a registered verdict on 2 of 24
  cells** — Gemma-3n-E4B-it frames 0 and 1, both with B second.
  Across-triple spread reaches 26.46 pp; the frozen triple lands at an
  extreme of its own admissible set in 7 of 24 cells; the sign flips in
  14 of 24.
- **Operating point (F_RUNNER_UP): changes no registered reading anywhere**,
  across 18 comparisons on 7 frames, despite every frame being
  `OPERATING_POINT_UNSTABLE`. Largest movement 12.77 pp, reading unchanged.
- **SPECTRUM**: δ_difficulty is negative in 25 of 28 cells and reads `L3e`
  (within ±10 pp of prediction) in 17: on those cells A's loss is within
  ±10 pp of what the fitted relation predicts for a companion of its
  measured stand-alone compliance. **The relation itself runs against the
  design's premise.** ι is a chance-corrected stand-alone *compliance*, so
  higher ι is an *easier* companion; the fitted slope is positive and
  excludes zero in 19 of 28 cells, meaning B fares **worse beside an easier
  companion**. Only 4 cells show the intuitive direction, and they include
  both orders of the one frame that produced the positive LOCAL result.

## The largest caveat

The study's one positive cell is its most reference-sensitive. Its three
per-reference contrasts are +5.63, **+35.45** and −3.16 pp; across the nine
admissible triples of its five frozen families Δ_R runs **−8.63 to +12.64
pp**, and the frozen triple is the single most harmful of the nine. The
graded-compliance recoding takes it to +7.07 pp. §17.4's both-bounds rule
withholds its levels. And the SPECTRUM arm on the same rows puts A **11.49
pp below** what companions of its measured difficulty predict. The
registered rule decides on the frozen triple and the result stands as
reported — but one reference of three carries it.

Separately: **Qwen3-4B-Instruct-2507's eligibility is sample-sensitive.**
Under a different partition of the same 216 pre-freeze topics the same
pipeline would not have admitted it. Its result must travel with that
sentence.

## Recommended paper headline

> Composing two verifiable instructions moves compliance enormously, but
> replacing the companion instead of removing it leaves almost all of that
> movement behind: in 23 of 24 preregistered conditions the matched-reference
> contrast is bounded below 10 percentage points at measured precision. The
> twenty-fourth — one model under one of four sentence frames with B second —
> is not, and it exists only because the design conditions on wording:
> averaging that model's three frames returns +0.06 points. A pair-specific
> claim needs an explicitly stated reference class *and* the phrasing under
> which that class was matched, and this study shows both decisions changing
> the answer.

## Where everything is

- **Full bundle**: `V8_1_POSTCONFIRM_PAPER_REWRITE_BUNDLE.md` (repo root of
  the `dev/v8-frame-aware-prescreen` worktree).
- **Figure and table datasets**: `dci1/reports/dci1v8dev/postconfirm/data/`
  (17 files, CSV + JSON).
- **SPECTRUM figures**: `dci1/reports/dci1v8dev/postconfirm/figures/` (PDF +
  PNG), drawn from those tables by `dci1/tools/v8_postconfirm_spectrum_plot.py`:
  `fig1_spectrum_forest` (main), `fig2_spectrum_explainer` (main),
  `fig3_spectrum_grid` (appendix). Their README states the ι orientation.
- **Signed records**: `dci1/evidence/dci1v8p1-confirm/durable/dci1v8/<model>/
  CONFIRMATORY_ANALYSIS/confirmatory_analysis.json`, bound to commit
  `034fc7214762b6848d5d904b14fd82b317830667`, preregistration hash
  `d3552f9f47e3f008…`.
