# v8 verifier unification — offline rescore of every stored response

**Change under test.** `dci1v8.verifiers.words.count_marker(text, marker)`
counts A (`however`) and MK1–MK8 with one function under §9.2's lexical rule
(segment the response as written, fold each run, compare). v7 counted A with
`s0_count` (fold the whole response, then segment). The two disagree only
when U+0130 `İ` immediately precedes the marker inside one alphabetic run.

**Method.** `dci1/tools/v8_rescore_marker_unification.py`, read-only over
`/home/cnm13ryan/git/dci/dci1/evidence` (gitignored; not part of this
branch), scoring each row's `final_answer` under v7's A rule, v7's MK rule
and v8's unified rule, and comparing verdicts at every registered severity
(A: n ∈ 1..8; each MK: q ∈ 1..12). Six workers at nice 19, 247 s, beside a
live v7 GPU run that was not paused.

**Result** (`verifier_unification_rescore.json`, same directory):

| | |
|---|---|
| evidence trees | 19 (dci1-v2, dci1-v3, dci1-v4, dci1v4r3, dci1v4r4, dci1v5, dci1v6, dci1v7, five dci1v7-development rehearsals, five v4 screens/pilots, one superseded v4 apparatus tree) |
| `rows.jsonl` files | 593 |
| rows scored | 4,311,315 |
| undecodable lines | 0 |
| rows containing U+0130 | **0** |
| rows with any differing count (A or any marker) | **0** |
| verdict flips, any instrument, any severity | **0** |

**Reading.** No existing verdict changes. The unification is a change of
rule with no realised consequence on any DCI-1 response ever generated; it
matters for what a v8 row *means* (one rule for A and its same-form
controls, literally), not for any number already recorded. v7's records
stand under v7's verifier hash and are not re-labelled.

**Identity.** `dci1v8.verifiers.verifier_source_hash()` = `9884aa78468aec71a182981bbb40eda633081310a1c64feae2462f242122654a` (covers dci1v8/{words,statistics,compliance}.py, dci1v4/words.py, dci1v7/{constraints,statistics,compliance,words}.py by path).
