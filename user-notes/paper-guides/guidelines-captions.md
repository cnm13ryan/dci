## **Guidelines for a Good Figure/Table Caption**

Synthesizing [Neel Nanda's advice on writing ML papers](https://www.lesswrong.com/posts/eJGptPbbFPZGLpjsp/highly-opinionated-advice-on-how-to-write-ml-papers) with the [ICML best practices](https://icml.cc/Conferences/2022/BestPractices), a strong caption should let a figure or table stand alone, communicating both what it shows and what the reader should conclude from it.

**Core function.** A caption is a *stand-alone explainer*: it tells the reader what is shown, how to read it, and why it matters, so that figure + caption + legend together convey the contribution on their own.

**Canonical structure**

1. **Lead Takeaway:** Open with what the reader should conclude from the figure or table — the finding, pattern, or claim. The caption should add information beyond the figure's title.
2. **Setup:** Name what is being shown — the variables, comparisons, conditions, or quantities — with units where relevant.
3. **Reading Guide:** Explain how to read the figure. Define every axis, row, column, color, marker, abbreviation, or symbol that requires interpretation, in the caption or legend.
4. **Evidence Markers:** Where applicable, note error bars, sample sizes, significance, baselines, or controls so the reader can judge the strength of the result.
5. **Type-Specific Emphasis:** Tailor the caption to the figure type.
    - **Results plot:** name the comparison, metric, baselines or controls, and headline finding.
    - **Schematic / explanatory:** state what process or structure is illustrated and the single conceptual point to walk away with.
    - **Table:** state what is compared across rows and columns and what pattern the reader should notice.
    - **Illustrative example:** state what the example demonstrates and why it is representative.

**Quality criteria**

* **Lead with the takeaway.** The first clause should state the conclusion. For example: "Accuracy plateaus beyond 7B parameters, suggesting diminishing returns from further scaling."
* **Make the figure stand alone.** A reader using only the caption and legend should understand what is shown, how to read it, and why it matters.
* **Explain every visual element that needs interpretation.** Define each axis, row, column, color, marker, abbreviation, and symbol the reader needs explained, including acronyms, condition names, and color codings.
* **Align caption, claim, and visual.** The takeaway should match the claim the figure is asked to support and should be visible in the figure itself.
* **Calibrate to the evidence.** State conclusions that the data supports, and surface the finding clearly.
* **Match the figure type.** Results plots, schematics, tables, and illustrative examples have different jobs; write each accordingly.
* **Be concise.** Aim for one to three sentences. Every clause should deliver the takeaway, support stand-alone comprehension, or explain a label.
* **Write tightly.** Each clause earns its place by adding information beyond the figure's title.
* **Use plain, precise language.** Use jargon when it improves the accuracy of the takeaway.
* **Self-check before publishing.** Confirm the caption (a) leads with a takeaway, (b) is stand-alone comprehensible, (c) explains all visual elements that need interpretation, (d) matches the supported claim with calibrated strength, and (e) is as short as it can be while preserving (a) through (d).
