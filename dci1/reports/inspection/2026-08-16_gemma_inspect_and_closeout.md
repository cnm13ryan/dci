# DCI-1: inspection of the Gemma pair, and study close-out under protocol v2

Date: 2026-08-16 (evening). Companion to `2026-08-16_qwen_explain_and_inspect.md` (design tutorial and Qwen inspection; the design explanation is not repeated here).
Scope: `gemma-3n-e2b-it` (google/gemma-3n-E2B-it @ `5e092ebc…`) and `gemma-3n-e4b-it` (google/gemma-3n-E4B-it @ `c1221e9c…`).
Evidence discipline unchanged: no raw response text, no prompt text, no mask key, no arm-level pilot quantity, no analysis estimate/interval/claim value was read. All numbers below come from gate records, integrity reports, backend sidecars, and structural (count/hash/schema/timestamp) inspection.

---

## 1. Five things you most need to know

1. **The Gemma pair did not "converge" to results — both reached a terminal outcome one gate *earlier* than the Qwen pair.** Both failed **Gate 0**, the procedural pilot, on the §17 truncation ceiling: 13.9% (E2B) and 15.0% (E4B) of pilot generations stopped at the frozen 400-token limit, against the registered ceiling of 0.10 [v2 §17, condition 3] (`prefreeze-apparatus/pilot_report.json`: `c3_truncation_at_or_below_ceiling: false`, `truncation_share_pool` 0.1389 / 0.1502; both `passed: false`). Every other pilot condition passed, 7/8. All four registered models are now terminal — Qwen at Gate 2, Gemma at Gate 0 — and confirmatory generation is permanently locked under protocol v2.

2. **The Gemma failure is model verbosity, not apparatus malfunction — which exposes a taxonomy gap in the preregistration.** The pipeline ran end to end flawlessly (1,152/1,152 generations per model, zero technical failures, complete pools, seals, restore drills, `verify-evidence` ok). What failed is that gemma-3n writes long answers under the frozen 400-token decoding budget [v2 §4]. §17 prescribes "repair the apparatus and rerun" for a Gate-0 failure, and §26 describes the Gate-0 terminal outcome as "the pipeline does not run end to end" — neither description fits a model that simply talks past the token budget, and the budget itself is a frozen scientific field the amendment forbids adjusting. Generation is seed-deterministic, so a §17 rerun would reproduce the identical rate. The registered gate binds; the registered *interpretation text* mischaracterises this failure mode. Reported as a prereg-vs-reality gap, not reconciled.

3. **The §17 ordering slip touched both Gemma models, but the decisions register discloses only one.** D27 discloses that E2B's calibration (1,824 responses, committed) was generated *before* its Gate-0 verdict, and claims "E4B's calibration was correctly withheld after its Gate 0 failure." The artifacts show otherwise: an E4B calibration generation was **started and produced 64 real responses** (two 32-row chunks, all `outcome: OK`) at 20:18–20:19 UTC — 0.3 seconds after E2B's calibration event, and *before* E4B's own qualification (20:21 UTC) and pilot (20:39 UTC) — then stopped. Nothing was committed (no `pool.jsonl`, no runrecord event, no durable copy), but the raw backend artifacts sit in the evidence tree (`gemma-3n-e4b-it/prefreeze-apparatus/calibration/pool/gen_round0/rows.jsonl`, 64 rows). "Withheld" is true of *commitment*; it is not true of *generation order*.

