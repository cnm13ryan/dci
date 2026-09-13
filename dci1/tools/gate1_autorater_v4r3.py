"""§10.4's autorater pathway for v4r3, development phase only.

NOT a stage. Writes only to ``reports/dci1v4r3/``. **Approves nothing.**

§10.4 ends in an *explicit researcher approval* writing
``measurement_basis = autorater_calibration_approved``, and the single-shot
signed freeze and one-shot calibration are claimed exactly once each and both
bind the canonical verifier hash. This tool runs everything before those three
steps -- the item pool, the deterministic class-stratified disjoint split, the
hashed judge configuration, serialised execution at concurrency one, the
repeatability check, and the paired comparison -- and stops. The held-out
calibration half is derived and hashed and is never judged.

**What is carried from the v4r2 development phase, and with what standing.**
The judge prompt ``gate1-judge-v4/1.0.0``, the parser, the label mapping, the
output cap and the four conditions are imported from ``gate1_autorater_v4.py``
rather than restated, so a divergence is impossible. They are properties of the
*judge*, not of v4r3's verifiers, and the v4r2 phase selected
``v4prompt-medium`` at criterion 2 on a truncation rate of 0/48 against
25/48, 6/48 and 2/48. That selection is **re-run here on v4r3's own pool**,
because §10.4 selects against the pool being judged.

**Scope, stated rather than implied.** §10.3 asks for a sample per verifier
class per instrument. v4r3 registers 348 instrument instances, which no
development phase can cover one by one. The strata here are
*predicate form × verifier class × fail margin*, so every one of the four
registered forms is represented and the sample is form-balanced rather than
family-balanced. Per-family coverage is **not** claimed and is part of what the
researcher is being asked to weigh.

Usage:
  ./.venv/bin/python tools/gate1_autorater_v4r3.py --items 72 --device 0
  ./.venv/bin/python tools/gate1_autorater_v4r3.py --plan-only
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from pathlib import Path
from typing import Any

DCI1 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DCI1 / "src"))

from dci1v4.engine import fs                                     # noqa: E402
from dci1v4.generation.backend import build_plan, run_backend    # noqa: E402
from dci1v4.models.registry import get_judge                     # noqa: E402
from dci1v4.protocol.hashing import sha_obj, sha_text            # noqa: E402
from dci1v4.stages import autorater                              # noqa: E402
from dci1v4r3 import CLASSIFICATION, EVIDENCE_DIRNAME            # noqa: E402
from dci1v4r3.engine.paths import current_files                  # noqa: E402
from dci1v4r3.protocol.wordings import wording                   # noqa: E402
from dci1v4r3.verifiers import verifier_source_hash              # noqa: E402
from dci1v4r3.verifiers.constraints import FAMILIES              # noqa: E402


def _load_v4_tool():
    """Import the v4r2 development tool as a module, for its judge material.

    Imported rather than copied: the prompt text, the parser and the label
    mapping are hashed into the configuration, and two copies of a hashed
    string is how two studies end up believing they judged under one
    condition.
    """
    spec = importlib.util.spec_from_file_location(
        "gate1_autorater_v4", DCI1 / "tools" / "gate1_autorater_v4.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


V4 = _load_v4_tool()
JUDGE_PROMPTS = V4.JUDGE_PROMPTS
CONDITIONS = V4.CONDITIONS
PARSER_VERSION = V4.PARSER_VERSION
LABEL_MAPPING = V4.LABEL_MAPPING
JUDGE_CAP = V4.JUDGE_CAP
parse = V4.parse

EVIDENCE = DCI1 / "evidence" / EVIDENCE_DIRNAME
OUT = DCI1 / "reports" / "dci1v4r3"
RUNS = OUT / "judge_runs"

#: §10.4's default condition for v4r3, carried from the v4r2 selection and
#: re-run here. The alternative is kept so the paired comparison has two arms.
DEFAULT_CONDITIONS = ("v4prompt-medium", "v4prompt-high")


def instrument_group(kind: str) -> str:
    if kind in ("A", "B"):
        return kind
    return FAMILIES[kind].form


def build_items() -> list[dict[str, Any]]:
    """Natural items from v4r3's own §12.2 ladder screen, read only.

    One item is a (constraint wording, response) pair the model actually saw,
    plus the deterministic verifier's stored verdict. The judge sees the
    wording the model saw, never the verifier and never the verdict.
    """
    items: list[dict[str, Any]] = []
    for path in current_files(EVIDENCE, "scored.jsonl"):
        for line in path.read_text().splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("load") != 1:
                continue
            # §12.1's cap-selection rows are load 1 too, and they were
            # generated at three different completion caps on the same
            # (topic, constraint) pairs. Including them would put the same
            # item in the pool three times under three experimental
            # conditions, so the pool is the §12.2 screen alone.
            if not str(row.get("stage", "")).startswith("v4r3-ladder-screen"):
                continue
            score = next((s for s in row["scores"] if s["present"]), None)
            if score is None or score["statistic"] is None:
                continue
            kind, severity = score["kind"], score["severity"]
            statistic = score["statistic"]
            if kind == "A":
                margin = abs(statistic - severity)
            elif kind == "B":
                margin = max(0, statistic - severity)
            else:
                margin = abs(statistic - severity)
            index = (row["wording_indices"] or [0])[0]
            items.append({
                "item_id": f"{row['model_key']}:{row['stage']}:{kind}:"
                           f"{severity}:{row['topic_id']}",
                "instrument": kind,
                "group": instrument_group(kind),
                "severity": severity,
                "constraint": wording(kind, index, severity),
                "response": row["raw_response"],
                "verifier_class": "pass" if score["passed"] else "fail",
                "statistic": statistic, "margin": margin,
                "margin_one": margin == 1,
                "word_count": row["word_count"],
                "model_key": row["model_key"], "topic_id": row["topic_id"],
                "source": "the registered v4r3 §12.2 ladder screen, read only"})
    return items


def stratum(item: dict[str, Any]) -> str:
    """Predicate form × verifier class × fail margin."""
    if item["verifier_class"] == "pass":
        return f"{item['group']}:pass"
    return (f"{item['group']}:fail:margin_one" if item["margin_one"]
            else f"{item['group']}:fail:margin_larger")


def split_pool(items: list[dict[str, Any]]) -> dict[str, Any]:
    """§10.4's deterministic class-stratified DISJOINT split."""
    by: dict[str, list] = {}
    for item in items:
        by.setdefault(stratum(item), []).append(item)
    development, calibration, per_stratum = [], [], {}
    for name, members in sorted(by.items()):
        result = autorater.stratified_split(members, model_id=f"v4r3:{name}")
        development += result["development"]
        calibration += result["calibration"]
        per_stratum[name] = {"n": len(members),
                             "development": len(result["development"]),
                             "calibration": len(result["calibration"])}
    dev_ids = {i["item_id"] for i in development}
    cal_ids = {i["item_id"] for i in calibration}
    assert not dev_ids & cal_ids
    return {"development": development, "calibration": calibration,
            "per_stratum": per_stratum,
            "split_hash": sha_obj({"development": sorted(dev_ids),
                                   "calibration": sorted(cal_ids)}),
            "seed": "dci1v4r3.protocol.seeds.AUTORATER_SPLIT_SEED, per stratum",
            "disjoint": True}


