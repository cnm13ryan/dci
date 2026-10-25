"""Pilot execution: the adapter over the shared vLLM seam, resume, and the
authorisation gate.

The seam is ``exploratory/vllm_backend`` (``plan.json`` + ``design.jsonl``
in, ``rows.jsonl`` out), executed by a separate pinned interpreter. Nothing
scientific crosses it: it receives prompt text and a seed and returns text,
token counts and a finish reason. This module writes the seam's existing
schema (the fields ``dci1v4/generation/backend.py::build_plan`` writes) and
does not import any DCI-1 package.

**Two namespaces, never mixed.** A run root is created either ``real`` or
``synthetic`` and says so in ``RUN.json``. Real generation needs an
authorised Freeze 1 (``freeze.assert_authorized``), including a live check
of the execution environment against the attested lock, and refuses a
stand-in generator; synthetic generation refuses the real backend.

**Before anything is generated** every requested row is authenticated
against the frozen design (``evidence.authenticate_design``): the prompt,
seed, identity and instruction count are recomputed, not read from labels.

**What is kept.** Each returned row is classified (``outcomes``). VALID and
EMPTY rows are behavioural evidence and are appended to ``rows.jsonl``.
TECHNICAL rows, and requested rows the backend never returned, go to
``rejected.jsonl`` with their attempt number and never become evidence; the
request stays open. A blocked engine (exit code 2, or a ``blocked``, missing
or unreadable provenance sidecar --- the condition v8.1's
``reusable_rows_checked`` exists for) has every row rejected and the step
fails. A crashed backend (exit code 3, or a timeout) keeps the complete
VALID/EMPTY rows it wrote before the crash, rejects the rest, and the step
fails; ``resume`` continues from there.

**Per attempt.** Each backend run gets its own directory
(``attempts/NNN``: plan, design and backend log), and a ``provenance.jsonl``
event naming the generator (the seam or the stand-in, set by the runner) and
the live environment identity it ran under; Freeze 2 binds both. A real
row must carry the seam's full schema (``outcomes.SEAM_ROW_KEYS``). A row
whose own outcome was TECHNICAL ``max_technical_attempts`` times is not sent
again: the stage stays incomplete and the run says so.

**Resume** sends only rows without an accepted generation. A stored row
whose identity differs from the design, a conflicting duplicate, or a
non-evidence row in ``rows.jsonl`` is refused. An identical duplicate
collapses (``store.index_rows``). An unterminated final line left by a
crash is removed and recorded. A lock (``store.run_lock``) refuses a second
process on the same root.

**GPU selection** is a parameter: ``HIP_VISIBLE_DEVICES`` on the ROCm
workstation, ``CUDA_VISIBLE_DEVICES`` on an NVIDIA host. Inherited
visibility variables are cleared first.

**One worker per GPU** (D12, 2026-10-25). ``execute(devices=(0, 1))`` runs
the ``(stage, model)`` groups on one worker per listed device, each group a
seam subprocess that sees only its own device; a worker takes the next
group when it is free. Tensor parallelism stays as configured (1), the
engine arguments are the seam plan's, and the root lock, the design
authentication and the live environment check stay in this process. Groups
write disjoint directories, and each backend run records its device.
"""
from __future__ import annotations

import json
import os
import queue
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from dci.batch1 import config as CFG
from dci.batch1 import environment as ENV
from dci.batch1 import evidence as EV
from dci.batch1 import freeze as F
from dci.batch1 import outcomes as OUT
from dci.batch1.store import (
    RunError, append_jsonl, index_rows, read_jsonl, record_hash,
    repair_partial_tail, run_lock,
)

__all__ = ["BackendSpec", "seam_plan", "seam_design_rows", "subprocess_backend",
           "init_root", "execute", "check_visibility", "read_rows",
           "GenerateFn", "RunError",
           "OK_EXITS", "BLOCKED_EXIT", "CRASH_EXIT", "SEAM_GENERATOR",
           "SYNTHETIC_GENERATOR"]

GenerateFn = Callable[[Path, dict[str, Any], list[dict[str, Any]]],
                      dict[str, Any]]

