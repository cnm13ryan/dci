"""Retention policies: screen evidence -> forwarding plan.

The seam this module introduces (2026-09-03) separates *what the screen
measured* (``prescreen.evidence``) from *what is forwarded to calibration*
and puts the second thing behind a named policy with one output shape,
``ForwardingPlan``, so the legacy rule and the frame-aware rule can be run
on the same evidence and compared line by line.

* ``LegacyPooledPolicy`` --- the frame-pooled rule the pilots r5--r13 ran:
  ``screen_families`` on the pooled table (one ι_A posterior for all
  frames) and ``retention.retain`` on that one screen; every frame gets
  the same forwarded set. Kept byte-for-byte (the characterization tests
  pin it against the signed r9/r12 records) and reachable only by name.
* ``FrameAwarePolicy`` --- one screen per frame on that frame's own table
  and A-grid (or against a supplied per-frame target, ``coordinate_target``),
  ``retain`` per frame with the same budgets, and a union with provenance:
  ``selected_by_frames[label]`` names every frame whose own evidence
  selected the rung. A rung selected for frame f is forwarded *for f*;
  nothing here makes it admissible on another frame.

**Frame locality, by construction.** ``FrameAwarePolicy.plan`` computes
frame f's screen and retention from ``evidence.by_frame[f]`` and the
config alone, so f's plan is a pure function of f's evidence: changing
another frame's counts cannot move it, and identical evidence on two
frames gives identical plans. ``tests_v8dev/test_prescreen_policy.py``
asserts both.

No policy reads a composed quantity: the evidence schema is
``schema.PrescreenRung`` (closed, refuses composed fields) and a target,
when supplied, is A's solo coordinate.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from dci1v4.errors import ProtocolError
from dci1v7.protocol import constants as C
from dci1v8dev.prescreen.evidence import FRAMES, ScreenEvidence
from dci1v8dev.prescreen.retention import (DEFAULT_RETENTION_CONFIG,
                                           RetentionConfig, retain)
from dci1v8dev.prescreen.screen import (DEFAULT_SCREEN_CONFIG, ScreenConfig,
                                        screen_families)

__all__ = ["LEGACY_POOLED", "FRAME_AWARE", "POLICIES", "TARGET_SCREEN_PROXY",
           "TARGET_CALIBRATION", "ForwardingPlan", "LegacyPooledPolicy",
           "FrameAwarePolicy", "policy_named", "screens_by_frame"]

LEGACY_POOLED = "legacy_pooled"
FRAME_AWARE = "frame_aware"
POLICIES = (LEGACY_POOLED, FRAME_AWARE)
#: What ι_A the frame-aware ranking is taken against: the frame's own
#: screen A-grid posterior (with §12.3's selection inside every draw), or a
#: coordinate supplied from calibration (``screen.coordinate_target``).
TARGET_SCREEN_PROXY = "screen_proxy"
TARGET_CALIBRATION = "calibration_iota_a"


@dataclass(frozen=True)
class ForwardingPlan:
    """What calibration measures, per frame, and why.

    ``by_frame[f]`` holds the frame's forwarded labels, the retention record
    ``retain`` produced for it and the screen summary it was produced from;
    ``union`` is every label some frame forwards; ``selected_by_frames``
    names, per label, the frames whose evidence selected it. Under the
    legacy policy every frame carries the same set and every label names
    every frame.
    """

    policy: str
    target_basis: str
    by_frame: dict[str, dict[str, Any]]
    union: list[str]
    selected_by_frames: dict[str, list[int]]
    generations_per_rung_per_frame: int
    provenance: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.policy not in POLICIES:
            raise ProtocolError(f"unknown retention policy {self.policy!r}")
        for label, frames in self.selected_by_frames.items():
            if label not in self.union:
                raise ProtocolError(f"{label}: selected by {frames} but not "
                                    "in the union")
        for f, entry in self.by_frame.items():
            for label in entry["forwarded"]:
                if int(f) not in self.selected_by_frames.get(label, ()):
                    raise ProtocolError(f"{label}: forwarded for frame {f} "
                                        "without provenance")

    @property
    def frames(self) -> list[int]:
        return sorted(int(f) for f in self.by_frame)

    def forwarded(self, frame: int) -> list[str]:
        return list(self.by_frame[str(frame)]["forwarded"])

    def spectrum_families(self, frame: int) -> list[str]:
        return list(self.by_frame[str(frame)]["retention"]["spectrum_families"])

    @property
    def cost(self) -> dict[str, Any]:
        """Calibration generations: per frame, the frame's own rungs on the
        frame's own blocks; the legacy comparator is the union on every
        block of every frame."""
        per = self.generations_per_rung_per_frame
        by_frame = {f: len(e["forwarded"]) * per for f, e in self.by_frame.items()}
        union_everywhere = len(self.union) * per * len(self.by_frame)
        total = sum(by_frame.values())
        return {"generations_per_rung_per_frame": per,
                "by_frame": by_frame, "total": total,
                "union_on_every_frame": union_everywhere,
                "n_union": len(self.union),
                "n_by_frame": {f: len(e["forwarded"])
                               for f, e in self.by_frame.items()},
                "multiplier_vs_union_everywhere":
                    (total / union_everywhere) if union_everywhere else None}

    def as_record(self) -> dict[str, Any]:
        return {"policy": self.policy, "target_basis": self.target_basis,
                "frames": self.frames,
                "by_frame": {f: {"forwarded": list(e["forwarded"]),
                                 "n_forwarded": len(e["forwarded"]),
                                 "spectrum_families":
                                     list(e["retention"]["spectrum_families"]),
                                 "local_families":
                                     list(e["retention"]["local_families"]),
                                 "screen_statuses": e["screen_statuses"],
                                 "screen_labels": e["screen_labels"],
                                 "iota_a_mean": e["iota_a_mean"],
                                 "iota_a_sd": e["iota_a_sd"],
                                 "n_topics": e["n_topics"],
                                 "retention": e["retention"]}
                             for f, e in sorted(self.by_frame.items())},
                "union": list(self.union),
                "n_union": len(self.union),
                "selected_by_frames": {k: list(v) for k, v in
                                       sorted(self.selected_by_frames.items())},
                "cost": self.cost, "provenance": dict(self.provenance)}


def _frame_entry(screen: Mapping[str, Any], retention: Mapping[str, Any],
                 n_topics: int) -> dict[str, Any]:
    return {"forwarded": [e["candidate"] for e in retention["forwarded"]],
            "retention": retention,
            "screen_statuses": {k: list(v) for k, v in screen["statuses"].items()},
            "screen_labels": {k: list(v) for k, v in screen["labels"].items()},
            "iota_a_mean": float(screen["iota_a"]["iota_a_mean"]),
            "iota_a_sd": float(screen["iota_a"]["iota_a_sd"]),
            "n_topics": int(n_topics)}


class LegacyPooledPolicy:
    """The frame-pooled rule, unchanged: one screen on the pooled table,
    one retention, the same forwarded set for every frame."""

    name = LEGACY_POOLED

    def __init__(self, *, screen_config: ScreenConfig = DEFAULT_SCREEN_CONFIG,
                 retention_config: RetentionConfig = DEFAULT_RETENTION_CONFIG,
                 frames: tuple[int, ...] = FRAMES):
        self.screen_config = screen_config
        self.retention_config = retention_config
        self.frames = tuple(frames)

    def screen(self, evidence: ScreenEvidence) -> dict[str, Any]:
        return screen_families(list(evidence.pooled.table),
                               list(evidence.pooled.a_grid),
                               config=self.screen_config)

    def plan_from_screen(self, screen: Mapping[str, Any], *,
                         n_topics: int) -> ForwardingPlan:
        retention = retain(screen, config=self.retention_config)
        entry = _frame_entry(screen, retention, n_topics)
        labels = list(entry["forwarded"])
        return ForwardingPlan(
            policy=self.name, target_basis=TARGET_SCREEN_PROXY,
            by_frame={str(f): dict(entry) for f in self.frames},
            union=labels,
            selected_by_frames={label: list(self.frames) for label in labels},
            generations_per_rung_per_frame=_per_frame_generations(
                self.retention_config),
            provenance={"pooled_over_frames": True,
                        "reads": "the frame-pooled table and A-grid; one "
                                 "iota_A posterior for every frame"})

    def plan(self, evidence: ScreenEvidence) -> ForwardingPlan:
        return self.plan_from_screen(self.screen(evidence),
                                     n_topics=evidence.pooled.n_topics)


def screens_by_frame(evidence: ScreenEvidence, *, screen_config: ScreenConfig,
                     targets: Mapping[int, Mapping[str, Any]] | None = None
                     ) -> dict[int, dict[str, Any]]:
    """One screen per frame, on that frame's evidence alone; ``targets[f]``
    (``screen.coordinate_target``) replaces frame f's screen-proxy ι_A."""
    out: dict[int, dict[str, Any]] = {}
    for f in evidence.frames:
        e = evidence.by_frame[f]
        target = (targets or {}).get(f)
        out[f] = screen_families(list(e.table), list(e.a_grid),
                                 config=screen_config, target=target)
    return out


