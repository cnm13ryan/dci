# Experiment coverage matrix — what has actually been tested

Reconstructed by `coverage.py` from `runs/*/config.json`, not from the
write-ups, because the write-ups are what is being audited. Regenerate with:

    uv run --project . python coverage.py

**Scope.** 27 runs, 13,624 generations, Rounds 1–5. Legend: **✔** tested,
**◐** partially tested (one level only, or confounded with another factor),
**✘** not tested.

---

## 0. The check that mattered most: are **q** and **N** crossed?

* **q** = the number of semicolons the *arm* demands.
* **N** = the number of sentences the *target* demands.

A per-sentence rule ("a semicolon in every sentence") has **no free q**: it
demands one per sentence, so q is pinned to N by construction. Only a
whole-answer floor ("at least q semicolons in the answer") lets q vary
independently.

**Run-cells by (q, N), semicolon-demanding arms only:**

| q ↓ / N → | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|
| **1** | ✘ | ✘ | ✘ | ✘ | ✘ |
| **2** | 1 *(pinned)* | ✘ | **2** *(free)* | ✘ | ✘ |
| **3** | ✘ | 1 *(pinned)* | ✘ | ✘ | ✘ |
| **4** | ✘ | ✘ | **24** (21 pinned, 3 free) | ✘ | ✘ |
| **5** | ✘ | ✘ | ✘ | 1 *(pinned)* | ✘ |
| **6** | ✘ | ✘ | **1** *(free)* | ✘ | 1 *(pinned)* |

Restricted to a **free** q (whole-answer floor), the entire grid is one column:

| q | N=2 | N=3 | **N=4** | N=5 | N=6 |
|---|---|---|---|---|---|
| 2 | ✘ | ✘ | 2 | ✘ | ✘ |
| 4 | ✘ | ✘ | 3 | ✘ | ✘ |
| 6 | ✘ | ✘ | 1 | ✘ | ✘ |

### Consequence, applied

**The claim "the threshold sits at about the target sentence count" is
UNIDENTIFIED and is withdrawn from the report as stated.** Free q was varied only
at N = 4, where q ≥ 4 and q ≥ N and q/N ≥ 1 are the same hypothesis. The E4b
data (q=2 → 0.20, q=4 → 0.975, q=6 → 0.99) are equally consistent with:

1. an absolute threshold at q ≈ 3–4, independent of N;
2. a ratio threshold at q/N ≈ 1;
3. a boundary at q = N.

Nothing in the corpus separates them. The N-sweep (E3) does not help, because it
moves N and q **together** along the diagonal. This is what Experiment A exists
to fix, and it is the highest-priority gap in the programme.

---

## 1. Model

| model | id | runs | N tested | q tested | backgrounds | wordings | splits | status |
|---|---|---|---|---|---|---|---|---|
| Qwen3-4B-Instruct | `Qwen/Qwen3-4B-Instruct-2507` @ `cdbee75f` | 26 | 2,3,4,5,6 | 0,2,3,4,5,6 | 7 | 0, 2 | pilot, burned | ✔ |
| Gemma-2-9B-it | `google/gemma-2-9b-it` @ `11c9b309` | 1 | **4 only** | 4 only | **1 only** | 0 only | pilot only | ◐ |
| Qwen3.5-4B | — | 0 | — | — | — | — | — | ✘ |
| Qwen3.5-9B | — | 0 | — | — | — | — | — | ✘ |
| Qwen3.6-* | — | 0 | — | — | — | — | — | ✘ **blocked, see §11** |

Everything about gemma rests on **one run, one cell of every other factor**. The
cross-model conclusion is therefore a comparison of a 26-run surface against a
single point.

---

## 2. Target constraint and parameter N

| target | rule | N | runs | status |
|---|---|---|---|---|
| `A` | exact sentence count | 4 | 22 | ✔ |
| `X_A2` / `X_A3` / `X_A5` / `X_A6` | exact sentence count | 2/3/5/6 | 1 each | ◐ one run each, one background, one wording, Qwen only |
| `X_PARA4` | exact paragraph count | 4 | 1 | ◐ |
| `U_NUM_FOURDISTINCT` | four distinct integers | — | 1 | ✘ **unusable**: fails 0.725 unaided |
| bullets / list items | — | — | 0 | ✘ |

---

## 3. Arm: mark × scope × dose

