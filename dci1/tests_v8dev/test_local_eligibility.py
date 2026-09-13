"""The LOCAL frame-eligibility rule (researcher decision of 2026-08-31,
docs/V8_FRAME_CONDITIONING.md §4d), on the production functions.

The nine contracts the decision states:

1.  the *full* registered LOCAL reference survival is required for
    `LOCAL_SUPPORTED` --- each of the three requirements alone is not enough;
2.  a broad `LOCAL_AND_SPECTRUM` frame state is **not** sufficient;
3.  0 or 1 supported frames leaves the model ineligible;
4.  2 or more makes it eligible;
5.  every supported frame is included, not a subset;
6.  an unsupported frame never enters LOCAL confirmatory generation;
7.  there is no "best two frames" selection --- no ranking, no truncation,
    and no dependence on the order the frames arrive in;
8.  no pooled or cross-frame statistic determines support;
9.  no composed outcome can affect eligibility, and none is reachable.
"""
from __future__ import annotations

import copy
import itertools

import pytest

from dci1v4.errors import ProtocolError
from dci1v7.protocol import constants as C
from dci1v8dev import rules as R
from dci1v8dev.run import eligibility as EL
from dci1v8dev.run import references as REF
from dci1v8dev.run import stages as S


def survival(*, families: int = S.MIN_LOCAL_FAMILIES, core: bool = True,
             backups: int = S.MIN_BACKUPS, coverage: bool = True,
             **extra) -> dict:
    """A survival block carrying exactly the fields the rule reads."""
    return {
        "core_identified": core,
        "n_local_valid_families": families,
        "meets_min_local_families": families >= S.MIN_LOCAL_FAMILIES,
        "n_backups": backups,
        "meets_min_backups": backups >= S.MIN_BACKUPS,
        "coverage_identified": coverage,
        **extra,
    }


def by_frame(**per_frame) -> dict:
    """`{frame: survival}`; a frame given ``None`` had no operating point."""
    out = {}
    for w in S.FRAMES:
        s = per_frame.get(f"f{w}", "default")
        if s == "default":
            s = survival()
        out[str(w)] = {
            "frame": w, "survival": s,
            "status": S.FRAME_SUPPORTED if s is not None else S.FRAME_UNSUPPORTED,
            "state": ("LOCAL_AND_SPECTRUM" if s is not None
                      else S.FRAME_UNSUPPORTED),
            "unsupported_reason": (None if s is not None
                                   else {"status": "GRID_RESOLUTION_INSUFFICIENT"}),
        }
    return out


# ------------------------------------------------------------------------ 1

def test_full_reference_survival_is_required_for_local_supported():
    """Each of §13.8's core, §13.15's family count and the backup count is
    necessary. Dropping any one alone loses the frame, and the reason names
    exactly the requirement that was missed."""
    assert EL.local_support(survival(), frame=0)["local_supported"] is True

    cases = [
        (survival(core=False), EL.CORE_NOT_IDENTIFIED),
        (survival(families=S.MIN_LOCAL_FAMILIES - 1),
         EL.LOCAL_FAMILIES_BELOW_MINIMUM),
        (survival(backups=S.MIN_BACKUPS - 1), EL.BACKUPS_BELOW_MINIMUM),
    ]
    for block, reason in cases:
        verdict = EL.local_support(block, frame=0)
        assert verdict["local_supported"] is False
        assert verdict["local_support_state"] == EL.LOCAL_UNSUPPORTED
        assert verdict["local_unsupported_reason"] == reason
        assert verdict["local_unsupported_reasons"] == [reason]

    # every failure is listed, not only the first
    both = EL.local_support(survival(families=1, backups=0, core=False),
                            frame=0)
    assert both["local_unsupported_reasons"] == [
        EL.CORE_NOT_IDENTIFIED, EL.LOCAL_FAMILIES_BELOW_MINIMUM,
        EL.BACKUPS_BELOW_MINIMUM]

    # a frame with no operating point is unsupported for that reason, and
    # Gate 2's own status is carried rather than replaced
    none = EL.local_support(None, frame=2,
                            operating_point=S.FRAME_UNSUPPORTED,
                            unsupported_reason={"status": "FOCAL_RANGE_EXHAUSTED"})
    assert none["local_supported"] is False
    assert none["local_unsupported_reason"] == EL.NO_OPERATING_POINT
    assert none["gate2_unsupported_reason"]["status"] == "FOCAL_RANGE_EXHAUSTED"

    # the minima are the registered ones, not local copies
    assert S.MIN_LOCAL_FAMILIES == C.MIN_QUALIFIED_FAMILIES
    assert S.MIN_BACKUPS == C.N_BACKUP_FAMILIES


