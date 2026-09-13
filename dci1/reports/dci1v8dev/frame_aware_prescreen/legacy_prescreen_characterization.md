# DCI-1 v8 — the legacy (frame-pooled) pre-screen, characterized

**Status.** Deliverable 1 of the frame-aware pre-screen redesign
(2026-09-03). Everything here is read from the repository at
`dev/v8-canonical` (`ab1b6be`) and from the signed, unprotected pre-freeze
pilot records of the four study roots bound by the frozen confirmatory
manifest (`dci1v8-pilot-r9`, `-r10`, `-r12`, `-r13`); no protected
confirmatory artifact was opened and nothing was generated. The frozen
root `dci1v8-confirm-r2` and every pilot root are immutable and untouched.

## 1. What the legacy screen does, stage by stage

The path from raw first-pass rows to membership, with the code that
implements each step:

| step | where | frame handling |
|---|---|---|
| raw first-pass rows | `run/regime.py::regime_payload` → `ladder_cells` → `execute.generate_and_score` | 24 `prescreen` topics × 1 draw; one block per topic, `frame = block_index % 4` (`execute.SoloCell`), so **six topics per frame**; every row carries `block_frame`, `block_index`, `frame` |
| difficulty / chance statistics | `regime.prescreen_counts` (counts) and `regime.difficulty_table` (rates) | **sums over every block of every frame**: `solo_k/solo_n` over the 24 topics, chance on the 24 unconstrained rows; the count schema `prescreen.schema.PrescreenRung` has no frame field and *refuses* one |
| labels and statuses | `prescreen.screen.screen_families` on the pooled table and A-grid | one ι_A posterior for all frames (`a_grid_draws`, §12.3's n\* re-selected inside every draw); per family P(support both), ACCEPT / REJECT / RESAMPLE; `LOCAL_REFERENCE_CANDIDATE` iff some rung has P(inside caliper) ≥ 0.25 against that pooled ι_A |
| second pass | `run/rescreen.py::second_pass_payload` → `prescreen.rescreen.run_rescreen` | batches of 24 fresh Calibration-A topics (six per frame), planned on the **pooled** statuses and deficiencies, merged into the pooled counts; up to three batches |
| family / rung ranking | `screen_families` (`ranking_spectrum`, `ranking_local`) and `prescreen.retention.retain` | score order with the family id as tie-break; rungs ranked by P(local) and by \|pooled ι − pooled ι_A\| |
| retention caps | `retention.RetentionConfig` from `rules.RETENTION_*` | ≤ 8 spectrum families × 5 roles, ≤ 12 local families × 4 rungs, class arm 2, near-form 3; **no frame appears anywhere in the config** |
| forwarded set | `SECOND_PASS_SCREEN.forwarded_set` | one list of labels |
| Gate 2 | `run/calibration.py::gate2_payload` | measures every forwarded rung on every block of every calibration pass — hence under every frame — then builds each frame's §13.11 table from *that frame's* rows only |
| n\*(f), m\*(f), ι_A(f) | `calibration.frame_operating_points`, `frame_a_coordinate` | per frame, from the grid runs' rows of that frame; **decided before the candidate run is generated** (the grids are measured first) |
| LOCAL / SPECTRUM validity | `run/references.py::frame_references` | per frame on the frame's table against ι_A(f) |
| references, backups, coverage | same | per frame |
| membership | `confirm/membership.py` via `pilot_import.frame_inputs` | per frame |

### 1a. Where frame information exists

Every scored row (all loads) carries `block_frame`, `block_index` and, on
load 1, `frame` (`execute._score_row`); `execute.frame_of_block` is defined
on every row and asserted equal to the stated frame. Gate 1 computes and
records the per-frame screen coordinate of every rung
(`GATE_1_INSTRUMENT.frame_comparison_screen`: ι, SE, n_topics = 6 per
frame) and *no pilot stage reads it*; the only production reader is the
confirmatory `LOCAL_TOPUP` rule.

### 1b. Where it is pooled

`prescreen_counts` (sums over frames), `PrescreenRung`/`ARung` (no frame),
`screen_families` (pooled ι_A posterior, pooled per-rung posteriors),
`retain` (one `iota_a_mean`), `plan_batch` (pooled statuses, pooled
deficiency direction, pooled ι_A for the reserve direction),
`legacy.prescreen_iota_a` (pooled point estimate).

### 1c. Which pooled quantities affect forwarding

* the family status (ACCEPT / REJECT / RESAMPLE from pooled P(support both));
* the labels (SPECTRUM from status; LOCAL from pooled P(inside caliper));
* `score_spectrum`, `score_local` (family order within the caps);
* per rung: `p_admissible` (≥ 0.5 to be retainable), `iota_mean` (the
  spaced roles are assigned by distance from the pooled `iota_a_mean`),
  `p_local` (local-rung order);
* the class-arm and near-form orderings (pooled `p_local`).

### 1d. Which later stages assume the forwarded set is frame-independent

* Gate 2 generates one candidate run over every block of every pass
  (`measure_candidates(non_outcome, "candidates")`), records
  `calibration_population.measured_under_every_frame: True`, and builds
  every frame's table from the same candidate list;
* the extension round declares reserve instances for the pooled
  `retention.spectrum_families` (`extension_instances`) and evaluates each
  frame's reach only over those families (`reach_input`), then measures the
  *union* of the frames' picks on every block ("a rung measured for one
  frame is data for every frame");
* an unsupported frame (no operating point) still has every candidate
  generated on its blocks; the rows are never used;
* the confirmatory `LOCAL_TOPUP` reads `calibration_population.forwarded`
  as one set.

### 1e. Every consumer of the forwarded representation

`SECOND_PASS_SCREEN.forwarded_set` → Gate 2 (`non_outcome`);
`SECOND_PASS_SCREEN.retention.spectrum_families` → Gate 2 (reserve
instances, reach); `retention.spectrum_geometry`, `n_batches`,
`resolved_at_max` → `PILOT_REPORT.LADDER_COVERAGE`;
`GATE_2_CALIBRATION.calibration_population.forwarded` → `confirm/topup.py`,
`tools/v8_frame_screen_diagnostic.py`; `run/contracts.py` (`forwarded_set`
→ G2; `retention` → G2, RP); `tools/v8_screen_frame_audit.py`,
`tools/v8_pipeline_validation.py`, `tools/v8_prescreen_backtest.py`
(development tools).

## 2. Legacy behaviour pinned, awkward parts included

Facts about the records (`tests_v8dev/test_legacy_prescreen_characterization.py`;
fixtures `tests_v8dev/fixtures/legacy_prescreen/{gemma-3n-e2b-it.r12,
qwen3-4b.r9}.json`, extracted by `tools/v8_prescreen_fixture.py` and
carrying the record hashes they came from):

1. **Byte-for-byte reproduction.** From the recorded pooled counts and the
   recorded seed (`seeds.screen_seed(model_id, stage)`), `screen_families`
   reproduces the signed `REGIME_SCREEN` screen — statuses, labels, both
   rankings, ι_A's posterior summary, every family's score and local
   rungs. `run_rescreen`, replayed from the recorded batch counts, plans
   exactly the recorded batches (families, rungs, topics), spends the
   recorded per-family budget, resolves the recorded families at the
   maximum, and `retain` forwards exactly the recorded set with the
   recorded roles and reasons (r12: 58 rungs; r9: 59).
2. **One target for four frames.** The retention measures every rung's
   distance from one number, the pooled posterior mean of ι_A after the second pass
   (r12: 0.672; r9: 0.697), and forwards one set for every frame. Gate 2 then fixes a
   different ι_A(f) on every frame: r12 f0 = 0.754, f1 = 0.612, f2 = 0.819,
   f3 = 0.663 (spread 0.207, twice the 0.10 caliper); r9 f0 = 0.671,
   f1 = 0.608, f2 = 0.672, f3 = 0.697 (spread 0.089). The set Gate 2
   calibrated is the pooled set (`calibration_population.forwarded` equals
   `forwarded_set` on every model).
3. **The second pass's fresh topics are counted as repeated draws.**
   `PrescreenRung.merged` infers the batch layout from the counts: a batch
   whose topic count equals the table's is taken for extra *draws* on the
   same topics. Every batch measures 24 fresh Calibration-A topics into a
   24-topic table, so the record shows e.g. r12 `MK8:4` after three batches
   as `solo_n = 96, n_topics = 24, draws_per_topic = 4` — 96 distinct
   topics read as four draws on 24. The ICC design effect
   (`statistics.effective_n`, ICC 0.40) then credits them with an
   effective 43.6 topics instead of 96: the second pass under-weights its
   own evidence by up to 2.2×. A's grid is merged the same way. This is a
   defect of the legacy layout inference, not of the counts; it is kept
   exactly as it was on the legacy path (the characterization test pins
   it) and is recorded as a follow-up (§5). The frame-aware loop declares
   its layout instead (`apply_batch(..., layout="topics")`).
4. **Per-frame evidence already exists and partitions the pooled.** The
   per-frame counts recomputed from the screen rows on each frame's own
   blocks sum, rung by rung, to the pooled counts
   (`evidence.ScreenEvidence.assert_consistent`); each frame holds six
   topics at one draw (`n_topics = 6` on every Gate-1 per-frame screen
   entry: 4 × 342 entries per model).
5. **Ranking and tie-breaks.** `ranking_spectrum` is `(−p_spectrum,
   family id)`; `ranking_local` is `(−score_local, family id)`; a family
   carries `SPECTRUM_REFERENCE_CANDIDATE` iff its status is ACCEPT and
   `LOCAL_REFERENCE_CANDIDATE` iff some rung has `p_local ≥
   rules.LOCAL_LABEL_MIN` (0.25, a threshold derived for the pooled
   24-topic precision).
6. **Accounting.** The per-rung calibration cost the record priced
   retention at is the all-frames cost of the universal four-pass
   allocation (3,072 generations); r12 forwarded 58 rungs = 178,176
   candidate generations; the second pass spent the recorded
   `cost_generations` within `max_cost_generations`.
7. **Arms with no consumer.** Retention forwards a class arm (2 rungs) and
   a near-form arm (3 rungs) for §12.6's C7/C8; the frozen confirmatory
   design has neither arm (`V8_CONFIRMATORY.md` §6). Those rungs are
   calibrated on every frame (5 × 3,072 generations per model) and enter
   the frames' tables like any other rung.

## 3. The seam

`prescreen/evidence.py` — `FrameEvidence` (one frame's table and A-grid;
the schema is unchanged, the frame is the key) and `ScreenEvidence`
(every frame's evidence beside the pooled table), built by the production
count kernel on each frame's own blocks and asserted to partition the
pooled counts.

`prescreen/policy.py` — one output shape, `ForwardingPlan` (per-frame
forwarded sets, the union, `selected_by_frames` provenance, cost), behind
two named policies:

* `LegacyPooledPolicy`: the pooled screen and `retain`, one set for every
  frame — reachable only by name; the characterization tests reach the
  signed r9/r12 forwarded sets through it;
* `FrameAwarePolicy`: one screen and one `retain` per frame on that frame's
  evidence, against the frame's own screen-proxy ι_A or against a supplied
  per-frame target (`screen.coordinate_target`, e.g. Gate 2's ι_A(f) at its
  topic-level SE). Frame f's plan is a pure function of frame f's evidence
  (`tests_v8dev/test_prescreen_policy.py`).

`prescreen/screen.py::screen_families(..., target=None)` — the only edit
to the legacy screen: an optional target that replaces the A-grid
posterior; unset, the behaviour is byte-identical (pinned).

`prescreen/rescreen.py::run_rescreen_by_frame` — the staged loop with one
screen per frame and one shared batch (the union of the frames' own plans,
with `requested_by_frames` on the record); every frame absorbs the batch on
its own blocks with a declared layout; the at-max rule resolves per frame.
`run_rescreen` (pooled) is unchanged.

Behaviour preservation: the fast v8 suite passes unchanged (408 passed, 2
skipped) with the new modules beside the old ones, and the golden-master
tests reproduce both stored models.

## 4. What the seam does not change

No threshold, caliper, band, operating-point rule, validity component,
reference library, prompt, verifier, calibration allocation or
confirmatory allocation. The successor's rule (deliverable 2) is a
retention rule and a screen measurement budget.

## 5. Follow-ups recorded, not fixed here

* The batch-layout inference in `PrescreenRung.merged` (§2.3): the legacy
  pooled second pass credits fresh topics as repeated draws. Left as is on
  the legacy path so the historical records stay reproducible; the
  frame-aware loop declares its layout.
* The class-arm and near-form-arm rungs (§2.7) are forwarded to a design
  that has no such arm.
* `docs/V8_CONFIRMATORY.md` §3a still says the top-up dry run measured
  seven rungs; the records say six (already noted by
  `reports/dci1v8dev/frame_screen_diagnostic/REPORT.md`).
