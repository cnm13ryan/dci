# DCI-1 v2 implementation — pre-freeze decisions register

Every entry is a dated, explicit pre-freeze decision. Each resolves a value the
preregistration (`user-notes/DCI-1_preregistration_v2.md`) or its registered
amendments leave to the implementer, or records a protocol-level interpretation.
Nothing here may change after per-model protocol freeze; the freeze record
carries these values and any post-freeze mismatch fails closed.

Decisions D01–D24 recorded 2026-08-16, before any calibration or confirmatory
generation for this study.

## A2 — user-authorized amendment: backend pin and model list (2026-08-16)

Authorized interactively by the researcher on 2026-08-16, before any
generation. Two facts forced it, both verified empirically on this machine:

1. The newest vLLM/PyTorch stacks do not run reliably on this workstation
   (researcher's constraint), so the study backend is pinned to the stack of
   `inoculation-prompting/gcd_sycophancy/pyproject.toml`, duplicated verbatim
   into `dci1/environments/backend/`: **vLLM 0.15.1+rocm720** (vendored wheel)
   with **torch 2.9.1+rocm7.2.0.lw.git7e1940d4**, torchvision
   0.24.0+rocm7.2.0, torchaudio 2.9.0+rocm7.2.0, triton 3.5.1+rocm7.2.0,
   transformers 4.57.6 (vLLM caps transformers <5), Python 3.12.
2. That build registers 272 architectures and serves **neither**
   `Qwen3_5ForConditionalGeneration` nor `Gemma4ForConditionalGeneration` by
   any path (native registry: absent; transformers fallback: capped at
   transformers <5, whose last release 4.57.6 knows neither `qwen3_5` nor
   `gemma4`). The task brief's §1.1 model list is therefore unsatisfiable
   under the mandated backend, and the researcher amended the registered
   model list to four checkpoints this build serves natively:

   | Registered model | Pinned revision |
   |---|---|
   | `Qwen/Qwen3-4B` | `1cfa9a7208912126459214e8b04321603b3df60c` |
   | `Qwen/Qwen3-4B-Instruct-2507` | `cdbee75f17c01a7cc42f958dc650907174af0554` |
   | `google/gemma-3n-E2B-it` | `5e092ebca197cdcd8d8b195040accf22693501bc` |
   | `google/gemma-3n-E4B-it` | `c1221e9c62e34a43ab7ffacd1be0ea71f126ef10` |

   Rationale for the quartet (researcher-selected): the Qwen pair holds size
   fixed at 4B and varies checkpoint type (hybrid-thinking run in no-thinking
   mode vs. a pure instruct checkpoint with no reasoning channel); the Gemma
   pair keeps the E2B/E4B MatFormer size ladder of the original list in the
   gemma-3n lineage this build supports. Each model remains a separate
   registered execution condition and replication (§1.1 semantics unchanged).

   Known dependency: both gemma-3n checkpoints are license-gated on
   Hugging Face; this machine holds no HF token, so their weights cannot be
   downloaded until the researcher runs `huggingface-cli login` and accepts
   the license. Their apparatus is built and their qualification blocks,
   fail-closed, until the weights exist locally.

No-thinking (§1.3) under A2:
* `Qwen/Qwen3-4B` — hybrid checkpoint; `enable_thinking=False` in
  `apply_chat_template` injects a pre-closed `<think>\n\n</think>` block into
  the prompt (verified by rendering in this repository); the generation
  carries no reasoning channel; the live template-switch check must show the
  kwarg is consumed.
* `Qwen/Qwen3-4B-Instruct-2507` — no reasoning channel exists; the template
  takes no thinking argument (`enable_thinking` verified inert); NO_THINKING
  is the checkpoint's only mode.
* `google/gemma-3n-E2B-it` / `E4B-it` — non-thinking instruction checkpoints;
  the template takes no thinking argument. Qualification must prove the
  claimed inertness by rendering with and without `enable_thinking` and
  asserting byte-identical prompts, and must show no reasoning markers or
  control tokens in generated text.

## Registered amendment values (§2.10 of the task brief)

- **D01 — generation_pool_size `M = 16`.** Fixed by the study brief as a
  study-specific adaptation of the Bootstrapping Inferences technique of
  Kim et al. (arXiv:2605.11209), which used 16 cached generations per input for
  Qwen2.5-Math-7B-Instruct. 16 is the smallest pool size used in that paper; it
  is **not** a value validated for Qwen3.5 or Gemma 4 and is not a library
  default. Provenance recorded here and in every freeze record.
- **D02 — primary_selection_rule: `primary_pool_index = 0` for every cell.**
  The task brief's "simplest implementation". Fixed before any generation,
  identical across all four models, never revisited after outcomes exist.
  Because pool member 0 is the first independent seeded draw for each prompt,
  the primary dataset is distributionally identical to the unamended protocol's
  single stochastic generation per cell.
- **D03 — pool_to_cell_mapping:** one cached response per `(model, block, arm)`
  cell, sampled uniformly with replacement across pseudo-runs, never averaged,
  never voted, never aggregated. Verbatim from the amendment.
- **D04 — pseudo_run_count `R = 1000`.** Sensitivity pseudo-runs. 1000 point-
  estimate reconstructions give Monte-Carlo error ≤ ~1.6 percentage points on
  any sign/threshold probability, at zero inference cost.
- **D05 — pseudo_run_full_analysis_count = 50.** The full 10,000-resample block
  bootstrap plus family intervals is additionally run on the first 50 pseudo-run
  indices (0–49) to measure variability of interval-based conclusions
  (exchangeability, equivalence). The remaining 950 pseudo-runs carry point
  estimates only. Fixed pre-freeze; purely a sensitivity analysis.
- **D06 — root seeds.**
  - `topic_split_seed = 202608160`
  - `generation_root_seed = 202608161`
  - `resampling_root_seed = 202608162`
  - `bootstrap_root_seed = 202608163`
  Chosen as date-derived integers before any generation. The three randomness
  levels (model generation / cached-response resampling / block bootstrap) use
  disjoint SHA-256 domain strings and disjoint root seeds; the mask permutation
  deliberately uses the system random source per prereg §19 and none of these.
- **D07 — seed derivation.** `generation_seed = SHA256("dci1:gen:v1" ∥ root ∥
  stream ∥ model_id ∥ prompt_sha256 ∥ pool_index)` truncated to 63 bits.
  Streams: `confirmatory`, `pilot`, `calibration`, `greedy`, `qualification`.
  Includes model identity, prompt hash and pool index as the amendment requires;
  independent of batch position and scheduler order.
- **D08 — resampling seed derivation.** Per pseudo-run r:
  `resampling_seed_r = SHA256("dci1:resample:v1" ∥ resampling_root_seed ∥
  model_id ∥ r)`; per cell the selected pool index is
  `SHA256("dci1:select:v1" ∥ resampling_seed_r ∥ block_id ∥ arm)` reduced to
  `[0, M)` by rejection sampling (exact for any M; unbiased). Order-independent
  and reconstructable per cell.

## Scope interpretations of the cached-generation amendment

- **D09 — pools apply to the stochastic confirmatory arms only.** The amendment
  defines pools "for every frozen (model, block, arm) prompt", i.e. the
  confirmatory block×arm design under the registered stochastic decoding
  policy. Calibration (Gate 2 solo prompts), the procedural pilot's apparatus
  check, and qualification probes are generation stages of the apparatus, and
  the greedy sensitivity replication is deterministic (a pool of M identical
  draws would be vacuous). Calibration and greedy runs therefore generate one
  response per prompt exactly as preregistered, using the same seed-derivation
  family with `pool_index = 0`. The **pilot** exercises the full amended
  apparatus (pools of M, primary selection, accepted table) because Gate 0
  certifies the apparatus that the confirmatory run will use.
- **D10 — pilot row accounting under pools.** Prereg §17 fixes "seventy-two of
  seventy-two rows committed": under the amendment this is the accepted-response
  table (12 blocks × 6 arms). Pool completeness (72 × M = 1152 members) is
  checked as an additional apparatus condition; the technical-failure and
  token-limit proportions (§17 conditions 2–3) are computed over **all pool
  generations** (the stricter, apparatus-level reading) and also reported for
  the 72 accepted rows.
- **D11 — one-accepted-response invariant.** After cache selection the primary
  analysis receives exactly one accepted observation per (model, block, arm):
  the accepted table has exactly blocks×6 rows; the block remains the
  assignment, pairing, clustering and generalisation unit; cached generations
  never reach any estimator; M appears in no scoring rule, contrast, interval
  or claim rule. Consequences enumerated in `MAPPING.md` §"Amendment
  consequences".

## Protocol details the preregistration leaves to fixing pre-freeze

- **D12 — prompt template exact bytes.**
  Two-constraint arms: `"{question}\n\n1. {first}\n2. {second}\n\nAnswer:"`.
  Target-alone: `"{question}\n\n1. {target}\n\nAnswer:"`.
  Topic-alone: `"{question}\n\nAnswer:"`.
  No system message; a single user turn; chat template applied by the engine
  with `add_generation_prompt=True`.
- **D13 — block indexing.** The 384 confirmatory topics are ordered
  stratum-major (the twelve §6 subject areas in their declared order), within
  stratum in the seeded-shuffle order that produced the split; block index
  i ∈ {0..383} follows that order; block_id = `B{i:03d}`. Even i → target
  first; wording(A) = i mod 4; wording(added) = ⌊i/4⌋ mod 4 (prereg §7).
  This yields 16 target-first and 16 added-first blocks per stratum.
- **D14 — calibration wording rotation.** Gate 2 solo prompts use wording index
  `p mod 4` for calibration-topic position p (0–95, stratum-major order), so
  all four wordings of every constraint appear equally often in calibration.
  The prereg fixes four wordings per constraint but not the calibration
  wording assignment; rotation matches the confirmatory design's averaging
  over the wording pool. Surfaced in the §10 report as a pre-freeze decision.
- **D15 — pilot design details.** Pilot topics: the first calibration topic of
  each of the twelve strata (deterministic under the split). Pilot block index
  j ∈ {0..11}: order = target-first for even j; wording(A) = j mod 4;
  wording(added) = ⌊j/3⌋ — the confirmatory formula ⌊j/4⌋ mod 4 cannot reach
  wording 3 with twelve blocks, and §17 requires all four wordings of each
  constraint represented. Pilot provisional parameters (discarded, never
  scientific): n = 2, m = 8, provisional references C1, C3, C10. No target
  failure rate, arm difference or contrast is computed on pilot rows.
- **D16 — word segmentation for all pool verifiers.** A "word" is a maximal run
  of Unicode-alphabetic characters (`str.isalpha`) in the lower-cased response
  — identical to the run definition the target verifier uses. Hyphenation and
  apostrophes split words ("don't" → "don", "t"). Letter comparisons are on the
  lower-cased text. A response with no words satisfies every universally
  quantified pool constraint vacuously; the ≤3-word compliance flag (§16)
  reports such degenerate responses.
- **D17 — S3 preprocessing definition.** (1) While the first line whose
  stripped text is non-empty ends with ":", delete that line. (2) Delete every
  line whose lower-cased text contains the lower-cased full text of any active
  constraint wording of that prompt. Then apply S0 to the remainder.
- **D18 — restatement similarity function (taxonomy category 4).**
  `difflib.SequenceMatcher(None, a, b).ratio()` over lower-cased,
  whitespace-collapsed strings, where `a` is the response and `b` is the
  numbered constraint block of the prompt; threshold strictly greater than
  0.60. Frozen with the taxonomy source hash.
- **D19 — refusal detection (taxonomy category 3).** Twenty frozen lower-case
  patterns (see `analysis/taxonomy.py`); a response is a refusal when at least
  one pattern occurs and removing every sentence containing a pattern leaves no
  alphabetic character ("contains no answer text").
- **D20 — instruction-length admission criterion (Gate 2).** Length is the
  whitespace-token count of wording index 0 with the calibrated parameter
  substituted; a candidate is admissible when
  |len(candidate) − len(focal)| / len(focal) ≤ 0.20.
- **D21 — wording-equivalence check set.** The fixed set of twenty test
  responses in `constraints/wording_check_responses.py`; all four wordings of a
  constraint must map to the same verifier and hence identical verdicts on all
  twenty; meaning-identity additionally checked by the researcher.

## Execution-environment deviations (surfaced, not silent)

- **D22 — no container image.** Prereg §28 specifies one container image with a
  recorded digest. This study executes on the workstation directly (2× Radeon
  RX 7900 XTX, gfx1100, ROCm). In place of a container digest the freeze
  record carries an **environment digest**: SHA-256 over the sorted
  `pip freeze` of both interpreters (backend and scientific) plus kernel and
  GPU identity, asserted at every generation exactly as the digest would be.
  This is an explicit deviation from §28, reported under item 18 of the study
  report.
- **D23 — backend identity (under amendment A2).** The backend code is
  `exploratory/vllm_backend` at the current commit of this repository. The
  backend interpreter is `dci1/environments/backend/.venv/bin/python`
  (Python 3.12), built from `dci1/environments/backend/pyproject.toml`, which
  duplicates the `gcd_sycophancy` GPU-stack pins: vLLM 0.15.1+rocm720
  (vendored wheel, sha256 recorded in `vendor/MANIFEST.sha256`), torch
  2.9.1+rocm7.2.0.lw.git7e1940d4 and the matching Radeon rocm-rel-7.2 wheel
  set. The scientific interpreter is the repo-root `.venv` (Python 3.13.12,
  numpy 2.5.1). Both identities (code commit + interpreter package freezes)
  enter the environment digest.
- **D24 — durable storage.** Durable root is `dci1/durable_root/` on the same
  filesystem, written by the same commit protocol (payload + commit marker) and
  used by the delete-and-restore checks (§17.7, §28). True off-machine
  durability is a release-time step and is reported as pending.

- **D26 — gemma-3n multimodal path left enabled (2026-08-16, pre-freeze,
  pre-generation).** The A2 configuration set
  `limit_mm_per_prompt = {"image": 0, "audio": 0}` for the gemma-3n pair to
  skip multimodal cache reservation in this text-only study. Verified on the
  pinned wheel: zeroing every modality makes vLLM 0.15.1 run the model in
  text-only mode (`MultiModalRegistry.supports_multimodal_inputs` → False),
  whose runner passes `inputs_embeds=None`, and the wheel's
  `Gemma3nForConditionalGeneration.forward` dereferences `inputs_embeds`
  unconditionally — engine initialization crashes
  (`AttributeError: 'NoneType' object has no attribute 'shape'`). Both
  gemma-3n qualification attempts failed closed with this signature and
  produced no cache rows. Resolution: `limit_mm_per_prompt` is unset for the
  gemma-3n specs — prompts remain text-only, the unused multimodal path stays
  enabled, and the backend configuration hash changes accordingly (no
  generation for these models predates the change). An engineering-envelope
  decision; no scientific field is affected. The pinned wheel is NOT patched.
  Follow-up, same date: with the multimodal path enabled, E4B's weights
  (14.93 GiB) left a negative KV budget at `gpu_memory_utilization = 0.85` on
  the 24 GiB card; the E4B spec alone runs at 0.95 (measured envelope).
  Decoding, context limits and every scientific field are identical across
  models; per-model memory utilization is hardware envelope, not science.

- **D27 — recorded procedural deviation: gemma-3n-E2B calibration preceded
  its Gate 0 completion (2026-08-16).** §17 orders the procedural pilot
  before any calibration generation. In the E2B execution chain the pilot
  stage crashed at module import (a missing pyarrow dependency during an
  environment repair — no generation occurred) and the chain proceeded to
  calibration; the pilot was completed afterwards and FAILED its §17
  truncation ceiling. E2B's calibration cache was therefore generated before
  its Gate 0 verdict existed. The deviation is materially inert — calibration
  generation is deterministic in the frozen seeds and configuration, so a
  post-pilot regeneration would be byte-identical — but it is a procedural
  deviation and is reported as such. E4B's calibration was correctly
  withheld after its Gate 0 failure; the Qwen models ran in order.

## Human-dependent protocol elements (pending, never faked)

- **D25 — human annotation.** Gate 1 human agreement (150 responses × 3
  annotators), face validity (3 annotators), the §25 human-written baseline,
  and the §23 forty hand-coded failures require human annotators. The
  machinery (deterministic sampling, blinded packets, evaluators) is
  implemented; the measurements are marked PENDING_HUMAN and Gate 1 cannot
  pass — and confirmatory generation cannot be unlocked — until they exist.
