# DCI-1: design explained, and inspection of the completed Qwen work

> **Postscript (2026-08-16, evening):** the Gemma pair has since run and both reached a terminal outcome at Gate 0 (§17 truncation ceiling). See the companion report `2026-08-16_gemma_inspect_and_closeout.md`, which also supersedes this report's §2 recommendation on Gemma sequencing and adds two study-wide integrity findings (D27 under-disclosure; environment-digest degeneracy).

Date: 2026-08-16.
Scope: `Qwen3-4B` (`qwen3-4b`) and `Qwen3-4B-Instruct-2507` (`qwen3-4b-instruct-2507`), the two runnable registered models of DCI-1 v2 under amendments A1/A2 and Addendum A.
Author's evidence discipline: no raw response text, no prompt text, and no mask key were read at any point; every outcome-adjacent number below comes from gate records, integrity reports, and structural (count/hash/schema) inspection. No arm-level pilot quantity was viewed (why: §7.3 below).

---

## 1. Five things you most need to know

1. **There is no confirmatory run to inspect.** The status table in the inspection brief says "generation complete" for both Qwen models; the artifacts say otherwise. Both models terminated at **Gate 2 with the preregistered terminal outcome "Regime not found"** [v2 §18, §26], no freeze record was ever produced, and confirmatory generation is locked and was never executed (`evidence/dci1-v2/<model>/` contains only `prefreeze-apparatus/` and `prefreeze-pilot/`; no 12-hex freeze tree exists; `cli readiness` reports `unlocked: false` for both). What *is* complete: qualification, the 1,824-response calibration run, and the 1,152-generation Gate-0 procedural pilot, per model.

2. **"Regime not found" is a genuine scientific result, not a malfunction.** Both checkpoints satisfy the target constraint ("use *however* exactly n times") almost perfectly — best-case solo failure 12.5% (`qwen3-4b`, n=3) and 7.3% (instruct, n=3), below the required [0.15, 0.50] headroom band — while every one of the twelve reference candidates is far harder than the focal constraint (closest: C10, distance 0.146 and 0.167 against a ±0.10 admission window; zero candidates admitted, three required) (`prefreeze-apparatus/calibration/gate2.json`, both models). The design detected, before spending the confirmatory budget, that it could not measure what it set out to measure on these models.

3. **The premise "Qwen3-4B-Base is a pretrained base model" is contradicted by the artifacts.** The registered checkpoint `Qwen/Qwen3-4B` (revision `1cfa9a72…`) is a post-trained **hybrid chat/thinking model** run in no-thinking mode: its qualification report shows a live chat template (`<|im_start|>user … <|im_start|>assistant`) and a live `enable_thinking` switch that, set `False`, injects a pre-closed `<think>\n\n</think>` block (`prefreeze-apparatus/qualification_report.json`, `template_probe`). The completed pair is therefore *hybrid-checkpoint-in-no-thinking-mode vs. pure-instruct-checkpoint* — a post-training-recipe difference, not a base-vs-instruct difference. Most of the "base-model risks" in the brief dissolve accordingly (§5 below).

4. **Apparatus integrity passes everything I could check.** `verify-evidence` returns ok for both pilot trees; 1,152/1,152 cache records per model with unique row identities and unique seeds; 72/72 accepted rows with unique (block, arm) keys; pool index sets complete (0–15 per cell); durable mirrors byte-identical with valid `.sha256` sidecars; 131/131 CPU protocol tests pass. One systemic caveat: **every derived artifact is stamped `writer_dirty: True`, and the entire `dci1/` module is untracked in git** (0 tracked files), so the recorded `analysis_code_commit` (094922b) does not contain the code that produced the artifacts. Tolerated for the non-registered pilot; fatal, by the protocol's own refusal rules, for any registered artifact [Addendum R20/R50].

5. **For these two models, the registered question is now permanently unanswerable under this protocol version.** Gate 2 failure is terminal per model; the design must not be adjusted post hoc [v2 §18]. Proceeding scientifically requires either (a) running the two Gemma models under the same frozen protocol (their Gate 2 may fail the same way), and/or (b) registering a new protocol version with a different target grid or reference pool. Nothing that unmasking could reveal exists to be revealed.

---

## 2. Ordering check and unmasking readiness (brief §3)

**Answer first: no confirmatory unmasking exists or can exist; the pilot trees were mask-cycled and unmasked as an apparatus exercise; no Gemma records of any kind exist; and Qwen calibration outcomes are already fully revealed while Gemma's calibration is entirely open — which is a real, but bounded, ordering exposure.**

1. **Unmasking records: yes, for both Qwen models — but only on the non-registered pilot trees.**
   - `evidence/dci1-v2/qwen3-4b/prefreeze-pilot/masking/unmasking_record.json`: unmasked 2026-08-16T19:10:12Z, actor `gate0-pilot`, reason "Gate 0 procedural pilot (non-registered, §17)", mask_key_hash `2c35f68e…`, commitment_hash `e7e09d9b…`.
   - Same for the instruct model at 19:13:05Z (mask_key_hash `44190dd1…`, commitment_hash `64ba4bdb…`).
   - The run records show mask construction and unmasking within the same second (`runrecord.jsonl`, events `mask_constructed` at 19:10:12 / 19:13:05); the masked analysis was executed and committed mechanically, with no human viewing window in between. Masking constraints on *pilot* data therefore no longer bind — but the preregistration's separate pilot discipline ("no contrast of any kind is computed or viewed" on pilot rows [v2 §17]) still does, and I honoured it.
   - There is **no confirmatory masked view and no confirmatory unmasking record anywhere** — because there is no confirmatory data.

2. **Frozen protocol records for the Gemma models: none.** `evidence/dci1-v2/` contains only `qwen3-4b/`, `qwen3-4b-instruct-2507/`, and `_synthetic/`. No `gemma-3n-e2b-it/` or `gemma-3n-e4b-it/` directory exists in either `evidence/` or `durable_root/`. Gate 3 was "not produced" for every model (`REPORT.md` §16). The Gemma pair is blocked upstream of everything on the Hugging Face licence gate (no token on this machine; `DECISIONS.md` A2).

3. **Timestamp comparison: not applicable** (nothing Gemma-side exists to compare).

