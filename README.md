# DCI — Directional Constraint Interference

## Repository map

This repository holds three studies that share a root but not code, plus the
manuscript. For the current scientific picture start at
[`RESEARCH_STATE.md`](RESEARCH_STATE.md); for working rules, `CLAUDE.md`.

| study | status | folders |
|---|---|---|
| **DCI-1** (the active line) | v8.1 frozen 2026-09-08, confirmatory analysis run 2026-09-10 | `dci1/` — preregistration and design docs in `dci1/docs/`, code in `dci1/src/dci1v<N>/` (one package per revision; v8 imports from `dci1v4` and `dci1v7`, so older revisions are live dependencies — map in [`dci1/src/README.md`](dci1/src/README.md)), results in `dci1/reports/`. Raw evidence (`dci1/evidence/`) is gitignored and lives on the workstation. |
| **v15/v19 protocol** | paused; confirmatory run not executed | `src/dci/`, `configs/`, `notebook_source/`, `tests/`, `docs/`, `tools/`, `scripts/` (incl. Lambda tooling), `environments/` — the rest of this README |
| **exploratory** | eleven rounds complete | `exploratory/` — index in [`exploratory/EXPERIMENTS.md`](exploratory/EXPERIMENTS.md) |

Also here:

- `manuscript/` — paper-writing documents for DCI-1 v8.1 (rewrite bundle,
  change brief, upstream agent prompt, executive summary). `paper/` is a
  different, gitignored build output.
- `user-notes/` — earlier DCI-1 preregistrations (v2–v7) and planning notes,
  indexed in [`user-notes/README.md`](user-notes/README.md). Files marked
  *pinned* there are cited by path from `dci1` code; do not move them.
- `autorater_forensics/` — standalone Inspect AI diagnosis of the DCI-1 Gate 1
  autorater; read-only with respect to registered evidence.
- `.provenance/` — pre-repair snapshot of the v15 source and tests.
- `CHANGES_SCIENTIFIC.md` — log of every change to what results mean.
- `docs/history/research_state_log.md` — the dated study log (§4c–§4ao) moved
  verbatim out of `RESEARCH_STATE.md`; citations by section number still apply.

## v15/v19 protocol package (`src/dci/`)

`src/dci/` is the authoritative implementation of the DCI v15 protocol,
extracted from the validated Colab notebook with **demonstrated behavioral
equivalence** (every Gate 0 self-test passes - the inventory lives in
`tests/regression/gate0_registry.py`; the frozen no-bypass `integration_pass`
baseline; 38 deterministic artifacts byte-identical to the notebook fixture
after volatile-field stripping). The notebook cells are archived under
`notebook_source/`; no second implementation of the pipeline exists.

To audit any stage against the cell it came from, diff
`src/dci/pipeline/stages/<stage>.py` against `notebook_source/cells/<n>.py`; the
eleven ledgered execution-only exceptions (`P0`-`P10`) are listed in
`docs/migration_ledger_patches.csv`, beside one later scientific verifier repair
(`P13-sentence-abbreviations`) that is outside the byte-identity boundary.
`tools/migrate_v15.py` reconstructs the v15 package from the archive into
`build/v15_reconstruction/` — it never writes over `src/`, which is the
authoritative repaired implementation and is not what the archive contains.

The scientific protocol is v15, unchanged: six individually defensible
references valid in both orders, the full 6×2 τ matrix with both orders
co-primary, the two nested estimands (`primary_total`, `kappa_matched`), the
joint reference-error certificate, lineage-independent pseudo-focal
validation, and the full gate/status taxonomy. `docs/MIGRATION.md` carries the
source audit, risk table, reproducibility report and open blockers;
`docs/migration_ledger.csv` records every substantive change.

## Layout

    src/dci/                 the package (see docs/MIGRATION.md for the map)
      pipeline/stages/       33 stage modules == the 33 notebook cells
      pipeline/state.py      the explicit shared run state (S.<name>)
      inference/             backend seam: oracle (dry run) + hf_transformers
      verifiers/ analysis/ … extracted pure libraries (84 defs, unit-tested)
    configs/profiles/        dev_fast, dev_fast_gpu, integration_pass, pilot, study
    environments/rocm|cuda/  the two GPU stacks — separate projects; torch (and on
                             ROCm its wheel set) is pinned, the HF libraries are
                             lower-bounded and their versions are recorded per
                             run; locks are generated on the target machine
    scripts/                 environment doctors + Lambda provisioning tooling
    tests/                   unit / integration / regression / hardware
    notebook_source/         the archived v15 cells + build harness (read-only)
    tools/migrate_v15.py     rebuilds the v15 package FROM that archive

