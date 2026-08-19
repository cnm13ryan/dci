## **Guidelines for a Good Results Section**

Synthesizing [Neel Nanda's advice on writing ML papers](https://www.lesswrong.com/posts/eJGptPbbFPZGLpjsp/highly-opinionated-advice-on-how-to-write-ml-papers) with the [ICML best practices](https://icml.cc/Conferences/2022/BestPractices), a strong Results section presents claim-relevant evidence clearly, precisely, and credibly.

**Core function.** The Results section substantiates the paper's claims. It reports what was observed, ties each finding to a claim, and calibrates how strongly the evidence supports each conclusion. The Methods section owns experimental design.

## Layout

Choose the layout that fits the evidence.

**Layout A — Pooled Results.** Use when most experiments share the same setup. Group results by claim or experiment family in the order of the Introduction's claims. For each, state the question, present the figure or table, and interpret the result. Place ablations and robustness checks after the main results.

**Layout B — Per-Claim Sections.** Use when different claims require substantially different evidence. Pair each claim with its setup and result so readers encounter them together.

## For Each Result

1. **Question.** Restate the claim the experiment tests.
2. **Result.** Lead with the headline finding — the key number, figure, or table the reader should remember.
3. **Interpretation.** Explain what the result shows about the claim, and state the main limitation of the evidence.

Push secondary sweeps and sensitivity analyses to a later paragraph or the appendix.

## Quantitative Reporting

* **Use concrete numbers.** Report "+4.2 points over the strongest baseline," with units and direction.
* **Report variation alongside point estimates.** Place confidence intervals, standard deviations across seeds, or other distributional summaries next to the headline number.
* **Treat marginal p-values with skepticism.** Aim for `p < .001` in exploratory work. Verify findings at `.01 < p < .05` through additional evidence.
* **Prioritize decisive experiments.** Surface the most claim-relevant evidence in the main body. Move secondary sweeps and confirmatory near-duplicates to the appendix.

## Honesty and Calibration

* **State limitations up front.** A result with caveats acknowledged earns more trust than one oversold.
* **Label pre-specified and post-hoc analyses.** Mark findings that confirmed predictions made before the experiment, and mark patterns spotted afterward.
* **Flag qualitative examples.** State whether each example is randomly sampled or curated. Single examples support existence-proof claims. Systematic claims require sampled or exhaustive evidence.
* **Match confidence language to evidence.** Use "existence-proof," "systematic," "hedged," "narrow," or "guaranteed" to signal the strength supported.

## Connection to the Narrative

* Each subsection has a clear answer to "what breaks in the paper if this is cut?"
* The order of results mirrors the order of claims in the Introduction.
* Section openings restate which claim is being addressed. Section closings summarize what was established.

## Random Access

An expert reader who jumps directly to a single result can understand it. Recap notation briefly, restate the claim, and write self-contained figure captions.

## Figures and Tables

* **One identifiable takeaway per figure.** Decide the takeaway before plotting.
* **Self-contained captions.** State what the figure shows, how to read it, which trace matters most, and the takeaway.
* **Annotate or visually emphasize the most important comparison.** De-emphasize supporting traces.
* **Make axes, ticks, and legends large enough to read at print size.** Use color choices that work for red-green colorblind readers.
* **Tables report metric, variation, and baselines side by side.**

## Separation of Layers

Keep the observation, the result, and the interpretation visibly separate. A reader can identify what was seen and what is inference.

The Results section is the place where the author's authority gives way to the reader's verification. Anything that obstructs that check — missing variance, cherry-picked qualitative cases, undefined comparisons — counts as a defect even when the underlying result is correct.
