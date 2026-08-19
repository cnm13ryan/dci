# Implement the Updated DCI-1 Confirmatory Study

## 0. Objective, authority, and specification reconciliation

Implement a new, self-contained, isolated confirmatory-like DCI-1 study from `DCI-1_preregistration_v2.md`.

The preregistration is the authoritative scientific specification for the phenomenon, design, measurement, prompts, calibration, verifiers, gates, estimands, bootstrap, masking, analysis, provenance, and reporting.

Apply requirements in this order:

1. `DCI-1_preregistration_v2.md`
2. the explicit registered amendments and operational requirements in this implementation specification

Where the preregistration already specifies a scientific field, schema element, masking procedure, environment record, table definition, codebook name, estimator, gate, or analysis procedure, reproduce it exactly unless this specification explicitly declares a registered amendment to that requirement.

Where this specification supplies operational detail that the preregistration leaves unspecified, implement that detail literally.

Do not redesign or simplify the preregistered science. Do not change any scientific design choice, estimand, gate, verifier, scoring rule, or estimator unless an explicit registered amendment below says to do so. Do not retrofit this study into the existing historical confirmatory pipeline.

### 0.1 Fail-closed rule

If an ambiguity concerns scientific design rather than ordinary implementation, stop that part of implementation and surface the ambiguity rather than silently choosing a convention.

If a requirement in this specification appears inconsistent with a higher-precedence preregistration requirement:

1. preserve the preregistered scientific design;
2. record the conflict;
3. stop implementation of the conflicting requirement;
4. do not resolve the conflict by inference;
5. block protocol freeze until the conflict is explicitly resolved.

Do not launch confirmatory generation while any protocol-defining field remains unresolved.

Code compilation or passing low-level software tests is insufficient to authorize confirmatory generation.

### 0.2 Reconciliation record

Before substantial implementation, create:

```text
docs/addendum_a_reconciliation.md
```

Use it as the canonical specification-reconciliation record.

Include one row for every operational requirement introduced by this specification that could overlap with the preregistration:

```text
requirement
source: v2 <section> | implementation specification <section> | conflict
resolved value
implementation location
test id
```

Where the preregistration supplies the authoritative value, record that value.

Where this specification fills a field left unspecified by the preregistration, record the operational value supplied here.

Where the two cannot be reconciled literally, mark:

```text
conflict
```

Any unresolved conflict blocks protocol freeze.

Where codebook names or field names differ, the higher-precedence preregistration name wins. Record every such mapping in the reconciliation document rather than silently renaming scientific fields.

### 0.3 Pre-freeze design discipline

Every design-defining or execution-defining choice introduced by the cached-generation adaptation or operational apparatus must be explicit before protocol freeze.

This includes at minimum:

```text
generation_pool_size = M
primary_selection_rule
pseudo_run_count = R
pool_to_cell_mapping
generation_root_seed
resampling_root_seed
storage_format_profile
schema_versions
masking_scheme_id
masking_root_seed
retention_policy_id
replication_target_id
```

These values may be deliberately revised before protocol freeze.

They must never be:

* populated from hidden defaults;
* inferred opportunistically during execution;
* changed after protocol freeze;
* changed after examining confirmatory outcomes;
* silently changed because another model behaves differently.

Behaviourally calibrated quantities may differ by model where the preregistration defines them through model behaviour. Operational conventions that are specified as common study infrastructure remain common unless explicitly registered otherwise.

---

# 1. Explicit protocol amendments

## 1.1 Models

Run the full study independently on:

* `Qwen/Qwen3.5-2B`
* `Qwen/Qwen3.5-4B`
* `google/gemma-4-E2B-it`
* `google/gemma-4-E4B-it`

Treat each model as a separate registered execution condition and replication of the same experimental design.

Do not pool models, introduce cross-model estimands, or enlarge the preregistered multiplicity families unless the preregistration or a separate registered amendment explicitly specifies this.

### Model-specific behavioural calibration

Behavioural calibration is model-specific.

Where calibration depends on observed model behaviour, calibrate and freeze the resulting quantities independently for each model.

This includes at minimum:

* selected target parameter `n`;
* selected focal parameter `m`;
* admitted reference candidates;
* final reference set;
* target headroom;
* focal solo followability;
* treatment-uptake quantities;
* behavioural gate outcomes;
* any model-dependent certification outcome defined by the protocol;
* resulting model-specific freeze records.

Different models may therefore legitimately freeze different:

```text
n
m
admitted references
final references
headroom values
followability values
gate outcomes
```

Do not force common calibrated values across models merely to make model comparisons easier.

A model failing a preregistered gate reaches the terminal outcome specified by that gate.

Do not modify the design after observing that failure in order to make the model pass.

Failure of one model does not authorize changes to another model's frozen protocol.

## 1.2 Inference backend

Use the repository's existing shared **vLLM inference backend** rather than Hugging Face Transformers.

Reuse it only as generic infrastructure.

Configure each model through an explicit model-specific adapter or configuration object.

Pin the exact model revision for every model before generation.

Record and freeze at minimum:

```text
model_repository
model_revision
vllm_version
tokenizer_revision
chat_template_configuration
dtype
hardware
execution_condition
decoding_configuration
no_thinking_configuration
context_limit
output_limit
backend_configuration_hash
```

Preserve the preregistered decoding policy.

Do not adopt model-card recommended decoding parameters merely because they differ from the preregistration.

## 1.3 No-thinking qualification

All four models must run in **no-thinking / direct-answer mode** through each model's actual tokenizer, chat-template, or API semantics.

Do not assume Qwen and Gemma expose the same mechanism.

For Qwen3.5, validate the actual vLLM chat-template configuration that yields the required non-thinking output.

For Gemma 4, explicitly disable thinking through the supported model/template mechanism.

Before any study generation, run model-specific qualification probes and inspect raw generated output.

Establish that:

* thinking or reasoning is disabled;
* no hidden or default reasoning mode is accidentally active;
* no reasoning channel is included in the scored answer;
* no reasoning markers leak into scored text;
* no chat-template or control tokens leak into scored text;
* answer extraction returns exactly the complete user-visible response;
* the requested configuration is actually consumed by vLLM;
* model revision is correctly recorded;
* backend identity is correctly recorded;
* requested decoding parameters are actually consumed.

Make each requirement an executable end-to-end regression test for every model.

---

# 2. Cached-generation adaptation

## 2.1 Scope

Adapt only the **Bootstrapping Inferences** technique from Kim et al., *Measuring Five-Nines Reliability: Sample-Efficient LLM Evaluation in Saturated Benchmarks* (`arXiv:2605.11209`).

The relevant idea is:

1. generate a finite cache of independent stochastic model responses for each fixed prompt;
2. preserve the cache;
3. use cached responses for later stochastic reconstructions rather than repeatedly invoking model inference.

Do not implement:

* cross-entropy estimation;
* importance sampling;
* parameterized GSM sampling;
* rare-event estimators;
* majority voting.

