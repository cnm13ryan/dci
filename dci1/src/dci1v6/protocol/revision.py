"""What v6 changes from v5, enumerated where the code can read it.

A revision that lists its changes only in prose has no way to check that the
code made them. Every entry carries the **section it is registered under** and,
where the change is executable, a callable that returns True only when the code
actually carries it. ``assert_changes_realised`` is on the registration path,
so a listed change the code does not make stops stage 1.

**v6 is a small revision on purpose.** The scientific question, the estimands,
every threshold, the claim ladder with L5 permanently withheld, F1-F11,
interaction-blind reference selection, the prohibition on a B+R composed
outcome entering selection, irreversible D6, the prospective freeze, one-shot
masking and §31's no-repair rule are all carried from v5 **unchanged**. What
changes is listed below and nothing else. Two of the four entries are repairs
to mechanisms that could not deliver what a registered rule already asked of
them, and are documented in ``dci1/reports/dci1v6/READINESS.md`` and
``CHANGES_SCIENTIFIC.md``.

Ordinary refactors and re-namespacing are not changes and are not listed.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from dci1v4.errors import ProtocolError

from dci1v6.protocol import constants as C
from dci1v6.verifiers.constraints import RESERVES

__all__ = ["Change", "CHANGES", "UNCHANGED", "assert_changes_realised",
           "revision_record"]


@dataclass(frozen=True)
class Change:
    id: str
    section: str
    what: str
    why: str
    #: A callable returning True when the code actually carries the change.
    check: Any = None


def _expansion_can_raise_a_span() -> bool:
    """V6-E01's repair: a SPAN_SHORT family extends outward, not inward.

    C4's span is ``max(iota) - min(iota)`` over a family's eligible rungs, so
    a rung admitted strictly between two measured edges cannot raise it. v5's
    rule had no outward branch at all and admitted no Tier-1 reserve rung on
    any replication. The check is behavioural, on a synthetic family whose
    measured rungs straddle iota_A with a short span.
    """
    from dci1v6.stages.regime import (
        expansion_plan_for_family, family_deficiency, family_c4_state)

    family, iota_a = "MK1", 0.60
    rows = [{"family": family, "severity": q, "iota": v, "eligible": True}
            for q, v in ((3, 0.70), (4, 0.66), (5, 0.55))]
    state = family_c4_state(rows, iota_a=iota_a)
    if family_deficiency(state) != "SPAN_SHORT":
        return False
    plan = expansion_plan_for_family(family, entries=rows,
                                     measured=[3, 4, 5], iota_a=iota_a)
    reserve = set(RESERVES[family]) - {3, 4, 5}
    return (plan["direction"] == "OUTWARD_BOTH"
            and bool(plan["picks"])
            and set(plan["picks"]) <= reserve
            and any(q > 5 for q in plan["picks"]))


def _coverage_shape_is_a_contract() -> bool:
    """V6-E02's repair: a row the criterion would silently drop is refused."""
    from dci1v4.errors import ProtocolError
    from dci1v6.stages.regime import assert_coverage_shape

    try:
        assert_coverage_shape(
            [{"family": "MK1", "severity": 1, "iota": 0.5}], where="check")
    except ProtocolError:
        return True
    return False


def _nineteen_stages_with_the_probe() -> bool:
    sequence = C.STAGE_SEQUENCE
    return (len(sequence) == 19
            and sequence[0] == C.STAGE_REGISTERED
            and sequence.index(C.STAGE_GATE2_75)
            == sequence.index(C.STAGE_GATE2_5) + 1
            and sequence.index(C.STAGE_GATE3A)
            == sequence.index(C.STAGE_GATE2_75) + 1
            and C.STAGE_GATE2_75 in C.GENERATION_STAGES)


def _headroom_unreachable_is_registered() -> bool:
    from dci1v6.stages.composed_probe import COMPOSED_HEADROOM_UNREACHABLE
    return COMPOSED_HEADROOM_UNREACHABLE in C.TERMINAL_STATUSES


