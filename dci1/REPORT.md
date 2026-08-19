# DCI-1 v2 — pre-execution study report

Date: 2026-08-16. Status: **apparatus complete and validated; confirmatory
generation locked (fail-closed); all four registered models have reached
preregistered terminal outcomes** — the Qwen pair at Gate 2 ("Regime not
found") and the gemma-3n pair at Gate 0 (the §17 truncation ceiling). No
confirmatory generation was performed.

Authoritative documents: `user-notes/DCI-1_preregistration_v2.md` (v2), the
main implementation prompt with amendments A1 (models/backend/no-thinking/
cached generation) and A2 (researcher-authorized backend pin + model list,
`DECISIONS.md`), Addendum A (`docs/addendum_a_reconciliation.md`).

## Main report (task §10)

**1. Location.** `dci1/` at the repository root — an isolated module: no
import from `src/dci` (historical confirmatory), `exploratory/dci_exploratory`
or `exploratory/crossmodel`. Layout in `README.md`.

**2. Mapping.** `MAPPING.md`: preregistration requirement → implementation →
executable test, section by section, plus the amendment-consequences analysis
for the one-accepted-response-per-cell statement (§2.9).

**3. Shared infrastructure reused.** (a) the shared vLLM backend, strictly
through its documented process boundary (`plan.json` + `design.jsonl` →
`python -m vllm_backend` → `rows.jsonl` + provenance sidecar), executed by the
pinned interpreter; (b) the generic content-hashing primitive (copied verbatim
into `protocol/hashing.py`); (c) the audited atomic-write pattern (copied into
`evidence/store.py`). Nothing else.

**4. Isolation.** All scientific content — constraints, wordings, witnesses,
verifiers, scoring rules, topics, block/prompt construction, estimators,
bootstrap, claim rules, taxonomy — written fresh from the preregistration
text. No historical registry, verifier, reference set, configuration or
`harvest.py`-style extraction is imported; the old confirmatory pipeline is
untouched.

**5. Models (amendment A2, user-authorized 2026-08-16).**

| model_key | Repository | Pinned revision |
|---|---|---|
| qwen3-4b | Qwen/Qwen3-4B | 1cfa9a7208912126459214e8b04321603b3df60c |
| qwen3-4b-instruct-2507 | Qwen/Qwen3-4B-Instruct-2507 | cdbee75f17c01a7cc42f958dc650907174af0554 |
| gemma-3n-e2b-it | google/gemma-3n-E2B-it | 5e092ebca197cdcd8d8b195040accf22693501bc |
| gemma-3n-e4b-it | google/gemma-3n-E4B-it | c1221e9c62e34a43ab7ffacd1be0ea71f126ef10 |

The original A1 list (Qwen3.5-2B/4B, gemma-4-E2B/E4B-it) is unservable by any
path under the mandated backend pin (architectures unregistered in vLLM
0.15.1; transformers <5 lacks both model types); the researcher amended the
list interactively. The gemma-3n licence gate was cleared by the researcher's
HF token (2026-08-16); both checkpoints were downloaded at their pinned
revisions and ran the full apparatus.

**6. No-thinking per model** (all verified live against the pinned backend's
own tokenizer, and on real generated text):
* qwen3-4b — `enable_thinking=False` in `apply_chat_template`; verified live
  (negating the kwarg changes the rendering; False injects a pre-closed
  `<think>\n\n</think>` into the prompt). Qualification: **QUALIFIED**, zero
  problems (no reasoning channel, no marker/control-token leakage, extraction
  returns the complete response, config consumed, revision recorded).
* qwen3-4b-instruct-2507 — no thinking switch exists; `enable_thinking`
  verified inert (all renders byte-identical); NO_THINKING is the
  checkpoint's only mode. Qualification: **QUALIFIED**, zero problems.
* gemma-3n-e2b-it / e4b-it — `enable_thinking` verified inert against the
  real templates (all renders byte-identical); no-thinking is native.
  Qualification: **QUALIFIED**, zero problems, both models. Two engineering
  facts recorded as D26: the pinned wheel crashes gemma-3n in text-only mode,
  so the unused multimodal path stays enabled; and E4B runs at
  `gpu_memory_utilization = 0.95` (weights 14.93 GiB left a negative KV
  budget at 0.85 on the 24 GiB card).

**7. vLLM configuration (amendment A2, decision D23).** Backend interpreter
`dci1/environments/backend/.venv/bin/python` (Python 3.12), built from
`dci1/environments/backend/pyproject.toml`, duplicated from
`gcd_sycophancy`: **vLLM 0.15.1+rocm720** (vendored wheel, sha256 in
`vendor/MANIFEST.sha256`), torch 2.9.1+rocm7.2.0.git7e1940d4, transformers
4.57.6, Radeon rocm-rel-7.2 wheel set. Engine: bfloat16, TP=1,
`gpu_memory_utilization=0.85`, `enforce_eager`, `max_model_len=4096`, engine
seed 20260812, one RX 7900 XTX (gfx1100) with explicit
`HIP_VISIBLE_DEVICES`. Decoding is the preregistered policy verbatim:
temperature 0.7, top-p 0.9, top-k 50 explicit, 400 max new tokens (echoed
back by the engine and asserted at qualification).

**8. Generation pool size.** `M = 16` — a registered pre-freeze study value
(decision D01), adopted as a study-specific adaptation of the Bootstrapping
Inferences technique of Kim et al. (arXiv:2605.11209; 16 was that paper's
smallest pool, for Qwen2.5-Math-7B-Instruct), not validated for the study
models and not an implementation default. Carried in every freeze record;
post-freeze change fails closed (tested).

**9. Generation-seed derivation (D06/D07).**
`SHA256("dci1:gen:v1" ∥ 202608161 ∥ stream ∥ model_id ∥ prompt_sha256 ∥
pool_index)` → 63-bit seed, per pool member; streams
confirmatory/pilot/calibration/greedy/qualification. Pure function of
scientific identity; pool members provably distinct (tested; recomputed and
asserted on every load).

**10. Primary selection rule (D02).** `primary_pool_index = 0` for every
cell, fixed before any generation, identical across models, never revisited
after outcomes exist. Member 0 is the first independent seeded draw, so the
primary dataset is distributionally identical to the unamended protocol's
single generation per cell.

**11. Pseudo-run rule (D04/D08).** `R = 1000` frozen;
`resampling_seed_r = SHA256("dci1:resample:v1" ∥ 202608162 ∥ model_id ∥ r)`;
per cell, uniform with replacement over `[0, M)` by rejection sampling on
`SHA256("dci1:select:v1" ∥ seed_r ∥ block_id ∥ arm)`. Full 10,000-resample
bootstrap additionally on the first 50 pseudo-runs (D05); the rest carry
point estimates only. Sensitivity only — never eligible for registered
claims.

**12. Resampling performs no inference — proof.** The pseudo-run and
primary-selection modules import nothing capable of inference (no backend
seam, no subprocess, no vLLM), asserted structurally by AST scan
(`test_no_inference_during_resampling`); selection reads only the sealed
append-only cache.

**13. Cached resampling and the block bootstrap stay separate — proof.**
Three disjoint SHA-256 domains and root seeds (202608161/2/3, D06); level-2
selection never touches numpy RNG; level-3 is `PCG64(bootstrap_seed)` over
block identifiers only, stratified by order, all six arms travelling together,
10,000 resamples (`test_seed_levels`, `test_unit_separation`, §12 checks
including the synthetic variance-behaviour test).

**14. Primary invariance under pseudo-runs — proof.** Pseudo-run code is
path-guarded out of the primary lineage, and the primary tree fingerprint is
asserted bit-identical before and after arbitrary pseudo-run execution
(`test_primary_bit_identical_across_pseudo_runs`, plus the flow-level
`assert_primary_invariant` run inside every sensitivity sweep). A primary
rebuild that diverges fails closed.

**15. Per-model calibration table** (96 calibration topics × 19 solo
conditions each; behavioural, per model):

| Quantity | qwen3-4b | qwen3-4b-instruct-2507 | gemma-3n-e2b-it | gemma-3n-e4b-it |
|---|---|---|---|---|
| A solo failure, n=1/2/3 | 0.031 / 0.021 / 0.125 | 0.052 / 0.052 / 0.073 | 0.490 / 0.333 / 0.323 | withheld (Gate 0 failed) |
| selected n (closest 0.30) | 3 | 3 | 3 | — |
| n in band [0.15,0.50] | **no** (0.125) | **no** (0.073) | **yes** (0.323) | — |
| B solo failure, m=7/8/9/10 | 0.760/0.625/0.458/0.323 | 0.510/0.333/0.208/0.052 | 0.229/0.198/0.073/0.063 | — |
| selected m | 10 (0.323) | 8 (0.333) | 7 (0.229) | — |
| m in band [0.15,0.55] | yes | yes | yes | — |
| candidate rates (min…max) | 0.469…1.000 | 0.500…1.000 | 0.812…1.000 | — |
| admitted candidates (≥3 needed) | **0** | **0** | **0** | — |
| references | none | none | none | — |

The calibrated models diverge exactly as the protocol anticipates (different
n-band outcomes, different m, different rates). The Qwen pair share one
terminal shape: the target constraint sits at **ceiling** (no headroom) while
every reference candidate is far harder than the focal constraint (closest:
C10 at distance 0.146 and 0.167, both outside the ±0.10 admission window).
gemma-3n-E2B is qualitatively different — it is the one model with genuine
target headroom (n = 3 at 0.323, inside the band) and a followable focal
constraint (m = 7 at 0.229) — yet the reference pool is still inadmissible:
all twelve candidates fail 81–100% of the time, the closest (C1) at distance
0.583. Across every calibrated model, the declared reference pool
(initial-letter, word-length, suffix, doubled-letter rules) is uniformly far
harder than either A or B — a consistent scientific finding about this
constraint family, not an apparatus artifact. E2B's calibration carries the
D27 procedural note (generated before its Gate 0 verdict; deterministically
regenerable, reported as a deviation).

**16. Gates and freeze status per model.**

| Gate | qwen3-4b | qwen3-4b-instruct-2507 | gemma-3n-e2b-it | gemma-3n-e4b-it |
|---|---|---|---|---|
| Qualification (§1.3) | QUALIFIED | QUALIFIED | QUALIFIED | QUALIFIED |
| Gate 0 (pilot, addendum apparatus) | PASSED 8/8 | PASSED 8/8 | **FAILED** (c3: truncation 0.139 > 0.10; 7/8 pass) | **FAILED** (c3: truncation 0.150 > 0.10; 7/8 pass) |
| Gate 1 (measurement) | PENDING_HUMAN (determinism 1.000; boundary 40/40; packets built) | PENDING_HUMAN (same) | PENDING_HUMAN (same; see D27) | not run (Gate 0 terminal) |
| Gate 2 (regime) | **FAILED — terminal** | **FAILED — terminal** | FAILED (0 admitted; D27 ordering note) | withheld (Gate 0 terminal) |
| Gate 3 (freeze) | not produced | not produced | not produced | not produced |

Terminal outcomes per §26, all four models, design never adjusted (§1.1):

* **Qwen pair — "Regime not found":** no operating point with headroom,
  deliverable treatment, and three comparable references exists in the
  declared pool. Both checkpoints satisfy "use *however* exactly n times"
  almost perfectly (2–12.5% solo failure) while failing the reference
  constraints 47–100% of the time.
* **gemma-3n pair — Gate 0 failed on the §17 truncation ceiling:** 13.9%
  (E2B) and 15.0% (E4B) of pilot generations stopped at the preregistered
  400-token limit, above the 0.10 acceptance ceiling. Every apparatus
  condition passes (72/72 rows once, zero technical failures, codebook and
  schema conformance, complete analysis, mutation detection, byte-identical
  restore, verify-evidence); the truncation is model verbosity under the
  frozen §4 decoding budget, which A1 §1.2 forbids adjusting. Generation is
  seed-deterministic, so a §17 rerun reproduces the identical rate — the
  condition cannot pass under this protocol version.

**17. Pilot and readiness.** The procedural pilot ran end to end on the full
Addendum-A apparatus for all four models (12 topics × 6 arms × M=16 = 1,152
cached generations each; 72 accepted rows committed exactly once; zero
unresolved technical failures; codebook and schema conformance; complete
analysis executed unviewed; byte-mutation detected; durable restore and full
derived-artifact restore drill byte-identical; `verify-evidence` passing).
Truncation shares: qwen3-4b 3.1%, instruct-2507 1.7% (Gate 0 PASSED);
gemma-3n-E2B 13.9%, E4B 15.0% (Gate 0 FAILED on the 0.10 ceiling, all other
conditions passing). Readiness (§9 + addendum): apparatus items all true for
every model; blocking items: Gate 1 PENDING_HUMAN, Gate 0/2 failures, no
freeze records. `generate` refuses (exit 1) — **confirmatory generation is
locked, and for all four registered models permanently so under this
protocol version.**

**18. Deviations from DCI-1 v2.** (i) A1: four models instead of one, vLLM
backend instead of HF Transformers, cached-generation machinery below the
observation level — all registered amendments. (ii) A2: backend pinned to
vLLM 0.15.1+rocm720 and the model list amended (researcher-authorized;
DECISIONS.md). (iii) D22: no container image — an environment digest over
both interpreters' package freezes + kernel + GPU identity replaces the §28
digest. (iv) D9/D10: pooling applies to the stochastic pooled stages; the
pilot's "72 rows" reads as the accepted table with pool completeness checked
additionally; calibration/greedy are single-draw. (v) D14/D15: calibration
wording rotation (p mod 4) and the pilot's added-wording rule (j//3), both
pre-freeze decisions the preregistration leaves open. (vi) Addendum A
conflicts R36/R37/R40/R41 resolved to v2 §19 by precedence (masking stays
per-block/system-random/post-generation; masked phase retains response text;
freeze carries null masking_root_seed / mask_key_hash with notes). (vii)
Human-dependent Gate 1 components and the §25 baseline are PENDING_HUMAN
(machinery complete; never faked). (viii) Durable replication is a local
second copy; off-machine durability remains a release-time step (D24).
(ix) D26: the pinned wheel crashes gemma-3n in text-only mode, so the unused
multimodal path stays enabled, and E4B runs at gpu_memory_utilization 0.95 —
engineering envelope, not science. (x) D27: gemma-3n-E2B's calibration was
generated before its Gate 0 verdict (a chain-ordering slip during an
environment repair); materially inert (seed-deterministic) but recorded as a
procedural deviation. E4B's calibration was correctly withheld.

**19. Commands.** See `README.md`: `check`, `smoke`, `dry-run`, `qualify`,
`pilot`, `calibrate [--human-labels]`, `freeze`, `readiness`,
`verify-evidence`, `generate` (locked), `select-primary`, `mask`, `analyze
--phase masked|unmasked`, `pseudo`, `greedy`, `baseline-packet`, `release`.
Tests: `cd dci1 && .venv/bin/python -m pytest tests/` (131 CPU tests; the
study's own venv — the repo-root venv stays pyarrow-free for the old study).

**20. Unresolved issues.** (i) All four registered models are terminally out
(Qwen pair at Gate 2; gemma-3n pair at Gate 0) — proceeding scientifically
requires a NEW protocol version (a harder target grid or an easier/matched
reference pool for the Qwen shape; a larger output budget or the E2B regime
revisited for the gemma shape), which only the researcher can register; the
current design was not adjusted. (ii) Gate 1 human annotation (150 responses
× 3 annotators; face validity; §25 baseline) — packets ready under
`evidence/dci1-v2/<model>/prefreeze-apparatus/calibration/gate1/`.
(iii) Registered analysis artifacts require a clean git tree; the `dci1/`
module is currently uncommitted.

## Addendum A annex (§8)

**1. Reconciliation.** `docs/addendum_a_reconciliation.md` — 55 rows, three
conflicts, all resolved by the stated precedence (v2 wins), **zero
unresolved**.

**2. Storage.** Profile `addendum-a-default-v1`: JSONL raw cache
(UTF-8, newline-terminated, `O_APPEND`, one record per append, per-record
`record_hash`); JSONL manifests; typed Parquet derived tables; deterministic
2-space sorted-key JSON records. Tree
`evidence/dci1-v2/<model_slug>/<freeze_id>/` with
prompts/cache/selection/derived/masking/integrity and `study_manifest.json`;
per-stage `MANIFEST.jsonl` (sha256, byte_length, record_count) + `_SEALED`;
stage flocks; sealed stages reject writes; raw layers replicated to
`durable_root/` before selection (recorded, enforced).

**3. Schemas.** `tables/schemas.py`: `accepted` (PK study/model/block/arm,
exactly blocks×6, no nulls, no response text — retrieved via
`cache_record_id`), `scored` (long; verifier_id ∈ target_s0..s3, added),
`analysis` (family/estimand/contrast rows with block-bootstrap CIs, claim
outcomes, full §5 provenance columns). Post-freeze schema immutability and
unknown-column rejection enforced and tested. Codebook name mapping (with
hash in the freeze record) in the reconciliation document.

**4. Masking and custody.** Scheme `v2-s19-block-primary-permutation`
(per-block system-random permutation of the four primary arms, constructed
after generation — v2 precedence). Custody per addendum: key written exactly
once to `masking/mask_key.sealed.json` with sealed hash; masked view excludes
prompt_hash/row ids/seeds (response text retained per v2 §19/§23); the
analysis entrypoint accepts only the masked-view root, and **no module under
`dci1/analysis` imports `dci1.masking`** (AST-scan test SM-06); the masked
view contains no key file (SM-05).

**5. Commitment/unmasking status.** Confirmatory: none (generation locked).
All four Gate-0 pilot trees (non-registered, `prefreeze-pilot`) exercised the
full custody path: qwen3-4b commitment `e7e09d9b67c1c8be…`
committed/unmasked 2026-08-16T19:10:12Z, mask_key `2c35f68ef9fb070c…`;
qwen3-4b-instruct-2507 `64ba4bdb76deb645…` at 19:13:05Z, mask_key
`44190dd13c38d272…`; gemma-3n-e2b-it `a400b27524a0260a…` at 20:26:39Z,
mask_key `22d3377e0e3d527e…`; gemma-3n-e4b-it `400434d6989c4588…` at
20:39:51Z, mask_key `802d60af18a2c7ce…`. Second unmask / second key /
re-mask all fail closed (tested and exercised in the blind dry run).

**6. Analysis-provenance header.** Every analysis row carries:
protocol_identity `DCI-1-2.0+A1-vllm-multimodel-cached-generation`,
freeze_record_hash, model_id/revision, input_manifest_hashes
(prompts/cache/selection), bootstrap_seed, resampling_root_seed,
masking_state, environment_record_hash (environment record includes
interpreter, lockfile hash, OS, kernel, CPU, GPU, vLLM version, BLAS
threading), analysis_command, wall_clock_utc (input-derived for byte-identical
regeneration; true wall clock in the run record). Refusals: dirty git tree,
freeze-hash mismatch, parent-manifest mismatch, stage inconsistent with
unmasking, `n_observations ≠ n_blocks × 6` — all tested.

**7. Worked provenance trace** (`docs/provenance_trace_example.json`, from
the qwen3-4b pilot tree): report.json (`analysis_table_hash 52c472f2…`) →
analysis row (F1, tau_target_first, input_accepted_hash `893692a5…`) →
accepted row (P00, focal, selected_pool_index 0, cache_record_id
`qwen3-4b:pilot:P00:focal:0`) → cache record (record_hash `d46aa0bf…`,
generation_seed 3652967726924556707, revision `1cfa9a72…`) → prompt
(hash `47156988…`, "Why do car windows fog up on the inside during cold,
damp weather?").
