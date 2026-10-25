# Batch 1 pilot protocol: plain-language review of every decision

**Update 2026-10-25:** your decisions of that day are applied (Python 3.12 for the orchestrator, replacing 3.11; P3 minimum 3; the D05 topic edits; the CUDA backend and one worker per GPU) and are written up for transcription in [`DECISIONS_2026-10-25.md`](DECISIONS_2026-10-25.md). Where this document says otherwise, that file and the code are current.

**For:** the researcher, or any reviewer new to the project. No knowledge of
the code or of earlier DCI studies is assumed. **Status on 2026-10-19:**
fourteen scientific decisions (D01–D14) define the pilot. One part of one
decision, Python 3.11 for the controlling program (in D12), was approved
by you in conversation; on 2026-10-25 you replaced it with 3.12. Every other part of every decision is **proposed and
awaiting your approval**. Nothing has been run on a model.

Part of the Batch 1 review package; start at
[`RESEARCHER_REVIEW.md`](RESEARCHER_REVIEW.md).

---

## 1. The study in brief

### 1.1 The research question

When a language model is given two instructions at once, one can make it
worse at following the other. Earlier DCI studies measured this for one pair:

- **A:** "Use the word *however* exactly N times."
- **B:** "Use only words of m letters or fewer."

They asked whether adding A makes the model worse at following B, and by more
than adding some other, comparable instruction would. The answer turned out
to depend heavily on *which* comparison instructions were used, on the model,
on the exact wording, and on the order of the two instructions.

This study is a **measurement-method study**. Its question is:

> Which restrictions on choosing the comparison instructions materially
> change the estimated interference, and how sensitive is that to the model,
> the wording, and the order?

### 1.2 Key terms

| term | meaning | example |
|---|---|---|
| **instruction** (or *constraint*) | one verifiable formatting rule, checked by a program | "Do not use the letter b." |
| **compliance** | the share of a model's answers that satisfy an instruction | 46 of 100 answers use *however* exactly 4 times → 46% |
| **reference instruction** (X) | a comparison instruction. Interference by A is judged against the interference caused by references | "Use the word *indeed* exactly 4 times." |
| **operation** / **object type** | what an instruction does / what it does it to | "exactly 3 commas" = *exact count* of *punctuation* |
| **wording frame** | one of two phrasings of every instruction: **F0** imperative ("Use…"), **F1** requirement ("Your answer must…") | F1: "Your answer must contain the word indeed exactly 4 times." |
| **model-frame** | one model with one wording frame: 4 models × 2 frames = 8 | Qwen3-4B, F1 |
| **configuration** | one model-frame with one of the two chosen B limits: 16 in all | Qwen3-4B, F1, B ≤ 10 letters |
| **difficulty-matched** | a reference whose stand-alone compliance is within 10 percentage points of A's, in that model-frame | A 46%, X 52% → matched |
| **G1–G6** | six populations of reference instructions, from narrow to broad (§1.4) | |
| **P1–P3** | the three primary comparisons between populations (§1.5) | |
| **pilot** | Batch 1: a calibration run in which every instruction is given **alone**, never combined | |
| **Freeze 1 / Freeze 2** | tamper-evident records (hashes) of the protocol before the pilot (1) and of the pilot's results and selections (2) | |

### 1.3 Why references are needed

Any extra instruction costs a model something: it has more to attend to.
To see whether A interferes with B *because of what A asks*, the cost of A is
compared with the cost of other instructions of similar difficulty. In the
study's notation, D(B ← X) is how much B's compliance drops when X is added,
and the reference-relative interference of A is

> Δ_G(A) = D(B ← A) − weighted average over references X in population G of D(B ← X).

The answer depends on G. The study does not assume one "right" reference
set; it measures how much the answer moves when G changes.

### 1.4 The six reference populations

All exclude A. For each configuration:

| population | same operation as A (exact count)? | same object type as A (word)? | difficulty-matched to A? |
|---|---|---|---|
| **G1** | yes | yes | yes |
| G2 | yes | yes | no requirement |
| **G3** | yes | any | yes |
| G4 | yes | any | no requirement |
| **G5** | any | any | yes |
| G6 | any | any | no requirement |

For example, "use *indeed* exactly 4 times" can be in G1; "exactly 3 commas"
in G3 (same operation, other object); "include the word *simple*" only in G5
(another operation). Every reference must also be **eligible** (followed at
least 20% of the time somewhere; D09) and **compatible** with the chosen B
limit (it must be possible to satisfy both; for example *consequently* has 12
letters and cannot appear under B ≤ 11).