def _probe_only_is_excluded_from_selection() -> bool:
    """A stand-in is not in the selectable pool, whatever else is true."""
    from dci1v6.verifiers.constraints import (
        FAMILY_IDS, PROBE_ONLY_FAMILY_IDS, SELECTABLE_FAMILY_IDS,
        assert_no_probe_only_selection_path)

    assert_no_probe_only_selection_path()
    return (set(SELECTABLE_FAMILY_IDS) | set(PROBE_ONLY_FAMILY_IDS)
            == set(FAMILY_IDS)
            and not (set(SELECTABLE_FAMILY_IDS) & set(PROBE_ONLY_FAMILY_IDS)))


def _name_scan_reads_the_probe_record() -> bool:
    from dci1v6.stages.audit_prefreeze import NAME_SCANNED_RECORDS
    return C.STAGE_GATE2_75 in NAME_SCANNED_RECORDS


def _bands_are_unchanged() -> bool:
    """No threshold moves in v6, and this is the executable form of it."""
    return (C.HEADROOM_BAND == (0.10, 0.90)
            and C.COMPOSED_HEADROOM_BAND == (0.05, 0.95)
            and C.COVERAGE_MIN_STRADDLING_FAMILIES == 6
            and C.COVERAGE_MIN_RUNGS_PER_STRADDLING_FAMILY == 3
            and C.COVERAGE_MIN_WITHIN_FAMILY_SPAN == 0.40
            and C.REFERENCE_CALIPER == 0.10
            and C.FOCAL_BAND == (0.60, 0.95)
            and C.TARGET_BAND == (0.50, 0.85))


def _l4a_is_within_replication() -> bool:
    from dci1v6.analysis import claims
    claims.assert_configuration_scope()
    return claims.CONFIGURATION_SCOPE == "within_replication"


CHANGES: tuple[Change, ...] = (
    Change("V1", "§12.6",
           "§12.6's expansion evaluates C4's three conditions per family and, "
           "when the deficiency is a SHORT SPAN, extends outward from both "
           "measured extremes instead of interpolating",
           "replayed on all four signed v5 pre-screen tables, v5's rule "
           "admitted ZERO Tier-1 reserve rungs in either round --- and §7.10 "
           "had widened that reserve from 1..10 to 1..12 for C4's span "
           "specifically. Interpolation cannot raise max(iota) - min(iota) at "
           "all, so on the one condition three replications failed the "
           "mechanism was incapable of helping by construction (V6-E01). "
           "C4 itself is unchanged",
           _expansion_can_raise_a_span),
    Change("V2", "§12.6",
           "``run_expansion`` requires its measured rows in the criterion's "
           "own shape and ``assert_coverage_shape`` refuses any other",
           "v5 extended its working table with raw difficulty rows carrying "
           "no ``eligible`` field, and ``coverage_criterion`` filters on "
           "``eligible`` first --- so every rung the expansion measured was "
           "counted as ineligible by the criterion it was measured to satisfy "
           "(V6-E02). Three v5 replications spent 93 to 99 reserve rungs that "
           "their own recorded coverage never saw",
           _coverage_shape_is_a_contract),
    Change("V3", "§18, §13.14",
           "a nineteenth stage, GATE_2_75_COMPOSED_PROBE, between Gate 2.5 "
           "and Gate 3A, measuring composed compliance headroom at m* "
           "against probe-only stand-ins before any reference exists",
           "m* is chosen at Gate 2 from B's SOLO curve and §13.14 checks the "
           "composed cells only after selection; all four v5 replications sat "
           "within 0.054 of the ceiling or over it once B was composed. The "
           "measurement was available two stages earlier",
           _nineteen_stages_with_the_probe),
    Change("V4", "§28",
           "COMPOSED_HEADROOM_UNREACHABLE is a registered terminal status",
           "the probe permits exactly one re-selection of m*, by a rule fixed "
           "before data; when no severity Gate 2 found eligible satisfies the "
           "margin the replication stops. A repair loop with no terminal "
           "outcome is not a rule",
           _headroom_unreachable_is_registered),
    Change("V5", "§7.10, §13.11",
           "``probe_only`` families exist as a category and are excluded by "
           "construction from every selectable pool",
           "timing already keeps the probe blind to references --- it runs "
           "before Gate 3A --- and this makes instrument identity a second, "
           "independent guarantee, so both would have to fail for a probed "
           "cell to be a B+R cell. Which stand-ins exist is §34 D24 and no "
           "probe-only family is authored yet",
           _probe_only_is_excluded_from_selection),
    Change("V6", "§33",
           "check 8's name scan reads the Gate-2.75 record on the same terms "
           "as the Gate-4 record, with its own declared refusals",
           "v5's check 8 read the Gate-4 record and nothing else. v6 adds a "
           "generating stage before reference selection, and a record no name "
           "scan reads is the one place an outcome-driven selection could be "
           "introduced without the audit seeing it",
           _name_scan_reads_the_probe_record),
    Change("V7", "§15, §3.2",
           "L4a's configuration scope is stated and enforced as "
           "within-replication",
           "§11.1's glossary makes a configuration (model, position) while "
           "CONFIGURATIONS is position-only, and a caller who widened L4a's "
           "set to span models would emit the cross-model replication claim "
           "§6.1 forbids and L5 permanently withholds --- through a data "
           "shape rather than a registered rule. §15 settles the reading; "
           "this makes it executable. NOT a change to what L4a means",
           _l4a_is_within_replication),
    Change("V8", "§13, §12.6",
           "NO THRESHOLD MOVES",
           "v5 failed on C4 and on §13.14's band, and the temptation a "
           "revision after a failed study faces is to move the bar that "
           "failed. Every v6 change adds measurement or supply, or repairs a "
           "mechanism that could not deliver what a registered rule asked. "
           "This entry is here so that the absence is checked rather than "
           "trusted",
           _bands_are_unchanged),
)

