# DCI-1 v4 revision 4 — adoption and pre-freeze decisions register

Every entry is a dated, explicit pre-freeze decision. Each resolves a value the
preregistration (`user-notes/DCI1_preregistration_v4r4.md`, which incorporates
`user-notes/DCI1_preregistration_v4r3.md` by reference) leaves open, or records
a protocol-level interpretation. Nothing here may change after the study-wide
freeze; the freeze record carries these values and any post-freeze mismatch
fails closed.

**v4r3's register (`DECISIONS_V4R3.md`) stands unchanged and is not superseded
entry by entry.** Its A0–A14 record decisions taken under v4r3, and v4r3's own
outcome — Gate 1 refused, `MEASUREMENT_EVIDENCE_INSUFFICIENT` — is what those
decisions produced. Where a v4r3 decision carries into v4r4 unchanged it is
cited rather than restated.

---

## B0 — researcher adoption of DCI-1 v4r4 (2026-08-21)

The researcher authorised, in the session brief of 2026-08-21 and before any
v4r4 stage record existed, that v4r3 be **closed at its legitimate Gate-1
failure** and that the study proceed as **DCI-1 v4 revision 4**: adopting the
deterministic-measurement Gate-1 architecture as v4r4's *native* rule,
resolving the CP4/CP7 specification ambiguity before v4r4's Gate 1, reusing
existing evidence only where scientifically and cryptographically valid,
regenerating explicitly what is invalidated, evaluating Gate 1 from scratch
under the new rule, and — if and only if it passes — resuming the registered
lifecycle.

The same authorisation **explicitly withholds** five things, and none of them
is taken:

1. any retrospective change to v4r3 or to earlier evidence;
2. any description of v4r3's Gate 1 as having passed;
3. any weakening of a gate after observing a failure;
4. any selection of a control from a composed outcome, and any inspection of a
   composed DCI outcome while resolving CP4/CP7;
5. `measurement_basis = human_validated`, which v4r4 never establishes and
   which §10.7 refuses to write.

**Why v4r4 and not v5.** v4r3 §31: *"Before study-wide freeze, any change is a
revision of this document."* v4r3 was never frozen and produced no confirmatory
data — all four replications stand at `REGIME_SCREEN`, no `gate1_measurement.json`
exists anywhere in its tree, and no estimand has been computed. A pre-freeze
change is therefore a revision. The v4r1 → v4r2 and v4r2 → v4r3 transitions are
the precedents, for the same reason.

**Why v4r4 and not an amendment to v4r3.** v4r3 had already *executed* Gate 1
and recorded a refusal. Amending the criterion of a gate that has run, inside
the revision that ran it, is exactly what §31's second consequence forbids, and
it would leave one revision holding two incompatible readings of one stage.
Closing v4r3 at its recorded outcome and starting a new revision keeps the two
readings in two documents with two hashes, which is the arrangement a reader
can check. This closes **E0** below.

## B1 — v4r3 is closed at Gate 1, and closure edits nothing (2026-08-21)

v4r3 terminated at `GATE_1_MEASUREMENT` with `MEASUREMENT_EVIDENCE_INSUFFICIENT`
under §18 stage 4 as registered at the time — §10.2 **plus §10.3 or §10.4**.

* **§10.2 passed** over the full 584-instrument declared population.
* **§10.3 was not established**: no annotator independent of the design and
  analysis team was available or obtainable. Author-performed labels are not
  independent validation and were never counted as such.
* **§10.4 was not established**: the pathway ran three times — §10.4, the
  repaired §10.4-R, and the microcase validator §10.4-R2 — and the last
  returned **FAIL** on its own registered criterion 5, whose stopping rule then
  ends the pathway.
* **Nothing followed.** No Gate 2, no reference selection, no composed-headroom
  check, no freeze, no confirmatory generation, no masked or unmasked analysis,
  and no DCI estimand of any kind.

The closure record is `dci1/reports/dci1v4r3/closure.json`. It is assembled
from the artifacts and hashed, so its summary can be checked against what it
summarises. **It edits nothing**: every v4r3 stage record, report, reviewer
artifact and generated row is byte-identical to what it was before this
revision existed, and `tests_v4r4/test_revision_and_reuse.py` asserts that the
Gate-1 record still reads as a refusal.

## B2 — Gate 1's measurement criterion is deterministic (2026-08-21)

Registered as §10.7 of the v4r4 preregistration. Changelog R4-1.

