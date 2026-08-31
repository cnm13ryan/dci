# Publication-ready captions

Numbers quoted in the captions are checked by `dci1/tools/v7_paper_figures_check.py`
against the signed `FINAL_REPORT` records. All figures show the four **canonical**
lanes only — one per model — in both prompt orders, giving eight configurations.

---

## Figure 2

**Across all eight model × prompt-order configurations, A costs B no more than
same-form companions matched to it on stand-alone difficulty do: every
simultaneous interval for $\Delta_R$ stops far short of the $+10$ pp threshold,
and in three of the eight it lies entirely below zero, meaning the matched
references cost B *more* than A does.** Each diamond is
$\Delta_R = \tfrac{1}{3}\sum_j c(B \mid B{+}R_j) - c(B \mid B{+}A)$ in percentage
points of B-compliance, so positive means A is associated with lower
B-compliance than the three references; filled diamonds have B stated first
(prompt B+A), open diamonds B stated second (prompt A+B), and the bar is the
simultaneous 95% block-bootstrap interval over 384 topic blocks for multiplicity
family F1. The hatched aprons and stop bars mark where an arm's own compliance
level put values arithmetically out of reach — for both Qwen configurations with
B first, nothing above $+9.9$ pp was attainable whatever the model did — and all
estimates are development-rehearsal evidence, not confirmatory results.

---

## Figure 3

**A large solo-to-composed change in B-compliance can carry almost no
companion-specific signal, because the matched references produce a change of
the same size or larger: on Gemma 3n E4B with B stated second, composition beside
A costs B $39.2$ pp while composition beside the matched references costs
$46.4$ pp.** For each model and prompt order the circle is the delivery loss for
B beside A and the hexagon the mean of the same loss beside the three matched
references, both on one axis where positive means composition reduced
B-compliance; the grey bar joining them *is* $\Delta_R$, so its length is the
companion-specific component and its direction the sign. The thin interval below
each row is the simultaneous 95% interval for $D(B \leftarrow A)$ — the reference
mean is a derived average and carries no registered interval — open markers have
B stated second, and all estimates are development-rehearsal evidence.

---

## Figure 4

**How much compliance composition costs depends both on which instruction is
measured and on where that instruction stands in the prompt.** Panel A shows,
within each prompt, the delivery loss measured on B beside A (circles) and on A
beside B (squares), with filled markers for the instruction stated first and open
markers for the one stated second, where composition and position change together
and the loss is not position-matched to its solo baseline; the two marks of a row
come from one prompt, not two. Panel B gives the registered order contrast for
each instruction — its loss when stated first minus its loss when stated second,
a difference of two composed cells that is free of that confound — with
simultaneous 95% intervals, dotted rules at the $\pm 10$ pp smallest effect of
interest, and $*$ where realised precision fell below the registered
precondition; all estimates are development-rehearsal evidence.

---

## Table 1

**Matched-reference results for the four models in both prompt orders, in
percentage points of B-compliance over 384 topic blocks.**
$D(B\!\leftarrow\!A)$ is B's solo compliance minus its compliance beside A, and
$\overline{D(B\!\leftarrow\!R)}$ the unweighted mean of the same loss beside the
three matched same-form references, so
$\Delta_R = D(B\!\leftarrow\!A) - \overline{D(B\!\leftarrow\!R)}$ and a positive
value means A is associated with lower B-compliance than its matched references.
Intervals are simultaneous 95% block-bootstrap intervals for multiplicity family
F1; $\overline{D(B\!\leftarrow\!R)}$ is a derived mean and carries no registered
interval; $\dagger$ marks configurations where an arm's compliance level
arithmetically restricts the range $\Delta_R$ can take. Development-rehearsal
evidence, not confirmatory results.

---

## Cross-figure visual grammar (for the Methods or a figure-conventions note)

| Encoding | Meaning | Used in |
|---|---|---|
| Colour | the companion instruction present in the composed cell: blue = A, rust = B, teal = the matched reference pool; neutral ink where the mark is a contrast between two arms | Figures 2–4 |
| Marker shape | what the mark is: ● a loss measured on B, ■ a loss measured on A, ⬢ the mean loss over the three matched references, ◆ a contrast between two composed arms | Figures 2–4 |
| Marker fill | the measured instruction's position: filled = stated first, open = stated second | Figures 2–4 |

Colour is always redundant with shape and fill, so every figure is readable in
grayscale. The palette (`#0173B2`, `#B4590A`, `#029E73`) passes all six checks of
the `dataviz` skill's validator on an all-pairs run against a light surface.
