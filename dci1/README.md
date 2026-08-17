# DCI-1 — isolated confirmatory study module

> **This module now holds two protocol versions.** The v2 implementation
> (`src/dci1`, below) is **closed**: all four model replications reached
> preregistered terminal outcomes with zero confirmatory generations. The
> active implementation is **v3** (`src/dci1v3`) — see the
> [DCI-1 v3](#dci-1-v3-srcdci1v3) section at the end of this file,
> `DECISIONS_V3.md`, and `REPORT_V3.md`.

## v2 (closed): preregistration v2 + amendments A1/A2 + Addendum A

This module implements `user-notes/DCI-1_preregistration_v2.md` literally,
under the registered amendments: A1 (task brief §1–§3: four models as separate
execution conditions, shared vLLM backend, no-thinking, cached-generation
resampling with `M = 16`), A2 (researcher-authorized 2026-08-16: backend
pinned to vLLM 0.15.1+rocm720 / torch 2.9.1+rocm7.2; model list amended to
Qwen3-4B, Qwen3-4B-Instruct-2507, gemma-3n-E2B-it, gemma-3n-E4B-it), and
Addendum A (operational storage/masking/provenance).

Authoritative documents, in order: the preregistration; `DECISIONS.md` (dated
pre-freeze decisions); `MAPPING.md` (requirement → implementation → test);
`docs/addendum_a_reconciliation.md` (Addendum-A requirement table, conflicts
resolved by precedence); `REPORT.md` (the pre-execution study report).

## Isolation boundary

Scientific dependencies point inward. This module imports **nothing** from
`src/dci` (the historical confirmatory pipeline), `exploratory/dci_exploratory`
or `exploratory/crossmodel`. It reuses exactly three generic things: the
shared vLLM backend through its documented process boundary only
(`plan.json` + `design.jsonl` → `python -m vllm_backend` → `rows.jsonl`,
executed by the pinned interpreter in `environments/backend/`); the generic
content-hashing primitive (copied into `protocol/hashing.py`); and the audited
atomic-write pattern (copied into `evidence/store.py`). All constraints,
wordings, witnesses, verifiers, scoring rules, topics, design logic,
estimators and analysis are written fresh from the preregistration text.

## Module layout

    environments/backend/   pinned ROCm vLLM environment (A2), uv project
    docs/                   addendum reconciliation, provenance-trace example
    src/dci1/
      protocol/    registered constants, hashing, 3-level seeds, codebook
      constraints/ A, B, C1–C12, four wordings each, witnesses
      verifiers/   S0–S3, pool verifiers, 40-case boundary suite, registry
      topics/      576-topic bank + seeded stratified split (96/384/96)
      design/      blocks, exact prompt bytes, stage cell plans
      models/      the four ModelSpec adapters + no-thinking qualification
      generation/  backend seam, pool construction/validation (M=16)
      evidence/    layout, append-only store, sealing, verify, provenance
      tables/      typed Parquet schemas + builders (accepted/scored/analysis)
      resampling/  primary selection (index 0) and pseudo-run lineage
      calibration/ Gate 1 (measurement) and Gate 2 (regime)
      pilot/       Gate 0 procedural pilot + synthetic end-to-end smoke
      freeze/      per-model freeze records (§18 + §2.10 + Addendum §7)
      masking/     v2 §19 masking, sealed-key custody, blind dry run
      analysis/    scored tables, block bootstrap, families F1–F6, claims,
                   checks, taxonomy, precision, sensitivity, masked entrypoint
      flow.py      the Addendum-A evidence flow over one StudyTree
      reports/     programmatic report builder, release manifest, baselines
      cli.py       stage commands + the §9 readiness gate
    tests/         CPU test suite (131 tests); GPU stages run via the CLI
    evidence/      ALL working evidence (gitignored; layout below)
    durable_root/  durable mirror of the raw layers (gitignored; same shape)

## Evidence layout

All results live under one root, `dci1/evidence/`, with the durable mirror at
`dci1/durable_root/` repeating the identical shape. The path grammar is three
fixed levels:

    evidence/<study_id>/<model_slug>/<tree_id>/...

* `<study_id>` — always `dci1-v2` for this study.
* `<model_slug>` — a registered model key (`qwen3-4b`,
  `qwen3-4b-instruct-2507`, `gemma-3n-e2b-it`, `gemma-3n-e4b-it`), or the
  reserved slug `_synthetic` for non-model apparatus checks. Reserved slugs
  always start with `_`.
* `<tree_id>` — which body of results this is:
  * `prefreeze-apparatus` — the model's pre-freeze stage results
    (qualification, calibration, gate records, pilot report, run record);
  * `prefreeze-pilot` — the Gate-0 procedural pilot's full evidence tree,
    in the registered Addendum-A layout;
  * a 12-hex `<freeze_id>` — a frozen confirmatory tree (none exist yet;
    created only when a model passes Gates 0–3 and freezes).

The same three levels under `durable_root/` hold the replicated raw layers
(`prompts/`, `cache/`, `selection/`, each file with a `.sha256` sidecar).

### Full tree with contents

    evidence/dci1-v2/
    ├── qwen3-4b/
    │   ├── prefreeze-apparatus/
    │   │   ├── qualification/            backend run: plan.json, design.jsonl,
    │   │   │                             rows.jsonl (raw probe generations),
    │   │   │                             rows_engine.json (engine provenance),
    │   │   │                             backend.log
    │   │   ├── qualification_report.json no-thinking verdict + all checks
    │   │   ├── calibration/
    │   │   │   ├── pool/                 solo-prompt cache: pool.jsonl (1,824
    │   │   │   │                         raw responses, append-once, hashed),
    │   │   │   │                         gen_round0/ backend artifacts,
    │   │   │   │                         pool_integrity_report.json
    │   │   │   ├── solo_rates.json       per-condition solo failure rates
    │   │   │   ├── gate1.json            Gate 1 record (determinism, boundary
    │   │   │   │                         suite, item behaviour, human status)
    │   │   │   ├── gate1/                blinded annotation_packet.jsonl +
    │   │   │   │                         annotation_truth.json (150 items)
    │   │   │   └── gate2.json            Gate 2 record: n/m selection, bands,
    │   │   │                             admission table, references, verdict
    │   │   ├── pilot-v0-superseded/      Gate-0 evidence from the first
    │   │   │                             (pre-Addendum-A) apparatus; retained
    │   │   │                             as record, superseded by
    │   │   │                             ../../prefreeze-pilot/
    │   │   ├── pilot_report.json         current Gate-0 report (8 conditions)
    │   │   └── runrecord.jsonl           append-only event log (generation
    │   │                                 rounds, gates, masks, unmasks)
    │   └── prefreeze-pilot/              ← the registered Addendum-A tree
    │       ├── freeze_record.json        the pilot's non-registered plan stub
    │       ├── prompts/                  cells.jsonl (exact prompt bytes +
    │       │                             hashes), MANIFEST.jsonl, _SEALED
    │       ├── cache/                    generations.jsonl (append-only raw
    │       │                             cache, 1,152 records, per-record
    │       │                             record_hash), backend_runs/,
    │       │                             MANIFEST.jsonl, _SEALED
    │       ├── selection/
    │       │   ├── primary/primary_selection.jsonl   (rule: pool index 0)
    │       │   └── pseudo_runs/pseudo_run_<r>.jsonl  (sensitivity draws)
    │       ├── derived/primary/          accepted.parquet, scored.parquet,
    │       │                             analysis.parquet (typed, reproducible
    │       │                             byte-for-byte from raw layers)
    │       ├── masking/                  mask_key.sealed.json (+.sha256),
    │       │                             masked_view/ (masked_rows.jsonl,
    │       │                             analysis_masked.parquet),
    │       │                             commitment.json,
    │       │                             unmasking_record.json
    │       ├── integrity/                cache_report.json, replication.json,
    │       │                             integrity_report.jsonl
    │       ├── study_manifest.json       stage-manifest hashes + key hash
    │       └── report.json               programmatic report (from analysis
    │                                     parquet; carries table hashes)
    ├── qwen3-4b-instruct-2507/           same shape as qwen3-4b
    ├── gemma-3n-e2b-it/                  created when the licence gate clears
    ├── gemma-3n-e4b-it/                  created when the licence gate clears
    └── _synthetic/
        ├── smoke/                        synthetic end-to-end smoke tree
        │                                 (smoke_report.json + synthetic pools,
        │                                 primary/pseudo lineages, mask,
        │                                 analysis) — regenerated by `smoke`
        └── dryrun/                       blind dry run tree
                                          (dry_run_report.json + full masked→
                                          commit→unmask cycle on synthetic
                                          data) — regenerated by `dry-run`

### Naming conventions

* **Stage seals** — a sealed stage contains `MANIFEST.jsonl` (one row per
  file: `path`, `sha256`, `byte_length`, `record_count`) and `_SEALED`
  (timestamp + manifest checksum). Sealed stages reject all writes.
* **Cache records** — `row_id = <model_key>:<stream>:<block_id>:<arm>:<pool_index>`;
  streams are `confirmatory | pilot | calibration | greedy | qualification`.
  Every record carries `record_hash` over its own payload.
* **Blocks/arms** — confirmatory blocks `B000`–`B383`, pilot blocks
  `P00`–`P11`, synthetic blocks `T*/S*/D*`; arms are
  `focal | ref1 | ref2 | ref3 | target_alone | topic_alone`, and calibration
  solo conditions are `solo:A:n=<n> | solo:B:m=<m> | solo:C<k>`.
* **Pseudo-runs** — `pseudo_run_<r>` with `r` zero-padded to 4 digits;
  pseudo lineages live only under `selection/pseudo_runs/` and
  `derived/pseudo_runs/`, never under `*/primary/`.
* **Parquet tables** — every table carries `schema_name`/`schema_version`
  metadata and the ten-field artifact header; derived timestamps are
  input-derived (cache seal time) so regeneration is byte-identical.
* **Superseded results** — never deleted; renamed with a `-v0-superseded`
  suffix and kept in place (e.g. `pilot-v0-superseded/`).
* **Locks** — transient flock files live in `evidence/.locks/` (GPU) and as
  `.lock_<stage>` inside a tree root; they are not evidence.

### Where to find each type of result

| Result | Path (under `evidence/dci1-v2/`) |
|---|---|
| No-thinking qualification verdict | `<model>/prefreeze-apparatus/qualification_report.json` |
| Raw qualification generations + engine provenance | `<model>/prefreeze-apparatus/qualification/rows.jsonl`, `rows_engine.json` |
| Calibration raw responses (1,824 solo answers) | `<model>/prefreeze-apparatus/calibration/pool/pool.jsonl` |
| Solo failure rates per constraint | `<model>/prefreeze-apparatus/calibration/solo_rates.json` |
| Gate 1 record / human-annotation packets | `<model>/prefreeze-apparatus/calibration/gate1.json`, `calibration/gate1/` |
| Gate 2 record (n, m, admission, references, verdict) | `<model>/prefreeze-apparatus/calibration/gate2.json` |
| Gate 0 pilot report (current apparatus) | `<model>/prefreeze-apparatus/pilot_report.json` |
| Gate 0 pilot raw cache (12×6×16 generations) | `<model>/prefreeze-pilot/cache/generations.jsonl` |
| Pilot accepted/scored/analysis tables | `<model>/prefreeze-pilot/derived/primary/*.parquet` |
| Mask key, commitment, unmasking record | `<model>/prefreeze-pilot/masking/` |
| Stage manifests, seals, study manifest | `<model>/prefreeze-pilot/{prompts,cache}/MANIFEST.jsonl`, `_SEALED`, `study_manifest.json` |
| Replication record (raw → durable) | `<model>/prefreeze-pilot/integrity/replication.json` |
| Per-model event history | `<model>/prefreeze-apparatus/runrecord.jsonl` |
| First-apparatus pilot (superseded, retained) | `<model>/prefreeze-apparatus/pilot-v0-superseded/` |
| Synthetic smoke report | `_synthetic/smoke/smoke_report.json` |
| Blind dry-run report | `_synthetic/dryrun/dry_run_report.json` |
| Durable copies of raw layers | `../durable_root/dci1-v2/<model>/<tree_id>/…` (+ `.sha256` sidecars) |
| Confirmatory evidence (future) | `<model>/<freeze_id>/…` — none exist; generation is locked |

To compare models, diff the same relative path across `<model_slug>`
directories (e.g. the two `gate2.json` files, or the two
`qualification_report.json` files). To check any tree's integrity:

    PYTHONPATH=src $PY -m dci1.cli verify-evidence --model <model> \
        --freeze prefreeze-pilot

## Commands

    PY=/home/cnm13ryan/git/dci/dci1/.venv/bin/python   # the study's own scientific env
    cd dci1
    $PY -m pytest tests/ -q                       # 131 CPU protocol tests
    PYTHONPATH=src $PY -m dci1.cli check          # measurement/witness checks
    PYTHONPATH=src $PY -m dci1.cli smoke          # synthetic end-to-end smoke
    PYTHONPATH=src $PY -m dci1.cli dry-run        # blind masking dry run
    PYTHONPATH=src $PY -m dci1.cli qualify   --model qwen3-4b
    PYTHONPATH=src $PY -m dci1.cli pilot     --model qwen3-4b
    PYTHONPATH=src $PY -m dci1.cli calibrate --model qwen3-4b \
        [--human-labels labels.jsonl]
    PYTHONPATH=src $PY -m dci1.cli freeze    --model qwen3-4b
    PYTHONPATH=src $PY -m dci1.cli readiness --model qwen3-4b
    PYTHONPATH=src $PY -m dci1.cli verify-evidence --model qwen3-4b \
        --freeze prefreeze-pilot
    PYTHONPATH=src $PY -m dci1.cli generate  --model qwen3-4b   # locked by §9
    PYTHONPATH=src $PY -m dci1.cli select-primary --model qwen3-4b
    PYTHONPATH=src $PY -m dci1.cli mask      --model qwen3-4b
    PYTHONPATH=src $PY -m dci1.cli analyze   --model qwen3-4b --phase masked
    PYTHONPATH=src $PY -m dci1.cli analyze   --model qwen3-4b --phase unmasked
    PYTHONPATH=src $PY -m dci1.cli pseudo    --model qwen3-4b
    PYTHONPATH=src $PY -m dci1.cli greedy    --model qwen3-4b

`generate` refuses until every item of the §9 readiness list holds for that
model — including Gate 1's human-agreement measurement (PENDING_HUMAN until
three annotators label the calibration packet) and the Addendum-A condition
that `docs/addendum_a_reconciliation.md` carries zero unresolved conflicts.
Current status per `REPORT.md`: both runnable models reached the
preregistered terminal outcome "Regime not found" at Gate 2; the gemma-3n
pair is blocked on the Hugging Face licence gate.

