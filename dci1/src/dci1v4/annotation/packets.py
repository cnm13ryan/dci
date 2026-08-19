"""The blinded annotation interface (§10.3), extended to five instruments.

The interface has the annotator mark each qualifying feature and tallies the
annotator's own marks. It performs **no** automatic detection, highlighting,
counting or normalisation, and shows **no** cell label, model, companion,
verdict, item identity or other annotator's work. Those are structural
properties of the packet this module builds, not of a template: a field that is
absent from the packet cannot leak through a rendering bug.

Properties reproduced from v3's interface, in v4's namespace and with nothing
imported from it:

* per-annotator seeded display order, so a class-ordered packet cannot leak
  its own stratification;
* structural absence of item identities, verdicts and other annotators' work;
* finalisation requiring a label on every item, immutable thereafter;
* session files recorded outside the evidence tree until submitted through the
  registered pathway.

**Author-performed labels are never independent validation (T-16, §10.3).**
Every packet records the annotator's independence, and ``assert_independent``
refuses to treat a packet from the design or analysis team as human validation.
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from dci1v4.engine import fs
from dci1v4.errors import IntegrityError, ProtocolError
from dci1v4.protocol import constants as C
from dci1v4.protocol.hashing import sha_obj, sha_text
from dci1v4.protocol.seeds import GATE1_SAMPLE_SEED, annotation_order_seed

#: Fields that would identify the true verdict, cell or arm. The v3 analogue
#: (decision V11) listed the fields identifying the true arm; v4 adds the
#: companion dimension and the per-instrument slot.
EXCLUDED_FROM_PACKET = (
    "cell_id", "cell_type", "slot", "companion_slot", "order", "position",
    "verdict", "passed", "graded", "statistic", "non_vacuous", "model_key",
    "model_id", "block_id", "topic_id", "prompt_hash", "severity",
    "other_annotator_labels", "verifier_source_hash",
)

#: What the annotator is asked to mark, per instrument class. Each is a
#: *feature to mark*, never a count to confirm: the interface tallies the
#: annotator's own marks and offers no candidate count.
MARKING_TASKS = {
    "A": "Mark every occurrence of the target word in the answer.",
    "B": "Mark every word in the answer you judge to be longer than the "
         "stated limit.",
    "RF": "Mark every occurrence of the feature the instruction names.",
}


@dataclass(frozen=True)
class PacketItem:
    item_index: int
    display_id: str
    response_text: str
    instruction_text: str
    marking_task: str


def _task_for(kind: str) -> str:
    return MARKING_TASKS["A" if kind == "A" else
                         "B" if kind == "B" else "RF"]


def build_packet(items: Sequence[Mapping[str, Any]], *, annotator_id: str,
                 packet_id: str, root: int = GATE1_SAMPLE_SEED
                 ) -> dict[str, Any]:
    """One blinded packet, in a per-annotator seeded display order."""
    ordered = sorted(items, key=lambda i: i["item_id"])
    rng = random.Random(annotation_order_seed(root, annotator_id, packet_id))
    rng.shuffle(ordered)
    built: list[PacketItem] = []
    for index, item in enumerate(ordered):
        leaked = [f for f in EXCLUDED_FROM_PACKET if f in item
                  and f not in ("slot",)]
        _ = leaked  # the source row may carry them; the packet must not
        built.append(PacketItem(
            item_index=index,
            # A display id derived from the packet, not from the item: the
            # true identity is not reconstructable from the packet alone.
            display_id=sha_text(f"{packet_id}|{index}")[:12],
            response_text=item["response_text"],
            instruction_text=item["instruction_text"],
            marking_task=_task_for(item["kind"])))
    packet = {
        "packet_id": packet_id, "annotator_id": annotator_id,
        "items": [{"item_index": p.item_index, "display_id": p.display_id,
                   "response_text": p.response_text,
                   "instruction_text": p.instruction_text,
                   "marking_task": p.marking_task} for p in built],
        "interface_properties": {
            "automatic_detection": False, "highlighting": False,
            "counting": False, "normalisation": False,
            "shows_cell_label": False, "shows_model": False,
            "shows_companion": False, "shows_verdict": False,
            "shows_item_identity": False,
            "shows_other_annotator_work": False,
        },
    }
    assert_packet_blinded(packet)
    packet["packet_hash"] = sha_obj(packet)
    return packet


def assert_packet_blinded(packet: Mapping[str, Any]) -> None:
    """Structural blinding: no excluded field appears anywhere in the packet."""
    def walk(node: Any, path: str) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                if key in EXCLUDED_FROM_PACKET:
                    raise IntegrityError(
                        f"the packet carries the blinded field {key!r} at "
                        f"{path}; §10.3 requires its structural absence")
                walk(value, f"{path}.{key}")
        elif isinstance(node, list):
            for index, value in enumerate(node):
                walk(value, f"{path}[{index}]")
    walk(packet, "packet")
    properties = packet["interface_properties"]
    enabled = [k for k, v in properties.items() if v]
    if enabled:
        raise IntegrityError(f"the interface enables {enabled}; §10.3 "
                             f"forbids all of them")


class AnnotationSession:
    """A session file recorded **outside** the evidence tree until submitted
    through the registered pathway (§10.3)."""

    def __init__(self, path: Path, packet: Mapping[str, Any]):
        self.path = Path(path)
        self.packet = packet
        self._marks: dict[int, list[str]] = {}
        self._finalised = False

    def mark(self, item_index: int, marks: Sequence[str]) -> None:
        if self._finalised:
            raise IntegrityError("the session is finalised and immutable")
        if not any(item["item_index"] == item_index
                   for item in self.packet["items"]):
            raise ProtocolError(f"item {item_index} is not in this packet")
        self._marks[item_index] = list(marks)

    def tally(self, item_index: int) -> int:
        """The interface tallies the ANNOTATOR'S OWN marks and nothing else."""
        return len(self._marks.get(item_index, []))

    def finalise(self) -> dict[str, Any]:
        """Finalisation requires a label on every item and is immutable."""
        if self._finalised:
            raise IntegrityError("the session is already finalised")
        missing = [item["item_index"] for item in self.packet["items"]
                   if item["item_index"] not in self._marks]
        if missing:
            raise ProtocolError(
                f"finalisation requires a label on every item; {len(missing)} "
                f"remain, first index {missing[0]}")
        self._finalised = True
        payload = {
            "packet_id": self.packet["packet_id"],
            "packet_hash": self.packet["packet_hash"],
            "annotator_id": self.packet["annotator_id"],
            "labels": [{"item_index": index, "marks": marks,
                        "tally": len(marks)}
                       for index, marks in sorted(self._marks.items())],
            "finalised": True,
        }
        fs.write_json_once(self.path, payload)
        return payload


def assert_independent(annotator: Mapping[str, Any]) -> None:
    """T-16, §10.3: author-performed labels are never independent validation."""
    if annotator.get("on_design_or_analysis_team", True):
        raise ProtocolError(
            f"annotator {annotator.get('annotator_id')!r} is on the design or "
            f"analysis team; their labels are diagnostic evidence and are "
            f"never described as independent validation. The registered "
            f"outcome is HUMAN_VALIDATION_UNAVAILABLE and the §10.4 pathway "
            f"(§10.3)")


def submit(session_payload: Mapping[str, Any], *,
           annotator: Mapping[str, Any], destination: Path) -> dict[str, Any]:
    """The registered pathway a session enters the evidence tree through."""
    assert_independent(annotator)
    if not session_payload.get("finalised"):
        raise ProtocolError("an unfinalised session is never submitted")
    payload = {**session_payload,
               "annotator_independent": True,
               "measurement_basis_candidate": "human_validated",
               "criterion": C.HUMAN_DISAGREEMENT_MAX}
    fs.write_json_once(Path(destination), payload)
    return payload