#: The seam's exit codes (``exploratory/vllm_backend/__main__.py``): 0 done,
#: 1 done with a ceiling hit (any truncated answer under NO_THINKING),
#: 2 engine blocked, 3 crashed.
OK_EXITS = (0, 1)
BLOCKED_EXIT, CRASH_EXIT = 2, 3
#: How each backend run is recorded in ``provenance.jsonl``. The runner, not
#: the backend, writes it: a real root accepts only the seam, and Freeze 2
#: checks every recorded run against the root's namespace.
SEAM_GENERATOR, SYNTHETIC_GENERATOR = EV.SEAM_GENERATOR, EV.SYNTHETIC_GENERATOR

_REPO = Path(__file__).resolve().parents[3]
_VISIBILITY = ("ROCR_VISIBLE_DEVICES", "HIP_VISIBLE_DEVICES",
               "CUDA_VISIBLE_DEVICES")


@dataclass(frozen=True)
class BackendSpec:
    python: str = str(_REPO / "dci1/environments/backend/.venv/bin/python")
    cwd: str = str(_REPO / "exploratory")
    visibility_var: str = "HIP_VISIBLE_DEVICES"
    device: int = 0
    timeout_seconds: float = 12 * 3600

    def env(self) -> dict[str, str]:
        if self.visibility_var not in ("HIP_VISIBLE_DEVICES",
                                       "CUDA_VISIBLE_DEVICES"):
            raise RunError(f"visibility variable {self.visibility_var!r}")
        # Inherited vLLM settings never reach the seam (third audit C5):
        # the engine's behaviour is the plan's, so "batch invariance off" and
        # the attention backend hold by construction, not by default.
        env = {k: v for k, v in os.environ.items()
               if k not in _VISIBILITY and not k.startswith("VLLM_")}
        env[self.visibility_var] = str(self.device)
        env["VLLM_WORKER_MULTIPROC_METHOD"] = "spawn"
        env["HF_HUB_OFFLINE"] = env.get("HF_HUB_OFFLINE", "1")
        return env


def seam_plan(model: CFG.ModelConfig, stage: str) -> dict[str, Any]:
    d = CFG.DECODING
    return {
        "model_id": model.model_id, "model_revision": model.revision,
        "model_family": model.family, "dtype": model.dtype,
        "quantization": "none",
        "tensor_parallel_size": model.tensor_parallel_size,
        "gpu_memory_utilization": model.gpu_memory_utilization,
        "disable_custom_all_reduce": True, "enforce_eager": True,
        "cpu_offload_gb": 0.0, "max_model_len": model.max_model_len,
        "engine_seed": d["engine_seed"], "trust_remote_code": False,
        "limit_mm_per_prompt": None, "temperature": d["temperature"],
        "top_p": d["top_p"], "top_k": d["top_k"],
        "generation_ceiling": d["max_new_tokens"],
        "answer_tokens": d["max_new_tokens"], "chunk_size": d["chunk_size"],
        "deadline_seconds": None, "strategy": "single_phase",
        "reasoning_mode": d["reasoning_mode"],
        "chat_template_kwargs": dict(model.chat_template_kwargs),
        "reasoning_parser": None, "think_open": "", "think_close": "",
        "decoding_policy": "stochastic",
        "skip_special_tokens": d["skip_special_tokens"],
        "thinking_policy": model.thinking_policy, "stage": f"batch1:{stage}",
    }


_SEAM_IDENTITY = ("identity_hash", "cell_id", "stage", "model", "frame",
                  "condition", "topic_id", "draw", "protocol_hash")


def seam_design_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [{"row_id": r["row_id"], "user_prompt": r["user_prompt"],
             "system_message": "", "scientific_seed": r["scientific_seed"],
             "answer_seed": 0, **{k: r[k] for k in _SEAM_IDENTITY}}
            for r in rows]


def _read_backend_rows(path: Path) -> list[dict[str, Any]]:
    """The seam's output, tolerating only a partial final line (a crash)."""
    rows = []
    lines = path.read_text(encoding="utf-8").splitlines()
    for i, line in enumerate(lines):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except ValueError:
            if i == len(lines) - 1:
                break
            raise RunError(f"{path}:{i + 1}: unreadable backend row") from None
    return rows


