# Prompt: rewrite the DCI-1 manuscript from v7 to v8.1

You are rewriting a NeurIPS submission. The study it reports has been redone:
what was a set of development runs under a frame-pooled design is now a
preregistered, frozen, completed confirmatory experiment under a
frame-conditioned design. Your job is to produce the v8.1 manuscript.

You have everything you need here. **Do not go looking for the analysis
codebase** — every number you may use is in this document, and every number
carries the artifact it came from.

---

## 0. Inputs, and one naming correction

| you are given | what it is | how to use it |
|---|---|---|
| `neurips-4.pdf` | **the v7 manuscript.** (The task that produced this prompt called it `neurips-5.pdf`; no such file exists on the machine, and `neurips-4.pdf` has exactly the structure being audited — §1–§8, Figures 1–4, Table 1, Appendices A/B/C.1–C.4/D, checklist.) | narrative shape, exposition, related work — **and none of its numbers** |
| `main_v8_1_preconfirm.tex` (in `v8_1_source/`) | the pre-confirmatory v8.1 design paper | **lift its §4 Method and Appendix B**: they are already the correct frozen protocol. Its Results section is obsolete. |
| `main_lp4fm.tex` (in `lp4fm_source/`) | the same body reframed for a prompt-sensitivity venue | harvest its extra related-work subsections if useful |
| this prompt | the confirmatory results | the source of every number in the new paper |

**Absolute rule.** v7's numbers are superseded development evidence produced
under a *different estimand* (pooled over wording frames). They may appear
only in a clearly-labelled historical appendix. Never mix them with v8.1
results, never compare them numerically in the main text.

---

## 1. The story to tell

**One sentence.** Against three same-form companions matched to it on
wording-conditioned stand-alone compliance, the focal instruction A costs
compliance with B less than 10 percentage points more than they do in 23 of
24 preregistered model × wording-frame × prompt-order conditions — while
composition itself moves B's compliance by up to 49 percentage points.

**The shape of the argument**, in four moves:

1. Composition moves compliance enormously, and how much depends on which
   instruction is measured and where it stands. *(survives from v7, stronger)*
2. Replace the companion instead of removing it, and almost all of that
   movement is left behind. *(survives from v7, now confirmatory)*
