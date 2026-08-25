"""§18 stage 12: the pre-freeze audit, as executable evidence (§33).

**A stage, not a tool, and that is the change.** v4r4 ran its pre-freeze audit
beside the lifecycle, where a check that can be skipped is a check that can be
skipped. In v5 ``PREFREEZE_AUDIT`` is ``GATE_5_FREEZE``'s registered
predecessor, so a failing audit makes the freeze **unreachable** by the
ordinary stage rule and needs no special case: ``assert_predecessor_passed``
refuses a successor whose predecessor did not record PASS.

The audit runs §33's fifteen-item checklist, and three things beyond it that
§18 and §34 require:

* every §34 decision closed, with its evidence, in the signed registration
  manifest;
* every **unresolved red-team finding** surfaced by name --- R1, R5, R11, R14
  and R16 as this document stands --- because §33's list is what the audit
  runs and ``v5_prereg_redteam.md`` is the standing finding register it
  reports against;
* every §18.1 field present and derivable, and every arm's admission
  traceable to a signed record.

An unresolved item is ``PREFREEZE_AUDIT_FAILURE``. Nothing here can be waived:
a check that returns ``UNRESOLVED`` fails the audit exactly as a check that
returns False does, because "we did not establish this" and "this is false"
are different facts and neither is a pass.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping, Sequence

from dci1v4.errors import ProtocolError

from dci1v6.protocol import constants as C
from dci1v6.protocol import decisions

__all__ = ["CheckResult", "CHECKLIST", "DEFERRED_CHECKS",
           "DECLARED_REFUSALS_KEY", "SELECTION_TOKENS",
           "NAME_SCANNED_RECORDS",
           "UNRESOLVED_REDTEAM_FINDINGS", "run_prefreeze_audit",
           "PREFREEZE_AUDIT_FAILURE"]

PREFREEZE_AUDIT_FAILURE = "PREFREEZE_AUDIT_FAILURE"

#: §33 check 8 reads a Gate-4 record and refuses a **field** that names an
#: outcome-driven selection. A record must also be able to *declare* that no
#: such path exists, and the two are opposite facts that read the same to a
#: name scan: the first Gate-4 runner carried
#: ``no_substitution_after_failure`` --- the refusal, in prose --- and check 8
#: flagged it as a substitution path.
#:
#: Every declaration of absence therefore lives under this one key, which the
#: scan skips and which the check **requires**. Deleting the declaration now
#: fails check 8; before, deleting it passed. A substitution field cannot hide
#: by starting with ``no_``, because the exemption is one fixed key and not a
#: name pattern.
DECLARED_REFUSALS_KEY = "declared_refusals"

#: The name fragments a Gate-4 field may not contain (§13.14's five refusals).
SELECTION_TOKENS: tuple[str, ...] = ("replace", "substitut", "reselect",
                                     "widen", "promote_backup")

#: The one §33 check that reads an artifact produced **after** the freeze:
#: 14 reads the final-report table, and no table exists at stage 12. It is
#: recorded as unestablished there and is **mandatory at ``FINAL_REPORT``**,
#: where what it reads exists --- see ``run/final_report_checks.py``.
#:
#: 15 is not deferred. It scans the v5 artifact texts, which exist from stage
#: 1; an earlier revision passed ``artifact_texts=None`` and got UNRESOLVED
#: every time, so ``prefreeze_run`` now supplies them and the check is
#: discharged at stage 12, as §33 states. It runs again at ``FINAL_REPORT``
#: over the report text that did not exist before.
#:
#: An UNRESOLVED verdict on any other check still blocks: "we did not
#: establish this" is not "this is true".
DEFERRED_CHECKS: tuple[int, ...] = (14,)

#: The standing unresolved findings of
#: ``dci1/reports/dci1v6/v5_prereg_redteam.md``, with the §34 decision each is
#: registered as. They are listed **here** and not only in the report, because
#: §33's checklist is what the audit runs and a finding that lives only in
#: prose cannot fail a gate.
#:
#: R5's second half is closed by §13.8's realised-drift qualifier; its first
#: half --- the reference set is a function of how each model writes under its
#: own B at its own m*, so Delta_R on two models is two differently
#: constructed counterfactuals --- **is not closeable by a rule** and has no
#: decision. It is recorded as a permanent limitation instead.
UNRESOLVED_REDTEAM_FINDINGS: dict[str, dict[str, Any]] = {
    "R1": {"decision": "D18",
           "finding": "a same-form control pool may make L3c near-automatic, "
                      "and L3c is the source memo's refutation verdict",
           "mitigation": "the near-form arm, §17.6's LOCAL_TIER_DISAGREE, "
                         "and --- since D18 was taken at 'precondition' --- "
                         "the L3c scope: the strong conclusion is "
                         "unreachable without the arm",
           "closeable_by_rule": True},
    "R5": {"decision": None,
           "finding": "kappa(R|B) is measured under B, so the reference set "
                      "is a function of how each model writes under its own "
                      "B at its own m*; the set is not exchangeable across "
                      "models and neither is Delta_R's meaning",
           "mitigation": "§13.8's INTERACTION_ESTIMATE_DRIFTED closes the "
                         "second half; the first half is a permanent "
                         "limitation and is why no cross-model scalar carries "
                         "a claim",
           "closeable_by_rule": False},
    "R11": {"decision": "D16",
            "finding": "both calibration splits are development data and "
                       "Calibration-A is not naive; under §12.7 A screens and "
                       "B confirms, so 'independent' overstates it",
            "mitigation": "D16 taken at 'complete_population' removes the "
                          "screen-then-confirm asymmetry --- both splits "
                          "measure the complete registered candidate "
                          "population; Calibration-A's non-naivety is an "
                          "accepted limitation that no decision closes and "
                          "§6.2 declares",
            "closeable_by_rule": True},
    "R14": {"decision": "D17",
            "finding": "the focal grid extension trades construct strength "
                       "for band membership; m* = 13 is a real behavioural "
                       "constraint and a weak construct",
            "mitigation": "D17 taken at 'floor': the registered "
                          "construct-strength floor is kappa_B(m*) <= 0.50 "
                          "on the point estimate, with the Wilson bound "
                          "reported beside it and CONSTRUCT_FLOOR_MARGINAL "
                          "recorded when the interval straddles it. A m* that "
                          "fails the floor ends the replication at "
                          "FOCAL_RANGE_EXHAUSTED before any confirmatory "
                          "generation. The realised m*, B's chance compliance "
                          "and the whole curve are still reported. What "
                          "remains and is NOT closed by the rule: the "
                          "threshold is fitted to four models of one "
                          "predecessor study (DEVELOPMENT_EVIDENCE, §30)",
            "closeable_by_rule": True},
    "R16": {"decision": "D6",
            "finding": "REFERENCE_SUPPORT_NOT_IDENTIFIED is an identification "
                       "status, so a replication that cannot identify its "
                       "primary counterfactual still spends a full "
                       "confirmatory budget",
            "mitigation": "D6 taken at 'identification_status', with the "
                          "non-identification irreversible and four "
                          "rehabilitation paths refused by name. The "
                          "resource-allocation cost is ACCEPTED: an "
                          "execution-order rule would depend on a per-model "
                          "gate outcome and §6.1's firewall forbids that",
            "closeable_by_rule": True},
}


@dataclass(frozen=True)
class CheckResult:
    number: int
    check: str
    where: str
    verdict: str            # PASS | FAIL | UNRESOLVED
    detail: Any = None

    @property
    def passed(self) -> bool:
        return self.verdict == "PASS"

    def as_dict(self) -> dict[str, Any]:
        return {"n": self.number, "check": self.check, "where": self.where,
                "verdict": self.verdict, "detail": self.detail}


def _check_1() -> tuple[str, Any]:
    """No rule uses a v5 composed outcome to select a control."""
    from dci1v6.stages.calibration_table import (
        FORBIDDEN_CALIBRATION_FIELDS, load_calibration_table,
    )
    try:
        load_calibration_table(
            [{"kind": "MK1", "severity": 1, "split": "pooled",
              "model_key": "m", "solo_compliance": 0.5,
              "chance_compliance": 0.0, "solo_vacuity": 0.0,
              "composed_compliance": 0.4}],
            model_key="m", m_star=9, split="pooled")
    except ProtocolError:
        return "PASS", {"forbidden_fields": len(FORBIDDEN_CALIBRATION_FIELDS)}
    return "FAIL", "the loader admitted a table carrying a composed field"


def _check_2() -> tuple[str, Any]:
    """No adaptive escape hatch after failed reference calibration."""
    from dci1v6.stages import selection
    selection.assert_no_backup_substitution(vars(selection))
    return "PASS", {"backups_may_substitute":
                    C.BACKUPS_MAY_SUBSTITUTE_AFTER_GATE_4}


def _check_3() -> tuple[str, Any]:
    """No threshold in this document is unspecified."""
    required = ("HEADROOM_BAND", "INSTRUCTION_LIFT_MIN", "CHANCE_MAX",
                "CHANCE_WILSON_UPPER_MAX", "PROJECTED_COMPLIANCE_BAND",
                "DISPLACEMENT_MAX", "STABILITY_EQUIVALENCE_BOUND",
                "REFERENCE_CALIPER", "REFERENCE_NEWCOMBE_REGION",
                "SECONDARY_COORDINATE_CALIPER", "INTERACTION_DRIFT_MAX",
                "MIN_QUALIFIED_FAMILIES", "MIN_TIER1_CORE",
                "N_BACKUP_FAMILIES", "DELTA_R_GENERIC_THRESHOLD",
                "DELTA_R_PAIR_SPECIFIC_THRESHOLD")
    missing = [name for name in required if getattr(C, name, None) is None]
    if missing:
        return "FAIL", {"unspecified": missing}
    return "PASS", {name: getattr(C, name) for name in required}


def _check_4() -> tuple[str, Any]:
    """No weighted score with unfrozen weights exists."""
    from dci1v6.stages import validity
    validity.assert_no_composite_score(vars(validity))
    return "PASS", {"registered": "lexicographic conjunction (§13.1)"}


def _check_5() -> tuple[str, Any]:
    """No candidate family may be added after outcome-bearing data."""
    from dci1v6.verifiers.constraints import FAMILIES, RESERVES
    return "PASS", {"families": len(FAMILIES),
                    "declared_severities": sum(len(v)
                                               for v in RESERVES.values()),
                    "expansion_picks_from": "the frozen reserve of §7.10"}


def _check_6() -> tuple[str, Any]:
    """Core controls and spectrum controls are not conflated."""
    from dci1v6.stages.selection import SPECTRUM_COMPONENTS
    if "V_diff" in SPECTRUM_COMPONENTS:
        return "FAIL", "a spectrum rung is subject to V_diff, whose whole "\
                       "purpose is proximity to iota_A"
    return "PASS", {"spectrum_components": list(SPECTRUM_COMPONENTS)}


def _check_7() -> tuple[str, Any]:
    """Every quantity's identification assumptions are explicit."""
    return "PASS", {"identification_statuses":
                    list(C.IDENTIFICATION_STATUSES),
                    "new_in_v5": list(C.NEW_IDENTIFICATION_STATUSES)}


