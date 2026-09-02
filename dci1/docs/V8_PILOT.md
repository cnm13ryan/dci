# DCI-1 v8 pilot — execution layer and criteria (prospective; not registered)

**Status (2026-08-30, branch `dev/v8-canonical`; revised the same day by
researcher decision --- §1a below; revised again after pilot r3: the
wording frame is part of the experimental condition, §1a item 6 and
`V8_FRAME_CONDITIONING.md`).** The execution layer of
the v8 candidate (`dci1/docs/V8_CANDIDATE.md`), written so that the four
questions the candidate leaves open can be measured on one real model
before anything is frozen. Package `dci1v8dev.run`; CLI
`python -m dci1v8dev.run.cli`; driver `tools/run_v8_pilot.sh`; validation
`tools/v8_validate.sh`. Nothing here has generated a token. The v7 study is
historical evidence and its code is imported, never edited; the pilot's
rows carry `study_id: dci1v8` and a classification naming a development
candidate, and no v7 reader accepts either.

## 1. What the pilot measures, and what it does not

Four prospective criteria (`run/stages.py`, bound by the pilot manifest
before any row exists, evaluated by `PILOT_REPORT` on signed records only):

| criterion | question | rule |
|---|---|---|
| `WORDING_DIAGNOSTIC` | how do the four frames behave, measured separately? | **no pass/fail rule** (§1a): per (frame, family, q) the sample, exact compliance, chance on the unconstrained cell, ι, SE and the comparison with the other frames, on the screen, the second pass and calibration; the report leaves the judgment explicit |
| `LADDER_COVERAGE` | does the screen/second pass/retention carry the ladder's geometry to calibration? | second pass resolves within 3 batches; ≥ 2 forwarded spectrum families reach both offsets at the screen; the spectrum-valid pool at calibration has ≥ 2 points from ≥ 2 families per side |
| `CHANCE_BASIS` | is κ measured on §13.2's unconstrained cell in both tables? | the screen's and Gate 2's chance basis is the unconstrained cell on every split, the column is not the zero column, ι_A is on the same basis (the all-absent v7 basis is recorded beside it) |
| `REFERENCE_SURVIVAL` | do LOCAL and SPECTRUM references survive calibration? | ≥ 5 LOCAL-valid families (§13.15 on the admissible basis), three core references by the registered §13.8 kernel, selected coverage identified with projected SE(β̂) ≤ 0.05, ≥ 2 admissible backups |

The three *decided* criteria (`stages.DECIDED_CRITERIA`) carry a
registered rule; the wording diagnostic carries none. A failed criterion
**terminates nothing**: it is recorded where it is measured and summarised
by the report. The only terminal statuses are v7's apparatus and
operating-regime ones
(`QUALIFICATION_FAILURE`, `APPARATUS_FAILURE`,
`RESPONSE_LENGTH_INCOMPATIBLE`, `TARGET_RANGE_EXHAUSTED`,
`FOCAL_RANGE_EXHAUSTED`, `GRID_RESOLUTION_INSUFFICIENT`, `REGIME_NOT_FOUND`).

**No composed cell.** The pilot generates load 0 and load 1 only.
`execute.assert_no_composed_cell` refuses a two-slot cell at the renderer,
at the row plan and at the generation seam; no stage builds one; the
sequence ends at the report; and `tests_v8dev` scans every module of the
layer for a composed constructor. The spectrum arm's B+X / X+B cells and
every composed or interference outcome (Δ_R, δ_diff, …) are a post-freeze
experiment (`V8_CANDIDATE.md` §12 step 4) that this layer cannot produce
and that may not be inspected before the wording policy and the v8 design
are frozen.

### 1a. Researcher decisions of 2026-08-30

1. **Second-pass sampling** --- fresh Calibration-A topics for the families
   the first pass could not settle; no extra draw on a pre-screen topic;
   Calibration-B untouched; batches disjoint (two topics per area per batch,
   three batches at most = 72 of 96); the budget of
   `rules.RESCREEN_MAX_BATCHES × RESCREEN_BATCH_TOPICS` unchanged. Asserted
   per batch (`rescreen.assert_batch_isolated`) and on every generated row
   (`topic_id`, `topic_split`, `run` = batch), recorded on the stage record
   (`topic_isolation`, `batches[].topic_ids`).
   *Pilot r2 finding (2026-08-30 06:17Z):* the rule's batch index was the
   largest per-family batch count and the cap was per family, so MK4 ---
   resolved after batch 0, back to `SCREEN_RESAMPLE` after batch 2 because
   the A-grid is re-measured every batch and ι_A moved --- got index 3 (a
   fourth batch, 648 rows on the last 24 Calibration-A topics) and then
   index 3 again, which the isolation assertion refused. Fixed in the rule
   (`prescreen.rescreen.plan_batch`): the index is the batch's position in
   the run and `RESCREEN_MAX_BATCHES` bounds that sequence; a family still
   undecided when the sequence is spent is resolved by the existing at-max
   rule. r2's root is kept (regime record and four batches on disk, no
   second-pass record); the pilot re-ran as r3 at the fixed commit.
2. **The v7-relative frame threshold is removed.** The former
   `FRAME_RELIABILITY` rule (best v7 frame + 0.05) is deleted from the
   stages, the manifest, the registration record, Gate 1 and the report; no
   v7 frame statistic enters any v8 verdict. `reports/dci1v8dev/frame_reference.json`
   remains as a descriptive report of the historical instrument. No
   replacement threshold was introduced.
3. **Every generated output is data.** Compliant and non-compliant rows are
   kept and counted; nothing downstream conditions on uptake or exact
   compliance. Each scored row carries `frame`, family and severity (in
   `scores[].kind/severity`), `topic_id`, `topic_split`, `run`, the observed
   constraint count (`scores[].statistic`), the exact-compliance verdict
   (`scores[].passed`) and the existing provenance. `execute.row_accounting`
   proves per run that every planned row was generated and every generated
   row scored; it runs on the path (a shortfall fails the stage) and is
   recorded on the regime, second-pass and Gate-2 records.
