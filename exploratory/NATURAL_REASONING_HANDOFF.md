# Handoff — `exp/natural-reasoning-headline`

## Starting point

Pinned base **`3fb03ad16b33c3366fa3bd1984d5fc7b304f9d86`**, branched explicitly
from that SHA into an isolated worktree at
`/home/cnm13ryan/git/dci-natural-reasoning-headline`. Baseline at that commit:
85 tests passing, plot QA passing.

## Final branch tip

**`4709a38df47f651f2b3b74070a567b75519c1098`** — clean tree.

## Commits introduced

| SHA | purpose |
|---|---|
| `78c2843` | prefer the re-seeded capped grid over the shared-seed one |
| `404546a` | record the natural-reasoning endpoint and the 4096 audit |
| `e839b16` | plain-language Figure 1 with a natural-reasoning endpoint |
| `94cf78c` | canonical reasoning data, classified by measurement |
| `20e6a14` | finalize Figure 1; robustness, outcome and technical panels |
| `b7b324c` | canonical natural-reasoning results |
| `4709a38` | mark the shared-seed grid deprecated, the re-seeded grid canonical |

## Canonical scientific result

Two prompts differ by one phrase — *"use exactly 1 pair of round brackets"*
against *"use exactly 1 semicolon"*. Everything else is identical.

When the model is **allowed to finish thinking on its own**, the bracket prompt's
conflict is gone completely: the competing instruction causes **exactly zero**
extra failures on "write exactly 4 sentences", in all 20 tasks. The semicolon
prompt still costs **+0.400 [+0.225, +0.551]**.

| condition | no thinking | natural reasoning |
|---|---|---|
| + one bracket pair | +0.450 [+0.275, +0.625] | **0.000 [0.000, 0.000]** |
| + one semicolon | +0.525 [+0.350, +0.676] | **+0.400 [+0.225, +0.551]** |

Natural reasoning used a median of **511** tokens with a maximum of **5,888**,
against an engineering ceiling of 39,550 that **0/160** rows reached.

What extra reasoning buys is *which* instruction survives, not joint success:
"both satisfied" reaches only 7.5% even in the repaired condition, and under the
semicolon instruction 45% of answers satisfy neither.

## Canonical data, and what it supersedes

| file | status |
|---|---|
| `s18_reseeded.jsonl` | **CANONICAL** capped grid — supersedes `s18_reasoning.jsonl` |
| `natural_reasoning.jsonl` | **CANONICAL** natural endpoint |
| `s18_reasoning.jsonl` | **DEPRECATED** — 390/400 replicate pairs identical (shared seed). Retained, refused by the loader. |
| `s18_transition.jsonl`, `s18_seedfix.jsonl` | **FOREIGN** — the other branch's work, not used here. The transition file measures 98.4% duplicate replicates. |

`exploratory/runs/` is gitignored, so the analysis input is pinned by
`CANONICAL_RUN_MANIFEST.json` (SHA-256, row counts, sampling regime per file) and
described in `REASONING_DATA_PROVENANCE.md`.

## Figures

* **Figure 1** — `figure1_headline.{png,pdf,svg}`, plus a 7-inch
  deployment-size variant.
* Supporting — `fig15_natural_reasoning_length` (how long it thought),
  `fig16_robustness`, `fig17_what_the_model_did`,
  `fig18_technical_companion` (the project's own notation).
* Design record — `prototype_A/B/C`, kept unfixed.
* Captions — `FIGURE_CAPTIONS_PLAIN_LANGUAGE.md`; test record —
  `COLD_READER_TEST.md`; design reasoning — `HEADLINE_FIGURE_RATIONALE.md`.

## Validity

* 85 tests pass; `make_figures.py` QA passes; `natural_analysis.py` — **22 guards,
  all pass**; `reasoning_provenance.py` exits clean.
* Seed audit: 0/80 natural and 0/400 capped replicate pairs identical, against
  390/400 before the fix.
* Ceiling audit: 0/160, all 160 closed naturally, 0 empty, 0 truncated.
* Leakage audit: 2/160 detector hits, both inspected, **both benign** — confirmed
  leakage 0/160. The detector's `\bwait\b` pattern over-flags ordinary prose.
* Robustness: leave-one-task-out never changes sign; dropping the longest 10% of
  traces in each arm moves the estimate from +0.400 to +0.472, on 18 of the 20
  tasks (SCIENTIFIC_CLAIM_AUDIT.md §1.5 has the per-arm repair).

## Deliberately not done here

Owned by the original experimental worktree: what property of the semicolon
instruction produces the effect, other punctuation marks, other instruction
orders, higher compositional load, other model families, and the Round 10
transition-budget line of work.

## Integration instructions

**Recommended: cherry-pick, not merge.** The branch is seven commits on top of
`3fb03ad`, and the original worktree has moved on independently since. Three of
the seven are self-contained and safe to take in any order:

* `94cf78c` (provenance and canonical analysis) — new files only.
* `b7b324c` (results document) — new file only.
* `20e6a14` (figures) — touches `make_headline.py` and the figure directory.

Two will conflict if the other branch has edited the same files:

* `78c2843` touches `dci_exploratory/plotdata.py`.
* `4709a38` and `404546a` append to `DECISIONS.md` and
  `REASONING_COMPUTE_MATRIX.md`, which the other branch also appends to.
  Take the appended sections, not the file wholesale.

**One thing to check before integrating:** the other branch's canonical documents
may still present the shared-seed capped grid as current. If so, that supersession
needs applying there too — the deprecation is a property of the data, not of this
branch.

No merge has been performed. The original worktree was not modified.
