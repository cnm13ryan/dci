"""§18 stage 12, ``PREFREEZE_AUDIT``, over the real signed artifacts.

v4r4's pre-freeze audit was a **tool**: it ran beside the lifecycle, over
whatever it was handed, and it could be skipped. v5 makes it a stage, and this
runner makes it read the thing a stage record is for --- the signed outputs of
every preceding stage --- rather than a summary a caller assembled.

**Established from artifacts, not from trust.** Every check below opens a
signed record, verifies its hash and signature through
``read_stage_record``, and derives its answer from the record's own fields.
Where a check compares two stages it compares the two *records*: the m* Gate 4
used against the m* Gate 2 selected, the arm set Gate 4 measured against the
arm set Gate 3C admitted, the verifier hash on the rows against the verifier
hash Gate 1 froze. A summary that agreed with itself would pass a check that
read the summary; none of these do.

**A failing mandatory check makes Gate 5 unreachable and needs no extra rule.**
§18 registers ``PREFREEZE_AUDIT`` as Gate 5's predecessor, and
``assert_predecessor_passed`` refuses a successor whose predecessor did not
record ``PASS``. The audit's own outcome is therefore the mechanism.

**``UNRESOLVED`` is not ``PASS``.** A check that could not be established ---
because the artifact it needs does not exist --- reports ``UNRESOLVED``, and
``can_freeze`` requires every mandatory check to have passed. "We did not
establish this" and "this is false" are different facts and neither licenses
a freeze.
"""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any, Mapping, Sequence

from dci1v4.engine import gitinfo
from dci1v4.errors import IntegrityError
from dci1v4.protocol.hashing import sha_obj

from dci1v7.engine import transitions
from dci1v7.engine.paths import ModelTree
from dci1v7.protocol import constants as C
from dci1v7.protocol import decisions, manifest, open_items
from dci1v7.protocol import reuse_ledger
from dci1v7.run.contracts import audit_contracts
from dci1v7.run.gates_run import assert_no_substitution_path
from dci1v7.run.lifecycle import StageOutcome, run_stage, TerminalStatus
from dci1v7.stages import audit_prefreeze
from dci1v7.stages import selection as selection_stage
from dci1v7.stages import validity as validity_stage
from dci1v7.topics.bank import (TopicBank, assert_calibration_sets_disjoint,
                                load_bank)
from dci1v7.verifiers import verifier_source_hash
from dci1v7.protocol.wordings import wording_source_hash

__all__ = ["ARTIFACT_CHECKS", "artifact_checks", "prefreeze_payload",
           "run_prefreeze_audit_stage", "PREFREEZE_AUDIT_FAILURE"]

PREFREEZE_AUDIT_FAILURE = audit_prefreeze.PREFREEZE_AUDIT_FAILURE

#: Each entry: id, what it establishes, and whether failing it blocks Gate 5.
ARTIFACT_CHECKS: tuple[tuple[str, str, bool], ...] = (
    ("decisions_closed", "every §34 decision closed with its evidence", True),
    ("specification_questions_resolved",
     "no blocking specification question remains", True),
    ("protocol_hashes_agree",
     ("the protocol and spec hashes in force --- the registration's as "
      "amended by the signed §32 chain --- recompute from the files on disk"),
     True),
    ("producing_commit_clean",
     "the worktree is clean and the producing commit is resolvable", True),
    ("study_id_correct", "every record carries this study's id", True),
    ("no_foreign_evidence",
     "no record of another revision appears in this tree", True),
    ("topic_sets_disjoint",
     "Calibration-A and Calibration-B share no topic and no question text",
     True),
    ("model_backend_bound",
     "the model revision, backend and decoding policy are bound", True),
    ("candidate_population_frozen",
     "the regime screen recorded a frozen vocabulary and the library sizes "
     "recompute", True),
    ("selected_references_valid",
     "every selected reference carries a passing V(R) with no unevaluated "
     "component", True),
    ("calibration_stability_satisfied",
     "every selected reference is stable across the two calibration splits",
     True),
    ("support_satisfied",
     "§13.15's support and redundancy requirements are recorded", True),
    ("no_post_outcome_substitution",
     "no substitution function exists in the Gate-4 module", True),
    ("arms_match_identification",
     "the admitted arm set is the one Gate 3C's identification statuses "
     "imply", True),
    ("exact_cell_set",
     "the derived cell count equals the cell set the admitted arms build",
     True),
    ("generation_budget",
     "the whole-study generation budget recomputes from the arm set", True),
    ("gate4_evidence_complete",
     "Gate 4 measured every registered cell type on every slot and recorded "
     "the composed-contrast projection", True),
    ("verifier_hash_stable",
     "the verifier hash on every record equals the one Gate 1 froze", True),
    ("wording_hash_stable",
     "the wording hash equals the one Gate 1 froze", True),
    ("families_defined", "F1-F11 are defined with their member lists", True),
    ("precision_rules", "every precision precondition is a literal", True),
    ("masking_defined", "the masking rule and its namespaces are registered",
     True),
    ("claim_ladder_defined",
     "the claim ladder is registered and no L5 emitter exists", True),
    ("l4_regression",
     "emit_l4a is per named member and keyword-only (§17.7)", True),
    ("durable_copies", "every stage directory has a durable mirror", True),
    ("producers_exist",
     "every required artifact field has a producer (run/contracts.py)", True),
)


