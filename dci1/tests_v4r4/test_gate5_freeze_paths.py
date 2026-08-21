"""Gate 5's assembly, on the paths that had never been walked.

Every replication that reaches §18.1 has to be able to freeze, and none could.
Five of §18.1's fields were readers with no producer, and the sixth defect is
the completeness rule reading an *empty* value as a *missing* one:

* `chat_template_hash` came from `spec.get("chat_template_hash", "UNKNOWN")`
  against a registration-manifest field that has never existed --- and the
  backend renders every prompt through `apply_chat_template`, so it is part of
  the model-facing text;
* `hardware_record` was `{}`, because `cmd_gate5` never passed one;
* `environment_digest` and `dependency_digest` defaulted to the literal `"-"`,
  which is not empty, so the completeness rule *accepted* them: two provenance
  fields could have frozen as a placeholder and called themselves complete;
* `gate1_measurement_basis` was read from
  `reports/dci1v4r4/gate1_measurement.json`, which is the name of the stage
  record file and not of any report this study writes;
* `AMENDMENT_DOCUMENTS` listed v4r3's three documents, so a v4r4 freeze bound
  the amendment history of the superseded revision and left its own
  preregistration, changelog and decision register unhashed;
* §8.6's reduced design leaves `core_references` and `spectrum_severities`
  legitimately empty, and `check_completeness` reported both as missing. Three
  of v4r4's four replications run that design, and §8.6 says the branch "is
  recorded in the freeze".

And one guard with no caller: §26's `assert_durable_before_freeze`.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

from dci1v4.errors import IntegrityError

from dci1v4r4.protocol.revision import PROTOCOL_DOCUMENTS
from dci1v4r4.run import freeze_run
from dci1v4r4.stages import freeze as F

DCI1 = Path(__file__).resolve().parents[1]


def _complete(**overrides):
    record = F.build_freeze_record(**{f: "set" for f in F.FREEZE_FIELDS})
    record.update(overrides)
    return record


# ---------------------------------------------------- §8.6's three variants

def test_the_reduced_design_can_freeze_without_references_or_a_spectrum():
    record = _complete(design_variant="reduced", core_references=[],
                       spectrum_severities=[],
                       identification_statuses=["COMPANION_CLASS_NOT_MATCHED",
                                                "DIFFICULTY_SUPPORT_NOT_IDENTIFIED",
                                                "EXCESS_NOT_IDENTIFIED"])
    status = F.check_completeness(record, decisions={d: "closed"
                                                     for d in F.OPEN_DECISIONS})
    assert status["can_freeze"], status["missing_fields"]
    assert status["fields_not_identified_by_this_variant"] == [
        "core_references", "spectrum_severities"]


def test_the_no_spectrum_design_may_drop_the_spectrum_and_nothing_else():
    record = _complete(design_variant="no_spectrum", spectrum_severities=[],
                       identification_statuses=[
                           "DIFFICULTY_SUPPORT_NOT_IDENTIFIED"])
    decisions = {d: "closed" for d in F.OPEN_DECISIONS}
    assert F.check_completeness(record, decisions=decisions)["can_freeze"]

    # The core matrix is still identified under that variant, so an empty
    # `core_references` there is a gap and not a decision.
    record = {**record, "core_references": []}
    status = F.check_completeness(record, decisions=decisions)
    assert not status["can_freeze"]
    assert "core_references" in status["missing_fields"]


def test_the_full_design_gets_no_exemption_at_all():
    record = _complete(design_variant="full", spectrum_severities=[],
                       identification_statuses=[
                           "DIFFICULTY_SUPPORT_NOT_IDENTIFIED"])
    status = F.check_completeness(record,
                                  decisions={d: "closed"
                                             for d in F.OPEN_DECISIONS})
    assert not status["can_freeze"]
    assert "spectrum_severities" in status["missing_fields"]
    assert F.VARIANT_EXEMPTIONS["full"] == {}


def test_an_exemption_needs_the_registered_status_and_not_merely_the_variant():
    """The exemption is for a decision that was taken and written down.

    A reduced replication whose record does not carry `EXCESS_NOT_IDENTIFIED`
    has not recorded the non-identification, and an empty `core_references`
    there is indistinguishable from a field that was never filled in.
    """
    record = _complete(design_variant="reduced", core_references=[],
                       spectrum_severities=[], identification_statuses=[])
    status = F.check_completeness(record,
                                  decisions={d: "closed"
                                             for d in F.OPEN_DECISIONS})
    assert not status["can_freeze"]
    assert set(status["missing_fields"]) == {"core_references",
                                             "spectrum_severities",
                                             # and the empty status list is
                                             # itself a missing bound field
                                             "identification_statuses"}


def test_an_unregistered_variant_earns_no_exemption():
    record = _complete(design_variant="whatever", core_references=[],
                       identification_statuses=["EXCESS_NOT_IDENTIFIED"])
    status = F.check_completeness(record,
                                  decisions={d: "closed"
                                             for d in F.OPEN_DECISIONS})
    assert "core_references" in status["missing_fields"]


def test_the_variant_exemptions_cover_exactly_the_registered_variants():
    from dci1v4r4.stages.confirmatory import DESIGN_VARIANTS
    assert set(F.VARIANT_EXEMPTIONS) == set(DESIGN_VARIANTS)


def test_the_identification_statuses_are_a_bound_field():
    assert "identification_statuses" in F.FREEZE_FIELDS
    assert "identification_statuses" in F.NEW_IN_V4R4


# -------------------------------------------------------- the provenance fields

def test_the_placeholder_provenance_arguments_are_gone():
    """`"-"` is not empty, so the completeness rule accepted it. There is no
    default to accept now: the values come from an artifact or not at all."""
    signature = ast.parse(
        (DCI1 / "src" / "dci1v4r4" / "run" / "freeze_run.py").read_text())
    func = next(n for n in ast.walk(signature)
                if isinstance(n, ast.FunctionDef) and n.name == "run_freeze")
    names = {a.arg for a in func.args.kwonlyargs}
    assert "provenance" in names
    for gone in ("environment_digest", "dependency_digest", "hardware_record"):
        assert gone not in names
    defaults = [d for d in func.args.kw_defaults if d is not None]
    assert not [d for d in defaults
                if isinstance(d, ast.Constant) and d.value == "-"]


def test_a_dash_would_still_have_passed_the_completeness_rule():
    """Characterisation of why the default was dangerous, not of the default."""
    record = _complete(design_variant="full", environment_digest="-",
                       dependency_digest="-")
    assert F.check_completeness(
        record, decisions={d: "closed" for d in F.OPEN_DECISIONS})["can_freeze"]


def test_the_amendment_documents_are_this_revisions_own():
    for document in PROTOCOL_DOCUMENTS:
        assert document in freeze_run.AMENDMENT_DOCUMENTS
    assert "user-notes/DCI1_preregistration_v4r4.md" \
        in freeze_run.AMENDMENT_DOCUMENTS
    assert "dci1/DECISIONS_V4R4.md" in freeze_run.AMENDMENT_DOCUMENTS
    hashes = freeze_run.amendment_hashes()
    assert set(hashes) == set(freeze_run.AMENDMENT_DOCUMENTS)
    assert "MISSING" not in hashes.values(), hashes


# ----------------------------------------------------------- §26's guard

def test_the_freeze_refuses_when_the_evidence_is_not_verifiably_duplicated():
    """The guard existed and had no caller; a freeze licenses the most
    expensive generation this study makes."""
    with pytest.raises(IntegrityError, match="not verifiably duplicated"):
        freeze_run.run_freeze("gemma-3n-e2b-it", manifest={}, records={},
                              gate1=None, durability=None, provenance={},
                              producing_commit="0" * 40)
    source = ast.parse(
        (DCI1 / "src" / "dci1v4r4" / "run" / "freeze_run.py").read_text())
    func = next(n for n in ast.walk(source)
                if isinstance(n, ast.FunctionDef) and n.name == "run_freeze")
    called = {n.func.id for n in ast.walk(func)
              if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
    assert "assert_durable_before_freeze" in called


def test_the_durability_gate_counts_a_terminal_report_as_critical():
    from dci1v4r4.stages import durability as D
    assert "terminal_report.json" in D.CRITICAL_SUFFIXES


# ------------------------------------------------- §20 under the reduced design

def test_the_masking_declaration_does_not_claim_the_full_design_case():
    """The note travelled into every masked record asserting that no
    registered estimand reads a singleton-companion slot as an OUTCOME. That
    is true of the 47-cell design and false of §8.6's 8-cell one, where A's
    only companion is B and `D(A <- B)` is a registered estimand."""
    from dci1v4r4.analysis import masking

    source = (DCI1 / "src" / "dci1v4r4" / "analysis" / "masking.py").read_text()
    assert "REDUCED design" in source
    assert "D(A <- B)" in source
    module = ast.parse(source)
    func = next(n for n in ast.walk(module)
                if isinstance(n, ast.FunctionDef)
                and n.name == "assert_mask_effective")
    keys = {n.value for n in ast.walk(func)
            if isinstance(n, ast.Constant) and isinstance(n.value, str)}
    assert "structurally_unmaskable_outcomes" in keys
    assert masking.MASKED_PHASE_DECLARATIONS
