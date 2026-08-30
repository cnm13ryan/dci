# DCI-1 v8 pilot — execution layer and criteria (prospective; not registered)

**Status (2026-08-30, branch `dev/v8-canonical`).** The execution layer of
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
| `FRAME_RELIABILITY` | are the repaired frames read reliably? | every v8 frame's marker-absent share over A and MK load-1 rows ≤ the best v7 frame's share on the same model (`reports/dci1v8dev/frame_reference.json`, from the stored-row audit) + 0.05 |
| `LADDER_COVERAGE` | does the screen/second pass/retention carry the ladder's geometry to calibration? | second pass resolves within 3 batches; ≥ 2 forwarded spectrum families reach both offsets at the screen; the spectrum-valid pool at calibration has ≥ 2 points from ≥ 2 families per side |
| `CHANCE_BASIS` | is κ measured on §13.2's unconstrained cell in both tables? | the screen's and Gate 2's chance basis is the unconstrained cell on every split, the column is not the zero column, ι_A is on the same basis (the all-absent v7 basis is recorded beside it) |
| `REFERENCE_SURVIVAL` | do LOCAL and SPECTRUM references survive calibration? | ≥ 5 LOCAL-valid families (§13.15 on the admissible basis), three core references by the registered §13.8 kernel, selected coverage identified with projected SE(β̂) ≤ 0.05, ≥ 2 admissible backups |

The margin on the first criterion is half the smallest effect of interest on
a rate (§11.9: 0.10), against a per-frame sampling SE of ≈ 0.015; without it
the criterion is unattainable on qwen3-4b-instruct-2507, whose best v7 frame
had 0 absent rows in 1,536. A failed criterion **terminates nothing**: it is
recorded where it is measured and summarised by the report. The only
terminal statuses are v7's apparatus and operating-regime ones
(`QUALIFICATION_FAILURE`, `APPARATUS_FAILURE`,
`RESPONSE_LENGTH_INCOMPATIBLE`, `TARGET_RANGE_EXHAUSTED`,
`FOCAL_RANGE_EXHAUSTED`, `GRID_RESOLUTION_INSUFFICIENT`, `REGIME_NOT_FOUND`).

**No composed cell.** The pilot generates load 0 and load 1 only. The
renderer refuses a two-slot cell (`execute.prompt_cell`), no stage builds
one, and the sequence ends at the report. The spectrum arm's B+X / X+B cells
are a post-freeze experiment (`V8_CANDIDATE.md` §12 step 4) that this layer
cannot produce.

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
    .venv/bin/python tools/v8_frame_reference.py --check
    .venv/bin/python -m dci1v8dev.run.cli audit                            # the producer/consumer contract
    .venv/bin/python -m dci1v8dev.run.cli plan --root /tmp/v8-plan         # what signing would bind

The synthetic walk drives all nine stages through the production runners
with v7's scripted composer (`tests_v7.synthetic_lifecycle._compose`) as the
generator, asserts the contract against real payloads, that every row
carries the v8 identity and no row is composed, that both tables read κ on
the unconstrained cell, that the second pass used disjoint Calibration-A
topics, and that the report evaluates the four criteria.

## 6. The pilot (not run here)

    cd dci1
    tools/run_v8_pilot.sh qwen3-4b-instruct-2507 <device> evidence/dci1v8-pilot <log_dir>

Sequence (V8_CANDIDATE.md §12): one model; inspect only the four criteria on
`PILOT_REPORT`; freeze v8 only if they hold; only then the spectrum arm.
Estimated generations per model ≈ 8k (cap) + 8.2k (screen) + 7–12k (second
pass) + 13k (grids) + 192 × 4 × forwarded (≈ 31–49k) + ≤ 12k (extension)
≈ 60–90k --- ≈ 1–1.5 h on qwen3-4b-instruct-2507 per card at the observed
Gate-2 throughput. No v7 lane is interrupted: the driver takes the per-card
lock the v7 driver uses and waits.

## 7. What the pilot cannot tell you

That the effect exists; that v8 works; anything about B+R or R+B. A pilot
whose four criteria hold licenses a freeze of the v8 candidate as a
registration to be written; one whose criteria fail names the stage and the
rule that failed on a signed record, and the candidate is revised there.