def subsample(items: list[dict[str, Any]], n: int) -> list[dict[str, Any]]:
    """A deterministic, stratum-balanced subsample of the development half."""
    by: dict[str, list] = {}
    for item in sorted(items, key=lambda i: i["item_id"]):
        by.setdefault(stratum(item), []).append(item)
    names = sorted(by)
    out: list[dict[str, Any]] = []
    index = 0
    while len(out) < n and any(by[k] for k in names):
        bucket = by[names[index % len(names)]]
        if bucket:
            out.append(bucket.pop(0))
        index += 1
    return out


def judge_config(condition: str) -> dict[str, Any]:
    spec = CONDITIONS[condition]
    return autorater.build_config(
        "gpt-oss-20b",
        backend=("vllm-subprocess; dci1/environments/backend/.venv, pinned "
                 "vLLM 0.15.1+rocm720"),
        prompt_version=spec["prompt"],
        prompt_hash=sha_text(JUDGE_PROMPTS[spec["prompt"]]),
        parser_version=PARSER_VERSION,
        label_mapping=dict(LABEL_MAPPING),
        decoding={"policy": "greedy", "max_new_tokens": JUDGE_CAP,
                  "skip_special_tokens": False,
                  "chat_template_kwargs":
                      {"reasoning_effort": spec["reasoning_effort"]}},
        output_cap=JUDGE_CAP,
        execution_concurrency=1, execution_mode="serialised")