Those methods are outside DCI-1.

DCI-1 has one accepted response per registered experimental cell. Cached responses therefore sit below the experimental observation.

## 2.2 Experimental-unit invariant

The registered experimental observation remains the `(model, block, arm)` cell.

For the registered primary dataset, the analysis input must contain:

[
\boxed{\text{exactly one accepted observation per }(model, block, arm)}
]

after the frozen primary-selection rule has been applied.

The hierarchy is:

```text
M cached stochastic generations
        ↓
frozen primary-selection rule
        ↓
exactly one accepted response
        ↓
one registered (model, block, arm) observation
        ↓
verifier and scoring
        ↓
registered estimator
```

Cached-generation rows:

* are not experimental units;
* are not blocks;
* do not enter the registered estimator directly;
* are not averaged together;
* are not converted into majority-vote outcomes;
* are not treated as replicated block observations;
* do not change the aggregation unit;
* do not change the clustering structure;
* do not redefine the estimand.

The registered estimator must receive only the accepted primary-response table containing exactly one accepted observation per `(model, block, arm)`.

## 2.3 Generation-pool size

Represent cache size explicitly as:

```text
generation_pool_size = M
```

The current pre-freeze study value is:

```text
M = 16
```

Treat `M = 16` as an **explicit pre-freeze study value**.

It is:

* a deliberate study choice;
* inspired by the smallest cache used in the cited reliability study;
* not a theoretical constant;
* not a value validated specifically for Qwen3.5 or Gemma 4;
* not an implementation default;
* not a fallback.

`M` may be deliberately changed before protocol freeze.

It must never be changed:

* implicitly;
* after protocol freeze;
* after observing confirmatory outcomes;
* because some generated members are missing;
* because a smaller surviving pool is convenient.

Require `generation_pool_size` to be explicitly populated in the protocol.

A missing value fails pre-freeze validation.

## 2.4 Generation identity and seeds

Every cache member must represent a genuinely distinct stochastic generation attempt.

Assign each member a deterministic, auditable `generation_seed`.

Derive it from a frozen generation root seed plus at least:

```text
model identity
prompt hash
pool index
```

Never reuse the same generation seed across members of one pool.

Persist for every generation:

```text
model_id
model_revision
block_id
arm
prompt_hash
pool_index
generation_seed
raw_response
response_content_hash
token_count
finish_reason
backend_config_hash
record_hash
```

Also include the global artifact metadata specified later.

Run diagnostics distinguishing:

* identical response content;
* identical generation seeds;
* missing generation identities;
* duplicate row identities.

Identical response content is permitted because independent stochastic generations may legitimately produce identical strings.

The following are integrity failures:

* reused seeds where distinct seeds are required;
* missing generation identities;
* duplicate row identities.

## 2.5 Missing generations are pipeline-integrity failures

A missing cached generation is always a **pipeline-integrity failure**.

Never:

* count it as model failure;
* count it as model success;
* encode it as behavioural missingness;
* silently continue with fewer than `M` members;
* sample from a reduced pool;
* redefine the pool denominator;
* substitute an unregistered stochastic draw.

Instead:

1. surface the missing registered pool identity;
2. identify its predetermined model, prompt, pool index, and seed;
3. repair that exact generation identity;
4. preserve the repair in the integrity record;
5. rerun cache validation;
6. require exactly `M` valid registered pool identities before cache acceptance.

The repair must use the previously determined generation identity and `generation_seed`.

Do not choose a fresh seed merely because the original generation attempt failed.

No primary selection, pseudo-run construction, scoring, or analysis may begin from an incomplete pool.

## 2.6 Immutable cache

Cached generations are raw evidence.

They must be:

* append-once during construction;
* immutable after acceptance;
* content-hashed;
* individually record-hashed;
* recoverable from durable storage;
* structurally separate from derived selections and analyses.

Never overwrite, compact, deduplicate, reorder, or truncate the cache.

Never regenerate raw responses merely to recreate a derived figure or analysis.

## 2.7 Registered primary selection

Define the primary selection rule explicitly before protocol freeze:

```text
primary_selection_rule
```

Permitted forms include a deterministic fixed-index rule such as:

```text
primary_pool_index = 0
```

or a deterministic seeded selection procedure fixed before outcome inspection.

Do not implement either as a hidden fallback.

The actual chosen rule must:

* be explicit;
* be frozen before scoring confirmatory outcomes;
* define exactly one selected cache member per `(model, block, arm)`;
* be deterministic;
* be reproducible;
* remain immutable after freeze.

If the protocol does not contain a frozen primary-selection rule, fail closed.

After selection, materialize a dedicated primary accepted-response table.

That table must contain exactly:

[
n_{\text{blocks}} \times 6
]

rows per model.

It is the only cached-generation-derived table eligible to feed the registered primary scoring and estimator.

## 2.8 Structural separation of primary and sensitivity datasets

Keep the registered primary dataset structurally separate from pseudo-run sensitivity analyses.

Use separate artifact roots and code paths:

```text
cache/
    immutable generations

selection/
    primary/
    pseudo_runs/

derived/
    primary/
    pseudo_runs/
```

Pseudo-run code must never:

* select the registered primary response;
* overwrite the primary selection manifest;
* replace a primary response;
* alter primary scoring;
* write into `derived/primary/`;
* change a primary point estimate;
* change a registered confidence interval;
* change a registered claim;
* determine which primary realisation is reported.

The registered primary analysis must remain exactly reproducible with the entire pseudo-run sensitivity pipeline disabled.

## 2.9 Pseudo-runs

Represent the number of pseudo-runs explicitly as:

```text
pseudo_run_count = R
```

`R` is a design-defining pre-freeze field.

Do not provide a hidden implementation default.

For pseudo-run `r`, derive its resampling seed deterministically from at least:

```text
resampling_root_seed
model identity
pseudo_run_index
```

For each registered `(model, block, arm)` cell:

1. identify its frozen generation pool;
2. verify that the pool contains exactly `M` registered members;
3. apply the frozen pool-to-cell mapping;
4. sample one pool index uniformly;
5. record the selected pool index;
6. expose exactly that response as the accepted response for that pseudo-run cell.

Sampling is with replacement **across pseudo-runs**.

The same cached response may therefore occur in multiple pseudo-runs.

Every pseudo-run must still contain exactly one response per `(model, block, arm)`.

Record:

```text
pseudo_run_id
model_id
block_id
arm
selected_pool_index
selected_response_hash
resampling_seed
```

Pseudo-run construction must perform zero new model inference.

## 2.10 Pool-to-cell mapping

Define and freeze the mapping:

```text
pool_to_cell_mapping
```

The normal invariant is:

```text
one frozen prompt identity
→ one cache containing exactly M generations
→ one registered (model, block, arm) cell
```

Any protocol-required exception must be explicit.

The mapping must be:

* deterministic;
* machine-readable;
* testable;
* frozen before confirmatory generation;
* unchanged during primary and sensitivity analyses.

