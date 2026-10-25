"""Throwaway vLLM throughput benchmark for the Batch 1 decoding settings.

Not protocol code and never evidence: synthetic prompts (no pilot or reserved
topics), no run root. Measures rows/s and generated tokens/s for one model at
one (enforce_eager, chunk_size) setting, with the pilot's decoding values, and
reports finish reasons, truncation and empty answers. With REPEAT > 1 the same
prompts are generated again in the same engine and the texts compared.
Usage: python bench_throughput.py MODEL_ID REVISION GPU_MEM_UTIL EAGER(0|1) CHUNK N [REPEAT [TEXTS_OUT]]
CHUNK 0 means all N prompts in one call. Prints one line: RESULT <json>.
Peak memory and utilisation come from nvidia-smi over [start, end]: the engine
runs in its own process, so this process's torch counters would read ~0.
"""
import collections
import hashlib
import json
import sys
import time

SUBJECTS = ["rivers", "bridges", "libraries", "bicycles", "bakeries", "tides",
            "orchards", "trains", "glaciers", "markets", "violins", "deserts",
            "lanterns", "harbours", "beehives", "printing presses"]


def main():
    from vllm import LLM, SamplingParams

    model, revision, mem = sys.argv[1:4]
    eager, n = bool(int(sys.argv[4])), int(sys.argv[6])
    chunk = int(sys.argv[5]) or n
    repeat = int(sys.argv[7]) if len(sys.argv) > 7 else 1
    t_start = time.strftime("%Y/%m/%d %H:%M:%S", time.gmtime())

    prompts = [[{"role": "user", "content":
                 f"In 60 to 120 words, explain one interesting fact about "
                 f"{SUBJECTS[i % len(SUBJECTS)]} (variant {i})."}]
               for i in range(n)]
    params = [SamplingParams(temperature=0.7, top_p=0.9, top_k=50,
                             max_tokens=512, seed=1000 + i) for i in range(n)]
    kwargs = {"chat_template_kwargs": {"enable_thinking": False}} \
        if model == "Qwen/Qwen3-4B" else {}
    base = {"model": model, "eager": eager, "chunk": chunk, "rows": n,
            "start": t_start}

    t0 = time.perf_counter()
    try:
        llm = LLM(model=model, revision=revision, dtype="bfloat16",
                  max_model_len=4096, gpu_memory_utilization=float(mem),
                  enforce_eager=eager, disable_custom_all_reduce=True,
                  seed=20261018, trust_remote_code=False)
    except Exception as exc:  # a setting that cannot load is a result
        print("RESULT " + json.dumps(
            {**base, "load_error": f"{type(exc).__name__}: {exc}"[:300]}),
            flush=True)
        return
    load = time.perf_counter() - t0

    def run():
        texts, finish, tokens = [], collections.Counter(), 0
        t = time.perf_counter()
        for s in range(0, n, chunk):
            for o in llm.chat(prompts[s:s + chunk], params[s:s + chunk],
                              use_tqdm=False, **kwargs):
                c = o.outputs[0]
                texts.append(c.text)
                finish[c.finish_reason] += 1
                tokens += len(c.token_ids)
        return texts, finish, tokens, time.perf_counter() - t

    texts, finish, tokens, gen = run()
    out = {**base, "load_s": round(load, 1), "gen_s": round(gen, 1),
           "rows_per_s": round(n / gen, 2), "tok_per_s": round(tokens / gen),
           "mean_tokens": round(tokens / n, 1), "finish": dict(finish),
           "truncated": finish.get("length", 0),
           "empty": sum(1 for x in texts if not x.strip()),
           "texts_sha256": hashlib.sha256(
               "\x00".join(texts).encode()).hexdigest()[:16]}
    for _ in range(repeat - 1):
        again = run()[0]
        out.setdefault("repeat_identical", []).append(
            sum(a == b for a, b in zip(texts, again)))
    if len(sys.argv) > 8:  # save texts so two separate processes can be compared
        with open(sys.argv[8], "w") as f:
            json.dump(texts, f)
    out["end"] = time.strftime("%Y/%m/%d %H:%M:%S", time.gmtime())
    print("RESULT " + json.dumps(out), flush=True)


if __name__ == "__main__":
    main()
