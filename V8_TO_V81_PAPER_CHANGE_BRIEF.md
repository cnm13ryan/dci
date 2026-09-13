# From the v7 manuscript to the v8.1 paper — evidence-grounded change brief

*Prepared 2026-09-10 from the frozen v8.1 confirmatory artifacts. Companion
document: `UPSTREAM_V81_PAPER_AGENT_PROMPT.md`, which is the prompt to hand
to the paper-writing agent.*

> **Manuscript identity.** The brief names `neurips-5.pdf`, which is not
> present on this machine. The v7 manuscript that *is* present is
> **`neurips-4.pdf`** (also at `/home/cnm13ryan/git/dci/neurips-4.pdf`), and
> its structure matches the requested audit exactly: §1 Introduction, §2
> Related Work, §3 Background, §4 Method, §5 Results with 5.1/5.2/5.3, §6
> Discussion, §7 Limitations, §8 Conclusion, Figures 1–4, Table 1,
> Appendix A (extended related work), B (protocol and implementation), C.1–C.4
> (sensitivities and diagnostics), D (broader impacts), NeurIPS checklist.
> **This audit is against `neurips-4.pdf`.** If a later `neurips-5.pdf`
> exists elsewhere, every section-level verdict below still applies by section
> identity, but its numbers must be re-checked against §3 before use.

---

# 1. Executive scientific story

**One sentence.** Against three same-form companions matched to it on
wording-conditioned stand-alone compliance, the focal instruction A costs
compliance with B no more than they do in 23 of 24 preregistered
model × wording-frame × prompt-order conditions — while composition itself
moves B's compliance by up to 49 percentage points.

**Abstract-level, three sentences.**

> Composing two verifiable instructions moves compliance enormously — B's
> compliance falls by as much as 49 pp beside A and rises by as much as 13 pp
> beside it, depending on model and position — but replacing the companion
> instead of removing it leaves almost all of that movement behind: in 23 of
> 24 preregistered conditions the simultaneous interval for the
> matched-reference contrast stops below 10 pp, at realised half-widths of
> 1.1–3.2 pp, so the smallness is measured rather than underpowered. The
> twenty-fourth condition — one model under one of four sentence frames with
> B stated second — puts Δ_R at +12.6 pp, a result the registered rule
> declines to certify and that three registered sensitivities undercut: one of
> its three references carries it, the registered graded recoding cuts it 44%
> to +7.1 pp, and the difficulty-spectrum arm on the same rows puts A 11.5 pp
> *below* what companions of its measured stand-alone compliance predict.
> Conditioning on wording is what made that condition visible at all —
> averaging the model's three frames returns +0.06 pp — so a pair-specific
> claim needs not only an explicitly stated reference class but the phrasing
> under which that class was matched.

**Main positive finding.** Exactly one: Gemma-3n-E4B-it, frame 1, B second,
Δ_R = +12.64 pp with a joint interval excluding zero. It reaches **no
registered level** and carries four independent registered qualifications.

**Main negative / bounded finding.** 23 of 24 conditions read `L3c` — the
joint upper bound stops below +10 pp — and 11 of those intervals lie wholly
*below zero*: the matched references cost B **more** than A does.

**Main qualification.** Reference-set choice changes a registered verdict on
2 of 24 conditions, and the frozen triple sits at an extreme of its own
admissible set on 7 of 24. The reported interval does not cover this: the
bootstrap resamples topics, not reference sets.

**The methodological lesson, upgraded.** v7's lesson — a solo-to-pair change
does not identify a harmful companion — survives confirmatory testing. Its
successor is that naming a reference class is not one decision but three:
*which admissible members you froze* (2 verdicts move), *under which wording
you matched them* (a 20.8 pp between-frame range that crosses a verdict
boundary), and *which comparison class you chose at all* (the LOCAL and
SPECTRUM arms disagree by 24 pp on the same rows).

---

# 2. Authoritative result summary

All numbers below are copied from the signed `CONFIRMATORY_ANALYSIS` records
of root `dci1/evidence/dci1v8p1-confirm`, bound to commit `034fc72`, via
`dci1/reports/dci1v8dev/postconfirm/data/`. §10 indexes every artifact.

## 2.1 Provenance

| item | value |
|---|---|
| confirmatory root | `dci1/evidence/dci1v8p1-confirm` |
| bound commit (every stage record) | `034fc7214762b6848d5d904b14fd82b317830667` |
| preregistration | `dci1/docs/DCI1_preregistration_v8.1.md`, hash `d3552f9f47e3f008…` |
| registration manifest | `8cfa20827b3f46fc…` (commit `c0b52ca`) |
| membership lock | `31af521c21d5cee4…` |
| rules hash | `3d9064ea0f99cc9b…` |
| verifier / wording hash | `ea885b0db67e3c7c…` / `fe3b5be15759af1c…` |
| topic split hash | `c10f17bc5846e185…` (v4r2 split seed, carried unchanged) |
| rows planned = generated | **2,353,152** (715,776 + 344,064 + 623,616 + 669,696) |
| bootstrap resamples | 10,000 |
| blocks per entering frame | 384 |
| analysis / final-report outcome | `PASS` on all four models; **7 of 7 traceability checks PASS**, `traceability_failed` empty |

Per-model record hashes: Qwen3-4B `5591cb46c64c127a` / `af7138f534420738`;
Qwen3-4B-Instruct-2507 `31f1b46be5e6416e` / `3dfab3cd8904acfa`;
Gemma-3n-E2B-it `5edcd5730bc4c031` / `2fad8b4cab4cbaaa`;
Gemma-3n-E4B-it `e90e0f7d6606bd8d` / `c6666bdbabcdd2ee` (analysis / final report).

## 2.2 Design

12 entering LOCAL frames and 14 entering SPECTRUM frames over four models;
24 LOCAL cells and 28 SPECTRUM cells once both prompt orders count.

| model | LOCAL frames | SPECTRUM frames | joint family |
|---|---|---|---:|
| Qwen3-4B | 0, 1, 2, 3 | 0, 1, 2, 3 | 24 |
| Qwen3-4B-Instruct-2507 | 1, 3 | 1, 3 | 12 |
| Gemma-3n-E2B-it | 0, 1, 3 | 0, 1, 2, 3 | 22 |
| Gemma-3n-E4B-it | 0, 1, 3 | 0, 1, 2, 3 | 22 |

**The decision interval is the JOINT cross-frame simultaneous interval** —
every F1 member of every entering frame of a model, one bootstrap draw shared
across frames, realised critical values 2.798–3.017. Never substitute the
marginal or the per-frame interval.

**Registered reading grammar for Δ_R** (`claims.delta_r_reading`): half-width
> 5 pp → `INSUFFICIENT_PRECISION`; lower > +10 pp → `L3a` (`L3b` if
> +25 pp); upper < +10 pp → `L3c`; else `INDETERMINATE@0.10`. Direction is read
separately: lower > 0 `A_HARMS_MORE`, upper < 0 `A_COMPARATIVELY_BETTER`.

## 2.3 Primary LOCAL result — the 24 cells

Source: `postconfirm/data/primary_delta_by_frame_order.{csv,json}`.