4. **The flag you asked for, prominently:** Qwen calibration outcomes — solo failure rates for every constraint, the selected n and m, the Gate-2 verdicts — are fully revealed (they are printed in `REPORT.md` and in the open gate records). Gemma's calibration values are not yet fixed. In a preregistered multi-replication design, every design choice for replication k must be demonstrably fixed before outcomes from replications 1..k−1 could influence it; otherwise a sceptic can claim the later replication was tuned toward (or away from) what the earlier ones showed, and the record cannot refute them. **The exposure here is bounded** because Gemma's per-model values (n, m, references) are derived mechanically from Gemma's own calibration data by rules frozen in the registered protocol [v2 §18 Gate 2], leaving no analyst degree of freedom *inside* this protocol version. The live danger is one level up: knowing exactly how and why the Qwen pair failed Gate 2 creates pressure to "fix" the design (target grid, reference pool, admission window) before or during the Gemma runs. Any such change is a new protocol version [v2 §18] and must be registered as one, and must not be informed by Gemma-side peeking either. **Recommendation:** as soon as the Gemma weights are obtainable, run and seal Gemma qualification + calibration + gates under the current frozen rules, before any v3 design discussion is written down; and commit `dci1/` to git first so those records are not produced from a dirty tree (§4 caveat above).

---

## 3. The design explained

*(Design claims cite the preregistration as [v2 §x]. Amendment and implementation facts cite `DECISIONS.md` (decisions D01–D25), `MAPPING.md`, or code, and are marked as such.)*

### 3.1 The question

When you give a language model two rules at once, does *which* second rule you picked change how well the model follows the first rule — even though the two prompts have the same number of rules, the same topic, and the same wording everywhere else? The study names this **directional constraint interference**: "directional" because one rule is designated the outcome (the *target*) and the other the treatment (the *focal* rule), by construction [v2 §2]. Observing it would mean: swapping the focal rule in for a comparable reference rule changes the probability of failing the target rule by at least 0.10 (the smallest effect the study cares about), with the uncertainty interval clear of zero [v2 §11, §15]. Ruling it out would mean: the interval lies wholly inside ±0.10, an *equivalence* finding — which is an affirmative result, not a shrug; "we couldn't tell" (interval straddling both) is declared inconclusive and reported as such [v2 §15]. Crucially, the study is *not* about whether adding more rules degrades compliance (both compared prompts always carry exactly two rules), and not about why the model behaves this way internally [v2 §3].

### 3.2 The vocabulary

- **Constraint**: an instruction written so that a fixed computer program can decide pass/fail — e.g. "Use the word *however* exactly 3 times" is checkable by counting; "be polite" is not a constraint in this study's sense [v2 §1].
- **Target constraint A**: the constraint whose compliance is the measured outcome. Here: "Use the word *however* exactly n times", n calibrated per model from {1,2,3} [v2 §5, §18].
- **Focal constraint B**: the constraint whose *presence* is the treatment. Here: "Every word in the answer must have at most m letters", m calibrated from {7,8,9,10} [v2 §5].
- **Reference constraint R**: a stand-in used instead of B to form the comparison — e.g. C10, "No word in the answer may end with the letters ly" [v2 §5]. Three references are admitted per model at calibration, matched to B on solo difficulty (±0.10), instruction length (±20%), and whole-answer scope [v2 §18].
- **Wording**: one of four frozen phrasings of the same rule, verified to produce identical verifier behaviour on twenty test responses — so the estimand averages over surface phrasing instead of being hostage to one [v2 §5, §29].
- **Topic**: one open-ended question the model answers, e.g. a short everyday-science question answerable in 60–120 words [v2 §6].
- **Subject stratum**: one of twelve declared subject areas (everyday science, history, geography, food, music, sport, work, health, technology, language, art, natural world), each contributing exactly 48 authored topics — stratification guarantees the topic sample covers the declared task space instead of clustering in one corner [v2 §6].
- **Block**: one topic *plus* its fixed presentation order and fixed wording choices, shared by all six of its prompts. Block index i determines: order (even i → target constraint listed first), target wording (i mod 4), added-constraint wording (⌊i/4⌋ mod 4) [v2 §7; block indexing detail: D13, implementation].
- **Arm**: one of the six conditions each block is run under, defined by what occupies the "added" slot [v2 §1, §8].

They nest like this: the task space splits into 12 strata → 48 topics each (576 total) → seeded split into 96 calibration / 384 confirmatory / 96 sequestered topics [v2 §6] → each confirmatory topic becomes one block with its fixed order and wordings [v2 §7] → each block yields six prompts (one per arm) [v2 §8] → each prompt yields exactly one accepted response, whose verifier verdicts are the data.

### 3.3 The six arms

Each of the 384 confirmatory blocks runs under six arms; one response each; 2,304 generations total [v2 §8].

| Arm | Prompt contains | Why it exists |
|---|---|---|
| Focal | A + B | Treatment condition |
| Reference 1 | A + R₁ | Comparison condition |
| Reference 2 | A + R₂ | Comparison condition |
| Reference 3 | A + R₃ | Comparison condition |
| Target alone | A only | Headroom diagnostic: how hard is A by itself on these topics [v2 §8, §16] |
| Topic alone | no constraints | Base rate of *accidental* compliance: how often unconstrained text hits "exactly n *however*s" by chance [v2 §8, §24] |

Why six and not two? One reference would leave the comparison hostage to that reference's idiosyncrasies; three references let the study *test* whether references are interchangeable (the exchangeability contrasts), which decides whether an observed effect can be attributed to B's identity (Level 2 claim) or only to "B versus this particular reference set" (Level 1) [v2 §2, §11]. The two diagnostic arms carry a different constraint load (one or zero), so they are excluded from every contrast and reported descriptively only [v2 §8].

### 3.4 The unit of analysis

A block is the unit at four distinct levels [v2 §12]: **assignment** (order and wordings are assigned to the block, identically for its six arms), **pairing** (the focal–reference comparison happens *inside* a block, so between-topic difficulty differences cancel out of the contrast), **clustering** (uncertainty resampling draws whole blocks, all six responses travelling together), and **generalisation** (claims extend to the declared population of topics, of which blocks are draws).

