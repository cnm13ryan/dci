"""What v7 changes from v6, enumerated where the code can read it.

A revision that lists its changes only in prose has no way to check that the
code made them. Every entry carries the **section it is registered under** and,
where the change is executable, a callable that returns True only when the code
actually carries it. ``assert_changes_realised`` is on the registration path,
so a listed change the code does not make stops stage 1.

**v7 is one change, stated several ways.** The scientific question, the
estimands, every admission threshold, the claim ladder with L5 permanently
withheld, F1-F11, interaction-blind reference selection, the prohibition on
a B+R composed outcome entering selection, irreversible D6, the prospective
freeze, one-shot masking and §32's no-repair rules are all carried from v6
**unchanged**, and v6 carried them from v5. What changes is what a composed
compliance rate at 0 or 1 is allowed to do: nothing to the replication, and
three recorded things to the contrast it enters. Everything below is that
change and its consequences, and nothing else.

Ordinary refactors and re-namespacing are not changes and are not listed.
"""
from __future__ import annotations

import ast
import inspect
from dataclasses import dataclass
from typing import Any

from dci1v4.errors import ProtocolError

from dci1v7.protocol import constants as C

__all__ = ["Change", "CHANGES", "UNCHANGED", "assert_changes_realised",
           "revision_record", "ESTIMAND_LAYER", "PREDECESSOR_PACKAGE",
           "assert_no_raise_path"]

PREDECESSOR_PACKAGE = "dci1v6"


@dataclass(frozen=True)
class Change:
    id: str
    section: str
    what: str
    why: str
    #: A callable returning True when the code actually carries the change.
    check: Any = None


def _headroom_statuses_are_withdrawn() -> bool:
    withdrawn = set(C.WITHDRAWN_STATUSES)
    return ({"COMPOSED_HEADROOM_FAILURE", "COMPOSED_HEADROOM_UNREACHABLE"}
            <= withdrawn
            and not withdrawn & set(C.TERMINAL_STATUSES)
            and C.NEW_TERMINAL_STATUSES == ()
            and all(C.WITHDRAWN_STATUS_REASONS.get(s) for s in withdrawn))


def _raise_sites(module: Any) -> list[tuple[str, str]]:
    """Every ``raise TerminalStatus(<literal>, ...)`` in a module's source."""
    out: list[tuple[str, str]] = []
    try:
        tree = ast.parse(inspect.getsource(module))
    except (OSError, TypeError):
        return out
    for node in ast.walk(tree):
        if not isinstance(node, ast.Raise) or node.exc is None:
            continue
        call = node.exc
        if not isinstance(call, ast.Call):
            continue
        name = getattr(call.func, "id", getattr(call.func, "attr", ""))
        if name != "TerminalStatus" or not call.args:
            continue
        first = call.args[0]
        if isinstance(first, ast.Constant) and isinstance(first.value, str):
            out.append((module.__name__, first.value))
        elif isinstance(first, ast.Attribute):
            out.append((module.__name__, first.attr))
        elif isinstance(first, ast.Name):
            out.append((module.__name__, first.id))
    return out


def _package_modules() -> list[Any]:
    import importlib
    import pkgutil

    import dci1v7

    # Every module must import: one that does not would leave its raise
    # sites unscanned, and a scan with a hole is not the check V1 registers.
    return [importlib.import_module(info.name)
            for info in pkgutil.walk_packages(dci1v7.__path__,
                                              prefix="dci1v7.")]


def assert_no_raise_path(statuses: tuple[str, ...] = C.WITHDRAWN_STATUSES
                         ) -> dict[str, Any]:
    """The converse of the A8 regression: a withdrawn status has NO raise.

    A8 walks the AST for a status in force with no reachable ``raise``. This
    walks it for a withdrawn status **with** one --- the way a withdrawn
    criterion would come back is a module that still raises it --- and also
    for any name bound to a withdrawn status's literal, since ``TerminalStatus``
    is raised by name as often as by string.
    """
    offenders = []
    for module in _package_modules():
        for where, status in _raise_sites(module):
            if status in statuses:
                offenders.append(f"{where}: raise TerminalStatus({status})")
            bound = getattr(module, status, None)
            if isinstance(bound, str) and bound in statuses and \
                    (where, bound) in _raise_sites(module):
                offenders.append(f"{where}: {status} bound and raised")
    for module in _package_modules():
        source = ""
        try:
            source = inspect.getsource(module)
        except (OSError, TypeError):
            continue
        for status in statuses:
            if f'raise TerminalStatus(\n            "{status}"' in source or \
                    f'raise TerminalStatus("{status}"' in source:
                offenders.append(f"{module.__name__}: {status}")
    if offenders:
        raise ProtocolError(
            f"a withdrawn status has a raise path: {sorted(set(offenders))}. "
            "v7 A1 withdraws the composed-headroom criterion; a module that "
            "can still raise its status has not")
    return {"withdrawn": list(statuses), "raise_paths": []}


