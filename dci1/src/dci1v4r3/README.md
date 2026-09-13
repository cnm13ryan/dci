# `dci1v4r3` — the executable form of DCI-1 v4 revision 3

**Status: ADOPTED and REGISTERED (2026-08-21). Not frozen. No confirmatory
data.** The adoption record is `dci1/DECISIONS_V4R3.md` A0; the signed
study-wide manifest is `dci1/evidence/dci1v4r3/registration/`.

The protocol is `user-notes/DCI1_preregistration_v4r3.md`, which is complete
and self-contained: everything here is implementation, and where the two ever
disagree the preregistration is the protocol and the disagreement is a defect.
`tests_v4r3/` checks the numbers both state.

## What it is

A sibling of `dci1v4`, following the same pattern the four v4r2 design screens
use: it imports that package's protocol-neutral machinery — hashing, signing,
the durable store, the generation seam, the raw word segmenter, the exact-count
rule, the topic bank and split — and defines its own protocol on top.

It never writes into another study's evidence tree, and `dci1v4` neither
imports it nor can read its artifacts. `STUDY_ID` is `dci1v4r3` with **no
hyphen**, because `dci1v4.engine.guards.assert_admissible_manifest` admits on
`startswith("dci1-v4")` and a hyphenated identifier would have passed it.

## The candidate library

A grammar, not a list: nine counted statistics × four predicate forms, grouped
into **eight feature groups**.

| | count |
|---|---:|
| feature groups | 8 |
| families | 20 (16 reference, 4 class-control) |
| severities measured at round 0 | 190 |
| severities in the declared library | 334 |
| Gate 1 instrument instances | 348 |
| realisable pairs discharged by §7.5 | 25,337 |

Two families of one feature group never share a cell and never both enter the
core reference set. That rule was **forced by the witness suite**, which found
1,748 unsatisfiable non-entailment obligations: a count budget at *q* = 0
entails the rate budget of the same numerator, and RF6 at *q* = 0 entails every
CR6 severity.

## The design in one table

| arm | cells/block | pairs with |
|---|---:|---|
| unconstrained (load 0) | 1 | — |
| core solo | 5 | — |
| core composed | 20 | every unordered pair, both orders |
| spectrum solo | 6 | — |
| spectrum composed | 12 | B only, both orders |
| class solo | 1 | — |
| class composed | 2 | B only, both orders |
| **total** | **47** | 384 blocks × M=8 → 144,384 per model |

## Module map

| Module | Registers |
|---|---|
| `verifiers/words.py` | §7.0's corrected composition order, and the one-character enumeration that scopes it |
| `verifiers/constraints.py` | §7.0, §7.2, §7.3, §7.4: the grammar, feature groups, ladders and reserves, the conditional focal extension, and the refusal that keeps a production family out of a reference slot |
| `verifiers/statistics.py` | the nine numerators, and the executable equivalence with v4r2 on U+0130-free text |
| `verifiers/compliance.py` | §7.6, §9.1, §9.3: four predicate forms, graded scores, non-vacuity, and the `present` flag separating treated verdicts from chance verdicts |
| `verifiers/independent.py` | §10.2's prose-only reimplementation. Imports nothing from any DCI package |
| `verifiers/boundary.py` | §10.2, §24: 136 frozen cases over 348 instruments |
| `verifiers/witnesses.py` | §7.5: joint satisfiability and non-entailment over every realisable pair |
| `verifiers/wording_suite.py` | §7.5: four wordings, one rule, one caliper |
| `verifiers/adversarial.py` | §24: the corpus, and the realised frequency of each phenomenon in genuine generations |
| `verifiers/carryover.py` | §10.2: what v4r3 inherits, what it does not, and why A's carry-over survives |
| `verifiers/__init__.py` | §10.6: the canonical hash, covering the carried `dci1v4` sources **by path** |
| `protocol/constants.py` | every registered v4r3 value, with its section |
| `protocol/wordings.py` | §7.5: four wordings per family over the whole declared range |
| `protocol/seeds.py` | §14.2: fresh roots and domains; v4r2's topic-split seed carried |
| `design/prompts.py` | §8.5: the four-part template, and the assertion that the stem is in every prompt |
| `design/cells.py` | §8.1, §8.4: the 47-cell block derived from its arms, and the allocation assertions |
| `engine/context.py` | §26: the study root, and isolation checked in both directions |
| `stages/registration.py` | §6.1: the signed study-wide manifest, and the model-adaptive guard |
| `stages/library.py` | §7.0, §12.6: the candidate library, the coverage criterion, the expansion, the vocabulary freeze |
| `stages/regime.py` | §12.2, §12.3: the difficulty table, the ranking, the shortlist |
| `stages/selection.py` | §13.3–§13.7, §13.9: the coordinate, core admission, strict straddling, the class arm, the closed input schema |
| `stages/gate1.py` | §10.2–§10.4: determinism, suites, reimplementation, witnesses, wordings, adversarial, carry-over, and the measurement basis Gate 1 cannot pass without |
| `stages/gates.py` | §12.3, §12.4, §13.10: Gate 2 with the share reading and the focal escalation, Gate 3, Gate 4 |
| `stages/freeze.py` | §18.1: 61 bound fields, 28 of them new in v4r3 |
| `analysis/spectrum.py` | §11.7, §13.8, §17.2: the fit, `delta_difficulty` in both algebraic forms, the support rule, the refitting bootstrap |
| `analysis/claims.py` | §3.2, §17.6: the ladder, the joint reading, the guarded L3 emitter |
| `run/execute.py` | plan → generate → score → record, with the §10.6 binding re-verified and a resume path that reuses generations only on an exact design identity |
| `run/regime_screen.py` | stage 3 end to end: §12.1's cap, §12.2's ladder, §12.6's loop |

## Running it

```
cd dci1
./.venv/bin/python -m pytest tests_v4r3 -q
./.venv/bin/python tools/run_v4r3.py register
./.venv/bin/python tools/run_v4r3.py regime --model qwen3-4b --device 0
./.venv/bin/python tools/v4r3_regime_report.py
./.venv/bin/python tools/allocation_v4r3.py
```

## What is not implemented yet

Gate 2 through Gate 5, confirmatory generation, masking and the unmasked
analysis pipeline. Gate 1 cannot pass without §10.4's researcher approval, and
nothing after Gate 1 may run until it does, so building the stages beyond it
would be building execution machinery for a gate that has not opened.
