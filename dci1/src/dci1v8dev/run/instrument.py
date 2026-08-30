"""Stage 6, ``GATE_1_INSTRUMENT``, and the instrument measurements it reads.

The pilot's first question is whether the repaired frames are read
reliably. ``frame_reliability`` measures it on the rows the screen and the
second pass generated: over every load-1 row whose stated constraint is A
or a Tier-1 marker family, per wording index, the share of answers in which
the marker never appears (statistic 0). The criterion
(``stages.FRAME_RELIABILITY_MARGIN``) compares each v8 frame's share with
the best v7 frame's share on the same model, bound in the manifest from the
v7 wording audit. Gate 1 also discharges §7.5's wording-equivalence
obligation over the v8 population, runs the v8 instrument's structural
suite, checks the v8 scorer's determinism on the screen's own corpus, and
freezes both instrument hashes on its record.

**A failed frame criterion terminates nothing.** It is recorded here and
summarised by ``PILOT_REPORT``: the pilot exists to measure it.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from dci1v4.engine import gitinfo
from dci1v4.errors import ProtocolError
from dci1v4.protocol.hashing import sha_obj
from dci1v7.protocol import constants as C
from dci1v7.verifiers.constraints import (FAMILIES, TIER1_FAMILY_IDS,
                                          Constraint, declared_range,
                                          focal_severities)

from dci1v8dev.run import stages as S
from dci1v8dev.run import transitions
from dci1v8dev.run.context import ModelTree, current_files
from dci1v8dev.run.execute import frame_of_row, marker_of
from dci1v8dev.run.lifecycle import (StageOutcome, instrument_hashes,
                                     run_stage)
from dci1v8dev.verifiers.compliance import (graded, passes,
                                            score_generation, statistic)
from dci1v8dev.wordings import (N_WORDINGS, assert_v8_instrument,
                                v8_wordings)

__all__ = ["SUITE_RESPONSES", "v8_wording_suite", "frame_reliability",
           "frame_criterion", "determinism_report", "gate1_payload",
           "run_gate1", "screen_rows"]

#: v7's twenty fixed responses, plus two that carry a v8 frame's own phrase,
#: so the suite covers an answer that echoes the instruction.
SUITE_RESPONSES: tuple[str, ...] = (
    "", "   ", ",,,", "point", "however", "however however however",
    "bold bold bold point clue", "helping helping point clue form",
    "o o o point clue form step", "cell cell bell point clue",
    "point, clue, form, step, unit", "Point Clue Form step unit",
    "area area area point clue", "duty duty duty point clue",
    "counterproductive point clue form",
    "point clue form step unit topic sound result point clue form step unit "
    "topic sound result point clue",
    "point clue form step unit topic sound result point clue form step unit "
    "topic sound result point clue form",
    "İstanbul is big", "however, however, however, area duty cell",
    "ＡＢＣ fullwidth Ⅷ H₂O",
    "The word however must appear here; however it does, however.",
    "Use the word namely exactly once: namely, this.",
)


def _population() -> list[tuple[str, int]]:
    out = [("A", q) for q in C.TARGET_GRID]
    out += [("B", q) for q in focal_severities(extended=True)]
    for kind in FAMILIES:
        out += [(kind, q) for q in declared_range(kind)]
    return out


def v8_wording_suite() -> dict[str, Any]:
    """§7.5 over the v8 population: four distinct wordings per instrument,
    and one verdict whatever the wording (the wording never reaches the
    verifier; the check is that the authored strings state one rule)."""
    checked = 0
    disagreements: list[str] = []
    for kind, severity in _population():
        four = v8_wordings(kind, severity)
        if len(set(four)) != N_WORDINGS:
            raise ProtocolError(
                f"{kind}:{severity} does not have four distinct v8 wordings")
        constraint = (Constraint(kind, severity) if kind == "A"
                      else Constraint(kind, severity, extended=True,
                                      reserve=True))
        for text in SUITE_RESPONSES:
            value = statistic(constraint, text)
            verdicts = {passes(constraint, value, text)}
            scores = {round(graded(constraint, value, text), 12)}
            checked += N_WORDINGS
            if len(verdicts) != 1 or len(scores) != 1:   # pragma: no cover
                disagreements.append(f"{kind}:{severity}")
    return {"responses": len(SUITE_RESPONSES),
            "instruments": len(_population()),
            "verdicts_checked": checked,
            "disagreements": disagreements,
            "passed": not disagreements}


def frame_reliability(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Marker-absent share per wording index over A and MK load-1 rows."""
    by_frame: dict[int, dict[str, Any]] = {
        w: {"n_rows": 0, "marker_absent": 0, "by_family": {}}
        for w in range(N_WORDINGS)}
    for row in rows:
        if row.get("load") != 1:
            continue
        frame = frame_of_row(row)
        if frame is None:
            continue
        present = [s for s in row["scores"] if s.get("present")]
        if len(present) != 1:
            continue
        kind = present[0]["kind"]
        if marker_of(kind) is None:
            continue
        stat = present[0].get("statistic")
        absent = 1 if (stat is None or int(stat) == 0) else 0
        entry = by_frame[frame]
        entry["n_rows"] += 1
        entry["marker_absent"] += absent
        fam = entry["by_family"].setdefault(kind, {"n_rows": 0,
                                                   "marker_absent": 0})
        fam["n_rows"] += 1
        fam["marker_absent"] += absent
    out: dict[str, Any] = {"by_frame": {}, "families": sorted(
        {k for e in by_frame.values() for k in e["by_family"]})}
    total_n = total_abs = 0
    for w, entry in by_frame.items():
        n, a = entry["n_rows"], entry["marker_absent"]
        total_n += n
        total_abs += a
        out["by_frame"][str(w)] = {
            "n_rows": n, "marker_absent": a,
            "share": (a / n) if n else None,
            "by_family": {k: {**v, "share": (v["marker_absent"] / v["n_rows"])
                              if v["n_rows"] else None}
                          for k, v in sorted(entry["by_family"].items())}}
    out["pooled"] = {"n_rows": total_n, "marker_absent": total_abs,
                     "share": (total_abs / total_n) if total_n else None}
    out["statistic"] = ("share of A and MK1-8 load-1 rows whose marker "
                        "statistic is 0, per wording index")
    return out


