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
* **Confirmatory precision per frame is that of one frame's share of the
  blocks**, not of all 384: one pass over the registered allocation (384
  blocks × 8 draws, wording by block) puts a quarter of the blocks under
  each frame, so a frame-specific Δ_R(f) or slope measured at one pass has
  twice the standard error of the pooled quantity. That is what the
  confirmatory allocation decision of §4e answers — three passes,
  `rules.CONFIRMATORY_BLOCKS_PER_FRAME` = 288. The design-time coverage
  projection (`spectrum.coverage`) is computed at that same number, and the
  projection at the registered single-pass total is recorded beside it as a
  comparator.
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


## 4b. The allocation is per model, and the Qwens run at the ceiling (amended 2026-08-31)

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

**What it bought, measured** (`V8_PILOT.md` §7g, root `dci1v8-pilot-r9`,
2026-08-31). Median per-frame SE(ι) fell 0.0356 → 0.0252, again the √2 the
design predicts, and coordinates inside the unchanged 0.05 floor went from
92 % to 98 %. **All four frames moved to `LOCAL_AND_SPECTRUM`** from
LOCAL_ONLY, NEITHER, SPECTRUM_ONLY and LOCAL_ONLY: spectrum coverage is
identified on 4 of 4 against 1 of 4, spectrum-valid points below A rose from
1–5 to 19–24, the projected SE(β) fell to 0.025–0.027 against the 0.05
floor on every frame, and `REFERENCE_SURVIVAL` passes on frames 0 and 3.
The spectrum arm's `V_stab` pass count roughly quadrupled (10–13 → 39–44),
which is what this section predicted from the split-level `V_coord` reading;
the LOCAL arm's rose far less (3–7 → 6–11), which is what it predicted
from the sole-blocker count. Frames 1 and 2 remain a family short of §13.15
and are still read `PRECISION_LIMITED` — and **there is now no further
allocation to spend**. See §10 item 1b.

**`qwen3-4b-instruct-2507` joins the ceiling (amended 2026-08-31).** r8 left
it with one LOCAL-supported frame, f1, which is one short of §4d's minimum,
so on r8's evidence the model would leave the LOCAL arm entirely. Its f3 is
the frame that decides this, and it misses on exactly the margin four passes
closed for `qwen3-4b`: **4 LOCAL-valid families where §13.15 asks 5, and 1
admissible backup where it asks 2** — the same shortfall, one family and one
backup, that `qwen3-4b`'s f0 and f3 carried at two passes and that r9's four
passes turned into 5-and-2 and 7-and-2. Its f0 is a different case and stays
retired: §4c's high-ι_A mechanism, which no allocation touches.

The raise is `rules.CALIBRATION_FRAME_OFFSETS_BY_MODEL["qwen3-4b-instruct-2507"]
= (0, 1, 2, 3)`, identical in kind to `qwen3-4b`'s: 192 topics per frame, 96
per §13.7 split, 4× Gate-2 generation, **no threshold, validity component,
grid, pool, wording frame or operating-point rule changed**, and the same
`assert_allocation_realised` check on the generated rows. It is a decision
about how much to measure, taken before Gate 3 runs on the raised
allocation — not a response to a verdict produced by it. Whether f3 then
meets §13.15 in full is a measurement, and the pre-registered possibility
that it does not is that the model stays `LOCAL_INELIGIBLE` with its
shortfall on the record.

**What it bought, measured** (`V8_PILOT.md` §7j, root `dci1v8-pilot-r10`,
2026-08-31, all nine stages `PASS`). **It did not close the gap; it showed
there was no gap to close.** f3 went from 4 LOCAL-valid families and 1 backup
to **3 and 0**, and the model stays `LOCAL_INELIGIBLE` on one supported
frame. Three things moved and each is worth reading separately.

* **f1 improved as the allocation predicts**: 6 families → **7**, backups 2 →
  2, ι_A 0.656 → 0.642. This is the `qwen3-4b` pattern.