### 1.5 The three primary comparisons

Each comparison relaxes one restriction and asks whether the estimate moves:
δ = Δ_restricted − Δ_relaxed.

| comparison | populations | restriction relaxed |
|---|---|---|
| **P1** | G1 vs G2 | difficulty matching |
| **P2** | G1 vs G3 | same object type |
| **P3** | G3 vs G5 | same operation |

A change of 5 points or more is provisionally "material", 10 or more
"large". Those thresholds belong to the later confirmatory analysis, not to
this pilot.

### 1.6 What the pilot measures, and what it does not

**Measures:** stand-alone compliance only, meaning how often each model
follows each instruction given alone, in each wording, on new everyday
questions:

- the task alone (no instruction), to measure chance compliance;
- each of 3 A counts (N = 2, 4, 6);
- each of 6 B limits (m = 8 to 13 letters);
- each of 51 reference instructions.

**Does not measure:** interference. No prompt in the pilot contains two
instructions, and the code cannot build one (a test and Freeze 2 check
this). No interference estimate exists or can be computed from pilot data,
so nothing about interference can influence the selections below.

**Size:** 15,616 responses in Stage 1, at most 15,360 in Stage 2, 30,976 in
total, on 4 models (Gemma 3n E2B and E4B; Qwen3-4B with thinking off; Qwen3-4B
Instruct 2507).

### 1.7 How A, B and the reference populations are chosen

In order, all from stand-alone pilot data only:

1. **Stage 1:** every stand-alone instruction is tried on the same 32 new
   questions (D05).
2. **Stage 2:** instructions whose Stage 1 result is close to a decision
   boundary get 64 more questions, up to 240 such cells (D06).
3. **B:** choose two limits m whose compliance differs clearly and is
   neither near 0% nor near 100% (D07).
4. **A:** choose one count N for all models and wordings, with compliance
   neither near 0% nor near 100% in most model-frames (D08).
5. **Eligibility:** keep references followed at least 20% of the time in
   some model-frame (D09).
6. **Populations:** in each configuration, build G1–G6 from eligible,
   compatible references, using the ±10-point matching rule (D10).
   **Every qualifying reference is kept.**
7. **Coverage:** decide in which configurations each comparison is
   estimable, and whether the study as a whole is feasible (D11).
8. **Freeze 2** records all of it before any combined prompt exists.

### 1.8 Why model and wording differences matter

The earlier studies found interference that changed sign between models and
between orders. If the study averaged over models or wordings it could
report an effect that holds for none of them. So every choice that can be
made per model-frame is made per model-frame (matching, populations,
coverage), and every choice that must be shared (one A count, two B limits,
one eligibility pool) is required to work across models rather than being
tuned to one. A model where it fails is reported, not dropped.

### 1.9 What happens after this review

You approve or revise each decision → Freeze 1 → environment attestation and
a small smoke test on the generation computer → the pilot (Stage 1, Stage 2)
→ Freeze 2 → your review of Freeze 2 → Batch 2 (the experiment with combined
instructions), which needs separate approval.

## 2. Status of every decision

*Origin:* **design** = the research brief's rule, operationalised;
**proposed** = a choice the implementation had to make. *Status* is the
formal state in `approvals.json`: no decision is APPROVED there yet.

| | decision | origin | status | recommendation |
|---|---|---|---|---|
| D01 | parameters of 29 new instruction variants | proposed | awaiting approval | approve |
| D02 | the two wording frames and the prompt | proposed | awaiting approval | approve |
| D03 | how text is counted (words, sentences) | proposed | awaiting approval | approve |
| D04 | what counts as compliance; empty and failed answers | proposed | awaiting approval | approve |
| D05 | pilot size and the topic bank | proposed | awaiting approval | **revise if any question in `TOPIC_REVIEW.md` is unacceptable; otherwise approve** |
| D06 | Stage 2 rule and stage completeness | proposed | awaiting approval | approve |
| D07 | choosing the two B limits | proposed | awaiting approval | approve |
| D08 | choosing the one A count | proposed | awaiting approval | approve |
| D09 | eligibility (20%) | design | awaiting approval | approve with the disclosure |
| D10 | difficulty matching (±10 points) | design | awaiting approval | approve with the disclosure |
| D11 | coverage minimums and feasibility target | design | awaiting approval | **revise: P3 minimum 3** |
| D12 | models, decoding, length cap, seeds, backend, Python | proposed | **Python 3.12 decided by you (2026-10-25; replaces 3.11); the rest awaiting** | approve after the smoke test |
| D13 | object types and reference weights | proposed | awaiting approval | approve with the disclosure |
| D14 | stability diagnostics | proposed | awaiting approval | approve as a diagnostic |