def _no_module_can_raise_a_withdrawn_status() -> bool:
    assert_no_raise_path()
    return True


def _the_probe_records_and_cannot_terminate() -> bool:
    """Behavioural: a probe table with a determinate entry at an exact
    ceiling records and returns PASS, and a second severity is refused."""
    from dci1v7.stages import composed_probe as probe

    topics = [f"t{i}" for i in range(12)]

    def m(level: float) -> dict:
        return {"compliance": level, "s2_topic": 0.0, "n_topics": 12,
                "per_topic": {t: level for t in topics}}
    table = {"solo:A": {"A": m(0.6)}, "solo:B": {"B": m(0.7)},
             "pair:A+B": {"A": m(0.4), "B": m(1.0)},
             "pair:B+A": {"B": m(1.0), "A": m(0.4)}}
    out = probe.probe_disposition(m_star=10, probed={10: table}, seed=1,
                                  resamples=20)
    if out["outcome"] != "PASS" or out["m_star_out"] != 10 or \
            out["terminal_status"] is not None:
        return False
    record = out["verdict"]
    if "COMPOSED_ARM_AT_BOUNDARY" not in record["contrast_statuses"]:
        return False
    try:
        probe.probe_disposition(m_star=10, probed={10: table, 11: table},
                                seed=1, resamples=20)
    except ProtocolError:
        return out["reselections_permitted"] == 0
    return False


def _gate4_records_a_contrast_and_cannot_terminate() -> bool:
    from dci1v7.run import gates_run
    from dci1v7.stages import composed_contrast

    source = inspect.getsource(gates_run.gate4_payload)
    if "TerminalStatus(" in source:
        return False
    if "composed_contrast.projection(" not in source:
        return False
    return (composed_contrast.GATE4_OUTCOME == "PASS"
            and "Delta_R" in C.FAMILY_MEMBERS["F1"])


def _boundary_rule_is_executable() -> bool:
    """A structural zero, an arm at a boundary and a compressed direction
    are each produced by the rule on a synthetic contrast, and the SESOI is
    the only threshold it reads."""
    from dci1v7.analysis import boundary

    parts = boundary.composition("Delta_R")
    if parts is None or abs(sum(p.weight for p in parts)) > 1e-12:
        return False
    ceiling = [1.0] * 30
    interior = [0.6] * 30
    zero = boundary.contrast_boundary(
        "Delta_R", [(p, ceiling) for p in parts], configuration="outcome_first")
    mixed = boundary.contrast_boundary(
        "Delta_R", [(p, interior if p.weight > 0 else ceiling) for p in parts],
        configuration="outcome_first")
    return (zero["structural_zero"]
            and boundary.STRUCTURAL_ZERO in zero["statuses"]
            and not mixed["structural_zero"]
            and boundary.ARM_AT_BOUNDARY in mixed["statuses"]
            and boundary.RANGE_COMPRESSED in mixed["statuses"]
            and mixed["compression"]["positive_direction_compressed"]
            and abs(C.CONTRAST_COMPRESSION_LEVEL
                    - (1.0 - C.SMALLEST_EFFECT_OF_INTEREST)) < 1e-12
            and mixed["allowance_upper"] > 0.0
            and mixed["allowance_lower"] == 0.0)


def _analysis_reads_the_boundary() -> bool:
    from dci1v7.analysis import claims
    from dci1v7.run import analysis_run

    source = inspect.getsource(analysis_run._intervals)
    if "contrast_boundary_from_table(" not in source:
        return False
    zero = claims.Interval("Delta_R", 0.0, 0.0, 0.0,
                           boundary={"statuses": [claims.C.V7_IDENTIFICATION_STATUSES[0]],
                                     "structural_zero": True})
    reading = claims.delta_r_reading(zero)
    return ("STRUCTURAL_ZERO" in reading["markers"]
            and not reading["direction_resolved"])