Why not treat the 2,304 responses as 2,304 independent observations? Because the six responses of a block share a topic, an order, and wordings, they are correlated: an unusually hard topic pushes all six toward failure together. Pretending they are independent would make the effective sample look ~6× larger than it is and produce confidence intervals that are too narrow — overclaiming certainty. The protocol enforces this with executable checks: the bootstrap must draw exactly 192 block identifiers per order stratum, each carrying six responses; no primary estimator function may even *accept* a response-level index; and a synthetic test doubles within-block noise and asserts the interval width doesn't move [v2 §12].

### 3.5 Measurement

A **verifier** is a deterministic program that reads the response text and returns pass/fail for one constraint — no model-as-judge, no human in the primary score, no knowledge of which arm the response came from [v2 §10]. The primary scoring rule **S0**: lowercase the whole response, find maximal runs of letters, count runs equal to `however`, pass iff the count equals n [v2 §9]. Three declared alternatives probe the judgement calls hidden in S0: **S1** (case-sensitive), **S2** (count `however` even inside longer words), **S3** (first strip preamble lines and constraint restatements) [v2 §9]. **F_A** is the failure indicator: 1 when the target verifier does not pass — including empty responses, refusals, truncations, and unprocessable text, all kept as failures because the treatment itself can cause them (dropping them would condition on a consequence of the treatment) [v2 §9]. **D_i** is the block contrast: block i's failure in the focal arm minus its *average* failure across the three reference arms, D_i = F_{i,B} − ⅓(F_{i,R1}+F_{i,R2}+F_{i,R3}) — in plain terms, "how much worse (or better) did this topic do under B than under a typical comparable constraint" [v2 §11]. The two primary estimands are the mean of D_i within each presentation order; three exchangeability contrasts compare the references pairwise [v2 §11].

### 3.6 Calibration, gates, and freeze

Parameters like n, m, and the reference set cannot be chosen after seeing results — that would let the outcome shape its own measuring stick. So a separate **calibration** run (96 topics never reused in the confirmatory set, each constraint presented alone, one response per prompt) fixes them by frozen mechanical rules [v2 §18]. A **gate** is a pre-registered go/no-go check that runs in a fixed order and can stop the study [v2 §18]:

- **Gate 0 (apparatus)**: the procedural pilot — 12 topics × 6 arms end-to-end, inspecting exactly four quantities (rows committed, technical-failure share, truncation share, codebook conformance) and *no contrast of any kind* [v2 §17].
- **Gate 1 (measurement)**: verifier determinism = 1.000 across three processes, a 40-case boundary suite, and human agreement on 150 blinded responses (≤2 disagreements per 75 per class) [v2 §18, §10].
- **Gate 2 (regime)**: pick n as the {1,2,3} value with solo failure closest to 0.30, required to land in [0.15, 0.50] — this is **headroom**, room for the failure rate to move in either direction (no ceiling, no floor); pick m likewise in [0.15, 0.55]; admit reference candidates within 0.10 solo-failure distance of B; require at least three [v2 §18].
- **Gate 3 (freeze)**: hash and record every design choice — constraints, parameters, references, wordings, splits, template, verifier source, scoring rules, model revision, decoding, seeds, block plan, families, equivalence regions, codebook, environment — before any confirmatory generation. Any later change to a frozen field is a new protocol version [v2 §18].

A gate failure is a *result*, not a bug: "Regime not found" is a registered terminal outcome with a fixed claim ("no operating point with headroom, deliverable treatment, and three comparable references exists in the declared pool for this model") [v2 §26]. That is exactly what happened here, for both models.

### 3.7 Masking

**What is hidden:** after confirmatory generation and before any analysis, the pipeline permutes the arm labels of the four primary arms independently within each block, using system randomness; analysis then runs on the permuted table [v2 §19]. So the analyst can see everything *except* which condition produced which response: failure rates, anomalies, even response text (v2 explicitly keeps text readable in the masked phase, for failure coding [v2 §19, §23; Addendum conflict R37 resolved to v2]) — but any contrast they compute is scrambled garbage until the labels are restored.

**From whom:** from the analyst — here a single custodian, since no second person holds the key; the protection rests on recorded hashes and timestamps that make masked-phase and post-unmasking decisions distinguishable in the record [v2 §30].

**Why:** the masked phase is where pipelines get debugged and anomalies get adjudicated. Those decisions (fix this parsing defect? declare that batch anomalous?) can each nudge the estimate. If the analyst can see the emerging result while making them, even honest judgement drifts toward the hoped-for answer. Masking makes those decisions *provably* independent of the result: permitted in the masked phase are code repairs, new diagnostics, and anomaly rules; forbidden forever are changes to estimands, families, equivalence regions, references, scoring rules, verifiers, claim rules, or splits [v2 §19].

**The unmasking event:** a single named function, invoked once, writes a timestamped entry with the hash of the analysis code at that moment, then the analysis reruns on true labels; everything changed after that timestamp is labelled post-unmasking and supports no primary claim [v2 §19]. It is deliberately irreversible — you cannot unknow the mapping — which is why the mask key file and raw text are radioactive to anyone who wants to keep analysis options open. Three executable checks enforce it: the permutation actually changed labels in at least half the blocks; the key file is opened exactly once per full run; and the masked-phase outputs are reproducible byte-for-byte from the recorded code hash [v2 §19]. (Implementation note: the custody machinery — sealed key file, commitment record before unmasking, second-unmask/second-key refusal — is Addendum A layered on v2 §19, and was exercised for real on both pilot trees and in a blind dry run that recovered a known injected effect of 0.5 exactly: `_synthetic/dryrun/dry_run_report.json`.)

### 3.8 The two resampling layers

Two different randomness layers exist, and confusing them corrupts the design (registered amendment A1/A2 material; D01–D11, implementation of the registered cached-generation amendment):

