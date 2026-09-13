# What the v3 confirmatory rows do and do not identify about companion identity

**Classification: DERIVED / POST-HOC re-analysis of closed v3 evidence.**
Read-only. v3 is closed and its registered result stands as `dci1/RESULTS_V3.md`
records it. Nothing here changes a v3 artifact, and nothing here licenses a
confirmatory claim.

Produced by `dci1/tools/v3_reciprocal_reanalysis.py`; every number below is in
`dci1/reports/v3_reanalysis/result.json`.

---

## 1. The identification statement, first, because it is the point

The v3 confirmatory design runs six arms on the same 384 blocks — `A` (the
target alone), `AB`, `AR1`, `AR2`, `AR3`, and `TOPIC` — and **no solo cell for
B or for any reference**. That asymmetry is not incidental: in v3 the swapped
slot was the companion and the recorded outcome was always the exact-count
target. So:

| quantity | status on the v3 confirmatory rows |
|---|---|
| `D(A←B)`, `D(A←R_j)` | **identified**, same topics, paired within block |
| `Δ^A`, `Δ^A_j` | **identified**; the solo baseline cancels |
| companion uptake in the composed cell, joint success | **identified** |
| `D(B←A)` | **not identified** — no B solo cell on the confirmatory topics |
| `D(R_j←A)` | **not identified** — no reference solo cell there either |
| `D(R_j←B)` | **not identified** — no B+R_j cell exists in the v3 design at all |
| `Λ` | **not identified** — needs `D(B←A)` |
| `Δ_R` | **not identified** — needs `D(B←R_j)` |
| `Ξ` | **not identified** — needs reference-on-reference cells, absent by design |

The only solo rates for B and the references live in the Gate 2A cache, on the
**96 calibration topics** — a disjoint set. Pairing across the two sets
manufactures a contrast the experiment never ran. §3 reports that cross-set
quantity anyway, bounded, because a previous review of this repository quoted it
without the bound.

**One reciprocal quantity is identified elsewhere and is worth naming here so
the gap is not overstated.** The B+R pilot generated B+R_j cells on the same 96
calibration topics the Gate 2A solo cells use, so `D(R_j←B)` **is** paired
within topic there, and the pilot reports it: −0.063, −0.115 and +0.271 on E2B,
and −0.208, +0.057 and +0.318 on E4B. Two of three are negative on each model —
B *raises* those references' compliance. `D(R_j←A)` is identified nowhere: it
needs R_j solo on the confirmatory topics, and no stage generated it.

## 2. What is identified, with block-level uncertainty

All 16 cached draws enter every cell mean. Uncertainty is a block bootstrap over
the 384 confirmatory blocks, 10,000 resamples, resampled **within order
stratum**; per-reference intervals are studentised maximum-modulus simultaneous
intervals over the family of three. Order is a **block-level** factor in v3 —
192 blocks `target_first`, 192 `added_first`, constant within block — so the
order contrast is between disjoint sets of blocks and is not paired.

Both Qwen replications terminated at Gate 2A with `REFERENCE_POOL_MISMATCH` and
generated no confirmatory data. That is non-identification, not a null.

### gemma-3n-e2b-it — n\* = 5, references RF1:5, RF2:5, RF6:4

| quantity | estimate | 95% percentile | clustered SE |
|---|---:|---|---:|
| `D(A←B)` | **+0.1375** | [+0.1089, +0.1659] | 0.0152 |
| `D(A←RF1:5)` | +0.0815 | [+0.0532, +0.1087] | 0.0144 |
| `D(A←RF2:5)` | −0.0042 | [−0.0291, +0.0207] | 0.0127 |
| `D(A←RF6:4)` | +0.1436 | [+0.1165, +0.1712] | 0.0151 |
| **Δ^A** | **+0.0639** | [+0.0405, +0.0871] | 0.0118 |

Per-reference, simultaneous over the family of three:

| | estimate | 95% simultaneous |
|---|---:|---|
| Δ^A vs RF1:5 | +0.0560 | [+0.0214, +0.0905] |
| Δ^A vs RF2:5 | +0.1418 | [+0.1110, +0.1725] |
| Δ^A vs RF6:4 | **−0.0060** | [−0.0367, +0.0246] |

### gemma-3n-e4b-it — n\* = 7, references RF2:2, RF6:4, RF4:4

| quantity | estimate | 95% percentile | clustered SE |
|---|---:|---|---:|
| `D(A←B)` | **+0.1815** | [+0.1532, +0.2095] | 0.0145 |
| `D(A←RF2:2)` | +0.1056 | [+0.0754, +0.1357] | 0.0152 |
| `D(A←RF6:4)` | +0.1136 | [+0.0861, +0.1406] | 0.0139 |
| `D(A←RF4:4)` | +0.1042 | [+0.0736, +0.1336] | 0.0153 |
| **Δ^A** | **+0.0737** | [+0.0519, +0.0951] | 0.0111 |

Per-reference, simultaneous: +0.0758 [+0.0454, +0.1063], +0.0679 [+0.0396,
+0.0961], +0.0773 [+0.0463, +0.1083].

### Reading

Δ^A is positive and its interval excludes zero on both models. On both models it
also lies **below 0.10**, the threshold `dci-construct-pass2.md` §G row 1 (14
August 2026) sets for generic load, and far below the 0.25 that would support a
pair-specific reading. Under the registered rule as stated, this is the
generic-load region.

Δ^A is a **demoted diagnostic** in v4 (§11.5, §32) and it is gated: outcome
headroom, a companion matched on measured solo compliance, and the configuration
quoted with the number. All three hold here — A's solo compliance is 0.662 and
0.583, v3's references were admitted on a solo caliper against B, and the order
strata are reported below — so it is admissible at that level and no higher.

**On E2B the pooled number hides a disagreement the §13.4 qualifier exists for.**
The three per-reference values are +0.056, +0.142 and **−0.006**: against RF6:4,
B is not a worse companion at all. On E4B the three agree to within 0.010. A
single pooled Δ^A reported without the spread would be misleading on one of the
two models.

### Order

| model | stratum | `D(A←B)` | Δ^A | Δ^A 95% |
|---|---|---:|---:|---|
| E2B | `added_first` | +0.058 | +0.039 | [+0.005, +0.073] |
| E2B | `target_first` | **+0.217** | +0.089 | [+0.058, +0.120] |
| E4B | `added_first` | +0.198 | +0.082 | [+0.050, +0.115] |
| E4B | `target_first` | +0.165 | +0.065 | [+0.037, +0.094] |

On E2B `D(A←B)` differs by a factor of nearly four between the two
configurations. Averaging over order would report a number that describes
neither. On E4B order barely moves anything.

### Companion uptake and joint success, same topics

| model | uptake of B in `AB` | uptake of R̄ | joint success `AB` | joint success R̄ |
|---|---:|---:|---:|---:|
| E2B | 0.344 | 0.282 | 0.192 | 0.186 |
| E4B | 0.444 | 0.061 | 0.192 | 0.035 |

On E4B the three references are satisfied in 4–8% of composed responses. A
reference that is essentially never delivered is not a working control, and
`dci1/RESULTS_V3.md` already flags exactly this.

### Response length, recorded and not conditioned on

Mean words per response, by arm:

| model | `TOPIC` | `A` | `AB` | `AR1` | `AR2` | `AR3` |
|---|---:|---:|---:|---:|---:|---:|
| E2B | 331.6 | 273.1 | **127.9** | 159.0 | 146.6 | 184.2 |
| E4B | 333.6 | 326.5 | **139.1** | 186.0 | 174.6 | 172.0 |

Composition roughly halves response length, and **B shortens more than any
reference does**. Length is a registered mediator (v4r2 §13.3, §22) and is
reported here beside the estimand, never inside it.

### The same contrast at matched response length

