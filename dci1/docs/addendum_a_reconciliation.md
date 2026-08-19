# Addendum A reconciliation — DCI-1 v2

Precedence: (1) `DCI-1_preregistration_v2.md` ("v2"), (2) the main
implementation prompt and its recorded amendments A1/A2 ("main"),
(3) Addendum A ("addendum"). Where a higher-precedence document specifies a
field, schema element, masking procedure, environment record, or table
definition, it is reproduced exactly; the addendum applies only where higher
documents are silent. Conflicts are recorded, resolved **only** by the stated
precedence order, and the addendum requirement on the losing side is not
implemented. Rows marked `conflict` name the winning source explicitly; a row
marked `conflict (unresolved)` blocks protocol freeze — there are currently
**zero** unresolved conflicts.

Test IDs refer to `tests/test_addendum_storage.py` (SA), `_schemas.py` (SC),
`_masking_custody.py` (SM), `_provenance.py` (SP); `existing:` marks coverage
already pinned by the main suite.

| # | Requirement | Source | Resolved value | Test id |
|---|---|---|---|---|
| R01 | Reconciliation doc exists, one row per requirement, conflicts block freeze | addendum §1 | this file; readiness gate item `reconciliation_zero_conflicts` | SP-01 |
| R02 | Addendum values are pre-freeze fields carried in each per-model freeze record, immutable after freeze | addendum §1 | `freeze/record.py` `addendum` block; immutability via existing byte-compare write-once | SC-08, existing: test_freeze_and_config |
| R03 | Raw generation cache: UTF-8 newline-terminated JSONL, one record/line | addendum §2 (v2 silent) | `evidence/store.py::CacheWriter` | SA-03 |
| R04 | Selection/pseudo-run/integrity manifests: JSONL | addendum §2 | `evidence/layout.py` paths; JSONL writers | SA-09 |
| R05 | accepted/scored/analysis tables: Parquet, explicit typed schemas | addendum §2 (v2 §28 names no format) | `tables/schemas.py` + `tables/build.py` (pyarrow 25.0.1) | SC-01..SC-05 |
| R06 | Freeze/masking/commitment/unmasking records: deterministic JSON, sorted keys, two-space indent | addendum §2 | `evidence/store.py::write_json` (indent=2, sort_keys) | SA-07 |
| R07 | Deterministic serialization; raw bytes preserved; ints as ints; stable floats; UTC ISO-8601 `Z` | addendum §2 | `evidence/store.py::utc_now`, json defaults; raw text stored verbatim in cache records | SA-07, SA-03 |
| R08 | One alternative storage profile may be declared pre-freeze, else fail closed | addendum §2 | `storage_format_profile = "addendum-a-default-v1"`, in freeze record; no alternative declared | SC-08 |
| R09 | Derived artifacts: temp file + flush + fsync + atomic rename on same filesystem | addendum §2; same as existing store | `evidence/store.py::atomic_write` (unchanged mechanism) | SA-01 |
| R10 | Raw cache opened `O_APPEND`, append-only; one complete record per append | addendum §2 | `CacheWriter.append` uses `os.open(..., O_APPEND)` and one `os.write` per record | SA-03 |
| R11 | Each cache record contains `record_hash` | addendum §2 (main prompt's `row_sha256` is this study's implementation name — codebook mapping) | cache records carry `record_hash` (sha256 of the record minus the hash field); mapping `row_sha256 → record_hash` recorded in codebook mapping | SA-04 |
| R12 | Never rewrite/reorder/compact/dedupe/truncate raw cache bytes | addendum §2 = v2 §28 raw-data rule | append-only writer + `verify-evidence` byte/hash checks + seal | SA-03, SA-05 |
| R13 | Serialize writes per (model, freeze_id, stage) via shared locking utility; reject concurrent writers | addendum §2 | `evidence/store.py::StageLock` (flock, non-blocking — the same fcntl utility pattern the repo's runlock uses) | SA-02 |
| R14 | On acceptance: write stage manifest, record checksum, create `_SEALED`; sealed stages reject writes | addendum §2 | `evidence/store.py::seal_stage`, `assert_stage_unsealed`; all writers check | SA-05, SA-06 |
| R15 | Never open raw evidence in truncating/in-place mode | addendum §2 | only `CacheWriter` (O_APPEND) and readers touch cache files; no `"w"` path exists for them | SA-03 |
| R16 | Directory layout `evidence/<study_id>/<model_slug>/<freeze_id>/…` | addendum §2 (higher docs silent) | `evidence/layout.py::StudyTree`; `study_id = "dci1-v2"`; `freeze_id` = 12-hex prefix of `freeze_hash`; pre-freeze Gate-0 pilot exercises the tree under reserved id `prefreeze-pilot` (recorded, non-registered) | SA-09 |
| R17 | Pseudo-run code receives only its pseudo-run output root; no write access to `derived/primary/` | addendum §2 = main prompt §2.7 | `resampling/pseudo.py` path guard + root-scoped API | existing: test_unit_separation; SM-09 |
| R18 | Artifact metadata header (study_id … created_at_utc) on every artifact; Parquet as columns, JSON at file level | addendum §2 | `evidence/store.py::artifact_header`; `tables/build.py` adds header columns | SC-06, SA-08 |
| R19 | `schema_version` semantic, changes with schema | addendum §2 | `tables/schemas.py::SCHEMA_VERSIONS` | SC-07 |
| R20 | Registered artifacts require `writer_dirty = false` | addendum §2 | `evidence/provenance.py::require_registered_writer` | SP-02 |
| R21 | Readers validate `schema_name`/`schema_version` before parsing; unknown/missing fail closed | addendum §2 | `tables/build.py::read_table` | SC-07 |
| R22 | Stage `MANIFEST.jsonl` rows carry sha256, byte_length, record_count | addendum §2 | `evidence/store.py::stage_manifest_rows` | SA-05 |
| R23 | `study_manifest.json` hashes every stage manifest + `freeze_record_hash` | addendum §2 | `evidence/store.py::write_study_manifest` | SA-05 |
| R24 | `verify-evidence --study --model` recomputes hashes/counts, checks seals/bindings, non-zero on mismatch | addendum §2 | `evidence/verify.py`; CLI `dci1.cli verify-evidence`; run before analysis and in tests | SA-05, SA-10 |
| R25 | Retain prompts/cache/selection indefinitely; replicate to durable storage before selection/scoring; record and require replication | addendum §2 (extends main D24) | `evidence/store.py::replicate_raw_layers` + gate in selection builders; `replication_target_id = "durable_root_local"` (off-machine durability remains a release step, as main D24) | SA-11 |
| R26 | Derived artifacts disposable, byte-for-byte reproducible; restore drill from replicated raw evidence in clean workspace | addendum §2 | `evidence/verify.py::restore_drill` | SA-12 |
| R27 | `accepted` PK (study, model, block, arm); exactly blocks×6 rows; no nulls | addendum §3 = v2 §20 step 2 | `tables/build.py::build_accepted` + validation | SC-01, SC-02 |
| R28 | `accepted` field list | addendum §3 (v2 codebook names override) | implemented verbatim, with mappings: `wording_id` ⇔ pair `t{i}a{j}` of the two block wording indices (main §7 has two indices); `stratum_id` = subject area; `presentation_order` = order; `resampling_seed = -1` sentinel on primary rows (no-nulls rule; primary selection is rule-based, main §2.7); `cache_record_id` = cache `row_id` | SC-01 |
| R29 | accepted does not duplicate raw text; retrieved from cache via `cache_record_id` | addendum §3 | `build_accepted` stores no response text; `tables/build.py::response_lookup` joins to the cache (the main prompt's JSONL accepted table with inline text remains as the *cache-side* selection artifact; the registered Parquet table follows the addendum) | SC-03 |
| R30 | `scored` PK (study, model, block, arm, verifier_id); one row per accepted observation per verifier | addendum §3 | long format; `verifier_id ∈ {target_s0, target_s1, target_s2, target_s3, added}`; the addendum's `scoring_rule ∈ {S0..S3}` domain is extended by the registered codebook (which the addendum defers to) with `ADDED` for the added-constraint verifier row; `manipulation_check_value` carries uptake | SC-04 |
| R31 | `F_A`/`D_i` never manually entered; computed by registered estimator in analysis stage | addendum §3 = v2 §11/§20 | verdicts stored per verifier; estimators consume BlockTable (existing) | existing: test_unit_separation |
| R32 | failure_taxonomy_code assigned before unmasking | addendum §3; v2 §23 (deterministic frozen program) | taxonomy is a frozen deterministic program (source hash in freeze record); its assignments are computed in the masked phase and identical whenever recomputed — the fixation the addendum wants is structural | SM-10 |
| R33 | `analysis` PK + field list + registered defaults | addendum §3 | `tables/build.py::build_analysis` from the §20 result dict; `n_blocks` = estimand scope size, `n_observations = n_blocks × 6` enforced for every estimand (full design = 384, per-order = 192; generalization recorded) | SC-05 |
| R34 | Pseudo-runs use same schemas with selection_source/pseudo_run_id/analysis_stage="sensitivity"; never eligible for registered claims | addendum §3 = main §2.7/§2.8 | `build_accepted(..., selection_source="pseudo_run")`; claim emission only on `analysis_stage ∈ {masked, final}` | SC-09 |
| R35 | Post-freeze schema immutability; unknown columns rejected; rows identify parent evidence; every value traceable to a cache record | addendum §3 | `tables/schemas.py::validate_table` (exact column set, no extras); parent keys `cache_record_id` / `input_accepted_hash` / `input_scored_hash` | SC-07, SP-05 |
| R36 | Masked representation: per-model deterministic permutation of six arms into arm_1..arm_6 | **conflict → v2 §19 wins** | v2 defines masking: the four PRIMARY arms are permuted independently **within each block**, seed from the **system random source**, mask constructed **after confirmatory generation and before analysis**. Implemented as v2. The addendum's per-model six-arm scheme is not implemented. | SM-01 (v2 checks), existing: test_analysis_integrity |
| R37 | Masked view excludes raw response text | **conflict → v2 §19/§23 win** | v2's masked phase explicitly includes "all reading of response text" and the §23 hand-coding of forty failures; response text stays in the masked view | SM-02 |
| R38 | Masked view excludes prompt text, prompt_hash, constraint_id, constraint_role, wording_id, constraint-identifying reason codes | addendum §4 (v2 silent — v2 permutes labels and does not require these columns in the analysed table) | adopted: the masked view drops `prompt_hash`, wording indices and any constraint-identifying column; retains block_id, masked arm, outcomes, scoring/compliance fields per the addendum | SM-02 |
| R39 | Independent permutation per model | addendum §4; v2 per-model studies | each model's mask is constructed independently (v2 construction is per model anyway) | SM-03 |
| R40 | Mask key derived from `masking_root_seed` + model, generated at freeze | **conflict → v2 §19 wins** | v2: key drawn from the system random source at mask construction (post-generation). `masking_root_seed` is recorded in the freeze record as `null` with an explicit v2-precedence note; `masking_scheme_id = "v2-s19-block-primary-permutation"` | SM-01, SC-08 |
| R41 | Key written exactly once to `masking/mask_key.sealed.json`, sealed, hash in freeze record and study_manifest | addendum §4 custody (retained); timing per v2 | key written once, sealed, hash recorded in the run record + `study_manifest.json` at construction; **freeze-record** `mask_key_hash` is `null` (v2 timing: freeze precedes generation precedes masking) — conflict resolved to v2, noted | SM-04 |
| R42 | Analysis entrypoint accepts only the masked-view root; no path/import to `masking/` key or permutation function; enforced structurally | addendum §4 (v2 single-custodian §30 compatible) | `analysis/entrypoint.py` takes a masked-view root; imports of `masking.custody`/`masking.mask` from `analysis/*` are forbidden and tested; key readable only via the single `unmask` custodian | SM-05, SM-06 |
| R43 | Pre-unmasking `commitment.json` with listed fields; requires clean git tree, completed masked analysis, sealed artifacts | addendum §4 | `masking/custody.py::write_commitment` | SM-07, SP-02 |
| R44 | `unmask --model --freeze` ordered procedure (verify → commitment → no prior record → seal record → final outputs) | addendum §4; the single named unmask function remains v2's | `cli.py::cmd_unmask2` wraps v2's `masking.mask.unmask` inside the addendum procedure | SM-07 |
| R45 | Unmasking irreversible; second attempt/second key/re-mask fail closed; masked artifacts retained; re-running registered masked analysis prohibited; later changes labelled exploratory | addendum §4; v2 §19 "after unmasking" | `masking/custody.py` guards + `unmasking_record.json`; post-unmask masked artifacts sealed | SM-07, SM-08 |
| R46 | Report states commitment hash + unmasking timestamp per model | addendum §4/§8 | `REPORT.md` §5 (currently: no model reaches masking — Gate 2 terminal) | report |
| R47 | Blind dry run on synthetic data with known truth before registered masked analysis | addendum §4 | `masking/dry_run.py` (extends the existing synthetic smoke with a known injected effect and recovery check) | SM-10 |
| R48 | Analysis artifacts record the §5 provenance fields | addendum §5 (v2 §28 environment record reproduced, extended where silent) | `evidence/provenance.py::analysis_provenance` | SP-03 |
| R49 | Environment record: interpreter, lockfile hash, OS, kernel, CPU, GPU, vLLM version, BLAS threading | addendum §5 (v2 §28 lists container digest — main D22 records env digest instead; extension is compatible) | `freeze/record.py::environment_record` extended | SP-03 |
| R50 | Refusal conditions: dirty git tree, freeze-hash mismatch, parent-manifest mismatch, stage inconsistent with unmasking status, n_observations violation | addendum §5 | `evidence/provenance.py::require_registered_writer` + `tables/build.py` gates | SP-02, SP-04, SC-05 |
| R51 | Report numbers generated programmatically from analysis.parquet; report carries analysis-table + study-manifest hashes; `make report` byte-identical | addendum §5 | `reports/build.py` + CLI `report`; regeneration test | SP-06 |
| R52 | CPU test batteries of addendum §6 | addendum §6 | the four new test modules (SA/SC/SM/SP ids above) | all |
| R53 | Freeze-record additions of addendum §7 | addendum §7 | `freeze/record.py` `addendum` block: storage_format_profile, schema_versions, manifest_hash_algorithm="sha256", masking_scheme_id, masking_root_seed=null (R40), mask_key_hash=null (R41), retention_policy_id="retain-raw-indefinitely-v1", replication_target_id="durable_root_local", addendum_version="A-1.0", codebook_name_mapping_hash | SC-08 |
| R54 | Report additions of addendum §8 | addendum §8 | `REPORT.md` sections 1–7 (addendum annex) | report |
| R55 | Readiness gains `reconciliation_zero_conflicts`; no confirmatory generation in this task | addendum §9 | `cli.py::readiness_report` extended; generation remains locked | SP-01 |

## Codebook name mapping (R11, R28, R30)

| Addendum name | Registered codebook / implementation name |
|---|---|
| record_hash | row_sha256 (cache JSONL, main-prompt schema) — Parquet-side tables use `record_hash` verbatim |
| cache_record_id | pool `row_id` |
| presentation_order | `order` (target_first / added_first) |
| stratum_id | subject area slug of `topic_id` |
| wording_id | `t{wording_target}a{wording_added}` (two block-level indices, main §7) |
| selected_pool_index | `pool_index` |
| verdict | pass/fail of the row's verifier (`f_s0` inverse for target_s0, etc.) |
| score_value | the rule's count (target rows) / 0-1 verdict (added row) |
| manipulation_check_value | `uptake` |
| compliance_flag | `short_flag or truncated or empty` |
| failure_taxonomy_code | `failure_category` |
| smallest_effect_of_interest | 0.10 (v2 §11) |

`codebook_name_mapping_hash` = sha256 of this table, recorded in each freeze
record.

## Conflicts summary

Three conflicts, all resolved by the stated precedence (v2 wins), none
unresolved, none touching an estimand, gate, verifier, or estimator:

1. **R36/R37** — masking representation and masked-view response text: v2 §19
   per-block random permutation of the four primary arms with the masked phase
   reading response text, versus the addendum's per-model deterministic
   six-arm permutation excluding response text. Implemented: v2.
2. **R40** — mask-key derivation and timing: v2 §19 system-random key at
   post-generation construction versus addendum freeze-time root-seed
   derivation. Implemented: v2; addendum freeze fields recorded as null with
   notes.
3. **R41 (partial)** — `mask_key_hash` in the freeze record: impossible under
   v2 ordering (freeze → generation → masking); the hash is recorded at
   construction in the run record and `study_manifest.json` instead.