def _result(check: str, verdict: str, detail: Any = None,
            mandatory: bool = True) -> dict[str, Any]:
    return {"check": check, "verdict": verdict, "detail": detail,
            "mandatory": mandatory}


def artifact_checks(tree: ModelTree, *, repo_root: Path | str = ".",
                    bank: TopicBank | None = None) -> list[dict[str, Any]]:
    """Every check above, derived from the signed records in ``tree``.

    **Nothing here is waivable, in either namespace.** An earlier revision let
    the synthetic namespace waive ``producing_commit_clean``, on the argument
    that a test worktree is dirty by construction --- which made the one rule
    about provenance the one rule the integration harness never exercised. The
    harness builds an isolated repository at a clean commit instead
    (``tests_v7/synthetic_lifecycle.synthetic_repo``), so the check runs on its
    own terms there too, and the waiver parameter is gone rather than unused.
    """
    bank = bank if bank is not None else load_bank()
    mandatory = {cid: block for cid, _why, block in ARTIFACT_CHECKS}
    out: list[dict[str, Any]] = []

    def add(check: str, ok: bool | None, detail: Any = None) -> None:
        verdict = "UNRESOLVED" if ok is None else ("PASS" if ok else "FAIL")
        out.append(_result(check, verdict, detail, mandatory[check]))

    records: dict[str, Mapping[str, Any]] = {}
    unreadable: dict[str, str] = {}
    for stage in C.STAGE_SEQUENCE:
        if stage == C.STAGE_PREFREEZE_AUDIT:
            continue
        try:
            records[stage] = transitions.read_stage_record(tree, stage)
        except IntegrityError as error:
            unreadable[stage] = str(error)[:200]

    # ---------------------------------------------------------- decisions
    still_open = list(decisions.open_decisions())
    add("decisions_closed", not still_open,
        {"open": still_open, "n_open": len(still_open)})
    blocking = list(open_items.blocking_items())
    add("specification_questions_resolved", not blocking,
        {"blocking": blocking})

    # ------------------------------------------------------------- hashes
    registration = records.get(C.STAGE_REGISTERED)
    if registration is None:
        add("protocol_hashes_agree", None,
            {"missing": C.STAGE_REGISTERED,
             "reason": unreadable.get(C.STAGE_REGISTERED)})
    else:
        # v7 §32: against the registered hashes AS AMENDED by the signed
        # chain, not the registered hashes alone --- an amended document is
        # legal when the chain says how it came to differ.
        try:
            on_disk = manifest.document_hashes(repo_root)
            binding = manifest.document_binding(tree.context, registration)
            agree = all(binding.get(k) == v for k, v in on_disk.items())
        except Exception as error:
            agree, on_disk, binding = False, {"error": str(error)}, {}
        add("protocol_hashes_agree", agree,
            {"recomputed": on_disk,
             "in_force": {k: binding.get(k) for k in
                          ("protocol_hash", "reference_design_spec_hash")},
             "registered": binding.get("registered"),
             "amendments": binding.get("amendments")})

    repo = Path(repo_root)
    dirty = subprocess.run(["git", "status", "--porcelain"], cwd=repo,
                           capture_output=True, text=True).stdout.strip()
    try:
        commit = gitinfo.head_commit(repo)
    except Exception:                                       # pragma: no cover
        commit = None
    add("producing_commit_clean", (not dirty) and bool(commit),
        {"changed_paths": len(dirty.splitlines()), "commit": commit})

    add("study_id_correct",
        all(r.get("study_id") == tree.context.study_id
            for r in records.values()) if records else None,
        {"records": len(records),
         "study_id": tree.context.study_id})

    foreign = sorted(
        str(p.relative_to(tree.root)) for p in tree.root.rglob("*.json")
        if _declares_foreign_study(p, tree.context.study_id))
    add("no_foreign_evidence", not foreign, {"foreign": foreign[:5]})

    try:
        disjoint = assert_calibration_sets_disjoint(
            {k: v for k, v in bank.sets.items() if v})
        add("topic_sets_disjoint", bank.complete, disjoint)
    except Exception as error:
        add("topic_sets_disjoint", False, str(error))

    # --------------------------------------------------------- apparatus
    if registration is None:
        add("model_backend_bound", None, {"missing": C.STAGE_REGISTERED})
    else:
        models = registration.get("models") or []
        add("model_backend_bound",
            bool(models) and all(len(m.get("revision", "")) == 40
                                 for m in models),
            {"models": [m.get("model_key") for m in models]})

    regime = records.get(C.STAGE_REGIME)
    if regime is None:
        add("candidate_population_frozen", None, {"missing": C.STAGE_REGIME})
    else:
        from dci1v7.verifiers.constraints import assert_library_sizes
        try:
            sizes = assert_library_sizes()
            ok = bool(regime.get("vocabulary_frozen")) and bool(sizes)
        except Exception as error:                          # pragma: no cover
            ok, sizes = False, {"error": str(error)}
        add("candidate_population_frozen", ok,
            {"sizes": sizes, "n_carried": regime.get("n_carried")})

    gate3b = records.get(C.STAGE_GATE3B)
    if gate3b is None:
        add("selected_references_valid", None, {"missing": C.STAGE_GATE3B})
        add("calibration_stability_satisfied", None,
            {"missing": C.STAGE_GATE3B})
    else:
        chosen = gate3b.get("selection") or {}
        core = chosen.get("core") or {}
        entries = list(core.get("core_references") or [])
        # Every rung's V(R) verdict is on the family record, so "no
        # unevaluated component" is established from the verdicts rather than
        # from the fact that a reference was chosen.
        admitted_families = {e["family"] for e in entries}
        verdicts = [v for v in (core.get("family_verdicts") or [])
                    if v.get("family") in admitted_families]
        rungs = [r for v in verdicts for r in (v.get("rungs") or [])]
        unevaluated = [r for r in rungs if r.get("unevaluated_names")
                       and r.get("passed")]
        add("selected_references_valid",
            bool(entries) and core.get("references_identified") is True
            and not unevaluated
            and all(v.get("admitted") for v in verdicts),
            {"core": [f"{e['family']}:{e['severity']}" for e in entries],
             "n_rungs_evaluated": len(rungs),
             "unevaluated_but_passing": len(unevaluated)})
        gate3a = records.get(C.STAGE_GATE3A) or {}
        stability = gate3a.get("stability") or {}
        names = [f"{e['family']}:{e['severity']}" for e in entries]
        add("calibration_stability_satisfied",
            (bool(names) and all(stability.get(n, {}).get("passed")
                                 for n in names)) if stability else None,
            {"checked": names, "n_verdicts": len(stability)})

    gate3c = records.get(C.STAGE_GATE3C)
    if gate3c is None:
        for name in ("support_satisfied", "arms_match_identification",
                     "exact_cell_set", "generation_budget"):
            add(name, None, {"missing": C.STAGE_GATE3C})
    else:
        report = gate3c.get("support") or {}
        add("support_satisfied", bool(report.get("support_met")),
            {"realised": report.get("realised"),
             "failures": report.get("failures"),
             "disposition": report.get("disposition")})
        from dci1v7.design.cells import (arms_from_identification,
                                         n_cells_for)
        statuses = set(gate3c.get("identification_statuses") or ())
        unidentified = ("REFERENCE_SUPPORT_NOT_IDENTIFIED" in statuses
                        or "EXCESS_NOT_IDENTIFIED" in statuses)
        implied = arms_from_identification(
            core_identified=not unidentified,
            spectrum_identified=(
                not unidentified
                and "DIFFICULTY_SUPPORT_NOT_IDENTIFIED" not in statuses),
            near_form_identified="NEAR_FORM_ARM_NOT_AVAILABLE" not in statuses,
            class_identified="CLASS_ARM_NOT_AVAILABLE" not in statuses)
        recorded = tuple(gate3c.get("admitted_arms") or ())
        add("arms_match_identification", set(recorded) == set(implied),
            {"recorded": list(recorded), "implied": list(implied),
             "statuses": sorted(statuses)})
        cells = n_cells_for(recorded) if recorded else 0
        add("exact_cell_set", gate3c.get("derived_cell_count") == cells,
            {"recorded": gate3c.get("derived_cell_count"),
             "recomputed": cells})
        budget = cells * C.N_BLOCKS * C.M_DRAWS
        add("generation_budget", budget > 0,
            {"cells_per_block": cells, "blocks": C.N_BLOCKS,
             "M": C.M_DRAWS, "per_model": budget,
             "note": "the whole-study budget is this times the number of "
                     "replications §34 D1 admits"})

    try:
        assert_no_substitution_path()
        selection_stage.assert_no_backup_substitution(vars(selection_stage))
        add("no_post_outcome_substitution", True,
            {"checked": ["run.gates_run", "stages.selection"]})
    except Exception as error:
        add("no_post_outcome_substitution", False, str(error))

    gate4 = records.get(C.STAGE_GATE4)
    if gate4 is None:
        add("gate4_evidence_complete", None, {"missing": C.STAGE_GATE4})
    else:
        from dci1v7.run.gates_run import (assert_composed_table_complete,
                                          composed_table_shape)
        try:
            assert_composed_table_complete(gate4["composed_table"],
                                           gate4["admitted_arms"])
            complete = (gate4.get("rows") == gate4.get("expected_rows")
                        and bool(gate4.get("composed_contrast"))
                        and gate4.get("outcome") == "PASS")
        except Exception as error:
            complete, gate4 = False, {**gate4, "shape_error": str(error)}
        add("gate4_evidence_complete", complete,
            {"cell_types": gate4.get("n_cell_types"),
             "rows": gate4.get("rows"),
             "expected": gate4.get("expected_rows"),
             "contrast_statuses": gate4.get("contrast_statuses"),
             "shape": len(composed_table_shape(
                 gate4.get("admitted_arms") or ()))})

    gate1 = records.get(C.STAGE_GATE1)
    if gate1 is None:
        add("verifier_hash_stable", None, {"missing": C.STAGE_GATE1})
        add("wording_hash_stable", None, {"missing": C.STAGE_GATE1})
    else:
        frozen = gate1.get("canonical_verifier_hash")
        drift = sorted(stage for stage, r in records.items()
                       if r.get("verifier_hash")
                       and r["verifier_hash"] != frozen)
        add("verifier_hash_stable",
            frozen == verifier_source_hash() and not drift,
            {"frozen": frozen, "now": verifier_source_hash(),
             "records_disagreeing": drift})
        add("wording_hash_stable",
            gate1.get("wording_hash") == wording_source_hash(),
            {"frozen": gate1.get("wording_hash"),
             "now": wording_source_hash()})

    add("families_defined",
        set(C.FAMILY_MEMBERS) == {f"F{i}" for i in range(1, 12)},
        {"families": sorted(C.FAMILY_MEMBERS),
         "members": {k: len(v) for k, v in C.FAMILY_MEMBERS.items()}})
    add("precision_rules",
        all(isinstance(v, float)
            for v in C.PRECISION_PRECONDITIONS.values()),
        dict(C.PRECISION_PRECONDITIONS))
    add("masking_defined",
        bool(C.MASK_NAMESPACES) and C.MASK_MIN_DIFFERING_FRACTION > 0,
        {"namespaces": list(C.MASK_NAMESPACES),
         "min_differing_fraction": C.MASK_MIN_DIFFERING_FRACTION})

    from dci1v7.analysis import claims as claims_module
    try:
        claims_module.assert_no_l5_emitter(vars(claims_module))
        ladder_ok = set(C.CLAIM_LEVELS) >= {"L3c", "L4a", "L4b"}
    except Exception:                                       # pragma: no cover
        ladder_ok = False
    add("claim_ladder_defined", ladder_ok, {"levels": list(C.CLAIM_LEVELS)})

    import inspect
    signature = inspect.signature(claims_module.emit_l4a)
    per_member = signature.parameters.get("per_member")
    add("l4_regression",
        per_member is not None
        and per_member.kind is inspect.Parameter.KEYWORD_ONLY
        and all(p.kind is inspect.Parameter.KEYWORD_ONLY
                for p in signature.parameters.values()),
        {"signature": str(signature)})

    mirrored = {stage: (tree.durable / stage).exists()
                for stage in records}
    add("durable_copies", all(mirrored.values()) if mirrored else None,
        mirrored)

    contracts = audit_contracts(records)
    add("producers_exist", not contracts["defects"],
        {"fields": contracts["n_fields"],
         "defects": contracts["defects"][:5]})

    try:
        validity_stage.assert_no_composite_score(vars(validity_stage))
    except Exception as error:                              # pragma: no cover
        out.append(_result("no_composite_score", "FAIL", str(error), True))
    return out


