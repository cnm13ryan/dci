"""Stage 122 — migrated from notebook cell 122.py (runtime_provenance_gates).

Importing this module RUNS the stage, exactly as executing the notebook cell
did; the runner imports stages in protocol order and tests never import them
directly. Body text is the notebook cell's, byte-for-byte, apart from the
mechanical shared-state rewrite (NAME -> S.NAME) and the ledgered patches;
diff against notebook_source/cells/122.py to audit.
"""
from __future__ import annotations

from dci.pipeline import state as S  # noqa: N811 - explicit shared run state
from dci.pipeline._prelude import *  # noqa: F401,F403 - the notebook's import cell
from dci.exceptions import LineageViolation, StudyStop  # noqa: F401
from dci.protocol.gate_types import GateOutcome  # noqa: F401
from dci.provenance.hashes import sha, sha_text  # noqa: F401
from dci.statuses import GateStatus  # noqa: F401

def hardware_report() -> dict[str, Any]:
    report: dict[str, Any] = {
        "cuda_available": torch.cuda.is_available(),
        "python": sys.version.replace("\n", " "),
        "platform": platform.platform(),
        "cpu_ram_gb": round(psutil.virtual_memory().total / 2**30, 2),
        "disk_free_gb": round(shutil.disk_usage("/").free / 2**30, 2),
        "colab_release_tag": os.environ.get("COLAB_RELEASE_TAG"),
    }
    if torch.cuda.is_available():
        props = torch.cuda.get_device_properties(0)
        report.update(gpu_name=props.name,
                      gpu_memory_gb=round(props.total_memory / 2**30, 2),
                      compute_capability=f"{props.major}.{props.minor}")
    return report


S.HARDWARE = hardware_report()

if not S.CFG.dry_run and not torch.cuda.is_available():
    raise RuntimeError("No CUDA device. Runtime > Change runtime type > GPU.")

S.PACKAGE_VERSIONS = {}
for _name in ("torch", "transformers", "tokenizers", "accelerate", "numpy",
              "pandas", "scipy", "statsmodels"):
    try:
        S.PACKAGE_VERSIONS[_name] = importlib.metadata.version(_name)
    except importlib.metadata.PackageNotFoundError:
        S.PACKAGE_VERSIONS[_name] = None








# ==================================================== execution fingerprint
# Everything that can change a generated response, other than the tokenizer
# state, which is only knowable after the model loads and is therefore carried
# alongside on every committed batch.
S.EXECUTION_CONDITION = {
    "protocol_version": S.CFG.protocol_version,
    "model_profile": S.CFG.model_profile,
    "model_id": S.CFG.model_id,
    "model_revision": S.CFG.model_revision,
    "engine": S.CFG.engine,
    "dtype": S.CFG.inference_dtype,
    "attn_implementation": S.CFG.attn_implementation,
    "do_sample": S.CFG.do_sample,
    "temperature": S.CFG.temperature,
    "top_p": S.CFG.top_p,
    "max_new_tokens": S.CFG.max_new_tokens,
    "max_input_tokens": S.CFG.max_input_tokens,
    "initial_batch_size": S.CFG.initial_batch_size,
    "adaptive_batching": S.CFG.adaptive_batching,
    "base_seed": S.CFG.base_seed,
    "transformers": S.PACKAGE_VERSIONS["transformers"],
    "tokenizers": S.PACKAGE_VERSIONS["tokenizers"],
    "torch": S.PACKAGE_VERSIONS["torch"],
    "dry_run": S.CFG.dry_run,
}
S.EXECUTION_SHA256 = sha(S.EXECUTION_CONDITION)

