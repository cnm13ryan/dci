## **Guidelines for a Good Bullet-Point Paper Outline**

Synthesizing [Neel Nanda's advice on writing ML papers](https://www.lesswrong.com/posts/eJGptPbbFPZGLpjsp/highly-opinionated-advice-on-how-to-write-ml-papers) with the [ICML best practices](https://icml.cc/Conferences/2022/BestPractices), a strong bullet-point outline is the scaffold the full draft will inherit. It commits to claims, sequences the evidence, and invites feedback before any prose is written.

**Core function.** The bullet-point outline is the third step in the iterative writing process: compressed narrative → introduction outline → full paper outline → first-draft figures → prose draft. Its job is to convince a skeptical, engaged reader that the paper's 1–3 claims are true, by laying out the sequence of background, methods, experiments, results, figures, and limitations that builds the case. Feedback on an outline costs far less to incorporate than feedback on eight pages of prose.

**North star.** The outline succeeds when a careful reader can trace each claim from the introduction through its background, method, experiment, and result, and identify the figure that anchors it.

## When to Write the Outline

Begin after the abstract and the introduction outline are drafted. The compressed narrative fixes the 1–3 claims. The introduction outline fixes how those claims are motivated and previewed. The full paper outline expands the rest of the paper to substantiate them.

## Canonical Structure

1. **Header section.** Restate the working title, abstract, and contributions list. The outline operates as a delta against these; everything else exists to support them.
2. **Introduction outline (reference).** Carry forward the bullet outline of the introduction, including paragraph-level claims, motivation, and the contributions list.
3. **Background bullets.** List the terminology, notation, problem setting, and standard methods the reader needs. Tag each item with the section it serves. Mark which items move to an appendix glossary.
4. **Methods bullets.** For each experiment, plan: the claim it supports, the hypothesis it discriminates, the setting (datasets, models, what varies, what stays fixed), the metric, the baselines, and the uncertainty protocol. Mark which analyses are pre-specified.
5. **Results bullets.** For each experiment, plan: the question, the headline finding, the interpretation, and the limitation. Order results to mirror the order of claims in the introduction.
6. **Figure plan.** Plan Figure 1 as the centerpiece — the diagram or composite that conveys the contribution at a glance. Plan one supporting figure or table per major experiment. For each, specify the takeaway, the form (results plot, schematic, table, illustrative example), the comparison, and the placement.
7. **Discussion bullets.** List the limitations, alternative explanations, implications, and future work directions. Cover the objections a careful reader would raise, and pair each with the bullet that addresses it.
8. **Related work bullets.** Decide placement (after the introduction or near the discussion). List the close, parallel, and corrective prior work, and write a one-sentence delta for each.
9. **Appendix bullets.** List the secondary sweeps, full hyperparameter tables, additional ablations, qualitative samples, and tacit-knowledge notes that support the main body from the back.

## Quality Criteria

* **Anchor every bullet to a claim.** Each bullet earns its place by serving one of the 1–3 claims. Apply the test: "What breaks in the paper if this is cut?" Cut anything that survives the test without consequence.
* **Map experiments to claims explicitly.** Tag each experiment bullet with the claim it supports. Surface gaps where a claim has weak coverage.
* **Plan Figure 1 first.** Treat Figure 1 as load-bearing alongside the abstract and introduction. Sketch its layout in the outline.
* **Plan, then defer rendering.** Specify each figure's takeaway, form, and comparison in the outline. Build the actual figures in the next stage.
* **Order results to mirror the introduction.** A reader who follows the contributions list should encounter the evidence in the same order.
* **Open and close paragraphs deliberately.** For each paragraph-level bullet, draft the opening sentence (what it shows) and the closing sentence (how it fits the paper).
* **Red-team in the outline.** List the holes a skeptical reader would find. For each, decide whether to run a new experiment, add an ablation, or address it as a limitation. Mark which bullets carry that weight.
* **Calibrate confidence per claim.** Tag each claim as existence-proof, systematic, hedged, narrow, or guaranteed. Match the planned evidence and language to the tag.
* **Mark pre-specified and post-hoc analyses.** Label confirmatory findings and findings that emerged from post-hoc inspection.
* **Flag qualitative example selection.** State whether examples are random, curated, or exhaustive. Reserve single examples for existence-proof claims.
* **State the novelty delta.** For each claim, specify what is new, what extends prior work, and what is borrowed. Decide where this delta lives (introduction, related work, or both).
* **Surface limitations explicitly.** Add a limitations bullet to the discussion section for each known caveat. Match the strength of the claim to the strength of the evidence.
* **Allocate time across the load-bearing surfaces.** Plan to spend roughly equal effort on the abstract, the introduction, the figures, and the rest of the paper combined.
* **Write for a cold-start expert reader.** Define each term the outline assumes. Bullets that feel obvious to the author are often opaque to the reader.
* **Use plain, precise language.** Reach for jargon when it sharpens a claim.

## Workflow

1. **Carry forward the abstract and introduction outline.** Start the document with these locked in.
2. **List every experiment.** For each, write a one-line claim → setting → metric → baseline → uncertainty bullet.
3. **Cut to the case-supporting subset.** Apply the "what breaks if I cut this?" test. Move the rest to appendix bullets.
4. **Sequence by claim.** Order experiments to mirror the introduction's contributions list.
5. **Plan figures.** Specify Figure 1 and one supporting figure per major experiment, each with a takeaway and form.
6. **Red-team.** List the strongest objections. Address each with an experiment, an ablation, or an explicit limitation.
7. **Draft openers and closers.** For each paragraph-level bullet, write the opening sentence and the closing sentence.
8. **Get feedback.** Share the outline with a mentor, collaborator, or paper-swap partner. Iterate before writing prose.

## Common Pitfalls

* **Including everything that was run.** Outlines bloat when the author writes from memory of the project. Write from the claims down.
* **Skipping figure planning.** Outlines that defer figures to the prose stage produce papers where figures arrive as afterthoughts.
* **Vague bullets.** "Discuss results of method X" hides decisions. Commit to the claim, the metric, and the comparison inside the bullet.
* **Background sprawl.** Background bullets multiply when the author tries to cover everything. List only what the reader needs to follow the claims.
* **Ordering by chronology of research.** Order by argument structure. The reader benefits from the logical sequence, regardless of the project's timeline.
* **Hiding limitations until the end.** Surface them in the outline. A paper that defends its limitations from the start earns trust.

## Practical Note

The outline is a living artifact. Expect to revise it as figures take shape, as feedback arrives, and as the prose draft surfaces gaps. Treat the outline as the cheapest place to make structural changes; every revision deferred to the prose stage costs more.
