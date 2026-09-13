# v8 development candidate — reports (read-only over stored evidence; development numbers)

| file | produced by | what |
|---|---|---|
| `wording_audit.{json,md}` | `tools/v8_wording_audit.py` | per (replication, family, severity, wording) exact-count compliance, zero-marker share, over/undershoot; flagged frames; MK ladders on all frames vs the robust subset |
| `wording_simulation.json` | `dci1v8dev.simulate_wording` | detection of absent-marker frames; apparent vs repaired span; truly flat stays flat |
| `severity_range_audit.{json,md}` | `tools/v8_severity_range_audit.py` | severity needed to reach ι_A − 0.15 per family and model; reserve sufficiency |
| `spectrum_precision.{json,md}` | `tools/v8_spectrum_precision.py` | per-point SE and block correlation from a completed root; SE(β̂)/SE(δ_diff) projections; MC check |
| `spectrum_backtest.{json,md}` | `tools/v8_spectrum_backtest.py` | folded vs unfolded stability, spectrum-valid pools, the new selection and coverage, admissible backups on 12 replications |
| `spectrum_scenarios.{json,md}` | `tools/v8_spectrum_scenarios.py` | constructed pools: local-not-spectrum, spectrum-without-old-C4, extreme-stable survives, degenerate rejected, reserve recovers a side |
| `simulation.{json,md}` | `tools/v8_prescreen_simulation.py` | operating characteristics of the legacy certificate and the new screen on eight archetypes; prospective threshold choice |
| `backtest.{json,md}`, `failure_table.md` | `tools/v8_prescreen_backtest.py` | pre-screen vs calibration per family on 12 replications; failure causes; metrics; emulated second pass; LOMO (retrospective) |

| `backtest.{json,md}`, `failure_table.md` (regenerated 2026-08-29 evening) | `tools/v8_prescreen_backtest.py --chance-cache ../chance_basis` | as above, on the §13.2 chance basis (Gate-2 tables and the pre-screen table), with the retention-recovery and local-recovery-detail sections |
| `../chance_basis/*.json` | `tools/v8_chance_basis_cache.py` | per replication: every candidate's chance compliance on the unconstrained cell, per split and pooled, for Gate 2 and for the regime screen |
| `../coverage_simulation.{json,md}` | `tools/v8_coverage_simulation.py` | the coverage gate's operating characteristics and the prospective threshold choice |
| `../pipeline_validation.{json,md}` | `tools/v8_pipeline_validation.py` | the candidate pipeline end to end on synthetic worlds, the invariances, and a gather of every retrospective replay |

Design of record: `dci1/docs/V8_CANDIDATE.md` (this directory's first design note, `dci1/docs/v8_prescreen_spectrum_redesign.md`, is superseded). Every `.json` here whose `chance_basis` says "corrected" was regenerated on the §13.2 basis; the wording, severity-range and precision audits do not read the chance column.