* **f3's family set churned rather than grew**: MK1 and MK8 out, XC1 in, at an
  unchanged operating point (n\* = 6, m\* = 12, ι_A 0.664 → 0.681). The
  mechanism is §13.7's **per-split admissibility**, not its equivalence
  clause. `V_stab` refusals are "not independently admissible on one split"
  in 64 of 64 cases at four passes and 64 of 65 at two; the equivalence
  interval itself behaved exactly as more data should make it, narrowing from
  [−0.167, +0.104] to [−0.122, +0.073] about a steady point estimate of
  −0.026. What 96 topics per split resolved is a **`V_diff` failure on split
  B** that 48 could not: MK1 and MK8 were admitted at two passes because the
  split-level test lacked the power to refuse them.
* **f0 lost its operating point entirely** — `GRID_RESOLUTION_INSUFFICIENT`,
  A's compliance falling 0.855 → 0.204 between severities 4 and 5, straddling
  a whole band. At two passes the same frame produced ι_A = 0.844, the
  implausible value §4c read as geometry. The finer grid replaces a bad
  operating point with a clean refusal, which is the better record.

So the raise was worth making and the result is the opposite of
`qwen3-4b`'s: four passes turned 4-and-1 into 5-and-2 and 7-and-2 there, and
into 3-and-0 here. **192 topics per frame is the bank's ceiling, so no
further allocation exists**, and §4d forbids moving anything else. The
conclusion is that `qwen3-4b-instruct-2507` f3 was never a near-miss — it
looked like one at 48 topics per split — and the model carries one solid
LOCAL frame and leaves the LOCAL arm.

## 4f. The fourth model, measured for the first time (2026-09-01)

`gemma-3n-e4b-it` is one of the four registered v8 models and had **never
been run through a v8 pilot**: r1–r10 covered the other three, and no
decision to drop it is recorded anywhere. Its only v8 appearances were
retrospective replays over stored v7 evidence. That made every eligibility
statement before this one a statement about three quarters of the study.

It was run at the **default** two-pass allocation (`dci1v8-pilot-r11`,
2026-09-01, all nine stages `PASS`), which needed no rule change: the model
is absent from `CALIBRATION_FRAME_OFFSETS_BY_MODEL` and resolves to
`CALIBRATION_FRAME_OFFSETS`, exactly as `gemma-3n-e2b-it` did in r8. Every
other model was first measured at the default and raised only on its own
evidence; this follows that order rather than pre-empting it.

**Gate 2 supports all four frames** — operating points n\* 4–8, m\* 9–10,
ι_A 0.659–0.724 — and **Gate 3 identifies the spectrum on all four**, which
no other model has done at the default allocation. The LOCAL arm is where it
stops:

| frame | ι_A | LOCAL-valid families | backups | LOCAL |
|---|---|---|---|---|
| f0 | 0.724 | 3 (MK1, MK2, MK4) | 0 | unsupported |
| f1 | 0.703 | 4 (MK1, MK4, MK5, XC3) | 1 | unsupported |
| f2 | 0.659 | 3 (MK2, MK4, MK5) | 0 | unsupported |
| **f3** | 0.682 | **6** (MK1–MK5, XC3) | **2** | **supported** |

One supported frame against §4d's minimum of two, so the model is
`LOCAL_INELIGIBLE`. Its f1 sits on the **4-and-1 margin** — the same margin
`qwen3-4b`'s f0 and f3 held at two passes, which four passes closed, and the
same margin `2507`'s f3 held, which four passes widened. The prior is
therefore genuinely two-sided, and whether to spend the ceiling on e4b is a
researcher decision (§10 item 7), not one this section takes.

The ι_A ≈ 0.724 that `V8_CANDIDATE.md` §11 predicted from stored v7 evidence
is confirmed on f0, and its "smallest margin above A of the four models"
reading survives: e4b's LOCAL arm is the thinnest of the four and its
spectrum arm the strongest.