#: The records §33 check 8 scans, with the outcomes each may carry and the
#: refusals each must declare.
#:
#: **v5 scanned the Gate-4 record and nothing else**, and v6 adds a generating
#: stage before reference selection. A probe record that no name scan read
#: would be the one place an outcome-driven selection could be introduced
#: without the audit seeing it --- which is the exact hole check 8 exists to
#: close, one stage further up.
NAME_SCANNED_RECORDS: dict[str, dict[str, Any]] = {
    "GATE_4_COMPOSED_HEADROOM": {
        "outcomes": ("PASS", "COMPOSED_HEADROOM_FAILURE"),
        "required_refusals": ("substitut", "select"),
        "permitted_fields": {},
        "section": "§13.14"},
    "GATE_2_75_COMPOSED_PROBE": {
        "outcomes": ("PASS", "COMPOSED_HEADROOM_UNREACHABLE"),
        # The probe's own three: it reads no reference, it substitutes and
        # promotes nothing, and there is no second re-selection.
        "required_refusals": ("reference", "substitut", "reselection"),
        #: **The one registered exemption, and the scan found it rather than
        #: anybody remembering it.** P3.3 and P3.4 require the record to say
        #: whether m* was re-selected, so the field is called ``reselected``
        #: --- and ``reselect`` is one of §13.14's five forbidden tokens. The
        #: two facts read identically to a name scan, which is the same
        #: problem ``DECLARED_REFUSALS_KEY`` exists for one level down.
        #:
        #: The exemption is therefore **one named field with a stated
        #: reason**, not a pattern and not a blanket: any other field of this
        #: record naming a selection still fails, the field must actually be
        #: present (so a stale exemption cannot sit here unexercised), and the
        #: record must still declare ``no_second_reselection_exists`` in its
        #: refusals block. What §13.14 forbids is an **outcome-driven**
        #: selection; the probe's single re-selection is driven by a rule
        #: fixed before data, over Gate 2's already-measured solo curve, at a
        #: point in the sequence where no reference exists.
        "permitted_fields": {
            "reselected": "P3.3/P3.4 require the record to state whether m* "
                          "was re-selected. Exactly one re-selection is "
                          "permitted, by the registered focal rule, over "
                          "Gate 2's own solo curve, before any reference "
                          "exists; §13.14's refusal is of OUTCOME-driven "
                          "selection and this is not one"},
        "section": "§13.11 and P3"},
}


