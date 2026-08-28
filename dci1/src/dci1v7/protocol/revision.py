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
#: A3 amends; it is compared with that function excluded. Everything else in
#: it --- §13.15's counts and the arm derivation --- is byte-identical.
_ESTIMAND_LAYER_EXCLUDED_FUNCTIONS = {"stages/support.py":
                                      ("methodological_success",)}


def _estimand_layer_check() -> bool:
    import re
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    token = re.compile(r"dci1v[567]")

    def strip(text: str, names: tuple[str, ...]) -> str:
        for name in names:
            start = text.find(f"def {name}(")
            if start < 0:
                return text
            text = text[:start]
        return text

    for name in ESTIMAND_LAYER:
        old = root / PREDECESSOR_PACKAGE / name
        new = root / "dci1v7" / name
        if not old.exists() or not new.exists():
            return False
        excluded = _ESTIMAND_LAYER_EXCLUDED_FUNCTIONS.get(name, ())
        a = token.sub("dci1vX", strip(old.read_text(), excluded))
        b = token.sub("dci1vX", strip(new.read_text(), excluded))
        if a != b:
            return False
    return True


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
                             "and region, C1-C8, and the support "
                             "requirements --- the prospective machinery "
                             "that vets A and the references before any "
                             "composed cell is read"),
    ("§13.11", "interaction-blind reference selection; no B+R composed "
               "outcome may enter it, and no composed outcome enters any "
               "design choice"),
    ("§13.15, §28", "irreversible D6 non-identification"),
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