The B-side companion contrast in the B+R pilot vanishes when the two cells are
compared at equal response length, because there the cells are five-fold apart
in words and barely overlap (`dci1/reports/pilot_reanalysis/`). The A side is
not like that. All four arms here contain A, so all four sit in the same length
regime — `AB` 127.9 words against `AR_j` 146.6–184.2 on E2B, a separation of
1.15–1.44× rather than 5.1× — and **all six word-count bins carry at least
thirty responses in every arm.**

| model | Δ^A raw | Δ^A within word-count bins | bins with ≥30 in all four arms |
|---|---:|---:|---:|
| E2B | +0.0639 | **+0.1178** | 6 of 6 |
| E4B | +0.0737 | **+0.0591** | 6 of 6 |

**Δ^A survives length matching.** Response length is a consequence of the
companion (v4r2 §13.3) and §22 forbids conditioning the primary estimand on it,
so this is a sub-population description and not a causal decomposition — but
unlike the B side, here it is a description with support behind it.

### Δ^A survives the registered vacuity bound, where the pilot's Δ does not

§17.4 registers the partial-identification recomputation: every estimand
recomputed with all vacuous passes forced to failures, no row dropped and
nothing conditioned on. Applied here:

| model | Δ^A raw | Δ^A §17.4-forced | change | vacuous passes in the composed arms |
|---|---:|---:|---:|---|
| E2B | +0.0639 | **+0.0634** | −0.0005 | 9 of 24,576 |
| E4B | +0.0737 | **+0.0720** | −0.0017 | 39 of 24,576 |

The A-side composed cells average 111–167 words and are essentially never
vacuous, so the bound barely moves. **The same bound applied to the B+R pilot's
Δ removes 72–82% of it** — +0.343 → +0.095 and +0.375 → +0.068
(`dci1/reports/pilot_reanalysis/`).

That asymmetry is not incidental. It is what a length-monotone **budget**
outcome does that an exact-count **production** outcome does not: B can be
satisfied by writing almost nothing, A cannot.

### And the length differential is itself order-dependent

Splitting by configuration changes the picture in a way the pooled number hides,
and the mechanism is visible in the arm lengths:

| model | configuration | mean words `AB` | mean words `AR̄` | Δ^A raw | Δ^A length-matched | bins |
|---|---|---:|---:|---:|---:|---:|
| E2B | `added_first` | 115 | 113 | +0.039 | **+0.047** | 5 of 6 |
| E2B | `target_first` | 141 | 213 | +0.089 | **+0.212** | 4 of 6 |
| E4B | `added_first` | 111 | 104 | +0.082 | **+0.048** | 5 of 6 |
| E4B | `target_first` | 167 | 251 | +0.065 | **+0.130** | 3 of 6 |

**In the configuration where the arms are naturally length-balanced — the
companion stated first, where `AB` and `AR̄` differ by two to seven words —
Δ^A is +0.047 on both models.** That is the cleanest estimate the v3 rows
contain: same topics, paired within block, all sixteen draws, no length
differential to match away, five of six bins supported. It sits squarely in the
generic-load region.

In the other configuration the references run 50–70 words longer than the `AB`
cell, longer answers make the exact-count constraint harder, and matching on
length therefore *raises* the estimate rather than lowering it — to +0.212 and
+0.130, on four and three bins. Length is masking part of the contrast there,
not manufacturing it.

Both readings are reported and neither is the estimate: what the split shows is
that **Δ^A, the length differential, and the order are one entangled system on
this design**, and that the one configuration in which they disentangle gives
+0.047.

### v3's references were admitted on solo rates that were 25–90% vacuous

This is the retrospective finding, and it is visible only through v4's lens:
**v3 registered no non-vacuity predicate at all.** §9.3's twenty-word threshold
is a v4 registration, so applying it to v3's Gate 2A cells is a re-description
and not a v3 criterion — but it is the re-description that explains v3's
downstream behaviour.

