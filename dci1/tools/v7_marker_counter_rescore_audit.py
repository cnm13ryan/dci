#!/usr/bin/env python3
"""Offline rescoring audit for the A / MK marker-counter unification.

**What is being checked.** Before the unification, A's counter (``s0_count``,
carried from v3 through ``dci1v4.verifiers.target``) lower-cased the whole
response and then segmented it; the eight Tier-1 marker counters segmented the
response and then lower-cased each word (§9.2's convention for every word
list). The two orders differ on exactly one character of Unicode, U+0130
LATIN CAPITAL LETTER I WITH DOT ABOVE (``verifiers/words.py``
``assert_single_splitter``). After the unification A and MK1-MK8 are one
function, ``verifiers.statistics.marker_count(text, word)``, in §9.2's order.

This tool reads every stored ``scored.jsonl`` row under the evidence roots
named on the command line **read-only**, and for every A and every marker
verdict the row carries it computes

* ``stored``  --- the statistic the row recorded when it was scored;
* ``old``     --- the pre-unification counter (A: fold-then-segment;
                  MK: segment-then-fold, unchanged);
* ``new``     --- the unified counter (segment-then-fold for both).

It reports how many statistics, pass verdicts and graded scores would move,
and lists every row on which any of them would. It rewrites nothing.

**Exactness.** A row's A or MK statistic can differ between the two orders
only if the response contains U+0130 (the enumeration in ``words.py`` is the
proof, and ``tests_v7/test_marker_counter_unification.py`` re-runs it). Every
row is therefore scanned for U+0130 at byte level, and every row that carries
it is fully recomputed under both orders. Rows without it are recomputed under
the unified counter only when ``--recompute-every`` selects them, as a
reproduction check that the stored statistic is what the counter computes.

Usage::

    python3 tools/v7_marker_counter_rescore_audit.py \
        --evidence /path/to/dci1/evidence --roots dci1v7 dci1v6 ... \
        --out reports/dci1v7/development/marker_counter_unification_audit.json
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

DCI1 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DCI1 / "src"))

from dci1v4.verifiers.target import s0_count as _fold_then_segment_a
from dci1v4.verifiers.words import alpha_runs
from dci1v7.verifiers.constraints import MARKER_WORDS, TARGET_WORD

SPLITTER = "İ"

#: family kind -> marker word, for the eight Tier-1 families and for A.
_MARKER_OF_KIND: dict[str, str] = {"A": TARGET_WORD}
_MARKER_OF_KIND.update({
    kind: MARKER_WORDS[statistic_id]
    for kind, statistic_id in (("MK1", "marker_thus"), ("MK2", "marker_hence"),
                               ("MK3", "marker_though"),
                               ("MK4", "marker_whereas"),
                               ("MK5", "marker_indeed"),
                               ("MK6", "marker_namely"),
                               ("MK7", "marker_instead"),
                               ("MK8", "marker_overall"))
})
#: v4r4's single marker family, so its rows are audited under the same rule.
_MARKER_OF_KIND["CX1"] = "thus"


def segment_then_fold(text: str, word: str) -> int:
    """The unified counter, restated here so the audit does not depend on
    which revision of ``dci1v7.verifiers.statistics`` is importable."""
    return sum(1 for run in alpha_runs(text) if run.lower() == word)


class _RowCounts:
    """Both orders, segmented once per row and read per verdict.

    ``fold_first`` is the word histogram under the pre-unification A rule
    (``alpha_runs(text.lower())``) and ``segment_first`` under §9.2's order.
    ``old_counter``/``new_counter`` are the per-entry rules the audit
    reports; the histograms only make them O(1) per verdict.
    """

    def __init__(self, text: str):
        from collections import Counter
        self.fold_first = Counter(alpha_runs(text.lower()))
        self.segment_first = Counter(run.lower() for run in alpha_runs(text))
        self._text = text

    def old(self, kind: str) -> int:
        if kind == "A":
            return self.fold_first[TARGET_WORD]
        return self.segment_first[_MARKER_OF_KIND[kind]]

    def new(self, kind: str) -> int:
        return self.segment_first[_MARKER_OF_KIND[kind]]


def old_counter(kind: str, text: str) -> int:
    if kind == "A":
        return _fold_then_segment_a(text)
    return segment_then_fold(text, _MARKER_OF_KIND[kind])


def new_counter(kind: str, text: str) -> int:
    return segment_then_fold(text, _MARKER_OF_KIND[kind])


def _assert_histograms_match_counters() -> None:
    """The O(1) reading and the per-entry rule agree on the shapes that
    separate the two orders; run once at start-up."""
    for text in ("İhowever thus", "however İ Thus", "İhowever however",
                 "howeverİ", "HOWEVER, thus; Hence", "İstanbul hence"):
        counts = _RowCounts(text)
        for kind in _MARKER_OF_KIND:
            assert counts.old(kind) == old_counter(kind, text), (kind, text)
            assert counts.new(kind) == new_counter(kind, text), (kind, text)


def _graded(statistic: int, q: int) -> float:
    return max(0.0, 1.0 - abs(statistic - q) / q)


def audit_file(args: tuple[str, int]) -> dict[str, Any]:
    path, recompute_every = args
    out: dict[str, Any] = {
        "file": path, "rows": 0, "rows_with_u0130": 0,
        "entries_checked": 0, "entries_recomputed": 0,
        "reproduction_mismatches": [], "changed": [],
        "kinds_seen": {},
    }
    with open(path, "rb") as handle:
        for index, raw in enumerate(handle):
            if not raw.strip():
                continue
            out["rows"] += 1
            # Decode before looking for the splitter. The two writers in this
            # repository disagree about escaping: `dci1v4.engine.fs` and
            # `.store` dump with ensure_ascii=False, so U+0130 is stored as
            # its UTF-8 bytes, while `dci1v7.run.execute` takes json.dumps'
            # default ensure_ascii=True and stores it as the ASCII escape
            # \u0130. A byte search finds the first and can never find the
            # second, which would silently under-count `rows_with_u0130` on
            # every v7-written file --- and, worse, let the skip below drop
            # exactly the rows the audit exists to examine. Parsing every row
            # costs the parse and keeps the promise.
            row = json.loads(raw)
            text = row.get("raw_response") or ""
            has_splitter = SPLITTER in text
            if has_splitter:
                out["rows_with_u0130"] += 1
            if not has_splitter and (recompute_every <= 0
                                     or index % recompute_every):
                continue
            counts = _RowCounts(text)
            for score in row.get("scores", ()):
                kind = score.get("kind")
                if kind not in _MARKER_OF_KIND:
                    continue
                q = int(score["severity"])
                stored = score.get("statistic")
                old = counts.old(kind)
                new = counts.new(kind)
                out["entries_checked"] += 1
                out["kinds_seen"][kind] = out["kinds_seen"].get(kind, 0) + 1
                if not has_splitter:
                    out["entries_recomputed"] += 1
                if stored is not None and int(stored) != old:
                    out["reproduction_mismatches"].append({
                        "row_id": row.get("row_id"), "kind": kind,
                        "severity": q, "stored": stored, "old": old})
                if old != new:
                    out["changed"].append({
                        "row_id": row.get("row_id"), "kind": kind,
                        "severity": q, "stored": stored, "old": old,
                        "new": new,
                        "pass_old": old == q, "pass_new": new == q,
                        "graded_old": _graded(old, q),
                        "graded_new": _graded(new, q),
                        "present": score.get("present"),
                        "study_id": row.get("study_id"),
                        "stage": row.get("stage"),
                        "model_key": row.get("model_key")})
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--evidence", required=True,
                        help="the dci1/evidence directory (read only)")
    parser.add_argument("--roots", nargs="+", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--recompute-every", type=int, default=1,
                        help="full recompute on every Nth row without "
                             "U+0130 (0 disables; rows with U+0130 are "
                             "always recomputed)")
    ns = parser.parse_args(argv)
    _assert_histograms_match_counters()
    evidence = Path(ns.evidence)
    files: list[tuple[str, str]] = []
    for root in ns.roots:
        for path in sorted((evidence / root).rglob("scored.jsonl")):
            files.append((root, str(path)))
    started = _dt.datetime.now(_dt.UTC).isoformat()
    per_root: dict[str, dict[str, Any]] = {
        root: {"files": 0, "rows": 0, "rows_with_u0130": 0,
               "entries_checked": 0, "entries_recomputed": 0,
               "reproduction_mismatches": 0, "statistics_changed": 0,
               "verdicts_changed": 0, "graded_changed": 0,
               "kinds_seen": {}} for root in ns.roots}
    changed_rows: list[dict[str, Any]] = []
    mismatches: list[dict[str, Any]] = []
    with ProcessPoolExecutor(max_workers=ns.workers) as pool:
        results = pool.map(audit_file, [(p, ns.recompute_every)
                                        for _, p in files])
        for (root, path), result in zip(files, results):
            summary = per_root[root]
            summary["files"] += 1
            for key in ("rows", "rows_with_u0130", "entries_checked",
                        "entries_recomputed"):
                summary[key] += result[key]
            for kind, n in result["kinds_seen"].items():
                summary["kinds_seen"][kind] = \
                    summary["kinds_seen"].get(kind, 0) + n
            for item in result["reproduction_mismatches"]:
                summary["reproduction_mismatches"] += 1
                mismatches.append({"root": root, "file": path, **item})
            for item in result["changed"]:
                summary["statistics_changed"] += 1
                if item["pass_old"] != item["pass_new"]:
                    summary["verdicts_changed"] += 1
                if item["graded_old"] != item["graded_new"]:
                    summary["graded_changed"] += 1
                changed_rows.append({"root": root, "file": path, **item})
            print(f"{root}: {Path(path).relative_to(evidence / root)} "
                  f"rows={result['rows']} u0130={result['rows_with_u0130']} "
                  f"changed={len(result['changed'])}", flush=True)
    totals = {k: sum(r[k] for r in per_root.values())
              for k in ("files", "rows", "rows_with_u0130", "entries_checked",
                        "entries_recomputed", "reproduction_mismatches",
                        "statistics_changed", "verdicts_changed",
                        "graded_changed")}
    a_changed = sum(1 for c in changed_rows if c["kind"] == "A")
    mk_changed = sum(1 for c in changed_rows if c["kind"] != "A")
    a_verdicts = sum(1 for c in changed_rows
                     if c["kind"] == "A" and c["pass_old"] != c["pass_new"])
    mk_verdicts = sum(1 for c in changed_rows
                      if c["kind"] != "A" and c["pass_old"] != c["pass_new"])
    record = {
        "tool": "tools/v7_marker_counter_rescore_audit.py",
        "started_utc": started,
        "finished_utc": _dt.datetime.now(_dt.UTC).isoformat(),
        "evidence": str(evidence), "roots": ns.roots,
        "recompute_every": ns.recompute_every,
        "rule": {
            "old_A": "dci1v4.verifiers.target.s0_count: lower-case the whole "
                     "response, segment, count runs == 'however' "
                     "(fold-then-segment)",
            "old_MK": "segment, lower-case each run, count runs == marker "
                      "(segment-then-fold)",
            "new_A_and_MK": "marker_count(text, word): segment, lower-case "
                            "each run, count runs == word "
                            "(segment-then-fold) for A and MK1-MK8 alike",
            "only_separating_character": "U+0130",
        },
        "totals": totals,
        "summary": {
            "A_statistics_changed": a_changed,
            "A_verdicts_changed": a_verdicts,
            "MK_statistics_changed": mk_changed,
            "MK_verdicts_changed": mk_verdicts,
        },
        "per_root": per_root,
        "changed_rows": changed_rows,
        "reproduction_mismatches": mismatches,
        "read_only": True,
        "note": "rows under roots still being written at audit time are a "
                "snapshot; the tool reads and rewrites nothing",
    }
    out = Path(ns.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(record, indent=1, ensure_ascii=False) + "\n")
    print(json.dumps({"totals": totals, "summary": record["summary"]},
                     indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
