# Scientifically consequential changes

Not a commit log. An entry belongs here only when a change alters what a number
means: experimental design, prompts, instruction wordings, order or load,
decoding, caps, seeds, verifiers, parsers, answer extraction, metrics, estimators
or interval code, or the admission rules that decide which data an analysis reads.

Refactors, renames, tests, tooling and documentation do not get an entry unless
they change one of those.

Newest first. Started 2026-08-13; earlier history is in `git log`, the per-round
reports under `exploratory/`, and `docs/migration_ledger.csv`.

---

## 2026-08-13 — figure data admission: the guard moved onto the mandatory path

**What changed.** `plotdata.load_all_reasoning` refused the deprecated shared-seed
grid, and four tests enforced that. `make_figures.py::build` never called it: it
called `plotdata.load_reasoning` directly on `s18_reasoning.jsonl` and
concatenated `s18_transition.jsonl`. The admission check now lives in
`load_reasoning` itself, keyed by a `NON_ADMISSIBLE` table mirroring the status
column in `REASONING_DATA_PROVENANCE.md`, with an explicit
`allow_non_admissible=True` opt-in used only to evidence the defect.
`build()` routes through `load_all_reasoning`.

**What measurement changed.** Which rows reach a figure. The previous path mixed
two sampling regimes on one curve:

* `s18_reasoning.jsonl` — DEPRECATED, one shared seed for all 160 requests, so
  390/400 nominal replicate pairs are byte-identical: two draws counted once;
* `s18_transition.jsonl` — FOREIGN, Round 10 transition budgets, 98.4% duplicate
  replicate pairs, already deprecated as curve-shape evidence.

**Which results are affected.** Everything `make_figures.py` wrote:
`reasoning_rows.csv`, `reasoning_cells.csv`, `reasoning_tau_and_delta.csv`,
`reasoning_timing.csv`, and figures fig01–fig18.

A later audit found the identical bypass in a **second** script:
`round10_analysis.py` loaded `s18_reasoning.jsonl` and appended
`s18_transition.jsonl` onto one curve, and writes `round10_s18.csv`. Its S18 cell
now loads `s18_reseeded.jsonl` only and is relabelled `S18 · QAC k=3`, since it no
longer includes the transition budgets. Its sibling cells
(`round10_s25/s26/s27.csv`) glob `*_reasoning.jsonl` inside their own run
directories and were never affected.

**Not** affected: `figure1_headline.*` and the natural-endpoint numbers, which
`make_headline.py` built through the guarded loader all along; the `natural_*.csv`
family; and `natural_analysis.py`, which already loaded `s18_reseeded.jsonl` and
printed a refusal notice for the deprecated grid.

**Comparability.** Old and new are **not** comparable for anything that reads the
capped curve's shape. The observable symptom is that the committed
`reasoning_rows.csv` carries `reasoning_budget` values 320/384/448/640, which a
guarded export cannot contain.

**Current interpretation.** The affected exports are marked
`SUPERSEDED_NOT_REGENERABLE_HERE` in
`exploratory/figures/reasoning_compute/data/PROVENANCE.json`. They are retained,
not deleted, because `runs/` is absent from this checkout and they are the only
surviving copy of the scored rows. Regeneration needs the workstation that holds
`runs/stageS18_reasoning_design_*/`. Point estimates in the seed-corrected
literature were previously reported as surviving the reseeding; the fine
curve-shape claims from the transition budgets were already deprecated
independently, so this change is expected to confirm rather than overturn the
published reading — but that is a prediction until the regeneration runs.

**Evidence.** `exploratory/tests/test_canonical_inputs.py` —
`test_the_raw_loader_itself_refuses_non_admissible_evidence`,
`test_the_figure_builder_uses_the_guarded_loader`, and
`test_no_production_script_names_a_non_admissible_generation_file`, which
generalises the second: it resolves loader call sites by AST across every script,
so a guard asserted at the one call site someone remembered cannot let a second
call site survive — which is exactly how `round10_analysis.py` was missed. It
checks USE, not mention, so a script that names a deprecated file in order to
refuse it does not trip.

---

## 2026-08-13 — figure timing no longer depends on an agent scratchpad

**What changed.** `make_figures.py` copied two driver logs from
`/tmp/claude-1000/-home-cnm13ryan-git-dci/<session-uuid>/scratchpad/` into the run
directory. That path belongs to a coding-agent session on a different host and
does not exist anywhere else. Logs are now read from the run directory only.

**What measurement changed.** Nothing behavioural. The time axis (fig09) and
`reasoning_timing.csv` are reconstructable only where the logs were already
preserved beside the generations; otherwise the timing frame is empty and the
figure is skipped, which the code already handled.

**Evidence.** `test_no_tracked_script_depends_on_an_ephemeral_session_path`.
