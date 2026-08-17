"""Per-model protocol freeze records (prereg §18 Gate 3; task §6, §2.10).

Each model's record is built from that model's own gates and calibrated values
only — no field is inherited or copied from another model's record, by
construction: `build_freeze_record` takes exactly one model's inputs.

The record is complete or it is nothing: every §18 frozen field and every
§2.10 design-defining resampling field must be present, or validation fails
closed. Once written, the record is immutable — a rebuild must byte-match, and
`assert_freeze_matches` refuses generation, selection or analysis against a
mismatched or incomplete record.
"""
from __future__ import annotations

import json
import platform
import subprocess
from pathlib import Path
from typing import Any

from dci1.constraints.wordings import all_wordings
from dci1.evidence.store import atomic_write
from dci1.masking.mask import analysis_code_hash
from dci1.models.adapters import ModelSpec, backend_plan
from dci1.protocol.constants import (
    AMENDMENT_ID,
    BOOTSTRAP_RESAMPLES,
    CANARY_STRING,
    DECODING,
    EQUIVALENCE_REGION_EXCHANGEABILITY,
    EQUIVALENCE_REGION_PRIMARY,
    EXCHANGEABILITY_MARGIN,
    FAMILY_SIZES,
    PROTOCOL_ID,
    PROTOCOL_VERSION,
    PSEUDO_RUN_FULL_ANALYSIS_COUNT,
    RESAMPLING_FIELDS,
    SMALLEST_EFFECT_OF_INTEREST,
    ProtocolError,
    StudyConfig,
)
from dci1.protocol.hashing import sha, sha_file
from dci1.tables.schemas import SCHEMA_VERSIONS as _SCHEMA_VERSIONS
from dci1.verifiers.registry import verifier_source_hash

DCI1_ROOT = Path(__file__).resolve().parents[3]
REPO_ROOT = DCI1_ROOT.parent
BACKEND_PYTHON = DCI1_ROOT / "environments" / "backend" / ".venv" / "bin" / "python"

REQUIRED_FIELDS = (
    "protocol", "model", "backend", "no_thinking", "decoding",
    "context_limits", "constraints", "topics", "prompt_template",
    "verifiers", "scoring_rules", "block_plan_hash", "families",
    "equivalence", "bootstrap", "resampling", "codebook_hash",
    "analysis_code_hash", "environment", "gates", "canary",
    "documents", "addendum",
)

#: Addendum-A §7 freeze fields; each must be present in every record.
ADDENDUM_FIELDS = (
    "storage_format_profile", "schema_versions", "manifest_hash_algorithm",
    "masking_scheme_id", "masking_root_seed", "mask_key_hash",
    "retention_policy_id", "replication_target_id", "addendum_version",
    "codebook_name_mapping_hash",
)


def _pip_freeze(python: Path) -> list[str]:
    try:
        out = subprocess.run([str(python), "-m", "pip", "freeze"],
                             capture_output=True, text=True, timeout=120)
        return sorted(out.stdout.splitlines())
    except Exception:
        return []


#: The study's own scientific interpreter (dci1/.venv). The repo-root .venv
#: belongs to the historical confirmatory study and must stay pristine —
#: installing pyarrow there flipped pandas 3's string backend and broke that
#: study's regression baselines, which is why this venv exists.
SCIENTIFIC_PYTHON = DCI1_ROOT / ".venv" / "bin" / "python"


def environment_record() -> dict[str, Any]:
    """The D22 environment digest inputs: both interpreters' package freezes,
    kernel identity, and GPU identity."""
    scientific = _pip_freeze(SCIENTIFIC_PYTHON)
    backend = _pip_freeze(BACKEND_PYTHON)
    try:
        gpus = subprocess.run(["rocm-smi", "--showproductname"],
                              capture_output=True, text=True,
                              timeout=60).stdout
        gcn = sorted(set(line.split()[-1] for line in gpus.splitlines()
                         if "GFX Version" in line))
    except Exception:
        gcn = []
    uname = platform.uname()
    cpu_model = ""
    try:
        for line in Path("/proc/cpuinfo").read_text().splitlines():
            if line.startswith("model name"):
                cpu_model = line.split(":", 1)[1].strip()
                break
    except OSError:
        pass
    vllm_version = next((p.split("==")[1] for p in backend
                         if p.startswith("vllm==")), "")
    lockfile = DCI1_ROOT / "environments" / "backend" / "uv.lock"
    record = {
        "kernel": uname.release,
        "os": f"{uname.system} {uname.version}",
        "cpu_model": cpu_model,
        "gpu_model": "AMD Radeon RX 7900 XTX" if gcn else "",
        "interpreter_version": platform.python_version(),
        "scientific_interpreter": str(SCIENTIFIC_PYTHON),
        "backend_interpreter": str(BACKEND_PYTHON),
        "scientific_freeze": scientific,
        "backend_freeze": backend,
        "gcn_archs": gcn,
        "vllm_version": vllm_version,
        "dependency_lockfile_hash": (sha_file(lockfile)
                                     if lockfile.exists() else ""),
        # BLAS threading (Addendum A §5): numpy's runtime thread config.
        "blas_threading": _blas_threading(),
    }
    record["environment_digest"] = sha(record)
    return record


