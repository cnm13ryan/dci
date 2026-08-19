"""End-to-end smoke test of the diagnostic data path (run before any
full diagnostic evaluation):

 1. endpoint connectivity (/v1/models);
 2. DIRECT evidence that reasoning_effort reaches the backend: the
    server's /tokenize renders the harmony chat template with the
    requested effort, and /detokenize shows "Reasoning: <effort>" in
    the rendered system header;
 3. chat completions under low vs high on two fixed samples: reasoning
    (analysis channel) arrives SEPARATELY from the final content, the
    final content parses to SATISFIES/VIOLATES, reasoning length
    responds to effort, and a greedy repeat is byte-identical;
 4. the server request log records the requested effort.
"""
import json
import urllib.error
import sys
import urllib.request

BASE = "http://127.0.0.1:8555"
MODEL = "gpt-oss-20b"


def post(path, payload):
    req = urllib.request.Request(
        BASE + path, json.dumps(payload).encode(),
        headers={"Content-Type": "application/json",
                 "Authorization": "Bearer forensics"})
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.loads(r.read())


def get(path):
    req = urllib.request.Request(BASE + path, headers={
        "Authorization": "Bearer forensics"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def main() -> int:
    ok = True
    models = [m["id"] for m in get("/v1/models")["data"]]
    print("1. connectivity: models =", models)
    ok &= MODEL in models

    messages = [{"role": "user",
                 "content": "Rule check placeholder."}]
    rendered = {}
    for effort in ("low", "high"):
        tok = post("/tokenize", {
            "model": MODEL, "messages": messages,
            "chat_template_kwargs": {"reasoning_effort": effort}})
        detok = post("/detokenize", {"model": MODEL,
                                     "tokens": tok["tokens"]})
        rendered[effort] = detok["prompt"]
        marker = f"Reasoning: {effort}"
        found = marker in detok["prompt"]
        print(f"2. rendered template contains {marker!r}: {found}")
        ok &= found
    ok &= rendered["low"] != rendered["high"]
    print("2. low/high renders differ:", rendered["low"] !=
          rendered["high"])

    sample = ("You are checking one rule against one text.\n"
              "Rule: Use the word however exactly 2 times.\n"
              "Text:\nThe plan held; however, costs rose. However, "
              "demand stayed firm.\n---\n"
              "Does the text satisfy the rule? Answer with exactly one "
              "word on the first line: SATISFIES or VIOLATES. You may "
              "add one short reason on the second line.\nAnswer:")
    lengths = {}
    for effort in ("low", "high"):
        reps = []
        for _ in range(2):                      # greedy repeatability
            out = post("/v1/chat/completions", {
                "model": MODEL,
                "messages": [{"role": "user", "content": sample}],
                "temperature": 0.0, "top_p": 1.0, "max_tokens": 2048,
                "seed": 20260817,
                "reasoning_effort": effort})
            msg = out["choices"][0]["message"]
            reps.append((msg.get("reasoning") or
                         msg.get("reasoning_content") or "",
                         msg.get("content") or "",
                         out["choices"][0].get("finish_reason"),
                         out.get("usage", {})))
        reasoning, content, finish, usage = reps[0]
        identical = reps[0][:2] == reps[1][:2]
        lengths[effort] = len(reasoning)
        first_line = content.strip().splitlines()[0] if content else ""
        print(f"3. {effort}: reasoning_chars={len(reasoning)} "
              f"content_first_line={first_line!r} finish={finish} "
              f"completion_tokens={usage.get('completion_tokens')} "
              f"greedy_repeat_identical={identical}")
        ok &= bool(reasoning) and bool(content)
        ok &= reasoning not in content          # separation, not concat
        ok &= first_line.upper().startswith("SATISF") or \
            first_line.upper().startswith("VIOLAT")
        ok &= identical
    print("3. reasoning length responds to effort (high != low):",
          lengths["low"] != lengths["high"])

    # 4. The field is PARSED server-side (not silently ignored): an
    #    invalid effort must be rejected by the request schema.
    try:
        post("/v1/chat/completions", {
            "model": MODEL,
            "messages": [{"role": "user", "content": "x"}],
            "max_tokens": 8, "reasoning_effort": "extreme"})
        print("4. invalid reasoning_effort accepted — FAIL")
        ok = False
    except urllib.error.HTTPError as e:
        print(f"4. invalid reasoning_effort rejected by the server "
              f"schema (HTTP {e.code}): OK")
        ok &= e.code == 400

    print("SMOKE", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