---

# DCI-1 v3 (`src/dci1v3`)

Implements `user-notes/DCI-1_preregistration_v3.md` (sole scientific
authority) under the anti-regression specification
`user-notes/DCI-1_v2-to-v3_changelog.md`. Scientifically independent of v2:
`dci1v3` imports nothing from `dci1` (executable test), has its own
constants, topics, verifiers, state machine, evidence tree, masking custody,
and analysis. Shared generic infrastructure: the vLLM backend process seam
(`exploratory/vllm_backend`, executed by the pinned interpreter in
`environments/backend/`) only.

Authoritative v3 documents: the preregistration; `DECISIONS_V3.md`
(registered manifest values and executable readings, V01–V19);
`REPORT_V3.md` (the item-65 readiness report).

## Layout

    src/dci1v3/
      protocol/    constants (every registered value), hashing, seeds,
                   wordings (4 per template, caliper), codebook
      topics/      528 released topics + opaque sequestered manifest,
                   seeded split, block plans (+ data/)
      verifiers/   S0–S3, focal + RF1–RF8, 40-case boundary suite,
                   witnesses (288 compositions), wording-equivalence suites
      models/      the four registered replications (E2B first)
      engine/      context/namespaces, canonical paths, signing (HMAC),
                   cross-process writer locks, git + uv provenance,
                   write-once store + durable mirror, artifact ledger,
                   state machine + transition log, canonical evidence
                   verification, the canonical dispatcher
      generation/  prompt cells + plans + coverage assertions, backend
                   seam, 16-draw cache, synthetic adapter (tests only)
      stages/      registration, qualification, pilot (Gate 0), regime
                   pre-screen, Gate 1 (+ E2B carry-over), Gate 2A/2B,
                   freeze, confirmatory chain (generate/select/mask/
                   masked-analysis/unmask/final-analysis), pseudo-runs,
                   greedy, verify-evidence, readiness
      analysis/    block estimators, stratified bootstrap + simultaneous
                   intervals, claims vocabulary, failure taxonomy, the
                   §20 fixed-order run
      cli.py       the canonical public execution interface
    tests_v3/      the canonical suite (82 tests) incl. the full synthetic
                   end-to-end lifecycle through the public entrypoints
    tools/         build_topics_v3.py (access-control, run once), new topics