#: What v6 deliberately does NOT change, named so a reader does not have to
#: infer it from an absence. Everything v5 carried unchanged from v4r4 is
#: carried again; only what v5 itself introduced is restated here.
UNCHANGED: tuple[tuple[str, str], ...] = (
    ("§10.7", "the deterministic-measurement architecture and its "
              "ten-condition Gate-1 rule, carried unchanged in substance from "
              "v5, which carried it unchanged from v4r4"),
    ("§10.5", "the measurement basis and its permanent scope sentence: v6's "
              "Gate 1 can write deterministic_measurement_validated and not "
              "human_validated"),
    ("§3.2", "the claim ladder L1-L4, with L5 --- generalisation --- "
             "permanently withheld"),
    ("§5, §11", "the primary question, Delta_j, Delta_R, Xi, "
                "delta_difficulty and the companion-specific identification "
                "goal"),
    ("§6.1", "four replications, each analysed separately, never pooled, and "
             "no cross-model scalar carrying a claim"),
    ("§13.4, §13.8, §13.14", "every band, caliper and region: [0.10, 0.90], "
                             "0.10 and the 0.05 Newcombe region, "
                             "[0.05, 0.95]"),
    ("§12.6", "C4's >= 6 straddling groups, >= 3 rungs per family and "
              ">= 0.40 within-family span"),
    ("§13.11", "interaction-blind reference selection; no B+R composed "
               "outcome may enter it"),
    ("§13.15, §28", "irreversible D6 non-identification"),
    ("§15", "F1-F11 and the multiplicity structure"),
    ("§16", "384 blocks, M = 8, 10,000 resamples; no v5 effect estimate "
            "enters any sample-size calculation --- there are none"),
    ("§18, §20, §31", "the write-once stage lifecycle, one-shot masking, and "
                      "the prohibition on post-outcome repair"),
    ("§30", "v5 is DEVELOPMENT_EVIDENCE for v6's design and no v5 row may "
            "enter a v6 estimand"),
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
            f"these registered v5 -> v6 changes are not present in the "
            f"code: {unrealised}")
    return {"changes": findings, "n_changes": len(CHANGES),
            "n_checked": sum(1 for c in CHANGES if c.check is not None),
            "unchanged": [{"section": s, "what": w} for s, w in UNCHANGED]}


def revision_record() -> dict[str, Any]:
    from dci1v6 import (
        CLASSIFICATION, PREREGISTRATION, STUDY_ID, SUPERSEDES,
        SUPERSEDES_TERMINAL_STAGE, SUPERSEDES_TERMINAL_STATUS,
    )

    return {"study_id": STUDY_ID, "classification": CLASSIFICATION,
            "preregistration": PREREGISTRATION, "supersedes": SUPERSEDES,
            "supersedes_terminal_stage": SUPERSEDES_TERMINAL_STAGE,
            "supersedes_terminal_status": SUPERSEDES_TERMINAL_STATUS,
            **assert_changes_realised()}