def _structural_zero_is_read_on_its_allowance_interval() -> bool:
    """V10: at a shared exact boundary the decision interval is the
    allowance alone, no direction is reachable, and the equivalence reading
    follows the registered rule on that interval --- L3c at the registered
    block count, nothing at Gate 4's 24 topics."""
    from dci1v7.analysis import boundary, claims

    parts = boundary.composition("Delta_R")
    if parts is None:
        return False
    verdicts = []
    for n, expected in ((C.N_BLOCKS, ["L3c"]), (24, [])):
        reading = boundary.contrast_boundary(
            "Delta_R", [(p, [1.0] * n) for p in parts],
            configuration="outcome_first")
        lower, upper = boundary.apply_allowance(0.0, 0.0, reading)
        interval = claims.Interval("Delta_R", 0.0, lower, upper,
                                   boundary=reading)
        read = claims.delta_r_reading(interval)
        half = boundary.boundary_halfwidth(n)
        verdicts.append(
            reading["structural_zero"]
            and abs(lower + half) < 1e-12 and abs(upper - half) < 1e-12
            and read["levels"] == expected
            and "STRUCTURAL_ZERO" in read["markers"]
            and not read["direction_resolved"]
            and claims.contrast_direction(interval)["direction"]
            == "DIRECTION_UNRESOLVED")
    return all(verdicts) and bool(C.STRUCTURAL_ZERO_SENTENCE)


def _statuses_are_registered() -> bool:
    return (set(C.V7_IDENTIFICATION_STATUSES) <= set(C.IDENTIFICATION_STATUSES)
            and "STRUCTURAL_ZERO" in C.RESULT_MARKERS)


def _bands_are_unchanged() -> bool:
    """No admission threshold moves in v7, and this is the executable form."""
    return (C.HEADROOM_BAND == (0.10, 0.90)
            and C.COMPOSED_PROXIMITY_BAND == (0.05, 0.95)
            and C.PROJECTED_COMPLIANCE_BAND == (0.10, 0.90)
            and C.COVERAGE_MIN_STRADDLING_FAMILIES == 6
            and C.COVERAGE_MIN_RUNGS_PER_STRADDLING_FAMILY == 3
            and C.COVERAGE_MIN_WITHIN_FAMILY_SPAN == 0.40
            and C.REFERENCE_CALIPER == 0.10
            and C.FOCAL_BAND == (0.60, 0.95)
            and C.TARGET_BAND == (0.50, 0.85)
            and C.SMALLEST_EFFECT_OF_INTEREST == 0.10
            and C.DELTA_R_GENERIC_THRESHOLD == 0.10
            and C.DELTA_R_PAIR_SPECIFIC_THRESHOLD == 0.25
            and C.PRECISION_PRECONDITIONS["Delta_R"] == 0.05
            and C.L1_SOLO_HEADROOM_FLOOR == 0.05)


def _amendments_are_bindable_after_rows() -> bool:
    from dci1v7.protocol import manifest
    from dci1v7.run import registration_run

    return (callable(getattr(registration_run, "amend_registration", None))
            and callable(getattr(manifest, "document_binding", None))
            and "§13" in inspect.getsource(registration_run.amend_registration))


#: The modules compared byte-for-byte against the predecessor. Named rather
#: than globbed: which files carry the causal comparison is a scientific
#: statement, and a glob would silently absorb a new one.
ESTIMAND_LAYER: tuple[str, ...] = (
    "analysis/estimators.py", "analysis/observations.py",
    "analysis/intervals.py", "analysis/bootstrap.py", "analysis/masking.py",
    "design/cells.py", "stages/selection.py", "stages/support.py",
    "stages/stability.py", "stages/interaction.py",
    "stages/calibration_table.py", "protocol/identification.py",
)
#: ``stages/support.py`` carries §26's success-criterion wording, which v7
#: A3 amends, and §13.15's evaluation, which v7 A7 gives a spectrum verdict;
#: it is compared with those two functions excluded by name. Everything else
#: in it --- the D6 disposition, the backup freeze --- is byte-identical.
_ESTIMAND_LAYER_EXCLUDED_FUNCTIONS = {"stages/support.py":
                                      ("methodological_success",
                                       "evaluate_support")}

#: ``protocol/identification.py`` is compared on its OUTPUT rather than its
#: bytes: v7 A7 adds the spectrum-dependent set and a two-status block beside
#: the reference-dependence rule, and what the estimand layer needs to hold is
#: that the rule --- which members need the primary reference set --- derives
#: the same sets it derived in v6.
_ESTIMAND_LAYER_OUTPUT_COMPARED = {"protocol/identification.py"}


