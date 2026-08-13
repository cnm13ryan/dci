# What Figure 1 has to do

## What should a completely new reader learn?

> **Letting the model think for longer removes its instruction conflict when the
> prompt also asks for one pair of brackets — but not when that same prompt asks
> for one semicolon instead.**

## Why should anyone care?

> **A model can look as though extra thinking has fixed its instruction-following
> problem, when the fix actually depends on an incidental detail of the prompt —
> so one score at one thinking budget can hide the failure entirely.**

---

## The whole experiment, in plain English

Every prompt asks the model to explain something and to satisfy three
instructions at once. Only one word ever changes between the two conditions.

| | |
|---|---|
| **the main instruction** (scored) | *"Write exactly 4 sentences."* |
| **the competing instruction** | *"Make each sentence strictly longer than the preceding sentence."* |
| **the comparison instruction** | *"Begin every sentence with a word whose first letter is S."* |
| **the third instruction — version 1** | *"Use exactly 1 pair of round brackets in the whole answer, and place it wherever you judge best."* |
| **the third instruction — version 2** | *"Use exactly 1 semicolon in the whole answer, and place it wherever you judge best."* |

The measured quantity is a difference between two otherwise identical prompts:

> how often the model fails *"write exactly 4 sentences"* when the competing
> instruction is present, **minus** how often it fails the same instruction when
> the comparison instruction is there instead.

Zero means the competing instruction cost nothing. 0.5 means it made the model
fail the main instruction 50 percentage points more often.

That is the y-axis. It needs no symbol and no acronym to state.

**The two lines differ in one word: "pair of round brackets" versus
"semicolon".** Everything else — task, wording, model, decoding, scoring — is
identical. That is what makes the result worth a figure.

---

## Why the current six-panel figure fails this reader

`main_compute_figure` is accurate and reproducible, and it fails the
five-second test:

* Panel titles read "τ(B→A)", "Δ contextual amplification", "arbitration" —
  three pieces of vocabulary a new reader does not have.
* The legend says "amplifier" and "control", which name the *conclusion* rather
  than the *manipulation*. A reader cannot tell what was actually different.
* Six panels invite the reader to look for six findings. There is one.
* The literal linear budget axis crushes 0, 256, 512 and 1024 into the first
  eighth of the plot — precisely the region where the control curve falls.
* Nothing on it states the conclusion; the reader has to derive it.

It stays in the set, retitled honestly, as the technical figure (§29 of the
brief). It stops being Figure 1.

---

## Design decisions and why

| decision | reason |
|---|---|
| **ordered categorical x-axis** | The scientific point is a progression across experimental settings, not a rate of change per token. Linear spacing hides the low end; quantitative spacing is preserved in the supporting technical figure. |
| **x-axis label "How much thinking the model was allowed"** | No symbol. The numbers underneath are captioned as maximum reasoning tokens. |
| **y-axis "Increase in failure rate on the main instruction"** | States the measure rather than naming it. The formal term appears in the caption, after the plain definition, never before. |
| **series labelled "+ one bracket pair" / "+ one semicolon"** | Concrete beats abstract: the reader learns what was manipulated instead of learning our label for its effect. "Amplifier" and "control" name a result, which is circular on the axis that shows the result. |
| **direct line labels, no legend box** | Two series; a legend would make the reader look away from the lines. |
| **two short callouts** | "More thinking fixes this one" / "This one stays broken" — the conclusion is on the figure, not inferred from it. |
| **"Natural reasoning" as the final point, visually separated** | It answers a different question from the capped points, so it is drawn across a gap rather than as one more budget. |
| **error bars described as "uncertainty across the 20 tasks"** | The method (percentile bootstrap over task clusters) belongs in the caption, not on the plot. |
| **no acronyms anywhere on the figure** | No DCI, τ, QAC, A/B/R/C, TP, KV, CI, IQR, or internal constraint IDs. |

## The claim the figure is allowed to make

Supported, and stated on the figure:

* with the bracket-pair instruction, the extra failures caused by the competing
  instruction fall to zero once the model is allowed more thinking;
* with the semicolon instruction, they do not.

**Not** claimed, and deliberately absent:

* that more thinking makes the semicolon condition *worse* — the widening gap is
  mostly the bracket condition being fixed, not the semicolon condition
  degrading;
* any scaling law, plateau, or extrapolation beyond the tested settings;
* that this generalises to reasoning models as a class. One checkpoint.

## Prototypes built and how they were judged

Three low-fidelity candidates were rendered and put to a cold reader who was
given the image and nothing else (see `COLD_READER_TEST.md`):

* **A — full progression, two lines.** The whole ordered sequence from "no
  thinking" to "natural reasoning". **SELECTED.** Understood in 10-15 seconds;
  its six recoverable gaps (what the lines are, the units, the error bars, the
  sample size, the model, a misleading trend arrow) were all closed in
  `figure1_headline`.
* **B — endpoint only.** A slope chart with just "no thinking" and "natural
  reasoning", maximising contrast at the cost of the middle. Not selected: the
  intermediate settings are what show that the bracket condition is repaired
  almost immediately and then stays repaired.
* **C — plot plus schematic.** A, with a small panel spelling out what the
  y-axis difference is made of. Not selected. It took the cold reader 45-60
  seconds, mostly fighting the layout, and it carries a real design flaw: the
  schematic explains the axis as a difference over the COMPETING instruction
  while the two lines vary the FORMATTING instruction, so it shows two
  manipulations in one panel without saying how they relate. The selected figure
  states that relationship in one sentence instead of drawing it.

## Outcome

The headline sentence survived the experiment and is now stated with the numbers
in hand: at natural reasoning the bracket-pair condition sits at **exactly
0.000** extra failures, the semicolon condition at **+0.400 [+0.225, +0.550]**.
See `COLD_READER_TEST.md` for the test transcript and every change it forced.
