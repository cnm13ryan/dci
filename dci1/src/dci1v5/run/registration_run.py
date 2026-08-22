"""§18 stage 1, ``PROTOCOL_REGISTERED``: adoption, and why it refuses.

This is where v5 stops being a draft. The runner assembles the signed
registration manifest, binds §34's nineteen closures and their evidence into
it, and writes the stage record that every later stage's predecessor check
reads.

**It cannot succeed today and that is the point.** Five separate things are
not ready --- open decisions, an unresolved specification question, a missing
topic-bank hash, an unapproved candidate population, and red-team findings
whose mitigation is itself a decision --- and ``protocol/manifest.py`` reports
each by name rather than collapsing them into one refusal. §18 stage 1's
registered failure status is ``REGISTRATION_INCOMPLETE``.

``plan_registration`` produces the same report **without** attempting to sign,
so a researcher can see exactly what adoption would bind and what stands in
the way, without a call that could write anything.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from dci1v4.engine import gitinfo

from dci1v5.engine.paths import ModelTree
from dci1v5.protocol import constants as C
from dci1v5.protocol import decisions, manifest, open_items
from dci1v5.run.lifecycle import StageOutcome, TerminalStatus, run_stage
from dci1v5.topics.bank import TopicBank, load_bank

__all__ = ["plan_registration", "registration_payload", "run_registration"]


def plan_registration(*, repo_root: Path | str = ".",
                      bank: TopicBank | None = None) -> dict[str, Any]:
    """What adoption would bind, and everything that stops it. Writes nothing.

    Safe to call at any time, including today. It never signs, never creates
    a key and never touches an evidence root.
    """
    bank = bank if bank is not None else load_bank()
    blockers = manifest.signing_blockers(bank)
    return {
        "stage": C.STAGE_REGISTERED,
        "can_register": not blockers,
        "failure_status": (None if not blockers
                           else manifest.REGISTRATION_INCOMPLETE),
        "blockers": blockers,
        "n_blockers": len(blockers),
        "open_decisions": list(decisions.open_decisions()),
        "blocking_specification_questions": list(open_items.blocking_items()),
        "calibration_b_status": bank.calibration_b_status,
        "topic_hashes": bank.hashes,
        "what_adoption_binds": list(manifest.REQUIRED_BINDINGS),
        "note": "no manifest is built by this call; build_manifest(...) "
                "assembles the payload for inspection and sign_registration "
                "is the only path that writes one",
    }


def registration_payload(tree: ModelTree, *, producing_commit: str,
                         adoption: Mapping[str, Any],
                         repo_root: Path | str = ".",
                         bank: TopicBank | None = None) -> dict[str, Any]:
    """The stage record. Raises ``REGISTRATION_INCOMPLETE`` when not ready."""
    bank = bank if bank is not None else load_bank()
    plan = plan_registration(repo_root=repo_root, bank=bank)
    if not plan["can_register"]:
        raise TerminalStatus(
            manifest.REGISTRATION_INCOMPLETE,
            gate=C.STAGE_REGISTERED,
            criterion="§34: every open decision closed with its evidence, "
                      "every specification question resolved, the topic-bank "
                      "hashes present and the candidate population approved",
            observed=plan["blockers"],
            strongest_permissible_statement=C.TERMINAL_SENTENCE)
    signed = manifest.sign_registration(
        tree.context, producing_commit=producing_commit, adoption=adoption,
        bank=bank, repo_root=repo_root)
    return {
        "stage": C.STAGE_REGISTERED,
        "artifact_type": C.STAGE_ARTIFACT_TYPE[C.STAGE_REGISTERED],
        "outcome": "PASS",
        "inputs": {},
        "manifest_hash": signed["manifest_hash"],
        "protocol_hash": signed["protocol_hash"],
        "reference_design_spec_hash": signed["reference_design_spec_hash"],
        "protocol_version": signed["protocol_version"],
        "decisions": signed["decisions"],
        "open_items": signed["open_items"],
        "topic_hashes": bank.hashes,
        "calibration_a_hash": bank.hashes[C.CALIBRATION_A],
        "calibration_b_hash": bank.hashes[C.CALIBRATION_B],
        "split_hash": bank.split_identity["split_hash"],
        "models": signed["models"],
        "measurement_basis": signed["measurement_basis"],
        "adoption": dict(adoption),
    }


def run_registration(tree: ModelTree, *, producing_commit: str | None = None,
                     adoption: Mapping[str, Any] | None = None,
                     repo_root: Path | str = ".",
                     environment_digest: str = "",
                     bank: TopicBank | None = None) -> StageOutcome:
    commit = producing_commit or gitinfo.head_commit(Path(repo_root))
    return run_stage(
        tree, C.STAGE_REGISTERED,
        compute=lambda _prev: registration_payload(
            tree, producing_commit=commit,
            adoption=dict(adoption or {"status": "DRAFT"}),
            repo_root=repo_root, bank=bank),
        producing_commit=commit, environment_digest=environment_digest)