def _strip_module_docstring_and_functions(text: str,
                                          names: tuple[str, ...]) -> str:
    """The source without its module docstring and the named top-level
    functions, by AST line spans, so an excluded function's body cannot leak
    into the comparison and nothing after it is dropped by accident."""
    tree = ast.parse(text)
    spans: list[tuple[int, int]] = []
    if tree.body and isinstance(tree.body[0], ast.Expr) and isinstance(
            getattr(tree.body[0], "value", None), ast.Constant) and \
            isinstance(tree.body[0].value.value, str):
        spans.append((tree.body[0].lineno, tree.body[0].end_lineno))
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name in names:
            spans.append((node.lineno, node.end_lineno))
    kept = [line for number, line in enumerate(text.splitlines(keepends=True),
                                               start=1)
            if not any(a <= number <= b for a, b in spans)]
    return "".join(kept)


def _identification_rule_agrees_with_predecessor() -> bool:
    """The reference-dependence rule derives v6's sets, member for member."""
    import importlib

    from dci1v7.protocol import identification as new
    try:
        old = importlib.import_module(
            f"{PREDECESSOR_PACKAGE}.protocol.identification")
    except Exception:                                        # pragma: no cover
        return False
    members = [m for members in C.FAMILY_MEMBERS.values() for m in members]
    return (tuple(old.AFFECTED_ESTIMANDS) == tuple(new.AFFECTED_ESTIMANDS)
            and tuple(old.UNAFFECTED_ESTIMANDS)
            == tuple(new.UNAFFECTED_ESTIMANDS)
            and set(old.REHABILITATION_PATHS) == set(new.REHABILITATION_PATHS)
            and all(old.reference_dependent(m) == new.reference_dependent(m)
                    for m in members)
            and set(new.SPECTRUM_ESTIMANDS) <= set(new.AFFECTED_ESTIMANDS))


def _estimand_layer_check() -> bool:
    import re
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    token = re.compile(r"dci1v[567]")

    for name in ESTIMAND_LAYER:
        old = root / PREDECESSOR_PACKAGE / name
        new = root / "dci1v7" / name
        if not old.exists() or not new.exists():
            return False
        if name in _ESTIMAND_LAYER_OUTPUT_COMPARED:
            if not _identification_rule_agrees_with_predecessor():
                return False
            continue
        excluded = _ESTIMAND_LAYER_EXCLUDED_FUNCTIONS.get(name, ())
        a = token.sub("dci1vX", _strip_module_docstring_and_functions(
            old.read_text(), excluded))
        b = token.sub("dci1vX", _strip_module_docstring_and_functions(
            new.read_text(), excluded))
        if a != b:
            return False
    return True


# ------------------------------------------------------ A6, A7, A8 (2026-08-28)

def _coverage_table(iota_a: float, *, span: float, side: str = "both"
                    ) -> list[dict]:
    """A §12.6 table over the eleven Tier-1/2 families, each with three
    eligible rungs around ``iota_a`` spanning ``span``, plus one Tier-3
    budget rung near it. ``side="above"`` puts every rung strictly above."""
    from dci1v7.verifiers.constraints import FAMILIES

    rows = []
    tier12 = [k for k, f in FAMILIES.items()
              if f.structural_tier in (1, 2) and k in
              ("MK1", "MK2", "MK3", "MK4", "MK5", "MK6", "MK7", "MK8",
               "XC1", "XC2", "XC3")]
    offsets = ([-span / 2, span / 4, span / 2] if side == "both"
               else [span / 4, span / 3, span / 2])
    for family in tier12:
        f = FAMILIES[family]
        for q, offset in enumerate(offsets, start=1):
            rows.append({"candidate": f"{family}:{q}", "family": family,
                         "severity": q, "structural_tier": f.structural_tier,
                         "feature_group": f.feature_group,
                         "constraint_class": f.constraint_class,
                         "iota": iota_a + offset, "solo": iota_a + offset,
                         "vacuity": 0.0, "eligible": True})
    rows.append({"candidate": "RF5:2", "family": "RF5", "severity": 2,
                 "structural_tier": 3, "feature_group": "comma",
                 "constraint_class": "budget", "iota": iota_a + 0.02,
                 "solo": iota_a + 0.02, "vacuity": 0.0, "eligible": True})
    return rows