# =====================================================================
# Hardware execution class (v15)
#
# v14 recorded hardware in a diagnostics report and then let a run resume on
# anything. Kernel selection, reduction order and numerical behaviour all depend
# on the device and the CUDA/attention stack, so a confirmatory dataset half
# generated on one GPU and half on another is one dataset produced under two
# execution conditions. v15 refuses by default. There are no validated
# equivalence classes yet, and inventing one here would be a guess.
# =====================================================================
def hardware_class() -> dict[str, Any]:
    if not torch.cuda.is_available():
        return {"gpu_name": None, "compute_capability": None,
                "cuda_runtime": None, "torch_cuda_build": None,
                "attn_implementation": S.CFG.attn_implementation,
                "device_count": 0, "class": "cpu_or_dry_run"}
    props = torch.cuda.get_device_properties(0)
    fields = {
        "gpu_name": props.name,
        "compute_capability": f"{props.major}.{props.minor}",
        "cuda_runtime": getattr(torch.version, "cuda", None),
        "torch_cuda_build": f"{torch.__version__}+cu{getattr(torch.version, 'cuda', 'na')}",
        "attn_implementation": S.CFG.attn_implementation,
        "device_count": int(torch.cuda.device_count()),
    }
    fields["class"] = sha(fields)[:16]
    return fields


S.HARDWARE_CLASS = hardware_class()
S.HARDWARE_CLASS_SHA256 = sha(S.HARDWARE_CLASS)


def assert_hardware_class(frozen: Optional[dict[str, Any]]) -> None:
    """Refuse to generate a scientific batch across a hardware class boundary."""
    if not frozen or not S.CFG.enforce_hardware_class or S.CFG.dry_run:
        return
    if sha(frozen) == S.HARDWARE_CLASS_SHA256:
        return
    if frozen.get("class") in S.CFG.hardware_equivalence_classes and \
            S.HARDWARE_CLASS.get("class") in S.CFG.hardware_equivalence_classes:
        S.log_departure("generation", "identical hardware execution class",
                      "resumed inside a declared equivalence class",
                      f"{frozen.get('class')} and {S.HARDWARE_CLASS.get('class')} "
                      "are both listed in hardware_equivalence_classes")
        return
    differing = sorted(k for k in S.HARDWARE_CLASS
                       if frozen.get(k) != S.HARDWARE_CLASS.get(k))
    raise StudyStop(
        GateOutcome(gate="generation", status=GateStatus.HARDWARE_CLASS_MISMATCH,
                    reason=f"hardware differs on {differing}",
                    quantities={"frozen": frozen, "current": S.HARDWARE_CLASS,
                                "differing_fields": differing},
                    new_protocol_version_required=True),
        f"HARDWARE_CLASS_MISMATCH on {differing}. This run was frozen on "
        f"{frozen.get('gpu_name')} ({frozen.get('compute_capability')}) and is "
        f"resuming on {S.HARDWARE_CLASS.get('gpu_name')} "
        f"({S.HARDWARE_CLASS.get('compute_capability')}). Kernel selection and "
        "reduction order depend on both, so the two halves of the dataset would "
        "not share an execution condition. v15 declares no validated hardware "
        "equivalence classes; adding one is a protocol decision that needs "
        "evidence, not a convenience flag.")
S.assert_hardware_class = assert_hardware_class

# Filled by load_model. Recorded on every committed batch and verified on
# restore, so a changed tokenizer or chat template invalidates the cache even
# though it cannot be known when the run directory is created.
S.TOKENIZER_STATE: dict[str, Optional[str]] = {
    "tokenizer_sha256": "dry-run" if S.CFG.dry_run else None,
    "chat_template_sha256": "dry-run" if S.CFG.dry_run else None,
}


def row_fingerprint() -> dict[str, Any]:
    return {"execution_sha256": S.EXECUTION_SHA256,
            "tokenizer_sha256": S.TOKENIZER_STATE["tokenizer_sha256"],
            "chat_template_sha256": S.TOKENIZER_STATE["chat_template_sha256"]}
S.row_fingerprint = row_fingerprint


# ============================================================ storage roots
from dci.storage.layout import resolve_durable_base
DRIVE_AVAILABLE, DRIVE_NOTE, DURABLE_BASE = resolve_durable_base(S.CFG)


PROFILE_ROOT = DURABLE_BASE / S.CFG.protocol_version / S.CFG.model_profile
PROFILE_ROOT.mkdir(parents=True, exist_ok=True)

SUBDIRS = ("config", "audit", "designs", "gates", "responses", "scores",
           "figures", "manifests", "exports", "checkpoints", "quarantine")


