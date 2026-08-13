# Tier-1 reliability audit — investigator handoff

Stage 2 has exactly one outstanding requirement: `verifiers.tier1_reliability`.
The audit protocol is **frozen**. This document states what is built, what the
protocol requires, and what human work remains.

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
`tests/unit/test_v19_tier1_audit.py` (98 tests):

- **`AuditCase`** — one authored example, carrying its source pool, author,
  provenance, intended truth class, and which of §10.6's 14 material categories it
  exercises. Refuses an untraceable case, an unknown unit, or an unlisted category.
- **`AuditManifest`** — deterministic ordering by (unit, class, case hash, id), a
  reproducible `manifest_hash`, per-unit/class counts, and a §10.6 coverage report.
  `assert_manifest_is_complete` refuses anything but *exactly* 100 per stratum, a
  missing §10.6 category, or a case serving two units - *before* anything is sent
  out, because discovering it afterwards wastes every judgement already made and
  the protocol permits no top-up.
- **Blinded packets** — `assert_blinded` refuses any packet carrying the arm, the
  automatic verdict, the constraint role, the constraint id, or the intended truth
  class. Packet ids are `sha(manifest_id, case_hash)`, so any packet is reproducible
  from its case.
- **`ingest`** — fail-closed. Refuses missing, duplicate, unknown, malformed, extra
  or mismatched records; refuses one reviewer answering twice; refuses a judgement
  from outside the frozen panel; refuses a non-boolean judgement. An unresolved
  disagreement is marked unusable and excluded. **A missing judgement is never read
  as the class the author intended.**
- **`select`** — the deterministic first-72 rule, over cases that are usable *and*
  adjudicated into their intended class. Raises `AUDIT_POOL_INSUFFICIENT` if any
  stratum falls short, and deliberately does not report how many more would be
  needed, because authoring after seeing the reviews is what the protocol forbids.
- **`certify_unit` / `certify_all`** — scores only the selected 72 through the frozen
  A3 design, so the denominator is exactly what A3 fixes. Splicing a widened stratum
  in is refused by the design check, which a test demonstrates at n=110.

Two design points worth reading in the source:

- `case_hash` deliberately **excludes** `case_id`. Two cases with the same text at
  the same parameters in the same class are the same judgement however they are
  named. Including the id would let a stratum be padded to 72 by copying one case
  under 72 ids — a denominator with no evidence behind it. A test asserts that.
- The reviewer is **not** asked "did the verifier get this right?". They establish
  ground truth and are never shown a machine verdict.

## The frozen protocol

`verifiers.tier1_audit_protocol` is **FROZEN** (`v19:tier1-audit-protocol.frozen-v1`),
accepted by the investigator on 2026-08-11. `docs/v19_tier1_audit_protocol_memo.md`
is superseded and has been removed; the decision and its reasoning are in the freeze
record's `evidence` field.

| | |
|---|---|
| Candidates authored per unit per **intended** class | **100** |
| Candidates per unit / total | 200 / **1,200** |
| Independent blinded reviewers per candidate | **2** (A, B) |
| Panel | **3**, frozen before review; C adjudicates A/B disagreements only |
| Reviewers communicate before submitting | **no** |
| Ground truth | **human adjudication only**, never the verifier |
| Cross-crediting between intended classes | **forbidden** — a mis-adjudicated candidate is **discarded** |
| Unresolved case | marked **unusable and excluded** |
| Selection | first **72** retained per stratum in frozen manifest order; reserve ignored |
| Adaptive top-up / conditional extension | **forbidden** |
| Stratum below 72 | **`AUDIT_POOL_INSUFFICIENT`** |
| Case serving two verifier units | **forbidden** |

**Why 100 and not 72.** A candidate's truth class is established by the reviewers,
not by its author. Authoring exactly 72 reaches 72 *adjudicated* cases with
probability ≈ 0.55 even when mis-adjudicated cases are credited to the other class,
and essentially never under the no-cross-crediting rule this protocol adopts. 72
remains the *denominator*; 100 is the authoring budget. At an 0.90 authoring accuracy
this leaves P(all 12 strata reach 72) ≈ 1.00 with ~28 reserve cases per stratum
ignored.

