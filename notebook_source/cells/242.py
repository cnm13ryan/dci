# ---------------------------------------------------------------- snapshot 1
# Before anything runs: the declared design at each allowed escalation, and the
# ceiling the escalation rule permits. Nominal by construction.
_esc = {}
for _p in CFG.paraphrase_schedule:
    _proj = generation_budget(len(CANDIDATE_IDS), _p, SECONDS_PER_GENERATION)
    _esc[_p] = int(_proj["generations"].sum())
record_budget(
    "1_declared_design",
    f"declared candidate pool ({len(CANDIDATE_IDS)}), paraphrase schedule "
    f"{list(CFG.paraphrase_schedule)}, nominal U split and pseudo-focal sets",
    realised=False,
    generations={f"schedule_P{_p}": _esc[_p] for _p in CFG.paraphrase_schedule},
    seconds_per_generation=SECONDS_PER_GENERATION,
    notes=(f"best case stops at P={min(CFG.paraphrase_schedule)} "
           f"({_esc[min(CFG.paraphrase_schedule)]} generations); worst allowed case runs to "
           f"P={max(CFG.paraphrase_schedule)} ({_esc[max(CFG.paraphrase_schedule)]}). The schedule is "
           "frozen at 4->6 for the workshop, so there is no 8 or 10 to cost."))
display(budget_frame().T)

RUN_BENCHMARK = True

RUNTIME_PROJECTION: dict[str, Any] = {}
if RUN_BENCHMARK:
    with phase("benchmark"):
        _bench_design = build_benchmark_design(CFG.benchmark_prompts)
        _started = time.perf_counter()
        _bench = run_generation_stage(_bench_design, "benchmark")
        _elapsed = time.perf_counter() - _started

    _profile = batch_profile_summary("benchmark")
    _gen_seconds = float(_profile.get("generate_seconds", pd.Series([np.nan])).iloc[0])
    _rows = int(_profile.get("rows", pd.Series([len(_bench)])).iloc[0]) or len(_bench)
    _measured = (_gen_seconds / _rows if np.isfinite(_gen_seconds) and _gen_seconds > 0
                 else _elapsed / max(_rows, 1))
    _latencies = [r.get("wall_seconds", np.nan) / max(r.get("batch_size", 1), 1)
                  for r in load_jsonl(RUN_ROOT / "benchmark_batch_profile.jsonl")
                  if r.get("run_attempt_id") == RUN_ATTEMPT_ID]
    _latencies = [x for x in _latencies if np.isfinite(x)]

    SECONDS_PER_GENERATION = float(_measured) if _measured > 0 else SECONDS_PER_GENERATION
    _projected = generation_budget(len(CANDIDATE_IDS), min(CFG.paraphrase_schedule),
                                   SECONDS_PER_GENERATION)

    RUNTIME_PROJECTION = {
        "model_profile": CFG.model_profile, "model_id": CFG.model_id,
        "dry_run": CFG.dry_run,
        "measured": not CFG.dry_run,
        "gpu": HARDWARE.get("gpu_name"),
        "batch_size": CFG.initial_batch_size,
        "prompts": _rows,
        "seconds_per_generation": SECONDS_PER_GENERATION,
        "prompts_per_second": 1.0 / SECONDS_PER_GENERATION if SECONDS_PER_GENERATION else None,
        "output_tokens_per_second": float(
            _profile.get("output_tokens_per_second", pd.Series([np.nan])).iloc[0]),
        "latency_seconds_p50": float(np.quantile(_latencies, 0.50)) if _latencies else None,
        "latency_seconds_p90": float(np.quantile(_latencies, 0.90)) if _latencies else None,
        "peak_gpu_memory_gb": (round(torch.cuda.max_memory_reserved() / 2**30, 2)
                               if torch.cuda.is_available() else None),
        "stage_hours": _projected.set_index("stage")["hours"].round(3).to_dict(),
        "pre_freeze_hours": round(float(_projected.attrs["pre_freeze_hours"]), 2),
        "total_hours": round(float(_projected["hours"].sum()), 2),
    }
    durable_write(RUN_ROOT / "runtime_projection.json",
                  json.dumps(RUNTIME_PROJECTION, indent=2, default=str))
    display(_projected.round(2))
    print(f"""
Runtime projection for profile '{CFG.model_profile}'
  measured seconds per generation : {SECONDS_PER_GENERATION:.3f}
  through Gate 3b                 : {RUNTIME_PROJECTION['pre_freeze_hours']:.1f} h
  whole study                     : {RUNTIME_PROJECTION['total_hours']:.1f} h
""")
    if CFG.dry_run:
        print("DRY RUN: these timings come from the synthetic oracle and measure "
              "the harness, not the model. Rerun with DRY_RUN_MODE = False on the "
              "target hardware before making a GPU decision.")
    checkpoint("benchmark", RUNTIME_PROJECTION)
