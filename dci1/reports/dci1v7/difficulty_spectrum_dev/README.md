# difficulty_spectrum_dev — DEVELOPMENT-ONLY investigation (2026-08-29)

Why C4 fails on every v7 replication and how a future design could obtain a
difficulty spectrum for D(B←R) vs ι(R). **Not evidence about any estimand;
not a v7 amendment; nothing here was run on a GPU.** Read `REPORT.md` first
(§0 answers the fourteen deliverable questions), then `SAFETY_AND_ISOLATION.md`.

| file | what |
|---|---|
| `REPORT.md` | the ten-phase report |
| `SAFETY_AND_ISOLATION.md` | before/after verification that no v7 process, evidence root, registration or GPU job was touched |
| `spectrum_dev.json` | per model: corrected-basis C1–C8, per-rung table, per-family C4 states on four bases with buckets, local vs spectrum support, selected slots |
| `rung_table.csv` | the per-rung table, flat (476 rows) |
| `family_c4_table.csv` | the per-family C4 table, flat |
| `counts/counts_<model>.json` | count distributions S per solo rung (P(S = q), P(S < q), P(S > q), histogram, median words) and the natural count distribution of every Tier-1/2 statistic |
| `counts/wordings_<model>.json` | the same split by the frozen wording index the row drew |
| `wording_sensitivity.json` | per (model, family): mean P(S = q) and P(S = 0) by wording index |
| `robust_wording_ladders.json` | ladders over the robust wordings only, Spearman(q, ι), C4-like state |
| `plots/plotA_landscape_<model>.png` | Plot A — every rung on the ι axis by family, ι_A, caliper, targets, ceiling, signed slots, backups |
| `plots/plotB_ladders_<model>.png` | Plot B — severity → ι per family with ι_A |
| `plots/plotC_wordings_<model>.png` | Plot C — P(S = q) vs q by wording index (the Phase-5 mechanism) |
| `log_analysis.txt`, `counts/log_*.txt` | tool logs |

Inputs (read-only): `/home/cnm13ryan/git/dci/dci1/evidence/dci1v7/<model>/{REGIME_SCREEN,GATE_2_FOCAL_CALIBRATION,GATE_2_5_…,GATE_3A_…,GATE_3B_…,GATE_3C_…}` records and the Gate-2 backend runs' `rows.jsonl` / `scored.jsonl`; the prior session's `../reference_support_landscape/landscape.json` (carried, uncommitted in its worktree of origin).

Tools: `dci1/tools/v7_spectrum_dev_analysis.py`, `v7_spectrum_dev_counts.py`, `v7_spectrum_dev_wordings.py`, `v7_spectrum_dev_wording_summary.py`, `v7_spectrum_dev_plot_wordings.py` (regeneration commands in `REPORT.md`, Appendix). They need `matplotlib`, which is installed only in this worktree's venv.