4. **E2B is the scientifically tantalising model.** It is the only one of the four with a genuinely admissible operating point on the model side: target headroom **in band** (n=3, solo failure 0.323 ∈ [0.15, 0.50]) and a followable focal constraint (m=7 at 0.229), healthier item behaviour (32% ceiling, 10% floor vs Qwen's 86% ceiling), and a **full 150-item human-annotation packet with no shortfall**. Its Gate 2 failed on exactly one condition: the reference pool — all twelve candidates fail 81–100% of the time, closest C1 at distance 0.583 vs the ±0.10 window (`calibration/gate2.json`). Across all three calibrated models, the reference pool is uniformly far harder than either A or B: that is now a replicated finding about this constraint family, and it is the single design element a v3 must fix.

5. **A new integrity finding that spans all four models: the D22 environment digest is degenerate.** Neither the scientific nor the backend interpreter has `pip` (both are uv-managed venvs), and `_pip_freeze` silently swallows the failure into an empty list — so the "environment digest" records **zero packages for both interpreters** and is identical (`d3df1a86…`) across all four models despite a documented mid-study environment upheaval (pyarrow removed from the repo-root venv after it broke the historical study's baselines; a new `dci1/.venv` created at 20:23 UTC — *after* the Qwen artifacts and E2B's calibration were already written against a `SCIENTIFIC_PYTHON` path that did not yet exist). The digest cannot detect package changes, which was its entire purpose as the container-image substitute [v2 §28; D22]. Data integrity is unaffected (all content hashes verify); environment *provenance* is weaker than the record claims.

---

## 2. Ordering check and unmasking readiness

**Answer first: nothing is masked anywhere in this study, nothing awaits unmasking, and the ordering question has collapsed — all four models' pre-freeze behaviour is now fully revealed, and any future design work necessarily proceeds with that knowledge.**

- Unmasking records exist for all four pilot trees, all actor `gate0-pilot`, all mask→commit→unmask within the same second (E2B 20:26:39Z, key `22d3377e…`; E4B 20:39:51Z, key `802d60af…`; runrecord = study_manifest = unmasking_record hashes consistent for both). Apparatus exercises, as for Qwen.
- No freeze record, no confirmatory tree, no confirmatory mask exists for any model. `readiness` reasons are moot: Gate 0 (Gemma) and Gate 2 (Qwen) are terminal.
- The previous report's recommendation — seal Gemma calibration before v3 discussion — was overtaken by events in two ways: (i) `dci1/` was **not** committed to git first (still 0 tracked files at HEAD `094922b`), so Gemma's records are again `writer_dirty: True`; (ii) E2B's calibration ran out of order (D27) and E4B's was aborted mid-flight rather than never started (§1.3 above). What survives: E2B's calibration and gate records are committed, hashed, and durable-mirrored, so their *values* are fixed and auditable even though their production order and writer state are blemished.
- Consequence for a v3: it will be designed in full view of all four models' calibration behaviour. That is unavoidable now and acceptable *only* because a v3 is a new registration [v2 §18]; nothing in v2 can be adjusted retroactively.

---

## 3. What was verified (apparatus integrity)

**PASS structurally for both Gemma trees — the Gate-0 verdict is an honest behavioural failure, not an integrity failure.**

| Check | gemma-3n-e2b-it | gemma-3n-e4b-it | Source |
|---|---|---|---|
| `verify-evidence` | ok=true, exit 0 | ok=true, exit 0 | `dci1.cli verify-evidence --freeze prefreeze-pilot` |
| Cache records (12×6×16) | 1,152 / 1,152 | 1,152 / 1,152 | `prefreeze-pilot/cache/generations.jsonl` |
| Row-id / seed uniqueness | 1,152 / 1,152 unique | same | same file |
| Pool completeness (indices 0–15) | 72/72 cells, no gaps | same | same file |
| Single pinned revision on every record | `5e092ebc…` ×1152 | `c1221e9c…` ×1152 | field `model_revision` |
| Accepted table | 72 rows, (block,arm) unique, 12×6, no text column | same | `derived/primary/accepted.parquet` |
| Analysis tables (structure only) | 29 rows = F1–F6 membership | same | `derived/primary/analysis.parquet` |
| Durable mirror byte-identity | identical (3 raw layers) | identical | `durable_root/…` vs evidence |
| Replication record | 20:26:39Z, durable_root_local | 20:39:51Z | `integrity/replication.json` |
| Masked view labels balanced, no role-revealing columns | 12 × each of 6 labels | same | `masking/masked_view/masked_rows.jsonl` |
| Pilot prompt bytes identical to Qwen's | prompts manifest `b049adca…` — same hash as both Qwen trees | same | `study_manifest.json` |
| Gate-0 conditions | 7/8 pass, **c3 fail** | 7/8 pass, **c3 fail** | `pilot_report.json` |
| CPU protocol tests | 131 passed (under `dci1/.venv`) | shared | `pytest tests/ -q` |

Duplicate categories: zero duplicated row identities, zero duplicated seeds, zero missing generations, and — remarkably — **zero identical outputs within pools** for both models (`integrity/cache_report.json`; my per-cell hash count agrees).

Qwen trees rechecked and untouched since the previous inspection: derived-parquet mtimes still 19:10:12/19:13 UTC, `study_manifest.json` stage hashes and mask-key hashes byte-for-byte as previously recorded.

---

## 4. Qualification and the D26 engineering deviations

Both models: **QUALIFIED, zero problems**, 8/8 probes OK, none truncated; `enable_thinking` verified **inert** against the real gemma template (all renders byte-identical; tail `<bos><start_of_turn>user … <start_of_turn>model\n`); decoding/dtype/revision consumed; parser null (whole response scored, per S0 [v2 §9]) (`qualification_report.json`, both).

D26, verified in code and artifacts: `limit_mm_per_prompt` deliberately **unset** for both gemma specs because zeroing every modality crashes the pinned vLLM 0.15.1 wheel at engine init (the wheel's `Gemma3nForConditionalGeneration.forward` dereferences `inputs_embeds` unconditionally); the unused multimodal path stays enabled; the wheel is not patched (`models/adapters.py` comments; a `blocked: true` engine sidecar from a failed 20:02 UTC attempt survives at `gemma-3n-e4b-it/…/calibration/pool/gen_round0/rows_engine.json`, engine error "Engine core initialization failed"). E4B alone runs at `gpu_memory_utilization = 0.95` (weights 14.93 GiB left a negative KV budget at 0.85 on the 24 GiB card). Engineering envelope, not science; decoding and context limits identical across all four models.

---

## 5. The D27 ordering violation, precisely timed

Reconstructed from `runrecord.jsonl` (UTC) and file mtimes (local BST = UTC+1, converted):

| UTC time | Event |
|---|---|
| 20:02:09 | E4B: failed engine attempt writes `blocked: true` sidecar (pre-D26-resolution era) |
| 20:08:24 | E2B qualification → QUALIFIED |
| 20:18:21 | **E2B calibration generation completes: 1,824/1,824 accepted** — before any E2B pilot exists |
| 20:18:23 | E2B calibration verdict recorded (n=3, m=7, refs `[]`, gate2_passed false) |
| 20:18:23.9 | **E4B calibration plan.json + design.jsonl written** — 0.3 s later, before E4B qualification |
| 20:19:23–20:19:50 | **E4B calibration generates 64/1,824 rows** (two +32-row chunks in `backend.log`), then stops |
| 20:21:18 | E4B qualification → QUALIFIED |
| 20:23:05 | `dci1/.venv` created (the environment repair) |
| 20:26:39 | E2B pilot tree: 1,152 generations, mask, commit, unmask; Gate 0 verdict **FAILED** (report mtime 20:26:40) |
| 20:39:51 | E4B pilot tree: same cycle; Gate 0 **FAILED** (report mtime 20:39:52) |

So: §17's ordering ("a procedural pilot runs before any calibration generation" [v2 §17]) was violated for **both** Gemma models — E2B completely (full calibration committed pre-pilot, as D27 discloses), E4B partially (64 rows generated pre-qualification and pre-pilot, then aborted; not disclosed; D27 affirmatively says "correctly withheld"). Mitigations that are real: generation is deterministic in the frozen seeds, so a post-pilot regeneration would be byte-identical (D27's argument, and the seed machinery is tested); the E4B fragment was never committed to any study record; and both models' Gate-0 verdicts are terminal anyway, so no calibration value feeds any downstream decision under v2. Mitigations do not make the register accurate: **D27 should be amended to disclose the E4B attempt**, and the leftover `gen_round0` artifacts should be explicitly labelled (not deleted) as an uncommitted out-of-order fragment.

---

## 6. Calibration and gates (E2B only; E4B has none and never will under v2)

E2B, from `calibration/gate2.json`, `gate1.json`, `solo_rates.json`, `pool/pool_integrity_report.json` (1,824/1,824 solo responses, unique seeds, zero within-pool duplicates):

- **Target A**: solo failure 0.490 / 0.333 / 0.323 at n=1/2/3 → n=3 selected at **0.323, in band [0.15, 0.50]** — the only model of the four with genuine headroom.
- **Focal B**: 0.229 / 0.198 / 0.073 / 0.063 at m=7/8/9/10 → m=7 selected at **0.229, in band** — followable but non-trivial.
- **References**: all twelve candidates 0.8125–1.0 solo failure; closest C1 at distance **0.583** vs the ±0.10 window; **0 admitted, 3 required** → Gate 2 FAILED on this single condition, recorded as "a scientific result, reported as such" [v2 §18, §26].
- **Gate 1 machine parts**: determinism 1.000 over 1,824×3; boundary suite 40/40; parse independence verified. **Human packet: 150 items, no shortfall** (75/75 achievable because E2B actually fails A often enough) — status PENDING_HUMAN, annotators still needed. Item behaviour: ceiling 32.3%, floor 10.4%, identical-verdicts 42.7% — the healthiest measurement regime of the four models.
- **D27 procedural note applies** to all of the above: these values were generated before E2B's Gate-0 verdict existed.

E4B: no committed calibration (no `pool.jsonl`, no integrity report, no solo rates, no gate records; runrecord silent) — correct *as commitment* under Gate-0 terminality; see §5 for the uncommitted 64-row fragment.

---

## 7. Diversity, compliance, stability

- **Diversity (content hashes only): perfect, both models.** Every one of the 72 cells per model has 16/16 distinct responses (min = median = max = 16); zero identical outputs within pools; the four-model spectrum is now: qwen3-4b mean 14.39 distinct/cell (min 5) < instruct 15.90 (min 13) < both gemmas 16.00 (min 16). No cell anywhere in the study collapses; the stochastic-stability layer would have had signal everywhere. The gemma diversity is partly *explained by* the verbosity that killed Gate 0 — long stochastic answers rarely collide.
- **Compliance / truncation**: finish reasons `stop`/`length`: E2B 992/160 (13.9%), E4B 979/173 (15.0%) (`cache/generations.jsonl`). Token counts: E2B min 50 / median 190 / p95 400 / mean 207; E4B min 49 / median 201 / p95 400 / mean 219 — versus Qwen medians of 75 and 108. The p95 *at* the cap is the whole Gate-0 story: gemma-3n's answer style does not fit a 400-new-token budget on these prompts. Per-arm rates: not viewed (§17 pilot discipline, as before).
- **Stability**: no pseudo-runs exist for either Gemma model (as for Qwen; the R=1000 frozen count applies to the confirmatory stage that never ran). Machinery remains validated on synthetic data only.

---

## 8. Deviations (new items beyond the Qwen report's list)

1. **D27 under-disclosure (blocking for the register's accuracy):** E4B calibration generation was attempted and partially executed out of order; D27 records the opposite ("correctly withheld"). E2B's disclosed slip is confirmed exactly as recorded.
2. **Environment digest degeneracy (all four models):** empty package freezes for both interpreters (no `pip` in uv venvs; `_pip_freeze` returns `[]` on any failure); identical `environment_record_hash` across a documented environment change; at Qwen-artifact time the recorded `SCIENTIFIC_PYTHON` path (`dci1/.venv`) did not exist. D22's digest cannot serve its stated function. Backend pins remain independently captured (vendored-wheel sha256 + `uv.lock` hash).
3. **D23 text stale:** the register still names the repo-root `.venv` as the scientific interpreter; the code now points at `dci1/.venv` (created 20:23 UTC, for the documented reason that pyarrow in the repo-root venv broke the historical study's baselines). The interpreter switch itself is reasonable; the register was not updated.
4. **Prereg §17/§26 taxonomy gap:** the truncation ceiling is written as an apparatus-repair condition and the Gate-0 terminal outcome as "pipeline does not run end to end"; the realised failure is frozen-budget model verbosity, unrepairable without a new protocol version. The gate's *binding force* is respected by the implementation (fail-closed, terminal); its *description* does not fit.
5. **Git state unchanged:** `dci1/` still untracked at the same HEAD; every Gemma artifact again `writer_dirty: True` with a code commit that contains none of the code. The prior report's blocking recommendation stands, now retrospectively unfixable for all four models' pre-freeze records.
6. Minor: no `report.json` in either Gemma pilot tree (same asymmetry as the instruct tree; only qwen3-4b has one); the pilot freeze stubs carry the confirmatory `pseudo_run_count: 1000` while no pseudo-runs exist (same cosmetic trap as before).

---

## 9. What this closes, and what remains open

**Closed:** DCI-1 v2 is complete as a protocol execution. All four registered replications reached preregistered terminal outcomes without one confirmatory token being spent and without one frozen field being adjusted: Qwen pair — "Regime not found" at Gate 2 (target at ceiling; reference pool uniformly too hard); Gemma pair — Gate 0 truncation ceiling (verbosity under the frozen 400-token budget). The apparatus itself is validated end-to-end on all four models and on synthetic data with a known recoverable effect.

**The replicated scientific residue, stated carefully:** across three independently calibrated models, every one of the twelve reference candidates (initial-letter, suffix, length, doubled-letter rules) is dramatically harder to satisfy than either the target ("*however* exactly n times") or the focal constraint ("words ≤ m letters") — solo failure 47–100% versus 2–33%. The candidate-pool difficulty structure, not model idiosyncrasy, is what makes the registered design inexecutable. Any v3 must re-match the reference pool to the focal constraint's difficulty; for gemma-3n it must additionally resolve the output budget (larger `max_new_tokens`, or a brevity instruction — itself a new constraint with design consequences); and E2B is the natural first target, being the only model with demonstrated headroom on both A and B.

**Still open under v2 (and now permanently):** every registered estimand, for every model. Unmasking adds nothing; there is nothing masked.

---

## 10. Open questions for you

1. **Amend D27?** The register misstates E4B's calibration history (§5). Amending a decisions register post hoc must itself be a dated, disclosed correction. *Blocks:* the register's accuracy for any future audit or release.
2. **Label or quarantine the E4B fragment?** `gemma-3n-e4b-it/prefreeze-apparatus/calibration/pool/gen_round0/` holds 64 uncommitted out-of-order generations plus a stale `blocked` sidecar from 20:02 UTC. Convention elsewhere in the tree is rename-with-`-v0-superseded`, never delete. *Blocks:* release hygiene.
3. **Fix the environment digest before any v3?** Options: record `uv.lock`/`uv export` hashes for both interpreters instead of `pip freeze`; fail closed when a freeze comes back empty; and update D23. *Blocks:* whether v3's environment provenance means anything.
4. **Commit `dci1/` at last?** Third time this is the blocking item: no registered artifact — including any v3 gate record — can be validly produced from an untracked module. *Blocks:* everything registered, going forward.
5. **Register v3?** The data now support a concrete shape: keep A and B; rebuild the reference pool to target ~0.2–0.35 solo failure (the current pool's *easiest* member fails 47–81% across models); revisit the token budget for verbose models; run E2B first. Only you can register it. *Blocks:* the scientific question itself.
6. **Human annotation for E2B's Gate 1?** Its 150-item packet is complete and blinded, and unlike the Qwen packets it has no fail-class shortfall. Annotating it would complete the only fully-formed Gate-1 measurement in the study — useful for v3 verifier validation even though v2 is terminal for E2B. *Blocks:* reusable measurement-validity evidence.