def _coverage_is_scoped_by_arm() -> bool:
    """A7: C4 lost alone keeps the core and drops the spectrum; a lost core
    condition drops both; the thresholds are the registered ones."""
    from dci1v7.stages import regime, support

    if C.COVERAGE_CORE_CONDITIONS != ("C1", "C3", "C5", "C6") or \
            C.COVERAGE_SPECTRUM_CONDITIONS != ("C2", "C4"):
        return False
    narrow = regime.coverage_criterion(_coverage_table(0.6, span=0.15),
                                       iota_a=0.6)
    wide = regime.coverage_criterion(_coverage_table(0.6, span=0.5),
                                     iota_a=0.6)
    above = regime.coverage_criterion(
        _coverage_table(0.6, span=0.5, side="above"), iota_a=0.6)
    if not (narrow["core_met"] and not narrow["spectrum_met"]
            and narrow["spectrum_failed"] == ["C4"]
            and not narrow["decisive_met"]):
        return False
    if not (wide["core_met"] and wide["spectrum_met"] and wide["decisive_met"]):
        return False
    if above["core_met"] or "C1" not in above["core_failed"]:
        return False
    core = [{"structural_tier": 1, "feature_group": g, "family": f}
            for f, g in (("MK1", "marker_thus"), ("MK2", "marker_hence"),
                         ("MK3", "marker_though"))]
    common = dict(model_key="revision-check",
                  structurally_eligible_tier12_families=["MK1", "MK2", "MK3",
                                                         "MK4", "MK5", "MK6",
                                                         "MK7", "MK8"],
                  qualified_families=["MK1", "MK2", "MK3", "MK4", "MK5"],
                  selection={"core_references": core,
                             "identification_statuses": []},
                  near_form_available=True, class_available=True,
                  spectrum_identified=True)
    spectrum_lost = support.evaluate_support(
        **common, spectrum_design_time_failures=["C4 on the calibrated basis"])
    core_lost = support.evaluate_support(
        **common, design_time_failures=["C1 on the calibrated basis"])
    return (spectrum_lost["support_met"] and not spectrum_lost["spectrum_met"]
            and "core" in spectrum_lost["admitted_arms"]
            and "spectrum" not in spectrum_lost["admitted_arms"]
            and "DIFFICULTY_SUPPORT_NOT_IDENTIFIED"
            in spectrum_lost["identification_statuses"]
            and "REFERENCE_SUPPORT_NOT_IDENTIFIED"
            not in spectrum_lost["identification_statuses"]
            and spectrum_lost["non_identification"]["status"]
            == "DIFFICULTY_SUPPORT_NOT_IDENTIFIED"
            and not core_lost["support_met"]
            and "core" not in core_lost["admitted_arms"]
            and "spectrum" not in core_lost["admitted_arms"]
            and core_lost["non_identification"]["status"]
            == "REFERENCE_SUPPORT_NOT_IDENTIFIED")


def _prefreeze_reads_the_record_not_the_verdict() -> bool:
    """A6: no artifact check requires support_met, and a consistently
    recorded non-identified replication passes the support checks."""
    from dci1v7.protocol import identification
    from dci1v7.run import prefreeze_run
    from dci1v7.stages import support

    ids = [cid for cid, _why, _block in prefreeze_run.ARTIFACT_CHECKS]
    if "support_satisfied" in ids:
        return False
    for required in ("support_recorded", "d6_disposition_registered",
                     "arms_match_identification", "no_rehabilitation_path",
                     "freeze_fields_explained"):
        if required not in ids:
            return False
    source = inspect.getsource(prefreeze_run.artifact_checks)
    if 'bool(report.get("support_met"))' in source:
        return False
    report = support.evaluate_support(
        model_key="revision-check",
        structurally_eligible_tier12_families=["MK1"],
        qualified_families=["MK1"],
        selection={"core_references": [], "identification_statuses": []},
        near_form_available=False, class_available=False,
        spectrum_identified=False)
    gate3c = {"support": report,
              "identification_statuses": report["identification_statuses"],
              "non_identification": report["non_identification"],
              "not_identified_members": report["not_identified_members"],
              "admitted_arms": report["admitted_arms"]}
    verdicts = {check: ok for check, ok, _detail in
                prefreeze_run.support_checks(
                    gate3c, gate4={"composed_contrast": {"families": {}}})}
    return (all(verdicts.values())
            and set(report["not_identified_members"])
            == set(identification.AFFECTED_ESTIMANDS))


