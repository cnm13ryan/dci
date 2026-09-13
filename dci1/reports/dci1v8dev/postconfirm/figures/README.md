# SPECTRUM figures

Three figures, in order of importance: a forest that answers both SPECTRUM
questions across all 28 conditions, one explanatory scatter, and an appendix
grid of every condition.

| input | sha256 |
|---|---|
| `../data/spectrum_points.csv` | `35cd21c7db2bf30aac86df16424e1060bdb432fc4635df9ffa58beda3207ced1` |
| `../data/spectrum_results.csv` | `369e42bb01fb6c22930455f5c87f6ac05733d32487172b4d21e9046055aeb026` |
| `../../../../tools/v8_postconfirm_spectrum_plot.py` | `d5cda45d03a7fac64dd9d4c01ccaa6277c17ad3be795b3e7cac202571e01a8b4` |

Both tables are copies of the signed `CONFIRMATORY_ANALYSIS` records of the
root `dci1/evidence/dci1v8p1-confirm`, bound to commit
`034fc7214762b6848d5d904b14fd82b317830667`. **No scientific quantity is
recomputed and no registered estimate or inference is altered.** The fitted
line is drawn from the recorded slope and recorded family intercepts, and
the script asserts — for every one of the 28 panels, failing closed — that
the line it draws passes through the record's own `predicted_loss_at_A_pp`
at the record's own `difficulty_a`.

## Read this before reading the x axis

**ι is a chance-corrected stand-alone *compliance*, not a difficulty score.**
`calibration_table.instructed_compliance` computes `(solo − chance) /
(1 − chance)` — "the share of the achievable improvement over chance that
stating the constraint delivers". So:

* **higher ι  →  the companion is followed more often  →  an EASIER companion**
* **lower ι  →  a HARDER companion**

The protocol calls ι "the registered difficulty coordinate" because it
*indexes* difficulty, but it runs in the opposite direction. Its own spectrum
slots agree: `SPECTRUM_LOW` / `side: below` sits at low ι, `SPECTRUM_HIGH` /
`side: above` at high ι, so "below" and "above" are positions on the
compliance scale.

ι is **not** transformed in these figures. The registered β is defined on the
ι scale, and plotting `1 − ι` would put a sign on the drawn line that the
signed record does not contain. Instead every x axis is labelled
"companion stand-alone compliance ι (chance-corrected)" and carries the cue
`← harder companion    easier companion →`.

**The consequence for β.** A positive β on a compliance axis means B's loss
is *larger* beside an *easier* companion. That is the majority finding here
(19 of 28 conditions with the interval excluding zero) and it runs against
the premise the arm was designed on. Only 4 conditions show the intuitive
direction. Any sentence of the form "harder companions cost B more" has the
sign backwards for most of this study.

## The figures

| file | role |
|---|---|
| `fig1_spectrum_forest.{pdf,png}` | **Main.** Panel A: fitted slope β with its registered simultaneous interval. Panel B: δ_difficulty with its registered joint decision interval. Rows grouped by model, then prompt order, `f0`–`f3` within. Circles are B-first, squares B-second. Ordinary cases are muted; only the scientifically exceptional ones carry colour — β < 0 in A, and `L3d` or "no registered level" in B. Summary counts sit above each panel. |
| `fig2_spectrum_explainer.{pdf,png}` | **Main.** Gemma-3n-E4B-it, frame 1, B second — the one condition whose LOCAL contrast put A above its three matched references. Neutral companion dots, the fitted line, A as a star, the prediction as an open marker, and the residual as a labelled vertical segment with observed, predicted and δ annotated directly. |
| `fig3_spectrum_grid.{pdf,png}` | **Appendix.** All 28 conditions, 8 rows (model × order) × 4 columns (frame). Neutral companion points, one consistent highlight for A, a shared legend, large facet labels, and β and δ as compact subtitles rather than annotation boxes. Each panel keeps its own y scale — the loss ranges differ by an order of magnitude between conditions. |

## What the marks mean

* **grey dots** — one spectrum companion each, at its ι and its realised
  loss D(B ← companion) in pp.
* **dark line** — the registered fit, `mean(family intercepts) + β·ι`. The
  registered fit uses *family-aware* intercepts, so this single line is the
  family-mean relation; it is the exact expression whose value at ι_A the
  record calls `predicted_at_A`.
* **grey band around the line** — the registered **simultaneous interval on
  β**, pivoted at the fitted centroid. This is a **slope** band. It is *not*
  a confidence band for the fitted mean: the record carries no intercept
  uncertainty, and inventing one would be a quantity the protocol does not
  contain.
* **star** — A at its own (ι_A, observed loss). **Open circle** — the loss
  the fit predicts at ι_A. **The segment joining them is δ_difficulty.**
* **thick pale segment (fig 2)** — the registered **joint** 95% decision
  interval on δ_difficulty, the one registered uncertainty that decides
  whether A sits above, below or on the relation.
* **pale horizontal band** — ±10 pp about the prediction, the registered
  equivalence region that decides the `L3e` reading.

## One asymmetry in the registered grammar

`L3d` requires the interval to lie **above zero**; `L3e` requires it to lie
wholly **inside ±10 pp**. The grammar is one-sided, so a large *negative*
residual reaches **no registered level**. That is a property of the rule, not
an absence of result: all ten such conditions are strongly negative, meaning
A costs B markedly *less* than its stand-alone compliance predicts. They are
drawn in dark slate in fig 1 panel B, and must not be reported as nulls.

## Regenerating

```
python tools/v8_postconfirm_spectrum_plot.py \
    --data reports/dci1v8dev/postconfirm/data \
    --out  reports/dci1v8dev/postconfirm/figures
```

Plotting runs on a **separate** interpreter (`/home/cnm13ryan/git/dci/.venv`,
matplotlib 3.11.1). The pinned backend venv has no matplotlib and must not
acquire one: it is the environment every protocol record is signed under.