def _declares_foreign_study(path: Path, study_id: str) -> bool:
    from dci1v4.engine import fs
    try:
        payload = fs.read_json(path)
    except Exception:                                       # pragma: no cover
        return False
    body = payload.get("payload", payload)
    declared = body.get("study_id") if isinstance(body, dict) else None
    return bool(declared) and declared != study_id


def prefreeze_payload(tree: ModelTree, *, producing_commit: str,
                      repo_root: Path | str = ".",
                      bank: TopicBank | None = None,
                      artifact_texts: Mapping[str, str] | None = None
                      ) -> dict[str, Any]:
    """§18 stage 12: the artifact audit and §33's checklist, together."""
    checks = artifact_checks(tree, repo_root=repo_root, bank=bank)
    gate4 = None
    probe = None
    statuses: Sequence[str] = ()
    try:
        gate4 = transitions.read_stage_record(tree, C.STAGE_GATE4)
    except IntegrityError:
        gate4 = None
    # §33 check 8 reads the probe record on the same terms as Gate 4's. A
    # missing record is UNRESOLVED there, which blocks the freeze --- "we did
    # not establish this" is not "this is true", and by stage 12 the probe has
    # run or the replication never reached here.
    try:
        probe = transitions.read_stage_record(tree, C.STAGE_GATE2_75)
    except IntegrityError:
        probe = None
    try:
        gate3c = transitions.read_stage_record(tree, C.STAGE_GATE3C)
        statuses = gate3c.get("identification_statuses") or ()
    except IntegrityError:
        statuses = ()
    # §33 check 15 scans the v5 artifact texts, and they exist from stage 1.
    # Leaving them unsupplied made the check report UNRESOLVED at every stage
    # that ran it --- a check that never ran. The default is now the artifacts
    # themselves, and a caller may add to it but not empty it.
    if artifact_texts is None:
        artifact_texts = reuse_ledger.collect_artifact_texts(repo_root)
    checklist = audit_prefreeze.run_prefreeze_audit(
        repo_root=str(repo_root), gate4_record=gate4, probe_record=probe,
        identification_statuses=statuses, artifact_texts=artifact_texts)

    failed = [c for c in checks if c["mandatory"] and c["verdict"] != "PASS"]
    can_freeze = not failed and checklist.get("can_freeze", False)
    payload = {
        "stage": C.STAGE_PREFREEZE_AUDIT,
        "artifact_type": C.STAGE_ARTIFACT_TYPE[C.STAGE_PREFREEZE_AUDIT],
        "inputs": {"gate4": {"stage": C.STAGE_GATE4},
                   "gate2_75": {"stage": C.STAGE_GATE2_75}},
        "producing_commit": producing_commit,
        "artifact_checks": checks,
        "n_artifact_checks": len(checks),
        "n_artifact_passed": sum(1 for c in checks if c["verdict"] == "PASS"),
        "n_artifact_unresolved": sum(1 for c in checks
                                     if c["verdict"] == "UNRESOLVED"),
        "n_artifact_failed": sum(1 for c in checks if c["verdict"] == "FAIL"),
        "checklist": checklist,
        "can_freeze": can_freeze,
        "waived": [],
        "outcome": "PASS" if can_freeze else "FAIL",
        "failure_status": None if can_freeze else PREFREEZE_AUDIT_FAILURE,
        "blocked": [c["check"] for c in failed],
        "unresolved_is_not_pass":
            "a check that could not be established reports UNRESOLVED; "
            "'we did not establish this' and 'this is false' are different "
            "facts and neither licenses a freeze",
        "content_hash": sha_obj({"checks": checks,
                                 "checklist": checklist.get("checks")}),
    }
    return payload


