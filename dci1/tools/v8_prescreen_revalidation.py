#!/usr/bin/env python3
"""Old versus successor: the v8 (pooled-screen) pilot roots beside the v8.1
(frame-aware) successor roots, per model x frame, with every change
attributed to the changed screen where the record lets it be.

Read-only, zero generation. Reads the signed pilot records of both root
sets (``REGIME_SCREEN``, ``SECOND_PASS_SCREEN``, ``GATE_2_CALIBRATION``,
``GATE_3_REFERENCES``, ``PILOT_REPORT`` where present); opens no
confirmatory stage and refuses a protected path. A successor root that has
not reached a stage is reported as pending for that stage.

Per model x frame it tabulates: Gate-2 support, n*(f), m*(f), iota_A(f) and
its SE (old and new), the forwarded set sizes (old: the pooled set; new:
the frame's own set, the provisional screen-proxy set and the legacy
comparator set on the same run), LOCAL-valid / SPECTRUM-valid counts, the
frame state, the §13.15 survival facts, LOCAL support and model
eligibility --- and, from ``GATE_3_REFERENCES.retention_comparison``, the
identification each comparator policy reaches on the *same* calibration
rows, which is what separates the effect of the forwarding rule from
fresh-sample variation of the operating point.

    dci1/.venv/bin/python tools/v8_prescreen_revalidation.py --all

Writes ``prescreen_revalidation_tables.md`` and ``revalidation.json`` under
``reports/dci1v8dev/frame_aware_prescreen/``.
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib
import statistics
import sys
from typing import Any, Mapping, Sequence

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))

from dci1v4.engine import fs                                       # noqa: E402
from dci1v4.engine.signing import verify_signed                    # noqa: E402
from dci1v4.errors import IntegrityError                           # noqa: E402
from dci1v7.protocol import constants as C                         # noqa: E402
from dci1v8dev import rules as R                                   # noqa: E402
from dci1v8dev.run import EVIDENCE_DIRNAME                         # noqa: E402
from dci1v8dev.run import eligibility as EL                        # noqa: E402
from dci1v8dev.run import stages as PS                             # noqa: E402

DCI1 = HERE.parent
OUT = DCI1 / "reports" / "dci1v8dev" / "frame_aware_prescreen"
PROTECTED = ("CONFIRMATORY_GENERATION", "CONFIRMATORY_ANALYSIS", "FINAL_REPORT")

OLD_ROOTS: dict[str, str] = {
    "qwen3-4b": "dci1v8-pilot-r9",
    "qwen3-4b-instruct-2507": "dci1v8-pilot-r10",
    "gemma-3n-e2b-it": "dci1v8-pilot-r12",
    "gemma-3n-e4b-it": "dci1v8-pilot-r13",
}
NEW_ROOTS: dict[str, str] = {
    "qwen3-4b": "dci1v8-pilot-r14",
    "qwen3-4b-instruct-2507": "dci1v8-pilot-r15",
    "gemma-3n-e2b-it": "dci1v8-pilot-r16",
    "gemma-3n-e4b-it": "dci1v8-pilot-r23",  # r17 invalidated (unanswered rows scored), r18 abandoned (12 h backend cap); r23 at 7d8e1d9 (cap raised) — prescreen_revalidation.md §2
}
# A second successor run of the same model on the same commit: a test-retest of
# the frame-aware forwarding and a third grid sample for the operating point.
# Rendered as an extra block whose "old" column is the FIRST successor run.
REPLICATE_ROOTS: dict[str, tuple[str, ...]] = {
    "gemma-3n-e2b-it": ("dci1v8-pilot-r19",),
    "qwen3-4b-instruct-2507": ("dci1v8-pilot-r20", "dci1v8-pilot-r25"),
    "qwen3-4b": ("dci1v8-pilot-r21",),
    "gemma-3n-e4b-it": ("dci1v8-pilot-r24",),  # at 7d8e1d9, paired with r23
}
# A re-execution of the v8 (pooled) design itself at the frozen commit: the
# control for the rule-attributed frames — does the pooled design's own
# verdict survive decoding noise? Rendered as a block whose "old" column is
# the v8 root and whose "new" column is the v8 re-execution.
OLD_REPLICATE_ROOTS: dict[str, tuple[str, ...]] = {
    "qwen3-4b-instruct-2507": ("dci1v8-pilot-r26",),  # at f7af7f2
}
# The topic-resampled methodology-validation replicates (2026-09-07,
# docs/V8_TOPIC_RESAMPLED_VALIDATION.md): the pilot lifecycle in the
# ``topic-replicate`` namespace on a re-partitioned pre-freeze topic pool.
# Rendered as a block whose "old" column is the first successor run.
TOPIC_REPLICATE_ROOTS: dict[str, str] = {
    "qwen3-4b": "dci1v8-pilot-t1-qwen3-4b",
    "qwen3-4b-instruct-2507": "dci1v8-pilot-t1-qwen3-4b-instruct-2507",
    "gemma-3n-e2b-it": "dci1v8-pilot-t1-gemma-3n-e2b-it",
    "gemma-3n-e4b-it": "dci1v8-pilot-t1-gemma-3n-e4b-it",
}
STAGES = (PS.STAGE_REGIME, PS.STAGE_SECOND_PASS, PS.STAGE_GATE2, PS.STAGE_GATE3,
          PS.STAGE_REPORT)


def _unprotected(path: pathlib.Path) -> pathlib.Path:
    if any(p in path.parts for p in PROTECTED):
        raise SystemExit(f"refusing a protected path: {path}")
    return path


def records(root: pathlib.Path, model_key: str) -> dict[str, Any]:
    """Every signed pilot record the root holds for the model, verified."""
    base = root / "evidence" / EVIDENCE_DIRNAME
    key = base / "keys" / "signing.key"
    out: dict[str, Any] = {"root": root.name, "exists": root.exists(), "stages": {}}
    if not root.exists() or not key.exists():
        return out
    for stage in STAGES:
        path = _unprotected(base / model_key / stage / "records"
                            / PS.STAGE_RECORD_FILES[stage])
        if path.exists():
            record = fs.read_json(path)
            out["stages"][stage] = verify_signed(record, key, where=f"{model_key}:{stage}")
            out.setdefault("hashes", {})[stage] = record["record_hash"]
    terminal = base / model_key / "terminal_report.json"
    if terminal.exists():
        out["terminal"] = fs.read_json(terminal).get("payload", {}).get("status")
    out["reached"] = max((s for s in STAGES if s in out["stages"]),
                         key=lambda s: STAGES.index(s), default=None)
    return out


def _se_iota_a(g2f: Mapping[str, Any]) -> float | None:
    per_topic: list[float] = []
    for vec in (g2f.get("a_per_topic_by_split") or {}).get("per_topic", {}).values():
        per_topic += [float(v) for v in vec]
    kappa = g2f.get("kappa_a")
    if len(per_topic) > 1 and kappa is not None and kappa < C.CHANCE_DEGENERACY_MAX:
        return statistics.stdev(per_topic) / math.sqrt(len(per_topic)) / (1.0 - kappa)
    return None


def frame_row(recs: Mapping[str, Any], frame: int) -> dict[str, Any]:
    g2 = (recs["stages"].get(PS.STAGE_GATE2) or {})
    g3 = (recs["stages"].get(PS.STAGE_GATE3) or {})
    row: dict[str, Any] = {"frame": frame, "gate2": None, "gate3": None}
    if g2:
        f2 = g2["by_frame"][str(frame)]
        supported = f2.get("status") == PS.FRAME_SUPPORTED
        row["gate2"] = {
            "supported": supported,
            "unsupported_reason": ((f2.get("unsupported_reason") or {}).get("status")
                                   if not supported else None),
            "n_star": f2.get("n_star"), "m_star": f2.get("m_star"),
            "iota_a": f2.get("iota_a"), "se_iota_a": _se_iota_a(f2) if supported else None,
            "n_tabled": len((f2.get("calibration_rows") or {}).get("pooled", [])) if supported else 0,
            "n_withheld": len((f2.get("calibration_rows_withheld") or {}).get("pooled", [])) if supported else 0,
            "forwarded": ((f2.get("forwarding") or {}).get("forwarded")
                          if supported else None),
            "comparator_extra": ((f2.get("comparator") or {}).get("extra_labels")
                                 if supported else None),
            "comparator_sets": ((f2.get("comparator") or {}).get("policies")
                                if supported else None),
            "extension_measured": f2.get("extension_measured") if supported else None,
        }
        pop = g2.get("calibration_population") or {}
        row["gate2"]["policy"] = pop.get("policy", "legacy_pooled_design")
        if row["gate2"]["forwarded"] is None and supported:
            row["gate2"]["forwarded"] = list(pop.get("forwarded") or ())
        prov = (pop.get("provisional_agreement") or {}).get(str(frame))
        row["gate2"]["provisional_agreement"] = prov
    if g3:
        f3 = g3["by_frame"][str(frame)]
        s = f3.get("survival")
        row["gate3"] = {
            "state": f3.get("state"),
            "n_local_valid": f3.get("n_local_valid"),
            "n_spectrum_valid": f3.get("n_spectrum_valid"),
            "n_local_valid_families": s["n_local_valid_families"] if s else None,
            "local_valid_families": s["local_valid_families"] if s else None,
            "n_backups": s["n_backups"] if s else None,
            "core_identified": s["core_identified"] if s else None,
            "core_references": [f"{c['family']}:{c['severity']}" for c in s["core_references"]] if s else None,
            "coverage_identified": s["coverage_identified"] if s else None,
            "local_supported": (bool(EL.local_support(s, frame=frame)["local_supported"])
                                if s else False),
        }
        rc = ((g3.get("retention_comparison") or {}).get("by_frame") or {}).get(str(frame))
        if rc and rc.get("available"):
            row["gate3"]["comparators"] = {
                policy: ({"state": v.get("state"),
                          "n_local_valid_families": v.get("n_local_valid_families"),
                          "n_backups": v.get("n_backups"),
                          "coverage_identified": v.get("coverage_identified"),
                          "local_supported": v.get("local_supported"),
                          "n_rungs": v.get("n_rungs"),
                          "n_shared_with_frame_set": v.get("n_shared_with_frame_set"),
                          "n_only_comparator": v.get("n_only_comparator"),
                          "n_only_frame_set": v.get("n_only_frame_set")}
                         if v.get("available") else {"available": False})
                for policy, v in rc["by_policy"].items()}
    return row


def _forwarded(recs: Mapping[str, Any], frame: int) -> set[str] | None:
    g2 = recs["stages"].get(PS.STAGE_GATE2) or {}
    cp = (g2.get("calibration_population") or {}).get("by_frame") or {}
    b = cp.get(str(frame))
    return set(b.get("forwarded") or []) if b else None


def _references(recs: Mapping[str, Any], frame: int) -> dict[str, Any] | None:
    g3 = recs["stages"].get(PS.STAGE_GATE3) or {}
    b = (g3.get("by_frame") or {}).get(str(frame))
    if not b or b.get("status") != PS.FRAME_SUPPORTED:
        return None
    sv = b.get("survival") or {}
    core = [f"{e['family']}:{e['severity']}" for e in (sv.get("core_references") or [])]
    backups = [str(x) if not isinstance(x, dict) else f"{x.get('family')}:{x.get('severity')}"
               for x in (sv.get("backups") or [])]
    return {"core": core, "backups": backups}


def frame_overlap(old: Mapping[str, Any], new: Mapping[str, Any], frame: int
                  ) -> dict[str, Any]:
    """Forwarded-set Jaccard and reference identity between two roots on one
    frame: what a re-execution or a topic replicate keeps and what moves."""
    a, b = _forwarded(old, frame), _forwarded(new, frame)
    out: dict[str, Any] = {"jaccard": None, "n_shared": None, "n_old": None, "n_new": None}
    if a is not None and b is not None:
        out.update({"jaccard": (len(a & b) / len(a | b)) if (a | b) else None,
                    "n_shared": len(a & b), "n_old": len(a), "n_new": len(b)})
    ra, rb = _references(old, frame), _references(new, frame)
    out["references"] = {"old": ra, "new": rb,
                         "core_identical": (ra["core"] == rb["core"]) if ra and rb else None,
                         "core_shared": (len(set(ra["core"]) & set(rb["core"]))) if ra and rb else None,
                         "backups_identical": (ra["backups"] == rb["backups"]) if ra and rb else None,
                         "backups_shared": (len(set(ra["backups"]) & set(rb["backups"]))) if ra and rb else None}
    return out


def model_block(model_key: str, old: Mapping[str, Any], new: Mapping[str, Any]
                ) -> dict[str, Any]:
    out: dict[str, Any] = {"model_key": model_key,
                           "old": {"root": old["root"], "reached": old.get("reached"),
                                   "terminal": old.get("terminal")},
                           "new": {"root": new["root"], "reached": new.get("reached"),
                                   "terminal": new.get("terminal"),
                                   "exists": new.get("exists")},
                           "by_frame": {}}
    for f in PS.FRAMES:
        out["by_frame"][str(f)] = {"old": frame_row(old, f), "new": frame_row(new, f)}
        out["by_frame"][str(f)]["overlap"] = frame_overlap(old, new, f)
    for which, recs in (("old", old), ("new", new)):
        g3 = recs["stages"].get(PS.STAGE_GATE3)
        if g3:
            elig = EL.local_eligibility(g3["by_frame"], frames=PS.FRAMES)
            out[which]["local_supported_frames"] = elig["local_supported_frames"]
            out[which]["local_eligible"] = elig["local_eligible"]
            out[which]["spectrum_frames"] = [
                int(w) for w in g3["supported_frames"]
                if g3["by_frame"][str(w)]["survival"]["coverage_identified"]]
            rc = g3.get("retention_comparison") or {}
            out[which]["comparator_eligibility"] = {
                p: {"supported": v["local_supported_frames"], "eligible": v["local_eligible"]}
                for p, v in (rc.get("comparator_eligibility") or {}).items()}
        rg = recs["stages"].get(PS.STAGE_REGIME)
        if rg:
            out[which]["screen_allocation"] = rg.get("screen_allocation") or {
                "passes": 1, "topics_per_frame": C.N_PRESCREEN // C.N_WORDINGS}
            out[which]["selected_cap"] = rg.get("selected_cap")
        rp = recs["stages"].get(PS.STAGE_REPORT)
        if rp:
            out[which]["generations"] = rp.get("generations")
            out[which]["pilot_status"] = rp.get("pilot_status")
            out[which]["frames_meeting_all_decided_criteria"] = rp.get(
                "frames_meeting_all_decided_criteria")
        sp = recs["stages"].get(PS.STAGE_SECOND_PASS)
        if sp:
            out[which]["n_batches"] = sp.get("n_batches")
            out[which]["provisional_union"] = len(sp.get("forwarded_set_provisional")
                                                  or sp.get("forwarded_set") or ())
    return out


# ------------------------------------------------------------- rendering
def _f(v: Any, nd: int = 3) -> str:
    if v is None:
        return "—"
    if isinstance(v, bool):
        return "yes" if v else "no"
    if isinstance(v, float):
        return f"{v:.{nd}f}"
    return str(v)


def _lsc(g3: Mapping[str, Any] | None) -> str:
    if not g3:
        return "—"
    return (f"{_f(g3['n_local_valid_families'])}/{_f(g3['n_backups'])}/"
            f"{'C' if g3['coverage_identified'] else 'c'}/"
            f"{'L' if g3['local_supported'] else 'l'}")


def render_overlap(models: Sequence[Mapping[str, Any]]) -> str:
    lines = ["", "## Forwarded-set overlap and reference identity, per frame (old → new of each block)", "",
             "| block | f | forwarded Jaccard (shared/old/new) | core references old → new | core identical | backups old → new | backups identical |",
             "|---|---:|---|---|---|---|---|"]
    for m in models:
        for f, b in sorted(m["by_frame"].items()):
            o = b.get("overlap") or {}
            r = o.get("references") or {}
            ra, rb = r.get("old"), r.get("new")
            if o.get("jaccard") is None and not (ra and rb):
                continue
            jac = (f"{o['jaccard']:.2f} ({o['n_shared']}/{o['n_old']}/{o['n_new']})"
                   if o.get("jaccard") is not None else "—")
            core = (f"{', '.join(ra['core'])} → {', '.join(rb['core'])}" if ra and rb else "—")
            bk = (f"{', '.join(ra['backups'])} → {', '.join(rb['backups'])}" if ra and rb else "—")
            lines.append(f"| `{m['model_key']}` | {f} | {jac} | {core} | "
                         f"{'yes' if r.get('core_identical') else ('no' if r.get('core_identical') is False else '—')} | {bk} | "
                         f"{'yes' if r.get('backups_identical') else ('no' if r.get('backups_identical') is False else '—')} |")
    return "\n".join(lines) + "\n"


def render(models: Sequence[Mapping[str, Any]]) -> str:
    L: list[str] = []
    A = L.append
    A("# DCI-1 v8 → v8.1 — old versus successor pilots, per model × frame (tables)")
    A("")
    A("> Generated by `dci1/tools/v8_prescreen_revalidation.py` from the signed "
      "pilot records of the v8 roots (r9/r10/r12/r13) and the v8.1 successor "
      "roots (r14, r15, r16, r23; r17 invalidated and r18 abandoned, see prescreen_revalidation.md §2). Read-only; no protected stage opened. A successor root "
      "that has not reached a stage is shown as pending.")
    A("")
    A("## Roots and progress")
    A("")
    A("| model | old root | old reached | new root | new reached | terminal | screen passes (old → new) | topics/frame (old → new) |")
    A("|---|---|---|---|---|---|---|---|")
    for m in models:
        o, n = m["old"], m["new"]
        A(f"| `{m['model_key']}` | `{o['root']}` | {o.get('reached')} | `{n['root']}` | "
          f"{n.get('reached') or 'pending'} | {n.get('terminal') or '—'} | "
          f"{(o.get('screen_allocation') or {}).get('passes', '—')} → "
          f"{(n.get('screen_allocation') or {}).get('passes', '—')} | "
          f"{(o.get('screen_allocation') or {}).get('topics_per_frame', '—')} → "
          f"{(n.get('screen_allocation') or {}).get('topics_per_frame', '—')} |")
    A("")
    A("## Operating points and forwarding, per frame")
    A("")
    A("| model | f | old Gate-2 | old n\\*/m\\* | old ι_A(f) ± SE | new Gate-2 | new n\\*/m\\* | new ι_A(f) ± SE | old forwarded (pooled) | new forwarded (frame) | new comparator extra | provisional ∩ final (Jaccard) |")
    A("|---|---:|---|---|---|---|---|---|---:|---:|---:|---:|")
    for m in models:
        for f, b in sorted(m["by_frame"].items()):
            o, n = b["old"]["gate2"], b["new"]["gate2"]
            def g(x, k):
                return (x or {}).get(k)
            def pt(x):
                return "—" if not x else ("SUPPORTED" if x["supported"] else f"UNSUPPORTED ({x['unsupported_reason']})")
            prov = (n or {}).get("provisional_agreement") or {}
            A(f"| `{m['model_key']}` | {f} | {pt(o)} | {_f(g(o,'n_star'))}/{_f(g(o,'m_star'))} | "
              f"{_f(g(o,'iota_a'))} ± {_f(g(o,'se_iota_a'))} | {pt(n) if n else 'pending'} | "
              f"{_f(g(n,'n_star'))}/{_f(g(n,'m_star'))} | {_f(g(n,'iota_a'))} ± {_f(g(n,'se_iota_a'))} | "
              f"{len(g(o,'forwarded') or []) if o and o['supported'] else '—'} | "
              f"{len(g(n,'forwarded') or []) if n and n['supported'] else '—'} | "
              f"{len(g(n,'comparator_extra') or []) if n and n['supported'] else '—'} | "
              f"{_f(prov.get('jaccard'), 2)} |")
    A("")
    A("## Identification, per frame: the frame's own set beside every policy on the same rows")
    A("")
    A("fam/bk/C|c/L|l = LOCAL-valid families / admissible backups / coverage "
      "identified or not / `LOCAL_SUPPORTED` or not. The comparator columns "
      "re-verdict the legacy pooled set and the provisional screen-proxy set "
      "on the successor run's own calibration rows (`retention_comparison`).")
    A("")
    A("| model | f | old (pooled run) | old LOCAL/SPECTRUM valid | new: frame set | new LOCAL/SPECTRUM valid | new: legacy set on new rows | new: proxy set on new rows | state old → new |")
    A("|---|---:|---|---|---|---|---|---|---|")
    for m in models:
        for f, b in sorted(m["by_frame"].items()):
            o, n = b["old"]["gate3"], b["new"]["gate3"]
            cmp = (n or {}).get("comparators") or {}
            A(f"| `{m['model_key']}` | {f} | {_lsc(o)} | "
              f"{_f((o or {}).get('n_local_valid'))}/{_f((o or {}).get('n_spectrum_valid'))} | "
              f"{_lsc(n) if n else 'pending'} | "
              f"{_f((n or {}).get('n_local_valid'))}/{_f((n or {}).get('n_spectrum_valid'))} | "
              f"{_lsc(cmp.get('legacy_pooled')) if cmp.get('legacy_pooled', {}).get('n_rungs') else '—'} | "
              f"{_lsc(cmp.get('frame_aware_screen_proxy')) if cmp.get('frame_aware_screen_proxy', {}).get('n_rungs') else '—'} | "
              f"{(o or {}).get('state', '—')} → {(n or {}).get('state', 'pending')} |")
    A("")
    A("## Model eligibility and generation")
    A("")
    A("| model | old LOCAL frames | old eligible | old SPECTRUM frames | new LOCAL frames | new eligible | new SPECTRUM frames | legacy set on new rows: LOCAL frames / eligible | proxy set on new rows: LOCAL frames / eligible | old generations | new generations |")
    A("|---|---|---|---|---|---|---|---|---|---:|---:|")
    for m in models:
        o, n = m["old"], m["new"]
        ce = n.get("comparator_eligibility") or {}
        A(f"| `{m['model_key']}` | {o.get('local_supported_frames', '—')} | {_f(o.get('local_eligible'))} | "
          f"{o.get('spectrum_frames', '—')} | {n.get('local_supported_frames', 'pending')} | "
          f"{_f(n.get('local_eligible'))} | {n.get('spectrum_frames', '—')} | "
          f"{(ce.get('legacy_pooled') or {}).get('supported', '—')} / {_f((ce.get('legacy_pooled') or {}).get('eligible'))} | "
          f"{(ce.get('frame_aware_screen_proxy') or {}).get('supported', '—')} / {_f((ce.get('frame_aware_screen_proxy') or {}).get('eligible'))} | "
          f"{(o.get('generations') or {}).get('total', '—')} | {(n.get('generations') or {}).get('total', '—')} |")
    A("")
    return "\n".join(L) + render_overlap(models)


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--model")
    ap.add_argument("--out", type=pathlib.Path, default=OUT)
    args = ap.parse_args(argv)
    keys = list(OLD_ROOTS) if args.all or not args.model else [args.model]
    models = []
    for key in keys:
        old = records(DCI1 / "evidence" / OLD_ROOTS[key], key)
        new = records(DCI1 / "evidence" / NEW_ROOTS[key], key)
        models.append(model_block(key, old, new))
        print(f"{key}: old reached {old.get('reached')}; new reached "
              f"{new.get('reached') or 'pending'}{' TERMINAL ' + new['terminal'] if new.get('terminal') else ''}")
    for key, reps in REPLICATE_ROOTS.items():
        if key not in keys:
            continue
        first = records(DCI1 / "evidence" / NEW_ROOTS[key], key)
        for rep in reps:
            again = records(DCI1 / "evidence" / rep, key)
            models.append(model_block(
                f"{key} · replicate ({NEW_ROOTS[key]} → {rep}; 'old' = first successor run)",
                first, again))
            print(f"{key} replicate {rep}: first reached {first.get('reached')}; again reached "
                  f"{again.get('reached') or 'pending'}")
    for key, rep in TOPIC_REPLICATE_ROOTS.items():
        if key not in keys:
            continue
        first = records(DCI1 / "evidence" / NEW_ROOTS[key], key)
        again = records(DCI1 / "evidence" / rep, key)
        models.append(model_block(
            f"{key} · topic-resampled replicate ({NEW_ROOTS[key]} → {rep}; 'old' = first successor run)",
            first, again))
        print(f"{key} topic replicate {rep}: first reached {first.get('reached')}; again reached "
              f"{again.get('reached') or 'pending'}")
    for key, reps in OLD_REPLICATE_ROOTS.items():
        if key not in keys:
            continue
        old_first = records(DCI1 / "evidence" / OLD_ROOTS[key], key)
        for rep in reps:
            again = records(DCI1 / "evidence" / rep, key)
            models.append(model_block(
                f"{key} · v8-design re-execution ({OLD_ROOTS[key]} → {rep}; both pooled)",
                old_first, again))
            print(f"{key} v8 re-execution {rep}: v8 reached {old_first.get('reached')}; again reached "
                  f"{again.get('reached') or 'pending'}")
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "revalidation.json").write_text(
        json.dumps({"models": models, "old_roots": OLD_ROOTS, "new_roots": NEW_ROOTS,
                    "replicate_roots": REPLICATE_ROOTS,
                    "old_replicate_roots": OLD_REPLICATE_ROOTS,
                    "topic_replicate_roots": TOPIC_REPLICATE_ROOTS,
                    "rules": {"screen_frame_offsets": list(R.SCREEN_FRAME_OFFSETS),
                              "retention_policy": R.RETENTION_POLICY,
                              "retention_target_basis": R.RETENTION_TARGET_BASIS,
                              "retention_comparator": R.RETENTION_COMPARATOR}},
                   indent=1, sort_keys=True, default=str) + "\n")
    (args.out / "prescreen_revalidation_tables.md").write_text(render(models))
    print(f"wrote {args.out / 'prescreen_revalidation_tables.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