def test_a_record_that_does_not_state_a_requirement_is_refused():
    """Support is the *full* requirement, so a survival block missing one of
    the fields it is made of cannot be decided --- defaulting a missing
    requirement to met is exactly the failure this rule exists to prevent."""
    for field in ("core_identified", "meets_min_local_families",
                  "meets_min_backups"):
        block = survival()
        block.pop(field)
        with pytest.raises(ProtocolError, match=field):
            EL.local_support(block, frame=0)


# ------------------------------------------------------------------------ 2

def test_a_broad_local_and_spectrum_state_is_not_sufficient():
    """`LOCAL_AND_SPECTRUM` says the core was identified and the coverage
    gate passed. r8's `qwen3-4b-instruct-2507` f3 and `gemma-3n-e2b-it` f0
    reached it on four LOCAL-valid families and one backup, which is §13.15
    unsatisfied. Support must not follow the state."""
    weak = survival(families=4, backups=1, core=True, coverage=True)
    frames = by_frame(f0=weak, f1=weak, f2=weak, f3=weak)
    for entry in frames.values():
        assert entry["state"] == "LOCAL_AND_SPECTRUM"

    out = EL.local_eligibility(frames)
    assert out["local_supported_frames"] == []
    assert out["local_eligible"] is False
    for w in S.FRAMES:
        reasons = out["by_frame"][str(w)]["local_unsupported_reasons"]
        assert reasons == [EL.LOCAL_FAMILIES_BELOW_MINIMUM,
                           EL.BACKUPS_BELOW_MINIMUM]

    # and the converse: the spectrum arm is not a LOCAL requirement, so a
    # frame meeting all three LOCAL requirements is supported with the
    # coverage gate failing
    no_cov = EL.local_support(survival(coverage=False), frame=0)
    assert no_cov["local_supported"] is True


# --------------------------------------------------------------------- 3, 4

@pytest.mark.parametrize("n_supported,eligible", [(0, False), (1, False),
                                                  (2, True), (3, True),
                                                  (4, True)])
def test_the_minimum_is_two_independently_supported_frames(n_supported,
                                                           eligible):
    weak = survival(families=4, backups=1)
    per = {f"f{w}": (survival() if w < n_supported else weak)
           for w in S.FRAMES}
    out = EL.local_eligibility(by_frame(**per))
    assert out["n_local_supported_frames"] == n_supported
    assert out["local_eligible"] is eligible
    assert out["local_eligibility_min_frames"] == R.LOCAL_ELIGIBILITY_MIN_FRAMES
    assert R.LOCAL_ELIGIBILITY_MIN_FRAMES == 2
    # an ineligible model contributes no frame to LOCAL generation
    assert out["frames_entering_local_confirmatory"] == (
        out["local_supported_frames"] if eligible else [])


# ------------------------------------------------------------------------ 5

def test_every_supported_frame_is_included():
    """Three supported frames give three, not the two the minimum names."""
    per = {"f0": survival(families=9, backups=4),
           "f1": survival(families=5, backups=2),
           "f2": survival(families=4, backups=1),
           "f3": survival(families=7, backups=3)}
    out = EL.local_eligibility(by_frame(**per))
    assert out["local_supported_frames"] == [0, 1, 3]
    assert out["frames_entering_local_confirmatory"] == [0, 1, 3]
    assert len(out["frames_entering_local_confirmatory"]) > \
        R.LOCAL_ELIGIBILITY_MIN_FRAMES


# ------------------------------------------------------------------------ 6

def test_an_unsupported_frame_never_enters_local_confirmatory_generation():
    per = {"f0": survival(), "f1": survival(),
           "f2": None, "f3": survival(families=4, backups=1)}
    out = EL.local_eligibility(by_frame(**per))
    assert out["local_eligible"] is True
    entering = out["frames_entering_local_confirmatory"]
    assert 2 not in entering and 3 not in entering
    assert entering == [0, 1]
    # and they stay visible, each with the exact requirement it missed
    assert set(out["local_unsupported_frames"]) == {"2", "3"}
    assert out["local_unsupported_frames"]["2"]["local_unsupported_reason"] \
        == EL.NO_OPERATING_POINT
    assert out["local_unsupported_frames"]["3"]["local_unsupported_reasons"] \
        == [EL.LOCAL_FAMILIES_BELOW_MINIMUM, EL.BACKUPS_BELOW_MINIMUM]
    assert set(out["by_frame"]) == {str(w) for w in S.FRAMES}


# ------------------------------------------------------------------------ 7

