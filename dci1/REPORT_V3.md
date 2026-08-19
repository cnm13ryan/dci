# DCI-1 v3 — implementation readiness report (item 65)

**Date:** 2026-08-17 · **Protocol:** DCI-1 v3.0 · **Study id:** `dci1-v3`
**Authority:** `user-notes/DCI-1_preregistration_v3.md` under
`user-notes/DCI-1_v2-to-v3_changelog.md`. Registered decisions:
`DECISIONS_V3.md` (V01–V19). Machine-readable readiness:
`reports/readiness_v3.json` (regenerate with `dci1v3.cli readiness`).

Registered confirmatory generation has **not** run (item 66). The four real
replications stand at `QUALIFIED`; everything beyond qualification that
needs the GPU or humans is listed under *Work not executed*.

## 1. Implementation root and files changed

Root: `dci1/src/dci1v3` (package `dci1v3`), tests `dci1/tests_v3`, access
tool `dci1/tools/build_topics_v3.py`. Introduced in commits `85fe950` and
`f0b2443` on `feat/unified-vllm-backend` (171 files, ~37.7k insertions —
these commits also brought the previously untracked v2 module and study
documents under version control, repairing the v2 provenance defect named
in prereg §33).

## 2. Model repositories, revisions, execution order

| # | Model key | Repository | Revision |
|---|-----------|------------|----------|
| 1 | `gemma-3n-e2b-it` | google/gemma-3n-E2B-it | `5e092ebca197cdcd8d8b195040accf22693501bc` |
| 2 | `qwen3-4b` (hybrid, thinking disabled) | Qwen/Qwen3-4B | `1cfa9a7208912126459214e8b04321603b3df60c` |
| 3 | `qwen3-4b-instruct-2507` | Qwen/Qwen3-4B-Instruct-2507 | `cdbee75f17c01a7cc42f958dc650907174af0554` |
| 4 | `gemma-3n-e4b-it` | google/gemma-3n-E4B-it | `c1221e9c62e34a43ab7ffacd1be0ea71f126ef10` |

Fixed in the signed registration manifest
(`evidence/dci1-v3/registration/manifest.json`, record hash
`ba1a3a36…b756`, producing commit `85fe950`) before any qualification.
E2B-first and the E2B stop rule are enforced mechanically
(`engine/dispatch.py::_assert_execution_order`; tested).

## 3. Scientific dependency isolation

`dci1v3` imports no earlier DCI implementation — enforced by AST scan
(`tests_v3/test_transcription.py::test_no_v2_imports`) over every module.
The only authorised v2 reads are (a) the carry-over operation's
byte-hashing of the E2B packet and the v2 instrument files (item 2), and
(b) the one-off access-control tool outside the package (V03).

## 4. Shared generic infrastructure

`exploratory/vllm_backend` via its subprocess seam (plan.json +
design.jsonl → rows.jsonl), executed by the pinned interpreter in
`environments/backend/.venv` (vLLM 0.15.1+rocm720 / torch 2.9.1+rocm7.2,
wheels pinned by `environments/backend/vendor/MANIFEST.sha256`). Nothing
scientific crosses the seam except prompt text and seeds.

## 5. Canonical interface, state machine, verification, locking

* **Interface:** `dci1v3.cli` — 17 operations + `register`/`readiness`,
  each dispatching through `engine/dispatch.py` (the item-5 production
  path). No command calls generation, storage, selection, masking,
  analysis, or reporting directly.
* **State machine:** `engine/transitions.py` — the item-6 sequence with
  signed, write-once stage records at the §27 filenames; every stage
  verifies its predecessor's content hash AND HMAC signature plus stage
  identity, PASS status, model identity/revision, producing commit,
  environment digest, input hashes, and (post-freeze) the freeze binding.
  A terminal report mechanically disables all generation commands.
* **Evidence verification:** `engine/verify.py` — one canonical routine,
  10 named checks covering the item-7 contract (protocol/model identity,
  stage chain with signatures, git provenance + invoked-source membership,
  dependency + interpreter, hardware class, cache integrity incl.
  prompt-plan membership / draw identities and counts / content hashes /
  duplicate refusal, artifact-state and type legality, required and
  stale/unexpected paths, durable storage, namespace). It runs inside
  every mutating dispatch, before and after the stage function; a prior
  success authorises nothing.
* **Writer locking:** `engine/locks.py` — per (study, model, operation)
  `flock`, non-blocking, cross-process (tested with real second
  processes; concurrent mask creation has exactly one winner).

## 6. Git cleanliness and uv provenance

`engine/gitinfo.py`: `git status --porcelain` must be empty and every
loaded `dci1v3` source file must exist byte-for-byte at
`dci1/src/dci1v3/…` in HEAD of the context's repository. Production code
contains no allow_dirty flag or bypass — synthetic tests satisfy the same
checks against a committed scratch repository. `engine/environment.py`:
`uv.lock` + committed `uv export --frozen` output are the canonical
dependency representation; missing or empty representations fail closed;
a dependency change provably alters the digest (tested).

## 7. Gate 1, sequestered access control, cache/selection, pseudo-runs