Ambiguous, missing, unintended many-to-one, or unintended one-to-many mappings fail closed.

## 2.11 Permitted pseudo-run analyses

Pseudo-runs are prespecified stochastic-stability sensitivity analyses.

Permitted uses include:

* distribution of registered point estimators across stochastic realisations;
* probability that an estimated effect changes sign;
* variation in reference-exchangeability conclusions;
* variation in suitable diagnostic quantities;
* sensitivity of conclusions to the stochastic response selected for each cell.

Pseudo-run results are never eligible for registered primary claim rules.

Never use pseudo-runs to:

* choose a favourable primary dataset;
* choose the primary cache index;
* replace the primary point estimate;
* replace the preregistered block-bootstrap interval;
* select `n`;
* select `m`;
* select references;
* revise gate outcomes;
* choose among models;
* modify the registered protocol after seeing results.

## 2.12 Preserve preregistration semantics

Do not alter:

* block definition;
* experimental unit;
* arm structure;
* estimands;
* aggregation unit;
* clustering structure;
* verifier definitions;
* scoring rules;
* estimator;
* multiplicity procedure;
* equivalence procedure;
* statistical block bootstrap;
* decision rules.

Do not redefine the estimand as an average over cached generations unless a separate registered pre-freeze amendment explicitly does so.

---

# 3. Randomness separation

Maintain three independent randomness systems.

| Level                       | Purpose                                          | Seed              |
| --------------------------- | ------------------------------------------------ | ----------------- |
| Model-generation randomness | Generates the `M` cached responses               | `generation_seed` |
| Cached-response resampling  | Selects one cached response per pseudo-run cell  | `resampling_seed` |
| Statistical block bootstrap | Registered 10,000-resample bootstrap over blocks | `bootstrap_seed`  |

Do not reuse RNG streams or seeds across these levels.

Every stochastic operation must be reconstructable from frozen identities and recorded seeds.

## 3.1 Registered block bootstrap remains unchanged

For the registered primary dataset:

```text
one accepted response per model × block × arm
        ↓
score registered outcomes
        ↓
construct registered block-level quantities
        ↓
bootstrap experimental blocks
        ↓
carry all six arms of each sampled block together
        ↓
10,000 bootstrap resamples
        ↓
simultaneous intervals
        ↓
registered claim rules
```

Never bootstrap individual cached generations.

Never treat the `M` cache members as independent experimental blocks.

Never silently combine generation resampling and block resampling into a new estimator.

Pseudo-runs may be passed through the registered estimator for sensitivity analysis, but their outputs remain explicitly labelled:

```text
analysis_stage = "sensitivity"
```

and have no registered claim status.

---

# 4. Study isolation, storage, and evidence architecture

## 4.1 Isolation boundary

Build the study as a new isolated research module.

The dependency structure should resemble:

```text
shared generic infrastructure
├── vLLM backend
├── GPU/resource locking and execution utilities
└── generic artifact/provenance primitives
          │
          ▼
DCI-1 study
├── protocol/
├── models/
├── topics/
├── constraints/
├── verifiers/
├── calibration/
├── generation/
├── selection/
├── sensitivity/
├── freeze/
├── masking/
├── analysis/
├── evidence/
├── integrity/
└── reports/
```

Reuse only genuinely generic infrastructure whose semantics are study-independent.

Do not import scientific state from historical confirmatory or exploratory experiments, including:

* existing constraint registries;
* historical verifier semantics;
* previous scientific defaults;
* historical references;
* previous prompt constructors;
* previous estimators;
* previous analysis assumptions;
* mutable registries belonging to earlier studies;
* live scientific extraction from another protocol.

Do not execute a historical confirmatory stage to obtain scientific definitions.

Do not modify the old confirmatory pipeline to accommodate this study.

Compare any apparently reusable scientific component against the new preregistration field by field before reuse.

## 4.2 Storage formats

Unless the preregistration specifies a conflicting authoritative format, use:

* raw generation cache: UTF-8, newline-terminated JSONL, one record per line;
* selection manifests: JSONL;
* pseudo-run manifests: JSONL;
* integrity manifests: JSONL;
* accepted tables: Parquet with explicit typed schemas;
* scored tables: Parquet with explicit typed schemas;
* analysis tables: Parquet with explicit typed schemas;
* freeze records: deterministic JSON;
* masking records: deterministic JSON;
* commitment records: deterministic JSON;
* unmasking records: deterministic JSON.

JSON serialization requirements:

* sorted keys;
* two-space indentation for object records where applicable;
* deterministic serialization;
* integers serialized as integers;
* stable float representation;
* UTC ISO-8601 timestamps ending in `Z`.

Preserve raw model-response bytes exactly.

One alternative storage-format profile may be explicitly declared before freeze.

If used, it must:

* be recorded in every relevant freeze record;
* be used consistently across all four models;
* satisfy the same integrity guarantees.

Any undeclared storage-format change fails closed.

## 4.3 Schema and artifact metadata

Every artifact must carry:

```text
study_id
model_id
freeze_id
freeze_record_hash
schema_name
schema_version
addendum_version
writer_commit
writer_dirty
created_at_utc
```

For JSON, store these at the appropriate record or file metadata level.

For Parquet, include them as typed columns or authoritative file metadata according to the reconciled schema.

`schema_version` is semantic.

Increment it whenever the schema changes.

Registered artifacts require:

```text
writer_dirty = false
```

Readers must validate both:

```text
schema_name
schema_version
```

before parsing.

Unknown or missing schema versions fail closed.

After protocol freeze:

* reject added columns;
* reject removed columns;
* reject renamed columns;
* reject retyped columns;
* reject unknown columns rather than silently ignoring them.

## 4.4 Append-only raw writes

Open the raw generation cache append-only using `O_APPEND`.

Write exactly one complete JSONL cache record per append.

Each raw cache record must include:

```text
record_hash
```

Never:

* rewrite existing records;
* reorder records;
* compact records;
* deduplicate records;
* truncate the file;
* modify bytes in place;
* open raw evidence in a mode permitting truncation or modification.

Serialize writes for each:

```text
(model, freeze_id, stage)
```

through the shared locking utility.

Reject concurrent writers to the same stage.

## 4.5 Atomic derived writes and sealing

For every derived artifact:

1. write to a temporary path on the same filesystem;
2. flush;
3. `fsync`;
4. atomically rename to the final path.

On stage acceptance:

1. construct the stage manifest;
2. record checksums and cardinalities;
3. seal the manifest;
4. create `_SEALED`.

Reject all subsequent writes to a sealed stage.

Interrupted writes must never leave an apparently valid final-path artifact.

## 4.6 Evidence directory layout

Implement:

```text
evidence/
└── <study_id>/
    └── <model_slug>/
        └── <freeze_id>/
            ├── freeze_record.json
            ├── prompts/
            ├── cache/
            │   ├── generations.jsonl
            │   ├── MANIFEST.jsonl
            │   └── _SEALED
            ├── selection/
            │   ├── primary/
            │   │   └── primary_selection.jsonl
            │   └── pseudo_runs/
            │       └── pseudo_run_<r>.jsonl
            ├── derived/
            │   ├── primary/
            │   │   ├── accepted.parquet
            │   │   ├── scored.parquet
            │   │   └── analysis.parquet
            │   └── pseudo_runs/
            │       ├── accepted_<r>.parquet
            │       ├── scored_<r>.parquet
            │       └── analysis_<r>.parquet
            ├── masking/
            │   ├── mask_key.sealed.json
            │   ├── masked_view/
            │   ├── commitment.json
            │   └── unmasking_record.json
            ├── integrity/
            │   └── integrity_report.jsonl
            └── study_manifest.json
```

Where stage-level manifests are required by the integrity model but omitted from the compact tree above, place them inside the relevant stage directory consistently.

Pseudo-run code must receive only its pseudo-run output root.

It must have no write access to:

```text
derived/primary/
selection/primary/
```

Enforce this structurally rather than relying only on developer convention.

## 4.7 Stage and study manifests

For every materialized file, record in its stage manifest:

```text
sha256
byte_length
record_count
```

where `record_count` is meaningful for the format.

Hash each accepted stage manifest into:

```text
study_manifest.json
```

together with:

```text
freeze_record_hash
```

The study manifest must bind the complete accepted evidence chain.

## 4.8 Evidence verification

Implement:

```text
verify-evidence --study <id> --model <slug>
```

It must:

* recompute file hashes;
* recompute byte lengths;
* recompute record counts;
* verify stage manifests;
* verify seals;
* verify manifest-to-study-manifest bindings;
* verify `freeze_record_hash`;
* verify expected schema versions;
* verify required artifact presence.

Exit non-zero on any mismatch.

Run `verify-evidence`:

* in CI against fixtures;
* after sealing raw evidence;
* before selection;
* before registered analysis;
* immediately before unmasking;
* before final report generation.

## 4.9 Retention and replication

Retain indefinitely:

```text
prompts/
cache/
selection/
```

Replicate these raw and selection layers to the registered durable-storage target before scoring or downstream analysis begins.

Record successful replication.

Refuse to proceed when required replication has not succeeded.

The replication destination must be identified through:

```text
replication_target_id
```

and frozen.

Derived artifacts are disposable in the sense that they must be reproducible from immutable parent evidence.

They remain integrity-protected while present.

## 4.10 Restore drill

Implement a clean-workspace restore test for at least one model.

Starting only from the replicated raw evidence and frozen protocol material:

1. restore prompts, cache, and selections;
2. reconstruct every derived artifact;
3. compare reconstructed artifacts against the originals;
4. require byte identity where deterministic output is specified.

For deterministic-output tests, hold all explicit metadata inputs, including injected timestamps, constant.

---

# 5. Canonical derived-table schemas

Where the preregistration defines an authoritative scientific column name, use that name.

Record every name mapping in:

```text
docs/addendum_a_reconciliation.md
```

The primary keys, cardinality constraints, nullability rules, and join relationships in this section are fixed unless the preregistration explicitly conflicts.

## 5.1 `accepted`

Primary key:

```text
(study_id, model_id, block_id, arm)
```

For the registered primary dataset:

* exactly one row per registered `(model, block, arm)`;
* exactly `n_blocks × 6` rows per model;
* no nulls.

Fields:

```text
study_id
freeze_id
model_id
model_revision
block_id
topic_id
stratum_id
arm
presentation_order
wording_id
prompt_hash
selection_source
pseudo_run_id
selected_pool_index
response_content_hash
cache_record_id
token_count
finish_reason
generation_seed
resampling_seed
```

For the registered dataset:

```text
selection_source = "primary"
pseudo_run_id = "primary"
```

Represent fields such as `resampling_seed` for the primary dataset using an explicitly defined non-null sentinel or preregistration-authorized representation recorded in the schema reconciliation. Do not allow accidental nullable behaviour.

Do not duplicate raw response text in `accepted`.

Retrieve raw text from the immutable cache using:

```text
cache_record_id
```

Every accepted row must resolve to exactly one cache record.

## 5.2 `scored`

Primary key:

```text
(study_id, model_id, block_id, arm, verifier_id)
```

Create one row per accepted observation per applicable verifier.

Fields:

```text
study_id
model_id
block_id
arm
response_content_hash
verifier_id
verifier_version
verifier_source_hash
constraint_id
constraint_role
wording_id
verdict
verdict_reason_code
parse_status
scoring_rule
score_value
manipulation_check_value
compliance_flag
failure_taxonomy_code
```

Use the registered codebook domains.

`scoring_rule` must be one of:

```text
S0
S1
S2
S3
```

Assign `failure_taxonomy_code` before unmasking according to the preregistered procedure.

Do not manually enter derived quantities such as `F_A` or `D_i`.

Compute them only through the registered estimator during analysis.

Every scored row must join to exactly one accepted observation.

## 5.3 `analysis`

Primary key:

```text
(study_id, model_id, family_id, estimand_id, contrast_id)
```

Fields:

```text
study_id
model_id
freeze_id
family_id
estimand_id
contrast_id
estimator_id
point_estimate
ci_lower
ci_upper
ci_method
n_bootstrap
simultaneous
multiplicity_adjustment
equivalence_lower
equivalence_upper
smallest_effect_of_interest
claim_rule_id
claim_outcome
n_blocks
n_observations
bootstrap_seed
analysis_stage
masked
input_accepted_hash
input_scored_hash
```

Registered values include:

```text
family_id ∈ {F1, F2, F3, F4, F5, F6}
ci_method = "block_bootstrap"
n_bootstrap = 10000
analysis_stage ∈ {"masked", "final"}
```

Use:

```text
simultaneous = true
```

for registered simultaneous intervals.

For every full-design estimand:

[
n_{\text{observations}} = n_{\text{blocks}} \times 6
]

Fail closed otherwise.

## 5.4 Pseudo-run tables

Use the same scientific schemas where applicable, with:

```text
selection_source = "pseudo_run"
pseudo_run_id = <run index>
analysis_stage = "sensitivity"
```

Pseudo-run analysis rows are never eligible for registered claim rules.

Prevent the sensitivity code path from emitting a registered claim outcome.

## 5.5 Lineage invariants

Require every derived row to identify its parent evidence.

Every reported value must be traceable through:

```text
reported result
→ analysis row
→ scored rows
→ accepted rows
→ selection manifest
→ immutable cache records
→ exact prompts and generation metadata
```

---

# 6. Faithful implementation of DCI-1 v2

Apart from the explicit amendments above, implement the preregistration literally.

This includes:

* declared phenomenon and scope;
* target `A`;
* focal `B`;
* reference definitions;
* complete twelve-reference candidate pool;
* `n` calibration grid;
* `m` calibration grid;
* four frozen wordings per constraint;
* parse-independence requirements;
* satisfiability witnesses;
* bidirectional non-entailment witnesses;
* 576-topic bank across 12 subject strata;
* stratified 96 calibration / 384 confirmatory / 96 sequestered split;
* block construction;
* exact prompt construction;
* block-level assignment of presentation order;
* block-level wording assignment;
* six-arm design;
* calibration procedure;
* `S0`, `S1`, `S2`, `S3`;
* verifier reliability procedures;
* verifier validity procedures;
* manipulation checks;
* compliance checks;
* apparatus-symmetry checks;
* declared estimands;
* multiplicity families F1 through F6;
* smallest effect of interest;
* exchangeability margin;
* equivalence regions;
* equivalence rules;
* sample-size and precision logic;
* procedural pilot;
* Gates 0 through 3;
* protocol freeze;
* masked analysis;
* unmasking;
* fixed analysis order;
* fail-closed behaviour;
* failure taxonomy;
* secondary analyses;
* codebook;
* computational environment recording;
* immutable raw data;
* durable provenance;
* release requirements.

---

# 7. Model-specific calibration and freeze

Run behavioural calibration independently for each model.

Gate 2 is behavioural and must run separately for all four models.

For each model independently determine and record:

```text
selected n
selected m
admitted reference candidates
final three references
target headroom
focal solo followability
required satisfiability certification
required non-entailment certification
Gate 0 outcome
Gate 1 outcome
Gate 2 outcome
Gate 3 outcome
final calibration disposition
```

Do not assume shared values across models.

## 7.1 Per-model freeze record

Produce a separate immutable freeze record for each model.

Include at minimum:

```text
study_id
freeze_id
common_protocol_identity

model_id
model_revision
tokenizer_revision
chat_template_configuration
no_thinking_configuration
decoding_configuration
backend_configuration_hash

selected_n
selected_m
admitted_references
final_references
gate_outcomes

prompt_plan_hash

generation_pool_size
primary_selection_rule
pseudo_run_count
pool_to_cell_mapping
generation_root_seed
resampling_root_seed
bootstrap_seed

storage_format_profile
schema_versions
manifest_hash_algorithm = "sha256"

masking_scheme_id
masking_root_seed
mask_key_hash

retention_policy_id
replication_target_id

addendum_version
codebook_name_mapping_hash

environment_record_hash
freeze_created_at_utc
freeze_record_hash
```

If the preregistration requires additional fields, include them.

Unknown or unresolved required freeze fields fail closed.

A model may become eligible for confirmatory generation only when its own calibration, gates, qualification checks, reconciliation, freeze validation, and apparatus checks pass.

---

# 8. Masking and unmasking

Where v2 defines a more specific masking procedure, implement v2 and preserve the custody, commitment, isolation, and integrity controls below wherever compatible.

## 8.1 Masked representation

For each model independently, permute the six design arms into:

```text
arm_1
arm_2
arm_3
arm_4
arm_5
arm_6
```

Use an independent permutation for every model.

The registered analyst and registered analysis code may observe:

* block structure;
* masked arm identity;
* permitted outcomes.

They must not be able to infer which masked label corresponds to:

* target-only;
* focal-only;
* combined;
* any particular reference arm.

Exclude from the masked analysis view:

```text
raw_response
prompt_text
prompt_hash
constraint_id
constraint_role
wording_id
constraint-identifying verdict_reason_code values
```

Retain only the fields required by the preregistered masked analysis, including where appropriate:

```text
block_id
masked_arm
score_value
scoring_rule
parse_status
compliance_flag
manipulation_check_value
failure_taxonomy_code
```

## 8.2 Mask-key generation and custody

Derive the permutation deterministically from:

```text
masking_root_seed + model identity
```

Generate the mask key once during freeze.

Write it exactly once to:

```text
masking/mask_key.sealed.json
```

Seal it.

Record its hash in:

* the model freeze record;
* `study_manifest.json`.

Creating a second mask key for the same:

```text
(model_id, freeze_id)
```

must fail.

## 8.3 Structural isolation of registered analysis

The registered masked-analysis entrypoint must accept only the masked-view root.

It must have no:

* path;
* import;
* accessor;
* dependency;
* utility;
* environment shortcut

through which it can access:

```text
masking/mask_key.sealed.json
```

or regenerate the permutation.

Enforce this structurally.

Do not rely solely on a runtime flag such as `masked=True`.

## 8.4 Pre-unmasking commitment

Before unmasking, write:

```text
masking/commitment.json
```

containing:

```text
freeze_id
model_id
analysis_code_commit
analysis_plan_hash
exclusion_decisions_hash
verifier_versions
failure_taxonomy_assignments_hash
masked_analysis_result_hash
diagnostics_hash
committed_at_utc
actor
```

Require:

* clean git tree;
* completed masked registered analysis;
* sealed referenced artifacts;
* all required pre-unmasking decisions fixed;
* valid evidence verification;
* valid parent manifest hashes.

Reject incomplete or inconsistent commitments.

Seal the commitment before unmasking.

## 8.5 Unmasking command

Implement:

```text
unmask --model <slug> --freeze <id>
```

It must execute in this order:

1. run full evidence verification;
2. verify the sealed commitment;
3. verify all hashes referenced by the commitment;
4. verify that no `unmasking_record.json` already exists;
5. create and seal `unmasking_record.json`;
6. apply the sealed mask key;
7. produce unmasked outputs with:

```text
analysis_stage = "final"
```

The unmasking record must contain:

```text
unmasked_at_utc
actor
freeze_id
model_id
commitment_hash
mask_key_hash
analysis_code_commit
protocol_defined_reason
```

Unmasking is irreversible for the registered analysis.

Fail closed on:

* second unmasking attempt;
* second mask key;
* attempted re-masking after unmasking;
* inconsistent commitment;
* modified masked evidence.

## 8.6 Post-unmasking restrictions

After unmasking:

* retain masked artifacts unchanged;
* prohibit rerunning the registered masked analysis as though still blinded;
* prohibit changing registered exclusions;
* prohibit changing registered estimators;
* prohibit changing failure-taxonomy assignments;
* prohibit changing analysis order;
* prohibit changing registered decision rules.

Any subsequent analysis change must be labelled exploratory and receive no registered claim status.

## 8.7 Blind dry run

Before registered masked analysis, run the complete masking and analysis pipeline on synthetic data with known ground truth and a known permutation.

Verify that:

* the full pipeline executes;
* structural isolation is enforced;
* fail-closed branches behave correctly;
* the injected structure is recovered after synthetic unmasking.

Do not use real study outcomes in the dry run.

---

# 9. Analysis provenance and reporting integrity

Every analysis artifact must record:

```text
protocol_identity
freeze_record_hash
model_id
model_revision
input_manifest_hashes
bootstrap_seed
resampling_root_seed
masking_state
environment_record_hash
analysis_command
wall_clock_utc
```

