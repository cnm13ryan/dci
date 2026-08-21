"""§10.4-R2: the microcase semantic audit, development and calibration.

Amendment R2, registered in `user-notes/DCI1_preregistration_v4r3.md` §10.4-R2
and changelog C28 **before this tool was run** and before any microcase was
judged. `dci1/DECISIONS_V4R3.md` A7 carries the decision.

What this tool does **not** do: score a generation, produce a compliance rate,
or approve anything. The deterministic verifier remains the study's only
scorer, and `measurement_basis = autorater_calibration_approved` is written by
`run_v4r3.py`, only after both phases pass, and only under the researcher's
recorded authorisation.

Usage::

    gate1_microcase_v4r3.py develop --condition mc-medium --device 2
    gate1_microcase_v4r3.py develop --condition mc-medium --device 2 --replicate 1
    gate1_microcase_v4r3.py freeze --condition mc-medium
    gate1_microcase_v4r3.py calibrate --device 2
    gate1_microcase_v4r3.py cases            # write the frozen case set, no GPU
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

from dci1v4.generation.backend import build_plan                    # noqa: E402
from dci1v4.models.registry import get_judge                        # noqa: E402
from dci1v4.protocol.hashing import sha_obj, sha_text               # noqa: E402
from dci1v4r3 import CLASSIFICATION                                 # noqa: E402
from dci1v4r3.stages.microcase import (                             # noqa: E402
    ARM_CONVENTIONS, ARM_INSTRUCTION, ARM_OF_DEFECT, CONVENTIONS_TEXT,
    DEFECT_KINDS, build_cases, case_set_hash, generator_hash, split_cases,
    stratum_counts,
)
from dci1v4r3.verifiers import verifier_source_hash                 # noqa: E402
from dci1v4r3.verifiers.constraints import FAMILIES                 # noqa: E402

OUT = DCI1 / "reports" / "dci1v4r3"
RUNS = OUT / "microcase_runs"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(
        name, DCI1 / "tools" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


V4R3 = _load("gate1_autorater_v4r3")
run_backend = V4R3.V4.run_backend

# --------------------------------------------------------------- the prompt
#
# Short, and deliberately so. §10.4-R's task asked the judge not to recount and
# it recounted anyway; here there is nothing to recount --- the answer is a
# dozen words at most --- and no derivation to endorse, because none is shown.

_BODY = (
    "You are checking whether a short answer satisfies a written instruction.\n"
    "\n"
    "INSTRUCTION: {instruction}\n"
    "\n"
    "ANSWER, between the two markers, and it may be empty:\n"
    "[begin answer]\n"
    "{answer}\n"
    "[end answer]\n"
    "\n"
    "The answer is a fragment, not a full response. Do not judge its topic, "
    "its usefulness or its style. Judge only whether it satisfies the "
    "INSTRUCTION exactly as the INSTRUCTION is written.\n"
    "\n"
    "Reply with exactly one word on the first line: YES or NO. If NO, add one "
    "short line naming what is wrong.\n"
)

MICROCASE_PROMPTS = {
    "microcase/1.0.0": _BODY,
    "microcase-conventions/1.0.0": CONVENTIONS_TEXT + "\n\n" + _BODY,
}
PROMPT_OF_ARM = {ARM_INSTRUCTION: "microcase/1.0.0",
                 ARM_CONVENTIONS: "microcase-conventions/1.0.0"}
PARSER_VERSION = "microcase-parse/1.0.0"
LABEL_MAPPING = {"YES": True, "NO": False}

#: The largest cap the registered judge can actually run, and how it is got.
#:
#: §10.4-R registered 8,192 as its non-binding cap fallback and named it as the
#: contingency for exactly the truncation failure it then suffered. **That
#: contingency was never runnable.** The registered judge carries
#: `max_model_len = 4096`, and vLLM is given `max_tokens` directly, so a
#: request for 8,192 new tokens does not fit in the context the engine was
#: built with. The first R2 attempt was configured at 8,192, produced zero
#: judged rows, and is retained at
#: `reports/dci1v4r3/microcase_runs/development-mc-medium-instruction_only-rep0/`
#: as the evidence for that sentence.
#:
#: So the cap is *derived* rather than chosen: the judge's own context less a
#: registered headroom for the prompt, asserted against the longest prompt the
#: case set actually produces. A number that cannot silently exceed the engine
#: is worth more here than a number that sounds generous.
PROMPT_HEADROOM_TOKENS = 512


def microcase_cap() -> int:
    return get_judge("gpt-oss-20b").max_model_len - PROMPT_HEADROOM_TOKENS


MICROCASE_CAP = microcase_cap()

CONDITIONS = {
    "mc-medium": {"reasoning_effort": "medium", "cap": MICROCASE_CAP},
    "mc-high": {"reasoning_effort": "high", "cap": MICROCASE_CAP},
    "mc-low": {"reasoning_effort": "low", "cap": MICROCASE_CAP},
}


def assert_prompts_fit(cases: list[dict[str, Any]]) -> dict[str, int]:
    """Every rendered prompt fits inside the registered headroom.

    Characters over four is a deliberate over-estimate of tokens for English
    prose; the point is a bound that fails loudly, not an exact count.
    """
    longest = 0
    for case in cases:
        for arm in (ARM_INSTRUCTION, ARM_CONVENTIONS):
            longest = max(longest, len(render(case, arm)))
        estimate = longest // 3
    if estimate >= PROMPT_HEADROOM_TOKENS:
        raise SystemExit(
            f"the longest microcase prompt is about {estimate} tokens and the "
            f"registered headroom is {PROMPT_HEADROOM_TOKENS}; the cap would "
            "not fit the engine's context")
    return {"longest_prompt_chars": longest, "estimated_tokens": estimate,
            "headroom": PROMPT_HEADROOM_TOKENS, "cap": MICROCASE_CAP}

#: §10.4-R's thresholds, carried unchanged. The unit of validation moved; what
#: counts as an adequate validator did not, and R2 must not be easier to pass
#: than the pathway it replaces.
THRESHOLDS = {
    "truncation_pooled_max": 0.10,
    "truncation_group_max": 0.20,
    "parse_validity_min": 0.95,
    "specificity_min": 0.90,
    "sensitivity_min": 0.80,
    "sensitivity_per_kind_min": 0.50,
    "per_kind_min_items": 4,
    # New in R2, and new because the unit is now small enough that a stable
    # answer is a reasonable thing to require. Two replicates of one frozen
    # configuration must agree on this share of parsed labels.
    "repeatability_min": 0.95,
}

_HARMONY_FINAL = "<|channel|>final<|message|>"
_HARMONY_STOPS = ("<|return|>", "<|end|>", "<|start|>")
VALID, REFUSAL, INVALID_OUTPUT = "valid", "refusal", "invalid_output"
_REFUSAL_MARKERS = ("i can't", "i cannot", "i won't", "i am unable",
                    "i'm unable", "as an ai")


def parse(raw: str) -> tuple[str, bool | None, str | None]:
    """(status, label, justification) --- parser microcase-parse/1.0.0."""
    text = (raw or "").strip()
    if not text:
        return INVALID_OUTPUT, None, None
    if "<|channel|>" in text:
        if _HARMONY_FINAL not in text:
            return INVALID_OUTPUT, None, None
        text = text.split(_HARMONY_FINAL, 1)[1]
        for stop in _HARMONY_STOPS:
            text = text.split(stop, 1)[0]
        text = text.strip()
    lowered = text.lower()
    if any(marker in lowered[:200] for marker in _REFUSAL_MARKERS):
        return REFUSAL, None, None
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if not lines:
        return INVALID_OUTPUT, None, None
    head = lines[0].strip().strip("*_# ").rstrip(".:").upper()
    for token, label in LABEL_MAPPING.items():
        if head == token or head.startswith(token):
            why = lines[1] if len(lines) > 1 else None
            return VALID, label, why
    return INVALID_OUTPUT, None, None


def render(case: dict[str, Any], arm: str) -> str:
    """The answer is inserted verbatim, never described.

    An empty answer renders as an empty line between the two markers. It is
    not replaced by a sentence saying it is empty, because that sentence would
    put words into the one case whose whole point is that there are none.
    """
    return MICROCASE_PROMPTS[PROMPT_OF_ARM[arm]].format(
        instruction=case["instruction"], answer=case["text"])


def validator_config(condition: str) -> dict[str, Any]:
    settings = CONDITIONS[condition]
    config = {
        "condition": condition,
        "judge_model_key": "gpt-oss-20b",
        "judge_revision": get_judge("gpt-oss-20b").revision,
        "prompts": {arm: PROMPT_OF_ARM[arm]
                    for arm in (ARM_INSTRUCTION, ARM_CONVENTIONS)},
        "prompt_hashes": {name: sha_text(body)
                          for name, body in MICROCASE_PROMPTS.items()},
        "parser_version": PARSER_VERSION,
        "reasoning_effort": settings["reasoning_effort"],
        "output_cap": settings["cap"],
        "temperature": 0.0,
        "generator_hash": generator_hash(),
        "verifier_hash": verifier_source_hash(),
        "thresholds": THRESHOLDS,
    }
    config["config_hash"] = sha_obj(config)
    return config


# ------------------------------------------------------------------ the run

def run_arm(cases: list[dict[str, Any]], arm: str, condition: str, *,
            device: int, replicate: int, phase: str) -> dict[str, Any]:
    config = validator_config(condition)
    spec = get_judge(config["judge_model_key"])
    plan = build_plan(spec, stage="v4r3-gate1-microcase",
                      max_new_tokens=CONDITIONS[condition]["cap"],
                      temperature=0.0, skip_special_tokens=False,
                      serialised=True)
    effort = CONDITIONS[condition]["reasoning_effort"]
    plan["chat_template_kwargs"] = {"reasoning_effort": effort}
    plan["thinking_policy"] = effort

    design_rows = []
    for case in cases:
        prompt = render(case, arm)
        design_rows.append({
            "cell_id": f"{arm}:{case['case_id']}", "draw_index": 0,
            "row_id": f"microcase:{arm}:{case['case_id']}",
            "prompt_hash": sha_text(prompt), "scientific_seed": 0,
            "user_prompt": prompt})

    sample_hash = sha_obj(sorted(c["case_id"] for c in cases))[:12]
    run_dir = (RUNS / f"{phase}-{condition}-{arm}-rep{replicate}"
               / f"{config['config_hash'][:12]}-{sample_hash}")
    started = time.monotonic()
    outcome = run_backend(run_dir, plan, design_rows, device=device,
                          timeout_seconds=60 * 60 * 10)
    elapsed = time.monotonic() - started

    by_row = {r["row_id"]: r for r in outcome["rows"]}
    rows = []
    for case, design in zip(cases, design_rows):
        raw = by_row.get(design["row_id"], {})
        text = raw.get("final_answer") or raw.get("raw_text") or ""
        status, label, why = parse(text)
        rows.append({
            "case_id": case["case_id"], "arm": arm, "kind": case["kind"],
            "form": case["form"], "severity": case["severity"],
            "covers": case["covers"], "discriminates": case["discriminates"],
            "correct": case["correct"], "status": status, "label": label,
            "agrees": None if label is None else (label == case["correct"]),
            "justification": why,
            "truncated": bool(raw.get("answer_truncated")),
            "tokens": raw.get("total_generated_tokens"),
            "config_hash": config["config_hash"],
            "prompt_hash": design["prompt_hash"]})
    return {"arm": arm, "condition": condition, "replicate": replicate,
            "phase": phase, "config": config, "items": len(cases),
            "rows": rows, "seconds": round(elapsed, 1),
            "seconds_per_item": round(elapsed / max(1, len(cases)), 2),
            "run_dir": str(run_dir.relative_to(DCI1))}


# ------------------------------------------------------------- the criteria

def _rate(hits: int, total: int) -> float | None:
    return hits / total if total else None


def evaluate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """The registered rates. Computed, not judged; `verdict` judges."""
    n = len(rows)
    truncated = sum(1 for r in rows if r["truncated"])
    parsed = [r for r in rows if r["status"] == VALID]

    by_group: dict[str, dict[str, int]] = {}
    for r in rows:
        group = f"{r['arm']}:{r['form']}"
        entry = by_group.setdefault(group, {"n": 0, "truncated": 0})
        entry["n"] += 1
        entry["truncated"] += int(r["truncated"])

    satisfied = [r for r in parsed if r["correct"]]
    violated = [r for r in parsed if not r["correct"]]

    per_kind: dict[str, dict[str, Any]] = {}
    for defect in DEFECT_KINDS:
        arm = ARM_OF_DEFECT[defect]
        items = [r for r in parsed
                 if r["arm"] == arm and defect in r["discriminates"]]
        per_kind[defect] = {
            "arm": arm, "n": len(items),
            "agreed": sum(1 for r in items if r["agrees"]),
            "sensitivity": _rate(sum(1 for r in items if r["agrees"]),
                                 len(items))}

    return {
        "n": n,
        "truncation": {
            "pooled": _rate(truncated, n),
            "by_group": {g: {**e, "rate": _rate(e["truncated"], e["n"])}
                         for g, e in sorted(by_group.items())}},
        "parse_validity": _rate(len(parsed), n),
        "status_counts": {s: sum(1 for r in rows if r["status"] == s)
                          for s in (VALID, REFUSAL, INVALID_OUTPUT)},
        "specificity": {
            "n": len(satisfied), "definition":
                "agreement with the registered verdict on cases the verifier "
                "records as satisfied --- the false-alarm side",
            "value": _rate(sum(1 for r in satisfied if r["agrees"]),
                           len(satisfied))},
        "sensitivity": {
            "n": len(violated), "definition":
                "agreement with the registered verdict on cases the verifier "
                "records as not satisfied --- the detection side",
            "value": _rate(sum(1 for r in violated if r["agrees"]),
                           len(violated)),
            "by_defect": per_kind},
        "by_arm": {
            arm: {"n": sum(1 for r in rows if r["arm"] == arm),
                  "parsed": sum(1 for r in parsed if r["arm"] == arm),
                  "agreement": _rate(
                      sum(1 for r in parsed if r["arm"] == arm and r["agrees"]),
                      sum(1 for r in parsed if r["arm"] == arm))}
            for arm in (ARM_INSTRUCTION, ARM_CONVENTIONS)},
        "composition": {
            "satisfied": sum(1 for r in rows if r["correct"]),
            "not_satisfied": sum(1 for r in rows if not r["correct"])},
    }


def repeatability(rows_a: list[dict], rows_b: list[dict]) -> dict[str, Any]:
    """Label agreement between two replicates of one frozen configuration."""
    index = {(r["arm"], r["case_id"]): r for r in rows_b}
    both, same = 0, 0
    for row in rows_a:
        other = index.get((row["arm"], row["case_id"]))
        if other is None or row["label"] is None or other["label"] is None:
            continue
        both += 1
        same += int(row["label"] == other["label"])
    return {"comparable": both, "identical": same,
            "value": _rate(same, both)}


def verdict(metrics: dict[str, Any],
            repeat: dict[str, Any] | None = None) -> dict[str, Any]:
    """Apply the registered thresholds. No threshold is computed from data."""
    t = THRESHOLDS
    checks: list[dict[str, Any]] = []

    trunc = metrics["truncation"]
    worst = max(((g, e["rate"]) for g, e in trunc["by_group"].items()
                 if e["rate"] is not None),
                key=lambda kv: kv[1], default=(None, 0.0))
    checks.append({
        "criterion": "2 adequate output cap and absence of problematic "
                     "truncation",
        "passed": (trunc["pooled"] is not None
                   and trunc["pooled"] <= t["truncation_pooled_max"]
                   and worst[1] <= t["truncation_group_max"]),
        "observed": {"pooled": trunc["pooled"], "worst_group": worst[0],
                     "worst_group_rate": worst[1]},
        "threshold": {"pooled": t["truncation_pooled_max"],
                      "per_group": t["truncation_group_max"]}})

    checks.append({
        "criterion": "3 valid parsing and coverage",
        "passed": (metrics["parse_validity"] is not None
                   and metrics["parse_validity"] >= t["parse_validity_min"]),
        "observed": metrics["parse_validity"],
        "threshold": t["parse_validity_min"]})

    spec = metrics["specificity"]["value"]
    checks.append({
        "criterion": "4 specificity on cases the verifier records as satisfied",
        "passed": spec is not None and spec >= t["specificity_min"],
        "observed": spec, "threshold": t["specificity_min"]})

    sens = metrics["sensitivity"]["value"]
    thin = {k: e for k, e in metrics["sensitivity"]["by_defect"].items()
            if e["n"] >= t["per_kind_min_items"]}
    failing = {k: e["sensitivity"] for k, e in thin.items()
               if e["sensitivity"] is None
               or e["sensitivity"] < t["sensitivity_per_kind_min"]}
    checks.append({
        "criterion": "5 sensitivity, overall and per defect kind",
        "passed": (sens is not None and sens >= t["sensitivity_min"]
                   and not failing),
        "observed": {"overall": sens,
                     "by_defect": {k: e["sensitivity"]
                                   for k, e in sorted(thin.items())},
                     "kinds_below_floor": failing,
                     "kinds_with_too_few_items": sorted(
                         set(metrics["sensitivity"]["by_defect"]) - set(thin))},
        "threshold": {"overall": t["sensitivity_min"],
                      "per_kind": t["sensitivity_per_kind_min"],
                      "per_kind_min_items": t["per_kind_min_items"]}})

    if repeat is not None:
        checks.append({
            "criterion": "6 repeatability across two replicates of one frozen "
                         "configuration",
            "passed": (repeat["value"] is not None
                       and repeat["value"] >= t["repeatability_min"]),
            "observed": repeat, "threshold": t["repeatability_min"]})

    failed = [c["criterion"] for c in checks if not c["passed"]]
    return {"checks": checks, "failed": failed,
            "outcome": "PASS" if not failed else "FAIL",
            "thresholds_registered_at":
                "§10.4-R2 and DECISIONS A7, before any microcase was judged; "
                "criteria 2 to 5 carried unchanged from §10.4-R"}


# ---------------------------------------------------------------- commands

def _cases(phase: str) -> list[dict[str, Any]]:
    every = build_cases()
    half = split_cases(every)[phase]
    return [c.as_dict() for c in half]


def cmd_cases(args) -> int:
    every = build_cases()
    split = split_cases(every)
    payload = {
        "artifact_type": "v4r3-microcase-set",
        "classification": CLASSIFICATION,
        "generator_hash": generator_hash(),
        "case_set_hash": case_set_hash(every),
        "verifier_hash": verifier_source_hash(),
        "strata": stratum_counts(every),
        "split": {half: {"n": len(cases),
                         "hash": case_set_hash(cases),
                         "strata": stratum_counts(cases)}
                  for half, cases in split.items()},
        "arms": {"instruction_only": "the wording and the answer",
                 "with_conventions": "and §7.3's registered lexical and rate "
                                     "rules, constant across every case"},
        "defect_arm": dict(ARM_OF_DEFECT),
        "families": sorted(FAMILIES),
        "cases": [c.as_dict() for c in every],
    }
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "microcase_set.json"
    path.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n")
    print(json.dumps({k: payload[k] for k in
                      ("generator_hash", "case_set_hash", "strata")}, indent=1))
    print(f"wrote {path.relative_to(DCI1)}")
    return 0


def _run_phase(args, phase: str) -> dict[str, Any]:
    cases = _cases(phase)
    fit = assert_prompts_fit(cases)
    results = [run_arm(cases, arm, args.condition, device=args.device,
                       replicate=args.replicate, phase=phase)
               for arm in (ARM_INSTRUCTION, ARM_CONVENTIONS)]
    rows = [r for result in results for r in result["rows"]]
    metrics = evaluate(rows)
    payload = {
        "artifact_type": "v4r3-microcase-run",
        "classification": CLASSIFICATION,
        "phase": phase, "condition": args.condition,
        "replicate": args.replicate,
        "config": results[0]["config"], "prompt_fit": fit,
        "case_set_hash": case_set_hash(build_cases()),
        "split_hash": sha_obj(sorted(c["case_id"] for c in cases)),
        "arms": [{k: v for k, v in r.items() if k != "rows"} for r in results],
        "metrics": metrics,
        "verdict": verdict(metrics),
        "rows": rows,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    name = f"section_10_4R2_{phase}_{args.condition}_rep{args.replicate}.json"
    (OUT / name).write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n")
    print(json.dumps({"phase": phase, "condition": args.condition,
                      "replicate": args.replicate,
                      "outcome": payload["verdict"]["outcome"],
                      "failed": payload["verdict"]["failed"],
                      "metrics": {k: metrics[k] for k in
                                  ("parse_validity", "specificity",
                                   "sensitivity", "by_arm")},
                      "seconds_per_item": [r["seconds_per_item"]
                                           for r in results],
                      "wrote": name}, indent=1, default=str))
    return payload


def cmd_develop(args) -> int:
    payload = _run_phase(args, "development")
    return 0 if payload["verdict"]["outcome"] == "PASS" else 1


def cmd_calibrate(args) -> int:
    payload = _run_phase(args, "calibration")
    return 0 if payload["verdict"]["outcome"] == "PASS" else 1


def cmd_repeat(args) -> int:
    """Criterion 6, over two development replicates already run."""
    a = json.loads((OUT / f"section_10_4R2_development_{args.condition}"
                          f"_rep0.json").read_text())
    b = json.loads((OUT / f"section_10_4R2_development_{args.condition}"
                          f"_rep1.json").read_text())
    repeat = repeatability(a["rows"], b["rows"])
    result = verdict(a["metrics"], repeat)
    path = OUT / f"section_10_4R2_repeatability_{args.condition}.json"
    path.write_text(json.dumps({"artifact_type": "v4r3-microcase-repeatability",
                                "condition": args.condition,
                                "repeatability": repeat,
                                "verdict": result}, indent=1) + "\n")
    print(json.dumps({"repeatability": repeat, "outcome": result["outcome"],
                      "failed": result["failed"]}, indent=1))
    return 0 if result["outcome"] == "PASS" else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("cases").set_defaults(func=cmd_cases)
    for name, func in (("develop", cmd_develop), ("calibrate", cmd_calibrate)):
        cmd = sub.add_parser(name)
        cmd.add_argument("--condition", default="mc-medium",
                         choices=sorted(CONDITIONS))
        cmd.add_argument("--replicate", type=int, default=0)
        cmd.add_argument("--device", type=int, default=0)
        cmd.set_defaults(func=func)
    rep = sub.add_parser("repeat")
    rep.add_argument("--condition", default="mc-medium",
                     choices=sorted(CONDITIONS))
    rep.set_defaults(func=cmd_repeat)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
