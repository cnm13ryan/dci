"""Annotation workspace: blinded sessions, autosave, immutable
finalisation, and export to the exact Gate 1 annotations format.

One session = one (model, annotator) pair over one registered packet.
Sessions are independent files; an annotator-facing payload contains only
the constraint text, the response text, and that annotator's own saved
work — never item identities, verifier verdicts, class structure, or other
annotators' labels. Display order is a per-annotator seeded shuffle, so
the packet's class-ordered layout cannot leak.

The scientific label vocabulary is the registered binary one
(``pass`` / ``fail``; shown as SATISFIES / VIOLATES). Flags, sequence
numbers, and timestamps are workflow metadata: they live in the session
file for audit and never enter the exported annotations file.
"""
from __future__ import annotations

import datetime as _dt
import json
import os
import random
import stat
from pathlib import Path
from typing import Any

from dci1v3.annotation import INTERFACE_VERSION
from dci1v3.annotation.rubric import RUBRIC_VERSION
from dci1v3.protocol.constants import GATE1_ANNOTATORS
from dci1v3.protocol.hashing import domain_int, sha_text

ORDER_DOMAIN = "dci1v3:annotation:v1"
LABELS = ("pass", "fail")
EXPORT_FILENAME = "gate1_annotations.json"

#: Packet keys an annotator-facing payload must never contain.
BLINDED_KEYS = ("item_id", "n", "verifier_class", "response_hash",
                "verdict", "s0")


class AnnotationWorkflowError(Exception):
    """A reviewer-workflow rule was violated (never a scientific status)."""


def _utc_now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


def load_packet(packet_path: Path) -> list[dict[str, Any]]:
    rows = []
    for line in Path(packet_path).read_text().splitlines():
        if line.strip():
            row = json.loads(line)
            for key in ("item_id", "constraint_text", "response_text"):
                if key not in row:
                    raise AnnotationWorkflowError(
                        f"packet row missing {key!r}; not a Gate 1 packet")
            rows.append(row)
    if not rows:
        raise AnnotationWorkflowError(f"empty packet at {packet_path}")
    ids = [r["item_id"] for r in rows]
    if len(set(ids)) != len(ids):
        raise AnnotationWorkflowError("duplicate item ids in packet")
    return rows


