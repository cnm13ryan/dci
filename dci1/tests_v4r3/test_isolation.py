"""v4r3 and v4r2 cannot read each other, in either direction.

v4r2 produced no confirmatory data, but it produced signed gate records on all
four models, and its admission guard is a *prefix* test on a study identifier:
``str(study).startswith("dci1-v4")``. A v4r3 identifier of ``dci1-v4r3`` would
satisfy it, and a v4r3 artifact could reach a v4r2 estimator without anything
raising. That is the failure these tests exist to make impossible.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

import dci1v4r3
from dci1v4.engine.guards import assert_admissible_manifest
from dci1v4.errors import ProvenanceGuardError

SRC = Path(__file__).resolve().parents[1] / "src"


def test_the_v4r3_study_id_cannot_satisfy_v4r2s_admission_prefix():
    # The exact expression dci1v4/engine/guards.py evaluates.
    assert not dci1v4r3.STUDY_ID.startswith("dci1-v4")
    with pytest.raises(ProvenanceGuardError):
        assert_admissible_manifest({"study_id": dci1v4r3.STUDY_ID})


def test_a_v4r2_study_id_cannot_satisfy_v4r3s_admission_rule():
    for foreign in ("dci1-v4", "dci1-v4-run", "dci1-v3", "dci1-v2",
                    "matrix-screen-v4", "fs-screen-v4", "br-pilot-v4"):
        assert any(foreign.startswith(p)
                   for p in dci1v4r3.FOREIGN_STUDY_PREFIXES), foreign
    assert not any(dci1v4r3.STUDY_ID.startswith(p)
                   for p in dci1v4r3.FOREIGN_STUDY_PREFIXES)


def test_v4r2_never_imports_v4r3():
    """The dependency is one-directional, as it is for every screen package."""
    offenders = []
    for path in (SRC / "dci1v4").rglob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            else:
                continue
            if any(n.startswith("dci1v4r3") for n in names):
                offenders.append(f"{path.name}:{node.lineno}")
    assert offenders == [], offenders


def test_v4r3_imports_no_screen_and_no_earlier_study_implementation():
    forbidden = ("dci1v3", "dci1v2", "br_pilot", "fs_screen_v4",
                 "bgrid_screen_v4", "cal_screen_v4", "matrix_screen_v4")
    offenders = []
    for path in (SRC / "dci1v4r3").rglob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            else:
                continue
            for name in names:
                if any(name.startswith(f) for f in forbidden):
                    offenders.append(f"{path.name}:{node.lineno}:{name}")
    assert offenders == [], offenders


def test_no_v4r3_module_writes_into_another_studys_tree():
    """A plain-text scan of every line that writes, as the screens use."""
    forbidden = ("evidence/dci1-v4", "evidence/dci1-v3", "evidence/dci1-v2",
                 "evidence/br-pilot", "evidence/fs-screen",
                 "evidence/bgrid-screen", "evidence/cal-screen",
                 "evidence/matrix-screen", "durable_root/dci1-v4")
    offenders = []
    for path in (SRC / "dci1v4r3").rglob("*.py"):
        for number, line in enumerate(path.read_text().splitlines(), 1):
            if "write" not in line.lower() and "open(" not in line:
                continue
            for root in forbidden:
                if root in line:
                    offenders.append(f"{path.name}:{number}")
    assert offenders == [], offenders


def test_the_evidence_dirname_is_a_sibling_of_every_other_study():
    assert dci1v4r3.EVIDENCE_DIRNAME == "dci1v4r3"
    for other in ("dci1-v2", "dci1-v3", "dci1-v4", "br-pilot-v4",
                  "fs-screen-v4", "bgrid-screen-v4", "cal-screen-v4",
                  "matrix-screen-v4"):
        assert dci1v4r3.EVIDENCE_DIRNAME != other


def test_the_v4r2_verifier_hash_is_untouched_by_v4r3s_existence():
    """v4r3 adds predicates; it must not move v4r2's canonical hash.

    The registered v4r2 value, recorded in its signed manifest, is pinned in
    dci1's own v4 suite. Here the point is only that importing v4r3 -- which
    imports v4's statistics and words modules -- changes nothing about them.
    """
    from dci1v4.verifiers import verifier_source_hash as v4_hash
    before = v4_hash()
    import dci1v4r3.verifiers as _  # noqa: F401
    from dci1v4r3.verifiers import verifier_source_hash as v4r3_hash
    assert v4_hash() == before
    assert v4r3_hash() != v4_hash()