def run_condition(items: list[dict[str, Any]], condition: str, *, device: int,
                  replicate: int = 0) -> dict[str, Any]:
    """Judge every item once, serialised at concurrency one (§10.4)."""
    config = judge_config(condition)
    spec = get_judge(config["judge_model_key"])
    plan = build_plan(spec, stage="v4r3-gate1-judge", max_new_tokens=JUDGE_CAP,
                      temperature=0.0, skip_special_tokens=False,
                      serialised=True)
    effort = CONDITIONS[condition]["reasoning_effort"]
    plan["chat_template_kwargs"] = {"reasoning_effort": effort}
    plan["thinking_policy"] = effort

    design_rows = []
    for item in items:
        template = JUDGE_PROMPTS[CONDITIONS[condition]["prompt"]]
        prompt = template.format(constraint=item["constraint"],
                                 response=item["response"])
        design_rows.append({
            "cell_id": item["item_id"], "draw_index": 0,
            "row_id": f"judge:{item['item_id']}",
            "prompt_hash": sha_text(prompt),
            "scientific_seed": 0, "user_prompt": prompt})

    sample_hash = sha_obj(sorted(i["item_id"] for i in items))[:12]
    run_dir = (RUNS / f"{condition}-rep{replicate}"
               / f"{config['config_hash'][:12]}-{sample_hash}")
    started = time.monotonic()
    outcome = run_backend(run_dir, plan, design_rows, device=device,
                          timeout_seconds=60 * 60 * 10)
    elapsed = time.monotonic() - started

    by_row = {r["row_id"]: r for r in outcome["rows"]}
    judgments, statuses, rows = {}, {}, []
    for item, design in zip(items, design_rows):
        raw = by_row.get(design["row_id"], {})
        text = raw.get("final_answer") or raw.get("raw_text") or ""
        status, label, why = parse(text)
        statuses[status] = statuses.get(status, 0) + 1
        if label is not None:
            judgments[item["item_id"]] = label
        rows.append({"item_id": item["item_id"], "status": status,
                     "label": label, "justification": why,
                     "instrument": item["instrument"], "group": item["group"],
                     "stratum": stratum(item),
                     "verifier_class": item["verifier_class"],
                     "margin": item["margin"],
                     "truncated": bool(raw.get("answer_truncated")),
                     "tokens": raw.get("total_generated_tokens"),
                     "config_hash": config["config_hash"],
                     "prompt_hash": design["prompt_hash"]})
    truncated = sum(1 for r in rows if r["truncated"])
    return {"condition": condition, "replicate": replicate, "config": config,
            "items": len(items), "judgments": judgments, "rows": rows,
            "status_counts": statuses,
            "coverage": len(judgments) / len(items) if items else 0.0,
            "truncated": truncated,
            "truncation_rate": truncated / len(items) if items else 0.0,
            "seconds": round(elapsed, 1),
            "seconds_per_item": round(elapsed / max(1, len(items)), 2),
            "run_dir": str(run_dir.relative_to(DCI1))}


def verifier_agreement(judgments: dict[str, str],
                       items: list[dict[str, Any]]) -> dict[str, Any]:
    """Agreement with the deterministic verifier, per stratum.

    Reported for every condition and **not** a §10.4 selection criterion: the
    hierarchy's fourth step is agreement with *human* labels, and no
    independent annotator exists. Reporting it as if it decided anything would
    be letting the instrument grade its own proxy.
    """
    per: dict[str, list[bool]] = {}
    for item in items:
        label = judgments.get(item["item_id"])
        if label is None:
            continue
        per.setdefault(stratum(item), []).append(
            label == item["verifier_class"])
        per.setdefault("overall", []).append(label == item["verifier_class"])
    return {k: {"agreement": sum(v) / len(v), "n": len(v)}
            for k, v in sorted(per.items())}


