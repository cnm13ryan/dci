"""E3.2 — prompt-rendering identity check (CPU only, no generation).

Run with the BACKEND venv (it owns the tokenizer stack):

    HF_HUB_OFFLINE=1 dci1/environments/backend/.venv/bin/python \
        experiments/exp3_path/compare_prompts.py [port]

For every control sample and every effort, compares:
  offline: tokenizer.apply_chat_template([user], tokenize=True,
           add_generation_prompt=True, reasoning_effort=e)
           (exactly `render_prompt` in exploratory/vllm_backend/engine.py)
  server:  POST /tokenize with the identical conversation and
           chat_template_kwargs (the serving layer's own rendering,
           which chat completions share).

Writes analysis/out/exp3_prompt_identity.json and prints a summary.
Token-ID identity here excludes chat-template rendering as a cause of
path divergence.
"""
import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REVISION = "6cee5e81ee83917806bbde320786a8fb61efebee"
EFFORTS = ("low", "medium", "high")


def server_tokenize(port: int, prompt: str, effort: str):
    body = json.dumps({
        "model": "gpt-oss-20b",
        "messages": [{"role": "user", "content": prompt}],
        "add_generation_prompt": True,
        "chat_template_kwargs": {"reasoning_effort": effort},
    }).encode()
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/tokenize", data=body,
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())["tokens"]


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8555
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained("openai/gpt-oss-20b",
                                        revision=REVISION)
    controls = [json.loads(l) for l in
                (ROOT / "dataset" / "diagnostic.jsonl").read_text()
                .splitlines()]
    controls = [r for r in controls if not r["contested"]]
    out = {"port": port, "revision": REVISION, "samples": {}}
    mismatches = 0
    for r in controls:
        per = {}
        for e in EFFORTS:
            offline_ids = tok.apply_chat_template(
                [{"role": "user", "content": r["input"]}],
                tokenize=True, add_generation_prompt=True,
                reasoning_effort=e)
            server_ids = server_tokenize(port, r["input"], e)
            same = list(offline_ids) == list(server_ids)
            per[e] = {"identical": same,
                      "offline_len": len(offline_ids),
                      "server_len": len(server_ids)}
            if not same:
                mismatches += 1
                # keep the first divergence point for diagnosis
                i = next((k for k, (a, b) in
                          enumerate(zip(offline_ids, server_ids))
                          if a != b), min(len(offline_ids),
                                          len(server_ids)))
                per[e]["first_divergence_index"] = i
                per[e]["offline_around"] = tok.decode(
                    offline_ids[max(0, i - 5):i + 5])
                per[e]["server_around"] = tok.decode(
                    server_ids[max(0, i - 5):i + 5])
        out["samples"][r["id"]] = per
    out["summary"] = {
        "controls": len(controls),
        "comparisons": len(controls) * len(EFFORTS),
        "mismatches": mismatches,
    }
    dest = ROOT / "analysis" / "out" / "exp3_prompt_identity.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, indent=1))
    print(json.dumps(out["summary"]))


if __name__ == "__main__":
    main()
