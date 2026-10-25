"""Score pilot responses and aggregate them into compliance tables.

Every behavioural response is scored against **every** library constraint
(A candidates, B candidates, all 51 references). The one the prompt stated
is ``present``; every other verdict is spontaneous. Three tables come out,
and they are kept apart on purpose:

* ``explicit``  --- (model, frame, condition): compliance with the stated
  constraint. p_A, p_B and p_X are read here.
* ``task_only`` --- (model, constraint): spontaneous compliance on
  task-only responses. This is kappa, the chance coordinate for iota.
* ``b_only``    --- (model, frame, m, constraint): spontaneous compliance on
  B_m-only responses. Reported; never substituted for kappa.

Only behavioural rows are scored (``outcomes.classify``: VALID or EMPTY).
A technical failure never reaches this module: the runner keeps it out of
``rows.jsonl``, and ``score_row`` refuses one if it arrives anyway. Empty
and truncated answers are behavioural: they are in every denominator and
never comply (D04).

Each scored record carries ``generation_hash``, the canonical hash of the
generated row it was computed from, so a score can always be traced to, and
checked against, the exact response text (Freeze 2 re-derives every record).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping

from dci.batch1 import library as L
from dci.batch1 import outcomes as OUT
from dci.batch1 import text as T
from dci.batch1 import verifiers as V
from dci.batch1.design import TASK_ONLY
from dci.batch1.store import index_rows, record_hash

__all__ = ["score_row", "score_rows", "PilotTables", "build_tables", "Count",
           "ScoringError"]


class ScoringError(ValueError):
    """A generated row that cannot be scored as pilot evidence."""


_STRUCTURE_LINE = re.compile(r"^\s*(#{1,6}\s|[-*+]\s|\d+[.)]\s|>\s)")


def structure_lines(text: str) -> int:
    """Markdown heading, list and quote lines: a diagnostic for D03."""
    return sum(1 for line in text.splitlines() if _STRUCTURE_LINE.match(line))


def score_row(raw: Mapping[str, Any], design: Mapping[str, Any],
              constraints: Iterable[L.Constraint] | None = None, *,
              bundle_hash: str | None = None) -> dict[str, Any]:
    """One generated row -> its scored record."""
    constraints = tuple(L.all_constraints() if constraints is None
                        else constraints)
    bundle_hash = bundle_hash or V.verifier_bundle_hash()
    if raw.get("row_id") != design["row_id"]:
        raise ScoringError(f"row {raw.get('row_id')} answers design row "
                           f"{design['row_id']}")
    if raw.get("identity_hash") != design["identity_hash"]:
        raise ScoringError(f"{design['row_id']}: identity changed in transit")
    if design["load"] > 1:
        raise ScoringError("a composed row cannot be scored by the pilot")
    cls = OUT.classify(raw)
    if not cls.behavioural:
        raise ScoringError(f"{design['row_id']}: {cls.reason}; a technical "
                           "failure is not behavioural evidence")
    text = raw["final_answer"] if cls.kind == OUT.VALID else ""
    truncated = bool(raw.get("answer_truncated"))
    stated = design["condition"]
    scores = {}
    for c in constraints:
        s = V.score_constraint(c.cid, c.family.verifier_id,
                               c.verifier_params(), c.family.vacuity, text,
                               present=c.cid == stated, truncated=truncated)
        scores[c.cid] = [s.scored, s.verdict, s.compliant, s.non_vacuous,
                         s.statistic, s.error]
    state = V.generation_state(text, truncated=truncated, behavioural=True)
    return {"row_id": design["row_id"], "stage": design["stage"],
            "model": design["model"], "frame": design["frame"],
            "condition": stated, "topic_id": design["topic_id"],
            "draw": design["draw"], "state": state,
            "outcome": raw.get("outcome"), "outcome_class": cls.kind,
            "finish_reason": raw.get("finish_reason", ""),
            "word_count": T.word_count(text),
            "format_characters": T.format_characters(text),
            "structure_lines": structure_lines(text),
            "refusal_like": OUT.refusal_like(text),
            "generation_hash": record_hash(raw),
            "verifier_bundle_hash": bundle_hash,
            "scores": scores}


def score_rows(raws: Iterable[Mapping[str, Any]],
               designs: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Score accepted rows once each; an identical repeat collapses, a
    conflicting one is refused (``store.index_rows``)."""
    by_id = {d["row_id"]: d for d in designs}
    raws_by_id, _ = index_rows(raws, what="generated rows")
    constraints = L.all_constraints()
    bundle_hash = V.verifier_bundle_hash()
    out = []
    for rid, raw in raws_by_id.items():
        if rid not in by_id:
            raise ScoringError(f"generated row {rid} is not in the design")
        out.append(score_row(raw, by_id[rid], constraints,
                             bundle_hash=bundle_hash))
    return out


