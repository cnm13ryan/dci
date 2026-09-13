"""§18.1's chat-template hash and hardware record, from what actually ran.

Two of §18.1's fields had readers and no producer, and `freeze_run` filled
both with a placeholder that `check_completeness` then refused --- so Gate 5
could not pass on any replication:

* **`chat_template_hash`.** `freeze_run` read it off the registration manifest
  with `spec.get("chat_template_hash", "UNKNOWN")`, and no manifest field of
  that name has ever existed. It is not decorative: the backend renders every
  prompt through `tokenizer.apply_chat_template`
  (`exploratory/vllm_backend/engine.py`), so the template is part of the
  model-facing text, and a template that moved between generation and a
  re-run would change what was asked without changing any prompt this
  repository stores. It is obtained here from the tokenizer of the **pinned
  revision**, loaded in the backend interpreter --- the same acquisition path
  the generation uses --- and hashed.

* **`hardware_record`.** `cmd_gate5` never passed one, so the freeze always
  saw `{}`. Rather than stamping the machine that happens to run the freeze,
  this reads the `host` block of every backend provenance sidecar the
  replication's stages actually wrote (`rows_engine.json`), checks they agree
  on architecture, device name, VRAM and the torch/vLLM/ROCm versions, and
  records that agreed identity together with the per-stage device index. What
  the freeze binds is then the hardware the evidence came off, which is the
  thing §27 is about.

Dependency provenance is included in the same artifact, over both
environments --- the analysis interpreter's `uv.lock` and
`requirements-frozen.txt`, and the backend's `uv.lock` and the vendored wheel
manifest --- because the generation and the analysis do not share a Python.

    ./.venv/bin/python tools/v4r4_backend_provenance.py

Writes `dci1/reports/dci1v4r4/backend_provenance.json`. Fails closed: a model
whose tokenizer will not load, or a stage with no sidecar, is an error rather
than an `UNKNOWN` that a later completeness check has to catch.
"""
from __future__ import annotations

import json
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any

DCI1 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DCI1 / "src"))

from dci1v4.engine import fs                                     # noqa: E402
from dci1v4.errors import IntegrityError                         # noqa: E402
from dci1v4.models.registry import MODEL_KEYS, get_model         # noqa: E402
from dci1v4.protocol.hashing import sha_file, sha_obj, sha_text  # noqa: E402

from dci1v4r4.engine.context import registered_context           # noqa: E402
from dci1v4r4.engine.paths import model_tree                     # noqa: E402
from dci1v4r4.protocol import constants as C                     # noqa: E402

OUT = DCI1 / "reports" / "dci1v4r4" / "backend_provenance.json"
BACKEND_PYTHON = DCI1 / "environments" / "backend" / ".venv" / "bin" / "python"

#: The host fields that must agree across every stage of one replication. A
#: disagreement means the evidence came off two different machines and the
#: freeze may not bind one of them as "the" hardware.
HOST_IDENTITY = ("gcn_archs", "device_names", "total_vram_gib",
                 "torch_version", "torch_hip", "vllm_version",
                 "platform_class")

_TEMPLATE_PROBE = r"""
import hashlib, json, sys
from transformers import AutoTokenizer
model_id, revision = sys.argv[1], sys.argv[2]
tok = AutoTokenizer.from_pretrained(model_id, revision=revision,
                                    local_files_only=True)
template = tok.chat_template
if isinstance(template, dict):          # a per-mode mapping, hashed as a whole
    payload = json.dumps(template, sort_keys=True)
elif template is None:
    payload = None
else:
    payload = template
print(json.dumps({
    "model_id": model_id, "revision": revision,
    "chat_template_present": payload is not None,
    "chat_template_hash": (hashlib.sha256(payload.encode()).hexdigest()
                           if payload is not None else None),
    "chat_template_chars": len(payload) if payload is not None else 0,
    "tokenizer_class": type(tok).__name__,
}))
"""


def chat_template_hashes() -> dict[str, dict[str, Any]]:
    """One entry per registered model, from the pinned revision's tokenizer.

    Run in the backend interpreter because that is where the tokenizer the
    generation uses lives; the analysis interpreter has no transformers and
    should not grow one for a hash.
    """
    if not BACKEND_PYTHON.exists():
        raise IntegrityError(
            f"backend interpreter missing: {BACKEND_PYTHON}. The chat "
            "template must come from the tokenizer the generation loads")
    out: dict[str, dict[str, Any]] = {}
    for model_key in MODEL_KEYS:
        spec = get_model(model_key)
        proc = subprocess.run(
            [str(BACKEND_PYTHON), "-c", _TEMPLATE_PROBE,
             spec.model_id, spec.revision],
            capture_output=True, text=True)
        if proc.returncode != 0:
            raise IntegrityError(
                f"{model_key}: could not read the chat template of "
                f"{spec.model_id}@{spec.revision[:12]}:\n{proc.stderr[-2000:]}")
        record = json.loads(proc.stdout.strip().splitlines()[-1])
        if not record["chat_template_present"]:
            raise IntegrityError(
                f"{model_key}: the pinned revision exposes no chat template, "
                "and the backend renders every prompt through "
                "`apply_chat_template`. §18.1 cannot bind what is not there")
        out[model_key] = record
    return out


