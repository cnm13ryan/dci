# Red-team: `dci1/prompt.md` vs. the current codebase

Date: 2026-08-16 (late evening). Target: `dci1/prompt.md` (2,467 lines, mtime 23:28) audited against `dci1/src/dci1/` at repo HEAD `094922b` (module untracked). Method: every prompt section read; every implicated module read in full (`cli.py`, `flow.py`, `evidence/{store,sealing,layout,verify,provenance,integrity}.py`, `masking/{mask,custody}.py`, `resampling/{primary,pseudo}.py`, `tables/{build,schemas}.py`, `freeze/record.py`, `generation/{pools,validation}.py`, `analysis/{entrypoint,sensitivity}.py`, `pilot/runner.py`, `protocol/constants.py`, `reports/build.py`); claims cross-checked against the artifacts in `evidence/dci1-v2/` and the earlier two inspection reports. No evidence-tree file was modified; no raw response or prompt text was read.

**Headline: the Addendum-A apparatus that Gate 0 certified is real and largely faithful — but it is not the apparatus the CLI would use for a confirmatory run.** The `generate → select-primary → mask → analyze` commands are wired to a pre-Addendum legacy pipeline that bypasses the evidence tree, sealing, custody, commitment, and the single-shot unmask. Because Gate 2/Gate 0 terminated all four models, this dormant path never executed — but it is the single most important thing to fix before any v3 reuses this module.

Severity bands: **A** = the registered confirmatory path would violate the spec if ever run; **B** = a spec mandate implemented nowhere; **C** = partial/weakened implementation; **D** = known, documented divergence (registered decision or declared precedence) where prompt.md itself was never updated.

---

## A. Critical — the confirmatory path is not the certified apparatus