## 4d. The LOCAL inclusion rule, and what it leaves out (amended 2026-08-31)

r9 closed the allocation question and left the inclusion question open:
`qwen3-4b` reached the topic ceiling with two frames meeting §13.15 and two
not, and §4c had already shown that two frames on the other models fail for a
reason no allocation touches. §10 items 1b and 3a are now **decided**.

**The rule.** A wording frame is `LOCAL_SUPPORTED` iff it satisfies the
**full registered LOCAL reference-survival requirements** on its own table at
its own ι_A(f): §13.8's three core references, §13.15's
`MIN_LOCAL_FAMILIES` = 5 LOCAL-valid families, and `MIN_BACKUPS` = 2
admissible backups. Otherwise `LOCAL_UNSUPPORTED`, with every requirement it
missed named on the record.

**Nothing rescues an unsupported frame.** Not a threshold, not q\*(f) or
m\*(f), not A's grid or `TARGET_BAND`, not `V_stab`, `V_head` or `V_diff`,
not the reference pool, not the wording frame, and never a reference borrowed
from another frame. The frame stays on the record with its reason.

**A model is `LOCAL_ELIGIBLE`** iff at least
`rules.LOCAL_ELIGIBILITY_MIN_FRAMES` = 2 of its frames are independently
`LOCAL_SUPPORTED`. Two, because §1's finding is that the four frames are not
exchangeable on A: a one-frame model would license a claim that is silently a
claim about one phrasing, and the second frame is what makes the wording
dependence a measurable question rather than an unexamined one. For an
eligible model **every** supported frame enters — there is no "best two", no
ranking, and no truncation to the minimum.

**Support is not the frame state.** `FRAME_STATES`'s `LOCAL_AND_SPECTRUM`
says only that the core was identified and the coverage gate passed. Three of
the eleven frames measured so far reach it on **four** LOCAL-valid families
and **one** backup — §13.15 unsatisfied — so a rule reading `state` would
admit them. `local_supported` is computed from the survival block and never
from the state (`run/eligibility.py`, `tests_v8dev/test_local_eligibility.py`
contract 2).

**What it may not read.** Δ_R(f), δ_diff, any composed cell, any pooled
statistic over frames, and any quantity belonging to another frame. The
inputs are one frame's own `survival` block and Gate 2's support status for
that frame. Selecting frames on an outcome would be selecting on the quantity
the study exists to estimate; nine contract tests pin it, including a
structural guard on the module's executable body.

**The verdict on the evidence** (`tools/v8_local_eligibility.py`, latest run
of each model; `reports/dci1v8dev/local_eligibility.md`):

| model | root | supported | unsupported, and why | eligible |
|---|---|---|---|---|
| `qwen3-4b` | r9 (4 passes) | f0, f3 | f1, f2 — 4 families, 1 backup | **yes** |
| `gemma-3n-e2b-it` | r8 (2 passes) | f1, f3 | f0 — 4 families, 1 backup; f2 — no core, 1 family, 0 backups | **yes** |
| `qwen3-4b-instruct-2507` | r8 (2 passes) | f1 | f0 — no core, 0 families; f2 — no operating point (`GRID_RESOLUTION_INSUFFICIENT`); f3 — 4 families, 1 backup | **no** |

Two of these differ from what the frame *states* suggest, and both
differences are the §13.15 gap above: `qwen3-4b-instruct-2507` f3 and
`gemma-3n-e2b-it` f0 are `LOCAL_AND_SPECTRUM` and are **not** LOCAL-supported.
`qwen3-4b-instruct-2507` is therefore one supported frame short of
eligibility on its current two-pass allocation. Whether to spend the ceiling
allocation on it, as r9 did for `qwen3-4b` — where the same two-pass gap
(4 families, 1 backup on f0 and f3) closed to 5 and 7 families with 2 backups
each — is a researcher decision the rule does not make. See §10 item 5.

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

## 4e. The confirmatory allocation: three passes, 288 blocks per frame (amended 2026-08-31)