The checklist of everything needed before Freeze 1 is
[`FINAL_APPROVAL_CHECKLIST.md`](FINAL_APPROVAL_CHECKLIST.md).

## 3. The decisions

Each decision below has nine parts: the question, why it matters, the
proposal, the justification, the alternatives, the trade-offs and
uncertainties, a recommendation, the supporting evidence, and the files to
inspect. All paths are relative to the repository root.

---

### D01 — Parameters of the 29 proposed instruction variants

1. **The question.** The brief fixed 22 word-count references (8 words ×
   counts 2, 4, 6, plus *nonetheless* and *consequently* × 2, 4) and named 29
   more slots by type. What exact rule fills each of the 29?
2. **Why it matters.** The references are what A is compared with. Their
   difficulty spread decides how many can match A, and so whether the
   comparisons are estimable at all.
3. **Proposal.**
   - exact counts: commas 3 and 6, semicolons 1 and 2, sentences 4 and 7,
     paragraphs 2 and 3;
   - inclusion: *simple*; *window* and *garden*; *silver*, *morning* and
     *quiet*; *remarkable*;
   - prohibition: *the*; *very*/*really*/*just*; the letters z and b;
   - sentence length bounds: ≤ 20 words, ≤ 12 words, ≥ 10 words;
   - uniqueness: no word of 5+ letters twice; no repeated word pair; at least
     3 sentences with different first words;
   - ordering: 4 sentences of increasing length; 4 decreasing; 4 with first
     words in alphabetical order; 6 increasing;
   - relational: 3+ sentences where each starts with the previous sentence's
     last word; with its last letter; or shares a 4+-letter word with it.
4. **Justification.** Each fills its slot with an instruction a program can
   check exactly. Within a slot, the variants span easy to hard, so some can
   land near A's difficulty. Every variant that needs several sentences
   states and enforces a minimum, so a one-sentence answer cannot pass.
5. **Alternatives.** Different words or counts; fewer hard variants;
   replacing "do not use *the*" with a content word.
6. **Trade-offs.** The chain and ordering variants are probably very hard
   and may be ineligible; eligibility (D09) handles that without changing
   the library. "Do not use *the*" is extreme in English.
7. **Recommendation: approve.** Optionally swap `pro.word.the` for a content
   word, before Freeze 1 only.