class AnnotatorSession:
    """One annotator's blinded, autosaving pass over one packet."""

    def __init__(self, *, packet_path: Path, workspace: Path, model: str,
                 annotator: str):
        self.model = model
        self.annotator = annotator
        self.packet_path = Path(packet_path)
        self.packet = load_packet(self.packet_path)
        self.packet_hash = sha_text(self.packet_path.read_text())
        self.dir = Path(workspace) / model
        self.path = self.dir / f"{annotator}.json"
        self._state = self._load_or_create()
        if self._state["packet_hash"] != self.packet_hash:
            raise AnnotationWorkflowError(
                "the packet changed since this session began; refusing to "
                "mix annotations across packets")
        seed = domain_int(ORDER_DOMAIN, model, annotator, self.packet_hash)
        order = list(range(len(self.packet)))
        random.Random(seed).shuffle(order)
        self._order = order                       # display k -> packet index

    # ------------------------------------------------------------ state
    def _load_or_create(self) -> dict[str, Any]:
        if self.path.exists():
            return json.loads(self.path.read_text())
        state = {
            "model": self.model, "annotator": self.annotator,
            "packet_hash": self.packet_hash,
            "rubric_version": RUBRIC_VERSION,
            "interface_version": INTERFACE_VERSION,
            "created": _utc_now(),
            "labels": {},                # item_id -> label/flag/seq/timestamp
            "face_validity": None,
            "finalized": None,
        }
        self._write(state)
        return state

    def _write(self, state: dict[str, Any]) -> None:
        self.dir.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_name(self.path.name + ".tmp")
        tmp.write_text(json.dumps(state, indent=2, sort_keys=True,
                                  ensure_ascii=False) + "\n")
        os.replace(tmp, self.path)

    def _save(self) -> None:
        if self._state["finalized"]:
            raise AnnotationWorkflowError(
                f"session {self.annotator}/{self.model} is finalised; "
                f"labels are immutable")
        self._write(self._state)

    # ------------------------------------------------------- annotation
    def _item_id_for_display(self, display: int) -> str:
        if not 1 <= display <= len(self.packet):
            raise AnnotationWorkflowError(f"display number {display} out "
                                          f"of range")
        return self.packet[self._order[display - 1]]["item_id"]

    def payload(self) -> list[dict[str, Any]]:
        """The complete annotator-facing item list, blinded."""
        items = []
        for display in range(1, len(self.packet) + 1):
            row = self.packet[self._order[display - 1]]
            saved = self._state["labels"].get(row["item_id"], {})
            items.append({
                "display": display,
                "constraint_text": row["constraint_text"],
                "response_text": row["response_text"],
                "label": saved.get("label"),
                "flag": bool(saved.get("flag", False)),
            })
        return items

    def record(self, display: int, *, label: str | None = None,
               flag: bool | None = None) -> dict[str, Any]:
        """Autosaved judgment or flag update for one displayed item."""
        if self._state["finalized"]:
            raise AnnotationWorkflowError(
                "session is finalised; labels are immutable")
        item_id = self._item_id_for_display(display)
        entry = self._state["labels"].setdefault(
            item_id, {"label": None, "flag": False, "seq": None,
                      "timestamp": None})
        if label is not None:
            if label not in LABELS:
                raise AnnotationWorkflowError(
                    f"label must be one of {LABELS}; a flag is not an "
                    f"answer")
            entry["label"] = label
            entry["seq"] = 1 + max(
                (e["seq"] or 0 for e in self._state["labels"].values()),
                default=0)
            entry["timestamp"] = _utc_now()
        if flag is not None:
            entry["flag"] = bool(flag)
        self._save()
        return {"display": display, "label": entry["label"],
                "flag": entry["flag"]}

    # ------------------------------------------------------- completion
    def progress(self) -> dict[str, Any]:
        labelled = [i for i in self._state["labels"].values()
                    if i["label"] in LABELS]
        unanswered = [d for d in range(1, len(self.packet) + 1)
                      if self._state["labels"].get(
                          self._item_id_for_display(d), {}).get("label")
                      not in LABELS]
        flagged = [d for d in range(1, len(self.packet) + 1)
                   if self._state["labels"].get(
                       self._item_id_for_display(d), {}).get("flag")]
        return {"total": len(self.packet), "labelled": len(labelled),
                "unanswered": unanswered, "flagged": flagged,
                "finalized": bool(self._state["finalized"])}

    def finalize(self, *, face_validity: bool) -> dict[str, Any]:
        """Immutable submission: every item must carry a binary label."""
        if self._state["finalized"]:
            raise AnnotationWorkflowError("session is already finalised")
        progress = self.progress()
        if progress["unanswered"]:
            raise AnnotationWorkflowError(
                f"{len(progress['unanswered'])} item(s) lack a binary "
                f"label; every item must be SATISFIES or VIOLATES before "
                f"final submission")
        if not isinstance(face_validity, bool):
            raise AnnotationWorkflowError("face-validity judgment must be "
                                          "a yes/no answer")
        self._state["face_validity"] = face_validity
        self._state["finalized"] = _utc_now()
        self._write(self._state)
        self.path.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
        return {"finalized": self._state["finalized"]}


# ------------------------------------------------------------ researcher
def _session_files(workspace: Path, model: str) -> list[Path]:
    model_dir = Path(workspace) / model
    if not model_dir.exists():
        return []
    return sorted(p for p in model_dir.glob("*.json")
                  if p.name != EXPORT_FILENAME
                  and not p.name.endswith(".tmp"))


def _load_sessions(workspace: Path, model: str) -> list[dict[str, Any]]:
    return [json.loads(p.read_text())
            for p in _session_files(workspace, model)]