## Evidence layout (v3)

    evidence/dci1-v3/registration/        signed study manifest + key
    evidence/dci1-v3/<model_slug>/
      qualification.json gate0_apparatus.json regime_screen.json
      gate1_measurement.json gate2a_solo.json gate2b_composed.json
      gate3_freeze.json confirmatory_manifest.json primary_selection.json
      confirmatory_mask_record.json masked_result.json unmask_record.json
      unmasked_result.json transition_log.jsonl terminal_report.json
      carry_over.json pseudo_runs.json greedy_run.json
      qualification/ pilot/ prescreen/ gate1/ gate2a/ gate2b/
      confirmatory/ masking/{pilot_mask,confirmatory_mask}/ analysis/
      artifacts/ledger.jsonl
    durable_root/dci1-v3/                 byte-identical durable mirror

Synthetic-namespace trees (study id `dci1-v3-synthetic`) exist only under
test scratch directories, never under `evidence/`.

## Commands

    PY=dci1/.venv/bin/python              # uv-synced scientific interpreter
    $PY -m dci1v3.cli register
    $PY -m dci1v3.cli qualify        --model gemma-3n-e2b-it
    $PY -m dci1v3.cli pilot          --model gemma-3n-e2b-it
    $PY -m dci1v3.cli prescreen      --model gemma-3n-e2b-it
    $PY -m dci1v3.cli carry-over     --model gemma-3n-e2b-it
    $PY -m dci1v3.cli gate1          --model gemma-3n-e2b-it \
        --annotations <labels.json>
    $PY -m dci1v3.cli gate2a         --model gemma-3n-e2b-it
    $PY -m dci1v3.cli gate2b         --model gemma-3n-e2b-it
    $PY -m dci1v3.cli freeze         --model gemma-3n-e2b-it
    $PY -m dci1v3.cli generate       --model ...   # locked until freeze
    $PY -m dci1v3.cli select-primary --model ...
    $PY -m dci1v3.cli mask / masked-analysis / unmask / final-analysis
    $PY -m dci1v3.cli pseudo-runs / greedy
    $PY -m dci1v3.cli verify-evidence --model ...
    $PY -m dci1v3.cli readiness

    cd dci1 && .venv/bin/python -m pytest tests_v3   # v3 suite
    cd dci1 && .venv/bin/python -m pytest            # both suites

