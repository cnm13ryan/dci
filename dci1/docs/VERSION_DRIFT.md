# DCI-1 version drift: which definition belongs to which revision

Written 2026-08-29 (branch `maint/v7-docs-marker-unification`, uncommitted)
and carried onto the canonical v8 development branch `dev/v8-canonical` the
same day, so that no agent mixes v4, v5, v6, v7 and v8 definitions. Every
fact below was read from source or `git log`; where a docstring and the
history disagreed, the history is what is recorded here. Commit hashes are
on `feat/dci1v4-fresh-study` unless stated.

## The lines and their namespaces

| Revision | Namespace | First commit | Standing (2026-08-29) |
|---|---|---|---|
| v2, v3 | `dci1/src/dci1`, `dci1v3` | `85fe950` 2026-08-17 | closed |
| v4r1, v4r2 | `dci1/src/dci1v4` | `79e6f15`, `09c3896` 2026-08-19 | closed; supplies carried sources (`alpha_runs`, A's wordings, S1/S2) |
| v4r3 | `dci1/src/dci1v4r3` | `4233ca6` 2026-08-21 | closed at Gate 1 |
| v4r4 | `dci1/src/dci1v4r4` | `d11e41c` 2026-08-21 | frozen at Gate 5 on two replications; confirmatory data in hand |
| v5 | `dci1/src/dci1v5` | `cf5cc08` 2026-08-22 | ran and closed 2026-08-24 |
| v6 | `dci1/src/dci1v6` | `655e2be` 2026-08-25 | ran and closed 2026-08-27 |
| **v7** | `dci1/src/dci1v7` | `ed0446f` 2026-08-28 | **live line**: adopted, registered, run and closed 2026-08-28; amended in place A6–A8; development rehearsals continuing under `evidence/dci1v7-development*`; the §13.11 chance-column fix (`fix/v7-chance-basis`, 7f89dae) is merged on `dev/v8-canonical` and not on the study branch |
| **v8 (candidate)** | `dci1/src/dci1v8dev` | branch `dev/v8-canonical` 2026-08-29 | prospective; not registered; no v8 evidence; `dci1v8` is the name reserved for the registered package at freeze |

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

**v8 candidate:** two of the four frames gain the two tokens
"the word" (`dci1v8dev.wording_v8.V8_FRAMES`): *Your answer must contain
the word however exactly q times.* and *Include the word however exactly q
times in your answer.*; the other two are unchanged. A and MK1–MK8 differ
only in the marker. No stored row was generated under the repaired frames.

## The marker families

| What | Introduced | Carried to |
|---|---|---|
| `CX1`, exact count of `thus` (the first marker family) and `CX2`, exact count of semicolons | v4r3 amendment R3, `0901526` 2026-08-21 | v4r4 (`d11e41c`) |
| `MK1`–`MK8`, eight markers (`thus`, `hence`, `though`, `whereas`, `indeed`, `namely`, `instead`, `overall`), templates **derived from A's** with the word substituted, one counting function `marker_count` | v5, `cf5cc08` 2026-08-22 | v6, v7 unchanged; `MK1` is `CX1` carried |
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
| `words_lower`, the word list every letter/suffix/marker test reads | v4r2: fold the whole response, then segment; **v4r3 (`4233ca6`) corrected it** to segment, then fold each word | corrected order carried v4r4 → v7 |
| `marker_count` (MK1–MK8) | segment, then fold | v5 → v7 |
| A's counter `s0_count` | **fold the whole response, then segment** (`dci1v4.verifiers.target`, from v3) | v3 → v7: scores every stored row of every revision; **unchanged in `dci1v7`** |
| A's counter | **segment, then fold** = `count_marker(text, "however")`, the same function object as every MK family's (`dci1v8dev.verifiers.words`) | v8 candidate (prospective); `fix/v8-verifier-unification` 5197c82, consolidated into `dci1v8dev.verifiers` on `dev/v8-canonical` |

The two orders differ on U+0130 alone. Two independent read-only rescores
found no stored row containing it and no verdict that moves:
`reports/dci1v8dev/verifier_unification/verifier_unification_rescore.json`
(4,311,315 rows, 19 trees) and the maintenance branch's audit (3,507,000
rows, 165,062,472 A/MK entries). `dci1v4.verifiers.target.s0_count` and
`dci1v7.verifiers.statistics` are unchanged and still score v3–v7 evidence;
do not "fix" them in place — `dci1v7/verifiers/*.py` are bound by the v7
verifier hash and `design/cells.py` and eleven other modules are pinned
byte-for-byte by `revision.V9`.

