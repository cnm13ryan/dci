# The Gate-2 calibration screen: §12.3, §12.4 and §13.2 on the registered calibration set

**Classification: NON-CONFIRMATORY DESIGN SCREEN.** Not a registered v4 stage.
Gate 1 is not approved and the canonical verifier hash is not frozen, so nothing
here is a §12.3 record and nothing here is adopted. Evidence under
`dci1/evidence/cal-screen-v4/`, outside the v4 namespace, where the
positive-admission guard refuses it. Protocol frozen before the first
generation at `reports/cal_screen_v4/screen_protocol.json`,
hash `fd49e5d4…`; the two extra arms carry their own per-model hashes.

---

## 1. Why this screen exists

Three artifacts in this repository make the same measurement a precondition of
their own conclusions, and none of them had run it:

| artifact | what it says it needs |
|---|---|
| `user-notes/DCI1_v4_amendment_B_reference_pool.md` §9 | "The candidate families must clear the conjunction on the calibration set before they are adopted into the registered pool." |
| `dci1/reports/fs_screen_v4/REPORT.md` §6 | "§12.3 re-measures on the disjoint 96 solo-calibration topics at M = 4, and §13.2 admits against *that*. This screen has never been shown to predict it." |
| `dci1/reports/bgrid_screen_v4/REPORT.md` §1.4 | verdict **MARGINAL**; "a fresh-topic confirmation is required before any grid amendment." |

Every earlier screen measured on the 24 pre-screen topics at one draw. This one
measures on the **96 registered solo-calibration topics at the registered
M_cal = 4**, which is the sample §13.2 admits against, and answers all three
questions from the same generation.

## 2. What decides, and what does not

The registered code does the deciding. `cal_screen_v4/admission.py` carries
§13.2's six conditions and proves it is the registered rule rather than a
lookalike: `assert_equivalent_to_registered` runs it and
`dci1v4.stages.gates.admit_family` over the same constructed input on RF1, at
every rung of the registered ladder, and refuses to differ — including every
reason string. §12.3's selection is `dci1v4.stages.gates.select_severity`
itself. Every threshold, caliper, band and aim is imported from
`dci1v4.protocol.constants`; a test asserts none of them moved.

The two rungs outside the registered focal grid, m = 11 and m = 12, go through
`bgrid_screen_v4.focal`, whose renderer and scorer are proved byte- and
verdict-identical to the registered ones on all four registered rungs. The
candidate families go through `fs_screen_v4.constraints`, unchanged from the
screen that proposed them.

## 3. The design, frozen before generation

| arm | stem | cells | why |
|---|---|---|---|
| A solo | floored | n ∈ 1…8 | n\* and §13.2's condition-1 anchor, under the stem being evaluated |
| B solo | floored | m ∈ 7…12 | m\*, the §12.4 clauses, and the B-grid screen's fresh-topic confirmation |
| B solo | current | m ∈ 7…12 | the comparator that prices the stem on the registered basis |
| candidates | floored | CR7, CR4, CR6 full ladders | Amendment B's precondition |
| registered control | floored | 4 rungs | so the candidate result is a comparison, not an assertion |
| **registered pool** (second arm) | floored | the §12.2 shortlist of all eight families, 24 rungs | whether Amendment B is *necessary* |
| **pre-screen at M_cal** (third arm) | floored | A grid + candidates + shortlist on the 24 pre-screen topics | whether §13.2 condition 2 decides on signal or on noise |

96 topics × 4 draws throughout. Wording allocation is the registered §8.4 solo
rule. Seeds are a fresh root (202608220, domain `calscreen:gen:v1`) with a
distinct stage label per arm, so no row can collide with a registered
generation or with another arm at an identical prompt.

The `current`-stem arm renders through the **registered** §8.5 template. It is
not a lookalike: `test_current_stem_render_is_the_registered_renderer` asserts
byte identity with `dci1v4.design.prompts.render` at zero, one and two
constraints, which is what makes §4 a statement about the registered design
rather than about this screen.

---

## 4. Q3 first, because it decides whether anything else matters

### The registered design cannot start on any model

§12.4 requires the realised solo vacuity rate of B — the share of **all**
responses in the cell that are vacuous passes — to be at most **0.10**.

**Current stem, B solo vacuity rate, 96 topics at M_cal = 4:**

