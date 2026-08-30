# DCI-1 v8 pilot — execution layer and criteria (prospective; not registered)

**Status (2026-08-30, branch `dev/v8-canonical`; revised the same day by
researcher decision --- §1a below).** The execution layer of
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
   variation --- is a later researcher decision on solo / pre-screen /
   calibration evidence only (`stages.WORDING_POLICY_OPTIONS`, status
   `OPEN` on the manifest, the registration record and the report).

## 2. The nine stages

| # | stage | generates | what it does |
|---|---|---|---|
| 1 | `PILOT_REGISTERED` | – | signs the pilot manifest once per root (documents, package, rules, both instrument hashes, models, topics, seeds, criteria, frame reference); a later replication is verified against it and refused on any difference |
| 2 | `QUALIFIED` | – | fifteen apparatus checks; fails closed with the whole list |
| 3 | `GATE_0_APPARATUS` | 12 topics × 5 cells × 4 | §19-shaped plumbing proof under the v8 frames: every cell/draw once, byte mutation refused, durable restore, v8 identity on every row |
| 4 | `REGIME_SCREEN` | cap selection 3 × 96; ladder 24 × (326 + 8 + 8 + 1) | §12.1, §12.2 under the v8 frames; κ on the unconstrained cell; frame reliability; the uncertainty-aware first pass (`prescreen.screen`) |
| 5 | `SECOND_PASS_SCREEN` | ≤ 3 batches × 24 × (rungs + 8 + 1) | `prescreen.rescreen.run_rescreen` with a real `measure`: fresh Calibration-A topics (two per area per batch, disjoint), reserve picks, A's grid; then `retention.retain` → the forwarded set |
| 6 | `GATE_1_INSTRUMENT` | – | frame criterion vs the bound reference; §7.5 over the v8 population; v8 scorer determinism; hashes frozen |
| 7 | `GATE_2_CALIBRATION` | 192 × 4 × (8 + 8 + 1) + 192 × 4 × forwarded + extension | n*, m*, adequacy (v7's rules); the forwarded set at calibration precision with B at m* absent; §13.11's table by the 7f89dae producer on the unconstrained cell; one extension round (≤ 2 reserve rungs per deficient side of a spectrum family) |
| 8 | `GATE_3_REFERENCES` | – | folded §13.7 stability; `classify_pool` (LOCAL = v7's full V(R); SPECTRUM = V_coord/unfolded V_stab/V_pos); core by `admit_core_references(require_spectrum=False)`; `select_spectrum`; `selected_coverage`; `admissible_backups` |
| 9 | `PILOT_REPORT` | – | the four criteria on the records; generation counts; what the freeze decision may rest on |

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
    .venv/bin/python tools/v8_wording_decision.py --root <root>            # the wording-policy decision report (Gate 2/3 only)

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
