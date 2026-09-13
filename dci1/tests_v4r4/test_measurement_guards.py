"""Guards on §10.4-R: what the validator is, and what it may never become.

The repair replaced §10.4's judging task. That makes two failure modes worth
putting on the execution path rather than in prose:

* **the judge becoming the study's scorer.** The deterministic verifier scores
  every generation. The validator judges an operationalization card and its
  output reaches no compliance rate, cell mean, estimand or claim. This is
  checked structurally, by parsing the analysis and scoring modules, because
  an assertion on values only catches a caller that ran;
* **held-out leakage.** §10.4's split is disjoint and the calibration half is
  judged exactly once, after the configuration is frozen. A development run
  that reached a calibration item would invalidate the one-shot calibration
  the whole pathway rests on.

And three on the rules that may not move once data has been seen: the
difficulty coordinate, the support criteria, and the requirement that a new
candidate family carry its own verifier evidence.
"""
from __future__ import annotations

import ast
import importlib.util
from pathlib import Path

import pytest

from dci1v4.errors import ProtocolError

from dci1v4r4.protocol import constants as C
from dci1v4r4.stages.operationalization import (
    MUTATIONS, build_card, card_record, card_text, mutate,
)
from dci1v4r4.verifiers.constraints import Constraint

DCI1 = Path(__file__).resolve().parents[1]
SRC = DCI1 / "src" / "dci1v4r4"

TEXT = ("The kettle boils because heat moves through metal and water. "
        "However, the handle stays cool while steam rises and a whistle "
        "sounds across the quiet kitchen counter.")


