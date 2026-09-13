# U2 — §11.8's tier-indicator secondary fit, and which of four to register

**Status: ADOPTED. U2 is resolved at A2 on 2026-08-23.**
U2 was a `RESEARCHER_DECISION_REQUIRED` item in `protocol/open_items.py` and
it **blocked adoption**. The researcher approved this packet's recommendation;
the resolution is recorded in `researcher_decisions.json` under `open_items`,
`analysis.spectrum.fit_with_tier_indicator` runs A2 by default, and
`assert_adopted_formulation` refuses A4 on any reporting path. §11.8's sentence
was amended to name the three core families explicitly, which is the amendment
§5 below asked for.

Evidence: `tests_v5/test_tier_fit.py::test_a2_recovers_the_slope_and_a4_
absorbs_family_levels` and `::test_a4s_gamma_depends_on_where_the_near_form_
points_happen_to_sit`. Both are executed by the suite, so the numbers below are
recomputed on every run rather than quoted.

---

## 1. The defect

§11.8 registers the secondary fit as

$$Y_{fs} = \alpha_f + \beta d_{fs} + \gamma\,\mathbb{1}[\text{Tier 2}]$$

over twelve points — the three core references with their six spectrum rungs,
and the three near-form controls — and never says **what $\alpha_f$ is for the
three near-form controls**. If each near-form control gets its own family
intercept, the tier indicator is exactly the sum of those three dummies:
the design matrix is singular and $\gamma$ has no unique least-squares value.

The repair is not unique, and the repairs do not estimate the same thing. That
is why this is a researcher decision and not a bug fix: choosing one silently
— by a pseudoinverse, a dropped column picked from the observed data, a ridge
term, or a reference coding nobody wrote down — would pick an estimand and
call it an implementation detail.

## 2. The four alternatives

| | Alternative | Design matrix | Estimand | Identified because | Assumptions | Family confounding | Interpretability | Primary-design impact | Complexity |
|---|---|---|---|---|---|---|---|---|---|
| **A1** | one intercept per family, all six | 6 dummies + $d$ + $\mathbb{1}$, 8 params, 12 points | **none** | it is not — $\mathbb{1}$ = sum of the three near-form dummies | — | — | — | none | never constructed |
| **A2** | $\alpha_f$ over the **three core** families; a Tier-2 point sits at the unweighted mean core intercept plus $\gamma$ | 3 dummies (Tier-2 rows carry $1/3$ in each) + $d$ + $\mathbb{1}$, 5 params, 12 points | $\gamma$ = the Tier-2 offset from the difficulty line the three core families define, at equal weight over them | 5 params, 12 points, full rank | the three core families' levels are the reference level, weighted equally | **removed** — each core family keeps its own level | direct: "how far above the core line a same-operator, different-statistic companion sits at the same difficulty" | **none** | 5 lines |
| **A3** | one intercept per core family + one shared Tier-2 intercept; $\gamma$ **not estimated** | 4 dummies + $d$, 5 params | no $\gamma$; the tier's contribution is read off the fourth intercept | full rank | same as A2 | removed | equivalent in fitted values to A2, but the offset is a difference of intercepts | none | 4 lines, **but it deletes a registered F8 member** |
| **A4** | one common intercept | 1 + $d$ + $\mathbb{1}$, 3 params | $\gamma$ = the Tier-2 offset from a **pooled** line that ignores between-family level differences | full rank | **all families share one level** | **present** — level differences load onto $\beta$ | superficially simplest, actually the hardest: $\beta$ means something different from the primary's $\beta$ | none | 2 lines |

## 3. Why they are not reparameterisations of each other

A2 and A4 are **not** the same model written two ways, and this is the point
the comparison turns on. Twelve noiseless points generated from a known
$\beta = 0.300$, $\gamma = 0.080$, with family levels $(0.10, 0.16, 0.22)$ and
family difficulty spans that do not overlap — a configuration §13.8 permits,
because its caliper matches each reference to **A**, not the references to each
other:

| | $\beta$ recovered | $\gamma$ recovered |
|---|---:|---:|
| truth | 0.300 | 0.080 |
| **A2** | **0.300** | **0.080** |
| A4 | 0.488 | 0.080 |

A4's slope is inflated by 63%, because the pooled intercept leaves the
between-family level differences nowhere to go but $\beta$. §11.8's **primary**
fit registers three family intercepts precisely to remove them, so under A4 the
secondary's $\beta$ and the primary's $\beta$ are different quantities under one
name — and $\delta_{\text{difficulty}}$, a primary-tier F1 member, is read
against the primary's line.