def _resolve_run_id() -> tuple[str, bool]:
    """Reuse a run only when its execution fingerprint matches exactly."""
    if S.RUN_ID:
        return S.RUN_ID, (PROFILE_ROOT / S.RUN_ID).exists()
    candidates = []
    for meta_path in sorted(PROFILE_ROOT.glob("*/run_meta.json")):
        try:
            meta = json.loads(meta_path.read_text())
        except json.JSONDecodeError:
            continue
        if meta.get("execution_sha256") == S.EXECUTION_SHA256:
            candidates.append((meta.get("created_utc", ""), meta_path.parent.name))
    if candidates:
        return sorted(candidates)[-1][1], True
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"run-{stamp}-{S.EXECUTION_SHA256[:8]}", False


S.RESOLVED_RUN_ID, RESUMED = _resolve_run_id()
S.RUN_ROOT = PROFILE_ROOT / S.RESOLVED_RUN_ID
for _d in SUBDIRS:
    (S.RUN_ROOT / _d).mkdir(parents=True, exist_ok=True)

# The local fast cache is scoped by profile and run so that no two profiles can
# ever see one another's batches even if the durable root is shared.
S.CACHE_DIR = Path(S.CFG.local_root) / "cache" / S.CFG.model_profile / S.RESOLVED_RUN_ID
S.CACHE_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_DIR = S.RUN_ROOT
S.CONFIG_DIR, S.AUDIT_DIR = S.RUN_ROOT / "config", S.RUN_ROOT / "audit"
S.DESIGN_DIR, S.GATE_DIR = S.RUN_ROOT / "designs", S.RUN_ROOT / "gates"
S.RESPONSE_DIR, S.SCORE_DIR = S.RUN_ROOT / "responses", S.RUN_ROOT / "scores"
S.FIGURE_DIR, MANIFEST_DIR = S.RUN_ROOT / "figures", S.RUN_ROOT / "manifests"
S.EXPORT_ROOT, CHECKPOINT_DIR = S.RUN_ROOT / "exports", S.RUN_ROOT / "checkpoints"
S.QUARANTINE_DIR = S.RUN_ROOT / "quarantine"

S.RUN_ATTEMPT_ID = f"{int(time.time())}-{os.getpid()}-{random.getrandbits(32):08x}"
RUN_META = {
    "protocol_version": S.CFG.protocol_version,
    "model_profile": S.CFG.model_profile,
    "run_id": S.RESOLVED_RUN_ID,
    "created_utc": datetime.now(timezone.utc).isoformat(),
    "execution_sha256": S.EXECUTION_SHA256,
    "execution_condition": S.EXECUTION_CONDITION,
    "produces_evidence": S.PROFILE["produces_evidence"],
    "stamp": S.PROFILE["stamp"],
    "hardware": S.HARDWARE,
    "drive_available": DRIVE_AVAILABLE,
    "durable_base": str(DURABLE_BASE),
}
if not (S.RUN_ROOT / "run_meta.json").exists():
    (S.RUN_ROOT / "run_meta.json").write_text(
        json.dumps(RUN_META, indent=2, default=str), encoding="utf-8")
(S.RUN_ROOT / f"run_attempt_{S.RUN_ATTEMPT_ID}.json").write_text(
    json.dumps({**RUN_META, "run_attempt_id": S.RUN_ATTEMPT_ID}, indent=2, default=str),
    encoding="utf-8")
(S.CONFIG_DIR / "config.json").write_text(
    json.dumps(asdict(S.CFG), indent=2, default=str), encoding="utf-8")


