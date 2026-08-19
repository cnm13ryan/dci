# Promoted evidence

`runs/` is gitignored and does not survive a clone. That is right for scratch
work and wrong for the runs a published claim rests on: the manifests in this
directory hash files that a fresh checkout does not have, and a hash of an
unrecoverable file is not something anyone can check.

Two kinds of run, therefore:

| | where | lifetime |
|---|---|---|
| **ephemeral** | `runs/<stage>_<timestamp>/` | overwritable, gitignored, expected to vanish |
| **promoted** | `evidence/<slug>/` | in git, one directory per durable claim |

Promotion is deliberate and per claim. A run nothing cites stays ephemeral.

## Promoting

```bash
uv run --project . python promote_evidence.py runs/<run> \
    --slug <claim-slug> --claim "what this supports" \
    --also scored_rows.jsonl --execute
```

The bundle copies the run's own records byte for byte — `config.json`,
`design.jsonl`, `environment.json`, `selection_audit.json`, `run_summary.json`,
`technical_failures.jsonl`, plus whatever `--also` names — and writes
`evidence.json` carrying design identity, resolved configuration, code identity
(commit, and whether the tree was dirty), model identity, seed regime, the
harvested definition hashes, and a file table with sizes and sha256.

Files over the copy budget are recorded by hash and location instead of copied,
so promoting never silently commits hundreds of megabytes.

`generations.jsonl` is promoted by default because it is what makes the numbers
checkable. Independent recomputation therefore runs against a bundle unchanged:

```bash
uv run --project . python verify_independently.py evidence/<claim-slug>
```

`tests/test_evidence.py` checks every bundle: required fields present, and every
file marked `COPIED` actually there with a matching hash.

## Currently promoted

None yet. The runs behind the published numbers are on the workstation and have
not been promoted from it; `figures/reasoning_compute/data/` is where the scored
rows currently survive, and `figures/reasoning_compute/data/PROVENANCE.json`
records what those exports are and why they are superseded.
