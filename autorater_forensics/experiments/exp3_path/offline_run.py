"""E3.3 — run the REGISTERED offline execution path on the 61 controls.

Run with the dci1 venv (imports dci1v3 READ-ONLY; all outputs go to
experiments/scratch/, never the evidence tree):

    dci1/.venv/bin/python experiments/exp3_path/offline_run.py \
        --effort high --chunk 32 --device 0

This is the same seam the registered rounds used: identical plan
construction (backend_plan + judge registry spec + chat_template_kwargs
override), identical subprocess boundary (run_backend -> backend venv
`python -m vllm_backend`), identical prompt builder (judge_prompt), and
the registered parser (parse_judgment). Only the item set (61 controls
instead of a full development round) and, when --chunk 1, the chunk
size differ — which is exactly the factor under test.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT.parent
sys.path.insert(0, str(REPO / "dci1" / "src"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--effort", required=True,
                    choices=["low", "medium", "high"])
    ap.add_argument("--chunk", type=int, default=32)
    ap.add_argument("--device", type=int, default=0)
    ap.add_argument("--cap", type=int, default=2048)
    ap.add_argument("--dataset", default=None,
                    help="alternate sample JSONL (default: the 61 "
                         "controls from diagnostic.jsonl)")
    args = ap.parse_args()

    from dci1v3.generation.backend import run_backend
    from dci1v3.generation.plans import backend_plan
    from dci1v3.models.registry import get_judge
    from dci1v3.protocol import constants as C
    from dci1v3.protocol.hashing import sha_text
    from dci1v3.protocol.seeds import domain_int
    from dci1v3.stages.autorater import judge_prompt, parse_judgment

    config = json.loads(
        (REPO / "dci1" / "src" / "dci1v3" / "protocol" / "data"
         / "autorater.json").read_text())
    judge = get_judge(config["judge_model_key"])
    # The registered plan builder only accepts registered caps; for the
    # diagnostic cap search we build at the registered AUTORATER_CAP and
    # override ONLY the cap fields (the parameter under test). Scratch
    # output only — never a registered run.
    build_cap = args.cap if args.cap in (2048,) else 2048
    plan = backend_plan(
        judge, cap=build_cap, decoding="greedy",
        chunk_size=args.chunk,
        skip_special_tokens=bool(
            config["decoding"].get("skip_special_tokens", True)))
    if args.cap != build_cap:
        plan["generation_ceiling"] = args.cap
        plan["answer_tokens"] = args.cap
        if plan["max_model_len"] < args.cap + 1024:
            plan["max_model_len"] = args.cap + 1024
    plan["chat_template_kwargs"] = {"reasoning_effort": args.effort}

    if args.dataset:
        controls = [json.loads(l) for l in
                    Path(args.dataset).read_text().splitlines()]
    else:
        controls = [json.loads(l) for l in
                    (ROOT / "dataset" / "diagnostic.jsonl").read_text()
                    .splitlines()]
        controls = [r for r in controls if not r["contested"]]
    design_rows = []
    for r in sorted(controls, key=lambda r: r["item_id"]):
        item = {"constraint_text": r["constraint_text"],
                "response_text": r["response_text"]}
        prompt = judge_prompt(config, item)
        design_rows.append({
            "row_id": f"judge:{r['item_id']}",
            "user_prompt": prompt,
            "scientific_seed": domain_int(
                C.DOMAIN_AUTORATER_SEED, C.AUTORATER_SPLIT_SEED,
                judge.model_id, sha_text(prompt)),
            "item_id": r["item_id"],
            "sample_id": r["id"],
            "prompt_hash": sha_text(prompt)})

    tag = (f"_{Path(args.dataset).stem}" if args.dataset else "")
    run_dir = (ROOT / "experiments" / "scratch" / "exp3"
               / f"offline_{args.effort}_chunk{args.chunk}"
                 f"_cap{args.cap}{tag}")
    outcome = run_backend(run_dir, plan, design_rows,
                          device=args.device)
    by_id = {row["row_id"]: row for row in outcome["rows"]}
    judgments = []
    for design in design_rows:
        raw = by_id.get(design["row_id"])
        if raw is None or raw.get("outcome") != "OK":
            judgments.append({"sample_id": design["sample_id"],
                              "item_id": design["item_id"],
                              "status": "generation_failure",
                              "label": None, "raw_generation": None})
            continue
        status, label, justification = parse_judgment(
            raw["raw_generation"])
        judgments.append({
            "sample_id": design["sample_id"],
            "item_id": design["item_id"],
            "status": status, "label": label,
            "justification": justification,
            "finish_reason": raw.get("finish_reason", ""),
            "raw_generation": raw["raw_generation"]})
    dest = run_dir / "judgments.jsonl"
    dest.write_text("".join(
        json.dumps(j, ensure_ascii=False) + "\n" for j in judgments))
    ok = sum(1 for j in judgments if j["status"] == "valid")
    print(f"{dest}: {len(judgments)} judgments, {ok} valid, "
          f"effort={args.effort} chunk={args.chunk} cap={args.cap}")


if __name__ == "__main__":
    main()
