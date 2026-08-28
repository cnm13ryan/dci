# 00 — The scientific story, the endpoint, and what can be claimed

Consolidated 2026-08-27 from the repository at HEAD `76ae840` (branch `feat/dci1v4-fresh-study`). This is the entry point to five self-contained documents that replace the need to read ~70 reports, seven preregistrations and two change logs to reconstruct the study. Every number links to the artifact it comes from; evidence class is always stated. Nothing in the repository was modified to produce these documents.

| Document | What it holds |
|---|---|
| **00** (this file) | narrative, endpoint, claim tiers, open items |
| [01_RESEARCH_QUESTION_AND_DESIGN](01_RESEARCH_QUESTION_AND_DESIGN.md) | the question; estimand and design of every version; claim ladder; gates; reference-matching machinery; measurement basis |
| [02_LIFECYCLE_AND_RESULTS](02_LIFECYCLE_AND_RESULTS.md) | the 28-replication attrition table; every result with numbers, by version; key findings with grades |
| [03_FAILURE_MODES_LIMITATIONS_INTEGRITY](03_FAILURE_MODES_LIMITATIONS_INTEGRITY.md) | recurring failure mechanisms; implementation-vs-science ledger; undocumented deviations; permanent limitations; withdrawn statements; evidence durability |
| [04_CONTEXT_PRIOR_WORK_PAPER_STATE](04_CONTEXT_PRIOR_WORK_PAPER_STATE.md) | the exploratory arm and un-run v19 protocol; citations in the repo and the comparison questions; the current paper plan and its gaps; framing options |

---

## 1. The story in one page

**The question.** When a language model is given two verifiable instructions at once, does one instruction degrade compliance with the other *because of what it is*, beyond the generic cost of one more instruction? The programme calls the pair-specific part *directional constraint interference* and identifies it by replacement: compare A+B against A+R where R is a reference instruction matched to B (later: to A) on difficulty. The construct evolved from a single target-failure difference τ to a per-constraint compliance vector with reciprocal delivery losses D(A←B), D(B←A), their asymmetry Λ, and a companion swap Δ_R = D(B←A) − ⅓ΣD(B←R_j); a five-level claim ladder licenses statements from "loss exists" (L1) to "pair-specific beyond generic load" (L3) and "replicates across configurations" (L4). ([01](01_RESEARCH_QUESTION_AND_DESIGN.md) §1–4)

**The first arc found the phenomenon and distrusted its own control.** Thirteen exploratory rounds on Qwen3-4B (2026-08-10…13) found large, order-reversible, background-dependent interference from punctuation-shaped instructions — and that the matched reference in the v19 preregistration was not matched on realised difficulty and could out-interfere the focal. The v19 confirmatory run was never executed (human Tier-1 labels never produced; an open segmentation defect). All of it is `EXPLORATORY_NO_EVIDENCE` and none of it is promoted. ([04](04_CONTEXT_PRIOR_WORK_PAPER_STATE.md) §1)

**The second arc registered the question seven times and identified the companion contrast zero times.** DCI-1 (from 2026-08-16) fixed one pair — A "use *however* exactly n times", B "every word ≤ m letters" — on four small open checkpoints and built a gated lifecycle in which every stage writes a signed record and a failed gate is terminal and write-once. v2 could not admit references (the fixed pool was uniformly harder than A or B). v3 produced two analysed Gemma replications whose τ intervals all contained zero and whose one equivalence claim turned on the draw lottery; the Qwens could not fill a reference set. The v4 redesign (compliance vector, references matched to A on a chance-corrected difficulty coordinate ι, a difficulty spectrum, a class companion) could not start under its registered prompt (B was vacuously satisfied ≥ 21 % of the time), and four non-confirmatory screens then measured what the confirmatory design would have to control: companion identity moves focal compliance by 0.05–0.10 while constraint class moves it 0.40–0.60 and position 0.29–0.35; a pilot "pair-specific" effect of +0.34 collapsed to +0.10 under the registered vacuity bound. v4r3 adopted the repairs and closed at Gate 1 because no independent human validation existed and the LLM-validator pathway failed its own criteria. ([02](02_LIFECYCLE_AND_RESULTS.md) §2–6)

