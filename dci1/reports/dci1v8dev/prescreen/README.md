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

Design note: `dci1/docs/v8_prescreen_spectrum_redesign.md`.