| model | m=7 | m=8 | m=9 | m=10 | m=11 | m=12 | **min** |
|---|---:|---:|---:|---:|---:|---:|---:|
| E2B | 0.352 | 0.359 | 0.372 | 0.422 | 0.339 | 0.380 | **0.339** |
| E4B | 0.221 | 0.208 | 0.258 | 0.286 | 0.312 | 0.310 | **0.208** |
| Qwen3-4B | 0.312 | 0.378 | 0.461 | 0.534 | 0.633 | 0.633 | **0.312** |
| Qwen3-4B-Inst | 0.659 | 0.766 | 0.815 | 0.854 | 0.870 | 0.852 | **0.659** |

**Not one rung of the registered grid — nor of the extended grid — meets §12.4
on any model.** It is not that m\* happens to fail; there is no m that could
pass. The registered replication returns `REGIME_NOT_FOUND` on all four models
before any reference question is reached.

**Floored stem, same cells:** 0.000 at every rung on both Gemmas, 0.000–0.010 on
qwen3-4b, 0.031–0.060 on qwen3-4b-instruct-2507. Every rung passes.

The B-grid screen reported the same thing on 24 pre-screen topics at one draw.
This is the registered basis: the sample §12.4 is evaluated on, at the
registered draw count.

### What the vacuity costs the estimand, on the registered bound

§17.4 registers the partial-identification recomputation — every vacuous pass
forced to a failure, no row dropped, nothing conditioned on. B's solo compliance
under it:

| model | stem | m=7 | m=10 | m=12 |
|---|---|---|---|---|
| E2B | current | 0.802 → **0.451** | 0.927 → **0.505** | 0.979 → **0.599** |
| E2B | **floored** | 0.404 → 0.404 | 0.807 → 0.807 | 0.914 → 0.914 |
| E4B | current | 0.807 → **0.586** | 0.927 → **0.641** | 0.982 → **0.672** |
| E4B | **floored** | 0.521 → 0.521 | 0.865 → 0.865 | 0.938 → 0.938 |
| Qwen3-4B | current | 0.331 → **0.018** | 0.711 → **0.177** | 0.922 → **0.289** |
| Qwen3-4B | **floored** | 0.023 → 0.021 | 0.453 → 0.451 | 0.753 → 0.753 |
| Qwen3-4B-Inst | current | 0.716 → **0.057** | 0.956 → **0.102** | 0.982 → **0.130** |
| Qwen3-4B-Inst | **floored** | 0.130 → 0.096 | 0.661 → 0.602 | 0.924 → 0.885 |

**Under the registered prompt, up to 85 points of qwen3-4b-instruct-2507's B
compliance is the model declining to answer.** Under the floored stem the point
estimate and the bound coincide to within 0.06 everywhere and are identical on
both Gemmas.

That is what §12.4's vacuity ceiling is for, and it is why the ceiling being
exceeded at every rung is not a technicality: it means the primary outcome does
not measure what it is named after.

**And §17.4 turns that into a decision rule.** Its last sentence: "a claim is
licensed only when the primary and the vacuity-forced recomputation license the
same claim; otherwise **the axis is reported unresolved** with both bounds."
Applied to `D(B←A)` on the FORM × STEM screen's own rows — measured
independently by the sibling session and recorded in `CHANGES_SCIENTIFIC.md`
under *"the screens now report the registered §17.4 vacuity bound"* — the bound
takes E2B's current-stem estimate from **+0.375 to +0.000** and reverses the
sign on both Qwens, while under the floored stem raw and forced are **identical
on three of four models**.

So under the registered prompt the primary axis of this study is unresolved *by
rule*, and under the floored stem it is not. That is a third argument for
Amendment A, independent of the reference pool and of the focal grid.

### And §12.4's graded clause has two readings that decide it differently

§12.4 also requires that "the graded distribution of each outcome constraint is
non-degenerate, meaning it is not concentrated above 0.99 or below 0.01".
`gates.gate2_payload` compares **one float per constraint** against
`GRADED_DEGENERACY_HIGH = 0.99` and does not say which float. Two readings are
available:

- **mean graded** — the cell's mean graded score;
- **share above 0.99** — the share of draws scoring above 0.99, which is the
  more natural reading of "concentrated".

They are not equivalent, and for B they are **maximally opposed**:

| reading | behaviour on B | consequence |
|---|---|---|
| mean graded | fires on **every** in-band rung, because mean graded rises with compliance and crosses 0.99 inside the band | §12.3 declares a rung eligible and §12.4 declares the same rung degenerate — **the two registered criteria contradict each other**, and no rung is feasible on any model under any stem |
| share above 0.99 | fires on **no** in-band rung, because it would need compliance above 0.99 and the band caps it at 0.95 | **inert** for B |