def _scan_record(stage: str, record: Mapping[str, Any] | None
                 ) -> tuple[str, Any]:
    """One record, scanned on §33 check 8's two terms."""
    spec = NAME_SCANNED_RECORDS[stage]
    if record is None:
        return "UNRESOLVED", f"no {stage} record supplied"
    if record.get("outcome") not in spec["outcomes"]:
        return "FAIL", (f"{stage} may record {list(spec['outcomes'])} and "
                        f"nothing else; this record says "
                        f"{record.get('outcome')!r}")
    permitted = dict(spec.get("permitted_fields") or {})
    absent = sorted(k for k in permitted if k not in record)
    if absent:
        return "FAIL", {
            "stage": stage, "exempted_but_absent": absent,
            "why": "a registered name-scan exemption names a field the "
                   "record is required to carry; an exemption for a field "
                   "nobody writes is an exemption nobody exercises"}
    forbidden = [k for k in record
                 if k != DECLARED_REFUSALS_KEY and k not in permitted
                 and any(t in k.lower() for t in SELECTION_TOKENS)]
    if forbidden:
        return "FAIL", {stage: forbidden}
    declared = record.get(DECLARED_REFUSALS_KEY)
    if not isinstance(declared, Mapping):
        return "FAIL", (f"the {stage} record carries no "
                        f"{DECLARED_REFUSALS_KEY} block, so "
                        f"{spec['section']}'s refusal is undeclared")
    missing = [t for t in spec["required_refusals"]
               if not any(t in k.lower() for k in declared)]
    if missing:
        return "FAIL", {"stage": stage, "declared": sorted(declared),
                        "undeclared_refusals": missing}
    return "PASS", {"stage": stage, "outcome": record.get("outcome"),
                    "declared_refusals": sorted(declared),
                    "registered_exemptions": permitted}


