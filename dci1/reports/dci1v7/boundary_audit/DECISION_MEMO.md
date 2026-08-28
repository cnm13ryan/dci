# DCI-1 v7 §13.14 — boundary-handling audit: decision memo

*2026-08-28, on the unadopted v7 draft, before any registration act.*
Scope: the boundary machinery only — the Wilson allowance, the structural-zero
rule, the compressed-direction reading, Gate 4's non-adaptivity and the sign
convention. The paired estimand, the 384-block design, the block bootstrap at
10,000 resamples, the frozen A/R selection and the SESOI are treated as fixed
and were not touched.

Everything numerical here was produced by `dci1/tools/v7_boundary_audit.py`
running the **production** analysis path — `ObservationTable` → the registered
estimators → `bootstrap_family` (studentised maximum-modulus over the F1
family, 10,000 resamples) → `boundary.contrast_boundary_from_table` →
`apply_allowance` → `claims.Interval` → `claims.delta_r_reading` /
`contrast_direction` / `emit_l3` — on simulated 384 × 8 paired tables. No
estimator, interval or rule was re-implemented. Machine-readable results:
`simulation_baseline.json`, `simulation_indep.json`, `simulation_grounded.json`,
`replicates_*.jsonl.gz` (one line per simulated experiment), `toy_cases.json`
beside this file.

The distinction the audit was asked to keep: *the code implements the intended
rule* (the v7 tests establish this) versus *the intended rule is valid* (this
memo).

---

## 1. The current v7 rule, as implemented

Read off `dci1/src/dci1v7/analysis/boundary.py`, `analysis/bootstrap.py`,
`analysis/claims.py` and `run/analysis_run.py::_intervals`.

**Interval.** For each family and configuration, `bootstrap_family` resamples
the 384 blocks with replacement (one index draw per replicate shared by every
member), standardises each member by its bootstrap standard error, takes the
95th percentile of the maximum absolute standardised deviation across the
family as the critical value *c*, and reports `estimate ± c·se`. For the F1
family (D(B←A), D(A←B), Λ, Δ_R, δ_diff, Ξ) *c* ≈ 2.5 in simulation, against
1.96 for a one-member family. This simultaneous interval is what every claim
rule reads; the marginal percentile interval is reported beside it (§17.1) and
decides nothing.

**Exact boundary trigger.** A constituent cell is "at an exact boundary" only
when *every* block mean is exactly 0 or exactly 1 (`classify_cell`,
tolerance 1e-12). A cell with 3,071 of 3,072 draws perfect is not.

**Allowance (reading 2).** For each constituent at an exact boundary, the
decision interval is widened in the *open* direction only by
`|weight| × h_n`, where `h_n = 1 − Wilson(1, n).lower` at `n` = block count
and the registered 95% two-sided *z*: `h_384 = 0.0099`, `h_192 = 0.0196`,
`h_24 = 0.138`. Because the two-sided *z* is used, each side is a 97.5%
one-sided bound at the block level. The draw count inside a block is not used
(blocks are the unit; draws within a block are correlated).

**Compressed direction (reading 3).** For a two-arm contrast with arm levels
`L_P`, `L_N`, the positive direction is flagged compressed when `L_N > 0.90`
or `L_P < 0.10`, the negative when `L_P > 0.90` or `L_N < 0.10`. Descriptive:
the licensing rule reads the interval exactly as registered; the status says
why the number came out as it did.

**Structural zero (reading 1) — as found.** When every weighted constituent
sits at the *same* exact boundary the contrast is 0 with zero observed
variance; the decision interval is the allowance alone, `[−h_n, +h_n]`; and
`claims.delta_r_reading`, `delta_near_reading`, `joint_reading` and the L1 /
L2 / L4b emitters **vetoed every classification** (levels `[]`, marker
`STRUCTURAL_ZERO`, no equivalence, no direction).

**No terminal status.** None of the three readings terminates, drops an arm or
moves a threshold (`terminates: False` on every record); the withdrawn
`COMPOSED_HEADROOM_*` statuses have no raise path in the package (V1).

---

## 2. Simulation results

**Design.** 384 blocks × 8 draws; a topic effect `u_b ~ N(0, τ²)` shared by
every cell of a block, a cell-by-topic deviation `N(0, ω²)`, Bernoulli draws;
target rates are *marginal* rates (the intercept is solved so the mean over
the block distribution equals the target), so the true Δ_R is exactly the
difference of the target rates. A target of exactly 0 or 1 is deterministic.
A "clustered" arm is a mixture of perfect blocks and half-rate blocks — the
worst case for a block-level bound. Baseline τ = 1.0, ω = 0.5 (a rate of 0.90
spans roughly 0.55–0.985 across blocks); sensitivity runs at τ = ω = 0
(independent draws) and τ = 2.0, ω = 1.0 (heavy clustering). 1,000
experiments per scenario, 10,000 resamples each; the Monte-Carlo standard
error of a coverage near 0.95 is 0.007.

