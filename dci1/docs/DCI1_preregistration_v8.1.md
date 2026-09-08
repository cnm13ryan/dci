# DCI-1 protocol v8.1 — preregistration (standalone; frame-aware pre-screen)

Status: DRAFT (successor design of 2026-09-03; the successor pilot roots and
the confirmatory root of Appendix B are named when the pilots have run, and
the status becomes FROZEN-READY only when every number here and in the code
agree and the researcher's remaining decision of §10.9 is taken). This
document supersedes `DCI1_preregistration_v8.md` **for the successor design
only**: the frozen v8 root `dci1v8-confirm-r2` (2026-09-03, `f7af7f2`), its
records and its preregistration are immutable historical evidence of the
pooled-screen design and are not altered retroactively.

This document describes the experiment the code executes. It is standalone:
nothing here is defined by reference to the v7 preregistration, although §20
states where v8 departs from v7. Every rule below is executable in
`dci1/src/dci1v8dev/rules.py`, `dci1/src/dci1v8dev/run/` (the pilot layer)
and `dci1/src/dci1v8dev/confirm/` (the confirmatory layer); the confirmatory
manifest binds this file by hash, every `FROZEN` record carries that hash,
and `dci1/tests_v8dev/` fails when a number here and a number in the code
disagree. Where a constant is named in code font it is the constant the code
reads; a prose restatement never overrides it.

## 1. Binding and scope

- **Protocol:** DCI-1 v8.1, `PROTOCOL_VERSION = "8.1-confirmatory"` (pilot
  layer `"8.1-pilot"`), Approach A (the wording frame is part of the
  experimental condition), with the frame-aware pre-screen of §10.
- **Bound by:** the confirmatory registration manifest
  (`confirm/manifest.py::build_manifest`, field `preregistration.hash`) and
  every `FROZEN` record (`confirm/freeze.py`, field `preregistration`).
- **Layers:** the pilot layer (`dci1v8dev.run`, nine stages, generates solo,
  unconstrained and counterfactual-chance cells only, never a composed cell)
  and the confirmatory layer (`dci1v8dev.confirm`, seven stages:
  `CONFIRM_REGISTERED → LOCAL_TOPUP → MEMBERSHIP → FROZEN →
  CONFIRMATORY_GENERATION → CONFIRMATORY_ANALYSIS → FINAL_REPORT`). A
  composed cell (two instructions in one prompt) exists only under
  `CONFIRMATORY_GENERATION`, after a signed freeze.
- **What v8 is:** a frame-conditioned redesign of DCI-1, not a replication
  of v7. v7 pooled the four wording frames, selected one operating point,
  one reference set and one Δ_R per model, and rendered the two lines of a
  composed prompt under different frames in three blocks of four. v8
  conditions every quantity on the frame, renders both lines of a composed
  prompt under the block's frame, and changed two of the four exact-count
  templates (§6). v7's evidence stands as historical evidence of the pooled
  design; nothing in it is re-read as a v8 result.
- **What v8.1 changes over v8:** the pre-screen, the second pass and the
  forwarding decision are per wording frame at the pooled screen's budget
  per frame (§10). No threshold, caliper, band, operating-point rule,
  validity component, reference library, prompt, verifier, calibration
  allocation or confirmatory allocation changes. The v8 pilot roots
  (r9, r10, r12, r13) and the frozen v8 root are evidence of the pooled
  design and enter no v8.1 verdict (§10.6).

## 2. Research question

Within a fixed reasonable wording frame f, does the target companion
instruction A cost the focal instruction B more compliance than matched
reference companions of comparable difficulty do? Secondarily, within a
frame, does B's loss under A sit where B's loss under companions of A's
difficulty would predict (the difficulty relation)?

## 3. Estimands

All quantities are formed **per model, per frame f ∈ {0, 1, 2, 3}, per
configuration** (`C.CONFIGURATIONS`: `outcome_first`, the outcome
instruction stated first in the prompt; `outcome_second`), from one
observation table per frame built from that frame's confirmatory blocks.
Every estimator is a per-block quantity averaged over blocks
(`dci1v7/analysis/estimators.py`).

- **Difficulty coordinate.** For an instruction X under frame f,
  `ι(X, f) = (p(X, f) − κ(X, f)) / (1 − κ(X, f))`, where p is the solo
  compliance rate and κ the rate at which the verifier for X passes an
  answer written under **no** instruction (the unconstrained cell of the
  same topic under the same frame). κ is measured on the same unconstrained
  cell for A and for every reference (§11.3). ι is undefined when κ ≥
  `CHANCE_DEGENERACY_MAX` = 0.99 (`DIFFICULTY_COORDINATE_DEGENERATE`).
- **Delivery loss.** `D(c ← g) = solo(c) − composed(c, g)`: the fall in c's
  compliance when g is stated alongside it.
- **Primary estimand, Δ_R(f).** With R1, R2, R3 the frozen core references
  of frame f (§14): `Δ_R(f) = mean_j P(B | B+R_j) − P(B | B+A)` inside each
  block (the cancelled form; the definitional form `D(B←A) − mean_j D(B←R_j)`
  agrees to `ALGEBRAIC_FORM_TOLERANCE` = 1e-9 and is asserted). Positive
  Δ_R(f) means A costs B more than matched companions do, under frame f, at
  the frozen operating points n*(f), m*(f) and the frozen triple.
- **Order asymmetry.** `Λ = D(B←A) − D(A←B)`.
- **Specificity.** `Ξ = Δ_R − [D(R̄←A) − D(R̄←R̄′)]`, with
  `D(R̄←g) = mean_j D(R_j←g)` and `D(R̄←R̄′)` the mean over the six ordered
  pairs of distinct references.
- **Difficulty relation, δ_difficulty(f).** `δ = D(B←A) − [ᾱ + β·ι_A]`,
  where `α_family + β·d` is fitted by ordinary least squares on the frame's
  selected spectrum points (§13; A excluded), with one intercept per family,
  a common slope β, and ᾱ the mean of the family intercepts. β is the §11.8
  slope. Degenerate points (κ ≥ 0.99) are dropped and the drop recorded.
- **Order contrasts.** `Ord_A`, `Ord_B`, `Ord_Λ = Ord_B − Ord_A`, `Ord_R̄`
  across the two configurations (family F11).
- **Reference-sensitivity contrast.** Δ_R(f) re-formed over every
  structurally admissible triple drawn from the five frozen families
  {R1..R5} (§14.4), from the same cells.
- **Runner-up sensitivity contrast.** Δ_R(f) re-formed at the runner-up
  operating point where §11.4 declares the frozen point unstable.
- **Model-level statement.** A LOCAL statement about a model is the
  conjunction over its entering frames (§18.5); no at-least-one-frame
  statement exists.

## 4. The instructions A and B

- **A (target).** The exact-count marker instruction on the word
  *however* (`TARGET_WORD = "however"`, family kind `A`, contrastive
  discourse role, verifier `words.count_marker` under §9.2's lexical rule).
  Severity grid `TARGET_GRID` = 1..8 (the required count n). Selection band
  `TARGET_BAND` = (0.50, 0.85) on raw solo compliance, aim
  `TARGET_AIM` = 0.70.
- **B (focal).** Every word in the answer has at most m letters (verifier on
  the longest word; m ≥ 7 because *however* has seven letters). Grid
  `FOCAL_GRID` = 7..14, extension `FOCAL_EXTENSION` = (15, 16), band
  `FOCAL_BAND` = (0.60, 0.95), aim `FOCAL_AIM` = 0.80. B's four wordings are
  v7's, unchanged: *Every word in the answer must have at most {m}
  letters.* / *Use only words of {m} letters or fewer.* / *Do not use any
  word longer than {m} letters.* / *No word in your answer may exceed {m}
  letters.*
- **Prompt.** Every prompt is a topic question from the bank (§9) with the
  stem *Answer in 60 to 120 words.* and zero, one or two instruction lines
  (loads 0, 1, 2). Load-2 prompts state the two instructions in the order
  the configuration names.

## 5. The reference families

`dci1v7/verifiers/constraints.py::FAMILIES` (37 selectable families; three
probe-only families PS1–PS3 are never selectable):

- **Tier 1** (exact count, production, each its own feature group, ladder
  1..8): MK1 *thus* (consecutive), MK2 *hence* (consecutive), MK3 *though*
  (contrastive), MK4 *whereas* (contrastive), MK5 *indeed* (emphatic), MK6
  *namely* (exemplifying), MK7 *instead* (substitutive), MK8 *overall*
  (summative). These share A's four templates (§6) with the marker
  substituted and are scored by the same counter as A.
- **Tier 2** (exact count, production, role none): XC1 semicolons (1..8),
  XC2 commas (2, 4, …, 16), XC3 sentences (3..10).
- **Tier 3** (budgets, role none): RF1–RF12 count budgets, CR1–CR12 rate
  budgets, CL7–CL8 count lower bounds. Tier 3 is admissible in no v8 slot
  (the near-form and class arms are not run, §20).
- **Core slot admissibility:** tiers 1 and 2 only (`SLOT_CORE`). A core
  triple needs three distinct feature groups, at least
  `MIN_TIER1_CORE` = 2 Tier-1 members and at least
  `MIN_CORE_DISCOURSE_ROLES` = 2 declared discourse roles (§14.1).

## 6. Wording frames and exact templates

Four frames, `N_WORDINGS` = 4. For A and MK1–MK8 (`V8_FRAMES`,
`dci1v8dev/wording_v8.py`; `{s}` is empty when q = 1):

| f | template |
|---|---|
| 0 | `Use the word {X} exactly {q} time{s}.` |
| 1 | `Your answer must contain the word {X} exactly {q} time{s}.` |
| 2 | `Include the word {X} exactly {q} time{s} in your answer.` |
| 3 | `The word {X} must appear exactly {q} time{s}.` |

Frames 0 and 3 are v7's; frames 1 and 2 gained exactly the two tokens *the
word* (v7's read *…contain {X} exactly…* and *Include {X} exactly…*), a
repair adopted after the 2026-08-29 wording audit showed the v7 phrasing
was read as a substring instruction. Every other family's templates are
v7's with grammatical number made correct at q = 1 (byte-identical at every
other severity). B's templates are unchanged. The wording instrument is
hashed (`v8_wording_source_hash`) and the hash is on every record; a
freeze refuses a record whose hash differs from the pilot's (§19).

## 7. Experimental unit and frame conditioning

- **Unit.** A **block** is one topic under one frame. Every cell of a block
  (unconstrained; every solo instruction; every composed pair in both
  orders) is rendered under the block's frame — every stated line of a
  load-2 prompt under the same frame (`confirm/design.py::
  assert_frame_allocation`; a slot under another frame is refused at
  rendering). Frame f of block index i is `i mod N_WORDINGS`.
- **Draws.** Each cell is generated `M_DRAWS` = 8 times (confirmatory) or
  `M_CAL` = 4 times (calibration) at distinct scientific seeds; estimators
  average draws within a cell first, so the independent unit is the block.
- **Frames are never pooled.** Every difficulty, operating point, validity
  verdict, reference set, spectrum set, estimate, interval and reading is
  frame-specific. Frames are compared or combined only after the
  frame-specific estimates exist, and only by the rules in §18.

## 8. Model checkpoints, backend, decoding, seeds

- **Study models** (`dci1v4/models/registry.py::MODELS`, revisions pinned):
  `gemma-3n-e2b-it` = google/gemma-3n-E2B-it @ 5e092ebc…; `gemma-3n-e4b-it`
  = google/gemma-3n-E4B-it @ c1221e9c…; `qwen3-4b` = Qwen/Qwen3-4B @
  1cfa9a72… (thinking disabled); `qwen3-4b-instruct-2507` =
  Qwen/Qwen3-4B-Instruct-2507 @ cdbee75f…. Each model is one replication;
  nothing pools across models.
- **Backend.** vLLM 0.15.1 (vendored ROCm 7.2 wheel, sha256 recorded in
  `environments/backend/vendor/MANIFEST.sha256`), torch 2.9.1+rocm7.2,
  Python 3.12, one card per replication (TP = 1, bfloat16, max model length
  4096, eager mode, no quantization). Every stage record carries an
  environment block naming the backend packages actually installed
  (`run/lifecycle.py::environment_record`).
- **Decoding** (`dci1v4/generation/backend.py::build_plan`): temperature
  0.7, top-p 0.9, top-k 50, no thinking mode, maximum new tokens = the
  selected completion cap (§10.1). The decoding policy form is bound in the
  manifest.
- **Seeds** (`dci1v8dev/run/seeds.py`): `GENERATION_ROOT_SEED` = 202608240;
  a generation seed is `domain_int("dci1v8:gen:v1", root, stage, model_id,
  prompt_hash, draw_index)` and travels on the row; a bootstrap seed is
  `domain_int("dci1v8:boot:v1", 202608241, estimand, model_id)`; the screen's
  Monte-Carlo seed is `domain_int("dci1v8:screen:v1", 202608241, model_id,
  stage)`. No seed has a hidden default; Python's builtin `hash()` seeds
  nothing (tested).
- **Reproducibility of text.** Fixed seeds make every prompt, seed, verdict
  and analysis reproducible **as data**. Bit-for-bit reproduction of the
  generated text on this vLLM/ROCm stack is **not** promised: measured on
  2026-09-02 (`reports/dci1v8dev/freeze_readiness/backend_determinism.md`),
  two fresh runs of 96 rows under identical plan and seeds agreed on 94
  rows, and each agreed with the pilot's own stored rows (generated inside
  a larger batch) on 66. Every planned row is accounted for by identity
  (`row_accounting`), so a re-run reproduces the design and the analysis of
  the stored rows, not the sampling.

## 9. Topic splits and the calibration allocation (universal)

- **Bank.** 720 topics in six areas (`TOPICS_PER_AREA` = 60), split once
  under `CARRIED_TOPIC_SPLIT_SEED` = 202608192 into `prescreen` (24),
  `calibration_a` (96), `calibration_b` (96), `composed` (24),
  `confirmatory` (384) and `sequestered` (96). The split identity (per-set
  hashes and counts) is bound in every manifest. `composed`, `confirmatory`
  and `sequestered` are reserved: no pre-freeze stage may spend one of their
  topics (`assert_no_reserved_topic_spent`); the confirmatory design spends
  every `confirmatory` topic and nothing else.
- **Calibration allocation, universal.** `CALIBRATION_FRAME_OFFSETS =
  (0, 1, 2, 3)` for every study model: a calibration pass renders every
  calibration topic under one frame, pass p shifting the frame by its
  offset, so every frame is measured on all `N_CALIBRATION` = 192 topics,
  96 from each of the two splits (§12's stability split). This is the
  ceiling (a fifth pass would repeat a topic within a frame). There is no
  per-model override (`CALIBRATION_POLICY`); a model whose pilot Gate 2 was
  measured at any other allocation cannot be frozen (§19.1 item 3).
  *History:* two passes (96 topics per frame) were adopted on 2026-08-30;
  on 2026-08-31 the two Qwen models were raised to four passes through a
  per-model table while the two Gemma models stayed at two — a
  model-specific decision taken after seeing reference survival on the
  study checkpoints. The audit of 2026-09-02 replaced the table with this
  universal value before any further calibration was generated; the Gemma
  models are re-measured on fresh pilot roots and every model's
  eligibility is recomputed on the same basis.

## 10. Pre-screen, second pass and retention

The pilot layer's nine stages, per model, in order (`run/stages.py`):
`PILOT_REGISTERED` (sign the pilot manifest), `QUALIFIED` (clean tree,
hashable commit, resolved revisions, schema-valid plan, structural suite,
wording equivalence, presence rule, composed-cell refusal at the renderer),
`GATE_0_APPARATUS` (12 topics × 4 draws, loads 0 and 1),
`REGIME_SCREEN`, `SECOND_PASS_SCREEN`, `GATE_1_INSTRUMENT`,
`GATE_2_CALIBRATION`, `GATE_3_REFERENCES` (no generation), `PILOT_REPORT`.

1. **Completion cap** (`REGIME_SCREEN`): the smallest of
   `COMPLETION_CAPS` = (512, 768, 1024) whose truncation share over
   `CAP_SELECTION_PROMPTS` = 96 prompts is under
   `CAP_TRUNCATION_MAX` = 0.10; none → `RESPONSE_LENGTH_INCOMPATIBLE`.
2. **First-pass screen** (`REGIME_SCREEN`): every selectable family's
   round-0 ladder, A's grid, B's grid and one unconstrained cell on the 24
   `prescreen` topics × 1 draw, laid out **one pass per frame offset**
   (`SCREEN_FRAME_OFFSETS` = (0, 1, 2, 3); `regime.screen_blocks`, the
   construction of §9's calibration passes): every topic under every
   frame, 96 blocks, `SCREEN_TOPICS_PER_FRAME` = 24 distinct topics per
   frame, no topic twice inside a frame (asserted on the generated rows).
   **Per frame**, on the frame's own blocks (chance on the frame's own
   unconstrained cells), the screen computes per family the posterior
   probability of supporting both sides of the frame's own screen-proxy
   ι_A(f) (§12.3's selection re-run inside every draw); `SCREEN_ACCEPT` =
   0.80 / `SCREEN_REJECT` = 0.20 bound the middle band. Readings unchanged:
   *eligible* (raw solo in [0.10, 0.90], vacuity ≤ 0.10, coordinate
   defined), *local-admissible* (adds κ ≤ 0.75 and lift ≥ 0.20),
   *spectrum-admissible* (same, on the guard band [0.10, 0.95]). The
   frame-pooled counts and screen are recorded as the legacy comparator
   and steer nothing.
3. **Second pass** (`SECOND_PASS_SCREEN`; `prescreen/rescreen.py::
   run_rescreen_by_frame`): per frame, every family that frame's own
   screen left in the middle band, its measured rungs plus at most
   `RESCREEN_RESERVE_PICKS_PER_BATCH` = 2 reserve severities in the
   frame's own deficient direction, plus A's grid; the batch is the union
   of the frames' plans (provenance `requested_by_frames`), rendered under
   every frame on 24 fresh `calibration_a` topics per batch (two per area;
   one pass per frame offset, so 24 topics per frame per batch), and
   absorbed by every frame on its own blocks as fresh topics
   (`RESCREEN_BATCH_LAYOUT` = `topics`, declared). At most
   `RESCREEN_MAX_BATCHES` = 3 batches in the sequence; a family still
   undecided at the maximum is resolved per frame by posterior majority
   (`RESCREEN_FINAL_ACCEPT_AT` = 0.50) and recorded `AMBIGUOUS_AT_MAX`.
   The record carries each frame's final table, a *provisional* frame-aware
   plan against the frame's screen-proxy ι_A(f) and the legacy pooled
   *comparator* plan; neither decides.
4. **Forwarding** (`run/calibration.py::FORWARDING_RULE`; `RETENTION_POLICY`
   = `frame_aware`, `RETENTION_TARGET_BASIS` = `calibration_iota_a`): at
   `GATE_2_CALIBRATION`, after the grids fix n\*(f), m\*(f) and ι_A(f)
   (§11) and **before any candidate cell is generated**, each supported
   frame's final second-pass evidence is screened against
   `screen.coordinate_target(ι_A(f), SE)` — the frame's own coordinate at
   the topic-level SE of A's per-topic solo at n\*(f) — and retained by
   `prescreen/retention.py` with the unchanged budgets: at most
   `RETENTION_MAX_SPECTRUM_FAMILIES` = 8 spectrum families ×
   `RETENTION_SPECTRUM_RUNGS` = 5 roles (`HARD_EXTREME`,
   `INTERMEDIATE_HARD`, `NEAR_A`, `INTERMEDIATE_EASY`, `EASY_EXTREME`),
   `RETENTION_MAX_LOCAL_FAMILIES` = 12 local families ×
   `RETENTION_LOCAL_RUNGS` = 4 rungs, admissibility ≥
   `RETENTION_ADMISSIBLE_MIN` = 0.50, `LOCAL_LABEL_MIN` = 0.25, the class
   and near-form arms, feature-group diversity first. Frame f's set is a
   function of frame f's evidence and frame f's ι_A(f) alone
   (`tests_v8dev/test_frame_aware_prescreen.py`). The union of the frames'
   sets is generated in one run, each rung on the blocks of the frames
   whose evidence selected it (`selected_by_frames` on the record); each
   frame's §13.11 table holds its own set only; an unsupported frame
   generates no candidate cell. The extension round (§10.8) runs per frame
   on the frame's blocks. ι_A(f) is A's solo coordinate on grid rows: no
   candidate, no composed quantity and no other frame enters it, so the
   forwarding has no cycle (`docs/V8_FRAME_AWARE_PRESCREEN.md`).
5. **Comparator arms (pilot only; admit nothing).** The legacy pooled
   set (`RETENTION_COMPARATOR` = `legacy_pooled`: the pooled counts with
   every batch absorbed by the legacy inference, screened and retained by
   the pooled rule) and the provisional screen-proxy set, minus the
   frame's own set, are generated on the frame's blocks into
   `comparator_rows`, never into the frame's table. `GATE_3_REFERENCES.
   retention_comparison` re-verdicts each comparator policy's set by the
   same kernel on the same rows beside the frame's own verdict, and
   reports each policy's LOCAL eligibility. The comparison is descriptive;
   the frame's verdict rests on its own set.
6. **What the replay on the v8 roots established** (`reports/dci1v8dev/
   frame_aware_prescreen/prescreen_feasibility.md`): on six pre-screen
   topics per frame a frame-aware screen keeps 79–85 % of the calibrated
   LOCAL-valid rungs and 60 % of the SPECTRUM-valid ones and is as unstable
   under topic resampling as the pooled rule subsampled to six topics — the
   noise is the sample size, not the frame — which is why every frame is
   given the pooled screen's budget (item 2) and why the successor pilots
   carry the comparator arms (item 5). The v8 pilot roots are evidence of
   the pooled design; nothing in them is re-read as a v8.1 result.
7. **Instrument diagnostic** (`GATE_1_INSTRUMENT`): per-frame wording
   diagnostic (exact compliance, κ, ι, SE, cross-frame comparison) on the
   screen rows; §7.5 equivalence; scorer determinism; hashes frozen.
8. **Extension** (`GATE_2_CALIBRATION`, one round, per frame): a side of A
   is reach-deficient below `EXTENSION_P_REACH` = 0.80 on the frame's own
   table against ι_A(f); at most `EXTENSION_CALIBRATION_PICKS` = 2 reserve
   rungs per deficient side are calibrated on that frame's blocks. Every
   rung any policy could forward and every candidate family's reserve are
   declared as scored instances on the grids (a scoring obligation, no
   generation), so the chance column and κ(R|B) of whatever is then
   measured are read on the same cells.
9. **The retention target, decided (2026-09-07).** The target of the final
   retention is Gate 2's ι_A(f) — `RETENTION_TARGET_BASIS =
   "calibration_iota_a"`, basis C — and it is **registered**. The successor
   pilots measured, on the same calibration rows, the identification
   reached by the frame's own set and by the provisional screen-proxy set
   (basis A, item 5): on all 14 supported frames of the four models the two
   bases give the same LOCAL-valid family count, the same admissible backup
   count and the same §13.15 verdict, while forwarding measurably different
   sets (Jaccard 0.63–0.97). The comparison therefore does not favour the
   proxy, and the registered basis stands on the precision argument of
   `V8_FRAME_AWARE_PRESCREEN.md` (the grid ι_A(f) carries SE ≈ 0.02 against
   the screen proxy's drift of ±0.05–0.17). Basis A remains a **comparator
   arm only**: it is generated and re-verdicted on every frame and reported,
   and it decides nothing. The evidence is in
   `reports/dci1v8dev/frame_aware_prescreen/prescreen_revalidation.md` §3.4.

## 11. Operating points, chance correction and their stability

1. **Calibration** (`GATE_2_CALIBRATION`): A's grid, B's grid (with the
   extension when §11.2 asks for it), the forwarded set and one
   unconstrained cell per block, at `M_CAL` = 4 draws, on the 192
   calibration topics under every frame (§9).
2. **Selection rule** (`dci1v7/stages/regime.py::select_operating_point`,
   applied per frame on that frame's own raw solo curves): the eligible
   severities are those whose raw solo compliance lies inside the band;
   the selected severity is the eligible one nearest the aim, ties to the
   smaller severity. n*(f) uses `TARGET_BAND`/`TARGET_AIM`; m*(f) uses
   `FOCAL_BAND`/`FOCAL_AIM`, escalating to `FOCAL_EXTENSION` only when no
   registered severity is eligible or the selection sits at the top of the
   grid. A selected severity not bracketed by measured neighbours carries
   `OPERATING_POINT_AT_GRID_BOUNDARY`. Two adjacent severities on opposite
   sides of a whole band → `GRID_RESOLUTION_INSUFFICIENT` for that frame; no
   eligible severity → `TARGET_RANGE_EXHAUSTED` / `FOCAL_RANGE_EXHAUSTED`;
   §12.4's regime adequacy (solo A in band, solo B in band, B's vacuity ≤
   0.10) → `REGIME_NOT_FOUND`. A frame that hits any of these is
   *unsupported* and takes no further part; the replication is terminal
   only when no frame is supported.
3. **Chance basis.** κ for A at n*(f), and κ for every candidate rung, is
   the pass rate of that instruction's verifier on the **unconstrained cell
   of the same topic under the same frame** (`run/calibration.py::
   _unconstrained_rate`, `frame_a_coordinate`; recorded as
   `chance_basis.cell = "unconstrained"`). A missing unconstrained cell is
   a `ProtocolError`, never a zero (tested in
   `tests_v8dev/test_chance_basis_guard.py`). *v7 defect, corrected:* v7
   recorded κ = 0 for every reference candidate through an exception
   fallback while A's κ came from a broader denominator, so v7's ι(R) was
   raw solo compliance; every v8 replay uses the corrected basis.
4. **Operating-point stability** (`confirm/stability.py`; recorded at
   `MEMBERSHIP`, frozen at `FROZEN`). For every supported model × frame the
   complete selection rule of §11.2 is re-run for n*(f) and for m*(f) on
   `OPERATING_POINT_BOOTSTRAP_RESAMPLES` = 2000 topic-level resamples of
   the frame's calibration topics (clustered: every rung's per-topic rate
   moves together; seed `bootstrap_seed("operating_point_stability:
   frame<f>", model_key)`). The record carries the empirical selection
   distribution, the share of resamples on which the frozen point is
   re-selected (`p_selected_reproduced`), the runner-up value and its share,
   and the bootstrap distribution of ι_A(f). A coordinate re-selected on
   fewer than `OPERATING_POINT_MIN_RECOVERY` = 2/3 of the resamples carries
   `OPERATING_POINT_UNSTABLE`. **The frozen n*(f), m*(f) are the ones the
   prospective rule selected on the point estimate; they are never replaced
   by the modal value, and Δ_R(f) is conditional on them.** An unstable
   coordinate on a LOCAL frame adds the runner-up arm (§17.3) so that the
   same blocks also carry Δ_R(f) at the runner-up value, reported as a
   sensitivity contrast that licenses no claim.

## 12. LOCAL validity (v7's full rule, per frame)

A candidate rung R is LOCAL-valid under frame f iff all eight components
hold on frame f's own table (`spectrum/validity.py::local_validity`,
delegating to `dci1v7/stages/validity.py`):

| component | rule |
|---|---|
| V_spec | specification complete; parse independence; wording length within `WORDING_LENGTH_TOLERANCE` = 0.20 of A's |
| V_sat | joint satisfiability and non-entailment witnesses, including a realistic witness at m*(f) |
| V_head | Wilson interval of raw solo compliance inside `HEADROOM_BAND` = (0.10, 0.90) |
| V_chance | κ ≤ `CHANCE_MAX` = 0.75, Wilson upper ≤ 0.85, vacuity ≤ `REFERENCE_VACUITY_MAX` = 0.10, lift p − κ ≥ `INSTRUCTION_LIFT_MIN` = 0.20 |
| V_struct | tier admissible in the core slot (tiers 1, 2) |
| V_inter | displacement ≤ `DISPLACEMENT_MAX` = 0.25 and projected compliance under B inside the headroom band |
| V_stab (folded) | §13.7: admissibility on each calibration split independently on (V_head, V_chance, V_inter, V_diff), and the split differences of ι and of raw solo inside ± `STABILITY_EQUIVALENCE_BOUND` = 0.20 (bootstrap, 10 000 resamples) |
| V_diff | \|ι_R(f) − ι_A(f)\| ≤ `REFERENCE_CALIPER` = 0.10, with the Newcombe region 0.05 and the secondary-coordinate caliper 0.15 |

A rung with κ ≥ 0.99 is refused at V_chance. A rung is compared only with
its own frame's ι_A(f); no cross-frame comparison exists.

## 13. SPECTRUM validity, selection and coverage (per frame)

1. **Validity** (`spectrum/validity.py::SpectrumRule`): V_spec, V_sat,
   **V_coord** (κ < 0.99; raw solo inside `SPECTRUM_GUARD_BAND` =
   (0.10, 0.95); vacuity ≤ 0.10; lift ≥ 0.20; SE(ι) ≤
   `SPECTRUM_MAX_SE_IOTA` = 0.05), V_chance, V_struct, **V_inter_s**
   (displacement ≤ 0.25; projected compliance under B inside the guard
   band; an unmeasured κ(R|B) fails), **V_stab unfolded** (§13.7 conditions
   2 and 3 verbatim; condition 1 on (V_coord, V_chance, V_inter_s) only — no
   V_diff, no headroom band), **V_pos** (\|ι − ι_A(f)\| ≥ `SPECTRUM_D_MIN`
   = 0.05). The LOCAL caliper never constrains spectrum admission
   (tested: `tests_v8dev/test_spectrum.py`). *v7 defect, corrected:* v7's
   spectrum inherited V_diff through V_stab's split admissibility and
   through drawing spectrum rungs from V_diff-passing core families only,
   so its spectrum pool spanned 0.07–0.16 in ι against ± 0.20 targets.
2. **Selection** (`spectrum/selection.py`, deterministic): per family at
   most two points aiming at ι_A(f) − `SELECTION_TARGET_BELOW` (0.20) and
   ι_A(f) + `SELECTION_TARGET_ABOVE` (0.15), at most
   `SELECTION_MAX_FAMILIES` = 4 families, points of one family at least
   `SELECTION_MIN_SEPARATION` = 0.05 apart. Selection is independent of the
   core families (a spectrum point that is the very rung of a core or
   backup reference is aliased to that slot rather than generated twice).
3. **Coverage gate** (`spectrum/coverage.py`, replaces v7's §12.6 C4): the
   selected set is *identified* iff at least `SPECTRUM_MIN_POINTS_BELOW` = 2
   points from ≥ 2 families below ι_A(f) − `SPECTRUM_OFFSET_BELOW` (0.10)
   and likewise above (+ 0.10), total span ≥ `SPECTRUM_MIN_TOTAL_SPAN` =
   0.20, every point's SE(ι) ≤ 0.05, and the slope's projected SE at the
   confirmatory allocation (§17; `spectrum/precision.py`, from the measured
   per-point SE 0.013 and block correlation 0.60 of the v7 rehearsal) ≤
   `SPECTRUM_MAX_SE_BETA` = 0.05.

## 14. Core references, backups and the reference-sensitivity plan

1. **Core triple** (`dci1v7/stages/selection.py::admit_core_references`,
   per frame): from the LOCAL-valid rungs of frame f, the three-family
   triple ranked by \|ι_R(f) − ι_A(f)\| that satisfies the structural rule
   (three feature groups; ≥ 2 Tier-1 members; ≥ 2 discourse roles). One
   rung per family. R1, R2, R3 are the frozen primary triple.
2. **Backups** (`spectrum/backups.py`): from the remaining LOCAL-valid
   families of admissible tier, the two nearest to ι_A(f) are R4, R5. A
   backup never substitutes for a core reference after the freeze
   (`BACKUPS_MAY_SUBSTITUTE_AFTER_GATE_4 = False`).
3. **Survival** (§13.15, per frame): core identified, ≥
   `MIN_QUALIFIED_FAMILIES` = 5 LOCAL-valid families, ≥
   `N_BACKUP_FAMILIES` = 2 admissible backups, on the frame's own table.
4. **Reference-sensitivity plan, pre-registered.** Because many triples are
   often admissible and their distances to ι_A(f) differ by less than the
   calibration SE (`reports/dci1v8dev/reference_sensitivity/`), the
   membership record enumerates every admissible triple over the five
   frozen families {R1..R5} (`confirm/membership.py::admissible_triples`,
   §14.1's structural rule) with every family's distance
   \|ι_R(f) − ι_A(f)\|. The confirmatory design generates R4 and R5 beside
   B (§17.3) and the analysis re-forms Δ_R(f) over every admissible triple
   as family F_REFSENS with its own simultaneous interval (§18.3). The
   frozen primary triple decides the claim; F_REFSENS reports the range of
   Δ_R(f) across triples and whether the reading (§18.4) would change on any
   of them. All five families are frozen before any composed row exists,
   and no composed outcome is read by any selection.

## 15. Frame support, model eligibility, top-up and the membership lock

1. **LOCAL_SUPPORTED** (`run/eligibility.py::local_support`): a supported
   frame f is LOCAL-supported iff §14.3's survival holds on its own table
   at its own ι_A(f). Nothing rescues a frame that does not: no threshold
   moves, no reference is borrowed from another frame.
2. **LOCAL_ELIGIBLE** (`rules.LOCAL_ELIGIBILITY_MIN_FRAMES` = 2): a model is
   LOCAL-eligible iff at least two of its frames are independently
   LOCAL-supported. **Every** supported frame of an eligible model enters
   the LOCAL arm; an unsupported frame stays on the record with the exact
   requirement it missed and enters no LOCAL analysis. A LOCAL-ineligible
   model runs no LOCAL cell on any frame.
3. **SPECTRUM entry** is per frame and independent of LOCAL standing: a
   supported frame whose selected set is identified (§13.3) enters the
   SPECTRUM arm whether or not the model is LOCAL-eligible.
4. **LOCAL_TOPUP** (`confirm/topup.py::TOPUP_RULE`, one round, before
   `MEMBERSHIP`): per supported frame f, `need(f) = max(0, 5 − |LOCAL-valid
   families on f|)`; the candidates are the Tier-1/2 rungs the first-pass
   screen measured under f whose frame-f screen ι lies within ι_A(f) ±
   0.10, from families not LOCAL-valid on f and not in **f's own**
   forwarded set (`calibration_population.by_frame[f].forwarded`); the
   top-up measures **every** candidate rung on f's own 192
   calibration topics at `M_CAL` iff `need(f) ≥ 1` and the candidate
   families ≥ `need(f)`; otherwise it measures nothing and records why.
   Gate 3 is then re-verdicted on the augmented table by the pilot's own
   kernel for every supported frame; that re-verdict, under the rules of
   this document, is authoritative for membership. On a frame the top-up
   did not touch, the LOCAL view (valid families, backups, core, support)
   must reproduce the pilot's verdict exactly or the stage fails; the
   spectrum view is recorded with both allocations (the pilot's projected
   block count and §17's) and must reproduce when they are equal.
5. **Membership** (`confirm/membership.py`): per frame, the arms, the slot
   map (A at n*(f), B at m*(f), R1..R3, R4, R5, S1..Sk with aliases, A2/B2
   where §11.4 applies), the stability record, the reference-sensitivity
   plan and the identification statuses. **Lock:**
   `tools/v8_membership_lock.py` writes
   `reports/dci1v8dev/confirmatory_membership.{json,md}` from every model's
   signed `MEMBERSHIP` record; every `FROZEN` record binds the lock's hash
   and refuses a lock that disagrees with its model's record. Membership is
   fixed prospectively: after the lock, no rule, threshold, operating point,
   reference or frame moves for any model.
6. **No model-specific exception.** Every rule above is universal. A
   near-miss after the lock is a near-miss; the only channel that could
   have added a rung is §15.4, which runs once, before the lock, by the
   stated rule.

## 16. Scope restriction

LOCAL Δ_R(f) is identified only for model × frame combinations where the
frozen screening/calibration/reference pipeline yields adequate matched
controls (§14.3) on a LOCAL-eligible model (§15.2). δ_difficulty(f) and the
slope are identified only for model × frame combinations whose selected
spectrum set passed the coverage gate (§13.3). A model × frame that enters
neither arm supports no claim; the record says which requirement it missed.
No statement generalises across frames, models, wordings outside the four
frames, instructions outside A and B, or compliance as a human would judge
it (`SCOPE_SENTENCE`).

## 17. Confirmatory allocation, arms and cells

1. **Allocation, one value.** `CONFIRMATORY_BLOCKS_PER_FRAME = 384`: every
   entering frame of every study model runs every registered confirmatory
   block (four passes, `CONFIRMATORY_FRAME_OFFSETS` = (0, 1, 2, 3); the
   ceiling), at `M_DRAWS` = 8 draws per cell, at the model's selected
   completion cap. The precision module (`confirm/precision.py`) projects
   §19.2's variance form at this allocation and chooses nothing; the
   coverage gate projects at it; the membership lock, the manifest, every
   freeze and this document state it; `tests_v8dev/test_confirmatory_
   allocation.py::test_every_active_source_of_the_allocation_agrees` fails
   if any of them disagree. *History:* 288 blocks per frame (three passes,
   2026-08-31) and a {288, 384} menu rule (2026-09-02, morning) preceded
   this value; both are superseded and recorded in `rules.py`.
2. **Arms and cells per block** (`confirm/design.py`):

   | arm | cells | contents |
   |---|---:|---|
   | base | 5 | unconstrained; A solo; B solo; A+B; B+A |
   | core (LOCAL) | 21 | R1..R3 solo; every remaining unordered pair over {A, B, R1, R2, R3}, both orders |
   | backup (LOCAL) | 6 | R4, R5 solo; B+R4, R4+B, B+R5, R5+B |
   | spectrum (SPECTRUM) | 3k | S_j solo; B+S_j, S_j+B for each non-aliased selected point (k ≤ 12) |
   | runner_up (LOCAL, §11.4) | 3 / 9 | A2 solo, B+A2, A2+B when n*(f) is unstable; B2 solo, A+B2, B2+A, R_j+B2, B2+R_j (j = 1..3) when m*(f) is |

   A LOCAL frame runs base + core + backup (+ runner_up); a SPECTRUM frame
   runs base + spectrum; a frame in both runs all. Both orders of every
   pair run in every block. The cell set of every block is asserted before
   generation and again at analysis.
3. **Generation** (`confirm/generation.py`): batches of 32 blocks per frame;
   every planned row is accounted for by identity; a batch is reused only
   from the same root; an incomplete generation is terminal
   (`GENERATION_INCOMPLETE`) and is never analysed.
4. **Scoring.** Every row is scored on every registered instance of its
   frame's slot map by the v8 verifier (`verifier_source_hash` on every
   row); a verdict carries `passed`, `graded`, `non_vacuous`,
   `vacuous_pass`, `present`, `position`, `configuration`. Every generated
   row is data: nothing downstream conditions on exact compliance or
   uptake.

## 18. Analysis (executed exactly as registered)

`confirm/analysis.py` runs once, unattended, on the frozen design; its
inputs are asserted against the freeze hash; the v7 analysis modules it
calls are hashed into the manifest and the freeze.

1. **Per frame, per configuration:** F1 (D(B←A), D(A←B), Λ, Δ_R,
   δ_difficulty, Ξ — Δ_R and Ξ only on a LOCAL frame, δ_difficulty only on
   a SPECTRUM frame), F2 (D(B←R_j), Δ_j), F3 (D(A←R_j), Δ^A), F4 (R̄
   members), F7 (reciprocal losses D(R_j←B), D(R_j←A); descriptive), F11
   (Ord_A, Ord_B, Ord_Λ, Ord_R̄; across configurations), F_REFSENS (§14.4;
   descriptive), F_SPECTRUM (the slope β with the fit's support,
   degeneracy and dropped points; descriptive), F_RUNNER_UP (§11.4;
   descriptive), F5 and F6 (§18.6).
2. **Intervals.** Block bootstrap, `BOOTSTRAP_RESAMPLES` = 10 000, one index
   draw shared by every member of a family per replicate, refit members
   (δ_difficulty, β) re-fitted in every replicate; simultaneous intervals by
   the studentised maximum-modulus construction at 95 %; `sidak_critical(k)`
   reported beside it and deciding nothing. §13.14's boundary allowance is
   applied to every contrast (structural zero; arm at a boundary widens the
   interval in the open direction by the Wilson half-width at the block
   count; compressed direction). The degenerate-replicate ceiling
   `DEGENERATE_REPLICATE_MAX` = 0.01 refuses a spectrum interval whose
   replicates dropped points more often than that.
3. **Multiplicity** (`confirm/precision.py::MULTIPLICITY_RULE`). Per
   (model, frame, configuration): F1 is the primary family (six members).
   Per (model, configuration): the **joint family** of every F1 member of
   every entering frame, its critical value from a topic-level bootstrap
   with one draw shared across frames; the joint interval is the decision
   interval of every primary claim. Descriptive families carry their own
   simultaneous interval and license no claim.
4. **Readings** (`dci1v7/analysis/claims.py`, unchanged): for Δ_R(f) —
   `INSUFFICIENT_PRECISION` when the joint half-width exceeds
   `PRECISION_PRECONDITIONS["Delta_R"]` = 0.05 (no level); L3a when the
   lower bound exceeds `DELTA_R_GENERIC_THRESHOLD` = 0.10; L3b when it
   exceeds `DELTA_R_PAIR_SPECIFIC_THRESHOLD` = 0.25 (`INDETERMINATE@0.25`
   when only the upper bound does); L3c when the upper bound is below 0.10,
   reported with disposition `NEAR_FORM_UNAVAILABLE` (no near-form arm
   exists, so the strong refutation is not licensed); otherwise
   `INDETERMINATE@0.10`. For δ_difficulty(f) — no level without spectrum
   support; L3d when the interval excludes zero from below; L3e when it lies
   wholly inside ± `EQUIVALENCE_REGION` = 0.10. L1 (a delivery loss exists)
   requires B's solo headroom ≥ `L1_SOLO_HEADROOM_FLOOR` = 0.05; L2 (Λ) is
   read only where L1 is licensed. The Ξ direction gate decides the wording
   of an L3 statement (*specific to B* against *A generally disruptive*);
   a Δ_R reading is qualified `REFERENCE_HETEROGENEOUS` when the three Δ_j
   intervals disagree on the side of 0.10. L4a records whether the two
   configurations agree on every reading; L4b is F11. L5 is withheld.
5. **Cross-frame and model-level rule.** A model-level LOCAL statement is
   the **conjunction** of its entering frames' readings on the joint
   intervals (intersection–union; no further adjustment). The verdict set
   (`confirm/analysis.py::MODEL_VERDICTS`) is `LOCAL_SUPPORTED_L3a`,
   `LOCAL_SUPPORTED_L3b` (every entering frame at that level or above),
   `LOCAL_EQUIVALENT_SAME_FORM_ONLY` (every entering frame at L3c; the
   strong refutation `LOCAL_EQUIVALENT_L3c` is unreachable without the
   near-form arm, disposition `NEAR_FORM_UNAVAILABLE`), `FRAME_HETEROGENEOUS`
   (the frames' readings differ), `INSUFFICIENT_PRECISION` (any entering
   frame's primary interval misses its precondition), `INDETERMINATE`, and
   `UNIDENTIFIED` (no entering LOCAL frame). Frames are reported side by
   side; a frame-specific statement is a statement about that frame.
6. **Robustness, executed.** F5: the six F1 members under the
   vacuity-forced recoding and D(B←A), Δ_R, δ_difficulty under the graded
   recoding at `GRADED_ROBUSTNESS_THRESHOLD` = 0.99; F6: the vacuity-rate
   differences of every composed B cell against B solo; the §17.4 gate
   (`F6_VACUITY_GATE` = 0.05): when the vacuity difference binds and F5's
   Δ_R bounds disagree with F1's on the threshold, the Δ_R reading is
   qualified `VACUITY_DEPENDENT`. Projection audit per frame: for every
   companion c stated beside B, the projected compliance
   `κ_c + ι_c(1 − κ_c)` (κ_c realised on the frame's confirmatory
   unconstrained cells, ι_c frozen) against the realised compliance of c in
   the composed cells, inside `PROJECTION_ERROR_ALLOWANCE` = 0.05 or
   flagged. Identification ledger: every registered member of every family
   is `ESTIMATED`, `NOT_ASKED` (the arm does not exist on the frame) or
   `NOT_IDENTIFIED` (with the reason); a silently absent member is a
   `ProtocolError`. §26's methodological success is restated per model:
   every asked F1 member estimated, every primary precondition met, every
   frame table complete. The final report checks traceability (every
   frozen frame analysed, every member ledgered, hashes matching) and
   fails its own record otherwise.
7. **Omitted v7 components, declared** (§20 gives the reasons): masking
   and unmasking stages; near-form and class arms and their families F9,
   F10, Ord_CL; the tier fit F8 (replaced by F_SPECTRUM on the v8
   selection); the raw-coordinate secondary analysis and its
   `DIFFICULTY_COORDINATE_DEPENDENT` qualifier; the projected-vs-realised
   boundary summary against a Gate-4 projection; the configuration-scope
   assertion; the L5 emitter guard.

## 19. Precision, failure handling, provenance and freeze requirements

1. **Freeze-readiness audit** (`confirm/readiness.py`, executed on the
   mandatory path of `FROZEN`, written into the record; a failing item is
   `FREEZE_REFUSED`, terminal for the root, no override): (1) this document
   exists, is not a draft, and is the document the registration manifest
   bound; (2) one allocation across the lock, the rules and the precision
   module; (3) this model's pilot Gate 2 was measured at the universal
   calibration allocation; (4) the stability record and status exist for
   every entering frame, and the runner-up arm exists exactly where §11.4
   requires; (5) the reference-sensitivity plan exists for every LOCAL
   frame; (6) no protected artifact exists under the model's tree; (7) the
   verifier and wording hashes are the pilot's; (8) the analysis code
   hashes bound at registration are current; (9) the worktree gate ran;
   (10) identification statuses are on the record; (11) this model's
   pilot screen ran at `SCREEN_FRAME_OFFSETS` and its forwarding was
   decided by `RETENTION_POLICY` against `RETENTION_TARGET_BASIS` — a
   pilot of the pooled design cannot be frozen under this document.
2. **Precision.** §16.1's variance form
   `Var(Δ_R) = (2(1 − ρ)σ²_topic + σ²_draw(1/M + 1/3M)) / blocks` is
   projected at 384 blocks × 8 draws under the registered planning
   constants (φ = 0.27, ρ = 0.5, p(1 − p) = 0.215), the alternate φ = 0.37,
   the composed-at-half and worst-case (ρ = 0) scenarios, at the joint
   Šidák constant for k = 6 × LOCAL frames; the projection is recorded in
   the lock and the freeze. The registered precondition (joint half-width
   ≤ 0.05) is projected to hold for a two-frame model under the adverse
   pair and not for a four-frame model; the realised interval decides
   (§18.4's `INSUFFICIENT_PRECISION`, non-terminal). No allocation moves
   after the freeze.
3. **Exclusions and failure handling.** A frame that fails §11.2 is
   unsupported; a frame that fails §14.3 or §13.3 enters the corresponding
   arm not at all; a model with fewer than two LOCAL-supported frames runs
   no LOCAL cell; a model with no entering frame is `NOT_ELIGIBLE`
   (terminal, no generation). `APPARATUS_FAILURE`, `FREEZE_REFUSED` and
   `GENERATION_INCOMPLETE` are terminal; a terminal root is never resumed —
   a repair is a fresh root with its own records. Rows are never dropped
   for their content. After protected outcomes exist, no rule, threshold,
   operating point, reference, frame, allocation, multiplicity rule or
   claim definition changes; an inconvenient, underpowered, heterogeneous
   or contrary result is reported as such.
4. **Provenance.** Every stage of both layers runs only from a clean,
   commit-addressable worktree and is addressed to HEAD
   (`run/lifecycle.py::stage_provenance`; an operator-supplied commit that
   is not HEAD, a dirty worktree, or a directory that is not a repository
   fails closed; synthetic namespaces record the state and are never
   evidence). Every record is HMAC-signed and write-once; the manifest
   binds the rule table (`rules_hash`), this document, the design notes,
   the wording and verifier hashes, the analysis code hashes, the decoding
   policy form, the split identity, the seeds and domains, the pilot roots'
   record hashes, and the environment. Backend text reproducibility is
   measured, not assumed (`reports/dci1v8dev/freeze_readiness/
   backend_determinism.md`).
5. **Stopping rule.** The study ends when every entering model has a
   `FINAL_REPORT` record or a terminal status. Nothing is added, re-run or
   re-selected in response to a result.

## 20. Intentional deviations from v7

| v7 | v8 | why | safeguard lost / replaced |
|---|---|---|---|
| frames pooled; one n*, m*, triple, Δ_R per model; composed lines under different frames in 3 of 4 blocks | frame is the condition; n*(f), m*(f), triple(f), Δ_R(f); one frame per block | the four frames are not exchangeable on A (r3: A at severity 5 read 0.22/0.68/0.42/0.52) | pooled precision replaced by per-frame precision at the ceiling; cross-frame heterogeneity now a reported verdict |
| κ_R = 0 fallback | one unconstrained-cell basis for A and every reference | v7 defect | none lost |
| one validity rule for LOCAL and SPECTRUM | LOCAL rule unchanged; separate SPECTRUM rule and coverage gate | v7's spectrum could not span | none lost; the LOCAL caliper is tested not to leak |
| masking / unmasking stages | none | the analysis is frozen code run once, unattended; there is no analyst decision point | the seal is replaced by freeze-bound code hashes |
| near-form and class arms (F9, F10, Ord_CL) | not run | the frame-conditioned design spends its budget on frames; the strong L3c refutation is therefore not licensed (`NEAR_FORM_UNAVAILABLE`) | strong L3c unavailable, declared |
| F8 tier fit | F_SPECTRUM slope on the v8 selection | selection is decoupled from the core families | tier indicator gone |
| raw-coordinate secondary analysis | not run | v8's coordinate basis is uniform; the secondary coordinate has no v8 admission role | `DIFFICULTY_COORDINATE_DEPENDENT` qualifier unavailable — a stated limitation of δ_difficulty(f) |
| boundary projected-vs-realised summary | per-member boundary readings only | no Gate-4 projection exists in v8 | the comparison is unavailable |
| prefreeze audit (§33) | readiness audit (§19.1) | restated for the v8 record | — |
| 2 wording templates | repaired (§6) | substring reading in v7's phrasing | v7 rows under the old templates are not reused |

## Appendix A — development history (adaptive decisions, disclosed)

Every scientifically consequential v8 decision, with what was visible when
it was made, is tabulated in
`reports/dci1v8dev/freeze_readiness/VERIFICATION_LEDGER.md` (finding 11).
None used a composed outcome (the earliest composed row in any root was
written at 10:11:44Z on 2026-09-02, after the last design commit of that
design; that root is superseded, `reports/dci1v8dev/confirmatory/
SUPERSEDED_dci1v8-confirm.md`). Three decisions were model-specific
(raising `qwen3-4b` and `qwen3-4b-instruct-2507` to four calibration passes
after pilot r8; running `gemma-3n-e4b-it` at two); this document replaces
them with the universal rule of §9 and every model is re-verdicted on that
basis. **2026-09-03 (v8.1):** after the v8 freeze and before any composed
row existed, the frame-pooled pre-screen was characterised
(`legacy_prescreen_characterization.md`), replayed against a frame-aware
rule on the stored roots (`prescreen_feasibility.md`; the comparison read
no protected artifact), and replaced by the per-frame screen and
forwarding of §10 with the pooled rule kept as a comparator arm. Every
v8.1 pilot is a fresh root from `REGIME_SCREEN`; no v8 pilot record enters
a v8.1 verdict. From this document onward no rule changes in response to a
pre-freeze near-miss unless the change is itself preregistered here.

## Appendix B — identities bound at freeze

Pilot roots that a v8.1 confirmatory manifest would bind (every model at
the universal calibration allocation of §9 and the screen allocation of
§10.2; every stage from a clean worktree at the named commit), as of
2026-09-05 22:00Z — the record of each is
`reports/dci1v8dev/frame_aware_prescreen/prescreen_revalidation.md` §2:

| model | successor root | commit | status | replicate (re-execution on the same topics and seeds; not bound) |
|---|---|---|---|---|
| qwen3-4b | `dci1v8-pilot-r14` | `025e138` | `PILOT_REPORT`, LOCAL on f0–f3 | `dci1v8-pilot-r21` at `025e138`, agrees |
| qwen3-4b-instruct-2507 | `dci1v8-pilot-r15` | `025e138` | `PILOT_REPORT`, LOCAL on f1, f3 | `dci1v8-pilot-r20` at `025e138`, agrees |
| gemma-3n-e2b-it | `dci1v8-pilot-r16` | `025e138` | `PILOT_REPORT`, LOCAL on f0, f1, f3 | `dci1v8-pilot-r19` at `025e138`, agrees |
| gemma-3n-e4b-it | `dci1v8-pilot-r23` | `7d8e1d9` | `PILOT_REPORT`, LOCAL on f0, f1, f3 (r17 invalidated, r18 abandoned; §2 of the record) | `dci1v8-pilot-r24` at `7d8e1d9`, agrees |

**The mixed commits are accepted (2026-09-07), on an audited
operational-only difference.** `git diff 025e138 7d8e1d9` touches one
source file, `dci1v8dev/run/execute.py`, and within it one constant: the
backend wall-clock cap, raised from 12 h to 36 h because
gemma-3n-e4b-it's Gate-2 candidate run needs about 16 h and a partial
backend run restarts from zero. The pilot manifests confirm it
independently of the diff: of the 72 hashed package files, 71 are
byte-identical between an `025e138` root and a `7d8e1d9` root, the sole
difference being that file, and the `rules`, `protocol`,
`protocol_version`, `documents` and `wording_diagnostic` bindings are
identical across all four roots. No protocol constant, prompt, wording
frame, verifier, pre-screen rule, second-pass rule, target basis,
forwarding rule, calibration allocation, operating-point selection,
LOCAL/SPECTRUM validity rule, reference selection, eligibility rule,
confirmatory allocation, estimand or analysis definition differs. The
other three models are therefore **not** re-run for commit uniformity, and
every `CONFIRM_REGISTERED` record carries each pilot's own producing
commit (`confirm/pilot_import`), so the mixture is on the record rather
than hidden.

Confirmatory root: named at registration. Nothing is frozen until §19.1's
readiness passes. The frozen v8 root
`dci1/evidence/dci1v8-confirm-r2` is historical evidence of the pooled
design and is not reused.


Recorded in every `FROZEN` record and checked by §19.1: the commit, the
rule-table hash, this document's hash, the wording hash
(`fe3b5be1…`) and verifier hash (`ea885b0d…`) current at writing (the
record's values are authoritative), the analysis code hashes, the pilot
record hashes, the membership lock hash, the environment record.

## Appendix C — what changed between DRAFT and this registered text

This document was drafted on 2026-09-03 with the successor design, and
registered on 2026-09-08 after the pre-freeze evidence was complete. The
changes are these, and nothing else; every one of them records a decision
already taken or a fact already on the evidence record, and none introduces
a scientific rule that the code does not execute.

1. **Status.** `DRAFT` → `FROZEN-READY`.
2. **§10 item 9, the retention target.** Was an open researcher decision
   between the calibrated basis (C) and the screen proxy (A), to be settled
   by the successor pilots. Now a registered decision: basis C, with basis A
   kept as a comparator arm that decides nothing. The pilots' evidence — the
   same family count, backup count and verdict on all 14 supported frames,
   with measurably different forwarded sets — is cited.
3. **Appendix B, pilot provenance.** The successor roots, their models,
   their commits and their outcomes are named, and the mixed pilot commits
   (`025e138` and `7d8e1d9`) are accepted on an audited operational-only
   difference, stated with the audit's evidence.
4. **Appendix D (new), methodology-validation evidence.** Records the three
   kinds of pre-freeze robustness evidence and what each does and does not
   license.

The operating-point rule of §11, its bands and aims, the runner-up
sensitivity arm of §11.4 and §17.3, the reference-ranking rule, the
LOCAL/SPECTRUM validity thresholds, the eligibility rule, the confirmatory
allocation, the estimands, the inference thresholds and the multiplicity
plan are **unchanged from the DRAFT**. In particular the operating-point
rule was not redesigned in response to the instability the validation
evidence documents (Appendix D); the registered response to an unstable
operating point remains the runner-up arm that §11.4 already specified.