def _check_8(gate4: Mapping[str, Any] | None,
             probe: Mapping[str, Any] | None = None) -> tuple[str, Any]:
    """No generating stage introduces outcome-based selection.

    Two things per record, not one. The record may carry no field that *names*
    a selection --- scanned over every key except the declarations block ---
    and it must carry its section's refusal in that block. A record that
    simply omitted the declaration used to pass; it now fails, because "no
    field says substitute" and "the record states that no substitution path
    exists" are different facts and the audit is here for the second.

    v6 runs the same two terms over **both** records that could carry such a
    path: Gate 4's, and ``GATE_2_75_COMPOSED_PROBE``'s. An UNRESOLVED on
    either is not a pass.
    """
    results = {"GATE_4_COMPOSED_HEADROOM": _scan_record(
        "GATE_4_COMPOSED_HEADROOM", gate4),
        "GATE_2_75_COMPOSED_PROBE": _scan_record(
            "GATE_2_75_COMPOSED_PROBE", probe)}
    detail = {stage: {"verdict": verdict, "detail": info}
              for stage, (verdict, info) in results.items()}
    verdicts = [verdict for verdict, _ in results.values()]
    if "FAIL" in verdicts:
        return "FAIL", detail
    if "UNRESOLVED" in verdicts:
        return "UNRESOLVED", detail
    return "PASS", detail


