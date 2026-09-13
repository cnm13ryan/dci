# Safety and isolation record — difficulty-spectrum investigation, 2026-08-29

Window: 2026-08-29 19:26:34Z (baseline) → 19:49:11Z (final check), UTC.
Baseline and final snapshots live in the session scratchpad
(`…/scratchpad/safety/*.before|after`); the checks below are `diff` results
between them plus the live listings at the end.

## What was verified

| check | method | result |
|---|---|---|
| registered v7 evidence untouched | SHA-256 of all 54 stage-record JSONs under `dci1/evidence/dci1v7/` (depth ≤ 3, incl. `registration/registration_manifest.json`) | **identical** |
| registered v7 row files untouched | size + mtime of all 92 `rows.jsonl` / `scored.jsonl` under `dci1/evidence/dci1v7/` | **identical** |
| durable root untouched | SHA-256 of all 378 files under `dci1/durable_root/dci1v7/` | **identical** |
| completed development roots untouched | SHA-256 of all 134 `*.json` under `dci1v7-development`, `-r2`, `-r3` | **identical** |
| live development root r4 | SHA-256 of its `README.md` and `registration/registration_manifest.json` | **identical**; its stage directories advanced (qwen3-4b-instruct-2507 `MASKED_ANALYSIS` → `FINAL_REPORT`; gemma-3n-e4b-it still in `GATE_2_FOCAL_CALIBRATION`) — written by its own lanes, which were never signalled |
| no v7 process signalled | pid list of `dci1v7.run.cli`, `vllm_backend`, `run_v7_replication.sh` before/after | two pids left the list because their lane **finished** (2834089 = r4 qwen-2507 driver, 2978604 = its `MASKED_ANALYSIS` stage; `FINAL_REPORT` now exists); the gemma-3n-e4b-it r4 lane (2909500 / 2939580 / 2959145, GPU 0) ran throughout; a **new** lane `gemma-3n-e2b-it` on GPU 1 in a new root `dci1v7-development-r5` (pid 2981971) was started by the concurrent rehearsal session, not by this investigation |
| no GPU used by this investigation | `rocm-smi --showpids` / `--showuse` | only the lanes' `VLLM::EngineCore` processes hold VRAM; this investigation ran CPU-only (`nice -n 10`), no `--device` argument was ever passed |
| no registration / freeze / amendment state changed | registered manifest hash identical; `registration/amendments/` unchanged; no `dci1v7 amend`, `register`, `freeze` invoked | **unchanged** |
| fix worktree `dci-v7-chance-fix` untouched | HEAD `7f89dae` and `git status` (two untracked paths) before/after | **identical**; its uncommitted landscape tool/report were *copied* into this worktree, never modified in place |
| main worktree `dci` | HEAD `3ea82b2` → `2a5ae8d`; status `M v7_producer_consumer.md` → clean | **changed by a concurrent session, not by this one**: three commits at 20:28–20:38 local (`a18db3d` producer/consumer regenerated, `473d30c` execution-path audit regenerated, `2a5ae8d` development-rehearsal report). This investigation issued no write, `git add`, commit or checkout in that worktree; it only read `dci1/evidence/…` from it by absolute path and created the new worktree entry in `.git/worktrees/` |

## Where this investigation's outputs live

- worktree `/home/cnm13ryan/git/dci-v7-spectrum-dev/` on branch `dev/v7-difficulty-spectrum` (from `7f89dae`), with its own `dci1/.venv` (uv; `numpy`, `matplotlib`, editable `dci1`) — no shared venv was modified;
- `dci1/reports/dci1v7/difficulty_spectrum_dev/` (this directory) and the five `dci1/tools/v7_spectrum_dev_*.py` tools;
- `dci1/reports/dci1v7/reference_support_landscape/` and `dci1/tools/v7_reference_support_landscape.py`, carried from the fix worktree as inputs;
- the session scratchpad (`safety/` snapshots, a schema-dump helper).

Nothing was written under `/home/cnm13ryan/git/dci/`, `/home/cnm13ryan/git/dci-v7-chance-fix/`, any `dci1/evidence/*` root, or `dci1/durable_root/`.

## Constraints honoured

- no process stopped, restarted or killed; no `kill`, `pkill`, `TaskStop`;
- no GPU generation; both cards were busy (GPU 0 gemma-e4b r4, GPU 1 qwen-2507 r4 then gemma-e2b r5) and were not used;
- v7 not amended, frozen, registered or re-run; no v8 registration created;
- all v7 evidence treated as read-only input; development-root READMEs unmodified.
