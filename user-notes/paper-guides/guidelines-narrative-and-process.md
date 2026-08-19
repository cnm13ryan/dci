## **Guidelines for Narrative, Claims, and Writing Process**

These guidelines apply across every section of the paper. They describe what makes a paper coherent, what makes evidence credible, and what writing process produces clarity. Each section guideline assumes these principles.

## Narrative and Claims

**A paper advances 1–3 specific concrete claims that fit a cohesive theme.** Everything else serves these claims: the abstract introduces them, the introduction motivates and previews them, the background provides their context, the methods and results substantiate them, and the discussion calibrates what they support.

**Compress the research into claims before writing.** List what was learned, identify the 1–3 statements you can defend, and select the experiments that most strongly support each. Move secondary findings to appendices.

**Calibrate claim strength to evidence:**

* **Existence-proof:** "We found at least one case where X happens."
* **Systematic:** "X happens across a wide range of contexts."
* **Hedged:** "There is suggestive evidence that X is true."
* **Narrow:** "X is the best method in setting Y under condition Z."
* **Guarantee:** "X is always true."

**State the novelty delta.** Specify what is new, what extends prior work, and what is borrowed. Use the Introduction and Related Work to make this delta explicit.

## Evidence Standards

* **Verify experiments before writeup.** Re-run, cross-validate, or re-implement at least 75% of the experiments worth mentioning, especially the most critical ones.
* **Apply the belief-update test.** Ask of every result: "Should this update a reader's beliefs about my claims?" Keep what passes. Cut what fails.
* **Red-team the narrative.** Assume a mistake exists and search for it. Identify the holes a skeptical reader would find. Run new experiments to address them and discuss the limitations directly.
* **Prioritize decisive experiments.** Surface the most claim-relevant evidence in the main body. Move secondary sweeps and confirmatory near-duplicates to the appendix.
* **Use diverse lines of evidence.** Combine qualitatively different tests of the same claim. Pair quantitative summaries with qualitative inspection where possible.
* **Tune baselines as seriously as the proposed method.** Document the prompting, scaffolding, and hyperparameter search effort applied to each baseline. Include the strongest plausible alternative readers would consider.
* **Treat marginal p-values with skepticism.** Aim for `p < .001` in exploratory work. Subject findings at `.01 < p < .05` to additional verification.
* **Label pre-specified and post-hoc analyses.** Pre-specified predictions carry the strongest evidential weight. Mark which findings are confirmatory and which emerged from post-hoc inspection.
* **Flag qualitative example selection.** State whether each example is random, curated, or exhaustive. Single examples support existence-proof claims. Systematic claims require sampled or exhaustive evidence.

## Writing Process

* **Treat writing as a major multiplier on impact.** A paper's value depends on readers understanding it. Allocate roughly equal time to the abstract, the introduction, the figures, and the rest of the paper combined.
* **Compress, then iteratively expand:**
  1. Write a bullet-point narrative capturing the 1–3 claims, motivation, and key evidence.
  2. Expand into a bullet-point introduction outline.
  3. Expand into a bullet-point full-paper outline.
  4. Make first-draft figures.
  5. Write a full prose draft.
  6. Edit, polish, and tighten.

  Get feedback after each step. Earlier feedback costs less to incorporate.
* **Address the illusion of transparency.** A reader has a small fraction of your context. Define terms, motivate choices, and specify details that feel obvious to you. Show drafts to someone unfamiliar with the work and ask what was unclear.
* **Use plain, precise language.** Reach for jargon when it sharpens the claim. Use simple language otherwise.

## Reader Experience

* **Support random access.** An expert reader can jump to any single result, definition, or claim and understand it. Recap notation briefly, restate the claim, and write self-contained captions.
* **Foreshadow the structure.** The Introduction names the claims and previews the evidence. Each section opens by stating which claim it addresses and closes by stating what was established.
* **Match confidence language to evidence.** Use "preliminary," "suggestive," "compelling," "definitive," "narrow," or "existence-proof" to signal the strength supported by the evidence.
* **Make the title contribution-focused and memorable.**