Worse, A4's $\gamma$ is not stable either. Holding everything fixed and moving
only **where the three near-form controls sit in difficulty** — a placement
§13.9 chooses on closeness to A, and which has nothing to do with the tier:

| near-form placement | A2 $\gamma$ | A4 $\gamma$ |
|---|---:|---:|
| low ($d \approx 0.20{-}0.36$) | 0.080 | **0.134** |
| centred ($d \approx 0.40{-}0.70$) | 0.080 | 0.080 |
| high ($d \approx 0.75{-}0.90$) | 0.080 | **0.024** |

A factor of 5.6 in a quantity generated from a single fixed value. A2 returns
0.080 in all three. **A4's $\gamma$ answers a question about the near-form
controls' position; A2's answers a question about their tier.** They are
different estimands, and only one of them is the structural-tier question
§11.8 asks.

## 4. Recommendation

> **Resolve U2 at A2**, and amend §11.8 to state that $\alpha_f$ ranges over
> the three **core** families, with a Tier-2 point predicted at the unweighted
> mean core intercept plus $\gamma$.

Five reasons, in the order they matter:

1. **It answers the question §11.8 asks.** $\gamma$ is the offset of a
   same-operator, different-statistic companion from the line the core pool
   defines at the same difficulty — a structural-tier quantity. A4's is a
   placement quantity.
2. **It leaves the primary alone in every sense.** No change to sampling, to
   reference selection, to the arms, to the cell set, or to any claim's
   interpretation. The secondary reads twelve points that already exist.
3. **It matches §15 F8 as registered.** F8 lists eleven members including
   `alpha_1`, `alpha_2`, `alpha_3` and `gamma_tier`. A2 reports exactly three
   intercepts and a $\gamma$. A3 reports four intercepts and no $\gamma$,
   which deletes a registered member — a §32 amendment to §15, for no gain in
   what is learned.
4. **It matches §11.8's own convention elsewhere.** The section's prediction
   at $\iota_A$ already uses the average family intercept; A2 uses the same
   average for the Tier-2 rows, so the section acquires no second convention.
5. **It is the same amount of code.** A2 and A4 are both constructed already;
   neither is cheaper to run.

**What A2 assumes, stated so it can be disagreed with.** The three core
families' levels are equally weighted in defining the reference line. With
three families and no basis for weighting them differently, equal weight is the
only choice that does not import a preference — but it *is* a choice, and if a
core family turns out to be an outlier in level, $\gamma$ moves with it. §11.8's
existing prediction-at-$\iota_A$ convention makes the same assumption, so
adopting A2 does not add one.

**What none of the four can fix.** $\gamma$ is estimated from **three** Tier-2
points against nine Tier-1 points. Whatever the parameterisation, it is a
low-precision quantity, it licenses no claim level, and F8 is a secondary
family. It should be reported with its interval and read as a diagnostic. A2
does not make it precise; it makes it *mean something*.

**What happens without the near-form arm.** All three near-form controls are
the only Tier-2 points in the fit, so a replication that drops the arm has an
indicator that does not vary and $\gamma$ is not identified at all. The code
already refuses with that message, and the status is
`NEAR_FORM_ARM_NOT_AVAILABLE`. This is a **second, independent reason** the
near-form arm is not free in §34 D1 — the first being D18's closure.

## 5. The choice, as taken

Both were done, on 2026-08-23:

1. **U2 is resolved at A2**, recorded in `researcher_decisions.json` under
   `open_items` with who resolved it and when. `open_items` reads that record
   at import, exactly as `decisions` reads the closures, so the resolution
   survives the process and the manifest binds it by the same hash.
2. **§11.8's sentence is amended** so `alpha_f` names the three core families
   explicitly. Until that amendment the section and the code disagreed about
   what was being fitted, which is the state U2 recorded.

`fit_with_tier_indicator` now runs A2 by default — and *only* because U2 is
resolved: it still refuses if the resolution goes away, rather than falling
back to A2, which is what would have happened had adoption been done by
writing `formulation="A2"` into the signature. `TierFit.adopted` says on the
object's own face whether the construction is the registered one, and
`assert_adopted_formulation` refuses a non-adopted fit on any reporting path.

**A4 stays constructed and non-adopted.** It is not dead code: the comparison
in §3 above is computed from it on every test run, so the evidence for
preferring A2 is recomputed rather than quoted. A1 is refused by name as
singular and A3 is never constructed.
