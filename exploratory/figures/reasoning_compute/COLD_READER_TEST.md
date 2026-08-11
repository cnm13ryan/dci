# Cold-reader comprehension test

## Method, and its limits

Two prototypes were shown to a reader with **no access to this project** — no
repository, no captions, no code, no README, no filenames beyond the images
themselves — and asked five comprehension questions plus four diagnostic ones,
with an explicit instruction to be blunt rather than charitable.

**This was a model-based proxy reader, not a human subject.** It is a genuine
test of whether the figure is self-contained, because the reader really did have
no project context; it is not a substitute for showing the figure to a person,
and no claim is made that it is.

## What the reader got right without help

* **The question under test.** "Whether giving a language model a larger
  thinking/reasoning-token budget makes it stop failing an instruction when a
  second, conflicting instruction is added."
* **The result.** "Extra thinking fixes one conflict entirely and does
  essentially nothing for the other."
* **Time to grasp prototype A: 10–15 seconds.** Prototype C: 45–60 seconds, and
  the reader said most of that was fighting the layout rather than thinking.

That is the five-second target substantially met on A, and clearly failed by C.

## What the reader could NOT recover — every one of these was fixed

| gap reported | fix in `figure1_headline` |
|---|---|
| "What the two conditions actually are — total guess." Could not answer "what is different between the two lines?" from A at all. | A one-sentence subtitle now states that every prompt carries the same three kinds of instruction and that **the lines differ only in the formatting instruction**; the lines stay directly labelled "+ one bracket pair" / "+ one semicolon". |
| "Whether the y-axis is percentage points, a proportion difference, or a ratio. Guessed." | The axis now names the main instruction — *"write exactly 4 sentences"* — and an on-figure note reads **"0 = the extra instruction cost the model nothing"**. |
| "What the error bars are — 95% CI? SE? Bootstrap? Not stated." | Footer: **"error bars are 95% intervals from resampling the tasks"**. |
| "Sample size … not stated." | Footer: **"20 tasks × 2 replicates behind every point"**. |
| "What model this is. Not stated anywhere." | Footer: **"Qwen3-4B"**. |
| "The annotation arrow drawn from 512 down to 4,096 implies a trend that the error bars don't support." | The callout no longer traces that path; it points at the flat right-hand section. **This was a fair objection and the arrow was misleading.** |

## What the reader flagged that is a real limitation, not a fixable label

* **"2,048 is missing with no explanation."** Correct. The tested sequence is
  0, 256, 512, 1,024, 4,096, natural; 2,048 was never run. The axis is ordered
  categorical, so the gap is invisible. This is stated in the caption rather than
  papered over.
* **"The orange line's zigzag is well inside its own error bars, so 'this one
  stays broken' may be the only real signal and the shape is probably noise."**
  Also correct, and it is exactly the claim the figure makes — persistence, not
  shape. No trend is asserted for the semicolon line anywhere.

## Why prototype C was not selected

The reader found it **broken as rendered**: the blue callout had moved on top of
the orange line and was clipped to read "*ixes this one*"; the grey explanatory
sentence was overprinted by the black question; both prompt boxes were too short,
so their last lines spilled below the border.

Beyond the rendering, it had a genuine design flaw the reader isolated precisely:

> "the axis varies one thing and the line colour varies another thing, and I had
> to work that out by re-reading the panel three times. I still don't know
> whether '+ one semicolon' means both A and B had the semicolon instruction, or
> only B did."

That is right. The schematic explains the y-axis as a difference over the
*competing* instruction, while the two lines vary the *formatting* instruction —
two different manipulations shown in one panel without saying how they relate.
Prototype C is kept as a prototype, unfixed, because it records why the selected
figure states the relationship in one sentence instead of drawing it.

## Verdict

**Prototype A selected**, with all six recoverable gaps closed, shipped as
`figure1_headline`. Prototypes B and C are retained as the design record.

Deployment-size check at 7 inches (two-column paper width): every label, callout
and footer remains legible without zooming, and the two series stay
distinguishable in greyscale through line style (solid/dashed) and marker shape
(circle/square) as well as colour.