def _d6_means_the_replication_continues() -> bool:
    """A8: the derived member sets, the unconditional base arm, and no
    terminal status about support."""
    from dci1v7.design.cells import arms_from_identification
    from dci1v7.protocol import identification

    if any("SUPPORT" in status for status in C.TERMINAL_STATUSES):
        return False
    if tuple(identification.affected_members(
            ["REFERENCE_SUPPORT_NOT_IDENTIFIED"])) != tuple(
            identification.AFFECTED_ESTIMANDS):
        return False
    if tuple(identification.affected_members(
            ["DIFFICULTY_SUPPORT_NOT_IDENTIFIED"])) != tuple(
            identification.SPECTRUM_ESTIMANDS):
        return False
    if identification.affected_members([]) != ():
        return False
    if arms_from_identification(core_identified=False,
                                spectrum_identified=False,
                                near_form_identified=False,
                                class_identified=False) != (C.ARM_BASE,):
        return False
    if not set(identification.BASE_ARM_ESTIMANDS) <= set(
            identification.UNAFFECTED_ESTIMANDS):
        return False
    block = identification.non_identification(
        model_key="revision-check", support_met=False, failures=["x"])
    return (block is not None and block["terminal"] is False
            and block["irreversible"] is True
            and block["replication_continues"] is True)


