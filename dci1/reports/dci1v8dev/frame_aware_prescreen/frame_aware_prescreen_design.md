# DCI-1 v8 — the frame-aware pre-screen: architectures, circularity, decision

**Status.** Deliverable 2 of the redesign (2026-09-03). The rule of record is
`dci1/docs/V8_FRAME_AWARE_PRESCREEN.md`; this document is the reasoning
behind it. Numbers quoted are from the counterfactual replay on the stored
pre-freeze roots (`prescreen_feasibility.md`, `prescreen_feasibility_tables.md`,
`prescreen_counterfactual.csv`) and from the characterization
(`legacy_prescreen_characterization.md`).

## 1. The requirement

Under Approach A the wording frame is part of the condition: n\*(f), m\*(f),
ι_A(f), every validity and every selection are per frame. The legacy screen
ranked and forwarded candidates on counts pooled over the four frames
against one pooled ι_A, so a pooled coordinate decided which rungs could
reach a frame's calibration. The end state required: a candidate's
pre-screen status, difficulty information, ranking and retention decision
for frame f rest on frame f's evidence, with no hidden pooled coordinate
controlling whether it can reach frame-specific calibration.

## 2. The dependency graph, and the circularity question

The facts the choice turns on (all from the code and the records):

| question | answer | where |
|---|---|---|
| Does every candidate rung have screen observations under every frame? | Yes. The first pass renders every rung on every block; each block carries one frame. Six topics per frame in the legacy layout; 24 under one pass per frame offset. | `run/regime.py::ladder_cells`, `execute.SoloCell` |
| Does A have per-frame screen evidence before retention? | Yes, at the same precision as the candidates: A's grid on six topics per frame (legacy). The frame's screen-proxy ι_A(f) has posterior sd 0.04–0.15 at six topics + batches and drifts from Gate 2's ι_A(f) by −0.17…+0.08 (replay table "ι_A"); the pooled screen's ι_A drifts by −0.15…+0.09. | `screen.a_grid_draws`; replay |
| When is final n\*(f) known? | Inside `GATE_2_CALIBRATION`, from the grid runs (`grid-A`, `grid-B`) on that frame's rows, **before the candidate run is generated** in the same stage. | `calibration.gate2_payload`: `measure_grid` → `frame_operating_points` → `measure_candidates` |
| When is final ι_A(f) known? | At the same point: `frame_a_coordinate` reads A's solo and chance on the frame's grid rows only. Topic-level SE ≈ 0.02 on 192 topics. | same |
| Would ranking the *initial* pre-screen against final ι_A(f) create a cycle? | For the first pass and for the second pass's batch planning, yes — they run before Gate 2. For the *final* retention, no: it can run inside Gate 2 after the grids and before any candidate cell exists, and ι_A(f) depends on A's grid rows alone, never on a candidate or a composed quantity. | — |

So the cycle exists only if the target of the *final* retention is required
before Gate 2. It is broken by ordering within Gate 2, at no reordering of
the nine-stage lifecycle.

## 3. Architectures considered

**A. Frame-specific screen proxy.** One screen per frame on the frame's
own counts, ranked against the frame's own screen-proxy ι_A(f); the
forwarded sets are fixed at `SECOND_PASS_SCREEN`; Gate 2 calibrates each
frame's set on its blocks. No cycle. Simplest structurally. Its error is the
proxy's: at six topics per frame the proxy is worthless (sd up to 0.15,
drift up to 0.17 — larger than the 0.10 caliper); at 24 topics per frame
its sampling sd falls to ≈ 0.05 and what remains is the topic-set drift
between the pre-screen topics and the calibration topics, estimated from
the stored roots (pooled screen ι_A minus the frame-mean of Gate 2's ι_A(f))
at −0.045, +0.046, 0.00, −0.01 across the four models — half the caliper.

**B. A-first two-stage screening.** Measure A's grid per frame at
calibration precision *before* the second pass, then screen, re-screen and
retain against ι_A(f). Every decision, batch steering included, targets the
definitive coordinate. Cleanest scientifically; no extra compute (the grid
run moves earlier). But it splits `GATE_2_CALIBRATION` into two stages and
reorders the lifecycle, touching the stage table, transitions, contracts,
the confirm layer's pilot import (which reads Gate 2's grid rows by stage
name for the stability bootstrap and the top-up), the tools and the
harness. Not surgical.

**C. Late frame-aware forwarding** (chosen). Keep the frame-aware first
pass and second pass on the screen proxy — they decide only *what is
measured next*, a measurement-budget decision that admits nothing — and
take the substantive per-frame retention **inside Gate 2, after the grids
fix n\*(f) and ι_A(f) and before any candidate is generated**, against
ι_A(f) at its topic-level SE (`screen.coordinate_target`). This is the
existing `LOCAL_TOPUP` mechanism generalised: the top-up already ranks
frame-f screen coordinates against Gate 2's ι_A(f); the successor applies
that target to the whole retention rather than to a shortfall. No cycle
(ι_A(f) is a solo quantity of A on grid rows), no lifecycle change, and the
provisional plan of A is recorded beside it and generated as a comparator
arm, so the A-vs-C difference is *measured* in the pilot rather than
assumed.

**D. Status quo plus top-up.** The pooled screen with the frame-aware
top-up as the only frame-specific channel. Rejected: the pooled coordinate
still decides forwarding (the objective), and the replay shows the top-up
fired on one frame of one model and moved nothing.

### Comparison