def _blas_threading() -> dict[str, Any]:
    import os

    try:
        import numpy

        blas = [{k: d.get(k) for k in
                 ("internal_api", "num_threads", "threading_layer")}
                for d in numpy.show_config(mode="dicts").get(
                    "Build Dependencies", {}).values()
                if isinstance(d, dict) and "name" in d] or "numpy-default"
    except Exception:                                    # noqa: BLE001
        blas = "unavailable"
    return {"numpy_blas": blas,
            "OMP_NUM_THREADS": os.environ.get("OMP_NUM_THREADS", ""),
            "OPENBLAS_NUM_THREADS":
                os.environ.get("OPENBLAS_NUM_THREADS", "")}


def _git_commit() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT,
                              capture_output=True, text=True,
                              timeout=30).stdout.strip()
    except Exception:
        return ""


def build_freeze_record(spec: ModelSpec, *, config: StudyConfig,
                        gate0: dict[str, Any], gate1: dict[str, Any],
                        gate2: dict[str, Any],
                        qualification: dict[str, Any],
                        topic_split_ids: dict[str, list[str]],
                        block_plan_hash: str,
                        environment: dict[str, Any] | None = None,
                        ) -> dict[str, Any]:
    """One model's complete freeze record, from that model's inputs only."""
    if not gate2.get("passed"):
        raise ProtocolError(
            f"{spec.model_key}: Gate 2 did not pass; a freeze record cannot "
            f"be produced for a model whose regime was not found")
    n = gate2["selected_n"]
    m = gate2["selected_m"]
    references = tuple(gate2["references"])
    plan = backend_plan(spec)
    from dci1.generation.pools import backend_config_hash
    from dci1.protocol.codebook import CODEBOOKS

    record: dict[str, Any] = {
        "protocol": {"id": PROTOCOL_ID, "version": PROTOCOL_VERSION,
                     "amendment": AMENDMENT_ID},
        "model": {"model_key": spec.model_key, "model_id": spec.model_id,
                  "revision": spec.revision, "family": spec.family},
        "backend": {
            "kind": "vllm_backend process boundary",
            "backend_code_commit": _git_commit(),
            "backend_interpreter": str(BACKEND_PYTHON),
            "plan": plan,
            "backend_config_hash": backend_config_hash(plan)},
        "no_thinking": {
            "chat_template_kwargs": dict(spec.chat_template_kwargs),
            "switch_expectation": spec.switch_expectation,
            "reasoning_mode": "NO_THINKING",
            "qualification_verdict": qualification.get("verdict")},
        "decoding": dict(DECODING),
        "context_limits": {"max_model_len": spec.max_model_len,
                           "max_new_tokens": DECODING["max_new_tokens"]},
        "constraints": {
            "n": n, "m": m, "references": list(references),
            "target_wordings": list(all_wordings("A", n=n)),
            "focal_wordings": list(all_wordings("B", m=m)),
            "reference_wordings": {r: list(all_wordings(r))
                                   for r in references},
            "certificates": gate2.get("certificates", [])},
        "topics": {"split_ids": topic_split_ids,
                   "counts": {k: len(v) for k, v in topic_split_ids.items()}},
        "prompt_template":
            "{question}\\n\\n<numbered constraints>\\n\\nAnswer: (D12)",
        "verifiers": {"source_hash": verifier_source_hash()},
        "scoring_rules": {
            "primary": "S0", "alternatives": ["S1", "S2", "S3"],
            "taxonomy_source_hash": sha_file(
                DCI1_ROOT / "src" / "dci1" / "analysis" / "taxonomy.py")},
        "block_plan_hash": block_plan_hash,
        "families": dict(FAMILY_SIZES),
        "equivalence": {
            "smallest_effect_of_interest": SMALLEST_EFFECT_OF_INTEREST,
            "exchangeability_margin": EXCHANGEABILITY_MARGIN,
            "primary_region": list(EQUIVALENCE_REGION_PRIMARY),
            "exchangeability_region":
                list(EQUIVALENCE_REGION_EXCHANGEABILITY)},
        "bootstrap": {"resamples": BOOTSTRAP_RESAMPLES,
                      "stratified_by": "presentation order"},
        "resampling": {**config.to_dict(),
                       "pseudo_run_full_analysis_count":
                           PSEUDO_RUN_FULL_ANALYSIS_COUNT},
        "codebook_hash": sha(CODEBOOKS),
        "analysis_code_hash": analysis_code_hash(),
        "environment": environment or environment_record(),
        "gates": {"gate0": {"passed": gate0.get("passed"),
                            "report": gate0},
                  "gate1": {"status": gate1.get("status"),
                            "passed": gate1.get("passed")},
                  "gate2": gate2},
        "canary": CANARY_STRING,
        "documents": {
            "preregistration_hash": sha_file(
                REPO_ROOT / "user-notes" / "DCI-1_preregistration_v2.md"),
            "decisions_hash": sha_file(DCI1_ROOT / "DECISIONS.md"),
            "mapping_hash": sha_file(DCI1_ROOT / "MAPPING.md"),
            "reconciliation_hash": sha_file(
                DCI1_ROOT / "docs" / "addendum_a_reconciliation.md")},
        # Addendum A §7 pre-freeze fields (reconciliation R53). The two null
        # values are conflicts resolved to v2 §19 by precedence: the mask key
        # is drawn from the system random source AFTER generation, so neither
        # a masking root seed nor the key hash can exist at freeze (R40/R41);
        # the key hash is recorded in the run record and study manifest at
        # construction instead.
        "addendum": {
            "storage_format_profile": "addendum-a-default-v1",
            "schema_versions": dict(_SCHEMA_VERSIONS),
            "manifest_hash_algorithm": "sha256",
            "masking_scheme_id": "v2-s19-block-primary-permutation",
            "masking_root_seed": None,
            "mask_key_hash": None,
            "retention_policy_id": "retain-raw-indefinitely-v1",
            "replication_target_id": "durable_root_local",
            "addendum_version": "A-1.0",
            "codebook_name_mapping_hash": _codebook_mapping_hash(),
        },
    }
    validate_freeze(record)
    record["freeze_hash"] = sha(record)
    return record