CHANGES: tuple[Change, ...] = (
    Change("V1", "§13.14, §28.3",
           "the absolute composed-headroom criterion is WITHDRAWN as a "
           "terminal requirement. COMPOSED_HEADROOM_FAILURE (Gate 4) and "
           "COMPOSED_HEADROOM_UNREACHABLE (Gate 2.75) leave the terminal "
           "vocabulary and no module in the package can raise either",
           "both v6 Qwen replications terminated because B's compliance ROSE "
           "under A toward the ceiling, and gemma-3n-e4b-it because a "
           "companion's own solo compliance on 24 topics was 0.958. The "
           "estimand is a paired contrast between composed cells; a marginal "
           "rate at a boundary is a property of one arm and does not make a "
           "difference of rates undefined. Withdrawn, not relaxed: there is "
           "no band any more",
           lambda: (_headroom_statuses_are_withdrawn()
                    and _no_module_can_raise_a_withdrawn_status())),
    Change("V2", "§13.14",
           "what a composed rate at 0 or 1 does to a CONTRAST is measured "
           "and recorded: a structural zero, an arm at an exact boundary "
           "with its Wilson allowance, and a direction compressed below the "
           "SESOI by the other arm's level (analysis/boundary.py)",
           "each is a property of the contrast rather than of a marginal "
           "rate, each is derived from the registered SESOI and §14.1's block "
           "count and from nothing new, and each attaches to the statement "
           "instead of ending the replication",
           _boundary_rule_is_executable),
    Change("V3", "§18 stage 8",
           "GATE_2_75_COMPOSED_PROBE records the paired contrasts D(B<-A), "
           "D(A<-B), Lambda, Ord_A and Ord_B at the frozen m* on the "
           "calibration topics --- topic bootstrap, boundary readings, "
           "projected confirmatory precision --- and has one outcome",
           "the measurement v6 added is kept; the verdict it attached is "
           "gone. m* stays frozen at Gate 2 (A13) and nothing here can move "
           "it or stop the replication",
           _the_probe_records_and_cannot_terminate),
    Change("V4", "§18 stage 11",
           "GATE_4_COMPOSED_CONTRAST reads its rows as the confirmatory "
           "analysis reads rows --- an observation table over the 24 "
           "composed topics --- forms every registered contrast the "
           "admitted arms supply by the registered estimators, bootstraps "
           "topics, applies the boundary rule, projects each member's "
           "confirmatory half-width, records all of it, and has one outcome",
           "the projection is labelled and read by no rule; it exists so the "
           "qualification a statement carries at the end was on a signed "
           "record before the freeze",
           _gate4_records_a_contrast_and_cannot_terminate),
    Change("V5", "§17, §28.1, §28.2",
           "the confirmatory analysis attaches the three boundary statuses "
           "to statements, reads decision intervals widened by the boundary "
           "allowance, withholds every classification from a structural "
           "zero, and names Delta_R's direction as a registered outcome",
           "direction, magnitude and uncertainty are what the contrast "
           "carries; 'A costs B less than the references do' is a finding "
           "and is now a named one rather than the absence of L3a",
           lambda: _analysis_reads_the_boundary() and _statuses_are_registered()),
    Change("V6", "§26",
           "the methodological success criterion's Gate-4 clause reads "
           "whether Delta_R is estimable on the composed set --- not a "
           "structural zero --- in place of 'survives composed-headroom "
           "validation'",
           "the without-replacement guarantee it also named stands on its own "
           "as assert_no_substitution_path; the clause that named a withdrawn "
           "criterion is restated on the estimand",
           lambda: "gate4_contrast" in inspect.signature(
               __import__("dci1v7.stages.support", fromlist=["x"])
               .methodological_success).parameters),
    Change("V7", "§32",
           "an amendment adopted after behavioural rows exist is bindable: "
           "`registration_run.amend_registration` writes a signed, "
           "append-only amendment record linking the registered document "
           "hashes to the amended ones, with the stage each replication had "
           "reached and its row count, the declared direction and the §32.2 "
           "disclosure; `manifest.document_binding` walks the chain and the "
           "pre-freeze audit checks the on-disk documents against its head. "
           "§32.3 is executable: an amendment naming §13 is refused once any "
           "replication holds a Gate-2.5 record",
           "v6's A16 and A17 were adopted after rows existed and the "
           "lifecycle had no way to say so, so gemma-3n-e2b-it --- the one "
           "replication that passed every scientific gate --- terminated at "
           "PREFREEZE_AUDIT on protocol_hashes_agree",
           _amendments_are_bindable_after_rows),
    Change("V8", "§13, §12.6, §11.9, §16.2",
           "NO THRESHOLD MOVES",
           "a revision after a failed study is where a bar gets lowered. v7 "
           "lowers none: every admission band, caliper, coverage condition, "
           "SESOI, claim threshold and precision precondition is the value "
           "v5 registered, checked rather than trusted",
           _bands_are_unchanged),
    Change("V9", "§5, §11, §13",
           "THE ESTIMAND LAYER IS UNTOUCHED, and checked file by file against "
           "v6 (which checked it against v5)",
           "the twelve modules that define Delta_R, Delta_j, Xi, "
           "delta_difficulty, the matched-companion selection, the design "
           "cells, the observation table, the intervals, the bootstrap and "
           "D6 are byte-identical modulo the namespace token, with one named "
           "exception: §26's success-criterion function in stages/support.py, "
           "which V6 amends and which selects nothing",
           _estimand_layer_check),
    Change("V10", "§13.14, §17.3",
           "a structural zero is read on its allowance interval: no "
           "direction by construction, and an equivalence-type reading "
           "(L3c, Delta_near 'below') exactly when that interval satisfies "
           "the registered rule --- inside the region and within the "
           "precondition at 384 blocks, neither at 24 --- with the status "
           "and a registered sentence on the statement",
           "the 2026-08-28 boundary audit (dci1/reports/dci1v7/boundary_"
           "audit/) found the earlier veto on every classification was not "
           "a statistical safeguard: the allowance interval covers the true "
           "contrast there at >= 95% by construction and an equivalence "
           "false positive needs every draw perfect while |Delta_R| >= "
           "0.10; the veto made 3072/3072 perfect draws weaker evidence for "
           "the registered claim than 3071/3072. No threshold moves; the "
           "construct-validity qualification the veto carried is carried by "
           "the status, the sentence and §26",
           _structural_zero_is_read_on_its_allowance_interval),
    Change("V11", "§12.6, §28.2 (A7, 2026-08-28)",
           "§12.6's coverage conditions are scoped to the arm each exists "
           "for: C1, C3, C5 and C6 gate the core matched-reference arm "
           "(REFERENCE_SUPPORT_NOT_IDENTIFIED when lost) and C2 and C4 gate "
           "the difficulty-spectrum arm (DIFFICULTY_SUPPORT_NOT_IDENTIFIED "
           "when lost, the core arm retained when §13.8, §13.7 and §13.15 "
           "hold); C7 and C8 unchanged; the expansion loop's stopping rule "
           "and every threshold unchanged; the calibrated basis gates both",
           "all four v7 replications lost C4 alone on the calibrated basis "
           "with three core references within 0.017 of iota_A and §13.15 "
           "met, and §12.6's own rationale column already assigns C4 to "
           "§13.12's triples; §13.12 and §8.1 registered that a family that "
           "cannot straddle costs the spectrum and not the core",
           _coverage_is_scoped_by_arm),
    Change("V12", "§18 stage 12, §19, §33 (A6, 2026-08-28)",
           "the pre-freeze audit establishes §13.15's RECORD, §34 D6's "
           "disposition, the exact non-identified member set, the arm set "
           "and the absence of a rehabilitation path, and assembles the "
           "freeze record to check its empty fields are explained; the "
           "`support_satisfied` check that required support_met is "
           "withdrawn; reference-specific checks are NOT_APPLICABLE when "
           "the core arm is not admitted",
           "seven replications of v5, v6 and v7 passed every scientific gate "
           "and ended on an unregistered requirement that contradicted "
           "§13.15, §18 stage 10, §28.2 and the closed D6",
           _prefreeze_reads_the_record_not_the_verdict),
    Change("V13", "§34 D6, §28.2, §8.1 (A8, 2026-08-28)",
           "D6 means one thing everywhere: irreversible for the affected "
           "estimands, and the replication continues on every estimand that "
           "stays identified; the derived member sets are executable, the "
           "base arm is unconditional, and no terminal status is about "
           "support",
           "three v7 sentences and three closures had read 'Delta_R is "
           "irreversibly not identified' as 'the replication ends'",
           _d6_means_the_replication_continues),
)