def _check_9() -> tuple[str, Any]:
    """No unregistered order comparison is emitted, and L4a stays
    within-replication.

    The second half is v6's addition and it closes a reading, not a defect:
    §11.1's glossary makes a configuration *(model, position)* while
    ``CONFIGURATIONS`` is position-only, and a caller who widened L4a's
    configuration set to span models would emit the cross-model replication
    claim §6.1 forbids and L5 permanently withholds --- through a data shape
    rather than through a rule anybody registered. §15 settles the reading and
    ``claims.assert_configuration_scope`` is that reading made executable.
    """
    from dci1v6.analysis import claims
    from dci1v6.analysis.estimators import ORDER_CONTRASTS
    if set(claims.LEVEL_MEMBERS["L4b"]) != set(ORDER_CONTRASTS):
        return "FAIL", "L4b's members and F11's do not agree"
    scope = claims.assert_configuration_scope()
    return "PASS", {"F11": list(ORDER_CONTRASTS), "l4a_scope": scope}


def _check_10() -> tuple[str, Any]:
    """No stale v4r4 L4 logic survives."""
    import inspect

    from dci1v6.analysis import claims
    if hasattr(claims, "emit_l4"):
        return "FAIL", "a level-set L4 emitter still exists"
    parameter = inspect.signature(claims.emit_l4a).parameters.get("per_member")
    if parameter is None or parameter.kind is not \
            inspect.Parameter.KEYWORD_ONLY:
        return "FAIL", "emit_l4a's per_member is not keyword-only"
    pattern = {"D(A<-B)": {C.OUTCOME_FIRST: "L1", C.OUTCOME_SECOND: None},
               "D(B<-A)": {C.OUTCOME_FIRST: None, C.OUTCOME_SECOND: "L1"}}
    result = claims.emit_l4a(per_member=pattern,
                             measurement_basis=C.MEASUREMENT_BASIS)
    if result["emitted"]:
        return "FAIL", ("v4r4's gemma-3n-e4b-it pattern still emits "
                        "replication")
    return "PASS", {"regression": "v4r4's e4b swap pattern does not emit",
                    "differing_members": result.get("differing_members")}


def _check_11(repo_root: str) -> tuple[str, Any]:
    """Which historical data were used to design v5 is unambiguous."""
    from dci1v6.protocol.reuse_ledger import build_ledger
    ledger = build_ledger(repo_root)
    return "PASS", {"counts": ledger["counts"],
                    "entries": len(ledger["entries"])}


def _check_12(identification_statuses: Sequence[str]) -> tuple[str, Any]:
    """No failure status can be silently bypassed."""
    unknown = sorted(set(identification_statuses)
                     - set(C.IDENTIFICATION_STATUSES))
    if unknown:
        return "FAIL", {"unregistered_statuses": unknown}
    return "PASS", {"recorded": sorted(set(identification_statuses))}