The cause is B's graded definition. `1 − (words over m)/(total words)` cannot
fall far from 1 for any plausible response: a failing sixty-word answer with
three over-length words scores 0.95, and a failing hundred-word answer with one
scores 0.99. A's graded score, `1 − |s₀ − n|/n`, varies over its whole range. One
threshold was written for two forms.

Measured on all 18,432 B rows of this screen, across four models and both stems:
**65 failures (0.35%) score above 0.99, and no pass ever scores at or below
0.99.** So under the share reading the clause is arithmetically almost the
compliance band restated.

**This is a preregistration defect, not a screen result, and the choice between
the readings is the researcher's.** It is recorded here because it decides
whether Gate 2 can start at all, and because no registered caller of
`gate2_payload` has ever fixed the reading — the only callers are a stage-machine
test passing arbitrary probes and this screen, which calls it twice and reports
both.

---

## 5. Q2 — the focal severity, per model

**B solo compliance under the floored stem, band [0.60, 0.95], aim 0.80:**

| model | m=7 | m=8 | m=9 | m=10 | m=11 | m=12 | m\* registered grid | m\* extended |
|---|---:|---:|---:|---:|---:|---:|---|---|
| E2B | 0.404 | 0.560 | 0.628 | 0.807 | 0.846 | 0.914 | **10** | 10 |
| E4B | 0.521 | 0.659 | 0.737 | 0.865 | 0.898 | 0.938 | **9** | 9 |
| Qwen3-4B | 0.023 | 0.125 | 0.247 | 0.453 | 0.654 | 0.753 | `FOCAL_RANGE_EXHAUSTED` | **12** |
| Qwen3-4B-Inst | 0.130 | 0.302 | 0.469 | 0.661 | 0.760 | 0.924 | **10** | 11 |

**Three of four models need no grid extension at all under the floored stem.**
The FORM × STEM screen read the floored stem as exhausting the focal range on
both Qwens at 24 topics and one draw; the B-grid screen corrected that for
qwen3-4b-instruct-2507 on an independently seeded redraw; this confirms the
correction on 96 fresh topics at M_cal = 4 and adds that E2B and E4B never
needed the extension either.

**Only qwen3-4b returns `FOCAL_RANGE_EXHAUSTED` on the registered grid**, with
m = 10 at 0.453 against a 0.60 floor. Its extended-grid m\* = 12 sits 4.26
clustered standard errors inside the band, which is the fresh-topic confirmation
the B-grid screen's MARGINAL verdict asked for.

**And on qwen3-4b-instruct-2507 the extension is actively harmful.** §12.3
selects the rung nearest 0.80, so extending the grid moves m\* from 10 to 11 —
and m = 10 is the only rung on any model feasible under **both** readings of the
graded clause, while m = 11 is not. A global extension of `FOCAL_GRID` would
therefore cost one model its only doubly-feasible operating point in order to
rescue another. **Amendment C should be per-model: the extended grid invoked
only for a replication whose registered grid is exhausted.**

**A solo compliance under the floored stem, band [0.50, 0.85], aim 0.70:**

| model | n=1 | n=2 | n=3 | n=4 | n=5 | n=6 | n=7 | n=8 | n\* | A at n\* |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| E2B | 0.589 | 0.492 | 0.479 | 0.391 | 0.531 | 0.544 | 0.612 | 0.565 | **7** | 0.612 |
| E4B | 0.854 | 0.773 | 0.784 | 0.727 | 0.766 | 0.714 | 0.617 | 0.552 | **6** | 0.714 |
| Qwen3-4B | 0.859 | 0.708 | 0.536 | 0.625 | 0.510 | 0.495 | 0.432 | 0.370 | **2** | 0.708 |
| Qwen3-4B-Inst | 0.984 | 0.997 | 0.977 | 0.909 | 0.602 | 0.534 | 0.404 | 0.484 | **5** | 0.602 |

The anchor moves on every model relative to the current stem, which is why the
§13.2 caliper below is computed against A at the calibration-set n\* under the
stem being evaluated and never against the pre-screen anchor.

---

## 6. Q1 — the reference pool

### What the pre-screen had established, and what it could not