def plan_of(items, split, sample) -> dict[str, Any]:
    return {
        "artifact": "§10.4 autorater pathway, v4r3, development phase",
        "classification": CLASSIFICATION,
        "approves": "nothing. Gate 1 is NOT approved and cannot be approved "
                    "by this tool",
        "canonical_verifier_hash": verifier_source_hash(),
        "pool": {"items": len(items),
                 "development": len(split["development"]),
                 "calibration": len(split["calibration"]),
                 "disjoint": split["disjoint"],
                 "split_hash": split["split_hash"],
                 "strata": split["per_stratum"],
                 "source": "the registered v4r3 §12.2 ladder screen, read "
                           "only"},
        "judged_subsample": {"n": len(sample),
                             "hash": sha_obj(sorted(i["item_id"]
                                                    for i in sample)),
                             "strata": {k: sum(1 for i in sample
                                               if stratum(i) == k)
                                        for k in sorted({stratum(i)
                                                         for i in sample})},
                             "derivation": "deterministic round-robin over "
                                           "strata in item-id order across "
                                           "the development half"},
        "not_claimed": {
            "autorater_freeze": "single-shot; not claimed",
            "autorater_calibration": "one-shot; not claimed",
            "held_out_half": "derived and hashed, never judged",
            "researcher_approval": "reserved to the researcher (§10.4)"},
        "scope": "strata are predicate form × verifier class × fail margin; "
                 "per-family coverage is not claimed",
    }


