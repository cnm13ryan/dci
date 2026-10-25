# Researcher decisions on the revision proposal (2026-10-26)

The researcher approved all thirteen decisions R1–R13 of
[`REVISION_PROPOSAL.md`](REVISION_PROPOSAL.md) §6 ("approve R1-R13"), with
each recommended option. Recorded by the implementing agent; these are
design decisions for library v2 and the next pilot. They are not yet
`approvals.json` entries: those are written against the payload hashes of the
implemented v2 code, before the next Freeze 1.

| # | decision | option approved |
|---|---|---|
| R1 | D01: library v2 | (a) the full v2 candidate pool (161 references; `candidate_library_v2.json`) |
| R2 | D02: wording | (a) quote target words in every frame, for A and all word targets |
| R3 | D08: A | (a) fix A = however × 6; A × 4 and × 5 as Stage A diagnostics only |
| R4 | D07: B | (a) fix B 8 and 10; check informativeness on T2 |
| R5 | D10: matching | (a) ±0.10 on raw compliance primary; posterior P(match) and labelled ±0.15 / ±0.20 / confident / iota sensitivities |
| R6 | D05: topics | (a) a fresh bank v2: T1 = 48 (screening), T2 = 96 (membership) |
| R7 | D05/D06: stages | (a) Stages A–D with carry rule, prespecified C′ top-up; cap 185,000 responses |
| R8 | D11 | (a) unchanged; early stop if the T1 forecast gives P(feasible) < 0.2 for any contrast |
| R9 | P2 contingency | (a) then (b): one P2-only library iteration on new screening topics; if P2 is still infeasible, report it not estimable and continue with P1 and P3 under an explicit scope amendment |
| R10 | D13: weights | (b) words equally, then counts within a word |
| R11 | D14: truncation | pilot cells signed off as reviewed; flag requires at least 2 truncated rows |
| R12 | technical | (a) interval fix; (b) versioned library; (c) promote pilot-1 evidence (location: compact files in git, raw rows by hash; your call on LFS); (d) independent audit before the next Freeze 1; (e) approvals written by the researcher |
| R13 | D12 | re-approve for the new code hashes after the v2 smoke test |

**Payload hashes moved by the interval fix** (`intervals.py` implements D06,
D09 and D10): D06, D09 and D10 change. Nothing approved earlier carries over
to the next Freeze 1 in any case.