def _codebook_mapping_hash() -> str:
    """Hash of the codebook name-mapping table in the reconciliation doc."""
    text = (DCI1_ROOT / "docs" / "addendum_a_reconciliation.md").read_text()
    marker = "## Codebook name mapping"
    section = text[text.index(marker):]
    from dci1.protocol.hashing import sha_text

    return sha_text(section.split("## ", 2)[1])


def validate_freeze(record: dict[str, Any]) -> None:
    """Completeness, §2.10 coverage, and non-null frozen fields; fail closed."""
    missing = [f for f in REQUIRED_FIELDS if f not in record]
    if missing:
        raise ProtocolError(f"freeze record incomplete: missing {missing}")
    resampling = record["resampling"]
    absent = [f for f in RESAMPLING_FIELDS if f not in resampling
              or resampling[f] is None]
    if absent:
        raise ProtocolError(
            f"freeze record missing design-defining resampling fields "
            f"{absent} (amendment §2.10); incomplete records fail closed")
    for field in ("n", "m", "references"):
        if record["constraints"].get(field) in (None, [], ""):
            raise ProtocolError(f"freeze record has empty calibrated field "
                                f"{field!r}")
    addendum = record.get("addendum", {})
    absent = [f for f in ADDENDUM_FIELDS if f not in addendum]
    if absent:
        raise ProtocolError(
            f"freeze record missing Addendum-A §7 fields {absent}")


def freeze_path(model_dir: Path) -> Path:
    return Path(model_dir) / "freeze" / "freeze_record.json"


def write_freeze(model_dir: Path, record: dict[str, Any]) -> Path:
    validate_freeze(record)
    path = freeze_path(model_dir)
    text = json.dumps(record, indent=2, sort_keys=True)
    if path.exists():
        if path.read_text() != text:
            raise ProtocolError(
                f"{path}: an existing freeze record differs — frozen fields "
                f"are immutable; a change requires a new protocol version")
    else:
        atomic_write(path, text)
    return path


def load_freeze(model_dir: Path) -> dict[str, Any]:
    path = freeze_path(model_dir)
    if not path.exists():
        raise ProtocolError(f"no freeze record at {path}")
    record = json.loads(path.read_text())
    validate_freeze(record)
    stored_hash = record.get("freeze_hash")
    body = {k: v for k, v in record.items() if k != "freeze_hash"}
    if sha(body) != stored_hash:
        raise ProtocolError(f"{path}: freeze record fails its own hash")
    return record


def assert_freeze_matches(record: dict[str, Any], spec: ModelSpec,
                          config: StudyConfig) -> None:
    """Refuse to run generation, selection or analysis against a mismatched
    freeze record (§27; task §8.6)."""
    if record["model"]["model_id"] != spec.model_id or \
            record["model"]["revision"] != spec.revision:
        raise ProtocolError(
            f"freeze record is for {record['model']['model_id']}@"
            f"{record['model']['revision']}, not {spec.model_id}@"
            f"{spec.revision}")
    frozen = {k: record["resampling"][k] for k in RESAMPLING_FIELDS}
    current = {k: config.to_dict()[k] for k in RESAMPLING_FIELDS}
    if frozen != current:
        diff = {k: (frozen[k], current[k]) for k in frozen
                if frozen[k] != current[k]}
        raise ProtocolError(
            f"study configuration differs from the frozen record on "
            f"{sorted(diff)}: {diff} — M and every §2.10 field are immutable "
            f"after freeze")
    if record["verifiers"]["source_hash"] != verifier_source_hash():
        raise ProtocolError("verifier source differs from the frozen hash")