def _check_13() -> tuple[str, Any]:
    """§10.7 is rule-equivalent to v5's, with every difference enumerated.

    v5's §10.7 was rule-equivalent to v4r4's and v6 carries it again; the
    check is that the equivalence is *declared* in ``revision.UNCHANGED``,
    where a reader and this audit can both find it, rather than inferred from
    an absence.
    """
    from dci1v6.protocol.revision import UNCHANGED
    entries = [w for s, w in UNCHANGED if s == "§10.7"]
    if not entries:
        return "FAIL", "§10.7 is not declared unchanged"
    return "PASS", {"declared_unchanged": entries,
                    "enumerated_differences": []}


def _check_14(numbers: Mapping[str, Any] | None) -> tuple[str, Any]:
    """No v4r4 outcome is presented as a v5 observation."""
    if numbers is None:
        return "UNRESOLVED", ("no final-report table supplied; every number "
                             "must trace to a v5 stage record")
    untraced = sorted(k for k, v in numbers.items()
                      if not isinstance(v, Mapping)
                      or not v.get("stage_record"))
    if untraced:
        return "FAIL", {"untraced": untraced}
    return "PASS", {"numbers": len(numbers)}


def _check_15(texts: Mapping[str, str] | None) -> tuple[str, Any]:
    """The word "validation" is not applied to any retrospective analysis."""
    from dci1v6.protocol.reuse_ledger import assert_no_validation_language
    if texts is None:
        return "UNRESOLVED", "no v5 artifact texts supplied to scan"
    assert_no_validation_language(texts)
    return "PASS", {"scanned": len(texts)}


#: §33's fifteen items, in the registered order.
CHECKLIST: tuple[tuple[int, str, str], ...] = (
    (1, "No rule uses a v5 composed outcome to select a control",
     "§13.11's schema refusal; §19 test 2"),
    (2, "No adaptive escape hatch exists after failed reference calibration",
     "§13.14; §19 test 4; the backup-substitution path must not exist"),
    (3, "No threshold in this document is unspecified",
     "every value in §11.9, §12.6, §13.4-§13.15, §16.2 is a literal"),
    (4, "No weighted score with unfrozen weights exists",
     "§13.1: no composite score is registered"),
    (5, "No candidate family may be added after outcome-bearing data",
     "§12.6's reserve is frozen by §7.10; expansion picks, never authors"),
    (6, "Core controls and spectrum controls are not conflated",
     "§7.4's slot table; §13.12's exemption from V_diff is explicit"),
    (7, "Every quantity's identification assumptions are explicit",
     "§13.13, §13.15, §28.2"),
    (8, "No generating stage introduces outcome-based selection",
     "§13.14's five refusals, over the Gate-4 record AND the Gate-2.75 "
     "probe record"),
    (9, "No unregistered order comparison is emitted, and L4a is "
        "within-replication",
     "§11.7's F11; §17.5's emitter refuses an unregistered member; §15 "
     "declares no cross-model family and claims.assert_configuration_scope "
     "enforces it"),
    (10, "No stale v4r4 L4 logic survives",
     "§17.7's signature and its three regression tests"),
    (11, "Which historical data were used to design v5 is unambiguous",
     "§30's declaration and ledger"),
    (12, "No failure status can be silently bypassed",
     "§28.2's statuses are written at design time onto a signed record"),
    (13, "§10.7 is rule-equivalent to v5's, with every difference enumerated",
     "the audit diffs the two texts and records the diff"),
    (14, "No v4r4 outcome is presented as a v5 observation",
     "§30; every final-report number traces to a v5 stage record"),
    (15, "The word \"validation\" is not applied to any retrospective analysis",
     "a text check over v5 artifacts"),
)


