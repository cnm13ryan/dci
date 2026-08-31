# DCI-1 v8 — the wording frame is part of the experimental condition (Approach A)

**Status (2026-08-30, branch `dev/v8-canonical`; researcher decision).**
Design note of record for how the v8 candidate treats its four wording
frames after the first real pilot. Approach A below is **approved** and is
what `dci1v8dev.run` implements from this date; Approach B is recorded as
the alternative that was considered and rejected for the current study.
Nothing here is registered, nothing is frozen, and no composed or
interference outcome (B+R, R+B, Δ_R, δ_diff) exists or may be produced
before a freeze. The pilot manifest binds this document by hash.

## 1. What forced the decision

The v8 instrument states every exact-count constraint (A and MK1–MK8) under
four reasonable wordings of one rule (`wording_v8.V8_FRAMES`):

    f0  Use the word X exactly q times.
    f1  Your answer must contain the word X exactly q times.
    f2  Include the word X exactly q times in your answer.
    f3  The word X must appear exactly q times.

Every other family, and B, likewise carries four wordings (v7's). A block
(one topic) is rendered under one frame, `block.index % 4`, so each frame
meets a quarter of the topics of every cell (§8.4's allocation, kept). At
**Gate 2** each run is laid out over two such allocations (§4a), so a
calibration frame meets half the topics rather than a quarter.

The first real pilot (`V8_PILOT.md` §7a; root `dci1v8-pilot-r3`,
qwen3-4b-instruct-2507, 2026-08-30) measured A's solo compliance per frame
on the 192 calibration topics (48 topics × 4 draws per frame):

| A at q | f0 | f1 | f2 | f3 | pooled |
|---|---|---|---|---|---|
| 4 | 0.812 | 0.974 | 0.964 | 0.932 | 0.921 |
| 5 | 0.219 | 0.682 | 0.417 | 0.521 | 0.460 |
| 6 | 0.240 | 0.615 | 0.312 | 0.688 | 0.464 |
| 7 | 0.182 | 0.500 | 0.156 | 0.385 | 0.306 |
| 8 | 0.422 | 0.469 | 0.255 | 0.651 | 0.449 |

The differences are 0.34–0.46 at q = 5–8, replicated on both calibration
splits (8 of 11 flagged rungs replicate with the same sign beyond the §13.7
bound), and family-specific: f0 is the hardest frame for A at every q ≥ 4
and f3 the hardest for B at every m ≥ 8. Pooled over frames, A's curve
jumps across the whole target band between q = 4 and q = 5 and §12.3 ends
the replication (`GRID_RESOLUTION_INSUFFICIENT`); under f0, f1 and f3
alone the band resolves. The instrument, read as one difficulty scale, is
out of regime because its four frames are not exchangeable on A.

## 2. Approach A — approved: the frame is part of the condition

The same underlying instruction under different reasonable wordings is
allowed to have different measured difficulty. Difficulty is defined
conditionally,

    ι(X, f) = (p(X, f) − κ(X, f)) / (1 − κ(X, f)),

where X is an instruction rung (a family at a severity, or A at n, or B at
m) and f ∈ {0, 1, 2, 3} is the wording frame of the block. The frame
identity is then carried through every step that reads a difficulty:

1. difficulty is estimated separately within each frame;
2. the usable operating point is chosen separately within each frame:
   n*(f) for A and m*(f) for B by §12.3 on that frame's own curves, and
   §12.4's adequacy on that frame's own rates;
3. a candidate reference R is matched to A **within the same frame**,
   ι(R, f) against ι_A(f); ι(R, f₁) is never compared with ι_A(f₂);
4. LOCAL validity (v7's full V(R), unchanged) is decided per (R, f);
5. SPECTRUM validity (v8's rule, unchanged) is decided per (R, f);
6. core references, spectrum points, coverage and backups are selected per
   frame, by the registered kernels, on that frame's table;
7. the eventual interference quantities are estimated per frame — Δ_R(f)
   from frame f's core references at frame f's operating points, and the
   difficulty-response relation from frame f's spectrum — and frames are
   compared or combined **only after** the frame-specific estimates exist.

The scientific question becomes: *within a fixed reasonable wording, does A
hurt B more than other companions of comparable difficulty?* A later
cross-frame analysis asks whether that answer itself depends on the
wording: the four Δ_R(f) reported side by side, their signs and magnitudes
compared, and — if a researcher registers it — an explicitly modelled frame
variation or a clearly defined average. No frame-specific estimate is ever
silently averaged into one number.

**What Approach A does not claim.** It does not claim that wording is
scientifically meaningful, and it does not select a "best" wording. It
declines to *assume* that one wording-independent difficulty coordinate
exists, because the pilot does not support that assumption; whether the
matched-reference result generalises across reasonable phrasings is then a
measurable question rather than an averaged-away one.

## 3. Approach B — rejected for the current study: one canonical wording

Choose one frame (f1, say, the frame under which the band resolved most
comfortably) and define the whole study on it: one difficulty scale, one
operating point, one reference pool, one Δ_R.

*For it:* simplicity — the registered v7 machinery runs unchanged with one
table; every reference is calibrated on all 192 topics instead of 48;
one estimand, one report.

*Against it:* it throws away the pilot's discovery that reasonable
wordings of one rule produce substantially different behaviour; it reduces
the scientific claim to one arbitrarily selected wording, chosen *after*
seeing which wording made the band resolve on one model; a different model
may favour a different frame (on this one, f1 is easiest for A and f3 the
hardest for B, so no single frame is "the" outlier); and it makes the
wording an unexamined nuisance the conclusion silently depends on.

## 4. The trade-off, and why A

A is preferred because it takes the observed wording sensitivity seriously
rather than averaging it away; avoids pretending that one
wording-independent difficulty coordinate exists when the data do not
support it; avoids an arbitrary post-pilot choice of a "best" wording;
preserves more information (four calibrated tables instead of one);
lets the matched-reference result be tested across reasonable phrasings;
and gives the eventual conclusion a built-in robustness test.

Its cost is real and is not hidden:

* **Calibration precision per frame** was that of 48 topics × 4 draws at
  the first allocation, not 192 × 4. On r3's grid rows the topic-level SE of
  a mid-range rate per frame is 0.04–0.058 (A at q = 5–8; B at m = 8–11),
  against ≈ 0.025 pooled; r5/r6 then measured a median per-frame SE(ι) of
  **0.0497** against the coordinate floor SE(ι) ≤ 0.05
  (`rules.SPECTRUM_MAX_SE_IOTA`), and no rung below A survived `V_coord`.
  **Amended 2026-08-30 (§4a): two calibration passes, 96 topics per frame.**
  The rules were not relaxed for this and are not relaxed now: a frame that
  cannot pin its coordinates at the allocation records that.
* **Potentially different n*(f), m*(f), references and support per frame.**
  A frame can identify LOCAL and not SPECTRUM, SPECTRUM and not LOCAL,
  both, or neither; a frame can have no admissible operating point at all.
  These are explicit states on the record, never collapsed into one.
* **Confirmatory precision per frame is that of 96 blocks**, not 384: the
  registered allocation (384 blocks × 8 draws, wording by block) puts a
  quarter of the blocks under each frame, so a frame-specific Δ_R(f) or
  slope has twice the standard error of the pooled quantity. The
  design-time coverage projection (`spectrum.coverage`) is computed for the
  frame's share of blocks (`rules.CONFIRMATORY_BLOCKS_PER_FRAME` = 96) and
  the full-allocation projection is recorded beside it for the allocation
  decision (§10).
* More downstream estimates and a more complicated report: four of
  everything, then a cross-frame section.

## 4a. The calibration allocation (amended 2026-08-30)

Approach A makes the calibration allocation a *per-frame* question, and
r5/r6 answered it with a measurement: at one frame per block a frame is
calibrated on 48 topics, the median SE(ι) is 0.0497 against the unchanged
0.05 floor, `V_coord` refuses 21 of ~30 rungs below A and `V_stab` 9, and
no frame reaches a spectrum. The amendment is to measure more, not to
admit more.

**The rule** (`rules.CALIBRATION_FRAME_OFFSETS = (0, 2)`). Gate 2 lays each
of its backend runs out over one **calibration pass** per frame offset. A
pass renders every calibration topic under one frame; pass *p* shifts the
frame by `offset_p`, so the topic at position *i* is met under frame
`(i + offset_p) % 4`. Two passes at distinct offsets therefore

* put every one of the 192 topics under **two** frames,
* give every frame **96 distinct topics**, 48 from each §13.7 split,
* repeat **no** topic inside a frame — the offsets are distinct modulo
  `N_WORDINGS`, asserted in `rules` — so a frame's per-topic vector has one
  entry per topic and the *topic*-level SE falls by √2 (extra draws would
  not have done this: every estimator averages draws within a topic first),
* pool **no** frame with another: every frame still has its own curves,
  n\*(f), m\*(f), ι_A(f), §13.11 table, validity, selection and estimand,
* cost exactly **2× the Gate-2 generation** and nothing else.

`calibration.calibration_blocks` bases pass *p* at a block index congruent
to `offset_p` and past every earlier pass's range, so block ids and row
identities stay disjoint **and** the one invariant every reader uses —
`frame = block_index % N_WORDINGS` (`execute.frame_of_block`) — keeps
holding on every row. `calibration.assert_allocation_realised` then checks
the allocation **on the generated rows** of the grids, the candidate run
and the extension round: every frame on the designed number of distinct
topics, balanced across the two splits, refused otherwise. The realised
counts and the rule are on the Gate-2 record
(`calibration_allocation`), carried to Gate 3, and bound by the manifest.

**What it is not.** Not a threshold change: `SPECTRUM_MAX_SE_IOTA`,
§13.7's equivalence bound, §13.8's caliper, the spectrum geometry, the
chance rules and the selection kernels are byte-identical. Not a pooling:
the second pass of *frames* is not a pooling *over* frames. Not a claim
that it will work — whether the extra precision lets the registered rules
admit references is what the next pilot measures.

**The ceiling.** A frame cannot be measured on more than the 192
calibration topics, which is `N_WORDINGS` passes (every block under every
frame, 4× generation). Two passes is half of the reachable range.

**What it bought, measured** (`V8_PILOT.md` §7d, root `dci1v8-pilot-r8`,
2026-08-30). Median per-frame SE(ι) fell by 1.39–1.40× — the √2 the design
predicts — and coordinates inside the unchanged 0.05 floor went from
54/68/75 % to 92/93/89 %. Spectrum coverage is identified on 7 of 11
supported frames against **0 of 11** at one pass, and `LADDER_COVERAGE`
passes on every model where it failed on every model before.
`REFERENCE_SURVIVAL` passes on `qwen3-4b-instruct-2507` (f1) and
`gemma-3n-e2b-it` (f1, f3) — the first v8 replications to clear it. The
LOCAL arm improved but its two leading refusals (`V_stab`, `V_head`) did
not change rank, and `V_head` is a statement about the candidate, so the
residual LOCAL gap is not purely an allocation question. Whether to spend
the remaining 2× to reach the ceiling is §10 item 1a.


## 4b. The allocation is per model, and `qwen3-4b` runs at the ceiling (amended 2026-08-31)

r8 left `qwen3-4b` short on both arms — f0 `LOCAL_ONLY`, f1 `NEITHER`,
f2 `SPECTRUM_ONLY`, f3 `LOCAL_ONLY` — with `V_stab` the leading
first-failing component on every frame. §4a read that as precision and
stopped there. `tools/v8_vstab_diagnosis.py` finished the reading, and the
answer changes what the next allocation buys.

**What `V_stab` actually asks** (`stages/stability.stability_verdict`,
§13.7): three conditions, of which only two are about the bootstrap.

1. R is independently admissible on Calibration-A **and** on
   Calibration-B, *each split evaluated alone*, under `V_head`, `V_chance`,
   `V_inter`, `V_diff` (the spectrum arm reads `V_coord`, `V_chance`,
   `V_inter_s` instead);
2. the 95 % percentile-bootstrap interval for `iota_A - iota_B`, topics
   resampled within split, lies wholly inside ±`STABILITY_EQUIVALENCE_BOUND`;
3. the same interval for `p_solo_A - p_solo_B`.

Condition 1 is **not** a precision statement — it re-runs four candidate
components at *half* the frame's topics. That is where r8's refusals came
from: on `qwen3-4b`, **221 of 332** split-level `V_coord` refusals carried
the SE clause and nothing else, and 34 of f0's 55 spectrum failures were
components that *pass on the frame's pooled table* and fail on a split.
The pooled coordinate satisfied `SPECTRUM_MAX_SE_IOTA` (median SE(ι)
0.0356); the split coordinate, at 48 topics, did not.

Two further readings matter. Of f0's 58 LOCAL failures only **6** have
`V_stab` as their sole blocker — the rest also fail a component no
allocation touches, and `V_stab` is merely first in §13.1's registered
lexicographic order, which "decides which reason is recorded and not which
candidates pass". And **no** equivalence failure on any frame has a point
estimate outside the bound: every one is an interval that does not resolve,
never two halves that genuinely disagree.

**The rule** (`rules.CALIBRATION_FRAME_OFFSETS_BY_MODEL`). The allocation
becomes a property of the replication. `qwen3-4b` runs four passes at
offsets (0, 1, 2, 3): every topic under every frame, **192 distinct topics
per frame, 96 per §13.7 split** — the ceiling of §4a, since the bank holds
exactly 192 calibration topics and every other set is reserved. Every other
model keeps (0, 2), so r8's meaning and any later run of those models are
untouched. `calibration_allocation` on the Gate-2 record names the model,
the offsets, whether they were the default, and whether the run sits at the
ceiling; the signed manifest binds the allocation of every model in the
study.

**What it is not.** Not a threshold change — `SPECTRUM_MAX_SE_IOTA`,
§13.7's bound, §13.8's caliper, `V_head`, `V_diff`, the chance rules, the
spectrum geometry, the slope-SE floor, the family-diversity minima, the
wording policy and the operating-point rule are byte-identical. Not a
relaxation of `V_stab`, which is unchanged in every clause. Not a claim
that it will work: whether 96 independent topics in each split let the
registered rules admit what 48 could not is what the next pilot measures.

## 4c. What the LOCAL failures on a high-ι_A frame are

r8's other two LOCAL gaps — `qwen3-4b-instruct-2507` f0 at ι_A = 0.844 and
`gemma-3n-e2b-it` f2 at ι_A = 0.794 — are a different problem, and
`tools/v8_operating_point_diagnosis.py` measures it as geometry rather than
as a shortage.

§13.8 matches a LOCAL reference inside ±0.10 of ι_A. §13.4's `V_head`
requires the *whole* Wilson interval for the candidate's raw solo
compliance inside [0.10, 0.90], which at 96 topics admits raw solo
compliance only in **[0.1605, 0.8395]** (0.8150 at 48 topics, 0.8575 at
192 — the band widens with the allocation because it is an interval test).
As ι_A approaches that ceiling the caliper window and the headroom band
stop overlapping, and no candidate can be a matched reference **however
many the pool holds**. On 2507 f0, ι_A = 0.8438 is *above* the ceiling and
only 48 % of the caliper window survives `V_head` by geometry alone; on
gemma f2, 73 %.

**Why ι_A sits there, and whether anything could move it.** §12.3 picks n\*
as A's eligible severity nearest 0.70 inside `TARGET_BAND` = (0.50, 0.85).
Under both frames exactly **one** rung falls in the band, and A's curve has
a cliff on either side of it: 2507 f0 goes 0.982 (n=3) → 0.844 (n=4) →
0.172 (n=5), gemma f2 goes 0.958 (n=1) → 0.794 (n=2) → 0.385 (n=3). There
is no nearby already-measured rung in a healthier region, and there is no
rung to *add*: A's severity is an integer count and `TARGET_GRID` is
already every integer 1–8. The grid is exhaustive over the construct.

This is a statement about the model's response to A under that wording, not
about the reference pool and not about a design choice with alternatives.
See §10 item 3.

## 5. Where the frame enters, stage by stage

| stage | frame handling | what pooled quantity remains, and its standing |
|---|---|---|
| generation (`run/execute`) | unchanged: one frame per block, `block.index % 4`; every row carries `frame` (load 1), `block_index` and `block_frame` (every load) | — |
| regime screen, second pass, retention (`run/regime`, `run/rescreen`, `prescreen/*`) | **pooled over frames, as a measurement budget only.** At 24 topics × 1 draw a frame holds six topics; no posterior on six topics can steer anything. The screen decides which rungs are *measured* at calibration — every measured rung is then calibrated under all four frames on the same blocks — and no admission, matching or selection reads a screen quantity (§12.2's registered principle). Recorded on both stage records as `frame_conditioning` | screen ι_A, the ACCEPT/REJECT/RESAMPLE statuses and the forwarded set: a budget rule, not an eligibility rule (§10 item 3) |
| Gate 1 (`run/instrument`) | the per-frame wording diagnostic (`run/wording`) is unchanged and is now the *primary* per-frame reading at screen precision | cross-frame comparison classes: descriptive |
| Gate 2 (`run/calibration`) | **two calibration passes** (§4a), then **per frame**: curves, n*(f), m*(f), §12.3 resolution, §12.4 adequacy, ι_A(f) with κ_A(f), per-split values and per-topic vectors, §13.11's table on the frame's own rows (§13.2's chance basis is the unconstrained cell of *the same blocks*, enforced by the producer), κ(R|B) at m*(f) on frame f's B-solo cell, degenerate rows withheld per frame, the extension reach per frame | `descriptive_pooled`: the frame-pooled solo curves and what §12.3 would have said on them — read by nothing; no pooled §13.11 table is written |
| Gate 3 (`run/references`) | **per supported frame**: folded §13.7 stability against ι_A(f) by split, ι_A(f)'s own stability, `classify_pool` (LOCAL and SPECTRUM) at ι_A(f), §13.8's core kernel, `select_spectrum`, `selected_coverage` at the frame's block share, `admissible_backups`; the frame's state | `cross_frame`: per family, which rung each frame chose; agreement counts — descriptive |
| report (`run/report`) | the three decided criteria evaluated per frame; the run-level verdict names the frames meeting them | the run-level `passed` is "at least one supported frame passes" with every frame's verdict beside it (§7) |
| post-freeze (not built) | Δ_R(f), the difficulty-response fit, per frame; cross-frame comparison afterwards | a cross-frame average only if registered as such |

## 6. Definitions the implementation uses

* **Block frame.** `frame_of_block(row) = block_index % N_WORDINGS`, equal
  to `frame` on every load-1 row (asserted at scoring) and defined on the
  unconstrained rows too, which is what lets κ be read per frame.
* **κ(X, f).** X's compliance on the unconstrained cells of frame f's
  blocks. The unconstrained cell states no wording, so κ is frame-free in
  expectation; it is nevertheless measured on the frame's own blocks
  because §13.2 says "the same topic set" and `_calibration_rows` refuses a
  chance measured on a different topic set from the solo cell. The cost is
  precision (96 topics at the two-pass allocation of §4a, not 192; 48
  before it); the record carries the frame-pooled κ beside it as a check.
* **Operating points.** n*(f) = `select_target` on frame f's A curve;
  m*(f) = `select_focal` on frame f's B curve, with §7.2's extension
  {15, 16} measured (on every block) when any frame needs it; the
  bracketing rule and `OPERATING_POINT_AT_GRID_BOUNDARY` per frame.
* **Supported frame.** A frame with n*(f), m*(f) and §12.4 adequacy on its
  own rates. An unsupported frame records the §12.3/§12.4 status it hit
  (`TARGET_RANGE_EXHAUSTED`, `FOCAL_RANGE_EXHAUSTED`,
  `GRID_RESOLUTION_INSUFFICIENT`, `REGIME_NOT_FOUND`) and takes no further
  part; the other frames continue. **The replication is terminal only when
  no frame is supported** — the status raised is the earliest step of the
  §12.3 → §12.4 sequence at which some frame failed, and the record carries
  every frame's status. No existing registered rule requires one frame's
  failure to end the others: §12.3 and §12.4 are statements about a curve,
  and under Approach A each frame has its own.
* **Calibration pass.** One rendering of every calibration topic under one
  frame each (§4a); `rules.CALIBRATION_FRAME_OFFSETS` names them and
  `rules.CALIBRATION_TOPICS_PER_FRAME` is what a frame's table is measured
  on.
* **The calibration population** is the second pass's forwarded set,
  measured once on every block of every calibration pass (so under every
  frame, on the frame's whole allocation). The extension round
  measures the union of the frames' plans, each frame's plan bounded by the
  existing rule (≤ 2 reserve rungs per deficient side per family, one
  round); a rung measured for one frame is data for every frame.
* **LOCAL(R, f)** = v7's full V(R) on frame f's pooled row with ι_A(f),
  solo_A(f) and A's frame topic count; V_stab is §13.7's folded verdict on
  frame f's two split rows against ι_A(f) on each split. **SPECTRUM(R, f)**
  = v8's rule (`spectrum/validity`) on the same rows at ι_A(f).
* **Selection per frame.** `admit_core_references(require_spectrum=False)`
  on frame f's pooled table; `select_spectrum` on frame f's spectrum-valid
  rows; `selected_coverage` with `n_blocks = CONFIRMATORY_BLOCKS_PER_FRAME`
  in the precision projection; `admissible_backups` from frame f's LOCAL
  verdicts.
* **Frame state** (`stages.FRAME_STATES`): `UNSUPPORTED` (no operating
  point), `NEITHER`, `LOCAL_ONLY`, `SPECTRUM_ONLY`, `LOCAL_AND_SPECTRUM`,
  where LOCAL means the three core references are identified by §13.8 and
  SPECTRUM means `selected_coverage` is identified; §13.15's ≥ 5 LOCAL-valid
  families and the backup count are reported beside the state as the
  freeze-support facts they are.
* **Estimands** (represented, not generated): Δ_R(f) per frame and per
  core reference; the difficulty-response slope per frame; secondary: the
  four Δ_R(f) compared. The Gate-3 record's `estimands` block states them.

## 7. The report's aggregation rule (a recorded choice)

Each decided criterion (`LADDER_COVERAGE`, `CHANCE_BASIS`,
`REFERENCE_SURVIVAL`) is evaluated on every supported frame and recorded
per frame. The run-level `passed` of a criterion is **"at least one
supported frame passes"**, with `frames_passing` and `frames_failing`
listed; `pilot_status` follows the same rule and
`frames_meeting_all_decided_criteria` is on the record. This is an
aggregation for the pilot's one-line status, not a threshold and not a
freeze rule: a freeze decision is per frame (a frame can be frozen with
its own references, or the researcher can require agreement across
frames), and the researcher reads the per-frame table. "Every supported
frame" was rejected as the aggregate because it would let one weak frame
report the pilot as failed, which is the collapse this design exists to
avoid; "any frame" never hides a failing frame because every frame's
verdict is beside it.

## 8. What stays pooled, and its standing

* The regime screen and the second pass (measurement budget; §5).
* The cross-frame comparison of ι (`run/wording.py`): it is *about* the
  frames and is the secondary analysis, not a pooled primary.
* `descriptive_pooled` on the Gate-2 record: the frame-pooled solo curves of
  A and B and §12.3's reading of them, kept so a reader can see what the
  pooled instrument would have said. Read by no stage.
* Nothing else. There is no pooled §13.11 table, no pooled ι_A, no pooled
  core set, no pooled spectrum, and the record fields `iota_a`, `m_star`,
  `calibration_rows`, `core_references` no longer exist at the top level of
  any record — every one lives under `by_frame[f]`.

## 9. Safeguards, unchanged

Fresh Calibration-A second pass (per batch and per row); Calibration-B
untouched by any selection; the bounded second-pass budget; every generated
row scored and accounted for (`row_accounting` on the path); provenance on
every row (frame, block frame, family, severity, topic, split, run, seed,
observed count, exact-compliance verdict; chance on the record); the
composed-cell block at the renderer, the row plan and the generation seam;
§13.11's closed schema on every per-frame table; the pilot ends at the
report and cannot freeze.

## 10. Remaining researcher decisions (genuine ones only)

1. ~~**Calibration allocation per frame.**~~ **Decided 2026-08-30** (§4a):
   two calibration passes, 96 topics per frame, 2× Gate-2 generation, no
   threshold moved. Run, and it did what it was bought for (§4a).
1a. ~~**Whether to spend the remaining 2× and reach the ceiling.**~~
   **Decided 2026-08-31** (§4b): for `qwen3-4b` only, four passes at 192
   topics per frame; every other model stays at two. The projection said
   the ceiling buys one model and costs 2× on all three, so it was bought
   for the one — and `tools/v8_vstab_diagnosis.py` then gave the mechanism
   the projection lacked: §13.7 condition 1 evaluates `V_coord` on each
   *split*, at half the frame's topics, and 221 of 332 of `qwen3-4b`'s
   split-level `V_coord` refusals were the SE clause alone.
3a. **The two high-ι_A frames** (`qwen3-4b-instruct-2507` f0 at 0.844,
   `gemma-3n-e2b-it` f2 at 0.794). §4c measures why LOCAL fails there:
   `V_head`'s Wilson band and §13.8's caliper stop overlapping as ι_A
   approaches the headroom ceiling, and A's grid holds exactly one rung in
   `TARGET_BAND` under each frame with no integer severity to add. The
   choice is to accept those two frames as LOCAL-unsupported — the
   recommendation the evidence supports — or to change what A is, which is
   a change to the construct and not to a measurement.
2. **Confirmatory allocation per frame.** The registered 384 blocks give 96
   per frame; Δ_R(f) at 96 blocks has twice the pooled SE. The precision
   preconditions (§16) were set for the pooled estimand. Keep the total and
   accept per-frame precision, or multiply the allocation.
3. **A frame-aware screen.** The screen and second pass pool the frames as
   a budget rule (§5). A frame-aware second pass would need many more
   topics per batch; the pilot's per-frame calibration will show whether
   the pooled budget rule loses frame-specific caliper rungs.
4. **The cross-frame summary's form** (comparison only, a registered
   average, or a modelled frame term) — a post-freeze registration item.

## 11. Record fields (producer/consumer contract)

`GATE_2_CALIBRATION`: `frames`, `by_frame[f]` (`status`, `n_star`,
`m_star`, `iota_a`, `kappa_a`, `solo_compliance_a`, `iota_a_by_split`,
`solo_a_by_split`, `a_per_topic_by_split`, `n_topics_a`,
`target_selection`, `focal_selection`, `grid_resolution`, `adequacy`,
`calibration_rows`, `calibration_rows_withheld`, `kappa_under_b_by_severity`,
`extension_reach`, `unsupported_reason`), `supported_frames`,
`unsupported_frames`, `descriptive_pooled`, `frame_conditioning`,
`calibration_allocation` (the passes, the offsets, the topics per frame and
per split, and the counts **realised** on the grids, the candidate run and
the extension), the extension block, the wording diagnostic,
`row_accounting`.
`GATE_3_REFERENCES`: `frames`, `by_frame[f]` (`stability`, `local`,
`spectrum`, `core`, `core_references`, `spectrum_selection`, `coverage`,
`backups`, `survival`, `wording_sensitive_rungs`, `state`), `frame_states`,
`cross_frame`, `estimands`. `PILOT_REPORT`: `criteria[name].by_frame`,
`frames_passing`, `frames_meeting_all_decided_criteria`.