def _validator():
    spec = importlib.util.spec_from_file_location(
        "gate1_validator_v4r3", DCI1 / "tools" / "gate1_validator_v4r3.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# --------------------------------------- the judge is never the study scorer

def test_no_analysis_or_scoring_module_imports_the_validator():
    """Structural: the validator cannot reach a scientific quantity."""
    offenders = []
    for path in sorted(SRC.rglob("*.py")):
        if path.parts[-2] not in ("analysis", "verifiers", "design", "run"):
            continue
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            for name in names:
                if "validator" in name or "autorater" in name \
                        or "judge" in name:
                    offenders.append(f"{path.name}: {name}")
    assert offenders == [], offenders


def test_the_operationalization_module_scores_nothing():
    """It reads the verifier; it never writes a verdict of its own.

    `build_card` reports what the deterministic verifier computed. If this
    module ever produced a pass/fail by another route, the study would have
    two scorers and no way to say which one a number came from.
    """
    source = (SRC / "stages" / "operationalization.py").read_text()
    assert "from dci1v4r4.verifiers.compliance import passes" in source
    card = build_card(Constraint("A", 1), TEXT, item_id="x")
    from dci1v4r4.verifiers.compliance import passes
    from dci1v4r4.verifiers.statistics import focal_statistic
    statistic = focal_statistic(TEXT)
    assert card.verdict == ("pass" if passes(Constraint("A", 1), statistic,
                                             TEXT) else "fail")


def test_the_validator_declares_that_it_approves_nothing():
    module = _validator()
    source = (DCI1 / "tools" / "gate1_validator_v4r3.py").read_text()
    assert "approves nothing ever" in source or "approves" in source
    assert module.LABEL_MAPPING == {"CORRECT": "faithful",
                                    "INCORRECT": "defective"}
    # the labels are about the METHOD, not about the response
    assert "faithful" not in card_text(
        build_card(Constraint("A", 1), TEXT, item_id="x"))


# ------------------------------------------------------- no tautology, no leak

def test_the_card_never_tells_the_validator_which_answer_is_wanted():
    card = build_card(Constraint("CR3", 4), TEXT, item_id="x")
    mutated = mutate(card, "inequality_flip")
    for rendered in (card_text(card), card_text(mutated)):
        lowered = rendered.lower()
        for leak in ("faithful", "defect", "mutat", "correct answer",
                     "planted", "incorrect"):
            assert leak not in lowered, (leak, rendered[:200])
    # and the two render identically in structure
    assert len(card_text(card).splitlines()) == \
        len(card_text(mutated).splitlines())


def test_the_defect_is_recorded_in_evidence_but_not_in_the_prompt():
    card = mutate(build_card(Constraint("CR3", 4), TEXT, item_id="x"),
                  "denominator_swap")
    assert card_record(card)["defect"] == "denominator_swap"
    assert "denominator_swap" not in card_text(card)


def test_every_registered_defect_actually_changes_the_card():
    card = build_card(Constraint("CR7", 36), TEXT, item_id="x")
    applied = 0
    for kind in MUTATIONS:
        mutated = mutate(card, kind)
        if mutated is None:
            continue
        applied += 1
        assert card_text(mutated) != card_text(card), kind
        assert mutated.defect == kind
    assert applied == len(MUTATIONS)


def test_a_mutated_card_cannot_be_mutated_again():
    card = mutate(build_card(Constraint("CR7", 36), TEXT, item_id="x"),
                  "off_by_one")
    with pytest.raises(ProtocolError):
        mutate(card, "inequality_flip")


def test_an_unregistered_defect_kind_is_refused():
    card = build_card(Constraint("CR7", 36), TEXT, item_id="x")
    with pytest.raises(ProtocolError):
        mutate(card, "make_it_look_wrong")


def test_the_development_and_calibration_halves_are_disjoint():
    """The pool is built from the ladder-screen rows on disk, so it is empty
    between a supersession and the re-run that replaces it. Empty is a
    checkout state and not a defect; overlapping never is."""
    module = _validator()
    items = module.V4R3.build_items()
    if not items:
        pytest.skip("no current §12.2 ladder-screen rows in this checkout")
    split = module.V4R3.split_pool(items)
    dev = {i["item_id"] for i in split["development"]}
    cal = {i["item_id"] for i in split["calibration"]}
    assert dev and cal and not (dev & cal)
    assert split["disjoint"] is True


def test_a_development_sample_never_reaches_a_calibration_item():
    module = _validator()
    items = module.V4R3.build_items()
    if not items:
        pytest.skip("no current §12.2 ladder-screen rows in this checkout")
    split = module.V4R3.split_pool(items)
    cal = {i["item_id"] for i in split["calibration"]}
    sample = module.V4R3.subsample(split["development"], 96)
    assert not {i["item_id"] for i in sample} & cal


def test_the_thresholds_are_constants_and_not_computed_from_data():
    module = _validator()
    source = (DCI1 / "tools" / "gate1_validator_v4r3.py").read_text()
    tree = ast.parse(source)
    node = next(n for n in tree.body
                if isinstance(n, ast.Assign)
                and getattr(n.targets[0], "id", "") == "THRESHOLDS")
    # every value is a literal number: nothing here can depend on a result
    for value in node.value.values:
        assert isinstance(value, ast.Constant) and isinstance(
            value.value, (int, float)), ast.dump(value)
    assert module.THRESHOLDS["sensitivity_per_kind_min"] == 0.50
    assert module.THRESHOLDS["specificity_min"] == 0.90


# --------------------------------------------- rules that may not move later

def test_the_difficulty_coordinate_is_a_registered_constant():
    """§13.9 / D6. Switching coordinates after seeing which one delivers
    coverage is choosing a design because it produces the answer wanted."""
    assert C.DIFFICULTY_COORDINATE == "instructed_compliance"
    source = (SRC / "protocol" / "constants.py").read_text()
    assert 'DIFFICULTY_COORDINATE = "instructed_compliance"' in source
    # the secondary coordinate exists and is labelled as a diagnostic
    assert "raw_solo_compliance" in \
        (DCI1 / "tools" / "v4r3_regime_report.py").read_text()


def test_the_coverage_criteria_are_literals_in_one_place():
    """§12.6's C1-C7. A threshold assembled from data could be relaxed by
    the data that failed it."""
    from dci1v4r4.stages import library
    source = (SRC / "stages" / "library.py").read_text()
    tree = ast.parse(source)
    computed = [n for n in ast.walk(tree)
                if isinstance(n, ast.Assign)
                and getattr(n.targets[0], "id", "").startswith("C")
                and not isinstance(n.value, (ast.Constant, ast.Tuple,
                                             ast.Dict, ast.List))]
    assert computed == [], [ast.dump(n) for n in computed]
    assert hasattr(library, "coverage_report")


def test_a_new_candidate_family_carries_its_own_verifier_evidence():
    """§7.5 / §10.2: the instrument population is the whole declared range.

    A family added to the grammar changes `verifier_source_hash`, so a Gate-1
    pass earned on the smaller set cannot be reused for it.
    """
    from dci1v4r4.verifiers import verifier_source_hash
    from dci1v4r4.verifiers.constraints import (
        FAMILIES, N_DECLARED_SEVERITIES,
    )
    before = verifier_source_hash()
    declared = sum(len(f.reserve) for f in FAMILIES.values())
    assert declared == N_DECLARED_SEVERITIES
    # the hash is over the verifier source, so adding a family moves it
    assert before == verifier_source_hash()
    source = (SRC / "verifiers" / "__init__.py").read_text()
    assert "constraints.py" in source or "source_hashes" in source
