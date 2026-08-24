# FIGURE_PLAN

Planned, not rendered. Step 4 of the process builds these; this file fixes the
takeaway, the form and the data path first, per
`guidelines-bullet-point-outline.md` ("plan, then defer rendering").

Forms are the three named in `guidelines-headline-figure.md`: **method or
system diagram**, **headline result plot**, **composite figure**.

---

## Production constraints — apply to every figure

- **Type 1 fonts, mandatory.** matplotlib's default PDF backend emits Type 3,
  which the submission does not accept. Set
  `rcParams["pdf.fonttype"] = 42` and `rcParams["ps.fonttype"] = 42`
  (TrueType, embedded — accepted alongside Type 1), or render through PGF with a
  LaTeX backend for true Type 1. **Validate the packaged PDF, not the figure
  file**, and validate it with the appendix included: `pdffonts paper.pdf` must
  show no `Type 3` row.
- **Colorblind-safe palette, and meaning on a second channel.** No information
  may depend on a red–green distinction. Every series is distinguished by
  **marker shape or line style as well as hue**; every heatmap is distinguished
  by **value labels as well as fill**. Diverging quantities (a signed loss) use
  red–white–blue; sequential quantities use white-to-blue.
- **Grayscale test.** Each figure must be readable when desaturated. Run it
  before the caption is written.
- **Legibility at deployment size.** Render at the single-column or full-width
  measure the figure will occupy and confirm tick labels are readable there,
  per the guideline's step 7.
- **No new computation.** Every figure reads a bundled artifact or the derived
  CSV. No figure script computes an estimand, a contrast or an interval; the
  intervals are read from the signed records.
- **Caption standard** (`guidelines-captions.md`): lead with the takeaway,
  then setup, then reading guide, then evidence markers. One to three sentences.

---

## Figure 1 — **candidate, deferred** · composite (method-then-result) · serves C2

> **Do not build this yet.** Figure 1 would carry C2, and what kind of
> contribution C2 is — or whether it is one a venue would take — is unresolved
> pending CITE-02 and CITE-03 (`GAPS.md`). Build it after §3 exists, so the
> figure is designed around a positioning that has been checked rather than
> assumed.

**Takeaway sentence, written out and kept visible through design:**

> Of four preregistered checkpoint runs, reference admission and composed-headroom
> validation left two — both on the reduced design — which licenses twenty
> interval-bearing estimates and none of the six companion-specific estimands
> the study was built to measure.

**Why composite.** What the figure has to carry is a method-and-negative result,
so neither form alone does it: a diagram alone would show attrition without
showing what survived, and a result plot alone would show the twenty
interval-bearing estimates without showing why the six companion-specific
estimands have none. `guidelines-headline-figure.md` names *method-then-result*
as the pattern for exactly this. **This is a statement about what the evidence
is, not a claim that it is novel.**

**Left panel — the attrition path.** Four lanes, one per checkpoint, running
left to right through Gate 1 → Gate 2 → Gate 3 → Gate 4 → Gate 5 → analysis.
Each lane is annotated at Gate 3 with the design it obtained (47-cell or 8-cell)
and terminates where it terminated. `gemma-3n-e2b-it`'s lane is the visually
dominant one — it is the only full design and it is the one Gate 4 ended — and
carries a short callout naming `COMPOSED_HEADROOM_FAILURE`. A vertical band at
Gate 3 lists the estimands each design can form, so the reader sees the estimand
set shrink as the lanes narrow.

- Data: `G3:<model>` → `design_variant`, `cells_per_block`; `TERM:<model>` →
  `status`, `gate`; `G5:<model>` → `producing_commit`.
- Emphasis channel besides colour: lane weight and terminal marker (× for
  terminal, ● for analysed).

**Right panel — what survived, and what did not.** A forest plot of the twenty
estimates: y-axis grouped by checkpoint run then configuration, x-axis the estimate
with its simultaneous 95% interval, a marker distinguishing emitted-L1 members
from withheld ones. **Below the twenty, six named rows with no interval drawn**,
labelled `Delta_R`, `Delta_j`, `Xi`, `delta_difficulty`, `D(B←R_j)`,
`D(R_j←B)`, each annotated `NOT IDENTIFIED`. Those six empty rows are the
figure's focal point; they are what the paper is about.