def test_there_is_no_best_two_selection():
    """Support is a per-frame threshold, so it cannot rank, cannot truncate
    to the minimum, and cannot depend on the order the frames arrive in."""
    per = {"f0": survival(families=5, backups=2),
           "f1": survival(families=12, backups=6),
           "f2": survival(families=11, backups=5),
           "f3": survival(families=6, backups=3)}
    out = EL.local_eligibility(by_frame(**per))
    # the two *strongest* would be f1 and f2; all four are supported
    assert out["local_supported_frames"] == [0, 1, 2, 3]
    assert out["n_local_supported_frames"] == 4

    # making one frame arbitrarily stronger removes nobody
    stronger = copy.deepcopy(per)
    stronger["f1"] = survival(families=99, backups=99)
    assert EL.local_eligibility(by_frame(**stronger))["local_supported_frames"] \
        == [0, 1, 2, 3]

    # and the verdict is invariant to the order the frames are supplied in
    frames = by_frame(**per)
    for order in itertools.permutations(S.FRAMES):
        shuffled = {str(w): frames[str(w)] for w in order}
        assert EL.local_eligibility(shuffled)["local_supported_frames"] \
            == [0, 1, 2, 3]


def test_one_frame_never_decides_another():
    """Each frame's verdict is a function of that frame's own survival block.
    Changing every other frame leaves it exactly where it was."""
    base = by_frame(f0=survival(), f1=survival(families=4, backups=1),
                    f2=survival(), f3=survival())
    reference = EL.local_eligibility(base)["by_frame"]["1"]
    for variant in (survival(families=99, backups=99), None,
                    survival(families=0, backups=0, core=False)):
        moved = by_frame(f0=variant, f1=survival(families=4, backups=1),
                         f2=variant, f3=variant)
        assert EL.local_eligibility(moved)["by_frame"]["1"] == reference


# ------------------------------------------------------------------------ 8

def test_no_pooled_statistic_determines_support():
    """A pooled or cross-frame quantity on the record cannot move a verdict.
    Gate 3's `cross_frame` block and Gate 2's `descriptive_pooled` are
    descriptive by construction (V8_FRAME_CONDITIONING.md §8); this pins
    that the LOCAL rule cannot read them even if handed them."""
    per = {"f0": survival(), "f1": survival(),
           "f2": survival(families=4, backups=1), "f3": survival()}
    clean = EL.local_eligibility(by_frame(**per))

    polluted = by_frame(**per)
    for w, entry in polluted.items():
        entry["cross_frame"] = {"pooled_local_valid_families": 40,
                                "agreement": 1.0}
        entry["descriptive_pooled"] = {"n_local_valid_families": 40,
                                       "meets_min_local_families": True,
                                       "n_backups": 40}
        entry["survival"] = {**entry["survival"],
                             "pooled_n_local_valid_families": 40,
                             "all_frames_backups": 40}
    assert EL.local_eligibility(polluted) == clean

    # the aggregate over frames is a *count of per-frame verdicts*, never a
    # statistic pooled over frames' underlying rows
    assert clean["n_local_supported_frames"] == sum(
        1 for w in S.FRAMES if clean["by_frame"][str(w)]["local_supported"])


# ------------------------------------------------------------------------ 9

def test_no_composed_outcome_can_affect_eligibility():
    """Δ_R(f), δ_diff and any composed cell are absent before a freeze. Even
    supplied, they change nothing: the rule reads three survival booleans."""
    per = {"f0": survival(), "f1": survival(),
           "f2": survival(families=4, backups=1), "f3": survival()}
    clean = EL.local_eligibility(by_frame(**per))

    for injected in ({"delta_r": 0.42}, {"delta_r": -0.42},
                     {"delta_difficulty": 0.9},
                     {"composed_compliance": {"pair:B+A": 0.1}},
                     {"delta_r_by_reference": {"MK1": 0.8, "MK2": -0.8}}):
        polluted = by_frame(**per)
        for entry in polluted.values():
            entry["survival"] = {**entry["survival"], **injected}
            entry.update(injected)
        assert EL.local_eligibility(polluted) == clean


