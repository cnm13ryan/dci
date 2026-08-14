# Experiment families

What exists in `exploratory/`, what each family asked, and where its code,
evidence and report are. The directory is flat and the family is encoded in the
filename prefix; this is the key.

Status words: **supported** (survived its own audits within its stated scope) ·
**tentative** · **weakened** · **open** · **blocked** · **void** (the
manipulation failed its check, so the estimate says nothing).

All of it is stamped `EXPLORATORY_NO_EVIDENCE`: ~20 pilot tasks, uncorrected
task-cluster bootstrap intervals, designs chosen adaptively between rounds. The
preregistered instrument is `src/dci/`, and no number here carries its guarantees.

| # | Family | Question | Entrypoints | Analysis | Report | Status |
|---|---|---|---|---|---|---|
| 1 | **Main probe** | Does replacing a comparable reference with B cost compliance with A? | `python -m dci_exploratory.experiment` | `dci_exploratory/analysis.py`, `verify_independently.py` | `README.md`, `FINDINGS.md`, `HYPOTHESES.md` | supported (effect real; **not** specific to the registered pair) |
| 2 | **Dose, scope, marks** | What property of an added instruction triggers the failure? | `qn_phase.py`, `factorial_bxc.py`, `nsweep.py`, `colon_property.py`, `background_sensitivity.py` | `e7_table.py` | `ROUND5_REPORT.md`, `COLON_AMPLIFIER_MATRIX.md`, `AMPLIFIER_MECHANISM_MATRIX.md` | supported (absolute dose threshold; scope is protective, not costly) |
| 3 | **Order and load** | Does presentation order change the effect, and does it transport to higher load? | `stage1_decoding.py`, `stage2_orderings.py`, `placement.py` | `coverage.py` → `EXPERIMENT_COVERAGE_MATRIX.md` | `CLAIM_EVIDENCE_MATRIX.md` | supported (order spans sign reversal); no simple positional rule |
| 4 | **Reasoning compute** | Does test-time reasoning remove the interference? | `vllm_backend/*.py`, `reasoning_score.py`, `natural_analysis.py` | `make_headline.py` (guarded), `make_figures.py`, `natural_figures.py` | `REASONING_COMPUTE_MATRIX.md`, `NATURAL_REASONING_RESULTS.md` | supported at the natural endpoint; **capped-curve exports superseded** — see `figures/reasoning_compute/data/PROVENANCE.json` |
| 5 | **Mechanism / boundary** | Is it clause-boundary affordance? | `mfr_preflight.py`, `mfr_preflight_design.py`, `mfr_boundary.py` | `mfr_figures.py` | `BOUNDARY_MECHANISM_REPORT.md` | supported predictively, not causally closed |
| 6 | **Focal ladder** | Does an easier focal create a real trade-off region? | `mfr_focal_design.py`, `mfr_focal_calibration.py` | — | `MECHANISM_AND_FOCAL_REPAIR_REPORT.md`, `NONDEGENERATE_FOCAL_CALIBRATION.md` | informative null — the pair has no trade-off region under the control background |
| 7 | **Splice intervention** | Does prohibiting the splice remove the amplification? | `ssi_preflight.py`, `ssi_design.py` | `ssi_figures.py` | `SEMICOLON_SPLICE_INTERVENTION_REPORT.md` | **void** — `ANTI_SPLICE_MANIPULATION_FAILED`; the instrument does not work |
| 8 | **Arbitration** | What does reasoning actually buy — the target, or the composition? | `arb_smoke_design.py`, `arb_priority_design.py`, `arb_exp1..3.py` | `arb_score.py`, `arb_verify.py`, `arb_figures.py` | `ROUND11_ARBITRATION_REPORT.md` | supported — reasoning re-prioritises; explicit priority cues do not control it |
| 9 | **Cross-model** | Does any of it transport to other checkpoints? | `crossmodel/`, `xm_run.py`, `xm_qualify.py`, `xm_kimi_run.py` | `xm_actual_results.py`, `xm_analysis.py`, `xm_verify_independently.py` | `ACTUAL_CROSS_MODEL_DCI_RESULTS.md`, `CROSS_MODEL_EXECUTION_MATRIX.md` | mostly **structural zeros** — the target saturates, so τ is unformable at this operating point |
| 10 | **Cross-model on vLLM** | Same five checkpoints without the backend confound | `xm_vllm_plan.py`, `xm_vllm_run.py`, `xm_vllm_smoke.py` | `xm_vllm_matrix.py`, `xm_vllm_compare.py` | `CROSS_MODEL_VLLM_TP2_*.md`, `ROOT_CAUSE_ANALYSIS.md` | **blocked/open** — the qualification gate passed 0/5, for three different reasons |
| 11 | **Measurement validation** | Do the instruments measure what they claim? | `verifier_audit.py`, `stress_corpus.py`, `independent_segmenter.py` | `reliability_and_rescore.py`, `abbrev_impact.py`, `metric_bugdiff.py` | `METRIC_SPEC.md`, `verifier_audit/` | supported — this family repeatedly caught the others |

## Cross-cutting tooling (not an experiment)

| Script | Job |
|---|---|
| `coverage.py` | Rebuilds the coverage matrix **from run configs**, because the write-ups are what is being audited |
| `seed_check.py` | Replicate independence — a byte-identical replicate pair is one draw counted twice |
| `reasoning_provenance.py` | Classifies every generation file `CANONICAL` / `DERIVED` / `DEPRECATED` / `FOREIGN` |
| `xm_manifest.py` | Cross-model run manifests: hashes, row identity, canonical status |
| `verify_independently.py` | Recomputes every headline from `generations.jsonl` alone |
| `reanalysis_standalone.py` | A second, fully independent reanalysis of every headline from the raw artifacts |
| `promote_evidence.py` | Moves a run out of ephemeral `runs/` into committed `evidence/` |
| `satisfiability_certificate.py` | Certifies that A ∧ B ∧ background is jointly satisfiable **without** using model success — so joint failure reads as a choice, not an impossible specification |
| `strategy_check.py` | Checks `splice_share` is outcome-*independent*; a mediator that is a function of the outcome manufactures its own correlation |
| `audit_chain.py` | Draws the stratified reproducible sample for the human read of `chain_share` |
| `inspect_raw.py` | Prints raw generations for a human to read — no classifier, no judge |
| `round10_analysis.py` | Round 10 scoring, generalised over (amplifier, control) pairs |

## Reading order

New to the project: `README.md` → `FINDINGS.md` → `CLAIM_EVIDENCE_MATRIX.md`.
Returning after a break: `../RESEARCH_STATE.md`, then `../CHANGES_SCIENTIFIC.md`.

## Why this file rather than directories

The flat layout has not been the source of any recorded failure — the failures
were seeds, caps, parsers, admission rules and shared definitions. Grouping 49
scripts into family directories would rewrite every documented invocation path in
eleven reports to fix a problem an index solves. Revisit if a family grows its
own package, or if two families start needing the same helper.