def subprocess_backend(spec: BackendSpec) -> GenerateFn:
    def generate(run_dir: Path, plan: dict[str, Any],
                 design_rows: list[dict[str, Any]]) -> dict[str, Any]:
        if not Path(spec.python).exists():
            raise RunError(f"backend interpreter missing: {spec.python}")
        run_dir.mkdir(parents=True, exist_ok=True)
        plan = dict(plan, expected_rows=len(design_rows))
        plan_path, design_path = run_dir / "plan.json", run_dir / "design.jsonl"
        out_path = run_dir / "backend_rows.jsonl"
        prov_path = out_path.with_name(out_path.stem + "_engine.json")
        for stale in (out_path, prov_path):
            if stale.exists():
                stale.unlink()
        F.write_json(plan_path, plan)
        design_path.write_text("".join(json.dumps(r, sort_keys=True) + "\n"
                                       for r in design_rows))
        started = time.time()
        with (run_dir / "backend.log").open("w") as log:
            try:
                proc = subprocess.run(
                    [spec.python, "-u", "-m", "vllm_backend", "--plan",
                     str(plan_path), "--design", str(design_path), "--out",
                     str(out_path), "--chunk-size", str(plan["chunk_size"])],
                    cwd=spec.cwd, env=spec.env(), stdout=log,
                    stderr=subprocess.STDOUT, timeout=spec.timeout_seconds)
                returncode = proc.returncode
            except subprocess.TimeoutExpired:
                returncode = CRASH_EXIT
        rows = _read_backend_rows(out_path) if out_path.exists() else []
        if out_path.exists():
            out_path.unlink()
        if prov_path.exists():
            try:
                provenance = json.loads(prov_path.read_text())
            except ValueError:
                provenance = {"blocked": True,
                              "detail": "provenance sidecar unreadable"}
        elif returncode in OK_EXITS:
            # The seam always writes its sidecar on a normal exit; without it
            # nothing attests that these rows were generated.
            provenance = {"blocked": True,
                          "detail": "provenance sidecar missing"}
        else:
            provenance = {}
        provenance["wall_seconds"] = round(time.time() - started, 1)
        return {"rows": rows, "provenance": provenance,
                "returncode": returncode, "log": str(run_dir / "backend.log"),
                "generator": SEAM_GENERATOR}
    return generate


def read_rows(path: Path) -> list[dict[str, Any]]:
    return read_jsonl(path)


def init_root(root: Path, *, synthetic: bool, freeze1_hash: str,
              namespace: str | None = None) -> dict[str, Any]:
    root = Path(root)
    marker = root / "RUN.json"
    state = {"schema": "dci.batch1/run/v1", "study_id": CFG.STUDY_ID,
             "namespace": namespace or ("synthetic" if synthetic else "real"),
             "freeze1_hash": freeze1_hash}
    if marker.exists():
        existing = F.read_json(marker)
        if existing != state:
            raise RunError(f"{root} belongs to another run: {existing}")
        return existing
    F.write_json(marker, state)
    return state


def _attempt_number(prov_path: Path) -> int:
    """One more than the attempts this group has made: recorded backend runs
    or attempt directories, whichever is more, so an attempt killed before
    its ``backend_run`` event never has its log overwritten (third audit
    C6c)."""
    recorded = sum(e.get("event") == "backend_run"
                   for e in read_jsonl(prov_path))
    made = [int(p.name) for p in (prov_path.parent / "attempts").glob("[0-9]*")
            if p.is_dir() and p.name.isdigit()]
    return 1 + max(recorded, max(made, default=0))


def _technical_failures(rejected_path: Path) -> dict[str, int]:
    """Per row, how many attempts ended in a TECHNICAL outcome of the row
    itself (blocked or crashed runs are failures of the run, not the row)."""
    counts: dict[str, int] = {}
    for r in read_jsonl(rejected_path):
        if str(r.get("reason", "")).startswith(OUT.TECHNICAL + ":"):
            counts[r["row_id"]] = counts.get(r["row_id"], 0) + 1
    return counts


def _blocked_detail(provenance: Mapping[str, Any]) -> str:
    for key in ("detail", "outcome", "engine_error"):
        if provenance.get(key):
            return str(provenance[key])[:200]
    return ""


