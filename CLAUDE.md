# Working in this repository

Start at [`RESEARCH_STATE.md`](RESEARCH_STATE.md). It is the 10-minute
orientation and it links to everything else.

## Research codebase principles

- Optimize for research velocity, reproducibility, and scientific legibility rather than production-software cleanliness.
- Inspect the relevant execution, evidence, and dependency paths before making consequential changes.
- Keep exploratory code easy to change, replace, and break. Do not preserve obsolete experimental interfaces for compatibility alone.
- Treat governed or frozen protocol code separately from exploratory code. Do not silently change reviewed scientific definitions or artifacts.
- Preserve important results through durable, self-describing evidence rather than through permanent source-code compatibility.
- When a result becomes scientifically important, ensure its configuration, protocol identity, execution condition, outputs, producing code, and provenance remain recoverable.
- Never allow implementation changes to silently change what existing evidence means. Identify the affected results and their comparability explicitly.
- Treat changes to verifiers, parsers, prompts, metrics, sampling, configuration, model loading, or inference behaviour as potentially scientifically consequential.
- Prefer experiment-local code and configuration until repeated reuse, repeated bugs, or a stable semantic boundary justifies extraction.
- Keep shared infrastructure small and narrow. Do not introduce universal experiment frameworks, giant configuration objects, or speculative abstractions.
- Put important invariants on mandatory execution paths and enforce them with tests or assertions rather than relying on documentation.
- Treat agent-produced results as provisional until load-bearing claims have been checked against raw outputs or independently recomputed.
- Produce machine-readable intermediate results for important analyses. Avoid relying on terminal output or manually transcribed numbers as evidence.
- Preserve historical observations and evidence when interpretations change. Record supersession, invalidation, or non-comparability rather than rewriting history.
- Keep the researcher-facing current-state documentation updated when a change materially alters the scientific picture, while linking to evidence rather than duplicating it.
- Prefer small, independently testable migrations and refactors over large rewrites. Refactor in response to demonstrated friction.

## Two areas, different expectations

- **`src/dci/`, `configs/`, `notebook_source/`** — the preregistered protocol.
  Changes here are amendments, and the frozen artifacts refuse values the running
  code cannot reproduce. When a legitimate amendment makes them stale, regenerate
  with `tools/refreeze_stage2.py` and `tools/generate_review_packets.py` rather
  than editing the JSON.
- **`exploratory/`** — fast, cheap, breakable. Redesign freely; breaking an
  exploratory interface is expected and needs no deprecation path.

`exploratory/dci_exploratory/harvest.py` executes confirmatory stages at runtime
to get constraint definitions, wordings, verifiers and the task bank. So a change
in `src/dci/` changes what exploratory designs and rescores mean, in both
directions, even though nothing in the directory tree shows it.

## Evidence

`runs/` is gitignored and does not survive a clone. A run that a durable claim
rests on must be promoted into `exploratory/evidence/` — see the README there.
An unpromoted run is fine; a cited unpromoted run is a broken citation.

Never edit a run directory in place, and never regenerate a committed derived
artifact by hand when a script produces it.

## Consequential changes

A change to verifiers, parsers, prompts, wordings, design, decoding, caps, seeds,
metrics, estimators, or the rules deciding which data an analysis reads is a
change to what existing numbers mean. Add an entry to
[`CHANGES_SCIENTIFIC.md`](CHANGES_SCIENTIFIC.md) saying what changed, which
results are affected, and whether old and new stay comparable — and update
`RESEARCH_STATE.md` if it moves the picture. Ordinary refactors and tooling do
not get an entry.

## Tests

Run them; both suites are CPU-only and take about two minutes together. A red
test is a finding — investigate before changing it. Two fixtures in this
repository had encoded a defect as expected behaviour, and correcting the code
required correcting them; that is different from relaxing an assertion to get
green, and the difference is whether the certified reference implementation
agrees.

The safeguards are already executable — seed regime, canonical-evidence
admission, metric spec, verifier audit, manifest identity. Reuse them and put new
ones on the path the production code actually takes, not beside it. Do not
restate them here.
