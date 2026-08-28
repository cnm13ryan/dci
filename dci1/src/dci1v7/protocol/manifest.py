"""§18 stage 1's signed registration manifest, and the five things that stop
it being signed.

The manifest is where every study-wide rule stops being a draft. §6.1's
cross-replication firewall decides what belongs in it: study-wide values are
bound here once, before the first qualification, and model-adaptive values ---
n*, m*, the completion cap, the closed vocabulary, the admitted references,
the arm set --- never appear, because they reach the code only through
per-model gate records. ``assert_no_model_adaptive_values`` enforces that
split executably rather than by convention.

**Every refusal that used to stop it is still built**, and each one is a
different kind of not-ready:

1. a §34 decision is open --- ``protocol/decisions.py``;
2. a specification question the documents do not settle is unresolved ---
   ``protocol/open_items.py``;
3. a required topic-bank hash is missing --- Calibration-B does not exist;
4. the candidate population is unapproved --- §34 D4;
5. a red-team finding whose registered mitigation *is* a decision is still
   open --- R1, R11, R14, R16;
6. a floor is unspecified, a model revision unpinned, a design not derivable,
   or a governed document still declares itself a draft.

They are checked separately and reported separately, because "we have not
decided" and "the work has not been done" are different facts and collapsing
them into one refusal loses which one a researcher has to act on. §18 stage
1's readiness status is ``REGISTRATION_INCOMPLETE`` for all of them, and since
amendment A15 it is a **refusal** and not a §28 terminal outcome: each of these
names work a researcher has to do, so the stage is attempted again once it is
done. ``run/lifecycle.ReadinessRefusal`` is where that is written down.

``build_manifest`` assembles the payload **whether or not it can be signed**,
so that a researcher can see exactly what adoption would bind before adopting
anything. ``assert_signable`` is what refuses, and ``sign_registration`` calls
it first.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from dci1v4.engine import fs, store
from dci1v4.engine.signing import create_signing_key, sign_payload, verify_signed
from dci1v4.errors import IntegrityError, ProtocolError
from dci1v4.models.registry import MODELS, registration_models
from dci1v4.protocol.hashing import sha_obj

from dci1v7 import (CLASSIFICATION, PREREGISTRATION, REFERENCE_DESIGN_SPEC,
                    STUDY_ID)
from dci1v7.analysis import spectrum
from dci1v7.design import budget, cells
from dci1v7.engine.context import StudyContext
from dci1v7.protocol import constants as C
from dci1v7.protocol import (decisions, identification, open_items,
                             revision, seeds, taxonomy)
from dci1v7.protocol import wordings
from dci1v7.protocol.wordings import wording_source_hash
from dci1v7.stages import construct_strength
from dci1v7.stages.audit_prefreeze import UNRESOLVED_REDTEAM_FINDINGS
from dci1v7.topics import calibration_b
from dci1v7.topics.bank import TopicBank, load_bank
from dci1v7.verifiers import constraints, verifier_source_hash
from dci1v7.verifiers.constraints import FAMILIES, RESERVES

__all__ = ["PROTOCOL_VERSION", "PROTOCOL_DOCUMENT", "MODEL_ADAPTIVE_KEYS",
           "DRAFT_MARKER", "assert_documents_adopted", "apparatus_faults",
           "REQUIRED_BINDINGS", "REGISTRATION_INCOMPLETE", "Blocker",
           "signing_blockers", "assert_signable", "build_manifest",
           "assert_no_model_adaptive_values", "document_hashes",
           "sign_registration", "ensure_registration", "load_manifest",
           "AMENDMENTS_DIRNAME", "AMENDMENT_DIRECTIONS", "amendment_records",
           "document_binding"]

#: The version a v7 artifact declares. A version number is a claim about what
#: a document fixes, and the document it fixes is ``PROTOCOL_DOCUMENT``, bound
#: by content hash into every signed manifest --- so the claim is checkable
#: rather than asserted. ``assert_documents_adopted`` reads that document's own
#: status line, so this constant never stands in for adoption.
PROTOCOL_VERSION = "7.0"
PROTOCOL_DOCUMENT = PREREGISTRATION
REGISTRATION_INCOMPLETE = decisions.REGISTRATION_INCOMPLETE

#: Keys that would be a model-adaptive value if they appeared (§6.1).
MODEL_ADAPTIVE_KEYS = (
    "n_star", "m_star", "completion_cap", "selected_cap", "carried_set",
    "admitted_references", "reference_severities", "spectrum_severities",
    "near_form_controls", "broad_class_control", "admitted_arms",
    "measured_vocabulary", "coverage_report", "qualified_pool",
    "identification_statuses", "derived_cell_count")

#: Every top-level binding §34 and §18.1 require the manifest to carry. The
#: tuple is asserted against the built payload, so a binding that is dropped
#: from the builder fails a test rather than going missing from a signature.
REQUIRED_BINDINGS = (
    "study_id", "protocol", "protocol_version", "protocol_document",
    "protocol_hash", "reference_design_spec", "reference_design_spec_hash",
    "classification", "producing_commit", "decisions", "open_items",
    "models", "backend", "topics", "candidate_library", "marker_population",
    "structural_taxonomy", "severity_ladders", "focal_grid", "constraints",
    "instruments", "design", "decoding_policy_form", "seeds",
    "selection_rules", "validity_rule", "interaction_rule", "stability_rule",
    "support_requirements", "lifecycle", "estimands", "order_estimands",
    "multiplicity_families", "claim_ladder", "masking", "freeze_requirements",
    "measurement_basis", "thresholds", "precision_preconditions",
    "reuse_ledger", "revision_changes", "red_team", "apparatus_faults",
    "amendments",
)


class Blocker(ProtocolError):
    """A named reason the registration manifest may not be signed."""


def document_hashes(repo_root: Path | str = ".") -> dict[str, Any]:
    """The two documents the manifest binds, by content.

    §18 stage 1 binds *this document's* hash and the spec file's hash, so a
    later reader can prove which text the study registered. A missing file is
    a refusal and not an empty string: an unbound protocol hash is exactly the
    hole this field exists to close.
    """
    out: dict[str, Any] = {}
    for name, rel in (("protocol_hash", PROTOCOL_DOCUMENT),
                      ("reference_design_spec_hash", REFERENCE_DESIGN_SPEC)):
        path = Path(repo_root) / rel
        if not path.exists():
            raise Blocker(
                f"§18 stage 1 binds the hash of {rel} and the file is not at "
                f"{path}; a registration that cannot name its own protocol "
                "text binds nothing")
        out[name] = sha_obj({"path": rel, "bytes": path.read_bytes().hex()})
    return out


def apparatus_faults(context: StudyContext) -> list[dict[str, Any]]:
    """Every retired stage-1 apparatus fault in this study, read from disk.

    A15. ``run/registration_run.retire_apparatus_fault`` retains a readiness
    verdict that a caller's own defect wrote as a §28.3 terminal report, and
    this is what puts it **inside** the signature of the registration that
    follows. A retirement recorded beside a registration rather than within it
    would let the study's own signed provenance read as though the failed
    attempt had never happened, which is exactly what §32 forbids.

    It is a plain read of the evidence tree: the list is empty for a study
    with no fault, so a manifest built anywhere carries the field and the
    honest value.
    """
    from dci1v7.engine import paths as P

    out: list[dict[str, Any]] = []
    for path in P.apparatus_fault_records(Path(context.study_root)):
        body = json.loads(path.read_text())
        out.append(body.get("payload", body))
    return out


#: The marker a governed document carries while it is not yet the study's
#: commitment. Both documents §18 stage 1 binds are checked for it.
DRAFT_MARKER = "DRAFT_NOT_ADOPTED"


def assert_documents_adopted(repo_root: Path | str = ".") -> dict[str, Any]:
    """Refuse a registration whose protocol text says it is a draft.

    ``document_hashes`` binds the two documents by content and refuses a
    *missing* one. That is not enough once a draft exists: a complete,
    self-consistent draft is exactly the thing that could be mistaken for a
    registration by being present. So the documents declare their own status
    and this reads it.

    The preregistration declares it on a line ``status: <value>``; the
    reference-design spec in its ``_status`` field. A document with no
    declaration at all is treated as a draft, because the safe reading of
    silence here is the one that refuses --- and so is a **missing** one, so
    that ``signing_blockers`` and ``document_hashes`` refuse the same two
    files for the same reason. Before this existed the plan could report
    ``can_register`` while neither document was written, because
    ``document_hashes`` raises only at ``build_manifest`` time.

    **Adopting a document is a researcher act.** Nothing in this package
    writes either file or edits either marker.
    """
    root = Path(repo_root)
    findings: list[dict[str, Any]] = []
    prereg = root / PROTOCOL_DOCUMENT
    if not prereg.exists():
        declared = "missing"
    else:
        lines = [ln.strip() for ln in prereg.read_text().splitlines()]
        declared = next((ln.split(":", 1)[1].strip() for ln in lines
                         if ln.lower().startswith("status:")), "none")
    if declared != "ADOPTED":
        findings.append({"document": PROTOCOL_DOCUMENT,
                         "declared": declared, "required": "ADOPTED"})
    spec = root / REFERENCE_DESIGN_SPEC
    if not spec.exists():
        declared = "missing"
    else:
        try:
            declared = str(json.loads(spec.read_text()).get("_status")
                           or "none")
        except json.JSONDecodeError:
            declared = "unreadable"
    if not declared.startswith("ADOPTED"):
        findings.append({"document": REFERENCE_DESIGN_SPEC,
                         "declared": declared, "required": "ADOPTED"})
    return {"adopted": not findings, "findings": findings,
            "draft_marker": DRAFT_MARKER,
            "why": "a registration binds these two documents by hash; a "
                   "document that says it is a draft may not be the text a "
                   "study registers, and adopting one is a researcher act"}


# ------------------------------------------------------------- refusals

def signing_blockers(bank: TopicBank | None = None, *,
                     repo_root: Path | str | None = None
                     ) -> list[dict[str, Any]]:
    """Every refusal, each reported separately and by kind.

    Five of them are about things nobody has decided yet. The last four are
    about things a decision *implies* and that a closure alone does not
    establish: a confirmation the researcher has to give, a floor a `floor`
    closure has to carry, model revisions that have to be pinned to a
    resolvable commit, and an arm set and a budget that have to be derivable.
    A manifest that bound a decision's label without the values the label
    stands for would be a signature over an intention.
    """
    bank = bank if bank is not None else load_bank()
    blockers: list[dict[str, Any]] = []

    # A complete draft is exactly the thing that could be mistaken for a
    # registration by being present, so its own declared status is read.
    from dci1v7.engine.context import REPO_ROOT

    adoption = assert_documents_adopted(
        REPO_ROOT if repo_root is None else repo_root)
    if not adoption["adopted"]:
        blockers.append({
            "kind": "DRAFT_DOCUMENT", "section": "§18 stage 1",
            "what": "a document §18 stage 1 binds by hash is missing or "
                    "declares itself a draft; adopting it is a researcher act",
            "n": len(adoption["findings"]),
            "findings": adoption["findings"]})

    # §34 D0 is the adoption act itself, and `do_not_adopt` is the only
    # closure in the register that means "this study does not run". Until
    # 2026-08-26 nothing read it, so closing there signed a manifest exactly
    # as `adopt` did --- a decision whose refusing value refused nothing.
    if decisions.is_closed("D0") and decisions.value_of("D0") == "do_not_adopt":
        blockers.append({
            "kind": "NOT_ADOPTED", "section": "§34 D0",
            "what": "§34 D0 is closed at `do_not_adopt`: the researcher "
                    "decided this protocol version is not adopted, and a "
                    "registration manifest is the act of adopting it",
            "n": 1,
            "detail": {"D0": decisions.value_of("D0"),
                       "evidence": decisions.DECISIONS["D0"].evidence}})

    still_open = list(decisions.open_decisions())
    if still_open:
        blockers.append({
            "kind": "OPEN_DECISION", "section": "§34",
            "detail": still_open,
            "n": len(still_open),
            "why": "§34 requires every decision closed, with its evidence, in "
                   "this manifest before stage 1 can pass"})

    blocking_items = list(open_items.blocking_items())
    if blocking_items:
        blockers.append({
            "kind": "UNRESOLVED_SPECIFICATION", "section": "§33",
            "detail": [{"id": i, "title": open_items.OPEN_ITEMS[i].title,
                        "alternatives":
                            [a.id for a in open_items.OPEN_ITEMS[i]
                             .alternatives]}
                       for i in blocking_items],
            "n": len(blocking_items),
            "why": "the preregistration, the spec and the implementation do "
                   "not determine the rule, and the admissible formulations "
                   "estimate different things"})

    missing_hashes = [name for name, value in bank.hashes.items()
                      if value is None and name != "sequestered"]
    if missing_hashes:
        blockers.append({
            "kind": "MISSING_TOPIC_HASH", "section": "§6.2",
            "detail": missing_hashes,
            "calibration_b_status": bank.calibration_b_status,
            "n": len(missing_hashes),
            "why": "§18 stage 1 binds the topic-bank hash and §13.7 needs two "
                   "disjoint 96-topic calibration sets; Calibration-B is "
                   f"{bank.calibration_b_status}"})

    if not decisions.is_closed("D4"):
        blockers.append({
            "kind": "CANDIDATE_POPULATION_UNAPPROVED", "section": "§7.10",
            "detail": {"decision": "D4",
                       "markers": list(C.MARKER_WORDS),
                       "families": C.N_FAMILIES,
                       "instruments": C.N_INSTRUMENTS},
            "n": 1,
            "why": "the manifest binds the marker population and the "
                   "candidate library; §34 D4 is the approval and it is open"})

    open_findings = {k: v for k, v in UNRESOLVED_REDTEAM_FINDINGS.items()
                     if v["decision"] and
                     not decisions.is_closed(v["decision"])}
    if open_findings:
        blockers.append({
            "kind": "OPEN_RED_TEAM_FINDING", "section": "§33",
            "detail": {k: {"decision": v["decision"],
                           "finding": v["finding"]}
                       for k, v in open_findings.items()},
            "n": len(open_findings),
            "why": "each of these findings' registered mitigation IS a §34 "
                   "decision; closing the decision is what resolves it"})

    # P1 is CONFIRM_AT_ADOPTION: a stale sentence was corrected to match the
    # rule three other sections and the code already implemented, and the
    # researcher confirms the correction **at adoption** rather than
    # discovering it afterwards. It does not block a stage --- nothing
    # executable turns on it --- but signing without it would be signing a
    # document nobody read.
    unconfirmed = [k for k, i in open_items.OPEN_ITEMS.items()
                   if i.status == open_items.CONFIRM_AT_ADOPTION
                   and i.resolution is None]
    if unconfirmed:
        blockers.append({
            "kind": "UNCONFIRMED_AT_ADOPTION", "section": "§33",
            "detail": [{"id": k, "title": open_items.OPEN_ITEMS[k].title}
                       for k in unconfirmed],
            "n": len(unconfirmed),
            "why": "a corrected sentence changes nothing executable and is "
                   "still a change to the registered text; adoption is when "
                   "the researcher confirms it"})

    # §34 D17 closed at `floor` without a FloorSpec is a decision to have a
    # rule and no rule. `registered_floor` raises rather than inventing one,
    # so this reports it as a blocker instead of letting the manifest build
    # and Gate 2 discover it.
    if decisions.value_of("D17") == "floor":
        try:
            floor = construct_strength.registered_floor()
        except ProtocolError as exc:
            blockers.append({
                "kind": "FLOOR_NOT_SPECIFIED", "section": "§34",
                "detail": str(exc), "n": 1,
                "why": "D17 is closed at 'floor'; the quantity, the value, "
                       "the semantics and the derivation live in the "
                       "researcher's record and this implementation does not "
                       "invent any of them"})
        else:
            if floor is None:                              # pragma: no cover
                blockers.append({
                    "kind": "FLOOR_NOT_SPECIFIED", "section": "§34",
                    "detail": "registered_floor() returned None under a "
                              "'floor' closure", "n": 1,
                    "why": "the branch and the spec disagree"})

    # §6.1 fixes the model revisions in this manifest before qualification, so
    # a manifest signed over an unpinned revision fixes nothing. Forty hex
    # characters is a resolved commit; a tag or a branch is not.
    unpinned = [m.model_key for m in MODELS
                if len(m.revision) != 40
                or any(c not in "0123456789abcdef" for c in m.revision)]
    if unpinned:
        blockers.append({
            "kind": "MODEL_REVISION_UNPINNED", "section": "§6.1",
            "detail": unpinned, "n": len(unpinned),
            "why": "§6.1 binds the exact revision of every replication into "
                   "this manifest and asserts it at every generation; a "
                   "revision that is not a resolved 40-character commit "
                   "binds nothing"})

    # D1 names a budget option; the arm set, the cell count and the generation
    # total are what the option *is*. If either is not derivable the manifest
    # would carry a label with no design behind it.
    try:
        cells.admitted_arms_from_decision()
        budget.registered_budget()
    except ProtocolError as exc:
        blockers.append({
            "kind": "DESIGN_NOT_DERIVABLE", "section": "§34",
            "detail": str(exc), "n": 1,
            "why": "§34 D1's closure has to yield an arm set, a cell count "
                   "and a generation budget the code can reproduce"})
    return blockers


def assert_signable(bank: TopicBank | None = None, *,
                    where: str = "registration",
                    repo_root: Path | str | None = None) -> None:
    """§18 stage 1: refuse, by name, everything that is not ready."""
    blockers = signing_blockers(bank, repo_root=repo_root)
    if blockers:
        summary = ", ".join(f"{b['kind']}({b['n']})" for b in blockers)
        raise Blocker(
            f"{where}: the v5 registration manifest may not be signed --- "
            f"{summary}. §18 stage 1 records {REGISTRATION_INCOMPLETE}. "
            f"Detail: {blockers}")


# ------------------------------------------------------------- the payload

def _candidate_library() -> dict[str, Any]:
    return {
        "grammar": "a registered counted statistic under a registered "
                   "predicate form; nothing else is a candidate family",
        "statistics": list(C.STATISTIC_IDS),
        "forms": list(C.FORMS),
        "families": {
            kind: {"statistic": f.statistic_id, "form": f.form,
                   "class": f.constraint_class,
                   "tier": f.structural_tier, "rule": f.rule,
                   "statistic_source": f.statistic_source,
                   "metadata": dict(f.metadata),
                   "ladder": list(f.ladder), "reserve": list(f.reserve)}
            for kind, f in FAMILIES.items()},
        "n_families": C.N_FAMILIES,
        "round_zero_severities": C.N_SEVERITIES,
        "declared_severities": sum(len(v) for v in RESERVES.values()),
        "instruments": C.N_INSTRUMENTS,
        "verifiers": C.N_VERIFIERS,
        "population": "the declared range of §7, not the round-0 ladder",
        "frozen_by": "§7.10; §12.6's expansion picks from the reserve and "
                     "never authors a family",
    }


def build_manifest(context: StudyContext, *, producing_commit: str,
                   adoption: Mapping[str, Any],
                   bank: TopicBank | None = None,
                   repo_root: Path | str = ".",
                   supersedes: str | None = None) -> dict[str, Any]:
    """Every study-wide rule, as one signable payload.

    Assembled whether or not it is signable. A researcher deciding whether to
    adopt v5 needs to see what adoption would bind, and a builder that
    refused before assembling would make that impossible.
    """
    bank = bank if bank is not None else load_bank()
    manifest: dict[str, Any] = {
        "study_id": context.study_id,
        "protocol": "DCI-1",
        "protocol_version": PROTOCOL_VERSION,
        "protocol_document": PROTOCOL_DOCUMENT,
        "reference_design_spec": REFERENCE_DESIGN_SPEC,
        "classification": CLASSIFICATION,
        "frozen": False,
        "status": ("registration manifest only; the protocol is NOT frozen "
                   "and no confirmatory data exist"),
        "producing_commit": producing_commit,
        "adoption": dict(adoption),
        **document_hashes(repo_root),

        # ------------------------------------------------ §34 and §33
        "decisions": decisions.registration_payload(),
        "open_items": open_items.manifest_payload(),
        "red_team": {
            # The finding register v7 carries is v5's, at v5's own path: the
            # findings are about the protocol all three versions share, and
            # neither v6 nor v7 rewrote or re-verdicted them. v6's audit
            # passes and v7's own are the READINESS sections named beside it.
            "source": "dci1/reports/dci1v5/v5_prereg_redteam.md",
            "v6_passes": ["dci1/reports/dci1v6/READINESS.md §13",
                          "dci1/reports/dci1v6/READINESS.md §14"],
            "v7_passes": ["dci1/reports/dci1v7/READINESS.md"],
            "unresolved": {k: dict(v)
                           for k, v in UNRESOLVED_REDTEAM_FINDINGS.items()},
            "not_closeable_by_rule":
                [k for k, v in UNRESOLVED_REDTEAM_FINDINGS.items()
                 if not v["closeable_by_rule"]],
        },
        "revision_changes": revision.revision_record(),

        # v7 §32: the amendment chain this registration starts from. Empty at
        # signing --- an amendment is adopted after a registration exists ---
        # and bound so a manifest signed after an earlier chain says so.
        "amendments": {
            "rule": "§32/v7 A4: an amendment adopted after this registration "
                    "is a signed, append-only record under "
                    f"registration/{AMENDMENTS_DIRNAME}/ linking the bound "
                    "document hashes to the amended ones, with the stage "
                    "each replication had reached and its row count, the "
                    "declared direction and the §32.2 disclosure. "
                    "`document_binding` walks the chain; the pre-freeze "
                    "audit and the freeze read its head. §32.3 is refused "
                    "executably: no amendment naming §13 once any "
                    "replication holds a Gate-2.5 record",
            "directions": list(AMENDMENT_DIRECTIONS),
            # Deliberately NOT the chain itself: `ensure_registration`
            # rebuilds this payload to verify a later replication's
            # registration against the signed one, and a manifest whose hash
            # moved with every amendment would refuse every registration
            # after the first amendment. The chain lives under
            # registration/amendments/, signed, and the freeze binds it.
            "chain_location": f"registration/{AMENDMENTS_DIRNAME}/",
            "bound_by": "GATE_5_FREEZE (`amendments`, `registered_protocol_hash`)",
        },

        # A15. Every stage-1 readiness verdict this study retired as an
        # apparatus fault, by the hash of the record retired. Read from the
        # evidence tree at build time and therefore inside the signature: a
        # registration that followed a retirement says so in its own payload,
        # so the study's signed provenance cannot read as though the failed
        # attempt never occurred. Empty for a study that had none.
        "apparatus_faults": {
            "rule": "§32/A15: a §18 stage-1 readiness verdict written as a "
                    "§28.3 terminal report by an apparatus or configuration "
                    "fault is RETAINED under "
                    "superseded/apparatus_fault/<record hash>/ and named "
                    "here. Nothing is deleted, and no scientific terminal is "
                    "retirable by that path",
            "retired": apparatus_faults(context),
        },

        # ------------------------------------------------------ apparatus
        "models": registration_models(),
        "judges": ["gpt-oss-20b"],
        "backend": {
            "backend": "vLLM", "pinned": "0.15.1+rocm720",
            "dtype": "bfloat16", "tensor_parallel_size": 1,
            "chat_template": "each model's own, from its pinned revision",
            "reasoning_mode": "disabled where the model offers one; "
                              "unavailable otherwise (§6.1)",
        },
        "decoding_policy_form": {
            "temperature": 0.7, "top_p": 0.9, "top_k": 50,
            "completion_cap_grid": list(C.COMPLETION_CAPS),
            "zero_shot": True, "single_turn": True,
            "no_examples_tools_retrieval_self_consistency_best_of_n": True,
        },
        "seeds": {
            "domain_strings": list(seeds.V4R3_DOMAINS),
            "generation_root": seeds.GENERATION_ROOT_SEED,
            "bootstrap_root": seeds.BOOTSTRAP_ROOT_SEED,
            "mask_root": seeds.MASK_ROOT_SEED,
            "topic_split_seed": "v4r2's, carried unchanged (§6.2)",
        },

        # --------------------------------------------------------- §6.2
        "topics": {
            **bank.split_identity,
            "sets": {name: {"n": len(bank.sets[name]),
                            "hash": bank.hashes[name]}
                     for name in C.TOPIC_SETS},
            "calibration_a_hash": bank.hashes[C.CALIBRATION_A],
            "calibration_b_hash": bank.hashes[C.CALIBRATION_B],
            "authoring_rules": list(C.AUTHORING_RULES),
            "development_sets": list(C.DEVELOPMENT_TOPIC_SETS),
            "reserved_sets": list(C.RESERVED_TOPIC_SETS),
            # §34 D3. The bank hash is already above; this is the claim that
            # makes it worth having --- when it was authored, against what,
            # and what had not happened yet. §13.7 is a stability test only
            # if the second split is naive, and that is a fact about the
            # authoring, not about the questions.
            "calibration_b_provenance": calibration_b.provenance_record(),
        },

        # ------------------------------------------------------ §7, §10
        "candidate_library": _candidate_library(),
        # §34 D4, closed at `approve_eight`. The exact eight --- ids, words,
        # discourse roles, verifier statistic ids, ladders and reserves ---
        # with the population hash that makes a substitution detectable
        # rather than merely forbidden, and the four limitations the
        # researcher accepted rather than substituted for.
        "marker_population": {
            "words": list(C.MARKER_WORDS),
            "max_letters": C.MARKER_MAX_LETTERS,
            "natural_frequency_max": C.MARKER_NATURAL_FREQUENCY_MAX,
            "benchmark": "A's own `however` frequency (§7.6 rule 3)",
            "evidence_class": "DEVELOPMENT_EVIDENCE",
            "approved_by": "§34 D4",
            "approval_status": decisions.value_of("D4"),
            **constraints.marker_population(),
        },
        "structural_taxonomy": {
            "fields": list(taxonomy.METADATA_FIELDS),
            "tiers": list(taxonomy.TIERS),
            "slots": list(taxonomy.SLOTS),
            "tier_rule": "computed from the metadata record, never declared",
            "a_record": dict(taxonomy.A_STRUCTURAL_RECORD),
        },
        "severity_ladders": {kind: {"ladder": list(f.ladder),
                                    "reserve": list(f.reserve)}
                             for kind, f in FAMILIES.items()},
        "focal_grid": {"grid": list(C.FOCAL_GRID),
                       "extension": list(C.FOCAL_EXTENSION),
                       "target_grid": list(C.TARGET_GRID),
                       "target_word": C.TARGET_WORD},
        "constraints": {
            "family_rule_statements":
                dict(wordings.FAMILY_RULE_STATEMENTS),
            "wordings_per_constraint": C.N_WORDINGS,
            "wording_length_tolerance": C.WORDING_LENGTH_TOLERANCE,
            "wording_length_measured_against": "A",
            "wording_hash": wording_source_hash(),
        },
        "instruments": {
            "canonical_verifier_hash": verifier_source_hash(),
            "non_vacuity_min_words": C.NON_VACUITY_MIN_WORDS,
            "stem_band": list(C.STEM_BAND),
            "exact_count_rules": list(C.EXACT_COUNT_RULES),
            "primary_exact_count_rule": C.PRIMARY_EXACT_COUNT_RULE,
            "presence_rule": "§9.1: an instance is scored present only where "
                             "the prompt stated it; absent verdicts are "
                             "chance verdicts and no estimand reads them as "
                             "treated",
            "determinism_processes": C.DETERMINISM_PROCESSES,
            "boundary_suite_min_cases": C.BOUNDARY_SUITE_MIN_CASES,
        },

        # ------------------------------------------------------------ §8
        "design": {
            "arms": list(C.ARMS),
            "optional_arms": list(C.OPTIONAL_ARMS),
            "cells_by_arm": dict(C.N_CELLS_BY_ARM),
            "cells_full": C.N_CELLS_FULL,
            "cell_set_is": "derived from the admitted arm set; there is no "
                           "named variant table (§8.1)",
            "registered_slot_order": list(C.REGISTERED_SLOT_ORDER),
            "configurations": list(C.CONFIGURATIONS),
            "order_is": "a cell-level factor (§8.4)",
            "wording_allocation": "w(c1) = i mod 4; w(c2) = (i + floor(i/4)) "
                                  "mod 4; solo uses i mod 4",
            "blocks": C.N_BLOCKS, "M": C.M_DRAWS, "M_cal": C.M_CAL,
            "prompt_template": {"zero": C.PROMPT_ZERO, "one": C.PROMPT_ONE,
                                "two": C.PROMPT_TWO},
            "stem_sentence": C.STEM_SENTENCE,
            # §34 D1's four options, each as the arm set and the scale it
            # runs, so the manifest binds what the budget IS rather than a
            # label for it. The near-form arm is essential under D18's
            # closure, which is why the 47-cell option is not a cheaper
            # version of the same study.
            "d1_options": {
                name: {"arms": list(arms),
                       "cells_per_block": cells.n_cells_for(arms),
                       **cells.D1_SCALE[name]}
                for name, arms in cells.D1_ARM_SETS.items()},
            "d1_value": decisions.value_of("D1"),
            # The adopted budget, computed from the constants above rather
            # than quoted from the decision packet: a number the manifest
            # carries and the code cannot reproduce is a number nobody can
            # check. `registered_budget` names every term and its driver.
            "d1_registered": budget.registered_budget(),
        },

        # ----------------------------------------------------------- §13
        "selection_rules": {
            "difficulty_coordinate": {
                "primary": C.DIFFICULTY_COORDINATE,
                "formula": "(solo - kappa) / (1 - kappa)",
                "secondary": C.SECONDARY_DIFFICULTY_COORDINATE,
                "degeneracy_ceiling": C.CHANCE_DEGENERACY_MAX,
                "evaluated": "last, in §13.1's lexicographic order",
            },
            "prescreen_retention_band": list(C.PRESCREEN_RETENTION_BAND),
            "prescreen_caliper": None,
            "prescreen_caliper_note":
                "§12.2 deletes v4r4's pre-screen distance caliper: the two "
                "stages' iota estimates disagree by a median of 0.071",
            "expansion": {"max_rounds": C.EXPANSION_MAX_ROUNDS,
                          "max_rungs_per_family_per_round":
                              C.EXPANSION_MAX_RUNGS_PER_FAMILY_PER_ROUND,
                          "source": "the frozen reserve of §7.10"},
            "coverage_conditions": list(C.COVERAGE_CONDITIONS),
            "coverage_decisive": list(C.COVERAGE_DECISIVE),
            "reference_caliper": C.REFERENCE_CALIPER,
            "secondary_coordinate_caliper": C.SECONDARY_COORDINATE_CALIPER,
            "spectrum": {"band": list(C.SPECTRUM_ELIGIBILITY_BAND),
                         "offset": C.SPECTRUM_OFFSET,
                         "per_family": C.N_SPECTRUM_PER_FAMILY,
                         "drawn_from": "the admitted core reference's own "
                                       "family (§13.12)"},
            "near_form": {"n": C.N_NEAR_FORM_CONTROLS, "tier": 2},
            "broad_class": {"caliper": C.CLASS_MATCH_CALIPER,
                            "class": "budget", "tier": 3},
            "backups": {"n_families": C.N_BACKUP_FAMILIES,
                        "may_substitute_after_gate_4":
                            C.BACKUPS_MAY_SUBSTITUTE_AFTER_GATE_4},
        },
        "validity_rule": {
            "components": list(C.VALIDITY_COMPONENTS),
            "combination": "conjunction; the order decides the recorded "
                           "reason and never the verdict",
            "composite_score": False,
            "headroom_band": list(C.HEADROOM_BAND),
            "instruction_lift_min": C.INSTRUCTION_LIFT_MIN,
            "reference_vacuity_max": C.REFERENCE_VACUITY_MAX,
            "chance_max": C.CHANCE_MAX,
            "chance_wilson_upper_max": C.CHANCE_WILSON_UPPER_MAX,
        },
        "interaction_rule": {
            "quantity": "kappa(R|B): P(R passes | B alone at m*, R absent)",
            "measured_on": "load-one B cells; R must be absent (§9.1)",
            "projected_compliance_band": list(C.PROJECTED_COMPLIANCE_BAND),
            "projection_error_allowance": C.PROJECTION_ERROR_ALLOWANCE,
            "displacement_max": C.DISPLACEMENT_MAX,
            "costs": "no additional generation",
        },
        "stability_rule": {
            "splits": list(C.TOPIC_SETS[1:3]),
            "equivalence_bound": C.STABILITY_EQUIVALENCE_BOUND,
            "bootstrap_resamples": C.STABILITY_BOOTSTRAP_RESAMPLES,
            "form": "an equivalence bound on the interval, not a threshold "
                    "on the point difference",
            "population": "§34 D16",
            "population_value": decisions.value_of("D16"),
        },
        "support_requirements": {
            "min_below": C.SUPPORT_MIN_BELOW, "min_above": C.SUPPORT_MIN_ABOVE,
            "min_families_per_side": C.SUPPORT_MIN_FAMILIES_PER_SIDE,
            "bootstrap_share_min": C.SUPPORT_BOOTSTRAP_SHARE_MIN,
            "min_qualified_families": C.MIN_QUALIFIED_FAMILIES,
            "min_structurally_eligible_tier12_families":
                C.MIN_STRUCTURALLY_ELIGIBLE_TIER12_FAMILIES,
            "n_core_references": C.N_CORE_REFERENCES,
            "min_tier1_core": C.MIN_TIER1_CORE,
            "n_core_feature_groups": C.N_CORE_FEATURE_GROUPS,
            "min_core_discourse_roles": C.MIN_CORE_DISCOURSE_ROLES,
            "status_when_unmet": "REFERENCE_SUPPORT_NOT_IDENTIFIED",
            "status_when_unmet_is_terminal": "§34 D6",
            "status_when_unmet_is_terminal_value": decisions.value_of("D6"),
            # D6 closed at `identification_status`: the replication continues
            # and the reference-dependent estimands are NOT_IDENTIFIED,
            # irreversibly. The affected set is bound here so a reader of the
            # signed manifest can see exactly which numbers a failed §13.15
            # costs, before any replication runs.
            "non_identification": identification.identification_payload(),
        },

        # ----------------------------------------------------------- §18
        "lifecycle": {
            "stages": list(C.STAGE_SEQUENCE),
            "generation_stages": list(C.GENERATION_STAGES),
            "terminal_statuses": list(C.TERMINAL_STATUSES),
            # A15. §18 stage 1's readiness vocabulary, disjoint from §28's
            # terminal one. Every entry names outstanding researcher work,
            # so a readiness verdict is a refusal the researcher can act on
            # and attempt again --- it writes no §28.3 record and disables
            # nothing. Every status above it stays as irreversible as it was.
            "readiness_refusal_statuses":
                list(C.READINESS_REFUSAL_STATUSES),
            "readiness_refusal_is_not_terminal":
                "a §18 stage-1 readiness verdict states that this STUDY is "
                "not yet ready to be signed; it carries no evidence about the "
                "replication it was attempted on and does not end it",
            # The registered *vocabulary*. Which statuses a replication
            # realises is model-adaptive and lives on its Gate 3C record;
            # the key is named so the two can never be confused.
            "identification_status_vocabulary":
                list(C.IDENTIFICATION_STATUSES),
            "verifier_bound_entry_points":
                list(C.VERIFIER_BOUND_ENTRY_POINTS),
            "artifact_types": list(C.ARTIFACT_TYPES),
            "stage_artifact_type": dict(C.STAGE_ARTIFACT_TYPE),
            "interpretation": "interaction-aware during development, "
                              "interaction-blind during confirmatory "
                              "selection",
        },

        # ------------------------------------------------------ §11, §15
        "estimands": {
            "D": "P(c passes alone) - P(c passes composed with g)",
            "Delta_j": "D(B<-A) - D(B<-R_j)",
            "Delta_R": "D(B<-A) - mean_j D(B<-R_j)",
            "Lambda": "D(B<-A) - D(A<-B)",
            "Xi": "§11.7's reciprocal gate",
            "delta_difficulty": "D(B<-A) minus the §11.8 prediction at iota_A",
            "Delta_near": "D(B<-A) - mean_k D(B<-N_k)",
            "Delta_broad": "D(B<-A) - D(B<-CL)",
            "difficulty_relation":
                "Y_fs = alpha_f + beta*d_fs, three family intercepts and one "
                "common slope, OLS on nine equally weighted points",
            # open_items U2, resolved at A2. §11.8 wrote alpha_f over
            # `families` and never said which families the twelve points
            # span; giving each near-form control its own intercept makes the
            # tier indicator exactly collinear with their sum. The adopted
            # reading names the three CORE families, so the fit is 5
            # parameters over 12 points and full rank, and gamma_tier means
            # one thing rather than whichever thing a pseudoinverse returned.
            "tier_indicator_secondary": {
                "formulation": spectrum.adopted_formulation(),
                "model": "Y_fs = alpha_f + beta*d_fs + gamma*1[Tier 2] over "
                         "twelve points; alpha_f ranges over the THREE CORE "
                         "families and a Tier-2 point sits at the unweighted "
                         "mean core intercept plus gamma",
                "gamma_tier": "the Tier-2 offset from the difficulty line the "
                              "three core families define, at equal weight "
                              "over them",
                "identified_by": "the near-form arm; without it the indicator "
                                 "does not vary, gamma is not identified and "
                                 "the status is NEAR_FORM_ARM_NOT_AVAILABLE",
                "tier": "secondary; gamma_tier licenses no claim level and "
                        "F8 is a secondary family",
                "estimated_from": "three Tier-2 points against nine Tier-1 "
                                  "points, so it is low precision whatever "
                                  "the parameterisation and is read as a "
                                  "diagnostic",
                "assumption": "the three core families' levels are equally "
                              "weighted in defining the reference line, which "
                              "is the same convention §11.8's prediction at "
                              "iota_A already uses",
                "non_adopted": ["A1", "A3", "A4"],
                "why_not": {
                    "A1": "exactly singular; gamma has no unique "
                          "least-squares value. Never constructed",
                    "A3": "identified, but it deletes gamma_tier, a "
                          "registered F8 member --- a §32 amendment to §15 "
                          "for no gain. Never constructed",
                    "A4": "identified, but a pooled intercept leaves "
                          "between-family level differences nowhere to go but "
                          "beta, which the primary form removes deliberately. "
                          "Constructed, non-adopted, and refused on any "
                          "reporting path",
                },
                "decision_packet":
                    "dci1/reports/dci1v7/u2_tier_model_decision.md",
            },
        },
        "order_estimands": {
            "family": "F11",
            "members": list(C.FAMILY_MEMBERS["F11"]),
            "cross_configuration": True,
            "dependence": "Ord_Lambda = Ord_B - Ord_A exactly, declared "
                          "rather than hidden (§11.7)",
        },
        "multiplicity_families": {
            name: {"members": list(members), "n": len(members),
                   "tier": ("primary" if name in C.PRIMARY_TIER_FAMILIES
                            else "secondary")}
            for name, members in C.FAMILY_MEMBERS.items()},
        "claim_ladder": {
            "levels": list(C.CLAIM_LEVELS),
            "withheld": list(C.WITHHELD_CLAIM_LEVELS),
            "l4a": "per named member (§17.7)",
            "l3c_near_form_precondition": "§34 D18",
            "l3c_near_form_precondition_value": decisions.value_of("D18"),
            # D18 closed at `precondition`: L3c carries a scope and the
            # strong scope --- the memo's refutation verdict --- requires the
            # near-form arm to have run.
            "l3c_scopes": list(C.L3C_SCOPES),
            "l3c_strong_sentence": C.L3C_STRONG_SENTENCE,
            "l3c_same_form_only_sentence": C.L3C_SAME_FORM_ONLY_SENTENCE,
            "l3c_strong_requires_near_form_arm": True,
            "reference_pool_sentence": C.REFERENCE_POOL_SAME_FORM_SENTENCE,
            "class_sentence": C.CLASS_SENTENCE,
            "l3c_without_near_form_sentence":
                C.L3C_WITHOUT_NEAR_FORM_SENTENCE,
        },
        "masking": {
            "namespaces": list(C.MASK_NAMESPACES),
            "min_differing_fraction": C.MASK_MIN_DIFFERING_FRACTION,
            "unmask": "once, bound to the sealed masked artifact and to the "
                      "analysis code hash (§20)",
        },
        "freeze_requirements": {
            "section": "§18.1",
            "empty_field_rule": "a field a variant legitimately leaves empty "
                                "is declared empty with the identification "
                                "status that explains it",
            "post_freeze": "no scientific rule changes after the freeze",
        },
        "measurement_basis": {
            "value": C.MEASUREMENT_BASIS,
            "refused": list(C.MEASUREMENT_BASES_REFUSED),
            "scope_sentence": C.SCOPE_SENTENCE,
            "permanent": True,
        },
        "thresholds": {
            "delta_r_generic": C.DELTA_R_GENERIC_THRESHOLD,
            "delta_r_pair_specific": C.DELTA_R_PAIR_SPECIFIC_THRESHOLD,
            "sesoi": C.SMALLEST_EFFECT_OF_INTEREST,
            "equivalence_region": C.EQUIVALENCE_REGION,
            "delta_near": dict(C.DELTA_NEAR_THRESHOLDS),
            "delta_broad": dict(C.DELTA_BROAD_THRESHOLDS),
            "delta_difficulty": dict(C.DELTA_DIFFICULTY_THRESHOLDS),
            "order": dict(C.ORDER_THRESHOLDS),
            "composed_headroom_band": list(C.COMPOSED_PROXIMITY_BAND),
            # §34 D17. Every other entry in this block is a number, and this
            # one has to be too: `thresholds` is where a reader looks to see
            # what value refuses what, and naming the *branch* --- "floor" ---
            # while leaving the threshold in another file makes the one rule
            # D17 registers the only one not readable here. The record still
            # owns it; this is the same values, bound in the payload that
            # carries every other threshold.
            "construct_floor": {
                "decision": "§34 D17",
                "branch": decisions.value_of("D17"),
                **({} if construct_strength.registered_floor() is None
                   else construct_strength.registered_floor().as_dict()),
                "measured_on": "the load-zero calibration cells --- NOT every "
                               "row where the severity was absent, which in "
                               "§12.3's focal grid includes the B-solo cells "
                               "at the other severities",
                "failure_status": "FOCAL_RANGE_EXHAUSTED",
                "marginal_status": construct_strength.MARGINAL_STATUS,
                "evidence_class": "DEVELOPMENT_EVIDENCE (§30): fitted to four "
                                  "models of one predecessor study on one "
                                  "task",
            },
        },
        "precision_preconditions": dict(C.PRECISION_PRECONDITIONS),
        "reuse_ledger": {
            "classifications": list(C.REUSE_CLASSIFICATIONS),
            "declaration": "historical v4r4 outcomes informed the DESIGN of "
                           "v5's matching rules; no v5 B+R outcome selects, "
                           "replaces, widens, adds, repairs or alters "
                           "anything (§30)",
        },
    }
    missing = [k for k in REQUIRED_BINDINGS if k not in manifest]
    if missing:
        raise ProtocolError(
            f"the registration manifest is missing required binding(s) "
            f"{missing}; REQUIRED_BINDINGS is what §34 and §18.1 ask it to "
            "carry and the builder must produce every one")
    if supersedes:
        # Folded in *before* the hash. ``sign_registration`` used to attach it
        # afterwards and rehash, which made a superseded manifest something
        # ``build_manifest`` could not reproduce --- and reproducibility from
        # the producing commit is exactly what ``ensure_registration`` checks
        # when the second replication registers.
        manifest["supersedes"] = supersedes
    assert_no_model_adaptive_values(manifest)
    manifest["manifest_hash"] = sha_obj(manifest)
    return manifest


def assert_no_model_adaptive_values(manifest: Mapping[str, Any]) -> None:
    """§6.1: a model-adaptive value never appears in a study-wide rule."""
    found: list[str] = []

    def walk(node: Any, path: str) -> None:
        if isinstance(node, Mapping):
            for key, value in node.items():
                if key in MODEL_ADAPTIVE_KEYS:
                    found.append(f"{path}.{key}")
                walk(value, f"{path}.{key}")
        elif isinstance(node, (list, tuple)):
            for index, value in enumerate(node):
                walk(value, f"{path}[{index}]")

    walk(manifest, "manifest")
    if found:
        raise ProtocolError(
            f"the registration manifest carries model-adaptive value(s) "
            f"{found}; those reach the code only through the per-model "
            "records (§6.1)")


def sign_registration(context: StudyContext, *, producing_commit: str,
                      adoption: Mapping[str, Any],
                      bank: TopicBank | None = None,
                      repo_root: Path | str = ".",
                      supersedes: str | None = None) -> dict[str, Any]:
    """Write and sign the manifest, once.

    ``assert_signable`` runs first and before any file is created, so a
    refused registration leaves no directory, no key and no partial artifact
    behind that a later run could mistake for a registration. It refused for
    as long as anything on ``signing_blockers``'s list was outstanding, and
    what changed on 2026-08-26 is that the researcher did the work each
    blocker names --- not that any of them stopped looking.
    """
    bank = bank if bank is not None else load_bank()
    assert_signable(bank, where="sign_registration",
                    repo_root=repo_root)
    manifest = build_manifest(context, producing_commit=producing_commit,
                              adoption=adoption, bank=bank,
                              repo_root=repo_root, supersedes=supersedes)
    context.signing_key_path.parent.mkdir(parents=True, exist_ok=True)
    if not context.signing_key_path.exists():
        create_signing_key(context.signing_key_path)
    context.registration_root.mkdir(parents=True, exist_ok=True)
    fs.write_json_once(context.registration_manifest,
                       sign_payload(manifest, context.signing_key_path))
    durable = (Path(context.durable_root) / STUDY_ID
               / context.registration_root.name)
    store.replicate(context.registration_root, durable)
    store.assert_replicated(context.registration_root, durable)
    return manifest


#: v7 §32: where post-registration amendments live, beside the manifest.
AMENDMENTS_DIRNAME = "amendments"
#: What an amendment may declare about itself relative to the criterion it
#: touches. `loosening` is the one §32.1 scrutinises, and the record carries
#: the argument for why the loosening is adoptable, not just the word.
AMENDMENT_DIRECTIONS = ("tightening", "loosening", "neutral")


def amendment_records(context: StudyContext) -> list[dict[str, Any]]:
    """Every signed amendment record in this study, in sequence order.

    Signatures are verified on read; a record that does not verify is an
    ``IntegrityError`` and not a skipped file, because the chain is what the
    freeze binds and a hole in it is a hole in the provenance.
    """
    root = Path(context.registration_root) / AMENDMENTS_DIRNAME
    if not root.is_dir():
        return []
    out: list[tuple[int, dict[str, Any]]] = []
    for path in sorted(root.glob("*.json")):
        payload = verify_signed(fs.read_json(path), context.signing_key_path,
                                where=f"amendment record {path.name}")
        out.append((int(payload["sequence"]), payload))
    out.sort(key=lambda pair: pair[0])
    expected = list(range(1, len(out) + 1))
    if [seq for seq, _ in out] != expected:
        raise IntegrityError(
            f"the amendment chain under {root} is not contiguous: "
            f"{[seq for seq, _ in out]}; an append-only register has no gaps")
    return [payload for _, payload in out]


def document_binding(context: StudyContext,
                     registration: Mapping[str, Any]) -> dict[str, Any]:
    """The document hashes in force: the registration's, as amended.

    Starts from the hashes the registration bound and applies every signed
    amendment in sequence, refusing a link whose ``before`` is not the chain
    head it claims to extend. The result is what the pre-freeze audit
    compares the on-disk documents against and what the freeze binds --- so
    an amended document is *legal* exactly when the chain says how it came
    to differ from the registered one, and *illegal* otherwise, which is
    what §32 asks and what v6's lifecycle could not express.
    """
    current = {"protocol_hash": registration.get("protocol_hash"),
               "reference_design_spec_hash":
                   registration.get("reference_design_spec_hash")}
    applied: list[dict[str, Any]] = []
    for record in amendment_records(context):
        before = record.get("before") or {}
        if any(before.get(k) != v for k, v in current.items()):
            raise IntegrityError(
                f"amendment {record.get('amendment_id')!r} (sequence "
                f"{record.get('sequence')}) claims to amend document hashes "
                f"{before} and the chain head is {current}; a link that does "
                "not extend the head is not part of the chain")
        current = dict(record["after"])
        applied.append({"amendment_id": record.get("amendment_id"),
                        "sequence": record.get("sequence"),
                        "record_hash": record.get("record_hash"),
                        "direction": record.get("direction"),
                        "adopted_on": record.get("adopted_on")})
    return {**current, "amendments": applied,
            "registered": {"protocol_hash": registration.get("protocol_hash"),
                           "reference_design_spec_hash":
                               registration.get("reference_design_spec_hash")}}


def latest_supersession(context: StudyContext) -> dict[str, Any] | None:
    """The most recent §32 supersession in this study, or ``None``.

    Read from ``registration/superseded/<hash>/supersession.json`` rather than
    from any in-memory state, because the replacement is signed by a separate
    command --- often a separate process --- from the one that superseded.
    """
    root = Path(context.registration_root) / "superseded"
    if not root.is_dir():
        return None
    records = []
    for entry in root.iterdir():
        record = entry / "supersession.json"
        if record.is_file():
            body = json.loads(record.read_text())
            records.append(body.get("payload", body))
    if not records:
        return None
    return max(records, key=lambda r: str(r.get("superseded_at", "")))


def assert_links_supersession(context: StudyContext,
                              supersedes: str | None) -> None:
    """A replacement manifest has to say what it replaces.

    ``build_manifest`` folds ``supersedes`` in before the hash, so the chain is
    readable from the payload alone --- that is the property this protects.
    ``run_registration`` took the argument and the command line did not pass
    it, so a registration signed through the documented entry point after a
    supersession was silently unlinked: the supersession record was already on
    disk, naming the manifest being replaced, and the replacement did not
    mention it. For a command family whose contract is that every command
    refuses before it does anything, dropping the one field that makes the
    chain self-describing is a fail-open, and nothing else recomputes it.

    The genesis registration has nothing to link and is unaffected.
    """
    record = latest_supersession(context)
    if record is None:
        return
    expected = record.get("superseded_manifest_hash")
    if not expected:                                        # pragma: no cover
        return
    if supersedes == expected:
        return
    raise IntegrityError(
        f"§32: this study has a supersession record retiring manifest "
        f"{expected}, and the replacement being signed "
        f"{'names ' + str(supersedes) if supersedes else 'names nothing'}. A "
        "replacement that does not carry `supersedes` is not readable as part "
        "of the chain from its own payload; pass the retired hash (the CLI "
        "flag is `--supersedes`) rather than signing an unlinked manifest")


def ensure_registration(context: StudyContext, *, producing_commit: str,
                        adoption: Mapping[str, Any],
                        bank: TopicBank | None = None,
                        repo_root: Path | str = ".",
                        supersedes: str | None = None) -> dict[str, Any]:
    """The study-level manifest: signed by the first replication, verified by
    the rest.

    §6.1 fixes every study-wide rule **before the first qualification**, so
    there is one manifest for the whole study --- but §18's stage record that
    binds it is *per model*, because ``assert_predecessor_passed`` reads the
    replication's own tree. Stage 1 therefore runs four times and must sign
    exactly once.

    It signed every time until the pre-data engineering amendment, and
    ``write_json_once`` then refused the second replication --- so
    ``gemma-3n-e4b-it``, ``qwen3-4b`` and ``qwen3-4b-instruct-2507`` could
    never obtain a stage-1 record and could never legally enter ``QUALIFIED``.
    Nothing caught it because the integration harness walks one model.

    Verification here is not a formality. The existing manifest is
    signature-checked, **rebuilt from the current code** and compared by hash,
    and its producing commit must be the one this replication is registering
    under. A second replication registering against a manifest the running
    code no longer reproduces, or from a different commit, is not the same
    registration and is refused rather than recorded.
    """
    bank = bank if bank is not None else load_bank()
    path = Path(context.registration_manifest)
    if not path.exists():
        assert_links_supersession(context, supersedes)
        return sign_registration(context, producing_commit=producing_commit,
                                 adoption=adoption, bank=bank,
                                 repo_root=repo_root, supersedes=supersedes)
    assert_signable(bank, where="ensure_registration",
                    repo_root=repo_root)
    existing = load_manifest(context)
    if existing["producing_commit"] != producing_commit:
        raise IntegrityError(
            f"the signed registration was produced at "
            f"{existing['producing_commit']} and this replication is "
            f"registering at {producing_commit}. Every replication in a study "
            "registers under one commit; a different one is a different "
            "registration and needs §32's supersession, not a second record")
    rebuilt = build_manifest(context,
                             producing_commit=existing["producing_commit"],
                             adoption=existing["adoption"], bank=bank,
                             repo_root=repo_root,
                             supersedes=existing.get("supersedes"))
    if rebuilt["manifest_hash"] != existing["manifest_hash"]:
        raise IntegrityError(
            f"the signed registration manifest "
            f"{existing['manifest_hash']} is not what this code now builds "
            f"({rebuilt['manifest_hash']}); the study-wide rules moved after "
            "registration, and a replication may not register against a "
            "manifest its own code no longer reproduces")
    return existing


def load_manifest(context: StudyContext) -> dict[str, Any]:
    """Read and verify the signed manifest. Fails closed when it is absent."""
    path = Path(context.registration_manifest)
    if not path.exists():
        raise IntegrityError(
            f"the signed v5 registration manifest is missing at {path}. §6.1 "
            "fixes every study-wide rule in it BEFORE the first "
            "qualification, so no replication may be qualified without it")
    payload = verify_signed(fs.read_json(path), context.signing_key_path,
                            where="v5 registration manifest")
    if payload.get("study_id") != context.study_id:
        raise IntegrityError(
            "the registration manifest belongs to another study")
    return payload
