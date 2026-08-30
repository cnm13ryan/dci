#!/usr/bin/env python3
"""Why did a frame fail LOCAL or SPECTRUM — precision, or the reference pool?

After the calibration-allocation amendment (two passes, 96 topics per frame;
`CHANGES_SCIENTIFIC.md` 2026-08-30) the question a pilot has to answer is no
longer "did it pass" but **what is now binding**: is a frame still short of
precision on its coordinates, or is it now precise and stable and simply
short of suitable reference candidates?

This tool decomposes every failing frame from the signed `GATE_2_CALIBRATION`
and `GATE_3_REFERENCES` records alone. Each recorded verdict already carries
its full component list, so nothing is recomputed and no rule is re-run.

**The one distinction it makes, stated up front.** A registered validity
component is either

* a **precision** statement --- how well the coordinate is pinned:
  `V_stab` (§13.7's split-equivalence bootstrap) and the SE clause of
  `V_coord` (`SPECTRUM_MAX_SE_IOTA`). Both get *strictly* easier with more
  calibration topics and neither says anything about the candidate itself;
* a **candidate** statement --- something about the rung: `V_spec`, `V_sat`,
  `V_head`, `V_chance`, `V_struct`, `V_diff`, `V_inter_s`, `V_pos`, and
  `V_coord`'s guard band, vacuity and lift clauses. More topics move these
  only through their intervals, never through their point.

A `V_coord` failure is counted as precision **only when every problem in its
recorded reason is the SE clause**; a rung outside the guard band fails
`V_coord` for a reason no allocation fixes and is counted as a candidate
failure.

**Where that line is generous to the pool.** `V_head`, `V_chance` and
`V_diff` are interval tests (Wilson, Newcombe) formed at the row's topic
count, so their *bounds* also tighten with more calibration topics even
though their point estimates do not. This tool counts them as candidate
failures, because what they test is a property of the rung; a rung failing
one of them only just may still be relieved by allocation. The consequence
is that `REFERENCE_POOL_LIMITED` and `OTHER_REGISTERED_RULE` are the
*conservative* readings here --- they can only understate how much more
precision would buy --- and `PRECISION_LIMITED` is never claimed on their
account.

**The counterfactual, and what it is not.** "Would this frame identify the
arm if precision were free?" is answered by counting the rungs whose
*candidate* components all pass, and comparing that count against the
registered minima (§13.15's five LOCAL-valid families, §13.13's points and
families per spectrum side). That is a diagnosis printed beside the real
verdict; **no selection, admission or record reads it**, and no threshold is
changed anywhere. It says which of two repairs could possibly work, not that
either would.

    python3 tools/v8_bottleneck_diagnosis.py --root <pilot root> --model <key>

Reads nothing past `GATE_3_REFERENCES`, names no composed or interference
quantity, writes `reports/dci1v8dev/bottleneck.<root>.<model>.{md,json}`.
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import statistics
import sys
from typing import Any, Mapping, Sequence

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))

from dci1v7.protocol import constants as C                         # noqa: E402
from dci1v8dev import rules as R                                   # noqa: E402
from dci1v8dev.run import stages as S                              # noqa: E402

REPORTS = HERE.parent / "reports" / "dci1v8dev"
STAGES_READ = (S.STAGE_GATE2, S.STAGE_GATE3)

#: Components whose failure is a statement about how well the coordinate is
#: pinned rather than about the candidate. `V_coord` is conditional: see
#: ``_is_precision_failure``.
PRECISION_COMPONENTS = ("V_stab",)
BOTTLENECKS = ("PRECISION_LIMITED", "REFERENCE_POOL_LIMITED", "MIXED",
               "OTHER_REGISTERED_RULE", "IDENTIFIED")


def _payload(path: pathlib.Path) -> dict[str, Any]:
    record = json.loads(path.read_text())
    return record.get("payload", record)


def _model_dir(root: pathlib.Path, model: str) -> pathlib.Path:
    for base in (root / "evidence" / "dci1v8", root / "dci1v8"):
        if (base / model).is_dir():
            return base / model
    raise SystemExit(f"no model tree for {model!r} under {root}")


def _record(model_dir: pathlib.Path, stage: str) -> dict[str, Any]:
    path = model_dir / stage / S.STAGE_RECORD_FILES[stage]
    if not path.exists():
        raise SystemExit(f"{stage} has no record at {path}")
    return _payload(path)


def _is_precision_failure(component: Mapping[str, Any]) -> bool:
    """Is this failing component a precision statement?"""
    name = component.get("component")
    if name in PRECISION_COMPONENTS:
        return True
    if name != "V_coord":
        return False
    reason = component.get("reason") or ""
    problems = [p.strip() for p in reason.split(";") if p.strip()]
    return bool(problems) and all(p.startswith("SE(iota)") for p in problems)


def _decompose(verdicts: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    """Per-candidate: which components fail, and of what kind."""
    first_failing = collections.Counter()
    precision_only: list[str] = []
    candidate_failures = collections.Counter()
    every_failure = collections.Counter()
    passed: list[str] = []
    for label, verdict in sorted(verdicts.items()):
        if verdict.get("passed"):
            passed.append(label)
            first_failing["PASSED"] += 1
            precision_only.append(label)
            continue
        first_failing[verdict.get("first_failing_component") or "?"] += 1
        failing = [c for c in verdict.get("components", ())
                   if c.get("passed") is False]
        for c in failing:
            every_failure[c["component"]] += 1
        non_precision = [c["component"] for c in failing
                         if not _is_precision_failure(c)]
        if not non_precision:
            precision_only.append(label)
        else:
            candidate_failures[non_precision[0]] += 1
    return {
        "n": len(verdicts),
        "n_passed": len(passed),
        "passed": passed,
        "first_failing": dict(first_failing.most_common()),
        "every_failing_component": dict(every_failure.most_common()),
        "n_failing_only_on_precision": len(precision_only) - len(passed),
        "would_pass_if_precision_were_free": sorted(precision_only),
        "first_candidate_failure": dict(candidate_failures.most_common()),
    }


def _families(labels: Sequence[str]) -> list[str]:
    return sorted({str(x).rpartition(":")[0] for x in labels})


def _frame_diagnosis(g2_frame: Mapping[str, Any], g3_frame: Mapping[str, Any]
                     ) -> dict[str, Any]:
    local = _decompose(g3_frame.get("local") or {})
    spectrum = _decompose(g3_frame.get("spectrum") or {})
    survival = g3_frame.get("survival") or {}
    iota_a = float(g3_frame["iota_a"])

    ses = [v["se_iota"] for v in (g3_frame.get("spectrum") or {}).values()
           if v.get("se_iota") is not None]
    rows = (g2_frame.get("calibration_rows") or {}).get("pooled") or []
    # pool structure, independent of precision: where the rungs sit
    below = [r for r in rows if r.get("chance_compliance", 1) < C.CHANCE_DEGENERACY_MAX
             and _iota(r) is not None and _iota(r) < iota_a]
    above = [r for r in rows if r.get("chance_compliance", 1) < C.CHANCE_DEGENERACY_MAX
             and _iota(r) is not None and _iota(r) > iota_a]
    caliper = [r for r in rows if _iota(r) is not None
               and abs(_iota(r) - iota_a) <= C.REFERENCE_CALIPER]

    # the counterfactual counts, against the registered minima
    cf_local = local["would_pass_if_precision_were_free"]
    cf_spectrum = spectrum["would_pass_if_precision_were_free"]
    cf_below = [lab for lab in cf_spectrum
                if (g3_frame["spectrum"][lab].get("side") == "below")]
    cf_above = [lab for lab in cf_spectrum
                if (g3_frame["spectrum"][lab].get("side") == "above")]
    counterfactual = {
        "rule": "candidates whose every non-precision component passes; a "
                "diagnosis, read by nothing",
        "local_families": _families(cf_local),
        "n_local_families": len(_families(cf_local)),
        "meets_min_local_families":
            len(_families(cf_local)) >= S.MIN_LOCAL_FAMILIES,
        "n_below": len(cf_below), "n_above": len(cf_above),
        "families_below": _families(cf_below), "families_above": _families(cf_above),
        "meets_spectrum_shape": (
            len(cf_below) >= C.SUPPORT_MIN_BELOW
            and len(cf_above) >= C.SUPPORT_MIN_ABOVE
            and len(_families(cf_below)) >= C.SUPPORT_MIN_FAMILIES_PER_SIDE
            and len(_families(cf_above)) >= C.SUPPORT_MIN_FAMILIES_PER_SIDE),
    }

    return {
        "frame": g3_frame.get("frame"),
        "state": g3_frame.get("state"),
        "iota_a": iota_a,
        "n_star": g3_frame.get("n_star"), "m_star": g3_frame.get("m_star"),
        "n_topics_a": g3_frame.get("n_topics_a"),
        "se_iota": {"median": statistics.median(ses) if ses else None,
                    "n": len(ses),
                    "n_within_floor": sum(1 for s in ses
                                          if s <= R.SPECTRUM_MAX_SE_IOTA),
                    "floor": R.SPECTRUM_MAX_SE_IOTA},
        "pool_structure": {
            "n_calibrated_rungs": len(rows),
            "n_below_iota_a": len(below), "n_above_iota_a": len(above),
            "families_below": _families(f"{r['kind']}:{r['severity']}" for r in below),
            "families_above": _families(f"{r['kind']}:{r['severity']}" for r in above),
            "n_within_local_caliper": len(caliper),
            "families_within_local_caliper": _families(
                f"{r['kind']}:{r['severity']}" for r in caliper),
            "caliper": C.REFERENCE_CALIPER,
            "reading": "where the calibrated rungs sit relative to iota_A, "
                       "before any validity rule: a fact about the reference "
                       "pool that no allocation changes"},
        "local": local, "spectrum": spectrum,
        "realised": {
            "core_identified": survival.get("core_identified"),
            "coverage_identified": survival.get("coverage_identified"),
            "n_local_valid_families": survival.get("n_local_valid_families"),
            "local_valid_families": survival.get("local_valid_families"),
            "n_backups": survival.get("n_backups"),
            "n_spectrum_below": len(survival.get("spectrum_valid_below") or ()),
            "n_spectrum_above": len(survival.get("spectrum_valid_above") or ()),
            "coverage_reasons": survival.get("coverage_reasons"),
            "projected_se_beta": survival.get("projected_se_beta"),
        },
        "counterfactual_if_precision_were_free": counterfactual,
        "bottleneck": {
            "local": _classify(
                identified=bool(survival.get("core_identified"))
                and bool(survival.get("meets_min_local_families")),
                counterfactual_ok=counterfactual["meets_min_local_families"],
                decomposition=local,
                pool_note=f"{len(caliper)} rungs from "
                          f"{len(_families(f'{r['kind']}:{r['severity']}' for r in caliper))} "
                          f"families lie inside the {C.REFERENCE_CALIPER} caliper"),
            "spectrum": _classify(
                identified=bool(survival.get("coverage_identified")),
                counterfactual_ok=counterfactual["meets_spectrum_shape"],
                decomposition=spectrum,
                pool_note=f"{len(below)} rungs below and {len(above)} above "
                          "iota_A are calibrated at all"),
        },
    }


def _iota(row: Mapping[str, Any]) -> float | None:
    p, k = row.get("solo_compliance"), row.get("chance_compliance")
    if p is None or k is None or k >= 1.0:
        return None
    return (p - k) / (1.0 - k)


def _classify(*, identified: bool, counterfactual_ok: bool,
              decomposition: Mapping[str, Any], pool_note: str
              ) -> dict[str, Any]:
    n_precision_only = decomposition["n_failing_only_on_precision"]
    candidate_first = decomposition["first_candidate_failure"]
    dominant = next(iter(candidate_first), None)
    dominant_n = candidate_first.get(dominant, 0) if dominant else 0
    n_failing = decomposition["n"] - decomposition["n_passed"]
    share = dominant_n / n_failing if n_failing else 0.0
    if identified:
        verdict, why = "IDENTIFIED", "the arm is identified on this frame"
    elif counterfactual_ok and n_precision_only:
        verdict = "PRECISION_LIMITED"
        why = (f"{n_precision_only} candidate(s) fail only on precision "
               "components, and with those satisfied the registered minima "
               "would be met: more calibration, not more candidates")
    elif not counterfactual_ok and share >= 0.5 and dominant:
        verdict = "OTHER_REGISTERED_RULE"
        why = (f"even with precision free the minima are not met, and "
               f"{dominant} is the first non-precision failure for "
               f"{dominant_n} of {n_failing} failing candidates "
               f"({share:.0%}): one registered rule dominates. {pool_note}")
    elif not counterfactual_ok and n_precision_only:
        verdict = "MIXED"
        why = (f"{n_precision_only} candidate(s) fail only on precision, but "
               "even with precision free the registered minima are not met: "
               f"both repairs are needed. {pool_note}")
    else:
        verdict = "REFERENCE_POOL_LIMITED"
        why = ("no candidate fails on precision alone and the minima are not "
               f"met with precision free: the pool is what is short. {pool_note}")
    return {"vocabulary": list(BOTTLENECKS), "verdict": verdict, "why": why,
            "n_failing_only_on_precision": n_precision_only,
            "dominant_non_precision_failure": dominant,
            "dominant_share_of_failures": share,
            "counterfactual_meets_minima": counterfactual_ok}


def diagnose(model: str, *, gate2: Mapping[str, Any], gate3: Mapping[str, Any]
             ) -> dict[str, Any]:
    supported = [int(w) for w in gate3.get("supported_frames", [])]
    by_frame = {str(w): _frame_diagnosis(gate2["by_frame"][str(w)],
                                         gate3["by_frame"][str(w)])
                for w in supported}
    return {
        "model_key": model,
        "stages_read": list(STAGES_READ),
        "reads_no_composed_outcome": True,
        "calibration_allocation": gate2.get("calibration_allocation"),
        "supported_frames": supported,
        "unsupported_frames": gate3.get("unsupported_frames") or {},
        "precision_components": {
            "always": list(PRECISION_COMPONENTS),
            "conditional": "V_coord, when every problem in its reason is the "
                           "SE(iota) clause",
            "why": "these are the only components whose failure is a "
                   "statement about how well the coordinate is pinned; every "
                   "other component states something about the candidate",
            "caveat": "V_head, V_chance and V_diff are interval tests formed "
                      "at the row's topic count, so their bounds also tighten "
                      "with the allocation even though their points do not. "
                      "Counting them as candidate failures makes "
                      "REFERENCE_POOL_LIMITED and OTHER_REGISTERED_RULE the "
                      "conservative readings and never inflates "
                      "PRECISION_LIMITED"},
        "by_frame": by_frame,
        "summary": {
            "local": {w: v["bottleneck"]["local"]["verdict"]
                      for w, v in by_frame.items()},
            "spectrum": {w: v["bottleneck"]["spectrum"]["verdict"]
                         for w, v in by_frame.items()}},
    }


def markdown(rep: Mapping[str, Any]) -> str:
    out: list[str] = []
    p = out.append
    alloc = rep.get("calibration_allocation") or {}
    per_frame = alloc.get("topics_per_frame", C.N_CALIBRATION // C.N_WORDINGS)
    p("# DCI-1 v8 — what is binding: coordinate precision, or the reference pool?\n")
    p("> Generated by `dci1/tools/v8_bottleneck_diagnosis.py`. Do not edit by hand.\n")
    p("> Reads the signed `GATE_2_CALIBRATION` and `GATE_3_REFERENCES` records "
      "only. Every verdict below is the one those records already carry; the "
      "counterfactual columns are a **diagnosis read by nothing** and change "
      "no threshold.\n")
    p(f"Model `{rep['model_key']}`; calibration at **{per_frame} topics per "
      f"frame** over {alloc.get('passes', 1)} pass(es). Supported frames "
      f"{rep['supported_frames']}; unsupported "
      f"{sorted(rep['unsupported_frames']) or '—'}.\n")
    p("## Bottleneck per frame\n")
    p("| frame | state | ι_A | median SE(ι) | SE within floor | LOCAL bottleneck | SPECTRUM bottleneck |")
    p("|---|---|---:|---:|---|---|---|")
    for w, v in sorted(rep["by_frame"].items()):
        se = v["se_iota"]
        med = "—" if se["median"] is None else f"{se['median']:.4f}"
        p(f"| f{w} | {v['state']} | {v['iota_a']:.3f} | {med} | "
          f"{se['n_within_floor']}/{se['n']} | "
          f"{v['bottleneck']['local']['verdict']} | "
          f"{v['bottleneck']['spectrum']['verdict']} |")
    p("")
    for w, v in sorted(rep["by_frame"].items()):
        p(f"### f{w} — {v['state']}\n")
        for arm in ("local", "spectrum"):
            b = v["bottleneck"][arm]
            p(f"**{arm.upper()}: `{b['verdict']}`** — {b['why']}\n")
            d = v[arm]
            p(f"- first-failing component: "
              + ", ".join(f"`{k}` {n}" for k, n in d["first_failing"].items()))
            p(f"- candidates failing **only** on precision components: "
              f"{d['n_failing_only_on_precision']} of {d['n'] - d['n_passed']} failing")
            p(f"- first *non-precision* failure: "
              + (", ".join(f"`{k}` {n}" for k, n in
                           d["first_candidate_failure"].items()) or "—"))
        cf = v["counterfactual_if_precision_were_free"]
        p(f"- counterfactual (precision free): {cf['n_local_families']} LOCAL "
          f"families ({'meets' if cf['meets_min_local_families'] else 'short of'} "
          f"§13.15's {S.MIN_LOCAL_FAMILIES}); spectrum "
          f"{cf['n_below']} below / {cf['n_above']} above "
          f"({'meets' if cf['meets_spectrum_shape'] else 'short of'} the "
          f"registered shape)")
        ps = v["pool_structure"]
        p(f"- pool structure (no rule applied): {ps['n_below_iota_a']} rungs "
          f"below ι_A from {len(ps['families_below'])} families, "
          f"{ps['n_above_iota_a']} above from {len(ps['families_above'])}; "
          f"{ps['n_within_local_caliper']} inside the {ps['caliper']} caliper "
          f"from {len(ps['families_within_local_caliper'])} families")
        r = v["realised"]
        p(f"- realised: core {r['core_identified']}, coverage "
          f"{r['coverage_identified']}, {r['n_local_valid_families']} "
          f"LOCAL-valid families, {r['n_backups']} backups, spectrum "
          f"{r['n_spectrum_below']} below / {r['n_spectrum_above']} above\n")
    return "\n".join(out) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--out", default=None)
    args = ap.parse_args(argv)
    root = pathlib.Path(args.root).resolve()
    model_dir = _model_dir(root, args.model)
    rep = diagnose(args.model,
                   gate2=_record(model_dir, S.STAGE_GATE2),
                   gate3=_record(model_dir, S.STAGE_GATE3))
    rep["root"] = str(root)
    out = pathlib.Path(args.out) if args.out else REPORTS
    out.mkdir(parents=True, exist_ok=True)
    # named by root as well as model: a later allocation's report must not
    # overwrite an earlier one's, and the file name should say which run it
    # describes.
    stem = f"bottleneck.{root.name}.{args.model}"
    (out / f"{stem}.json").write_text(
        json.dumps(rep, indent=1, sort_keys=True) + "\n")
    (out / f"{stem}.md").write_text(markdown(rep))
    print(f"wrote {out / (stem + '.md')}")
    print("LOCAL:   ", rep["summary"]["local"])
    print("SPECTRUM:", rep["summary"]["spectrum"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
