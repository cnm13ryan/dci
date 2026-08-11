# What these figures say

**Answer first.** Giving this reasoning model more test-time reasoning does not
simply make it better at following composed instructions. It removes one kind of
directional interference almost completely and leaves another kind essentially
untouched — so *how much a reasoning model appears to suffer from instruction
conflict depends on how much reasoning you gave it, and on the instructional
context you measured it in.*

A single fixed-budget compliance score, or a single DCI bar, cannot show either
of those things.

---

### Finding 1 — reasoning changes directional interference, and not by a little

τ(B→A) under the matched control background falls from **+0.400** at the native
non-thinking setting to **exactly 0.000** by b = 512 and stays there through
b = 4096. Figure 3 shows this is a change in the **focal** arm — focal A-failure
goes to zero — which is what a directional claim requires; it is not the
reference arm drifting up to meet it.

### Finding 2 — the ordinary condition benefits far more than the amplified one

Under the amplifying background (*"use exactly 1 semicolon, place it wherever you
judge best"*) τ ends at **+0.500 [+0.300, +0.700]**. The gap between the two,
Δ, grows from +0.200 [−0.150, +0.550] at b = 0 to **+0.500 [+0.300, +0.700]** at
b = 4096.

The right way to say this is **amplified interference is more compute-resistant
than ordinary interference**. The wrong way is "more reasoning makes the
amplifier stronger": the amplifier's own τ at b = 4096 (+0.500) is *below* its
value at b = 0 (+0.600). The gap widens mostly because the control's interference
is *resolved*, not because the amplified condition deteriorates.

### Finding 3 — the improvement is arbitration, not reconciliation

Figure 6 is the mechanism-shaped part. Under the control background, reasoning
moves probability out of "neither constraint satisfied" (0.400 → **0.000**) and
into "**target only**" (0.600 → **0.900**). "Both satisfied" only ever reaches
0.100. Under the amplifier, "neither" stays at 0.500–0.600 at every budget.

So additional reasoning does not teach the model to satisfy competing constraints
together. It makes the model *pick the target and drop the focal constraint* —
and under the amplifying background it does not reliably manage even that.

### Finding 4 — an absolute-compliance curve would have hidden all of this

Figure 7 puts the two views on one shared budget axis. The top panel is what a
conventional evaluation would report: target compliance climbing to **1.000** and
saturating — the task looks solved. The bottom panel, over the identical budgets,
shows the contextual gap widening. Reporting only the first curve would
have concluded that reasoning fixes composed-instruction following. It does, in
one context, and does not in another that differs by a single background clause.

### Finding 5 — "amplification" is not one mechanism

Figure 14 breaks the tempting shortcut. The semicolon amplifies (τ ≈ +0.95) while
collapsing the answer onto ~1.3 sentences with `chain_share` ≈ 0.43 — clauses
chained where sentence boundaries should be. The **ellipsis also amplifies**
(τ = +0.400, compliance 1.000) with `chain_share` ≈ 0.03 and ~3.3 sentences — it
simply writes too few sentences, with no chaining at all.

Two instructions in the same structural class produce the same *outcome* through
visibly different *strategies*. `chain_share` does not order them and is
therefore not a sufficient mediator of amplification. Figure 13 makes the same
point about robustness: at k = 5 the semicolon's effect survives (Δ = +0.650)
and the ellipsis's does not (Δ = +0.125 [−0.075, +0.325]).

---

## What is *not* shown here

* **No scaling law.** Five budgets, one checkpoint, points joined only as a
  visual guide. Nothing is fitted or extrapolated, and no plateau beyond 4096 is
  claimed.
* **b = 256 is not smoothed away.** At that budget the reasoning phase was cut
  short on **95%** of rows, and both τ values collapse toward zero — the only
  non-monotone point in the set. Severe restriction may induce a different
  strategy rather than simply "less of the same reasoning"; these data cannot
  tell those apart, so the point is drawn, ringed, and left unexplained.
* **b = 0 is a different kind of condition.** It is the model's own non-thinking
  mode, so the b = 0 → b > 0 step mixes *entering* thinking mode with *having
  more* reasoning. The quantitative dose reading is cleaner among b > 0.
* **Realised reasoning is descriptive.** Figure 8 plots outcomes against realised
  tokens because it is informative, and labels itself post-treatment because it
  is. Nothing is regressed on M.
* **Free placement is untested, not refuted.** All ten positional wordings failed
  their manipulation check (compliance ≤ 0.338 against 0.938–1.000 for free
  placement), so Figure 11's grey rows carry no information about placement. What
  *is* established is that single-character atomicity is **not** required, since a
  three-character unattached mark amplifies.
* **One checkpoint.** Every reasoning curve is `Qwen3-4B` at one decoding setting
  on one backend. These are exploratory, checkpoint-specific results, not a
  property of reasoning models as a class.

## Reproducing

```
uv run python make_figures.py
```

Rebuilds every table in `data/` and every figure from the stored generations,
then re-derives 27 published values and fails if any disagrees. Intervals are
seeded per estimand, so they do not depend on the order the figures are drawn.