For registered analyses:

```text
masking_state ∈ {"masked", "final"}
```

Record `resampling_root_seed` even though the registered primary estimator does not use cached-response resampling.

## 9.1 Environment record

Unless v2 specifies a more complete environment record, include at minimum:

```text
interpreter_version
dependency_lockfile_hash
OS
kernel
CPU_model
GPU_model
vLLM_version
BLAS_threading_configuration
```

Include all additional backend and hardware fields required elsewhere in the protocol.

## 9.2 Registered-analysis refusal conditions

Refuse to emit a registered analysis artifact when:

* git working tree is dirty;
* `freeze_record_hash` differs from the frozen record on disk;
* any required parent-manifest hash differs;
* evidence verification fails;
* requested analysis stage conflicts with unmasking status;
* schema validation fails;
* the primary accepted table does not contain exactly one observation per registered cell;
* a full-design estimand has:

[
n_{\text{observations}} \neq n_{\text{blocks}}\times6
]

* pseudo-run data appear in a registered primary analysis input;
* any required lineage link is missing.

## 9.3 Programmatic reporting

Generate every report number, table, and figure programmatically from registered derived artifacts.

For registered numerical findings, `analysis.parquet` is the authoritative reporting table.

Do not manually transcribe numerical results.

The final report must record:

```text
analysis_table_hash
study_manifest_hash
```

Implement:

```text
make report
```

such that, under identical sealed inputs and deterministic metadata, report regeneration is byte-identical.

---

# 10. Canonical validation and test specification

This is the **single canonical test specification** for the study.

Do not create parallel scientific checklists elsewhere.

All implementation stages and the final readiness report must reference these test IDs.

Use GPU tests only where actual model execution is required.

Keep protocol, schemas, verifiers, scoring, calibration, selection, resampling, masking, integrity, freeze, and statistical analysis CPU-testable wherever model execution is unnecessary.

## T1. Specification reconciliation and protocol fidelity

Validate:

* `docs/addendum_a_reconciliation.md` exists;
* every applicable requirement has a row;
* every row identifies its authoritative source;
* every scientific-name mapping is explicit;
* zero unresolved conflicts are permitted at freeze;
* exact topic split sizes;
* topic stratification;
* calibration/confirmatory/sequestered disjointness;
* exact six-arm structure;
* complete block × arm coverage;
* presentation-order assignment;
* presentation-order balance;
* wording assignment;
* matched-arm prompt identity except for the intended constraint-line difference;
* `S0` to `S3`;
* verifier boundary cases;
* satisfiability witnesses;
* bidirectional non-entailment;
* calibration rules;
* gate rules;
* codebook constraints.

## T2. Model execution qualification

For each of the four models test:

* exact repository identity;
* exact revision;
* tokenizer identity;
* chat-template identity;
* no-thinking mode actually applied;
* requested decoding consumed by vLLM;
* complete answer extraction;
* no reasoning-channel leakage;
* no reasoning-marker leakage;
* no template-token leakage;
* backend configuration recorded correctly.

## T3. Model-specific behavioural calibration

For each model independently test:

* calibration uses only that model's behavioural evidence;
* registered `n` selection rule;
* registered `m` selection rule;
* reference-admission rule;
* final reference selection;
* target-headroom calculation;
* focal solo-followability calculation;
* each applicable gate;
* gate failure terminates rather than triggering redesign;
* calibrated values are preserved in that model's freeze record;
* different models may legitimately freeze different values.

## T4. Raw storage and append integrity

Test:

* interrupted writes leave no valid final-path derived artifact;
* raw cache uses append-only semantics;
* each append preserves every previous byte;
* each append writes exactly one complete JSONL record;
* raw evidence cannot be truncated in place;
* raw evidence cannot be rewritten;
* sealed stages reject subsequent writes;
* concurrent writers to the same stage are rejected;
* `record_hash` validation works;
* one flipped raw byte is detected;
* deterministic serialization behaves reproducibly for fixed metadata inputs.

## T5. Cache cardinality and missing-generation integrity

For every required prompt test:

* exactly `M` registered pool identities exist;
* `M` equals the frozen protocol value;
* all required pool indices exist;
* generation seeds satisfy distinctness requirements;
* seed derivation is deterministic;
* duplicate row identities are rejected;
* identical output strings are not automatically rejected;
* missing pool members cause integrity failure;
* incomplete pools cannot be sealed;
* incomplete pools cannot feed primary selection;
* incomplete pools cannot feed pseudo-runs;
* missing members cannot be encoded as behaviour;
* missing members cannot reduce the sampling pool;
* repaired members use the predetermined identity and seed.

## T6. Schema validation

Test:

* `accepted` contains exactly `n_blocks × 6` rows per model;
* `accepted` contains no prohibited nulls;
* `accepted` primary key is unique;
* `scored` primary key is unique;
* `analysis` primary key is unique;
* every scored row joins to exactly one accepted row;
* every accepted row resolves to exactly one cache record;
* every full-design analysis row satisfies:

[
n_{\text{observations}} = n_{\text{blocks}}\times6
]

* unknown schema versions fail;
* missing schema versions fail;
* unknown columns fail;
* post-freeze renamed columns fail;
* post-freeze added columns fail;
* post-freeze removed columns fail;
* post-freeze retyped columns fail;
* all scientific columns have complete codebook-name reconciliation.

## T7. Primary-selection integrity

Given a fixed complete cache and frozen protocol, test:

* `primary_selection_rule` is present;
* no hidden selection default exists;
* the rule was frozen before outcome inspection;
* selection is deterministic;
* exactly one response is selected per `(model, block, arm)`;
* every selected index belongs to the correct pool;
* every selected response hash matches the cache;
* resulting primary table contains exactly one row per registered cell;
* cache members do not enter the registered estimator directly;
* cache members are never averaged into primary outcomes;
* primary selection performs no new model inference.

## T8. Pseudo-run resampling integrity

Test:

* `pseudo_run_count` is explicit;
* `pool_to_cell_mapping` is explicit;
* resampling seed derivation is deterministic;
* selected indices reproduce exactly;
* every selected index lies in `[0,M)`;
* source pools contain exactly `M` valid members;
* sampling is with replacement across pseudo-runs;
* every pseudo-run contains exactly one response per registered cell;
* selected response hashes match;
* different pseudo-run seeds can alter selections;
* resampling performs no model inference.

## T9. Primary-versus-sensitivity isolation

Test structurally that:

* primary and pseudo-run manifests use separate roots;
* primary and pseudo-run derived tables use separate roots;
* pseudo-run code cannot write into `selection/primary/`;
* pseudo-run code cannot write into `derived/primary/`;
* pseudo-runs cannot replace primary selections;
* pseudo-runs cannot modify primary scores;
* pseudo-runs cannot modify primary analysis;
* pseudo-runs cannot emit registered claims;
* registered primary analysis succeeds with sensitivity code disabled;
* deleting sensitivity outputs leaves the registered primary result unchanged.

