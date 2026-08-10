# DCI — Directional Constraint Interference (v15 protocol, portable implementation)

This repository is the authoritative implementation of the DCI v15 protocol,
extracted from the validated Colab notebook with **demonstrated behavioral
equivalence** (every Gate 0 self-test passes - the inventory lives in
`tests/regression/gate0_registry.py`; the frozen no-bypass `integration_pass`
baseline; 38 deterministic artifacts byte-identical to the notebook fixture
after volatile-field stripping). No second implementation of the pipeline
exists.

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
    environments/rocm|cuda/  the two GPU stacks — separate projects, separate locks
    tests/                   unit / integration / regression / hardware

The operational tooling tree and the read-only notebook archive are added by the
two changes that follow this one in the stack, and are documented there rather
than here: a path is described in the snapshot that contains it.

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

## Lambda runbook

Documented alongside the tooling it invokes, which arrives later in this stack.

## Failure taxonomy

Exit 0 completed · **10 scientific stop** (a gate returned its status; the
artifacts and `stop.json` stand — `NOT_IDENTIFIED_SUPPORT` is an experimental
outcome, not a crash) · 20 implementation-invariant failure · 30 environment ·
1 unexpected crash.