@dataclass
class Count:
    k: int = 0              # compliant (primary, D04)
    n: int = 0              # behavioural rows: valid + empty
    planned: int = 0
    truncated: int = 0
    empty: int = 0
    literal_pass: int = 0   # verdict PASS, whatever the state
    vacuous_pass: int = 0   # PASS on a scorable answer under the word floor
    truncated_pass: int = 0
    empty_pass: int = 0
    unscored: int = 0       # verifier error: in n, never compliant
    refusal_like: int = 0   # diagnostic only

    @property
    def p(self) -> float | None:
        return self.k / self.n if self.n else None

    @property
    def p_literal(self) -> float | None:
        return self.literal_pass / self.n if self.n else None

    def state(self) -> dict[str, Any]:
        return {name: getattr(self, name) for name in _COUNT_FIELDS}

    @classmethod
    def from_state(cls, s: Mapping[str, Any]) -> "Count":
        return cls(**{k: int(v) for k, v in s.items()})


_COUNT_FIELDS = ("k", "n", "planned", "truncated", "empty", "literal_pass",
                 "vacuous_pass", "truncated_pass", "empty_pass", "unscored",
                 "refusal_like")


def _key(*parts: Any) -> str:
    return "|".join("-" if p is None else str(p) for p in parts)


@dataclass
class PilotTables:
    explicit: dict[str, Count] = field(default_factory=dict)
    task_only: dict[str, Count] = field(default_factory=dict)
    b_only: dict[str, Count] = field(default_factory=dict)
    synthetic: bool = False

    # Readers. Each returns a Count (empty when the cell does not exist).
    def x(self, model: str, frame: str, cid: str) -> Count:
        return self.explicit.get(_key(model, frame, cid), Count())

    def kappa(self, model: str, cid: str) -> Count:
        return self.task_only.get(_key(model, cid), Count())

    def kappa_b(self, model: str, frame: str, m: int, cid: str) -> Count:
        return self.b_only.get(_key(model, frame, m, cid), Count())

    def state(self) -> dict[str, Any]:
        return {"schema": "dci.batch1/pilot-tables/v2",
                "synthetic": self.synthetic,
                "explicit": {k: v.state() for k, v in sorted(self.explicit.items())},
                "task_only": {k: v.state() for k, v in sorted(self.task_only.items())},
                "b_only": {k: v.state() for k, v in sorted(self.b_only.items())}}

    @classmethod
    def from_state(cls, s: Mapping[str, Any]) -> "PilotTables":
        return cls({k: Count.from_state(v) for k, v in s["explicit"].items()},
                   {k: Count.from_state(v) for k, v in s["task_only"].items()},
                   {k: Count.from_state(v) for k, v in s["b_only"].items()},
                   bool(s.get("synthetic")))


_EXCLUDED = {"vacuous": "vacuous_pass", "truncated": "truncated_pass",
             "empty": "empty_pass"}


def _tally(count: Count, entry: list[Any], row: Mapping[str, Any]) -> None:
    scored, verdict, compliant, non_vacuous = entry[:4]
    state = row["state"]
    if state not in (V.STATE_SCORABLE, V.STATE_TRUNCATED, V.STATE_EMPTY):
        raise ScoringError(f"{row['row_id']}: state {state!r} is not "
                           "behavioural and cannot be tallied")
    count.n += 1
    count.truncated += state == V.STATE_TRUNCATED
    count.empty += state == V.STATE_EMPTY
    count.refusal_like += bool(row.get("refusal_like"))
    if not scored:
        count.unscored += 1
        return
    count.k += bool(compliant)
    if verdict == "PASS":
        count.literal_pass += 1
        if not compliant:
            excluded = {V.STATE_SCORABLE: "vacuous",
                        V.STATE_TRUNCATED: "truncated",
                        V.STATE_EMPTY: "empty"}[state]
            name = _EXCLUDED[excluded]
            setattr(count, name, getattr(count, name) + 1)


def build_tables(scored: Iterable[Mapping[str, Any]],
                 designs: Iterable[Mapping[str, Any]], *,
                 synthetic: bool = False) -> PilotTables:
    """Aggregate scored rows, pooling stages within a cell."""
    tables = PilotTables(synthetic=synthetic)
    b_limit = {c.cid: c.p["m"] for c in L.b_candidates()}
    cids = [c.cid for c in L.all_constraints()]
    for d in designs:
        if d["condition"] == TASK_ONLY:
            for cid in cids:
                tables.task_only.setdefault(_key(d["model"], cid),
                                            Count()).planned += 1
            continue
        tables.explicit.setdefault(
            _key(d["model"], d["frame"], d["condition"]), Count()).planned += 1
        if d["condition"] in b_limit:
            for cid in cids:
                if cid not in b_limit:
                    tables.b_only.setdefault(
                        _key(d["model"], d["frame"], b_limit[d["condition"]],
                             cid), Count()).planned += 1
    seen: set[str] = set()
    for row in scored:
        if row["row_id"] in seen:
            raise ScoringError(f"{row['row_id']} is scored twice")
        seen.add(row["row_id"])
        model, frame, cond = row["model"], row["frame"], row["condition"]
        if cond == TASK_ONLY:
            for cid, entry in row["scores"].items():
                _tally(tables.task_only.setdefault(_key(model, cid), Count()),
                       entry, row)
            continue
        _tally(tables.explicit.setdefault(_key(model, frame, cond), Count()),
               row["scores"][cond], row)
        if cond in b_limit:
            for cid, entry in row["scores"].items():
                if cid in b_limit:
                    continue
                _tally(tables.b_only.setdefault(
                    _key(model, frame, b_limit[cond], cid), Count()),
                    entry, row)
    return tables