§18 stage 4 becomes *§10.2 for every verifier in the final instrument
population, plus §10.7 A–E; verifier hash and wording hash frozen*. Ten
conditions, none of them a reviewer-agreement threshold. Reviewer evidence is
carried under `supplementary_diagnostics` and is read by nothing.

**The decision this records is the researcher's, not the implementation's.**
The scientific argument is that a registered DCI constraint is mechanically
decidable — the verifier's output *is* the compliance outcome, not an estimate
of a latent human judgement — so an agreement rate with a reviewer measures the
reviewer. v4r3's development evidence is what makes that concrete rather than
theoretical: across three reviewing designs, human and LLM reviewers introduced
counting, arithmetic, segmentation, threshold and convention errors of exactly
the kind the instrument exists to remove, and §10.4-R2's diagnosis
(`validator_diagnosis.json`) attributes its failure to **convention access**
rather than competence — 0.929→0.943 agreement on answers with words against
0.231→0.692 on wordless ones.

**What is explicitly not claimed.** That deterministic code is automatically
correct. §10.7 exists because it is not: a deterministic verifier can implement
the wrong predicate perfectly, and a prose instruction can fail to pin down
which predicate was meant. A–E test those two failure modes directly.

**The §31 objection is registered inside the rule**, together with the one
checkable fact offered against it: the basis §10.7 writes is not
`human_validated`, so §10.5's scope sentence attaches permanently and no claim
available under v4r4 was unavailable under v4r3. The revision changes whether
the study executes, not what it may assert. A reader may weigh that and still
prefer v4r3's reading; the v4r3 tree is intact and its Gate-1 record unmodified.

This closes **E1**.

## B3 — CP4 and CP7 are removed rather than reworded (2026-08-21)

Registered as §7.0-R4. Changelog R4-2. Artifact:
`dci1/reports/dci1v4r4/cp4_cp7_analysis.json`.

Two of each family's four model-facing wordings state the severity as a target
quantity and name no bound — *"Give {q} percent of words letter a."*,
*"Make {q} percent of words carry doubled letters."* — while the registered
predicate is `100·S/W ≥ q`. The prose does not distinguish `≥ q` from `== q`;
the readings agree at `q` and disagree past it, where the verifier records a
**pass**. A one-sided leniency in the treatment, not in the verifier, and not
waivable.

**The decision rule was prospective and outcome-safe.** *Remove the families if
every registered coverage requirement holds without them with acceptable
support; otherwise rewrite the wordings, invalidate every row generated under
them and regenerate before recomputing coverage.* The evaluation read only the
§12.2 pre-screen difficulty table on the four v4r3 regime records — solo
compliance, chance compliance, solo vacuity per rung — and no composed cell,
`D`, `Δ` or `Ξ`. The loader it used refuses a composed field by name before any
value is read.

**The result.** §12.6's C1–C6 read `reference`-role rows and both families are
`class_control`, so those six cannot move; the run confirms it rather than
resting on it. C7 holds on all four replications. `ι_A` is unchanged on every
model. **Removal branch taken.**

**Not chosen for cost.** Rewriting would have invalidated the whole of both
families' measured rows — 16 rungs × 24 topics × 4 replications = 1,536
generations, not merely the 768 carrying the defective wordings — because §12.2
spreads four wordings over its 24 pre-screen topics. That figure is recorded in
the artifact because a reader is entitled to see it, and it did not enter the
decision.

**What removal costs.** These were the only rate-lower-bound families; the
class arm is now {count lower bound, exact count}. §7.4-R3's argument stands:
`CX1` is A's own predicate form and is the tightest class companion the grammar
can build. This closes **E2**.

## B4 — the prose-to-predicate invariant, and the one documented construction (2026-08-21)

Registered as §10.7 A′. Changelog R4-3.

Every model-facing wording must expose the comparison direction of the
predicate that scores it, by naming an operator from the registered direction
lexicon or by matching a construction registered as entailing one and
admissible for that operator. A target quantity with no operator fails.

**One construction is registered: the requirement verb.** *need*, *must*,
*require* are necessity operators over the counted feature; necessity of `q` is
satisfied by `q` or more, and English does not license the converse — *"needs
at most"* is a contradiction, not a redundancy. It therefore entails `≥` and is
admissible only where the registered operator is `≥`.