4. **Wording sensitivity is measured directly** (`run/wording.py`): for every
   (frame, family, q) --- sample, exact-compliance rate, chance on the
   unconstrained cell, ι, SE, and the comparison with the other frames; per
   frame, the ladder class over q (`prescreen.ladder`); per frame, the
   stability of ι between disjoint topic sets (screen vs second pass;
   Calibration-A vs Calibration-B); the dependence of ι on the frame (τ²
   net of sampling variance, class shares). Frames are never averaged as the
   primary diagnostic. Two frames' difference in ι is described against the
   registered §13.7 equivalence bound (0.20, `stages.WORDING_REFERENCE_BOUND`):
   beyond it with a 95 % interval excluding zero is `WORDING_SENSITIVE`
   (instrument instability), beyond it otherwise `UNRESOLVED`, else
   `CONSISTENT`. No frame is discarded on any class. The per-frame SE is
   the topic-level SE floored by the Agresti–Coull binomial SE over the
   frame's topics (a frame whose few screen topics all pass or all fail
   has an SD of 0, and without the floor any difference would count as
   resolved). At the screen a frame holds 6 topics × 1 draw, so the
   cross-frame comparison there is mostly `UNRESOLVED` by construction;
   the calibration basis (48 topics × 4 draws per frame per split at the
   two-pass allocation, `V8_CANDIDATE.md` §5b; 24 before it) is the one
   that resolves it.
5. **The pilot informs the wording policy; outcome data must not.** The
   policy --- retain all frames, retain a specified subset, or model frame
   variation --- was a researcher decision on solo / pre-screen /
   calibration evidence only (`stages.WORDING_POLICY_OPTIONS`); taken on
   2026-08-30 after r3 (item 6), status `DECIDED` on the manifest, the
   registration record and the report.
6. **The wording frame is part of the experimental condition (Approach A,
   2026-08-30, after r3).** Design note `V8_FRAME_CONDITIONING.md`
   (Approach B --- one canonical wording --- recorded and rejected).
   Difficulty is ι(X, f). Gate 2 selects n*(f) and m*(f) by §12.3 on each
   frame's own curves, checks §12.4 on each frame's own rates, and writes
   §13.11's table per frame on that frame's rows (§13.2's chance on the
   unconstrained cells of the frame's own blocks --- the producer's
   same-topic rule; κ(R|B) at m*(f) on the frame's B-solo cell; the
   extension reach at ι_A(f)). Gate 3 decides LOCAL and SPECTRUM
   validity, the core references, the spectrum points, the coverage
   (projected at the frame's 96 of the 384 confirmatory blocks) and the
   backups per frame and records each frame's state (`UNSUPPORTED`,
   `NEITHER`, `LOCAL_ONLY`, `SPECTRUM_ONLY`, `LOCAL_AND_SPECTRUM`). An
   unsupported frame records the §12.3/§12.4 status it hit and the other
   frames continue; the replication is terminal only when no frame is
   supported. The report evaluates the decided criteria per frame and
   aggregates by "at least one supported frame passes" with every frame's
   verdict beside it. The screen and second pass stay pooled over frames
   as a measurement budget. No pooled ι_A, table, core set or spectrum
   exists on any record; the frame-pooled curves are `descriptive_pooled`,
   read by nothing. Executable: `tests_v8dev/test_frame_conditioning.py`.

## 2. The nine stages

