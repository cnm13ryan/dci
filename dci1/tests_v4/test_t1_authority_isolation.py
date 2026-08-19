"""T1. Authority and isolation.

Source precedence; zero v2, v3 or pilot scientific imports; separate artifact
roots; immutable historical evidence; the carry-over performed as a data-level
byte comparison rather than an import; the deprecated-and-foreign input guard;
and the §6.1 cross-replication firewall asserted statically.
"""
from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from dci1v4 import STUDY_ID, SYNTHETIC_STUDY_ID
from dci1v4.engine.context import (
    DCI1_ROOT,
    foreign_roots,
    registered_context,
    synthetic_context,
)
from dci1v4.engine.guards import (
    assert_admissible_manifest,
    assert_registered_v4_input,
    assert_rows_admissible,
    classify,
    design_evidence_read,
)
from dci1v4.errors import ProtocolError, ProvenanceGuardError

PACKAGE = DCI1_ROOT / "src" / "dci1v4"
#: Every module name a v4 scientific import would have to name.
FORBIDDEN_ROOTS = ("dci1v3", "dci1v2", "dci1.", "br_pilot_v4", "tools.")


def _modules() -> list[Path]:
    return [p for p in sorted(PACKAGE.rglob("*.py"))
            if "__pycache__" not in p.parts]