def test_the_rule_reads_no_composed_symbol():
    """A structural guard on the *code*: the module that decides inclusion
    must not name a composed quantity, so a later edit that reaches for one
    fails here rather than silently selecting frames on the outcome.

    Docstrings are excluded on purpose --- the module says in prose which
    quantities it may not read, and that prose is not a read. The check is on
    the executable body, taken from the parsed tree so a comment cannot trip
    it and a string constant cannot hide one."""
    import ast
    import inspect
    tree = ast.parse(inspect.getsource(EL))
    read: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            read.add(node.id.lower())
        elif isinstance(node, ast.Attribute):
            read.add(node.attr.lower())
        elif isinstance(node, ast.Subscript) and isinstance(
                node.slice, ast.Constant) and isinstance(node.slice.value, str):
            # a field actually looked up on a record
            read.add(node.slice.value.lower())
        elif isinstance(node, ast.Call):
            for kw in node.keywords:
                if kw.arg:
                    read.add(kw.arg.lower())
    forbidden = ("delta_r", "delta_difficulty", "delta_diff", "composed",
                 "outcome_first", "outcome_second", "pair:", "b_plus",
                 "cross_frame", "pooled")
    offenders = sorted(n for n in read if any(f in n for f in forbidden))
    assert offenders == [], offenders

    # the only inputs are one frame's survival block and Gate 2's status
    assert set(inspect.signature(EL.local_support).parameters) == {
        "survival", "frame", "operating_point", "unsupported_reason"}


def test_the_stored_pilot_records_give_the_recorded_verdict():
    """The rule, run on the signed pre-freeze records it was written for.

    Pinned because the numbers are the researcher decision's own evidence,
    and now over all four registered models:

    * `qwen3-4b` (r9, four passes) f0 and f3 --- eligible;
    * `gemma-3n-e2b-it` (r8, two passes) f1 and f3 --- eligible;
    * `qwen3-4b-instruct-2507` (r10, four passes, the ceiling) f1 alone;
    * `gemma-3n-e4b-it` (r11, two passes) f3 alone.

    The last two are **ineligible**: one supported frame cannot separate a
    property of the instruction pair from a property of the phrasing it was
    stated in. r8's 2507 lane is kept in the table beside r10's because the
    pair is the evidence for §4b's finding --- the ceiling moved f3 from
    4-and-1 to 3-and-0, so the shortfall was an artefact of the two-pass
    split size rather than a gap the allocation could close.
    """
    import json
    import pathlib as _p
    evidence = _p.Path(__file__).resolve().parents[1] / "evidence"
    expected = {
        ("dci1v8-pilot-r9", "qwen3-4b"): ([0, 3], True),
        ("dci1v8-pilot-r8", "gemma-3n-e2b-it"): ([1, 3], True),
        ("dci1v8-pilot-r8", "qwen3-4b-instruct-2507"): ([1], False),
        ("dci1v8-pilot-r10", "qwen3-4b-instruct-2507"): ([1], False),
        ("dci1v8-pilot-r11", "gemma-3n-e4b-it"): ([3], False),
    }
    seen = 0
    for (root, model), (frames, eligible) in expected.items():
        path = (evidence / root / "evidence" / "dci1v8" / model
                / "GATE_3_REFERENCES" / "gate3_references.json")
        if not path.exists():
            continue
        record = json.loads(path.read_text())
        record = record.get("payload", record)
        out = EL.local_eligibility(record["by_frame"], frames=S.FRAMES)
        assert out["local_supported_frames"] == frames, (root, model)
        assert out["local_eligible"] is eligible, (root, model)
        seen += 1
    if seen == 0:
        pytest.skip("no promoted v8 pilot evidence in this working tree")


# ---------------------------------------------------- the production wiring

def test_gate3_survival_carries_the_verdict_and_the_reason():
    """`survival_summary` is what Gate 3 writes, so the verdict must come out
    of the same function that computes the requirements it is made of."""
    pool = {"local": {"MK1:2": {"passed": True}, "MK2:3": {"passed": True},
                      "MK3:4": {"passed": True}, "MK4:5": {"passed": False}},
            "spectrum": {}}
    core = {"references_identified": True,
            "core_references": [{"family": "MK1", "severity": 2, "iota": 0.6},
                                {"family": "MK2", "severity": 3, "iota": 0.6},
                                {"family": "MK3", "severity": 4, "iota": 0.6}]}
    selection = {"coverage": {"identified": False, "status": "X",
                              "reasons": [], "projection": {"n_blocks": 96}},
                 "families": [], "n_spectrum_references": 0}
    out = REF.survival_summary(pool, core, selection, {"backups": ["MK9"]},
                               iota_a=0.6, frame=1)
    assert out["n_local_valid_families"] == 3
    assert out["local_supported"] is False
    assert out["local_unsupported_reasons"] == [
        EL.LOCAL_FAMILIES_BELOW_MINIMUM, EL.BACKUPS_BELOW_MINIMUM]
    # and the LOCAL arm's precision projection is stated at the frame's blocks
    assert out["projected_delta_r_precision"]["n_blocks"] == \
        R.CONFIRMATORY_BLOCKS_PER_FRAME
