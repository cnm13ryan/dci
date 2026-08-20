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

## 2026-08-19 — DCI-1 v4: a fresh study, and two findings that move v4r2's own numbers

**What changed.** A complete implementation of `DCI1_preregistration_v4r2.md`
under `dci1/src/dci1v4/`, isolated from v2, v3 and the B+R pilot: its own
namespace, its own evidence and durable roots, its own root seeds and
`dci1v4:` domain strings, its own 624-topic bank, and no scientific import of
any earlier DCI module. The protocol is **not frozen** and no confirmatory
generation has run; Gate 5 and confirmatory generation are implemented and
refuse to execute.

**What measurement changed for v4.** Everything, relative to v3, because v4r2
is a different protocol: the primitive is the per-constraint compliance vector
rather than target failure; the outcome scale is compliance rather than
failure; references are matched to **A** on solo compliance rather than to B on
solo failure; order is a cell-level factor; all M draws enter the cell mean and
no draw selector exists; a composed generation yields two observations. None of
this reinterprets a v3 number: v3's evidence tree is untouched and v4 reads it
only as design evidence, through one guarded door that stamps every result
non-confirmatory.

**What measurement changed for v4r2's registered constants.** Two pre-freeze
checks produced figures that differ from the ones v4r2 carries, and both bear
on decisions the researcher has not yet made.

* **C6, the companion-difficulty anchor.** v4r2 §13.1 and the change summary
  report the reference-minus-A solo gap as +0.198 (E2B) and +0.210 (E4B),
  taking `P(A solo)` from the v3 confirmatory target-alone arm and the
  reference rates from the Gate 2A cells on a different topic set. Reading
  `solo:A:<n*>` from the Gate 2A cache instead puts A and every reference on
  the same 96 topics and the same estimator, which is what C6 asks for, and
  the gap is **+0.164 (E2B) and +0.101 (E4B)**. Only 4 of 32 measured rungs
  sit within the registered 0.10 caliper of A on the v3 four-point grid.
* **C12, the allocation.** §16.1 registers phi = 0.27 under an assumed
  among-reference correlation of 1 and phi ~ 0.37 under 0.5, both fitted to
  the pilot's reported interval widths. Estimated directly from the pilot rows
  on the outcome the design uses — B re-scored under the v4 instrument at the
  pilot's own m\* — the among-reference correlation is **0.72** and phi is
  **0.556 (E2B) and 0.441 (E4B)** pooled. Pooled phi carries the pilot's
  order variance, which the v4 design cannot have because order is
  within-block; estimated inside each order stratum it is **0.395**. At 0.395
  the registered 384 blocks at M = 4 still meets every precision precondition,
  by 0.0008 on the half-width of D. At phi = 0.44 it stops qualifying and the
  registered menu rule moves to 480 blocks at M = 4, 48,000 generations per
  model.

**Which results are affected.** No existing result. v3's evidence, its records
and its reported numbers are unchanged and unreinterpreted; the B+R pilot's
rows are unchanged and were re-scored from raw text under the current v4
instrument with agreement 1.000 against its recorded verdicts (C13). What the
two findings affect is prospective: the feasibility of the §13.2 caliper (C7)
and the choice of allocation (V1), both of which are still open.

**Comparability.** v3 and v4 numbers are not comparable and are never compared:
different estimands, different outcome scale, different topics, different
instrument population, different design. C18 confirms the one algebraic bridge
that does exist — v4's demoted Delta^A reproduces v3's recorded
`secondary.pooled_swap_effect` exactly from the v3 rows, at -0.009548611 and
+0.065104167 — and confirms the compliance/failure identity that makes the
demotion argument rest on rows rather than on a summary.

**A third finding, from the real-model screens, in four of four replications.**
All four registered models completed QUALIFIED, GATE_0_APPARATUS and
REGIME_SCREEN; each selected cap 512; 15,264 real generations in total.