def _imported_names(path: Path) -> set[str]:
    names: set[str] = set()
    tree = ast.parse(path.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def test_no_scientific_import_of_v2_v3_or_the_pilot():
    offending: list[tuple[str, str]] = []
    for module in _modules():
        for name in _imported_names(module):
            if any(name == root.rstrip(".") or name.startswith(root)
                   for root in FORBIDDEN_ROOTS):
                offending.append((str(module.relative_to(PACKAGE)), name))
    assert offending == [], (
        f"the v4 package imports from an earlier DCI implementation: "
        f"{offending}")


def test_no_module_names_a_v3_or_pilot_runtime_path_outside_the_carry_over():
    """Only the carry-over and the design-evidence guard may name a v3 or
    pilot path, and the carry-over reads it as data."""
    allowed = {"verifiers/carryover.py", "engine/guards.py",
               "engine/context.py"}
    offending = []
    for module in _modules():
        rel = str(module.relative_to(PACKAGE))
        if rel in allowed:
            continue
        text = module.read_text()
        for marker in ("dci1v3", "dci1-v3", "br-pilot-v4", "br_pilot_v4",
                       "dci1-v2"):
            for line in text.splitlines():
                if marker in line and not line.lstrip().startswith(("#", "*")):
                    # A docstring mention is history, not a runtime path.
                    if '"' in line or "'" in line:
                        if "/" in line or "Path" in line or "import" in line:
                            offending.append((rel, line.strip()[:70]))
    assert offending == [], offending


def test_carry_over_is_a_data_level_byte_comparison_not_an_import():
    source = (PACKAGE / "verifiers" / "carryover.py").read_text()
    names = _imported_names(PACKAGE / "verifiers" / "carryover.py")
    assert not any(n.startswith("dci1v3") for n in names)
    assert "read_text()" in source and "ast.parse" in source
    assert "literal_eval" in source


def test_carry_over_record_verifies_and_refuses_on_drift(tmp_path):
    from dci1v4.errors import CarryOverMismatch
    from dci1v4.verifiers.carryover import carry_over_record

    record = carry_over_record()
    assert all(entry["identical"] for entry in record["entries"])
    assert record["boundary"]["cases"] == 40
    assert record["boundary"]["v3_sha256"] == record["boundary"]["v4_sha256"]

    v3 = DCI1_ROOT / "src" / "dci1v3" / "verifiers"
    fake = tmp_path / "verifiers"
    fake.mkdir()
    for name in ("words.py", "target.py", "families.py", "boundary.py"):
        (fake / name).write_text((v3 / name).read_text())
    drifted = (fake / "words.py").read_text().replace(
        "if ch.isalpha():", "if ch.isalpha() or ch == '-':")
    (fake / "words.py").write_text(drifted)
    with pytest.raises(CarryOverMismatch):
        carry_over_record(fake)


def test_v4_roots_are_separate_and_refuse_historical_trees(tmp_path):
    context = registered_context()
    assert context.study_id == STUDY_ID
    assert context.study_root.name == "dci1-v4"
    for foreign in foreign_roots():
        assert not context.study_root.resolve().is_relative_to(
            foreign.resolve())
    synthetic = synthetic_context(tmp_path)
    assert synthetic.study_id == SYNTHETIC_STUDY_ID
    with pytest.raises(ProtocolError):
        # A synthetic root that would place the v4 study tree inside the v3
        # evidence tree is refused before anything is written.
        synthetic_context(DCI1_ROOT / "evidence" / "dci1-v3")


def test_deprecated_and_foreign_guard_refuses_legacy_v3_and_pilot(tmp_path):
    context = synthetic_context(tmp_path)
    for label, path in (
            ("v3", DCI1_ROOT / "evidence" / "dci1-v3" / "gemma-3n-e2b-it"),
            ("pilot", DCI1_ROOT / "evidence" / "br-pilot-v4"),
            ("legacy", DCI1_ROOT.parent / "exploratory" / "evidence")):
        assert classify(path) is not None, label
        with pytest.raises(ProvenanceGuardError):
            assert_registered_v4_input(context, path)

    outside = tmp_path / "elsewhere" / "rows.jsonl"
    outside.parent.mkdir(parents=True)
    outside.write_text("{}")
    with pytest.raises(ProvenanceGuardError):
        assert_registered_v4_input(context, outside)

    inside = context.study_root / "model" / "confirmatory" / "cache.jsonl"
    inside.parent.mkdir(parents=True)
    inside.write_text("{}")
    assert assert_registered_v4_input(context, inside) == inside.resolve()


def test_guard_refuses_a_deprecated_or_foreign_manifest():
    for classification in ("DEPRECATED", "FOREIGN", "design_evidence"):
        with pytest.raises(ProvenanceGuardError):
            assert_admissible_manifest({"classification": classification})
    with pytest.raises(ProvenanceGuardError):
        assert_admissible_manifest({"study_id": "dci1-v3"})
    assert_admissible_manifest({"study_id": "dci1-v4",
                                "classification": "confirmatory_evidence"})


def test_guard_refuses_rows_from_another_study(tmp_path):
    context = synthetic_context(tmp_path)
    with pytest.raises(ProvenanceGuardError):
        assert_rows_admissible(context, [{"study_id": "dci1-v3"}])
    assert assert_rows_admissible(
        context, [{"study_id": SYNTHETIC_STUDY_ID}]) == 1


def test_design_evidence_door_labels_its_result_non_confirmatory():
    pilot = DCI1_ROOT / "evidence" / "br-pilot-v4"
    if not pilot.exists():
        pytest.skip("the pilot cache is not present in this checkout")
    stamp = design_evidence_read(pilot, check="C12",
                                 purpose="variance re-estimate")
    assert stamp["status"] == "non-confirmatory"
    assert stamp["classification"] == "design_evidence"
    with pytest.raises(ProvenanceGuardError):
        design_evidence_read(Path("/tmp"), check="C12", purpose="x")


def test_cross_replication_firewall_is_static():
    """§6.1: no study-wide value is reachable from a per-model record, and no
    per-model outcome can write a study-wide rule."""
    # The study-wide module cannot read a per-model record: it performs no
    # filesystem access at all and imports nothing from the engine.
    constants_path = PACKAGE / "protocol" / "constants.py"
    constants = constants_path.read_text()
    for marker in ("open(", "read_text", "read_json", "Path(", "json.load"):
        assert marker not in constants, marker
    assert not any(name.startswith("dci1v4.engine")
                   for name in _imported_names(constants_path))
    # No registry function reads another model's record, and no early-stop
    # binding exists. Checked on the parsed module rather than on its prose,
    # which explains why v3's E2B_STOP_STATUSES has no analogue here.
    registry_path = PACKAGE / "models" / "registry.py"
    tree = ast.parse(registry_path.read_text())
    bound: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            bound.add(node.id)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                             ast.ClassDef)):
            bound.add(node.name)
        if isinstance(node, ast.Attribute):
            bound.add(node.attr)
    for forbidden in ("E2B_STOP_STATUSES", "stage_record", "terminal_status",
                      "early_stop", "read_json", "read_text"):
        assert forbidden not in bound, forbidden
    assert not any(name.startswith("dci1v4.engine")
                   for name in _imported_names(registry_path))


def test_historical_evidence_is_untouched():
    """Nothing v4 wrote may live inside a historical tree."""
    for foreign in foreign_roots():
        if not foreign.exists():
            continue
        for path in foreign.rglob("*dci1-v4*"):
            pytest.fail(f"a v4-looking artifact exists inside {foreign}: "
                        f"{path}")


def test_no_v3_or_pilot_topic_enters_a_v4_set():
    from dci1v4.topics.bank import load_bank

    v3_bank = json.loads(
        (DCI1_ROOT / "src" / "dci1v3" / "topics" / "data"
         / "topics_v3.json").read_text())
    v3_questions = {t["question"].strip().lower() for t in v3_bank}
    for topic in load_bank():
        assert topic["question"].strip().lower() not in v3_questions
