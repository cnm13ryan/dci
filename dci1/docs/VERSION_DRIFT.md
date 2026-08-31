# DCI-1 version drift: which definition belongs to which revision

Written 2026-08-29 so that no agent mixes v4, v5, v6, v7 and v8 definitions.
Every fact below was read from source or `git log`; where a docstring and the
history disagreed, the history is what is recorded here. Commit hashes are on
`feat/dci1v4-fresh-study`.

## The lines and their namespaces

| Revision | Namespace | First commit | Standing (2026-08-29) |
|---|---|---|---|
| v2, v3 | `dci1/src/dci1`, `dci1v3` | `85fe950` 2026-08-17 | closed |
| v4r1, v4r2 | `dci1/src/dci1v4` | `79e6f15`, `09c3896` 2026-08-19 | closed; supplies carried sources (`alpha_runs`, A's wordings, S1/S2) |
| v4r3 | `dci1/src/dci1v4r3` | `4233ca6` 2026-08-21 | closed at Gate 1 |
| v4r4 | `dci1/src/dci1v4r4` | `d11e41c` 2026-08-21 | frozen at Gate 5 on two replications; confirmatory data in hand |
| v5 | `dci1/src/dci1v5` | `cf5cc08` 2026-08-22 | ran and closed 2026-08-24 |
| v6 | `dci1/src/dci1v6` | `655e2be` 2026-08-25 | ran and closed 2026-08-27 |
| **v7** | `dci1/src/dci1v7` | `ed0446f` 2026-08-28 | **live line**: adopted, registered, run and closed 2026-08-28; amended in place A6–A8; development rehearsals continuing under `evidence/dci1v7-development*` |
| v8 | none yet | — | prospective; candidate work on `dev/v8-prescreen-redesign` and `maint/v7-docs-marker-unification` |

`dci1/README.md`'s banner said v4r3 was live until 2026-08-29; the
authoritative orientation is the repository's `RESEARCH_STATE.md` §4b.

## A's wording

Four templates, `Use the word however exactly {n} time(s).` and three
alternates, authored for v3 (`85fe950`) and restated in
`dci1v4/protocol/wordings.py` (`09c3896`).

**The restatement was not byte-identical, and this is a model-facing
difference.** Only the canonical template carried unchanged. v4 drops the
noun phrase *the word* from alternates 1 and 2, and the locative *in your
answer* from alternate 3:

| | v3 (`dci1v3.protocol.wordings`) | v4 (`dci1v4.protocol.wordings`) |
|---|---|---|
| canonical | `Use the word however exactly 1 time.` | *identical* |
| alt 1 | `Your answer must contain **the word** however exactly 1 time.` | `Your answer must contain however exactly 1 time.` |
| alt 2 | `Include **the word** however exactly 1 time in your answer.` | `Include however exactly 1 time in your answer.` |
| alt 3 | `The word however must appear exactly 1 time **in your answer**.` | `The word however must appear exactly 1 time.` |

From v4 onward the four are carried byte-identically by every later
revision through `target_wordings`. Singular at n = 1 from the start.

A v3 A-rate is therefore **not** prompt-identical to a v4-or-later one on
three of the four alternates, and must not be pooled across that boundary
--- which is exactly the mixing this document exists to prevent.

## The marker families

| What | Introduced | Carried to |
|---|---|---|
| `CX1`, exact count of `thus` (the first marker family) and `CX2`, exact count of semicolons | v4r3 amendment R3, `0901526` 2026-08-21 | v4r4 (`d11e41c`) |
| `MK1`–`MK8`, eight markers (`thus`, `hence`, `though`, `whereas`, `indeed`, `namely`, `instead`, `overall`), templates **derived from A's** with the word substituted (`_marker_templates`), one counting function `marker_count` | v5, `cf5cc08` 2026-08-22 | v6, v7 unchanged; `MK1` is `CX1` carried (`CARRIED_FROM_V4R4`) |
| `XC1` (= `CX2` carried), `XC2`, `XC3` | v5 | v6, v7 |
| `PS1`–`PS3`, probe-only stand-ins, never selectable | v6, `ad4eec7` 2026-08-26 | v7 |

Family counts, computed from each namespace's `FAMILIES`: v4r2 **8**, v4r3
**30**, v4r4 **28** (CP4 and CP7 removed), v5 **37**, v6 and v7 **40** (37
selectable + 3 probe-only). A docstring that says "37 families" is describing
v5; v7's asserted sizes are in `constraints.assert_library_sizes`.

## The marker counter and the word-list order

| Rule | Order | Revisions |
|---|---|---|
| `alpha_runs` (a word is a maximal run of Unicode letters) | — | v3 → v7, byte-identical |
| `words_lower`, the word list every letter/suffix/marker test reads | v4r2: fold the whole response, then segment; **v4r3 (`4233ca6`) corrected it** to segment, then fold each word, after §10.2's reimplementation disagreed on `one_letter` | corrected order carried v4r4 → v7 |
| `marker_count` (MK1–MK8) | segment, then fold | v5 → v7 |
| A's counter `s0_count` | **fold the whole response, then segment** (`dci1v4.verifiers.target`, from v3) | v3 → v7 **until 2026-08-29**; scored every stored row of every revision |
| A's counter `s0_count` | **segment, then fold** = `marker_count(text, "however")` (`dci1v7.verifiers.statistics`) | v7 branch `maint/v7-docs-marker-unification`, prospective (v8 / any v7 re-run) |

The two orders differ on U+0130 alone. An audit over every stored scored
row of every root (3,507,000 rows, 165,062,472 A/MK verdict entries) found
no row containing it and no verdict that moves:
`reports/dci1v7/development/marker_counter_unification_audit.json`.
`dci1v4.verifiers.target.s0_count` is unchanged and still scores v3–v6
evidence; do not "fix" it.

## Singular and plural in the wordings

| Templates | Number handling | Since |
|---|---|---|
| A (`time`/`times`) | correct from the start | v3 |
| MK1–MK8 (`time{s}`, derived from A) | correct from the start | v5 |
| B (`{m} letters`, m ≥ 7) | never singular | v4r2 |
| RF1–RF8 (carried from v4r2), RF9–RF12, CR5, CR12, CL7, CL8, XC1–XC3, PS1, PS2 | plural hard-coded: *at most 1 words*, *exactly 1 semicolons* | v4r2 / v4r3 / v5 / v6 → v7 **until 2026-08-29** |
| the same templates with `{s}`/`{v}` (`number_fields`) | *1 word*, *1 semicolon*, *1 word contains*; identical at every q ≠ 1 | branch `maint/v7-docs-marker-unification`, prospective |

Rows generated under the plural rendering at q = 1 carry that text in their
`constraint_sentence`; they are not prompt-identical with rows generated
under the corrected rendering and `carryover.assert_wordings_match_stored`
refuses to treat them as such.

## Report trees, and where v5's design evidence lives

v5's decision packets and development measurements were written under
`dci1/reports/dci1v5/` (`6760c2b`, `e52924a`, 2026-08-22/23) and **never
moved**; v6 and v7 re-took the decisions on their own records
(`reports/dci1v6/researcher_decisions.json`,
`reports/dci1v7/researcher_decisions.json`) and cite the packets at v5's
path. v7's own artifacts are under `dci1/reports/dci1v7/` (`READINESS.md`,
`CLOSURE.md`, `closure.json`, `researcher_decisions.json`, `development/`,
`development_rehearsal/`, `boundary_audit/`, `execution_path_audit.*`,
`v7_producer_consumer.md`, `reference_design_spec.json`,
`replication_summary.json`, `execution_logs/`).