def frame_criterion(reliability: Mapping[str, Any],
                    reference: Mapping[str, Any] | None, *,
                    margin: float = S.FRAME_RELIABILITY_MARGIN
                    ) -> dict[str, Any]:
    """FRAME_RELIABILITY: every v8 frame's share <= best v7 frame's + margin."""
    if not reference or reference.get("best_v7_frame_share") is None:
        return {"criterion": "FRAME_RELIABILITY", "passed": None,
                "reason": "no v7 frame reference for this model",
                "margin": margin}
    best = float(reference["best_v7_frame_share"])
    limit = best + margin
    per_frame = {}
    verdicts = []
    for w, entry in reliability["by_frame"].items():
        share = entry.get("share")
        ok = None if share is None else bool(share <= limit)
        per_frame[w] = {"share": share, "n_rows": entry["n_rows"],
                        "limit": limit, "passed": ok,
                        "v7_share": (reference.get("shares") or {}).get(w)}
        if ok is not None:
            verdicts.append(ok)
    return {"criterion": "FRAME_RELIABILITY",
            "passed": bool(verdicts) and all(verdicts),
            "per_frame": per_frame,
            "best_v7_frame_share": best,
            "best_v7_frames": reference.get("best_v7_frames"),
            "reference_tree": reference.get("reference_tree"),
            "margin": margin, "limit": limit,
            "rule": "every v8 frame's marker-absent share is at most the "
                    "best v7 frame's share on this model plus the margin"}


def determinism_report(texts: Sequence[str], *, sample: int = 200
                       ) -> dict[str, Any]:
    """The v8 scorer scores the same text to the same verdict, twice, across
    a fixed instrument sample; the digest is what a re-run must reproduce."""
    picked = list(texts)[:sample]
    instruments = [Constraint("A", C.TARGET_GRID[2]),
                   Constraint("B", C.FOCAL_GRID[3])]
    for kind in TIER1_FAMILY_IDS[:3]:
        instruments.append(Constraint(kind, FAMILIES[kind].ladder[1]))
    for kind in ("RF1", "CL1", "XC1"):
        if kind in FAMILIES:
            instruments.append(Constraint(kind, FAMILIES[kind].ladder[0]))

    def digest() -> str:
        verdicts = []
        for text in picked:
            scores = score_generation(text, present=(), absent=tuple(instruments))
            verdicts.append([[s.kind, s.severity, s.statistic, s.passed]
                             for s in scores.scores])
        return sha_obj(verdicts)

    first, second = digest(), digest()
    return {"n_texts": len(picked), "n_instruments": len(instruments),
            "digest": first, "deterministic": first == second}