| model | f | order | n\* | m\* | ι_A | frozen triple | Δ_R pp | joint 95% CI | ≤5 pp | reading |
|---|---:|---|---:|---:|---:|---|---:|---|:-:|---|
| Qwen3-4B | 0 | B first | 6 | 12 | 0.674 | XC3:10 / MK1:4 / MK6:6 | −2.65 | [−4.73, −0.56] | ✓ | L3c |
| Qwen3-4B | 0 | B second | 6 | 12 | 0.674 | XC3:10 / MK1:4 / MK6:6 | −5.54 | [−8.31, −2.78] | ✓ | L3c |
| Qwen3-4B | 1 | B first | 7 | 12 | 0.608 | MK7:2 / XC3:9 / MK2:7 | −1.20 | [−3.41, +1.00] | ✓ | L3c |
| Qwen3-4B | 1 | B second | 7 | 12 | 0.608 | MK7:2 / XC3:9 / MK2:7 | −2.93 | [−5.67, −0.19] | ✓ | L3c |
| Qwen3-4B | 2 | B first | 3 | 12 | 0.673 | MK7:2 / MK1:6 / MK6:5 | −0.76 | [−2.71, +1.19] | ✓ | L3c |
| Qwen3-4B | 2 | B second | 3 | 12 | 0.673 | MK7:2 / MK1:6 / MK6:5 | −3.49 | [−6.70, −0.29] | ✓ | L3c |
| Qwen3-4B | 3 | B first | 5 | 13 | 0.702 | XC3:8 / MK2:5 / MK7:2 | +0.10 | [−0.95, +1.15] | ✓ | L3c |
| Qwen3-4B | 3 | B second | 5 | 13 | 0.702 | XC3:8 / MK2:5 / MK7:2 | −1.02 | [−2.99, +0.95] | ✓ | L3c |
| Qwen3-4B-Instruct-2507 | 1 | B first | 6 | 10 | 0.652 | MK2:8 / MK5:6 / MK3:2 | +1.50 | [−0.13, +3.12] | ✓ | L3c |
| Qwen3-4B-Instruct-2507 | 1 | B second | 6 | 10 | 0.652 | MK2:8 / MK5:6 / MK3:2 | −1.00 | [−3.74, +1.75] | ✓ | L3c |
| Qwen3-4B-Instruct-2507 | 3 | B first | 6 | 12 | 0.673 | MK6:10 / MK8:3 / MK7:6 | −0.88 | [−2.68, +0.92] | ✓ | L3c |
| Qwen3-4B-Instruct-2507 | 3 | B second | 6 | 12 | 0.673 | MK6:10 / MK8:3 / MK7:6 | −2.43 | [−4.43, −0.43] | ✓ | L3c |
| Gemma-3n-E2B-it | 0 | B first | 8 | 8 | 0.642 | MK4:1 / MK2:6 / XC3:8 | −0.43 | [−2.97, +2.10] | ✓ | L3c |
| Gemma-3n-E2B-it | 0 | B second | 8 | 8 | 0.642 | MK4:1 / MK2:6 / XC3:8 | **−11.19** | [−14.43, −7.95] | ✓ | L3c |
| Gemma-3n-E2B-it | 1 | B first | 3 | 10 | 0.635 | MK2:5 / XC3:9 / MK5:8 | +1.41 | [−1.11, +3.93] | ✓ | L3c |
| Gemma-3n-E2B-it | 1 | B second | 3 | 10 | 0.635 | MK2:5 / XC3:9 / MK5:8 | −2.99 | [−5.93, −0.06] | ✓ | L3c |
| Gemma-3n-E2B-it | 3 | B first | 7 | 11 | 0.686 | MK6:8 / MK8:3 / MK2:3 | −6.93 | [−9.20, −4.67] | ✓ | L3c |
| Gemma-3n-E2B-it | 3 | B second | 7 | 11 | 0.686 | MK6:8 / MK8:3 / MK2:3 | −10.03 | [−13.08, −6.97] | ✓ | L3c |
| Gemma-3n-E4B-it | 0 | B first | 6 | 9 | 0.745 | MK2:6 / MK1:5 / MK4:8 | −2.21 | [−4.84, +0.41] | ✓ | L3c |
| Gemma-3n-E4B-it | 0 | B second | 6 | 9 | 0.745 | MK2:6 / MK1:5 / MK4:8 | −8.18 | [−10.78, −5.58] | ✓ | L3c |
| Gemma-3n-E4B-it | 1 | B first | 6 | 9 | 0.711 | MK3:3 / XC3:9 / MK5:6 | +2.15 | [−0.37, +4.66] | ✓ | L3c |
| **Gemma-3n-E4B-it** | **1** | **B second** | **6** | **9** | **0.711** | **MK3:3 / XC3:9 / MK5:6** | **+12.64** | **[+9.62, +15.66]** | ✓ | **INDETERMINATE@0.10** |
| Gemma-3n-E4B-it | 3 | B first | 8 | 10 | 0.688 | MK2:6 / MK1:5 / MK3:1 | +0.76 | [−1.61, +3.13] | ✓ | L3c |
| Gemma-3n-E4B-it | 3 | B second | 8 | 10 | 0.688 | MK2:6 / MK1:5 / MK3:1 | −4.29 | [−7.21, −1.36] | ✓ | L3c |

Summary: Δ_R ∈ [−11.19, +12.64] pp. 18 of 24 point estimates negative; **11 of
24 joint intervals lie wholly below zero**; 1 wholly above. Precision
precondition met **24 of 24** (half-widths 1.05–3.24 pp). Largest joint upper
bound +15.66 pp; 3 cells exceed +3.9 pp. **`beyond_sesoi` is false in all 24**
— no cell resolves an excess beyond the 10 pp smallest effect of interest.

**Registered qualification statuses on the readings.**
`A_GENERAL_NOT_EXCLUDED` (the Ξ gate: the excess is not distinguishable from A
being generally disruptive) on **18 of 24**.
`COMPOSED_CONTRAST_RANGE_COMPRESSED` (the §13.14 boundary reading, the v8.1
analogue of v7's daggered cells) on **8 of 24**, every one on a Qwen model:
Qwen3-4B f0/f1/f2 B-first and f3 both orders; 2507 f1 B-first and f3 both
orders. `REFERENCE_HETEROGENEOUS` on 3; `VACUITY_DEPENDENT` on 7.

## 2.4 Model-level conjunction verdicts

Source: `postconfirm/data/model_level_verdicts.csv`. The verdict is the
conjunction over the model's entering LOCAL frames of the Δ_R reading **on the
joint interval**; frames are conditions, never averaged.

| model | B first | B second |
|---|---|---|
| Qwen3-4B | `LOCAL_EQUIVALENT_SAME_FORM_ONLY` | `LOCAL_EQUIVALENT_SAME_FORM_ONLY` |
| Qwen3-4B-Instruct-2507 | `LOCAL_EQUIVALENT_SAME_FORM_ONLY` | `LOCAL_EQUIVALENT_SAME_FORM_ONLY` |
| Gemma-3n-E2B-it | `LOCAL_EQUIVALENT_SAME_FORM_ONLY` | `LOCAL_EQUIVALENT_SAME_FORM_ONLY` |
| Gemma-3n-E4B-it | `LOCAL_EQUIVALENT_SAME_FORM_ONLY` | **`FRAME_HETEROGENEOUS`** |

Every verdict carries **`NEAR_FORM_UNAVAILABLE`**. The design runs no
near-form arm, so §34 D18's *strong* L3c refutation verdict is unreachable
**by construction**, and the narrow `LOCAL_EQUIVALENT_SAME_FORM_ONLY` is the
most that a same-form pool licenses.

**§26 methodological success**: `MET` on both Gemma models; **`NOT_MET` on both
Qwen models**, on `D(A←B)`'s precision precondition alone (10 intervals for
Qwen3-4B, 5 for 2507). Every Δ_R interval in the study meets its precondition.
The paper must report the `NOT_MET` verdict and that it does not touch the
primary estimand.

**Scope sentence, verbatim from the FINAL_REPORT record**
(`strongest_permissible_statement`):

> "each Delta_R(f) is a statement about this model under this wording frame at
> the frozen n*(f), m*(f) and reference triple; the model-level verdict is the
> conjunction over its entering frames; nothing here generalises across
> wordings or models"

## 2.5 Raw composition versus the matched-reference contrast

Source: `postconfirm/data/raw_vs_reference_loss.csv`.

| quantity | range over the 24 LOCAL cells |
|---|---|
| D(B←A), the raw solo-to-pair change on B | **−13.5 to +49.2 pp** |
| D(B←R̄), the same change beside the matched references | **−11.9 to +57.4 pp** |
| D(A←B), the reciprocal change on A | **−36.1 to +54.5 pp** |
| Λ = D(A←B) − D(B←A) | **−49.8 to +52.3 pp** |
| Δ_R | **−11.2 to +12.6 pp** |

11 of 24 cells move B by more than 10 pp raw; 3 of 24 move Δ_R by more than
10 pp. |D(B←A)| / |Δ_R| has median **3.8** and maximum **88.6**.

**The strongest confirmatory replacement for v7's Figure 4 example.**
Gemma-3n-E4B-it, frame 0, B second: B's compliance falls from **0.713 alone to
0.221 beside A** (49.2 pp) and to **0.140 beside the three matched references**
(57.4 pp); Δ_R = **−8.18 pp**. Essentially none of a 49-point composition
effect is attributable to A's identity, and this is larger than v7's
E4B/B-second example (39.2 vs 46.4).