## T10. Statistical-unit and RNG separation

Test:

* generation-pool rows are never treated as blocks;
* cache members never enter registered estimation directly;
* primary input has exactly one accepted response per registered cell;
* the block bootstrap resamples blocks;
* all six arms of a sampled block travel together;
* `n_bootstrap = 10000`;
* registered simultaneous intervals retain their preregistered semantics;
* generation RNG differs from resampling RNG;
* resampling RNG differs from bootstrap RNG;
* cached-response resampling and block resampling are not silently composed.

## T11. Evidence manifests, sealing, and verification

Test:

* every required artifact is represented in its stage manifest;
* file SHA-256 values verify;
* byte lengths verify;
* record counts verify;
* stage seals verify;
* study-manifest bindings verify;
* `freeze_record_hash` binding verifies;
* a flipped byte causes `verify-evidence` to exit non-zero;
* missing evidence causes non-zero exit;
* modified manifest causes non-zero exit;
* sealed stages reject writes.

## T12. Replication and restore

Test:

* raw evidence cannot proceed to downstream scoring before required durable replication succeeds;
* replication status is recorded;
* `replication_target_id` matches the frozen protocol;
* a clean-workspace restore reconstructs every required derived artifact;
* reconstructed deterministic artifacts are byte-identical to their originals under identical metadata inputs.

## T13. Masking isolation

Test:

* permutation is deterministic for fixed model and masking root seed;
* different models receive independently derived permutations;
* masked views contain no denylisted role-revealing fields;
* masked analysis can see only the permitted masked root;
* masked-analysis entrypoint cannot resolve the mask-key path;
* no registered analysis module imports the mask-key accessor;
* no registered analysis module can regenerate the permutation;
* second mask-key creation fails;
* synthetic blind dry run completes;
* injected synthetic structure is recovered after unmasking.

## T14. Commitment and unmasking

Test:

* unmasking without valid commitment fails;
* incomplete commitment fails;
* commitment with mismatched hashes fails;
* dirty git state blocks commitment where required;
* second unmasking attempt fails;
* re-masking after unmasking fails;
* masked artifacts remain byte-identical after unmasking;
* final analysis cannot run without an unmasking record;
* registered masked analysis cannot be rerun after registered unmasking.

## T15. Freeze completeness

Before enabling confirmatory generation for a model, test that its freeze record contains every applicable required field, including:

```text
model identity
model revision
tokenizer/chat-template identity
no-thinking configuration
decoding configuration

model-specific n
model-specific m
admitted references
final references
gate outcomes

prompt-plan identity

M
primary_selection_rule
R
pool_to_cell_mapping
generation_root_seed
resampling_root_seed
bootstrap_seed

storage_format_profile
schema_versions
manifest_hash_algorithm

masking_scheme_id
masking_root_seed
mask_key_hash

retention_policy_id
replication_target_id
addendum_version
codebook_name_mapping_hash
environment_record_hash
```

No required field may be supplied by an implicit runtime default.

## T16. Registered analysis integrity

Test:

* masking invariants;
* unmasking invariants;
* fixed registered analysis order;
* correct scoring;
* correct registered estimands;
* multiplicity families F1 to F6;
* registered equivalence logic;
* registered block bootstrap;
* input table cardinality;
* parent hashes;
* raw-response hashes;
* fail-closed behaviour;
* exact regeneration of derived outputs from immutable evidence.

## T17. Analysis provenance

Test:

* dirty git state blocks registered output;
* freeze-record hash mismatch blocks registered output;
* parent-manifest mismatch blocks registered output;
* every analysis artifact contains complete provenance;
* every reported result can be traced to originating cache records;
* `analysis_stage="final"` fails without unmasking;
* `analysis_stage="masked"` fails after registered unmasking;
* registered primary analysis rejects pseudo-run inputs.

## T18. Reporting reproducibility

Test:

* every report number is programmatically sourced;
* every table is programmatically sourced;
* every figure is programmatically sourced;
* analysis table hash appears in the report;
* study manifest hash appears in the report;
* `make report` regenerates deterministic report output byte-for-byte under identical sealed inputs and metadata.

## T19. End-to-end readiness

Require successful completion of:

* reconciliation;
* protocol tests;
* verifier tests;
* schema tests;
* storage-integrity tests;
* synthetic end-to-end smoke test;
* model-specific qualification;
* full preregistered procedural pilot;
* Gates 0 through 3 as applicable;
* model-specific calibration;
* model-specific freeze validation;
* masking dry run;
* evidence verification;
* replication checks;
* restore drill;
* primary-selection validation;
* statistical-analysis validation.

A failed required condition keeps that model in a non-runnable confirmatory state.

---

# 11. Canonical implementation order

This is the **single implementation sequence**.

Do not maintain another competing implementation checklist.

1. Inspect the repository.

2. Locate the shared vLLM seam, resource locking, GPU management, and generic provenance utilities.

3. Identify exactly which components are scientifically neutral and therefore reusable.

4. Read `DCI-1_preregistration_v2.md` section by section.

5. Create:

```text
docs/addendum_a_reconciliation.md
```

6. Create the canonical traceability mapping:

```text
preregistration or implementation requirement
→ resolved authoritative value
→ implementation location
→ canonical test ID
```

7. Resolve every non-conflicting field through the stated precedence rules.

8. Record unresolved conflicts and stop implementation of those requirements.

9. Build the isolated DCI-1 module skeleton.

10. Define explicit protocol schemas.

11. Set the current pre-freeze study value:

```text
M = 16
```

explicitly in protocol configuration.

12. Require explicit values for all other design-defining resampling fields, including:

```text
primary_selection_rule
pseudo_run_count
pool_to_cell_mapping
```

13. Implement deterministic storage serialization.

14. Implement append-only raw-cache writing.

15. Implement atomic derived-artifact writes.

16. Implement stage manifests, sealing, and `study_manifest.json`.

17. Implement `verify-evidence`.

18. Implement schema-version validation.

19. Implement retention and durable-replication controls.

20. Implement verifiers and scoring rules.

21. Implement topic bank and stratified splits.

22. Implement constraint definitions and frozen wordings.

23. Implement exact block construction.

24. Implement presentation-order and wording assignment.

25. Implement exact six-arm prompt construction.

26. Implement model-specific no-thinking adapters.

27. Qualify all four model execution paths.

28. Implement the complete model-specific calibration procedure.

29. Implement Gates 0 through 3.

30. Establish model-specific calibrated `n`, `m`, references, and gate outcomes.

31. Implement cached-generation pool construction.

32. Implement exact generation identities and deterministic seeds.

33. Implement strict missing-generation detection.

34. Implement exact-identity repair for failed or missing cache members.

35. Require complete pools of exactly `M` members.

36. Implement pool sealing and durable replication.

37. Implement frozen pool-to-cell mapping.

38. Implement deterministic primary selection.

39. Materialize the primary accepted-response table.

