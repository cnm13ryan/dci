"""§18 stage 18's own checks: what only the final report can establish.

§33 says its checklist is executed at stage 12, and thirteen of its fifteen
items are: they read code, thresholds, schemas and signed records that all
exist before the freeze. **Check 14 cannot be**, because it reads the
final-report table and no table exists at stage 12. An earlier revision left
it reporting ``UNRESOLVED`` there and nowhere else, which is a check that
never ran --- so it is registered as *deferred* at stage 12 and **mandatory
here**, and this module is where it runs.

The rest of this module is the other half of the same idea. A final report
that merely reprints the unmasked analysis proves nothing; a final report that
re-derives every number's provenance from signed records proves the chain. So
each check below opens the records again and establishes its answer from them:
the estimate against the unmasked record it claims to come from, the
identification statuses against the freeze, the hashes against the files on
disk, the unmask against the stage machine that is supposed to refuse a
second one.

**A failing mandatory check fails the stage.** ``FINAL_REPORT`` has no
successor to refuse, so the record is written with ``outcome`` ``FAIL`` --- the
evidence of what failed is the point --- and ``run_final_report`` then raises.
A report that cannot establish its own traceability is not a report.
"""
from __future__ import annotations

import inspect
from pathlib import Path
from typing import Any, Mapping, Sequence

from dci1v4.errors import IntegrityError
from dci1v4.protocol.hashing import sha_obj

from dci1v7.engine import transitions
from dci1v7.engine.paths import ModelTree
from dci1v7.protocol import constants as C
from dci1v7.protocol import reuse_ledger
from dci1v7.stages import audit_prefreeze

__all__ = ["FINAL_REPORT_CHECKS", "final_report_checks",
           "deferred_checklist_results", "FINAL_REPORT_FAILURE"]

FINAL_REPORT_FAILURE = "FINAL_REPORT_FAILURE"

#: id, what it establishes, mandatory.
FINAL_REPORT_CHECKS: tuple[tuple[str, str, bool], ...] = (
    ("deferred_prefreeze_checks_discharged",
     "every §33 item the pre-freeze audit deferred has a verdict here", True),
    ("estimates_trace_to_unmasked_analysis",
     "every reported estimate equals the unmasked record's own value", True),
    ("no_irreversibly_unidentified_member_is_estimated",
     "§34 D6: no reported row carries an estimate for a member Gate 3C "
     "marked NOT_IDENTIFIED for want of reference support", True),
    ("identification_statuses_trace_to_the_freeze",
     ("the reported statuses are the ones Gate 5 bound, and Gate 5 bound "
      "exactly the union of Gate 2's and Gate 3C's"), True),
    ("lifecycle_records_complete",
     "every registered stage has a signed record and a transition-log entry",
     True),
    ("claim_levels_are_registered",
     "every claim level and every member of it is registered", True),
    ("l4a_is_named_member_replication",
     "§17.7: emit_l4a is per named member, and v4r4's swap pattern does not "
     "emit", True),
    ("l4b_is_f11_order_effects",
     "L4b's members are exactly F11's order contrasts", True),
    ("no_l5_emitter", "no L5 emitter exists in the claims module", True),
    ("no_unidentified_quantity_rendered_as_an_estimate",
     "a NOT_IDENTIFIED row carries a reason and no point", True),
    ("no_historical_evidence_presented_as_v7_confirmation",
     "§30: only NEW_V7_EVIDENCE is estimand-admissible, and no artifact "
     "calls a retrospective analysis validation", True),
    ("hash_chain_intact",
     "every stage-record hash the report carries recomputes from the record "
     "on disk", True),
    ("unmask_occurred_once",
     "one unmask event, and a second unmask is refused by the stage machine",
     True),
    ("durable_copies_recorded",
     "every stage directory has a verified durable mirror", True),
)



def bound_statuses(gate2_statuses, gate3c_statuses) -> list[str]:
    """The identification statuses §18.1 binds: Gate 2's and Gate 3C's,
    as one sorted set --- the same union `freeze_run.assemble` writes."""
    return sorted(set(gate2_statuses) | set(gate3c_statuses))

def _result(check: str, verdict: str, detail: Any, mandatory: bool
            ) -> dict[str, Any]:
    return {"check": check, "verdict": verdict, "detail": detail,
            "mandatory": mandatory}