3. But conditioning on wording is what makes that comparison well defined —
   and on one model it reveals a condition that pooling would have hidden.
   *(new; the paper's reason to exist in this form)*
4. And even the one positive condition turns on which of three references was
   frozen, which the registered sensitivity analysis quantifies and the
   second arm contradicts. *(new; the paper's most interesting content)*

**The central methodological lesson.** v7 said a solo-to-pair change does not
identify a harmful companion; that survives. Its successor: naming a reference
class is not one decision but three — *which admissible members you froze*
(2 of 24 verdicts move), *under which wording you matched them* (a 20.8 pp
between-frame range that crosses a verdict boundary), and *which comparison
class you chose at all* (the two arms disagree by 24 pp on the same rows). A
paper that reports only the first is reporting a third of its own uncertainty.

**Write this abstract-level result** (adapt the prose, keep every number):

> Composing two verifiable instructions moves compliance enormously — B's
> compliance falls by as much as 49 pp beside A and rises by as much as 13 pp
> beside it, depending on model and position — but replacing the companion
> instead of removing it leaves almost all of that movement behind: in 23 of
> 24 preregistered conditions the simultaneous interval for the
> matched-reference contrast stops below 10 percentage points, at realised
> half-widths of 1.1–3.2 points, so the smallness is measured rather than
> underpowered. The twenty-fourth condition — one model under one of four
> sentence frames with B stated second — puts the contrast at +12.6 points, a
> result the registered rule declines to certify and that three registered
> sensitivities undercut: one of its three references carries it, the
> registered graded recoding cuts it 44% to +7.1 points, and the
> difficulty-spectrum arm on the same rows puts A 11.5 points *below* what
> companions of its measured stand-alone compliance predict. Conditioning on
> wording is what made that condition visible at all — averaging the model's
> three frames returns +0.06 points — so a pair-specific claim needs not only
> an explicitly stated reference class but the phrasing under which that class
> was matched.

---

## 2. The design, in the terms the paper must use

Four wording frames f ∈ {0,1,2,3} phrase the same instruction. **The frame is
part of the experimental condition**, not presentation: the operating points
n\*(f) and m\*(f), the difficulty coordinate ι_A(f), the admissibility test and
the reference set are all conditioned on f, and Gates 2 and 3, the analysis and
the report are all per frame. The estimand is Δ_R(f), per frame — **there is
no registered quantity that pools frames, and you must not construct one.**

12 entering LOCAL frames and 14 entering SPECTRUM frames over four models; 24
LOCAL cells and 28 SPECTRUM cells once both prompt orders count.

| model | LOCAL frames | SPECTRUM frames |
|---|---|---|
| Qwen3-4B | 0, 1, 2, 3 | 0, 1, 2, 3 |
| Qwen3-4B-Instruct-2507 | 1, 3 | 1, 3 |
| Gemma-3n-E2B-it | 0, 1, 3 | 0, 1, 2, 3 |
| Gemma-3n-E4B-it | 0, 1, 3 | 0, 1, 2, 3 |

**Three method facts v7 has no analogue for. Put all three in §4.**

1. **The decision interval is the JOINT cross-frame simultaneous interval** —
   every F1 member of every entering frame of a model, critical value from a
   topic-level block bootstrap with one draw shared across frames (realised
   values 2.798–3.017). The per-frame and marginal intervals are reported
   beside it but **decide nothing**. Never substitute one for the other.
2. **The registered reading grammar for Δ_R.** Half-width > 5 pp →
   `INSUFFICIENT_PRECISION`. Lower > +10 pp → `L3a` (and `L3b` if > +25 pp).
   Upper < +10 pp → `L3c`, the bounded reading. Otherwise
   `INDETERMINATE@0.10`. Direction is read separately: lower > 0 is
   `A_HARMS_MORE`, upper < 0 is `A_COMPARATIVELY_BETTER`.
3. **The model-level verdict is the conjunction over entering frames**
   (intersection–union, no further adjustment). There is no
   at-least-one-frame claim. **Disagreement between frames is itself a
   verdict** (`FRAME_HETEROGENEOUS`), not a failure and not noise.

**Provenance block for Appendix B** (replace v7's "current status"):
confirmatory root `dci1/evidence/dci1v8p1-confirm`; every stage record bound
to commit `034fc7214762b6848d5d904b14fd82b317830667`; preregistration
`dci1/docs/DCI1_preregistration_v8.1.md` hash `d3552f9f47e3f008…`;
registration manifest `8cfa20827b3f46fc…`; membership lock `31af521c21d5cee4…`;
rules hash `3d9064ea0f99cc9b…`; verifier `ea885b0db67e3c7c…`; wording
`fe3b5be15759af1c…`; topic split `c10f17bc5846e185…` (v4r2 split seed carried
unchanged); **2,353,152 rows planned and generated**, complete with zero
missing, duplicate or unexpected identities; 384 blocks per entering frame;
10,000 bootstrap resamples; decoding stochastic T = 0.7, top-p 0.9, top-k 50,
`NO_THINKING`, engine seed 20260819, pinned backend, TP = 1. The frozen
analysis and the frozen final report each ran **once**, unattended, returning
`PASS` for all four models with **7 of 7 traceability checks passing**.

---

## 3. The results the paper must report

### 3.1 Table 1 — the primary matrix (all 24 cells)

Δ_R is mean reference loss minus focal loss: **positive means B fares worse
beside A than beside the three references**. All magnitudes in percentage
points of B-compliance. The interval is the JOINT one.

| model | f | order | n\* | m\* | ι_A | frozen triple | Δ_R | joint 95% CI | reading |
|---|---:|---|---:|---:|---:|---|---:|---|---|
| Qwen3-4B | 0 | B first | 6 | 12 | 0.674 | XC3:10 / MK1:4 / MK6:6 | −2.65 | [−4.73, −0.56] | L3c † |
| Qwen3-4B | 0 | B second | 6 | 12 | 0.674 | XC3:10 / MK1:4 / MK6:6 | −5.54 | [−8.31, −2.78] | L3c |
| Qwen3-4B | 1 | B first | 7 | 12 | 0.608 | MK7:2 / XC3:9 / MK2:7 | −1.20 | [−3.41, +1.00] | L3c † |
| Qwen3-4B | 1 | B second | 7 | 12 | 0.608 | MK7:2 / XC3:9 / MK2:7 | −2.93 | [−5.67, −0.19] | L3c |
| Qwen3-4B | 2 | B first | 3 | 12 | 0.673 | MK7:2 / MK1:6 / MK6:5 | −0.76 | [−2.71, +1.19] | L3c † |
| Qwen3-4B | 2 | B second | 3 | 12 | 0.673 | MK7:2 / MK1:6 / MK6:5 | −3.49 | [−6.70, −0.29] | L3c |
| Qwen3-4B | 3 | B first | 5 | 13 | 0.702 | XC3:8 / MK2:5 / MK7:2 | +0.10 | [−0.95, +1.15] | L3c † |
| Qwen3-4B | 3 | B second | 5 | 13 | 0.702 | XC3:8 / MK2:5 / MK7:2 | −1.02 | [−2.99, +0.95] | L3c † |
| Qwen3-4B-Instruct-2507 | 1 | B first | 6 | 10 | 0.652 | MK2:8 / MK5:6 / MK3:2 | +1.50 | [−0.13, +3.12] | L3c † |
| Qwen3-4B-Instruct-2507 | 1 | B second | 6 | 10 | 0.652 | MK2:8 / MK5:6 / MK3:2 | −1.00 | [−3.74, +1.75] | L3c |
| Qwen3-4B-Instruct-2507 | 3 | B first | 6 | 12 | 0.673 | MK6:10 / MK8:3 / MK7:6 | −0.88 | [−2.68, +0.92] | L3c † |
| Qwen3-4B-Instruct-2507 | 3 | B second | 6 | 12 | 0.673 | MK6:10 / MK8:3 / MK7:6 | −2.43 | [−4.43, −0.43] | L3c † |
| Gemma-3n-E2B-it | 0 | B first | 8 | 8 | 0.642 | MK4:1 / MK2:6 / XC3:8 | −0.43 | [−2.97, +2.10] | L3c |
| Gemma-3n-E2B-it | 0 | B second | 8 | 8 | 0.642 | MK4:1 / MK2:6 / XC3:8 | **−11.19** | [−14.43, −7.95] | L3c |
| Gemma-3n-E2B-it | 1 | B first | 3 | 10 | 0.635 | MK2:5 / XC3:9 / MK5:8 | +1.41 | [−1.11, +3.93] | L3c |
| Gemma-3n-E2B-it | 1 | B second | 3 | 10 | 0.635 | MK2:5 / XC3:9 / MK5:8 | −2.99 | [−5.93, −0.06] | L3c |
| Gemma-3n-E2B-it | 3 | B first | 7 | 11 | 0.686 | MK6:8 / MK8:3 / MK2:3 | −6.93 | [−9.20, −4.67] | L3c |
| Gemma-3n-E2B-it | 3 | B second | 7 | 11 | 0.686 | MK6:8 / MK8:3 / MK2:3 | −10.03 | [−13.08, −6.97] | L3c |
| Gemma-3n-E4B-it | 0 | B first | 6 | 9 | 0.745 | MK2:6 / MK1:5 / MK4:8 | −2.21 | [−4.84, +0.41] | L3c |
| Gemma-3n-E4B-it | 0 | B second | 6 | 9 | 0.745 | MK2:6 / MK1:5 / MK4:8 | −8.18 | [−10.78, −5.58] | L3c |
| Gemma-3n-E4B-it | 1 | B first | 6 | 9 | 0.711 | MK3:3 / XC3:9 / MK5:6 | +2.15 | [−0.37, +4.66] | L3c |
| **Gemma-3n-E4B-it** | **1** | **B second** | 6 | 9 | 0.711 | **MK3:3 / XC3:9 / MK5:6** | **+12.64** | **[+9.62, +15.66]** | **INDETERMINATE@0.10** |
| Gemma-3n-E4B-it | 3 | B first | 8 | 10 | 0.688 | MK2:6 / MK1:5 / MK3:1 | +0.76 | [−1.61, +3.13] | L3c |
| Gemma-3n-E4B-it | 3 | B second | 8 | 10 | 0.688 | MK2:6 / MK1:5 / MK3:1 | −4.29 | [−7.21, −1.36] | L3c |

† = `COMPOSED_CONTRAST_RANGE_COMPRESSED`: the arms' own compliance levels
arithmetically restricted how large Δ_R could have been. Eight cells, **all on
Qwen models**. This is the v8.1 analogue of v7's dagger and must be marked.

**Summary sentences you may write.** Δ_R ranges −11.19 to +12.64 pp; 18 of 24
point estimates negative; **11 of 24 joint intervals lie wholly below zero**
(the references cost B more than A) and 1 wholly above; the precision
precondition is met **24 of 24** with realised half-widths 1.05–3.24 pp
against a 5 pp requirement; the largest joint upper bound is +15.66 pp;
**`beyond_sesoi` is false in every one of the 24 cells**, so no condition
resolves an excess beyond the 10 pp smallest effect of interest.

**Two further registered qualifications to state in the text.**
`A_GENERAL_NOT_EXCLUDED` — the Ξ gate does not resolve outcome-specificity —
fires on **18 of 24** cells: even a resolved excess could be A being generally
disruptive rather than specifically harmful to B. `REFERENCE_HETEROGENEOUS`
fires on 3, `VACUITY_DEPENDENT` on 7.

*Source: `primary_delta_by_frame_order.csv`.*

### 3.2 Model-level verdicts

| model | B first | B second |
|---|---|---|
| Qwen3-4B | `LOCAL_EQUIVALENT_SAME_FORM_ONLY` | `LOCAL_EQUIVALENT_SAME_FORM_ONLY` |
| Qwen3-4B-Instruct-2507 | `LOCAL_EQUIVALENT_SAME_FORM_ONLY` | `LOCAL_EQUIVALENT_SAME_FORM_ONLY` |
| Gemma-3n-E2B-it | `LOCAL_EQUIVALENT_SAME_FORM_ONLY` | `LOCAL_EQUIVALENT_SAME_FORM_ONLY` |
| Gemma-3n-E4B-it | `LOCAL_EQUIVALENT_SAME_FORM_ONLY` | **`FRAME_HETEROGENEOUS`** |

Every verdict carries **`NEAR_FORM_UNAVAILABLE`**: the design runs no
near-form arm, so the *strong* refutation verdict is unreachable **by
construction**, and `LOCAL_EQUIVALENT_SAME_FORM_ONLY` — no excess relative to
same-form, exact-count companions matched on frame-conditioned compliance — is
the most a same-form pool licenses.

**§26 methodological success**: `MET` on both Gemma models, **`NOT_MET` on both
Qwen models**. The cause is confined to one member — `D(A←B)`, the reciprocal
loss, misses its precision precondition on 10 intervals for Qwen3-4B and 5 for
2507. **Every Δ_R interval in the study meets its precondition.** Report the
`NOT_MET` verdict *and* that it does not touch the primary estimand.

**Scope sentence, verbatim from the signed FINAL_REPORT record** — use it in
the Discussion:

> "each Δ_R(f) is a statement about this model under this wording frame at the
> frozen n\*(f), m\*(f) and reference triple; the model-level verdict is the
> conjunction over its entering frames; nothing here generalises across
> wordings or models"

*Source: `model_level_verdicts.csv`; FINAL_REPORT `strongest_permissible_statement`.*

### 3.3 Composition versus companion identity

| quantity | range over the 24 cells |
|---|---|
| D(B←A), the raw solo-to-pair change on B | **−13.5 to +49.2 pp** |
| D(B←R̄), the same beside the matched references | **−11.9 to +57.4 pp** |
| D(A←B), the reciprocal change on A | **−36.1 to +54.5 pp** |
| Λ = D(A←B) − D(B←A) | **−49.8 to +52.3 pp** |
| Δ_R | **−11.2 to +12.6 pp** |

11 of 24 cells move B by more than 10 pp raw; 3 of 24 move Δ_R by more than 10
pp. The ratio |D(B←A)| / |Δ_R| has median **3.8** and maximum **88.6**.

**Use these two examples; they replace v7's.**
*The headline example*: Gemma-3n-E4B-it, frame 0, B second — B's compliance
falls from **0.713 alone to 0.221 beside A** (49.2 pp) and to **0.140 beside
the three matched references** (57.4 pp), Δ_R = **−8.18 pp**. Almost none of a
49-point composition effect is attributable to A's identity.
*The opposite regime*: Qwen3-4B, frame 0, B first — B *improves* by 13.5 pp
beside A and by 10.9 pp beside the references, Δ_R = −2.65 pp. On the Qwen
models D(B←A) is negative in 10 of 12 cells: composition often *helps*. Keep
v7's observation that this is a direct counterexample to any shared-resource
reading; it replicates.

**Position dominates companion identity.** The registered order contrasts
(F11): `Ord_B` excludes zero on **all 14 frames** and reaches **−46.84 pp**
(Gemma-3n-E4B-it f0); `Ord_A` excludes zero on 11 of 14; `Ord_Λ` reaches
−35.25 pp. Mark Qwen3-4B's `Ord_A` on f0 and f1 — they miss the precision
precondition.

*Sources: `raw_vs_reference_loss.csv`, `order_contrasts.csv`.*

### 3.4 Frame and order heterogeneity — the argument for conditioning

Between-frame range in Δ_R: Qwen3-4B 2.75 / 4.52 pp; 2507 2.38 / 1.43 pp;
Gemma-3n-E2B-it 8.34 / 8.19 pp; **Gemma-3n-E4B-it 4.36 / 20.82 pp**.

Order differences run **−10.75 pp** (E2B f0) to **+10.49 pp** (E4B f1). In 11
of 12 frames Δ_R falls when B is stated second; E4B f1 is the exception, and
it is the frame that produces the only positive result.

**The decisive sentence.** Averaging Gemma-3n-E4B-it's three entering frames
with B second gives (−8.18 + 12.64 − 4.29)/3 = **+0.06 pp** — a clean-looking
null that would have concealed the only positive condition in the study.

**Be honest about the asymmetry.** On the two Qwen models frame conditioning
found nothing pooling would have missed, and it cost a quarter of the evidence
per cell. The argument is not that heterogeneity is ubiquitous; it is that it
is model-specific and unpredictable in advance.

### 3.5 Reference-set sensitivity (registered family F_REFSENS)

Δ_R re-formed over every structurally admissible triple of the frame's five
frozen families, on the same cells, each with its own simultaneous interval.
**The primary claim is decided by the frozen triple and by nothing else**;
this family is descriptive and licenses no claim.

| class | cells |
|---|---:|
| reference-robust (one verdict, spread < 5 pp) | 12 |
| sensitive but same registered verdict | 10 |
| **registered verdict changes across admissible triples** | **2** |

Across-triple spread reaches **26.46 pp**; the sign flips on **14 of 24**; the
spread exceeds 10 pp on **6 of 24**; the frozen triple sits at an extreme of
its own admissible set on **7 of 24**.

**The two verdict changes, both Gemma-3n-E4B-it with B second:**

- **f0** — the frozen Δ_R of −8.18 is the **most negative of nine** admissible
  triples; the others run to **+16.92 pp**, and five of nine have simultaneous
  intervals wholly above +10 pp (an `L3a` reading). Per-reference contrasts:
  −12.53, −12.11, +0.10.
- **f1**, the study's only positive cell — the frozen +12.64 is the **most
  harmful of nine**; the range is **−8.63 to +12.64 pp**, a spread of 21.27,
  and the sign flips. Two triples read `L3a`, one `INDETERMINATE@0.10` (the
  frozen one), six `L3c`. Its three per-reference contrasts are +5.63
  (MK3:3), **+35.45 (XC3:9)** and −3.16 (MK5:6), all with intervals excluding
  zero.

**Say this in Results, not in an appendix**: the bootstrap resamples *topics*,
not reference sets, so the reported interval says nothing about this
variation — and here, as in v7, it is the larger source.

*Source: `reference_sensitivity.csv`, `per_reference_contrasts.csv`.*

### 3.6 Per-reference heterogeneity

The three per-reference contrasts **disagree in sign on 15 of 24 cells**; the
within-cell spread exceeds |Δ_R| on **21 of 24** and the joint half-width on
21 of 24; spreads run **0.52 pp** to **50.98 pp** (Gemma-3n-E2B-it f0
B-second: −15.92, −34.31, +16.67 → mean −11.19). v7 reported 2.9–10.3 pp; the
heterogeneity got *larger*, not smaller.

**One descriptive observation worth a Discussion paragraph — flag it as
post-hoc.** A is `marker_however`, an exact-count instruction over a marker
word. Grouping the 72 registered per-reference contrasts by the reference's
family: **XC3** (same exact-count form, counts *sentences*) has mean Δ_j
**+5.17 pp** (n = 12, max +35.45); the eight **marker-word** families pooled
have mean **−3.51 pp** (n = 60). So against companions that count another
marker word A is unexceptional; against a same-form companion counting a
different object it looks worse. **This is exactly the registered ambiguity
the design flags — "A is not special" versus "the excess is a property of the
exact-count form" — now measured.** It is a post-hoc grouping of registered
quantities, carries no interval, and no registered family estimates a
family-level contrast. Present it as an open question, never as a tested
effect.

### 3.7 Operating-point robustness (registered family F_RUNNER_UP)

**Every entering frame of every model carries `OPERATING_POINT_UNSTABLE`** —
the frozen n\*(f) was re-selected on fewer than two-thirds of 2,000 topic
resamples. The registered response is not to replace it but to carry the
contrast at the runner-up severity on the *same* blocks. Runner-up arms exist
on **7 of the 12 LOCAL frames**, giving **18 comparisons**.

| class | comparisons |
|---|---:|
| operating-point robust (same reading, \|change\| < 2 pp) | 12 |
| quantitatively sensitive, same reading | 6 |
| **registered reading changes** | **0** |

**Operating-point choice changes no registered reading anywhere in the
study.** Largest movement **12.77 pp** (Gemma-3n-E2B-it f0 B-second under the
B2 runner-up, −11.19 → +1.58), reading `L3c` on both sides; the sign flips on
2 of 18.

**Separate numerical from inferential instability explicitly**, because they
point opposite ways here. The *selection rule* is genuinely unstable — that is
why every frame carries the status. The *inference* is not — no reading moves.
And on the one positive cell the runner-up moves Δ_R by only **0.88 pp**
(+12.64 → +13.52); on the within-frame simultaneous interval both read `L3a`.
It is the **joint** cross-frame interval — the registered decision interval,
widened by sharing one bootstrap draw across the model's three entering
frames — that spans +10 pp and yields `INDETERMINATE@0.10`. Write that
plainly: the excess is stable to the operating point and to the estimator, and
it is the registered multiplicity correction, not noise, that stops short of
certifying it.

*Source: `runner_up_sensitivity.csv`.*

### 3.8 SPECTRUM — the second arm

#### Read this before writing a word about the x axis

**ι is a chance-corrected stand-alone *compliance*, not a difficulty score.**
It is `(solo − chance)/(1 − chance)` — "the share of the achievable
improvement over chance that stating the constraint delivers". Therefore
**higher ι means the companion is followed more often, i.e. an EASIER
companion**; lower ι is harder. The protocol calls ι "the difficulty
coordinate" because it *indexes* difficulty, but it runs the other way, and
the protocol's own spectrum slots agree (`SPECTRUM_LOW`/`below` sits at low ι).

**Do not label any axis "difficulty" and do not plot `1 − ι`**: the registered
slope β is defined on the ι scale. Label it "companion stand-alone compliance
ι" with the cue `← harder · easier →`.

#### Does companion difficulty predict B's loss?

Over the 28 SPECTRUM conditions the slope's registered simultaneous interval
**excludes zero above it in 19**, **below it in 4**, and **spans zero in 5**
(the point estimate is positive in 22).

**On a compliance axis, β > 0 means B's loss is LARGER beside an EASIER
companion.** So the majority direction runs *against* the premise the arm was
designed on. The four clearly negative conditions — Qwen3-4B f0 B-first,
Gemma-3n-E2B-it f2 B-second, and **both orders of Gemma-3n-E4B-it f1** — are
where the intuitive direction holds. The pattern appears within families as
well as across them: on Gemma-3n-E2B-it f3 B-second, family MK2 runs +35.0 →
+36.9 → +40.1 pp as ι rises 0.57 → 0.69 → 0.91. Largest slope +0.297 (E4B f3
B-second). β even changes sign across frames of one model: E4B B-first gives
+0.010 (f0), **−0.042** (f1), +0.095 (f3).

**Do not restate the design's premise as a finding.** Report the direction as
measured. Claim no mechanism: the design reads no model internals, and ι and
the loss are measured on the same blocks.

#### Where does A lie relative to the fitted expectation?

δ_difficulty = observed D(B←A) − [α̂_family + β̂·ι_A], with family-aware
intercepts.

- **Negative in 25 of 28 conditions**: A costs B *less* than the relation
  predicts for a companion of its measured stand-alone compliance.
- **17 conditions read `L3e`** — the residual lies wholly inside the ±10 pp
  registered equivalence region.
- **1 condition reads `L3d`** — Qwen3-4B-Instruct-2507 f1 B-first,
  δ = **+1.60 pp**, joint CI [+0.05, +3.15]. The only registered direction
  claim in the arm, and it is +1.6 pp.
- **10 conditions reach no registered level**, all strongly negative, to
  **−28.69 pp**. The grammar is one-sided — `L3d` needs the interval above
  zero, `L3e` needs it inside ±10 pp — so a large *negative* residual has no
  level to reach. **Report these by point estimate and interval and say the
  grammar has no level for them. Do not call them nulls.**
- The support check holds on **28 of 28**: no condition extrapolates.

#### The disagreement that should be in the Discussion

On **Gemma-3n-E4B-it f1 B-second** — the one condition where the LOCAL arm
puts A above its matched references at +12.64 pp — the SPECTRUM arm gives
δ_difficulty = **−11.49 pp**, joint CI [−14.40, −8.58]. The two arms are not
contradictory in the logical sense (they name different comparison classes),
but they point opposite ways by 24 pp on the same rows, and the raw points show
why: A's loss is +43.29 pp against a spectrum running +35.81 to +75.68 (B's
compliance falls from 0.768 alone to 0.335 beside A, against 0.410 beside the
gentlest companion and **0.011** beside the harshest). The LOCAL triple is
MK3:3 (+37.66), **XC3:9 (+7.85)** and MK5:6 (+46.45) — its mean is dragged
down by one sentence-count companion whose effect on B is less than a quarter
of the gentlest companion on the spectrum. **A looks harmful in this condition
not because it is harsh but because one of its three matched references is
unusually gentle.**

#### Difficulty versus companion identity

Neither arm licenses "difficulty explains interference". SPECTRUM says A is
close to what its *compliance* predicts in 17 of 28 conditions and below it in
25 — but the fit carries **family-aware intercepts**, conceding by
construction that family matters at fixed ι, and §3.6 shows how much. The
defensible statement: after conditioning on stand-alone compliance A is
unexceptional, and what the relation does not absorb tracks the companion's
*family*, not A's identity.

*Sources: `spectrum_results.csv`, `spectrum_points.csv`.*

### 3.9 Table 2 — the robustness ledger

Build this table; no prior version of the paper has it and a referee will look
for it.

| analysis | largest movement | most affected condition | headline survives? | qualification |
|---|---|---|:-:|---|
| Reference-set sensitivity (F_REFSENS) | 26.46 pp spread | Gemma-3n-E2B-it f0 B-second | **on 22 of 24** | verdict changes on E4B f0 and f1, B second |
| Operating point (F_RUNNER_UP) | 12.77 pp | Gemma-3n-E2B-it f0 B-second | **yes, everywhere** | none |
| Graded-compliance recoding (F5) | −15.76 pp | Gemma-3n-E4B-it f1 B-second | **yes** | **the one positive Δ_R falls +12.64 → +7.07 pp**, inside the bound |
| Vacuous-pass recoding (F5) | −11.45 pp | 2507 f3 B-first (−0.88 → −12.33) | **yes** | §17.4 withholds levels on E4B f1 B-second |
| F6 vacuity gate | bounds [−15.15, −9.51] pp | 2507 f3 B-first | **yes** | binds on 6 of 24; 7 carry `VACUITY_DEPENDENT` |
| §23 projection audit | 0.867 absolute error | Qwen3-4B f0, cell B+S2 (projected 0.932, realised 0.065) | **yes** (licenses nothing) | **370 of 370** audited composed cells outside the 0.05 allowance, median \|error\| **0.264** |
| Order contrasts (F11) | −46.84 pp | Gemma-3n-E4B-it f0, `Ord_B` | **yes** | position dominates companion identity |
| Cross-configuration consistency (L4a) | — | Gemma-3n-E4B-it f1 | **yes** | Δ_R agrees on 11 of 12 frames; δ_difficulty on 5 of 12 |
| Identification ledger (§34 D6) | — | — | **yes** | 1,512 `ESTIMATED`, 134 `NOT_ASKED`, **0 `NOT_IDENTIFIED`** |

**Two of these touch the one positive condition and both weaken it**: the
graded recoding cuts it 44%, and §17.4's both-bounds rule withholds its levels
independently of the interval. With `REFERENCE_HETEROGENEOUS` and
`A_GENERAL_NOT_EXCLUDED` that is four registered qualifications on one cell.
Write all four in the paragraph that reports it.

### 3.10 Methodology validation — one page, no more

This was the *whole* of the pre-confirmatory paper. It is now a supporting
section whose job is to establish that the pipeline that chose the operating
points and reference sets is stable enough in its **verdicts** for the
confirmatory contrast to mean something — while being explicit that the
**objects** it selects are not.

**Keep three robustness concepts apart and never substitute one for another.**
**A. Re-execution**: same topics, same seeds, run again → decoding
nondeterminism. **B. Topic resampling**: a fresh area-stratified partition of
the 216 pre-freeze topics into the same roles → topic-sampling sensitivity.
**C. Topic bootstrap**: resampling stored calibration rows → conditional
resampling stability. The confirmatory bootstrap and the operating-point
stability statistic are both C.

- **Frame-conditioned forwarding changes what is identifiable.** At equal
  budget on identical rows, the frame's own candidate set yields at least as
  many admissible families as the frame-pooled set on **13 of 14** supported
  frames, and on **2** the admissibility verdict differs (2507 f3: 5 families
  / 2 backups against 4 / 1; Gemma-3n-E4B-it f0: 7 / 2 against 4 / 1). One
  model is eligible because of it.
- **State the 2507 claim in its corrected form.** A control run re-executed
  the *pooled* design itself at its own frozen commit and gave 5/2 on 2507 f3.
  Across every observation the pooled set clears the survival minimum in **2
  of 5** and the frame-aware set in **3 of 3**. So: *the pooled rule is
  marginal there, not reliably failing.* The paired comparisons on identical
  rows remain the strongest evidence, and E4B f0 (7/2 against 4/1 in both
  successor runs) is untouched.

| measure | A (decoding) | B (topics) |
|---|---|---|
| LOCAL verdicts agreeing | 16 of 16 | **13 of 14** |
| SPECTRUM identification agreeing | — | 13 of 14 |
| operating points agreeing | — | 11 of 14 |
| model eligibility agreeing | 4 of 4 | **3 of 4** |
| forwarded-set Jaccard | 0.59–1.00 | 0.51–0.77 |
| core reference triple identical | 5 of 16 | 3 of 14 |
| admissible backups identical | 8 of 16 | 3 of 14 |

- **The one eligibility disagreement.** Qwen3-4B-Instruct-2507 frame 1 carries
  6 LOCAL-valid families and 2 backups in the bound pilot and **4 and 1**
  under a resampled partition, below the minimum — so the model would **not**
  have been eligible. Sound on both sides (supported at Gate 2 in both, same
  chance basis, ι_A 0.652 against 0.641, complete row accounting). A genuine
  sensitivity, not a defect. Its confirmatory result must travel with this
  sentence.
- **Knife-edge operating points.** Gemma-3n-E2B-it f0 selected n\* = 1, 8 and 3
  across three samples of the same topic pool.
- **Engineering integrity, one short paragraph.** A row-reuse defect (a
  previous run was matched on design identity but not on whether its rows had
  been generated) is fixed and guarded on both the pilot and confirmatory
  paths, with seven regression tests; a scan of 108 backend runs across 9
  roots found no other affected evidence. The four bound pilots sit at two
  commits differing in one constant (a backend wall-clock cap), with 71 of 72
  hashed package files identical and all rule, protocol and document bindings
  identical — audited, so no model was re-run for commit uniformity.

---

## 4. What to do with each part of `neurips-4.pdf`

| section | action | instruction |
|---|---|---|
| **Title** | KEEP BUT REFRAME | Retain "Compared With What?". Suggested: *"Compared With What? A Frame-Conditioned Confirmatory Test of Pair-Specific Instruction Interference"*. |
| **Abstract** | REPLACE | Keep the two-things-change-at-once framing, the verifier-scope sentence and "a pair-specific claim needs an explicitly stated reference class". Delete every number. Use §1's abstract. |
| **§1 Introduction** | KEEP BUT REFRAME | Paragraphs 1–2 ("The comparison that is missing", "Replace the companion instead of removing it") are the best exposition in either manuscript — keep near-verbatim. Rewrite only "What we find, and how far it reaches". Delete "these are development runs". Add one sentence naming the single positive condition. |
| **Contributions** | REPLACE | (i) the frame-conditioned design and estimand; (ii) a preregistered frozen confirmatory test at 384 blocks per frame over 2.35 M generations; (iii) the bounded result on 23 of 24 conditions at measured precision; (iv) the one heterogeneous model and the three registered sensitivities that undercut it; (v) the reference-set sensitivity result. |
| **§2 Related Work** | KEEP | The estimand-gap argument is untouched. |
| **§3 Background** | KEEP | Unchanged. |
| **§4 Method** | MAJOR REWRITE | Lift from `main_v8_1_preconfirm.tex` §4 and Appendix B, then insert §2's three method facts (joint interval, reading grammar, conjunction rule). |
| **§5.1 Claim 1** | KEEP THE ARGUMENT, UPDATE ALL NUMBERS | §3.3 here. Keep the "both instructions improve on Qwen" counterexample — it replicates. |
| **§5.2 Claim 2** | MAJOR REWRITE | Becomes 23 of 24 with a named exception. Of v7's four qualifications: keep the threshold paragraph; update ceiling compression to 8 of 24, all Qwen; keep and strengthen "the references disagree"; **promote "the interval is conditional on those three references" to a result** (§3.5). |
| **§5.3 Claim 3** | KEEP, RE-EXAMPLE | Swap in the E4B f0 B-second example (49.2 vs 57.4, Δ_R −8.18). |
| **NEW §5.4** | CREATE | The SPECTRUM arm (§3.8). |
| **NEW §5.5** | CREATE | The robustness ledger (Table 2). |
| **§6 Discussion** | KEEP BUT REFRAME | Keep "What the matched contrast licenses" and "What it does not license" — both correct and unusually careful. Add: why one positive condition neither overturns nor confirms the bounded result; the LOCAL/SPECTRUM disagreement; the reference-family observation as the open question. |
| **§7 Limitations** | REPLACE, REORDERED | Delete "these are development runs" and the protocol-change-after-outcomes admission — both resolved by the freeze. **Keep the measurement paragraph verbatim**; it is still exactly right. New order: §5 of this prompt. |
| **§8 Conclusion** | KEEP THE SHAPE | New second half: the contrast against a named class is small in 23 of 24 conditions and is not in the twenty-fourth, and which class you name — and under which wording — decides that. |
| **Figure 1** (design schematic) | KEEP, EXTEND | Add the per-frame conditioning strip. |
| **Figure 2** (raw effects) | UPDATE NUMBERS, KEEP FORM | |
| **Figure 3** (Δ_R forest) | REPLACE | Now 24 cells, joint intervals, per frame. |
| **Figure 4** (loss decomposition) | KEEP FORM, RE-EXAMPLE | |
| **Table 1** | REPLACE | §3.1's 24 rows. |
| **Appendix A** | KEEP | |
| **Appendix B** | MAJOR REWRITE | Lift the v8.1 protocol; replace "current status" with §2's provenance block; add the reuse-guard fix and the commit audit. |
| **Appendix C.1** | KEEP AND EXPAND | Full per-reference table. |
| **Appendix C.2** | REPLACE | F5/F6 tables. |
| **Appendix C.3** | KEEP | Note that v8.1 runs no class arm at all, so the class estimand is unavailable *by design* rather than degenerate. |
| **Appendix C.4** | KEEP THE FRAMING | The v8.1 analogues are the §23 projection audit and the F7 reciprocal losses. |
| **NEW Appendix C.5–C.9** | CREATE | F_REFSENS in full; F_RUNNER_UP in full; SPECTRUM in full; the identification ledger; L4a. |
| **Appendix D** | KEEP | |
| **Checklist** | UPDATE | Flip every "no confirmatory result exists" answer; point reproducibility items at the root, commit, preregistration hash and per-model record hashes. |
| **NEW historical appendix** | CREATE | v7's Table 1, clearly labelled superseded development evidence, plus one paragraph on which claims replicate, weaken or fail. Do not delete it. |

**Recommended main-text structure** (do not feel bound by v7's three-claim
Results): §1 Introduction · §2 Related Work · §3 Background · §4 Method ·
§5 Identification and its stability (~1 page) · §6 Results (6.1 composition ·
6.2 the matched-reference contrast · 6.3 the one heterogeneous condition ·
6.4 difficulty is not the explanation · 6.5 what the sensitivities do) ·
§7 Discussion · §8 Limitations · §9 Conclusion.

---

## 5. Figures to commission

Ask the plotting agent for these. Every dataset named is a committed CSV under
`dci1/reports/dci1v8dev/postconfirm/data/`.

**Figure 1 — Composition versus companion identity (visual abstract).**
*Claim*: a large solo-to-pair change can carry almost no companion-specific
signal. *Data*: `raw_vs_reference_loss.csv`. *Panels*: per model × order, a
circle at D(B←A) and a hexagon at D(B←R̄) joined by a bar whose length is Δ_R;
frames as small offsets. *Highlight*: E4B f0 B-second (49.2 → 57.4, Δ_R −8.18)
and Qwen3-4B f0 B-first (−13.5 → −10.9, Δ_R −2.65) as the two regimes.
*De-emphasise*: absolute compliance levels, individual frames.
*Caption takeaway*: "B falls 49 points beside A and 57 points beside its
matched references: almost none of a large composition effect is about A."

**Figure 2 — The frame-conditioned Δ_R(f) forest (primary result).**
*Claim*: 23 of 24 conditions bound the contrast below +10 pp at measured
precision; one does not. *Data*: `primary_delta_by_frame_order.csv`.
*Panels*: one row per model, one line per entering frame, filled marker
B-first and open B-second; vertical rules at 0 and +10; the **joint** interval
as the bar and the within-frame interval as a thin whisker so the multiplicity
cost is visible. *Highlight*: the single `INDETERMINATE@0.10` marker past +10.
*De-emphasise*: hatch the 8 compressed cells. *Caption takeaway*:
"Twenty-three of twenty-four intervals stop short of +10 points; the Qwen
models' frames sit on top of one another, the Gemmas' spread out, and one open
marker sits alone past the threshold."

**Figure 3 — Where the one positive condition comes from (result + sensitivity).**
*Claim*: the only positive contrast rests on one reference of three, and the
choice among admissible triples changes the registered verdict. *Data*:
`reference_sensitivity.csv`, `per_reference_contrasts.csv`. *Panels*: (a) the
nine admissible triples for E4B f1 B-second as a dot plot from −8.63 to +12.64
with the frozen triple starred at the extreme; (b) its three per-reference
contrasts (+5.63, +35.45, −3.16) with intervals; (c) optionally the same for
E4B f0 B-second (−8.18, the minimum, against a maximum of +16.92).
*Highlight*: XC3:9's +35.45 and the frozen triple's extremity.
*De-emphasise*: the 12 reference-robust cells — summarise as a count.
*Caption takeaway*: "The frozen triple is the most harmful of its nine
admissible alternatives; swap one reference and the registered reading
changes."

**Figure 4 — SPECTRUM (second arm).**
*Claim*: after conditioning on stand-alone compliance A is unexceptional —
including in the one condition where the LOCAL arm says otherwise. *Data*:
`spectrum_results.csv`, `spectrum_points.csv`. *Panels*: (a) δ_difficulty with
its joint interval across all 28 conditions, ±10 pp band, colour only on the
`L3d` and no-level cases; (b) the E4B f1 B-second scatter with the fitted
line, A's star at +43.29 and the prediction at +54.78, residual −11.49
annotated. *Highlight*: that panel (b)'s residual points the *opposite* way to
Figure 3's Δ_R. *Axis warning*: label x as **stand-alone compliance ι** with
the cue `← harder · easier →`; do not call it difficulty and do not plot
`1 − ι`. *Caption takeaway*: "In the one condition where A costs B more than
its three matched references, A costs B 11.5 points *less* than companions of
its measured stand-alone compliance predict."

**Appendix figures**: the full 28-panel SPECTRUM grid; all 18 runner-up
comparisons; the A-versus-B methodology-validation stability table; frame and
order detail. Three are already drawn under
`dci1/reports/dci1v8dev/postconfirm/figures/` (`fig1_spectrum_forest`,
`fig2_spectrum_explainer`, `fig3_spectrum_grid`) with a README recording input
hashes and the ι orientation. **Do not reuse the candidate-set turnover plot
in the main text** — its subject is no longer the paper's result.

---

## 6. Claims you may and may not make

| statement | verdict |
|---|---|
| **"A is not unusually harmful."** | **Never write it.** The strong refutation verdict is unreachable by construction (`NEAR_FORM_UNAVAILABLE`), and one condition reads `INDETERMINATE@0.10`. |
| **"Pair-specific interference is absent."** | **Never write it.** A bounded contrast against a named class is not an absence claim, and 18 of 24 cells carry `A_GENERAL_NOT_EXCLUDED`. |
| **"Large composition effects are generic."** | Licensed: "composition effects are large and are not explained by the companion's identity within the named class." "Generic" implies a mechanism the design cannot see. |
| **"Difficulty explains interference."** | **Not licensed.** The fit carries family-aware intercepts, i.e. it concedes that family matters at fixed ι. |
| **"Difficulty does not fully explain interference."** | Licensed as: "after conditioning on stand-alone compliance A is unexceptional; what the relation does not absorb tracks the companion's family." Attach no interval to the family grouping. |
| **"Reference identity matters."** | Licensed: "the choice among admissible matched triples moves Δ_R by up to 26 pp and changes the registered reading on two of twenty-four conditions." Do not imply the frozen triple is wrong. |
| **"Wording changes the control set."** | Licensed **as methodology validation**: 2 of 14 admissibility verdicts, 1 model's eligibility. Not as a confirmatory finding. |
| **"The result generalises across models."** | **Not licensed.** Four checkpoints in two families, reported per model, never pooled, and one disagrees with itself across frames. |
| **"The result is robust to reference selection."** | **False as stated.** Two of 24 registered verdicts change. |
| **"The result is robust to operating-point choice."** | Licensed: "the runner-up operating point changes no registered reading" — with the qualification that every frame is `OPERATING_POINT_UNSTABLE` and the robustness is against the registered runner-up, not the whole grid. |
| **"Harder companions cost B more."** | **Contradicted in 19 of 28 conditions.** On a compliance axis the majority slope says the opposite. |
| **"The effect is equivalent to zero."** | Not licensed. `L3c` bounds an excess above +10 pp; it does not certify equivalence to zero, and 11 of 24 intervals in fact exclude zero on the *negative* side. |
| Mechanism, internals, human-judged compliance, answer quality | **Never.** The design reads no model internals, no human labelling was performed, and no quantity measures answer quality. |

**Limitations to state, in this order**: reference-set sensitivity (2 verdicts
change) · 2507's sample-sensitive eligibility · §26 `NOT_MET` on both Qwen
models (on D(A←B)'s precision, not Δ_R's) · the §23 projection audit outside
its allowance on every audited composed cell · every frame
`OPERATING_POINT_UNSTABLE` · no near-form arm, so `NEAR_FORM_UNAVAILABLE` ·
no class arm · ceiling compression on 8 of 24 · Ξ unresolved on 18 of 24 ·
verifier-defined compliance with no human labelling and no answer-quality
measure · scope (one focal instruction, one genre, three references per
model × frame, four checkpoints, two positions, never pooled) · no mechanism ·
four sentence templates, not a sample of phrasings.

---

## 7. Standing rules while you write

1. Confirmatory v8.1 evidence dominates. v7 numbers live only in the
   historical appendix.
2. Keep **PRIMARY_CONFIRMATORY**, **REGISTERED_SENSITIVITY**,
   **REGISTERED_DESCRIPTIVE**, **METHODOLOGY_VALIDATION** and
   **HISTORICAL_DEVELOPMENT** visibly distinct. A reader must always know
   which they are looking at.
3. **Invent no pooled estimand** across wording frames or across models.
4. **Never convert a bounded result into a claim of zero effect or
   equivalence.** `L3c` bounds an excess above +10 pp and nothing more.
5. **Treat disagreement and fragility as findings**, not as nuisances. The
   heterogeneous model, the two verdict-changing cells, the LOCAL/SPECTRUM
   disagreement and the `NOT_MET` criterion are among the paper's most
   valuable content.
6. Report every number to the precision given here, in **percentage points**,
   and say which interval it is (joint, within-frame, or marginal).
7. Where you need a number this prompt does not contain, say so rather than
   estimating it.