| mark | per-sentence | whole-answer floor (≥q) | whole-answer exact (=q) |
|---|---|---|---|
| semicolon | ✔ q=2,3,4,5,6 (all pinned to N) | ◐ q=2,4,6 **at N=4 only** | ◐ q=2 (`U_FMT_SEMI2`), N=4 |
| colon | ✔ N=4 | ◐ q=4, N=4 | ◐ q=1 (`U_FMT_COLON1`, used as background) |
| dash | ✔ N=4 | ◐ q=4, N=4 | ✘ |
| comma | ✔ N=4 (q=1 and q=2 forms) | ◐ q=4, N=4 | ✘ |
| none (`C_L3`, `C_W3`, `B`, `C_O2`) | ✔ | — | — |

**Missing:** q ∈ {1, 3, 5} at *any* N; every non-semicolon mark at any N ≠ 4;
every whole-answer floor at any N ≠ 4.

---

## 4. Instruction order

✔ **Fully crossed.** Every one of the 27 runs used both `o_A` and `o_Q`. No run
tested a single order, and no cell is order-confounded.

---

## 5. Background set

| background | runs | arms measured |
|---|---|---|
| *(none, load k=2)* | 1 | B, C_L3, C_O2, C_W3, S_SEMICOLON |
| `U_LEX_FORBID3 + U_NUM_MAXINT + U_FMT_COLON1` | 12 | the modal set |
| `U_LEX_FORBID3 + U_NUM_MAXINT + U_FMT_PAREN1` | 3 | E4, E4b, E4c |
| `U_LEX_FORBID3 + U_FMT_COLON1 + U_LEX_NOLY` | 1 | E5b |
| `U_LEX_FORBID3 + U_NUM_MAXINT + X_NO_{EXCLAM,SEMI_SPLICE,COMMA_SPLICE}` | 3 | E7 |
| `U_LEX_FORBID3 + U_FMT_COLON1 + X_NO_{…}` | 3 | E7c |
| `U_FMT_COLON1 + U_LEX_ALLIT_P + U_NUM_FOURDISTINCT` | 1 | Stage A5 (withdrawn: content-dictating) |
| default rule for a paragraph target | 1 | E5a |

✔ Well covered for Qwen — 7 distinct sets — and this coverage is what produced the
background-conditionality finding. ✘ Not varied at all for gemma.

**But the 2×2 that would identify the B × colon interaction has never been run.**
The corpus contains `A + B + colon-background` and `A + B + paren-background` in
separate runs, but never the clean four cells `A`, `A+B`, `A+C`, `A+B+C` in one
matched design. See Experiment B.

---

## 6. Wording

| wording index | runs | note |
|---|---|---|
| 0 | 26 | the default |
| 2 | 1 (E2b) | ◐ single replication |
| 1, 3, 4, 5 | 0 | ✘ |
| 6, 7 | 0 | permanently held out for Gate 3b — correctly untouched |