def deferred_checklist_results(tree: ModelTree, report: Mapping[str, Any], *,
                               repo_root: Path | str = ".",
                               ) -> dict[str, Any]:
    """The §33 items stage 12 deferred, run over what now exists.

    Check 14 reads the report's own table --- one entry per reported number,
    each of which must name the v5 stage record it came from. Check 15 is
    re-run with the report text included, because the report is a v5 artifact
    and it is the artifact most likely to describe a retrospective result as
    a confirmation.
    """
    numbers = {
        f"{row['member']}@{row['configuration']}": {
            "stage_record": row.get("source_stage"),
            "freeze_hash": row.get("freeze_hash"),
            "status": row.get("status")}
        for row in report.get("results", ())}
    texts = reuse_ledger.collect_artifact_texts(
        repo_root, extra={f"{C.STAGE_FINAL_REPORT}:{tree.model_key}":
                          _report_text(report)})
    checklist = audit_prefreeze.run_prefreeze_audit(
        repo_root=str(repo_root),
        gate4_record=transitions.read_stage_record(tree, C.STAGE_GATE4),
        identification_statuses=report.get("identification_statuses", ()),
        final_report_numbers=numbers, artifact_texts=texts)
    # What must be discharged here is what the *pre-freeze record* deferred,
    # not what this module's constant says today. If the audit deferred an
    # item and a later edit dropped it from DEFERRED_CHECKS, the item would
    # otherwise go undischarged in both places.
    audit = transitions.read_stage_record(tree, C.STAGE_PREFREEZE_AUDIT)
    owed = sorted({r["n"] for r in
                   audit["checklist"].get("deferred_to_final_report", ())}
                  | set(audit_prefreeze.DEFERRED_CHECKS))
    results = {r["n"]: r for r in checklist["checklist"]}
    missing = [n for n in owed if n not in results]
    discharged = [results[n] for n in owed if n in results]
    # Check 15 is not deferred --- it is discharged at stage 12 --- but it is
    # re-run here over the report text, which did not exist then.
    rerun = [r for r in checklist["checklist"] if r["n"] == 15]
    return {"deferred_by_the_audit": owed,
            "results": discharged,
            "rerun_over_the_report_text": rerun,
            "n_numbers_traced": len(numbers),
            "n_texts_scanned": len(texts),
            "all_discharged": (not missing
                               and all(r["verdict"] == "PASS"
                                       for r in discharged)
                               and all(r["verdict"] == "PASS"
                                       for r in rerun)),
            "not_run": missing}


def _report_text(report: Mapping[str, Any]) -> str:
    """Every string the report carries, for the §33 check 15 text scan."""
    parts: list[str] = []

    def walk(value: Any) -> None:
        if isinstance(value, str):
            parts.append(value)
        elif isinstance(value, Mapping):
            for key, item in value.items():
                parts.append(str(key))
                walk(item)
        elif isinstance(value, (list, tuple)):
            for item in value:
                walk(item)

    walk(report)
    return "\n".join(parts)