# ==================================================================== seeds
def set_all_seeds(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    set_seed(seed)
S.set_all_seeds = set_all_seeds




S.set_all_seeds(S.CFG.base_seed)
torch.backends.cuda.matmul.allow_tf32 = False

S.RESOLVED_DTYPE = S.CFG.inference_dtype
if torch.cuda.is_available() and S.CFG.require_exact_dtype:
    _props = torch.cuda.get_device_properties(0)
    if S.CFG.inference_dtype == "bfloat16" and _props.major < 8:
        raise RuntimeError(
            f"inference_dtype is bfloat16 but {_props.name} is compute "
            f"{_props.major}.{_props.minor}.")




def source_fingerprint(objects: list[Any]) -> str:
    import inspect

    def fallback(obj: Any) -> str:
        code = getattr(obj, "__code__", None)
        if code is not None:
            return "|".join([getattr(obj, "__qualname__", "?"), code.co_name,
                             hashlib.sha256(code.co_code).hexdigest(),
                             repr(code.co_names), repr(code.co_varnames)])
        if isinstance(obj, type):
            return obj.__qualname__ + "|" + repr(sorted(
                k for k in vars(obj) if not k.startswith("__")))
        return f"{type(obj).__name__}:{getattr(obj, '__qualname__', '?')}"

    chunks = []
    for obj in objects:
        try:
            chunks.append(inspect.getsource(obj))
        except (TypeError, OSError):
            chunks.append(fallback(obj))
    return sha_text("\n".join(chunks))
S.source_fingerprint = source_fingerprint


# =================================================================== phases
S.PHASES: dict[str, float] = {}


class phase:
    def __init__(self, name: str):
        self.name = name

    def __enter__(self):
        self.started = time.perf_counter()
        return self

    def __exit__(self, *exc):
        S.PHASES[self.name] = S.PHASES.get(self.name, 0.0) + (
            time.perf_counter() - self.started)
        return False
S.phase = phase


S.PHASE_NAMES = (
    "gate0_selftest", "gateM_measurement", "benchmark", "screen_u", "prescreen",
    "hard_eligibility", "calibration", "feature_build", "caliper_derivation",
    "gate2_feasibility", "pool_audit", "pseudo_focal_cohort",
    "gate3_validation", "gate3b_wording", "freeze", "verify", "bootstrap",
    "analysis", "gee", "robustness", "gate4_falsification", "plotting",
    "hashing", "archiving", "drive_restore", "drive_mirror",
)

# ================================================================ telemetry
S.TELEMETRY: list[dict[str, Any]] = []
S._telemetry_stop = None
_TELEMETRY_BASELINE: dict[str, float] = {}
_PROC = psutil.Process()
S.CUMULATIVE_COUNTERS = ("disk_read_mb", "disk_write_mb", "proc_read_mb",
                       "proc_write_mb")


def start_telemetry() -> None:
    pass
    if not S.CFG.sample_telemetry or S._telemetry_stop is not None:
        return
    import threading

    S._telemetry_stop = threading.Event()

    def _loop():
        query = ("utilization.gpu,utilization.memory,memory.used,"
                 "power.draw,temperature.gpu")
        while not S._telemetry_stop.wait(S.CFG.telemetry_interval_s):
            sample: dict[str, Any] = {"t": time.time()}
            try:
                cpu = psutil.cpu_times_percent(interval=None)
                sample.update(cpu_percent=psutil.cpu_percent(interval=None),
                              iowait_percent=getattr(cpu, "iowait", None),
                              ram_used_gb=psutil.virtual_memory().used / 2**30)
                io = psutil.disk_io_counters()
                if io:
                    sample.update(disk_read_mb=io.read_bytes / 2**20,
                                  disk_write_mb=io.write_bytes / 2**20)
                try:
                    pio = _PROC.io_counters()
                    sample.update(proc_read_mb=pio.read_bytes / 2**20,
                                  proc_write_mb=pio.write_bytes / 2**20)
                except (psutil.AccessDenied, AttributeError):
                    pass
            except Exception:
                pass
            if torch.cuda.is_available():
                try:
                    out = subprocess.check_output(
                        ["nvidia-smi", f"--query-gpu={query}",
                         "--format=csv,noheader,nounits"], text=True, timeout=5)
                    parts = [p.strip() for p in out.strip().splitlines()[0].split(",")]
                    keys = ["gpu_util", "gpu_mem_util", "gpu_mem_used_mb",
                            "gpu_power_w", "gpu_temp_c"]
                    sample.update({k: float(v) if v not in ("", "N/A") else None
                                   for k, v in zip(keys, parts)})
                except Exception:
                    pass
            for name in S.CUMULATIVE_COUNTERS:
                value = sample.get(name)
                if value is None:
                    continue
                _TELEMETRY_BASELINE.setdefault(name, float(value))
                sample[f"{name}_delta"] = float(value) - _TELEMETRY_BASELINE[name]
            S.TELEMETRY.append(sample)

    threading.Thread(target=_loop, daemon=True).start()


def stop_telemetry() -> None:
    if S._telemetry_stop is not None:
        S._telemetry_stop.set()
S.stop_telemetry = stop_telemetry


start_telemetry()

# =============================================================== departures
S.DEPARTURES: list[dict[str, str]] = []


def log_departure(stage: str, planned: str, actual: str, reason: str) -> None:
    S.DEPARTURES.append({"stage": stage, "planned": planned, "actual": actual,
                       "reason": reason, "utc": datetime.now(timezone.utc).isoformat()})
    print(f"DEPARTURE [{stage}]: {actual} (planned: {planned}). Reason: {reason}")
S.log_departure = log_departure


# ==================================================== gate outcome records




S.GATE_STATE: dict[str, GateOutcome] = {}


def record_gate(outcome: GateOutcome) -> GateOutcome:
    """Single source of truth. Every gate writes here and to its own artifact."""
    assert outcome.status in GateStatus.ALL, f"unknown status {outcome.status!r}"
    outcome.recorded_utc = datetime.now(timezone.utc).isoformat()
    S.GATE_STATE[outcome.gate] = outcome
    (S.GATE_DIR / f"gate_{outcome.gate}.json").write_text(
        json.dumps(outcome.as_dict(), indent=2, default=str), encoding="utf-8")
    if not outcome.gate.startswith("_"):
        print(f"GATE {outcome.gate}: {outcome.status}"
              + ("  [DRY-RUN BYPASS]" if outcome.dry_run_bypassed else ""))
    return outcome
S.record_gate = record_gate


def stop(gate: str, status: str, reason: str, quantities: dict[str, Any],
         thresholds: dict[str, Any], more_data_could_resolve: bool,
         new_protocol_version_required: bool, message: str = "") -> GateOutcome:
    """Record a failure and raise, unless a dry run is exercising the path."""
    bypass = bool(S.CFG.dry_run and S.CFG.dry_run_bypass_gates)
    outcome = S.record_gate(GateOutcome(
        gate=gate, status=status, reason=reason, quantities=quantities,
        thresholds=thresholds, more_data_could_resolve=more_data_could_resolve,
        new_protocol_version_required=new_protocol_version_required,
        dry_run_bypassed=bypass))
    print(message or reason)
    if bypass:
        S.log_departure(gate, f"halt on {status}",
                      "continued so the remaining cells could be exercised",
                      "DRY RUN ONLY. Unreachable when dry_run is False. Nothing "
                      "computed after this point is evidence.")
        return outcome
    raise StudyStop(outcome, message or reason)
S.stop = stop


def require_gate(*names: str) -> None:
    for name in names:
        outcome = S.GATE_STATE.get(name)
        if outcome is None:
            raise StudyStop(
                GateOutcome(gate=name, status=GateStatus.MEASUREMENT_VALIDITY_FAILED,
                            reason="gate has not run"),
                f"gate '{name}' has not run. Execute its cell before this one.")
        if not outcome.passed and not outcome.dry_run_bypassed:
            raise StudyStop(outcome,
                            f"gate '{name}' returned {outcome.status}: {outcome.reason}")
S.require_gate = require_gate


# =====================================================================
# Object lineage (v15)
#
# v14 proved that hard_eligible_universe() referenced no B-relative symbol, by
# disassembling it. That is a property of the FUNCTION. It says nothing about
# the ARGUMENT, and v14 called it on PRESCREEN_KEPT, which is the output of a
# prescreen that ranks candidates by their isolated-difficulty distance to B.
# The universe was therefore downstream of a B-relative filter while the audit
# reported it as independent.
#
# Lineage tracks the taints an object carries, propagated through the objects it
# was derived from, and lets a construction refuse a tainted input outright.
# =====================================================================
S.TAINT_FOCAL_RELATIVE = "focal_relative"
S.TAINT_UVAL_OBSERVED = "u_val_observed"
S.TAINT_CONFIRMATORY = "confirmatory_observed"

LINEAGE: dict[str, frozenset[str]] = {}


def declare_lineage(name: str, taints: Iterable[str] = (),
                    parents: Iterable[str] = ()) -> frozenset[str]:
    """Record an object's taints, inheriting every taint of its parents."""
    carried = set(taints)
    for parent in parents:
        if parent not in LINEAGE:
            raise KeyError(f"lineage of {name!r} names an undeclared parent {parent!r}")
        carried |= LINEAGE[parent]
    LINEAGE[name] = frozenset(carried)
    return LINEAGE[name]
S.declare_lineage = declare_lineage


def lineage_of(name: str) -> frozenset[str]:
    if name not in LINEAGE:
        raise KeyError(f"{name!r} has no declared lineage. Declare it before use.")
    return LINEAGE[name]
S.lineage_of = lineage_of




def require_untainted(name: str, forbidden: Iterable[str], context: str) -> None:
    """Refuse an input whose ancestry includes a forbidden influence.

    This is enforced at the CALL, so substituting a tainted object upstream
    fails even though the callee's own source is unchanged.
    """
    bad = sorted(S.lineage_of(name) & set(forbidden))
    if bad:
        raise LineageViolation(
            f"{context}: {name!r} carries {bad}, which may not influence it. "
            f"Its full lineage is {sorted(S.lineage_of(name))}.")
S.require_untainted = require_untainted


def lineage_table() -> pd.DataFrame:
    return pd.DataFrame(
        [{"object": k, "taints": ";".join(sorted(v)) or "(none)"}
         for k, v in sorted(LINEAGE.items())]).set_index("object")
S.lineage_table = lineage_table


# =====================================================================
# Staged compute budget (v15)
#
# v14 printed one projection, computed before anything was known, from the first
# paraphrase stage and assumed constants for the U split, the U_val measured set
# and the pseudo-focal donor union. It then never revised it, so a nominal
# figure was presented where a frozen realised one belonged.
#
# v15 records a budget SNAPSHOT at each milestone. Each one states what it is
# based on and whether it is nominal or realised.
# =====================================================================
S.BUDGET_SNAPSHOTS: list[dict[str, Any]] = []


def record_budget(stage: str, basis: str, realised: bool,
                  generations: dict[str, int], notes: str = "",
                  seconds_per_generation: Optional[float] = None) -> dict[str, Any]:
    total = int(sum(generations.values()))
    rate = seconds_per_generation
    snapshot = {
        "snapshot": stage,
        "basis": basis,
        "realised": bool(realised),
        "total_generations": total,
        "seconds_per_generation": rate,
        "gpu_hours": (round(total * rate / 3600.0, 3) if rate else None),
        "gpu_hours_source": ("measured benchmark" if rate and realised
                             else "placeholder rate" if rate else "not costed"),
        "notes": notes,
        **{f"gen_{k}": int(v) for k, v in generations.items()},
    }
    S.BUDGET_SNAPSHOTS.append(snapshot)
    return snapshot
S.record_budget = record_budget


def budget_frame() -> pd.DataFrame:
    if not S.BUDGET_SNAPSHOTS:
        return pd.DataFrame()
    return pd.DataFrame(S.BUDGET_SNAPSHOTS).set_index("snapshot")
S.budget_frame = budget_frame


def checkpoint(stage: str, payload: dict[str, Any]) -> None:
    """A durable marker after every gate, so a disconnect resumes with context."""
    body = {"stage": stage, "utc": datetime.now(timezone.utc).isoformat(),
            "run_attempt_id": S.RUN_ATTEMPT_ID,
            "gates": {k: v.status for k, v in S.GATE_STATE.items()},
            "payload": payload}
    (CHECKPOINT_DIR / f"{stage}.json").write_text(
        json.dumps(body, indent=2, default=str), encoding="utf-8")
S.checkpoint = checkpoint


print(f"run id   : {S.RESOLVED_RUN_ID}  ({'resumed' if RESUMED else 'new'})")
print(f"durable  : {S.RUN_ROOT}")
print(f"cache    : {S.CACHE_DIR}")
print(f"execution: {S.EXECUTION_SHA256[:16]}")
