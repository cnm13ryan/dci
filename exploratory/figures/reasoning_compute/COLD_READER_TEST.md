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

---

# Round 2 — retest of the final `figure1_headline`

Same protocol, same model-based proxy, one image and nothing else. The reader
answered questions 1–7 substantially correctly, including the one-sentence
conclusion:

> "For Qwen3-4B, extra thinking time eliminates the cost of one added formatting
> instruction (a bracket pair) but not another (a semicolon), so 'let it think
> longer' is not a general fix for instruction interference."

Time to the main point: **25–30 seconds** — slower than round 1's 10–15, because
the figure now carries the setup the reader previously had to guess at.

## What the retest changed

The reader's sharpest objections were about **claims stronger than the data**, and
all three were acted on rather than defended:

| objection | verdict | action |
|---|---|---|
| "*More thinking fixes this one* is not what the blue line shows — it collapses between no-thinking and 256, the smallest budget tested, then is flat. The arrow points at 1024, which is arbitrary." | **Correct.** | Callout re-aimed at the 0 → 256 drop. First reworded to "Any thinking at all fixes this one"; **that wording was itself withdrawn later** — see the note below — and is now **"Gone by the smallest budget tested"**. |
| "The orange annotation arrow ends in empty space … it reads as if tracing a downward trend — exactly the opposite of the claim it is attached to." | **Correct.** | The arrow is **removed**. The text now sits above the line and makes a claim about level, not shape: **"This one never returns to zero"**. |
| "*The conflict between its instructions* is not measured — the competing instruction is never named. The figure's headline concept is invisible in the data." | **Correct.** | The subtitle now names it: *make each sentence longer than the last*. |

### Later correction to the first row

"Any thinking at all" replaced one overclaim with another, and a subsequent
review caught it. The wording asserted a result across the entire 1–255 range,
in which no positive budget was ever run, so a transition or a reversal inside
that range stays fully consistent with the plotted points.

The second problem is larger and was not raised in review. 256 is not a clean
small-budget condition: **86% of bracket rows and 94% of semicolon rows hit that
cap**, so it is a truncation condition in which the cap forms part of the
treatment rather than a budget the model finished inside. The same applies to
the semicolon point at 512, whose 60% cap-hit rate sits underneath the highest
estimate on the chart.

The callout therefore now claims only the level at the smallest budget actually
tested, and every materially cap-bound point is drawn with a hollow marker so a
reader can see which conditions were cut off. The uncapped natural condition,
with a 0% cap-hit rate, is what carries the bracket claim.

Three further fixes followed from the same report: the y-axis note now says what
the increase is **over** ("0 = the competing instruction caused no extra
failures"); the footer states that each point is a paired difference across 20
tasks with 80 answers behind it, resolving a "160 vs 20 × 2" arithmetic the
reader could not reconcile; and the footer records that **2,048 was never run**
and that the axis is ordered rather than to scale.

## Objections recorded but NOT fixed on the figure

* **"The orange series bounces by 0.3 with error bars of ±0.2."** Right, and it is
  why no shape is claimed anywhere. The figure asserts only that the line never
  returns to zero, which its intervals do support.
* **"At *No thinking* the two conditions are statistically indistinguishable."**
  Right — +0.450 [+0.275, +0.625] against +0.525 [+0.350, +0.676]. The separation
  appears from 256 onward. Recorded in `NATURAL_REASONING_RESULTS.md` rather than
  crowding the figure.
* **"Natural has a median of 511, essentially the 512 condition, yet gives 0.40
  against 0.63."** The best catch in either round. It is now stated explicitly as
  an unresolved tension in `NATURAL_REASONING_RESULTS.md`: the 512 setting cut
  short 60% of its rows while natural's tail runs to 5,888, *and* the intervals
  overlap, so part of the gap may be noise. The figure does not claim natural
  beats 512.
* **"How sentences are counted is not stated."** True; it is a frozen verifier
  documented in `METRIC_SPEC.md`, not something Figure 1 can carry.

## Standing limitation

Both rounds used a **model-based proxy reader, not a human subject**. It is a real
test of whether the figure is self-contained, because the reader genuinely had no
project context. It is not a human study and is not described as one.