The FORM × STEM screen measured the registered pool under both stems on 24
pre-screen topics at one draw and found the `count × current` cell returning
**0 of 4** models with three families reaching the condition-1 ∧ condition-6
conjunction, against 0.41–0.88 bootstrap probability for the candidates. Its own
report says what it could not do: "§12.3 re-measures on the disjoint 96
solo-calibration topics at M = 4, and §13.2 admits against *that*. This screen
has never been shown to predict it."

Two arms answer that here. The **registered-pool arm** carries the §12.2
shortlist of all eight registered families — three rungs per family, bracketing
A's anchor on the floored pre-screen curve — on the 96 calibration topics at
M_cal = 4. The **main arm** carries the three candidate rate families over their
full ladders on the same topics. Both are scored by the registered verifier and
admitted by the registered §13.2 code.

### Three dispositions of condition 2, and why

§13.2 condition 2 requires the reference-minus-A distance to be at most 0.15 on
the **disjoint 24 pre-screen topics**. Its input is a §12.2 measurement: 24
topics at **one draw**. Computed from the FORM × STEM screen's own floored rows,
the median paired standard error of that difference is **0.10–0.12** — of the
same order as the caliper it is checked against — so a reference whose true
pre-screen distance is zero is rejected about a fifth of the time. The anchor
moves with it: qwen3-4b's A at n\* = 2 reads 0.542 on the one-draw pre-screen
and 0.708 on the calibration set, a 0.167 shift applied to every reference at
once.

There is also a data-availability problem specific to this screen. §12.2
measures **all 94 rungs** on the pre-screen topics, so in the real study every
rung has a value; the floored-stem pre-screen available here was produced by the
FORM × STEM screen, which measured only the **current-stem caliper rungs** under
the floored stem. Rejecting a rung because that particular screen never measured
it is an artifact, not a criterion.

So three dispositions are computed and all three are reported:

| disposition | condition 2 | what it is for |
|---|---|---|
| **strict** | as registered; a rung with no floored pre-screen value is rejected | reproduces the registered code exactly, and is contaminated by the artifact above |
| **where measured** | applied to rungs that have a one-draw value; not evaluated for the rest | removes the artifact and nothing else |
| **at M_cal** | the registered criterion and threshold, its input measured at M_cal = 4 on the same 24 topics | removes the precision problem; differs from §12.2 only in draw count |

A fourth, **condition 2 off entirely**, is reported as a §23-style sensitivity.
It admits nothing and no reference decision rests on it.

Measuring the same quantity more precisely against the same threshold is not
weakening a criterion (§31): it rejects rungs the noisier estimate would have
admitted as well as the reverse, and on these models it does both.

**Which disposition the matrix screen uses, and why it is not the best
measurement.** It uses the second — conditions 1 and 3–6 exactly as registered
on the calibration set, condition 2 with its registered §12.2 one-draw input,
applied where that input exists. **Not** the M_cal variant, even though the
M_cal variant measures condition 2's quantity better. §12.2 registers one draw,
and letting a screen-invented precision upgrade choose the design would be the
screen deciding a protocol question that belongs to the researcher.

The M_cal variant is reported as a sensitivity, and it is a large one **that
moves in opposite directions on different models** — the four-model table
appears with the Q1 results below. The pattern: the one-draw pre-screen anchor
misses the 96-topic calibration value by −0.03, −0.13, −0.17 and +0.02; the
M_cal anchor misses it by −0.14, +0.01, −0.01 and −0.05; and the admitted-family
count swings **7 → 3, 5 → 6, 3 → 5, 7 → 4**.

On qwen3-4b the M_cal count equals the condition-2-off count exactly, which says
the one-draw anchor was the whole of what condition 2 was doing on that model.
On E2B the better-measured anchor happens to land further from the calibration
value and condition 2 then rejects nearly everything.

That is not a disagreement about the references. **It is the criterion moving
because its reference point moved**, in both directions, on a quantity whose
24-topic single-draw standard error is about 0.10 against a caliper of 0.15.

**Condition 2 is therefore the least stable of the six conditions**, and it is
the only one whose input the registered protocol measures at one draw. Whether
§12.2's draw count should rise, or condition 2's caliper should be stated
relative to its own standard error, or condition 2 should be dropped in favour
of the §13.2 realised-gap qualifier the confirmatory design already carries, is a
§31 decision and this screen does not take it.

### The result

**The registered reference pool was length-falsified, not falsified.**