- Data: `UA:<model>` → `payload.result.<cfg>.families.<F>.members.<member>`
  (`estimate`, `simultaneous`); the six names from `FR` →
  `study_level_not_identified`.
- Emphasis: the six empty rows sit in a lightly shaded band with a single
  annotation. Zero line drawn.
- **Risk to check at render time:** the empty rows must not read as "estimated
  at zero". Draw no marker at all, and set the annotation inside the row.

**Caption draft.** "Four preregistered checkpoint runs entered and two produced
confirmatory data, both on the reduced design (left); the surviving design
licenses twenty interval-bearing estimates and none of the six companion-specific
estimands (right, shaded). Left: each lane is one model checkpoint through the
gate sequence, annotated with the design admitted at Gate 3 and the status at
termination; × marks a terminal checkpoint run. Right: point estimates with 95%
simultaneous intervals (studentised maximum-modulus, 10,000 block-bootstrap
resamples over T = 384 blocks, M = 8); filled markers are members whose L1
statement was emitted. The six shaded rows are drawn without markers because no
estimate of them exists."

---

## Figure 2 — headline result plot · serves C2, §4.4

**Takeaway.** The candidate ladder is skewed harder than the target constraint
on every checkpoint run: of the 84 shortlisted rungs Gate 2 calibrated, 65 lie
below ι_A, and at most two eligible rungs sit above it on any one run.

**Framing constraints — three, and all three bind.**

1. **The 84 are the shortlist, not the library.** Each panel plots the rungs of
   the six budget-class families §12.3 shortlisted on that checkpoint run — 21,
   20, 23 and 20 — and the pooled 84 is their sum. The pre-screen measured 254
   eligible rungs per run. The axis label, the panel subtitle and the caption all
   say *shortlisted rungs calibrated at Gate 2*; **the words "measured rungs"
   must not appear unqualified**, and no panel total may be presented as a
   library total. `EVIDENCE_MAP.md` Table 3 rows 2d–2e carry the funnel.
2. **Plot the unconditional distribution.** The 58-of-66 split is conditional on
   a rung having already been refused for a caliper miss, so it must not be shown
   as the share of the library that is harder; if it appears it appears as an
   annotation, labelled conditional.
3. **The ι plotted is the Gate-2 calibration value, and the shortlist was chosen
   on pre-screen ι.** The same 84 rungs split **54 below / 30 above** ι_A at
   pre-screen and **65 / 19** at calibration. The movement behind that is **14
   above→below and 3 below→above — 17 rungs changing side**, netting 11; 51
   stayed below and 16 stayed above. *Never write "14 crossed"* — 14 is the
   one-way count. **Recommended rendering (`ITERATION.md` Q11): show the shift in
   the figure, not only in the caption.** Plot pre-screen ι as a faint second
   marker per rung with ι_A drawn at both its pre-screen and calibration
   positions, and annotate each panel with its own transition (e2b 4/2, e4b 3/1,
   qwen3-4b 2/0, qwen-instruct 5/0, as above→below / below→above). A reader who
   sees only 65/19 will take the skew for a fixed library property; the shift is
   part of what the panel is reporting. Do not let the figure imply the shortlist
   was drawn from below *A* — §12.3 reserves a slot above *A* per family wherever
   the pre-screen has one.

**Form.** Four small multiples, one per checkpoint run. Horizontal axis is ι.
Each shortlisted rung is a point; ι_A is a vertical line; the ±0.10 caliper is a
shaded band. Points are shaped by verdict — admitted, refused-on-caliper,
refused-on-Newcombe, refused-other — so the verdict reads without colour.

- Data: `ADM` → `models.<model>.families.<F>.rungs[*].iota`,
  `.distance_from_iota_A`, `.admissible_13_4`, `.rejection_reasons`;
  `models.<model>.iota_a`; `thresholds.REFERENCE_CALIPER`.
- Emphasis: the region above ι_A, which holds 2, 1, 1 and 0 eligible rungs
  across the four panels. Annotate the count on each panel. The annotation is
  **descriptive** — the figure shows how few sat above the target, and no
  counterfactual in this study shows that scarcity is what bound the design. On
  `qwen3-4b-instruct-2507` it is empty; on `gemma-3n-e4b-it` the single eligible
  rung above ι_A is `RF9:13` at 0.7043, and the panel must show it rather than
  suggest emptiness.