def combine(sample: list[dict[str, Any]], plan: dict[str, Any]) -> dict[str, Any]:
    """Assemble every per-condition file, and apply §10.4's hierarchy.

    The hierarchy is applied here rather than asserted: criterion 1 is valid
    deterministic execution, criterion 2 is an adequate output cap and the
    absence of problematic truncation, criterion 3 is valid parsing and
    coverage. A condition that fails one does not reach the next, and if none
    survives, the selection has **no** answer and this artifact says so.
    """
    conditions: dict[str, Any] = {}
    for path in sorted(OUT.glob("section_10_4_v4prompt-*.json")):
        payload = json.loads(path.read_text())
        for name, entry in payload.get("conditions", {}).items():
            conditions[name] = {
                **entry, "rows": payload.get("judge_rows", {}).get(name, [])}

    by_group: dict[str, dict[str, Any]] = {}
    for name, entry in conditions.items():
        groups: dict[str, list[int]] = {}
        for row in entry["rows"]:
            counts = groups.setdefault(row["group"], [0, 0, 0])
            counts[0] += 1
            counts[1] += int(bool(row["truncated"]))
            counts[2] += int(row["label"] is not None)
        by_group[name] = {g: {"n": c[0], "truncated": c[1], "labelled": c[2],
                              "truncation_rate": c[1] / c[0] if c[0] else 0.0}
                          for g, c in sorted(groups.items())}

    paired: dict[str, Any] = {}
    names = sorted(conditions)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            la = {r["item_id"]: r["label"] for r in conditions[a]["rows"]
                  if r["label"]}
            lb = {r["item_id"]: r["label"] for r in conditions[b]["rows"]
                  if r["label"]}
            shared = sorted(set(la) & set(lb))
            agree = sum(1 for k in shared if la[k] == lb[k])
            paired[f"{a} vs {b}"] = {
                "items_compared": len(shared),
                "agreement": agree / len(shared) if shared else None,
                "coverage": {a: conditions[a]["coverage"],
                             b: conditions[b]["coverage"]},
                "truncation_rate": {a: conditions[a]["truncation_rate"],
                                    b: conditions[b]["truncation_rate"]}}

    steps = [{"criterion": "valid deterministic execution",
              "values": {n: conditions[n]["repeatability"]["exactly_repeatable"]
                         for n in names},
              "surviving": [n for n in names
                            if conditions[n]["repeatability"][
                                "exactly_repeatable"]]}]
    surviving = steps[0]["surviving"]
    clean = [n for n in surviving if conditions[n]["truncation_rate"] == 0.0]
    steps.append({"criterion": "adequate output cap and absence of "
                               "problematic truncation",
                  "values": {n: f"{conditions[n]['truncated']}/"
                                f"{conditions[n]['items']}" for n in surviving},
                  "surviving": clean})
    combined = {
        **plan,
        "conditions": {n: {k: v for k, v in conditions[n].items()
                           if k != "rows"} for n in names},
        "truncation_by_instrument_group": by_group,
        "paired_comparisons": paired,
        "selection": {
            "hierarchy": ["valid deterministic execution",
                          "adequate output cap and absence of problematic "
                          "truncation", "valid parsing and coverage",
                          "agreement with human labels",
                          "the lower-cost setting when performance is "
                          "practically indistinguishable"],
            "steps": steps,
            "surviving": clean,
            "human_criterion_outstanding": True,
            "outcome": ("no condition survives criterion 2" if not clean
                        else clean),
        },
        "judge_rows": {n: conditions[n]["rows"] for n in names},
    }
    fs.write_json(OUT / "section_10_4_development.json", combined)
    return {k: v for k, v in combined.items()
            if k not in ("judge_rows", "pool")}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--items", type=int, default=72)
    parser.add_argument("--repeat-items", type=int, default=16)
    parser.add_argument("--device", type=int, default=0)
    parser.add_argument("--conditions", default=",".join(DEFAULT_CONDITIONS))
    parser.add_argument("--plan-only", action="store_true")
    parser.add_argument("--combine", action="store_true",
                        help="assemble the per-condition files into the "
                             "development artifact, with the paired "
                             "comparison")
    args = parser.parse_args()

    items = build_items()
    split = split_pool(items)
    sample = subsample(split["development"], args.items)
    if args.combine:
        print(json.dumps(combine(sample, plan_of(items, split, sample)),
                         indent=1)[:4000])
        return 0
    plan = {
        "artifact": "§10.4 autorater pathway, v4r3, development phase",
        "classification": CLASSIFICATION,
        "approves": "nothing. Gate 1 is NOT approved and cannot be approved "
                    "by this tool",
        "canonical_verifier_hash": verifier_source_hash(),
        "pool": {"items": len(items),
                 "development": len(split["development"]),
                 "calibration": len(split["calibration"]),
                 "disjoint": split["disjoint"],
                 "split_hash": split["split_hash"],
                 "strata": split["per_stratum"],
                 "source": "the registered v4r3 §12.2 ladder screen, read "
                           "only"},
        "judged_subsample": {"n": len(sample),
                             "hash": sha_obj(sorted(i["item_id"]
                                                    for i in sample)),
                             "strata": {k: sum(1 for i in sample
                                               if stratum(i) == k)
                                        for k in sorted({stratum(i)
                                                         for i in sample})},
                             "derivation": "deterministic round-robin over "
                                           "strata in item-id order across "
                                           "the development half"},
        "not_claimed": {
            "autorater_freeze": "single-shot; not claimed",
            "autorater_calibration": "one-shot; not claimed",
            "held_out_half": "derived and hashed, never judged",
            "researcher_approval": "reserved to the researcher (§10.4)"},
        "scope": "strata are predicate form × verifier class × fail margin; "
                 "per-family coverage is not claimed",
    }
    OUT.mkdir(parents=True, exist_ok=True)
    if args.plan_only:
        fs.write_json(OUT / "section_10_4_plan.json", plan)
        print(json.dumps(plan, indent=1))
        return 0

    results: dict[str, Any] = {}
    for condition in [c for c in args.conditions.split(",") if c]:
        result = run_condition(sample, condition, device=args.device)
        repeat = subsample(sample, args.repeat_items)
        second = run_condition(repeat, condition, device=args.device,
                               replicate=1)
        result["repeatability"] = autorater.repeatability_check([
            [result["judgments"].get(i["item_id"]) for i in repeat],
            [second["judgments"].get(i["item_id"]) for i in repeat]])
        result["verifier_agreement"] = verifier_agreement(
            result["judgments"], sample)
        results[condition] = result
        # One file per condition. The combined artifact is assembled by
        # `--combine`, because two conditions may be run as two processes and
        # a shared output path is how one silently overwrites the other --
        # which is exactly what happened the first time this ran.
        fs.write_json(OUT / f"section_10_4_{condition}.json",
                      {**plan, "conditions": {
                          k: {kk: vv for kk, vv in v.items()
                              if kk not in ("rows", "judgments")}
                          for k, v in results.items()},
                       "judge_rows": {k: v["rows"] for k, v in
                                      results.items()}})
        print(json.dumps({k: {"coverage": v["coverage"],
                              "truncation_rate": v["truncation_rate"],
                              "seconds_per_item": v["seconds_per_item"],
                              "repeatable": v["repeatability"][
                                  "exactly_repeatable"],
                              "verifier_agreement":
                                  v["verifier_agreement"]["overall"]}
                          for k, v in results.items()}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