Second-strongest, and the opposite regime: Qwen3-4B, frame 0, B first, where
B *improves* by 13.5 pp beside A and by 10.9 pp beside the references, Δ_R =
−2.65 pp. On both Qwen models D(B←A) is negative in 10 of 12 cells — a direct
confirmatory counterexample to any shared-resource reading of composition.

## 2.6 Frame and order heterogeneity

Source: `postconfirm/data/primary_delta_by_frame_order.csv`,
`order_contrasts.csv`.

Between-frame range in Δ_R, per model × order: Qwen3-4B 2.75 / 4.52;
2507 2.38 / 1.43; Gemma-3n-E2B-it 8.34 / 8.19; **Gemma-3n-E4B-it 4.36 /
20.82**.

Order differences in Δ_R run **−10.75 pp** (Gemma-3n-E2B-it f0) to **+10.49
pp** (Gemma-3n-E4B-it f1). In 11 of 12 frames Δ_R falls when B is stated
second; f1 of E4B is the exception, and it is the frame that produces the only
positive result.

**The decisive arithmetic for the frame argument**: averaging
Gemma-3n-E4B-it's three entering frames with B second gives
(−8.18 + 12.64 − 4.29)/3 = **+0.06 pp** — a clean-looking null that would have
concealed the only positive condition in the study.

**Registered order contrasts (F11)**: `Ord_B` excludes zero on **all 14
frames** and reaches **−46.84 pp** (E4B f0); `Ord_A` excludes zero on 11 of 14;
`Ord_Λ` reaches −35.25 pp. Position moves compliance by up to four times what
companion identity moves it. Qwen3-4B's `Ord_A` misses its precision
precondition on f0 and f1 — mark those two.

## 2.7 Per-reference heterogeneity

Source: `postconfirm/data/per_reference_contrasts.csv`. Δ_j = D(B←A) − D(B←R_j),
so positive means A harms B more than R_j.

- The three per-reference contrasts **disagree in sign in 15 of 24 cells**.
- The within-cell spread exceeds |Δ_R| in **21 of 24** and the joint
  half-width in **21 of 24**.
- Range of spreads: **0.52 pp** (Qwen3-4B f3 B-first) to **50.98 pp**
  (Gemma-3n-E2B-it f0 B-second: −15.92, −34.31, +16.67 → mean −11.19).
- v7 reported spreads of 2.9–10.3 pp. Under frame conditioning they are
  **0.5–51.0 pp**. The heterogeneity got larger, not smaller.

**Descriptive finding worth a Discussion paragraph, flagged as post-hoc.**
Grouping the 72 registered Δ_j by the reference's instruction family: XC3
(same exact-count form, counts *sentences*) has mean Δ_j **+5.17 pp** (n = 12,
max +35.45); the eight marker-word families pooled have mean **−3.51 pp**
(n = 60). A is itself a marker-word instruction (`marker_however`, discourse
role `contrastive`). So against companions that count another marker word A is
unexceptional; against a same-form companion counting a different object it
looks worse. **This is §34 D18's registered ambiguity — "A is not special"
versus "the excess is a property of the exact-count form" — measured.** It is
a post-hoc grouping of registered quantities: no registered family estimates a
family-level contrast, and it carries no interval.

## 2.8 Reference-set sensitivity (F_REFSENS)

Source: `postconfirm/data/reference_sensitivity.csv`. Descriptive family:
Δ_R re-formed over every admissible triple of the frame's five frozen
families, on the same cells, each with its own simultaneous interval. **The
primary claim is decided by the frozen triple R1+R2+R3 and by nothing else.**

| class | cells |
|---|---:|
| reference-robust (one verdict, spread < 5 pp) | 12 |
| sensitive but same registered verdict | 10 |
| **registered verdict changes across admissible triples** | **2** |

Across-triple spread reaches **26.46 pp**; sign flips on **14 of 24**; the
spread exceeds 10 pp on **6 of 24**; the frozen triple is at an extreme of its
own admissible set (rank 1 or rank n) on **7 of 24**.

**The two verdict changes, both Gemma-3n-E4B-it with B second.**

- **f0**: frozen Δ_R = −8.18 is the **most negative of nine** triples; the
  others run to **+16.92 pp**, and five of nine have simultaneous intervals
  wholly above +10 pp — an `L3a` reading. Per-reference contrasts −12.53,
  −12.11, +0.10.
