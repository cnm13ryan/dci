"""§10.4-R: the operationalization validator, development and calibration.

Amendment R1, registered at commit f657de2 **before** this tool was written and
before any card was judged. `user-notes/DCI1_preregistration_v4r3.md` §10.4-R
carries the criteria and their thresholds; `dci1/DECISIONS_V4R3.md` A5 carries
the decision; `DCI1_v4r2_to_v4r3_changelog.md` C26 carries the change.

What this tool does **not** do: score a generation, produce a compliance rate,
or approve anything. The deterministic verifier remains the study's scorer, and
`measurement_basis = autorater_calibration_approved` is written by
`run_v4r3.py`, only after both phases pass, and only under the researcher's
recorded authorisation.

Usage::

    gate1_validator_v4r3.py develop --condition v4r-medium --items 96
    gate1_validator_v4r3.py develop --condition v4r-medium --items 96 --replicate 1
    gate1_validator_v4r3.py select
    gate1_validator_v4r3.py freeze --condition <winner>
    gate1_validator_v4r3.py calibrate --items 96
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
from dci1v4.stages import autorater                                 # noqa: E402
from dci1v4r3 import CLASSIFICATION                                 # noqa: E402
from dci1v4r3.stages.operationalization import (                    # noqa: E402
    MUTATIONS, build_card, card_record, card_text, mutate,
)
from dci1v4r3.verifiers import verifier_source_hash                 # noqa: E402
from dci1v4r3.verifiers.constraints import Constraint               # noqa: E402

OUT = DCI1 / "reports" / "dci1v4r3"
RUNS = OUT / "validator_runs"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(
        name, DCI1 / "tools" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


V4R3 = _load("gate1_autorater_v4r3")
run_backend = V4R3.V4.run_backend

# --------------------------------------------------------------- the prompt

VALIDATOR_PROMPTS = {
    "opcheck/1.0.0": (
        "You are auditing a checker. You are not answering a question and you "
        "are not being graded on your own writing.\n\n"
        "Below is an INSTRUCTION that was given to another system, the ANSWER "
        "that system produced, and a record of HOW A CHECKER SCORED IT: the "
        "word convention the checker used, what it counted, what it divided "
        "by if anything, the arithmetic it performed, and the verdict it "
        "recorded.\n\n"
        "Decide whether the checker's method is a correct reading of the "
        "INSTRUCTION. Consider whether what it counted is what the "
        "instruction asks about; whether what it divided by is the right "
        "basis; whether the comparison uses the right direction and the right "
        "threshold; whether the arithmetic shown is consistent with the "
        "ANSWER; and whether the recorded verdict follows from the "
        "comparison.\n\n"
        "Do not recount the answer yourself. Judge the method.\n\n"
        "{card}\n\n"
        "Reply with exactly one word on the first line: CORRECT or "
        "INCORRECT. If INCORRECT, add one short line naming what is wrong.\n"),
}
PARSER_VERSION = "opcheck-parse/1.0.0"
LABEL_MAPPING = {"CORRECT": "faithful", "INCORRECT": "defective"}
VALIDATOR_CAP = 2048

#: §10.4-R's registered fallback cap. Chosen to be **non-binding** rather than
#: tuned: the observed median generated length at medium effort is about 800
#: tokens against a 2,048 cap, so 8,192 puts the cap far outside the range any
#: judged item has used. It is not chosen by trying values until a threshold
#: passes, and the number was fixed before the larger-cap conditions ran.
VALIDATOR_CAP_LARGE = 8192

#: One condition is one hashed configuration. Two axes, both registered by
#: §10.4: the prompt version and the rendered reasoning effort — plus the
#: output cap, which §10.4-R names as the fallback when truncation binds and
#: which enters the configuration hash.
CONDITIONS = {
    "v4r-medium": {"prompt": "opcheck/1.0.0", "reasoning_effort": "medium",
                   "cap": VALIDATOR_CAP},
    "v4r-high": {"prompt": "opcheck/1.0.0", "reasoning_effort": "high",
                 "cap": VALIDATOR_CAP},
    # The two registered contingencies. `low` is a point on §10.4's own
    # reasoning-effort axis and the hierarchy's step 6 already prefers the
    # lower-cost setting; `medium-8k` is §10.4-R's named cap fallback.
    "v4r-low": {"prompt": "opcheck/1.0.0", "reasoning_effort": "low",
                "cap": VALIDATOR_CAP},
    "v4r-medium-8k": {"prompt": "opcheck/1.0.0", "reasoning_effort": "medium",
                      "cap": VALIDATOR_CAP_LARGE},
}


def cap_of(condition: str) -> int:
    return CONDITIONS[condition].get("cap", VALIDATOR_CAP)

#: §10.4-R, registered at f657de2 before any card was judged.
THRESHOLDS = {
    "truncation_pooled_max": 0.10,
    "truncation_group_max": 0.20,
    "parse_validity_min": 0.95,
    "specificity_min": 0.90,
    "sensitivity_min": 0.80,
    "sensitivity_per_kind_min": 0.50,
    "per_kind_min_items": 4,
    "indistinguishable": 0.05,
}

_HARMONY_FINAL = "<|channel|>final<|message|>"
_HARMONY_STOPS = ("<|return|>", "<|end|>", "<|start|>")
VALID, REFUSAL, INVALID_OUTPUT = "valid", "refusal", "invalid_output"
_REFUSAL_MARKERS = ("i can't", "i cannot", "i won't", "i am unable",
                    "i'm unable", "as an ai")


def parse(raw: str) -> tuple[str, str | None, str | None]:
    """(status, label, justification) — parser opcheck-parse/1.0.0.

    CORRECT/INCORRECT on the first line of the final message. Every other
    outcome keeps its own operational status and is never recoded to a label.
    """
    text = (raw or "").strip()
    if not text:
        return INVALID_OUTPUT, None, None
    if "<|channel|>" in text:
        if _HARMONY_FINAL not in text:
            return INVALID_OUTPUT, None, None     # never reached a verdict
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


# ----------------------------------------------------------------- the cards

def build_cards(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """One card per item; every second item carries one planted defect.

    Assignment is deterministic in item id order, and the defect kind rotates
    through the registered list, so the composition is a property of the split
    rather than of a random draw. An item whose applicable-mutation set is
    empty stays faithful and is recorded as such.
    """
    kinds = sorted(MUTATIONS)
    used = {kind: 0 for kind in kinds}
    out: list[dict[str, Any]] = []
    for position, item in enumerate(sorted(items, key=lambda i: i["item_id"])):
        constraint = Constraint(item["instrument"], item["severity"],
                                extended=True, reserve=True)
        card = build_card(constraint, item["response"],
                          item_id=item["item_id"])
        if position % 2 == 1:
            # Least-used applicable kind, ties broken by name. A plain
            # rotation does not work here: three of the six defects apply only
            # to rate families, and A and B items -- which admit only
            # off_by_one and inequality_flip -- would absorb the rotation and
            # leave the rate-only kinds below criterion 5's four-item minimum,
            # excluding them from the per-kind floor. That would weaken the
            # criterion exactly where it does the most work.
            candidates = [(used[k], k, mutate(card, k)) for k in kinds]
            applicable = [c for c in candidates if c[2] is not None]
            if applicable:
                _, kind, mutated = min(applicable, key=lambda c: (c[0], c[1]))
                used[kind] += 1
                card = mutated
        out.append({"item": item, "card": card})
    return out


def render(card, condition: str) -> str:
    template = VALIDATOR_PROMPTS[CONDITIONS[condition]["prompt"]]
    return template.format(card=card_text(card))


def validator_config(condition: str) -> dict[str, Any]:
    spec = CONDITIONS[condition]
    return autorater.build_config(
        "gpt-oss-20b",
        backend=("vllm-subprocess; dci1/environments/backend/.venv, pinned "
                 "vLLM 0.15.1+rocm720"),
        prompt_version=spec["prompt"],
        prompt_hash=sha_text(VALIDATOR_PROMPTS[spec["prompt"]]),
        parser_version=PARSER_VERSION,
        label_mapping=dict(LABEL_MAPPING),
        decoding={"policy": "greedy", "max_new_tokens": cap_of(condition),
                  "skip_special_tokens": False,
                  "chat_template_kwargs":
                      {"reasoning_effort": spec["reasoning_effort"]}},
        output_cap=cap_of(condition),
        execution_concurrency=1, execution_mode="serialised")


def run_condition(cards: list[dict[str, Any]], condition: str, *, device: int,
                  replicate: int = 0, phase: str = "development"
                  ) -> dict[str, Any]:
    """Judge every card once, serialised at concurrency one (§10.4)."""
    config = validator_config(condition)
    spec = get_judge(config["judge_model_key"])
    plan = build_plan(spec, stage="v4r3-gate1-opcheck",
                      max_new_tokens=cap_of(condition), temperature=0.0,
                      skip_special_tokens=False, serialised=True)
    effort = CONDITIONS[condition]["reasoning_effort"]
    plan["chat_template_kwargs"] = {"reasoning_effort": effort}
    plan["thinking_policy"] = effort

    design_rows = []
    for entry in cards:
        prompt = render(entry["card"], condition)
        design_rows.append({
            "cell_id": entry["card"].item_id, "draw_index": 0,
            "row_id": f"opcheck:{entry['card'].item_id}",
            "prompt_hash": sha_text(prompt), "scientific_seed": 0,
            "user_prompt": prompt})

    sample_hash = sha_obj(sorted(e["card"].item_id for e in cards))[:12]
    run_dir = (RUNS / f"{phase}-{condition}-rep{replicate}"
               / f"{config['config_hash'][:12]}-{sample_hash}")
    started = time.monotonic()
    outcome = run_backend(run_dir, plan, design_rows, device=device,
                          timeout_seconds=60 * 60 * 10)
    elapsed = time.monotonic() - started

    by_row = {r["row_id"]: r for r in outcome["rows"]}
    rows = []
    for entry, design in zip(cards, design_rows):
        card, item = entry["card"], entry["item"]
        raw = by_row.get(design["row_id"], {})
        text = raw.get("final_answer") or raw.get("raw_text") or ""
        status, label, why = parse(text)
        rows.append({
            **card_record(card),
            "group": item["group"], "status": status, "label": label,
            "justification": why,
            "truncated": bool(raw.get("answer_truncated")),
            "tokens": raw.get("total_generated_tokens"),
            "config_hash": config["config_hash"],
            "prompt_hash": design["prompt_hash"]})
    return {"condition": condition, "replicate": replicate, "phase": phase,
            "config": config, "items": len(cards), "rows": rows,
            "seconds": round(elapsed, 1),
            "seconds_per_item": round(elapsed / max(1, len(cards)), 2),
            "run_dir": str(run_dir.relative_to(DCI1))}


# ------------------------------------------------------------- the criteria

def _rate(hits: int, total: int) -> float | None:
    return hits / total if total else None


def evaluate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """§10.4-R criteria 2 to 5, computed but not judged. `verdict` judges."""
    n = len(rows)
    truncated = sum(1 for r in rows if r["truncated"])
    parsed = [r for r in rows if r["status"] == VALID]

    by_group: dict[str, dict[str, int]] = {}
    for r in rows:
        entry = by_group.setdefault(r["group"], {"n": 0, "truncated": 0})
        entry["n"] += 1
        entry["truncated"] += int(r["truncated"])

    faithful = [r for r in parsed if r["faithful"]]
    mutated = [r for r in parsed if not r["faithful"]]
    per_kind: dict[str, dict[str, Any]] = {}
    for r in mutated:
        entry = per_kind.setdefault(r["defect"], {"n": 0, "caught": 0})
        entry["n"] += 1
        entry["caught"] += int(r["label"] == "defective")
    for entry in per_kind.values():
        entry["sensitivity"] = _rate(entry["caught"], entry["n"])

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
            "n": len(faithful),
            "value": _rate(sum(1 for r in faithful
                               if r["label"] == "faithful"), len(faithful))},
        "sensitivity": {
            "n": len(mutated),
            "value": _rate(sum(1 for r in mutated
                               if r["label"] == "defective"), len(mutated)),
            "by_defect": per_kind},
        "composition": {"faithful_cards": sum(1 for r in rows if r["faithful"]),
                        "mutated_cards": sum(1 for r in rows
                                             if not r["faithful"])},
    }


def verdict(metrics: dict[str, Any]) -> dict[str, Any]:
    """Apply the registered thresholds. No threshold is computed from data."""
    t = THRESHOLDS
    checks: list[dict[str, Any]] = []

    trunc = metrics["truncation"]
    worst_group = max(
        ((g, e["rate"]) for g, e in trunc["by_group"].items()
         if e["rate"] is not None), key=lambda kv: kv[1], default=(None, 0.0))
    checks.append({
        "criterion": "2 adequate output cap and absence of problematic "
                     "truncation",
        "passed": (trunc["pooled"] is not None
                   and trunc["pooled"] <= t["truncation_pooled_max"]
                   and worst_group[1] <= t["truncation_group_max"]),
        "observed": {"pooled": trunc["pooled"],
                     "worst_group": worst_group[0],
                     "worst_group_rate": worst_group[1]},
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
        "criterion": "4 specificity on faithful cards",
        "passed": spec is not None and spec >= t["specificity_min"],
        "observed": spec, "threshold": t["specificity_min"]})

    sens = metrics["sensitivity"]["value"]
    thin = {k: e for k, e in metrics["sensitivity"]["by_defect"].items()
            if e["n"] >= t["per_kind_min_items"]}
    failing_kinds = {k: e["sensitivity"] for k, e in thin.items()
                     if e["sensitivity"] < t["sensitivity_per_kind_min"]}
    checks.append({
        "criterion": "5 sensitivity on mutated cards",
        "passed": (sens is not None and sens >= t["sensitivity_min"]
                   and not failing_kinds),
        "observed": {"overall": sens,
                     "by_defect": {k: e["sensitivity"]
                                   for k, e in sorted(thin.items())},
                     "kinds_below_floor": failing_kinds,
                     "kinds_with_too_few_items": sorted(
                         set(metrics["sensitivity"]["by_defect"]) - set(thin))},
        "threshold": {"overall": t["sensitivity_min"],
                      "per_kind": t["sensitivity_per_kind_min"],
                      "per_kind_min_items": t["per_kind_min_items"]}})

    failed = [c["criterion"] for c in checks if not c["passed"]]
    return {"checks": checks, "failed": failed,
            "outcome": "PASS" if not failed else "FAIL",
            "thresholds_registered_at": "commit f657de2, before any card was "
                                        "judged (§10.4-R, DECISIONS A5)"}


# ---------------------------------------------------------------- commands

def _pool(items_n: int, phase: str):
    items = V4R3.build_items()
    split = V4R3.split_pool(items)
    half = split["development" if phase == "development" else "calibration"]
    return items, split, V4R3.subsample(half, items_n)


def cmd_develop(args) -> int:
    _, split, sample = _pool(args.items, "development")
    cards = build_cards(sample)
    result = run_condition(cards, args.condition, device=args.device,
                           replicate=args.replicate, phase="development")
    metrics = evaluate(result["rows"])
    payload = {
        "artifact": "§10.4-R operationalization validator, development phase",
        "amendment": "R1, registered at commit f657de2 before any judging",
        "classification": CLASSIFICATION,
        "canonical_verifier_hash": verifier_source_hash(),
        "deterministic_scorer_unchanged": True,
        "approves": "nothing. Gate 1 is NOT approved by this tool",
        "split_hash": split["split_hash"],
        "condition": result["condition"], "replicate": result["replicate"],
        "config": result["config"], "metrics": metrics,
        "verdict": verdict(metrics),
        "seconds_per_item": result["seconds_per_item"],
        "run_dir": result["run_dir"], "rows": result["rows"],
    }
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / (f"section_10_4R_{args.condition}"
                  f"{'' if args.replicate == 0 else f'-rep{args.replicate}'}"
                  ".json")
    path.write_text(json.dumps(payload, indent=1, sort_keys=True))
    print(json.dumps({"wrote": str(path.relative_to(DCI1)),
                      "verdict": payload["verdict"]["outcome"],
                      "failed": payload["verdict"]["failed"],
                      "metrics": {k: metrics[k] for k in
                                  ("truncation", "parse_validity",
                                   "specificity", "sensitivity")}},
                     indent=1, default=str))
    return 0


def cmd_select(args) -> int:
    """§10.4's hierarchy over whatever development runs exist."""
    runs = {}
    for path in sorted(OUT.glob("section_10_4R_*.json")):
        payload = json.loads(path.read_text())
        if payload.get("replicate"):
            continue
        runs[payload["condition"]] = payload
    if not runs:
        print(json.dumps({"error": "no development runs"}))
        return 1

    repeat = {}
    for condition in runs:
        rep = OUT / f"section_10_4R_{condition}-rep1.json"
        if not rep.exists():
            repeat[condition] = {"checked": False}
            continue
        other = json.loads(rep.read_text())
        base = {r["item_id"]: r["label"] for r in runs[condition]["rows"]}
        again = {r["item_id"]: r["label"] for r in other["rows"]}
        shared = sorted(set(base) & set(again))
        agree = sum(1 for i in shared if base[i] == again[i])
        repeat[condition] = {
            "checked": True, "items": len(shared),
            "agreement": agree / len(shared) if shared else None,
            "passed": bool(shared) and agree == len(shared)}

    steps = []
    surviving = [c for c in sorted(runs)
                 if repeat[c].get("checked") and repeat[c].get("passed")]
    steps.append({"criterion": "1 valid deterministic execution",
                  "surviving": surviving,
                  "values": {c: repeat[c] for c in sorted(runs)}})
    for index, name in ((1, "2 adequate output cap and absence of problematic "
                            "truncation"),
                        (2, "3 valid parsing and coverage"),
                        (3, "4 specificity on faithful cards"),
                        (4, "5 sensitivity on mutated cards")):
        nxt = [c for c in surviving
               if runs[c]["verdict"]["checks"][index - 1]["passed"]]
        steps.append({"criterion": name, "surviving": nxt,
                      "values": {c: runs[c]["verdict"]["checks"][index - 1]
                                 ["observed"] for c in surviving}})
        surviving = nxt

    chosen = None
    if len(surviving) == 1:
        chosen = surviving[0]
    elif len(surviving) > 1:
        # criterion 6: the lower-cost setting when indistinguishable
        def key(c):
            return (runs[c]["seconds_per_item"], c)
        spread = max(
            abs((runs[a]["metrics"][m]["value"] or 0)
                - (runs[b]["metrics"][m]["value"] or 0))
            for m in ("specificity", "sensitivity")
            for a in surviving for b in surviving)
        if spread <= THRESHOLDS["indistinguishable"]:
            chosen = min(surviving, key=key)
            steps.append({"criterion": "6 the lower-cost setting",
                          "spread": spread, "chosen": chosen})
        else:
            chosen = max(surviving,
                         key=lambda c: runs[c]["metrics"]["sensitivity"]
                         ["value"] or 0)
            steps.append({"criterion": "6 not applicable; conditions differ",
                          "spread": spread, "chosen": chosen})

    out = {"artifact": "§10.4-R condition selection",
           "amendment": "R1", "steps": steps, "selected": chosen,
           "outcome": ("selected" if chosen
                       else "no condition survives the hierarchy"),
           "approves": "nothing"}
    path = OUT / "section_10_4R_selection.json"
    path.write_text(json.dumps(out, indent=1, sort_keys=True, default=str))
    print(json.dumps(out, indent=1, default=str))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    dev = sub.add_parser("develop")
    dev.add_argument("--condition", required=True, choices=sorted(CONDITIONS))
    dev.add_argument("--items", type=int, default=96)
    dev.add_argument("--replicate", type=int, default=0)
    dev.add_argument("--device", type=int, default=0)
    dev.set_defaults(func=cmd_develop)
    sub.add_parser("select").set_defaults(func=cmd_select)
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
