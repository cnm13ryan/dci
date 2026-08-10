# Exploratory DCI probe — local ROCm

The smallest experiment that can move our belief about whether **pair-specific
directional constraint interference** is real: does adding instruction **B** cost
more compliance with instruction **A** than adding *comparable* instructions does?

The comparison is always matched:

```
S ∪ {A, B}        versus        S ∪ {A, C_j}      for four references C_j
```

and compliance is scored on **A only**. The unmatched "with B versus without B"
contrast is never computed — that is the generic-load confound the reference
construction exists to remove.

Everything here is stamped `EXPLORATORY_NO_EVIDENCE`. It is deliberately smaller
than the preregistered confirmatory design, runs no gate, and authorises nothing.
See `IMPLEMENTATION_NOTE.md` for what is reused, what is new, and what is
omitted; see `FINDINGS.md` for the result.

## Reproduce

One-time setup (downloads the ROCm wheels and ~8 GB of model weights):

```bash
cd exploratory
uv sync
uv run python -m dci_exploratory.rocm_doctor      # environment record + GPU smoke test
```

The whole study, from the exploratory worktree root:

```bash
cd exploratory

# 1. design-only rehearsal — validates matching, loads no model
uv run python -m dci_exploratory.experiment --stage rehearsal --tasks 20 --dry-run

# 2. the run  (~17 min on one RX 7900 XTX, 960 generations)
uv run python -m dci_exploratory.experiment --stage B --tasks 20 --replicates 3 --load 5

# 3. analysis — tables and figures into <run>/analysis/
uv run python -m dci_exploratory.analysis runs/stageB_<timestamp>

# 4. manual audit export into <run>/audit/
uv run python -m dci_exploratory.audit runs/stageB_<timestamp>

# 5. independent recomputation of the headline numbers
uv run python verify_independently.py runs/stageB_<timestamp>
```

Tests, which never load a model and must pass before any GPU time is spent:

```bash
uv run python -m pytest tests/ -q
```

## What each run directory holds

| File | What it is |
|---|---|
| `config.json` | resolved configuration, task ids, model + revision, reference weights, provenance hashes of the reused definitions |
| `selection_audit.json` | every candidate reference considered, its eligibility verdict, coupling with A, satisfiability, and why it was or was not chosen |
| `design.jsonl` | every planned row with its `pair_key`, before generation |
| `environment.json` | GPU, ROCm, package versions, git commit and branch |
| `generations.jsonl` | **the raw artifact** — prompt, rendered prompt, response, verifier verdict and detail, termination record, per row |
| `technical_failures.jsonl` | backend faults and empty generations, kept out of the behavioural numerator |
| `batch_profiles.json` | timing, tokens, peak VRAM per batch |
| `run_summary.json` | throughput, wall time, model fingerprint |
| `analysis/` | `table_*.csv`, `headline.json`, `fig1..fig4*.png` |
| `audit/` | `audit_cases.md`, `audit_cases.jsonl`, `audit_sample.json` |

`generations.jsonl` alone is sufficient to recompute every headline number
without rerunning the model — which is what `verify_independently.py` does, using
only the standard library and the repository's verifiers.

Runs are never overwritten: each gets its own timestamped directory, and
`exploratory/runs/` is gitignored.

## Determinism

Seeding is at **batch** level, not row level: HF sampling draws from the global
RNG, so a per-row seed would be a fiction. Rows are sorted by `row_id` into fixed
batches and each batch is seeded from `base_seed + batch_offset`, both recorded
on every row. The same command on the same machine reproduces the same batches
and the same seeds. Exact token-level reproduction across different GPU counts,
batch sizes or ROCm versions is not claimed — batch composition changes the
padded width, and that changes the kernels.

## Configuration that matters

| | |
|---|---|
| model | `Qwen/Qwen3-4B-Instruct-2507` @ `cdbee75f...`, BF16, one GPU |
| A (target) | `Write exactly 4 sentences.` — verifier `v_exact_sentence_count` |
| B (focal) | `Make each sentence strictly longer than the preceding sentence when measured by word count.` |
| references | `C_L3`, `C_O2`, `C_W3`, `S_SEMICOLON` (selected before any generation) |
| background S | three whole-text prohibitions/counts, identical in every arm |
| load | k = 5 (v19 `LOADS`); k = 2 was tested in Stage A and floors A |
| orders | `o_A` and `o_Q`, both run, reported separately |
| decoding | temperature 0.7, top_p 0.9, top_k 0, `max_new_tokens` 512 |

`max_new_tokens` is **512, not the protocol's 180** — Stage A showed B's answers
sitting exactly on the 180 ceiling, which made the sentence count A is scored on
a property of the cap. `dci.analysis.output_budget` makes the same argument in
the repository's own words.
