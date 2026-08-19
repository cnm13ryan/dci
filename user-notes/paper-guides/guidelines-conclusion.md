## **Guidelines for a Good Conclusion Section**

Synthesizing [Neel Nanda's advice on writing ML papers](https://www.lesswrong.com/posts/eJGptPbbFPZGLpjsp/highly-opinionated-advice-on-how-to-write-ml-papers) with the [ICML best practices](https://icml.cc/Conferences/2022/BestPractices), a strong Conclusion section delivers a final, calibrated synthesis of the paper's contribution that the Introduction and Discussion do not already provide.

**Core function.** The Conclusion is optional. Include one only when it adds a final synthesis the Introduction and Discussion lack: a compact restatement of the contribution, its scope, and what the reader should now do or believe. When a Conclusion would only repeat the Introduction, omit it and let the Discussion close the paper. When space is tight and the Discussion already states limitations first, cutting the Conclusion is preferable to padding it.

## When to Include One

* **Include** a Conclusion when it synthesizes claim, scope, implication, and next step into one place no other section occupies, or when venue norms expect the section.
* **Omit** it when it would duplicate the Introduction's summary, when the Discussion already provides the closing synthesis, or when page limits are binding.

## Limitations-First Principle

A Conclusion must stay calibrated. State the contribution first so the section reads as a confident close, then bound it immediately so the reader leaves with beliefs matched to the evidence. Limitations appear early and prominently, never as an afterthought and never omitted. The full enumeration of limitations belongs in the Discussion; the Conclusion names only the single boundary that most constrains the headline claim and refers to the Discussion for the rest.

## Canonical Structure

A limitations-first Conclusion follows five moves, most one sentence each.

1. **Contribution, compressed.** State the one to three claims and the single takeaway. Match the verb to evidence strength: "show" or "establish" for systematic results, "provide evidence that" for hedged results, "exhibit a case where" for existence proofs.
2. **Scope and limitations bound.** State the regime the results hold for, the generalization not claimed, and the single most consequential open caveat. Point to the Discussion for the full list rather than re-enumerating.
3. **Calibrated implication.** State the concrete action or belief update the results support, and for which audience, using the same confidence word as move 1.
4. **One pointed future direction.** Name a single decisive experiment tied to a claim and what it would resolve, falsify, or strengthen. Avoid a list of directions.
5. **Conditional significance** (optional). State the broader payoff conditioned on the boundary in move 2, keeping forward-looking claims honest.

## Two Modes

* **Paper has a separate Discussion.** Keep the Conclusion to a tight four-to-six-sentence paragraph using the five moves. Move 2 names one boundary and defers the rest to the Discussion, so the Conclusion stays synthetic and avoids duplication.
* **Paper has no separate Discussion.** Let the Conclusion absorb the Discussion's role: expand move 2 into a full limitations list, then add Implications, Future Work, and Reflections and Tacit Knowledge as separate elements. (See the discussion guideline for the canonical order of those elements.)

## Quality Criteria

* **Add synthesis, not repetition.** Every sentence should compress something the Introduction and Discussion state separately, or it should be cut.
* **Open confident, bound early.** Lead with the contribution, then state the governing limitation before the implication.
* **Name one limitation, not all.** Surface the single most constraining caveat and defer the full list to the Discussion.
* **Calibrate language to evidence.** Use consistent confidence terms (preliminary, suggestive, compelling, definitive) and keep the same term across the contribution and its implication.
* **Make the implication concrete.** Specify the action, design choice, or belief revision, and the audience it applies to.
* **Point future work at a claim.** Give one decisive next experiment and the question it resolves, rather than a list.
* **Stay within the evidence.** Keep every statement inside what the design and analysis establish.
* **Prefer omission to padding.** If the Conclusion cannot add synthesis, drop it and let the Discussion close the paper.

## Worked Example

A limitations-first Conclusion for a paper that already has a separate Discussion:

> We provide evidence that pruning attention heads by [importance metric] recovers 98% of baseline accuracy at 40% sparsity across three encoder models and two benchmarks. These results hold for encoder models under 1B parameters; we do not claim transfer to decoder-only models at scale, and whether the retained heads are causally necessary rather than merely sufficient remains open. At this level of evidence, the findings suggest [metric] is a usable first-pass pruning criterion for resource-constrained deployment, with task-specific fine-tuning still required for production accuracy. The most informative next step is an ablation that re-trains after pruning, which would separate capacity loss from representational redundancy. If the decoder-only boundary can be closed, the criterion could generalize to current production-scale models.
