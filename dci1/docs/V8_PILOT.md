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
   the calibration basis (48 topics × 4 draws per frame per split) is the
   one that resolves it.
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
| 8 | `GATE_3_REFERENCES` | – | **per supported frame**: folded §13.7 stability against ι_A(f); `classify_pool` (LOCAL = v7's full V(R); SPECTRUM = V_coord/unfolded V_stab/V_pos); core by `admit_core_references(require_spectrum=False)`; `select_spectrum`; `selected_coverage` at 96 blocks per frame; `admissible_backups`; the frame's state; a descriptive cross-frame block; the estimands stated per frame |
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

The pilot re-runs in a fresh root at the fixed commit with the same models
and configuration; its outcome is recorded here when it has run. What it
measures per frame: n*(f), m*(f), ι_A(f), the number of calibrated
candidates, LOCAL-valid families, the spectrum-valid pool, the core
references, the selected spectrum points, the backups, and the frame's
state; and whether the frames agree.

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