def _run_group(root: Path, stage: str, model_key: str,
               rows: list[Mapping[str, Any]], generate: GenerateFn,
               expected: Mapping[str, Mapping[str, Any]], *,
               generator: str, environment_identity_hash: str | None,
               max_technical_attempts: int,
               device: int | None = None) -> dict[str, Any]:
    run_dir = Path(root) / "generation" / stage / model_key
    rows_path, rejected_path = run_dir / "rows.jsonl", run_dir / "rejected.jsonl"
    prov_path = run_dir / "provenance.jsonl"
    repaired = repair_partial_tail(rows_path)
    if repaired:
        append_jsonl(prov_path, [{"event": "repaired_partial_line", **repaired}])
    have, repeats = index_rows(read_jsonl(rows_path), what=str(rows_path))
    for rid, r in have.items():
        want = expected.get(rid)
        if want is None:
            raise RunError(f"{rid}: stored in {rows_path} but not a row of the "
                           "frozen design")
        if r.get("identity_hash") != want["identity_hash"]:
            raise RunError(f"{rid}: stored under a different identity; "
                           "it belongs to another protocol")
        cls = OUT.classify(r)
        if not cls.behavioural:
            raise RunError(f"{rid}: {rows_path} holds a non-evidence row "
                           f"({cls.reason}); this runner never writes one, "
                           "so it is refused")
    failures = _technical_failures(rejected_path)
    exhausted = sorted(r["row_id"] for r in rows if r["row_id"] not in have
                       and failures.get(r["row_id"], 0) >= max_technical_attempts)
    missing = [r for r in rows
               if r["row_id"] not in have and r["row_id"] not in exhausted]
    group = {"stage": stage, "model": model_key, "planned": len(rows),
             "reused": sum(r["row_id"] in have for r in rows),
             "accepted_now": 0,
             "rejected_now": 0, "repeats_collapsed": repeats,
             "returncode": None, "open": len(exhausted),
             "exhausted": exhausted}
    if not missing:
        return group
    attempt = _attempt_number(prov_path)
    # One directory per attempt, so a crashed attempt's log, plan and design
    # survive the resume that follows it (re-audit R4.3).
    attempt_dir = run_dir / "attempts" / f"{attempt:03d}"
    out = generate(attempt_dir, seam_plan(CFG.MODEL_BY_KEY[model_key], stage),
                   seam_design_rows(missing))
    returncode = out.get("returncode", 0)
    provenance = dict(out.get("provenance") or {})
    produced, _ = index_rows(out["rows"], what="backend output")
    requested = {r["row_id"]: r for r in missing}
    unknown = set(produced) - set(requested)
    if unknown:
        raise RunError(f"backend returned rows not requested: "
                       f"{sorted(unknown)[:3]}")
    blocked = returncode == BLOCKED_EXIT or bool(provenance.get("blocked"))
    crashed = not blocked and returncode not in OK_EXITS
    accepted, rejected = [], []
    for rid, design_row in requested.items():
        raw = produced.get(rid)
        if raw is None:
            reason = "NOT_RETURNED"
        elif blocked:
            reason = f"BLOCKED_RUN:{raw.get('outcome')}"
        elif raw.get("identity_hash") != design_row["identity_hash"]:
            raise RunError(f"{rid}: the backend changed the row identity")
        elif raw.get("seed_reasoning", raw.get("scientific_seed")) != \
                design_row["scientific_seed"]:
            raise RunError(f"{rid}: generated under another seed")
        else:
            cls = OUT.classify(raw)
            if cls.behavioural and generator == SEAM_GENERATOR:
                absent = OUT.SEAM_ROW_KEYS - set(raw)
                if absent:
                    raise RunError(f"{rid}: the backend returned a row without "
                                   f"the seam schema (missing "
                                   f"{sorted(absent)[:5]})")
            if cls.behavioural:
                accepted.append(raw)
                continue
            reason = f"{cls.kind}:{cls.reason}"
        rejected.append({"row_id": rid, "attempt": attempt, "reason": reason,
                         "returncode": returncode, "record": raw})
    append_jsonl(rows_path, accepted)
    append_jsonl(rejected_path, rejected)
    append_jsonl(prov_path, [{"event": "backend_run", "attempt": attempt,
                              "generator": generator,
                              "environment_identity_hash":
                                  environment_identity_hash,
                              "device": device,
                              "attempt_dir": attempt_dir.relative_to(
                                  run_dir).as_posix(),
                              "returncode": returncode, "blocked": blocked,
                              "crashed": crashed, "requested": len(missing),
                              "accepted": len(accepted),
                              "rejected": len(rejected),
                              "provenance": provenance}])
    group.update(returncode=returncode, accepted_now=len(accepted),
                 rejected_now=len(rejected),
                 open=len(rejected) + len(exhausted))
    if blocked:
        raise RunError(f"{stage}/{model_key}: the backend was blocked (exit "
                       f"{returncode}; {_blocked_detail(provenance)}); "
                       f"{len(rejected)} rows rejected, none accepted; fix the "
                       "engine and resume")
    if crashed:
        raise RunError(f"{stage}/{model_key}: the backend exited {returncode}; "
                       f"{len(accepted)} completed rows kept, {len(rejected)} "
                       f"rejected; see {out.get('log', run_dir)} and resume")
    return group