**A1. The CLI confirmatory pipeline bypasses the Addendum evidence architecture entirely** [prompt §4.5, §4.6, §4.7, §8; contradicts D09's "Gate 0 certifies the apparatus that the confirmatory run will use"].
*Evidence.* `cli.py:307-326` (`cmd_generate`) writes pools to `model_apparatus_dir/confirmatory/` via `generation/pools.py` (`pool.jsonl`, `AppendOnceJsonl`), not to a `StudyTree` freeze-id tree; `cli.py:329-347` (`cmd_select_primary`) uses `resampling/primary.py::build_primary` into `confirmatory/primary/*.jsonl`; `cli.py:365-374` (`cmd_mask`) and `cli.py:377-402` (`cmd_analyze`) operate on `model_dir/analysis/` with `masked_accepted.jsonl` and a **plain `mask_key.json`**. No CLI command invokes `flow.write_prompts` / `flow.generate_cache` / `flow.select_primary` / `flow.construct_masked_view` / `flow.derive_primary` for a confirmatory tree, and nothing creates the 12-hex `<freeze_id>` tree the README and `layout.py:16` promise. The certified path (`flow.py` + `sealing.py` + `custody.py`) is reachable only from `pilot/runner.py`, `pilot/smoke.py`, and `masking/dry_run.py`.
*Consequence.* A confirmatory run would produce evidence with no stage manifests, no seals, no study manifest, no sealed mask key, no commitment, no unmasking record, no Parquet accepted/scored/analysis tables, and no provenance refusal gates — everything §4–§9 of the prompt exists to guarantee.
*Fix.* Rewire `generate`/`select-primary`/`mask`/`analyze` (and `pseudo`, `greedy`) to construct `StudyTree(model_slug, freeze_id=freeze_hash[:12])` after Gate 3 and route through `flow.py`; delete or explicitly quarantine (`-v0-superseded`) the legacy `model_dir/{confirmatory,analysis}` path; add a regression test asserting the confirmatory commands write only inside a freeze-id tree.

**A2. The §8.5 `unmask` command does not exist, and the wired unmask path has no guards** [prompt §8.5; reconciliation R44 is factually wrong].
*Evidence.* `COMMANDS` (`cli.py:446-454`) contains no `unmask`; `grep cmd_unmask2` over `src/` and `tests/` returns nothing, yet `docs/addendum_a_reconciliation.md` R44 claims "`cli.py::cmd_unmask2` wraps v2's `masking.mask.unmask` inside the addendum procedure." The reachable unmask (`cli.py:393` → `masking/mask.py:95-116`) opens the key with **no evidence verification, no commitment check, no prior-record check, no unmasking record, and no single-shot guard** — running `analyze --phase unmasked` twice unmasks twice. The guarded procedure exists only as library functions (`masking/custody.py:97-129`) called inline by the pilot runner.
*Fix.* Implement `unmask --model --freeze` executing §8.5's order (verify-evidence → verify sealed commitment → hash checks → no prior record → seal `unmasking_record.json` → apply key → `analysis_stage="final"`); make `analyze --phase unmasked` refuse unless that record exists; correct R44.

**A3. The legacy mask path permits re-masking and a second key** [prompt §8.2 "creating a second mask key … must fail"; §8.5 "re-masking after unmasking fails"].
*Evidence.* `masking/mask.py:78-85` (`construct_mask`) has no existence check for `mask_key.json` or `masked_accepted.jsonl`, and `evidence/store.py:47-60` (`atomic_write`) overwrites via `os.replace` — a second `cli mask` run silently regenerates the permutation and replaces the key. The guards live only in `custody.write_mask_key_sealed` (`custody.py:29-47`), which the CLI path never calls.
*Fix.* Subsumed by A1/A2; minimally, add fail-closed existence guards to `construct_mask`.

---

## B. High — mandated, implemented nowhere

**B1. `make report` and a `report` command are absent** [prompt §9.3, §11 step 55, T18; reconciliation R51 claims "CLI `report`"].
*Evidence.* No `Makefile` under `dci1/` or the repo root; `COMMANDS` has no `report`; `reports/build.py::build_report` exists and is exercised by `tests/test_addendum_provenance.py`, but only the qwen3-4b pilot tree ever received a `report.json` (the other three trees have none) — it was invoked ad hoc.
*Fix.* Add a `report` CLI command (and optionally a Makefile target) that runs `verify_evidence` first (§4.8) and regenerates byte-identically; run it for all trees; correct R51 or the CLI.

**B2. `verify-evidence` covers a fraction of §4.8 and is not invoked at the mandated points.**
*Evidence.* `evidence/verify.py:22-62` verifies stage manifests, seals, cache record hashes, and study-manifest bindings — but performs **no schema-version validation, no required-artifact-presence check** (absent stages report `"absent"` and `ok` stays true), and never touches `derived/` or `masked_view` Parquet. The freeze binding is checked only `if manifest.get("freeze_record_hash")` (line 52) — always null today. Invocation points: §4.8 requires it after sealing, **before selection, before registered analysis, immediately before unmasking, before report generation**; actual call sites are the CLI command, `pilot/runner.py:195` (after unmasking, as condition c8), and tests. `flow.select_primary`/`derive_primary` gate on `assert_replicated` and freeze consistency only; `custody.write_commitment` checks only the key sidecar. The CLI signature is also `--model/--freeze` with no `--study` (`cli.py:100-108, 466`).
*Fix.* Extend `verify_evidence` with schema-version checks (`read_table`) over `derived/` and `masked_view`, and an expected-artifact manifest per stage; call it in `select_primary`, `derive_primary`, `write_commitment`, the future `unmask`, and `build_report`; accept `--study`.

**B3. Selection and masking stages are never sealed or manifested, and the study manifest does not bind the full chain** [prompt §4.5 "on stage acceptance … seal", §4.7 "bind the complete accepted evidence chain"].
*Evidence.* Every real tree reports `"selection": "unsealed (no manifest yet)", "masking": "unsealed (no manifest yet)"` (verify-evidence output, all four models); `study_manifest.json` binds only `prompts` and `cache` (`stage_manifest_sha256` has two keys). Worse, `flow.py:453` writes the study manifest with `freeze_record_hash=None` **unconditionally** — even a registered confirmatory tree would carry a null freeze binding, which `verify.py:52` then skips.
*Fix.* Seal `selection` after primary selection is accepted and `masking` after the masked view + commitment are complete; pass the real freeze hash into `write_study_manifest`; make a null `freeze_record_hash` a verification failure for non-pilot trees.

**B4. Pseudo-run derived Parquet tables are not produced by any production path** [prompt §4.6 `derived/pseudo_runs/accepted_<r>.parquet`…, §5.4].
*Evidence.* `flow.select_pseudo` writes selection JSONL only; `StudyTree.derived_pseudo` (`layout.py:106-107`) ignores its `run_index` argument and has no callers in `src/`; the production sensitivity sweep (`analysis/sensitivity.py:54-115`, via `cli pseudo`) runs on the **legacy** lineage (`confirmatory/pseudo/run_<r>/{manifest,table}.jsonl` + `sensitivity_summary.json`) and never materialises `accepted_<r>/scored_<r>/analysis_<r>` Parquet with `analysis_stage="sensitivity"`. `build_accepted(selection_source="pseudo_run", …)` and `build_analysis(analysis_stage="sensitivity")` are exercised only by tests (`tests/test_addendum_schemas.py:146-158`).
*Fix.* Add `flow.derive_pseudo(run_index)` writing the three Parquet tables under `derived/pseudo_runs/`, fix `derived_pseudo` to use `run_index`, and point the sensitivity sweep at it.

**B5. Freeze-record fields required by §7.1 are missing.**
*Evidence.* `freeze/record.py:50-57` (`REQUIRED_FIELDS`) and `build_freeze_record` (158-263) contain no `tokenizer_revision`, no `freeze_created_at_utc` (the record carries no timestamp at all), and no named `environment_record_hash` (the full environment dict is embedded instead; its digest is inside it). The §7.1 name `prompt_plan_hash` is implemented as `block_plan_hash` with **no row in the reconciliation's name-mapping table** (`docs/addendum_a_reconciliation.md`, codebook mapping section) — contra §0.2 "record every such mapping."
*Fix.* Add the three fields (tokenizer revision is pinned = model revision; record that explicitly), plus a `freeze_created_at_utc` stamp excluded from the immutability byte-compare or included before hashing; add the `prompt_plan_hash → block_plan_hash` mapping row.

**B6. The environment record is degenerate and the register describing it is stale** [prompt §9.1; §1.2 requires `vllm_version` frozen].
*Evidence.* Neither interpreter has `pip` (verified live: `ModuleNotFoundError` in both `dci1/.venv` and `environments/backend/.venv`), and `_pip_freeze` (`freeze/record.py:68-76`) swallows every failure into `[]` — so `scientific_freeze` and `backend_freeze` are empty in every recorded environment, `vllm_version` (derived from the backend freeze at `record.py:106-108`) is `""`, and the digest is identical (`d3df1a86…`) across all four models despite the documented mid-study venv upheaval. At Qwen-artifact time the coded `SCIENTIFIC_PYTHON` path (`dci1/.venv`, `record.py:77-82`) did not yet exist (venv born 20:23 UTC; Qwen artifacts 19:10/19:13 UTC) and nothing noticed. `DECISIONS.md` D23 still names the repo-root `.venv` as the scientific interpreter, contradicting the code and its own comment.
*Fix.* Replace `pip freeze` with `uv export`/lockfile hashes for both interpreters; **fail closed on an empty freeze or missing interpreter binary**; populate `vllm_version` from the engine echo (qualification already has it); amend D23 with a dated correction.

---

## C. Medium — partial or weakened implementations

**C1. §4.3 artifact metadata header exists only on Parquet tables.** Cache records (`sealing.py CacheWriter` rows; verified against `cache/generations.jsonl` field lists), selection manifests, `commitment.json`, `unmasking_record.json`, `study_manifest.json`, and the freeze stub all lack the ten-field header; SA-08 (`tests/test_addendum_storage.py:116-128`) tests only the helper's key set, not its application. *Fix:* add file-level header blocks to JSON/JSONL artifacts, or register the narrowing explicitly in the reconciliation.

**C2. The canonical test IDs T1–T19 are referenced nowhere** [prompt §10 "single canonical test specification … all stages and the final readiness report must reference these test IDs"]. No test file, `MAPPING.md`, `README.md`, or `REPORT.md` mentions them; the implementation uses its own scheme (module names + SA/SC/SM/SP), and `MAPPING.md`/`REPORT.md` are exactly the "parallel checklists" §10/§12 forbid. *Fix:* add a T-ID column to `MAPPING.md` mapping each T1–T19 bullet to its test(s), and reference it from the readiness report.

**C3. Legacy pool writes are not serialized** [prompt §4.4 "serialize writes … through the shared locking utility; reject concurrent writers"]. `generation/pools.py::build_pools` and `store.AppendOnceJsonl.append` take no lock (no `StageLock`/`flock` anywhere in that path); two concurrent `calibrate`/`generate` invocations could interleave the check-then-append and duplicate identities. Only `flow.py` locks (`sealing.py:70-93`). *Fix:* wrap `build_pools` in the flock utility.

**C4. `parse_status` is hardcoded `"ok"`** (`tables/build.py:149`) and has no codebook domain (`protocol/codebook.py` never mentions it). The §16/§23 "response the verifier cannot process" state can never surface in the scored table. *Fix:* derive from the verifier call (exception → `"error"`), register the domain.

**C5. Commitment preconditions are partial and the dirty-tree escape is unscoped** [prompt §8.4 requires clean git tree, completed masked analysis, sealed referenced artifacts, valid evidence verification, valid parent hashes]. `custody.write_commitment` (`custody.py:61-94`) checks the key sidecar, one result hash, and the dirty flag — no evidence verification, no parent-manifest hashes, no seal check on the masked view; and `allow_dirty=True` is available to any caller (used by `pilot/runner.py:107,117`; nothing restricts it to non-registered trees). *Fix:* add the missing preconditions; restrict `allow_dirty` to `freeze_id ∈ {prefreeze-pilot, _synthetic}` structurally.

**C6. Pilot order vs §8.5:** `verify_evidence` runs only *after* unmasking (`pilot/runner.py:195`, c8), not "immediately before unmasking" (§8.5 step 1). *Fix:* move/duplicate the call before `write_unmasking_record`.

**C7. `integrity/integrity_report.jsonl` is promised, never written** (prompt §4.6 tree; `layout.py:13` docstring; README tree diagram). Real trees hold `cache_report.json` + `replication.json`. *Fix:* either emit the aggregate JSONL or amend the three documents.

**C8. Hidden seed default:** `generation_seed` is recorded as `int(row.get("seed_reasoning", 0))` (`flow.py:123`; `pools.py:175`) — a backend row missing the field would be stamped seed 0 rather than failing. Caught downstream by `validate_pools`' derivation check, but §2.4/§0.3 forbid the hidden default in the first place. *Fix:* raise on missing `seed_reasoning`.

---

## D. Documented divergences prompt.md never absorbed (report-only)

**D1. Model list** — §1.1 names Qwen3.5-2B/4B and gemma-4-E2B/E4B; implemented are Qwen3-4B / Qwen3-4B-Instruct-2507 / gemma-3n-E2B/E4B (`models/adapters.py:59-113`), under researcher-authorized amendment A2 (`DECISIONS.md`), forced by the pinned backend serving neither original architecture. prompt.md was never revised; anyone auditing from prompt.md alone will conclude the wrong models ran.

**D2. Masking scheme** — §8.1/§8.2 (per-model six-arm `arm_1..6` permutation, derived from `masking_root_seed` at freeze, key hash in freeze record, `raw_response` excluded from the masked view) vs implemented v2 §19 (per-block four-primary-arm permutation, system random, post-generation, response text retained; `masking_root_seed`/`mask_key_hash` null in the freeze record with notes). Resolved correctly by prompt.md's own precedence rule (§8 preamble "Where v2 defines a more specific masking procedure, implement v2") and recorded as conflicts R36/R37/R40/R41 — but note T13's "deterministic for fixed masking root seed" is therefore untestable as written.

**D3. `wall_clock_utc` is not wall clock** — deliberately input-derived (cache seal time) for byte-identical regeneration (`tables/schemas.py` docstring; `tables/build.py:220`); true times live in `runrecord.jsonl`. Registered in the docs; prompt §9 unamended.

**D4. `scoring_rule` domain extended with `"ADDED"`** for the added-constraint verifier row (`tables/build.py:176`) vs §5.2's closed `{S0..S3}`; recorded in reconciliation R30.

**D5. Legacy cache-side accepted table duplicates response text** (`resampling/primary.py:91`, `accepted.jsonl`) vs §5.1 "do not duplicate raw response text"; reinterpreted in R29 (the registered Parquet table is clean — verified: no text column in any `accepted.parquet`). Becomes moot if A1's fix removes the legacy path.

**D6. Run-record timestamps end `+00:00`, not `Z`** (`store.py:229` uses `.isoformat()`; e.g. every `runrecord.jsonl` event) vs §4.2. All other JSON artifacts use `utc_now()` which does end in `Z` (`sealing.py:33-34`). One-line fix.

---

## Verified faithful (for balance)

Registered constants transcribed exactly (`protocol/constants.py`: decoding, grids, bands, SEOI/margins, families, M=16, R=1000, D06 seeds); three-level randomness separation with disjoint domains (`protocol/seeds.py`, `test_seed_levels`); pool construction/repair per §2.3–§2.5 including exact-identity repair under original seeds and fail-closed incompleteness (`pools.py`, `validation.py`, `flow.generate_cache`); append-once/O_APPEND cache with per-record hashes (`sealing.CacheWriter`); atomic derived writes; typed Parquet schemas with PK-uniqueness, unknown-column rejection, schema-version validation on read (`tables/schemas.py`); primary bit-identity invariant and pseudo write-path guard (`resampling/*`, `test_unit_separation`); claim-outcome suppression for sensitivity rows (`tables/build.py:257-258`); Addendum custody guards where used (second key/second unmask/commitmentless unmask all refuse — exercised for real in four pilot trees and the blind dry run); replication-before-selection gate (`sealing.assert_replicated`, `flow.select_primary:227`); restore drill with byte-identity (`verify.restore_drill`, pilot c7); analysis-entrypoint isolation (R42 + AST test); 131/131 CPU tests pass.

---

## Priority order for fixes

1. A1 (rewire the confirmatory CLI through `flow.py`/StudyTree) — everything else in band A/B assumes it.
2. A2 (+C5, C6): implement `unmask` and complete the commitment preconditions.
3. B3 (seal selection/masking; real freeze hash in the study manifest) and B2 (verify-evidence coverage + call sites).
4. B6 (environment record fail-closed; D23 correction) — prerequisite for any v3 freeze meaning anything.
5. B5 (freeze-record fields), B4 (pseudo Parquet lineage), B1 (`report` command).
6. C-band hardening and the D-band documentation sync (fold A2's model list and the masking/timestamp deviations into prompt.md or a dated amendment appendix, and fix the false R44/R51 rows).

One process note: the reconciliation document is keyed to a different sectioning of the specification than prompt.md (its rows cite "addendum §2–§9"; prompt.md's corresponding material sits in §4–§9 with tests as §10 T1–T19). Several prompt.md-specific mandates (T-IDs, `--study` flag, `unmask` command, `make report`) therefore have **no reconciliation row at all**, which is itself a §0.2 violation worth closing when the rows for R44/R51 are corrected.
