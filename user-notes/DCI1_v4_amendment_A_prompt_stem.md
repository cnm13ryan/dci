# Amendment A (draft) — a uniform answer-length instruction in the prompt stem

**Status: DRAFT. Not applied. Not adopted. Not signed.**
No code, constant, verifier, threshold, grid, ladder or wording has been
changed on account of this document. It amends nothing until the researcher
adopts it; the FORM × STEM screen (`reports/fs_screen_v4/`) is the evidence it
waits on.

**Amends:** §8.5 (prompt construction), with consequences for §6.2 (topics),
§9.3 (non-vacuity), §12 (regime screen and calibration) and §17.4.

---

## 1. The change

One sentence is inserted into the prompt template, between the topic question
and the numbered constraint list:

```
Answer in 60 to 120 words.
```

§8.5 currently reads: *"Every prompt has three parts in the same order: the
topic question, a numbered list of the active constraints, and the line
`Answer:`."* It would read: **four parts** — the topic question, the answer-length
sentence, the numbered list, and `Answer:`.

The sentence appears in **every cell without exception**: zero-constraint,
solo, and composed, in both instruction orders, for every model. It is
template text, byte-identical everywhere, and carries no topic-specific or
cell-specific content.

## 2. What it is not

The sentence is **background, not a constraint under study**. Specifically:

- it is **never scored as an outcome** — no `X_c`, no `G_c`;
- it **never enters a compliance vector** (§9.1) at any position;
- it **never counts toward load** — a prompt carrying it and one constraint
  is a load-1 prompt, exactly as now;
- it is **not a registered constraint** and has no severity, no ladder, no
  wordings, and no witness obligations;
- it is **not subject to the §7.3 length caliper**, because it is not a
  constraint wording.

Its realised satisfaction rate — the fraction of answers landing in
[60, 120] words — is recorded as a **diagnostic** on every stage record, so
we learn whether the models obey it. That rate is descriptive. It gates
nothing and no estimand reads it.

## 3. Why this is not a §6.2 leak

§6.2 requires of each authored question: *"no wording that itself mentions
any letter, word length, word shape, punctuation-count, or capitalisation
requirement."*

Two readings, and the amendment should state both rather than pick the
convenient one.

**Strict reading — the prohibition does not reach this sentence.** §6.2
governs the 624 **authored questions**, and its enumerated prohibitions are
all *per-word* properties: letters, word length, word shape,
punctuation-counts, capitalisation. Those are exactly the properties the
registered constraints test, and the rule exists to stop a question hinting at
its own cell's constraint. *Answer length in words* is on none of that list,
and the stem is not question text — it is template text that §8.5 governs. On
this reading Amendment A needs no §6.2 carve-out at all and is purely an §8.5
change.

**Cautious reading — take the carve-out anyway.** The spirit of §6.2 is that
prompt text must not carry information correlated with the constraint being
measured. B ("every word at most *m* letters") is a length constraint, and an
answer-length instruction is a length instruction, so a reader may reasonably
say the rule is engaged. The carve-out is then argued on the ground that
matters:

> A fixed template sentence, identical in every cell of every block for every
> model, is **not a per-topic leak**. §6.2's concern is *differential*
> information — a question whose wording tips off its own constraint. A
> constant cannot be differential. It shifts the level of every cell equally
> and cancels from every within-block contrast the design estimates, because
> every registered estimand is a difference between two cells of the same
> block that both carry it.

The recommendation is to adopt the carve-out explicitly, in §6.2 as a new
final sentence, so no future reader has to relitigate which reading applies:

> *This rule governs authored question text. Fixed template text that is
> identical in every cell — including the answer-length sentence of §8.5 — is
> not question text and is not restricted by this rule.*

## 4. The strongest argument for it, which is about §9.3

§9.3 registers the 20-word non-vacuity threshold on this reasoning, verbatim:

> *"The 20-word threshold is registered on the reasoning that the topic space
> asks for sixty to one hundred and twenty word answers, so an answer below
> twenty words has abandoned the task rather than satisfied the constraint."*