**v4r4 is the only version with confirmatory data.** With a deterministic Gate 1, all four replications passed measurement, calibration and reference selection — but the difficulty spectrum was identified on one replication only, and Gate 4's composed-headroom predicate ended that replication (a reference at 0.96–1.00 compliance in composition) and one more (a class companion at 0.99 solo). The two survivors ran the 8-cell reduced design: 24,576 generations each, masked, unmasked, analysed once. Delivery loss exists (L1) — on qwen3-4b the loss falls entirely on A in both orders (D(A←B) = +0.392 [+0.350, +0.434] and +0.329 [+0.284, +0.375]); on gemma-3n-e4b-it which constraint pays flips with position (D(A←B) = +0.116 first; D(B←A) = +0.283 second) and Λ reverses sign. L2 is withheld everywhere; six companion-specific quantities including Δ_R are `NOT_IDENTIFIED` study-wide; L4's emitter had a defect and one replication's replication claim is invalidated in favour of "configuration dependence". ([02](02_LIFECYCLE_AND_RESULTS.md) §7)

**v5 and v6 were prospective tests of whether the companion contrast could be identified at all — and both failed on registered gates.** v5 inverted the reference pool to same-form production-class markers, added an interaction gate and two calibration splits, and required six straddling feature groups. It ran to 459,312 rows and no replication reached confirmatory generation: three failed reference support (4/5/5 groups of 6, with 14–21 eligible rungs above ι_A against 143–163 below) and two failed composed headroom (the survivors had cleared by 0.054). v6 moved a headroom probe before reference selection at a frozen operating point, repaired the expansion rule, and was registered on 2026-08-26; on 2026-08-27 all four replications went terminal — two at the new probe, one at Gate 4 on a companion slot the probe cannot gate, one at the pre-freeze audit after the calibrated coverage re-read failed. Zero confirmatory rows in either. ([02](02_LIFECYCLE_AND_RESULTS.md) §8–9)

**What recurred.** Two mechanisms, each measured: the eligible reference ladder is one-sided below A's difficulty and moves more than the caliper between a 24-topic pre-screen and a 96/192-topic calibration; and the focal operating point is chosen on solo curves while composition lifts the focal slot by up to +0.10, so companion slots saturate at a gate that runs after references are fixed and may not revise them. ([03](03_FAILURE_MODES_LIMITATIONS_INTEGRITY.md) §1)