* **Gate 1** (`stages/gate1.py`): forty-case boundary suite (40/40),
  three-process determinism at 1.000, closed natural reservoir
  (pre-screen + frozen 300-response validation set), seeded
  `min(150, N_c)` per class, one-sided 95% Wilson bound ≤ 0.10, with
  `MEASUREMENT_NOT_ESTABLISHED` / `MEASUREMENT_EVIDENCE_INSUFFICIENT`
  exactly per items 33–34. Human labels enter via `--annotations`;
  without them the gate reports PENDING_HUMAN and does not pass.
* **Sequestered topics** (`topics/sequestered.py`): opaque manifest only
  (96 ids + strata + pre-existing content hashes); fail-closed when
  missing; executable no-materialisation check on every load.
* **Cache and primary selection** (`generation/cache.py`,
  `stages/select.py`): predetermined draw identities with frozen per-draw
  seeds; repair only by exact identity; duplicate identities refused
  before mutation; rows carry every item-56 field including all verifier
  verdicts with the frozen instrument hash. The selector is
  `H("primary-root", model-id, prompt-hash) mod 16` and structurally
  receives nothing else (signature-tested).
* **Pseudo-runs** (`stages/sensitivity.py`): separate `dci1v3:pseudo:v1`
  domain and separate derived path; primary selection untouched; no
  confirmatory claim.

## 8. Masking and unmasking custody

`stages/masking.py`: reservation (O_EXCL) written and made durable
**before** any mask randomness; existing reservation/key/view fails a
second attempt before key generation (tested in-process and
cross-process); system-randomness per-block permutation of the four
primary arms with the ≥-half-blocks-changed assertion; key write-once with
its hash recorded at write time; masked view excludes every
arm-identifying field (V11). Unmask: reservation before key access;
`open_mask_key` is the single opener (builtins-open audit test: exactly
one open); the unmask record carries timestamp, mask-key hash, and
analysis-code hash; re-masking after unmasking fails before mutation;
`pilot_mask` and `confirmatory_mask` are disjoint namespaces with a
byte-identity isolation check.

## 9. Durable restoration and artifact states

`engine/store.py`: incremental byte-verified replication after every
operation (including failed ones), `assert_replicated` in every dispatch,
and `restore` reproducing every committed row byte-for-byte (drilled in
the pilot and again in the e2e suite). `engine/artifacts.py`: append-only
ledger, monotone `generated → committed → accepted (→ superseded)`,
illegal moves refused at append and re-checked at verification.

## 10. Canonical test results

`dci1/.venv/bin/python -m pytest` — **82/82 v3 tests** and **131/131 v2
tests** green (2026-08-17). The v3 suite covers every item-62 area:
transcription (registered values, allocation formulas, no-v2-imports),
verifiers/Gate 1 (boundary 40/40, 288 witness compositions, 44
wording-equivalence combinations, parse-independence signatures),
state machine (illegal transitions, tampered hash and tampered signature,
terminal lockout, single-shot records, E2B ordering and stop rule),
engine (cross-process locks, dirty refusal, source-membership divergence,
uv fail-closed + digest change, write-once, row-hash refusal, durable
drill, artifact monotonicity, namespace separation), selection/analysis
(blind selector formula, pseudo separation, Gate 2A/2B tie-breakers,
§12 resampling-unit/signature/variance checks, degenerate-contrast
reporting, guarded claims vocabulary, codebook domains and post-treatment
refusal, taxonomy priority order, deterministic report reproduction),
masking custody (8 tests), and the lifecycle below.

## 11. Synthetic end-to-end lifecycle (items 63–64)

`tests_v3/test_lifecycle_e2e.py`, through the actual public entrypoints
(`dci1v3.cli`), synthetic namespace, real inference replaced by the
synthetic adapter and nothing else:

    register → qualify → pilot (72 cells / 1,152 draws; tamper probe;
    restore drill; pilot_mask cycle) → prescreen (3 cap runs × 96 +
    1,056 severity cells; cap 512 selected; 8 plausible families) →
    gate1 (PENDING_HUMAN → harness labels → PASS) → gate2a (4,224
    responses; n*, m*, family admission) → gate2b (composed validation;
    3 references) → freeze → generate (2,304 cells / 36,864 cached
    draws) → select-primary (2,304) → mask → masked-analysis (10,000
    resamples) → unmask (single) → final-analysis (masked outputs
    reproduced byte-for-byte, then true labels) → pseudo-runs → greedy
    (384) → verify-evidence

reaching `UNMASKED_ANALYSIS`. Adversarial attempts, all failing before
prohibited mutation or key access: second mask creation; second unmask;
concurrent duplicate cached-draw write; dirty-worktree artifact
production; tampered predecessor PASS record; tampered predecessor
signature. Pilot and confirmatory paths are asserted to be the same
production functions.

## 12. Authorised E2B carry-over (item 2)

`carry-over` ran for E2B and **accepted** the complete 150-item v2 packet
(`carry_over.json`; the first, refused record — an implementation defect
in the singular-wording comparison, no scientific consequence — is
preserved as `superseded_non_evidence`). Recorded hashes:

| Surface | SHA-256 |
|---|---|
| Source packet (150 items) | `9790028ec0b17c5adc525c74ac12a06029a667345bb2eda53e56498468204004` |
| Construct definition | `82c1a20976796a0dd02ccc4898a59db097ea6df7739066e553a1f304d46de305` |
| Normalisation (`alpha_runs` source) | `7bb2879c1e23cc43bffbee025efb21ee50b45d7c13bd0febf31db393d62d365b` |
| Target verifier (`s0_count` source) | `092285e3870b90311f87773f8ec0898ecba26ec5cc4ca5d79b7d6d79c28822a2` |
| Boundary specification | `757710a8857321dc43eb61c1dadc37763827f1031c28a1ad697c6d91041b404b` |
| v2 `target.py` / `words.py` | `67d0c590…ecc1` / `35996f70…34c0` |

The packet's **annotation** remains human work (below).

## 13. Current model-replication states and terminal outcomes

All four registered replications: **`QUALIFIED`** (signed records,
producing commit `85fe950`, hardware class `gfx1100-rx7900xtx`,
environment digests recorded). `verify-evidence`: VERIFIED on all four
trees. **No v3 terminal outcome has been reached.** (v2's four terminal
replications are closed history under `evidence/dci1-v2/`, untouched.)

## 14. Work not executed (hardware- or human-dependent)

1. **GPU stages** for the real replications, in order per model:
   `pilot` → `prescreen` → `gate1` → `gate2a` → `gate2b` → `freeze`
   (E2B first; its `REFERENCE_POOL_MISMATCH` / `COMPOSED_HEADROOM_FAILURE`
   would stop the study).
2. **Gate 1 human annotation** — three annotators over the seeded
   sample; for E2B the carried 150-item packet
   (`evidence/dci1-v2/gemma-3n-e2b-it/prefreeze-apparatus/calibration/gate1/`)
   is the authorised evidence once labelled; labels enter via
   `gate1 --annotations`.
3. **Registered confirmatory generation** — prohibited at readiness
   (item 66); mechanically locked behind Gate 3 and canonical
   verification.

## 15. Conditions still blocking freeze or confirmation

Per model: Gate 0 (pilot), the regime screen (cap + curves + ≥3 plausible
families), Gate 1 (human labels + bounds), Gate 2A (eligible n*, m*, ≥3
admitted families), Gate 2B (≥3 composed-valid families) — each with its
registered terminal status if failed. Nothing else blocks: the apparatus,
custody, provenance, and analysis machinery are complete and exercised
end to end.

---

## Addendum (2026-08-17): amendment A1 — single-annotator Gate 1

After this report was written and **before any human annotation began**,
the researcher amended Gate 1 from three annotators to **one independent
human annotator per model** (DECISIONS_V3.md, Amendments, A1). Gate 1 now
measures human-to-verifier disagreement from one independent judgment per
item; the sampled packets, verifier-class stratification, one-sided 95%
Wilson bound, ≤ 0.10 threshold, exhausted-class rules, and all other
registered rules are unchanged. The annotations contract is
`{item_id: ["pass"|"fail"], "face_validity": [bool]}` (length exactly 1,
enforced). References to "three annotators" elsewhere in this report
describe the pre-amendment design and are retained as the historical
record.

## Addendum (2026-08-17): amendment A2 — autorater-assisted Gate 1

No independent human annotator is available. Gate 1 now runs the
autorater-assisted verifier workflow (DECISIONS_V3.md, Amendments, A2):
deterministic development/calibration split of the existing response pool,
one configured autorater for development-phase disagreement inspection,
a study-level verifier-freeze manifest, held-out calibration reported as a
full 2×2 contingency with no automatic threshold, and an explicit
researcher approval closing the gate. The A1 human packet, reviewer GUI,
and single-annotator criterion are preserved verbatim behind
`human-audit` for future independent validation. Claim boundary, stated
in every gate, freeze, and analysis record: **"The frozen deterministic
verifier was developed and evaluated on held-out responses against the
specified autorater under the registered configuration. Independent human
validation is unavailable."** Autorater agreement is never presented as
human validation or ground truth, and no language model judges any scored
outcome.

## Addendum (2026-08-19): execution complete — see RESULTS_V3.md

The registered pipeline has since run to completion under the amended
Gate 1 (A2/A3 line, autorater-config/4, verifier freeze `334bb2b18079`):
`gemma-3n-e2b-it` and `gemma-3n-e4b-it` completed every stage through
`UNMASKED_ANALYSIS` with `verify-evidence` VERIFIED; `qwen3-4b` and
`qwen3-4b-instruct-2507` reached the registered terminal outcome
`REFERENCE_POOL_MISMATCH` at Gate 2A. Statements above that generation
has not run, that no terminal outcome exists, and the item-14/15 lists
of unexecuted work are the historical record of the readiness snapshot.
The final results, claim outcomes, measurement-validity caveats, and
remaining blockers are reported in **`RESULTS_V3.md`** (with the
evidence index of signed record hashes).