8. **Evidence.** Every variant has a constructed passing example and a
   failing example, checked by its verifier (`validate-verifiers`), and a
   60–120-word example that also satisfies B, for every compatible B limit
   (305 of 305 cells; confirmed by the auditor's own independent checker).
9. **Files.** `src/dci/batch1/library.py`, `src/dci/batch1/verifiers.py`,
   `docs/batch1/library_review.md`, `docs/batch1/compatibility_review.md`.

---

### D02 — The two wording frames and the prompt

1. **The question.** How exactly is each instruction phrased, and what does
   the whole prompt look like?
2. **Why it matters.** Wording ("paraphrase") changed results in earlier
   studies; the study measures that sensitivity, so the two wordings must be
   fixed in advance.
3. **Proposal.** **F0** imperative ("Use the word indeed exactly 4 times.")
   and **F1** requirement ("Your answer must contain the word indeed exactly
   4 times."). A and B keep the historical v8.1 wordings. The prompt is
   unchanged from earlier studies: the question, "Answer in 60 to 120 words.",
   one numbered instruction, then "Answer:".
4. **Justification.** Two systematically different phrasings of every
   instruction let wording effects be estimated, not averaged away. Keeping
   A, B and the template makes the pilot comparable with history.
5. **Alternatives.** More frames; free paraphrases per instruction.
6. **Trade-offs.** Two frames sample wording variation narrowly. One
   cosmetic inconsistency: B's F1 says "the answer" where the others say
   "your answer". It is kept because B's wording is historical.
7. **Recommendation: approve.**
8. **Evidence.** A test renders every parameter in both frames; the
   verifier never sees the frame.
9. **Files.** `src/dci/batch1/library.py`, `src/dci/batch1/design.py`,
   `src/dci/batch1/config.py`, `docs/batch1/library_review.md`.

---

### D03 — How text is counted

1. **The question.** What is a word, a sentence, a paragraph?
2. **Why it matters.** Every verdict depends on it. For example, is
   "don't" one word or two for "no word longer than 8 letters"?
3. **Proposal.** The historical B checker's rules:
   - a word is a run of letters, so apostrophes and hyphens split words
     ("don't" = "don" + "t"), digits are not letters, and accented letters
     count;
   - sentences are split with the certified sentence splitter of the earlier
     protocol, so a heading or list item counts as a sentence;
   - paragraphs are blocks separated by a blank line.
4. **Justification.** Reusing the historical definitions keeps B's verdicts
   identical to earlier studies' and avoids inventing new semantics.
5. **Alternatives.** Unicode normalisation; treating markdown structure
   specially.
6. **Trade-offs.** A zero-width space splits a word, which a model could in
   principle exploit under B; every scored answer records such characters,
   so any use is visible.
7. **Recommendation: approve.**
8. **Evidence.** Tests compare the copied rules with the historical code,
   byte for byte where carried.
9. **Files.** `src/dci/batch1/text.py`, `src/dci/verifiers/rules.py`.

---

### D04 — What counts as compliance; empty and failed answers

1. **The question.** When does an answer comply, and what happens to blank
   answers and to technical failures?
2. **Why it matters.** Treating a blank answer as "no data" would make
   instructions that cause blank answers look easier than they are.
   Treating a crash as a failure would penalise the instruction for a
   machine fault.
3. **Proposal.**
   - An answer complies when the checker passes it and it is not blank, not
     cut off by the length cap, and long enough to be meaningful (at least
     20 words for prohibitions, bounds and B, as historically).
   - A **blank** answer counts in the denominator and never complies, and
     is not regenerated.
   - A **technical failure** is never evidence. It is logged separately and
     retried; after 3 failures of the same row it is not retried, and the
     stage stays incomplete until you decide (new, re-audit R4.4).
4. **Justification.** Blank answers are behaviour; crashes are not. A retry
   limit stops a prompt that always fails from looping forever, without
   inventing a missing-data rule.
5. **Alternatives.** Excluding blank answers; a missing-data rule after N
   failures.
6. **Trade-offs.** A deterministic failure blocks the pilot until you act.
   That is deliberate.
7. **Recommendation: approve.**
8. **Evidence.** Audit F1 (fixed); re-audit B confirmed it with rows built
   by the real backend code; tests in `tests/batch1/test_outcomes_and_runner.py`
   and `tests/batch1/test_pins_and_provenance.py`.
9. **Files.** `src/dci/batch1/outcomes.py`, `src/dci/batch1/verifiers.py`,
   `src/dci/batch1/scoring.py`, `src/dci/batch1/runner.py`.

---

### D05 — Pilot size and the topic bank

1. **The question.** How many questions per instruction in Stage 1, and
   which questions?
2. **Why it matters.** Sample size decides how noisy every pilot rate is.
   The questions must be new so that the pilot is an independent
   measurement and the reserved set stays unseen.
3. **Proposal.** 32 Stage 1 questions shared by every instruction (task
   alone: 64 answers per model), 64 Stage 2 questions, 96 pilot questions in
   all, from a new bank of 576 with 480 reserved. After the re-audit, 88
   questions were rewritten to remove restatements of historical questions
   and duplicates.
4. **Justification.** A shared question set means every instruction is
   compared on the same questions. The precision simulations showed that
   larger budgets barely improve the selections.
5. **Alternatives.** More Stage 1 questions for A and B only; more Stage 2
   cells (simulated: little gain).
6. **Trade-offs.** 32 questions give noisy single rates (about ±17 points);
   Stage 2 targets the borderline ones.
7. **Recommendation: approve after reading
   [`TOPIC_REVIEW.md`](TOPIC_REVIEW.md);** revise any question you find
   unacceptable first.
8. **Evidence.** Topic review (88 replacements, three semantic passes, clean
   screens, balanced features); re-audit R1; `CALIBRATION_PRECISION_REVIEW.md`.
9. **Files.** `src/dci/batch1/data/topics_source.json`,
   `src/dci/batch1/topics.py`, `src/dci/batch1/design.py`,
   `docs/batch1/TOPIC_REVIEW.md`.

---

### D06 — Stage 2 rule and stage completeness

1. **The question.** Which instructions get more data in Stage 2, and when
   is a stage complete?
2. **Why it matters.** Stage 2 spends half the budget; it must go where a
   decision is uncertain, chosen by a fixed rule, and only once Stage 1 is
   finished.
3. **Proposal.** One round of at most 240 cells × 64 new questions. A cell
   qualifies when its Stage 1 uncertainty interval straddles a decision
   boundary. Cells are ranked:
   1. A near the edge of its headroom band;
   2. B near the edge of its informative band;
   3. eligibility at 20%;
   4. matching at ±10 points;
   5. eligibility at 10%.

   Within a class, closest to the boundary first. Stage 2 is chosen only
   from complete Stage 1 evidence and records that evidence's hash; nothing
   proceeds with missing data.
4. **Justification.** A fixed, prespecified ranking means Stage 2 cannot be
   steered. Eligibility ranks above matching because it decides library
   membership for every model.
5. **Alternatives.** Uniform extra data; several adaptive rounds; a
   partial-completion rule.
6. **Trade-offs.** Matching cells rank fourth and often miss the cap, which
   is where matching noise (D10) remains.
7. **Recommendation: approve.**
8. **Evidence.** Audit F2 (fixed; re-audit confirmed); precision review §4
   (allocation barely matters).
9. **Files.** `src/dci/batch1/calibration.py`, `src/dci/batch1/evidence.py`,
   `src/dci/batch1/pipeline.py`.

---

### D07 — Choosing the two B limits

1. **The question.** Which two word-length limits (from 8 to 13 letters)
   does the study use?
2. **Why it matters.** B is the instruction interference is measured on.
   If B is almost always or never followed, a drop cannot be seen. The two
   limits must differ clearly, so that B's strictness is a real variable.
3. **Proposal.** A pair qualifies when:
   - the limits are at least 2 letters apart;
   - median compliance rises by at least 15 points between them;
   - that holds in at least 3 of the 4 models;
   - each limit is between 15% and 85% compliance in at least 4 of 8
     model-frames.

   Among qualifying pairs, prefer the most informative. If none qualifies,
   B selection fails and the study stops for revision.
4. **Justification.** The thresholds rule out pairs that differ by noise,
   or only in one model.
5. **Alternatives.** 10 or 20 points of separation (simulated in the first
   precision review); allowing a near-ceiling limit above 85%.
6. **Trade-offs.** With a shallow B curve, no pair may qualify; that is
   reported rather than forced.
7. **Recommendation: approve,** keeping limits above 85% inadmissible (a
   near-ceiling B hides interference).
8. **Evidence.** Audit F9 (revised); re-audit: the plateau counterexample
   now fails; precision review §7.
9. **Files.** `src/dci/batch1/calibration.py`, `src/dci/batch1/config.py`.

---

### D08 — Choosing the one A count

1. **The question.** Use *however* exactly 2, 4 or 6 times, one value for
   every model and wording?
2. **Why it matters.** If A is nearly always or never followed in a
   model-frame, no reference can match it, and that configuration
   contributes nothing.
3. **Proposal.** N qualifies when its compliance is between 10% and 90% in
   at least 6 of 8 model-frames, across at least 3 models. Among qualifying
   N, prefer the most configurations with a supported G1, then headroom,
   then N = 4. Configurations where A is outside the band are reported but
   never counted. No qualifying N means A selection fails; there is never a
   per-model A.
4. **Justification.** "6 of 8 across 3 models" is what the 12-of-16,
   3-model feasibility target needs.
5. **Alternatives.** Per-model N (forbidden by the brief); a different band.
6. **Trade-offs.** The earlier v8.1 study chose N per model-frame (between 2
   and 8), so one global N may fail; failing is then the honest result.
7. **Recommendation: approve.**
8. **Evidence.** Audit F3 (revised; re-audit confirmed on the floor
   counterexample); simulation: the true A is chosen in 97–100% of pilots on
   typical surfaces, 55–61% when A is hard to pick.
9. **Files.** `src/dci/batch1/calibration.py`,
   `src/dci/batch1/references.py`.

---

### D09 — Eligibility (20%)

1. **The question.** Which references are followable enough to use?
2. **Why it matters.** A reference almost no model follows tells nothing
   about interference.
3. **Proposal (the brief's rule).** Eligible if followed at least 20% of the
   time in at least one model-frame; then eligible for all models. Those
   reaching only 10% are a separate sensitivity set, never mixed in.
4. **Justification.** One shared pool keeps the library identical across
   models; the 20% floor removes the unfollowable.
5. **Alternatives.** Requiring 20% in most model-frames; using intervals.
6. **Trade-offs (disclosed).** "In at least one of eight" admits a
   reference whose true rate is 12% everywhere with probability 0.49 at 32
   answers per cell (0.07 at 96).
7. **Recommendation: approve with the disclosure.** The coverage simulation
   found eligibility noise contributes nothing measurable to verdict errors.
8. **Evidence.** Precision review §3; coverage simulation §6.2.
9. **Files.** `src/dci/batch1/references.py`.

---

### D10 — Difficulty matching (±10 points)

1. **The question.** When is a reference "as hard as A"?
2. **Why it matters.** G1, G3 and G5 are the matched populations; P1–P3
   compare them.
3. **Proposal (the brief's rule).** Within 10 percentage points of A's
   compliance, separately in each model-frame, on raw compliance. A
   chance-corrected version is reported as a sensitivity.
4. **Justification.** Simple, prespecified, and never pooled across models
   or wordings.
5. **Alternatives.** Wider or narrower tolerance; a rule using uncertainty
   (each would need its own review).
6. **Trade-offs (disclosed, and the main known weakness).** At pilot sample
   sizes, a reference within 2 points of the ±10 edge is classified wrongly
   about 45% of the time. Matched populations overlap the true ones only
   about half the time (Jaccard ≈ 0.5). This is what drives false FEASIBLE
   verdicts (D11).
7. **Recommendation: approve with the disclosure,** and treat matching
   precision as a candidate for a separate future decision; none is
   proposed now.
8. **Evidence.** Precision review §5; coverage simulation §6.2 and §6.4.
9. **Files.** `src/dci/batch1/references.py`, `src/dci/batch1/intervals.py`.

---

### D11 — Coverage minimums and the feasibility target

1. **The question.** When is a comparison estimable in a configuration,
   and when is the study feasible?
2. **Why it matters.** It decides whether Batch 2 runs.
3. **Proposal in the code (the brief's design values).**
   - G1 needs references with at least 3 distinct target words;
   - P1 needs G2 to add at least 2 references;
   - P2 needs G3 to add at least 2 of another object type;
   - P3 needs G3 to have at least 3 references and G5 to add at least 2 of
     another operation;
   - each comparison must be supported in at least 12 of 16 configurations,
     across at least 3 models and both B limits.

   **Every qualifying reference is admitted;** a minimum never caps a
   population (verified by tests).
4. **Justification.** Minimum representation, as the brief specifies.
5. **Alternatives tested.** 15 rules: minimums of 2–5, per comparison or
   for all; diversity across operations or families; counting only
   references measured well inside the tolerance.
6. **Trade-offs.** With the design minimum, false FEASIBLE is 73% when true
   coverage is thin (up to 87%). A minimum of 3 for P3 lowers that to 18%
   at about 1 point of extra false INFEASIBLE. No rule removes wrongly
   admitted references from accepted configurations.
7. **Recommendation: revise to a P3 minimum of 3** (P1 and P2 unchanged),
   or, if P3 should mean "more than one other operation", 3 from at least 2
   operations. You have said you are not yet approving 3; the code holds 2
   until you decide.
8. **Evidence.** [`COVERAGE_SIMULATION_REVIEW.md`](COVERAGE_SIMULATION_REVIEW.md)
   (12,000 paired simulated pilots); re-audit R3.
9. **Files.** `src/dci/batch1/references.py`, `src/dci/batch1/config.py`,
   `src/dci/batch1/coverage_study.py`.

---

### D12 — Models, decoding, length cap, seeds, backend and Python

1. **The question.** Which models, run how, on which software?
2. **Why it matters.** These define the measurement conditions. A
   different model revision or software version is a different measurement.
3. **Proposal.**
   - the four historical models at pinned revisions;
   - decoding: temperature 0.7, top-p 0.9, top-k 50, thinking off;
   - a cap of 512 response tokens, about three times a 120-word answer; any
     cell where more than 2% of answers are cut off is listed for review;
   - seeds derived from what each prompt is, never from its position in a
     batch;
   - the existing vLLM backend code;
   - **Python 3.12** for the controlling program (your decision of 2026-10-25, replacing 3.11) and
     **Python 3.12** for the vLLM backend (proposed: the repository's pinned
     vLLM 0.15.1 build is for Python 3.12, and its CUDA environment requires
     3.12 or later).

   The exact software on the generation computer is recorded by an
   attestation there and checked before every run.
4. **Justification.** Carries the historical conditions forward. Pinning
   Python means what was reviewed is what runs. The code fingerprints that
   bind every approval no longer depend on the Python version.
5. **Alternatives.** Other cap values; a Python 3.11 backend (would need a
   different vLLM build from the one the repository pins).
6. **Trade-offs.** No CUDA backend environment exists yet; throughput and
   truncation on the target computer are unknown until the smoke test.
7. **Recommendation: approve after** the environment attestation and the
   smoke test on the generation computer. The smoke test now uses only
   non-focal instructions, so it reveals nothing about A or B.
8. **Evidence.** Re-audit R2 (fixed: identical code fingerprints under
   Python 3.11, 3.12 and 3.13, by test); `tests/batch1/test_pins_and_provenance.py`.
9. **Files.** `src/dci/batch1/config.py`, `src/dci/batch1/environment.py`,
   `src/dci/batch1/runner.py`, `src/dci/batch1/smoke.py`,
   `src/dci/batch1/store.py`, `.python-version`,
   `dci1/environments/backend/pyproject.toml`.

---

### D13 — Object types and reference weights

1. **The question.** How are references grouped, and how much does each
   count in a population average?
2. **Why it matters.** Without weighting, the 22 word-count variants would
   dominate every broad population.
3. **Proposal.** Commas and semicolons share the object type
   *punctuation*. Weights are equal across operations, then across object
   types within an operation, then across variants. Each count variant of a
   word is its own variant.
4. **Justification.** The brief's scheme; the taxonomy is fixed across
   models and wordings.
5. **Alternatives.** Equal weight per reference; an extra level for the
   target word.
6. **Trade-offs (disclosed).** An operation represented by one reference
   gets a whole operation's weight: in simulated G5 populations such
   references carry 22–55% of the weight, and weights shift more under noise
   than equal weights would.
7. **Recommendation: approve with the disclosure.** Batch 2 should report
   each population's effective number of references and a
   leave-one-reference-out check.
8. **Evidence.** Coverage simulation §6.5.
9. **Files.** `src/dci/batch1/references.py`, `src/dci/batch1/library.py`.

---

### D14 — Stability diagnostics

1. **The question.** How does the pilot report how much its selections
   would change with different questions?
2. **Why it matters.** Memberships are noisy (D10); the reviewer of Freeze
   2 needs to see which are fragile.
3. **Proposal.**
   - resample the pilot's questions 200 times;
   - report how often each reference is included, how often each A, B and
     verdict is chosen, the borderline matches, and feasibility on references
     included in at least half the resamples;
   - report a Stage-1-only re-analysis;
   - flag a FEASIBLE verdict whose weakest comparison is supported in at most
     14 of 16 configurations (new, re-audit R4.5).

   These are diagnostics, never gates: they change nothing automatically.
4. **Justification.** They make instability visible without inventing a
   rule after the data are seen.
5. **Alternatives.** Using them as gates. Simulation showed they cannot
   reliably separate true from false FEASIBLE verdicts.
6. **Trade-offs.** The near-threshold flag catches most false FEASIBLE
   verdicts but also fires on 30–76% of correct ones.
7. **Recommendation: approve as diagnostics,** and decide now how you will
   read their flags when Freeze 2 arrives.
8. **Evidence.** Precision review §6; coverage simulation §6.7.
9. **Files.** `src/dci/batch1/stability.py`, `src/dci/batch1/freeze.py`.

## 4. How approval works

Each decision's exact content (its *payload*: the parameter values, the
wordings, and a fingerprint of the code that implements it) has a hash.
You approve a decision by writing APPROVED, your name and the date next to
that hash in an `approvals.json` file. Changing the decision, or the code
that carries it out, changes the hash and voids the approval. The code never
writes APPROVED itself. Real generation refuses to start unless every
decision is approved, Freeze 1 validates, the generation computer's software
matches its attestation, and the Freeze 1 hash is given as an authorisation
token.

Generated register with hashes: [`decisions.md`](decisions.md); template:
[`approvals_template.json`](approvals_template.json).