40. Assert exactly one primary row per `(model, block, arm)`.

41. Implement pseudo-run resampling in a separate output namespace.

42. Enforce write isolation between primary and sensitivity paths.

43. Implement the canonical `accepted`, `scored`, and `analysis` schemas.

44. Implement parent-row lineage.

45. Implement per-model freeze records.

46. Implement mask-key generation and sealing.

47. Implement structurally isolated masked views.

48. Implement pre-unmasking commitment.

49. Implement irreversible unmasking.

50. Implement registered masked and final analysis stages.

51. Implement the unchanged registered 10,000-resample block bootstrap.

52. Implement separate pseudo-run stochastic-sensitivity analyses.

53. Implement analysis provenance.

54. Implement programmatic reporting.

55. Implement `make report`.

56. Run the canonical CPU-only test suite.

57. Run the synthetic masking dry run.

58. Run a tiny synthetic end-to-end smoke test.

59. Run the preregistered procedural pilot.

60. Evaluate required gates independently for each model.

61. Run evidence verification.

62. Run the raw-evidence replication check.

63. Run the restore drill.

64. Confirm that `docs/addendum_a_reconciliation.md` contains zero unresolved conflicts.

65. Freeze each eligible model's complete protocol.

66. Validate all frozen fields and hashes.

67. Produce the readiness report in Section 12.

68. Stop.

Do **not** perform confirmatory generation as part of this implementation task.

The apparatus may become runnable after all readiness conditions pass, but this task ends before executing registered confirmatory generations.

Prefer:

* narrow modules;
* explicit configuration;
* typed schemas;
* immutable evidence;
* scientific-boundary tests;
* small smoke runs;
* machine-readable artifacts;
* deterministic provenance.

Avoid:

* giant universal experiment abstractions;
* scientific defaults hidden in utility code;
* mutable cross-study registries;
* manual result transcription;
* reduced-pool recovery;
* compatibility machinery for obsolete experiments;
* convenience shortcuts that weaken masking or evidence isolation.

---

# 12. Canonical final readiness and report checklist

Produce one final implementation/readiness report.

Do not create another overlapping reporting checklist.

Report the following.

1. Repository location of the new isolated study.

2. Completed specification reconciliation table.

3. Confirmation that the reconciliation contains zero unresolved conflicts, or a clear statement that readiness is blocked.

4. Complete preregistration/specification → implementation → canonical-test mapping.

5. Shared generic infrastructure reused.

6. Scientific components deliberately isolated.

7. Explicit isolation boundaries.

8. Exact repositories and revisions for all four models.

9. Exact tokenizer and chat-template configuration for each model.

10. Exact no-thinking configuration for each model.

11. Exact vLLM and decoding configuration.

12. Backend configuration hashes.

13. Implemented storage-format profile.

14. Implemented directory layout.

15. Append-only raw-cache mechanism.

16. Atomic-write mechanism.

17. Stage sealing model.

18. Manifest and hashing model.

19. `verify-evidence` implementation and test status.

20. Retention policy.

21. Durable replication target and status.

22. Restore-drill result.

23. The three implemented derived-table schemas.

24. Complete codebook-name mapping.

25. Current `generation_pool_size = M`.

26. Explicit statement that `M = 16` is the current pre-freeze study value rather than an implementation default.

27. Any deliberate pre-freeze revision to `M`.

28. Generation-seed derivation.

29. Frozen primary-selection rule.

30. Frozen pseudo-run count.

31. Frozen resampling-seed derivation.

32. Frozen pool-to-cell mapping.

33. Evidence that all design-defining cached-resampling choices were fixed before freeze.

34. Evidence that every required pool contains exactly `M` registered members.

35. Every missing-generation or other cache-integrity failure encountered.

36. How each missing registered generation identity was repaired.

37. Proof that missing generations were never treated as model behaviour.

38. Proof that resampling never occurred from a reduced pool.

39. Proof that the registered primary accepted table contains exactly one observation per `(model, block, arm)`.

40. Proof that cached-generation rows never enter the registered estimator directly.

41. Proof that the experimental unit remains the block-level preregistered unit.

42. Proof that primary and pseudo-run artifacts are structurally separate.

43. Proof that pseudo-run code cannot write into primary paths.

44. Proof that pseudo-runs cannot select, replace, or alter the primary result.

45. Proof that pseudo-run construction performs no model inference.

46. Proof that cached-response resampling and the statistical block bootstrap use separate RNG systems.

47. Proof that the registered 10,000-resample block bootstrap remains unchanged.

48. Per-model calibrated `n`.

49. Per-model calibrated `m`.

50. Per-model admitted references.

51. Per-model final references.

52. Per-model target headroom.

53. Per-model focal solo followability.

54. Per-model required certifications.

55. Per-model Gates 0 through 3 status.

56. Per-model freeze status.

57. Per-model freeze-record hash.

58. Procedural-pilot status.

59. Masking scheme.

60. Mask-key custody boundary.

61. Evidence that the registered analysis entrypoint cannot access the mask key.

62. Synthetic blind-dry-run result.

63. Commitment status for each model.

64. Commitment hash for each model where applicable.

65. Unmasking status for each model.

66. Unmasking timestamp where applicable.

67. Analysis-provenance header.

68. Environment-record hash.

69. Analysis table hash.

70. Study manifest hash.

71. One worked provenance trace:

```text
reported result
→ analysis row
→ scored rows
→ accepted rows
→ selection manifest
→ cache record
→ exact generation seed
→ exact prompt
→ frozen protocol
```

72. Results of every canonical test in Section 10.

73. Report-regeneration result.

74. Restore-test result.

75. Any explicit deviation from DCI-1 v2.

76. Commands for:

```text
calibration
gate evaluation
freeze
cache generation
evidence verification
primary selection
pseudo-run sensitivity generation
masked analysis
commitment
unmasking
final registered analysis
report generation
restore verification
```

77. Every unresolved issue that would make confirmatory generation scientifically ambiguous, procedurally invalid, or evidentially unrecoverable.

## Final readiness criterion

Implementation is ready for confirmatory generation only when all applicable conditions below are true:

```text
reconciliation complete
AND zero unresolved conflicts
AND all design-defining fields explicit
AND all required fields frozen
AND all model-specific calibration complete
AND required gates pass
AND all model paths qualified
AND storage invariants enforced
AND complete M-member caches can be constructed
AND missing-generation repair is fail-closed
AND evidence manifests verify
AND raw evidence replication succeeds
AND derived schemas validate
AND primary selection produces exactly one observation per registered cell
AND primary/sensitivity isolation is proven
AND masking is structurally isolated
AND commitment machinery validates
AND provenance is complete
AND canonical tests pass
AND procedural pilot passes
AND restore test passes
AND deterministic report regeneration passes
```

A failed condition blocks confirmatory generation for the affected model.

Do not perform confirmatory generation as part of this task.

Implement, validate, reconcile, freeze, and report the apparatus first.