§4a and §4b bought precision at Gate 2, where it decides what is *admitted*.
This section buys it in the confirmatory design, where it decides what the
study can *resolve*. The question is §10 item 2 and it was open until it was
measured.

**What one pass gives, measured** (`tools/v8_local_precision.py`,
`reports/dci1v8dev/local_precision.md`). §8.4 renders one frame per block, so
one pass over the registered 384 blocks leaves each frame 96 of them — and
the block is the independent unit, because §17.1's bootstrap resamples blocks
and carries every cell mean of a drawn block, so the eight draws inside a cell
shrink the draw component and leave the topic component untouched. Through
§16.1's registered variance form at §16.2's own planning constants, and at
F1's Šidák value — the constant §16.2's table is quoted at, and an upper bound
on the bootstrap's studentised maximum-modulus value — the **simultaneous**
half-width of Δ_R(f) at 96 blocks is **0.078** against Δ_R's registered
precondition of **0.05**, and the ~80 %-power MDE is **0.103** against
§11.9's smallest effect of interest of **0.10**. The design would sit on its
own SESOI with no margin, and `claims.Interval.meets_precondition` reads
exactly the quantity that misses.

**The rule** (`rules.CONFIRMATORY_FRAME_OFFSETS = (0, 1, 2)`). A confirmatory
**pass** is the exact analogue of §4a's calibration pass: it renders every
registered confirmatory block under one frame, pass *p* shifting the frame by
`offset_p`, so the block at position *i* is met under frame
`(i + offset_p) % 4`. Three passes at distinct offsets therefore

* give every frame **288 distinct blocks**, three quarters of the 384
  confirmatory topics, at 1152 blocks in all,
* repeat **no** block inside a frame — the offsets are distinct modulo
  `N_WORDINGS`, asserted in `rules` — so a frame's 288 is a count of
  *independent units*, which is what the block bootstrap resamples over and
  what every standard error is formed at,
* pool **no** frame with another: Δ_R(f) stays frame-specific, and so does
  every reference, operating point, slope and report row,
* cost exactly **3× the confirmatory generation** and nothing else.

**Why three.** Three is the smallest allocation at which the design's own
planning row meets the registered precondition: the simultaneous half-width
is 0.0779 at one pass, 0.0551 at two — still outside 0.05 — and **0.0450** at
three, with the MDE at 0.059 against a SESOI of 0.10. Every scenario in
`local_precision.md` that is an *estimate* clears the precondition at 288:
0.0450 registered-planning, 0.0495 registered-alternate, 0.0288 on the v7
rehearsal's measured composed-cell precision, 0.0319–0.0388 with each frame's
own calibration-anchored variance decomposition at the registered ρ. The two
rows that do **not** clear it are the two that are explicitly *bounds*, and
neither is reachable at any feasible allocation: `WORST_CASE` fixes p(1−p) at
its 0.25 maximum with ρ = 0 and would need 585 blocks per frame, and
`CALIBRATION_ANCHORED`'s ρ is measured between two *different constraints'*
solo cells where the ρ governing Δ_R is between composed cells that all
measure **B**, and it would need 522 — both above the 384-block ceiling. A
fourth pass would buy 0.0390 and cannot rescue either bound; it is not bought.

**What it is not.** Not a threshold change: `PRECISION_PRECONDITIONS`,
`SMALLEST_EFFECT_OF_INTEREST`, the Šidák family, §16.1's variance form,
§17.1's bootstrap, §17.3's `INSUFFICIENT_PRECISION` consequence and every
admission rule in the pilot are byte-identical. Not a change to the estimand:
Δ_R(f) is the same contrast on the same four composed cells. Not a claim
about a value: no composed cell exists, and the projection is labelled
`PROJECTION_NOT_REGISTERED_FOR_INFERENCE` for that reason.

