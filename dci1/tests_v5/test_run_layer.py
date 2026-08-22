"""The run layer: it exists, it is complete, and it cannot execute today."""
from __future__ import annotations

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


def _tree(tmp_path):
    return model_tree(synthetic_context(tmp_path), MODEL)


def test_the_first_stage_refuses_while_a_decision_is_open(tmp_path):
    tree = _tree(tmp_path)
    with pytest.raises(decisions.DecisionOpenError):
        cli.RUNNERS[C.STAGE_REGISTERED](tree, producing_commit="0" * 40)


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


def test_the_plan_command_writes_nothing_and_says_what_is_missing():
    plan = registration_run.plan_registration(
        repo_root=synthetic_context.__globals__["REPO_ROOT"])
    assert plan["can_register"] is False
    assert plan["failure_status"] == "REGISTRATION_INCOMPLETE"
    assert plan["calibration_b_status"] == "AUTHORED"
    assert len(plan["open_decisions"]) == 15
    assert plan["blocking_specification_questions"] == ["U2"]


def test_a_refused_transition_is_logged(tmp_path):
    from dci1v5.engine import transitions

    tree = _tree(tmp_path)
    tree.root.mkdir(parents=True, exist_ok=True)
    with pytest.raises(decisions.DecisionOpenError):
        cli.RUNNERS[C.STAGE_REGISTERED](tree, producing_commit="0" * 40)
    rows = transitions.transition_rows(tree)
    assert rows and rows[-1]["outcome"] == "REFUSED"
    assert len(rows[-1]["open_decisions"]) == 15


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