The dense ladder **does** reach A: five or six of the eight families carry a
rung within the 0.10 caliper in every model, against 4 of 32 rungs on the v3
four-point grid. But **not one of the 64 matched rungs across the four models
survives §13.2's family-solo-vacuity condition** — 13, 9, 24 and 18 matched
rungs, zero surviving in each case, leaving zero viable families everywhere.

The mechanism is structural rather than incidental, and it is measured on
identical prompts: unconstrained, gemma-3n-E2B-it writes 329 words and
Qwen3-4B writes 282; with one constraint, 121 and 49; with two, 80 and 25. A's
solo compliance is low, so matching it needs a restrictive "at most q"; a
restrictive budget constraint is satisfied by writing a shorter answer; and a
shorter answer makes the pass vacuous. Of the 4,873 vacuous passes across the
four screens, **seven** were truncations. §13.2 condition 1 and condition 6
pull against each other by construction.

§13.2 is evaluated at Gate 2 on 96 topics at M = 4, not on these screening
samples, so this is not an admission decision. It is decision-relevant for V3
(the caliper), V4 (the 20-word threshold, whose §9.3 justification — a topic
space asking for sixty to one hundred and twenty word answers — holds
unconstrained and does not describe what any of the four models produces once a
constraint is present) and V5 (difficulty-spanning references would not need
the reference to be as hard as A). It is reported rather than resolved. If it
holds at Gate 2, every replication takes the §8.6 reduced design with
`EXCESS_NOT_IDENTIFIED` and L3 — the study's headline claim level — is withheld
in all four.

**A fourth finding: two Qwen grid boundaries.** Neither Qwen model's operating
regime existed anywhere in the corpus. Qwen3-4B is squeezed at both edges of
the registered grids — n\* would be 1, the floor, and m\* would be 10, the
ceiling and the only eligible value, its B curve reading 0.25 / 0.58 / 0.54 /
0.75 against a [0.60, 0.95] band. A small shift at Gate 2 puts it into
`TARGET_RANGE_EXHAUSTED` or `FOCAL_RANGE_EXHAUSTED`, which are statements about
the registered grid and never about the model. Qwen3-4B-Instruct-2507 is the
mirror image on the A side, 0.92 at both n = 1 and n = 2 falling to 0.12 by
n = 8. The thinking-disabled path was validated on real data: zero
`<think>`/`</think>` leakage in 1,200 Qwen3-4B pilot draws.

**The same screen also measures trap T-7.** At cap 512 the constrained
truncation rate is 0.028 and the zero-constraint rate is 0.917. Had the
zero-constraint prompts entered the cap criterion, no registered cap would have
qualified (0.250 even at 1024) and the replication would have terminated
`RESPONSE_LENGTH_INCOMPATIBLE` before measuring anything.

**Evidence.** `dci1/docs/v4_prefreeze/` (one JSON per check, C1 to C20),
`docs/v4_traceability.md`, `dci1/tests_v4/` (324 tests: T1 to T14 plus the
anti-regression group), and the signed v4 records under
`dci1/evidence/dci1-v4/`.

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

## 2026-08-20 — durable replication moved to the stage exit (operational)

**What changed.** `engine/dispatch.run_stage` now replicates to
`durable_root/` *after* the signed stage record and its transition-log entry
are written, and verifies the copy with `store.assert_replicated`. The stage
bodies replicated before returning, so the record itself — written afterwards
by the dispatcher — was the one file guaranteed not to be mirrored.
`stages/registration.register` likewise now mirrors the manifest.

**Which results are affected.** None numerically. Four `regime_screen.json`
records, the registration manifest, four transition logs and three backend logs
had no current second copy; the mirror has been completed and verified
(157 files, `assert_replicated` passes). No evidence content changed — the
missing files were copied, not regenerated.

**Comparability.** Old and new remain fully comparable. This is a durability
defect in replication ordering, not a change to what any number means.

**Also.** `generation/backend.run_backend` now starts the backend in its own
process group with `PR_SET_PDEATHSIG`, and tears the group down on every exit
path. Three `vllm_backend` parents had survived their driver by twelve hours.
No effect on generated content: the backend binary, plan and seeds are unchanged.