## Singular and plural in the wordings

| Templates | Number handling | Since |
|---|---|---|
| A (`time`/`times`) | correct from the start | v3 |
| MK1–MK8 (`time{s}`, derived from A) | correct from the start | v5 |
| B (`{m} letters`, m ≥ 7) | never singular | v4r2 |
| RF1–RF8 (carried from v4r2), RF9–RF12, CR5, CR12, CL7, CL8, XC1–XC3, PS1, PS2 | plural hard-coded: *at most 1 words*, *exactly 1 semicolons* | v4r2 / v4r3 / v5 / v6 → **v7, still** |
| the same templates with `{s}`/`{v}` (`number_fields`) | *1 word*, *1 semicolon*, *1 word contains*; byte-identical at every q ≠ 1 | v8 candidate: `dci1v8dev.wordings` applies the checked rewrite to v7's templates at import; `dci1v7/protocol/wordings.py` (wording-hash bound) is untouched |

Rows generated under the plural rendering at q = 1 carry that text in their
`constraint_sentence`; they are not prompt-identical with rows generated
under the corrected rendering.

## The chance column

| Quantity | Basis | Revisions |
|---|---|---|
| Gate-2 `chance_compliance` (§13.11) | recorded **0.0** for every candidate — the absent-instance scan found no grid row and fell back | v5, v6, v7 as run and signed |
| the same | §13.2's unconstrained cell of the grid runs (`cell_rates(..., present=False, arm="unconstrained")`) | v7 fix 7f89dae (V14), on `fix/v7-chance-basis` and `dev/v8-canonical`; every v8 backtest reads this basis through `dci1v8dev.chance_basis` (cache under `reports/dci1v8dev/chance_basis/`) |
| pre-screen `chance` (§12.2 difficulty table) | `instance_rates` over **every** row in which the instance is absent (other candidates' solo answers included); differs from the unconstrained cell with SD 0.21 on Tier-3 budget families, 0.005 on Tier 1 | v5, v6, v7 as run; the v8 candidate reads the regime screen's unconstrained cell instead (`chance_basis.build_prescreen_cache`) |
| ι_A on the Gate-2 record | `chance_curves["A"]` (load-zero rows of grid-A and the other target severities' solo cells) | v5–v7; the v8 backtests restate ι_A on the unconstrained cell (the difference is ≤ 0.026 on the twelve stored replications) |

## Report trees, and where v5's design evidence lives

v5's decision packets and development measurements were written under
`dci1/reports/dci1v5/` (`6760c2b`, `e52924a`, 2026-08-22/23) and **never
moved**; v6 and v7 re-took the decisions on their own records and cite the
packets at v5's path. v7's own artifacts are under `dci1/reports/dci1v7/`.
The v8 candidate's reports are under `dci1/reports/dci1v8dev/`
(`prescreen/`, `verifier_unification/`, `chance_basis/`,
`coverage_simulation.*`, `pipeline_validation.*`).

Stale references **known and left in place** on the v8 branch (the modules
are hash- or pin-bound; a v8 registration fixes them in its own namespace):

| stale reference | correct target |
|---|---|
| `dci1/reports/dci1v7/development/d6_marker_frequency.json` (`dci1v7/verifiers/constraints.py`) | `dci1/reports/dci1v5/development/d6_marker_frequency.json` (v5 design evidence) |
| `dci1/reports/dci1v7/d4_marker_audit.md` (`dci1v7/verifiers/constraints.py`) | `dci1/reports/dci1v5/d4_marker_audit.md` |
| `dci1/reports/dci1v7/u2_tier_model_decision.md` (`dci1v7/protocol/manifest.py`) | `dci1/reports/dci1v5/u2_tier_model_decision.md` |
| `reports/dci1v7/d1_arm_compute_decision.md` (`dci1v7/design/cells.py`, V9-pinned) | `dci1/reports/dci1v5/d1_arm_compute_decision.md` |
| "The v5 candidate library", "37 families", "for every v5 family", "The v4r3 instrument layer", "what v6 registers" (docstrings in `dci1v7/verifiers/*.py`, `protocol/reuse_ledger.py`) | v7's library, v5's carried through v6; 40 families (37 selectable) |

The v7 registration's `tests_v7/test_documentation_paths.py` (maintenance
branch) is not carried; `tests_v8dev/test_documentation_paths.py` checks the
v8 candidate's own citations.
