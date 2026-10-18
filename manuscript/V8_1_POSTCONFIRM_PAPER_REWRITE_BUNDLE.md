# DCI-1 v8.1 — post-confirmatory paper-rewrite bundle

*Written 2026-09-10, after the frozen registered confirmatory analysis and
final report ran once on the complete confirmatory row set. Every number
below names the signed artifact it came from. Nothing here re-decides a
registered rule.*

---

# 1. Executive summary

The frozen confirmatory experiment ran to completion on four models,
2,353,152 generated rows, 12 entering LOCAL frames and 14 entering SPECTRUM
frames, at 384 topic blocks per frame. The registered analysis and the
registered final report both returned `PASS` for every model.

**The one-sentence result.** Against the three same-form companions matched
to it on frame-conditioned stand-alone difficulty, the simultaneous upper
bound on how much more the focal instruction A costs compliance with B stops
below the registered +10 pp margin in 23 of the 24 entering
model × frame × prompt-order cells — and in the twenty-fourth,
Gemma-3n-E4B-it under frame 1 with B stated second, A costs B **+12.6 pp**
more, an excess the registered rule declines to certify and that the
registered sensitivity analyses substantially undercut.

**What changed relative to the superseded v7 development paper.** v7 pooled
the four wording frames, ran eight configurations, and found every
simultaneous upper bound below +3.9 pp. Conditioning on wording splits those
eight configurations into twenty-four and reveals a cell that pooling could
not have shown: the widest between-frame range within one model × order is
**20.8 pp** (Gemma-3n-E4B-it, B second: −8.18, +12.64, −4.29 across frames
0, 1, 3), which is larger than any single Δ_R the v7 design reported.
Frames are conditions, and on this model averaging them would have hidden
the only positive result in the study.

**The seven headline facts.**

1. Δ_R over the 24 entering cells runs from **−11.19 pp to +12.64 pp**;
   18 of 24 point estimates are negative, and 11 of the 24 joint intervals
   lie wholly below zero — the references cost B more than A does.
2. **23 of 24** joint decision intervals stop below +10 pp (registered
   reading `L3c`); the twenty-fourth spans it (`INDETERMINATE@0.10`).
3. The registered precision precondition (joint half-width ≤ 5 pp) is met in
   **24 of 24** cells; realised half-widths are 1.05–3.24 pp. The smallness
   is measured, not underpowered.
4. Raw composition remains large: D(B←A) runs −13.5 to **+49.2 pp**, D(A←B)
   runs −36.1 to **+54.5 pp**, and the asymmetry Λ runs −49.8 to +52.3 pp.
   The ratio |D(B←A)| / |Δ_R| has a median of 3.8 and a maximum of 88.6:
   composition typically moves compliance about four times as far as
   companion identity does, and sometimes far more.
5. Seven of eight model × order configurations return
   `LOCAL_EQUIVALENT_SAME_FORM_ONLY`. The eighth, Gemma-3n-E4B-it with B
   second, returns **`FRAME_HETEROGENEOUS`** — a verdict, not a failure.
6. Reference-set choice changes the registered reading on **2 of 24** cells,
   both on Gemma-3n-E4B-it. Operating-point choice changes it on **none**.
7. The SPECTRUM arm points the other way on the one positive cell: relative
   to companions of the same measured difficulty, A on Gemma-3n-E4B-it frame
   1 with B second is **11.5 pp *less* harmful than predicted**
   (δ_difficulty = −11.49 pp, joint CI [−14.40, −8.58]).

**The single most important qualification.** The one cell that breaks the
pattern is the most reference-sensitive cell in the study. Its three
per-reference contrasts are +5.63, **+35.45** and −3.16 pp — they disagree
in sign with intervals excluding zero — and across the nine admissible
triples of its five frozen families Δ_R runs from **−8.63 to +12.64 pp**.
The frozen triple is the single most harmful of the nine. The registered
rule decides on the frozen triple and the result stands as reported; but the
paper cannot describe that cell as evidence of pair-specific interference
without saying that one of its three references — a sentence-count companion
matched to A on difficulty but four times gentler on B — carries it.

---

# 2. Provenance and confirmatory-analysis integrity

## 2.1 The analysis boundary, and that it held

The registered analysis stage `CONFIRMATORY_ANALYSIS` is the first stage
permitted to read a composed outcome. Before running it, this session
verified the confirmatory root, the freeze, the membership lock, the bound
analysis code and the readiness record. The stage status for all four models
read `stage_reached: CONFIRMATORY_GENERATION, next_stage:
CONFIRMATORY_ANALYSIS` immediately before the first run, so no protected
outcome had been read, summarised, or computed from under this protocol.
No composed row, no informal Δ_R, and no individual response was inspected
first. The first scientific reading of the confirmatory data is the one the
frozen code produced.

## 2.2 Identities

