# Captions, written result-first

Every caption here follows one rule: **state the result, then the setup, then how
to read it, then the caveat.** Technical terms appear only after the idea they
name has already been explained, and never in the first sentence.

---

## Figure 1 — `figure1_headline`

> **Letting the model think for longer removes the conflict between its
> instructions when the prompt asks for one pair of brackets, but not when the
> same prompt asks for one semicolon instead.** Every prompt asks the model to
> explain something in exactly four sentences while also obeying a competing
> instruction and one formatting instruction; the lines show how much more often
> the model breaks the four-sentence instruction when the competing instruction
> is present, as it is allowed more thinking. "Natural reasoning" means the model
> was allowed to finish thinking on its own instead of being stopped at a token
> limit — no response came close to the safety ceiling. Error bars are 95%
> intervals from resampling the 20 tasks.

If the formal vocabulary is needed later: the quantity plotted is the increase in
target-constraint failure caused by adding the focal constraint rather than a
matched reference, which this project calls **directional constraint
interference** and denotes τ<sub>B→A</sub>; the two backgrounds are the
amplifying and matched-control formatting constraints at instruction order QAC
and load k = 3.

**Exact wordings.** Main instruction: *"Write exactly 4 sentences."* Competing
instruction: *"Make each sentence strictly longer than the preceding sentence."*
Matched comparison: *"Begin every sentence with a word whose first letter is S."*
Formatting instruction, the only thing that differs between the lines: *"Use
exactly 1 pair of round brackets in the whole answer, and place it wherever you
judge best."* against *"Use exactly 1 semicolon in the whole answer, and place it
wherever you judge best."*

**Caveats.** The thinking settings tested were 0, 256, 512, 1,024, 4,096 and
natural; **2,048 was not run**, and the axis is ordered rather than to scale. The
semicolon line's up-and-down shape is well within its own error bars — the claim
is that it *persists*, not that it has a trend. Nothing here says extra thinking
makes the semicolon condition worse: at natural reasoning it sits at +0.40,
below its own no-thinking value of +0.53. One model, one task family.

---

## Figure 2 — `fig15_natural_reasoning_length`

> **When nothing stopped it, the model usually thought for about 500 tokens, and
> never came near the limit we had to impose for engineering reasons.** The left
> panel counts responses by how many reasoning tokens they used; the right panel
> is a cumulative view — the height of each curve at a given length is the share
> of responses that had finished thinking by then. The safety ceiling was 39,550
> tokens and **0 of 160 responses reached it**, which is what makes it fair to
> call this condition natural rather than merely generous.

Median 511 reasoning tokens, and the longest single trace 5,888. One response
exceeded 4,096 — which is precisely the tail that the 4,096-token setting cuts
off. The semicolon condition thinks noticeably longer than the bracket condition.

---

## Figure 3 — the technical compute-response figure (`main_compute_figure`)

> **For readers who want the exact experimental structure rather than the
> headline.** Six panels on the assigned-budget axis: per-constraint compliance,
> the two failure rates the interference measure is built from, τ<sub>B→A</sub>
> for both backgrounds, the amplification difference Δ, conflict arbitration, and
> the realised-reasoning and cap-hit diagnostics. Uses the project's own
> notation throughout, with quantitative rather than ordered spacing.

The natural condition is deliberately **not** on this axis: its ceiling of 39,550
is an engineering bound that never binds, not a comparable assigned treatment
level, and plotting it at its numeric position would put one point at 39,550 on
an axis whose others end at 4,096. It appears in Figures 1 and 2.

---

## A note on what "natural reasoning" does and does not mean

It means exactly one thing: **the experiment did not stop the model's reasoning
before it finished.** It does not mean unlimited compute, unlimited context, or
the model's maximum capability. A ceiling still existed for engineering reasons;
the condition is valid because that ceiling was never reached.

## A note on "2 replicates"

Each point rests on 20 tasks × 2 replicates. An earlier version of the generation
harness passed one random seed for every request, which made replicate pairs
byte-identical — two draws counted once. Every number in these figures comes from
regenerated runs with per-row seeds, verified at **0 of 400 replicate pairs
identical**, against 390 of 400 before the fix.