- **Layer 1 — the cached generation pool.** For every (model, block, arm) prompt, the pipeline generated M = 16 responses, each with its own deterministic seed, into an append-only content-hashed cache (D01, D07). Exactly **one** of them — pool index 0, a rule fixed before any generation (D02) — becomes the accepted response that the analysis sees. The other 15 exist for **pseudo-runs**: alternative datasets built by re-drawing one cached response per cell (uniformly, with replacement; D03, D08), re-running the *point estimates*, and asking "would the numbers have looked different if the dice of decoding had fallen differently?" (R = 1000 pseudo-runs, full bootstrap on the first 50; D04–D05). Pseudo-runs cost zero model inference — the code that builds them is structurally incapable of inference (AST-scan test) — and can never touch, replace, or be promoted into the primary lineage (bit-identity check) [`MAPPING.md` amendment consequences; `REPORT.md` §12–14].
- **Layer 2 — the block bootstrap.** 10,000 resamples that draw **blocks** (topics) with replacement, stratified by presentation order, all six arms travelling with each drawn block, to price *topic-sampling* uncertainty: "how different could the estimate be if we had drawn different topics from the task space?" [v2 §12, §20].

Layer 1 asks about decoding noise *within* the realised topics; layer 2 asks about generalisation *across* topics. They use disjoint seed roots and disjoint SHA-256 domains so they can never bleed into each other (D06). And **M = 16 is not a sample size**: the cache sits *below* the observation level; the accepted table still has exactly blocks × 6 rows, one response per cell, and M appears in no estimator, interval, or claim rule [`MAPPING.md`; D11]. Sixteen cached generations do not make the study 16× bigger any more than 16 photographs of one voter make 16 voters.

### 3.9 Scope

The design can establish, per model: whether swapping a matched reference constraint for this one focal constraint changes failure of this one target constraint, on this topic space, at load two, in English, under one prompt template and one decoding policy — with the further attribution to B's *identity* only if the references prove exchangeable [v2 §3, §11]. It cannot establish: effects of *adding* constraints (load), effects for other constraint families, the reciprocal effect of A on B, internal mechanisms, or generalisation to other models, languages, formats, or decoding policies — each claim carries every fixed condition as a rider [v2 §3, §30]. Under the A1/A2 amendment, each of the four models is a separate replication with its own calibration and frozen record; nothing pools across models (`DECISIONS.md` A2; `README.md`).

### 3.10 A worked example

*(Hypothetical topic; constraint text from the preregistration and the frozen template from D12. No real study prompt or response appears here.)*

Suppose block **B042** exists for the instruct model, with topic "Why do kettles get louder just before boiling?" from the everyday-science stratum. Index 42 is even → target constraint listed first; target wording index 42 mod 4 = 2; added wording ⌊42/4⌋ mod 4 = 2 [v2 §7; D13]. Suppose calibration had selected n = 2, m = 8, references C1, C3, C10.

Six prompts are built from the frozen template `"{question}\n\n1. {first}\n2. {second}\n\nAnswer:"` (D12). The focal-arm prompt lists wording 2 of "Use the word *however* exactly 2 times" as line 1 and wording 2 of "Every word in the answer must have at most 8 letters" as line 2. The reference-1 arm is byte-identical except line 2 now carries wording 2 of C1 ("Every word in the answer must have at least two letters"). Reference arms 2 and 3 swap in C3 and C10; target-alone drops line 2; topic-alone has no numbered list [v2 §7–8].

Each prompt gets 16 seeded generations into the cache; pool index 0 of each cell becomes the accepted response (D02). S0 scores each accepted response: say the focal response used *however* once (F=1, taxonomy category "too few" [v2 §23]), the C1 and C10 responses used it exactly twice (F=0), and the C3 response used it three times (F=1). Block B042's contrast is D₄₂ = 1 − ⅓(0+1+0) = +0.667: on this topic, the focal constraint hurt the target more than the average reference did. That single number — not the six responses — is B042's contribution to τ_target-first, averaged with the other 191 target-first blocks [v2 §11]. When the bootstrap draws B042, all six responses come along [v2 §12]. Before unmasking, the analyst would have seen B042's four primary-arm labels scrambled, so this +0.667 could not be traced to "focal vs references" [v2 §19].

---

## 4. Integrity verdict

**PASS, with two prominent caveats (dirty writer state; code not in version control) — and with the four duplicate categories all clean.**

Checks run and their results (per model; identical structure both):

| Check | qwen3-4b | qwen3-4b-instruct-2507 | Source |
|---|---|---|---|
| `verify-evidence` (seals, manifests, cache hashes, study manifest) | ok=true, exit 0 | ok=true, exit 0 | `dci1.cli verify-evidence --freeze prefreeze-pilot` |
| Cache records vs plan (12 blocks × 6 arms × M=16) | 1,152 / 1,152 | 1,152 / 1,152 | `prefreeze-pilot/cache/generations.jsonl` (line count; per-cell count) |
| Cells with full pool, indices 0–15 | 72/72, no gaps | 72/72, no gaps | same file, fields `block_id, arm, pool_index` |
| **Duplicate row identities** (integrity failure if any) | 0 (1,152 unique `row_id`) | 0 | same file |
| **Identical seeds** (integrity failure if any) | 0 (1,152 unique `generation_seed`) | 0 | same file |
| **Missing generations** (integrity failure if any) | 0 | 0 | same file; `pilot_report.json` status COMPLETE |
| **Identical outputs within pools** (legitimate) | 116 | 7 | `integrity/cache_report.json`; my per-cell hash count agrees |
| Accepted table rows vs blocks×arms, key uniqueness | 72 rows, (block, arm) unique, 12×6 balanced | same | `derived/primary/accepted.parquet` |
| Accepted table carries no response text | confirmed (no text column) | confirmed | same, column list |
| Scored table row count | 336 (= 48 two-constraint cells × 5 verifiers + 24 diagnostic cells × 4) | 336 | `derived/primary/scored.parquet` |
| Analysis tables carry all 29 family members (F1..F6 = 2+3+6+6+9+3) | 29 rows | 29 rows | `derived/primary/analysis.parquet`, `masking/masked_view/analysis_masked.parquet` (row/column structure only; no estimate value read) |
| Durable mirror byte-identity + `.sha256` sidecars | identical, sidecars OK | identical, sidecars OK | `durable_root/dci1-v2/<model>/prefreeze-pilot/*` vs evidence copies |
| Masked view excludes role-revealing columns | yes (no prompt_hash / wording / constraint columns; labels permuted per block) | yes | `masking/masked_view/masked_rows.jsonl` key list |
| Mask custody records consistent (key hash in runrecord = study_manifest = unmasking record) | yes (`2c35f68e…`) | yes (`44190dd1…`) | `runrecord.jsonl`, `study_manifest.json`, `masking/unmasking_record.json` |
| CPU protocol test suite | 131 passed | (shared suite) | `pytest tests/ -q` |
| Synthetic end-to-end smoke; blind dry run (known effect 0.5 recovered; second unmask/key refused) | pass | (shared) | `_synthetic/smoke/smoke_report.json`, `_synthetic/dryrun/dry_run_report.json` |