def screen_rows(tree: ModelTree, *stages: str) -> list[dict[str, Any]]:
    """Every scored row the named generating stages hold, read from disk."""
    import json as _json

    rows: list[dict[str, Any]] = []
    for stage in stages:
        root = tree.backend_runs(stage)
        if not root.exists():
            continue
        for path in current_files(root, "scored.jsonl"):
            for line in path.read_text().splitlines():
                if line.strip():
                    rows.append(_json.loads(line))
    return rows


def gate1_payload(tree: ModelTree, *, producing_commit: str,
                  second_pass_record: Mapping[str, Any],
                  regime_record: Mapping[str, Any],
                  registration_record: Mapping[str, Any],
                  texts: Sequence[str] = ()) -> dict[str, Any]:
    hashes = instrument_hashes()
    bound = registration_record["instrument"]
    if (bound["verifier_hash"], bound["wording_hash"]) != (
            hashes["verifier_hash"], hashes["wording_hash"]):
        raise ProtocolError(
            "the instrument hashes at Gate 1 differ from the ones the pilot "
            "manifest bound; the instrument moved after registration")
    screen_reliability = regime_record["frame_reliability"]
    pass_reliability = second_pass_record.get("frame_reliability")
    pooled_rows = None
    reference = registration_record.get("frame_reference")
    verdict_screen = frame_criterion(screen_reliability, reference)
    verdict_pass = (frame_criterion(pass_reliability, reference)
                    if pass_reliability and pass_reliability["pooled"]["n_rows"]
                    else None)
    determinism = determinism_report(texts) if texts else {
        "n_texts": 0, "deterministic": None}
    return {
        "stage": S.STAGE_GATE1,
        "artifact_type": S.STAGE_ARTIFACT_TYPE[S.STAGE_GATE1],
        "outcome": "PASS",
        "inputs": {"second_pass": {"stage": S.STAGE_SECOND_PASS},
                   "regime": {"stage": S.STAGE_REGIME,
                              "cap": regime_record.get("selected_cap")},
                   "registration": {"stage": S.STAGE_REGISTERED}},
        "producing_commit": producing_commit,
        **hashes,
        "hashes_frozen": ["verifier_hash", "wording_hash"],
        "instrument_assertions": assert_v8_instrument(),
        "wording_suite": v8_wording_suite(),
        "frame_reliability": {"screen": screen_reliability,
                              "second_pass": pass_reliability},
        "frame_criterion": verdict_screen,
        "frame_criterion_second_pass": verdict_pass,
        "frame_reference": reference,
        "determinism": determinism,
        "measurement_basis": C.MEASUREMENT_BASIS,
        "scope_sentence": C.SCOPE_SENTENCE,
        "terminates_nothing": True,
        "_unused": pooled_rows,
    }


def run_gate1(tree: ModelTree, *, producing_commit: str | None = None,
              environment_digest: str = "",
              texts: Sequence[str] | None = None,
              determinism_sample: int = 200) -> StageOutcome:
    commit = producing_commit or gitinfo.head_commit(Path(tree.context.repo_root))
    regime = transitions.read_stage_record(tree, S.STAGE_REGIME)
    registration = transitions.read_stage_record(tree, S.STAGE_REGISTERED)
    corpus = (list(texts) if texts is not None else
              [r["raw_response"] for r in screen_rows(tree, S.STAGE_REGIME)]
              [:determinism_sample])
    return run_stage(
        tree, S.STAGE_GATE1,
        compute=lambda previous: {
            k: v for k, v in gate1_payload(
                tree, producing_commit=commit, second_pass_record=previous,
                regime_record=regime, registration_record=registration,
                texts=corpus).items() if k != "_unused"},
        producing_commit=commit, environment_digest=environment_digest)