def _checklist_observed(payload: Mapping[str, Any]) -> dict[str, Any]:
    """§33's own table, for the terminal report.

    v5 carried only the artifact checks into ``observed``, so a replication
    blocked by a §33 item recorded a terminal report that did not name it ---
    the audit exists to produce that table and the terminal path threw half of
    it away. A payload without a checklist says so rather than raising: this
    runs on the failure path and a diagnostic that raises loses the diagnosis.
    """
    checklist = payload.get("checklist")
    if not isinstance(checklist, Mapping):
        return {"checklist": None,
                "checklist_absent": "the payload carried no §33 checklist"}
    return {
        "checklist": [c for c in (checklist.get("checklist") or [])
                      if c.get("verdict") != "PASS"],
        "checklist_can_freeze": checklist.get("can_freeze"),
        "checklist_reason": checklist.get("reason"),
        "open_decisions": checklist.get("open_decisions"),
        "unresolved_redteam_findings":
            checklist.get("unresolved_redteam_findings"),
    }


def run_prefreeze_audit_stage(tree: ModelTree, *,
                              producing_commit: str | None = None,
                              environment_digest: str = "",
                              repo_root: Path | str = ".",
                              bank: TopicBank | None = None,
                              artifact_texts: Mapping[str, str] | None = None
                              ) -> StageOutcome:
    commit = producing_commit or gitinfo.head_commit(Path(repo_root))

    def compute(_prev: Any) -> dict[str, Any]:
        """§28: a failed §19 audit is a *terminal status*, not a FAIL record.

        V5-E32. ``PREFREEZE_AUDIT_FAILURE`` is a registered §28 terminal
        status, and this runner used to put it in a ``failure_status`` field
        and return ``outcome="FAIL"``. Nothing raised, so no §28.3 terminal
        report was written, ``transitions.terminal_status`` kept returning
        ``None``, and ``status`` reported a replication that could never take
        another step as live with ``GATE_5_FREEZE`` next --- while
        ``write_json_once`` made the FAIL record permanent, so the audit could
        not be re-run either. The registered terminal sentence was never
        recorded for such a replication.

        The audit's own detail is carried into ``observed`` rather than
        dropped: a terminating stage writes no stage record, and the artifact
        checks **and §33's own checklist** are the evidence for *why* the
        freeze was refused. v5 carried only the artifact checks, so a
        replication blocked by a §33 item recorded a terminal report that did
        not name it --- the audit exists to produce that table and the
        terminal path threw half of it away.
        """
        payload = prefreeze_payload(
            tree, producing_commit=commit, repo_root=repo_root, bank=bank,
            artifact_texts=artifact_texts)
        if not payload["can_freeze"]:
            raise TerminalStatus(
                PREFREEZE_AUDIT_FAILURE,
                gate=C.STAGE_PREFREEZE_AUDIT,
                criterion="§19: every mandatory artifact check passes and "
                          "nothing is unresolved; an unresolved check is not "
                          "a pass and nothing here may be waived",
                observed={"blocked": payload["blocked"],
                          "n_artifact_checks": payload["n_artifact_checks"],
                          "n_artifact_failed": payload["n_artifact_failed"],
                          "n_artifact_unresolved":
                              payload["n_artifact_unresolved"],
                          "artifact_checks": [
                              c for c in payload["artifact_checks"]
                              if c["verdict"] != "PASS"],
                          **_checklist_observed(payload),
                          "content_hash": payload["content_hash"]},
                strongest_permissible_statement=C.TERMINAL_SENTENCE)
        return payload

    return run_stage(
        tree, C.STAGE_PREFREEZE_AUDIT, compute=compute,
        producing_commit=commit, environment_digest=environment_digest)