def _sidecars(model_key: str) -> dict[str, dict[str, Any]]:
    """stage -> the `host` block of every backend run that stage made."""
    tree = model_tree(registered_context(), model_key)
    found: dict[str, dict[str, Any]] = {}
    for stage in C.STAGE_SEQUENCE:
        directory = tree.root / stage / "backend_runs"
        if not directory.exists():
            continue
        for sidecar in sorted(directory.rglob("*_engine.json")):
            payload = fs.read_json(sidecar)
            host = payload.get("host")
            if not host:
                raise IntegrityError(
                    f"{model_key}:{stage}: {sidecar.relative_to(DCI1)} "
                    "carries no host block, so the hardware that produced "
                    "those rows is not recorded")
            key = str(sidecar.relative_to(tree.root))
            found[key] = host
    return found


def hardware_record(model_key: str) -> dict[str, Any]:
    """The agreed hardware identity of every backend run this model made."""
    hosts = _sidecars(model_key)
    if not hosts:
        raise IntegrityError(
            f"{model_key} has no backend provenance sidecar; a freeze cannot "
            "bind the hardware of generations it cannot see")
    identity = {field: sorted({json.dumps(h.get(field), sort_keys=True)
                               for h in hosts.values()})
                for field in HOST_IDENTITY}
    disagreements = {f: v for f, v in identity.items() if len(v) != 1}
    if disagreements:
        raise IntegrityError(
            f"{model_key}: the backend runs disagree about the hardware they "
            f"ran on: {disagreements}. §18.1 binds one hardware record and "
            "this replication has more than one")
    devices = sorted({h.get("env", {}).get("HIP_VISIBLE_DEVICES")
                      for h in hosts.values()})
    return {
        **{field: json.loads(values[0]) for field, values in identity.items()},
        "device_count_per_run": sorted({h.get("device_count")
                                        for h in hosts.values()}),
        "hip_visible_devices_used": devices,
        "backend_runs": sorted(hosts),
        "note": "the hardware the evidence came off, read from the backend's "
                "own provenance sidecars, not the machine that ran the freeze",
    }


def dependency_record() -> dict[str, Any]:
    """Both environments, because generation and analysis do not share one."""
    files = {
        "dci1/uv.lock": DCI1 / "uv.lock",
        "dci1/requirements-frozen.txt": DCI1 / "requirements-frozen.txt",
        "dci1/environments/backend/uv.lock":
            DCI1 / "environments" / "backend" / "uv.lock",
        "dci1/environments/backend/vendor/MANIFEST.sha256":
            DCI1 / "environments" / "backend" / "vendor" / "MANIFEST.sha256",
    }
    hashes: dict[str, str] = {}
    for name, path in files.items():
        if not path.exists() or not path.read_bytes().strip():
            raise IntegrityError(
                f"dependency representation missing or empty: {name}")
        hashes[name] = sha_file(path)
    return {"files": hashes, "dependency_digest": sha_obj(hashes)}


def environment_record(chat_templates, hardware, dependencies) -> dict:
    uname = platform.uname()
    record = {
        "artifact_type": "v4r4-backend-provenance",
        "analysis_interpreter": {
            "python_version": platform.python_version(),
            "executable": str(Path(sys.executable)),
        },
        "backend_interpreter": str(BACKEND_PYTHON),
        "operating_system": f"{uname.system} {uname.version}",
        "kernel": uname.release,
        "dependencies": dependencies,
        "chat_templates": chat_templates,
        "hardware": hardware,
    }
    record["environment_digest"] = sha_text(json.dumps(
        {k: v for k, v in record.items() if k != "environment_digest"},
        sort_keys=True))
    return record


def main() -> int:
    chat_templates = chat_template_hashes()
    hardware = {model_key: hardware_record(model_key)
                for model_key in MODEL_KEYS}
    record = environment_record(chat_templates, hardware, dependency_record())
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fs.write_json(OUT, record)
    print(json.dumps({
        "written": str(OUT.relative_to(DCI1)),
        "environment_digest": record["environment_digest"][:16],
        "dependency_digest": record["dependencies"]["dependency_digest"][:16],
        "chat_template_hashes": {k: v["chat_template_hash"][:12]
                                 for k, v in chat_templates.items()},
        "hardware": {k: v["device_names"] for k, v in hardware.items()},
    }, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