**Why the selection is prospective.** The order is `AuditManifest.ordered` — (unit,
intended class, case hash, case id) — fixed by the manifest hash before any reviewer
sees anything, and a function of case content only. It cannot respond to verifier
output, so it is not the conditional selection A3 forbids. The denominator entering
the interval is exactly 72, which is what A3's design check requires.

## What is missing — and it is not code

### 1. The 1,200 cases do not exist (blocking)

`pool.p1.audit`, `pool.p2.audit`, `pool.p3.audit` are `PENDING_CONTENT`,
`BLOCKED_BY_CONTENT`. Their declared rule is *"human-adjudicated examples with both
true-pass and true-fail support per Tier-1 verifier unit (section 10.4)"*.

§11.1 makes the audit pool one of the six disjoint scientific splits, and content
"may be authored before freeze under a versioned content procedure". §11.2's
content-sufficiency gate requires counting "human-audit examples with both true
pass and true fail support" separately by pair and scope — the slots
`sufficiency.{pair}.audit_true_pass_examples` and `…_true_fail_examples`, also
unauthored.

**No code can supply these.** Generating 1,200 plausible cases would put unauthored
scientific material into the artifact trail where nothing downstream could tell it
from material a person wrote. The module refuses to do it and a test asserts the
module ships no cases of its own.

A gate defect was fixed alongside this: `verifiers.tier1_reliability` did **not**
depend on the audit pools, so the certificate could in principle have been frozen
with the pools still empty. It now depends on all three.

### 2. The reviewer panel is not named

`ReviewerPanel` must be constructed with the two independent reviewers and the
adjudicator, and frozen before review begins. It refuses a reviewer occupying two
seats and refuses an adjudicator who is also an independent reviewer. `ingest` also
refuses a judgement from anyone outside the frozen panel.

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

**Reviewers A and B must not communicate** before submitting. Each judges every one
of the 1,200 candidates.

**Disagreement** goes to reviewer C, whose judgement establishes the class. If C
does not resolve it, the case is marked **unusable and excluded** — never resolved
by preferring either reviewer, which would invent a ground truth.

**A candidate adjudicated into the other class is discarded**, not moved. An
intended true-pass adjudicated as failing does not become true-fail evidence.

## How the evidence enters `stage2_frozen.json`

1. Author 100 candidates per unit per intended class (1,200 total); freeze
   `pool.{pair}.audit` and the sufficiency counts. Hash-bind before review begins.
2. Name and freeze the three-person `ReviewerPanel`.
3. Build the manifest; `assert_manifest_is_complete` must pass — it requires
   *exactly* 100 per stratum, every §10.6 material category, and no case serving two
   units.
4. Generate and archive `reviewer_bundle(manifest)`; record the `manifest_hash`.
5. Collect judgements. `ingest(manifest, returned, slots, panel)` — fail-closed.
6. `certify_all(manifest, adjudicated, verifier_verdicts)` → the
   `tier1_certificates` record. Raises `AUDIT_POOL_INSUFFICIENT` if any stratum has
   fewer than 72 usable cases; that is terminal, and the remedy is a fresh
   prospectively specified audit, never further authoring.
7. Append it to `stage2_frozen.json` with `frozen_by`, `recorded_at` and evidence
   naming the manifest hash and the reviewers. The typed domain re-checks that every
   unit passed and no truth class is unavailable.
8. Re-run the clean-snapshot suite and `certify_stage2`.

§10.6: *"A signed audit cannot be overwritten by a later run."* `frozen.apply`
already refuses to re-freeze a resolved slot.

## Status

**`READY_FOR_HUMAN_AUTHORING`.** The protocol is frozen and the apparatus enforces
it. What remains is human work: author 1,200 candidates, name the panel, and run the
review. `verifiers.tier1_reliability` stays unresolved until then, so Stage 2 is not
certified.