Gate 2A solo cells, 96 calibration topics, with v4's §9.3 predicate applied:

| model | cell | pass | **vacuous-pass rate** | mean words |
|---|---|---:|---:|---:|
| E2B | A at n\*=5 | 0.708 | **0.000** | 269 |
| E2B | B at m\*=7 | 0.812 | 0.198 | 34 |
| E2B | RF1:5 | 0.865 | **0.490** | 23 |
| E2B | RF2:5 | 0.865 | **0.667** | 22 |
| E2B | RF3:5 | 0.979 | **0.823** | 14 |
| E2B | RF6:4 | 0.865 | 0.427 | 30 |
| E4B | A at n\*=7 | 0.688 | **0.000** | 323 |
| E4B | B at m\*=7 | 0.760 | 0.156 | 36 |
| E4B | RF2:2 | 0.781 | **0.667** | 27 |
| E4B | RF3:5 | 0.990 | **0.896** | 9 |
| E4B | RF6:4 | 0.781 | 0.552 | 20 |

**A's solo cell has zero vacuity and 270–320 word answers. Every reference cell
has 25–90% vacuity and 9–45 word answers.** v3's §18 admission matched
references to B within 0.10 on solo failure — and on both models that matching
was done on quantities in which a majority of the passes were the model
declining to answer.

It explains what `dci1/RESULTS_V3.md` already flagged without explaining: the
admitted references were satisfied in **2–8%** of composed responses on E4B.
A control admitted because it is satisfied by a nine-word answer stops being
satisfied as soon as a second constraint forces the model to write something.

Applying §17.4's forcing to the reciprocal losses the pilot reports makes the
same point from the other side:

| model | `D(R_j←B)` raw | §17.4-forced |
|---|---|---|
| E2B | −0.063, −0.115, +0.271 | **−0.229, −0.443, +0.203** |
| E4B | −0.208, +0.057, +0.318 | **−0.484, −0.302, +0.031** |

Five of six become strongly negative: once vacuous passes are recoded, **B
raises the references' genuine compliance**, because composing with B produces
longer answers than the reference alone does.

None of this invalidates a v3 row or a v3 verdict. v3 was internally consistent
under its own registered rules, and its rules contained no vacuity gate. What it
shows is that v4's §9.3 predicate and §12.4 vacuity ceiling are not bureaucratic
additions: they are the response to a defect that was already present, already
load-bearing, and already invisible.

### The companion-difficulty relation is unidentifiable here by construction

Decision V5 asks whether references should span a range of companion difficulty
so that `D(A←g)` can be read as a function of it. These rows show why the
matched-only default cannot answer it. Companion solo compliance, from the Gate
2A cells at the severities the confirmatory arms used, against the loss measured
on the confirmatory topics:

| model | companion | companion solo | `D(A←g)` |
|---|---|---:|---:|
| E2B | B:7 | 0.812 | +0.1375 |
| E2B | RF1:5 | **0.865** | +0.0815 |
| E2B | RF2:5 | **0.865** | −0.0042 |
| E2B | RF6:4 | **0.865** | +0.1436 |
| E4B | B:7 | 0.760 | +0.1815 |
| E4B | RF2:2 | 0.781 | +0.1056 |
| E4B | RF6:4 | 0.781 | +0.1136 |
| E4B | RF4:4 | 0.802 | +0.1042 |

**On E2B the three references have identical solo compliance to four decimal
places.** The x-axis has zero variance, the slope is undefined, and no
difficulty relation can be fitted at all. On E4B the three span 0.021 and the
loss spans 0.011, giving a slope of −0.26 that is extrapolated to B at 0.760 —
an extrapolation of one x-range beyond the data, from three points, on a range
narrower than the standard error of any one of them.

This is v4r2 §13.4's observation stated as an identification problem rather than
as a curiosity: the caliper that makes the references valid controls is
precisely what destroys the variation needed to read difficulty off them.
**A difficulty-spanning arm is not an optional extra; it is the only way the
question V5 asks can be answered**, and no existing DCI-1 artifact contains one.