What a failure in each duplicate category would have meant:
- **Identical outputs within a pool** — legitimate: two independent seeded draws produced the same text; expected for a peaked output distribution, and itself a diversity measurement (§7.1).
- **Identical seeds** — the seed-derivation function is broken; pool members are not independent draws and the whole resampling layer is fiction.
- **Missing generations** — the pool under-fills its frozen size; pseudo-run draws would be biased toward the responses that exist.
- **Duplicated row identities** — the append-once cache discipline failed; a response could be double-counted or silently overwritten, breaking the one-accepted-response invariant [v2 §20, §27].

**Caveats (named, per brief §5.1 "any artifact written from a dirty working tree"):**
1. **Every derived artifact in both trees records `writer_dirty: True`** (`accepted.parquet` provenance columns, both models), and the whole `dci1/` module is untracked (`git ls-files dci1/` → 0 files). The recorded `analysis_code_commit` `094922b` therefore does **not** contain the producing code, so the v2 §19 check "rerun the masked phase from the recorded code hash and compare byte-for-byte" is unsatisfiable from version control for these trees. Acceptable for the non-registered Gate-0 pilot (the addendum's `writer_dirty=false` refusal applies to *registered* artifacts [Addendum R20/R50]); it must be fixed before any registered artifact — including Gemma gate records — is written.
2. **Stale paths inside `gate1.json`**: the human-annotation packet paths point at `dci1/evidence_root/…`, which does not exist; the actual packets are at `evidence/dci1-v2/<model>/prefreeze-apparatus/calibration/gate1/` (verified present, 2026-08-16 19:38/19:42). Cosmetic, but a record pointing at a nonexistent path is the kind of thing an auditor trips over.

---

## 5. Base against instruct (brief §5.2)

**Answer first: the comparison the brief asked for — base vs instruct — does not exist in this study. Both completed models are post-trained chat checkpoints; they differ in post-training recipe (hybrid thinking model with the reasoning channel switched off, vs a pure instruct model with no reasoning channel at all). Their independently calibrated values genuinely differ where they should (m: 10 vs 8; every solo rate), and the fields that are identical are identical because the registered protocol fixes them study-wide, not because anything was copied.**

Since no Gate-3 freeze record exists for either model (Gate 2 terminal), the side-by-side below uses each model's actual pre-freeze records: `qualification_report.json`, `calibration/gate2.json`, `calibration/gate1.json`, the pilot `freeze_record.json` stub, and `runrecord.jsonl`.

| Field | qwen3-4b | qwen3-4b-instruct-2507 | Differs? |
|---|---|---|---|
| Model / revision | Qwen/Qwen3-4B @ `1cfa9a72…` | Qwen/Qwen3-4B-Instruct-2507 @ `cdbee75f…` | yes (registered, A2) |
| Selected n (solo failure) | 3 (0.125) | 3 (0.073) | same n, **independently derived** (rates differ; both simply the max of the grid, still under band) |
| n in band [0.15, 0.50] | **no** | **no** | — |
| Selected m (solo failure) | **10** (0.323) | **8** (0.333) | **yes — independent calibration visible** |
| Admitted references / final set | 0 / none (3 required) | 0 / none | — |
| Closest candidate | C10 @ distance 0.146 | C10 @ distance 0.167 | yes |
| Headroom / regime | ceiling; Gate 2 **FAILED (terminal)** | ceiling; Gate 2 **FAILED (terminal)** | — |
| Gate outcomes | Qual QUALIFIED; G0 8/8 PASS; G1 PENDING_HUMAN (determinism 1.000, boundary 40/40); G2 FAIL; G3 not produced | identical statuses | — |
| Decoding | T=0.7, top-p 0.9, top-k 50, max 400 | same | identical **by registration** [v2 §4] |
| Pool size M / primary rule | 16 / index 0 | 16 / index 0 | identical **by registration** (D01, D02) |
| Root seeds (gen/resample/bootstrap) | 202608161/2/3 | same | identical **by registration** (D06 — study-wide constants; per-generation seeds still differ because model_id enters the hash, D07) |
| Engine seed / hardware | 20260812 / gfx1100 | same | identical by registration (D23) |
| Backend config hash | `c9db445d…` | `323335af…` | yes (per-model plans) |
| Pilot truncation share (pool / accepted) | 0.031 / 0.028 | 0.016 / 0.014 | yes |
| Identical outputs within pilot pools | 116 | 7 | yes (§7.1) |

No field shows the copied-instead-of-calibrated signature: everything behavioural (solo rates, m, distances, truncation, diversity) differs between the models; everything identical is identical because the registered protocol fixes it study-wide.

**The four "base-model risks", re-examined against what `Qwen/Qwen3-4B` actually is:**

1. **Prompt rendering.** Not raw completion and not a hand-written template: both models use their own checkpoint's chat template, applied by the engine with `add_generation_prompt=True`, over the identical single-user-turn study text (D12). The qualification template probe shows the actual renderings: for qwen3-4b, `…Answer:<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n` (the pre-closed think block injected by `enable_thinking=False`); for the instruct model, `…Answer:<|im_end|>\n<|im_start|>assistant\n` (`qualification_report.json`, `template_probe.rendered_tail_*`). Within-model byte-identity of matched-arm prompts apart from the constraint line is asserted by the passing protocol-fidelity tests (`test_prompt_bytes`, in the 131-pass suite) on the pre-template study text; and the two models' pilot `prompts/cells.jsonl` files are byte-identical to each other (identical stage-manifest hash `b049adca…` in both `study_manifest.json` files; `cmp` confirms), as the design requires — the template divergence happens downstream, inside the engine, identically for all arms of a model. *Caveat I cannot close without reading prompt text:* byte-identity of the final *rendered* prompts across arms is implied by template determinism (probe-verified) applied to byte-identical-except-one-line inputs, not directly observed by me.
2. **No-thinking configuration.** Honestly recorded, and *different* per model, which is what honesty looks like here: qwen3-4b declares `switch_expectation: "live"` and qualification verified that negating `enable_thinking` changes the rendering (`renders_identical_true_vs_false: false`); the instruct model declares `"inert"` and qualification verified all renders byte-identical — "no reasoning channel exists; NO_THINKING is the checkpoint's only mode" (`models/adapters.py`, implementation; `qualification_report.json`, both). No copied placeholder: the two records make opposite factual claims and each was verified live against the pinned engine's tokenizer.
3. **Answer extraction and stopping.** Extraction is the identity function — no parser (`parser_is_null: true`, both qualification reports), whole response scored, as S0 requires [v2 §9]. Finish reasons across the 1,152 pilot generations: qwen3-4b 1,116 `stop` / 36 `length` (3.1% truncated); instruct 1,133 / 19 (1.6%) (`cache/generations.jsonl`, field `finish_reason`; matches `pilot_report.json`). Token counts (all generations): qwen3-4b min 8 / median 75 / p95 353 / max 400, mean 110.5; instruct min 16 / median 108 / p95 287 / max 400, mean 121.8. Neither looks length-limited as a rule; qwen3-4b has a modestly heavier truncated tail (its p95 nearly reaches the 400-token cap). Both sit well under the §17 ceiling of 0.10.
4. **Instruction-following floor.** The opposite problem, decisively: on calibration, qwen3-4b fails the target constraint alone only 2.1–12.5% of the time across n∈{1,2,3}, and the instruct model 5.2–7.3% (`calibration/solo_rates.json`, 96 responses per condition, 19 conditions, 1,824 total per model). Both models are at **ceiling**, not floor — they follow the *however*-counting instruction almost perfectly. Where they genuinely struggle is the letter-shape reference candidates (47–100% solo failure). So the estimand is starved of information not because the model ignores instructions but because it obeys the target one too well — and because no reference candidate is comparable to B [`gate2.json`, both models].

---

## 6. Can this study conclude anything (brief §5.3)

**qwen3-4b: no — and the study itself established that, at Gate 2, before spending a single confirmatory token; solo target failure 0.125 sits below the 0.15 headroom floor and zero of twelve references are admissible.**
**qwen3-4b-instruct-2507: no — same terminal verdict, further from the band (0.073) and likewise zero admissible references.**

The precision quantities the brief asks for — interval widths per registered estimand and family, ratios to the ±0.10 equivalence region and to the 0.10 smallest effect of interest, share of estimands wider than the region — **do not exist**, because no confirmatory data was ever generated and hence no confirmatory masked analysis exists (no `<freeze_id>` tree; `masking/masked_view/` exists only inside the pilot trees). The only analysis tables anywhere are the Gate-0 pilot's 29-row apparatus tables on 12 blocks, which the preregistration forbids inspecting for any contrast-bearing quantity ("No arm difference is computed. No contrast of any kind is computed or viewed" [v2 §17]); I verified their structure (rows, columns, family membership) and deliberately did not read their estimate, interval, or claim columns — both to honour §17 and because 12-block pilot intervals would be meaninglessly wide anyway.

What can be said from design arithmetic alone: with solo target failure at 0.073–0.125, the negative half of the equivalence region is partly unreachable (failure cannot fall below zero, so an effect of −0.10 is arithmetically impossible for much of the topic space), block discordance is necessarily small, and most topics would be "uninformative" in the §10 sense — the calibration item-behaviour tabulation already shows **86.5% of topics at ceiling with 86.5–88.5% giving identical verdicts everywhere** (`gate1.json`, `item_behaviour`, both models). The gates exist precisely to catch this before the irreversible steps; they did. No unmasking decision arises, for either model, ever, under this protocol version.

---

## 7. Diversity, compliance, and stability

### 7.1 Generation diversity (brief §5.4) — from content hashes only

Per cell (12 blocks × 6 arms = 72 cells, M = 16 each), distinct `response_content_hash` values (`prefreeze-pilot/cache/generations.jsonl`):

| Quantity | qwen3-4b | qwen3-4b-instruct-2507 |
|---|---|---|
| Minimum distinct / 16 | **5** | **13** |
| Median distinct | 16 | 16 |
| Mean distinct | 14.39 | 15.90 |
| Cells with exactly 1 distinct response | 0 | 0 |
| Cells with ≤ 2 distinct | 0 | 0 |
| Cells fully distinct (16/16) | 43 / 72 | 69 / 72 |
| Duplicate pairs recorded by integrity report | 116 | 7 |

Consequence in plain terms: **neither pool collapses**. No cell repeats a single response, so the pseudo-run layer has genuine variation to resample everywhere; had any cell collapsed to one response, stochastic "stability" there would have been an artifact of a degenerate output distribution, not robustness. The two models do differ, in the direction opposite to the brief's expectation (it expected the "base" model to be more diverse): the hybrid checkpoint run no-thinking is *less* diverse (a fifth of a pool identical in its worst cell; 116 duplicate pairs) than the instruct checkpoint (near-total diversity; 7 duplicate pairs). Consistent with both being post-trained models, one of them apparently peakier under this template.

### 7.2 Compliance, manipulation checks, parse quality (brief §5.5)

The brief asks for these per masked arm label from confirmatory masked scored outputs — which do not exist. Arm-level pilot rates are §17-prohibited viewing (and I did not view them). What the registered records legitimately provide:

- **Apparatus-level (pilot, registered §17 quantities)**: 72/72 rows committed exactly once; zero unresolved technical failures; truncation 3.1% / 1.6% of pool generations (2.8% / 1.4% of accepted rows); full codebook conformance (`pilot_report.json`, both models).
- **Compliance floor/ceiling (calibration, per solo condition, 96 responses each)**: target constraint at **ceiling** for both models (§6 above). Explicit floor detection: reference candidates C4 and C9 sit at exactly 1.000 solo failure for qwen3-4b, C9 at 1.000 for the instruct model — literal floors (`solo_rates.json` / `gate2.json` admission tables).
- **Manipulation-check analogue (uptake of the added constraint when presented alone)**: focal B was followed 67.7% (qwen3-4b, m=10) and 66.7% (instruct, m=8) of the time; reference candidates only 0–53% — the treatment *can* be delivered, but no comparable comparison condition exists.
- **Parse quality**: verifier determinism 1.000 over 1,824 calibration responses × 3 processes; 40/40 boundary cases; parse independence of the pool verified (`gate1.json`, both). Nothing the verifier could not process was recorded anywhere in the registered quantities.

**Did each model follow instructions well enough for the comparison to mean anything?** Both followed the *target* instruction too well (ceiling) and the reference candidates too poorly — so the registered comparison is starved from both ends. That is precisely Gate 2's finding.

### 7.3 Stochastic stability (brief §5.6)

**No pseudo-runs exist for either Qwen model.** The frozen counts (R = 1000, full bootstrap on 50; D04–D05) apply to the confirmatory stage, which never ran; neither pilot tree contains a `selection/pseudo_runs/` or `derived/pseudo_runs/` directory. So there is no dispersion and no sign-change rate to report — nothing was computed whose sign could change. The machinery itself is validated: the synthetic smoke tree exercises pool → primary → pseudo lineages (`_synthetic/smoke/confirmatory/pseudo/run_0000..0002`) with `primary_invariant_under_pseudo_runs: true`; the no-inference property is enforced structurally (AST-scan test in the passing suite; `REPORT.md` §12); and pseudo lineages are path-guarded out of `*/primary/` (`README.md` naming rules; tested).

---

## 8. Deviations (preregistration vs implementation vs artifacts present)

Reported, not reconciled; blocking items marked.

1. **Brief vs artifacts (blocking for the brief's own premise):** "generation complete" for both Qwen models vs *no confirmatory generation exists*; both models terminal at Gate 2 [v2 §18, §26]. Everything downstream in the brief (masked precision, per-arm compliance, pseudo-run dispersion) has no object.
2. **Brief vs artifacts:** "Qwen3-4B-Base is a pretrained base model, no chat template" vs the registered `Qwen/Qwen3-4B` hybrid chat checkpoint with a live template and thinking switch (`qualification_report.json`). The base-vs-instruct framing should be retired in favour of hybrid-no-thinking vs instruct-only.
3. **Prereg §4 vs registered amendments:** one model (Qwen2.5-3B-Instruct), HF Transformers backend vs four models on pinned vLLM 0.15.1+rocm720, M=16 cached pools, pseudo-runs — registered amendments A1/A2 (`DECISIONS.md`), each model a separate replication.
4. **Prereg §28 container image vs D22 environment digest** (no container; digest over both interpreters' freezes + kernel + GPU) — explicit registered deviation.
5. **Prereg §10/§18 human-agreement sample (75 pass + 75 fail = 150) vs artifacts: packets hold 92 items (75 pass + all 17 available fails)** — the ceiling starves the fail class; recorded as `shortfall: {fail: 17}` in `gate1.json`, status PENDING_HUMAN, never faked. Whether a 17-fail class can satisfy Gate 1's "≤2 of 75" criterion is undefined in the preregistration — flagged as blocking for any Gate-1 pass claim (moot for the Qwens, live for Gemma if the same ceiling appears).
6. **v2 §19 masking timing (after confirmatory generation) vs pilot-tree mask cycles** — the pilot exercised mask → commit → unmask on non-registered data as a Gate-0 apparatus certification (recorded reason string says exactly that). Defensible under Gate 0's purpose; noted because §19's wording ties masking to confirmatory data.
7. **Addendum A vs v2, three conflicts, all resolved to v2 by precedence** (masking scheme per block, system-random key, masked view retains response text; freeze-record masking fields null with notes) — zero unresolved (`docs/addendum_a_reconciliation.md`, R36/R37/R40/R41).
8. **Version-control state vs the protocol's own reproducibility checks:** `dci1/` untracked, `writer_dirty: True` on every derived artifact, recorded `analysis_code_commit` does not contain the code — v2 §19 check 3 and Addendum R20 unsatisfiable for registered runs until committed. **Blocking for all future registered artifacts, including Gemma gates.**
9. **Minor artifact inconsistencies:** stale `evidence_root/` paths inside both `gate1.json` files; `report.json` present in the qwen3-4b pilot tree but absent from the instruct tree (report generation apparently run for one model only); pilot `freeze_record.json` stubs carry `pseudo_run_count: 1000` while no pseudo-runs exist on real trees (the value is the frozen *confirmatory* parameter, but a reader can be misled).
10. **Prereg §17 pilot wording formula unreachable with 12 blocks** (⌊j/4⌋ mod 4 cannot reach wording 3) — implementation uses ⌊j/3⌋, a documented pre-freeze decision (D15).

---

## 9. What unmasking would add, and what would remain unanswerable

**For these two models: unmasking has nothing left to do.** The confirmatory mask that v2 §19 describes was never constructed because the data it would protect was never generated. The pilot masks were already applied and removed as an apparatus exercise. There is no hidden Qwen result waiting behind a key: the registered outcome for both models is already public in the gate records — "Regime not found," with the fixed claim that no operating point with headroom, a deliverable treatment, and three comparable references exists in the declared pool for these models [v2 §26].

What remains unanswerable, permanently, under protocol version 2 for these two checkpoints: τ at either order, all three exchangeability contrasts, every family F1–F6 member, equivalence or its absence — the entire registered estimand set. Not because the study failed to run, but because its own admissibility conditions were unmet and its rules forbid adjusting the design to force a run [v2 §18]. Answering the scientific question for these models requires a *new registered protocol version* — plausibly a harder target (larger n, or a rarer word), an easier or re-matched reference pool, or a widened admission window — designed, registered, and gated afresh, with the sequestered 96 topics available for an uncontaminated re-run [v2 §6, §24]. What this study *did* deliver for the Qwen pair is a validated end-to-end apparatus (Gate 0, smoke, blind dry run, custody cycle all green) and a replicated, quantified characterisation of *why* the regime is absent: near-perfect target compliance and a uniformly-too-hard reference pool, in two independently calibrated replications.

---

## 10. Glossary

- **Arm** — one of the six conditions a block's topic is run under (focal, ref1–3, target-alone, topic-alone) [v2 §8].
- **Block** — one topic plus its fixed presentation order and wording choices, shared across its six arms; the unit of assignment, pairing, clustering, and generalisation [v2 §1, §12].
- **Block bootstrap** — uncertainty estimation by re-drawing whole blocks with replacement (10,000×, stratified by order), all six responses travelling with each drawn block [v2 §12, §20].
- **Cached generation pool** — the M=16 seeded responses stored per (model, block, arm) prompt, of which exactly one (index 0) is the accepted observation; the rest feed pseudo-runs only (D01–D03, registered amendment).
- **Calibration** — the pre-freeze run on 96 dedicated topics that fixes n, m, and the reference set by frozen mechanical rules [v2 §18].
- **Ceiling / floor / headroom** — a constraint that almost always passes / almost always fails / neither, leaving room to detect change in both directions [v2 §1].
- **Commitment record** — the pre-unmasking snapshot (code commit, plan hash, masked-result hash) that makes later changes detectable [Addendum R43].
- **Constraint** — an instruction a fixed program can verify (target A: "*however* exactly n times"; focal B: "every word ≤ m letters"; references C1–C12) [v2 §1, §5].
- **D_i (block contrast)** — focal-arm failure minus mean reference-arm failure, per block [v2 §11].
- **Equivalence region** — ±0.10 (primary) / ±0.05 (exchangeability): the interval inside which an effect counts as negligible, claimable only when the simultaneous interval sits wholly inside it [v2 §11, §15].
- **Exchangeability** — the tested property that the three references are interchangeable; required for attributing an effect to B's identity (Level 2) [v2 §2, §11].
- **F_A** — the target-failure indicator: 1 unless the target verifier passes (empty, refused, truncated, unprocessable all count as failure) [v2 §9].
- **Family / simultaneous interval** — a declared set of quantities sharing one 95% confidence statement across the whole set (F1–F6) [v2 §14].
- **Focal constraint (B)** — the constraint whose presence is the treatment [v2 §1].
- **Gate** — a pre-registered go/no-go check (0 apparatus, 1 measurement, 2 regime, 3 freeze); failure is a registered result [v2 §18, §26].
- **Freeze** — hashing and recording every design choice before confirmatory generation; later changes create a new protocol version [v2 §18].
- **Mask key** — the stored true-label mapping, sealed in one file, opened once by the single unmask function [v2 §19].
- **Masking** — permuting the four primary-arm labels within each block before analysis so that pipeline decisions cannot depend on the result [v2 §19].
- **Manipulation check (uptake)** — compliance with the *added* constraint, showing the treatment reached the model; never a filter on the primary estimate [v2 §16].
- **Pseudo-run** — an alternative dataset built by re-drawing one cached response per cell; sensitivity only, zero inference, never promotable to primary (D03–D05, D08).
- **Reference constraint (R)** — a difficulty-, length-, and scope-matched stand-in for B forming the comparison condition [v2 §1, §18].
- **Regime** — an operating point with headroom, a deliverable treatment, and ≥3 comparable references; "Regime not found" is the terminal outcome when none exists [v2 §18, §26].
- **Scoring rules S0–S3** — the primary count-based pass rule and its three declared variants (case-sensitive; substring; preamble-stripped) [v2 §9].
- **Subject stratum** — one of twelve declared topic areas, equally represented by construction [v2 §6].
- **Target constraint (A)** — the constraint whose compliance is the measured outcome [v2 §1].
- **Verifier** — the deterministic program returning pass/fail for one constraint from response text alone, blind to arm [v2 §10].
- **Witness** — a written response proving a constraint combination is jointly satisfiable [v2 §1, §5].

---

## 11. Open questions for you

1. **The status premise.** The brief states "generation complete" for both Qwen models; the artifacts show pre-freeze completion only, with Gate 2 terminal. Did you mean the pilot/calibration generations, or did you believe confirmatory generation had run? *Blocks:* whether any further Qwen inspection is wanted at all, and how to describe the Qwen pair in anything you publish.
2. **Model identity in the record.** Given `Qwen/Qwen3-4B` is a hybrid post-trained checkpoint, do you want the study's public framing amended from "base vs instruct" to "hybrid (no-thinking) vs instruct-only"? *Blocks:* the comparison framing of the amendment's Qwen pair in the eventual release.
3. **Version control before Gemma.** Will you commit `dci1/` (and the evidence-layout decision of what is committed vs gitignored) before running Gemma qualification/calibration? The protocol's own refusal rules make registered artifacts impossible from a dirty tree, and today's records carry `writer_dirty: True`. *Blocks:* Gemma gate records that would survive audit; satisfying v2 §19 check 3 on any future masked analysis.
4. **Gemma sequencing.** Do you authorise running and sealing Gemma calibration + gates under the current frozen protocol as soon as the licence gate clears, explicitly before any v3 design discussion? (§2.4 explains the ordering exposure.) *Blocks:* the credibility of the two pending replications; requires your `huggingface-cli login` + licence acceptance.
5. **Gate 1's starved fail class.** The prereg requires 75 failing responses in the human-agreement packet; only 17 exist per model. If Gemma shows the same ceiling, do you want (a) a registered interpretation note that the fail class is exhaustive-but-small, or (b) Gate 1 to be treated as unpassable in that case? *Blocks:* whether Gate 1 can ever pass for a ceiling-bound model; the design of the annotation task you'd give the three annotators.
6. **A v3 protocol.** Both Qwen replications say the same two things quantitatively: the target is too easy (0.073–0.125 solo failure at n=3) and every reference is too hard relative to B (closest distance 0.146/0.167 vs 0.10). Do you want a v3 drafted — as a new registration — that re-grids the target and/or re-pools the references, holding the rest of the machinery (which is validated end-to-end) fixed? *Blocks:* whether the scientific question ever gets answered for the Qwen pair; note the 96 sequestered topics exist precisely to support an uncontaminated re-run [v2 §6, §24].
7. **Minor repairs, your call only.** Stale `evidence_root/` paths inside both `gate1.json` files and the missing instruct-side `report.json` are trivial to fix but sit inside evidence trees, which I do not touch. *Blocks:* nothing scientific; audit tidiness only.
