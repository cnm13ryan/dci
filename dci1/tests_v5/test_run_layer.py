"""The run layer: it exists, it is complete, and adoption unblocked it."""
from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

from dci1v4.errors import IntegrityError, ProtocolError

from dci1v5.engine.context import synthetic_context
from dci1v5.engine.paths import model_tree
from dci1v5.protocol import constants as C
from dci1v5.protocol import decisions
from dci1v5.run import cli, registration_run
from dci1v5.run.gates_run import assert_no_substitution_path
from dci1v5.run.lifecycle import TerminalStatus, terminal_statuses_in_force

MODEL = "gemma-3n-e2b-it"
REPO_ROOT = Path(__file__).resolve().parents[2]


def _tree(tmp_path):
    return model_tree(synthetic_context(tmp_path), MODEL)


def test_the_first_stage_refuses_again_if_a_decision_reopens(tmp_path):
    """§34's guard on stage 1, which needs all nineteen.

    All nineteen are closed, so the refusal has to be provoked --- and a guard
    nothing provokes is a guard that quietly stops working.
    """
    tree = _tree(tmp_path)
    held = decisions.DECISIONS["D13"]
    decisions.DECISIONS["D13"] = dataclasses.replace(
        held, value=decisions.UNRESOLVED)
    try:
        with pytest.raises(decisions.DecisionOpenError):
            cli.RUNNERS[C.STAGE_REGISTERED](tree, producing_commit="0" * 40)
    finally:
        decisions.DECISIONS["D13"] = held


def test_every_later_stage_refuses_too(tmp_path):
    """§18: in order, and §34: not while a decision it depends on is open.

    The two refusals are different and both matter, so this asserts only
    that *something* refuses --- a stage that ran would be the finding.
    """
    tree = _tree(tmp_path)
    for stage in C.STAGE_SEQUENCE[1:]:
        # The three registered refusals: an open decision, an illegal
        # transition, a missing predecessor record. Naming them is what makes
        # this a test --- a stage that failed on a typo would pass a blind
        # `Exception` assertion and look like a refusal.
        with pytest.raises((ProtocolError, IntegrityError,
                            decisions.DecisionOpenError)):
            cli.RUNNERS[stage](tree, producing_commit="0" * 40)


def test_the_plan_command_writes_nothing_and_reports_the_one_open_question():
    """It never signs, never creates a key and never touches a root.

    A4 opened U4 --- §12.6 makes a rung's eligibility "§13's band on iota" and
    §13 bands p_solo, and the two readings admit different rungs --- so the
    plan reports exactly one blocker and `can_register` is False. Every other
    prerequisite is met, which is what makes the one that is not legible.
    """
    plan = registration_run.plan_registration(repo_root=REPO_ROOT)
    assert plan["can_register"] is False
    assert plan["blocking_specification_questions"] == ["U4"]
    assert [b["kind"] for b in plan["blockers"]] == ["UNRESOLVED_SPECIFICATION"]
    assert plan["calibration_b_status"] == "AUTHORED"
    assert plan["open_decisions"] == []
    assert "no manifest is built by this call" in plan["note"]


def test_the_plan_says_nothing_else_is_missing(u4_named_for_testing):
    """Under a named §12.6 formulation every other prerequisite is met."""
    plan = registration_run.plan_registration(repo_root=REPO_ROOT)
    assert plan["can_register"] is True
    assert plan["failure_status"] is None
    assert plan["blockers"] == []
    assert plan["blocking_specification_questions"] == []


def test_a_refused_transition_is_logged(tmp_path):
    from dci1v5.engine import transitions

    tree = _tree(tmp_path)
    tree.root.mkdir(parents=True, exist_ok=True)
    held = decisions.DECISIONS["D13"]
    decisions.DECISIONS["D13"] = dataclasses.replace(
        held, value=decisions.UNRESOLVED)
    try:
        with pytest.raises(decisions.DecisionOpenError):
            cli.RUNNERS[C.STAGE_REGISTERED](tree, producing_commit="0" * 40)
    finally:
        decisions.DECISIONS["D13"] = held
    rows = transitions.transition_rows(tree)
    assert rows and rows[-1]["outcome"] == "REFUSED"
    assert rows[-1]["open_decisions"] == ["D13"]


def test_no_post_gate4_substitution_path_exists():
    """§13.14 and §33 check 2, as a static namespace check."""
    assert assert_no_substitution_path()["found"] == []
    with pytest.raises(Exception, match="substitution"):
        assert_no_substitution_path(
            {"substitute_backup_reference": lambda: None})


def test_the_terminal_vocabulary_is_derived_from_d6(restore_decisions):
    """D6 is closed at ``identification_status``, so the status is not one.

    The `terminal` branch is exercised through the test-only override, which
    is the only way to reach it: a run's closures come from the committed
    record and the record says otherwise.
    """
    assert "REFERENCE_SUPPORT_NOT_IDENTIFIED" not in \
        terminal_statuses_in_force()
    with pytest.raises(ProtocolError):
        TerminalStatus("REFERENCE_SUPPORT_NOT_IDENTIFIED", gate="x",
                       criterion="x", observed=None,
                       strongest_permissible_statement="x")
    restore_decisions.override_for_testing("D6", "terminal")
    assert "REFERENCE_SUPPORT_NOT_IDENTIFIED" in terminal_statuses_in_force()
    raised = TerminalStatus("REFERENCE_SUPPORT_NOT_IDENTIFIED", gate="x",
                            criterion="x", observed=None,
                            strongest_permissible_statement="x")
    assert raised.status == "REFERENCE_SUPPORT_NOT_IDENTIFIED"


def test_the_cli_status_and_audit_commands_are_safe_now(tmp_path, capsys):
    assert cli.main(["audit"]) == 0
    assert cli.main(["audit", "--matrix"]) == 0
    assert cli.main(["status", "--model", MODEL, "--root", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "stage_reached" in out