Every mutating command runs the one production path: writer lock →
clean-worktree check → canonical evidence verification → predecessor
validation → stage function → durable write → hash verification →
signed record → transition log. There is no dirty-tree bypass.

## Gate 1 reviewer GUI (v3)

Human annotation runs through a dependency-free local web app
(`dci1v3/annotation/`, decision V20 as amended by A1). Under amendment A1,
**exactly one independent annotator** covers each model packet — Gate 1
measures human-to-verifier disagreement from one independent judgment per
item, with the registered Wilson bound and thresholds unchanged:

    $PY -m dci1v3.annotation.server --model gemma-3n-e2b-it --annotator A1
    # keyboard-first: 1 = SATISFIES, 2 = VIOLATES, F = flag; autosaves.

The annotator sees only the registered constraint text and the unmodified
response, in a seeded shuffled order; item identities, verifier verdicts,
autorater outputs, class structure, and sampling status are structurally
absent. Finalisation requires a binary label on every item plus the §10
face-validity judgment, and is immutable. The researcher dashboard
(`--dashboard`) shows completion status only until that single annotator
finalises, then reveals human-to-verifier diagnostics and exports the
exact file (`{item_id: ["pass"|"fail"], "face_validity": [bool]}`) for:

    $PY -m dci1v3.cli human-audit --model <model> --annotations \
        annotations/<model>/gate1_annotations.json