def check_visibility(environment: Mapping[str, Any],
                      spec: BackendSpec) -> None:
    """A CUDA backend must be given CUDA_VISIBLE_DEVICES: with the ROCm
    variable every worker would land on cuda:0 while recording another
    device (third audit C6a)."""
    if environment.get("torch_cuda") and \
            spec.visibility_var != "CUDA_VISIBLE_DEVICES":
        raise RunError("the backend is a CUDA build (CUDA "
                       f"{environment.get('torch_cuda')}) but GPUs would be "
                       f"selected with {spec.visibility_var}; pass "
                       "--accelerator cuda")


def execute(root: Path, design: Sequence[Mapping[str, Any]], *,
            freeze1: Mapping[str, Any], approvals: Mapping[str, Any] | None,
            token: str | None = None, generate: GenerateFn | None = None,
            backend: BackendSpec | None = None,
            devices: Sequence[int] | None = None) -> dict[str, Any]:
    """Generate every row of ``design`` that has no accepted generation,
    with one worker per device in ``devices`` (default: the backend's)."""
    synthetic = generate is not None
    if synthetic and backend is not None:
        raise RunError("a stand-in generator and a real backend were both "
                       "given")
    identity_hash = None
    if not synthetic:
        spec = backend or BackendSpec()
        live: dict[str, Any] = {}

        def probe_live() -> Mapping[str, Any]:
            live.update(ENV.probe(spec.python))
            return live
        F.assert_authorized(freeze1, approvals or {}, token,
                            live_environment=probe_live)
        identity_hash = record_hash(ENV.identity_of(live))
        check_visibility(live, spec)
    devices = tuple(devices) if devices else \
        ((backend or BackendSpec()).device,)
    if len(set(devices)) != len(devices):
        raise RunError(f"a device is listed twice: {list(devices)}")
    workers = {d: generate if synthetic else
               subprocess_backend(replace(spec, device=d)) for d in devices}
    limit = EV.config_of(freeze1).max_technical_attempts
    if any(r.get("load", 0) > 1 for r in design):
        raise RunError("a composed row reached the pilot runner")
    init_root(root, synthetic=synthetic, freeze1_hash=freeze1["manifest_hash"])
    summary: dict[str, Any] = {"generated": 0, "reused": 0, "rejected": 0,
                               "open": 0, "repeats_collapsed": 0,
                               "exhausted": [], "groups": []}
    with run_lock(root):
        expected = EV.authenticate_design(root, freeze1, design)
        groups: dict[tuple[str, str], list[Mapping[str, Any]]] = {}
        for r in design:
            groups.setdefault((r["stage"], r["model"]), []).append(r)
        pending = sorted(groups)
        free: queue.SimpleQueue[int] = queue.SimpleQueue()
        for d in devices:
            free.put(d)

        def work(key: tuple[str, str]) -> dict[str, Any]:
            device = free.get()
            try:
                return _run_group(root, key[0], key[1], groups[key],
                                  workers[device], expected[key[0]],
                                  generator=(SYNTHETIC_GENERATOR if synthetic
                                             else SEAM_GENERATOR),
                                  environment_identity_hash=identity_hash,
                                  max_technical_attempts=limit,
                                  device=device)
            finally:
                free.put(device)
        with ThreadPoolExecutor(max_workers=len(devices)) as pool:
            futures = [pool.submit(work, key) for key in pending]
        errors = [f.exception() for f in futures if f.exception()]
        if errors:
            raise errors[0]
        for g in (f.result() for f in futures):
            summary["generated"] += g["accepted_now"]
            summary["reused"] += g["reused"]
            summary["rejected"] += g["rejected_now"]
            summary["open"] += g["open"]
            summary["repeats_collapsed"] += g["repeats_collapsed"]
            summary["exhausted"] += g["exhausted"]
            summary["groups"].append(g)
    summary["complete"] = summary["open"] == 0
    if summary["exhausted"]:
        summary["note"] = (
            f"{len(summary['exhausted'])} rows failed technically "
            f"{limit} times and are not retried (max_technical_attempts, "
            "D04); the stage cannot complete until the researcher decides. "
            "No partial-completion rule exists (D06)")
    return summary