- **f1** (the study's only positive cell): frozen +12.64 is the **most harmful
  of nine**; range **−8.63 to +12.64 pp**, spread 21.27, sign flips. Two
  triples read `L3a`, one `INDETERMINATE@0.10` (the frozen one), six `L3c`.
  Per-reference contrasts +5.63 (MK3:3), **+35.45 (XC3:9)**, −3.16 (MK5:6),
  all with intervals excluding zero.

**Implication for Discussion and Limitations.** A reference-set-conditional
interval is the honest object. The bootstrap resamples *topics*, not reference
sets, so the reported interval says nothing about this variation — and here,
as in v7, this is the larger source. This must be a Results-section item, not
an appendix footnote.

## 2.9 Operating-point robustness (F_RUNNER_UP)

Source: `postconfirm/data/runner_up_sensitivity.csv`.

**Every entering frame of every model carries `OPERATING_POINT_UNSTABLE`** —
the frozen n\*(f) was re-selected on fewer than two-thirds of 2,000 topic
resamples. The registered response is not replacement but the runner-up arm,
carrying the contrast at the alternative severity on the *same* blocks.
Runner-up arms exist on **7 of the 12 LOCAL frames** (Qwen3-4B's four at slot
A2; Gemma-3n-E2B-it f0 and Gemma-3n-E4B-it f0 at both A2 and B2;
Gemma-3n-E4B-it f1 at A2) — **18 comparisons** once both orders count.

Comparing like with like (the frozen Δ_R on its *within-frame* simultaneous
interval against the runner-up on its own):

| class | comparisons |
|---|---:|
| operating-point robust (same reading, \|change\| < 2 pp) | 12 |
| quantitatively sensitive, same reading | 6 |
| **registered reading changes** | **0** |

**Operating-point choice changes no registered reading anywhere.** Largest
movement **12.77 pp** (Gemma-3n-E2B-it f0 B-second under the B2 runner-up,
−11.19 → +1.58) with the reading `L3c` on both sides; sign flips on 2 of 18.

**Separate numerical from inferential instability explicitly.** The selection
rule is genuinely unstable — that is why every frame carries the status — but
the *inference* is not: no reading moves. On the one positive cell the
runner-up moves Δ_R by only **0.88 pp** (+12.64 → +13.52), and on the
within-frame interval both read `L3a`; it is the **joint** cross-frame
interval, widened by sharing one bootstrap draw across three frames, that
spans +10 pp and yields `INDETERMINATE@0.10`. Say this plainly: the excess is
stable to the operating point and to the estimator, and it is the registered
multiplicity correction, not noise, that stops short of certifying it.

## 2.10 SPECTRUM

Sources: `postconfirm/data/spectrum_results.csv`, `spectrum_points.csv`.

### The sign and semantics of ι — read this before writing anything

**ι is a chance-corrected stand-alone *compliance*, not a difficulty score.**
`dci1v7/stages/calibration_table.py::instructed_compliance` computes
`(solo − chance)/(1 − chance)`, "the share of the achievable improvement over
chance that stating the constraint delivers". Therefore:

- **higher ι → the companion is followed more often → an EASIER companion**
- **lower ι → a HARDER companion**

The protocol calls ι "the registered difficulty coordinate" because it
*indexes* difficulty, but it runs the other way. Its own spectrum slots agree:
`SPECTRUM_LOW`/`side: below` sits at low ι, `SPECTRUM_HIGH`/`side: above` at
high ι — "below" and "above" are positions on the *compliance* scale.

### Does companion difficulty predict B's loss?

Over the 28 SPECTRUM cells the point estimate of β is positive in 22; the
registered simultaneous interval **excludes zero above it in 19**, **below it
in 4**, and **spans zero in 5**.

**On a compliance axis, β > 0 means B's loss is LARGER beside an EASIER
companion.** So the majority direction runs *against* the premise the arm was
designed on. The four clearly negative cells — Qwen3-4B f0 B-first,
Gemma-3n-E2B-it f2 B-second, and **both orders of Gemma-3n-E4B-it f1** — are
the ones where the intuitive direction holds. The pattern is visible within
families as well as across them: on Gemma-3n-E2B-it f3 B-second, MK2 runs
+35.0 → +36.9 → +40.1 pp as ι rises 0.57 → 0.69 → 0.91, and MK5 and MK6 do the
same. Largest slope +0.297 (E4B f3 B-second). β also changes sign across
frames of one model: E4B B-first gives +0.010 (f0), **−0.042** (f1), +0.095
(f3).

**The paper must not restate the design's premise as a finding.** Report the
direction as measured and claim no mechanism — the design reads no model
internals, and ι and the loss are measured on the same blocks.

### Where does A lie relative to prediction?

δ_difficulty = observed D(B←A) − [α̂_family + β̂·ι_A], with family-aware
intercepts, OLS, equal weights (§11.7).

- **Negative in 25 of 28 cells**: A costs B *less* than the fitted relation
  predicts for a companion of A's measured stand-alone compliance.
- **17 cells read `L3e`** — the residual lies wholly inside the ±10 pp
  equivalence region.
- **1 cell reads `L3d`** — Qwen3-4B-Instruct-2507 f1 B-first, δ = **+1.60 pp**,
  joint CI [+0.05, +3.15]. This is the only registered direction claim in the
  arm, and it is +1.6 pp.
- **10 cells reach no registered level**, all strongly negative, down to
  **−28.69 pp** (Gemma-3n-E2B-it f2 B-second). The registered grammar is
  one-sided — `L3d` needs the interval above zero, `L3e` needs it inside
  ±10 pp — so a large *negative* residual has no level to reach. **Do not
  report these as nulls**; report the point estimate and interval and say the
  grammar has no level for them.
- The support check `holds` on **28 of 28**: A's ι is inside the fitted range
  everywhere, so no cell extrapolates.

### Does SPECTRUM corroborate or contradict the LOCAL-positive condition?

**It contradicts it, on the same rows.** On Gemma-3n-E4B-it f1 B-second the
LOCAL arm gives Δ_R = +12.64 pp while SPECTRUM gives δ_difficulty = **−11.49
pp**, joint CI [−14.40, −8.58]. The raw points explain why. A's loss is
+43.29 pp against a spectrum running +35.81 to +75.68 (B's compliance falls
from 0.768 alone to 0.335 beside A, against 0.410 beside the gentlest
companion and **0.011** beside the harshest, CL7:95). The LOCAL triple is
MK3:3 (+37.66), **XC3:9 (+7.85)** and MK5:6 (+46.45): its mean is dragged down
by one sentence-count companion whose effect on B is less than a quarter of
the gentlest companion on the spectrum. **A looks harmful in this cell not
because it is harsh but because one of its three matched references is
unusually gentle.**

### Difficulty versus companion identity

Neither arm licenses "difficulty explains interference". SPECTRUM says A's
loss is close to what its *compliance* predicts in 17 of 28 conditions and
below it in 25; but the fit carries **family-aware intercepts**, i.e. it
concedes by construction that family matters at fixed ι, and the F2 grouping
of §2.7 shows how much. The defensible statement is: after conditioning on
stand-alone compliance A is unexceptional, and what remains unexplained tracks
the companion's *family*, not A's identity.

## 2.11 Other registered robustness

Sources: `postconfirm/data/registered_gates.csv`, `recoding_robustness.csv`,
`projection_audit.csv`, `identification_ledger.csv`,
`cross_configuration_consistency.csv`.

| analysis | largest movement | most affected cell | headline survives? | qualification |
|---|---|---|:-:|---|
| Reference-set sensitivity (F_REFSENS) | 26.46 pp spread | Gemma-3n-E2B-it f0 B-second | **on 22 of 24** | verdict changes on E4B f0 and f1, B second |
| Operating point (F_RUNNER_UP) | 12.77 pp | Gemma-3n-E2B-it f0 B-second | **yes, everywhere** | none |
| Graded-compliance recoding (F5 `graded_0.99`) | −15.76 pp | Gemma-3n-E4B-it f1 B-second | **yes** | **the one positive Δ_R falls +12.64 → +7.07 pp**, inside the bound |
| Vacuous-pass recoding (F5 `vacuity_forced`) | −11.45 pp | 2507 f3 B-first (−0.88 → −12.33) | **yes** | §17.4 withholds levels on E4B f1 B-second |
| F6 vacuity gate | bounds [−15.15, −9.51] pp | 2507 f3 B-first | **yes** | gate binds on 6 of 24; 7 carry `VACUITY_DEPENDENT` |
| §23 projection audit | 0.867 absolute error | Qwen3-4B f0, cell B+S2 (projected 0.932, realised 0.065) | **yes** (licenses nothing) | **370 of 370** audited composed cells outside the 0.05 allowance, median \|error\| **0.264** |
| Order contrasts (F11) | −46.84 pp | Gemma-3n-E4B-it f0, `Ord_B` | **yes** | position dominates companion identity |
| L4a cross-configuration consistency | — | Gemma-3n-E4B-it f1 | **yes** | Δ_R agrees on 11 of 12 frames; δ_difficulty on 5 of 12; 16 of 24 member-frame pairs agree |
| §34 D6 identification ledger | — | — | **yes** | 1,512 `ESTIMATED`, 134 `NOT_ASKED`, **0 `NOT_IDENTIFIED`** |

Of these, exactly **two touch the one positive cell** and both weaken it: the
graded recoding cuts it 44%, and §17.4's both-bounds rule
(`forced_agrees = false`) withholds its levels independently of the interval.
Together with `REFERENCE_HETEROGENEOUS` and `A_GENERAL_NOT_EXCLUDED` that is
four registered qualifications on one cell.

## 2.12 Methodology validation (pre-freeze; not confirmatory)

Source: `dci1/reports/dci1v8dev/frame_aware_prescreen/prescreen_revalidation.md`
§§2–5 and `revalidation.json`; digest in
`postconfirm/data/methodology_validation_final.csv`.

**Keep three robustness concepts apart and never substitute one for another:**

| | what is perturbed | what it measures |
|---|---|---|
| **A. Re-execution** | same topics, same seeds, run again | decoding / backend nondeterminism |
| **B. Topic resampling** | fresh area-stratified partition of the 216 pre-freeze topics into the same roles | topic-sampling sensitivity |
| **C. Topic bootstrap** | resampling stored calibration rows | conditional resampling stability |

The confirmatory bootstrap is C. The operating-point stability statistic is C.

- **Frame-conditioned forwarding changes what is identifiable.** At equal
  budget on identical rows, the frame's own candidate set yields at least as
  many admissible families as the frame-pooled set on **13 of 14** supported
  frames, and on **2** the §13.15 verdict differs (2507 f3: 5 families / 2
  backups vs 4 / 1; Gemma-3n-E4B-it f0: 7 / 2 vs 4 / 1). One model — 2507 — is
  eligible because of it.
- **r26 and the honest form of the 2507 claim.** `dci1v8-pilot-r26`
  re-executed the **v8 pooled design itself** at the frozen v8 commit
  `f7af7f2` on the same model, topics and seeds, and gave 5/2 on 2507 f3.
  Across every observation, the pooled set clears §13.15 in **2 of 5** and the
  frame-aware set in **3 of 3**. The claim is therefore "the pooled rule is
  *marginal* there, not reliably failing"; the paired comparisons (r15, r20 —
  identical rows, frame-aware supported and pooled not) remain the strongest
  evidence, and E4B f0 (7/2 vs 4/1 in both successor runs) is untouched.
  **Nothing in v8.1 changed because of r26.**
- **A vs B, side by side:**

| measure | A (decoding) | B (topics) |
|---|---|---|
| LOCAL verdicts agreeing | 16 of 16 | **13 of 14** |
| SPECTRUM identification agreeing | — | 13 of 14 |
| operating points agreeing | — | 11 of 14 |
| model eligibility agreeing | 4 of 4 | **3 of 4** |
| forwarded-set Jaccard | 0.59–1.00 | 0.51–0.77 |
| core reference triple identical | 5 of 16 | 3 of 14 |
| core reference families identical | 8 of 16 | 7 of 14 |
| admissible backups identical | 8 of 16 | 3 of 14 |

  Topic sampling is the larger source on every measure, but not by a wide
  margin, and on both perturbations the pipeline's **verdicts** are far more
  stable than the **objects** it selects.