- Constraint note: `ADM` is a **post-hoc diagnostic** whose verdicts were
  computed by the registered selection functions on the signed Gate-2 table
  (`ADM` → `_provenance`), and it holds only the shortlisted rungs. The caption
  says both.

---

## Figure 3 — headline result plot · serves C2, §4.7

**Takeaway.** The admitted reference `RF11:26` measured 0.6875 solo and 0.9688
composed with the outcome constraint *B*, exceeding the registered [0.05, 0.95]
headroom ceiling.

**Form.** A slope plot: solo rate on the left, composed rate on the right, one
line per (cell, slot) that Gate 4 evaluated on `gemma-3n-e2b-it`, with the
[0.05, 0.95] band shaded and the five failing slots emphasised. A small second
panel carries `qwen3-4b-instruct-2507`'s single failure, which is a *solo*
ceiling on the class companion and therefore a different failure — the panel
exists to prevent the reader from merging the two.

- Data: `G2:gemma-3n-e2b-it` → `calibration_table` (solo side);
  `TERM:gemma-3n-e2b-it` → `table`, `failures`, `band` (composed side);
  `TERM:qwen3-4b-instruct-2507` → `failures`. Slot identities from
  `G3:gemma-3n-e2b-it` → `slot_map`.
- Emphasis: the five failing lines are heavier and labelled; the rest recede.
- Second channel: failing lines carry an end marker as well as weight.

---

## Table 1 — §5.3 · serves C1

**Takeaway.** In the two position-matched cells a composed constraint loses
delivery relative to itself alone; the two position-shifted cells confound
composition with position, and the table marks which is which.

Rows: checkpoint run × configuration × member; a column marks position-matched
versus position-shifted. Columns: estimate, simultaneous
95%, marginal 95%, bootstrap SE, half-width, precision precondition, whether L1
was emitted. Source: `EVIDENCE_MAP.md` Table 1, which is generated from the
signed records rather than transcribed. Tabular numerals; consistent 4-decimal
precision; no colour.

## Table 2 — §5.5 · serves C1, C2

**Takeaway.** L2 and L3 are withheld in every cell and L4 is withheld on
`gemma-3n-e4b-it` but licensed on `qwen3-4b`; the record names the rule in each
case.

**Structure — two bands, because the levels have two different grains.** L1, L2
and L3 are **configuration-level**: they are emitted per member inside each
configuration's `statements` list [`UA:<model>` →
`payload.claims.<configuration>.statements[*]`]. L4 is **checkpoint-run-level**:
one record per run, spanning both configurations, carrying
`configuration: "outcome_first|outcome_second"` and a `levels_by_configuration`
map [`UA:<model>` → `payload.claims.L4`]. It sits as a sibling of the two
configuration blocks, not inside them.

- **Band 1 — L1, L2, L3 × checkpoint run × configuration** (12 rows).
- **Band 2 — L4 × checkpoint run** (2 rows), spanning the configuration column
  or with it struck through. **Do not repeat L4 per configuration** — that would
  present one classification as two results and is the same set-versus-member
  confusion the emitter defect turned on.

Columns: emitted, the registered reason quoted, the identification statuses
attached. Source: `UA:<model>` → `payload.claims`.

## Table 3 — §4.6 · serves C2

**Takeaway.** Two routes to the reduced design: one admitted family that cannot
straddle, or two that can and a registered requirement of three. Rows: the four
checkpoints. Columns: ι_A, admitted budget families, straddling, core
references, spectrum triples, design, the one-line reason. Source:
`EVIDENCE_MAP.md` Table 3 row 5 and `ADM`.

## Table 4 — Appendix B · no claim; supports §6.1

**Takeaway.** Gate 1's ten conditions were met at agreement 1.0 across 524
instruments, 36,164 responses and 650,952 statistic comparisons. Rows: the ten
conditions. Columns: what it checks, the realised figure, the field it came
from. Source: `EVIDENCE_MAP.md` Table 4.

---

## Not planned, and why

- **No per-block scatter of the derived cell means.** `per_block_cell_means.csv`
  is bundled for verification, not for display; a figure over 11,520 rows would
  invite reading an estimand off it.
- **No cross-model comparison plot.** No cross-model estimand is registered;
  a plot placing the two survivors on one axis would imply a contrast the study
  does not test.
- **No figure for the exploratory arm.** Different constraint vocabulary,
  outside this paper's scope.