Stale references found and corrected on 2026-08-29:

| stale reference | current meaning | correct target | action |
|---|---|---|---|
| `dci1/reports/dci1v7/development/d6_marker_frequency.json` (`verifiers/constraints.py`, `_TIER1` comment) | v5's marker-frequency measurement on v4r4's unconstrained responses, design evidence for §7.10 | `dci1/reports/dci1v5/development/d6_marker_frequency.json` | pointer corrected; labelled v5 design evidence, not a v7 measurement |
| `dci1/reports/dci1v7/d4_marker_audit.md` (`verifiers/constraints.py`, `marker_population()["audit"]`) | v5's §34 D4 marker-audit packet, re-taken by v6 and v7 at the same value | `dci1/reports/dci1v5/d4_marker_audit.md` | pointer corrected; historical, not regenerated |
| `dci1/reports/dci1v7/u2_tier_model_decision.md` (`protocol/manifest.py`) | v5's U2 tier-model decision packet | `dci1/reports/dci1v5/u2_tier_model_decision.md` | pointer corrected |
| `reports/dci1v7/d1_arm_compute_decision.md` (`design/cells.py`) | v5's §34 D1 arm/compute decision packet | `dci1/reports/dci1v5/d1_arm_compute_decision.md` | pointer corrected |
| "live protocol line is v4 revision 3" (`dci1/README.md`) | the live line is v7 | `RESEARCH_STATE.md` §4b | banner rewritten; the earlier description kept as history |
| `tools/…`, `docs/…` tokens flagged by a repo-root scan | paths written relative to `dci1/` | `dci1/tools/…`, `dci1/docs/…` (exist) | no change; `tests_v7/test_documentation_paths.py` resolves both roots |

Historical citations that are **correct as written** and were left alone:
`dci1/reports/dci1v5/v5_prereg_redteam.md` (`protocol/manifest.py`,
`stages/audit_prefreeze.py`), `dci1/reports/dci1v5/researcher_decisions.json`
(`protocol/decisions.py`), `dci1/reports/dci1v5/v5_reconciliation.md` and
`d17_b_strength_decision.md` (`tests_v7`), and every `dci1/reports/dci1v6/…`
path in `protocol/reuse_ledger.py`.

## Docstrings that described an earlier state (corrected 2026-08-29)

| Where | Said | Is |
|---|---|---|
| `verifiers/constraints.py` | "The v5 candidate library"; "37 families; 326 …; 650 instances in 39 verifiers"; "no v5 family instantiates `rate_lower_bound`"; "No probe-only family is registered yet" | v7's library, v5's carried through v6; 40/350/656/674/42 with the selectable 37/326/632; PS3 exercises the form; PS1–PS3 are registered |
| `verifiers/statistics.py`, `verifiers/words.py` | "for every v5 family", "for v5"; "A's own counter … folds first" | v7; A and the markers are one function |
| `verifiers/__init__.py` | "The v4r3 instrument layer" | v7's, v4r3's in shape |
| `verifiers/boundary.py` | "for every v4r3 instrument" | v7's, the corpus v4r3 froze and later revisions extended |
| `verifiers/carryover.py` | "what v5 inherits"; "`s0_count` carried byte-identical" | v7, through v5 and v6; S0 no longer carried, S1/S2 are |
| `verifiers/compliance.py` | rate lower bounds "unused in v5" | exercised by PS3 only |
| `protocol/reuse_ledger.py` | "The entries v6 registers"; "what enters v6 directly" | v7 |

Kept deliberately, because they are provenance and are true as history:
"new in v5", "carried from v4r4", "v4r4 registered …", "v4r3 §13.1 says …",
"v4r3 inserts the answer-length sentence", the "v5's 37 families" comment in
`tests_v7/test_library_and_regime.py`, and every `Change` in
`protocol/revision.py`.