Five members of F1 are simulated (all but δ_diff, which needs the spectrum
fit), so the family critical value is slightly *below* production's — the
simulated decision interval is, if anything, narrower than the real one.

**Columns.** `dec` = coverage of the decision interval (simultaneous +
allowance; what the claims read). `sim` = the same without the allowance.
`alone` = the decision interval for a one-member family (*c* ≈ 1.96; the fair
test of the procedure's own calibration). `fam` = all five simulated members
covered simultaneously by their decision intervals. `w` = mean decision width.
`sz` = share of experiments that were a structural zero. `wrong` = share
whose decision interval excluded zero on the wrong side (under a true null,
the directional false-positive rate).

### 2.1 Baseline (τ = 1.0, ω = 0.5)

| scenario | P(B∣B+A) / P(B∣B+R) | true Δ_R | dec | sim | alone | fam (no allowance → with) | w | sz | wrong | L3 reading |
|---|---|---|---|---|---|---|---|---|---|---|
| interior_null | 0.70 / 0.70 | 0 | 0.988 | 0.988 | 0.949 | 0.952 → 0.952 | 0.050 | 0 | 0.002 | L3c 100% |
| interior_pos_030 | 0.60 / 0.90 | +0.30 | 0.979 | 0.979 | 0.941 | 0.954 → 0.954 | 0.057 | 0 | 0 | L3a 100%, L3b 96% |
| interior_neg_030 | 0.90 / 0.60 | −0.30 | 0.986 | 0.986 | 0.943 | 0.936 → 0.936 | 0.049 | 0 | 0 | L3c 100% (A better) |
| sesoi_pos_010 | 0.80 / 0.90 | +0.10 | 0.980 | 0.980 | 0.946 | 0.942 → 0.942 | 0.043 | 0 | 0 | indeterminate@0.10 98%, L3a 0.9%, L3c 1.1% |
| inside_equiv_008 | 0.80 / 0.88 | +0.08 | 0.985 | 0.985 | 0.942 | 0.954 → 0.954 | 0.043 | 0 | 0 | L3c 41% |
| specific_025 | 0.60 / 0.85 | +0.25 | 0.978 | 0.978 | 0.934 | 0.938 → 0.938 | 0.055 | 0 | 0 | L3a 100%, L3b 0.9% |
| high_090 | 0.90 / 0.90 | 0 | 0.983 | 0.983 | 0.940 | 0.943 → 0.943 | 0.033 | 0 | 0.017 | L3c 100% |
| high_095 | 0.95 / 0.95 | 0 | 0.989 | 0.989 | 0.948 | 0.949 → 0.949 | 0.023 | 0 | 0.003 | L3c 100% |
| high_099 | 0.99 / 0.99 | 0 | 0.984 | 0.984 | 0.944 | 0.944 → 0.944 | 0.011 | 0 | 0.003 | L3c 100% |
| high_0995 | 0.995 / 0.995 | 0 | 0.996 | 0.996 | 0.964 | 0.955 → 0.955 | 0.007 | 0 | 0.004 | L3c 100% |
| high_0999 | 0.999 / 0.999 | 0 | 0.998 | 0.964 | 0.985 | **0.929 → 0.959** | 0.004 | 0 | 0.002 | L3c 100% |
| high_09995 | 0.9995 / 0.9995 | 0 | 1.000 | 0.958 | 0.998 | **0.920 → 0.961** | 0.007 | 0.004 | 0 | L3c 99.6%, sz 0.4% |
| high_unequal | 0.999 / 0.99 | −0.009 | 0.995 | 0.993 | 0.948 | 0.946 → 0.948 | 0.007 | 0 | 0 | L3c 100% |
| ceil_A_099 | **1.00** / 0.99 | −0.01 | 0.979 | 0.979 | 0.949 | 0.943 → 0.948 | 0.016 | 0 | 0 | L3c 100% |
| ceil_A_095 | **1.00** / 0.95 | −0.05 | 0.983 | 0.983 | 0.964 | 0.943 → 0.948 | 0.027 | 0 | 0 | L3c 100% |
| ceil_A_090 | **1.00** / 0.90 | −0.10 | 0.983 | 0.978 | 0.967 | 0.940 → 0.946 | 0.038 | 0 | 0 | L3c 100% |
| ceil_A_0995 | **1.00** / 0.995 | −0.005 | 0.980 | 0.979 | 0.946 | 0.943 → 0.949 | 0.014 | 0 | 0 | L3c 100% |
| ceil_A_09995 | **1.00** / 0.9995 | −0.0005 | 1.000 | **0.938** | 1.000 | **0.905 → 0.968** | 0.013 | 0.007 | 0 | L3c 99.3%, sz 0.7% |
| ceil_R_099 | 0.99 / **1.00** | +0.01 | 0.988 | 0.987 | 0.964 | 0.947 → 0.948 | 0.020 | 0 | 0 | L3c 100% |
| ceil_both | **1.00 / 1.00** | 0 | 1.000 | 1.000 | 1.000 | 0.954 → 0.962 | 0.020 | **1.000** | 0 | *current:* none (STRUCTURAL_ZERO); *counterfactual:* L3c 100% |
| ceil_A_mixed_refs | **1.00** / (1, 1, 0.97) | −0.01 | 1.000 | 0.976 | 1.000 | **0.920 → 0.946** | 0.023 | 0 | 0 | L3c 100% |
| ceil_A_clustered_R_001 | **1.00** / 1% half-rate blocks | −0.005 | 0.984 | 0.975 | 0.947 | 0.938 → 0.952 | 0.018 | 0 | 0 | L3c 100% |
| ceil_A_clustered_R_002 | **1.00** / 2% half-rate blocks | −0.01 | 0.976 | 0.975 | 0.943 | 0.938 → 0.944 | 0.021 | 0 | 0 | L3c 100% |
| clustered_both_001 | 1% half-rate blocks, both arms | 0 | 0.981 | 0.960 | 0.945 | **0.922 → 0.941** | 0.016 | 0 | 0.019 | L3c 100% |
| low_001 | 0.01 / 0.01 | 0 | 0.985 | 0.985 | 0.947 | 0.957 → 0.957 | 0.011 | 0 | 0.015 | L3c 100% |
| floor_A_001 | **0.00** / 0.01 | +0.01 | 0.987 | 0.986 | 0.963 | 0.951 → 0.966 | 0.016 | 0 | 0 | L3c 100% |
| floor_both | **0.00 / 0.00** | 0 | 1.000 | 1.000 | 1.000 | 0.946 → 0.965 | 0.020 | **1.000** | 0 | as ceil_both |
| near_ceiling_pos | 0.85 / 0.99 | +0.14 | 0.992 | 0.992 | 0.951 | 0.947 → 0.947 | 0.043 | 0 | 0 | L3a 99.7% |
| near_floor_neg | 0.15 / 0.01 | −0.14 | 0.983 | 0.983 | 0.945 | 0.955 → 0.955 | 0.043 | 0 | 0 | L3c 100% (A better) |

All 39 scenarios are in `simulation_baseline.json`; the omitted rows behave
like their neighbours above. The precision precondition (half-width ≤ 0.05)
was met in every experiment of every scenario; the widest mean decision
interval is 0.057.

### 2.2 What the numbers say

1. **The decision interval never under-covers.** Marginal coverage of Δ_R's
   decision interval is 0.976–1.000 in every scenario, interior or boundary.
   It is a simultaneous interval read for one member, so ~0.98 is its design
   value, not a boundary artefact: the interior rows show the same.
2. **The procedure's own calibration is ordinary and not boundary-specific.**
   The one-member interval (`alone`) sits at 0.934–0.951 in interior
   scenarios — the usual ~1% anticonservatism of a bootstrap interval at
   n = 384 — and at 0.943–1.000 near and at the boundaries. Nothing near a
   boundary is worse than the interior; the exact-boundary cases are, if
   anything, over-covered.
3. **The allowance is necessary and it works.** Without it, the *family*
   simultaneous coverage falls to 0.905–0.929 whenever some cell of some
   member sits at an exact boundary (ceil_A_09995, high_09995,
   ceil_A_mixed_refs, clustered_both_001, high_0999): the bootstrap sees no
   variance from that cell and the family's critical value cannot know. With
   the allowance every one of those recovers to 0.941–0.968. Its cost is
   bounded by `2 × h_384 = 0.020` of width, one fifth of the SESOI, and it
   changed no L3 verdict and no precision verdict in any scenario.
4. **The marginal percentile interval is not fit for decisions near a
   boundary** (0.829 at 0.9995/0.9995, 0.918 clustered) — and the rules do not
   read it. It stays a §17.1 companion column.
5. **Direction.** Under every true null the directional false-positive rate is
   0.002–0.019 (the simultaneous interval is conservative); with |Δ_R| ≥ 0.10
   a direction is claimed in 100% of experiments and never the wrong one. At
   Δ_R = +0.10 exactly, 98% of experiments are `INDETERMINATE@0.10` and the
   two classifications split 0.9% / 1.1% — the threshold behaves as a
   threshold.
6. **Equivalence.** L3c is one-sided by registration (`upper < 0.10`, "no
   excess"), so it is read at Δ_R = −0.30 as well as at 0 — with the
   direction label `A_COMPARATIVELY_BETTER` on the statement (v7 §28.1). At
   Δ_R = +0.08 it is read 41% of the time, at +0.10 1.1%.
7. **The structural zero.** At a shared exact boundary the decision interval
   is `[−0.0099, +0.0099]`; it covered the true contrast in 1,000 of 1,000
   experiments in every shared-boundary process tried, including the 0.4–0.7%
   of 0.9995-rate tables that happened to come out perfect. The current rule
   reads nothing there; the counterfactual (veto lifted, nothing else changed)
   reads L3c in 100% of them, and never a direction.

### 2.3 Sensitivity (τ = ω = 0 and τ = 2.0, ω = 1.0)

Sixteen scenarios re-run at 1,000 experiments each under independent draws
(`simulation_indep.json`) and under heavy clustering (`simulation_grounded.json`;
τ = 2 on the logit scale means a 0.995-rate arm has block rates from about 0.5
to 1, with its failures concentrated in roughly 2–3% of blocks). Each cell is
`dec / alone / fam(no allowance → with)`.

| scenario | true Δ_R | baseline τ=1, ω=0.5 | independent draws | heavy clustering τ=2, ω=1 | w (heavy) | sz (heavy) | wrong (heavy) |
|---|---|---|---|---|---|---|---|
| interior_null | 0 | 0.988 / 0.949 / 0.952→0.952 | 0.989 / 0.956 / 0.951→0.951 | 0.982 / 0.954 / 0.936→0.936 | 0.055 | 0 | 0.002 |
| sesoi_pos_010 | +0.10 | 0.980 / 0.946 / 0.942→0.942 | 0.980 / 0.944 / 0.933→0.933 | 0.979 / 0.942 / 0.938→0.938 | 0.050 | 0 | 0 |
| inside_equiv_008 | +0.08 | 0.985 / 0.942 / 0.954→0.954 | 0.981 / 0.954 / 0.947→0.947 | 0.986 / 0.946 / 0.951→0.951 | 0.049 | 0 | 0 |
| high_099 | 0 | 0.984 / 0.944 / 0.944→0.944 | 0.994 / 0.953 / 0.949→0.949 | 0.983 / 0.943 / 0.938→0.938 | 0.012 | 0 | 0.003 |
| high_0995 | 0 | 0.996 / 0.964 / 0.955→0.955 | 0.996 / 0.953 / 0.947→0.947 | 0.986 / 0.951 / 0.936→0.936 | 0.008 | 0 | 0.014 |
| high_0999 | 0 | 0.998 / 0.985 / 0.929→0.959 | 0.994 / 0.976 / 0.896→0.944 | 0.991 / 0.974 / 0.913→0.939 | 0.005 | 0 | 0.009 |
| high_09995 | 0 | 1.000 / 0.998 / 0.920→0.961 | 1.000 / 0.999 / 0.901→0.952 | 1.000 / 0.998 / 0.925→0.952 | 0.007 | 0.007 | 0 |
| ceil_A_099 | −0.01 | 0.979 / 0.949 / 0.943→0.948 | 0.990 / 0.956 / 0.949→0.957 | **0.965 / 0.929 / 0.921→0.925** | 0.019 | 0 | 0 |
| ceil_A_0995 | −0.005 | 0.980 / 0.946 / 0.943→0.949 | 0.984 / 0.948 / 0.943→0.952 | **0.952 / 0.891 / 0.910→0.912** | 0.016 | 0 | 0 |
| ceil_A_09995 | −0.0005 | 1.000 / 1.000 / 0.905→0.968 | 1.000 / 1.000 / 0.910→0.970 | 1.000 / 1.000 / 0.864→0.959 | 0.014 | 0.022 | 0 |
| ceil_both | 0 | 1.000 / 1.000 / 0.954→0.962 | 1.000 / 1.000 / 0.943→0.949 | 1.000 / 1.000 / 0.938→0.947 | 0.020 | 1.000 | 0 |
| clustered_both_001 | 0 | 0.981 / 0.945 / 0.922→0.941 | 0.984 / 0.952 / 0.928→0.941 | 0.981 / 0.945 / 0.927→0.946 | 0.016 | 0 | 0.019 |
| ceil_A_clustered_R_001 | −0.005 | 0.984 / 0.947 / 0.938→0.952 | 0.979 / 0.946 / 0.928→0.949 | 0.985 / 0.947 / 0.936→0.947 | 0.018 | 0 | 0 |
| low_001 | 0 | 0.985 / 0.947 / 0.957→0.957 | 0.989 / 0.956 / 0.947→0.947 | 0.986 / 0.947 / 0.948→0.948 | 0.012 | 0 | 0.014 |
| floor_A_001 | +0.01 | 0.987 / 0.963 / 0.951→0.966 | 0.987 / 0.951 / 0.940→0.955 | 0.972 / 0.937 / 0.928→0.949 | 0.020 | 0 | 0 |
| near_ceiling_pos | +0.14 | 0.992 / 0.951 / 0.947→0.947 | 0.982 / 0.946 / 0.950→0.950 | 0.982 / 0.948 / 0.953→0.953 | 0.056 | 0 | 0 |

**Reading.** Independent draws reproduce the baseline throughout: the
decision interval at 0.979–1.000, and the same family-level gap without the
allowance (0.896–0.910 at 0.999–0.9995) closed by it (0.944–0.970).

Heavy clustering exposes one place where the machinery is stretched, and it
is not the boundary rule: **an arm near the ceiling but not at it, with its
failures concentrated in a handful of blocks** (`ceil_A_0995`: A exact, the
references at 0.995 with ~8–12 imperfect blocks; `ceil_A_099` to a lesser
degree). There the block bootstrap's standard error rests on those few
blocks, the one-member interval under-covers (0.891, 0.929) in the way any
bootstrap does at a small effective sample, and the family coverage sits at
0.91–0.93 with or without the allowance — which is correct, because no cell
is at an exact boundary and the allowance is not owed. **The registered
decision interval still covers at 0.952 and 0.965**, held there by the F1
family's critical value. This is the *cliff* of §3 seen from the other side:
it is a property of the bootstrap with rare informative blocks, made visible
near a ceiling, and the exact-boundary trigger is not the cause. Everything
else under heavy clustering is at 0.972–1.000. No change is made for it; it
is recorded as the one limitation this audit found, with the reading rule
that follows: when a realised confirmatory table shows a near-ceiling arm
whose failures sit in fewer than ~15 blocks, the F1 half-width is protected
by the family inflation and not by the per-member bootstrap, and the reader
should know that a one-member interval there would be about 3–5 points short.

---

## 3. Wilson correction verdict: **keep**

The correction is statistically justified, and the simulation shows it is
*needed*:

- **Why the bootstrap fails there.** A cell whose every block mean is 1
  contributes exactly zero to every resample; the contrast's bootstrap
  variance is then the other arm's alone, and the family critical value is
  computed from deviations that omit that arm. Family coverage 0.905 without
  the allowance, at a process where the arm's true rate is 0.9995, is the
  measured consequence.
- **Why this particular repair is principled.** The only sampling statement
  the design licenses about a rate observed at 1 over `n` exchangeable blocks
  is the Wilson bound at `n`; `h_n` is derived from the registered *z* and the
  registered block count and from nothing chosen. It is applied per
  constituent, weighted by the constituent's weight, in the open direction
  only, and added to the simultaneous interval — a union bound, conservative
  by construction. Using blocks rather than draws is the right unit: draws
  within a block are correlated, and the clustered scenarios (1–2% of blocks
  at half rate, the adversarial case for a block-level bound) cover at
  0.976–0.984.
- **Is it unnecessarily conservative?** At an exact boundary the decision
  interval over-covers (1.000). The price is ≤ 0.02 of width and it moved no
  verdict at the registered thresholds. A draw-level bound (`h = 0.0012` at
  3,072 draws) would be invalid under any within-block dependence. Keep.
- **Under heavy clustering** (§2.3) a near-ceiling arm whose failures sit in
  a few blocks under-covers at the one-member level (0.89–0.93) because the
  bootstrap has few informative blocks; the registered decision interval
  holds at 0.952–0.965 and no cell is at an exact boundary, so the
  allowance is neither owed nor the remedy. Recorded, not changed.
- **The cliff.** The trigger is exact: 3,072/3,072 perfect draws gets
  `+0.0099`, 3,071/3,072 gets `+0.0000` and an interval three times narrower
  on that side (`toy: A 383 ones + one block at 7/8 → half-width 0.0031`
  against `0.0080`). The simulation looked for the coverage loss this
  predicts — high_0995, high_0999, ceil_A_0995, high_unequal_0999_099 — and
  did not find it: the paired contrast's variance is carried by the arm that
  has failures, and the one-member coverage there is 0.946–0.985. The cliff
  is real as a discontinuity of width, not as a coverage defect. No change;
  recorded here so it is not rediscovered.

---

## 4. Structural-zero verdict: **modify — read it on its allowance interval**

**Claim A** ("A and R behave identically under arbitrary harder tasks") is not
the registered estimand and nothing in v7 asserts it. **Claim B** ("on the
registered task distribution the excess of A over its matched references is
below the SESOI") is exactly L3c's registered content — *no excess relative to
same-form exact-count companions* — and the question is whether a shared
exact boundary can validly support it.

It can, and the veto did not protect anything:

1. **Validity of the interval.** At a shared boundary the decision interval is
   `[−h_n, +h_n]`. Under the block-as-unit model each arm's true rate lies
   within `h_n` of the boundary with one-sided confidence 97.5% (the two-sided
   *z* is used), the lower side of the interval fails only if a reference
   arm's rate is below `1 − h_n` and the upper side only if A's is — disjoint
   events — so the interval covers at ≥ 95% by construction. Simulation:
   1,000/1,000 at every shared-boundary process.
2. **Type I error for equivalence.** An L3c read at a structural zero while
   `|Δ_R| ≥ 0.10` requires every draw of every differenced cell to be perfect
   while some arm's true rate is ≤ 0.90: probability below `0.90^384`. The
   veto guarded against an event that cannot occur.
3. **Coherence of the evidence map.** Under the veto a table with 3,072/3,072
   perfect draws on every cell licensed *less* than a table with 3,071/3,072
   on one of them, which the rule already read as L3c with
   `COMPOSED_CONTRAST_RANGE_COMPRESSED`. More evidence for Claim B withdrew
   the claim. That is a defect in the rule, not a safeguard.
4. **What the veto actually carried** is a construct-validity qualification:
   the composed set did not discriminate, and Claim B is *bounded* rather than
   *measured*. That is already what `COMPOSED_ARM_AT_BOUNDARY` and
   `COMPOSED_CONTRAST_RANGE_COMPRESSED` say for the 0.999 case, and it is
   what §26's `NOT_MET` ("Δ_R estimable on Gate 4's composed set: not a
   structural zero") records for the design. The status stays; a registered
   sentence is added to the statement.
5. **Lifting the veto can add only equivalence-type readings.** The interval
   is symmetric about zero at every block count, so no lower bound above zero
   and no upper bound below zero exists: L1, L2, L3a, L3b, L3d and L4b remain
   unreachable, and the direction is `DIRECTION_UNRESOLVED`. The only
   readings that change are Δ_R's L3c and Δ_near's "below".
6. **Block count does the honest work.** At 384 blocks `±0.0099` lies inside
   the ±0.10 region and meets the 0.05 precondition → L3c. At Gate 4's 24
   topics `±0.138` does neither → no level, `INSUFFICIENT_PRECISION`. At
   the probe's 192 topics `±0.0196` → L3c on the projection. The rule reads
   the same way everywhere and its answer scales with the evidence.

The equivalence criterion itself — interval inside ±0.10, half-width ≤ 0.05 —
is unchanged. What changed is that a valid interval is no longer vetoed.

**Registered as V10** (`protocol/revision.py`, with an executable check that
the shared-boundary decision interval is `±h_n`, reads L3c at 384 and nothing
at 24, and never a direction); preregistration §13.14 reading 1, §5 and §7
amended with the date and the reasons; `STRUCTURAL_ZERO_SENTENCE` attached to
every L3 statement read there; §26 unchanged.

---

## 5. Gate-4 leakage audit: **genuinely descriptive and non-adaptive**

Traced from the production code and `run/contracts.py` (every consumer of
`GATE_4_COMPOSED_CONTRAST` and `GATE_2_75_COMPOSED_PROBE`; the execution-path
audit's 74 rules agree).

**Where each design fact is fixed, and that it is fixed before Gate 4:**

| fact | fixed at | evidence |
|---|---|---|
| n* | Gate 2 (stage 6) | `contracts.py` `_f(G2, "n_star", (G25, G275, G3B, G4, G5, CONF))` |
| m* | Gate 2 (stage 6), §12.3 on B's solo curve | `gates_run.effective_m_star` returns Gate 2's value and refuses a probe record that disagrees; `composed_probe.assert_m_star_unmoved` on the producing side |
| reference set R_j, severity, slot map | Gate 3B (stage 10), `feasibility.selection_at` on calibration data | `gates_run.py:1888-1903` |
| admitted arms / cell count | Gate 3C (stage 11) | `gates_run.py:1985` |
| instruction order | design constant: every block runs both orders of every composed cell (§8.4) | `freeze_run.py:243` |
| model / configuration, completion cap | registration; REGIME_SCREEN | `contracts.py:101` |
| N_BLOCKS = 384, M_DRAWS = 8 | literals, bound at the freeze, asserted at CONFIRMATORY | `freeze_run.py:255`, `confirmatory_run.py:96` |

Gate 2.75 is stage 8 and Gate 4 is stage 12 of 19; neither is upstream of any
row above.

**Every consumer of the Gate 4 record:**

| consumer | reads | feeds |
|---|---|---|
| `freeze_run.assemble` | the whole `composed_contrast` projection | bound into the freeze as `composed_contrast_projection` — description |
| `freeze_run.assemble` | `outcome`, truthiness of `composed_contrast` | completeness refusal (an empty projection stops the freeze); `outcome` is the constant `PASS` |
| `identification.assert_not_rehabilitated` | every member the record offers a number for | refuses a projection that names a member Gate 3C dropped — a presence/consistency guard, not a threshold on any estimate |
| `prefreeze_run.gate4_evidence_complete` | `composed_table`, `admitted_arms`, `rows`, `expected_rows`, `outcome` | completeness only; `contrast_statuses` is recorded in the detail and compared to nothing |
| `audit_prefreeze` check 8 | `outcome`, top-level key *names*, `declared_refusals` | name scan for selection tokens: a check that Gate 4 *cannot* select |
| `support.methodological_success` | `F1:<cfg>.members.Delta_R.boundary.structural_zero` (via the freeze) | §26 `MET`/`NOT_MET` on the final report; terminates nothing; no later check reads it |
| `analysis_run._boundary_summary` | `members[*].statuses` | placed beside the realised readings; `projected_and_realised_agree` is recorded and branches nothing |

**Every consumer of the Gate 2.75 record:** one field reaches a design
quantity — `m_star` — and on every path it is asserted equal to Gate 2's
(`effective_m_star`, `gate3a_payload`, `assert_m_star_unmoved`). The other
twelve fields are bound by the freeze for the record and read by no rule.

**One hardening made.** `freeze_run.freeze_payload` wrote B's confirmatory
severity as `int(probe["m_star"])` — a copy from the probe record without a
local equality assertion (correct only because the producer guard makes a
disagreeing signed record impossible). It now reads
`effective_m_star(tree)`, so the operating point the study runs is bound
through the checked equality and no record written after a composed outcome
supplies it on its own. The v6-era test that pinned the copy
(`test_the_freeze_binds_b_at_the_probes_operating_point_not_gate_2s`) encoded
v5/v6 semantics in which the probe could move m*; it is rewritten to v7's.

**Termination surface.** Gate 2.75 and Gate 4 have exactly one outcome each
(`PASS`); the only `TerminalStatus` raise between Gate 2 and the freeze is
Gate 3C's `REFERENCE_SUPPORT_NOT_IDENTIFIED`, whose input is §13.15 support,
not any composed reading. A Gate 4 record can stop the lifecycle only through
completeness (empty projection, incomplete table, missing record), never
through the value of an estimate.

Conclusion: Gate 4 may observe an extreme composed result; nothing downstream
can use it to choose R_j, severity, m*, n*, order, model, the admitted set,
the sample size, or whether the confirmatory arm is generated.

---

## 6. Direction sanity check (`toy_cases.json`, deterministic tables, 10,000 resamples)

Δ_R = mean_j P(B∣B+R_j) − P(B∣B+A). Positive means the references deliver B
better than A does — **A harms more**.

| case | P(B∣B+A) | P(B∣B+R) | estimate | decision interval | direction label | levels | statuses | L3 statement |
|---|---|---|---|---|---|---|---|---|
| 1 — A permits better B delivery | 0.90 | 0.60 | −0.3000 | [−0.306, −0.294] | `A_COMPARATIVELY_BETTER` | L3c | RANGE_COMPRESSED | L3c emitted, direction `A_COMPARATIVELY_BETTER`, scope `same_form_only` |
| 2 — A damages B more | 0.60 | 0.90 | +0.3000 | [+0.294, +0.306] | `A_HARMS_MORE` | L3a, L3b | RANGE_COMPRESSED | L3a and L3b emitted, direction `A_HARMS_MORE` |
| 3 — as 1, A arm at 0.92 | 0.92 | 0.60 | −0.3200 | [−0.326, −0.314] | `A_COMPARATIVELY_BETTER` | L3c | RANGE_COMPRESSED (positive direction closed by A's level) | as 1 |
| 4 — as 2, R arm at 0.92 | 0.60 | 0.92 | +0.3200 | [+0.314, +0.326] | `A_HARMS_MORE` | L3a, L3b | RANGE_COMPRESSED | as 2 |
| exact zero, interior | 0.70 | 0.70 | +0.0000 | [−0.006, +0.006] | `DIRECTION_UNRESOLVED` | L3c | — | L3c, direction unresolved |
| near zero | 0.70 | 0.72 | +0.0200 | [+0.014, +0.026] | `A_HARMS_MORE` (below SESOI) | L3c | — | L3c, `beyond_sesoi: False` |
| near zero | 0.72 | 0.70 | −0.0200 | [−0.026, −0.014] | `A_COMPARATIVELY_BETTER` | L3c | — | L3c |
| shared ceiling | 1.00 | 1.00 | 0.0000 | [−0.0099, +0.0099] | `DIRECTION_UNRESOLVED` | *before V10:* none; *V10:* L3c | STRUCTURAL_ZERO, ARM_AT_BOUNDARY, RANGE_COMPRESSED | *V10:* L3c with `structural_zero_sentence` |
| shared floor | 0.00 | 0.00 | 0.0000 | [−0.0099, +0.0099] | `DIRECTION_UNRESOLVED` | as above | as above | as above |
| A exact ceiling only | 1.00 | 0.95 | −0.0500 | [−0.054, −0.036] | `A_COMPARATIVELY_BETTER` | L3c | ARM_AT_BOUNDARY, RANGE_COMPRESSED | upper widened by +0.0099 |
| R exact ceiling only | 0.95 | 1.00 | +0.0500 | [+0.034, +0.056] | `A_HARMS_MORE` | L3c | ARM_AT_BOUNDARY, RANGE_COMPRESSED | lower widened by −0.0099 |
| A exact floor only | 0.00 | 0.05 | +0.0540 | [+0.041, +0.058] | `A_HARMS_MORE` | L3c | ARM_AT_BOUNDARY, RANGE_COMPRESSED | — |

The estimator's sign, the block-vector mean, the direction label, the
human-readable reading, the claim ladder, the L3 statement's `direction`
field and the boundary statuses agree in every case. The one thing a reader
must know is registered rather than inferred: **L3c is one-sided** ("no
excess", `upper < 0.10`), so it is read when A is *better* than its
references, and the statement then carries `A_COMPARATIVELY_BETTER`.

---

## 7. Minimal recommended changes — implemented in the draft

1. **V10 — structural zero read on its allowance interval** (§13.14 reading 1,
   §17.3). `claims.delta_r_reading` and `delta_near_reading` proceed by the
   registered rule on `[−h_n, +h_n]` and carry the `STRUCTURAL_ZERO` marker;
   `joint_reading` no longer has a "local structural zero" row;
   `l3_vacuity_agrees` compares the recoding as for any claim; the L1/L2/L4b
   emitters keep their early return (no direction by construction) with the
   reason reworded; `emit_l3` attaches `C.STRUCTURAL_ZERO_SENTENCE`; the
   status's registered meaning is rewritten; `revision.py` V10 with an
   executable check; preregistration §13.14/§5/§7 amended and dated; the
   reference design spec regenerated. Tests: `test_boundary.py`,
   `test_composed_contrast.py` (three tests rewritten or added, including
   "a structural zero can never license a direction" over block counts 2 to
   5,000), `test_reuse_and_revision.py` (ten changes).
2. **Freeze binds m\* through the checked equality**
   (`freeze_run.freeze_payload` → `effective_m_star(tree)`); the v6-era
   source pin rewritten to v7 semantics.
3. **Nothing else.** The Wilson allowance, the exact trigger, the block-level
   `n`, the compressed-direction reading, the SESOI, the precision
   precondition, §26 and the marginal-interval reporting are kept as
   registered. No threshold moves.

What remains non-identifiable under v7 is unchanged: fewer than three admitted
references (`REFERENCE_SUPPORT_NOT_IDENTIFIED`, Gate 3C), no spectrum support
(`DIFFICULTY_SUPPORT_NOT_IDENTIFIED`), a realised half-width above 0.05
(`INSUFFICIENT_PRECISION`), a vacuity-gate disagreement (§17.4), a missing or
partial cell (§21, fails closed). A structural zero at 24 topics is
`INSUFFICIENT_PRECISION` by the same rule as everything else.

---

## Provenance

- Simulation and toy cases: `dci1/tools/v7_boundary_audit.py` (this
  directory's JSON/JSONL are its outputs; the baseline took 3,915 s on 22
  workers).
- Gate 4 trace: `dci1/reports/dci1v7/execution_path_audit.md`,
  `v7_producer_consumer.md`, and the consumer list in §5 above.
- Code changed: `dci1/src/dci1v7/analysis/{claims,boundary}.py`,
  `protocol/{constants,revision}.py`, `run/freeze_run.py`,
  `tools/v7_reference_design_spec.py`; tests under `dci1/tests_v7/`.
- The v7 registration remains `DRAFT_NOT_ADOPTED`; adoption is the
  researcher's act.