**Two wordings in the final population rely on it**, `CL7`'s and `CL8`'s fourth
templates (*"Your answer needs {q} words with letter a."* and *"… ending with
y."*), at 28 severities each. They are reported in full in
`reports/dci1v4r4/wording_review.json` with the construction named and its
derivation attached, **because this is the class of finding a reader should be
able to disagree with**. If the researcher judges the construction
insufficiently unambiguous, the remedy is B3's other branch: rewrite both
templates, invalidate every row generated under them, and regenerate — 16 rungs
× 24 topics × 4 replications = 1,536 generations. That decision is open as
**E3** and is the researcher's.

The distinction the construction rests on is lexical, not stylistic: *give* and
*make* are production verbs taking a quantity as their object, assert no
necessity, and entail no inequality. That is the whole difference between
*"Your answer needs 20 words with letter a"* and *"Give 20 percent of words
letter a"*.

## B5 — evidence is carried through a ledger, and only there (2026-08-21)

Registered as §26-R4. Changelog R4-4. Artifact:
`dci1/reports/dci1v4r4/evidence_reuse_ledger.json`.

**Generations are carried; every derived quantity is recomputed.** The model at
its pinned revision, the decoding configuration and the rendered prompt
determine a generation, and none of those changed for the 28 families v4r4
carries. Verdicts, compliance, vacuity, the §12.2 difficulty table, §12.6's
coverage and §12.3's shortlist are computed again under v4r4's canonical
verifier hash, which is new because `constraints.py` changed — §10.6 forbids
carrying a stale hash forward on the grounds that behaviour looks unchanged,
and the behavioural equivalence is therefore *measured*: 524 instruments × 164
frozen cases, both revisions' predicates, verdict against verdict.

**Nothing is `INVALIDATED_AND_REGENERATED`**, because B3 removed the two
families rather than rewording them, so v4r4 declares no instrument their rows
could score. Those rows are `HISTORICAL_ONLY`.

**One consequence recorded rather than hidden.** v4r4's seed domain carries its
study id, so a carried row's scientific seed is v4r3's. Carried rows are
reproducible from v4r3's seed schedule, which is preserved, and not from
v4r4's alone. Every carry note counts the divergence.

**What a carried Gate 0 does not exercise** is the backend call itself. §19's
pilot carries v4r3's generations and runs every other §19 check — scoring, the
observation table, the redacted structural analysis, the masking cycle,
cache-deletion-and-durable-restore, the byte-mutation refusal — under v4r4's
code, in v4r4's tree. The stage record says so on its face. This closes **E4**.

## B6 and B7 were entered after Gate 1 passed, and the register hash moves

Both close decisions this register had left open (E3, E5). Both were taken by
the researcher on 2026-08-21, **after** v4r4's Gate 1 returned PASS and
**before** Gate 2 began. Neither changes a rule Gate 1 applied: B6 ratifies a
classification the specification module already produced when the gate ran, and
B7 declines to invoke an option, leaving thresholds, candidate families and the
frozen reserve exactly as the gate saw them.

This file is a protocol document, so adding them moves the protocol hash. That
is the binding working, not a defect, and it is recorded rather than absorbed:
Gate 1's record binds `protocol_hash 1e7a7b2d` over the register at
`2ef65124`, and it carries the per-document hash table, so the delta is
resolvable to the byte. `dci1/reports/dci1v4r4/register_amendment.json` carries
both protocol hashes, both register hashes, the proof that the other three
protocol documents are byte-identical, and the proof that no measurement hash —
verifier, wordings, specification, mutation, measurement-rule — moved at all.
**No Gate-1 record was rewritten, and no gate was re-run.**

---

## B6 — the requirement-verb construction stands, and `CL7`/`CL8` are not regenerated (2026-08-21)

Closes **E3**, the decision B4 raised and left to the researcher. Registered
against §10.7 A′. Artifact: `dci1/reports/dci1v4r4/wording_review.json`, whose
`unambiguous_documented` list is the 56 wordings this turns on.

**The judgement.** *"Your answer needs {q} words with letter a."* is read as a
minimum requirement — the registered `≥ q` — and the `requirement_verb`
construction that licenses it stays registered and admissible for `≥` alone.

**Why it is different from the wordings B3 removed.** *Give {q} percent of
words letter a* names a production verb whose object is a quantity. It asserts
that `q` be produced and says nothing about `q + 1`, so `≥ q` and `== q` both
survive it and the prose selects neither: that is a comparison direction the
wording does not state. *Needs* is a necessity operator over the counted
feature. An answer that needs `q` still needs `q` when it has more, so
`necessary(S = q)` and `S ≥ q` select the same answers, and the `== q` reading
would require the verb to forbid a further occurrence, which *need* cannot do —
*"needs at most"* is a contradiction in English, not a redundancy. The
distinction is lexical and it is checkable in the artifact, where the
derivation travels attached to every wording that relies on it.

**Consequence.** No row is invalidated. The 1,536 generations B4 costed as the
price of the other branch are not spent, and the 56 wordings keep the
`unambiguous_documented` classification they were given before the gate ran —
this decision confirms a classification already recorded, it does not change
one. A reader who disagrees can find every affected wording, its severity and
the derivation in one file, which is why they were reported in full.

**What it does not do.** It registers no second construction. `DIRECTION_LEXICON`
and `DOCUMENTED_CONSTRUCTIONS` are unchanged, `assert_direction_lexicon_is_exhaustive`
still runs on the mandatory path, and any future wording that names no operator
and matches no registered construction still blocks Gate 1.

## B7 — C4's thin margin is a recorded limitation, not a trigger for expansion (2026-08-21)

Closes **E5**. Artifacts: `dci1/reports/dci1v4r4/coverage.json`
(`leave_one_family_out`, per model) and `cp4_cp7_analysis.json`
(`leave_one_family_out_finding`).

**The decision: §12.6's registered candidate expansion is not invoked.** C4 is
met on all four replications under the criterion as registered. Expanding the
candidate population because a passing solution has no spare margin would be an
adaptive design choice made after seeing a coverage result, which is exactly
the move §12.6's expansion rule exists to keep out of the study's discretion.
Thresholds, candidate families and the frozen reserve are all untouched, and
none of them may move before Gate 2.

**The limitation, recorded and carried forward:**

> C4 is identified but fragile on three models. `gemma-3n-e2b-it`, `qwen3-4b`
> and `qwen3-4b-instruct-2507` satisfy C4 with **exactly four** well-formed
> straddling feature groups, so every one of them is load-bearing and there is
> no leave-one-family-out margin. `gemma-3n-e4b-it` has five and is robust.
> Load-bearing families: `CR5`, `RF11`, `RF8` (e2b); `CR5`, `RF11`, `RF3`,
> `RF6` (qwen3-4b); `RF10`, `RF11`, `RF8`, `RF9` (qwen3-4b-instruct).

**It is inherited, not introduced.** The same sweep run on v4r3's 30-family
population returns the same load-bearing families, so B3's removal of `CP4` and
`CP7` did not cause it: `leave_one_family_out_is_unchanged_by_the_removal` is
true in the artifact. It is a property of the reference pool the study has had
since §7.0-R3.

**What it means for anything downstream.** Any Gate-3 or Gate-4 result on the
three fragile models is conditional on all four of its straddling groups
holding, and that conditionality travels with the result rather than being
re-litigated later. The expansion remains available; invoking it would be a new
decision, prospectively registered, with its own record.

---

## E — the registered open decisions and their standing

| # | Decision | Standing as of 2026-08-21 |
|---|---|---|
| E0 | Adopt v4r4 as a revision, closing v4r3 at Gate 1 | **CLOSED** by B0 and B1 |
| E1 | Gate 1's measurement criterion | **CLOSED** by B2: §10.2 plus §10.7 A–E |
| E2 | CP4/CP7: remove or reword | **CLOSED** by B3: removed under §10.2's removal rule |
| E3 | Whether the requirement-verb construction is unambiguous enough for `CL7[3]` and `CL8[3]` | **CLOSED** by B6: accepted, read as `≥ q`; no row regenerated |
| E4 | Whether a carried Gate 0 satisfies §19 | **CLOSED** by B5: yes for every check except the backend call, which the record names |
| E5 | Whether §12.6's C4 margin is thin enough to invoke the registered expansion | **CLOSED** by B7: not invoked. The zero margin on three models is carried as a recorded robustness limitation |
| E6 | Models carried to confirmation | open; four registered, per-model outcomes independent |
| E7 | Confirmatory compute budget | carried from `DECISIONS_V4R3.md` A1: 384 blocks at M = 8 |

Every v4r3 decision not listed here carries forward unchanged. `DECISIONS_V4R3.md`
remains the register for the study's history up to Gate 1.