- **The one eligibility disagreement.** 2507 frame 1 carries 6 LOCAL-valid
  families and 2 backups in the bound pilot and **4 and 1** under the
  resampled partition, below §13.15's minimum — so its LOCAL set would be {3}
  alone and the model would **not** be eligible under
  `LOCAL_ELIGIBILITY_MIN_FRAMES = 2`. Sound on both sides (SUPPORTED at Gate 2
  in both, same chance basis κ = 0, ι_A 0.652 vs 0.641, complete row
  accounting). A genuine sensitivity, not a defect.
- **Knife-edge operating points.** Gemma-3n-E2B-it f0 selected n\* = 1, 8 and 3
  across three samples of the same 216-topic pool; 2507 f0 moved between
  unsupported and supported under decoding noise alone.
- **Engineering integrity.** The row-reuse defect (`_reusable_rows` matched
  design identity but not whether rows were generated) is fixed by
  `reusable_rows_checked` on both the pilot and confirmatory paths, with seven
  regression tests; a scan of 108 backend runs across 9 roots found no other
  affected evidence; its first production use correctly admitted a complete
  265,728-row run after a memory kill. The mixed-commit audit:
  `git diff 025e138 7d8e1d9` touches one source file and one constant (the
  backend wall-clock cap), 71 of 72 hashed package files identical, all
  rule/protocol/document bindings identical — no model was re-run for commit
  uniformity.
- **Freeze readiness**: 11 of 11 items passed for every model. Target basis
  **C** (`RETENTION_TARGET_BASIS = calibration_iota_a`) registered on the
  precision argument, with basis A generated as a comparator that decides
  nothing; the two bases forward different sets (Jaccard 0.63–0.97) and reach
  the same family count, backup count and §13.15 verdict on **all 14** frames.

---

# 3. What fundamentally changed from v7 to v8.1

| # | change | consequence for the paper |
|---|---|---|
| 1 | **The estimand changed.** v7's Δ_R is pooled over the four wording frames; v8.1's is Δ_R(f), per frame, with n\*(f), m\*(f), ι_A(f), the admissibility test and the reference set all conditioned on f. No registered v8.1 quantity pools frames. | v7 numbers are **not comparable** and must never be merged. Eight configurations become twenty-four cells. |
| 2 | **Evidence status changed.** v7 was development runs at a commit whose protocol change was adopted after the outcomes were visible. v8.1 is preregistered, frozen, and analysed once by frozen code on 2.35 M rows. | Every hedge of the form "these are development results" is deleted and replaced by the provenance block of §2.1. |
| 3 | **The bounded result survives but its edge does not.** v7: "no simultaneous upper bound above +3.9 pp". v8.1: largest joint upper bound **+15.66 pp**, and one condition is not bounded below +10 pp. | v7's headline sentence must be **deleted, not softened**. |
| 4 | **Reference-set sensitivity is now measured and changes verdicts.** v7 flagged it qualitatively ("dropping one reference reverses the sign"). v8.1's registered F_REFSENS shows a 26.46 pp spread and **2 of 24 registered verdicts changing**. | This is promoted from a caveat to a Results-section finding and to a first-order Limitation. |
| 5 | **A new arm exists with its own answer.** SPECTRUM (28 conditions) was not in v7. It puts A *below* prediction in 25 of 28 conditions and **contradicts the LOCAL-positive cell by 24 pp on the same rows**. | A new Results subsection and a new main figure. |
| 6 | **The frame argument acquired confirmatory force.** Pooling E4B's three B-second frames returns +0.06 pp, concealing the only positive condition. | The wording-frame argument moves from methodological motivation to a demonstrated result. |
| 7 | **The ι direction.** β > 0 on a compliance axis means B fares worse beside an *easier* companion — the majority direction, and the opposite of the arm's premise. | Any sentence of the form "harder companions cost B more" is wrong for 19 of 28 conditions. |

---

# 4. Section-by-section audit of `neurips-4.pdf`

Format: **v7 purpose → what remains valid → what is stale → replacement
evidence → action.**

### Title — *KEEP BUT REFRAME*
"Compared With What? Distinguishing Generic Composition Costs from
Pair-Specific Instruction Interference". The question survives; the paper is
now confirmatory and frame-conditioned. Suggested:
**"Compared With What? A Frame-Conditioned Confirmatory Test of Pair-Specific
Instruction Interference"**. Retain "Compared With What?" — it is the paper's
thesis in three words.

### Abstract — *REPLACE*
Valid: the two-things-change-at-once framing; the verifier-scope sentence;
"a pair-specific claim needs an explicitly stated reference class".
Stale: "−13.2 to +39.2"; "∆R runs from −8.5 to +1.3"; "no simultaneous 95%
interval reaches an upper bound above +3.9 points"; "in three configurations
the references cost B more than A"; "These are development results".
Replacement: §1's three-sentence abstract; keep the 0.22/0.68/0.42/0.52
motivating fact from the v8.1 pre-confirmatory manuscript.
Action: **REPLACE** wholesale except the framing and scope sentences.

### §1 Introduction — *KEEP BUT REFRAME*
Valid and strong: paragraphs 1–2 ("The comparison that is missing", "Replace
the companion instead of removing it") are the best exposition in either
manuscript — keep near-verbatim. Stale: the "What we find, and how far it
reaches" paragraph, and "these are development runs".
Replacement: §2.3–2.5 here. Add one sentence naming the single positive
condition — a reader who first meets it in Results will distrust the paper.
Action: **KEEP BUT REFRAME**, rewriting only the findings paragraph.

### Contributions — *REPLACE*
v7's Claims 1/2/3. Claim 1 survives and strengthens; Claim 2's specific
numbers are dead; Claim 3 survives and is now confirmatory.
New list: (i) the frame-conditioned design and estimand; (ii) a preregistered,
frozen confirmatory test at 384 blocks per frame over 2.35 M generations;
(iii) the bounded result on 23 of 24 conditions at measured precision;
(iv) the one heterogeneous model and the three registered sensitivities that
undercut it; (v) the reference-set sensitivity result — a matched-reference
conclusion can turn on which admissible triple was frozen.

### §2 Related Work — *KEEP*
The estimand-gap argument (CSE, Instruction Stacking Collapse, MOSAIC,
SustainScore, Control Illusion, cross-component interference, WIRE) is
untouched by v8.1. Optionally fold in the prompt-sensitivity subsections from
`lp4fm_source/main_lp4fm.tex` if the venue rewards it.

### §3 Background — *KEEP*
Verifier-defined compliance, the directional outcome, the position factor. No
change.

### §4 Method — *MAJOR REWRITE*
v7's method is the pooled design. The v8.1 method already exists and is
correct in `main_v8_1_preconfirm.tex` §4 and Appendix B — **lift it**, then
insert three things v7 has no analogue for:
(a) the **joint cross-frame decision interval** and that it, not the marginal
or per-frame interval, decides;
(b) the registered reading grammar `L3a`/`L3b`/`L3c`/`INDETERMINATE@0.10` and
the `NEAR_FORM_UNAVAILABLE` disposition;
(c) the model-level conjunction rule and that heterogeneity is a *verdict*.

### §5 Results — *REPLACE (restructure)*
See §5 of this brief for the recommended new structure.

**§5.1 "Claim 1: raw composition effects are large, directional and
position-dependent" — KEEP THE ARGUMENT, UPDATE ALL NUMBERS.** Replace
−13.2/+39.2 with −13.5/+49.2; add D(A←B) −36.1..+54.5 and Λ −49.8..+52.3; add
F11 (`Ord_B` excludes zero on all 14 frames, reaching −46.84 pp). Keep the
"both instructions improve on Qwen" counterexample — it replicates (D(B←A)
negative in 10 of 12 Qwen cells).

**§5.2 "Claim 2: against the three selected references, no excess above 10
points" — MAJOR REWRITE.** The claim becomes *23 of 24* and acquires a named
exception. Of v7's four qualifications: "the threshold" **KEEP** (it is still
prior and still pre-registered); "two configurations could not have failed"
**UPDATE** (now 8 of 24 `COMPOSED_CONTRAST_RANGE_COMPRESSED`, all on Qwen
models); "the references disagree with one another" **KEEP AND STRENGTHEN**
(0.5–51.0 pp, exceeding |Δ_R| on 21 of 24); "the interval is conditional on
those three references" **PROMOTE TO A RESULT** — F_REFSENS now quantifies it
and changes 2 verdicts.