**What it does change, stated plainly.** The design-time coverage projection
(`spectrum.coverage.FRAME_COVERAGE_RULE`) is *defined* as the projection at
the confirmatory blocks a frame will hold, so it moves from 96 to 288 with
the design. Its threshold `SPECTRUM_MAX_SE_BETA` = 0.05 does not move, but a
projected SE(β) falls by √3, so condition 4 of §12.6's replacement — and only
condition 4 — is met by designs with about a third of the within-family
leverage it previously required. That is a consequence of measuring more, not
a relaxation, but it means **r8's and r9's recorded SPECTRUM verdicts were
evaluated against a one-pass projection and are conservative with respect to
this design**; they are not overwritten and not recomputed, and any frame
whose coverage status would differ is listed in
`reports/dci1v8dev/coverage_at_288.md`. The **LOCAL** arm is untouched in
both directions: `local_validity`, §13.8's core kernel, §13.15's family count
and `admissible_backups` read no block count, so every LOCAL support verdict
on r8 and r9 means exactly what it meant, and `tests_v8dev` pins that
invariance directly.

## 5. Where the frame enters, stage by stage

| stage | frame handling | what pooled quantity remains, and its standing |
|---|---|---|
| generation (`run/execute`) | unchanged: one frame per block, `block.index % 4`; every row carries `frame` (load 1), `block_index` and `block_frame` (every load) | — |
| regime screen, second pass, retention (`run/regime`, `run/rescreen`, `prescreen/*`) | **Superseded for the successor design (2026-09-03; `V8_FRAME_AWARE_PRESCREEN.md`).** Pilots r5–r13 pooled the screen and the second pass over frames as a measurement budget (six topics per frame) and forwarded one set to every frame. The successor lays the screen and every batch out one pass per frame offset (24 topics per frame), screens each frame on its own blocks, and Gate 2 forwards each frame's set against the frame's own ι_A(f); a rung is calibrated on the blocks of the frames whose evidence selected it. The pooled screen is recorded as a comparator and decides nothing | the pooled screen and the pooled forwarding plan: a comparator arm in the successor pilots, never an eligibility rule |
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
1b. ~~**What to do about a frame that is still `PRECISION_LIMITED` at the
   ceiling.**~~ **Decided 2026-08-31** (§4d): accept it as
   `LOCAL_UNSUPPORTED`, on the record with its reason, and let the model's
   other supported frames carry the arm — provided at least two remain. No
   threshold, operating point, grid, validity component, pool or frame is
   changed to rescue it. r9's `qwen3-4b` f1 and f2 are the first two frames
   this retires; f0 and f3 carry the model.
3a. ~~**The two high-ι_A frames**~~ **Decided 2026-08-31** (§4d): the same
   rule retires them. §4c measured why LOCAL fails there — `V_head`'s Wilson
   band and §13.8's caliper stop overlapping as ι_A approaches the headroom
   ceiling, and A's grid holds exactly one rung in `TARGET_BAND` with no
   integer severity to add — so the alternative was changing what A is, which
   is a change to the construct. `qwen3-4b-instruct-2507` f0 and
   `gemma-3n-e2b-it` f2 are `LOCAL_UNSUPPORTED`.
2. ~~**Confirmatory allocation per frame.**~~ **Decided 2026-08-31** (§4e):
   three confirmatory passes, **288 blocks per frame**, 3× confirmatory
   generation, no threshold moved. What forced it was a measurement
   (`tools/v8_local_precision.py`, `reports/dci1v8dev/local_precision.md`):
   at one pass the projected **simultaneous** half-width of Δ_R(f) — §16.1's
   registered variance form at §16.2's own planning constants, at F1's Šidák
   value — is **0.078** against Δ_R's registered precondition of **0.05**,
   with an ~80 %-power MDE of **0.103** against a SESOI of 0.10. At three
   passes it is **0.0450** with an MDE of **0.059**, and every scenario that
   is an estimate rather than a bound clears the precondition. Three is the
   smallest allocation that does: two passes give 0.0551. The two rows that
   still miss are the two explicit bounds, and neither is reachable at any
   feasible allocation (522 and 585 blocks per frame against a 384 ceiling).
