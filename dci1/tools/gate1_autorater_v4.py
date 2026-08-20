"""The §10.4 autorater pathway for the A and B classes — development phase.

NOT a stage. Writes only to ``reports/gate1_v4/``. Approves nothing.

**What this deliberately does NOT do.** §10.4's single-shot signed freeze and
one-shot calibration are claimed through an append-only ledger and can be
performed exactly once. Both bind the canonical verifier hash. Three amendments
are pending, and Amendment C changes ``FOCAL_GRID``, which is inside the
semantic module set and therefore changes that hash. Claiming either one-shot
now would spend it on a hash that is likely to be superseded, and recovering
would require an explicit invalidation. So this tool runs the whole
development phase -- split derivation, serialised judge execution, the
repeatability check, the paired condition comparison and selection under the
§10.4 hierarchy -- and stops before the freeze. The held-out calibration half
is derived and hashed but never judged.

**Author labels are not independent validation.** The §10.4 hierarchy's fourth
criterion is agreement with human labels. No annotator independent of the design
and analysis team exists, so that criterion cannot be met and is reported as
outstanding; the first three criteria and the fifth are decided here.

Usage:
  PYTHONPATH=src python tools/gate1_autorater_v4.py --items 8 --probe
  PYTHONPATH=src python tools/gate1_autorater_v4.py --items 120 --device 0
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

DCI1 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DCI1 / "src"))

from dci1v4.generation.backend import build_plan, run_backend    # noqa: E402
from dci1v4.models.registry import get_judge                     # noqa: E402
from dci1v4.protocol.hashing import sha_obj, sha_text            # noqa: E402
from dci1v4.protocol.wordings import wording                     # noqa: E402
from dci1v4.stages import autorater                              # noqa: E402
from dci1v4.verifiers import verifier_source_hash                # noqa: E402

EVIDENCE = DCI1 / "evidence" / "dci1-v4"
OUT = DCI1 / "reports" / "gate1_v4"
RUNS = OUT / "judge_runs"

MODELS = ("gemma-3n-e2b-it", "gemma-3n-e4b-it", "qwen3-4b",
          "qwen3-4b-instruct-2507")

#: **The carried prompt.** Byte-identical to the v3 registered constant. v3's
#: only instrument was the exact-count rule; v4 adds the word-length rule, and
#: the probe below shows the carried prompt does not survive the change.
JUDGE_PROMPTS = {
    "gate1-judge/2.0.0": (
        "You are checking one rule against one text.\n"
        "Rule: {constraint}\n"
        "Text:\n{response}\n"
        "---\n"
        "Does the text satisfy the rule? Answer with exactly one word on "
        "the first line: SATISFIES or VIOLATES. You may add one short "
        "reason on the second line.\n"
        "Answer:"),
    # Authored for v4. The carried prompt fails on the B class for a reason
    # that is visible in the judge's own reasoning transcript: every registered
    # B wording says "the answer" ("Every word in the answer must have at most
    # 7 letters"), and after "Answer:" the judge reads that as binding on ITS
    # OWN reply -- "we must ensure that the answer itself has at most 7
    # letters". It then spends the whole 2048-token cap composing a compliant
    # reply and never reaches its verdict. This version says who "the answer"
    # is, delimits the text, and states that the judge's reply is not graded.
    "gate1-judge-v4/1.0.0": (
        "You are grading, not writing.\n\n"
        "Below is a RULE that was given to another system, and the TEXT that "
        "system produced in response. Decide whether the TEXT obeys the RULE.\n\n"
        "Wherever the rule says \"the answer\" or \"your answer\" it means the "
        "TEXT below, never your own reply. The rule does not apply to your "
        "reply and your reply is not graded.\n\n"
        "RULE: {constraint}\n\n"
        "TEXT:\n"
        "<<<\n{response}\n>>>\n\n"
        "Reply with exactly one word on the first line: SATISFIES or "
        "VIOLATES. You may add one short reason on a second line.\n"),
}
CARRIED_PROMPT_VERSION = "gate1-judge/2.0.0"
PARSER_VERSION = "gate1-parse/2.0.0"
LABEL_MAPPING = {"SATISFIES": "pass", "VIOLATES": "fail"}
JUDGE_CAP = 2048

_HARMONY_FINAL = "<|channel|>final<|message|>"
_HARMONY_STOPS = ("<|return|>", "<|end|>", "<|start|>")
VALID, REFUSAL, INVALID_OUTPUT = "valid", "refusal", "invalid_output"

#: One condition is one hashed configuration. Two axes: the prompt version and
#: the rendered reasoning effort. Compared paired on the same items (§10.4).
CONDITIONS = {
    "carried-medium": {"prompt": CARRIED_PROMPT_VERSION,
                       "reasoning_effort": "medium"},
    "carried-high": {"prompt": CARRIED_PROMPT_VERSION,
                     "reasoning_effort": "high"},
    "v4prompt-medium": {"prompt": "gate1-judge-v4/1.0.0",
                        "reasoning_effort": "medium"},
    "v4prompt-high": {"prompt": "gate1-judge-v4/1.0.0",
                      "reasoning_effort": "high"},
}

_REFUSAL_MARKERS = ("i can't", "i cannot", "i won't", "i am unable",
                    "i'm unable", "as an ai", "i do not feel comfortable")


def parse(raw: str) -> tuple[str, str | None, str | None]:
    """(status, label, justification) — parser gate1-parse/2.0.0.

    SATISFIES/VIOLATES on the first line of the judge's final message, mapped by
    LABEL_MAPPING. Every other outcome keeps its own operational status and is
    never recoded into a label.
    """
    text = (raw or "").strip()
    if not text:
        return INVALID_OUTPUT, None, None
    if "<|channel|>" in text:
        if _HARMONY_FINAL not in text:
            return INVALID_OUTPUT, None, None      # never reached its verdict
        text = text.rsplit(_HARMONY_FINAL, 1)[1]
        for stop in _HARMONY_STOPS:
            text = text.split(stop, 1)[0]
        text = text.strip()
        if not text:
            return INVALID_OUTPUT, None, None
    first, _, rest = text.partition("\n")
    token = "".join(ch for ch in first.strip().upper() if ch.isalpha())
    if token.startswith("SATISF"):
        return VALID, LABEL_MAPPING["SATISFIES"], rest.strip() or None
    if token.startswith("VIOLAT"):
        return VALID, LABEL_MAPPING["VIOLATES"], rest.strip() or None
    low = text.lower()
    if any(marker in low for marker in _REFUSAL_MARKERS):
        return REFUSAL, None, None
    return INVALID_OUTPUT, None, None


# ---------------------------------------------------------------- the pool
def build_items() -> list[dict[str, Any]]:
    """Natural A-class and B-class items from the registered §12.2 ladder screen.

    One item is a (constraint wording, response) pair the model actually saw,
    together with the deterministic verifier's stored verdict. The judge sees
    the wording the model saw, never the verifier and never the verdict.
    """
    items: list[dict[str, Any]] = []
    for model in MODELS:
        paths = sorted((EVIDENCE / model / "prescreen").glob(
            "ladder-cap*/cache.jsonl"))
        assert len(paths) == 1, paths
        for line in paths[0].open():
            row = json.loads(line)
            _, kind, severity = row["cell_type"].split(":")
            if kind not in ("A", "B"):
                continue
            severity = int(severity)
            score = row["scores"][0]
            statistic = score["statistic"]
            margin = (abs(statistic - severity) if kind == "A"
                      else max(0, statistic - severity))
            items.append({
                "item_id": f"{model}:{row['cell_type']}:{row['topic_id']}",
                "instrument": kind, "severity": severity,
                "constraint": wording(kind, score.get("wording_index", 0),
                                      severity),
                "response": row["raw_response"],
                "verifier_class": "pass" if score["passed"] else "fail",
                "statistic": statistic, "margin": margin,
                "margin_one": margin == 1,
                "word_count": row["word_count"],
                "model_key": model, "topic_id": row["topic_id"],
                "source": "registered §12.2 ladder screen (read only)"})
    return items


def stratum(item: dict[str, Any]) -> str:
    """Instrument x verifier class x fail-margin, the §10.3 strata."""
    if item["verifier_class"] == "pass":
        return f"{item['instrument']}:pass"
    return (f"{item['instrument']}:fail:margin_one" if item["margin_one"]
            else f"{item['instrument']}:fail:margin_larger")


def split_pool(items: list[dict[str, Any]]) -> dict[str, Any]:
    """§10.4: a deterministic class-stratified DISJOINT split.

    ``autorater.stratified_split`` strata on ``verifier_class``; the strata used
    here are finer -- instrument x class x fail margin -- so each is split by the
    registered function separately and the halves concatenated. The split is a
    pure function of the registered seed and the item ids.
    """
    by: dict[str, list] = {}
    for item in items:
        by.setdefault(stratum(item), []).append(item)
    development, calibration, per_stratum = [], [], {}
    for name, members in sorted(by.items()):
        # Every member of a stratum already shares one verifier_class, so
        # the registered function splits it as a single group. The items are
        # passed unchanged -- overwriting verifier_class here would corrupt
        # both stratum() downstream and the agreement denominator.
        result = autorater.stratified_split(members, model_id=f"v4:{name}")
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
            "seed": "protocol.seeds.AUTORATER_SPLIT_SEED, per stratum",
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


# --------------------------------------------------------------- execution
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
        # The rendered reasoning condition goes INSIDE `decoding`, which is
        # a hashed CONFIG_FIELD. `autorater.build_config` keeps only the
        # declared fields, so a caller that passed chat_template_kwargs as a
        # sibling would produce the SAME config_hash for medium and high --
        # two conditions that demonstrably produce different judgments. See
        # the finding recorded in the Track 2 report.
        decoding={"policy": "greedy", "max_new_tokens": JUDGE_CAP,
                  "skip_special_tokens": False,
                  "chat_template_kwargs":
                      {"reasoning_effort": spec["reasoning_effort"]}},
        output_cap=JUDGE_CAP,
        execution_concurrency=1, execution_mode="serialised")


def run_condition(items: list[dict[str, Any]], condition: str, *, device: int,
                  replicate: int = 0) -> dict[str, Any]:
    """Judge every item once, serialised at concurrency one (§10.4, T-15)."""
    config = judge_config(condition)
    spec = get_judge(config["judge_model_key"])
    plan = build_plan(spec, stage="gate1-judge", max_new_tokens=JUDGE_CAP,
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

    # The sample hash is in the path so a run over a different item set can
    # never resume from a previous run's rows.jsonl.
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
                     "instrument": item["instrument"],
                     "stratum": stratum(item),
                     "verifier_class": item["verifier_class"],
                     "margin": item["margin"],
                     "truncated": bool(raw.get("answer_truncated")),
                     "tokens": raw.get("total_generated_tokens"),
                     "config_hash": config["config_hash"],
                     "prompt_hash": design["prompt_hash"]})
    truncated = sum(1 for r in rows if r["truncated"])
    return {
        "condition": condition, "replicate": replicate,
        "config": config, "items": len(items),
        "judgments": judgments, "rows": rows,
        "status_counts": statuses,
        "coverage": len(judgments) / len(items) if items else 0.0,
        "truncated": truncated,
        "truncation_rate": truncated / len(items) if items else 0.0,
        "seconds": round(elapsed, 1),
        "seconds_per_item": round(elapsed / max(1, len(items)), 2),
        "run_dir": str(run_dir.relative_to(DCI1)),
    }


def agreement(judgments: dict[str, str],
              items: list[dict[str, Any]]) -> dict[str, Any]:
    per: dict[str, list[bool]] = {}
    for item in items:
        label = judgments.get(item["item_id"])
        if label is None:
            continue
        per.setdefault(stratum(item), []).append(
            label == item["verifier_class"])
        per.setdefault("overall", []).append(label == item["verifier_class"])
    return {k: {"n": len(v), "agreement": sum(v) / len(v)}
            for k, v in sorted(per.items())}


def _wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / d
    return (max(0.0, centre - half), min(1.0, centre + half))


def select(results: dict[str, dict], items: list[dict[str, Any]],
           repeatability: dict[str, Any]) -> dict[str, Any]:
    """§10.4's hierarchy, in order, under BOTH readings of its threshold words.

    Criterion 2 is worded "adequate output cap and **absence of problematic**
    truncation" and criterion 3 "**valid** parsing and coverage". Those are
    threshold words, not ranking words, and no threshold is registered. Two
    readings follow and they do not agree, so both are reported:

    * **ranking** -- take the best value at each criterion. Decisive, but it can
      decide on a difference of two items out of forty-eight.
    * **threshold** -- eliminate only a condition that is *distinguishably*
      worse than the best, meaning its 95% Wilson interval does not overlap the
      best condition's. Turns the threshold words into a decision without
      inventing a constant.

    A later criterion never overrides an earlier one under either reading.
    """
    names = sorted(results)

    def ranking(values, prefer):
        best = prefer(values.values())
        return [k for k, v in values.items() if v == best]

    def distinguishable(counts, n, *, lower_is_better):
        """Survivors: everything whose Wilson interval overlaps the best."""
        rates = {k: counts[k] / n[k] for k in counts}
        best = (min if lower_is_better else max)(rates.values())
        anchor = next(k for k, v in rates.items() if v == best)
        lo_a, hi_a = _wilson(counts[anchor], n[anchor])
        out = []
        for k in counts:
            lo, hi = _wilson(counts[k], n[k])
            worse_and_separated = (lo > hi_a) if lower_is_better else (hi < lo_a)
            if not worse_and_separated:
                out.append(k)
        return sorted(out)

    readings: dict[str, Any] = {}
    for reading in ("ranking", "threshold"):
        alive, steps = list(names), []
        det = {k: repeatability.get(k, {}).get("exactly_repeatable")
               for k in alive}
        if set(det.values()) != {None}:
            survivors = [k for k, v in det.items() if v] or alive
            steps.append({"criterion": "valid deterministic execution",
                          "values": det, "surviving": survivors,
                          "decided": len(survivors) == 1})
            alive = survivors
        if len(alive) > 1:
            trunc = {k: results[k]["truncated"] for k in alive}
            n = {k: results[k]["items"] for k in alive}
            survivors = (ranking({k: results[k]["truncation_rate"] for k in alive}, min)
                         if reading == "ranking"
                         else distinguishable(trunc, n, lower_is_better=True))
            steps.append({
                "criterion": ("adequate output cap and absence of problematic "
                              "truncation"),
                "values": {k: f"{trunc[k]}/{n[k]}" for k in alive},
                "surviving": survivors, "decided": len(survivors) == 1})
            alive = survivors
        if len(alive) > 1:
            covered = {k: len(results[k]["judgments"]) for k in alive}
            n = {k: results[k]["items"] for k in alive}
            survivors = (ranking({k: results[k]["coverage"] for k in alive}, max)
                         if reading == "ranking"
                         else distinguishable(covered, n, lower_is_better=False))
            steps.append({"criterion": "valid parsing and coverage",
                          "values": {k: f"{covered[k]}/{n[k]}" for k in alive},
                          "surviving": survivors,
                          "decided": len(survivors) == 1})
            alive = survivors
        human_pending = len(alive) > 1
        if human_pending:
            steps.append({
                "criterion": "agreement with human labels",
                "values": None, "surviving": alive, "decided": False,
                "note": ("OUTSTANDING. No annotator independent of the design "
                         "and analysis team exists, so §10.3's criterion cannot "
                         "be met; author labels are diagnostic evidence and "
                         "§10.4 hierarchy input, never independent validation.")})
        readings[reading] = {"steps": steps, "surviving": alive,
                             "decided_at": (steps[-1]["criterion"]
                                            if steps and steps[-1]["decided"]
                                            else None),
                             "human_criterion_outstanding": human_pending}

    return {
        "hierarchy": list(autorater.SELECTION_HIERARCHY),
        "readings": readings,
        "reading_note": (
            "criterion 2 says 'absence of PROBLEMATIC truncation' and criterion "
            "3 'VALID parsing and coverage'. Those are threshold words and no "
            "threshold is registered. The ranking reading takes the best value "
            "at each criterion; the threshold reading eliminates only what is "
            "distinguishably worse at 95%. Both are reported because they do "
            "not agree on whether criterion 4 is reached."),
        "agreed_by_both_readings": sorted(
            set(readings["ranking"]["surviving"])
            & set(readings["threshold"]["surviving"])),
        "steps": readings["ranking"]["steps"],
        "surviving_after_criteria_1_to_3": readings["ranking"]["surviving"],
        "human_criterion_outstanding": (
            readings["threshold"]["human_criterion_outstanding"]),
        "verifier_agreement_by_condition": {
            k: agreement(results[k]["judgments"], items) for k in names},
        "note": ("agreement with the deterministic VERIFIER is reported for "
                 "every condition but is not a selection criterion: §10.4's "
                 "fourth criterion is agreement with HUMAN labels. Selecting "
                 "the judge that best matches the verifier would make the "
                 "held-out evaluation circular."),
    }


COND_DIR = OUT / "conditions"


def emit_condition(condition: str, sample, *, device: int,
                   repeat_items: int = 0) -> dict[str, Any]:
    """Judge the whole sample once, then re-judge a prefix for repeatability.

    §10.4 asks for "a development-phase repeatability check" and fixes no size.
    Repeatability is a property of the execution path, not of the item set, so
    it is established on a prefix rather than on the whole sample -- which is
    what makes it affordable to measure it for the rejected conditions too,
    instead of only for the surviving one.
    """
    runs = [run_condition(sample, condition, device=device, replicate=0)]
    repeat = None
    if repeat_items:
        prefix = sample[:repeat_items]
        second = run_condition(prefix, condition, device=device, replicate=1)
        repeat = autorater.repeatability_check([
            [runs[0]["judgments"].get(i["item_id"], "") for i in prefix],
            [second["judgments"].get(i["item_id"], "") for i in prefix]])
        repeat["items"] = len(prefix)
        repeat["second_run"] = {k: second[k] for k in
                                ("coverage", "status_counts",
                                 "truncation_rate", "seconds", "run_dir")}
        runs.append(second)
    payload = {
        "condition": condition,
        "spec": dict(CONDITIONS[condition]),
        "config": runs[0]["config"],
        "replicates": [{k: run[k] for k in
                        ("replicate", "items", "status_counts", "coverage",
                         "truncated", "truncation_rate", "seconds",
                         "seconds_per_item", "run_dir")} for run in runs],
        "repeatability": repeat,
        "judgments": runs[0]["judgments"],
        "rows": runs[0]["rows"],
        "sample_hash": sha_obj(sorted(i["item_id"] for i in sample)),
    }
    COND_DIR.mkdir(parents=True, exist_ok=True)
    (COND_DIR / f"{condition}.json").write_text(
        json.dumps(payload, indent=1, sort_keys=True) + "\n")
    return payload


def combine(sample) -> dict[str, Any]:
    """Read every persisted condition and apply the §10.4 hierarchy."""
    loaded = {}
    for path in sorted(COND_DIR.glob("*.json")):
        if path.name.startswith("_"):
            continue          # sidecars (e.g. the cross-device check) are not
                              # conditions and never enter the selection
        payload = json.loads(path.read_text())
        if payload["sample_hash"] != sha_obj(sorted(i["item_id"]
                                                    for i in sample)):
            raise SystemExit(f"{path.name} was judged on a different sample")
        loaded[payload["condition"]] = payload
    if not loaded:
        raise SystemExit("no condition artifacts in " + str(COND_DIR))
    results = {k: {"condition": k, "config": v["config"],
                   "judgments": v["judgments"], "rows": v["rows"],
                   "items": v["replicates"][0]["items"],
                   "status_counts": v["replicates"][0]["status_counts"],
                   "coverage": v["replicates"][0]["coverage"],
                   "truncated": v["replicates"][0]["truncated"],
                   "truncation_rate": v["replicates"][0]["truncation_rate"],
                   "seconds": v["replicates"][0]["seconds"],
                   "seconds_per_item": v["replicates"][0]["seconds_per_item"],
                   "run_dir": v["replicates"][0]["run_dir"]}
               for k, v in loaded.items()}
    repeat = {k: v["repeatability"] for k, v in loaded.items()
              if v["repeatability"]}
    reference = {i["item_id"]: i["verifier_class"] for i in sample}
    names = sorted(results)
    pairs = {}
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            pairs[f"{a} vs {b}"] = autorater.paired_comparison(
                [i["item_id"] for i in sample], results[a]["judgments"],
                results[b]["judgments"], reference)
    sidecars = {}
    for path in sorted(COND_DIR.glob("_*.json")):
        side = json.loads(path.read_text())
        condition = side["condition"]
        primary = loaded.get(condition)
        if primary is None:
            continue
        common = [k for k in side["judgments"] if k in primary["judgments"]]
        prefix = [i["item_id"] for i in sample[:side["items"]]]
        # Agreement over the prefix INCLUDING items that produced no verdict:
        # a device that changed which items reach a verdict would be a device
        # effect too, so non-verdicts are compared rather than dropped.
        agree = sum(1 for k in prefix
                    if side["judgments"].get(k) == primary["judgments"].get(k))
        sidecars[path.stem] = {
            **{k: side[k] for k in ("sidecar", "condition", "device", "items",
                                    "coverage", "truncation_rate",
                                    "config_hash", "note")},
            "compared_against": f"{condition} replicate 0",
            "items_compared": len(prefix),
            "labels_identical": agree,
            "agreement": agree / len(prefix) if prefix else float("nan"),
            "device_is_inert": agree == len(prefix),
            "same_config_hash": side["config_hash"] == primary["config"]["config_hash"],
            "counted_in_selection": False,
        }

    alive = select(results, sample, repeat)["readings"]["threshold"]["surviving"]
    discordant: set[str] = set()
    for i, a in enumerate(sorted(alive)):
        for b in sorted(alive)[i + 1:]:
            for d in pairs[f"{a} vs {b}"]["discordant_items"]:
                discordant.add(d["item_id"])
    by_stratum: dict[str, int] = {}
    index = {i["item_id"]: i for i in sample}
    for item_id in discordant:
        key = stratum(index[item_id])
        by_stratum[key] = by_stratum.get(key, 0) + 1
    criterion_4_set = {
        "conditions_still_alive": sorted(alive),
        "discordant_items": sorted(discordant),
        "n_discordant": len(discordant),
        "by_stratum": by_stratum,
        "matched_control": len(discordant),
        "total_to_label": 2 * len(discordant),
        "estimated_minutes": [round(2 * len(discordant) * 30 / 60),
                              round(2 * len(discordant) * 60 / 60)],
        "rule": ("§10.4's fourth criterion needs only enough paired items to "
                 "separate the surviving conditions. Conditions that never "
                 "disagree cannot be separated by any number of labels, so "
                 "only the discordant items carry information; an equal number "
                 "of concordant controls is added so the sample is not "
                 "conditioned on disagreement."),
        "invariant": ("these are author labels: diagnostic evidence and §10.4 "
                      "hierarchy input, never independent validation"),
    }

    return {"sidecars": sidecars, "criterion_4_annotation_set": criterion_4_set,
            "conditions": {k: {kk: v[kk] for kk in
                               ("condition", "config", "items",
                                "status_counts", "coverage", "truncated",
                                "truncation_rate", "seconds",
                                "seconds_per_item", "run_dir")}
                           for k, v in results.items()},
            "repeatability": repeat,
            "paired_comparisons": pairs,
            "selection": select(results, sample, repeat),
            "judge_rows": {k: v["rows"] for k, v in results.items()}}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--items", type=int, default=48)
    parser.add_argument("--device", type=int, default=0)
    parser.add_argument("--repeat-items", type=int, default=16,
                        help="prefix size for the repeatability check; 0 skips")
    parser.add_argument("--probe", action="store_true",
                        help="one replicate only; timing and truncation")
    parser.add_argument("--conditions", default="")
    parser.add_argument("--combine", action="store_true")
    args = parser.parse_args()

    items = build_items()
    split = split_pool(items)
    sample = subsample(split["development"], args.items)
    print(f"pool {len(items)}  development {len(split['development'])}  "
          f"calibration {len(split['calibration'])}  judging {len(sample)}",
          file=sys.stderr)

    OUT.mkdir(parents=True, exist_ok=True)
    if not args.combine:
        for condition in [c for c in args.conditions.split(",") if c]:
            result = emit_condition(
                condition, sample, device=args.device,
                repeat_items=0 if args.probe else args.repeat_items)
            first = result["replicates"][0]
            print(f"{condition}: {first['seconds']}s "
                  f"({first['seconds_per_item']}s/item) coverage "
                  f"{first['coverage']:.3f} truncation "
                  f"{first['truncation_rate']:.3f}", file=sys.stderr)
        return 0

    combined = combine(sample)
    payload = {
        "artifact": ("§10.4 autorater pathway, development phase, A and B "
                     "classes"),
        "classification": ("Gate 1 input evidence. Gate 1 is NOT approved. The "
                           "single-shot freeze and the one-shot calibration are "
                           "deliberately NOT claimed."),
        "not_claimed": {
            "autorater_freeze": "single-shot; not claimed",
            "autorater_calibration": "one-shot; not claimed",
            "reason": ("both bind the canonical verifier hash, and Amendment C "
                       "would change it by changing FOCAL_GRID, which is inside "
                       "the §10.6 semantic module set. Spending a one-shot on a "
                       "hash that is likely to be superseded would require an "
                       "explicit invalidation to recover."),
            "held_out_half": ("derived and hashed, never judged; it stays "
                              "untouched for the real one-shot calibration"),
        },
        "canonical_verifier_hash": verifier_source_hash(),
        "prompts": {k: {"version": k, "hash": sha_text(v)}
                    for k, v in JUDGE_PROMPTS.items()},
        "pool": {
            "items": len(items),
            "source": "the registered §12.2 dense ladder screen, read only",
            "instruments": {"A": sum(1 for i in items if i["instrument"] == "A"),
                            "B": sum(1 for i in items if i["instrument"] == "B")},
            "strata": dict(split["per_stratum"]),
            "split_hash": split["split_hash"],
            "development": len(split["development"]),
            "calibration": len(split["calibration"]),
            "disjoint": True,
        },
        "judged_subsample": {
            "n": len(sample), "stratum_balanced": True,
            "derivation": ("deterministic round-robin over strata in item-id "
                           "order across the development half"),
            "hash": sha_obj(sorted(i["item_id"] for i in sample)),
            "strata": {s: sum(1 for i in sample if stratum(i) == s)
                       for s in sorted({stratum(i) for i in sample})},
        },
        **combined,
    }
    (OUT / "section_10_4_development.json").write_text(
        json.dumps(payload, indent=1, sort_keys=True) + "\n")
    print(json.dumps({
        "conditions": {k: {"coverage": v["coverage"],
                           "truncation_rate": v["truncation_rate"],
                           "seconds_per_item": v["seconds_per_item"]}
                       for k, v in payload["conditions"].items()},
        "repeatability": {k: v["exactly_repeatable"]
                          for k, v in payload["repeatability"].items()},
        "selection_steps": [{s["criterion"]: s["surviving"]}
                            for s in payload["selection"]["steps"]],
        "surviving": payload["selection"]["surviving_after_criteria_1_to_3"],
    }, indent=1))
    print("written: reports/gate1_v4/section_10_4_development.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