Arm-wording was additionally varied *within* E4 (`X_SEMICOLON_EACH` vs the
registry's `S_SEMICOLON`), which is a stronger control than a second paraphrase
index and came out indistinguishable.

---

## 7. Task / topic split

| split | runs | n_tasks |
|---|---|---|
| pilot (PLT01–20) | 25 | 4 or 20 |
| burned (BRN01–20) | 1 (E2a) | 20 |
| screening / calibration / wording / confirmatory | 0 | ✘ correctly untouched — reserved for the confirmatory study |

Task offset was never used other than 0; the 20 pilot topics are the same 20 in
every pilot run, so runs share sampling variation on the topic axis.

---

## 8. Decoding configuration

| parameter | values tested | status |
|---|---|---|
| temperature | **0.7 only** | ✘ **never varied** |
| top_p | **0.9 only** | ✘ never varied |
| top_k | 0 only | ✘ never varied |
| do_sample | True only | ✘ **greedy never tested** |
| max_new_tokens | 180 (Stage A, withdrawn as cap-limited), 512 | ◐ |
| dtype | bfloat16 only | ✘ |

**This is the second-largest untested dimension.** Every result in the programme
is at one sampling configuration. Whether the clause-chain is a mode of the
distribution or an artefact of sampling at T=0.7 is not known. A greedy run is
nearly free and would settle it.

---

## 9. Replicates and seeds

| | value |
|---|---|
| replicates per (task, arm, order) | 2 (most runs), 3 (Stage B) |
| base seed | 20260810 in every run |
| batch seed | `base_seed + batch_index`, deterministic from row-id ordering |
| clusters for the bootstrap | 20 tasks |

◐ **One base seed throughout.** Replicates vary the sample within a run, but no
run has been repeated under a different base seed, so seed-level variance is
unmeasured. The four independent replications of the N=4 `S_SEMICOLON` cell
(Stage B, E1, E3-N4, E4c) share the seed but differ in run, batching and
replicate structure, which is weaker than a true seed replication and stronger
than nothing.

---

## 10. Scaffolds and interventions

| condition | runs | status |
|---|---|---|
| no scaffold | 25 | ✔ |
| `one_sentence_per_line` | 2 (D2, E1) | ✔ but **withdrawn as an instrument** |
| `weak_reminder`, `sham_plain_style` | 1 (E1) | ✔ |
| prohibition as a numbered instruction | 6 (E7, E7c) | ✔ ran, ✘ **manipulation check failed** |

---

## 11. Models requested but not runnable

Verified against the Hub on 2026-08-11.

| model | exists | params | bf16 weights | verdict |
|---|---|---|---|---|
| `Qwen/Qwen3.5-4B` | ✔ public | 4,659,865,088 | ≈ 9.3 GB | **runnable** — fits one 24 GB GPU |
| `Qwen/Qwen3.5-9B` | ✔ public | 9,653,104,368 | ≈ 19.3 GB | **runnable** — fits one 24 GB GPU |
| `Qwen/Qwen3.6-27B` | ✔ public | 27,781,427,952 | ≈ **55.6 GB** | **BLOCKED** — exceeds 48 GB total VRAM (2 × 25.75 GB) |
| `Qwen/Qwen3.6-35B-A3B` | ✔ public | 35,951,822,704 | ≈ **71.9 GB** | **BLOCKED** — same reason |

Notes recorded rather than worked around:

* The Qwen3.5/3.6 line drops the `-Instruct` suffix; the plain id **is** the
  instruct model and `-Base` marks the base model. `Qwen/Qwen3.5-4B-Instruct`
  does not exist (HTTP 401), and no substitution was made silently.
* Both Qwen3.6 sizes ship FP8 and GPTQ-Int4 variants that would fit. Neither is
  used: **gfx1100 (RDNA3) has no FP8 tensor support** in this torch/ROCm build,
  and the Int4 path would require a GPTQ runtime that is not installed and would
  change the numeric condition, making the comparison with the bf16 runs
  uninterpretable. **A quantised stand-in would not answer the question asked.**
* `transformers` 5.15.0 registers `qwen3_5` and `qwen3_5_moe`, so the 3.5 models
  load without a custom architecture.

**Therefore: Qwen 3.6 cannot be tested on this hardware, at any size, in the
numeric condition the rest of the study uses.** This is a hardware blocker, not a
scientific decision.

---

## 12. Summary — the ranked gaps

| # | gap | consequence | cost |
|---|---|---|---|
| **1** | **q × N never crossed** | the threshold claim is unidentified | low |
| **2** | **B × colon 2×2 never run** | the headline DCI result's status is undetermined | low |
| **3** | **gemma tested at one cell of every factor** | the cross-model claim rests on one point | low |
| **4** | **decoding never varied** | the whole programme is at one sampling configuration | very low |
| **5** | newer Qwen generations untested | cannot separate "Qwen family" from "this checkpoint" | medium (download) |
| 6 | one base seed throughout | seed variance unmeasured | low |
| 7 | q ∈ {1,3,5} untested anywhere | the dose curve has three points | folded into gap 1 |
| 8 | non-semicolon marks only at N=4 | mark-specificity is an N=4 statement | medium |
| 9 | numerical-family target unusable | no cross-family evidence | low (needs a new target) |


---

## 13. Round 6 update — gaps 1, 2, 3 and 5 closed

| gap | status after Round 6 |
|---|---|
| **1. q × N never crossed** | **CLOSED.** `R6A_N{2,3,4,5,6}` × `X_SEMICOLON_TOTAL{1..6}` — a full 6 × 5 grid with free q at every N, plus two q = 0 controls. 3,560 generations. |
| **2. B × colon 2×2 never run** | **CLOSED.** `R6B_load2` / `R6B_load3` give all four cells with an inert filler for count-matching. 920 generations. |
| **3. gemma at one cell only** | **PARTLY CLOSED.** Four models now run the identical battery. Still one cell of N, background, wording and split per non-Qwen model. |
| **5. newer Qwen generations** | **CLOSED for 3.5** (`Qwen3.5-4B`, `Qwen3.5-9B`); **BLOCKED for 3.6** — see §11, unchanged. |
| **4. decoding never varied** | **STILL OPEN**, and now the top remaining gap. |
| 6. one base seed | still open |
| 8. non-semicolon marks only at N = 4 | still open |
| 9. numerical-family target unusable | still open |

### A new coverage dimension Round 6 forced into existence: **reasoning mode**

| model | template default | run under |
|---|---|---|
| Qwen3-4B-Instruct-2507 | no thinking block | default |
| Gemma-2-9B-it | no thinking block, **no system role** | system merged into first user turn |
| Qwen3.5-4B / 3.5-9B | **opens `<think>` by default** | `enable_thinking=False` (the model's own non-thinking mode) |

The first Qwen3.5-4B run was made under the template default and is **invalid**:
the 512-token budget went to a reasoning trace, giving 36 "sentences", 268 words
and `output_truncated=True`. It is retained as `runs/stageR6C_qwen35_4b_*` and
marked invalid. `prompt_convention` in every run summary now records which
convention produced the prompts, so no future comparison can silently mix them.


---

## 14. Round 7 update

| dimension | before Round 7 | after |
|---|---|---|
| **decoding** | T=0.7 only — the top open gap | ✔ **T = 0.0 (greedy), 0.3, 0.7** at N=4, q ∈ {0,2,3,4} |
| **order/permutation** | ✔ o_A/o_Q only — the target and one added instruction | ✔ **all six S₃ orderings** of (target, focal slot, background slot), × 2 focal occupants × 2 variants |
| **load × ordering** | ✘ | ✔ k=3 vs k=5 for the three gradient levels, two background members frozen |
| **reasoning mode** | ◐ recorded | ✔ recorded per run in `prompt_convention`; Qwen3.5 runs use the model's own `enable_thinking=False` |
| **reasoning budget** | ✘ | ✘ **not run** — see §15 |
| punctuation dose (colon) | ✘ | ✘ still open, and **reframed** by I14: the mark need not appear, so a dose grid over the mark may be the wrong probe |

New runs: `S1_Tgreedy`, `S1_Tt03` (1,040), `S2_orderings` (960), `S3_load5` (480).
Cumulative: **35 runs, ~17,600 generations, 0 technical failures.**

## 15. Stages specified but not run, with reasons

| stage | status | reason |
|---|---|---|
| **4 — reasoning budget as treatment** | **not run** | Needs a hard reasoning-budget control (`b`) and a separate reasoning/answer channel in the harness. The thinking/non-thinking *mode* distinction is implemented and recorded; a graded budget is not, and implementing it is a harness project rather than an experiment. Qwen3.5-4B/9B are available and validated for it. |
| **5 — colon anatomy** | **not run, and reframed** | Stage 2's I14 removed its original premise. A dose/scope/wording grid over the *mark* now tests the wrong thing; the live question is what property of an *instruction* makes it amplify a neighbour when its own mark need not appear. |
| **7 — structural-unit generalisation** | **not run** | Depends on a characterised mechanism; I14 reopened that. |
| **8 — DCI Pairs 1 and 2** | **not run** | Pair 1's verifiers are unimplemented in the registry and Pair 2's registered measurement risk is logical impossibility of the composition — the reason this study selected Pair 3 in Round 1. Transferring the disposition/amplification/arbitration decomposition needs pair-specific diagnostics authored first. |
| **Qwen 3.6** | **blocked, unchanged** | 27B ≈ 55.6 GB bf16 vs 48 GB total VRAM; 35B-A3B ≈ 71.9 GB. FP8 unsupported on gfx1100; Int4 would change the numeric condition. No substitution made. |


---

## 16. Round 8 update

| dimension | status |
|---|---|
| **reasoning model** | ✔ `Qwen/Qwen3.5-4B` (hybrid, 4.66 B, bf16, no quantisation) |
| **reasoning mode** | ✔ thinking / non-thinking, both native, recorded per run |
| **assigned reasoning budget** | ◐ b ∈ {0, 64, 1024, 4096, 8192} attempted; **8192 OOMs**, and 4096 is still binding in 14/16 rows |
| **realised reasoning usage** | ✔ recorded per row (`reasoning_tokens`), but **censored** — no arm/background/ordering comparison is identified |
| **reasoning-cap hit** | ✔ recorded per row |
| **colon-property variant** | ✔ four matched exactly-one variants at π = QAC, k = 3 |
| **fixed vs free placement** | ✘ **not run** — the cheapest remaining test |

New runs: `S0_smoke` (48), `S1_natural` (**invalid, 48 OOM, retained**),
`S1_natural2` (16), `S14_markproperty` (320).

## 17. Blocked, with the exact resource constraint

| item | blocker |
|---|---|
| hard-budget reasoning factorial (Stages 2–13) | Qwen3.5-4B needs > 4096 reasoning tokens in ~87% of rows; 8192 × batch 8 exceeds 24 GB VRAM. Any affordable budget interrupts rather than limits. |
| Qwen3.6 | 27 B ≈ 55.6 GB bf16 vs 48 GB total; 35B-A3B ≈ 71.9 GB. FP8 unsupported on gfx1100; Int4 would change the numeric condition. |