def summary(workspace: Path, model: str, packet_path: Path
            ) -> dict[str, Any]:
    """Pre-lock researcher view: completion status only."""
    packet = load_packet(packet_path)
    packet_hash = sha_text(Path(packet_path).read_text())
    sessions = []
    for state in _load_sessions(workspace, model):
        labelled = sum(1 for e in state["labels"].values()
                       if e.get("label") in LABELS)
        sessions.append({
            "annotator": state["annotator"],
            "labelled": labelled, "total": len(packet),
            "flags": sum(1 for e in state["labels"].values()
                         if e.get("flag")),
            "finalized": bool(state["finalized"]),
            "packet_current": state["packet_hash"] == packet_hash,
        })
    finalized = sum(1 for s in sessions if s["finalized"]
                    and s["packet_current"])
    return {"model": model, "items": len(packet), "sessions": sessions,
            "required_annotators": GATE1_ANNOTATORS,
            "locked": finalized >= GATE1_ANNOTATORS}


def _locked_sessions(workspace: Path, model: str, packet_path: Path
                     ) -> list[dict[str, Any]]:
    packet_hash = sha_text(Path(packet_path).read_text())
    finalized = [s for s in _load_sessions(workspace, model)
                 if s["finalized"] and s["packet_hash"] == packet_hash]
    if len(finalized) < GATE1_ANNOTATORS:
        raise AnnotationWorkflowError(
            f"{len(finalized)}/{GATE1_ANNOTATORS} annotators finalised; "
            f"agreement and verifier diagnostics stay hidden until every "
            f"required label is locked")
    if len(finalized) > GATE1_ANNOTATORS:
        raise AnnotationWorkflowError(
            f"{len(finalized)} finalised sessions exceed the registered "
            f"{GATE1_ANNOTATORS}; remove the surplus before export")
    return sorted(finalized, key=lambda s: s["annotator"])


def export_annotations(workspace: Path, model: str, packet_path: Path,
                       out_path: Path | None = None) -> Path:
    """The exact external file `gate1 --annotations` accepts."""
    packet = load_packet(packet_path)
    sessions = _locked_sessions(workspace, model, packet_path)
    annotations: dict[str, Any] = {}
    for row in packet:
        labels = []
        for state in sessions:
            entry = state["labels"].get(row["item_id"], {})
            if entry.get("label") not in LABELS:
                raise AnnotationWorkflowError(
                    f"annotator {state['annotator']} lacks a label for a "
                    f"packet item; export refused")
            labels.append(entry["label"])
        annotations[row["item_id"]] = labels
    annotations["face_validity"] = [bool(s["face_validity"])
                                    for s in sessions]
    out_path = Path(out_path) if out_path else \
        Path(workspace) / model / EXPORT_FILENAME
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(annotations, indent=2, sort_keys=True,
                                   ensure_ascii=False) + "\n")
    return out_path


def diagnostics(workspace: Path, model: str, packet_path: Path
                ) -> dict[str, Any]:
    """Post-lock only: agreement, verifier comparison, disagreements."""
    from dci1v3.verifiers.target import s0_count

    packet = load_packet(packet_path)
    sessions = _locked_sessions(workspace, model, packet_path)
    names = [s["annotator"] for s in sessions]
    pair_counts = {(a, b): 0 for i, a in enumerate(names)
                   for b in names[i + 1:]}
    majority_vs_verifier = {"pass": {"items": 0, "disagreements": 0},
                            "fail": {"items": 0, "disagreements": 0}}
    disagreement_items = 0
    for row in packet:
        labels = {s["annotator"]: s["labels"][row["item_id"]]["label"]
                  for s in sessions}
        for (a, b) in pair_counts:
            pair_counts[(a, b)] += labels[a] == labels[b]
        votes = sum(1 for v in labels.values() if v == "pass")
        majority = "pass" if votes * 2 > len(labels) else "fail"
        verifier = ("pass" if s0_count(row["response_text"]) == row["n"]
                    else "fail")
        majority_vs_verifier[verifier]["items"] += 1
        if majority != verifier:
            majority_vs_verifier[verifier]["disagreements"] += 1
            disagreement_items += 1
    total = len(packet)
    return {
        "model": model, "items": total, "annotators": names,
        "pairwise_agreement": {f"{a}|{b}": count / total
                               for (a, b), count in pair_counts.items()},
        "majority_vs_verifier_by_class": majority_vs_verifier,
        "majority_verifier_disagreements": disagreement_items,
        "face_validity": [bool(s["face_validity"]) for s in sessions],
    }
