# Batch 1 revision proposal (after the INFEASIBLE pilot of 2026-10-25)

**Status: a PROPOSAL for the researcher. Nothing in it is approved.**

- No GPU run has been made.
- No freeze has been created or modified.
- No approval has been written.
- No reserved topic has been read for calibration.

**Branch:** `feat/batch1-revision-2026-10`.

**Evidence base:** the pilot `runs/pilot-2026-10-25b`, its verified copy and
[`RESULTS_2026-10-25.md`](../RESULTS_2026-10-25.md).

**Untouched:**

- that pilot's freezes, evidence, hashes and approvals;
- the abandoned run `pilot-2026-10-25`;
- the decision records.

**Labels:** every claim is marked **evidence** (computed from stored pilot
data, with the script named) or **hypothesis** (a projection or an
untested mechanism).

---

## 0. Recommendation in brief

| question | answer |
|---|---|
| Does D01 expansion alone suffice? | **Necessary, and probably sufficient for P1 and P3; uncertain for P2.** Expansion has to be paired with fresh topics and a staged measurement (§5), which are design consequences rather than changes to the scientific criteria. On the pilot's data, even perfect measurement of the current library gives P1 ≈ 7, P2 ≈ 1 and P3 ≈ 2 of 16, with P(feasible) ≈ 0 (evidence). Projections put P1 at 0.7–0.9 and P3 at 0.35–0.8 with an expanded library, but P2 at only about 0.1–0.2 (hypothesis). |
| Should A stay unchanged? | **Yes: keep A = "however" × 6, fixed, not re-selected.** A × 4 recovers nothing (P1 ≈ 6, P2 ≈ 3, P3 ≈ 1; evidence). A × 4 and A × 5 are measured only as labelled diagnostics. Quoting the target word (§2.1, D02) is recommended for construct validity. |
| Should D10 matching stay unchanged? | **Yes: keep ±0.10 on raw compliance as the primary rule.** ±0.20 would recover P1 and P3 but not P2 (P2 ≈ 8; evidence), at the cost of comparing instructions 20 points apart in difficulty. Wider tolerances are reported only as labelled sensitivities. More samples improve membership correctness, not coverage (§4). |
| Is the P1/P2/P3 scope still feasible? | **P1: likely. P3: plausible. P2: at risk.** The library's other object types are at floor or ceiling for the Qwen models. Whether count instructions on other objects can sit near A's difficulty there is an empirical question that Stage A answers before the main measurement. §6 decision R9 sets in advance what happens if P2 stays infeasible. |
| What needs your approval? | 13 decisions, R1–R13 in §6. Before the next pilot can be planned in code: R1 library, R2 wording, R3 A, R4 B, R5 matching, R6 topics, R7 staged design and budget, R8 coverage and early stop, R9 the P2 contingency. R10–R13 are also needed before Freeze 1. |

---

## 1. Failure diagnosis

### 1.1 What was checked first

**The membership and feasibility computation is correct (evidence).**
`analysis/infprec.py` is an independent re-implementation of D08, D09, D10
and D11 written for this revision. From the stored counts alone it
reproduces the stored verdict exactly: P1 7, P2 0, P3 1. The code's own
calibration, run on the pilot's `tables.json`, reproduces every population,
support decision, selection and the stored calibration hash
(`tests/batch1/test_pilot_regression.py`).

**Platform-dependent hash: cause found and fixed (evidence).**
- **Cause:** `intervals.newcombe` squared with `x ** 2`. That goes through
  the C library's `pow`, which is not correctly rounded on macOS.
- **Before the fix:** the Mac reproduced 812 of 816 stored interval pairs.
- **After the fix:** the squares are products (`x * x`, exactly rounded under
  IEEE 754), and the Mac reproduces all 816 Linux values and the stored hash
  `ba07458e…`.
- **Decisions:** none changes.

**Scoring checks (evidence).**
- **Paragraph counts at 1.00:** genuine. All 64 answers to "exactly 2
  paragraphs" have 2, and all 64 to "exactly 3" have 3.
- **The `instead` anomaly:** Gemma 3n scores 0.00–0.22 on "instead" at every
  count. Gemma 3n E2B omits the word entirely in 62 of 64 answers to
  "instead × 2", while Qwen-Instruct scores 0.56–0.97 on the same word.