Working files live in `annotations/` (gitignored); labels enter evidence
only through the registered `human-audit` pathway.

## Gate 1 without a human annotator (amendment A2)

No independent human annotator is currently available, so Gate 1 runs the
autorater-assisted verifier workflow (one configured autorater,
`src/dci1v3/protocol/data/autorater.json`; a proxy instrument — never
human validation, never ground truth, never part of scoring):

    $PY -m dci1v3.cli gate1-dev       --model <model>   # dev half + report
    #   inspect evidence/dci1-v3/<model>/gate1/autorater/dev/report.json,
    #   refine the verifier if needed (regression tests), re-run gate1-dev
    $PY -m dci1v3.cli verifier-freeze                   # study-level, once
    $PY -m dci1v3.cli gate1-calibrate --model <model>   # held-out half
    #   inspect evidence/dci1-v3/<model>/gate1_calibration.json
    $PY -m dci1v3.cli gate1 --model <model> \
        --approve-autorater-calibration                 # explicit approval

The development/calibration split is deterministic, stratified, and
disjoint; the calibration half stays untouched until the verifier freezes;
the calibration report carries coverage, marginals, directional
disagreement, and the full 2×2 contingency table with **no automatic
acceptance threshold** — closing the gate is an explicit researcher
decision. If behaviorally relevant verifier code changes after freezing,
calibration evidence is marked contaminated and a fresh held-out split is
required. Strongest supported claim: *"The frozen deterministic verifier
was developed and evaluated on held-out responses against the specified
autorater under the registered configuration. Independent human validation
is unavailable."*