Counting families with a rung clearing §13.2 **condition 1 and condition 6 at
the same severity** — the exact conjunction the FORM × STEM screen measured as
**0 of 64** under the current stem — the registered pool alone now delivers, on
the 96 calibration topics at M_cal = 4 under the floored stem:

| model | registered families clearing conditions 1 ∧ 6 | which |
|---|---:|---|
| E2B | **3** | RF2, RF3, RF8 |
| E4B | **4** | RF2, RF3, RF6, RF8 |
| Qwen3-4B | **1** | RF7 |
| Qwen3-4B-Inst | **4** | RF1, RF2, RF3, RF7 |

with solo vacuity of **0.000** at almost every one of them. The pool's
condition-6 failure was a property of the responses the current prompt elicits,
not of the pool.

> **CORRECTED 2026-08-20, after this report was written.** The paragraphs that
> follow call the disposition of an unmeasurable condition 2 a preregistration
> gap and a researcher decision. **It is neither, and that reading is
> withdrawn.** §13.2's feasible set is a subset of §12.2's shortlist, §12.2
> measures all 94 rungs on the pre-screen topics, so in the registered pipeline
> condition 2 always has its input — verified on all four registered
> `REGIME_SCREEN` records, 94 of 94 rungs measured and 0 shortlisted rungs
> without a value. Where the case is constructed anyway the registered
> `gates.admit_family` rejects. This screen met the case because it ran §13.2
> over rungs outside the §12.2 shortlist and because its floored-stem
> pre-screen was partial — both properties of the screen. **The tables below
> remain valid as what they are** (§13.2 run over a rung set the registered
> pipeline would not present to it) **and are not two readings of the
> registered rule.** See `dci1/reports/section_13_2_v4/REPORT.md`.

**Whether that becomes "three admitted references" depends on a reading §13.2
does not fix.** Conditions 1 and 6 are two of six. Most of the rungs above have
**no §12.2 pre-screen measurement at all**, so condition 2 — the disjoint
24-topic confirmation — cannot be evaluated on them, and the protocol does not
say whether an unmeasurable condition abstains or fails. Both dispositions are
computed and both are on the artifact:

| disposition | E2B | E4B | Qwen3-4B | Qwen3-4B-Inst | three from the registered pool? |
|---|---:|---:|---:|---:|---|
| condition 2 applied where its one-draw input exists (**abstain**) | 3 | 4 | 1 | 4 | on three of four models |
| condition 2 counted as failed when unmeasurable (**reject**) | 1 | 2 | 1 | 2 | **on no model** |

Under abstain, three of four models reach the §13.2 requirement of three from
the registered pool alone. Under reject, none does and Amendment B is necessary
everywhere. The matrix screen declares abstain in its frozen protocol and
reports reject beside it as `strict_registered_precision`; neither is a claim,
and **choosing between them is a researcher decision of the same kind as
§12.4's graded clause** — a preregistration gap, not a measurement.

**The consequence for Amendment B is direct, and conditional on that reading.**
Its §1 argues from prefix closure that the pool "crosses A's compliance level
*only* through the vacuity channel". Under the floored stem that is no longer
true: the crossings above are at vacuity 0.000, and that part does not depend on
the disposition. Under **abstain** Amendment B is **not necessary on three of
four models**, and adopting it would buy nothing there while costing a canonical
verifier hash change, a Gate 1 instrument re-freeze, a boundary-suite extension,
and the §7.3 witness obligation over the enlarged pool that its own §5a now
sizes at 2,448–5,472 uncertified pairs.

Under **reject** it is necessary on all four, and the cost is incurred anyway.

**And three references do exist on every model, under every disposition** — the
enlarged pool admits 5, 3, 3 and 5. But on **E4B and qwen3-4b the third slot can
only be filled by a lower-bound (production-class) family**, so on those two the
constraint-class confound moves inside the reference set instead of sitting
beside it in a control arm. That is a design consequence worth more than the
count: a Δ_R whose reference mean includes a production companion is not a
budget-only comparison, and on qwen3-4b the matrix screen records exactly that.

Where Amendment B still buys something under either reading is **qwen3-4b**,
whose registered pool supplies one family and which reaches two only with CR7. Whether it reaches three there
turns entirely on §13.2 condition 2, which rejects CR4:13 and CR6:10 at
calibration distances of −0.042 and −0.013.


### Families admitted under §13.2, floored stem, four dispositions of condition 2