| # | stage | generates | what it does |
|---|---|---|---|
| 1 | `PILOT_REGISTERED` | – | signs the pilot manifest once per root (documents, package, rules, both instrument hashes, models, topics, seeds, criteria, frame reference); a later replication is verified against it and refused on any difference |
| 2 | `QUALIFIED` | – | fifteen apparatus checks; fails closed with the whole list |
| 3 | `GATE_0_APPARATUS` | 12 topics × 5 cells × 4 | §19-shaped plumbing proof under the v8 frames: every cell/draw once, byte mutation refused, durable restore, v8 identity on every row |
| 4 | `REGIME_SCREEN` | cap selection 3 × 96; ladder 24 × (326 + 8 + 8 + 1) | §12.1, §12.2 under the v8 frames; κ on the unconstrained cell; frame reliability; the uncertainty-aware first pass (`prescreen.screen`) |
| 5 | `SECOND_PASS_SCREEN` | ≤ 3 batches × 24 × (rungs + 8 + 1) | `prescreen.rescreen.run_rescreen` with a real `measure`: fresh Calibration-A topics (two per area per batch, disjoint), reserve picks, A's grid; then `retention.retain` → the forwarded set |
| 6 | `GATE_1_INSTRUMENT` | – | frame criterion vs the bound reference; §7.5 over the v8 population; v8 scorer determinism; hashes frozen |
| 7 | `GATE_2_CALIBRATION` | 192 × 4 × (8 + 8 + 1) + 192 × 4 × forwarded + extension | **per frame** (§1a item 6): n*(f), m*(f), adequacy (v7's rules on the frame's own curves); the forwarded set at calibration precision on every block, with B at every supported frame's m*(f) absent; §13.11's table per frame by the 7f89dae producer on the frame's own unconstrained cells; one extension round (the union of the frames' plans, each ≤ 2 reserve rungs per deficient side of a spectrum family); unsupported frames recorded, terminal only when none is supported |
| 8 | `GATE_3_REFERENCES` | – | **per supported frame**: folded §13.7 stability against ι_A(f); `classify_pool` (LOCAL = v7's full V(R); SPECTRUM = V_coord/unfolded V_stab/V_pos); core by `admit_core_references(require_spectrum=False)`; `select_spectrum`; `selected_coverage` at `rules.CONFIRMATORY_BLOCKS_PER_FRAME` blocks per frame; `admissible_backups`; the frame's state; a descriptive cross-frame block; the estimands stated per frame |
| 9 | `PILOT_REPORT` | – | the four criteria on the records, the three decided ones per frame; the run-level aggregate (`any_supported_frame`); frames meeting every decided criterion; generation counts; what the freeze decision may rest on |

Second-pass topics: §12.5 admits only the three development sets to
iterative work and the pre-screen set is spent at round 0, so batches are
cut from Calibration-A (three batches use 72 of 96) and Calibration-B is
left untouched by every selection step --- §13.7's split equivalence keeps a
selection-free half. Recorded per batch on the stage record.

## 3. Roots, namespaces, isolation

* `pilot` --- study id `dci1v8`; the pinned backend, the real model, every
  rule; a generation callable is refused. Root: `--root <dir>`, convention
  `dci1/evidence/dci1v8-pilot` → `.../evidence/dci1v8/<model>/<STAGE>/`.
* `synthetic` --- `dci1v8-synthetic`; a stand-in generator and the scale
  knobs (rung subset, `topic_limit`, fewer resamples); the lifecycle test.
* A v8 root may neither lie inside nor contain any other study's evidence,
  durable or source tree; every child of `dci1/evidence` and
  `dci1/durable_root` not named `dci1v8*` is foreign, so `dci1v7`,
  `dci1v7-development-r3/r4/r5` and every earlier revision are refused by
  rule (`context.assert_isolated_root`, `tests_v8dev/test_pilot_layer.py`).
* Seeds: v7's root seeds under `dci1v8:*` domains; no v8 draw coincides with
  a v7 draw. Signing key per root. Records write-once, in order, terminal is
  terminal, one study.

## 4. What is reused from v7 unchanged, and what is v8's

Reused (pure functions of rows/tables): the generative seam
`dci1v4.generation.backend`; `run/execute.cell_rates`, `instance_rates`,
`per_topic_compliance`, the reuse rule `_reusable_rows`; §12.3's
`select_target/select_focal/grid_resolution/regime_adequacy`; §13.11's
producer `gates_run._calibration_rows` with `_kappa_columns` and
`_withhold_degenerate` (the 7f89dae chance fix); §13.7's `stability_verdict`;
§13.8's `admit_core_references`; the topic bank; the engine's process pools.

v8's: the study id, classification, evidence layout, seed domain, the prompt
(`dci1v8dev.wordings`), the scorer (`dci1v8dev.verifiers`), the screen /
second pass / retention / extension / validity / selection / coverage /
backups rules (`dci1v8dev.prescreen`, `dci1v8dev.spectrum`), the nine
records, the manifest and the criteria. v7's §34 construct floor is not
applied: the pilot selects no confirmatory operating point and reads m* only
for κ(R|B) (recorded on the Gate-2 record).

## 5. Validation without a GPU

    cd dci1
    tools/v8_validate.sh                       # everything below, in parallel
    .venv/bin/python -m pytest tests_v8dev -q -p no:cacheprovider          # rule + execution layer
    .venv/bin/python -m pytest tests_v8dev/test_pilot_lifecycle.py -q      # the nine-stage synthetic walk
    .venv/bin/python tools/v8_pilot_walk.py                                # reports/dci1v8dev/pilot_walk.md
    .venv/bin/python tools/v8_frame_reference.py --check                   # descriptive report only
    .venv/bin/python -m dci1v8dev.run.cli audit                            # the producer/consumer contract
    .venv/bin/python -m dci1v8dev.run.cli plan --root /tmp/v8-plan         # what signing would bind
    .venv/bin/python tools/v8_wording_decision.py --root <root>            # the per-frame wording report (Gate 2/3 only)
    .venv/bin/python -m pytest tests_v8dev/test_frame_conditioning.py -q   # Approach A's sixteen contracts (one slow)

The synthetic walk drives all nine stages through the production runners
with v7's scripted composer (`tests_v7.synthetic_lifecycle._compose`) as the
generator, asserts the contract against real payloads, that every row
carries the v8 identity and no row is composed, that both tables read κ on
the unconstrained cell, that the second pass used disjoint Calibration-A
topics, and that the report evaluates the four criteria.

## 6. The pilot (not run here)

    cd dci1
    tools/run_v8_pilot.sh qwen3-4b-instruct-2507 <device> evidence/dci1v8-pilot <log_dir>

Sequence (V8_CANDIDATE.md §12): one model; inspect the three decided
criteria and the wording diagnostic on `PILOT_REPORT`; take the wording
policy decision on that evidence; freeze v8 only then; only then the
spectrum arm.
Estimated generations per model ≈ 8k (cap) + 8.2k (screen) + 7–12k (second
pass) + 13k (grids) + 192 × 4 × forwarded (≈ 31–49k) + ≤ 12k (extension)
≈ 60–90k --- ≈ 1–1.5 h on qwen3-4b-instruct-2507 per card at the observed
Gate-2 throughput. No v7 lane is interrupted: the driver takes the per-card
lock the v7 driver uses and waits.

## 7a. Outcome of the first real pilot (r3, 2026-08-30)

`dci1/evidence/dci1v8-pilot-r3`, qwen3-4b-instruct-2507, gpu1, commit
190e660, 05:38Z–07:14Z. Registered, qualified (15/15), Gate 0 (8/8), regime
screen (cap 512; 342 rungs; κ on the unconstrained cell; 0 `SCREEN_ACCEPT`,
19 reject, 18 resample), second pass (3 batches × 24 fresh Calibration-A
topics, 12 768 generations, every row scored; 15 families resolved at the
maximum, 6 accepted; 56 rungs forwarded; 5 of 6 spectrum families reach
both offsets), Gate 1 --- all signed `PASS`. **Gate 2 ended terminal:
`GRID_RESOLUTION_INSUFFICIENT`** (§12.3) after the A and B grids (13 824
rows) and before any candidate: A's solo compliance pooled over the four
frames is 0.986 / 0.993 / 0.982 / 0.921 / 0.460 / 0.464 / 0.306 / 0.449 at
q = 1…8, and q4 → q5 jumps across the whole target band [0.50, 0.85]. Under
v7's frames the same model (r4) had 0.87 → 0.566 there and passed.

The wording diagnostic on the grid rows (`reports/dci1v8dev/wording_decision.md`,
recomputed from the rows because the stage wrote no record; 48 topics × 4
draws per frame per split; κ = 0 on A, so ι is raw compliance) shows why:
**the four A frames disagree by 0.34–0.46 at q = 5–8, replicated on both
splits** (A:5 --- f0 0.219, f1 0.682, f2 0.417, f3 0.521; A:6 --- 0.240 /
0.615 / 0.312 / 0.688). Frame 0 (*Use the word however exactly q times.*)
is the hardest at every q ≥ 4, frame 1 (*Your answer must contain the word
however exactly q times.*) the easiest; on B a different frame (f3, *No
word in your answer may exceed q letters.*) is the hardest at every q ≥ 8
(B:9 --- 0.578 / 0.661 / 0.442 / 0.296). The failure mode on A is a
systematic off-by-one (under f0 at q = 5, 150 of 192 answers use the word
exactly four times; the verifier's count agrees with an independent regex
count on every row). Per frame, §12.3 resolves the band under f0, f1 and f3
alone and fails under f2 alone and under the pooled curve. 11 of 16 A/B
rungs are `WORDING_SENSITIVE` or `UNRESOLVED`; 8 of the 11 replicate (same
sign, beyond the bound on both splits); τ median 0.115. Gate 3 was not
reached, so the exposure of the reference set (item 4) is unmeasured.

What this licenses: nothing about the effect. It says the v8 instrument
as pooled by §7.8 is out of regime on this model because its frames are
not exchangeable on A, and the wording policy (§1a item 5) is now the
blocking decision: retain all frames (then the target rule needs a
per-frame or frame-robust operating point), a specified subset (f1, or
f1 + f3, resolve the band; the choice would rest on this one model), or an
explicit frame term in ι (then §12.3 and §13.11 need a frame-aware
reading). Earlier roots: `dci1v8-pilot` (terminal at `QUALIFIED`,
`clean_worktree`) and `dci1v8-pilot-r2` (the second-pass index defect,
§1a item 1) are apparatus records.

## 7b. The pilot under Approach A (2026-08-30)

**r4 (both models, 09:01Z–10:26Z) is an apparatus record.** Registered,
qualified, Gate 0, regime screen, second pass and Gate 1 signed `PASS` for
`qwen3-4b` and `qwen3-4b-instruct-2507`; `qwen3-4b` reached Gate 2, measured
both grids and all 53 forwarded candidates on every block, and the §13.11
producer then refused the extension round's first rung — *kappa_c for MK6:9
has no unconstrained cell to be measured in*. A reserve rung the extension
measures had never been declared as an instance on the grids, so it had no
chance column and no kappa(R|B) (`CHANGES_SCIENTIFIC.md`, 2026-08-30 pilot
r4); the round was inert rather than wrong, and no replication had reached
it before. Fixed by `calibration.extension_instances` (no generation);
pinned by `tests_v8dev/test_frame_conditioning.py`. r4's grids did show
Approach A working on real rows: `qwen3-4b`'s four A curves select **three
different operating points** (n* = 4, 7, 4, 6 for f0…f3) where the
frame-pooled curve selects 4.

**r5 and r6 ran Approach A to the pre-freeze endpoint on three
checkpoints** --- `dci1v8-pilot-r5` (qwen3-4b and qwen3-4b-instruct-2507,
10:34Z--12:39Z) and `dci1v8-pilot-r6` (gemma-3n-e2b-it, 12:29Z--14:55Z),
all nine stages signed `PASS`, 73.7k / 93.5k / 83.4k generations, no
composed cell, no freeze.

| | qwen3-4b | qwen3-4b-instruct-2507 | gemma-3n-e2b-it |
|---|---|---|---|
| supported frames | 0,1,2,3 | 0,1,3 (**f2 `GRID_RESOLUTION_INSUFFICIENT`**) | 0,1,2,3 |
| n*(f) | 3, 7, 4, 4 | 4, 5, --, 6 | 8, 3, 2, 3 |
| m*(f) | 12, 12, 12, 13 | 11, 10, --, 12 | 7, 10, 10, 11 |
| ι_A(f) | .682 / .625 / .719 / .682 | .807 / .682 / -- / .682 | .688 / .609 / .714 / .724 |
| candidates per frame | 56 (ext. 2) | 77 (ext. 11) | 68 (ext. 9) |
| frame states | NEITHER ×4 | NEITHER ×3, UNSUPPORTED | **LOCAL_ONLY**, NEITHER ×3 |
| `CHANCE_BASIS` | pass, every frame | pass | pass |
| `LADDER_COVERAGE` / `REFERENCE_SURVIVAL` | fail | fail | fail |

Four findings the pilot was run to obtain.

1. **Approach A keeps a replication alive that the pooled instrument
   kills.** On qwen3-4b-instruct-2507 --- the model and configuration that
   ended r3 --- the frame-pooled A curve is still out of regime
   (`n* = None`, `grid_resolution_insufficient`), but f0, f1 and f3 each
   have an operating point and the replication continues on them. Under
   §7.8's pooled reading it terminates; under Approach A it does not.
2. **The frames are separate conditions in the data, not in principle.**
   Three checkpoints give three different n* patterns, up to four distinct
   operating points on one model (Gemma: 8, 3, 2, 3), and on Gemma four
   different Gate-3 states with **no family LOCAL-valid under every frame**
   (f0 {MK2,MK4,MK5,XC3}, f1 {}, f2 {MK4}, f3 {MK5,MK8}). 51 %, 56 % and
   61 % of calibration rungs are `WORDING_SENSITIVE` (τ median
   0.073 / 0.077 / 0.094) while each frame's own ι is stable across its two
   fresh-topic splits (92 % inside the §13.7 bound).
3. **What binds is the per-frame allocation, not the frames.** A frame is
   calibrated on 48 of the 192 topics, and the measured per-frame SE(ι) is
   0.0497 --- exactly the registered 0.05 floor (46 % of coordinates above
   it). Of the ~30 rungs positioned below A per frame, `V_coord` refuses 21
   on that floor and the two-split `V_stab` refuses 9, so **no rung below A
   survives**, no family straddles, and no spectrum is selected; LOCAL fails
   at `V_stab` (~32 of 56) and `V_head` (~21). The screen, second pass and
   retention halves of `LADDER_COVERAGE` **pass** on every model (seven
   families reach both offsets, three batches, the extension fires): only
   the per-frame calibration half fails. No threshold was relaxed to obtain
   a passing run; the projection
   `reports/dci1v8dev/allocation_projection*.md` runs the production Gate-3
   rules at ×1/×2/×4 topics per frame and is the measured input to the
   allocation decision.
4. **The v8 frame repair works, and what remains is marker-specific.** On
   Gemma --- where v7's audit found w1/w2 marker-absent in 46--53 % of
   answers and *though* in 92--100 % --- the four v8 frames are at 14--22 %
   (pooled 19.7 %), *though* at 2--15 %, and six of the eight marker
   families are ≤ 0.15 under every frame. Two markers remain unreliable and
   they are unreliable **by family, not by frame**: *namely* (MK6, .73/.81/.77
   under f0/f1/f2) and *instead* (MK7, .96/.96/.98) --- and f3, the frame
   that puts the marker where it cannot be read as a connective of the
   instruction, rescues both (.17 and .71). That frame × family interaction
   is the empirical case for Approach A: under one canonical wording the
   choice of frame would silently decide whether two of eight marker
   families exist on Gemma.

`GRID_RESOLUTION_INSUFFICIENT` on one frame of one model is the only
terminal status any replication recorded, and it terminated a frame rather
than a replication --- which is §6 of `V8_FRAME_CONDITIONING.md` working as
designed. Provenance note: r5's records carry two producing commits
(`2145277` through the regime screen, `2aa3378` from the second pass on)
because a test-only commit landed mid-run; the manifest's package and
document hashes are identical across the two, and r6 runs on one commit. What it
measures per frame: n*(f), m*(f), ι_A(f), the number of calibrated
candidates, LOCAL-valid families, the spectrum-valid pool, the core
references, the selected spectrum points, the backups, and the frame's
state; and whether the frames agree.

## 7c. The calibration allocation amended, and the 2x pilot (2026-08-30)

r5/r6's finding 3 is an allocation result, and the researcher took the
allocation decision on it: **two calibration passes, 96 topics per frame**
(`V8_FRAME_CONDITIONING.md` §4a, `V8_CANDIDATE.md` §5b,
`CHANGES_SCIENTIFIC.md`). Gate 2 renders each of its runs over one pass per
frame offset `(0, 2)`, so every calibration topic is met under two frames,
every frame is measured on 96 distinct topics (48 per §13.7 split), no
topic recurs inside a frame, no frame is pooled with another, and Gate-2
generation doubles. **No threshold changed.** The record carries
`calibration_allocation` with the counts realised on the grids, the
candidate run and the extension, and
`calibration.assert_allocation_realised` refuses a frame that is short or
unbalanced.

## 7d. The 2x pilot (r8, 2026-08-30) — what more measurement bought

`dci1v8-pilot-r8`, all three checkpoints, all nine stages signed `PASS`,
16:02Z--22:03Z, at commit `c8b70d3`, 143.9k / 157.4k / 139.4k generations
(2.0x / 1.7x / 1.7x of r5/r6), no composed cell, no freeze. The allocation
is realised on every Gate-2 run --- the grids, the candidate run **and** the
extension round --- at 96 distinct topics per frame, 48 per split, refused
otherwise on the path.

| | qwen3-4b | qwen3-4b-instruct-2507 | gemma-3n-e2b-it |
|---|---|---|---|
| supported frames | 0,1,2,3 | 0,1,3 (**f2 `GRID_RESOLUTION_INSUFFICIENT`**, as r5) | 0,1,2,3 |
| n*(f) | 3, 7, 4, 4 | 4, 5, --, 6 | 8, 3, 2, 7 |
| m*(f) | 12, 12, 12, 13 | 11, 10, --, 12 | 8, 10, 10, 11 |
| iota_A(f) | .714/.630/.701/.708 | .844/.656/--/.664 | .680/.628/.794/.680 |
| frame states | NEITHER, NEITHER, **SPECTRUM_ONLY**, LOCAL_ONLY (f0 LOCAL_ONLY) | NEITHER, **LOCAL_AND_SPECTRUM**, --, **LOCAL_AND_SPECTRUM** | **LOCAL_AND_SPECTRUM** x3, SPECTRUM_ONLY |
| `LADDER_COVERAGE` | **pass** | **pass** | **pass** |
| `CHANCE_BASIS` | pass | pass | pass |
| `REFERENCE_SURVIVAL` | fail | **pass** (f1) | **pass** (f1, f3) |

Four things it measured.

1. **The precision the amendment was bought for arrived, exactly.** The
   median per-frame SE(iota) fell 0.0497 -> 0.0356 (qwen3-4b), 0.0465 ->
   0.0331 (2507) and 0.0411 -> 0.0296 (Gemma): ratios 1.40, 1.40, 1.39
   against the sqrt(2) the two-pass design predicts. Coordinates inside the
   unchanged 0.05 floor went 54% -> 92%, 68% -> 93%, 75% -> 89%.
2. **The spectrum problem was a precision problem.** `V_coord` fell from the
   leading SPECTRUM refusal (117--132 of ~230 candidate-frames) to second
   (54--69), and outright passes rose from 7--15 to 40--91; on Gemma
   `PASSED` is now the modal outcome. Spectrum coverage is identified on
   4/4 Gemma frames, 2/3 on 2507 and 1/4 on qwen3-4b, against **0/11**
   across all three models at one pass. `LADDER_COVERAGE`, which failed on
   every model at one pass, now passes on every model.
3. **The LOCAL arm is not the same story.** `V_stab` and `V_head` remain its
   two leading refusals and barely moved (qwen3-4b V_stab 133 -> 132,
   V_head 86 -> 91); what changed is that outright passes rose from ~1 to
   18--34. Two frames of two models now identify a core with two backups,
   which is what `REFERENCE_SURVIVAL` needs, but §13.15's five LOCAL-valid
   families is reached on only three of eleven supported frames.
   `V_head` is a headroom statement about the candidate, so where LOCAL
   still fails it is not purely a precision story --- see
   `reports/dci1v8dev/bottleneck.dci1v8-pilot-r8.*.md`.
4. **The frames stayed separate conditions.** 2507's f2 is out of regime
   again, on the same status as r5, and the four frames still choose
   different operating points (Gemma 8, 3, 2, 7) and different reference
   sets. Approach A is doing the same work at the new allocation.

The projection was **not** a reliable guide to any single number: it was
right for 2507 (2/3 LOCAL, 2/3 SPECTRUM, exactly), understated Gemma
(2/4 . 3/4 projected against 3/4 . 4/4 observed) and got qwen3-4b's two arms
the wrong way round (0/4 . 2/4 projected against 2/4 . 1/4 observed). The
direction --- more topics per frame identifies more references --- held on
every model; the per-frame detail did not, because repeating a measured
per-topic vector makes the two §13.7 splits more alike than fresh topics
are, which flatters `V_stab`.

## 7e. The allocation raised to the ceiling for `qwen3-4b` (2026-08-31)

r8 read `V_stab` as the leading LOCAL and SPECTRUM refusal on every
`qwen3-4b` frame and the bottleneck tool called it precision.
`tools/v8_vstab_diagnosis.py` decomposed §13.7 into its three registered
conditions and found the mechanism the summary had hidden.

| frame | arm | cands | pass `V_stab` | `V_stab` sole blocker | condition-1 failures | of those, split-noise only | equivalence points outside ±0.20 |
|---|---|---:|---:|---:|---:|---:|---:|
| f0 | LOCAL | 65 | 7 | 6 | 56 | 4 | 0 |
| f0 | SPECTRUM | 65 | 10 | 29 | 55 | 34 | 0 |
| f1 | LOCAL | 65 | 5 | 7 | 60 | 7 | 1 |
| f1 | SPECTRUM | 65 | 10 | 31 | 54 | 33 | 0 |
| f2 | LOCAL | 65 | 3 | 7 | 59 | 4 | 0 |
| f2 | SPECTRUM | 65 | 13 | 29 | 50 | 33 | 0 |
| f3 | LOCAL | 65 | 4 | 7 | 59 | 5 | 0 |
| f3 | SPECTRUM | 65 | 12 | 27 | 52 | 31 | 0 |

Three readings, and they point in different directions.

1. **`V_stab`'s dominance is largely an ordering artefact.** §13.7's
   condition 1 embeds `V_diff`, and §13.1's registered lexicographic order
   puts `V_stab` before `V_diff`. A rung outside §13.8's caliper therefore
   surfaces as a `V_stab` failure and would have failed `V_diff` regardless.
   `V_stab` is the *sole* blocker for only 6--7 LOCAL candidates per frame
   (6, 7, 7, 7 on f0--f3),
   which is the same population the bottleneck tool counted as
   precision-only, and those are the ones an allocation can move.
2. **The spectrum arm is different, and it is genuinely precision.** All 50
   to 55 SPECTRUM failures per frame are condition-1 failures, and 31--34 of
   them are components that **pass on the frame's pooled table and fail on a
   split**. Across all four frames, **221 of 332** split-level `V_coord`
   refusals carry the SE clause and nothing else. The pooled coordinate met
   `SPECTRUM_MAX_SE_IOTA` after the 2026-08-30 amendment; the split
   coordinate, at 48 topics, did not.
3. **Nothing here is two halves that disagree.** Not one equivalence failure
   on any frame or arm has a point estimate outside ±0.20; median |Δι|
   across splits is 0.023--0.050 against a bound of 0.20, and the median
   interval half-width is 0.11--0.14. Every equivalence failure is an
   interval that does not resolve. ι_A's own equivalence passes on every
   frame, though f0's interval [-0.172, 0.089] is not far from the bound.

Hence the amendment of 2026-08-31 (`CHANGES_SCIENTIFIC.md`,
`V8_FRAME_CONDITIONING.md` §4b): `qwen3-4b` alone moves to four calibration
passes — 192 distinct topics per frame, 96 per §13.7 split, the ceiling the
bank permits — and every other model stays at two. No threshold moved.

## 7f. The high-ι_A frames: geometry, not a shortage (2026-08-31)

r8's other two LOCAL gaps sit on frames whose ι_A is high, and
`tools/v8_operating_point_diagnosis.py` measures them from the same signed
records.

| | 2507 f0 | gemma f2 |
|---|---|---|
| ι_A | 0.8438 | 0.7937 |
| `V_head` admits raw solo (96 topics) | [0.1605, 0.8395] | [0.1605, 0.8395] |
| A itself inside that ceiling? | **no** (0.8438 > 0.8395) | yes |
| caliper window | [0.744, 0.944] | [0.694, 0.894] |
| overlap with the headroom band | 0.096 of 0.20 (**48%**) | 0.146 of 0.20 (**73%**) |
| candidates inside the caliper | 12, from 7 families | 12, from 9 families |
| ...also inside the headroom band | 3, from 3 families | 5, from 5 families |
| realised LOCAL-valid families | 0 | 1 |
| counterfactual: precision free | 2 | 3 |
| counterfactual: `V_head` ignored + precision free | 3 | 4 |
| A's rungs inside `TARGET_BAND` (0.50, 0.85) | **1** (n=4) | **1** (n=2) |
| widest adjacent step on A's curve | n=4→5: 0.844 → 0.172 | n=2→3: 0.794 → 0.385 |

Read together: §13.8's caliper and §13.4's `V_head` band stop overlapping as
ι_A approaches the headroom ceiling, so half the matching region is gone
before any candidate is considered; and even ignoring `V_head` *and* giving
precision away, neither frame reaches §13.15's five families. The pool is
not the constraint and more of it would not help.

Nor is the operating point a choice. §12.3 picks n\* nearest 0.70 inside
`TARGET_BAND`, exactly one of A's rungs falls in the band under each frame,
and A's curve has a cliff on either side. There is no nearby rung to prefer
and no rung to add: A's severity is an integer count and `TARGET_GRID` is
already every integer 1--8, so the grid is exhaustive over the construct.
Moving ι_A would mean changing what A is.

## 7g. The 4x pilot (r9, 2026-08-31) — qwen3-4b at the topic ceiling

`dci1v8-pilot-r9`, `qwen3-4b` alone, all nine stages signed `PASS`,
06:41Z--11:21Z at commit `41a0758`, 266,424 generations (1.85x r8), no
composed cell, no freeze. The allocation is realised on the grids, the
candidate run **and** the extension round at 192 distinct topics per frame,
96 per §13.7 split, refused otherwise on the path. Gate-2 rows match the
design exactly: 55,296 grid and 181,248 candidate.

**Every frame now identifies both arms.**

| quantity | f0 | f1 | f2 | f3 |
|---|---|---|---|---|
| n\* (96 → 192) | 3 → 6 | 7 → 7 | 4 → 3 | 4 → 5 |
| m\* | 12 → 12 | 12 → 12 | 12 → 12 | 13 → 13 |
| ι_A | .714 → .671 | .630 → .608 | .701 → .672 | .708 → .697 |
| SE(ι_A) | .0335 → .0258 | .0353 → .0247 | .0364 → .0250 | .0328 → .0236 |
| median SE(ι) | .0362 → .0258 | .0366 → .0252 | .0343 → .0248 | .0355 → .0249 |
| within the 0.05 floor | 56/65 → 62/63 | 62/65 → 62/63 | 62/65 → 62/63 | 58/65 → 62/63 |
| `V_stab` pass, LOCAL | 7 → 8 | 5 → 6 | 3 → 11 | 4 → 10 |
| `V_stab` pass, SPECTRUM | 10 → **40** | 10 → **39** | 13 → **40** | 12 → **44** |
| LOCAL-valid families | 4 → 5 | 3 → 4 | 1 → 4 | 4 → **7** |
| core / backups | T/1 → T/2 | F/2 → T/1 | F/0 → T/1 | T/1 → T/2 |
| spectrum below/above | 1/6 → **21/9** | 2/8 → **19/15** | 5/7 → **22/13** | 4/7 → **24/13** |
| coverage identified | F → **T** | F → **T** | T → **T** | F → **T** |
| projected SE(β) | .0744 → .0254 | .0516 → .0245 | .0315 → .0264 | .0639 → .0273 |
| frame state | LOCAL_ONLY | NEITHER | SPECTRUM_ONLY | LOCAL_ONLY |
| | → **L_AND_S** | → **L_AND_S** | → **L_AND_S** | → **L_AND_S** |
| `REFERENCE_SURVIVAL` | F → **T** | F → F | F → F | F → **T** |

`REFERENCE_SURVIVAL` passes on the run for the first time on this model, on
frames 0 and 3; f1 and f2 reach a core and coverage but hold 4 LOCAL-valid
families against §13.15's 5, and one backup against two.

**What it says about `V_stab`.** The residual is still finite-sample, and
the evidence for that is unusually clean:

* the median equivalence half-width fell 0.133--0.143 → 0.096--0.099 on the
  LOCAL arm and 0.108--0.122 → 0.098--0.100 on the spectrum arm, the √2 the
  design predicts;
* **not one** equivalence failure, on any frame or arm, at either
  allocation, has a point estimate outside ±0.20. The median |Δι| across the
  two 96-topic halves is 0.029--0.039 against a bound of 0.20. The two topic
  halves do not disagree; the interval simply did not resolve;
* `V_stab` is now the *sole* blocker for 2--4 LOCAL candidates per frame
  (was 6--7) and 3--10 spectrum candidates (was 27--31);
* what remains of §13.7 condition 1 is almost entirely
  allocation-**invariant**: `V_diff` 96--100 refusals per frame, against 4--6
  components that pass on the pooled table and fail on a split. At 48 topics
  per split that ratio was 34 split-noise refusals of 55 on the spectrum arm.

So the two frames still short of §13.15 are `PRECISION_LIMITED` by the
bottleneck tool's reading — with precision free, f1 would have 6 LOCAL
families and f2 five — and **there is no further allocation to spend**: 192
topics per frame is every calibration topic the bank holds.

**And qwen3-4b never had the high-ι_A problem** (§7f). Its A curve carries
five rungs inside `TARGET_BAND` on f0 against the single rung 2507 f0 and
gemma f2 each had, ι_A lands at 0.61--0.70 against an aim of 0.70, and the
caliper window sits entirely inside `V_head`'s band — 0.200 of 0.20 on every
frame, against 48 % and 73 % there. The headroom geometry is a property of a
model's response to A under a wording, not of the allocation.

## 7h. The LOCAL inclusion rule, and the precision that blocks the freeze (2026-08-31)

Two pre-freeze questions were closed after r9, neither by generating anything.

**Which (model, frame) combinations enter the LOCAL arm** (researcher
decision; `V8_FRAME_CONDITIONING.md` §4d, `run/eligibility.py`,
`tools/v8_local_eligibility.py`,
`reports/dci1v8dev/local_eligibility.md`). A frame is `LOCAL_SUPPORTED` iff it
meets the **full** registered LOCAL reference survival on its own table:
§13.8's three core references, §13.15's five LOCAL-valid families, two
admissible backups. Nothing is changed to rescue one that does not. A model is
`LOCAL_ELIGIBLE` iff at least two frames are independently supported, and then
**every** supported frame enters.

| model | root | LOCAL-supported | LOCAL-unsupported, and why | eligible |
|---|---|---|---|---|
| `qwen3-4b` | r9 (4 passes) | f0, f3 | f1, f2 — 4 families, 1 backup | yes |
| `gemma-3n-e2b-it` | r8 (2 passes) | f1, f3 | f0 — 4 families, 1 backup; f2 — no core, 1 family, 0 backups | yes |
| `qwen3-4b-instruct-2507` | r8 (2 passes) | f1 | f0 — no core, 0 families; f2 — no operating point; f3 — 4 families, 1 backup | **no** |

The two entries that surprise are `qwen3-4b-instruct-2507` f3 and
`gemma-3n-e2b-it` f0: both are recorded `LOCAL_AND_SPECTRUM` and neither is
LOCAL-supported, because the state means "core identified and coverage gate
passed" and both hold four LOCAL-valid families and one backup. **Support is
the survival requirement, not the state**, and reading the state would have
admitted them. `qwen3-4b-instruct-2507` is therefore one frame short of
eligibility at its two-pass allocation — the same margin four passes closed on
`qwen3-4b`.

**Whether the planned LOCAL confirmatory allocation is precise enough**
(`tools/v8_local_precision.py`, `reports/dci1v8dev/local_precision.md`).
§8.4 renders one frame per block, so the registered 384 confirmatory blocks
give **96 per frame**, 8 draws per cell, four composed cells per configuration
— 3,072 generations entering Δ_R(f), on **96 independent units**, because
§17.1's bootstrap resamples blocks and carries every cell mean of a drawn
block. Through §16.1's registered variance form verbatim
(`dci1v4.analysis.variance.variances`) at §16.2's own planning constants:

| | at 96 blocks/frame |
|---|---|
| SE[Δ_R(f)] | 0.0296 (range across scenarios 0.011–0.047) |
| simultaneous 95 % half-width | **0.078** (estimates 0.050–0.087) |
| Δ_R's registered precondition | **0.05** |
| ~80 %-power MDE | 0.103 (estimates 0.066–0.114) |

The only rows clearing the precondition are the v7 rehearsal's central
measured value — which lands on 0.0500, the precondition to four decimals —
and the optimistic end of that rehearsal's recorded range. In percentage
points: **effects of about seven to eleven points would usually be detected,
and effects of five points or less would usually remain unresolved**, while
§11.9's smallest effect of interest is 0.10. The allocation sits on its own
SESOI with no margin. **Three passes over the confirmatory topics (288 blocks
per frame) bring every non-bound scenario inside the precondition**, and four
passes — every confirmatory topic under every frame — is the topic-bank
ceiling.

The projection is labelled `PROJECTION_NOT_REGISTERED_FOR_INFERENCE` and gates
nothing: §17.3 evaluates precision on the realised confirmatory interval and
`INSUFFICIENT_PRECISION` is its registered, non-terminal consequence.

## 7i. Both gaps closed, and what each cost (2026-08-31)

Two decisions followed §7h, and neither moved a threshold.

**The confirmatory allocation is three passes** (`V8_FRAME_CONDITIONING.md`
§4e, `rules.CONFIRMATORY_FRAME_OFFSETS = (0, 1, 2)`). A confirmatory pass is
§4a's calibration pass applied to the confirmatory blocks: every registered
block rendered under one frame, pass *p* offset by `offset_p`, offsets
distinct modulo `N_WORDINGS` so no block recurs inside a frame and the count
is a count of independent units.

| | 1 pass | 2 passes | **3 passes** | 4 (ceiling) |
|---|---|---|---|---|
| blocks per frame | 96 | 192 | **288** | 384 |
| SE[Δ_R(f)] | 0.0296 | 0.0209 | **0.0171** | 0.0148 |
| simultaneous 95 % half-width | 0.0779 | 0.0551 | **0.0450** | 0.0390 |
| ~80 %-power MDE | 0.103 | 0.073 | **0.059** | 0.051 |
| meets the 0.05 precondition | no | no | **yes** | yes |

(§16.1's registered variance form at §16.2's own planning constants, at F1's
Šidák value.) Three is the smallest allocation that clears the precondition,
so three is what was bought. The two scenarios that still miss at 288 are the
two that are explicit *bounds* — `WORST_CASE`'s p(1−p) = 0.25 with ρ = 0, and
`CALIBRATION_ANCHORED`'s ρ measured between two different constraints' solo
cells — and they need 585 and 522 blocks per frame against a 384 ceiling, so
no feasible allocation reaches them. The cost is 3× the confirmatory
generation. One consequence is recorded rather than left implicit: the
spectrum coverage projection is *defined* at the blocks a frame will hold, so
condition 4 now projects at 288, and r8/r9's SPECTRUM verdicts are
conservative with respect to this design — `reports/dci1v8dev/coverage_at_288.md`
restates all sixteen read-only, of which exactly one would differ. The LOCAL
arm reads no block count and is invariant.

**`qwen3-4b-instruct-2507` runs at the calibration ceiling** (§4b). Four
passes, 192 topics per frame, 96 per split, rerun from `PILOT_REGISTERED` in
root `dci1v8-pilot-r10`; r8 untouched. The question it answers is narrow and
was fixed before the run: does f3 — 4 LOCAL-valid families against §13.15's
5, and 1 admissible backup against 2 on r8 — reach full survival at the
allocation that closed the same gap for `qwen3-4b`'s f0 and f3, and does the
model therefore reach the two supported frames §4d requires. Its f0 is not
reopened: §7f's high-ι_A geometry, which no allocation touches.

## 7j. Both runs, and the four-model picture (2026-08-31 / 2026-09-01)

**r10 — `qwen3-4b-instruct-2507` at the calibration ceiling.** Nine stages
`PASS`, 196,608 calibration generations (64 forwarded rungs x 192 topics x 4
draws x 4 passes, exact), Gate 2 in 5 h 13 m on one card.

| | r8 (2 passes) | r10 (4 passes) |
|---|---|---|
| f0 | operating point at ι_A 0.844, no core | **no operating point** |
| f1 | 6 families, 2 backups — supported | **7 families, 2 backups** — supported |
| f2 | no operating point | no operating point |
| f3 | 4 families, 1 backup | **3 families, 0 backups** |
| eligible | no | **no** |

The finding is not "the allocation failed" but "the shortfall was an
artefact": §13.7 requires each rung to be independently admissible on **each
split**, and at 48 topics per split that test could not resolve a `V_diff`
failure on split B for MK1 and MK8. At 96 it does. `V_stab` refusals are "not
independently admissible on one split" in 64 of 64 cases at four passes and
64 of 65 at two, and the equivalence interval narrowed exactly as more data
should make it ([−0.167, +0.104] → [−0.122, +0.073], point −0.031 → −0.026).
f0 tells the same story: A's compliance falls 0.855 → 0.204 between
severities 4 and 5, so §12.3 refuses an operating point where two passes had
produced ι_A = 0.844.

**r11 — `gemma-3n-e4b-it`, the fourth model, never previously piloted in
v8.** Nine stages `PASS` at the **default** two passes (93,696 calibration
generations from 61 rungs), Gate 2 in 7 h 06 m — e4b runs about half the
throughput of the Qwens. All four frames reach a supported operating point
and **all four identify the spectrum**, which no other model has managed at
the default allocation; the LOCAL arm yields one supported frame (f3: 6
families, 2 backups) with f1 at 4-and-1.

**The four-model picture, which is the first complete one:**

| model | root | passes | LOCAL-supported | eligible | spectrum identified |
|---|---|---|---|---|---|
| `qwen3-4b` | r9 | 4 | f0, f3 | **yes** | 4/4 |
| `gemma-3n-e2b-it` | r8 | 2 | f1, f3 | **yes** | — |
| `qwen3-4b-instruct-2507` | r10 | 4 | f1 | no | — |
| `gemma-3n-e4b-it` | r11 | 2 | f3 | no | 4/4 |

Two of four models carry the LOCAL arm, with two supported frames each, so
**four (model, frame) Δ_R(f) estimates would be generated**. The two
ineligible models both have live spectrum arms, which makes §10 item 6 —
whether an ineligible model still runs the difficulty-response arm — the
consequential open question rather than a formality.

## 7. What the pilot cannot tell you

That the effect exists; that v8 works; anything about B+R or R+B; which
frames to keep. A pilot whose three decided criteria hold, together with an
explicit researcher judgment on the wording diagnostic, licenses a freeze of
the v8 candidate as a registration to be written; one whose criteria fail
names the stage and the rule that failed on a signed record, and the
candidate is revised there.

The report shows, per frame: whether the frame produces an interpretable
difficulty ladder (ladder classes at the screen and at calibration);
whether its ι estimates are stable across fresh topics (share of (frame,
rung) inside the §13.7 bound between the screen and the second pass, and
between the two calibration splits); how strongly difficulty depends on
wording (τ², spreads, class shares); whether enough LOCAL and SPECTRUM
candidates survive (Gate 3's survival block); and every wording-sensitive
or unresolved rung with its standing in the reference set.

**The decision report** (`tools/v8_wording_decision.py`, 2026-08-30) reads
the signed Gate-2 and Gate-3 records and the Gate-2 rows of one root and
writes `reports/dci1v8dev/wording_decision.{md,json}` answering the five
questions the wording policy turns on: (1) per (family, q) the four frames'
ι ± SE, spread and class, pooled and on each split; (2) whether any frame is
a systematic outlier (leave-one-out over rungs, ties sharing credit);
(3) whether flagged differences replicate on Calibration-A and
Calibration-B separately; (4) whether flagged rungs are LOCAL-valid,
SPECTRUM-valid, core, selected spectrum points or backup rungs; (5) for the
strongest cases the four exact prompts, the observed-count distribution and
representative outputs per frame. It ends with the evidence bearing on each
of the three options and chooses none. It reads no stage beyond Gate 3,
refuses a composed row, and on a root without a Gate-2 record says so and
lists the stages that must finish (exit 2). The synthetic walk's copy
(`wording_decision.synthetic.md`, fixtures, no wording effect by
construction) shows only the report's shape.
