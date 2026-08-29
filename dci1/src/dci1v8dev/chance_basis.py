"""§13.2's chance basis for the stored Gate-2 tables, read-only, cached.

**Why this module exists.** Every signed v5–v7 Gate-2 record carries
``chance_compliance = 0.0`` for every candidate (`CHANGES_SCIENTIFIC.md`,
2026-08-29, "in force: §13.11's chance column is §13.2's κ_c"): the
producer's absent-instance scan found no grid row stating a non-outcome
candidate and fell back to zero. The quantity §13.2 registers --- the
candidate's compliance on the split's **unconstrained cell** --- was measured
by the grid runs (``backend_runs/grid-A``, ``grid-B``: 192 topics × 8
independent load-zero draws, every carried candidate scored as an absent
instance) and never read. The first v8 development backtests
(``backtest.py`` before 2026-08-29 evening) reconstructed κ from the recorded
ι and therefore inherited the zero column: their V_chance and lift checks
were vacuous on the calibrated tables and every ι was the raw solo rate.

This module reads the unconstrained cells once per replication, in a single
pass over the two grid runs' ``scored.jsonl``, and writes a small cache
(``reports/dci1v8dev/chance_basis/<tree>__<model>.json``) holding, per
candidate label and per split (Calibration-A, Calibration-B, pooled), the
topic-mean compliance and vacuity on that cell --- the same statistic
``dci1v7.run.execute.cell_rates(..., present=False, arm="unconstrained")``
computes, and ``verify_against_cell_rates`` asserts the equality on a sample
so the shortcut is checked, not trusted. ``corrected_gate2`` returns a copy
of the Gate-2 record with the chance column replaced on every split and
ι_A restated on the same basis (the record's ι_A used
``chance_curves["A"]``, the load-zero rows of grid-A *and* the other target
severities' solo cells --- the known basis discrepancy).

Nothing here writes under an evidence root.
"""
from __future__ import annotations

import copy
import hashlib
import json
import pathlib
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

from dci1v4.errors import ProtocolError
from dci1v7.protocol import constants as C

__all__ = [
    "CACHE_DIRNAME",
    "SPLITS",
    "UNCONSTRAINED_ARM",
    "build_cache",
    "build_prescreen_cache",
    "corrected_regime",
    "cache_path",
    "corrected_gate2",
    "iota_from",
    "read_cache",
    "scan_unconstrained",
    "verify_against_cell_rates",
    "write_cache",
]

UNCONSTRAINED_ARM = "unconstrained"
SPLITS = (C.CALIBRATION_A, C.CALIBRATION_B, "pooled")
CACHE_DIRNAME = "chance_basis"
_NEEDLE = '"arm": "unconstrained"'


def iota_from(solo: float, chance: float) -> float | None:
    if chance >= C.CHANCE_DEGENERACY_MAX:
        return None
    return (solo - chance) / (1.0 - chance)