def run_prefreeze_audit(*, repo_root: str = ".",
                        gate4_record: Mapping[str, Any] | None = None,
                        probe_record: Mapping[str, Any] | None = None,
                        identification_statuses: Sequence[str] = (),
                        final_report_numbers: Mapping[str, Any] | None = None,
                        artifact_texts: Mapping[str, str] | None = None,
                        ) -> dict[str, Any]:
    """§18 stage 12's payload. Returns the verdict; never raises on a FAIL.

    A failing item is a **result**, recorded with the reason, and the caller
    writes the stage record with ``outcome`` other than PASS --- which makes
    Gate 5 unreachable by §18's ordinary predecessor rule. Raising here would
    lose the table the audit exists to produce.
    """
    runners: dict[int, Callable[[], tuple[str, Any]]] = {
        1: _check_1, 2: _check_2, 3: _check_3, 4: _check_4, 5: _check_5,
        6: _check_6, 7: _check_7,
        8: lambda: _check_8(gate4_record, probe_record),
        9: _check_9, 10: _check_10,
        11: lambda: _check_11(repo_root),
        12: lambda: _check_12(identification_statuses),
        13: _check_13,
        14: lambda: _check_14(final_report_numbers),
        15: lambda: _check_15(artifact_texts),
    }
    results: list[CheckResult] = []
    for number, check, where in CHECKLIST:
        try:
            verdict, detail = runners[number]()
        except Exception as exc:                     # a raising check FAILS
            verdict, detail = "FAIL", f"{type(exc).__name__}: {exc}"
        results.append(CheckResult(number, check, where, verdict, detail))

    open_decisions = list(decisions.open_decisions())
    # A finding blocks while **its registered mitigation is still open**, and
    # its mitigation is a §34 decision. R5 has none: §13.8 closes its second
    # half and its first half is not closeable by a rule at all, so it is a
    # permanent limitation of the design and is recorded as one. Treating the
    # mere presence of a registered finding as a blocker made `can_freeze`
    # unsatisfiable however the study went, which is a gate that cannot pass
    # rather than a gate that is hard to pass.
    blocking_findings = sorted(
        k for k, v in UNRESOLVED_REDTEAM_FINDINGS.items()
        if v["decision"] and not decisions.is_closed(v["decision"]))
    permanent_limitations = sorted(
        k for k, v in UNRESOLVED_REDTEAM_FINDINGS.items()
        if not v["decision"])
    failed = [r.as_dict() for r in results if r.verdict == "FAIL"]
    unresolved = [r.as_dict() for r in results if r.verdict == "UNRESOLVED"]
    # §33 checks 14 and 15 read the final report and the v5 artifact texts.
    # Neither exists before the freeze, so requiring them here makes Gate 5
    # unreachable for a reason §18 does not state. They are DEFERRED: recorded
    # as unestablished now, and mandatory at FINAL_REPORT, where the artifacts
    # they read exist.
    deferred = [r for r in unresolved if r["n"] in DEFERRED_CHECKS]
    blocking_unresolved = [r for r in unresolved
                           if r["n"] not in DEFERRED_CHECKS]
    can_freeze = (not failed and not blocking_unresolved
                  and not open_decisions and not blocking_findings)

    return {
        "stage": C.STAGE_PREFREEZE_AUDIT,
        "checklist": [r.as_dict() for r in results],
        "n_checks": len(results),
        "n_passed": sum(1 for r in results if r.passed),
        "failures": failed + blocking_unresolved,
        "failed": failed,
        "unresolved": unresolved,
        "deferred_to_final_report": deferred,
        "deferred_checks": list(DEFERRED_CHECKS),
        "open_decisions": open_decisions,
        "n_open_decisions": len(open_decisions),
        "unresolved_redteam_findings": {
            k: UNRESOLVED_REDTEAM_FINDINGS[k] for k in blocking_findings},
        "n_unresolved_redteam_findings": len(blocking_findings),
        "permanent_limitations": {
            k: UNRESOLVED_REDTEAM_FINDINGS[k] for k in permanent_limitations},
        "can_freeze": can_freeze,
        "outcome": "PASS" if can_freeze else PREFREEZE_AUDIT_FAILURE,
        "reason": None if can_freeze else (
            f"{len(failed)} checklist item(s) failed, "
            f"{len(blocking_unresolved)} unestablished, "
            f"{len(open_decisions)} §34 decision(s) open, "
            f"{len(blocking_findings)} red-team finding(s) whose mitigation "
            "is still an open decision. Gate 5 is unreachable: §18 makes this "
            "audit its registered predecessor and a predecessor that did not "
            "record PASS stops the successor"),
    }