class FrameAwarePolicy:
    """One screen and one retention per frame, on that frame's evidence."""

    name = FRAME_AWARE

    def __init__(self, *, screen_config: ScreenConfig = DEFAULT_SCREEN_CONFIG,
                 retention_config: RetentionConfig = DEFAULT_RETENTION_CONFIG):
        self.screen_config = screen_config
        self.retention_config = retention_config

    def plan_from_screens(self, screens: Mapping[int, Mapping[str, Any]], *,
                          n_topics: Mapping[int, int],
                          target_basis: str = TARGET_SCREEN_PROXY,
                          provenance: Mapping[str, Any] | None = None
                          ) -> ForwardingPlan:
        if target_basis not in (TARGET_SCREEN_PROXY, TARGET_CALIBRATION):
            raise ProtocolError(f"unknown target basis {target_basis!r}")
        by_frame: dict[str, dict[str, Any]] = {}
        selected: dict[str, list[int]] = {}
        for f in sorted(screens):
            retention = retain(screens[f], config=self.retention_config)
            entry = _frame_entry(screens[f], retention, n_topics[f])
            by_frame[str(f)] = entry
            for label in entry["forwarded"]:
                selected.setdefault(label, []).append(int(f))
        union = sorted(selected)
        return ForwardingPlan(
            policy=self.name, target_basis=target_basis,
            by_frame=by_frame, union=union,
            selected_by_frames={k: sorted(v) for k, v in selected.items()},
            generations_per_rung_per_frame=_per_frame_generations(
                self.retention_config),
            provenance={"pooled_over_frames": False,
                        "reads": "each frame's own table and A-grid (or the "
                                 "supplied per-frame target); no frame reads "
                                 "another's coordinate",
                        **dict(provenance or {})})

    def plan(self, evidence: ScreenEvidence, *,
             targets: Mapping[int, Mapping[str, Any]] | None = None
             ) -> ForwardingPlan:
        screens = screens_by_frame(evidence, screen_config=self.screen_config,
                                   targets=targets)
        return self.plan_from_screens(
            screens, n_topics={f: evidence.by_frame[f].n_topics for f in screens},
            target_basis=(TARGET_CALIBRATION if targets else TARGET_SCREEN_PROXY),
            provenance={"evidence": dict(evidence.provenance)})


def _per_frame_generations(config: RetentionConfig) -> int:
    """One rung on one frame's calibration blocks: the retention config's
    per-rung figure is the *all-frames* cost (``rules.calibration_generations_per_rung``),
    and a frame holds ``1 / N_WORDINGS`` of the passes' blocks."""
    return int(config.generations_per_rung // C.N_WORDINGS)


def policy_named(name: str, **kwargs: Any):
    if name == LEGACY_POOLED:
        return LegacyPooledPolicy(**kwargs)
    if name == FRAME_AWARE:
        return FrameAwarePolicy(**kwargs)
    raise ProtocolError(f"unknown retention policy {name!r}; registered: "
                        f"{POLICIES}")