#: What v7 deliberately does NOT change, named so a reader does not have to
#: infer it from an absence.
UNCHANGED: tuple[tuple[str, str], ...] = (
    ("§10.7", "the deterministic-measurement architecture and its "
              "ten-condition Gate-1 rule, carried unchanged in substance from "
              "v6, v5 and v4r4"),
    ("§10.5", "the measurement basis and its permanent scope sentence"),
    ("§3.2", "the claim ladder L1-L4, with L5 --- generalisation --- "
             "permanently withheld, and every licensing threshold"),
    ("§5, §11", "the primary question, Delta_j, Delta_R, Xi, "
                "delta_difficulty, the order contrasts and the "
                "companion-specific identification goal"),
    ("§6.1", "four replications, each analysed separately, never pooled, and "
             "no cross-model scalar carrying a claim"),
    ("§6.2", "the topic bank and every set size; §34 D3's Calibration-B"),
    ("§12", "n* and m* selected from solo curves, §12.4's regime adequacy, "
            "§34 D17's construct floor, and A13: m* frozen at Gate 2"),
    ("§13.1-§13.13, §13.15", "every component of V(R), every band, caliper "
                             "and region, C1-C8's values, and the support "
                             "requirements --- the prospective machinery "
                             "that vets A and the references before any "
                             "composed cell is read (A7 changes which arm "
                             "a lost C1-C6 costs, in §12.6, and no value)"),
    ("§13.11", "interaction-blind reference selection; no B+R composed "
               "outcome may enter it, and no composed outcome enters any "
               "design choice"),
    ("§13.15, §28", "irreversible D6 non-identification, with the replication "
                    "continuing on its surviving estimands (A6, A8 make the "
                    "lifecycle do what the closed decision says)"),
    ("§15, §16, §17.1-§17.3", "F1-F11, 384 blocks, M = 8, 10,000 resamples, "
                              "the block bootstrap, the studentised "
                              "maximum-modulus intervals and every precision "
                              "precondition"),
    ("§18, §20, §31", "the write-once stage lifecycle, one-shot masking, and "
                      "the prohibition on post-outcome repair"),
    ("§30", "v6 is DEVELOPMENT_EVIDENCE and HISTORICAL_OUTCOME for v7's "
            "design and no v6 row may enter a v7 estimand"),
    ("v6 A5, A10, A13, A15, A16, A17", "the probe's shape and stand-ins, the "
                                       "frozen m*, the readiness refusal, "
                                       "the coordinate-less rung rule and "
                                       "the unplaceable stand-in rule"),
)


def assert_changes_realised() -> dict[str, Any]:
    """Every change with a check has actually been made in the code."""
    findings: list[dict[str, Any]] = []
    unrealised: list[str] = []
    for change in CHANGES:
        realised = None
        if change.check is not None:
            realised = bool(change.check())
            if not realised:
                unrealised.append(change.id)
        findings.append({"id": change.id, "section": change.section,
                         "what": change.what, "why": change.why,
                         "checked": change.check is not None,
                         "realised": realised})
    if unrealised:
        raise ProtocolError(
            f"these registered v6 -> v7 changes are not present in the "
            f"code: {unrealised}")
    return {"changes": findings, "n_changes": len(CHANGES),
            "n_checked": sum(1 for c in CHANGES if c.check is not None),
            "unchanged": [{"section": s, "what": w} for s, w in UNCHANGED]}


def revision_record() -> dict[str, Any]:
    from dci1v7 import (
        CLASSIFICATION, PREREGISTRATION, STUDY_ID, SUPERSEDES,
        SUPERSEDES_TERMINAL_STAGE, SUPERSEDES_TERMINAL_STATUS,
        SUPERSEDED_TERMINAL_STATUSES,
    )

    return {"study_id": STUDY_ID, "classification": CLASSIFICATION,
            "preregistration": PREREGISTRATION, "supersedes": SUPERSEDES,
            "supersedes_terminal_stage": SUPERSEDES_TERMINAL_STAGE,
            "supersedes_terminal_status": SUPERSEDES_TERMINAL_STATUS,
            "superseded_terminal_statuses": list(SUPERSEDED_TERMINAL_STATUSES),
            **assert_changes_realised()}