## Local runbook (clean checkout → tests → dev_fast)

    # CPU tier (any machine; no GPU stack):
    pip install -e . && pip install pytest
    dci doctor                       # exit 0 = supported
    dci test                         # unit + fast integration (CPU markers)
    dci validate --profile integration_pass    # no-bypass baseline, exit 0
    dci run --profile dev_fast --data-root ~/dci-artifacts     # full dry run

    # Workstation GPU tier (2x RX 7900 XTX, ROCm):
    cd environments/rocm && uv sync && cd ../..
    uv run --project environments/rocm dci doctor --gpu --expect-devices 2
    uv run --project environments/rocm dci run --profile dev_fast_gpu --device 0 \
        --data-root ~/dci-artifacts          # real 0.5B smoke, DEVELOPMENT_ONLY

    # two-GPU workers (deterministic sharding; both share one --run-id):
    uv run --project environments/rocm dci run --profile dev_fast_gpu \
        --device 0 --shard 0/2 --run-id smoke1 --data-root ~/dci-artifacts &
    uv run --project environments/rocm dci run --profile dev_fast_gpu \
        --device 1 --shard 1/2 --run-id smoke1 --data-root ~/dci-artifacts

Local profiles are non-evidence by construction (`DEVELOPMENT_ONLY`,
`SYNTHETIC_NO_EVIDENCE`); the hardware class they freeze can never resume on
Lambda, and the package refuses the attempt (`HARDWARE_CLASS_MISMATCH`).

## Lambda runbook (preflight → run → collect → terminate)

Two arguments have no default on purpose. `--data-root` and `--remote` must both
name the SAME persistent filesystem path: the instance root disk is erased on
termination, and a plausible-but-wrong default is how a run gets collected from
the wrong tree, verified as empty, and then deleted.

    export LAMBDA_API_KEY=...        # read -rsp; never in the repo
    export LAMBDA_REGION=...  LAMBDA_SSH_KEY_NAME=...
    export DCI_DATA_ROOT=/lambda/nfs/<fs>/dci        # the persistent root
    python scripts/lambda_cloud.py doctor --instance-type gpu_1x_a10 \
        --region "$LAMBDA_REGION" --ssh-key-name "$LAMBDA_SSH_KEY_NAME"
    python scripts/lambda_cloud.py launch ...            # dry-run: prints JSON
    python scripts/lambda_cloud.py launch ... --state-file .lambda/instance.json --execute
    python scripts/lambda_cloud.py wait --instance-id $ID > .lambda/active.json
    bash scripts/lambda_upload.sh --host $IP --key $SSH_KEY
    ssh ubuntu@$IP  "cd dci && bash scripts/lambda_bootstrap.sh \
        --data-root $DCI_DATA_ROOT"                      # doctor + tests
    ssh ubuntu@$IP  "cd dci && tmux new -d -s dci \
        'dci run --profile pilot --data-root $DCI_DATA_ROOT --execute'"
    bash scripts/lambda_collect.sh --host $IP --key $SSH_KEY \
        --remote $DCI_DATA_ROOT --destination lambda-results
    python scripts/lambda_cloud.py terminate --instance-id $ID          # review
    python scripts/lambda_cloud.py terminate --instance-id $ID --execute
    python scripts/lambda_cloud.py instances                            # empty

Rules the tooling enforces or the runbook requires: dry-run by default and
`--execute` for anything billable or destructive; no GPU-SKU substitution
(capacity gaps are reported); collection fails closed unless at least one
manifest was found, at least one entry was checked, and every declared artifact
matched its recorded hash — so nothing can report that termination is safe
without having verified something; environment provenance written to the
persistent root, not the root disk; terminate through the API, never
`shutdown`/`poweroff` (Lambda documents billing can continue in Alert status); a
cloud run starts from a clean state and never imports a generation cache from
another hardware class.

## Failure taxonomy

Exit 0 completed · **10 scientific stop** (a gate returned its status; the
artifacts and `stop.json` stand — `NOT_IDENTIFIED_SUPPORT` is an experimental
outcome, not a crash) · 20 implementation-invariant failure · 30 environment ·
1 unexpected crash.