| model | anchor A@n\* | strict | where measured | at M_cal | condition 2 off |
|---|---:|---:|---:|---:|---:|
| E2B | 0.612 (n=7) | 5 | 7 | 3 | 7 |
| E4B | 0.714 (n=6) | 3 | 5 | 6 | 8 |
| Qwen3-4B | 0.708 (n=2) | 3 | 3 | 5 | 5 |
| Qwen3-4B-Inst | 0.602 (n=5) | 5 | 7 | 4 | 7 |

### The admitted families themselves

| model | disposition used by the matrix screen | families |
|---|---|---|
| E2B | conditions 1 and 3-6 as registered on the 96 calibration topics; condition 2 with its registered one-draw §12.2 input, applied where that input exists | CR6, RF3, RF2, CL7, CL8, CR4, RF8 (7) |
| E4B | conditions 1 and 3-6 as registered on the 96 calibration topics; condition 2 with its registered one-draw §12.2 input, applied where that input exists | RF8, RF3, CL8, RF2, RF6 (5) |
| Qwen3-4B | conditions 1 and 3-6 as registered on the 96 calibration topics; condition 2 with its registered one-draw §12.2 input, applied where that input exists | CR7, CL8, RF7 (3) |
| Qwen3-4B-Inst | conditions 1 and 3-6 as registered on the 96 calibration topics; condition 2 with its registered one-draw §12.2 input, applied where that input exists | CR7, RF1, RF7, CL8, RF3, CR4, RF2 (7) |

### Registered-family rungs clearing conditions 1 and 6 together

| model | family:severity | solo | distance from A | vacuity | admitted |
|---|---|---:|---:|---:|---|
| E2B | RF2:6 | 0.594 | -0.018 | 0.000 | no pre-screen measurement |
| E2B | RF2:7 | 0.661 | +0.049 | 0.000 | no pre-screen measurement |
| E2B | RF3:4 | 0.604 | -0.008 | 0.000 | **yes** |
| E2B | RF8:6 | 0.659 | +0.047 | 0.000 | no pre-screen measurement |
| E4B | RF2:7 | 0.628 | -0.086 | 0.000 | no pre-screen measurement |
| E4B | RF2:8 | 0.661 | -0.052 | 0.000 | no pre-screen measurement |
| E4B | RF3:4 | 0.742 | +0.029 | 0.000 | **yes** |
| E4B | RF6:2 | 0.622 | -0.091 | 0.000 | **yes** |
| E4B | RF8:7 | 0.633 | -0.081 | 0.000 | no pre-screen measurement |
| E4B | RF8:8 | 0.716 | +0.003 | 0.000 | no pre-screen measurement |
| Qwen3-4B | RF7:24 | 0.651 | -0.057 | 0.005 | **yes** |
| Qwen3-4B-Inst | RF1:4 | 0.555 | -0.047 | 0.005 | pre-screen distance 0.2083 exceeds 0.15 |
| Qwen3-4B-Inst | RF1:5 | 0.617 | +0.016 | 0.003 | no pre-screen measurement |
| Qwen3-4B-Inst | RF2:4 | 0.529 | -0.073 | 0.000 | **yes** |
| Qwen3-4B-Inst | RF3:1 | 0.648 | +0.047 | 0.000 | no pre-screen measurement |
| Qwen3-4B-Inst | RF7:24 | 0.622 | +0.021 | 0.000 | **yes** |

### Candidate rate families

| model | family:severity | solo | distance from A | vacuity | admitted |
|---|---|---:|---:|---:|---|
| E2B | CR4:11 | 0.565 | -0.047 | 0.000 | **yes** |
| E2B | CR6:7 | 0.615 | +0.003 | 0.000 | **yes** |
| E4B | CR7:44 | 0.810 | +0.096 | 0.000 | pre-screen distance 0.1667 exceeds 0.15 |
| E4B | CR4:13 | 0.669 | -0.044 | 0.000 | pre-screen distance 0.2083 exceeds 0.15 |
| E4B | CR6:8 | 0.792 | +0.078 | 0.000 | pre-screen distance 0.3750 exceeds 0.15 |
| Qwen3-4B | CR7:44 | 0.680 | -0.029 | 0.000 | **yes** |
| Qwen3-4B | CR4:13 | 0.667 | -0.042 | 0.000 | pre-screen distance 0.1667 exceeds 0.15 |
| Qwen3-4B | CR6:10 | 0.695 | -0.013 | 0.000 | pre-screen distance 0.2083 exceeds 0.15 |
| Qwen3-4B-Inst | CR7:44 | 0.586 | -0.016 | 0.000 | **yes** |
| Qwen3-4B-Inst | CR4:13 | 0.654 | +0.052 | 0.000 | **yes** |