| what | value |
|---|---|
| confirmatory root | `dci1/evidence/dci1v8p1-confirm` |
| bound commit (every stage record) | `034fc7214762b6848d5d904b14fd82b317830667` |
| registration manifest commit | `c0b52ca203b7179b90bbbf088a6952fcc2b8a805` |
| confirm manifest record hash | `8cfa20827b3f46fc49fea7444c00babf430eed494f5261c9df487c7a5a9b80a3` |
| preregistration | `dci1/docs/DCI1_preregistration_v8.1.md`, hash `d3552f9f47e3f00800622f033cfad579dcd6085b1068f0bcb35c643e8bb1908d` |
| rules hash | `3d9064ea0f99cc9b24d64af1c73f0d8f7d5f28cada890a322bc760e75f213c0f` |
| membership lock | `dci1/reports/dci1v8dev/confirmatory_membership.json`, hash `31af521c21d5cee4fcc99e7f9267d0a9950347683db03e82b6b4d61cd8695b3c` |
| verifier hash | `ea885b0db67e3c7c7c75398290c6cce7f57f7e74422d530f611f52470d4ad433` |
| wording hash | `fe3b5be15759af1ca1301d413d8145f60d04723dab3fa48aa24148ee9956a0c2` |
| topic split hash | `c10f17bc5846e1858705af3c8daa21c450b1c63f00618ce0d414181fc8861f10` (v4r2's split seed, carried unchanged, §6.2) |
| protocol version | `8.1-confirmatory` |
| analysis code | 7 modules under `dci1v7/analysis/`, hashes bound at registration and re-verified byte-for-byte before the run |
| bootstrap resamples | 10,000 (`C.BOOTSTRAP_RESAMPLES`) |

Topic split, from the manifest: prescreen 24, calibration A 96, calibration
B 96, composed 24, confirmatory **384**, sequestered 0, over 12 areas.

Model revisions, from the manifest: `google/gemma-3n-E2B-it`
`5e092ebca197cdcd8d8b195040accf22693501bc`; `google/gemma-3n-E4B-it`
`c1221e9c62e34a43ab7ffacd1be0ea71f126ef10`; `Qwen/Qwen3-4B`
`1cfa9a7208912126459214e8b04321603b3df60c`; `Qwen/Qwen3-4B-Instruct-2507`
`cdbee75f17c01a7cc42f958dc650907174af0554`. Decoding: stochastic, T = 0.7,
top-p 0.9, top-k 50, `NO_THINKING`, engine seed 20260819, no quantisation,
pinned backend, TP = 1 lanes.

## 2.3 Per-model records

| model | rows planned = produced | freeze hash | generation hash | analysis hash | final report hash | analysis recorded at |
|---|---:|---|---|---|---|---|
| Qwen3-4B | 715,776 | `7902b05f12a2bb60` | `287e507ed9b1dc86` | `5591cb46c64c127a` | `af7138f534420738` | 2026-09-10T13:54:01Z |
| Qwen3-4B-Instruct-2507 | 344,064 | `4d72e728af137746` | `a98dc7aa45f75ed0` | `31f1b46be5e6416e` | `3dfab3cd8904acfa` | 2026-09-10T13:49:50Z |
| Gemma-3n-E2B-it | 623,616 | `33595b8078525a12` | `117e95aa9a8b2ae1` | `5edcd5730bc4c031` | `2fad8b4cab4cbaaa` | 2026-09-10T13:53:39Z |
| Gemma-3n-E4B-it | 669,696 | `70bcb5da77f2cbca` | `e4dd54ff8575dcee` | `e90e0f7d6606bd8d` | `c6666bdbabcdd2ee` | 2026-09-10T13:56:09Z |

Total 2,353,152 rows. Every generation record carries
`completeness.complete = true` with zero missing, zero duplicate and zero
unexpected `(block, cell, draw)` identities. The analysis stage re-counted
the rows on disk against the generation record before computing.

## 2.4 The command that was run

```
cd /home/cnm13ryan/git/dci-v8-topicrep/dci1        # clean worktree at 034fc72
.venv/bin/python -m dci1v8dev.confirm.cli run \
    --stage CONFIRMATORY_ANALYSIS --model <key> \
    --root <repo>/dci1/evidence/dci1v8p1-confirm \
    --environment "rocm7.2/vllm0.15.1"
# then, identically, --stage FINAL_REPORT
```

CPU only; 4–8 minutes and ≈11 GB of RAM per model. All eight invocations
exited 0 and wrote `outcome: PASS`. Logs are under
`dci1/evidence/dci1v8p1-confirm/logs/<model>.{ANALYSIS,FINAL_REPORT}.out`.
Nothing in the frozen analysis code was modified, and no environment
intervention was needed.

## 2.5 What the freeze declares as deviations

Two, both carried from the freeze record and both consequential for wording:

1. **No masked-analysis / unmasking stage.** v7 masks companion labels to
   protect analyst decisions taken between generation and the report; this
   layer has no such decision point — `CONFIRMATORY_ANALYSIS` is frozen code
   that runs once, unattended, on the complete row set. Recorded as a
   deviation, not as an equivalence.
2. **No near-form arm and no class arm.** v8's pilot selected no near-form
   controls and no class companion, so Δ_near and Δ_broad are unavailable
   and §34 D18's *strong* L3c refutation verdict is unreachable **by
   construction**. An L3c-level reading is therefore reported with the
   disposition `NEAR_FORM_UNAVAILABLE` and the model verdict is the narrower
   `LOCAL_EQUIVALENT_SAME_FORM_ONLY`. **The paper may not write "A is not
   unusually harmful"; it may write "A costs B less than 10 pp more than
   same-form, exact-count companions matched on frame-conditioned
   difficulty."** L3c bounds the excess below the +10 pp margin; it does not
   show the excess is zero, so "no more than" without the margin is too strong.
   (Wording corrected 2026-09-13; earlier versions of this bundle licensed the
   unqualified "no more than".)

---

# 3. Frozen design and membership

Four wording frames f ∈ {0, 1, 2, 3}. A frame is part of the experimental
condition: the operating points n\*(f) and m\*(f), the difficulty coordinate
ι_A(f), the admissibility test and the reference set are all conditioned on
f, and Gates 2 and 3, the analysis and the report are all per frame.

| model | LOCAL frames | SPECTRUM frames | joint family size | blocks/frame | draws | rows |
|---|---|---|---:|---:|---:|---:|
| Qwen3-4B | 0, 1, 2, 3 | 0, 1, 2, 3 | 24 | 384 | 8 | 715,776 |
| Qwen3-4B-Instruct-2507 | 1, 3 | 1, 3 | 12 | 384 | 8 | 344,064 |
| Gemma-3n-E2B-it | 0, 1, 3 | 0, 1, 2, 3 | 22 | 384 | 8 | 623,616 |
| Gemma-3n-E4B-it | 0, 1, 3 | 0, 1, 2, 3 | 22 | 384 | 8 | 669,696 |

12 LOCAL frames, 14 SPECTRUM frames, 24 LOCAL cells once both prompt orders
are counted, 28 SPECTRUM cells.

**Multiplicity, as registered.** Per (model, frame, configuration), family
F1's six members share a studentised maximum-modulus critical value from a
block bootstrap. Per (model, configuration), the **JOINT** family collects
every F1 member of every entering frame and takes its critical value from a
topic-level block bootstrap with **one draw shared across frames** (the same
topic underlies each frame's block). **The decision interval of every primary
claim is the joint one.** A model-level LOCAL claim is the conjunction over
entering frames (intersection–union, no further adjustment); there is no
at-least-one-frame claim. Realised joint critical values are 2.798–3.017.

**Registered thresholds.** Generic Δ_R threshold 0.10; pair-specific
threshold 0.25; equivalence region 0.10; SESOI 0.10; precision precondition
half-width ≤ 0.05.

**Registered reading grammar for Δ_R** (`claims.delta_r_reading`), on the
decision interval:

- half-width > 5 pp → `INSUFFICIENT_PRECISION`, no level;
- lower > +10 pp → **L3a** (and L3b if lower > +25 pp);
- upper < +10 pp → **L3c**, the bounded reading;
- otherwise → `INDETERMINATE@0.10`.

The direction is read separately: lower > 0 is `A_HARMS_MORE`, upper < 0 is
`A_COMPARATIVELY_BETTER`, else `DIRECTION_UNRESOLVED`.

**Operating-point stability.** Every entering frame of every model carries
status `OPERATING_POINT_UNSTABLE` (the frozen coordinate was re-selected on
fewer than 2/3 of 2,000 topic resamples). The frozen point is never
replaced; the registered response is the runner-up arm, which carries the
contrast at the alternative severity on the *same* blocks. Runner-up arms
were generated on **7 of the 12 LOCAL frames**: Qwen3-4B's four (slot A2
each), Gemma-3n-E2B-it f0 and Gemma-3n-E4B-it f0 (both A2 and B2) and
Gemma-3n-E4B-it f1 (A2) — 18 comparisons once both prompt orders count.

---

# 4. Primary confirmatory results

**Every magnitude below is in percentage points of B-compliance. Δ_R is
mean reference loss minus focal loss: positive means B fares worse beside A
than beside the three references.** The decision interval is the JOINT
cross-frame simultaneous interval, as registered — never the marginal one.

### T1. Primary confirmatory matrix

| model | f | order | n\*(f) | m\*(f) | ι_A(f) | R1 / R2 / R3 | Δ_R (pp) | SE | joint 95% CI (pp) | half-width | ≤5 pp | registered reading | direction | qualifiers |
|---|---:|---|---:|---:|---:|---|---:|---:|---|---:|:-:|---|---|---|
| Qwen3-4B | 0 | B first | 6 | 12 | 0.674 | XC3:10 / MK1:4 / MK6:6 | **-2.65** | 0.69 | [-4.73, -0.56] | 2.09 | yes | L3c | A_COMPARATIVELY_BETTER | VACUITY_DEPENDENT |
| Qwen3-4B | 0 | B second | 6 | 12 | 0.674 | XC3:10 / MK1:4 / MK6:6 | **-5.54** | 0.91 | [-8.31, -2.78] | 2.76 | yes | L3c | A_COMPARATIVELY_BETTER | — |
| Qwen3-4B | 1 | B first | 7 | 12 | 0.608 | MK7:2 / XC3:9 / MK2:7 | **-1.20** | 0.73 | [-3.41, +1.00] | 2.20 | yes | L3c | DIRECTION_UNRESOLVED | — |
| Qwen3-4B | 1 | B second | 7 | 12 | 0.608 | MK7:2 / XC3:9 / MK2:7 | **-2.93** | 0.90 | [-5.67, -0.19] | 2.74 | yes | L3c | A_COMPARATIVELY_BETTER | — |
| Qwen3-4B | 2 | B first | 3 | 12 | 0.673 | MK7:2 / MK1:6 / MK6:5 | **-0.76** | 0.66 | [-2.71, +1.19] | 1.95 | yes | L3c | DIRECTION_UNRESOLVED | — |
| Qwen3-4B | 2 | B second | 3 | 12 | 0.673 | MK7:2 / MK1:6 / MK6:5 | **-3.49** | 1.07 | [-6.70, -0.29] | 3.20 | yes | L3c | A_COMPARATIVELY_BETTER | — |
| Qwen3-4B | 3 | B first | 5 | 13 | 0.702 | XC3:8 / MK2:5 / MK7:2 | **+0.10** | 0.35 | [-0.95, +1.15] | 1.05 | yes | L3c | DIRECTION_UNRESOLVED | VACUITY_DEPENDENT |
| Qwen3-4B | 3 | B second | 5 | 13 | 0.702 | XC3:8 / MK2:5 / MK7:2 | **-1.02** | 0.66 | [-2.99, +0.95] | 1.97 | yes | L3c | DIRECTION_UNRESOLVED | — |
| Qwen3-4B-Instruct-2507 | 1 | B first | 6 | 10 | 0.652 | MK2:8 / MK5:6 / MK3:2 | **+1.50** | 0.58 | [-0.13, +3.12] | 1.63 | yes | L3c | DIRECTION_UNRESOLVED | VACUITY_DEPENDENT |
| Qwen3-4B-Instruct-2507 | 1 | B second | 6 | 10 | 0.652 | MK2:8 / MK5:6 / MK3:2 | **-1.00** | 0.98 | [-3.74, +1.75] | 2.75 | yes | L3c | DIRECTION_UNRESOLVED | VACUITY_DEPENDENT |
| Qwen3-4B-Instruct-2507 | 3 | B first | 6 | 12 | 0.673 | MK6:10 / MK8:3 / MK7:6 | **-0.88** | 0.65 | [-2.68, +0.92] | 1.80 | yes | L3c | DIRECTION_UNRESOLVED | VACUITY_DEPENDENT |
| Qwen3-4B-Instruct-2507 | 3 | B second | 6 | 12 | 0.673 | MK6:10 / MK8:3 / MK7:6 | **-2.43** | 0.72 | [-4.43, -0.43] | 2.00 | yes | L3c | A_COMPARATIVELY_BETTER | VACUITY_DEPENDENT |
| Gemma-3n-E2B-it | 0 | B first | 8 | 8 | 0.642 | MK4:1 / MK2:6 / XC3:8 | **-0.43** | 0.85 | [-2.97, +2.10] | 2.54 | yes | L3c | DIRECTION_UNRESOLVED | — |
| Gemma-3n-E2B-it | 0 | B second | 8 | 8 | 0.642 | MK4:1 / MK2:6 / XC3:8 | **-11.19** | 1.08 | [-14.43, -7.95] | 3.24 | yes | L3c | A_COMPARATIVELY_BETTER | REFERENCE_HETEROGENEOUS |
| Gemma-3n-E2B-it | 1 | B first | 3 | 10 | 0.635 | MK2:5 / XC3:9 / MK5:8 | **+1.41** | 0.86 | [-1.11, +3.93] | 2.52 | yes | L3c | DIRECTION_UNRESOLVED | — |
| Gemma-3n-E2B-it | 1 | B second | 3 | 10 | 0.635 | MK2:5 / XC3:9 / MK5:8 | **-2.99** | 0.99 | [-5.93, -0.06] | 2.94 | yes | L3c | A_COMPARATIVELY_BETTER | REFERENCE_HETEROGENEOUS |
| Gemma-3n-E2B-it | 3 | B first | 7 | 11 | 0.686 | MK6:8 / MK8:3 / MK2:3 | **-6.93** | 0.76 | [-9.20, -4.67] | 2.26 | yes | L3c | A_COMPARATIVELY_BETTER | — |
| Gemma-3n-E2B-it | 3 | B second | 7 | 11 | 0.686 | MK6:8 / MK8:3 / MK2:3 | **-10.03** | 1.06 | [-13.08, -6.97] | 3.05 | yes | L3c | A_COMPARATIVELY_BETTER | — |
| Gemma-3n-E4B-it | 0 | B first | 6 | 9 | 0.745 | MK2:6 / MK1:5 / MK4:8 | **-2.21** | 0.87 | [-4.84, +0.41] | 2.62 | yes | L3c | DIRECTION_UNRESOLVED | — |
| Gemma-3n-E4B-it | 0 | B second | 6 | 9 | 0.745 | MK2:6 / MK1:5 / MK4:8 | **-8.18** | 0.89 | [-10.78, -5.58] | 2.60 | yes | L3c | A_COMPARATIVELY_BETTER | — |
| Gemma-3n-E4B-it | 1 | B first | 6 | 9 | 0.711 | MK3:3 / XC3:9 / MK5:6 | **+2.15** | 0.84 | [-0.37, +4.66] | 2.51 | yes | L3c | DIRECTION_UNRESOLVED | — |
| Gemma-3n-E4B-it | 1 | B second | 6 | 9 | 0.711 | MK3:3 / XC3:9 / MK5:6 | **+12.64** | 1.02 | [+9.62, +15.66] | 3.02 | yes | INDETERMINATE@0.10 | A_HARMS_MORE | REFERENCE_HETEROGENEOUS, VACUITY_DEPENDENT |
| Gemma-3n-E4B-it | 3 | B first | 8 | 10 | 0.688 | MK2:6 / MK1:5 / MK3:1 | **+0.76** | 0.79 | [-1.61, +3.13] | 2.37 | yes | L3c | DIRECTION_UNRESOLVED | — |
| Gemma-3n-E4B-it | 3 | B second | 8 | 10 | 0.688 | MK2:6 / MK1:5 / MK3:1 | **-4.29** | 0.99 | [-7.21, -1.36] | 2.93 | yes | L3c | A_COMPARATIVELY_BETTER | — |

## 4.1 What the primary matrix says

- **Δ_R range −11.19 to +12.64 pp.** 18 of 24 negative, 6 positive.
- **Precision: 24 of 24.** Joint half-widths 1.05–3.24 pp against the 5 pp
  precondition. The design measured what it registered.
- **23 of 24 read `L3c`**: the joint upper bound stops below +10 pp.
- **One cell reads `INDETERMINATE@0.10`**: Gemma-3n-E4B-it, f1, B second,
  Δ_R = +12.64, joint CI [+9.62, +15.66]. The lower bound sits 0.4 pp below
  the threshold, so the registered rule certifies neither an excess above
  +10 pp nor a bound below it.
- **Direction resolved in 12 cells.** `A_COMPARATIVELY_BETTER` in 11 (the
  joint interval lies wholly below zero: the references cost B more than A);
  `A_HARMS_MORE` in 1 (the cell above); `DIRECTION_UNRESOLVED` in 12.
- **`beyond_sesoi` is false in every one of the 24 cells**, including the
  positive one. No cell resolves a Δ_R excess beyond the 10 pp
  smallest-effect-of-interest.

## 4.2 The registered readings, stated exactly

| what the paper may write | licensed by |
|---|---|
| "the interval stops below +10 pp" (23 cells) | `L3c` on the joint interval |
| "the references cost B more than A does" (11 cells) | `A_COMPARATIVELY_BETTER`, interval wholly below zero |
| "the registered rule certifies neither an excess above +10 pp nor a bound below it" (1 cell) | `INDETERMINATE@0.10` |
| "no configuration resolves an excess beyond the smallest effect of interest" (24 cells) | `beyond_sesoi = false` throughout |

Wording that is **not** licensed anywhere in this study:

- "A is not unusually harmful" — the strong L3c verdict is unreachable by
  construction (`NEAR_FORM_UNAVAILABLE`), so no cell licenses it.
- "pair-specific interference is absent" — a bounded contrast against a
  named class is not an absence claim.
- "the effect is equivalent to zero" — `L3c` bounds an excess above +10 pp,
  it does not certify equivalence to zero; 11 of the 24 intervals in fact
  exclude zero on the *negative* side.
- Any mechanism statement. The design reads no model internals.
- Any statement about human-judged compliance or answer quality.

## 4.3 The two registered qualifications carried on the readings

`A_GENERAL_NOT_EXCLUDED` (the Ξ gate) appears on **18** of the 24 cells: the
excess is not distinguishable from A being generally disruptive as a
companion rather than specifically harmful to B.

`COMPOSED_CONTRAST_RANGE_COMPRESSED` (the §13.14 boundary reading) appears
on **8** cells, every one of them on a Qwen model (Qwen3-4B f0/f1/f2 with B
first and f3 in both orders; Qwen3-4B-Instruct-2507 f1 with B first and f3 in
both orders) — the arms'
own compliance levels arithmetically restrict how large Δ_R could have been.
These are the v8.1 analogue of v7's daggered cells and must be marked in any
figure.

`REFERENCE_HETEROGENEOUS` appears on **3** cells and `VACUITY_DEPENDENT` on
**7**; both are read in §7 and §11 below.

---

# 5. Model-level registered readings



The model-level verdict is the **conjunction** over the model's entering
LOCAL frames of the per-frame Δ_R reading on the joint decision interval.
Frames are conditions, not repeated measurements: nothing is averaged across
them, and disagreement is itself a verdict.

### T7. Model-level registered verdicts

| model | order | entering LOCAL frames | per-frame reading | frames agree | model verdict | L3c disposition | §26 methodological success |
|---|---|---|---|:-:|---|---|---|
| Qwen3-4B | B first | 0, 1, 2, 3 | f0=L3c, f1=L3c, f2=L3c, f3=L3c | yes | **LOCAL_EQUIVALENT_SAME_FORM_ONLY** | NEAR_FORM_UNAVAILABLE | NOT_MET (D(A←B) precision, 10 intervals) |
| Qwen3-4B | B second | 0, 1, 2, 3 | f0=L3c, f1=L3c, f2=L3c, f3=L3c | yes | **LOCAL_EQUIVALENT_SAME_FORM_ONLY** | NEAR_FORM_UNAVAILABLE | NOT_MET (D(A←B) precision, 10 intervals) |
| Qwen3-4B-Instruct-2507 | B first | 1, 3 | f1=L3c, f3=L3c | yes | **LOCAL_EQUIVALENT_SAME_FORM_ONLY** | NEAR_FORM_UNAVAILABLE | NOT_MET (D(A←B) precision, 5 intervals) |
| Qwen3-4B-Instruct-2507 | B second | 1, 3 | f1=L3c, f3=L3c | yes | **LOCAL_EQUIVALENT_SAME_FORM_ONLY** | NEAR_FORM_UNAVAILABLE | NOT_MET (D(A←B) precision, 5 intervals) |
| Gemma-3n-E2B-it | B first | 0, 1, 3 | f0=L3c, f1=L3c, f3=L3c | yes | **LOCAL_EQUIVALENT_SAME_FORM_ONLY** | NEAR_FORM_UNAVAILABLE | MET |
| Gemma-3n-E2B-it | B second | 0, 1, 3 | f0=L3c, f1=L3c, f3=L3c | yes | **LOCAL_EQUIVALENT_SAME_FORM_ONLY** | NEAR_FORM_UNAVAILABLE | MET |
| Gemma-3n-E4B-it | B first | 0, 1, 3 | f0=L3c, f1=L3c, f3=L3c | yes | **LOCAL_EQUIVALENT_SAME_FORM_ONLY** | NEAR_FORM_UNAVAILABLE | MET |
| Gemma-3n-E4B-it | B second | 0, 1, 3 | f0=L3c, f1=INDETERMINATE, f3=L3c | **no** | **FRAME_HETEROGENEOUS** | NEAR_FORM_UNAVAILABLE | MET |

**Reading the verdicts.**

- **Qwen3-4B** (4 LOCAL frames) and **Qwen3-4B-Instruct-2507** (2) return
  `LOCAL_EQUIVALENT_SAME_FORM_ONLY` in both orders, with every frame at
  `L3c` and no frame disagreeing.
- **Gemma-3n-E2B-it** (3 LOCAL frames) returns the same in both orders,
  though three of its six cells have Δ_R below −6 pp — a *bounded* reading
  that is nevertheless a large negative contrast.
- **Gemma-3n-E4B-it** returns `LOCAL_EQUIVALENT_SAME_FORM_ONLY` with B
  first, and **`FRAME_HETEROGENEOUS`** with B second, because frame 1 reads
  `INDETERMINATE` while frames 0 and 3 read `L3c`. This is the study's one
  disagreement across frames, and the registered rule reports it rather than
  resolving it.

**`NEAR_FORM_UNAVAILABLE` on all eight.** No verdict is the strong L3c. The
scope sentence the protocol attaches: an L3c with no near-form comparison
cannot distinguish "A is not special" from "the excess is a property of the
exact-count form". §6.4 below shows this is not a formality — the data
separate the two.

**§26 methodological success.** `MET` for both Gemma models; **`NOT_MET`**
for both Qwen models. The reason is confined to one member: **D(A←B)**, the
reciprocal loss, misses its precision precondition on 10 intervals for
Qwen3-4B and 5 for Qwen3-4B-Instruct-2507. **Every Δ_R interval in the study
meets its precondition.** The paper must report the `NOT_MET` verdict, and
must report that it does not touch the primary estimand.

**Identification ledger (§34 D6).** Over all frames, configurations and
families: 1,512 members `ESTIMATED`, 134 `NOT_ASKED` (the arms the design
does not run), **0 `NOT_IDENTIFIED`**. No registered member is a silent
omission.

---

# 6. Raw composition versus matched-reference effects

### T2. Raw composition beside the matched-reference contrast

| model | f | order | c(B\|B) | c(B\|B+A) | c(B\|B+R̄) | D(B←A) pp | D(B←R̄) pp | Δ_R pp | D(A←B) pp | Λ pp |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Qwen3-4B | 0 | B first | 0.768 | 0.904 | 0.877 | -13.54 | -10.89 | **-2.65** | +1.50 | -15.04 |
| Qwen3-4B | 0 | B second | 0.768 | 0.869 | 0.814 | -10.09 | -4.55 | **-5.54** | +26.46 | -36.56 |
| Qwen3-4B | 1 | B first | 0.805 | 0.920 | 0.908 | -11.46 | -10.25 | **-1.20** | +1.07 | -12.53 |
| Qwen3-4B | 1 | B second | 0.805 | 0.881 | 0.852 | -7.62 | -4.69 | **-2.93** | -3.26 | -4.36 |
| Qwen3-4B | 2 | B first | 0.837 | 0.910 | 0.903 | -7.29 | -6.53 | **-0.76** | +35.87 | -43.16 |
| Qwen3-4B | 2 | B second | 0.837 | 0.791 | 0.756 | +4.65 | +8.15 | **-3.49** | +54.46 | -49.80 |
| Qwen3-4B | 3 | B first | 0.889 | 0.976 | 0.977 | -8.66 | -8.76 | **+0.10** | -3.55 | -5.11 |
| Qwen3-4B | 3 | B second | 0.889 | 0.941 | 0.931 | -5.21 | -4.19 | **-1.02** | -12.53 | +7.32 |
| Qwen3-4B-Instruct-2507 | 1 | B first | 0.795 | 0.899 | 0.914 | -10.42 | -11.91 | **+1.50** | +13.51 | -23.93 |
| Qwen3-4B-Instruct-2507 | 1 | B second | 0.795 | 0.782 | 0.772 | +1.24 | +2.24 | **-1.00** | +31.25 | -30.01 |
| Qwen3-4B-Instruct-2507 | 3 | B first | 0.815 | 0.939 | 0.930 | -12.34 | -11.46 | **-0.88** | +3.42 | -15.76 |
| Qwen3-4B-Instruct-2507 | 3 | B second | 0.815 | 0.901 | 0.876 | -8.53 | -6.10 | **-2.43** | +9.54 | -18.07 |
| Gemma-3n-E2B-it | 0 | B first | 0.757 | 0.734 | 0.729 | +2.34 | +2.78 | **-0.43** | +36.52 | -34.18 |
| Gemma-3n-E2B-it | 0 | B second | 0.757 | 0.614 | 0.502 | +14.29 | +25.48 | **-11.19** | +22.27 | -7.98 |
| Gemma-3n-E2B-it | 1 | B first | 0.772 | 0.750 | 0.764 | +2.28 | +0.87 | **+1.41** | -20.70 | +22.98 |
| Gemma-3n-E2B-it | 1 | B second | 0.772 | 0.611 | 0.581 | +16.18 | +19.17 | **-2.99** | -36.10 | +52.28 |
| Gemma-3n-E2B-it | 3 | B first | 0.807 | 0.860 | 0.791 | -5.31 | +1.63 | **-6.93** | +16.60 | -21.91 |
| Gemma-3n-E2B-it | 3 | B second | 0.807 | 0.570 | 0.470 | +23.70 | +33.72 | **-10.03** | +16.57 | +7.13 |
| Gemma-3n-E4B-it | 0 | B first | 0.713 | 0.690 | 0.668 | +2.34 | +4.56 | **-2.21** | +8.07 | -5.73 |
| Gemma-3n-E4B-it | 0 | B second | 0.713 | 0.221 | 0.140 | +49.19 | +57.37 | **-8.18** | +20.61 | +28.58 |
| Gemma-3n-E4B-it | 1 | B first | 0.768 | 0.725 | 0.747 | +4.26 | +2.12 | **+2.15** | -1.30 | +5.57 |
| Gemma-3n-E4B-it | 1 | B second | 0.768 | 0.335 | 0.461 | +43.29 | +30.65 | **+12.64** | +19.86 | +23.44 |
| Gemma-3n-E4B-it | 3 | B first | 0.753 | 0.785 | 0.792 | -3.16 | -3.92 | **+0.76** | +25.13 | -28.29 |
| Gemma-3n-E4B-it | 3 | B second | 0.753 | 0.432 | 0.389 | +32.13 | +36.41 | **-4.29** | +27.86 | +4.26 |

## 6.1 How large is composition, and how much of it survives the swap?

| quantity | range over the 24 LOCAL cells |
|---|---|
| D(B←A), the raw solo-to-pair change on B | **−13.5 to +49.2 pp** |
| D(B←R̄), the same change beside the matched references | **−11.9 to +57.4 pp** |
| D(A←B), the reciprocal change on A | **−36.1 to +54.5 pp** |
| Λ = D(A←B) − D(B←A), the asymmetry | **−49.8 to +52.3 pp** |
| Δ_R, what survives the companion swap | **−11.2 to +12.6 pp** |

11 of 24 cells move B by more than 10 pp on the raw comparison; 3 of 24 move
Δ_R by more than 10 pp. The ratio |D(B←A)| / |Δ_R| runs from 0.8 to 88.6,
with a median of 3.8.

**A large raw composition effect coexists with a small matched-reference
contrast, and the strongest example is stronger than anything in v7.** On
Gemma-3n-E4B-it, frame 0, with B stated second, B's compliance falls from
**0.713 alone to 0.221 beside A** — a 49.2 pp collapse — and to **0.140
beside the three matched references**, a 57.4 pp collapse. Δ_R is **−8.18
pp**: A is *less* harmful than its matched companions, and essentially none
of a 49-point composition effect is attributable to A's identity.

## 6.2 The pattern differs by model family and by position

- **Gemma models, B second**: composition is strongly harmful. D(B←A) is
  +14.3 to +49.2 pp, and D(B←R̄) is larger still in 5 of 6 cells.
- **Gemma models, B first**: composition barely moves B at all (−5.3 to
  +4.3 pp). Position is the dominant factor, not the companion.
- **Qwen models**: composition mostly *helps* B. D(B←A) is negative in 10 of
  12 cells, down to −13.5 pp — B's compliance **improves** when a second
  instruction is present. This is a direct counterexample to any
  shared-resource reading of composition, and it replicates v7's finding
  under confirmatory conditions.

## 6.3 Position dominates, per the registered F11 family

### T9. F11 registered order contrasts (cross-configuration family)

| model | f | Ord_A | Ord_B | Ord_Λ | Ord_R̄ | members failing the precision precondition |
|---|---:|---:|---:|---:|---:|---|
| Gemma-3n-E2B-it | 0 | +14.26* | -11.95* | -26.20* | -22.70* | — |
| Gemma-3n-E2B-it | 1 | +15.40* | -13.90* | -29.30* | -18.31* | — |
| Gemma-3n-E2B-it | 2 | +1.50* | -17.22* | -18.72* | — | — |
| Gemma-3n-E2B-it | 3 | +0.03 | -29.00* | -29.04* | -32.10* | — |
| Gemma-3n-E4B-it | 0 | -12.53* | -46.84* | -34.31* | -52.81* | — |
| Gemma-3n-E4B-it | 1 | -21.16* | -39.03* | -17.87* | -28.54* | — |
| Gemma-3n-E4B-it | 2 | +3.52* | -31.74* | -35.25* | — | — |
| Gemma-3n-E4B-it | 3 | -2.73 | -35.29* | -32.55* | -40.33* | — |
| Qwen3-4B | 0 | -24.97* | -3.45* | +21.52* | -6.35* | Ord_A |
| Qwen3-4B | 1 | +4.33 | -3.84* | -8.17* | -5.57* | Ord_A |
| Qwen3-4B | 2 | -18.59* | -11.95* | +6.64* | -14.68* | — |
| Qwen3-4B | 3 | +8.98* | -3.45* | -12.43* | -4.57* | — |
| Qwen3-4B-Instruct-2507 | 1 | -17.74* | -11.65* | +6.09* | -14.15* | — |
| Qwen3-4B-Instruct-2507 | 3 | -6.12* | -3.81* | +2.31 | -5.36* | — |

Ord_B — the order contrast on B — excludes zero on **all 14 frames** and
reaches **−46.8 pp** on Gemma-3n-E4B-it frame 0. Ord_A excludes zero on 11 of
14. Λ's order contrast reaches −35.3 pp. Where an instruction stands in the
prompt moves compliance by up to four times what the companion's identity
moves it. (Qwen3-4B's Ord_A misses its precision precondition on frames 0
and 1; those two entries carry the marker.)

## 6.4 The finding the paper should build on: the reference *family*, not A, carries the sign

**Status: registered descriptive quantities (F2's Δ_j), grouped post hoc.
This grouping is not a registered estimand and carries no interval.**

A is `marker_however`: *"Use the word* however *exactly n times"* in frame 0's
phrasing, discourse role `contrastive`. The eight MK families are the same
exact-count form over eight other marker words; XC3 is the same exact-count
form over a different counted object, *sentences*. Every core reference in
this study is same-form, and every one is matched to A on frame-conditioned
ι within the registered caliper. Grouping the 72 per-reference contrasts
Δ_j = D(B←A) − D(B←R_j) by the reference's family:

| reference family | n cells | mean Δ_j (pp) | median | min | max |
|---|---:|---:|---:|---:|---:|
| **XC3** (counts sentences) | 12 | **+5.17** | +2.21 | −5.21 | **+35.45** |
| MK3 | 6 | +1.51 | +1.01 | −3.09 | +5.63 |
| MK5 | 6 | +1.09 | +0.73 | −3.16 | +6.87 |
| MK7 | 8 | −1.34 | −0.59 | −4.49 | +2.05 |
| MK1 | 8 | −2.91 | −2.08 | −12.11 | +3.35 |
| MK6 | 8 | −3.58 | −3.65 | −5.73 | −1.60 |
| MK4 | 4 | −4.33 | −0.75 | −15.92 | +0.10 |
| MK2 | 16 | −7.22 | −3.26 | **−34.31** | +2.05 |
| MK8 | 4 | −7.73 | −7.57 | −12.96 | −2.83 |
| **all MK\* (marker-word) pooled** | 60 | **−3.51** | | | |

Against companions that count **another marker word**, A costs B about 3.5 pp
*less* on average: within the marker-word exact-count form, A is
unexceptional. Against companions that count **sentences** at the same
matched difficulty, A costs B about 5 pp *more*, and up to 35 pp more.

This is §34 D18's registered ambiguity, measured. The excess, where it
exists, tracks *what the companion counts*, not the word *however*. It is
also the direct cause of the study's one positive cell (§8), whose frozen
triple contains the single most extreme XC3 contrast in the study.

**The paper may state this as a description of the registered per-reference
contrasts. It may not state it as a tested effect: no registered family
estimates a family-level contrast, and this grouping was formed after seeing
the confirmatory results.**

---

# 7. Per-reference heterogeneity

### T3. Per-reference contrasts

| model | f | order | Δ_1 (R1) | Δ_2 (R2) | Δ_3 (R3) | spread | signs disagree | Δ_R | spread > \|Δ_R\| |
|---|---:|---|---:|---:|---:|---:|:-:|---:|:-:|
| Qwen3-4B | 0 | B first | -2.93* | +0.26 | -5.27* | 5.53 | yes | -2.65 | yes |
| Qwen3-4B | 0 | B second | -5.21* | -5.70* | -5.73* | 0.52 | no | -5.54 | no |
| Qwen3-4B | 1 | B first | -0.39 | -2.47* | -0.75 | 2.08 | no | -1.20 | yes |
| Qwen3-4B | 1 | B second | -4.07* | -1.14 | -3.58* | 2.93 | no | -2.93 | yes |
| Qwen3-4B | 2 | B first | -0.78 | +0.42 | -1.92 | 2.34 | yes | -0.76 | yes |
| Qwen3-4B | 2 | B second | -4.49* | -0.98 | -5.01* | 4.04 | no | -3.49 | yes |
| Qwen3-4B | 3 | B first | -0.23 | +0.23 | +0.29 | 0.52 | yes | +0.10 | yes |
| Qwen3-4B | 3 | B second | +2.44* | -2.12* | -3.39* | 5.83 | yes | -1.02 | yes |
| Qwen3-4B-Instruct-2507 | 1 | B first | +2.05* | +2.18* | +0.26 | 1.92 | no | +1.50 | yes |
| Qwen3-4B-Instruct-2507 | 1 | B second | -0.75 | +0.85 | -3.09 | 3.94 | yes | -1.00 | yes |
| Qwen3-4B-Instruct-2507 | 3 | B first | -1.86 | -2.83* | +2.05* | 4.88 | yes | -0.88 | yes |
| Qwen3-4B-Instruct-2507 | 3 | B second | -3.35* | -4.00* | +0.07 | 4.07 | yes | -2.43 | yes |
| Gemma-3n-E2B-it | 0 | B first | -0.98 | -2.57* | +2.25 | 4.82 | yes | -0.43 | yes |
| Gemma-3n-E2B-it | 0 | B second | -15.92* | -34.31* | +16.67* | 50.98 | yes | -11.19 | yes |
| Gemma-3n-E2B-it | 1 | B first | -5.99* | +3.35* | +6.87* | 12.86 | yes | +1.41 | yes |
| Gemma-3n-E2B-it | 1 | B second | -21.26* | +11.65* | +0.62 | 32.91 | yes | -2.99 | yes |
| Gemma-3n-E2B-it | 3 | B first | -1.60 | -11.13* | -8.07* | 9.54 | no | -6.93 | yes |
| Gemma-3n-E2B-it | 3 | B second | -3.94* | -12.96* | -13.18* | 9.24 | no | -10.03 | no |
| Gemma-3n-E4B-it | 0 | B first | -2.93* | -3.19* | -0.52 | 2.67 | no | -2.21 | yes |
| Gemma-3n-E4B-it | 0 | B second | -12.53* | -12.11* | +0.10 | 12.63 | yes | -8.18 | yes |
| Gemma-3n-E4B-it | 1 | B first | +5.11* | +2.18 | -0.85 | 5.96 | yes | +2.15 | yes |
| Gemma-3n-E4B-it | 1 | B second | +5.63* | +35.45* | -3.16* | 38.61 | yes | +12.64 | yes |
| Gemma-3n-E4B-it | 3 | B first | -2.83* | +3.35* | +1.76 | 6.18 | yes | +0.76 | yes |
| Gemma-3n-E4B-it | 3 | B second | -6.93* | -5.34* | -0.59 | 6.35 | no | -4.29 | yes |

`*` marks a per-reference contrast whose within-family simultaneous interval
excludes zero.

- The three per-reference contrasts **disagree in sign in 15 of 24 cells**.
- The within-cell spread exceeds |Δ_R| in **21 of 24 cells** and exceeds the
  joint half-width in **21 of 24**.
- The largest spread is **50.98 pp** (Gemma-3n-E2B-it f0, B second:
  −15.92, −34.31, +16.67); next is 38.61 pp (Gemma-3n-E4B-it f1, B second).
  The smallest is 0.52 pp (Qwen3-4B f3, B first).
- The registered qualifier `REFERENCE_HETEROGENEOUS` — the three contrasts
  falling on both sides of the 10 pp threshold — fires on 3 cells:
  Gemma-3n-E2B-it f0 and f1 with B second, and Gemma-3n-E4B-it f1 with B
  second.

**Frames where the frozen mean is least representative** (the mean describes
none of its three constituents): Gemma-3n-E4B-it f1 B second (+5.63, +35.45,
−3.16 → mean +12.64) and Gemma-3n-E2B-it f0 B second (−15.92, −34.31, +16.67
→ mean −11.19). In both, one reference of the three carries the whole
result.

**Frames where it is most representative**: every Qwen3-4B cell, where the
three contrasts sit within 4 pp of each other and of their mean.

This is the same observation v7 made — the references disagree with one
another by more than Δ_R — carried into confirmatory evidence, and it is
now larger, not smaller: v7's per-reference spreads were 2.9–10.3 pp against
0.5–51.0 pp here.

---

# 8. Reference-set sensitivity (the registered F_REFSENS family)

**This family is descriptive. The primary claim is decided by the frozen
triple R1+R2+R3 and by nothing else. F_REFSENS says how much the frozen
choice mattered; it never substitutes for it.**

For each entering frame, Δ_R is re-formed over every structurally admissible
triple of the frame's five frozen families {R1…R5} on the same cells, with
its own simultaneous interval. Frames have 9 or 10 admissible triples.

### T4. Reference-set sensitivity (F_REFSENS): every admissible triple of the five frozen families

| model | f | order | frozen Δ_R | frozen reading | #triples | min | max | spread | sign flips | frozen rank (1 = least harmful) | verdicts across triples | class |
|---|---:|---|---:|---|---:|---:|---:|---:|:-:|---:|---|---|
| Qwen3-4B | 0 | B first | -2.65 | L3c | 9 | -3.90 | -1.63 | 2.27 | no | 6/9 | L3c | reference-robust |
| Qwen3-4B | 0 | B second | -5.54 | L3c | 9 | -9.06 | -5.54 | 3.52 | no | 9/9 | L3c | reference-robust |
| Qwen3-4B | 1 | B first | -1.20 | L3c | 9 | -2.44 | -0.01 | 2.43 | no | 6/9 | L3c | reference-robust |
| Qwen3-4B | 1 | B second | -2.93 | L3c | 9 | -6.61 | -2.75 | 3.86 | no | 8/9 | L3c | reference-robust |
| Qwen3-4B | 2 | B first | -0.76 | L3c | 10 | -1.49 | -0.38 | 1.11 | no | 6/10 | L3c | reference-robust |
| Qwen3-4B | 2 | B second | -3.49 | L3c | 10 | -5.57 | -2.91 | 2.66 | no | 8/10 | L3c | reference-robust |
| Qwen3-4B | 3 | B first | +0.10 | L3c | 9 | -0.72 | +0.10 | 0.81 | yes | 9/9 | L3c | reference-robust |
| Qwen3-4B | 3 | B second | -1.02 | L3c | 9 | -4.56 | -1.02 | 3.54 | no | 9/9 | L3c | reference-robust |
| Qwen3-4B-Instruct-2507 | 1 | B first | +1.50 | L3c | 10 | +0.64 | +2.05 | 1.41 | no | 9/10 | L3c | reference-robust |
| Qwen3-4B-Instruct-2507 | 1 | B second | -1.00 | L3c | 10 | -2.30 | +1.06 | 3.36 | yes | 4/10 | L3c | reference-robust |
| Qwen3-4B-Instruct-2507 | 3 | B first | -0.88 | L3c | 10 | -2.16 | +0.39 | 2.55 | yes | 5/10 | L3c | reference-robust |
| Qwen3-4B-Instruct-2507 | 3 | B second | -2.43 | L3c | 10 | -2.62 | +1.42 | 4.04 | yes | 2/10 | L3c | reference-robust |
| Gemma-3n-E2B-it | 0 | B first | -0.43 | L3c | 10 | -4.46 | +1.37 | 5.83 | yes | 7/10 | L3c | sensitive, same verdict |
| Gemma-3n-E2B-it | 0 | B second | -11.19 | L3c | 10 | -25.80 | +0.66 | 26.46 | yes | 6/10 | L3c | sensitive, same verdict |
| Gemma-3n-E2B-it | 1 | B first | +1.41 | L3c | 9 | -3.39 | +3.20 | 6.59 | yes | 7/9 | L3c | sensitive, same verdict |
| Gemma-3n-E2B-it | 1 | B second | -2.99 | L3c | 9 | -18.00 | -0.05 | 17.95 | no | 7/9 | L3c | sensitive, same verdict |
| Gemma-3n-E2B-it | 3 | B first | -6.93 | L3c | 10 | -8.43 | -3.72 | 4.71 | no | 3/10 | L3c | reference-robust |
| Gemma-3n-E2B-it | 3 | B second | -10.03 | L3c | 10 | -10.03 | +3.72 | 13.75 | yes | 1/10 | L3c | sensitive, same verdict |
| Gemma-3n-E4B-it | 0 | B first | -2.21 | L3c | 9 | -2.21 | +5.72 | 7.93 | yes | 1/9 | L3c | sensitive, same verdict |
| Gemma-3n-E4B-it | 0 | B second | -8.18 | L3c | 9 | -8.18 | +16.92 | 25.10 | yes | 1/9 | L3a / L3c | **verdict changes** |
| Gemma-3n-E4B-it | 1 | B first | +2.15 | L3c | 9 | -1.20 | +2.20 | 3.41 | yes | 8/9 | L3c | reference-robust |
| Gemma-3n-E4B-it | 1 | B second | +12.64 | INDETERMINATE@0.10 | 9 | -8.63 | +12.64 | 21.27 | yes | 9/9 | INDETERMINATE@0.10 / L3a / L3c | **verdict changes** |
| Gemma-3n-E4B-it | 3 | B first | +0.76 | L3c | 9 | -5.37 | +1.16 | 6.53 | yes | 8/9 | L3c | sensitive, same verdict |
| Gemma-3n-E4B-it | 3 | B second | -4.29 | L3c | 9 | -6.29 | +4.64 | 10.94 | yes | 3/9 | L3c | sensitive, same verdict |

## 8.1 Classification

| class | cells | which |
|---|---:|---|
| **reference-robust** (one verdict, spread < 5 pp) | 12 | every Qwen3-4B cell, every Qwen3-4B-Instruct-2507 cell, Gemma-3n-E2B-it f3 B first, Gemma-3n-E4B-it f1 B first |
| **sensitive but same registered verdict** | 10 | Gemma-3n-E2B-it f0/f1 both orders, f3 B second; Gemma-3n-E4B-it f0 B first, f3 both orders |
| **registered verdict changes across admissible triples** | **2** | **Gemma-3n-E4B-it f0 B second and f1 B second** |

## 8.2 The two cells where the verdict moves

**Gemma-3n-E4B-it, f0, B second.** The frozen triple gives Δ_R = −8.18 pp,
which is the **most negative of the nine** admissible triples. The other
eight run to **+16.92 pp**, and five of the nine have simultaneous intervals
lying wholly above +10 pp — an `L3a` reading. The three frozen references
give per-reference contrasts −12.53, −12.11 and +0.10; the two backups (R4,
R5) turn the picture over. The registered result for this cell is `L3c`; a
different admissible triple of the same five frozen families would have
supported the opposite registered reading.

**Gemma-3n-E4B-it, f1, B second** — the study's only positive cell. Frozen
Δ_R = +12.64 is the **most harmful of the nine**; the range is **−8.63 to
+12.64 pp**, a spread of 21.27 pp, and the sign flips. Two triples read
`L3a`, one reads `INDETERMINATE@0.10` (the frozen one), six read `L3c`. Its
three per-reference contrasts are +5.63 (MK3:3), **+35.45 (XC3:9)** and
−3.16 (MK5:6), all with intervals excluding zero.

## 8.3 What this licenses

The frozen triple stands and the primary readings are as reported. But the
paper must say, in the Results and not only in an appendix, that:

- across 24 cells the frozen triple's rank among its own admissible triples
  runs from 1st (least harmful) to 9th (most harmful), and lands at an
  extreme (rank 1 or rank n) in **7 cells**;
- the total across-triple spread reaches **26.46 pp** (Gemma-3n-E2B-it f0 B
  second) and exceeds 10 pp in 6 cells, with the sign flipping across
  admissible triples in 14 of 24;
- on **2 cells** a different admissible triple of the *same five frozen
  families* would have changed the registered reading.

**A reference-set-conditional interval is the honest object. The bootstrap
resamples topics, not reference sets, so the reported interval says nothing
about the variation quantified here — and here, as in v7, that variation is
the larger one.**

---

# 9. Operating-point sensitivity (the registered F_RUNNER_UP family)

**Every entering frame of every model is `OPERATING_POINT_UNSTABLE`** — the
frozen n\*(f) was re-selected on fewer than two-thirds of 2,000 topic
resamples. The registered response is not to replace it but to carry the
contrast at the runner-up severity on the same blocks. 18 runner-up
comparisons exist across 7 frames.

The frozen Δ_R's decision interval is the *joint* one, while F_RUNNER_UP is a
descriptive family with its own within-family simultaneous interval. The
table below compares like with like — the frozen Δ_R on its **within-frame**
simultaneous interval against the runner-up on its own.

### T5. Operating-point sensitivity (F_RUNNER_UP), on comparable within-family intervals

| model | f | order | arm | frozen Δ_R [within-frame CI] | reading | runner-up Δ_R [CI] | reading | \|change\| | class |
|---|---:|---|---|---|---|---|---|---:|---|
| Qwen3-4B | 0 | B first | Delta_R[A2] | -2.65 [-4.43, -0.87] | L3c | -2.52 [-4.01, -1.02] | L3c | 0.13 | operating-point robust |
| Qwen3-4B | 0 | B second | Delta_R[A2] | -5.54 [-7.86, -3.23] | L3c | -3.62 [-5.45, -1.80] | L3c | 1.92 | operating-point robust |
| Qwen3-4B | 1 | B first | Delta_R[A2] | -1.20 [-3.08, +0.67] | L3c | -1.79 [-3.10, -0.48] | L3c | 0.59 | operating-point robust |
| Qwen3-4B | 1 | B second | Delta_R[A2] | -2.93 [-5.23, -0.63] | L3c | -0.55 [-2.43, +1.32] | L3c | 2.38 | quantitatively sensitive, same reading |
| Qwen3-4B | 2 | B first | Delta_R[A2] | -0.76 [-2.45, +0.93] | L3c | -0.86 [-2.06, +0.35] | L3c | 0.10 | operating-point robust |
| Qwen3-4B | 2 | B second | Delta_R[A2] | -3.49 [-6.22, -0.76] | L3c | -5.09 [-7.22, -2.96] | L3c | 1.60 | operating-point robust |
| Qwen3-4B | 3 | B first | Delta_R[A2] | +0.10 [-0.79, +0.99] | L3c | -0.10 [-0.76, +0.56] | L3c | 0.20 | operating-point robust |
| Qwen3-4B | 3 | B second | Delta_R[A2] | -1.02 [-2.72, +0.68] | L3c | -1.18 [-2.16, -0.21] | L3c | 0.16 | operating-point robust |
| Gemma-3n-E2B-it | 0 | B first | Delta_R[A2] | -0.43 [-2.58, +1.71] | L3c | -1.61 [-3.21, -0.00] | L3c | 1.17 | operating-point robust |
| Gemma-3n-E2B-it | 0 | B first | Delta_R[B2] | -0.43 [-2.58, +1.71] | L3c | +1.57 [-0.40, +3.55] | L3c | 2.01 | quantitatively sensitive, same reading |
| Gemma-3n-E2B-it | 0 | B second | Delta_R[A2] | -11.19 [-13.92, -8.46] | L3c | -6.56 [-8.91, -4.21] | L3c | 4.62 | quantitatively sensitive, same reading |
| Gemma-3n-E2B-it | 0 | B second | Delta_R[B2] | -11.19 [-13.92, -8.46] | L3c | +1.58 [-0.92, +4.09] | L3c | 12.77 | quantitatively sensitive, same reading |
| Gemma-3n-E4B-it | 0 | B first | Delta_R[A2] | -2.21 [-4.44, +0.01] | L3c | -3.55 [-5.67, -1.43] | L3c | 1.33 | operating-point robust |
| Gemma-3n-E4B-it | 0 | B first | Delta_R[B2] | -2.21 [-4.44, +0.01] | L3c | -1.03 [-2.46, +0.40] | L3c | 1.18 | operating-point robust |
| Gemma-3n-E4B-it | 0 | B second | Delta_R[A2] | -8.18 [-10.44, -5.93] | L3c | -8.34 [-10.39, -6.29] | L3c | 0.16 | operating-point robust |
| Gemma-3n-E4B-it | 0 | B second | Delta_R[B2] | -8.18 [-10.44, -5.93] | L3c | -13.35 [-15.68, -11.01] | L3c | 5.16 | quantitatively sensitive, same reading |
| Gemma-3n-E4B-it | 1 | B first | Delta_R[A2] | +2.15 [+0.02, +4.27] | L3c | +2.31 [+0.66, +3.96] | L3c | 0.16 | operating-point robust |
| Gemma-3n-E4B-it | 1 | B second | Delta_R[A2] | +12.64 [+10.06, +15.22] | L3a | +13.52 [+11.50, +15.54] | L3a | 0.88 | operating-point robust |

## 9.1 Classification

| class | comparisons |
|---|---:|
| operating-point robust (same reading, \|change\| < 2 pp) | 12 |
| quantitatively sensitive, same reading | 6 |
| **registered reading changes** | **0** |

**Operating-point choice changes no registered reading anywhere in the
study.** The largest movement is **12.77 pp** (Gemma-3n-E2B-it f0 B second
under the B2 runner-up, −11.19 → +1.58) and the reading stays `L3c` on both.
Sign flips on 2 of 18 comparisons.

## 9.2 One precise statement about the positive cell

On Gemma-3n-E4B-it f1 B second the runner-up severity moves Δ_R by only
**0.88 pp**, from +12.64 to +13.52. On the *within-frame* simultaneous
interval both read `L3a`; it is the **joint** cross-frame interval —
the registered decision interval, widened by sharing one bootstrap draw
across the model's three entering frames — that spans +10 pp and yields
`INDETERMINATE@0.10`. The paper should say this plainly: the cell's excess
is stable to the operating point and to the estimator, and it is the
registered multiplicity correction, not noise in the estimate, that stops
short of certifying it.

---

# 10. SPECTRUM results

The SPECTRUM arm asks a different question from LOCAL: not "how does A
compare with three matched companions?" but "given how B's loss varies with
companion difficulty across nine spread-out companions from several
families, is A's own loss what that relation predicts?" The registered
estimand is δ_difficulty = D(B←A) − [α̂_family + β̂ · ι_A], with
family-aware intercepts and OLS on equal weights (§11.7).

### T6. SPECTRUM arm: the difficulty relation and A's residual

| model | f | order | LOCAL? | slope β [95% CI] | ι_A | observed D(B←A) | predicted at ι_A | δ_difficulty | joint CI | reading | support |
|---|---:|---|:-:|---|---:|---:|---:|---:|---|---|:-:|
| Qwen3-4B | 0 | B first | L | -0.0248 [-0.047, -0.003] | 0.736 | -13.54 | -10.64 | **-2.90** | [-4.88, -0.92] | L3e | yes |
| Qwen3-4B | 0 | B second | L | +0.0988 [+0.070, +0.128] | 0.736 | -10.09 | -1.57 | **-8.53** | [-11.35, -5.70] | NO_LEVEL | yes |
| Qwen3-4B | 1 | B first | L | +0.0375 [+0.021, +0.054] | 0.688 | -11.46 | -9.32 | **-2.14** | [-4.23, -0.06] | L3e | yes |
| Qwen3-4B | 1 | B second | L | +0.0997 [+0.073, +0.126] | 0.688 | -7.62 | +1.16 | **-8.77** | [-11.76, -5.79] | NO_LEVEL | yes |
| Qwen3-4B | 2 | B first | L | +0.0148 [-0.001, +0.030] | 0.711 | -7.29 | -5.60 | **-1.69** | [-3.85, +0.46] | L3e | yes |
| Qwen3-4B | 2 | B second | L | +0.0486 [+0.025, +0.073] | 0.711 | +4.65 | +7.48 | **-2.83** | [-5.91, +0.26] | L3e | yes |
| Qwen3-4B | 3 | B first | L | +0.0087 [-0.005, +0.022] | 0.744 | -8.66 | -7.51 | **-1.15** | [-2.29, -0.01] | L3e | yes |
| Qwen3-4B | 3 | B second | L | +0.0354 [+0.015, +0.056] | 0.744 | -5.21 | -2.08 | **-3.13** | [-5.22, -1.05] | L3e | yes |
| Qwen3-4B-Instruct-2507 | 1 | B first | L | +0.0309 [+0.012, +0.049] | 0.641 | -10.42 | -12.02 | **+1.60** | [+0.05, +3.15] | L3d | yes |
| Qwen3-4B-Instruct-2507 | 1 | B second | L | +0.0809 [+0.050, +0.112] | 0.641 | +1.24 | +6.90 | **-5.67** | [-8.39, -2.95] | L3e | yes |
| Qwen3-4B-Instruct-2507 | 3 | B first | L | +0.0923 [+0.070, +0.114] | 0.638 | -12.34 | -10.88 | **-1.45** | [-3.19, +0.28] | L3e | yes |
| Qwen3-4B-Instruct-2507 | 3 | B second | L | +0.0664 [+0.042, +0.091] | 0.638 | -8.53 | -7.03 | **-1.50** | [-3.40, +0.39] | L3e | yes |
| Gemma-3n-E2B-it | 0 | B first | L | +0.0884 [+0.058, +0.118] | 0.611 | +2.34 | +4.88 | **-2.54** | [-4.79, -0.29] | L3e | yes |
| Gemma-3n-E2B-it | 0 | B second | L | +0.0927 [+0.057, +0.129] | 0.611 | +14.29 | +39.16 | **-24.87** | [-28.23, -21.51] | NO_LEVEL | yes |
| Gemma-3n-E2B-it | 1 | B first | L | +0.0989 [+0.074, +0.123] | 0.597 | +2.28 | +13.58 | **-11.30** | [-13.85, -8.75] | NO_LEVEL | yes |
| Gemma-3n-E2B-it | 1 | B second | L | +0.1435 [+0.120, +0.167] | 0.597 | +16.18 | +34.39 | **-18.21** | [-21.07, -15.35] | NO_LEVEL | yes |
| Gemma-3n-E2B-it | 2 | B first | — | -0.0104 [-0.041, +0.020] | 0.823 | +2.80 | +21.30 | **-18.50** | [-21.19, -15.82] | NO_LEVEL | yes |
| Gemma-3n-E2B-it | 2 | B second | — | -0.0380 [-0.065, -0.011] | 0.823 | +20.02 | +48.71 | **-28.69** | [-31.92, -25.46] | NO_LEVEL | yes |
| Gemma-3n-E2B-it | 3 | B first | L | +0.1296 [+0.104, +0.155] | 0.672 | -5.31 | +0.44 | **-5.75** | [-7.77, -3.73] | L3e | yes |
| Gemma-3n-E2B-it | 3 | B second | L | +0.2115 [+0.176, +0.247] | 0.672 | +23.70 | +33.74 | **-10.04** | [-12.94, -7.15] | NO_LEVEL | yes |
| Gemma-3n-E4B-it | 0 | B first | L | +0.0095 [-0.021, +0.040] | 0.736 | +2.34 | +0.55 | **+1.80** | [-0.46, +4.05] | L3e | yes |
| Gemma-3n-E4B-it | 0 | B second | L | +0.1142 [+0.087, +0.142] | 0.736 | +49.19 | +51.04 | **-1.86** | [-4.31, +0.60] | L3e | yes |
| Gemma-3n-E4B-it | 1 | B first | L | -0.0415 [-0.061, -0.022] | 0.701 | +4.26 | +11.31 | **-7.04** | [-9.54, -4.55] | L3e | yes |
| Gemma-3n-E4B-it | 1 | B second | L | -0.0483 [-0.069, -0.028] | 0.701 | +43.29 | +54.78 | **-11.49** | [-14.40, -8.58] | NO_LEVEL | yes |
| Gemma-3n-E4B-it | 2 | B first | — | -0.0036 [-0.027, +0.020] | 0.674 | +2.64 | +2.35 | **+0.28** | [-1.84, +2.40] | L3e | yes |
| Gemma-3n-E4B-it | 2 | B second | — | +0.0849 [+0.055, +0.115] | 0.674 | +34.38 | +42.02 | **-7.64** | [-10.55, -4.73] | NO_LEVEL | yes |
| Gemma-3n-E4B-it | 3 | B first | L | +0.0954 [+0.064, +0.127] | 0.719 | -3.16 | -1.93 | **-1.23** | [-3.35, +0.89] | L3e | yes |
| Gemma-3n-E4B-it | 3 | B second | L | +0.2969 [+0.251, +0.343] | 0.719 | +32.13 | +38.67 | **-6.54** | [-9.56, -3.53] | L3e | yes |

## 10.1 What ι is, and which way the relation actually runs

**ι is a chance-corrected stand-alone *compliance*, not a difficulty score.**
`calibration_table.instructed_compliance` computes (solo − chance)/(1 − chance),
"the share of the achievable improvement over chance that stating the
constraint delivers". **Higher ι means the companion is followed more often —
an *easier* companion. Lower ι is harder.** The protocol's own spectrum slots
confirm the orientation: `SPECTRUM_LOW`/`side: below` sits at low ι and
`SPECTRUM_HIGH`/`side: above` at high ι, so "below" and "above" are on the
compliance scale. The protocol calls ι "the difficulty coordinate" because it
*indexes* difficulty, but it runs in the opposite direction, and any figure or
sentence that treats rightward-on-ι as "harder" has the sign backwards.

With that fixed, the relation mostly runs **against** intuition. Over the 28
SPECTRUM cells the point estimate of β is **positive in 22** and its
simultaneous interval **excludes zero above it in 19** — and a positive β on a
compliance axis means **B's loss is larger beside an *easier* companion**.
Only **4** cells are significantly negative (Qwen3-4B f0 B first,
Gemma-3n-E2B-it f2 B second, and **both orders of Gemma-3n-E4B-it f1**), and
those four are the ones where the intuitive direction holds: harder companions
cost B more. Five span zero.

The largest slope is +0.297 (Gemma-3n-E4B-it f3, B second): a companion whose
stand-alone compliance is 10 points *higher* costs B about 3 points more. The
pattern is visible within families as well as across them — on Gemma-3n-E2B-it
f3 with B second, MK2 runs +35.0 → +36.9 → +40.1 pp as ι rises 0.57 → 0.69 →
0.91, and MK5 and MK6 do the same.

**The paper must not repeat the design's premise as a finding.** The SPECTRUM
arm was built on the expectation that a harder companion costs B more; in
these confirmatory data that expectation is contradicted in 19 conditions,
supported in 4, and unresolved in 5. Report the direction as measured, and
claim no mechanism for it — the design reads no model internals, and ι and the
loss are measured on the same blocks.

The relation is real but neither universal nor stable across frames of the
same model: on Gemma-3n-E4B-it, β runs +0.010 (f0), **−0.042** (f1) and
+0.095 (f3) with B first. **Wording frame changes the sign of the
compliance-response relation within a single model.**

## 10.2 Is A unusually harmful relative to companions of its stand-alone compliance?

**No — and emphatically so.** δ_difficulty is **negative in 25 of the 28
cells**: A costs B *less* than the fitted relation predicts for a companion of
A's measured stand-alone compliance.

- **17 cells read `L3e`** — the residual lies wholly inside the ±10 pp
  equivalence region. A behaves as its difficulty predicts.
- **1 cell reads `L3d`** — Qwen3-4B-Instruct-2507 f1, B first,
  δ_difficulty = **+1.60 pp**, joint CI [+0.05, +3.15]. This is the only
  registered *direction* claim in the SPECTRUM arm, and it is +1.6 pp.
- **10 cells reach no registered level.** All ten are strongly negative,
  down to **−28.69 pp** (Gemma-3n-E2B-it f2, B second). The registered
  grammar is one-sided — `L3d` needs the interval above zero, `L3e` needs it
  inside ±10 pp — so a large negative residual has no level to reach. **The
  paper must not read "no level" as "no result": the point estimate and its
  interval are reported descriptively and the direction is unambiguous.**
- The support check `holds` on **28 of 28** cells: A's difficulty is inside
  the fitted range in every one, so no cell extrapolates.

## 10.3 SPECTRUM against LOCAL on the one positive cell

This is the study's most important internal disagreement.

On **Gemma-3n-E4B-it, frame 1, B second** the LOCAL arm gives Δ_R = +12.64
pp (A worse than its three matched references) while the SPECTRUM arm gives
δ_difficulty = **−11.49 pp**, joint CI [−14.40, −8.58] (A better than
companions of its difficulty predict). The two arms are not contradictory —
they compare A against different reference sets — but they point opposite
ways, and the raw points show why:

| slot | family | ι | B loss (pp) |
|---|---|---:|---:|
| S5 | MK3 | 0.318 | +38.31 |
| S1 | CL7 | 0.446 | +75.68 |
| S7 | MK8 | 0.526 | +50.52 |
| S3 | MK1 | 0.534 | +59.64 |
| **A** | **marker_however** | **0.701** | **+43.29** |
| R1 | MK3 | 0.769 | +37.66 |
| S4 | MK1 | 0.897 | +54.69 |
| S6 | MK3 | 0.900 | +35.81 |
| S2 | CL7 | 0.920 | +75.26 |
| S8 | MK8 | 0.933 | +48.08 |

A's +43.29 pp sits in the middle of a spectrum running +35.8 to +75.7 —
B's compliance falls from 0.768 alone to 0.335 beside A, against 0.410 beside
the gentlest spectrum companion and **0.011** beside the harshest (CL7:95, a
class-family companion that all but destroys compliance with B). The
LOCAL triple for this cell is MK3:3 (+37.66), **XC3:9 (+7.85)** and MK5:6
(+46.45): its mean is dragged down by a single sentence-count companion
whose effect on B is less than a quarter of the gentlest companion on the
spectrum.

**A looks harmful in this cell not because it is harsh but because one of
its three matched references is unusually gentle.**

## 10.4 What SPECTRUM licenses

- "B's loss varies systematically with the companion's stand-alone
  compliance" — yes, and in 19 of 28 conditions the sign is that an *easier*
  companion costs B more. State the direction explicitly; do not paraphrase
  it as "harder companions cost more", which the data contradict.
- "A is not unusually harmful relative to companions of its measured
  stand-alone compliance" — this is the closest the study comes to that
  sentence, and
  it is licensed only as `L3e` on the 17 cells that reach it, with the
  scope "relative to the nine fitted spectrum companions of this frame".
- **Not licensed**: a mechanism; any transfer of `L3e` to the LOCAL arm's
  claim; a general absence of pair-specific interference.

---

# 11. Other registered robustness analyses

## 11.1 §17.4 vacuity: the F6 gate and the F5 recomputation

The both-halves rule: F6 (the vacuity-rate family) gates the **reporting**
half — the qualification sentence and the partial-identification bounds —
while the F5 vacuity-forced recomputation gates the **licensing** half:
both bounds must license the same claim.

- The F6 gate **binds on 6 of the 24 cells** (all four Qwen3-4B-Instruct-2507
  cells, plus Qwen3-4B f0 and f3 with B first). Where it binds, the registered
  partial-identification bounds are reported, e.g.
  Qwen3-4B-Instruct-2507 f3 B first: [−15.15, −9.51] pp against a point
  estimate of −0.88.
- The F5 recomputation **agrees on 23 of 24 cells**. The exception is
  **Gemma-3n-E4B-it f1 B second**, where `forced_agrees = false` and the
  registered flag `vacuity_withholds_levels` fires — an independent second
  reason that cell reaches no level. That cell therefore carries the
  `VACUITY_DEPENDENT` qualifier without the F6 gate binding, which is why
  seven cells carry the qualifier and six carry the gate.

## 11.2 §15 F5 recodings: vacuous-pass and graded-compliance

96 recoded members over the 24 LOCAL cells. Six sign changes: four under
the graded recoding (three on D(B←A), one on Δ_R) and two under the
vacuous-pass recoding (one each). Largest movements:

| model | f | order | member | primary | recoded | movement |
|---|---:|---|---|---:|---:|---:|
| Gemma-3n-E4B-it | 1 | B second | D(B←A) \| graded_0.99 | +43.29 | +27.54 | −15.76 |
| Gemma-3n-E2B-it | 0 | B second | D(B←A) \| graded_0.99 | +14.29 | +0.55 | −13.74 |
| Gemma-3n-E4B-it | 0 | B second | D(B←A) \| graded_0.99 | +49.19 | +36.00 | −13.18 |
| Qwen3-4B-Instruct-2507 | 3 | B first | Δ_R \| vacuity_forced | −0.88 | −12.33 | −11.45 |
| Gemma-3n-E2B-it | 0 | B second | Δ_R \| graded_0.99 | −11.19 | −21.88 | −10.69 |
| **Gemma-3n-E4B-it** | **1** | **B second** | **Δ_R \| graded_0.99** | **+12.64** | **+7.07** | **−5.57** |

**The study's one positive Δ_R loses 44% of its magnitude under the
registered graded-compliance recoding**, falling to +7.07 pp — inside the
10 pp bound. This belongs in the Results paragraph about that cell, not in
an appendix.

## 11.3 §23 projection audit

§13.6's admission projection is compared with the realised composed rate on
every composed cell. **370 of 370 audited cells fall outside the 0.05
allowance**, with a median absolute error of **0.264** and a maximum of
**0.867** (Qwen3-4B f0, B+S2: projected 0.932, realised 0.065). The record's
own sentence: this is an **admission** quantity, its record is prospective,
and it licenses no claim and revises no admission. But the size of the
mismatch is a real methodological finding: the independence-style projection
used to decide which companions are admissible bears almost no relation to
what composed cells actually do, and the paper should say so in Limitations.

## 11.4 §34 D6 identification ledger

1,512 `ESTIMATED`, 134 `NOT_ASKED`, **0 `NOT_IDENTIFIED`**.

## 11.5 L4a cross-configuration consistency

Per named member, across the two prompt positions: **16 of 24 member-frame
pairs agree**. Δ_R agrees on **11 of 12 frames** — the exception is
Gemma-3n-E4B-it f1 (L3c with B first, no level with B second).
δ_difficulty agrees on 5 of 12 (it reaches `L3e` with B first and no level
with B second on five frames, because the residual grows past ±10 pp when B
is stated second). The registered reading for a disagreement is
"configuration dependence (§28.1)", not an error.

## 11.6 Summary table

| analysis | largest numerical movement | most affected cell | sign changes | headline survives? | qualification |
|---|---|---|---|---|---|
| Reference-set sensitivity (F_REFSENS) | 26.46 pp spread | Gemma-3n-E2B-it f0 B second | sign flips in 14 of 24 cells | **on 22 of 24** | verdict changes on Gemma-3n-E4B-it f0 and f1, B second |
| Operating point (F_RUNNER_UP) | 12.77 pp | Gemma-3n-E2B-it f0 B second | 2 of 18 | **yes, everywhere** | none |
| Graded-compliance recoding | −15.76 pp | Gemma-3n-E4B-it f1 B second | 4 of 48 members | **yes** | the one positive Δ_R falls to +7.07 pp |
| Vacuous-pass recoding | −11.45 pp | Qwen3-4B-Instruct-2507 f3 B first | 2 of 48 members | **yes** | §17.4 withholds levels on Gemma-3n-E4B-it f1 B second |
| F6 vacuity gate | bounds [−15.15, −9.51] pp | Qwen3-4B-Instruct-2507 f3 B first | — | **yes** | gate binds on 6 cells; 7 carry `VACUITY_DEPENDENT` |
| §23 projection audit | 0.867 absolute error | Qwen3-4B f0 B+S2 | — | **yes** (licenses nothing) | the admission projection is badly calibrated |
| Order contrasts (F11) | −46.84 pp | Gemma-3n-E4B-it f0, Ord_B | — | **yes** | position dominates companion identity |
| L4a consistency | — | Gemma-3n-E4B-it f1 | — | **yes** | Δ_R order-dependent on 1 of 12 frames |

---

# 12. Frame and order heterogeneity

### T8. Frame and order heterogeneity in Δ_R

| model | order | Δ_R by frame (pp) | between-frame range | readings |
|---|---|---|---:|---|
| Gemma-3n-E2B-it | B first | f0 -0.43, f1 +1.41, f3 -6.93 | 8.34 | L3c |
| Gemma-3n-E2B-it | B second | f0 -11.19, f1 -2.99, f3 -10.03 | 8.19 | L3c |
| Gemma-3n-E4B-it | B first | f0 -2.21, f1 +2.15, f3 +0.76 | 4.36 | L3c |
| Gemma-3n-E4B-it | B second | f0 -8.18, f1 +12.64, f3 -4.29 | 20.82 | INDETERMINATE@0.10 / L3c |
| Qwen3-4B | B first | f0 -2.65, f1 -1.20, f2 -0.76, f3 +0.10 | 2.75 | L3c |
| Qwen3-4B | B second | f0 -5.54, f1 -2.93, f2 -3.49, f3 -1.02 | 4.52 | L3c |
| Qwen3-4B-Instruct-2507 | B first | f1 +1.50, f3 -0.88 | 2.38 | L3c |
| Qwen3-4B-Instruct-2507 | B second | f1 -1.00, f3 -2.43 | 1.43 | L3c |

| model | f | Δ_R B first | Δ_R B second | order difference |
|---|---:|---:|---:|---:|
| Gemma-3n-E2B-it | 0 | -0.43 | -11.19 | -10.75 |
| Gemma-3n-E2B-it | 1 | +1.41 | -2.99 | -4.41 |
| Gemma-3n-E2B-it | 3 | -6.93 | -10.03 | -3.09 |
| Gemma-3n-E4B-it | 0 | -2.21 | -8.18 | -5.97 |
| Gemma-3n-E4B-it | 1 | +2.15 | +12.64 | +10.49 |
| Gemma-3n-E4B-it | 3 | +0.76 | -4.29 | -5.05 |
| Qwen3-4B | 0 | -2.65 | -5.54 | -2.90 |
| Qwen3-4B | 1 | -1.20 | -2.93 | -1.73 |
| Qwen3-4B | 2 | -0.76 | -3.49 | -2.73 |
| Qwen3-4B | 3 | +0.10 | -1.02 | -1.12 |
| Qwen3-4B-Instruct-2507 | 1 | +1.50 | -1.00 | -2.50 |
| Qwen3-4B-Instruct-2507 | 3 | -0.88 | -2.43 | -1.55 |

## 12.1 How much does the conclusion depend on wording frame?

- Between-frame ranges in Δ_R: **2.38 pp** (Qwen3-4B-Instruct-2507, B first)
  to **20.82 pp** (Gemma-3n-E4B-it, B second).
- On the two Qwen models the frames agree closely — ranges of 1.43–4.52 pp,
  every frame `L3c`, every sign the same. **Frame conditioning costs
  precision there and buys nothing.**
- On the two Gemma models the frames disagree substantially — ranges of
  4.36–20.82 pp — and on Gemma-3n-E4B-it with B second the disagreement
  crosses a registered verdict boundary.

## 12.2 How much does it depend on prompt position?

Order differences in Δ_R run from **−10.75 pp** (Gemma-3n-E2B-it f0) to
**+10.49 pp** (Gemma-3n-E4B-it f1). In 11 of 12 frames Δ_R falls when B is
stated second (A looks comparatively better); on Gemma-3n-E4B-it f1 it rises
by 10.5 pp, which is exactly the frame that produces the study's only
positive result. Position is not a nuisance: it is a factor of the same
magnitude as the frame.

## 12.3 Would averaging have hidden something?

Yes, once, and decisively. Averaging Gemma-3n-E4B-it's three entering frames
with B second gives (−8.18 + 12.64 − 4.29)/3 = **0.06 pp** — a number that
would read as a clean null and would have concealed the only cell in the
study where A costs B more than its references. That single arithmetic fact
is the strongest confirmatory argument for treating frames as conditions,
and it should appear in the paper's Results.

The converse is also true and should be stated: on the two Qwen models,
frame conditioning found nothing that pooling would have missed, and it cost
a quarter of the evidence per cell. The honest summary is that frame
conditioning is necessary because you cannot know in advance which model is
a Gemma.

---


# 13. Comparison with the superseded v7 development evidence

**Never merge the two. v7 (`neurips-4.pdf`) pooled the four wording frames,
ran on development lanes at a different commit under a design whose
protocol change was adopted after its outcomes were visible, and reports
eight configurations. v8.1 conditions on frame, is preregistered and frozen,
and reports twenty-four cells. Their Δ_R are not the same estimand: v7's is
pooled over frames, v8.1's is per frame.**

## 13.1 v7's Table 1, reproduced here only for reference

| model | B stated | D(B←A) | D(B←R̄) | Δ_R | simultaneous 95% CI |
|---|---|---:|---:|---:|---|
| Gemma 3n E2B | first | −2.3 | +0.9 | −3.2 | [−5.9, −0.5] |
| | second | +21.1 | +29.6 | −8.5 | [−11.9, −5.1] |
| Gemma 3n E4B | first | +3.5 | +6.2 | −2.7 | [−5.6, +0.2] |
| | second | +39.2 | +46.4 | −7.3 | [−10.3, −4.2] |
| Qwen3 4B | first | −12.3 | −12.0 | −0.3 † | [−2.4, +1.8] |
| | second | −2.0 | −3.2 | +1.3 | [−1.4, +3.9] |
| Qwen3 4B Instruct | first | −13.2 | −13.8 | +0.6 † | [−1.5, +2.8] |
| | second | −10.7 | −10.4 | −0.3 | [−3.0, +2.3] |

*Development evidence. Superseded. Do not present as a current result.*

## 13.2 Claim-by-claim

| v7 claim | v8.1 classification | why |
|---|---|---|
| "Raw composition effects are large and depend on which instruction is measured and where it appears; in all eight configurations at least one instruction moves by more than 10 pp with an interval excluding zero" | **REPLICATES QUALITATIVELY, STRENGTHENS** | D(B←A) now reaches +49.2 pp against v7's +39.2; D(A←B) reaches +54.5 pp; Λ spans −49.8 to +52.3 pp; Ord_B excludes zero on all 14 frames and reaches −46.8 pp. |
| "Direction is not uniform across models" | **REPLICATES** | Composition still helps B on the Qwen models (D(B←A) negative in 10 of 12 cells) and hurts it badly on the Gemmas with B second. The counterexample to a shared-resource reading survives. |
| "Δ_R runs between −8.5 and +1.3 pp" | **WEAKENS** (range widens, both ways) | v8.1: **−11.19 to +12.64 pp**. Both tails are outside v7's interval. Conditioning on frame reveals variation pooling averaged out. |
| "No simultaneous upper bound exceeds +3.9 pp" | **DOES NOT REPLICATE** | v8.1's largest joint upper bound is **+15.66 pp**, and 3 of 24 cells have upper bounds above +3.9 pp (Gemma-3n-E2B-it f1 B first +3.93, Gemma-3n-E4B-it f1 B first +4.66 and f1 B second +15.66). This specific v7 sentence must be deleted, not softened. |
| "In three configurations the references cost B more than A" | **REPLICATES, STRENGTHENS** | 11 of 24 cells now have joint intervals wholly below zero, and the largest is −11.19 pp against v7's −8.5. |
| "Matched-reference interference is much smaller than raw composition loss" | **REPLICATES** | \|D(B←A)\| / \|Δ_R\| runs 0.8 to 88.6; 11 of 24 cells move B by >10 pp raw against 3 of 24 for Δ_R. |
| "Every entering configuration satisfies the bounded (<+10 pp) reading" | **WEAKENS: 23 of 24, not 24 of 24** | Gemma-3n-E4B-it f1 B second reads `INDETERMINATE@0.10`. |
| "Are there current positive pair-specific effects?" | **NEW: yes, one, and not certified** | +12.64 pp with the joint interval excluding zero — but no registered level, four qualifications, and the SPECTRUM arm pointing the other way. |
| "The references disagree with one another by more than Δ_R" | **REPLICATES, STRENGTHENS** | v7: spreads 2.9–10.3 pp, exceeding \|Δ_R\| in 7 of 8. v8.1: **0.5–51.0 pp**, exceeding \|Δ_R\| in 21 of 24. |
| "Two configurations could not have failed (ceiling compression)" | **REPLICATES with a different footprint** | `COMPOSED_CONTRAST_RANGE_COMPRESSED` fires on 8 of 24 cells, all on Qwen models. |
| "Only 6–14% of candidates per model survived the stability screen, and no run generated a second reference set" | **SUPERSEDED / RESOLVED** | v8.1 freezes five families per frame and the registered F_REFSENS re-forms Δ_R over all 9–10 admissible triples. |
| "The interval is conditional on those three references" | **REPLICATES and is now quantified** | The across-triple spread reaches 26.46 pp and changes the registered verdict on 2 of 24 cells. |
| "Admission used raw solo compliance where the protocol specifies a chance-corrected coordinate" | **NOT COMPARABLE — fixed** | v8.1 admits on the chance-corrected ι throughout. |
| v7's per-model, per-order verdicts | **NOT COMPARABLE** | The estimand changed: v7's Δ_R is pooled over frames, v8.1's is per frame, and no registered v8.1 quantity pools them. |
| "A is not unusually harmful" (implied in places) | **NEVER LICENSED, IN EITHER** | v7 disclaims it in its Discussion; v8.1 makes it unreachable by construction (`NEAR_FORM_UNAVAILABLE`). |

## 13.3 Did conditioning on wording reveal heterogeneity that pooling hid?

**Yes, once, decisively.** Averaging Gemma-3n-E4B-it's three entering frames
with B second gives +0.06 pp — indistinguishable from v7's pooled −7.3 pp
being "small" — while the frames are −8.18, **+12.64** and −4.29. The
between-frame range of 20.82 pp is larger than any single Δ_R v7 reported.

**And it revealed nothing on the Qwen models,** where the frames agree
within 1.4–4.5 pp and every reading is `L3c`. The lesson is asymmetric:
frame conditioning is necessary because heterogeneity is model-specific and
unpredictable in advance, not because it is ubiquitous.

## 13.4 Does the old central lesson survive?

Yes, and it is now confirmatory rather than developmental. A large
solo-to-pair change does not identify a harmful companion: the strongest
single illustration in the study is Gemma-3n-E4B-it frame 0 with B second,
where B falls 49.2 pp beside A and **57.4 pp** beside its matched
references. What has changed is the second half of the lesson. v7 could say
"and the contrast against a named class is always small". v8.1 cannot: the
contrast against a named class is small in 23 of 24 cells, and in the
twenty-fourth it is not — and *which* class you name, and under *which
wording*, decides that.

---

# 14. Final methodology-validation evidence

*Source: `dci1/reports/dci1v8dev/frame_aware_prescreen/prescreen_revalidation.md`
(§§2–5) and `revalidation.json`; machine-readable digest in
`postconfirm/data/methodology_validation_final.csv`. All of it is
**pre-freeze** evidence about identification, generated before any composed
cell existed. None of it is confirmatory.*

## 14.1 Keep three robustness concepts apart

| | what is perturbed | what it measures |
|---|---|---|
| **A. Re-execution** | same topics, same seeds, run again | decoding / backend nondeterminism |
| **B. Topic resampling** | a fresh area-stratified partition of the 216 pre-freeze topics into the same roles | topic-sampling sensitivity |
| **C. Topic bootstrap** | resampling stored calibration rows | conditional resampling stability of a fixed sample |

The confirmatory bootstrap is C. The operating-point stability statistic is
C. §3.5's replicates are A. §3.7's replicates are B. **Never describe one as
another.**

## 14.2 Frame-conditioned forwarding changes what is identifiable

At equal measurement budget, on identical calibration rows, the frame's own
candidate set yields at least as many admissible families as the frame-pooled
set on **13 of 14** supported model × frame combinations, and on **2** the
§13.15 verdict itself differs (Qwen3-4B-Instruct-2507 f3: 5 families / 2
backups against 4 / 1; Gemma-3n-E4B-it f0: 7 / 2 against 4 / 1). One model —
2507 — is eligible because of it.

## 14.3 r26, and the honest form of the 2507 claim

`dci1v8-pilot-r26` re-executed the **v8 pooled design itself** at the frozen
v8 commit `f7af7f2` on the same model, topics and seeds. On 2507 frame 3 it
gave 5 / 2 — supported. Gathering every observation of a pooled forwarded
set on that frame: it clears §13.15 in **2 of 5** observations and misses in
3, while the frame-aware set clears it in **3 of 3**.

**The registered form of the claim is therefore: the pooled rule is
*marginal* on that frame, not reliably failing.** The paired comparisons
(r15 and r20, identical rows, frame-aware supported and pooled not) remain
the strongest evidence, and Gemma-3n-E4B-it frame 0 (7/2 against 4/1 in both
successor runs) is untouched. **Nothing in v8.1 changed because of r26**; it
was prespecified as a control on the interpretation of a
methodology-validation finding, and the design it re-executes is superseded.

## 14.4 Decoding re-execution (perturbation A)

All **16 of 16** frame-level verdicts agree between the two runs of every
model; entering-frame sets and model eligibilities are identical in every
pair; admissible-family counts move by at most one on the three
nondeterministic models and not at all on Gemma-3n-E4B-it; ι_A(f) agrees
within 0.02 on every replicated frame. Underneath, forwarded-set Jaccard is
**0.59–1.00**, the core reference triple recurs on **5 of 16** frames and the
core families on 8 of 16. Between 23% and 49% of calibration grid rows decode
differently under fixed seeds on three models; Gemma-3n-E4B-it is effectively
deterministic on this stack.

## 14.5 Topic resampling (perturbation B) — the genuinely fresh-sample test

Prespecified in `dci1/docs/V8_TOPIC_RESAMPLED_VALIDATION.md` and committed
(`8032673`) before any replicate row was generated. The 216 pre-freeze
topics (prescreen + calibration A + calibration B) are re-partitioned into
the same roles, area-stratified, under a domain-separated seed
(`dci1v8:topicrep:v1`, index 1, seed `2969019755343878771`), leaving the
composed, confirmatory and sequestered sets untouched. Verified at row level:
the Qwen3-4B replicate's 24-topic screen shares **2** topics with the pilot's,
the number a uniform re-deal predicts. Runs in the `topic-replicate`
namespace under study id `dci1v8-topicrep`, which `confirm/pilot_import`
refuses, so **no replicate root can be bound by a freeze**. Every scientific
rule unchanged.

| measure | perturbation A (decoding) | perturbation B (topics) |
|---|---|---|
| LOCAL verdicts agreeing | 16 of 16 | **13 of 14** |
| SPECTRUM identification agreeing | — | 13 of 14 |
| operating points agreeing | — | 11 of 14 |
| model eligibility agreeing | 4 of 4 | **3 of 4** |
| forwarded-set Jaccard | 0.59–1.00 | 0.51–0.77 |
| core reference triple identical | 5 of 16 | 3 of 14 |
| core reference families identical | 8 of 16 | 7 of 14 |
| admissible backups identical | 8 of 16 | 3 of 14 |

**Topic sampling is the larger source of variation on every measure, but not
by a wide margin. On both perturbations the pipeline's *verdicts* are far
more stable than the objects it selects.** Gemma-3n-E4B-it is the clean
contrast: its decoding is deterministic on this stack, so its
topic-resampled figures isolate topic sampling with no decoding noise.

## 14.6 The one eligibility disagreement, and two knife-edge frames

**Qwen3-4B-Instruct-2507 frame 1** carries 6 LOCAL-valid families and 2
backups in the bound pilot and **4 and 1** in the topic replicate, below
§13.15's minimum — so the replicate's LOCAL set is {3} alone and the model
would **not** be eligible under `LOCAL_ELIGIBILITY_MIN_FRAMES = 2`. The
measurement is sound on both sides: `SUPPORTED` at Gate 2 in both, same
chance basis (κ = 0), ι_A(f) 0.652 against 0.641, complete row accounting on
both (138,240 and 137,472 candidate rows). **This is a genuine sensitivity
of that model's eligibility to which pre-freeze topics land in which role.**
The registered rule decides on the bound pilot, so the model entered — and
its confirmatory result is reported with this caveat attached.

**Gemma-3n-E2B-it frame 0** has selected n\* = 1, 8 and 3 across three
samples of the same 216-topic pool under the unchanged rule on an unchanged
eligible set. **Qwen3-4B-Instruct-2507 frame 0** has moved between
unsupported and supported under decoding noise alone. The runner-up arm is
the registered instrument for exactly this, and §9 shows it changes no
reading.

## 14.7 Engineering integrity: the reuse defect and the commit audit

**The row-reuse defect.** `run.execute._reusable_rows` matched a previous
run on design-generation identity and row-id set but not on whether those
rows had actually been generated, so a run killed mid-flight could be
"reused" with unanswered `TECHNICAL_FAILURE` rows. It was found when it
invalidated pilot r17 (274,176 unanswered rows reused after an out-of-memory
kill left an orphan engine core). It is now fixed by
`reusable_rows_checked`, which refuses a previous run whose sidecar is
blocked, unreadable, or that contains any row whose outcome is not the
backend's generated outcome. **Both the pilot path and the confirmatory
generation path go through the guard**, and seven regression tests pin it. A
scan of 108 backend runs across 9 roots found no other affected evidence.
Its first production use admitted a complete 265,728-row Gemma-3n-E4B-it run
after a memory kill, so the retry redid only the scoring tail.

**A stale integrity test, found and corrected on 2026-09-10.**
`tests_v8dev/test_frame_aware_prescreen.py::test_the_frozen_root_and_the_pilot_roots_still_verify`
asserts that the superseded v8 root `dci1v8-confirm-r2` is untouched by
comparing its MEMBERSHIP record hashes against
`reports/dci1v8dev/confirmatory_membership.json`. That path holds the
**study-level** lock, and commit `034fc72` correctly repointed it at the
v8.1 root while archiving the v8 lock beside it — so since 2026-09-08 the
test has been comparing the v8 root against the v8.1 lock and failing. The
evidence is intact: all four of `dci1v8-confirm-r2`'s MEMBERSHIP records
hash exactly to the archived v8 lock's values (`16ed7358…`, `d30ced8235…`,
`eb84e293…`, `83a07d56…`). The test now reads the lock written **for that
root** and asserts the lock's own `root` field names it. The failure
predates the confirmatory analysis and could not have been caused by it —
`FROZEN` and everything before it are immutable once the freeze exists.

*What was re-run to check it.* A bounded selection of twelve `tests_v8dev`
files covering the confirm layer, the freeze and readiness gates, the reuse
guard, the provenance gate, the reference-sensitivity tool, the allocation,
the rules-provenance and documentation-path checks, and the whole
frame-aware pre-screen file that carried the corrected test: **118 passed,
0 failed, in 10 minutes**. The *full* `tests_v8dev` breadth was started and
then stopped deliberately — see the operational note below — so this bundle
does not claim a complete-suite pass. Nothing under `src/` was modified by
this work, so the suite's behaviour cannot have changed; the only source
edit is the one test.

**An operational note for whoever runs the suites next.** `tests_v8dev` at
full breadth writes fixture trees under `/tmp/pytest-of-*` that reached
**45 GB** in twenty minutes on this host and took the root filesystem to
99% full — the same condition that killed two GPU lanes with `OSError`
during the pilot phase (2026-09-06). Run bounded selections, watch
`df`, and `rm -rf /tmp/pytest-of-*` afterwards.

**The mixed-commit audit.** The four bound pilots are `dci1v8-pilot-r14`
(Qwen3-4B), `r15` (2507), `r16` (Gemma-3n-E2B-it) at commit `025e138`, and
`r23` (Gemma-3n-E4B-it) at `7d8e1d9`. `git diff 025e138 7d8e1d9` touches one
source file and within it one constant — the backend wall-clock cap. 71 of
72 hashed package files are identical and the `rules`, `protocol`,
`documents` and `wording_diagnostic` bindings are identical across all four
roots. **No scientific rule differs**, so no model was re-run for commit
uniformity.

## 14.8 Freeze readiness

Eleven of eleven readiness items passed for every model: preregistration,
allocation, calibration policy, operating-point stability, reference
sensitivity, no protected artifacts, instrument, analysis code, worktree,
identification statuses, pre-screen policy. Target basis **C**
(`RETENTION_TARGET_BASIS = calibration_iota_a`) was registered on the
precision argument, with basis A generated and re-verdicted as a comparator
that decides nothing; the two bases forward measurably different sets
(Jaccard 0.63–0.97) and reach the same family count, backup count and
§13.15 verdict on **all 14** supported frames.

## 14.9 What this section is for in the paper

It is no longer the paper's scientific endpoint. It now does one job:
it establishes that the identification pipeline that chose the operating
points and the reference sets is stable enough in its **verdicts** for the
confirmatory contrast to mean something, while being explicit that the
**objects** it selects are not stable — which is exactly why §8's
reference-set sensitivity is a Results-section item and not an appendix.

---


# 15. Claim ledger

Evidence classes: **PC** primary confirmatory · **RS** registered
sensitivity · **RD** registered descriptive · **MV** methodology validation
· **SD** superseded development · **EP** exploratory post-hoc.

| # | candidate claim | class | evidence | scope | strongest licensed wording | wording that would be too strong | paper section |
|---:|---|:-:|---|---|---|---|---|
| 1 | A costs B no more than same-form companions matched on frame-conditioned difficulty | **PC** | `L3c` on the joint interval, 23 of 24 cells; `data/primary_delta_by_frame_order.csv` | per model × frame × order | "In 23 of the 24 entering conditions the simultaneous interval for Δ_R(f) stops below +10 pp." | "A is not unusually harmful"; "no pair-specific interference"; "equivalent to zero"; "no more than" without the +10 pp margin | Results |
| 2 | Model-level equivalence to same-form companions | **PC** | `LOCAL_EQUIVALENT_SAME_FORM_ONLY`, 7 of 8 model × order | per model × order | "Seven of the eight model × order configurations return the registered same-form-only equivalence verdict." | dropping "same-form-only"; generalising to companions at large | Results |
| 3 | One condition shows A costing B more than its references | **PC** | Gemma-3n-E4B-it f1 B second, Δ_R = +12.64, joint CI [+9.62, +15.66], `INDETERMINATE@0.10` | one cell | "On Gemma-3n-E4B-it under frame 1 with B second, Δ_R = +12.6 pp with a joint interval excluding zero; the registered rule certifies neither an excess above +10 pp nor a bound below it." | "A specifically interferes with B on this model"; omitting the four qualifications | Results |
| 4 | Frames disagree within a model | **PC** | `FRAME_HETEROGENEOUS`, Gemma-3n-E4B-it B second | one model × order | "On one model and prompt order the entering frames do not reach the same reading, and the registered verdict is heterogeneity." | treating heterogeneity as a null or as noise | Results |
| 5 | Raw composition effects are large, directional and position-dependent | **PC** | F1 D(B←A), D(A←B), Λ; F11 order contrasts | 24 cells / 14 frames | "Composition moves B's compliance by −13.5 to +49.2 pp and A's by −36.1 to +54.5 pp; the order contrast on B excludes zero on all fourteen frames and reaches −46.8 pp." | any mechanism; "composition redistributes a shared resource" | Results |
| 6 | Composition can help | **PC** | D(B←A) negative in 10 of 12 Qwen cells | Qwen models | "On both Qwen models B's compliance improves when a second instruction is present, by up to 13.5 pp." | generalising beyond these checkpoints | Results |
| 7 | A large raw effect can carry almost no companion-specific signal | **PC** | Gemma-3n-E4B-it f0 B second: 49.2 vs 57.4 pp, Δ_R −8.18 | one cell, illustrative | "B falls 49 pp beside A and 57 pp beside its matched references." | presenting it as the typical case | Results / Figure |
| 8 | The result is robust to operating-point choice | **RS** | F_RUNNER_UP, 18 comparisons, 0 reading changes | 7 frames | "The runner-up operating point changes no registered reading; the largest movement is 12.8 pp and the reading is unchanged on both sides." | "the operating point does not matter" — every frame is `OPERATING_POINT_UNSTABLE` | Results / Appendix |
| 9 | The result is **not** uniformly robust to reference choice | **RS** | F_REFSENS, 2 of 24 verdicts change, spread to 26.5 pp | 24 cells | "On two cells a different admissible triple of the same five frozen families supports a different registered reading; across-triple spread reaches 26.5 pp." | "the result is robust to reference choice" | Results |
| 10 | A is unexceptional relative to companions of its measured difficulty | **PC** (SPECTRUM) | δ_difficulty `L3e` on 17 of 28 cells, negative in 25 | per frame × order | "In seventeen of twenty-eight conditions A's loss lies within ±10 pp of what the fitted difficulty relation predicts, and in twenty-five of twenty-eight the point estimate is below the prediction." | transferring this to the LOCAL claim; "A is harmless" | Results |
| 11 | B's loss varies with the companion's stand-alone compliance, mostly in the counter-intuitive direction | **PC** (SPECTRUM) | slope β on the ι (compliance) axis: 19 of 28 intervals above zero, 4 below, 5 spanning | per frame × order | "The fitted slope is positive and excludes zero in nineteen of twenty-eight conditions — B fares worse beside an *easier* companion — and is negative in four." | "harder companions cost B more" (the data contradict this in 19 of 28); any mechanism | Results |
| 12 | The two arms disagree on the one positive cell | **PC** | Δ_R +12.64 vs δ_difficulty −11.49 on the same cell | one cell | "On the one condition where A costs B more than its three matched references, A costs B 11.5 pp *less* than companions of its measured difficulty predict." | resolving the disagreement in either direction | Results / Discussion |
| 13 | Wording changes which controls are admissible | **MV** | 13 of 14 at-least-as-supported; 2 verdict differences; one eligibility change | pre-freeze | "At equal budget, frame-conditioned forwarding changes the admissibility verdict on two of fourteen supported frames and one model's eligibility." | claiming it changes the confirmatory result | Method / Validation |
| 14 | Frame-level verdicts replicate; the selected objects do not | **MV** | A: 16/16, Jaccard 0.59–1.00, triples 5/16. B: 13/14, 0.51–0.77, 3/14 | pre-freeze | "Verdicts agree on 16 of 16 under re-execution and 13 of 14 under topic resampling, while forwarded sets overlap at 0.51–1.00 and the selected triple recurs on 3–5 of 14–16 frames." | calling A a resampling test or B a decoding test | Validation |
| 15 | One model's eligibility is sample-sensitive | **MV** | 2507 f1: 6/2 → 4/1 under a fresh partition | one model | "Under a different partition of the same 216 pre-freeze topics, Qwen3-4B-Instruct-2507 would not have been eligible." | suppressing it; calling it a defect | Limitations |
| 16 | The reference *family*, not A's identity, carries the sign of Δ_j | **RD + EP** | F2 Δ_j grouped by family: XC3 +5.17 pp mean, MK\* −3.51 pp | 72 registered contrasts, grouped post hoc | "Descriptively, the per-reference contrasts against sentence-count companions average +5.2 pp while those against other marker-word companions average −3.5 pp." | presenting it as a tested effect or attaching an interval | Discussion, flagged as post-hoc |
| 17 | The admission projection is badly calibrated | **RD** | §23 audit: 370 of 370 outside the 0.05 allowance, median error 0.264 | all composed cells | "The §13.6 admission projection lies outside its allowance on every audited composed cell." | treating it as invalidating admission — it revises no admission by rule | Limitations |
| 18 | The §26 methodological criterion is not met on the Qwen models | **PC** | `NOT_MET`, D(A←B) precision only | 2 models | "The registered methodological-success criterion is not met on either Qwen model, because the reciprocal loss D(A←B) misses its precision precondition; every Δ_R interval meets it." | omitting it; or implying Δ_R is imprecise | Results / Limitations |
| 19 | Δ_R between −8.5 and +1.3 pp; no upper bound above +3.9 pp | **SD** | v7 Table 1 | superseded | may be cited only as "the superseded development design reported…" | any presentation as a current result | Historical appendix |
| 20 | A large solo-to-pair change does not identify a harmful companion | **PC** (was SD) | claims 5, 7, 1 together | the whole study | "A solo-to-pair change is not by itself evidence about the companion's identity; a pair-specific claim requires an explicitly stated reference class." | dropping "explicitly stated reference class" | Conclusion |

## 15.1 The eight sentences the prompt asked about, adjudicated

| sentence | verdict |
|---|---|
| "A is not unusually harmful" | **Never licensed.** `NEAR_FORM_UNAVAILABLE` makes the strong L3c unreachable by construction, and one cell reads `INDETERMINATE@0.10`. |
| "Pair-specific interference is absent" | **Never licensed.** A bounded contrast against a named class is not an absence claim, and 18 of 24 cells carry `A_GENERAL_NOT_EXCLUDED`. |
| "Composition effects are generic" | **Not licensed as stated.** Licensed: composition effects are large and are not explained by the companion's identity within the named class. "Generic" implies a mechanism the design cannot see. |
| "Wording changes the control set" | **Licensed as methodology validation** (2 of 14 admissibility verdicts, 1 eligibility). Not licensed as a confirmatory finding. |
| "Matched references explain most composition loss" | **Licensed descriptively**, with the ratio: \|D(B←A)\|/\|Δ_R\| from 0.8 to 88.6. Not as a decomposition — no registered quantity decomposes the loss. |
| "The effect generalises across models" | **Not licensed.** Four checkpoints in two families, reported per model, never pooled, and one of the four disagrees with itself across frames. |
| "The result is robust to reference choice" | **False as stated.** Two of 24 registered verdicts change across admissible triples of the frozen five. |
| "The result is robust to operating-point choice" | **Licensed**, with the qualification that every frame is `OPERATING_POINT_UNSTABLE` and the robustness is against the registered runner-up, not against the whole grid. |

---

# 16. Recommended figures and tables

## 16.1 The datasets

All under `dci1/reports/dci1v8dev/postconfirm/data/`, produced by
`dci1/tools/v8_postconfirm_extract.py` (reads the signed records only) and
`dci1/tools/v8_postconfirm_spectrum_points.py` (re-forms the registered
spectrum fit's own input and asserts it reproduces the recorded residuals).

| file | rows | contents |
|---|---:|---|
| `primary_delta_by_frame_order.csv` / `.json` | 24 | the primary matrix: Δ_R, SE, marginal / within-frame / **joint** intervals, precision flag, registered reading, direction, statuses, qualifiers, boundary record, n\*, m\*, ι_A, the frozen triple |
| `raw_vs_reference_loss.csv` | 24 | B solo, c(B\|B+A), c(B\|B+R̄), D(B←A), D(B←R1..R3), mean, D(A←B), Λ |
| `per_reference_contrasts.csv` | 72 | Δ_1..Δ_3 with within-family intervals, family, ι, B-loss and realised c(B \| B+R_j) beside each reference, c(B \| B) and c(B \| B+A), spread, heterogeneity flags |
| `reference_sensitivity.csv` | 226 | every admissible triple's Δ_R with its simultaneous interval, min/max/spread, sign-flip and frozen-triple flags |
| `runner_up_sensitivity.csv` | 18 | frozen vs runner-up operating point, with intervals and the stability status |
| `spectrum_results.csv` | 28 | slope with interval, ι_A, observed and predicted loss, δ_difficulty with the joint interval and reading, support, intercepts, residuals |
| `spectrum_points.csv` | 288 | the (companion, family, ι, B-loss, realised c(B \| B+companion)) points the registered fit consumed, plus A's point, prediction and residual |
| `registered_gates.csv` | 24 | L1 headroom, L2, Ξ, vacuity (binds / gate / forced-agrees / bounds), reference heterogeneity, projection audit |
| `recoding_robustness.csv` | 96 | F5 vacuity-forced and graded-0.99 recomputations with movements and sign flips |
| `order_contrasts.csv` | 54 | F11 Ord_A, Ord_B, Ord_Λ, Ord_R̄ with intervals and precision flags |
| `projection_audit.csv` | 384 | §23 projected vs realised composed rate per cell |
| `cross_configuration_consistency.csv` | 24 | L4a per-member agreement across the two orders |
| `identification_ledger.csv` | 1,646 | §34 D6 status of every registered member |
| `model_level_verdicts.csv` | 8 | model verdict, per-frame readings, agreement, L3c disposition, §26 outcome |
| `methodology_validation_final.csv` | 21 | the A/B perturbation digest of §14 |
| `provenance.json` | — | per-model record hashes, commit, resamples, row counts, frames |

## 16.2 Main-paper figures (recommended: 3)

**Figure 1 — The frame-conditioned Δ_R forest.** *(primary confirmatory)*

- **Question**: under each wording frame and prompt order, does A cost B
  more than its matched references?
- **Panels**: one row per model; within a row, one line per entering frame,
  filled marker for B first and open for B second. x-axis Δ_R in pp, with a
  vertical line at 0 and at +10. Draw the **joint** simultaneous interval as
  the bar and the within-frame interval as a thin whisker so the multiplicity
  cost is visible. Hatch the 8 `COMPOSED_CONTRAST_RANGE_COMPRESSED` cells.
- **What the reader learns**: 23 of 24 intervals stop short of +10 pp; the
  Qwen models' frames sit on top of one another while the Gemmas' spread
  out; one open marker on Gemma-3n-E4B-it sits alone past +10.
- **Data**: `primary_delta_by_frame_order.csv`.
- This replaces v7's Figure 3 and is the paper's central exhibit.

**Figure 2 — Composition versus companion identity.** *(primary confirmatory)*

- **Question**: how much of a large solo-to-pair change is about *this*
  companion?
- **Panels**: for each model × order, a circle at D(B←A) and a hexagon at
  D(B←R̄) joined by a grey bar whose length is Δ_R; frames as small offsets
  within the cell.
- **What the reader learns**: the bars are short and the markers are far
  from zero. Annotate Gemma-3n-E4B-it f0 B second (49.2 → 57.4, Δ_R −8.18)
  and Qwen3-4B f0 B first (−13.5 → −10.9, Δ_R −2.65) as the two regimes.
- **Data**: `raw_vs_reference_loss.csv`.
- This is v7's Figure 4 rebuilt on confirmatory evidence, and it is stronger.

**Figure 3 — Where the one positive result comes from.** *(primary + registered sensitivity)*

- **Question**: what does the study's only positive cell actually rest on?
- **Panels**: (a) the nine admissible triples for Gemma-3n-E4B-it f1 B
  second as a dot plot from −8.63 to +12.64 with the frozen triple starred at
  the extreme; (b) the SPECTRUM scatter for the same cell — ι on x, B-loss on
  y, the ten points from `spectrum_points.csv`, the fitted line, A marked
  with its residual of −11.49 pp drawn as an arrow to the prediction.
- **What the reader learns**: the excess is carried by one reference of
  three; and on the same rows, the difficulty relation puts A *below*
  prediction. This is the paper's honest centrepiece and its most novel
  content.
- **Data**: `reference_sensitivity.csv`, `spectrum_points.csv`.

### 16.2a Figures already drawn

Three figures in `dci1/reports/dci1v8dev/postconfirm/figures/`, vector PDF
and 300-dpi PNG, rendered from the committed tables by
`dci1/tools/v8_postconfirm_spectrum_plot.py`. The script asserts per panel,
failing closed, that the line it draws passes through the record's own
`predicted_loss_at_A_pp` at the record's own `difficulty_a`; all 28 pass.

| file | role |
|---|---|
| `fig1_spectrum_forest` | **main.** Panel A: β with its simultaneous interval. Panel B: δ_difficulty with its joint decision interval. Rows grouped by model then prompt order, `f0`–`f3` within, circles B-first and squares B-second; ordinary cases muted, colour only on β < 0 and on `L3d` / no-level; summary counts above each panel. |
| `fig2_spectrum_explainer` | **main.** Gemma-3n-E4B-it f1 B second, with observed, predicted and δ = −11.5 pp annotated directly on the residual segment. |
| `fig3_spectrum_grid` | **appendix.** All 28 conditions, 8 × 4, shared legend, β and δ as compact subtitles. |

**The x axis is a compliance axis, and that changes the reading.** ι is
`(solo − chance)/(1 − chance)`, so higher ι is an *easier* companion (§10.1).
The figures label it as compliance and carry an explicit
`← harder · easier →` cue rather than transforming it, because the registered
β is defined on the ι scale and plotting `1 − ι` would put a sign on the
drawn line that the record does not contain.

Two further things the panels encode that prose keeps losing. The grey band
around the line is a **slope** band — the simultaneous interval on β pivoted
at the centroid — and not a confidence band for the fitted mean, which the
record cannot support because it carries no intercept uncertainty. And the
registered grammar is **one-sided**: `L3d` needs the interval above zero,
`L3e` needs it inside ±10 pp, so a large *negative* residual reaches no
level. The ten dark-slate rows in fig 1B are not nulls; they are the
conditions where A is most clearly *less* harmful than its compliance
predicts.

**Optional fourth (supplementary if space is short) — the identification
figure from the pre-confirmatory manuscripts** (`f81_identification.pdf`,
`f81_frames.pdf`) should move to an appendix: it is now background, not
result.

## 16.3 Main-paper tables (recommended: 2)

**Table 1 — the primary matrix**, T1 above, trimmed to model, frame, order,
n\*, m\*, the frozen triple, Δ_R, the joint CI and the registered reading.
24 rows fits a NeurIPS page in `\small`. Mark compressed cells with a dagger
as v7 did.

**Table 2 — the robustness ledger**, §11.6 above: one row per registered
robustness analysis, its largest movement, the most affected cell, and
whether the headline survives. This is what a referee will look for and no
prior version of the paper has it.

**Appendix tables**: T3 (per-reference), T4 (reference sensitivity), T5
(runner-up), T6 (spectrum), T9 (order contrasts).

*Figures were chosen from the findings, not from the existing plotting code:
`figure2_delta_r_forest.pdf` and `figure3_loss_decomposition.pdf` happen to
be reusable shapes for Figures 1 and 2, but Figure 3 is new and
`f81_turnover.pdf` — the candidate-set turnover plot — should be demoted to
the appendix because its subject is no longer the paper's result.*

---


# 17. Section-by-section manuscript rewrite map

Base the rewrite on **`v8_1_source.pdf` / `main_v8_1_preconfirm.tex`** — it
is the frame-conditioned design paper and its Method, Appendix B and
Appendix C are already correct. `lp4fm_source/main_lp4fm.tex` is the same
body reframed for a prompt-sensitivity venue and carries two extra
related-work subsections worth harvesting. `neurips-4.pdf` supplies the
Results *narrative shape* — and none of its numbers.

| section | action | what to do |
|---|---|---|
| **Title** | **MODIFY** | v8.1's *"Compared With What? Frame-Conditioned Matched References for Pair-Specific Instruction Interference"* still fits, but the paper is no longer only about identification. Consider *"Compared With What? A Frame-Conditioned Confirmatory Test of Pair-Specific Instruction Interference"*. Keep lp4fm's title only if targeting a prompt-sensitivity venue. |
| **Abstract** | **REPLACE** | Every sentence from "This paper reports the design and its validation, not its outcome" onward is now false. Delete "We report no value, sign or interval for ∆R(f)". Write the three-sentence result of §18.2 below, keep the 0.22/0.68/0.42/0.52 motivating fact, keep the verifier-scope sentence. |
| **Introduction** | **MODIFY** | Keep §§1–2 of the motivation verbatim. Replace the "what we will find" paragraph with what was found. Add one sentence naming the single positive cell — a reader who meets it first in Results will distrust the paper. |
| **Contributions** | **REPLACE** | New list: (i) the frame-conditioned design; (ii) a preregistered, frozen confirmatory test at 384 blocks per frame on 2.35 M generations; (iii) the bounded result on 23 of 24 conditions with measured precision; (iv) the one heterogeneous model and what three registered sensitivities do to it; (v) the reference-set sensitivity result — that a matched-reference conclusion can turn on which admissible triple is frozen. |
| **Related Work** | **KEEP** | Unchanged; the estimand gap argument is untouched. Optionally fold in lp4fm's prompt-sensitivity subsection if the venue rewards it. |
| **Background** | **KEEP** | Unchanged. |
| **Method** | **KEEP, with three insertions** | It is already the frozen protocol. Insert: (a) the joint cross-frame decision interval and that it — not the marginal or within-frame interval — decides; (b) the registered reading grammar L3a/L3b/L3c/`INDETERMINATE@0.10` and the `NEAR_FORM_UNAVAILABLE` disposition; (c) the conjunction rule for the model verdict and that heterogeneity is a verdict. |
| **§5 "Methodology validation"** | **MOVE and SHRINK** | Becomes §5 "Identification and its stability", roughly one page: Result 1 (2 of 14 verdicts, 1 eligibility), Result 2 restated with **both** perturbations A and B and the r26 correction, Result 3 (operating-point instability) compressed to three sentences pointing at the runner-up arm. Everything else to Appendix C. It is no longer the paper's endpoint. |
| **Results** | **REPLACE (new section)** | 5.1 raw composition and position; 5.2 the matched-reference contrast, Table 1 + Figure 1; 5.3 the one heterogeneous model, Figure 3, with all four qualifications; 5.4 the SPECTRUM arm; 5.5 the robustness ledger, Table 2. Borrow `neurips-4`'s paragraph rhythm — claim, number, qualification — and none of its values. |
| **Discussion** | **MODIFY** | Keep "what the design exists to draw apart" and the wording-frame paragraph. Replace the forward-looking paragraph with: what a bounded Δ_R(f) licenses; why one positive cell does not overturn it and does not confirm it either; the family-composition observation of §6.4 as the most interesting open question; the two arms' disagreement. |
| **Limitations** | **REPLACE** | New list in this order: the reference-set sensitivity (2 verdicts change); the 2507 eligibility sample-sensitivity; the §26 `NOT_MET` on both Qwen models; the §23 projection audit; every frame `OPERATING_POINT_UNSTABLE`; no near-form arm so `NEAR_FORM_UNAVAILABLE`; verifier-defined compliance with no human labelling and no answer-quality measure; scope (one focal pair, one genre, four checkpoints, never pooled). Delete "no confirmatory composed observation exists". |
| **Conclusion** | **MODIFY** | Keep v7's shape. New second half: the contrast against a named class is small in 23 of 24 conditions and is not in the twenty-fourth, and which class you name — and under which wording — decides that. |
| **Appendix A (extended related work)** | **KEEP** | Unchanged. |
| **Appendix B (protocol and implementation)** | **MODIFY** | Replace "Freeze, provenance and current status" with §2 of this bundle: the root, the commit, the hashes, the row counts, the completeness record, the exact command. Add the reuse-guard fix and the mixed-commit audit. |
| **Appendix C (sensitivity design "and what it will report")** | **REPLACE** | Change tense. It now reports: the full F_REFSENS table, the full F_RUNNER_UP table, the F5 recodings, the F6 vacuity family, the §23 audit, the identification ledger, L4a. Tables T3–T6 and T9 live here. |
| **Historical-development appendix** | **KEEP, retitle** | Keep v7's Table 1 as clearly-labelled superseded development evidence and add one paragraph: which of its claims replicate, weaken or fail (§13.2 of this bundle). Do not delete it — it is the honest record of how the design got here. |
| **Broader impacts** | **KEEP** | Unchanged. |
| **NeurIPS checklist** | **MODIFY** | Flip every "no confirmatory result exists" answer. Point the reproducibility items at the frozen root, the commit, the preregistration hash and the analysis-record hashes in §2.2–2.3. |

## 17.1 Sentences that must disappear

1. "This paper reports the design and its validation, not its outcome."
2. "No confirmatory composed observation exists under this design."
3. "We report no value, sign or interval for ∆R(f)."
4. "No simultaneous 95% interval reaches an upper bound above +3.9 points."
5. "∆R runs from −8.5 to +1.3 points" — as a current result.
6. Any sentence implying the matched-reference contrast is uniformly small.
7. Any sentence implying the reference-set choice is a minor qualification.

---

# 18. The strongest scientifically defensible paper story

## 18.1 Which of the candidate stories the evidence supports

| candidate | verdict |
|---|---|
| A. Large composition effects largely disappear under matched companion replacement | **Strongly supported**, and the primary spine. |
| B. Pair-specific interference exists, but only for particular frames / models / orders | **Weakly supported — one cell**, uncertified by the registered rule and undercut by three registered sensitivities. Report it; do not build on it. |
| C. Reference-set choice materially changes the conclusion | **Supported on 2 of 24 cells** and is the study's most important methodological finding. |
| D. Operating-point choice materially changes the conclusion | **Not supported.** No reading changes. |
| E. Difficulty explains much of the effect and A is unexceptional | **Supported for A's position** (δ_difficulty `L3e` on 17 of 28, negative in 25) but **not in the assumed direction**: the fitted relation says B fares worse beside an *easier* companion in 19 of 28 conditions. |
| F. A remains anomalous after conditioning on companion difficulty | **Not supported**; the one `L3d` is +1.6 pp. |
| G. Wording changes not only identification but the substantive result | **Supported on one model**: a 20.8 pp between-frame range that crosses a verdict boundary, on a model where pooling would have returned +0.06 pp. |
| H. The evidence is mixed or imprecise | **Rejected on precision** (24 of 24 met the precondition); **partly true on mixedness**, confined to one model × order. |

**The paper's story is A + C + E, with B and G as the honest complication.**

## 18.2 The strongest one-sentence result

> Against three same-form companions matched to it on wording-conditioned
> stand-alone difficulty, the focal instruction costs compliance with the
> measured instruction less than 10 percentage points more than they do in
> 23 of 24 preregistered model × wording-frame × prompt-order conditions —
> while composition itself moves compliance by up to 49 percentage points.

## 18.3 The strongest three-sentence abstract-level result

> Composing two verifiable instructions moves compliance enormously — B's
> compliance falls by as much as 49 percentage points beside A and rises by
> as much as 13 beside it, depending on the model and on where B stands —
> but replacing the companion instead of removing it leaves almost all of
> that movement behind: in 23 of 24 preregistered conditions the
> simultaneous interval for the matched-reference contrast stops below 10
> percentage points, with realised half-widths of 1 to 3 points, so the
> smallness is measured rather than underpowered. The twenty-fourth
> condition — one model under one of four sentence frames with B stated
> second — puts the contrast at +12.6 points, a result the registered rule
> declines to certify and that three registered sensitivities undercut: one
> of its three references carries it, the registered graded recoding cuts it
> by 44% to +7.1 points, and the difficulty-spectrum arm on the same rows
> puts A 11.5 points *below* what
> companions of its measured difficulty predict. Conditioning on wording is
> what made that condition visible at all — averaging the model's three
> frames returns +0.06 points — so a pair-specific claim needs not only an
> explicitly stated reference class but the phrasing under which that class
> was matched.

## 18.4 The main surprise

That the study's one positive result is manufactured by a *single* reference
of three. Gemma-3n-E4B-it frame 1 with B second is simultaneously the most
harmful-looking cell in the study on the LOCAL arm and one of the most
benign on the SPECTRUM arm, and the reason is legible in the raw points: its
frozen triple contains XC3:9, a sentence-count companion matched to A on ι
whose effect on B (+7.85 pp) is less than a quarter of the gentlest of the
nine spectrum companions (+35.81 pp) and a ninth of the harshest
(+75.68 pp). The design's own warning — that a matched-reference conclusion
is conditional on the reference set — turns out to be its most important
empirical finding.

## 18.5 The main qualification

Reference-set choice changes a registered verdict on 2 of 24 cells, and the
frozen triple lands at an extreme of its own admissible set in 7 of 24. The
reported interval does not cover this: the bootstrap resamples topics, not
reference sets.

## 18.6 The most important negative result

Operating-point sensitivity, which the pre-confirmatory manuscripts flagged
as the pipeline's least stable stage and which every entering frame carries
as `OPERATING_POINT_UNSTABLE`, **changes no registered reading anywhere**.
The runner-up arm was the right response and it came back clean. Report it —
a preregistered worry that did not materialise is evidence.

## 18.7 The most informative disagreement

Between the LOCAL and SPECTRUM arms on Gemma-3n-E4B-it frame 1 with B
second: +12.64 pp against −11.49 pp on the same rows. Neither is wrong;
they name different comparison classes, and the gap between them is the size
of the reference-class problem.

## 18.8 The central methodological lesson

A matched-reference design does not remove the reference-class problem; it
makes it measurable and moves it somewhere it can be audited. Once you have
named a class, three things still decide your answer, and this study
measures all three: **which admissible members you froze** (2 verdicts move),
**under which wording you matched them** (a 20.8 pp between-frame range that
crosses a verdict boundary), and **which comparison class you chose in the
first place** (LOCAL and SPECTRUM disagree by 24 pp on the same rows). The
v7 lesson — a solo-to-pair change does not identify a harmful companion —
survives confirmatory testing. Its successor is that naming a reference
class is not one decision but three, and a paper that reports only the first
is reporting a third of its own uncertainty.

---

# 19. Limitations and claims that remain unavailable

1. **`NEAR_FORM_UNAVAILABLE`.** No near-form arm was run, so no verdict can
   distinguish "A is not special" from "the excess is a property of the
   exact-count form" — and §6.4 shows the data actively raise that question.
   No claim of the form "A is not unusually harmful" is available anywhere.
2. **No class arm.** Δ_broad is unavailable; nothing is licensed about
   companions outside the exact-count form.
3. **Reference-set conditionality.** 2 of 24 verdicts change across
   admissible triples of the frozen five; the frozen triple is at an extreme
   of its set in 7 of 24; the reported interval does not cover this.
4. **Every frame is `OPERATING_POINT_UNSTABLE`.** Δ_R(f) is conditional on
   the frozen n\*(f), m\*(f). The runner-up arm bounds one alternative, not
   the grid.
5. **Qwen3-4B-Instruct-2507's eligibility is sample-sensitive.** Under a
   different partition of the same 216 pre-freeze topics it would not have
   entered. Its confirmatory result must travel with this sentence.
6. **§26 `NOT_MET` on both Qwen models**, on D(A←B)'s precision.
7. **The §23 admission projection is outside its allowance on every audited
   composed cell** (median absolute error 0.264).
8. **Ceiling compression** on 8 of 24 cells (`COMPOSED_CONTRAST_RANGE_COMPRESSED`).
9. **Ξ does not resolve outcome-specificity on 18 of 24 cells**
   (`A_GENERAL_NOT_EXCLUDED`): even a resolved excess could be A being
   generally disruptive rather than specifically harmful to B.
10. **Verifier-defined compliance.** Deterministic verifier, validated
    against an independent reimplementation, a frozen boundary suite, an
    adversarial corpus and seeded-defect tests — but **no human labelling**.
    Nothing supports a claim about compliance as a human would judge it, and
    no quantity measures answer quality.
11. **Scope.** One focal instruction (`marker_however`, exact-count form),
    one base-task genre, three same-form references per model × frame, four
    small open-weight checkpoints in two families, two prompt positions.
    Reported per model, never pooled, and the four models already disagree.
12. **No mechanism.** The design reads no model internals.
13. **Frames are four sentence templates**, not a sample from a population of
    phrasings. Nothing generalises to unseen wordings.

## 19.1 `OPTIONAL_POSTHOC_ANALYSES` — recorded, not run

None of these were run; none would be confirmatory; each would need its own
registration before it could carry a claim.

1. **Reference-family contrast.** §6.4's grouping of Δ_j by reference family
   is descriptive. A proper analysis would need a registered family-level
   estimand and a multiplicity plan.
2. **Why XC3 companions are gentler on B.** A near-form arm, or a
   companion-property regression on the spectrum points, would separate
   "counts a different object" from "is easier to satisfy jointly with B".
3. **Leave-one-reference-out on every cell.** F_REFSENS covers triples of
   five families; a leave-one-out over the wider admissible pool would bound
   the reference-set problem more tightly.
4. **A frame-level variance component.** Would require treating frames as a
   sample, which the design explicitly does not.
5. **Response length.** Stored, used by no analysis; no length control is
   claimed.
6. **Why D(A←B) misses its precision precondition on the Qwen models.**
   Operationally interesting; changes no primary reading.
7. **Recalibrating the §13.6 admission projection.** It is outside its
   allowance on every cell; a better projection would change which
   companions are admissible in a *future* design, not this one.

---

# 20. Source and provenance index

## 20.1 Result → artifact → root → freeze → commit

```
every number in §§4–12
  └─ dci1/reports/dci1v8dev/postconfirm/data/*.csv
       └─ produced by dci1/tools/v8_postconfirm_extract.py
                  and dci1/tools/v8_postconfirm_spectrum_points.py
            └─ read from  <root>/durable/dci1v8/<model>/CONFIRMATORY_ANALYSIS/
                          confirmatory_analysis.json   (signed)
                 └─ signed under freeze_hash, which is
                    <root>/durable/dci1v8/<model>/FROZEN/freeze.json
                      └─ inputs: membership_lock_hash 31af521c…,
                                 manifest_hash 8cfa2082…,
                                 pilot record hashes (r14/r15/r16/r23)
                         └─ producing_commit 034fc7214762b6848d5d904b14fd82b317830667
                            preregistration d3552f9f47e3f008…
```

`<root>` = `dci1/evidence/dci1v8p1-confirm`, on branch
`dev/v8-frame-aware-prescreen` in the worktree
`/home/cnm13ryan/git/dci-v8-canonical`. The signed records are mirrored
under both `durable/` and `evidence/`, and the `records/` subdirectory of
each holds the `record_hash`.

**`dci1/evidence/` is gitignored and does not survive a clone.** The durable
artifact for every number in this bundle is therefore the committed CSV/JSON
under `dci1/reports/dci1v8dev/postconfirm/data/`, whose `provenance.json`
carries each model's analysis-record hash, freeze hash, generation-record
hash, producing commit, resample count and row count. A reader without the
evidence tree can still check that a quoted number came from the record it
names; a reader with the tree can recompute the CSVs and compare hashes. If
the confirmatory root has to be preserved beyond this machine, it is 37 GB
(19 GB under `durable/` and the same again mirrored under `evidence/`),
almost all of it `scored.jsonl`; the signed stage records themselves are
about 290 MB, and a reproduction check needs only those.

## 20.2 Documents

| document | what it is |
|---|---|
| `dci1/docs/DCI1_preregistration_v8.1.md` | the preregistration, hash `d3552f9f…` |
| `dci1/docs/V8_CONFIRMATORY.md` | the confirmatory layer's design |
| `dci1/docs/V8_FRAME_CONDITIONING.md` | Approach A: frame as part of the condition |
| `dci1/docs/V8_FRAME_AWARE_PRESCREEN.md` | the v8.1 pre-screen |
| `dci1/docs/V8_CANDIDATE.md` | the v8 candidate design of record |
| `dci1/docs/V8_TOPIC_RESAMPLED_VALIDATION.md` | the prespecified topic-resampled plan |
| `dci1/reports/dci1v8dev/frame_aware_prescreen/prescreen_revalidation.md` | the methodology-validation record (§14's source) |
| `dci1/reports/dci1v8dev/confirmatory/V8P1_FREEZE_AND_GENERATION.md` | freeze and generation provenance |
| `dci1/reports/dci1v8dev/confirmatory_membership.{json,md}` | the membership lock |
| `CHANGES_SCIENTIFIC.md`, `RESEARCH_STATE.md` | the running scientific record |

## 20.3 Code

| path | role |
|---|---|
| `dci1/src/dci1v8dev/confirm/analysis.py` | the registered analysis stage |
| `dci1/src/dci1v8dev/confirm/report.py` | the registered final report |
| `dci1/src/dci1v7/analysis/{observations,estimators,bootstrap,intervals,spectrum,boundary,claims}.py` | the 7 bound analysis modules, hashes on every record |
| `dci1/src/dci1v8dev/confirm/{lifecycle,freeze,membership,precision}.py` | stage machine, freeze protection, multiplicity |
| `dci1/tools/v8_postconfirm_extract.py` | reads signed records → the paper's CSV/JSON |
| `dci1/tools/v8_postconfirm_spectrum_points.py` | re-forms the registered spectrum fit's input and checks it against the recorded residuals |
| `dci1/tools/v8_postconfirm_spectrum_plot.py` | draws the SPECTRUM figures from the committed tables; asserts the drawn fit reproduces the record's prediction |

## 20.4 Manuscripts

| file | status |
|---|---|
| `~/Downloads/v8_1_source/main_v8_1_preconfirm.tex` (+ `v8_1_source.pdf`) | **the rewrite base**: correct design, pre-confirmatory results |
| `~/Downloads/lp4fm_source/main_lp4fm.tex` | alternative framing; harvest the prompt-sensitivity related work |
| `~/Downloads/neurips-4.pdf` (`neurips-4(1).pdf`) | **superseded development evidence**; narrative shape only, no numbers |
| `/home/cnm13ryan/git/dci/V8_1_PAPER_REWRITE_BUNDLE.md` | the pre-confirmatory bundle this one supersedes for results |

## 20.5 Reproducing the analysis

```bash
cd /home/cnm13ryan/git/dci-v8-topicrep/dci1     # clean worktree at 034fc72
for m in qwen3-4b qwen3-4b-instruct-2507 gemma-3n-e2b-it gemma-3n-e4b-it; do
  .venv/bin/python -m dci1v8dev.confirm.cli run --stage CONFIRMATORY_ANALYSIS \
     --model $m --root <repo>/dci1/evidence/dci1v8p1-confirm
done
cd <repo>/dci1
python3 tools/v8_postconfirm_extract.py \
    --root evidence/dci1v8p1-confirm --out reports/dci1v8dev/postconfirm/data
```

The stage is write-once: a second `CONFIRMATORY_ANALYSIS` on the same root is
refused by the lifecycle. Re-running requires a fresh root and re-generation.
