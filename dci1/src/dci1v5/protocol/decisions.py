"""The nineteen registered open decisions of §34, as executable state.

**This module is why the v5 implementation cannot pretend to be a v5 study.**
§34 says all nineteen must be closed, with the decision and its evidence
recorded in the signed registration manifest, before stage 1 can pass; and
§18 stage 1 fails ``REGISTRATION_INCOMPLETE`` when one is not. Writing that
as prose in a preregistration and as nothing in the code is exactly how a
draft choice becomes an implementation fact --- the code needs a value, the
value gets chosen by whoever writes the line, and the choice is never
recorded as one.

So every decision here carries ``UNRESOLVED`` and a **standing proposal that
is not the decision**. Where a decision selects between behaviours the
implementation expresses *both*, behind ``choice()``, which raises until the
decision is closed. Nothing in this package reads a standing proposal as a
value.

Two shapes of dependence are distinguished, because they refuse at different
times:

* ``blocks_stages`` --- the lifecycle stages that may not run while the
  decision is open. ``assert_decisions_closed_for_stage`` is called by the
  stage machine, so an open decision stops the study rather than the
  function.
* ``blocks_calls`` --- named functions whose *behaviour* the decision selects.
  Those call ``choice()`` and raise where they are used, so a caller cannot
  route around the stage machine and get a default.

**Closing a decision is a researcher act and it happens here, on the record.**
``close()`` requires the resolution, the evidence and who took it; it refuses
a value the decision does not offer; and it is write-once per process.

**And it survives the process, because a closure that lives only in a running
interpreter is not a decision anybody took.** ``RECORD_PATH`` is a committed
file carrying every closure the researcher has actually made, with its
evidence, who took it and when; this module reads it at import and applies it.
So ``value_of("D18")`` answers with what the researcher decided, a test that
reopens the registry restores *that* state rather than a blank one, and the
registration manifest binds the record's hash beside the closures themselves.
A decision absent from the record is ``UNRESOLVED`` and every path that
depends on it still refuses.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Mapping, Sequence

from dci1v4.errors import ProtocolError
from dci1v4.protocol.hashing import sha_obj

__all__ = ["UNRESOLVED", "Decision", "DecisionOpenError", "DECISIONS",
           "DECISION_IDS", "open_decisions", "closed_decisions", "is_closed",
           "value_of", "choice", "assert_decisions_closed",
           "assert_decisions_closed_for_stage", "assert_decisions_closed_for",
           "decisions_blocking_stage", "decisions_blocking_call", "close",
           "reopen_all_for_testing", "override_for_testing",
           "registration_payload",
           "REGISTRATION_INCOMPLETE", "RECORD_PATH", "RECORD_RELPATH",
           "recorded_closures", "apply_recorded_closures", "record_hash",
           "record_payload", "non_adopted_alternatives", "recorded_spec",
           "read_record"]

#: The value every decision carries until a researcher closes it.
UNRESOLVED = "UNRESOLVED"

#: §18 stage 1's failure status when a decision is still open.
REGISTRATION_INCOMPLETE = "REGISTRATION_INCOMPLETE"


class DecisionOpenError(ProtocolError):
    """A code path that depends on an unresolved §34 decision was reached."""


@dataclass(frozen=True)
class Decision:
    """One §34 entry.

    ``standing_proposal`` is the preregistration's own proposal, quoted so a
    reader can see what the researcher is being asked to accept or reject. It
    is **not** a default: ``value`` stays ``UNRESOLVED`` until ``close`` is
    called, and no function in this package falls back to the proposal.
    """

    id: str
    question: str
    standing_proposal: str
    #: The values a closure may take, or () when the decision is an
    #: acceptance rather than a selection between coded behaviours.
    admissible_values: tuple[Any, ...] = ()
    #: Lifecycle stages that may not run while this is open.
    blocks_stages: tuple[str, ...] = ()
    #: Fully-qualified functions whose behaviour this decision selects.
    blocks_calls: tuple[str, ...] = ()
    #: The red-team finding this decision carries, where there is one.
    redteam: str | None = None
    value: Any = UNRESOLVED
    evidence: str | None = None
    decided_by: str | None = None
    decided_on: str | None = None

    @property
    def resolved(self) -> bool:
        return self.value != UNRESOLVED

    def as_dict(self) -> dict[str, Any]:
        return {"id": self.id, "question": self.question,
                "standing_proposal": self.standing_proposal,
                "admissible_values": list(self.admissible_values),
                "blocks_stages": list(self.blocks_stages),
                "blocks_calls": list(self.blocks_calls),
                "redteam": self.redteam, "status":
                    "CLOSED" if self.resolved else "OPEN",
                "value": self.value, "evidence": self.evidence,
                "decided_by": self.decided_by, "decided_on": self.decided_on}


# Stage names are duplicated here as literals rather than imported from
# `constants`, because `constants` imports this module: a decision has to be
# expressible before the constants that depend on one are.
_S1 = "PROTOCOL_REGISTERED"
_S2 = "QUALIFIED"
_S4 = "REGIME_SCREEN"
_S6 = "GATE_2_FOCAL_CALIBRATION"
_S7 = "GATE_2_5_CANDIDATE_QUALIFICATION"
_S8 = "GATE_3A_REFERENCE_CALIBRATION"
_S9 = "GATE_3B_REFERENCE_SELECTION"
_S10 = "GATE_3C_IDENTIFICATION"
_S12 = "PREFREEZE_AUDIT"
_S17 = "UNMASKED_ANALYSIS"

_REGISTERED: tuple[Decision, ...] = (
    Decision(
        "D0",
        "Whether to adopt v5 at all, given that its matching rule is fitted "
        "to v4r4 and §30 says so plainly",
        "Adopt, with §30's declaration attached permanently",
        admissible_values=("adopt", "do_not_adopt"),
        blocks_stages=(_S1,)),
    Decision(
        "D1",
        "The confirmatory compute budget: which arms and how many models",
        "Four models at 56 cells, with §6.1's execution order and "
        "NOT_EXECUTED for any replication not reached",
        admissible_values=("four_models_56_cells", "four_models_47_cells",
                           "two_models_56_cells", "384_blocks_m4"),
        blocks_stages=(_S1,),
        blocks_calls=("design.cells.admitted_arms_from_decision",),
        redteam="R1 (dropping the near-form arm removes R1's only mitigation)"),
    Decision(
        "D2",
        "Whether a load-three arm is added so that the memo's Gamma becomes "
        "estimable",
        "No load-three arm; §5's exclusion stands",
        admissible_values=("no_load_three", "add_load_three"),
        blocks_stages=(_S1,)),
    Decision(
        "D3",
        "Whether the 96 new Calibration-B questions are authored before "
        "adoption",
        "Author before adoption; the bank hash enters the registration "
        "manifest",
        admissible_values=("author_before_adoption", "author_after_adoption"),
        blocks_stages=(_S1, _S2),
        blocks_calls=("topics.calibration_b_bank",)),
    Decision(
        "D4",
        "The Tier-1 marker vocabulary: the eight registered markers of §7.10",
        "The eight of §7.10, with every rejection reason recorded",
        admissible_values=("approve_eight", "approve_with_substitution",
                           "reject"),
        blocks_stages=(_S1, _S4),
        blocks_calls=("verifiers.constraints.assert_marker_vocabulary_"
                      "approved",)),
    Decision(
        "D5",
        "Whether a weighted composite validity score replaces the "
        "lexicographic conjunction",
        "Lexicographic; no composite score, because the development data "
        "cannot fix weights that generalise",
        admissible_values=("lexicographic", "weighted_composite"),
        blocks_stages=(_S1,)),
    Decision(
        "D6",
        "Whether REFERENCE_SUPPORT_NOT_IDENTIFIED is terminal or an "
        "identification status",
        "Identification status, with §13.15's argument recorded",
        admissible_values=("identification_status", "terminal"),
        blocks_stages=(_S1, _S10),
        blocks_calls=("stages.support.support_disposition",),
        redteam="R16"),
    Decision(
        "D7",
        "The interaction-gate ceiling of 0.90",
        "0.90, with the coincidence recorded and not used as evidence",
        admissible_values=(0.90, 0.85, 0.95),
        blocks_stages=(_S1,),
        redteam="R13"),
    Decision(
        "D8",
        "The chance ceiling of 0.75",
        "0.75 on the point, 0.85 on the Wilson upper bound",
        admissible_values=(0.75, 0.50, 0.90),
        blocks_stages=(_S1,)),
    Decision(
        "D9",
        "Whether an independent annotator will be available, which decides "
        "whether §10.3 can ever supersede §10.5's basis",
        "Unavailable; deterministic_measurement_validated with the scope "
        "sentence attached permanently",
        admissible_values=("unavailable", "available"),
        blocks_stages=(_S1,)),
    Decision(
        "D10",
        "Whether the broad-class arm carries more than one companion",
        "One companion; no class claim is made",
        admissible_values=("one_companion", "several_companions"),
        blocks_stages=(_S1,)),
    Decision(
        "D11",
        "Whether the confirmatory topics are re-authored rather than carried "
        "from v4",
        "Carry, with §6.2's statement of the residual",
        admissible_values=("carry", "re_author"),
        blocks_stages=(_S1,)),
    Decision(
        "D12",
        "Whether delta_difficulty or an order contrast receives a magnitude "
        "threshold of its own",
        "Direction and the SESOI only; the memo's 0.25 is not transferred",
        admissible_values=("direction_and_sesoi_only", "own_threshold"),
        blocks_stages=(_S1,)),
    Decision(
        "D13",
        "Whether F11 is primary-tier",
        "Primary tier, F11, licensing L4b",
        admissible_values=("primary_tier", "secondary"),
        blocks_stages=(_S1,)),
    Decision(
        "D14",
        "Whether instructed compliance remains the difficulty coordinate now "
        "that the core pool is chance-free",
        "iota remains primary, raw solo secondary, "
        "DIFFICULTY_COORDINATE_DEPENDENT on disagreement",
        admissible_values=("iota_primary", "raw_primary"),
        blocks_stages=(_S1,)),
    Decision(
        "D15",
        "Whether the memo's 0.10 and 0.25 apply to a same-form Delta_R",
        "Both transfer, on the ground that the memo defined them for the "
        "shape of the contrast. Recorded as contestable",
        admissible_values=("both_transfer", "neither_transfers",
                           "generic_only"),
        blocks_stages=(_S1,),
        redteam="R2"),
    Decision(
        "D16",
        "Whether Calibration-B measures the full carried set or only "
        "Calibration-A's survivors",
        "Restrict to A-survivors, with §12.7's statement of the asymmetry",
        admissible_values=("a_survivors", "complete_population"),
        blocks_stages=(_S1, _S8),
        blocks_calls=("stages.stability.calibration_b_population",),
        redteam="R11"),
    Decision(
        "D17",
        "Whether a construct floor is registered for m*",
        "No construct floor; the realised m*, B's chance compliance at m* "
        "and B's whole curve are reported",
        admissible_values=("no_floor", "floor"),
        blocks_stages=(_S1, _S6),
        blocks_calls=("stages.regime.assert_construct_floor",),
        redteam="R14"),
    Decision(
        "D18",
        "Whether the near-form arm is a precondition of emitting L3c",
        "Not a precondition; L3c without the arm carries "
        "NEAR_FORM_ARM_NOT_AVAILABLE and §17.6's fixed sentence",
        admissible_values=("not_a_precondition", "precondition"),
        blocks_stages=(_S1, _S17),
        blocks_calls=("analysis.claims.l3c_requires_near_form",),
        redteam="R1"),
)

DECISIONS: dict[str, Decision] = {d.id: d for d in _REGISTERED}
DECISION_IDS: tuple[str, ...] = tuple(DECISIONS)

#: §34 says nineteen and this asserts it rather than describing it, because a
#: summary that drifts from the list is exactly the defect §33 asks for.
assert len(DECISIONS) == 19, (
    f"§34 registers nineteen open decisions D0-D18; this module carries "
    f"{len(DECISIONS)}")
assert DECISION_IDS == tuple(f"D{i}" for i in range(19))


def open_decisions() -> tuple[str, ...]:
    return tuple(k for k, d in DECISIONS.items() if not d.resolved)


def closed_decisions() -> tuple[str, ...]:
    return tuple(k for k, d in DECISIONS.items() if d.resolved)


def is_closed(decision_id: str) -> bool:
    return _get(decision_id).resolved


def _get(decision_id: str) -> Decision:
    try:
        return DECISIONS[decision_id]
    except KeyError as exc:
        raise ProtocolError(
            f"{decision_id!r} is not a registered §34 decision; registered: "
            f"{DECISION_IDS}") from exc


def value_of(decision_id: str) -> Any:
    """The closed value, or ``UNRESOLVED``. Never a standing proposal."""
    return _get(decision_id).value


def choice(decision_id: str, options: Mapping[Any, Any], *,
           where: str) -> Any:
    """Select the behaviour a closed decision names, or refuse.

    ``options`` maps each admissible value to what the implementation does
    under it, so both branches exist in the source and neither is reachable
    while the decision is open. A decision that offers a value this call has
    no branch for is a defect here, not a researcher error, and it says so.
    """
    decision = _get(decision_id)
    if decision.admissible_values:
        missing = [v for v in decision.admissible_values if v not in options]
        if missing:
            raise ProtocolError(
                f"{where}: §34 {decision_id} admits {missing} and this call "
                "supplies no behaviour for them; both branches of a "
                "researcher decision must exist in the source")
    if not decision.resolved:
        raise DecisionOpenError(
            f"{where}: §34 {decision_id} is UNRESOLVED --- "
            f"{decision.question}. The preregistration's standing proposal is "
            f"{decision.standing_proposal!r} and a standing proposal is not a "
            f"value. Close it with decisions.close({decision_id!r}, ...) and "
            "record it in the signed registration manifest; §18 stage 1 "
            f"returns {REGISTRATION_INCOMPLETE} until then")
    return options[decision.value]


def decisions_blocking_stage(stage: str) -> tuple[str, ...]:
    return tuple(k for k, d in DECISIONS.items()
                 if stage in d.blocks_stages and not d.resolved)


def decisions_blocking_call(call: str) -> tuple[str, ...]:
    return tuple(k for k, d in DECISIONS.items()
                 if call in d.blocks_calls and not d.resolved)


def assert_decisions_closed(ids: Sequence[str], *, where: str) -> None:
    still_open = [i for i in ids if not _get(i).resolved]
    if still_open:
        raise DecisionOpenError(
            f"{where}: these §34 decisions are UNRESOLVED and this path "
            f"depends on them: {still_open}. §34 requires every one closed, "
            "with its evidence, in the signed registration manifest before "
            "stage 1 can pass")


def assert_decisions_closed_for_stage(stage: str) -> None:
    """§18: a stage may not run while a decision it depends on is open.

    Stage 1 depends on **all** of them, so this is also the executable form
    of ``REGISTRATION_INCOMPLETE``.
    """
    blocking = decisions_blocking_stage(stage)
    if blocking:
        raise DecisionOpenError(
            f"{stage} may not run: §34 decisions {list(blocking)} are "
            f"UNRESOLVED. §18 stage 1 records {REGISTRATION_INCOMPLETE}")


def assert_decisions_closed_for(call: str) -> None:
    blocking = decisions_blocking_call(call)
    if blocking:
        raise DecisionOpenError(
            f"{call} depends on §34 decisions {list(blocking)}, which are "
            "UNRESOLVED")


def close(decision_id: str, value: Any, *, evidence: str, decided_by: str,
          decided_on: str) -> Decision:
    """Record a researcher's closure. Write-once, and never a default.

    The four arguments are all required because §34 requires the decision
    *and its evidence* in the manifest: a closure with no evidence is a
    default with a signature on it.
    """
    decision = _get(decision_id)
    if decision.resolved:
        raise ProtocolError(
            f"{decision_id} is already closed at {decision.value!r} by "
            f"{decision.decided_by!r}; a decision is closed once and a change "
            "is an amendment under §32, not a re-close")
    if decision.admissible_values and value not in decision.admissible_values:
        raise ProtocolError(
            f"{decision_id} admits {decision.admissible_values}; got "
            f"{value!r}")
    if not (evidence and decided_by and decided_on):
        raise ProtocolError(
            f"closing {decision_id} requires the evidence, who took it and "
            "when; §34 binds all three into the registration manifest")
    updated = replace(decision, value=value, evidence=evidence,
                      decided_by=decided_by, decided_on=decided_on)
    DECISIONS[decision_id] = updated
    return updated


def override_for_testing(decision_id: str, value: Any) -> Decision:
    """Force a decision to a value, bypassing write-once. **Tests only.**

    It exists for one job: keeping the branch the researcher did *not* adopt
    executed by a test rather than merely present in the source. A retained
    alternative nobody runs rots, and the first time anyone needs it --- to
    reproduce a historical replication, or to see what the refused option
    would have done --- it does not work.

    It cannot affect a run. A run's closures come from ``RECORD_PATH``, this
    writes nothing to it, and ``reopen_all_for_testing`` puts the registry
    back to what the record says.
    """
    decision = _get(decision_id)
    if decision.admissible_values and value not in decision.admissible_values:
        raise ProtocolError(
            f"{decision_id} admits {decision.admissible_values}; got "
            f"{value!r}")
    DECISIONS[decision_id] = replace(
        decision, value=value, evidence="OVERRIDDEN FOR A TEST",
        decided_by="test", decided_on="test")
    return DECISIONS[decision_id]


def reopen_all_for_testing() -> None:
    """Restore the registry to **the recorded state**, not to a blank one.

    Exists so that a test can exercise a closed-decision path and leave the
    module as it found it. What it found it in is the state ``RECORD_PATH``
    describes: a decision the researcher has taken is taken, and a fixture
    that reopened it would let a test assert behaviour the protocol no longer
    admits. Decisions the record does not carry go back to ``UNRESOLVED``.
    """
    for key, decision in list(DECISIONS.items()):
        DECISIONS[key] = replace(decision, value=UNRESOLVED, evidence=None,
                                 decided_by=None, decided_on=None)
    apply_recorded_closures()


# ------------------------------------------------------ the durable record

#: Repository-relative, so the manifest can name it and a reader can find it.
RECORD_RELPATH = "dci1/reports/dci1v5/researcher_decisions.json"
RECORD_PATH = Path(__file__).resolve().parents[3] / "reports" / "dci1v5" / \
    "researcher_decisions.json"


def _read_record(path: Path | str | None = None) -> dict[str, Any]:
    path = Path(path) if path is not None else RECORD_PATH
    if not path.exists():
        return {"closures": [], "source": None, "recorded_on": None,
                "path": str(path), "present": False}
    payload = json.loads(path.read_text())
    closures = payload.get("closures")
    if not isinstance(closures, list):
        raise ProtocolError(
            f"{path}: the researcher-decision record must carry a "
            "'closures' list; a record whose shape is wrong is not a record")
    return {**payload, "path": str(path), "present": True}


def read_record(path: Path | str | None = None) -> dict[str, Any]:
    """The whole record document. ``open_items`` reads its own section."""
    return _read_record(path)


def recorded_closures(path: Path | str | None = None
                      ) -> tuple[dict[str, Any], ...]:
    """Every closure the record carries, validated but not yet applied."""
    record = _read_record(path)
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for entry in record["closures"]:
        for field in ("id", "value", "evidence", "decided_by", "decided_on"):
            if not str(entry.get(field, "")).strip():
                raise ProtocolError(
                    f"{record['path']}: a recorded closure needs {field}; §34 "
                    "binds the decision AND its evidence, and an entry "
                    "missing one is a default with a filename on it")
        decision = _get(entry["id"])
        if entry["id"] in seen:
            raise ProtocolError(
                f"{record['path']}: {entry['id']} is recorded twice; a change "
                "to a closed decision is a §32 amendment, not a second entry")
        seen.add(entry["id"])
        if decision.admissible_values and \
                entry["value"] not in decision.admissible_values:
            raise ProtocolError(
                f"{record['path']}: {entry['id']} admits "
                f"{decision.admissible_values} and the record says "
                f"{entry['value']!r}")
        out.append(dict(entry))
    return tuple(out)


def apply_recorded_closures(path: Path | str | None = None) -> tuple[str, ...]:
    """Apply the record to the registry. Idempotent, and never a downgrade.

    Re-applying an identical closure is a no-op rather than the write-once
    refusal ``close`` raises, because importing this module twice is not a
    researcher taking a decision twice. A record that *disagrees* with a
    closure already in force is refused: that is an amendment and it does not
    happen by a file changing under a running process.
    """
    applied: list[str] = []
    for entry in recorded_closures(path):
        current = _get(entry["id"])
        if current.resolved:
            if current.value != entry["value"]:
                raise ProtocolError(
                    f"{entry['id']} is in force at {current.value!r} and the "
                    f"record says {entry['value']!r}; a change to a closed "
                    "decision is a §32 amendment")
            continue
        close(entry["id"], entry["value"], evidence=entry["evidence"],
              decided_by=entry["decided_by"], decided_on=entry["decided_on"])
        applied.append(entry["id"])
    return tuple(applied)


def recorded_spec(decision_id: str, path: Path | str | None = None
                  ) -> dict[str, Any] | None:
    """The registered payload a closure carries beyond its value.

    Some decisions select a *value* and some select a value **and the
    parameters that value has no room for**. §34 D17's ``floor`` is the case
    that forced this: the admissible values are ``no_floor`` and ``floor``,
    and ``floor`` alone says nothing about which quantity is bounded, by what
    number, under which semantics, or on what derivation. Putting those in
    the code would be exactly the move §34 exists to stop, so they live in the
    record beside the closure that requires them, and the module that applies
    the floor reads them from here rather than from a literal.

    Returns ``None`` when the decision is not recorded or carries no spec ---
    which is most of them, and is not an error.
    """
    _get(decision_id)
    for entry in recorded_closures(path):
        if entry["id"] == decision_id:
            spec = entry.get("spec")
            return dict(spec) if isinstance(spec, Mapping) else None
    return None


def record_hash(path: Path | str | None = None) -> str | None:
    """The record's content identity, for the registration manifest.

    Over the closures **and** the open-item resolutions, because both are
    researcher acts recorded in the same file and a hash that covered only
    half of it would let U2's resolution change under a signature that did
    not move.
    """
    record = _read_record(path)
    if not record["present"]:
        return None
    return sha_obj({"path": RECORD_RELPATH, "closures": record["closures"],
                    "open_items": record.get("open_items") or []})


def non_adopted_alternatives() -> dict[str, list[Any]]:
    """Per closed decision, the branches the researcher did **not** take.

    ``choice()`` still carries every branch, because a study has to be able
    to show what it could have done. This names them as not-adopted so that
    a reader of the manifest cannot mistake a retained branch for a live
    scientific alternative.
    """
    return {k: [v for v in d.admissible_values if v != d.value]
            for k, d in DECISIONS.items()
            if d.resolved and d.admissible_values}


def record_payload(path: Path | str | None = None) -> dict[str, Any]:
    record = _read_record(path)
    return {
        "path": RECORD_RELPATH,
        "present": record["present"],
        "hash": record_hash(path),
        "recorded_on": record.get("recorded_on"),
        "source": record.get("source"),
        "closed_here": [e["id"] for e in record["closures"]],
        "resolved_here": [e["id"] for e in (record.get("open_items") or [])],
    }


def registration_payload() -> dict[str, Any]:
    """What §18 stage 1 binds into the signed registration manifest."""
    return {
        "section": "§34",
        "n_decisions": len(DECISIONS),
        "all_closed": not open_decisions(),
        "open": list(open_decisions()),
        "record": record_payload(),
        "non_adopted_alternatives": non_adopted_alternatives(),
        "decisions": [d.as_dict() for d in DECISIONS.values()],
    }


#: Applied at import: a closure the researcher recorded is in force, and a
#: module that reported it open would be reporting a decision nobody may take
#: again as one still to take.
apply_recorded_closures()