- **Likely cause (hypothesis):** the prompt "Use the word instead exactly 2
  times" can be read as "*instead*, use the word exactly 2 times". The same
  ambiguity is possible for every adverb or connective target, A's
  "however" included. This is a construct-validity issue, not a scoring
  bug (§2.1, R2).

**Truncation review, the three flagged Qwen-Instruct F0 cells (evidence).**
All 5 truncated answers in the pilot are degenerate repetition loops ("No
seam. No join. No gap. …") cut at 512 tokens, not answers stopped mid-thought.

- **Meaning:** the cap does not change what compliance means; they are
  failures either way.
- **Why the flags fired:** cell size. One truncated answer in 32 is 3.1%,
  above the 2% threshold.
- **Recommended sign-off:** reviewed, no action (R11).

**Regeneration is not byte-exact** (95–97% identical in a fresh process).
That affects only rows regenerated on resume. It does not affect stored
evidence, which Freeze 2 binds. It is already disclosed; no change.

### 1.2 Why each comparison failed

All figures are from the stored data. Per model-frame tables are in
`analysis/outputs/diag_by_mf.txt` and `ladders.txt`.

**P1: 7 of 16. G1 needs at least 3 distinct target words matched to A.**

- **B removes candidate words by proof.** Of the 8 library words, only
  indeed, instead, perhaps, although and moreover (at most 8 letters)
  survive B 8; "therefore" adds a sixth at B 10. "nonetheless" and
  "consequently" never survive. So G1 can draw on only 5–6 words.
- **For Qwen3-4B the words that match A are exactly the incompatible ones.**
  Under F0, "consequently × 4" is at 0.62 and "nonetheless × 4" at 0.59,
  against A at 0.62. Both are removed by B, which leaves G1 with 1 word
  ("instead") in all four Qwen3-4B configurations. This is an interaction
  of the library with B, not noise.
- **Difficulty depends on the word, the model and the frame, and the count
  ladder is coarse.** With counts 2/4/6 only, consecutive levels jump by
  0.3–0.5. "moreover" for Qwen-Instruct F0 is at 1.00 / 0.50 / 0.01, against
  A at 0.23. Levels are often not monotone in the count; "although" for
  Gemma E2B F0 is .92 / .39 / .59.

**P2: 0 of 16. It needs at least 2 matched references of another object type.**

- **The other-object families sit at floor or ceiling.**
  - `ep.2` and `ep.3` are at 1.00 in every model-frame.
  - `ec.comma.3` and `ec.comma.6` are at 0.00–0.18, and so are not eligible
    at 20%.
  - `es.4` and `es.7` are at 0.98–1.00 for both Qwen models.
  - `ec.semicolon.1` is at 0.97–1.00 for Qwen.
- **Consequence:** never more than 1 other-object reference matched in any
  model-frame.
- **Not fixable by measurement.** Even counting every reference whose
  interval overlaps ±0.10 as matched, P2 could reach at most 10 of 16
  (`diag_configs.txt`).

**P3: 1 of 16. It needs G3 ≥ 3 and at least 3 matched references of another operation.**

- **12 of the 51 references are uninformative in every model-frame:** at
  least 0.95 everywhere, or below 0.20 everywhere.
  - Ceiling: `ep.2`, `ep.3`, `pro.word.very+really+just`, `nb.max20`,
    `inc.simple`.
  - Floor: `ord.inc4`, `ord.dec4`, `ord.inc6`, `pro.letter.b`, `unq.word5`,
    and both comma counts.
- **Most inclusions and bounds** sit at 0.7–1.0 for Qwen.
- **Consequence:** 0–3 other-operation references matched per model-frame,
  and G3 ≥ 3 fails in 7 of 16 configurations.

### 1.3 Library deficiency or sampling uncertainty?

Most cells have n = 32 (stage-1 only), and a few n = 96 (refined). A
difference interval at n = 32 is about ±0.2 wide, so single memberships are
noisy. But coverage is not mainly a noise problem.

**Method.** Each cell's true compliance is drawn from its Beta posterior,
and the exact D08–D11 rules are applied to the draw (`analysis/infprec.py`,
4,000 draws). This estimates what perfect measurement of the current
library would show.

| contrast | coverage at perfect precision, posterior mean (90% interval) | P(feasible) |
|---|---|---|
| P1 | 6.9 / 16 (4–10) | 0.003 |
| P2 | 0.7 / 16 (0–3) | 0.000 |
| P3 | 2.0 / 16 (0–5) | 0.000 |

**Conclusion (evidence).** The current library cannot meet the target
however precisely it is measured. Additional sampling of the same library
would not resolve the failure, which is structural: a library deficiency,
compounded by the B-compatibility interaction for P1. Sampling uncertainty
matters for which references are members, not for how many configurations
can be supported.

### 1.4 Does A contribute?

These sensitivities are **labelled; none is a proposal**
(`analysis/outputs/sensitivity.txt`, perfect-precision posterior).

| variant | P1 | P2 | P3 | P(all feasible) |
|---|---|---|---|---|
| design: A × 6, ±0.10 | 6.9 | 0.7 | 2.0 | 0.000 |
| A × 4, ±0.10 | 6.3 | 2.9 | 1.2 | 0.000 |
| A × 6, ±0.15 | 11.1 | 3.6 | 8.0 | 0.000 |
| A × 6, ±0.20 | 13.9 | 7.7 | 12.6 | 0.025 |
| A × 4, ±0.15 | 11.1 | 8.4 | 4.7 | 0.000 |

**A's role.** It is not the main cause. A × 6 varies strongly by frame
(Qwen-Instruct 0.23 under F0 and 0.68 under F1; Gemma E2B 0.55 and 0.28),
which spreads the targets the references must hit. But no A count rescues
coverage, and A × 4 is at the ceiling for Qwen-Instruct (0.92, 1.00).

---

## 2. Revised D01 specification (library v2)

The full candidate table is
[`candidate_library_v2.json`](candidate_library_v2.json), generated by
`analysis/build_candidates.py`. It has 161 references: the 51 existing ones
plus 110 candidates.

### 2.1 Rules

1. **Ladders, not single points.** Each family gets several parameter
   levels spanning floor to ceiling, so some level can land near A in each
   model-frame. Levels are chosen from where the families sat in the pilot,
   never from where A sits.
2. **B compatibility by construction.**
   - **Lengths:** every new target word and required word has at most 8
     letters, so no candidate is incompatible with B 8 or B 10 by proof.
   - **Witnesses:** compatibility is still established only by a
     constructed witness (`compatibility.py`), never by model behaviour.
   - **Long-word references:** the 7 existing ones are kept unchanged, for
     continuity.
3. **Hygiene.** No target, required or forbidden word may occur in any
   topic: bank v1 (including the reserved 480) and the fresh pilot topics.
   Checked for all new words against bank v1: 0 occurrences (“rather”,
   “still”, “end”, “and”, “of” were rejected for occurring).
4. **Distinct, verifiable, non-vacuous.** Every candidate needs:
   - a deterministic verifier with a witness and a violation self-test;
   - the existing non-vacuity rules;
   - a review that it is not a paraphrase of another candidate.
5. **Nothing is assumed matched.** Stage A measures every candidate on
   screening topics, and only Stage C topics decide membership (§5).
6. **Wording (D02, recommended): quote target words.** For example: Use the
   word "however" exactly 6 times. This applies to A and to every word-target
   reference (counts, inclusions, prohibitions, positional), and removes the
   imperative misreading behind the `instead` anomaly.
   - **Cost:** A's measured difficulty changes, but A is re-measured anyway.
   - **Comparability:** prompts are no longer word-for-word comparable with
     pilot 1 or DCI-1.

### 2.2 Taxonomy and counts

| population | operation / object | existing | v2 total | ladder |
|---|---|---|---|---|
| G2 → G1 (P1) | exact count / word | 22 | 72 | 13 connectives of at most 8 letters (5 existing + thus, hence, besides, anyway, likewise, overall, notably, namely) × counts 2–6; the 7 long-word references kept |
| G4 → G3 (P2) | exact count / punctuation | 4 | 18 | semicolon 1–4, colon 1–3, question mark 1–3, exclamation 1–3, opening parenthesis 1–3, comma 3, 6 |
| | exact count / sentence | 2 | 7 | 3–9 sentences |
| | exact count / paragraph | 2 | 5 | 2–6 paragraphs |
| | exact count / numeral (new object type) | 0 | 3 | 1–3 numbers written as digits |
| G6 → G5 (P3) | prohibition / letter | 2 | 7 | z, b + q, x, j, k, v (by letter frequency) |
| | prohibition / word | 2 | 4 | + "also", "this" |
| | required inclusion / word | 4 | 8 | + 2, 3, 4, 5 unrelated nouns of at most 8 letters |
| | numerical bound / sentence | 3 | 9 | max 6, 8, 10, 12, 20; min 10, 12, 14, 16 words per sentence |
| | uniqueness | 3 | 9 | no repeated word of 4–7 letters; distinct openers over 3–6 sentences; no repeated bigram |
| | ordering | 4 | 8 | length order over 3, 4, 6 sentences (increasing), 3, 4 (decreasing); alphabetical openers 3–5 |
| | relational | 3 | 8 | word and letter chains over 2, 3 sentences; shared word of 3–5 letters |
| | positional (new operation) | 0 | 3 | start with a named word; end with a question; end with a named word |

### 2.3 Scoring

- **Existing families.** 104 of the 110 candidates are new parameter values
  of verifier families that already exist and are tested. They change no
  verifier code.
- **Two new families, to implement and self-test before any measurement:**
  - `b1.exact_numeral_count`: tokens matching `[0-9]+` (with an optional
    decimal or thousands part), counted on the answer text.
  - `b1.positional`: a start or end word (folded, punctuation stripped) or a
    final "?". Both need witnesses for each B limit and violation tests.
- **Weights (D13).** Unchanged. With 5 counts per word, a word can
  contribute several variant shares; see R10.
- **Versioning.** v1 (51 references) stays the frozen library of pilot 1,
  and the regression tests keep reading it. v2 is selected by the next
  Freeze 1, so pilot 1's data can always be re-derived (§6 R12).

---

## 3. Revised protocol: what changes and why

| item | status | justification |
|---|---|---|
| Research question; P1/P2/P3 contrasts; G1–G6 hierarchy and nesting | **unchanged** | — |
| Models, frames, decoding (D12 as amended), B task wording, 60–120 word task | **unchanged** | — |
| B limits 8 and 10 (D07) | **unchanged, fixed** (not re-selected) | preserves the comparison; still checked informative on the new topics (R4) |
| A = however × 6 (D08) | **unchanged, fixed**; A × 4 and A × 5 measured as diagnostics only | §1.4 (R3) |
| Eligibility at 20% OR across model-frames (D09) | **unchanged** | — |
| Matching ±0.10 on raw compliance (D10) | **unchanged as the primary rule**; posterior P(match) and labelled sensitivities added to reporting | §1.3, §1.4 (R5) |
| Coverage minima and target 12/16, 3 models, both B (D11) | **unchanged** | not relaxed (R8) |
| Library (D01) | **revised: v2** | **necessary**: the deficiency is structural (§1.3) (R1) |
| Topics (D05) | **revised: fresh screening set T1 (48) and membership set T2 (96)** | **necessary**: the pilot's 96 topics informed the revision, and the reserved 480 are untouchable (R6) |
| Stages (D05/D06) | **revised: Stages A–D** with a held-out membership set | **necessary for validity at this library size**: screening on one set and deciding membership on another avoids the winner's curse (R7) |
| Budget | **revised: at most 185,000 responses** (was 30,976) | at about 200 responses/s across both H100s, roughly 25 GPU-minutes (R7) |
| Wording (D02): quote target words | **recommended** | construct validity (§1.1) (R2) |
| Interval arithmetic (D10 implementation) | **fixed** (`x * x`) | reproducibility (§1.1) (R12) |
| Truncation-review threshold | **optional**: also require at least 2 truncated rows | avoids 1-in-32 false alarms (R11) |

---

## 4. Feasibility analysis

**Evidence:**

- **The current library fails structurally** (§1.3).
- **Sampling more does not change coverage materially.** Under the
  projection below, coverage measured at n = 96 or n = 192 per cell is
  within about 0.5 configurations of perfect precision. Sampling decides
  which references are members, and how stable they are.

**Hypothesis: a projection** (`analysis/project.py`,
`outputs/projection.txt`). New references are assumed to behave like
resampled existing ones of the same group:

- whole 8-cell difficulty profiles are resampled, and each word's count
  ladder is kept together;
- the "graded" pool excludes profiles at floor or ceiling everywhere;
- every synthetic word is compatible with both B limits.

| library: words × 3 counts / other-object / other-operation | P(P1) | P(P2) | P(P3) | P(all) |
|---|---|---|---|---|
| 5 / 8 / 21 (current, short words only) | 0.03 | 0.00 | 0.00–0.01 | 0.00 |
| 10 / 16 / 30, graded | 0.68 | 0.03 | 0.36 | 0.01 |
| 12 / 20 / 36, graded | 0.88 | 0.06–0.10 | 0.66 | 0.04–0.06 |
| 15 / 24 / 40, graded | 0.97 | 0.17–0.21 | 0.77–0.80 | 0.15–0.17 |

How to read this:

- **The direction is clear; the size is uncertain.**
  - **P1** recovers with more short connectives (the v2 library has 13 short
    words × 5 counts).
  - **P3** recovers with graded other-operation ladders.
  - **P2** is the binding risk.
- **Why the projection is pessimistic for P2.** It can only resample the
  few graded other-object profiles that exist (semicolons, sentences), and
  those are at the ceiling for both Qwen models.
- **What could change P2.** The v2 ladders (harder sentence, paragraph and
  semicolon levels, colons, question and exclamation marks, numerals) may
  sit lower for Qwen. That is an empirical question that Stage A answers
  cheaply.
- **No coverage guarantee.** Additional sampling does not guarantee
  recovery for any contrast whose library cannot reach A's difficulty.

**Changes that will not help (evidence):**

- re-selecting A from {2, 4, 6};
- more sampling of the current library;
- tolerance ±0.15, for P2.

---

## 5. Pilot implementation and execution plan (not run)

### 5.1 Topics: isolation safeguards

- **A new bank, v2.**
  - **Size:** 144 new questions, 12 per area: T1 = 48 (4 per area) and
    T2 = 96 (8 per area).
  - **Authoring and review:** as for v1, with the D05 procedure of
    2026-10-25. The checks are word-overlap and rare-stem screens; a
    semantic review blind to the author, under the containment rule; a
    fresh second pass; and your reading.
  - **Screened against:** the 2,096 historical records, all 576 v1
    questions (the 96 used and the 480 reserved) and each other.
- **No code path reads the reserved 480.** The existing test that no Batch 1
  code reads them extends to the new stages.
- **Hygiene** includes every v2 target word.
- **Determinism:** the split T1/T2 is a pure function of ids and a fixed
  seed.

### 5.2 Stages

| stage | topics | what | output |
|---|---|---|---|
| **A: screen** | T1 (48) | every v2 reference, A × 4/5/6, B 8 and B 10, task only; 8 model-frames | stand-alone tables on T1; eligibility screen; verifier and outcome health; witness and hygiene checks already passed before Freeze 1 |
| **B: coverage forecast** | T1 | posterior coverage at perfect precision for P1–P3 (the `infprec` method, in the package) | **early stop** if P(feasible) < 0.2 for any contrast: report "library-limited for P_x" and stop before T2 (R8, R9) |
| **C: membership measurement** | T2 (96) | the carried references (§5.3), A × 6, B 8 and B 10, task only; all at the same n on the same topics (paired) | the only data that decide eligibility, matching and membership |
| **C′: boundary top-up** (optional, prespecified) | T2, second draw | references whose T2 difference interval straddles ±0.10 in any configuration (at most 40) | pooled two-draw estimates for those references; the bootstrap is over topic clusters |
| **D: verdict** | T2 | D08–D11 rules unchanged; D14 diagnostics with 200 topic-cluster resamples on T2; T1-versus-T2 agreement reported (a winner's-curse diagnostic) | Freeze 2 only if you authorise it; `REVISION_REQUIRED` otherwise |

### 5.3 Rules, fixed in Freeze 1 before Stage A

- **Carry rule (T1 → T2).** A reference is carried if it is eligible on T1,
  B-compatible, and has posterior P(|θ_X − θ_A| ≤ 0.10) ≥ 0.05 in at least
  one configuration.
  - **Generous on purpose:** wide pruning on T1 would select noise.
  - **Cap:** 110 references, keeping the highest maximum posterior.
- **No pooling across sets.** T1 data never enter T2 membership. T1 only
  chooses what to measure, and supplies the early stop.
- **Fixed A and B.** A and B are not re-selected. The run stops with
  `A_NOT_ADMISSIBLE` if A × 6 fails D08 admissibility on T2, or
  `B_NOT_INFORMATIVE` if B 8 or B 10 fails D07 informativeness on T2.

### 5.4 Budget and resources

These use the measured H100 rates at 512 requests per call and CUDA graphs
off: 58–143 rows/s per model, about 200/s over two GPUs.

| stage | rows (maximum) | GPU time |
|---|---|---|
| A | (161 + 3 + 2) × 8 × 48 + 384 = **64,128** | about 6 min + loads |
| C | (110 + 1 + 2) × 8 × 96 + 384 = **87,168** | about 8 min + loads |
| C′ | 40 × 8 × 96 = **30,720** | about 3 min |
| **cap** | **185,000** | about 25 min in total |

- **Storage:** about 1.2 GB for the run root.
- **Smoke test:** on library v2, before Freeze 1.

**Stopping conditions:**

- any refusal or technical exhaustion (as now);
- the Stage B early stop;
- `A_NOT_ADMISSIBLE` or `B_NOT_INFORMATIVE`;
- the budget cap.

**Success condition:** the D11 feasibility rule, unchanged, on T2.

### 5.5 Commands

To be implemented after approval; names indicative:

```bash
P="python -m dci.batch1"
$P validate-library --library v2 && $P validate-verifiers && $P check-compatibility --library v2
$P write-review-artifacts            # v2 library, compatibility, topic v2 screens, decisions
$P smoke-plan && $P smoke ...        # on v2, with --environment-lock
$P freeze-protocol --root R ...      # binds v2, T1/T2, carry/top-up/early-stop rules
$P plan --root R --stage screen && $P execute ... --devices 0,1 && $P score --root R --stage screen
$P forecast-coverage --root R        # Stage B; exits non-zero on the early stop
$P select-carry --root R             # the T1 -> T2 carried set, hash-bound like the Stage 2 plan
$P execute --root R --stage membership ... && $P score ...
$P select-topup --root R && $P execute --root R --stage topup ... && $P score ...   # if C' is approved
$P finalize-calibration --root R && $P report-coverage --root R && $P freeze-membership --root R
```

---

## 6. Decision register

| # | decision | options | evidence | risks | recommendation |
|---|---|---|---|---|---|
| **R1** | D01: library v2 | (a) the full v2 candidate pool (161); (b) words only (P1 only); (c) defer | §1.2–1.3; projection §4 | more variants to verify and compute; some candidates will be uninformative (expected; screening drops them) | **(a)** |
| **R2** | D02: quote target words in every frame | (a) quote, for A and all word targets; (b) keep, choosing unambiguous words; (c) keep as is | the `instead` anomaly (§1.1) | prompts not comparable with pilot 1 or DCI-1; A's difficulty shifts (re-measured anyway) | **(a)** |
| **R3** | D08: A | (a) fix A × 6, with A × 4 and × 5 diagnostics only; (b) re-select by D08 on T1 from {4, 5, 6} | §1.4: no A count rescues coverage | (b) adds an adaptive choice and breaks the comparison with pilot 1 | **(a)** |
| **R4** | D07: B | (a) fix 8 and 10, check informativeness on T2; (b) re-select | pilot: 8/10 the only admissible pair | (b) adds adaptivity | **(a)** |
| **R5** | D10: matching | (a) keep ±0.10 primary, plus posterior P(match) and labelled ±0.15 / ±0.20 / confident / iota sensitivities; (b) widen | §1.3–1.4 | (a) may still leave P2 short; (b) weakens "equally difficult" | **(a)** |
| **R6** | D05: topics | (a) a fresh bank v2: T1 48 + T2 96; (b) larger T2 (144) for precision | the reserved 480 must stay unseen | authoring and review effort; more topics give more precision | **(a)**; (b) if you want tighter memberships |
| **R7** | D05/D06: stages and budget | (a) Stages A–D, carry rule, C′ top-up, cap 185,000; (b) without C′ (cap 155,000) | precision review; §5.4 | C′ is adaptive, though prespecified and topic-clustered | **(a)** |
| **R8** | D11 and early stop | (a) D11 unchanged, early stop if T1 P(feasible) < 0.2 for any contrast; (b) no early stop | §1.3 method | a 0.2 threshold could stop a design that might pass | **(a)** |
| **R9** | P2 contingency, decided now | (a) one further P2-only library iteration (v2.1, new screening topics), then (b); (b) report P2 not estimable and continue with P1 and P3 under an explicit scope amendment; (c) stop the study | §4: P2 is the binding risk | (b) narrows the claims; deciding afterwards would be adaptive | **(a) then (b)** |
| **R10** | D13: weights with ladders | (a) unchanged; (b) weight words equally, then counts within a word | more count variants per word | (a) lets a word with several matched counts carry more weight | **(b)**, a small change that keeps D13's intent |
| **R11** | D14: truncation | sign off the pilot's 3 cells as reviewed; optionally require at least 2 truncated rows for the flag | §1.1 | — | **sign off; adopt the 2-row minimum** |
| **R12** | technical | (a) the `x * x` interval fix; (b) a versioned library (v1 frozen, v2 for the next pilot); (c) promote the pilot evidence: compact files (freezes, tables, calibration, approvals, lock: about 2 MB) in git, and the generation and scored rows (about 200 MB) in Git LFS or an archive referenced by hash; (d) an independent audit of `9b77370..0cde3b9` and of this branch before the next Freeze 1; (e) approvals written by you | §1.1; repo evidence rules | — | **all five**; (c) location is your call |
| **R13** | D12 | same host and environment; re-approve for the new code hashes; smoke test on v2 | — | — | **re-approve after the v2 smoke test** |

---

## 7. Audit report (this branch)

### Code changed

| file | change |
|---|---|
| `src/dci/batch1/intervals.py` | `newcombe` squares as products |

- **Platforms:** values are unchanged on Linux and now identical on macOS.
- **Hashes:** this is a D10 implementing module (D10's payload hash changes)
  and a Freeze 1 rule module. The frozen pilot is validated at `0cde3b9`,
  on Linux, as before.

### Added

- **`tests/batch1/test_pilot_regression.py`:** 4 tests on the original pilot
  data. The code reproduces the pilot's decisions (A, B, eligibility, all 16
  configurations' populations and support, the 7/0/1 verdict) and the stored
  calibration hash.
- **`tests/batch1/fixtures/pilot_2026_10_25b/`:** the pilot's own
  `tables.json` and `freeze1.json` (byte-identical), plus an excerpt of
  `freeze2.json` with the full file's sha256.
- **`docs/batch1/revision/`:**
  - this proposal;
  - `candidate_library_v2.json`, with its generator;
  - the analysis scripts (`infprec.py`, `project.py`) and their outputs.

### Not implemented (after approval)

- **Library and verifiers:** library v2 as a versioned module; the two new
  verifier families; witness-pool extensions.
- **Topics:** topic bank v2.
- **Stages:** Stages A–D in the design, the runner, evidence and freezes,
  plus coverage forecasting and the carry and top-up selection.
- **Reporting:** posterior P(match) reporting.
- **Evidence:** promotion of pilot 1.

This is several days of implementation and review, followed by an audit.

### Tests

The results of the full Batch 1 CPU tier on this branch are recorded in the
commit message.

### Uncertainties and limits

- **Projections:** they rest on exchangeability with existing references;
  real v2 difficulties may differ in either direction.
- **The posterior method** treats cells as independent with uniform priors.
- **The `instead` anomaly:** the wording-ambiguity explanation is a
  hypothesis; quoting tests it directly.
- **Construct:** for P2 and P3, whether count, ordering and relational
  instructions that land at A's difficulty measure "equally difficult"
  interference is a question about the construct, not something
  calibration can settle.
- **Adaptivity:** the revision was designed with pilot 1's data. Its topics
  are excluded from all future measurement, and T1/T2 are fresh.