**The prompts never say so.** §6.2 describes the task space as *"answerable in
sixty to one hundred and twenty words"*, and §8.5's template never states it.
The registered vacuity threshold therefore rests on a premise the instrument
does not put to the model. A 12-word answer is currently scored as having
"abandoned the task" against a length expectation it was never given.

The 2026-08-20 diagnostic shows what that costs. Under the current stem:

| model | B-solo median words | B-solo passes that are <20 words |
|---|---:|---:|
| E2B | 25 | 47 % |
| E4B | 31 | 39 % |
| Qwen3-4B | 8 | 100 % |
| Qwen3-4B-Inst | 8 | 94 % |

Truncation is ~0 in every one of those cells, so this is behaviour, not a
completion cap. Both Qwens answer a B-solo prompt in a median of **eight
words**. Amendment A does not change what counts as vacuous; it makes the
prompt state the expectation against which vacuity was already being judged.

That is the honest framing: **this is not a new requirement, it is the
existing premise made operative.**

## 5. What it costs

Stated plainly, because it is not small.

1. **Every registered rate is re-screened.** Completion-cap selection (§12.1),
   the dense ladder screen (§12.2), *n\** and *m\** (§12.3) and the §13.2
   reference admission are all measured under the current stem. A prompt-template
   change is a change of experimental condition, so every one of them is
   re-measured. Nothing already measured is invalidated — it stops being
   comparable, which is different, and both readings must be recorded.
2. **The completion cap may move.** Zero-constraint prompts truncated in 92 %
   (E2B) and 88 % (E4B) of cases at cap 512. A length instruction that the
   models obey would *reduce* that, possibly changing which cap §12.1 selects.
3. **The operating bands may move.** §12.3's bands assume compliance curves
   measured without a length floor. Longer answers make every length-monotone
   constraint — B and all eight reference families — **harder**, so both curves
   shift down. The Q6 fragility analysis shows Qwen3-4B has one eligible focal
   severity, at the permissive end of the grid, with 0.150 of downward margin;
   a downward shift is exactly the direction that triggers
   `FOCAL_RANGE_EXHAUSTED` with no fallback rung. **This is the main risk of
   Amendment A and the screen is designed to measure it.**
4. **§6.2's description becomes true of the prompts for the first time.** The
   task space has always been *described* as 60–120 words. After this change it
   is *stated* to the model. Generalisation claims about "the topic population
   of §6.2" become claims about a population the prompts actually define.
5. **A new failure mode: instruction interference.** The stem is one more
   instruction competing for compliance. If it is itself subject to delivery
   loss, it could interact with the constraints under study rather than sitting
   inertly beneath them. Its recorded satisfaction rate by load is the
   diagnostic for that, and a strong load-dependence in it would be an argument
   against adoption.

## 6. Adoption condition

Adopt only if the screen shows, under `floored`:

- B-solo vacuous share of passes **≤ 0.10 on all four models** (the §2.4
  B-side criterion); and
- no model pushed to `TARGET_RANGE_EXHAUSTED` or `FOCAL_RANGE_EXHAUSTED`; and
- the stem's own satisfaction rate not strongly load-dependent.

If the first holds and the second fails for one model, that is a real result
and not a reason to discard the amendment: it means the length channel and the
operating-point channel cannot both be satisfied on the current grids, which is
itself decision-relevant and belongs in the record.

## 7. What this amendment does not fix

Amendment A removes the *shortening escape*. It does **not** remove the
length **gradient**: B and all eight registered reference families remain
`S ≤ q` monotone count budgets whose pass sets are downward-closed under
prefix. Within the 60–120 band, a 62-word answer still passes them more easily
than a 118-word one. Amendment A narrows the range over which that gradient can
operate; it does not change its direction. Amendment B addresses the gradient.
The two are complements and the screen tests them as crossed factors precisely
so that their separate sufficiency can be reported.