**What sits underneath.** Outcomes are verifier-defined (no version reached `human_validated`); the two survivors disagree qualitatively; every threshold from v5 on was fitted to its predecessor; and a set of implementation defects — mostly "a reader with no producer", found by executing registered paths for the first time — moved one design variant and one emitted claim in v4r4 and were repaired prospectively in v5/v6. Several deviations from the registered analysis (F1 family size, Gate-2 chance severity, emitters committed after the freeze, §28.1 outcomes never emitted, v6's hash re-binding) are undocumented and must be declared. ([03](03_FAILURE_MODES_LIMITATIONS_INTEGRITY.md) §2–3)

## 2. The endpoint, numerically

| | Replications | Reached confirmatory analysis | Companion-swap estimand Δ_R identified |
|---|---|---|---|
| v2 | 4 | 0 | — |
| v3 | 4 | 2 (Gemmas; τ direction-unresolved) | τ estimated, exchangeability failed; different protocol |
| v4r2 | 4 | 0 (Gate 2 not run; would fail) | — |
| v4r3 | 4 | 0 (closed at Gate 1) | — |
| **v4r4** | 4 | **2** (reduced design) | **0** — six quantities `NOT_IDENTIFIED` |
| v5 | 4 | 0 | 0 (D6 ×3, headroom ×2) |
| v6 | 4 | 0 | 0 (probe ×2, headroom ×1, audit ×1) |

Full table with reasons: [02](02_LIFECYCLE_AND_RESULTS.md) §1.

## 3. What can be claimed, by tier

**Registered and signed**
1. Compositional delivery loss exists (L1), verifier-defined, on 2 of 4 checkpoints, one pair, reduced design, per configuration — qwen D(A←B) both orders; e4b position-dependent. L2 withheld; L3 unreachable; L4 licensed on qwen for D(A←B) only.
2. Which constraint pays is model- and position-dependent (Λ −0.515/−0.341 on qwen; −0.110/+0.315 on e4b); Δ_class ≈ 0 on qwen and −0.31/−0.51 on e4b. Described, not estimated across models.
3. Three consecutive registered designs (v4r4 full, v5, v6; twelve replications) ended pre-confirmatory on registered gates — `COMPOSED_HEADROOM_FAILURE` ×5, `COMPOSED_HEADROOM_UNREACHABLE` ×2, `REFERENCE_SUPPORT_NOT_IDENTIFIED` → `PREFREEZE_AUDIT_FAILURE` ×4 (one un-raised) — each carrying "a terminal pre-confirmatory status carries no evidence about the effect".
4. Measurement validation (v4r4 Gate 1): reimplementation 1.000 over 628,800 verdicts; mutation 0 undetected; basis `deterministic_measurement_validated`.

**Diagnostic / screen / post-hoc**
5. Companion identity (Δ_R 0.05–0.10) is an order of magnitude below class (0.40–0.60) and position (0.29–0.35); single-order Δ_R flips sign; an admitted reference out-damages A.
6. Screen-level pair-specific effects dissolve under the registered vacuity bound and length matching.
7. Reference support collapses pre-screen → calibration (35.7 % of candidates move more than the caliper; straddling 7/5/4/4 → 3/0/2/0); ladders are one-sided below ι_A; composed headroom fires falsely on an in-band replication 12–19 % of the time at 24 topics.
8. Two implementation defects (unreachable expansion; expansion rows invisible to the coverage criterion) sit inside v5's attrition: qwen3-4b's C4 would be True over the full table.
9. Exploratory (Arc 1): higher-order interaction with background; order sign reversal; no trade-off region; reasoning re-prioritises without composing — motivation only.

**Not established**
10. Any L3 verdict (pair-specific vs generic load) under the v4+ definition; L2; human-judged compliance; cross-model or cross-configuration effects; that non-identification is a property of the design *family* rather than this library, coordinate and four checkpoints (no ablation exists); that `NOT_IDENTIFIED` means small (it does not, by registered note).

## 4. Recommended framing and the one blocking uncertainty

The evidence supports a **negative-result / identification-methodology paper with one narrow behavioural finding**: a preregistered, gated attempt to measure companion-specific instruction interference beyond difficulty-matched controls produced registered delivery-loss estimates on two of four checkpoints and failed — on registered gates, for measured reasons — to identify the companion counterfactual in three successive designs across twelve replications. The candidate contributions, in the order the repository's own audits support them: (i) the thrice-replicated, prospectively registered non-identification and its measured attrition mechanics; (ii) the demonstration that screen-level "pair-specific" effects dissolve under vacuity/length control and that class and position dominate identity; (iii) the narrow L1 result; (iv) the gated-preregistration methodology and its defect classes.

The single uncertainty that most prevents locking the narrative: **whether the non-identification is a property of the design family or of this candidate library, matching coordinate and four checkpoints.** No counterfactual ablation separates them ([`GAPS.md`](../paper-dci1v4r4-i1/GAPS.md) G16/G17), and two implementation deviations (Gate-2 chance severity; unreachable expansion) sit inside the attrition path.

## 5. Open items before drafting

Documents: a v6 closure record and `CHANGES_SCIENTIFIC.md` entry (all four terminal; the `protocol_hashes_agree` defect and its §32.2 disposition); a ledger of the undocumented analysis deviations ([03](03_FAILURE_MODES_LIMITATIONS_INTEGRITY.md) §3) with "moves a number / moves a verdict"; Related Work and a `.bib`; a reproducibility statement acknowledging workstation-local evidence.

Analyses: the attrition table as one artifact (now [02](02_LIFECYCLE_AND_RESULTS.md) §1); a failure-mode decomposition separating registered outcomes, preregistration underdetermination and implementation defects, with the computed counterfactuals; F1 at k = 6; ι_A/ι_B at n*/m* with §13.4 admission re-run read-only; §17.3 equivalence classifications; the G17 ablations (wider caliper; larger straddling library); Gate-4 MDE promoted from `precision_design.json`; the registered-but-unproduced §22 length decomposition and joint-satisfaction vectors; wording-level heterogeneity; a decision on whether any Arc-1 run is cited (and promoted).

Literature: the seven comparison questions in [04](04_CONTEXT_PRIOR_WORK_PAPER_STATE.md) §2.3.

Decisions: centre of the paper (B vs A-first); design-family vs instance attribution; whether the F1/emitter deviations re-label the L1 results; whether v6's hash failure is an apparatus fault; whether e4b-first D(A←B) counts as a clean cell; whether v3's Δ^A enters; "four checkpoints of two families", not "four models".