**§5.3 "Claim 3: a large solo-to-pair change does not identify a harmful
companion" — KEEP, RE-EXAMPLE.** Replace the E4B/B-second example (39.2 vs
46.4) with the confirmatory E4B f0 B-second example (49.2 vs 57.4, Δ_R −8.18),
and the E2B second example with E2B f3 B-second (23.7 vs 33.7, Δ_R −10.03).

### §6 Discussion — *KEEP BUT REFRAME*
Keep "What the matched contrast licenses" and "What it does not license" —
both are correct and unusually careful, and D18's ambiguity that v7 states
abstractly is now *measured* (§2.7). Add: why one positive condition neither
overturns nor confirms the bounded result; the LOCAL/SPECTRUM disagreement;
the reference-family observation as the most interesting open question.

### §7 Limitations — *REPLACE (reordered)*
Delete "these are development runs" and "the protocol change was adopted after
their outcomes were visible" — both are resolved by the freeze. Keep the
measurement paragraph (verifier-defined, no human labelling, no answer
quality, word-segmentation choices) verbatim; it is still exactly right.
New order: reference-set sensitivity (2 verdicts change) → 2507's
sample-sensitive eligibility → §26 `NOT_MET` on both Qwen models → §23
projection audit → every frame `OPERATING_POINT_UNSTABLE` → no near-form arm
→ measurement → scope.

### §8 Conclusion — *KEEP THE SHAPE, REPLACE THE SECOND HALF*
v7's shape is right. New second half: the contrast against a named class is
small in 23 of 24 conditions and is not in the twenty-fourth, and which class
you name — and under which wording — decides that.