def _sha256(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def scan_unconstrained(gate2_dir: pathlib.Path, *,
                       run_prefix: str | tuple[str, ...] = "grid"
                       ) -> dict[str, Any]:
    """One pass over the runs named ``run_prefix*``: per absent-scored label,
    per split, the per-topic lists of (passed, vacuous_pass) on the
    unconstrained cell. Gate 2's runs are ``grid-A``/``grid-B``; the regime
    screen's ladder run is ``ladder`` (24 pre-screen topics, one draw)."""
    gate2_dir = pathlib.Path(gate2_dir)
    runs = sorted(p for p in (gate2_dir / "backend_runs").iterdir()
                  if p.name.startswith(run_prefix))
    if not runs:
        raise ProtocolError(f"{gate2_dir}: no runs named {run_prefix}* under backend_runs")
    per: dict[str, dict[str, dict[str, list[tuple[int, int]]]]] = {}
    n_rows = 0
    for run in runs:
        with open(run / "scored.jsonl") as f:
            for line in f:
                if _NEEDLE not in line:
                    continue
                r = json.loads(line)
                if r.get("arm") != UNCONSTRAINED_ARM:
                    continue
                n_rows += 1
                split, topic = r.get("topic_split") or "prescreen", r["topic_id"]
                for s in r["scores"]:
                    if s["present"]:
                        continue
                    label = f"{s['kind']}:{s['severity']}"
                    per.setdefault(label, {}).setdefault(split, {}) \
                        .setdefault(topic, []).append(
                            (int(bool(s["passed"])), int(bool(s["vacuous_pass"]))))
    if n_rows == 0:
        raise ProtocolError(f"{gate2_dir}: no unconstrained rows in the grid runs")
    return {"runs": [p.name for p in runs], "n_rows": n_rows, "per": per}


def _rates(topics: Mapping[str, Sequence[tuple[int, int]]]) -> dict[str, Any]:
    names = sorted(topics)
    comp = [sum(p for p, _ in topics[t]) / len(topics[t]) for t in names]
    vac = [sum(v for _, v in topics[t]) / len(topics[t]) for t in names]
    return {"compliance": sum(comp) / len(comp), "vacuity": sum(vac) / len(vac),
            "n_topics": len(names),
            "n_observations": sum(len(topics[t]) for t in names)}


def build_cache(model_dir: pathlib.Path, *, tree: str, model: str
                ) -> dict[str, Any]:
    """The cache record for one replication."""
    model_dir = pathlib.Path(model_dir)
    gate2_dir = model_dir / "GATE_2_FOCAL_CALIBRATION"
    record = gate2_dir / "gate2_focal_calibration.json"
    scan = scan_unconstrained(gate2_dir)
    chance: dict[str, dict[str, Any]] = {}
    for label, by_split in scan["per"].items():
        entry: dict[str, Any] = {}
        pooled: dict[str, list[tuple[int, int]]] = {}
        for split in (C.CALIBRATION_A, C.CALIBRATION_B):
            if split in by_split:
                entry[split] = _rates(by_split[split])
                for t, v in by_split[split].items():
                    pooled.setdefault(t, []).extend(v)
        if pooled:
            entry["pooled"] = _rates(pooled)
        chance[label] = entry
    prescreen = None
    if (model_dir / "REGIME_SCREEN" / "backend_runs").exists():
        prescreen = build_prescreen_cache(model_dir)
    return {"tree": tree, "model": model, "model_dir": str(model_dir),
            "prescreen": prescreen,
            "gate2_record": str(record),
            "gate2_record_sha256": _sha256(record) if record.exists() else None,
            "basis": "§13.2 unconstrained cell of the grid runs, topic-mean "
                     "(draws within topic, then topics), absent-scored "
                     "instances only; arm == 'unconstrained'",
            "runs": scan["runs"], "n_unconstrained_rows": scan["n_rows"],
            "chance": chance, "read_only": True}


def build_prescreen_cache(model_dir: pathlib.Path) -> dict[str, Any]:
    """The regime screen's unconstrained cell (its ``ladder`` run: the 24
    pre-screen topics at one draw), per absent-scored label.

    §12.2's recorded ``chance`` is ``instance_rates`` over *every* row in
    which the instance was absent --- the other candidates' solo answers
    included. For a Tier-3 budget rung that denominator is a different
    population from the unconstrained cell (answers written under another
    constraint satisfy "at most q commas" at another rate), and on the twelve
    stored replications the two differ with SD 0.21 for Tier-3 budget
    families (0.005 for Tier 1). The v8 screen reads κ on the unconstrained
    cell, as §13.2 does at calibration; 24 draws is a noisy basis and the
    screen's posterior carries that noise as ``chance_n = 24``.
    """
    model_dir = pathlib.Path(model_dir)
    regime_dir = model_dir / "REGIME_SCREEN"
    # the ladder run and every §12.6 expansion round (same 24 topics, the
    # selected cap); the cap-selection runs are other generation conditions
    scan = scan_unconstrained(regime_dir, run_prefix=("ladder", "expansion"))
    chance = {}
    for label, by_split in scan["per"].items():
        pooled: dict[str, list[tuple[int, int]]] = {}
        for topics in by_split.values():
            for t, v in topics.items():
                pooled.setdefault(t, []).extend(v)
        chance[label] = _rates(pooled)
    return {"runs": scan["runs"], "n_unconstrained_rows": scan["n_rows"],
            "basis": "§13.2 unconstrained cell of the regime screen's ladder run "
                     "(24 pre-screen topics × 1 draw), topic-mean, absent-scored "
                     "instances only",
            "chance": chance}


def corrected_regime(regime: Mapping[str, Any], prescreen_cache: Mapping[str, Any]
                     ) -> dict[str, Any]:
    """The regime record with §12.2's ``chance`` restated on the unconstrained
    cell (ι recomputed), the recorded column kept beside the table."""
    out = copy.deepcopy(dict(regime))
    chance = prescreen_cache["chance"]
    recorded = {}
    for row in out["difficulty_table"]:
        label = f"{row['kind']}:{row['severity']}"
        cell = chance.get(label)
        if cell is None:
            if row.get("is_outcome") or row["kind"] == "B":
                continue
            raise ProtocolError(f"{label}: not scored on the pre-screen's unconstrained cell")
        if cell["n_topics"] != row["n_topics"]:
            raise ProtocolError(f"{label}: {cell['n_topics']} unconstrained topics "
                                f"against {row['n_topics']} pre-screen topics")
        recorded[label] = row["chance"]
        row["chance"] = cell["compliance"]
        row["chance_vacuity"] = cell["vacuity"]
        row["iota"] = iota_from(row["solo"], row["chance"])
    out["chance_recorded"] = recorded
    out["chance_basis"] = {"rule": prescreen_cache["basis"],
                           "runs": prescreen_cache["runs"],
                           "n_unconstrained_rows": prescreen_cache["n_unconstrained_rows"]}
    return out


def cache_path(cache_dir: pathlib.Path, *, tree: str, model: str) -> pathlib.Path:
    return pathlib.Path(cache_dir) / f"{tree}__{model}.json"


def write_cache(cache: Mapping[str, Any], cache_dir: pathlib.Path) -> pathlib.Path:
    cache_dir = pathlib.Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = cache_path(cache_dir, tree=cache["tree"], model=cache["model"])
    path.write_text(json.dumps(cache, indent=1, sort_keys=True))
    return path


def read_cache(cache_dir: pathlib.Path, *, tree: str, model: str) -> dict[str, Any]:
    path = cache_path(cache_dir, tree=tree, model=model)
    if not path.exists():
        raise ProtocolError(
            f"no chance-basis cache at {path}; run "
            "tools/v8_chance_basis_cache.py --evidence <root> first (the "
            "recorded Gate-2 chance column is the zero column and is never "
            "read by a v8 backtest)")
    with open(path) as f:
        return json.load(f)


def corrected_gate2(gate2: Mapping[str, Any], cache: Mapping[str, Any]
                    ) -> dict[str, Any]:
    """The Gate-2 record with §13.2's chance column and ι_A on that basis.

    Refuses a candidate/split whose unconstrained cell covers a different
    topic count from its solo cell (the cells must share the topic set).
    """
    if cache.get("gate2_record_sha256") and gate2.get("_sha256") \
            and cache["gate2_record_sha256"] != gate2["_sha256"]:
        raise ProtocolError("chance cache was built from a different Gate-2 record")
    out = copy.deepcopy(dict(gate2))
    chance = cache["chance"]
    #: The recorded column, kept beside the table (never inside a row: the
    #: §13.11 schema is closed and refuses an unlisted column).
    recorded: dict[str, dict[str, float]] = {}
    for split in SPLITS:
        rows = out["calibration_rows"][split]
        for row in rows:
            label = f"{row['kind']}:{row['severity']}"
            cell = chance.get(label, {}).get(split)
            if cell is None:
                raise ProtocolError(f"{label} on {split}: no unconstrained cell in the cache")
            if cell["n_topics"] != row["n_topics"]:
                raise ProtocolError(
                    f"{label} on {split}: {cell['n_topics']} unconstrained topics "
                    f"against {row['n_topics']} solo topics")
            recorded.setdefault(split, {})[label] = row["chance_compliance"]
            row["chance_compliance"] = cell["compliance"]
    # §11.2 on the corrected table, exactly as the Gate-2 fix
    # (run/gates_run._withhold_degenerate) does: a row whose κ_c is at or
    # above CHANCE_DEGENERACY_MAX has no coordinate and leaves the table of
    # the split it is degenerate on; it is recorded beside it with its values.
    withheld: dict[str, list[dict[str, Any]]] = {}
    for split in SPLITS:
        kept, gone = [], []
        for row in out["calibration_rows"][split]:
            if float(row["chance_compliance"]) < C.CHANCE_DEGENERACY_MAX:
                kept.append(row)
            else:
                gone.append({**row, "status": "DIFFICULTY_COORDINATE_DEGENERATE",
                             "why": f"chance compliance {row['chance_compliance']:.4f} at or "
                                    f"above {C.CHANCE_DEGENERACY_MAX} on the §13.2 basis"})
        out["calibration_rows"][split] = kept
        withheld[split] = gone
    out["calibration_rows_withheld"] = withheld
    n_star = int(gate2["n_star"])
    a_label = f"A:{n_star}"
    if a_label not in chance:
        raise ProtocolError(f"{a_label}: A's severity is not scored on the unconstrained cell")
    out["chance_compliance_recorded"] = recorded
    out["iota_a_recorded"] = gate2["iota_a"]
    out["iota_a_by_split_recorded"] = dict(gate2["iota_a_by_split"])
    k_pooled = chance[a_label]["pooled"]["compliance"]
    iota_a = iota_from(float(gate2["solo_compliance_a"]), k_pooled)
    if iota_a is None:
        raise ProtocolError("A is degenerate on the unconstrained basis")
    out["iota_a"] = iota_a
    out["kappa_a"] = k_pooled
    by_split = {}
    for split in (C.CALIBRATION_A, C.CALIBRATION_B):
        k = chance[a_label][split]["compliance"]
        by_split[split] = iota_from(float(gate2["solo_a_by_split"][split]), k)
    out["iota_a_by_split"] = by_split
    out["chance_basis"] = {"rule": cache["basis"], "runs": cache["runs"],
                           "n_unconstrained_rows": cache["n_unconstrained_rows"],
                           "source": "dci1v8dev.chance_basis (read-only cache)"}
    return out


def verify_against_cell_rates(gate2_dir: pathlib.Path, cache: Mapping[str, Any],
                              labels: Iterable[str]) -> dict[str, Any]:
    """Check the single-pass statistic against the production kernel on a
    sample of labels (every split). Raises on any disagreement."""
    from dci1v7.run.execute import cell_rates
    rows = []
    gate2_dir = pathlib.Path(gate2_dir)
    for run in sorted(p for p in (gate2_dir / "backend_runs").iterdir()
                      if p.name.startswith("grid")):
        with open(run / "scored.jsonl") as f:
            for line in f:
                if _NEEDLE not in line:
                    continue
                r = json.loads(line)
                if r.get("arm") != UNCONSTRAINED_ARM:
                    continue
                rows.append({"topic_split": r["topic_split"], "arm": r["arm"],
                             "topic_id": r["topic_id"], "word_count": r["word_count"],
                             "truncated": r["truncated"],
                             "scores": [s for s in r["scores"] if not s["present"]]})
    checked = []
    for label in labels:
        kind, sev = label.split(":")
        for split in SPLITS:
            got = cache["chance"][label][split]
            ref = cell_rates(rows, kind=kind, severity=int(sev), present=False,
                             split=None if split == "pooled" else split,
                             arm=UNCONSTRAINED_ARM)
            if abs(got["compliance"] - ref["compliance"]) > 1e-12 or \
                    got["n_topics"] != ref["n_topics"] or \
                    abs(got["vacuity"] - ref["vacuity"]) > 1e-12:
                raise ProtocolError(f"{label}/{split}: cache {got} != cell_rates {ref}")
            checked.append((label, split))
    return {"checked": checked, "n": len(checked), "agree": True}