def final_report_checks(tree: ModelTree, report: Mapping[str, Any], *,
                        repo_root: Path | str = ".") -> list[dict[str, Any]]:
    """Every check above, established from the signed records in ``tree``."""
    mandatory = {cid: block for cid, _why, block in FINAL_REPORT_CHECKS}
    out: list[dict[str, Any]] = []

    def add(check: str, ok: bool | None, detail: Any = None) -> None:
        verdict = "UNRESOLVED" if ok is None else ("PASS" if ok else "FAIL")
        out.append(_result(check, verdict, detail, mandatory[check]))

    rows = list(report.get("results", ()))

    # ------------------------------------------------- the deferred §33 items
    try:
        deferred = deferred_checklist_results(tree, report,
                                              repo_root=repo_root)
        add("deferred_prefreeze_checks_discharged", deferred["all_discharged"],
            deferred)
    except Exception as error:
        add("deferred_prefreeze_checks_discharged", False,
            f"{type(error).__name__}: {error}")

    # ------------------------------------------------------- the estimates
    analysis = transitions.read_stage_record(tree, C.STAGE_UNMASKED_ANALYSIS)
    estimands = analysis["estimands"]
    mismatched: list[dict[str, Any]] = []
    for row in rows:
        bucket = (estimands["cross_configuration"]
                  if row["configuration"] == "cross"
                  else estimands["configurations"].get(row["configuration"],
                                                       {}))
        entry = bucket.get(row["member"])
        if entry is None:
            mismatched.append({"row": row["member"], "why": "no such estimand"})
        elif entry["status"] != row["status"] or \
                entry.get("point") != row.get("point"):
            mismatched.append({"row": row["member"],
                               "reported": row.get("point"),
                               "record": entry.get("point")})
    add("estimates_trace_to_unmasked_analysis",
        bool(rows) and not mismatched,
        {"rows": len(rows), "mismatched": mismatched[:5],
         "source_stage": C.STAGE_UNMASKED_ANALYSIS})

    # ---------------------------------------------- identification statuses
    from dci1v7.run.freeze_run import load_freeze

    freeze_record = load_freeze(tree)
    gate3c = transitions.read_stage_record(tree, C.STAGE_GATE3C)

    # ------------------------------------------------------- §34 D6
    # The last stage that could lift a Gate-3C non-identification, and the
    # first at which the *table* exists to lift it in. `assert_not_
    # rehabilitated` raises; here the verdict is recorded instead, because
    # FINAL_REPORT has no successor to refuse and the failure has to land on
    # the record itself.
    frozen = freeze_record.get("non_identification") or \
        gate3c.get("non_identification")
    forbidden = set((frozen or {}).get("not_identified_members", ()))
    offered = sorted({row["member"] for row in rows
                      if row["member"] in forbidden
                      and row.get("estimate") is not None})
    add("no_irreversibly_unidentified_member_is_estimated", not offered,
        {"frozen_members": len(forbidden), "offered": offered,
         "decision": "D6",
         "note": "null when §13.15 was met; the check is then vacuously "
                 "satisfied and says so rather than being skipped"})
    # §18.1 binds every identification status the replication carries:
    # Gate 2's (`OPERATING_POINT_AT_GRID_BOUNDARY`, `EXCESS_NOT_IDENTIFIED`
    # at the operating point) with Gate 3C's, and `freeze_run.assemble`
    # writes their union. Until 2026-08-29 this check required the freeze
    # to equal Gate 3C's set alone, so a replication with any Gate-2 status
    # failed its final report by construction --- first reached on the
    # development rehearsal r3 of gemma-3n-e2b-it.
    gate2 = transitions.read_stage_record(tree, C.STAGE_GATE2)
    reported = sorted(set(report.get("identification_statuses", ())))
    bound = bound_statuses(gate2.get("identification_statuses", ()),
                           gate3c.get("identification_statuses", ()))
    frozen_statuses = sorted(set(freeze_record["identification_statuses"]))
    add("identification_statuses_trace_to_the_freeze",
        reported == frozen_statuses == bound,
        {"report": reported, "freeze": frozen_statuses,
         "gate2": sorted(set(gate2.get("identification_statuses", ()))),
         "gate3c": sorted(set(gate3c.get("identification_statuses", ()))),
         "bound_by_gate_5": bound})

    # ------------------------------------------------------ the lifecycle
    log_entries = {entry.get("stage")
                   for entry in transitions.transition_rows(tree)}
    # Every stage *before* this one. Stage 18's own record is being computed
    # right now and its log entry is written after it, so requiring them here
    # is a check no run could ever pass.
    earlier = [s for s in C.STAGE_SEQUENCE if s != C.STAGE_FINAL_REPORT]
    missing = [stage for stage in earlier
               if not tree.stage_record(stage).exists()]
    unlogged = [stage for stage in earlier if stage not in log_entries]
    add("lifecycle_records_complete", not missing and not unlogged,
        {"n_stages_required": len(earlier),
         "missing_records": missing, "unlogged": unlogged,
         "note": "FINAL_REPORT's own record and log entry are written after "
                 "this payload is computed"})

    # ----------------------------------------------------- the claim ladder
    from dci1v7.analysis import claims

    statements = list(report.get("statements", ()))
    # A row whose member reached no level carries None, which is §15's
    # "Secondary" and §17.3's withheld statement written as a fact rather
    # than as a level the estimate does not support. An unregistered *level*
    # still fails.
    bad_levels = sorted(
        {row.get("claim_level") for row in rows if row.get("claim_level")}
        - set(C.CLAIM_LEVELS))
    bad_members = [s for s in statements
                   if s.get("claim_level") in claims.LEVEL_MEMBERS
                   and s.get("member") is not None
                   and s["member"] not in
                   claims.LEVEL_MEMBERS[s["claim_level"]]]
    add("claim_levels_are_registered", not bad_levels and not bad_members,
        {"levels_used": sorted(
            {row.get("claim_level") or "none" for row in rows}),
         "registered": list(C.CLAIM_LEVELS),
         "unregistered_levels": bad_levels,
         "unregistered_members": [s.get("member") for s in bad_members]})

    signature = inspect.signature(claims.emit_l4a)
    per_member = signature.parameters.get("per_member")
    swap = {"D(A<-B)": {C.OUTCOME_FIRST: "L1", C.OUTCOME_SECOND: None},
            "D(B<-A)": {C.OUTCOME_FIRST: None, C.OUTCOME_SECOND: "L1"}}
    replicated = claims.emit_l4a(per_member=swap,
                                 measurement_basis=C.MEASUREMENT_BASIS)
    add("l4a_is_named_member_replication",
        per_member is not None
        and per_member.kind is inspect.Parameter.KEYWORD_ONLY
        and not hasattr(claims, "emit_l4")
        and not replicated["emitted"],
        {"signature": str(signature),
         "v4r4_swap_pattern_emits": replicated["emitted"],
         "differing_members": replicated.get("differing_members")})

    from dci1v7.analysis.estimators import ORDER_CONTRASTS

    cross = [row for row in rows if row["configuration"] == "cross"]
    add("l4b_is_f11_order_effects",
        set(claims.LEVEL_MEMBERS["L4b"]) == set(ORDER_CONTRASTS)
        == set(C.FAMILY_MEMBERS["F11"])
        and all(row["family"] == "F11" for row in cross),
        {"L4b": sorted(claims.LEVEL_MEMBERS["L4b"]),
         "F11": sorted(C.FAMILY_MEMBERS["F11"]),
         "order_contrasts": sorted(ORDER_CONTRASTS),
         "cross_rows": len(cross)})

    try:
        claims.assert_no_l5_emitter(vars(claims))
        add("no_l5_emitter", True,
            {"withheld": list(C.WITHHELD_CLAIM_LEVELS)})
    except Exception as error:
        add("no_l5_emitter", False, str(error))

    rendered = [row["member"] for row in rows
                if row["status"] != "IDENTIFIED"
                and (row.get("point") is not None
                     or not row.get("identification_status"))]
    add("no_unidentified_quantity_rendered_as_an_estimate", not rendered,
        {"n_not_identified": sum(1 for row in rows
                                 if row["status"] != "IDENTIFIED"),
         "rendered_anyway": rendered[:5]})

    # -------------------------------------------------------------- §30
    try:
        ledger = reuse_ledger.build_ledger(repo_root)
        inadmissible = sorted(
            {e["classification"] for e in ledger["entries"]}
            - set(reuse_ledger.ESTIMAND_ADMISSIBLE))
        confirmatory = transitions.read_stage_record(tree, C.STAGE_CONFIRMATORY)
        v7_only = all(
            row.get("study_id") == tree.context.study_id
            for row in __import__("dci1v7.run.confirmatory_run",
                                  fromlist=["x"]).collect_rows(tree))
        add("no_historical_evidence_presented_as_v7_confirmation",
            v7_only and reuse_ledger.ESTIMAND_ADMISSIBLE == ("NEW_V7_EVIDENCE",),
            {"estimand_admissible": list(reuse_ledger.ESTIMAND_ADMISSIBLE),
             "ledger_classifications_present": inadmissible,
             "confirmatory_rows": confirmatory.get("n_rows"),
             "every_row_is_this_study": v7_only})
    except Exception as error:
        add("no_historical_evidence_presented_as_v7_confirmation", False,
            f"{type(error).__name__}: {error}")

    # ------------------------------------------------------- the hash chain
    recorded = dict(report.get("stage_record_hashes") or {})
    drifted = sorted(
        stage for stage, digest in recorded.items()
        if sha_obj(transitions.read_stage_record(tree, stage)) != digest)
    # FINAL_REPORT hashes the records that existed when it ran, which is every
    # stage before it; its own record does not yet exist to hash.
    expected = [s for s in C.STAGE_SEQUENCE if s != C.STAGE_FINAL_REPORT]
    add("hash_chain_intact",
        not drifted and sorted(recorded) == sorted(expected),
        {"n_hashes": len(recorded), "drifted": drifted,
         "missing": sorted(set(expected) - set(recorded))})

    # ----------------------------------------------------------- the unmask
    unmask = transitions.read_stage_record(tree, C.STAGE_UNMASKING)
    try:
        transitions.assert_transition_legal(tree, C.STAGE_UNMASKING)
        refused = False
    except IntegrityError:
        refused = True
    events = unmask.get("unmask_event")
    add("unmask_occurred_once",
        bool(unmask.get("unmasked")) and refused and bool(events),
        {"second_unmask_refused": refused,
         "analysis_code_hash": unmask.get("analysis_code_hash"),
         "event": events if not isinstance(events, Sequence) else events})

    # -------------------------------------------------------- the durability
    from dci1v4.engine import store

    mirrored: dict[str, bool] = {}
    for stage in C.STAGE_SEQUENCE:
        source = tree.stage_dir(stage)
        durable = tree.durable / stage
        if not source.exists():
            mirrored[stage] = False
            continue
        try:
            store.assert_replicated(source, durable)
            mirrored[stage] = True
        except Exception:
            mirrored[stage] = False
    # The final report's own directory is mirrored after this payload is
    # written, so it is reported and not required.
    checked = {k: v for k, v in mirrored.items() if k != C.STAGE_FINAL_REPORT}
    add("durable_copies_recorded", all(checked.values()),
        {"mirrored": mirrored,
         "note": "FINAL_REPORT mirrors after its own record is written"})
    return out
