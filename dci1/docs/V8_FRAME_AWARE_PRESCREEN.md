# DCI-1 v8 — the frame-aware pre-screen (successor design; prospective)

**Status.** Design note of record for the successor of the frozen v8
protocol (`dci1v8-confirm-r2`, frozen 2026-09-03 at `f7af7f2`). Written
2026-09-03 before any successor pilot ran. It amends the screen, the second
pass and the forwarding step of the pilot layer and nothing else. The
earlier freeze is **superseded for this successor design only**: its root,
its records and its preregistration are immutable historical evidence and
are not altered retroactively.

## 1. What changes, and why

Approach A (`V8_FRAME_CONDITIONING.md`) makes every quantity from Gate 2
onward frame-specific. The pilots r5–r13 screened, ranked and forwarded
candidates on counts **pooled over the four wording frames** against one
pooled ι_A (`V8_FRAME_CONDITIONING.md` §5 called it a measurement-budget
rule: six pre-screen topics per frame). The characterization
(`reports/dci1v8dev/frame_aware_prescreen/legacy_prescreen_characterization.md`)
shows the consequence on the records: one forwarded set for four frames
whose Gate-2 ι_A(f) differ by up to 0.21 (twice the reference caliper).

The successor makes the screen, the second pass and the forwarding decision
frame-specific, at the pooled screen's precision per frame, without
changing any threshold, caliper, band, operating-point rule, validity
component, reference library, prompt, verifier, calibration allocation or
confirmatory allocation.

## 2. The rule (`dci1v8dev.rules`, 2026-09-03)

| constant | value | meaning |
|---|---|---|
| `SCREEN_FRAME_OFFSETS` | `(0, 1, 2, 3)` | the first pass and every second-pass batch are laid out one pass per frame offset — every screen topic under every frame — the construction `CALIBRATION_FRAME_OFFSETS` already uses; offsets distinct modulo the wordings, so no topic recurs within a frame |
| `SCREEN_TOPICS_PER_FRAME` | 24 (derived) | distinct topics per frame at round 0 and per batch |
| `RETENTION_POLICY` | `frame_aware` | one screen and one retention per frame on that frame's own evidence (`prescreen.policy.FrameAwarePolicy`) |
| `RETENTION_TARGET_BASIS` | `calibration_iota_a` | the final retention ranks against Gate 2's own ι_A(f) at its topic-level SE (`screen.coordinate_target`), decided inside Gate 2 after the grids and before any candidate is generated |
| `RETENTION_COMPARATOR` | `legacy_pooled` | the pooled rule is measured beside the frame-aware set in a pilot (comparator arm), never admitted |
| `RESCREEN_BATCH_LAYOUT` | `topics` | a batch's counts are pooled into a frame's table as fresh topics, declared, not inferred |

The retention budgets (`RETENTION_*`), the screen thresholds
(`SCREEN_ACCEPT`, `SCREEN_REJECT`, `LOCAL_LABEL_MIN`), the second-pass
budget (`RESCREEN_*`) and the extension rule are unchanged and now apply
per frame.

## 3. Stage by stage

**`REGIME_SCREEN`.** Cap selection unchanged. The ladder screen is rendered
over `regime.screen_blocks` (four passes over the 24 pre-screen topics: 96
blocks, 24 per frame). Per frame, the counts are formed on the frame's own
blocks (`prescreen_table_by_frame`; chance on the frame's own unconstrained
cells) and screened by `screen_families` (`screen_by_frame`). The pooled
counts and screen are recorded as the legacy comparator (`screen`,
`prescreen_table`; `screen_standing`) and steer nothing. The realised
allocation is asserted on the rows (`assert_screen_allocation`).

**`SECOND_PASS_SCREEN`.** `prescreen.rescreen.run_rescreen_by_frame`: each
frame plans its own batch with the registered planner on its own statuses
and deficiencies; the batch is the union of the frames' plans
(`requested_by_frames`), rendered under every frame on 24 fresh
Calibration-A topics (four passes; topic isolation as before), and every
frame absorbs it on its own blocks with the declared layout. Stopping and
the at-max rule are per frame; the sequence cap of three batches is
global. The record carries each frame's final table and screen, the
**provisional plan** (the frame-aware policy against the frame's own
screen-proxy ι_A(f)) and the **comparator plan** (the legacy pooled policy
on the pooled counts with every batch absorbed by the legacy inference);
neither decides.

**`GATE_2_CALIBRATION`.** Grids as before → n\*(f), m\*(f), ι_A(f) per
frame → **forwarding** (`calibration.FORWARDING_RULE`): for each supported
frame, the frame's final second-pass evidence is screened against
`coordinate_target(ι_A(f), SE)` and retained with the registered budgets;
the union of the frames' sets is generated in one backend run, each rung on
the blocks of the frames whose evidence selected it (`selected_by_frames`
on the record); each frame's §13.11 table holds its own set only. The
comparator arms — the legacy pooled union and the provisional plan, minus
the frame's own set — are generated on the frame's blocks and tabled into
`comparator_rows`, never into the frame's table. The extension round runs
per frame on the frame's blocks. Every rung any policy could forward and
every candidate family's reserve are declared as instances on the grids
(scoring only). An unsupported frame generates no candidate cell.

**`GATE_3_REFERENCES`.** The frame's verdict is unchanged. A descriptive
`retention_comparison` block re-verdicts, by the same kernel on the same
calibration rows, the set each comparator policy would have had on the
frame, and the comparator eligibility per policy.

**`LOCAL_TOPUP` (confirm).** The rule is unchanged; it reads the frame's own
forwarded set (`calibration_population.by_frame[f].forwarded`).

## 4. What the successor is not

* not a change to any admission rule: `V(R)`, the SPECTRUM rule, the
  coverage gate, the core kernel, the backups, `LOCAL_ELIGIBILITY_MIN_FRAMES`,
  the top-up rule, the allocations;
* not a frame selection: every frame is screened, every supported frame
  is forwarded, nothing ranks frames against each other;
* not outcome-informed: the target is A's solo coordinate on grid rows;
  the schema of every table stays closed; no composed cell exists before a
  freeze.

## 5. Invalidation boundary

A changed retention rule changes which rungs a frame's table holds. From
the stored roots nothing after `GATE_0_APPARATUS` is reusable by the
successor: the screen is laid out differently (four passes), the second
pass plans differently, Gate 2's candidate population is different, and
every later stage reads Gate 2. The successor therefore reruns every stage
from `REGIME_SCREEN` in fresh pilot roots; the stored roots stay as they
are. Which downstream artifacts must be regenerated, and what the reruns
found, is in
`reports/dci1v8dev/frame_aware_prescreen/prescreen_revalidation.md`.

## 6. Evidence behind the design

`reports/dci1v8dev/frame_aware_prescreen/`: `legacy_prescreen_characterization.md`
(deliverable 1), `frame_aware_prescreen_design.md` (architectures,
circularity, decision), `prescreen_counterfactual.csv` and
`prescreen_feasibility.md` (the replay on the stored roots: at six topics
per frame a frame-aware screen is no better than the pooled one because
the sample size, not the frame, sets the noise; hence the four-pass
screen), `prescreen_revalidation.md` (the successor pilots).
