"""What v4r4 is, what it changed, and the hash that binds the answer.

**The revision boundary, in one place.** A reader who meets a v4r4 artifact
and wants to know how it relates to v4r3 should not have to diff two packages.
`DIFFERENCES` enumerates every intended difference, each with the reason it
was made, and `INHERITED_UNCHANGED` names the scientific content v4r4 carries
forward without alteration --- which is almost all of it, because v4r4 revises
how measurement validity is *established* and revises nothing about what the
study measures.

**The causal history, stated rather than implied.**

    v4r3 failed Gate 1 under reviewer-based validation
        -> development evidence showed that validation architecture was
           poorly matched to mechanically decidable constraints
        -> before Gate 2 and before any confirmatory scientific outcome was
           observed, v4r4 prospectively adopted deterministic specification
           and implementation validation
        -> v4r4 was evaluated under that rule from scratch

Two things that history does **not** say, and that no v4r4 artifact says
either. It does not say v4r3's Gate 1 passed; v4r3's record stands, and its
status is `MEASUREMENT_EVIDENCE_INSUFFICIENT`. And it does not say the failed
criterion was irrelevant after the fact: §10.5's second question --- would an
independent human reproduce these verdicts? --- is a real question, v4r3 was
right to ask it, and v4r4 does not answer it. What v4r4 establishes is that
the study can be *executed* while that question is open, because the basis it
writes is not `human_validated` and the scope sentence attaches permanently.

**The objection this revision has to answer.** §31 of the v4r3
preregistration says an amendment is never used to weaken a criterion in order
to make a gate pass, and that a gate executed and failed gets the registered
reading rather than a further revision. v4r4 is adopted after v4r3's Gate 1
failed, so the objection applies to it directly and is recorded here rather
than resolved quietly. The counter-argument is checkable rather than
rhetorical, and it has two halves:

* **The revision buys no stronger claim.** `MEASUREMENT_BASIS` is not
  `human_validated`; `SCOPE_SENTENCE` therefore attaches to every analysis
  record, every claim at every rung, and the final report. A criterion whose
  removal licenses no additional assertion was not standing between the study
  and a conclusion.
* **The replacement is stricter where it can be.** The specification is
  *executed* rather than described; mutation sensitivity becomes a gate
  condition; a prose-to-predicate invariant runs over all 2,096 model-facing
  wordings, which §10.6's verifier hash never covered. The first thing that
  invariant found was a defect in the treatment that reviewer agreement had
  not surfaced in three attempts, and v4r4 removed the two families carrying
  it rather than waiving it.

A reader who weighs those and still prefers v4r3's reading has everything
needed to say so: the v4r3 tree is intact, its Gate-1 record is unmodified,
and this module names the difference.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from dci1v4.protocol.hashing import canonical_json, sha_text

from dci1v4r4 import (
    CLASSIFICATION, PREREGISTRATION, STUDY_ID, SUPERSEDES,
    SUPERSEDES_TERMINAL_STAGE, SUPERSEDES_TERMINAL_STATUS,
)

DCI1 = Path(__file__).resolve().parents[3]
REPO = DCI1.parent

__all__ = ["REVISION", "PROTOCOL_DOCUMENTS", "DIFFERENCES",
           "INHERITED_UNCHANGED", "document_hashes", "revision_record",
           "protocol_hash"]

REVISION = "v4r4"

#: The documents this revision lives in. Hashed into the protocol hash, so an
#: edit to any of them after a stage record is written is visible as a hash
#: that no longer matches.
PROTOCOL_DOCUMENTS = (
    "user-notes/DCI1_preregistration_v4r4.md",
    "user-notes/DCI1_v4r3_to_v4r4_changelog.md",
    "dci1/DECISIONS_V4R4.md",
    # v4r4's preregistration is a revision document: it restates in full only
    # the sections it changes and incorporates the rest of v4r3's by
    # reference. So v4r3's document is part of what v4r4 registers, and an
    # edit to it after a v4r4 stage record exists must be as visible as an
    # edit to v4r4's own.
    "user-notes/DCI1_preregistration_v4r3.md",
)

#: Every intended difference from v4r3, with its reason. A difference not
#: listed here is a defect, and `tests_v4r4/test_revision.py` is what makes
#: that statement testable rather than aspirational.
DIFFERENCES: tuple[dict[str, str], ...] = (
    {
        "id": "R4-1",
        "area": "Gate 1 measurement criterion",
        "v4r3": "§18 stage 4: §10.2 for every verifier in the final "
                "instrument population, plus §10.3 (independent human "
                "validation) or §10.4 (autorater calibration approved by the "
                "researcher)",
        "v4r4": "§18 stage 4: §10.2 for every verifier in the final "
                "instrument population, plus §10.7 A-E --- specification "
                "validity, implementation validity, independent "
                "reimplementation, adversarial/boundary/mutation validation, "
                "and provenance binding",
        "why": "the study's constraints are mechanically decidable: the "
               "pipeline is model response -> deterministic verifier -> "
               "compliance outcome, and the verifier's output IS the outcome. "
               "There is no latent quantity an external rater estimates, so "
               "an agreement rate measures the rater. v4r3's development "
               "record shows what it measured: human and LLM reviewers "
               "introduced counting, arithmetic, segmentation, threshold and "
               "convention errors of exactly the kind the instrument exists "
               "to remove",
        "consequence": "reviewer agreement can move no v4r4 gate in either "
                       "direction; §10.3/§10.4 artifacts are preserved as "
                       "diagnostics",
    },
    {
        "id": "R4-2",
        "area": "candidate population (§7.0-R4)",
        "v4r3": "30 families, 584 declared instruments; the class arm is CL7, "
                "CL8, CP4, CP7, CX1, CX2",
        "v4r4": "28 families, 524 declared instruments; the class arm is CL7, "
                "CL8, CX1, CX2",
        "why": "CP4's and CP7's third and fourth model-facing wordings state "
               "the severity as a target and name no bound, while the "
               "registered predicate is a lower bound. The prose does not "
               "distinguish >= q from == q; the readings agree at q and "
               "disagree past it, where the verifier records a pass. That is "
               "a defect in the treatment, and it is not waivable",
        "consequence": "no rate-lower-bound family remains; §12.6's C1-C6 "
                       "read reference-role rows only and are unchanged by "
                       "construction, and C7 keeps an eligible class rung "
                       "within the §13.7 caliper on all four replications. "
                       "The verifier hash, the wording hash and the "
                       "instrument-population hash all move because of this",
    },
    {
        "id": "R4-3",
        "area": "prose-to-predicate invariant (§10.7 A')",
        "v4r3": "the wording review classified findings and recorded them; "
                "there was no registered rule that a wording must expose its "
                "comparison direction",
        "v4r4": "every model-facing wording must name an operator from the "
                "registered direction lexicon, or match a construction "
                "registered as entailing one and admissible for that "
                "operator. A wording that gives only a target quantity fails "
                "specification validation",
        "why": "an ambiguous instruction is a defect in the treatment, and "
               "§10.2 cannot see it: two implementations of the same "
               "predicate agree with each other whatever the prose says",
        "consequence": "the rule is what removed CP4 and CP7; it also "
                       "documents, with its derivation, the one construction "
                       "two remaining wordings rely on",
    },
    {
        "id": "R4-4",
        "area": "measurement basis",
        "v4r3": "human_validated | autorater_calibration_approved | "
                "human_validation_unavailable",
        "v4r4": "deterministic_measurement_validated, and Gate 1 refuses "
                "every reviewer-derived basis before it reads any evidence",
        "why": "the basis names how validity was established. A record that "
               "said human_validated under this rule would be false",
        "consequence": "SCOPE_SENTENCE attaches permanently; §10.5's second "
                       "question is unanswered under v4r4 exactly as under "
                       "v4r3",
    },
    {
        "id": "R4-5",
        "area": "stage records",
        "v4r3": "records carried stage, artifact type, outcome and content; "
                "study identity was implicit in the path and the signing key",
        "v4r4": "every record carries study_id; write_stage_record stamps it "
                "and read_stage_record refuses a record from another study",
        "why": "v4r4 runs beside a closed v4r3 whose signed QUALIFIED, "
               "GATE_0_APPARATUS and REGIME_SCREEN records exist on disk. "
               "None may satisfy a v4r4 predecessor check, and the guard "
               "belongs at the point of reading, where it still holds if a "
               "record is copied",
        "consequence": "a v4r3 record produces an IntegrityError naming both "
                       "study ids, rather than being silently absent",
    },
    {
        "id": "R4-6",
        "area": "evidence reuse",
        "v4r3": "not applicable: v4r3 generated its own evidence",
        "v4r4": "every artifact carried from v4r3 is classified in an "
                "explicit ledger (stages/reuse.py) as REUSED_UNCHANGED, "
                "RECOMPUTED_FROM_EXISTING_RAW_DATA, "
                "INVALIDATED_AND_REGENERATED, HISTORICAL_ONLY or "
                "NOT_APPLICABLE, with its source hash and the v4r4 criterion "
                "it satisfies",
        "why": "reuse is only valid when every quantity that determines the "
               "evidence is unchanged. Naming the quantities and checking "
               "them is the difference between reuse and assumption",
        "consequence": "a v4r4 stage record that rests on v4r3 rows says so "
                       "on its face rather than presenting them as newly "
                       "generated",
    },
    {
        "id": "R4-7",
        "area": "N_CLASS_FAMILIES",
        "v4r3": "the literal 4, while the pool held six class families",
        "v4r4": "derived from CLASS_FAMILY_IDS",
        "why": "the registration record it feeds described a pool it "
               "disagreed with",
        "consequence": "the value is 4 and is now true",
    },
)

#: The scientific content v4r4 carries from v4r3 without alteration. Named
#: because the interesting claim about a revision is usually what it did *not*
#: change, and a reader comparing a v4r3 number to a v4r4 number needs to know
#: which side of that line it falls on.
INHERITED_UNCHANGED: tuple[str, ...] = (
    "the research question and the interference construct (§3)",
    "the estimands: D, Delta_R, Delta_j, delta_difficulty, Xi, Lambda and "
    "the reciprocal matrix (§11)",
    "the hypotheses and the claim ladder L1-L5, with L5 withheld (§3.2)",
    "the four registered replications and their revisions (§5)",
    "the difficulty coordinate: instructed compliance, with raw solo "
    "compliance reported beside it (§13.3)",
    "the candidate-library grammar, its ladders, its frozen reserves and the "
    "expansion rule (§7.0, §12.6) --- minus the two families of R4-2",
    "every registered threshold, caliper, band and precision precondition "
    "(§12, §13, §16, §11.8)",
    "the topic bank, its five sets and the reservation rule (§6.2, §12.5)",
    "the masking principle and the one-shot unmasking rule (§14, §17)",
    "the confirmatory analysis plan, the bootstrap and the multiplicity "
    "correction (§15, §17)",
    "the counting statistics, the segmentation convention and the compliance "
    "predicates (§7.3, §9.2) --- byte-identical",
    "§10.2's evidence architecture in full: determinism, boundary suites, "
    "independent reimplementation, adversarial corpus, witnesses, carry-over",
)


def document_hashes() -> dict[str, str]:
    out: dict[str, str] = {}
    for relative in PROTOCOL_DOCUMENTS:
        path = REPO / relative
        out[relative] = (hashlib.sha256(path.read_bytes()).hexdigest()
                         if path.exists() else "MISSING")
    return out


def revision_record() -> dict[str, Any]:
    """Everything the protocol hash covers, assembled once."""
    return {
        "revision": REVISION,
        "study_id": STUDY_ID,
        "classification": CLASSIFICATION,
        "preregistration": PREREGISTRATION,
        "supersedes": SUPERSEDES,
        "supersedes_terminal_stage": SUPERSEDES_TERMINAL_STAGE,
        "supersedes_terminal_status": SUPERSEDES_TERMINAL_STATUS,
        "supersession_is_not_a_retroactive_pass":
            "v4r3's Gate 1 record stands as written. v4r4 is a new revision "
            "evaluated from scratch, not a re-reading of v4r3's outcome",
        "documents": document_hashes(),
        "differences": [dict(entry) for entry in DIFFERENCES],
        "inherited_unchanged": list(INHERITED_UNCHANGED),
    }


def protocol_hash(record: dict[str, Any] | None = None) -> str:
    """The v4r4 protocol hash: the revision record, documents included."""
    return sha_text(canonical_json(record if record is not None
                                   else revision_record()))