5. ~~**Whether `qwen3-4b-instruct-2507` runs at the ceiling allocation.**~~
   **Decided and answered 2026-08-31** (§4b): it ran, and f3 did **not**
   reach §13.15 — 3 LOCAL-valid families and 0 backups, against 4 and 1 at
   two passes. The model keeps one supported frame (f1, improved to 7
   families) and is `LOCAL_INELIGIBLE`. 192 topics per frame is the bank's
   ceiling, so this is final unless a rule changes, and §4d forbids that.
6. **Whether an ineligible model still runs the SPECTRUM arm.** §4d is a
   LOCAL inclusion rule and says nothing about the difficulty-response arm,
   whose support is a separate per-frame verdict. **This is now the larger
   question it was not before**: two of the four models are LOCAL-ineligible,
   and both have strong spectrum arms — `gemma-3n-e4b-it` identifies coverage
   on **4 of 4** frames and `qwen3-4b-instruct-2507` on its supported frames.
   Discarding them because their LOCAL arm is thin would throw away the
   difficulty-response evidence they do carry. Not decided here.
7. **Whether `gemma-3n-e4b-it` runs at the ceiling allocation.** It has one
   LOCAL-supported frame (f3, 6 families, 2 backups) and its f1 holds the
   4-and-1 margin at the default two passes (§4f). The evidence on what four
   passes does to that margin is now **two-sided**: it closed it for
   `qwen3-4b` (4-and-1 → 5-and-2 and 7-and-2) and widened it for
   `qwen3-4b-instruct-2507` (4-and-1 → 3-and-0), because more topics per
   split resolve §13.7 per-split admissibility in whichever direction the
   truth lies. So this is a real coin-toss on ~13 h of generation, not a
   near-certain gain, and it is the researcher's call. Declining it leaves
   the LOCAL arm at two models.
3. ~~**A frame-aware screen.**~~ **Redesigned 2026-09-03**
   (`V8_FRAME_AWARE_PRESCREEN.md`): the replay on the stored roots
   (`reports/dci1v8dev/frame_aware_prescreen/prescreen_feasibility.md`)
   measured that at six topics per frame a frame-aware screen is no better
   than the pooled one because the sample size, not the frame, sets the
   noise; the successor gives every frame the pooled screen's budget (one
   pass per frame offset over the same topics) and forwards per frame
   against ι_A(f). Whether that buys anything at equal budget is what the
   successor pilots measure, with the pooled rule as a comparator arm.
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
`cross_frame`, `estimands`, and — since 2026-08-31 (§4d) —
`local_eligibility` (`by_frame[f]` with `local_supported`,
`local_support_state`, `local_unsupported_reason`,
`local_unsupported_reasons`; `local_supported_frames`,
`local_unsupported_frames`, `n_local_supported_frames`,
`local_eligibility_min_frames`, `local_eligible`,
`frames_entering_local_confirmatory`). The same four per-frame fields are on
`by_frame[f].survival` and on `frame_states[f]`, and
`by_frame[f].survival.projected_delta_r_precision` states the LOCAL arm's own
precision projection at the frame's blocks beside the spectrum arm's
`projected_se_beta`. `PILOT_REPORT`: `criteria[name].by_frame`,
`frames_passing`, `frames_meeting_all_decided_criteria`,
`local_eligibility`.

The signed manifest carries the allocations, both of them, before any stage
runs: `design.calibration_allocation` (the default, the per-model overrides
and the ceiling) and — since 2026-08-31 (§4e) —
`design.confirmatory_allocation` (`frame_offsets`, `passes`,
`blocks_per_frame`, `blocks_total`, `single_pass_blocks_per_frame`,
`at_block_ceiling`, `max_passes`, `draws`, the rule and the amendment). The
confirmatory allocation has no per-model override: it is a property of the
design, and `rule_table()` binds every one of its constants.
