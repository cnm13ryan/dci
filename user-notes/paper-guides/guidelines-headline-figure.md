## **Guidelines for a Strong Headline Figure 1**

Synthesizing [Neel Nanda's advice on writing ML papers](https://www.lesswrong.com/posts/eJGptPbbFPZGLpjsp/highly-opinionated-advice-on-how-to-write-ml-papers) with the [ICML best practices](https://icml.cc/Conferences/2022/BestPractices), a strong Figure 1 should communicate the paper's core contribution at a glance and give skimming readers a reason to keep reading.

**Core function.** Figure 1 is a *visual abstract*: it pairs with the title and abstract to convey the paper's central claim and key evidence in a single image, so that skimming readers understand what the paper contributes. Nanda recommends spending roughly the same effort on Figure 1 as on the abstract or the introduction, since they reach comparable numbers of readers.

### 1. The Purpose of a Headline Figure 1

Figure 1 is the most-seen visual in the paper. Many readers see the title, abstract, and Figure 1 before deciding whether to read further; some see Figure 1 first when the paper is shared on social media or in slides. Its job is to:

- Communicate the paper's headline claim or method in a single image.
- Give a skimming reader the same takeaway that the abstract delivers in prose.
- Provide a memorable visual anchor that readers carry into discussions, tweets, talks, and citations.
- Earn continued attention by making the contribution visible and intuitive within seconds.

A figure that does this well functions as the paper's flag — the artifact people remember and reuse.

### 2. Identifying the Figure's Central Message

A Figure 1 succeeds when it communicates a single, specific idea. Before designing it, answer three questions in writing:

- **What is the one claim the paper most needs to communicate?** This should match the headline claim of the abstract. If the paper has 1–3 claims that fit a cohesive theme, Figure 1 foregrounds the strongest of them.
- **What should a reader conclude from this figure?** State this as a specific sentence in plain language, naming the technique, the population, and the measured effect. Example: "removing a single direction from the weights jailbreaks the model across model families without retraining."
- **Why should a reader care?** Articulate what changes in the field if this claim holds. The figure should make those stakes legible.

The takeaway sentence stays visible throughout the design process. Every visual choice in Figure 1 either delivers it, supports it, or earns its place by explaining a label needed to read it.

### 3. Choosing the Right Visual Structure

Figure 1 typically takes one of three forms. Choose the form that matches the kind of contribution.

- **Method or system diagram.** Use when the contribution is a new technique, architecture, or pipeline. The diagram shows inputs, the key transformation that makes the method novel, and outputs, with the conceptually important step visually emphasized. This works especially well when the technical setup is unfamiliar to the broader audience.
- **Headline result plot.** Use when the contribution is an empirical finding — a comparison, scaling trend, or measurable effect. Plot the metric that most directly supports the claim, against the baselines that make the comparison meaningful.
- **Composite figure.** Use when the contribution requires multiple panels. Common patterns are *method-then-result* (left panel illustrates the technique, right panel shows the headline number) and *multi-evidence* (several small panels showing the same conclusion holds across settings, models, or datasets).

When in doubt, pick the form that produces an image you would put first in a tweet thread about the paper.

### 4. Components the Figure Should Include

A strong Figure 1 contains:

- **A clear focal point.** The eye should land first on the panel or visual element that carries the main claim. Use size, position, contrast, or annotation to direct attention.
- **Self-explaining visuals.** Labels, axes, panel titles, and group names should communicate the structure of the figure on their own.
- **Legible typography.** Axis labels, tick labels, legend entries, and annotations should be readable at the size the figure will appear in the published paper.
- **A colorblind-safe palette.** Roughly 4% of readers are red-green colorblind, so carry meaning on additional channels such as shape, position, or line style. For sequential heatmaps (zero to positive), white-to-blue scales work well; for diverging heatmaps (negative through zero to positive), red-white-blue works well.
- **Deliberate visual emphasis.** A short callout, an emphasized line, a highlighted panel, or a contrasting marker can carry the reader to the conclusion the figure is meant to support. When one line, point, or region matters most, make it visually dominant and let the rest recede.
- **A stand-alone caption.** Caption + legend + figure together should communicate what is shown, how to read it, and what to conclude. (See the captions guideline for the full standard.)

### 5. Common Pitfalls

These pitfalls appear consistently in weak Figure 1s. Each entry below states the principle that addresses the pitfall.

- **Make the takeaway visible.** Add an annotation, an emphasized line, or a panel title that names the conclusion the reader should walk away with.
- **Foreground one headline claim.** Reserve Figure 1 for the strongest claim, and let later figures carry the rest.
- **Design the visualization deliberately.** Choose chart type, color, emphasis, and layout to serve the takeaway.
- **Render at deployment size while iterating.** Confirm axis labels, ticks, and annotations stay readable at the published column width.
- **Define every visual element in the caption or legend.** Spell out model names, condition codes, abbreviations, and color codings the reader needs to interpret the figure.
- **Scope the figure's claim to what the experiment shows.** Match the visual to the data; later figures can broaden the picture as evidence accumulates.
- **Frame qualitative examples honestly.** Present a single illustrative case as an existence proof, or pair it with quantitative evidence in a side panel or later figure.
- **Include the strongest plausible baseline.** Tune competitor methods properly and place the headline comparison in the same figure as the result.
- **Keep every element earning its place.** Each series, panel, and annotation should deliver the takeaway, support it, or define a label needed to read it.

### 6. Step-by-Step Checklist

Use this sequence each time Figure 1 is built or revised.

1. **Write the takeaway sentence.** In one sentence, state what the reader should conclude. Keep it visible while designing.
2. **Choose the form.** Decide between method diagram, result plot, or composite based on what the takeaway sentence requires.
3. **Sketch low-fidelity first.** Iterate on layout on paper or in a rough tool, then move to production rendering.
4. **Build the focal panel first.** The panel that carries the takeaway gets designed first and most carefully; other panels support it.
5. **Add the visual emphasis that delivers the takeaway.** Annotate, highlight, or visually dominate the element the reader should walk away with.
6. **Check labels and legends.** Confirm every axis, color, marker, abbreviation, and panel is defined either on the figure or in the caption.
7. **Test legibility at deployment size.** Render the figure at the actual width it will appear and confirm all text is readable.
8. **Test color accessibility.** Verify the figure works in grayscale and for red-green color blindness, and switch palettes when information depends on red-green distinctions.
9. **Write the caption.** Lead with the takeaway, define the visual elements, and note any evidence markers (sample size, error bars, baselines). See the captions guideline.
10. **Show it cold to a reader who hasn't seen the paper.** Ask what they take from the figure and caption alone. Iterate until their summary matches the takeaway sentence from step 1.
11. **Align with the abstract.** Confirm the takeaway in Figure 1 matches the headline claim in the abstract, and keep them aligned as the paper evolves.
12. **Polish.** Tighten alignment, spacing, and typography, retaining the visual elements that earn their place.