### Lower-bound (production-class) families

| model | family:severity | solo | distance from A | vacuity | admitted |
|---|---|---:|---:|---:|---|
| E2B | CL7:80 | 0.646 | +0.034 | 0.000 | **yes** |
| E2B | CL8:25 | 0.573 | -0.039 | 0.000 | **yes** |
| E4B | CL8:25 | 0.680 | -0.034 | 0.000 | **yes** |
| Qwen3-4B | CL8:5 | 0.753 | +0.044 | 0.000 | **yes** |
| Qwen3-4B-Inst | CL8:10 | 0.641 | +0.039 | 0.005 | **yes** |

### Condition 2 at registered precision and at M_cal, all four models

| model | A pre-screen at n\*, one draw | at M_cal | A on the 96 calibration topics | families: registered precision → M_cal → condition 2 off |
|---|---:|---:|---:|---|
| E2B | 0.583 | 0.469 | 0.612 | 7 → 3 → 7 |
| E4B | 0.583 | 0.719 | 0.714 | 5 → 6 → 8 |
| Qwen3-4B | 0.542 | 0.698 | 0.708 | 3 → 5 → 5 |
| Qwen3-4B-Inst | 0.625 | 0.552 | 0.602 | 7 → 4 → 7 |

### What the lower-bound arm buys

A **class-matched production companion** is admissible under the full §13.2 rule
on **all four models** — CL7:80 on E2B and CL8 at 25, 5 and 10 on the other
three — at distances from A of +0.034, −0.034, +0.044 and +0.039 and solo
vacuity of 0.000 to 0.005. So Δ_class = D(B←A) − D(B←CL) is estimable, and the
production-versus-budget confound is a testable hypothesis rather than a
standing objection.

Where three budget families are also admitted, the lower-bound family is
reserved for the class arm and Δ_R stays a pure budget contrast. Where they are
not — qwen3-4b has two — §13.2's plain ordering puts the lower-bound family in an
R slot instead, and that reference's own Δ_j **is** the class contrast for that
model, at the cost of a Δ_R that averages over one production and two budget
companions.


---

## 7. What the stem does to the mediator, which is why it is load-bearing

Response length is a registered mediator (§13.3, §22) and the B+R pilot's Δ
turns out to be nearly collinear with it — the pilot's two cells are five-fold
apart in words and overlap on 8–9% of one arm
(`dci1/reports/pilot_reanalysis/`). A companion contrast can only be a
companion contrast if the cells being differenced share a length regime.

Median response words, solo cells on the 96 calibration topics:

| model | stem | A | B | CR7 | CR4 | CR6 | registered pool | A ÷ B |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| E2B | current | — | **24** | — | — | — | — | — |
| E2B | **floored** | 121 | 83 | 92 | 97 | 100 | 86 | **1.46×** |
| E4B | current | — | **30** | — | — | — | — | — |
| E4B | **floored** | 122 | 83 | 90 | 96 | 102 | 87 | **1.47×** |
| Qwen3-4B | current | — | **10** | — | — | — | — | — |
| Qwen3-4B | **floored** | 75 | 53 | 73 | 79 | 75 | 61 | **1.42×** |
| Qwen3-4B-Inst | current | — | **6** | — | — | — | — | — |
| Qwen3-4B-Inst | **floored** | 75 | 52 | 73 | 74 | 78 | 67 | **1.44×** |

(The current-stem arm of this screen carries B only, by design; the dashes are
cells it did not generate, not missing data.)

**Under the floored stem the constraint types sit within a factor of 1.5 of each
other in response length.** That is the regime in which v3's A-side contrast
lives — `AB` 127.9 words against `AR_j` 146.6–184.2, a separation of 1.15–1.44×
— and it is the regime in which Δ^A survives length matching with full common
support. The pilot's B-side contrast at 5.1–5.6× does not.

### The stem is obeyed unevenly, and that is a limitation of it

The stem is an instruction, not a truncation rule, and the model obeys it to
different degrees depending on which constraint it is carrying. Share of
responses landing in the 60–120 word window:

| model | A solo | B solo | references |
|---|---:|---:|---:|
| E2B | 0.497 | 0.988 | 0.992 |
| E4B | 0.459 | 0.968 | 0.994 |
| Qwen3-4B | 0.879 | **0.289** | 0.726 |
| Qwen3-4B-Inst | 0.979 | **0.288** | 0.898 |

The Gemmas overshoot the ceiling under A — 121 and 122 median words against a
120 cap — and both Qwens undershoot the floor under B, at 52–53 words. So the
stem **narrows** the length differential from 5.1–5.6× to about 1.45× and does
not eliminate it. That is worth stating plainly against the FORM × STEM
screen's pooled "71–89% of floored answers land in the band", which averages
over exactly the asymmetry that matters.

Truncation at the §12.1 cap of 512 is **0.0000–0.0035** in every floored cell on
every model, so the cap selection survives the stem and the §12.1 bound is not
approached.

So Amendment A is not only a vacuity fix. **It is what puts the cells whose
difference Δ_R is into the same length regime**, and without it Δ_R is a length
contrast with a companion label on it. A B-solo cell of six to thirty words is
not a measurement of B; it is a measurement of the model declining to answer.

---

## 8. What this screen does not decide

- **Nothing is adopted.** Amendments A, B and C remain drafts. `FOCAL_GRID`,
  `REFERENCE_LADDERS`, `REFERENCE_CALIPER`, `REFERENCE_VACUITY_MAX`,
  `REGIME_VACUITY_MAX`, `TARGET_BAND`, `FOCAL_BAND`, `M_CAL` and every registered
  wording are unchanged, and `tests_v4/test_cal_and_matrix_screen_isolation.py`
  asserts it.
- **§10.2 for any family verifier.** Whatever pool is adopted, Gate 1 needs the
  full §10.2 evidence set for every family verifier Gate 3 could admit —
  determinism over the calibration pool, a frozen boundary suite of at least
  forty authored cases each, an independent reimplementation, an adversarial
  corpus. None of that is here, and this screen does not shorten it. It only
  changes **which** instruments need it.
- **The §12.4 graded reading.** Reported, not chosen.
- **Whether the pre-screen predicts the calibration set in general.** This
  screen shows it does not, on the quantity §13.2 condition 2 reads. It does not
  license a general claim about §12.2.
- **Anything about composed behaviour.** This screen has no composed cells. The
  pairwise-matrix screen has them.
- **Anything confirmatory.** Gate 1 is not approved, no verifier hash is frozen,
  no freeze record exists, and none of these rows may enter a v4 estimator.

---

## 9. What now stands between this study and its decisive test

In order, and none of it is mine to decide.

1. **The §12.4 graded reading.** Under the mean reading no rung of any grid is
   feasible on any model under any stem, and §12.3 and §12.4 contradict each
   other. Under the share reading the clause is inert for B. The registered code
   fixes neither. **Nothing downstream can start until this is chosen.**
2. **The prompt stem.** The registered prompt cannot pass §12.4 on any model.
   Amendment A fixes it, restores common support on the mediator, and is the
   only proposal on the table that does either. Its cost is measured here rather
   than assumed: it moves n\* and m\* on every model, and §5 below prices the
   focal-grid consequence per model.
3. **The focal grid.** Per-model, not global. Only qwen3-4b needs the extension;
   on qwen3-4b-instruct-2507 a global extension moves m\* off the only rung
   feasible under both readings of the graded clause.
4. **The reference pool.** Three of four models reach three admitted families
   from the **registered** pool under the floored stem. Amendment B is
   unnecessary for those three and is the only route to three for qwen3-4b,
   where the binding condition is condition 2 rather than the pool's form.
5. **§13.2 condition 2's precision.** Its input is a §12.2 measurement at one
   draw whose paired standard error, 0.10–0.12, is of the same order as the
   0.15 caliper it feeds. Raising §12.2's draw count is a strengthening, not a
   weakening, and it changes which references are admitted on at least one
   model. Whether to amend §12.2 is a §31 decision.
6. **§10.2 for every admitted family verifier**, then Gate 1, then the freeze.
   Whichever pool is adopted, the §10.2 evidence set is required for every
   family verifier Gate 3 could admit and none of it exists yet.
7. **Explicit researcher approval** of `measurement_basis =
   autorater_calibration_approved`, with `HUMAN_VALIDATION_UNAVAILABLE` as the
   identification status and the §10.5 scope sentence on every claim.

Items 1, 2, 3, 4, 5 and 7 are decisions. This screen is their evidence and none
of them is taken here.
