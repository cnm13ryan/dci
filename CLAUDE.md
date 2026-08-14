# Working in this repository

Start at [`RESEARCH_STATE.md`](RESEARCH_STATE.md). It is the 10-minute
orientation and it links to everything else.

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