### Figure 1 (design schematic) — *KEEP, EXTEND*
Still the right opening. Extend it with the per-frame conditioning strip
(the v8.1 pre-confirmatory manuscript's Figure 1 already does this).

### Figure 2 (raw composition effects) — *UPDATE NUMBERS, KEEP FORM*

### Figure 3 (Δ_R forest) — *REPLACE*
Now 24 cells, joint intervals, per-frame. See §6, Figure 2.

### Figure 4 (loss decomposition) — *KEEP FORM, RE-EXAMPLE*
See §6, Figure 1.

### Table 1 — *REPLACE*
v7's 8 rows become the 24-row matrix of §2.3.

### Appendix A (extended related work) — *KEEP*

### Appendix B (protocol and implementation) — *MAJOR REWRITE*
Lift from `main_v8_1_preconfirm.tex` Appendix B, then replace "Freeze,
provenance and current status" with §2.1 here, and add the reuse-guard fix and
the mixed-commit audit.

### Appendix C (C.1–C.4 sensitivities) — *REPLACE, EXPAND*
C.1 "The three references, and how much they differ" → **KEEP AND EXPAND**
with the full per-reference table. C.2 "Robustness recomputations" → **REPLACE**
with the F5/F6 tables. C.3 "Why no companion-class claim appears in the main
text" → **KEEP** and note that v8.1 runs no class arm at all, so Δ_broad is
unavailable by design rather than degenerate. C.4 "Diagnostics that license
nothing" → **KEEP the framing**; the v8.1 analogue is the §23 projection audit
and the F7 reciprocal losses. **NEW subsections**: F_REFSENS in full,
F_RUNNER_UP in full, SPECTRUM in full, the identification ledger, L4a.

### Appendix D (broader impacts) — *KEEP*

### NeurIPS checklist — *UPDATE*
Flip every "no confirmatory result exists" answer. Point the reproducibility
items at the frozen root, the bound commit, the preregistration hash and the
per-model analysis-record hashes in §2.1.

### NEW: historical-development appendix — *CREATE*
Keep v7's Table 1 as clearly-labelled superseded development evidence, plus
one paragraph on which of its claims replicate, weaken or fail (§7 here). Do
not delete it: it is the honest record of how the design got here.

---

# 5. Recommended main-text structure

The v8.1 science does not fit v7's three-claim Results section, because there
are now two arms and a sensitivity result that is itself a finding.

```
1  Introduction                     (v7 §1, findings paragraph replaced)
2  Related Work                     (v7 §2, unchanged)
3  Background                       (v7 §3, unchanged)
4  Method                           (v8.1 preconfirm §4 + joint interval,
                                     reading grammar, conjunction rule)
5  Identification and its stability  (~1 page; was v8.1 preconfirm §5)
6  Results
   6.1  Composition is large, directional and position-dependent
   6.2  The matched-reference contrast            [Table 1, Figure 2]
   6.3  The one heterogeneous condition           [Figure 3]
   6.4  Difficulty is not the explanation         [Figure 4]
   6.5  What the sensitivities do to the headline [Table 2]
7  Discussion
8  Limitations
9  Conclusion
```

**Main text**: §2.3 (24-cell table), §2.4 (verdicts), §2.5 (composition),
§2.6 (frame/order), the two verdict-changing F_REFSENS cells, the
F_RUNNER_UP one-line result, the SPECTRUM headline and the LOCAL/SPECTRUM
disagreement, the robustness ledger.

**Appendix**: full per-reference table, all 9–10 admissible triples per cell,
all 18 runner-up comparisons, all 28 SPECTRUM conditions, F5/F6 tables, the
projection audit, the identification ledger, L4a, the methodology-validation
detail, and the historical v7 table.

---

# 6. Figure and table plan

The proposed hierarchy (visual abstract → primary Δ_R → reference sensitivity
→ SPECTRUM) **is the right one**, with one amendment: the reference-sensitivity
figure and the one-positive-condition figure should be **the same figure**,
because the study's most reference-sensitive cell *is* its only positive cell.
That merge buys a slot for the raw-versus-matched decomposition, which is the
paper's most intuitive exhibit and its best inheritance from v7.

### Figure 1 — Composition versus companion identity *(visual abstract)*
- **Claim**: a large solo-to-pair change can carry almost no
  companion-specific signal.
- **Data**: `postconfirm/data/raw_vs_reference_loss.csv`.
- **Panels**: per model × order, a circle at D(B←A) and a hexagon at D(B←R̄)
  joined by a bar whose length is Δ_R; frames as small offsets.
- **Highlight**: Gemma-3n-E4B-it f0 B-second (49.2 → 57.4, Δ_R −8.18) and
  Qwen3-4B f0 B-first (−13.5 → −10.9, Δ_R −2.65) as the two regimes.
- **De-emphasise**: absolute compliance levels; individual frames.
- **Caption takeaway**: "B falls 49 points beside A and 57 points beside its
  matched references: almost none of a large composition effect is about A."

### Figure 2 — The frame-conditioned Δ_R(f) forest *(primary confirmatory)*
- **Claim**: 23 of 24 conditions bound the contrast below +10 pp at measured
  precision; one does not.
- **Data**: `postconfirm/data/primary_delta_by_frame_order.csv`.
- **Panels**: one row per model; within a row one line per entering frame,
  filled marker B-first, open B-second; vertical rules at 0 and +10.
  Draw the **joint** interval as the bar and the within-frame interval as a
  thin whisker so the multiplicity cost is visible.
- **Highlight**: the single `INDETERMINATE@0.10` marker past +10.
- **De-emphasise**: hatch the 8 `COMPOSED_CONTRAST_RANGE_COMPRESSED` cells.
- **Caption takeaway**: "Twenty-three of twenty-four intervals stop short of
  +10 points. The Qwen models' frames sit on top of one another; the Gemmas'
  spread out; one open marker sits alone past the threshold."

### Figure 3 — Where the one positive condition comes from *(primary + sensitivity)*
- **Claim**: the study's only positive contrast rests on one reference of
  three, and the choice of admissible triple changes the registered verdict.
- **Data**: `postconfirm/data/reference_sensitivity.csv`,
  `per_reference_contrasts.csv`.
- **Panels**: (a) the nine admissible triples for E4B f1 B-second as a dot
  plot from −8.63 to +12.64, frozen triple starred at the extreme;
  (b) the three per-reference contrasts (+5.63, +35.45, −3.16) with their
  intervals; (c) optionally the same dot plot for E4B f0 B-second (−8.18, the
  minimum, against a maximum of +16.92).
- **Highlight**: XC3:9's +35.45 and the frozen triple's extremity.
- **De-emphasise**: the 12 reference-robust cells (summarise as a count).
- **Caption takeaway**: "The frozen triple is the most harmful of its nine
  admissible alternatives; swap one reference and the registered reading
  changes."

### Figure 4 — SPECTRUM *(primary confirmatory, second arm)*
- **Claim**: after conditioning on stand-alone compliance, A is unexceptional
  — including in the one condition where the LOCAL arm says otherwise.
- **Data**: `postconfirm/data/spectrum_results.csv`, `spectrum_points.csv`.
- **Panels**: (a) the residual forest — δ_difficulty with its joint interval
  across all 28 conditions, ±10 pp band, colour only on `L3d` and the
  no-level cases; (b) the E4B f1 B-second scatter with the fitted line, A's
  star at +43.29 and the prediction at +54.78, residual −11.49 annotated.
- **Highlight**: that panel (b)'s residual points the *opposite* way to
  Figure 3's Δ_R.
- **De-emphasise**: individual companion identities in panel (a).
- **Caption takeaway**: "In the one condition where A costs B more than its
  three matched references, A costs B 11.5 points *less* than companions of
  its measured stand-alone compliance predict."
- **Axis warning**: label x as *stand-alone compliance ι*, with the cue
  `← harder · easier →`. Do **not** call it difficulty and do **not** plot
  `1 − ι`: β is registered on the ι scale.

### Table 1 — the 24-cell primary matrix
§2.3, trimmed to model, frame, order, n\*, m\*, frozen triple, Δ_R, joint CI,
registered reading. Dagger the compressed cells as v7 did.

### Table 2 — the robustness ledger
§2.11: one row per registered robustness analysis, its largest movement, the
most affected cell, whether the headline survives. **No prior version of the
paper has this and a referee will look for it.**

### Appendix figures
Full 28-panel SPECTRUM grid; all 18 runner-up comparisons; the
methodology-validation stability table (A vs B perturbations); the frame/order
detail. Already drawn: `dci1/reports/dci1v8dev/postconfirm/figures/`
(`fig1_spectrum_forest`, `fig2_spectrum_explainer`, `fig3_spectrum_grid`),
with a README recording input hashes and the ι orientation.

**Do not reuse** `f81_turnover.pdf` (candidate-set turnover) in the main text:
its subject is no longer the paper's result.

---

# 7. v7 claim-by-claim disposition

| v7 claim | disposition | why |
|---|---|---|
| "Raw composition effects are large and depend on which instruction is measured and where it appears" | **REPLICATES, STRENGTHENS** | D(B←A) now reaches +49.2 (was +39.2); D(A←B) +54.5; Λ spans −49.8..+52.3; `Ord_B` excludes zero on all 14 frames at up to −46.8 pp |
| "Direction is not uniform across models" | **REPLICATES** | composition still helps B on both Qwen models (10 of 12 cells negative) |
| "Δ_R runs between −8.5 and +1.3 pp" | **WEAKENS — range widens both ways** | v8.1: −11.19 to +12.64 pp |
| "No simultaneous upper bound exceeds +3.9 pp" | **DOES NOT REPLICATE** | largest joint upper bound +15.66 pp; 3 of 24 exceed +3.9. **Delete, do not soften.** |
| "In three configurations the references cost B more than A" | **REPLICATES, STRENGTHENS** | 11 of 24 joint intervals wholly below zero, to −11.19 pp |
| "Matched-reference interference is much smaller than raw composition loss" | **REPLICATES** | ratio median 3.8, max 88.6; 11 of 24 raw cells >10 pp against 3 of 24 for Δ_R |
| "Every entering configuration satisfies the bounded reading" | **WEAKENS: 23 of 24** | E4B f1 B-second reads `INDETERMINATE@0.10` |
| "The references disagree by more than Δ_R" | **REPLICATES, STRENGTHENS** | spreads 0.5–51.0 pp (v7: 2.9–10.3), exceeding |Δ_R| on 21 of 24 |
| "Two configurations could not have failed (ceiling compression)" | **REPLICATES, different footprint** | 8 of 24 cells, all Qwen |
| "The interval is conditional on those three references" | **REPLICATES and is now quantified** | across-triple spread to 26.46 pp; 2 verdicts change |
| "Only 6–14% of candidates survived; no run generated a second reference set" | **SUPERSEDED / RESOLVED** | v8.1 freezes five families per frame and re-forms Δ_R over all 9–10 admissible triples |
| "Admission used raw solo compliance where the protocol specifies a chance-corrected coordinate" | **NOT COMPARABLE — fixed** | v8.1 admits on chance-corrected ι throughout |
| v7's per-model, per-order verdicts | **NOT COMPARABLE** | the estimand changed: pooled vs per-frame |
| "A is not unusually harmful" | **NEVER LICENSED, IN EITHER** | v7 disclaims it; v8.1 makes it unreachable by construction |
| Are there positive pair-specific effects? | **NEW: one, uncertified** | +12.64 pp, interval excludes zero, no registered level, four qualifications, SPECTRUM contradicting |

**Did conditioning on wording reveal heterogeneity that pooling hid?** Yes,
once, decisively (E4B B-second: +0.06 pp pooled against −8.18/+12.64/−4.29).
And nothing on the Qwen models, where frames agree within 1.4–4.5 pp. The
lesson is asymmetric: frame conditioning is necessary because heterogeneity is
model-specific and unpredictable in advance, not because it is ubiquitous.

---

# 8. Claim ledger

Evidence classes: **PC** primary confirmatory · **RS** registered sensitivity ·
**RD** registered descriptive · **MV** methodology validation ·
**SD** superseded development · **EP** exploratory post-hoc.

| candidate statement | class | scope | exact supporting result | allowed wording | too-strong wording |
|---|:-:|---|---|---|---|
| A costs B no more than same-form companions matched on frame-conditioned compliance | **PC** | per model × frame × order | `L3c` on the joint interval, 23 of 24 | "In 23 of the 24 entering conditions the simultaneous interval for Δ_R(f) stops below +10 pp." | "A is not unusually harmful"; "no pair-specific interference"; "equivalent to zero" |
| Model-level equivalence | **PC** | per model × order | 7 of 8 `LOCAL_EQUIVALENT_SAME_FORM_ONLY` | "Seven of eight model × order configurations return the registered same-form-only equivalence verdict." | dropping "same-form-only"; generalising to companions at large |
| One condition shows A costing B more | **PC** | one cell | +12.64 pp, [+9.62, +15.66], `INDETERMINATE@0.10` | "Δ_R = +12.6 pp with a joint interval excluding zero; the registered rule certifies neither an excess above +10 pp nor a bound below it." | "A specifically interferes with B on this model"; omitting the four qualifications |
| Frames disagree within a model | **PC** | one model × order | `FRAME_HETEROGENEOUS` | "On one model and prompt order the entering frames do not reach the same reading; the registered verdict is heterogeneity." | treating heterogeneity as a null or as noise |
| **"A is not unusually harmful."** | — | — | — | **Never licensed.** `NEAR_FORM_UNAVAILABLE` makes the strong L3c unreachable by construction, and one condition reads `INDETERMINATE@0.10`. | any use at all |
| **"Large composition effects are generic."** | **PC** (partly) | 24 cells | D(B←A) −13.5..+49.2; Δ_R bounded on 23 of 24 | "Composition effects are large and are not explained by the companion's identity within the named class." | "generic" — it implies a mechanism the design cannot see |
| **"Difficulty explains interference."** | — | — | SPECTRUM `L3e` on 17 of 28 | **Not licensed.** The fit carries family-aware intercepts, i.e. it concedes that family matters at fixed ι. | any causal or explanatory reading |
| **"Difficulty does not fully explain interference."** | **PC + RD** | 28 SPECTRUM cells | family-aware intercepts required; F2 Δ_j by family (XC3 +5.17, MK\* −3.51) | "After conditioning on stand-alone compliance, A is unexceptional; what the relation does not absorb tracks the companion's family." | attaching an interval to the family grouping |
| **"Reference identity matters."** | **RS + RD** | 24 cells | across-triple spread to 26.46 pp; 2 verdicts change; per-reference spreads to 50.98 pp | "The choice among admissible matched triples moves Δ_R by up to 26 pp and changes the registered reading on two of twenty-four conditions." | implying the frozen triple is wrong or replaceable |
| **"Wording changes the control set."** | **MV** | pre-freeze | 2 of 14 admissibility verdicts; 1 model's eligibility | "At equal budget, frame-conditioned forwarding changes the admissibility verdict on two of fourteen supported frames and one model's eligibility." | claiming it changes the confirmatory result |
| **"The result generalises across models."** | — | — | — | **Not licensed.** Four checkpoints in two families, reported per model, never pooled, and one disagrees with itself across frames. | any cross-model generalisation |
| **"The result is robust to reference selection."** | — | — | 2 of 24 verdicts change | **False as stated.** | any unqualified robustness claim |
| **"The result is robust to operating-point choice."** | **RS** | 18 comparisons, 7 frames | 0 reading changes; max movement 12.77 pp | "The runner-up operating point changes no registered reading." | "the operating point does not matter" — every frame is `OPERATING_POINT_UNSTABLE` |
| B's loss varies with the companion's compliance | **PC** | 28 cells | β: 19 above zero, 4 below, 5 spanning | "The fitted slope excludes zero above it in nineteen of twenty-eight conditions — B fares worse beside an *easier* companion — and below it in four." | "harder companions cost B more" (contradicted in 19 of 28); any mechanism |
| §26 not met on the Qwen models | **PC** | 2 models | `NOT_MET`, D(A←B) precision only | "The registered methodological-success criterion is not met on either Qwen model, because D(A←B) misses its precision precondition; every Δ_R interval meets it." | omitting it; implying Δ_R is imprecise |
| The admission projection is badly calibrated | **RD** | all composed cells | 370 of 370 outside the 0.05 allowance, median \|err\| 0.264 | "The §13.6 admission projection lies outside its allowance on every audited composed cell." | treating it as invalidating admission — by rule it revises none |
| A large solo-to-pair change does not identify a harmful companion | **PC** | the whole study | the three results above together | "A solo-to-pair change is not by itself evidence about the companion's identity; a pair-specific claim requires an explicitly stated reference class." | dropping "explicitly stated reference class" |
| v7's "Δ_R between −8.5 and +1.3; no bound above +3.9" | **SD** | superseded | v7 Table 1 | only as "the superseded development design reported…" | any presentation as a current result |

---

# 9. Limitations and claims that remain unavailable

1. **`NEAR_FORM_UNAVAILABLE`.** No near-form arm, so no verdict distinguishes
   "A is not special" from "the excess is a property of the exact-count form"
   — and §2.7 shows the data actively raise that question.
2. **No class arm.** Δ_broad unavailable; nothing licensed about companions
   outside the exact-count form.
3. **Reference-set conditionality.** 2 of 24 verdicts change; the frozen
   triple is at an extreme of its set on 7 of 24; the reported interval does
   not cover this.
4. **Every frame `OPERATING_POINT_UNSTABLE`.** Δ_R(f) is conditional on the
   frozen n\*(f), m\*(f); the runner-up arm bounds one alternative, not the
   grid.
5. **2507's eligibility is sample-sensitive.** Under a different partition of
   the same 216 pre-freeze topics it would not have entered. Its result must
   travel with that sentence.
6. **§26 `NOT_MET` on both Qwen models**, on D(A←B)'s precision.
7. **§23 projection audit** outside its allowance on every audited composed
   cell.
8. **Ceiling compression** on 8 of 24 cells.
9. **Ξ does not resolve outcome-specificity on 18 of 24 cells**: even a
   resolved excess could be A being generally disruptive rather than
   specifically harmful to B.
10. **Verifier-defined compliance.** Deterministic verifier validated against
    an independent reimplementation, a frozen boundary suite, an adversarial
    corpus and seeded-defect tests — but **no human labelling**, and no
    quantity measures answer quality.
11. **Scope.** One focal instruction (`marker_however`, exact-count form), one
    base-task genre, three same-form references per model × frame, four small
    open-weight checkpoints in two families, two prompt positions. Per model,
    never pooled.
12. **No mechanism.** The design reads no model internals.
13. **Frames are four sentence templates**, not a sample from a population of
    phrasings. Nothing generalises to unseen wordings.

---

# 10. Source-artifact and dataset index

```
result → postconfirm CSV → signed analysis record → freeze → commit
  dci1/reports/dci1v8dev/postconfirm/data/*.csv
    ← dci1/tools/v8_postconfirm_extract.py
       ← <root>/durable/dci1v8/<model>/CONFIRMATORY_ANALYSIS/confirmatory_analysis.json
          ← FROZEN/freeze.json  (membership 31af521c…, manifest 8cfa2082…)
             ← commit 034fc7214762b6848d5d904b14fd82b317830667
                preregistration d3552f9f47e3f008…
```

`<root>` = `dci1/evidence/dci1v8p1-confirm`, worktree
`/home/cnm13ryan/git/dci-v8-canonical`, branch `dev/v8-frame-aware-prescreen`.
**`dci1/evidence/` is gitignored and does not survive a clone**; the durable
artifact for every number is the committed CSV/JSON, whose `provenance.json`
carries each model's analysis-record hash, freeze hash, generation-record
hash, producing commit, resample count and row count.

| dataset | rows | contents |
|---|---:|---|
| `primary_delta_by_frame_order.{csv,json}` | 24 | Δ_R, SE, marginal / within-frame / **joint** intervals, precision flag, registered reading, direction, statuses, qualifiers, boundary record, n\*, m\*, ι_A, frozen triple |
| `raw_vs_reference_loss.csv` | 24 | B solo, c(B\|B+A), c(B\|B+R̄), D(B←A), D(B←R1..R3), D(A←B), Λ |
| `per_reference_contrasts.csv` | 72 | Δ_1..Δ_3 with within-family intervals, family, ι, realised c(B\|B+R_j), spread, heterogeneity flags |
| `reference_sensitivity.csv` | 226 | every admissible triple's Δ_R with its simultaneous interval, min/max/spread, sign-flip and frozen flags |
| `runner_up_sensitivity.csv` | 18 | frozen vs runner-up operating point with intervals and stability status |
| `spectrum_results.csv` | 28 | β with interval, ι_A, observed and predicted loss, δ_difficulty with joint interval and reading, support, intercepts, residuals |
| `spectrum_points.csv` | 288 | the (companion, family, ι, B-loss, realised compliance) points the registered fit consumed, plus A's point, prediction and residual |
| `registered_gates.csv` | 24 | L1 headroom, L2, Ξ, vacuity, reference heterogeneity, projection audit |
| `recoding_robustness.csv` | 96 | F5 vacuity-forced and graded-0.99 recomputations |
| `order_contrasts.csv` | 54 | F11 `Ord_A`, `Ord_B`, `Ord_Λ`, `Ord_R̄` |
| `projection_audit.csv` | 384 | §23 projected vs realised composed rate |
| `cross_configuration_consistency.csv` | 24 | L4a per-member agreement across orders |
| `identification_ledger.csv` | 1,646 | §34 D6 status of every registered member |
| `model_level_verdicts.csv` | 8 | model verdict, per-frame readings, L3c disposition, §26 outcome |
| `methodology_validation_final.csv` | 21 | the A/B perturbation digest |
| `provenance.json` | — | per-model record hashes, commit, resamples, row counts, frames |

**Other authoritative documents**: `V8_1_POSTCONFIRM_PAPER_REWRITE_BUNDLE.md`
(full interpretation, 20 sections); `POSTCONFIRM_EXEC_SUMMARY.md`;
`dci1/reports/dci1v8dev/frame_aware_prescreen/prescreen_revalidation.md`
(methodology validation); `dci1/reports/dci1v8dev/confirmatory/V8P1_FREEZE_AND_GENERATION.md`;
`dci1/docs/DCI1_preregistration_v8.1.md`; `dci1/docs/V8_CONFIRMATORY.md`;
`dci1/docs/V8_FRAME_CONDITIONING.md`; `dci1/docs/V8_TOPIC_RESAMPLED_VALIDATION.md`;
figures and their README under `dci1/reports/dci1v8dev/postconfirm/figures/`.

**Manuscript sources**: `~/Downloads/v8_1_source/main_v8_1_preconfirm.tex`
(the correct v8.1 Method and Appendix B — lift these);
`~/Downloads/lp4fm_source/main_lp4fm.tex` (prompt-sensitivity framing and two
extra related-work subsections); `~/Downloads/neurips-4.pdf` and
`/home/cnm13ryan/git/dci/neurips-4.pdf` (the v7 manuscript — narrative shape
only, **no numbers**).