| criterion | A: screen proxy | B: A-first | C: late forwarding (chosen) |
|---|---|---|---|
| scientific cleanliness | proxy target; topic-set drift ≈ ±0.05 remains in the decision | definitive target everywhere | definitive target in the decision; proxy steers measurement only |
| outcome leakage | none (solo quantities only) | none | none; ι_A(f) is A's solo coordinate, schema closed |
| circularity | none | none | none: grids precede candidates inside Gate 2 |
| statistical noise | candidate side: needs 24 topics/frame; target side: ±0.05 drift + 0.05 sd | candidate side: same; target side: SE 0.02 | candidate side: same; target side: SE 0.02 |
| compute | screen ×4; calibration Σ_f \|S(f)\| × 768 (≤ legacy worst case) | same | same, plus the comparator arms in a pilot |
| code complexity | second pass + regime | lifecycle split (most invasive) | second pass + regime + a forwarding step in Gate 2 |
| gate structure | unchanged | changed (10 stages) | unchanged (9 stages) |
| LOCAL vs SPECTRUM retention | same `retain` per frame; LOCAL reads P(inside caliper of the target), SPECTRUM reads P(support both sides of the target) | same | same |

### Why the screen budget had to change

The replay (14 supported frames, four models) settles what six topics per
frame can do: the frame-aware policy keeps 79–85 % of the calibrated
LOCAL-valid rungs and 60 % of the SPECTRUM-valid ones, forwards 13–15
never-calibrated rungs per frame whose value is unknowable, and its
round-0 forwarded set has a topic-resampling Jaccard of 0.48–0.58 against
0.63–0.72 for the pooled set — while the pooled rule *subsampled to six of
its own topics* is exactly as unstable (0.49–0.54). The instability is the
sample size, not the frame. A frame-aware screen therefore needs, per
frame, the topic count the pooled screen had. One pass per frame offset
over the same 24 pre-screen topics (every topic under every frame, the
construction Gate 2 already uses) gives each frame 24 topics at one draw
and every batch 24 fresh topics per frame, at four times the screen and
second-pass generation (≈ 33k + ≈ 36k per model against ≈ 55k for the
grids and ≈ 140–200k for the candidates).

### Why the calibration target, and what is left open

Both frame-aware targets remove the pooled coordinate; they are not
scientifically equivalent (A ranks against a proxy with ≈ ±0.05 topic-set
drift, C against the coordinate every later caliper uses, SE ≈ 0.02). On
the stored six-topic evidence the replay cannot separate them (LOCAL recall
0.79 vs 0.85; LOCAL-supported frames 8 vs 6 of 14 — differences inside the
six-topic noise). The precision argument favours C, and C is the
generalisation of a mechanism the frozen design already carries. C is the
default; A's plan is recorded on every `SECOND_PASS_SCREEN` record and its
extra rungs are generated on every frame as a comparator arm, so the
successor pilot reports both policies' identification on the same
calibration rows (`GATE_3_REFERENCES.retention_comparison`). If that
comparison favours the proxy, the change is one constant
(`rules.RETENTION_TARGET_BASIS`) and a re-run; it is a researcher decision,
flagged in `prescreen_revalidation.md`.

## 4. The chosen design, stated

1. `REGIME_SCREEN`: the ladder screen laid out one pass per frame offset
   (`rules.SCREEN_FRAME_OFFSETS = (0, 1, 2, 3)`); per-frame counts from each
   frame's own blocks (`prescreen_table_by_frame`); one screen per frame
   (`screen_by_frame`); the pooled counts and screen recorded as the legacy
   comparator, deciding nothing.
2. `SECOND_PASS_SCREEN`: `run_rescreen_by_frame` — each frame plans its own
   batch by the registered planner on its own statuses; the batch is the
   union (provenance `requested_by_frames`), rendered under every frame
   (24 fresh Calibration-A topics per frame per batch), absorbed by every
   frame on its own blocks with the declared layout; at-max resolution per
   frame. The record carries each frame's final table, the **provisional**
   frame-aware plan (screen proxy) and the **legacy pooled comparator**
   plan; neither decides.
3. `GATE_2_CALIBRATION`: grids → n\*(f), m\*(f), ι_A(f) per frame →
   **forwarding** (`FORWARDING_RULE`): each supported frame's final screen
   evidence screened against `coordinate_target(ι_A(f), SE)` and retained
   with the registered budgets; the union generated once, each rung on the
   blocks of the frames whose evidence selected it (`selected_by_frames`);
   each frame's §13.11 table holds its own set only; the comparator arms'
   extra rungs generated on the frame's blocks into `comparator_rows`; the
   extension round per frame on the frame's blocks; unsupported frames
   generate nothing.
4. `GATE_3_REFERENCES`: unchanged for the frame's verdict; a descriptive
   `retention_comparison` block re-verdicts each comparator policy's set on
   the same rows.
5. `LOCAL_TOPUP` (confirm): unchanged rule, reads the frame's own forwarded
   set.

Nothing else moves: no threshold, caliper, band, operating-point rule,
validity component, reference library, prompt, verifier, calibration
allocation or confirmatory allocation.

## 5. Invariants the tests hold

Frame f's plan is a function of frame f's evidence and the config alone
(`test_prescreen_policy.py`); identical evidence on two frames gives
identical plans; changing another frame's counts cannot move frame f's
plan; ranking and tie-breaks are deterministic and order-invariant; every
forwarded label carries the frames that selected it and a label selected
for one frame is not forwarded for another; the per-frame counts partition
the pooled counts; the legacy policy is reachable only by name and
reproduces the signed r9/r12 records byte for byte
(`test_legacy_prescreen_characterization.py`); the stage-level contracts
are in `test_frame_aware_prescreen.py`.
