# Reasoning data provenance

Every reasoning file in the frozen run directory, classified by **measurement** rather than by filename. Regenerate with `uv run python reasoning_provenance.py`; hashes and row counts are in `CANONICAL_RUN_MANIFEST.json`.

Run directory: `runs/stageS18_reasoning_design_20260811T144250Z` (gitignored, hence this manifest).

| file | status | role | rows | budgets | replicate pairs | identical | independent seeds |
|---|---|---|---|---|---|---|---|
| `natural_reasoning.jsonl` | **CANONICAL** | natural reasoning | 160 | 39550 | 80 | 0 (0.0%) | yes |
| `s18_reasoning.jsonl` | **DEPRECATED** | capped reasoning grid | 800 | 0, 256, 512, 1024, 4096 | 400 | 390 (97.5%) | **NO** |
| `s18_reasoning.scored.jsonl` | **DERIVED** | scoring output | 800 | 0, 256, 512, 1024, 4096 | 400 | 390 (97.5%) | **NO** |
| `s18_reseeded.jsonl` | **CANONICAL** | capped reasoning grid | 800 | 0, 256, 512, 1024, 4096 | 400 | 0 (0.0%) | yes |
| `s18_seedfix.jsonl` | **FOREIGN** | Round 10 seed-fix verification | 480 | 0, 512, 4096 | 240 | 0 (0.0%) | yes |
| `s18_transition.jsonl` | **FOREIGN** | transition budgets 320-640 | 640 | 320, 384, 448, 640 | 320 | 315 (98.4%) | **NO** |

## Why each file has its status

**`natural_reasoning.jsonl` — CANONICAL.** Per-row seeds, context-derived 39,550-token engineering ceiling, native natural closure. The endpoint of the headline figure.

**`s18_reasoning.jsonl` — DEPRECATED.** One shared seed for all 160 requests, so nominal replicate pairs are duplicates. Superseded by s18_reseeded.jsonl. Retained, never loaded.

**`s18_reasoning.scored.jsonl` — DERIVED.** An analysis output of the deprecated grid, not a generation artifact.

**`s18_reseeded.jsonl` — CANONICAL.** Regenerated with per-row seeds. The default capped input for every figure on this branch.

**`s18_seedfix.jsonl` — FOREIGN.** Another branch's verification run. Not used as canonical input here; reported only as an independent consistency check.

**`s18_transition.jsonl` — FOREIGN.** Belongs to the Round 10 line of work on the original branch. Outside this branch's scope; not used here.

## The rule this encodes

A nominal replicate pair that is byte-identical is one draw counted twice. Sampling noise makes a few plausible; a majority means a shared seed. Anything above 25% duplicates is refused as canonical input, and a file declared canonical that fails this test is re-labelled `CONTRADICTED` rather than silently trusted.