### Accidental compliance

v3's `TOPIC` arm carries the same 384 topics with no constraint at all. Applying
the other verifiers to those responses:

| model | mean words | B:7 | R₁ | R₂ | R₃ |
|---|---:|---:|---:|---:|---:|
| E2B | 331.6 | 0.000 | RF1:5 0.084 | RF2:5 0.048 | RF6:4 0.000 |
| E4B | 333.6 | 0.000 | RF2:2 0.005 | RF6:4 0.000 | RF4:4 0.000 |

At v3's operating length, compliance is delivery and not accident. That is not a
length-free statement: the same constraints applied to a 23-word answer would
show much higher accidental rates, which is one more reason the pilot's
short-answer cells are not comparable with v3's long-answer ones.

## 3. The cross-set quantity, and the correction it carries

A previous review of this repository quoted, as `D(B←A)` against `D(R̄←A)`:

| model | B | R̄ | difference |
|---|---:|---:|---:|
| E2B | 0.468 | 0.582 | **−0.114** |
| E4B | 0.316 | 0.727 | **−0.411** |

Those numbers are reproduced exactly here and they are **not delivery losses**.
Each subtracts a composed rate measured on the 384 confirmatory topics from a
solo rate measured on the 96 calibration topics. The sets are disjoint and the
contrast is unpaired, so each carries the topic-set shift as well as the
companion effect.

The size of that shift is measurable for one constraint, because A's solo cell
exists on both sets at the same severity under the same estimator:

| model | A solo, 96 calibration topics | A solo, 384 confirmatory topics | shift |
|---|---:|---:|---:|
| E2B | 0.7083 | 0.6619 | **−0.046** |
| E4B | 0.6875 | 0.5827 | **−0.105** |

The assumption the cross-set quantity needs is that this shift is the same for B
and for each reference. It is measured for A only and assumed, never shown, for
the others. A shift of that magnitude does not overturn a difference of −0.114 or
−0.411, so the qualitative reading survives it — **A damages these references at
least as much as it damages B** — but the reading has a second and larger
confound that no shift correction touches: on E4B the references are satisfied in
4–8% of composed responses, so their loss is near its ceiling by construction.
Whether that is "A damages references more" or "these references are
structurally incompatible with A" is not separable from these rows.

**Status: diagnostic. It is not `D(B←A)`, it is not `D(R̄←A)`, and it may not be
quoted as either.**

## 4. Provenance

`Δ^A` on all cached draws reproduces pre-freeze check
`dci1/docs/v4_prefreeze/C18.json` to **1.4 × 10⁻¹⁷** on both models
(+0.06391059027777778 against +0.06391059027777779; +0.07367621527777778 against
+0.07367621527777779). That is a provenance check rather than a scientific one:
it establishes that this re-analysis reads the rows C18 read, which a reader
cannot otherwise verify.

Re-running the tool reproduces `result.json` **byte for byte** — every seed is
fixed and no wall-clock or filesystem-order input reaches a number.

C18 records point estimates only. What this adds is block-level uncertainty,
order stratification, simultaneous per-reference intervals, the uptake and joint
tables, the length record, and the identification statement of §1.

Source caches, by digest:

| model | confirmatory cache sha256 | Gate 2A cache sha256 |
|---|---|---|
| E2B | `f74402e83188da86…` | `a99e802ceac97bcb…` |
| E4B | `5438abeb2b88e796…` | `868e7ec7be29dcab…` |

## 5. What this does not say

It does not say that companion identity fails to matter. It says that the only
same-topic companion-swap contrast the repository has ever executed is on the
**A** side, is positive on both Gemmas, sits below the registered generic-load
threshold on both, disagrees across references on one of them, and moves by a
factor of four with order on that same one. The B-side contrast — `Δ_R`, the
registered primary — has never been estimated in this constraint vocabulary by
any registered stage, and cannot be estimated from these rows.
