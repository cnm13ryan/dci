# Tier-1 reliability audit — investigator handoff

Stage 2 has exactly one outstanding requirement: `verifiers.tier1_reliability`.
This document states what is built, what is missing, and what must be decided
before a single reviewer can be asked anything.

## The requirement

§10.4, as amended by A3:

| | |
|---|---|
| verifier units | 6 (each pair's target and focal) |
| adjudicated **true failures** per unit | 72 |
| adjudicated **true passes** per unit | 72 |
| total labels | **864** |
| interval | exact two-sided 95% Clopper–Pearson |
| errors permitted | **0** |
| conditional extension | **forbidden** |
| remedy on failure | repair, then a *fresh prospectively specified* audit |

§10.4 also fixes what each denominator is for: *"A false-pass bound requires
adjudicated examples that truly fail the constraint. A false-fail bound requires
adjudicated examples that truly pass."*

## What is built

`dci.v19.tier1_audit`, with regression tests in
`tests/unit/test_v19_tier1_audit.py` (69 tests):

- **`AuditCase`** — one authored example, carrying its source pool, author,
  provenance, intended truth class, and which of §10.6's 14 material categories it
  exercises. Refuses an untraceable case, an unknown unit, or an unlisted category.
- **`AuditManifest`** — deterministic ordering by (unit, class, case hash, id), a
  reproducible `manifest_hash`, per-unit/class counts, and a §10.6 coverage report.
  `assert_manifest_is_complete` refuses a short stratum *before* anything is sent
  out, because discovering it afterwards wastes every judgement already made.
- **Blinded packets** — `assert_blinded` refuses any packet carrying the arm, the
  automatic verdict, the constraint role, the constraint id, or the intended truth
  class. Packet ids are `sha(manifest_id, case_hash)`, so any packet is reproducible
  from its case.
- **`ingest`** — fail-closed. Refuses missing, duplicate, unknown, malformed, extra
  or mismatched records; refuses one reviewer answering twice; refuses a
  non-boolean judgement; refuses an unresolved disagreement. **A missing judgement
  is never read as the class the author intended.**
- **`certify_unit` / `certify_all`** — scores through the frozen A3 design
  unmodified, so an over- or under-running stratum fails on the design rather than
  being trimmed. Trimming would be the conditional selection A3 forbids.

Two design points worth reading in the source:

- `case_hash` deliberately **excludes** `case_id`. Two cases with the same text at
  the same parameters in the same class are the same judgement however they are
  named. Including the id would let a stratum be padded to 72 by copying one case
  under 72 ids — a denominator with no evidence behind it. A test asserts that.
- The reviewer is **not** asked "did the verifier get this right?". They establish
  ground truth and are never shown a machine verdict.

## What is missing — and it is not code

### 1. The 864 cases do not exist (blocking)

`pool.p1.audit`, `pool.p2.audit`, `pool.p3.audit` are `PENDING_CONTENT`,
`BLOCKED_BY_CONTENT`. Their declared rule is *"human-adjudicated examples with both
true-pass and true-fail support per Tier-1 verifier unit (section 10.4)"*.

§11.1 makes the audit pool one of the six disjoint scientific splits, and content
"may be authored before freeze under a versioned content procedure". §11.2's
content-sufficiency gate requires counting "human-audit examples with both true
pass and true fail support" separately by pair and scope — the slots
`sufficiency.{pair}.audit_true_pass_examples` and `…_true_fail_examples`, also
unauthored.

**No code can supply these.** Generating 864 plausible cases would put unauthored
scientific material into the artifact trail where nothing downstream could tell it
from material a person wrote. The module refuses to do it and a test asserts the
module ships no cases of its own.

A gate defect was fixed alongside this: `verifiers.tier1_reliability` did **not**
depend on the audit pools, so the certificate could in principle have been frozen
with the pools still empty. It now depends on all three.

### 2. The human procedure is undecided (blocking)

`verifiers.tier1_audit_protocol` is new, `PENDING_DECISION`. Three questions §10.4
does not answer:

**A. How many reviewers judge each case, and who adjudicates disagreement?**
§10.4 says "human-adjudicated" and stops there. §8.6's two-independent-reviewers-
plus-third-adjudicator rule is scoped to *semantic review of compositions* — it
governs clauses "whose intended semantics are not exhaustively covered by the
frozen machine encoding and deterministic verifier". Applying it here would be an
implementer deciding a protocol question. It is the obvious candidate; it is still
your call.

**B. How exactly 72 per class is reached, given the class is known only afterwards.**
A case's truth class is established *by* the reviewers. So a manifest of exactly 72
per *intended* class yields exactly 72 per *adjudicated* class only if every case
lands where its author intended. Two prospective answers, both admissible under A3
because both are fixed before any judgement is seen:

- `exact_authoring` — author exactly 72 per class and treat any case that lands in
  the other class as an audit failure requiring re-authoring;
- `prospective_oversample` — author more than 72, and fix *now* the rule selecting
  which adjudicated cases count (the manifest order is already deterministic, so
  "the first 72 by manifest order in each adjudicated class" is available).

Choosing after seeing the labels would be exactly the conditional selection A3
forbids.

**C. Whether a case adjudicated against its intended class counts.** The apparatus
records `matched_intent` per case and counts it toward the class the humans put it
in; whether such a case is admissible evidence or a case-authoring defect to be
replaced is part of decision B.

The typed domain `tier1_audit_protocol` refuses an incomplete answer: fewer than
two independent reviewers, no named adjudicator, an `unresolved_disagreement` other
than `"fails"`, or a `prospective_oversample` with no selection rule.

## Reviewer workflow

**Reviewers receive** the `packets` array of `reviewer_bundle(manifest)` — nothing
else. Each packet contains only: an opaque packet id, the requirement in the
protocol's own words, the parameter realisation, the response to judge, and the
answer schema.

**Reviewers do not receive** the unblinding index, the arm, the verifier's verdict,
the constraint role or id, or the class the author intended. `assert_blinded`
enforces this structurally, and it caught a real leak during development — a test
fixture that named the truth class inside the response text.

**Reviewers return**, per packet: `packet_id` (copied back unchanged),
`reviewer_id`, `satisfied` (a real boolean), and a `rationale` (required — an
unexplained judgement cannot be adjudicated against a disagreeing one).

**Disagreement** goes to the adjudicator named in the frozen protocol, whose
judgement resolves the case. An unresolved disagreement is not evidence and does
not certify.

## How the evidence enters `stage2_frozen.json`

1. Author the audit pools; freeze `pool.{pair}.audit` and the sufficiency counts.
2. Decide and freeze `verifiers.tier1_audit_protocol`.
3. Build the manifest; `assert_manifest_is_complete` must pass.
4. Generate and archive `reviewer_bundle(manifest)`; record the `manifest_hash`.
5. Collect judgements. `ingest(manifest, returned, slots)` — fail-closed.
6. `certify_all(adjudicated, verifier_verdicts)` → the `tier1_certificates` record.
7. Append it to `stage2_frozen.json` with `frozen_by`, `recorded_at` and evidence
   naming the manifest hash and the reviewers. The typed domain re-checks that every
   unit passed and no truth class is unavailable.
8. Re-run the clean-snapshot suite and `certify_stage2`.

§10.6: *"A signed audit cannot be overwritten by a later run."* `frozen.apply`
already refuses to re-freeze a resolved slot.

## Status

**`NOT READY_FOR_HUMAN_TIER1_AUDIT`.** The apparatus is complete and tested; the
audit material does not exist and the human procedure is undecided. Both are yours,
and neither is a coding task.
